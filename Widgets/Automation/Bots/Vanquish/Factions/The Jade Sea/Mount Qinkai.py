from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Map, Agent, AgentArray, ConsoleLog, Player, Timer, IniManager, SharedCommandType, HeroType
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
import Py4GW
import PyImGui
import os
import random
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
BOT_NAME = "VQ Mount Qinkai"
MODULE_NAME = "Mount Qinkai (Vanquish)"
MODULE_ICON = "Textures\\Module_Icons\\Vanquish - Mount Qinkai.png"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "ApoSource", "textures", "VQ_Helmet.png")
OUTPOST_TO_TRAVEL = 389 # Mount Qinkai outpost
CAVALON= 193 # Cavalon for faction donation
LOAD_RESUME_STABLE_MS = 1500
CONSET_RESTOCK_TARGET = 250
PCON_RESTOCK_TARGET = 250
SUMMONING_STONES_RESTOCK_TARGET = 10

_restock_use_conset = True
_restock_use_pcons = True
_restock_use_summoning_stones = True
_restock_kits_enabled = False
_id_kits_target = 2
_salvage_kits_target = 5
_merchant_sell_materials = False
_merchant_sell_jadeite_shards = False
_merchant_buy_ectos = False
_merchant_ecto_threshold = 800_000
_merchant_alt_wait_ms = 2000
_donation_min_luxon_points = 10_000
_randomize_district = True
_RANDOM_DISTRICTS = [6, 7, 8, 9]
_settings_loaded = False
_SETTINGS_SECTION = "MountQinkaiSettings"
_MULTIBOX_ALTS_KEY = "use_multibox_alts"
_RANDOMIZE_DISTRICT_KEY = "randomize_district"
_USE_CONSET_KEY = "use_conset"
_USE_PCONS_KEY = "use_pcons"
_USE_SUMMONING_STONES_KEY = "use_summoning_stones"
_USE_RESTOCK_KITS_KEY = "use_restock_kits"
_ID_KITS_TARGET_KEY = "id_kits_target"
_SALVAGE_KITS_TARGET_KEY = "salvage_kits_target"
_MERCHANT_SELL_MATERIALS_KEY = "merchant_sell_materials"
_MERCHANT_SELL_JADEITE_SHARDS_KEY = "merchant_sell_jadeite_shards"
_MERCHANT_BUY_ECTOS_KEY = "merchant_buy_ectos"
_MERCHANT_ECTO_THRESHOLD_KEY = "merchant_ecto_threshold"
_MERCHANT_ALT_WAIT_MS_KEY = "merchant_alt_wait_ms"
_DONATION_MIN_LUXON_POINTS_KEY = "donation_min_luxon_points"
_CONSET_RESTOCK_TARGET_KEY = "conset_restock_target"
_PCON_RESTOCK_TARGET_KEY = "pcon_restock_target"
_SUMMONING_STONES_RESTOCK_TARGET_KEY = "summoning_stones_restock_target"
_MAX_RESTOCK_TARGET = 999
_MAX_ALT_SETTLE_WAIT_MS = 5000
_MIN_DONATION_THRESHOLD = 10_000
_MAX_DONATION_THRESHOLD = 10_000_000
_SCROLL_MODEL_IDS = {5594, 5595, 5611, 5853, 5975, 5976, 21233}
_SCROLL_MODEL_FILTER = "5594,5595,5611,5853,5975,5976,21233"
_JADEITE_SHARD_MODELS = {int(ModelID.Jadeite_Shard.value)}
_JADEITE_SHARD_FILTER = str(int(ModelID.Jadeite_Shard.value))
_MERCHANT_MANAGED_WIDGETS = ("InventoryPlus",)
_PRETRAVEL_DISABLE_WIDGETS = ("InventoryPlus",)
_party_mode: int = 1  # 0 = Single Account with Heroes, 1 = Multiboxing

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


_HERO_OPTIONS: List[HeroType] = [HeroType.None_] + sorted(
    [h for h in HeroType if h != HeroType.None_],
    key=lambda h: _humanize_hero_name(h.name),
)
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
_hero_config_loaded: bool = False

CONSET_ITEMS: list[tuple[int, str]] = [
    (ModelID.Essence_Of_Celerity.value, "Essence_of_Celerity_item_effect"),
    (ModelID.Grail_Of_Might.value, "Grail_of_Might_item_effect"),
    (ModelID.Armor_Of_Salvation.value, "Armor_of_Salvation_item_effect"),
]

PCON_ITEMS: list[tuple[int, str]] = [
    (ModelID.Birthday_Cupcake.value, "Birthday_Cupcake_skill"),
    (ModelID.Golden_Egg.value, "Golden_Egg_skill"),
    (ModelID.Candy_Corn.value, "Candy_Corn_skill"),
    (ModelID.Candy_Apple.value, "Candy_Apple_skill"),
    (ModelID.Slice_Of_Pumpkin_Pie.value, "Pie_Induced_Ecstasy"),
    (ModelID.Drake_Kabob.value, "Drake_Skin"),
    (ModelID.Bowl_Of_Skalefin_Soup.value, "Skale_Vigor"),
    (ModelID.Pahnai_Salad.value, "Pahnai_Salad_item_effect"),
    (ModelID.War_Supplies.value, "Well_Supplied"),
]

CONSET_RESTOCK_MODELS = [m for m, _ in CONSET_ITEMS]
PCON_RESTOCK_MODELS = [m for m, _ in PCON_ITEMS] + [
    ModelID.Honeycomb.value,
    ModelID.Scroll_Of_Resurrection.value,
]

