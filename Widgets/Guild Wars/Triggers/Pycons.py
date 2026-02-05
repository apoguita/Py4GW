# ============================================================
# Pycons.py - FPS-optimized widget
# - Inventory scan ONLY when we are about to consume
# - Inventory results cached briefly (default 1.5s) to avoid back-to-back scans
# - Skill IDs cached (lazy-resolved + retry if cache isn't ready yet)
# - INI writes only when config changes (throttled)
# - ALWAYS requires MapValid before consuming (no UI toggle)
#
# Hard "do not consume" gates:
# - Do not consume while dead
# - Do not consume while loading / zoning
# - Do not consume while inventory UI is not ready
#
# UI:
# - Green ON badge + Settings grouped (Explorable/Outpost/Alcohol dropdowns, Conset on top)
# - Search auto-opens matching dropdown + shows only matches
# - Search clear collapses dropdowns (shows nothing)
# - Select/Clear all visible only affects visible rows
# - Selected list auto-expands on selection and auto-collapses when nothing selected
#
# Alcohol-specific polish
# - Alcohol enabled toggle + Target drunk level (0..5)
# - Alcohol usage checkboxes: Explorable / Outpost (check both if you want both)
# - "Now" uses real drunk level when API exists (fallback: time-based estimate)
# - Alcohol preference: Smooth / Strong-first / Weak-first
#
# Low stock status (main window):
# - Shows "—" if unknown (no recent scan)
# - Shows "0" if last scan saw none
# - Shows count if last scan saw some
# ============================================================

# ---- REQUIRED BY WIDGET HANDLER (define immediately) ----
def configure():
    pass

def main():
    return

__all__ = ["main", "configure"]

_INIT_OK = False
_INIT_ERROR = None

