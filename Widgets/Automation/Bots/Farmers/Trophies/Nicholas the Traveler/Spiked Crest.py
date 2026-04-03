from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

BOT_NAME = "Spiked Crest Farm"
MODULE_NAME = "Spiked Crest Farm (Nicholas the Traveler)"
MODULE_ICON = "Textures\\Module_Icons\\Nicholas the Traveler - Spiked Crest.png"
MODEL_ID_TO_FARM = ModelID.Spiked_Crest
OUTPOST_TO_TRAVEL = 19 #Sanctum Cay
EXPLORABLE_TO_TRAVEL = 19 #Sanctum Cay Mission    
                
KILLING_PATH = [
                (-11031.4,-5933.8),
(-11583.0,-7435.2),
(-11588.6,-8938.7),
(-10088.1,-10224.4),
(-8587.3,-10888.7),
(-7083.5,-12368.7),
(-5583.1,-13000.2),
(-4081.2,-13463.5),
(-2577.5,-13759.6),
(-1076.9,-14081.8),
(427.3,-14760.8),

                ]

NICK_OUTPOST = 117 #Thirsty River
COORDS_TO_EXIT_OUTPOST = (13104,13755)
EXPLORABLE_AREA = 108 #the scar
NICK_COORDS = [(-4510.0, -6737.0),] #Nicholas the Traveler Location

bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Map.EnterChallenge(12000, target_map_id=EXPLORABLE_TO_TRAVEL, target_map_name="")
    bot.Move.FollowPath(KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_3")
    bot.States.AddHeader(f"Path_to_Nicholas")
    bot.Templates.Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=NICK_OUTPOST)
    bot.Move.XYAndExitMap(*COORDS_TO_EXIT_OUTPOST, EXPLORABLE_AREA)
    bot.Move.FollowAutoPath(NICK_COORDS, step_name="Nicholas_the_Traveler_Location")
    bot.Wait.UntilOnOutpost()

bot.SetMainRoutine(bot_routine)

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
