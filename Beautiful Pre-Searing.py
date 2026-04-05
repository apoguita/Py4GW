import Py4GW
import PyImGui

from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager

from Sources.ApoSource.beautiful_pre_searing_src.acquire_belt_pouch import AcquireBeltPouch
from Sources.ApoSource.beautiful_pre_searing_src.acquire_weapon import AcquireWeapon
from Sources.ApoSource.beautiful_pre_searing_src.globals import ITEMS_BLACKLIST

from Sources.ApoSource.beautiful_pre_searing_src.globals import *
from Sources.ApoSource.beautiful_pre_searing_src.helpers import *
from Sources.ApoSource.beautiful_pre_searing_src.tree_builder import CommonMapExit, ensure_botting_tree
from Sources.ApoSource.beautiful_pre_searing_src.unlock_pet import UnlockPet
from Sources.ApoSource.beautiful_pre_searing_src.getting_started import GetGettingStartedSequence
from Sources.ApoSource.beautiful_pre_searing_src.farming_routines import FarmSkale, FarmUntilItemQuantityReached

BANNER_WIDTH = 422
BANNER_HEIGHT = 200
initialized = False
INI_KEY = ""
INI_PATH = "Widgets/BeautifulPreSearing"
INI_FILENAME = "BeautifulPreSearing.ini"
projects_root = Py4GW.Console.get_projects_path()
TEXTURE_PATH = f"{projects_root}/Sources/ApoSource/beautiful_pre_searing_src/resources/Beautiful Pre-Searing-banner.png"

draw_move_path = True
draw_move_path_labels = False
draw_move_path_thickness = 4.0
draw_move_waypoint_radius = 15.0
draw_move_current_waypoint_radius = 20.0
selected_debug_tree_name = "Getting Started"


def GettingStartedTree():
    return GetGettingStartedSequence(
        print_to_console=PRINT_TO_CONSOLE,
    )


def SkaleFarmLoopTree() -> BehaviorTree:
    return FarmUntilItemQuantityReached(
        start_map_id=ASCALON_CITY_MAP_ID,
        perform_farming_tree=FarmSkale,
        model_id=SKALE_FIN_MODEL_ID,
        target_quantity=5,
        exclude_models=ITEMS_BLACKLIST,
    )
    

def UnlockWizardsFolly() -> BehaviorTree:
    return CommonMapExit(
        travel_map_id=ASHFORD_ABBEY_MAP_ID,
        path_tree=BehaviorTree(
            BehaviorTree.SequenceNode(
                name="MoveToWizardsFollyExit",
                children=[
                    LogMessage("Moving to Wizard's Folly exit"),
                    BT.Move(GO_TO_WIZARDS_FOLLY_EXIT_COORDS),
                    BT.WaitForMapLoad(WIZARDS_FOLLY_MAP_ID),
                    BT.Move(GO_TO_FOIBLES_FAIR_COORDS),
                    BT.WaitForMapLoad(FOIBLES_FAIR_MAP_ID),
                ],
            )
        ),
        exclude_models=ITEMS_BLACKLIST,
    )


def UnlockBarradinState() -> BehaviorTree:
    return CommonMapExit(
        travel_map_id=ASCALON_CITY_MAP_ID,
        path_tree=BehaviorTree(
            BehaviorTree.SequenceNode(
                name="MoveToBarradinStateExit",
                children=[
                    LogMessage("Moving to Barradin State exit"),
                    BT.Move(GO_TO_GREEN_HILLS_COUNTY_COORDS),
                    BT.WaitForMapLoad(GREEN_HILLS_COUNTY_MAP_ID),
                    BT.Move(GO_TO_BARRADIN_STATE_COORDS),
                    BT.WaitForMapLoad(BARRADIN_STATE_MAP_ID),
                ],
            )
        ),
        exclude_models=ITEMS_BLACKLIST,
    )

