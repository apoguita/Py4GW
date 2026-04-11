from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

BOT_NAME = "Maguuma Mane Farmer"
MODEL_ID_TO_FARM = ModelID.Maguuma_Mane
MODULE_NAME = "Maguuma Mane Farm (Nicholas the Traveler)"
MODULE_ICON = "Textures\\Module_Icons\\Nicholas the Traveler - Maguuma Mane.png"
OUTPOST_TO_TRAVEL = 139 #Ventaris Refuge
COORD_TO_EXIT_MAP = (-15548.0,315.0)
EXPLORABLE_TO_TRAVEL = 44 #Ettin's Back   
                
KILLING_PATH = [
    (-23141.0,2336.0),
    (-26780.0,-90.0),
    (-20716.0,2033.0),
    (-17502.0,-636.0),
    (-14045.0,-5790.0),
    (-11923.0,-13431.0),
    (-14470.0,-13795.0),
    (-14530.0,-10277.0),
    (-19321.0,-8034.0),
    (-20898.0,-11066.0),
]
NICK_OUTPOST = 639 #Umbral grotto
COORDS_TO_EXIT_OUTPOST = (-22646.0, 6289.0)
EXPLORABLE_AREA = 566 #verdant cascades
NICK_COORDS = [(-5367.88, -13457.16),]

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
