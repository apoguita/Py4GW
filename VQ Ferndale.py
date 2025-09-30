from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Range, Utils, ConsoleLog
import Py4GW

BOT_NAME = "VQ Ferndale"
TEXTURE = Py4GW.Console.get_projects_path() + "//Vanquished_Helmet.png"

HZH= 77

bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True)
                
def bot_routine(bot: Botting) -> None:
    #events
    #party member left behind
    condition = lambda: OnPartyMemberBehind(bot)
    bot.Events.OnPartyMemberBehindCallback(condition)
    #party member dead behind
    condition = lambda: OnPartyMemberDeathBehind(bot)
    bot.Events.OnPartyMemberDeadBehindCallback(condition)
    #party wipe
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.PrepareForFarm(map_id_to_travel=HZH)
    
    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(10446, -1147,210) #Ferndale
    bot.Wait.ForTime(4000)
    bot.Move.XYAndInteractNPC(-12909.00, 15616.00)
    bot.Multibox.SendDialogToTarget(0x86) #Get Bounty
    bot.States.AddHeader("Start Combat") #3
    bot.Multibox.UseAllConsumables()
    bot.States.AddManagedCoroutine("Upkeep_Multibox_Consumables", lambda: _upkeep_multibox_consumables(bot))
    Ferndale = [
        (-10166.0, 9355.0),
        (-8861.0, 10761.0),
        (-9327.0, 14264.0),
        (-10560.0, 17028.0),
        (-12126.0, 19243.0),
        (-11499.0, 20293.0),
        (-9356.0, 19472.0),
        (-8532.0, 19509.0),
        (-6647.0, 19811.0),
        (-5644.0, 18769.0),
        (-5164.0, 15703.0),
        (-5532.0, 18292.0),
        (-3431.0, 19554.0),
        (-1635.0, 19823.0),
        (821.0, 15267.0),
        (2905.0, 15017.0),
        (7394.0, 16019.0),
        (9580.0, 16248.0),
        (11417.0, 18904.0),
        (9543.0, 15348.0),
        (9398.0, 13417.0),
        (11589.0, 13283.0),
        (11794.0, 10356.0),
        (11648.0, 10179.0),
        (9972.0, 9346.0),
        (7458.0, 8882.0),
        (3776.0, 6845.0),
        (3752.0, 6242.0),
        (5189.0, 4619.0),
        (6394.0, 4092.0),
        (8922.0, 3668.0),
        (9569.0, 2893.0),
        (12229.0, 3743.0),
        (13981.0, 1566.0),
        (14962.0, 1329.0),
        (12806.0, 3177.0),
        (12694.0, 5036.0),
        (13053.0, 6566.0),
        (13008.0, 8202.0),
        (11466.0, 9395.0),
        (11858.0, 12920.0),
        (8775.0, 13824.0),
        (8961.0, 15157.0),
        (7380.0, 15079.0),
        (6047.0, 15121.0),
        (4148.0, 15018.0),
        (3519.0, 14529.0),
        (2246.0, 12958.0),
        (1157.0, 12277.0),
        (-252.0, 11399.0),
        (236.0, 9655.0),
        (1299.0, 10049.0),
        (1930.0, 9030.0),
        (2550.0, 8265.0),
        (3559.0, 6563.0),
        (4860.0, 7711.0),
        (5894.0, 8624.0),
        (8140.0, 11040.0),
        (8810.0, 12012.0),
        (9050.0, 12876.0),
        (704.0, 12645.0),
        (-4761.0, 15572.0),
        (-2201.0, 14383.0),
        (-1760.0, 13705.0),
        (-2528.0, 12058.0),
        (-4742.0, 10742.0),
        (-5173.0, 8726.0),
        (-5324.0, 8397.0),
        (-3936.0, 6274.0),
        (-1311.0, 8367.0),
        (-3765.0, 6173.0),
        (-4474.0, 3839.0),
        (-4132.0, 6355.0),
        (-6112.0, 8309.0),
        (-9147.0, 8828.0),
        (-9929.0, 8857.0),
        (-12276.0, 7118.0),
        (-10972.0, 6380.0),
        (-11062.0, 2938.0),
        (-10703.0, 1038.0),
        (-7880.0, 2550.0),
        (-6168.0, 2954.0),
        (-5233.0, 2459.0),
        (-4465.0, 910.0),
        (-4746.0, 19.0),
        (-2865.0, -153.0),
        (-1270.0, 1063.0),
        (703.0, 2572.0),
        (1813.0, 3627.0),
        (2178.0, 4085.0),
        (-3071.0, -377.0),
        (-6735.0, -1447.0),
        (-8566.0, -3474.0),
        (-8398.0, -6178.0),
        (-8380.0, -7556.0),
        (-9558.0, -8679.0),
        (-8461.0, -7796.0),
        (-6293.0, -7455.0),
        (-7092.0, -4184.0),
        (-5788.0, -3299.0),
        (-3791.0, -1121.0),
        (-1972.0, -2206.0),
        (-23.0, -2434.0),
        (355.0, -2379.0),
        (1149.0, -2522.0),
        (-1642.0, -2598.0),
        (-3099.0, -4228.0),
        (-4741.0, -5315.0),
        (-2723.0, -7449.0),
        (-1146.0, -9239.0),
        (-833.0, -10064.0),
        (-612.0, -11067.0),
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
        (8511.0, -14698.0),
        (8339.0, -15559.0),
        (9471.0, -17038.0),
        (10715.0, -17162.0),
        (12262.0, -18031.0),
        (12688.0, -18252.0),
        (11570.0, -17722.0),
        (9393.0, -17134.0),
        (7898.0, -15955.0),
        (7228.0, -15298.0),
        (6941.0, -14395.0),
        (5138.0, -13272.0),
        (4258.0, -13911.0),
        (3408.0, -14215.0),
        (1913.0, -16522.0),
        (327.0, -17969.0),
        (-294.0, -18315.0),
        (-2054.0, -18747.0),
        (-3569.0, -19027.0),
        (-5662.0, -17885.0),
        (-6836.0, -18019.0),
    ]
    bot.Move.FollowAutoPath(Ferndale, "Kill Route")
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.Multibox.DonateFaction()
    bot.Wait.ForTime(15000)
    bot.States.JumpToStepName("[H]VQ Ferndale_1")
    
