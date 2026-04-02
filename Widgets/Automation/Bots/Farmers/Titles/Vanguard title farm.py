# region Imports & Config
from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, Agent, Player, ConsoleLog, IniManager, ModelID, HeroType
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
from Py4GWCoreLib.botting_src.property import Property
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
import Py4GW
import os
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Optional

BOT_NAME = "Vanguard Title Farm"

MODULE_NAME = BOT_NAME
MODULE_ICON = "Textures/Skill_Icons/[2233] - Ebon Battle Standard of Honor.jpg"

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
DALADA_UPLANDS_OUTPOST_ID = 648
DALADA_UPLANDS_MAP_ID = 647
ENABLE_COMBAT_MODE_STEP_NAME = "[H]Enable Combat Mode_1"
START_COMBAT_STEP_NAME = "[H]Start Combat_2"

DALADA_UPLANDS_OUTPOST_PATH = [
    (-16016.0, 17340.0),
    (-15400.0, 13500.0),
]

DALADA_SEGMENT_1_BLESS = (-14971.00, 11013.00)
DALADA_SEGMENT_1_PATH = [
    (-14350.5, 12790.6), (-17600.7, 10388.3), (-16649.0, 6485.4), (-16131.3, 2494.2),
    (-13528.1, -571.5), (-15663.4, -3959.4), (-18089.6, -7150.1), (-17921.5, -11167.4),
    (-15917.0, -14662.3), (-13390.84, -16843.04), (-12191.4, -16190.6), (-8482.2, -14675.8), (-7746.7, -18628.1),
    (-4699.0, -15996.0), (-734.2, -16733.1), (3209.2, -17521.2), (7204.8, -17236.8),
    (10660.3, -15173.9), (14231.2, -13323.1), (15486.11, -14122.26), (17868.1, -11540.7), (14280.7, -9705.3),
    (13958.0, -5657.5), (17851.7, -4510.7), (14141.2, -2985.1), (10104.9, -2608.4),
    (10392.6, 1429.8), (14414.1, 923.4), (16536.4, 4358.9), (17027.8, 8366.5),
    (14253.5, 11258.4), (12708.4, 14995.4), (8842.1, 16056.3), (5366.9, 18114.6),
    (2657.9, 15144.8), (-1025.2, 16731.2), (1142.8, 13355.0), (-2272.1, 11178.6),
    (-6246.7, 12038.8), (-8875.1, 15092.1), (-9545.32, 16453.30), (-10593.52, 14475.55), (-11859.57, 12183.40), (-9680.6, 11168.8), (-7630.3, 7678.4),
    (-3717.2, 8618.1), (-3227.72, 8829.67), (232.2, 9451.7), (4266.0, 9959.4), (8007.6, 8342.5),
    (4888.8, 5766.7), (1037.3, 4668.6), (-2887.1, 3697.4), (-6918.0, 4104.1),
    (-10897.1, 4922.3), (-14702.6, 6233.5), (-10898.6, 4878.2), (-9045.5, 1321.2),
    (-8657.0, -2712.6), (-5189.2, -611.5), (-1172.4, 95.6), (2474.3, 1913.7),
    (6476.9, 2343.3), (5489.0, -1545.9), (5552.4, -5596.4), (7189.7, -9305.8), (8261.67, -12055.48),
    (5228.1, -5784.1), (2164.1, -3177.7), (-1530.8, -4867.3), (156.3, -8499.8),
    (3819.1, -10133.5), (2167.7, -13796.2), (-1821.5, -14135.8), (-5747.9, -13218.7),
]

DALADA_SEGMENT_2_BLESS = (-2641.00, 449.00)
DALADA_SEGMENT_2_PATH = [
    (-1172.4, 95.6), (2474.3, 1913.7), (6476.9, 2343.3), (5489.0, -1545.9),
    (5552.4, -5596.4), (7189.7, -9305.8), (8261.67, -12055.48), (5228.1, -5784.1),
    (2164.1, -3177.7), (-1530.8, -4867.3), (156.3, -8499.8), (3819.1, -10133.5),
    (2167.7, -13796.2), (-1821.5, -14135.8), (-5747.9, -13218.7),
]

DALADA_SEGMENT_3_BLESS = (-3954.00, -11426.00)
DALADA_SEGMENT_3_PATH = [
    (-5747.9, -13218.7), (-9790.9, -13258.0), (-11047.5, -9448.2), (-7777.1, -7032.2),
    (-4638.2, -4496.5), (-1131.0, -2524.7), (1852.3, 163.3), (5104.8, 2594.2),
    (8307.3, 5060.4), (7509.3, 8998.1), (10537.1, 11668.0), (8091.5, 8492.2),
    (11725.8, 6705.3), (7964.3, 8157.4), (4666.3, 10422.2),
]

