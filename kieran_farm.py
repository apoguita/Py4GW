from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui)
import PyMap, PyImGui

bot = Botting("Kieran Farm Bot")

def create_bot_routine(bot: Botting) -> None:
    GoToHOM(bot)
    AcquireBow(bot)
    

def GoToHOM(bot: Botting) -> None:
    bot.States.AddHeader("Go to HOM")
    bot.Map.Travel(target_map_id=642) #eye of the north outpost
    bot.Move.XYAndExitMap(x=-4873.00, y=5284.00, target_map_id=646, step_name="Exit to HOM")

def AcquireBow(bot: Botting) -> None:
    bot.States.AddHeader("Acquire Bow")
    bot.Move.XYAndDialog(-6583.00, 6672.00, 0x0000008A) #take bow with gwen

bot.SetMainRoutine(create_bot_routine)

def main():
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()
