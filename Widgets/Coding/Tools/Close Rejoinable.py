from datetime import datetime, timedelta
import os

import Py4GW
import PyImGui


from Py4GWCoreLib import ImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler


project_path = Py4GW.Console.get_projects_path()
MODULE_NAME = "Close Rejoinable"
MODULE_ICON = os.path.join("Textures", "Module_Icons", "Research Code.png")

widget_manager = get_widget_handler()

enqueued = False
started_at = datetime.now()
popup_requested = False
CONFIRM_POPUP_ID = "Close Rejoinable Confirmation##close_rejoinable_confirm"


def FreezeAndCloseRejoinable():
    while True:
        if datetime.now() - started_at > timedelta(milliseconds=50):
            #kill process
            os._exit(0)
        pass


def _disable_widget_only():
    widget_manager.disable_widget(MODULE_NAME)


def _enqueue_close():
    global enqueued, started_at

    if enqueued:
        return

    started_at = datetime.now()
    widget_manager.disable_widget(MODULE_NAME)
    GLOBAL_CACHE._ActionQueueManager.AddAction("ACTION", None)
    GLOBAL_CACHE._ActionQueueManager.AddAction("ACTION", None)

    GLOBAL_CACHE._ActionQueueManager.AddAction("TRANSITION", None)
    GLOBAL_CACHE._ActionQueueManager.AddAction("TRANSITION", None)

    GLOBAL_CACHE._ActionQueueManager.AddAction("ACTION", FreezeAndCloseRejoinable)
    GLOBAL_CACHE._ActionQueueManager.AddAction("TRANSITION", FreezeAndCloseRejoinable)
    enqueued = True


color_red = (1.0, 0.2, 0.2, 1.0)
def _draw_confirmation_popup():
    global popup_requested
    
    PyImGui.open_popup(CONFIRM_POPUP_ID)
    PyImGui.set_next_window_size((400, 0), PyImGui.ImGuiCond.Always)
    
    if not PyImGui.begin_popup_modal(CONFIRM_POPUP_ID, True, PyImGui.WindowFlags.AlwaysAutoResize):
        return

    ImGui.text_colored("Warning!", color=color_red, font_size=18)
    ImGui.text_wrapped("This will close the current Guild Wars client in a way to be able to rejoin the same instance if retried within a few minutes. You have to login with the same character for this to work!")
    PyImGui.spacing()
    ImGui.text_colored("Do you really want to close the Guild Wars client?", color=color_red, font_style="Bold", font_size=14)

    width = PyImGui.get_content_region_avail()[0]
    if PyImGui.button("YES", width=(width - 5) / 2):
        _enqueue_close()
        PyImGui.close_current_popup()
    ImGui.show_tooltip("This will close the Guild Wars client.")
    
    PyImGui.same_line(0, 5)

    if PyImGui.button("NO", width=(width - 5) / 2):
        _disable_widget_only()
        PyImGui.close_current_popup()
    ImGui.show_tooltip("This will keep your current Guild Wars client alive.")
    
    PyImGui.end_popup_modal()
    
def tooltip():
    PyImGui.set_next_window_size((400, 0))
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.image(MODULE_ICON, (32, 32))
    PyImGui.same_line(0, 10)
    ImGui.push_font("Regular", 20)
    ImGui.text_aligned(MODULE_NAME, alignment=Alignment.MidLeft, color=title_color.color_tuple, height=32)
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    ImGui.text_colored("Warning!", color=color_red, font_size=18)
    ImGui.text_wrapped("This widget will close the current Guild Wars client in a way to be able to rejoin the same instance if retried within a few minutes. You have to login with the same character for this to work!")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by frenkey")

    PyImGui.end_tooltip()
    
def main():
    if enqueued:
        return

    _draw_confirmation_popup()

if __name__ == "__main__":
    main()