def _upkeep_multibox_consumables(bot: "Botting"):
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
            

def _on_party_member_behind(bot: "Botting"):
    print("Party Member behind, emitting pixel stack")
    yield from Routines.Yield.Movement.StopMovement()
    yield from bot.helpers.Multibox._pixel_stack()

    last_emit = Utils.GetBaseTimestamp()
    while not Routines.Checks.Party.IsAllPartyMembersInRange(Range.Earshot.value):
        yield from bot.helpers.Wait._for_time(500)

        # Reissue pixel stack every 10000 ms
        now = Utils.GetBaseTimestamp()
        if now - last_emit >= 10000:
            print("Re-emitting pixel stack")
            yield from bot.helpers.Multibox._pixel_stack()
            last_emit = now

        if not Routines.Checks.Agents.InDanger():
            yield from Routines.Yield.Movement.StopMovement()
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            yield
            break

    print("Party Member in range, resuming")
    bot.config.FSM.resume()
    yield

    
      
def OnPartyMemberBehind(bot: "Botting"):
    print ("Party Member behind, Triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnBehind_OPD", _on_party_member_behind(bot))

    
def _on_party_member_death_behind(bot: "Botting"):
    dead_player = Routines.Party.GetDeadPartyMemberID()
    if dead_player == 0:
        bot.config.FSM.resume()
        return

    pos = GLOBAL_CACHE.Agent.GetXY(dead_player)
    path = [(pos[0], pos[1])]
    bot.helpers.Move.set_path_to(path)
    yield from bot.helpers.Move._follow_path()
    bot.config.FSM.resume()

def OnPartyMemberDeathBehind(bot: "Botting"):
    ConsoleLog("on_party_member_dead_behind","event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeathBehind_OPD", lambda: _on_party_member_death_behind(bot))
    
def _on_party_wipe(bot: "Botting"):
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.helpers.Wait._for_time(1000)
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
