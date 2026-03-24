import os

import Py4GW
import PyImGui

from Py4GWCoreLib import Console, ConsoleLog, IniHandler, Party, Timer
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Sources.modular_bot.prebuilts.fow import (
    DEFAULT_FOW_COMBAT_WIDGET_KEY,
    DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY,
    DEFAULT_FOW_ENTRYPOINT_KEY,
    FOW_COMBAT_WIDGETS,
    FOW_ENTRYPOINTS,
    FOW_QUEST_ORDER,
    INVENTORY_MANAGEMENT_LOCATIONS,
    ModularFowOptions,
    apply_fow_runtime_properties,
    create_modular_fow_bot,
)

MODULE_NAME = "Modular FoW"
MODULE_ICON = "Textures/Module_Icons/Fissure of Woe.png"
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
        self.upkeep_auto_inventory_management_active = ini_handler.read_bool(
            BOT_NAME, "upkeep_auto_inventory_management_active", True
        )
        self.skip_merchant_actions = ini_handler.read_bool(BOT_NAME, "skip_merchant_actions", False)
        self.sell_non_cons_materials = ini_handler.read_bool(BOT_NAME, "sell_non_cons_materials", False)
        self.sell_all_common_materials = ini_handler.read_bool(BOT_NAME, "sell_all_common_materials", False)
        self.buy_ectoplasm = ini_handler.read_bool(BOT_NAME, "buy_ectoplasm", False)
        self.debug_logging = ini_handler.read_bool(BOT_NAME, "debug_logging", False)
        self.entrypoint = str(
            ini_handler.read_key(BOT_NAME, "entrypoint", DEFAULT_FOW_ENTRYPOINT_KEY) or DEFAULT_FOW_ENTRYPOINT_KEY
        )
        self.inventory_management_location = str(
            ini_handler.read_key(
                BOT_NAME,
                "inventory_management_location",
                DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY,
            )
            or DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY
        )
        self.post_gh_combat_widget = str(
            ini_handler.read_key(
                BOT_NAME,
                "post_gh_combat_widget",
                DEFAULT_FOW_COMBAT_WIDGET_KEY,
            )
            or DEFAULT_FOW_COMBAT_WIDGET_KEY
        )

    def to_options(self) -> ModularFowOptions:
        return ModularFowOptions(
            hard_mode=bool(self.hard_mode),
            use_consumables=bool(self.use_consumables),
            restock_consumables=bool(self.restock_consumables),
            auto_loot=bool(self.auto_loot),
            upkeep_auto_inventory_management_active=bool(self.upkeep_auto_inventory_management_active),
            skip_merchant_actions=bool(self.skip_merchant_actions),
            sell_non_cons_materials=bool(self.sell_non_cons_materials),
            sell_all_common_materials=bool(self.sell_all_common_materials),
            buy_ectoplasm=bool(self.buy_ectoplasm),
            debug_logging=bool(self.debug_logging),
            entrypoint=self.entrypoint,
            inventory_management_location=self.inventory_management_location,
            post_gh_combat_widget=self.post_gh_combat_widget,
        )

    def save_throttled(self):
        if not sync_timer.HasElapsed(SYNC_INTERVAL_MS):
            return

        sync_timer.Start()
        ini_handler.write_key(BOT_NAME, "hard_mode", str(bool(self.hard_mode)))
        ini_handler.write_key(BOT_NAME, "use_consumables", str(bool(self.use_consumables)))
        ini_handler.write_key(BOT_NAME, "restock_consumables", str(bool(self.restock_consumables)))
        ini_handler.write_key(BOT_NAME, "auto_loot", str(bool(self.auto_loot)))
        ini_handler.write_key(
            BOT_NAME,
            "upkeep_auto_inventory_management_active",
            str(bool(self.upkeep_auto_inventory_management_active)),
        )
        ini_handler.write_key(BOT_NAME, "skip_merchant_actions", str(bool(self.skip_merchant_actions)))
        ini_handler.write_key(BOT_NAME, "sell_non_cons_materials", str(bool(self.sell_non_cons_materials)))
        ini_handler.write_key(BOT_NAME, "sell_all_common_materials", str(bool(self.sell_all_common_materials)))
        ini_handler.write_key(BOT_NAME, "buy_ectoplasm", str(bool(self.buy_ectoplasm)))
        ini_handler.write_key(BOT_NAME, "debug_logging", str(bool(self.debug_logging)))
        ini_handler.write_key(BOT_NAME, "entrypoint", str(self.entrypoint))
        ini_handler.write_key(BOT_NAME, "inventory_management_location", str(self.inventory_management_location))
        ini_handler.write_key(BOT_NAME, "post_gh_combat_widget", str(self.post_gh_combat_widget))


