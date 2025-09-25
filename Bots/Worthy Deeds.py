from Py4GWCoreLib import *
bot = Botting("Let's get to it")
def Routine(bot: Botting) -> None:
    bot.Map.Travel(target_map_name="Sifhalla")
    bot.Wait.ForMapLoad(target_map_id=643)
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Enable("auto_combat")
    bot.States.AddHeader("Worthy Deeds")
    bot.Move.XYAndDialog(14380, 23968, 0x833A01) #Worthy Deeds
    bot.Move.XYAndExitMap(8832, 23870, target_map_id=513)
    bot.Wait.ForMapLoad(target_map_id=513)
    bot.Move.XY(11434, 19708)
    bot.Move.XY(14164, 2682)
    bot.Move.XY(9435, -5806) # if you got here and no boss restart
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(1914, -6963) #Myish, Lady of the Lake
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(4735, -14202)
    bot.Move.XY(5752, -15236)
    bot.Move.XY(8924, -15922)
    bot.Move.XY(14134, -16744)
    bot.Move.XY(12581, -19343) #Rabbit hole start
    bot.Move.XY(12702, -23855) #around the bend
    bot.Move.XY(13952, -23063) #Nulfastu, Earthbound
    bot.Wait.ForTime(45000) #45 seconds max to kill this guy and back to town after, if you die though it will keep going
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Wait.ForMapLoad(target_map_id=643)
    bot.Move.XYAndDialog(14380, 23968, 0x833A07) #Rewards
bot.SetMainRoutine(Routine)

def main():
    bot.Update()
    bot.UI.draw_window(icon_path="IAU.png")


if __name__ == "__main__":
    main()
