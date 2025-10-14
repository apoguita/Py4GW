from Py4GWCoreLib import Botting, get_texture_for_model, ModelID

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Frosted_Griffon_Wing_Bot"
MODEL_ID_TO_FARM = ModelID.Frosted_Griffon_Wing
OUTPOST_TO_TRAVEL = 155 #Camp Rankor 
COORD_TO_EXIT_MAP = (5435, -40809) #Camp Rankor to Snake Dance
EXPLORABLE_TO_TRAVEL = 91 #snake dance
KILLING_PATH = [ (3162, -36810), (1362, -39175), (690, -41191), (-749, -41671), (1239, -43234), (-1069, -44007), (-4123, -43566), (-6346, -42793), (-3665, -40343) ]

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
