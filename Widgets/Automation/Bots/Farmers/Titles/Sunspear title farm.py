from Py4GWCoreLib import *
from Py4GWCoreLib import Botting, Map, Player, ConsoleLog, Agent, Routines, GLOBAL_CACHE, TitleID, TITLE_TIERS

import Py4GW
import PyImGui
import os
import time

MODULE_NAME = "Sunspear Title Farm copia"
MODULE_ICON = "Textures/Skill_Icons/[1816] - Sunspear Rebirth Signet.jpg"

class BotSettings:
    BOT_NAME = "Sunspear Title Farm"
    OUTPOST_TO_TRAVEL = 381
    EXPLORABLE_TO_TRAVEL = 380
    COORD_TO_EXIT_MAP = (4603,904)
    COORD_TO_ENTER_MAP = (-20222,-14488)
    KILLING_PATH:list[tuple[float, float]] = [
    (-18697,-12296),
    (-18557,-10503),
    (-17265,-15287),
    (-17158,-16655),
    ]
    BOUNTY_COORDS = (-17223.00, -12543.00)
    BOUNTY_DIALOG = 0x85
    TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Skill_Icons", "[1816] - Sunspear Rebirth Signet.jpg")
    TIMER = 10 # Max minutes to stay in instance
    WIDGETS_TO_ENABLE: tuple[str, ...] = (
        "Return to outpost on defeat",
    )

bot = Botting(BotSettings.BOT_NAME,
              upkeep_armor_of_salvation_restock=2,
              upkeep_essence_of_celerity_restock=2,
              upkeep_grail_of_might_restock=2,
              upkeep_war_supplies_restock=2,
              upkeep_honeycomb_restock=20)

def bot_routine(bot: Botting) -> None:
    # Widgets    
    bot.Multibox.ApplyWidgetPolicy(enable_widgets=BotSettings.WIDGETS_TO_ENABLE)

    # Events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)

    # Combat preparations
    bot.States.AddHeader("Combat preparations") # 1
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=BotSettings.OUTPOST_TO_TRAVEL) # 2
    bot.Party.SetHardMode(True)
    
    # Resign setup
    bot.States.AddHeader("Resign setup") # 3
    bot.Move.XYAndExitMap(*BotSettings.COORD_TO_EXIT_MAP, target_map_id=BotSettings.EXPLORABLE_TO_TRAVEL)
    bot.Move.XYAndExitMap(*BotSettings.COORD_TO_ENTER_MAP, target_map_id=BotSettings.OUTPOST_TO_TRAVEL)
    
    # Combat loop
    bot.States.AddHeader("Combat loop") # 4
    PrepareForBattle(bot)
    bot.Move.XYAndExitMap(*BotSettings.COORD_TO_EXIT_MAP, target_map_id=BotSettings.EXPLORABLE_TO_TRAVEL)
    
    # Max Instance Timer coroutine setup
    bot.States.AddManagedCoroutine("TimeoutWatchdog", lambda: TimeoutWatchdog(bot))

    # Bounty interaction
    bot.States.AddHeader("Bounty interaction") # 5
    bot.Move.XY(*BotSettings.BOUNTY_COORDS)
    bot.Wait.ForTime(1500)
    bot.Move.XYAndInteractNPC(*BotSettings.BOUNTY_COORDS)
    bot.Multibox.SendDialogToTarget(BotSettings.BOUNTY_DIALOG)
    bot.Wait.ForTime(1500)

    # Killing path
    bot.States.AddHeader("Killing path") # 6
    bot.Move.FollowAutoPath(BotSettings.KILLING_PATH)
    bot.Wait.UntilOutOfCombat()

    # Resign & restart
    bot.States.AddHeader("Resign") # 7
    bot.States.RemoveManagedCoroutine("TimeoutWatchdog")
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName("[H]Combat loop_4")

def PrepareForBattle(bot: Botting):                  
    bot.Items.Restock.ArmorOfSalvation()
    bot.Items.Restock.EssenceOfCelerity()
    bot.Items.Restock.GrailOfMight()
    bot.Items.Restock.WarSupplies()
    bot.Items.Restock.Honeycomb()

def TimeoutWatchdog(bot: "Botting"):
    ConsoleLog("TimeoutWatchdog", f"Instance timer of {BotSettings.TIMER} minutes started.", Py4GW.Console.MessageType.Debug, True)
    while True:
        instance_time = Map.GetInstanceUptime() / 1000
        if instance_time > BotSettings.TIMER * 60:
            ConsoleLog("TimeoutWatchdog", f"Instance timer of {BotSettings.TIMER} minutes exceeded, force resigning.", Py4GW.Console.MessageType.Debug, True)
            bot.config.FSM.pause()
            bot.config.FSM.jump_to_state_by_name("[H]Resign_7")
            bot.config.FSM.resume()
            return
        yield from Routines.Yield.wait(500)
    
