import Py4GW

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Sources.ApoSource.absolute_pre_searing_src.prepare_quests import get_sequence_builders
from Sources.ApoSource.absolute_pre_searing_src import GENESIS_DATA

import PyImGui

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree


MODULE_NAME = "Absolute Pre-Searing"
BANNER_WIDTH = 600
BANNER_HEIGHT = 200
initialized = False
INI_KEY = ""
INI_PATH = "Widgets/AbsolutePreSearing"
INI_FILENAME = "AbsolutePreSearing.ini"
projects_root = Py4GW.Console.get_projects_path()
TEXTURE_PATH = f"{projects_root}/Sources/ApoSource/absolute_pre_searing_src/absolute-pre-searing-banner.png"
botting_trees: dict[str, BottingTree] = {}
selected_debug_tree_name = "Prepare Character"
selected_start_sequence = "Sequence_001_Common"
draw_move_path = True
draw_move_path_labels = False
draw_move_path_thickness = 4.0
draw_move_waypoint_radius = 15.0
draw_move_current_waypoint_radius = 20.0
print_log_to_console = False

IMP_BAG_ID = 1
IMP_BAG_SLOT = 0
PREPARE_CHARACTER_TREE_NAME = "Prepare Character"
UNLOCK_RANGER_SECONDARY_TREE_NAME = "Unlock Ranger Secondary"

#unlock ranger profession
def UnlockRangerSecondary(module_name: str) -> BehaviorTree:
    unlock_ranger_secondary_data = GENESIS_DATA.unlock_ranger_secondary_data

    tree = BehaviorTree.SequenceNode(
        name="Starting common sequence",
        children=[
            RoutinesBT.Player.LogMessage(source=module_name, to_console=lambda: print_log_to_console, to_blackboard=True, message=unlock_ranger_secondary_data.ashford_abbey_travel_message),
            RoutinesBT.Map.TravelToOutpost(outpost_id=unlock_ranger_secondary_data.ashford_abbey_map_id, log=False),
            RoutinesBT.Player.LogMessage(source=module_name, to_console=lambda: print_log_to_console, to_blackboard=True, message=unlock_ranger_secondary_data.lakeside_county_travel_message),
            
            RoutinesBT.Player.Move(x=unlock_ranger_secondary_data.lakeside_county_exit_coords_001[0], y=unlock_ranger_secondary_data.lakeside_county_exit_coords_001[1], log=False),
            RoutinesBT.Player.Move(x=unlock_ranger_secondary_data.lakeside_county_exit_coords[0], y=unlock_ranger_secondary_data.lakeside_county_exit_coords[1], log=False),
            RoutinesBT.Map.WaitforMapLoad(map_id=unlock_ranger_secondary_data.lakeside_county_map_id, log=False),
            
            RoutinesBT.Player.LogMessage(source=module_name, to_console=lambda: print_log_to_console, to_blackboard=True, message=unlock_ranger_secondary_data.destroy_summoning_stones_message),
            RoutinesBT.Items.DestroyItems(
                model_ids=list([ModelID.Igneous_Summoning_Stone.value,]),
                log=False,
                aftercast_ms=100,
            ),
            
            RoutinesBT.Player.LogMessage(source=module_name, to_console=lambda: print_log_to_console, to_blackboard=True, message=unlock_ranger_secondary_data.regent_valley_travel_message),
            
            RoutinesBT.Player.Move(x=unlock_ranger_secondary_data.regent_valley_mid_001_exit_coords[0], y=unlock_ranger_secondary_data.regent_valley_mid_001_exit_coords[1], log=False),
            RoutinesBT.Player.Move(x=unlock_ranger_secondary_data.regent_valley_mid_002_exit_coords[0], y=unlock_ranger_secondary_data.regent_valley_mid_002_exit_coords[1], log=False),
            RoutinesBT.Player.MoveDirect(unlock_ranger_secondary_data.regent_valley_over_bridge_exit_coords, log=False),
            RoutinesBT.Player.Move(x=unlock_ranger_secondary_data.regent_valley_exit_coords[0], y=unlock_ranger_secondary_data.regent_valley_exit_coords[1], log=False),
            RoutinesBT.Map.WaitforMapLoad(map_id=unlock_ranger_secondary_data.regent_valley_map_id, log=False),
            
            
            RoutinesBT.Player.LogMessage(source=module_name, to_console=lambda: print_log_to_console, to_blackboard=True, message=unlock_ranger_secondary_data.master_ranger_nente_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=unlock_ranger_secondary_data.master_ranger_nente_coords[0],
                y=unlock_ranger_secondary_data.master_ranger_nente_coords[1],
                button_number=0,
                log=False,
            ),
            RoutinesBT.Player.SendAutomaticDialog(button_number=0, log=False),
            
            RoutinesBT.Player.LogMessage(source=module_name, to_console=lambda: print_log_to_console, to_blackboard=True, message=unlock_ranger_secondary_data.melandru_statue_message),
            RoutinesBT.Player.Move(x=unlock_ranger_secondary_data.melandru_statue_coords[0], y=unlock_ranger_secondary_data.melandru_statue_coords[1], log=False),
            
            RoutinesBT.Player.LogMessage(source=module_name,to_console=lambda: print_log_to_console,to_blackboard=True,message=unlock_ranger_secondary_data.hero_ai_disable_message,),
            BottingTree.DisableHeroAITree(),
            
            RoutinesBT.Agents.MoveAndTargetByModelID(
                model_id=unlock_ranger_secondary_data.pet_model_id,
                log=False,
            ),

            RoutinesBT.Skills.CastSkillID(
                skill_id=unlock_ranger_secondary_data.charm_pet_skill_id,
                log=False,
            ),
            RoutinesBT.Player.Wait(duration_ms=unlock_ranger_secondary_data.charm_pet_wait_ms, log=False),
            BottingTree.EnableHeroAITree(),
            
            RoutinesBT.Player.LogMessage(source=module_name, to_console=lambda: print_log_to_console, to_blackboard=True, message=unlock_ranger_secondary_data.master_ranger_nente_message),
            RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
                x=unlock_ranger_secondary_data.master_ranger_nente_coords[0],
                y=unlock_ranger_secondary_data.master_ranger_nente_coords[1],
                button_number=0,
                log=False,
            ),
            
            
            #RoutinesBT.Player.LogMessage(source=module_name, to_console=lambda: print_log_to_console, to_blackboard=True, message=unlock_ranger_secondary_data.ashford_abbey_travel_message),
            #RoutinesBT.Map.TravelToOutpost(outpost_id=unlock_ranger_secondary_data.ashford_abbey_map_id, log=False),
        ],
    )
    return BehaviorTree(tree)



