
from Py4GWCoreLib import *

bot = Botting("GTOB Killer")

def Routine(bot: Botting) -> None:
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Enable("auto_combat")
    
    bot.Move.XY(-6062, -2688,"Exit Outpost")
    bot.Wait.ForMapLoad(target_map_name="Isle of the Nameless")
    bot.Move.XY(24.22, 662.37, "Master Of Healing")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(3531.49, 3936.87, "Master Of Hexes")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(1832.22, 9710.28, "Master Of Enchantments")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(5870.76, 8822.76, "Master Of Axes")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(8603.14, 6247.41, "Master Of Hammers")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(6527.84, 1637.41, "Master Of Lighting")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7873.69, -1941.89, "Master Of Energy Denial")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(3354.89, -7001.23, "Master Of Interrupts")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(3071.38, -2879.04, "Master Of Spirits")
    bot.Wait.UntilOutOfCombat()
    bot.UI.PrintMessageToConsole("GTOB Killer", "Finished routine")

bot.SetMainRoutine(Routine)


def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()