DALADA_SEGMENT_4_BLESS = (5884.00, 11749.00)
DALADA_SEGMENT_4_PATH = [
    (4666.3, 10422.2),
    (1772.7, 13212.8),
]

bot = Botting(
    BOT_NAME,
    upkeep_armor_of_salvation_restock=2,
    upkeep_essence_of_celerity_restock=2,
    upkeep_grail_of_might_restock=2,
    upkeep_war_supplies_restock=2,
    upkeep_birthday_cupcake_restock=2,
    upkeep_honeycomb_restock=20,
    upkeep_auto_combat_active=True,
    upkeep_auto_inventory_management_active=True,
    upkeep_auto_loot_active=True
)

bot.config.config_properties.use_conset = Property(bot.config, "use_conset", active=False)
bot.config.config_properties.use_pcons = Property(bot.config, "use_pcons", active=False)

_SETTINGS_SECTION = "TitleBotSettings"
_USE_CONSET_KEY = "use_conset"
_USE_PCONS_KEY = "use_pcons"

# Hero config
_BOT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
_HERO_CONFIG_PATH = os.path.join(_BOT_SCRIPT_DIR, f"{BOT_NAME} Heroes.json")
_HERO_ICONS_BASE = os.path.normpath(os.path.join(
    Py4GW.Console.get_projects_path(), "..", "Property-of-Wick-Divinus-and-Kendor",
    "PVE Skills Unlocker", "Textures", "Skill_Icons"
))
_HERO_SLOTS_COUNT = 7
_intentional_resign_in_progress = False


@dataclass
class _PartyHeroSlot:
    hero_id: int = 0
    template: str = ""


def _humanize_hero_name(enum_name: str) -> str:
    if enum_name == "None_":
        return "<Empty>"
    words: List[str] = []
    current = enum_name[0]
    for char in enum_name[1:]:
        if (char.isupper() and not current[-1].isupper()) or (char.isdigit() and not current[-1].isdigit()):
            words.append(current)
            current = char
        else:
            current += char
    words.append(current)
    return " ".join(words)


_HERO_OPTIONS: List[HeroType] = [HeroType.None_] + sorted([h for h in HeroType if h != HeroType.None_], key=lambda h: _humanize_hero_name(h.name))
_HERO_OPTION_LABELS: List[str] = [_humanize_hero_name(h.name) for h in _HERO_OPTIONS]
_HERO_ID_TO_OPTION_INDEX: Dict[int, int] = {int(h): i for i, h in enumerate(_HERO_OPTIONS)}

_HERO_ICON_FILENAMES: Dict[HeroType, str] = {
    HeroType.Norgu: "Norgu-icon.jpg",           HeroType.Goren: "Goren-icon.jpg",
    HeroType.Tahlkora: "Tahlkora-icon.jpg",      HeroType.MasterOfWhispers: "MasterOfWhispers-icon.jpg",
    HeroType.AcolyteJin: "AcolyteSousuke-icon.jpg", HeroType.Koss: "Koss-icon.jpg",
    HeroType.Dunkoro: "Dunkoro-icon.jpg",        HeroType.AcolyteSousuke: "AcolyteSousuke-icon.jpg",
    HeroType.Melonni: "Melonni-icon.jpg",        HeroType.ZhedShadowhoof: "ZhedShadowhoof-icon.jpg",
    HeroType.GeneralMorgahn: "GeneralMorgahn-icon.jpg", HeroType.MagridTheSly: "MargridTheSly-icon.jpg",
    HeroType.Zenmai: "Zenmai-icon.jpg",          HeroType.Olias: "Olias-icon.jpg",
    HeroType.Razah: "Razah-icon.jpg",            HeroType.MOX: "M.O.X.-icon.jpg",
    HeroType.KeiranThackeray: "KeiranThackeray-icon.jpg", HeroType.Jora: "Jora-icon.jpg",
    HeroType.PyreFierceshot: "Pyre_Fierceshot-icon.jpg", HeroType.Anton: "Anton-icon.jpg",
    HeroType.Livia: "Livia-icon.jpg",            HeroType.Hayda: "Hayda-icon.jpg",
    HeroType.Kahmu: "Kahmu-icon.jpg",            HeroType.Gwen: "Gwen-icon.jpg",
    HeroType.Xandra: "Xandra-icon.jpg",          HeroType.Vekk: "Vekk-icon.jpg",
    HeroType.Ogden: "Ogden_Stonehealer-icon.jpg", HeroType.Miku: "Miku-icon.jpg",
    HeroType.ZeiRi: "Zei_Ri-icon.jpg",
}

