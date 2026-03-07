import PyImGui
import Py4GW
import importlib
import tome_targets
importlib.reload(tome_targets)
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import Botting, ConsoleLog, Routines, Agent, Player, ImGui, Color, GLOBAL_CACHE
from tome_targets import ELITE_TOME_TARGETS

BOT_NAME = "Elite Tome Farmer by XLeek"
MODULE_ICON = "Textures\\Module_Icons\\Ssaresh's Kris Daggers.png"
bot = Botting(BOT_NAME)

# =========================
# BOT SETTINGS & COUNTERS
# =========================

class BotSettings:
    TOTAL_RUNS: int = 0
    FAILED_RUNS: int = 0
    TOMES_DROPPED: int = 0
    _tome_count_before: int = 0  # snapshot before the run

def _success_rate():
    if BotSettings.TOTAL_RUNS == 0:
        return "0.00%"
    successful = BotSettings.TOTAL_RUNS - BotSettings.FAILED_RUNS
    return f"{successful / BotSettings.TOTAL_RUNS * 100:.2f}%"

def _increment_run(result: str):
    BotSettings.TOTAL_RUNS += 1
    if result == "fail":
        BotSettings.FAILED_RUNS += 1

def _snapshot_tome_count(model_id: int):
    """Takes a snapshot of the tome count in inventory before the run."""
    BotSettings._tome_count_before = GLOBAL_CACHE.Inventory.GetModelCount(model_id)

def _update_tome_count(model_id: int):
    """Calculates the delta and updates the dropped tomes counter."""
    count_after = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
    delta = count_after - BotSettings._tome_count_before
    if delta > 0:
        BotSettings.TOMES_DROPPED += delta

# =========================
# UI STATE
# =========================

CLASS_LIST = list(ELITE_TOME_TARGETS.keys())
_selected_index = [0]
_farm_configured = [False]
_current_target = [None]
_chosen_class = [""]


def draw_class_selector():
    PyImGui.set_next_window_size(400, 230)
    if PyImGui.begin("Elite Tome Farmer - Configuration"):

        title_color = Color(255, 200, 100, 255)
        ImGui.push_font("Regular", 18)
        PyImGui.text_colored("Choose the class of the tome to farm", title_color.to_tuple_normalized())
        ImGui.pop_font()
        PyImGui.spacing()
        PyImGui.separator()
        PyImGui.spacing()

        new_index = PyImGui.combo("Target Class", _selected_index[0], CLASS_LIST)
        if new_index != _selected_index[0]:
            _selected_index[0] = new_index

        chosen_class = CLASS_LIST[_selected_index[0]]
        target = ELITE_TOME_TARGETS[chosen_class]

        PyImGui.spacing()

        if target["boss_name"] and target["boss_name"] != "TODO":
            PyImGui.text(f"Boss: {target['boss_name']}")
        else:
            PyImGui.text_colored(
                "Boss: Not configured",
                Color(255, 80, 80, 255).to_tuple_normalized()
            )

        if target.get("notes"):
            PyImGui.text(f"Notes: {target['notes']}")

        PyImGui.spacing()
        PyImGui.separator()
        PyImGui.spacing()

        ready = (
            target["outpost_map_id"] is not None
            and target["farm_map_id"] is not None
            and len(target["killing_path"]) > 0
        )

        if not ready:
            PyImGui.begin_disabled(True)
            PyImGui.button("Start Farming", 180, 30)
            PyImGui.end_disabled()
            PyImGui.text_colored(
                "This class is not configured yet.",
                Color(255, 150, 50, 255).to_tuple_normalized()
            )
        else:
            if PyImGui.button("Start Farming", 180, 30):
                _current_target[0] = target
                _chosen_class[0] = chosen_class
                _farm_configured[0] = True
                ConsoleLog(BOT_NAME, f"Starting farm - Elite Tome: {chosen_class}")

    PyImGui.end()


# =========================
# WIPE HANDLING
# =========================

