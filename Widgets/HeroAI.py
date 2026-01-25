#region Imports
import math
import sys
import traceback
import Py4GW

from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

MODULE_NAME = "HeroAI"

for module in list(sys.modules):
    if MODULE_NAME in module:
        del sys.modules[module]

from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.routines_src.BehaviourTrees import BehaviorTree

from HeroAI.cache_data import CacheData
from HeroAI.constants import (FOLLOW_DISTANCE_OUT_OF_COMBAT, MELEE_RANGE_VALUE, RANGED_RANGE_VALUE)
from HeroAI.globals import hero_formation
from HeroAI.utils import (DistanceFromWaypoint)
from HeroAI.windows import (HeroAI_FloatingWindows ,HeroAI_Windows,)
from HeroAI.ui import (draw_configure_window, draw_skip_cutscene_overlay)
from Py4GWCoreLib import (GLOBAL_CACHE, Agent, ActionQueueManager, LootConfig,
                          Range, Routines, ThrottledTimer, SharedCommandType, Utils)

#region GLOBALS
FOLLOW_COMBAT_DISTANCE = 25.0  # if body blocked, we get close enough.
LEADER_FLAG_TOUCH_RANGE_THRESHOLD_VALUE = Range.Touch.value * 1.1
LOOT_THROTTLE_CHECK = ThrottledTimer(250)

cached_data = CacheData()
map_quads : list[Map.Pathing.Quad] = []

#region Combat
def HandleOutOfCombat(cached_data: CacheData):
    options = cached_data.account_options
    
    if not options or not options.Combat:  # halt operation if combat is disabled
        return False
    
    if cached_data.data.in_aggro:
        return False

    return cached_data.combat_handler.HandleCombat(ooc=True)
def HandleCombatFlagging(cached_data: CacheData):
    # Suspends all activity until HeroAI has made it to the flagged position
    # Still goes into combat as long as its within the combat follow range value of the expected flag
    party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
    own_options = GLOBAL_CACHE.ShMem.GetGerHeroAIOptionsByPartyNumber(party_number)
    leader_options = GLOBAL_CACHE.ShMem.GetGerHeroAIOptionsByPartyNumber(0)
    
    if not own_options:
        return False    

    if own_options.IsFlagged:
        own_follow_x = own_options.FlagPosX
        own_follow_y = own_options.FlagPosY
        own_flag_coords = (own_follow_x, own_follow_y)
        if (
            Utils.Distance(own_flag_coords, Agent.GetXY(Player.GetAgentID()))
            >= FOLLOW_COMBAT_DISTANCE
        ):
            return True  # Forces a reset on autoattack timer
    elif leader_options and leader_options.IsFlagged:
        leader_follow_x = leader_options.FlagPosX
        leader_follow_y = leader_options.FlagPosY
        leader_flag_coords = (leader_follow_x, leader_follow_y)
        if (
            Utils.Distance(leader_flag_coords, Agent.GetXY(Player.GetAgentID()))
            >= LEADER_FLAG_TOUCH_RANGE_THRESHOLD_VALUE
        ):
            return True  # Forces a reset on autoattack timer
    return False


def HandleCombat(cached_data: CacheData):
    options = cached_data.account_options
    
    if not options or not options.Combat:  # halt operation if combat is disabled
        return False
    
    if not cached_data.data.in_aggro:
        return False

    combat_flagging_handled = HandleCombatFlagging(cached_data)
    if combat_flagging_handled:
        return combat_flagging_handled
    return cached_data.combat_handler.HandleCombat(ooc=False)

def HandleAutoAttack(cached_data: CacheData) -> bool:
    options = cached_data.account_options
    if not options.Combat:  # halt operation if combat is disabled
        return False
    
    target_id = Player.GetTargetID()
    _, target_aliegance = Agent.GetAllegiance(target_id)

    if target_id == 0 or Agent.IsDead(target_id) or (target_aliegance != "Enemy"):
        if (
            options.Combat
            and (not Agent.IsAttacking(Player.GetAgentID()))
            and (not Agent.IsCasting(Player.GetAgentID()))
            and (not Agent.IsMoving(Player.GetAgentID()))
        ):
            cached_data.combat_handler.ChooseTarget()
            cached_data.auto_attack_timer.Reset()
            return True

    # auto attack
    if cached_data.auto_attack_timer.HasElapsed(cached_data.auto_attack_time) and cached_data.data.weapon_type != 0:
        if (
            options.Combat
            and (not Agent.IsAttacking(Player.GetAgentID()))
            and (not Agent.IsCasting(Player.GetAgentID()))
            and (not Agent.IsMoving(Player.GetAgentID()))
        ):
            cached_data.combat_handler.ChooseTarget()
        cached_data.auto_attack_timer.Reset()
        cached_data.combat_handler.ResetSkillPointer()
        return True
    return False


