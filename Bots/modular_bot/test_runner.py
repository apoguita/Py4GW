"""
Test bot: Run recipe — Eye of the North to Gunnar's Hold.

Usage: Load this script in Py4GW. Must be a Dervish/Assassin with
       the correct skills available. The bot will travel to EotN,
       equip the D/A runner build, and run to Gunnar's Hold.
"""

from Sources.modular_bot import ModularBot, Phase
from Sources.modular_bot.recipes import Run

bot = ModularBot(
    name="Test: Runner",
    phases=[
        Run("Eye Of The North - Full Tour", "_1_Eotn_To_Gunnars"),
    ],
    loop=False,
)


def main():
    bot.update()