def UnlockFortRanik() -> BehaviorTree:
    return CommonMapExit(
        travel_map_id=ASHFORD_ABBEY_MAP_ID,
        path_tree=BehaviorTree(
            BehaviorTree.SequenceNode(
                name="MoveToFortRanikExit",
                children=[
                    LogMessage("Moving to Fort Ranik exit"),
                    BT.Move(FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[0]),
                    BT.Move(FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[1]),
                    BT.MoveDirect([FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[2]]),
                    BT.Move(FROM_ASHFORD_ABBEY_TO_REGENT_VALLEY_COORDS[3]),
                    BT.WaitForMapLoad(REGENT_VALLEY_MAP_ID),
                    BT.Move(GO_TO_FORT_RANIK_COORDS),
                    BT.WaitForMapLoad(FORT_RANIK_MAP_ID),
                ],
            )
        ),
        exclude_models=ITEMS_BLACKLIST,
    )



def _draw_welcome_tab() -> None:
    ImGui.push_font("Bold", 22)
    ImGui.text("Welcome to Beautiful Pre-Searing!")
    ImGui.pop_font()

    if ImGui.collapsing_header("About this script", flags=0):
        ImGui.text_wrapped("This script is a comprehensive collection of quests and activities for the Pre-Searing area.")
        ImGui.text_wrapped("Each tab contains a list of activities that can be completed, including quests, leveling, farming, and other content.")
        ImGui.separator()

    if ImGui.collapsing_header("How to use", flags=0):
        ImGui.bullet_text("Set your looting filters")
        ImGui.bullet_text("Deactivate Automatic Handling in Inventory+")
        ImGui.bullet_text("Deactivate HeroAI or any other combat automator")
        ImGui.bullet_text("Create a new character")
        ImGui.bullet_text('Press "Getting Started" to execute starting setup')
        ImGui.bullet_text("After finishing, explore the tabs and select the activities you want to do")
        ImGui.separator()

    ImGui.separator()


def _draw_getting_started_tab(botting_tree: BottingTree) -> None:
    global selected_debug_tree_name

    if ImGui.collapsing_header("1. Prepare Your Character"):
        ImGui.text_wrapped("This routine will complete important early quests that unlock essential features and quality of life improvements for the rest of the content in Pre-Searing.")
        ImGui.separator()

        if selected_debug_tree_name == "Getting Started" and botting_tree.IsStarted():
            if PyImGui.button("Stop Routines"):
                botting_tree.Stop()
            PyImGui.same_line(0, -1)
            if botting_tree.IsPaused():
                if PyImGui.button("Unpause Routines"):
                    botting_tree.Pause(False)
            else:
                if PyImGui.button("Pause Routines"):
                    botting_tree.Pause(True)
        else:
            if PyImGui.button("Getting Started"):
                selected_debug_tree_name = "Getting Started"
                botting_tree.SetCurrentNamedPlannerSteps(
                    GettingStartedTree(),
                    name="All quests sequence",
                    auto_start=True,
                )

    if ImGui.collapsing_header("2. Capture Pet and Unlock Secondary Profession"):
        ImGui.text_wrapped("This routine will capture the pet from the first quest and complete the necessary steps to unlock the secondary profession.")
        ImGui.text_wrapped("This is a separate routine because it involves a lot of waiting for the pet capture to succeed, which can take a long time and is not required to be done early on.")
        ImGui.separator()

        if selected_debug_tree_name == "Unlock Pet" and botting_tree.IsStarted():
            if PyImGui.button("Stop Unlock Pet"):
                botting_tree.Stop()
            PyImGui.same_line(0, -1)
            if botting_tree.IsPaused():
                if PyImGui.button("Unpause Unlock Pet"):
                    botting_tree.Pause(False)
            else:
                if PyImGui.button("Pause Unlock Pet"):
                    botting_tree.Pause(True)
        else:
            if PyImGui.button("Unlock Pet"):
                selected_debug_tree_name = "Unlock Pet"
                botting_tree.SetCurrentTree(
                    UnlockPet(),
                    auto_start=True,
                )

    if ImGui.collapsing_header("3. Acquire a Weapon"):
        ImGui.text_wrapped("This section will cover acquiring a weapon for your character")
        ImGui.text_wrapped("Nevermore Flatbow is the best weapon to acquire in Pre-Searing, we will attempt to acquire it")
        ImGui.text_wrapped("If Nevermore is not available, we will fall back to Farming material for Buying a bow with a collector")
        ImGui.separator()

        if selected_debug_tree_name == "Acquire Weapon" and botting_tree.IsStarted():
            if PyImGui.button("Stop Acquire Weapon"):
                botting_tree.Stop()
            PyImGui.same_line(0, -1)
            if botting_tree.IsPaused():
                if PyImGui.button("Unpause Acquire Weapon"):
                    botting_tree.Pause(False)
            else:
                if PyImGui.button("Pause Acquire Weapon"):
                    botting_tree.Pause(True)
        else:
            if PyImGui.button("Acquire Weapon"):
                selected_debug_tree_name = "Acquire Weapon"
                botting_tree.SetCurrentTree(
                    AcquireWeapon(),
                    auto_start=True,
                )

    if ImGui.collapsing_header("4. Acquire a Belt Pouch"):
        ImGui.text_wrapped("This section will cover acquiring a belt pouch for your character")
        ImGui.text_wrapped("Belt pouches are a very useful item that increase your inventory space, and the one available in Pre-Searing is very easy to acquire")
        ImGui.separator()

        if selected_debug_tree_name == "Acquire Belt Pouch" and botting_tree.IsStarted():
            if PyImGui.button("Stop Acquire Belt Pouch"):
                botting_tree.Stop()
            PyImGui.same_line(0, -1)
            if botting_tree.IsPaused():
                if PyImGui.button("Unpause Acquire Belt Pouch"):
                    botting_tree.Pause(False)
            else:
                if PyImGui.button("Pause Acquire Belt Pouch"):
                    botting_tree.Pause(True)
        else:
            if PyImGui.button("Acquire Belt Pouch"):
                selected_debug_tree_name = "Acquire Belt Pouch"
                botting_tree.SetCurrentTree(
                    AcquireBeltPouch(
                        exclude_models=ITEMS_BLACKLIST,
                    ),
                    auto_start=True,
                )


