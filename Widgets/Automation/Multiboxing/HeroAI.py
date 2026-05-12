#region Imports
import math
import os
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
from HeroAI.follow.follower_runtime import FollowExecutionState, execute_follower_follow

from HeroAI.windows import (HeroAI_FloatingWindows ,HeroAI_Windows,)
from HeroAI.ui_base import HeroAI_BaseUI
from HeroAI.ui import (draw_configure_window, draw_skip_cutscene_overlay)
from HeroAI import team_viewer_broadcast
from Py4GWCoreLib import (GLOBAL_CACHE, Agent, LootConfig,
                          Range, Routines, ThrottledTimer, SharedCommandType)

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

    player_agent_id = Player.GetAgentID()
    if cached_data.combat_handler.InCastingRoutine() or Agent.IsCasting(player_agent_id):
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
follow_execution_state = FollowExecutionState()
FOLLOW_INI_FILENAMES = (
    "FollowModule_Formations.ini",
    "FollowModule_Settings.ini",
)
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
    if _follow_ini_ready():
        return

    try:
        from HeroAI.follow.editor import _init_once
        _init_once()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Follow formation INI bootstrap failed: {e}", Py4GW.Console.MessageType.Error)

def Follow(cached_data: CacheData) -> BehaviorTree.NodeState:
    return execute_follower_follow(cached_data, follow_execution_state)

def handle_UI (cached_data: CacheData):
    global HeroAI_BT
    team_viewer_broadcast.tick()
    if not cached_data.ui_state_data.show_classic_controls:
        HeroAI_BaseUI.DrawEmbeddedWindow(cached_data)
    else:
        HeroAI_BaseUI.DrawControlPanelWindow(cached_data)
        if HeroAI_FloatingWindows.settings.ShowPartyPanelUI:
            HeroAI_BaseUI.DrawFollowerUI(cached_data)

    if HeroAI_BaseUI.show_debug:
        HeroAI_BaseUI.draw_debug_window(HeroAI_BT)

    HeroAI_FloatingWindows.show_ui(cached_data)
    HeroAI_BaseUI.DrawBuildMatchesWindow(cached_data)
    HeroAI_BaseUI.DrawFollowFormationsQuickWindow(cached_data)
   
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
    
    HeroAI_BaseUI._process_flagging_runtime(cached_data)
    #HeroAI_FloatingWindows.draw_Targeting_floating_buttons(cached_data)     
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
        return BehaviorTree.NodeState.SUCCESS   # block lower-priority automation for this tick
    return BehaviorTree.NodeState.FAILURE      # allow next branch


def user_interrupt() -> BehaviorTree.NodeState:
    if IsUserInterrupting():
        return BehaviorTree.NodeState.SUCCESS   # block lower-priority automation for this tick
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
                    name="UserInterrupt",
                    action_fn=lambda: user_interrupt(),
                ),

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
    PyImGui.bullet_text("Intelligent interrupt logic, hex removal, enemy tracking, and more")
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
    PyImGui.bullet_text("Sloppynacho, Wick-Divinus, LLYANL, Zilvereyes, valkogw")

    PyImGui.end_tooltip()

modulo = 0

def main():
    global cached_data, map_quads, modulo
    
    try:
        cached_data.Update()

        EnsureFollowModuleIni()
        HeroAI_FloatingWindows.update()
        handle_UI(cached_data)
        
        if initialize(cached_data):
            modulo += 1
            if modulo >= 2:
                modulo = 0
                HeroAI_BT.tick()
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
