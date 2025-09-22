from Py4GWCoreLib import *
bot = Botting("I can do better")
def Routine(bot: Botting) -> None:
    bot.Map.Travel(target_map_name="Sifhalla")
    bot.Wait.ForMapLoad(target_map_id=643)
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Enable("auto_combat")
    bot.States.AddHeader("Anything you can do")
    bot.Move.XYAndDialog(14380, 23874, 0x833E01) #Anything you can do
    bot.Move.XY(14682, 22900)
    bot.Move.XYAndExitMap(17000, 22872, target_map_id=546)
    bot.Wait.ForMapLoad(target_map_id=546)
    bot.Move.XY(-9431, -20124)
    bot.Move.XY(-8441, -13685)
    bot.Move.XY(-9743, -6744)
    bot.Move.XY(-10672, 4815) #wall hugging
    bot.Move.XY(-8464, 17239) #up to Avarr the Fallen
    bot.Move.XY(-11700, 24101)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-8464, 17239) #back down the hill
    bot.Move.XY(-638, 17801) #up to Whiteout look out for boulder
    bot.Move.XY(-933, 15368) #run away from boulder
    bot.Wait.ForTime(6000)
    bot.Move.XY(-1339, 22089) #Kill Whiteout
    bot.Wait.ForTime(5000) #extra time here incase of party wipe
    bot.Multibox.ResignParty()
    bot.Wait.ForMapLoad(target_map_id=643)
 



    
    #bot.Map.Travel(target_map_name="Sifhalla")
    #bot.Move.XYAndDialog(14380, 23968, 0x833E07) #Rewards
bot.SetMainRoutine(Routine)

def main():
    bot.Update()
    bot.UI.draw_window(icon_path="IAU.png")


if __name__ == "__main__":
    main()
