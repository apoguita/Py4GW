from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, Agent, Player, ConsoleLog
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
import Py4GW
import os
import time

BOT_NAME = "Asura Title Farm"

MODULE_NAME = BOT_NAME
MODULE_ICON = "Textures/Skill_Icons/[2372] - Edification.jpg"

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
RATASUM = 640

bot = Botting(BOT_NAME,
              upkeep_armor_of_salvation_restock=2,
              upkeep_essence_of_celerity_restock=2,
              upkeep_grail_of_might_restock=2,
              upkeep_war_supplies_restock=2,
              upkeep_birthday_cupcake_restock=2,
              upkeep_honeycomb_restock=20,
              upkeep_auto_loot_active=True)

def Routine(bot: Botting) -> None:
    PrepareForCombat(bot)
    Fight(bot)

def PrepareForCombat(bot: Botting) -> None:
    bot.States.AddHeader("Enable Combat Mode")
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("hero_ai")
    bot.Multibox.ApplyWidgetPolicy(enable_widgets=('CustomBehaviors',))
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=RATASUM)
    bot.Party.SetHardMode(True)

def Fight(bot: Botting) -> None:
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    bot.States.AddHeader("Start Combat")
    bot.Move.XY(-6062, -2688,"Exit Outpost")
    bot.Wait.ForMapLoad(target_map_name="Magus Stones")
    PrepareForBattle(bot)
    bot.States.AddManagedCoroutine("Anti-Stuck Watchdog", lambda: _anti_stuck_watchdog(bot))
    bot.Move.XY(14778.00, 13178.00)
    bot.Wait.ForTime(1500)
    bot.Move.XYAndInteractNPC(14778.00, 13178.00)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Multibox.SendDialogToTarget(0x85)

    # Path segment 1
    bot.Move.XY(18825, 6180, "First Spider Group")
    bot.Move.XY(18447, 4537, "Second Spider Group")
    bot.Move.XY(18331, 2108, "Spider Pop")
    bot.Move.XY(17526, 143, "Spider Pop 2")
    bot.Move.XY(17205, -1355, "Third Spider Group")
    bot.Move.XY(17542, -4865, "Krait Group")
    bot.Move.XY(15562, -5524, "Moving")
    bot.Move.XY(16270, -6288, "Moving")
    bot.Move.XY(17501, -5545, "Moving")
    bot.Move.XY(18111, -8030, "Krait Group")
    bot.Move.XY(18409, -8474, "Moving")
    bot.Move.XY(18613, -11799, "Froggy Group")
    bot.Move.XY(17154, -15669, "Krait Patrol")
    bot.Move.XY(14250, -16744, "Second Patrol")
    bot.Move.XY(12186, -14139, "Krait Patrol")
    bot.Move.XY(12540, -13440, "Krait Patrol")
    bot.Move.XY(13234, -9948, "Krait Group")
    bot.Move.XY(8875, -9065, "Krait Group")
    bot.Move.XY(8647, -5852, "Moving")
    bot.Move.XY(6939, -3629, "Moving")
    bot.Move.XY(8711, -6046, "Moving")
    bot.Move.XY(7616, -8978, "Moving")
    bot.Move.XY(4671, -8699, "Krait Patrol")
    bot.Move.XY(-5203, -8280, "Moving")
    bot.Move.XY(1534, -5493, "Krait Group")
    bot.Move.XY(1052, -7074, "Moving")
    bot.Move.XY(-1029, -8724, "Spider Group")
    bot.Move.XY(-3439, -10339, "Krait Group")
    bot.Move.XY(-3024, -12586, "Spider Cave")
    bot.Move.XY(-742, -13786, "Spider Cave")
    bot.Move.XY(-2755, -14099, "Spider Cave")
    bot.Move.XY(-3393, -15633, "Spider Cave")
    bot.Move.XY(-4635, -16643, "Spider Pop")
    bot.Move.XY(-7814, -17796, "Spider Group")
    bot.Move.XY(-10109, -17520, "Moving")
    bot.Move.XY(-9111, -17237, "Moving")
    bot.Move.XY(-10963, -15506, "Ranger Boss Group")
    bot.Move.XY(-13975, -17857, "Corner Spiders")
    bot.Move.XY(-11912, -10641, "Froggy Group")
    bot.Move.XY(-8760, -9933, "Krait Boss Warrior")
    bot.Move.XY(-14030, -9780, "Froggy Coing Group")
    bot.Move.XY(-12368, -7330, "Froggy Group")

    # Path segment 2 blessing
    bot.Move.XY(-9317, -2618, "Taking Blessing")
    bot.Wait.ForTime(1500)
    bot.Move.XYAndInteractNPC(-9317, -2618)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Multibox.SendDialogToTarget(0x85)

    # Path segment 2
    bot.Move.XY(-12368, -7330, "Froggy Group")
    bot.Move.XY(-16527, -8175, "Froggy Patrol")
    bot.Move.XY(-17391, -5984, "Froggy Group")
    bot.Move.XY(-15704, -3996, "Froggy Patrol")
    bot.Move.XY(-16609, -2607, "Moving")
    bot.Move.XY(-16480, 2522, "Krait Group")
    bot.Move.XY(-17090, 5252, "Krait Group")
    bot.Move.XY(-18640, 8724, "Moving")
    bot.Move.XY(-18484, 12021, "Krait Patrol")
    bot.Move.XY(-17180, 13093, "Krait Patrol")
    bot.Move.XY(-15072, 14075, "Froggy Group")
    bot.Move.XY(-11888, 15628, "Froggy Group")
    bot.Move.XY(-12043, 18463, "Froggy Boss Warrior")
    bot.Move.XY(-8876, 17415, "Froggy Group")
    bot.Move.XY(-4770, 20353, "Froggy Group")
    bot.Move.XY(-10970, 16860, "Moving Back")
    bot.Move.XY(-9301, 15054, "Moving")
    bot.Move.XY(-9942, 12561, "Moving")
    bot.Move.XY(-9786, 10297, "Moving")
    bot.Move.XY(-5379, 16642, "Krait Group")
    bot.Move.XY(-2828, 18210, "Moving")
    bot.Move.XY(-4246, 16728, "Krait Group")
    bot.Move.XY(-2974, 14197, "Krait Group")
    bot.Move.XY(-5228, 12475, "Boss Patrol")
    bot.Move.XY(-6756, 12380, "Moving")
    bot.Move.XY(-3468, 10837, "Lonely Patrol")
    bot.Move.XY(-3804, 8017, "Krait Group")
    bot.Move.XY(-3288, 7276, "Moving")
    bot.Move.XY(-1346, 12360, "Moving")

    # Path segment 3 blessing
    bot.Move.XY(4835, 440, "Taking Blessing")
    bot.Wait.ForTime(1500)
    bot.Move.XYAndInteractNPC(4835, 440)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Multibox.SendDialogToTarget(0x85)

    # Path segment 3
    bot.Move.XY(-1346, 12360, "Moving")
    bot.Move.XY(874, 14367, "Moving")
    bot.Move.XY(3572, 13698, "Krait Group Standing")
    bot.Move.XY(5899, 14205, "Moving")
    bot.Move.XY(7407, 11867, "Krait Group")
    bot.Move.XY(9541, 9027, "Rider")
    bot.Move.XY(12639, 7537, "Rider Group")
    bot.Move.XY(9064, 7312, "Rider")
    bot.Move.XY(7986, 4365, "Krait group")
    bot.Move.XY(8558, 2759, "Moving")
    bot.Move.XY(10685, 3500, "Moving")
    bot.Move.XY(10202, 5369, "Moving")
    bot.Move.XY(8043, 5949, "Moving")
    bot.Move.XY(7978, 3339, "Moving")
    bot.Move.XY(6341, 3029, "Krait Group")
    bot.Move.XY(5362, 3391, "Moving")
    bot.Move.XY(7097, 92, "Krait Group")
    bot.Move.XY(8943, -985, "Krait Boss")
    bot.Move.XY(10949, -2056, "Krait Patrol")
    bot.Move.XY(13780, -5667, "Rider Patrol")
    bot.Move.XY(10752, 991, "Moving")
    bot.Move.XY(8193, -841, "Moving Back")
    bot.Move.XY(3284, -1599, "Krait Group")
    bot.Move.XY(-76, -1498, "Krait Group")
    bot.Move.XY(578, 719, "Krait Group")
    bot.Move.XY(1703, 3975, "Moving")
    bot.Move.XY(316, 2489, "Krait Group")
    bot.Move.XY(-1018, -1235, "Moving Back")
    bot.Move.XY(-3195, -1538, "Krait Patrol")
    bot.Move.XY(-6322, -2565, "Krait Group")
    bot.Move.XY(-11414, 4055, "Leftovers Krait")
    bot.Move.XY(-7030, 8396, "Moving")
    bot.Move.XY(-8689, 11227, "Leftovers Krait and Rider")
    bot.Move.XY(4671, -8699, "Krait Patrol")
    bot.Move.XY(-1018, -1235, "Moving Back")
    bot.Move.XY(-6322, -2565, "Krait Group")
    bot.Move.XY(-8760, -9933, "Krait Boss Warrior")
    
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.Wait.ForTime(5000)
    bot.States.JumpToStepName("[H]Enable Combat Mode_1")


