import traceback
from typing import Any, Generator, override
from Py4GWCoreLib import Botting
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.py4gwcorelib_src.Lootconfig_src import LootConfig
from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract
from Widgets.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers

from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers

class nick_pillaged_goods(BottingAbstract):
    def __init__(self):
        super().__init__()

    @override
    def bot_routine(self, bot_instance: Botting):

        bot_instance.States.AddHeader("MAIN_LOOP")
        bot_instance.Map.Travel(target_map_id=213)
        bot_instance.Party.SetHardMode(False)

        bot_instance.States.AddHeader("EXIT_OUTPOST")
        bot_instance.UI.PrintMessageToConsole("Debug", "Added header: EXIT_OUTPOST")
        bot_instance.Move.XY(19453, 14369, "Exit Outpost")
        bot_instance.Wait.ForMapLoad(target_map_id=237)

        bot_instance.States.AddHeader("FARM_LOOP")
        for farm_coordinate in self.farm_coordinates():
            bot_instance.Move.XY(farm_coordinate[0], farm_coordinate[1])

        bot_instance.States.AddHeader("RESIGN")
        bot_instance.config.FSM.AddSelfManagedYieldStep( "wait for party resign.", lambda: BottingHelpers.wrapper(action=BottingHelpers.wait_until_party_resign(timeout_ms = 50_000), on_failure=self.botting_unrecoverable_issue))
        bot_instance.Wait.ForMapLoad(target_map_id=213) # we are back in outpost
        
        # Loop back to farm loop
        bot_instance.States.JumpToStepName("[H]MAIN_LOOP_1")

        bot_instance.States.AddHeader("END")

    @property
    @override
    def name(self) -> str:
        return "[NICK] gold_crimson_skull"

    @property
    @override
    def description(self) -> str:
        return "farm [NICK] gold_crimson_skull"

    def farm_coordinates(self) -> list[tuple[float, float]]:
        return [ (11408, -16978), (7103, -16858), (7455, -13737), (5217, -5943), (4353, -3805), (5981, -1130), (9768, -59), (6889, 519), (7568, 4493), (6366, 5916), (8217, 5118), (9056, 6211), (11050, 6758), (6966, 9630) ]