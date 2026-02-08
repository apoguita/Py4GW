from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Silver_Bullion_Coin Farmer"
MODEL_ID_TO_FARM = ModelID.Silver_Bullion_Coin
OUTPOST_TO_TRAVEL = 489 #kodlonu hamlet
COORD_TO_EXIT_MAP = (4682, -3499)
EXPLORABLE_TO_TRAVEL =488 #mehtani keys           
                
KILLING_PATH = [(-15263.63, 8165.77),
                (-14399.33, 4530.90),
                (-10802.99, 1653.46),
                (-6692.22, -1549.79),
                (649.73, -3253.13), #nick location
                (3150.80, -7789.69),
                (6314.76, -8436.42), #in the middle
                (7349.34, -9001.34),
                
                (4491.12, -4043.92),
                (7491.48, -4150.04),
                (8367.56, -8672.04),
                (8469.15, -10911.50), #peninsula
                (9045.15, -13585.27),
                (6043.60, -12071.96),
                (2907.86, -8912.01),
                (-2650.41, -11715.51), #island
                (-6825.53, -12234.29),
                (-9029.79, -11572.72),
                ]

NICK_OUTPOST = 489 #kodlonu hamlet
COORDS_TO_EXIT_OUTPOST =(4682, -3499)
EXPLORABLE_AREA = 488 #mehtani keys
NICK_COORDS = [(-15263.63, 8165.77),
                (-14399.33, 4530.90),
                (-10802.99, 1653.46),
                (-6692.22, -1549.79),
                (649.73, -3253.13), ]

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
