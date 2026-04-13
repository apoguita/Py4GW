# region Imports & Config
from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Agent, Player, ConsoleLog, IniManager, HeroType, AgentArray, SharedCommandType
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
from Py4GWCoreLib.botting_src.property import Property
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
import Py4GW
import os
import random
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

_MULTIBOX_ALTS_KEY = "use_multibox_alts"
_party_mode: int = 0  # 0 = Single Account with Heroes, 1 = Multiboxing
_mode_loaded: bool = False

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
_USE_RESTOCK_KITS_KEY = "use_restock_kits"
_ID_KITS_TARGET_KEY = "id_kits_target"
_SALVAGE_KITS_TARGET_KEY = "salvage_kits_target"
_MERCHANT_SELL_MATERIALS_KEY = "merchant_sell_materials"
_MERCHANT_ALT_WAIT_MS_KEY = "merchant_alt_wait_ms"
_RANDOMIZE_DISTRICT_KEY = "randomize_district"
_DEFAULT_ID_KITS_TARGET = 2
_DEFAULT_SALVAGE_KITS_TARGET = 5
_DEFAULT_ALT_SETTLE_WAIT_MS = 2000
_MAX_ALT_SETTLE_WAIT_MS = 5000

_restock_kits_enabled: bool = False
_id_kits_target: int = _DEFAULT_ID_KITS_TARGET
_salvage_kits_target: int = _DEFAULT_SALVAGE_KITS_TARGET
_merchant_sell_materials: bool = False
_merchant_alt_wait_ms: int = _DEFAULT_ALT_SETTLE_WAIT_MS
_randomize_district: bool = True
_SCROLL_MODEL_IDS = {5594, 5595, 5611, 5853, 5975, 5976, 21233}
_SCROLL_MODEL_FILTER = "5594,5595,5611,5853,5975,5976,21233"
_MERCHANT_MANAGED_WIDGETS = ("InventoryPlus",)
_PRETRAVEL_DISABLE_WIDGETS = ("InventoryPlus",)
_RANDOM_DISTRICTS = [6, 7, 8, 9]

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
    if _party_mode == 1:
        bot.Templates.Multibox_Aggressive()
    else:
        bot.Templates.Aggressive()
    bot.Properties.Enable("auto_inventory_management")
# endregion


# region Bot Routine
def Routine(bot: Botting) -> None:
    _ensure_mode_loaded(bot)
    PrepareForCombat(bot)
    Fight(bot)


def PrepareForCombat(bot: Botting) -> None:
    bot.States.AddHeader("Prepare For Farm")
    _load_consumable_settings(bot)
    _load_kit_restock_settings(bot)
    _sync_consumable_toggles(bot)
    bot.States.AddCustomState(lambda: _gh_merchant_setup_if_enabled(bot, RATASUM), "GH Merchant Setup If Enabled")
    bot.States.AddCustomState(lambda: _coro_travel_random_district(bot, RATASUM), "Travel to Rata Sum")
    bot.States.AddCustomState(lambda: _maybe_setup_heroes(bot), "Setup Heroes")
    bot.States.AddCustomState(lambda: _restock_consumables_if_enabled(bot), "Restock Consumables If Enabled")
    bot.Party.SetHardMode(True)


