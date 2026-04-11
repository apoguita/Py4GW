from typing import Callable

import PyMerchant

from Py4GWCoreLib import GLOBAL_CACHE, Inventory, Item
from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, Utils
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler

from Sources.ApoSource.ApoBottingLib import wrappers as BT
from .globals import *
from .helpers import *


def EquipStarterBow() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="Ensure Starter Bow Equipped",
            children=[
                BehaviorTree.SequenceNode(
                    name="Starter Bow Already Equipped",
                    children=[
                        BT.IsItemEquipped(STARTER_BOW_MODEL_ID),
                        LogMessage("Starter Bow is already equipped"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="Equip Starter Bow",
                    children=[
                        LogMessage("Equipping Starter Bow"),
                        BT.EquipItemByModelID(STARTER_BOW_MODEL_ID),
                        BT.IsItemEquipped(STARTER_BOW_MODEL_ID),
                    ],
                ),
            ],
        )
    )


def _merge_model_lists(*model_lists: list[int]) -> list[int]:
    merged: list[int] = []
    seen: set[int] = set()
    for model_list in model_lists:
        for model_id in model_list:
            if model_id in seen:
                continue
            seen.add(model_id)
            merged.append(model_id)
    return merged


def _without_model(model_ids: list[int], model_id_to_remove: int) -> list[int]:
    return [model_id for model_id in model_ids if model_id != model_id_to_remove]


def _warrior_salvage_exclude_models(exclude_models: list[int]) -> list[int]:
    return _merge_model_lists(list(exclude_models), [DULL_CARAPACES_MODEL_ID])


def _has_model_in_inventory_or_equipped(model_id: int) -> bool:
    return (
        GLOBAL_CACHE.Inventory.GetModelCount(model_id) > 0
        or GLOBAL_CACHE.Inventory.GetModelCountInEquipped(model_id) > 0
        or Inventory.GetModelCount(model_id) > 0
        or Inventory.GetModelCountInEquipped(model_id) > 0
    )


def _collect_sellable_item_ids(exclude_models: list[int] | None = None) -> list[int]:
    excluded_models = set(exclude_models or [])
    sellable_item_ids: list[int] = []
    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue
        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        if model_id in excluded_models:
            continue
        if GLOBAL_CACHE.Item.Properties.GetValue(item_id) <= 0:
            continue
        sellable_item_ids.append(item_id)
    return sellable_item_ids


def _collect_zero_value_item_ids(exclude_models: list[int] | None = None) -> list[int]:
    excluded_models = set(exclude_models or [])
    zero_value_item_ids: list[int] = []
    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue
        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        if model_id in excluded_models:
            continue
        if GLOBAL_CACHE.Item.Properties.GetValue(item_id) > 0:
            continue
        zero_value_item_ids.append(item_id)
    return zero_value_item_ids


def _collect_sellable_item_ids_for_models(model_ids: list[int]) -> list[int]:
    tracked_models = set(model_ids)
    sellable_item_ids: list[int] = []
    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue
        if GLOBAL_CACHE.Item.GetModelID(item_id) not in tracked_models:
            continue
        if GLOBAL_CACHE.Item.Properties.GetValue(item_id) <= 0:
            continue
        sellable_item_ids.append(item_id)
    return sellable_item_ids


def SellSpecificInventoryModels(model_ids: list[int]) -> BehaviorTree:
    tracked_models = set(model_ids)

    def _collect_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        sellable_item_ids = _collect_sellable_item_ids_for_models(list(tracked_models))
        node.blackboard["merchant_sell_item_ids"] = sellable_item_ids
        node.blackboard["merchant_sell_queued_count"] = 0
        return BehaviorTree.NodeState.SUCCESS

    def _queue_sell_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        item_ids = list(node.blackboard.get("merchant_sell_item_ids", []))
        if not item_ids:
            node.blackboard["merchant_sell_queued_count"] = 0
            return BehaviorTree.NodeState.SUCCESS

        merchant_queue = ActionQueueManager()
        merchant_queue.ResetQueue("ACTION")

        queued_count = 0
        for item_id in item_ids:
            quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
            value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
            cost = quantity * value

            if quantity <= 0 or value <= 0:
                continue

            merchant_queue.AddAction(
                "ACTION",
                GLOBAL_CACHE.Trading._merchant_instance.merchant_sell_item,
                item_id,
                cost,
            )
            queued_count += 1

        node.blackboard["merchant_sell_queued_count"] = queued_count
        return BehaviorTree.NodeState.SUCCESS

    def _wait_for_sell_queue_to_finish(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        queued_count = int(node.blackboard.get("merchant_sell_queued_count", 0) or 0)
        if queued_count <= 0:
            return BehaviorTree.NodeState.SUCCESS

        if not ActionQueueManager().IsEmpty("ACTION"):
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="SellSpecificInventoryModels",
            children=[
                BehaviorTree.ActionNode(
                    name="CollectSpecificSellItems",
                    action_fn=_collect_items,
                    aftercast_ms=0,
                ),
                BehaviorTree.ActionNode(
                    name="QueueSpecificMerchantSellItems",
                    action_fn=_queue_sell_items,
                    aftercast_ms=0,
                ),
                BehaviorTree.ActionNode(
                    name="WaitForSpecificMerchantSellQueue",
                    action_fn=_wait_for_sell_queue_to_finish,
                    aftercast_ms=0,
                ),
            ],
        )
    )


def _has_salvage_kit() -> bool:
    return (
        GLOBAL_CACHE.Inventory.GetFirstSalvageKit(use_lesser=False) != 0
        or Inventory.GetFirstSalvageKit(use_lesser=False) != 0
        or _has_model_in_inventory_or_equipped(SALVAGE_KIT_MODEL_ID)
    )


def _has_id_kit() -> bool:
    return (
        GLOBAL_CACHE.Inventory.GetFirstIDKit() != 0
        or Inventory.GetFirstIDKit() != 0
        or _has_model_in_inventory_or_equipped(ID_KIT_MODEL_ID)
    )


def _has_warrior_weapon_materials() -> bool:
    return (
        GLOBAL_CACHE.Inventory.GetModelCount(WOOD_PLANKS_MODEL_ID) >= 1
        and GLOBAL_CACHE.Inventory.GetModelCount(IRON_INGOT_MODEL_ID) >= 4
    )


WARRIOR_AXE_CRAFT_GOLD_COST = 100
WARRIOR_AXE_CUSTOMIZE_GOLD_COST = 10
WARRIOR_AXE_TOTAL_GOLD_REQUIRED = WARRIOR_AXE_CRAFT_GOLD_COST + WARRIOR_AXE_CUSTOMIZE_GOLD_COST


def _needs_warrior_gold_only() -> bool:
    return (
        _has_warrior_weapon_materials()
        and int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter() or 0) < WARRIOR_AXE_TOTAL_GOLD_REQUIRED
    )


def _has_warrior_weapon_recipe_ready() -> bool:
    return (
        _has_warrior_weapon_materials()
        and int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter() or 0) >= WARRIOR_AXE_TOTAL_GOLD_REQUIRED
    )


