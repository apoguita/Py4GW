import os
import traceback

import Py4GW
from Py4GWCoreLib import PyImGui, IniHandler, Routines, Timer, Color, ImGui
from HeroAI.cache_data import CacheData

from Sources.aC_Scripts.Titlehelper.titlehelper_main import TitleHelper, draw_title_helper_window
from Sources.aC_Scripts.Titlehelper import ItemSelector

# === Paths and Constants ===
script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = Py4GW.Console.get_projects_path()
BASE_DIR = os.path.join(project_root, "Widgets/Config")
os.makedirs(BASE_DIR, exist_ok=True)

INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "titlehelper.ini")
MODULE_NAME = "TitleHelper - By aC"
MODULE_ICON = "Textures/Module_Icons/TitleHelper.png"
COLLAPSED = "collapsed"
X_POS = "x"
Y_POS = "y"

# === Persistent Window State ===
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()
first_run = True
window_x = ini_window.read_int(MODULE_NAME, X_POS, 100)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 100)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)

# === TitleHelper State ===
title_helper = TitleHelper()
title_helper_runner = title_helper.run()
cached_data = CacheData()


def draw_widget(cached_data):
    global first_run, window_x, window_y, window_collapsed

    if first_run:
        PyImGui.set_next_window_pos(window_x, window_y)
        PyImGui.set_next_window_collapsed(window_collapsed, 0)
        first_run = False

    is_window_opened = PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize)
    new_collapsed = PyImGui.is_window_collapsed()
    end_pos = PyImGui.get_window_pos()

    if is_window_opened:
        draw_title_helper_window(title_helper)

    PyImGui.end()

    if save_window_timer.HasElapsed(1000):
        if (end_pos[0], end_pos[1]) != (window_x, window_y):
            window_x, window_y = int(end_pos[0]), int(end_pos[1])
            ini_window.write_key(MODULE_NAME, X_POS, str(window_x))
            ini_window.write_key(MODULE_NAME, Y_POS, str(window_y))

        if new_collapsed != window_collapsed:
            window_collapsed = new_collapsed
            ini_window.write_key(MODULE_NAME, COLLAPSED, str(window_collapsed))
        save_window_timer.Reset()


def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("TitleHelper", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A comprehensive automation suite for tracking and completing")
    PyImGui.text("various in-game titles. This widget streamlines the grind for")
    PyImGui.text("account-wide achievements and specialized title tracks.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Title Tracking: Real-time progress monitoring for active title goals")
    PyImGui.bullet_text("Item Selector: Integrated utility for choosing specific items for title tasks")
    PyImGui.bullet_text("Automation: Handles repetitive actions required for title advancement")
    PyImGui.bullet_text("State Persistence: Automatically saves window position and collapsed state")
    PyImGui.bullet_text("HeroAI Sync: Leverages shared cache data for optimized party coordination")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by aC")

    PyImGui.end_tooltip()


def main():
    global cached_data
    try:
        if not Routines.Checks.Map.MapValid():
            return

        cached_data.Update()
        if Routines.Checks.Map.IsMapReady() and Routines.Checks.Party.IsPartyLoaded():
            draw_widget(cached_data)

        if ItemSelector.show_item_selector:
            ItemSelector.draw_item_selector_window()

        try:
            next(title_helper_runner)
        except StopIteration:
            pass

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, traceback.format_exc(), Py4GW.Console.MessageType.Error)


if __name__ == "__main__":
    main()