def Fight(bot: Botting) -> None:
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    bot.Events.OnPartyMemberBehindCallback(lambda: bot.Templates.Routines.OnPartyMemberBehind())
    bot.Events.OnPartyMemberInDangerCallback(lambda: bot.Templates.Routines.OnPartyMemberInDanger())
    bot.Events.OnPartyMemberDeadBehindCallback(lambda: bot.Templates.Routines.OnPartyMemberDeathBehind())
    #end events
    bot.States.AddHeader("Zoning into explorable area")
    bot.Move.XY(-6062, -2688,"Exit Outpost")
    bot.Wait.ForMapLoad(target_map_name="Magus Stones")
    ConfigureAggressiveEnv(bot)
    bot.States.AddHeader("Start Combat")
    bot.States.AddCustomState(lambda: PrepareForBattle(bot), "Use Consumables If Enabled")
    bot.States.AddCustomState(lambda x=14778.00, y=13178.00: _take_asura_blessing_at(bot, x, y), "Take Blessing")

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
    bot.States.AddCustomState(lambda x=-9317, y=-2618: _take_asura_blessing_at(bot, x, y), "Take Blessing")

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
    bot.States.AddCustomState(lambda x=4835, y=440: _take_asura_blessing_at(bot, x, y), "Take Blessing")

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
    if _party_mode == 1:
        bot.Multibox.ResignParty()
        bot.Wait.UntilOnOutpost()
    else:
        bot.Map.Travel(target_map_id=RATASUM)
    bot.States.JumpToStepName("[H]Prepare For Farm_1")

def PrepareForBattle(bot: Botting):
    _sync_consumable_toggles(bot)
    yield from _use_consumables_if_enabled(bot)


bot.UI.override_draw_config(lambda: _draw_settings(bot))

bot.SetMainRoutine(Routine)
# endregion


# region Merchant
def _find_npc_xy_by_name(name_fragment: str, max_dist: float = 15000.0):
    npcs = AgentArray.GetNPCMinipetArray()
    npcs = AgentArray.Filter.ByDistance(npcs, Player.GetXY(), max_dist)
    for npc_id in npcs:
        npc_name = Agent.GetNameByID(int(npc_id))
        if name_fragment.lower() in npc_name.lower():
            return Agent.GetXY(int(npc_id))
    return None


def _restock_kits_locally(bot: Botting, x: float, y: float):
    yield from bot.Move._coro_xy_and_interact_npc(x, y)
    yield from bot.Wait._coro_for_time(1200)

    id_kits = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Identification_Kit.value))
    sup_id_kits = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Superior_Identification_Kit.value))
    salvage_kits = int(GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Salvage_Kit.value))

    id_to_buy = max(0, _id_kits_target - (id_kits + sup_id_kits))
    salvage_to_buy = max(0, _salvage_kits_target - salvage_kits)

    yield from Routines.Yield.Merchant.BuyIDKits(id_to_buy, log=True)
    yield from Routines.Yield.Merchant.BuySalvageKits(salvage_to_buy, log=True)


def _restock_kits_if_enabled(bot: Botting):
    yield from _gh_merchant_setup_if_enabled(bot, RATASUM)


def _coro_travel_random_district(bot: Botting, target_map_id: int):
    if _randomize_district:
        district = random.choice(_RANDOM_DISTRICTS)
        ConsoleLog(BOT_NAME, f"Traveling to map {target_map_id} with random EU district {district}")
        Map.TravelToDistrict(target_map_id, district=district)
        yield from Routines.Yield.wait(500)
        yield from bot.Wait._coro_for_map_load(target_map_id=target_map_id)
        return
    yield from bot.Map._coro_travel(target_map_id, "")


def _get_leftover_material_item_ids(batch_size: int = 10) -> list[int]:
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    leftovers: list[int] = []
    for item_id in item_array:
        if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
            continue
        if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
            continue
        qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
        if 0 < qty < batch_size:
            leftovers.append(int(item_id))
    return leftovers


def _coro_sell_scrolls(bot: Botting, mx: float, my: float):
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sell_ids = [int(item_id) for item_id in item_array if int(GLOBAL_CACHE.Item.GetModelID(item_id)) in _SCROLL_MODEL_IDS]
    if not sell_ids:
        return
    yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (scrolls)")
    yield from Routines.Yield.wait(1200)
    yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
    yield from Routines.Yield.wait(300)


