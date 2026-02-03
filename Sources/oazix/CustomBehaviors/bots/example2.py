from Bots.Winter.snowball_dominance import on_death
from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

from Sources.oazix.CustomBehaviors.primitives.botting.botting_fsm_helper import BottingFsmHelpers

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Truffle Farmer"
MODEL_ID_TO_FARM = ModelID.Truffle
OUTPOST_TO_TRAVEL = 130 #Vasburg Armory
COORD_TO_EXIT_MAP = (24082, 7150)
EXPLORABLE_TO_TRAVEL =205 #Morostav Trail        
                
KILLING_PATH = [(-12902.83, 3627.39),
                (-17624.64, 9130.87),
                ]

NICK_OUTPOST = 130 #Vasburg Armory
COORDS_TO_EXIT_OUTPOST = (24082, 7150)
EXPLORABLE_AREA = 205 #Morostav Trail
NICK_COORDS = [(-10685.96, 3025.99),
               (-984.28, -2503.44), ]

bot = Botting(BOT_NAME)
bot.Properties.Enable("auto_inventory_management")
bot.Properties.Disable("auto_loot")
bot.Properties.Disable("hero_ai")
bot.Properties.Disable("auto_combat")
bot.Properties.Disable("pause_on_danger")
bot.Properties.Disable("halt_on_death")
bot.Properties.Set("movement_timeout",value=-1)



how to set on_death
as stuff is cleanned each time we call   bot.Templates.Aggressive()

on_death / resign if needed to change ?
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Templates.Aggressive()
    bot.Wait.ForTime(3000)
    bot.Templates.Pacifist()
    bot.Wait.ForTime(4000)
    bot.Templates.Aggressive()
    bot.Wait.ForTime(3000)

    bot.Wait.ForTime(10000000)

bot.SetMainRoutine(bot_routine)

def nicks_window():
    if PyImGui.begin("Nicholas the Traveler", True):
        PyImGui.text(BOT_NAME)
        PyImGui.separator()
        PyImGui.text("Travel to Nicholas the Traveler location")
        
        if PyImGui.button("Start"):
            bot.StartAtStep("[H]Path_to_Nicholas_4")

def main():
    bot.Update()
    texture = get_texture_for_model(model_id=MODEL_ID_TO_FARM)
    bot.UI.draw_window(icon_path=texture)
    nicks_window()

if __name__ == "__main__":
    main()