def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
    bot.States.JumpToStepName("[H]Resign_7")
    bot.config.FSM.resume()

def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    bot.config.FSM.pause()
    bot.config.FSM.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

bot.UI.override_draw_config(lambda: _draw_settings(bot))
bot.UI.override_draw_help(lambda: _draw_help(bot))

def _draw_settings(bot: Botting):
    PyImGui.text("Bot Settings")

    # Conset controls
    use_conset = bot.Properties.Get("armor_of_salvation", "active")
    use_conset = PyImGui.checkbox("Restock & use Conset", use_conset)
    bot.Properties.ApplyNow("armor_of_salvation", "active", use_conset)
    bot.Properties.ApplyNow("essence_of_celerity", "active", use_conset)
    bot.Properties.ApplyNow("grail_of_might", "active", use_conset)

    # War Supplies controls
    use_war_supplies = bot.Properties.Get("war_supplies", "active")
    use_war_supplies = PyImGui.checkbox("Restock & use War Supplies", use_war_supplies)
    bot.Properties.ApplyNow("war_supplies", "active", use_war_supplies)
                          
    # Honeycomb controls
    use_honeycomb = bot.Properties.Get("honeycomb", "active")
    use_honeycomb = PyImGui.checkbox("Restock & use Honeycomb", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)
    hc_restock_qty = bot.Properties.Get("honeycomb", "restock_quantity")
    hc_restock_qty = PyImGui.input_int("Honeycomb Restock Quantity", hc_restock_qty)
    bot.Properties.ApplyNow("honeycomb", "restock_quantity", hc_restock_qty)

def _draw_help(bot: Botting):
    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(BotSettings.BOT_NAME + " bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi-account bot to " + BotSettings.BOT_NAME)
    PyImGui.spacing()
    PyImGui.text_colored("Requirements:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Yohlon Haven outpost")     
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Aura")
    PyImGui.bullet_text("Contributors:")
    PyImGui.bullet_text("- Wick-Divinus for script template")

def tooltip():
    PyImGui.begin_tooltip()
    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(BotSettings.BOT_NAME + " bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi-account bot to " + BotSettings.BOT_NAME)
    PyImGui.spacing()
    PyImGui.text_colored("Requirements:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Yohlon Haven outpost")  
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Aura")
    PyImGui.bullet_text("Contributors:")
    PyImGui.bullet_text("- Wick-Divinus for script template")
    PyImGui.end_tooltip()

_session_baselines: dict[str, int] = {}
_session_start_times: dict[str, float] = {}

def _draw_title_track():
    global _session_baselines, _session_start_times

    title_idx = int(TitleID.Sunspear)
    tiers = TITLE_TIERS.get(TitleID.Sunspear, [])
    now = time.time()
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        name = account.AgentData.CharacterName
        pts = account.TitlesData.Titles[title_idx].CurrentPoints
        if name not in _session_baselines:
            _session_baselines[name] = pts
            _session_start_times[name] = now
        tier_name = "Unranked"
        tier_rank = 0
        tier_max_rank = len(tiers)
        prev_required = 0
        next_required = tiers[0].required if tiers else 0
        for i, tier in enumerate(tiers):
            if pts >= tier.required:
                tier_rank = i + 1
                tier_name = tier.name
                prev_required = tier.required
                next_required = tiers[i + 1].required if i + 1 < len(tiers) else tier.required
            else:
                next_required = tier.required
                break
        gained = pts - _session_baselines[name]
        elapsed = now - _session_start_times[name]
        formatted_time = time.strftime('%H:%M:%S', time.gmtime(elapsed))
        pts_hr = int(gained / elapsed * 3600) if elapsed > 0 else 0
        tier_missing = next_required - pts

        PyImGui.separator()
        ImGui.push_font("Regular", 18)
        PyImGui.text("Statistics")
        ImGui.pop_font()

        PyImGui.text(f"{name} - {tier_name} [{tier_rank}/{tier_max_rank}]")
        PyImGui.text(f"Points: {pts:,} / {next_required:,} - Next rank: {tier_missing:,}")
        if next_required > prev_required:
            frac = min((pts - prev_required) / (next_required - prev_required), 1.0)
            PyImGui.progress_bar(frac, -1, 0, f"{pts - prev_required:,} / {next_required - prev_required:,}")
        PyImGui.text(f"+{gained:,} points ({pts_hr:,}/hr) - Running for: {formatted_time}")

bot.SetMainRoutine(bot_routine)

def main():
    bot.Update()
    bot.UI.draw_window(icon_path=BotSettings.TEXTURE, additional_ui=_draw_title_track)

if __name__ == "__main__":
    main()
