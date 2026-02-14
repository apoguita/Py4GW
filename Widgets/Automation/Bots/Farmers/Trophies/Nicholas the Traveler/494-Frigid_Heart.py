from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

MODULE_ICON = "Textures\\Items\\Frigid Heart.png"
BOT_NAME = "Frigid Heart Farm"
MODEL_ID_TO_FARM = ModelID.Frigid_Heart
MODULE_ICON = "Textures\\Module_Icons\\Frigid Heart.png"
OUTPOST_TO_TRAVEL = 22 #Ice Caves of Sorrow
COORD_TO_EXIT_MAP = (-23232, -5550)
EXPLORABLE_TO_TRAVEL = 26 #Talus chute    
                
KILLING_PATH = [
                (18439.63, -8245.48),
                (16104.44, -8460.50), #killspot1
                (16815.58, -10754.63),
                
                (16104.44, -8460.50), #back to killspot1
                (12903.62, -11476.76), #killspot2
                
                (16153.73, -5694.80), #fork
                #(14139.02, -1924.83), #left pack
                (16447.49, -2899.66), #center pack
                
                (15891.33, 1246.17), #upper area floodfill
                (19220.44, 1642.79),
                (15097.72, 1894.32),
                (15116.30, 4019.30),
                (16263.56, 6178.35),
                (17890.70, 6171.38),
                (17801.10, 7223.64),
                (21263.21, 10341.20),
                
                
                ]

NICK_OUTPOST = 117 #Thirsty River
COORDS_TO_EXIT_OUTPOST = (13104,13755)
EXPLORABLE_AREA = 108 #the scar
NICK_COORDS = [(-4510.0, -6737.0),] #Nicholas the Traveler Location

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