Vanquish_Path:list[tuple[float, float]] = [
      (-13384.42, -9866.60), #snake yetis  
      (-17490.23, -10193.84), #tendril
      (-13498.94, -4763.97),
      (-11674.48, -4599.29), #wallow patrol
      (-14406.66, -2555.92), #hole
      (-13735.23, -1511.41), #exit hole
      (-10319.44, 2159.07), #cave entrance
      (-7937.16, 3062.79), #wallow patrol
      (-9173.34, 7675.70),
      (-8041.39, 8370.92),
      (-4787.85, 6801.43), #clear
      (-3314.36, 7860.74),
      (-2001.17, 9037.19),
      (-6694.74, 2240.26), #out of cave
      (-9176.05, -13.35),
      (-6789.09, 189.53), #just in case
      (-6890.70, -3249.73), #lower wallows
      (-8307.69, -5465.48),
      (-5021.97, -3830.00),
      (-2310.74, -8512.54),
      (1983.03, -8555.85), #lower oxix
      (6484.80, 1017.07), #wallow patrol
      (6212.15, -8736.39), #beach onis
      (11368.18, -7458.21), #beach patrol
      (14728.93, -9258.35),
      (14774.19, -4493.75),
      (11622.91, -4078.38),
      (13287.39, 296.37),
      (16030.41, 6932.02),
      (11591.91, 7965.41), #water
      (10822.86, 9232.65),
      (7920.46, 5972.42),
      (6274.33, 7410.21), #hill
      (5824.00, 5289.97),
      (4266.50, 5832.48),
      
      (1506.29, 1406.74), #last aptrols
      (1737.57, 1202.17),
      (4450.66, 1146.03), #just in case
      (700.20, -398.73),
      (-273.59, -2516.34),
      (95.02, -3131.64),
      (-1687.58, -3565.68),

      
      
    ]

bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True,
              upkeep_hero_ai_active=True,
              upkeep_auto_loot_active=True)

_load_resume_timer = Timer()
_loading_pause_active = False
_session_baselines: dict[str, int] = {}
_session_start_times: dict[str, float] = {}
_EXPANDED_TAB_CHILD_SIZE = (500, 620)
                
def bot_routine(bot: Botting) -> None:
    global Vanquish_Path
    _ensure_settings_loaded(bot)
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    
    bot.States.AddHeader(BOT_NAME)
    _configure_party_environment(bot)
    bot.Properties.Enable("auto_loot")
    bot.States.AddCustomState(lambda: _enable_looting(bot), "Enable Looting")
    bot.States.AddCustomState(lambda: _leave_party_before_start(bot), "Leave Party Before Start")
    bot.States.AddCustomState(lambda: _gh_merchant_setup_if_enabled(bot, OUTPOST_TO_TRAVEL), "GH Merchant Setup If Enabled")
    bot.States.AddCustomState(lambda: _coro_travel_random_district(bot, OUTPOST_TO_TRAVEL), "Travel to Mount Qinkai")
    bot.States.AddCustomState(lambda: _maybe_setup_party(bot), "Setup Party")
    
    bot.Party.SetHardMode(True)
    bot.States.AddCustomState(lambda: _restock_consumables_if_enabled(bot), "Restock Consumables If Enabled")
    bot.Move.XYAndExitMap(-5490, 13672, 200) # Mount Qinkai
    bot.Wait.ForTime(4000)
    
    # Check faction allegiance and get blessing if needed
    current_luxon = Player.GetLuxonData()[0]
    current_kurzick = Player.GetKurzickData()[0]
    
    bot.States.AddCustomState(
        lambda bribe=current_kurzick >= current_luxon: _take_luxon_blessing(bot, bribe),
        "Take Luxon Blessing",
    )
    bot.States.AddHeader("Start Combat") #3
    bot.States.AddCustomState(lambda: _use_consumables_if_enabled(bot), "Use Consumables If Enabled")
    bot.States.AddManagedCoroutine("Upkeep Consumables", lambda: _upkeep_consumables(bot))
    
    bot.Move.FollowAutoPath(Vanquish_Path, "Kill Route")
    bot.Wait.UntilOutOfCombat()

    if _party_mode == 1:
        bot.Multibox.ResignParty()
        bot.Wait.UntilOnOutpost()
    else:
        bot.Map.Travel(target_map_id=OUTPOST_TO_TRAVEL)
    bot.States.AddCustomState(lambda: _donate_luxon_if_threshold_met(bot), "Donate Luxon Faction If Threshold Met")
    bot.States.JumpToStepName("[H]VQ Mount Qinkai_1")
    

def _configure_party_environment(bot: Botting) -> None:
    if _party_mode == 1:
        bot.Templates.Multibox_Aggressive()
    else:
        bot.Templates.Aggressive()
    bot.Properties.Enable("auto_inventory_management")

    
def _leave_party_before_start(bot: "Botting"):
    if _party_mode == 1:
        yield from bot.helpers.Multibox._leave_party_on_all_accounts()
    GLOBAL_CACHE.Party.LeaveParty()
    yield from bot.Wait._coro_for_time(1000)


def _enable_looting(bot: "Botting"):
    bot.Properties.ApplyNow("auto_loot", "active", True)
    if _party_mode == 1:
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            account_email = getattr(account, "AccountEmail", "")
            if not account_email:
                continue
            options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
            if options is None:
                continue
            options.Looting = True
            GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, options)
    bot.ResetHeroAICombatState(
        active=True,
        following=True,
        avoidance=True,
        looting=True,
        targeting=True,
        combat=True,
        skills=True,
    )
    yield


def _dispatch_dialog_to_alts_only(dialog_id: int) -> list[tuple[str, int]]:
    if _party_mode != 1:
        return []
    sender_email = Player.GetAccountEmail()
    target = Player.GetTargetID()
    if not sender_email or target == 0:
        return []

    refs: list[tuple[str, int]] = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = getattr(account, "AccountEmail", "")
        if not account_email or account_email == sender_email:
            continue
        idx = int(GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            account_email,
            SharedCommandType.SendDialogToTarget,
            (target, dialog_id, 0, 0),
        ))
        refs.append((account_email, idx))
    return refs


