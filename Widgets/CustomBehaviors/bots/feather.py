from typing import Any, Generator, override
from Py4GWCoreLib import Botting
from Py4GWCoreLib.py4gwcorelib_src.Lootconfig import LootConfig
from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers


class feather(BottingAbstract):
    def __init__(self):
        super().__init__()

    @override
    def bot_routine(self, bot_instance: Botting):
        # Set up the FSM states properly
        bot_instance.States.AddHeader("MAIN_LOOP")
        bot_instance.Map.Travel(target_map_id=250)
        bot_instance.Party.SetHardMode(True)

        bot_instance.States.AddHeader("EXIT_OUTPOST")
        bot_instance.UI.PrintMessageToConsole("Debug", "Added header: EXIT_OUTPOST")
        bot_instance.Move.XY(16570, 17713, "Exit Outpost")
        bot_instance.Wait.ForMapLoad(target_map_id=196)

        bot_instance.States.AddHeader("FARM LOOP")

        for farm_coordinate in self.farm_coordinates():
            bot_instance.Move.XY(farm_coordinate[0], farm_coordinate[1])

        bot_instance.States.AddHeader("END")
        bot_instance.Multibox.ResignParty()
        bot_instance.UI.PrintMessageToConsole("END", "Finished routine")

        # Loop back to farm loop
        bot_instance.States.JumpToStepName("[H]MAIN_LOOP_1")

    @property
    @override
    def name(self) -> str:
        return "[FARM] feather"

    @property
    @override
    def description(self) -> str:
        return "farm feather"

    def farm_coordinates(self) -> list[tuple[float, float]]:
        return [
            (9000, -12680),
            (7588, -10609),
            (2900, -9700),
            (1540, -6995),
            (-472, -4342),
            (-1536, -1686),
            (586, -76),
            (-1556, 2786),
            (-2229, -815),
            (-5247, -3290),
            (-6994, -2273),
            (-5042, -6638),
            (-11040, -8577),
            (-10860, -2840),
            (-14900, -3000),
            (-12200, 150),
            (-12500, 4000),
            (-12111, 1690),
            (-10303, 4110),
            (-10500, 5500),
            (-9700, 2400)
         ]

