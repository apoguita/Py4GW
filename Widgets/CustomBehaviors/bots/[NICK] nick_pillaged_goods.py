import traceback
from typing import Any, Generator, override
from Py4GWCoreLib import Botting
from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract

class nick_pillaged_goods(BottingAbstract):
    def __init__(self):
        super().__init__()

    @override
    def bot_routine(self, bot_instance: Botting):
        # Set up the FSM states properly

        bot_instance.States.AddHeader("MAIN_LOOP")
        bot_instance.Map.Travel(target_map_id=476)
        bot_instance.Party.SetHardMode(False)

        bot_instance.States.AddHeader("EXIT_OUTPOST")
        bot_instance.UI.PrintMessageToConsole("Debug", "Added header: EXIT_OUTPOST")
        bot_instance.Move.XY(-5281, -2562, "Exit Outpost")
        bot_instance.Wait.ForMapLoad(target_map_id=397)

        bot_instance.States.AddHeader("MOVE_TO_FARM_AREA")
        bot_instance.Move.XY(17726, 9465)
        bot_instance.Wait.ForTime(2000)
        bot_instance.Wait.ForMapLoad(target_map_id=395)

        bot_instance.States.AddHeader("FARM_LOOP")
        for farm_coordinate in self.farm_coordinates():
            bot_instance.Move.XY(farm_coordinate[0], farm_coordinate[1])

        bot_instance.Wait.ForMapLoad(target_map_id=397)
        bot_instance.Wait.ForTime(2000)
        
        # Loop back to farm loop
        bot_instance.States.JumpToStepName("[H]MOVE_TO_FARM_AREA_3")

    @property
    @override
    def name(self) -> str:
        return "[NICK] pillaged_goods"

    @property
    @override
    def description(self) -> str:
        return "farm nick_pillaged_goods"

    def farm_coordinates(self) -> list[tuple[float, float]]:
        return [
            (-15945.758926908922, -14193.140128347102),
            (-16474.226274278495, -11890.508443287788),
            (-17747.3456838063, -8172.717630729574),
            (-18155.70511768495, -3207.6666679551563),
            (-14684.095854129337, 3425.280139882794),
            (-13880.210079844823, 7213.710867016402),
            (-9293.665352322569, 7858.369597264538),
            (-9063.060237582613, 10966.922552660926),
            (-10504.327260726757, 13154.438269538),
            (-7228.23388671875, 13492.703125),
            (-13386.868454136275, 14046.70835345806),
            (-14437.8974609375, 4886.30908203125),
            (-17078.712890625, 5621.9609375),
            (-16845.913987797947, 2504.766615792578),
            (-16930.170797287632, -178.76817294911234),
            (-20389.21698068759, -1301.2983356849945),
            (-20879.248301342013, -2395.049599894999),
            (-18602.042935171732, -4640.115703488522),
            (-15829.27600849414, -13904.416874455408),
            (-18458, -16135),
        ]