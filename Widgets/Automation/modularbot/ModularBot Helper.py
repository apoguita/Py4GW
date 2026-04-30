"""
Modular Coder Assistant widget entry point.

This thin wrapper exposes Sources.modular_bot.tools.script_helper
through the Widgets tree so it can be launched from Widget Manager.
"""

from Sources.modular_bot.tools import script_helper


module_name = "Modular Coder Assistant"
MODULE_NAME = "Modular Coder Assistant"
MODULE_TAGS = ["Automation", "modular_bot"]


def main():
    script_helper.main()

