from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Range, Utils, ConsoleLog
import Py4GW
import os
BOT_NAME = "Secret Lair of the Snowmen"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
GROTTO = 639
SECRET_LAIR = 701
HZH= 77

middle_path = [
    (-13752.06, -504.66),
    (-12084.77, -1592.58),
    (-12745.70, -3899.97),
    (-13262.00, -7346.00),
    (-14891.95, -10069.69),
    (-9573.00, -10963.00)
]



bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True)
                
def bot_routine(bot: Botting) -> None:
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=GROTTO) 
    bot.States.AddHeader("Start Loop")
    #bot.Party.SetHardMode(True)
    bot.Move.XYAndDialog(-23884, 13954,0x84)
    bot.Wait.ForMapToChange(target_map_id=SECRET_LAIR)
    bot.Move.XYAndInteractNPC(-14078.00, 15449.00)
    bot.Multibox.PixelStack()
    bot.Wait.ForTime(4000)
    bot.Multibox.SendDialogToTarget(0x84) #Get Blessing
    bot.States.AddHeader("Start Combat") #3
    #bot.Multibox.UseAllConsumables()
    #bot.States.AddManagedCoroutine("Upkeep_Multibox_Consumables", lambda: _upkeep_multibox_consumables(bot))

    bot.Move.XY(-14543.05, 12171.06) #before first pack
    bot.UI.PrintMessageToConsole("pixelstack","#0")
    bot.Multibox.PixelStack() #0
    bot.Wait.ForTime(4000)
    starting_path = [
    (-15628, 9589),
    (-17602, 6858),
    (-19769, 5046),
    (-16697.96, 1302.89),
    ]
    bot.Move.FollowAutoPath(starting_path, "Kill Route")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-15775.88, 2963.18)
    bot.UI.PrintMessageToConsole("pixelstack","#1")
    bot.Multibox.PixelStack() #1
    bot.Wait.ForTime(4000)
    bot.Move.XY(-12482.00, 3924.00)
    bot.Move.XYAndInteractNPC(-12482.00, 3924.00) #interact with beacon of droknars
    bot.Multibox.InteractWithTarget() #activate beacon
    
    bot.Move.XY(-14155.53, 494.25)
    bot.Multibox.PixelStack()
    bot.Wait.ForTime(4000)
    
    bot.Move.FollowAutoPath(middle_path, "Kill Route 2")
    bot.Wait.UntilOutOfCombat()
    
    values = [
        1246843460,
        843900544,
        1273891916,
        1635507500,
        1584740864,
        1832505952,
        1635566384, #boss key
        # add more values manually here
    ]
    bot.Interact.WithKeyByBitmask()
    bot.Move.XYAndInteractNPC(-16093.00, -10723.00) #beacon of droknars
    bot.Multibox.PixelStack() #2
    bot.Multibox.InteractWithTarget() #activate beacon
    bot.Wait.ForTime(4000)
    
    bot.Move.XY(-15756.00, -12335.00)
    bot.Wait.UntilOutOfCombat()
    
    bot.Move.XYAndInteractNPC(-15435.00, -12277.00) #lock
    bot.Wait.ForTime(2000)
    bot.Move.XY(-17542.00, -14048.00)
    bot.Multibox.PixelStack() #2
    bot.Wait.ForTime(4000)
    bot.Move.XY(-13088.00, -17749.00)
    bot.Wait.UntilOutOfCombat() # ??
    bot.Interact.WithKeyByBitmask() #boss key
    bot.UI.PrintMessageToConsole("finished lair", "exiting")
    bot.Wait.ForTime(5000)
    
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName("[H]Start Loop_3")

    

def _on_party_wipe(bot: "Botting"):
    from Py4GWCoreLib import GLOBAL_CACHE, Routines

    print("[OnPartyWipe] Coroutine started")

    try:
        print("[OnPartyWipe] Step 0: Checking MapValid()...")
        if not Routines.Checks.Map.MapValid():
            print("[OnPartyWipe] Map invalid at start → exiting, resuming FSM")
            bot.config.FSM.resume()
            return

        # 1) ignore false-wipe if the player is NOT actually dead
        print("[OnPartyWipe] Step 1: Checking if player is actually dead...")
        player_id = GLOBAL_CACHE.Player.GetAgentID()
        player_dead = GLOBAL_CACHE.Agent.IsDead(player_id)
        print(f"[OnPartyWipe] PlayerDead = {player_dead}")

        if not player_dead:
            print("[OnPartyWipe] Player is alive → false wipe → exiting, resuming FSM")
            bot.config.FSM.resume()
            return

        # 2) ignore early loading phase wipe
        print("[OnPartyWipe] Step 2: Checking map uptime...")
        map_uptime = GLOBAL_CACHE.Map.GetInstanceUptime()
        print(f"[OnPartyWipe] MapUptime = {map_uptime}")

        if map_uptime < 5000:
            print("[OnPartyWipe] Map uptime too low (<5000) → ignoring wipe → exiting, resuming FSM")
            bot.config.FSM.resume()
            return

        # 3) normal logic
        print("[OnPartyWipe] Step 3: Waiting for player revival...")
        while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            print("[OnPartyWipe]   Player still dead → waiting 1 second")
            yield from bot.Wait._coro_for_time(1000)

            if not Routines.Checks.Map.MapValid():
                print("[OnPartyWipe]   Map invalid during wait → exiting, resuming FSM")
                bot.config.FSM.resume()
                return

        # 4) player revived
        print("[OnPartyWipe] Step 4: Player revived → doing recovery transition")
        bot.config.FSM.pause()
        yield

        print("[OnPartyWipe] Jumping to recovery state: [H]Start Combat_3")
        bot.config.FSM.jump_to_state_by_name("[H]Start Combat_4")
        yield

        print("[OnPartyWipe] Resuming FSM after recovery")
        bot.config.FSM.resume()
        yield

        print("[OnPartyWipe] Recovery sequence finished")

    finally:
        print("[OnPartyWipe] Coroutine end")


    
def OnPartyWipe(bot: "Botting"):
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


bot.SetMainRoutine(bot_routine)


def configure():
    global bot
    bot.UI.draw_configure_window()
    
    
def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE)

if __name__ == "__main__":
    main()
