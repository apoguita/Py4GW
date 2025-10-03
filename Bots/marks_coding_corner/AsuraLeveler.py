from Py4GWCoreLib import *

selected_step = 0
RATA_SUM = "Rata Sum"


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


bot = Botting("Asura Leveler")


def asura_leveler(bot: Botting) -> None:
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Enable("auto_combat")
    map_id = GLOBAL_CACHE.Map.GetMapID()
    if map_id != 640:
        bot.Map.Travel(target_map_name=RATA_SUM)
        bot.Wait.ForMapLoad(target_map_name=RATA_SUM)
    bot.States.AddCustomState(AddHenchies, "Add Henchmen")
    bot.Move.XY(20340, 16899, "Exit Outpost")
    bot.Wait.ForMapLoad(target_map_name="Riven Earth")
    bot.Move.XY(-26633, -4072, "Setup Resign Spot")

    for i in range(100):
        bot.States.AddHeader("Farm Loop")
        bot.Wait.ForMapLoad(target_map_name=RATA_SUM)
        bot.Move.XY(20340, 16899, "Exit Outpost")
        bot.Wait.ForMapLoad(target_map_name="Riven Earth")
        bot.Move.XY(-24347, -5543, "Go towards the Krewe Member")
        bot.Dialogs.AtXY(-24272.00, -5719.00, 0x84, "Grab blessing")
        bot.Move.XY(-21018, -6969, "Fight outside the cave")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-20884, -8497, "Move to Cave Entrace")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-19760, -10225, "Fight in Cave 1")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-18663, -10910, "Fight in Cave 2")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-18635, -11925, "Fight in Cave 3")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-20473, -11404, "Fight in Cave 4")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-21460, -12145, "Fight in Cave 5")
        bot.Wait.UntilOutOfCombat()
        bot.Move.XY(-23755, -11391, "Fight in Cave BOSS")
        bot.Wait.UntilOutOfCombat()
        bot.Party.Resign()
        bot.States.AddCustomState(ReturnToOutpost, "Return to Outpost")


bot.SetMainRoutine(asura_leveler)


def main():
    bot.Update()
    projects_path = Py4GW.Console.get_projects_path()
    widgets_path = projects_path + "\\Bots\\marks_coding_corner\\textures\\"
    texture_icon_path = f'{widgets_path}\\dust_art.png'
    bot.UI.draw_window(icon_path=texture_icon_path)


if __name__ == "__main__":
    main()