def _on_party_wipe(bot: "Botting"):
    _increment_run("fail")
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return
    bot.States.JumpToStepName("[H]Combat_3")
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog(BOT_NAME, "Party wipe detected")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


# =========================
# MAIN ROUTINE
# =========================

def Routine(bot: Botting) -> None:
    target = _current_target[0]
    tome_model_id = target["tome_model_id"]

    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')

    bot.Templates.Multibox_Aggressive()
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=target["outpost_map_id"])
    bot.Properties.Disable("auto_inventory_management")
    bot.Party.SetHardMode(True)

    bot.States.AddHeader("Exit Outpost")

    # Snapshot before leaving the outpost
    def _pre_run_snapshot():
        _snapshot_tome_count(tome_model_id)
        yield

    bot.States.AddCustomState(lambda: _pre_run_snapshot(), "SnapshotTomeCount")

    ex = target["exit_coords"]
    bot.Move.XYAndExitMap(ex[0], ex[1], target_map_id=target["farm_map_id"])
    bot.Wait.ForMapLoad(target["farm_map_id"])
    bot.Wait.ForTime(3000)

    bot.States.AddHeader("Combat")
    bot.Move.FollowAutoPath(target["killing_path"], f"{target['boss_name']} Kill Route")
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(8000)

    bot.States.AddHeader("Resign and Return to Outpost")
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=target["outpost_map_id"])

    # Tome delta + successful run increment
    def _post_run():
        _update_tome_count(tome_model_id)
        _increment_run("success")
        yield

    bot.States.AddCustomState(lambda: _post_run(), "PostRunUpdate")
    bot.UI.PrintMessageToConsole(BOT_NAME, "Run completed - Restarting...")
    bot.States.JumpToStepName("[H]Exit Outpost_2")


bot.SetMainRoutine(Routine)


# =========================
# DRAW STATS
# =========================

def _draw_stats():
    successful = BotSettings.TOTAL_RUNS - BotSettings.FAILED_RUNS

    ImGui.push_font("Regular", 18)
    PyImGui.text("Statistics")
    ImGui.pop_font()
    PyImGui.spacing()

    if _chosen_class[0]:
        PyImGui.LabelTextV("Class", "%s", [_chosen_class[0]])

    PyImGui.spacing()

    if PyImGui.collapsing_header("Runs"):
        PyImGui.LabelTextV("Total", "%s", [str(BotSettings.TOTAL_RUNS)])

        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 1.0, 0.0, 1.0))
        PyImGui.LabelTextV("Successful", "%s", [f"{successful} ({_success_rate()})"])
        PyImGui.pop_style_color(1)

        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.0, 0.0, 1.0))
        PyImGui.LabelTextV("Failed", "%s", [str(BotSettings.FAILED_RUNS)])
        PyImGui.pop_style_color(1)

    if PyImGui.collapsing_header("Dropped Tomes"):
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.84, 0.0, 1.0))
        PyImGui.LabelTextV("Elite Tomes", "%s", [str(BotSettings.TOMES_DROPPED)])
        PyImGui.pop_style_color(1)

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    if PyImGui.button("Change Class", 180, 30):
        _farm_configured[0] = False
        _current_target[0] = None
        _chosen_class[0] = ""
        bot.Stop()
        ConsoleLog(BOT_NAME, "Class change requested - returning to selector")

bot.UI.override_draw_config(lambda: _draw_stats())


# =========================
# TOOLTIP
# =========================

def tooltip():
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Elite Tome Farmer", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text("Farm elite tomes from bosses in Hard Mode")
    PyImGui.spacing()
    PyImGui.bullet_text("Choose the target class in the interface")
    PyImGui.bullet_text("6-8 well-equipped accounts recommended")
    PyImGui.bullet_text("Hero AI widget required on all accounts")
    PyImGui.bullet_text("Launch only on the party leader")
    PyImGui.bullet_text("Created by XLeek")
    PyImGui.end_tooltip()


# =========================
# MAIN LOOP
# =========================

def main():
    if not _farm_configured[0]:
        draw_class_selector()
        return

    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()