def _draw_outpost_unlocks_tab(botting_tree: BottingTree) -> None:
    global selected_debug_tree_name

    if ImGui.collapsing_header("1. Unlock Wizard's Folly"):
        ImGui.text_wrapped("This routine travels from Ashford Abbey through Wizard's Folly and into Foible's Fair to unlock the outpost path.")
        ImGui.separator()

        if selected_debug_tree_name == "Unlock Wizard's Folly" and botting_tree.IsStarted():
            if PyImGui.button("Stop Unlock Wizard's Folly"):
                botting_tree.Stop()
            PyImGui.same_line(0, -1)
            if botting_tree.IsPaused():
                if PyImGui.button("Unpause Unlock Wizard's Folly"):
                    botting_tree.Pause(False)
            else:
                if PyImGui.button("Pause Unlock Wizard's Folly"):
                    botting_tree.Pause(True)
        else:
            if PyImGui.button("Unlock Wizard's Folly"):
                selected_debug_tree_name = "Unlock Wizard's Folly"
                botting_tree.SetCurrentTree(
                    UnlockWizardsFolly(),
                    auto_start=True,
                )
                
    if ImGui.collapsing_header("2. Unlock Barradin State"):
        ImGui.text_wrapped("This routine travels from Ascalon City through Green Hills County and into Barradin State to unlock the outpost path.")
        ImGui.separator()

        if selected_debug_tree_name == "Unlock Barradin State" and botting_tree.IsStarted():
            if PyImGui.button("Stop Unlock Barradin State"):
                botting_tree.Stop()
            PyImGui.same_line(0, -1)
            if botting_tree.IsPaused():
                if PyImGui.button("Unpause Unlock Barradin State"):
                    botting_tree.Pause(False)
            else:
                if PyImGui.button("Pause Unlock Barradin State"):
                    botting_tree.Pause(True)
        else:
            if PyImGui.button("Unlock Barradin State"):
                selected_debug_tree_name = "Unlock Barradin State"
                botting_tree.SetCurrentTree(
                    UnlockBarradinState(),
                    auto_start=True,
                )
                
    if ImGui.collapsing_header("3. Unlock Fort Ranik"):
        ImGui.text_wrapped("This routine travels from Ashford Abbey through Regent Valley and into Fort Ranik to unlock the outpost path.")
        ImGui.separator()

        if selected_debug_tree_name == "Unlock Fort Ranik" and botting_tree.IsStarted():
            if PyImGui.button("Stop Unlock Fort Ranik"):
                botting_tree.Stop()
            PyImGui.same_line(0, -1)
            if botting_tree.IsPaused():
                if PyImGui.button("Unpause Unlock Fort Ranik"):
                    botting_tree.Pause(False)
            else:
                if PyImGui.button("Pause Unlock Fort Ranik"):
                    botting_tree.Pause(True)
        else:
            if PyImGui.button("Unlock Fort Ranik"):
                selected_debug_tree_name = "Unlock Fort Ranik"
                botting_tree.SetCurrentTree(
                    UnlockFortRanik(),
                    auto_start=True,
                )


