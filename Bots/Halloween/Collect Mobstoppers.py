from Py4GWCoreLib import Botting, Py4GW, Routines, GLOBAL_CACHE

bot = Botting("Mobstopper Collector")

STEWARD_ID = 147
QUEST_SELECT = 0x846303
QUEST_ACCEPT = 0x846301
QUEST_ID = 1123


def create_bot_routine(bot: Botting) -> None:
    TravelToLionsArch(bot)
    free_slots_in_inventory = GLOBAL_CACHE.Inventory.GetFreeSlotCount()

    iterations = free_slots_in_inventory * 83
    bot.States.AddHeader(f"Mobstoppers {iterations} Cycles")
    for _ in range(iterations):
        bot.States.AddHeader(f"Take and Abandon Quest")
        TakeQuest(bot)
        bot.Wait.ForTime(1)
        AbandonQuest(bot)

    bot.States.AddHeader("Done")
    bot.Stop()


def TravelToLionsArch(bot: Botting) -> None:
    bot.States.AddHeader("Travel to Lion's Arch")
    bot.Map.Travel(target_map_id=808)
    bot.Move.XY(5332.00, 9048.00, "Move to Steward")


def TakeQuest(bot: Botting) -> None:
    bot.Dialogs.WithModel(STEWARD_ID, QUEST_SELECT, "Talk to Steward")
    bot.Dialogs.WithModel(STEWARD_ID, QUEST_ACCEPT, "Accept Quest")


def AbandonQuest(bot: Botting):
    def _abandon_gen():
        bot.Quests.Abandon(QUEST_ID)

    bot.States.AddCustomState(_abandon_gen, "AbandonQuestState")


bot.SetMainRoutine(create_bot_routine)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=None)


if __name__ == "__main__":
    main()
