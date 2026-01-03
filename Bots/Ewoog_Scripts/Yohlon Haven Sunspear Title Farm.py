from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, Agent, Range, Utils, ConsoleLog
import Py4GW
import os

bot = Botting("Sunspear Title Farm - Yohlon Haven",)


KILLING_PATH = [ (-18601.0, -12507.0), (-18103.0, -8169.0), (-16868.0, -7706.0), (-18433.0, -14250.0), (-16334.0, -17663.0), (-14982.0, -16881.0) ]



def Routine(bot: Botting) -> None:
    bot.Templates.Multibox_Aggressive()
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=381)  # Yohlon Haven

    bot.States.AddHeader("Travel to Yohlon Haven")
    bot.Map.Travel(target_map_id=381)  # Yohlon Haven
    bot.Party.SetHardMode(True)

    bot.States.AddHeader("Exit to Yohlon Haven to Arkjok Ward")
    bot.Move.XYAndExitMap(5580, 946, 380)  # Exit to Arkjok Ward
    bot.Wait.ForMapLoad(target_map_id=380)  # Arkjok Ward

    bot.States.AddHeader("Get Bounty from Sunspear Agent")  # 2
    bot.Move.XYAndInteractNPC(-17223, -12543)
    bot.Wait.ForTime(2000)
    bot.Multibox.SendDialogToTarget(0x85) #Get Bounty
    bot.Wait.ForTime(6000)

    bot.States.AddHeader("Start Combat") #3
    bot.Move.FollowAutoPath(KILLING_PATH, "Kill Route")
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Resign Party and Return to Yohlon Haven") #4
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=381)
    bot.UI.PrintMessageToConsole("Sunspear Title Farm", "Finished routine")
    bot.States.JumpToStepName("[H]Travel to Yohlon Haven_2")


bot.SetMainRoutine(Routine)


def main():
    bot.Update()
    bot.UI.draw_window()


def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
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


if __name__ == "__main__":
    main()
