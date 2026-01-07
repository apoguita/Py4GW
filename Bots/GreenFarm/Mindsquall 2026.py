from Py4GWCoreLib import Botting, get_texture_for_model, ModelID

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "The Mindsquall_Farm"
MODEL_ID_TO_FARM = ModelID.Feathered_Crest
OUTPOST_TO_TRAVEL = 640 #Rata Sum
COORD_TO_EXIT_MAP = (16429.57, 13491.29) #Rata Sum exit to Magus Stones
EXPLORABLE_TO_TRAVEL = 569 #Magus Stones
KILLING_PATH = [(16845.38, 11494.00),
                (15590.38, 8148.21),
                (14830.84, 8253.73),
                (13010.51, 6993.52),
                (14830.84, 8253.73),
                (13010.51, 6993.52),
                (13511.45, 7823.19),
                (15123.12, 8488.75),
                (13960.76, 10583.61),
                (12175.51, 9514.61),
                (13960.76, 10583.61),
                (12175.51, 9514.61),
                (13960.76, 10583.61),
                (12175.51, 9514.61),
                (11951.20, 7661.88),
                (9738.14, 9081.23),
                (9482.51, 8770.36),
                (9082.11, 9638.05),
                (7546.94, 12105.38),
                (7221.61, 10923.58),
                (5173.30, 10854.70),
                (3845.28, 13876.48),
                (-1146.77, 12302.44),
                (-4257.07, 12403.80),
                (-6287.15, 13025.13),
                (-8988.33, 12881.63),
                ]

bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Party.SetHardMode(False)
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Wait.ForTime(4000)
    bot.Move.XYAndInteractNPC(14810.47, 13164.24)
    bot.Multibox.SendDialogToTarget(0x84) #Get Bounty
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