def PrepareForBattle(bot: Botting):

    # Conset enabled in settings
    if bot.Properties.Get("armor_of_salvation", "active"):
        bot.Items.Restock.Conset()

    # Pcons enabled in settings
    if bot.Properties.Get("birthday_cupcake", "active"):
        bot.Items.Restock.AllPcons()


EXPLORABLE_TIMEOUT_SECONDS = 3 * 3600  # 3 hours


def _anti_stuck_resign(bot: "Botting"):
    """Called when the timeout fires: resign, wait for outpost, then restart."""
    yield from bot.helpers.Multibox._resignParty()
    while True:
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            continue
        if Routines.Checks.Map.IsOutpost():
            break
    bot.States.JumpToStepName("[H]Enable Combat Mode_1")
    bot.config.FSM.resume()
    yield


def _anti_stuck_watchdog(bot: "Botting"):
    """Resign the party if stuck in explorable for more than 3 hours."""
    explorable_entry_time = None
    while True:
        yield from bot.Wait._coro_for_time(60000)  # check every minute
        if not Routines.Checks.Map.MapValid():
            explorable_entry_time = None
            continue
        if Routines.Checks.Map.IsOutpost():
            explorable_entry_time = None
            continue
        # We are in explorable
        if explorable_entry_time is None:
            explorable_entry_time = time.time()
            continue
        elapsed = time.time() - explorable_entry_time
        if elapsed >= EXPLORABLE_TIMEOUT_SECONDS:
            ConsoleLog(BOT_NAME, f"Anti-stuck: {elapsed/3600:.1f}h in explorable - resigning party.", Py4GW.Console.MessageType.Warning)
            explorable_entry_time = None
            bot.config.FSM.pause()
            bot.config.FSM.AddManagedCoroutine("AntiStuck_Resign", lambda: _anti_stuck_resign(bot))


