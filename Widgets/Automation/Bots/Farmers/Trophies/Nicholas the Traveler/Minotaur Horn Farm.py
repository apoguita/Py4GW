from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui
#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Minotaur_Horn_farm"
MODULE_NAME = "Minotaur Horn Farm (Nicholas the Traveler)"
MODULE_ICON = "Textures\\Module_Icons\\Nicholas the Traveler - Minotaur Horn.png"
MODEL_ID_TO_FARM = ModelID.Minotaur_Horn
MAP_TO_TRAVEL = 118 #Elona reach

KILLING_PATH = [(13663.38, 822.91), #around mine
                (12682.96, 1254.73), #first pack
                #(17992.46, 1559.90), #right pack (waste of time)
                (11564.66, -2009.70), #left pack
                (11668.46, 565.36),
                (10325.84, 2588.03), #center pack
                (7811.36, 4053.21), #avoid burrower
                (5405.39, 3959.88), #right patrol
                (4599.24, 5043.31), #end
                ]

NICK_OUTPOST = 38 #Nicholas the traveler outpost
COORDS_TO_EXIT_OUTPOST = (-20855,-357)
EXPLORABLE_AREA = 113
NICK_COORDS = (-5708.32, 7173.69)

bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=MAP_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Map.EnterChallenge(delay= 15_000, target_map_id=MAP_TO_TRAVEL)
    bot.Move.XY(14113.48, -533.04) #move to priest
    bot.Interact.WithNpcAtXY(14064.00, -463.00) #talk with priest
    bot.UI.Keybinds.DropBundle()  #drop bundle
    bot.Move.FollowAutoPath(KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_3")
    bot.States.AddHeader(f"Path_to_Nicholas")
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=NICK_OUTPOST)
    bot.Move.XYAndExitMap(*COORDS_TO_EXIT_OUTPOST, EXPLORABLE_AREA)
    bot.Move.XY(*NICK_COORDS)
    bot.Wait.UntilOnOutpost()
    

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
