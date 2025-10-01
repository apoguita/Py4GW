
from Py4GWCoreLib import *

bot = Botting("Get TOA")

def Routine(bot: Botting) -> None:
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Enable("auto_combat")
    bot.Map.Travel(target_map_id=650) #Longeyes Ledge
    bot.Move.XY(-22664, 13175) #a starting coord
    bot.Move.XY(-4163, -203, "Res Shrine 1")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(11385, 2228, "Res Shrine 2")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(19190, -12141, "Res Shrine 3")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndExitMap(23054, -13225, target_map_name="Sacnoth Valley")
    bot.Move.XY(-16333, 16622, "Res Shrine 4")
    bot.Move.XY(-16605, 12608) #wall hugging
    bot.Move.XY(-17653, 8825) #Charr Group
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-17085, 5034) #Charr Group 2
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-13308, 4215) #Charr Group 3
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-13020, 270, "Res Shrine 5")
    bot.Move.XY(-9647, -12780, "Boss")
    bot.Wait.UntilOutOfCombat()
    
   

bot.SetMainRoutine(Routine)


def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()