def _wait_for_alt_dialogs(message_refs: list[tuple[str, int]], timeout_ms: int = 5000):
    pending = {(email, idx) for email, idx in message_refs if idx >= 0}
    elapsed = 0
    while pending and elapsed < timeout_ms:
        completed: list[tuple[str, int]] = []
        for account_email, message_index in pending:
            message = GLOBAL_CACHE.ShMem.GetInbox(message_index)
            if not getattr(message, "Active", False):
                completed.append((account_email, message_index))
        for key in completed:
            pending.discard(key)
        if pending:
            yield from Routines.Yield.wait(250)
            elapsed += 250


def _reset_hero_ai_after_blessing(bot: "Botting") -> None:
    bot.ResetHeroAICombatState(
        active=True,
        following=True,
        avoidance=True,
        looting=True,
        targeting=True,
        combat=True,
        skills=True,
    )


def _send_priest_dialog(bot: "Botting", dialog_id: int):
    target = Player.GetTargetID()
    if target == 0:
        return
    alt_refs = _dispatch_dialog_to_alts_only(dialog_id)
    yield from Routines.Yield.Player.InteractAgent(target)
    yield from bot.Wait._coro_for_time(500)
    Player.SendDialog(dialog_id)
    yield from _wait_for_alt_dialogs(alt_refs)
    yield from bot.Wait._coro_for_time(500)


def _take_luxon_blessing(bot: "Botting", bribe_priest: bool):
    yield from bot.Move._coro_xy_and_interact_npc(-8394, -9801)
    yield from bot.Wait._coro_for_time(500)
    if bribe_priest:
        yield from _send_priest_dialog(bot, 0x84)  # Bribe if Kurzick faction is greater or equal to Luxon.
    yield from _send_priest_dialog(bot, 0x86)      # Get bounty.
    _reset_hero_ai_after_blessing(bot)
    yield from bot.Wait._coro_for_time(500)


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


def _coro_sell_rare_mats_at_trader(x: float, y: float, model_ids: set[int]):
    yield from Routines.Yield.Movement.FollowPath([(x, y)])
    yield from Routines.Yield.wait(100)
    yield from Routines.Yield.Agents.InteractWithAgentXY(x, y)
    yield from Routines.Yield.wait(1000)

    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sold_total = 0
    for item_id in item_array:
        if int(GLOBAL_CACHE.Item.GetModelID(item_id)) not in model_ids:
            continue
        stack_qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
        while stack_qty > 0:
            quoted = yield from Routines.Yield.Merchant._wait_for_quote(
                GLOBAL_CACHE.Trading.Trader.RequestSellQuote,
                item_id,
                timeout_ms=750,
                step_ms=10,
            )
            if quoted <= 0:
                break
            GLOBAL_CACHE.Trading.Trader.SellItem(item_id, quoted)
            new_qty = yield from Routines.Yield.Merchant._wait_for_stack_quantity_drop(
                item_id,
                stack_qty,
                timeout_ms=750,
                step_ms=10,
            )
            if new_qty >= stack_qty:
                break
            sold_total += stack_qty - new_qty
            stack_qty = new_qty
    ConsoleLog(BOT_NAME, f"[Merchant] Sold {sold_total} Jadeite Shard(s) at Rare Material Trader")


def _disable_inventoryplus_pretravel():
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    wh = _get_wh()
    for name in _PRETRAVEL_DISABLE_WIDGETS:
        wh.disable_widget(name)
    if _party_mode != 1:
        yield from Routines.Yield.wait(1500)
        return
    my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = getattr(acc, "AccountEmail", "")
        if account_email and account_email != my_email:
            for name in _PRETRAVEL_DISABLE_WIDGETS:
                GLOBAL_CACHE.ShMem.SendMessage(
                    my_email,
                    account_email,
                    SharedCommandType.DisableWidget,
                    (0, 0, 0, 0),
                    (name, "", "", ""),
                )
    yield from Routines.Yield.wait(1500)


def _disable_merchant_widgets():
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    wh = _get_wh()
    for name in _MERCHANT_MANAGED_WIDGETS:
        wh.disable_widget(name)
    if _party_mode != 1:
        yield
        return
    my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = getattr(acc, "AccountEmail", "")
        if account_email and account_email != my_email:
            for name in _MERCHANT_MANAGED_WIDGETS:
                GLOBAL_CACHE.ShMem.SendMessage(
                    my_email,
                    account_email,
                    SharedCommandType.DisableWidget,
                    (0, 0, 0, 0),
                    (name, "", "", ""),
                )
    yield


def _reenable_merchant_widgets():
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    wh = _get_wh()
    for name in _MERCHANT_MANAGED_WIDGETS:
        wh.enable_widget(name)

    if _party_mode != 1:
        yield
        return

    my_email = Player.GetAccountEmail()
    refs: list[tuple[str, int]] = []
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = getattr(acc, "AccountEmail", "")
        if account_email and account_email != my_email:
            for name in _MERCHANT_MANAGED_WIDGETS:
                idx = int(GLOBAL_CACHE.ShMem.SendMessage(
                    my_email,
                    account_email,
                    SharedCommandType.EnableWidget,
                    (0, 0, 0, 0),
                    (name, "", "", ""),
                ))
                if idx >= 0:
                    refs.append((account_email, idx))
    yield from _wait_for_alt_dispatch_completion("enable_widgets", refs, SharedCommandType.EnableWidget, timeout_ms=15000)


def _dispatch_to_alts(command, params, extra_data=("", "", "", "")) -> list[tuple[str, int]]:
    if _party_mode != 1:
        return []
    my_email = Player.GetAccountEmail()
    refs: list[tuple[str, int]] = []
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = getattr(acc, "AccountEmail", "")
        if account_email and account_email != my_email:
            idx = int(GLOBAL_CACHE.ShMem.SendMessage(my_email, account_email, command, params, extra_data))
            refs.append((account_email, idx))
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
            if getattr(acc, "AccountEmail", "") != my_email
            and int(getattr(acc.AgentData.Map, "MapID", 0) or 0) == target_map_id
        )
        if arrived >= expected_alts:
            yield from Routines.Yield.wait(1000)
            return
        yield from Routines.Yield.wait(500)
    ConsoleLog(BOT_NAME, f"[Merchant] {stage_name}: alt arrival timeout on map {target_map_id}", Py4GW.Console.MessageType.Warning)


