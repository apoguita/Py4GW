# region Imports & Config
from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Agent, Player, ConsoleLog, IniManager, HeroType
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

BOT_NAME = "Asura Title Farm"

MODULE_NAME = BOT_NAME
MODULE_ICON = "Textures/Skill_Icons/[2372] - Edification.jpg"

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
RATASUM = 640
ZONING_STEP_NAME = "[H]Zoning into explorable area_2"
START_COMBAT_STEP_NAME = "[H]Start Combat_3"

bot = Botting(BOT_NAME,
              upkeep_armor_of_salvation_restock=2,
              upkeep_essence_of_celerity_restock=2,
              upkeep_grail_of_might_restock=2,
              upkeep_war_supplies_restock=2,
              upkeep_birthday_cupcake_restock=2,
              upkeep_honeycomb_restock=20,
              upkeep_auto_combat_active=True,
              upkeep_auto_inventory_management_active=True,
              upkeep_auto_loot_active=True)

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

# Module-level hero config state
_hero_slots: List[_PartyHeroSlot] = [_PartyHeroSlot() for _ in range(_HERO_SLOTS_COUNT)]
_hero_config_dirty: bool = False
_hero_config_status: str = ""
_hero_import_source_index: int = 0

# (model_id, effect_skill_name) â€” single source of truth for consumable use & restock
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
    bot.States.AddHeader("Prepare For Farm")
    _load_consumable_settings(bot)
    _sync_consumable_toggles(bot)
    bot.Map.Travel(target_map_id=RATASUM)
    bot.States.AddCustomState(lambda: _setup_heroes(bot), "Setup Heroes")
    bot.States.AddCustomState(lambda: _restock_consumables_if_enabled(bot), "Restock Consumables If Enabled")
    bot.Party.SetHardMode(True)


