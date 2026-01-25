from Py4GWCoreLib import Botting, get_texture_for_model, ModelID, Routines, ConsoleLog, Map, Agent, Player
from Py4GW_widget_manager import get_widget_handler
import Py4GW

BOT_NAME = "The Crystalline Farm"
MODEL_ID_TO_FARM = ModelID.Feathered_Crest
OUTPOST_TO_TRAVEL = 206  # Deldrimor war camp
COORD_TO_EXIT_MAP = (-2854, -3613)  # Deldrimor war camp exit to Grenth Footprint
EXPLORABLE_TO_TRAVEL = 191  # Grenth Footprint

opened_chests: set[int] = set()
bot = Botting(BOT_NAME)


# ==================== FONCTIONS ====================

def OpenChest1_Test():
    chest_id = Routines.Agents.GetNearestGadget(200)
    yield from Routines.Yield.wait(1000)
    yield from Routines.Yield.Player.ChangeTarget(chest_id)
    yield from Routines.Yield.Player.InteractAgent(chest_id)
    yield

def OpenChest2_Test():
    chest_id = Routines.Agents.GetNearestGadget(200)
    yield from Routines.Yield.wait(1000)
    yield from Routines.Yield.Player.ChangeTarget(chest_id)
    yield from Routines.Yield.Player.InteractAgent(chest_id)
    yield

def OpenChest3_Test():
    chest_id = Routines.Agents.GetNearestGadget(200)
    yield from Routines.Yield.wait(1000)
    yield from Routines.Yield.Player.ChangeTarget(chest_id)
    yield from Routines.Yield.Player.InteractAgent(chest_id)
    yield

def CheckIfStuck(last_position, current_position, threshold=50):
    """Verifie si le joueur est bloque en comparant les positions"""
    if not last_position:
        return False
    dx = current_position[0] - last_position[0]
    dy = current_position[1] - last_position[1]
    distance_moved = (dx**2 + dy**2)**0.5
    return distance_moved < threshold


def UnstuckPlayer():
    """Tente de debloquer le joueur"""
    ConsoleLog(BOT_NAME, f"[UNSTUCK] Joueur bloque detecte, tentative de deblocage...", Py4GW.Console.MessageType.Warning)
    
    current_pos = Player.GetXY()
    offsets = [(9000, 0), (-9000, 0), (0, 9000), (0, -9000), (9500, 9500), (-9500, -9500)]
    
    for offset_x, offset_y in offsets:
        new_x = current_pos[0] + offset_x
        new_y = current_pos[1] + offset_y
        ConsoleLog(BOT_NAME, f"[UNSTUCK] Tentative deplacement vers ({new_x:.0f}, {new_y:.0f})", Py4GW.Console.MessageType.Info)
        yield from Routines.Yield.Movement.FollowPath(path_points=[(new_x, new_y)])
        yield from Routines.Yield.wait(500)
        
        check_pos = Player.GetXY()
        if not CheckIfStuck(current_pos, check_pos, threshold=100):
            ConsoleLog(BOT_NAME, f"[UNSTUCK] Deblocage reussi!", Py4GW.Console.MessageType.Info)
            break
    
    yield


def ResetOpenedChests():
    """Reinitialise la liste des coffres ouverts pour le prochain run"""
    global opened_chests
    opened_chests = set()
    yield


def _on_party_wipe(bot: "Botting"):
    ConsoleLog(BOT_NAME, f"[WIPE] Party wipe detecte!", Py4GW.Console.MessageType.Warning)
    
    while Agent.IsDead(Player.GetAgentID()):
        yield from Routines.Yield.wait(1000)
        
        if not Routines.Checks.Map.MapValid():
            ConsoleLog(BOT_NAME, f"[WIPE] Teleporte en ville apres mort du PNJ, relance du run...", Py4GW.Console.MessageType.Warning)
            
            yield from Routines.Yield.wait(3000)
            
            global opened_chests
            opened_chests = set()
            
            bot.config.FSM.resume()
            bot.config.FSM.jump_to_state_by_name(f"[H]{BOT_NAME}_loop_3")
            
            ConsoleLog(BOT_NAME, f"[WIPE] Redemarrage du run depuis la boucle, team conservee", Py4GW.Console.MessageType.Info)
            return

    ConsoleLog(BOT_NAME, f"[WIPE] Joueur ressuscite sur place, continuation...", Py4GW.Console.MessageType.Info)
    bot.config.FSM.pause()
    bot.config.FSM.jump_to_state_by_name(f"[H]{BOT_NAME}_loop_3")
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


# ==================== ROUTINE PRINCIPALE ====================

