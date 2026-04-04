import os

import Py4GW
import PyImGui

from Py4GWCoreLib import Console, ConsoleLog, IniHandler, Party, Timer
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Sources.modular_bot.hero_setup import (
    draw_setup_tab,
    draw_team_configuration_window,
    toggle_team_configuration_window,
)
from Sources.modular_bot.prebuilts.nightfall_campaign import (
    NIGHTFALL_PHASE_SPECS,
    NIGHTFALL_REGION_SPANS,
    NightfallCampaignOptions,
    create_nightfall_campaign_bot,
)

MODULE_NAME = "Nightfall Campaign"
MODULE_ICON = "Textures/Module_Icons/Nightfall.png"
BOT_NAME = "NightfallCampaign"
SYNC_INTERVAL_MS = 1000

root_directory = Py4GW.Console.get_projects_path()
ini_file_location = os.path.join(root_directory, "Widgets", "Config", "NightfallCampaign.ini")
ini_handler = IniHandler(ini_file_location)
sync_timer = Timer()
sync_timer.Start()


class Config:
    def __init__(self):
        self.start_phase_index = max(0, int(ini_handler.read_int(BOT_NAME, "start_phase_index", 0) or 0))
        self.loop = bool(ini_handler.read_bool(BOT_NAME, "loop", False))
        self.show_all_regions = bool(ini_handler.read_bool(BOT_NAME, "show_all_regions", False))
        self.debug_logging = bool(ini_handler.read_bool(BOT_NAME, "debug_logging", False))

    def to_options(self) -> NightfallCampaignOptions:
        return NightfallCampaignOptions(
            start_phase_index=int(self.start_phase_index),
            loop=bool(self.loop),
            team_selection="priority",
        )

    def save_throttled(self):
        if not sync_timer.HasElapsed(SYNC_INTERVAL_MS):
            return
        sync_timer.Start()
        ini_handler.write_key(BOT_NAME, "start_phase_index", str(int(self.start_phase_index)))
        ini_handler.write_key(BOT_NAME, "loop", str(bool(self.loop)))
        ini_handler.write_key(BOT_NAME, "show_all_regions", str(bool(self.show_all_regions)))
        ini_handler.write_key(BOT_NAME, "debug_logging", str(bool(self.debug_logging)))


config = Config()
bot = None
_BOT_REBUILD_PENDING = False
_open_region_name: str | None = None
_regions_initialized = False


def _debug(message: str) -> None:
    if config.debug_logging:
        ConsoleLog(BOT_NAME, message, Console.MessageType.Info)


def _should_show_widget() -> bool:
    try:
        if not Party.IsPartyLoaded():
            return True
        if Party.GetPlayerCount() <= 1:
            return True
        return bool(Party.IsPartyLeader())
    except Exception:
        return True


def _queue_rebuild() -> None:
    global _BOT_REBUILD_PENDING
    _BOT_REBUILD_PENDING = True
    _debug("Queued Nightfall Campaign bot rebuild due to setting change.")


def _build_bot():
    return create_nightfall_campaign_bot(
        options=config.to_options(),
        main_ui=_draw_main,
        settings_ui=_draw_settings,
        help_ui=_draw_help,
        name="Nightfall Campaign",
    )


def _phase_title(index: int) -> str:
    if bot is None:
        return f"Phase {index + 1}"
    if 0 <= index < len(bot._phases):
        return bot._phases[index].name
    return f"Phase {index + 1}"


def _phase_summary() -> tuple[int, int, float]:
    total = len(NIGHTFALL_PHASE_SPECS)
    remaining = max(0, total - int(config.start_phase_index))
    skipped_pct = 0.0 if total == 0 else (int(config.start_phase_index) / total) * 100.0
    return total, remaining, skipped_pct


def _fsm_step_name() -> str:
    if bot is None:
        return ""
    fsm = bot.bot.config.FSM
    try:
        return str(fsm.get_current_step_name() or "")
    except Exception:
        current_state = getattr(fsm, "current_state", None)
        return str(getattr(current_state, "name", "") or "")