def Fight(bot: Botting) -> None:
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    bot.States.AddHeader("Zoning into explorable area")
    bot.Move.XY(-6062, -2688,"Exit Outpost")
    bot.Wait.ForMapLoad(target_map_name="Magus Stones")
    ConfigureAggressiveEnv(bot)
    bot.States.AddHeader("Start Combat")
    bot.States.AddCustomState(lambda: PrepareForBattle(bot), "Use Consumables If Enabled")
    bot.Move.XY(14778.00, 13178.00)
    bot.Wait.ForTime(1500)
    bot.Move.XYAndDialog(14778.00, 13178.00, 0x84)
    bot.States.AddCustomState(lambda: _send_local_dialog(bot, 0x85), "Local Dialog 0x85")

    # Path segment 1
    bot.Move.XY(18825, 6180, "First Spider Group")
    bot.Move.XY(18447, 4537, "Second Spider Group")
    bot.Move.XY(18331, 2108, "Spider Pop")
    bot.Move.XY(17526, 143, "Spider Pop 2")
    bot.Move.XY(17205, -1355, "Third Spider Group")
    bot.Move.XY(17542, -4865, "Krait Group")
    bot.Move.XY(15562, -5524, "Moving")
    bot.Move.XY(16270, -6288, "Moving")
    bot.Move.XY(17501, -5545, "Moving")
    bot.Move.XY(18111, -8030, "Krait Group")
    bot.Move.XY(18409, -8474, "Moving")
    bot.Move.XY(18613, -11799, "Froggy Group")
    bot.Move.XY(17154, -15669, "Krait Patrol")
    bot.Move.XY(14250, -16744, "Second Patrol")
    bot.Move.XY(12186, -14139, "Krait Patrol")
    bot.Move.XY(12540, -13440, "Krait Patrol")
    bot.Move.XY(13234, -9948, "Krait Group")
    bot.Move.XY(8875, -9065, "Krait Group")
    bot.Move.XY(8647, -5852, "Moving")
    bot.Move.XY(6939, -3629, "Moving")
    bot.Move.XY(8711, -6046, "Moving")
    bot.Move.XY(7616, -8978, "Moving")
    bot.Move.XY(4671, -8699, "Krait Patrol")
    bot.Move.XY(-5203, -8280, "Moving")
    bot.Move.XY(1534, -5493, "Krait Group")
    bot.Move.XY(1052, -7074, "Moving")
    bot.Move.XY(-1029, -8724, "Spider Group")
    bot.Move.XY(-3439, -10339, "Krait Group")
    bot.Move.XY(-3024, -12586, "Spider Cave")
    bot.Move.XY(-742, -13786, "Spider Cave")
    bot.Move.XY(-2755, -14099, "Spider Cave")
    bot.Move.XY(-3393, -15633, "Spider Cave")
    bot.Move.XY(-4635, -16643, "Spider Pop")
    bot.Move.XY(-7814, -17796, "Spider Group")
    bot.Move.XY(-10109, -17520, "Moving")
    bot.Move.XY(-9111, -17237, "Moving")
    bot.Move.XY(-10963, -15506, "Ranger Boss Group")
    bot.Move.XY(-13975, -17857, "Corner Spiders")
    bot.Move.XY(-11912, -10641, "Froggy Group")
    bot.Move.XY(-8760, -9933, "Krait Boss Warrior")
    bot.Move.XY(-14030, -9780, "Froggy Coing Group")
    bot.Move.XY(-12368, -7330, "Froggy Group")

    # Path segment 2 blessing
    bot.Move.XY(-9317, -2618, "Taking Blessing")
    bot.Wait.ForTime(1500)
    bot.Move.XYAndDialog(-9317, -2618, 0x84)
    bot.States.AddCustomState(lambda: _send_local_dialog(bot, 0x85), "Local Dialog 0x85")

    # Path segment 2
    bot.Move.XY(-12368, -7330, "Froggy Group")
    bot.Move.XY(-16527, -8175, "Froggy Patrol")
    bot.Move.XY(-17391, -5984, "Froggy Group")
    bot.Move.XY(-15704, -3996, "Froggy Patrol")
    bot.Move.XY(-16609, -2607, "Moving")
    bot.Move.XY(-16480, 2522, "Krait Group")
    bot.Move.XY(-17090, 5252, "Krait Group")
    bot.Move.XY(-18640, 8724, "Moving")
    bot.Move.XY(-18484, 12021, "Krait Patrol")
    bot.Move.XY(-17180, 13093, "Krait Patrol")
    bot.Move.XY(-15072, 14075, "Froggy Group")
    bot.Move.XY(-11888, 15628, "Froggy Group")
    bot.Move.XY(-12043, 18463, "Froggy Boss Warrior")
    bot.Move.XY(-8876, 17415, "Froggy Group")
    bot.Move.XY(-4770, 20353, "Froggy Group")
    bot.Move.XY(-10970, 16860, "Moving Back")
    bot.Move.XY(-9301, 15054, "Moving")
    bot.Move.XY(-9942, 12561, "Moving")
    bot.Move.XY(-9786, 10297, "Moving")
    bot.Move.XY(-5379, 16642, "Krait Group")
    bot.Move.XY(-2828, 18210, "Moving")
    bot.Move.XY(-4246, 16728, "Krait Group")
    bot.Move.XY(-2974, 14197, "Krait Group")
    bot.Move.XY(-5228, 12475, "Boss Patrol")
    bot.Move.XY(-6756, 12380, "Moving")
    bot.Move.XY(-3468, 10837, "Lonely Patrol")
    bot.Move.XY(-3804, 8017, "Krait Group")
    bot.Move.XY(-3288, 7276, "Moving")
    bot.Move.XY(-1346, 12360, "Moving")

    # Path segment 3 blessing
    bot.Move.XY(4835, 440, "Taking Blessing")
    bot.Wait.ForTime(1500)
    bot.Move.XYAndDialog(4835, 440, 0x84)
    bot.States.AddCustomState(lambda: _send_local_dialog(bot, 0x85), "Local Dialog 0x85")

    # Path segment 3
    bot.Move.XY(-1346, 12360, "Moving")
    bot.Move.XY(874, 14367, "Moving")
    bot.Move.XY(3572, 13698, "Krait Group Standing")
    bot.Move.XY(5899, 14205, "Moving")
    bot.Move.XY(7407, 11867, "Krait Group")
    bot.Move.XY(9541, 9027, "Rider")
    bot.Move.XY(12639, 7537, "Rider Group")
    bot.Move.XY(9064, 7312, "Rider")
    bot.Move.XY(7986, 4365, "Krait group")
    bot.Move.XY(8558, 2759, "Moving")
    bot.Move.XY(10685, 3500, "Moving")
    bot.Move.XY(10202, 5369, "Moving")
    bot.Move.XY(8043, 5949, "Moving")
    bot.Move.XY(7978, 3339, "Moving")
    bot.Move.XY(6341, 3029, "Krait Group")
    bot.Move.XY(5362, 3391, "Moving")
    bot.Move.XY(7097, 92, "Krait Group")
    bot.Move.XY(8943, -985, "Krait Boss")
    bot.Move.XY(10949, -2056, "Krait Patrol")
    bot.Move.XY(13780, -5667, "Rider Patrol")
    bot.Move.XY(10752, 991, "Moving")
    bot.Move.XY(8193, -841, "Moving Back")
    bot.Move.XY(3284, -1599, "Krait Group")
    bot.Move.XY(-76, -1498, "Krait Group")
    bot.Move.XY(578, 719, "Krait Group")
    bot.Move.XY(1703, 3975, "Moving")
    bot.Move.XY(316, 2489, "Krait Group")
    bot.Move.XY(-1018, -1235, "Moving Back")
    bot.Move.XY(-3195, -1538, "Krait Patrol")
    bot.Move.XY(-6322, -2565, "Krait Group")
    bot.Move.XY(-11414, 4055, "Leftovers Krait")
    bot.Move.XY(-7030, 8396, "Moving")
    bot.Move.XY(-8689, 11227, "Leftovers Krait and Rider")
    bot.Move.XY(4671, -8699, "Krait Patrol")
    bot.Move.XY(-1018, -1235, "Moving Back")
    bot.Move.XY(-6322, -2565, "Krait Group")
    bot.Move.XY(-8760, -9933, "Krait Boss Warrior")
    bot.Map.Travel(target_map_id=RATASUM)
    bot.States.JumpToStepName(ZONING_STEP_NAME)


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
        yield from bot.helpers.Items.use_conset()
    if _as_bool(bot.Properties.Get("use_pcons", "active")):
        yield from bot.helpers.Items.use_pcons()