def _coro_sell_nonsalvageable_golds(bot: Botting, mx: float, my: float):
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sell_ids = []
    for item_id in item_array:
        _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
        if rarity != "Gold":
            continue
        if not GLOBAL_CACHE.Item.Usage.IsIdentified(item_id):
            continue
        if GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id):
            continue
        sell_ids.append(int(item_id))
    if not sell_ids:
        return
    yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (non-salvageable golds)")
    yield from Routines.Yield.wait(1200)
    yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
    yield from Routines.Yield.wait(300)


def _disable_inventoryplus_pretravel():
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    wh = _get_wh()
    for name in _PRETRAVEL_DISABLE_WIDGETS:
        wh.disable_widget(name)
    my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != my_email:
            for name in _PRETRAVEL_DISABLE_WIDGETS:
                GLOBAL_CACHE.ShMem.SendMessage(my_email, acc.AccountEmail, SharedCommandType.DisableWidget, (0, 0, 0, 0), (name, "", "", ""))
    yield from Routines.Yield.wait(1500)


def _disable_merchant_widgets():
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    wh = _get_wh()
    for name in _MERCHANT_MANAGED_WIDGETS:
        wh.disable_widget(name)
    my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != my_email:
            for name in _MERCHANT_MANAGED_WIDGETS:
                GLOBAL_CACHE.ShMem.SendMessage(my_email, acc.AccountEmail, SharedCommandType.DisableWidget, (0, 0, 0, 0), (name, "", "", ""))
    yield


def _reenable_merchant_widgets():
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    wh = _get_wh()
    for name in _MERCHANT_MANAGED_WIDGETS:
        wh.enable_widget(name)

    my_email = Player.GetAccountEmail()
    refs: list[tuple[str, int]] = []
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != my_email:
            for name in _MERCHANT_MANAGED_WIDGETS:
                idx = int(GLOBAL_CACHE.ShMem.SendMessage(my_email, acc.AccountEmail, SharedCommandType.EnableWidget, (0, 0, 0, 0), (name, "", "", "")))
                if idx >= 0:
                    refs.append((acc.AccountEmail, idx))
    yield from _wait_for_alt_dispatch_completion("enable_widgets", refs, SharedCommandType.EnableWidget, timeout_ms=15000)


def _dispatch_to_alts(command, params, extra_data=("", "", "", "")) -> list[tuple[str, int]]:
    my_email = Player.GetAccountEmail()
    refs: list[tuple[str, int]] = []
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != my_email:
            idx = int(GLOBAL_CACHE.ShMem.SendMessage(my_email, acc.AccountEmail, command, params, extra_data))
            refs.append((acc.AccountEmail, idx))
    return refs


def _wait_for_alt_dispatch_completion(stage_name: str, message_refs: list[tuple[str, int]], command, timeout_ms: int = 30000):
    if not message_refs:
        return
    pending = {(email, idx): None for email, idx in message_refs if int(idx) >= 0}
    if not pending:
        return
    deadline = time.monotonic() + (max(0, int(timeout_ms)) / 1000.0)
    my_email = Player.GetAccountEmail()
    while pending and time.monotonic() < deadline:
        completed: list[tuple[str, int]] = []
        for email, idx in list(pending.keys()):
            message = GLOBAL_CACHE.ShMem.GetInbox(idx)
            is_same_message = (
                bool(getattr(message, "Active", False))
                and str(getattr(message, "ReceiverEmail", "") or "") == email
                and str(getattr(message, "SenderEmail", "") or "") == my_email
                and int(getattr(message, "Command", -1)) == int(command)
            )
            if not is_same_message:
                completed.append((email, idx))
        for key in completed:
            pending.pop(key, None)
        if pending:
            yield from Routines.Yield.wait(50)
    if pending:
        pending_accounts = ", ".join(sorted({email for email, _ in pending}))
        ConsoleLog(BOT_NAME, f"[Merchant] {stage_name}: timeout waiting for alt completion. Pending: {pending_accounts}", Py4GW.Console.MessageType.Warning)


