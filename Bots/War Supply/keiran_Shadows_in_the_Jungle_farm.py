from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui, ActionQueueManager, Keystroke, Key)
from typing import List, Tuple

bot = Botting("Kieran Rise Farm")
     
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    GoToEOTN(bot)
    GetBonusBow(bot)
    ExitToHOM(bot)
    AcquireKieransBow(bot)
    EnterQuest(bot)
    AuspiciousBeginnings(bot)

def _on_death(bot: "Botting"):
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.Properties.ApplyNow("halt_on_death","active", True)
    bot.Properties.ApplyNow("movement_timeout","value", 15000)
    bot.Properties.ApplyNow("auto_combat","active", False)
    yield from Routines.Yield.wait(8000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Acquire Kieran's Bow_4") 
    fsm.resume()                           
    yield  
    
def on_death(bot: "Botting"):
    print ("Player is dead. Run Failed, Restarting...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))
    
def InitializeBot(bot: Botting) -> None:
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)
    
def GoToEOTN(bot: Botting) -> None:
    bot.States.AddHeader("Go to EOTN")
    bot.Map.Travel(target_map_id=642) #eye of the north outpost
      
def GetBonusBow(bot: Botting):
    bot.States.AddHeader("Check for Bonus Bow")

    def _get_bonus_bow(bot: Botting):
        if not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(ModelID.Bonus_Nevermore_Flatbow.value):
            yield from bot.helpers.Items._spawn_bonus_items()
            yield from bot.helpers.Items._equip(ModelID.Bonus_Nevermore_Flatbow.value)
        yield from bot.helpers.Items._destroy_bonus_items(exclude_list=[ModelID.Bonus_Nevermore_Flatbow.value])

    bot.States.AddCustomState(lambda: _get_bonus_bow(bot), "GetBonusBow")
    

def ExitToHOM(bot: Botting) -> None:
    bot.States.AddHeader("Exit to HOM")
    bot.Move.XYAndExitMap(x=-4873.00, y=5284.00, target_map_id=646, step_name="Exit to HOM")

def AcquireKieransBow(bot: Botting) -> None:
    KIERANS_BOW = 35829
    bot.States.AddHeader("Acquire Kieran's Bow")

    def _acquire_keirans_bow(bot: Botting):
        if not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(KIERANS_BOW):
            # Direct coroutine: interact with Gwen to take the bow
            yield from bot.Move._coro_xy_and_dialog(-6583.00, 6672.00,dialog_id=0x0000008A)

        if not Routines.Checks.Inventory.IsModelEquipped(KIERANS_BOW):
            yield from bot.helpers.Items._equip(KIERANS_BOW)

    bot.States.AddCustomState(lambda: _acquire_keirans_bow(bot), "AcquireKieransBow")

        
def EnterQuest(bot: Botting) -> None:
    bot.States.AddHeader("Enter Quest")
    bot.Move.XYAndDialog(-6662.00, 6584.00, 0x640) #enter quest with scrying pool
    bot.Wait.ForMapLoad(847)
    
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
        
        
    bot.States.AddHeader("Rise")
    _EnableCombat(bot)
    bot.Items.Equip(ModelID.Bonus_Nevermore_Flatbow.value)
    #start the loop
    bot.Move.XY(-8896.96, -6874.15,"First Group")
    bot.Move.XY(-9231.78, -4391.16,"Second Group")
    bot.Move.XY(-5400.65, -4153.40,"Third Group")
    bot.Move.XY(-2327.16, 3521.47,"Fourth Group")
    bot.Move.XY(-2458.25, 12024.10,"Fifth Group")
    bot.Move.XY(1954.51, 9831.73,"Sixth Group")
    bot.Move.XY(1831.94, 5297.14,"Seventh Group")

    bot.Wait.ForMapToChange(target_map_id=646)
    _DisableCombat(bot)
    bot.States.JumpToStepName("[H]Acquire Kieran's Bow_4") 
    

bot.SetMainRoutine(create_bot_routine)

def main():
    bot.Update()
    bot.UI.draw_window(icon_path="Keiran_art.png")


if __name__ == "__main__":
    main()