def _restock_models_locally(model_ids: list[int], quantity: int):
    for model_id in model_ids:
        yield from Routines.Yield.Items.RestockItems(model_id, quantity)
# endregion


# region Events
def _on_party_wipe(bot: "Botting"):
    if not Routines.Checks.Map.MapValid() or not Routines.Checks.Map.IsExplorable():
        bot.config.FSM.resume()
        return
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid() or not Routines.Checks.Map.IsExplorable():
            # Map invalid â†’ release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map â†’ jump to recovery step
    if not Routines.Checks.Map.MapValid() or not Routines.Checks.Map.IsExplorable():
        bot.config.FSM.resume()
        return

    bot.States.JumpToStepName(START_COMBAT_STEP_NAME)
    bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
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
    # Single wait for all heroes to join
    yield from bot.Wait._coro_for_time(1000)
    # Load skill templates
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
    bot.UI.SendChatCommand("resign")
    yield from bot.Wait._coro_for_time(500)


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
    PyImGui.text_colored("Asura Title Farm", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Single account, farm Asura title in Magus Stones")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Wick Divinus")
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
    title_idx = int(TitleID.Asuran)
    tiers = TITLE_TIERS.get(TitleID.Asuran, [])
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


REFORGED_TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "Wick Divinus bots", "Reforged_Icon.png")
_EXPANDED_TAB_CHILD_SIZE = (500, 620)
# endregion


# region Entry Point
_hero_config_loaded = False


def _draw_statistics_tab() -> None:
    import PyImGui
    if PyImGui.begin_child("AsuraStatisticsTabChild", _EXPANDED_TAB_CHILD_SIZE, False):
        _draw_title_track()
    PyImGui.end_child()


def _draw_heroes_tab() -> None:
    import PyImGui
    if PyImGui.begin_child("AsuraHeroesTabChild", _EXPANDED_TAB_CHILD_SIZE, False):
        _draw_hero_settings_tab()
    PyImGui.end_child()


def main():
    global _hero_config_loaded
    if not _hero_config_loaded:
        _load_hero_config()
        _hero_config_loaded = True
    if Map.IsMapLoading():
        return
    bot.Update()
    bot.UI.draw_window(icon_path=REFORGED_TEXTURE, extra_tabs=[
        ("Statistics", _draw_statistics_tab),
        ("Heroes", _draw_heroes_tab),
    ])


if __name__ == "__main__":
    main()
# endregion
