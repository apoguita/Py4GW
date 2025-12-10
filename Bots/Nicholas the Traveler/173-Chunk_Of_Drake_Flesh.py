from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Chunk Of Drake Flesh Farmer"
MODEL_ID_TO_FARM = ModelID.Chunk_Of_Drake_Flesh
OUTPOST_TO_TRAVEL = 489 #kodlonu hamlet
COORD_TO_EXIT_MAP = (4682, -3499)
EXPLORABLE_TO_TRAVEL =488 #mehtani keys           
                
KILLING_PATH = [(-15402.88, 8244.09),
                (-16753.15, 248.14),
                (-16286.26, -3263.86),
                (-14455.23, -7689.65),
                (-15412.24, -11981.53), #Irontooth Drakes 1
                (-10637.94, -14875.95),
                (-6832.23, -14397.14),
                (-5822.79, -11464.23),
                (-4075.63, -7421.08),   #Irontooth Drakes 2
                (829.90, -9111.14),     #Irontooth Drakes 3
                (1827.48, -12405.52),   #Trying to avoid crap
                (5629.24, -12486.72),   #Trying to avoid crap
                (5953.86, -17699.39),   #Irontooth Drakes 4
                (6649.20, -17017.07),   #Just to make sure all loot was collected
                ]

NICK_OUTPOST = 489 #kodlonu hamlet
COORDS_TO_EXIT_OUTPOST =(-4700.55, -2343.60)
EXPLORABLE_AREA = 486 #Issnur Isles
NICK_COORDS = [(20258.98, -370.21),
                (19638.66, -2569.45),
                (17642.26, -4354.77), ]

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
