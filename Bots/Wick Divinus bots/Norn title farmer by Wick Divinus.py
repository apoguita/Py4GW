from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Range, Utils, ConsoleLog
import Py4GW
import os
BOT_NAME = "Norn title farm by Wick Divinus"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
OLAFSTEAD = 645
VARAJAR_FELLS = 553

Norn_Path: list[tuple[float, float]] = [
    (-2484.73, 118.55),
    (-3059.12, -419.00),
    (-3301.01, -2008.23),
    (-2034, -4512),
    (-5278, -5771),
    (-5456, -7921),
    (-8793, -5837),
    (-14092, -9662),
    (-17260, -7906),
    (-21964, -12877),
    (-22275, -12462),
    (-21671, -2163),
    (-19592, 772),
    (-13795, -751),
    (-17012, -5376),
    (-12071, -4274),
    (-8351, -2633),
    (-4362, -1610),
    (-4316, 4033),
    (-8809, 5639),
    (-14916, 2475),
    (-11282, 5466),
    (-16051, 6492),
    (-16934, 11145),
    (-19378, 14555),
    (-22751, 14163),
    (-15932, 9386),
    (-13777, 8097),
    (-4729, 15385),
    (-2290, 14879),
    (-1810, 4679),
    (-6911, 5240),
    (-15471, 6384),
    (-411, 5874),
    (2859, 3982),
    (4909, -4259),
    (7514, -6587),
    (3800, -6182),
    (7755, -11467),
    (15403, -4243),
    (21597, -6798),
    (24522, -6532),
    (22883, -4248),
    (18606, -1894),
    (14969, -4048),
    (13599, -7339),
    (10056, -4967),
    (10147, -1630),
    (8963, 4043),
    (9339.46, 3859.12),
    (15576, 7156),
    (22838, 7914),
    (22961, 12757),
    (18067, 8766),
    (13311, 11917),
    (13714, 14520),
    (11126, 10443),
    (5575, 4696),
    (-503, 9182),
    (1582, 15275),
    (7857, 10409)
]

bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True)
                