def _wait_for_alts_on_current_map(stage_name: str, expected_alts: int, target_map_id: int, timeout_ms: int = 30000):
    if _party_mode != 1:
        return
    if expected_alts <= 0:
        return
    my_email = Player.GetAccountEmail()
    deadline = time.time() + (max(0, int(timeout_ms)) / 1000.0)
    while time.time() < deadline:
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        arrived = sum(
            1 for acc in accounts
            if acc.AccountEmail != my_email and int(getattr(acc.AgentData.Map, "MapID", 0) or 0) == target_map_id
        )
        if arrived >= expected_alts:
            yield from Routines.Yield.wait(1000)
            return
        yield from Routines.Yield.wait(500)
    ConsoleLog(BOT_NAME, f"[Merchant] {stage_name}: alt arrival timeout on map {target_map_id}", Py4GW.Console.MessageType.Warning)


def _kick_current_party_accounts():
    own_login = int(Player.GetLoginNumber() or 0)
    for member in list(GLOBAL_CACHE.Party.GetPlayers()):
        login_number = int(getattr(member, "login_number", 0) or 0)
        if login_number <= 0 or login_number == own_login:
            continue
        player_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
        if player_name:
            GLOBAL_CACHE.Party.Players.KickPlayer(str(player_name))


def _gh_merchant_setup_if_enabled(bot: Botting, outpost_id: int):
    if not _restock_kits_enabled:
        return

    if _party_mode == 1:
        _kick_current_party_accounts()
        for _ in range(20):
            yield from bot.Wait._coro_for_time(250)
            if GLOBAL_CACHE.Party.GetPlayerCount() <= 1:
                break

    yield from _disable_inventoryplus_pretravel()

    expected_gh_alts = 0
    travel_refs: list[tuple[str, int]] = []
    if _party_mode == 1:
        my_email = Player.GetAccountEmail()
        expected_gh_alts = len([acc for acc in GLOBAL_CACHE.ShMem.GetAllAccountData() if acc.AccountEmail != my_email])
        travel_refs = _dispatch_to_alts(SharedCommandType.TravelToGuildHall, (0, 0, 0, 0))

    if not Map.IsGuildHall():
        Map.TravelGH()
    yield from bot.Wait._coro_until_on_outpost()
    if _party_mode == 1:
        yield from _wait_for_alt_dispatch_completion("travel_gh", travel_refs, SharedCommandType.TravelToGuildHall, timeout_ms=10000)

    gh_deadline = time.time() + 30.0
    while not Map.IsGuildHall() and time.time() < gh_deadline:
        yield from Routines.Yield.wait(500)
    if not Map.IsGuildHall():
        ConsoleLog(BOT_NAME, "[Merchant] Failed to reach Guild Hall, skipping merchant setup", Py4GW.Console.MessageType.Warning)
        return

    if _party_mode == 1:
        yield from _wait_for_alts_on_current_map("travel_gh_arrival", expected_gh_alts, int(Map.GetMapID()), timeout_ms=60000)

    npc_deadline = time.time() + 20.0
    while _find_npc_xy_by_name("Merchant", max_dist=30000.0) is None and time.time() < npc_deadline:
        yield from Routines.Yield.wait(500)

    yield from _disable_merchant_widgets()

    merchant_xy = _find_npc_xy_by_name("Merchant", max_dist=30000.0)
    mat_xy = _find_npc_xy_by_name("Material Trader", max_dist=30000.0) if _merchant_sell_materials else None

    if _merchant_sell_materials and mat_xy:
        tmx, tmy = mat_xy
        sell_mat_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (tmx, tmy, 0, 0), ("sell", "", "", "")) if _party_mode == 1 else []
        yield from Routines.Yield.Merchant.SellMaterialsAtTrader(tmx, tmy)
        if _party_mode == 1:
            yield from _wait_for_alt_dispatch_completion("sell_materials", sell_mat_refs, SharedCommandType.MerchantMaterials)

        if merchant_xy:
            mx, my = merchant_xy
            leftover_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (mx, my, 0, 0), ("sell_merchant_leftovers", "", "10", "")) if _party_mode == 1 else []
            leftover_ids = _get_leftover_material_item_ids()
            if leftover_ids:
                yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (leftovers)")
                yield from Routines.Yield.wait(1200)
                yield from Routines.Yield.Merchant.SellItems(leftover_ids, log=True)
                yield from Routines.Yield.wait(300)
            if _party_mode == 1:
                yield from _wait_for_alt_dispatch_completion("sell_merchant_leftovers", leftover_refs, SharedCommandType.MerchantMaterials)

    if merchant_xy:
        mx, my = merchant_xy
        sell_gold_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (mx, my, 0, 0), ("sell_nonsalvageable_golds", "", "", "")) if _party_mode == 1 else []
        yield from _coro_sell_nonsalvageable_golds(bot, mx, my)
        if _party_mode == 1:
            yield from _wait_for_alt_dispatch_completion("sell_nonsalvageable_golds", sell_gold_refs, SharedCommandType.MerchantMaterials)

        sell_scroll_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (mx, my, 0, 0), ("sell_scrolls", _SCROLL_MODEL_FILTER, "", "")) if _party_mode == 1 else []
        yield from _coro_sell_scrolls(bot, mx, my)
        if _party_mode == 1:
            yield from _wait_for_alt_dispatch_completion("sell_scrolls", sell_scroll_refs, SharedCommandType.MerchantMaterials)

        kit_refs = _dispatch_to_alts(SharedCommandType.MerchantItems, (mx, my, _id_kits_target, _salvage_kits_target)) if _party_mode == 1 else []
        yield from _restock_kits_locally(bot, mx, my)
        if _party_mode == 1:
            yield from _wait_for_alt_dispatch_completion("restock_kits", kit_refs, SharedCommandType.MerchantItems)

    if _merchant_alt_wait_ms > 0:
        yield from Routines.Yield.wait(_merchant_alt_wait_ms)

    #yield from _coro_travel_random_district(bot, outpost_id)
    if _party_mode == 1:
        yield from Routines.Yield.wait(1500)
    yield from _reenable_merchant_widgets()
