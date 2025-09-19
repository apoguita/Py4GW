import traceback
from typing import Any, Generator, override
from Py4GWCoreLib import Botting
from Py4GWCoreLib.py4gwcorelib_src.Lootconfig import LootConfig
from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers

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
        # self.bot_instance.States.AddCustomState(Helpers.MoveToXY_ExitIfMapReached(-5281, -2562,target_map_id=397))

        bot_instance.States.AddHeader("MOVE_TO_FARM_AREA") #todo correct name
        bot_instance.Move.XY(17726, 9465)
        bot_instance.Wait.ForTime(2000)
        bot_instance.Wait.ForMapLoad(target_map_id=395)

        bot_instance.States.AddHeader("FARM_LOOP")
        bot_instance.Move.XY(-15945.758926908922, -14193.140128347102)
        bot_instance.Move.XY(-16474.226274278495, -11890.508443287788)
        bot_instance.Move.XY(-17747.3456838063, -8172.717630729574)
        bot_instance.Move.XY(-18155.70511768495, -3207.6666679551563)
        bot_instance.Move.XY(-14684.095854129337, 3425.280139882794)
        bot_instance.Move.XY(-13880.210079844823, 7213.710867016402)
        bot_instance.Move.XY(-9293.665352322569, 7858.369597264538)
        bot_instance.Move.XY(-9063.060237582613, 10966.922552660926)
        bot_instance.Move.XY(-10504.327260726757, 13154.438269538)
        bot_instance.Move.XY(-7228.23388671875, 13492.703125)
        bot_instance.Move.XY(-13386.868454136275, 14046.70835345806)
        bot_instance.Move.XY(-14437.8974609375, 4886.30908203125)
        bot_instance.Move.XY(-17078.712890625, 5621.9609375)
        bot_instance.Move.XY(-16845.913987797947, 2504.766615792578)
        bot_instance.Move.XY(-16930.170797287632, -178.76817294911234)
        bot_instance.Move.XY(-20389.21698068759, -1301.2983356849945)
        bot_instance.Move.XY(-20879.248301342013, -2395.049599894999)
        bot_instance.Move.XY(-18602.042935171732, -4640.115703488522)
        bot_instance.Move.XY(-15829.27600849414, -13904.416874455408)
        bot_instance.Move.XY(-18458, -16135)

        # todo the farm loop
        bot_instance.Wait.ForMapLoad(target_map_id=397)
        bot_instance.Wait.ForTime(2000)
        
        # Loop back to farm loop
        bot_instance.States.JumpToStepName("[H]MOVE_TO_FARM_AREA_3")

    @property
    @override
    def name(self) -> str:
        return "nick_pillaged_goods"

    @property
    @override
    def description(self) -> str:
        return "farm nick_pillaged_goods"

example = nick_pillaged_goods()
def main():
    example.act()

def configure():
    pass

__all__ = ["main", "configure"]


# [
# (-15945.758926908922, -14193.140128347102),
# (-16474.226274278495, -11890.508443287788),
# (-17747.3456838063, -8172.717630729574),
# (-18155.70511768495, -3207.6666679551563),
# (-14684.095854129337, 3425.280139882794),
# (-13880.210079844823, 7213.710867016402),
# (-9293.665352322569, 7858.369597264538),
# (-9063.060237582613, 10966.922552660926),
# (-10504.327260726757, 13154.438269538),
# (-7228.23388671875, 13492.703125),
# (-13386.868454136275, 14046.70835345806),
# (-14437.8974609375, 4886.30908203125),
# (-17078.712890625, 5621.9609375),
# (-16845.913987797947, 2504.766615792578),
# (-16930.170797287632, -178.76817294911234),
# (-20389.21698068759, -1301.2983356849945),
# (-20879.248301342013, -2395.049599894999),
# (-18602.042935171732, -4640.115703488522),
# (-15829.27600849414, -13904.416874455408),
# (-18458, -16135),
# ]