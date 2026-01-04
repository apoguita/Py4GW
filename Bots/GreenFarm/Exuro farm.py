import os

import Py4GW
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Routines

BOT_NAME = "Exuro Farm"
bot = Botting(BOT_NAME)

KILLING_PATH = [
    (-8097, -13973),
    (-7129, -15616),
    (-6878, -16406),
    (-7656, -17393),
    (-6303, -18706),
    (-8616, -19107),
    
  ]

# =========================
# WIPE HANDLING
# =========================

def _on_party_wipe(bot: "Botting"):
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return
    # Quand le joueur est ressuscité, reprendre au combat
    bot.States.JumpToStepName("[H]Combat_3")
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "party wipe detected")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


# =========================
# MAIN ROUTINE
# =========================

def Routine(bot: Botting) -> None:
    """Routine principale du farm Exuro"""
    
    # ===== CONFIGURATION MULTIBOX =====
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')
    
    bot.Templates.Multibox_Aggressive()
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=495)
    bot.Properties.Disable("auto_inventory_management")
    bot.Party.SetHardMode(False)
    # ==================================

    bot.States.AddHeader("Exit Outpost")
    bot.Move.XYAndExitMap(-16382, -13370, target_map_id=472)
    bot.Wait.ForMapLoad(472)
    bot.Wait.ForTime(3000)

    bot.States.AddHeader("Combat")
    bot.Move.FollowAutoPath(KILLING_PATH, "Exuro Kill Route")
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(8000)

    bot.States.AddHeader("Resign and Return to Outpost")
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=495)
    bot.UI.PrintMessageToConsole(BOT_NAME, "Finished routine - Restarting...")
    bot.States.JumpToStepName("[H]Exit Outpost_2")


bot.SetMainRoutine(Routine)


def main():
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()