# endregion


# region Consumables
def _restock_consumables_if_enabled(bot: Botting):
    _sync_consumable_toggles(bot)
    if _party_mode == 1:
        if _as_bool(bot.Properties.Get("use_conset", "active")):
            yield from bot.helpers.Multibox._restock_conset_message(250)
        if _as_bool(bot.Properties.Get("use_pcons", "active")):
            yield from bot.helpers.Multibox._restock_all_pcons_message(250)
        return
    if _as_bool(bot.Properties.Get("use_conset", "active")):
        yield from _restock_models_locally(CONSET_RESTOCK_MODELS, 250)
    if _as_bool(bot.Properties.Get("use_pcons", "active")):
        yield from _restock_models_locally(PCON_RESTOCK_MODELS, 250)


def _use_consumables_if_enabled(bot: Botting):
    _sync_consumable_toggles(bot)
    if _party_mode == 1:
        yield from _use_multibox_consumables(bot)
        return
    if _as_bool(bot.Properties.Get("use_conset", "active")):
        yield from bot.helpers.Items.use_conset()
    if _as_bool(bot.Properties.Get("use_pcons", "active")):
        yield from bot.helpers.Items.use_pcons()


def _restock_models_locally(model_ids: list[int], quantity: int):
    for model_id in model_ids:
        yield from Routines.Yield.Items.RestockItems(model_id, quantity)


