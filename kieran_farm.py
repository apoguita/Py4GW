from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui, ActionQueueManager, Keystroke, Key)
import PyMap, PyImGui
from typing import List, Tuple

bot = Botting("Kieran Farm Bot")


        
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    GoToEOTN(bot)
    GetBonusBow(bot)
    ExitToHOM(bot)
    AcquireKieransBow(bot)
    EnterQuest(bot)
    AuspiciousBeginnings(bot)

def _call_dangerous_targets(bot: Botting):
    MODULE = "Check Dangerous Targets"
    dangerous_models = {
        8207,  # adherent
        8341,  # zealot
        8097,  # peacekeeper
        8235,  # devotee
        8200,  # savant
        8227,  # scout
    }

    ConsoleLog(MODULE, "Coroutine started.")

    while True:
        try:
            # Guards
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue

            if not GLOBAL_CACHE.Map.IsExplorable():
                yield from Routines.Yield.wait(1000)
                continue

            if not GLOBAL_CACHE.Party.IsPartyLoaded():
                yield from Routines.Yield.wait(1000)
                continue

            players = GLOBAL_CACHE.Party.GetPlayers()
            if not players:
                yield from Routines.Yield.wait(1000)
                continue

            target = players[0].called_target_id

            # If player 0 already called something, don't override.
            if target != 0:
                yield from Routines.Yield.wait(1000)
                continue

            # Need to call a dangerous target
            px, py = GLOBAL_CACHE.Player.GetXY()
            enemies = Routines.Agents.GetFilteredEnemyArray(
                px, py, max_distance=Range.Spellcast.value, aggressive_only=False
            )

            for enemy in enemies:
                if not GLOBAL_CACHE.Agent.IsValid(enemy):
                    continue
                if not GLOBAL_CACHE.Agent.IsAlive(enemy):
                    continue

                enemy_model = GLOBAL_CACHE.Agent.GetModelID(enemy)
                if enemy_model in dangerous_models:
                    GLOBAL_CACHE.Player.ChangeTarget(enemy)
                    GLOBAL_CACHE.Player.Interact(enemy, True)
                    ActionQueueManager().AddAction(
                        "ACTION", Keystroke.PressAndReleaseCombo, [Key.Ctrl.value, Key.Space.value]
                    )
                    break

            yield from Routines.Yield.wait(1000)

        except Exception as e:
            # Never die silently
            ConsoleLog(MODULE, f"Error: {e!r}. Recovering in 1s.")
            yield from Routines.Yield.wait(1000)


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
    bot.States.AddManagedCoroutine("DangerousTargets", lambda: _call_dangerous_targets(bot))
    
    

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
    bot.Move.XY(8655.57, -8782.28, step_name="To corner")
    bot.Move.XY(4518.81, -9504.34, step_name="To safe spot 0")
    bot.Wait.ForTime(5000)
    bot.Move.XY(2501.02, -10844.87, step_name="To patrol")
    bot.Move.XY(3173.55, -12144.88, step_name="To safe spot 1")
    
    bot.Move.XY(869.17, -13687.34, step_name="To safe spot 2")
    bot.Move.XY(130.81, -13343.52, step_name="To safe spot 3")
    bot.Wait.ForTime(5000)
    
    bot.Move.XY(-2860.21, -12198.37, step_name="To middle")
    bot.Wait.ForTime(5000)
    bot.Move.XY(-6832.97, -12470.33, step_name="To safe spot 4")
    
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
