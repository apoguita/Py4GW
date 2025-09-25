from Py4GWCoreLib import Botting
import PyImGui

#QUEST TO INCREASE SPAWNS https://wiki.guildwars.com/wiki/Lady_Mukei_Musagi
BOT_NAME = "example to jump to step name"


bot = Botting(BOT_NAME)
                
def bot_routine(bot: Botting) -> None:
    bot.States.AddHeader("Unlock Skill #1")
    bot.UI.PrintMessageToConsole("Skill #1","This is a fake message pretending to do something useful in skill 1")
    bot.States.JumpToStepName("[H]End_4")
    bot.States.AddHeader("Unlock Skill #2")
    bot.UI.PrintMessageToConsole("Skill #2","This is a fake message pretending to do something useful in skill 2")
    bot.States.JumpToStepName("[H]End_4")
    bot.States.AddHeader("Unlock Skill #3")
    bot.UI.PrintMessageToConsole("Skill #3","This is a fake message pretending to do something useful in skill 3")
    bot.States.JumpToStepName("[H]End_4")
    bot.States.AddHeader("End")
    bot.UI.PrintMessageToConsole("End","This is the end of the bot routine")



bot.SetMainRoutine(bot_routine)

def Draw_Window():
    if PyImGui.begin("My Skill Farmer", True, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text("This is an example bot that jumps to a step name")
        if PyImGui.button("Start Bot  at Step 'Unlock Skill #1'"):
            bot.StartAtStep("[H]Unlock Skill #1_1")
            
        if PyImGui.button("Start Bot  at Step 'Unlock Skill #2'"):
            bot.StartAtStep("[H]Unlock Skill #2_2")

        if PyImGui.button("Start Bot  at Step 'Unlock Skill #3'"):
            bot.StartAtStep("[H]Unlock Skill #3_3")

        PyImGui.end()

def main():
    bot.Update()
    Draw_Window()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()
