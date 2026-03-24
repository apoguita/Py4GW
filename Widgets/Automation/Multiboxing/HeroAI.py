#region Imports
import math
import os
import random
import sys
import traceback
import Py4GW
import PyImGui

from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build

MODULE_NAME = "HeroAI"
MODULE_ICON = "Textures/Module_Icons/HeroAI.png"

from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.routines_src.BehaviourTrees import BehaviorTree

from HeroAI.cache_data import CacheData

from HeroAI.windows import (HeroAI_FloatingWindows ,HeroAI_Windows,)
from HeroAI.ui_base import HeroAI_BaseUI
from HeroAI.ui import (draw_configure_window, draw_skip_cutscene_overlay)
from Py4GWCoreLib import (GLOBAL_CACHE, Agent, ActionQueueManager, LootConfig,
                          Range, Routines, ThrottledTimer, SharedCommandType, Utils)
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

#region GLOBALS
LOOT_THROTTLE_CHECK = ThrottledTimer(250)

cached_data = CacheData()
heroai_build = HeroAI_Build(cached_data)
map_quads : list[Map.Pathing.Quad] = []
build_contract_map_signature: tuple[int, int, int, int] | None = None
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

    heroai_build.set_cached_data(cached_data)
    next(heroai_build.ProcessOOC(), None)
    return heroai_build.DidTickSucceed()

def HandleCombat(cached_data: CacheData):
    options = cached_data.account_options
    
    if not options or not options.Combat:  # halt operation if combat is disabled
        return False
    
    if not cached_data.data.in_aggro:
        return False

    heroai_build.set_cached_data(cached_data)
    next(heroai_build.ProcessCombat(), None)
    return heroai_build.DidTickSucceed()



#region Following
following_flag = False
last_follow_move_point: tuple[float, float] | None = None
follow_map_entry_signature: tuple[int, int, int, int] | None = None
follow_require_front_after_map_entry = False
FOLLOW_MODULE_NAME = "FollowingModule"
FOLLOW_INI_FILENAMES = (
    "FollowModule_Formations.ini",
    "FollowModule_Settings.ini",
)
follow_ini_bootstrap_disable_after_create = False
printed_widget_list = False

def _follow_ini_paths() -> list[str]:
    base_path = os.path.join(
        Py4GW.Console.get_projects_path(),
        "Settings",
        "Global",
        "HeroAI",
    )
    return [os.path.join(base_path, filename) for filename in FOLLOW_INI_FILENAMES]

def _follow_ini_ready() -> bool:
    return all(os.path.exists(path) for path in _follow_ini_paths())

def EnsureFollowModuleIni() -> None:
    global follow_ini_bootstrap_disable_after_create

    if _follow_ini_ready():
        if follow_ini_bootstrap_disable_after_create:
            widget_handler = get_widget_handler()
            if widget_handler.is_widget_enabled(FOLLOW_MODULE_NAME):
                widget_handler.disable_widget(FOLLOW_MODULE_NAME)
            follow_ini_bootstrap_disable_after_create = False
        return
    widget_handler = get_widget_handler()
    if widget_handler.is_widget_enabled(FOLLOW_MODULE_NAME):
        return

    widget_handler.enable_widget(FOLLOW_MODULE_NAME)
    follow_ini_bootstrap_disable_after_create = True

