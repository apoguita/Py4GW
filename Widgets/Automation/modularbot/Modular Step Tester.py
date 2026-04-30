"""
Modular Step Tester widget entry point.

Thin wrapper that exposes Sources.modular_data.tools.step_tester.
"""
import PyImGui

from Sources.modular_data.tools import step_tester
from Py4GWCoreLib.modular.widget_runtime import guarded_widget_main


MODULE_NAME = "Modular Step Tester"
MODULE_ICON = "Textures/Module_Icons/Route Planner.png"
MODULE_TAGS = ["Automation", "modular_bot"]


def main():
    guarded_widget_main(
        MODULE_NAME,
        step_tester.main,
        get_bot=step_tester.get_bot,
    )


def tooltip():
    PyImGui.set_next_window_size((430, 0))
    PyImGui.begin_tooltip()
    PyImGui.text(MODULE_NAME)
    PyImGui.separator()
    PyImGui.text_wrapped("Run one registered modular step with editable params.")
    PyImGui.text_wrapped("Wrapper for Sources/modular_data/tools/step_tester.py")
    PyImGui.end_tooltip()


if __name__ == "__main__":
    main()
