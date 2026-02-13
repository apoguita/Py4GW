import Py4GW
import PyImGui
import os

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.PathLocator import PathLocator
from Sources.oazix.CustomBehaviors.primitives.botting.botting_manager import BottingManager
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers

# Global state for bot selection and control
_selected_bot_index = 0
_bot_scripts_cache = None
_last_scan_time = 0
_show_utility_skills_config = False

def _scan_bot_scripts():
    """
    Scan the bots folder and return a list of (bot_name, script_path) tuples.
    Caches results to avoid repeated file system scans.
    """
    global _bot_scripts_cache, _last_scan_time
    import time

    current_time = time.time()
    # Cache for 5 seconds
    if _bot_scripts_cache is not None and (current_time - _last_scan_time) < 5:
        return _bot_scripts_cache

    bots_folder = PathLocator.get_custom_behaviors_root_directory() + "\\bots"
    bot_scripts = []

    try:
        if os.path.exists(bots_folder):
            for filename in os.listdir(bots_folder):
                if filename.endswith(".py") and not filename.startswith("__"):
                    # Remove .py extension for display name
                    bot_name = os.path.splitext(filename)[0]
                    script_path = os.path.join(bots_folder, filename)
                    bot_scripts.append((bot_name, script_path))

            # Sort by bot name
            bot_scripts.sort(key=lambda x: x[0])
    except Exception as e:
        pass  # Silently fail if folder doesn't exist or can't be read

    _bot_scripts_cache = bot_scripts
    _last_scan_time = current_time
    return bot_scripts

def render():
    global _selected_bot_index

    if CustomBehaviorLoader()._botting_daemon_fsm is not None and CustomBehaviorLoader().custom_combat_behavior is not None:
        PyImGui.text(f"CustomBehavior FSM Management")

        PyImGui.text(f"CustomBehavior.IsExecutingUtilitySkills: {CustomBehaviorLoader().custom_combat_behavior.is_executing_utility_skills()}")

        from Py4GWCoreLib.py4gwcorelib_src.FSM import FSM
        fsm:FSM = CustomBehaviorLoader()._botting_daemon_fsm
        PyImGui.text(f"FSM.IsStarted: {fsm.is_started()}")
        PyImGui.text(f"FSM.IsPaused: {fsm.paused}")
        PyImGui.text(f"FSM.IsFinished: {fsm.is_finished()}")
        PyImGui.text(f"FSM.CurrentState: {fsm.get_current_step_name()}")

        PyImGui.separator()

    PyImGui.text(f"Multiboxing Botting behaviors")

    if not custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader():
        PyImGui.text(f"Feature restricted to party leader.")
        return
    
    PyImGui.separator()

    _render_utility_skills_config()
    _render_bot_scripts_table()


def _render_bot_scripts_table():
    """Render the bot scripts table UI section."""
    global _show_bots_scripts

    _show_bots_scripts = PyImGui.collapsing_header("Bot Scripts")

    if not _show_bots_scripts:
        return
    
    # Bot Scripts Table
    bot_scripts = _scan_bot_scripts()

    if len(bot_scripts) > 0:
        PyImGui.text(f"Available Bot Scripts ({len(bot_scripts)})")
        PyImGui.separator()

        # Create table with 2 columns: Bot Name and Load Button
        table_flags = PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.ScrollY
        if PyImGui.begin_table("BotScriptsTable", 2, table_flags, 0, 300):
            # Setup columns
            PyImGui.table_setup_column("Bot Name", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Action", PyImGui.TableColumnFlags.WidthFixed, 80)
            PyImGui.table_headers_row()

            # Render each bot script as a row
            for bot_name, script_path in bot_scripts:
                PyImGui.table_next_row()

                # Column 0: Bot Name
                PyImGui.table_set_column_index(0)
                PyImGui.text(bot_name)

                # Column 1: Load Button
                PyImGui.table_set_column_index(1)
                button_id = f"Load##{bot_name}"
                if PyImGui.button(button_id):
                    # Load and run the bot script with a 500ms delay
                    Py4GW.Console.defer_stop_load_and_run(script_path, delay_ms=500)

            PyImGui.end_table()
    else:
        PyImGui.text("No bot scripts found in the bots folder.")
        PyImGui.text("Place .py files in: Sources.oazix.CustomBehaviors/bots/")

def _render_utility_skills_config():
    """Render the utility skills configuration UI section."""
    global _show_utility_skills_config

    _show_utility_skills_config = PyImGui.collapsing_header("Utility Skills Configuration")

    if not _show_utility_skills_config:
        return

    config = BottingManager()

    # Pacifist Skills Section
    if PyImGui.tree_node("Pacifist Skills"):
        _render_skill_list(config.pacifist_skills, "pacifist")
        PyImGui.tree_pop()

    # Aggressive Skills Section
    if PyImGui.tree_node("Aggressive Skills"):
        _render_skill_list(config.aggressive_skills, "aggressive")
        PyImGui.tree_pop()

    # Automover Skills Section
    if PyImGui.tree_node("Automover Skills"):
        _render_skill_list(config.automover_skills, "automover")
        PyImGui.tree_pop()

    if PyImGui.button(f"Save Configuration {IconsFontAwesome5.ICON_SAVE}"):
        config.save()
    PyImGui.same_line(0.0, 10.0)
    if PyImGui.button(f"Delete Configuration {IconsFontAwesome5.ICON_TRASH}"):
        config.delete_configuration()
 

def _render_skill_list(skills: list, category: str):
    """Render a list of utility skills with toggle checkboxes."""
    for i, skill in enumerate(skills):
        checkbox_id = f"{skill.display_name}##{category}_{i}"
        new_value = PyImGui.checkbox(checkbox_id, skill.enabled)
        if new_value != skill.enabled:
            skill.enabled = new_value