config = Config()
bot = None
_BOT_REBUILD_PENDING = False
ENTRYPOINT_KEYS = list(FOW_ENTRYPOINTS.keys())
ENTRYPOINT_LABELS = [label for label, _map_id in FOW_ENTRYPOINTS.values()]
INVENTORY_LOCATION_KEYS = list(INVENTORY_MANAGEMENT_LOCATIONS.keys())
INVENTORY_LOCATION_LABELS = [INVENTORY_MANAGEMENT_LOCATIONS[key] for key in INVENTORY_LOCATION_KEYS]
COMBAT_WIDGET_KEYS = list(FOW_COMBAT_WIDGETS.keys())
COMBAT_WIDGET_LABELS = [FOW_COMBAT_WIDGETS[key] for key in COMBAT_WIDGET_KEYS]


def _entrypoint_index() -> int:
    try:
        return ENTRYPOINT_KEYS.index(config.entrypoint)
    except ValueError:
        return 0


def _draw_entrypoint_combo(disabled: bool = False) -> None:
    if disabled:
        PyImGui.begin_disabled(True)
    PyImGui.text("FoW Entrypoint")
    PyImGui.push_item_width(PyImGui.get_content_region_avail()[0])
    selected_index = PyImGui.combo("##FoWEntrypoint", _entrypoint_index(), ENTRYPOINT_LABELS)
    PyImGui.pop_item_width()
    if 0 <= selected_index < len(ENTRYPOINT_KEYS):
        new_entrypoint = ENTRYPOINT_KEYS[selected_index]
        if new_entrypoint != config.entrypoint:
            config.entrypoint = new_entrypoint
            if bot is not None:
                _queue_rebuild()
    if disabled:
        PyImGui.end_disabled()


def _inventory_location_index() -> int:
    try:
        return INVENTORY_LOCATION_KEYS.index(config.inventory_management_location)
    except ValueError:
        return 0


def _draw_inventory_location_combo(disabled: bool = False) -> None:
    if disabled:
        PyImGui.begin_disabled(True)
    PyImGui.text("Inventory Management Location")
    PyImGui.push_item_width(PyImGui.get_content_region_avail()[0])
    selected_index = PyImGui.combo(
        "##FoWInventoryManagementLocation",
        _inventory_location_index(),
        INVENTORY_LOCATION_LABELS,
    )
    PyImGui.pop_item_width()
    if 0 <= selected_index < len(INVENTORY_LOCATION_KEYS):
        new_location = INVENTORY_LOCATION_KEYS[selected_index]
        if new_location != config.inventory_management_location:
            config.inventory_management_location = new_location
            if bot is not None:
                _queue_rebuild()
    if disabled:
        PyImGui.end_disabled()


def _combat_widget_index() -> int:
    try:
        return COMBAT_WIDGET_KEYS.index(config.post_gh_combat_widget)
    except ValueError:
        return 0


def _draw_combat_widget_combo(disabled: bool = False) -> None:
    if disabled:
        PyImGui.begin_disabled(True)
    PyImGui.text("Combat Engine")
    PyImGui.push_item_width(PyImGui.get_content_region_avail()[0])
    selected_index = PyImGui.combo(
        "##FoWPostGhCombatWidget",
        _combat_widget_index(),
        COMBAT_WIDGET_LABELS,
    )
    PyImGui.pop_item_width()
    if 0 <= selected_index < len(COMBAT_WIDGET_KEYS):
        new_widget = COMBAT_WIDGET_KEYS[selected_index]
        if new_widget != config.post_gh_combat_widget:
            config.post_gh_combat_widget = new_widget
            if bot is not None:
                _queue_rebuild()
    if disabled:
        PyImGui.end_disabled()


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
    _debug("Queued FoW bot rebuild due to idle setting change.")


def _build_bot():
    return create_modular_fow_bot(
        options=config.to_options(),
        main_ui=_draw_main,
        settings_ui=_draw_settings,
        help_ui=_draw_help,
        debug_hook=_debug,
    )