_DEFAULT_HERO_TEMPLATES: Dict[HeroType, str] = {
    HeroType.Norgu: "OQBDAawDSvAIgcQ5ZkAFgZAEBA",
    HeroType.Gwen: "OQhkAsC8gFKzJIHM9MdDBcaG4iB",
    HeroType.Vekk: "OgVDI8gsS5AnATPmOHgCAZAFBA",
    HeroType.MasterOfWhispers: "OABDUshnSyBVBoBKgbhVVfCWCA",
    HeroType.Olias: "OAhjQoGYIP3hhWVVaO5EeDTqNA",
    HeroType.Ogden: "OwUUMsG/E4SNgbE3N3ETfQgZAMEA",
    HeroType.Razah: "OAWjMMgMJPYTr3jLcCNdmZgeAA",
}

_hero_slots: List[_PartyHeroSlot] = [_PartyHeroSlot() for _ in range(_HERO_SLOTS_COUNT)]
_hero_config_dirty: bool = False
_hero_config_status: str = ""
_hero_import_source_index: int = 0

# (model_id, effect_skill_name) — single source of truth for consumable use & restock
CONSET_ITEMS: list[tuple[int, str]] = [
    (ModelID.Essence_Of_Celerity.value, "Essence_of_Celerity_item_effect"),
    (ModelID.Grail_Of_Might.value,      "Grail_of_Might_item_effect"),
    (ModelID.Armor_Of_Salvation.value,  "Armor_of_Salvation_item_effect"),
]

PCON_ITEMS: list[tuple[int, str]] = [
    (ModelID.Birthday_Cupcake.value,      "Birthday_Cupcake_skill"),
    (ModelID.Golden_Egg.value,            "Golden_Egg_skill"),
    (ModelID.Candy_Corn.value,            "Candy_Corn_skill"),
    (ModelID.Candy_Apple.value,           "Candy_Apple_skill"),
    (ModelID.Slice_Of_Pumpkin_Pie.value,  "Pie_Induced_Ecstasy"),
    (ModelID.Drake_Kabob.value,           "Drake_Skin"),
    (ModelID.Bowl_Of_Skalefin_Soup.value, "Skale_Vigor"),
    (ModelID.Pahnai_Salad.value,          "Pahnai_Salad_item_effect"),
    (ModelID.War_Supplies.value,          "Well_Supplied"),
]

CONSET_RESTOCK_MODELS = [m for m, _ in CONSET_ITEMS]
PCON_RESTOCK_MODELS   = [m for m, _ in PCON_ITEMS] + [
    ModelID.Honeycomb.value,
    ModelID.Scroll_Of_Resurrection.value,
]


def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Templates.Aggressive()
    bot.Properties.Enable("auto_inventory_management")
# endregion


# region Bot Routine
def Routine(bot: Botting) -> None:
    PrepareForCombat(bot)
    Fight(bot)


def PrepareForCombat(bot: Botting) -> None:
    bot.States.AddHeader("Enable Combat Mode")
    _load_consumable_settings(bot)
    _sync_consumable_toggles(bot)
    bot.Map.Travel(target_map_id=DALADA_UPLANDS_OUTPOST_ID)
    bot.States.AddCustomState(lambda: _setup_heroes(bot), "Setup Heroes")
    bot.States.AddCustomState(lambda: _restock_consumables_if_enabled(bot), "Restock Consumables If Enabled")
    bot.Party.SetHardMode(True)


def _do_bless_and_path(bot: Botting, bless_xy: tuple[float, float], path: list[tuple[float, float]], label: str) -> None:
    bot.Move.XY(bless_xy[0], bless_xy[1], label)
    bot.Wait.ForTime(1500)
    bot.Move.XYAndDialog(bless_xy[0], bless_xy[1], 0x84)
    bot.States.AddCustomState(lambda: _send_local_dialog(bot, 0x85), "Local Dialog 0x85")
    bot.Move.FollowAutoPath(path)


