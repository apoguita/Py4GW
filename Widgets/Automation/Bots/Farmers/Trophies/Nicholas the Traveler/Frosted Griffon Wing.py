from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Frosted_Griffon_Wing_Bot"
MODULE_ICON = "Textures\\Module_Icons\\Frosted Griffon Wing.png"
MODEL_ID_TO_FARM = ModelID.Frosted_Griffon_Wing
OUTPOST_TO_TRAVEL = 155 #Camp Rankor 
COORD_TO_EXIT_MAP = (5435, -40809) #Camp Rankor to Snake Dance
EXPLORABLE_TO_TRAVEL = 91 #snake dance             
                
KILLING_PATH = [ (3162, -36810), #1st pack (danger)
                (-2569.78, -38270.38), #spawn hill
                (-6120.68, -36030.23), #up the hill
                (-724.64, -39770.79), #down the hill
                (6.97, -41847.79),
                (1168.24, -43209.32),
                (-1143.77, -44296.21),
                (-5388.29, -43029.41),
                (-3740.81, -40425.59)
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
