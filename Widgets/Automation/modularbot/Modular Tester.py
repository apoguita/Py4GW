"""
Modular Tester widget entry point.

Thin wrapper that exposes Sources.modular_data.tools.test_modular_blocks
inside the Widgets tree.
"""

import PyImGui

from Sources.modular_data.tools import test_modular_blocks
from Py4GWCoreLib.modular.widget_runtime import guarded_widget_main


MODULE_NAME = "Modular Tester"
MODULE_ICON = "Textures/Module_Icons/Route Planner.png"
MODULE_TAGS = ["Automation", "modular_bot"]


def main():
    guarded_widget_main(
        MODULE_NAME,
        test_modular_blocks.main,
        get_bot=test_modular_blocks.get_bot,
    )


def tooltip():
    PyImGui.set_next_window_size((430, 0))
    PyImGui.begin_tooltip()
    PyImGui.text(MODULE_NAME)
    PyImGui.separator()
    PyImGui.text_wrapped(
        "Run modular blocks by kind/folder/recipe selection with one-click start."
    )
    PyImGui.text_wrapped(
        "Wrapper for Sources/modular_data/tools/test_modular_blocks.py"
    )
    PyImGui.end_tooltip()


if __name__ == "__main__":
    main()