def Fight(bot: Botting) -> None:
    # events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    # end events

    bot.States.AddHeader("Start Combat")
    bot.Move.FollowPathAndExitMap(DALADA_UPLANDS_OUTPOST_PATH, target_map_id=DALADA_UPLANDS_MAP_ID)
    bot.Wait.ForMapLoad(target_map_id=DALADA_UPLANDS_MAP_ID)
    bot.Wait.ForTime(4000)
    ConfigureAggressiveEnv(bot)
    bot.States.AddCustomState(lambda: PrepareForBattle(bot), "Use Consumables If Enabled")
    bot.States.AddManagedCoroutine("Anti-Stuck Watchdog", lambda: _anti_stuck_watchdog(bot))

    # Path segment 1
    _do_bless_and_path(bot, DALADA_SEGMENT_1_BLESS, DALADA_SEGMENT_1_PATH, "Taking Blessing")

    # Path segment 2
    _do_bless_and_path(bot, DALADA_SEGMENT_2_BLESS, DALADA_SEGMENT_2_PATH, "Taking Blessing")

    # Path segment 3
    _do_bless_and_path(bot, DALADA_SEGMENT_3_BLESS, DALADA_SEGMENT_3_PATH, "Taking Blessing")

    # Path segment 4
    _do_bless_and_path(bot, DALADA_SEGMENT_4_BLESS, DALADA_SEGMENT_4_PATH, "Taking Blessing")

    bot.States.AddCustomState(lambda: _resign(bot), "Resign Party")
    bot.Wait.UntilOnOutpost()
    bot.Wait.ForTime(5000)
    bot.States.JumpToStepName(ENABLE_COMBAT_MODE_STEP_NAME)


def PrepareForBattle(bot: Botting):
    _sync_consumable_toggles(bot)
    yield from _use_consumables_if_enabled(bot)


bot.UI.override_draw_config(lambda: _draw_settings(bot))

bot.SetMainRoutine(Routine)
# endregion


# region Consumables
def _restock_consumables_if_enabled(bot: Botting):
    _sync_consumable_toggles(bot)
    if _as_bool(bot.Properties.Get("use_conset", "active")):
        yield from _restock_models_locally(CONSET_RESTOCK_MODELS, 250)
    if _as_bool(bot.Properties.Get("use_pcons", "active")):
        yield from _restock_models_locally(PCON_RESTOCK_MODELS, 250)


def _use_consumables_if_enabled(bot: Botting):
    _sync_consumable_toggles(bot)
    if _as_bool(bot.Properties.Get("use_conset", "active")):
        yield from bot.Items.UseConset()
    if _as_bool(bot.Properties.Get("use_pcons", "active")):
        yield from bot.Items.UsePcons()


def _restock_models_locally(model_ids: list[int], quantity: int):
    for model_id in model_ids:
        yield from Routines.Yield.Items.RestockItems(model_id, quantity)
# endregion


# region Anti-Stuck
EXPLORABLE_TIMEOUT_SECONDS = 3 * 3600  # 3 hours


def _anti_stuck_resign(bot: "Botting"):
    """Called when the timeout fires: resign, wait for outpost, then restart."""
    yield from _resign(bot)
    while True:
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            continue
        if Routines.Checks.Map.IsOutpost():
            break
    bot.States.JumpToStepName(ENABLE_COMBAT_MODE_STEP_NAME)
    bot.config.FSM.resume()
    yield


def _anti_stuck_watchdog(bot: "Botting"):
    """Resign the party if stuck in explorable for more than 3 hours."""
    explorable_entry_time = None
    while True:
        yield from bot.Wait._coro_for_time(60000)  # check every minute
        if not Routines.Checks.Map.MapValid():
            explorable_entry_time = None
            continue
        if Routines.Checks.Map.IsOutpost():
            explorable_entry_time = None
            continue
        # We are in explorable
        if explorable_entry_time is None:
            explorable_entry_time = time.time()
            continue
        elapsed = time.time() - explorable_entry_time
        if elapsed >= EXPLORABLE_TIMEOUT_SECONDS:
            ConsoleLog(BOT_NAME, f"Anti-stuck: {elapsed/3600:.1f}h in explorable - resigning party.", Py4GW.Console.MessageType.Warning)
            explorable_entry_time = None
            bot.config.FSM.pause()
            bot.config.FSM.AddManagedCoroutine("AntiStuck_Resign", lambda: _anti_stuck_resign(bot))
# endregion


# region Events
def _on_party_wipe(bot: "Botting"):
    global _intentional_resign_in_progress
    if _intentional_resign_in_progress or not Routines.Checks.Map.MapValid() or not Routines.Checks.Map.IsExplorable():
        bot.config.FSM.resume()
        return
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if _intentional_resign_in_progress or not Routines.Checks.Map.MapValid() or not Routines.Checks.Map.IsExplorable():
            bot.config.FSM.resume()
            return
        if not Routines.Checks.Map.MapValid():
            # Map invalid -> release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map -> jump to recovery step
    if _intentional_resign_in_progress or not Routines.Checks.Map.MapValid() or not Routines.Checks.Map.IsExplorable():
        bot.config.FSM.resume()
        return

    bot.States.JumpToStepName(START_COMBAT_STEP_NAME)
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    if _intentional_resign_in_progress:
        ConsoleLog("on_party_wipe", "ignored during intentional resign")
        return
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))
# endregion