def Follow(cached_data: CacheData) -> BehaviorTree.NodeState:
    global last_follow_move_point, follow_map_entry_signature, follow_require_front_after_map_entry

    def _is_nonzero_xy(x: float, y: float) -> bool:
        return abs(float(x)) > 0.001 or abs(float(y)) > 0.001

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
        #follow_require_front_after_map_entry = True
        follow_require_front_after_map_entry = False
        last_follow_move_point = None

    leader_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(0)
    own_flag_active = bool(getattr(options, "IsFlagged", False)) and _is_nonzero_xy(
        float(options.FlagPos.x),
        float(options.FlagPos.y),
    )
    all_flag_active = (
        leader_options is not None
        and bool(getattr(leader_options, "IsFlagged", False))
        and _is_nonzero_xy(float(leader_options.AllFlag.x), float(leader_options.AllFlag.y))
    )

    follow_threshold_raw = float(options.FollowMoveThreshold)
    combat_threshold_raw = float(options.FollowMoveThresholdCombat)

    if own_flag_active:
        follow_x = float(options.FlagPos.x)
        follow_y = float(options.FlagPos.y)
        follow_z = 0
    elif all_flag_active:
        follow_x = float(leader_options.AllFlag.x)
        follow_y = float(leader_options.AllFlag.y)
        follow_z = 0
    else:
        if follow_threshold_raw < 0.0 and combat_threshold_raw < 0.0:
            return BehaviorTree.NodeState.FAILURE
        follow_x = float(options.FollowPos.x)
        follow_y = float(options.FollowPos.y)
        follow_z = int(float(options.FollowPos.z))

    if cached_data.data.in_aggro:
        if combat_threshold_raw >= 0.0:
            follow_distance = max(0.0, combat_threshold_raw)
        else:
            follow_distance = max(0.0, follow_threshold_raw)

        if not own_flag_active and not all_flag_active:
            leader_agent_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
            if leader_agent_id:
                leader_distance = Utils.Distance(Agent.GetXY(leader_agent_id), Player.GetXY())
                if leader_distance <= follow_distance:
                    return BehaviorTree.NodeState.FAILURE
    else:
        follow_distance = max(0.0, follow_threshold_raw)
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
        if abs(xx - last_x) <= 10 and abs(yy - last_y) <= 10:
            xx += random.uniform(-5.0, 5.0)
            yy += random.uniform(-5.0, 5.0)

    ActionQueueManager().ResetQueue("ACTION")
    if follow_z == 0:
        #Player.Move(xx, yy, follow_z)
        Player.Move(xx, yy)
    else:
        from Py4GWCoreLib.UIManager import UIManager
        from Py4GWCoreLib.enums_src.UI_enums import ControlAction
        ActionQueueManager().AddAction("ACTION",UIManager.Keypress,ControlAction.ControlAction_TargetPartyMember1.value, 0)
        ActionQueueManager().AddAction("ACTION",UIManager.Keypress,ControlAction.ControlAction_Follow.value, 0)


    last_follow_move_point = (xx, yy)
    follow_require_front_after_map_entry = False
    cached_data.follow_throttle_timer.Reset()
    # In combat and out of range: fleeing/repositioning should preempt combat for this tick.
    if cached_data.data.in_aggro:
        return BehaviorTree.NodeState.SUCCESS
    # Out of combat: keep follow non-blocking so OOC behavior can still run freely.
    return BehaviorTree.NodeState.FAILURE

def handle_UI (cached_data: CacheData):    
    global HeroAI_BT
    if not cached_data.ui_state_data.show_classic_controls:
        HeroAI_BaseUI.DrawEmbeddedWindow(cached_data)
    else:
        HeroAI_BaseUI.DrawControlPanelWindow(cached_data)
        if HeroAI_FloatingWindows.settings.ShowPartyPanelUI:
            HeroAI_BaseUI.DrawFollowerUI(cached_data)

    if HeroAI_BaseUI.show_debug:
        HeroAI_BaseUI.draw_debug_window(HeroAI_BT)

    HeroAI_FloatingWindows.show_ui(cached_data)
   
def initialize(cached_data: CacheData) -> bool:  
    global build_contract_map_signature

    if not Routines.Checks.Map.MapValid():
        heroai_build.ClearBuildContract()
        build_contract_map_signature = None
        return False
    
    if not GLOBAL_CACHE.Party.IsPartyLoaded():
        return False
        
    if not Map.IsExplorable():  # halt operation if not in explorable area
        heroai_build.ClearBuildContract()
        build_contract_map_signature = None
        return False

    if Map.IsInCinematic():  # halt operation during cinematic
        return False
    
    HeroAI_Windows.DrawFlags(cached_data)
    HeroAI_FloatingWindows.draw_Targeting_floating_buttons(cached_data)     
    heroai_build.set_cached_data(cached_data)
    map_signature = (
        int(Map.GetMapID()),
        int(Map.GetRegion()[0]),
        int(Map.GetDistrict()),
        int(Map.GetLanguage()[0]),
    )
    if build_contract_map_signature != map_signature:
        heroai_build.EnsureBuildContract(cached_data)
        build_contract_map_signature = map_signature
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

        if not _follow_ini_ready():
            get_widget_handler().enable_widget(FOLLOW_MODULE_NAME)
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
