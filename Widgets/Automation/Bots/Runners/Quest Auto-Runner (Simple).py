"""
Quest Auto-Runner (Simple)

- Follows active quest marker using AutoPathing + FollowPath
- Pauses movement for combat/looting/party safety so AutoCombat can engage

UI:
- Main window (Start/Stop, Settings, Consumables)
  - Compact width forced
  - Enabled consumables list is a dropdown (collapsible)
- Settings window (Debug Logging, HeroAI)
- Consumables window:
  - Search/filter box
  - Select All Visible / Clear All Visible
  - Multi-select consumables + consets
  - Restock disabled (consume only)

Notes:
- HeroAI applied live.
- Consumables upkeep applied live (no restart), using Multibox._use_consumable_message when possible.
"""

import os
import time
import PyImGui

from Py4GWCoreLib import (
    Botting,
    Quest,
    Map,
    ConsoleLog,
    Console,
    Routines,
    IniHandler,
    Timer,
    GLOBAL_CACHE,
    ModelID,
    ImGui, Color,
)
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.enums import SharedCommandType
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5


BOT_NAME = "Quest Auto-Runner (Simple)"
MARKER_UPDATE_TIMEOUT_S = 20.0
MARKER_POLL_INTERVAL_S = 1.0

SYNC_INTERVAL_MS = 1000

# Compact width (your tuned value)
DEFAULT_MAIN_WINDOW_WIDTH = 280.0


# -------------------------
# Helpers
# -------------------------
def _same_line(spacing=8.0):
    PyImGui.same_line(0.0, float(spacing))


def _set_next_window_fixed_width(width):
    """
    Force width every frame. Height stays auto.
    ImGuiCond_Always is typically 1; we pass 1 directly.
    """
    try:
        PyImGui.set_next_window_size(float(width), 0.0, 1)
    except TypeError:
        try:
            PyImGui.set_next_window_size(float(width), 0.0)
        except Exception:
            pass
    except Exception:
        pass


def _draw_badge(text, enabled=True):
    """
    Green ON / Grey OFF pill.
    """
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
        PyImGui.small_button(f" {text} ")
        PyImGui.pop_style_color(3)
    except Exception:
        PyImGui.text(f"[{text}]")


def _model_id_value(name: str, default: int = 0) -> int:
    """
    Safely fetch ModelID.<name>.value.
    If it doesn't exist in your version, returns default.
    """
    try:
        obj = getattr(ModelID, name, None)
        if obj is None:
            return int(default)
        return int(getattr(obj, "value", obj))
    except Exception:
        return int(default)


# -------------------------
# INI
# -------------------------
import Py4GW
try:
    script_directory = Py4GW.Console.get_projects_path()
except NameError:
    script_directory = os.getcwd()

root_directory = Py4GW.Console.get_projects_path()
ini_file_location = os.path.join(root_directory, "Widgets/Config/Quest Auto-Runner.ini")
ini_handler = IniHandler(ini_file_location)

sync_timer = Timer()
sync_timer.Start()


class Config:
    def __init__(self):
        self.debug_logging = ini_handler.read_bool(BOT_NAME, "debug_logging", False)
        self.hero_ai_enabled = ini_handler.read_bool(BOT_NAME, "hero_ai_enabled", False)
        self.show_consumables_list = ini_handler.read_bool(BOT_NAME, "show_consumables_list", False)
        self.consumables_enabled = {}

    def save_throttled(self):
        if not sync_timer.HasElapsed(SYNC_INTERVAL_MS):
            return
        sync_timer.Start()

        ini_handler.write_key(BOT_NAME, "debug_logging", str(bool(self.debug_logging)))
        ini_handler.write_key(BOT_NAME, "hero_ai_enabled", str(bool(self.hero_ai_enabled)))
        ini_handler.write_key(BOT_NAME, "show_consumables_list", str(bool(self.show_consumables_list)))

        for k, v in self.consumables_enabled.items():
            ini_handler.write_key(BOT_NAME, f"consumable_{k}", str(bool(v)))


bot_config = Config()


