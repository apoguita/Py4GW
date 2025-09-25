from Py4GWCoreLib import *
bot = Botting("Melandru")

def Routine(bot: Botting) -> None:
    bot.States.AddHeader("Goto Town")
    bot.Map.Travel(target_map_id=641)
    bot.Wait.ForMapLoad(target_map_id=641)
    bot.Properties.ApplyNow("pause_on_danger", "active", True)
    bot.Properties.ApplyNow("halt_on_death","active", True)
    bot.Properties.ApplyNow("movement_timeout","value", 15000)
    bot.Properties.ApplyNow("auto_combat","active", True)
    bot.States.AddHeader("Melandru")
    bot.Move.XYAndDialog(25203, -10694, 0x837C01) #Melandru
    bot.Move.XY(18781, -10477)
    bot.Wait.ForMapLoad(target_map_name="Alcazia Tangle")
    bot.Move.XY(17024, -600)
    bot.Move.XY(18237, 6691) #res shrine 1
    bot.Move.XY(15518, 8375)
    bot.Move.XY(13200, 15000) #Spot 1 confirmed
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOutOfCombat() #move on to spot 2
    bot.Move.XY(19516, 4686) #rez shrine 2 cliff
    bot.Move.XY(12184, 370) #midway
    bot.Move.XY(4802, -4990) #Rez Shrine 3
    bot.Move.XY(-8760, -3378) #Rez Shrine 4 
    bot.Move.XY(-5555, -2108)
    bot.Move.XY(-6678, 6477) # Spot 3 Confirmed
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOutOfCombat() #move on to spot 3
    bot.Move.XY(-8860, -3178) #Rez Shrine 4 again
    bot.Move.XY(-11202, 758) # Spot 3 Confirmed
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Wait.ForMapLoad(target_map_id=641)
    bot.Move.XYAndDialog(25203, -10694, 0x837C07) #Rewards
bot.SetMainRoutine(Routine)

def main():
    bot.Update()
    bot.UI.draw_window(icon_path="IAU.png")


if __name__ == "__main__":
    main()