#region UI
def _configure_common_upkeep_trees(tree: BottingTree) -> BottingTree:
    tree.SetUpkeepTrees([
        (
            "OutpostImpService",
            lambda: RoutinesBT.Upkeepers.OutpostImpService(
                target_bag=IMP_BAG_ID,
                slot=IMP_BAG_SLOT,
                log=False,
            ),
        ),
        (
            "ExplorableImpService",
            lambda: RoutinesBT.Upkeepers.ExplorableImpService(
                log=False,
            ),
        ),
    ])
    return tree


def _build_prepare_character_tree() -> BottingTree:
    tree = _configure_common_upkeep_trees(BottingTree(INI_KEY))
    tree.SetNamedPlannerSteps(
        get_sequence_builders(MODULE_NAME, print_to_console=lambda: print_log_to_console),
        start_from=selected_start_sequence,
        name="All quests sequence",
    )
    return tree


def _ensure_prepare_character_tree(auto_start: bool = False) -> BottingTree:
    global botting_trees
    if PREPARE_CHARACTER_TREE_NAME not in botting_trees:
        botting_trees[PREPARE_CHARACTER_TREE_NAME] = _build_prepare_character_tree()
    tree = botting_trees[PREPARE_CHARACTER_TREE_NAME]
    if auto_start:
        tree.Start()
    return tree


def _build_unlock_ranger_secondary_tree() -> BottingTree:
    tree = _configure_common_upkeep_trees(BottingTree(INI_KEY))
    tree.SetNamedPlannerSteps(
        [
            (UNLOCK_RANGER_SECONDARY_TREE_NAME, lambda: UnlockRangerSecondary(MODULE_NAME)),
        ],
        name=UNLOCK_RANGER_SECONDARY_TREE_NAME,
    )
    return tree


def _ensure_unlock_ranger_secondary_tree(auto_start: bool = False) -> BottingTree:
    global botting_trees
    if UNLOCK_RANGER_SECONDARY_TREE_NAME not in botting_trees:
        botting_trees[UNLOCK_RANGER_SECONDARY_TREE_NAME] = _build_unlock_ranger_secondary_tree()
    tree = botting_trees[UNLOCK_RANGER_SECONDARY_TREE_NAME]
    if auto_start:
        tree.Start()
    return tree


def _get_debug_tree_names() -> list[str]:
    return list(botting_trees.keys())


