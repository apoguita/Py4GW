from Py4GWCoreLib import *
import Py4GW
import os
import time

BOT_NAME = "Lightbringer - MirrorOfLyss"
OUTPOST_TO_TRAVEL = 414
EXPLORABLE_TO_TRAVEL = 419
KILLING_PATH:list[tuple[float, float]] = [
    (-13760, -13924),
    (-10600, -12671),
    (-4785, -14912),
    (-2451, -15086),
	(1174,	-13787),
	(6728,	-12014),
	(9554,	-14517),
	(16856, -14068),
	(19428, -13168),
	(16961, -7251),
	(20212, -5510),
	(20373, -580),
	(19778, 2882),
	(19561, 6432),
	(15914, 10322),
	(12116, 7908),
	(12932, 6907),
	(12956, 2637)
]
COORD_TO_EXIT_MAP = (-850.00, 4700.00)
COORD_TO_ENTER_MAP = (-19350.00, -16900.00)

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Skill_Icons", "[1813] - Lightbringer.jpg")

bot = Botting(BOT_NAME)

def bot_routine(bot: Botting) -> None:
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events

    # Combat preparations
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)
    bot.Party.SetHardMode(True)
    
    # Resign setup
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Move.XYAndExitMap(*COORD_TO_ENTER_MAP, target_map_id=OUTPOST_TO_TRAVEL)
    
    # Combat loop
    bot.States.AddHeader(f"{BOT_NAME}_loop") # 3
    bot.Move.XYAndExitMap(*COORD_TO_EXIT_MAP, target_map_id=EXPLORABLE_TO_TRAVEL)
    bot.Move.XYAndInteractNPC(-20928, -13121) # Bounty coords
    bot.Multibox.SendDialogToTarget(0x85) # Get Bounty
    bot.Move.FollowAutoPath(KILLING_PATH)
    bot.Wait.UntilOutOfCombat()
    bot.States.AddHeader("Resign") # 4
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(1000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_3")

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(BOT_NAME + " bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi-account bot to " + BOT_NAME)
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("- The Kodash Bazaar outpost.")

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Aura")
    PyImGui.bullet_text("Contributors:")
    PyImGui.bullet_text("- Wick-Divinus for script template")
    PyImGui.bullet_text("- Kronos for script idea and coords")
    PyImGui.end_tooltip()

def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
    bot.States.JumpToStepName("[H]Resign_4")
    bot.config.FSM.resume()
    
def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

bot.SetMainRoutine(bot_routine)

_session_baselines: dict[str, int] = {}
_session_start_times: dict[str, float] = {}

def _draw_title_track():
    global _session_baselines, _session_start_times
    import PyImGui
    title_idx = int(TitleID.Lightbringer)
    tiers = TITLE_TIERS.get(TitleID.Lightbringer, [])
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
                tier_rank = i
                tier_name = tier.name
                prev_required = tier.required
                next_required = tiers[i + 1].required if i + 1 < len(tiers) else tier.required
            else:
                next_required = tier.required
                break
        gained = pts - _session_baselines[name]
        elapsed = now - _session_start_times[name]
        pts_hr = int(gained / elapsed * 3600) if elapsed > 0 else 0
        PyImGui.separator()
        PyImGui.text(f"{name} - {tier_rank}/{tier_max_rank} - {tier_name}")
        PyImGui.text(f"Points: {pts:,} / {next_required:,}")
        if next_required > prev_required:
            frac = min((pts - prev_required) / (next_required - prev_required), 1.0)
            PyImGui.progress_bar(frac, -1, 0, f"{pts - prev_required:,} / {next_required - prev_required:,}")
        PyImGui.text(f"+{gained:,}  ({pts_hr:,}/hr)")

def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE, additional_ui=_draw_title_track)

if __name__ == "__main__":
    main()