def _gh_merchant_setup_if_enabled(bot: Botting, outpost_id: int):
    if not _restock_kits_enabled:
        return

    yield from _disable_inventoryplus_pretravel()

    my_email = Player.GetAccountEmail()
    expected_gh_alts = len([
        acc for acc in GLOBAL_CACHE.ShMem.GetAllAccountData()
        if getattr(acc, "AccountEmail", "") and getattr(acc, "AccountEmail", "") != my_email
    ])
    travel_refs = _dispatch_to_alts(SharedCommandType.TravelToGuildHall, (0, 0, 0, 0))

    if not Map.IsGuildHall():
        Map.TravelGH()
    yield from bot.Wait._coro_until_on_outpost()
    yield from _wait_for_alt_dispatch_completion("travel_gh", travel_refs, SharedCommandType.TravelToGuildHall, timeout_ms=10000)

    gh_deadline = time.time() + 30.0
    while not Map.IsGuildHall() and time.time() < gh_deadline:
        yield from Routines.Yield.wait(500)
    if not Map.IsGuildHall():
        ConsoleLog(BOT_NAME, "[Merchant] Failed to reach Guild Hall, skipping merchant setup", Py4GW.Console.MessageType.Warning)
        return

    yield from _wait_for_alts_on_current_map("travel_gh_arrival", expected_gh_alts, int(Map.GetMapID()), timeout_ms=60000)

    npc_deadline = time.time() + 20.0
    while _find_npc_xy_by_name("Merchant", max_dist=30000.0) is None and time.time() < npc_deadline:
        yield from Routines.Yield.wait(500)

    yield from _disable_merchant_widgets()

    merchant_xy = _find_npc_xy_by_name("Merchant", max_dist=30000.0)
    mat_xy = _find_npc_xy_by_name("Material Trader", max_dist=30000.0) if _merchant_sell_materials else None
    rare_xy = _find_npc_xy_by_name("Rare", max_dist=30000.0) if (_merchant_sell_jadeite_shards or _merchant_buy_ectos) else None

    if _merchant_sell_materials and mat_xy:
        tmx, tmy = mat_xy
        sell_mat_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (tmx, tmy, 0, 0), ("sell", "", "", ""))
        yield from Routines.Yield.Merchant.SellMaterialsAtTrader(tmx, tmy)
        yield from _wait_for_alt_dispatch_completion("sell_materials", sell_mat_refs, SharedCommandType.MerchantMaterials)

        if merchant_xy:
            mx, my = merchant_xy
            leftover_refs = _dispatch_to_alts(
                SharedCommandType.MerchantMaterials,
                (mx, my, 0, 0),
                ("sell_merchant_leftovers", "", "10", ""),
            )
            leftover_ids = _get_leftover_material_item_ids()
            if leftover_ids:
                yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (leftovers)")
                yield from Routines.Yield.wait(1200)
                yield from Routines.Yield.Merchant.SellItems(leftover_ids, log=True)
                yield from Routines.Yield.wait(300)
            yield from _wait_for_alt_dispatch_completion("sell_merchant_leftovers", leftover_refs, SharedCommandType.MerchantMaterials)

    if merchant_xy:
        mx, my = merchant_xy
        sell_gold_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (mx, my, 0, 0),
            ("sell_nonsalvageable_golds", "", "", ""),
        )
        yield from _coro_sell_nonsalvageable_golds(bot, mx, my)
        yield from _wait_for_alt_dispatch_completion("sell_nonsalvageable_golds", sell_gold_refs, SharedCommandType.MerchantMaterials)

        sell_scroll_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (mx, my, 0, 0),
            ("sell_scrolls", _SCROLL_MODEL_FILTER, "", ""),
        )
        yield from _coro_sell_scrolls(bot, mx, my)
        yield from _wait_for_alt_dispatch_completion("sell_scrolls", sell_scroll_refs, SharedCommandType.MerchantMaterials)

        kit_refs = _dispatch_to_alts(SharedCommandType.MerchantItems, (mx, my, _id_kits_target, _salvage_kits_target))
        yield from _restock_kits_locally(bot, mx, my)
        yield from _wait_for_alt_dispatch_completion("restock_kits", kit_refs, SharedCommandType.MerchantItems)

    if _merchant_sell_jadeite_shards:
        if rare_xy:
            rx, ry = rare_xy
            jadeite_refs = _dispatch_to_alts(
                SharedCommandType.MerchantMaterials,
                (rx, ry, 0, 0),
                ("sell_rare_mats", _JADEITE_SHARD_FILTER, "", ""),
            )
            yield from _coro_sell_rare_mats_at_trader(rx, ry, _JADEITE_SHARD_MODELS)
            yield from _wait_for_alt_dispatch_completion("sell_jadeite_shards", jadeite_refs, SharedCommandType.MerchantMaterials)
        else:
            ConsoleLog(BOT_NAME, "[Merchant] No Rare Material Trader found - skipping Jadeite Shard sale", Py4GW.Console.MessageType.Warning)

    if _merchant_buy_ectos:
        if rare_xy:
            rx, ry = rare_xy
            buy_ecto_refs = _dispatch_to_alts(
                SharedCommandType.MerchantMaterials,
                (rx, ry, _merchant_ecto_threshold, _merchant_ecto_threshold),
                ("buy_ectoplasm", "1", "0", ""),
            )
            leader_storage = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())
            if leader_storage > _merchant_ecto_threshold:
                ConsoleLog(
                    BOT_NAME,
                    f"[Merchant] Leader buying ectos (storage={leader_storage:,}, threshold={_merchant_ecto_threshold:,})",
                )
                yield from Routines.Yield.Merchant.BuyEctoplasm(
                    rx,
                    ry,
                    use_storage_gold=True,
                    start_threshold=_merchant_ecto_threshold,
                    stop_threshold=_merchant_ecto_threshold,
                )
            else:
                ConsoleLog(
                    BOT_NAME,
                    f"[Merchant] Leader storage ({leader_storage:,}) at/below threshold - skipping leader ecto buy",
                )
            yield from _wait_for_alt_dispatch_completion("buy_ectoplasm", buy_ecto_refs, SharedCommandType.MerchantMaterials)
        else:
            ConsoleLog(BOT_NAME, "[Merchant] Ecto buy skipped - no Rare Material Trader found", Py4GW.Console.MessageType.Warning)

    if _merchant_alt_wait_ms > 0:
        yield from Routines.Yield.wait(_merchant_alt_wait_ms)

    yield from _reenable_merchant_widgets()


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
        PyImGui.text("Import Team: save another Mount Qinkai hero lineup first.")
        PyImGui.pop_style_color(1)
    PyImGui.separator()

    if PyImGui.begin_child("MountQinkaiHeroSlotsChild", (0, -1), True):
        for i in range(_HERO_SLOTS_COUNT):
            _draw_hero_slot_editor(i)
            if i < _HERO_SLOTS_COUNT - 1:
                PyImGui.separator()
    PyImGui.end_child()