def _has_warrior_prep_kits() -> bool:
    return _has_salvage_kit() and _has_id_kit()


def _can_afford_missing_warrior_prep_kits() -> bool:
    gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter() or 0)
    required_gold = 0

    if not _has_salvage_kit():
        purchase_data = _get_merchant_item_purchase_data(SALVAGE_KIT_MODEL_ID)
        if purchase_data is None:
            return False
        required_gold += purchase_data[1]

    if not _has_id_kit():
        purchase_data = _get_merchant_item_purchase_data(ID_KIT_MODEL_ID)
        if purchase_data is None:
            return False
        required_gold += purchase_data[1]

    return gold >= required_gold


def _get_merchant_item_purchase_data(model_id: int) -> tuple[int, int] | None:
    for item_id in GLOBAL_CACHE.Trading.Merchant.GetOfferedItems():
        if GLOBAL_CACHE.Item.GetModelID(item_id) != model_id:
            continue
        value = max(0, int(GLOBAL_CACHE.Item.Properties.GetValue(item_id) or 0) * 2)
        return item_id, value
    return None


def _resolve_trade_item_ids(trade_model_ids: list[int], quantity_list: list[int]) -> tuple[list[int], list[int]] | None:
    k = min(len(trade_model_ids), len(quantity_list))
    if k == 0:
        return None

    requested_models = trade_model_ids[:k]
    requested_quantities = quantity_list[:k]
    trade_item_ids: list[int] = []
    trade_item_quantities: list[int] = []

    for model_id, required_quantity in zip(requested_models, requested_quantities):
        remaining_quantity = int(required_quantity)

        for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
            if item_id == 0:
                continue
            if GLOBAL_CACHE.Item.GetModelID(item_id) != model_id:
                continue

            item_quantity = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id) or 1)
            if item_quantity <= 0:
                continue

            used_quantity = min(item_quantity, remaining_quantity)
            trade_item_ids.append(item_id)
            trade_item_quantities.append(used_quantity)
            remaining_quantity -= used_quantity

            if remaining_quantity <= 0:
                break

        if remaining_quantity > 0:
            return None

    return trade_item_ids, trade_item_quantities


def _has_identify_candidates(exclude_models: list[int]) -> bool:
    return _get_identify_candidate(exclude_models) != 0


def _has_salvage_candidates(exclude_models: list[int]) -> bool:
    return _get_salvage_candidate(exclude_models) != 0


def _is_salvage_candidate(item_id: int, exclude_models: list[int]) -> bool:
    excluded = set(exclude_models)
    model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
    if model_id in excluded:
        return False
    if not GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id):
        return False
    if GLOBAL_CACHE.Item.Properties.IsCustomized(item_id):
        return False
    if Item.Rarity.IsGreen(item_id):
        return False
    return Item.Rarity.IsWhite(item_id) or GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)


def _get_identify_candidate(exclude_models: list[int]) -> int:
    excluded = set(exclude_models)
    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue
        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        if model_id in excluded:
            continue
        if not GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id):
            continue
        if GLOBAL_CACHE.Item.Properties.IsCustomized(item_id):
            continue
        if Item.Rarity.IsWhite(item_id) or Item.Rarity.IsGreen(item_id):
            continue
        if GLOBAL_CACHE.Item.Usage.IsIdentified(item_id):
            continue
        return item_id
    return 0


def _get_salvage_candidate(exclude_models: list[int]) -> int:
    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue
        if _is_salvage_candidate(item_id, exclude_models):
            return item_id
    return 0


def _count_identify_candidates(exclude_models: list[int]) -> int:
    count = 0
    excluded = set(exclude_models)
    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue
        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        if model_id in excluded:
            continue
        if not GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id):
            continue
        if GLOBAL_CACHE.Item.Properties.IsCustomized(item_id):
            continue
        if Item.Rarity.IsWhite(item_id) or Item.Rarity.IsGreen(item_id):
            continue
        if GLOBAL_CACHE.Item.Usage.IsIdentified(item_id):
            continue
        count += 1
    return count


def _count_salvage_candidates(exclude_models: list[int]) -> int:
    count = 0
    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue
        if _is_salvage_candidate(item_id, exclude_models):
            count += 1
    return count


def _count_identify_uses_required(exclude_models: list[int]) -> int:
    return _count_identify_candidates(exclude_models)


def _count_salvage_uses_required(exclude_models: list[int]) -> int:
    uses_required = 0
    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue
        if not _is_salvage_candidate(item_id, exclude_models):
            continue
        uses_required += max(1, int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id) or 1))
    return uses_required


def _count_available_id_uses() -> int:
    uses = 0
    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue
        if not GLOBAL_CACHE.Item.Usage.IsIDKit(item_id):
            continue
        uses += max(0, int(GLOBAL_CACHE.Item.Usage.GetUses(item_id) or 0))
    return uses


def _count_available_salvage_uses() -> int:
    uses = 0
    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue
        if not GLOBAL_CACHE.Item.Usage.IsSalvageKit(item_id):
            continue
        uses += max(0, int(GLOBAL_CACHE.Item.Usage.GetUses(item_id) or 0))
    return uses


def _has_enough_id_uses_for_inventory(exclude_models: list[int]) -> bool:
    return _count_available_id_uses() >= _count_identify_uses_required(exclude_models)


def _has_enough_salvage_uses_for_inventory(exclude_models: list[int]) -> bool:
    return _count_available_salvage_uses() >= _count_salvage_uses_required(exclude_models)


def _needs_warrior_inventory_cleanup(exclude_models: list[int]) -> bool:
    return bool(_collect_sellable_item_ids(exclude_models)) or bool(_collect_zero_value_item_ids(exclude_models))


def DebugWarriorMaterialState() -> BehaviorTree:
    def _log(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        wood = GLOBAL_CACHE.Inventory.GetModelCount(WOOD_PLANKS_MODEL_ID)
        iron = GLOBAL_CACHE.Inventory.GetModelCount(IRON_INGOT_MODEL_ID)
        salvage_kit = GLOBAL_CACHE.Inventory.GetModelCount(SALVAGE_KIT_MODEL_ID)
        id_kit = GLOBAL_CACHE.Inventory.GetModelCount(ID_KIT_MODEL_ID)
        gold = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
        LogMessage(
            f"DEBUG Warrior mats: wood={wood}/1 iron={iron}/4 "
            f"salvage_kits={salvage_kit} id_kits={id_kit} gold={gold}/{WARRIOR_AXE_TOTAL_GOLD_REQUIRED}"
        ).root.tick()
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="DebugWarriorMaterialState",
            action_fn=_log,
        )
    )


