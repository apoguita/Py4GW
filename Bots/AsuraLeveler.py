
from Py4GWCoreLib import *


selected_step = 0
RATA_SUM = "Rata Sum"


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
        bot.Travel(target_map_name=RATA_SUM)
        bot.WaitForMapLoad(target_map_name=RATA_SUM)
    bot.AddFSMCustomYieldState(AddHenchies, "Add Henchmen")
    bot.MoveTo(20340, 16899, "Exit Outpost")
    bot.WaitForMapLoad(target_map_name="Riven Earth")
    bot.MoveTo(-26633, -4072, "Setup Resign Spot")

    for i in range(100):
        bot.AddHeaderStep("Farm Loop")
        bot.WaitForMapLoad(target_map_name=RATA_SUM)
        bot.MoveTo(20340, 16899, "Exit Outpost")
        bot.WaitForMapLoad(target_map_name="Riven Earth")
        bot.MoveTo(-24347, -5543, "Go towards the Krewe Member")
        bot.DialogAt(-24272.00, -5719.00, 0x84)
        bot.MoveTo(-21018, -6969, "Fight outside the cave")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-20884, -8497, "Move to Cave Entrace")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-19760, -10225, "Fight in Cave 1")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-18663, -10910, "Fight in Cave 2")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-18635, -11925, "Fight in Cave 3")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-20473, -11404, "Fight in Cave 4")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-21460, -12145, "Fight in Cave 5")
        bot.WasteTimeUntilOOC()
        bot.MoveTo(-23755, -11391, "Fight in Cave BOSS")
        bot.WasteTimeUntilOOC()
        bot.Resign()
        bot.AddFSMCustomYieldState(ReturnToOutpost, "Return to Outpost")

bot.Routine = Routine.__get__(bot)

def main():
    global selected_step
    
    bot.Update()

    if PyImGui.begin("ASURA", PyImGui.WindowFlags.AlwaysAutoResize):
        
        if PyImGui.button("start bot"):
            bot.Start()

        if PyImGui.button("stop bot"):
            bot.Stop()

    PyImGui.end()


if __name__ == "__main__":
    main()
