
from Py4GWCoreLib import *


selected_step = 0

#dialog = 0x0000008A #get bow
#dialog = 0x63E #enter quest

bot = Botting("GTOB Killer")
def Routine(bot: Botting) -> None:
    bot.MoveTo(-6062, -2688,"Exit Outpost")
    bot.WaitForMapLoad(target_map_name="Isle of the Nameless")
    bot.MoveTo(24.22, 662.37, "Master Of Healing")
    bot.WasteTimeUntilOOC()
    bot.MoveTo(3531.49, 3936.87, "Master Of Hexes")
    bot.WasteTimeUntilOOC()
    bot.MoveTo(1832.22, 9710.28, "Master Of Enchantments")
    bot.WasteTimeUntilOOC()
    bot.MoveTo(5870.76, 8822.76, "Master Of Axes")
    bot.WasteTimeUntilOOC()
    bot.MoveTo(8603.14, 6247.41, "Master Of Hammers")
    bot.WasteTimeUntilOOC()
    bot.MoveTo(6527.84, 1637.41, "Master Of Lighting")
    bot.WasteTimeUntilOOC()
    bot.MoveTo(7873.69, -1941.89, "Master Of Energy Denial")
    bot.WasteTimeUntilOOC()
    bot.MoveTo(3354.89, -7001.23, "Master Of Interrupts")
    bot.WasteTimeUntilOOC()
    bot.MoveTo(3071.38, -2879.04, "Master Of Spirits")
    bot.WasteTimeUntilOOC()
    bot.PrintMessageToConsole("GTOB Killer", "Finished routine")

bot.Routine = Routine.__get__(bot)



def main():
    global selected_step
    
    bot.Update()

    if PyImGui.begin("PathPlanner Test", PyImGui.WindowFlags.AlwaysAutoResize):
        
        if PyImGui.button("start bot"):
            bot.Start()

        if PyImGui.button("stop bot"):
            bot.Stop()

    PyImGui.end()


if __name__ == "__main__":
    main()