def DebugLog(msg, message_type=Console.MessageType.Info):
    if bot_config.debug_logging:
        ConsoleLog(BOT_NAME, msg, message_type)


def InfoLog(msg):
    # Always-visible log (helps when debug logging is off)
    ConsoleLog(BOT_NAME, msg, Console.MessageType.Info)


# -------------------------
# Consumables
# -------------------------
MAINTAIN_CONSUMABLES = [
    {"key": "war_supplies", "label": "War Supplies", "model_id": ModelID.War_Supplies.value, "skills": ["Well_Supplied"]},
    {"key": "birthday_cupcake", "label": "Birthday Cupcake", "model_id": ModelID.Birthday_Cupcake.value, "skills": ["Birthday_Cupcake_skill"]},
    {"key": "golden_egg", "label": "Golden Egg", "model_id": ModelID.Golden_Egg.value, "skills": ["Golden_Egg_skill"]},
    {"key": "candy_corn", "label": "Candy Corn", "model_id": ModelID.Candy_Corn.value, "skills": ["Candy_Corn_skill"]},
    {"key": "candy_apple", "label": "Candy Apple", "model_id": ModelID.Candy_Apple.value, "skills": ["Candy_Apple_skill"]},
    {"key": "pumpkin_cookie", "label": "Pumpkin Cookie", "model_id": _model_id_value("Pumpkin_Cookie", 0), "skills": ["Pumpkin_Cookie_skill"]},
    {"key": "pumpkin_pie", "label": "Slice of Pumpkin Pie", "model_id": ModelID.Slice_Of_Pumpkin_Pie.value, "skills": ["Pie_Induced_Ecstasy"]},
    {"key": "drake_kabob", "label": "Drake Kabob", "model_id": ModelID.Drake_Kabob.value, "skills": ["Drake_Skin"]},
    {"key": "skalefin_soup", "label": "Bowl of Skalefin Soup", "model_id": ModelID.Bowl_Of_Skalefin_Soup.value, "skills": ["Skale_Vigor"]},
    {"key": "pahnai_salad", "label": "Pahnai Salad", "model_id": ModelID.Pahnai_Salad.value, "skills": ["Pahnai_Salad_item_effect"]},
    {"key": "honeycomb", "label": "Honeycomb", "model_id": ModelID.Honeycomb.value, "skills": ["Honeycomb_skill", "Honeycomb_item_effect", "Honeycomb"]},
]

CONSETS = [
    {"key": "armor_of_salvation", "label": "Armor of Salvation", "model_id": ModelID.Armor_Of_Salvation.value, "skills": ["Armor_of_Salvation_item_effect"]},
    {"key": "essence_of_celerity", "label": "Essence of Celerity", "model_id": ModelID.Essence_Of_Celerity.value, "skills": ["Essence_of_Celerity_item_effect"]},
    {"key": "grail_of_might", "label": "Grail of Might", "model_id": ModelID.Grail_Of_Might.value, "skills": ["Grail_of_Might_item_effect"]},
]

ALL_CONSUMABLES = MAINTAIN_CONSUMABLES + CONSETS
ALL_BY_KEY = {c["key"]: c for c in ALL_CONSUMABLES}

for c in ALL_CONSUMABLES:
    k = c["key"]
    bot_config.consumables_enabled[k] = ini_handler.read_bool(BOT_NAME, f"consumable_{k}", False)


def _enabled_keys():
    return [k for k, v in bot_config.consumables_enabled.items() if v]


# -------------------------
# Bot init
# -------------------------
bot = Botting(BOT_NAME)
properties = bot.Properties

properties.Enable("pause_on_danger")
properties.Enable("auto_combat")
properties.Enable("auto_loot")
properties.Disable("auto_inventory_management")
properties.Disable("halt_on_death")
properties.Set("movement_timeout", value=-1)


def _apply_hero_ai_live():
    enabled = bool(bot_config.hero_ai_enabled)

    try:
        if hasattr(properties, "ApplyNow"):
            try:
                properties.ApplyNow("hero_ai", "active", enabled)
            except Exception:
                try:
                    properties.ApplyNow("hero_ai", enabled)
                except Exception:
                    pass
    except Exception:
        pass

    try:
        if enabled:
            properties.Enable("hero_ai")
        else:
            properties.Disable("hero_ai")
    except Exception:
        pass