def bot_routine(bot: Botting) -> None:
    global Norn_Path
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OLAFSTEAD)
    
    bot.Party.SetHardMode(True)
    auto_path_list = [(-328, 1240), (-1500, 1250)]
    bot.Move.FollowPath(auto_path_list)
    bot.Wait.ForMapLoad(target_map_id=553)
    bot.States.AddHeader("Start Combat")
    bot.Multibox.UseAllConsumables()
    bot.States.AddManagedCoroutine("Upkeep Multibox Consumables", lambda: _upkeep_multibox_consumables(bot))
    
    # Initial path to first blessing
    bot.Move.XY(-2484.73, 118.55, "Start")
    bot.Move.XY(-3059.12, -419.00, "Move to bridge")
    bot.Move.XY(-3301.01, -2008.23, "Move to shrine")
    bot.Move.XY(-2034, -4512, "Move to blessing 1")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-1892.00, -4505.00)
    bot.Multibox.SendDialogToTarget(0x84) #Get Blessing 1
    bot.Wait.ForTime(5000)
    
    # Path to blessing 2
    bot.Move.XY(-5278, -5771, "Aggro: Berzerker")
    bot.Move.XY(-5456, -7921, "Aggro: Berzerker")
    bot.Move.XY(-8793, -5837, "Aggro: Berzerker")
    bot.Move.XY(-14092, -9662, "Aggro: Vaettir and Berzerker")
    bot.Move.XY(-17260, -7906, "Aggro: Vaettir and Berzerker")
    bot.Move.XY(-21964, -12877, "Aggro: Jotun")
    bot.Move.XY(-25341.00, -11957.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-25341.00, -11957.00) 
    bot.Multibox.SendDialogToTarget(0x84) # Edda Blessing 2
    bot.Wait.ForTime(10000)
    
    # Path to blessing 3
    bot.Move.XY(-22275, -12462, "Move to area 2")
    bot.Move.XY(-21671, -2163, "Aggro: Berzerker")
    bot.Move.XY(-19592, 772, "Aggro: Berzerker")
    bot.Move.XY(-13795, -751, "Aggro: Berzerker")
    bot.Move.XY(-17012, -5376, "Aggro: Berzerker")
    bot.Move.XY(-10606.23, -1625.26)
    bot.Move.XY(-12158.00, -4277.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-12158.00, -4277.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 3
    bot.Wait.ForTime(10000)
    
    # Path to blessing 4
    bot.Move.XY(-12071, -4274, "Aggro: Berzerker")
    bot.Move.XY(-8351, -2633, "Move to regroup")
    bot.Move.XY(-4362, -1610, "Aggro: Lake")
    bot.Move.XY(-4316, 4033, "Aggro: Lake")
    bot.Move.XY(-8809, 5639, "Aggro: Lake")
    bot.Move.XY(-14916, 2475)
    bot.Move.XY(-11204.00, 5479.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-11204.00, 5479.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 4
    bot.Wait.ForTime(10000)
    
    # Path to blessing 5
    bot.Move.XY(-11282, 5466, "Aggro: Elemental")
    bot.Move.XY(-16051, 6492, "Aggro: Elemental")
    bot.Move.XY(-16934, 11145, "Aggro: Elemental")
    bot.Move.XY(-19378, 14555)
    bot.Move.XY(-22889.00, 14165.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-22889.00, 14165.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 5
    bot.Wait.ForTime(10000)
    
    # Path to blessing 6
    bot.Move.XY(-22751, 14163, "Aggro: Elemental")
    bot.Move.XY(-15932, 9386, "Move to camp")
    bot.Move.XY(-13777, 8097, "Aggro: Lake")
    bot.Move.XY(-2217.00, 14914.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-2217.00, 14914.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 6
    bot.Wait.ForTime(10000)
    
    # Continue route
    # bot.Move.XY(-2290, 14879, "Aggro: Modnir")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-1810, 4679, "Move to boss")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-6911, 5240, "Aggro: Boss")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-15471, 6384, "Move to regroup")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-411, 5874, "Aggro: Modniir")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(2859, 3982, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(4909, -4259, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(7514, -6587, "Aggro: Berserker")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(3800, -6182, "Aggro: Berserker")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(7755, -11467, "Aggro: Elementals and Griffins")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(15403, -4243, "Aggro: Elementals and Griffins")
    # bot.Wait.UntilOutOfCombat()
    
    # # Path to blessing 7
    # bot.Move.XY(21597, -6798)
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-2217.00, 14914.00)
    # bot.Wait.ForTime(5000)
    # bot.Move.XYAndInteractNPC(-2217.00, 14914.00)
    # bot.Multibox.SendDialogToTarget(0x84) #Blessing 7
    # bot.Wait.ForTime(10000)
    
    # bot.Move.XY(24522, -6532, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(22883, -4248, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(18606, -1894, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(14969, -4048, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(13599, -7339, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(10056, -4967, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(10147, -1630, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    
    # # Path to blessing 8
    # bot.Move.XY(8963, 4043, "Take blessing 8")
    # bot.Wait.ForTime(5000)
    # bot.Move.XYAndInteractNPC(8963, 4043)
    # bot.Multibox.SendDialogToTarget(0x84) #Blessing 8
    # bot.Wait.ForTime(10000)
    
    # bot.Move.XY(9339.46, 3859.12, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(15576, 7156, "Aggro: Berserker")
    # bot.Wait.UntilOutOfCombat()
    
    # # Path to blessing 9
    # bot.Move.XY(22838, 7914, "Take blessing 9")
    # bot.Wait.ForTime(5000)
    # bot.Move.XYAndInteractNPC(22838, 7914)
    # bot.Multibox.SendDialogToTarget(0x84) #Blessing 9
    # bot.Wait.ForTime(10000)
    
    # # Final route section
    # bot.Move.XY(22961, 12757, "Move to shrine")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(18067, 8766, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(13311, 11917, "Aggro: Area")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(13714, 14520, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(11126, 10443, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(5575, 4696, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-503, 9182, "Aggro: Modniir and Elemental 2")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(1582, 15275, "Aggro: Modniir and Elemental 2")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(7857, 10409, "Aggro: Modniir and Elemental 2")
    # bot.Wait.UntilOutOfCombat()
    
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    
    bot.Wait.ForTime(5000)
    bot.States.JumpToStepName("[H]Norn title farm by Wick Divinus_1")
    
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
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    GLOBAL_CACHE.Map
    # Player revived on same map → jump to recovery step
    bot.States.JumpToStepName("[H]Start Combat_3")
    bot.config.FSM.resume()
    
def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot)) 

bot.SetMainRoutine(bot_routine)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path="Reforged_Icon.png")

if __name__ == "__main__":
    main()
