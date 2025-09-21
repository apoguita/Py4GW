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
        bot_instance.Map.Travel(target_map_id=639)
        bot_instance.Party.SetHardMode(True)

        bot_instance.States.AddHeader("ENTER_DUNGEONS")
        bot_instance.UI.PrintMessageToConsole("Debug", "Added header: EXIT_OUTPOST")
        bot_instance.Move.XY(-23886, 13874) #go to NPC

        bot_instance.Dialogs.AtXY(-23886, 13874, 0x84) #enter instance if quest in hand
        bot_instance.Dialogs.AtXY(-23886, 13874, 0x10) #accept quest
        bot_instance.Dialogs.AtXY(-23886, 13874, 0x18) #enter instance
        bot_instance.Wait.ForMapLoad(target_map_id=701) # we are in the dungeon

        bot_instance.States.AddHeader("DUNGEON_LOOP")
        bot_instance.UI.PrintMessageToConsole("DUNGEON_LOOP", "blessing is managed for the party by custom_behavior")

        bot_instance.Wait.ForTime(200)
        # bot_instance.Move.XY(-10480, -10938, "GO TO THE KEY")
        # # todo interract key-chest.
        # bot_instance.Move.XY(-8271, -19101, "GO TO THE END BOSS")
        # todo interract with end-chest.


        bot_instance.States.AddHeader("END")
        bot_instance.Multibox.ResignParty()
        bot_instance.Wait.ForMapLoad(target_map_id=639) # we are back in outpost
        
        # todo finalize quest.

        bot_instance.Move.XY(-22835, 6402, "REFRESH_OUTPOST")
        bot_instance.Map.Travel(target_map_id=566)

        bot_instance.Move.XY(-23139, 8233, "ENTER_OUTPOST_AGAIN")
        bot_instance.Map.Travel(target_map_id=639)

        bot_instance.UI.PrintMessageToConsole("END", "Finished routine")

        # Loop back to farm loop
        bot_instance.States.JumpToStepName("[H]MAIN_LOOP_1")


    @property
    @override
    def name(self) -> str:
        return "[REPUTATION] deldrimor"

    @property
    @override
    def description(self) -> str:
        return "farm Secret Lair of the Snowmen - This typically results in earning approximately 1,500 points per run (2,000 in hard mode)."

    def farm_coordinates(self) -> list[tuple[float, float]]:
        return [
            (17209, -15758),
            (16479, -14961),
            (16488, -14155),
            (16543, -13096),
            (16182, -12239),
            (15149, -11928),
            (13927, -11844),
            (12405, -11677),
            (11576, -11550),
            (11092, -10912),
            (10296, -10847),
            (9175, -9825),
            (9387, -9036),
            (10007, -8225),
            (10449, -7194),
            (9933, -5654),
            (10188, -5057),
            (11495, -5214),
            (12697, -7177),
            (13474, -7637),
            (15093, -8209),
            (15943, -7909),
            (16725, -7957),
            (16997, -7467),
            (16591, -6785),
            (16004, -6407),
            (14890, -4413),
            (13161, -3865),
            (11240, -4564),
            (10070, -3924),
            (9242, -2992),
            (8614, -2497),
            (7162, -1992),
            (6426, -1832),
            (6012, -1958),
            (5579, -2558),
            (4971, -3346),
            (4161, -4285),
            (3510, -5065),
            (2966, -5656),
            (2500, -6004),
            (2585, -7044),
            (2577, -8456),
            (2838, -9936),
            (2316, -10961),
            (1966, -11313),
            (880, -11090),
            (645, -8981),
            (174, -6461),
            (-399, -5250),
            (-1172, -3509),
            (-2241, -3176),
            (-3004, -2927),
            (-4013, -1080),
            (-4374, 809),
            (-4171, 2737),
            (-3867, 3853),
            (-3785, 4696),
            (-3736, 9057),
            (-4928, 10563),
            (-5579, 11195),
            (-6025, 11400),
            (-6300, 10450),
            (-6805, 9596),
            (-7995, 8760),
            (-9273, 8047),
            (-10373, 6902),
         ]

example = plant_fiber()
example.open_bot()

def main():
    example.act()

def configure():
    pass

__all__ = ["main", "configure"]