# region Settings
def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _send_local_dialog(bot: Botting, dialog_id: int):
    Player.SendDialog(dialog_id)
    yield from bot.Wait._coro_for_time(500)


def _ensure_bot_ini(bot: Botting) -> str:
    if not bot.config.ini_key_initialized:
        bot.config.ini_key = IniManager().ensure_key(
            f"BottingClass/bot_{bot.config.bot_name}",
            f"bot_{bot.config.bot_name}.ini",
        )
        bot.config.ini_key_initialized = True
    return bot.config.ini_key


def _load_hero_config():
    global _hero_slots, _hero_config_dirty, _hero_config_status
    if not os.path.exists(_HERO_CONFIG_PATH):
        _hero_config_status = ""
        return
    try:
        with open(_HERO_CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _hero_slots = _parse_hero_config_entries(raw)
        _hero_config_dirty = False
        _hero_config_status = "Loaded."
    except Exception as exc:
        _hero_config_status = f"Load error: {exc}"


def _save_hero_config():
    global _hero_config_dirty, _hero_config_status
    payload = [{"hero_id": int(s.hero_id), "template": s.template} for s in _hero_slots]
    try:
        os.makedirs(os.path.dirname(_HERO_CONFIG_PATH), exist_ok=True)
        with open(_HERO_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        _hero_config_dirty = False
        _hero_config_status = "Saved."
    except Exception as exc:
        _hero_config_status = f"Save error: {exc}"


def _reset_hero_config():
    global _hero_slots, _hero_config_dirty, _hero_config_status
    _hero_slots = [_PartyHeroSlot() for _ in range(_HERO_SLOTS_COUNT)]
    _hero_config_dirty = True
    _hero_config_status = "Reset to empty."


def _parse_hero_config_entries(raw) -> List[_PartyHeroSlot]:
    slots: List[_PartyHeroSlot] = []
    for i in range(_HERO_SLOTS_COUNT):
        entry = raw[i] if isinstance(raw, list) and i < len(raw) else {}
        hero_id = int(entry.get("hero_id", 0) or 0)
        if hero_id not in _HERO_ID_TO_OPTION_INDEX:
            hero_id = 0
        slots.append(_PartyHeroSlot(hero_id=hero_id, template=str(entry.get("template", "") or "")))
    return slots


def _list_importable_hero_configs() -> List[str]:
    try:
        hero_files = []
        for entry in os.listdir(_BOT_SCRIPT_DIR):
            if not entry.endswith(" Heroes.json"):
                continue
            full_path = os.path.join(_BOT_SCRIPT_DIR, entry)
            if os.path.isfile(full_path):
                hero_files.append(full_path)
        hero_files.sort(key=lambda path: os.path.basename(path).lower())
        return hero_files
    except OSError:
        return []


def _hero_import_label(path: str) -> str:
    name = os.path.splitext(os.path.basename(path))[0]
    return name[:-7] if name.endswith(" Heroes") else name


def _import_hero_config(path: str):
    global _hero_slots, _hero_config_dirty, _hero_config_status
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _hero_slots = _parse_hero_config_entries(raw)
        _hero_config_dirty = True
        _save_hero_config()
        _hero_config_status = f"Imported from {_hero_import_label(path)} and saved."
    except Exception as exc:
        _hero_config_status = f"Import error: {exc}"


def _get_hero_icon_path(hero_id: int) -> Optional[str]:
    try:
        hero_type = HeroType(hero_id)
    except ValueError:
        return None
    filename = _HERO_ICON_FILENAMES.get(hero_type)
    if not filename:
        return None
    path = os.path.join(_HERO_ICONS_BASE, filename)
    return path if os.path.exists(path) else None


def _draw_hero_icon(hero_id: int, size: int = 24):
    import PyImGui

    path = _get_hero_icon_path(hero_id)
    if path:
        try:
            cx, cy = PyImGui.get_cursor_screen_pos()
            ImGui.DrawTextureInDrawList(pos=(float(cx), float(cy)), size=(float(size), float(size)), texture_path=path)
        except Exception:
            try:
                ImGui.DrawTexture(texture_path=path, width=size, height=size)
            except Exception:
                pass
    PyImGui.dummy(int(size), int(size))


def _draw_hero_combo(label: str, hero_id: int) -> int:
    import PyImGui

    current_index = _HERO_ID_TO_OPTION_INDEX.get(hero_id, 0)
    preview = _HERO_OPTION_LABELS[current_index]
    if PyImGui.begin_combo(label, preview, PyImGui.ImGuiComboFlags.NoFlag):
        for index, hero in enumerate(_HERO_OPTIONS):
            if hero != HeroType.None_:
                _draw_hero_icon(int(hero), size=20)
            else:
                PyImGui.dummy(20, 20)
            PyImGui.same_line(0.0, 8.0)
            if PyImGui.selectable(f"{_HERO_OPTION_LABELS[index]}##{label}_{index}", index == current_index, 0, [0.0, 0.0]):
                current_index = index
        PyImGui.end_combo()
    return int(_HERO_OPTIONS[current_index])


def _draw_hero_slot_editor(slot_index: int):
    import PyImGui

    global _hero_config_dirty
    slot = _hero_slots[slot_index]
    combo_label_width = 70.0

    PyImGui.text(f"Hero {slot_index + 1}")
    PyImGui.same_line(combo_label_width, 8.0)
    _draw_hero_icon(slot.hero_id, size=24)
    PyImGui.same_line(0.0, 8.0)
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_hero_id = _draw_hero_combo(f"##hero_{slot_index}", slot.hero_id)
    if new_hero_id != slot.hero_id:
        slot.hero_id = new_hero_id
        if slot.hero_id == HeroType.None_.value:
            slot.template = ""
        elif not slot.template.strip():
            try:
                hero_type = HeroType(slot.hero_id)
            except ValueError:
                hero_type = HeroType.None_
            slot.template = _DEFAULT_HERO_TEMPLATES.get(hero_type, "")
        _hero_config_dirty = True

    PyImGui.text("Template")
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.small_button(f"Clear##slot_{slot_index}"):
        if slot.hero_id != HeroType.None_.value or slot.template:
            slot.hero_id = HeroType.None_.value
            slot.template = ""
            _hero_config_dirty = True
    PyImGui.set_next_item_width(PyImGui.get_content_region_avail()[0])
    new_template = PyImGui.input_text(f"##template_{slot_index}", slot.template)
    if new_template != slot.template:
        slot.template = new_template
        _hero_config_dirty = True


def _draw_hero_settings_tab():
    import PyImGui
    global _hero_import_source_index
    PyImGui.text("Configure up to 7 heroes for Single Account mode.")
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.7, 0.7, 0.7, 1.0))
    PyImGui.text("Heroes are added in order; duplicates and empty slots are skipped.")
    PyImGui.pop_style_color(1)
    PyImGui.spacing()

    if _hero_config_dirty:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.8, 0.2, 1.0))
        PyImGui.text("Unsaved changes")
        PyImGui.pop_style_color(1)
    elif _hero_config_status:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.6, 0.9, 0.6, 1.0))
        PyImGui.text(_hero_config_status)
        PyImGui.pop_style_color(1)

    if PyImGui.button("Save", 100, 26):
        _save_hero_config()
    PyImGui.same_line(0, 8)
    if PyImGui.button("Reload", 100, 26):
        _load_hero_config()
    PyImGui.same_line(0, 8)
    if PyImGui.button("Reset", 100, 26):
        _reset_hero_config()
    import_paths = _list_importable_hero_configs()
    if import_paths:
        if _hero_import_source_index >= len(import_paths):
            _hero_import_source_index = 0
        import_labels = [_hero_import_label(path) for path in import_paths]
        _hero_import_source_index = PyImGui.combo("Import Team From", _hero_import_source_index, import_labels)
        if PyImGui.button("Import Team", 120, 26):
            _import_hero_config(import_paths[_hero_import_source_index])
    else:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.7, 0.7, 0.7, 1.0))
        PyImGui.text("Import Team: save another title bot hero lineup first.")
        PyImGui.pop_style_color(1)
    PyImGui.separator()

    if PyImGui.begin_child("HeroSlotsChild", (0, -1), True):
        for i in range(_HERO_SLOTS_COUNT):
            _draw_hero_slot_editor(i)
            if i < _HERO_SLOTS_COUNT - 1:
                PyImGui.separator()
    PyImGui.end_child()


