from Py4GWCoreLib import Botting, get_texture_for_item, ModelID

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Jade_Bracelet_farm"
MODEL_ID_TO_FARM = ModelID.Jade_Bracelet
OUTPOST_TO_TRAVEL = 303 #the marketplace
COORD_TO_EXIT_MAP = (11550, 15370) #the marketplace exit to wajjun bazaar
EXPLORABLE_TO_TRAVEL = 239 #wajjun bazaar
KILLING_PATH = [(8783.02, 13982.29), #1st pack
                (4052.50, 10602.61), #boss plattform
                (4349.28, 8925.03), 
                (484.37, 11195.94), # u turn
                (2116.56, 12560.05), 
                (2122.46, 15444.26), #across bridge
                (-157.73, 16189.70), 
                (1495.84, 17942.95), #pop ups
                (-927.66, 19029.05),
                (-4559.49, 21825.98), #center room
                (-6839.20, 20286.12),
                (-4559.49, 21825.98), #back to bridge
                (-8662.86, 21764.57), #over bridge (left)
                (-14481.43, 21896.48), #left patrol
                (-8662.86, 21764.57), #over bridge (return)
                (-6243.48, 16866.82), #lower part
                (-4634.25, 17171.83), #bridge pop ups
                (-8077.50, 14842.13),
                (-7602.12, 14178.50), #pop ups
                (-7782.83, 15887.14), #kill the pop ups
                (-7548.14, 11638.42), #res shrine patrol
                (-3371.81, 11433.03), #last patrol
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
    texture = get_texture_for_item(model_id=MODEL_ID_TO_FARM)
    bot.UI.draw_window(icon_path=texture)

if __name__ == "__main__":
    main()
