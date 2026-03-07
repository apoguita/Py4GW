#region Imports
import math
import random
import sys
import traceback
import Py4GW
import PyImGui

from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

MODULE_NAME = "HeroAI"
MODULE_ICON = "Textures/Module_Icons/HeroAI.png"

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
#region Looting
def LootingNode(cached_data: CacheData)-> BehaviorTree.NodeState:
    options = cached_data.account_options
    if not options or not options.Looting:
        return BehaviorTree.NodeState.FAILURE
    
    if cached_data.data.in_aggro:
        return BehaviorTree.NodeState.FAILURE
    
    
    account_email = Player.GetAccountEmail()
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)

    if index != -1 and message and message.Command == SharedCommandType.PickUpLoot:
        if LOOT_THROTTLE_CHECK.IsExpired():
            return BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.RUNNING
    
    if GLOBAL_CACHE.Inventory.GetFreeSlotCount() <= 1:
        return BehaviorTree.NodeState.FAILURE
    
    loot_array = LootConfig().GetfilteredLootArray(
        Range.Earshot.value,
        multibox_loot=True,
        allow_unasigned_loot=False,
    )

    if len(loot_array) == 0:
        return BehaviorTree.NodeState.FAILURE

    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
    if self_account:
        GLOBAL_CACHE.ShMem.SendMessage(
            self_account.AccountEmail,
            self_account.AccountEmail,
            SharedCommandType.PickUpLoot,
            (0, 0, 0, 0),
        )
        LOOT_THROTTLE_CHECK.Reset()
        # Return RUNNING so the tree knows the task started
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree.NodeState.FAILURE




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
    own_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(party_number)
    leader_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(0)
    
    if not own_options:
        return False    

    if own_options.IsFlagged:
        own_follow_x = own_options.FlagPos.x
        own_follow_y = own_options.FlagPos.y
        own_flag_coords = (own_follow_x, own_follow_y)
        if (
            Utils.Distance(own_flag_coords, Agent.GetXY(Player.GetAgentID()))
            >= FOLLOW_COMBAT_DISTANCE
        ):
            return True  # Forces a reset on autoattack timer
    elif leader_options and leader_options.IsFlagged:
        leader_follow_x = leader_options.AllFlag.x
        leader_follow_y = leader_options.AllFlag.y
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



#region Following
following_flag = False
last_follow_move_point: tuple[float, float] | None = None
follow_map_entry_signature: tuple[int, int, int, int] | None = None
follow_require_front_after_map_entry = False
def Follow(cached_data: CacheData) -> BehaviorTree.NodeState:
    global last_follow_move_point, follow_map_entry_signature, follow_require_front_after_map_entry
    
    options = cached_data.account_options
    if not options or not options.Following:  # halt operation if following is disabled
        return BehaviorTree.NodeState.FAILURE
    
    if not cached_data.follow_throttle_timer.IsExpired():
        return BehaviorTree.NodeState.FAILURE

    if Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
        cached_data.follow_throttle_timer.Reset()
        return BehaviorTree.NodeState.FAILURE

    map_sig = (
        int(Map.GetMapID()),
        int(Map.GetRegion()[0]),
        int(Map.GetDistrict()),
        int(Map.GetLanguage()[0]),
    )
    if follow_map_entry_signature != map_sig:
        follow_map_entry_signature = map_sig
        follow_require_front_after_map_entry = True
        last_follow_move_point = None

    follow_x = float(options.FollowPos.x)
    follow_y = float(options.FollowPos.y)
    follow_z = int(float(getattr(options.FollowPos, "z", 0.0)))
    if cached_data.data.in_aggro:
        combat_threshold_raw = float(getattr(options, "FollowMoveThresholdCombat", -1.0))
        if combat_threshold_raw >= 0.0:
            follow_distance = max(0.0, combat_threshold_raw)
        else:
            follow_distance = max(0.0, float(getattr(options, "FollowMoveThreshold", 0.0)))
    else:
        follow_distance = max(0.0, float(getattr(options, "FollowMoveThreshold", 0.0)))
    if Utils.Distance((follow_x, follow_y), Player.GetXY()) <= follow_distance:
        # Inside threshold: do not let follow preempt OOC/combat logic.
        return BehaviorTree.NodeState.FAILURE

    if follow_require_front_after_map_entry:
        px, py = Player.GetXY()
        dx = follow_x - px
        dy = follow_y - py
        if abs(dx) > 0.001 or abs(dy) > 0.001:
            facing = Agent.GetRotationAngle(Player.GetAgentID())
            if ((dx * math.cos(facing)) + (dy * math.sin(facing))) <= 0.0:
                return BehaviorTree.NodeState.FAILURE

    xx = follow_x
    yy = follow_y
    if last_follow_move_point is not None:
        last_x, last_y = last_follow_move_point
        if abs(xx - last_x) <= 0.0001 and abs(yy - last_y) <= 0.0001:
            xx += random.uniform(-5.0, 5.0)
            yy += random.uniform(-5.0, 5.0)

    ActionQueueManager().ResetQueue("ACTION")
    #Player.Move(xx, yy, follow_z)
    Player.Move(xx, yy)

    last_follow_move_point = (xx, yy)
    follow_require_front_after_map_entry = False
    cached_data.follow_throttle_timer.Reset()
    # In combat and out of range: fleeing/repositioning should preempt combat for this tick.
    if cached_data.data.in_aggro:
        return BehaviorTree.NodeState.SUCCESS
    # Out of combat: keep follow non-blocking so OOC behavior can still run freely.
    return BehaviorTree.NodeState.FAILURE

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

