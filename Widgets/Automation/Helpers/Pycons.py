import hashlib
import os
from datetime import datetime, timezone

# ---- REQUIRED BY WIDGET HANDLER (define immediately) ----
def configure():
    pass

def main():
    return

__all__ = ["main", "configure"]

_INIT_OK = False
_INIT_ERROR = None

MODULE_NAME = "Pycons"
MODULE_ICON = "Textures\\Module_Icons\\Pycons.png"
PYCONS_SYNC_OPCODE_RELOAD_CONFIG = 1
PYCONS_SYNC_OPCODE_RELOAD_RESULT = 2
PYCONS_SYNC_SELECTION_ENABLED_STATE_ONCE_KEY = "sync_selection_enabled_state_once"

_PYCONS_CONFIG_DIR = os.path.normpath(os.path.join("Widgets", "Config", "Pycons"))
_PYCONS_PROFILES_DIR = os.path.normpath(os.path.join(_PYCONS_CONFIG_DIR, "Profiles"))
_LEGACY_CONFIG_DIR = os.path.normpath(os.path.join("Widgets", "Config"))


def _hash_account_email(account_email: str) -> str:
    email = str(account_email or "").strip()
    if not email:
        return ""
    return hashlib.md5(email.encode()).hexdigest()[:8]


def get_pycons_generic_ini_candidates() -> tuple[str, str]:
    canonical = os.path.normpath(os.path.join(_PYCONS_CONFIG_DIR, "Pycons.ini"))
    legacy = os.path.normpath(os.path.join(_LEGACY_CONFIG_DIR, "Pycons.ini"))
    return canonical, legacy


def get_pycons_account_ini_candidates(account_email: str) -> tuple[str, str]:
    email_hash = _hash_account_email(account_email)
    if not email_hash:
        return get_pycons_generic_ini_candidates()

    canonical = os.path.normpath(os.path.join(_PYCONS_CONFIG_DIR, f"Pycons_{email_hash}.ini"))
    legacy = os.path.normpath(os.path.join(_LEGACY_CONFIG_DIR, f"Pycons_{email_hash}.ini"))
    return canonical, legacy


def resolve_pycons_generic_ini_path() -> str:
    canonical, legacy = get_pycons_generic_ini_candidates()
    if os.path.exists(canonical):
        return canonical
    if os.path.exists(legacy):
        return legacy
    return canonical


def resolve_pycons_account_ini_path(account_email: str) -> str:
    canonical, legacy = get_pycons_account_ini_candidates(account_email)
    if os.path.exists(canonical):
        return canonical
    if os.path.exists(legacy):
        return legacy
    return canonical

try:
    from typing import Any, cast
    import shutil
    import re
    import unicodedata
    import PyImGui
    import Py4GW
    import PyInventory
    from Py4GWCoreLib import (
        ConsoleLog,
        Console,
        Routines,
        IniHandler,
        Timer,
        GLOBAL_CACHE,
        ModelID,
        Map,
        ImGui,          # NEW: needed for persisted windows
        SharedCommandType,
    )
    from Py4GWCoreLib import ItemArray, Bag, Item, Effects, Player, Party, Bags, Agent, Quest
    from Py4GWCoreLib.IniManager import IniManager  # NEW: persisted windows
    import threading

    BOT_NAME = "Pycons"
    INI_SECTION = "Pycons"

    MIN_INTERVAL_MS = 250
    MIN_RESTOCK_INTERVAL_MS = 800
    DEFAULT_RESTOCK_INTERVAL_MS = 1500
    DEFAULT_INTERNAL_COOLDOWN_MS = 5000
    AFTERCAST_MS = 350
    ALCOHOL_EFFECT_TICK_MS = 1000
    MIN_ALCOHOL_FAST_INTERVAL_MS = 250
    DEFAULT_ALCOHOL_FAST_INTERVAL_MS = 1000
    MAX_ALCOHOL_FAST_INTERVAL_MS = 60000
    MIN_SWEETS_FAST_INTERVAL_MS = 250
    DEFAULT_SWEETS_FAST_INTERVAL_MS = 1000
    MAX_SWEETS_FAST_INTERVAL_MS = 60000
    MIN_PARTY_ITEM_INTERVAL_MS = 250
    DEFAULT_PARTY_ITEM_INTERVAL_MS = 1000
    MAX_PARTY_ITEM_INTERVAL_MS = 60000
    PARTY_ITEM_DEFAULT_COOLDOWN_MS = MIN_PARTY_ITEM_INTERVAL_MS
    MIN_MOVEMENT_SAFETY_WINDOW_MS = 250
    DEFAULT_MOVEMENT_SAFETY_WINDOW_MS = 5000
    MAX_MOVEMENT_SAFETY_WINDOW_MS = 60000
    DEFAULT_MOVEMENT_PARTY_ITEMS_FAST_THRESHOLD_MS = DEFAULT_PARTY_ITEM_INTERVAL_MS
    MOVEMENT_DELTA_EPSILON_SQ = 25.0
    MOVEMENT_POSITION_RESET_DELTA_SQ = 4000000.0
    TONIC_TIPSINESS_EFFECT_ID = 3402
    TONIC_TIPSINESS_DELAY_MS = 5000
    CRATE_FIREWORKS_DISPLAY_MS = 10 * 60 * 1000
    DISCO_BALL_DISPLAY_MS = 3 * 60 * 1000
    VAULT_RESTOCK_ACTION_MS = 800
    VAULT_RESTOCK_TARGET_QTY = 1
    RESTOCK_MODE_BALANCED = 0
    RESTOCK_MODE_WITHDRAW_ONLY = 1
    RESTOCK_MODE_DEPOSIT_ONLY = 2
    DEFAULT_RESTOCK_MODE = RESTOCK_MODE_BALANCED
    RESTOCK_SCOPE_ACCOUNT_WIDE = 0
    RESTOCK_SCOPE_ALLOW_LIST = 1
    RESTOCK_SCOPE_BLOCK_LIST = 2
    DEFAULT_RESTOCK_SCOPE_MODE = RESTOCK_SCOPE_ACCOUNT_WIDE
    MIN_RESTOCK_MOVE_CAP_PER_CYCLE = 1
    MAX_RESTOCK_MOVE_CAP_PER_CYCLE = 2500
    DEFAULT_RESTOCK_MOVE_CAP_PER_CYCLE = MAX_RESTOCK_MOVE_CAP_PER_CYCLE
    BLOCKED_ACTION_RETENTION_MS = 45000
    BLOCKED_ACTION_MAX_UI_ROWS = 4
    MAX_RESTOCK_CHARACTER_LIST_TEXT_LEN = 512
    MAIN_WINDOW_DEFAULT_SIZE = (560.0, 560.0)
    MAIN_SELECTED_CHILD_MIN_HEIGHT = 120.0
    MAIN_SELECTED_CHILD_MAX_HEIGHT = 420.0
    EXPERIMENTAL_TEAM_FLAG_SYNC_DEFAULT = True
    EXPERIMENTAL_MAINLOOP_REFRESH_QUEUE_DEFAULT = True

    # Brief cache so multiple "due" items don't rescan bags back-to-back
    INVENTORY_CACHE_MS = 1500
    BROADCAST_KEEPALIVE_MS = 5000
    TEAM_SETTINGS_CACHE_MS = 3000

    # In-town speed effects use explicit ids so fallback timing matches the visible effect.
    SUGAR_JOLT_SHORT_EFFECT_ID = 1916
    SUGAR_JOLT_SHORT_MS = 2 * 60 * 1000
    SUGAR_JOLT_LONG_EFFECT_ID = 1933
    SUGAR_JOLT_LONG_MS = 5 * 60 * 1000
    SUGAR_RUSH_MEDIUM_EFFECT_ID = 1323
    SUGAR_RUSH_MEDIUM_MS = 3 * 60 * 1000
    SUGAR_RUSH_LONG_EFFECT_ID = 1612
    SUGAR_RUSH_LONG_MS = 5 * 60 * 1000
    SUMMONING_STONE_DURATION_MS = 30 * 60 * 1000
    IGNEOUS_SUMMON_DURATION_MS = 60 * 60 * 1000
    SUMMONING_SICKNESS_EFFECT_ID = 2886
    SUMMONING_RESTRICTED_QUEST_IDS = frozenset({
        490,  # The Council is Called
        503,  # All's Well That Ends Well
        504,  # Warning Kehanni
        505,  # Calling the Order
        507,  # Pledge of the Merchant Princes
        581,  # Heart or Mind: Garden in Danger
        586,  # Heart or Mind: Ronjok in Danger
        683,  # Securing Champions Dawn
        730,  # Gain Goren
        737,  # Battle Preparations
    })
    SUMMONING_RESTRICTED_MAP_IDS = frozenset({
        119,  # Augury Rock mission
        351,  # Divine Path
        423,  # The Tribunal
        436,  # Command Post
        503,  # Throne of Secrets
        700,  # The Norn Fighting Tournament
        710,  # Epilogue
        840,  # Lion's Arch Keep
    })
    SUMMONING_UNIQUE_PARTY_MODEL_IDS = frozenset({
        513,         # Fire Imp (existing summon detection path)
        1726,        # Fire Imp (model data variant)
        8028,        # Legionnaire
        9055, 9076,  # Tengu Support Flare - Warrior
        9056, 9077,  # Tengu Support Flare - Ranger
        9058, 9079,  # Tengu Support Flare - Monk
        9060, 9081,  # Tengu Support Flare - Mesmer
        9062, 9083,  # Tengu Support Flare - Ritualist
        9065, 9086,  # Tengu Support Flare - Assassin
        9067, 9088,  # Tengu Support Flare - Elementalist
        9069, 9090,  # Tengu Support Flare - Necromancer
    })

    # Scan only these bags, and only on-demand
    SCAN_BAGS = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]

    # Consumable icon discovery
    _ICON_SEARCH_ROOT = "."
    _ICON_PREFERRED_ROOTS = (
        os.path.normpath("Textures\\Consumables\\Trimmed"),
        os.path.normpath("Textures\\Consumables"),
        os.path.normpath("Textures\\Item Models"),
    )
    # Aliases keep matching deterministic for known name variations.
    CONSUMABLE_ICON_NAME_ALIASES = {
        "creme_brulee": ("creme brulee",),
        "witchs_brew": ("witchs brew", "witch brew", "witch's brew"),
        "hunters_ale": ("hunters ale", "hunter ale"),
        "elixir_of_valor": ("elixir of valor",),
        "igneous_summoning_stone": ("igneous summoning stone",),
        "imperial_guard_reinforcement_order": ("imperial guard reinforcement order", "imperial guard summon"),
        "legionnaire_summoning_crystal": ("legionnaire summoning crystal",),
        "mercantile_summoning_stone": ("mercantile summoning stone", "merchant summon", "merchant summoning stone"),
        "mischievous_tonic": ("mischievious tonic",),
        "sinister_automatonic": ("sinister automatonic tonic",),
        "skeletonic": ("skeletonic tonic",),
        "powerstone_of_courage": ("powerstone of courage",),
        "seal_of_the_dragon_empire": ("seal of the dragon empire",),
        "shining_blade_war_horn": ("shining blade war horn", "shining blade summon"),
        "tengu_support_flare": ("tengu support flare", "tengu summon"),
    }
    # Explicit filename overrides for known consumables when deterministic mapping is preferred.
    CONSUMABLE_ICON_FILE_OVERRIDES = {
        "powerstone_of_courage": "Powerstone_of_Courage.png",
    }
    _icon_candidates_cache = None
    _icon_path_by_key_cache = {}

    # -------------------------
    # Window position persistence (minimal)
    # -------------------------
    _ini_ready = False
    INI_KEY_MAIN = ""
    INI_KEY_SETTINGS = ""
    INI_KEY_FLOATING_UI = ""
    _INI_PATH = "Widgets/Pycons"
    _INI_MAIN_FILE = "Pycons.MainWindow.ini"
    _INI_SETTINGS_FILE = "Pycons.SettingsWindow.ini"
    _INI_FLOATING_FILE = "Pycons.FloatingIcon.ini"
    FLOATING_ICON_WINDOW_ID = "##pycons_floating_icon_button"
    FLOATING_ICON_WINDOW_NAME = "Pycons Toggle"

    def _init_window_persistence_once() -> bool:
        """Create/load separate ImGui ini files for main, settings, and floating icon UI."""
        global _ini_ready, INI_KEY_MAIN, INI_KEY_SETTINGS, INI_KEY_FLOATING_UI
        if _ini_ready:
            return True
        if not Routines.Checks.Map.MapValid():
            return False

        ini = IniManager()

        INI_KEY_MAIN = ini.ensure_key(_INI_PATH, _INI_MAIN_FILE)
        if not INI_KEY_MAIN:
            return False
        ini.load_once(INI_KEY_MAIN)

        INI_KEY_SETTINGS = ini.ensure_key(_INI_PATH, _INI_SETTINGS_FILE)
        if not INI_KEY_SETTINGS:
            return False
        ini.load_once(INI_KEY_SETTINGS)

        INI_KEY_FLOATING_UI = ini.ensure_key(_INI_PATH, _INI_FLOATING_FILE)
        if not INI_KEY_FLOATING_UI:
            return False

        _ini_ready = True
        return True

    def _get_floating_icon_path() -> str:
        return os.path.join(Py4GW.Console.get_projects_path(), MODULE_ICON)

    def _set_main_window_visible(visible: bool, *, persist: bool = False, expand_on_show: bool = True):
        value = bool(visible)
        _rt.show_main_window = value
        if value and expand_on_show:
            _rt.expand_main_window_on_next_show = True
        if not value:
            show_settings[0] = False
        if _rt.floating_button is not None:
            _rt.floating_button.set_visible(value, persist=persist, invoke_callback=False)

    def _on_floating_icon_visibility_toggled(visible: bool):
        _set_main_window_visible(bool(visible), persist=False, expand_on_show=bool(visible))

    def _ensure_floating_ui():
        if _rt.floating_button is None:
            _rt.floating_button = ImGui.FloatingIcon(
                icon_path=_get_floating_icon_path(),
                window_id=FLOATING_ICON_WINDOW_ID,
                window_name=FLOATING_ICON_WINDOW_NAME,
                tooltip_visible="Hide Pycons window",
                tooltip_hidden="Show Pycons window",
                visible=bool(_rt.show_main_window),
                toggle_ini_key=INI_KEY_FLOATING_UI,
                toggle_var_name="show_main_window",
                toggle_default=True,
                on_toggle=_on_floating_icon_visibility_toggled,
            )
            _rt.floating_button.load_visibility()
            _rt.show_main_window = bool(_rt.floating_button.visible)
        return _rt.floating_button

    # -------------------------
    # UI helpers (tuple/non-tuple returns)
    # -------------------------
    def ui_input_int(label: str, value: int):
        res = PyImGui.input_int(label, int(value))
        if isinstance(res, tuple) and len(res) == 2:
            return bool(res[0]), int(res[1])
        new_val = int(res)
        return (new_val != int(value)), new_val

    def ui_input_int_fixed(label: str, value: int, width: float = 96.0):
        try:
            if hasattr(PyImGui, "push_item_width"):
                PyImGui.push_item_width(float(width))
            res = PyImGui.input_int(label, int(value))
        finally:
            try:
                if hasattr(PyImGui, "pop_item_width"):
                    PyImGui.pop_item_width()
            except Exception:
                pass
        if isinstance(res, tuple) and len(res) == 2:
            return bool(res[0]), int(res[1])
        new_val = int(res)
        return (new_val != int(value)), new_val

    def ui_input_text(label: str, value: str, max_len: int):
        res = PyImGui.input_text(label, value, int(max_len))
        if isinstance(res, tuple) and len(res) == 2:
            return bool(res[0]), str(res[1])
        new_val = str(res)
        return (new_val != value), new_val

    def ui_checkbox(label: str, value: bool):
        res = PyImGui.checkbox(label, bool(value))
        if isinstance(res, tuple) and len(res) == 2:
            return bool(res[0]), bool(res[1])
        new_val = bool(res)
        return (new_val != bool(value)), new_val

    def ui_combo(label: str, current_index: int, items: list[str]):
        try:
            idx = int(PyImGui.combo(label, int(current_index), items))
        except Exception:
            idx = int(current_index)
        max_idx = max(0, len(items) - 1)
        idx = max(0, min(max_idx, idx))
        return (idx != int(current_index)), idx

    def ui_collapsing_header(label: str, default_open: bool):
        try:
            return bool(PyImGui.collapsing_header(label, bool(default_open)))
        except Exception:
            try:
                return bool(PyImGui.collapsing_header(label))
            except Exception:
                return bool(default_open)

    def _same_line(spacing=8.0):
        PyImGui.same_line(0.0, float(spacing))

    def _collapsing_header_force(label: str, force_open, default_open: bool):
        # force_open: True/False/None
        if force_open is not None:
            try:
                cond = getattr(PyImGui, "ImGuiCond_Always", None)
                if hasattr(PyImGui, "set_next_item_open"):
                    if cond is not None:
                        PyImGui.set_next_item_open(bool(force_open), cond)
                    else:
                        PyImGui.set_next_item_open(bool(force_open))
            except Exception:
                pass
        return ui_collapsing_header(label, default_open)

    SECTION_ACCENTS = {
        "general": {
            "header": (0.11, 0.15, 0.20, 0.82),
            "header_hovered": (0.15, 0.20, 0.27, 0.90),
            "header_active": (0.18, 0.24, 0.32, 0.96),
            "text": (0.90, 0.93, 0.97, 1.00),
            "meta": (0.74, 0.79, 0.86, 1.00),
        },
        "explorable": {
            "header": (0.09, 0.18, 0.16, 0.82),
            "header_hovered": (0.12, 0.24, 0.21, 0.90),
            "header_active": (0.15, 0.29, 0.25, 0.96),
            "text": (0.82, 0.93, 0.88, 1.00),
            "meta": (0.68, 0.82, 0.77, 1.00),
        },
        "outpost": {
            "header": (0.09, 0.15, 0.24, 0.82),
            "header_hovered": (0.12, 0.20, 0.31, 0.90),
            "header_active": (0.15, 0.25, 0.38, 0.96),
            "text": (0.82, 0.89, 0.98, 1.00),
            "meta": (0.67, 0.78, 0.92, 1.00),
        },
        "mbdp": {
            "header": (0.23, 0.18, 0.08, 0.82),
            "header_hovered": (0.29, 0.22, 0.10, 0.90),
            "header_active": (0.35, 0.27, 0.12, 0.96),
            "text": (0.96, 0.88, 0.72, 1.00),
            "meta": (0.88, 0.76, 0.54, 1.00),
        },
        "summoning": {
            "header": (0.19, 0.13, 0.08, 0.82),
            "header_hovered": (0.25, 0.18, 0.10, 0.90),
            "header_active": (0.31, 0.22, 0.12, 0.96),
            "text": (0.96, 0.88, 0.76, 1.00),
            "meta": (0.88, 0.77, 0.60, 1.00),
        },
        "alcohol": {
            "header": (0.22, 0.13, 0.08, 0.82),
            "header_hovered": (0.28, 0.17, 0.10, 0.90),
            "header_active": (0.34, 0.21, 0.12, 0.96),
            "text": (1.00, 0.78, 0.30, 1.00),
            "meta": (0.92, 0.64, 0.22, 1.00),
        },
        "party_items": {
            "header": (0.34, 0.34, 0.34, 0.82),
            "header_hovered": (0.40, 0.40, 0.40, 0.90),
            "header_active": (0.46, 0.46, 0.46, 0.96),
            "text": (1.00, 0.78, 0.30, 1.00),
            "meta": (0.92, 0.64, 0.22, 1.00),
        },
        "restock": {
            "header": (0.21, 0.18, 0.10, 0.82),
            "header_hovered": (0.27, 0.23, 0.13, 0.90),
            "header_active": (0.33, 0.28, 0.16, 0.96),
            "text": (0.95, 0.91, 0.76, 1.00),
            "meta": (0.84, 0.79, 0.61, 1.00),
        },
        "settings_profiles": {
            "header": (0.95, 0.48, 0.00, 0.88),
            "header_hovered": (1.00, 0.56, 0.06, 0.94),
            "header_active": (1.00, 0.64, 0.14, 1.00),
            "header_text": (0.06, 0.05, 0.02, 1.00),
            "text": (0.90, 0.93, 0.97, 1.00),
            "meta": (0.74, 0.79, 0.86, 1.00),
        },
        "settings_other_accounts": {
            "header": (0.48, 0.17, 0.75, 0.88),
            "header_hovered": (0.56, 0.27, 0.84, 0.94),
            "header_active": (0.64, 0.36, 0.91, 1.00),
            "header_text": (0.96, 0.96, 0.96, 1.00),
            "text": (0.96, 0.88, 0.72, 1.00),
            "meta": (0.88, 0.76, 0.54, 1.00),
        },
        "settings_select": {
            "header": (0.00, 0.00, 0.00, 0.88),
            "header_hovered": (0.08, 0.08, 0.08, 0.94),
            "header_active": (0.14, 0.14, 0.14, 1.00),
            "header_text": (0.96, 0.96, 0.96, 1.00),
            "text": (0.90, 0.93, 0.97, 1.00),
            "meta": (0.74, 0.79, 0.86, 1.00),
        },
        "settings_select_explorable": {
            "header": (0.10, 0.10, 0.10, 0.88),
            "header_hovered": (0.16, 0.16, 0.16, 0.94),
            "header_active": (0.22, 0.22, 0.22, 1.00),
            "header_text": (0.96, 0.96, 0.96, 1.00),
            "text": (0.82, 0.93, 0.88, 1.00),
            "meta": (0.68, 0.82, 0.77, 1.00),
        },
        "settings_select_summoning": {
            "header": (0.15, 0.15, 0.15, 0.88),
            "header_hovered": (0.21, 0.21, 0.21, 0.94),
            "header_active": (0.27, 0.27, 0.27, 1.00),
            "header_text": (0.96, 0.96, 0.96, 1.00),
            "text": (0.96, 0.88, 0.76, 1.00),
            "meta": (0.88, 0.77, 0.60, 1.00),
        },
        "settings_select_mbdp": {
            "header": (0.20, 0.20, 0.20, 0.88),
            "header_hovered": (0.26, 0.26, 0.26, 0.94),
            "header_active": (0.32, 0.32, 0.32, 1.00),
            "header_text": (0.96, 0.96, 0.96, 1.00),
            "text": (0.96, 0.88, 0.72, 1.00),
            "meta": (0.88, 0.76, 0.54, 1.00),
        },
        "settings_select_outpost": {
            "header": (0.25, 0.25, 0.25, 0.88),
            "header_hovered": (0.31, 0.31, 0.31, 0.94),
            "header_active": (0.37, 0.37, 0.37, 1.00),
            "header_text": (0.96, 0.96, 0.96, 1.00),
            "text": (0.82, 0.89, 0.98, 1.00),
            "meta": (0.67, 0.78, 0.92, 1.00),
        },
        "settings_select_alcohol": {
            "header": (0.30, 0.30, 0.30, 0.88),
            "header_hovered": (0.36, 0.36, 0.36, 0.94),
            "header_active": (0.42, 0.42, 0.42, 1.00),
            "header_text": (0.96, 0.96, 0.96, 1.00),
            "text": (0.97, 0.84, 0.74, 1.00),
            "meta": (0.88, 0.72, 0.58, 1.00),
        },
        "settings_select_party_items": {
            "header": (0.35, 0.35, 0.35, 0.88),
            "header_hovered": (0.41, 0.41, 0.41, 0.94),
            "header_active": (0.47, 0.47, 0.47, 1.00),
            "header_text": (0.96, 0.96, 0.96, 1.00),
            "text": (0.94, 0.94, 0.94, 1.00),
            "meta": (0.80, 0.80, 0.80, 1.00),
        },
        "settings_mbdp": {
            "header": (0.82, 0.00, 0.00, 0.88),
            "header_hovered": (0.88, 0.10, 0.10, 0.94),
            "header_active": (0.94, 0.20, 0.20, 1.00),
            "header_text": (0.96, 0.96, 0.96, 1.00),
            "text": (0.96, 0.88, 0.72, 1.00),
            "meta": (0.88, 0.76, 0.54, 1.00),
        },
        "settings_alcohol": {
            "header": (0.00, 0.64, 0.26, 0.88),
            "header_hovered": (0.06, 0.72, 0.34, 0.94),
            "header_active": (0.12, 0.80, 0.42, 1.00),
            "header_text": (0.96, 0.98, 0.96, 1.00),
            "text": (0.97, 0.84, 0.74, 1.00),
            "meta": (0.88, 0.72, 0.58, 1.00),
        },
        "settings_movement_safety": {
            "header": (0.81, 0.76, 0.62, 0.88),
            "header_hovered": (0.87, 0.82, 0.68, 0.94),
            "header_active": (0.93, 0.88, 0.74, 1.00),
            "header_text": (0.08, 0.07, 0.04, 1.00),
            "text": (0.98, 0.93, 0.78, 1.00),
            "meta": (0.84, 0.79, 0.64, 1.00),
        },
        "settings_restock": {
            "header": (0.00, 0.45, 0.70, 0.88),
            "header_hovered": (0.06, 0.52, 0.77, 0.94),
            "header_active": (0.10, 0.58, 0.84, 1.00),
            "header_text": (0.96, 0.98, 1.00, 1.00),
            "text": (0.95, 0.91, 0.76, 1.00),
            "meta": (0.84, 0.79, 0.61, 1.00),
        },
        "settings_tooltip": {
            "header": (0.94, 0.89, 0.26, 0.88),
            "header_hovered": (0.98, 0.93, 0.34, 0.94),
            "header_active": (1.00, 0.97, 0.43, 1.00),
            "header_text": (0.06, 0.06, 0.04, 1.00),
            "text": (0.90, 0.93, 0.97, 1.00),
            "meta": (0.74, 0.79, 0.86, 1.00),
        },
    }

    def _section_palette(section_key: str) -> dict:
        return SECTION_ACCENTS.get(str(section_key or ""), SECTION_ACCENTS["general"])

    def _push_section_header_style(section_key: str) -> int:
        pushed = 0
        palette = _section_palette(section_key)
        for col_name, key in (
            ("Header", "header"),
            ("HeaderHovered", "header_hovered"),
            ("HeaderActive", "header_active"),
            ("Text", "header_text"),
        ):
            try:
                col = getattr(PyImGui.ImGuiCol, col_name, None)
                if col is None or key not in palette:
                    continue
                PyImGui.push_style_color(col, palette[key])
                pushed += 1
            except Exception:
                continue
        return int(pushed)

    def _pop_style_color_count(count: int):
        if int(count) <= 0:
            return
        try:
            PyImGui.pop_style_color(int(count))
        except Exception:
            try:
                for _ in range(int(count)):
                    PyImGui.pop_style_color(1)
            except Exception:
                pass

    def _styled_collapsing_header(label: str, default_open: bool, section_key: str):
        pushed = _push_section_header_style(section_key)
        try:
            return ui_collapsing_header(label, default_open)
        finally:
            _pop_style_color_count(pushed)

    def _styled_collapsing_header_force(label: str, force_open, default_open: bool, section_key: str):
        pushed = _push_section_header_style(section_key)
        try:
            return _collapsing_header_force(label, force_open, default_open)
        finally:
            _pop_style_color_count(pushed)

    def _begin_disabled(disabled: bool):
        if not disabled:
            return None
        try:
            fn_begin_disabled = getattr(PyImGui, "begin_disabled", None)
            if callable(fn_begin_disabled):
                try:
                    fn_begin_disabled(True)
                except Exception:
                    fn_begin_disabled()
                return "begin_disabled"
        except Exception:
            pass
        try:
            item_flags = getattr(PyImGui, "ImGuiItemFlags", None)
            disabled_flag = getattr(item_flags, "Disabled", None) if item_flags is not None else None
            style_vars = getattr(PyImGui, "ImGuiStyleVar", None)
            alpha_var = getattr(style_vars, "Alpha", None) if style_vars is not None else None
            fn_push_item_flag = getattr(PyImGui, "push_item_flag", None)
            if callable(fn_push_item_flag) and disabled_flag is not None:
                fn_push_item_flag(disabled_flag, True)
                try:
                    if alpha_var is not None:
                        PyImGui.push_style_var(alpha_var, 0.5)
                        return "flag+alpha"
                    return "flag"
                except Exception:
                    return "flag"
        except Exception:
            pass
        try:
            style_vars = getattr(PyImGui, "ImGuiStyleVar", None)
            alpha_var = getattr(style_vars, "Alpha", None) if style_vars is not None else None
            if alpha_var is None:
                return None
            PyImGui.push_style_var(alpha_var, 0.5)
            return "alpha"
        except Exception:
            return None

    def _end_disabled(mode):
        if mode == "begin_disabled":
            try:
                PyImGui.end_disabled()
            except Exception:
                pass
        elif mode == "flag+alpha":
            try:
                PyImGui.pop_style_var(1)
            except Exception:
                pass
            try:
                fn_pop_item_flag = getattr(PyImGui, "pop_item_flag", None)
                if callable(fn_pop_item_flag):
                    fn_pop_item_flag()
            except Exception:
                pass
        elif mode == "flag":
            try:
                fn_pop_item_flag = getattr(PyImGui, "pop_item_flag", None)
                if callable(fn_pop_item_flag):
                    fn_pop_item_flag()
            except Exception:
                pass
        elif mode == "alpha":
            try:
                PyImGui.pop_style_var(1)
            except Exception:
                pass

    def _badge_button(text: str, enabled: bool, id_suffix: str) -> bool:
        try:
            if enabled:
                bg = (0.15, 0.55, 0.20, 1.00)
                bg_h = (0.18, 0.62, 0.23, 1.00)
                bg_a = (0.12, 0.48, 0.18, 1.00)
            else:
                bg = (0.30, 0.30, 0.30, 1.00)
                bg_h = (0.36, 0.36, 0.36, 1.00)
                bg_a = (0.26, 0.26, 0.26, 1.00)

            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, bg)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, bg_h)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, bg_a)

            clicked = bool(PyImGui.small_button(f" {text} ##{id_suffix}"))

            PyImGui.pop_style_color(3)
            return clicked
        except Exception:
            try:
                PyImGui.text(f"[{text}]")
            except Exception:
                pass
            return False

    # Tooltip helper for the last UI item
    def _tooltip_if_hovered(text: str):
        if not text:
            return
        # Keep tooltip width readable by pre-wrapping long lines.
        def _wrapped_tooltip_text(raw: str, width: int = 88) -> str:
            try:
                import textwrap
                out = []
                for part in str(raw).splitlines():
                    p = str(part).strip()
                    if not p:
                        out.append("")
                        continue
                    out.extend(textwrap.wrap(p, width=int(width), break_long_words=False, break_on_hyphens=False))
                return "\n".join(out)
            except Exception:
                return str(raw)

        try:
            fn_hover = getattr(PyImGui, "is_item_hovered", None)
            if callable(fn_hover) and fn_hover():
                wrapped = _wrapped_tooltip_text(text)
                fn_tip = getattr(PyImGui, "set_tooltip", None)
                if callable(fn_tip):
                    fn_tip(str(wrapped))
                    return
                bt = getattr(PyImGui, "begin_tooltip", None)
                et = getattr(PyImGui, "end_tooltip", None)
                if callable(bt) and callable(et):
                    bt()
                    if hasattr(PyImGui, "text_wrapped"):
                        PyImGui.text_wrapped(str(wrapped))
                    else:
                        PyImGui.text(str(wrapped))
                    et()
        except Exception:
            pass

    def _fmt_effective(value: int) -> str:
        try:
            return f"{int(value):+d}"
        except Exception:
            return "+0"

    TOOLTIP_VISIBILITY_OPTIONS = ["Off", "On hover", "Always show"]
    TOOLTIP_LENGTH_OPTIONS = ["Short", "Long"]
    ALCOHOL_PREFERENCE_OPTIONS = ["Smooth", "Strong-first", "Weak-first"]
    RESTOCK_MODE_OPTIONS = ["Balanced", "Withdraw only", "Deposit only"]
    RESTOCK_SCOPE_OPTIONS = ["Account-wide", "Allow list", "Block list"]
    SETTINGS_CONSUMABLE_CATEGORY_ORDER = ["explorable", "summoning", "mbdp", "outpost", "alcohol", "party_items"]

    _TOOLTIP_TEXTS = {
        "tooltip_visibility": {
            "short": "Controls when help text is shown.",
            "long": "Choose how tooltip help appears. Off hides all setting help. On hover only shows help when the setting is hovered. Always show displays full help text under each setting.",
            "why": "Use Always show while learning, then switch to On hover once your setup is stable.",
        },
        "tooltip_length": {
            "short": "Controls short vs detailed help text.",
            "long": "Short gives one-line practical summaries. Long gives full explanations with behavior details, tradeoffs, and profile-focused recommendations.",
            "why": "Long is best during setup; Short is better once you already know the system.",
        },
        "tooltip_show_why": {
            "short": "Shows an extra impact line in each tooltip.",
            "long": "When enabled, tooltips include a 'Why this matters' line to explain practical impact like safety, item burn, and team behavior side effects.",
            "why": "This makes tooltips longer but reduces guesswork while tuning settings.",
        },
        "debug_logging": {
            "short": "Shows detailed Pycons decisions in console.",
            "long": "Shows extra console messages explaining why Pycons did or did not use an item. Leave it off during normal play to keep the console quiet.",
            "why": "Useful when an item is not being used and you want to see the reason.",
        },
        "team_broadcast": {
            "short": "Broadcast usage to team.",
            "long": "When this account uses a broadcastable consumable, Pycons tells your other same-party accounts on the same map. Those accounts still use their own safety checks before spending anything.",
            "why": "Turn this on for the account that should lead shared consumable use, including team morale/DP calls.",
        },
        "mbdp_name": {
            "short": "MB/DP means Morale Boost / Death Penalty.",
            "long": "This section controls items that raise morale or remove death penalty for you or your party.",
            "why": "The short name is kept because it is compact, but the feature is about morale and DP recovery items.",
        },
        "team_consume_opt_in": {
            "short": "Opt in to team broadcasts.",
            "long": "When enabled, this account can use matching items when another account broadcasts a team call. If disabled, this account ignores those calls.",
            "why": "Use this on follower accounts that should help with shared consumables.",
        },
        "advanced_intervals": {
            "short": "Show timing controls for each item.",
            "long": "Shows extra timing fields for individual items. Most players can leave this off unless they need very specific pacing.",
            "why": "Bad timing values can waste items or make important items trigger late.",
        },
        "persist_main_runtime_toggles": {
            "short": "Choose whether main-window ON/OFF changes are saved.",
            "long": "When off, ON/OFF changes in the main window are temporary and reset after reload. When on, those changes are saved as your default settings.",
            "why": "Leave off for one-run changes. Turn on when the main window should edit your saved setup.",
        },
        "auto_vault_restock": {
            "short": "Auto-restock missing selected consumables from Xunlai Vault.",
            "long": "When enabled, Pycons automatically opens the Xunlai Vault (in outposts) and balances selected consumables that are restock-enabled in Restock Settings.",
            "why": "Keeps automation running when inventory stacks run out, without manual chest management.",
        },
        "restock_interval_ms": {
            "short": "How often Pycons checks Xunlai restock.",
            "long": "Controls how often Pycons checks whether selected items need to be moved to or from Xunlai. Slower values reduce repeated Xunlai actions.",
            "why": "A slower restock check is usually smoother and avoids extra blocked actions.",
        },
        "restock_mode": {
            "short": "Choose whether restock withdraws, deposits, or both.",
            "long": "Balanced keeps inventory near target by withdrawing shortages first, then depositing excess. Withdraw only fills shortages and skips deposits. Deposit only removes excess and skips withdrawals.",
            "why": "Use Balanced for full target maintenance, or one-way modes when you want tighter control over vault traffic.",
        },
        "restock_move_cap_per_cycle": {
            "short": "Most items Pycons may move at once.",
            "long": "Limits how many items Pycons may withdraw or deposit in one Xunlai restock action. Lower values move stock more gently; higher values catch up faster.",
            "why": "Smaller moves are smoother. Larger moves finish restocking faster.",
        },
        "restock_keep_target_on_deselect": {
            "short": "Keep per-item restock target when item is deselected.",
            "long": "When ON, deselecting an item keeps its configured restock target for later reuse. When OFF, deselecting an item immediately sets that item's restock target to 0.",
            "why": "Choose ON for temporary toggling, OFF for strict cleanup behavior.",
        },
        "restock_set_all_selected_target": {
            "short": "Set one target value for all selected items at once.",
            "long": "Applies the bulk target value to every currently selected item shown in Restock Settings.",
            "why": "Fastest way to align many items to the same inventory target.",
        },
        "restock_enable_all_selected": {
            "short": "Enable restock for all selected items.",
            "long": "Turns ON the restock toggle for every currently selected item shown in Restock Settings.",
            "why": "Useful when building or restoring a full restock loadout quickly.",
        },
        "restock_disable_all_selected": {
            "short": "Disable restock for all selected items.",
            "long": "Turns OFF the restock toggle for every currently selected item shown in Restock Settings.",
            "why": "Useful when you want to pause vault balancing in bulk without changing main-window usage toggles.",
        },
        "alcohol_enabled": {
            "short": "Master toggle for alcohol automation.",
            "long": "Enables or disables all alcohol upkeep logic. If OFF, alcohol settings below are ignored regardless of target or preference.",
            "why": "Useful to instantly pause alcohol consumption without changing item selections.",
        },
        "alcohol_disable_effect": {
            "short": "Hide the drunk screen blur while still being drunk.",
            "long": "When enabled, Pycons repeatedly clears the Guild Wars drunk post-processing blur while alcohol is active. This only affects the visual blur and does not change drunk level, title progress, or alcohol upkeep decisions.",
            "why": "Useful when you want alcohol effects and title progress without the screen blur.",
        },
        "alcohol_use_explorable": {
            "short": "Allow alcohol automation in explorable areas.",
            "long": "When enabled, alcohol upkeep can run in explorable zones (missions, vanquishes, and open areas).",
            "why": "Prevents accidental item use in content where you do not want alcohol upkeep active.",
        },
        "alcohol_use_outpost": {
            "short": "Allow alcohol automation in outposts.",
            "long": "When enabled, alcohol upkeep can run in towns and outposts.",
            "why": "Useful when you only want upkeep once combat starts, or only while waiting in town.",
        },
        "alcohol_target_level": {
            "short": "Target drunk level to maintain (0-5).",
            "long": "Sets the drunk level goal for alcohol upkeep. Higher values increase frequency and speed of alcohol consumption, lower values conserve stock.",
            "why": "This is the main knob controlling alcohol consumption rate.",
        },
        "alcohol_preference_smooth": {
            "short": "Balanced alcohol usage near target.",
            "long": "Smooth mode aims to stay near target efficiently without wasting strong alcohol too early.",
            "why": "Best default for stable long sessions.",
        },
        "alcohol_preference_strong": {
            "short": "Reach target faster using stronger alcohol first.",
            "long": "Strong-first prioritizes high-point alcohol so you reach the target level quickly after zoning or startup.",
            "why": "Great for speed; less efficient for stock preservation.",
        },
        "alcohol_preference_weak": {
            "short": "Conserve rare alcohol using weaker options first.",
            "long": "Weak-first delays strong alcohol usage and climbs more gradually, useful when conserving expensive items matters more than speed.",
            "why": "Best for stretching inventory over long runs.",
        },
        "alcohol_preference_mode": {
            "short": "Choose how alcohol strength is prioritized.",
            "long": "Smooth aims to hit target efficiently with minimal waste. Strong-first prioritizes high-point alcohol for fastest ramp-up. Weak-first prioritizes lower-point alcohol to conserve stronger stock.",
            "why": "This directly changes how quickly you reach target and how efficiently inventory is consumed.",
        },
        "alcohol_fast_spending": {
            "short": "Spend selected alcohol stacks quickly.",
            "long": "When enabled, alcohol uses the selected ON items at the speed below instead of stopping at the target drunk level.",
            "why": "Useful when you want title progress or stack cleanup instead of normal drunk-level upkeep.",
        },
        "alcohol_fast_interval_ms": {
            "short": "How fast alcohol is used in fast spending mode.",
            "long": "Controls how often Pycons tries to drink selected alcohol while Fast alcohol spending is enabled.",
            "why": "Fast title spending should not force normal Pycons item checks to run faster.",
        },
        "party_item_interval_ms": {
            "short": "How fast Party Items are used.",
            "long": "Controls how often Pycons tries to use selected Party Items. Lower values spend stacks faster; higher values are gentler for normal play.",
            "why": "Fast title-point spending should not force every other Pycons consumable to run faster.",
        },
        "sweets_fast_spending": {
            "short": "Spend selected sweet stacks quickly.",
            "long": "When enabled, Pycons uses selected ON in-town speed boost sweets at the speed below instead of waiting for their normal speed effect to end.",
            "why": "Useful when you want Sweet Tooth title progress or stack cleanup instead of normal speed upkeep.",
        },
        "sweets_fast_interval_ms": {
            "short": "How fast sweets are used in fast spending mode.",
            "long": "Controls how often Pycons tries to use selected in-town speed boost sweets while Fast sweets spending is enabled.",
            "why": "Fast title spending should not force normal Pycons item checks to run faster.",
        },
        "movement_safety_window_ms": {
            "short": "How long movement counts as recent.",
            "long": "When a movement requirement is enabled, Pycons only uses that item type if your character moved within this many milliseconds.",
            "why": "This helps prevent item waste if a bot is stuck or the player has gone idle.",
        },
        "movement_require_explorable": {
            "short": "Require recent movement before explorable consumables are used.",
            "long": "When enabled, regular explorable consumables wait until your character has moved recently.",
            "why": "Useful for consets and long-duration items that should not keep spending while stuck or idle.",
        },
        "movement_require_summoning": {
            "short": "Require recent movement before summoning items are used.",
            "long": "When enabled, summoning stones and similar summoning items wait until your character has moved recently.",
            "why": "Prevents summoning items from being burned while the character is not actively moving through content.",
        },
        "movement_require_mbdp": {
            "short": "Require recent movement before morale and DP items are used.",
            "long": "When enabled, Morale Boost and Death Penalty cleanup items wait until your character has moved recently.",
            "why": "This can reduce wasted morale and DP spending while idle, but may delay recovery if you are intentionally standing still.",
        },
        "movement_require_alcohol": {
            "short": "Require recent movement before alcohol is used.",
            "long": "When enabled, normal alcohol upkeep and fast alcohol spending wait until your character has moved recently.",
            "why": "Useful when title spending should pause if the character is no longer active.",
        },
        "movement_require_party_items": {
            "short": "Require recent movement before Party Items are used.",
            "long": "When enabled, selected Party Items wait until your character has moved recently.",
            "why": "Useful when party-point spending should pause if the character is stuck or idle.",
        },
        "movement_require_sweets": {
            "short": "Require recent movement before sweets are used.",
            "long": "When enabled, in-town speed boost sweets and fast sweets spending wait until your character has moved recently.",
            "why": "Useful when Sweet Tooth spending should pause while idle.",
        },
        "movement_alcohol_fast_only": {
            "short": "Only require movement during Fast alcohol spending.",
            "long": "When enabled, the Alcohol movement requirement applies only while Fast alcohol spending is on. Normal drunk-level upkeep can still run without movement.",
            "why": "Good when you want anti-AFK protection for stack spending without changing normal alcohol upkeep.",
        },
        "movement_party_items_speed_only": {
            "short": "Only require movement when Party Items are being used quickly.",
            "long": "When enabled, the Party Items movement requirement applies only when Party Items speed is below the safety cutoff below.",
            "why": "Good when normal Party Item use is fine, but faster title spending should pause while idle.",
        },
        "movement_party_items_fast_threshold_ms": {
            "short": "Choose when Party Items speed should require movement.",
            "long": "This does not change how fast Party Items are used. It only decides when movement safety treats the Party Items speed as fast spending.",
            "why": "Use this if you consider a different Party Items speed to be normal play instead of title spending.",
        },
        "movement_sweets_fast_only": {
            "short": "Only require movement during Fast sweets spending.",
            "long": "When enabled, the Sweets movement requirement applies only while Fast sweets spending is on. Normal in-town speed upkeep can still run without movement.",
            "why": "Good when you want Sweet Tooth stack cleanup protected without changing normal speed boost behavior.",
        },
        "mbdp_enabled": {
            "short": "Master toggle for morale/DP automation.",
            "long": "Turns all morale boost and death penalty item automation on or off. If off, none of the settings below will use items.",
            "why": "Use this as the main switch for morale and DP cleanup.",
        },
        "mbdp_allow_partywide_in_human_parties": {
            "short": "Allow team items when extra human players are in party.",
            "long": "When off, Pycons avoids party-wide morale and DP items if there are human party members that Pycons is not coordinating. When on, Pycons may still use party-wide items in mixed human parties.",
            "why": "Off is safer. Turn on only when everyone in the party expects these items to be used.",
        },
        "mbdp_receiver_require_enabled": {
            "short": "Followers only use team items enabled on that account.",
            "long": "When on, a follower only reacts to a team item call if that exact item is enabled locally. When off, a team call can make the follower use the item even if its local toggle is off.",
            "why": "On is safer and prevents accidental follower spending.",
        },
        "mbdp_prefer_seal_for_recharge": {
            "short": "Prefer Seal over Pumpkin for self +10 morale upkeep.",
            "long": "When self morale top-up decides to use a +10 self item and both are available, use Seal first instead of Pumpkin.",
            "why": "This is a preference/order setting only.",
        },
        "mbdp_restore_defaults": {
            "short": "Reset morale/DP settings in this section to defaults.",
            "long": "Restores only morale and death penalty values in this section to balanced defaults. Does not change general, alcohol, or consumable selection settings.",
            "why": "Fast recovery if experimentation made morale/DP behavior unpredictable.",
        },
        "mbdp_self_dp_minor_threshold": {
            "short": "Your DP level where light cleanup starts.",
            "long": "When your DP reaches this value, Pycons may use lighter DP cleanup items for you, such as Refined Jelly or Wintergreen Candy Cane. Example: -30 means cleanup can start at -30 DP.",
            "why": "Closer to 0 triggers earlier/more often; closer to -60 triggers later/less often.",
        },
        "mbdp_self_dp_major_threshold": {
            "short": "Your DP level where stronger cleanup starts.",
            "long": "When your DP reaches this value, Pycons may use stronger DP cleanup items for you, such as Peppermint Candy Cane. Example: -45 means stronger cleanup can start at -45 DP.",
            "why": "Usually set lower (more negative) than minor so it acts like escalation.",
        },
        "mbdp_self_morale_target_effective": {
            "short": "Morale level Pycons tries to keep on you.",
            "long": "Target morale for yourself, from -60 DP to +10 morale boost. 0 means neutral. Higher values use morale items more aggressively.",
            "why": "Use this to control how aggressively self morale is topped up.",
        },
        "mbdp_self_min_morale_gain": {
            "short": "Minimum self gain required before morale item use.",
            "long": "Minimum expected gain required before a self morale item is used.",
            "why": "Higher values reduce waste from tiny top-ups.",
        },
        "mbdp_party_min_members": {
            "short": "Party members needed before team items can be used.",
            "long": "Minimum number of party members who must be valid targets before party-wide morale or DP items are considered.",
            "why": "This prevents spending team items for too few people.",
        },
        "mbdp_party_min_interval_ms": {
            "short": "Minimum time between team morale/DP item uses.",
            "long": "Minimum time between party-wide morale or DP item uses. Lower values react faster and spend more. Higher values are slower and more conservative.",
            "why": "This strongly affects total item consumption rate.",
        },
        "mbdp_party_target_effective": {
            "short": "Morale level Pycons tries to keep for the party.",
            "long": "Party morale target used when deciding if team morale items are worth using. +10 means try to keep the party near maximum morale boost.",
            "why": "This affects when party morale options are considered worth using.",
        },
        "mbdp_strict_party_plus10": {
            "short": "Aggressively maintain +10 party morale.",
            "long": "When enabled, party morale decisions ignore minimum party-gain limits and try to top up morale whenever any checked party member is below +10. DP cleanup still runs first.",
            "why": "Use this when your goal is to keep party morale as close to +10 as possible instead of conserving morale consumables.",
        },
        "mbdp_party_min_total_gain_5": {
            "short": "Minimum total party gain before a +5 morale item.",
            "long": "Minimum total morale benefit across the party before +5 party morale items are allowed.",
            "why": "Lower this to fire +5 items more often.",
        },
        "mbdp_party_min_total_gain_10": {
            "short": "Minimum total party gain before a +10 morale item.",
            "long": "Minimum total morale benefit across the party before +10 party morale items are allowed.",
            "why": "Raise this to make +10 items rarer; lower it to use them sooner.",
        },
        "mbdp_party_light_dp_threshold": {
            "short": "Party DP level where light cleanup starts.",
            "long": "DP value for lighter party DP recovery items, such as Four-Leaf Clover. Example: -15 means this cleanup can start when party members reach -15 DP, if enough members qualify.",
            "why": "Use this as the earlier, softer party DP response. If stronger items are unavailable, Pycons can still use lower options when valid.",
        },
        "mbdp_party_heavy_dp_threshold": {
            "short": "Party DP level where stronger cleanup starts.",
            "long": "DP value for stronger party DP recovery items, such as Oath of Purity. Example: -30 means this cleanup can start when party members reach -30 DP, if enough members qualify.",
            "why": "Usually set lower, meaning more negative, than light cleanup so it acts as escalation. If stronger items are unavailable, Pycons can fall back to lower valid options.",
        },
        "mbdp_powerstone_dp_threshold": {
            "short": "Party DP level where Powerstone emergency starts.",
            "long": "Severe DP value for emergency cleanup. Example: -45 means emergency cleanup can start when party members reach -45 DP, if enough members qualify.",
            "why": "Use this for severe DP only. If unavailable, Pycons tries lower DP cleanup and then valid morale options instead of stalling.",
        },
        "filter_search": {
            "short": "Filter consumables by name.",
            "long": "Searches the consumable lists in Settings. Works across explorable, summoning, outpost, morale/DP, and alcohol groups.",
            "why": "Speeds up setup when many items exist.",
        },
        "select_all_visible": {
            "short": "Select all currently visible items.",
            "long": "Marks every item currently visible by search/filter/expanded groups as selected.",
            "why": "Fast bulk setup, but verify filtered view before applying.",
        },
        "clear_all_visible": {
            "short": "Clear selection for all currently visible items.",
            "long": "Unselects every item currently visible by search/filter/expanded groups.",
            "why": "Fast bulk cleanup; can remove many settings at once.",
        },
        "expand_all": {
            "short": "Open all consumable groups.",
            "long": "Expands all consumable sections in the settings window.",
            "why": "Useful when auditing all selected items at once.",
        },
        "collapse_all": {
            "short": "Close all consumable groups.",
            "long": "Collapses all consumable sections for a compact settings view.",
            "why": "Reduces visual noise after setup.",
        },
        "only_show_available_inventory": {
            "short": "Show only items currently in inventory.",
            "long": "When ON, settings lists hide items not present in inventory. This is useful for cleanup but can hide items you still plan to configure for later.",
            "why": "Great for active runs; not ideal when planning future loadouts.",
        },
        "only_show_selected_items": {
            "short": "Show only items currently selected for the main window.",
            "long": "When ON, settings lists hide items that are not selected to appear in the main window. Selected items are shown even when inventory count is 0.",
            "why": "Useful for quickly auditing and editing your active loadout.",
        },
        "presets_section": {
            "short": "Manage shared saved profiles for Pycons.",
            "long": "Saved profiles live in the shared Pycons profile library, while built-in quick presets stay available in Morale Boost & Death Penalty settings.",
            "why": "Useful when switching between solo, leader, and team playstyles without manually changing many fields.",
        },
        "preset_leader_force_plus10_team": {
            "short": "Leader mode that enforces a team morale target.",
            "long": "ON makes the leader account try to keep valid party members at the chosen morale target. Morale items are only used when someone is below that target. Turning this off only disables this leader preset; normal morale and DP settings can still run.",
            "why": "Use this when one leader account should manage party morale without turning off the rest of morale/DP behavior.",
        },
        "preset_solo_safe": {
            "short": "Safe single-account preset with local-only behavior.",
            "long": "Applies a conservative solo profile: no team calls, morale/DP enabled with safe defaults, and follower safety protections kept on.",
            "why": "Good baseline when you are not coordinating consumables across accounts.",
        },
        "profile_save_new": {
            "short": "Save the current settings as a new named profile.",
            "long": "Creates a new shared Pycons profile using the current Pycons settings, including the current main-window ON/OFF state.",
            "why": "Useful when you want to snapshot your current setup without overwriting an existing profile.",
        },
        "profile_load_selected": {
            "short": "Load the selected saved profile for this account.",
            "long": "Applies the selected shared profile to this account, reloads Pycons immediately, and refreshes the current session.",
            "why": "Fast profile switching for different team roles or farming modes without pushing changes to other accounts.",
        },
        "profile_save_over_selected": {
            "short": "Overwrite the selected saved profile with the current settings.",
            "long": "Updates the selected shared profile using your current Pycons settings while keeping that profile's identity and created date.",
            "why": "Useful when you want to revise an existing saved setup after tuning it in the main window.",
        },
        "profile_rename": {
            "short": "Rename the selected saved profile.",
            "long": "Updates only the selected shared profile's display name and saved update time.",
            "why": "Lets you clean up or clarify saved setups without changing how they are stored.",
        },
        "profile_duplicate": {
            "short": "Duplicate the selected saved profile.",
            "long": "Creates a new shared profile by copying the selected saved profile. It does not use the current settings.",
            "why": "Useful when you want a starting point for a variant setup without overwriting the original saved profile.",
        },
        "profile_delete": {
            "short": "Delete the selected saved profile.",
            "long": "Removes the selected profile from the shared Pycons profile library. The current account settings are not changed.",
            "why": "Keeps the saved-profile list tidy when a setup is no longer needed.",
        },
        "preset_set_others_optin": {
            "short": "Set all other party accounts: Opt-in ON.",
            "long": "Turns team broadcast opt-in on for every other account Pycons currently sees in the same party and map.",
            "why": "Useful after applying leader presets so followers can react to team broadcasts.",
        },
        "preset_set_others_optout": {
            "short": "Set all other party accounts: Opt-in OFF.",
            "long": "Turns team broadcast opt-in off for every other account Pycons currently sees.",
            "why": "Useful for quickly stopping follower consumption without editing each account manually.",
        },
    }

    def _cfg_int(name: str, default: int = 0) -> int:
        try:
            return int(getattr(cfg, name, default))
        except Exception:
            return int(default)

    def _tooltip_text_for(setting_key: str, fallback: str = "") -> str:
        def _sentence_lines(text: str) -> str:
            # Render tooltips in short stacked lines (chat-like) for readability.
            try:
                import re
                out = []
                for para in str(text or "").splitlines():
                    p = str(para).strip()
                    if not p:
                        continue
                    parts = re.split(r'(?<=[.!?])\s+', p)
                    for s in parts:
                        ss = str(s).strip()
                        if ss:
                            out.append(ss)
                return "\n".join(out)
            except Exception:
                return str(text or "")

        data = _TOOLTIP_TEXTS.get(setting_key)
        if not data:
            return str(fallback or "")

        length_idx = max(0, min(len(TOOLTIP_LENGTH_OPTIONS) - 1, _cfg_int("tooltip_length", 1)))
        show_why = bool(getattr(cfg, "tooltip_show_why", True))

        base = str(data.get("long") if length_idx == 1 else data.get("short", "")) or str(fallback or "")
        base = _sentence_lines(base)
        if setting_key == "preset_leader_force_plus10_team":
            cur_target = _fmt_effective(int(getattr(cfg, "force_team_morale_value", 0)))
            base = f"{base}\nCurrent force target: {cur_target}"
        if show_why:
            why = str(data.get("why", "")).strip()
            if why:
                base = f"{base}\nWhy this matters: {_sentence_lines(why)}"
        return base.strip()

    def _show_setting_tooltip(setting_key: str, fallback: str = ""):
        txt = _tooltip_text_for(setting_key, fallback)
        if not txt:
            return
        vis = max(0, min(len(TOOLTIP_VISIBILITY_OPTIONS) - 1, _cfg_int("tooltip_visibility", 1)))
        if vis == 0:
            return
        if vis == 1:
            _tooltip_if_hovered(txt)
            return
        try:
            if hasattr(PyImGui, "text_wrapped"):
                PyImGui.text_wrapped(txt)
            else:
                PyImGui.text(txt)
        except Exception:
            pass

    def _ordered_consumable_category_keys(keys: list[str]) -> list[str]:
        seen = set()
        ordered = []
        for key in SETTINGS_CONSUMABLE_CATEGORY_ORDER:
            if key in keys and key not in seen:
                ordered.append(key)
                seen.add(key)
        for key in keys:
            if key not in seen:
                ordered.append(key)
                seen.add(key)
        return ordered

    LEADER_FORCE_PRESET_KEY = "leader_force_target_morale"
    PYCONS_PROFILE_SECTION_PREFIX = "PyconsProfile:"
    PYCONS_SHARED_PROFILE_SECTION = "PyconsProfile"
    PYCONS_SHARED_PROFILE_MIGRATION_FLAG_KEY = "profiles_shared_library_migrated_v1"
    PROFILE_NAME_MAX_LEN = 64
    PROFILE_BOOL_KEYS = {
        "auto_vault_restock",
        "restock_keep_target_on_deselect",
        "alcohol_enabled",
        "alcohol_disable_effect",
        "alcohol_fast_spending",
        "sweets_fast_spending",
        "movement_require_explorable",
        "movement_require_summoning",
        "movement_require_mbdp",
        "movement_require_alcohol",
        "movement_require_party_items",
        "movement_require_sweets",
        "movement_alcohol_fast_only",
        "movement_party_items_speed_only",
        "movement_sweets_fast_only",
        "alcohol_use_explorable",
        "alcohol_use_outpost",
        "team_broadcast",
        "team_consume_opt_in",
        "mbdp_enabled",
        "mbdp_allow_partywide_in_human_parties",
        "mbdp_receiver_require_enabled",
        "mbdp_strict_party_plus10",
        "mbdp_prefer_seal_for_recharge",
    }
    PROFILE_SCALAR_KEYS = [
        "interval_ms",
        "auto_vault_restock",
        "restock_interval_ms",
        "restock_mode",
        "restock_move_cap_per_cycle",
        "restock_keep_target_on_deselect",
        "alcohol_enabled",
        "alcohol_disable_effect",
        "alcohol_fast_spending",
        "alcohol_fast_interval_ms",
        "sweets_fast_spending",
        "sweets_fast_interval_ms",
        "movement_safety_window_ms",
        "movement_party_items_fast_threshold_ms",
        "movement_require_explorable",
        "movement_require_summoning",
        "movement_require_mbdp",
        "movement_require_alcohol",
        "movement_require_party_items",
        "movement_require_sweets",
        "movement_alcohol_fast_only",
        "movement_party_items_speed_only",
        "movement_sweets_fast_only",
        "alcohol_target_level",
        "alcohol_use_explorable",
        "alcohol_use_outpost",
        "alcohol_preference",
        "party_item_interval_ms",
        "team_broadcast",
        "team_consume_opt_in",
        "force_team_morale_value",
        "mbdp_enabled",
        "mbdp_allow_partywide_in_human_parties",
        "mbdp_receiver_require_enabled",
        "mbdp_strict_party_plus10",
        "mbdp_self_dp_minor_threshold",
        "mbdp_self_dp_major_threshold",
        "mbdp_self_morale_target_effective",
        "mbdp_self_min_morale_gain",
        "mbdp_party_min_members",
        "mbdp_party_min_interval_ms",
        "mbdp_party_target_effective",
        "mbdp_party_min_total_gain_5",
        "mbdp_party_min_total_gain_10",
        "mbdp_party_light_dp_threshold",
        "mbdp_party_heavy_dp_threshold",
        "mbdp_powerstone_dp_threshold",
        "mbdp_prefer_seal_for_recharge",
    ]

    def _default_pycons_sync_category_selection() -> dict[str, bool]:
        return {str(key): False for key, _label in PYCONS_SYNC_CATEGORY_DEFS}

    def _save_ini_config(ini_handler, config):
        ini_handler.save(config)

    def _ensure_pycons_profiles_dir() -> bool:
        try:
            os.makedirs(_PYCONS_PROFILES_DIR, exist_ok=True)
            return True
        except Exception:
            return False

    def _pycons_profiles_lock_path() -> str:
        return os.path.normpath(os.path.join(_PYCONS_PROFILES_DIR, ".pycons_profiles.lock"))

    def _acquire_pycons_profiles_library_lock(timeout_ms: int = 5000, *, poll_ms: int = 50, stale_after_ms: int = 120000) -> str:
        import time as _time

        if not _ensure_pycons_profiles_dir():
            raise OSError("Could not create the shared Pycons profiles folder.")

        lock_path = _pycons_profiles_lock_path()
        deadline = _time.monotonic() + max(0.25, float(timeout_ms) / 1000.0)
        sleep_seconds = max(0.01, float(poll_ms) / 1000.0)
        stale_after_ms = max(1000, int(stale_after_ms))

        while True:
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                try:
                    lock_body = (
                        f"pid={os.getpid()}\n"
                        f"created_at={_profile_timestamp_now()}\n"
                    )
                    os.write(fd, lock_body.encode("utf-8"))
                finally:
                    os.close(fd)
                return lock_path
            except FileExistsError:
                try:
                    lock_age_ms = int(max(0.0, (_time.time() - os.path.getmtime(lock_path)) * 1000.0))
                except OSError:
                    lock_age_ms = 0

                if lock_age_ms >= stale_after_ms:
                    try:
                        os.remove(lock_path)
                        continue
                    except OSError:
                        pass

                if _time.monotonic() >= deadline:
                    raise TimeoutError("Pycons shared profile library is busy. Try again in a moment.")
                _time.sleep(sleep_seconds)

    def _release_pycons_profiles_library_lock(lock_path: str):
        safe_lock_path = str(lock_path or "").strip()
        if not safe_lock_path:
            return
        try:
            if os.path.exists(safe_lock_path):
                os.remove(safe_lock_path)
        except OSError:
            pass

    def _with_pycons_profiles_library_lock(action, *, timeout_ms: int = 5000):
        lock_path = _acquire_pycons_profiles_library_lock(timeout_ms=timeout_ms)
        try:
            return action()
        finally:
            _release_pycons_profiles_library_lock(lock_path)

    def _profile_section_name(profile_id: str) -> str:
        return f"{PYCONS_PROFILE_SECTION_PREFIX}{str(profile_id or '').strip()}"

    def _profile_id_from_section(section_name: str) -> str:
        prefix = str(PYCONS_PROFILE_SECTION_PREFIX)
        name = str(section_name or "")
        if name.lower().startswith(prefix.lower()):
            return name[len(prefix):]
        return ""

    def _profile_file_path(profile_id: str) -> str:
        safe_profile_id = re.sub(r"[^A-Za-z0-9_-]", "", str(profile_id or "").strip())
        if not safe_profile_id:
            return ""
        return os.path.normpath(os.path.join(_PYCONS_PROFILES_DIR, f"{safe_profile_id}.ini"))

    def _profile_id_from_path(profile_path: str) -> str:
        safe_path = str(profile_path or "").strip()
        if not safe_path:
            return ""
        filename = os.path.basename(safe_path)
        stem, ext = os.path.splitext(filename)
        if str(ext or "").lower() != ".ini":
            return ""
        return re.sub(r"[^A-Za-z0-9_-]", "", str(stem or "").strip())

    def _profile_timestamp_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _profile_name_norm(name: str) -> str:
        return _normalize_name(str(name or ""))

    def _profile_display_name(raw_name: str, profile_id: str = "") -> str:
        clean = _compact_character_name(str(raw_name or ""))[:PROFILE_NAME_MAX_LEN]
        if clean:
            return clean
        suffix = str(profile_id or "").strip()[:8]
        return f"Profile {suffix or 'Unnamed'}"

    def _profile_reserved_name_norms() -> set[str]:
        return {_profile_name_norm(name) for name in BUILTIN_PRESET_NAMES}

    def _profile_default_scalar_value(key: str):
        defaults = {
            "interval_ms": 1500,
            "auto_vault_restock": False,
            "restock_interval_ms": DEFAULT_RESTOCK_INTERVAL_MS,
            "restock_mode": DEFAULT_RESTOCK_MODE,
            "restock_move_cap_per_cycle": DEFAULT_RESTOCK_MOVE_CAP_PER_CYCLE,
            "restock_keep_target_on_deselect": True,
            "alcohol_enabled": False,
            "alcohol_disable_effect": False,
            "alcohol_fast_spending": False,
            "alcohol_fast_interval_ms": int(DEFAULT_ALCOHOL_FAST_INTERVAL_MS),
            "sweets_fast_spending": False,
            "sweets_fast_interval_ms": int(DEFAULT_SWEETS_FAST_INTERVAL_MS),
            "movement_safety_window_ms": int(DEFAULT_MOVEMENT_SAFETY_WINDOW_MS),
            "movement_party_items_fast_threshold_ms": int(DEFAULT_MOVEMENT_PARTY_ITEMS_FAST_THRESHOLD_MS),
            "movement_require_explorable": False,
            "movement_require_summoning": False,
            "movement_require_mbdp": False,
            "movement_require_alcohol": False,
            "movement_require_party_items": False,
            "movement_require_sweets": False,
            "movement_alcohol_fast_only": False,
            "movement_party_items_speed_only": False,
            "movement_sweets_fast_only": False,
            "alcohol_target_level": 3,
            "alcohol_use_explorable": True,
            "alcohol_use_outpost": True,
            "alcohol_preference": 0,
            "party_item_interval_ms": int(DEFAULT_PARTY_ITEM_INTERVAL_MS),
            "team_broadcast": False,
            "team_consume_opt_in": False,
            "force_team_morale_value": int(MBDP_DEFAULTS["force_team_morale_value"]),
            "mbdp_enabled": bool(MBDP_DEFAULTS["mbdp_enabled"]),
            "mbdp_allow_partywide_in_human_parties": bool(MBDP_DEFAULTS["mbdp_allow_partywide_in_human_parties"]),
            "mbdp_receiver_require_enabled": bool(MBDP_DEFAULTS["mbdp_receiver_require_enabled"]),
            "mbdp_strict_party_plus10": bool(MBDP_DEFAULTS["mbdp_strict_party_plus10"]),
            "mbdp_self_dp_minor_threshold": int(MBDP_DEFAULTS["mbdp_self_dp_minor_threshold"]),
            "mbdp_self_dp_major_threshold": int(MBDP_DEFAULTS["mbdp_self_dp_major_threshold"]),
            "mbdp_self_morale_target_effective": int(MBDP_DEFAULTS["mbdp_self_morale_target_effective"]),
            "mbdp_self_min_morale_gain": int(MBDP_DEFAULTS["mbdp_self_min_morale_gain"]),
            "mbdp_party_min_members": int(MBDP_DEFAULTS["mbdp_party_min_members"]),
            "mbdp_party_min_interval_ms": int(MBDP_DEFAULTS["mbdp_party_min_interval_ms"]),
            "mbdp_party_target_effective": int(MBDP_DEFAULTS["mbdp_party_target_effective"]),
            "mbdp_party_min_total_gain_5": int(MBDP_DEFAULTS["mbdp_party_min_total_gain_5"]),
            "mbdp_party_min_total_gain_10": int(MBDP_DEFAULTS["mbdp_party_min_total_gain_10"]),
            "mbdp_party_light_dp_threshold": int(MBDP_DEFAULTS["mbdp_party_light_dp_threshold"]),
            "mbdp_party_heavy_dp_threshold": int(MBDP_DEFAULTS["mbdp_party_heavy_dp_threshold"]),
            "mbdp_powerstone_dp_threshold": int(MBDP_DEFAULTS["mbdp_powerstone_dp_threshold"]),
            "mbdp_prefer_seal_for_recharge": bool(MBDP_DEFAULTS["mbdp_prefer_seal_for_recharge"]),
        }
        default_value = defaults.get(key, False if key in PROFILE_BOOL_KEYS else 0)
        return bool(default_value) if key in PROFILE_BOOL_KEYS else int(default_value)

    def _profile_default_payload() -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for key in PROFILE_SCALAR_KEYS:
            payload[key] = _profile_default_scalar_value(key)
        for spec in CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if item_key:
                payload[f"min_interval_{item_key}"] = 0
        for spec in ALL_CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            payload[f"selected_{item_key}"] = False
            payload[f"enabled_{item_key}"] = False
            payload[f"restock_enabled_{item_key}"] = False
            payload[f"restock_target_{item_key}"] = 0
        for spec in ALCOHOL_ITEMS:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            payload[f"alcohol_selected_{item_key}"] = False
            payload[f"alcohol_enabled_{item_key}"] = False
            payload[f"restock_enabled_{item_key}"] = False
            payload[f"restock_target_{item_key}"] = 0
        return payload

    def _profile_dp_threshold_to_effective(raw_value: int) -> int:
        value = int(raw_value or 0)
        if value > 0:
            value = -value
        return max(-60, min(0, int(value)))

    def _profile_target_to_effective(raw_value: int) -> int:
        value = int(raw_value or 0)
        if value > 10:
            value = value - 100
        return max(-60, min(10, int(value)))

    def _read_profile_payload_from_ini(ini_handler, section: str, *, prefix: str = "", fallback_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = dict(fallback_payload or _profile_default_payload())

        for key in PROFILE_SCALAR_KEYS:
            default_value = payload.get(key, _profile_default_scalar_value(key))
            full_key = f"{prefix}{key}"
            if key in PROFILE_BOOL_KEYS:
                payload[key] = bool(ini_handler.read_bool(section, full_key, bool(default_value)))
            else:
                payload[key] = int(ini_handler.read_int(section, full_key, int(default_value)))

        payload["restock_interval_ms"] = max(MIN_RESTOCK_INTERVAL_MS, int(payload.get("restock_interval_ms", DEFAULT_RESTOCK_INTERVAL_MS)))
        payload["restock_mode"] = max(
            RESTOCK_MODE_BALANCED,
            min(RESTOCK_MODE_DEPOSIT_ONLY, int(payload.get("restock_mode", DEFAULT_RESTOCK_MODE))),
        )
        payload["restock_move_cap_per_cycle"] = max(
            MIN_RESTOCK_MOVE_CAP_PER_CYCLE,
            min(MAX_RESTOCK_MOVE_CAP_PER_CYCLE, int(payload.get("restock_move_cap_per_cycle", DEFAULT_RESTOCK_MOVE_CAP_PER_CYCLE))),
        )
        payload["alcohol_target_level"] = max(0, min(5, int(payload.get("alcohol_target_level", 3))))
        alcohol_preference = int(payload.get("alcohol_preference", 0))
        payload["alcohol_preference"] = alcohol_preference if alcohol_preference in (0, 1, 2) else 0
        payload["alcohol_fast_interval_ms"] = max(
            MIN_ALCOHOL_FAST_INTERVAL_MS,
            min(MAX_ALCOHOL_FAST_INTERVAL_MS, int(payload.get("alcohol_fast_interval_ms", DEFAULT_ALCOHOL_FAST_INTERVAL_MS))),
        )
        payload["sweets_fast_interval_ms"] = max(
            MIN_SWEETS_FAST_INTERVAL_MS,
            min(MAX_SWEETS_FAST_INTERVAL_MS, int(payload.get("sweets_fast_interval_ms", DEFAULT_SWEETS_FAST_INTERVAL_MS))),
        )
        payload["party_item_interval_ms"] = max(
            MIN_PARTY_ITEM_INTERVAL_MS,
            min(MAX_PARTY_ITEM_INTERVAL_MS, int(payload.get("party_item_interval_ms", DEFAULT_PARTY_ITEM_INTERVAL_MS))),
        )
        payload["movement_safety_window_ms"] = max(
            MIN_MOVEMENT_SAFETY_WINDOW_MS,
            min(MAX_MOVEMENT_SAFETY_WINDOW_MS, int(payload.get("movement_safety_window_ms", DEFAULT_MOVEMENT_SAFETY_WINDOW_MS))),
        )
        payload["movement_party_items_fast_threshold_ms"] = max(
            MIN_PARTY_ITEM_INTERVAL_MS,
            min(
                MAX_PARTY_ITEM_INTERVAL_MS,
                int(payload.get("movement_party_items_fast_threshold_ms", DEFAULT_MOVEMENT_PARTY_ITEMS_FAST_THRESHOLD_MS)),
            ),
        )
        payload["force_team_morale_value"] = max(-60, min(10, int(payload.get("force_team_morale_value", MBDP_DEFAULTS["force_team_morale_value"]))))
        payload["mbdp_self_dp_minor_threshold"] = _profile_dp_threshold_to_effective(payload.get("mbdp_self_dp_minor_threshold", MBDP_DEFAULTS["mbdp_self_dp_minor_threshold"]))
        payload["mbdp_self_dp_major_threshold"] = _profile_dp_threshold_to_effective(payload.get("mbdp_self_dp_major_threshold", MBDP_DEFAULTS["mbdp_self_dp_major_threshold"]))
        payload["mbdp_self_morale_target_effective"] = _profile_target_to_effective(payload.get("mbdp_self_morale_target_effective", MBDP_DEFAULTS["mbdp_self_morale_target_effective"]))
        payload["mbdp_self_min_morale_gain"] = max(0, min(10, int(payload.get("mbdp_self_min_morale_gain", MBDP_DEFAULTS["mbdp_self_min_morale_gain"]))))
        payload["mbdp_party_target_effective"] = _profile_target_to_effective(payload.get("mbdp_party_target_effective", MBDP_DEFAULTS["mbdp_party_target_effective"]))
        payload["mbdp_party_min_members"] = max(2, min(8, int(payload.get("mbdp_party_min_members", MBDP_DEFAULTS["mbdp_party_min_members"]))))
        payload["mbdp_party_min_interval_ms"] = max(1000, int(payload.get("mbdp_party_min_interval_ms", MBDP_DEFAULTS["mbdp_party_min_interval_ms"])))
        payload["mbdp_party_min_total_gain_5"] = max(0, min(60, int(payload.get("mbdp_party_min_total_gain_5", MBDP_DEFAULTS["mbdp_party_min_total_gain_5"]))))
        payload["mbdp_party_min_total_gain_10"] = max(0, min(120, int(payload.get("mbdp_party_min_total_gain_10", MBDP_DEFAULTS["mbdp_party_min_total_gain_10"]))))
        payload["mbdp_party_light_dp_threshold"] = _profile_dp_threshold_to_effective(payload.get("mbdp_party_light_dp_threshold", MBDP_DEFAULTS["mbdp_party_light_dp_threshold"]))
        payload["mbdp_party_heavy_dp_threshold"] = _profile_dp_threshold_to_effective(payload.get("mbdp_party_heavy_dp_threshold", MBDP_DEFAULTS["mbdp_party_heavy_dp_threshold"]))
        payload["mbdp_powerstone_dp_threshold"] = _profile_dp_threshold_to_effective(payload.get("mbdp_powerstone_dp_threshold", MBDP_DEFAULTS["mbdp_powerstone_dp_threshold"]))

        for spec in CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            min_key = f"min_interval_{item_key}"
            payload[min_key] = max(0, int(ini_handler.read_int(section, f"{prefix}{min_key}", int(payload.get(min_key, 0) or 0))))

        for spec in ALL_CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            selected_key = f"selected_{item_key}"
            enabled_key = f"enabled_{item_key}"
            restock_enabled_key = f"restock_enabled_{item_key}"
            restock_target_key = f"restock_target_{item_key}"
            selected_value = bool(ini_handler.read_bool(section, f"{prefix}{selected_key}", bool(payload.get(selected_key, False))))
            enabled_value = bool(ini_handler.read_bool(section, f"{prefix}{enabled_key}", bool(payload.get(enabled_key, False))))
            restock_enabled_value = bool(ini_handler.read_bool(section, f"{prefix}{restock_enabled_key}", bool(payload.get(restock_enabled_key, False))))
            default_target = int(payload.get(restock_target_key, 0) or 0)
            if (not bool(ini_handler.has_key(section, f"{prefix}{restock_target_key}"))) and selected_value and restock_enabled_value and default_target <= 0:
                default_target = int(VAULT_RESTOCK_TARGET_QTY)
            payload[selected_key] = bool(selected_value)
            payload[enabled_key] = bool(enabled_value) if bool(selected_value) else False
            payload[restock_enabled_key] = bool(restock_enabled_value)
            payload[restock_target_key] = max(0, min(2500, int(ini_handler.read_int(section, f"{prefix}{restock_target_key}", default_target))))

        for spec in ALCOHOL_ITEMS:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            selected_key = f"alcohol_selected_{item_key}"
            enabled_key = f"alcohol_enabled_{item_key}"
            restock_enabled_key = f"restock_enabled_{item_key}"
            restock_target_key = f"restock_target_{item_key}"
            selected_value = bool(ini_handler.read_bool(section, f"{prefix}{selected_key}", bool(payload.get(selected_key, False))))
            enabled_value = bool(ini_handler.read_bool(section, f"{prefix}{enabled_key}", bool(payload.get(enabled_key, False))))
            restock_enabled_value = bool(ini_handler.read_bool(section, f"{prefix}{restock_enabled_key}", bool(payload.get(restock_enabled_key, False))))
            default_target = int(payload.get(restock_target_key, 0) or 0)
            if (not bool(ini_handler.has_key(section, f"{prefix}{restock_target_key}"))) and selected_value and restock_enabled_value and default_target <= 0:
                default_target = int(VAULT_RESTOCK_TARGET_QTY)
            payload[selected_key] = bool(selected_value)
            payload[enabled_key] = bool(enabled_value) if bool(selected_value) else False
            payload[restock_enabled_key] = bool(restock_enabled_value)
            payload[restock_target_key] = max(0, min(2500, int(ini_handler.read_int(section, f"{prefix}{restock_target_key}", default_target))))

        return payload

    def _build_current_profile_payload() -> dict[str, Any]:
        payload = _profile_default_payload()
        if cfg is None:
            return payload

        for key in PROFILE_SCALAR_KEYS:
            value = getattr(cfg, key, _profile_default_scalar_value(key))
            payload[key] = bool(value) if key in PROFILE_BOOL_KEYS else int(value)

        for spec in CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if item_key:
                payload[f"min_interval_{item_key}"] = max(0, int(cfg.min_interval_ms.get(item_key, 0) or 0))

        for spec in ALL_CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            payload[f"selected_{item_key}"] = bool(cfg.selected.get(item_key, False))
            payload[f"enabled_{item_key}"] = bool(_runtime_regular_enabled(item_key))
            payload[f"restock_enabled_{item_key}"] = bool(cfg.restock_enabled_items.get(item_key, False))
            payload[f"restock_target_{item_key}"] = max(0, min(2500, int(cfg.restock_targets.get(item_key, 0) or 0)))

        for spec in ALCOHOL_ITEMS:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            payload[f"alcohol_selected_{item_key}"] = bool(cfg.alcohol_selected.get(item_key, False))
            payload[f"alcohol_enabled_{item_key}"] = bool(_runtime_alcohol_enabled(item_key))
            payload[f"restock_enabled_{item_key}"] = bool(cfg.restock_enabled_items.get(item_key, False))
            payload[f"restock_target_{item_key}"] = max(0, min(2500, int(cfg.restock_targets.get(item_key, 0) or 0)))

        return payload

    def _profile_payload_key_order() -> list[str]:
        ordered_keys: list[str] = []
        seen_keys: set[str] = set()

        def add_key(key: str):
            safe_key = str(key or "").strip()
            if not safe_key or safe_key in seen_keys:
                return
            seen_keys.add(safe_key)
            ordered_keys.append(safe_key)

        for key in PROFILE_SCALAR_KEYS:
            add_key(key)
        for spec in CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if item_key:
                add_key(f"min_interval_{item_key}")
        for spec in ALL_CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            add_key(f"selected_{item_key}")
            add_key(f"enabled_{item_key}")
            add_key(f"restock_enabled_{item_key}")
            add_key(f"restock_target_{item_key}")
        for spec in ALCOHOL_ITEMS:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            add_key(f"alcohol_selected_{item_key}")
            add_key(f"alcohol_enabled_{item_key}")
            add_key(f"restock_enabled_{item_key}")
            add_key(f"restock_target_{item_key}")

        return ordered_keys

    def _profile_payload_signature(payload: dict[str, Any]) -> str:
        defaults = _profile_default_payload()
        serialized_parts = []
        for key in _profile_payload_key_order():
            default_value = defaults.get(key, False)
            value = payload.get(key, default_value)
            if isinstance(default_value, bool):
                serialized_parts.append(f"{key}={1 if bool(value) else 0}")
            else:
                serialized_parts.append(f"{key}={int(value or 0)}")
        return hashlib.md5("\n".join(serialized_parts).encode()).hexdigest()

    def _write_profile_payload_to_section(
        config,
        section: str,
        *,
        profile_id: str,
        display_name: str,
        payload: dict[str, Any],
        created_at: str,
        updated_at: str,
    ):
        if config.has_section(section):
            config.remove_section(section)
        config.add_section(section)

        def set_profile_key(key: str, value):
            config.set(section, str(key), str(value))

        effective_created_at = str(created_at or _profile_timestamp_now())
        effective_updated_at = str(updated_at or effective_created_at or _profile_timestamp_now())
        set_profile_key("name", _profile_display_name(display_name, profile_id))
        set_profile_key("created_at", effective_created_at)
        set_profile_key("updated_at", effective_updated_at)
        for key in PROFILE_SCALAR_KEYS:
            set_profile_key(key, payload.get(key, _profile_default_scalar_value(key)))
        for spec in CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if item_key:
                set_profile_key(f"min_interval_{item_key}", int(max(0, int(payload.get(f'min_interval_{item_key}', 0) or 0))))
        for spec in ALL_CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            set_profile_key(f"selected_{item_key}", bool(payload.get(f"selected_{item_key}", False)))
            set_profile_key(f"enabled_{item_key}", bool(payload.get(f"enabled_{item_key}", False)))
            set_profile_key(f"restock_enabled_{item_key}", bool(payload.get(f"restock_enabled_{item_key}", False)))
            set_profile_key(f"restock_target_{item_key}", int(max(0, min(2500, int(payload.get(f"restock_target_{item_key}", 0) or 0)))))
        for spec in ALCOHOL_ITEMS:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            set_profile_key(f"alcohol_selected_{item_key}", bool(payload.get(f"alcohol_selected_{item_key}", False)))
            set_profile_key(f"alcohol_enabled_{item_key}", bool(payload.get(f"alcohol_enabled_{item_key}", False)))
            set_profile_key(f"restock_enabled_{item_key}", bool(payload.get(f"restock_enabled_{item_key}", False)))
            set_profile_key(f"restock_target_{item_key}", int(max(0, min(2500, int(payload.get(f"restock_target_{item_key}", 0) or 0)))))

    def _write_profile_section_to_config(
        config,
        *,
        profile_id: str,
        display_name: str,
        payload: dict[str, Any],
        created_at: str,
        updated_at: str,
    ):
        _write_profile_payload_to_section(
            config,
            _profile_section_name(profile_id),
            profile_id=profile_id,
            display_name=display_name,
            payload=payload,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _write_shared_profile_file(
        *,
        profile_id: str,
        display_name: str,
        payload: dict[str, Any],
        created_at: str,
        updated_at: str,
    ):
        profile_path = _profile_file_path(profile_id)
        if not profile_path:
            raise ValueError("Profile id is required.")
        if not _ensure_pycons_profiles_dir():
            raise OSError("Could not create the shared Pycons profiles folder.")

        handler = IniHandler(profile_path)
        config = handler.reload()
        for section_name in list(config.sections()):
            config.remove_section(section_name)
        _write_profile_payload_to_section(
            config,
            PYCONS_SHARED_PROFILE_SECTION,
            profile_id=profile_id,
            display_name=display_name,
            payload=payload,
            created_at=created_at,
            updated_at=updated_at,
        )
        _save_ini_config(handler, config)

    def _apply_profile_payload_to_live_config(config, payload: dict[str, Any], *, profile_name: str):
        if not config.has_section(INI_SECTION):
            config.add_section(INI_SECTION)

        def set_live_key(key: str, value):
            config.set(INI_SECTION, str(key), str(value))

        for key in PROFILE_SCALAR_KEYS:
            set_live_key(key, payload.get(key, _profile_default_scalar_value(key)))
        for spec in CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if item_key:
                set_live_key(f"min_interval_{item_key}", int(max(0, int(payload.get(f'min_interval_{item_key}', 0) or 0))))
        for spec in ALL_CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            selected_key = f"selected_{item_key}"
            enabled_key = f"enabled_{item_key}"
            restock_enabled_key = f"restock_enabled_{item_key}"
            restock_target_key = f"restock_target_{item_key}"
            selected_value = bool(payload.get(selected_key, False))
            set_live_key(selected_key, selected_value)
            set_live_key(enabled_key, bool(payload.get(enabled_key, False)) if selected_value else False)
            set_live_key(restock_enabled_key, bool(payload.get(restock_enabled_key, False)))
            set_live_key(restock_target_key, int(max(0, min(2500, int(payload.get(restock_target_key, 0) or 0)))))
        for spec in ALCOHOL_ITEMS:
            item_key = str(spec.get("key", "") or "")
            if not item_key:
                continue
            selected_key = f"alcohol_selected_{item_key}"
            enabled_key = f"alcohol_enabled_{item_key}"
            restock_enabled_key = f"restock_enabled_{item_key}"
            restock_target_key = f"restock_target_{item_key}"
            selected_value = bool(payload.get(selected_key, False))
            set_live_key(selected_key, selected_value)
            set_live_key(enabled_key, bool(payload.get(enabled_key, False)) if selected_value else False)
            set_live_key(restock_enabled_key, bool(payload.get(restock_enabled_key, False)))
            set_live_key(restock_target_key, int(max(0, min(2500, int(payload.get(restock_target_key, 0) or 0)))))
        set_live_key("last_applied_preset", _profile_display_name(profile_name))

    def _read_profile_record_from_path(
        profile_path: str,
        *,
        include_payload: bool = False,
        fallback_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        safe_profile_path = str(profile_path or "").strip()
        if not safe_profile_path or not os.path.isfile(safe_profile_path):
            return None

        profile_id = _profile_id_from_path(safe_profile_path)
        if not profile_id:
            return None

        handler = IniHandler(safe_profile_path)
        config = handler.reload()
        if not config.has_section(PYCONS_SHARED_PROFILE_SECTION):
            return None

        entry: dict[str, Any] = {
            "id": str(profile_id),
            "path": safe_profile_path,
            "section": PYCONS_SHARED_PROFILE_SECTION,
            "name": _profile_display_name(handler.read_key(PYCONS_SHARED_PROFILE_SECTION, "name", ""), profile_id),
            "created_at": str(handler.read_key(PYCONS_SHARED_PROFILE_SECTION, "created_at", "") or ""),
            "updated_at": str(handler.read_key(PYCONS_SHARED_PROFILE_SECTION, "updated_at", "") or ""),
        }
        if include_payload:
            payload = _read_profile_payload_from_ini(
                handler,
                PYCONS_SHARED_PROFILE_SECTION,
                fallback_payload=fallback_payload,
            )
            entry["payload"] = payload
            entry["payload_signature"] = _profile_payload_signature(payload)
        return entry

    def _read_profile_record(profile_id: str, *, include_payload: bool = False, fallback_payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
        return _read_profile_record_from_path(
            _profile_file_path(profile_id),
            include_payload=include_payload,
            fallback_payload=fallback_payload,
        )

    def _list_pycons_profiles(ini_handler = None, *, include_payload: bool = False, fallback_payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        del ini_handler
        if not _ensure_pycons_profiles_dir():
            return []

        profiles = []
        try:
            filenames = os.listdir(_PYCONS_PROFILES_DIR)
        except Exception:
            return []

        for filename in filenames:
            if not str(filename or "").lower().endswith(".ini"):
                continue
            profile_path = os.path.join(_PYCONS_PROFILES_DIR, filename)
            if not os.path.isfile(profile_path):
                continue
            try:
                entry = _read_profile_record_from_path(
                    profile_path,
                    include_payload=include_payload,
                    fallback_payload=fallback_payload,
                )
            except Exception:
                entry = None
            if entry is not None:
                profiles.append(entry)

        profiles.sort(key=lambda entry: (_profile_name_norm(entry.get("name", "")), str(entry.get("id", ""))))
        return profiles

    def _profile_selected_item_count(payload: dict[str, Any] | None) -> int:
        if payload is None:
            return 0

        total = 0
        for spec in ALL_CONSUMABLES:
            item_key = str(spec.get("key", "") or "")
            if item_key and bool(payload.get(f"selected_{item_key}", False)):
                total += 1
        for spec in ALCOHOL_ITEMS:
            item_key = str(spec.get("key", "") or "")
            if item_key and bool(payload.get(f"alcohol_selected_{item_key}", False)):
                total += 1
        return int(total)

    def _profile_summary_text(payload: dict[str, Any] | None) -> str:
        if payload is None:
            return ""

        selected_count = _profile_selected_item_count(payload)
        parts = [
            f"Team calls {'ON' if bool(payload.get('team_broadcast', False)) else 'OFF'}",
            f"Follow team calls {'ON' if bool(payload.get('team_consume_opt_in', False)) else 'OFF'}",
            f"Morale/DP {'ON' if bool(payload.get('mbdp_enabled', False)) else 'OFF'}",
            f"Alcohol {'ON' if bool(payload.get('alcohol_enabled', False)) else 'OFF'}",
            f"Auto-restock {'ON' if bool(payload.get('auto_vault_restock', False)) else 'OFF'}",
            f"{selected_count} item{'s' if selected_count != 1 else ''} selected",
        ]
        return " | ".join(parts)

    def _selected_profile_ui_context(profile_entry: dict[str, Any] | None) -> dict[str, Any] | None:
        if not profile_entry:
            return None

        profile_id = str(profile_entry.get("id", "") or "").strip()
        if not profile_id:
            return None

        detail = _read_profile_record(profile_id, include_payload=True)
        if detail is None:
            return None

        payload = dict(detail.get("payload") or _profile_default_payload())
        detail["payload"] = payload
        detail["summary_text"] = _profile_summary_text(payload)
        detail["matches_live"] = bool(
            _profile_payload_signature(payload) == _profile_payload_signature(_build_current_profile_payload())
        )
        return detail

    def _profile_existing_name_norms(ini_handler = None, *, exclude_profile_id: str = "") -> set[str]:
        existing = set()
        for profile in _list_pycons_profiles(ini_handler):
            profile_id = str(profile.get("id", "") or "")
            if exclude_profile_id and profile_id == str(exclude_profile_id):
                continue
            existing.add(_profile_name_norm(profile.get("name", "")))
        return existing

    def _profile_name_is_available(candidate: str, existing_name_norms: set[str], reserved_name_norms: set[str]) -> bool:
        candidate_norm = _profile_name_norm(candidate)
        return bool(candidate_norm) and candidate_norm not in existing_name_norms and candidate_norm not in reserved_name_norms

    def _profile_append_suffix(stem: str, suffix: str) -> str:
        safe_stem = _profile_display_name(stem)
        safe_suffix = str(suffix or "")
        if not safe_suffix:
            return safe_stem[:PROFILE_NAME_MAX_LEN]
        trimmed_stem = safe_stem[:max(1, PROFILE_NAME_MAX_LEN - len(safe_suffix))]
        return f"{trimmed_stem}{safe_suffix}"

    def _make_unique_profile_display_name(base_name: str, existing_name_norms: set[str], *, preferred_suffix: str = "") -> str:
        reserved = _profile_reserved_name_norms()
        stem = _profile_display_name(base_name)
        if not preferred_suffix and _profile_name_is_available(stem, existing_name_norms, reserved):
            return stem

        counter = 2
        suffix_base = str(preferred_suffix or "").strip()
        while True:
            if suffix_base:
                suffix = f" ({suffix_base})" if counter <= 2 else f" ({suffix_base} {counter - 1})"
            else:
                suffix = f" ({counter})"
            candidate = _profile_append_suffix(stem, suffix)
            if _profile_name_is_available(candidate, existing_name_norms, reserved):
                return candidate
            counter += 1

    def _make_duplicate_profile_display_name(source_name: str, existing_name_norms: set[str]) -> str:
        reserved = _profile_reserved_name_norms()
        stem = _profile_display_name(source_name)
        counter = 1
        while True:
            suffix = " Copy" if counter <= 1 else f" Copy {counter}"
            candidate = _profile_append_suffix(stem, suffix)
            if _profile_name_is_available(candidate, existing_name_norms, reserved):
                return candidate
            counter += 1

    def _validate_profile_display_name(profile_name: str, *, exclude_profile_id: str = "") -> tuple[bool, str, str]:
        clean_name = _compact_character_name(str(profile_name or ""))[:PROFILE_NAME_MAX_LEN]
        clean_norm = _profile_name_norm(clean_name)
        if not clean_norm:
            return False, "Profile name is required.", ""
        if clean_norm in _profile_reserved_name_norms():
            return False, "That name is reserved for a built-in quick preset.", ""
        if clean_norm in _profile_existing_name_norms(exclude_profile_id=exclude_profile_id):
            return False, "A saved profile with that name already exists.", ""
        return True, "", clean_name

    def _profiles_available_for_current_ini() -> bool:
        return not _is_generic_ini_path(_get_ini_path())

    def _generate_profile_id(display_name: str = "") -> str:
        seed = f"{display_name}|{_profile_timestamp_now()}|{os.urandom(8).hex()}"
        candidate = hashlib.md5(seed.encode()).hexdigest()[:12]
        while True:
            profile_path = _profile_file_path(candidate)
            if profile_path and not os.path.exists(profile_path):
                return candidate
            seed = f"{seed}|{os.urandom(4).hex()}"
            candidate = hashlib.md5(seed.encode()).hexdigest()[:12]

    def _profile_migration_source_suffix(ini_handler = None) -> str:
        del ini_handler
        try:
            account_email = str(Player.GetAccountEmail() or "").strip()
        except Exception:
            account_email = ""
        account_hash = _hash_account_email(account_email)
        if account_hash:
            return f"acct-{account_hash}"

        match = re.search(r"pycons_([0-9a-f]{8})\.ini$", os.path.basename(str(_get_ini_path() or "")), re.IGNORECASE)
        if match:
            return f"acct-{str(match.group(1) or '').lower()}"
        return "account"

    def _list_account_local_dynamic_profiles(ini_handler, *, fallback_payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        config = ini_handler.reload()
        profiles: list[dict[str, Any]] = []
        for section in config.sections():
            profile_id = _profile_id_from_section(section)
            if not profile_id:
                continue
            payload = _read_profile_payload_from_ini(
                ini_handler,
                section,
                fallback_payload=fallback_payload,
            )
            profiles.append(
                {
                    "id": str(profile_id),
                    "section": str(section),
                    "name": _profile_display_name(ini_handler.read_key(section, "name", ""), profile_id),
                    "created_at": str(ini_handler.read_key(section, "created_at", "") or ""),
                    "updated_at": str(ini_handler.read_key(section, "updated_at", "") or ""),
                    "payload": payload,
                    "payload_signature": _profile_payload_signature(payload),
                }
            )
        profiles.sort(key=lambda entry: (_profile_name_norm(entry.get("name", "")), str(entry.get("id", ""))))
        return profiles

    def _import_profile_record_into_shared_library(
        record: dict[str, Any],
        *,
        existing_profiles: list[dict[str, Any]],
        source_suffix: str,
        source_label: str,
    ) -> tuple[bool, bool, bool]:
        payload = dict(record.get("payload") or _profile_default_payload())
        payload_signature = str(record.get("payload_signature", "") or _profile_payload_signature(payload))
        display_name = _profile_display_name(
            record.get("name", ""),
            str(record.get("id", "") or ""),
        )
        name_norm = _profile_name_norm(display_name)

        for existing in existing_profiles:
            if _profile_name_norm(existing.get("name", "")) != name_norm:
                continue
            if str(existing.get("payload_signature", "") or "") == payload_signature:
                return False, False, True

        existing_name_norms = {_profile_name_norm(existing.get("name", "")) for existing in existing_profiles}
        final_name = display_name
        renamed = False
        if name_norm and name_norm in existing_name_norms:
            final_name = _make_unique_profile_display_name(
                display_name,
                existing_name_norms,
                preferred_suffix=source_suffix,
            )
            renamed = final_name != display_name
            if renamed:
                ConsoleLog(
                    BOT_NAME,
                    f"Renamed migrated Pycons profile '{display_name}' to '{final_name}' to avoid a shared-library name conflict ({source_label}).",
                    Console.MessageType.Info,
                )

        final_profile_id = str(record.get("id", "") or "").strip() or _generate_profile_id(final_name)
        existing_id_entry = next(
            (
                existing
                for existing in existing_profiles
                if str(existing.get("id", "") or "") == final_profile_id
            ),
            None,
        )
        if existing_id_entry is not None:
            old_profile_id = final_profile_id
            final_profile_id = _generate_profile_id(final_name)
            ConsoleLog(
                BOT_NAME,
                f"Assigned new profile id '{final_profile_id}' for migrated Pycons profile '{final_name}' because shared id '{old_profile_id}' already exists ({source_label}).",
                Console.MessageType.Info,
            )

        created_at = str(record.get("created_at", "") or "") or _profile_timestamp_now()
        updated_at = str(record.get("updated_at", "") or "") or created_at
        _write_shared_profile_file(
            profile_id=final_profile_id,
            display_name=final_name,
            payload=payload,
            created_at=created_at,
            updated_at=updated_at,
        )
        existing_profiles.append(
            {
                "id": final_profile_id,
                "name": final_name,
                "created_at": created_at,
                "updated_at": updated_at,
                "payload_signature": payload_signature,
            }
        )
        return True, renamed, False

    def _migrate_account_local_profiles_to_shared_library_if_needed(ini_handler = None) -> int:
        handler = ini_handler or _get_ini_handler()
        if _is_generic_ini_path(_get_ini_path()):
            return 0

        config = handler.reload()
        if not config.has_section(INI_SECTION):
            return 0
        if bool(handler.read_bool(INI_SECTION, PYCONS_SHARED_PROFILE_MIGRATION_FLAG_KEY, False)):
            return 0

        live_payload = _read_profile_payload_from_ini(handler, INI_SECTION)
        local_profiles = _list_account_local_dynamic_profiles(handler, fallback_payload=live_payload)
        source_records = local_profiles

        def _run_migration_locked():
            existing_shared_profiles = _list_pycons_profiles(include_payload=True)
            source_suffix = _profile_migration_source_suffix(handler)
            imported_count = 0
            renamed_count = 0
            skipped_duplicate_count = 0

            for record in source_records:
                source_label = f"account {source_suffix}"
                imported, renamed, skipped_duplicate = _import_profile_record_into_shared_library(
                    record,
                    existing_profiles=existing_shared_profiles,
                    source_suffix=source_suffix,
                    source_label=source_label,
                )
                if skipped_duplicate:
                    skipped_duplicate_count += 1
                if imported:
                    imported_count += 1
                if renamed:
                    renamed_count += 1

            return imported_count, renamed_count, skipped_duplicate_count

        imported_count, renamed_count, skipped_duplicate_count = _with_pycons_profiles_library_lock(
            _run_migration_locked,
            timeout_ms=10000,
        )

        if not config.has_section(INI_SECTION):
            config.add_section(INI_SECTION)
        config.set(INI_SECTION, PYCONS_SHARED_PROFILE_MIGRATION_FLAG_KEY, "True")
        _save_ini_config(handler, config)

        if imported_count > 0 or skipped_duplicate_count > 0:
            source_text = "account-local Pycons saved profile(s)"
            detail_parts = [f"imported {imported_count}"]
            if renamed_count > 0:
                detail_parts.append(f"renamed {renamed_count}")
            if skipped_duplicate_count > 0:
                detail_parts.append(f"skipped {skipped_duplicate_count} duplicate(s)")
            ConsoleLog(
                BOT_NAME,
                f"Shared Pycons profile migration checked {source_text}: {', '.join(detail_parts)}.",
                Console.MessageType.Info,
            )
        return int(imported_count)

    def _save_current_as_new_profile(profile_name: str) -> tuple[bool, str, str]:
        if not _profiles_available_for_current_ini():
            return False, "Saved profiles are unavailable until Pycons knows which account settings file to use.", ""

        valid, error_message, clean_name = _validate_profile_display_name(profile_name)
        if not valid:
            return False, error_message, ""

        try:
            payload = _build_current_profile_payload()
            timestamp = _profile_timestamp_now()
            def _save_new_locked():
                valid_locked, error_message_locked, clean_name_locked = _validate_profile_display_name(profile_name)
                if not valid_locked:
                    return False, error_message_locked, ""

                profile_id = _generate_profile_id(clean_name_locked)
                _write_shared_profile_file(
                    profile_id=profile_id,
                    display_name=clean_name_locked,
                    payload=payload,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
                return True, f"Saved profile '{clean_name_locked}'.", profile_id

            return _with_pycons_profiles_library_lock(
                _save_new_locked,
                timeout_ms=5000,
            )
        except Exception as exc:
            return False, f"Failed to save profile '{clean_name}': {exc}", ""

    def _save_over_profile(profile_id: str) -> tuple[bool, str]:
        if not _profiles_available_for_current_ini():
            return False, "Saved profiles are unavailable until Pycons knows which account settings file to use."

        try:
            payload = _build_current_profile_payload()
            def _save_over_locked():
                profile_entry = _read_profile_record(profile_id, include_payload=False)
                if profile_entry is None:
                    return False, "The selected profile no longer exists."

                display_name = _profile_display_name(profile_entry.get("name", ""), profile_id)
                created_at = str(profile_entry.get("created_at", "") or _profile_timestamp_now())
                _write_shared_profile_file(
                    profile_id=str(profile_id or ""),
                    display_name=display_name,
                    payload=payload,
                    created_at=created_at,
                    updated_at=_profile_timestamp_now(),
                )
                return True, f"Updated profile '{display_name}'."

            return _with_pycons_profiles_library_lock(
                _save_over_locked,
                timeout_ms=5000,
            )
        except Exception as exc:
            return False, f"Failed to overwrite the selected profile: {exc}"

    def _rename_profile(profile_id: str, profile_name: str) -> tuple[bool, str, str]:
        if not _profiles_available_for_current_ini():
            return False, "Saved profiles are unavailable until Pycons knows which account settings file to use.", ""

        valid, error_message, clean_name = _validate_profile_display_name(profile_name, exclude_profile_id=profile_id)
        if not valid:
            return False, error_message, ""

        try:
            def _rename_locked():
                profile_id_str = str(profile_id or "").strip()
                profile_entry = _read_profile_record(profile_id, include_payload=True)
                if profile_entry is None:
                    return False, "Select a saved profile first.", ""

                valid_locked, error_message_locked, clean_name_locked = _validate_profile_display_name(
                    profile_name,
                    exclude_profile_id=profile_id,
                )
                if not valid_locked:
                    return False, error_message_locked, ""

                was_active_profile = bool(
                    profile_id_str
                    and _get_active_applied_profile_id(_list_pycons_profiles()) == profile_id_str
                )
                _write_shared_profile_file(
                    profile_id=profile_id_str,
                    display_name=clean_name_locked,
                    payload=dict(profile_entry.get("payload") or _profile_default_payload()),
                    created_at=str(profile_entry.get("created_at", "") or _profile_timestamp_now()),
                    updated_at=_profile_timestamp_now(),
                )
                if was_active_profile:
                    live_applied_name = _profile_display_name(clean_name_locked, profile_id_str)
                    if cfg is not None:
                        cfg.last_applied_preset = live_applied_name
                    ini_handler = _get_ini_handler()
                    config = ini_handler.reload()
                    if not config.has_section(INI_SECTION):
                        config.add_section(INI_SECTION)
                    config.set(INI_SECTION, "last_applied_preset", live_applied_name)
                    _save_ini_config(ini_handler, config)
                return True, f"Renamed profile to '{clean_name_locked}'.", clean_name_locked

            return _with_pycons_profiles_library_lock(
                _rename_locked,
                timeout_ms=5000,
            )
        except Exception as exc:
            return False, f"Failed to rename the selected profile: {exc}", ""

    def _duplicate_profile(profile_id: str) -> tuple[bool, str, str, str]:
        if not _profiles_available_for_current_ini():
            return False, "Saved profiles are unavailable until Pycons knows which account settings file to use.", "", ""

        try:
            def _duplicate_locked():
                profile_entry = _read_profile_record(profile_id, include_payload=True)
                if profile_entry is None:
                    return False, "Select a saved profile first.", "", ""

                source_name = _profile_display_name(profile_entry.get("name", ""), profile_id)
                existing_profiles = _list_pycons_profiles()
                existing_name_norms = {
                    _profile_name_norm(existing_profile.get("name", ""))
                    for existing_profile in existing_profiles
                }
                duplicate_name = _make_duplicate_profile_display_name(source_name, existing_name_norms)
                timestamp = _profile_timestamp_now()
                duplicate_profile_id = _generate_profile_id(duplicate_name)
                _write_shared_profile_file(
                    profile_id=duplicate_profile_id,
                    display_name=duplicate_name,
                    payload=dict(profile_entry.get("payload") or _profile_default_payload()),
                    created_at=timestamp,
                    updated_at=timestamp,
                )
                return True, f"Duplicated profile '{source_name}' as '{duplicate_name}'.", duplicate_profile_id, duplicate_name

            return _with_pycons_profiles_library_lock(
                _duplicate_locked,
                timeout_ms=5000,
            )
        except Exception as exc:
            return False, f"Failed to duplicate the selected profile: {exc}", "", ""

    def _delete_profile(profile_id: str) -> tuple[bool, str]:
        if not _profiles_available_for_current_ini():
            return False, "Saved profiles are unavailable until Pycons knows which account settings file to use."

        try:
            def _delete_locked():
                profile_entry = _read_profile_record(profile_id, include_payload=False)
                if profile_entry is None:
                    return False, "The selected profile no longer exists."

                display_name = _profile_display_name(profile_entry.get("name", ""), profile_id)
                profile_path = str(profile_entry.get("path", "") or "")
                if not profile_path or not os.path.isfile(profile_path):
                    return False, "The selected profile no longer exists."
                os.remove(profile_path)
                if str(getattr(_rt, "profile_active_applied_id", "") or "") == str(profile_id or ""):
                    _set_active_applied_profile_id("")
                return True, f"Deleted profile '{display_name}'."

            return _with_pycons_profiles_library_lock(
                _delete_locked,
                timeout_ms=5000,
            )
        except Exception as exc:
            return False, f"Failed to delete the selected profile: {exc}"

    def _load_profile(profile_id: str) -> tuple[bool, str]:
        global _last_mbdp_party_ms
        if not _profiles_available_for_current_ini():
            return False, "Saved profiles are unavailable until Pycons knows which account settings file to use."

        try:
            ini_handler = _get_ini_handler()
            config = ini_handler.reload()
            live_payload = _read_profile_payload_from_ini(ini_handler, INI_SECTION)
            profile_entry = _read_profile_record(
                profile_id,
                include_payload=True,
                fallback_payload=live_payload,
            )
            if profile_entry is None:
                return False, "Select a saved profile first."

            display_name = _profile_display_name(profile_entry.get("name", ""), profile_id)
            payload = dict(profile_entry.get("payload") or live_payload)
            _apply_profile_payload_to_live_config(config, payload, profile_name=display_name)
            _save_ini_config(ini_handler, config)

            _last_mbdp_party_ms = 0
            reload_ok, reload_detail = pycons_reload_config_from_disk(reason=f"profile load: {display_name}")
            if reload_ok:
                _set_active_applied_profile_id(profile_id)
                return True, f"Loaded profile '{display_name}'."
            detail = f" {reload_detail}" if reload_detail else ""
            return False, f"Profile '{display_name}' was saved to current settings, but reload failed.{detail}"
        except Exception as exc:
            return False, f"Failed to load the selected profile: {exc}"

    def _set_item_toggle(key: str, selected: bool, enabled: bool):
        cfg.selected[key] = bool(selected)
        cfg.enabled[key] = bool(enabled)
        _rt.runtime_selected[key] = bool(selected)
        _rt.runtime_enabled[key] = bool(enabled)
        if bool(selected):
            _apply_restock_target_on_select(key)
        else:
            _apply_restock_target_on_deselect(key)

    BUILTIN_PRESET_NAMES = {
        "Solo Safe",
        "Leader - Force Team Morale",
    }

    def _mark_mbdp_preset_custom():
        if not cfg:
            return
        current = str(getattr(cfg, "last_applied_preset", "") or "")
        if current in BUILTIN_PRESET_NAMES:
            cfg.last_applied_preset = "Custom"
            cfg.mark_dirty()

    def _is_leader_force_team_morale_active() -> bool:
        if not cfg:
            return False
        expected_target = max(-60, min(10, int(getattr(cfg, "force_team_morale_value", 0))))
        return (
            bool(cfg.mbdp_enabled)
            and bool(cfg.team_broadcast)
            and (not bool(cfg.team_consume_opt_in))
            and (not bool(cfg.mbdp_allow_partywide_in_human_parties))
            and bool(cfg.mbdp_receiver_require_enabled)
            and bool(cfg.mbdp_strict_party_plus10)
            and int(cfg.mbdp_party_target_effective) == int(expected_target)
            and int(cfg.mbdp_party_min_members) == 2
            and int(cfg.mbdp_party_min_interval_ms) == 12000
        )

    def _apply_builtin_preset(key: str, announce: bool = True):
        global _last_mbdp_party_ms
        _set_active_applied_profile_id("")
        if key == "solo_safe":
            cfg.team_broadcast = False
            cfg.team_consume_opt_in = False
            cfg.mbdp_enabled = True
            cfg.mbdp_allow_partywide_in_human_parties = False
            cfg.mbdp_receiver_require_enabled = True
            cfg.mbdp_self_dp_minor_threshold = -30
            cfg.mbdp_self_dp_major_threshold = -45
            cfg.mbdp_self_morale_target_effective = 0
            cfg.mbdp_self_min_morale_gain = 4
            cfg.mbdp_party_min_members = 2
            cfg.mbdp_party_min_interval_ms = 15000
            cfg.mbdp_party_target_effective = 0
            cfg.mbdp_strict_party_plus10 = False
            cfg.mbdp_party_min_total_gain_5 = 8
            cfg.mbdp_party_min_total_gain_10 = 12
            cfg.mbdp_party_light_dp_threshold = -15
            cfg.mbdp_party_heavy_dp_threshold = -30
            cfg.mbdp_powerstone_dp_threshold = -45
            cfg.mbdp_prefer_seal_for_recharge = False
            _last_mbdp_party_ms = 0
            cfg.last_applied_preset = "Solo Safe"
            cfg.mark_dirty()
            if announce:
                _log("Applied preset: Solo Safe.", Console.MessageType.Info)
        elif key in ("leader_force_plus10_team_morale", LEADER_FORCE_PRESET_KEY):
            cfg.mbdp_enabled = True
            cfg.team_broadcast = True
            cfg.team_consume_opt_in = False
            cfg.mbdp_allow_partywide_in_human_parties = False
            cfg.mbdp_receiver_require_enabled = True
            cfg.mbdp_party_target_effective = max(-60, min(10, int(getattr(cfg, "force_team_morale_value", 0))))
            cfg.mbdp_strict_party_plus10 = True
            cfg.mbdp_party_min_members = 2
            cfg.mbdp_party_min_interval_ms = 12000
            _last_mbdp_party_ms = 0
            cfg.last_applied_preset = "Leader - Force Team Morale"
            cfg.mark_dirty()
            if announce:
                _log(
                    f"Applied preset: Leader - Force Team Morale (target={_fmt_effective(cfg.mbdp_party_target_effective)}).",
                    Console.MessageType.Info,
                )

    def _resolve_same_party_accounts_for_opt_toggle(self_email: str):
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
        me = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email)
        my_party_id = _acc_party_id(me) if me else 0
        accounts = []
        party_rows_count = 0
        if my_party_id > 0:
            for acc in all_accounts:
                if not acc:
                    continue
                if not bool(getattr(acc, "IsAccount", False)):
                    continue
                if _acc_party_id(acc) != my_party_id:
                    continue
                accounts.append(acc)
            return accounts, int(my_party_id), int(party_rows_count)

        # Fallback path when shared-memory party IDs are unavailable:
        # use live party roster names and map to shared-memory account names.
        party_rows = _get_party_player_rows()
        party_name_norms = {str(r.get("name_norm", "") or "") for r in party_rows if str(r.get("name_norm", "") or "")}
        party_rows_count = len(party_rows)
        for acc in all_accounts:
            if not acc:
                continue
            if not bool(getattr(acc, "IsAccount", False)):
                continue
            cname = _normalize_name(_acc_name(acc))
            if not cname:
                continue
            if cname in party_name_norms:
                accounts.append(acc)
        return accounts, int(my_party_id), int(party_rows_count)

    def _set_team_opt_in_for_accounts(accounts, self_email: str, opt_in: bool):
        updated = 0
        seen = set()
        toggled_names = []
        value = "True" if bool(opt_in) else "False"
        for acc in accounts:
            email = _acc_email(acc)
            if not email or email == self_email or email in seen:
                continue
            seen.add(email)
            ini = IniHandler(_resolve_account_ini_path(email, migrate_legacy=True, log_migration=False))
            ini.write_key(INI_SECTION, "team_consume_opt_in", value)
            updated += 1
            nm = _acc_name(acc)
            if nm:
                toggled_names.append(nm)
        return int(updated), toggled_names

    def _set_other_party_accounts_opt_in():
        try:
            self_email = str(Player.GetAccountEmail() or "")
            if not self_email:
                _log("Could not update team-call responses for other accounts: local account email unavailable.", Console.MessageType.Warning)
                return
            accounts, my_party_id, party_rows_count = _resolve_same_party_accounts_for_opt_toggle(self_email)
            updated, toggled_names = _set_team_opt_in_for_accounts(accounts, self_email, True)
            if updated == 0:
                cfg.last_party_opt_toggle_summary = "Team calls ON: none"
                _log(
                    f"Allowed team-call responses for 0 other party account(s). "
                    f"Detected accounts={len(accounts)} my_party_id={my_party_id} "
                    f"party_rows={party_rows_count}. No non-party accounts were modified.",
                    Console.MessageType.Warning
                )
            else:
                unique_names = sorted(set(toggled_names), key=lambda s: s.lower())
                names_str = ", ".join(unique_names) if unique_names else f"{updated} account(s)"
                cfg.last_party_opt_toggle_summary = f"Team calls ON: {names_str}"
                _log(f"Allowed team-call responses for {updated} other party account(s).", Console.MessageType.Info)
            cfg.mark_dirty()
        except Exception as e:
            _debug(f"Failed setting opt-in for other party accounts: {e}", Console.MessageType.Warning)

    def _set_other_party_accounts_opt_out():
        try:
            self_email = str(Player.GetAccountEmail() or "")
            if not self_email:
                _log("Could not update team-call responses for other accounts: local account email unavailable.", Console.MessageType.Warning)
                return
            accounts, _my_party_id_unused, _party_rows_count_unused = _resolve_same_party_accounts_for_opt_toggle(self_email)
            updated, toggled_names = _set_team_opt_in_for_accounts(accounts, self_email, False)
            if updated == 0:
                cfg.last_party_opt_toggle_summary = "Team calls OFF: none"
                _log("Blocked team-call responses for 0 other party account(s). No non-party accounts were modified.", Console.MessageType.Warning)
            else:
                unique_names = sorted(set(toggled_names), key=lambda s: s.lower())
                names_str = ", ".join(unique_names) if unique_names else f"{updated} account(s)"
                cfg.last_party_opt_toggle_summary = f"Team calls OFF: {names_str}"
                _log(f"Blocked team-call responses for {updated} other party account(s).", Console.MessageType.Info)
            cfg.mark_dirty()
        except Exception as e:
            _debug(f"Failed setting opt-out for other party accounts: {e}", Console.MessageType.Warning)

    def _refresh_local_team_flags_from_ini():
        try:
            ini = _get_ini_handler()
            new_broadcast = bool(ini.read_bool(INI_SECTION, "team_broadcast", bool(cfg.team_broadcast)))
            new_optin = bool(ini.read_bool(INI_SECTION, "team_consume_opt_in", bool(cfg.team_consume_opt_in)))
            team_flags_changed = (
                bool(cfg.team_broadcast) != bool(new_broadcast)
                or bool(cfg.team_consume_opt_in) != bool(new_optin)
            )

            # Default (legacy) behavior: always mirror local flags from INI.
            if not bool(getattr(cfg, "experimental_team_flag_sync", EXPERIMENTAL_TEAM_FLAG_SYNC_DEFAULT)):
                cfg.team_broadcast = new_broadcast
                cfg.team_consume_opt_in = new_optin
                if team_flags_changed:
                    _mark_mbdp_preset_custom()
                return

            # Experimental behavior: avoid clobbering local unsaved edits.
            if bool(getattr(cfg, "_dirty", False)):
                return

            cfg.team_broadcast = new_broadcast
            cfg.team_consume_opt_in = new_optin
            if team_flags_changed:
                _mark_mbdp_preset_custom()
        except Exception:
            pass

    # -------------------------
    # Logging
    # -------------------------
    def _log(msg, t=Console.MessageType.Info):
        ConsoleLog(BOT_NAME, msg, t)

    def _debug(msg, t=Console.MessageType.Debug):
        if cfg.debug_logging:
            _log(msg, t)

    def _model_id_value(name: str, default: int = 0) -> int:
        try:
            obj = getattr(ModelID, name, None)
            if obj is None:
                return int(default)
            return int(getattr(obj, "value", obj))
        except Exception:
            return int(default)

    def _party_item_spec(
        key: str,
        label: str,
        model_name: str,
        points: int,
        *,
        tonic: bool = False,
        guild_hall_only: bool = False,
        town_or_guild_hall_only: bool = False,
        display_cooldown_ms: int = 0,
        note: str = "",
    ) -> dict:
        spec = {
            "key": str(key),
            "label": str(label),
            "model_id": int(_model_id_value(model_name, 0)),
            "use_where": "party_items",
            "party_points": int(points),
            "default_cooldown_ms": int(PARTY_ITEM_DEFAULT_COOLDOWN_MS),
            "suppress_team_broadcast": True,
        }
        if bool(tonic):
            spec["blocked_effect_id"] = int(TONIC_TIPSINESS_EFFECT_ID)
            spec["fallback_duration_ms"] = int(TONIC_TIPSINESS_DELAY_MS)
            spec["restriction_note"] = "Waits for Tonic Tipsiness before using another tonic."
        if bool(guild_hall_only):
            spec["guild_hall_only"] = True
        if bool(town_or_guild_hall_only):
            spec["town_or_guild_hall_only"] = True
        if int(display_cooldown_ms) > 0:
            # Fireworks displays do not expose a reliable active-display flag here,
            # so Pycons waits for the display duration after one use attempt.
            spec["fallback_duration_ms"] = int(display_cooldown_ms)
        if str(note or "").strip():
            spec["restriction_note"] = str(note or "").strip()
        return spec

    # -------------------------
    # Consumables list (THIS is the working ModelID casing)
    # -------------------------
    CONSUMABLES = [
        # Conset (Explorable) - kept on top
        {"key": "armor_of_salvation", "label": "Armor of Salvation", "model_id": int(ModelID.Armor_Of_Salvation.value), "skills": ["Armor_of_Salvation_item_effect"], "use_where": "explorable"},
        {"key": "essence_of_celerity", "label": "Essence of Celerity", "model_id": int(ModelID.Essence_Of_Celerity.value), "skills": ["Essence_of_Celerity_item_effect"], "use_where": "explorable"},
        {"key": "grail_of_might", "label": "Grail of Might", "model_id": int(ModelID.Grail_Of_Might.value), "skills": ["Grail_of_Might_item_effect"], "use_where": "explorable"},

        # Explorable (alphabetical by label)
        {"key": "birthday_cupcake", "label": "Birthday Cupcake", "model_id": int(ModelID.Birthday_Cupcake.value), "skills": ["Birthday_Cupcake_skill"], "use_where": "explorable"},
        {"key": "blue_rock_candy", "label": "Blue Rock Candy", "model_id": int(_model_id_value("Blue_Rock_Candy", 0)), "skills": ["Blue_Rock_Candy_Rush"], "use_where": "explorable", "require_effect_id": True},
        {"key": "bowl_of_skalefin_soup", "label": "Bowl of Skalefin Soup", "model_id": int(ModelID.Bowl_Of_Skalefin_Soup.value), "skills": ["Skale_Vigor"], "use_where": "explorable"},
        {"key": "candy_apple", "label": "Candy Apple", "model_id": int(ModelID.Candy_Apple.value), "skills": ["Candy_Apple_skill"], "use_where": "explorable"},
        {"key": "candy_corn", "label": "Candy Corn", "model_id": int(ModelID.Candy_Corn.value), "skills": ["Candy_Corn_skill"], "use_where": "explorable"},
        {"key": "drake_kabob", "label": "Drake Kabob", "model_id": int(ModelID.Drake_Kabob.value), "skills": ["Drake_Skin"], "use_where": "explorable"},
        {"key": "golden_egg", "label": "Golden Egg", "model_id": int(ModelID.Golden_Egg.value), "skills": ["Golden_Egg_skill"], "use_where": "explorable"},
        {"key": "green_rock_candy", "label": "Green Rock Candy", "model_id": int(_model_id_value("Green_Rock_Candy", 0)), "skills": ["Green_Rock_Candy_Rush"], "use_where": "explorable", "require_effect_id": True},
        {"key": "pahnai_salad", "label": "Pahnai Salad", "model_id": int(ModelID.Pahnai_Salad.value), "skills": ["Pahnai_Salad_item_effect"], "use_where": "explorable"},
        {"key": "red_rock_candy", "label": "Red Rock Candy", "model_id": int(_model_id_value("Red_Rock_Candy", 0)), "skills": ["Red_Rock_Candy_Rush"], "use_where": "explorable", "require_effect_id": True},
        {"key": "slice_of_pumpkin_pie", "label": "Slice of Pumpkin Pie", "model_id": int(ModelID.Slice_Of_Pumpkin_Pie.value), "skills": ["Pie_Induced_Ecstasy"], "use_where": "explorable"},
        {"key": "war_supplies", "label": "War Supplies", "model_id": int(ModelID.War_Supplies.value), "skills": ["Well_Supplied"], "use_where": "explorable"},

        # Summoning (runtime priority order matches existing botting summon upkeep)
        {"key": "legionnaire_summoning_crystal", "label": "Legionnaire Summoning Crystal", "model_id": int(_model_id_value("Legionnaire_Summoning_Crystal", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "igneous_summoning_stone", "label": "Igneous Summoning Stone", "model_id": int(_model_id_value("Igneous_Summoning_Stone", 0)), "use_where": "summoning", "summon_duration_ms": IGNEOUS_SUMMON_DURATION_MS},
        {"key": "amber_summoning_stone", "label": "Amber Summoning Stone", "model_id": int(_model_id_value("Amber_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "arctic_summoning_stone", "label": "Arctic Summoning Stone", "model_id": int(_model_id_value("Arctic_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "automaton_summoning_stone", "label": "Automaton Summoning Stone", "model_id": int(_model_id_value("Automaton_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "celestial_summoning_stone", "label": "Celestial Summoning Stone", "model_id": int(_model_id_value("Celestial_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "chitinous_summoning_stone", "label": "Chitinous Summoning Stone", "model_id": int(_model_id_value("Chitinous_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "demonic_summoning_stone", "label": "Demonic Summoning Stone", "model_id": int(_model_id_value("Demonic_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "fossilized_summoning_stone", "label": "Fossilized Summoning Stone", "model_id": int(_model_id_value("Fossilized_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "frosty_summoning_stone", "label": "Frosty Summoning Stone", "model_id": int(_model_id_value("Frosty_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "gelatinous_summoning_stone", "label": "Gelatinous Summoning Stone", "model_id": int(_model_id_value("Gelatinous_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "ghastly_summoning_stone", "label": "Ghastly Summoning Stone", "model_id": int(_model_id_value("Ghastly_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "imperial_guard_reinforcement_order", "label": "Imperial Guard Reinforcement Order", "model_id": int(_model_id_value("Imperial_Guard_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "jadeite_summoning_stone", "label": "Jadeite Summoning Stone", "model_id": int(_model_id_value("Jadeite_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "mercantile_summoning_stone", "label": "Mercantile Summoning Stone", "model_id": int(_model_id_value("Merchant_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "mischievous_summoning_stone", "label": "Mischievous Summoning Stone", "model_id": int(_model_id_value("Mischievous_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "mysterious_summoning_stone", "label": "Mysterious Summoning Stone", "model_id": int(_model_id_value("Mysterious_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "mystical_summoning_stone", "label": "Mystical Summoning Stone", "model_id": int(_model_id_value("Mystical_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "shining_blade_war_horn", "label": "Shining Blade War Horn", "model_id": int(_model_id_value("Shining_Blade_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "tengu_support_flare", "label": "Tengu Support Flare", "model_id": int(_model_id_value("Tengu_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},
        {"key": "zaishen_summoning_stone", "label": "Zaishen Summoning Stone", "model_id": int(_model_id_value("Zaishen_Summon", 0)), "use_where": "summoning", "summon_duration_ms": SUMMONING_STONE_DURATION_MS},

        # Outpost-only (alphabetical by label)
        {"key": "chocolate_bunny", "label": "Chocolate Bunny", "model_id": int(_model_id_value("Chocolate_Bunny", 0)), "skills": ["Sugar_Jolt_(long)"], "effect_id": SUGAR_JOLT_LONG_EFFECT_ID, "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": SUGAR_JOLT_LONG_MS},
        {"key": "creme_brulee", "label": "Crème Brûlée", "model_id": int(_model_id_value("Creme_Brulee", 0)), "skills": ["Sugar_Jolt_(long)"], "effect_id": SUGAR_JOLT_LONG_EFFECT_ID, "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": SUGAR_JOLT_LONG_MS},
        {"key": "fruitcake", "label": "Fruitcake", "model_id": int(_model_id_value("Fruitcake", 0)), "skills": ["Sugar_Rush_(medium)"], "effect_id": SUGAR_RUSH_MEDIUM_EFFECT_ID, "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": SUGAR_RUSH_MEDIUM_MS},
        {"key": "jar_of_honey", "label": "Jar of Honey", "model_id": int(_model_id_value("Jar_Of_Honey", 0)), "skills": ["Sugar_Rush_(long)"], "effect_id": SUGAR_RUSH_LONG_EFFECT_ID, "use_where": "outpost", "require_effect_id": False, "fallback_duration_ms": SUGAR_RUSH_LONG_MS},
        {"key": "red_bean_cake", "label": "Red Bean Cake", "model_id": int(_model_id_value("Red_Bean_Cake", 0)), "skills": ["Sugar_Rush_(medium)"], "effect_id": SUGAR_RUSH_MEDIUM_EFFECT_ID, "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": SUGAR_RUSH_MEDIUM_MS},
        {"key": "sugary_blue_drink", "label": "Sugary Blue Drink", "model_id": int(_model_id_value("Sugary_Blue_Drink", 0)), "skills": ["Sugar_Jolt_(short)"], "effect_id": SUGAR_JOLT_SHORT_EFFECT_ID, "use_where": "outpost", "require_effect_id": False, "fallback_duration_ms": SUGAR_JOLT_SHORT_MS},

        # Party Items (Party Animal title points). Most are safe to use repeatedly.
        _party_item_spec("bottle_rocket", "Bottle Rocket", "Bottle_Rocket", 1),
        _party_item_spec("champagne_popper", "Champagne Popper", "Champagne_Popper", 1),
        _party_item_spec("ghost_in_the_box", "Ghost-in-the-Box", "Ghost_In_The_Box", 1),
        _party_item_spec("snowman_summoner", "Snowman Summoner", "Snowman_Summoner", 1),
        _party_item_spec("sparkler", "Sparkler", "Sparkler", 1),
        _party_item_spec("squash_serum", "Squash Serum", "Squash_Serum", 1),
        _party_item_spec("beetle_juice_tonic", "Beetle Juice Tonic", "Beetle_Juice_Tonic", 2, tonic=True),
        _party_item_spec("cottontail_tonic", "Cottontail Tonic", "Cottontail_Tonic", 2, tonic=True),
        _party_item_spec("frosty_tonic", "Frosty Tonic", "Frosty_Tonic", 2, tonic=True),
        _party_item_spec("mischievous_tonic", "Mischievous Tonic", "Mischievious_Tonic", 2, tonic=True),
        _party_item_spec("sinister_automatonic", "Sinister Automatonic", "Sinister_Automatonic_Tonic", 2, tonic=True),
        _party_item_spec("transmogrifier_tonic", "Transmogrifier Tonic", "Transmogrifier_Tonic", 2, tonic=True),
        _party_item_spec("yuletide_tonic", "Yuletide Tonic", "Yuletide_Tonic", 2, tonic=True),
        _party_item_spec("cerebral_tonic", "Cerebral Tonic", "Cerebral_Tonic", 2, tonic=True),
        _party_item_spec("searing_tonic", "Searing Tonic", "Searing_Tonic", 2, tonic=True),
        _party_item_spec("abyssal_tonic", "Abyssal Tonic", "Abyssal_Tonic", 2, tonic=True),
        _party_item_spec("unseen_tonic", "Unseen Tonic", "Unseen_Tonic", 2, tonic=True),
        _party_item_spec("phantasmal_tonic", "Phantasmal Tonic", "Phantasmal_Tonic", 2, tonic=True),
        _party_item_spec("automatonic", "Automatonic", "Automatonic_Tonic", 2, tonic=True),
        _party_item_spec("boreal_tonic", "Boreal Tonic", "Boreal_Tonic", 2, tonic=True),
        _party_item_spec("trapdoor_tonic", "Trapdoor Tonic", "Trapdoor_Tonic", 2, tonic=True),
        _party_item_spec("macabre_tonic", "Macabre Tonic", "Macabre_Tonic", 2, tonic=True),
        _party_item_spec("skeletonic", "Skeletonic", "Skeletonic_Tonic", 2, tonic=True),
        _party_item_spec("gelatinous_tonic", "Gelatinous Tonic", "Gelatinous_Tonic", 2, tonic=True),
        _party_item_spec("abominable_tonic", "Abominable Tonic", "Abominable_Tonic", 2, tonic=True),
        _party_item_spec(
            "crate_of_fireworks",
            "Crate of Fireworks",
            "Crate_Of_Fireworks",
            3,
            guild_hall_only=True,
            display_cooldown_ms=CRATE_FIREWORKS_DISPLAY_MS,
            note="Only used in a guild hall, then waits while the fireworks display is active.",
        ),
        _party_item_spec("minutely_mad_king_tonic", "Minutely Mad King Tonic", "Minutely_Mad_King_Tonic", 3, tonic=True),
        _party_item_spec("zaishen_tonic", "Zaishen Tonic", "Zaishen_Tonic", 3, tonic=True),
        _party_item_spec("mysterious_tonic", "Mysterious Tonic", "Mysterious_Tonic", 5, tonic=True),
        _party_item_spec(
            "disco_ball",
            "Disco Ball",
            "Disco_Ball",
            7,
            town_or_guild_hall_only=True,
            display_cooldown_ms=DISCO_BALL_DISPLAY_MS,
            note="Only used in towns, outposts, or guild halls, then waits while the display is active.",
        ),
        _party_item_spec("spooky_tonic", "Spooky Tonic", "Spooky_Tonic", 25, tonic=True),
        _party_item_spec("party_beacon", "Party Beacon", "Party_Beacon", 50),
    ]

    SUMMONING_ITEMS = [c for c in CONSUMABLES if str(c.get("use_where", "")).lower() == "summoning"]
    SWEET_ITEMS = [c for c in CONSUMABLES if str(c.get("use_where", "")).lower() == "outpost"]
    PARTY_ITEMS = [c for c in CONSUMABLES if str(c.get("use_where", "")).lower() == "party_items"]

    MB_DP_ITEMS = [
        # Self-only morale
        {"key": "pumpkin_cookie", "label": "Pumpkin Cookie", "model_id": int(_model_id_value("Pumpkin_Cookie", 0)), "use_where": "mbdp"},
        {"key": "seal_of_the_dragon_empire", "label": "Seal of the Dragon Empire", "model_id": int(_model_id_value("Seal_Of_The_Dragon_Empire", 0)), "use_where": "mbdp"},

        # Party morale
        {"key": "honeycomb", "label": "Honeycomb", "model_id": int(_model_id_value("Honeycomb", int(ModelID.Honeycomb.value))), "use_where": "mbdp"},
        {"key": "rainbow_candy_cane", "label": "Rainbow Candy Cane", "model_id": int(_model_id_value("Rainbow_Candy_Cane", 0)), "use_where": "mbdp"},
        {"key": "elixir_of_valor", "label": "Elixir of Valor", "model_id": int(_model_id_value("Elixir_Of_Valor", 0)), "use_where": "mbdp"},
        {"key": "powerstone_of_courage", "label": "Powerstone of Courage", "model_id": int(_model_id_value("Powerstone_Of_Courage", 0)), "use_where": "mbdp"},

        # Self-only DP
        {"key": "refined_jelly", "label": "Refined Jelly", "model_id": int(_model_id_value("Refined_Jelly", 0)), "use_where": "mbdp"},
        {"key": "wintergreen_candy_cane", "label": "Wintergreen Candy Cane", "model_id": int(_model_id_value("Wintergreen_Candy_Cane", 0)), "use_where": "mbdp"},
        {"key": "peppermint_candy_cane", "label": "Peppermint Candy Cane", "model_id": int(_model_id_value("Peppermint_Candy_Cane", 0)), "use_where": "mbdp"},

        # Party DP
        {"key": "four_leaf_clover", "label": "Four-Leaf Clover", "model_id": int(_model_id_value("Four_Leaf_Clover", 0)), "use_where": "mbdp"},
        {"key": "oath_of_purity", "label": "Oath of Purity", "model_id": int(_model_id_value("Oath_Of_Purity", 0)), "use_where": "mbdp"},
    ]

    ALL_CONSUMABLES = CONSUMABLES + MB_DP_ITEMS
    ALL_BY_KEY = {c["key"]: c for c in ALL_CONSUMABLES}
    SUMMONING_BY_KEY = {c["key"]: c for c in SUMMONING_ITEMS}
    SWEET_ITEMS_BY_KEY = {c["key"]: c for c in SWEET_ITEMS}
    PARTY_ITEMS_BY_KEY = {c["key"]: c for c in PARTY_ITEMS}
    MB_DP_BY_KEY = {c["key"]: c for c in MB_DP_ITEMS}
    CONSET_KEYS = {"armor_of_salvation", "essence_of_celerity", "grail_of_might"}
    MBDP_PARTY_KEYS = frozenset({
        "elixir_of_valor",
        "four_leaf_clover",
        "honeycomb",
        "oath_of_purity",
        "powerstone_of_courage",
        "rainbow_candy_cane",
    })
    MBDP_SELF_KEYS = frozenset({
        "peppermint_candy_cane",
        "pumpkin_cookie",
        "refined_jelly",
        "seal_of_the_dragon_empire",
        "wintergreen_candy_cane",
    })

    # Central MB/DP defaults (player-friendly effective scale)
    MBDP_DEFAULTS = {
        "mbdp_enabled": True,
        "mbdp_allow_partywide_in_human_parties": False,
        "mbdp_receiver_require_enabled": True,
        "mbdp_self_dp_minor_threshold": -30,
        "mbdp_self_dp_major_threshold": -45,
        "mbdp_self_morale_target_effective": 0,
        "mbdp_self_min_morale_gain": 4,
        "mbdp_party_min_members": 2,
        "mbdp_party_min_interval_ms": 15000,
        "mbdp_party_target_effective": 0,
        "mbdp_strict_party_plus10": False,
        "mbdp_party_min_total_gain_5": 8,
        "mbdp_party_min_total_gain_10": 12,
        "mbdp_party_light_dp_threshold": -15,
        "mbdp_party_heavy_dp_threshold": -30,
        "mbdp_powerstone_dp_threshold": -45,
        "mbdp_prefer_seal_for_recharge": False,
        "force_team_morale_value": 0,
    }

    # -------------------------
    # Alcohol items
    # -------------------------
    ALCOHOL_ITEMS = [
        {"key": "aged_dwarven_ale", "label": "Aged Dwarven Ale", "model_id": int(_model_id_value("Aged_Dwarven_Ale", 0)), "drunk_add": 5, "use_where": "both"},
        {"key": "aged_hunters_ale", "label": "Aged Hunter's Ale", "model_id": int(_model_id_value("Aged_Hunters_Ale", 0)), "drunk_add": 5, "use_where": "both"},
        {"key": "battle_isle_iced_tea", "label": "Battle Isle Iced Tea", "model_id": int(_model_id_value("Battle_Isle_Iced_Tea", 0)), "drunk_add": 5, "use_where": "both"},
        {"key": "bottle_of_grog", "label": "Bottle of Grog", "model_id": int(_model_id_value("Bottle_Of_Grog", 0)), "drunk_add": 5, "use_where": "both", "skills": ["Yo_Ho_Ho_and_a_Bottle_of_Grog"]},
        {"key": "bottle_of_juniberry_gin", "label": "Bottle of Juniberry Gin", "model_id": int(_model_id_value("Bottle_Of_Juniberry_Gin", 0)), "drunk_add": 1, "use_where": "both"},
        {"key": "bottle_of_rice_wine", "label": "Bottle of Rice Wine", "model_id": int(_model_id_value("Bottle_Of_Rice_Wine", 0)), "drunk_add": 1, "use_where": "both"},
        {"key": "bottle_of_vabbian_wine", "label": "Bottle of Vabbian Wine", "model_id": int(_model_id_value("Bottle_Of_Vabbian_Wine", 0)), "drunk_add": 1, "use_where": "both"},
        {"key": "dwarven_ale", "label": "Dwarven Ale", "model_id": int(_model_id_value("Dwarven_Ale", 0)), "drunk_add": 3, "use_where": "both"},
        {"key": "eggnog", "label": "Eggnog", "model_id": int(_model_id_value("Eggnog", 0)), "drunk_add": 1, "use_where": "both"},
        {"key": "flask_of_firewater", "label": "Flask of Firewater", "model_id": int(_model_id_value("Flask_Of_Firewater", 0)), "drunk_add": 5, "use_where": "both"},
        {"key": "hard_apple_cider", "label": "Hard Apple Cider", "model_id": int(_model_id_value("Hard_Apple_Cider", 0)), "drunk_add": 1, "use_where": "both"},
        {"key": "hunters_ale", "label": "Hunters Ale", "model_id": int(_model_id_value("Hunters_Ale", 0)), "drunk_add": 3, "use_where": "both"},
        {"key": "keg_of_aged_hunters_ale", "label": "Keg of Aged Hunter's Ale", "model_id": int(_model_id_value("Keg_Of_Aged_Hunters_Ale", 0)), "drunk_add": 5, "use_where": "both"},
        {"key": "krytan_brandy", "label": "Krytan Brandy", "model_id": int(_model_id_value("Krytan_Brandy", 0)), "drunk_add": 5, "use_where": "both"},
        {"key": "shamrock_ale", "label": "Shamrock Ale", "model_id": int(_model_id_value("Shamrock_Ale", 0)), "drunk_add": 1, "use_where": "both"},
        {"key": "spiked_eggnog", "label": "Spiked Eggnog", "model_id": int(_model_id_value("Spiked_Eggnog", 0)), "drunk_add": 5, "use_where": "both"},
        {"key": "vial_of_absinthe", "label": "Vial of Absinthe", "model_id": int(_model_id_value("Vial_Of_Absinthe", 0)), "drunk_add": 1, "use_where": "both"},
        {"key": "witchs_brew", "label": "Witchs Brew", "model_id": int(_model_id_value("Witchs_Brew", 0)), "drunk_add": 1, "use_where": "both"},
        {"key": "zehtukas_jug", "label": "Zehtukas Jug", "model_id": int(_model_id_value("Zehtukas_Jug", 0)), "drunk_add": 5, "use_where": "both"},
    ]
    ALCOHOL_BY_KEY = {a["key"]: a for a in ALCOHOL_ITEMS}
    PYCONS_SYNC_CATEGORY_ALCOHOL = "alcohol_settings"
    PYCONS_SYNC_CATEGORY_MOVEMENT_SAFETY = "movement_safety_settings"
    PYCONS_SYNC_CATEGORY_MBDP = "mbdp_settings"
    PYCONS_SYNC_CATEGORY_RESTOCK = "restock_settings"
    PYCONS_SYNC_CATEGORY_SELECTION = "main_window_selection"
    PYCONS_SYNC_CATEGORY_DEFS = [
        (PYCONS_SYNC_CATEGORY_ALCOHOL, "Alcohol/Party & Sweets settings"),
        (PYCONS_SYNC_CATEGORY_MOVEMENT_SAFETY, "Movement safety settings"),
        (PYCONS_SYNC_CATEGORY_MBDP, "Morale Boost & Death Penalty settings"),
        (PYCONS_SYNC_CATEGORY_RESTOCK, "Restock settings"),
        (PYCONS_SYNC_CATEGORY_SELECTION, "Select consumables to show in main window"),
    ]
    PYCONS_SYNC_ALCOHOL_SCALAR_KEYS = [
        "alcohol_enabled",
        "alcohol_disable_effect",
        "alcohol_fast_spending",
        "alcohol_fast_interval_ms",
        "sweets_fast_spending",
        "sweets_fast_interval_ms",
        "alcohol_use_explorable",
        "alcohol_use_outpost",
        "alcohol_target_level",
        "alcohol_preference",
        "party_item_interval_ms",
    ]
    PYCONS_SYNC_MOVEMENT_SAFETY_SCALAR_KEYS = [
        "movement_safety_window_ms",
        "movement_party_items_fast_threshold_ms",
        "movement_require_explorable",
        "movement_require_summoning",
        "movement_require_mbdp",
        "movement_require_alcohol",
        "movement_require_party_items",
        "movement_require_sweets",
        "movement_alcohol_fast_only",
        "movement_party_items_speed_only",
        "movement_sweets_fast_only",
    ]
    PYCONS_SYNC_MBDP_SCALAR_KEYS = [
        "mbdp_enabled",
        "mbdp_allow_partywide_in_human_parties",
        "mbdp_receiver_require_enabled",
        "mbdp_prefer_seal_for_recharge",
        "mbdp_self_dp_minor_threshold",
        "mbdp_self_dp_major_threshold",
        "mbdp_self_morale_target_effective",
        "mbdp_self_min_morale_gain",
        "mbdp_party_min_members",
        "mbdp_party_min_interval_ms",
        "mbdp_party_target_effective",
        "mbdp_strict_party_plus10",
        "mbdp_party_min_total_gain_5",
        "mbdp_party_min_total_gain_10",
        "mbdp_party_light_dp_threshold",
        "mbdp_party_heavy_dp_threshold",
        "mbdp_powerstone_dp_threshold",
        "force_team_morale_value",
    ]
    PYCONS_SYNC_RESTOCK_SCALAR_KEYS = [
        "auto_vault_restock",
        "restock_keep_target_on_deselect",
        "restock_interval_ms",
        "restock_mode",
        "restock_move_cap_per_cycle",
    ]
    CONSUMABLE_TOOLTIPS = {
        "armor_of_salvation": "Grant your party members immunity to 50% of critical hits, +10 armor, +1 Health regeneration, and damage reduction of 5 for the next 30 minutes.",
        "birthday_cupcake": "For 30 minutes, your maximum Health is increased by 100, your maximum energy is increased by 10, and your movement speed is increased by 25%.",
        "blue_rock_candy": "You move and attack 25% faster and your skill activation times are reduced by 20% for the next 30 minutes.",
        "bowl_of_skalefin_soup": "For 30 minutes you have +1 Health regeneration.",
        "candy_apple": "For 30 minutes, your maximum Health is increased by 100 and your maximum Energy is increased by 10.",
        "candy_corn": "For 30 minutes, all of your attributes are raised by 1.",
        "chocolate_bunny": "For 5 minutes, you move 50% faster.",
        "creme_brulee": "For 10 minutes, you move 25% faster.",
        "drake_kabob": "For 30 minutes you have +5 armor.",
        "elixir_of_valor": "Grant your party members a 10% morale boost",
        "essence_of_celerity": "Grant your party members 20% faster movement and attack speeds, and to reduce their skill activation and recharge times by 20% for the next 30 minutes.",
        "four_leaf_clover": "Remove a random amount of DP (5%-15%) from your entire party. If 15% DP is removed, you gain 4 points towards the Lucky title track.",
        "fruitcake": "For 5 minutes you run 25% faster.",
        "golden_egg": "For 30 minutes, all of your attributes are raised by 1.",
        "grail_of_might": "Grants your party members +100 maximum health, +10 maximum energy, and +1 to all of their attributes for 30 minutes.",
        "green_rock_candy": "You move and attack 15% faster and your skill activation times are reduced by 15% for the next 30 minutes.",
        "honeycomb": "Give your party a 5% morale boost. This morale boost does not cause skills to instantly recharge.",
        "jar_of_honey": "For 10 minutes, you move 25% faster.",
        "oath_of_purity": "Remove 15% of all party member's Death Penalty.",
        "pahnai_salad": "For 30 minutes you have +20 maximum Health.",
        "peppermint_candy_cane": "Remove all Death Penalty from yourself",
        "powerstone_of_courage": "Remove all Death Penalty from your party. Your entire party then receives a 10% Morale Boost.",
        "pumpkin_cookie": "Give yourself a 10% morale boost.",
        "rainbow_candy_cane": "Give your party a 5% morale boost. This morale boost does not cause skills to instantly recharge.",
        "red_bean_cake": "For 5 minutes you run 25% faster.",
        "red_rock_candy": "You move and attack 33% faster and your skill activation times are reduced by 25% for the next 30 minutes.",
        "refined_jelly": "Remove 15% of your Death Penalty.",
        "seal_of_the_dragon_empire": "Give yourself a 10% morale boost.",
        "slice_of_pumpkin_pie": "You attack 25% faster and your skill activation times are reduced by 15% for the next 30 minutes.",
        "sugary_blue_drink": "For 2 minutes, you move 50% faster.",
        "war_supplies": "For 30 minutes, you have +5 armor and +1 Health Regeneration.",
        "wintergreen_candy_cane": "Remove 15% of your Death Penalty.",
    }

    def _party_points_text(points: int) -> str:
        pts = int(points or 0)
        return f"{pts} point" if pts == 1 else f"{pts} points"

    def _consumable_tooltip_text(key: str) -> str:
        tooltip = str(CONSUMABLE_TOOLTIPS.get(str(key or ""), "") or "").strip()
        if tooltip:
            return tooltip
        party_spec = PARTY_ITEMS_BY_KEY.get(str(key or ""))
        if party_spec:
            points_text = _party_points_text(int(party_spec.get("party_points", 0) or 0))
            note = str(party_spec.get("restriction_note", "") or "").strip()
            base = f"Adds {points_text} toward the Party Animal title."
            if note:
                return f"{base} {note}"
            return base
        summon_spec = SUMMONING_BY_KEY.get(str(key or ""))
        if summon_spec:
            duration_ms = int(summon_spec.get("summon_duration_ms", SUMMONING_STONE_DURATION_MS) or SUMMONING_STONE_DURATION_MS)
            duration_minutes = max(1, int(round(float(duration_ms) / 60000.0)))
            return (
                f"Summons an allied creature to assist you for up to {duration_minutes} minutes. "
                "Using a summoning item applies Summoning Sickness for 10 minutes. "
                "Do not use while Summoning Sickness is active or while another summoned ally is already present."
            )
        return "No description available."

    def _consumable_tooltip_with_label(key: str, label: str) -> str:
        base_label = str(label or "").strip()
        extra = str(_consumable_tooltip_text(key) or "").strip()
        if extra and extra != "No description available.":
            return f"{base_label}\n{extra}" if base_label else extra
        return base_label if base_label else extra

    def _normalize_icon_name(value: str) -> str:
        txt = str(value or "")
        txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
        txt = txt.lower().replace("&", " and ")
        txt = re.sub(r"[^a-z0-9]+", " ", txt)
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt

    def _singularize_token(tok: str) -> str:
        t = str(tok or "").strip()
        if len(t) > 4 and t.endswith("ies"):
            return t[:-3] + "y"
        if len(t) > 4 and t.endswith("es"):
            return t[:-2]
        if len(t) > 3 and t.endswith("s"):
            return t[:-1]
        return t

    def _icon_tokens(value: str) -> set[str]:
        stop = {"of", "the", "and", "a", "an", "item", "items"}
        norm = _normalize_icon_name(value)
        if not norm:
            return set()
        out = set()
        for tok in norm.split(" "):
            if not tok or tok in stop:
                continue
            out.add(tok)
            out.add(_singularize_token(tok))
        return {t for t in out if t}

    def _candidate_name_variants(stem: str) -> list[str]:
        raw = str(stem or "")
        out = [raw]
        # Item model textures commonly use "<id>-Item_Name".
        if "-" in raw:
            left, right = raw.split("-", 1)
            if left.isdigit() and right:
                out.append(right)
        return out

    def _icon_dir_priority(rel_path_lc: str) -> int:
        rp = str(rel_path_lc or "").replace("/", "\\")
        preferred_scores = (300, 260, 180)
        for idx, base in enumerate(_ICON_PREFERRED_ROOTS):
            base_lc = str(base).replace("/", "\\").lower()
            if base_lc and base_lc in rp:
                return preferred_scores[idx]
        if "\\textures\\" in rp:
            return 40
        return 0

    def _to_texture_path(full_path: str) -> str:
        try:
            rel = os.path.relpath(full_path, os.getcwd())
            return rel.replace("/", "\\")
        except Exception:
            return str(full_path or "").replace("/", "\\")

    def _existing_icon_search_roots() -> list[str]:
        existing = []
        seen = set()
        for base in _ICON_PREFERRED_ROOTS:
            try:
                abs_base = os.path.abspath(str(base or ""))
            except Exception:
                continue
            if not abs_base or not os.path.isdir(abs_base):
                continue
            norm_lc = os.path.normpath(abs_base).replace("\\", "/").lower()
            if norm_lc in seen:
                continue
            seen.add(norm_lc)
            existing.append(abs_base)

        # Collapse nested roots so parent scans cover child folders once.
        collapsed = []
        collapsed_lc = []
        for root in sorted(existing, key=lambda p: len(os.path.normpath(p))):
            root_lc = os.path.normpath(root).replace("\\", "/").lower()
            if any(root_lc == prev or root_lc.startswith(prev + "/") for prev in collapsed_lc):
                continue
            collapsed.append(root)
            collapsed_lc.append(root_lc)
        return collapsed

    def _scan_icon_candidates(search_roots: list[str]) -> list[dict]:
        candidates = []
        seen_paths = set()
        for root in list(search_roots or []):
            for dirpath, _dirnames, filenames in os.walk(root):
                _dirnames.sort()
                filenames.sort()
                for filename in filenames:
                    if not str(filename).lower().endswith(".png"):
                        continue
                    full_path = os.path.join(dirpath, filename)
                    rel_path = _to_texture_path(full_path)
                    rel_lc = rel_path.lower()
                    if rel_lc in seen_paths:
                        continue
                    seen_paths.add(rel_lc)
                    stem = os.path.splitext(filename)[0]
                    variants = _candidate_name_variants(stem)
                    tokens = set()
                    norm_variants = set()
                    for variant in variants:
                        tokens.update(_icon_tokens(variant))
                        n = _normalize_icon_name(variant)
                        if n:
                            norm_variants.add(n)
                    if not tokens:
                        continue
                    candidates.append({
                        "path": rel_path,
                        "tokens": tokens,
                        "norm_variants": norm_variants,
                        "priority": _icon_dir_priority(rel_lc),
                        "path_lc": rel_lc,
                    })
        return candidates

    def _build_icon_candidates():
        preferred_roots = _existing_icon_search_roots()
        candidates = _scan_icon_candidates(preferred_roots)
        if candidates:
            return candidates
        root = os.path.abspath(_ICON_SEARCH_ROOT)
        return _scan_icon_candidates([root])

    def _icon_match_profile(key: str, label: str) -> dict:
        key_norm = _normalize_icon_name(key.replace("_", " "))
        label_norm = _normalize_icon_name(label)
        key_tokens = _icon_tokens(key)
        label_tokens = _icon_tokens(label)
        wanted = set(key_tokens) | set(label_tokens)
        for alias in CONSUMABLE_ICON_NAME_ALIASES.get(str(key or ""), ()):
            wanted.update(_icon_tokens(alias))
        return {
            "key_norm": key_norm,
            "label_norm": label_norm,
            "key_tokens": key_tokens,
            "label_tokens": label_tokens,
            "wanted": wanted,
        }

    def _score_icon_candidate(key: str, label: str, cand: dict, profile=None) -> int:
        if profile is None:
            profile = _icon_match_profile(key, label)
        key_norm = str(profile.get("key_norm", "") or "")
        label_norm = str(profile.get("label_norm", "") or "")
        key_tokens = set(profile.get("key_tokens", set()) or set())
        label_tokens = set(profile.get("label_tokens", set()) or set())
        wanted = set(profile.get("wanted", set()) or set())
        if not wanted:
            return -1
        cand_tokens = set(cand.get("tokens", set()) or set())
        overlap = wanted.intersection(cand_tokens)
        if not overlap:
            return -1
        strong_overlap = [t for t in overlap if len(t) >= 4]
        score = int(cand.get("priority", 0))
        score += len(overlap) * 7
        score += len(strong_overlap) * 11
        cand_norms = set(cand.get("norm_variants", set()) or set())
        if key_norm in cand_norms:
            score += 160
        if label_norm in cand_norms:
            score += 160
        if key_tokens and key_tokens.issubset(cand_tokens):
            score += 80
        if label_tokens and label_tokens.issubset(cand_tokens):
            score += 70
        if "\\textures\\consumables\\" in str(cand.get("path_lc", "")):
            score += 20
        return score

    def _resolve_consumable_icon_path(key: str, label: str) -> str:
        global _icon_candidates_cache, _icon_path_by_key_cache
        k = str(key or "")
        if not k:
            return ""
        if k in _icon_path_by_key_cache:
            return str(_icon_path_by_key_cache.get(k, "") or "")
        override_filename = str(CONSUMABLE_ICON_FILE_OVERRIDES.get(k, "") or "").strip()
        if override_filename:
            for base in _ICON_PREFERRED_ROOTS:
                override_path = os.path.normpath(os.path.join(base, override_filename))
                if os.path.exists(override_path):
                    _icon_path_by_key_cache[k] = override_path.replace("/", "\\")
                    return str(_icon_path_by_key_cache[k] or "")
        if _icon_candidates_cache is None:
            _icon_candidates_cache = _build_icon_candidates()
        profile = _icon_match_profile(k, label)
        best_score = -1
        best_path = ""
        for cand in _icon_candidates_cache:
            score = _score_icon_candidate(k, label, cand, profile)
            if score > best_score:
                best_score = score
                best_path = str(cand.get("path", "") or "")
            elif score == best_score and score >= 0:
                cand_path = str(cand.get("path", "") or "")
                if cand_path and (not best_path or cand_path < best_path):
                    best_path = cand_path
        if best_score < 50:
            best_path = ""
        _icon_path_by_key_cache[k] = best_path
        return best_path

    def _draw_icon_toggle_or_checkbox(
        state_now: bool,
        key: str,
        label: str,
        id_prefix: str,
        icon_size: float = 20.0,
        highlight_selected_box: bool = False,
    ):
        tooltip_text = _consumable_tooltip_with_label(key, label)
        icon_path = _resolve_consumable_icon_path(key, label)
        current = bool(state_now)
        if icon_path:
            pushed_alpha = False
            pushed_colors = 0
            try:
                try:
                    # Keep icon backing dark by default; use a green slot tint when selected
                    # in settings (InventoryPlus-style fill + stronger edge/active tones).
                    if bool(highlight_selected_box) and bool(current):
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.10, 0.28, 0.12, 1.00))
                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.14, 0.38, 0.16, 1.00))
                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.18, 0.46, 0.20, 1.00))
                    else:
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.02, 0.02, 0.02, 1.00))
                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.08, 0.08, 0.08, 1.00))
                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.00, 0.00, 0.00, 1.00))
                    pushed_colors = 3
                except Exception:
                    pushed_colors = 0
                if not current:
                    style_vars = getattr(PyImGui, "ImGuiStyleVar", None)
                    alpha_var = getattr(style_vars, "Alpha", None) if style_vars is not None else None
                    if alpha_var is not None and hasattr(PyImGui, "push_style_var"):
                        PyImGui.push_style_var(alpha_var, 0.45)
                        pushed_alpha = True
                if ImGui.ImageButton(f"##{id_prefix}_icon_{key}", icon_path, float(icon_size), float(icon_size)):
                    current = not current
            finally:
                if pushed_alpha:
                    try:
                        PyImGui.pop_style_var(1)
                    except Exception:
                        pass
                if pushed_colors > 0:
                    try:
                        PyImGui.pop_style_color(pushed_colors)
                    except Exception:
                        pass
            _tooltip_if_hovered(tooltip_text)
            changed = bool(current) != bool(state_now)
            return bool(current), bool(changed), True

        # Fallback path when no icon can be resolved for this consumable.
        pushed_colors = 0
        try:
            if bool(highlight_selected_box) and bool(current):
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0.10, 0.28, 0.12, 1.00))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0.14, 0.38, 0.16, 1.00))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0.18, 0.46, 0.20, 1.00))
                pushed_colors = 3
            _, current = ui_checkbox(f"##{id_prefix}_cb_{key}", bool(state_now))
        finally:
            if pushed_colors > 0:
                try:
                    PyImGui.pop_style_color(pushed_colors)
                except Exception:
                    pass
        _tooltip_if_hovered(tooltip_text)
        changed = bool(current) != bool(state_now)
        return bool(current), bool(changed), False

    def _draw_static_consumable_icon(
        key: str,
        label: str,
        id_prefix: str,
        icon_size: float = 18.0,
        highlight_box: bool = False,
    ) -> bool:
        tooltip_text = _consumable_tooltip_with_label(key, label)
        icon_path = _resolve_consumable_icon_path(key, label)
        if not icon_path:
            return False
        pushed_colors = 0
        try:
            try:
                if bool(highlight_box):
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.10, 0.28, 0.12, 1.00))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.14, 0.38, 0.16, 1.00))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.18, 0.46, 0.20, 1.00))
                else:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.02, 0.02, 0.02, 1.00))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.08, 0.08, 0.08, 1.00))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.00, 0.00, 0.00, 1.00))
                pushed_colors = 3
            except Exception:
                pushed_colors = 0
            ImGui.ImageButton(f"##{id_prefix}_icon_{key}", icon_path, float(icon_size), float(icon_size))
        except Exception:
            return False
        finally:
            if pushed_colors > 0:
                try:
                    PyImGui.pop_style_color(pushed_colors)
                except Exception:
                    pass
        _tooltip_if_hovered(tooltip_text)
        return True

    def _alcohol_display_label(spec: dict) -> str:
        base = str(spec.get("label", "") or "")
        pts = int(spec.get("drunk_add", 0) or 0)
        if pts > 0:
            suffix = f" ({pts})"
            if base.endswith(suffix):
                return base
            return base + suffix
        return base

    # -------------------------
    # Config (dirty-save throttled)
    # -------------------------
    # Lazy INI handler creation to ensure account email is available
    _ini_handler_cache = None
    _ini_path_cache: str | None = None
    _ini_generic_fallback_logged = False
    _ini_generic_cached_with_email_logged = False
    _GENERIC_INI_PATH, _LEGACY_GENERIC_INI_PATH = get_pycons_generic_ini_candidates()
    _PYCONS_CONFIG_DIR = os.path.dirname(_GENERIC_INI_PATH)
    _LEGACY_CONFIG_DIR = os.path.dirname(_LEGACY_GENERIC_INI_PATH)

    def _norm_path_lower(path: str | None) -> str:
        try:
            return os.path.normpath(str(path or "")).replace("\\", "/").lower()
        except Exception:
            return str(path or "").replace("\\", "/").lower()

    def _is_generic_ini_path(path: str | None) -> bool:
        try:
            p = _norm_path_lower(path)
            return p == _norm_path_lower(_GENERIC_INI_PATH) or p == _norm_path_lower(_LEGACY_GENERIC_INI_PATH)
        except Exception:
            return False

    def _ensure_pycons_config_dir() -> bool:
        try:
            os.makedirs(_PYCONS_CONFIG_DIR, exist_ok=True)
            return True
        except Exception:
            return False

    def _resolve_account_ini_path(account_email: str, migrate_legacy: bool = True, log_migration: bool = False) -> str:
        email = str(account_email or "").strip()
        if not email:
            return _resolve_generic_ini_path(migrate_legacy=migrate_legacy, log_migration=log_migration)

        canonical, legacy = get_pycons_account_ini_candidates(email)

        if os.path.exists(canonical):
            return canonical

        if bool(migrate_legacy) and os.path.exists(legacy):
            try:
                _ensure_pycons_config_dir()
                if not os.path.exists(canonical):
                    shutil.copy2(legacy, canonical)
                if bool(log_migration):
                    ConsoleLog(BOT_NAME, f"Migrated config file: {legacy} -> {canonical}", Console.MessageType.Info)
                return canonical
            except Exception as e:
                if bool(log_migration):
                    ConsoleLog(BOT_NAME, f"Config migration failed ({legacy} -> {canonical}): {e}", Console.MessageType.Warning)
                return legacy

        _ensure_pycons_config_dir()
        return canonical

    def _resolve_generic_ini_path(migrate_legacy: bool = True, log_migration: bool = False) -> str:
        canonical, legacy = get_pycons_generic_ini_candidates()

        if os.path.exists(canonical):
            return canonical

        if bool(migrate_legacy) and os.path.exists(legacy):
            try:
                _ensure_pycons_config_dir()
                if not os.path.exists(canonical):
                    shutil.copy2(legacy, canonical)
                if bool(log_migration):
                    ConsoleLog(BOT_NAME, f"Migrated config file: {legacy} -> {canonical}", Console.MessageType.Info)
                return canonical
            except Exception as e:
                if bool(log_migration):
                    ConsoleLog(BOT_NAME, f"Config migration failed ({legacy} -> {canonical}): {e}", Console.MessageType.Warning)
                return legacy

        _ensure_pycons_config_dir()
        return canonical
    
    def _get_ini_handler():
        global _ini_handler_cache, _ini_path_cache, _ini_generic_fallback_logged, _ini_generic_cached_with_email_logged
        if _ini_handler_cache is not None:
            if _is_generic_ini_path(_ini_path_cache):
                try:
                    account_email_live = str(Player.GetAccountEmail() or "")
                except Exception:
                    account_email_live = ""
                if account_email_live and not _ini_generic_cached_with_email_logged:
                    ConsoleLog(
                        BOT_NAME,
                        "Config handler is still bound to generic INI "
                        f"({_ini_path_cache}) even though account email is now available "
                        f"({account_email_live}). Automatic rebind to the account INI is pending.",
                        Console.MessageType.Warning,
                    )
                    _ini_generic_cached_with_email_logged = True
            return _ini_handler_cache
        if _ini_handler_cache is None:
            account_email = Player.GetAccountEmail()
            if not account_email:
                # Fallback to generic file if not logged in yet
                _ini_path_cache = _resolve_generic_ini_path(migrate_legacy=True, log_migration=True)
                if not _ini_generic_fallback_logged:
                    ConsoleLog(
                        BOT_NAME,
                        "Account email unavailable at config init; using generic INI "
                        f"({_ini_path_cache}) for this session.",
                        Console.MessageType.Warning,
                    )
                    _ini_generic_fallback_logged = True
            else:
                _ini_path_cache = _resolve_account_ini_path(account_email, migrate_legacy=True, log_migration=True)
            try:
                parent_dir = os.path.dirname(str(_ini_path_cache or ""))
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
            except Exception:
                pass
            _ini_handler_cache = IniHandler(_ini_path_cache)
            ConsoleLog(BOT_NAME, f"Using config file: {_ini_path_cache} (account: {account_email})", Console.MessageType.Info)
        return _ini_handler_cache
    
    def _get_ini_path():
        global _ini_path_cache
        if _ini_path_cache is None:
            _get_ini_handler()  # Initialize if needed
        return _ini_path_cache

    def _maybe_rebind_cfg_from_generic_ini() -> bool:
        global cfg, _ini_handler_cache, _ini_path_cache, _ini_generic_cached_with_email_logged
        if cfg is None or _ini_handler_cache is None:
            return False
        if not _is_generic_ini_path(_ini_path_cache):
            return False
        if bool(getattr(cfg, "_dirty", False)):
            return False

        try:
            account_email = str(Player.GetAccountEmail() or "").strip()
        except Exception:
            account_email = ""
        if not account_email:
            return False

        old_path = str(_ini_path_cache or "")
        new_path = _resolve_account_ini_path(account_email, migrate_legacy=True, log_migration=True)
        if _norm_path_lower(new_path) == _norm_path_lower(old_path):
            return False

        if (not os.path.exists(new_path)) and old_path and os.path.exists(old_path):
            try:
                _ensure_pycons_config_dir()
                shutil.copy2(old_path, new_path)
                ConsoleLog(
                    BOT_NAME,
                    f"Seeded account config from generic fallback: {old_path} -> {new_path}",
                    Console.MessageType.Info,
                )
            except Exception as e:
                ConsoleLog(
                    BOT_NAME,
                    f"Failed seeding account config from generic fallback ({old_path} -> {new_path}): {e}",
                    Console.MessageType.Warning,
                )

        _ini_path_cache = new_path
        try:
            parent_dir = os.path.dirname(str(_ini_path_cache or ""))
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
        except Exception:
            pass
        _ini_handler_cache = IniHandler(_ini_path_cache)
        _ini_generic_cached_with_email_logged = False

        cfg = Config()
        _runtime_sync_from_cfg_full()
        _clear_one_shot_synced_enabled_defaults_if_needed()
        _team_flags_cache.clear()
        try:
            _local_team_flags_refresh_timer.Stop()
        except Exception:
            pass
        ConsoleLog(BOT_NAME, f"Rebound config file: {old_path} -> {new_path} (account: {account_email})", Console.MessageType.Info)
        return True

    def _ini_key_exists(ini_handler, section: str, key: str) -> bool:
        try:
            val = ini_handler.read_key(section, key, None)
            if val is None:
                return False
            txt = str(val)
            return txt != ""
        except Exception:
            return False

    class Config:
        def __init__(self):
            ini_handler = _get_ini_handler()
            self.debug_logging = ini_handler.read_bool(INI_SECTION, "debug_logging", False)
            self.interval_ms = ini_handler.read_int(INI_SECTION, "interval_ms", 1500)
            self.party_item_interval_ms = max(
                MIN_PARTY_ITEM_INTERVAL_MS,
                min(MAX_PARTY_ITEM_INTERVAL_MS, int(ini_handler.read_int(INI_SECTION, "party_item_interval_ms", DEFAULT_PARTY_ITEM_INTERVAL_MS))),
            )
            self.restock_interval_ms = max(MIN_RESTOCK_INTERVAL_MS, int(ini_handler.read_int(INI_SECTION, "restock_interval_ms", DEFAULT_RESTOCK_INTERVAL_MS)))
            self.restock_mode = max(
                RESTOCK_MODE_BALANCED,
                min(RESTOCK_MODE_DEPOSIT_ONLY, int(ini_handler.read_int(INI_SECTION, "restock_mode", DEFAULT_RESTOCK_MODE))),
            )
            self.restock_scope_mode = max(
                RESTOCK_SCOPE_ACCOUNT_WIDE,
                min(RESTOCK_SCOPE_BLOCK_LIST, int(ini_handler.read_int(INI_SECTION, "restock_scope_mode", DEFAULT_RESTOCK_SCOPE_MODE))),
            )
            self.restock_allowed_characters = str(ini_handler.read_key(INI_SECTION, "restock_allowed_characters", "") or "").strip()
            self.restock_blocked_characters = str(ini_handler.read_key(INI_SECTION, "restock_blocked_characters", "") or "").strip()
            self.restock_move_cap_per_cycle = max(
                MIN_RESTOCK_MOVE_CAP_PER_CYCLE,
                min(MAX_RESTOCK_MOVE_CAP_PER_CYCLE, int(ini_handler.read_int(INI_SECTION, "restock_move_cap_per_cycle", DEFAULT_RESTOCK_MOVE_CAP_PER_CYCLE))),
            )
            self.show_selected_list = ini_handler.read_bool(INI_SECTION, "show_selected_list", True)
            self.only_show_available_inventory = ini_handler.read_bool(INI_SECTION, "only_show_available_inventory", False)
            self.only_show_selected_items = ini_handler.read_bool(INI_SECTION, "only_show_selected_items", False)
            self.auto_vault_restock = ini_handler.read_bool(INI_SECTION, "auto_vault_restock", False)
            self.restock_keep_target_on_deselect = ini_handler.read_bool(INI_SECTION, "restock_keep_target_on_deselect", True)
            self.tooltip_visibility = max(0, min(2, int(ini_handler.read_int(INI_SECTION, "tooltip_visibility", 1))))
            self.tooltip_length = max(0, min(1, int(ini_handler.read_int(INI_SECTION, "tooltip_length", 1))))
            self.tooltip_show_why = ini_handler.read_bool(INI_SECTION, "tooltip_show_why", True)
            self.last_applied_preset = str(ini_handler.read_key(INI_SECTION, "last_applied_preset", "None") or "None")
            self.last_party_opt_toggle_summary = str(ini_handler.read_key(INI_SECTION, "last_party_opt_toggle_summary", "None") or "None")
            self.sync_selection_include_enabled_state = ini_handler.read_bool(INI_SECTION, "sync_selection_include_enabled_state", False)
            self._sync_selection_enabled_state_once = ini_handler.read_bool(INI_SECTION, PYCONS_SYNC_SELECTION_ENABLED_STATE_ONCE_KEY, False)

            # Optional per-item min intervals
            self.show_advanced_intervals = ini_handler.read_bool(INI_SECTION, "show_advanced_intervals", False)
            self.persist_main_runtime_toggles = ini_handler.read_bool(INI_SECTION, "persist_main_runtime_toggles", False)
            self.min_interval_ms = {}
            for c in CONSUMABLES:
                k = c["key"]
                self.min_interval_ms[k] = max(0, int(ini_handler.read_int(INI_SECTION, f"min_interval_{k}", 0)))

            # Alcohol
            self.alcohol_enabled = ini_handler.read_bool(INI_SECTION, "alcohol_enabled", False)
            self.alcohol_disable_effect = ini_handler.read_bool(INI_SECTION, "alcohol_disable_effect", False)
            self.alcohol_fast_spending = ini_handler.read_bool(INI_SECTION, "alcohol_fast_spending", False)
            self.alcohol_fast_interval_ms = max(
                MIN_ALCOHOL_FAST_INTERVAL_MS,
                min(MAX_ALCOHOL_FAST_INTERVAL_MS, int(ini_handler.read_int(INI_SECTION, "alcohol_fast_interval_ms", DEFAULT_ALCOHOL_FAST_INTERVAL_MS))),
            )
            self.sweets_fast_spending = ini_handler.read_bool(INI_SECTION, "sweets_fast_spending", False)
            self.sweets_fast_interval_ms = max(
                MIN_SWEETS_FAST_INTERVAL_MS,
                min(MAX_SWEETS_FAST_INTERVAL_MS, int(ini_handler.read_int(INI_SECTION, "sweets_fast_interval_ms", DEFAULT_SWEETS_FAST_INTERVAL_MS))),
            )
            self.movement_safety_window_ms = max(
                MIN_MOVEMENT_SAFETY_WINDOW_MS,
                min(
                    MAX_MOVEMENT_SAFETY_WINDOW_MS,
                    int(ini_handler.read_int(INI_SECTION, "movement_safety_window_ms", DEFAULT_MOVEMENT_SAFETY_WINDOW_MS)),
                ),
            )
            self.movement_party_items_fast_threshold_ms = max(
                MIN_PARTY_ITEM_INTERVAL_MS,
                min(
                    MAX_PARTY_ITEM_INTERVAL_MS,
                    int(
                        ini_handler.read_int(
                            INI_SECTION,
                            "movement_party_items_fast_threshold_ms",
                            DEFAULT_MOVEMENT_PARTY_ITEMS_FAST_THRESHOLD_MS,
                        )
                    ),
                ),
            )
            self.movement_require_explorable = ini_handler.read_bool(INI_SECTION, "movement_require_explorable", False)
            self.movement_require_summoning = ini_handler.read_bool(INI_SECTION, "movement_require_summoning", False)
            self.movement_require_mbdp = ini_handler.read_bool(INI_SECTION, "movement_require_mbdp", False)
            self.movement_require_alcohol = ini_handler.read_bool(INI_SECTION, "movement_require_alcohol", False)
            self.movement_require_party_items = ini_handler.read_bool(INI_SECTION, "movement_require_party_items", False)
            self.movement_require_sweets = ini_handler.read_bool(INI_SECTION, "movement_require_sweets", False)
            self.movement_alcohol_fast_only = ini_handler.read_bool(INI_SECTION, "movement_alcohol_fast_only", False)
            self.movement_party_items_speed_only = ini_handler.read_bool(INI_SECTION, "movement_party_items_speed_only", False)
            self.movement_sweets_fast_only = ini_handler.read_bool(INI_SECTION, "movement_sweets_fast_only", False)
            self.alcohol_target_level = max(0, min(5, int(ini_handler.read_int(INI_SECTION, "alcohol_target_level", 3))))

            self.alcohol_use_explorable = ini_handler.read_bool(INI_SECTION, "alcohol_use_explorable", True)
            self.alcohol_use_outpost = ini_handler.read_bool(INI_SECTION, "alcohol_use_outpost", True)

            # 0=smooth, 1=strong-first, 2=weak-first
            self.alcohol_preference = int(ini_handler.read_int(INI_SECTION, "alcohol_preference", 0))
            if self.alcohol_preference not in (0, 1, 2):
                self.alcohol_preference = 0

            self.selected = {}
            self.enabled = {}
            self.restock_enabled_items = {}
            for c in ALL_CONSUMABLES:
                k = c["key"]
                self.selected[k] = ini_handler.read_bool(INI_SECTION, f"selected_{k}", False)
                self.enabled[k] = ini_handler.read_bool(INI_SECTION, f"enabled_{k}", False)
                self.restock_enabled_items[k] = ini_handler.read_bool(INI_SECTION, f"restock_enabled_{k}", False)
            self.restock_targets = {}
            for c in ALL_CONSUMABLES:
                k = c["key"]
                default_target = int(VAULT_RESTOCK_TARGET_QTY) if bool(self.selected.get(k, False)) and bool(self.restock_enabled_items.get(k, False)) else 0
                raw_target = int(ini_handler.read_int(INI_SECTION, f"restock_target_{k}", default_target))
                self.restock_targets[k] = max(0, min(2500, raw_target))

            # Settings-window consumables group open/closed state
            self.settings_explorable_open = ini_handler.read_bool(INI_SECTION, "settings_explorable_open", False)
            self.settings_summoning_open = ini_handler.read_bool(INI_SECTION, "settings_summoning_open", False)
            self.settings_outpost_open = ini_handler.read_bool(INI_SECTION, "settings_outpost_open", False)
            self.settings_mbdp_open = ini_handler.read_bool(INI_SECTION, "settings_mbdp_open", False)
            self.settings_alcohol_open = ini_handler.read_bool(INI_SECTION, "settings_alcohol_open", False)
            self.settings_party_items_open = ini_handler.read_bool(INI_SECTION, "settings_party_items_open", False)
            # Settings-window top-level section open/closed state
            self.settings_ui_tooltip_open = ini_handler.read_bool(INI_SECTION, "settings_ui_tooltip_open", False)
            self.settings_ui_sync_open = ini_handler.read_bool(INI_SECTION, "settings_ui_sync_open", False)
            self.settings_ui_alcohol_open = ini_handler.read_bool(INI_SECTION, "settings_ui_alcohol_open", False)
            self.settings_ui_movement_safety_open = ini_handler.read_bool(INI_SECTION, "settings_ui_movement_safety_open", False)
            self.settings_ui_mbdp_open = ini_handler.read_bool(INI_SECTION, "settings_ui_mbdp_open", False)
            self.settings_ui_presets_open = ini_handler.read_bool(INI_SECTION, "settings_ui_presets_open", False)
            self.settings_ui_restock_open = ini_handler.read_bool(INI_SECTION, "settings_ui_restock_open", False)

            # Morale boost + DP upkeep settings
            self.mbdp_enabled = ini_handler.read_bool(INI_SECTION, "mbdp_enabled", bool(MBDP_DEFAULTS["mbdp_enabled"]))
            self.mbdp_allow_partywide_in_human_parties = ini_handler.read_bool(INI_SECTION, "mbdp_allow_partywide_in_human_parties", bool(MBDP_DEFAULTS["mbdp_allow_partywide_in_human_parties"]))
            self.mbdp_receiver_require_enabled = ini_handler.read_bool(INI_SECTION, "mbdp_receiver_require_enabled", bool(MBDP_DEFAULTS["mbdp_receiver_require_enabled"]))
            def _dp_threshold_to_effective(v: int) -> tuple[int, bool]:
                iv = int(v)
                # Legacy format stored DP thresholds as 0..60. New format stores effective trigger as -60..0.
                if iv > 0:
                    return max(-60, min(0, -iv)), True
                return max(-60, min(0, iv)), False

            _raw_self_minor = int(ini_handler.read_int(INI_SECTION, "mbdp_self_dp_minor_threshold", abs(int(MBDP_DEFAULTS["mbdp_self_dp_minor_threshold"]))))
            _raw_self_major = int(ini_handler.read_int(INI_SECTION, "mbdp_self_dp_major_threshold", abs(int(MBDP_DEFAULTS["mbdp_self_dp_major_threshold"]))))
            self.mbdp_self_dp_minor_threshold, _m1 = _dp_threshold_to_effective(_raw_self_minor)
            self.mbdp_self_dp_major_threshold, _m2 = _dp_threshold_to_effective(_raw_self_major)

            def _target_to_effective(v: int) -> int:
                iv = int(v)
                # Legacy format stored raw morale (40..110, neutral=100). New format stores effective (-60..+10).
                if iv > 10:
                    iv = iv - 100
                return max(-60, min(10, iv))

            _raw_self_target = int(ini_handler.read_int(INI_SECTION, "mbdp_self_morale_target_effective", int(MBDP_DEFAULTS["mbdp_self_morale_target_effective"])))
            _raw_party_target = int(ini_handler.read_int(INI_SECTION, "mbdp_party_target_effective", int(MBDP_DEFAULTS["mbdp_party_target_effective"])))
            self.mbdp_self_morale_target_effective = _target_to_effective(_raw_self_target)
            self.mbdp_self_min_morale_gain = max(0, min(10, int(ini_handler.read_int(INI_SECTION, "mbdp_self_min_morale_gain", int(MBDP_DEFAULTS["mbdp_self_min_morale_gain"])))))
            self.mbdp_party_target_effective = _target_to_effective(_raw_party_target)
            self.mbdp_strict_party_plus10 = ini_handler.read_bool(INI_SECTION, "mbdp_strict_party_plus10", bool(MBDP_DEFAULTS["mbdp_strict_party_plus10"]))
            self.mbdp_party_min_members = max(2, min(8, int(ini_handler.read_int(INI_SECTION, "mbdp_party_min_members", int(MBDP_DEFAULTS["mbdp_party_min_members"])))))
            self.mbdp_party_min_interval_ms = max(1000, int(ini_handler.read_int(INI_SECTION, "mbdp_party_min_interval_ms", int(MBDP_DEFAULTS["mbdp_party_min_interval_ms"]))))
            self.mbdp_party_min_total_gain_5 = max(0, min(60, int(ini_handler.read_int(INI_SECTION, "mbdp_party_min_total_gain_5", int(MBDP_DEFAULTS["mbdp_party_min_total_gain_5"])))))
            self.mbdp_party_min_total_gain_10 = max(0, min(120, int(ini_handler.read_int(INI_SECTION, "mbdp_party_min_total_gain_10", int(MBDP_DEFAULTS["mbdp_party_min_total_gain_10"])))))
            _raw_party_light = int(ini_handler.read_int(INI_SECTION, "mbdp_party_light_dp_threshold", abs(int(MBDP_DEFAULTS["mbdp_party_light_dp_threshold"]))))
            _raw_party_heavy = int(ini_handler.read_int(INI_SECTION, "mbdp_party_heavy_dp_threshold", abs(int(MBDP_DEFAULTS["mbdp_party_heavy_dp_threshold"]))))
            _raw_party_emergency = int(ini_handler.read_int(INI_SECTION, "mbdp_powerstone_dp_threshold", abs(int(MBDP_DEFAULTS["mbdp_powerstone_dp_threshold"]))))
            self.mbdp_party_light_dp_threshold, _m3 = _dp_threshold_to_effective(_raw_party_light)
            self.mbdp_party_heavy_dp_threshold, _m4 = _dp_threshold_to_effective(_raw_party_heavy)
            self.mbdp_powerstone_dp_threshold, _m5 = _dp_threshold_to_effective(_raw_party_emergency)
            self.mbdp_prefer_seal_for_recharge = ini_handler.read_bool(INI_SECTION, "mbdp_prefer_seal_for_recharge", bool(MBDP_DEFAULTS["mbdp_prefer_seal_for_recharge"]))
            self.force_team_morale_value = max(-60, min(10, int(ini_handler.read_int(INI_SECTION, "force_team_morale_value", int(MBDP_DEFAULTS["force_team_morale_value"])))))
            self._mbdp_targets_migrated = (
                (_raw_self_target != self.mbdp_self_morale_target_effective)
                or (_raw_party_target != self.mbdp_party_target_effective)
                or _m1 or _m2 or _m3 or _m4 or _m5
            )

            self.alcohol_selected = {}
            self.alcohol_enabled_items = {}
            for a in ALCOHOL_ITEMS:
                k = a["key"]
                self.alcohol_selected[k] = ini_handler.read_bool(INI_SECTION, f"alcohol_selected_{k}", False)
                self.alcohol_enabled_items[k] = ini_handler.read_bool(INI_SECTION, f"alcohol_enabled_{k}", False)
                self.restock_enabled_items[k] = ini_handler.read_bool(INI_SECTION, f"restock_enabled_{k}", False)
                default_target = int(VAULT_RESTOCK_TARGET_QTY) if bool(self.alcohol_selected.get(k, False)) and bool(self.restock_enabled_items.get(k, False)) else 0
                raw_target = int(ini_handler.read_int(INI_SECTION, f"restock_target_{k}", default_target))
                self.restock_targets[k] = max(0, min(2500, raw_target))

            # Team / multibox settings
            self.team_broadcast = ini_handler.read_bool(INI_SECTION, "team_broadcast", False)
            self.team_consume_opt_in = ini_handler.read_bool(INI_SECTION, "team_consume_opt_in", False)
            self.experimental_team_flag_sync = ini_handler.read_bool(
                INI_SECTION,
                "experimental_team_flag_sync",
                bool(EXPERIMENTAL_TEAM_FLAG_SYNC_DEFAULT),
            )
            self.experimental_mainloop_refresh_queue = ini_handler.read_bool(
                INI_SECTION,
                "experimental_mainloop_refresh_queue",
                bool(EXPERIMENTAL_MAINLOOP_REFRESH_QUEUE_DEFAULT),
            )

            # Backfill newly introduced experimental flags into existing INIs so
            # users/admins can see explicit values without manual edits.
            _experimental_defaults_backfilled = False
            if not _ini_key_exists(ini_handler, INI_SECTION, "experimental_team_flag_sync"):
                _experimental_defaults_backfilled = True
            if not _ini_key_exists(ini_handler, INI_SECTION, "experimental_mainloop_refresh_queue"):
                _experimental_defaults_backfilled = True

            self._dirty = bool(getattr(self, "_mbdp_targets_migrated", False))
            if bool(_experimental_defaults_backfilled):
                self._dirty = True
            self._save_timer = Timer()
            self._save_timer.Start()
            self._save_timer.Stop()

            try:
                _migrate_account_local_profiles_to_shared_library_if_needed(ini_handler)
            except Exception as e:
                ConsoleLog(BOT_NAME, f"Shared Pycons profile migration failed: {e}", Console.MessageType.Warning)

        def mark_dirty(self):
            self._dirty = True

        def save_if_dirty_throttled(self, every_ms: int = 750):
            if not self._dirty:
                return
            if not (self._save_timer.IsStopped() or self._save_timer.HasElapsed(int(every_ms))):
                return
            self._save_timer.Start()

            ini_handler = _get_ini_handler()
            config = ini_handler.reload()
            if not config.has_section(INI_SECTION):
                config.add_section(INI_SECTION)

            def set_key(key: str, value):
                config.set(INI_SECTION, str(key), str(value))

            set_key("debug_logging", bool(self.debug_logging))
            set_key("interval_ms", int(self.interval_ms))
            set_key(
                "party_item_interval_ms",
                int(max(MIN_PARTY_ITEM_INTERVAL_MS, min(MAX_PARTY_ITEM_INTERVAL_MS, int(self.party_item_interval_ms)))),
            )
            set_key("restock_interval_ms", int(max(MIN_RESTOCK_INTERVAL_MS, int(self.restock_interval_ms))))
            set_key("restock_mode", int(max(RESTOCK_MODE_BALANCED, min(RESTOCK_MODE_DEPOSIT_ONLY, int(self.restock_mode)))))
            set_key("restock_scope_mode", int(max(RESTOCK_SCOPE_ACCOUNT_WIDE, min(RESTOCK_SCOPE_BLOCK_LIST, int(self.restock_scope_mode)))))
            set_key("restock_allowed_characters", str(getattr(self, "restock_allowed_characters", "") or "").strip())
            set_key("restock_blocked_characters", str(getattr(self, "restock_blocked_characters", "") or "").strip())
            set_key(
                "restock_move_cap_per_cycle",
                int(max(MIN_RESTOCK_MOVE_CAP_PER_CYCLE, min(MAX_RESTOCK_MOVE_CAP_PER_CYCLE, int(self.restock_move_cap_per_cycle)))),
            )
            set_key("show_selected_list", bool(self.show_selected_list))
            set_key("only_show_available_inventory", bool(self.only_show_available_inventory))
            set_key("only_show_selected_items", bool(self.only_show_selected_items))
            set_key("auto_vault_restock", bool(self.auto_vault_restock))
            set_key("restock_keep_target_on_deselect", bool(self.restock_keep_target_on_deselect))
            set_key("tooltip_visibility", int(self.tooltip_visibility))
            set_key("tooltip_length", int(self.tooltip_length))
            set_key("tooltip_show_why", bool(self.tooltip_show_why))
            set_key("last_applied_preset", self.last_applied_preset)
            set_key("last_party_opt_toggle_summary", self.last_party_opt_toggle_summary)
            set_key("sync_selection_include_enabled_state", bool(self.sync_selection_include_enabled_state))
            set_key(PYCONS_SYNC_SELECTION_ENABLED_STATE_ONCE_KEY, bool(getattr(self, "_sync_selection_enabled_state_once", False)))

            set_key("show_advanced_intervals", bool(self.show_advanced_intervals))
            set_key("persist_main_runtime_toggles", bool(self.persist_main_runtime_toggles))
            for k, v in self.min_interval_ms.items():
                set_key(f"min_interval_{k}", int(max(0, int(v))))

            set_key("alcohol_enabled", bool(self.alcohol_enabled))
            set_key("alcohol_disable_effect", bool(self.alcohol_disable_effect))
            set_key("alcohol_fast_spending", bool(self.alcohol_fast_spending))
            set_key(
                "alcohol_fast_interval_ms",
                int(max(MIN_ALCOHOL_FAST_INTERVAL_MS, min(MAX_ALCOHOL_FAST_INTERVAL_MS, int(self.alcohol_fast_interval_ms)))),
            )
            set_key("sweets_fast_spending", bool(self.sweets_fast_spending))
            set_key(
                "sweets_fast_interval_ms",
                int(max(MIN_SWEETS_FAST_INTERVAL_MS, min(MAX_SWEETS_FAST_INTERVAL_MS, int(self.sweets_fast_interval_ms)))),
            )
            set_key(
                "movement_safety_window_ms",
                int(max(MIN_MOVEMENT_SAFETY_WINDOW_MS, min(MAX_MOVEMENT_SAFETY_WINDOW_MS, int(self.movement_safety_window_ms)))),
            )
            set_key(
                "movement_party_items_fast_threshold_ms",
                int(
                    max(
                        MIN_PARTY_ITEM_INTERVAL_MS,
                        min(MAX_PARTY_ITEM_INTERVAL_MS, int(self.movement_party_items_fast_threshold_ms)),
                    )
                ),
            )
            set_key("movement_require_explorable", bool(self.movement_require_explorable))
            set_key("movement_require_summoning", bool(self.movement_require_summoning))
            set_key("movement_require_mbdp", bool(self.movement_require_mbdp))
            set_key("movement_require_alcohol", bool(self.movement_require_alcohol))
            set_key("movement_require_party_items", bool(self.movement_require_party_items))
            set_key("movement_require_sweets", bool(self.movement_require_sweets))
            set_key("movement_alcohol_fast_only", bool(self.movement_alcohol_fast_only))
            set_key("movement_party_items_speed_only", bool(self.movement_party_items_speed_only))
            set_key("movement_sweets_fast_only", bool(self.movement_sweets_fast_only))
            set_key("alcohol_target_level", int(self.alcohol_target_level))
            set_key("alcohol_use_explorable", bool(self.alcohol_use_explorable))
            set_key("alcohol_use_outpost", bool(self.alcohol_use_outpost))
            set_key("alcohol_preference", int(self.alcohol_preference))
            set_key("mbdp_enabled", bool(self.mbdp_enabled))
            set_key("mbdp_allow_partywide_in_human_parties", bool(self.mbdp_allow_partywide_in_human_parties))
            set_key("mbdp_receiver_require_enabled", bool(self.mbdp_receiver_require_enabled))
            set_key("mbdp_self_dp_minor_threshold", int(self.mbdp_self_dp_minor_threshold))
            set_key("mbdp_self_dp_major_threshold", int(self.mbdp_self_dp_major_threshold))
            set_key("mbdp_self_morale_target_effective", int(self.mbdp_self_morale_target_effective))
            set_key("mbdp_self_min_morale_gain", int(self.mbdp_self_min_morale_gain))
            set_key("mbdp_party_target_effective", int(self.mbdp_party_target_effective))
            set_key("mbdp_strict_party_plus10", bool(self.mbdp_strict_party_plus10))
            set_key("mbdp_party_min_members", int(self.mbdp_party_min_members))
            set_key("mbdp_party_min_interval_ms", int(self.mbdp_party_min_interval_ms))
            set_key("mbdp_party_min_total_gain_5", int(self.mbdp_party_min_total_gain_5))
            set_key("mbdp_party_min_total_gain_10", int(self.mbdp_party_min_total_gain_10))
            set_key("mbdp_party_light_dp_threshold", int(self.mbdp_party_light_dp_threshold))
            set_key("mbdp_party_heavy_dp_threshold", int(self.mbdp_party_heavy_dp_threshold))
            set_key("mbdp_powerstone_dp_threshold", int(self.mbdp_powerstone_dp_threshold))
            set_key("mbdp_prefer_seal_for_recharge", bool(self.mbdp_prefer_seal_for_recharge))
            set_key("force_team_morale_value", int(self.force_team_morale_value))
            set_key("settings_explorable_open", bool(self.settings_explorable_open))
            set_key("settings_summoning_open", bool(self.settings_summoning_open))
            set_key("settings_outpost_open", bool(self.settings_outpost_open))
            set_key("settings_mbdp_open", bool(self.settings_mbdp_open))
            set_key("settings_alcohol_open", bool(self.settings_alcohol_open))
            set_key("settings_party_items_open", bool(self.settings_party_items_open))
            set_key("settings_ui_tooltip_open", bool(self.settings_ui_tooltip_open))
            set_key("settings_ui_sync_open", bool(self.settings_ui_sync_open))
            set_key("settings_ui_alcohol_open", bool(self.settings_ui_alcohol_open))
            set_key("settings_ui_movement_safety_open", bool(self.settings_ui_movement_safety_open))
            set_key("settings_ui_mbdp_open", bool(self.settings_ui_mbdp_open))
            set_key("settings_ui_presets_open", bool(self.settings_ui_presets_open))
            set_key("settings_ui_restock_open", bool(self.settings_ui_restock_open))
            set_key("experimental_team_flag_sync", bool(self.experimental_team_flag_sync))
            set_key("experimental_mainloop_refresh_queue", bool(self.experimental_mainloop_refresh_queue))

            for k, v in self.alcohol_selected.items():
                set_key(f"alcohol_selected_{k}", bool(v))
            for k, v in self.alcohol_enabled_items.items():
                set_key(f"alcohol_enabled_{k}", bool(v))
            for k, v in self.restock_enabled_items.items():
                set_key(f"restock_enabled_{k}", bool(v))
            for c in ALL_CONSUMABLES:
                k = str(c.get("key", "") or "")
                if k:
                    set_key(f"restock_target_{k}", int(max(0, min(2500, int(self.restock_targets.get(k, VAULT_RESTOCK_TARGET_QTY) or 0)))))
            for a in ALCOHOL_ITEMS:
                k = str(a.get("key", "") or "")
                if k:
                    set_key(f"restock_target_{k}", int(max(0, min(2500, int(self.restock_targets.get(k, VAULT_RESTOCK_TARGET_QTY) or 0)))))

            # Team / multibox settings
            # team_broadcast: When enabled, broadcasts item usage to other accounts
            # team_consume_opt_in: When enabled (on followers), consumes items when broadcasts are received
            # Legacy behavior keeps team_consume_opt_in saved by immediate settings writes.
            # Experimental team-flag sync writes both flags here to reduce refresh races.
            set_key("team_broadcast", bool(self.team_broadcast))
            if bool(getattr(self, "experimental_team_flag_sync", EXPERIMENTAL_TEAM_FLAG_SYNC_DEFAULT)):
                set_key("team_consume_opt_in", bool(self.team_consume_opt_in))

            for k, v in self.selected.items():
                set_key(f"selected_{k}", bool(v))
            for k, v in self.enabled.items():
                set_key(f"enabled_{k}", bool(v))

            ini_handler.save(config)
            self._dirty = False

    # Config will be lazy-loaded on first main() call to ensure account email is available
    cfg = cast("Config", None)

    def _apply_mbdp_defaults():
        global _last_mbdp_party_ms
        cfg.mbdp_enabled = bool(MBDP_DEFAULTS["mbdp_enabled"])
        cfg.mbdp_allow_partywide_in_human_parties = bool(MBDP_DEFAULTS["mbdp_allow_partywide_in_human_parties"])
        cfg.mbdp_receiver_require_enabled = bool(MBDP_DEFAULTS["mbdp_receiver_require_enabled"])
        cfg.mbdp_self_dp_minor_threshold = int(MBDP_DEFAULTS["mbdp_self_dp_minor_threshold"])
        cfg.mbdp_self_dp_major_threshold = int(MBDP_DEFAULTS["mbdp_self_dp_major_threshold"])
        cfg.mbdp_self_morale_target_effective = int(MBDP_DEFAULTS["mbdp_self_morale_target_effective"])
        cfg.mbdp_self_min_morale_gain = int(MBDP_DEFAULTS["mbdp_self_min_morale_gain"])
        cfg.mbdp_party_min_members = int(MBDP_DEFAULTS["mbdp_party_min_members"])
        cfg.mbdp_party_min_interval_ms = int(MBDP_DEFAULTS["mbdp_party_min_interval_ms"])
        cfg.mbdp_party_target_effective = int(MBDP_DEFAULTS["mbdp_party_target_effective"])
        cfg.mbdp_strict_party_plus10 = bool(MBDP_DEFAULTS["mbdp_strict_party_plus10"])
        cfg.mbdp_party_min_total_gain_5 = int(MBDP_DEFAULTS["mbdp_party_min_total_gain_5"])
        cfg.mbdp_party_min_total_gain_10 = int(MBDP_DEFAULTS["mbdp_party_min_total_gain_10"])
        cfg.mbdp_party_light_dp_threshold = int(MBDP_DEFAULTS["mbdp_party_light_dp_threshold"])
        cfg.mbdp_party_heavy_dp_threshold = int(MBDP_DEFAULTS["mbdp_party_heavy_dp_threshold"])
        cfg.mbdp_powerstone_dp_threshold = int(MBDP_DEFAULTS["mbdp_powerstone_dp_threshold"])
        cfg.mbdp_prefer_seal_for_recharge = bool(MBDP_DEFAULTS["mbdp_prefer_seal_for_recharge"])
        cfg.force_team_morale_value = int(MBDP_DEFAULTS["force_team_morale_value"])
        _last_mbdp_party_ms = 0
        cfg.mark_dirty()

    # -------------------------
    # Runtime state
    # -------------------------
    class _RuntimeState:
        """Runtime-only mutable state grouped for clearer ownership."""
        def __init__(self):
            self.show_main_window = True
            self.expand_main_window_on_next_show = False
            self.floating_button = None
            self.show_settings = [False]
            self.filter_text = [""]
            self.last_search_active = [False]
            self.request_expand_selected = [False]
            self.request_collapse_selected = [False]
            self.restock_bulk_target = [int(VAULT_RESTOCK_TARGET_QTY)]
            self.runtime_selected = {}
            self.runtime_enabled = {}
            self.runtime_alcohol_selected = {}
            self.runtime_alcohol_enabled = {}
            self.sync_selected_accounts = {}
            self.sync_selected_categories = _default_pycons_sync_category_selection()
            self.sync_statuses = {}
            self.sync_summary_text = "No other-accounts action run yet."
            self.sync_active_request_id = ""
            self.sync_request_counter = 0
            self.sync_pending_profile_apply_id = ""
            self.sync_pending_profile_apply_targets_key = ""
            self.profile_selected_id = ""
            self.profile_active_applied_id = ""
            self.profile_new_name_input = ""
            self.profile_rename_input = ""
            self.profile_rename_input_source_id = ""
            self.profile_status_text = ""
            self.profile_status_error = False
            self.profile_pending_save_over_id = ""
            self.profile_pending_delete_id = ""

    _rt = _RuntimeState()
    # Aliases preserved so UI code and existing access patterns remain identical.
    show_settings = _rt.show_settings
    filter_text = _rt.filter_text
    last_search_active = _rt.last_search_active
    request_expand_selected = _rt.request_expand_selected
    request_collapse_selected = _rt.request_collapse_selected
    restock_bulk_target = _rt.restock_bulk_target

    tick_timer = Timer()
    tick_timer.Start()
    party_tick_timer = Timer()
    party_tick_timer.Start()
    restock_tick_timer = Timer()
    restock_tick_timer.Start()

    aftercast_timer = Timer()
    aftercast_timer.Start()
    aftercast_timer.Stop()

    internal_timers = {}
    _skill_id_cache = {}
    _skill_name_cache = {}
    _skill_retry_timer = {}
    _warn_timer = {}
    _blocked_actions = {}
    _last_used_ms = {}
    _last_broadcast_ms = {}
    _team_flags_cache = {}
    _last_mbdp_party_ms = 0
    _movement_last_xy = None
    _movement_last_ms = 0
    _movement_last_map_id = 0
    _movement_last_map_signature = None
    _movement_last_poll_ms = 0
    _movement_position_known = False
    _movement_wait_reason = ""
    _local_team_flags_refresh_timer = Timer()
    _local_team_flags_refresh_timer.Start()
    _local_team_flags_refresh_timer.Stop()

    # Alcohol estimate fallback
    _alcohol_last_drink_ms = 0
    _alcohol_level_base = 0

    # Inventory caching + stock counts
    _inv_cache_items = None
    _inv_cache_ts = 0
    _inv_counts_by_model = {}
    _inv_best_item_id_by_model = {}
    _inv_ready_cached = True
    _inv_ready_ts = 0
    _pending_refresh_due_ms = []
    _first_main_call = True
    _vault_deposit_dest_cooldown_until = {}
    _vault_last_confirmed_storage_bag_id = 0
    _vault_pending_state = {}
    _vault_action_cooldown_until = {}
    def _now_ms() -> int:
        import time
        return int(time.time() * 1000)

    def _get_or_create_stopped_timer(pool: dict, key: str) -> Timer:
        t = pool.get(key)
        if t is None:
            t = Timer()
            # Match existing behavior: initialized then immediately stopped.
            t.Start()
            t.Stop()
            pool[key] = t
        return t

    def _timer_for(key: str) -> Timer:
        return _get_or_create_stopped_timer(internal_timers, key)

    def _retry_timer_for(key: str) -> Timer:
        return _get_or_create_stopped_timer(_skill_retry_timer, key)

    def _warn_timer_for(key: str) -> Timer:
        return _get_or_create_stopped_timer(_warn_timer, key)

    def _record_blocked_action(code: str, message: str):
        c = str(code or "").strip()
        msg = str(message or "").strip()
        if not c or not msg:
            return
        now = int(_now_ms())
        state = _blocked_actions.get(c)
        prev_count = 0
        if isinstance(state, dict):
            prev_count = int(state.get("count", 0) or 0)
        _blocked_actions[c] = {
            "message": msg,
            "count": int(prev_count + 1),
            "last_ms": int(now),
        }

        # Keep tracker bounded to recent signals only.
        cutoff = int(now - int(BLOCKED_ACTION_RETENTION_MS))
        for k, v in list(_blocked_actions.items()):
            try:
                last_ms = int(v.get("last_ms", 0) or 0)
            except Exception:
                last_ms = 0
            if last_ms < cutoff:
                del _blocked_actions[k]

    def _active_blocked_actions(limit: int = BLOCKED_ACTION_MAX_UI_ROWS) -> list[tuple[str, int, int]]:
        now = int(_now_ms())
        cutoff = int(now - int(BLOCKED_ACTION_RETENTION_MS))
        rows: list[tuple[int, str, int]] = []
        for k, v in list(_blocked_actions.items()):
            try:
                last_ms = int(v.get("last_ms", 0) or 0)
            except Exception:
                last_ms = 0
            if last_ms < cutoff:
                del _blocked_actions[k]
                continue
            msg = str(v.get("message", "") or "").strip()
            if not msg:
                continue
            try:
                count = int(v.get("count", 0) or 0)
            except Exception:
                count = 0
            rows.append((int(last_ms), msg, max(1, int(count))))
        rows.sort(key=lambda r: int(r[0]), reverse=True)
        top = rows[:max(1, int(limit))]
        return [(str(msg), int(count), max(0, int((now - int(last_ms)) / 1000))) for last_ms, msg, count in top]

    def _movement_safety_window_ms() -> int:
        if cfg is None:
            return int(DEFAULT_MOVEMENT_SAFETY_WINDOW_MS)
        try:
            raw = int(getattr(cfg, "movement_safety_window_ms", DEFAULT_MOVEMENT_SAFETY_WINDOW_MS))
        except Exception:
            raw = int(DEFAULT_MOVEMENT_SAFETY_WINDOW_MS)
        return int(max(MIN_MOVEMENT_SAFETY_WINDOW_MS, min(MAX_MOVEMENT_SAFETY_WINDOW_MS, raw)))

    def _party_item_interval_ms() -> int:
        if cfg is None:
            return int(DEFAULT_PARTY_ITEM_INTERVAL_MS)
        try:
            raw = int(getattr(cfg, "party_item_interval_ms", DEFAULT_PARTY_ITEM_INTERVAL_MS))
        except Exception:
            raw = int(DEFAULT_PARTY_ITEM_INTERVAL_MS)
        return int(max(MIN_PARTY_ITEM_INTERVAL_MS, min(MAX_PARTY_ITEM_INTERVAL_MS, raw)))

    def _movement_party_items_fast_threshold_ms() -> int:
        if cfg is None:
            return int(DEFAULT_MOVEMENT_PARTY_ITEMS_FAST_THRESHOLD_MS)
        try:
            raw = int(getattr(cfg, "movement_party_items_fast_threshold_ms", DEFAULT_MOVEMENT_PARTY_ITEMS_FAST_THRESHOLD_MS))
        except Exception:
            raw = int(DEFAULT_MOVEMENT_PARTY_ITEMS_FAST_THRESHOLD_MS)
        return int(max(MIN_PARTY_ITEM_INTERVAL_MS, min(MAX_PARTY_ITEM_INTERVAL_MS, raw)))

    def _current_map_id() -> int:
        try:
            for name in ("GetMapID", "GetMapId", "GetCurrentMapID", "GetCurrentMapId"):
                fn = getattr(Map, name, None)
                if callable(fn):
                    value = int(fn() or 0)
                    if value > 0:
                        return value
        except Exception:
            pass
        return 0

    def _current_map_signature() -> tuple[int, int, int, int]:
        map_id = int(_current_map_id())
        if map_id <= 0:
            return 0, 0, 0, 0
        region = 0
        district = 0
        language = 0
        try:
            region_value = Map.GetRegion()
            if isinstance(region_value, (tuple, list)) and len(region_value) >= 1:
                region = int(region_value[0] or 0)
            else:
                region = int(region_value or 0)
        except Exception:
            region = 0
        try:
            district = int(Map.GetDistrict() or 0)
        except Exception:
            district = 0
        try:
            language_value = Map.GetLanguage()
            if isinstance(language_value, (tuple, list)) and len(language_value) >= 1:
                language = int(language_value[0] or 0)
            else:
                language = int(language_value or 0)
        except Exception:
            language = 0
        return int(map_id), int(region), int(district), int(language)

    def _player_xy() -> tuple[float, float] | None:
        try:
            pos = Player.GetXY()
            if isinstance(pos, (tuple, list)) and len(pos) >= 2:
                return float(pos[0]), float(pos[1])
            x = getattr(pos, "x", None)
            y = getattr(pos, "y", None)
            if x is not None and y is not None:
                return float(x), float(y)
        except Exception:
            pass

        try:
            agent_id = int(Player.GetAgentID() or 0)
            if agent_id <= 0:
                return None
            pos = Agent.GetXY(agent_id)
            if isinstance(pos, (tuple, list)) and len(pos) >= 2:
                return float(pos[0]), float(pos[1])
            x = getattr(pos, "x", None)
            y = getattr(pos, "y", None)
            if x is not None and y is not None:
                return float(x), float(y)
        except Exception:
            pass
        return None

    def _player_is_moving_now() -> bool | None:
        try:
            agent_id = int(Player.GetAgentID() or 0)
            if agent_id <= 0:
                return None
            return bool(Agent.IsMoving(agent_id))
        except Exception:
            return None

    def _update_movement_tracker(force: bool = False) -> None:
        global _movement_last_xy, _movement_last_ms, _movement_last_map_id, _movement_last_map_signature, _movement_last_poll_ms, _movement_position_known, _movement_wait_reason

        now = int(_now_ms())
        if (not bool(force)) and int(_movement_last_poll_ms or 0) > 0 and (now - int(_movement_last_poll_ms)) < 250:
            return
        _movement_last_poll_ms = int(now)

        xy = _player_xy()
        if xy is None:
            _movement_position_known = False
            return

        map_signature = _current_map_signature()
        map_id = int(map_signature[0])
        previous_signature = _movement_last_map_signature
        map_context_became_known = bool(
            map_id > 0
            and previous_signature is not None
            and int(previous_signature[0]) <= 0
        )
        map_changed = bool(
            map_context_became_known
            or (
                map_id > 0
                and previous_signature is not None
                and int(previous_signature[0]) > 0
                and tuple(map_signature) != tuple(previous_signature)
            )
        )
        if _movement_last_xy is None or map_changed:
            _movement_last_xy = (float(xy[0]), float(xy[1]))
            _movement_last_ms = 0
            _movement_last_map_id = int(map_id)
            _movement_last_map_signature = tuple(map_signature)
            _movement_position_known = True
            _movement_wait_reason = "map_load" if bool(map_changed) else "startup"
            return

        moving_now = _player_is_moving_now()
        if moving_now is False:
            _movement_last_xy = (float(xy[0]), float(xy[1]))
            if map_id > 0:
                _movement_last_map_id = int(map_id)
                _movement_last_map_signature = tuple(map_signature)
            _movement_position_known = True
            return

        prev_x, prev_y = _movement_last_xy
        dx = float(xy[0]) - float(prev_x)
        dy = float(xy[1]) - float(prev_y)
        delta_sq = float(dx * dx + dy * dy)
        if (moving_now is not False) and delta_sq >= float(MOVEMENT_POSITION_RESET_DELTA_SQ):
            _movement_last_xy = (float(xy[0]), float(xy[1]))
            _movement_last_ms = 0
            _movement_wait_reason = "map_load"
        elif (moving_now is not False) and delta_sq >= float(MOVEMENT_DELTA_EPSILON_SQ):
            _movement_last_xy = (float(xy[0]), float(xy[1]))
            _movement_last_ms = int(now)
            _movement_wait_reason = ""
        if map_id > 0:
            _movement_last_map_id = int(map_id)
            _movement_last_map_signature = tuple(map_signature)
        _movement_position_known = True

    def _movement_recently_moved(now_ms: int | None = None) -> bool:
        _update_movement_tracker()
        if not bool(_movement_position_known):
            return True
        now = int(_now_ms() if now_ms is None else now_ms)
        last_ms = int(_movement_last_ms or 0)
        if last_ms <= 0:
            return False
        return bool((now - last_ms) <= int(_movement_safety_window_ms()))

    def _movement_status_summary(compact: bool = False) -> tuple[str, bool, int]:
        _update_movement_tracker(force=True)
        if not bool(_movement_position_known):
            prefix = "Movement" if bool(compact) else "Movement status"
            return f"{prefix}: unavailable", True, 0
        now = int(_now_ms())
        last_ms = int(_movement_last_ms or 0)
        elapsed_ms = max(0, int(now - int(last_ms or now)))
        recently_moved = bool(_movement_recently_moved(now))
        prefix = "Movement" if bool(compact) else "Movement status"
        wait_reason = str(_movement_wait_reason or "")
        if bool(compact):
            if recently_moved:
                return f"{prefix}: recent", True, int(elapsed_ms)
            return f"{prefix}: waiting", False, int(elapsed_ms)
        if recently_moved:
            return f"Movement status: Recently moved ({elapsed_ms} ms ago)", True, int(elapsed_ms)
        if wait_reason == "map_load":
            return f"{prefix}: Waiting for movement after map load", False, int(elapsed_ms)
        if wait_reason == "startup":
            return f"{prefix}: Waiting for movement after startup", False, int(elapsed_ms)
        return f"{prefix}: Standing still ({elapsed_ms} ms ago)", False, int(elapsed_ms)

    def _movement_requirement_attr(category: str) -> str:
        category_key = str(category or "").strip().lower()
        attrs = {
            "explorable": "movement_require_explorable",
            "summoning": "movement_require_summoning",
            "mbdp": "movement_require_mbdp",
            "alcohol": "movement_require_alcohol",
            "party_items": "movement_require_party_items",
            "sweets": "movement_require_sweets",
        }
        return attrs.get(category_key, "")

    def _movement_category_label(category: str) -> str:
        category_key = str(category or "").strip().lower()
        labels = {
            "explorable": "Explorable consumables",
            "summoning": "Summoning items",
            "mbdp": "Morale/DP items",
            "alcohol": "Alcohol",
            "party_items": "Party Items",
            "sweets": "Sweets",
        }
        return labels.get(category_key, "Consumables")

    def _movement_required_for_category(category: str) -> bool:
        if cfg is None:
            return False
        attr = _movement_requirement_attr(category)
        if not attr:
            return False
        if not bool(getattr(cfg, attr, False)):
            return False
        category_key = str(category or "").strip().lower()
        if category_key == "alcohol" and bool(getattr(cfg, "movement_alcohol_fast_only", False)):
            return bool(getattr(cfg, "alcohol_fast_spending", False))
        if category_key == "party_items" and bool(getattr(cfg, "movement_party_items_speed_only", False)):
            return bool(_party_item_interval_ms() < int(_movement_party_items_fast_threshold_ms()))
        if category_key == "sweets" and bool(getattr(cfg, "movement_sweets_fast_only", False)):
            return bool(getattr(cfg, "sweets_fast_spending", False))
        return True

    def _movement_gate_allows(category: str) -> bool:
        if not _movement_required_for_category(category):
            return True
        return bool(_movement_recently_moved())

    def _movement_category_for_spec(spec: dict) -> str:
        if _is_party_item_spec(spec):
            return "party_items"
        if _is_summoning_spec(spec):
            return "summoning"
        if _is_sweets_spec(spec):
            return "sweets"
        use_where = str(spec.get("use_where", "explorable") or "explorable").strip().lower()
        if use_where in ("explorable", "both"):
            return "explorable"
        return ""

    def _record_movement_block(category: str, label: str):
        category_key = str(category or "").strip().lower()
        if not category_key:
            return
        wt = _warn_timer_for(f"movement_required_{category_key}")
        if not (wt.IsStopped() or wt.HasElapsed(8000)):
            return
        wt.Start()
        category_label = _movement_category_label(category_key)
        clean_label = str(label or category_label).strip() or category_label
        _record_blocked_action(f"movement_required_{category_key}", f"{category_label}: waiting for movement")
        _debug(f"Skipping {clean_label}: movement required.", Console.MessageType.Debug)

    def _deposit_dest_key(model_id: int, bag_id: int, slot: int) -> tuple[int, int, int]:
        return int(model_id), int(bag_id), int(slot)

    def _is_deposit_dest_on_cooldown(model_id: int, bag_id: int, slot: int, now_ms: int | None = None) -> bool:
        now = int(_now_ms() if now_ms is None else now_ms)
        k = _deposit_dest_key(model_id, bag_id, slot)
        until = int(_vault_deposit_dest_cooldown_until.get(k, 0) or 0)
        if until <= now:
            if k in _vault_deposit_dest_cooldown_until:
                del _vault_deposit_dest_cooldown_until[k]
            return False
        return True

    def _mark_deposit_dest_cooldown(model_id: int, bag_id: int, slot: int, cooldown_ms: int = 6000):
        now = int(_now_ms())
        k = _deposit_dest_key(model_id, bag_id, slot)
        _vault_deposit_dest_cooldown_until[k] = int(now + max(250, int(cooldown_ms)))

    def _vault_action_key(action: str, model_id: int) -> tuple[str, int]:
        return str(action or ""), int(model_id or 0)

    def _is_vault_action_on_cooldown(action: str, model_id: int, now_ms: int | None = None) -> bool:
        now = int(_now_ms() if now_ms is None else now_ms)
        k = _vault_action_key(action, model_id)
        until = int(_vault_action_cooldown_until.get(k, 0) or 0)
        if until <= now:
            if k in _vault_action_cooldown_until:
                del _vault_action_cooldown_until[k]
            return False
        return True

    def _mark_vault_action_cooldown(action: str, model_id: int, cooldown_ms: int = 15000):
        now = int(_now_ms())
        k = _vault_action_key(action, model_id)
        _vault_action_cooldown_until[k] = int(now + max(500, int(cooldown_ms)))

    def _clear_vault_pending(action: str, model_id: int):
        k = _vault_action_key(action, model_id)
        if k in _vault_pending_state:
            del _vault_pending_state[k]

    def _record_vault_pending(action: str, model_id: int, inventory_count: int) -> int:
        now = int(_now_ms())
        k = _vault_action_key(action, model_id)
        inv_count = int(inventory_count or 0)
        state = _vault_pending_state.get(k)
        repeats = 1
        if isinstance(state, dict):
            prev_count = int(state.get("inventory_count", -999999))
            prev_ms = int(state.get("last_ms", 0))
            prev_repeats = int(state.get("repeats", 0))
            if prev_count == inv_count and (now - prev_ms) <= 15000:
                repeats = int(prev_repeats + 1)
        _vault_pending_state[k] = {"inventory_count": inv_count, "last_ms": int(now), "repeats": int(repeats)}
        return int(repeats)

    def _runtime_sync_from_cfg_full():
        if cfg is None:
            return
        for c in ALL_CONSUMABLES:
            k = c["key"]
            _rt.runtime_selected[k] = bool(cfg.selected.get(k, False))
            _rt.runtime_enabled[k] = bool(cfg.enabled.get(k, False))
        for a in ALCOHOL_ITEMS:
            k = a["key"]
            _rt.runtime_alcohol_selected[k] = bool(cfg.alcohol_selected.get(k, False))
            _rt.runtime_alcohol_enabled[k] = bool(cfg.alcohol_enabled_items.get(k, False))

    def _clear_one_shot_synced_enabled_defaults_if_needed() -> bool:
        if cfg is None or not bool(getattr(cfg, "_sync_selection_enabled_state_once", False)):
            return False

        for c in ALL_CONSUMABLES:
            key = str(c.get("key", "") or "")
            if key:
                cfg.enabled[key] = False
        for a in ALCOHOL_ITEMS:
            key = str(a.get("key", "") or "")
            if key:
                cfg.alcohol_enabled_items[key] = False

        cfg._sync_selection_enabled_state_once = False
        cfg.mark_dirty()
        cfg.save_if_dirty_throttled(0)

        try:
            ini_handler = _get_ini_handler()
            config = ini_handler.reload()
            if config.has_section(INI_SECTION):
                config.set(INI_SECTION, PYCONS_SYNC_SELECTION_ENABLED_STATE_ONCE_KEY, "False")
                ini_handler.save(config)
        except Exception:
            pass
        return True

    def _force_bind_ini_handler_to_account() -> bool:
        global _ini_handler_cache, _ini_path_cache, _ini_generic_cached_with_email_logged
        try:
            account_email = str(Player.GetAccountEmail() or "").strip()
        except Exception:
            account_email = ""
        if not account_email:
            return False

        new_path = _resolve_account_ini_path(account_email, migrate_legacy=True, log_migration=False)
        if _norm_path_lower(new_path) == _norm_path_lower(_ini_path_cache):
            return False

        try:
            parent_dir = os.path.dirname(str(new_path or ""))
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
        except Exception:
            pass

        _ini_path_cache = new_path
        _ini_handler_cache = IniHandler(_ini_path_cache)
        _ini_generic_cached_with_email_logged = False
        return True

    def pycons_reload_config_from_disk(reason: str = "") -> tuple[bool, str]:
        global cfg
        try:
            _force_bind_ini_handler_to_account()
            cfg = Config()
            _runtime_sync_from_cfg_full()
            cleared_one_shot_enabled_defaults = _clear_one_shot_synced_enabled_defaults_if_needed()
            _team_flags_cache.clear()
            try:
                _local_team_flags_refresh_timer.Stop()
            except Exception:
                pass
            detail = "Pycons config reloaded from disk."
            if cleared_one_shot_enabled_defaults:
                detail = f"{detail} Synced ON/OFF state is active for this session only."
            if reason:
                detail = f"{detail} Reason: {str(reason)}."
            return True, detail
        except Exception as exc:
            return False, str(exc)

    def _runtime_regular_enabled(key: str) -> bool:
        return bool(_rt.runtime_enabled.get(key, bool(cfg.enabled.get(key, False))))

    def _runtime_alcohol_enabled(key: str) -> bool:
        return bool(_rt.runtime_alcohol_enabled.get(key, bool(cfg.alcohol_enabled_items.get(key, False))))

    def _main_runtime_persist_enabled() -> bool:
        return bool(getattr(cfg, "persist_main_runtime_toggles", False))

    def _set_main_runtime_regular_enabled(key: str, enabled: bool):
        value = bool(enabled)
        _rt.runtime_enabled[key] = value
        if _main_runtime_persist_enabled():
            if bool(cfg.enabled.get(key, False)) != value:
                cfg.enabled[key] = value
                cfg.mark_dirty()

    def _set_main_runtime_alcohol_enabled(key: str, enabled: bool):
        value = bool(enabled)
        _rt.runtime_alcohol_enabled[key] = value
        if _main_runtime_persist_enabled():
            if bool(cfg.alcohol_enabled_items.get(key, False)) != value:
                cfg.alcohol_enabled_items[key] = value
                cfg.mark_dirty()

    def _enabled_selected_keys():
        return [
            k
            for k in cfg.enabled.keys()
            if bool(cfg.selected.get(k, False))
            and _runtime_regular_enabled(k)
            and not _is_party_item_spec(ALL_BY_KEY.get(k, {}))
        ]

    def _enabled_selected_party_item_keys() -> list[str]:
        out: list[str] = []
        for spec in PARTY_ITEMS:
            key = str(spec.get("key", "") or "")
            if key and bool(cfg.selected.get(key, False)) and _runtime_regular_enabled(key):
                out.append(key)
        return out

    def _enabled_selected_sweet_keys() -> list[str]:
        out: list[str] = []
        for spec in SWEET_ITEMS:
            key = str(spec.get("key", "") or "")
            if key and bool(cfg.selected.get(key, False)) and _runtime_regular_enabled(key):
                out.append(key)
        return out

    def _alcohol_pool_keys():
        out = []
        for k in cfg.alcohol_selected.keys():
            if bool(cfg.alcohol_selected.get(k, False)) and _runtime_alcohol_enabled(k):
                out.append(k)
        return out

    def _any_selected_anywhere() -> bool:
        for v in cfg.selected.values():
            if bool(v):
                return True
        for v in cfg.alcohol_selected.values():
            if bool(v):
                return True
        return False

    # -------------------------
    # Hard "do not consume" gates
    # -------------------------
    def _player_is_dead() -> bool:
        try:
            fn = getattr(Player, "IsDead", None)
            if callable(fn):
                return bool(fn())
        except Exception:
            pass
        return False

    def _map_is_loading() -> bool:
        try:
            for nm in ("IsLoading", "IsMapLoading", "IsLoadingMap", "IsInLoadingScreen"):
                fn = getattr(Map, nm, None)
                if callable(fn):
                    if bool(fn()):
                        return True
        except Exception:
            pass
        return False

    def _inventory_ready() -> bool:
        global _inv_ready_cached, _inv_ready_ts
        now = _now_ms()
        if (now - int(_inv_ready_ts)) < 500:
            return bool(_inv_ready_cached)

        ready = True
        try:
            inv = getattr(GLOBAL_CACHE, "Inventory", None)
            if inv is not None:
                fn = getattr(inv, "IsReady", None)
                if callable(fn):
                    ready = bool(fn())
                else:
                    try:
                        ItemArray.GetItemArray([Bag.Backpack])
                        ready = True
                    except Exception:
                        ready = False
            else:
                ready = True
        except Exception:
            ready = False

        _inv_ready_cached = bool(ready)
        _inv_ready_ts = int(now)
        return bool(ready)

    def _should_block_consumption() -> bool:
        if _player_is_dead():
            return True
        if _map_is_loading():
            return True
        if not _inventory_ready():
            return True
        return False

    def _consume_precheck():
        """
        Stable gate ordering for regular consumables.
        Returns (ok, keys, in_explorable).
        """
        keys = _enabled_selected_keys()
        if not keys:
            return False, keys, False
        if not Routines.Checks.Map.MapValid():
            return False, keys, False
        if _should_block_consumption():
            return False, keys, False
        if not (aftercast_timer.IsStopped() or aftercast_timer.HasElapsed(int(AFTERCAST_MS))):
            return False, keys, False
        return True, keys, bool(_in_explorable())

    def _party_items_precheck():
        """
        Stable gate ordering for Party Items.
        Returns (ok, keys, in_explorable).
        """
        keys = _enabled_selected_party_item_keys()
        if not keys:
            return False, keys, False
        if not Routines.Checks.Map.MapValid():
            return False, keys, False
        if _should_block_consumption():
            return False, keys, False
        if not (aftercast_timer.IsStopped() or aftercast_timer.HasElapsed(int(AFTERCAST_MS))):
            return False, keys, False
        if not _movement_gate_allows("party_items"):
            _record_movement_block("party_items", "Party Items")
            return False, keys, False
        return True, keys, bool(_in_explorable())

    def _sweets_precheck():
        """
        Stable gate ordering for fast sweets spending.
        Returns (ok, keys, in_explorable).
        """
        if not bool(getattr(cfg, "sweets_fast_spending", False)):
            return False, [], False
        keys = _enabled_selected_sweet_keys()
        if not keys:
            return False, keys, False
        if not Routines.Checks.Map.MapValid():
            return False, keys, False
        if _should_block_consumption():
            return False, keys, False
        if not (aftercast_timer.IsStopped() or aftercast_timer.HasElapsed(int(AFTERCAST_MS))):
            return False, keys, False
        if not _movement_gate_allows("sweets"):
            _record_movement_block("sweets", "Sweets")
            return False, keys, False
        return True, keys, bool(_in_explorable())

    def _alcohol_precheck():
        """
        Stable gate ordering for alcohol upkeep.
        Returns (ok, target, pool_keys, in_explorable, now_ms, cur_level).
        """
        if not bool(cfg.alcohol_enabled):
            return False, 0, [], False, 0, 0

        fast_spending = bool(getattr(cfg, "alcohol_fast_spending", False))
        target = int(cfg.alcohol_target_level)
        if target <= 0 and not fast_spending:
            return False, target, [], False, 0, 0

        if not bool(cfg.alcohol_use_explorable) and not bool(cfg.alcohol_use_outpost):
            return False, target, [], False, 0, 0

        if not Routines.Checks.Map.MapValid():
            return False, target, [], False, 0, 0

        if _should_block_consumption():
            return False, target, [], False, 0, 0

        if not (aftercast_timer.IsStopped() or aftercast_timer.HasElapsed(int(AFTERCAST_MS))):
            return False, target, [], False, 0, 0

        if not _movement_gate_allows("alcohol"):
            _record_movement_block("alcohol", "Alcohol")
            return False, target, [], False, 0, 0

        pool_keys = _alcohol_pool_keys()
        if not pool_keys:
            return False, target, pool_keys, False, 0, 0

        in_explorable = bool(_in_explorable())
        if not _alcohol_allowed_here(in_explorable):
            return False, target, pool_keys, in_explorable, 0, 0

        now = _now_ms()
        cur_level = _alcohol_current_level(now)
        if cur_level >= target and not fast_spending:
            return False, target, pool_keys, in_explorable, now, cur_level

        return True, target, pool_keys, in_explorable, now, cur_level

    def _apply_selection_change_core(
        key: str,
        selected: bool,
        selected_map: dict,
        runtime_selected_map: dict,
        enabled_map: dict,
        runtime_enabled_map: dict,
    ):
        selected_map[key] = bool(selected)
        runtime_selected_map[key] = bool(selected)
        if not bool(selected):
            enabled_map[key] = False
            runtime_enabled_map[key] = False
            _apply_restock_target_on_deselect(key)
            if not _any_selected_anywhere():
                cfg.show_selected_list = False
                request_collapse_selected[0] = True
        else:
            _apply_restock_target_on_select(key)
            if not bool(cfg.show_selected_list):
                cfg.show_selected_list = True
            request_expand_selected[0] = True
        cfg.mark_dirty()

    def _apply_regular_selection_change(key: str, selected: bool):
        _apply_selection_change_core(
            key,
            bool(selected),
            cfg.selected,
            _rt.runtime_selected,
            cfg.enabled,
            _rt.runtime_enabled,
        )

    def _apply_alcohol_selection_change(key: str, selected: bool):
        _apply_selection_change_core(
            key,
            bool(selected),
            cfg.alcohol_selected,
            _rt.runtime_alcohol_selected,
            cfg.alcohol_enabled_items,
            _rt.runtime_alcohol_enabled,
        )

    # -------------------------
    # Skill resolution (robust)
    # -------------------------
    def _skill_candidates(base_name: str):
        if not base_name:
            return []
        s = str(base_name)
        out = []
        seen = set()

        def add(x):
            if x and x not in seen:
                seen.add(x)
                out.append(x)

        add(s)
        add(s.replace(" ", "_"))
        add(s.replace("(", "").replace(")", ""))

        for dur in ["short", "medium", "long"]:
            token = f"({dur})"
            if token in s:
                add(s.replace(token, f"_{dur}"))
                add(s.replace(token, dur))
                add(s.replace(token, ""))

        for nm in list(out):
            add(nm + "_item_effect")
            add(nm + "_effect")

        return out

    def _resolve_effect_id_for(key: str, spec: dict) -> int:
        explicit_effect_id = int(spec.get("effect_id", 0) or 0)
        if explicit_effect_id > 0:
            _skill_id_cache[key] = int(explicit_effect_id)
            return int(explicit_effect_id)

        cached = int(_skill_id_cache.get(key, 0))
        if cached > 0:
            return cached

        rt = _retry_timer_for(key)
        if not (rt.IsStopped() or rt.HasElapsed(2500)):
            return 0
        rt.Start()

        skills = spec.get("skills") or []
        for base in skills:
            for cand in _skill_candidates(base):
                try:
                    sid = int(GLOBAL_CACHE.Skill.GetID(cand))
                except Exception:
                    sid = 0
                if sid > 0:
                    _skill_id_cache[key] = sid
                    _skill_name_cache[key] = str(cand)
                    return sid

        _skill_id_cache[key] = 0
        _skill_name_cache[key] = str(skills[0]) if skills else ""
        return 0

    def _has_effect(effect_id: int) -> bool:
        if effect_id <= 0:
            return False
        try:
            pid = int(Player.GetAgentID())
            return bool(Effects.EffectExists(pid, int(effect_id)) or Effects.BuffExists(pid, int(effect_id)))
        except Exception:
            return False

    def _fallback_active(key: str, spec: dict) -> bool:
        dur = int(spec.get("fallback_duration_ms", 0) or 0)
        if dur <= 0:
            return False
        last = int(_last_used_ms.get(key, 0) or 0)
        return last > 0 and (_now_ms() - last) < dur

    def _in_explorable() -> bool:
        try:
            return bool(Map.IsExplorable())
        except Exception:
            return False

    def _allowed_here(spec: dict, in_explorable: bool) -> bool:
        use_where = str(spec.get("use_where", "explorable")).lower().strip()
        if use_where == "both":
            return True
        if use_where == "party_items":
            return True
        if use_where == "outpost":
            return not in_explorable
        return in_explorable

    def _alcohol_allowed_here(in_explorable: bool) -> bool:
        if bool(in_explorable):
            return bool(cfg.alcohol_use_explorable)
        return bool(cfg.alcohol_use_outpost)

    def _is_summoning_spec(spec: dict) -> bool:
        return str(spec.get("use_where", "") or "").strip().lower() == "summoning"

    def _is_party_item_spec(spec: dict) -> bool:
        return str(spec.get("use_where", "") or "").strip().lower() == "party_items"

    def _is_sweets_spec(spec: dict) -> bool:
        return str(spec.get("use_where", "") or "").strip().lower() == "outpost"

    def _is_guild_hall() -> bool:
        try:
            return bool(Map.IsGuildHall())
        except Exception:
            return False

    def _is_outpost_or_guild_hall() -> bool:
        if _is_guild_hall():
            return True
        try:
            return bool(Map.IsOutpost())
        except Exception:
            return False

    def _party_item_block_reason(key: str, spec: dict) -> str:
        if not _is_party_item_spec(spec):
            return ""

        if bool(spec.get("guild_hall_only", False)) and not _is_guild_hall():
            return "only used in a guild hall"

        if bool(spec.get("town_or_guild_hall_only", False)) and not _is_outpost_or_guild_hall():
            return "only used in towns, outposts, or guild halls"

        blocked_effect_id = int(spec.get("blocked_effect_id", 0) or 0)
        if blocked_effect_id > 0 and _has_effect(blocked_effect_id):
            return "waiting for Tonic Tipsiness"

        return ""

    def _record_party_item_block(key: str, label: str, reason: str):
        clean_reason = str(reason or "").strip()
        if not clean_reason:
            return
        wt = _warn_timer_for(f"party_item_block_{key}")
        if not (wt.IsStopped() or wt.HasElapsed(8000)):
            return
        wt.Start()
        _record_blocked_action(f"party_item_block_{key}", f"{label}: {clean_reason}")
        _debug(f"Skipping {label}: {clean_reason}.", Console.MessageType.Debug)

    def _party_player_agent_ids() -> set[int]:
        out = set()
        try:
            me = int(Player.GetAgentID() or 0)
            if me > 0:
                out.add(me)
        except Exception:
            pass
        try:
            for player in Party.GetPlayers() or []:
                try:
                    login_number = int(getattr(player, "login_number", 0) or 0)
                    if login_number <= 0:
                        continue
                    agent_id = int(Party.Players.GetAgentIDByLoginNumber(login_number) or 0)
                    if agent_id > 0:
                        out.add(agent_id)
                except Exception:
                    continue
        except Exception:
            pass
        return out

    def _has_active_party_summon() -> bool:
        owner_ids = _party_player_agent_ids()
        try:
            others = Party.GetOthers() or []
        except Exception:
            others = []

        for other in others:
            try:
                agent_id = int(other or 0)
            except Exception:
                agent_id = 0
            if agent_id <= 0:
                continue
            try:
                if not Agent.IsAlive(agent_id):
                    continue
            except Exception:
                continue
            try:
                if Agent.IsSpirit(agent_id) or Agent.IsMinion(agent_id):
                    continue
            except Exception:
                pass

            try:
                model_id = int(Agent.GetModelID(agent_id) or 0)
            except Exception:
                model_id = 0
            if model_id in SUMMONING_UNIQUE_PARTY_MODEL_IDS:
                return True

            try:
                owner_id = int(Agent.GetOwnerID(agent_id) or 0)
            except Exception:
                owner_id = 0
            if owner_id > 0 and owner_id in owner_ids:
                try:
                    if Agent.IsNPC(agent_id):
                        return True
                except Exception:
                    return True

        return False

    def _summoning_block_reason(key: str, in_explorable: bool) -> str:
        if not bool(in_explorable):
            return "summoning items require an explorable area"

        if str(key or "") == "igneous_summoning_stone":
            try:
                if int(Player.GetLevel() or 0) >= 20:
                    return "Igneous Summoning Stone is only usable below level 20"
            except Exception:
                pass

        try:
            current_sp, _ = Player.GetSkillPointData()
            if int(current_sp or 0) <= 0:
                return "no skill points available for summoning"
        except Exception:
            pass

        try:
            if int(Map.GetMapID() or 0) in SUMMONING_RESTRICTED_MAP_IDS:
                return "summoning items are blocked in this area"
        except Exception:
            pass

        try:
            active_quests = set(int(qid) for qid in (Quest.GetQuestLogIds() or []))
            if active_quests.intersection(SUMMONING_RESTRICTED_QUEST_IDS):
                return "summoning items are blocked in this quest context"
        except Exception:
            pass

        if _has_effect(int(SUMMONING_SICKNESS_EFFECT_ID)):
            return "Summoning Sickness is active"

        if _has_active_party_summon():
            return "a summoned ally is already active"

        return ""

    def _record_summoning_block(key: str, label: str, reason: str):
        if not reason:
            return
        slug = re.sub(r"[^a-z0-9]+", "_", f"{key}_{reason}".lower()).strip("_")[:56]
        code = f"summon_block_{slug}"
        _record_blocked_action(code, f"{label}: {reason}")
        wt = _warn_timer_for(code)
        if wt.IsStopped() or wt.HasElapsed(8000):
            wt.Start()
            _debug(f"Skipping {label}: {reason}.", Console.MessageType.Info)

    # -------------------------
    # Inventory caching + stock counts
    # -------------------------
    def _schedule_refresh(delay_ms: int):
        if bool(getattr(cfg, "experimental_mainloop_refresh_queue", EXPERIMENTAL_MAINLOOP_REFRESH_QUEUE_DEFAULT)):
            try:
                due_ms = int(_now_ms()) + max(0, int(delay_ms))
            except Exception:
                due_ms = int(_now_ms())
            # Keep this bounded in pathological loops.
            if len(_pending_refresh_due_ms) > 64:
                del _pending_refresh_due_ms[0:len(_pending_refresh_due_ms) - 64]
            _pending_refresh_due_ms.append(int(due_ms))
            return

        try:
            t = threading.Timer(delay_ms / 1000.0, lambda: _refresh_inventory_cache(force=True))
            t.daemon = True
            t.start()
        except Exception as e:
            try:
                _debug(f"Failed to schedule inventory refresh: {e}", Console.MessageType.Debug)
            except Exception:
                pass

    def _drain_scheduled_refresh_queue():
        if not bool(getattr(cfg, "experimental_mainloop_refresh_queue", EXPERIMENTAL_MAINLOOP_REFRESH_QUEUE_DEFAULT)):
            return
        if not _pending_refresh_due_ms:
            return

        now = int(_now_ms())
        due_count = 0
        for due in _pending_refresh_due_ms:
            try:
                if int(due) <= int(now):
                    due_count += 1
            except Exception:
                due_count += 1

        if due_count <= 0:
            return

        # Coalesce multiple due entries into one forced refresh this frame.
        del _pending_refresh_due_ms[0:due_count]
        _refresh_inventory_cache(force=True)

    def _refresh_inventory_cache(force: bool = False) -> bool:
        global _inv_cache_items, _inv_cache_ts, _inv_counts_by_model, _inv_best_item_id_by_model
        now = _now_ms()
        if (not force) and _inv_cache_items is not None and (now - int(_inv_cache_ts)) < INVENTORY_CACHE_MS:
            return True

        try:
            item_ids = []
            counts = {}
            best_item_ids = {}
            best_qty_by_model = {}
            bag_handles = _get_inventory_bag_handles()
            for _bag_enum, _bag, _size, items in bag_handles:
                for it in items:
                    try:
                        item_id = int(getattr(it, "item_id", 0) or 0)
                        mid = int(getattr(it, "model_id", 0) or 0)
                        qty = int(getattr(it, "quantity", 0) or 0)
                    except Exception:
                        continue
                    if item_id <= 0 or mid <= 0:
                        continue
                    if qty <= 0:
                        try:
                            qty = int(Item.Properties.GetQuantity(int(item_id)) or 0)
                        except Exception:
                            qty = 0
                    if qty <= 0:
                        qty = 1
                    item_ids.append(int(item_id))
                    mid = int(mid)
                    qty = int(qty)
                    counts[mid] = int(counts.get(mid, 0)) + qty
                    if qty < int(best_qty_by_model.get(mid, 10**9)):
                        best_qty_by_model[mid] = qty
                        best_item_ids[mid] = int(item_id)

            # Fallback path for edge cases where bag snapshots are temporarily unavailable.
            if not item_ids:
                items = ItemArray.GetItemArray(SCAN_BAGS)
                for item_id in list(items or []):
                    try:
                        iid = int(item_id or 0)
                        if iid <= 0:
                            continue
                        mid = int(Item.GetModelID(iid))
                        if mid <= 0:
                            continue
                        qty = 1
                        try:
                            qty = int(Item.Properties.GetQuantity(iid) or 0)
                        except Exception:
                            qty = 1
                        if qty <= 0:
                            qty = 1
                        item_ids.append(int(iid))
                        mid = int(mid)
                        qty = int(qty)
                        counts[mid] = int(counts.get(mid, 0)) + qty
                        if qty < int(best_qty_by_model.get(mid, 10**9)):
                            best_qty_by_model[mid] = qty
                            best_item_ids[mid] = int(iid)
                    except Exception:
                        continue

            _inv_cache_items = list(item_ids)
            _inv_counts_by_model = counts
            _inv_best_item_id_by_model = best_item_ids
            _inv_cache_ts = int(now)
            return True
        except Exception as e:
            _inv_cache_items = None
            _inv_counts_by_model = {}
            _inv_best_item_id_by_model = {}
            _inv_cache_ts = int(now)
            _debug(f"Inventory cache refresh failed: {e}", Console.MessageType.Warning)
            return False

    def _stock_status_for_model_id(model_id: int):
        if model_id <= 0:
            return False, 0
        if _inv_cache_items is None:
            return False, 0
        return True, int(_inv_counts_by_model.get(int(model_id), 0))

    def _find_item_id_by_model_id(model_id: int) -> int:
        model_id = int(model_id or 0)
        if model_id <= 0:
            return 0

        if _refresh_inventory_cache(False):
            cached_item_id = int(_inv_best_item_id_by_model.get(int(model_id), 0) or 0)
            if cached_item_id > 0:
                return int(cached_item_id)

        best_item_id = 0
        best_qty = 10**9
        for _bag_enum, _bag, _size, items in _get_inventory_bag_handles():
            for it in items:
                try:
                    mid = int(getattr(it, "model_id", 0) or 0)
                    if int(mid) != int(model_id):
                        continue
                    item_id = int(getattr(it, "item_id", 0) or 0)
                    if item_id <= 0:
                        continue
                    qty = int(getattr(it, "quantity", 0) or 0)
                    if qty <= 0:
                        try:
                            qty = int(Item.Properties.GetQuantity(int(item_id)) or 0)
                        except Exception:
                            qty = 0
                    qty = max(1, int(qty))
                except Exception:
                    continue
                if qty < best_qty:
                    best_qty = int(qty)
                    best_item_id = int(item_id)

        if best_item_id > 0:
            return int(best_item_id)

        if not _inv_cache_items:
            return 0
        for item_id in _inv_cache_items:
            try:
                if int(Item.GetModelID(int(item_id))) == int(model_id):
                    return int(item_id)
            except Exception:
                continue
        return 0

    def _inventory_contains_item_id(item_id: int) -> bool:
        item_id = int(item_id or 0)
        if item_id <= 0:
            return False

        for _bag_enum, _bag, _size, items in _get_inventory_bag_handles():
            for it in items:
                try:
                    if int(getattr(it, "item_id", 0) or 0) == int(item_id):
                        return True
                except Exception:
                    continue
        return False

    def _storage_contains_item_id(item_id: int) -> bool:
        item_id = int(item_id or 0)
        if item_id <= 0:
            return False

        for _bag_enum, _bag, _size, items in _get_storage_bag_handles():
            for it in items:
                try:
                    if int(getattr(it, "item_id", 0) or 0) == int(item_id):
                        return True
                except Exception:
                    continue
        return False

    def _confirm_deposit_move(
        model_id: int,
        source_item_id: int,
        source_qty_before: int,
        before_count: int,
        expected_move: int,
    ) -> tuple[int, int]:
        moved_qty_actual = 0
        after_count = int(before_count)
        after_known = False
        expected_move = int(max(1, int(expected_move or 1)))
        source_qty_before = int(max(1, int(source_qty_before or 1)))

        # Probe a few times because inventory snapshots can lag after MoveItem is accepted.
        for probe in range(5):
            _refresh_inventory_cache(force=True)
            known, count = _stock_status_for_model_id(model_id)
            if known:
                after_known = True
                after_count = int(count)
                moved_qty_actual = max(
                    int(moved_qty_actual),
                    int(max(0, int(before_count) - int(after_count))),
                )

            source_qty_after = -1
            try:
                source_qty_after = int(Item.Properties.GetQuantity(int(source_item_id)) or 0)
            except Exception:
                source_qty_after = -1

            if source_qty_after > 0:
                moved_qty_actual = max(
                    int(moved_qty_actual),
                    int(max(0, int(source_qty_before) - int(source_qty_after))),
                )
            elif source_qty_after == 0 and not _inventory_contains_item_id(int(source_item_id)):
                # Source stack vanished from inventory; treat as moved from that stack.
                moved_qty_actual = max(
                    int(moved_qty_actual),
                    int(min(int(source_qty_before), int(expected_move))),
                )

            moved_qty_actual = int(max(0, min(int(expected_move), int(moved_qty_actual))))
            if moved_qty_actual > 0:
                break

            if probe < 4:
                try:
                    threading.Event().wait(0.06)
                except Exception:
                    pass

        effective_after_count = int(after_count)
        if moved_qty_actual > 0 and (not after_known or int(effective_after_count) >= int(before_count)):
            effective_after_count = int(max(0, int(before_count) - int(moved_qty_actual)))

        return int(moved_qty_actual), int(effective_after_count)

    def _confirm_withdraw_move(
        model_id: int,
        source_item_id: int,
        source_qty_before: int,
        before_count: int,
        expected_move: int,
    ) -> tuple[int, int]:
        moved_qty_actual = 0
        after_count = int(before_count)
        after_known = False
        expected_move = int(max(1, int(expected_move or 1)))
        source_qty_before = int(max(1, int(source_qty_before or 1)))

        # Probe a few times because inventory snapshots can lag after MoveItem is accepted.
        for probe in range(5):
            _refresh_inventory_cache(force=True)
            known, count = _stock_status_for_model_id(model_id)
            if known:
                after_known = True
                after_count = int(count)
                moved_qty_actual = max(
                    int(moved_qty_actual),
                    int(max(0, int(after_count) - int(before_count))),
                )

            source_qty_after = -1
            try:
                source_qty_after = int(Item.Properties.GetQuantity(int(source_item_id)) or 0)
            except Exception:
                source_qty_after = -1

            if source_qty_after > 0:
                moved_qty_actual = max(
                    int(moved_qty_actual),
                    int(max(0, int(source_qty_before) - int(source_qty_after))),
                )
            elif source_qty_after == 0 and not _storage_contains_item_id(int(source_item_id)):
                # Source stack vanished from storage; treat as moved from that stack.
                moved_qty_actual = max(
                    int(moved_qty_actual),
                    int(min(int(source_qty_before), int(expected_move))),
                )

            moved_qty_actual = int(max(0, min(int(expected_move), int(moved_qty_actual))))
            if moved_qty_actual > 0:
                break

            if probe < 4:
                try:
                    threading.Event().wait(0.06)
                except Exception:
                    pass

        effective_after_count = int(after_count)
        if moved_qty_actual > 0 and (not after_known or int(effective_after_count) <= int(before_count)):
            effective_after_count = int(before_count) + int(moved_qty_actual)

        return int(moved_qty_actual), int(effective_after_count)

    def _restock_should_keep_target_on_deselect() -> bool:
        try:
            return bool(getattr(cfg, "restock_keep_target_on_deselect", True))
        except Exception:
            return True

    def _restock_item_enabled(key: str) -> bool:
        return bool(getattr(cfg, "restock_enabled_items", {}).get(str(key or ""), False))

    def _set_restock_item_enabled(key: str, enabled: bool):
        key = str(key or "")
        if not key:
            return
        value = bool(enabled)
        changed = bool(getattr(cfg, "restock_enabled_items", {}).get(key, False)) != value
        cfg.restock_enabled_items[key] = value
        if value and _restock_target_for_key(key) <= 0:
            cfg.restock_targets[key] = int(VAULT_RESTOCK_TARGET_QTY)
            changed = True
        if changed:
            cfg.mark_dirty()

    def _apply_restock_target_on_select(key: str):
        key = str(key or "")
        if not key:
            return
        if _restock_item_enabled(key) and _restock_target_for_key(key) <= 0:
            cfg.restock_targets[key] = int(VAULT_RESTOCK_TARGET_QTY)

    def _apply_restock_target_on_deselect(key: str):
        key = str(key or "")
        if not key:
            return
        if not _restock_should_keep_target_on_deselect():
            cfg.restock_targets[key] = 0

    def _restock_target_for_key(key: str) -> int:
        try:
            raw_val = int(cfg.restock_targets.get(key, VAULT_RESTOCK_TARGET_QTY))
        except Exception:
            raw_val = int(VAULT_RESTOCK_TARGET_QTY)
        return max(0, min(2500, int(raw_val)))

    def _restock_mode_value() -> int:
        try:
            raw_val = int(getattr(cfg, "restock_mode", DEFAULT_RESTOCK_MODE))
        except Exception:
            raw_val = int(DEFAULT_RESTOCK_MODE)
        return max(RESTOCK_MODE_BALANCED, min(RESTOCK_MODE_DEPOSIT_ONLY, int(raw_val)))

    def _restock_move_cap_per_cycle_value() -> int:
        try:
            raw_val = int(getattr(cfg, "restock_move_cap_per_cycle", DEFAULT_RESTOCK_MOVE_CAP_PER_CYCLE))
        except Exception:
            raw_val = int(DEFAULT_RESTOCK_MOVE_CAP_PER_CYCLE)
        return max(MIN_RESTOCK_MOVE_CAP_PER_CYCLE, min(MAX_RESTOCK_MOVE_CAP_PER_CYCLE, int(raw_val)))

    def _selected_restock_specs() -> list[tuple[str, dict]]:
        out = []
        for spec in ALL_CONSUMABLES:
            key = str(spec.get("key", "") or "")
            if key and bool(cfg.selected.get(key, False)):
                out.append((key, spec))
        for spec in ALCOHOL_ITEMS:
            key = str(spec.get("key", "") or "")
            if key and bool(cfg.alcohol_selected.get(key, False)):
                out.append((key, spec))
        return out

    def _restock_regular_enabled(key: str) -> bool:
        return bool(cfg.selected.get(key, False)) and bool(_restock_item_enabled(key))

    def _restock_alcohol_enabled(key: str) -> bool:
        return bool(cfg.alcohol_selected.get(key, False)) and bool(_restock_item_enabled(key))

    def _build_vault_restock_candidates():
        out = []
        seen_models = set()

        for spec in ALL_CONSUMABLES:
            key = str(spec.get("key", "") or "")
            if not key or not _restock_regular_enabled(key):
                continue
            model_id = int(spec.get("model_id", 0) or 0)
            if model_id <= 0:
                if int(_restock_target_for_key(key)) > 0:
                    wt = _warn_timer_for(f"restock_modelid_missing_{key}")
                    if wt.IsStopped() or wt.HasElapsed(15000):
                        wt.Start()
                        _record_blocked_action(
                            f"restock_modelid_missing_{key}",
                            f"{str(spec.get('label', key) or key)}: model_id=0",
                        )
                        _debug(f"Vault restock: skipping {spec.get('label', key)} because model_id is 0.", Console.MessageType.Warning)
                continue
            if model_id in seen_models:
                continue
            known, cnt = _stock_status_for_model_id(model_id)
            if not known:
                continue
            target = _restock_target_for_key(key)
            delta = int(target) - int(cnt)
            if delta != 0:
                out.append((key, spec, model_id, int(cnt), int(target), int(delta)))
            seen_models.add(model_id)

        for spec in ALCOHOL_ITEMS:
            key = str(spec.get("key", "") or "")
            if not key or not _restock_alcohol_enabled(key):
                continue
            model_id = int(spec.get("model_id", 0) or 0)
            if model_id <= 0:
                if int(_restock_target_for_key(key)) > 0:
                    wt = _warn_timer_for(f"restock_modelid_missing_{key}")
                    if wt.IsStopped() or wt.HasElapsed(15000):
                        wt.Start()
                        _record_blocked_action(
                            f"restock_modelid_missing_{key}",
                            f"{str(spec.get('label', key) or key)}: model_id=0",
                        )
                        _debug(f"Vault restock: skipping {spec.get('label', key)} because model_id is 0.", Console.MessageType.Warning)
                continue
            if model_id in seen_models:
                continue
            known, cnt = _stock_status_for_model_id(model_id)
            if not known:
                continue
            target = _restock_target_for_key(key)
            delta = int(target) - int(cnt)
            if delta != 0:
                out.append((key, spec, model_id, int(cnt), int(target), int(delta)))
            seen_models.add(model_id)

        return out

    def _ordered_vault_restock_candidates(candidates):
        shortage_first = [c for c in candidates if int(c[5]) > 0]
        excess_second = [c for c in candidates if int(c[5]) < 0]
        restock_mode = int(_restock_mode_value())
        if restock_mode == int(RESTOCK_MODE_WITHDRAW_ONLY):
            return shortage_first
        if restock_mode == int(RESTOCK_MODE_DEPOSIT_ONLY):
            return excess_second
        return shortage_first + excess_second

    def _has_actionable_vault_restock_need(inv, candidates) -> bool:
        if inv is None or not candidates:
            return False
        if not _refresh_inventory_cache(force=True):
            return False

        move_cap_per_cycle = int(_restock_move_cap_per_cycle_value())
        now_ms = _now_ms()
        for key, spec, model_id, _cur_count, _target_count, _delta in _ordered_vault_restock_candidates(candidates):
            if key in cfg.alcohol_selected:
                if not _restock_alcohol_enabled(key):
                    continue
            else:
                if not _restock_regular_enabled(key):
                    continue

            live_known, live_count = _stock_status_for_model_id(int(model_id))
            if not live_known:
                continue
            live_target = int(_restock_target_for_key(key))
            live_delta = int(live_target) - int(live_count)
            if live_delta == 0:
                continue

            if int(live_delta) > 0:
                if _is_vault_action_on_cooldown("withdraw", int(model_id), int(now_ms)):
                    continue
                try:
                    in_storage = int(inv.GetModelCountInStorage(int(model_id)))
                except Exception:
                    in_storage = 0
                to_withdraw = int(min(int(live_delta), int(in_storage), int(move_cap_per_cycle)))
                if to_withdraw > 0:
                    return True
                continue

            if _is_vault_action_on_cooldown("deposit", int(model_id), int(now_ms)):
                continue

            excess = int(min(max(0, -int(live_delta)), int(move_cap_per_cycle)))
            if excess <= 0:
                continue

            source_item_id = _find_item_id_by_model_id(int(model_id))
            source_is_stackable = True
            if source_item_id > 0:
                try:
                    source_is_stackable = bool(Item.Customization.IsStackable(int(source_item_id)))
                except Exception:
                    source_is_stackable = True

            probe_destinations = _storage_deposit_destinations(int(model_id), 1, bool(source_is_stackable))
            if probe_destinations:
                return True

        return False

    def _get_storage_bag_handles():
        candidates = [
            Bags.Storage1, Bags.Storage2, Bags.Storage3, Bags.Storage4,
            Bags.Storage5, Bags.Storage6, Bags.Storage7, Bags.Storage8,
            Bags.Storage9, Bags.Storage10, Bags.Storage11, Bags.Storage12,
            Bags.Storage13, Bags.Storage14,
        ]
        out = []
        for bag_enum in candidates:
            try:
                bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
                size = int(bag.GetSize() or 0)
                if size <= 0:
                    continue
                items = list(bag.GetItems() or [])
                out.append((bag_enum, bag, size, items))
            except Exception:
                continue
        out.sort(key=lambda entry: int(entry[0].value))
        return out

    def _get_inventory_bag_handles():
        candidates = [Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2]
        out = []
        for bag_enum in candidates:
            try:
                bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
                size = int(bag.GetSize() or 0)
                if size <= 0:
                    continue
                items = list(bag.GetItems() or [])
                out.append((bag_enum, bag, size, items))
            except Exception:
                continue
        out.sort(key=lambda entry: int(entry[0].value))
        return out

    def _storage_stack_entries(model_id: int) -> list[tuple[int, int, int, int]]:
        model_id = int(model_id or 0)
        if model_id <= 0:
            return []
        out = []
        for bag_enum, _bag, _size, items in _get_storage_bag_handles():
            for it in items:
                try:
                    if int(getattr(it, "model_id", 0) or 0) != model_id:
                        continue
                    item_id = int(getattr(it, "item_id", 0) or 0)
                    if item_id <= 0:
                        continue
                    qty = int(getattr(it, "quantity", 0) or 0)
                    if qty <= 0:
                        try:
                            qty = int(Item.Properties.GetQuantity(item_id) or 0)
                        except Exception:
                            qty = 0
                    if qty <= 0:
                        continue
                    slot = int(getattr(it, "slot", 0) or 0)
                    out.append((item_id, qty, int(bag_enum.value), slot))
                except Exception:
                    continue
        return out

    def _storage_slot_item_info(bag_id: int, slot: int) -> tuple[int, int]:
        bag_id = int(bag_id or 0)
        slot = int(slot)
        if bag_id <= 0:
            return 0, 0
        for bag_enum, _bag, _size, items in _get_storage_bag_handles():
            if int(bag_enum.value) != int(bag_id):
                continue
            for it in items:
                try:
                    if int(getattr(it, "slot", -99999) or -99999) != int(slot):
                        continue
                    item_id = int(getattr(it, "item_id", 0) or 0)
                    model_id = int(getattr(it, "model_id", 0) or 0)
                    return int(item_id), int(model_id)
                except Exception:
                    continue
            return 0, 0
        return 0, 0

    def _allow_slot_edge_candidates(size: int, occupied: set[int]) -> tuple[bool, bool]:
        size = int(size or 0)
        has_zero = 0 in occupied
        has_size = int(size) in occupied
        allow_zero = bool(has_zero and (not has_size))
        allow_size = bool(has_size and (not has_zero))
        if bool(getattr(cfg, "debug_logging", False)) and (bool(allow_zero) or bool(allow_size)):
            _debug(
                f"Vault restock: slot edge candidates enabled (size={int(size)}, "
                f"allow_zero={bool(allow_zero)}, allow_size={bool(allow_size)}).",
                Console.MessageType.Debug,
            )
        return bool(allow_zero), bool(allow_size)

    def _empty_slot_candidates(size: int, occupied_slots: set[int]) -> list[int]:
        size = int(size or 0)
        if size <= 0:
            return []

        occupied = set()
        for raw_slot in list(occupied_slots or []):
            try:
                occupied.add(int(raw_slot))
            except Exception:
                continue

        # Prefer interior slots valid in both 0-based and 1-based schemes.
        # Only use edge slots (0 or size) when indexing evidence is unambiguous.
        shared = [slot for slot in range(1, int(size)) if slot not in occupied]
        allow_zero_edge, allow_size_edge = _allow_slot_edge_candidates(int(size), occupied)

        out = []
        for slot in shared:
            slot = int(slot)
            if slot in occupied:
                continue
            if slot not in out:
                out.append(int(slot))
        if bool(allow_zero_edge) and 0 not in occupied and 0 not in out:
            out.append(0)
        if bool(allow_size_edge) and int(size) not in occupied and int(size) not in out:
            out.append(int(size))
        return out

    def _find_inventory_withdraw_destination(model_id: int, max_quantity: int, is_stackable: bool):
        if int(max_quantity) <= 0:
            return None
        bag_handles = _get_inventory_bag_handles()
        if not bag_handles:
            return None

        if bool(is_stackable):
            for bag_enum, _bag, _size, items in bag_handles:
                for it in items:
                    try:
                        if int(getattr(it, "model_id", 0) or 0) != int(model_id):
                            continue
                        cur_qty = int(getattr(it, "quantity", 0) or 0)
                        if cur_qty >= 250:
                            continue
                        room = max(0, 250 - cur_qty)
                        if room <= 0:
                            continue
                        move_qty = min(int(max_quantity), int(room))
                        if move_qty > 0:
                            return int(bag_enum.value), int(getattr(it, "slot", 0) or 0), int(move_qty)
                    except Exception:
                        continue

        for bag_enum, _bag, size, items in bag_handles:
            if int(len(items)) >= int(max(0, int(size))):
                continue
            occupied = set()
            for it in items:
                try:
                    occupied.add(int(getattr(it, "slot", -1) or -1))
                except Exception:
                    continue
            slot_candidates = _empty_slot_candidates(int(size), occupied)
            for slot in slot_candidates:
                if slot in occupied:
                    continue
                if bool(is_stackable):
                    move_qty = min(int(max_quantity), 250)
                else:
                    move_qty = 1
                if move_qty > 0:
                    return int(bag_enum.value), int(slot), int(move_qty)
        return None

    def _storage_deposit_destinations(model_id: int, max_quantity: int, is_stackable: bool):
        if int(max_quantity) <= 0:
            return []
        bag_handles = _get_storage_bag_handles()
        if not bag_handles:
            return []

        partials = []
        empties = []

        if bool(is_stackable):
            for bag_enum, _bag, _size, items in bag_handles:
                for it in items:
                    try:
                        if int(getattr(it, "model_id", 0) or 0) != int(model_id):
                            continue
                        cur_qty = int(getattr(it, "quantity", 0) or 0)
                        if cur_qty >= 250:
                            continue
                        room = max(0, 250 - cur_qty)
                        if room <= 0:
                            continue
                        move_qty = min(int(max_quantity), int(room))
                        if move_qty > 0:
                            partials.append(
                                (
                                    int(bag_enum.value),
                                    int(getattr(it, "slot", 0) or 0),
                                    int(move_qty),
                                    True,
                                    int(cur_qty),
                                )
                            )
                    except Exception:
                        continue

        for bag_enum, _bag, size, items in bag_handles:
            if int(len(items)) >= int(max(0, int(size))):
                continue
            occupied = set()
            for it in items:
                try:
                    occupied.add(int(getattr(it, "slot", -1) or -1))
                except Exception:
                    continue
            slot_candidates = _empty_slot_candidates(int(size), occupied)
            for slot in slot_candidates:
                if slot in occupied:
                    continue
                if bool(is_stackable):
                    move_qty = min(int(max_quantity), 250)
                else:
                    move_qty = 1
                if move_qty > 0:
                    empties.append((int(bag_enum.value), int(slot), int(move_qty), False))

        # Deposit preference: highest existing partial stack first, then safe empty
        # slots in generated priority order (do not re-sort empties by slot).
        partials.sort(key=lambda d: (-int(d[4]), int(d[0]), int(d[1])))
        merged = [(d[0], d[1], d[2], d[3]) for d in partials] + empties

        # When a previous deposit succeeded, prefer staying on that storage bag/tab.
        # This avoids repeatedly targeting stale/inaccessible destinations across bags.
        preferred_bag = int(_vault_last_confirmed_storage_bag_id or 0)
        if preferred_bag > 0:
            preferred = [d for d in merged if int(d[0]) == int(preferred_bag)]
            if preferred:
                others = [d for d in merged if int(d[0]) != int(preferred_bag)]
                merged = preferred + others
        return merged

    def _withdraw_model_amount(model_id: int, amount: int) -> tuple[bool, int]:
        amount = int(amount or 0)
        if amount <= 0:
            return False, 0
        model_id = int(model_id or 0)
        if model_id <= 0:
            return False, 0

        before_known, before_count = _stock_status_for_model_id(model_id)
        if not before_known:
            _refresh_inventory_cache(force=True)
            before_known, before_count = _stock_status_for_model_id(model_id)
        if not before_known:
            return False, 0

        remaining = int(amount)
        moved_total = 0
        attempts = 0

        while remaining > 0 and attempts < 64:
            attempts += 1
            # Withdrawal preference: consume lowest vault stack first.
            sources = _storage_stack_entries(model_id)
            if not sources:
                break
            sources.sort(key=lambda entry: (int(entry[1]), int(entry[2]), int(entry[3]), int(entry[0])))

            moved_this_pass = 0
            pending_move = False
            for source_item_id, source_qty, _src_bag_id, _src_slot in sources:
                source_item_id = int(source_item_id or 0)
                source_qty = int(source_qty or 0)
                if source_item_id <= 0 or source_qty <= 0:
                    continue

                try:
                    is_stackable = bool(Item.Customization.IsStackable(int(source_item_id)))
                except Exception:
                    is_stackable = True

                max_move = min(int(remaining), int(source_qty))
                if not is_stackable:
                    max_move = 1
                if max_move <= 0:
                    continue

                dest = _find_inventory_withdraw_destination(model_id, int(max_move), bool(is_stackable))
                if not dest:
                    continue

                bag_id, slot, move_qty = dest
                move_qty = int(max(1, min(int(move_qty), int(max_move))))

                moved_ok = False
                try:
                    _debug(
                        f"Vault restock: withdraw attempt "
                        f"(model_id={int(model_id)}, item_id={int(source_item_id)}, "
                        f"src={int(_src_bag_id)}:{int(_src_slot)}, dest={int(bag_id)}:{int(slot)}, "
                        f"requested={int(move_qty)}, inventory_count={int(before_count)}).",
                        Console.MessageType.Debug,
                    )
                    moved_ok = bool(PyInventory.PyInventory().MoveItem(int(source_item_id), int(bag_id), int(slot), int(move_qty)))
                except Exception:
                    moved_ok = False
                if not moved_ok:
                    continue

                moved_qty_actual, after_count = _confirm_withdraw_move(
                    int(model_id),
                    int(source_item_id),
                    int(source_qty),
                    int(before_count),
                    int(move_qty),
                )
                if moved_qty_actual <= 0:
                    # MoveItem may report success before movement is visible.
                    # Treat this as pending and retry on next tick instead of issuing
                    # a burst of additional move commands.
                    pending_move = True
                    break

                moved_this_pass = int(moved_qty_actual)
                moved_total += int(moved_this_pass)
                remaining -= int(moved_this_pass)
                before_count = int(after_count)
                break

            if pending_move:
                return False, -1
            if moved_this_pass <= 0:
                break

        return bool(moved_total > 0), int(moved_total)

    def _deposit_model_amount(inv, model_id: int, amount: int) -> tuple[bool, int]:
        global _vault_last_confirmed_storage_bag_id
        amount = int(amount or 0)
        if amount <= 0:
            return False, 0
        model_id = int(model_id or 0)
        if model_id <= 0:
            return False, 0

        before_known, before_count = _stock_status_for_model_id(model_id)
        if not before_known:
            _refresh_inventory_cache(force=True)
            before_known, before_count = _stock_status_for_model_id(model_id)
        if not before_known:
            return False, 0

        remaining = int(amount)
        moved_total = 0
        attempts = 0

        while remaining > 0 and attempts < 64:
            attempts += 1
            source_item_id = _find_item_id_by_model_id(model_id)
            if source_item_id <= 0:
                break

            try:
                source_qty = int(Item.Properties.GetQuantity(int(source_item_id)) or 0)
            except Exception:
                source_qty = 0
            if source_qty <= 0:
                source_qty = 1

            try:
                is_stackable = bool(Item.Customization.IsStackable(int(source_item_id)))
            except Exception:
                is_stackable = True

            max_move = min(int(remaining), int(source_qty))
            if not is_stackable:
                max_move = 1
            if max_move <= 0:
                break

            # Deposit exact excess amount only (withdraw-like behavior). Avoid helper
            # paths that may move full stacks when depositing into empty slots.
            destinations = _storage_deposit_destinations(model_id, int(max_move), bool(is_stackable))
            if not destinations:
                break

            now_ms = _now_ms()
            destinations = [
                d for d in destinations
                if not _is_deposit_dest_on_cooldown(int(model_id), int(d[0]), int(d[1]), int(now_ms))
            ]
            if not destinations:
                break

            moved_this_pass = 0
            blocked_dest_this_pass = False
            for bag_id, slot, move_qty, _into_existing_stack in destinations:
                move_qty = int(max(1, min(int(move_qty), int(max_move))))
                try:
                    # Re-validate destination occupancy immediately before MoveItem.
                    # This prevents swaps when a candidate no longer points at a truly
                    # empty slot (or expected same-model partial stack).
                    dst_item_id, dst_model_id = _storage_slot_item_info(int(bag_id), int(slot))
                    if bool(_into_existing_stack):
                        if int(dst_item_id) <= 0 or int(dst_model_id) != int(model_id):
                            if bool(getattr(cfg, "debug_logging", False)):
                                _debug(
                                    f"Vault restock: skipping deposit destination (model_id={int(model_id)}, "
                                    f"dest={int(bag_id)}:{int(slot)}, into_existing=True, "
                                    f"dst_item_id={int(dst_item_id)}, dst_model_id={int(dst_model_id)}).",
                                    Console.MessageType.Debug,
                                )
                            _mark_deposit_dest_cooldown(int(model_id), int(bag_id), int(slot), 3000)
                            continue
                    else:
                        if int(dst_item_id) > 0:
                            if bool(getattr(cfg, "debug_logging", False)):
                                _debug(
                                    f"Vault restock: skipping deposit destination (model_id={int(model_id)}, "
                                    f"dest={int(bag_id)}:{int(slot)}, into_existing=False, "
                                    f"dst_item_id={int(dst_item_id)}, dst_model_id={int(dst_model_id)}).",
                                    Console.MessageType.Debug,
                                )
                            _mark_deposit_dest_cooldown(int(model_id), int(bag_id), int(slot), 3000)
                            continue

                    # Prefer direct MoveItem result for storage actions; queued wrappers can
                    # report optimistic success without confirming an actual move.
                    moved_ok = False
                    try:
                        _debug(
                            f"Vault restock: deposit attempt "
                            f"(model_id={int(model_id)}, item_id={int(source_item_id)}, "
                            f"dest={int(bag_id)}:{int(slot)}, requested={int(move_qty)}, "
                            f"into_existing={bool(_into_existing_stack)}, inventory_count={int(before_count)}).",
                            Console.MessageType.Debug,
                        )
                        moved_ok = bool(PyInventory.PyInventory().MoveItem(int(source_item_id), int(bag_id), int(slot), int(move_qty)))
                    except Exception:
                        moved_ok = False

                    if moved_ok:
                        moved_qty_actual, after_count = _confirm_deposit_move(
                            int(model_id),
                            int(source_item_id),
                            int(source_qty),
                            int(before_count),
                            int(move_qty),
                        )
                        if moved_qty_actual <= 0:
                            # If a destination repeatedly reports MoveItem success but never
                            # changes inventory counts, treat that destination as blocked for
                            # a short window and retry restock on a different destination.
                            _mark_deposit_dest_cooldown(int(model_id), int(bag_id), int(slot))
                            _debug(
                                f"Vault restock: deposit unconfirmed; cooling destination "
                                f"(model_id={int(model_id)}, item_id={int(source_item_id)}, "
                                f"dest={int(bag_id)}:{int(slot)}, requested={int(move_qty)}, "
                                f"inventory_count={int(before_count)}).",
                                Console.MessageType.Debug,
                            )
                            blocked_dest_this_pass = True
                            break

                        moved_this_pass = int(min(int(max_move), int(moved_qty_actual)))
                        moved_total += int(moved_this_pass)
                        remaining -= int(moved_this_pass)
                        before_count = int(after_count)
                        _vault_last_confirmed_storage_bag_id = int(bag_id)
                        break
                except Exception:
                    continue

            if blocked_dest_this_pass:
                return False, -1
            if moved_this_pass <= 0:
                break

        return bool(moved_total > 0), int(moved_total)

    def _tick_vault_restock() -> bool:
        if cfg is None or not bool(getattr(cfg, "auto_vault_restock", False)):
            return False
        if not _restock_current_character_allowed():
            return False
        if not Routines.Checks.Map.MapValid():
            return False
        if _player_is_dead() or _map_is_loading():
            return False
        if bool(_in_explorable()):
            return False
        if not _inventory_ready():
            return False
        if not _refresh_inventory_cache(force=True):
            return False

        candidates = _build_vault_restock_candidates()
        if not candidates:
            return False

        inv = getattr(GLOBAL_CACHE, "Inventory", None)
        if inv is None:
            return False

        restock_timer = _timer_for("vault_restock_action")
        if not (restock_timer.IsStopped() or restock_timer.HasElapsed(int(VAULT_RESTOCK_ACTION_MS))):
            return False

        try:
            storage_open = bool(inv.IsStorageOpen())
        except Exception:
            storage_open = False

        if not storage_open:
            if not _has_actionable_vault_restock_need(inv, candidates):
                return False
            try:
                inv.OpenXunlaiWindow()
                _debug("Vault restock: opening Xunlai Vault.")
            except Exception as e:
                _debug(f"Vault restock: failed opening Xunlai Vault: {e}", Console.MessageType.Warning)
            restock_timer.Start()
            return True

        ordered_candidates = _ordered_vault_restock_candidates(candidates)
        move_cap_per_cycle = int(_restock_move_cap_per_cycle_value())

        for key, spec, model_id, _cur_count, _target_count, _delta in ordered_candidates:
            # Guard against runtime/UI changes while iterating candidates.
            if key in cfg.alcohol_selected:
                if not _restock_alcohol_enabled(key):
                    continue
            else:
                if not _restock_regular_enabled(key):
                    continue

            # Always re-evaluate current inventory state before attempting any action.
            if not _refresh_inventory_cache(force=True):
                continue
            live_known, live_count = _stock_status_for_model_id(int(model_id))
            if not live_known:
                continue
            live_target = int(_restock_target_for_key(key))
            live_delta = int(live_target) - int(live_count)
            if live_delta == 0:
                _clear_vault_pending("deposit", int(model_id))
                _clear_vault_pending("withdraw", int(model_id))
                continue

            label = str(spec.get("label", key) or key)
            if int(live_delta) > 0:
                if _is_vault_action_on_cooldown("withdraw", int(model_id)):
                    continue
                try:
                    in_storage = int(inv.GetModelCountInStorage(int(model_id)))
                except Exception:
                    in_storage = 0
                if in_storage <= 0:
                    wt = _warn_timer_for(f"vault_restock_nostock_{key}")
                    if wt.IsStopped() or wt.HasElapsed(15000):
                        wt.Start()
                        _record_blocked_action(f"vault_restock_nostock_{key}", f"{label}: no stock in vault")
                        _debug(f"Vault restock: no storage stock for {label}.")
                    continue

                to_withdraw = max(1, min(int(live_delta), int(in_storage), int(move_cap_per_cycle)))
                try:
                    ok, moved_qty = _withdraw_model_amount(int(model_id), int(to_withdraw))
                except Exception as e:
                    ok, moved_qty = False, 0
                    _debug(f"Vault restock: withdraw failed for {label}: {e}", Console.MessageType.Warning)

                restock_timer.Start()
                if int(moved_qty) < 0:
                    repeats = int(_record_vault_pending("withdraw", int(model_id), int(live_count)))
                    if repeats >= 4:
                        _mark_vault_action_cooldown("withdraw", int(model_id), 15000)
                        _clear_vault_pending("withdraw", int(model_id))
                        _debug(f"Vault restock: withdraw pending repeated for {label}; cooling withdraw attempts.", Console.MessageType.Warning)
                    _refresh_inventory_cache(force=True)
                    _schedule_refresh(250)
                    return True

                if ok and int(moved_qty) > 0:
                    _clear_vault_pending("withdraw", int(model_id))
                    _debug(f"Vault restock: withdrew {moved_qty}x {label} ({live_count}->{min(int(live_count) + int(moved_qty), int(live_target))}/{live_target}).")
                    _refresh_inventory_cache(force=True)
                    _schedule_refresh(250)
                    _schedule_refresh(700)
                    return True

                _clear_vault_pending("withdraw", int(model_id))
                _mark_vault_action_cooldown("withdraw", int(model_id), 5000)
                wt = _warn_timer_for(f"vault_restock_withdraw_failed_{key}")
                if wt.IsStopped() or wt.HasElapsed(10000):
                    wt.Start()
                    _debug(f"Vault restock: withdraw returned False for {label}.", Console.MessageType.Warning)
                _refresh_inventory_cache(force=True)
                _schedule_refresh(250)
                return True

            if _is_vault_action_on_cooldown("deposit", int(model_id)):
                continue

            excess = int(max(0, -int(live_delta)))
            excess = int(min(int(excess), int(move_cap_per_cycle)))
            if excess <= 0:
                continue

            source_item_id = _find_item_id_by_model_id(int(model_id))
            source_is_stackable = True
            if source_item_id > 0:
                try:
                    source_is_stackable = bool(Item.Customization.IsStackable(int(source_item_id)))
                except Exception:
                    source_is_stackable = True
            probe_destinations = _storage_deposit_destinations(int(model_id), 1, bool(source_is_stackable))
            if not probe_destinations:
                wt = _warn_timer_for(f"vault_restock_storage_full_{key}")
                if wt.IsStopped() or wt.HasElapsed(15000):
                    wt.Start()
                    _record_blocked_action(f"vault_restock_storage_full_{key}", f"{label}: storage full")
                    _debug(f"Vault restock: storage appears full for {label}; no deposit destination.", Console.MessageType.Warning)
                continue

            ok, moved_qty = _deposit_model_amount(inv, int(model_id), int(excess))
            restock_timer.Start()
            if int(moved_qty) < 0:
                repeats = int(_record_vault_pending("deposit", int(model_id), int(live_count)))
                if repeats >= 4:
                    _mark_vault_action_cooldown("deposit", int(model_id), 15000)
                    _clear_vault_pending("deposit", int(model_id))
                    _debug(f"Vault restock: deposit pending repeated for {label}; cooling deposit attempts.", Console.MessageType.Warning)
                _refresh_inventory_cache(force=True)
                _schedule_refresh(250)
                return True
            if ok and int(moved_qty) > 0:
                _clear_vault_pending("deposit", int(model_id))
                _debug(f"Vault restock: deposited {moved_qty}x {label} ({live_count}->{max(0, int(live_count) - int(moved_qty))}/{live_target}).")
                _refresh_inventory_cache(force=True)
                _schedule_refresh(250)
                _schedule_refresh(700)
                return True

            _clear_vault_pending("deposit", int(model_id))
            _mark_vault_action_cooldown("deposit", int(model_id), 5000)
            wt = _warn_timer_for(f"vault_restock_deposit_failed_{key}")
            if wt.IsStopped() or wt.HasElapsed(10000):
                wt.Start()
                _debug(f"Vault restock: deposit failed for {label}.", Console.MessageType.Warning)
            _refresh_inventory_cache(force=True)
            _schedule_refresh(250)
            return True

        restock_timer.Start()
        return False

    def _use_item_id(item_id: int, key: str) -> bool:
        try:
            GLOBAL_CACHE.Inventory.UseItem(int(item_id))
            # immediate + scheduled refreshes to catch delayed state updates
            try:
                _refresh_inventory_cache(force=True)
                _schedule_refresh(200)
                _schedule_refresh(600)
            except Exception:
                pass
            return True
        except Exception as e:
            _debug(f"UseItem failed (item_id={item_id}, key={key}): {e}", Console.MessageType.Warning)
            return False

    # -------------------------
    # Alcohol "real" drunk level (best-effort)
    # -------------------------
    def _alcohol_real_level():
        try:
            for nm in ("GetDrunkLevel", "DrunkLevel", "GetAlcoholLevel", "GetDrunkenness", "GetDrunkness"):
                fn = getattr(Player, nm, None)
                if callable(fn):
                    v = fn()
                    try:
                        v = cast(Any, v)
                        v = int(v)
                    except Exception:
                        continue
                    return int(max(0, min(5, v)))
        except Exception:
            pass
        return None

    # -------------------------
    # Alcohol estimate fallback (time-based)
    # -------------------------
    def _alcohol_current_level_estimate(now_ms: int) -> int:
        global _alcohol_last_drink_ms, _alcohol_level_base
        if _alcohol_last_drink_ms <= 0:
            return 0
        elapsed = int(now_ms - _alcohol_last_drink_ms)
        if elapsed <= 60000:
            return int(max(0, min(5, _alcohol_level_base)))
        decays = int((elapsed - 60000) // 60000) + 1
        return int(max(0, min(5, _alcohol_level_base - decays)))

    def _alcohol_current_level(now_ms: int) -> int:
        real = _alcohol_real_level()
        if real is not None:
            return int(real)
        return int(_alcohol_current_level_estimate(now_ms))

    def _alcohol_apply_drink(drunk_add: int, now_ms: int):
        global _alcohol_last_drink_ms, _alcohol_level_base
        cur = _alcohol_current_level(now_ms)
        _alcohol_level_base = int(min(5, cur + int(drunk_add)))
        _alcohol_last_drink_ms = int(now_ms)

    def _tick_disable_alcohol_effect() -> bool:
        if cfg is None or not bool(getattr(cfg, "alcohol_disable_effect", False)):
            return False

        t = _timer_for("alcohol_disable_effect")
        if not (t.IsStopped() or t.HasElapsed(int(ALCOHOL_EFFECT_TICK_MS))):
            return False
        t.Start()

        try:
            if not bool(Routines.Checks.Map.IsMapReady()):
                return False
        except Exception:
            if not Routines.Checks.Map.MapValid():
                return False

        try:
            current_alcohol_level = int(Effects.GetAlcoholLevel() or 0)
        except Exception as e:
            wt = _warn_timer_for("alcohol_disable_effect_read")
            if wt.IsStopped() or wt.HasElapsed(15000):
                wt.Start()
                _debug(f"Alcohol blur disable read failed: {e}", Console.MessageType.Warning)
            return False

        if current_alcohol_level <= 0:
            return False

        try:
            Effects.ApplyDrunkEffect(0, 0)
            return True
        except Exception as e:
            wt = _warn_timer_for("alcohol_disable_effect_apply")
            if wt.IsStopped() or wt.HasElapsed(15000):
                wt.Start()
                _debug(f"Alcohol blur disable apply failed: {e}", Console.MessageType.Warning)
            return False

    # -------------------------
    # Team broadcast helper
    # -------------------------
    def _get_team_broadcast_recipients():
        sender = str(Player.GetAccountEmail() or "")
        if not sender:
            return [], "missing_sender_email"
        try:
            me = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender)
            if not me:
                return [], "missing_sender_shared_data"
            map_data = getattr(getattr(me, "AgentData", None), "Map", None)
            if not map_data:
                return [], "missing_sender_map_data"
            party_id = _acc_party_id(me)
            map_id = int(getattr(map_data, "MapID", 0) or 0)
            map_region = int(getattr(map_data, "Region", 0) or 0)
            map_district = int(getattr(map_data, "District", 0) or 0)
            map_language = int(getattr(map_data, "Language", 0) or 0)
            if party_id <= 0 or map_id <= 0:
                return [], f"invalid_sender_scope(party={party_id},map={map_id})"

            party_accounts = GLOBAL_CACHE.ShMem.GetPlayersFromParty(
                party_id,
                map_id,
                map_region,
                map_district,
                map_language,
            ) or []
            recipients = []
            skipped_not_opt_in = 0
            for acc in party_accounts:
                email = _acc_email(acc)
                if not email or email == sender:
                    continue
                _, opt_in = _load_team_flags_for_email(email)
                if not bool(opt_in):
                    skipped_not_opt_in += 1
                    continue
                recipients.append(str(email))
            recipients = list(dict.fromkeys(recipients))
            reason = (
                f"party={party_id} map={map_id}/{map_region}/{map_district}/{map_language} "
                f"party_accounts={len(party_accounts)} opted_in={len(recipients)} skipped_opt_in={skipped_not_opt_in}"
            )
            return recipients, reason
        except Exception as e:
            return [], f"recipient_query_error={e}"

    def _broadcast_use(model_id: int, repeat: int = 1, effect_id: int = 0, recipients=None):
        try:
            if not bool(cfg.team_broadcast):
                return
            sender = str(Player.GetAccountEmail() or "")
            if not sender:
                return

            if recipients is None:
                selected_recipients, reason = _get_team_broadcast_recipients()
            else:
                selected_recipients = [str(x) for x in recipients if str(x or "")]
                selected_recipients = [x for x in list(dict.fromkeys(selected_recipients)) if x != sender]
                reason = "explicit_recipients"

            if not selected_recipients:
                _debug(
                    f"UseItem broadcast skip model={int(model_id)} repeat={int(repeat)} effect={int(effect_id)}; no recipients ({reason})."
                )
                return

            _debug(
                f"UseItem broadcast model={int(model_id)} repeat={int(repeat)} effect={int(effect_id)} "
                f"recipients={len(selected_recipients)} reason={reason} -> {', '.join(selected_recipients)}"
            )
            for to_email in selected_recipients:
                try:
                    GLOBAL_CACHE.ShMem.SendMessage(
                        sender,
                        to_email,
                        SharedCommandType.UseItem,
                        (float(model_id), float(repeat), float(effect_id), 0.0),
                    )
                except Exception as e:
                    _debug(f"UseItem broadcast send failed to {to_email}: {e}", Console.MessageType.Warning)
        except Exception as e:
            _debug(f"UseItem broadcast failed: {e}", Console.MessageType.Warning)

    def _broadcast_enabled_request_without_local_item(
        key: str,
        spec: dict,
        model_id: int,
        effect_id: int,
        timer: Timer,
    ) -> bool:
        if not bool(cfg.team_broadcast):
            return False
        if _is_summoning_spec(spec) or bool(spec.get("suppress_team_broadcast", False)):
            return False
        if int(model_id or 0) <= 0:
            return False

        recipients, reason = _get_team_broadcast_recipients()
        if not recipients:
            return False

        label = str(spec.get("label", key) or key)
        _debug(
            f"Broadcasting {label} request without local inventory; "
            f"recipients={len(recipients)} reason={reason}."
        )
        _broadcast_use(int(model_id), 1, int(effect_id or 0), recipients=recipients)
        timer.Start()
        _last_broadcast_ms[str(key)] = _now_ms()
        return True

    def _broadcast_keepalive(key: str, model_id: int, effect_id: int):
        if effect_id <= 0:
            return
        if not bool(cfg.team_broadcast):
            return
        now = _now_ms()
        last = int(_last_broadcast_ms.get(key, 0) or 0)
        if last > 0 and (now - last) < int(BROADCAST_KEEPALIVE_MS):
            return
        _last_broadcast_ms[key] = now
        _broadcast_use(model_id, 1, effect_id)

    def _pick_alcohol(cur_level: int, target_level: int, pool_keys: list):
        if not pool_keys:
            return None
        candidates = []
        for k in pool_keys:
            spec = ALCOHOL_BY_KEY.get(k)
            if not spec:
                continue
            add = int(spec.get("drunk_add", 1) or 1)
            candidates.append((add, spec.get("label", ""), spec))

        if not candidates:
            return None

        mode = int(cfg.alcohol_preference)

        if mode == 0:
            reaching = [c for c in candidates if min(5, cur_level + c[0]) >= target_level]
            if reaching:
                reaching.sort(key=lambda x: (x[0], x[1]))
                return reaching[0][2]
            candidates.sort(key=lambda x: (-x[0], x[1]))
            return candidates[0][2]

        if mode == 1:
            candidates.sort(key=lambda x: (-x[0], x[1]))
            return candidates[0][2]

        delta = max(0, target_level - cur_level)
        non_over = [c for c in candidates if c[0] <= delta and c[0] > 0]
        if non_over:
            non_over.sort(key=lambda x: (x[0], x[1]))
            return non_over[0][2]
        candidates.sort(key=lambda x: (x[0], x[1]))
        return candidates[0][2]

    def _cooldown_for_key(key: str, spec: dict | None = None) -> int:
        v = int(cfg.min_interval_ms.get(key, 0) or 0)
        if v <= 0 and spec is not None:
            v = int(spec.get("default_cooldown_ms", 0) or 0)
        if v <= 0:
            return int(DEFAULT_INTERNAL_COOLDOWN_MS)
        return int(max(250, v))

    def _compact_character_name(name: str) -> str:
        return " ".join((name or "").strip().split())

    def _normalize_name(name: str) -> str:
        return _compact_character_name(name).lower()

    def _acc_email(acc) -> str:
        return str(getattr(acc, "AccountEmail", "") or "")

    def _acc_name(acc) -> str:
        try:
            return str(getattr(getattr(acc, "AgentData", None), "CharacterName", "") or "")
        except Exception:
            return ""

    def _restock_scope_mode_value(raw_value = None) -> int:
        try:
            if raw_value is None:
                raw_val = int(getattr(cfg, "restock_scope_mode", DEFAULT_RESTOCK_SCOPE_MODE))
            else:
                raw_val = int(raw_value)
        except Exception:
            raw_val = int(DEFAULT_RESTOCK_SCOPE_MODE)
        return max(RESTOCK_SCOPE_ACCOUNT_WIDE, min(RESTOCK_SCOPE_BLOCK_LIST, int(raw_val)))

    def _restock_parse_character_list(raw_value: str) -> list[str]:
        out = []
        seen = set()
        for raw_name in re.split(r"[,;\n|]+", str(raw_value or "")):
            name = _compact_character_name(raw_name)
            if not name:
                continue
            normalized = _normalize_name(name)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            out.append(name)
        return out

    def _restock_serialize_character_list(names: list[str]) -> str:
        cleaned = []
        seen = set()
        for raw_name in list(names or []):
            name = _compact_character_name(raw_name)
            if not name:
                continue
            normalized = _normalize_name(name)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            cleaned.append(name)
        return ", ".join(cleaned)

    def _restock_character_membership_set(raw_value: str) -> set[str]:
        return {_normalize_name(name) for name in _restock_parse_character_list(raw_value)}

    def _current_character_name() -> str:
        try:
            current = _compact_character_name(str(Player.GetName() or ""))
        except Exception:
            current = ""
        if current:
            return current
        try:
            account_email = str(Player.GetAccountEmail() or "").strip()
        except Exception:
            account_email = ""
        if not account_email:
            return ""
        try:
            acc = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        except Exception:
            acc = None
        return _compact_character_name(_acc_name(acc)) if acc else ""

    def _restock_current_character_participation() -> tuple[bool, str, str]:
        current_name = _current_character_name()
        display_name = current_name or "Unavailable"
        normalized_name = _normalize_name(current_name)
        mode = _restock_scope_mode_value()

        if mode == RESTOCK_SCOPE_ACCOUNT_WIDE:
            return True, display_name, "Allowed: account-wide mode."

        if not normalized_name:
            return False, display_name, "Blocked: current character name is unavailable in list mode."

        if mode == RESTOCK_SCOPE_ALLOW_LIST:
            allowed_names = _restock_character_membership_set(str(getattr(cfg, "restock_allowed_characters", "") or ""))
            if normalized_name in allowed_names:
                return True, display_name, "Allowed: current character is in the allow list."
            return False, display_name, "Blocked: current character is not in the allow list."

        blocked_names = _restock_character_membership_set(str(getattr(cfg, "restock_blocked_characters", "") or ""))
        if normalized_name in blocked_names:
            return False, display_name, "Blocked: current character is in the block list."
        return True, display_name, "Allowed: current character is not in the block list."

    def _restock_current_character_allowed() -> bool:
        allowed, _display_name, _summary = _restock_current_character_participation()
        return bool(allowed)

    def _restock_add_character_to_raw_list(raw_value: str, character_name: str) -> str:
        names = _restock_parse_character_list(raw_value)
        names.append(character_name)
        return _restock_serialize_character_list(names)

    def _acc_party_id(acc) -> int:
        try:
            return int(getattr(getattr(acc, "AgentPartyData", None), "PartyID", 0) or 0)
        except Exception:
            return 0

    def _acc_party_position(acc) -> int:
        try:
            return int(getattr(getattr(acc, "AgentPartyData", None), "PartyPosition", 9999) or 9999)
        except Exception:
            return 9999

    def _acc_player_morale(acc) -> int:
        try:
            agent_data = getattr(acc, "AgentData", None)
            if agent_data is not None and hasattr(agent_data, "Morale"):
                return int(getattr(agent_data, "Morale", 0) or 0)
            return int(getattr(acc, "PlayerMorale", 0) or 0)
        except Exception:
            return 0

    def _normalize_sync_account_email(raw_value: str) -> str:
        return str(raw_value or "").strip().lower()

    def _pycons_sync_account_display_name(acc) -> str:
        name = str(_acc_name(acc) or "").strip()
        if name:
            return name
        email = str(_acc_email(acc) or "").strip()
        return email or "Unknown Account"

    def _pycons_sync_account_map_tuple(acc) -> tuple[int, int, int, int]:
        agent_map = getattr(getattr(acc, "AgentData", None), "Map", None)
        map_id = int(getattr(agent_map, "MapID", getattr(acc, "MapID", 0)) or 0)
        region = int(getattr(agent_map, "Region", getattr(acc, "MapRegion", 0)) or 0)
        district = int(getattr(agent_map, "District", getattr(acc, "MapDistrict", 0)) or 0)
        language = int(getattr(agent_map, "Language", getattr(acc, "MapLanguage", 0)) or 0)
        return map_id, region, district, language

    def _pycons_sync_is_same_map(acc) -> bool:
        try:
            own_region = Map.GetRegion() or (0, 0)
            own_language = Map.GetLanguage() or (0, 0)
            own_tuple = (
                int(Map.GetMapID() or 0),
                int(own_region[0] or 0),
                int(Map.GetDistrict() or 0),
                int(own_language[0] or 0),
            )
        except Exception:
            own_tuple = (0, 0, 0, 0)
        return own_tuple == _pycons_sync_account_map_tuple(acc)

    def _pycons_sync_is_same_party(acc) -> bool:
        try:
            own_party_id = int(GLOBAL_CACHE.Party.GetPartyID() or 0)
        except Exception:
            own_party_id = 0
        return bool(own_party_id > 0 and own_party_id == _acc_party_id(acc))

    def _pycons_sync_current_account_is_party_leader() -> bool:
        try:
            account_email = str(Player.GetAccountEmail() or "").strip()
        except Exception:
            account_email = ""
        if account_email:
            try:
                own_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
            except Exception:
                own_account = None
            if own_account is not None:
                try:
                    party_data = getattr(own_account, "AgentPartyData", None)
                    if party_data is not None and hasattr(party_data, "IsPartyLeader"):
                        return bool(getattr(party_data, "IsPartyLeader", False))
                except Exception:
                    pass

        try:
            own_party_id = int(GLOBAL_CACHE.Party.GetPartyID() or 0)
            own_agent_id = int(Player.GetAgentID() or 0)
            leader_agent_id = int(GLOBAL_CACHE.Party.GetPartyLeaderID() or 0)
        except Exception:
            return False
        return bool(own_party_id > 0 and own_agent_id > 0 and own_agent_id == leader_agent_id)

    def _pycons_sync_is_follower(acc) -> bool:
        if not _pycons_sync_is_same_party(acc):
            return False
        try:
            party_data = getattr(acc, "AgentPartyData", None)
            if party_data is not None and hasattr(party_data, "IsPartyLeader"):
                return not bool(getattr(party_data, "IsPartyLeader", False))
        except Exception:
            pass
        return bool(_acc_party_id(acc) > 0 and _acc_party_position(acc) > 0)

    def _get_pycons_sync_accounts() -> list[object]:
        own_email = str(Player.GetAccountEmail() or "").strip()
        own_email_norm = _normalize_sync_account_email(own_email)
        accounts = []
        for acc in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
            if not acc:
                continue
            raw_email = str(_acc_email(acc) or "").strip()
            if not raw_email:
                continue
            if _normalize_sync_account_email(raw_email) == own_email_norm:
                continue
            if not bool(getattr(acc, "IsSlotActive", False)):
                continue
            if not bool(getattr(acc, "IsAccount", False)):
                continue
            if bool(getattr(acc, "IsHero", False)):
                continue
            accounts.append(acc)
        accounts.sort(key=lambda acc: (_acc_party_position(acc), _pycons_sync_account_display_name(acc).lower(), _normalize_sync_account_email(_acc_email(acc))))
        return accounts

    def _get_selected_pycons_sync_categories() -> list[str]:
        return [str(key) for key, _label in PYCONS_SYNC_CATEGORY_DEFS if bool(_rt.sync_selected_categories.get(str(key), False))]

    def _get_selected_pycons_sync_account_emails() -> list[str]:
        active_email_map: dict[str, str] = {}
        for acc in _get_pycons_sync_accounts():
            raw_email = str(_acc_email(acc) or "").strip()
            normalized_email = _normalize_sync_account_email(raw_email)
            if raw_email and normalized_email and normalized_email not in active_email_map:
                active_email_map[normalized_email] = raw_email
        return [
            raw_email
            for normalized_email, raw_email in active_email_map.items()
            if bool(_rt.sync_selected_accounts.get(normalized_email, False))
        ]

    def _pycons_sync_display_name_from_email(account_email: str) -> str:
        normalized_email = _normalize_sync_account_email(account_email)
        for acc in _get_pycons_sync_accounts():
            if _normalize_sync_account_email(_acc_email(acc)) == normalized_email:
                return _pycons_sync_account_display_name(acc)
        raw_email = str(account_email or "").strip()
        return raw_email or normalized_email or "Unknown Account"

    def _pycons_sync_refresh_summary():
        statuses = list((_rt.sync_statuses or {}).values())
        if not statuses:
            _rt.sync_summary_text = "No other-accounts action run yet."
            return

        written_count = sum(1 for status in statuses if str(status.get("state", "")) != "write_failed")
        requested_count = sum(1 for status in statuses if str(status.get("state", "")) == "reload_requested")
        reloaded_count = sum(1 for status in statuses if str(status.get("state", "")) == "reloaded")
        unavailable_count = sum(1 for status in statuses if str(status.get("state", "")) == "reload_unavailable")
        issue_count = sum(
            1
            for status in statuses
            if str(status.get("state", "")) in ("write_failed", "reload_failed", "reload_not_queued", "reload_unavailable")
        )
        _rt.sync_summary_text = (
            f"Last other-accounts action: {written_count} written | {requested_count} reload requested | "
            f"{reloaded_count} reloaded | {unavailable_count} reload unavailable | {issue_count} issue(s)."
        )

    def _pycons_sync_set_status(
        account_email: str,
        *,
        state: str,
        status_label: str,
        summary: str,
        detail: str = "",
        success: bool = False,
    ):
        normalized_email = _normalize_sync_account_email(account_email)
        if not normalized_email:
            return
        _rt.sync_statuses[normalized_email] = {
            "email": str(account_email or "").strip(),
            "display_name": _pycons_sync_display_name_from_email(account_email),
            "state": str(state or "").strip(),
            "status_label": str(status_label or "").strip(),
            "summary": str(summary or "").strip(),
            "detail": str(detail or "").strip(),
            "success": bool(success),
        }
        _pycons_sync_refresh_summary()

    def _pycons_sync_next_request_id() -> str:
        _rt.sync_request_counter = int(getattr(_rt, "sync_request_counter", 0) or 0) + 1
        return f"pycons_sync_{int(_now_ms())}_{int(_rt.sync_request_counter)}"

    def _pycons_sync_write_categories_to_account(account_email: str, categories: list[str]) -> str:
        target_path = _resolve_account_ini_path(account_email, migrate_legacy=True, log_migration=False)
        ini_handler = IniHandler(target_path)
        config = ini_handler.reload()
        if not config.has_section(INI_SECTION):
            config.add_section(INI_SECTION)

        def set_key(key: str, value):
            config.set(INI_SECTION, str(key), str(value))

        category_set = {str(category) for category in categories}

        if PYCONS_SYNC_CATEGORY_ALCOHOL in category_set:
            for key in PYCONS_SYNC_ALCOHOL_SCALAR_KEYS:
                set_key(key, getattr(cfg, key))

        if PYCONS_SYNC_CATEGORY_MOVEMENT_SAFETY in category_set:
            for key in PYCONS_SYNC_MOVEMENT_SAFETY_SCALAR_KEYS:
                set_key(key, getattr(cfg, key))

        if PYCONS_SYNC_CATEGORY_MBDP in category_set:
            for key in PYCONS_SYNC_MBDP_SCALAR_KEYS:
                set_key(key, getattr(cfg, key))

        if PYCONS_SYNC_CATEGORY_RESTOCK in category_set:
            for key in PYCONS_SYNC_RESTOCK_SCALAR_KEYS:
                set_key(key, getattr(cfg, key))
            for spec in ALL_CONSUMABLES:
                item_key = str(spec.get("key", "") or "")
                if not item_key:
                    continue
                set_key(f"restock_enabled_{item_key}", bool(cfg.restock_enabled_items.get(item_key, False)))
                set_key(f"restock_target_{item_key}", int(max(0, min(2500, int(cfg.restock_targets.get(item_key, VAULT_RESTOCK_TARGET_QTY) or 0)))))
            for spec in ALCOHOL_ITEMS:
                item_key = str(spec.get("key", "") or "")
                if not item_key:
                    continue
                set_key(f"restock_enabled_{item_key}", bool(cfg.restock_enabled_items.get(item_key, False)))
                set_key(f"restock_target_{item_key}", int(max(0, min(2500, int(cfg.restock_targets.get(item_key, VAULT_RESTOCK_TARGET_QTY) or 0)))))

        if PYCONS_SYNC_CATEGORY_SELECTION in category_set:
            include_enabled_state = bool(getattr(cfg, "sync_selection_include_enabled_state", False))
            set_key(PYCONS_SYNC_SELECTION_ENABLED_STATE_ONCE_KEY, bool(include_enabled_state))
            for spec in ALL_CONSUMABLES:
                item_key = str(spec.get("key", "") or "")
                if not item_key:
                    continue
                selected_value = bool(cfg.selected.get(item_key, False))
                set_key(f"selected_{item_key}", selected_value)
                if bool(include_enabled_state):
                    set_key(f"enabled_{item_key}", bool(_runtime_regular_enabled(item_key)) if selected_value else False)
                elif not selected_value:
                    set_key(f"enabled_{item_key}", False)
            for spec in ALCOHOL_ITEMS:
                item_key = str(spec.get("key", "") or "")
                if not item_key:
                    continue
                selected_value = bool(cfg.alcohol_selected.get(item_key, False))
                set_key(f"alcohol_selected_{item_key}", selected_value)
                if bool(include_enabled_state):
                    set_key(f"alcohol_enabled_{item_key}", bool(_runtime_alcohol_enabled(item_key)) if selected_value else False)
                elif not selected_value:
                    set_key(f"alcohol_enabled_{item_key}", False)

        ini_handler.save(config)
        return target_path

    def _pycons_write_profile_to_account(account_email: str, profile_payload: dict[str, Any], profile_name: str) -> str:
        target_path = _resolve_account_ini_path(account_email, migrate_legacy=True, log_migration=False)
        ini_handler = IniHandler(target_path)
        config = ini_handler.reload()
        _apply_profile_payload_to_live_config(config, profile_payload, profile_name=profile_name)
        ini_handler.save(config)
        return target_path

    def _pycons_sync_send_reload_request(account_email: str, request_id: str) -> bool:
        sender_email = str(Player.GetAccountEmail() or "").strip()
        receiver_email = str(account_email or "").strip()
        if not sender_email or not receiver_email:
            return False
        message_index = GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            receiver_email,
            SharedCommandType.Pycons,
            (float(PYCONS_SYNC_OPCODE_RELOAD_CONFIG), 0.0, 0.0, 0.0),
            (str(request_id or ""), "Sync", "", ""),
        )
        return bool(message_index != -1)

    def _pycons_message_extra_data(message) -> tuple[str, str, str, str]:
        values: list[str] = []
        for raw in getattr(message, "ExtraData", ()) or ():
            try:
                values.append("".join(ch for ch in raw if ch != "\0").rstrip())
            except Exception:
                values.append("")
        while len(values) < 4:
            values.append("")
        return values[0], values[1], values[2], values[3]

    def _pycons_message_opcode(message) -> int:
        try:
            return int(getattr(message, "Params", [0])[0])
        except Exception:
            return 0

    def _pycons_message_success_flag(message) -> bool:
        try:
            return bool(int(getattr(message, "Params", [0, 0, 0, 0])[3]))
        except Exception:
            return False

    def pycons_send_sync_result_message(
        sender_email: str,
        receiver_email: str,
        *,
        request_id: str,
        status_label: str,
        summary: str,
        detail: str = "",
        success_flag: bool = False,
    ) -> bool:
        sender = str(sender_email or "").strip()
        receiver = str(receiver_email or "").strip()
        if not sender or not receiver:
            return False
        message_index = GLOBAL_CACHE.ShMem.SendMessage(
            sender,
            receiver,
            SharedCommandType.Pycons,
            (float(PYCONS_SYNC_OPCODE_RELOAD_RESULT), 0.0, 0.0, 1.0 if bool(success_flag) else 0.0),
            (str(request_id or ""), str(status_label or ""), str(summary or ""), str(detail or "")),
        )
        return bool(message_index != -1)

    def pycons_reply_reload_unavailable_for_message(message) -> bool:
        if _pycons_message_opcode(message) != PYCONS_SYNC_OPCODE_RELOAD_CONFIG:
            return False
        request_id, _status_label, _summary, _detail = _pycons_message_extra_data(message)
        sender_email = str(getattr(message, "SenderEmail", "") or "").strip()
        receiver_email = str(getattr(message, "ReceiverEmail", "") or Player.GetAccountEmail() or "").strip()
        return pycons_send_sync_result_message(
            receiver_email,
            sender_email,
            request_id=request_id,
            status_label="Reload Unavailable",
            summary="Config was written, but Pycons is not currently loaded on the target account.",
            detail="Enable Pycons on the target account to apply this change immediately.",
            success_flag=False,
        )

    def pycons_handle_shared_message(message) -> bool:
        request_id, status_label, summary, detail = _pycons_message_extra_data(message)
        sender_email = str(getattr(message, "SenderEmail", "") or "").strip()
        receiver_email = str(getattr(message, "ReceiverEmail", "") or Player.GetAccountEmail() or "").strip()
        try:
            opcode = _pycons_message_opcode(message)
            success_flag = _pycons_message_success_flag(message)

            if opcode == PYCONS_SYNC_OPCODE_RELOAD_RESULT:
                return bool(
                    pycons_handle_sync_result(
                        sender_email=sender_email,
                        request_id=request_id,
                        status_label=status_label,
                        summary=summary,
                        detail=detail,
                        success_flag=success_flag,
                    )
                )

            if opcode != PYCONS_SYNC_OPCODE_RELOAD_CONFIG:
                ConsoleLog(
                    BOT_NAME,
                    f"Pycons message ignored unknown opcode={opcode}.",
                    Console.MessageType.Warning,
                )
                return False

            reload_result = pycons_reload_config_from_disk(reason="other accounts action")
            if isinstance(reload_result, tuple):
                reload_ok = bool(reload_result[0])
                reload_detail = str(reload_result[1] or "")
            else:
                reload_ok = bool(reload_result)
                reload_detail = ""

            if reload_ok:
                pycons_send_sync_result_message(
                    receiver_email,
                    sender_email,
                    request_id=request_id,
                    status_label="Reloaded",
                    summary="Config was written and Pycons reloaded from disk on the target account.",
                    detail=reload_detail,
                    success_flag=True,
                )
                return True

            pycons_send_sync_result_message(
                receiver_email,
                sender_email,
                request_id=request_id,
                status_label="Reload Failed",
                summary="Config was written, but Pycons could not reload its config on the target account.",
                detail=reload_detail,
                success_flag=False,
            )
            return False
        except Exception as exc:
            ConsoleLog(BOT_NAME, f"Pycons shared-message error: {exc}", Console.MessageType.Error)
            pycons_send_sync_result_message(
                receiver_email,
                sender_email,
                request_id=request_id,
                status_label="Reload Failed",
                summary="Config was written, but Pycons hit an error during reload on the target account.",
                detail=str(exc),
                success_flag=False,
            )
            return False

    def _pycons_start_settings_sync():
        selected_categories = _get_selected_pycons_sync_categories()
        selected_accounts = _get_selected_pycons_sync_account_emails()
        if not selected_categories:
            _rt.sync_summary_text = "Select at least one settings category to copy."
            return
        if not selected_accounts:
            _rt.sync_summary_text = "Select at least one active target account."
            return

        _rt.sync_statuses = {}
        _rt.sync_active_request_id = _pycons_sync_next_request_id()
        request_id = str(_rt.sync_active_request_id or "")

        for account_email in selected_accounts:
            try:
                _pycons_sync_write_categories_to_account(account_email, selected_categories)
            except Exception as exc:
                _pycons_sync_set_status(
                    account_email,
                    state="write_failed",
                    status_label="Write Failed",
                    summary="Selected settings categories could not be written to the target account's live Pycons config.",
                    detail=str(exc),
                    success=False,
                )
                continue

            if _pycons_sync_send_reload_request(account_email, request_id):
                _pycons_sync_set_status(
                    account_email,
                    state="reload_requested",
                    status_label="Reload Requested",
                    summary="Selected settings categories written; waiting for Pycons reload result.",
                    success=False,
                )
            else:
                _pycons_sync_set_status(
                    account_email,
                    state="reload_not_queued",
                    status_label="Reload Not Queued",
                    summary="Selected settings categories written, but the reload request could not be queued.",
                    detail="The target account may apply the copied settings the next time Pycons loads.",
                    success=False,
                )

    def _pycons_start_profile_apply_to_accounts(profile_id: str):
        selected_profile_id = str(profile_id or "").strip()
        if not selected_profile_id:
            _rt.sync_summary_text = "Select a saved profile first."
            return

        selected_accounts = _get_selected_pycons_sync_account_emails()
        if not selected_accounts:
            _rt.sync_summary_text = "Select at least one active target account."
            return

        profile_entry = _read_profile_record(selected_profile_id, include_payload=True)
        if profile_entry is None:
            _rt.sync_summary_text = "The selected saved profile is no longer available."
            return

        display_name = _profile_display_name(profile_entry.get("name", ""), selected_profile_id)
        payload = dict(profile_entry.get("payload") or _profile_default_payload())

        _rt.sync_statuses = {}
        _rt.sync_active_request_id = _pycons_sync_next_request_id()
        request_id = str(_rt.sync_active_request_id or "")

        for account_email in selected_accounts:
            try:
                _pycons_write_profile_to_account(account_email, payload, display_name)
            except Exception as exc:
                _pycons_sync_set_status(
                    account_email,
                    state="write_failed",
                    status_label="Write Failed",
                    summary=f"Profile '{display_name}' could not be written to the target account's live Pycons config.",
                    detail=str(exc),
                    success=False,
                )
                continue

            if _pycons_sync_send_reload_request(account_email, request_id):
                _pycons_sync_set_status(
                    account_email,
                    state="reload_requested",
                    status_label="Reload Requested",
                    summary=f"Profile '{display_name}' written; waiting for Pycons reload result.",
                    success=False,
                )
            else:
                _pycons_sync_set_status(
                    account_email,
                    state="reload_not_queued",
                    status_label="Reload Not Queued",
                    summary=f"Profile '{display_name}' written, but the reload request could not be queued.",
                    detail="The target account may apply the profile the next time Pycons loads.",
                    success=False,
                )

    def pycons_handle_sync_result(
        *,
        sender_email: str,
        request_id: str,
        status_label: str,
        summary: str,
        detail: str = "",
        success_flag: bool = False,
    ) -> bool:
        current_request_id = str(getattr(_rt, "sync_active_request_id", "") or "")
        incoming_request_id = str(request_id or "").strip()
        if incoming_request_id and current_request_id and incoming_request_id != current_request_id:
            return False

        status_label_clean = str(status_label or "").strip()
        if status_label_clean == "Reloaded" and bool(success_flag):
            state = "reloaded"
        elif status_label_clean == "Reload Unavailable":
            state = "reload_unavailable"
        elif status_label_clean == "Reload Failed":
            state = "reload_failed"
        else:
            state = "reloaded" if bool(success_flag) else "reload_failed"

        _pycons_sync_set_status(
            sender_email,
            state=state,
            status_label=status_label_clean or ("Reloaded" if bool(success_flag) else "Reload Failed"),
            summary=str(summary or "").strip() or "Pycons reload result received.",
            detail=str(detail or "").strip(),
            success=bool(success_flag),
        )
        return True

    def _load_team_flags_for_email(account_email: str) -> tuple[bool, bool]:
        if not account_email:
            return False, False
        now = _now_ms()
        cached = _team_flags_cache.get(account_email)
        if cached and (now - int(cached[0])) < int(TEAM_SETTINGS_CACHE_MS):
            return bool(cached[1]), bool(cached[2])
        try:
            ini = IniHandler(_resolve_account_ini_path(account_email, migrate_legacy=True, log_migration=False))
            is_broadcaster = bool(ini.read_bool(INI_SECTION, "team_broadcast", False))
            is_optin = bool(ini.read_bool(INI_SECTION, "team_consume_opt_in", False))
        except Exception:
            is_broadcaster = False
            is_optin = False
        _team_flags_cache[account_email] = (now, is_broadcaster, is_optin)
        return is_broadcaster, is_optin

    def _morale_state(raw_value: int) -> dict:
        raw = int(raw_value or 0)
        if raw <= 0:
            return {"raw": raw, "effective": 0, "morale_boost": 0, "dp": 0, "format": "unknown"}
        if raw <= 10:
            boost = max(0, min(10, raw))
            return {"raw": raw, "effective": boost, "morale_boost": boost, "dp": 0, "format": "morale_only"}
        if raw < 40:
            dp = max(0, min(60, raw))
            return {"raw": raw, "effective": -dp, "morale_boost": 0, "dp": dp, "format": "dp_only"}
        eff = max(-60, min(10, raw - 100))
        return {"raw": raw, "effective": eff, "morale_boost": max(0, eff), "dp": max(0, -eff), "format": "effective"}

    def _morale_states_for_targeting(states: list[dict]) -> list[dict]:
        return [s for s in states if str(s.get("format", "")) != "unknown"]

    def _get_party_player_rows():
        rows = []
        try:
            players = Party.GetPlayers() or []
        except Exception:
            players = []
        for p in players:
            try:
                login_number = int(getattr(p, "login_number", 0) or 0)
                if login_number <= 0:
                    continue
                name = str(Party.Players.GetPlayerNameByLoginNumber(login_number) or "")
                if not name:
                    continue
                agent_id = int(Party.Players.GetAgentIDByLoginNumber(login_number) or 0)
                rows.append({
                    "name": name,
                    "name_norm": _normalize_name(name),
                    "login_number": login_number,
                    "agent_id": agent_id,
                    "member_type": "human",
                    "is_human": True,
                })
            except Exception:
                continue
        return rows

    def _hero_member_type(hero_obj) -> str:
        # Mercenary heroes are HeroType IDs 28..35 in this codebase.
        # Other hero IDs are regular heroes (NPC party members).
        try:
            hero_id_obj = getattr(hero_obj, "hero_id", None)
            hero_id = int(hero_id_obj.GetID() if hero_id_obj is not None else 0)
            if 28 <= hero_id <= 35:
                return "mercenary"
        except Exception:
            pass
        return "hero"

    def _get_party_member_rows():
        rows = []
        counts = {"humans": 0, "heroes": 0, "mercenaries": 0, "henchmen": 0}
        seen_agent_ids = set()

        # Humans
        for r in _get_party_player_rows():
            aid = int(r.get("agent_id", 0) or 0)
            if aid > 0:
                seen_agent_ids.add(aid)
            rows.append(r)
            counts["humans"] += 1

        # Heroes (regular heroes + mercenaries)
        try:
            heroes = Party.GetHeroes() or []
        except Exception:
            heroes = []
        for h in heroes:
            try:
                agent_id = int(getattr(h, "agent_id", 0) or 0)
                if agent_id <= 0 or agent_id in seen_agent_ids:
                    continue
                mtype = _hero_member_type(h)
                seen_agent_ids.add(agent_id)
                rows.append({
                    "name": f"{'Mercenary' if mtype == 'mercenary' else 'Hero'} {agent_id}",
                    "name_norm": "",
                    "login_number": 0,
                    "agent_id": agent_id,
                    "member_type": mtype,
                    "is_human": False,
                })
                if mtype == "mercenary":
                    counts["mercenaries"] += 1
                else:
                    counts["heroes"] += 1
            except Exception:
                continue

        # Henchmen
        try:
            hench = Party.GetHenchmen() or []
        except Exception:
            hench = []
        for h in hench:
            try:
                agent_id = int(getattr(h, "agent_id", 0) or 0)
                if agent_id <= 0 or agent_id in seen_agent_ids:
                    continue
                seen_agent_ids.add(agent_id)
                rows.append({
                    "name": f"Henchman {agent_id}",
                    "name_norm": "",
                    "login_number": 0,
                    "agent_id": agent_id,
                    "member_type": "henchman",
                    "is_human": False,
                })
                counts["henchmen"] += 1
            except Exception:
                continue

        return rows, counts

    def _get_same_party_accounts():
        try:
            self_email = str(Player.GetAccountEmail() or "")
            if not self_email:
                return []
            me = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email)
            if not me:
                return []
            my_party_id = _acc_party_id(me)
            if my_party_id <= 0:
                return []
            all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
            out = []
            for acc in all_accounts:
                if not acc:
                    continue
                if not bool(getattr(acc, "IsAccount", False)):
                    continue
                if _acc_party_id(acc) != my_party_id:
                    continue
                out.append(acc)
            return out
        except Exception:
            return []

    def _find_item_enabled_and_available(key: str):
        spec = MB_DP_BY_KEY.get(key)
        if not spec:
            return None, 0
        if not bool(cfg.selected.get(key, False)) or not _runtime_regular_enabled(key):
            return None, 0
        model_id = int(spec.get("model_id", 0) or 0)
        if model_id <= 0:
            return None, 0
        item_id = _find_item_id_by_model_id(model_id)
        if item_id <= 0:
            return None, 0
        return spec, item_id

    def _compute_party_morale_states(eligible_name_norms: set, party_rows: list, same_party_accounts: list):
        morale_by_agent = {}
        try:
            for agent_id, morale in (Party.GetPartyMorale() or []):
                morale_by_agent[int(agent_id)] = int(morale)
        except Exception:
            morale_by_agent = {}

        accounts_by_name = {}
        for acc in same_party_accounts:
            nm = _normalize_name(_acc_name(acc))
            if nm:
                accounts_by_name[nm] = acc

        states = []
        for row in party_rows:
            if bool(row.get("is_human", False)):
                if row["name_norm"] not in eligible_name_norms:
                    continue
            else:
                if str(row.get("member_type", "")) not in ("hero", "mercenary", "henchman"):
                    continue
            # API compatibility: some builds key Party.GetPartyMorale() by agent_id,
            # others by login_number (player_id). Try both.
            raw = morale_by_agent.get(int(row["agent_id"]), None)
            if raw is None:
                login_number = int(row.get("login_number", 0) or 0)
                if login_number > 0:
                    raw = morale_by_agent.get(login_number, None)
            if raw is None:
                acc = accounts_by_name.get(row["name_norm"])
                if acc:
                    raw = _acc_player_morale(acc)
            if raw is None and int(row["agent_id"]) == int(Player.GetAgentID()):
                raw = int(Player.GetMorale() or 0)
            if raw is None and not bool(row.get("is_human", False)):
                continue
            st = _morale_state(int(raw or 0))
            st["name"] = row["name"]
            st["name_norm"] = row["name_norm"]
            st["agent_id"] = int(row["agent_id"])
            st["member_type"] = str(row.get("member_type", "human"))
            states.append(st)
        return states

    def _coordinator_gate(same_party_accounts: list) -> bool:
        self_email = str(Player.GetAccountEmail() or "")
        broadcasters = []
        for acc in same_party_accounts:
            email = _acc_email(acc)
            if not email:
                continue
            is_broadcaster, _ = _load_team_flags_for_email(email)
            if is_broadcaster:
                broadcasters.append(acc)
        if not broadcasters:
            return False
        broadcasters.sort(key=lambda x: (_acc_party_position(x), _acc_email(x)))
        leader_email = _acc_email(broadcasters[0])
        return bool(self_email and leader_email and self_email == leader_email)

    def _mbdp_tick_precheck() -> bool:
        if not bool(cfg.mbdp_enabled):
            return False
        if not Routines.Checks.Map.MapValid():
            return False
        if _should_block_consumption():
            return False
        if not bool(_in_explorable()):
            return False
        if not (aftercast_timer.IsStopped() or aftercast_timer.HasElapsed(int(AFTERCAST_MS))):
            return False
        if not _movement_gate_allows("mbdp"):
            _record_movement_block("mbdp", "Morale/DP items")
            return False
        return True

    def _mbdp_run_self_phase() -> bool:
        self_state = _morale_state(int(Player.GetMorale() or 0))
        self_dp = int(self_state["dp"])
        self_eff = int(self_state["effective"])
        st = _warn_timer_for("mbdp_self_state")
        if st.IsStopped() or st.HasElapsed(2500):
            st.Start()
            _debug(f"MB/DP SELF state: raw={self_state['raw']} effective={_fmt_effective(self_eff)} dp={self_dp}")

        # Self DP upkeep: remove-all first if high DP.
        self_major_dp_threshold = max(0, -int(cfg.mbdp_self_dp_major_threshold))
        self_minor_dp_threshold = max(0, -int(cfg.mbdp_self_dp_minor_threshold))

        if self_dp >= self_major_dp_threshold:
            spec, item_id = _find_item_enabled_and_available("peppermint_candy_cane")
            if spec and item_id > 0:
                _debug(
                    f"MB/DP SELF fire {spec['label']}: raw={self_state['raw']} eff={_fmt_effective(self_eff)} "
                    f"dp={self_dp} trigger={_fmt_effective(cfg.mbdp_self_dp_major_threshold)} (~{self_major_dp_threshold}% DP)"
                )
                if _use_item_id(item_id, spec["key"]):
                    aftercast_timer.Start()
                    _last_used_ms[spec["key"]] = _now_ms()
                    return True

        if self_dp >= self_minor_dp_threshold:
            for key in ("refined_jelly", "wintergreen_candy_cane"):
                spec, item_id = _find_item_enabled_and_available(key)
                if spec and item_id > 0:
                    _debug(
                        f"MB/DP SELF fire {spec['label']}: raw={self_state['raw']} eff={_fmt_effective(self_eff)} "
                        f"dp={self_dp} trigger={_fmt_effective(cfg.mbdp_self_dp_minor_threshold)} (~{self_minor_dp_threshold}% DP)"
                    )
                    if _use_item_id(item_id, spec["key"]):
                        aftercast_timer.Start()
                        _last_used_ms[spec["key"]] = _now_ms()
                        return True
                    break

        # Self morale upkeep: only fire if gain would not be mostly wasted.
        gain_if_10 = max(0, min(10, 10 - self_eff))
        if self_eff < int(cfg.mbdp_self_morale_target_effective) and gain_if_10 >= int(cfg.mbdp_self_min_morale_gain):
            order = ("seal_of_the_dragon_empire", "pumpkin_cookie") if bool(cfg.mbdp_prefer_seal_for_recharge) else ("pumpkin_cookie", "seal_of_the_dragon_empire")
            for key in order:
                spec, item_id = _find_item_enabled_and_available(key)
                if spec and item_id > 0:
                    _debug(
                        f"MB/DP SELF fire {spec['label']}: raw={self_state['raw']} eff={_fmt_effective(self_eff)} dp={self_dp} "
                        f"target={_fmt_effective(cfg.mbdp_self_morale_target_effective)} gain10={gain_if_10}"
                    )
                    if _use_item_id(item_id, spec["key"]):
                        aftercast_timer.Start()
                        _last_used_ms[spec["key"]] = _now_ms()
                        return True
                    break
        return False

    def _mbdp_prepare_party_context():
        if not bool(cfg.team_broadcast):
            return None
        same_party_accounts = _get_same_party_accounts()
        if not same_party_accounts:
            return None
        if not _coordinator_gate(same_party_accounts):
            return None

        party_rows, party_counts = _get_party_member_rows()
        if not party_rows:
            return None
        party_human_name_norms = {r["name_norm"] for r in party_rows if bool(r.get("is_human", False)) and r.get("name_norm")}
        self_email = str(Player.GetAccountEmail() or "")
        self_name_norm = _normalize_name(Player.GetName())
        if not self_name_norm:
            for acc in same_party_accounts:
                if _acc_email(acc) == self_email:
                    self_name_norm = _normalize_name(_acc_name(acc))
                    break
        other_human_name_norms = set(party_human_name_norms)
        if self_name_norm in other_human_name_norms:
            other_human_name_norms.remove(self_name_norm)
        else:
            # If local name could not be resolved, avoid false "other human" positives in solo+NPC parties.
            other_human_name_norms = set()
        npc_member_count = int(party_counts["heroes"]) + int(party_counts["mercenaries"]) + int(party_counts["henchmen"])
        _debug(
            f"MB/DP PARTY roster: total={len(party_rows)} humans={party_counts['humans']} heroes={party_counts['heroes']} "
            f"mercs={party_counts['mercenaries']} hench={party_counts['henchmen']}"
        )

        broadcasters = set()
        optins = set()
        recipients_emails = []
        for acc in same_party_accounts:
            email = _acc_email(acc)
            name_norm = _normalize_name(_acc_name(acc))
            if not email or not name_norm:
                continue
            b, o = _load_team_flags_for_email(email)
            if b:
                broadcasters.add(name_norm)
            if o:
                optins.add(name_norm)
                if name_norm in party_human_name_norms and email != self_email:
                    recipients_emails.append(email)

        eligible_humans = party_human_name_norms.intersection(broadcasters.union(optins))
        eligible_total = len(eligible_humans) + npc_member_count
        if eligible_total < int(cfg.mbdp_party_min_members):
            _debug(
                f"MB/DP PARTY skip: eligible_total={eligible_total} (humans={len(eligible_humans)}, npc={npc_member_count}) "
                f"< min_members={cfg.mbdp_party_min_members}"
            )
            return None
        if other_human_name_norms and len(recipients_emails) < 1:
            _debug(
                f"MB/DP PARTY skip: no opted-in recipients among other humans in current party "
                f"(other_humans={len(other_human_name_norms)})."
            )
            return None

        if (not bool(cfg.mbdp_allow_partywide_in_human_parties)) and len(party_human_name_norms.difference(eligible_humans)) > 0:
            _debug(
                f"MB/DP PARTY skip: found non-eligible human party members ({len(party_human_name_norms.difference(eligible_humans))}); "
                "enable 'allow party-wide in human parties' to override."
            )
            return None

        now = _now_ms()
        if _last_mbdp_party_ms > 0 and (now - int(_last_mbdp_party_ms)) < int(cfg.mbdp_party_min_interval_ms):
            return None

        states = _compute_party_morale_states(eligible_humans, party_rows, same_party_accounts)
        if len(states) < int(cfg.mbdp_party_min_members):
            _debug(
                f"MB/DP PARTY skip: sampled_members={len(states)} < min_members={cfg.mbdp_party_min_members} "
                f"(humans={party_counts['humans']} heroes={party_counts['heroes']} mercs={party_counts['mercenaries']} hench={party_counts['henchmen']})"
            )
            return None
        if states:
            _debug(f"MB/DP PARTY sample: {states[0]['name']} raw={states[0]['raw']} effective={_fmt_effective(states[0]['effective'])} dp={states[0]['dp']}")

        total_dp = sum(int(s["dp"]) for s in states)
        party_light_dp_threshold = max(0, -int(cfg.mbdp_party_light_dp_threshold))
        party_heavy_dp_threshold = max(0, -int(cfg.mbdp_party_heavy_dp_threshold))
        party_emergency_dp_threshold = max(0, -int(cfg.mbdp_powerstone_dp_threshold))
        light_cnt = sum(1 for s in states if int(s["dp"]) >= party_light_dp_threshold)
        heavy_cnt = sum(1 for s in states if int(s["dp"]) >= party_heavy_dp_threshold)
        emergency_cnt = sum(1 for s in states if int(s["dp"]) >= party_emergency_dp_threshold)
        target_states = _morale_states_for_targeting(states)
        target_eff = int(cfg.mbdp_party_target_effective)
        gain_5 = sum(max(0, min(5, target_eff - int(s["effective"]))) for s in target_states)
        gain_10 = sum(max(0, min(10, target_eff - int(s["effective"]))) for s in target_states)
        strict_target = int(cfg.mbdp_party_target_effective)
        strict_target_missing = sum(max(0, strict_target - int(s["effective"])) for s in target_states)
        strict_target_members = sum(1 for s in target_states if int(s["effective"]) < strict_target)

        return {
            "same_party_accounts": same_party_accounts,
            "party_rows": party_rows,
            "party_counts": party_counts,
            "states": states,
            "total_dp": int(total_dp),
            "light_cnt": int(light_cnt),
            "heavy_cnt": int(heavy_cnt),
            "emergency_cnt": int(emergency_cnt),
            "party_light_dp_threshold": int(party_light_dp_threshold),
            "party_heavy_dp_threshold": int(party_heavy_dp_threshold),
            "party_emergency_dp_threshold": int(party_emergency_dp_threshold),
            "gain_5": int(gain_5),
            "gain_10": int(gain_10),
            "strict_target": int(strict_target),
            "strict_target_missing": int(strict_target_missing),
            "strict_target_members": int(strict_target_members),
            "recipients_emails": list(recipients_emails),
            "now": int(now),
        }

    def _mbdp_build_party_candidates(ctx: dict) -> list[tuple[str, str]]:
        candidate_choices = []
        if int(ctx["emergency_cnt"]) >= int(cfg.mbdp_party_min_members):
            candidate_choices.append(
                ("powerstone_of_courage", f"emergency_cnt={ctx['emergency_cnt']} trigger={_fmt_effective(cfg.mbdp_powerstone_dp_threshold)} (~{ctx['party_emergency_dp_threshold']}% DP)")
            )
        if int(ctx["heavy_cnt"]) >= int(cfg.mbdp_party_min_members):
            candidate_choices.append(
                ("oath_of_purity", f"heavy_cnt={ctx['heavy_cnt']} trigger={_fmt_effective(cfg.mbdp_party_heavy_dp_threshold)} (~{ctx['party_heavy_dp_threshold']}% DP)")
            )
        if int(ctx["light_cnt"]) >= int(cfg.mbdp_party_min_members):
            candidate_choices.append(
                ("four_leaf_clover", f"light_cnt={ctx['light_cnt']} trigger={_fmt_effective(cfg.mbdp_party_light_dp_threshold)} (~{ctx['party_light_dp_threshold']}% DP)")
            )

        leader_force_active = bool(cfg.mbdp_strict_party_plus10)
        if leader_force_active:
            # In leader force mode, morale spending is strictly target-driven.
            # Only add morale candidates if party members are below the configured target.
            if int(ctx["strict_target_missing"]) > 0:
                strict_reason = (
                    f"strict_target={_fmt_effective(int(ctx['strict_target']))} "
                    f"members_below_target={ctx['strict_target_members']} total_missing={ctx['strict_target_missing']}"
                )
                candidate_choices.append(("elixir_of_valor", strict_reason))
                if bool(cfg.selected.get("rainbow_candy_cane", False)) and _runtime_regular_enabled("rainbow_candy_cane"):
                    candidate_choices.append(("rainbow_candy_cane", strict_reason + " fallback+5"))
                candidate_choices.append(("honeycomb", strict_reason + " fallback+5"))
        else:
            if int(ctx["gain_10"]) >= int(cfg.mbdp_party_min_total_gain_10):
                candidate_choices.append(("elixir_of_valor", f"gain10={ctx['gain_10']} min={cfg.mbdp_party_min_total_gain_10}"))
            elif int(ctx["gain_5"]) >= int(cfg.mbdp_party_min_total_gain_5):
                gain5_reason = f"gain5={ctx['gain_5']} min={cfg.mbdp_party_min_total_gain_5}"
                if bool(cfg.selected.get("rainbow_candy_cane", False)) and _runtime_regular_enabled("rainbow_candy_cane"):
                    candidate_choices.append(("rainbow_candy_cane", gain5_reason))
                candidate_choices.append(("honeycomb", gain5_reason))
        return candidate_choices

    def _mbdp_select_candidate_item(candidate_choices: list[tuple[str, str]]):
        chosen_key = None
        chosen_reason = ""
        spec = None
        item_id = 0
        tried_unavailable = []
        tried_seen = set()
        for key, key_reason in candidate_choices:
            if key in tried_seen:
                continue
            tried_seen.add(key)
            c_spec, c_item_id = _find_item_enabled_and_available(key)
            if c_spec and c_item_id > 0:
                chosen_key = key
                chosen_reason = key_reason
                spec = c_spec
                item_id = c_item_id
                break
            tried_unavailable.append(key)
        return chosen_key, chosen_reason, spec, int(item_id), tried_unavailable

    def _mbdp_execute_party_phase(ctx: dict, candidate_choices: list[tuple[str, str]]) -> bool:
        global _last_mbdp_party_ms
        if not candidate_choices:
            _debug(
                f"MB/DP PARTY skip: members={len(ctx['states'])} total_dp={ctx['total_dp']} light={ctx['light_cnt']} heavy={ctx['heavy_cnt']} "
                f"gain5={ctx['gain_5']} gain10={ctx['gain_10']}"
            )
            return False

        _debug("MB/DP PARTY states: " + ", ".join([f"{s['name']} raw={s['raw']} eff={_fmt_effective(s['effective'])} dp={s['dp']}" for s in ctx["states"]]))
        chosen_key, chosen_reason, spec, item_id, tried_unavailable = _mbdp_select_candidate_item(candidate_choices)
        if not spec or item_id <= 0:
            _debug(
                "MB/DP PARTY skip: no available candidate item after fallback chain; "
                f"tried={','.join(tried_unavailable)}"
            )
            return False
        if tried_unavailable:
            _debug(
                f"MB/DP PARTY fallback: unavailable={','.join(tried_unavailable)} -> using {chosen_key}."
            )

        _debug(
            f"MB/DP PARTY fire {spec['label']}: {chosen_reason}; members={len(ctx['states'])} total_dp={ctx['total_dp']} "
            f"gain5={ctx['gain_5']} gain10={ctx['gain_10']} recipients={len(ctx['recipients_emails'])}"
        )
        if _use_item_id(item_id, spec["key"]):
            _last_mbdp_party_ms = int(ctx["now"])
            _last_used_ms[spec["key"]] = int(ctx["now"])
            aftercast_timer.Start()
            try:
                _broadcast_use(int(spec.get("model_id", 0)), 1, 0, recipients=ctx["recipients_emails"])
            except Exception:
                pass
            return True
        return False

    def _tick_morale_dp_v2() -> bool:
        if not _mbdp_tick_precheck():
            return False
        if _mbdp_run_self_phase():
            return True
        ctx = _mbdp_prepare_party_context()
        if not ctx:
            return False
        candidate_choices = _mbdp_build_party_candidates(ctx)
        return _mbdp_execute_party_phase(ctx, candidate_choices)

    def _tick_morale_dp() -> bool:
        return _tick_morale_dp_v2()

    # -------------------------
    # Tick: normal consumables
    # -------------------------
    def _tick_consume() -> bool:
        ok, keys, in_explorable = _consume_precheck()
        if not ok:
            return False

        for key in keys:
            spec = ALL_BY_KEY.get(key)
            if not spec:
                continue
            if key in MB_DP_BY_KEY:
                continue

            if _is_party_item_spec(spec):
                continue

            if bool(getattr(cfg, "sweets_fast_spending", False)) and _is_sweets_spec(spec):
                continue

            if not _allowed_here(spec, in_explorable):
                continue

            movement_category = _movement_category_for_spec(spec)
            if movement_category and not _movement_gate_allows(movement_category):
                _record_movement_block(movement_category, str(spec.get("label", key) or key))
                continue

            if _is_summoning_spec(spec):
                summon_block_reason = _summoning_block_reason(key, in_explorable)
                if summon_block_reason:
                    _record_summoning_block(key, str(spec.get("label", key) or key), summon_block_reason)
                    continue

            effect_id = _resolve_effect_id_for(key, spec)

            if effect_id and _has_effect(effect_id):
                model_id = int(spec.get("model_id", 0))
                if model_id > 0:
                    _broadcast_keepalive(key, model_id, effect_id)
                continue
            if effect_id <= 0 and _fallback_active(key, spec):
                continue

            if bool(spec.get("require_effect_id", False)) and effect_id <= 0:
                wt = _warn_timer_for(key)
                if wt.IsStopped() or wt.HasElapsed(8000):
                    wt.Start()
                    nm = _skill_name_cache.get(key, "") or (spec.get("skills") or [""])[0]
                    _debug(f"Skipping {spec.get('label','(unknown)')}: could not resolve effect id (tried from '{nm}').", Console.MessageType.Warning)
                continue

            t = _timer_for(key)
            cd = _cooldown_for_key(key, spec)
            if not (t.IsStopped() or t.HasElapsed(int(cd))):
                continue

            model_id = int(spec.get("model_id", 0))
            if model_id <= 0:
                wt = _warn_timer_for(f"consume_modelid_missing_{key}")
                if wt.IsStopped() or wt.HasElapsed(15000):
                    wt.Start()
                    _record_blocked_action(
                        f"consume_modelid_missing_{key}",
                        f"{str(spec.get('label', key) or key)}: model_id=0",
                    )
                    _debug(f"Skipping {spec.get('label','(unknown)')}: model_id is 0 (missing ModelID entry?).", Console.MessageType.Warning)
                continue

            item_id = _find_item_id_by_model_id(model_id)
            if item_id <= 0:
                if _broadcast_enabled_request_without_local_item(key, spec, model_id, effect_id, t):
                    return True
                continue

            _log(f"Using {spec['label']}.", Console.MessageType.Debug)
            if _use_item_id(item_id, key):
                t.Start()
                aftercast_timer.Start()
                _last_used_ms[key] = _now_ms()
                if not _is_summoning_spec(spec) and not bool(spec.get("suppress_team_broadcast", False)):
                    try:
                        _broadcast_use(model_id, 1, effect_id)
                    except Exception:
                        pass
                # Force refresh inventory cache to show accurate count after consumption
                _refresh_inventory_cache(force=True)
                return True

        return False

    # -------------------------
    # Tick: Party Items
    # -------------------------
    def _tick_party_items() -> bool:
        ok, keys, in_explorable = _party_items_precheck()
        if not ok:
            return False

        for key in keys:
            spec = PARTY_ITEMS_BY_KEY.get(key)
            if not spec:
                continue

            if not _allowed_here(spec, in_explorable):
                continue

            party_block_reason = _party_item_block_reason(key, spec)
            if party_block_reason:
                _record_party_item_block(key, str(spec.get("label", key) or key), party_block_reason)
                continue

            if _fallback_active(key, spec):
                continue

            t = _timer_for(key)
            cd = _cooldown_for_key(key, spec)
            if not (t.IsStopped() or t.HasElapsed(int(cd))):
                continue

            model_id = int(spec.get("model_id", 0))
            if model_id <= 0:
                wt = _warn_timer_for(f"consume_modelid_missing_{key}")
                if wt.IsStopped() or wt.HasElapsed(15000):
                    wt.Start()
                    _record_blocked_action(
                        f"consume_modelid_missing_{key}",
                        f"{str(spec.get('label', key) or key)}: model_id=0",
                    )
                    _debug(f"Skipping {spec.get('label','(unknown)')}: model_id is 0 (missing ModelID entry?).", Console.MessageType.Warning)
                continue

            item_id = _find_item_id_by_model_id(model_id)
            if item_id <= 0:
                continue

            _log(f"Using {spec['label']}.", Console.MessageType.Debug)
            if _use_item_id(item_id, key):
                t.Start()
                aftercast_timer.Start()
                _last_used_ms[key] = _now_ms()
                _refresh_inventory_cache(force=True)
                return True

        return False

    # -------------------------
    # Tick: fast sweets spending
    # -------------------------
    def _tick_sweets() -> bool:
        ok, keys, in_explorable = _sweets_precheck()
        if not ok:
            return False

        t = _timer_for("sweets_fast_global")
        interval_ms = int(
            max(
                MIN_SWEETS_FAST_INTERVAL_MS,
                min(MAX_SWEETS_FAST_INTERVAL_MS, int(getattr(cfg, "sweets_fast_interval_ms", DEFAULT_SWEETS_FAST_INTERVAL_MS))),
            )
        )
        if not (t.IsStopped() or t.HasElapsed(interval_ms)):
            return False
        t.Start()

        for key in keys:
            spec = SWEET_ITEMS_BY_KEY.get(key)
            if not spec:
                continue
            if not _allowed_here(spec, in_explorable):
                continue

            model_id = int(spec.get("model_id", 0))
            if model_id <= 0:
                wt = _warn_timer_for(f"consume_modelid_missing_{key}")
                if wt.IsStopped() or wt.HasElapsed(15000):
                    wt.Start()
                    _record_blocked_action(
                        f"consume_modelid_missing_{key}",
                        f"{str(spec.get('label', key) or key)}: model_id=0",
                    )
                    _debug(f"Skipping {spec.get('label','(unknown)')}: model_id is 0 (missing ModelID entry?).", Console.MessageType.Warning)
                continue

            item_id = _find_item_id_by_model_id(model_id)
            if item_id <= 0:
                continue

            _log(f"Fast using {spec.get('label','Sweets')}.", Console.MessageType.Debug)
            if _use_item_id(item_id, key):
                aftercast_timer.Start()
                _last_used_ms[key] = _now_ms()
                _refresh_inventory_cache(force=True)
                return True

        return False

    # -------------------------
    # Tick: alcohol upkeep
    # -------------------------
    def _tick_alcohol() -> bool:
        ok, target, pool_keys, _in_explorable_unused, now, cur_level = _alcohol_precheck()
        if not ok:
            return False

        t = _timer_for("alcohol_global")
        fast_spending = bool(getattr(cfg, "alcohol_fast_spending", False))
        interval_ms = (
            max(
                MIN_ALCOHOL_FAST_INTERVAL_MS,
                min(MAX_ALCOHOL_FAST_INTERVAL_MS, int(getattr(cfg, "alcohol_fast_interval_ms", DEFAULT_ALCOHOL_FAST_INTERVAL_MS))),
            )
            if fast_spending
            else 2500
        )
        if not (t.IsStopped() or t.HasElapsed(int(interval_ms))):
            return False

        pick = _pick_alcohol(cur_level, target, pool_keys)
        if not pick:
            return False

        model_id = int(pick.get("model_id", 0))
        if model_id <= 0:
            wt = _warn_timer_for("alcohol_modelid_missing_" + pick.get("key", "unknown"))
            if wt.IsStopped() or wt.HasElapsed(15000):
                wt.Start()
                _record_blocked_action(
                    "alcohol_modelid_missing_" + str(pick.get("key", "unknown")),
                    f"{str(pick.get('label','(unknown)') or '(unknown)')}: model_id=0",
                )
                _debug(f"Alcohol '{pick.get('label','(unknown)')}' has model_id=0 in your build, skipping.", Console.MessageType.Warning)
            return False

        item_id = _find_item_id_by_model_id(model_id)
        if item_id <= 0:
            return False

        if fast_spending:
            _log(f"Fast drinking {pick.get('label','Alcohol')}.", Console.MessageType.Debug)
        else:
            _log(f"Drinking {pick.get('label','Alcohol')} (target {target}).", Console.MessageType.Debug)
        if _use_item_id(item_id, pick.get("key", "alcohol")):
            _alcohol_apply_drink(int(pick.get("drunk_add", 1) or 1), now)
            t.Start()
            aftercast_timer.Start()
            try:
                _broadcast_use(model_id, 1, 0)
            except Exception:
                pass
            # Force refresh inventory cache to show accurate count after consumption
            _refresh_inventory_cache(force=True)
            return True

        return False

    def _stock_text_for_model_id(model_id: int) -> str:
        mid = int(model_id or 0)
        if mid <= 0:
            return ""
        known, cnt = _stock_status_for_model_id(mid)
        if not known:
            return "qty -"
        return f"qty {int(cnt)}"

    def _text_with_color(text: str, color: tuple[float, float, float, float]):
        try:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color)
            PyImGui.text(str(text))
            PyImGui.pop_style_color(1)
        except Exception:
            PyImGui.text(str(text))

    def _text_wrapped_with_color(text: str, color: tuple[float, float, float, float]):
        pushed = False
        try:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color)
            pushed = True
            if hasattr(PyImGui, "text_wrapped"):
                PyImGui.text_wrapped(str(text))
            else:
                PyImGui.text(str(text))
        except Exception:
            if hasattr(PyImGui, "text_wrapped"):
                PyImGui.text_wrapped(str(text))
            else:
                PyImGui.text(str(text))
        finally:
            if pushed:
                try:
                    PyImGui.pop_style_color(1)
                except Exception:
                    pass

    def _text_secondary(text: str):
        _text_with_color(str(text), (0.82, 0.84, 0.88, 1.00))

    def _text_meta(text: str):
        _text_with_color(str(text), (0.72, 0.75, 0.80, 1.00))

    def _text_meta_wrapped(text: str):
        _text_wrapped_with_color(str(text), (0.72, 0.75, 0.80, 1.00))

    def _profile_set_ui_status(text: str, *, error: bool = False):
        _rt.profile_status_text = str(text or "")
        _rt.profile_status_error = bool(error)

    def _set_active_applied_profile_id(profile_id: str):
        _rt.profile_active_applied_id = str(profile_id or "").strip()

    def _get_active_applied_profile_id(profiles: list[dict[str, Any]] | None = None) -> str:
        profile_list = list(profiles or [])
        valid_profile_ids = {str(profile.get("id", "") or "") for profile in profile_list}

        active_profile_id = str(getattr(_rt, "profile_active_applied_id", "") or "").strip()
        if active_profile_id:
            if not valid_profile_ids or active_profile_id in valid_profile_ids:
                return active_profile_id
            _set_active_applied_profile_id("")

        if cfg is None or not profile_list:
            return ""

        last_applied_name_norm = _profile_name_norm(str(getattr(cfg, "last_applied_preset", "") or ""))
        if not last_applied_name_norm:
            return ""

        for profile in profile_list:
            profile_id = str(profile.get("id", "") or "").strip()
            if profile_id and _profile_name_norm(profile.get("name", "")) == last_applied_name_norm:
                _set_active_applied_profile_id(profile_id)
                return profile_id
        return ""

    def _clear_remote_profile_apply_confirmation():
        _rt.sync_pending_profile_apply_id = ""
        _rt.sync_pending_profile_apply_targets_key = ""

    def _clear_profile_confirmation_state():
        _rt.profile_pending_save_over_id = ""
        _rt.profile_pending_delete_id = ""
        _clear_remote_profile_apply_confirmation()

    def _set_selected_profile_id(profile_id: str, *, clear_status: bool = True):
        new_profile_id = str(profile_id or "")
        current_profile_id = str(getattr(_rt, "profile_selected_id", "") or "")
        if new_profile_id == current_profile_id:
            return
        _rt.profile_selected_id = new_profile_id
        _clear_profile_confirmation_state()
        if not new_profile_id:
            _rt.profile_rename_input = ""
            _rt.profile_rename_input_source_id = ""
        if clear_status:
            _profile_set_ui_status("")

    def _get_selected_profile_entry(profiles: list[dict[str, str]]):
        valid_profile_ids = {str(profile.get("id", "") or "") for profile in profiles}
        selected_id = str(getattr(_rt, "profile_selected_id", "") or "")
        if selected_id and selected_id not in valid_profile_ids:
            _set_selected_profile_id("", clear_status=True)
            selected_id = ""

        pending_overwrite_id = str(getattr(_rt, "profile_pending_save_over_id", "") or "")
        pending_delete_id = str(getattr(_rt, "profile_pending_delete_id", "") or "")
        if (
            (pending_overwrite_id and pending_overwrite_id not in valid_profile_ids)
            or (pending_delete_id and pending_delete_id not in valid_profile_ids)
        ):
            _clear_profile_confirmation_state()
            _profile_set_ui_status("")

        selected_profile = None
        for profile in profiles:
            if str(profile.get("id", "") or "") == selected_id:
                selected_profile = profile
                break

        selected_profile_id = str(selected_profile.get("id", "") or "") if selected_profile else ""
        if selected_profile_id:
            if str(getattr(_rt, "profile_rename_input_source_id", "") or "") != selected_profile_id:
                _rt.profile_rename_input = str(selected_profile.get("name", "") or "")
                _rt.profile_rename_input_source_id = selected_profile_id
        elif not profiles:
            _set_selected_profile_id("", clear_status=False)
            _rt.profile_rename_input_source_id = ""

        return selected_profile

    def _selected_pycons_sync_accounts_key(account_emails: list[str] | None = None) -> str:
        emails = account_emails if account_emails is not None else _get_selected_pycons_sync_account_emails()
        normalized = sorted(
            {
                _normalize_sync_account_email(email)
                for email in (emails or [])
                if _normalize_sync_account_email(email)
            }
        )
        return "|".join(normalized)

    def _set_pycons_sync_account_selected(normalized_email: str, selected: bool):
        key = _normalize_sync_account_email(normalized_email)
        if not key:
            return
        next_value = bool(selected)
        current_value = bool(_rt.sync_selected_accounts.get(key, False))
        if current_value == next_value:
            return
        _rt.sync_selected_accounts[key] = next_value
        _clear_remote_profile_apply_confirmation()

    def _replace_pycons_sync_account_selection(active_accounts: list[object], selector) -> None:
        for acc in list(active_accounts or []):
            raw_email = str(_acc_email(acc) or "").strip()
            normalized_email = _normalize_sync_account_email(raw_email)
            if not normalized_email:
                continue
            try:
                should_select = bool(selector(acc))
            except Exception:
                should_select = False
            _set_pycons_sync_account_selected(normalized_email, should_select)

    def _section_text(text: str, section_key: str, secondary: bool = False):
        palette = _section_palette(section_key)
        color_key = "meta" if bool(secondary) else "text"
        _text_with_color(str(text), palette[color_key])

    def _draw_pycons_sync_section():
        active_accounts = _get_pycons_sync_accounts()
        selected_categories = _get_selected_pycons_sync_categories()
        selected_accounts = _get_selected_pycons_sync_account_emails()
        current_account_is_party_leader = _pycons_sync_current_account_is_party_leader()
        profiles = _list_pycons_profiles()
        selected_profile = _get_selected_profile_entry(profiles)
        selected_profile_context = _selected_profile_ui_context(selected_profile)
        if selected_profile_context is not None:
            selected_profile = selected_profile_context
        selected_profile_id = str(selected_profile.get("id", "") or "") if selected_profile else ""
        selected_profile_name = str(selected_profile.get("name", "") or "") if selected_profile else ""
        selected_profile_summary = str(selected_profile.get("summary_text", "") or "") if selected_profile else ""
        selected_profile_matches_live = bool(selected_profile.get("matches_live", True)) if selected_profile else True
        selected_accounts_key = _selected_pycons_sync_accounts_key(selected_accounts)

        pending_profile_apply_id = str(getattr(_rt, "sync_pending_profile_apply_id", "") or "")
        pending_profile_apply_targets_key = str(getattr(_rt, "sync_pending_profile_apply_targets_key", "") or "")
        if pending_profile_apply_id and (
            pending_profile_apply_id != selected_profile_id
            or pending_profile_apply_targets_key != selected_accounts_key
            or not selected_profile_id
            or not selected_accounts_key
        ):
            _clear_remote_profile_apply_confirmation()

        _text_secondary("Select active multibox target accounts below. Both actions use the same target list.")
        _text_secondary("Window layout, presets, and filters stay local. Temporary ON/OFF changes copy only when selected below.")
        PyImGui.dummy(0, 4)

        _text_secondary(f"{len(active_accounts)} active account(s) | {len(selected_accounts)} selected")
        if active_accounts:
            _text_meta("Quick target selectors below replace the current target selection set.")

        if active_accounts:
            if PyImGui.small_button("Select All##pycons_sync_accounts_all"):
                _replace_pycons_sync_account_selection(active_accounts, lambda _acc: True)
            _same_line(10)
            if PyImGui.small_button("Same Map##pycons_sync_accounts_same_map"):
                _replace_pycons_sync_account_selection(active_accounts, _pycons_sync_is_same_map)
            if current_account_is_party_leader:
                _same_line(10)
                if PyImGui.small_button("Followers##pycons_sync_accounts_followers"):
                    _replace_pycons_sync_account_selection(active_accounts, _pycons_sync_is_follower)
            _same_line(10)
            if PyImGui.small_button("Clear##pycons_sync_accounts_clear"):
                _replace_pycons_sync_account_selection(active_accounts, lambda _acc: False)
        else:
            PyImGui.text_disabled("No other active multibox accounts were detected.")

        child_height = min(180, 40 + (26 * max(1, len(active_accounts))))
        if active_accounts:
            if PyImGui.begin_child("pycons_sync_accounts_child", (0, child_height), True, PyImGui.WindowFlags.NoFlag):
                if PyImGui.begin_table(
                    "pycons_sync_accounts_table",
                    4,
                    PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV,
                ):
                    PyImGui.table_setup_column("Use", PyImGui.TableColumnFlags.WidthFixed, 48.0)
                    PyImGui.table_setup_column("Account", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_setup_column("Context", PyImGui.TableColumnFlags.WidthFixed, 180.0)
                    PyImGui.table_setup_column("Status", PyImGui.TableColumnFlags.WidthStretch)
                    for acc in active_accounts:
                        raw_email = str(_acc_email(acc) or "").strip()
                        normalized_email = _normalize_sync_account_email(raw_email)
                        if not raw_email or not normalized_email:
                            continue
                        display_name = _pycons_sync_account_display_name(acc)
                        status = _rt.sync_statuses.get(normalized_email)

                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        is_selected = bool(_rt.sync_selected_accounts.get(normalized_email, False))
                        new_selected = PyImGui.checkbox(f"##pycons_sync_select_{raw_email}", is_selected)
                        if new_selected != is_selected:
                            _set_pycons_sync_account_selected(normalized_email, bool(new_selected))

                        PyImGui.table_set_column_index(1)
                        PyImGui.text(display_name)
                        if raw_email and raw_email != display_name:
                            _text_meta(raw_email)

                        PyImGui.table_set_column_index(2)
                        context_parts = [
                            "Same Map" if _pycons_sync_is_same_map(acc) else "Other Map",
                            "Party" if _pycons_sync_is_same_party(acc) else "No Party",
                        ]
                        _text_meta(" | ".join(context_parts))

                        PyImGui.table_set_column_index(3)
                        if status is None:
                            _text_meta("Idle")
                        else:
                            PyImGui.text(str(status.get("status_label", "Idle") or "Idle"))
                            summary = str(status.get("summary", "") or "").strip()
                            if summary:
                                _text_meta(summary)
                            detail = str(status.get("detail", "") or "").strip()
                            if detail:
                                if hasattr(PyImGui, "text_wrapped"):
                                    PyImGui.text_wrapped(detail)
                                else:
                                    PyImGui.text(detail)
                    PyImGui.end_table()
            PyImGui.end_child()

        selected_accounts = _get_selected_pycons_sync_account_emails()
        selected_accounts_key = _selected_pycons_sync_accounts_key(selected_accounts)

        PyImGui.separator()
        PyImGui.text("Copy selected settings categories to other accounts")
        _text_secondary("Copy only the checked settings groups to the selected accounts.")
        _text_secondary("Use this for small setting changes. Use profiles below for a full setup.")
        PyImGui.dummy(0, 4)

        if PyImGui.small_button("Select All Categories##pycons_sync_categories_all"):
            for category_key, _label in PYCONS_SYNC_CATEGORY_DEFS:
                _rt.sync_selected_categories[str(category_key)] = True
        _same_line(10)
        if PyImGui.small_button("Clear Categories##pycons_sync_categories_clear"):
            for category_key, _label in PYCONS_SYNC_CATEGORY_DEFS:
                _rt.sync_selected_categories[str(category_key)] = False

        for category_key, label in PYCONS_SYNC_CATEGORY_DEFS:
            changed, value = ui_checkbox(
                f"{label}##pycons_sync_category_{category_key}",
                bool(_rt.sync_selected_categories.get(str(category_key), False)),
            )
            if changed:
                _rt.sync_selected_categories[str(category_key)] = bool(value)
            if str(category_key) == PYCONS_SYNC_CATEGORY_SELECTION:
                _same_line(10)
                changed, include_enabled = ui_checkbox(
                    "Copy ON/OFF state##pycons_sync_selection_enabled_state",
                    bool(getattr(cfg, "sync_selection_include_enabled_state", False)),
                )
                if changed:
                    cfg.sync_selection_include_enabled_state = bool(include_enabled)
                    cfg.mark_dirty()
                _tooltip_if_hovered(
                    "When checked, this also copies the sender's current ON/OFF state for the selected main-window items."
                )

        selected_categories = _get_selected_pycons_sync_categories()
        copy_disabled = (len(selected_categories) == 0 or len(selected_accounts) == 0)
        mode = _begin_disabled(copy_disabled)
        if PyImGui.button("Copy Selected Settings Categories##pycons_sync_settings_button"):
            _pycons_start_settings_sync()
        _end_disabled(mode)

        PyImGui.separator()
        PyImGui.text("Load selected profile on selected accounts")
        if selected_profile_id:
            PyImGui.text(f"Source profile: {selected_profile_name}")
            if selected_profile_summary:
                _text_secondary(selected_profile_summary)
            if not selected_profile_matches_live:
                _text_meta("This uses the selected saved profile, not your current unsaved changes.")
        else:
            PyImGui.text_disabled("No saved profile selected. Select one in Profiles.")
        _text_secondary("Loads the full selected profile on the selected accounts and asks them to reload Pycons.")
        _text_secondary("Includes team settings such as team calls and follower responses.")

        remote_apply_disabled = (not bool(selected_profile_id) or len(selected_accounts) == 0)
        remote_apply_confirm_required = bool(
            selected_profile_id
            and selected_accounts_key
            and selected_profile_id == str(getattr(_rt, "sync_pending_profile_apply_id", "") or "")
            and selected_accounts_key == str(getattr(_rt, "sync_pending_profile_apply_targets_key", "") or "")
        )
        remote_apply_label = (
            "Click Again to Load Selected Profile on Selected Accounts##pycons_sync_apply_profile_button"
            if remote_apply_confirm_required
            else "Load Selected Profile on Selected Accounts##pycons_sync_apply_profile_button"
        )
        mode = _begin_disabled(remote_apply_disabled)
        if PyImGui.button(remote_apply_label):
            if remote_apply_confirm_required:
                _pycons_start_profile_apply_to_accounts(selected_profile_id)
                _clear_remote_profile_apply_confirmation()
            else:
                _rt.sync_pending_profile_apply_id = str(selected_profile_id or "")
                _rt.sync_pending_profile_apply_targets_key = str(selected_accounts_key or "")
        _end_disabled(mode)

        _text_secondary(str(getattr(_rt, "sync_summary_text", "") or "No other-accounts action run yet."))

    def _draw_inline_stock_text(model_id: int, spacing: float = 10.0):
        stock_text = _stock_text_for_model_id(int(model_id or 0))
        if not stock_text:
            return
        _same_line(spacing)
        _text_meta(stock_text)

    def _draw_main_row_checkbox_and_badge(key: str, label: str, enabled_now: bool, id_prefix: str, model_id: int = 0):
        enabled, _changed, _used_icon = _draw_icon_toggle_or_checkbox(
            bool(enabled_now), key, label, f"{id_prefix}_main", icon_size=20.0
        )
        _same_line(10)
        PyImGui.text(label)
        _tooltip_if_hovered(_consumable_tooltip_with_label(key, label))
        _draw_inline_stock_text(model_id, spacing=10.0)
        _same_line(12)
        if _badge_button("ON" if enabled else "OFF", enabled=bool(enabled), id_suffix=f"{id_prefix}_btn_{key}"):
            enabled = not enabled
        _tooltip_if_hovered(
            "Temporary toggle for this session only. Use Settings to change saved defaults."
            if not _main_runtime_persist_enabled()
            else "This toggle is active now and also saved as the default."
        )
        changed = (bool(enabled_now) != bool(enabled))
        return bool(enabled), bool(changed)

    def _has_inventory_for_model_id(model_id: int) -> bool:
        mid = int(model_id or 0)
        if mid <= 0:
            return False
        known, cnt = _stock_status_for_model_id(mid)
        if not known:
            _refresh_inventory_cache(False)
            known, cnt = _stock_status_for_model_id(mid)
        return bool(known and int(cnt) > 0)

    def _draw_blocked_actions_section():
        rows = _active_blocked_actions()
        if not rows:
            return
        PyImGui.separator()
        try:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.00, 0.86, 0.36, 1.00))
            PyImGui.text("Blocked actions:")
            PyImGui.pop_style_color(1)
        except Exception:
            PyImGui.text("Blocked actions:")
        _same_line(10)
        if PyImGui.small_button("Clear##pycons_blocked_actions_clear"):
            _blocked_actions.clear()
            return
        for msg, count, age_s in rows:
            suffix = f" x{int(count)}" if int(count) > 1 else ""
            line = f"- {msg}{suffix} ({int(age_s)}s ago)"
            try:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.00, 0.94, 0.78, 1.00))
                PyImGui.text(line)
                PyImGui.pop_style_color(1)
            except Exception:
                PyImGui.text(line)

    def _restock_status_snapshot() -> tuple[int, int, str]:
        shortages = 0
        excess = 0
        seen_models = set()

        try:
            _refresh_inventory_cache(False)
        except Exception:
            pass

        for key, spec in _selected_restock_specs():
            if key in cfg.alcohol_selected:
                if not _restock_alcohol_enabled(key):
                    continue
            else:
                if not _restock_regular_enabled(key):
                    continue

            model_id = int(spec.get("model_id", 0) or 0)
            if model_id <= 0 or model_id in seen_models:
                continue

            known, cnt = _stock_status_for_model_id(int(model_id))
            if not known:
                continue

            target = int(_restock_target_for_key(key))
            delta = int(target) - int(cnt)
            if delta > 0:
                shortages += int(delta)
            elif delta < 0:
                excess += int(-delta)
            seen_models.add(int(model_id))

        vault_state = "Closed"
        try:
            inv = getattr(GLOBAL_CACHE, "Inventory", None)
            if inv is not None:
                vault_state = "Open" if bool(inv.IsStorageOpen()) else "Closed"
        except Exception:
            vault_state = "Closed"

        return int(shortages), int(excess), str(vault_state)

    def _draw_restock_status_line():
        shortages, excess, vault_state = _restock_status_snapshot()
        _section_text("Restock:", "restock")
        _same_line(8)
        _text_secondary(f"Shortages {int(shortages)} | Excess {int(excess)} | Vault {vault_state}")

    def _draw_movement_status_line(compact: bool = False):
        status_text, is_recent, _elapsed_ms = _movement_status_summary(compact=compact)
        color = (0.62, 0.90, 0.62, 1.00) if bool(is_recent) else (0.98, 0.70, 0.38, 1.00)
        _text_with_color(status_text, color)

    def _draw_movement_requirement_checkbox(attr_name: str, label: str, tooltip_key: str):
        current = bool(getattr(cfg, attr_name, False))
        changed, value = ui_checkbox(f"{label}##pycons_{attr_name}", current)
        if changed:
            setattr(cfg, attr_name, bool(value))
            cfg.mark_dirty()
        _show_setting_tooltip(tooltip_key)

    def _movement_requirement_attrs() -> tuple[str, ...]:
        return (
            "movement_require_explorable",
            "movement_require_summoning",
            "movement_require_mbdp",
            "movement_require_alcohol",
            "movement_require_party_items",
            "movement_require_sweets",
        )

    def _movement_fast_only_attrs() -> tuple[str, ...]:
        return (
            "movement_alcohol_fast_only",
            "movement_party_items_speed_only",
            "movement_sweets_fast_only",
        )

    def _any_movement_requirement_enabled() -> bool:
        if cfg is None:
            return False
        return any(
            bool(_movement_required_for_category(category))
            for category in ("explorable", "summoning", "mbdp", "alcohol", "party_items", "sweets")
        )

    def _movement_rule_summary_text() -> str:
        if cfg is None:
            return "Active rules: unavailable"

        parts: list[str] = []
        for category in ("explorable", "summoning", "mbdp", "alcohol", "party_items", "sweets"):
            attr_name = _movement_requirement_attr(category)
            if not attr_name or not bool(getattr(cfg, attr_name, False)):
                continue

            label = _movement_category_label(category)
            if category == "alcohol" and bool(getattr(cfg, "movement_alcohol_fast_only", False)):
                parts.append("Alcohol during Fast alcohol spending")
            elif category == "party_items" and bool(getattr(cfg, "movement_party_items_speed_only", False)):
                parts.append(
                    f"Party Items below {_movement_party_items_fast_threshold_ms()} ms (speed is {_party_item_interval_ms()} ms)"
                )
            elif category == "sweets" and bool(getattr(cfg, "movement_sweets_fast_only", False)):
                parts.append("Sweets during Fast sweets spending")
            else:
                parts.append(f"{label} always")

        if not parts:
            return "Active rules: Off"
        return "Active rules: " + ", ".join(parts)

    def _set_movement_requirements(values_by_attr: dict[str, bool]):
        changed_any = False
        for attr_name in _movement_requirement_attrs():
            next_value = bool(values_by_attr.get(attr_name, False))
            if bool(getattr(cfg, attr_name, False)) != next_value:
                setattr(cfg, attr_name, next_value)
                changed_any = True
        if changed_any:
            cfg.mark_dirty()

    def _set_all_movement_requirements(enabled: bool):
        _set_movement_requirements({attr_name: bool(enabled) for attr_name in _movement_requirement_attrs()})

    def _set_movement_fast_only(values_by_attr: dict[str, bool]):
        changed_any = False
        for attr_name in _movement_fast_only_attrs():
            next_value = bool(values_by_attr.get(attr_name, False))
            if bool(getattr(cfg, attr_name, False)) != next_value:
                setattr(cfg, attr_name, next_value)
                changed_any = True
        if changed_any:
            cfg.mark_dirty()

    def _apply_movement_safety_preset(preset: str):
        preset_key = str(preset or "").strip().lower()
        if preset_key == "safe_botting":
            _set_all_movement_requirements(True)
            _set_movement_fast_only({
                "movement_alcohol_fast_only": False,
                "movement_party_items_speed_only": False,
                "movement_sweets_fast_only": False,
            })
            return
        if preset_key == "title_spending":
            _set_movement_requirements({
                "movement_require_explorable": False,
                "movement_require_summoning": False,
                "movement_require_mbdp": False,
                "movement_require_alcohol": True,
                "movement_require_party_items": True,
                "movement_require_sweets": True,
            })
            _set_movement_fast_only({
                "movement_alcohol_fast_only": True,
                "movement_party_items_speed_only": True,
                "movement_sweets_fast_only": True,
            })
            return
        if preset_key == "off":
            _set_all_movement_requirements(False)
            _set_movement_fast_only({
                "movement_alcohol_fast_only": False,
                "movement_party_items_speed_only": False,
                "movement_sweets_fast_only": False,
            })

    def _draw_movement_fast_only_checkbox(attr_name: str, label: str, tooltip_key: str):
        current = bool(getattr(cfg, attr_name, False))
        changed, value = ui_checkbox(f"{label}##pycons_{attr_name}", current)
        if changed:
            setattr(cfg, attr_name, bool(value))
            cfg.mark_dirty()
        _show_setting_tooltip(tooltip_key)

    def _selected_list_child_height(
        selected_explorable_conset: list,
        selected_explorable_other: list,
        selected_summoning: list,
        selected_outpost: list,
        selected_mbdp: list,
        selected_alcohol: list,
        selected_party_items: list,
    ) -> float:
        try:
            line_h = float(PyImGui.get_text_line_height() or 18.0)
        except Exception:
            line_h = 18.0

        rows = 0.0
        if selected_explorable_conset or selected_explorable_other:
            rows += 1.0
            if selected_explorable_conset:
                rows += 1.0 + float(len(selected_explorable_conset)) + 0.5
            if selected_explorable_other:
                rows += float(len(selected_explorable_other)) + 0.6
        if selected_summoning:
            rows += 1.0 + float(len(selected_summoning)) + 0.6
        if selected_outpost:
            rows += 1.0 + float(len(selected_outpost)) + 0.6
        if selected_mbdp:
            rows += 3.0 + float(len(selected_mbdp)) + 0.8
        if selected_alcohol:
            rows += 1.0 + float(len(selected_alcohol)) + 0.4
        if selected_party_items:
            rows += 1.0 + float(len(selected_party_items)) + 0.4

        estimated = (line_h * max(3.0, rows)) + 16.0
        return float(max(MAIN_SELECTED_CHILD_MIN_HEIGHT, min(MAIN_SELECTED_CHILD_MAX_HEIGHT, estimated)))

    def _begin_persistent_window_with_close_state(
        ini_key: str,
        name: str,
        flags: int = PyImGui.WindowFlags.NoFlag,
    ) -> tuple[bool, bool]:
        ini = IniManager()
        ini.begin_window_config(ini_key)

        begin_result = ImGui.begin_with_close(name, True, flags)
        if isinstance(begin_result, tuple) and len(begin_result) == 2:
            expanded, window_open = bool(begin_result[0]), bool(begin_result[1])
        else:
            expanded = bool(begin_result)
            window_open = bool(begin_result)

        if ImGui._is_textured_theme():
            window = ImGui.WindowModule._windows.get(name)
            if window is not None:
                window_open = bool(window.open)
                expanded = bool(window.open and not window.collapse)

        if window_open:
            ini.track_window_collapsed(ini_key, expanded)
            if expanded:
                ini.mark_begin_success(ini_key)

        return expanded, window_open

    def _draw_main_window():
        if cfg is None or not bool(_rt.show_main_window):
            return  # Config not yet loaded
        if bool(_rt.expand_main_window_on_next_show):
            try:
                PyImGui.set_next_window_collapsed(False, PyImGui.ImGuiCond.Always)
            except Exception:
                pass
            _rt.expand_main_window_on_next_show = False
        try:
            PyImGui.set_next_window_size(MAIN_WINDOW_DEFAULT_SIZE, PyImGui.ImGuiCond.FirstUseEver)
        except Exception:
            pass

        window_expanded, window_open = _begin_persistent_window_with_close_state(INI_KEY_MAIN, BOT_NAME)
        _set_main_window_visible(bool(window_open), persist=True, expand_on_show=False)
        if not window_open:
            ImGui.End(INI_KEY_MAIN)
            return
        if not window_expanded:
            ImGui.End(INI_KEY_MAIN)
            return

        if PyImGui.button("Settings##pycons_settings"):
            show_settings[0] = not show_settings[0]

        PyImGui.separator()

        PyImGui.text("How often to check items (ms):")
        _same_line(10)
        changed, val = ui_input_int("##pycons_interval", int(cfg.interval_ms))
        if changed:
            cfg.interval_ms = int(max(MIN_INTERVAL_MS, val))
            cfg.mark_dirty()

        _draw_restock_status_line()
        if _any_movement_requirement_enabled():
            _draw_movement_status_line(compact=True)
        _draw_blocked_actions_section()

        PyImGui.separator()

        # --- Alcohol, Party, and Sweets settings (collapsed dropdown for compactness) ---
        if _styled_collapsing_header("Alcohol/Party & Sweets Settings##pycons_alcohol_dropdown", False, "settings_alcohol"):
            _section_text("Alcohol", "alcohol")
            PyImGui.text("Alcohol upkeep:")
            _same_line(10)
            if _badge_button("ON" if cfg.alcohol_enabled else "OFF", enabled=bool(cfg.alcohol_enabled), id_suffix="pycons_alcohol_toggle"):
                cfg.alcohol_enabled = not bool(cfg.alcohol_enabled)
                cfg.mark_dirty()

            changed, v = ui_checkbox("Disable drunk blur##pycons_alc_disable_effect", bool(cfg.alcohol_disable_effect))
            if changed:
                cfg.alcohol_disable_effect = bool(v)
                cfg.mark_dirty()
                _debug(f"Disable drunk blur setting changed to: {cfg.alcohol_disable_effect}", Console.MessageType.Debug)
            _tooltip_if_hovered(_tooltip_text_for("alcohol_disable_effect"))

            changed, v = ui_checkbox("Explorable##pycons_alc_use_expl", bool(cfg.alcohol_use_explorable))
            if changed:
                cfg.alcohol_use_explorable = bool(v)
                cfg.mark_dirty()

            changed, v = ui_checkbox("Outpost##pycons_alc_use_outpost", bool(cfg.alcohol_use_outpost))
            if changed:
                cfg.alcohol_use_outpost = bool(v)
                cfg.mark_dirty()

            PyImGui.text(f"Target: {int(cfg.alcohol_target_level)}/5")
            _same_line(10)
            if PyImGui.small_button("-##pycons_alc_tgt_minus"):
                cfg.alcohol_target_level = int(max(0, int(cfg.alcohol_target_level) - 1))
                cfg.mark_dirty()
            _same_line(4)
            if PyImGui.small_button("+##pycons_alc_tgt_plus"):
                cfg.alcohol_target_level = int(min(5, int(cfg.alcohol_target_level) + 1))
                cfg.mark_dirty()

            lvl = _alcohol_current_level(_now_ms())
            PyImGui.text(f"Now: {int(lvl)}/5")

            PyImGui.text("Preference:")
            _same_line(10)
            changed, pref_idx = ui_combo("##pycons_alc_pref_main", int(cfg.alcohol_preference), ALCOHOL_PREFERENCE_OPTIONS)
            if changed:
                cfg.alcohol_preference = int(pref_idx)
                cfg.mark_dirty()
            _tooltip_if_hovered(
                "Smooth: balanced target upkeep with less waste.\n"
                "Strong-first: fastest ramp to target.\n"
                "Weak-first: conserves stronger alcohol."
            )

            changed, fast_spending = ui_checkbox(
                "Fast alcohol spending##pycons_alc_fast_spending_main",
                bool(getattr(cfg, "alcohol_fast_spending", False)),
            )
            if changed:
                cfg.alcohol_fast_spending = bool(fast_spending)
                cfg.mark_dirty()
            _tooltip_if_hovered(_tooltip_text_for("alcohol_fast_spending"))
            _same_line(10)
            PyImGui.text("Interval (ms):")
            _same_line(6)
            changed, fast_interval = ui_input_int_fixed(
                "##pycons_alc_fast_interval_main",
                int(getattr(cfg, "alcohol_fast_interval_ms", DEFAULT_ALCOHOL_FAST_INTERVAL_MS)),
                width=120.0,
            )
            if changed:
                cfg.alcohol_fast_interval_ms = int(
                    max(MIN_ALCOHOL_FAST_INTERVAL_MS, min(MAX_ALCOHOL_FAST_INTERVAL_MS, int(fast_interval)))
                )
                cfg.mark_dirty()
            _tooltip_if_hovered(_tooltip_text_for("alcohol_fast_interval_ms"))

            PyImGui.separator()

            _section_text("Party Items", "party_items")
            PyImGui.text("Speed (ms):")
            _same_line(10)
            changed, party_interval = ui_input_int_fixed(
                "##pycons_party_item_interval_main",
                int(getattr(cfg, "party_item_interval_ms", DEFAULT_PARTY_ITEM_INTERVAL_MS)),
                width=120.0,
            )
            if changed:
                cfg.party_item_interval_ms = int(
                    max(MIN_PARTY_ITEM_INTERVAL_MS, min(MAX_PARTY_ITEM_INTERVAL_MS, int(party_interval)))
                )
                cfg.mark_dirty()
            _tooltip_if_hovered(_tooltip_text_for("party_item_interval_ms"))

            PyImGui.separator()

            _section_text("Sweets", "alcohol")
            changed, sweets_fast = ui_checkbox(
                "Fast sweets spending##pycons_sweets_fast_spending_main",
                bool(getattr(cfg, "sweets_fast_spending", False)),
            )
            if changed:
                cfg.sweets_fast_spending = bool(sweets_fast)
                cfg.mark_dirty()
            _tooltip_if_hovered(_tooltip_text_for("sweets_fast_spending"))
            _same_line(10)
            PyImGui.text("Interval (ms):")
            _same_line(6)
            changed, sweets_interval = ui_input_int_fixed(
                "##pycons_sweets_fast_interval_main",
                int(getattr(cfg, "sweets_fast_interval_ms", DEFAULT_SWEETS_FAST_INTERVAL_MS)),
                width=120.0,
            )
            if changed:
                cfg.sweets_fast_interval_ms = int(
                    max(MIN_SWEETS_FAST_INTERVAL_MS, min(MAX_SWEETS_FAST_INTERVAL_MS, int(sweets_interval)))
                )
                cfg.mark_dirty()
            _tooltip_if_hovered(_tooltip_text_for("sweets_fast_interval_ms"))

            PyImGui.separator()

        PyImGui.separator()

        force_open = None
        if request_expand_selected[0]:
            force_open = True
        elif request_collapse_selected[0]:
            force_open = False

        expanded = _styled_collapsing_header_force(
            "Selected consumables##pycons_list",
            force_open,
            bool(cfg.show_selected_list),
            "settings_select",
        )

        if request_expand_selected[0]:
            request_expand_selected[0] = False
        if request_collapse_selected[0]:
            request_collapse_selected[0] = False

        if expanded != bool(cfg.show_selected_list):
            cfg.show_selected_list = bool(expanded)
            cfg.mark_dirty()

        if expanded:
            _text_secondary("Items selected in Settings appear here.")
            if _main_runtime_persist_enabled():
                _text_secondary("ON/OFF here changes this session and saves the new default.")
            else:
                _text_secondary("ON/OFF here only changes this session. Turn on saving in Settings to keep changes.")
            if PyImGui.button(
                "Enable all now and save##pycons_main_select_all"
                if _main_runtime_persist_enabled()
                else "Enable all for this session##pycons_main_select_all"
            ):
                for c in ALL_CONSUMABLES:
                    k = c["key"]
                    if bool(cfg.selected.get(k, False)):
                        _set_main_runtime_regular_enabled(k, True)
                for a in ALCOHOL_ITEMS:
                    k = a["key"]
                    if bool(cfg.alcohol_selected.get(k, False)):
                        _set_main_runtime_alcohol_enabled(k, True)
            _same_line(10)
            if PyImGui.button(
                "Disable all now and save##pycons_main_clear_all"
                if _main_runtime_persist_enabled()
                else "Disable all for this session##pycons_main_clear_all"
            ):
                for c in ALL_CONSUMABLES:
                    k = c["key"]
                    if bool(cfg.selected.get(k, False)):
                        _set_main_runtime_regular_enabled(k, False)
                for a in ALCOHOL_ITEMS:
                    k = a["key"]
                    if bool(cfg.alcohol_selected.get(k, False)):
                        _set_main_runtime_alcohol_enabled(k, False)

            selected_explorable_conset = [c for c in CONSUMABLES if c.get("use_where") == "explorable" and c.get("key") in CONSET_KEYS and bool(cfg.selected.get(c["key"], False))]
            selected_explorable_other = [c for c in CONSUMABLES if c.get("use_where") == "explorable" and c.get("key") not in CONSET_KEYS and bool(cfg.selected.get(c["key"], False))]
            selected_summoning = sorted(
                [c for c in CONSUMABLES if c.get("use_where") == "summoning" and bool(cfg.selected.get(c["key"], False))],
                key=lambda x: str(x.get("label", "")).lower(),
            )
            selected_outpost = [c for c in CONSUMABLES if c.get("use_where") == "outpost" and bool(cfg.selected.get(c["key"], False))]
            selected_mbdp = [c for c in MB_DP_ITEMS if bool(cfg.selected.get(c["key"], False))]
            selected_alcohol = [a for a in ALCOHOL_ITEMS if bool(cfg.alcohol_selected.get(a["key"], False))]
            selected_party_items = [c for c in PARTY_ITEMS if bool(cfg.selected.get(c["key"], False))]
            # Keep the main selected-items panel stable even when inventory hits 0.
            # Availability filtering remains in the Settings browser.

            any_selected = bool(selected_explorable_conset or selected_explorable_other or selected_summoning or selected_outpost or selected_mbdp or selected_alcohol or selected_party_items)
            if not any_selected:
                PyImGui.text_disabled("None selected. Open Settings and pick consumables.")
            else:
                child_height = _selected_list_child_height(
                    selected_explorable_conset,
                    selected_explorable_other,
                    selected_summoning,
                    selected_outpost,
                    selected_mbdp,
                    selected_alcohol,
                    selected_party_items,
                )
                try:
                    avail_h = float(PyImGui.get_content_region_avail()[1] or 0.0)
                    if avail_h > 0.0:
                        child_height = max(1.0, float(avail_h))
                except Exception:
                    pass
                if PyImGui.begin_child(
                    "PyconsSelectedConsumablesChild",
                    size=(0.0, float(child_height)),
                    border=False,
                    flags=PyImGui.WindowFlags.NoFlag,
                ):
                    if selected_explorable_conset or selected_explorable_other:
                        _section_text("Explorable:", "explorable")
                        if selected_explorable_conset:
                            _section_text("Conset:", "explorable", secondary=True)
                            for c in selected_explorable_conset:
                                k = c["key"]
                                new_enabled, chg = _draw_main_row_checkbox_and_badge(
                                    k, c["label"], _runtime_regular_enabled(k), "pycons", int(c.get("model_id", 0))
                                )
                                if chg:
                                    _set_main_runtime_regular_enabled(k, bool(new_enabled))
                            PyImGui.separator()

                        for c in selected_explorable_other:
                            k = c["key"]
                            new_enabled, chg = _draw_main_row_checkbox_and_badge(
                                k, c["label"], _runtime_regular_enabled(k), "pycons", int(c.get("model_id", 0))
                            )
                            if chg:
                                _set_main_runtime_regular_enabled(k, bool(new_enabled))
                        PyImGui.separator()

                    if selected_summoning:
                        _section_text("Summoning Stones/Items:", "summoning")
                        for c in selected_summoning:
                            k = c["key"]
                            new_enabled, chg = _draw_main_row_checkbox_and_badge(
                                k, c["label"], _runtime_regular_enabled(k), "pycons_summon", int(c.get("model_id", 0))
                            )
                            if chg:
                                _set_main_runtime_regular_enabled(k, bool(new_enabled))
                        PyImGui.separator()

                    if selected_outpost:
                        _section_text("In-town speed boosts:", "outpost")
                        for c in selected_outpost:
                            k = c["key"]
                            new_enabled, chg = _draw_main_row_checkbox_and_badge(
                                k, c["label"], _runtime_regular_enabled(k), "pycons", int(c.get("model_id", 0))
                            )
                            if chg:
                                _set_main_runtime_regular_enabled(k, bool(new_enabled))
                        PyImGui.separator()

                    if selected_mbdp:
                        _section_text("Morale Boost & Death Penalty:", "mbdp")
                        mbdp_by_key = {str(s.get("key", "")): s for s in MB_DP_ITEMS}
                        missing_party_keys = sorted([k for k in MBDP_PARTY_KEYS if k not in mbdp_by_key])
                        missing_self_keys = sorted([k for k in MBDP_SELF_KEYS if k not in mbdp_by_key])

                        party_specs = [c for c in selected_mbdp if str(c.get("key", "")) in MBDP_PARTY_KEYS]
                        self_specs = [c for c in selected_mbdp if str(c.get("key", "")) in MBDP_SELF_KEYS]
                        unmapped_specs = [c for c in selected_mbdp if str(c.get("key", "")) not in MBDP_PARTY_KEYS and str(c.get("key", "")) not in MBDP_SELF_KEYS]

                        _section_text("Party:", "mbdp", secondary=True)
                        for c in sorted(party_specs, key=lambda x: str(x.get("label", "")).lower()):
                            k = c["key"]
                            new_enabled, chg = _draw_main_row_checkbox_and_badge(
                                k, c["label"], _runtime_regular_enabled(k), "pycons_mbdp", int(c.get("model_id", 0))
                            )
                            if chg:
                                _set_main_runtime_regular_enabled(k, bool(new_enabled))

                        if missing_party_keys:
                            PyImGui.text_disabled("Missing mapped party keys: " + ", ".join(missing_party_keys))

                        PyImGui.spacing()
                        _section_text("Self:", "mbdp", secondary=True)
                        for c in sorted(self_specs, key=lambda x: str(x.get("label", "")).lower()):
                            k = c["key"]
                            new_enabled, chg = _draw_main_row_checkbox_and_badge(
                                k, c["label"], _runtime_regular_enabled(k), "pycons_mbdp", int(c.get("model_id", 0))
                            )
                            if chg:
                                _set_main_runtime_regular_enabled(k, bool(new_enabled))

                        if missing_self_keys:
                            PyImGui.text_disabled("Missing mapped self keys: " + ", ".join(missing_self_keys))

                        if unmapped_specs:
                            PyImGui.separator()
                            _section_text("Unmapped:", "mbdp", secondary=True)
                            for c in sorted(unmapped_specs, key=lambda x: str(x.get("label", "")).lower()):
                                k = c["key"]
                                new_enabled, chg = _draw_main_row_checkbox_and_badge(
                                    k, c["label"], _runtime_regular_enabled(k), "pycons_mbdp", int(c.get("model_id", 0))
                                )
                                if chg:
                                    _set_main_runtime_regular_enabled(k, bool(new_enabled))
                        PyImGui.separator()

                    if selected_alcohol:
                        _section_text("Alcohol:", "alcohol")
                        for a in sorted(selected_alcohol, key=lambda x: x.get("label", "")):
                            k = a["key"]
                            enabled_now = _runtime_alcohol_enabled(k)
                            new_enabled, chg = _draw_main_row_checkbox_and_badge(
                                k, _alcohol_display_label(a), enabled_now, "pycons_alc", int(a.get("model_id", 0))
                            )
                            if chg:
                                _set_main_runtime_alcohol_enabled(k, bool(new_enabled))
                        PyImGui.separator()

                    if selected_party_items:
                        _section_text("Party Items:", "party_items")
                        for c in sorted(selected_party_items, key=lambda x: (int(x.get("party_points", 0) or 0), str(x.get("label", "")).lower())):
                            k = c["key"]
                            new_enabled, chg = _draw_main_row_checkbox_and_badge(
                                k, c["label"], _runtime_regular_enabled(k), "pycons_party", int(c.get("model_id", 0))
                            )
                            if chg:
                                _set_main_runtime_regular_enabled(k, bool(new_enabled))
                    PyImGui.end_child()

        ImGui.End(INI_KEY_MAIN)

    # -------------------------
    # Settings Window
    # -------------------------
    def _matches_filter(label, flt):
        return (not flt) or (flt in label.lower())

    def _draw_min_interval_editor(key: str):
        if not bool(cfg.show_advanced_intervals):
            return
        if not bool(cfg.selected.get(key, False)):
            return
        _same_line(12)
        PyImGui.text_disabled("min ms:")
        _same_line(6)
        changed, val = ui_input_int(f"##minint_{key}", int(cfg.min_interval_ms.get(key, 0) or 0))
        if changed:
            cfg.min_interval_ms[key] = int(max(0, val))
            cfg.mark_dirty()

    def _passes_settings_item_filters(
        spec: dict,
        label: str,
        flt: str,
        selected_now: bool,
        only_available: bool = False,
        only_selected: bool = False,
    ) -> bool:
        if not _matches_filter(label, flt):
            return False
        if bool(only_selected) and not bool(selected_now):
            return False
        model_id = int(spec.get("model_id", 0))
        if bool(only_available) and model_id > 0 and not _has_inventory_for_model_id(model_id):
            return False
        return True

    def _count_visible_settings_specs(spec_list: list, flt: str, only_available: bool = False, only_selected: bool = False, alcohol: bool = False) -> int:
        total = 0
        for spec in list(spec_list or []):
            key = str(spec.get("key", "") or "")
            label = _alcohol_display_label(spec) if alcohol else str(spec.get("label", "") or "")
            selected_now = bool(cfg.alcohol_selected.get(key, False)) if alcohol else bool(cfg.selected.get(key, False))
            if _passes_settings_item_filters(spec, label, flt, selected_now, only_available=only_available, only_selected=only_selected):
                total += 1
        return int(total)

    def _effective_section_open(force_open, saved_open: bool) -> bool:
        if force_open is not None:
            return bool(force_open)
        return bool(saved_open)

    def _draw_settings_row(spec: dict, flt: str, visible_keys_out=None, only_available: bool = False, only_selected: bool = False):
        k = spec["key"]
        label = spec["label"]
        prev = bool(cfg.selected.get(k, False))
        if not _passes_settings_item_filters(spec, label, flt, prev, only_available=only_available, only_selected=only_selected):
            return
        if visible_keys_out is not None:
            visible_keys_out.append(k)
        model_id = int(spec.get("model_id", 0))
        selected, _changed, _used_icon = _draw_icon_toggle_or_checkbox(
            prev, k, label, "pycons_selected", icon_size=18.0, highlight_selected_box=True
        )
        _same_line(10)
        PyImGui.text(label)
        _tooltip_if_hovered(_consumable_tooltip_with_label(k, label))
        _draw_inline_stock_text(model_id, spacing=10.0)

        _draw_min_interval_editor(k)

        selected = bool(selected)
        if prev != selected:
            _apply_regular_selection_change(k, selected)

    def _draw_alcohol_settings_row(spec: dict, flt: str, visible_keys_out=None, only_available: bool = False, only_selected: bool = False):
        k = spec["key"]
        label = _alcohol_display_label(spec)
        prev = bool(cfg.alcohol_selected.get(k, False))
        if not _passes_settings_item_filters(spec, label, flt, prev, only_available=only_available, only_selected=only_selected):
            return
        if visible_keys_out is not None:
            visible_keys_out.append(k)
        model_id = int(spec.get("model_id", 0))
        selected, _changed, _used_icon = _draw_icon_toggle_or_checkbox(
            prev, k, label, "pycons_alcohol_selected", icon_size=18.0, highlight_selected_box=True
        )
        _same_line(10)
        PyImGui.text(label)
        _tooltip_if_hovered(_consumable_tooltip_with_label(k, label))
        _draw_inline_stock_text(model_id, spacing=10.0)

        selected = bool(selected)
        if prev != selected:
            _apply_alcohol_selection_change(k, selected)

    def _draw_party_item_settings_row(spec: dict, flt: str, visible_keys_out=None, only_available: bool = False, only_selected: bool = False):
        k = spec["key"]
        label = spec["label"]
        prev = bool(cfg.selected.get(k, False))
        if not _passes_settings_item_filters(spec, label, flt, prev, only_available=only_available, only_selected=only_selected):
            return
        if visible_keys_out is not None:
            visible_keys_out.append(k)
        model_id = int(spec.get("model_id", 0))
        selected, _changed, _used_icon = _draw_icon_toggle_or_checkbox(
            prev, k, label, "pycons_party_selected", icon_size=18.0, highlight_selected_box=True
        )
        _same_line(10)
        PyImGui.text(label)
        _same_line(6)
        _text_meta(f"({_party_points_text(int(spec.get('party_points', 0) or 0))})")
        _tooltip_if_hovered(_consumable_tooltip_with_label(k, label))
        _draw_inline_stock_text(model_id, spacing=10.0)

        _draw_min_interval_editor(k)

        selected = bool(selected)
        if prev != selected:
            _apply_regular_selection_change(k, selected)

    def _list_has_match(spec_list: list, flt: str) -> bool:
        if not flt:
            return False
        for s in spec_list:
            if "drunk_add" in s:
                lbl = _alcohol_display_label(s)
            else:
                lbl = s.get("label", "")
            if _matches_filter(lbl, flt):
                return True
        return False

    def _draw_restock_target_item_row(key: str, spec: dict):
        model_id = int(spec.get("model_id", 0) or 0)
        known, cnt = _stock_status_for_model_id(model_id)
        label = _alcohol_display_label(spec) if str(key or "") in ALCOHOL_BY_KEY else str(spec.get("label", key) or key)
        current_target = _restock_target_for_key(key)
        restock_enabled_now = _restock_item_enabled(key)

        PyImGui.table_next_row()
        PyImGui.table_next_column()
        restock_enabled, _changed, _used_icon = _draw_icon_toggle_or_checkbox(
            restock_enabled_now,
            key,
            label,
            "pycons_restock_target",
            icon_size=18.0,
            highlight_selected_box=True,
        )
        if bool(restock_enabled) != bool(restock_enabled_now):
            _set_restock_item_enabled(key, bool(restock_enabled))
        _same_line(10)
        PyImGui.text(label)
        _tooltip_if_hovered(_consumable_tooltip_with_label(key, label))

        PyImGui.table_next_column()
        PyImGui.text(str(int(cnt)) if known else "-")

        PyImGui.table_next_column()
        changed_target, new_target = ui_input_int_fixed(f"##pycons_restock_target_{key}", int(current_target), width=90.0)
        if changed_target:
            cfg.restock_targets[key] = max(0, min(2500, int(new_target)))
            cfg.mark_dirty()

    def _draw_settings_explorable_category(
        explorable_force,
        flt: str,
        search_active: bool,
        conset_has_match: bool,
        explorable_other_has_match: bool,
        explorable_consets: list,
        explorable_other: list,
        visible_regular_keys: list,
        only_available_settings: bool,
        only_selected_settings: bool,
    ):
        explorable_open = _styled_collapsing_header_force(
            "Explorable##pycons_hdr_explorable",
            explorable_force,
            bool(cfg.settings_explorable_open),
            "settings_select_explorable",
        )
        if bool(cfg.settings_explorable_open) != bool(explorable_open):
            cfg.settings_explorable_open = bool(explorable_open)
            cfg.mark_dirty()
        if explorable_open:
            before_explorable = len(visible_regular_keys)
            if (not search_active) or conset_has_match:
                _section_text("Conset:", "explorable", secondary=True)
            for spec in explorable_consets:
                _draw_settings_row(
                    spec,
                    flt,
                    visible_regular_keys,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                )

            if (not search_active) or explorable_other_has_match:
                PyImGui.separator()

            for spec in explorable_other:
                _draw_settings_row(
                    spec,
                    flt,
                    visible_regular_keys,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                )

            if only_available_settings and len(visible_regular_keys) == before_explorable:
                PyImGui.text_disabled("No available items.")

            PyImGui.separator()

    def _draw_settings_mbdp_category(
        mbdp_force,
        flt: str,
        mbdp_items: list,
        visible_regular_keys: list,
        only_available_settings: bool,
        only_selected_settings: bool,
    ):
        mbdp_open = _styled_collapsing_header_force(
            "Morale Boost & Death Penalty##pycons_hdr_mbdp",
            mbdp_force,
            bool(cfg.settings_mbdp_open),
            "settings_select_mbdp",
        )
        if bool(cfg.settings_mbdp_open) != bool(mbdp_open):
            cfg.settings_mbdp_open = bool(mbdp_open)
            cfg.mark_dirty()
        if mbdp_open:
            before_mbdp = len(visible_regular_keys)
            mbdp_by_key = {str(s.get("key", "")): s for s in mbdp_items}
            party_specs = [mbdp_by_key[k] for k in MBDP_PARTY_KEYS if k in mbdp_by_key]
            self_specs = [mbdp_by_key[k] for k in MBDP_SELF_KEYS if k in mbdp_by_key]
            unmapped_specs = [s for s in mbdp_items if str(s.get("key", "")) not in MBDP_PARTY_KEYS and str(s.get("key", "")) not in MBDP_SELF_KEYS]

            missing_party_keys = sorted([k for k in MBDP_PARTY_KEYS if k not in mbdp_by_key])
            missing_self_keys = sorted([k for k in MBDP_SELF_KEYS if k not in mbdp_by_key])

            _section_text("Party:", "mbdp", secondary=True)
            for spec in sorted(party_specs, key=lambda x: str(x.get("label", "")).lower()):
                _draw_settings_row(
                    spec,
                    flt,
                    visible_regular_keys,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                )

            if missing_party_keys:
                PyImGui.text_disabled("Missing mapped party keys: " + ", ".join(missing_party_keys))

            PyImGui.separator()
            _section_text("Self:", "mbdp", secondary=True)
            for spec in sorted(self_specs, key=lambda x: str(x.get("label", "")).lower()):
                _draw_settings_row(
                    spec,
                    flt,
                    visible_regular_keys,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                )

            if missing_self_keys:
                PyImGui.text_disabled("Missing mapped self keys: " + ", ".join(missing_self_keys))

            if unmapped_specs:
                PyImGui.separator()
                _section_text("Unmapped:", "mbdp", secondary=True)
                for spec in sorted(unmapped_specs, key=lambda x: str(x.get("label", "")).lower()):
                    _draw_settings_row(
                        spec,
                        flt,
                        visible_regular_keys,
                        only_available=only_available_settings,
                        only_selected=only_selected_settings,
                    )
            if only_available_settings and len(visible_regular_keys) == before_mbdp:
                PyImGui.text_disabled("No available items.")

    def _draw_settings_outpost_category(
        outpost_force,
        flt: str,
        outpost_items: list,
        visible_regular_keys: list,
        only_available_settings: bool,
        only_selected_settings: bool,
    ):
        outpost_open = _styled_collapsing_header_force(
            "In-town speed boosts##pycons_hdr_outpost",
            outpost_force,
            bool(cfg.settings_outpost_open),
            "settings_select_outpost",
        )
        if bool(cfg.settings_outpost_open) != bool(outpost_open):
            cfg.settings_outpost_open = bool(outpost_open)
            cfg.mark_dirty()
        if outpost_open:
            before_outpost = len(visible_regular_keys)
            for spec in outpost_items:
                _draw_settings_row(
                    spec,
                    flt,
                    visible_regular_keys,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                )
            if only_available_settings and len(visible_regular_keys) == before_outpost:
                PyImGui.text_disabled("No available items.")

    def _draw_settings_summoning_category(
        summoning_force,
        flt: str,
        summoning_items: list,
        visible_regular_keys: list,
        only_available_settings: bool,
        only_selected_settings: bool,
    ):
        summoning_open = _styled_collapsing_header_force(
            "Summoning Stones/Items##pycons_hdr_summoning",
            summoning_force,
            bool(cfg.settings_summoning_open),
            "settings_select_summoning",
        )
        if bool(cfg.settings_summoning_open) != bool(summoning_open):
            cfg.settings_summoning_open = bool(summoning_open)
            cfg.mark_dirty()
        if summoning_open:
            before_summoning = len(visible_regular_keys)
            for spec in sorted(summoning_items, key=lambda x: str(x.get("label", "")).lower()):
                _draw_settings_row(
                    spec,
                    flt,
                    visible_regular_keys,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                )
            if only_available_settings and len(visible_regular_keys) == before_summoning:
                PyImGui.text_disabled("No available items.")
            PyImGui.separator()

    def _draw_settings_alcohol_category(
        alcohol_force,
        flt: str,
        alcohol_items: list,
        visible_alcohol_keys: list,
        only_available_settings: bool,
        only_selected_settings: bool,
    ):
        alcohol_open = _styled_collapsing_header_force(
            "Alcohol##pycons_hdr_alcohol",
            alcohol_force,
            bool(cfg.settings_alcohol_open),
            "settings_select_alcohol",
        )
        if bool(cfg.settings_alcohol_open) != bool(alcohol_open):
            cfg.settings_alcohol_open = bool(alcohol_open)
            cfg.mark_dirty()
        if alcohol_open:
            before_alcohol = len(visible_alcohol_keys)
            for spec in sorted(alcohol_items, key=lambda x: x.get("label", "")):
                _draw_alcohol_settings_row(
                    spec,
                    flt,
                    visible_alcohol_keys,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                )
            if only_available_settings and len(visible_alcohol_keys) == before_alcohol:
                PyImGui.text_disabled("No available items.")

    def _draw_settings_party_items_category(
        party_items_force,
        flt: str,
        party_items: list,
        visible_regular_keys: list,
        only_available_settings: bool,
        only_selected_settings: bool,
    ):
        party_items_open = _styled_collapsing_header_force(
            "Party Items##pycons_hdr_party_items",
            party_items_force,
            bool(getattr(cfg, "settings_party_items_open", False)),
            "settings_select_party_items",
        )
        if bool(getattr(cfg, "settings_party_items_open", False)) != bool(party_items_open):
            cfg.settings_party_items_open = bool(party_items_open)
            cfg.mark_dirty()
        if party_items_open:
            before_party_items = len(visible_regular_keys)
            sorted_party_items = sorted(
                list(party_items or []),
                key=lambda x: (int(x.get("party_points", 0) or 0), str(x.get("label", "")).lower()),
            )
            last_points = None
            for spec in sorted_party_items:
                points = int(spec.get("party_points", 0) or 0)
                label = str(spec.get("label", "") or "")
                selected_now = bool(cfg.selected.get(str(spec.get("key", "") or ""), False))
                if not _passes_settings_item_filters(
                    spec,
                    label,
                    flt,
                    selected_now,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                ):
                    continue
                if last_points != points:
                    if last_points is not None:
                        PyImGui.separator()
                    _section_text(f"{_party_points_text(points)}:", "party_items", secondary=True)
                    last_points = points
                _draw_party_item_settings_row(
                    spec,
                    flt,
                    visible_regular_keys,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                )
            if only_available_settings and len(visible_regular_keys) == before_party_items:
                PyImGui.text_disabled("No available items.")

    def _draw_settings_window():
        if cfg is None:
            return  # Config not yet loaded
        if not bool(_rt.show_main_window):
            show_settings[0] = False
            return
        if not show_settings[0]:
            return

        # Allow manual resizing of the Settings window by removing the
        # AlwaysAutoResize flag. Users can now expand/collapse and resize
        # the settings window to their preference.
        window_expanded, window_open = _begin_persistent_window_with_close_state(
            INI_KEY_SETTINGS,
            "Pycons - Settings##PyconsSettings",
        )
        if not window_open:
            show_settings[0] = False
            ImGui.End(INI_KEY_SETTINGS)
            return
        if not window_expanded:
            ImGui.End(INI_KEY_SETTINGS)
            return

        changed, v = ui_checkbox("Debug logging##pycons_debug", bool(cfg.debug_logging))
        if changed:
            cfg.debug_logging = bool(v)
            cfg.mark_dirty()
        _show_setting_tooltip("debug_logging")

        # Team settings
        changed, v = ui_checkbox("Broadcast usage to team##pycons_team_broadcast", bool(cfg.team_broadcast))
        if changed:
            cfg.team_broadcast = bool(v)
            _mark_mbdp_preset_custom()
            cfg.mark_dirty()
            # Immediately write broadcast setting (don't wait for throttle)
            try:
                ini_handler = _get_ini_handler()
                ini_handler.write_key(INI_SECTION, "team_broadcast", str(bool(v)))
                _log(f"Team broadcast setting changed to: {bool(v)}", Console.MessageType.Info)
            except Exception as e:
                _debug(f"Failed to write team_broadcast: {e}", Console.MessageType.Warning)
        _show_setting_tooltip("team_broadcast")

        changed, v = ui_checkbox("Opt in to team broadcasts (consume when others broadcast)##pycons_team_optin", bool(cfg.team_consume_opt_in))
        if changed:
            cfg.team_consume_opt_in = bool(v)
            _mark_mbdp_preset_custom()
            cfg.mark_dirty()
            # Immediately write opt-in setting (don't wait for throttle)
            try:
                ini_handler = _get_ini_handler()
                ini_handler.write_key(INI_SECTION, "team_consume_opt_in", str(bool(v)))
                _log(f"Team call response setting changed to: {bool(v)}.", Console.MessageType.Info)
            except Exception as e:
                _debug(f"Failed to write team_consume_opt_in: {e}", Console.MessageType.Warning)
        _show_setting_tooltip("team_consume_opt_in")

        changed, v = ui_checkbox("Show per-item timing controls##pycons_advint", bool(cfg.show_advanced_intervals))
        if changed:
            cfg.show_advanced_intervals = bool(v)
            cfg.mark_dirty()
        _show_setting_tooltip("advanced_intervals")

        changed, v = ui_checkbox(
            "Save main-window ON/OFF changes as defaults##pycons_persist_main_runtime_toggles",
            bool(cfg.persist_main_runtime_toggles),
        )
        if changed:
            cfg.persist_main_runtime_toggles = bool(v)
            cfg.mark_dirty()
        _show_setting_tooltip("persist_main_runtime_toggles")

        if PyImGui.button("Set all other party accounts: Opt-in ON##pycons_preset_set_other_optin"):
            _set_other_party_accounts_opt_in()
        _show_setting_tooltip("preset_set_others_optin")

        if PyImGui.button("Set all other party accounts: Opt-in OFF##pycons_preset_set_other_optout"):
            _set_other_party_accounts_opt_out()
        _show_setting_tooltip("preset_set_others_optout")
        PyImGui.text(f"Last team-call change: {str(cfg.last_party_opt_toggle_summary or 'None')}")

        PyImGui.separator()
        presets_section_open = _styled_collapsing_header(
            "Profiles##pycons_settings_presets_dropdown",
            bool(cfg.settings_ui_presets_open),
            "settings_profiles",
        )
        if bool(cfg.settings_ui_presets_open) != bool(presets_section_open):
            cfg.settings_ui_presets_open = bool(presets_section_open)
            cfg.mark_dirty()
        if presets_section_open:
            _show_setting_tooltip("presets_section")
            PyImGui.text(f"Last applied preset/profile: {str(cfg.last_applied_preset or 'None')}")
            PyImGui.separator()
            PyImGui.text("Saved profiles (shared across accounts):")
            if not _profiles_available_for_current_ini():
                _text_secondary("Saved profiles are unavailable until Pycons knows which account config to use.")
            else:
                profiles = _list_pycons_profiles()
                selected_profile = _get_selected_profile_entry(profiles)
                selected_profile_id = str(selected_profile.get("id", "") or "") if selected_profile else ""
                selected_profile_name = str(selected_profile.get("name", "") or "") if selected_profile else ""
                active_profile_id = _get_active_applied_profile_id(profiles)
                selected_profile_summary = ""
                selected_profile_matches_live = True
                selected_profile_is_active = False

                changed_new_profile_name, new_profile_name = ui_input_text(
                    "New profile name##pycons_profile_new_name",
                    str(getattr(_rt, "profile_new_name_input", "") or ""),
                    PROFILE_NAME_MAX_LEN,
                )
                if changed_new_profile_name:
                    _rt.profile_new_name_input = str(new_profile_name or "")

                if PyImGui.button("Save Current As New##pycons_profile_save_new"):
                    _clear_profile_confirmation_state()
                    ok, message, _new_profile_id_unused = _save_current_as_new_profile(
                        str(getattr(_rt, "profile_new_name_input", "") or "")
                    )
                    _profile_set_ui_status(message, error=not ok)
                    if ok:
                        _rt.profile_new_name_input = ""
                        _log(message, Console.MessageType.Info)
                    else:
                        _log(message, Console.MessageType.Warning)
                _show_setting_tooltip("profile_save_new")

                PyImGui.separator()

                if profiles:
                    profile_combo_items = ["<Select saved profile...>"] + [str(profile.get("name", "") or "") for profile in profiles]
                    current_profile_index = 0
                    for idx, profile in enumerate(profiles, start=1):
                        if str(profile.get("id", "") or "") == selected_profile_id:
                            current_profile_index = int(idx)
                            break
                    changed_profile_idx, profile_idx = ui_combo(
                        "Saved profiles##pycons_profile_select",
                        int(current_profile_index),
                        profile_combo_items,
                    )
                    if changed_profile_idx:
                        if int(profile_idx) <= 0:
                            _set_selected_profile_id("")
                        elif int(profile_idx) <= len(profiles):
                            selected_profile = profiles[int(profile_idx) - 1]
                            selected_profile_id = str(selected_profile.get("id", "") or "")
                            selected_profile_name = str(selected_profile.get("name", "") or "")
                            _set_selected_profile_id(selected_profile_id)
                            _rt.profile_rename_input = selected_profile_name
                            _rt.profile_rename_input_source_id = selected_profile_id

                    selected_profile = _get_selected_profile_entry(profiles)
                    selected_profile_context = _selected_profile_ui_context(selected_profile)
                    if selected_profile_context is not None:
                        selected_profile = selected_profile_context
                    selected_profile_id = str(selected_profile.get("id", "") or "") if selected_profile else ""
                    selected_profile_name = str(selected_profile.get("name", "") or "") if selected_profile else ""
                    active_profile_id = _get_active_applied_profile_id(profiles)
                    selected_profile_summary = str(selected_profile.get("summary_text", "") or "") if selected_profile else ""
                    selected_profile_matches_live = bool(selected_profile.get("matches_live", True)) if selected_profile else True
                    selected_profile_is_active = bool(
                        selected_profile_id
                        and active_profile_id
                        and selected_profile_id == active_profile_id
                    )
                    if selected_profile:
                        PyImGui.text(f"Selected profile: {selected_profile_name}")
                        created_at = str(selected_profile.get("created_at", "") or "")
                        updated_at = str(selected_profile.get("updated_at", "") or "")
                        if created_at or updated_at:
                            _text_meta(f"Created: {created_at or '-'} | Updated: {updated_at or '-'}")
                        if selected_profile_summary:
                            _text_secondary(selected_profile_summary)
                        if selected_profile_matches_live:
                            if selected_profile_is_active:
                                _text_meta("This profile is already applied and matches the current settings.")
                            else:
                                _text_meta("Matches selected profile.")
                                _text_meta("This profile is not the active profile on this account.")
                        else:
                            _text_secondary("Live settings differ from selected profile.")
                            if selected_profile_is_active:
                                _text_meta("Use Revert Live Settings to Selected Profile or Save Over Selected below.")
                            else:
                                _text_meta("This profile is not the active profile on this account.")
                    else:
                        _text_secondary("Select a saved profile to load, rename, overwrite, or delete.")
                else:
                    _text_secondary("No saved profiles yet.")
                    _set_active_applied_profile_id("")
                    _set_selected_profile_id("", clear_status=False)
                    _clear_profile_confirmation_state()

                if str(getattr(_rt, "profile_status_text", "") or ""):
                    if bool(getattr(_rt, "profile_status_error", False)):
                        _text_with_color(str(_rt.profile_status_text), (0.92, 0.54, 0.54, 1.00))
                    else:
                        _text_secondary(str(_rt.profile_status_text))

                disabled_mode = _begin_disabled(not bool(selected_profile_id))
                try:
                    changed_rename_name, rename_value = ui_input_text(
                        "Rename to##pycons_profile_rename_name",
                        str(getattr(_rt, "profile_rename_input", "") or ""),
                        PROFILE_NAME_MAX_LEN,
                    )
                    if changed_rename_name:
                        _rt.profile_rename_input = str(rename_value or "")

                    if PyImGui.button("Rename Selected##pycons_profile_rename"):
                        _clear_profile_confirmation_state()
                        ok, message, clean_name = _rename_profile(
                            selected_profile_id,
                            str(getattr(_rt, "profile_rename_input", "") or ""),
                        )
                        _profile_set_ui_status(message, error=not ok)
                        if ok:
                            _rt.profile_rename_input = str(clean_name or "")
                            _rt.profile_rename_input_source_id = str(selected_profile_id or "")
                            _log(message, Console.MessageType.Info)
                        else:
                            _log(message, Console.MessageType.Warning)
                    _show_setting_tooltip("profile_rename")

                    _same_line(8)
                    if PyImGui.button("Duplicate Selected##pycons_profile_duplicate"):
                        _clear_profile_confirmation_state()
                        ok, message, duplicate_profile_id, duplicate_name = _duplicate_profile(selected_profile_id)
                        _profile_set_ui_status(message, error=not ok)
                        if ok:
                            _set_selected_profile_id(duplicate_profile_id, clear_status=False)
                            _rt.profile_rename_input = str(duplicate_name or "")
                            _rt.profile_rename_input_source_id = str(duplicate_profile_id or "")
                            _log(message, Console.MessageType.Info)
                        else:
                            _log(message, Console.MessageType.Warning)
                    _show_setting_tooltip("profile_duplicate")

                    _same_line(8)
                    load_selected_label = "Load Selected##pycons_profile_load_selected"
                    load_selected_disabled = False
                    if selected_profile_is_active:
                        if selected_profile_matches_live:
                            load_selected_label = "Already Matches##pycons_profile_load_selected"
                            load_selected_disabled = True
                        else:
                            load_selected_label = "Revert Live Settings to Selected Profile##pycons_profile_load_selected"
                    load_selected_mode = _begin_disabled(load_selected_disabled)
                    if PyImGui.button(load_selected_label):
                        _clear_profile_confirmation_state()
                        ok, message = _load_profile(selected_profile_id)
                        _profile_set_ui_status(message, error=not ok)
                        if ok:
                            _log(message, Console.MessageType.Info)
                        else:
                            _log(message, Console.MessageType.Warning)
                    _end_disabled(load_selected_mode)
                    _show_setting_tooltip("profile_load_selected")

                    _same_line(8)
                    overwrite_confirm_required = bool(
                        selected_profile_id
                        and selected_profile_id == str(getattr(_rt, "profile_pending_save_over_id", "") or "")
                    )
                    overwrite_label = (
                        "Click Again to Save Over Selected##pycons_profile_save_over_selected"
                        if overwrite_confirm_required
                        else "Save Over Selected##pycons_profile_save_over_selected"
                    )
                    if PyImGui.button(overwrite_label):
                        if overwrite_confirm_required:
                            ok, message = _save_over_profile(selected_profile_id)
                            _clear_profile_confirmation_state()
                            _profile_set_ui_status(message, error=not ok)
                            if ok:
                                _log(message, Console.MessageType.Info)
                            else:
                                _log(message, Console.MessageType.Warning)
                        else:
                            _rt.profile_pending_save_over_id = str(selected_profile_id or "")
                            _rt.profile_pending_delete_id = ""
                            _profile_set_ui_status(
                                f"Click Save Over Selected again to replace '{selected_profile_name}'."
                            )
                    _show_setting_tooltip("profile_save_over_selected")

                    _same_line(8)
                    delete_confirm_required = bool(
                        selected_profile_id
                        and selected_profile_id == str(getattr(_rt, "profile_pending_delete_id", "") or "")
                    )
                    delete_label = (
                        "Click Again to Delete Selected##pycons_profile_delete"
                        if delete_confirm_required
                        else "Delete Selected##pycons_profile_delete"
                    )
                    if PyImGui.button(delete_label):
                        if delete_confirm_required:
                            ok, message = _delete_profile(selected_profile_id)
                            _clear_profile_confirmation_state()
                            _profile_set_ui_status(message, error=not ok)
                            if ok:
                                _set_selected_profile_id("", clear_status=False)
                                _log(message, Console.MessageType.Info)
                            else:
                                _log(message, Console.MessageType.Warning)
                        else:
                            _rt.profile_pending_delete_id = str(selected_profile_id or "")
                            _rt.profile_pending_save_over_id = ""
                            _profile_set_ui_status(
                                f"Click Delete again to remove '{selected_profile_name}'."
                            )
                    _show_setting_tooltip("profile_delete")
                finally:
                    _end_disabled(disabled_mode)
            PyImGui.separator()
        sync_section_open = _styled_collapsing_header(
            "Other Accounts##pycons_settings_sync_dropdown",
            bool(getattr(cfg, "settings_ui_sync_open", False)),
            "settings_other_accounts",
        )
        if bool(getattr(cfg, "settings_ui_sync_open", False)) != bool(sync_section_open):
            cfg.settings_ui_sync_open = bool(sync_section_open)
            cfg.mark_dirty()
        if sync_section_open:
            _draw_pycons_sync_section()
            PyImGui.separator()
        if _styled_collapsing_header("Select consumables to show in the main window##pycons_settings_consumables_dropdown", False, "settings_select"):
            _text_secondary("Items selected here appear in the main window.")
            if bool(cfg.persist_main_runtime_toggles):
                _text_secondary("Main-window ON/OFF also updates saved enabled defaults.")
            else:
                _text_secondary("Main-window ON/OFF changes are temporary unless saving is enabled above.")
            PyImGui.dummy(0, 4)
            PyImGui.text("Search:")
            _same_line(10)
            changed, new_val = ui_input_text("##pycons_filter", filter_text[0], 64)
            if changed:
                filter_text[0] = new_val
            _show_setting_tooltip("filter_search")

            flt = (filter_text[0] or "").strip().lower()
            search_active = bool(flt)

            collapse_now = (last_search_active[0] and not search_active)
            last_search_active[0] = search_active

            PyImGui.dummy(0, 6)

            explorable_consets = [c for c in CONSUMABLES if c.get("use_where") == "explorable" and c.get("key") in CONSET_KEYS]
            explorable_other = [c for c in CONSUMABLES if c.get("use_where") == "explorable" and c.get("key") not in CONSET_KEYS]
            summoning_items = [c for c in CONSUMABLES if c.get("use_where") == "summoning"]
            outpost_items = [c for c in CONSUMABLES if c.get("use_where") == "outpost"]
            mbdp_items = MB_DP_ITEMS
            alcohol_items = ALCOHOL_ITEMS
            party_items = PARTY_ITEMS

            conset_has_match = search_active and _list_has_match(explorable_consets, flt)
            explorable_other_has_match = search_active and _list_has_match(explorable_other, flt)
            explorable_has_match = search_active and (conset_has_match or explorable_other_has_match)
            summoning_has_match = search_active and _list_has_match(summoning_items, flt)
            outpost_has_match = search_active and _list_has_match(outpost_items, flt)
            mbdp_has_match = search_active and _list_has_match(mbdp_items, flt)
            alcohol_has_match = search_active and _list_has_match(alcohol_items, flt)
            party_items_has_match = search_active and _list_has_match(party_items, flt)

            pending_select_visible = False
            pending_clear_visible = False
            pending_expand_all = False
            pending_collapse_all = False

            only_available_settings = bool(cfg.only_show_available_inventory)
            only_selected_settings = bool(cfg.only_show_selected_items)
            if only_available_settings:
                _refresh_inventory_cache(False)

            current_explorable_force = False if collapse_now else (True if explorable_has_match else (False if search_active else None))
            current_summoning_force = False if collapse_now else (True if summoning_has_match else (False if search_active else None))
            current_outpost_force = False if collapse_now else (True if outpost_has_match else (False if search_active else None))
            current_mbdp_force = False if collapse_now else (True if mbdp_has_match else (False if search_active else None))
            current_alcohol_force = False if collapse_now else (True if alcohol_has_match else (False if search_active else None))
            current_party_items_force = False if collapse_now else (True if party_items_has_match else (False if search_active else None))

            current_visible_count = 0
            if _effective_section_open(current_explorable_force, bool(cfg.settings_explorable_open)):
                current_visible_count += _count_visible_settings_specs(
                    explorable_consets,
                    flt,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                    alcohol=False,
                )
                current_visible_count += _count_visible_settings_specs(
                    explorable_other,
                    flt,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                    alcohol=False,
                )
            if _effective_section_open(current_summoning_force, bool(cfg.settings_summoning_open)):
                current_visible_count += _count_visible_settings_specs(
                    summoning_items,
                    flt,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                    alcohol=False,
                )
            if _effective_section_open(current_mbdp_force, bool(cfg.settings_mbdp_open)):
                current_visible_count += _count_visible_settings_specs(
                    mbdp_items,
                    flt,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                    alcohol=False,
                )
            if _effective_section_open(current_outpost_force, bool(cfg.settings_outpost_open)):
                current_visible_count += _count_visible_settings_specs(
                    outpost_items,
                    flt,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                    alcohol=False,
                )
            if _effective_section_open(current_alcohol_force, bool(cfg.settings_alcohol_open)):
                current_visible_count += _count_visible_settings_specs(
                    alcohol_items,
                    flt,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                    alcohol=True,
                )
            if _effective_section_open(current_party_items_force, bool(getattr(cfg, "settings_party_items_open", False))):
                current_visible_count += _count_visible_settings_specs(
                    party_items,
                    flt,
                    only_available=only_available_settings,
                    only_selected=only_selected_settings,
                    alcohol=False,
                )

            disabled_top = (int(current_visible_count) == 0)
            mode = _begin_disabled(disabled_top)

            if PyImGui.button("Select all visible##pycons_sel_all"):
                pending_select_visible = True
            _show_setting_tooltip("select_all_visible")
            _same_line(10)
            if PyImGui.button("Clear all visible##pycons_clear_all"):
                pending_clear_visible = True
            _show_setting_tooltip("clear_all_visible")

            _end_disabled(mode)
            _same_line(10)
            if PyImGui.button("Expand All##pycons_expand_all"):
                pending_expand_all = True
            _show_setting_tooltip("expand_all")
            _same_line(10)
            if PyImGui.button("Collapse All##pycons_collapse_all"):
                pending_collapse_all = True
            _show_setting_tooltip("collapse_all")

            if disabled_top:
                PyImGui.text_disabled("No visible items (open a dropdown or search).")

            PyImGui.separator()
            changed, v = ui_checkbox("Only show available items in inventory##pycons_only_available_inventory", bool(cfg.only_show_available_inventory))
            if changed:
                cfg.only_show_available_inventory = bool(v)
                cfg.mark_dirty()
            _show_setting_tooltip("only_show_available_inventory")
            _same_line(18)
            changed, v = ui_checkbox("Only show selected items##pycons_only_selected_items", bool(cfg.only_show_selected_items))
            if changed:
                cfg.only_show_selected_items = bool(v)
                cfg.mark_dirty()
            _show_setting_tooltip("only_show_selected_items")
            PyImGui.separator()

            only_available_settings = bool(cfg.only_show_available_inventory)
            only_selected_settings = bool(cfg.only_show_selected_items)
            if only_available_settings:
                _refresh_inventory_cache(False)

            if pending_expand_all:
                explorable_force = True
                summoning_force = True
                outpost_force = True
                mbdp_force = True
                alcohol_force = True
                party_items_force = True
            elif pending_collapse_all:
                explorable_force = False
                summoning_force = False
                outpost_force = False
                mbdp_force = False
                alcohol_force = False
                party_items_force = False
            else:
                explorable_force = False if collapse_now else (True if explorable_has_match else (False if search_active else None))
                summoning_force = False if collapse_now else (True if summoning_has_match else (False if search_active else None))
                outpost_force = False if collapse_now else (True if outpost_has_match else (False if search_active else None))
                mbdp_force = False if collapse_now else (True if mbdp_has_match else (False if search_active else None))
                alcohol_force = False if collapse_now else (True if alcohol_has_match else (False if search_active else None))
                party_items_force = False if collapse_now else (True if party_items_has_match else (False if search_active else None))

            visible_regular_keys = []
            visible_alcohol_keys = []

            category_keys = _ordered_consumable_category_keys(["explorable", "summoning", "mbdp", "outpost", "alcohol", "party_items"])
            for category_key in category_keys:
                if category_key == "explorable":
                    _draw_settings_explorable_category(
                        explorable_force,
                        flt,
                        search_active,
                        conset_has_match,
                        explorable_other_has_match,
                        explorable_consets,
                        explorable_other,
                        visible_regular_keys,
                        only_available_settings,
                        only_selected_settings,
                    )
                elif category_key == "summoning":
                    _draw_settings_summoning_category(
                        summoning_force,
                        flt,
                        summoning_items,
                        visible_regular_keys,
                        only_available_settings,
                        only_selected_settings,
                    )
                elif category_key == "mbdp":
                    _draw_settings_mbdp_category(
                        mbdp_force,
                        flt,
                        mbdp_items,
                        visible_regular_keys,
                        only_available_settings,
                        only_selected_settings,
                    )
                elif category_key == "outpost":
                    _draw_settings_outpost_category(
                        outpost_force,
                        flt,
                        outpost_items,
                        visible_regular_keys,
                        only_available_settings,
                        only_selected_settings,
                    )
                elif category_key == "alcohol":
                    _draw_settings_alcohol_category(
                        alcohol_force,
                        flt,
                        alcohol_items,
                        visible_alcohol_keys,
                        only_available_settings,
                        only_selected_settings,
                    )
                elif category_key == "party_items":
                    _draw_settings_party_items_category(
                        party_items_force,
                        flt,
                        party_items,
                        visible_regular_keys,
                        only_available_settings,
                        only_selected_settings,
                    )

            visible_count = len(visible_regular_keys) + len(visible_alcohol_keys)

            if visible_count > 0:
                if pending_select_visible:
                    any_new = False
                    for k in visible_regular_keys:
                        if not bool(cfg.selected.get(k, False)):
                            cfg.selected[k] = True
                            _rt.runtime_selected[k] = True
                            _apply_restock_target_on_select(k)
                            any_new = True
                    for k in visible_alcohol_keys:
                        if not bool(cfg.alcohol_selected.get(k, False)):
                            cfg.alcohol_selected[k] = True
                            _rt.runtime_alcohol_selected[k] = True
                            _apply_restock_target_on_select(k)
                            any_new = True

                    if any_new:
                        if not bool(cfg.show_selected_list):
                            cfg.show_selected_list = True
                        request_expand_selected[0] = True

                    cfg.mark_dirty()

                if pending_clear_visible:
                    for k in visible_regular_keys:
                        cfg.selected[k] = False
                        cfg.enabled[k] = False
                        _rt.runtime_selected[k] = False
                        _rt.runtime_enabled[k] = False
                        _apply_restock_target_on_deselect(k)
                    for k in visible_alcohol_keys:
                        cfg.alcohol_selected[k] = False
                        cfg.alcohol_enabled_items[k] = False
                        _rt.runtime_alcohol_selected[k] = False
                        _rt.runtime_alcohol_enabled[k] = False
                        _apply_restock_target_on_deselect(k)

                    if not _any_selected_anywhere():
                        cfg.show_selected_list = False
                        request_collapse_selected[0] = True

                    cfg.mark_dirty()

        mbdp_section_open = _styled_collapsing_header(
            "Morale Boost & Death Penalty settings##pycons_settings_mbdp_dropdown",
            bool(cfg.settings_ui_mbdp_open),
            "settings_mbdp",
        )
        if bool(cfg.settings_ui_mbdp_open) != bool(mbdp_section_open):
            cfg.settings_ui_mbdp_open = bool(mbdp_section_open)
            cfg.mark_dirty()
        if mbdp_section_open:
            PyImGui.text("Morale and DP upkeep:")
            _same_line(10)
            if _badge_button("ON" if cfg.mbdp_enabled else "OFF", enabled=bool(cfg.mbdp_enabled), id_suffix="pycons_settings_mbdp_toggle"):
                cfg.mbdp_enabled = not bool(cfg.mbdp_enabled)
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_enabled")

            changed, v = ui_checkbox("Allow party-wide items with extra human players##pycons_mbdp_human", bool(cfg.mbdp_allow_partywide_in_human_parties))
            if changed:
                cfg.mbdp_allow_partywide_in_human_parties = bool(v)
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_allow_partywide_in_human_parties")

            changed, v = ui_checkbox("Followers only use items enabled on that account##pycons_mbdp_receiver_require_enabled", bool(cfg.mbdp_receiver_require_enabled))
            if changed:
                cfg.mbdp_receiver_require_enabled = bool(v)
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_receiver_require_enabled")

            changed, v = ui_checkbox("Prefer Seal over Pumpkin for self +10 morale##pycons_mbdp_prefer_seal", bool(cfg.mbdp_prefer_seal_for_recharge))
            if changed:
                cfg.mbdp_prefer_seal_for_recharge = bool(v)
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_prefer_seal_for_recharge")

            if PyImGui.button("Restore default morale/DP settings##pycons_mbdp_restore_defaults"):
                _apply_mbdp_defaults()
                _mark_mbdp_preset_custom()
                _debug("MB/DP settings restored to defaults.", Console.MessageType.Info)
                cfg.save_if_dirty_throttled(0)
            _show_setting_tooltip("mbdp_restore_defaults")

            PyImGui.separator()
            PyImGui.text("Quick role presets:")

            if PyImGui.button("Apply: Solo Safe##pycons_preset_apply_solo_safe"):
                _apply_builtin_preset("solo_safe")
            _show_setting_tooltip("preset_solo_safe")

            if PyImGui.button("Apply: Leader - Force Team Morale##pycons_preset_apply_leader_force"):
                _apply_builtin_preset(LEADER_FORCE_PRESET_KEY)
            _show_setting_tooltip("preset_leader_force_plus10_team")
            _same_line(10)
            PyImGui.text("Value:")
            _same_line(6)
            changed_force_val, force_val = ui_input_int_fixed(
                "##pycons_preset_force_team_morale_value",
                int(getattr(cfg, "force_team_morale_value", 0)),
                width=110.0,
            )
            if changed_force_val:
                new_force = max(-60, min(10, int(force_val)))
                if int(getattr(cfg, "force_team_morale_value", 0)) != int(new_force):
                    cfg.force_team_morale_value = int(new_force)
                    cfg.mark_dirty()
                    # Keep live-apply behavior only when strict mode is currently active.
                    if bool(cfg.mbdp_strict_party_plus10):
                        _apply_builtin_preset(LEADER_FORCE_PRESET_KEY, announce=False)
                    else:
                        _mark_mbdp_preset_custom()
            _show_setting_tooltip("preset_leader_force_plus10_team")
            _same_line(8)
            leader_force_active = _is_leader_force_team_morale_active()
            if _badge_button(
                "ON" if leader_force_active else "OFF",
                enabled=leader_force_active,
                id_suffix="pycons_preset_leader_force_strict_toggle",
            ):
                if leader_force_active:
                    cfg.mbdp_strict_party_plus10 = False
                    _mark_mbdp_preset_custom()
                    cfg.mark_dirty()
                else:
                    _apply_builtin_preset(LEADER_FORCE_PRESET_KEY, announce=False)
            _show_setting_tooltip("preset_leader_force_plus10_team")

            PyImGui.separator()

            PyImGui.text(f"Your light DP cleanup starts at ({_fmt_effective(cfg.mbdp_self_dp_minor_threshold)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_self_minor", int(cfg.mbdp_self_dp_minor_threshold))
            if changed:
                cfg.mbdp_self_dp_minor_threshold = max(-60, min(0, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_self_dp_minor_threshold")

            PyImGui.text(f"Your stronger DP cleanup starts at ({_fmt_effective(cfg.mbdp_self_dp_major_threshold)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_self_major", int(cfg.mbdp_self_dp_major_threshold))
            if changed:
                cfg.mbdp_self_dp_major_threshold = max(-60, min(0, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_self_dp_major_threshold")

            PyImGui.text(f"Your morale target ({_fmt_effective(cfg.mbdp_self_morale_target_effective)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_self_target", int(cfg.mbdp_self_morale_target_effective))
            if changed:
                cfg.mbdp_self_morale_target_effective = max(-60, min(10, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_self_morale_target_effective")

            PyImGui.text("Minimum useful morale gain for you:")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_self_gain", int(cfg.mbdp_self_min_morale_gain))
            if changed:
                cfg.mbdp_self_min_morale_gain = max(0, min(10, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_self_min_morale_gain")

            PyImGui.text("Party members needed before team items:")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_members", int(cfg.mbdp_party_min_members))
            if changed:
                cfg.mbdp_party_min_members = max(2, min(8, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_min_members")

            PyImGui.text("Minimum time between team item uses (ms):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_interval", int(cfg.mbdp_party_min_interval_ms), width=150.0)
            if changed:
                cfg.mbdp_party_min_interval_ms = max(1000, int(val))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_min_interval_ms")

            PyImGui.text(f"Party morale target ({_fmt_effective(cfg.mbdp_party_target_effective)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_target", int(cfg.mbdp_party_target_effective))
            if changed:
                cfg.mbdp_party_target_effective = max(-60, min(10, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_target_effective")

            PyImGui.text("Minimum party gain before +5 item:")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_gain5", int(cfg.mbdp_party_min_total_gain_5))
            if changed:
                cfg.mbdp_party_min_total_gain_5 = max(0, min(60, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_min_total_gain_5")

            PyImGui.text("Minimum party gain before +10 item:")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_gain10", int(cfg.mbdp_party_min_total_gain_10))
            if changed:
                cfg.mbdp_party_min_total_gain_10 = max(0, min(120, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_min_total_gain_10")

            PyImGui.text(f"Party light DP cleanup starts at ({_fmt_effective(cfg.mbdp_party_light_dp_threshold)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_light", int(cfg.mbdp_party_light_dp_threshold))
            if changed:
                cfg.mbdp_party_light_dp_threshold = max(-60, min(0, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_light_dp_threshold")

            PyImGui.text(f"Party heavy DP cleanup starts at ({_fmt_effective(cfg.mbdp_party_heavy_dp_threshold)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_heavy", int(cfg.mbdp_party_heavy_dp_threshold))
            if changed:
                cfg.mbdp_party_heavy_dp_threshold = max(-60, min(0, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_heavy_dp_threshold")

            PyImGui.text(f"Powerstone emergency starts at ({_fmt_effective(cfg.mbdp_powerstone_dp_threshold)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_powerstone", int(cfg.mbdp_powerstone_dp_threshold))
            if changed:
                cfg.mbdp_powerstone_dp_threshold = max(-60, min(0, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_powerstone_dp_threshold")

            PyImGui.separator()

        # --- Alcohol, Party, and Sweets settings (collapsed dropdown for compactness) ---
        alcohol_section_open = _styled_collapsing_header(
            "Alcohol/Party & Sweets Settings##pycons_settings_alcohol_dropdown",
            bool(cfg.settings_ui_alcohol_open),
            "settings_alcohol",
        )
        if bool(cfg.settings_ui_alcohol_open) != bool(alcohol_section_open):
            cfg.settings_ui_alcohol_open = bool(alcohol_section_open)
            cfg.mark_dirty()
        if alcohol_section_open:
            _section_text("Alcohol", "alcohol")
            PyImGui.text("Alcohol upkeep:")
            _same_line(10)
            if _badge_button("ON" if cfg.alcohol_enabled else "OFF", enabled=bool(cfg.alcohol_enabled), id_suffix="pycons_settings_alcohol_toggle"):
                cfg.alcohol_enabled = not bool(cfg.alcohol_enabled)
                cfg.mark_dirty()
            _show_setting_tooltip("alcohol_enabled")

            changed, v = ui_checkbox("Disable drunk blur##pycons_settings_alc_disable_effect", bool(cfg.alcohol_disable_effect))
            if changed:
                cfg.alcohol_disable_effect = bool(v)
                cfg.mark_dirty()
                _debug(f"Disable drunk blur setting changed to: {cfg.alcohol_disable_effect}", Console.MessageType.Debug)
            _show_setting_tooltip("alcohol_disable_effect")

            changed, v = ui_checkbox("Use in Explorable##pycons_settings_alc_expl", bool(cfg.alcohol_use_explorable))
            if changed:
                cfg.alcohol_use_explorable = bool(v)
                cfg.mark_dirty()
            _show_setting_tooltip("alcohol_use_explorable")

            changed, v = ui_checkbox("Use in Outpost##pycons_settings_alc_outpost", bool(cfg.alcohol_use_outpost))
            if changed:
                cfg.alcohol_use_outpost = bool(v)
                cfg.mark_dirty()
            _show_setting_tooltip("alcohol_use_outpost")

            PyImGui.text("Target drunk level:")
            _same_line(10)
            changed, vv = ui_input_int("##pycons_alcohol_target", int(cfg.alcohol_target_level))
            if changed:
                cfg.alcohol_target_level = int(max(0, min(5, vv)))
                cfg.mark_dirty()
            _show_setting_tooltip("alcohol_target_level")

            PyImGui.text("Preference:")
            _same_line(10)
            changed, pref_idx = ui_combo(
                "##pycons_alc_pref_settings",
                int(cfg.alcohol_preference),
                ALCOHOL_PREFERENCE_OPTIONS,
            )
            if changed:
                cfg.alcohol_preference = int(pref_idx)
                cfg.mark_dirty()
            _show_setting_tooltip("alcohol_preference_mode")

            changed, fast_spending = ui_checkbox(
                "Fast alcohol spending##pycons_settings_alc_fast_spending",
                bool(getattr(cfg, "alcohol_fast_spending", False)),
            )
            if changed:
                cfg.alcohol_fast_spending = bool(fast_spending)
                cfg.mark_dirty()
            _tooltip_if_hovered(_tooltip_text_for("alcohol_fast_spending"))
            _same_line(10)
            PyImGui.text("Interval (ms):")
            _same_line(6)
            changed, fast_interval = ui_input_int_fixed(
                "##pycons_settings_alc_fast_interval",
                int(getattr(cfg, "alcohol_fast_interval_ms", DEFAULT_ALCOHOL_FAST_INTERVAL_MS)),
                width=130.0,
            )
            if changed:
                cfg.alcohol_fast_interval_ms = int(
                    max(MIN_ALCOHOL_FAST_INTERVAL_MS, min(MAX_ALCOHOL_FAST_INTERVAL_MS, int(fast_interval)))
                )
                cfg.mark_dirty()
            _show_setting_tooltip("alcohol_fast_interval_ms")

            PyImGui.separator()

            _section_text("Party Items", "party_items")
            PyImGui.text("Speed (ms):")
            _same_line(10)
            changed, party_interval = ui_input_int_fixed(
                "##pycons_party_item_interval_ms",
                int(getattr(cfg, "party_item_interval_ms", DEFAULT_PARTY_ITEM_INTERVAL_MS)),
                width=120.0,
            )
            if changed:
                cfg.party_item_interval_ms = int(
                    max(MIN_PARTY_ITEM_INTERVAL_MS, min(MAX_PARTY_ITEM_INTERVAL_MS, int(party_interval)))
                )
                cfg.mark_dirty()
            _show_setting_tooltip("party_item_interval_ms")

            PyImGui.separator()

            _section_text("Sweets", "alcohol")
            changed, sweets_fast = ui_checkbox(
                "Fast sweets spending##pycons_settings_sweets_fast_spending",
                bool(getattr(cfg, "sweets_fast_spending", False)),
            )
            if changed:
                cfg.sweets_fast_spending = bool(sweets_fast)
                cfg.mark_dirty()
            _tooltip_if_hovered(_tooltip_text_for("sweets_fast_spending"))
            _same_line(10)
            PyImGui.text("Interval (ms):")
            _same_line(6)
            changed, sweets_interval = ui_input_int_fixed(
                "##pycons_settings_sweets_fast_interval",
                int(getattr(cfg, "sweets_fast_interval_ms", DEFAULT_SWEETS_FAST_INTERVAL_MS)),
                width=130.0,
            )
            if changed:
                cfg.sweets_fast_interval_ms = int(
                    max(MIN_SWEETS_FAST_INTERVAL_MS, min(MAX_SWEETS_FAST_INTERVAL_MS, int(sweets_interval)))
                )
                cfg.mark_dirty()
            _show_setting_tooltip("sweets_fast_interval_ms")

            PyImGui.separator()

        movement_section_open = _styled_collapsing_header(
            "Movement Safety Settings##pycons_settings_movement_safety_dropdown",
            bool(getattr(cfg, "settings_ui_movement_safety_open", False)),
            "settings_movement_safety",
        )
        if bool(getattr(cfg, "settings_ui_movement_safety_open", False)) != bool(movement_section_open):
            cfg.settings_ui_movement_safety_open = bool(movement_section_open)
            cfg.mark_dirty()
        if movement_section_open:
            _section_text("Movement Safety", "settings_movement_safety")
            _draw_movement_status_line()

            PyImGui.text("Movement window (ms):")
            _same_line(10)
            changed, movement_window = ui_input_int_fixed(
                "##pycons_movement_safety_window_ms",
                int(getattr(cfg, "movement_safety_window_ms", DEFAULT_MOVEMENT_SAFETY_WINDOW_MS)),
                width=130.0,
            )
            if changed:
                cfg.movement_safety_window_ms = int(
                    max(MIN_MOVEMENT_SAFETY_WINDOW_MS, min(MAX_MOVEMENT_SAFETY_WINDOW_MS, int(movement_window)))
                )
                cfg.mark_dirty()
            _show_setting_tooltip("movement_safety_window_ms")

            PyImGui.separator()
            PyImGui.text("Presets:")
            _same_line(10)
            if PyImGui.small_button("Safe botting##pycons_movement_safety_preset_safe"):
                _apply_movement_safety_preset("safe_botting")
            _same_line(6)
            if PyImGui.small_button("Title spending##pycons_movement_safety_preset_title"):
                _apply_movement_safety_preset("title_spending")
            _same_line(6)
            if PyImGui.small_button("Off##pycons_movement_safety_preset_off"):
                _apply_movement_safety_preset("off")
            _text_meta_wrapped(
                "Safe botting checks all categories. Title spending checks Alcohol, Party Items, and Sweets while spending stacks."
            )
            PyImGui.separator()

            _draw_movement_requirement_checkbox(
                "movement_require_explorable",
                "Require movement for Explorable consumables",
                "movement_require_explorable",
            )
            _draw_movement_requirement_checkbox(
                "movement_require_summoning",
                "Require movement for Summoning items",
                "movement_require_summoning",
            )
            _draw_movement_requirement_checkbox(
                "movement_require_mbdp",
                "Require movement for Morale/DP items",
                "movement_require_mbdp",
            )
            _draw_movement_requirement_checkbox(
                "movement_require_alcohol",
                "Require movement for Alcohol",
                "movement_require_alcohol",
            )
            _draw_movement_requirement_checkbox(
                "movement_require_party_items",
                "Require movement for Party Items",
                "movement_require_party_items",
            )
            _draw_movement_requirement_checkbox(
                "movement_require_sweets",
                "Require movement for Sweets",
                "movement_require_sweets",
            )

            PyImGui.separator()
            _section_text("Fast-use only", "settings_movement_safety")
            _text_secondary("Use these when only stack spending should wait for movement.")
            _draw_movement_fast_only_checkbox(
                "movement_alcohol_fast_only",
                "Alcohol: fast spending only",
                "movement_alcohol_fast_only",
            )
            _draw_movement_fast_only_checkbox(
                "movement_party_items_speed_only",
                "Party Items: fast speed only",
                "movement_party_items_speed_only",
            )
            PyImGui.text("Party Items movement cutoff (ms):")
            _same_line(10)
            changed, party_fast_threshold = ui_input_int_fixed(
                "##pycons_movement_party_items_fast_threshold_ms",
                int(_movement_party_items_fast_threshold_ms()),
                width=130.0,
            )
            if changed:
                cfg.movement_party_items_fast_threshold_ms = int(
                    max(MIN_PARTY_ITEM_INTERVAL_MS, min(MAX_PARTY_ITEM_INTERVAL_MS, int(party_fast_threshold)))
                )
                cfg.mark_dirty()
            _show_setting_tooltip("movement_party_items_fast_threshold_ms")
            _text_meta_wrapped(
                f"This cutoff value only decides when movement safety treats it as fast spending. Party Items speed is set above in Alcohol/Party & Sweets Settings, currently ({_party_item_interval_ms()} ms)."
            )
            _draw_movement_fast_only_checkbox(
                "movement_sweets_fast_only",
                "Sweets: fast spending only",
                "movement_sweets_fast_only",
            )
            _text_meta_wrapped(_movement_rule_summary_text())
            PyImGui.separator()

        restock_section_open = _styled_collapsing_header(
            "Restock Settings##pycons_settings_restock_dropdown",
            bool(cfg.settings_ui_restock_open),
            "settings_restock",
        )
        if bool(cfg.settings_ui_restock_open) != bool(restock_section_open):
            cfg.settings_ui_restock_open = bool(restock_section_open)
            cfg.mark_dirty()
        if restock_section_open:
            changed, v = ui_checkbox("Auto-restock from Xunlai Vault##pycons_auto_vault_restock", bool(cfg.auto_vault_restock))
            if changed:
                cfg.auto_vault_restock = bool(v)
                cfg.mark_dirty()
            _show_setting_tooltip("auto_vault_restock")

            changed, v = ui_checkbox("Keep target when deselected##pycons_restock_keep_target", bool(cfg.restock_keep_target_on_deselect))
            if changed:
                cfg.restock_keep_target_on_deselect = bool(v)
                cfg.mark_dirty()
            _show_setting_tooltip("restock_keep_target_on_deselect")

            PyImGui.text("How often to check Xunlai restock (ms):")
            _same_line(10)
            changed, v = ui_input_int_fixed("##pycons_restock_interval_ms", int(cfg.restock_interval_ms), width=120.0)
            if changed:
                cfg.restock_interval_ms = int(max(MIN_RESTOCK_INTERVAL_MS, int(v)))
                cfg.mark_dirty()
            _show_setting_tooltip("restock_interval_ms")

            changed, mode_idx = ui_combo("Restock mode##pycons_restock_mode", int(cfg.restock_mode), RESTOCK_MODE_OPTIONS)
            if changed:
                cfg.restock_mode = int(max(RESTOCK_MODE_BALANCED, min(RESTOCK_MODE_DEPOSIT_ONLY, int(mode_idx))))
                cfg.mark_dirty()
            _show_setting_tooltip("restock_mode")

            PyImGui.text("Most items to move at once:")
            _same_line(10)
            changed, cap_val = ui_input_int_fixed("##pycons_restock_move_cap", int(cfg.restock_move_cap_per_cycle), width=120.0)
            if changed:
                cfg.restock_move_cap_per_cycle = int(
                    max(MIN_RESTOCK_MOVE_CAP_PER_CYCLE, min(MAX_RESTOCK_MOVE_CAP_PER_CYCLE, int(cap_val)))
                )
                cfg.mark_dirty()
            _show_setting_tooltip("restock_move_cap_per_cycle")

            PyImGui.separator()
            PyImGui.text_wrapped(
                "Character participation only controls which characters on this account may use Xunlai restock. "
                "Item targets and item restock toggles stay shared across the account."
            )

            changed, scope_mode_idx = ui_combo(
                "Participation mode##pycons_restock_scope_mode",
                int(getattr(cfg, "restock_scope_mode", DEFAULT_RESTOCK_SCOPE_MODE)),
                RESTOCK_SCOPE_OPTIONS,
            )
            if changed:
                cfg.restock_scope_mode = int(_restock_scope_mode_value(scope_mode_idx))
                cfg.mark_dirty()
            _show_setting_tooltip(
                "restock_scope_mode",
                "Controls which characters on this account may use auto-restock from Xunlai. "
                "It does not change the shared restock item settings.",
            )

            changed, new_allow_list = ui_input_text(
                "Allow list (comma-separated)##pycons_restock_allow_list",
                str(getattr(cfg, "restock_allowed_characters", "") or ""),
                MAX_RESTOCK_CHARACTER_LIST_TEXT_LEN,
            )
            if changed:
                cfg.restock_allowed_characters = str(new_allow_list or "")
                cfg.mark_dirty()
            _show_setting_tooltip(
                "restock_allowed_characters",
                "Only used in Allow list mode. Only the listed characters may use auto-restock from Xunlai.",
            )

            changed, new_block_list = ui_input_text(
                "Block list (comma-separated)##pycons_restock_block_list",
                str(getattr(cfg, "restock_blocked_characters", "") or ""),
                MAX_RESTOCK_CHARACTER_LIST_TEXT_LEN,
            )
            if changed:
                cfg.restock_blocked_characters = str(new_block_list or "")
                cfg.mark_dirty()
            _show_setting_tooltip(
                "restock_blocked_characters",
                "Only used in Block list mode. Listed characters cannot use auto-restock from Xunlai.",
            )

            current_character_name = _current_character_name()
            restock_scope_mode = _restock_scope_mode_value()
            add_current_disabled = (restock_scope_mode == RESTOCK_SCOPE_ACCOUNT_WIDE or not current_character_name)
            mode_disabled = _begin_disabled(add_current_disabled)
            if PyImGui.button("Add current character##pycons_restock_add_current_character"):
                if restock_scope_mode == RESTOCK_SCOPE_ALLOW_LIST:
                    updated_value = _restock_add_character_to_raw_list(
                        str(getattr(cfg, "restock_allowed_characters", "") or ""),
                        current_character_name,
                    )
                    if updated_value != str(getattr(cfg, "restock_allowed_characters", "") or ""):
                        cfg.restock_allowed_characters = updated_value
                        cfg.mark_dirty()
                elif restock_scope_mode == RESTOCK_SCOPE_BLOCK_LIST:
                    updated_value = _restock_add_character_to_raw_list(
                        str(getattr(cfg, "restock_blocked_characters", "") or ""),
                        current_character_name,
                    )
                    if updated_value != str(getattr(cfg, "restock_blocked_characters", "") or ""):
                        cfg.restock_blocked_characters = updated_value
                        cfg.mark_dirty()
            _end_disabled(mode_disabled)
            _same_line(10)
            if restock_scope_mode == RESTOCK_SCOPE_ACCOUNT_WIDE:
                PyImGui.text_disabled("Switch to Allow list or Block list mode to store character entries.")
            elif not current_character_name:
                PyImGui.text_disabled("Current character name unavailable.")
            elif restock_scope_mode == RESTOCK_SCOPE_ALLOW_LIST:
                PyImGui.text_disabled(f"Adds '{current_character_name}' to the allow list.")
            else:
                PyImGui.text_disabled(f"Adds '{current_character_name}' to the block list.")

            allowed_now, current_character_display, participation_summary = _restock_current_character_participation()
            _text_secondary(
                f"Current character: {current_character_display} | "
                f"Can use auto-restock: {'Yes' if allowed_now else 'No'}"
            )
            _text_meta(participation_summary)

            PyImGui.text_wrapped("Choose how many of each selected item you want to keep in inventory. Click an item icon to include or exclude it from Xunlai restock.")
            PyImGui.text_wrapped("Main-window ON/OFF controls item use only. Restock uses the icon toggle below.")
            selected_specs = _selected_restock_specs()

            disabled_selected = (int(len(selected_specs)) == 0)
            mode = _begin_disabled(disabled_selected)
            if PyImGui.button("Restock all selected items##pycons_restock_enable_all"):
                changed_any = False
                for key, _spec in selected_specs:
                    if not _restock_item_enabled(key):
                        _set_restock_item_enabled(key, True)
                        changed_any = True
                if changed_any:
                    cfg.mark_dirty()
            _show_setting_tooltip("restock_enable_all_selected")
            _same_line(10)
            if PyImGui.button("Stop restocking all selected items##pycons_restock_disable_all"):
                changed_any = False
                for key, _spec in selected_specs:
                    if _restock_item_enabled(key):
                        _set_restock_item_enabled(key, False)
                        changed_any = True
                if changed_any:
                    cfg.mark_dirty()
            _show_setting_tooltip("restock_disable_all_selected")
            _end_disabled(mode)

            PyImGui.text("Set inventory target for all selected items:")
            _same_line(10)
            changed_bulk, bulk_val = ui_input_int_fixed("##pycons_restock_bulk_target", int(restock_bulk_target[0]), width=90.0)
            if changed_bulk:
                restock_bulk_target[0] = max(0, min(2500, int(bulk_val)))
            _same_line(10)
            if PyImGui.button("Apply to all selected##pycons_restock_apply_all"):
                target = int(max(0, min(2500, int(restock_bulk_target[0]))))
                changed_any = False
                for key, _spec in selected_specs:
                    prev = _restock_target_for_key(key)
                    if int(prev) != int(target):
                        cfg.restock_targets[key] = int(target)
                        changed_any = True
                if changed_any:
                    cfg.mark_dirty()
            _show_setting_tooltip("restock_set_all_selected_target")

            if not selected_specs:
                PyImGui.text_disabled("No selected items. Select consumables first.")
            else:
                selected_specs = sorted(selected_specs, key=lambda pair: str(pair[1].get("label", "")).lower())
                selected_conset_specs = [pair for pair in selected_specs if str(pair[0]) in CONSET_KEYS]
                selected_non_conset_specs = [pair for pair in selected_specs if str(pair[0]) not in CONSET_KEYS]
                _refresh_inventory_cache(False)

                if PyImGui.begin_table("pycons_restock_targets_table", 3):
                    PyImGui.table_setup_column("Item", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_setup_column("In Inventory", PyImGui.TableColumnFlags.WidthFixed, 110.0)
                    PyImGui.table_setup_column("Target", PyImGui.TableColumnFlags.WidthFixed, 110.0)

                    if selected_conset_specs:
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        PyImGui.text("Conset:")
                        PyImGui.table_next_column()
                        PyImGui.text("")
                        PyImGui.table_next_column()
                        PyImGui.text("")

                        for key, spec in selected_conset_specs:
                            _draw_restock_target_item_row(key, spec)

                        if selected_non_conset_specs:
                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            PyImGui.separator()
                            PyImGui.table_next_column()
                            PyImGui.separator()
                            PyImGui.table_next_column()
                            PyImGui.separator()

                    for key, spec in selected_non_conset_specs:
                        _draw_restock_target_item_row(key, spec)

                    PyImGui.end_table()
        tooltip_section_open = _styled_collapsing_header(
            "Tooltip settings##pycons_settings_tooltip_dropdown",
            bool(cfg.settings_ui_tooltip_open),
            "settings_tooltip",
        )
        if bool(cfg.settings_ui_tooltip_open) != bool(tooltip_section_open):
            cfg.settings_ui_tooltip_open = bool(tooltip_section_open)
            cfg.mark_dirty()
        if tooltip_section_open:
            changed, idx = ui_combo("Help visibility##pycons_tip_visibility", int(cfg.tooltip_visibility), TOOLTIP_VISIBILITY_OPTIONS)
            if changed:
                cfg.tooltip_visibility = int(idx)
                cfg.mark_dirty()
            _show_setting_tooltip("tooltip_visibility")

            changed, idx = ui_combo("Help length##pycons_tip_length", int(cfg.tooltip_length), TOOLTIP_LENGTH_OPTIONS)
            if changed:
                cfg.tooltip_length = int(idx)
                cfg.mark_dirty()
            _show_setting_tooltip("tooltip_length")

            changed, v = ui_checkbox("Show 'Why this matters' line##pycons_tip_why", bool(cfg.tooltip_show_why))
            if changed:
                cfg.tooltip_show_why = bool(v)
                cfg.mark_dirty()
            _show_setting_tooltip("tooltip_show_why")
            PyImGui.separator()

        ImGui.End(INI_KEY_SETTINGS)

    def configure():
        pass

    def main():
        global _first_main_call, cfg
        if not _init_window_persistence_once():  # NEW: ensure both window INIs are ready
            return

        # Initialize config on first call (after player is logged in)
        if cfg is None:
            cfg = Config()
            _runtime_sync_from_cfg_full()
            _clear_one_shot_synced_enabled_defaults_if_needed()
        else:
            _maybe_rebind_cfg_from_generic_ini()

        # Refresh inventory on first load to show quantities immediately
        if _first_main_call:
            _first_main_call = False
            try:
                _refresh_inventory_cache(force=True)
            except Exception:
                pass

        if _local_team_flags_refresh_timer.IsStopped() or _local_team_flags_refresh_timer.HasElapsed(1000):
            _local_team_flags_refresh_timer.Start()
            _refresh_local_team_flags_from_ini()

        _drain_scheduled_refresh_queue()
        _update_movement_tracker()

        floating_button = _ensure_floating_ui()
        floating_button.draw(INI_KEY_FLOATING_UI)
        _rt.show_main_window = bool(floating_button.visible)

        _draw_main_window()
        _draw_settings_window()

        _tick_disable_alcohol_effect()

        cfg.save_if_dirty_throttled(750)

        if (
            bool(getattr(cfg, "auto_vault_restock", False))
            and _restock_current_character_allowed()
            and restock_tick_timer.HasElapsed(int(max(MIN_RESTOCK_INTERVAL_MS, int(getattr(cfg, "restock_interval_ms", DEFAULT_RESTOCK_INTERVAL_MS)))))
        ):
            restock_tick_timer.Start()
            _tick_vault_restock()

        if tick_timer.HasElapsed(int(max(MIN_INTERVAL_MS, cfg.interval_ms))):
            tick_timer.Start()
            used = _tick_morale_dp()
            if not used:
                used = _tick_consume()
            if not used and not bool(getattr(cfg, "alcohol_fast_spending", False)):
                _tick_alcohol()

        if bool(getattr(cfg, "alcohol_fast_spending", False)):
            _tick_alcohol()

        if bool(getattr(cfg, "sweets_fast_spending", False)):
            _tick_sweets()

        party_interval_ms = int(
            max(
                MIN_PARTY_ITEM_INTERVAL_MS,
                min(MAX_PARTY_ITEM_INTERVAL_MS, int(getattr(cfg, "party_item_interval_ms", DEFAULT_PARTY_ITEM_INTERVAL_MS))),
            )
        )
        if party_tick_timer.HasElapsed(party_interval_ms):
            party_tick_timer.Start()
            _tick_party_items()

    __all__ = ["main", "configure"]
    _INIT_OK = True

except Exception as e:
    _INIT_OK = False
    _INIT_ERROR = e
    try:
        fn_console_log = globals().get("ConsoleLog")
        console_mod = globals().get("Console")
        msg_type = getattr(getattr(console_mod, "MessageType", None), "Error", None)
        if callable(fn_console_log) and msg_type is not None:
            fn_console_log("Pycons", f"Init failed: {e}", msg_type)
    except Exception:
        pass


