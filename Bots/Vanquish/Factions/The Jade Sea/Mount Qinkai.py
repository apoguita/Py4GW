from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Range, Utils, ConsoleLog
import Py4GW
import os
BOT_NAME = "VQ Mount Qinkai"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
OUTPOST_TO_TRAVEL = 389 # Mount Qinkai outpost
HZH= 193 # Cavalon for faction donation

Vanquish_Path:list[tuple[float, float]] = [
        (-8394, -9801),    # First waypoint - get blessing here
        (-13046, -9347),   # Continue path
        (-17348, -9895), 
        (-17929, -10300),
        (-14702, -6671), 
        (-11080, -6126), 
        (-13426, -2344), 
        (-15055, -3226),
        (-9448, -283), 
        (-9918, 2826), 
        (-8721, 7682), 
        (-3749, 8053),
        (-7474, -1144), 
        (-9666, 2625), 
        (-5895, -3959), 
        (-3509, -8000),
        (-195, -9095), 
        (6298, -8707), 
        (3981, -3295), 
        (496, -2581),
        (2069, 1127), 
        (5859, 1599), 
        (6412, 6572), 
        (10507, 8140),
        (14403, 6938), 
        (18080, 3127), 
        (13518, -35), 
        (13450, -6084),
        (13764, -4816), 
        (13450, -6084), 
        (15390, -8892), 
        (13764, -4816)  # Final waypoint
    ]

bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True)
                
def bot_routine(bot: Botting) -> None:
    global Vanquish_Path
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    
    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(-5490, 13672, 200) # Mount Qinkai
    bot.Wait.ForTime(4000)
    bot.Move.XYAndInteractNPC(-8394, -9801)
    bot.Multibox.SendDialogToTarget(0x86) #Get Bounty
    bot.States.AddHeader("Start Combat") #3
    bot.Multibox.UseAllConsumables()
    bot.States.AddManagedCoroutine("Upkeep Multibox Consumables", lambda: _upkeep_multibox_consumables(bot))
    
    bot.Move.FollowAutoPath(Vanquish_Path, "Kill Route")
    bot.Wait.UntilOutOfCombat()
    #bot.States.AddCustomState(lambda: _reverse_path(), "Reverse Path") #if not VQ we reverse path
    #bot.Move.FollowAutoPath(Vanquish_Path, "Return Route")
    #bot.Wait.UntilOutOfCombat()
    
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.Multibox.DonateFaction()
    bot.Wait.ForTime(20000)
    bot.States.JumpToStepName("[H]VQ Mount Qinkai_1")
    
def _upkeep_multibox_consumables(bot :"Botting"):
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
            

def _reverse_path():
    global Vanquish_Path
    if GLOBAL_CACHE.Map.GetIsVanquishComplete():
        Vanquish_Path = []
        yield 
        return
    
    Vanquish_Path = list(reversed(Vanquish_Path))
    yield
    
def _on_party_wipe(bot: "Botting"):
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

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
    bot.UI.draw_window(icon_path=TEXTURE)

if __name__ == "__main__":
    main()