def _ensure_party_safety_callbacks_runtime() -> None:
    """
    Re-apply party safety callbacks at runtime for FoW runs.
    This is idempotent and ensures callbacks stay wired in HeroAI mode.
    """
    if bot is None:
        return
    try:
        bot.bot.Events.OnPartyMemberBehindCallback(
            lambda: bot.bot.Templates.Routines.OnPartyMemberBehind()
        )
        bot.bot.Events.OnPartyMemberInDangerCallback(
            lambda: bot.bot.Templates.Routines.OnPartyMemberInDanger()
        )
        bot.bot.Events.OnPartyMemberDeadBehindCallback(
            lambda: bot.bot.Templates.Routines.OnPartyMemberDeathBehind()
        )
        behind_cb = bool(getattr(bot.bot.config.events.on_party_member_behind, "callback", None))
        danger_cb = bool(getattr(bot.bot.config.events.on_party_member_in_danger, "callback", None))
        dead_behind_cb = bool(getattr(bot.bot.config.events.on_party_member_dead_behind, "callback", None))
        _debug(
            "FoW safety callbacks armed "
            f"(behind={behind_cb}, in_danger={danger_cb}, dead_behind={dead_behind_cb})"
        )
    except Exception as exc:
        _debug(f"Failed to arm FoW safety callbacks: {exc}")


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
    _ensure_party_safety_callbacks_runtime()
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
    PyImGui.set_next_window_size((500, 460), PyImGui.ImGuiCond.FirstUseEver)
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
    config.upkeep_auto_inventory_management_active = PyImGui.checkbox(
        "Auto Inventory Management",
        config.upkeep_auto_inventory_management_active,
    )
    config.skip_merchant_actions = PyImGui.checkbox("Skip Merchant Actions", config.skip_merchant_actions)
    PyImGui.text("Material Handling")
    PyImGui.begin_disabled(config.skip_merchant_actions)
    config.sell_non_cons_materials = PyImGui.checkbox("Sell Non-Cons Materials", config.sell_non_cons_materials)
    config.sell_all_common_materials = PyImGui.checkbox("Sell All Common Materials", config.sell_all_common_materials)
    config.buy_ectoplasm = PyImGui.checkbox("Buy Ectoplasm", config.buy_ectoplasm)
    _draw_inventory_location_combo(disabled=config.skip_merchant_actions)
    _draw_combat_widget_combo(disabled=config.skip_merchant_actions)
    PyImGui.end_disabled()
    _draw_entrypoint_combo()
    config.debug_logging = PyImGui.checkbox("Debug Logging", config.debug_logging)

    PyImGui.separator()
    if PyImGui.button("CLICK TO START THE BOT"):
        _start_bot()
        PyImGui.end()
        return

    config.save_throttled()
    PyImGui.end()


def _draw_main() -> None:
    is_running = bool(bot.bot.config.fsm_running) if bot is not None else False
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
    new_auto_inventory_management = PyImGui.checkbox(
        "Auto Inventory Management",
        config.upkeep_auto_inventory_management_active,
    )
    if new_auto_inventory_management != config.upkeep_auto_inventory_management_active:
        config.upkeep_auto_inventory_management_active = new_auto_inventory_management
        _queue_rebuild()
    new_skip_merchant_actions = PyImGui.checkbox("Skip Merchant Actions", config.skip_merchant_actions)
    if new_skip_merchant_actions != config.skip_merchant_actions:
        config.skip_merchant_actions = new_skip_merchant_actions
        _queue_rebuild()
    PyImGui.begin_disabled(config.skip_merchant_actions)
    new_sell_non_cons_materials = PyImGui.checkbox("Sell Non-Cons Materials", config.sell_non_cons_materials)
    if new_sell_non_cons_materials != config.sell_non_cons_materials:
        config.sell_non_cons_materials = new_sell_non_cons_materials
        _queue_rebuild()
    new_sell_all_common_materials = PyImGui.checkbox("Sell All Common Materials", config.sell_all_common_materials)
    if new_sell_all_common_materials != config.sell_all_common_materials:
        config.sell_all_common_materials = new_sell_all_common_materials
        _queue_rebuild()
    new_buy_ectoplasm = PyImGui.checkbox("Buy Ectoplasm", config.buy_ectoplasm)
    if new_buy_ectoplasm != config.buy_ectoplasm:
        config.buy_ectoplasm = new_buy_ectoplasm
        _queue_rebuild()
    _draw_inventory_location_combo(disabled=is_running or config.skip_merchant_actions)
    _draw_combat_widget_combo(disabled=is_running or config.skip_merchant_actions)
    PyImGui.end_disabled()
    _draw_entrypoint_combo(disabled=is_running)
    PyImGui.end_disabled()

    config.save_throttled()


