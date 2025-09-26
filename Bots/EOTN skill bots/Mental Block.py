from Py4GWCoreLib import *
bot = Botting("Balthazar")



def Routine(bot: Botting) -> None:
    bot.Map.Travel(target_map_id=641)
    bot.Wait.ForMapLoad(target_map_id=641)
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Enable("auto_combat")
    bot.States.AddHeader("Balthazar")
    bot.Move.XYAndDialog(25203, -10694, 0x837701) #Balthazar
    bot.Map.Travel(target_map_id=639)
    bot.Wait.ForMapLoad(target_map_id=639)
    bot.Move.XY(-22999, 6530)
    bot.Wait.ForMapLoad(target_map_id=566)
    bot.Move.XY(-9761, -8000) #spot 1
    bot.Move.XY(7833, -8293) #spot 2
    bot.Move.XY(11690, -6215) #spot 3
    bot.Move.XY(15918, -2667) #spot 4
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForMapLoad(target_map_id=639)
    bot.Map.Travel(target_map_id=641)
    bot.Wait.ForMapLoad(target_map_id=641)
    bot.Move.XYAndDialog(25203, -10694, 0x837707) #Rewards
bot.SetMainRoutine(Routine)

def main():
    bot.Update()
    bot.UI.draw_window(icon_path="Mental Block.png")


if __name__ == "__main__":
    main()