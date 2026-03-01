from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

BOT_NAME = "Gold Doubloons Farm"
MODULE_NAME = "Gold Doubloon Farm (Nicholas the Traveler)"
MODULE_ICON = "Textures\\Module_Icons\\Nicholas the Traveler - Gold Doubloon.png"
MODEL_ID_TO_FARM = ModelID.Gold_Doubloon #Gold Doubloon
OUTPOST_TO_TRAVEL = 376 #Camp Hojanu
COORD_TO_EXIT_MAP = (-13986, 18223)
EXPLORABLE_TO_TRAVEL = 375 #Barbarous Shore   
                
KILLING_PATH = [
                (-9029, 16930),
                (-663, 16784),
                (690, 14386),
                (-407, 11862),
                (1019, 9586),
                (-3967, 7156),
                (-4960, 5225),
                (-4137, 3963),
                (-4576, 2235),
                (-2954, 956),
                (357, 236),
                (1317, 3116),
                (736, -1878),
                (-1347, -4621),
                (-3295, -3003),
                (-3981, -3634),
                (-3542, -4676),
                (-4694, -5225),
                (-4694, -6870),
                (-6778, -7254),
                (-8671, -9174),
                (-10042, -11424),
                (-9459, -13227),
                (-10230, -14628),
                (-12287, -15451),
                (-12726, -14820),
                (-12972, -12352),
                (-12369, -10925)
                
                ]

NICK_OUTPOST = 376  #Camp Hojanu
COORDS_TO_EXIT_OUTPOST = (-13986, 18223)
EXPLORABLE_AREA = 375 #Barbarous Shore
NICK_COORDS = [(-5203.44, -2907.11),] #Nicholas the Traveler Location

bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Move.FollowAutoPath(KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_3")
    bot.States.AddHeader(f"Path_to_Nicholas")
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=NICK_OUTPOST)
    bot.Move.XYAndExitMap(*COORDS_TO_EXIT_OUTPOST, EXPLORABLE_AREA)
    bot.Move.FollowAutoPath(NICK_COORDS, step_name="Nicholas_the_Traveler_Location")
    bot.Wait.UntilOnOutpost()

bot.SetMainRoutine(bot_routine)

def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
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

def nicks_window():
    if PyImGui.begin("Nicholas the Traveler", True):
        PyImGui.text(BOT_NAME)
        PyImGui.separator()
        PyImGui.text("Travel to Nicholas the Traveler location")
        
        if PyImGui.button("Start"):
            bot.StartAtStep("[H]Path_to_Nicholas_4")

def main():
    bot.Update()
    texture = get_texture_for_model(model_id=MODEL_ID_TO_FARM)
    bot.UI.draw_window(icon_path=texture)
    nicks_window()

if __name__ == "__main__":
    main()
