from Py4GWCoreLib import Botting, get_texture_for_model, ModelID

#QUEST TO INCREASE SPAWNS https://wiki.guildwars.com/wiki/Lady_Mukei_Musagi
BOT_NAME = "Donate Faction Multibox"
MODEL_ID_TO_FARM = ModelID.Gold_Crimson_Skull_Coin
OUTPOST_TO_TRAVEL = 77 #House Zu Helzer


bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.Wait.ForTime(1000)
    bot.Multibox.DonateFaction()
    bot.Wait.UntilOnCombat()

bot.SetMainRoutine(bot_routine)

def main():
    bot.Update()
    texture = get_texture_for_model(model_id=MODEL_ID_TO_FARM)
    bot.UI.draw_window(icon_path=texture)

if __name__ == "__main__":
    main()