def DebugWarriorPrepState(exclude_models: list[int]) -> BehaviorTree:
    def _log(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        wood = GLOBAL_CACHE.Inventory.GetModelCount(WOOD_PLANKS_MODEL_ID)
        iron = GLOBAL_CACHE.Inventory.GetModelCount(IRON_INGOT_MODEL_ID)
        salvage_kit = GLOBAL_CACHE.Inventory.GetModelCount(SALVAGE_KIT_MODEL_ID)
        id_kit = GLOBAL_CACHE.Inventory.GetModelCount(ID_KIT_MODEL_ID)
        usable_salvage_kit = int(GLOBAL_CACHE.Inventory.GetFirstSalvageKit(use_lesser=False) or 0)
        usable_id_kit = int(GLOBAL_CACHE.Inventory.GetFirstIDKit() or 0)
        gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter() or 0)
        identify_candidates = _count_identify_candidates(exclude_models)
        salvage_candidates = _count_salvage_candidates(exclude_models)
        identify_uses_required = _count_identify_uses_required(exclude_models)
        salvage_uses_required = _count_salvage_uses_required(exclude_models)
        available_id_uses = _count_available_id_uses()
        available_salvage_uses = _count_available_salvage_uses()
        sellable_count = len(_collect_sellable_item_ids(exclude_models))
        LogMessage(
            "DEBUG Warrior prep: "
            f"wood={wood}/1 iron={iron}/4 "
            f"salvage_kits={salvage_kit} id_kits={id_kit} "
            f"usable_salvage_kit={usable_salvage_kit} usable_id_kit={usable_id_kit} "
            f"gold={gold}/{WARRIOR_AXE_TOTAL_GOLD_REQUIRED} "
            f"identify_candidates={identify_candidates} salvage_candidates={salvage_candidates} "
            f"identify_uses={available_id_uses}/{identify_uses_required} "
            f"salvage_uses={available_salvage_uses}/{salvage_uses_required} "
            f"sellable_count={sellable_count} excluded_models={exclude_models}"
        ).root.tick()
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="DebugWarriorPrepState",
            action_fn=_log,
        )
    )


def _is_model_equipped_strict(model_id: int) -> bool:
    return (
        GLOBAL_CACHE.Inventory.GetModelCountInEquipped(model_id) > 0
        or Inventory.GetModelCountInEquipped(model_id) > 0
    )


def IsItemEquippedStrict(model_id: int, item_name: str) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.ConditionNode(
            name=f"IsItemEquippedStrict({item_name})",
            condition_fn=lambda: _is_model_equipped_strict(model_id),
        )
    )


def DebugItemState(model_id: int, item_name: str) -> BehaviorTree:
    def _log_state(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        cache_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        cache_equipped = GLOBAL_CACHE.Inventory.GetModelCountInEquipped(model_id)
        live_bags = Inventory.GetModelCount(model_id)
        live_equipped = Inventory.GetModelCountInEquipped(model_id)
        strict_equipped = _is_model_equipped_strict(model_id)
        LogMessage(
            f"DEBUG {item_name}: model={model_id} "
            f"cache_bags={cache_bags} cache_equipped={cache_equipped} "
            f"live_bags={live_bags} live_equipped={live_equipped} "
            f"strict_equipped={strict_equipped}"
        ).root.tick()
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"DebugItemState({item_name})",
            action_fn=_log_state,
        )
    )


def EnsureOwnedItemEquipped(model_id: int, item_name: str) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name=f"Ensure {item_name} Equipped",
            children=[
                BehaviorTree.SequenceNode(
                    name=f"{item_name} Already Equipped",
                    children=[
                        DebugItemState(model_id, item_name),
                        IsItemEquippedStrict(model_id, item_name),
                        LogMessage(f"{item_name} is already equipped"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name=f"Equip {item_name} From Inventory",
                    children=[
                        DebugItemState(model_id, f"{item_name} before equip"),
                        BT.IsItemInInventoryBags(model_id),
                        LogMessage(f"Equipping {item_name}"),
                        BT.EquipItemByModelID(model_id),
                        BT.Wait(500),
                        DebugItemState(model_id, f"{item_name} after equip"),
                        IsItemEquippedStrict(model_id, item_name),
                    ],
                ),
            ],
        )
    )


def TryEnsureMerchantItem(model_id: int, item_name: str) -> BehaviorTree:
    def _try_buy(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        if _has_model_in_inventory_or_equipped(model_id):
            return BehaviorTree.NodeState.SUCCESS

        purchase_data = _get_merchant_item_purchase_data(model_id)
        if purchase_data is None:
            LogMessage(f"{item_name} is not offered by this merchant").root.tick()
            return BehaviorTree.NodeState.FAILURE

        item_id, cost = purchase_data
        gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter() or 0)
        if gold < cost:
            LogMessage(f"Not enough gold to buy {item_name} (need {cost}, have {gold})").root.tick()
            return BehaviorTree.NodeState.FAILURE

        LogMessage(f"Buying {item_name} for {cost} gold").root.tick()
        GLOBAL_CACHE.Trading.Merchant.BuyItem(item_id, cost)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"TryEnsureMerchantItem({item_name})",
            action_fn=_try_buy,
            aftercast_ms=500,
        )
    )


def TryTopUpMerchantItemUses(
    model_id: int,
    item_name: str,
    required_uses_fn: Callable[[], int],
    available_uses_fn: Callable[[], int],
    fallback_cost: int,
) -> BehaviorTree:
    def _try_top_up(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        required_uses = int(required_uses_fn() or 0)
        available_uses = int(available_uses_fn() or 0)
        if available_uses >= required_uses:
            return BehaviorTree.NodeState.SUCCESS

        purchase_data = _get_merchant_item_purchase_data(model_id)
        cost = fallback_cost
        item_id = 0
        if purchase_data is not None:
            item_id, discovered_cost = purchase_data
            cost = discovered_cost

        gold = int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter() or 0)
        if item_id == 0:
            LogMessage(
                f"{item_name} top-up unavailable from this merchant "
                f"(uses {available_uses}/{required_uses})"
            ).root.tick()
            return BehaviorTree.NodeState.FAILURE
        if gold < cost:
            LogMessage(
                f"Not enough gold to top up {item_name} "
                f"(uses {available_uses}/{required_uses}, need {cost}, have {gold})"
            ).root.tick()
            return BehaviorTree.NodeState.FAILURE

        LogMessage(
            f"Topping up {item_name} for inventory workload "
            f"(uses {available_uses}/{required_uses})"
        ).root.tick()
        GLOBAL_CACHE.Trading.Merchant.BuyItem(item_id, cost)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"TryTopUpMerchantItemUses({item_name})",
            action_fn=_try_top_up,
            aftercast_ms=500,
        )
    )


