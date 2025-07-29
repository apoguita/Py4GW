import os
import traceback

import Py4GW
from Py4GWCoreLib import PyImGui, IniHandler, Routines, Timer
from HeroAI.cache_data import CacheData

from Bots.aC_Scripts.Titlehelper.titlehelper_main import TitleHelper, draw_title_helper_window
from Bots.aC_Scripts.Titlehelper import ItemSelector

# === Paths and Constants ===
script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))
BASE_DIR = os.path.join(project_root, "Widgets/Config")
os.makedirs(BASE_DIR, exist_ok=True)

INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "titlehelper.ini")
MODULE_NAME = "TitleHelper - By aC"
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


def configure():
    pass


def main():
    global cached_data
    try:
        if not Routines.Checks.Map.MapValid():
            return

        cached_data.Update()
        if cached_data.data.is_map_ready and cached_data.data.is_party_loaded:
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