def _setup_heroes(bot: Botting):
    GLOBAL_CACHE.Party.LeaveParty()
    for _ in range(8):
        yield from bot.Wait._coro_for_time(250)
        if GLOBAL_CACHE.Party.GetPlayerCount() <= 1:
            break
    GLOBAL_CACHE.Party.Heroes.KickAllHeroes()
    yield from bot.Wait._coro_for_time(500)

    seen: set[int] = set()
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


def _maybe_setup_party(bot: Botting):
    if _party_mode == 1:
        yield from bot.helpers.Multibox._summon_all_accounts()
        yield from bot.Wait._coro_for_time(4000)
        yield from bot.helpers.Multibox._invite_all_accounts()
        return
    yield from _setup_heroes(bot)


def _restock_models_locally(model_ids: list[int], quantity: int):
    for model_id in model_ids:
        yield from Routines.Yield.Items.RestockItems(model_id, quantity)


def _restock_consumables_if_enabled(bot: Botting):
    if _party_mode == 1:
        if _restock_use_conset:
            yield from bot.helpers.Multibox._restock_conset_message(CONSET_RESTOCK_TARGET)
        if _restock_use_pcons:
            yield from bot.helpers.Multibox._restock_all_pcons_message(PCON_RESTOCK_TARGET)
        if _restock_use_summoning_stones:
            yield from bot.helpers.Multibox._restock_summoning_stones_message(SUMMONING_STONES_RESTOCK_TARGET)
        return
    if _restock_use_conset:
        yield from _restock_models_locally(CONSET_RESTOCK_MODELS, CONSET_RESTOCK_TARGET)
    if _restock_use_pcons:
        yield from _restock_models_locally(PCON_RESTOCK_MODELS, PCON_RESTOCK_TARGET)
    if _restock_use_summoning_stones:
        yield from bot.helpers.Restock._restock_summoning_stones_impl(SUMMONING_STONES_RESTOCK_TARGET)


def _use_multibox_consumables(bot: Botting):
    if _restock_use_conset:
        for model_id, effect_name in CONSET_ITEMS:
            yield from bot.helpers.Multibox._use_consumable_message((
                model_id,
                GLOBAL_CACHE.Skill.GetID(effect_name),
                0,
                0,
            ))
    if _restock_use_pcons:
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
    if _restock_use_summoning_stones:
        yield from bot.helpers.Multibox._use_summoning_stone_message()


def _use_consumables_if_enabled(bot: Botting):
    if _party_mode == 1:
        yield from _use_multibox_consumables(bot)
        return
    if _restock_use_conset:
        yield from bot.helpers.Items.use_conset()
    if _restock_use_pcons:
        yield from bot.helpers.Items.use_pcons()
    if _restock_use_summoning_stones:
        yield from bot.helpers.Items.use_summoning_stone()


def _upkeep_consumables(bot: Botting):
    while True:
        yield from bot.Wait._coro_for_time(15000)
        if not Routines.Checks.Map.MapValid() or Routines.Checks.Map.IsOutpost():
            continue
        if _party_mode == 1:
            yield from _use_multibox_consumables(bot)
            continue
        if _restock_use_conset:
            yield from bot.helpers.Items.use_conset()
        if _restock_use_pcons:
            yield from bot.helpers.Items.use_pcons()
            for _ in range(4):
                honeycomb_item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Honeycomb.value)
                if not honeycomb_item_id:
                    break
                GLOBAL_CACHE.Inventory.UseItem(honeycomb_item_id)
                yield from bot.Wait._coro_for_time(250)
        if _restock_use_summoning_stones:
            yield from bot.helpers.Items.use_summoning_stone()


def _get_account_luxon_points(account, own_email: str) -> int:
    account_email = getattr(account, "AccountEmail", "")
    if account_email == own_email:
        return int(Player.GetLuxonData()[0])
    try:
        return int(account.FactionData.Luxon.Current)
    except Exception:
        return 0


