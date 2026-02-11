from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

BOT_NAME = "Shriveled Eye Farm"
MODEL_ID_TO_FARM = ModelID.Shriveled_Eye
OUTPOST_TO_TRAVEL = 38 #Augury Rock
COORD_TO_EXIT_MAP = (-19992.90, -377.76)
EXPLORABLE_TO_TRAVEL = 113 #Prophet's Path
                
KILLING_PATH = [(17471.15, 2235.48),
                (13471.71, -457.15),
                (11641.73, 4171.57),
                (8791.09, 7502.06),
                (9326.00, 10791.87),
                (10223.25, 12516.27),
                (14898.85, 11212.67),
                (15974.86, 9039.27),
                (14898.85, 11212.67),
                (18289.23, 14466.59),
                (15745.63, 13927.53),
                (13245.50, 13373.15),
                (12153.57, 15722.99),
                (12006.16, 17258.61),
                (10369.99, 17260.07),
                (10357.87, 19431.29),]

FARM_KILLING_PATH = [(10357.87, 19431.29),
                     (10369.99, 17260.07),
                     (12006.16, 17258.61),
                     (12153.57, 15722.99),
                     (13245.50, 13373.15),
                     (15745.63, 13927.53),
                     (18289.23, 14466.59),
                     (14898.85, 11212.67),
                     (15974.86, 9039.27),]

SALT_FLATS = 114 #Salt Flats
COORDS_TO_EXIT_TO_SALT_FLATS = (7798.55, 19815.52)
COORDS_TO_REENTER_PROPHETS_PATH = (-4344.50, -19996.98)

NICK_OUTPOST = 38 #Augury Rock
COORDS_TO_EXIT_OUTPOST = (-15167.73, 2175.31)
EXPLORABLE_AREA = 115 #Skyward Reach
NICK_COORDS = [(-12302.75, 2452.19),
               (-11552.17, -1845.30),
               (-12192.00, -4002.30),
               (-12787.93, -5538.32),
               (-9832.29, -8628.04),
               (-5139.93, -11872.20),
               (-2102.44, -12570.22),
               (-1182.99, -13793.38),
               (3441.26, -15414.18),
               (8560.06, -14136.05),
               (9892.16, -13048.30),
               (12632.67, -12645.65),
               (14380.81, -14158.82),
               (14262.85, -16198.79),
               (12814.56, -15511.31),] #Nicholas the Traveler Location

bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Move.FollowAutoPath(KILLING_PATH)
    bot.States.AddHeader(f"{BOT_NAME}_farm_loop")
    bot.Move.FollowAutoPath(FARM_KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndExitMap(*COORDS_TO_EXIT_TO_SALT_FLATS, target_map_id=SALT_FLATS)
    bot.Wait.ForTime(500)
    bot.Move.XYAndExitMap(*COORDS_TO_REENTER_PROPHETS_PATH, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_farm_loop_3")
    bot.States.AddHeader(f"Path_to_Nicholas")
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=NICK_OUTPOST)
    bot.Move.XYAndExitMap(*COORDS_TO_EXIT_OUTPOST, EXPLORABLE_AREA)
    bot.Move.FollowAutoPath(NICK_COORDS, step_name="Nicholas_the_Traveler_Location")
    bot.Wait.UntilOnOutpost()

bot.SetMainRoutine(bot_routine)

def main_window_extra_ui():
    PyImGui.text("Nicholas the Traveler")
    PyImGui.separator()
    PyImGui.text("Travel to Nicholas the Traveler location")
    if PyImGui.button("Start Nick Route"):
        bot.StartAtStep("[H]Path_to_Nicholas_4")

def main():
    bot.Update()
    texture = get_texture_for_model(model_id=MODEL_ID_TO_FARM)
    bot.UI.draw_window(icon_path=texture, additional_ui=main_window_extra_ui)

if __name__ == "__main__":
    main()
