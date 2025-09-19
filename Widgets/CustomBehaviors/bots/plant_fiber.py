from typing import Any, Generator, override
from Py4GWCoreLib import Botting
from Py4GWCoreLib.py4gwcorelib_src.Lootconfig import LootConfig
from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers


class plant_fiber(BottingAbstract):
    def __init__(self):
        super().__init__()

    @override
    def bot_routine(self, bot_instance: Botting):
        # Set up the FSM states properly
        bot_instance.States.AddHeader("MAIN_LOOP")
        bot_instance.Map.Travel(target_map_id=396)
        bot_instance.Party.SetHardMode(True)

        bot_instance.States.AddHeader("EXIT_OUTPOST")
        bot_instance.UI.PrintMessageToConsole("Debug", "Added header: EXIT_OUTPOST")
        bot_instance.Move.XY(-2086, 6664, "Exit Outpost")
        bot_instance.Wait.ForMapLoad(target_map_id=395)

        bot_instance.States.AddHeader("END")
        bot_instance.UI.PrintMessageToConsole("END", "Finished routine")

    @property
    @override
    def name(self) -> str:
        return "plant_fiber [WIP]"

    @property
    @override
    def description(self) -> str:
        return "farm plant_fiber but it's still WIP"

example = plant_fiber()
example.open_bot()

def main():
    example.act()

def configure():
    pass

__all__ = ["main", "configure"]

