from Py4GWCoreLib import Botting, get_texture_for_model, ModelID

#QUEST TO INCREASE SPAWNS https://wiki.guildwars.com/wiki/Lady_Mukei_Musagi
BOT_NAME = "Gold_Crimson_Skull_farm"
MODEL_ID_TO_FARM = ModelID.Gold_Crimson_Skull_Coin
OUTPOST_TO_TRAVEL = 213 #zen daijun
COORD_TO_EXIT_MAP = (19453, 14369) #zen daijun exit to haiju lagoon
EXPLORABLE_TO_TRAVEL = 237 #haiju lagoon
KILLING_PATH = [(10723.99, -16477.64),(8121.74, -16777.29),(7323.90, -13430.26),
                (5155.61, -5554.35),(7767.08, -1231.90),(6709.90, 1558.74),
                (7628.94, 4270.59),(6136.08, 6090.77),(8261.40, 5307.92),
                (9428.20, 6738.58),(10957.15, 6759.82),(6693.86, 9704.84),]

bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
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
