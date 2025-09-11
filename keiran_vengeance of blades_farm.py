from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, ModelID, Botting,
                          ActionQueueManager)

from Py4GWCoreLib.Builds import KeiranThackerayEOTN



bot = Botting("Vengeance of Blades Farm")




def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    GoToEOTN(bot)
    GetBonusBow(bot)
    ExitToHOM(bot)
    AcquireKieransBow(bot)
    EnterQuest(bot)
    VengeanceOfBlades(bot)

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
    bot.OverrideBuild(KeiranThackerayEOTN())
    
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
            yield from bot.helpers.Move._get_path_to(-6583.00, 6672.00)
            yield from bot.helpers.Move._follow_path()
            yield from bot.helpers.Interact._with_agent((-6583.00, 6672.00), dialog_id=0x0000008A)

        if not Routines.Checks.Inventory.IsModelEquipped(KIERANS_BOW):
            yield from bot.helpers.Items._equip(KIERANS_BOW)

    bot.States.AddCustomState(lambda: _acquire_keirans_bow(bot), "AcquireKieransBow")

        
def EnterQuest(bot: Botting) -> None:
    bot.States.AddHeader("Enter Quest")
    bot.Move.XYAndDialog(-6662.00, 6584.00, 0x63F) #enter quest with scrying pool
    bot.Wait.ForMapLoad(848)

def VengeanceOfBlades(bot: Botting) -> None:
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
        
        
    bot.States.AddHeader("Vengeance of Blades Farm")
    _EnableCombat(bot)
    bot.Items.Equip(ModelID.Bonus_Nevermore_Flatbow.value)
    bot.Wait.ForTime(25000)  #wait for the dialog to end

    #front of the quest
    bot.Properties.Disable("pause_on_danger")
    bot.Move.XY(15361.70, 3539.00)
    bot.Move.XY(15614.51, 2566.24)
    bot.Wait.UntilOutOfCombat()
    bot.Properties.Enable("pause_on_danger")
    bot.Move.XY(11663.13, 3917.35)
    bot.Move.XY(13880.35, 6271.86)
    
    bot.Move.XY(9532.97, 7396.32) #forest corner
    
    bot.Move.XY(7924.48, 4460.73) #tree evade
    bot.Move.XY(7077.30, -182.58) #tree patrol
    bot.Move.XY(6208.84, 4139.12) #evade tree 2
    bot.Move.XY(2740.14, 2118.45)
    bot.Move.XY(-6420.64, -2680.36)
    bot.Move.XY(-17341.90, -307.75)
    bot.Move.XY(-21701.85, 768.69)
    

    
    
    bot.Wait.ForMapToChange(target_map_id=646)
    _DisableCombat(bot)
    bot.States.JumpToStepName("[H]Acquire Kieran's Bow_4") 
    

bot.SetMainRoutine(create_bot_routine)

def main():
    bot.Update()
    bot.UI.draw_window(icon_path="Keiran_art.png")


if __name__ == "__main__":
    main()