def IsUserInterrupting() -> bool:
    from Py4GWCoreLib.enums_src.IO_enums import Key
    io = PyImGui.get_io()
    
    if io.want_capture_keyboard or io.want_capture_mouse:
        return False
    
    movement_keys = [
        Key.W.value, Key.A.value, Key.S.value, Key.D.value,
        Key.Q.value, Key.E.value, Key.Z.value, Key.R.value,
        Key.UpArrow.value, Key.DownArrow.value, 
        Key.LeftArrow.value, Key.RightArrow.value
    ]
    
    for vk in movement_keys:
        if PyImGui.is_key_down(vk):
            return True

    if (PyImGui.is_mouse_down(0) and PyImGui.is_mouse_down(1)) or PyImGui.is_mouse_down(2):
        return True

    return False
    
    
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
        
        BehaviorTree.ConditionNode(
            name="NotUserInterrupting",
            condition_fn=lambda: not IsUserInterrupting()
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
                BehaviorTree.ActionNode(name="LootingRoutine",
                    action_fn=lambda: LootingNode(cached_data),
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

                # Follow
                BehaviorTree.ActionNode(
                    name="Follow",
                    action_fn=lambda: Follow(cached_data),
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
    
def tooltip():
    import PyImGui
    from Py4GWCoreLib.py4gwcorelib_src.Color import Color
    from Py4GWCoreLib.ImGui import ImGui
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("HeroAI: Multibox Combat Engine", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An advanced multi-account synchronization and combat AI system.")
    PyImGui.text("This widget transforms extra game instances into intelligent,")
    PyImGui.text("automated party members that behave like high-performance heroes.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Multibox Logic: Synchronizes actions across multiple game clients")
    PyImGui.bullet_text("Advanced AI: Replaces standard hero behavior with custom combat routines")
    PyImGui.bullet_text("Formation Control: Dynamic follower distancing and tactical positioning")
    PyImGui.bullet_text("Automation Suite: Integrated auto-looting, salvaging, and cutscene skipping")
    PyImGui.bullet_text("Behavior Trees: Complex decision-making for combat and out-of-combat states")
    PyImGui.bullet_text("Shared Memory: Seamless data exchange via the Shared Memory Manager (SMM)")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    PyImGui.bullet_text("Contributors: Mark, frenkey, Dharmantrix, aC, Greg-76, ")
    PyImGui.bullet_text("Wick-Divinus, LLYANL, Zilvereyes, valkogw")

    PyImGui.end_tooltip()



def main():
    global cached_data, map_quads
    
    try:        
        cached_data.Update()  
        HeroAI_FloatingWindows.update()
        handle_UI(cached_data)  
        
        if initialize(cached_data):
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