_apply_hero_ai_live()

bot.Events.OnPartyMemberBehindCallback(lambda: bot.Templates.Routines.OnPartyMemberBehind())
bot.Events.OnPartyMemberDeadBehindCallback(lambda: bot.Templates.Routines.OnPartyMemberDeathBehind())


# -------------------------
# Loot check
# -------------------------
def LootingRoutineActive():
    from Py4GWCoreLib.Player import Player
    try:
        account_email = Player.GetAccountEmail()
        index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
        if index == -1 or message is None:
            return False
        return message.Command == SharedCommandType.PickUpLoot
    except Exception:
        return False


# -------------------------
# Consumables upkeep coroutine
# -------------------------
def _coro_upkeep_consumables():
    while True:
        yield from bot.Wait._coro_for_time(1500)

        keys = _enabled_keys()
        if not keys:
            continue

        try:
            if not Routines.Checks.Map.MapValid():
                continue
            if Routines.Checks.Map.IsOutpost():
                continue
        except Exception:
            pass

        for key in keys:
            spec = ALL_BY_KEY.get(key)
            if not spec:
                continue

            model_id = int(spec.get("model_id", 0))
            if model_id <= 0:
                DebugLog(f"Consumable '{spec.get('label', key)}' has no valid model_id in this build; skipping.", Console.MessageType.Warning)
                continue

            skill_names = spec.get("skills", [])
            attempted_multibox = False

            # Preferred: multibox method
            try:
                if hasattr(bot, "helpers") and hasattr(bot.helpers, "Multibox") and hasattr(bot.helpers.Multibox, "_use_consumable_message"):
                    skill_id = 0
                    for nm in skill_names:
                        try:
                            skill_id = int(GLOBAL_CACHE.Skill.GetID(nm))
                        except Exception:
                            skill_id = 0
                        if skill_id:
                            break

                    if skill_id:
                        attempted_multibox = True
                        yield from bot.helpers.Multibox._use_consumable_message((model_id, skill_id, 0, 0))
                        yield from bot.Wait._coro_for_time(150)
            except Exception:
                attempted_multibox = False

            if attempted_multibox:
                continue

            # Fallback: Inventory.UseItem
            try:
                if key == "honeycomb":
                    for _ in range(4):
                        GLOBAL_CACHE.Inventory.UseItem(model_id)
                        yield from bot.Wait._coro_for_time(250)
                else:
                    GLOBAL_CACHE.Inventory.UseItem(model_id)
                    yield from bot.Wait._coro_for_time(150)
            except Exception:
                pass


bot.States.AddManagedCoroutine("Upkeep Consumables", lambda: _coro_upkeep_consumables())


# -------------------------
# Quest marker + navigation
# -------------------------
quest_info = {"marker_x": 0.0, "marker_y": 0.0, "is_valid": False}


def GetQuestData():
    active_quest_id = Quest.GetActiveQuest()
    if active_quest_id == 0:
        raise Exception("No active quest")
    return Quest.GetQuestData(active_quest_id)


def ConvertQuestMarkerCoordinates(quest_data):
    mx = quest_data.marker_x
    my = quest_data.marker_y

    if mx == 2147483648 or my == 2147483648:
        return None
    if mx == 0 and my == 0:
        return None

    if my > 2147483647:
        my = my - 4294967296
    if mx > 2147483647:
        mx = mx - 4294967296

    return float(mx), float(my)