def _draw_settings() -> None:
    is_running = bool(bot is not None and bot.bot.config.fsm_running)
    PyImGui.begin_disabled(is_running)
    new_auto_inventory_management = PyImGui.checkbox(
        "Auto Inventory Management",
        config.upkeep_auto_inventory_management_active,
    )
    if new_auto_inventory_management != config.upkeep_auto_inventory_management_active:
        config.upkeep_auto_inventory_management_active = new_auto_inventory_management
        _queue_rebuild()
    new_skip_merchant_actions = PyImGui.checkbox("Skip Merchant Actions", config.skip_merchant_actions)
    if new_skip_merchant_actions != config.skip_merchant_actions:
        config.skip_merchant_actions = new_skip_merchant_actions
        _queue_rebuild()
    _draw_inventory_location_combo(disabled=bool(bot is not None and bot.bot.config.fsm_running) or config.skip_merchant_actions)
    _draw_entrypoint_combo(disabled=bool(bot is not None and bot.bot.config.fsm_running))
    PyImGui.begin_disabled(config.skip_merchant_actions)
    _draw_combat_widget_combo(disabled=is_running or config.skip_merchant_actions)
    new_sell_non_cons_materials = PyImGui.checkbox("Sell Non-Cons Materials", config.sell_non_cons_materials)
    if new_sell_non_cons_materials != config.sell_non_cons_materials:
        config.sell_non_cons_materials = new_sell_non_cons_materials
        _queue_rebuild()
    new_sell_all_common_materials = PyImGui.checkbox("Sell All Common Materials", config.sell_all_common_materials)
    if new_sell_all_common_materials != config.sell_all_common_materials:
        config.sell_all_common_materials = new_sell_all_common_materials
        _queue_rebuild()
    new_buy_ectoplasm = PyImGui.checkbox("Buy Ectoplasm", config.buy_ectoplasm)
    if new_buy_ectoplasm != config.buy_ectoplasm:
        config.buy_ectoplasm = new_buy_ectoplasm
        _queue_rebuild()
    PyImGui.end_disabled()
    PyImGui.end_disabled()
    config.debug_logging = PyImGui.checkbox("Debug Logging", config.debug_logging)
    config.save_throttled()


def _draw_help() -> None:
    PyImGui.text("ModularFow")
    PyImGui.separator()
    PyImGui.text_wrapped("Widget wrapper for the FoW prebuilt route using the shared modular FoW builder.")
    PyImGui.bullet_text("Uses the same FoW route builder as the standalone modular bot")
    PyImGui.bullet_text("Loads quest steps from Sources/modular_bot/quests/FoW/*.json")
    PyImGui.bullet_text("Supports inventory management in Guild Hall or Eye of the North")
    PyImGui.bullet_text("Optional skip for all merchant/inventory management setup actions")
    PyImGui.bullet_text("Optional material selling before entry at the selected inventory location")
    PyImGui.bullet_text("Optional ectoplasm buying from current character gold only")
    PyImGui.bullet_text("Groups on the selected FoW entrypoint map before scrolling in")
    PyImGui.bullet_text("Supports FoW entry from Zin Ku Corridor, Chantry of Secrets, Temple of the Ages, or Embark Beach")
    PyImGui.bullet_text("Keeps widget options for hard mode, consumables, autoloot, and debug logging")
    PyImGui.bullet_text("Settings are persisted in Widgets/Config/ModularFow.ini")


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
        _debug("FoW widget bot invalidated; it will rebuild on next start.")
        _draw_prestart_window()
        return

    bot.update()


def tooltip():
    PyImGui.set_next_window_size((400, 0))
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.image(MODULE_ICON, (32, 32))
    PyImGui.same_line(0, 10)
    ImGui.push_font("Regular", 20)
    ImGui.text_aligned(MODULE_NAME, alignment=Alignment.MidLeft, color=title_color.color_tuple, height=32)
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text_wrapped("Modular FoW is a widget that integrates the modular FoW bot routine into a Py4GW widget, allowing you to run the FoW route with customizable options and real-time status display directly from the widget interface.")
    
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Yods")

    PyImGui.end_tooltip()

if __name__ == "__main__":
    main()
