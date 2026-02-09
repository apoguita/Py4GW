from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Truffle Farmer"
MODEL_ID_TO_FARM = ModelID.Truffle
OUTPOST_TO_TRAVEL = 130 #Vasburg Armory
COORD_TO_EXIT_MAP = (24082, 7150)
EXPLORABLE_TO_TRAVEL =205 #Morostav Trail        
                
KILLING_PATH = [(-12902.83, 3627.39),
                (-17624.64, 9130.87),
                ]

NICK_OUTPOST = 130 #Vasburg Armory
COORDS_TO_EXIT_OUTPOST = (24082, 7150)
EXPLORABLE_AREA = 205 #Morostav Trail
NICK_COORDS = [(-10685.96, 3025.99),
               (-984.28, -2503.44), ]

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
