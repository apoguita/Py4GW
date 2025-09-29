from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Range, Console, ConsoleLog
import Py4GW

BOT_NAME = "VQ Morostav Trail"
TEXTURE = Py4GW.Console.get_projects_path() + "//Vanquished_Helmet.png"
OUTPOST_TO_TRAVEL = 298 #Unwaking Waters
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
    bot.Templates.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    
    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(-14168,-8050,205) #Morostav Trail exit to Unwaking Waters
    bot.Wait.ForTime(4000)
    bot.Move.XYAndInteractNPC(22155.34, 12125.13)
    bot.Multibox.SendDialogToTarget(0x86) #Get Bounty
    bot.States.AddHeader("Start Combat") #3
    bot.Multibox.UseAllConsumables()
    bot.States.AddManagedCoroutine("Upkeep_Multibox_Consumables", lambda: _upkeep_multibox_consumables(bot))
    path = [(19283.57, 12803.82), #pack1
            (20840.22, 8834.50) , #round the corner
            (16449.09, 9398.16),  #hunt pack3
            (17075.29, 11542.65), #boss hole
            (16726.07, 8022.25),  #hunt pack under root
            (14536.42, 7882.84),  #hunt more
            (14301.47, 10907.79), #inner pack
            (9584.61, 7463.74),   #fork

            (7995.83, 2784.03), #shore pop up
            (6276.70, 3501.12), #shore pop up 2
            (9708.27, 10151.21), #back to fork
            (11146.95, 11058.01), #around the fork

            (3864.64, 10955.62), #fork 2 rest
            (4661.88, 8195.97), #fork pop up
            (3717.29, 4726.01), #fork 2 shore
            (2058.90, 8523.23), #fork 2 narrow path

            (-2809.45, 5616.83), #patrol
            (-3830.95, 2980.44), #fork 3
            (1208.90, 1636.80), #fork3 shore
            (1808.52, -210.84), #fork 3 pop up
            (-3830.95, 2980.44), #fork 3
            (-4466.05, -3042.06), #sanity pop ups corridor
            (-3830.95, 2980.44), #fork 3
            (-8124.41, 1811.43), #before big area

            #left area
            (-10910.36, 3394.90), #inner patrol
            (-12340.56, 1729.70), #patrol 
            (-11702.48, 392.32), #blooddrinker patrol
            (-15392.24, 229.49), #boss hole
            (-13211.56, 5161.36), #Around the patrols
            (-16117.06, 7344.00), #fungal wallows
            (-15516.23, 5475.97), #hill base
            (-20066.16, 5669.60), #around the mountain near res shrine
            (-17902.03, 10859.59), #Dredges
            (-9231.53, -559.27), #blood drikers (far)
            (-9368.10, -5884.38), #stone pop ups
            (-11865.10, -2936.87), #blood drinker patrol
            (-8437.68, -6600.21), #door

            #center area
            (-6317.80, -7314.83), #patrols
            (-4490.83, -8522.61), #stone pop ups
            (-5057.49, -4348.15), #patrols
            (-2541.39, -3694.41),
            (-3897.96, -6575.30), #cross
            (-1685.32, -4872.92),
            (-925.03, -2848.67), #patrol and stone pop ups
            #res shrine
            (-1099.51, -6853.82),
            (624.54, -5716.24), #stone pop ups

            #big room
            (4233.68, -4846.76), #Dredges
            (3809.45, -1779.69), #shore pop ups
            (7325.51, -7398.68), #fungus patrols  \
            #res shrine
            (10400.24, -6050.92), #patrol
            (10116.56, -3449.12), #multi patrols danger
            (11055.48, -2158.53), #pop ups danger
            (8462.69, -1815.47),  #hill patrol danger

            #danger room
            (13641.88, 165.81), 
            (15200.67, -542.67), #around the mountain
            (15679.82, -1033.62), #pop ups
            (14458.41, -2669.81), #bosses danger
            (9555.91, -765.55), #bridge base
            (8071.68, 2811.61), #shore
            (5180.92, 961.27), #boss
    ]
    bot.Move.FollowAutoPath(path, "Kill Route")
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.Templates.PrepareForFarm(map_id_to_travel=HZH)
    bot.Multibox.DonateFaction()
    bot.Wait.ForTime(15000)
    bot.States.JumpToStepName("[H]VQ Morostav Trail_1")
    
def _upkeep_multibox_consumables(bot: "Botting"):
    while True:
        yield from bot.helpers.Wait._for_time(15000)
        if not Routines.Checks.Map.MapValid():
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
    bot.config.FSM.pause()
    ConsoleLog("on_party_member_behind","event triggered")
    yield from bot.helpers.Multibox._pixel_stack()
    
    while not Routines.Checks.Party.IsAllPartyMembersInRange(Range.Earshot.value):
        yield from bot.helpers.Wait._for_time(1000)
        if not Routines.Checks.Map.MapValid():
            break
    
      
def OnPartyMemberBehind(bot: "Botting"):
    bot.States.AddManagedCoroutine("OnBehind_OPD", lambda: _on_party_member_behind(bot))
    
def _on_party_member_death_behind(bot: "Botting"):
    bot.config.FSM.pause()
    ConsoleLog("on_party_member_dead_behind","event triggered")
    dead_player = Routines.Party.GetDeadPartyMemberID()
    if dead_player == 0:
        bot.config.FSM.resume()
        return

    pos = GLOBAL_CACHE.Agent.GetXY(dead_player)
    yield from bot.helpers.Move.get_path_to(pos[0], pos[1])
    yield from bot.helpers.Move.follow_path()
    bot.config.FSM.resume()

def OnPartyMemberDeathBehind(bot: "Botting"):
    bot.States.AddManagedCoroutine("OnDeathBehind_OPD", lambda: _on_party_member_death_behind(bot))
    
def _on_party_wipe(bot: "Botting"):
    bot.config.FSM.pause()
    ConsoleLog("on_party_wipe","event triggered")
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.helpers.Wait._for_time(1000)
        if not Routines.Checks.Map.MapValid():
            break
    bot.States.JumpToStepName("[H]Start Combat_3")
    bot.config.FSM.resume()
    
def OnPartyWipe(bot: "Botting"):
    bot.States.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

bot.SetMainRoutine(bot_routine)

def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)

if __name__ == "__main__":
    main()
