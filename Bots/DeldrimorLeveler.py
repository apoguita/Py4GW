
from Py4GWCoreLib import *


selected_step = 0
DOOMLORE_SHRINE = "Doomlore Shrine"


def AddHenchies():
    for i in range(1,8):
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
def Routine(bot: Botting) -> None:
    map_id = GLOBAL_CACHE.Map.GetMapID()
    if map_id != 640:
        bot.Travel(target_map_name=DOOMLORE_SHRINE)
        bot.WaitForMapLoad(target_map_name=DOOMLORE_SHRINE)
    bot.AddFSMCustomYieldState(AddHenchies, "Add Henchmen")
    bot.MoveTo(-18579, 17984, 'Move to NPC')
    bot.DialogAt(-19166.00, 17980.00, 0x832101)  # Temple of the damned quest 0x832101
    bot.DialogAt(-19166.00, 17980.00, 0x88)  # Enter COF Level 1

    bot.WaitForMapLoad(target_map_name="Cathedral of Flames (level 1)")

    bot.MoveTo(-20250, -7333, "Setup Resign Spot")

    for i in range(100):
        bot.AddHeaderStep("Farm Loop")
        bot.WaitForMapLoad(target_map_name=DOOMLORE_SHRINE)
        bot.DialogAt(-19166.00, 17980.00, 0x832101)  # Temple of the damned quest 0x832101
        bot.DialogAt(-19166.00, 17980.00, 0x88)  # Enter COF Level 1
        bot.WaitForMapLoad(target_map_name="Cathedral of Flames (level 1)")
        bot.DialogAt(-18250.00, -8595.00, 0x84)
        bot.MoveTo(-17734, -9195, "Fight in entrance")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-15477, -8560, "Fight at Spot 1")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-15736, -6609, "Fight at Spot 2")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-14748, -3623, "Fight at Spot 3")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-13126, -3364, "Fight at Spot 4")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-12350, -1648, "Fight at Spot 5")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-12162, -1413, "Fight at Spot 6")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-10869, -2, "Fight at Spot 7")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-10728, 420, "Fight at Spot 8")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-12632, 3241, "Fight at Spot 9")
        bot.WasteTimeUntilOOC()
        bot.Resign() 
        bot.AddFSMCustomYieldState(ReturnToOutpost, "Return to Doomlore")


bot.Routine = Routine.__get__(bot)

def main():
    global selected_step
    
    bot.Update()

    if PyImGui.begin("DELDRIMOR", PyImGui.WindowFlags.AlwaysAutoResize):
        
        if PyImGui.button("start bot"):
            bot.Start()

        if PyImGui.button("stop bot"):
            bot.Stop()

    PyImGui.end()


if __name__ == "__main__":
    main()
