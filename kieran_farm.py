from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui)
import PyMap, PyImGui
from typing import List, Tuple

bot = Botting("Kieran Farm Bot")


        
def create_bot_routine(bot: Botting) -> None:
    GoToEOTN(bot)
    GetBonusBow(bot)
    ExitToHOM(bot)
    AcquireKieransBow(bot)
    EnterQuest(bot)
    AuspiciousBeginnings(bot)


def GoToEOTN(bot: Botting) -> None:
    bot.States.AddHeader("Go to EOTN")
    bot.Map.Travel(target_map_id=642) #eye of the north outpost
      
def GetBonusBow(bot: Botting):
    bot.States.AddHeader("Check for Bonus Bow")
    if not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(ModelID.Bonus_Nevermore_Flatbow.value): #Bonus Bow
        bot.Items.SpawnBonusItems()
        bot.Items.Equip(ModelID.Bonus_Nevermore_Flatbow.value)
        bot.Items.DestroyBonusItems()  

def ExitToHOM(bot: Botting) -> None:
    bot.States.AddHeader("Exit to HOM")
    bot.Move.XYAndExitMap(x=-4873.00, y=5284.00, target_map_id=646, step_name="Exit to HOM")

def AcquireKieransBow(bot: Botting) -> None:
    KIERANS_BOW = 35829
    bot.States.AddHeader("Acquire Kieran's Bow")
    if not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(KIERANS_BOW): #Kierans
        bot.Move.XYAndDialog(-6583.00, 6672.00, 0x0000008A) #take bow with gwen
        
    if not Routines.Checks.Inventory.IsModelEquipped(KIERANS_BOW):
        bot.Items.Equip(KIERANS_BOW)
        
def EnterQuest(bot: Botting) -> None:
    bot.States.AddHeader("Enter Quest")
    bot.Move.XYAndDialog(-6662.00, 6584.00, 0x63E) #enter quest with gwen
    bot.Wait.ForMapLoad(849)
    
def AuspiciousBeginnings(bot: Botting) -> None:
    def _EnableCombat(bot: Botting) -> None:
        bot.Properties.Enable("pause_on_danger")
        bot.Properties.Disable("halt_on_death")
        bot.Properties.Set("movement_timeout",value=-1)
        bot.Properties.Enable("auto_combat")
        
    def _DisableCombat(bot: Botting) -> None:
        bot.Properties.Disable("pause_on_danger")
        bot.Properties.Enable("halt_on_death")
        bot.Properties.Set("movement_timeout",value=15000)
        bot.Properties.Disable("auto_combat")
        
    bot.States.AddHeader("Auspicious Beginnings")
    _EnableCombat(bot)
    bot.Items.Equip(ModelID.Bonus_Nevermore_Flatbow.value)
    bot.Move.XY(11864.74, -4899.19)
    bot.Wait.UntilOnCombat()
    bot.Move.XY(8243.03, -8571.58, step_name="To corner")
    bot.Move.XY(3173.55, -12144.88, step_name="To safe spot 1")
    bot.Move.XY(869.17, -13687.34, step_name="To safe spot 2")
    bot.Move.XY(130.81, -13343.52, step_name="To safe spot 3")
    bot.Move.XY(-5157.64, -12775.74, step_name="To safe spot 4")
    bot.Move.XY(-15858.25, -8840.35, step_name="To End of Path")
    bot.Wait.ForMapToChange(target_map_id=646)
    _DisableCombat(bot)
    bot.States.JumpToStepName("[H]Acquire Kieran's Bow_4")
    


bot.SetMainRoutine(create_bot_routine)

def main():
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()
