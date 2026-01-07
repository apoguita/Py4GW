import os
import Py4GW
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Routines

BOT_NAME = "Chaar farm 4man"
bot = Botting(BOT_NAME)

KILLING_PATH = [
    (-12603, -2389),
    (-13137, -4024),
    (-14936, -5728),
    (-13889, -6633),
    (-12212, -8044),
    (-10209, -5856),
    (-9734, -4228),
    (-5599, -4529),
    (-3721, -6626),
    (-1223, -3256),
    (229, -4576),
    (793, -4253),
    (2871, -4145),
    (2533, -2395),
    (1667, -3082),
    (85, -3258),
]

# =========================
# WIPE HANDLING
# =========================
def _on_party_wipe(bot: "Botting"):
    """Gère le wipe de l'équipe"""
    while Routines.Checks.Player.IsDead():
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return
    # Quand le joueur est ressuscité, reprendre au combat
    bot.States.JumpToStepName("[H]Combat_3")
    bot.config.FSM.resume()

def OnPartyWipe(bot: "Botting"):
    """Callback appelé lors d'un wipe"""
    ConsoleLog("on_party_wipe", "Party wipe detected", log=True)
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

# =========================
# CUSTOM STATES
# =========================
def UseImpStone():
    """Utilise l'Imp Stone (item ID 30847)"""
    ConsoleLog("UseImpStone", "Recherche de l'Imp Stone...", log=True)
    
    item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(30847)
    
    if item_id:
        ConsoleLog("UseImpStone", f"Imp Stone trouvée (item_id: {item_id}), utilisation...", log=True)
        GLOBAL_CACHE.Inventory.UseItem(item_id)
        yield from Routines.Yield.wait(1000)
        ConsoleLog("UseImpStone", "Imp Stone utilisée!", log=True)
    else:
        ConsoleLog("UseImpStone", "Imp Stone non trouvée dans l'inventaire", log=True)
    
    yield

# =========================
# MAIN ROUTINE
# =========================
def Routine(bot: Botting) -> None:
    """Routine principale du farm chaar - Setup puis boucle automatique"""
    
    # ===== CONFIGURATION INITIALE (une seule fois) =====
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')
    
    bot.Templates.Multibox_Aggressive()
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=779)
    bot.Properties.Disable("auto_inventory_management")
    bot.Party.SetHardMode(False)
    
    # ===== SORTIE DE VILLE (point de boucle) =====
    bot.States.AddHeader("Exit Outpost")
    bot.Move.XYAndExitMap(-13542, 961, target_map_id=147)
    bot.Wait.ForMapLoad(147)
    bot.Wait.ForTime(3000)
    
    # ===== UTILISATION IMP STONE =====
    bot.States.AddCustomState(UseImpStone, "Use Imp Stone")
    
    # ===== COMBAT =====
    bot.States.AddHeader("Combat")
    bot.Move.FollowAutoPath(KILLING_PATH, "Chaar farm route")
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(8000)
    
    # ===== RETOUR EN VILLE =====
    bot.States.AddHeader("Resign and Return to Outpost")
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=779)
    
    # ===== BOUCLE AUTOMATIQUE =====
    bot.UI.PrintMessageToConsole(BOT_NAME, "Run completed - Restarting...")
    # Retourne à "Exit Outpost" - c'est le 2ème header donc _2
    bot.States.JumpToStepName("[H]Exit Outpost_2")

# =========================
# DÉMARRAGE DU BOT
# =========================
bot.SetMainRoutine(Routine)

def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()