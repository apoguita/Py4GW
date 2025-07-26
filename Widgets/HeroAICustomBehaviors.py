import os
import pathlib
import sys
import traceback

import Py4GW  # type: ignore
from HeroAI.cache_data import CacheData
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Timer
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import Color
from Py4GWCoreLib.Py4GWcorelib import Utils
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
WITH_DETAIL = False


def render_custom_behavior_gui():
    global WITH_DETAIL

    custom_combat_behavior = CustomBehaviorLoader().custom_combat_behavior
    if PyImGui.button(f"{IconsFontAwesome5.ICON_SYNC} Search build again"):
        CustomBehaviorLoader().refresh_custom_behavior_candidate()

    if not custom_combat_behavior:
        PyImGui.text("Current build is None.")
        return

    PyImGui.text(f"HasLoaded : {CustomBehaviorLoader()._has_loaded}")
    PyImGui.text(f"Selected template : {custom_combat_behavior.__class__.__name__}")
    if custom_combat_behavior:
        PyImGui.text(f"Account state:{custom_combat_behavior.get_state()}")
        PyImGui.text(f"Final state:{custom_combat_behavior.get_final_state()}")

    if custom_combat_behavior.get_is_enabled():
        if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES} Disable"):
            custom_combat_behavior.disable()
    else:
        if PyImGui.button(f"{IconsFontAwesome5.ICON_CHECK} Enable"):
            custom_combat_behavior.enable()
    pass

    if custom_combat_behavior and type(custom_combat_behavior).mro()[1].__name__ != CustomBehaviorBaseUtility.__name__:
        PyImGui.separator()
        PyImGui.text("Generic skills : ")
        generic_behavior_build = custom_combat_behavior.get_generic_behavior_build()
        if generic_behavior_build:
            for skill in generic_behavior_build:  # type: ignore
                PyImGui.text(f"bbb {skill.skill_name}")  # type: ignore

    if custom_combat_behavior and type(custom_combat_behavior).mro()[1].__name__ == CustomBehaviorBaseUtility.__name__:
        PyImGui.separator()
        instance: CustomBehaviorBaseUtility = custom_combat_behavior  # type: ignore
        PyImGui.text("Utility system : ")
        PyImGui.same_line(0, -1)
        WITH_DETAIL = PyImGui.checkbox("with detail", WITH_DETAIL)

        scores: list[tuple[CustomSkillUtilityBase, float | None]] = instance.get_all_scores()
        if PyImGui.begin_table("skill", 2, int(PyImGui.TableFlags.SizingStretchProp)):
            PyImGui.table_setup_column("A")
            PyImGui.table_setup_column("B")

        for score in scores:

            def label_generic_utility(utility: CustomSkillUtilityBase) -> str:
                if utility.__class__.__name__ == "HeroAiUtility":
                    return f"{IconsFontAwesome5.ICON_GAMEPAD} "
                return ""

            current_path = pathlib.Path.cwd()
            prefix = ""
            if "Widgets" in str(current_path):
                prefix = "..\\"

            score_text = f"Score = {score[1]:06.2f}" if score[1] is not None else "Score = 0"
            texture_file = prefix + GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(score[0].custom_skill.skill_id)

            PyImGui.table_next_row()
            PyImGui.table_next_column()
            ImGui.DrawTexture(texture_file, 44, 44)
            PyImGui.table_next_column()

            skill: CustomSkillUtilityBase = score[0]
            PyImGui.text_scaled(
                f"{label_generic_utility(skill)}{score_text}", Color(0, 255, 0, 255).to_tuple_normalized(), 1.2
            )
            PyImGui.text(f"{skill.custom_skill.skill_name}")

            if WITH_DETAIL:
                PyImGui.bullet_text("required ressource")
                PyImGui.same_line(0, -1)
                PyImGui.text_colored(f"{skill.mana_required_to_cast}", Utils.RGBToNormal(27, 126, 246, 255))
                PyImGui.bullet_text(f"allowed in : {[x.name for x in skill.allowed_states]}")  # type: ignore
                PyImGui.bullet_text(f"pre_check : {skill.are_common_pre_checks_valid(instance.get_final_state())}")

            PyImGui.table_next_row()

        PyImGui.end_table()


# Iterate through all modules in sys.modules (already imported modules)
# Iterate over all imported modules and reload them
for module_name in list(sys.modules.keys()):
    if module_name not in ("sys", "importlib", "cache_data"):
        try:
            if "behavior" in module_name.lower():
                print(f"Reloading module: {module_name}")
                del sys.modules[module_name]
                pass
        except Exception as e:
            print(f"Error reloading module {module_name}: {e}")


script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))

first_run = True

BASE_DIR = os.path.join(project_root, "Widgets/Config")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "hero_ai_custom_behavior.ini")
os.makedirs(BASE_DIR, exist_ok=True)

cached_data = CacheData()
widget_handler = get_widget_handler()

# ——— Window Persistence Setup ———
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()

# String consts
MODULE_NAME = "HeroAICustomBehavior"  # Change this Module name
COLLAPSED = "collapsed"
X_POS = "x"
Y_POS = "y"

# load last‐saved window state (fallback to 100,100 / un-collapsed)
window_x = ini_window.read_int(MODULE_NAME, X_POS, 100)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 100)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)
party_forced_state_combo = 0


def draw_widget():
    global window_x, window_y, window_collapsed, first_run

    if first_run:
        PyImGui.set_next_window_pos(window_x, window_y)
        PyImGui.set_next_window_collapsed(window_collapsed, 0)
        first_run = False

    is_window_opened = PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize)
    new_collapsed = PyImGui.is_window_collapsed()
    end_pos = PyImGui.get_window_pos()

    if is_window_opened:
        global party_forced_state_combo

        is_hero_ai_enabled = widget_handler.is_widget_enabled("HeroAI")
        if not is_hero_ai_enabled:
            header_text = "The following prevents you from using HeroAICustomBehavior:"
            final_text = header_text
            if not is_hero_ai_enabled:
                final_text += "\n  - HeroAI is not running"
            PyImGui.text(final_text)
            return

        PyImGui.begin_tab_bar("current_build")

        if PyImGui.begin_tab_item("current_build"):
            render_custom_behavior_gui()
            PyImGui.end_tab_item()

        PyImGui.end_tab_bar()

    PyImGui.end()
    if save_window_timer.HasElapsed(1000):
        # Position changed?
        if (end_pos[0], end_pos[1]) != (window_x, window_y):
            window_x, window_y = int(end_pos[0]), int(end_pos[1])
            ini_window.write_key(MODULE_NAME, X_POS, str(window_x))
            ini_window.write_key(MODULE_NAME, Y_POS, str(window_y))
        # Collapsed state changed?
        if new_collapsed != window_collapsed:
            window_collapsed = new_collapsed
            ini_window.write_key(MODULE_NAME, COLLAPSED, str(window_collapsed))
        save_window_timer.Reset()


def configure():
    pass


def main():
    global cached_data
    try:
        if not Routines.Checks.Map.MapValid():
            return

        cached_data.Update()
        if cached_data.data.is_map_ready and cached_data.data.is_party_loaded:
            draw_widget()

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


if __name__ == "__main__":
    main()

__all__ = ["main", "configure"]
