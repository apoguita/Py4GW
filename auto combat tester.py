from __future__ import annotations
from typing import List, Tuple

from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,ActionQueueManager)

bot = Botting("Auto Combat Tester",
              upkeep_birthday_cupcake_restock=50,
              upkeep_honeycomb_restock=100,
              upkeep_auto_inventory_management_active=False,
              upkeep_auto_loot_active=False,
              upkeep_auto_combat_active=False)

def create_bot_routine(bot: Botting) -> None:
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)
    bot.Wait.UntilCondition(lambda: False)
    
def _on_death(bot: "Botting"):
    ConsoleLog(bot.config.bot_name, "You have died.", Py4GW.Console.MessageType.Warning)                          
    yield  
    
def on_death(bot: "Botting"):
    ConsoleLog("Death detected", "running code", Py4GW.Console.MessageType.Notice)
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))
    
    
bot.SetMainRoutine(create_bot_routine)

def main():
    global bot

    try:
        bot.Update()
        bot.UI.draw_window()

    except Exception as e:
        Py4GW.Console.Log(bot.config.bot_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
