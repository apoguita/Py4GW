"""
Test bot: Mission recipe — The Great Northern Wall.

The bot will:
1. Travel to the outpost (map 28)
2. Set hard mode
3. Leave party, add heroes from hero_config.json (party_4 = 3 heroes)
4. Enter the mission via EnterChallenge
5. Follow paths with combat (CB handles fighting)
6. Interact with quest NPCs, gadgets, items along the way
7. Mission concludes automatically when objectives are met

Hero configuration: edit Bots/modular_bot/missions/hero_config.json
"""

import sys
import os
import Py4GW

bots_dir = os.path.join(Py4GW.Console.get_projects_path(), "Bots")
if bots_dir not in sys.path:
    sys.path.insert(0, bots_dir)

from modular_bot import ModularBot, Phase
from modular_bot.recipes import Mission


def set_normal_mode(bot):
    bot.Party.SetHardMode(False)


bot = ModularBot(
    name="Test: Mission",
    phases=[
        Phase("Set Normal Mode", set_normal_mode),
        Mission("the_great_northern_wall"),
    ],
    loop=False,
    template="aggressive",
    use_custom_behaviors=True,
)


def main():
    bot.update()
