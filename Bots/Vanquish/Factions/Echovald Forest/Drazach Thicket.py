from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Range, Utils, ConsoleLog
import Py4GW
import os

BOT_NAME = "VQ Drazach Thicket"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
OUTPOST_TO_START = 222 #Eternal Grove Outpost
COORDS_TO_EXIT_OUTPOST = (-7544,14343) #to Drazach Thicket
EXPLORABLE_TO_VANQUISH = 195 #Drazach Thicket
COORDS_FOR_PRIEST = (-5592.00, -16263.00) #to priest
DIALOG_FOR_PRIEST = 0x86
HOUSE_ZU_HELZER = 77 #House Zu Helzer

Vanquish_Path = [(-9878.31, -14870.55), #ugly first corner
                (-6024.71, -10824.51), #first room
                (-4546.84, -9157.54), #right
                (-6683.80, -8867.51), #ambush 
                (-7756.96, -9672.30), #left

                (-5651.87, -6857.37), #connector room
                (-6603.41, -5635.55),

                (-11036.84, -8096.66), #left ambush room
                (-12024.07, -8840.55), #far pop ups

                (-10875.07, -5594.80), #left hallway
                (-10516.25, -2471.60), #left lower room
                (-9792.65, -536.86), #hallway
                (-11308.45, 3273.95), #hallway tendril
                (-12730.60, 5712.96), #patrol hidden
                (-7237.03, -2142.75), #oni pop ups
                (-7105.36, -2426.90), #oni pop ups 2

                (-4554.99, 776.04), #next hallway
                (-1223.03, 2129.13), #floodfill
                (-1896.83, 5606.69), 
                #(2774.97, 3717.76),
                (-1813.93, -2020.71), 
                (-5234.42, -5652.45), 

                (211.23, -5091.44), #rock spawn
                (1371.50, -4038.61), 
                (3255.87, -4785.59),
                (1558.04, -6938.50), 
                (668.36, -9314.83),
                (2366.87, -9547.91), 

                (5625.59, -1360.20), #room over slope
                (4755.49, 821.61),
                (7347.70, 311.06),

                (9152.04, 4514.65), #right side
                (13031.58, 7149.48),
                (9152.04, 4514.65), #back to right side
                (7016.99, 6483.00), 
                (3104.65, 10852.02), 

                (8982.88, 10737.52), #top
                (7201.44, 13909.25), 
                (7109.79, 12134.53), 
                (3154.82, 11441.71), 

                (1574.23, 15445.42), #snake top pop ups
                (-1110.71, 15221.18), 
                (-5693.68, 15871.91),

                (-6212.60, 13582.10), #star road
                (-4150.74, 12059.19),
                (-5363.25, 10258.17),

                (-2856.84, 10372.21), #to the right
                (1247.34, 9651.55),
                (2498.04, 11076.82),

                (-2488.08, 8399.15), #patrol trigger
                (-2095.59, 7311.56), #to the center
                (-3500.78, 6488.78), #oni spawn
                (-6663.06, 4662.32), #tendril
                (-5713.13, 8684.84), #group

                (-7201.17, 9957.66), #back to star
                (-7640.64, 12424.33), 
                (-10422.90, 10846.65), 

                (-12227.19, 7684.96), #left
                (-12730.60, 5712.96), #patrol hidden
                (-10030.67, 4909.71), 
                
    ]

bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True)
                
def bot_routine(bot: Botting) -> None:
    #events
    global Vanquish_Path
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_START)
    
    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(*COORDS_TO_EXIT_OUTPOST,EXPLORABLE_TO_VANQUISH) #Morostav Trail exit to Unwaking Waters
    bot.Wait.ForTime(4000)
    bot.Move.XYAndInteractNPC(*COORDS_FOR_PRIEST)
    bot.Multibox.SendDialogToTarget(DIALOG_FOR_PRIEST) #Get Bounty
    bot.States.AddHeader("Start Combat") #3
    bot.Multibox.UseAllConsumables()
    #bot.States.AddManagedCoroutine("Upkeep_Multibox_Consumables", lambda: _upkeep_multibox_consumables(bot))

    bot.Move.FollowAutoPath(Vanquish_Path, "Kill Route")
    bot.Wait.UntilOutOfCombat()
    
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=HOUSE_ZU_HELZER)
    bot.Multibox.DonateFaction()
    bot.Wait.ForTime(20000)
    bot.States.JumpToStepName("[H]VQ Drazach Thicket_1")
    
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