def _get_selected_debug_tree() -> BottingTree | None:
    if selected_debug_tree_name in botting_trees:
        return botting_trees[selected_debug_tree_name]
    if botting_trees:
        first_name = next(iter(botting_trees))
        return botting_trees[first_name]
    return None


def _draw_welcome_tab(botting_tree:BottingTree | None):
    ImGui.push_font("Bold",22)
    ImGui.text("Welcome to Absolute Pre-Searing!")
    ImGui.pop_font()
    ImGui.separator()
    if ImGui.collapsing_header("About this script", flags=PyImGui.TreeNodeFlags.DefaultOpen):
        ImGui.text_wrapped("This script is a comprehensive collection of quests and activities for the Pre-Searing area.")
        ImGui.text_wrapped("Each tab contains a list of activities that can be completed, including quests, leveling, farming, and other content.")
        ImGui.separator()
    
    if ImGui.collapsing_header("How to use", flags=PyImGui.TreeNodeFlags.DefaultOpen):
        ImGui.bullet_text("Set your looting filters")
        ImGui.bullet_text("Deactivate Automatic Handling in Inventory+")
        ImGui.bullet_text("This Script has no Item handling, manual intervention is required to keep bags clean.")
        ImGui.bullet_text("Deactivate HeroAI or any other combat automator")
        ImGui.bullet_text("Create a new character")
        ImGui.bullet_text('Press "Prepare Character" to execute starting setup')
        ImGui.bullet_text("After finishing, explore the tabs and select the activities you want to do")
        ImGui.separator()

    if botting_tree is not None and botting_tree.IsStarted():
        if PyImGui.button("Stop Routines"):
            botting_tree.Stop()
    else:
        if PyImGui.button("Prepare Character"):
            _ensure_prepare_character_tree(auto_start=True)
       
    if botting_tree is not None and botting_tree.IsStarted():     
        PyImGui.same_line(0, -1)
        
        if botting_tree.IsPaused():
            if PyImGui.button("Unpause Routines"):
                botting_tree.Pause(False)
        else:
            if PyImGui.button("Pause Routines"):
                botting_tree.Pause(True)
                
    ImGui.separator()
    
def _draw_debug_tab():
    global selected_start_sequence, print_log_to_console, selected_debug_tree_name
    tree_names = _get_debug_tree_names()
    if tree_names:
        current_tree_index = tree_names.index(selected_debug_tree_name) if selected_debug_tree_name in tree_names else 0
        new_tree_index = PyImGui.combo("Debug Tree", current_tree_index, tree_names)
        if 0 <= new_tree_index < len(tree_names):
            selected_debug_tree_name = tree_names[new_tree_index]
    else:
        ImGui.text("No trees instantiated yet.")
        return

    botting_tree = _get_selected_debug_tree()
    if botting_tree is None:
        ImGui.text("Selected tree is unavailable.")
        return

    sequence_names = botting_tree.GetNamedPlannerStepNames()
    current_index = sequence_names.index(selected_start_sequence) if selected_start_sequence in sequence_names else 0
    
    new_index = PyImGui.combo("Start From Sequence", current_index, sequence_names)
    if 0 <= new_index < len(sequence_names):
        selected_start_sequence = sequence_names[new_index]
    if PyImGui.button("Restart From Selected Sequence"):
        botting_tree = _ensure_prepare_character_tree()
        botting_tree.RestartFromSequence(selected_start_sequence, auto_start=True, name="All quests sequence")
    ImGui.separator()
    
    print_log_to_console = PyImGui.checkbox("Print Log To Console", print_log_to_console)
    if PyImGui.button("Clear UI Log"):
        botting_tree.ClearBlackboardLog()
        botting_tree.ClearBlackboardLogHistory()
    PyImGui.same_line(0, -1)
    if PyImGui.button("Copy UI Log"):
        log_history = botting_tree.GetBlackboardLogHistory()
        PyImGui.set_clipboard_text("\n".join(log_history))
    ImGui.separator()
    
    if ImGui.collapsing_header("Draw Move Path Debug Options", flags=PyImGui.TreeNodeFlags.DefaultOpen):
        global draw_move_path, draw_move_path_labels, draw_move_path_thickness, draw_move_waypoint_radius, draw_move_current_waypoint_radius
        draw_move_path = PyImGui.checkbox("Draw Move Path", draw_move_path)
        draw_move_path_labels = PyImGui.checkbox("Draw Path Labels", draw_move_path_labels)
        draw_move_path_thickness = PyImGui.slider_float("Path Thickness", draw_move_path_thickness, 1.0, 6.0)
        draw_move_waypoint_radius = PyImGui.slider_float("Waypoint Radius", draw_move_waypoint_radius, 15.0, 100.0)
        draw_move_current_waypoint_radius = PyImGui.slider_float("Current Waypoint Radius", draw_move_current_waypoint_radius, 20.0, 120.0)
        
    log_history = botting_tree.GetBlackboardLogHistory()
    if PyImGui.begin_child("AbsolutePreSearingLog", (0, 200), True, PyImGui.WindowFlags.HorizontalScrollbar):
        reversed_log_history = log_history[::-1]
        for entry in reversed_log_history:
            PyImGui.text_wrapped(entry)
        #if log_history:
        #    PyImGui.set_scroll_here_y(1.0)
    PyImGui.end_child()
  