def _draw_farming_tab(botting_tree: BottingTree) -> None:
    global selected_debug_tree_name

    if ImGui.collapsing_header("1. Skale Fin Farm"):
        ImGui.text_wrapped("Placeholder skale fin farming routine using the reusable farming helper.")
        ImGui.text_wrapped("Update the start map, kill path, model id, and target quantity in this script if you want to customize the farm.")
        ImGui.separator()

        if selected_debug_tree_name == "Skale Fin Farm" and botting_tree.IsStarted():
            if PyImGui.button("Stop Skale Fin Farm"):
                botting_tree.Stop()
            PyImGui.same_line(0, -1)
            if botting_tree.IsPaused():
                if PyImGui.button("Unpause Skale Fin Farm"):
                    botting_tree.Pause(False)
            else:
                if PyImGui.button("Pause Skale Fin Farm"):
                    botting_tree.Pause(True)
        else:
            if PyImGui.button("Start Skale Fin Farm"):
                selected_debug_tree_name = "Skale Fin Farm"
                botting_tree.SetCurrentTree(
                    SkaleFarmLoopTree(),
                    auto_start=True,
                )


def _draw_debug_tab() -> None:
    global selected_debug_tree_name
    botting_tree = ensure_botting_tree()

    if selected_debug_tree_name == "HeroAI Only" and botting_tree.IsStarted():
        if PyImGui.button("Stop HeroAI Only"):
            botting_tree.Stop()
        PyImGui.same_line(0, -1)
        if botting_tree.IsPaused():
            if PyImGui.button("Unpause HeroAI Only"):
                botting_tree.Pause(False)
        else:
            if PyImGui.button("Pause HeroAI Only"):
                botting_tree.Pause(True)
    else:
        if PyImGui.button("Start HeroAI Only"):
            selected_debug_tree_name = "HeroAI Only"
            botting_tree.SetCurrentTree(
                None,
                auto_start=True,
            )
    ImGui.separator()

    tree_names = [
        "Getting Started",
        "HeroAI Only",
        "Unlock Pet",
        "Unlock Wizard's Folly",
        "Unlock Barradin State",
        "Unlock Fort Ranik",
        "Acquire Weapon",
        "Acquire Belt Pouch",
        "Skale Fin Farm",
    ]
    current_tree_index = tree_names.index(selected_debug_tree_name) if selected_debug_tree_name in tree_names else 0

    if botting_tree.IsStarted():
        ImGui.text_wrapped(f"Active routine: {selected_debug_tree_name}")
        ImGui.text_wrapped("Stop the current routine to switch the debug context.")
    else:
        new_tree_index = PyImGui.combo("Debug Tree", current_tree_index, tree_names)
        if 0 <= new_tree_index < len(tree_names) and tree_names[new_tree_index] != selected_debug_tree_name:
            selected_debug_tree_name = tree_names[new_tree_index]
            if selected_debug_tree_name == "Getting Started":
                botting_tree.SetCurrentNamedPlannerSteps(
                    GettingStartedTree(),
                    name="All quests sequence",
                    auto_start=False,
                )
            elif selected_debug_tree_name == "HeroAI Only":
                botting_tree.SetCurrentTree(None, auto_start=False)
            elif selected_debug_tree_name == "Unlock Pet":
                botting_tree.SetCurrentTree(UnlockPet(), auto_start=False)
            elif selected_debug_tree_name == "Unlock Wizard's Folly":
                botting_tree.SetCurrentTree(UnlockWizardsFolly(), auto_start=False)
            elif selected_debug_tree_name == "Unlock Barradin State":
                botting_tree.SetCurrentTree(UnlockBarradinState(), auto_start=False)
            elif selected_debug_tree_name == "Unlock Fort Ranik":
                botting_tree.SetCurrentTree(UnlockFortRanik(), auto_start=False)
            elif selected_debug_tree_name == "Acquire Weapon":
                botting_tree.SetCurrentTree(AcquireWeapon(), auto_start=False)
            elif selected_debug_tree_name == "Acquire Belt Pouch":
                botting_tree.SetCurrentTree(
                    AcquireBeltPouch(
                        exclude_models=ITEMS_BLACKLIST,
                    ),
                    auto_start=False,
                )
            elif selected_debug_tree_name == "Skale Fin Farm":
                botting_tree.SetCurrentTree(SkaleFarmLoopTree(), auto_start=False)


    if ImGui.collapsing_header("Draw Move Path Debug Options", flags=PyImGui.TreeNodeFlags.DefaultOpen):
        global draw_move_path, draw_move_path_labels, draw_move_path_thickness, draw_move_waypoint_radius, draw_move_current_waypoint_radius
        draw_move_path = PyImGui.checkbox("Draw Move Path", draw_move_path)
        draw_move_path_labels = PyImGui.checkbox("Draw Path Labels", draw_move_path_labels)
        draw_move_path_thickness = PyImGui.slider_float("Path Thickness", draw_move_path_thickness, 1.0, 6.0)
        draw_move_waypoint_radius = PyImGui.slider_float("Waypoint Radius", draw_move_waypoint_radius, 15.0, 100.0)
        draw_move_current_waypoint_radius = PyImGui.slider_float("Current Waypoint Radius", draw_move_current_waypoint_radius, 20.0, 120.0)

    botting_tree.DrawDebugConsole(
        child_id="BeautifulPreSearingLog",
        height=200,
        reverse_order=True,
        show_controls=True,
    )


