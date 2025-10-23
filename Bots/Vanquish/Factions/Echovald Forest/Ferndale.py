from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Range, Utils, ConsoleLog
import Py4GW
import os
BOT_NAME = "VQ Ferndale"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
HZH= 77

Vanquish_Path:list[tuple[float, float]] = [
        (-9358.26, 12733.01), #middle patrol
        (-11763.50, 6875.62), #bridge patrol
        (-8343.50, 10348.14), #spawn under bridge
        (-9358.26, 12733.01), #middle patrol point
        (-11057.97, 20483.20), #mushrooms at the top
        (-5486.26, 18571.37), #up the staris
        (-5214.33, 15808.12), #bridge
        (-3129.34, 15116.34), #around the rock
        (-1997.73, 19808.71), 
        (937.34, 14460.03), #floodfill
        (-1552.20, 12181.78), #left side
        (-418.83, 9722.58),
        (1623.41, 11681.61),
        (2353.03, 8665.77), 
        (3497.35, 7112.98),
        (4920.25, 14639.28), #issue!!!! stuck?
        #(3471.81, 13055.59), #middle part (biggest)
        #(4150.67, 15073.04),
        (4777.39, 8038.80),
        (6225.68, 14860.03),
        (7747.10, 12009.60), #oni spawn
        (9991.06, 11601.30),
        (9188.73, 16076.83),
        (12075.11, 18961.69), #stairs
        (11635.97, 9944.48), #right side
        (3388.01, 5963.63), #FORK MOUNTAINS
        (-2324.46, 224.24), #engage patrols
        (4964.69, 4695.06), #around right mountains
        (9769.06, 3201.43),
        (11953.75, 9212.22), #right patrol and spawns
        (14419.30, 1311.15),
        (8990.68, 518.77), #right pocket
        (9532.74, -2186.87),
        (5588.56, -1831.51),
        (4358.47, -3596.96), #bridge stuff
        (2391.71, -3199.59),
        (-811.80, -2427.94), #pop ups
        (4681.77, -12246.70), #tendrils foodfill
        (8444.18, -11786.52),
        (8241.50, -13956.31),
        (10657.37, -17255.84), #right tendril
        (14073.04, -19839.37),
        (3291.92, -13745.13), #left tendril
        (3629.04, -14834.70), #oni spawn
        (-7260.26, -18284.58),
        (1653.33, -10685.74), #garden
        (-531.23, -10904.48), #floodfill lower garden
        (-114.91, -9269.86), 
        (-2798.66, -7118.50), #floodfill garden
        (-7398.05, -6884.35),
        (-9947.11, -8920.49), #oni spawn
        (-8121.48, -5619.89), 
        (-2614.03, -5811.48),
        (-2540.95, -3791.90),
        (-5708.50, -3462.03),
        (-7744.69, -4578.63),
        (-7268.23, -1897.74), 
        (-4026.24, 152.70), #end garden floodfill
        (-10708.04, 1472.96), #finish left side spawns
        (-12390.78, 6997.02), 
        (-10708.04, 1472.96),
        (-4870.12, 3132.08),
        (-4187.85, 6256.14), 
        (-828.52, 8779.88), #finish right forks
        (-6834.56, 8525.84), #bridge spawns
        (-1292.07, 14085.61)
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