def RunWarriorSalvagePrep(exclude_models: list[int]) -> BehaviorTree:
    state: dict[str, object] = {"generator": None}

    def _generator():
        salvage_exclude_models = _warrior_salvage_exclude_models(exclude_models)
        handler = AutoInventoryHandler()
        handler.id_whites = False
        handler.id_blues = True
        handler.id_purples = True
        handler.id_golds = True
        handler.id_greens = False
        handler.id_model_blacklist = list(exclude_models)

        handler.salvage_whites = True
        handler.salvage_rare_materials = False
        handler.salvage_blues = True
        handler.salvage_purples = True
        handler.salvage_golds = True
        handler.salvage_dialog_auto_handle = True
        handler.salvage_dialog_auto_confirm_materials = True
        handler.salvage_dialog_debug = False
        handler.salvage_blacklist = list(salvage_exclude_models)

        if _has_identify_candidates(exclude_models):
            LogMessage("Identifying salvage candidates").root.tick()
            yield from handler.IdentifyItems(log=False)

        if _has_warrior_weapon_recipe_ready():
            return

        if _has_salvage_candidates(salvage_exclude_models):
            LogMessage("Salvaging trash for warrior weapon materials").root.tick()
            yield from handler.SalvageItems(log=False)

        if not _has_warrior_weapon_recipe_ready():
            LogMessage(
                "Warrior salvage prep ended without enough materials yet "
                f"(wood={GLOBAL_CACHE.Inventory.GetModelCount(WOOD_PLANKS_MODEL_ID)}/1 "
                f"iron={GLOBAL_CACHE.Inventory.GetModelCount(IRON_INGOT_MODEL_ID)}/4 "
                f"gold={int(GLOBAL_CACHE.Inventory.GetGoldOnCharacter() or 0)}/{WARRIOR_AXE_TOTAL_GOLD_REQUIRED})"
            ).root.tick()

    def _step(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        generator = state.get("generator")
        if generator is None:
            generator = _generator()
            state["generator"] = generator

        try:
            next(generator)
            return BehaviorTree.NodeState.RUNNING
        except StopIteration:
            state["generator"] = None
            return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="RunWarriorSalvagePrep",
            action_fn=_step,
            aftercast_ms=0,
        )
    )


def WarriorMerchantPrepAndCleanup(
    merchant_coords: Vec2f,
    exclude_models: list[int] | None = None,
    target_distance: float = Range.Area.value,
) -> BehaviorTree:
    merchant_frame_hash = 3613855137
    warrior_exclude_models = _merge_model_lists(
        list(exclude_models or []),
        [WOOD_PLANKS_MODEL_ID, IRON_INGOT_MODEL_ID, SERRATED_SHIELD_MODEL_ID],
    )

    def _needs_warrior_merchant_visit() -> bool:
        return _needs_warrior_inventory_cleanup(warrior_exclude_models) or (
            _needs_warrior_gold_only() and bool(_collect_sellable_item_ids_for_models([DULL_CARAPACES_MODEL_ID]))
        )

    def _is_merchant_window_open() -> bool:
        from Py4GWCoreLib.UIManager import UIManager

        merchant_frame_id = UIManager.GetFrameIDByHash(merchant_frame_hash)
        return merchant_frame_id != 0 and UIManager.FrameExists(merchant_frame_id)

    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="WarriorMerchantPrepAndCleanup",
            children=[
                BehaviorTree.SequenceNode(
                    name="WarriorCleanupRequired",
                    children=[
                        BehaviorTree.ConditionNode(
                            name="NeedsWarriorMerchantVisit",
                            condition_fn=_needs_warrior_merchant_visit,
                        ),
                        LogMessage("Warrior inventory cleanup needed, visiting merchant"),
                        BT.MoveAndInteract(merchant_coords, target_distance=target_distance),
                        BehaviorTree.ConditionNode(
                            name="MerchantWindowOpen",
                            condition_fn=_is_merchant_window_open,
                        ),
                        DebugWarriorMaterialState(),
                        DebugWarriorPrepState(warrior_exclude_models),
                        BehaviorTree.SelectorNode(
                            name="WarriorMaterialsReadyOrPrep",
                            children=[
                                BehaviorTree.SequenceNode(
                                    name="WarriorMaterialsAlreadyReady",
                                    children=[
                                        BehaviorTree.ConditionNode(
                                            name="HasWarriorWeaponMaterials",
                                            condition_fn=_has_warrior_weapon_recipe_ready,
                                        ),
                                        LogMessage("Warrior weapon recipe is ready"),
                                    ],
                                ),
                                BehaviorTree.SequenceNode(
                                    name="SellForWarriorRecipeGold",
                                    children=[
                                        BehaviorTree.ConditionNode(
                                            name="NeedsWarriorGoldOnly",
                                            condition_fn=_needs_warrior_gold_only,
                                        ),
                                        DebugWarriorPrepState(warrior_exclude_models),
                                        LogMessage(
                                            f"Warrior materials are ready, selling trash to reach "
                                            f"{WARRIOR_AXE_TOTAL_GOLD_REQUIRED} gold"
                                        ),
                                        SellSpecificInventoryModels([DULL_CARAPACES_MODEL_ID]),
                                    ],
                                ),
                                BehaviorTree.SequenceNode(
                                    name="SellForMissingWarriorPrepKits",
                                    children=[
                                        BehaviorTree.ConditionNode(
                                            name="MissingWarriorPrepKits",
                                            condition_fn=lambda: not _has_warrior_prep_kits(),
                                        ),
                                        BehaviorTree.ConditionNode(
                                            name="CannotAffordMissingWarriorPrepKits",
                                            condition_fn=lambda: not _can_afford_missing_warrior_prep_kits(),
                                        ),
                                        DebugWarriorPrepState(warrior_exclude_models),
                                        LogMessage("Selling trash until warrior salvage and ID kits can be bought"),
                                        BT.SellInventoryItems(exclude_models=warrior_exclude_models, log=False),
                                    ],
                                ),
                                BehaviorTree.SequenceNode(
                                    name="EnsureWarriorKitsAndPrepareMaterials",
                                    children=[
                                        BehaviorTree.SelectorNode(
                                            name="EnsureWarriorSalvageKit",
                                            children=[
                                                BehaviorTree.ConditionNode(
                                                    name="HasWarriorSalvageKit",
                                                    condition_fn=_has_salvage_kit,
                                                ),
                                                TryEnsureMerchantItem(SALVAGE_KIT_MODEL_ID, "Salvage Kit"),
                                            ],
                                        ),
                                        BehaviorTree.SelectorNode(
                                            name="EnsureWarriorSalvageKitUses",
                                            children=[
                                                BehaviorTree.ConditionNode(
                                                    name="HasEnoughWarriorSalvageUses",
                                                    condition_fn=lambda: _has_enough_salvage_uses_for_inventory(warrior_exclude_models),
                                                ),
                                                TryTopUpMerchantItemUses(
                                                    SALVAGE_KIT_MODEL_ID,
                                                    "Salvage Kit",
                                                    required_uses_fn=lambda: _count_salvage_uses_required(warrior_exclude_models),
                                                    available_uses_fn=_count_available_salvage_uses,
                                                    fallback_cost=40,
                                                ),
                                            ],
                                        ),
                                        BehaviorTree.SelectorNode(
                                            name="EnsureWarriorIDKit",
                                            children=[
                                                BehaviorTree.ConditionNode(
                                                    name="HasWarriorIDKit",
                                                    condition_fn=_has_id_kit,
                                                ),
                                                TryEnsureMerchantItem(ID_KIT_MODEL_ID, "Identification Kit"),
                                            ],
                                        ),
                                        BehaviorTree.SelectorNode(
                                            name="EnsureWarriorIDKitUses",
                                            children=[
                                                BehaviorTree.ConditionNode(
                                                    name="HasEnoughWarriorIDUses",
                                                    condition_fn=lambda: _has_enough_id_uses_for_inventory(warrior_exclude_models),
                                                ),
                                                TryTopUpMerchantItemUses(
                                                    ID_KIT_MODEL_ID,
                                                    "Identification Kit",
                                                    required_uses_fn=lambda: _count_identify_uses_required(warrior_exclude_models),
                                                    available_uses_fn=_count_available_id_uses,
                                                    fallback_cost=100,
                                                ),
                                            ],
                                        ),
                                        DebugWarriorPrepState(warrior_exclude_models),
                                        RunWarriorSalvagePrep(warrior_exclude_models),
                                        DebugWarriorMaterialState(),
                                    ],
                                ),
                            ],
                        ),
                        BT.SellInventoryItems(exclude_models=warrior_exclude_models, log=False),
                        BT.DestroyZeroValueItems(exclude_models=warrior_exclude_models, log=False),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="NoWarriorCleanupRequired",
                    children=[
                        BehaviorTree.ConditionNode(
                            name="NoWarriorInventoryCleanupNeeded",
                            condition_fn=lambda: not _needs_warrior_merchant_visit(),
                        ),
                        LogMessage("No warrior merchant cleanup needed"),
                    ],
                ),
            ],
        )
    )