def _get_luxon_donation_candidates() -> list[tuple[str, str, int]]:
    own_email = Player.GetAccountEmail()
    accounts = list(GLOBAL_CACHE.ShMem.GetAllAccountData())
    if _party_mode != 1:
        own_name = Player.GetName()
        for account in accounts:
            account_email = getattr(account, "AccountEmail", "")
            character_name = getattr(getattr(account, "AgentData", None), "CharacterName", "") or account_email
            if account_email == own_email or character_name == own_name:
                return [(account_email or own_email, character_name or own_name, _get_account_luxon_points(account, own_email))]
        return [(own_email, own_name, int(Player.GetLuxonData()[0]))] if own_email else []
    if not accounts:
        return [(own_email, Player.GetName(), int(Player.GetLuxonData()[0]))] if own_email else []

    candidates: list[tuple[str, str, int]] = []
    for account in accounts:
        account_email = getattr(account, "AccountEmail", "")
        if not account_email:
            continue
        character_name = getattr(account.AgentData, "CharacterName", "") or account_email
        luxon_points = _get_account_luxon_points(account, own_email)
        candidates.append((account_email, character_name, luxon_points))
    return candidates


def _donate_luxon_if_threshold_met(bot: Botting):
    threshold = max(_MIN_DONATION_THRESHOLD, min(_MAX_DONATION_THRESHOLD, int(_donation_min_luxon_points)))
    yield from Routines.Yield.wait(1000)

    candidates = _get_luxon_donation_candidates()
    eligible = [(email, name, points) for email, name, points in candidates if points >= threshold]
    if not eligible:
        highest = max((points for _, _, points in candidates), default=0)
        ConsoleLog(
            BOT_NAME,
            f"[Donation] Skipping Cavalon: highest Luxon faction is {highest:,}, threshold is {threshold:,}.",
        )
        return

    ConsoleLog(BOT_NAME, f"[Donation] {len(eligible)} account(s) meet Luxon donation threshold {threshold:,}.")
    yield from _leave_party_before_start(bot)
    yield from _coro_travel_random_district(bot, CAVALON)
    if _party_mode == 1:
        yield from bot.helpers.Multibox._summon_all_accounts()
        yield from bot.Wait._coro_for_time(4000)

    sender_email = Player.GetAccountEmail()
    refs: list[tuple[str, int]] = []
    for account_email, character_name, points in eligible:
        idx = int(GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            account_email,
            SharedCommandType.DonateToGuild,
            (0, 0, 0, 0),
        ))
        refs.append((account_email, idx))
        ConsoleLog(BOT_NAME, f"[Donation] Queued {character_name} ({points:,} Luxon).", log=False)

    yield from _wait_for_alt_dispatch_completion("donate_luxon", refs, SharedCommandType.DonateToGuild, timeout_ms=90000)
    yield from Routines.Yield.wait(1000)


def _coro_travel_random_district(bot: Botting, target_map_id: int):
    if _randomize_district:
        district = random.choice(_RANDOM_DISTRICTS)
        ConsoleLog(BOT_NAME, f"Traveling to map {target_map_id} with random EU district {district}")
        Map.TravelToDistrict(target_map_id, district=district)
        yield from Routines.Yield.wait(500)
        yield from bot.Wait._coro_for_map_load(target_map_id=target_map_id)
        return
    yield from bot.Map._coro_travel(target_map_id, "")


def _upkeep_multibox_consumables(bot: "Botting"):
    yield from _upkeep_consumables(bot)
            

def _reverse_path():
    global Vanquish_Path
    if Map.IsVanquishCompleted():
        Vanquish_Path = []
        yield 
        return
    
    Vanquish_Path = list(reversed(Vanquish_Path))
    yield
    
def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
    bot.States.JumpToStepName("[H]Start Combat_3")
    bot.config.FSM.resume()
    
def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


def _runtime_map_ready() -> bool:
    return bool(Routines.Checks.Map.MapValid() and Player.IsPlayerLoaded())


def _should_suspend_for_loading() -> bool:
    global _loading_pause_active

    if not _runtime_map_ready():
        _loading_pause_active = True
        _load_resume_timer.Stop()
        return True

    if _loading_pause_active:
        if _load_resume_timer.IsStopped():
            _load_resume_timer.Start()
        if not _load_resume_timer.HasElapsed(LOAD_RESUME_STABLE_MS):
            return True
        _loading_pause_active = False
        _load_resume_timer.Stop()

    return False


def _ensure_bot_ini(bot: Botting) -> str:
    if not bot.config.ini_key_initialized:
        bot.config.ini_key = IniManager().ensure_key(
            f"BottingClass/bot_{bot.config.bot_name}",
            f"bot_{bot.config.bot_name}.ini",
        )
        bot.config.ini_key_initialized = True
    return bot.config.ini_key


