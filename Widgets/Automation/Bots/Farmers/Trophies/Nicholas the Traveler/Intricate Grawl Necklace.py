from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

BOT_NAME = "Intricate Grawl Necklace Farm"
MODEL_ID_TO_FARM = ModelID.Intricate_Grawl_Necklace
OUTPOST_TO_TRAVEL = 20 #Droknar's Forge
COORD_TO_EXIT_MAP = (5745.68, 1432.18)
EXPLORABLE_TO_TRAVEL = 95 #Witman's Folly
                
KILLING_PATH = [(-13997.61, 8259.06),
                (-9677.07, 7219.08),
                (-9187.69, 5834.49),
                (-9085.87, 4831.35),
                (-6626.67, 2975.06),
                (-4357.86, 4173.27),
                (-1893.25, 3501.05),
                (-1893.25, 3501.05),
                (277.87, 82.73),
                (3461.01, 1714.21),
                (6320.51, 2984.08),
                (5312.75, 5369.24),
                (6338.68, 8764.41),
                (1955.89, 8073.79),
                (-1797.45, 8747.20),
                (-4666.03, 7970.55),
                (-1100.41, 5410.17),]

NICK_OUTPOST = 20 #Droknar's Forge
COORDS_TO_EXIT_OUTPOST = (5745.68, 1432.18)
EXPLORABLE_AREA = 95 #Witman's Folly
NICK_COORDS = [(-14055.93, 8406.26),
               (-9336.01, 7261.95),
               (-8010.28, 3568.91),
               (-4221.07, 3896.70),
               (-2045.63, 1898.84),
               (-5500.29, -1778.08),
               (-3594.06, -6713.41),] #Nicholas the Traveler Location

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
