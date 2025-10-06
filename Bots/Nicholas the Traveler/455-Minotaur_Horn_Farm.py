from Py4GWCoreLib import Botting, get_texture_for_model, ModelID

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Minotaur_Horn_farm"
MODEL_ID_TO_FARM = ModelID.Minotaur_Horn
MAP_TO_TRAVEL = 118 #Elona reach

KILLING_PATH = [(14162.11, 710.98), #around mine
                (12682.96, 1254.73), #first pack
                #(17992.46, 1559.90), #right pack (waste of time)
                #(11488.23, -3075.93), #left pack #see if patrol reaches here
                (10325.84, 2588.03), #center pack
                (5405.39, 3959.88), #right patrol
                (4599.24, 5043.31), #end
                ]

bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=MAP_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Map.EnterChallenge(delay= 15_000, target_map_id=MAP_TO_TRAVEL)
    bot.Move.XY(14113.48, -533.04) #move to priest
    bot.Interact.WithNpcAtXY(14064.00, -463.00) #talk with priest
    bot.UI.DropBundle()  #drop bundle
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
