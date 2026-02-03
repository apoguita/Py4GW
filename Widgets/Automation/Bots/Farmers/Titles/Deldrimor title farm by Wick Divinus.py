from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Agent, Player, ConsoleLog
import Py4GW
import os

bot = Botting("Deldrimor title farm by Wick Divinus",
              upkeep_honeycomb_active=True)
 
def Routine(bot: Botting) -> None:
    PrepareForCombat(bot)
    Snowman(bot)

def PrepareForCombat(bot: Botting) -> None:
    bot.States.AddHeader("Enable Combat Mode")
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=639)
    bot.Party.SetHardMode(True)

def Snowman(bot: Botting):
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    bot.States.AddHeader("Start Combat")
    bot.Move.XYAndDialog(-23884, 13954, 0x84)
    bot.Wait.ForMapToChange(target_map_id=701)
    bot.Multibox.UseAllConsumables()
    bot.States.AddManagedCoroutine("Upkeep Multibox Consumables", lambda: _upkeep_multibox_consumables(bot))
    bot.Move.XYAndInteractNPC(-14078.00, 15449.00)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Move.XY(-14804, 10703)
    bot.Move.XY(-15628, 9589)
    bot.Move.XY(-17602, 6858)
    bot.Wait.ForTime(1000)
    bot.Move.XY(-19769, 5046)
    bot.Move.XY(-16697.96, 1302.89)
    # bot.Move.XY(-14673.79, 2621.35) # Default
    bot.Move.XY(-15090.34, 2057.10) # Updated to avoid agroing both corridor and bridge groups
    bot.Move.XYAndInteractNPC(-12482.00, 3924.00)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Move.XY(-13824.00, 924.00)
    bot.Move.XY(-13752.06, -504.66)
    bot.Move.XY(-12084.77, -1592.58)
    bot.Move.XY(-12745.70, -3899.97)
    bot.Move.XY(-13262.00, -7346.00)
    bot.Move.XY(-14891.95, -10069.69)
    bot.Move.XY(-9573.00, -10963.00)
    bot.Move.FollowPath([(-9703.92, -10948.97)])
    bot.Wait.UntilOutOfCombat()
    bot.Items.LootItems()
    bot.Move.XYAndInteractNPC(-16093.00, -10723.00)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Move.XY(-15756.00, -12335.00)
    bot.Interact.WithGadgetAtXY(-15435.00, -12277.00) #lock
    bot.Wait.ForTime(3000)
    bot.Move.XY(-17542.00, -14048.00)
    bot.Move.XY(-13088.00, -17749.00)
    bot.Move.XY(-13004.20, -17304.91)
    bot.Wait.UntilOutOfCombat()
    bot.Items.LootItems()
    bot.Move.XY(-11136.00, -18043.00)
    bot.Interact.WithGadgetAtXY(-11136.00, -18043.00) #boss lock
    bot.Wait.ForTime(3000)
    bot.Move.XY(-7422.59, -18622.13)
    bot.Wait.ForTime(60000)
    bot.Interact.WithGadgetAtXY(-7594.00, -18657.00)
    bot.Items.LootItems()
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=639)
    bot.States.JumpToStepName("[H]Enable Combat Mode_1")

def _upkeep_multibox_consumables(bot: "Botting"):
    while True:
        yield from bot.Wait._coro_for_time(15000)
        if not Routines.Checks.Map.MapValid():
            continue
        
        if Routines.Checks.Map.IsOutpost():
            continue
        
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Essence_Of_Celerity.value, 
                                            GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0))  
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Grail_Of_Might.value, 
                                                GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect"), 0, 0))  
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Armor_Of_Salvation.value, 
                                                GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect"), 0, 0))
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Birthday_Cupcake.value, 
                                                GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill"), 0, 0))  
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Golden_Egg.value, 
                                                GLOBAL_CACHE.Skill.GetID("Golden_Egg_skill"), 0, 0))  
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Candy_Corn.value, 
                                                GLOBAL_CACHE.Skill.GetID("Candy_Corn_skill"), 0, 0))  
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Candy_Apple.value, 
                                                GLOBAL_CACHE.Skill.GetID("Candy_Apple_skill"), 0, 0))  
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Slice_Of_Pumpkin_Pie.value, 
                                                GLOBAL_CACHE.Skill.GetID("Pie_Induced_Ecstasy"), 0, 0))    
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Drake_Kabob.value, 
                                                GLOBAL_CACHE.Skill.GetID("Drake_Skin"), 0, 0))  
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Bowl_Of_Skalefin_Soup.value, 
                                                GLOBAL_CACHE.Skill.GetID("Skale_Vigor"), 0, 0))  
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Pahnai_Salad.value, 
                                                GLOBAL_CACHE.Skill.GetID("Pahnai_Salad_item_effect"), 0, 0))  
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.War_Supplies.value, 
                                                                GLOBAL_CACHE.Skill.GetID("Well_Supplied"), 0, 0))
        for i in range(1, 5): 
            GLOBAL_CACHE.Inventory.UseItem(ModelID.Honeycomb.value)
            yield from bot.Wait._coro_for_time(250)
            
def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
    bot.States.JumpToStepName("[H]Start Combat_2")
    bot.config.FSM.resume()
    
def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot)) 

bot.SetMainRoutine(Routine)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Asura Title Farm", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi Account, farm Asura title in Magus Stones")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Wick Divinus")
    PyImGui.end_tooltip()

REFORGED_TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "Wick Divinus bots", "Reforged_Icon.png")
def main():
    bot.Update()
    bot.UI.draw_window(icon_path=REFORGED_TEXTURE)

if __name__ == "__main__":
    main()