def _setup_heroes(bot: Botting):
    global _hero_slots
    GLOBAL_CACHE.Party.LeaveParty()
    for _ in range(8):
        yield from bot.Wait._coro_for_time(250)
        if GLOBAL_CACHE.Party.GetPlayerCount() <= 1:
            break
    GLOBAL_CACHE.Party.Heroes.KickAllHeroes()
    yield from bot.Wait._coro_for_time(500)
    seen: set = set()
    for slot in _hero_slots:
        hero_id = int(slot.hero_id)
        if hero_id <= 0 or hero_id in seen:
            continue
        seen.add(hero_id)
        GLOBAL_CACHE.Party.Heroes.AddHero(hero_id)
    yield from bot.Wait._coro_for_time(1000)
    template_map = {int(s.hero_id): s.template for s in _hero_slots if s.template}
    party_hero_count = GLOBAL_CACHE.Party.GetHeroCount()
    for position in range(1, party_hero_count + 1):
        hero_agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(position)
        if hero_agent_id > 0:
            hero_id = GLOBAL_CACHE.Party.Heroes.GetHeroIDByAgentID(hero_agent_id)
            template = template_map.get(hero_id, "")
            if template:
                GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(position, template)
            yield from bot.Wait._coro_for_time(500)


def _resign(bot: Botting):
    global _intentional_resign_in_progress
    _intentional_resign_in_progress = True
    yield from Routines.Yield.Player.SendChatCommand("resign")
    yield from bot.Wait._coro_for_time(500)