# -------------------------
# MAIN ROUTINE (IMPORTANT: not a generator!)
# -------------------------
def bot_routine(_bot: Botting):
    """
    IMPORTANT:
    This function MUST NOT contain 'yield' anywhere.
    It only registers states. The STATE functions yield.
    """
    _bot.States.AddHeader("Quest Navigation")

    def load_quest_state():
        try:
            InfoLog("Loading quest marker...")
            qd = GetQuestData()
            coords = ConvertQuestMarkerCoordinates(qd)
            if coords is None:
                ConsoleLog(BOT_NAME, "Quest has no valid marker. Make sure the quest is active and has a green star.", Console.MessageType.Error)
                _bot.Stop()
                return
            quest_info["marker_x"], quest_info["marker_y"] = coords
            quest_info["is_valid"] = True

            # Always log this so you can see it even with debug off
            ConsoleLog(BOT_NAME, f"Quest marker: ({quest_info['marker_x']:.0f}, {quest_info['marker_y']:.0f})", Console.MessageType.Info)
        except Exception as e:
            ConsoleLog(BOT_NAME, f"No active quest / marker: {e}", Console.MessageType.Error)
            _bot.Stop()
            return
        yield

    def navigate_state():
        if not quest_info.get("is_valid"):
            ConsoleLog(BOT_NAME, "Quest marker invalid. Stopping.", Console.MessageType.Error)
            return

        marker_x = float(quest_info["marker_x"])
        marker_y = float(quest_info["marker_y"])
        start_map_id = Map.GetMapID()

        InfoLog("Starting navigation to quest marker...")

        loot_hold_until = [0.0]
        combat_hold_until = [0.0]

        def should_pause():
            now = time.time()
            try:
                if _bot.config.FSM.is_paused():
                    return True

                dead_player = Routines.Party.GetDeadPartyMemberID()
                if dead_player != 0:
                    return True

                if LootingRoutineActive():
                    loot_hold_until[0] = now + 0.5
                    return True

                in_danger = False
                try:
                    in_danger = bool(Routines.Checks.Agents.InDanger())
                except Exception:
                    pass

                if in_danger:
                    combat_hold_until[0] = now + 2.0
                    return True

                if loot_hold_until[0] > now or combat_hold_until[0] > now:
                    return True

                return False
            except Exception as e:
                DebugLog(f"should_pause error: {e}", Console.MessageType.Warning)
                return False

        def refresh_marker_from_quest():
            qd = GetQuestData()
            return ConvertQuestMarkerCoordinates(qd)

        def wait_for_next_marker(current_marker):
            start_time = time.time()
            while time.time() - start_time < MARKER_UPDATE_TIMEOUT_S:
                try:
                    qd2 = Quest.GetQuestData(Quest.GetActiveQuest())
                    if qd2.is_completed:
                        return None
                    next_marker = ConvertQuestMarkerCoordinates(qd2)
                except Exception:
                    next_marker = None

                if next_marker is not None and next_marker != current_marker:
                    return next_marker

                yield from Routines.Yield.wait(int(MARKER_POLL_INTERVAL_S * 1000))
            return None

        while True:
            if Map.GetMapID() != start_map_id:
                refreshed = refresh_marker_from_quest()
                if refreshed is None:
                    ConsoleLog(BOT_NAME, "Quest marker missing after map change. Stopping.", Console.MessageType.Error)
                    return
                marker_x, marker_y = refreshed
                start_map_id = Map.GetMapID()
                ConsoleLog(BOT_NAME, f"Updated marker: ({marker_x:.0f}, {marker_y:.0f})", Console.MessageType.Info)

            try:
                path = yield from AutoPathing().get_path_to(marker_x, marker_y)
            except Exception as e:
                DebugLog(f"Pathfinding failed: {e}", Console.MessageType.Warning)
                path = []

            if not path:
                DebugLog("No path returned; retrying...", Console.MessageType.Warning)
                yield from Routines.Yield.wait(1000)
                continue

            DebugLog(f"Following path with {len(path)} waypoints", Console.MessageType.Info)

            success = yield from Routines.Yield.Movement.FollowPath(
                path_points=path,
                tolerance=200,
                timeout=120000,
                custom_pause_fn=should_pause,
            )

            if not success:
                DebugLog("FollowPath returned false; retrying...", Console.MessageType.Warning)
                yield from Routines.Yield.wait(1000)
                continue

            # Reached marker; wait for next marker if it updates
            next_marker = yield from wait_for_next_marker((marker_x, marker_y))
            if next_marker is None:
                ConsoleLog(BOT_NAME, "Arrived at quest marker (no further marker detected).", Console.MessageType.Success)
                break

            marker_x, marker_y = next_marker
            quest_info["marker_x"], quest_info["marker_y"] = marker_x, marker_y
            ConsoleLog(BOT_NAME, f"New quest marker: ({marker_x:.0f}, {marker_y:.0f})", Console.MessageType.Info)

        yield

    _bot.States.AddCustomState(load_quest_state, "Load Quest Marker")
    _bot.States.AddCustomState(navigate_state, "Navigate to Marker")
    _bot.Wait.UntilOutOfCombat()