def _use_multibox_consumables(bot: Botting):
    if _as_bool(bot.Properties.Get("use_conset", "active")):
        for model_id, effect_name in CONSET_ITEMS:
            yield from bot.helpers.Multibox._use_consumable_message((
                model_id,
                GLOBAL_CACHE.Skill.GetID(effect_name),
                0,
                0,
            ))
    if _as_bool(bot.Properties.Get("use_pcons", "active")):
        for model_id, effect_name in PCON_ITEMS:
            yield from bot.helpers.Multibox._use_consumable_message((
                model_id,
                GLOBAL_CACHE.Skill.GetID(effect_name),
                0,
                0,
            ))
        yield from bot.helpers.Multibox._use_consumable_message((
            ModelID.Honeycomb.value,
            0,
            0,
            0,
        ))
# endregion


# region Upkeep
def _upkeep_consumables(bot: "Botting"):
    while True:
        yield from bot.Wait._coro_for_time(15000)
        if not Routines.Checks.Map.MapValid() or Routines.Checks.Map.IsOutpost():
            continue
        if _party_mode == 1:
            yield from _use_multibox_consumables(bot)
            continue
        if _as_bool(bot.Properties.Get("use_conset", "active")):
            yield from bot.helpers.Items.use_conset()
        if _as_bool(bot.Properties.Get("use_pcons", "active")):
            yield from bot.helpers.Items.use_pcons()
            for _ in range(4):
                honeycomb_item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Honeycomb.value)
                if not honeycomb_item_id:
                    break
                GLOBAL_CACHE.Inventory.UseItem(honeycomb_item_id)
                yield from bot.Wait._coro_for_time(250)
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


def _load_kit_restock_settings(bot: Botting) -> None:
    global _restock_kits_enabled, _id_kits_target, _salvage_kits_target, _merchant_sell_materials, _merchant_alt_wait_ms
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    _restock_kits_enabled = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _USE_RESTOCK_KITS_KEY,
        _restock_kits_enabled,
    )
    _id_kits_target = max(0, int(IniManager().read_int(
        ini_key,
        _SETTINGS_SECTION,
        _ID_KITS_TARGET_KEY,
        _id_kits_target,
    )))
    _salvage_kits_target = max(0, int(IniManager().read_int(
        ini_key,
        _SETTINGS_SECTION,
        _SALVAGE_KITS_TARGET_KEY,
        _salvage_kits_target,
    )))
    _merchant_sell_materials = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _MERCHANT_SELL_MATERIALS_KEY,
        _merchant_sell_materials,
    )
    _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, int(IniManager().read_int(
        ini_key,
        _SETTINGS_SECTION,
        _MERCHANT_ALT_WAIT_MS_KEY,
        _merchant_alt_wait_ms,
    ))))


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


def _save_kit_restock_settings(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _USE_RESTOCK_KITS_KEY, bool(_restock_kits_enabled))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _ID_KITS_TARGET_KEY, int(_id_kits_target))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _SALVAGE_KITS_TARGET_KEY, int(_salvage_kits_target))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MERCHANT_SELL_MATERIALS_KEY, bool(_merchant_sell_materials))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MERCHANT_ALT_WAIT_MS_KEY, int(_merchant_alt_wait_ms))


def _ensure_consumable_settings_ui_loaded(bot: Botting) -> None:
    if getattr(bot.config, "_consumable_settings_ui_loaded", False):
        return
    _load_consumable_settings(bot)
    _load_kit_restock_settings(bot)
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
    if _party_mode == 1:
        _kick_current_party_accounts()
    else:
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


def _maybe_setup_heroes(bot: Botting):
    if _party_mode == 1:
        yield from bot.helpers.Multibox._summon_all_accounts()
        yield from bot.Wait._coro_for_time(4000)
        yield from bot.helpers.Multibox._invite_all_accounts()
        return
    yield from _setup_heroes(bot)


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
def _load_mode_setting(bot: Botting) -> None:
    global _party_mode, _randomize_district
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    raw = IniManager().read_bool(ini_key, _SETTINGS_SECTION, _MULTIBOX_ALTS_KEY, False)
    _party_mode = 1 if raw else 0
    _randomize_district = IniManager().read_bool(ini_key, _SETTINGS_SECTION, _RANDOMIZE_DISTRICT_KEY, _randomize_district)


