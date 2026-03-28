from __future__ import annotations

import time
from enum import IntEnum
from typing import Any, Callable, Optional, cast

import Py4GW
import PyInventory
from PyItem import DyeColor

from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.Item import Bag, Item
from Py4GWCoreLib.Merchant import Trading
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.enums_src.Item_enums import MAX_STACK_SIZE, ItemType, Rarity
from Py4GWCoreLib.enums_src.Item_enums import MAX_STACK_SIZE
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.frenkeyLib.ItemHandling.Items.ItemCache import ITEM_CACHE
from Sources.frenkeyLib.ItemHandling.Items.item_snapshot import ItemSnapshot
from Sources.frenkeyLib.ItemHandling.Items.types import INVENTORY_BAGS, STORAGE_BAGS
from Sources.frenkeyLib.ItemHandling.Rules.types import MATERIAL_SLOTS, SalvageMode
from Sources.frenkeyLib.ItemHandling.UIManagerExtensions import UIManagerExtensions
from Sources.frenkeyLib.ItemHandling.utility import GetDestinationSlots, GetItemsLocations, HasSpaceForItem

SALVAGE_WINDOW_HASH = 684387150
LESSER_CONFIRM_HASH = 140452905

class BTNodes:
    NodeState = BehaviorTree.NodeState

    @staticmethod
    def _success_if(condition: bool) -> BehaviorTree.NodeState:
        return BehaviorTree.NodeState.SUCCESS if condition else BehaviorTree.NodeState.FAILURE

    class Merchant:
        @staticmethod 
        def Restock(
            model_id: int,
            item_type: ItemType,
            quantity: int,
        ):
            def _restock(node: BehaviorTree.Node):
                if not UIManagerExtensions.IsMerchantWindowOpen():
                    return BehaviorTree.NodeState.FAILURE
                
                inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(Bag.Backpack, Bag.Bag_2)
                current_qty = sum(i.quantity for bag in inventory_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.model_id == model_id and i.item_type == item_type) if inventory_snapshot else 0
                
                if current_qty >= quantity:
                    return BehaviorTree.NodeState.SUCCESS
                
                offered_items = Trading.Merchant.GetOfferedItems()
                item_id = next((iid for iid in offered_items if Item.GetModelID(iid) == model_id and Item.GetItemType(iid)[0] == item_type), None)
                
                if not item_id:
                    return BehaviorTree.NodeState.FAILURE

                available_gold = Inventory.GetGoldOnCharacter()
                quantity_to_buy = quantity - current_qty
            
                price = (Item.Properties.GetValue(item_id) * 2)
                affordable_qty = available_gold // price if price > 0 else quantity_to_buy
                has_space, space_for_qty = HasSpaceForItem(item_id, Bag.Backpack, Bag.Bag_2, quantity=affordable_qty)
                count = min(quantity_to_buy, affordable_qty, space_for_qty)
                
                if not has_space or count <= 0:
                    return BehaviorTree.NodeState.FAILURE
                                    
                for _ in range(max(0, count)):
                    Trading.Merchant.BuyItem(item_id, price)

                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.ActionNode(name="Merchant.Restock", action_fn=_restock)
        
        @staticmethod
        def SellItems(
            item_ids: list[int],
            aftercast_ms: int = 150,
        ):
            def _sell(node: BehaviorTree.Node):
                if not UIManagerExtensions.IsMerchantWindowOpen():
                    return BehaviorTree.NodeState.FAILURE
                
                items = [ITEM_CACHE.get_item_snapshot(iid) for iid in item_ids]
                sold_any = False
                for item in items:
                    if item is None or not item.is_valid or not item.is_inventory_item:
                        continue
                    
                    Trading.Merchant.SellItem(item.id, Item.Properties.GetValue(item.id) * item.quantity)
                    sold_any = True

                return BTNodes._success_if(sold_any)

            return BehaviorTree.ActionNode(name="Merchant.SellItems", action_fn=_sell, aftercast_ms=aftercast_ms)

        @staticmethod
        def BuyItems(
            item_ids_quantities: list[tuple[int, int]],
            aftercast_ms: int = 150,
        ):
            def _buy(node: BehaviorTree.Node):
                if not UIManagerExtensions.IsMerchantWindowOpen():  
                    return BehaviorTree.NodeState.FAILURE
                
                offered_items = Trading.Merchant.GetOfferedItems()
                valid_item_ids_quantities = [(item_id, qty) for item_id, qty in item_ids_quantities if item_id in offered_items]
                
                if not valid_item_ids_quantities:
                    return BehaviorTree.NodeState.FAILURE

                bought_any = False
                available_gold = Inventory.GetGoldOnCharacter()
                
                for i, (offered_item_id, quantity) in enumerate(item_ids_quantities):
                    price =  (Item.Properties.GetValue(offered_item_id) * 2)
                    affordable_qty = available_gold // price if price > 0 else quantity
                    has_space, qty = HasSpaceForItem(offered_item_id, Bag.Backpack, Bag.Bag_2, quantity=affordable_qty)
                    count = min(quantity, affordable_qty, qty)
                    
                    if not has_space or count <= 0:
                        continue
                                        
                    for _ in range(max(0, count)):
                        Trading.Merchant.BuyItem(offered_item_id, price)
                        bought_any = True

                return BTNodes._success_if(bought_any)

            return BehaviorTree.ActionNode(name="Merchant.BuyItems", action_fn=_buy, aftercast_ms=aftercast_ms)

    class Trader:
        class TraderProgress:
            def __init__(self):                
                self.initial_qty = 0
                self.current_qty = 0
                self.desired_qty = 0
                
                self.quote_requested_at = 0.0
                self.traded_at = 0.0
                
                self.requested = False
                self.traded = False
                self.trade_confirmed = False
            
            def reset(self):        
                self.quote_requested_at = 0.0
                self.traded_at = 0.0
                
                self.requested = False
                self.traded = False
                self.trade_confirmed = False
        
        @staticmethod
        def BuyItem(
            item_id : int,
            quantity: int = 1,
            quote_timeout_ms: int = 500,
            aftercast_ms: int = 0,
        ):
            def _buy(node: BehaviorTree.Node):
                now = time.monotonic()
                
                if not UIManagerExtensions.IsMerchantWindowOpen():
                    return BehaviorTree.NodeState.FAILURE
                
                offered_items = Trading.Trader.GetOfferedItems()
                
                if item_id not in offered_items:
                    return BehaviorTree.NodeState.FAILURE
                
                item = ITEM_CACHE.get_item_snapshot(item_id)
                if not item or not item.is_valid:
                    return BehaviorTree.NodeState.FAILURE
                                 
                state = node.blackboard.get("trader_buy_progress")
                state = cast(BTNodes.Trader.TraderProgress, state) if state else None
                
                if state is None:
                    state = BTNodes.Trader.TraderProgress()
                    inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(Bag.Backpack, Bag.Bag_2)
                    state.initial_qty = sum(i.quantity for bag in inventory_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.same_kind_as(item)) if inventory_snapshot else 0
                    state.desired_qty = state.initial_qty + quantity
                    node.blackboard["trader_buy_progress"] = state
                
                if state.current_qty < state.desired_qty:
                    quote = Trading.Trader.GetQuotedValue()
                    quote_available = Trading.Trader.GetQuotedItemID() == item_id
                    
                    if not state.requested:
                        Trading.Trader.RequestQuote(item_id)
                        state.quote_requested_at = now
                        state.requested = True
                        return BehaviorTree.NodeState.RUNNING
                                        
                    if not state.traded:                        
                        if quote_available and quote > 0:
                            Trading.Trader.BuyItem(item_id, quote)
                            state.traded = True
                            state.traded_at = now
                            
                            return BehaviorTree.NodeState.RUNNING
                    
                    if not state.trade_confirmed:
                        inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(Bag.Backpack, Bag.Bag_2)
                        state.current_qty = sum(i.quantity for bag in inventory_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.same_kind_as(item)) if inventory_snapshot else 0
                        state.trade_confirmed = state.current_qty > state.initial_qty
                        
                        
                        if state.trade_confirmed:
                            state.initial_qty = state.current_qty
                            state.requested = False
                            state.traded = False
                            state.trade_confirmed = False
                            state.quote_requested_at = 0.0
                            state.traded_at = 0.0
                            return BehaviorTree.NodeState.RUNNING
                                        
                    if state.traded_at and (now - state.traded_at) * 1000 >= quote_timeout_ms:
                        state.traded = False
                        state.trade_confirmed = False
                        state.traded_at = 0.0
                        return BehaviorTree.NodeState.RUNNING
                    
                    if state.quote_requested_at and (now - state.quote_requested_at) * 1000 >= quote_timeout_ms:
                        state.requested = False
                        state.quote_requested_at = 0.0
                        return BehaviorTree.NodeState.RUNNING
                    
                    return BehaviorTree.NodeState.RUNNING
                
                else:
                    return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.ActionNode(name="Trader.BuyItems", action_fn=_buy, aftercast_ms=aftercast_ms)

        @staticmethod
        def SellItem(
            item_id : int,
            quantity: int = 1,
            quote_timeout_ms: int = 500,
            aftercast_ms: int = 0,
        ):
            def _sell(node: BehaviorTree.Node):
                now = time.monotonic()
                
                if not UIManagerExtensions.IsMerchantWindowOpen():
                    return BehaviorTree.NodeState.FAILURE
                                
                item = ITEM_CACHE.get_item_snapshot(item_id)
                
                if not item or not item.is_valid or not item.is_inventory_item:
                    return BehaviorTree.NodeState.SUCCESS
                                 
                state = node.blackboard.get("trader_sell_progress")
                state = cast(BTNodes.Trader.TraderProgress, state) if state else None
                
                if state is None:
                    state = BTNodes.Trader.TraderProgress()
                    inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(Bag.Backpack, Bag.Bag_2)
                    state.initial_qty = sum(i.quantity for bag in inventory_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.same_kind_as(item)) if inventory_snapshot else 0
                    state.current_qty = state.initial_qty
                    state.desired_qty = state.initial_qty - (quantity if not item.is_material or item.is_rare_material else quantity // 10 * 10)
                    node.blackboard["trader_sell_progress"] = state 
                
                if state.current_qty > state.desired_qty:
                    quote = Trading.Trader.GetQuotedValue()
                    quote_available = Trading.Trader.GetQuotedItemID() == item_id
                    
                    if not state.requested:
                        Trading.Trader.RequestSellQuote(item_id)
                        state.quote_requested_at = now
                        state.requested = True
                        return BehaviorTree.NodeState.RUNNING
                                        
                    if not state.traded:                        
                        if quote_available and quote > 0:
                            Trading.Trader.SellItem(item_id, quote)
                            state.traded = True
                            state.traded_at = now
                            
                            return BehaviorTree.NodeState.RUNNING
                    
                    if not state.trade_confirmed:
                        inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(Bag.Backpack, Bag.Bag_2)
                        state.current_qty = sum(i.quantity for bag in inventory_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.same_kind_as(item)) if inventory_snapshot else 0
                        state.trade_confirmed = state.current_qty < state.initial_qty
                        
                        if state.trade_confirmed:
                            state.initial_qty = state.current_qty
                            state.requested = False
                            state.traded = False
                            state.trade_confirmed = False
                            state.quote_requested_at = 0.0
                            state.traded_at = 0.0
                            return BehaviorTree.NodeState.RUNNING
                                        
                    if state.traded_at and (now - state.traded_at) * 1000 >= quote_timeout_ms:
                        state.traded = False
                        state.trade_confirmed = False
                        state.traded_at = 0.0
                        return BehaviorTree.NodeState.RUNNING
                    
                    if state.quote_requested_at and (now - state.quote_requested_at) * 1000 >= quote_timeout_ms:
                        state.requested = False
                        state.quote_requested_at = 0.0
                        return BehaviorTree.NodeState.RUNNING
                    
                    return BehaviorTree.NodeState.RUNNING
                
                else:
                    return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.ActionNode(name="Trader.SellItems", action_fn=_sell, aftercast_ms=aftercast_ms)

    class Items:
        @staticmethod
        def UseItems(
            item_ids: list[int],
            quantities: Optional[list[int]] = None,
            aftercast_ms: int = 150,
            succeed_if_any_used: bool = True,
        ):
            def _use(node: BehaviorTree.Node):
                if not item_ids:
                    return BehaviorTree.NodeState.FAILURE

                used_any = False
                items = [ITEM_CACHE.get_item_snapshot(iid) for iid in item_ids]
                
                for item in items:
                    if item is None or not item.is_valid or not item.is_inventory_item:
                        continue
                    
                    quantity = quantities[items.index(item)] if quantities and items.index(item) < len(quantities) else 1
                    for _ in range(max(0, quantity)):
                        Inventory.UseItem(item.id)
                        used_any = True

                return BehaviorTree.NodeState.SUCCESS if used_any else BehaviorTree.NodeState.FAILURE

            return BehaviorTree.ActionNode(name="Items.UseItems", action_fn=_use, aftercast_ms=aftercast_ms)
        
        @staticmethod
        def DropItems(
            item_ids: list[int],
            aftercast_ms: int = 150,
            succeed_if_any_dropped: bool = True,
        ):
            def _drop(node: BehaviorTree.Node):
                if not item_ids:
                    return BehaviorTree.NodeState.FAILURE

                dropped_any = False
                items = [ITEM_CACHE.get_item_snapshot(iid) for iid in item_ids]
                
                for item in items:
                    if item is None or not item.is_valid or not item.is_inventory_item:
                        continue
                    
                    Inventory.DropItem(item.id, item.quantity)
                    dropped_any = True

                return BehaviorTree.NodeState.SUCCESS if dropped_any else BehaviorTree.NodeState.FAILURE

            return BehaviorTree.ActionNode(name="Items.DropItems", action_fn=_drop, aftercast_ms=aftercast_ms)
        
        @staticmethod
        def IdentifyItems(
            item_ids: list[int] | None = None,
            fail_if_no_kit: bool = True,
            succeed_if_already_identified: bool = True,
            aftercast_ms: int = 150,
        ):
            def _identify(node: BehaviorTree.Node):
                if not item_ids:
                    return BehaviorTree.NodeState.FAILURE

                identified_any = False
                items = [ITEM_CACHE.get_item_snapshot(iid) for iid in item_ids]
                
                for item in items:
                    if item is None or not item.is_valid or not item.is_inventory_item:
                        continue
                    
                    kit_id = Inventory.GetFirstIDKit()
                    
                    if kit_id == 0:
                        return BehaviorTree.NodeState.FAILURE if fail_if_no_kit else (BehaviorTree.NodeState.SUCCESS if identified_any else (BehaviorTree.NodeState.SUCCESS if succeed_if_already_identified else BehaviorTree.NodeState.FAILURE))
                    
                    Inventory.IdentifyItem(item.id, kit_id)
                    identified_any = True

                return BehaviorTree.NodeState.SUCCESS if identified_any else (BehaviorTree.NodeState.SUCCESS if succeed_if_already_identified else BehaviorTree.NodeState.FAILURE)

            return BehaviorTree.ActionNode(name="Items.IdentifyItems", action_fn=_identify, aftercast_ms=aftercast_ms)

        @staticmethod
        def DestroyItems(
            item_ids: list[int] | None = None,
            aftercast_ms: int = 100,
            succeed_always: bool = True,
        ):
            def _destroy(node: BehaviorTree.Node):
                if not item_ids:
                    return BehaviorTree.NodeState.FAILURE

                destroyed_any = False
                items = [ITEM_CACHE.get_item_snapshot(iid) for iid in item_ids]                
                for item in items:
                    if item is None or not item.is_valid or not item.is_inventory_item:
                        continue
                    
                    Py4GW.Console.Log(node.name, f"Destroying '{item.names.full}' (ID: {item.id}) from bag {item.bag.name} slot {item.slot} quantity {item.quantity}")
                    Inventory.DestroyItem(item.id)
                    destroyed_any = True

                return BehaviorTree.NodeState.SUCCESS if succeed_always else BTNodes._success_if(destroyed_any)

            return BehaviorTree.ActionNode(name="Items.DestroyItems", action_fn=_destroy, aftercast_ms=aftercast_ms)

        class SavalvageProgress():
            def __init__(self, item_id: int, salvage_started_at: float, initial_qty: int, salvage_amount: int):
                self.item_id = item_id
                self.salvage_started_at = salvage_started_at
                self.initial_qty = initial_qty
                self.desired_qty = initial_qty - salvage_amount
                self.salvage_amount = salvage_amount
                self.confirm_clicked_at = 0.0
                self.salvaged_any = False
                
        @staticmethod
        def SalvageItem(
            item_id : int,
            salvage_mode: "SalvageMode | int" = 0,
            salvage_amount: Optional[int] = None,
            allow_expert_for_common_materials: bool = False,
            state_key: str = "_salvage_state",
            timeout_ms_per_item: int = 1500,
            aftercast_ms: int = 0,
        ):
            def _reset_state(node: BehaviorTree.Node):
                node.blackboard.pop(state_key, None)
            
            def _get_expert_salvage_kit() -> int:
                inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(Bag.Backpack, Bag.Bag_2)
                expert_kits = [i for bag in inventory_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.is_salvage_kit and i.model_id in (ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit)]
                
                if not expert_kits:
                    return 0
                
                return min(expert_kits, key=lambda k: k.uses).id
            
            def _get_lesser_salvage_kit() -> int:
                inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(Bag.Backpack, Bag.Bag_2)
                lesser_kits = [i for bag in inventory_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.is_salvage_kit and i.model_id == ModelID.Salvage_Kit]
                
                if not lesser_kits:
                    return 0
                
                return min(lesser_kits, key=lambda k: k.uses).id
            
            def _is_mod_salvaged(item: ItemSnapshot, salvage_mode: SalvageMode) -> bool:
                match salvage_mode:
                    case SalvageMode.Prefix:
                        return item.prefix is None
                    
                    case SalvageMode.Suffix:
                        return item.suffix is None
                    
                    case SalvageMode.Inscription:
                        return item.inscription is None
            
                return False
            
            def _salvage(node: BehaviorTree.Node):        
                if item_id is None or item_id <= 0:
                    return BehaviorTree.NodeState.FAILURE
                
                try:
                    mode = SalvageMode(int(salvage_mode))
                except Exception:
                    mode = SalvageMode.NONE
                
                if mode == SalvageMode.NONE:
                    return BehaviorTree.NodeState.FAILURE
                                
                state = node.blackboard.get(state_key)
                state = cast(BTNodes.Items.SavalvageProgress, state) if state else None
                item = ITEM_CACHE.get_item_snapshot(item_id)
                
                if (state and item_id != state.item_id) or item is None or not item.is_valid or not item.is_salvageable or not item.is_inventory_item or _is_mod_salvaged(item, mode):
                    return BehaviorTree.NodeState.SUCCESS
                
                if state is None:
                    state = BTNodes.Items.SavalvageProgress(item_id=item.id, salvage_started_at=0.0, initial_qty=item.quantity, salvage_amount=min(item.quantity, salvage_amount if salvage_amount else item.quantity))                   
                    node.blackboard[state_key] = state
                    
                now = time.monotonic()

                if Inventory.GetFreeSlotCount() <= 0:
                    return BehaviorTree.NodeState.FAILURE

                # Start salvage once per item.
                if not state.salvage_started_at:                    
                    if salvage_mode != SalvageMode.LesserCraftingMaterials:
                        kit_id = _get_expert_salvage_kit()
                        
                    else:
                        kit_id = _get_lesser_salvage_kit()
                        if allow_expert_for_common_materials and kit_id == 0:
                            kit_id = _get_expert_salvage_kit()

                    kit = ITEM_CACHE.get_item_snapshot(kit_id)
                    if kit_id <= 0 or (kit is None or kit.model_id == ModelID.Salvage_Kit and (item.rarity > Rarity.White and not item.is_identified)):
                        return BehaviorTree.NodeState.FAILURE

                    Inventory.SalvageItem(item_id, kit_id)
                    state.salvage_started_at = now
                    return BehaviorTree.NodeState.RUNNING

                # Handle salvage windows/frames while waiting for completion.
                if UIManagerExtensions.IsConfirmLesserMaterialsWindowOpen():
                    if UIManagerExtensions.ConfirmLesserSalvage():
                        state.confirm_clicked_at = now
                        return BehaviorTree.NodeState.RUNNING
                    
                if UIManagerExtensions.ConfirmModMaterialSalvageVisible():
                    if UIManagerExtensions.ConfirmModMaterialSalvage():
                        state.confirm_clicked_at = now
                        return BehaviorTree.NodeState.RUNNING
                    
                if UIManagerExtensions.IsSalvageWindowNoIdentifiedOpen():
                    if UIManagerExtensions.ConfirmSalvageWindowNoIdentified():
                        state.confirm_clicked_at = now
                        return BehaviorTree.NodeState.RUNNING
                    
                if UIManagerExtensions.IsSalvageWindowOpen():
                    if UIManagerExtensions.SelectSalvageOptionAndSalvage(mode):
                        state.confirm_clicked_at = now
                        return BehaviorTree.NodeState.RUNNING
                    else:
                        UIManagerExtensions.CancelSalvageOption()
                        return BehaviorTree.NodeState.FAILURE

                # Completion checks.
                current_qty = item.quantity
                initial_qty = state.initial_qty
                desired_qty = state.desired_qty
                confirm_clicked_at = state.confirm_clicked_at

                qty_changed = current_qty < initial_qty
                item_gone = not item.is_inventory_item
                mod_salvaged = _is_mod_salvaged(item, mode)
                windows_closed_after_confirm = (
                    confirm_clicked_at > 0.0
                    and not UIManagerExtensions.AnySalvageRelatedWindowOpen()
                    and (now - confirm_clicked_at) >= 0.20
                )
                
                if not item_gone and item.is_stackable and qty_changed and current_qty > desired_qty:
                    Py4GW.Console.Log("BTNodes.Items.SalvageItem", f"Partially salvaged item id {item.id}, quantity reduced from {initial_qty} to {current_qty}, desired quantity is {desired_qty}. Continuing to salvage the remaining quantity.")
                    state.salvage_started_at = 0.0
                    state.initial_qty = item.quantity
                    
                    return BehaviorTree.NodeState.RUNNING

                if qty_changed or item_gone or windows_closed_after_confirm or mod_salvaged:
                    return BehaviorTree.NodeState.SUCCESS

                if (now - float(state.salvage_started_at)) * 1000 >= timeout_ms_per_item:
                    Py4GW.Console.Log("BTNodes.Items.SalvageItem", f"Salvage of item id {item.id} timed out after {timeout_ms_per_item} ms. Failing salvage action.")
                    node.blackboard.pop(state_key, None)
                    return BehaviorTree.NodeState.FAILURE

                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree.ActionNode(name="Items.SalvageItems", action_fn=_salvage, aftercast_ms=aftercast_ms)

        class ItemTransferInstructions:
            def __init__(self, bag: Bag, slot: int, stack_item: Optional[ItemSnapshot], available_space: int = MAX_STACK_SIZE):                
                self.bag = bag
                self.slot = slot
                self.stack_item = stack_item                
                self.available_space = available_space - stack_item.quantity if stack_item and stack_item.is_stackable else available_space
                
                self.items : list[tuple[ItemSnapshot, int]] = []
        
        @staticmethod
        def GetTransferInstructions(
            item_ids: list[int],
            target : list[Bag],
            quantities: Optional[list[int]] = None,
            fill_materials_first: bool = False,
        ) -> dict[Bag, dict[int, BTNodes.Items.ItemTransferInstructions]]:
            
            locations = GetItemsLocations(item_ids)
            source = list(set(bag for bag, _ in locations))
            
            to_inventory = any(bag in INVENTORY_BAGS for bag in target)
            to_storage = any(bag in STORAGE_BAGS or bag == Bag.Material_Storage for bag in target)
            
            from_inventory = any(bag in INVENTORY_BAGS for bag in source)
            from_storage = any(bag in STORAGE_BAGS or bag == Bag.Material_Storage for bag in source)
           
            material_storage_snapshot = ITEM_CACHE.get_bag_snapshot(Bag.Material_Storage) if (from_storage or to_storage) else {}
            target_snapshot = ITEM_CACHE.get_bags_snapshot(target)
            moving_instructions : dict[Bag, dict[int, BTNodes.Items.ItemTransferInstructions]] = {}
            
            #get max quantity from material_storage_snapshot.get(Bag.Material_Storage, {}).values() and ceil to the next MAX_STACK_SIZE to determine the max capacity
            material_storage_capacity = (
                max(
                    (item.quantity for item in material_storage_snapshot.values() if item),
                    default=0
                )
                + MAX_STACK_SIZE - 1
            ) // MAX_STACK_SIZE * MAX_STACK_SIZE
            if material_storage_capacity <= 0:
                material_storage_capacity = MAX_STACK_SIZE
                                            
            for index, item_id in enumerate(item_ids):
                item = ITEM_CACHE.get_item_snapshot(item_id)
                qty = quantities[index] if quantities and index < len(quantities) else item.quantity if item else 0            
                
                if not item or not item.is_valid or (item.is_inventory_item and to_inventory) or (item.is_storage_item and to_storage) or (not item.is_inventory_item and from_inventory) or (not item.is_storage_item and from_storage):
                    continue
                
                if item.is_stackable:
                    if fill_materials_first and from_inventory and (item.is_material or item.is_rare_material):
                        for slot, stack_item in material_storage_snapshot.items():
                            if stack_item and stack_item.is_valid and stack_item.is_stackable and stack_item.same_kind_as(item) and stack_item.quantity < material_storage_capacity:
                                moving_instructions.setdefault(Bag.Material_Storage, {})
                                dest = moving_instructions[Bag.Material_Storage].setdefault(slot, BTNodes.Items.ItemTransferInstructions(Bag.Material_Storage, slot, stack_item, available_space=material_storage_capacity))
                                
                                if dest.available_space > 0:
                                    qty_to_move = min(dest.available_space, qty)
                                    dest.available_space -= qty_to_move
                                    dest.items.append((item, qty_to_move))
                                    qty -= qty_to_move
                                    
                                    stack_item.quantity += qty_to_move  # simulate the move in the cache to get correct available space for subsequent stacks of the same item
                                    
                                    if qty <= 0:
                                        Py4GW.Console.Log("GetTransferInstructions", f"Planned to move {qty_to_move} of '{item.names.plain}' (ID: {item.id}) to Material Storage bag {Bag.Material_Storage.name} slot {slot}")
                                        break
                        
                        if qty <= 0:
                            break                                
                        
                    # get all items with the same model and type that have free space in their stacks and add them as potential destinations for the current item until we have found enough space for the whole stack. This way we minimize fragmentation in the bank and maximize the chances of fitting all items. We get them all from bag_enum, bag in inventory_snapshot.items()
                    stacks_of_same_kind_with_space = [(i, bag_id) for bag_id, bag in target_snapshot.items() for i in bag.values() if i and i.is_valid and i.is_stackable and i.same_kind_as(item) and i.quantity < MAX_STACK_SIZE]
                    
                    #sorted by least free space to most free space to fill up more full stacks first, then by bag and slot, so we fill from the beginning of the bank to the end to minimize fragmentation
                    stacks_of_same_kind_with_space.sort(key=lambda x: (-x[0].quantity, x[1].value, x[0].slot))
                    
                    for stack_item, bag in stacks_of_same_kind_with_space:
                        if stack_item.quantity >= MAX_STACK_SIZE:
                            continue
                        
                        moving_instructions.setdefault(bag, {})
                        dest = moving_instructions[bag].setdefault(stack_item.slot, BTNodes.Items.ItemTransferInstructions(bag, stack_item.slot, stack_item))
                        if dest.available_space > 0:
                            qty_to_move = min(dest.available_space, qty)
                            dest.available_space -= qty_to_move
                            dest.items.append((item, qty_to_move))
                            qty -= qty_to_move
                            
                            stack_item.quantity += qty_to_move  # simulate the move in the cache to get correct available space for subsequent stacks of the same item
                            
                            if qty <= 0:
                                Py4GW.Console.Log("GetTransferInstructions", f"Item quantity reduced to 0, moving on to next item.")
                                break
                    
                    
                        if qty <= 0:
                            break
                    
                if qty > 0:
                    for bag_enum, bag in target_snapshot.items():
                        for slot, stack_item in bag.items():
                            if stack_item is None:
                                moving_instructions.setdefault(bag_enum, {})
                                dest = moving_instructions[bag_enum].setdefault(slot, BTNodes.Items.ItemTransferInstructions(bag_enum, slot, None))
                                
                                qty_to_move = min(dest.available_space, qty)
                                dest.available_space -= qty_to_move
                                dest.items.append((item, qty_to_move))
                                qty -= qty_to_move
                                                                
                                if qty <= 0:
                                    break
                        
                        if qty <= 0:
                            break
                
            return moving_instructions            
        
        @staticmethod
        def DepositItems(
            item_ids: list[int],
            target : list[Bag] = STORAGE_BAGS,
            anniversary_panel: bool = False,
            fill_materials_first: bool = True,
            fail_if_no_space: bool = True,
            aftercast_ms: int = 25,
        ):
            if not anniversary_panel and Bag.Storage_14 in target:
                target = [b for b in target if b != Bag.Storage_14]
            
            def _deposit(node: BehaviorTree.Node):
                instructions = BTNodes.Items.GetTransferInstructions(item_ids, target, fill_materials_first=fill_materials_first)
                moved_any = False
                
                if not instructions:
                    return BehaviorTree.NodeState.FAILURE if fail_if_no_space else BehaviorTree.NodeState.SUCCESS
                
                for bag in instructions.values():
                    for dest in bag.values():
                        for item, qty in dest.items:
                            Inventory.MoveItem(item.id, dest.bag.value, dest.slot, qty)
                            Py4GW.Console.Log(node.name, f"Moving {qty} of '{item.names.plain}' (ID: {item.id}) to bag {dest.bag.name} slot {dest.slot}")
                            moved_any = True
                
                return BehaviorTree.NodeState.SUCCESS if moved_any else BehaviorTree.NodeState.FAILURE

            return BehaviorTree.ActionNode(name="Items.DepositItems", action_fn=_deposit, aftercast_ms=aftercast_ms)
        
        @staticmethod
        def WithdrawItems(
            item_ids: list[int],
            target : list[Bag] = INVENTORY_BAGS,
            fill_materials_first: bool = True,
            fail_if_no_space: bool = True,
            aftercast_ms: int = 25,
        ):                   
            def _withdraw(node: BehaviorTree.Node):
                instructions = BTNodes.Items.GetTransferInstructions(item_ids, target, fill_materials_first=fill_materials_first)
                moved_any = False
                
                if not instructions:
                    return BehaviorTree.NodeState.FAILURE if fail_if_no_space else BehaviorTree.NodeState.SUCCESS
                
                for bag in instructions.values():
                    for dest in bag.values():
                        for item, qty in dest.items:
                            Inventory.MoveItem(item.id, dest.bag.value, dest.slot, qty)
                            Py4GW.Console.Log(node.name, f"Moving {qty} of '{item.names.plain}' (ID: {item.id}) to bag {dest.bag.name} slot {dest.slot}")
                            moved_any = True
                
                return BehaviorTree.NodeState.SUCCESS if moved_any else BehaviorTree.NodeState.FAILURE

            return BehaviorTree.ActionNode(name="Items.WithdrawItems", action_fn=_withdraw, aftercast_ms=aftercast_ms)

    class Bags:
        @staticmethod
        def Restock(
            model_id: int,
            item_type: ItemType,
            quantity: int,
        ):
            def _restock(node: BehaviorTree.Node):        
                inventory_snapshot = ITEM_CACHE.get_inventory_snapshot(Bag.Backpack, Bag.Bag_2)
                current_qty = sum(i.quantity for bag in inventory_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.model_id == model_id and i.item_type == item_type) if inventory_snapshot else 0
                left_to_restock = max(0, quantity - current_qty)
                
                if left_to_restock <= 0:
                    return BehaviorTree.NodeState.SUCCESS
                
                storage_snapshot = ITEM_CACHE.get_bags_snapshot(STORAGE_BAGS)
                desired_items = [i for bag in storage_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.model_id == model_id and i.item_type == item_type] if storage_snapshot else []
                
                if not desired_items:
                    return BehaviorTree.NodeState.FAILURE
                
                item_ids = []
                quantities = []
                
                sort_by_lowest_qty = sorted(desired_items, key=lambda i: i.quantity)
                for item in sort_by_lowest_qty:
                    if item.quantity <= 0:
                        continue
                    
                    has_space, space_for_qty = HasSpaceForItem(item.id, Bag.Backpack, Bag.Bag_2, quantity=item.quantity)
                    if not has_space or space_for_qty <= 0:
                        continue
                                        
                    qty_to_move = min(space_for_qty, item.quantity, left_to_restock)
                    current_qty += qty_to_move
                    
                    item_ids.append(item.id)
                    quantities.append(qty_to_move)
                    left_to_restock -= qty_to_move
                    
                    if left_to_restock <= 0:
                        break
                
                instructions = BTNodes.Items.GetTransferInstructions(item_ids, INVENTORY_BAGS, quantities=quantities)
                if not instructions:
                    return BehaviorTree.NodeState.FAILURE
                
                for bag in instructions.values():
                    for dest in bag.values():
                        for item, qty in dest.items:
                            Inventory.MoveItem(item.id, dest.bag.value, dest.slot, qty)
                            Py4GW.Console.Log(node.name, f"Moving {qty} of '{item.names.plain}' (ID: {item.id}) to bag {dest.bag.name} slot {dest.slot}")

                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.ActionNode(name="Bags.Restock", action_fn=_restock)
        
        @staticmethod
        def FillMaterialStorage(
            source : list[Bag] = STORAGE_BAGS,
            aftercast_ms: int = 150,
            succeed_if_already_filled: bool = True,
        ):
            def _fill_material_storage(node: BehaviorTree.Node):
                source_bags = [bag for bag in source if bag != Bag.Material_Storage]
                if not source_bags:
                    return BehaviorTree.NodeState.FAILURE

                source_snapshot = ITEM_CACHE.get_bags_snapshot(source_bags)
                material_snapshot = ITEM_CACHE.get_bag_snapshot(Bag.Material_Storage)

                material_storage_capacity = (
                    max((item.quantity for item in material_snapshot.values() if item), default=0) + MAX_STACK_SIZE - 1
                ) // MAX_STACK_SIZE * MAX_STACK_SIZE
                if material_storage_capacity <= 0:
                    material_storage_capacity = MAX_STACK_SIZE

                moved_any = False
                transfer_instructions: dict[int, BTNodes.Items.ItemTransferInstructions] = {}
                bag_item_map : dict[int, Bag] = {item_id: bag for bag, bag_items in source_snapshot.items() for item_id, item in bag_items.items() if item}
                
                for _, bag_items in source_snapshot.items():
                    for _, item in bag_items.items():
                        if item is None or not item.is_valid or not item.is_stackable or bag_item_map.get(item.id) == Bag.Material_Storage:
                            continue
                        
                        if not (item.is_material or item.is_rare_material):
                            continue
                        
                        slot = MATERIAL_SLOTS.get(item.model_id, None)
                        if slot is None:
                            continue
                        
                        material = material_snapshot.get(slot, None)
                        transfer_instructions.setdefault(slot, BTNodes.Items.ItemTransferInstructions(Bag.Material_Storage, slot, material, available_space=material_storage_capacity))
                        inst = transfer_instructions.get(slot)
                        
                        if inst is None:
                            continue
                        
                        qty_to_move = min(inst.available_space, item.quantity)
                        
                        if qty_to_move <= 0:
                            continue
                        
                        inst.available_space -= qty_to_move
                        inst.items.append((item, qty_to_move))
                        item.quantity -= qty_to_move
                
                for dest in transfer_instructions.values():
                    for item, qty in dest.items:
                        Inventory.MoveItem(item.id, dest.bag.value, dest.slot, qty)
                        Py4GW.Console.Log(node.name, f"Moving {qty} of '{item.names.plain}' (ID: {item.id}) to Material Storage slot {dest.slot}")
                        moved_any = True

                return BTNodes._success_if(moved_any or succeed_if_already_filled)

            return BehaviorTree.ActionNode(name="Inventory.FillMaterialStorage", action_fn=_fill_material_storage, aftercast_ms=aftercast_ms)
        
        @staticmethod
        def CompactBags(
            bags : list[Bag] = INVENTORY_BAGS,         
            aftercast_ms: int = 150,
        ):
            def _compact(node: BehaviorTree.Node):
                snapshot = ITEM_CACHE.get_bags_snapshot(bags)
                grouped_items : dict[tuple[ItemType, int, int], list[tuple[Bag, int, ItemSnapshot]]] = {}
                moved_any = False
                
                for bag in bags:
                    for slot, item in snapshot.get(bag, {}).items():
                        if item and item.is_valid and item.is_stackable and item.quantity < MAX_STACK_SIZE:
                            key = (item.item_type, item.model_id, item.color.value)
                            grouped_items.setdefault(key, []).append((bag, slot, item))
                            
                for _, items in grouped_items.items():
                    if len(items) <= 1:
                        continue
                    
                    items.sort(key=lambda x: x[2].quantity, reverse=True)
                    target_bag, target_slot, target_item = items[0]
                    
                    for source_bag, source_slot, source_item in items[1:]:
                        if target_item.quantity >= MAX_STACK_SIZE:
                            break
                        
                        qty_to_move = min(source_item.quantity, MAX_STACK_SIZE - target_item.quantity)
                        if qty_to_move <= 0:
                            continue
                        
                        Inventory.MoveItem(source_item.id, target_bag.value, target_slot, qty_to_move)
                        Py4GW.Console.Log(node.name, f"Moved {qty_to_move} of '{source_item.names.plain}' (ID: {source_item.id}) from bag {source_bag.name} slot {source_slot} to bag {target_bag.name} slot {target_slot}")
                        moved_any = True
                        target_item.quantity += qty_to_move
                        source_item.quantity -= qty_to_move
                
                
                return BTNodes._success_if(moved_any)
            return BehaviorTree.ActionNode(name="Inventory.CompactBags", action_fn=_compact, aftercast_ms=aftercast_ms)

        @staticmethod
        def SortBags(
            bags : list[Bag] = INVENTORY_BAGS,         
            aftercast_ms: int = 150,
        ):
            def _sort(node: BehaviorTree.Node):
                snapshot = ITEM_CACHE.get_bags_snapshot(bags)

                # TODO: Here we want to implement our sorting configuration, for now this is just the default behavior
                item_typeOrder = [
                    int(ItemType.Kit),
                    int(ItemType.Key),
                    int(ItemType.Usable),
                    int(ItemType.Trophy),
                    int(ItemType.Quest_Item),
                    int(ItemType.Materials_Zcoins)
                ]

                # then everything else
                item_typeOrder += [int(item)
                                for item in ItemType if int(item) not in item_typeOrder]
                
                index_to_bag_map : dict[int, tuple[Bag, int]] = {}
                index = 0
                
                for bag in bags:
                    for slot in snapshot.get(bag, {}).keys():
                        index_to_bag_map[index] = (bag, slot)
                        index += 1
                            
                items = [item for bag in bags for slot, item in snapshot.get(bag, {}).items() if item and item.is_valid]
                sorted_items = sorted(
                    items,
                    key=lambda item: (
                        item.item_type == ItemType.Unknown,
                        item_typeOrder.index(item.item_type),
                        item.model_id,
                        -item.rarity.value,
                        -item.quantity,
                        -item.value,
                        item.color.value,
                        item.id
                    )
                )
                
                for index, item in enumerate(sorted_items):
                    bag, slot = index_to_bag_map.get(index, (None, None))
                    
                    if bag is None or slot is None:
                        continue
                
                    Inventory.MoveItem(item.id, bag.value, slot, item.quantity)
                
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.ActionNode(name="Inventory.SortBags", action_fn=_sort, aftercast_ms=aftercast_ms)

    class Crafting:
        @staticmethod
        def CraftItem(
            output_item_id: int,
            cost: int,
            material_item_ids: list[int],
            material_quantities: list[int],
            aftercast_ms: int = 250,
        ):
            def _craft():
                k = min(len(material_item_ids), len(material_quantities))
                if output_item_id <= 0 or k == 0:
                    return BehaviorTree.NodeState.FAILURE
                Trading.Crafter.CraftItem(output_item_id, cost, material_item_ids[:k], material_quantities[:k])
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.ActionNode(name="Crafting.CraftItem", action_fn=_craft, aftercast_ms=aftercast_ms)

        @staticmethod
        def CraftItems(
            recipes: dict[int, tuple[list[int], list[int]]],
            aftercast_ms: int = 250,
        ):
            def _craft(node: BehaviorTree.Node):
                crafted_any = False
                for output_item_id, (material_item_ids, material_quantities) in recipes.items():
                    k = min(len(material_item_ids), len(material_quantities))
                    
                    if output_item_id <= 0 or k == 0:
                        continue
                    
                    Trading.Crafter.CraftItem(output_item_id, 0, material_item_ids[:k], material_quantities[:k])
                    crafted_any = True
                    
                return BTNodes._success_if(crafted_any)

            return BehaviorTree.ActionNode(name="Crafting.CraftItems", action_fn=_craft, aftercast_ms=aftercast_ms)