def TryAcquireBonusShield() -> BehaviorTree:
    destroy_exclude_list = [IGNEOUS_SUMMONING_STONE_MODEL_ID, SERRATED_SHIELD_MODEL_ID]

    def _build_runtime_buy_starter_shield(node: BehaviorTree.Node) -> BehaviorTree:
        merchant_coords = get_merchant_coords_from_map_id()
        if merchant_coords is None:
            return BehaviorTree(
                BehaviorTree.FailerNode(
                    name="MissingMerchantForStarterShield",
                )
            )

        merchant_frame_hash = 3613855137

        def _is_merchant_window_open() -> bool:
            from Py4GWCoreLib.UIManager import UIManager

            merchant_frame_id = UIManager.GetFrameIDByHash(merchant_frame_hash)
            return merchant_frame_id != 0 and UIManager.FrameExists(merchant_frame_id)

        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="BuyAndEquipStarterShield",
                children=[
                    LogMessage("Serrated Shield unavailable, visiting merchant for Starter Shield"),
                    BT.MoveAndInteract(merchant_coords, target_distance=Range.Area.value),
                    BehaviorTree.ConditionNode(
                        name="MerchantWindowOpenForStarterShield",
                        condition_fn=_is_merchant_window_open,
                    ),
                    TryEnsureMerchantItem(STARTER_SHIELD_MODEL_ID, "Starter Shield"),
                    EnsureOwnedItemEquipped(STARTER_SHIELD_MODEL_ID, "Starter Shield"),
                ],
            )
        )

    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="TryAcquireBonusShield",
            children=[
                BehaviorTree.SequenceNode(
                    name="SerratedShieldAlreadyEquipped",
                    children=[
                        BT.IsItemEquipped(SERRATED_SHIELD_MODEL_ID),
                        LogMessage("Serrated Shield is already equipped"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="EquipSerratedShieldFromInventory",
                    children=[
                        BT.IsItemInInventoryBags(SERRATED_SHIELD_MODEL_ID),
                        LogMessage("Serrated Shield found in inventory, equipping it"),
                        BT.EquipItemByModelID(SERRATED_SHIELD_MODEL_ID),
                        BT.IsItemEquipped(SERRATED_SHIELD_MODEL_ID),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="SpawnAndEquipSerratedShield",
                    children=[
                        LogMessage("Spawning bonus items and checking for Serrated Shield"),
                        BT.SpawnBonusItems(),
                        LogMessage("Deleting spawned bonus items except Igneous Summoning Stone and Serrated Shield"),
                        BT.DestroyBonusItems(exclude_list=destroy_exclude_list),
                        BT.IsItemInInventoryBags(SERRATED_SHIELD_MODEL_ID),
                        LogMessage("Serrated Shield spawned into inventory, equipping it"),
                        BT.EquipItemByModelID(SERRATED_SHIELD_MODEL_ID),
                        BT.IsItemEquipped(SERRATED_SHIELD_MODEL_ID),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="StarterShieldAlreadyEquipped",
                    children=[
                        BT.IsItemEquipped(STARTER_SHIELD_MODEL_ID),
                        LogMessage("Starter Shield is already equipped"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="EquipStarterShieldFromInventory",
                    children=[
                        BT.IsItemInInventoryBags(STARTER_SHIELD_MODEL_ID),
                        LogMessage("Starter Shield found in inventory, equipping it"),
                        BT.EquipItemByModelID(STARTER_SHIELD_MODEL_ID),
                        BT.IsItemEquipped(STARTER_SHIELD_MODEL_ID),
                    ],
                ),
                BehaviorTree.SubtreeNode(
                    name="RuntimeBuyStarterShield",
                    subtree_fn=_build_runtime_buy_starter_shield,
                ),
                BehaviorTree.SucceederNode(
                    name="SkipMissingSerratedShield",
                ),
            ],
        )
    )


def EnsureWarriorShieldEquipped() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="EnsureWarriorShieldEquipped",
            children=[
                BehaviorTree.SelectorNode(
                    name="BestEffortAcquireWarriorShield",
                    children=[
                        TryAcquireBonusShield().root,
                        BehaviorTree.SucceederNode(
                            name="ContinueToStrictShieldEquip",
                        ),
                    ],
                ),
                BehaviorTree.SelectorNode(
                    name="EnsurePreferredWarriorShieldEquipped",
                    children=[
                        EnsureOwnedItemEquipped(SERRATED_SHIELD_MODEL_ID, "Serrated Shield").root,
                        EnsureOwnedItemEquipped(STARTER_SHIELD_MODEL_ID, "Starter Shield").root,
                    ],
                ),
            ],
        )
    )


def TryAcquireNevermoreFlatbow() -> BehaviorTree:
    destroy_exclude_list = [IGNEOUS_SUMMONING_STONE_MODEL_ID, NEVERMORE_FLATBOW_MODEL_ID]
    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="TryAcquireNevermoreFlatbow",
            children=[
                BehaviorTree.SequenceNode(
                    name="NevermoreFlatbowAlreadyEquipped",
                    children=[
                        BT.IsItemEquipped(NEVERMORE_FLATBOW_MODEL_ID),
                        LogMessage("Nevermore Flatbow is already equipped"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="EquipNevermoreFlatbowFromInventory",
                    children=[
                        BT.IsItemInInventoryBags(NEVERMORE_FLATBOW_MODEL_ID),
                        LogMessage("Nevermore Flatbow found in inventory, equipping it"),
                        BT.EquipItemByModelID(NEVERMORE_FLATBOW_MODEL_ID),
                        BT.IsItemEquipped(NEVERMORE_FLATBOW_MODEL_ID),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="SpawnAndEquipNevermoreFlatbow",
                    children=[
                        LogMessage("Spawning bonus items and checking for Nevermore Flatbow"),
                        BT.SpawnBonusItems(),
                        LogMessage("Deleting spawned bonus items except Igneous Summoning Stone and Nevermore Flatbow"),
                        BT.DestroyBonusItems(exclude_list=destroy_exclude_list),
                        BT.IsItemInInventoryBags(NEVERMORE_FLATBOW_MODEL_ID),
                        LogMessage("Nevermore Flatbow spawned into inventory, equipping it"),
                        BT.EquipItemByModelID(NEVERMORE_FLATBOW_MODEL_ID),
                        BT.IsItemEquipped(NEVERMORE_FLATBOW_MODEL_ID),
                    ],
                ),
            ],
        )
    )


def TryAcquireTigersRoar() -> BehaviorTree:
    destroy_exclude_list = [IGNEOUS_SUMMONING_STONE_MODEL_ID, TIGERS_ROAR_MODEL_ID]
    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="TryAcquireTigersRoar",
            children=[
                BehaviorTree.SequenceNode(
                    name="TigersRoarAlreadyOwned",
                    children=[
                        DebugItemState(TIGERS_ROAR_MODEL_ID, "Tiger's Roar ownership check"),
                        BehaviorTree.ConditionNode(
                            name="HasTigersRoarInBagsOrEquipped",
                            condition_fn=lambda: _has_model_in_inventory_or_equipped(TIGERS_ROAR_MODEL_ID),
                        ),
                        LogMessage("Tiger's Roar is already owned"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="SpawnAndKeepTigersRoar",
                    children=[
                        LogMessage("Spawning bonus items and checking for Tiger's Roar"),
                        BT.SpawnBonusItems(),
                        LogMessage("Deleting spawned bonus items except Igneous Summoning Stone and Tiger's Roar"),
                        BT.DestroyBonusItems(exclude_list=destroy_exclude_list),
                        DebugItemState(TIGERS_ROAR_MODEL_ID, "Tiger's Roar after bonus spawn"),
                        BehaviorTree.ConditionNode(
                            name="HasTigersRoarAfterSpawn",
                            condition_fn=lambda: _has_model_in_inventory_or_equipped(TIGERS_ROAR_MODEL_ID),
                        ),
                        LogMessage("Tiger's Roar is available for the elementalist weapon path"),
                    ],
                ),
            ],
        )
    )


def EnsureNevermoreFlatbowEquipped() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="EnsureNevermoreFlatbowEquipped",
            children=[
                BehaviorTree.SelectorNode(
                    name="BestEffortAcquireNevermoreFlatbow",
                    children=[
                        TryAcquireNevermoreFlatbow().root,
                        BehaviorTree.SucceederNode(
                            name="ContinueToStrictNevermoreEquip",
                        ),
                    ],
                ),
                EnsureOwnedItemEquipped(NEVERMORE_FLATBOW_MODEL_ID, "Nevermore Flatbow"),
            ],
        )
    )


def _get_weapon_acquisition_profile() -> str:
    primary, _secondary = Agent.GetProfessionNames(Player.GetAgentID())
    if primary == "Warrior":
        return "warrior"
    if primary == "Elementalist":
        return "elementalist"
    return "default"


def FarmBow(exclude_models: list[int] | None = None) -> BehaviorTree:
    LAKESIDE_COUNTY_EXIT_COORDS_001: Vec2f = Vec2f(-12508.46, -6135.42)
    LAKESIDE_COUNTY_EXIT_COORDS_002: Vec2f = Vec2f(-10905, -6287)

    REGENT_VALLEY_MID_001_EXIT_COORDS: Vec2f = Vec2f(-6316.87, -6808.10)
    REGENT_VALLEY_MID_002_EXIT_COORDS: Vec2f = Vec2f(-4833.97, -12199.93)
    REGENT_VALLEY_OVER_BRIDGE_EXIT_COORDS: list[Vec2f] = [Vec2f(-3464.73, -13135.62)]
    REGENT_VALLEY_EXIT_COORDS: Vec2f = Vec2f(6516, -19822)

    KILLSPOT_COORDS: Vec2f = Vec2f(-15440.87, 10063.57)
    ROWNAN_COORDS: Vec2f = Vec2f(-17002.54, 10695.05)

    def _build_runtime_merchant_cleanup(node: BehaviorTree.Node) -> BehaviorTree:
        merchant_coords = get_merchant_coords_from_map_id()
        if merchant_coords is None:
            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="NoMerchantCleanup",
                    action_fn=lambda runtime_node: BehaviorTree.NodeState.SUCCESS,
                )
            )

        return MoveInteractAndSellItems(
            merchant_coords=merchant_coords,
            exclude_models=exclude_models,
            destroy_zero_value_items=True,
            log=False,
        )

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Farm Bow",
            children=[
                LogMessage("Traveling to Ashford Abbey to Farm for Ascalon Hornbow"),
                BT.TravelToOutpost(ASHFORD_ABBEY_MAP_ID),
                BehaviorTree.SubtreeNode(
                    name="RuntimeMerchantCleanup",
                    subtree_fn=_build_runtime_merchant_cleanup,
                ),
                LogMessage("Exiting to Lakeside County"),
                BT.Move(LAKESIDE_COUNTY_EXIT_COORDS_001),
                BT.Move(LAKESIDE_COUNTY_EXIT_COORDS_002),
                BT.WaitForMapLoad(LAKESIDE_COUNTY_MAP_ID),
                LogMessage("Exiting to Regent Valley"),
                BT.Move(REGENT_VALLEY_MID_001_EXIT_COORDS),
                BT.Move(REGENT_VALLEY_MID_002_EXIT_COORDS),
                BT.MoveDirect(REGENT_VALLEY_OVER_BRIDGE_EXIT_COORDS),
                BT.Move(REGENT_VALLEY_EXIT_COORDS),
                BT.WaitForMapLoad(REGENT_VALLEY_MAP_ID),
                LogMessage("Farming in Regent Valley for Ascalon Hornbow"),
                BT.Move(KILLSPOT_COORDS),
                LogMessage("Clearing enemies around killspot"),
                BT.ClearEnemiesInArea(pos=KILLSPOT_COORDS, radius=Range.Earshot.value),
                LogMessage("Moving to Melandru Statue to kill more enemies"),
                BT.Move(Vec2f(-17670.05, 8973.73)),
                BT.Move(MELANDRU_STATUE_COORDS),
                LogMessage("Returning to Rownan"),
                BT.Move(ROWNAN_COORDS),
                LogMessage("Interacting with Rownan"),
                BT.MoveAndInteract(ROWNAN_COORDS, target_distance=Range.Area.value),
            ],
        )
    )


