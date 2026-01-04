from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

# Farm des Saurian Bones à Riven Earth (sortie de Rata Sum)
BOT_NAME = "Saurian_Bone_Farmer"
MODEL_ID_TO_FARM = ModelID.Saurian_Bone
OUTPOST_TO_TRAVEL = 640  # Rata Sum
COORD_TO_EXIT_MAP = (20091, 16856)  # Sortie vers Riven Earth
EXPLORABLE_TO_TRAVEL = 501  # Riven Earth
                
KILLING_PATH = [(-22788.35, -7395.83),
                (-21152.77, -9351.26),
                (-19285.32, -10412.26),
                (-19489.34, -12276.55),
                (-20887.78, -11281.10),
                (-22261.11, -12643.81),
                (-23085.04, -11902.00),
                (-23293.07, -10863.60),
                ]

NICK_OUTPOST = 640  # Rata Sum
COORDS_TO_EXIT_OUTPOST = (20091, 16856)
EXPLORABLE_AREA = 501  # Riven Earth
NICK_COORDS = [(-22788.35, -7395.83),
               (-18345.24, -8801.11),
               (-15282.19, -8637.26),
               (-13504.29, -12107.34),
               (-7994.64, -13041.42),
               (-338.48, -8849.78),
               (2793.29, -11594.35),
               (9888.96, -10685.56),
               (16346.44, -8881.42),     #Bridge
               (20036.23, -4774.40),
               (20934.02, -6074.08),
               ]

bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Move.XYAndInteractNPC(-24286.94, -5667.19)
    bot.Multibox.SendDialogToTarget(0x84) #Get Bounty
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