bot.SetMainRoutine(bot_routine)


# -------------------------
# UI
# -------------------------
show_settings = [False]
show_consumables = [False]
consumable_filter = [""]


def _draw_main_window():
    _set_next_window_fixed_width(DEFAULT_MAIN_WINDOW_WIDTH)

    if not PyImGui.begin(BOT_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    quest_name = "No quest loaded"
    quest_map = "Unknown"
    try:
        active_id = Quest.GetActiveQuest()
        if active_id != 0:
            qd = Quest.GetQuestData(active_id)
            quest_name = qd.name if qd.name else f"Quest #{active_id}"
            quest_map = Map.GetMapName(qd.map_to)
    except Exception:
        pass

    PyImGui.text(BOT_NAME)
    PyImGui.text(quest_name)
    PyImGui.text(f"Target: {quest_map}")
    PyImGui.separator()

    status = "Status: Idle"
    try:
        if bot.config.FSM.is_started():
            status = "Status: Running"
            if getattr(bot.config.FSM, "is_paused", lambda: False)():
                status = "Status: Paused"
    except Exception:
        pass
    PyImGui.text(status)

    PyImGui.separator()

    is_running = False
    try:
        is_running = bool(bot.config.FSM.is_started())
    except Exception:
        pass

    icon = IconsFontAwesome5.ICON_STOP_CIRCLE if is_running else IconsFontAwesome5.ICON_PLAY_CIRCLE
    legend = "  Stop Bot" if is_running else "  Start Bot"

    if PyImGui.button(icon + legend + "##BotToggle"):
        try:
            if is_running:
                bot.Stop()
            else:
                bot.Start()
        except Exception:
            pass

    _same_line(10)
    if PyImGui.button("Settings##btn_settings"):
        show_settings[0] = not show_settings[0]

    _same_line(10)
    if PyImGui.button("Consumables##btn_consumables"):
        show_consumables[0] = not show_consumables[0]

    PyImGui.separator()

    PyImGui.text("HeroAI:")
    _same_line(10)
    _draw_badge("ON" if bot_config.hero_ai_enabled else "OFF", enabled=bot_config.hero_ai_enabled)

    enabled = _enabled_keys()
    PyImGui.text("Consumables:")
    _same_line(10)
    _draw_badge("ON" if enabled else "OFF", enabled=bool(enabled))

    opened = False
    try:
        if hasattr(PyImGui, "collapsing_header"):
            opened = bool(PyImGui.collapsing_header("Show enabled list##cons_list", bot_config.show_consumables_list))
            bot_config.show_consumables_list = opened
        else:
            opened = bool(PyImGui.tree_node("Show enabled list##cons_list"))
            bot_config.show_consumables_list = opened
    except Exception:
        opened = bool(bot_config.show_consumables_list)

    if opened:
        if not enabled:
            PyImGui.text_disabled("None enabled.")
        else:
            for k in enabled:
                label = ALL_BY_KEY[k]["label"] if k in ALL_BY_KEY else k
                PyImGui.bullet_text("")
                _same_line(6)
                PyImGui.text_wrapped(label)
                _same_line(10)
                _draw_badge("ON", True)

        try:
            if not hasattr(PyImGui, "collapsing_header"):
                PyImGui.tree_pop()
        except Exception:
            pass

    bot_config.save_throttled()
    PyImGui.end()


def _draw_settings_window():
    if PyImGui.begin(f"{BOT_NAME} Settings##{BOT_NAME}", PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text("Debug Logging:")
        bot_config.debug_logging = PyImGui.checkbox("##debug_logging", bool(bot_config.debug_logging))

        PyImGui.separator()

        before = bool(bot_config.hero_ai_enabled)
        bot_config.hero_ai_enabled = PyImGui.checkbox("Enable HeroAI##hero_ai", before)
        if bool(bot_config.hero_ai_enabled) != before:
            _apply_hero_ai_live()

        bot_config.save_throttled()
    PyImGui.end()


def _matches_filter(label, flt):
    if not flt:
        return True
    return flt in label.lower()


def _draw_consumable_row(spec, filter_text):
    k = spec["key"]
    label = spec["label"]
    if not _matches_filter(label, filter_text):
        return

    enabled = bool(bot_config.consumables_enabled.get(k, False))
    enabled = PyImGui.checkbox(f"##cb_{k}", enabled)
    _same_line(10)
    PyImGui.text(label)
    _same_line(12)
    if PyImGui.small_button(("ON" if enabled else "OFF") + f"##btn_{k}"):
        enabled = not enabled
    bot_config.consumables_enabled[k] = bool(enabled)


def _draw_consumables_window():
    if PyImGui.begin(f"{BOT_NAME} Consumables##{BOT_NAME}", PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text("Search:")
        _same_line(10)
        try:
            res = PyImGui.input_text("##consumable_filter", consumable_filter[0], 64)
            if isinstance(res, tuple) and len(res) == 2:
                consumable_filter[0] = res[1]
            elif isinstance(res, str):
                consumable_filter[0] = res
        except Exception:
            pass

        filter_text = consumable_filter[0].strip().lower()

        PyImGui.dummy(0, 6)

        if PyImGui.button("Select All Visible##select_all_visible"):
            for spec in ALL_CONSUMABLES:
                if _matches_filter(spec["label"], filter_text):
                    bot_config.consumables_enabled[spec["key"]] = True

        _same_line(10)
        if PyImGui.button("Clear All Visible##clear_all_visible"):
            for spec in ALL_CONSUMABLES:
                if _matches_filter(spec["label"], filter_text):
                    bot_config.consumables_enabled[spec["key"]] = False

        PyImGui.separator()

        PyImGui.text("Maintain Consumables:")
        PyImGui.separator()
        for spec in MAINTAIN_CONSUMABLES:
            _draw_consumable_row(spec, filter_text)

        PyImGui.dummy(0, 8)
        PyImGui.text("Conset:")
        PyImGui.separator()
        for spec in CONSETS:
            _draw_consumable_row(spec, filter_text)

        PyImGui.dummy(0, 8)
        PyImGui.text_disabled("Restock is disabled (restock=0). If you run out, it just stops consuming.")

        bot_config.save_throttled()
    PyImGui.end()


def draw_ui():
    _draw_main_window()
    if show_settings[0]:
        _draw_settings_window()
    if show_consumables[0]:
        _draw_consumables_window()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Quest Auto-Runner (Simple)", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A streamlined automation bot that follows active quest markers.")
    PyImGui.text("It bridges the gap between navigation and combat by pausing")
    PyImGui.text("movement to allow HeroAI or AutoCombat to clear hostiles.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Auto-Pathing: Intelligently follows active quest markers across the map")
    PyImGui.bullet_text("Combat Integration: Smart-pauses navigation when enemies are engaged")
    PyImGui.bullet_text("Consumable Manager: Automated upkeep of pcons and consets via search filter")
    PyImGui.bullet_text("Multibox Sync: Broadcasts state changes to the party via Shared Commands")
    PyImGui.bullet_text("Dynamic Wait: Automatically waits for party members and loading screens")
    PyImGui.bullet_text("Safety Logic: Detects stuck states and stale markers with auto-timeout")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by RaphaelHoefer")
    PyImGui.bullet_text("Contributors: Icefox")

    PyImGui.end_tooltip()


def main():
    bot.Update()
    draw_ui()


if __name__ == "__main__":
    main()
