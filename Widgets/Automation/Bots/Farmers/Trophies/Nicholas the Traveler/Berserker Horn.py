from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

BOT_NAME = "Berserker Horn Farm"
MODEL_ID_TO_FARM = ModelID.Berserker_Horn
MODULE_NAME = "Berserker Horn Farm (Nicholas the Traveler)"
MODULE_ICON = "Textures\\Module_Icons\\Nicholas the Traveler - Berserker Horn.png"
OUTPOST_TO_TRAVEL = 650 #Longeye's Ledge
COORD_TO_EXIT_MAP = (-26552,16351)
EXPLORABLE_TO_TRAVEL = 482 #Bjora Marches
                
KILLING_PATH = [
    (15249.0,-12218.0),
    (12973.0,-7506.0),
    (11032.0,-7360.0),
    (9674.0,-3673.0),
    (6084.0,499.0),
    (6427.0,4343.0),
    (5324.0,-178.0),
    (2297.0,-101.0),
    (3811.0,-3749.0),
    (2491.0,-5806.0),
    (2483.0,-9595.0),
    (4472.0,-10953.0),
    (4278.0,-13233.0),
    (5927.0,-13864.0),
    (8595.0,-12360.0),
    (10730.0,-15562.0),
]

NICK_OUTPOST = 117 #Thirsty River
COORDS_TO_EXIT_OUTPOST = (13104,13755)
EXPLORABLE_AREA = 108 #the scar
NICK_COORDS = [(-4510.0, -6737.0),] #Nicholas the Traveler Location

bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Aggressive()
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
    bot.Templates.Aggressive()
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