def _detect_current_phase_index() -> int | None:
    if bot is None:
        return None
    current_step = _fsm_step_name()
    for idx, phase in enumerate(bot._phases):
        header_name = bot.get_phase_header(phase.name)
        if header_name and current_step.startswith(header_name):
            return idx
    for idx, phase in enumerate(bot._phases):
        if phase.name and phase.name in current_step:
            return idx
    return None


def _draw_current_activity() -> None:
    current_phase_idx = _detect_current_phase_index()
    current_step = _fsm_step_name() or "FSM not initialized"
    PyImGui.text("Current Activity")
    PyImGui.separator()
    if current_phase_idx is None:
        PyImGui.text_colored("Phase: Not detected yet", (0.85, 0.7, 0.35, 1.0))
    else:
        spec = NIGHTFALL_PHASE_SPECS[current_phase_idx]
        PyImGui.text_colored(
            f"Phase {current_phase_idx + 1:02d}: {spec[1].title()} - {spec[3]}",
            (0.95, 0.85, 0.35, 1.0),
        )
    PyImGui.text_wrapped(f"FSM Step: {current_step}")


def _set_start_phase_index(index: int) -> None:
    total = len(NIGHTFALL_PHASE_SPECS)
    if total <= 0:
        config.start_phase_index = 0
    else:
        config.start_phase_index = max(0, min(int(index), total - 1))
    if bot is not None and not bot.bot.config.fsm_running:
        _queue_rebuild()


def _start_bot() -> None:
    global bot, _BOT_REBUILD_PENDING
    bot = _build_bot()
    if not bot.bot.config.initialized:
        bot._build_routine(bot.bot)
        bot.bot.config.initialized = True
        bot.bot.SetMainRoutine(lambda *_args, **_kwargs: None)
    bot.bot.Start()
    _BOT_REBUILD_PENDING = False
    _debug("Initialized and started Nightfall Campaign widget bot.")


def _draw_prestart_window() -> None:
    global _open_region_name, _regions_initialized

    PyImGui.set_next_window_size((640, 860), PyImGui.ImGuiCond.FirstUseEver)
    if not PyImGui.begin(BOT_NAME):
        PyImGui.end()
        return

    total_phases, remaining, skipped_pct = _phase_summary()
    PyImGui.text("Nightfall Campaign")
    PyImGui.text(f"Phases: {total_phases} | Remaining from start: {remaining}")
    PyImGui.text(f"Skipped: {config.start_phase_index} ({skipped_pct:.1f}%)")
    PyImGui.separator()

    config.loop = PyImGui.checkbox("Loop Campaign", config.loop)
    PyImGui.text_colored("Team Selection: PRIORITY settings are used.", (0.95, 0.85, 0.35, 1.0))
    if PyImGui.button("Configure Teams / Templates"):
        toggle_team_configuration_window("nightfall_campaign")

    PyImGui.separator()
    if (not _regions_initialized) and _open_region_name is None:
        for span_name, span_start, span_end in NIGHTFALL_REGION_SPANS:
            if span_start <= int(config.start_phase_index) <= span_end:
                _open_region_name = span_name
                break
        if _open_region_name is None and NIGHTFALL_REGION_SPANS:
            _open_region_name = NIGHTFALL_REGION_SPANS[0][0]
        _regions_initialized = True

    for span_name, span_start, span_end in NIGHTFALL_REGION_SPANS:
        region_total = span_end - span_start + 1
        region_remaining = max(0, span_end - int(config.start_phase_index) + 1) if int(config.start_phase_index) <= span_end else 0
        is_open = str(_open_region_name or "") == str(span_name)
        header_label = f"{'[-]' if is_open else '[+]'} {span_name} ({region_remaining}/{region_total})###{span_name}"
        if PyImGui.button(header_label):
            _open_region_name = None if is_open else str(span_name)
            is_open = str(_open_region_name or "") == str(span_name)
        open_region = is_open
        if not open_region:
            continue

        if PyImGui.button(f"Start here##{span_name}"):
            _set_start_phase_index(span_start)
        PyImGui.same_line(0, -1)
        PyImGui.text(f"Range: {span_start + 1:02d}-{span_end + 1:02d}")

        for idx_step in range(span_start, span_end + 1):
            selected = idx_step == int(config.start_phase_index)
            enabled = idx_step >= int(config.start_phase_index)
            changed = PyImGui.checkbox(f"##phase_start_{idx_step}", enabled)
            PyImGui.same_line(0, -1)
            label = f"{idx_step + 1:02d}. {NIGHTFALL_PHASE_SPECS[idx_step][1].title()}: {NIGHTFALL_PHASE_SPECS[idx_step][3]}"
            if selected:
                PyImGui.text_colored(label, (0.95, 0.85, 0.35, 1.0))
            elif enabled:
                PyImGui.text(label)
            else:
                PyImGui.text_colored(label, (0.55, 0.55, 0.55, 1.0))
            if changed != enabled:
                _set_start_phase_index(idx_step)

    PyImGui.separator()
    PyImGui.text(f"Start from: {int(config.start_phase_index) + 1:02d}. {_phase_title(int(config.start_phase_index))}")

    if PyImGui.button("CLICK TO START THE BOT"):
        _start_bot()
        PyImGui.end()
        return

    config.save_throttled()
    PyImGui.end()
    draw_team_configuration_window(ui_id="nightfall_campaign", title="Nightfall Campaign Team Setup")


