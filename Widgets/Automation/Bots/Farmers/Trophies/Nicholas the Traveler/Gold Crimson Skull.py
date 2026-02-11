from Py4GWCoreLib import Botting, get_texture_for_model, ModelID

#QUEST TO INCREASE SPAWNS https://wiki.guildwars.com/wiki/Lady_Mukei_Musagi
BOT_NAME = "Gold_Crimson_Skull_farm"
MODEL_ID_TO_FARM = ModelID.Gold_Crimson_Skull_Coin
OUTPOST_TO_TRAVEL = 213 #zen daijun
COORD_TO_EXIT_MAP = (19453, 14369) #zen daijun exit to haiju lagoon
EXPLORABLE_TO_TRAVEL = 237 #haiju lagoon
KILLING_PATH = [(11408.93, -16978.96),
                (7103.21, -16858.03),
                (7455.71, -13737.78),
                (5217.51, -5943.70),
                (4353.15, -3805.84),
                (5981.66, -1130.67),
                (9768.93, -59.43), #nagas
                (6529.08, 1079.59),
                (7568.13, 4493.92),
                (6366.02, 5916.83),
                (8217.38, 5118.34),
                (9056.74, 6211.91),
                (11050.25, 6758.59),
                (6966.44, 9630.68),
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
