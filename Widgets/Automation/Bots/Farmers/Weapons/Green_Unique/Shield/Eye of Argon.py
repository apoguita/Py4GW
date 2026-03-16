import os
from Py4GWCoreLib import Botting

MODULE_NAME = "Eye of Argon shield"
MODULE_ICON = "Textures\\Module_Icons\\Darkroot's Daggers.png"

class BotSettings:
    BOT_NAME = "Eye of Argon shield Farm"
    OUTPOST_TO_TRAVEL = 387
    COORD_TO_EXIT_MAP = [
        (-419,4024),
    ]
    TRANSIT_EXPLORABLE = 436
    TRANSIT_PATH = [
        (5316,7722),
    ]
    EXPLORABLE_TO_TRAVEL = 369
    KILLING_PATH = [
    (-6988,8797),
    (-5883,9168),
    (-4752,8737),
    (-4599,5727),
    (-8331,-1268),
]

bot = Botting(BotSettings.BOT_NAME)

def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BotSettings.BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=BotSettings.OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BotSettings.BOT_NAME}_loop")
    bot.Party.SetHardMode(False)
    bot.Move.FollowPathAndExitMap(BotSettings.COORD_TO_EXIT_MAP, target_map_id=BotSettings.TRANSIT_EXPLORABLE)
    bot.Move.FollowAutoPath(BotSettings.TRANSIT_PATH)
    bot.Wait.ForMapToChange(BotSettings.EXPLORABLE_TO_TRAVEL)
    bot.Move.FollowAutoPath(BotSettings.KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName(f"[H]{BotSettings.BOT_NAME}_loop_3")

bot.SetMainRoutine(bot_routine)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(BotSettings.BOT_NAME + " bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi-account bot to " + BotSettings.BOT_NAME)
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("Sunspear Sanctuary outpost")

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Aura")
    PyImGui.end_tooltip()

TEXTURE = MODULE_ICON

def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)

if __name__ == "__main__":
    main()
