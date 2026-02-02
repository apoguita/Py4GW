from Py4GWCoreLib import Botting
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty

def bot_routine(bot_instance: Botting):

    CustomBehaviorParty().set_party_is_blessing_enabled(True)

    bot_instance.Templates.Routines.UseCustomBehaviors(
        on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
        on_party_death=BottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue)

    bot_instance.Templates.Aggressive()

    # Set up the FSM states properly
    bot_instance.States.AddHeader("MAIN_LOOP")
    bot_instance.Map.Travel(target_map_id=639)
    bot_instance.Party.SetHardMode(True)

    bot_instance.States.AddHeader("ENTER_DUNGEON")
    bot_instance.Move.XY(-23886, 13874, "go to NPC")
    bot_instance.Dialogs.AtXY(-23886, 13874, 0x838201) #accept quest
    bot_instance.Wait.ForTime(500)
    bot_instance.Dialogs.AtXY(-23886, 13874, 0x84) #enter instance
    bot_instance.Wait.ForMapLoad(target_map_id=701) # we are in the dungeon

    bot_instance.States.AddHeader("LOOT_DUNGEON_LOCK_KEY")
    bot_instance.Move.XY(-14603, 11927, "go to the key step0")
    bot_instance.Move.XY(-19247, 5187, "go to the key step1")
    bot_instance.Move.XY(-10307, -11027, "go to the key step2")

    bot_instance.config.FSM.AddSelfManagedYieldStep("loot the dungeon lock key.", lambda: BottingHelpers.wrapper(action=BottingHelpers.wait_until_item_looted("Dungeon Key" ,timeout_ms = 15_000), on_failure=BottingHelpers.botting_unrecoverable_issue))
    bot_instance.Wait.ForTime(2_000)

    bot_instance.States.AddHeader("OPEN_DUNGEON_LOCK")
    bot_instance.Move.XY(-15419, -12252, "go to the dungeon lock") # GadgetId=8728 IsGadget=true
    bot_instance.Interact.WithGadgetAtXY(-15419, -12252)
    bot_instance.Wait.ForTime(2_000)

    bot_instance.States.AddHeader("LOOT_BOSS_KEY")
    bot_instance.Move.XY(-13206, -17459, "go to the boss")
    bot_instance.config.FSM.AddSelfManagedYieldStep("loot the boss key.", lambda: BottingHelpers.wrapper(action=BottingHelpers.wait_until_item_looted("Boss Key" ,timeout_ms = 15_000), on_failure=BottingHelpers.botting_unrecoverable_issue))

    bot_instance.States.AddHeader("OPEN_BOSS_LOCK")
    bot_instance.Move.XY(-11162, -18054, "go to the boss lock") # GadgetId=8730 IsGadget=true
    bot_instance.Interact.WithGadgetAtXY(-11162, -18054)
    bot_instance.Wait.ForTime(2_000)

    bot_instance.States.AddHeader("END_CHEST")
    bot_instance.Move.XY(-7851, -19001, "GO TO THE END CHEST") # GadgetId=9274 IsGadget=true
    # looting is a simple custom_behavior.utility_skill : open_near_dungeon_chest_utility
    bot_instance.Wait.ForTime(120_000)

    bot_instance.States.AddHeader("RESIGN")
    bot_instance.config.FSM.AddSelfManagedYieldStep( "wait for party resign.", lambda: BottingHelpers.wrapper(action=BottingHelpers.wait_until_party_resign(timeout_ms = 50_000), on_failure=BottingHelpers.botting_unrecoverable_issue))
    bot_instance.Wait.ForMapLoad(target_map_id=639) # we are back in outpost

    bot_instance.States.AddHeader("FINALIZE_QUEST")
    bot_instance.Move.XY(-23886, 13874, "go to NPC.")
    bot_instance.Dialogs.AtXY(-23886, 13874, 0x838207, "finalize the quest.")

    bot_instance.States.AddHeader("REFRESH_OUTPOST")
    bot_instance.Move.XY(-22835, 6402, "refresh the outpost.")
    bot_instance.Wait.ForMapLoad(target_map_id=566)

    bot_instance.States.AddHeader("ENTER_OUTPOST_AGAIN")
    bot_instance.Move.XY(-23139, 8233, "enter outpost again.")
    bot_instance.Wait.ForMapLoad(target_map_id=639)

    # Loop back to farm loop
    bot_instance.States.JumpToStepName("[H]MAIN_LOOP_1")

    bot_instance.States.AddHeader("END")

bot = Botting("[DUNGEON] Secret Lair of the Snowmen")
bot.SetMainRoutine(bot_routine)

def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()