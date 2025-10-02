from Py4GWCoreLib import Botting, get_texture_for_model, ModelID

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Jade_Bracelet_Nicks_Location"
MODEL_ID_TO_FARM = ModelID.Jade_Bracelet
OUTPOST_TO_TRAVEL = 284 #zin ku corridor
COORD_TO_EXIT_MAP = (2720.85, -15937.43) #zin ku corridor exit to tahnnakai temple
EXPLORABLE_TO_TRAVEL = 269 #tahnnakai temple
KILLING_PATH = [(2628.76, -12700.21),
                (3600.44, -12322.98),
                (1742.43, -12650.80),
                (-510.65, -8331.95),
                (467.50, -5417.71),
                (3252.85, -2439.24),
                (3043.17, 1892.77),
                (5509.59, 6334.03),
                (2925.67, 8540.64),
                (2628.22, 10164.93),
                (2242.05, 11424.77),
                (1007.35, 11444.69),
                (943.35, 12661.05),
                (-401.27, 12647.83),
                (-3083.85, 18615.01),
                (-5766.43, 18860.22),
                (-5716.97, 21188.86),
                (-3338.20, 21167.88),
                (-4991.98, 19185.82),
                (-4895.71, 20586.71),
                (-4294.17, 19781.30),
                (-4274.91, 17724.34),
                (-4431.24, 16951.75),
                (-6160.20, 15806.81),
                (-3100.32, 14707.95),
                (-4081.45, 11866.37),
                (-3852.29, 8394.97),
                (-1442.23, 8284.82),
                (-1159.14, 6807.80),
                (-1173.96, 3414.98),
                (-473.15, 2173.49),
                (-592.83, 1142.38),
                (-1844.01, -731.19),
                ]

bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Move.FollowAutoPath(KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_3")

bot.SetMainRoutine(bot_routine)

def main():
    bot.Update()
    texture = get_texture_for_model(model_id=MODEL_ID_TO_FARM)
    bot.UI.draw_window(icon_path=texture)

if __name__ == "__main__":
    main()
