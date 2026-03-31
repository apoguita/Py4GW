from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

BOT_NAME = "Behemoth Jaw Farm"
MODEL_ID_TO_FARM = ModelID.Behemoth_Jaw
MODULE_NAME = "Behemoth Jaw Farm (Nicholas the Traveler)"
MODULE_ICON = "Textures\\Module_Icons\\Nicholas the Traveler - Behemoth Jaw.png"
OUTPOST_TO_TRAVEL = 141 #Maguuma Stade
COORD_TO_EXIT_MAP = (407,-9748)
COORD_TO_CHANGE_MAP = (5253.0,-7793.0)
COORD_TO_EXIT_MAP2 = (-19598,5306)
EXPLORABLE_TO_TRAVEL2 = 47 #Dry Top
EXPLORABLE_TO_TRAVEL = 48 # Tangle Root

TRAVEL_PATH = [
    (513.0,-6786.0),
    (-4689.0,-7903.0),
    (-16385.0,-7282.0),
    (-25452.0,-6436.0),
    (-26007.0,-6096.0),
    (-23821.0,-3057.0),
    (-21736.0,2485.0),
    (-19004.0,3228.0),
    
]

KILLING_PATH = [
    (4730.0,-6242.0),
    (6268.0,-5291.0),
    (6855.0,-4425.0),
    (5738.0,-2064.0),
    (6352.0,-3138.0),
    (7023.0,-5040.0),
    (4982.0,-6606.0),
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
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Move.FollowAutoPath(TRAVEL_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP2, target_map_id=EXPLORABLE_TO_TRAVEL2)
    bot.Move.FollowAutoPath(KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndExitMap(*COORD_TO_CHANGE_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
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
