from Py4GWCoreLib import Botting, get_texture_for_model, ModelID, GLOBAL_CACHE, Routines

BOT_NAME = "Ritualist elite tome Farm"
MODEL_ID_TO_FARM = ModelID.Ritualist_Elite_Tome
MAP_TO_TRAVEL = 298 #Unwaking Waters

bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=MAP_TO_TRAVEL)
    bot.Party.SetHardMode(True)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Move.XY(-14278, -7954)
    bot.Wait.ForMapLoad(target_map_id=205) #Morostav trail
    bot.Move.XY(22553, 13212)
    bot.Move.XY(20697, 12435)
    bot.Move.XY(18903.56, 12656.72)
    bot.Multibox.PixelStack()
    bot.Wait.ForTime(4000)
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
