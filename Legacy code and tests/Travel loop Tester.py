from __future__ import annotations
from typing import List, Tuple, Generator, Any
import os
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui, ActionQueueManager)


bot = Botting("Travel Test",
              upkeep_birthday_cupcake_restock=10,
              upkeep_honeycomb_restock=20,
              upkeep_war_supplies_restock=2,
              upkeep_auto_inventory_management_active=False,
              upkeep_auto_combat_active=False,
              upkeep_auto_loot_active=True)
 
def create_bot_routine(bot: Botting) -> None:
    TravelTest(bot)    
    

def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.Templates.Pacifist()
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Disable("honeycomb")
    bot.Properties.Disable("war_supplies")
    bot.Items.Restock.BirthdayCupcake()
    bot.Items.Restock.WarSupplies()
    bot.Items.Restock.Honeycomb()

def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Templates.Aggressive()
    bot.Properties.Enable("birthday_cupcake")
    bot.Properties.Enable("honeycomb")
    bot.Properties.Enable("war_supplies")
    bot.Items.Restock.BirthdayCupcake()
    bot.Items.Restock.WarSupplies()
    bot.Items.Restock.Honeycomb()

def TravelTest(bot: Botting) -> None:
    bot.States.AddHeader("Travel Test")
    bot.Map.Travel(target_map_id=479)#Champions Dawn
    bot.Map.Travel(target_map_id=449)# Kamadan
    bot.Map.Travel(target_map_id=479)#Champions Dawn
    bot.Move.XY(22834, 6223)
    bot.Wait.ForMapToChange(target_map_id=432)
    bot.Move.XY(23772, 6605)
    bot.Wait.ForMapLoad(target_map_id=479)
    bot.Move.XY(22834, 6223)
    bot.Wait.ForMapLoad(target_map_name="Cliffs of Dohjok")
    bot.Move.XY(23772, 6605)
    bot.Wait.ForMapLoad(target_map_name="Champions Dawn")  
    bot.Move.XY(22834, 6223)
    bot.Wait.ForMapToChange(target_map_id=432)
    bot.Move.XY(23772, 6605)
    bot.Wait.ForMapToChange(target_map_id=479)
    bot.States.JumpToStepName("[H]Travel Test_1")
    
bot.SetMainRoutine(create_bot_routine)


def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()
