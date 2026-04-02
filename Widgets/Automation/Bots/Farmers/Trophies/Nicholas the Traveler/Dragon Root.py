from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

BOT_NAME = "Dragon Root Farm"
MODEL_ID_TO_FARM = ModelID.Dragon_Root
MODULE_NAME = "Dragon Root Farm (Nicholas the Traveler)"
MODULE_ICON = "Textures\\Module_Icons\\Nicholas the Traveler - Dragon Root.png"
OUTPOST_TO_TRAVEL = 349 #Saint Anjeka's Shrine
COORD_TO_EXIT_MAP = (-11282, -23031)
EXPLORABLE_TO_TRAVEL = 195 #Drazach Thicket   
                
KILLING_PATH = [
                (-10531.0,19116.0),
(-9028.8,18773.3),
(-7525.7,18280.7),
(-6079.5,16778.4),
(-5571.7,15887.2),               
                
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
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Move.FollowAutoPath(KILLING_PATH)
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
