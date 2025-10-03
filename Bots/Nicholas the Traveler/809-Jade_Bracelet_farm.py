from Py4GWCoreLib import Botting, get_texture_for_model, ModelID

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Jade_Bracelet_farm"
MODEL_ID_TO_FARM = ModelID.Jade_Bracelet
OUTPOST_TO_TRAVEL = 303 #the marketplace
COORD_TO_EXIT_MAP = (11550, 15370) #the marketplace exit to wajjun bazaar
EXPLORABLE_TO_TRAVEL = 239 #wajjun bazaar
KILLING_PATH = [(8783.02, 13982.29),
                (6380.29, 14769.24),
                (4771.89, 8527.53),
                (1730.61, 13009.83),
                (1081.21, 11236.47),
                (-2974.30, 12832.58),
                (-4224.05, 11043.88),
                (-7583.54, 11530.00),
                (-7638.18, 14662.45),
                (-8848.08, 16631.98),
                (-7282.28, 16474.78),
                (-4923.08, 18027.32),
                (-8730.03, 22096.41),
                (-5287.91, 22084.04),
                (-850.16, 22369.29),
                (-1428.99, 17535.78),
                (968.68, 17458.33),
                (157.88, 16306.99),
                (2077.53, 15510.69),
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
