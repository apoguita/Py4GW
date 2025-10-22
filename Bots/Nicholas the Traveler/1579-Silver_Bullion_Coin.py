from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Silver_Bullion_Coin Farmer"
MODEL_ID_TO_FARM = ModelID.Silver_Bullion_Coin
OUTPOST_TO_TRAVEL = 376 # Camp Hojanur 
COORD_TO_EXIT_MAP = (-13433, 17852) #Barbarous  shore
EXPLORABLE_TO_TRAVEL =375 # Barbarous Shore             
                
KILLING_PATH = [(-12032.38, 16223.01),
                (-1282.05, 16592.38), #right corner
                (206.77, 8098.54), #fork
                (-3533.88, 10546.35), #around the rock to the left
                (-4739.70, 6106.03), #res shrine
                (196.85, 7709.82), #to fork road
                (2310.37, 4956.57), #mesa
                (3618.70, 4255.12), #mesa floodfill
                (1313.10, 3630.13), #ff2
                (3181.63, 1412.95), #ff3
                (502.33, -215.21), #ff exit
                (-3369.37, 537.74), #patrol
                (-4430.59, 2131.17), #snake patrol 
                (-7883.52, -1381.38), #fork betreen rocks
                (-12002.93, -6489.35), #unavoidable rest
                (-12751.13, -8924.20), #unavoidable 2
                (-13193.59, -11212.24), #res shrine
                (-12966.85, -13007.42),
                (-17546.62, -15103.07), #corsair floodfill
                (-17408.27, -18450.41),
                (-13281.60, -18272.45),
                (-13008.40, -16677.63), #bridge
                (-15311.79, -15939.08),
                (-12668.85, -15105.11),
                (-8789.26, -13026.13), #next area
                (-6526.41, -10307.15),
                (-7327.67, -7865.69),
                (-9237.68, -8668.41),
                (-10193.92, -11620.16),
                ]

NICK_OUTPOST = 155 #Camp Rankor
COORDS_TO_EXIT_OUTPOST =(5435, -40809)
EXPLORABLE_AREA = 91 #snake dance
NICK_COORDS = (-7176.39, -2448.33)



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
    bot.Move.XY(*NICK_COORDS)
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
