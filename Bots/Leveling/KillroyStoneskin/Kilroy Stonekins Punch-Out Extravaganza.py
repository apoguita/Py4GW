from Py4GWCoreLib import Botting, get_texture_for_model, GLOBAL_CACHE, Routines, ActionQueueManager
import PyImGui, Py4GW
import os
BOT_NAME = "Killroy Stoneskin"

bot = Botting(BOT_NAME)

def bot_routine(bot: Botting) -> None:
    KillroyMap(bot)
    UnlockKillroy(bot)
    #end_routine(bot)
                
def KillroyMap(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    OnDeath(bot)
    bot.Map.Travel(target_map_id=644) # Gunnar's Hold
    bot.Templates.Aggressive(enable_imp=False)
    bot.Move.XYAndDialog(17341.00, -4796.00, 0x835803)
    bot.Move.XYAndDialog(17341.00, -4796.00, 0x835801)
    bot.Move.XYAndDialog(17341.00, -4796.00, 0x85)
    bot.Wait.UntilOnExplorable()
    path = [(-15115.72, -15375.61),(-11299.54, -16402.40),(-7284.53, -16235.58),
            (-4397.42, -16123.15),(-1385.20, -14400.23),(505.33, -14073.99),
            (2959.12, -15991.76),(5740.82, -15543.48),(7157.02, -15755.44),
            (12249.79, -16291.74),]
    bot.Move.FollowAutoPath(path)
    bot.Wait.UntilOutOfCombat()
    bot.Interact.WithGadgetAtXY(13275.00, -16039.00)
    bot.Templates.Pacifist()
    bot.Wait.ForTime(3000)
    bot.Party.Resign()
    bot.Wait.UntilOnOutpost()
    bot.Move.XYAndDialog(17341.00, -4796.00, 0x835807)
    bot.Map.TravelGH()
    bot.Wait.UntilOnOutpost()
    bot.Map.LeaveGH()
    bot.Wait.ForMapLoad(target_map_id=644)  # gunnars_hold_id
    bot.States.JumpToStepName("[H]Killroy Stoneskin_1")
  
def UnlockKillroy(bot: Botting):
    bot.States.AddHeader("Unlock Killroy and Skills")
    bot.Map.Travel(target_map_id=644)  # gunnars_hold_id
    bot.Templates.Aggressive(enable_imp=False)
    bot.Move.XYAndDialog(17341.00, -4796.00, 0x835A01)
    bot.Dialogs.AtXY(17341.00, -4796.00, 0x84)
    bot.Wait.ForMapLoad(target_map_id=703)  # killroy_map_id
    bot.Items.Equip(24897) #brass_knuckles_item_id
    bot.Move.XY(19290.50, -11552.23)
    bot.Wait.UntilOnOutpost()
    bot.Move.XYAndDialog(17341.00, -4796.00,0x835A07)
    bot.UI.CancelSkillRewardWindow()

    
#region Events
def _on_death(bot: "Botting"):
    import PySkillbar
    skillbar = PySkillbar.Skillbar()
    slot = 8 # slot 8 is the default "revive" skill
    while True:
        if not Routines.Checks.Map.MapValid():
            yield from Routines.Yield.wait(1000)
            continue
        
        energy = GLOBAL_CACHE.Agent.GetEnergy(GLOBAL_CACHE.Player.GetAgentID())
        max_energy = GLOBAL_CACHE.Agent.GetMaxEnergy(GLOBAL_CACHE.Player.GetAgentID())
        if max_energy >= 80: #we can go much higher but were dying too much, not worth the time
            bot.config.FSM.pause()
            yield from bot.Map._coro_travel(644)
            bot.config.FSM.jump_to_state_by_name("[H]Killroy Stoneskin_1")
            bot.config.FSM.resume()
            yield from Routines.Yield.wait(1000)
            continue
        
        
        while energy < 0.9999:
            ActionQueueManager().AddAction("FAST", skillbar.UseSkillTargetless, slot)
            yield from Routines.Yield.wait(20)
            energy = GLOBAL_CACHE.Agent.GetEnergy(GLOBAL_CACHE.Player.GetAgentID())
            if energy >= 0.9999:
                ActionQueueManager().ResetAllQueues()

        yield from Routines.Yield.wait(500)
            
    
def OnDeath(bot: "Botting"):
    bot.States.AddManagedCoroutine("OnDeath_OPD", lambda: _on_death(bot))

bot.SetMainRoutine(bot_routine)        

def draw_window(bot: Botting):
    if PyImGui.begin("debug data"):
        #PyImGui.text(f"IsDead: {GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID())}")
        #PyImGui.text(f"Energy: {GLOBAL_CACHE.Agent.GetEnergy(GLOBAL_CACHE.Player.GetAgentID())}")
        #PyImGui.text(f"Max Energy: {GLOBAL_CACHE.Agent.GetMaxEnergy(GLOBAL_CACHE.Player.GetAgentID())}")
        #PyImGui.text(f"Health: {GLOBAL_CACHE.Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID())}")
        #PyImGui.text(f"Max Health: {GLOBAL_CACHE.Agent.GetMaxHealth(GLOBAL_CACHE.Player.GetAgentID())}")
        if PyImGui.button("Unlock Killroy and Skills"):
            bot.StartAtStep("[H]Unlock Killroy and Skills_2")
    PyImGui.end()
    
def configure():
    global bot
    bot.UI.draw_configure_window()
    
    
def main():
    bot.Update()
    draw_window(bot)
    path = os.path.join(Py4GW.Console.get_projects_path(),"Bots", "Leveling", "KillroyStoneskin","Kilroy Stonekins Punch-Out Extravaganza-art.png")
    bot.UI.draw_window(icon_path=path)

if __name__ == "__main__":
    main()
