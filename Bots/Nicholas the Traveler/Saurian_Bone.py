from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

# Farm des Saurian Bones à Riven Earth (sortie de Rata Sum)
BOT_NAME = "Saurian_Bone_Farmer"
MODEL_ID_TO_FARM = ModelID.Saurian_Bone
OUTPOST_TO_TRAVEL = 640  # Rata Sum
COORD_TO_EXIT_MAP = (20091, 16856)  # Sortie vers Riven Earth
EXPLORABLE_TO_TRAVEL = 501  # Riven Earth
                
KILLING_PATH = [
                (-20439.48, -6241.88),   # Premier spawn de Raptors
                (-20828.68, -10486.12),  # Deuxième spawn
                (-23149.12, -11032.64),  # Troisième spawn
                (-20148.12, -11946.11),  # Quatrième spawn
                (-14024.27, -10626.06),  # Cinquième spawn
                ]

NICK_OUTPOST = 640  # Rata Sum
COORDS_TO_EXIT_OUTPOST = (20091, 16856)
EXPLORABLE_AREA = 501  # Riven Earth
NICK_COORDS = [
                # À compléter si Nicholas est dans cette zone
               ]

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