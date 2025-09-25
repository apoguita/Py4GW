from Py4GWCoreLib import *
bot = Botting("Dwarven_Stability")
def Routine(bot: Botting) -> None:
    bot.Map.Travel(target_map_name="Sifhalla")
    bot.Wait.ForMapLoad(target_map_id=643)
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Enable("auto_combat")
    bot.Move.XYAndDialog(12009, 24726, 0x837E03) #Big Unfriendly Jotun
    bot.Dialogs.AtXY(12009, 24726, 0x837E01) #take quest
    bot.Move.XYAndExitMap(13583, 18781, target_map_id=513)
    bot.Wait.ForMapLoad(target_map_id=513)
    bot.Move.XY(15159, 12506)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Wait.ForMapToChange(target_map_id=643)
    bot.Move.XYAndDialog(12009, 24726, 0x837E07) #Big Unfriendly Jotun Reward   
bot.SetMainRoutine(Routine)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path="Dwarven_stability.png")


if __name__ == "__main__":
    main()
