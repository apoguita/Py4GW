from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Map, Utils, ConsoleLog
import Py4GW
import os
BOT_NAME = "VQ Mount Qinkai"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
OUTPOST_TO_TRAVEL = 389 # Mount Qinkai outpost
CAVALON= 193 # Cavalon for faction donation

Vanquish_Path:list[tuple[float, float]] = [
      (-13384.42, -9866.60), #snake yetis  
      (-17490.23, -10193.84), #tendril
      (-13498.94, -4763.97),
      (-11674.48, -4599.29), #wallow patrol
      (-14406.66, -2555.92), #hole
      (-13735.23, -1511.41), #exit hole
      (-10319.44, 2159.07), #cave entrance
      (-7937.16, 3062.79), #wallow patrol
      (-9173.34, 7675.70),
      (-8041.39, 8370.92),
      (-4787.85, 6801.43), #clear
      (-3314.36, 7860.74),
      (-2001.17, 9037.19),
      (-6694.74, 2240.26), #out of cave
      (-9176.05, -13.35),
      (-6789.09, 189.53), #just in case
      (-6890.70, -3249.73), #lower wallows
      (-8307.69, -5465.48),
      (-5021.97, -3830.00),
      (-2310.74, -8512.54),
      (1983.03, -8555.85), #lower oxix
      (6484.80, 1017.07), #wallow patrol
      (6212.15, -8736.39), #beach onis
      (11368.18, -7458.21), #beach patrol
      (14728.93, -9258.35),
      (14774.19, -4493.75),
      (11622.91, -4078.38),
      (13287.39, 296.37),
      (16030.41, 6932.02),
      (11591.91, 7965.41), #water
      (10822.86, 9232.65),
      (7920.46, 5972.42),
      (6274.33, 7410.21), #hill
      (5824.00, 5289.97),
      (4266.50, 5832.48),
      
      (1506.29, 1406.74), #last aptrols
      (1737.57, 1202.17),
      (4450.66, 1146.03), #just in case
      (700.20, -398.73),
      (-273.59, -2516.34),
      (95.02, -3131.64),
      (-1687.58, -3565.68),

      
      
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

    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=CAVALON)
    bot.Multibox.DonateFaction()
    bot.Wait.ForTime(30000)
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
    if Map.IsVanquishCompleted():
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