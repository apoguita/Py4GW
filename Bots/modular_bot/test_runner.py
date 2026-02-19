"""
Test bot: Run recipe — Eye of the North to Gunnar's Hold.

Usage: Load this script in Py4GW. Must be a Dervish/Assassin with
       the correct skills available. The bot will travel to EotN,
       equip the D/A runner build, and run to Gunnar's Hold.
"""

import sys
import os
import Py4GW

bots_dir = os.path.join(Py4GW.Console.get_projects_path(), "Bots")
if bots_dir not in sys.path:
    sys.path.insert(0, bots_dir)

from modular_bot import ModularBot, Phase
from modular_bot.recipes import Run

bot = ModularBot(
    name="Test: Runner",
    phases=[
        Run("Eye Of The North - Full Tour", "_1_Eotn_To_Gunnars"),
    ],
    loop=False,
)


def main():
    bot.update()