def draw() -> None:
    global INI_KEY
    if not INI_KEY:
        return

    botting_tree = ensure_botting_tree()
    PyImGui.set_next_window_size((BANNER_WIDTH + 20, 0))
    if ImGui.Begin(ini_key=INI_KEY, name="Beautiful Pre-Searing", flags=PyImGui.WindowFlags.AlwaysAutoResize):
        if ImGui.begin_tab_bar("MainTabBar##BeautifulPreSearing"):
            if ImGui.begin_tab_item("Welcome"):
                ImGui.DrawTexture(TEXTURE_PATH, BANNER_WIDTH, BANNER_HEIGHT)
                ImGui.separator()
                _draw_welcome_tab()
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Getting Started"):
                _draw_getting_started_tab(botting_tree)
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Outpost Unlocks"):
                _draw_outpost_unlocks_tab(botting_tree)
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Quests"):
                pass
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Farms"):
                _draw_farming_tab(botting_tree)
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Debug"):
                _draw_debug_tab()
                ImGui.end_tab_item()
            ImGui.end_tab_bar()
    ImGui.End(ini_key=INI_KEY)


def _add_config_vars() -> None:
    global INI_KEY
    IniManager().add_bool(INI_KEY, "draw_move_path", "Display", "DrawMovePath", default=True)
    IniManager().add_bool(INI_KEY, "draw_move_path_labels", "Display", "DrawMovePathLabels", default=False)
    IniManager().add_float(INI_KEY, "draw_move_path_thickness", "Display", "DrawMovePathThickness", default=2.0)
    IniManager().add_float(INI_KEY, "draw_move_waypoint_radius", "Display", "DrawMoveWaypointRadius", default=45.0)
    IniManager().add_float(INI_KEY, "draw_move_current_waypoint_radius", "Display", "DrawMoveCurrentWaypointRadius", default=65.0)


def main() -> None:
    global INI_KEY, initialized

    if not initialized:
        if not INI_KEY:
            INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not INI_KEY:
                return
            _add_config_vars()
            IniManager().load_once(INI_KEY)

        ensure_botting_tree().SetCurrentNamedPlannerSteps(
            GettingStartedTree(),
            name="All quests sequence",
            auto_start=False,
        )
        initialized = True

    botting_tree = ensure_botting_tree()
    botting_tree.tick()

    if draw_move_path:
        botting_tree.DrawMovePath(
            draw_labels=draw_move_path_labels,
            path_thickness=draw_move_path_thickness,
            waypoint_radius=draw_move_waypoint_radius,
            current_waypoint_radius=draw_move_current_waypoint_radius,
        )


if __name__ == "__main__":
    main()