def _draw_main() -> None:
    is_running = bool(bot is not None and bot.bot.config.fsm_running)
    PyImGui.text("Nightfall Campaign")
    PyImGui.separator()
    PyImGui.text(f"Status: {'Running' if is_running else 'Idle'}")
    _draw_current_activity()
    PyImGui.separator()
    if PyImGui.button("Configure Teams / Templates##main"):
        toggle_team_configuration_window("nightfall_campaign")
    PyImGui.text(f"Start index: {int(config.start_phase_index) + 1:02d}")
    PyImGui.text(f"Loop: {'On' if config.loop else 'Off'}")
    PyImGui.text("Team selection: priority")
    config.save_throttled()
    draw_team_configuration_window(ui_id="nightfall_campaign", title="Nightfall Campaign Team Setup")


def _draw_settings() -> None:
    draw_setup_tab()


def _draw_help() -> None:
    PyImGui.text("Nightfall Campaign")
    PyImGui.separator()
    PyImGui.text_wrapped("Widget wrapper for the Nightfall campaign prebuilt (missions + primary quests).")
    PyImGui.bullet_text("Select a campaign start point by region or step")
    PyImGui.bullet_text("Uses Sources/modular_bot/prebuilts/nightfall_campaign.py")
    PyImGui.bullet_text("Nightfall campaign always uses priority team settings")
    PyImGui.bullet_text("Hero team setup is available in Settings")
    PyImGui.bullet_text("Widget settings are persisted in Widgets/Config/NightfallCampaign.ini")


def main():
    global bot, _BOT_REBUILD_PENDING
    if not _should_show_widget():
        return

    if bot is None:
        _draw_prestart_window()
        return

    if _BOT_REBUILD_PENDING and not bot.bot.config.fsm_running:
        bot = None
        _BOT_REBUILD_PENDING = False
        _draw_prestart_window()
        return

    bot.update()


def tooltip():
    PyImGui.set_next_window_size((400, 0))
    PyImGui.begin_tooltip()

    title_color = Color(255, 200, 100, 255)
    ImGui.image(MODULE_ICON, (32, 32))
    PyImGui.same_line(0, 10)
    ImGui.push_font("Regular", 20)
    ImGui.text_aligned(MODULE_NAME, alignment=Alignment.MidLeft, color=title_color.color_tuple, height=32)
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text_wrapped(
        "Nightfall Campaign runs the modular Nightfall mission + primary-quest sequence with region-based start selection."
    )
    PyImGui.end_tooltip()


if __name__ == "__main__":
    main()
