from Sources.Sasemoi.utils.inventory_utils import filter_valuable_rune_type
from Py4GWCoreLib import Routines, Console
from Py4GWCoreLib import Botting
from Py4GWCoreLib import GLOBAL_CACHE

bot = Botting(
    "ID Rune Testing Bot",
)

def create_bot_routine(bot: Botting) -> None:
    InitBot(bot)


def InitBot(bot: Botting) -> None:
    bot.States.AddHeader("Init Bot")
    bot.States.AddCustomState(lambda: TestIDRunes(), "Test Rune Identifying")

def TestIDRunes():
    rarities = ["Purple", "Gold"]
    all_items = Routines.Items.GetSalvageableItems(rarities=rarities, slot_blacklist=[])

    for item_id in all_items:
        Console.Log('Test Rune Identifying', f"Found salvageable item ID: {item_id}", Console.MessageType.Info)

    valuable_runes = [item_id for item_id in all_items if filter_valuable_rune_type(item_id)]

    for item_id in valuable_runes:
        Console.Log('Test Rune Identifying', f"Identified valuable rune item ID: {item_id}", Console.MessageType.Info)

bot.SetMainRoutine(create_bot_routine)
base_path = Console.get_projects_path()


def configure():
    global bot
    bot.UI.draw_configure_window()

def main():
    bot.Update()
    projects_path = Console.get_projects_path()
    widgets_path = projects_path + "\\Widgets\\Config\\textures\\"
    bot.UI.draw_window(icon_path=widgets_path + "YAVB 2.0 mascot.png")

if __name__ == "__main__":
    main()
