from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Map, Agent, AgentArray, ConsoleLog, Player, Timer, IniManager, SharedCommandType
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
import Py4GW
import PyImGui
import os
import random
import time
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
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Enable("auto_loot")
    bot.States.AddCustomState(lambda: _enable_looting(bot), "Enable Looting")
    bot.States.AddCustomState(lambda: _leave_party_before_start(bot), "Leave Party Before Start")
    bot.States.AddCustomState(lambda: _gh_merchant_setup_if_enabled(bot, OUTPOST_TO_TRAVEL), "GH Merchant Setup If Enabled")
    bot.States.AddCustomState(lambda: _coro_travel_random_district(bot, OUTPOST_TO_TRAVEL), "Travel to Mount Qinkai")
    bot.Multibox.SummonAllAccounts()
    bot.Wait.ForTime(4000)
    bot.Multibox.InviteAllAccounts()
    
    bot.Party.SetHardMode(True)
    if _restock_use_conset:
        bot.Multibox.RestockConset(CONSET_RESTOCK_TARGET)
    if _restock_use_pcons:
        bot.Multibox.RestockAllPcons(PCON_RESTOCK_TARGET)
    if _restock_use_summoning_stones:
        bot.Multibox.RestockSummoningStones(SUMMONING_STONES_RESTOCK_TARGET)
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
    if _restock_use_conset:
        bot.Multibox.UseConset()
    if _restock_use_pcons:
        bot.Multibox.UsePcons()
    if _restock_use_summoning_stones:
        bot.Multibox.UseSummoningStone()
    bot.States.AddManagedCoroutine("Upkeep Multibox Consumables", lambda: _upkeep_multibox_consumables(bot))
    
    bot.Move.FollowAutoPath(Vanquish_Path, "Kill Route")
    bot.Wait.UntilOutOfCombat()

    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.States.AddCustomState(lambda: _donate_luxon_if_threshold_met(bot), "Donate Luxon Faction If Threshold Met")
    bot.States.JumpToStepName("[H]VQ Mount Qinkai_1")
    
    
def _leave_party_before_start(bot: "Botting"):
    yield from bot.helpers.Multibox._leave_party_on_all_accounts()
    GLOBAL_CACHE.Party.LeaveParty()
    yield from bot.Wait._coro_for_time(1000)


def _enable_looting(bot: "Botting"):
    bot.Properties.ApplyNow("auto_loot", "active", True)
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


def _upkeep_multibox_consumables(bot :"Botting"):
    while True:
        yield from bot.Wait._coro_for_time(15000)
        if not Routines.Checks.Map.MapValid():
            continue
        
        if Routines.Checks.Map.IsOutpost():
            continue
        
        if _restock_use_conset:
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Essence_Of_Celerity.value, 
                                                GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Grail_Of_Might.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Armor_Of_Salvation.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect"), 0, 0))
        if _restock_use_pcons:
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Birthday_Cupcake.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Golden_Egg.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Golden_Egg_skill"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Candy_Corn.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Candy_Corn_skill"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Candy_Apple.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Candy_Apple_skill"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Slice_Of_Pumpkin_Pie.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Pie_Induced_Ecstasy"), 0, 0))    
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Drake_Kabob.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Drake_Skin"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Bowl_Of_Skalefin_Soup.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Skale_Vigor"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Pahnai_Salad.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Pahnai_Salad_item_effect"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.War_Supplies.value, 
                                                                    GLOBAL_CACHE.Skill.GetID("Well_Supplied"), 0, 0))
            for i in range(1, 5): 
                GLOBAL_CACHE.Inventory.UseItem(ModelID.Honeycomb.value)
                yield from bot.Wait._coro_for_time(250)
        if _restock_use_summoning_stones:
            yield from bot.helpers.Multibox._use_summoning_stone_message()
            

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
    global _randomize_district, _restock_use_conset, _restock_use_pcons, _restock_use_summoning_stones
    global CONSET_RESTOCK_TARGET, PCON_RESTOCK_TARGET, SUMMONING_STONES_RESTOCK_TARGET
    global _restock_kits_enabled, _id_kits_target, _salvage_kits_target
    global _merchant_sell_materials, _merchant_sell_jadeite_shards
    global _merchant_buy_ectos, _merchant_ecto_threshold, _merchant_alt_wait_ms
    global _donation_min_luxon_points

    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return

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
    PyImGui.text("Multibox Consumables")

    new_use_conset = PyImGui.checkbox("Restock & use Conset (Multibox)", _restock_use_conset)
    if new_use_conset != _restock_use_conset:
        _restock_use_conset = new_use_conset
        changed = True

    new_use_pcons = PyImGui.checkbox("Restock & use Pcons (Multibox)", _restock_use_pcons)
    if new_use_pcons != _restock_use_pcons:
        _restock_use_pcons = new_use_pcons
        changed = True

    new_use_summoning = PyImGui.checkbox("Restock & use Summoning Stones (Multibox)", _restock_use_summoning_stones)
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
    if accounts:
        return accounts
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



bot.SetMainRoutine(bot_routine)
bot.UI.override_draw_config(_draw_settings)

def main():
    _ensure_settings_loaded(bot)
    if not _should_suspend_for_loading():
        bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE, extra_tabs=[("Statistics", _draw_statistics_tab)])

if __name__ == "__main__":
    main()
