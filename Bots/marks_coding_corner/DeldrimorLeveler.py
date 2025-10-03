from Py4GWCoreLib import *

selected_step = 0
DOOMLORE_SHRINE = "Doomlore Shrine"


def AddHenchies():
    for i in range(1, 8):
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(i)
        yield from Routines.Yield.wait(250)


def ReturnToOutpost():
    yield from Routines.Yield.wait(4000)
    is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
    is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
    is_explorable = GLOBAL_CACHE.Map.IsExplorable()
    is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated()

    if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
        GLOBAL_CACHE.Party.ReturnToOutpost()
        yield from Routines.Yield.wait(4000)


bot = Botting("Deldrimor Leveler")


def deldrimor_leveler(bot: Botting) -> None:
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Enable("auto_combat")
    map_id = GLOBAL_CACHE.Map.GetMapID()
    if map_id != 648:
        bot.Map.Travel(target_map_name=DOOMLORE_SHRINE)
        bot.Wait.ForMapLoad(target_map_name=DOOMLORE_SHRINE)
    bot.States.AddCustomState(AddHenchies, "Add Henchmen")
    bot.Move.XY(-18579, 17984, 'Move to NPC')
    bot.Dialogs.AtXY(-19166.00, 17980.00, 0x832101, "Temple of the damned Quest")  # Temple of the damned quest 0x832101
    bot.Dialogs.AtXY(-19166.00, 17980.00, 0x88, "Enter COF Level 1")  # Enter COF Level 1

    bot.Wait.ForMapLoad(target_map_name="Cathedral of Flames (level 1)")

    bot.Move.XY(-20250, -7333, "Setup Resign Spot")

    for i in range(100):
        bot.States.AddHeader("Farm Loop")
        bot.Wait.ForMapLoad(target_map_name=DOOMLORE_SHRINE)
        bot.Dialogs.AtXY(-19166.00, 17980.00, 0x832101, "Temple of the damned Quest")  # Temple of the damned quest 0x832101
        bot.Dialogs.AtXY(-19166.00, 17980.00, 0x88, "Enter COF Level 1")  # Enter COF Level 1
        bot.Wait.ForMapLoad(target_map_name="Cathedral of Flames (level 1)")
        bot.Move.XY(-18295.50, -8614.49, "Move towards shrine")
        bot.Dialogs.AtXY(-18250.00, -8595.00, 0x84)
        bot.Move.XY(-17734, -9195, "Fight in entrance")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-15477, -8560, "Fight at Spot 1")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-15736, -6609, "Fight at Spot 2")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-14748, -3623, "Fight at Spot 3")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-13126, -3364, "Fight at Spot 4")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-12350, -1648, "Fight at Spot 5")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-12162, -1413, "Fight at Spot 6")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-10869, -2, "Fight at Spot 7")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-10728, 420, "Fight at Spot 8")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-12632, 3241, "Fight at Spot 9")
        bot.Wait.UntilOutOfCombat()
        bot.Party.Resign()
        bot.States.AddCustomState(ReturnToOutpost, "Return to Doomlore")


bot.SetMainRoutine(deldrimor_leveler)


def main():
    bot.Update()
    projects_path = Py4GW.Console.get_projects_path()
    widgets_path = projects_path + "\\Bots\\marks_coding_corner\\textures\\"
    texture_icon_path = f'{widgets_path}\\cof_art.png'
    bot.UI.draw_window(icon_path=texture_icon_path)


if __name__ == "__main__":
    main()
