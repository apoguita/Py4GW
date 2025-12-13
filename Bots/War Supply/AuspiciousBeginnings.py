from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui, ActionQueueManager)

from Py4GWCoreLib.Builds import KeiranThackerayEOTN
import Py4GW


bot = Botting("Auspicious Beginnings",
              custom_build=KeiranThackerayEOTN())
     
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    GoToEOTN(bot)
    #GetBonusBow(bot)
    ExitToHOM(bot)
    AcquireKeiransBow(bot)
    EnterQuest(bot)
    AuspiciousBeginnings(bot)

def _on_death(bot: "Botting"):
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.Properties.ApplyNow("halt_on_death","active", True)
    bot.Properties.ApplyNow("movement_timeout","value", 15000)
    bot.Properties.ApplyNow("auto_combat","active", False)
    yield from Routines.Yield.wait(8000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Acquire Keiran's Bow_3") 
    fsm.resume()                           
    yield  
    
def on_death(bot: "Botting"):
    print ("Player is dead. Run Failed, Restarting...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))

def _EnableCombat(bot: Botting) -> None:
        bot.OverrideBuild(KeiranThackerayEOTN())
        bot.Templates.Aggressive(enable_imp=False)
 
def _DisableCombat(bot: Botting) -> None:
        bot.Templates.Pacifist()

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

def AcquireKeiransBow(bot: Botting) -> None:
    KEIRANS_BOW = 35829
    bot.States.AddHeader("Acquire Keiran's Bow")
    bot.Wait.ForMapLoad(target_map_id=646)

    def _acquire_keirans_bow(bot: Botting):
        if not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(KEIRANS_BOW):
            # Direct coroutine: interact with Gwen to take the bow
            yield from bot.Move._coro_xy_and_dialog(-6583.00, 6672.00, dialog_id=0x0000008A)
        if not Routines.Checks.Inventory.IsModelEquipped(KEIRANS_BOW):
            yield from bot.helpers.Items._equip(KEIRANS_BOW)

    bot.States.AddCustomState(lambda: _acquire_keirans_bow(bot), "AcquireKeiransBow")

def deposit_gold(bot: Botting):
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    # Deposit all gold if character has 90k or more
    if gold_on_char >= 90000:
        bot.Map.Travel(target_map_id=642)
        bot.Wait.ForMapLoad(target_map_id=642)
        yield from Routines.Yield.wait(500)
        GLOBAL_CACHE.Inventory.DepositGold(gold_on_char)
        yield from Routines.Yield.wait(500)
        bot.Move.XYAndExitMap(-4873.00, 5284.00, target_map_id=646)
        bot.Wait.ForMapLoad(target_map_id=646)
        yield

def EnterQuest(bot: Botting) -> None:
    bot.States.AddHeader("Enter Quest")
    bot.Move.XYAndDialog(-6662.00, 6584.00, 0x63E) #enter quest with pool
    bot.Wait.ForMapLoad(target_map_id=849)
    
def AuspiciousBeginnings(bot: Botting) -> None:    
    bot.States.AddHeader("Auspicious Beginnings")
    _EnableCombat(bot)
    #bot.Items.Equip(ModelID.Bonus_Nevermore_Flatbow.value)
    bot.Move.XY(11864.74, -4899.19)
    #bot.Properties.Enable("war_supplies")
    bot.Wait.UntilOnCombat(Range.Spirit)
    #bot.Properties.Disable("war_supplies")
    bot.Move.XY(10165.07, -6181.43, step_name="First Spawn")
    #bot.Wait.UntilOutOfCombat()
    bot.Properties.Disable("pause_on_danger")
    path = [(8859.57, -7388.68), (9012.46, -9027.44)]
    bot.Move.FollowAutoPath(path, step_name="To corner")
    bot.Properties.Enable("pause_on_danger")
    #bot.Wait.UntilOutOfCombat()

    bot.Move.XY(4518.81, -9504.34, step_name="To safe spot 0")
    bot.Wait.ForTime(4000)
    bot.Properties.Disable("pause_on_danger")
    bot.Move.XY(2622.71, -9575.04, step_name="To patrol")
    bot.Properties.Enable("pause_on_danger")
    bot.Move.XY(325.22, -11728.24)
    
    bot.Properties.Disable("pause_on_danger")
    bot.Move.XY(-2860.21, -12198.37, step_name="To middle")
    bot.Move.XY(-5109.05, -12717.40, step_name="To patrol 3")
    bot.Move.XY(-6868.76, -12248.82, step_name="To patrol 4")
    bot.Properties.Enable("pause_on_danger")

    bot.Move.XY(-15858.25, -8840.35, step_name="To End of Path")
    bot.Wait.ForMapToChange(target_map_id=646)
    _DisableCombat(bot)
    #bot.States.AddCustomState(lambda: deposit_gold(bot), "DepositGoldIfNeeded")
    bot.States.JumpToStepName("[H]Acquire Keiran's Bow_3")
    
bot.SetMainRoutine(create_bot_routine)

def main():
    bot.Update()
    projects_path = Py4GW.Console.get_projects_path()
    full_path = projects_path + "\\Bots\\War Supply\\"
    bot.UI.draw_window(icon_path=full_path + "Keiran_art.png")


if __name__ == "__main__":
    main()
