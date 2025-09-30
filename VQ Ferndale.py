from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Range, Utils, ConsoleLog
import Py4GW

BOT_NAME = "VQ Ferndale"
TEXTURE = Py4GW.Console.get_projects_path() + "//Vanquished_Helmet.png"
HZH= 77

Vanquish_Path:list[tuple[float, float]] = [
        (-10166.0, 9355.0), #bridge Patrol
        (-8861.0, 10761.0), #spawn under bridge
        (-10560.0, 17028.0), #hill
        (-11499.0, 20293.0), #shrooms
        (-5644.0, 18769.0), #stairs
        (-5164.0, 15703.0), #corner and bridge
        (-5532.0, 18292.0), 
        (-1635.0, 19823.0), #over rock
        (9580.0, 16248.0), #around top
		(12499.93, 19223.35),
        (11794.0, 10356.0), #right
        (3776.0, 6845.0), #to fork
		(2439.09, 4549.33), #engage patrol
        (8922.0, 3668.0), #trough bridge
        (13981.0, 1566.0), #onix spawn
        (8775.0, 13824.0), #back to big room far
        (6047.0, 15121.0),
        (4148.0, 15018.0),
		(1718.32, 14582.40),
        (1157.0, 12277.0),
		(519.32, 9930.01), #added unstuck 
		(-429.58, 9365.55),
        (-252.0, 11399.0),
        (236.0, 9655.0),
		(2927.17, 9195.88),
        (1299.0, 10049.0),
        (1930.0, 9030.0),
        (8140.0, 11040.0), #onyx spawn
        (8810.0, 12012.0),
        (9050.0, 12876.0),
        (704.0, 12645.0),
        (-4761.0, 15572.0), #bridge
        (-2201.0, 14383.0),
        (-1760.0, 13705.0),
        (-3936.0, 6274.0), #to fork
        (-1311.0, 8367.0), #back
        (-4474.0, 3839.0),
        (-12276.0, 7118.0), #corner
        (-10972.0, 6380.0),
        (-10703.0, 1038.0),
        (-4746.0, 19.0), #garden
        (2178.0, 4085.0), #end fork
        (-6735.0, -1447.0), #garden stairs
        (-8566.0, -3474.0), #onyx spawn
        (-9942.78, -8803.36),
        (-6293.0, -7455.0),
        (-7092.0, -4184.0), #out of garden
        (-3791.0, -1121.0),
        (-23.0, -2434.0),
        (355.0, -2379.0), #across Garden
        (-3099.0, -4228.0),
        (-612.0, -11067.0),#boss spawn
        (821.0, -10173.0),
        (3390.0, -12037.0),
        (4463.0, -11023.0),
        (4807.0, -9845.0),
        (5129.0, -8744.0),
        (5618.0, -7067.0),
        (5716.0, -6254.0),
        (5252.0, -5325.0),
        (4691.0, -3853.0),
        (5299.0, -2241.0),
        (4869.0, -2143.0),
        (2730.0, -3075.0),
        (5561.0, -1964.0),
        (8398.0, -2521.0),
        (9970.0, -3052.0),
        (10800.0, -2639.0),
        (10832.0, -1580.0),
        (10121.0, -1074.0),
        (9855.0, 247.0),
        (9453.0, 2002.0),
        (9791.0, 3194.0),
        (7856.0, 87.0),
        (7508.0, -1235.0),
        (5245.0, -2593.0),
        (4777.0, -3761.0),
        (5738.0, -6775.0),
        (5223.0, -8348.0),
        (4813.0, -9391.0),
        (4951.0, -11169.0),
        (6193.0, -11747.0),
        
        (7659.0, -11088.0),
        (8959.0, -11489.0),
        (11570.0, -17722.0),
        (327.0, -17969.0),
        (-6836.0, -18019.0),
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
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=HZH)
    
    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(10446, -1147,210) #Ferndale
    bot.Wait.ForTime(4000)
    bot.Move.XYAndInteractNPC(-12909.00, 15616.00)
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
    bot.States.JumpToStepName("[H]VQ Ferndale_1")
    
def _upkeep_multibox_consumables(bot :"Botting"):
    while True:
        yield from bot.helpers.Wait._for_time(15000)
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
            yield from bot.helpers.Wait._for_time(250)
            

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
        yield from bot.helpers.Wait._for_time(1000)
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
    bot.UI.draw_window(icon_path=TEXTURE)

if __name__ == "__main__":
    main()
