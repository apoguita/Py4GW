import os

import Py4GW
import PyImGui

from Py4GWCoreLib import Console, ConsoleLog, IniHandler, Party, Player, Timer
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Sources.modular_data.prebuilt.fow import (
    DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY,
    DEFAULT_FOW_ENTRYPOINT_KEY,
    FOW_ENTRYPOINTS,
    FOW_QUEST_ORDER,
    INVENTORY_MANAGEMENT_LOCATIONS,
    ModularFowOptions,
    apply_fow_runtime_properties,
    create_modular_fow_bot,
)
from Py4GWCoreLib.modular.widget_runtime import guarded_widget_main, start_widget_bot

MODULE_NAME = "Modular FoW"
MODULE_ICON = "Textures/Module_Icons/Fissure of Woe.png"
MODULE_TAGS = ["Automation", "modular_bot"]
BOT_NAME = "ModularFow"
SYNC_INTERVAL_MS = 1000
DEFAULT_FOW_ENTRY_METHOD_KEY = "scroll"
FOW_ENTRY_METHODS = {
    "scroll": "Use FoW Scroll",
    "kneel": "Temple of the Ages (/kneel)",
}

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
        self.use_merchant_rules_inventory = ini_handler.read_bool(BOT_NAME, "use_merchant_rules_inventory", False)
        self.sell_non_cons_materials = ini_handler.read_bool(BOT_NAME, "sell_non_cons_materials", False)
        self.sell_all_common_materials = ini_handler.read_bool(BOT_NAME, "sell_all_common_materials", False)
        self.buy_ectoplasm = ini_handler.read_bool(BOT_NAME, "buy_ectoplasm", False)
        self.debug_logging = ini_handler.read_bool(BOT_NAME, "debug_logging", False)
        self.entrypoint = str(
            ini_handler.read_key(BOT_NAME, "entrypoint", DEFAULT_FOW_ENTRYPOINT_KEY) or DEFAULT_FOW_ENTRYPOINT_KEY
        )
        self.entry_method = str(
            ini_handler.read_key(BOT_NAME, "entry_method", DEFAULT_FOW_ENTRY_METHOD_KEY) or DEFAULT_FOW_ENTRY_METHOD_KEY
        )
        self.inventory_management_location = str(
            ini_handler.read_key(
                BOT_NAME,
                "inventory_management_location",
                DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY,
            )
            or DEFAULT_INVENTORY_MANAGEMENT_LOCATION_KEY
        )

    def to_options(self) -> ModularFowOptions:
        return ModularFowOptions(
            hard_mode=bool(self.hard_mode),
            use_consumables=bool(self.use_consumables),
            restock_consumables=bool(self.restock_consumables),
            auto_loot=bool(self.auto_loot),
            upkeep_auto_inventory_management_active=bool(self.upkeep_auto_inventory_management_active),
            skip_merchant_actions=bool(self.skip_merchant_actions),
            use_merchant_rules_inventory=bool(self.use_merchant_rules_inventory),
            sell_non_cons_materials=bool(self.sell_non_cons_materials),
            sell_all_common_materials=bool(self.sell_all_common_materials),
            buy_ectoplasm=bool(self.buy_ectoplasm),
            debug_logging=bool(self.debug_logging),
            entrypoint=self.entrypoint,
            entry_method=self.entry_method,
            inventory_management_location=self.inventory_management_location,
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
        ini_handler.write_key(BOT_NAME, "use_merchant_rules_inventory", str(bool(self.use_merchant_rules_inventory)))
        ini_handler.write_key(BOT_NAME, "sell_non_cons_materials", str(bool(self.sell_non_cons_materials)))
        ini_handler.write_key(BOT_NAME, "sell_all_common_materials", str(bool(self.sell_all_common_materials)))
        ini_handler.write_key(BOT_NAME, "buy_ectoplasm", str(bool(self.buy_ectoplasm)))
        ini_handler.write_key(BOT_NAME, "debug_logging", str(bool(self.debug_logging)))
        ini_handler.write_key(BOT_NAME, "entrypoint", str(self.entrypoint))
        ini_handler.write_key(BOT_NAME, "entry_method", str(self.entry_method))
        ini_handler.write_key(BOT_NAME, "inventory_management_location", str(self.inventory_management_location))


config = Config()
bot = None
_BOT_REBUILD_PENDING = False
ENTRYPOINT_KEYS = list(FOW_ENTRYPOINTS.keys())
ENTRYPOINT_LABELS = [label for label, _map_id in FOW_ENTRYPOINTS.values()]
ENTRY_METHOD_KEYS = list(FOW_ENTRY_METHODS.keys())
ENTRY_METHOD_LABELS = [FOW_ENTRY_METHODS[key] for key in ENTRY_METHOD_KEYS]
INVENTORY_LOCATION_KEYS = list(INVENTORY_MANAGEMENT_LOCATIONS.keys())
INVENTORY_LOCATION_LABELS = [INVENTORY_MANAGEMENT_LOCATIONS[key] for key in INVENTORY_LOCATION_KEYS]


def _entrypoint_index() -> int:
    try:
        return ENTRYPOINT_KEYS.index(config.entrypoint)
    except ValueError:
        return 0


def _entry_method_index() -> int:
    try:
        return ENTRY_METHOD_KEYS.index(config.entry_method)
    except ValueError:
        return 0


def _uses_temple_kneel_entry() -> bool:
    return str(config.entry_method).strip().lower() == "kneel"


def _draw_entry_method_combo(disabled: bool = False) -> None:
    if disabled:
        PyImGui.begin_disabled(True)
    PyImGui.text("FoW Entry Method")
    PyImGui.push_item_width(PyImGui.get_content_region_avail()[0])
    selected_index = PyImGui.combo("##FoWEntryMethod", _entry_method_index(), ENTRY_METHOD_LABELS)
    PyImGui.pop_item_width()
    if 0 <= selected_index < len(ENTRY_METHOD_KEYS):
        new_entry_method = ENTRY_METHOD_KEYS[selected_index]
        if new_entry_method != config.entry_method:
            config.entry_method = new_entry_method
            if bot is not None:
                _queue_rebuild()
    if disabled:
        PyImGui.end_disabled()


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


def _fsm_step_name() -> str:
    if bot is None:
        return ""
    return str(bot.get_current_step_name() or "")


def _phase_progress() -> tuple[int, int, str]:
    if bot is None:
        return (0, 0, "")
    return bot.get_phase_progress()


def _step_progress() -> tuple[int, int, str, str]:
    if bot is None:
        return (0, 0, "", "")
    return bot.get_step_progress()


def _debug(message: str) -> None:
    if config.debug_logging:
        ConsoleLog(BOT_NAME, message, Console.MessageType.Info)


def _is_current_party_leader() -> bool:
    try:
        if not Party.IsPartyLoaded():
            return True
        if Party.GetPlayerCount() <= 1:
            return True
        return int(Party.GetPartyLeaderID()) == int(Player.GetAgentID())
    except Exception:
        try:
            return bool(Party.IsPartyLeader())
        except Exception:
            return True


def _should_show_widget() -> bool:
    try:
        if bot is not None:
            return True
        if not Party.IsPartyLoaded():
            return True
        if Party.GetPlayerCount() <= 1:
            return True
        return _is_current_party_leader()
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


def _start_bot() -> None:
    global bot, _BOT_REBUILD_PENDING

    def _post_build(new_bot) -> None:
        apply_fow_runtime_properties(new_bot.bot, config.to_options(), debug_hook=_debug)

    _debug("Start button clicked.")
    started_bot = start_widget_bot(BOT_NAME, _build_bot, post_build_fn=_post_build)
    if started_bot is None:
        _BOT_REBUILD_PENDING = False
        return
    bot = started_bot
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
    config.use_merchant_rules_inventory = PyImGui.checkbox(
        "Use MerchantRules For Merchanting",
        config.use_merchant_rules_inventory,
    )
    if config.use_merchant_rules_inventory:
        PyImGui.text_wrapped("FoW merchant stage will call MerchantRules Execute (leader + alts). Sell/buy options below are ignored in this mode.")
    PyImGui.text("Material Handling")
    PyImGui.begin_disabled(config.skip_merchant_actions)
    PyImGui.begin_disabled(config.use_merchant_rules_inventory)
    config.sell_non_cons_materials = PyImGui.checkbox("Sell Non-Cons Materials", config.sell_non_cons_materials)
    config.sell_all_common_materials = PyImGui.checkbox("Sell All Common Materials", config.sell_all_common_materials)
    config.buy_ectoplasm = PyImGui.checkbox("Buy Ectoplasm", config.buy_ectoplasm)
    PyImGui.end_disabled()
    _draw_inventory_location_combo(disabled=False)
    PyImGui.end_disabled()
    _draw_entry_method_combo()
    _draw_entrypoint_combo(disabled=_uses_temple_kneel_entry())
    if _uses_temple_kneel_entry():
        PyImGui.text_wrapped("Temple of the Ages is used automatically when /kneel entry is selected.")
    config.debug_logging = PyImGui.checkbox("Debug Logging", config.debug_logging)

    PyImGui.separator()
    if PyImGui.button("CLICK TO START THE BOT"):
        _start_bot()
        PyImGui.end()
        return

    config.save_throttled()
    PyImGui.end()


def _draw_main() -> None:
    is_running = bool(bot is not None and bot.is_running())
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
    new_use_merchant_rules_inventory = PyImGui.checkbox(
        "Use MerchantRules For Merchanting",
        config.use_merchant_rules_inventory,
    )
    if new_use_merchant_rules_inventory != config.use_merchant_rules_inventory:
        config.use_merchant_rules_inventory = new_use_merchant_rules_inventory
        _queue_rebuild()
    if config.use_merchant_rules_inventory:
        PyImGui.text_wrapped("FoW merchant stage will call MerchantRules Execute (leader + alts). Sell/buy options below are ignored in this mode.")
    PyImGui.begin_disabled(config.skip_merchant_actions)
    PyImGui.begin_disabled(config.use_merchant_rules_inventory)
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
    _draw_inventory_location_combo(disabled=is_running)
    PyImGui.end_disabled()
    _draw_entry_method_combo(disabled=is_running)
    _draw_entrypoint_combo(disabled=is_running or _uses_temple_kneel_entry())
    if _uses_temple_kneel_entry():
        PyImGui.text_wrapped("Temple of the Ages is used automatically when /kneel entry is selected.")
    PyImGui.end_disabled()

    config.save_throttled()


def _draw_settings() -> None:
    is_running = bool(bot is not None and bot.is_running())
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
    new_use_merchant_rules_inventory = PyImGui.checkbox(
        "Use MerchantRules For Merchanting",
        config.use_merchant_rules_inventory,
    )
    if new_use_merchant_rules_inventory != config.use_merchant_rules_inventory:
        config.use_merchant_rules_inventory = new_use_merchant_rules_inventory
        _queue_rebuild()
    if config.use_merchant_rules_inventory:
        PyImGui.text_wrapped("FoW merchant stage will call MerchantRules Execute (leader + alts). Sell/buy options below are ignored in this mode.")
    _draw_inventory_location_combo(disabled=bool(bot is not None and bot.is_running()) or config.skip_merchant_actions)
    _draw_entry_method_combo(disabled=is_running)
    _draw_entrypoint_combo(disabled=is_running or _uses_temple_kneel_entry())
    if _uses_temple_kneel_entry():
        PyImGui.text_wrapped("Temple of the Ages is used automatically when /kneel entry is selected.")
    PyImGui.begin_disabled(config.skip_merchant_actions)
    PyImGui.begin_disabled(config.use_merchant_rules_inventory)
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
    PyImGui.end_disabled()
    new_debug_logging = PyImGui.checkbox("Debug Logging", config.debug_logging)
    if bool(new_debug_logging) != bool(config.debug_logging):
        config.debug_logging = bool(new_debug_logging)
        if bot is not None:
            bot.set_debug_logging(config.debug_logging)
    config.save_throttled()


def _draw_help() -> None:
    PyImGui.text("ModularFow")
    PyImGui.separator()
    PyImGui.text_wrapped("Widget wrapper for the FoW prebuilt route using the shared modular FoW builder.")
    PyImGui.bullet_text("Uses the same FoW route builder as the standalone modular bot")
    PyImGui.bullet_text("Loads quest steps from Sources/modular_data/quests/FoW/*.json")
    PyImGui.bullet_text("Supports inventory management in Guild Hall or Eye of the North")
    PyImGui.bullet_text("Optional skip for all merchant/inventory management setup actions")
    PyImGui.bullet_text("Optional MerchantRules-backed merchant stage (leader + multibox followers)")
    PyImGui.bullet_text("Optional material selling before entry at the selected inventory location")
    PyImGui.bullet_text("Optional ectoplasm buying from current character gold only")
    PyImGui.bullet_text("Supports FoW entry with either a scroll or Temple of the Ages /kneel")
    PyImGui.bullet_text("Groups on the selected FoW entrypoint map before scrolling in")
    PyImGui.bullet_text("Supports FoW entry from Zin Ku Corridor, Chantry of Secrets, Temple of the Ages, or Embark Beach")
    PyImGui.bullet_text("Keeps widget options for hard mode, consumables, autoloot, and debug logging")
    PyImGui.bullet_text("Settings are persisted in Widgets/Config/ModularFow.ini")


def _main_impl() -> None:
    global bot, _BOT_REBUILD_PENDING

    if bot is None:
        if not _should_show_widget():
            return
        _draw_prestart_window()
        return

    if _BOT_REBUILD_PENDING and not bot.is_running():
        bot = None
        _BOT_REBUILD_PENDING = False
        _debug("FoW widget bot invalidated; it will rebuild on next start.")
        _draw_prestart_window()
        return

    bot.update()


def main():
    guarded_widget_main(BOT_NAME, _main_impl, get_bot=lambda: bot)


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
