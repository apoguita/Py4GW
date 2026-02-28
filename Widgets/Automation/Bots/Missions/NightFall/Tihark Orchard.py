from Py4GWCoreLib import (Routines,Botting,ActionQueueManager)

bot = Botting("tihark_orchard")
MODULE_NAME = "Tihark Orchard"
MODULE_ICON = "Textures\\Module_Icons\\Mission - Tihark Orchard.png"
     
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    EnterMission(bot)
    TiharkOrchard(bot)

def _on_death(bot: "Botting"):
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.Properties.ApplyNow("halt_on_death","active", True)
    bot.Properties.ApplyNow("movement_timeout","value", 15000)
    bot.Properties.ApplyNow("auto_combat","active", False)
    yield from Routines.Yield.wait(8000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Initialize Bot_1") 
    fsm.resume()                           
    yield  
    
def on_death(bot: "Botting"):
    print ("Player is dead. Run Failed, Restarting...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM 
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))
    
def InitializeBot(bot: Botting) -> None:
    bot.States.AddHeader("Initialize Bot")
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)
    bot.Templates.Pacifist()

def EnterMission(bot: Botting):
    bot.States.AddHeader("Enter Mission")
    bot.Map.Travel(428)
    bot.Wait.UntilOnOutpost()
    bot.Move.XYAndDialog (-1458.05, 13841.14, 0x84)
    bot.Wait.UntilOnExplorable()
    
def TiharkOrchard(bot: Botting):
    bot.States.AddHeader("Tihark Orchard")
    path = [(-5243.16, -5885.16), (-10958.97, 1535.55)]
    bot.Move.FollowAutoPath(path)
    bot.Move.XYAndDialog(-11145.00, 2400.00, 0x84, "Talkhora")
    bot.Move.XYAndDialog(-10799.00, 2478.00, 0x84, "Guard")
    bot.Move.XYAndDialog(-11148.00, 2704.00, 0x84, "Methu the Wise")
    bot.Move.XYAndDialog(-11403.00, 1257.00, 0x84, "Bokka")
    bot.Move.XYAndDialog(-10880.00, 145.00, 0x84, "Amthur")
    bot.Interact.WithNpcAtXY(-10880.00, 145.00)
    bot.Wait.ForTime(5000)
    bot.Templates.Aggressive()
    path = [(-7808.27, 2277.65), (-5930.22, 3588.73), (-7981.76, 380.05), (-6094.06, -3301.68)]
    bot.Move.FollowAutoPath(path)
    bot.Wait.UntilOnOutpost()

bot.SetMainRoutine(create_bot_routine)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Tihark Orchard Bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Single Account, finish Mission Tihark Orchard")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    PyImGui.end_tooltip()

def main():
    bot.Update()
    bot.UI.draw_window(icon_path="Keiran_art.png")

if __name__ == "__main__":
    main()
