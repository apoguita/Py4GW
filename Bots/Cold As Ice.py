from Py4GWCoreLib import *
bot = Botting("Cold As Ice")
def Routine(bot: Botting) -> None:
    bot.Map.Travel(target_map_name="Sifhalla")
    bot.Wait.ForMapLoad(target_map_id=643)
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Enable("auto_combat")
    bot.States.AddHeader("Cold As Ice")
    bot.Move.XYAndDialog(14380, 23968, 0x834401) #Cold As Ice
    bot.Dialogs.AtXY(14380, 23968, 0x834404)
    bot.Dialogs.AtXY(14380, 23968, 0x85) #I am Ready
    bot.Wait.ForMapLoad(target_map_id=690) #Special Sifhalla Map
    bot.Wait.ForTime(14000)
    bot.Move.XY(15187, 23163)
    bot.Wait.UntilOnCombat()
    bot.Target.Model(2411)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    bot.Wait.ForMapLoad(target_map_id=643)
    bot.Move.XYAndDialog(14380, 23968, 0x834407) #Rewards
bot.SetMainRoutine(Routine)

def main():
    bot.Update()
    bot.UI.draw_window(icon_path="IAU.png")


if __name__ == "__main__":
    main()