def _load_settings(bot: Botting) -> None:
    global _party_mode
    global _randomize_district, _restock_use_conset, _restock_use_pcons, _restock_use_summoning_stones
    global CONSET_RESTOCK_TARGET, PCON_RESTOCK_TARGET, SUMMONING_STONES_RESTOCK_TARGET
    global _restock_kits_enabled, _id_kits_target, _salvage_kits_target
    global _merchant_sell_materials, _merchant_sell_jadeite_shards
    global _merchant_buy_ectos, _merchant_ecto_threshold, _merchant_alt_wait_ms
    global _donation_min_luxon_points

    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return

    _party_mode = 1 if IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _MULTIBOX_ALTS_KEY, _party_mode == 1
    ) else 0
    _randomize_district = IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _RANDOMIZE_DISTRICT_KEY, _randomize_district
    )
    _restock_use_conset = IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _USE_CONSET_KEY, _restock_use_conset
    )
    _restock_use_pcons = IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _USE_PCONS_KEY, _restock_use_pcons
    )
    _restock_use_summoning_stones = IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _USE_SUMMONING_STONES_KEY, _restock_use_summoning_stones
    )
    _restock_kits_enabled = IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _USE_RESTOCK_KITS_KEY, _restock_kits_enabled
    )
    _id_kits_target = max(0, int(IniManager().read_int(
        ini_key, _SETTINGS_SECTION, _ID_KITS_TARGET_KEY, _id_kits_target
    )))
    _salvage_kits_target = max(0, int(IniManager().read_int(
        ini_key, _SETTINGS_SECTION, _SALVAGE_KITS_TARGET_KEY, _salvage_kits_target
    )))
    _merchant_sell_materials = IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _MERCHANT_SELL_MATERIALS_KEY, _merchant_sell_materials
    )
    _merchant_sell_jadeite_shards = IniManager().read_bool(
        ini_key,
        _SETTINGS_SECTION,
        _MERCHANT_SELL_JADEITE_SHARDS_KEY,
        _merchant_sell_jadeite_shards,
    )
    _merchant_buy_ectos = IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _MERCHANT_BUY_ECTOS_KEY, _merchant_buy_ectos
    )
    _merchant_ecto_threshold = max(0, int(IniManager().read_int(
        ini_key, _SETTINGS_SECTION, _MERCHANT_ECTO_THRESHOLD_KEY, _merchant_ecto_threshold
    )))
    _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, int(IniManager().read_int(
        ini_key, _SETTINGS_SECTION, _MERCHANT_ALT_WAIT_MS_KEY, _merchant_alt_wait_ms
    ))))
    _donation_min_luxon_points = max(_MIN_DONATION_THRESHOLD, min(_MAX_DONATION_THRESHOLD, int(IniManager().read_int(
        ini_key, _SETTINGS_SECTION, _DONATION_MIN_LUXON_POINTS_KEY, _donation_min_luxon_points
    ))))
    CONSET_RESTOCK_TARGET = max(0, min(_MAX_RESTOCK_TARGET, int(IniManager().read_int(
        ini_key, _SETTINGS_SECTION, _CONSET_RESTOCK_TARGET_KEY, CONSET_RESTOCK_TARGET
    ))))
    PCON_RESTOCK_TARGET = max(0, min(_MAX_RESTOCK_TARGET, int(IniManager().read_int(
        ini_key, _SETTINGS_SECTION, _PCON_RESTOCK_TARGET_KEY, PCON_RESTOCK_TARGET
    ))))
    SUMMONING_STONES_RESTOCK_TARGET = max(0, min(_MAX_RESTOCK_TARGET, int(IniManager().read_int(
        ini_key, _SETTINGS_SECTION, _SUMMONING_STONES_RESTOCK_TARGET_KEY, SUMMONING_STONES_RESTOCK_TARGET
    ))))


def _ensure_settings_loaded(bot: Botting) -> None:
    global _settings_loaded
    if _settings_loaded:
        return
    _load_settings(bot)
    _settings_loaded = True


def _save_settings(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return

    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MULTIBOX_ALTS_KEY, _party_mode == 1)
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _RANDOMIZE_DISTRICT_KEY, bool(_randomize_district))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _USE_CONSET_KEY, bool(_restock_use_conset))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _USE_PCONS_KEY, bool(_restock_use_pcons))
    IniManager().write_key(
        ini_key,
        _SETTINGS_SECTION,
        _USE_SUMMONING_STONES_KEY,
        bool(_restock_use_summoning_stones),
    )
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _USE_RESTOCK_KITS_KEY, bool(_restock_kits_enabled))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _ID_KITS_TARGET_KEY, int(_id_kits_target))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _SALVAGE_KITS_TARGET_KEY, int(_salvage_kits_target))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MERCHANT_SELL_MATERIALS_KEY, bool(_merchant_sell_materials))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MERCHANT_SELL_JADEITE_SHARDS_KEY, bool(_merchant_sell_jadeite_shards))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MERCHANT_BUY_ECTOS_KEY, bool(_merchant_buy_ectos))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MERCHANT_ECTO_THRESHOLD_KEY, int(_merchant_ecto_threshold))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _MERCHANT_ALT_WAIT_MS_KEY, int(_merchant_alt_wait_ms))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _DONATION_MIN_LUXON_POINTS_KEY, int(_donation_min_luxon_points))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _CONSET_RESTOCK_TARGET_KEY, int(CONSET_RESTOCK_TARGET))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _PCON_RESTOCK_TARGET_KEY, int(PCON_RESTOCK_TARGET))
    IniManager().write_key(
        ini_key,
        _SETTINGS_SECTION,
        _SUMMONING_STONES_RESTOCK_TARGET_KEY,
        int(SUMMONING_STONES_RESTOCK_TARGET),
    )


