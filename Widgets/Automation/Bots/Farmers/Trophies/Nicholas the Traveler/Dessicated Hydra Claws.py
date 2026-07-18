from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

BOT_NAME = "Dessicated Hydra Claws Farm"
MODULE_NAME = "Dessicated Hydra Claws Farm (Nicholas the Traveler)"
MODULE_ICON = "Textures\\Module_Icons\\Nicholas the Traveler - Dessicated Hydra Claw.png"
MODEL_ID_TO_FARM = ModelID.Dessicated_Hydra_Claw
OUTPOST_TO_TRAVEL = 38 #Augury Rock
COORD_TO_EXIT_MAP = (-15169, 2357)
EXPLORABLE_TO_TRAVEL = 115 #skyward reach      
                
KILLING_PATH = [
                (-11759.14, 7042.38), #floodfill
                (-10542.00, 8967.21),
                (-10441.84, 12723.53),
                (-8204.89, 14474.05),
                
                (-10441.84, 12723.53),
                #(-9178.10, 12680.75),
                
                (-3887.92, 9187.13),
                (-1114.75, 10886.89),
                (-1785.17, 14405.61),
                (629.19, 12602.50),
                (66.25, 10202.94),
                (2793.54, 9735.18),
                (5340.15, 9114.43),
                (9363.65, 7711.48),
                #end
                (9880.96, 5695.88),
                (12656.96, 6140.85),
                (13569.95, 8803.42),
                (7465.07, 11988.38),
                #way back
                (5077.34, 7215.82),
                (2543.52, 8106.04),
                (-1309.46, 8040.95),
                (-5930.14, 7329.36),
                
                (-5345.60, 2123.46),
                (-7015.40, 2356.46),
                (-8046.64, 5480.42),
                (-11982.74, 3697.23),
                (-10345.89, 1990.04),
                
                #lower part
                (-10921.43, -2393.92),
                (-8792.48, -3682.47),
                (-6891.95, -2609.71),
                (-4747.02, -3013.14),
                (-4166.56, -4857.63),
                (-2514.72, -5256.47),
                (-4712.76, -6577.13),
                
                (-11427.89, -4324.15),
                (-15360.52, -4869.66),
                (-10377.60, -6568.56),
                (-8776.30, -8505.00),
                
                #floodfill
                (-5500.49, -10728.68),
                (-2829.93, -8485.09),
                (-1851.69, -6793.46),
                (-290.64, -7519.74),
                (-3128.07, -11428.44),
                
                (-1063.04, -11655.35),
                (-3068.92, -16529.97),
                (2040.55, -17564.76),
                (4609.22, -17936.43),
                (2638.95, -15735.74),
                
                (-1905.84, -15610.54),
                (1499.38, -13694.37),
                (90.23, -11348.57),
                (2088.19, -9024.79),
                (2338.77, -7571.33),
                (4635.63, -7373.09),
                (4155.84, -11965.16),

                #last area
                (10278.25, -8022.89),
                (9418.56, -6403.22),
                (10942.36, -5251.81),
                
                (13955.04, -3888.58),
                
                (11434.88, -8399.74),
                (10259.06, -12258.38),
                (7744.35, -13300.28),
                (15698.09, -15437.02),
                (12403.57, -15616.12),

                ]

NICK_OUTPOST = 117 #Thirsty River
COORDS_TO_EXIT_OUTPOST = (13104,13755)
EXPLORABLE_AREA = 108 #the scar
NICK_COORDS = [(-4510.0, -6737.0),] #Nicholas the Traveler Location

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
