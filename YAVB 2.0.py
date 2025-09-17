import Py4GW
from Py4GWCoreLib import (Routines,Botting,ActionQueueManager, ConsoleLog, GLOBAL_CACHE)
from Py4GWCoreLib.enums import Profession

from Py4GWCoreLib.Builds import ShadowFormAssassinVaettir
from Py4GWCoreLib.Builds import ShadowFormMesmerVaettir


bot = Botting("YAVB 2.0",
              upkeep_birthday_cupcake_restock=1,
              custom_build=ShadowFormAssassinVaettir())
     
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    
def InitializeBot(bot: Botting) -> None:
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)
    bot.States.AddHeader("Initialize Bot")
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Disable("auto_loot")
    bot.Properties.Disable("hero_ai")
    bot.Properties.Enable("auto_combat")
    bot.Properties.Disable("pause_on_danger")
    bot.Properties.Enable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=15000)
    bot.Properties.Enable("birthday_cupcake")
    
def EquipSkillBar(bot: Botting):
    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    match profession:
        case Profession.Assassin.value:
            bot.OverrideBuild(ShadowFormAssassinVaettir())
            
        case Profession.Mesmer.value:
            bot.OverrideBuild(ShadowFormMesmerVaettir())  # Placeholder for Mesmer build
            
        case _:
            ConsoleLog("Unsupported Profession", f"The profession '{profession}' is not supported by this bot.", Py4GW.Console.MessageType.Error)
            bot.Stop()
            return
    yield from bot.config.build_handler.LoadSkillBar()

        
def TownRoutines(bot: Botting) -> None:
    bot.States.AddHeader("Town Routines")
    bot.Map.Travel(target_map_name="Longeyes Ledge")
    bot.States.AddCustomState(EquipSkillBar, "Equip SkillBar")
    bot.Items.AutoIDAndSalvageAndDepositItems()


#region Events
    
def _on_death(bot: "Botting"):
    yield from Routines.Yield.wait(8000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Initialize Bot_1") 
    fsm.resume()                           
    yield  
    
def on_death(bot: "Botting"):
    ConsoleLog("Death detected", "Run Failed, Restarting...", Py4GW.Console.MessageType.Notice)
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))

 

bot.SetMainRoutine(create_bot_routine)
base_path = Py4GW.Console.get_projects_path()
        
def main():
    bot.Update()
    bot.UI.draw_window(icon_path="YAVB 2.0 mascot.png")


if __name__ == "__main__":
    main()