def FarmWarriorMaterials(exclude_models: list[int] | None = None) -> BehaviorTree:
    warrior_exclude_models = _merge_model_lists(
        list(exclude_models or []),
        [WOOD_PLANKS_MODEL_ID, IRON_INGOT_MODEL_ID, SERRATED_SHIELD_MODEL_ID],
    )

    LAKESIDE_COUNTY_EXIT_COORDS_001: Vec2f = Vec2f(-12508.46, -6135.42)
    LAKESIDE_COUNTY_EXIT_COORDS_002: Vec2f = Vec2f(-10905, -6287)

    REGENT_VALLEY_MID_001_EXIT_COORDS: Vec2f = Vec2f(-6316.87, -6808.10)
    REGENT_VALLEY_MID_002_EXIT_COORDS: Vec2f = Vec2f(-4833.97, -12199.93)
    REGENT_VALLEY_OVER_BRIDGE_EXIT_COORDS: list[Vec2f] = [Vec2f(-3464.73, -13135.62)]
    REGENT_VALLEY_EXIT_COORDS: Vec2f = Vec2f(6516, -19822)

    KILLSPOT_COORDS: Vec2f = Vec2f(-14696.82, 10211.46)
    ROWNAN_COORDS: Vec2f = Vec2f(-17002.54, 10695.05)

    def _build_runtime_warrior_cleanup(node: BehaviorTree.Node) -> BehaviorTree:
        merchant_coords = get_merchant_coords_from_map_id()
        if merchant_coords is None:
            return BehaviorTree(
                BehaviorTree.SucceederNode(
                    name="SkipWarriorMerchantCleanup",
                )
            )
        return WarriorMerchantPrepAndCleanup(
            merchant_coords=merchant_coords,
            exclude_models=warrior_exclude_models,
        )

    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="Farm Warrior Materials",
            children=[
                BehaviorTree.SequenceNode(
                    name="MaterialsReadyAfterMerchantPrep",
                    children=[
                        LogMessage("Traveling to Ashford Abbey to farm warrior weapon materials"),
                        BT.TravelToOutpost(ASHFORD_ABBEY_MAP_ID),
                        BehaviorTree.SubtreeNode(
                            name="RuntimeWarriorMerchantCleanup",
                            subtree_fn=_build_runtime_warrior_cleanup,
                        ),
                        DebugWarriorMaterialState(),
                        BehaviorTree.ConditionNode(
                            name="HasWarriorWeaponMaterialsAfterMerchantCleanup",
                            condition_fn=_has_warrior_weapon_recipe_ready,
                        ),
                        LogMessage("Warrior weapon recipe ready after merchant prep"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="FarmWarriorMaterialsInRegentValley",
                    children=[
                        LogMessage("Traveling to Ashford Abbey to farm warrior weapon materials"),
                        BT.TravelToOutpost(ASHFORD_ABBEY_MAP_ID),
                        BehaviorTree.SubtreeNode(
                            name="RuntimeWarriorMerchantCleanup",
                            subtree_fn=_build_runtime_warrior_cleanup,
                        ),
                        LogMessage("Exiting to Lakeside County"),
                        BT.Move(LAKESIDE_COUNTY_EXIT_COORDS_001),
                        BT.Move(LAKESIDE_COUNTY_EXIT_COORDS_002),
                        BT.WaitForMapLoad(LAKESIDE_COUNTY_MAP_ID),
                        LogMessage("Exiting to Regent Valley"),
                        BT.Move(REGENT_VALLEY_MID_001_EXIT_COORDS),
                        BT.Move(REGENT_VALLEY_MID_002_EXIT_COORDS),
                        BT.MoveDirect(REGENT_VALLEY_OVER_BRIDGE_EXIT_COORDS),
                        BT.Move(REGENT_VALLEY_EXIT_COORDS),
                        BT.WaitForMapLoad(REGENT_VALLEY_MAP_ID),
                        LogMessage("Farming in Regent Valley for warrior weapon materials"),
                        BT.Move(KILLSPOT_COORDS),
                        BT.ClearEnemiesInArea(pos=KILLSPOT_COORDS, radius=CLEAR_ENEMIES_AREA_RADIUS),
                        BT.Move(Vec2f(-17670.05, 8973.73)),
                        BT.Move(MELANDRU_STATUE_COORDS),
                        BT.Move(ROWNAN_COORDS),
                        BT.MoveAndInteract(ROWNAN_COORDS, target_distance=Range.Area.value),
                    ],
                ),
            ],
        )
    )