def _draw_unlock_professions_tab():
    if PyImGui.button("Unlock Ranger Secondary"):
        global selected_debug_tree_name
        _ensure_unlock_ranger_secondary_tree(auto_start=True)
        selected_debug_tree_name = UNLOCK_RANGER_SECONDARY_TREE_NAME
    unlock_tree = botting_trees.get(UNLOCK_RANGER_SECONDARY_TREE_NAME)
    if unlock_tree is not None and unlock_tree.IsStarted():
        PyImGui.same_line(0, -1)
        if PyImGui.button("Stop Unlock Ranger Secondary"):
            unlock_tree.Stop()
    
def draw():
    global INI_KEY
    global draw_move_path, draw_move_path_labels
    global draw_move_path_thickness, draw_move_waypoint_radius, draw_move_current_waypoint_radius
    if not INI_KEY:
        return
    prepare_character_tree = botting_trees.get(PREPARE_CHARACTER_TREE_NAME)
    PyImGui.set_next_window_size((BANNER_WIDTH + 20, 0))
    if ImGui.Begin(ini_key=INI_KEY, name="Absolute Pre-Searing", flags=PyImGui.WindowFlags.AlwaysAutoResize):
        ImGui.DrawTexture(TEXTURE_PATH, BANNER_WIDTH, BANNER_HEIGHT)
        ImGui.separator()
        if ImGui.begin_tab_bar("MainTabBar##AbsolutePreSearing"):
            if ImGui.begin_tab_item("Welcome"):
                _draw_welcome_tab(prepare_character_tree)
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Unlock Professions"):
                _draw_unlock_professions_tab()
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Outpost Unlocks"):
                pass
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Quests"):
                pass
                ImGui.end_tab_item()    
            if ImGui.begin_tab_item("Farms"):
                pass
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Debug"):
                _draw_debug_tab()
                ImGui.end_tab_item() 
            ImGui.end_tab_bar()
    ImGui.End(ini_key=INI_KEY)

#region main
def _add_config_vars():
    global INI_KEY
    IniManager().add_bool(INI_KEY, "show_tree", "Display", "ShowTree", default=True)
    IniManager().add_bool(INI_KEY, "enable_headless_heroai", "Behavior", "EnableHeadlessHeroAI", default=True)
    IniManager().add_bool(INI_KEY, "print_log_to_console", "Display", "PrintLogToConsole", default=False)
    IniManager().add_bool(INI_KEY, "draw_move_path", "Display", "DrawMovePath", default=True)
    IniManager().add_bool(INI_KEY, "draw_move_path_labels", "Display", "DrawMovePathLabels", default=False)
    IniManager().add_float(INI_KEY, "draw_move_path_thickness", "Display", "DrawMovePathThickness", default=2.0)
    IniManager().add_float(INI_KEY, "draw_move_waypoint_radius", "Display", "DrawMoveWaypointRadius", default=45.0)
    IniManager().add_float(INI_KEY, "draw_move_current_waypoint_radius", "Display", "DrawMoveCurrentWaypointRadius", default=65.0)

def main():
    global INI_KEY, initialized, print_log_to_console

    if not initialized:
        if not INI_KEY:
            INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not INI_KEY:
                return
            _add_config_vars()
            IniManager().load_once(INI_KEY)

        print_log_to_console = IniManager().getBool(INI_KEY, "print_log_to_console", default=False)
        initialized = True

    for tree in botting_trees.values():
        tree.tick()

    selected_tree = _get_selected_debug_tree()
    if selected_tree is not None and draw_move_path:
        selected_tree.DrawMovePath(
            draw_labels=draw_move_path_labels,
            path_thickness=draw_move_path_thickness,
            waypoint_radius=draw_move_waypoint_radius,
            current_waypoint_radius=draw_move_current_waypoint_radius,
        )


if __name__ == "__main__":
    main()
