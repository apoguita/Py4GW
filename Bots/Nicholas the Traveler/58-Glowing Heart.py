from Py4GWCoreLib import Botting, get_texture_for_model, ModelID

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Glowing Heart Farm"
MODEL_ID_TO_FARM = ModelID.Glowing_Heart
OUTPOST_TO_TRAVEL = 15 #D'Alessio Seaboard
COORD_TO_EXIT_MAP = (16100.95, 17153.15) #D'Alessio Seaboard exit to North Kryta Province               
EXPLORABLE_TO_TRAVEL = 58 #North Kryta Province
KILLING_PATH = [(-11726.47, -17031.03),
                (-10083.99, -12505.94),
                (-8819.55, -17244.03),
                (-6533.14, -15805.85),
                (-5172.82, -16486.04),
                (-2579.66, -16194.29),
                (-2742.62, -11661.84),
                (-6118.77, -7830.03),
                (-6837.74, -8934.17),
                (-1888.90, -6998.72),
                (1191.74, -9957.51),
                (4830.70, -10383.47),
                (3755.32, -12336.01),
                (4753.88, -14820.70),
                (2840.75, -17477.89),
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

bot.SetMainRoutine(bot_routine)

def main():
    bot.Update()
    texture = get_texture_for_model(model_id=MODEL_ID_TO_FARM)
    bot.UI.draw_window(icon_path=texture)

if __name__ == "__main__":
    main()