def FarmWarriorWeaponMaterialsUntilReady(exclude_models: list[int] | None = None) -> BehaviorTree:
    warrior_exclude_models = _merge_model_lists(
        list(exclude_models or []),
        [WOOD_PLANKS_MODEL_ID, IRON_INGOT_MODEL_ID, SERRATED_SHIELD_MODEL_ID],
    )
    return BehaviorTree(
        BehaviorTree.RepeaterUntilSuccessNode(
            name="FarmWarriorWeaponMaterialsUntilReady",
            child=BehaviorTree.SequenceNode(
                name="WarriorMaterialLoop",
                children=[
                    BehaviorTree.SelectorNode(
                        name="WarriorMaterialsReadyOrFarm",
                        children=[
                            BehaviorTree.SequenceNode(
                                name="WarriorMaterialsReady",
                                children=[
                                    DebugWarriorMaterialState(),
                                    BehaviorTree.ConditionNode(
                                        name="HasWarriorWeaponMaterials",
                                        condition_fn=_has_warrior_weapon_recipe_ready,
                                    ),
                                    LogMessage("Warrior weapon recipe is ready"),
                                ],
                            ),
                            FarmWarriorMaterials(exclude_models=warrior_exclude_models),
                        ],
                    ),
                    DebugWarriorMaterialState(),
                    BehaviorTree.ConditionNode(
                        name="HasWarriorWeaponMaterialsAfterFarmLoop",
                        condition_fn=_has_warrior_weapon_recipe_ready,
                    ),
                ],
            ),
        )
    )