def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
    bot.States.JumpToStepName("[H]Start Combat_2")
    bot.config.FSM.resume()
    
def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot)) 

bot.UI.override_draw_config(lambda: _draw_settings(bot))

bot.SetMainRoutine(Routine)

def _draw_settings(bot: Botting):
    import PyImGui

    PyImGui.text("Bot Settings")

    # Conset controls
    use_conset = bot.Properties.Get("armor_of_salvation", "active")
    use_conset = PyImGui.checkbox("Restock & use Conset", use_conset)
    for key in ("armor_of_salvation", "essence_of_celerity", "grail_of_might"):
        bot.Properties.ApplyNow(key, "active", use_conset)

    # Pcons controls
    use_pcons = bot.Properties.Get("birthday_cupcake", "active")
    use_pcons = PyImGui.checkbox("Restock & use Pcons", use_pcons)
    for key in (
        "birthday_cupcake",
        "golden_egg",
        "candy_corn",
        "candy_apple",
        "slice_of_pumpkin_pie",
        "drake_kabob",
        "bowl_of_skalefin_soup",
        "pahnai_salad",
        "war_supplies",
        "honeycomb",
    ):
        bot.Properties.ApplyNow(key, "active", use_pcons)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Asura Title Farm", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi Account, farm Asura title in Magus Stones")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Wick Divinus")
    PyImGui.end_tooltip()

_session_baselines: dict[str, int] = {}
_session_start_times: dict[str, float] = {}

def _draw_title_track():
    global _session_baselines, _session_start_times
    import PyImGui
    title_idx = int(TitleID.Asuran)
    tiers = TITLE_TIERS.get(TitleID.Asuran, [])
    now = time.time()
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        name = account.AgentData.CharacterName
        pts = account.TitlesData.Titles[title_idx].CurrentPoints
        if name not in _session_baselines:
            _session_baselines[name] = pts
            _session_start_times[name] = now
        tier_name = "Unranked"
        prev_required = 0
        next_required = tiers[0].required if tiers else 0
        for i, tier in enumerate(tiers):
            if pts >= tier.required:
                tier_name = tier.name
                prev_required = tier.required
                next_required = tiers[i + 1].required if i + 1 < len(tiers) else tier.required
            else:
                next_required = tier.required
                break
        is_maxed = tiers and pts >= tiers[-1].required
        PyImGui.separator()
        PyImGui.text(f"{name}  [{tier_name}]")
        if is_maxed:
            PyImGui.text_colored("Maximum rank achieved. Title complete.", (0.4, 1.0, 0.4, 1.0))
            continue
        gained = pts - _session_baselines[name]
        elapsed = now - _session_start_times[name]
        pts_hr = int(gained / elapsed * 3600) if elapsed > 0 else 0
        PyImGui.text(f"Points: {pts:,} / {next_required:,}")
        if next_required > prev_required:
            frac = min((pts - prev_required) / (next_required - prev_required), 1.0)
            PyImGui.progress_bar(frac, -1, 0, f"{pts - prev_required:,} / {next_required - prev_required:,}")
        PyImGui.text(f"+{gained:,}  ({pts_hr:,}/hr)")

REFORGED_TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "Wick Divinus bots", "Reforged_Icon.png")
def main():
    bot.Update()
    bot.UI.draw_window(icon_path=REFORGED_TEXTURE, extra_tabs=[("Statistics", _draw_title_track)])

if __name__ == "__main__":
    main()
