"""
modular_bot — Modular Bot Builder on top of Botting.

Build bots by composing Phase objects — each Phase is a function that
registers FSM states on a Botting instance.  ModularBot handles all
orchestration: templates, CustomBehaviors, looping, recovery, GUI.

Quick Start:
    from modular_bot import ModularBot, Phase
    from Py4GWCoreLib import Botting

    def travel(bot: Botting):
        bot.Map.Travel(target_map_id=381)
        bot.Party.SetHardMode(True)

    def farm(bot: Botting):
        bot.Move.FollowAutoPath(KILL_PATH, "Kill Route")
        bot.Wait.UntilOutOfCombat()

    def resign(bot: Botting):
        bot.Multibox.ResignParty()
        bot.Wait.ForMapToChange(target_map_id=381)

    bot = ModularBot(
        name="My Farm",
        phases=[
            Phase("Travel", travel),
            Phase("Farm",   farm),
            Phase("Resign", resign),
        ],
        loop=True,
        template="multibox_aggressive",
        use_custom_behaviors=True,
        on_party_wipe="Travel",
    )

    def main():
        bot.update()
"""

from .phase import Phase
from .bot import ModularBot

# Recipes are importable via modular_bot.recipes
# e.g.: from modular_bot.recipes import Run, Vanquish, Mission

__all__ = ["ModularBot", "Phase"]
__version__ = "1.1.0"