def AcquireWarriorCollectorAxe() -> BehaviorTree:
    def _send_exact_crafter_request(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        offered_item_id = 0
        for candidate in GLOBAL_CACHE.Trading.Crafter.GetOfferedItems():
            if GLOBAL_CACHE.Item.GetModelID(candidate) == KYHLO_AXE_OF_FORTITUDE_MODEL_ID:
                offered_item_id = candidate
                break

        if offered_item_id == 0:
            LogMessage("Khila Axe of Fortitude is not present in Arthur Ayala's crafter offers").root.tick()
            return BehaviorTree.NodeState.FAILURE

        trade_payload = _resolve_trade_item_ids(
            [IRON_INGOT_MODEL_ID, WOOD_PLANKS_MODEL_ID],
            [4, 1],
        )
        if trade_payload is None:
            LogMessage("Could not resolve bag item ids for 4 Iron Ingots and 1 Wood Plank").root.tick()
            return BehaviorTree.NodeState.FAILURE

        trade_item_ids, trade_item_quantities = trade_payload
        GLOBAL_CACHE.Trading.Crafter.CraftItem(
            offered_item_id,
            100,
            trade_item_ids,
            trade_item_quantities,
        )
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="AcquireWarriorCollectorAxe",
            children=[
                BehaviorTree.SequenceNode(
                    name="KhilaAxeAlreadyEquipped",
                    children=[
                        BT.IsItemEquipped(KYHLO_AXE_OF_FORTITUDE_MODEL_ID),
                        LogMessage("Khila Axe of Fortitude is already equipped"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="TravelExchangeAndEquipKhilaAxe",
                    children=[
                        LogMessage("Traveling to Ascalon City for Arthur Ayala"),
                        BT.TravelToOutpost(ASCALON_CITY_MAP_ID),
                        LogMessage("Moving to Arthur Ayala"),
                        BT.MoveAndInteract(ARTHUR_AYALA_COORDS, target_distance=Range.Area.value),
                        LogMessage("Crafting Khila Axe of Fortitude with 4 Iron Ingots, 1 Wood Plank, and 100 gold"),
                        BehaviorTree.ActionNode(
                            name="CraftKhilaAxeExactCrafterRequest",
                            action_fn=_send_exact_crafter_request,
                            aftercast_ms=250,
                        ),
                        BT.Wait(500),
                        LogMessage("Equipping Khila Axe of Fortitude"),
                        BT.EquipItemByModelID(KYHLO_AXE_OF_FORTITUDE_MODEL_ID),
                        BT.Wait(500),
                        BT.IsItemEquipped(KYHLO_AXE_OF_FORTITUDE_MODEL_ID),
                        LogMessage("Moving to Elias to customize Khila Axe of Fortitude"),
                        BT.MoveAndInteract(ELIAS_COORDS, target_distance=Range.Area.value),
                        LogMessage("Customizing Khila Axe of Fortitude"),
                        BT.CustomizeWeapon(),
                    ],
                ),
            ],
        )
    )


def FarmBowUntilFlatbowEquipped(
    exclude_models: list[int] | None = None,
    target_item_model_id: int = ASCALON_HORNBOW_MODEL_ID,
    allow_nevermore_flatbow_success: bool = True,
) -> BehaviorTree:
    selector_children: list[BehaviorTree | BehaviorTree.Node] = []
    if allow_nevermore_flatbow_success:
        selector_children.append(BT.IsItemEquipped(NEVERMORE_FLATBOW_MODEL_ID))
    selector_children.append(BT.IsItemEquipped(target_item_model_id))
    selector_children.append(
        BehaviorTree.SequenceNode(
            name="Sell Trash And Farm Bow",
            children=[
                FarmBow(exclude_models=exclude_models),
                LogMessage(F"Exchanging 3 Dull Carapaces for {target_item_model_id}"),
                BT.ExchangeCollectorItem(
                    output_model_id=target_item_model_id,
                    trade_model_ids=[DULL_CARAPACES_MODEL_ID],
                    quantity_list=[3],
                ),
                LogMessage(F"Equipping {target_item_model_id}"),
                BT.EquipItemByModelID(target_item_model_id),
                LogMessage("Traveling to Ashford Abbey, routine finished"),
                BT.TravelToOutpost(ASHFORD_ABBEY_MAP_ID),
                BT.IsItemEquipped(target_item_model_id),
            ],
        )
    )

    return BehaviorTree(
        BehaviorTree.RepeaterUntilSuccessNode(
            name="Farm Until Flatbow Equipped",
            child=BehaviorTree.SelectorNode(
                name="Farm Bow Loop",
                children=selector_children,
            ),
        )
    )


def _build_warrior_weapon_tree() -> BehaviorTree:
    warrior_exclude_models = _merge_model_lists(
        ITEMS_BLACKLIST,
        [WOOD_PLANKS_MODEL_ID, IRON_INGOT_MODEL_ID, SERRATED_SHIELD_MODEL_ID],
    )
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="AcquireWeaponWarrior",
            children=[
                EnsureWarriorShieldEquipped(),
                EnsureNevermoreFlatbowEquipped(),
                FarmWarriorWeaponMaterialsUntilReady(
                    exclude_models=warrior_exclude_models,
                ),
                AcquireWarriorCollectorAxe(),
            ],
        )
    )


def _build_elementalist_weapon_tree() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="AcquireWeaponElementalist",
            children=[
                BehaviorTree.SequenceNode(
                    name="EarthWandAlreadyEquipped",
                    children=[
                        IsItemEquippedStrict(EARTH_WAND_MODEL_ID, "Earth Wand"),
                        LogMessage("Earth Wand is already equipped"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="AcquireEarthWandViaTigersRoarAndNevermore",
                    children=[
                        TryAcquireTigersRoar(),
                        EnsureOwnedItemEquipped(TIGERS_ROAR_MODEL_ID, "Tiger's Roar"),
                        EnsureNevermoreFlatbowEquipped(),
                        BehaviorTree.ConditionNode(
                            name="HasTigersRoarForElementalistPath",
                            condition_fn=lambda: _is_model_equipped_strict(TIGERS_ROAR_MODEL_ID),
                        ),
                        LogMessage("Tiger's Roar is present and Nevermore Flatbow is equipped, farming for Earth Wand"),
                        FarmBowUntilFlatbowEquipped(
                            exclude_models=ITEMS_BLACKLIST,
                            target_item_model_id=EARTH_WAND_MODEL_ID,
                            allow_nevermore_flatbow_success=False,
                        ),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="FarmCollectorBowWithoutElementalistSpecialItems",
                    children=[
                        LogMessage("Tiger's Roar or Nevermore Flatbow unavailable, farming collector bow"),
                        EquipStarterBow(),
                        FarmBowUntilFlatbowEquipped(
                            exclude_models=ITEMS_BLACKLIST,
                            target_item_model_id=ASCALON_HORNBOW_MODEL_ID,
                            allow_nevermore_flatbow_success=False,
                        ),
                    ],
                ),
            ],
        )
    )


def _build_default_weapon_tree() -> BehaviorTree:
    def _build_runtime_farm_weapon(node: BehaviorTree.Node) -> BehaviorTree:
        return BehaviorTree(
            BehaviorTree.SelectorNode(
                name="FarmCollectorBow",
                children=[
                    BT.IsItemEquipped(ASCALON_HORNBOW_MODEL_ID),
                    BehaviorTree.SequenceNode(
                        name="EquipStarterBowAndFarmCollectorBow",
                        children=[
                            LogMessage("Farming collector bow"),
                            EquipStarterBow(),
                            FarmBowUntilFlatbowEquipped(
                                exclude_models=ITEMS_BLACKLIST,
                                target_item_model_id=ASCALON_HORNBOW_MODEL_ID,
                            ),
                        ],
                    ),
                ],
            )
        )

    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="Acquire Weapon",
            children=[
                BehaviorTree.SequenceNode(
                    name="NevermoreFlatbowAlreadyEquipped",
                    children=[
                        BT.IsItemEquipped(NEVERMORE_FLATBOW_MODEL_ID),
                        LogMessage("Nevermore Flatbow is already equipped"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="EnsureNevermoreFlatbowEquipped",
                    children=[
                        EnsureNevermoreFlatbowEquipped(),
                        LogMessage("Nevermore Flatbow equipped from owned or bonus items"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="Farm For Weapon",
                    children=[
                        LogMessage("Nevermore Flatbow is unavailable, farming collector bow instead"),
                        BehaviorTree.SubtreeNode(
                            name="RuntimeFarmWeaponBranch",
                            subtree_fn=_build_runtime_farm_weapon,
                        ),
                    ],
                ),
            ],
        )
    )


def AcquireWeapon() -> BehaviorTree:
    profile = _get_weapon_acquisition_profile()
    if profile == "warrior":
        return _build_warrior_weapon_tree()
    if profile == "elementalist":
        return _build_elementalist_weapon_tree()
    return _build_default_weapon_tree()
