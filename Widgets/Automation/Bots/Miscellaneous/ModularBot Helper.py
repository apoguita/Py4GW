"""
ModularBot Helper widget entry point.

This thin wrapper exposes Sources.modular_bot.tools.script_helper
through the Widgets tree so it can be launched from Widget Manager.
"""

from Sources.modular_bot.tools import script_helper


module_name = "ModularBot Helper"
MODULE_NAME = "ModularBot Helper"


def main():
    script_helper.main()