def _load_consumable_settings(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    saved_use_conset = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _USE_CONSET_KEY,
        _as_bool(bot.Properties.Get("use_conset", "active")),
    )
    saved_use_pcons = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _USE_PCONS_KEY,
        _as_bool(bot.Properties.Get("use_pcons", "active")),
    )
    bot.Properties.ApplyNow("use_conset", "active", _as_bool(saved_use_conset))
    bot.Properties.ApplyNow("use_pcons", "active", _as_bool(saved_use_pcons))


def _save_consumable_settings(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    IniManager().write_key(
        ini_key,
        _SETTINGS_SECTION,
        _USE_CONSET_KEY,
        _as_bool(bot.Properties.Get("use_conset", "active")),
    )
    IniManager().write_key(
        ini_key,
        _SETTINGS_SECTION,
        _USE_PCONS_KEY,
        _as_bool(bot.Properties.Get("use_pcons", "active")),
    )


def _ensure_consumable_settings_ui_loaded(bot: Botting) -> None:
    if getattr(bot.config, "_consumable_settings_ui_loaded", False):
        return
    _load_consumable_settings(bot)
    bot.config._consumable_settings_ui_loaded = True


def _sync_consumable_toggles(bot: Botting) -> None:
    use_conset = _as_bool(bot.Properties.Get("use_conset", "active"))
    use_pcons = _as_bool(bot.Properties.Get("use_pcons", "active"))

    for key in ("armor_of_salvation", "essence_of_celerity", "grail_of_might"):
        bot.Properties.ApplyNow(key, "active", use_conset)

    for key in (
        "birthday_cupcake",
        "golden_egg",
        "candy_corn",
        "candy_apple",
        "slice_of_pumpkin_pie",
        "drake_kabob",
        "bowl_of_skalefin_soup",
        "pahnai_salad",
        "war_supplies",
        "honeycomb",
    ):
        bot.Properties.ApplyNow(key, "active", use_pcons)


# endregion


# region GUI
def _draw_settings(bot: Botting):
    import PyImGui

    PyImGui.text("Bot Settings")

    _ensure_consumable_settings_ui_loaded(bot)
    PyImGui.text("Combat Backend")
    PyImGui.text("Current: Auto Combat")
    PyImGui.text("Mode: Single Account with Heroes")

    # Conset controls
    use_conset = _as_bool(bot.Properties.Get("use_conset", "active"))
    new_use_conset = PyImGui.checkbox("Restock & use Conset", use_conset)
    if new_use_conset != use_conset:
        bot.Properties.ApplyNow("use_conset", "active", new_use_conset)
        _save_consumable_settings(bot)

    # Pcons controls
    use_pcons = _as_bool(bot.Properties.Get("use_pcons", "active"))
    new_use_pcons = PyImGui.checkbox("Restock & use Pcons", use_pcons)
    if new_use_pcons != use_pcons:
        bot.Properties.ApplyNow("use_pcons", "active", new_use_pcons)
        _save_consumable_settings(bot)
    _sync_consumable_toggles(bot)


def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color

    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Vanguard Title Farm", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("Farm Vanguard title in Dalada Uplands")
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by AH")
    PyImGui.bullet_text("With help from Wick Divinus")
    PyImGui.end_tooltip()


_session_baselines: dict[str, int] = {}
_session_start_times: dict[str, float] = {}


def _get_title_track_accounts():
    accounts = list(GLOBAL_CACHE.ShMem.GetAllAccountData())
    own_email = Player.GetAccountEmail()
    filtered = [account for account in accounts if getattr(account, "AccountEmail", "") == own_email]
    if filtered:
        return filtered
    own_name = Player.GetName()
    filtered = [account for account in accounts if getattr(account.AgentData, "CharacterName", "") == own_name]
    if filtered:
        return filtered
    return accounts[:1] if len(accounts) == 1 else []


def _draw_title_track():
    global _session_baselines, _session_start_times
    import PyImGui

    title_idx = int(TitleID.Ebon_Vanguard)
    tiers = TITLE_TIERS.get(TitleID.Ebon_Vanguard, [])
    now = time.time()
    accounts = _get_title_track_accounts()
    if not accounts:
        PyImGui.text("No local account statistics available yet.")
        return
    for account in accounts:
        name = account.AgentData.CharacterName
        pts = account.TitlesData.Titles[title_idx].CurrentPoints
        if name not in _session_baselines:
            _session_baselines[name] = pts
            _session_start_times[name] = now
        tier_name = "Unranked"
        tier_rank = 0
        prev_required = 0
        next_required = tiers[0].required if tiers else 0
        for i, tier in enumerate(tiers):
            if pts >= tier.required:
                tier_name = tier.name
                tier_rank = i + 1
                prev_required = tier.required
                next_required = tiers[i + 1].required if i + 1 < len(tiers) else tier.required
            else:
                next_required = tier.required
                break
        is_maxed = tiers and pts >= tiers[-1].required
        gained = pts - _session_baselines[name]
        elapsed = now - _session_start_times[name]
        pts_hr = int(gained / elapsed * 3600) if elapsed > 0 else 0
        tier_missing = max(next_required - pts, 0)
        next_rank_progress_current = max(pts, 0)
        next_rank_progress_total = max(next_required, 1)
        PyImGui.separator()
        PyImGui.text(f"{name}  [{tier_name} (Rank {tier_rank})]")
        PyImGui.text(f"Total Points: {pts:,}")
        if is_maxed:
            PyImGui.text("Next Rank: Maxed")
            PyImGui.text("Points To Go: 0")
            PyImGui.progress_bar(1.0, -1, 0, "Complete")
            PyImGui.text_colored("Maximum rank achieved. Title complete.", (0.4, 1.0, 0.4, 1.0))
        else:
            PyImGui.text(f"Next Rank: {next_required:,}")
            PyImGui.text(f"Points To Go: {tier_missing:,}")
            frac = min(next_rank_progress_current / next_rank_progress_total, 1.0)
            PyImGui.progress_bar(frac, -1, 0, f"{next_rank_progress_current:,} / {next_rank_progress_total:,}")
        PyImGui.text(f"+{gained:,}  ({pts_hr:,}/hr)")


REFORGED_TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Skill_Icons", "[2233] - Ebon Battle Standard of Honor.jpg")
_EXPANDED_TAB_CHILD_SIZE = (500, 620)
# endregion


# region Entry Point
_hero_config_loaded = False


def _draw_statistics_tab() -> None:
    import PyImGui
    if PyImGui.begin_child("VanguardStatisticsTabChild", _EXPANDED_TAB_CHILD_SIZE, False):
        _draw_title_track()
    PyImGui.end_child()


def _draw_heroes_tab() -> None:
    import PyImGui
    if PyImGui.begin_child("VanguardHeroesTabChild", _EXPANDED_TAB_CHILD_SIZE, False):
        _draw_hero_settings_tab()
    PyImGui.end_child()


def _clear_intentional_resign_guard() -> None:
    global _intentional_resign_in_progress
    if not _intentional_resign_in_progress:
        return
    if bot.config.FSM.paused:
        return
    if Routines.Checks.Map.MapValid() and Routines.Checks.Map.IsOutpost():
        _intentional_resign_in_progress = False


def main():
    global _hero_config_loaded
    if not _hero_config_loaded:
        _load_hero_config()
        _hero_config_loaded = True
    if Map.IsMapLoading():
        return
    bot.Update()
    _clear_intentional_resign_guard()
    bot.UI.draw_window(icon_path=REFORGED_TEXTURE, extra_tabs=[
        ("Statistics", _draw_statistics_tab),
        ("Heroes", _draw_heroes_tab),
    ])


if __name__ == "__main__":
    main()
# endregion
