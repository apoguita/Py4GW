from Py4GWCoreLib import Botting, get_texture_for_model, ModelID

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Minotaur_Horn_farm"
MODEL_ID_TO_FARM = ModelID.Minotaur_Horn
OUTPOST_TO_TRAVEL = 152 #Heroes' Audience
COORD_TO_EXIT_MAP = (-14919.86, -14413.34) #Heroes' Audience exit to Prophet's Path
EXPLORABLE_TO_TRAVEL = 113 #Prophet's Path
KILLING_PATH = [(-14291.14, -10090.61),
                (-16161.88, -4125.89),
                (-12476.75, -219.51),
                (-9976.50, -2423.78),
                (-11200.86, 2002.30),
                (-7088.60, 1476.05),
                (-7179.46, 5484.45),
                (-4353.88, 4545.13),
                (-3344.99, -223.10),
                (-7572.56, -1920.62),
                (-5836.28, -6174.29),
                (2088.78, 7810.71),
                (5190.07, 8797.19),
                (9580.65, 10899.99),
                (12631.94, 9835.60),
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
