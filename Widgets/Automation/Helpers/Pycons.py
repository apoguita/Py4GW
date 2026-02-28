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

try:
    from typing import Any, cast
    import os
    import re
    import unicodedata
    import PyImGui
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
    from Py4GWCoreLib import ItemArray, Bag, Item, Effects, Player, Party
    from Py4GWCoreLib.IniManager import IniManager  # NEW: persisted windows
    import threading

    BOT_NAME = "Pycons"
    INI_SECTION = "Pycons"

    MIN_INTERVAL_MS = 250
    DEFAULT_INTERNAL_COOLDOWN_MS = 5000
    AFTERCAST_MS = 350

    # Brief cache so multiple "due" items don't rescan bags back-to-back
    INVENTORY_CACHE_MS = 1500
    BROADCAST_KEEPALIVE_MS = 5000
    TEAM_SETTINGS_CACHE_MS = 3000

    # Fallback durations (ms) for items that cannot resolve effect IDs:
    FALLBACK_SHORT_MS = 10 * 60 * 1000
    FALLBACK_MEDIUM_MS = 20 * 60 * 1000
    FALLBACK_LONG_MS = 30 * 60 * 1000

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
        "powerstone_of_courage": ("powerstone of courage",),
        "seal_of_the_dragon_empire": ("seal of the dragon empire",),
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
    SETTINGS_CONSUMABLE_CATEGORY_ORDER = ["explorable", "mbdp", "outpost", "alcohol"]

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
        "alcohol_enabled": {
            "short": "Master toggle for alcohol automation.",
            "long": "Enables or disables all alcohol upkeep logic. If OFF, alcohol settings below are ignored regardless of target or preference.",
            "why": "Useful to instantly pause alcohol consumption without changing item selections.",
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
            "long": "Search text filter for consumables lists in the settings window. Works across explorable, outpost, MB/DP, and alcohol groups.",
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
        "show_advanced_intervals",
        "alcohol_enabled",
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
        "show_advanced_intervals",
        "alcohol_enabled",
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
            and bool(cfg.selected.get("honeycomb", False))
            and bool(cfg.enabled.get("honeycomb", False))
            and (not bool(cfg.selected.get("elixir_of_valor", False)))
            and (not bool(cfg.enabled.get("elixir_of_valor", False)))
            and (not bool(cfg.selected.get("rainbow_candy_cane", False)))
            and (not bool(cfg.enabled.get("rainbow_candy_cane", False)))
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
            _set_item_toggle("honeycomb", True, True)
            _set_item_toggle("elixir_of_valor", False, False)
            _set_item_toggle("rainbow_candy_cane", False, False)
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
        for item in ALCOHOL_ITEMS:
            k = str(item.get("key", "") or "")
            if not k:
                continue
            ini_handler.write_key(INI_SECTION, f"{prefix}alcohol_selected_{k}", str(bool(cfg.alcohol_selected.get(k, False))))
            ini_handler.write_key(INI_SECTION, f"{prefix}alcohol_enabled_{k}", str(bool(cfg.alcohol_enabled_items.get(k, False))))
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

        for item in ALL_CONSUMABLES:
            k = str(item.get("key", "") or "")
            if not k:
                continue
            cfg.selected[k] = bool(ini_handler.read_bool(INI_SECTION, f"{prefix}selected_{k}", bool(cfg.selected.get(k, False))))
            cfg.enabled[k] = bool(ini_handler.read_bool(INI_SECTION, f"{prefix}enabled_{k}", bool(cfg.enabled.get(k, False))))
        for item in ALCOHOL_ITEMS:
            k = str(item.get("key", "") or "")
            if not k:
                continue
            cfg.alcohol_selected[k] = bool(ini_handler.read_bool(INI_SECTION, f"{prefix}alcohol_selected_{k}", bool(cfg.alcohol_selected.get(k, False))))
            cfg.alcohol_enabled_items[k] = bool(ini_handler.read_bool(INI_SECTION, f"{prefix}alcohol_enabled_{k}", bool(cfg.alcohol_enabled_items.get(k, False))))

        _runtime_sync_from_cfg_full()

        _last_mbdp_party_ms = 0
        cfg.last_applied_preset = str(cfg.preset_slot_names.get(slot, _preset_slot_default_name(slot)))
        cfg.mark_dirty()
        _log(f"Loaded custom preset slot {slot}.", Console.MessageType.Info)
        return True

    def _set_other_party_accounts_opt_in():
        try:
            self_email = str(Player.GetAccountEmail() or "")
            if not self_email:
                _log("Could not set opt-in for others: local account email unavailable.", Console.MessageType.Warning)
                return
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
            else:
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

            updated = 0
            seen = set()
            toggled_names = []
            for acc in accounts:
                email = _acc_email(acc)
                if not email or email == self_email or email in seen:
                    continue
                seen.add(email)
                email_hash = hashlib.md5(email.encode()).hexdigest()[:8]
                ini = IniHandler(f"Widgets/Config/Pycons_{email_hash}.ini")
                ini.write_key(INI_SECTION, "team_consume_opt_in", "True")
                updated += 1
                nm = _acc_name(acc)
                if nm:
                    toggled_names.append(nm)
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
            all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
            me = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email)
            my_party_id = _acc_party_id(me) if me else 0
            accounts = []
            if my_party_id > 0:
                for acc in all_accounts:
                    if not acc:
                        continue
                    if not bool(getattr(acc, "IsAccount", False)):
                        continue
                    if _acc_party_id(acc) != my_party_id:
                        continue
                    accounts.append(acc)
            else:
                party_rows = _get_party_player_rows()
                party_name_norms = {str(r.get("name_norm", "") or "") for r in party_rows if str(r.get("name_norm", "") or "")}
                for acc in all_accounts:
                    if not acc:
                        continue
                    if not bool(getattr(acc, "IsAccount", False)):
                        continue
                    cname = _normalize_name(_acc_name(acc))
                    if cname and cname in party_name_norms:
                        accounts.append(acc)

            updated = 0
            seen = set()
            toggled_names = []
            for acc in accounts:
                email = _acc_email(acc)
                if not email or email == self_email or email in seen:
                    continue
                seen.add(email)
                email_hash = hashlib.md5(email.encode()).hexdigest()[:8]
                ini = IniHandler(f"Widgets/Config/Pycons_{email_hash}.ini")
                ini.write_key(INI_SECTION, "team_consume_opt_in", "False")
                updated += 1
                nm = _acc_name(acc)
                if nm:
                    toggled_names.append(nm)
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
            cfg.team_broadcast = new_broadcast
            cfg.team_consume_opt_in = new_optin
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

        # Outpost-only (alphabetical by label)
        {"key": "chocolate_bunny", "label": "Chocolate Bunny", "model_id": int(_model_id_value("Chocolate_Bunny", 0)), "skills": ["Sugar_Jolt_(long)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_LONG_MS},
        {"key": "creme_brulee", "label": "Crème Brûlée", "model_id": int(_model_id_value("Creme_Brulee", 0)), "skills": ["Sugar_Jolt_(long)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_LONG_MS},
        {"key": "fruitcake", "label": "Fruitcake", "model_id": int(_model_id_value("Fruitcake", 0)), "skills": ["Sugar_Rush_(medium)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_MEDIUM_MS},
        {"key": "jar_of_honey", "label": "Jar of Honey", "model_id": int(_model_id_value("Jar_Of_Honey", 0)), "skills": ["Sugar_Rush_(long)"], "use_where": "outpost", "require_effect_id": False, "fallback_duration_ms": FALLBACK_LONG_MS},
        {"key": "red_bean_cake", "label": "Red Bean Cake", "model_id": int(_model_id_value("Red_Bean_Cake", 0)), "skills": ["Sugar_Rush_(medium)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_MEDIUM_MS},
        {"key": "sugary_blue_drink", "label": "Sugary Blue Drink", "model_id": int(_model_id_value("Sugary_Blue_Drink", 0)), "skills": ["Sugar_Jolt_(short)"], "use_where": "outpost", "require_effect_id": False, "fallback_duration_ms": FALLBACK_SHORT_MS},
    ]

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
    MB_DP_BY_KEY = {c["key"]: c for c in MB_DP_ITEMS}
    CONSET_KEYS = {"armor_of_salvation", "essence_of_celerity", "grail_of_might"}

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

    def _build_icon_candidates():
        candidates = []
        root = os.path.abspath(_ICON_SEARCH_ROOT)
        for dirpath, _dirnames, filenames in os.walk(root):
            _dirnames.sort()
            filenames.sort()
            for filename in filenames:
                if not str(filename).lower().endswith(".png"):
                    continue
                full_path = os.path.join(dirpath, filename)
                rel_path = _to_texture_path(full_path)
                rel_lc = rel_path.lower()
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

    def _score_icon_candidate(key: str, label: str, cand: dict) -> int:
        key_norm = _normalize_icon_name(key.replace("_", " "))
        label_norm = _normalize_icon_name(label)
        key_tokens = _icon_tokens(key)
        label_tokens = _icon_tokens(label)
        wanted = set(key_tokens) | set(label_tokens)
        for alias in CONSUMABLE_ICON_NAME_ALIASES.get(str(key or ""), ()):
            wanted.update(_icon_tokens(alias))
        if not wanted:
            return -1
        overlap = wanted.intersection(set(cand.get("tokens", set())))
        if not overlap:
            return -1
        strong_overlap = [t for t in overlap if len(t) >= 4]
        score = int(cand.get("priority", 0))
        score += len(overlap) * 7
        score += len(strong_overlap) * 11
        cand_norms = set(cand.get("norm_variants", set()))
        if key_norm in cand_norms:
            score += 160
        if label_norm in cand_norms:
            score += 160
        if key_tokens and key_tokens.issubset(set(cand.get("tokens", set()))):
            score += 80
        if label_tokens and label_tokens.issubset(set(cand.get("tokens", set()))):
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
        best_score = -1
        best_path = ""
        for cand in _icon_candidates_cache:
            score = _score_icon_candidate(k, label, cand)
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

    def _draw_icon_toggle_or_checkbox(state_now: bool, key: str, label: str, id_prefix: str, icon_size: float = 20.0):
        tooltip_text = _consumable_tooltip_with_label(key, label)
        icon_path = _resolve_consumable_icon_path(key, label)
        current = bool(state_now)
        if icon_path:
            pushed_alpha = False
            pushed_colors = 0
            try:
                try:
                    # Keep a dark backing panel behind icon textures for readability.
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
        _, current = ui_checkbox(f"##{id_prefix}_cb_{key}", bool(state_now))
        _tooltip_if_hovered(tooltip_text)
        changed = bool(current) != bool(state_now)
        return bool(current), bool(changed), False

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
    import hashlib
    _ini_handler_cache = None
    _ini_path_cache = None
    
    def _get_ini_handler():
        global _ini_handler_cache, _ini_path_cache
        if _ini_handler_cache is None:
            account_email = Player.GetAccountEmail()
            if not account_email:
                # Fallback to generic file if not logged in yet
                _ini_path_cache = "Widgets/Config/Pycons.ini"
            else:
                email_hash = hashlib.md5(account_email.encode()).hexdigest()[:8]
                _ini_path_cache = f"Widgets/Config/Pycons_{email_hash}.ini"
            _ini_handler_cache = IniHandler(_ini_path_cache)
            ConsoleLog(BOT_NAME, f"Using config file: {_ini_path_cache} (account: {account_email})", Console.MessageType.Info)
        return _ini_handler_cache
    
    def _get_ini_path():
        global _ini_path_cache
        if _ini_path_cache is None:
            _get_ini_handler()  # Initialize if needed
        return _ini_path_cache

    class Config:
        def __init__(self):
            ini_handler = _get_ini_handler()
            self.debug_logging = ini_handler.read_bool(INI_SECTION, "debug_logging", False)
            self.interval_ms = ini_handler.read_int(INI_SECTION, "interval_ms", 1500)
            self.show_selected_list = ini_handler.read_bool(INI_SECTION, "show_selected_list", True)
            self.only_show_available_inventory = ini_handler.read_bool(INI_SECTION, "only_show_available_inventory", False)
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
            self.min_interval_ms = {}
            for c in CONSUMABLES:
                k = c["key"]
                self.min_interval_ms[k] = max(0, int(ini_handler.read_int(INI_SECTION, f"min_interval_{k}", 0)))

            # Alcohol
            self.alcohol_enabled = ini_handler.read_bool(INI_SECTION, "alcohol_enabled", False)
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

            # Settings-window consumables group open/closed state
            self.settings_explorable_open = ini_handler.read_bool(INI_SECTION, "settings_explorable_open", False)
            self.settings_outpost_open = ini_handler.read_bool(INI_SECTION, "settings_outpost_open", False)
            self.settings_mbdp_open = ini_handler.read_bool(INI_SECTION, "settings_mbdp_open", False)
            self.settings_alcohol_open = ini_handler.read_bool(INI_SECTION, "settings_alcohol_open", False)

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

            # Team / multibox settings
            self.team_broadcast = ini_handler.read_bool(INI_SECTION, "team_broadcast", False)
            self.team_consume_opt_in = ini_handler.read_bool(INI_SECTION, "team_consume_opt_in", False)

            self._dirty = bool(getattr(self, "_mbdp_targets_migrated", False))
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
            ini_handler.write_key(INI_SECTION, "show_selected_list", str(bool(self.show_selected_list)))
            ini_handler.write_key(INI_SECTION, "only_show_available_inventory", str(bool(self.only_show_available_inventory)))
            ini_handler.write_key(INI_SECTION, "tooltip_visibility", str(int(self.tooltip_visibility)))
            ini_handler.write_key(INI_SECTION, "tooltip_length", str(int(self.tooltip_length)))
            ini_handler.write_key(INI_SECTION, "tooltip_show_why", str(bool(self.tooltip_show_why)))
            ini_handler.write_key(INI_SECTION, "last_applied_preset", str(self.last_applied_preset))
            ini_handler.write_key(INI_SECTION, "last_party_opt_toggle_summary", str(self.last_party_opt_toggle_summary))
            for i in range(1, PRESET_SLOT_COUNT + 1):
                ini_handler.write_key(INI_SECTION, f"preset_slot_{i}_name", str(self.preset_slot_names.get(i, _preset_slot_default_name(i))))

            ini_handler.write_key(INI_SECTION, "show_advanced_intervals", str(bool(self.show_advanced_intervals)))
            for k, v in self.min_interval_ms.items():
                ini_handler.write_key(INI_SECTION, f"min_interval_{k}", str(int(max(0, int(v)))))

            ini_handler.write_key(INI_SECTION, "alcohol_enabled", str(bool(self.alcohol_enabled)))
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
            ini_handler.write_key(INI_SECTION, "settings_outpost_open", str(bool(self.settings_outpost_open)))
            ini_handler.write_key(INI_SECTION, "settings_mbdp_open", str(bool(self.settings_mbdp_open)))
            ini_handler.write_key(INI_SECTION, "settings_alcohol_open", str(bool(self.settings_alcohol_open)))

            for k, v in self.alcohol_selected.items():
                ini_handler.write_key(INI_SECTION, f"alcohol_selected_{k}", str(bool(v)))
            for k, v in self.alcohol_enabled_items.items():
                ini_handler.write_key(INI_SECTION, f"alcohol_enabled_{k}", str(bool(v)))

            # Team / multibox settings
            # team_broadcast: When enabled, broadcasts item usage to other accounts
            # team_consume_opt_in: When enabled (on followers), consumes items when broadcasts are received
            # Note: team_consume_opt_in is saved separately (below in settings window) to avoid conflicts
            ini_handler.write_key(INI_SECTION, "team_broadcast", str(bool(self.team_broadcast)))
            _debug(f"Saved team_broadcast setting: {self.team_broadcast}", Console.MessageType.Debug)

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
            self.last_visible_count = [0]
            self.request_expand_selected = [False]
            self.request_collapse_selected = [False]
            self.runtime_selected = {}
            self.runtime_enabled = {}
            self.runtime_alcohol_selected = {}
            self.runtime_alcohol_enabled = {}

    _rt = _RuntimeState()
    # Aliases preserved so UI code and existing access patterns remain identical.
    show_settings = _rt.show_settings
    filter_text = _rt.filter_text
    last_search_active = _rt.last_search_active
    last_visible_count = _rt.last_visible_count
    request_expand_selected = _rt.request_expand_selected
    request_collapse_selected = _rt.request_collapse_selected

    tick_timer = Timer()
    tick_timer.Start()

    aftercast_timer = Timer()
    aftercast_timer.Start()
    aftercast_timer.Stop()

    internal_timers = {}
    _skill_id_cache = {}
    _skill_name_cache = {}
    _skill_retry_timer = {}
    _warn_timer = {}
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
    _inv_ready_cached = True
    _inv_ready_ts = 0
    _first_main_call = True

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

    def _runtime_regular_selected(key: str) -> bool:
        return bool(_rt.runtime_selected.get(key, bool(cfg.selected.get(key, False))))

    def _runtime_regular_enabled(key: str) -> bool:
        return bool(_rt.runtime_enabled.get(key, bool(cfg.enabled.get(key, False))))

    def _runtime_alcohol_selected(key: str) -> bool:
        return bool(_rt.runtime_alcohol_selected.get(key, bool(cfg.alcohol_selected.get(key, False))))

    def _runtime_alcohol_enabled(key: str) -> bool:
        return bool(_rt.runtime_alcohol_enabled.get(key, bool(cfg.alcohol_enabled_items.get(key, False))))

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

    def _apply_regular_selection_change(key: str, selected: bool):
        cfg.selected[key] = bool(selected)
        _rt.runtime_selected[key] = bool(selected)
        if not bool(selected):
            cfg.enabled[key] = False
            _rt.runtime_enabled[key] = False
            if not _any_selected_anywhere():
                cfg.show_selected_list = False
                request_collapse_selected[0] = True
        else:
            if not bool(cfg.show_selected_list):
                cfg.show_selected_list = True
            request_expand_selected[0] = True
        cfg.mark_dirty()

    def _apply_alcohol_selection_change(key: str, selected: bool):
        cfg.alcohol_selected[key] = bool(selected)
        _rt.runtime_alcohol_selected[key] = bool(selected)
        if not bool(selected):
            cfg.alcohol_enabled_items[key] = False
            _rt.runtime_alcohol_enabled[key] = False
            if not _any_selected_anywhere():
                cfg.show_selected_list = False
                request_collapse_selected[0] = True
        else:
            if not bool(cfg.show_selected_list):
                cfg.show_selected_list = True
            request_expand_selected[0] = True
        cfg.mark_dirty()

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

    # -------------------------
    # Inventory caching + stock counts
    # -------------------------
    def _schedule_refresh(delay_ms: int):
        try:
            t = threading.Timer(delay_ms / 1000.0, lambda: _refresh_inventory_cache(force=True))
            t.daemon = True
            t.start()
        except Exception as e:
            try:
                _debug(f"Failed to schedule inventory refresh: {e}", Console.MessageType.Debug)
            except Exception:
                pass

    def _refresh_inventory_cache(force: bool = False) -> bool:
        global _inv_cache_items, _inv_cache_ts, _inv_counts_by_model
        now = _now_ms()
        if (not force) and _inv_cache_items is not None and (now - int(_inv_cache_ts)) < INVENTORY_CACHE_MS:
            return True

        try:
            items = ItemArray.GetItemArray(SCAN_BAGS)
            _inv_cache_items = list(items) if items else []
            _inv_cache_ts = int(now)

            counts = {}
            for item_id in _inv_cache_items:
                try:
                    mid = int(Item.GetModelID(int(item_id)))
                    # Get the stack quantity by accessing the item instance
                    qty = 1
                    try:
                        item_obj = Item.item_instance(int(item_id))
                        qty = int(getattr(item_obj, 'quantity', 1))
                        if qty <= 0:
                            qty = 1
                    except Exception as qty_error:
                        _debug(f"Failed to get quantity for item_id {item_id}: {qty_error}", Console.MessageType.Debug)
                except Exception:
                    continue
                counts[mid] = int(counts.get(mid, 0)) + int(qty)
            _inv_counts_by_model = counts
            return True
        except Exception as e:
            _inv_cache_items = None
            _inv_counts_by_model = {}
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
        if model_id <= 0:
            return 0
        if not _refresh_inventory_cache(False):
            return 0
        if not _inv_cache_items:
            return 0
        for item_id in _inv_cache_items:
            try:
                if int(Item.GetModelID(int(item_id))) == int(model_id):
                    return int(item_id)
            except Exception:
                continue
        return 0

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
            import hashlib
            email_hash = hashlib.md5(account_email.encode()).hexdigest()[:8]
            ini = IniHandler(f"Widgets/Config/Pycons_{email_hash}.ini")
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
            raw = morale_by_agent.get(int(row["agent_id"]), None)
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

    def _tick_morale_dp() -> bool:
        global _last_mbdp_party_ms
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

        # Party decisions only from the broadcaster coordinator.
        if not bool(cfg.team_broadcast):
            return False
        same_party_accounts = _get_same_party_accounts()
        if not same_party_accounts:
            return False
        if not _coordinator_gate(same_party_accounts):
            return False

        party_rows, party_counts = _get_party_member_rows()
        if not party_rows:
            return False
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
            return False
        if other_human_name_norms and len(recipients_emails) < 1:
            _debug(
                f"MB/DP PARTY skip: no opted-in recipients among other humans in current party "
                f"(other_humans={len(other_human_name_norms)})."
            )
            return False

        if (not bool(cfg.mbdp_allow_partywide_in_human_parties)) and len(party_human_name_norms.difference(eligible_humans)) > 0:
            _debug(
                f"MB/DP PARTY skip: found non-eligible human party members ({len(party_human_name_norms.difference(eligible_humans))}); "
                "enable 'allow party-wide in human parties' to override."
            )
            return False

        now = _now_ms()
        if _last_mbdp_party_ms > 0 and (now - int(_last_mbdp_party_ms)) < int(cfg.mbdp_party_min_interval_ms):
            return False

        states = _compute_party_morale_states(eligible_humans, party_rows, same_party_accounts)
        if len(states) < int(cfg.mbdp_party_min_members):
            _debug(
                f"MB/DP PARTY skip: sampled_members={len(states)} < min_members={cfg.mbdp_party_min_members} "
                f"(humans={party_counts['humans']} heroes={party_counts['heroes']} mercs={party_counts['mercenaries']} hench={party_counts['henchmen']})"
            )
            return False
        if states:
            _debug(f"MB/DP PARTY sample: {states[0]['name']} raw={states[0]['raw']} effective={_fmt_effective(states[0]['effective'])} dp={states[0]['dp']}")

        total_dp = sum(int(s["dp"]) for s in states)
        party_light_dp_threshold = max(0, -int(cfg.mbdp_party_light_dp_threshold))
        party_heavy_dp_threshold = max(0, -int(cfg.mbdp_party_heavy_dp_threshold))
        party_emergency_dp_threshold = max(0, -int(cfg.mbdp_powerstone_dp_threshold))
        light_cnt = sum(1 for s in states if int(s["dp"]) >= party_light_dp_threshold)
        heavy_cnt = sum(1 for s in states if int(s["dp"]) >= party_heavy_dp_threshold)
        emergency_cnt = sum(1 for s in states if int(s["dp"]) >= party_emergency_dp_threshold)
        target_eff = int(cfg.mbdp_party_target_effective)
        gain_5 = sum(max(0, min(5, target_eff - int(s["effective"]))) for s in states)
        gain_10 = sum(max(0, min(10, target_eff - int(s["effective"]))) for s in states)
        strict_target = int(cfg.mbdp_party_target_effective)
        strict_target_missing = sum(max(0, strict_target - int(s["effective"])) for s in states)
        strict_target_members = sum(1 for s in states if int(s["effective"]) < strict_target)

        # Decision order: emergency -> deterministic DP -> smoothing DP -> morale.
        candidate_choices = []
        if emergency_cnt >= int(cfg.mbdp_party_min_members):
            candidate_choices.append(
                ("powerstone_of_courage", f"emergency_cnt={emergency_cnt} trigger={_fmt_effective(cfg.mbdp_powerstone_dp_threshold)} (~{party_emergency_dp_threshold}% DP)")
            )
        if heavy_cnt >= int(cfg.mbdp_party_min_members):
            candidate_choices.append(
                ("oath_of_purity", f"heavy_cnt={heavy_cnt} trigger={_fmt_effective(cfg.mbdp_party_heavy_dp_threshold)} (~{party_heavy_dp_threshold}% DP)")
            )
        if light_cnt >= int(cfg.mbdp_party_min_members):
            candidate_choices.append(
                ("four_leaf_clover", f"light_cnt={light_cnt} trigger={_fmt_effective(cfg.mbdp_party_light_dp_threshold)} (~{party_light_dp_threshold}% DP)")
            )

        leader_force_active = bool(cfg.mbdp_strict_party_plus10)
        if leader_force_active:
            # In leader force mode, morale spending is strictly target-driven.
            # Only add morale candidates if party members are below the configured target.
            if strict_target_missing > 0:
                strict_reason = (
                    f"strict_target={_fmt_effective(strict_target)} "
                    f"members_below_target={strict_target_members} total_missing={strict_target_missing}"
                )
                candidate_choices.append(("elixir_of_valor", strict_reason))
                if bool(cfg.selected.get("rainbow_candy_cane", False)) and _runtime_regular_enabled("rainbow_candy_cane"):
                    candidate_choices.append(("rainbow_candy_cane", strict_reason + " fallback+5"))
                candidate_choices.append(("honeycomb", strict_reason + " fallback+5"))
        else:
            if gain_10 >= int(cfg.mbdp_party_min_total_gain_10):
                candidate_choices.append(("elixir_of_valor", f"gain10={gain_10} min={cfg.mbdp_party_min_total_gain_10}"))
            elif gain_5 >= int(cfg.mbdp_party_min_total_gain_5):
                gain5_reason = f"gain5={gain_5} min={cfg.mbdp_party_min_total_gain_5}"
                if bool(cfg.selected.get("rainbow_candy_cane", False)) and _runtime_regular_enabled("rainbow_candy_cane"):
                    candidate_choices.append(("rainbow_candy_cane", gain5_reason))
                candidate_choices.append(("honeycomb", gain5_reason))

        if not candidate_choices:
            _debug(
                f"MB/DP PARTY skip: members={len(states)} total_dp={total_dp} light={light_cnt} heavy={heavy_cnt} "
                f"gain5={gain_5} gain10={gain_10}"
            )
            return False

        _debug("MB/DP PARTY states: " + ", ".join([f"{s['name']} raw={s['raw']} eff={_fmt_effective(s['effective'])} dp={s['dp']}" for s in states]))
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
            f"MB/DP PARTY fire {spec['label']}: {chosen_reason}; members={len(states)} total_dp={total_dp} "
            f"gain5={gain_5} gain10={gain_10} recipients={len(recipients_emails)}"
        )
        if _use_item_id(item_id, spec["key"]):
            _last_mbdp_party_ms = now
            _last_used_ms[spec["key"]] = now
            aftercast_timer.Start()
            try:
                _broadcast_use(int(spec.get("model_id", 0)), 1, 0, recipients=recipients_emails)
            except Exception:
                pass
            return True

        return False

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

    def _draw_main_row_checkbox_and_badge(key: str, label: str, enabled_now: bool, id_prefix: str):
        enabled, _changed, _used_icon = _draw_icon_toggle_or_checkbox(
            bool(enabled_now), key, label, f"{id_prefix}_main", icon_size=20.0
        )
        _same_line(10)
        PyImGui.text(label)
        _tooltip_if_hovered(_consumable_tooltip_with_label(key, label))
        _same_line(12)
        if _badge_button("ON" if enabled else "OFF", enabled=bool(enabled), id_suffix=f"{id_prefix}_btn_{key}"):
            enabled = not enabled
        _tooltip_if_hovered(_consumable_tooltip_with_label(key, label))
        changed = (bool(enabled_now) != bool(enabled))
        return bool(enabled), bool(changed)

    def _stock_suffix_for_model_id(model_id: int) -> str:
        known, cnt = _stock_status_for_model_id(int(model_id))
        if not known:
            return " —"
        return f" {int(cnt)}"

    def _has_inventory_for_model_id(model_id: int) -> bool:
        mid = int(model_id or 0)
        if mid <= 0:
            return False
        known, cnt = _stock_status_for_model_id(mid)
        if not known:
            _refresh_inventory_cache(False)
            known, cnt = _stock_status_for_model_id(mid)
        return bool(known and int(cnt) > 0)

    # -------------------------
    # Main Window
    # -------------------------
    def _draw_main_window():
        if cfg is None:
            return  # Config not yet loaded
        if not ImGui.Begin(INI_KEY_MAIN, BOT_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
            ImGui.End(INI_KEY_MAIN)
            return

        if PyImGui.button("Settings##pycons_settings"):
            show_settings[0] = not show_settings[0]

        PyImGui.separator()

        PyImGui.text("Interval (ms):")
        _same_line(10)
        changed, val = ui_input_int("##pycons_interval", int(cfg.interval_ms))
        if changed:
            cfg.interval_ms = int(max(MIN_INTERVAL_MS, val))
            cfg.mark_dirty()

        PyImGui.separator()

        # --- Alcohol settings (collapsed dropdown for compactness) ---
        if ui_collapsing_header("Alcohol settings##pycons_alcohol_dropdown", False):
            PyImGui.text("Alcohol upkeep:")
            _same_line(10)
            if _badge_button("ON" if cfg.alcohol_enabled else "OFF", enabled=bool(cfg.alcohol_enabled), id_suffix="pycons_alcohol_toggle"):
                cfg.alcohol_enabled = not bool(cfg.alcohol_enabled)
                cfg.mark_dirty()

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

            # Preference (ONE LINE)
            PyImGui.text("Preference:")
            _same_line(10)

            changed, v = ui_checkbox("Smooth##pycons_alc_pref_smooth_main", int(cfg.alcohol_preference) == 0)
            _tooltip_if_hovered("Default Best all around. Keeps you near the target without burning high-point alcohol unnecessarily")
            if changed and bool(v):
                cfg.alcohol_preference = 0
                cfg.mark_dirty()

            _same_line(10)
            changed, v = ui_checkbox("Strong-first##pycons_alc_pref_strong_main", int(cfg.alcohol_preference) == 1)
            _tooltip_if_hovered("Good when you just want to be drunk ASAP (e.g., you zone in and want max level quickly)")
            if changed and bool(v):
                cfg.alcohol_preference = 1
                cfg.mark_dirty()

            _same_line(10)
            changed, v = ui_checkbox("Weak-first##pycons_alc_pref_weak_main", int(cfg.alcohol_preference) == 2)
            _tooltip_if_hovered("Good if you are trying to stretch rare/valuable alcohol and do not mind it taking longer to climb")
            if changed and bool(v):
                cfg.alcohol_preference = 2
                cfg.mark_dirty()

            PyImGui.separator()

        PyImGui.separator()

        force_open = None
        if request_expand_selected[0]:
            force_open = True
        elif request_collapse_selected[0]:
            force_open = False

        expanded = _collapsing_header_force(
            "Selected consumables##pycons_list",
            force_open=force_open,
            default_open=bool(cfg.show_selected_list),
        )

        if request_expand_selected[0]:
            request_expand_selected[0] = False
        if request_collapse_selected[0]:
            request_collapse_selected[0] = False

        if expanded != bool(cfg.show_selected_list):
            cfg.show_selected_list = bool(expanded)
            cfg.mark_dirty()

        if expanded:
            if PyImGui.button("Select All##pycons_main_select_all"):
                for c in ALL_CONSUMABLES:
                    k = c["key"]
                    if bool(cfg.selected.get(k, False)):
                        _rt.runtime_enabled[k] = True
                for a in ALCOHOL_ITEMS:
                    k = a["key"]
                    if bool(cfg.alcohol_selected.get(k, False)):
                        _rt.runtime_alcohol_enabled[k] = True
            _same_line(10)
            if PyImGui.button("Clear All##pycons_main_clear_all"):
                for c in ALL_CONSUMABLES:
                    k = c["key"]
                    if bool(cfg.selected.get(k, False)):
                        _rt.runtime_enabled[k] = False
                for a in ALCOHOL_ITEMS:
                    k = a["key"]
                    if bool(cfg.alcohol_selected.get(k, False)):
                        _rt.runtime_alcohol_enabled[k] = False

            selected_explorable_conset = [c for c in CONSUMABLES if c.get("use_where") == "explorable" and c.get("key") in CONSET_KEYS and bool(cfg.selected.get(c["key"], False))]
            selected_explorable_other = [c for c in CONSUMABLES if c.get("use_where") == "explorable" and c.get("key") not in CONSET_KEYS and bool(cfg.selected.get(c["key"], False))]
            selected_outpost = [c for c in CONSUMABLES if c.get("use_where") == "outpost" and bool(cfg.selected.get(c["key"], False))]
            selected_mbdp = [c for c in MB_DP_ITEMS if bool(cfg.selected.get(c["key"], False))]
            selected_alcohol = [a for a in ALCOHOL_ITEMS if bool(cfg.alcohol_selected.get(a["key"], False))]
            if bool(cfg.only_show_available_inventory):
                selected_explorable_conset = [c for c in selected_explorable_conset if _has_inventory_for_model_id(int(c.get("model_id", 0)))]
                selected_explorable_other = [c for c in selected_explorable_other if _has_inventory_for_model_id(int(c.get("model_id", 0)))]
                selected_outpost = [c for c in selected_outpost if _has_inventory_for_model_id(int(c.get("model_id", 0)))]
                selected_mbdp = [c for c in selected_mbdp if _has_inventory_for_model_id(int(c.get("model_id", 0)))]
                selected_alcohol = [a for a in selected_alcohol if _has_inventory_for_model_id(int(a.get("model_id", 0)))]

            any_selected = bool(selected_explorable_conset or selected_explorable_other or selected_outpost or selected_mbdp or selected_alcohol)
            if not any_selected:
                PyImGui.text_disabled("None selected. Open Settings and pick consumables.")
            else:
                if selected_explorable_conset or selected_explorable_other:
                    PyImGui.text("Explorable:")
                    if selected_explorable_conset:
                        PyImGui.text("Conset:")
                        for c in selected_explorable_conset:
                            k = c["key"]
                            suffix = _stock_suffix_for_model_id(int(c.get("model_id", 0)))
                            new_enabled, chg = _draw_main_row_checkbox_and_badge(
                                k, c["label"] + suffix, _runtime_regular_enabled(k), "pycons"
                            )
                            if chg:
                                _rt.runtime_enabled[k] = bool(new_enabled)
                        PyImGui.separator()

                    for c in selected_explorable_other:
                        k = c["key"]
                        suffix = _stock_suffix_for_model_id(int(c.get("model_id", 0)))
                        new_enabled, chg = _draw_main_row_checkbox_and_badge(
                            k, c["label"] + suffix, _runtime_regular_enabled(k), "pycons"
                        )
                        if chg:
                            _rt.runtime_enabled[k] = bool(new_enabled)
                    PyImGui.separator()

                if selected_outpost:
                    PyImGui.text("In-town speed boosts:")
                    for c in selected_outpost:
                        k = c["key"]
                        suffix = _stock_suffix_for_model_id(int(c.get("model_id", 0)))
                        new_enabled, chg = _draw_main_row_checkbox_and_badge(
                            k, c["label"] + suffix, _runtime_regular_enabled(k), "pycons"
                        )
                        if chg:
                            _rt.runtime_enabled[k] = bool(new_enabled)
                    PyImGui.separator()

                if selected_mbdp:
                    PyImGui.text("Morale Boost & Death Penalty:")
                    mbdp_party_keys = {
                        "elixir_of_valor",
                        "four_leaf_clover",
                        "honeycomb",
                        "oath_of_purity",
                        "powerstone_of_courage",
                        "rainbow_candy_cane",
                    }
                    mbdp_self_keys = {
                        "peppermint_candy_cane",
                        "pumpkin_cookie",
                        "refined_jelly",
                        "seal_of_the_dragon_empire",
                        "wintergreen_candy_cane",
                    }

                    mbdp_by_key = {str(s.get("key", "")): s for s in MB_DP_ITEMS}
                    missing_party_keys = sorted([k for k in mbdp_party_keys if k not in mbdp_by_key])
                    missing_self_keys = sorted([k for k in mbdp_self_keys if k not in mbdp_by_key])

                    party_specs = [c for c in selected_mbdp if str(c.get("key", "")) in mbdp_party_keys]
                    self_specs = [c for c in selected_mbdp if str(c.get("key", "")) in mbdp_self_keys]
                    unmapped_specs = [c for c in selected_mbdp if str(c.get("key", "")) not in mbdp_party_keys and str(c.get("key", "")) not in mbdp_self_keys]

                    PyImGui.text("Party:")
                    for c in sorted(party_specs, key=lambda x: str(x.get("label", "")).lower()):
                        k = c["key"]
                        suffix = _stock_suffix_for_model_id(int(c.get("model_id", 0)))
                        new_enabled, chg = _draw_main_row_checkbox_and_badge(
                            k, c["label"] + suffix, _runtime_regular_enabled(k), "pycons_mbdp"
                        )
                        if chg:
                            _rt.runtime_enabled[k] = bool(new_enabled)

                    if missing_party_keys:
                        PyImGui.text_disabled("Missing mapped party keys: " + ", ".join(missing_party_keys))

                    PyImGui.spacing()
                    PyImGui.text("Self:")
                    for c in sorted(self_specs, key=lambda x: str(x.get("label", "")).lower()):
                        k = c["key"]
                        suffix = _stock_suffix_for_model_id(int(c.get("model_id", 0)))
                        new_enabled, chg = _draw_main_row_checkbox_and_badge(
                            k, c["label"] + suffix, _runtime_regular_enabled(k), "pycons_mbdp"
                        )
                        if chg:
                            _rt.runtime_enabled[k] = bool(new_enabled)

                    if missing_self_keys:
                        PyImGui.text_disabled("Missing mapped self keys: " + ", ".join(missing_self_keys))

                    if unmapped_specs:
                        PyImGui.separator()
                        PyImGui.text("Unmapped:")
                        for c in sorted(unmapped_specs, key=lambda x: str(x.get("label", "")).lower()):
                            k = c["key"]
                            suffix = _stock_suffix_for_model_id(int(c.get("model_id", 0)))
                            new_enabled, chg = _draw_main_row_checkbox_and_badge(
                                k, c["label"] + suffix, _runtime_regular_enabled(k), "pycons_mbdp"
                            )
                            if chg:
                                _rt.runtime_enabled[k] = bool(new_enabled)
                    PyImGui.separator()

                if selected_alcohol:
                    PyImGui.text("Alcohol:")
                    for a in sorted(selected_alcohol, key=lambda x: x.get("label", "")):
                        k = a["key"]
                        suffix = _stock_suffix_for_model_id(int(a.get("model_id", 0)))
                        enabled_now = _runtime_alcohol_enabled(k)
                        new_enabled, chg = _draw_main_row_checkbox_and_badge(
                            k, _alcohol_display_label(a) + suffix, enabled_now, "pycons_alc"
                        )
                        if chg:
                            _rt.runtime_alcohol_enabled[k] = bool(new_enabled)

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

    def _draw_settings_row(spec: dict, flt: str, visible_keys_out=None, only_available: bool = False):
        k = spec["key"]
        label = spec["label"]
        if not _matches_filter(label, flt):
            return
        model_id = int(spec.get("model_id", 0))
        if bool(only_available) and model_id > 0 and not _has_inventory_for_model_id(model_id):
            return
        if visible_keys_out is not None:
            visible_keys_out.append(k)

        prev = bool(cfg.selected.get(k, False))
        model_id = int(spec.get("model_id", 0))
        stock_suffix = _stock_suffix_for_model_id(model_id) if model_id > 0 else " —"
        display_label = label + stock_suffix
        selected, _changed, _used_icon = _draw_icon_toggle_or_checkbox(
            prev, k, display_label, "pycons_selected", icon_size=18.0
        )
        _same_line(10)
        PyImGui.text(display_label)
        _tooltip_if_hovered(_consumable_tooltip_with_label(k, display_label))

        _draw_min_interval_editor(k)

        selected = bool(selected)
        if prev != selected:
            _apply_regular_selection_change(k, selected)

    def _draw_alcohol_settings_row(spec: dict, flt: str, visible_keys_out=None, only_available: bool = False):
        k = spec["key"]
        label = _alcohol_display_label(spec)
        if not _matches_filter(label, flt):
            return
        model_id = int(spec.get("model_id", 0))
        if bool(only_available) and model_id > 0 and not _has_inventory_for_model_id(model_id):
            return
        if visible_keys_out is not None:
            visible_keys_out.append(k)

        prev = bool(cfg.alcohol_selected.get(k, False))
        model_id = int(spec.get("model_id", 0))
        stock_suffix = _stock_suffix_for_model_id(model_id) if model_id > 0 else " —"
        display_label = label + stock_suffix
        selected, _changed, _used_icon = _draw_icon_toggle_or_checkbox(
            prev, k, display_label, "pycons_alcohol_selected", icon_size=18.0
        )
        _same_line(10)
        PyImGui.text(display_label)
        _tooltip_if_hovered(_consumable_tooltip_with_label(k, display_label))

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

    def _draw_settings_window():
        if cfg is None:
            return  # Config not yet loaded
        if not show_settings[0]:
            return

        # Allow manual resizing of the Settings window by removing the
        # AlwaysAutoResize flag. Users can now expand/collapse and resize
        # the settings window to their preference.
        if not ImGui.Begin(INI_KEY_SETTINGS, "Pycons - Settings##PyconsSettings"):
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

        if PyImGui.button("Set all other party accounts: Opt-in ON##pycons_preset_set_other_optin"):
            _set_other_party_accounts_opt_in()
        _show_setting_tooltip("preset_set_others_optin")

        if PyImGui.button("Set all other party accounts: Opt-in OFF##pycons_preset_set_other_optout"):
            _set_other_party_accounts_opt_out()
        _show_setting_tooltip("preset_set_others_optout")
        PyImGui.text(f"Last party opt toggle: {str(cfg.last_party_opt_toggle_summary or 'None')}")

        PyImGui.separator()
        if ui_collapsing_header("Tooltip settings##pycons_settings_tooltip_dropdown", False):
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
        if ui_collapsing_header("Alcohol settings##pycons_settings_alcohol_dropdown", False):
            PyImGui.text("Alcohol upkeep:")
            _same_line(10)
            if _badge_button("ON" if cfg.alcohol_enabled else "OFF", enabled=bool(cfg.alcohol_enabled), id_suffix="pycons_settings_alcohol_toggle"):
                cfg.alcohol_enabled = not bool(cfg.alcohol_enabled)
                cfg.mark_dirty()
            _show_setting_tooltip("alcohol_enabled")

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

            # Preference (ONE LINE)
            PyImGui.text("Preference:")
            _same_line(10)

            changed, v = ui_checkbox("Smooth##pycons_alc_pref_smooth_settings", int(cfg.alcohol_preference) == 0)
            _show_setting_tooltip("alcohol_preference_smooth")
            if changed and bool(v):
                cfg.alcohol_preference = 0
                cfg.mark_dirty()

            _same_line(10)
            changed, v = ui_checkbox("Strong-first##pycons_alc_pref_strong_settings", int(cfg.alcohol_preference) == 1)
            _show_setting_tooltip("alcohol_preference_strong")
            if changed and bool(v):
                cfg.alcohol_preference = 1
                cfg.mark_dirty()

            _same_line(10)
            changed, v = ui_checkbox("Weak-first##pycons_alc_pref_weak_settings", int(cfg.alcohol_preference) == 2)
            _show_setting_tooltip("alcohol_preference_weak")
            if changed and bool(v):
                cfg.alcohol_preference = 2
                cfg.mark_dirty()

            PyImGui.separator()

        if ui_collapsing_header("Morale Boost & Death Penalty settings##pycons_settings_mbdp_dropdown", False):
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

        if ui_collapsing_header("MB/DP Presets##pycons_settings_presets_dropdown", False):
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

        if ui_collapsing_header("Select consumables to show in the main window##pycons_settings_consumables_dropdown", False):
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
            outpost_items = [c for c in CONSUMABLES if c.get("use_where") == "outpost"]
            mbdp_items = list(MB_DP_ITEMS)
            alcohol_items = list(ALCOHOL_ITEMS)

            explorable_has_match = search_active and (_list_has_match(explorable_consets, flt) or _list_has_match(explorable_other, flt))
            outpost_has_match = search_active and _list_has_match(outpost_items, flt)
            mbdp_has_match = search_active and _list_has_match(mbdp_items, flt)
            alcohol_has_match = search_active and _list_has_match(alcohol_items, flt)

            predicted_visible = int(last_visible_count[0])
            if collapse_now:
                predicted_visible = 0
            elif search_active and (explorable_has_match or outpost_has_match or mbdp_has_match or alcohol_has_match):
                predicted_visible = 1

            pending_select_visible = False
            pending_clear_visible = False
            pending_expand_all = False
            pending_collapse_all = False

            disabled_top = (predicted_visible == 0)
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
            PyImGui.separator()

            conset_has_match = search_active and _list_has_match(explorable_consets, flt)
            only_available_settings = bool(cfg.only_show_available_inventory)
            if only_available_settings:
                _refresh_inventory_cache(False)

            if pending_expand_all:
                explorable_force = True
                outpost_force = True
                mbdp_force = True
                alcohol_force = True
            elif pending_collapse_all:
                explorable_force = False
                outpost_force = False
                mbdp_force = False
                alcohol_force = False
            else:
                explorable_force = False if collapse_now else (True if explorable_has_match else (False if search_active else None))
                outpost_force = False if collapse_now else (True if outpost_has_match else (False if search_active else None))
                mbdp_force = False if collapse_now else (True if mbdp_has_match else (False if search_active else None))
                alcohol_force = False if collapse_now else (True if alcohol_has_match else (False if search_active else None))

            visible_regular_keys = []
            visible_alcohol_keys = []

            def _draw_explorable_category():
                explorable_open = _collapsing_header_force(
                    "Explorable##pycons_hdr_explorable",
                    force_open=explorable_force,
                    default_open=bool(cfg.settings_explorable_open),
                )
                if bool(cfg.settings_explorable_open) != bool(explorable_open):
                    cfg.settings_explorable_open = bool(explorable_open)
                    cfg.mark_dirty()
                if explorable_open:
                    before_explorable = len(visible_regular_keys)
                    if (not search_active) or conset_has_match:
                        PyImGui.text("Conset:")
                    for spec in explorable_consets:
                        _draw_settings_row(spec, flt, visible_regular_keys, only_available=only_available_settings)

                    if (not search_active) or _list_has_match(explorable_other, flt):
                        PyImGui.separator()

                    for spec in explorable_other:
                        _draw_settings_row(spec, flt, visible_regular_keys, only_available=only_available_settings)

                    if only_available_settings and len(visible_regular_keys) == before_explorable:
                        PyImGui.text_disabled("No available items.")

                    PyImGui.separator()

            def _draw_mbdp_category():
                mbdp_open = _collapsing_header_force(
                    "Morale Boost & Death Penalty##pycons_hdr_mbdp",
                    force_open=mbdp_force,
                    default_open=bool(cfg.settings_mbdp_open),
                )
                if bool(cfg.settings_mbdp_open) != bool(mbdp_open):
                    cfg.settings_mbdp_open = bool(mbdp_open)
                    cfg.mark_dirty()
                if mbdp_open:
                    before_mbdp = len(visible_regular_keys)
                    mbdp_party_keys = {
                        "elixir_of_valor",
                        "four_leaf_clover",
                        "honeycomb",
                        "oath_of_purity",
                        "powerstone_of_courage",
                        "rainbow_candy_cane",
                    }
                    mbdp_self_keys = {
                        "peppermint_candy_cane",
                        "pumpkin_cookie",
                        "refined_jelly",
                        "seal_of_the_dragon_empire",
                        "wintergreen_candy_cane",
                    }

                    mbdp_by_key = {str(s.get("key", "")): s for s in mbdp_items}
                    party_specs = [mbdp_by_key[k] for k in mbdp_party_keys if k in mbdp_by_key]
                    self_specs = [mbdp_by_key[k] for k in mbdp_self_keys if k in mbdp_by_key]
                    unmapped_specs = [s for s in mbdp_items if str(s.get("key", "")) not in mbdp_party_keys and str(s.get("key", "")) not in mbdp_self_keys]

                    missing_party_keys = sorted([k for k in mbdp_party_keys if k not in mbdp_by_key])
                    missing_self_keys = sorted([k for k in mbdp_self_keys if k not in mbdp_by_key])

                    PyImGui.text("Party:")
                    for spec in sorted(party_specs, key=lambda x: str(x.get("label", "")).lower()):
                        _draw_settings_row(spec, flt, visible_regular_keys, only_available=only_available_settings)

                    if missing_party_keys:
                        PyImGui.text_disabled("Missing mapped party keys: " + ", ".join(missing_party_keys))

                    PyImGui.separator()
                    PyImGui.text("Self:")
                    for spec in sorted(self_specs, key=lambda x: str(x.get("label", "")).lower()):
                        _draw_settings_row(spec, flt, visible_regular_keys, only_available=only_available_settings)

                    if missing_self_keys:
                        PyImGui.text_disabled("Missing mapped self keys: " + ", ".join(missing_self_keys))

                    if unmapped_specs:
                        PyImGui.separator()
                        PyImGui.text("Unmapped:")
                        for spec in sorted(unmapped_specs, key=lambda x: str(x.get("label", "")).lower()):
                            _draw_settings_row(spec, flt, visible_regular_keys, only_available=only_available_settings)
                    if only_available_settings and len(visible_regular_keys) == before_mbdp:
                        PyImGui.text_disabled("No available items.")

            def _draw_outpost_category():
                outpost_open = _collapsing_header_force(
                    "In-town speed boosts##pycons_hdr_outpost",
                    force_open=outpost_force,
                    default_open=bool(cfg.settings_outpost_open),
                )
                if bool(cfg.settings_outpost_open) != bool(outpost_open):
                    cfg.settings_outpost_open = bool(outpost_open)
                    cfg.mark_dirty()
                if outpost_open:
                    before_outpost = len(visible_regular_keys)
                    for spec in outpost_items:
                        _draw_settings_row(spec, flt, visible_regular_keys, only_available=only_available_settings)
                    if only_available_settings and len(visible_regular_keys) == before_outpost:
                        PyImGui.text_disabled("No available items.")

            def _draw_alcohol_category():
                alcohol_open = _collapsing_header_force(
                    "Alcohol##pycons_hdr_alcohol",
                    force_open=alcohol_force,
                    default_open=bool(cfg.settings_alcohol_open),
                )
                if bool(cfg.settings_alcohol_open) != bool(alcohol_open):
                    cfg.settings_alcohol_open = bool(alcohol_open)
                    cfg.mark_dirty()
                if alcohol_open:
                    before_alcohol = len(visible_alcohol_keys)
                    for spec in sorted(alcohol_items, key=lambda x: x.get("label", "")):
                        _draw_alcohol_settings_row(spec, flt, visible_alcohol_keys, only_available=only_available_settings)
                    if only_available_settings and len(visible_alcohol_keys) == before_alcohol:
                        PyImGui.text_disabled("No available items.")

            category_renderers = {
                "explorable": _draw_explorable_category,
                "mbdp": _draw_mbdp_category,
                "outpost": _draw_outpost_category,
                "alcohol": _draw_alcohol_category,
            }
            category_keys = _ordered_consumable_category_keys(list(category_renderers.keys()))
            for category_key in category_keys:
                renderer = category_renderers.get(category_key)
                if callable(renderer):
                    renderer()

            visible_count = len(visible_regular_keys) + len(visible_alcohol_keys)
            last_visible_count[0] = int(visible_count)

            if visible_count > 0:
                if pending_select_visible:
                    any_new = False
                    for k in visible_regular_keys:
                        if not bool(cfg.selected.get(k, False)):
                            cfg.selected[k] = True
                            _rt.runtime_selected[k] = True
                            any_new = True
                    for k in visible_alcohol_keys:
                        if not bool(cfg.alcohol_selected.get(k, False)):
                            cfg.alcohol_selected[k] = True
                            _rt.runtime_alcohol_selected[k] = True
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
                    for k in visible_alcohol_keys:
                        cfg.alcohol_selected[k] = False
                        cfg.alcohol_enabled_items[k] = False
                        _rt.runtime_alcohol_selected[k] = False
                        _rt.runtime_alcohol_enabled[k] = False

                    if not _any_selected_anywhere():
                        cfg.show_selected_list = False
                        request_collapse_selected[0] = True

                    cfg.mark_dirty()
        else:
            last_visible_count[0] = 0

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

        _draw_main_window()
        _draw_settings_window()

        cfg.save_if_dirty_throttled(750)

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