cached_data.in_looting_routine = False

#region Looting
def LootingRoutineActive():
    account_email = Player.GetAccountEmail()
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)

    if index == -1 or message is None:
        return False

    if message.Command != SharedCommandType.PickUpLoot:
        return False
    return True


def Loot(cached_data: CacheData):
    global LOOT_THROTTLE_CHECK
    options = cached_data.account_options

    if not options or not options.Looting:
        return False

    if cached_data.data.in_aggro:
        return False

    if LootingRoutineActive():
        return True

    if not LOOT_THROTTLE_CHECK.IsExpired():
        cached_data.in_looting_routine = True
        return True

    # Stop if inventory is full
    if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1:
        return False

    # Build the loot array based on filtering rules
    
    loot_array = LootConfig().GetfilteredLootArray(
        Range.Earshot.value,
        multibox_loot=True,
        allow_unasigned_loot=False,
    )
    if len(loot_array) == 0:
        cached_data.in_looting_routine = False
        return False

    cached_data.in_looting_routine = True
    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(cached_data.account_email)
    if not self_account:
        cached_data.in_looting_routine = False
        return False

    # === Throttled Send ===
    if LOOT_THROTTLE_CHECK.IsExpired():
        GLOBAL_CACHE.ShMem.SendMessage(
            self_account.AccountEmail,
            self_account.AccountEmail,
            SharedCommandType.PickUpLoot,
            (0, 0, 0, 0),
        )
        LOOT_THROTTLE_CHECK.Reset()

    return True


following_flag = False


#region Following
def Follow(cached_data: CacheData):
    global FOLLOW_DISTANCE_ON_COMBAT, following_flag, map_quads
    
    options = cached_data.account_options
    if not options or not options.Following:  # halt operation if following is disabled
        return False
    
    if not cached_data.follow_throttle_timer.IsExpired():
        return False
    
    if not map_quads:
        map_quads = Map.Pathing.GetMapQuads()

        

    if Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
        cached_data.follow_throttle_timer.Reset()
        return False

    party_number = GLOBAL_CACHE.Party.GetOwnPartyNumber()
    leader_options = GLOBAL_CACHE.ShMem.GetGerHeroAIOptionsByPartyNumber(0)
        
    follow_x = 0.0
    follow_y = 0.0
    follow_angle = -1.0

    if options.IsFlagged:  # my own flag
        follow_x = options.FlagPosX
        follow_y = options.FlagPosY
        follow_angle = options.FlagFacingAngle
        following_flag = True
        
    elif leader_options and leader_options.IsFlagged:  # leader's flag
        follow_x = leader_options.FlagPosX
        follow_y = leader_options.FlagPosY
        follow_angle = leader_options.FlagFacingAngle
        following_flag = False
        
    else:  # follow leader
        following_flag = False
        follow_x, follow_y = Agent.GetXY(GLOBAL_CACHE.Party.GetPartyLeaderID())
        follow_angle = Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())

    if following_flag:
        FOLLOW_DISTANCE_ON_COMBAT = FOLLOW_COMBAT_DISTANCE
    elif Agent.IsMelee(Player.GetAgentID()):
        FOLLOW_DISTANCE_ON_COMBAT = MELEE_RANGE_VALUE
    else:
        FOLLOW_DISTANCE_ON_COMBAT = RANGED_RANGE_VALUE

    if cached_data.data.in_aggro:
        follow_distance = FOLLOW_DISTANCE_ON_COMBAT
    else:
        follow_distance = FOLLOW_DISTANCE_OUT_OF_COMBAT if not following_flag else 0.0

    angle_changed_pass = False
    if cached_data.data.angle_changed and (not cached_data.data.in_aggro):
        angle_changed_pass = True

    close_distance_check = DistanceFromWaypoint(follow_x, follow_y) <= follow_distance

    if not angle_changed_pass and close_distance_check:
        return False

    hero_grid_pos = party_number + GLOBAL_CACHE.Party.GetHeroCount() + GLOBAL_CACHE.Party.GetHenchmanCount()
    angle_on_hero_grid = follow_angle + Utils.DegToRad(hero_formation[hero_grid_pos])

    def is_position_on_map(x, y) -> bool:
        if not HeroAI_FloatingWindows.settings.ConfirmFollowPoint:
            return True
        
        for quad in map_quads:    
            if Map.Pathing._point_in_quad(x, y, quad):
                return True
            
        return False
    
    if following_flag:
        xx = follow_x
        yy = follow_y
    else:
        xx = Range.Touch.value * math.cos(angle_on_hero_grid) + follow_x
        yy = Range.Touch.value * math.sin(angle_on_hero_grid) + follow_y
            
        if not is_position_on_map(xx, yy):
            ## fallback to direct follow if calculated point is off-map to avoid getting stuck or falling behind
            xx = follow_x
            yy = follow_y
    
    point_zero = (0.0, 0.0)
    if Utils.Distance((follow_x, follow_y), point_zero) <= 5:
        ConsoleLog(MODULE_NAME, "Follow: Target position too close to point zero, skipping move.", Py4GW.Console.MessageType.Warning)
        return False
    
    if not Agent.IsValid(GLOBAL_CACHE.Party.GetPartyLeaderID()):
        ConsoleLog(MODULE_NAME, "Follow: Party leader agent is not valid, cannot follow.", Py4GW.Console.MessageType.Warning)
        return False
    
    cached_data.data.angle_changed = False
    ActionQueueManager().ResetQueue("ACTION")
    Player.Move(xx, yy)
    return True

