from typing import Any, Generator, override
from Py4GWCoreLib import Botting, Item
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.py4gwcorelib_src.Lootconfig import LootConfig
from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers


class secret_lair_of_the_snowmen(BottingAbstract):
    def __init__(self):
        super().__init__()

    @override
    def bot_routine(self, bot_instance: Botting):
        # Set up the FSM states properly
        bot_instance.States.AddHeader("MAIN_LOOP")
        bot_instance.Map.Travel(target_map_id=639)
        bot_instance.Party.SetHardMode(True)

        bot_instance.States.AddHeader("ENTER_DUNGEON")
        bot_instance.UI.PrintMessageToConsole("Debug", "Added header: ENTER_DUNGEON")
        bot_instance.Move.XY(-23886, 13874) #go to NPC
        bot_instance.Dialogs.AtXY(-23886, 13874, 0x838201) #accept quest
        bot_instance.Wait.ForTime(1000)
        bot_instance.Dialogs.AtXY(-23886, 13874, 0x84) #enter instance
        bot_instance.Wait.ForMapLoad(target_map_id=701) # we are in the dungeon

        bot_instance.States.AddHeader("LOOT_DUNGEON_LOCK_KEY")
        bot_instance.Move.XY(-19247, 5187, "GO TO THE KEY step1")
        bot_instance.Move.XY(-10307, -11027, "GO TO THE KEY step2")
        bot_instance.Interact.WithItemAtXY(-10307, -11027)  # ItemId=196 IsItem=true IsGadget=False
        key_agent_id = GLOBAL_CACHE.Item.GetAgentID(196)
        # GLOBAL_CACHE.Player.Interact(key_agent_id, False)
        bot_instance.Wait.ForTime(2000)

        bot_instance.States.AddHeader("OPEN_DUNGEON_LOCK")
        bot_instance.Move.XY(-15428, -12148, "GO TO THE DUNGEON LOCK") # GadgetId=8728 IsGadget=true
        bot_instance.Interact.WithGadgetAtXY(-15428, -12148)
        bot_instance.Wait.ForTime(2_000)

        bot_instance.States.AddHeader("LOOT_BOSS_KEY")
        bot_instance.Move.XY(-13206, -17459, "GO TO THE BOSS")
        boss_key_agent_id = GLOBAL_CACHE.Item.GetAgentID(34) # ItemId=34 IsItem=true
        GLOBAL_CACHE.Player.Interact(boss_key_agent_id, False)

        # OPEN BOSS LOCK
        bot_instance.States.AddHeader("OPEN_BOSS_LOCK")
        bot_instance.Move.XY(-11286, -18139, "GO TO THE BOSS LOCK") # GadgetId=8730 IsGadget=true
        bot_instance.Interact.WithGadgetAtXY(-11286, -18139)
        bot_instance.Wait.ForTime(2_000)
        
        # GO TO END CHEST
        bot_instance.Move.XY(-7851, -19001, "GO TO THE END CHEST") # GadgetId=9274 IsGadget=true
        bot_instance.Wait.ForTime(60_000)

        bot_instance.States.AddHeader("END")
        bot_instance.Multibox.ResignParty()
        bot_instance.Wait.ForMapLoad(target_map_id=639) # we are back in outpost
        bot_instance.UI.PrintMessageToConsole("Debug", "Looting the end chest is managed by a custom_behavior.")
        
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
        return "[DONGEON] Secret Lair of the Snowmen"

    @property
    @override
    def description(self) -> str:
        return "farm Secret Lair of the Snowmen - This typically results in earning approximately 1,500 points per run (2,000 in hard mode)."

example = secret_lair_of_the_snowmen()
example.open_bot()

def main():
    example.act()

def configure():
    pass

__all__ = ["main", "configure"]