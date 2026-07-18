from Py4GWCoreLib import (
    Botting,
    Routines,
    GLOBAL_CACHE,
    Map,
    Agent,
    ConsoleLog,
    Player,
    Skill,
    FSM,
    Range,
    Utils,
)
from Py4GWCoreLib.Builds.CombatAutomatorExcluded.SF_Derv_Runner import SF_Derv_Runner
import Py4GW
import os
import re
import math
import time
import PyImGui
import importlib.util
projects_base_path = Py4GW.Console.get_projects_path()
ac_folder_path = os.path.join(projects_base_path, "Sources", "aC_Scripts")
from Sources.aC_Scripts.aC_api import *
RUNS_DIR = os.path.join(ac_folder_path, "OutpostRunner", "maps")

MODULE_NAME = "Outpost Runner v2"
MODULE_ICON = "Textures\\Skill_Icons\\[1543] - Pious Haste.jpg"

# =============================================================================
# region BOT SETTINGS
# =============================================================================
class BotSettings:
    BOT_NAME = "Outpost Runner v2"
    WIDGETS_TO_ENABLE: tuple[str, ...] = (
        "Titles",
        "Return to outpost on defeat",
    )
    WIDGETS_TO_DISABLE: tuple[str, ...] = (
        "HeroAI",
    )

bot = Botting(BotSettings.BOT_NAME,
            custom_build=SF_Derv_Runner(),
            upkeep_birthday_cupcake_restock=5,
            upkeep_birthday_cupcake_active=True,
            upkeep_war_supplies_restock=5,
            upkeep_war_supplies_active=True,
            upkeep_alcohol_active=True,
            upkeep_armor_of_salvation_restock=5,
            upkeep_essence_of_celerity_restock=5,
            upkeep_grail_of_might_restock=5,
            upkeep_armor_of_salvation_active=False,
            upkeep_essence_of_celerity_active=False,
            upkeep_grail_of_might_active=False,
            upkeep_honeycomb_restock=10,
            upkeep_honeycomb_active=False,
            upkeep_hero_ai_active=True,
            config_draw_path=True)
# endregion

# =============================================================================
# region RUN QUEUE DATA
# =============================================================================
class QueuedRun:
    """Stores all data needed to execute a single run."""
    def __init__(self, region: str, run_name: str, display: str,
                 outpost_id: int, outpost_path: list, segments: list):
        self.region = region
        self.run_name = run_name
        self.display = display
        self.outpost_id = outpost_id
        self.outpost_path = outpost_path
        self.segments = segments

_queued_runs: list[QueuedRun] = []
_queue_version: int = 0
_current_run_index: int = 0
_run_tries: list[int] = []
# endregion

# =============================================================================
# region BOT ROUTINE
# =============================================================================
def bot_routine(bot: Botting) -> None:
    global _current_run_index, _run_tries

    if not _queued_runs:
        ConsoleLog(BotSettings.BOT_NAME, "No runs queued!", Py4GW.Console.MessageType.Error)
        bot.States.AddCustomState(lambda: _stop_bot(), "StopBot")
        return

    # Initialize tries counter
    _run_tries = [0] * len(_queued_runs)

    # Events
    bot.Events.OnDeathCallback(lambda: OnDeath(bot))
    bot.helpers.Events.set_on_unmanaged_fail(lambda: False)

    # Configuration
    bot.States.AddHeader("Run Preparations") # Header 1

    # Load skill bar from the build
    def _load_build_skillbar():
        yield from bot.config.build_handler.LoadSkillBar()
    bot.States.AddCustomState(lambda: _load_build_skillbar(), "LoadSkillBar")

    for run_idx, run in enumerate(_queued_runs):
        bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, f"Starting run {run_idx + 1} - {run.run_name}.")

        # -- Header for this specific run (used by OnDeath to retry) --
        run_header = f"Run_{run_idx + 1}_{run.run_name}"
        bot.States.AddHeader(run_header)

        # -- Update current run index and increment tries --
        def _set_current_index(idx=run_idx):
            global _current_run_index
            _current_run_index = idx
            _run_tries[idx] += 1
            yield
        bot.States.AddCustomState(lambda idx=run_idx: _set_current_index(idx),
                                  f"SetRunIndex_{run_idx}")

        # -- Travel to outpost --
        bot.Multibox.KickAllAccounts()
        bot.Map.Travel(target_map_id=run.outpost_id)
        bot.Multibox.SummonAllAccounts()
        bot.Wait.ForTime(4000)
        bot.Multibox.InviteAllAccounts()
        bot.Party.SetHardMode(False)
        bot.Items.Restock.WarSupplies()
        bot.Items.Restock.BirthdayCupcake()
        bot.Items.Restock.Honeycomb()
        bot.Items.Restock.ArmorOfSalvation()
        bot.Items.Restock.EssenceOfCelerity()
        bot.Items.Restock.GrailOfMight()

        # Widgets
        bot.Multibox.ApplyWidgetPolicy(enable_widgets=BotSettings.WIDGETS_TO_ENABLE)

        # -- Exit outpost --
        first_map_id = run.segments[0]["map_id"] if run.segments else 0
        bot.Move.FollowPathAndExitMap(run.outpost_path, target_map_id=first_map_id)

        # -- Follow explorable segments --
        for seg_i, entry in enumerate(run.segments):
            seg_path = entry.get("path", [])
            if seg_path:
                next_map_id = (
                    run.segments[seg_i + 1]["map_id"]
                    if seg_i + 1 < len(run.segments)
                    else entry["map_id"]
                )
                bot.Move.FollowAutoPath(seg_path)
                bot.Wait.ForMapToChange(next_map_id)

    # All runs finished
    bot.States.AddHeader("All Runs Finished")
    bot.UI.PrintMessageToConsole(BotSettings.BOT_NAME, "All runs finished. Bot Stopped.")
    bot.States.AddCustomState(lambda: _stop_bot(), "StopBot")

