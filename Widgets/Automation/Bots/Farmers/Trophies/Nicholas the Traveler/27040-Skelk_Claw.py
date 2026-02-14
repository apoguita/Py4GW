from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

MODULE_ICON = "Textures\\Items\\Skelk Claw.png"
BOT_NAME = "Skelk Farmer"
MODEL_ID_TO_FARM = ModelID.Skelk_Claw
MODULE_ICON = "Textures\\Module_Icons\\Skelk Claw.png"
OUTPOST_TO_TRAVEL = 639 #Umbral grotto
COORD_TO_EXIT_MAP = (-22646, 6289)
EXPLORABLE_TO_TRAVEL = 566 #verdant cascades        
                
KILLING_PATH = [#(-16090.61, 4796.22),
                #(-17213.55, 1136.15),
                (-8537.49, 2108.35),
                (-10074.82, -2150.32),
                #floodfill
                (-7614.65, 1302.55),
                (-6693.68, -701.32),
                (-5876.84, 1222.03),
                
                (-3234.19, -3135.18),
                (-2129.97, -3269.13),
                (-2528.14, -4620.56),
                
                (-4224.32, -8524.97), #ambush
                
                #floodfill
                (1488.64, -10291.60),
                (3207.30, -5411.58), #up patrol
                
                (3197.91, -9864.20),
                (3726.21, -11908.08),
                (5272.44, -10511.60),
                (6896.16, -11388.40),
                
                (9923.25, -8108.26),
                (14649.71, -11481.27),
                (15128.50, -9517.24),
                (17701.87, -6310.94),
                (13943.78, -7925.01),
                (13187.99, -6217.26),
                (10600.87, -6880.84),
                
                (9260.61, -2200.76),
                (6357.21, -1597.28),
                (8436.38, 854.56),
                (5881.31, 4605.50),
                
                ]

NICK_OUTPOST = 639 #Umbral grotto
COORDS_TO_EXIT_OUTPOST = (-22646, 6289)
EXPLORABLE_AREA = 566 #verdant cascades
NICK_COORDS = [(-5367.88, -13457.16),]

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
