from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

BOT_NAME = "Jade Mandible Farmer"
MODEL_ID_TO_FARM = ModelID.Jade_Mandible
MODULE_NAME = "Jade Mandible Farm (Nicholas the Traveler)"
MODULE_ICON = "Textures\\Module_Icons\\Nicholas the Traveler - Jade Mandible.png"
OUTPOST_TO_TRAVEL = 109 #The Amnoon Oasis
COORD_TO_EXIT_MAP = (6842.0,-6019.0)
EXPLORABLE_TO_TRAVEL = 113 #Prophet's Path   
                
KILLING_PATH = [
    (-15360.0,18879.0),
    (-17516.0,16326.0),
    (-17572.0,12809.0),
    (-18764.0,9972.0),
    (-18197.0,8157.0),
    (-17799.0,10596.0),
    (-16438.0,12072.0),
    (-14395.0,10767.0),
    (-12126.0,12582.0),
    (-10594.0,13944.0),
    (-8836.0,10143.0),
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
