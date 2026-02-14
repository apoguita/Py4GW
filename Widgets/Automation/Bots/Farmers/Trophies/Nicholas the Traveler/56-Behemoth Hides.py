from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

MODULE_ICON = "Textures\\Items\\Behemoth Hide.png"
BOT_NAME = "Behemoth Hide Farm"
MODULE_ICON = "Textures\\Module_Icons\\Behemoth Hide.png"
MODEL_ID_TO_FARM = ModelID.Behemoth_Hide
OUTPOST_TO_TRAVEL = 433 #Dzagonur Bastion
COORD_TO_EXIT_MAP = (4950.00, 1176.77)
EXPLORABLE_TO_TRAVEL = 404 #Wilderness of Bahdza
KILLING_PATH = [(-13729.33, 220.80),
                (-11330.43, -3653.23),
                (-17698.11, -7560.70),]

NICK_OUTPOST =  433 #Dzagonur Bastion
COORDS_TO_EXIT_OUTPOST = (4950.00, 1176.77)
EXPLORABLE_AREA = 404 #Wilderness of Bahdza
NICK_COORDS = [(-7861.24, 11115.86),] #Nicholas the Traveler Location

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
