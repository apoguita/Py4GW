from Py4GWCoreLib import Botting, get_texture_for_model, ModelID, GLOBAL_CACHE, Routines
import PyImGui
#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Totem Axe Farm"
MODEL_ID_TO_FARM = ModelID.Totem_Axe
MAP_TO_TRAVEL = 139 #ventaris refuge


bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=MAP_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Move.XYAndExitMap(-15432, 115, 44) #ettins back
    bot.Move.XYAndExitMap(-23253, -11516, 45) #reed bog
    bot.Move.XY(-2194.33, -7495.35) #corner obstacle
    bot.Move.XY(-2927.30, -6533.62) #next corner
    bot.Move.XY(-6298.86, -7133.81)
    bot.Move.XYAndExitMap(-6489, -8230, 46) #the falls
    bot.Move.XY(2705.70, -16301.66)
    bot.Move.XY(-6753.60, -19203.25) #intersection

    bot.Move.XY(-14549.87, -13156.52) #balth temple
    bot.Move.XY(-18459.97, -8492.36) #corner
    bot.Move.XY(-12080.85, -4276.94) #loop

    bot.Move.XY(-13002.76, -5426.64)
    bot.Multibox.PixelStack()
    bot.Wait.ForTime(6000)
    #bot.Properties.Disable("pause_on_danger") #disable combat
    bot.Move.XY(-11127.64, -1070.10)
    #bot.Properties.Enable("pause_on_danger") #enable combat
    bot.Move.XY(-5447.10, -1369.62)
    
    #root behemoth locations
    behemoth_path = [(-4478.41, -3121.69), #st fork
            (-884.77, -7038.26),
            (-4478.41, -3121.69),
            (2945.17, -5985.73),
            (3751.78, -4006.87),
            
            (-2383.12, -3604.00), #sanity around
            
            (70.69, -1777.78), #2nd fork

            (-349.57, 2146.79), #pool
            (1647.16, 2389.09),
            (1359.23, 4266.31),
            
            (-3830.96, 3598.69), #fork 3 north
            (-5256.69, 4596.09),
            (-5391.62, 5708.04),
            (-10584.81, 7791.51),

            (2899.82, 6330.49), #back to pool
            (3293.26, 8932.29),
            (1663.14, 10357.10),
            (2047.11, 12849.01),

            #bridge
            (3149.54, 15254.85),
    ]
       
    bot.Move.FollowAutoPath(behemoth_path) 

    
    bot.Multibox.PixelStack()
    bot.Wait.ForTime(6000)
    
    path = [(3062.96, 15896.36),
            (2835.07, 17391.36),
    ]
    bot.Move.FollowPath(path)

    behemoth_path2 = [(-3537.32, 19198.30),
            (-5542.02, 18472.33),
            (-7835.15, 18384.68),
            (-9752.22, 19234.68), #near other bridge
            (-6088.62, 16294.07),
            (-5908.28, 14143.33),
            (-1520.87, 16605.64),
            (-269.50, 15357.26),
    ]

    bot.Move.FollowAutoPath(behemoth_path2)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()

    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_3")

    
def _on_party_wipe(bot: "Botting"):
    global party_wiped
    party_wiped = True
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.helpers.Wait._for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid - release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map - jump to recovery step
    print("Player revived, jumping to recovery step")
    bot.config.FSM.pause()
    bot.config.FSM.jump_to_state_by_name(f"[H]{BOT_NAME}_loop_3")
    bot.config.FSM.resume()
    #bot.States.JumpToStepName("[H]Start Combat_3")
    #bot.config.FSM.resume()
    
def OnPartyWipe(bot: "Botting"):
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

bot.SetMainRoutine(bot_routine)


def main():
    bot.Update()
    texture = get_texture_for_model(model_id=MODEL_ID_TO_FARM)
    bot.UI.draw_window(icon_path=texture)

if __name__ == "__main__":
    main()