def _ensure_mode_loaded(bot: Botting) -> None:
    global _mode_loaded
    if _mode_loaded:
        return
    _load_mode_setting(bot)
    _mode_loaded = True


def _save_mode_setting(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MULTIBOX_ALTS_KEY, _party_mode == 1)
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _RANDOMIZE_DISTRICT_KEY, bool(_randomize_district))


def _do_dialog_at(bot: Botting, x: float, y: float, dialog_id: int, broadcast_to_alts: bool = True):
    if _party_mode == 1 and broadcast_to_alts:
        yield from bot.Move._coro_xy_and_interact_npc(x, y)
        yield from bot.Wait._coro_for_time(1500)
        yield from bot.helpers.Multibox._send_dialog_with_target(dialog_id)
        yield from bot.Wait._coro_for_time(1500)
    else:
        yield from bot.Move._coro_xy_and_dialog(x, y, dialog_id)
        yield from bot.Wait._coro_for_time(500)


def _take_asura_blessing_at(bot: Botting, x: float, y: float):
    yield from _do_dialog_at(bot, x, y, 0x84)
    yield from bot.Wait._coro_for_time(6000)


def _draw_settings(bot: Botting):
    import PyImGui

    PyImGui.text("Bot Settings")

    _ensure_consumable_settings_ui_loaded(bot)

    global _party_mode, _randomize_district
    _ensure_mode_loaded(bot)
    PyImGui.separator()
    PyImGui.text("Party Mode:")
    new_mode = PyImGui.radio_button("Single Account with Heroes", _party_mode, 0)
    PyImGui.same_line(0, 16)
    new_mode = PyImGui.radio_button("Multiboxing", new_mode, 1)
    if new_mode != _party_mode:
        _party_mode = new_mode
        _save_mode_setting(bot)
    if _party_mode == 1:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.6, 0.9, 1.0, 1.0))
        PyImGui.text("Resign uses Multibox Party Resign. Hero setup is skipped.")
        PyImGui.pop_style_color(1)
    new_randomize = PyImGui.checkbox("Randomize EU District", _randomize_district)
    if new_randomize != _randomize_district:
        _randomize_district = new_randomize
        _save_mode_setting(bot)
    PyImGui.separator()

    PyImGui.text("Combat Backend")
    PyImGui.text("Current: Auto Combat")

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

    global _restock_kits_enabled, _id_kits_target, _salvage_kits_target, _merchant_sell_materials, _merchant_alt_wait_ms
    PyImGui.separator()
    new_restock_kits = PyImGui.checkbox("Guild Hall merchant on startup", _restock_kits_enabled)
    if new_restock_kits != _restock_kits_enabled:
        _restock_kits_enabled = new_restock_kits
        _save_kit_restock_settings(bot)

    if _restock_kits_enabled:
        new_id_target = PyImGui.input_int("ID Kits target##asura_id", _id_kits_target)
        if new_id_target != _id_kits_target:
            _id_kits_target = max(0, new_id_target)
            _save_kit_restock_settings(bot)

        new_salvage_target = PyImGui.input_int("Salvage Kits target##asura_salv", _salvage_kits_target)
        if new_salvage_target != _salvage_kits_target:
            _salvage_kits_target = max(0, new_salvage_target)
            _save_kit_restock_settings(bot)

        new_sell_materials = PyImGui.checkbox("Sell common materials##asura_sell", _merchant_sell_materials)
        if new_sell_materials != _merchant_sell_materials:
            _merchant_sell_materials = new_sell_materials
            _save_kit_restock_settings(bot)

        new_wait = PyImGui.input_int("Alt settle wait (ms)##asura_alt_wait", _merchant_alt_wait_ms)
        if new_wait != _merchant_alt_wait_ms:
            _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, new_wait))
            _save_kit_restock_settings(bot)


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
    if _party_mode == 1:
        return accounts if accounts else []
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