show_debug = False

def draw_debug_window(cached_data: CacheData):
    global HeroAI_BT, show_debug
    import PyImGui
    visible, show_debug = PyImGui.begin_with_close("HeroAI Debug", show_debug, 0)
    if visible:
        if HeroAI_BT is not None:
            HeroAI_BT.draw()
    PyImGui.end()
        

def handle_UI (cached_data: CacheData):    
    global show_debug    
    if not cached_data.ui_state_data.show_classic_controls:   
        HeroAI_FloatingWindows.DrawEmbeddedWindow(cached_data)
    else:
        HeroAI_Windows.DrawControlPanelWindow(cached_data)  
        if HeroAI_FloatingWindows.settings.ShowPartyPanelUI:         
            HeroAI_Windows.DrawFollowerUI(cached_data)
        
    if show_debug:
        draw_debug_window(cached_data)
        
    HeroAI_FloatingWindows.show_ui(cached_data) 
   
def initialize(cached_data: CacheData) -> bool:  
    if not Routines.Checks.Map.MapValid():
        return False
    
    if not GLOBAL_CACHE.Party.IsPartyLoaded():
        return False
        
    if not Map.IsExplorable():  # halt operation if not in explorable area
        return False

    if Map.IsInCinematic():  # halt operation during cinematic
        return False
    
    HeroAI_Windows.DrawFlags(cached_data)
    HeroAI_FloatingWindows.draw_Targeting_floating_buttons(cached_data)     
    cached_data.UpdateCombat()
    return True

        
#region main  
#DEPRECATED FOR BEHAVIOUR TREE IMPLEMENTATION
#KEPT FOR REFERENCE
"""def UpdateStatus(cached_data: CacheData) -> bool:
    
    if (
            not Agent.IsAlive(Player.GetAgentID())
            or (HeroAI_FloatingWindows.DistanceToDestination(cached_data) >= Range.SafeCompass.value)
            or Agent.IsKnockedDown(Player.GetAgentID())
            or cached_data.combat_handler.InCastingRoutine()
            or Agent.IsCasting(Player.GetAgentID())
        ):
            return False

    
    if LootingRoutineActive():
        return True

    if HandleOutOfCombat(cached_data):
        return True

    if Agent.IsMoving(Player.GetAgentID()):
        return False

    if Loot(cached_data):
        return True

    if Follow(cached_data):
        cached_data.follow_throttle_timer.Reset()
        return True

    if HandleCombat(cached_data):
        cached_data.auto_attack_timer.Reset()
        return True

    if not cached_data.data.in_aggro:
        return False

    if HandleAutoAttack(cached_data):
        return True
    
    return False"""

    
GlobalGuardNode = BehaviorTree.SequenceNode(
    name="GlobalGuard",
    children=[
        BehaviorTree.ConditionNode(
            name="IsAlive",
            condition_fn=lambda:
                Agent.IsAlive(Player.GetAgentID())
        ),

        BehaviorTree.ConditionNode(
            name="DistanceSafe",
            condition_fn=lambda:
                HeroAI_FloatingWindows.DistanceToDestination(cached_data)
                < Range.SafeCompass.value
        ),

        BehaviorTree.ConditionNode(
            name="NotKnockedDown",
            condition_fn=lambda:
                not Agent.IsKnockedDown(Player.GetAgentID())
        ),
    ],
)
  
