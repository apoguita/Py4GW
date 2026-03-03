import os

import Py4GW
import PyImGui

from Py4GWCoreLib import Console, ConsoleLog, IniHandler, Timer
from Sources.modular_bot.prebuilts.fow import (
    FOW_QUEST_ORDER,
    ModularFowOptions,
    apply_fow_runtime_properties,
    create_modular_fow_bot,
)


BOT_NAME = "ModularFow"
SYNC_INTERVAL_MS = 1000

root_directory = Py4GW.Console.get_projects_path()
ini_file_location = os.path.join(root_directory, "Widgets", "Config", "ModularFow.ini")
ini_handler = IniHandler(ini_file_location)
sync_timer = Timer()
sync_timer.Start()


class Config:
    def __init__(self):
        self.hard_mode = ini_handler.read_bool(BOT_NAME, "hard_mode", True)
        self.use_consumables = ini_handler.read_bool(BOT_NAME, "use_consumables", True)
        self.restock_consumables = ini_handler.read_bool(BOT_NAME, "restock_consumables", True)
        self.auto_loot = ini_handler.read_bool(BOT_NAME, "auto_loot", True)
        self.debug_logging = ini_handler.read_bool(BOT_NAME, "debug_logging", False)

    def to_options(self) -> ModularFowOptions:
        return ModularFowOptions(
            hard_mode=bool(self.hard_mode),
            use_consumables=bool(self.use_consumables),
            restock_consumables=bool(self.restock_consumables),
            auto_loot=bool(self.auto_loot),
            debug_logging=bool(self.debug_logging),
        )

    def save_throttled(self):
        if not sync_timer.HasElapsed(SYNC_INTERVAL_MS):
            return

        sync_timer.Start()
        ini_handler.write_key(BOT_NAME, "hard_mode", str(bool(self.hard_mode)))
        ini_handler.write_key(BOT_NAME, "use_consumables", str(bool(self.use_consumables)))
        ini_handler.write_key(BOT_NAME, "restock_consumables", str(bool(self.restock_consumables)))
        ini_handler.write_key(BOT_NAME, "auto_loot", str(bool(self.auto_loot)))
        ini_handler.write_key(BOT_NAME, "debug_logging", str(bool(self.debug_logging)))


config = Config()
bot = None
_BOT_REBUILD_PENDING = False


def _fsm_step_name() -> str:
    if bot is None:
        return ""
    fsm = bot.bot.config.FSM
    try:
        return str(fsm.get_current_step_name() or "")
    except Exception:
        current_state = getattr(fsm, "current_state", None)
        return str(getattr(current_state, "name", "") or "")


def _phase_progress() -> tuple[int, int, str]:
    if bot is None:
        return (0, 0, "")

    current_step = _fsm_step_name()
    phases = getattr(bot, "_phases", [])
    total = len(phases)
    if total <= 0:
        return (0, 0, "")

    for idx, phase in enumerate(phases):
        header_name = bot.get_phase_header(phase.name)
        if header_name and current_step.startswith(header_name):
            return (idx + 1, total, phase.name)

    for idx, phase in enumerate(phases):
        if phase.name and phase.name in current_step:
            return (idx + 1, total, phase.name)

    return (0, total, "")


def _step_progress() -> tuple[int, int, str, str]:
    if bot is None:
        return (0, 0, "", "")

    config_obj = bot.bot.config
    step_index = int(getattr(config_obj, "modular_step_index", 0) or 0)
    step_total = int(getattr(config_obj, "modular_step_total", 0) or 0)
    recipe_title = str(getattr(config_obj, "modular_recipe_title", "") or "")
    step_title = str(getattr(config_obj, "modular_step_title", "") or "")
    return (step_index, step_total, recipe_title, step_title)


def _debug(message: str) -> None:
    if config.debug_logging:
        ConsoleLog(BOT_NAME, message, Console.MessageType.Info)


def _queue_rebuild() -> None:
    global _BOT_REBUILD_PENDING
    _BOT_REBUILD_PENDING = True
    _debug("Queued FoW bot rebuild due to idle setting change.")


def _build_bot():
    return create_modular_fow_bot(
        options=config.to_options(),
        main_ui=_draw_main,
        settings_ui=_draw_settings,
        help_ui=_draw_help,
        debug_hook=_debug,
    )


def _start_bot() -> None:
    global bot, _BOT_REBUILD_PENDING

    _debug("Start button clicked.")
    bot = _build_bot()
    if not bot.bot.config.initialized:
        _debug("Building ModularBot routine manually.")
        bot._build_routine(bot.bot)
        bot.bot.config.initialized = True
        bot.bot.SetMainRoutine(lambda *_args, **_kwargs: None)
        _debug(
            "Routine build complete. "
            f"fsm_states={len(bot.bot.config.FSM.states)} "
            f"headers={len(getattr(bot, '_phase_headers', {}))}"
        )

    apply_fow_runtime_properties(bot.bot, config.to_options(), debug_hook=_debug)
    _debug(
        "Calling bot.Start(). "
        f"initialized={bot.bot.config.initialized} "
        f"fsm_running_before={bot.bot.config.fsm_running} "
        f"fsm_states={len(bot.bot.config.FSM.states)}"
    )
    bot.bot.Start()
    _debug(
        "bot.Start() returned. "
        f"fsm_running_after={bot.bot.config.fsm_running} "
        f"current_state={getattr(bot.bot.config.FSM.current_state, 'name', None)}"
    )
    _BOT_REBUILD_PENDING = False
    _debug("Initialized and started FoW widget bot.")


