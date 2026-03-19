import hashlib
import os

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

_PYCONS_CONFIG_DIR = os.path.normpath(os.path.join("Widgets", "Config", "Pycons"))
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
    VAULT_RESTOCK_ACTION_MS = 800
    VAULT_RESTOCK_TARGET_QTY = 1
    RESTOCK_MODE_BALANCED = 0
    RESTOCK_MODE_WITHDRAW_ONLY = 1
    RESTOCK_MODE_DEPOSIT_ONLY = 2
    DEFAULT_RESTOCK_MODE = RESTOCK_MODE_BALANCED
    MIN_RESTOCK_MOVE_CAP_PER_CYCLE = 1
    MAX_RESTOCK_MOVE_CAP_PER_CYCLE = 2500
    DEFAULT_RESTOCK_MOVE_CAP_PER_CYCLE = MAX_RESTOCK_MOVE_CAP_PER_CYCLE
    BLOCKED_ACTION_RETENTION_MS = 45000
    BLOCKED_ACTION_MAX_UI_ROWS = 4
    MAIN_WINDOW_DEFAULT_SIZE = (560.0, 560.0)
    MAIN_SELECTED_CHILD_MIN_HEIGHT = 120.0
    MAIN_SELECTED_CHILD_MAX_HEIGHT = 420.0
    EXPERIMENTAL_TEAM_FLAG_SYNC_DEFAULT = True
    EXPERIMENTAL_MAINLOOP_REFRESH_QUEUE_DEFAULT = True

    # Brief cache so multiple "due" items don't rescan bags back-to-back
    INVENTORY_CACHE_MS = 1500
    BROADCAST_KEEPALIVE_MS = 5000
    TEAM_SETTINGS_CACHE_MS = 3000

    # Fallback durations (ms) for items that cannot resolve effect IDs:
    FALLBACK_SHORT_MS = 10 * 60 * 1000
    FALLBACK_MEDIUM_MS = 20 * 60 * 1000
    FALLBACK_LONG_MS = 30 * 60 * 1000
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
    _INI_PATH = "Widgets/Pycons"
    _INI_MAIN_FILE = "Pycons.MainWindow.ini"
    _INI_SETTINGS_FILE = "Pycons.SettingsWindow.ini"

    def _init_window_persistence_once() -> bool:
        """Create/load separate ImGui ini files for main + settings windows (runs once)."""
        global _ini_ready, INI_KEY_MAIN, INI_KEY_SETTINGS
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

        _ini_ready = True
        return True

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
            "text": (0.97, 0.84, 0.74, 1.00),
            "meta": (0.88, 0.72, 0.58, 1.00),
        },
        "restock": {
            "header": (0.21, 0.18, 0.10, 0.82),
            "header_hovered": (0.27, 0.23, 0.13, 0.90),
            "header_active": (0.33, 0.28, 0.16, 0.96),
            "text": (0.95, 0.91, 0.76, 1.00),
            "meta": (0.84, 0.79, 0.61, 1.00),
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
        ):
            try:
                col = getattr(PyImGui.ImGuiCol, col_name, None)
                if col is None:
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
    SETTINGS_CONSUMABLE_CATEGORY_ORDER = ["explorable", "summoning", "mbdp", "outpost", "alcohol"]

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
            "long": "Enable detailed logging for consume checks and MB/DP decisions. Use this to diagnose why an item did or did not trigger. Leave it off in normal play to keep console noise low.",
            "why": "Debug logs are the fastest way to confirm thresholds, eligibility, and trigger ordering.",
        },
        "team_broadcast": {
            "short": "Send this account's item usage events to team accounts.",
            "long": "This account broadcasts consumable usage events to same-party accounts on the same map. Broadcasters coordinate party MB/DP behavior; receiving accounts still apply their own local safety checks before consuming.",
            "why": "Party-wide MB/DP coordination depends on broadcasters; without it, team sync behavior will not run.",
        },
        "team_consume_opt_in": {
            "short": "Allow this account to consume when teammates broadcast.",
            "long": "This account opts in as a receiver for team consume broadcasts. If disabled, incoming broadcasts are ignored. Receiver-side local enabled checks may still block item use if local safety requires it.",
            "why": "This controls whether followers are passive observers or active consumers in team workflows.",
        },
        "advanced_intervals": {
            "short": "Shows per-item timing controls.",
            "long": "Displays advanced per-item interval options so you can tune how frequently each selected item is checked. This is mostly for performance tuning or specialized pacing strategies.",
            "why": "Wrong interval tuning can increase item burn or delay important triggers.",
        },
        "persist_main_runtime_toggles": {
            "short": "Optionally save main-window ON/OFF toggles as defaults.",
            "long": "When OFF, ON/OFF toggles in the main selected-items list are runtime-only and reset from saved defaults on reload. When ON, those same main-window toggles also update the corresponding saved enabled defaults in Settings.",
            "why": "Leave OFF for temporary run-only overrides; turn ON when you want quick main-window changes to persist.",
        },
        "auto_vault_restock": {
            "short": "Auto-restock missing selected consumables from Xunlai Vault.",
            "long": "When enabled, Pycons automatically opens the Xunlai Vault (in outposts) and withdraws missing selected consumables from storage so active upkeep items stay available.",
            "why": "Keeps automation running when inventory stacks run out, without manual chest management.",
        },
        "restock_interval_ms": {
            "short": "How often vault balancing checks run.",
            "long": "Controls how frequently Pycons runs the outpost vault-balancing pass for selected restock targets. Use a slower interval than consume checks to reduce chest churn and blocked actions.",
            "why": "Decoupling restock cadence from consume cadence keeps upkeep responsive without over-polling Xunlai actions.",
        },
        "restock_mode": {
            "short": "Choose whether restock withdraws, deposits, or both.",
            "long": "Balanced keeps inventory near target by withdrawing shortages first, then depositing excess. Withdraw only fills shortages and skips deposits. Deposit only removes excess and skips withdrawals.",
            "why": "Use Balanced for full target maintenance, or one-way modes when you want tighter control over vault traffic.",
        },
        "restock_move_cap_per_cycle": {
            "short": "Maximum quantity moved in one restock action.",
            "long": "Limits how many units a single restock action may withdraw or deposit. Lower values reduce per-action inventory swings; higher values converge to target faster.",
            "why": "Smaller moves can feel smoother during active play; larger moves finish balancing faster.",
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
        "mbdp_enabled": {
            "short": "Master toggle for morale/DP automation.",
            "long": "Turns all morale/death-penalty automation on or off. If OFF, none of the MB/DP settings below do anything, even if configured.",
            "why": "Use this as the global enable/disable for all MB/DP behavior. When enabled, unavailable higher-tier items can fall back to lower-tier valid options.",
        },
        "mbdp_allow_partywide_in_human_parties": {
            "short": "Allow party-wide MB/DP with non-eligible humans present.",
            "long": "If OFF, party-wide MB/DP spending is blocked when there are human party members not considered eligible by your team flags. If ON, party-wide logic can still spend even in mixed human groups.",
            "why": "Use OFF for safety; use ON only for fully coordinated teams.",
        },
        "mbdp_receiver_require_enabled": {
            "short": "Receivers only consume MB/DP items enabled locally.",
            "long": "If ON, a receiver account will only consume a broadcast MB/DP item if that exact item is also enabled locally on that account. If OFF, broadcast can trigger consumption even if local item toggle is OFF.",
            "why": "ON is safer and prevents accidental follower spending.",
        },
        "mbdp_prefer_seal_for_recharge": {
            "short": "Prefer Seal over Pumpkin for self +10 morale upkeep.",
            "long": "When self morale top-up decides to use a +10 self item and both are available, use Seal first instead of Pumpkin.",
            "why": "This is a preference/order setting only.",
        },
        "mbdp_restore_defaults": {
            "short": "Reset MB/DP settings in this section to defaults.",
            "long": "Restores only MB/DP values in this section to balanced defaults. Does not change general, alcohol, or consumable selection settings.",
            "why": "Fast recovery if experimentation made MB/DP behavior unpredictable.",
        },
        "mbdp_self_dp_minor_threshold": {
            "short": "Self DP threshold for lighter cleanup actions.",
            "long": "DP value where lighter self DP cleanup starts. This threshold is for lower-strength self DP recovery items (for example Refined Jelly / Wintergreen Candy Cane). Example: -30 means self cleanup can start when you reach -30 DP.",
            "why": "Closer to 0 triggers earlier/more often; closer to -60 triggers later/less often.",
        },
        "mbdp_self_dp_major_threshold": {
            "short": "Self DP threshold for stronger cleanup actions.",
            "long": "DP value where stronger self DP cleanup can start. This threshold is for stronger self DP recovery items (for example Peppermint Candy Cane). Example: -45 means stronger cleanup can start when you reach -45 DP.",
            "why": "Usually set lower (more negative) than minor so it acts like escalation.",
        },
        "mbdp_self_morale_target_effective": {
            "short": "Desired self effective morale (-60..+10).",
            "long": "Target morale state for yourself on effective scale (-60 to +10). 0 means neutral (no DP, no extra morale). Higher target means more aggressive morale upkeep.",
            "why": "Use this to control how aggressively self morale is topped up.",
        },
        "mbdp_self_min_morale_gain": {
            "short": "Minimum self gain required before morale item use.",
            "long": "Minimum expected gain required before a self morale item is used.",
            "why": "Higher values reduce waste from tiny top-ups.",
        },
        "mbdp_party_min_members": {
            "short": "Minimum eligible members needed for party MB/DP logic.",
            "long": "Minimum number of eligible party members required before party-wide MB/DP logic can fire.",
            "why": "This is a strict gate for party behavior.",
        },
        "mbdp_party_min_interval_ms": {
            "short": "Minimum time between party-wide MB/DP actions.",
            "long": "Minimum time between party MB/DP triggers. Lower means faster reactions and more item use. Higher means slower, more conservative spending.",
            "why": "This strongly affects total item consumption rate.",
        },
        "mbdp_party_target_effective": {
            "short": "Desired party effective morale (-60..+10).",
            "long": "Party morale target used for benefit calculations. +10 means try to keep party near max morale boost.",
            "why": "This affects when party morale options are considered worth using.",
        },
        "mbdp_strict_party_plus10": {
            "short": "Aggressively maintain +10 party morale.",
            "long": "When enabled, party morale decisions ignore minimum total-gain thresholds and will attempt to top up morale whenever any sampled party member is below +10. DP cleanup stages still run first.",
            "why": "Use this when your goal is to keep party morale as close to +10 as possible instead of conserving morale consumables.",
        },
        "mbdp_party_min_total_gain_5": {
            "short": "Minimum summed gain required before +5 party morale item use.",
            "long": "Minimum summed projected value needed before +5 party morale items are allowed.",
            "why": "Lower this to fire +5 items more often.",
        },
        "mbdp_party_min_total_gain_10": {
            "short": "Minimum summed gain required before +10 party morale item use.",
            "long": "Minimum summed projected value needed before +10 party morale items are allowed.",
            "why": "Raise this to make +10 items rarer; lower it to use them sooner.",
        },
        "mbdp_party_light_dp_threshold": {
            "short": "Party DP threshold for light cleanup stage.",
            "long": "DP value for the lighter party DP cleanup stage. This threshold is for lower-strength party DP recovery items (for example Four-Leaf Clover). Example: -15 means this stage can start when members reach -15 DP (plus member-count rules).",
            "why": "Use this as the earlier/softer party DP response stage. If higher tiers are unavailable, Pycons can fall through to this and then to morale options when valid.",
        },
        "mbdp_party_heavy_dp_threshold": {
            "short": "Party DP threshold for heavy cleanup stage.",
            "long": "DP value for the stronger party DP cleanup stage. This threshold is for stronger party DP recovery items (for example Oath of Purity). Example: -30 means this stage can start when members reach -30 DP (plus member-count rules).",
            "why": "Usually set lower (more negative) than light so it acts as escalation. If this tier is unavailable, Pycons can fall back to lower valid tiers.",
        },
        "mbdp_powerstone_dp_threshold": {
            "short": "Emergency DP threshold for Powerstone-level response.",
            "long": "Severe DP value for emergency cleanup stage. Example: -45 means emergency stage can start when members reach -45 DP (plus member-count rules).",
            "why": "Use this as emergency-only escalation for severe DP. If unavailable, Pycons falls through lower DP tiers and then morale tiers instead of stalling.",
        },
        "filter_search": {
            "short": "Filter consumables by name.",
            "long": "Search text filter for consumables lists in the settings window. Works across explorable, summoning, outpost, MB/DP, and alcohol groups.",
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
            "short": "Apply built-in presets or save/load your own settings profiles.",
            "long": "Preset controls let you apply predefined behavior quickly, or store your own configuration in custom slots and reload it later.",
            "why": "Useful when switching between solo, leader, and team-sync playstyles without manually changing many fields.",
        },
        "preset_leader_force_plus10_team": {
            "short": "Leader mode that enforces a team morale target.",
            "long": "ON enables leader-force target enforcement for party morale. Value sets the effective morale target to maintain for eligible party members. In this mode, morale items are only used when eligible members are below that target; if everyone is already at or above target, no morale item is spent. OFF disables this specific leader-force target-enforcement mode only. OFF does not disable MB/DP as a whole, and other MB/DP settings, thresholds, and presets can still run separately. DP cleanup can still be handled by your regular MB/DP DP trigger settings.",
            "why": "Use this when one leader account should enforce a specific team morale target without turning off the rest of MB/DP behavior.",
        },
        "preset_solo_safe": {
            "short": "Safe single-account preset with local-only behavior.",
            "long": "Applies a conservative solo profile: no team broadcast/opt-in, MB/DP enabled with safe defaults, and receiver-local safety protections kept on.",
            "why": "Good baseline when you are not coordinating consumables across accounts.",
        },
        "preset_save_slot": {
            "short": "Save current settings into this slot.",
            "long": "Stores the current profile values and selected/enabled item toggles into this preset slot. You can rename each slot first.",
            "why": "Lets you keep multiple ready-to-use setups and switch quickly.",
        },
        "preset_load_slot": {
            "short": "Load settings from this slot.",
            "long": "Loads all saved values from this preset slot and applies them to the current account.",
            "why": "Fast profile switching for different team roles or farming modes.",
        },
        "preset_set_others_optin": {
            "short": "Set all other same-party accounts to opt in.",
            "long": "Writes team-consume opt-in ON to every other account currently detected in the same party/map instance as this account.",
            "why": "Useful after applying leader presets so followers immediately receive broadcasted consume actions.",
        },
        "preset_set_others_optout": {
            "short": "Set all other same-party accounts to opt out.",
            "long": "Writes team-consume opt-in OFF to every other account currently detected by Pycons account discovery.",
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

    PRESET_SLOT_COUNT = 3
    LEADER_FORCE_PRESET_KEY = "leader_force_target_morale"
    PRESET_BOOL_KEYS = {
        "debug_logging",
        "only_show_available_inventory",
        "only_show_selected_items",
        "show_advanced_intervals",
        "persist_main_runtime_toggles",
        "auto_vault_restock",
        "restock_keep_target_on_deselect",
        "alcohol_enabled",
        "alcohol_disable_effect",
        "alcohol_use_explorable",
        "alcohol_use_outpost",
        "mbdp_enabled",
        "mbdp_allow_partywide_in_human_parties",
        "mbdp_receiver_require_enabled",
        "mbdp_prefer_seal_for_recharge",
        "mbdp_strict_party_plus10",
        "team_broadcast",
        "team_consume_opt_in",
    }
    PRESET_SCALAR_KEYS = [
        "debug_logging",
        "only_show_available_inventory",
        "only_show_selected_items",
        "show_advanced_intervals",
        "persist_main_runtime_toggles",
        "auto_vault_restock",
        "restock_interval_ms",
        "restock_mode",
        "restock_move_cap_per_cycle",
        "restock_keep_target_on_deselect",
        "alcohol_enabled",
        "alcohol_disable_effect",
        "alcohol_target_level",
        "alcohol_use_explorable",
        "alcohol_use_outpost",
        "alcohol_preference",
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

    def _preset_slot_default_name(slot_idx: int) -> str:
        return f"Preset {int(slot_idx)}"

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

    def _save_custom_preset_slot(slot_idx: int):
        slot = max(1, min(PRESET_SLOT_COUNT, int(slot_idx)))
        ini_handler = _get_ini_handler()
        prefix = f"preset_slot_{slot}_"
        ini_handler.write_key(INI_SECTION, f"{prefix}saved", "True")
        for key in PRESET_SCALAR_KEYS:
            try:
                ini_handler.write_key(INI_SECTION, f"{prefix}{key}", getattr(cfg, key))
            except Exception:
                pass
        for item in ALL_CONSUMABLES:
            k = str(item.get("key", "") or "")
            if not k:
                continue
            ini_handler.write_key(INI_SECTION, f"{prefix}selected_{k}", str(bool(cfg.selected.get(k, False))))
            ini_handler.write_key(INI_SECTION, f"{prefix}enabled_{k}", str(bool(cfg.enabled.get(k, False))))
            ini_handler.write_key(INI_SECTION, f"{prefix}restock_target_{k}", str(int(max(0, min(2500, int(cfg.restock_targets.get(k, VAULT_RESTOCK_TARGET_QTY) or 0))))))
        for item in ALCOHOL_ITEMS:
            k = str(item.get("key", "") or "")
            if not k:
                continue
            ini_handler.write_key(INI_SECTION, f"{prefix}alcohol_selected_{k}", str(bool(cfg.alcohol_selected.get(k, False))))
            ini_handler.write_key(INI_SECTION, f"{prefix}alcohol_enabled_{k}", str(bool(cfg.alcohol_enabled_items.get(k, False))))
            ini_handler.write_key(INI_SECTION, f"{prefix}restock_target_{k}", str(int(max(0, min(2500, int(cfg.restock_targets.get(k, VAULT_RESTOCK_TARGET_QTY) or 0))))))
        _log(f"Saved custom preset slot {slot}.", Console.MessageType.Info)

    def _load_custom_preset_slot(slot_idx: int) -> bool:
        global _last_mbdp_party_ms
        slot = max(1, min(PRESET_SLOT_COUNT, int(slot_idx)))
        ini_handler = _get_ini_handler()
        prefix = f"preset_slot_{slot}_"
        if not ini_handler.read_bool(INI_SECTION, f"{prefix}saved", False):
            _log(f"Preset slot {slot} is empty.", Console.MessageType.Warning)
            return False

        for key in PRESET_SCALAR_KEYS:
            try:
                if key in PRESET_BOOL_KEYS:
                    setattr(cfg, key, bool(ini_handler.read_bool(INI_SECTION, f"{prefix}{key}", bool(getattr(cfg, key)))))
                else:
                    setattr(cfg, key, int(ini_handler.read_int(INI_SECTION, f"{prefix}{key}", int(getattr(cfg, key)))))
            except Exception:
                pass
        cfg.restock_interval_ms = max(MIN_RESTOCK_INTERVAL_MS, int(getattr(cfg, "restock_interval_ms", DEFAULT_RESTOCK_INTERVAL_MS)))
        cfg.restock_mode = max(RESTOCK_MODE_BALANCED, min(RESTOCK_MODE_DEPOSIT_ONLY, int(getattr(cfg, "restock_mode", DEFAULT_RESTOCK_MODE))))
        cfg.restock_move_cap_per_cycle = max(
            MIN_RESTOCK_MOVE_CAP_PER_CYCLE,
            min(MAX_RESTOCK_MOVE_CAP_PER_CYCLE, int(getattr(cfg, "restock_move_cap_per_cycle", DEFAULT_RESTOCK_MOVE_CAP_PER_CYCLE))),
        )

        for item in ALL_CONSUMABLES:
            k = str(item.get("key", "") or "")
            if not k:
                continue
            cfg.selected[k] = bool(ini_handler.read_bool(INI_SECTION, f"{prefix}selected_{k}", bool(cfg.selected.get(k, False))))
            cfg.enabled[k] = bool(ini_handler.read_bool(INI_SECTION, f"{prefix}enabled_{k}", bool(cfg.enabled.get(k, False))))
            cfg.restock_targets[k] = max(0, min(2500, int(ini_handler.read_int(INI_SECTION, f"{prefix}restock_target_{k}", int(cfg.restock_targets.get(k, VAULT_RESTOCK_TARGET_QTY) or 0)))))
        for item in ALCOHOL_ITEMS:
            k = str(item.get("key", "") or "")
            if not k:
                continue
            cfg.alcohol_selected[k] = bool(ini_handler.read_bool(INI_SECTION, f"{prefix}alcohol_selected_{k}", bool(cfg.alcohol_selected.get(k, False))))
            cfg.alcohol_enabled_items[k] = bool(ini_handler.read_bool(INI_SECTION, f"{prefix}alcohol_enabled_{k}", bool(cfg.alcohol_enabled_items.get(k, False))))
            cfg.restock_targets[k] = max(0, min(2500, int(ini_handler.read_int(INI_SECTION, f"{prefix}restock_target_{k}", int(cfg.restock_targets.get(k, VAULT_RESTOCK_TARGET_QTY) or 0)))))

        _runtime_sync_from_cfg_full()

        _last_mbdp_party_ms = 0
        cfg.last_applied_preset = str(cfg.preset_slot_names.get(slot, _preset_slot_default_name(slot)))
        cfg.mark_dirty()
        _log(f"Loaded custom preset slot {slot}.", Console.MessageType.Info)
        return True

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
                _log("Could not set opt-in for others: local account email unavailable.", Console.MessageType.Warning)
                return
            accounts, my_party_id, party_rows_count = _resolve_same_party_accounts_for_opt_toggle(self_email)
            updated, toggled_names = _set_team_opt_in_for_accounts(accounts, self_email, True)
            if updated == 0:
                cfg.last_party_opt_toggle_summary = "Opt-in ON: none"
                _log(
                    f"Set team consume opt-in ON for 0 other party account(s). "
                    f"Detected accounts={len(accounts)} my_party_id={my_party_id} "
                    f"party_rows={party_rows_count}. No non-party accounts were modified.",
                    Console.MessageType.Warning
                )
            else:
                unique_names = sorted(set(toggled_names), key=lambda s: s.lower())
                names_str = ", ".join(unique_names) if unique_names else f"{updated} account(s)"
                cfg.last_party_opt_toggle_summary = f"Opt-in ON: {names_str}"
                _log(f"Set team consume opt-in ON for {updated} other party account(s).", Console.MessageType.Info)
            cfg.mark_dirty()
        except Exception as e:
            _debug(f"Failed setting opt-in for other party accounts: {e}", Console.MessageType.Warning)

    def _set_other_party_accounts_opt_out():
        try:
            self_email = str(Player.GetAccountEmail() or "")
            if not self_email:
                _log("Could not set opt-out for others: local account email unavailable.", Console.MessageType.Warning)
                return
            accounts, _my_party_id_unused, _party_rows_count_unused = _resolve_same_party_accounts_for_opt_toggle(self_email)
            updated, toggled_names = _set_team_opt_in_for_accounts(accounts, self_email, False)
            if updated == 0:
                cfg.last_party_opt_toggle_summary = "Opt-in OFF: none"
                _log("Set team consume opt-in OFF for 0 other party account(s). No non-party accounts were modified.", Console.MessageType.Warning)
            else:
                unique_names = sorted(set(toggled_names), key=lambda s: s.lower())
                names_str = ", ".join(unique_names) if unique_names else f"{updated} account(s)"
                cfg.last_party_opt_toggle_summary = f"Opt-in OFF: {names_str}"
                _log(f"Set team consume opt-in OFF for {updated} other party account(s).", Console.MessageType.Info)
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
        {"key": "chocolate_bunny", "label": "Chocolate Bunny", "model_id": int(_model_id_value("Chocolate_Bunny", 0)), "skills": ["Sugar_Jolt_(long)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_LONG_MS},
        {"key": "creme_brulee", "label": "Crème Brûlée", "model_id": int(_model_id_value("Creme_Brulee", 0)), "skills": ["Sugar_Jolt_(long)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_LONG_MS},
        {"key": "fruitcake", "label": "Fruitcake", "model_id": int(_model_id_value("Fruitcake", 0)), "skills": ["Sugar_Rush_(medium)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_MEDIUM_MS},
        {"key": "jar_of_honey", "label": "Jar of Honey", "model_id": int(_model_id_value("Jar_Of_Honey", 0)), "skills": ["Sugar_Rush_(long)"], "use_where": "outpost", "require_effect_id": False, "fallback_duration_ms": FALLBACK_LONG_MS},
        {"key": "red_bean_cake", "label": "Red Bean Cake", "model_id": int(_model_id_value("Red_Bean_Cake", 0)), "skills": ["Sugar_Rush_(medium)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_MEDIUM_MS},
        {"key": "sugary_blue_drink", "label": "Sugary Blue Drink", "model_id": int(_model_id_value("Sugary_Blue_Drink", 0)), "skills": ["Sugar_Jolt_(short)"], "use_where": "outpost", "require_effect_id": False, "fallback_duration_ms": FALLBACK_SHORT_MS},
    ]

    SUMMONING_ITEMS = [c for c in CONSUMABLES if str(c.get("use_where", "")).lower() == "summoning"]

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

    def _consumable_tooltip_text(key: str) -> str:
        tooltip = str(CONSUMABLE_TOOLTIPS.get(str(key or ""), "") or "").strip()
        if tooltip:
            return tooltip
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
            self.restock_interval_ms = max(MIN_RESTOCK_INTERVAL_MS, int(ini_handler.read_int(INI_SECTION, "restock_interval_ms", DEFAULT_RESTOCK_INTERVAL_MS)))
            self.restock_mode = max(
                RESTOCK_MODE_BALANCED,
                min(RESTOCK_MODE_DEPOSIT_ONLY, int(ini_handler.read_int(INI_SECTION, "restock_mode", DEFAULT_RESTOCK_MODE))),
            )
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
            self.preset_slot_names = {}
            for i in range(1, PRESET_SLOT_COUNT + 1):
                default_name = _preset_slot_default_name(i)
                name = str(ini_handler.read_key(INI_SECTION, f"preset_slot_{i}_name", default_name) or default_name).strip()
                self.preset_slot_names[i] = name if name else default_name

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
            self.alcohol_target_level = max(0, min(5, int(ini_handler.read_int(INI_SECTION, "alcohol_target_level", 3))))

            self.alcohol_use_explorable = ini_handler.read_bool(INI_SECTION, "alcohol_use_explorable", True)
            self.alcohol_use_outpost = ini_handler.read_bool(INI_SECTION, "alcohol_use_outpost", True)

            # 0=smooth, 1=strong-first, 2=weak-first
            self.alcohol_preference = int(ini_handler.read_int(INI_SECTION, "alcohol_preference", 0))
            if self.alcohol_preference not in (0, 1, 2):
                self.alcohol_preference = 0

            self.selected = {}
            self.enabled = {}
            for c in ALL_CONSUMABLES:
                k = c["key"]
                self.selected[k] = ini_handler.read_bool(INI_SECTION, f"selected_{k}", False)
                self.enabled[k] = ini_handler.read_bool(INI_SECTION, f"enabled_{k}", False)
            self.restock_targets = {}
            for c in ALL_CONSUMABLES:
                k = c["key"]
                default_target = int(VAULT_RESTOCK_TARGET_QTY) if bool(self.selected.get(k, False)) and bool(self.enabled.get(k, False)) else 0
                raw_target = int(ini_handler.read_int(INI_SECTION, f"restock_target_{k}", default_target))
                self.restock_targets[k] = max(0, min(2500, raw_target))

            # Settings-window consumables group open/closed state
            self.settings_explorable_open = ini_handler.read_bool(INI_SECTION, "settings_explorable_open", False)
            self.settings_summoning_open = ini_handler.read_bool(INI_SECTION, "settings_summoning_open", False)
            self.settings_outpost_open = ini_handler.read_bool(INI_SECTION, "settings_outpost_open", False)
            self.settings_mbdp_open = ini_handler.read_bool(INI_SECTION, "settings_mbdp_open", False)
            self.settings_alcohol_open = ini_handler.read_bool(INI_SECTION, "settings_alcohol_open", False)
            # Settings-window top-level section open/closed state
            self.settings_ui_tooltip_open = ini_handler.read_bool(INI_SECTION, "settings_ui_tooltip_open", False)
            self.settings_ui_alcohol_open = ini_handler.read_bool(INI_SECTION, "settings_ui_alcohol_open", False)
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
                default_target = int(VAULT_RESTOCK_TARGET_QTY) if bool(self.alcohol_selected.get(k, False)) and bool(self.alcohol_enabled_items.get(k, False)) else 0
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

        def mark_dirty(self):
            self._dirty = True

        def save_if_dirty_throttled(self, every_ms: int = 750):
            if not self._dirty:
                return
            if not (self._save_timer.IsStopped() or self._save_timer.HasElapsed(int(every_ms))):
                return
            self._save_timer.Start()

            ini_handler = _get_ini_handler()
            ini_handler.write_key(INI_SECTION, "debug_logging", str(bool(self.debug_logging)))
            ini_handler.write_key(INI_SECTION, "interval_ms", str(int(self.interval_ms)))
            ini_handler.write_key(INI_SECTION, "restock_interval_ms", str(int(max(MIN_RESTOCK_INTERVAL_MS, int(self.restock_interval_ms)))))
            ini_handler.write_key(
                INI_SECTION,
                "restock_mode",
                str(int(max(RESTOCK_MODE_BALANCED, min(RESTOCK_MODE_DEPOSIT_ONLY, int(self.restock_mode))))),
            )
            ini_handler.write_key(
                INI_SECTION,
                "restock_move_cap_per_cycle",
                str(int(max(MIN_RESTOCK_MOVE_CAP_PER_CYCLE, min(MAX_RESTOCK_MOVE_CAP_PER_CYCLE, int(self.restock_move_cap_per_cycle))))),
            )
            ini_handler.write_key(INI_SECTION, "show_selected_list", str(bool(self.show_selected_list)))
            ini_handler.write_key(INI_SECTION, "only_show_available_inventory", str(bool(self.only_show_available_inventory)))
            ini_handler.write_key(INI_SECTION, "only_show_selected_items", str(bool(self.only_show_selected_items)))
            ini_handler.write_key(INI_SECTION, "auto_vault_restock", str(bool(self.auto_vault_restock)))
            ini_handler.write_key(INI_SECTION, "restock_keep_target_on_deselect", str(bool(self.restock_keep_target_on_deselect)))
            ini_handler.write_key(INI_SECTION, "tooltip_visibility", str(int(self.tooltip_visibility)))
            ini_handler.write_key(INI_SECTION, "tooltip_length", str(int(self.tooltip_length)))
            ini_handler.write_key(INI_SECTION, "tooltip_show_why", str(bool(self.tooltip_show_why)))
            ini_handler.write_key(INI_SECTION, "last_applied_preset", str(self.last_applied_preset))
            ini_handler.write_key(INI_SECTION, "last_party_opt_toggle_summary", str(self.last_party_opt_toggle_summary))
            for i in range(1, PRESET_SLOT_COUNT + 1):
                ini_handler.write_key(INI_SECTION, f"preset_slot_{i}_name", str(self.preset_slot_names.get(i, _preset_slot_default_name(i))))

            ini_handler.write_key(INI_SECTION, "show_advanced_intervals", str(bool(self.show_advanced_intervals)))
            ini_handler.write_key(INI_SECTION, "persist_main_runtime_toggles", str(bool(self.persist_main_runtime_toggles)))
            for k, v in self.min_interval_ms.items():
                ini_handler.write_key(INI_SECTION, f"min_interval_{k}", str(int(max(0, int(v)))))

            ini_handler.write_key(INI_SECTION, "alcohol_enabled", str(bool(self.alcohol_enabled)))
            ini_handler.write_key(INI_SECTION, "alcohol_disable_effect", str(bool(self.alcohol_disable_effect)))
            ini_handler.write_key(INI_SECTION, "alcohol_target_level", str(int(self.alcohol_target_level)))
            ini_handler.write_key(INI_SECTION, "alcohol_use_explorable", str(bool(self.alcohol_use_explorable)))
            ini_handler.write_key(INI_SECTION, "alcohol_use_outpost", str(bool(self.alcohol_use_outpost)))
            ini_handler.write_key(INI_SECTION, "alcohol_preference", str(int(self.alcohol_preference)))
            ini_handler.write_key(INI_SECTION, "mbdp_enabled", str(bool(self.mbdp_enabled)))
            ini_handler.write_key(INI_SECTION, "mbdp_allow_partywide_in_human_parties", str(bool(self.mbdp_allow_partywide_in_human_parties)))
            ini_handler.write_key(INI_SECTION, "mbdp_receiver_require_enabled", str(bool(self.mbdp_receiver_require_enabled)))
            ini_handler.write_key(INI_SECTION, "mbdp_self_dp_minor_threshold", str(int(self.mbdp_self_dp_minor_threshold)))
            ini_handler.write_key(INI_SECTION, "mbdp_self_dp_major_threshold", str(int(self.mbdp_self_dp_major_threshold)))
            ini_handler.write_key(INI_SECTION, "mbdp_self_morale_target_effective", str(int(self.mbdp_self_morale_target_effective)))
            ini_handler.write_key(INI_SECTION, "mbdp_self_min_morale_gain", str(int(self.mbdp_self_min_morale_gain)))
            ini_handler.write_key(INI_SECTION, "mbdp_party_target_effective", str(int(self.mbdp_party_target_effective)))
            ini_handler.write_key(INI_SECTION, "mbdp_strict_party_plus10", str(bool(self.mbdp_strict_party_plus10)))
            ini_handler.write_key(INI_SECTION, "mbdp_party_min_members", str(int(self.mbdp_party_min_members)))
            ini_handler.write_key(INI_SECTION, "mbdp_party_min_interval_ms", str(int(self.mbdp_party_min_interval_ms)))
            ini_handler.write_key(INI_SECTION, "mbdp_party_min_total_gain_5", str(int(self.mbdp_party_min_total_gain_5)))
            ini_handler.write_key(INI_SECTION, "mbdp_party_min_total_gain_10", str(int(self.mbdp_party_min_total_gain_10)))
            ini_handler.write_key(INI_SECTION, "mbdp_party_light_dp_threshold", str(int(self.mbdp_party_light_dp_threshold)))
            ini_handler.write_key(INI_SECTION, "mbdp_party_heavy_dp_threshold", str(int(self.mbdp_party_heavy_dp_threshold)))
            ini_handler.write_key(INI_SECTION, "mbdp_powerstone_dp_threshold", str(int(self.mbdp_powerstone_dp_threshold)))
            ini_handler.write_key(INI_SECTION, "mbdp_prefer_seal_for_recharge", str(bool(self.mbdp_prefer_seal_for_recharge)))
            ini_handler.write_key(INI_SECTION, "force_team_morale_value", str(int(self.force_team_morale_value)))
            ini_handler.write_key(INI_SECTION, "settings_explorable_open", str(bool(self.settings_explorable_open)))
            ini_handler.write_key(INI_SECTION, "settings_summoning_open", str(bool(self.settings_summoning_open)))
            ini_handler.write_key(INI_SECTION, "settings_outpost_open", str(bool(self.settings_outpost_open)))
            ini_handler.write_key(INI_SECTION, "settings_mbdp_open", str(bool(self.settings_mbdp_open)))
            ini_handler.write_key(INI_SECTION, "settings_alcohol_open", str(bool(self.settings_alcohol_open)))
            ini_handler.write_key(INI_SECTION, "settings_ui_tooltip_open", str(bool(self.settings_ui_tooltip_open)))
            ini_handler.write_key(INI_SECTION, "settings_ui_alcohol_open", str(bool(self.settings_ui_alcohol_open)))
            ini_handler.write_key(INI_SECTION, "settings_ui_mbdp_open", str(bool(self.settings_ui_mbdp_open)))
            ini_handler.write_key(INI_SECTION, "settings_ui_presets_open", str(bool(self.settings_ui_presets_open)))
            ini_handler.write_key(INI_SECTION, "settings_ui_restock_open", str(bool(self.settings_ui_restock_open)))
            ini_handler.write_key(INI_SECTION, "experimental_team_flag_sync", str(bool(self.experimental_team_flag_sync)))
            ini_handler.write_key(INI_SECTION, "experimental_mainloop_refresh_queue", str(bool(self.experimental_mainloop_refresh_queue)))

            for k, v in self.alcohol_selected.items():
                ini_handler.write_key(INI_SECTION, f"alcohol_selected_{k}", str(bool(v)))
            for k, v in self.alcohol_enabled_items.items():
                ini_handler.write_key(INI_SECTION, f"alcohol_enabled_{k}", str(bool(v)))
            for c in ALL_CONSUMABLES:
                k = str(c.get("key", "") or "")
                if k:
                    ini_handler.write_key(INI_SECTION, f"restock_target_{k}", str(int(max(0, min(2500, int(self.restock_targets.get(k, VAULT_RESTOCK_TARGET_QTY) or 0))))))
            for a in ALCOHOL_ITEMS:
                k = str(a.get("key", "") or "")
                if k:
                    ini_handler.write_key(INI_SECTION, f"restock_target_{k}", str(int(max(0, min(2500, int(self.restock_targets.get(k, VAULT_RESTOCK_TARGET_QTY) or 0))))))

            # Team / multibox settings
            # team_broadcast: When enabled, broadcasts item usage to other accounts
            # team_consume_opt_in: When enabled (on followers), consumes items when broadcasts are received
            # Legacy behavior keeps team_consume_opt_in saved by immediate settings writes.
            # Experimental team-flag sync writes both flags here to reduce refresh races.
            ini_handler.write_key(INI_SECTION, "team_broadcast", str(bool(self.team_broadcast)))
            if bool(getattr(self, "experimental_team_flag_sync", EXPERIMENTAL_TEAM_FLAG_SYNC_DEFAULT)):
                ini_handler.write_key(INI_SECTION, "team_consume_opt_in", str(bool(self.team_consume_opt_in)))

            for k, v in self.selected.items():
                ini_handler.write_key(INI_SECTION, f"selected_{k}", str(bool(v)))
            for k, v in self.enabled.items():
                ini_handler.write_key(INI_SECTION, f"enabled_{k}", str(bool(v)))

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
        return [k for k in cfg.enabled.keys() if bool(cfg.selected.get(k, False)) and _runtime_regular_enabled(k)]

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

    def _alcohol_precheck():
        """
        Stable gate ordering for alcohol upkeep.
        Returns (ok, target, pool_keys, in_explorable, now_ms, cur_level).
        """
        if not bool(cfg.alcohol_enabled):
            return False, 0, [], False, 0, 0

        target = int(cfg.alcohol_target_level)
        if target <= 0:
            return False, target, [], False, 0, 0

        if not bool(cfg.alcohol_use_explorable) and not bool(cfg.alcohol_use_outpost):
            return False, target, [], False, 0, 0

        if not Routines.Checks.Map.MapValid():
            return False, target, [], False, 0, 0

        if _should_block_consumption():
            return False, target, [], False, 0, 0

        if not (aftercast_timer.IsStopped() or aftercast_timer.HasElapsed(int(AFTERCAST_MS))):
            return False, target, [], False, 0, 0

        pool_keys = _alcohol_pool_keys()
        if not pool_keys:
            return False, target, pool_keys, False, 0, 0

        in_explorable = bool(_in_explorable())
        if not _alcohol_allowed_here(in_explorable):
            return False, target, pool_keys, in_explorable, 0, 0

        now = _now_ms()
        cur_level = _alcohol_current_level(now)
        if cur_level >= target:
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
        if use_where == "outpost":
            return not in_explorable
        return in_explorable

    def _alcohol_allowed_here(in_explorable: bool) -> bool:
        if bool(in_explorable):
            return bool(cfg.alcohol_use_explorable)
        return bool(cfg.alcohol_use_outpost)

    def _is_summoning_spec(spec: dict) -> bool:
        return str(spec.get("use_where", "") or "").strip().lower() == "summoning"

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
                    if qty > int(best_qty_by_model.get(mid, -1)):
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
                        if qty > int(best_qty_by_model.get(mid, -1)):
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
        best_qty = -1
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
                if qty > best_qty:
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

    def _apply_restock_target_on_select(key: str):
        key = str(key or "")
        if not key:
            return
        if _restock_target_for_key(key) <= 0:
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
        return bool(cfg.selected.get(key, False)) and bool(_runtime_regular_enabled(key))

    def _restock_alcohol_enabled(key: str) -> bool:
        return bool(cfg.alcohol_selected.get(key, False)) and bool(_runtime_alcohol_enabled(key))

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
            try:
                inv.OpenXunlaiWindow()
                _debug("Vault restock: opening Xunlai Vault.")
            except Exception as e:
                _debug(f"Vault restock: failed opening Xunlai Vault: {e}", Console.MessageType.Warning)
            restock_timer.Start()
            return True

        shortage_first = [c for c in candidates if int(c[5]) > 0]
        excess_second = [c for c in candidates if int(c[5]) < 0]
        restock_mode = int(_restock_mode_value())
        if restock_mode == int(RESTOCK_MODE_WITHDRAW_ONLY):
            ordered_candidates = shortage_first
        elif restock_mode == int(RESTOCK_MODE_DEPOSIT_ONLY):
            ordered_candidates = excess_second
        else:
            ordered_candidates = shortage_first + excess_second
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

    def _cooldown_for_key(key: str) -> int:
        v = int(cfg.min_interval_ms.get(key, 0) or 0)
        if v <= 0:
            return int(DEFAULT_INTERNAL_COOLDOWN_MS)
        return int(max(250, v))

    def _normalize_name(name: str) -> str:
        return " ".join((name or "").strip().lower().split())

    def _acc_email(acc) -> str:
        return str(getattr(acc, "AccountEmail", "") or "")

    def _acc_name(acc) -> str:
        try:
            return str(getattr(getattr(acc, "AgentData", None), "CharacterName", "") or "")
        except Exception:
            return ""

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

            if not _allowed_here(spec, in_explorable):
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
            cd = _cooldown_for_key(key)
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
                if not _is_summoning_spec(spec):
                    try:
                        _broadcast_use(model_id, 1, effect_id)
                    except Exception:
                        pass
                # Force refresh inventory cache to show accurate count after consumption
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
        if not (t.IsStopped() or t.HasElapsed(2500)):
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

    def _text_secondary(text: str):
        _text_with_color(str(text), (0.82, 0.84, 0.88, 1.00))

    def _text_meta(text: str):
        _text_with_color(str(text), (0.72, 0.75, 0.80, 1.00))

    def _section_text(text: str, section_key: str, secondary: bool = False):
        palette = _section_palette(section_key)
        color_key = "meta" if bool(secondary) else "text"
        _text_with_color(str(text), palette[color_key])

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
            "Runtime-only toggle (not saved). Use Settings to set persistent defaults."
            if not _main_runtime_persist_enabled()
            else "Runtime toggle is also saved as the persistent enabled default."
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

    def _selected_list_child_height(
        selected_explorable_conset: list,
        selected_explorable_other: list,
        selected_summoning: list,
        selected_outpost: list,
        selected_mbdp: list,
        selected_alcohol: list,
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

    def _disable_pycons_widget():
        try:
            from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
            get_widget_handler().disable_widget(MODULE_NAME)
        except Exception as e:
            _debug(f"Failed to disable Pycons widget: {e}", Console.MessageType.Warning)

    # -------------------------
    # Main Window
    # -------------------------
    def _draw_main_window():
        if cfg is None:
            return  # Config not yet loaded
        try:
            PyImGui.set_next_window_size(MAIN_WINDOW_DEFAULT_SIZE, PyImGui.ImGuiCond.FirstUseEver)
        except Exception:
            pass

        window_expanded, window_open = _begin_persistent_window_with_close_state(INI_KEY_MAIN, BOT_NAME)
        if not window_open:
            ImGui.End(INI_KEY_MAIN)
            show_settings[0] = False
            _disable_pycons_widget()
            return
        if not window_expanded:
            ImGui.End(INI_KEY_MAIN)
            return

        if PyImGui.button("Settings##pycons_settings"):
            show_settings[0] = not show_settings[0]

        PyImGui.separator()

        PyImGui.text("Consume interval (ms):")
        _same_line(10)
        changed, val = ui_input_int("##pycons_interval", int(cfg.interval_ms))
        if changed:
            cfg.interval_ms = int(max(MIN_INTERVAL_MS, val))
            cfg.mark_dirty()

        _draw_restock_status_line()
        _draw_blocked_actions_section()

        PyImGui.separator()

        # --- Alcohol settings (collapsed dropdown for compactness) ---
        if _styled_collapsing_header("Alcohol settings##pycons_alcohol_dropdown", False, "alcohol"):
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
            "general",
        )

        if request_expand_selected[0]:
            request_expand_selected[0] = False
        if request_collapse_selected[0]:
            request_collapse_selected[0] = False

        if expanded != bool(cfg.show_selected_list):
            cfg.show_selected_list = bool(expanded)
            cfg.mark_dirty()

        if expanded:
            _text_secondary("Selected in Settings -> shown here.")
            if _main_runtime_persist_enabled():
                _text_secondary("ON/OFF here -> active now and saved as the enabled default.")
            else:
                _text_secondary("ON/OFF here -> active now only. Enable persistence in Settings to save defaults.")
            if PyImGui.button(
                "Enable all (runtime + save)##pycons_main_select_all"
                if _main_runtime_persist_enabled()
                else "Enable all (runtime)##pycons_main_select_all"
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
                "Disable all (runtime + save)##pycons_main_clear_all"
                if _main_runtime_persist_enabled()
                else "Disable all (runtime)##pycons_main_clear_all"
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
            # Keep the main selected-items panel stable even when inventory hits 0.
            # Availability filtering remains in the Settings browser.

            any_selected = bool(selected_explorable_conset or selected_explorable_other or selected_summoning or selected_outpost or selected_mbdp or selected_alcohol)
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
        label = str(spec.get("label", key) or key)
        current_target = _restock_target_for_key(key)

        PyImGui.table_next_row()
        PyImGui.table_next_column()
        drew_icon = _draw_static_consumable_icon(
            key,
            label,
            "pycons_restock_target",
            icon_size=18.0,
            highlight_box=True,
        )
        if drew_icon:
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
            "explorable",
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
            "mbdp",
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
            "outpost",
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
            "summoning",
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
            "alcohol",
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

    def _draw_settings_window():
        if cfg is None:
            return  # Config not yet loaded
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
                _log(f"Team opt-in setting changed to: {bool(v)} (saved to {_get_ini_path()})", Console.MessageType.Info)
            except Exception as e:
                _debug(f"Failed to write team_consume_opt_in: {e}", Console.MessageType.Warning)
        _show_setting_tooltip("team_consume_opt_in")

        changed, v = ui_checkbox("Advanced intervals##pycons_advint", bool(cfg.show_advanced_intervals))
        if changed:
            cfg.show_advanced_intervals = bool(v)
            cfg.mark_dirty()
        _show_setting_tooltip("advanced_intervals")

        changed, v = ui_checkbox(
            "Persist main-window toggles to enabled defaults##pycons_persist_main_runtime_toggles",
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
        PyImGui.text(f"Last party opt toggle: {str(cfg.last_party_opt_toggle_summary or 'None')}")

        PyImGui.separator()
        tooltip_section_open = _styled_collapsing_header(
            "Tooltip settings##pycons_settings_tooltip_dropdown",
            bool(cfg.settings_ui_tooltip_open),
            "general",
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

        # --- Alcohol settings (collapsed dropdown for compactness) ---
        alcohol_section_open = _styled_collapsing_header(
            "Alcohol settings##pycons_settings_alcohol_dropdown",
            bool(cfg.settings_ui_alcohol_open),
            "alcohol",
        )
        if bool(cfg.settings_ui_alcohol_open) != bool(alcohol_section_open):
            cfg.settings_ui_alcohol_open = bool(alcohol_section_open)
            cfg.mark_dirty()
        if alcohol_section_open:
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

            PyImGui.separator()

        mbdp_section_open = _styled_collapsing_header(
            "Morale Boost & Death Penalty settings##pycons_settings_mbdp_dropdown",
            bool(cfg.settings_ui_mbdp_open),
            "mbdp",
        )
        if bool(cfg.settings_ui_mbdp_open) != bool(mbdp_section_open):
            cfg.settings_ui_mbdp_open = bool(mbdp_section_open)
            cfg.mark_dirty()
        if mbdp_section_open:
            PyImGui.text("MB/DP upkeep:")
            _same_line(10)
            if _badge_button("ON" if cfg.mbdp_enabled else "OFF", enabled=bool(cfg.mbdp_enabled), id_suffix="pycons_settings_mbdp_toggle"):
                cfg.mbdp_enabled = not bool(cfg.mbdp_enabled)
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_enabled")

            changed, v = ui_checkbox("Allow party-wide in human parties##pycons_mbdp_human", bool(cfg.mbdp_allow_partywide_in_human_parties))
            if changed:
                cfg.mbdp_allow_partywide_in_human_parties = bool(v)
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_allow_partywide_in_human_parties")

            changed, v = ui_checkbox("Receiver requires item enabled locally##pycons_mbdp_receiver_require_enabled", bool(cfg.mbdp_receiver_require_enabled))
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

            if PyImGui.button("Restore default MB/DP settings##pycons_mbdp_restore_defaults"):
                _apply_mbdp_defaults()
                _mark_mbdp_preset_custom()
                _debug("MB/DP settings restored to defaults.", Console.MessageType.Info)
                cfg.save_if_dirty_throttled(0)
            _show_setting_tooltip("mbdp_restore_defaults")

            PyImGui.text(f"Self minor DP trigger ({_fmt_effective(cfg.mbdp_self_dp_minor_threshold)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_self_minor", int(cfg.mbdp_self_dp_minor_threshold))
            if changed:
                cfg.mbdp_self_dp_minor_threshold = max(-60, min(0, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_self_dp_minor_threshold")

            PyImGui.text(f"Self major DP trigger ({_fmt_effective(cfg.mbdp_self_dp_major_threshold)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_self_major", int(cfg.mbdp_self_dp_major_threshold))
            if changed:
                cfg.mbdp_self_dp_major_threshold = max(-60, min(0, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_self_dp_major_threshold")

            PyImGui.text(f"Self target effective ({_fmt_effective(cfg.mbdp_self_morale_target_effective)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_self_target", int(cfg.mbdp_self_morale_target_effective))
            if changed:
                cfg.mbdp_self_morale_target_effective = max(-60, min(10, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_self_morale_target_effective")

            PyImGui.text("Self minimum useful morale benefit:")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_self_gain", int(cfg.mbdp_self_min_morale_gain))
            if changed:
                cfg.mbdp_self_min_morale_gain = max(0, min(10, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_self_min_morale_gain")

            PyImGui.text("Party minimum eligible members:")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_members", int(cfg.mbdp_party_min_members))
            if changed:
                cfg.mbdp_party_min_members = max(2, min(8, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_min_members")

            PyImGui.text("Party trigger interval (ms):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_interval", int(cfg.mbdp_party_min_interval_ms), width=150.0)
            if changed:
                cfg.mbdp_party_min_interval_ms = max(1000, int(val))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_min_interval_ms")

            PyImGui.text(f"Party target effective ({_fmt_effective(cfg.mbdp_party_target_effective)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_target", int(cfg.mbdp_party_target_effective))
            if changed:
                cfg.mbdp_party_target_effective = max(-60, min(10, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_target_effective")

            PyImGui.text("Party +5 minimum total benefit:")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_gain5", int(cfg.mbdp_party_min_total_gain_5))
            if changed:
                cfg.mbdp_party_min_total_gain_5 = max(0, min(60, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_min_total_gain_5")

            PyImGui.text("Party +10 minimum total benefit:")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_gain10", int(cfg.mbdp_party_min_total_gain_10))
            if changed:
                cfg.mbdp_party_min_total_gain_10 = max(0, min(120, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_min_total_gain_10")

            PyImGui.text(f"Party light DP trigger ({_fmt_effective(cfg.mbdp_party_light_dp_threshold)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_light", int(cfg.mbdp_party_light_dp_threshold))
            if changed:
                cfg.mbdp_party_light_dp_threshold = max(-60, min(0, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_light_dp_threshold")

            PyImGui.text(f"Party heavy DP trigger ({_fmt_effective(cfg.mbdp_party_heavy_dp_threshold)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_heavy", int(cfg.mbdp_party_heavy_dp_threshold))
            if changed:
                cfg.mbdp_party_heavy_dp_threshold = max(-60, min(0, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_party_heavy_dp_threshold")

            PyImGui.text(f"Powerstone emergency trigger ({_fmt_effective(cfg.mbdp_powerstone_dp_threshold)}):")
            _same_line(10)
            changed, val = ui_input_int_fixed("##pycons_mbdp_party_powerstone", int(cfg.mbdp_powerstone_dp_threshold))
            if changed:
                cfg.mbdp_powerstone_dp_threshold = max(-60, min(0, int(val)))
                cfg.mark_dirty()
                _mark_mbdp_preset_custom()
            _show_setting_tooltip("mbdp_powerstone_dp_threshold")

            PyImGui.separator()

        presets_section_open = _styled_collapsing_header(
            "MB/DP Presets##pycons_settings_presets_dropdown",
            bool(cfg.settings_ui_presets_open),
            "mbdp",
        )
        if bool(cfg.settings_ui_presets_open) != bool(presets_section_open):
            cfg.settings_ui_presets_open = bool(presets_section_open)
            cfg.mark_dirty()
        if presets_section_open:
            _show_setting_tooltip("presets_section")
            PyImGui.text(f"Active preset: {str(cfg.last_applied_preset or 'None')}")
            PyImGui.separator()

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
            PyImGui.text("Custom preset slots:")
            for i in range(1, PRESET_SLOT_COUNT + 1):
                PyImGui.text(f"Slot {i}:")
                _same_line(8)
                current_name = str(cfg.preset_slot_names.get(i, _preset_slot_default_name(i)))
                changed_name, new_name = ui_input_text(f"##pycons_preset_name_{i}", current_name, 64)
                if changed_name:
                    n = str(new_name or "").strip()
                    cfg.preset_slot_names[i] = n if n else _preset_slot_default_name(i)
                    cfg.mark_dirty()
                _same_line(8)
                if PyImGui.button(f"Save##pycons_preset_save_{i}"):
                    _save_custom_preset_slot(i)
                _show_setting_tooltip("preset_save_slot")
                _same_line(8)
                if PyImGui.button(f"Load##pycons_preset_load_{i}"):
                    _load_custom_preset_slot(i)
                _show_setting_tooltip("preset_load_slot")
            PyImGui.separator()

        restock_section_open = _styled_collapsing_header(
            "Restock Settings##pycons_settings_restock_dropdown",
            bool(cfg.settings_ui_restock_open),
            "restock",
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

            PyImGui.text("Restock interval (ms):")
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

            PyImGui.text("Per-cycle move cap:")
            _same_line(10)
            changed, cap_val = ui_input_int_fixed("##pycons_restock_move_cap", int(cfg.restock_move_cap_per_cycle), width=120.0)
            if changed:
                cfg.restock_move_cap_per_cycle = int(
                    max(MIN_RESTOCK_MOVE_CAP_PER_CYCLE, min(MAX_RESTOCK_MOVE_CAP_PER_CYCLE, int(cap_val)))
                )
                cfg.mark_dirty()
            _show_setting_tooltip("restock_move_cap_per_cycle")

            PyImGui.text_wrapped("Choose target inventory amounts for selected items. Pycons will withdraw shortages and deposit excess while Xunlai Vault restock is enabled.")
            PyImGui.text_wrapped("Restock balancing follows the active item toggles in the main window.")
            selected_specs = _selected_restock_specs()

            PyImGui.text("Set all selected targets to:")
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

        if _styled_collapsing_header("Select consumables to show in the main window##pycons_settings_consumables_dropdown", False, "general"):
            _text_secondary("Selected here -> shown in the main window.")
            if bool(cfg.persist_main_runtime_toggles):
                _text_secondary("Main-window ON/OFF also updates saved enabled defaults.")
            else:
                _text_secondary("Main-window ON/OFF is runtime-only unless persistence is enabled above.")
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

            conset_has_match = search_active and _list_has_match(explorable_consets, flt)
            explorable_other_has_match = search_active and _list_has_match(explorable_other, flt)
            explorable_has_match = search_active and (conset_has_match or explorable_other_has_match)
            summoning_has_match = search_active and _list_has_match(summoning_items, flt)
            outpost_has_match = search_active and _list_has_match(outpost_items, flt)
            mbdp_has_match = search_active and _list_has_match(mbdp_items, flt)
            alcohol_has_match = search_active and _list_has_match(alcohol_items, flt)

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
            elif pending_collapse_all:
                explorable_force = False
                summoning_force = False
                outpost_force = False
                mbdp_force = False
                alcohol_force = False
            else:
                explorable_force = False if collapse_now else (True if explorable_has_match else (False if search_active else None))
                summoning_force = False if collapse_now else (True if summoning_has_match else (False if search_active else None))
                outpost_force = False if collapse_now else (True if outpost_has_match else (False if search_active else None))
                mbdp_force = False if collapse_now else (True if mbdp_has_match else (False if search_active else None))
                alcohol_force = False if collapse_now else (True if alcohol_has_match else (False if search_active else None))

            visible_regular_keys = []
            visible_alcohol_keys = []

            category_keys = _ordered_consumable_category_keys(["explorable", "summoning", "mbdp", "outpost", "alcohol"])
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

        _draw_main_window()
        _draw_settings_window()
        _tick_disable_alcohol_effect()

        cfg.save_if_dirty_throttled(750)

        if bool(getattr(cfg, "auto_vault_restock", False)) and restock_tick_timer.HasElapsed(int(max(MIN_RESTOCK_INTERVAL_MS, int(getattr(cfg, "restock_interval_ms", DEFAULT_RESTOCK_INTERVAL_MS))))):
            restock_tick_timer.Start()
            _tick_vault_restock()

        if tick_timer.HasElapsed(int(max(MIN_INTERVAL_MS, cfg.interval_ms))):
            tick_timer.Start()
            used = _tick_morale_dp()
            if not used:
                used = _tick_consume()
            if not used:
                _tick_alcohol()

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