def bot_routine(bot: Botting) -> None:
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Party.SetHardMode(False)
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Wait.ForTime(4000)
    
    # Premier chemin de farming - Grenth Footprint
    bot.Move.XY(-2844.9, -3954.6)
    bot.Move.XY(-1120.8, -338.3)
    bot.Move.XY(-4416.6, -2605.6)
    bot.Move.XY(-5546.1, -6445.4)
    
    bot.Move.XYAndInteractNPC(-5893.00, -7661.00)
    bot.Multibox.SendDialogToTarget(0x1)  # Get quest
    
    # Deuxieme chemin de farming - Nouveau chemin optimise
    bot.Move.XY(-5345.56, -7053.34)
    bot.Move.XY(-5953.41, -5875.99)
    bot.Move.XY(-7233.55, -5920.48)
    bot.Move.XY(-8573.38, -5871.67)
    bot.Move.XY(-10648.20, -4579.88)
    bot.Move.XY(-9987.77, -3375.22)
    bot.Move.XY(-8032.36, -2356.49)
    bot.Move.XY(-6379.28, -887.81)
    bot.Move.XY(-6012.41, 380.61)
    bot.Move.XY(-8336.88, 3129.62)
    bot.Move.XY(-6269.52, 4507.12)
    bot.Move.XY(-8713.16, 6788.40)
    
    bot.Wait.ForTime(3000)  # Regroupement avant changement de map
    
    bot.Move.XYAndExitMap(-10168, 8616, 190)  # Sorrow's Furnace
    
    bot.Wait.ForTime(5000)  # Timer apres le changement de map
    
    bot.Move.XYAndInteractNPC(-16345.22, 16792.16)
    bot.Multibox.SendDialogToTarget(0x80ED01)  # Get quest
    
    # Troisieme chemin de farming - Sorrow's Furnace
    bot.Move.XY(-17021.99, 15775.23)
    # bot.Wait.ForTime(35000)   CANT SKIP CINEMATIC SINCE     
    bot.Move.XY(-14593.18, 13944.71)
    bot.Move.XY(-7829.34, 17260.79)
    bot.Move.XY(-4117.31, 14745.04)
    bot.Move.XY(-889.62, 15426.97)
    bot.Move.XY(328.98, 16636.02)
    bot.Move.XY(-730.90, 18166.77)  # XY24
    bot.Party.FlagAllHeroes(-235, 17959)
    bot.Wait.ForTime(1000)
    bot.Party.FlagAllHeroes(-19, 16849)
    bot.Wait.ForTime(2000)
    bot.Party.FlagAllHeroes(3273, 13441)
    bot.Wait.ForTime(15000)
    
    # PREMIER COFFRE
    bot.Move.XY(-821,18310,500)
    bot.Wait.ForTime(1000)
    bot.States.AddCustomState(OpenChest1_Test, "TEST OUVERTURE COFFRE 1")
    
    bot.Move.XY(3107.73, 13533.00)
    bot.Party.UnflagAllHeroes()
    bot.Move.XY(6993.74, 12703.58)
    bot.Move.XY(12059.48, 16139.21)
    bot.Move.XY(14444.08, 16538.68)
    bot.Move.XY(16801.18, 15074.61)
    bot.Move.XY(18324.47, 17511.60)
    
    # DEUXIEME COFFRE
    bot.Move.XY(16740.12, 16897.12)
    bot.Party.FlagAllHeroes(18814, 11860)
    bot.Wait.ForTime(20000)
    bot.Move.XY(16894, 16975,500)  # Point plus proche du coffre
    bot.Wait.ForTime(1000)
    bot.States.AddCustomState(OpenChest2_Test, "TEST OUVERTURE COFFRE 2")
    
    bot.Move.XY(18162.17, 13624.02)
    bot.Party.UnflagAllHeroes()
    bot.Move.XY(17290.40, 10190.77)  # Pont start
    bot.Move.XY(13950.53, 7026.81)
    bot.Wait.ForTime(9000)  # Regroupement
    bot.Move.XY(13235.83, 6349.28)  # Pont fin
    
    bot.Move.XY(10027.94, 2944.84)  # XY37
    bot.Wait.ForTime(9000)  # Regroupement
    
    bot.Move.XY(4266.01, 5921.17)  # XY38
    bot.Wait.ForTime(9000)  # Regroupement
    
    bot.Move.XY(2028.40, 5763.65)  # XY39
    bot.Wait.ForTime(9000)  # Regroupement
    
    bot.Move.XY(-987.32, 8226.98)  # XY40
    
    bot.Move.XY(-3537.40, 6402.52)  # XY41
    bot.Move.XY(-4407.11, 8117.99)  # XY42
    bot.Move.XY(-2982.06, 9292.26)  # XY43
    
    # TROISIEME COFFRE
    bot.Move.XY(-3795.37, 9128.38)
    bot.Party.FlagAllHeroes(-5140, 3127)
    bot.Wait.ForTime(15000)
    bot.Move.XY(-3489, 8996,500)  # Point plus proche du coffre
    bot.Wait.ForTime(1000)
    bot.States.AddCustomState(OpenChest3_Test, "TEST OUVERTURE COFFRE 3")
    
    bot.Move.XYAndInteractNPC(-4763.24, 9548.95)
    bot.Multibox.SendDialogToTarget(0x80ED07)  # Turn in quest
    
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    
    bot.States.AddCustomState(lambda: ResetOpenedChests(), "Reinitialiser Coffres Ouverts")
    
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_3")


# ==================== MAIN ====================

bot.SetMainRoutine(bot_routine)

def main():
    bot.Update()
    texture = get_texture_for_model(model_id=MODEL_ID_TO_FARM)
    bot.UI.draw_window(icon_path=texture)

if __name__ == "__main__":
    main()