try:
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
    )
    from Py4GWCoreLib import ItemArray, Bag, Item, Effects, Player

    BOT_NAME = "Pycons"
    INI_SECTION = "Pycons"

    MIN_INTERVAL_MS = 250
    DEFAULT_INTERNAL_COOLDOWN_MS = 5000
    AFTERCAST_MS = 350

    # Brief cache so multiple "due" items don't rescan bags back-to-back
    INVENTORY_CACHE_MS = 1500

    # Fallback durations (ms) for items that cannot resolve effect IDs:
    FALLBACK_SHORT_MS = 10 * 60 * 1000
    FALLBACK_MEDIUM_MS = 20 * 60 * 1000
    FALLBACK_LONG_MS = 30 * 60 * 1000

    # Scan only these bags, and only on-demand
    SCAN_BAGS = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2]

    # -------------------------
    # UI helpers (tuple/non-tuple returns)
    # -------------------------
    def ui_input_int(label: str, value: int):
        res = PyImGui.input_int(label, int(value))
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
            if hasattr(PyImGui, "begin_disabled"):
                try:
                    PyImGui.begin_disabled(True)
                except Exception:
                    PyImGui.begin_disabled()
                return "begin_disabled"
        except Exception:
            pass
        try:
            if hasattr(PyImGui, "push_item_flag") and hasattr(PyImGui, "ImGuiItemFlags") and hasattr(PyImGui.ImGuiItemFlags, "Disabled"):
                PyImGui.push_item_flag(PyImGui.ImGuiItemFlags.Disabled, True)
                try:
                    PyImGui.push_style_var(PyImGui.ImGuiStyleVar.Alpha, 0.5)
                    return "flag+alpha"
                except Exception:
                    return "flag"
        except Exception:
            pass
        try:
            PyImGui.push_style_var(PyImGui.ImGuiStyleVar.Alpha, 0.5)
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
                PyImGui.pop_item_flag()
            except Exception:
                pass
        elif mode == "flag":
            try:
                PyImGui.pop_item_flag()
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
        try:
            fn_hover = getattr(PyImGui, "is_item_hovered", None)
            if callable(fn_hover) and fn_hover():
                fn_tip = getattr(PyImGui, "set_tooltip", None)
                if callable(fn_tip):
                    fn_tip(str(text))
                    return
                bt = getattr(PyImGui, "begin_tooltip", None)
                et = getattr(PyImGui, "end_tooltip", None)
                if callable(bt) and callable(et):
                    bt()
                    if hasattr(PyImGui, "text_wrapped"):
                        PyImGui.text_wrapped(str(text))
                    else:
                        PyImGui.text(str(text))
                    et()
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
        {"key": "honeycomb", "label": "Honeycomb", "model_id": int(ModelID.Honeycomb.value), "skills": ["Honeycomb_skill", "Honeycomb_item_effect", "Honeycomb"], "use_where": "explorable"},
        {"key": "pahnai_salad", "label": "Pahnai Salad", "model_id": int(ModelID.Pahnai_Salad.value), "skills": ["Pahnai_Salad_item_effect"], "use_where": "explorable"},
        {"key": "pumpkin_cookie", "label": "Pumpkin Cookie", "model_id": int(_model_id_value("Pumpkin_Cookie", 0)), "skills": ["Pumpkin_Cookie_skill"], "use_where": "explorable"},
        {"key": "red_rock_candy", "label": "Red Rock Candy", "model_id": int(_model_id_value("Red_Rock_Candy", 0)), "skills": ["Red_Rock_Candy_Rush"], "use_where": "explorable", "require_effect_id": True},
        {"key": "slice_of_pumpkin_pie", "label": "Slice of Pumpkin Pie", "model_id": int(ModelID.Slice_Of_Pumpkin_Pie.value), "skills": ["Pie_Induced_Ecstasy"], "use_where": "explorable"},
        {"key": "war_supplies", "label": "War Supplies", "model_id": int(ModelID.War_Supplies.value), "skills": ["Well_Supplied"], "use_where": "explorable"},

        # Outpost-only (alphabetical by label)
        {"key": "chocolate_bunny", "label": "Chocolate Bunny (Outpost)", "model_id": int(_model_id_value("Chocolate_Bunny", 0)), "skills": ["Sugar_Jolt_(long)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_LONG_MS},
        {"key": "creme_brulee", "label": "Crème Brûlée (Outpost)", "model_id": int(_model_id_value("Creme_Brulee", 0)), "skills": ["Sugar_Jolt_(long)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_LONG_MS},
        {"key": "fruitcake", "label": "Fruitcake (Outpost)", "model_id": int(_model_id_value("Fruitcake", 0)), "skills": ["Sugar_Rush_(medium)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_MEDIUM_MS},
        {"key": "jar_of_honey", "label": "Jar of Honey (Outpost)", "model_id": int(_model_id_value("Jar_Of_Honey", 0)), "skills": ["Sugar_Rush_(long)"], "use_where": "outpost", "require_effect_id": False, "fallback_duration_ms": FALLBACK_LONG_MS},
        {"key": "red_bean_cake", "label": "Red Bean Cake (Outpost)", "model_id": int(_model_id_value("Red_Bean_Cake", 0)), "skills": ["Sugar_Rush_(medium)"], "use_where": "outpost", "require_effect_id": True, "fallback_duration_ms": FALLBACK_MEDIUM_MS},
        {"key": "sugary_blue_drink", "label": "Sugary Blue Drink (Outpost)", "model_id": int(_model_id_value("Sugary_Blue_Drink", 0)), "skills": ["Sugar_Jolt_(short)"], "use_where": "outpost", "require_effect_id": False, "fallback_duration_ms": FALLBACK_SHORT_MS},
    ]

    ALL_BY_KEY = {c["key"]: c for c in CONSUMABLES}
    CONSET_KEYS = {"armor_of_salvation", "essence_of_celerity", "grail_of_might"}

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
    ini_handler = IniHandler("Widgets/Config/Pycons.ini")
    # -------------------------
    # Window position persistence (main + settings)
    # -------------------------
    _WIN_MAIN_X_KEY = "window_main_x"
    _WIN_MAIN_Y_KEY = "window_main_y"
    _WIN_SETTINGS_X_KEY = "window_settings_x"
    _WIN_SETTINGS_Y_KEY = "window_settings_y"

    _saved_main_pos = (
        int(ini_handler.read_int(INI_SECTION, _WIN_MAIN_X_KEY, -1)),
        int(ini_handler.read_int(INI_SECTION, _WIN_MAIN_Y_KEY, -1)),
    )
    _saved_settings_pos = (
        int(ini_handler.read_int(INI_SECTION, _WIN_SETTINGS_X_KEY, -1)),
        int(ini_handler.read_int(INI_SECTION, _WIN_SETTINGS_Y_KEY, -1)),
    )

    _applied_main_pos = False
    _applied_settings_pos = False

    _pos_save_timer = Timer()
    _pos_save_timer.Start()
    _pos_save_timer.Stop()

    _last_main_pos = _saved_main_pos
    _last_settings_pos = _saved_settings_pos

    def _imgui_set_next_window_pos(x: int, y: int) -> bool:
        fn = None
        for nm in ("set_next_window_pos", "set_next_window_position"):
            cand = getattr(PyImGui, nm, None)
            if callable(cand):
                fn = cand
                break
        if not fn:
            return False

        # Prefer "Always" so it restores every load, but we apply it only once per run.
        cond = getattr(PyImGui, "ImGuiCond_Always", None)

        for args in (
            (float(x), float(y), cond),
            (float(x), float(y)),
            ((float(x), float(y)), cond),
            ((float(x), float(y)),),
        ):
            try:
                # Some bindings don't like passing None as cond
                if len(args) == 3 and args[2] is None:
                    continue
                fn(*args)
                return True
            except Exception:
                continue
        return False

    def _imgui_get_window_pos():
        for nm in ("get_window_pos", "get_window_position"):
            fn = getattr(PyImGui, nm, None)
            if callable(fn):
                try:
                    return fn()
                except Exception:
                    continue
        return None

    def _apply_saved_window_pos(is_settings: bool):
        global _applied_main_pos, _applied_settings_pos
        if is_settings:
            if _applied_settings_pos:
                return
            x, y = _saved_settings_pos
            if int(x) >= 0 and int(y) >= 0:
                _imgui_set_next_window_pos(int(x), int(y))
            _applied_settings_pos = True
            return

        if _applied_main_pos:
            return
        x, y = _saved_main_pos
        if int(x) >= 0 and int(y) >= 0:
            _imgui_set_next_window_pos(int(x), int(y))
        _applied_main_pos = True

    def _capture_and_save_window_pos(is_settings: bool):
        global _last_main_pos, _last_settings_pos, _pos_save_timer
        pos = _imgui_get_window_pos()
        if not pos:
            return

        try:
            x = int(pos[0])
            y = int(pos[1])
        except Exception:
            return

        # Only write if it actually moved, and throttle writes.
        if not (_pos_save_timer.IsStopped() or _pos_save_timer.HasElapsed(500)):
            return

        if is_settings:
            if (x, y) == tuple(_last_settings_pos):
                return
            _last_settings_pos = (x, y)
            ini_handler.write_key(INI_SECTION, _WIN_SETTINGS_X_KEY, str(int(x)))
            ini_handler.write_key(INI_SECTION, _WIN_SETTINGS_Y_KEY, str(int(y)))
        else:
            if (x, y) == tuple(_last_main_pos):
                return
            _last_main_pos = (x, y)
            ini_handler.write_key(INI_SECTION, _WIN_MAIN_X_KEY, str(int(x)))
            ini_handler.write_key(INI_SECTION, _WIN_MAIN_Y_KEY, str(int(y)))

        _pos_save_timer.Start()

    class Config:
        def __init__(self):
            self.debug_logging = ini_handler.read_bool(INI_SECTION, "debug_logging", False)
            self.interval_ms = ini_handler.read_int(INI_SECTION, "interval_ms", 1500)
            self.show_selected_list = ini_handler.read_bool(INI_SECTION, "show_selected_list", True)

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
            for c in CONSUMABLES:
                k = c["key"]
                self.selected[k] = ini_handler.read_bool(INI_SECTION, f"selected_{k}", False)
                self.enabled[k] = ini_handler.read_bool(INI_SECTION, f"enabled_{k}", False)

            self.alcohol_selected = {}
            self.alcohol_enabled_items = {}
            for a in ALCOHOL_ITEMS:
                k = a["key"]
                self.alcohol_selected[k] = ini_handler.read_bool(INI_SECTION, f"alcohol_selected_{k}", False)
                self.alcohol_enabled_items[k] = ini_handler.read_bool(INI_SECTION, f"alcohol_enabled_{k}", False)

            self._dirty = False
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

            ini_handler.write_key(INI_SECTION, "debug_logging", str(bool(self.debug_logging)))
            ini_handler.write_key(INI_SECTION, "interval_ms", str(int(self.interval_ms)))
            ini_handler.write_key(INI_SECTION, "show_selected_list", str(bool(self.show_selected_list)))

            ini_handler.write_key(INI_SECTION, "show_advanced_intervals", str(bool(self.show_advanced_intervals)))
            for k, v in self.min_interval_ms.items():
                ini_handler.write_key(INI_SECTION, f"min_interval_{k}", str(int(max(0, int(v)))))

            ini_handler.write_key(INI_SECTION, "alcohol_enabled", str(bool(self.alcohol_enabled)))
            ini_handler.write_key(INI_SECTION, "alcohol_target_level", str(int(self.alcohol_target_level)))
            ini_handler.write_key(INI_SECTION, "alcohol_use_explorable", str(bool(self.alcohol_use_explorable)))
            ini_handler.write_key(INI_SECTION, "alcohol_use_outpost", str(bool(self.alcohol_use_outpost)))
            ini_handler.write_key(INI_SECTION, "alcohol_preference", str(int(self.alcohol_preference)))

            for k, v in self.alcohol_selected.items():
                ini_handler.write_key(INI_SECTION, f"alcohol_selected_{k}", str(bool(v)))
            for k, v in self.alcohol_enabled_items.items():
                ini_handler.write_key(INI_SECTION, f"alcohol_enabled_{k}", str(bool(v)))

            for k, v in self.selected.items():
                ini_handler.write_key(INI_SECTION, f"selected_{k}", str(bool(v)))
            for k, v in self.enabled.items():
                ini_handler.write_key(INI_SECTION, f"enabled_{k}", str(bool(v)))

            self._dirty = False

    cfg = Config()

    # -------------------------
    # Runtime state
    # -------------------------
    show_settings = [False]
    filter_text = [""]
    last_search_active = [False]
    last_visible_count = [0]

    request_expand_selected = [False]
    request_collapse_selected = [False]

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

    # Alcohol estimate fallback
    _alcohol_last_drink_ms = 0
    _alcohol_level_base = 0

    # Inventory caching + stock counts
    _inv_cache_items = None
    _inv_cache_ts = 0
    _inv_counts_by_model = {}
    _inv_ready_cached = True
    _inv_ready_ts = 0

    def _now_ms() -> int:
        import time
        return int(time.time() * 1000)

    def _timer_for(key: str) -> Timer:
        t = internal_timers.get(key)
        if t is None:
            t = Timer()
            t.Start()
            t.Stop()
            internal_timers[key] = t
        return t

    def _retry_timer_for(key: str) -> Timer:
        t = _skill_retry_timer.get(key)
        if t is None:
            t = Timer()
            t.Start()
            t.Stop()
            _skill_retry_timer[key] = t
        return t

    def _warn_timer_for(key: str) -> Timer:
        t = _warn_timer.get(key)
        if t is None:
            t = Timer()
            t.Start()
            t.Stop()
            _warn_timer[key] = t
        return t

    def _enabled_selected_keys():
        return [k for k in cfg.enabled.keys() if cfg.selected.get(k, False) and cfg.enabled.get(k, False)]

    def _alcohol_pool_keys():
        out = []
        for k, sel in cfg.alcohol_selected.items():
            if sel and bool(cfg.alcohol_enabled_items.get(k, False)):
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
                except Exception:
                    continue
                counts[mid] = int(counts.get(mid, 0)) + 1
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
            if key == "honeycomb":
                for _ in range(4):
                    GLOBAL_CACHE.Inventory.UseItem(int(item_id))
                return True
            GLOBAL_CACHE.Inventory.UseItem(int(item_id))
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

    # -------------------------
    # Tick: normal consumables
    # -------------------------
    def _tick_consume() -> bool:
        keys = _enabled_selected_keys()
        if not keys:
            return False

        if not Routines.Checks.Map.MapValid():
            return False

        if _should_block_consumption():
            return False

        if not (aftercast_timer.IsStopped() or aftercast_timer.HasElapsed(int(AFTERCAST_MS))):
            return False

        in_explorable = bool(_in_explorable())

        for key in keys:
            spec = ALL_BY_KEY.get(key)
            if not spec:
                continue

            if not _allowed_here(spec, in_explorable):
                continue

            effect_id = _resolve_effect_id_for(key, spec)

            if effect_id and _has_effect(effect_id):
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
                return True

        return False

    # -------------------------
    # Tick: alcohol upkeep
    # -------------------------
    def _tick_alcohol() -> bool:
        if not bool(cfg.alcohol_enabled):
            return False
        target = int(cfg.alcohol_target_level)
        if target <= 0:
            return False

        if not bool(cfg.alcohol_use_explorable) and not bool(cfg.alcohol_use_outpost):
            return False

        if not Routines.Checks.Map.MapValid():
            return False

        if _should_block_consumption():
            return False

        if not (aftercast_timer.IsStopped() or aftercast_timer.HasElapsed(int(AFTERCAST_MS))):
            return False

        pool_keys = _alcohol_pool_keys()
        if not pool_keys:
            return False

        in_explorable = bool(_in_explorable())
        if not _alcohol_allowed_here(in_explorable):
            return False

        now = _now_ms()
        cur_level = _alcohol_current_level(now)
        if cur_level >= target:
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
            return True

        return False

    def _draw_main_row_checkbox_and_badge(key: str, label: str, enabled_now: bool, id_prefix: str):
        _, enabled = ui_checkbox(f"##{id_prefix}_cb_{key}", bool(enabled_now))
        _same_line(10)
        PyImGui.text(label)
        _same_line(12)
        if _badge_button("ON" if enabled else "OFF", enabled=bool(enabled), id_suffix=f"{id_prefix}_btn_{key}"):
            enabled = not enabled
        changed = (bool(enabled_now) != bool(enabled))
        return bool(enabled), bool(changed)

    def _stock_suffix_for_model_id(model_id: int) -> str:
        known, cnt = _stock_status_for_model_id(int(model_id))
        if not known:
            return " —"
        return f" {int(cnt)}"

    # -------------------------
    # Main Window
    # -------------------------
    def _draw_main_window():
        _apply_saved_window_pos(is_settings=False)
        if not PyImGui.begin(BOT_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
            PyImGui.end()
            return

        _capture_and_save_window_pos(is_settings=False)

        if PyImGui.button("Settings##pycons_settings"):
            show_settings[0] = not show_settings[0]

        _same_line(10)
        if PyImGui.button("Enable all##pycons_enable_all"):
            for c in CONSUMABLES:
                k = c["key"]
                if cfg.selected.get(k, False):
                    cfg.enabled[k] = True
            for a in ALCOHOL_ITEMS:
                k = a["key"]
                if cfg.alcohol_selected.get(k, False):
                    cfg.alcohol_enabled_items[k] = True
            cfg.mark_dirty()

        _same_line(10)
        if PyImGui.button("Disable all##pycons_disable_all"):
            for c in CONSUMABLES:
                k = c["key"]
                if cfg.selected.get(k, False):
                    cfg.enabled[k] = False
            for a in ALCOHOL_ITEMS:
                k = a["key"]
                if cfg.alcohol_selected.get(k, False):
                    cfg.alcohol_enabled_items[k] = False
            cfg.mark_dirty()

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
            selected_explorable_conset = [c for c in CONSUMABLES if c.get("use_where") == "explorable" and c.get("key") in CONSET_KEYS and cfg.selected.get(c["key"], False)]
            selected_explorable_other = [c for c in CONSUMABLES if c.get("use_where") == "explorable" and c.get("key") not in CONSET_KEYS and cfg.selected.get(c["key"], False)]
            selected_outpost = [c for c in CONSUMABLES if c.get("use_where") == "outpost" and cfg.selected.get(c["key"], False)]
            selected_alcohol = [a for a in ALCOHOL_ITEMS if cfg.alcohol_selected.get(a["key"], False)]

            any_selected = bool(selected_explorable_conset or selected_explorable_other or selected_outpost or selected_alcohol)
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
                                k, c["label"] + suffix, bool(cfg.enabled.get(k, False)), "pycons"
                            )
                            if chg:
                                cfg.enabled[k] = bool(new_enabled)
                                cfg.mark_dirty()
                        PyImGui.separator()

                    for c in selected_explorable_other:
                        k = c["key"]
                        suffix = _stock_suffix_for_model_id(int(c.get("model_id", 0)))
                        new_enabled, chg = _draw_main_row_checkbox_and_badge(
                            k, c["label"] + suffix, bool(cfg.enabled.get(k, False)), "pycons"
                        )
                        if chg:
                            cfg.enabled[k] = bool(new_enabled)
                            cfg.mark_dirty()
                    PyImGui.separator()

                if selected_outpost:
                    PyImGui.text("Outpost:")
                    for c in selected_outpost:
                        k = c["key"]
                        suffix = _stock_suffix_for_model_id(int(c.get("model_id", 0)))
                        new_enabled, chg = _draw_main_row_checkbox_and_badge(
                            k, c["label"] + suffix, bool(cfg.enabled.get(k, False)), "pycons"
                        )
                        if chg:
                            cfg.enabled[k] = bool(new_enabled)
                            cfg.mark_dirty()
                    PyImGui.separator()

                if selected_alcohol:
                    PyImGui.text("Alcohol:")
                    for a in sorted(selected_alcohol, key=lambda x: x.get("label", "")):
                        k = a["key"]
                        suffix = _stock_suffix_for_model_id(int(a.get("model_id", 0)))
                        enabled_now = bool(cfg.alcohol_enabled_items.get(k, False))
                        new_enabled, chg = _draw_main_row_checkbox_and_badge(
                            k, _alcohol_display_label(a) + suffix, enabled_now, "pycons_alc"
                        )
                        if chg:
                            cfg.alcohol_enabled_items[k] = bool(new_enabled)
                            cfg.mark_dirty()

        PyImGui.end()

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

    def _draw_settings_row(spec: dict, flt: str, visible_keys_out=None):
        k = spec["key"]
        label = spec["label"]
        if not _matches_filter(label, flt):
            return
        if visible_keys_out is not None:
            visible_keys_out.append(k)

        prev = bool(cfg.selected.get(k, False))
        _, selected = ui_checkbox(f"##pycons_selected_{k}", prev)
        _same_line(10)
        PyImGui.text(label)

        _draw_min_interval_editor(k)

        selected = bool(selected)
        if prev != selected:
            cfg.selected[k] = selected
            if not selected:
                cfg.enabled[k] = False
                if not _any_selected_anywhere():
                    cfg.show_selected_list = False
                    request_collapse_selected[0] = True
            else:
                if not bool(cfg.show_selected_list):
                    cfg.show_selected_list = True
                request_expand_selected[0] = True
            cfg.mark_dirty()

    def _draw_alcohol_settings_row(spec: dict, flt: str, visible_keys_out=None):
        k = spec["key"]
        label = _alcohol_display_label(spec)
        if not _matches_filter(label, flt):
            return
        if visible_keys_out is not None:
            visible_keys_out.append(k)

        prev = bool(cfg.alcohol_selected.get(k, False))
        _, selected = ui_checkbox(f"##pycons_alcohol_selected_{k}", prev)
        _same_line(10)
        PyImGui.text(label)

        selected = bool(selected)
        if prev != selected:
            cfg.alcohol_selected[k] = selected
            if not selected:
                cfg.alcohol_enabled_items[k] = False
                if not _any_selected_anywhere():
                    cfg.show_selected_list = False
                    request_collapse_selected[0] = True
            else:
                if not bool(cfg.show_selected_list):
                    cfg.show_selected_list = True
                request_expand_selected[0] = True
            cfg.mark_dirty()

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
        if not show_settings[0]:
            return

        _apply_saved_window_pos(is_settings=True)

        if not PyImGui.begin("Pycons - Settings##PyconsSettings", PyImGui.WindowFlags.AlwaysAutoResize):
            PyImGui.end()
            return

        _capture_and_save_window_pos(is_settings=True)

        changed, v = ui_checkbox("Debug logging##pycons_debug", bool(cfg.debug_logging))
        if changed:
            cfg.debug_logging = bool(v)
            cfg.mark_dirty()

        changed, v = ui_checkbox("Advanced intervals##pycons_advint", bool(cfg.show_advanced_intervals))
        if changed:
            cfg.show_advanced_intervals = bool(v)
            cfg.mark_dirty()

        # ---- Tooltip (safe, non-breaking) ----
        try:
            hovered = False
            if hasattr(PyImGui, "is_item_hovered"):
                hovered = bool(PyImGui.is_item_hovered())
            if hovered:
                tip = "Leave this off unless you need it (performance tuning, special timing needs, or you want certain items checked less often)."
                if hasattr(PyImGui, "set_tooltip"):
                    PyImGui.set_tooltip(tip)
                elif hasattr(PyImGui, "begin_tooltip") and hasattr(PyImGui, "end_tooltip"):
                    PyImGui.begin_tooltip()
                    if hasattr(PyImGui, "text_wrapped"):
                        PyImGui.text_wrapped(tip)
                    else:
                        PyImGui.text(tip)
                    PyImGui.end_tooltip()
        except Exception:
            pass

        PyImGui.separator()

        PyImGui.text("Search:")
        _same_line(10)
        changed, new_val = ui_input_text("##pycons_filter", filter_text[0], 64)
        if changed:
            filter_text[0] = new_val

        flt = (filter_text[0] or "").strip().lower()
        search_active = bool(flt)

        collapse_now = (last_search_active[0] and not search_active)
        last_search_active[0] = search_active

        PyImGui.dummy(0, 6)

        explorable_consets = [c for c in CONSUMABLES if c.get("use_where") == "explorable" and c.get("key") in CONSET_KEYS]
        explorable_other = [c for c in CONSUMABLES if c.get("use_where") == "explorable" and c.get("key") not in CONSET_KEYS]
        outpost_items = [c for c in CONSUMABLES if c.get("use_where") == "outpost"]
        alcohol_items = list(ALCOHOL_ITEMS)

        explorable_has_match = search_active and (_list_has_match(explorable_consets, flt) or _list_has_match(explorable_other, flt))
        outpost_has_match = search_active and _list_has_match(outpost_items, flt)
        alcohol_has_match = search_active and _list_has_match(alcohol_items, flt)

        predicted_visible = int(last_visible_count[0])
        if collapse_now:
            predicted_visible = 0
        elif search_active and (explorable_has_match or outpost_has_match or alcohol_has_match):
            predicted_visible = 1

        pending_select_visible = False
        pending_clear_visible = False

        disabled_top = (predicted_visible == 0)
        mode = _begin_disabled(disabled_top)

        if PyImGui.button("Select all visible##pycons_sel_all"):
            pending_select_visible = True
        _same_line(10)
        if PyImGui.button("Clear all visible##pycons_clear_all"):
            pending_clear_visible = True

        _end_disabled(mode)

        if disabled_top:
            PyImGui.text_disabled("No visible items (open a dropdown or search).")

        PyImGui.separator()

        # --- Alcohol settings (collapsed dropdown for compactness) ---
        if ui_collapsing_header("Alcohol settings##pycons_settings_alcohol_dropdown", False):
            PyImGui.text("Alcohol upkeep:")
            _same_line(10)
            if _badge_button("ON" if cfg.alcohol_enabled else "OFF", enabled=bool(cfg.alcohol_enabled), id_suffix="pycons_settings_alcohol_toggle"):
                cfg.alcohol_enabled = not bool(cfg.alcohol_enabled)
                cfg.mark_dirty()

            changed, v = ui_checkbox("Use in Explorable##pycons_settings_alc_expl", bool(cfg.alcohol_use_explorable))
            if changed:
                cfg.alcohol_use_explorable = bool(v)
                cfg.mark_dirty()

            changed, v = ui_checkbox("Use in Outpost##pycons_settings_alc_outpost", bool(cfg.alcohol_use_outpost))
            if changed:
                cfg.alcohol_use_outpost = bool(v)
                cfg.mark_dirty()

            PyImGui.text("Target drunk level:")
            _same_line(10)
            changed, vv = ui_input_int("##pycons_alcohol_target", int(cfg.alcohol_target_level))
            if changed:
                cfg.alcohol_target_level = int(max(0, min(5, vv)))
                cfg.mark_dirty()

            # Preference (ONE LINE)
            PyImGui.text("Preference:")
            _same_line(10)

            changed, v = ui_checkbox("Smooth##pycons_alc_pref_smooth_settings", int(cfg.alcohol_preference) == 0)
            _tooltip_if_hovered("Default Best all around. Keeps you near the target without burning high-point alcohol unnecessarily")
            if changed and bool(v):
                cfg.alcohol_preference = 0
                cfg.mark_dirty()

            _same_line(10)
            changed, v = ui_checkbox("Strong-first##pycons_alc_pref_strong_settings", int(cfg.alcohol_preference) == 1)
            _tooltip_if_hovered("Good when you just want to be drunk ASAP (e.g., you zone in and want max level quickly)")
            if changed and bool(v):
                cfg.alcohol_preference = 1
                cfg.mark_dirty()

            _same_line(10)
            changed, v = ui_checkbox("Weak-first##pycons_alc_pref_weak_settings", int(cfg.alcohol_preference) == 2)
            _tooltip_if_hovered("Good if you are trying to stretch rare/valuable alcohol and do not mind it taking longer to climb")
            if changed and bool(v):
                cfg.alcohol_preference = 2
                cfg.mark_dirty()

            PyImGui.separator()

        PyImGui.separator()
        PyImGui.text("Select consumables to show in the main window:")
        PyImGui.separator()

        conset_has_match = search_active and _list_has_match(explorable_consets, flt)

        explorable_force = False if collapse_now else (True if explorable_has_match else (False if search_active else None))
        outpost_force = False if collapse_now else (True if outpost_has_match else (False if search_active else None))
        alcohol_force = False if collapse_now else (True if alcohol_has_match else (False if search_active else None))

        visible_regular_keys = []
        visible_alcohol_keys = []

        explorable_open = _collapsing_header_force("Explorable##pycons_hdr_explorable", force_open=explorable_force, default_open=False)
        if explorable_open:
            if (not search_active) or conset_has_match:
                PyImGui.text("Conset:")
            for spec in explorable_consets:
                _draw_settings_row(spec, flt, visible_regular_keys)

            if (not search_active) or _list_has_match(explorable_other, flt):
                PyImGui.separator()

            for spec in explorable_other:
                _draw_settings_row(spec, flt, visible_regular_keys)

            PyImGui.separator()

        outpost_open = _collapsing_header_force("Outpost##pycons_hdr_outpost", force_open=outpost_force, default_open=False)
        if outpost_open:
            for spec in outpost_items:
                _draw_settings_row(spec, flt, visible_regular_keys)

        alcohol_open = _collapsing_header_force("Alcohol##pycons_hdr_alcohol", force_open=alcohol_force, default_open=False)
        if alcohol_open:
            for spec in sorted(alcohol_items, key=lambda x: x.get("label", "")):
                _draw_alcohol_settings_row(spec, flt, visible_alcohol_keys)

        visible_count = len(visible_regular_keys) + len(visible_alcohol_keys)
        last_visible_count[0] = int(visible_count)

        if visible_count > 0:
            if pending_select_visible:
                any_new = False
                for k in visible_regular_keys:
                    if not bool(cfg.selected.get(k, False)):
                        cfg.selected[k] = True
                        any_new = True
                for k in visible_alcohol_keys:
                    if not bool(cfg.alcohol_selected.get(k, False)):
                        cfg.alcohol_selected[k] = True
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
                for k in visible_alcohol_keys:
                    cfg.alcohol_selected[k] = False
                    cfg.alcohol_enabled_items[k] = False

                if not _any_selected_anywhere():
                    cfg.show_selected_list = False
                    request_collapse_selected[0] = True

                cfg.mark_dirty()

        PyImGui.end()

    def configure():
        pass

    def main():
        _draw_main_window()
        _draw_settings_window()

        cfg.save_if_dirty_throttled(750)

        if tick_timer.HasElapsed(int(max(MIN_INTERVAL_MS, cfg.interval_ms))):
            tick_timer.Start()
            used = _tick_consume()
            if not used:
                _tick_alcohol()

    __all__ = ["main", "configure"]
    _INIT_OK = True

except Exception as e:
    _INIT_OK = False
    _INIT_ERROR = e
    try:
        ConsoleLog("Pycons", f"Init failed: {e}", Console.MessageType.Error)
    except Exception:
        pass
