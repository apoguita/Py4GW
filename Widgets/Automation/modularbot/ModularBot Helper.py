"""
Modular Coder Assistant widget entry point.

This thin wrapper exposes Sources.modular_data.tools.script_helper
through the Widgets tree so it can be launched from Widget Manager.
"""

from Sources.modular_data.tools import script_helper
from Py4GWCoreLib.modular.widget_runtime import guarded_widget_main


module_name = "Modular Coder Assistant"
MODULE_NAME = "Modular Coder Assistant"
MODULE_TAGS = ["Automation", "modular_bot"]


def main():
    guarded_widget_main(MODULE_NAME, script_helper.main)