def _draw_prestart_window() -> None:
    if not PyImGui.begin(BOT_NAME):
        PyImGui.end()
        return

    PyImGui.text("Fissure of Woe")
    PyImGui.separator()
    PyImGui.text("Status: Idle")
    PyImGui.text("Current: Not initialized")
    PyImGui.text(f"Quests loaded: {len(FOW_QUEST_ORDER)}")
    PyImGui.text("Route: Full run from setup to reward")

    PyImGui.separator()
    config.hard_mode = PyImGui.checkbox("Hard Mode", config.hard_mode)
    config.use_consumables = PyImGui.checkbox("Use Consumables", config.use_consumables)
    PyImGui.begin_disabled(not config.use_consumables)
    config.restock_consumables = PyImGui.checkbox("Restock Consumables", config.restock_consumables)
    PyImGui.end_disabled()
    config.auto_loot = PyImGui.checkbox("Auto Loot", config.auto_loot)
    config.debug_logging = PyImGui.checkbox("Debug Logging", config.debug_logging)

    PyImGui.separator()
    if PyImGui.button("CLICK TO START THE BOT"):
        _start_bot()
        PyImGui.end()
        return

    config.save_throttled()
    PyImGui.end()


def _draw_main() -> None:
    is_running = bool(bot.bot.config.fsm_running)
    current_step = _fsm_step_name() or "Idle"
    phase_index, phase_total, phase_name = _phase_progress()
    step_index, step_total, recipe_title, step_title = _step_progress()

    PyImGui.text("Fissure of Woe")
    PyImGui.separator()
    PyImGui.text(f"Status: {'Running' if is_running else 'Idle'}")
    if phase_total > 0 and phase_name:
        PyImGui.text(f"Phase: {phase_index}/{phase_total} - {phase_name}")
    else:
        PyImGui.text("Phase: Not started")
    if recipe_title:
        PyImGui.text(f"Recipe: {recipe_title}")
    if step_title:
        if step_total > 0:
            PyImGui.text(f"Step: {step_index}/{step_total} - {step_title}")
        else:
            PyImGui.text(f"Step: {step_title}")
    else:
        PyImGui.text("Step: Waiting")
    if phase_total > 0:
        PyImGui.text(f"Phase Progress: {phase_index}/{phase_total}")
    PyImGui.text("Route: Full run from setup to reward")
    PyImGui.text(f"Quests loaded: {len(FOW_QUEST_ORDER)}")
    PyImGui.text_wrapped(f"FSM: {current_step}")

    PyImGui.separator()
    PyImGui.begin_disabled(is_running)
    new_hard_mode = PyImGui.checkbox("Hard Mode", config.hard_mode)
    if new_hard_mode != config.hard_mode:
        config.hard_mode = new_hard_mode
        _queue_rebuild()

    new_use_consumables = PyImGui.checkbox("Use Consumables", config.use_consumables)
    if new_use_consumables != config.use_consumables:
        config.use_consumables = new_use_consumables
        _queue_rebuild()

    PyImGui.begin_disabled(not config.use_consumables)
    new_restock_consumables = PyImGui.checkbox("Restock Consumables", config.restock_consumables)
    if new_restock_consumables != config.restock_consumables:
        config.restock_consumables = new_restock_consumables
        _queue_rebuild()
    PyImGui.end_disabled()

    new_auto_loot = PyImGui.checkbox("Auto Loot", config.auto_loot)
    if new_auto_loot != config.auto_loot:
        config.auto_loot = new_auto_loot
        _queue_rebuild()
    PyImGui.end_disabled()

    config.save_throttled()


def _draw_settings() -> None:
    config.debug_logging = PyImGui.checkbox("Debug Logging", config.debug_logging)
    config.save_throttled()


def _draw_help() -> None:
    PyImGui.text("ModularFow")
    PyImGui.separator()
    PyImGui.text_wrapped("Widget wrapper for the FoW prebuilt route using the shared modular FoW builder.")
    PyImGui.bullet_text("Uses the same FoW route builder as the standalone modular bot")
    PyImGui.bullet_text("Loads quest steps from Sources/modular_bot/quests/FoW/*.json")
    PyImGui.bullet_text("Keeps widget options for hard mode, consumables, autoloot, and debug logging")
    PyImGui.bullet_text("Settings are persisted in Widgets/Config/ModularFow.ini")


def main():
    global bot, _BOT_REBUILD_PENDING

    if bot is None:
        _draw_prestart_window()
        return

    if _BOT_REBUILD_PENDING and not bot.bot.config.fsm_running:
        bot = None
        _BOT_REBUILD_PENDING = False
        _debug("FoW widget bot invalidated; it will rebuild on next start.")
        _draw_prestart_window()
        return

    _debug(
        "Tick: "
        f"fsm_running={bot.bot.config.fsm_running} "
        f"initialized={bot.bot.config.initialized} "
        f"fsm_states={len(bot.bot.config.FSM.states)} "
        f"current_state={getattr(bot.bot.config.FSM.current_state, 'name', None)}"
    )
    bot.update()


if __name__ == "__main__":
    main()