def _draw_settings():
    global _party_mode
    global _restock_use_conset, _restock_use_pcons, _restock_use_summoning_stones
    global CONSET_RESTOCK_TARGET, PCON_RESTOCK_TARGET, SUMMONING_STONES_RESTOCK_TARGET
    global _randomize_district, _restock_kits_enabled, _id_kits_target, _salvage_kits_target
    global _merchant_sell_materials, _merchant_sell_jadeite_shards
    global _merchant_buy_ectos, _merchant_ecto_threshold, _merchant_alt_wait_ms
    global _donation_min_luxon_points

    _ensure_settings_loaded(bot)

    PyImGui.text("Mount Qinkai Settings")
    PyImGui.separator()
    changed = False

    PyImGui.text("Party Mode:")
    new_mode = PyImGui.radio_button("Single Account with Heroes", _party_mode, 0)
    PyImGui.same_line(0, 16)
    new_mode = PyImGui.radio_button("Multiboxing", new_mode, 1)
    if new_mode != _party_mode:
        _party_mode = new_mode
        changed = True
    if _party_mode == 0:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.6, 0.9, 0.6, 1.0))
        PyImGui.text("Single account uses the team configured in the Heroes tab.")
        PyImGui.pop_style_color(1)
    else:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.6, 0.9, 1.0, 1.0))
        PyImGui.text("Multibox mode summons, invites, and controls alt accounts.")
        PyImGui.pop_style_color(1)
    PyImGui.separator()

    new_randomize = PyImGui.checkbox("Randomize EU District", _randomize_district)
    if new_randomize != _randomize_district:
        _randomize_district = new_randomize
        changed = True

    PyImGui.separator()
    PyImGui.text("Faction Donation")

    new_donation_threshold = PyImGui.input_int("Donate at Luxon faction >=##mount_qinkai_donate_threshold", _donation_min_luxon_points)
    new_donation_threshold = max(_MIN_DONATION_THRESHOLD, min(_MAX_DONATION_THRESHOLD, new_donation_threshold))
    if new_donation_threshold != _donation_min_luxon_points:
        _donation_min_luxon_points = new_donation_threshold
        changed = True

    PyImGui.separator()
    PyImGui.text("Consumables")

    new_use_conset = PyImGui.checkbox("Restock & use Conset", _restock_use_conset)
    if new_use_conset != _restock_use_conset:
        _restock_use_conset = new_use_conset
        changed = True

    new_use_pcons = PyImGui.checkbox("Restock & use Pcons", _restock_use_pcons)
    if new_use_pcons != _restock_use_pcons:
        _restock_use_pcons = new_use_pcons
        changed = True

    new_use_summoning = PyImGui.checkbox("Restock & use Summoning Stones", _restock_use_summoning_stones)
    if new_use_summoning != _restock_use_summoning_stones:
        _restock_use_summoning_stones = new_use_summoning
        changed = True

    PyImGui.separator()
    new_conset_target = max(0, min(_MAX_RESTOCK_TARGET, PyImGui.input_int("Conset restock target##mount_qinkai_conset", CONSET_RESTOCK_TARGET)))
    if new_conset_target != CONSET_RESTOCK_TARGET:
        CONSET_RESTOCK_TARGET = new_conset_target
        changed = True

    new_pcon_target = max(0, min(_MAX_RESTOCK_TARGET, PyImGui.input_int("Pcons restock target##mount_qinkai_pcons", PCON_RESTOCK_TARGET)))
    if new_pcon_target != PCON_RESTOCK_TARGET:
        PCON_RESTOCK_TARGET = new_pcon_target
        changed = True

    new_summoning_target = max(0, min(_MAX_RESTOCK_TARGET, PyImGui.input_int("Summoning Stones restock target##mount_qinkai_summoning", SUMMONING_STONES_RESTOCK_TARGET)))
    if new_summoning_target != SUMMONING_STONES_RESTOCK_TARGET:
        SUMMONING_STONES_RESTOCK_TARGET = new_summoning_target
        changed = True

    PyImGui.separator()
    PyImGui.text("Guild Hall Merchant")

    new_restock_kits = PyImGui.checkbox("Guild Hall merchant on startup", _restock_kits_enabled)
    if new_restock_kits != _restock_kits_enabled:
        _restock_kits_enabled = new_restock_kits
        changed = True

    if _restock_kits_enabled:
        new_id_target = PyImGui.input_int("ID Kits target##mount_qinkai_id", _id_kits_target)
        if new_id_target != _id_kits_target:
            _id_kits_target = max(0, new_id_target)
            changed = True

        new_salvage_target = PyImGui.input_int("Salvage Kits target##mount_qinkai_salvage", _salvage_kits_target)
        if new_salvage_target != _salvage_kits_target:
            _salvage_kits_target = max(0, new_salvage_target)
            changed = True

        new_sell_materials = PyImGui.checkbox("Sell common materials##mount_qinkai_sell_materials", _merchant_sell_materials)
        if new_sell_materials != _merchant_sell_materials:
            _merchant_sell_materials = new_sell_materials
            changed = True

        new_sell_jadeite = PyImGui.checkbox("Sell Jadeite Shards to Rare Material Trader##mount_qinkai_jadeite", _merchant_sell_jadeite_shards)
        if new_sell_jadeite != _merchant_sell_jadeite_shards:
            _merchant_sell_jadeite_shards = new_sell_jadeite
            changed = True

        new_buy_ectos = PyImGui.checkbox("Buy Glob of Ectoplasm when storage over threshold##mount_qinkai_ectos", _merchant_buy_ectos)
        if new_buy_ectos != _merchant_buy_ectos:
            _merchant_buy_ectos = new_buy_ectos
            changed = True

        if _merchant_buy_ectos:
            new_ecto_threshold = PyImGui.input_int("Storage threshold (gold)##mount_qinkai_ecto_threshold", _merchant_ecto_threshold)
            if new_ecto_threshold != _merchant_ecto_threshold:
                _merchant_ecto_threshold = max(0, new_ecto_threshold)
                changed = True

        new_wait = PyImGui.input_int("Alt settle wait (ms)##mount_qinkai_alt_wait", _merchant_alt_wait_ms)
        if new_wait != _merchant_alt_wait_ms:
            _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, new_wait))
            changed = True

    if changed:
        _save_settings(bot)


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
    title_id = TitleID.Luxon
    title_idx = int(title_id)
    tiers = TITLE_TIERS.get(title_id, [])
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
        next_required = tiers[0].required if tiers else 0
        for i, tier in enumerate(tiers):
            if pts >= tier.required:
                tier_name = tier.name
                tier_rank = i + 1
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


def _draw_statistics_tab() -> None:
    if PyImGui.begin_child("MountQinkaiStatisticsTabChild", _EXPANDED_TAB_CHILD_SIZE, False):
        PyImGui.text("Luxon Title Statistics")
        _draw_title_track()
    PyImGui.end_child()


def _draw_heroes_tab() -> None:
    if PyImGui.begin_child("MountQinkaiHeroesTabChild", _EXPANDED_TAB_CHILD_SIZE, False):
        _draw_hero_settings_tab()
    PyImGui.end_child()


bot.SetMainRoutine(bot_routine)
bot.UI.override_draw_config(_draw_settings)

def main():
    global _hero_config_loaded
    _ensure_settings_loaded(bot)
    if not _hero_config_loaded:
        _load_hero_config()
        _hero_config_loaded = True
    if not _should_suspend_for_loading():
        bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE, extra_tabs=[
        ("Statistics", _draw_statistics_tab),
        ("Heroes", _draw_heroes_tab),
    ])

if __name__ == "__main__":
    main()
