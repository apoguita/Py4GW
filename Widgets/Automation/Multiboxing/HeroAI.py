#region Imports
import math
import sys
import traceback
import Py4GW
import PyImGui

from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

MODULE_NAME = "HeroAI"

from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.routines_src.BehaviourTrees import BehaviorTree
from Py4GWCoreLib.Pathing import AutoPathing

from HeroAI.cache_data import CacheData
from HeroAI.constants import (FOLLOW_DISTANCE_OUT_OF_COMBAT, MELEE_RANGE_VALUE, RANGED_RANGE_VALUE)
from HeroAI.utils import (DistanceFromWaypoint)
from HeroAI.following import Follow, LeaderUpdate, draw_follow_config, reset_map_quads as follow_reset_map_quads
from HeroAI.windows import (HeroAI_FloatingWindows ,HeroAI_Windows,)
from HeroAI.ui import (draw_configure_window, draw_skip_cutscene_overlay)
from Py4GWCoreLib import (GLOBAL_CACHE, Agent, ActionQueueManager, LootConfig,
                          Range, Routines, ThrottledTimer, SharedCommandType, Utils)

#region GLOBALS
FOLLOW_COMBAT_DISTANCE = 25.0  # if body blocked, we get close enough.
LEADER_FLAG_TOUCH_RANGE_THRESHOLD_VALUE = Range.Touch.value * 1.1
LOOT_THROTTLE_CHECK = ThrottledTimer(250)

cached_data = CacheData()
map_quads: list[Map.Pathing.Quad] = []

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



#region Following
# Follow logic moved to HeroAI.following module
# Follow() and LeaderUpdate() are imported at the top

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
    
    # Leader-only follow config window
    draw_follow_config(cached_data)
   
def initialize(cached_data: CacheData) -> bool:  
    if not Routines.Checks.Map.MapValid():
        return False
    
    if not GLOBAL_CACHE.Party.IsPartyLoaded():
        return False
        
    # Handle map change cleanup
    current_map_id = Map.GetMapID()
    if not hasattr(cached_data, "last_map_id") or cached_data.last_map_id != current_map_id:
        cached_data.last_map_id = current_map_id
        follow_reset_map_quads()
        
    if not Map.IsExplorable():  # halt operation if not in explorable area
        return False

    if Map.IsInCinematic():  # halt operation during cinematic
        return False
    
    HeroAI_Windows.DrawFlags(cached_data)
    HeroAI_FloatingWindows.draw_Targeting_floating_buttons(cached_data)     
    cached_data.UpdateCombat()
    
    # Ensure NavMesh is loaded for follower pathfinding
    if not AutoPathing().get_navmesh():
        if not getattr(AutoPathing(), "loader", None):
            AutoPathing().loader = AutoPathing().load_pathing_maps()
        try:
            next(AutoPathing().loader)
        except StopIteration:
            AutoPathing().loader = None
    
    # Leader calculates and writes follow positions for all followers
    LeaderUpdate(cached_data)
    
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
            follow_reset_map_quads()
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