def _stop_bot():
    bot.Stop()
    yield
# endregion

# =============================================================================
# region DEATH / RESIGN HANDLER
# =============================================================================
def _get_current_run_header() -> str:
    if _current_run_index < len(_queued_runs):
        run = _queued_runs[_current_run_index]
        suffix = _current_run_index + 2
        return f"[H]Run_{_current_run_index + 1}_{run.run_name}_{suffix}"
    return "[H]Run Preparations_1"

def _on_death(bot: "Botting"):
    yield from bot.helpers.Multibox._resignParty()
    yield from bot.Wait._coro_until_on_outpost()

    target_header = _get_current_run_header()
    ConsoleLog("on_death", f"Retrying run: jumping to {target_header}")
    bot.config.FSM.jump_to_state_by_name(target_header)
    bot.config.FSM.resume()

def OnDeath(bot: "Botting"):
    ConsoleLog("on_death", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", lambda: _on_death(bot))
# endregion

# =============================================================================
# region UI
# =============================================================================
region_index = 0
run_index = 0
_prev_queue_version: int = -1

def _load_run_data(region_dir: str, run_name: str) -> QueuedRun:
    """Load a run module and return a QueuedRun with all its data."""
    run_file = os.path.join(region_dir, run_name) + ".py"
    spec = importlib.util.spec_from_file_location(run_name, run_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def _getattr_ci(module, suffix, default=None):
        """Case-insensitive getattr: find attribute ending with suffix."""
        suffix_lower = suffix.lower()
        for attr_name in dir(module):
            if attr_name.lower().endswith(suffix_lower):
                return getattr(module, attr_name)
        return default

    ids = _getattr_ci(mod, "_ids", {})
    outpost_id = ids.get("outpost_id", 0)
    outpost_path = _getattr_ci(mod, "_outpost_path", [])
    segments = _getattr_ci(mod, "_segments", [])

    region_name = os.path.basename(region_dir)
    display = f"[{region_name}] {run_name}"

    return QueuedRun(
        region=region_name,
        run_name=run_name,
        display=display,
        outpost_id=outpost_id,
        outpost_path=outpost_path,
        segments=segments,
    )

def _draw_settings():
    global region_index, run_index, _queue_version, _prev_queue_version

    # --- Region combo ---
    PyImGui.text("Region & Run Selection")
    PyImGui.separator()
    regions = sorted([d for d in os.listdir(RUNS_DIR) if os.path.isdir(os.path.join(RUNS_DIR, d))])
    region_index = PyImGui.combo("##Region", region_index, regions)
    REGION_DIR = os.path.join(RUNS_DIR, regions[region_index])

    # --- Run combo ---
    runs = sorted([
        f[:-3] for f in os.listdir(REGION_DIR) if f.endswith(".py")],
        key=lambda name: int(re.search(r"_(\d+)_", name).group(1))
            if re.search(r"_(\d+)_", name) else 0
    )
    run_index = PyImGui.combo("##Run", run_index, runs)
    if run_index >= len(runs):
        run_index = 0

    # --- Add Region / Add Run / Clear Runs buttons ---
    if PyImGui.button("Add Region", 120, 25):
        for rn in runs:
            qr = _load_run_data(REGION_DIR, rn)
            _queued_runs.append(qr)
        _queue_version += 1

    PyImGui.same_line(0, 10)
    if PyImGui.button("Add Run", 120, 25):
        qr = _load_run_data(REGION_DIR, runs[run_index])
        _queued_runs.append(qr)
        _queue_version += 1

    PyImGui.same_line(0, 10)
    if PyImGui.button("Clear Runs", 120, 25):
        _queued_runs.clear()
        _queue_version += 1

    # --- Queue display ---
    PyImGui.separator()
    PyImGui.text(f"Queued runs: {len(_queued_runs)}")
    to_remove = None
    for i, qr in enumerate(_queued_runs):
        marker = " <-- CURRENT" if i == _current_run_index and bot.config.initialized else ""
        tries = f" (tries: {_run_tries[i]})" if i < len(_run_tries) and _run_tries[i] > 0 else ""
        PyImGui.text(f"  {i + 1}. {qr.display}{marker}{tries}")
        PyImGui.same_line(0, 10)
        if PyImGui.button(f"X##{i}", 20, 20):
            to_remove = i
    if to_remove is not None:
        _queued_runs.pop(to_remove)
        _queue_version += 1

    # --- Rebuild FSM when queue changes ---
    if _queue_version != _prev_queue_version:
        bot.Stop()
        bot.config.FSM = FSM(BotSettings.BOT_NAME)
        bot.config.counters.clear_all()
        bot.config.initialized = False
        bot.UI._FSM_FILTER_START = 0
        bot.UI._FSM_FILTER_END = 0
        _prev_queue_version = _queue_version

    _draw_settings_consumables()
    #_draw_settings_debug()

def _draw_settings_consumables():
    PyImGui.separator()
    PyImGui.text("Consumables Selection")
    PyImGui.separator()

    use_birthday_cupcake = bot.Properties.Get("birthday_cupcake", "active")
    use_birthday_cupcake = PyImGui.checkbox("Restock & use Birthday Cupcake", use_birthday_cupcake)
    bot.Properties.ApplyNow("birthday_cupcake", "active", use_birthday_cupcake)

    use_war_supplies = bot.Properties.Get("war_supplies", "active")
    use_war_supplies = PyImGui.checkbox("Restock & use War Supplies", use_war_supplies)
    bot.Properties.ApplyNow("war_supplies", "active", use_war_supplies)

    use_alcohol = bot.Properties.Get("alcohol", "active")
    use_alcohol = PyImGui.checkbox("Use alcohol in inventory", use_alcohol)
    bot.Properties.ApplyNow("alcohol", "active", use_alcohol)

    use_conset = bot.Properties.Get("armor_of_salvation", "active")
    use_conset = PyImGui.checkbox("Restock & use Conset", use_conset)
    bot.Properties.ApplyNow("armor_of_salvation", "active", use_conset)
    bot.Properties.ApplyNow("essence_of_celerity", "active", use_conset)
    bot.Properties.ApplyNow("grail_of_might", "active", use_conset)

    use_honeycomb = bot.Properties.Get("honeycomb", "active")
    use_honeycomb = PyImGui.checkbox("Restock & use Honeycomb", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)

def _draw_settings_debug():
    PyImGui.separator()
    PyImGui.text("DEBUG DATA")
    PyImGui.separator()
    PyImGui.text(f"_queue_version: {_queue_version}")
    PyImGui.text(f"_current_run_index: {_current_run_index}")
    PyImGui.text(f"_queued_runs: {len(_queued_runs)}")
    PyImGui.text(f"_run_tries: {_run_tries}")
    for i, qr in enumerate(_queued_runs):
        marker = " <-- CURRENT" if i == _current_run_index else ""
        tries = _run_tries[i] if i < len(_run_tries) else 0
        PyImGui.text(f"  {i+1}. {qr.display} (outpost={qr.outpost_id}) tries={tries}{marker}")

def _draw_help():
    PyImGui.text("Equipment")
    PyImGui.bullet_text("+5e +20% enchant duration weapon")
    PyImGui.bullet_text("+45hp -2dmg while enchanted shield")
    PyImGui.bullet_text("x5 Windwalker insignias")
    PyImGui.bullet_text("+1 head +1 Mysticism Rune")
    PyImGui.bullet_text("Major Vigor Rune")
    PyImGui.bullet_text("x3 Atunnement Rune")
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()
    PyImGui.text("Developed by: Aura")
    PyImGui.text("Credits to: aC original script")
   
# endregion

# =============================================================================
# region MAIN
# =============================================================================
bot.SetMainRoutine(bot_routine)

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Skill_Icons", "[1543] - Pious Haste.jpg")
bot.UI.override_draw_config(lambda: _draw_settings())
bot.UI.override_draw_help(lambda: _draw_help())

def main():
    if not Routines.Checks.Map.MapValid() or not Player.IsPlayerLoaded():
        return
    
    bot.UI.draw_window(icon_path=TEXTURE)

    if _queued_runs:
        bot.Update()

if __name__ == "__main__":
    main()
# endregion