CastingBlockNode = BehaviorTree.ConditionNode(
    name="IsCasting",
    condition_fn=lambda:
        BehaviorTree.NodeState.RUNNING
        if (
            cached_data.combat_handler.InCastingRoutine()
            or Agent.IsCasting(Player.GetAgentID())
        )
        else BehaviorTree.NodeState.SUCCESS
)

    
    
def movement_interrupt() -> BehaviorTree.NodeState:
    if Agent.IsMoving(Player.GetAgentID()):
        return BehaviorTree.NodeState.RUNNING   # block automation
    return BehaviorTree.NodeState.FAILURE      # allow next branch


HeroAI_BT = BehaviorTree.SequenceNode(name="HeroAI_Main_BT",
    children=[
        # ---------- GLOBAL HARD GUARD ----------
        GlobalGuardNode,
        CastingBlockNode,

        # ---------- PRIORITY SELECTOR ----------
        BehaviorTree.SelectorNode(name="UpdateStatusSelector",
            children=[
                # Looting routine already active (allowed anytime)
                BehaviorTree.ActionNode(name="LootingRoutineActive",
                    action_fn=lambda: (
                        BehaviorTree.NodeState.RUNNING
                        if LootingRoutineActive()
                        else BehaviorTree.NodeState.FAILURE
                    ),
                ),

                # Out-of-combat behavior (allowed while moving)
                BehaviorTree.ActionNode(
                    name="HandleOutOfCombat",
                    action_fn=lambda: (
                        BehaviorTree.NodeState.SUCCESS
                        if HandleOutOfCombat(cached_data)
                        else BehaviorTree.NodeState.FAILURE
                    ),
                ),

                # User / external movement override (blocks below)
                BehaviorTree.ActionNode(
                    name="MovementInterrupt",
                    action_fn=lambda: movement_interrupt(),
                ),

                # Loot
                BehaviorTree.ActionNode(
                    name="Loot",
                    action_fn=lambda: (
                        BehaviorTree.NodeState.SUCCESS
                        if Loot(cached_data)
                        else BehaviorTree.NodeState.FAILURE
                    ),
                ),

                # Follow
                BehaviorTree.ActionNode(
                    name="Follow",
                    action_fn=lambda: (
                        cached_data.follow_throttle_timer.Reset()
                        or BehaviorTree.NodeState.SUCCESS
                        if Follow(cached_data)
                        else BehaviorTree.NodeState.FAILURE
                    ),
                ),

                # Combat
                BehaviorTree.ActionNode(
                    name="HandleCombat",
                    action_fn=lambda: (
                        cached_data.auto_attack_timer.Reset()
                        or BehaviorTree.NodeState.SUCCESS
                        if HandleCombat(cached_data)
                        else BehaviorTree.NodeState.FAILURE
                    ),
                ),

                # Auto-attack (guarded by in_aggro)
                BehaviorTree.SequenceNode(
                    name="AutoAttackSequence",
                    children=[
                        BehaviorTree.ConditionNode(
                            name="InAggro",
                            condition_fn=lambda: cached_data.data.in_aggro,
                        ),
                        BehaviorTree.ActionNode(
                            name="HandleAutoAttack",
                            action_fn=lambda: (
                                BehaviorTree.NodeState.SUCCESS
                                if HandleAutoAttack(cached_data)
                                else BehaviorTree.NodeState.FAILURE
                            ),
                        ),
                    ],
                ),
            ],
        ),
    ],
)


#region real_main
def configure():
    draw_configure_window(MODULE_NAME, HeroAI_FloatingWindows.configure_window)



def main():
    global cached_data, map_quads
    
    try:        
        cached_data.Update()  
        HeroAI_FloatingWindows.update()
        handle_UI(cached_data)  
        
        if initialize(cached_data):
            # UpdateStatus(cached_data)
            HeroAI_BT.tick()
            pass
        else:
            map_quads.clear()
            HeroAI_BT.reset()



    except ImportError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(MODULE_NAME, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass

def minimal():    
    draw_skip_cutscene_overlay()

def on_enable():
    HeroAI_FloatingWindows.settings.reset()
    HeroAI_FloatingWindows.SETTINGS_THROTTLE.SetThrottleTime(50)

__all__ = ['main', 'configure', 'on_enable']