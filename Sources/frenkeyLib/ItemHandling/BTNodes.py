"""
BT nodes support file notes
===========================

This file is both:
- a behavior-tree helper surface for frenkeyLib item handling flows
- a support layer that builds ready-to-run `BehaviorTree` nodes for inventory,
  merchant, trader, storage, and crafting actions

Authoring and discovery conventions
-----------------------------------
- Keep existing class names as the system-level grouping surface.
- Use `PascalCase` for public/front-facing routine methods.
- Use `snake_case` for helper/internal methods.
- Use `_snake_case` for explicitly private helpers.
- Treat the structured `Meta:` block as the discovery gate.

Routine docstring template
--------------------------
Each routine docstring should use:
- a free human-readable description first
- a structured `Meta:` block after it

Template:

    \"\"\"
    One or more human-readable paragraphs explaining what the routine builds.

    Meta:
      Expose: true
      Audience: intermediate
      Display: Sell Items
      Purpose: Sell a list of inventory items through the open merchant window.
      UserDescription: Use this when you want a BT step that sells known item ids.
      Notes: Keep metadata single-line. Structural truth should stay in code.
    \"\"\"

Docstring parsing rules
-----------------------
- Only the `Meta:` section is intended for machine parsing.
- Keep metadata lines single-line and in `Key: Value` form.
- Unknown keys should be safe for tooling to ignore.
- Prefer adding presentation/help metadata in docstrings instead of duplicating
  structural metadata that already exists in code.
"""

from __future__ import annotations

import time
from typing import Optional, cast

import Py4GW

from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.Item import Item
from Py4GWCoreLib.Merchant import Trading
from Py4GWCoreLib.enums_src.Item_enums import INVENTORY_BAGS, MAX_STACK_SIZE, STORAGE_BAGS, Bags, ItemType, Rarity, SalvageMode
from Py4GWCoreLib.enums_src.Item_enums import MAX_STACK_SIZE
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.item_data.ItemData import MATERIAL_STORAGE_SLOTS
from Py4GWCoreLib.item_data.item_snapshot import ItemSnapshot
from Sources.frenkeyLib.ItemHandling.UIManagerExtensions import UIManagerExtensions
from Sources.frenkeyLib.ItemHandling.utility import HasSpaceForItem

SALVAGE_WINDOW_HASH = 684387150
LESSER_CONFIRM_HASH = 140452905

class BTNodes:
    """
    Root BT helper catalog for frenkeyLib item-handling routines.

    Meta:
      Expose: true
      Audience: advanced
      Display: BT Nodes
      Purpose: Group BT helper routines for item handling, trading, storage movement, and crafting flows.
      UserDescription: Root catalog for frenkeyLib behavior-tree helper routines.
      Notes: Discovery should start from this class and then inspect grouped helper surfaces marked for exposure.
    """
    NodeState = BehaviorTree.NodeState
    
    @staticmethod
    def debug(category: str, message: str, log_to_console: bool = True):
        if log_to_console:
            Py4GW.Console.Log(category, message)

    @staticmethod
    def _success_if(condition: bool) -> BehaviorTree.NodeState:
        """
        Convert a boolean condition into a success-or-failure node state.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal Success If Helper
          Purpose: Normalize simple boolean results into `BehaviorTree.NodeState` values for helper routines.
          UserDescription: Internal support routine.
          Notes: Returns success for truthy input and failure for falsy input.
        """
        return BehaviorTree.NodeState.SUCCESS if condition else BehaviorTree.NodeState.FAILURE

    class Merchant:
        """
        BT helper group for merchant-window item transactions.

        Meta:
          Expose: true
          Audience: advanced
          Display: Merchant
          Purpose: Group BT helper routines that buy, sell, and restock items through merchant interactions.
          UserDescription: Built-in BT helper group for merchant-window actions.
          Notes: These routines expect the merchant window to already be open when they run.
        """
        @staticmethod 
        def Restock(
            model_id: int,
            item_type: ItemType,
            quantity: int,
        ):
            """
            Build an action node that restocks a merchant item until the requested inventory quantity is met.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Restock
              Purpose: Buy enough copies of a merchant item to reach a target quantity in inventory.
              UserDescription: Use this when you want a BT step that tops inventory back up from an open merchant window.
              Notes: Fails when the merchant window is closed, the item is not offered, there is no space, or the player cannot afford enough stock.
            """
            def _restock(node: BehaviorTree.Node):
                if not UIManagerExtensions.MerchantWindow.IsOpen():
                    return BehaviorTree.NodeState.FAILURE
                
                inventory_snapshot = ItemSnapshot.get_inventory_snapshot(Bags.Backpack, Bags.Bag2)
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
                has_space, space_for_qty = HasSpaceForItem(item_id, Bags.Backpack, Bags.Bag2, quantity=affordable_qty)
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
            """
            Build an action node that sells a list of inventory items through the open merchant window.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Sell Items
              Purpose: Sell one or more inventory items to the currently open merchant.
              UserDescription: Use this when you want a BT step that sells known item ids at a merchant.
              Notes: Ignores invalid or non-inventory items and succeeds only if at least one item is sold.
            """
            def _sell(node: BehaviorTree.Node):
                if not UIManagerExtensions.MerchantWindow.IsOpen():
                    return BehaviorTree.NodeState.FAILURE
                
                items = [ItemSnapshot.from_item_id(iid) for iid in item_ids]
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
            """
            Build an action node that buys several offered merchant items with quantity limits.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Buy Items
              Purpose: Buy one or more offered merchant items while respecting gold and bag-space limits.
              UserDescription: Use this when you want a BT step that purchases several merchant items in one pass.
              Notes: Skips items that are unavailable, unaffordable, or cannot fit in inventory, and succeeds only if at least one purchase is made.
            """
            def _buy(node: BehaviorTree.Node):
                if not UIManagerExtensions.MerchantWindow.IsOpen():  
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
                    has_space, qty = HasSpaceForItem(offered_item_id, Bags.Backpack, Bags.Bag2, quantity=affordable_qty)
                    count = min(quantity, affordable_qty, qty)
                    
                    if not has_space or count <= 0:
                        continue
                                        
                    for _ in range(max(0, count)):
                        Trading.Merchant.BuyItem(offered_item_id, price)
                        bought_any = True

                return BTNodes._success_if(bought_any)

            return BehaviorTree.ActionNode(name="Merchant.BuyItems", action_fn=_buy, aftercast_ms=aftercast_ms)

    class Trader:
        """
        BT helper group for quoted trader buy and sell flows.

        Meta:
          Expose: true
          Audience: advanced
          Display: Trader
          Purpose: Group BT helper routines that interact with trader quotes and transactional progress state.
          UserDescription: Built-in BT helper group for trader-window purchase and sale flows.
          Notes: These routines manage quote polling and transaction confirmation through blackboard state.
        """
        class TraderProgress:
            """
            Internal runtime progress container for multi-step trader transactions.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Trader Progress
              Purpose: Store quote and transaction progress state for trader buy and sell helper routines.
              UserDescription: Internal support helper class.
              Notes: This class is blackboard-backed runtime state and not intended for direct discovery.
            """
            def __init__(self):                
                """
                Initialize default trader progress bookkeeping fields.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Trader Progress Initializer
                  Purpose: Set up initial quote, trade, and quantity-tracking fields for trader flows.
                  UserDescription: Internal support routine.
                  Notes: Used by trader buy and sell helpers to persist progress across ticks.
                """
                self.initial_qty = 0
                self.current_qty = 0
                self.desired_qty = 0
                
                self.quote_requested_at = 0.0
                self.traded_at = 0.0
                
                self.requested = False
                self.traded = False
                self.trade_confirmed = False
            
            def reset(self):        
                """
                Reset transient quote and trade confirmation fields.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Trader Progress Reset Helper
                  Purpose: Clear quote timing and trade confirmation state while preserving quantity targets.
                  UserDescription: Internal support routine.
                  Notes: Used when a trader flow needs to restart a quote-confirmation cycle.
                """
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
            """
            Build an action node that buys a trader item by repeatedly requesting quotes until the desired quantity is reached.

            Meta:
              Expose: true
              Audience: advanced
              Display: Buy Item
              Purpose: Purchase a trader item through the quote-confirmation flow until a target quantity is reached.
              UserDescription: Use this when you want a BT step that handles trader quote timing automatically for one item.
              Notes: Stores progress in the blackboard under `trader_buy_progress` and returns running while the quote cycle is active.
            """
            def _buy(node: BehaviorTree.Node):
                now = time.monotonic()
                
                if not UIManagerExtensions.MerchantWindow.IsOpen():
                    return BehaviorTree.NodeState.FAILURE
                
                offered_items = Trading.Trader.GetOfferedItems()
                
                if item_id not in offered_items:
                    return BehaviorTree.NodeState.FAILURE
                
                item = ItemSnapshot.from_item_id(item_id)
                if not item or not item.is_valid:
                    return BehaviorTree.NodeState.FAILURE
                                 
                state = node.blackboard.get("trader_buy_progress")
                state = cast(BTNodes.Trader.TraderProgress, state) if state else None
                
                if state is None:
                    state = BTNodes.Trader.TraderProgress()
                    inventory_snapshot = ItemSnapshot.get_inventory_snapshot(Bags.Backpack, Bags.Bag2)
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
                        inventory_snapshot = ItemSnapshot.get_inventory_snapshot(Bags.Backpack, Bags.Bag2)
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
            """
            Build an action node that sells a trader item through repeated quote-confirmation cycles.

            Meta:
              Expose: true
              Audience: advanced
              Display: Sell Item
              Purpose: Sell a trader item until the desired quantity has been removed from inventory.
              UserDescription: Use this when you want a BT step that handles trader sell quotes automatically for one item.
              Notes: Stores progress in the blackboard under `trader_sell_progress` and returns running while the quote cycle is active.
            """
            def _sell(node: BehaviorTree.Node):
                now = time.monotonic()
                
                if not UIManagerExtensions.MerchantWindow.IsOpen():
                    return BehaviorTree.NodeState.FAILURE
                                
                item = ItemSnapshot.from_item_id(item_id)
                
                if not item or not item.is_valid or not item.is_inventory_item:
                    return BehaviorTree.NodeState.SUCCESS
                                 
                state = node.blackboard.get("trader_sell_progress")
                state = cast(BTNodes.Trader.TraderProgress, state) if state else None
                
                if state is None:
                    state = BTNodes.Trader.TraderProgress()
                    inventory_snapshot = ItemSnapshot.get_inventory_snapshot(Bags.Backpack, Bags.Bag2)
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
                        inventory_snapshot = ItemSnapshot.get_inventory_snapshot(Bags.Backpack, Bags.Bag2)
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
        """
        BT helper group for inventory item usage, destruction, movement, salvage, and transfer flows.

        Meta:
          Expose: true
          Audience: advanced
          Display: Items
          Purpose: Group BT helper routines that act on inventory and storage items.
          UserDescription: Built-in BT helper group for inventory, salvage, storage, and transfer actions.
          Notes: Includes both direct inventory actions and storage-transfer planning helpers.
        """
        @staticmethod
        def UseItems(
            item_ids: list[int],
            quantities: Optional[list[int]] = None,
            aftercast_ms: int = 150,
            succeed_if_any_used: bool = True,
        ):
            """
            Build an action node that uses one or more inventory items.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Use Items
              Purpose: Use one or more inventory items, optionally with per-item quantity counts.
              UserDescription: Use this when you want a BT step that consumes or activates known inventory items.
              Notes: Invalid items are skipped and success depends on whether any item was actually used.
            """
            def _use(node: BehaviorTree.Node):
                if not item_ids:
                    return BehaviorTree.NodeState.FAILURE

                used_any = False
                items = [ItemSnapshot.from_item_id(iid) for iid in item_ids]
                
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
            """
            Build an action node that drops one or more inventory items.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Drop Items
              Purpose: Drop one or more inventory items onto the ground.
              UserDescription: Use this when you want a BT step that removes known items from bags by dropping them.
              Notes: Invalid items are skipped and success depends on whether any item was dropped.
            """
            def _drop(node: BehaviorTree.Node):
                if not item_ids:
                    return BehaviorTree.NodeState.FAILURE

                dropped_any = False
                items = [ItemSnapshot.from_item_id(iid) for iid in item_ids]
                
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
            """
            Build an action node that identifies one or more inventory items.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Identify Items
              Purpose: Identify inventory items using the first available identification kit.
              UserDescription: Use this when you want a BT step that identifies a known set of items.
              Notes: Supports configurable behavior when no kit is found or items were already identified.
            """
            def _identify(node: BehaviorTree.Node):
                if not item_ids:
                    return BehaviorTree.NodeState.FAILURE

                identified_any = False
                items = [ItemSnapshot.from_item_id(iid) for iid in item_ids]
                
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
            """
            Build an action node that destroys one or more inventory items.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Destroy Items
              Purpose: Destroy one or more inventory items by item id.
              UserDescription: Use this when you want a BT step that deletes known items from inventory.
              Notes: Can be configured to succeed even when no item was actually destroyed.
            """
            def _destroy(node: BehaviorTree.Node):
                if not item_ids:
                    return BehaviorTree.NodeState.FAILURE

                destroyed_any = False
                items = [ItemSnapshot.from_item_id(iid) for iid in item_ids]                
                for item in items:
                    if item is None or not item.is_valid or not item.is_inventory_item:
                        continue
                    
                    Py4GW.Console.Log(node.name, f"Destroying '{item.names.full}' (ID: {item.id}) from bag {item.bag.name} slot {item.slot} quantity {item.quantity}")
                    Inventory.DestroyItem(item.id)
                    destroyed_any = True

                return BehaviorTree.NodeState.SUCCESS if succeed_always else BTNodes._success_if(destroyed_any)

            return BehaviorTree.ActionNode(name="Items.DestroyItems", action_fn=_destroy, aftercast_ms=aftercast_ms)

        class SavalvageProgress():
            """
            Internal runtime progress container for salvage operations.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Salvage Progress
              Purpose: Store salvage timing, desired quantity, and confirmation state across ticks.
              UserDescription: Internal support helper class.
              Notes: This class is runtime-only salvage bookkeeping and not intended for discovery.
            """
            def __init__(self, item_id: int, salvage_started_at: float, initial_qty: int, salvage_amount: int):
                """
                Initialize salvage progress tracking for one target item.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Salvage Progress Initializer
                  Purpose: Set up the initial salvage state for a single item and target salvage amount.
                  UserDescription: Internal support routine.
                  Notes: Tracks desired quantity reduction and the timing of salvage UI confirmations.
                """
                self.item_id = item_id
                self.salvage_started_at = salvage_started_at
                self.initial_qty = initial_qty
                self.desired_qty = initial_qty - salvage_amount
                self.salvage_amount = salvage_amount
                self.confirm_clicked_at = 0.0
                self.window_detected_at = 0.0
                self.salvaged_any = False
                
        @staticmethod
        def SalvageItem(
            item_id : int,
            salvage_mode: "SalvageMode | int" = 0,
            salvage_amount: Optional[int] = None,
            preferred_kit_id: Optional[int] = None,
            allow_expert_for_common_materials: bool = False,
            state_key: str = "_salvage_state",
            timeout_ms_per_item: int = 1500,
            aftercast_ms: int = 0,
            debug_enabled: bool = False,
        ):
            """
            Build an action node that salvages an item using the requested salvage mode and UI flow.

            Meta:
              Expose: true
              Audience: advanced
              Display: Salvage Item
              Purpose: Drive the salvage window workflow for a target item until the requested salvage completes or fails.
              UserDescription: Use this when you want a BT step that manages salvage UI and progress automatically for one item.
              Notes: Stores runtime state in the blackboard, supports expert or lesser kits, and returns running while the salvage flow is in progress.
            """
            def _reset_state(node: BehaviorTree.Node):
                node.blackboard.pop(state_key, None)

            def _debug(message: str, msg_type: int = Py4GW.Console.MessageType.Info):
                if not debug_enabled:
                    return
                Py4GW.Console.Log("BTNodes.Items.SalvageItem", message, msg_type)

            pop_up_delays = 0
            
            def _resolve_preferred_kit(valid_model_ids: tuple[ModelID, ...]) -> int:
                if preferred_kit_id is None or preferred_kit_id <= 0:
                    return 0

                preferred = ItemSnapshot.from_item_id(preferred_kit_id)
                if preferred is None or not preferred.is_valid or not preferred.is_salvage_kit or preferred.uses <= 0:
                    return 0

                try:
                    preferred_model_id = ModelID(preferred.model_id)
                except ValueError:
                    return 0

                return preferred.id if preferred_model_id in valid_model_ids else 0

            def _get_expert_salvage_kit() -> int:
                preferred = _resolve_preferred_kit((ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit))
                if preferred > 0:
                    return preferred

                inventory_snapshot = ItemSnapshot.get_inventory_snapshot(Bags.Backpack, Bags.Bag2)
                expert_kits = [i for bag in inventory_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.is_salvage_kit and i.model_id in (ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit)]
                
                if not expert_kits:
                    return 0
                
                return min(expert_kits, key=lambda k: k.uses).id
            
            def _get_lesser_salvage_kit() -> int:
                preferred = _resolve_preferred_kit((ModelID.Salvage_Kit,))
                if preferred > 0:
                    return preferred

                inventory_snapshot = ItemSnapshot.get_inventory_snapshot(Bags.Backpack, Bags.Bag2)
                lesser_kits = [i for bag in inventory_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.is_salvage_kit and i.model_id == ModelID.Salvage_Kit]
                
                if not lesser_kits:
                    return 0
                
                return min(lesser_kits, key=lambda k: k.uses).id

            def _get_upgrade_salvage_kit() -> int:
                preferred = _resolve_preferred_kit((ModelID.Perfect_Salvage_Kit, ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit))
                if preferred > 0:
                    return preferred

                inventory_snapshot = ItemSnapshot.get_inventory_snapshot(Bags.Backpack, Bags.Bag2)
                upgrade_kits = [
                    i for bag in inventory_snapshot.values() for i in bag.values()
                    if i is not None and i.is_valid and i.is_salvage_kit and i.model_id in (
                        ModelID.Perfect_Salvage_Kit,
                        ModelID.Expert_Salvage_Kit,
                        ModelID.Superior_Salvage_Kit,
                    )
                ]

                if not upgrade_kits:
                    return 0

                return min(upgrade_kits, key=lambda k: k.uses).id
            
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
                    _debug(f"Invalid item_id={item_id}.")
                    return BehaviorTree.NodeState.FAILURE
                
                try:
                    mode = SalvageMode(int(salvage_mode))
                except Exception:
                    mode = SalvageMode.NONE
                
                if mode == SalvageMode.NONE:
                    _debug(f"Invalid salvage mode for item id {item_id}: raw={salvage_mode!r}.")
                    return BehaviorTree.NodeState.FAILURE
                                 
                state = node.blackboard.get(state_key)
                state = cast(BTNodes.Items.SavalvageProgress, state) if state else None
                item = ItemSnapshot.from_item_id(item_id)
                item_name = {item.complete_name if item else 'Unknown Item'}
                
                if state and item_id != state.item_id:
                    _debug(f"State item mismatch: requested={item_id}, state_item={state.item_id}.")
                    return BehaviorTree.NodeState.SUCCESS

                if item is None:
                    _debug(f"Item {item_name} [{item_id}] no longer exists.")
                    return BehaviorTree.NodeState.SUCCESS

                if not item.is_valid:
                    _debug(f"Item {item_name} [{item_id}] is not valid.")
                    return BehaviorTree.NodeState.SUCCESS

                if not item.is_salvageable:
                    _debug(f"Item {item_name} [{item_id}] is no longer salvageable.")
                    return BehaviorTree.NodeState.SUCCESS

                if not item.is_inventory_item:
                    _debug(f"Item {item_name} [{item_id}] is no longer in inventory.")
                    return BehaviorTree.NodeState.SUCCESS

                if _is_mod_salvaged(item, mode):
                    _debug(f"Requested salvage mode {mode.name} already resolved for item {item_name} [{item_id}].")
                    return BehaviorTree.NodeState.SUCCESS
                
                if state is None:
                    state = BTNodes.Items.SavalvageProgress(item_id=item.id, salvage_started_at=0.0, initial_qty=item.quantity, salvage_amount=min(item.quantity, salvage_amount if salvage_amount else item.quantity))                   
                    node.blackboard[state_key] = state
                    _debug(
                        f"Initialized salvage state for item={item_name} [{item_id}] mode={mode.name} "
                        f"qty={item.quantity} desired_qty={state.desired_qty} timeout_ms={timeout_ms_per_item}."
                    )
                    
                now = time.monotonic()
                salvage_window_open = UIManagerExtensions.AnySalvageWindowOpen()

                if Inventory.GetFreeSlotCount() <= 0:
                    _debug(f"Cannot salvage item {item_name} [{item_id}]: no free inventory slots.", Py4GW.Console.MessageType.Warning)
                    return BehaviorTree.NodeState.FAILURE

                # Start salvage once per item.
                if not state.salvage_started_at:
                    if salvage_window_open:
                        _debug(
                            f"Cannot start salvage for item={item_name} [{item_id}] while another salvage-related window is open."
                            f"Closing existing salvage windows and waiting before retrying."
                        )
                        UIManagerExtensions.CancelAnySalvageRelatedWindow()
                        return BehaviorTree.NodeState.RUNNING

                    if mode == SalvageMode.LesserCraftingMaterials:
                        kit_id = _get_lesser_salvage_kit()
                        if allow_expert_for_common_materials and kit_id == 0:
                            kit_id = _get_expert_salvage_kit()
                    elif mode == SalvageMode.RareCraftingMaterials:
                        kit_id = _get_expert_salvage_kit()
                    else:
                        kit_id = _get_upgrade_salvage_kit()

                    kit = ItemSnapshot.from_item_id(kit_id)
                    if kit_id <= 0 or (kit is None or kit.model_id == ModelID.Salvage_Kit and (item.rarity > Rarity.White and not item.is_identified)):
                        _debug(
                            f"Failed to resolve valid salvage kit for item={item_name} [{item_id}] mode={mode.name}. "
                            f"kit_id={kit_id} kit_model={(kit.model_id if kit else 'None')} "
                            f"item_rarity={item.rarity.name} item_identified={item.is_identified}.",
                            Py4GW.Console.MessageType.Warning,
                        )
                        return BehaviorTree.NodeState.FAILURE

                    _debug(
                        f"Starting salvage item={item_name} [{item_id}] mode={mode.name} kit_id={kit_id} "
                        f"kit_model={kit.model_id if kit else 'None'} item_qty={item.quantity} "
                        f"preferred_kit_id={preferred_kit_id or 0}."
                    )
                    Inventory.SalvageItem(item_id, kit_id)
                    state.salvage_started_at = now
                    return BehaviorTree.NodeState.RUNNING

                # Handle salvage windows/frames while waiting for completion.
                if UIManagerExtensions.LesserSalvageWindow.IsOpen():
                    if not state.window_detected_at:
                        state.window_detected_at = now
                    elapsed_ms = int((now - state.window_detected_at) * 1000)
                    if elapsed_ms < pop_up_delays:
                        _debug(
                            f"Confirm lesser materials window open for item={item_name} [{item_id}]; "
                            f"waiting {elapsed_ms}/{pop_up_delays} ms before confirm."
                        )
                        return BehaviorTree.NodeState.RUNNING
                    if UIManagerExtensions.LesserSalvageWindow.Confirm():
                        state.confirm_clicked_at = now
                        state.window_detected_at = 0.0
                        _debug(f"Confirmed lesser materials salvage for item={item_name} [{item_id}].")
                        return BehaviorTree.NodeState.RUNNING
                    
                if UIManagerExtensions.SalvageConfirmationPopup.IsOpen():
                    if not state.window_detected_at:
                        state.window_detected_at = now
                    elapsed_ms = int((now - state.window_detected_at) * 1000)
                    if elapsed_ms < pop_up_delays:
                        _debug(
                            f"Confirm mod/material warning visible for item={item_name} [{item_id}]; "
                            f"waiting {elapsed_ms}/{pop_up_delays} ms before confirm."
                        )
                        return BehaviorTree.NodeState.RUNNING
                    if UIManagerExtensions.SalvageConfirmationPopup.Confirm():
                        state.confirm_clicked_at = now
                        state.window_detected_at = 0.0
                        _debug(f"Confirmed mod/material warning for item={item_name} [{item_id}].")
                        return BehaviorTree.NodeState.RUNNING
                    
                if UIManagerExtensions.ExpertSalvageUnidentifiedWindow.IsOpen():
                    if not state.window_detected_at:
                        state.window_detected_at = now
                    elapsed_ms = int((now - state.window_detected_at) * 1000)
                    if elapsed_ms < pop_up_delays:
                        _debug(
                            f"Unidentified salvage warning open for item={item_name} [{item_id}]; "
                            f"waiting {elapsed_ms}/{pop_up_delays} ms before confirm."
                        )
                        return BehaviorTree.NodeState.RUNNING
                    if UIManagerExtensions.ExpertSalvageUnidentifiedWindow.Confirm():
                        state.confirm_clicked_at = now
                        state.window_detected_at = 0.0
                        _debug(f"Confirmed unidentified salvage warning for item={item_name} [{item_id}].")
                        return BehaviorTree.NodeState.RUNNING
                    
                if UIManagerExtensions.SalvageOptionsWindow.IsOpen():
                    if not state.window_detected_at:
                        state.window_detected_at = now
                    elapsed_ms = int((now - state.window_detected_at) * 1000)
                    if elapsed_ms < pop_up_delays:
                        _debug(
                            f"Salvage choice window open for item={item_name} [{item_id}], "
                            f"waiting {elapsed_ms}/{pop_up_delays} ms before selecting mode={mode.name}."
                        )
                        return BehaviorTree.NodeState.RUNNING
                    if UIManagerExtensions.SalvageOptionsWindow.SelectOption(mode):
                        UIManagerExtensions.SalvageOptionsWindow.Confirm()
                        state.confirm_clicked_at = now
                        state.window_detected_at = 0.0
                        _debug(f"Selected salvage option {mode.name} for item={item_name} [{item_id}].")
                        return BehaviorTree.NodeState.RUNNING
                    else:
                        _debug(f"Failed to select salvage option {mode.name} for item={item_name} [{item_id}]; cancelling.", Py4GW.Console.MessageType.Warning)
                        state.window_detected_at = 0.0
                        UIManagerExtensions.SalvageOptionsWindow.Cancel()
                        return BehaviorTree.NodeState.FAILURE

                if state.window_detected_at:
                    state.window_detected_at = 0.0

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
                    and not salvage_window_open
                    and (now - confirm_clicked_at) >= 0.20
                )
                
                time_since_confirm = (now - confirm_clicked_at) * 1000 if confirm_clicked_at > 0.0 else None
                if time_since_confirm is not None and time_since_confirm < pop_up_delays:
                    _debug(
                        f"Salvage confirm clicked for item={item_name} [{item_id}] but waiting for windows to close..."
                        f"Elapsed since confirm: {int(time_since_confirm)} ms."
                    )
                    return BehaviorTree.NodeState.RUNNING
                
                if salvage_window_open:
                    _debug(
                        f"Waiting for salvage-related windows to close for item={item_name} [{item_id}] "
                        f"before restarting or finishing salvage."
                    )
                    return BehaviorTree.NodeState.RUNNING

                if not item_gone and item.is_stackable and qty_changed and current_qty > desired_qty:
                    _debug(
                        f"Partial salvage item={item_name} [{item_id}]: initial_qty={initial_qty}, current_qty={current_qty}, "
                        f"desired_qty={desired_qty}. Restarting for remaining quantity."
                    )
                    state.salvage_started_at = 0.0
                    state.initial_qty = item.quantity
                    
                    return BehaviorTree.NodeState.RUNNING

                if qty_changed or item_gone or windows_closed_after_confirm or mod_salvaged:
                    _debug(
                        f"Salvage complete item={item_name} [{item_id}] mode={mode.name} "
                        f"qty_changed={qty_changed} item_gone={item_gone} "
                        f"windows_closed_after_confirm={windows_closed_after_confirm} mod_salvaged={mod_salvaged} "
                        f"initial_qty={initial_qty} current_qty={current_qty} desired_qty={desired_qty}."
                    )
                    return BehaviorTree.NodeState.SUCCESS

                if (now - float(state.salvage_started_at)) * 1000 >= timeout_ms_per_item:
                    cancelled_window = False
                    if salvage_window_open:
                        cancelled_window = UIManagerExtensions.CancelAnySalvageRelatedWindow()
                    _debug(
                        f"Timeout item={item_name} [{item_id}] mode={mode.name} after {timeout_ms_per_item} ms. "
                        f"initial_qty={initial_qty} current_qty={current_qty} desired_qty={desired_qty} "
                        f"confirm_clicked_at={confirm_clicked_at:.3f} "
                        f"windows={{salvage:{UIManagerExtensions.SalvageOptionsWindow.IsOpen()}, "
                        f"lesser_confirm:{UIManagerExtensions.LesserSalvageWindow.IsOpen()}, "
                        f"material_confirm:{UIManagerExtensions.SalvageConfirmationPopup.IsOpen()}, "
                        f"unidentified:{UIManagerExtensions.ExpertSalvageUnidentifiedWindow.IsOpen()}}} "
                        f"cancelled_window={cancelled_window} "
                        f"free_slots={Inventory.GetFreeSlotCount()}.",
                        Py4GW.Console.MessageType.Warning,
                    )
                    node.blackboard.pop(state_key, None)
                    return BehaviorTree.NodeState.FAILURE

                _debug(
                    f"Waiting item={item_name} [{item_id}] mode={mode.name} "
                    f"elapsed_ms={int((now - float(state.salvage_started_at)) * 1000)} "
                    f"initial_qty={initial_qty} current_qty={current_qty} desired_qty={desired_qty} "
                    f"confirm_clicked_at={confirm_clicked_at:.3f} "
                )
                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree.ActionNode(name="Items.SalvageItems", action_fn=_salvage, aftercast_ms=aftercast_ms)

        class ItemTransferInstructions:
            """
            Internal transfer-plan entry describing how much item quantity should move into one destination slot.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal Item Transfer Instructions
              Purpose: Represent one target bag-slot destination and the item quantities that should be moved there.
              UserDescription: Internal support helper class.
              Notes: Used by storage and inventory transfer planning helpers before actual move actions are issued.
            """
            def __init__(self, bag: Bags, slot: int, stack_item: Optional[ItemSnapshot], available_space: int = MAX_STACK_SIZE):                
                """
                Initialize a transfer instruction for one destination slot.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Item Transfer Instructions Initializer
                  Purpose: Set up destination bag, slot, stack context, and available space for item transfer planning.
                  UserDescription: Internal support routine.
                  Notes: Available space is reduced automatically when the destination already contains a partial stack.
                """
                self.bag = bag
                self.slot = slot
                self.stack_item = stack_item                
                self.available_space = available_space - stack_item.quantity if stack_item and stack_item.is_stackable else available_space
                
                self.items : list[tuple[ItemSnapshot, int]] = []

        @staticmethod
        def _get_material_storage_capacity(material_storage_snapshot: dict[int, Optional[ItemSnapshot]]) -> int:
            capacity = (
                max(
                    (item.quantity for item in material_storage_snapshot.values() if item),
                    default=0,
                )
                + MAX_STACK_SIZE
                - 1
            ) // MAX_STACK_SIZE * MAX_STACK_SIZE

            return capacity if capacity > 0 else MAX_STACK_SIZE

        @staticmethod
        def _cleanup_empty_transfer_instruction(
            moving_instructions: dict[Bags, dict[int, "BTNodes.Items.ItemTransferInstructions"]],
            bag: Bags,
            slot: int,
        ) -> None:
            bag_instructions = moving_instructions.get(bag)
            if not bag_instructions:
                return

            instruction = bag_instructions.get(slot)
            if instruction is not None and not instruction.items:
                bag_instructions.pop(slot, None)

            if not bag_instructions:
                moving_instructions.pop(bag, None)

        @staticmethod
        def _get_planned_transfer_item_ids(
            moving_instructions: dict[Bags, dict[int, "BTNodes.Items.ItemTransferInstructions"]],
        ) -> list[int]:
            planned_item_ids: list[int] = []
            seen_item_ids: set[int] = set()

            for bag_instructions in moving_instructions.values():
                for instruction in bag_instructions.values():
                    for item, _ in instruction.items:
                        if item.id in seen_item_ids:
                            continue

                        seen_item_ids.add(item.id)
                        planned_item_ids.append(item.id)

            return planned_item_ids

        @staticmethod
        def _format_transfer_destination(bag: Bags, slot: int) -> str:
            if bag == Bags.MaterialStorage:
                return f"Material Storage slot {slot}"

            return f"bag {bag.name} slot {slot}"

        @staticmethod
        def _get_planned_destinations_for_item(
            moving_instructions: dict[Bags, dict[int, "BTNodes.Items.ItemTransferInstructions"]],
            item_id: int,
        ) -> list[str]:
            destinations: list[str] = []

            for bag, bag_instructions in moving_instructions.items():
                for slot, instruction in bag_instructions.items():
                    qty_for_item = sum(qty for planned_item, qty in instruction.items if planned_item.id == item_id)
                    if qty_for_item <= 0:
                        continue

                    destinations.append(
                        f"{qty_for_item} to {BTNodes.Items._format_transfer_destination(bag, slot)}"
                    )

            return destinations

        @staticmethod
        def _move_item_to_transfer_destination(
            item: ItemSnapshot,
            destination: "BTNodes.Items.ItemTransferInstructions",
            quantity: int,
            log_category: str,
        ) -> None:
            target_bag = Bags.MaterialStorage if destination.bag == Bags.MaterialStorage else destination.bag.value
            Inventory.MoveItem(item.id, target_bag, destination.slot, quantity)
            Py4GW.Console.Log(
                log_category,
                f"Moving {quantity} of '{item.names.plain}' (ID: {item.id}) to {BTNodes.Items._format_transfer_destination(destination.bag, destination.slot)}",
            )
        
        @staticmethod
        def GetTransferInstructions(
            item_ids: list[int],
            target : list[Bags],
            quantities: Optional[list[int]] = None,
            fill_materials_first: bool = False,
            log_plans: bool = False,
        ) -> dict[Bags, dict[int, BTNodes.Items.ItemTransferInstructions]]:
            """
            Build a destination-slot transfer plan for moving items into target bags.

            Meta:
              Expose: true
              Audience: advanced
              Display: Get Transfer Instructions
              Purpose: Compute a bag-slot transfer plan that minimizes fragmentation and respects stack rules.
              UserDescription: Use this when you need a planning step that figures out where item quantities should move before issuing inventory actions.
              Notes: Supports inventory-to-storage and storage-to-inventory planning, including optional material-storage prefill behavior.
            """
            to_inventory = any(bag in INVENTORY_BAGS for bag in target)
            to_storage = any(bag in STORAGE_BAGS or bag == Bags.MaterialStorage for bag in target)
           
            material_storage_snapshot = ItemSnapshot.get_bag_snapshot(Bags.MaterialStorage) if to_storage else {}
            target_snapshot = ItemSnapshot.get_bags_snapshot(target)
            moving_instructions : dict[Bags, dict[int, BTNodes.Items.ItemTransferInstructions]] = {}
            
            material_storage_capacity = BTNodes.Items._get_material_storage_capacity(material_storage_snapshot)
                                            
            for index, item_id in enumerate(item_ids):
                item = ItemSnapshot.from_item_id(item_id)
                qty = quantities[index] if quantities and index < len(quantities) else item.quantity if item else 0
                requested_qty = qty
                item_is_inventory = item.is_inventory_item if item is not None else False
                item_is_storage = item.is_storage_item if item is not None else False
                
                if (
                    not item
                    or not item.is_valid
                    or (item_is_inventory and to_inventory)
                    or (item_is_storage and to_storage)
                    or (not item_is_inventory and not item_is_storage)
                ):
                    continue

                def _plan_into_destination(
                    dest_bag: Bags,
                    dest_slot: int,
                    stack_item: Optional[ItemSnapshot],
                    available_space: int,
                ) -> None:
                    nonlocal qty
                    if qty <= 0:
                        return

                    moving_instructions.setdefault(dest_bag, {})
                    dest = moving_instructions[dest_bag].setdefault(
                        dest_slot,
                        BTNodes.Items.ItemTransferInstructions(dest_bag, dest_slot, stack_item, available_space=available_space),
                    )

                    if dest.available_space <= 0:
                        return

                    qty_to_move = min(dest.available_space, qty)
                    if qty_to_move <= 0:
                        return

                    dest.available_space -= qty_to_move
                    if item is not None:
                        dest.items.append((item, qty_to_move))
                    
                    qty -= qty_to_move
                
                if item.is_stackable:
                    material_slot = MATERIAL_STORAGE_SLOTS.get(item.model_id)
                    if fill_materials_first and item_is_inventory and (item.is_material or item.is_rare_material) and material_slot is not None:
                        stack_item = material_storage_snapshot.get(material_slot)
                        if stack_item is None or not stack_item.is_valid or stack_item.same_kind_as(item):
                            _plan_into_destination(
                                Bags.MaterialStorage,
                                material_slot,
                                stack_item,
                                material_storage_capacity,
                            )
                        
                    # get all items with the same model and type that have free space in their stacks and add them as potential destinations for the current item until we have found enough space for the whole stack. This way we minimize fragmentation in the bank and maximize the chances of fitting all items. We get them all from bag_enum, bag in inventory_snapshot.items()
                    stacks_of_same_kind_with_space = [(i, bag_id) for bag_id, bag in target_snapshot.items() for i in bag.values() if i and i.is_valid and i.is_stackable and i.same_kind_as(item) and i.quantity < MAX_STACK_SIZE]
                    
                    #sorted by least free space to most free space to fill up more full stacks first, then by bag and slot, so we fill from the beginning of the bank to the end to minimize fragmentation
                    stacks_of_same_kind_with_space.sort(key=lambda x: (-x[0].quantity, x[1].value, x[0].slot))
                    
                    for stack_item, bag in stacks_of_same_kind_with_space:
                        if stack_item.quantity >= MAX_STACK_SIZE or (bag == Bags.MaterialStorage and stack_item.slot == material_slot):
                            continue

                        stack_capacity = material_storage_capacity if bag == Bags.MaterialStorage else MAX_STACK_SIZE
                        _plan_into_destination(bag, stack_item.slot, stack_item, stack_capacity)

                        if qty <= 0:
                            break
                    
                if qty > 0:
                    for bag_enum, bag in target_snapshot.items():
                        for slot, stack_item in bag.items():
                            if stack_item is None:
                                available_space = material_storage_capacity if bag_enum == Bags.MaterialStorage else (MAX_STACK_SIZE if item.is_stackable else 1)
                                _plan_into_destination(bag_enum, slot, None, available_space)
                                                                
                                if qty <= 0:
                                    break
                        
                        if qty <= 0:
                            break

                planned_qty = requested_qty - qty
                destinations = BTNodes.Items._get_planned_destinations_for_item(moving_instructions, item.id)
                destination_text = ", ".join(destinations) if destinations else "no destination"

                if log_plans:
                    if planned_qty <= 0:
                        Py4GW.Console.Log(
                            "GetTransferInstructions",
                            f"Could not plan a move for '{item.names.plain}' (ID: {item.id}).",
                        )
                    elif planned_qty < requested_qty:
                        Py4GW.Console.Log(
                            "GetTransferInstructions",
                            f"Planned partial move of {planned_qty}/{requested_qty} for '{item.names.plain}' (ID: {item.id}).\n{destination_text}.",
                        )
                        
                    elif planned_qty == requested_qty:
                        Py4GW.Console.Log(
                            "GetTransferInstructions",
                            f"Planned to move {requested_qty} of '{item.names.plain}' (ID: {item.id}).\n{destination_text}.",
                        )
                
            return moving_instructions            
        
        @staticmethod
        def DepositItems(
            item_ids: list[int],
            target : list[Bags] = STORAGE_BAGS,
            anniversary_panel: bool = False,
            fill_materials_first: bool = True,
            fail_if_no_space: bool = True,
            aftercast_ms: int = 25,
            precomputed_instructions: Optional[dict[Bags, dict[int, "BTNodes.Items.ItemTransferInstructions"]]] = None,
        ):
            """
            Build an action node that deposits items into storage bags using transfer planning.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Deposit Items
              Purpose: Move inventory items into storage according to computed transfer instructions.
              UserDescription: Use this when you want a BT step that deposits known items into storage automatically.
              Notes: Can optionally fail when no valid storage destination exists and supports anniversary-panel bag filtering.
            """
            if not anniversary_panel and Bags.Storage14 in target:
                target = [b for b in target if b != Bags.Storage14]
            
            def _deposit(node: BehaviorTree.Node):
                instructions = precomputed_instructions if precomputed_instructions is not None else BTNodes.Items.GetTransferInstructions(item_ids, target, fill_materials_first=fill_materials_first)
                moved_any = False
                
                if not instructions:
                    return BehaviorTree.NodeState.FAILURE if fail_if_no_space else BehaviorTree.NodeState.SUCCESS
                
                for bag in instructions.values():
                    for dest in bag.values():
                        for item, qty in dest.items:
                            BTNodes.Items._move_item_to_transfer_destination(item, dest, qty, node.name)
                            moved_any = True
                
                return BehaviorTree.NodeState.SUCCESS if moved_any else BehaviorTree.NodeState.FAILURE

            return BehaviorTree.ActionNode(name="Items.DepositItems", action_fn=_deposit, aftercast_ms=aftercast_ms)

        @staticmethod
        def GetDepositableItemIds(
            item_ids: list[int],
            target: list[Bags] = STORAGE_BAGS,
            fill_materials_first: bool = True,
            anniversary_panel: bool = False,
            log_plans: bool = False,
        ) -> list[int]:
            if not anniversary_panel and Bags.Storage14 in target:
                target = [b for b in target if b != Bags.Storage14]

            instructions = BTNodes.Items.GetTransferInstructions(
                item_ids,
                target,
                fill_materials_first=fill_materials_first,
                log_plans=log_plans,
            )

            return BTNodes.Items._get_planned_transfer_item_ids(instructions)
        
        @staticmethod
        def WithdrawItems(
            item_ids: list[int],
            target : list[Bags] = INVENTORY_BAGS,
            fill_materials_first: bool = True,
            fail_if_no_space: bool = True,
            aftercast_ms: int = 25,
        ):                   
            """
            Build an action node that withdraws items from storage into inventory using transfer planning.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Withdraw Items
              Purpose: Move storage items into inventory according to computed transfer instructions.
              UserDescription: Use this when you want a BT step that pulls known items from storage automatically.
              Notes: Can optionally fail when no valid inventory destination exists.
            """
            def _withdraw(node: BehaviorTree.Node):
                instructions = BTNodes.Items.GetTransferInstructions(item_ids, target, fill_materials_first=fill_materials_first)
                moved_any = False
                
                if not instructions:
                    return BehaviorTree.NodeState.FAILURE if fail_if_no_space else BehaviorTree.NodeState.SUCCESS
                
                for bag in instructions.values():
                    for dest in bag.values():
                        for item, qty in dest.items:
                            BTNodes.Items._move_item_to_transfer_destination(item, dest, qty, node.name)
                            moved_any = True
                
                return BehaviorTree.NodeState.SUCCESS if moved_any else BehaviorTree.NodeState.FAILURE

            return BehaviorTree.ActionNode(name="Items.WithdrawItems", action_fn=_withdraw, aftercast_ms=aftercast_ms)

    class Bags:
        """
        BT helper group for bag-level restocking, material fill, compaction, and sorting flows.

        Meta:
          Expose: true
          Audience: advanced
          Display: Bags
          Purpose: Group BT helper routines that reorganize or refill inventory and storage bags.
          UserDescription: Built-in BT helper group for bag maintenance and organization routines.
          Notes: These routines typically operate on bag snapshots and issue multiple move actions per execution.
        """
        @staticmethod
        def Restock(
            model_id: int,
            item_type: ItemType,
            quantity: int,
        ):
            """
            Build an action node that restocks inventory from storage bags.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Restock Bags
              Purpose: Move enough storage items into inventory to reach a target quantity.
              UserDescription: Use this when you want a BT step that refills inventory stock from storage rather than from a merchant.
              Notes: Fails when matching storage items cannot be found or no valid transfer destinations exist.
            """
            def _restock(node: BehaviorTree.Node):        
                inventory_snapshot = ItemSnapshot.get_inventory_snapshot(Bags.Backpack, Bags.Bag2)
                current_qty = sum(i.quantity for bag in inventory_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.model_id == model_id and i.item_type == item_type) if inventory_snapshot else 0
                left_to_restock = max(0, quantity - current_qty)
                
                if left_to_restock <= 0:
                    return BehaviorTree.NodeState.SUCCESS
                
                storage_snapshot = ItemSnapshot.get_bags_snapshot(STORAGE_BAGS)
                desired_items = [i for bag in storage_snapshot.values() for i in bag.values() if i is not None and i.is_valid and i.model_id == model_id and i.item_type == item_type] if storage_snapshot else []
                
                if not desired_items:
                    return BehaviorTree.NodeState.FAILURE
                
                item_ids = []
                quantities = []
                
                sort_by_lowest_qty = sorted(desired_items, key=lambda i: i.quantity)
                for item in sort_by_lowest_qty:
                    if item.quantity <= 0:
                        continue
                    
                    has_space, space_for_qty = HasSpaceForItem(item.id, Bags.Backpack, Bags.Bag2, quantity=item.quantity)
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
                            BTNodes.Items._move_item_to_transfer_destination(item, dest, qty, node.name)

                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.ActionNode(name="Bags.Restock", action_fn=_restock)
        
        @staticmethod
        def FillMaterialStorage(
            source : list[Bags] = STORAGE_BAGS,
            aftercast_ms: int = 150,
            succeed_if_already_filled: bool = True,
        ):
            """
            Build an action node that fills material storage from the provided source bags.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Fill Material Storage
              Purpose: Move stackable material items into their material-storage slots.
              UserDescription: Use this when you want a BT step that consolidates materials into material storage automatically.
              Notes: Succeeds when any move is made or, optionally, when the storage is already effectively full.
            """
            def _fill_material_storage(node: BehaviorTree.Node):
                source_bags = [bag for bag in source if bag != Bags.MaterialStorage]
                if not source_bags:
                    return BehaviorTree.NodeState.FAILURE

                source_snapshot = ItemSnapshot.get_bags_snapshot(source_bags)
                material_snapshot = ItemSnapshot.get_bag_snapshot(Bags.MaterialStorage)

                material_storage_capacity = (
                    max((item.quantity for item in material_snapshot.values() if item), default=0) + MAX_STACK_SIZE - 1
                ) // MAX_STACK_SIZE * MAX_STACK_SIZE
                if material_storage_capacity <= 0:
                    material_storage_capacity = MAX_STACK_SIZE

                moved_any = False
                transfer_instructions: dict[int, BTNodes.Items.ItemTransferInstructions] = {}
                bag_item_map : dict[int, Bags] = {item_id: bag for bag, bag_items in source_snapshot.items() for item_id, item in bag_items.items() if item}
                
                for _, bag_items in source_snapshot.items():
                    for _, item in bag_items.items():
                        if item is None or not item.is_valid or not item.is_stackable or bag_item_map.get(item.id) == Bags.MaterialStorage:
                            continue
                        
                        if not (item.is_material or item.is_rare_material):
                            continue
                        
                        slot = MATERIAL_STORAGE_SLOTS.get(item.model_id, None)
                        if slot is None:
                            continue
                        
                        material = material_snapshot.get(slot, None)
                        transfer_instructions.setdefault(slot, BTNodes.Items.ItemTransferInstructions(Bags.MaterialStorage, slot, material, available_space=material_storage_capacity))
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
                        BTNodes.Items._move_item_to_transfer_destination(item, dest, qty, node.name)
                        moved_any = True

                return BTNodes._success_if(moved_any or succeed_if_already_filled)

            return BehaviorTree.ActionNode(name="Inventory.FillMaterialStorage", action_fn=_fill_material_storage, aftercast_ms=aftercast_ms)
        
        @staticmethod
        def _get_default_sort_item_type_order() -> list[int]:
            item_type_order = [
                int(ItemType.Kit),
                int(ItemType.Key),
                int(ItemType.Usable),
                int(ItemType.Trophy),
                int(ItemType.Quest_Item),
                int(ItemType.Materials_Zcoins),
            ]
            item_type_order += [int(item_type) for item_type in ItemType if int(item_type) not in item_type_order]
            return item_type_order

        @staticmethod
        def GetPlannedBagLayout(
            bags: list[Bags] = INVENTORY_BAGS,
        ) -> dict[Bags, dict[int, Optional[ItemSnapshot]]]:
            """
            Build the planned bag layout for the current default sort order without moving items.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Get Planned Bag Layout
              Purpose: Compute the target bag-slot layout that Sort Bags would currently try to produce.
              UserDescription: Use this when you want to inspect or compare the default planned bag arrangement before executing it.
              Notes: Returns a slot map using the current live snapshot and the same ordering rules as Sort Bags.
            """
            snapshot = ItemSnapshot.get_bags_snapshot(bags)
            item_type_order = BTNodes.Bags._get_default_sort_item_type_order()

            ordered_slots: list[tuple[Bags, int]] = []
            planned_layout: dict[Bags, dict[int, Optional[ItemSnapshot]]] = {}

            for bag in bags:
                planned_layout[bag] = {}
                for slot in sorted(snapshot.get(bag, {}).keys()):
                    ordered_slots.append((bag, slot))
                    planned_layout[bag][slot] = None

            items = [
                item
                for bag in bags
                for _, item in sorted(snapshot.get(bag, {}).items())
                if item is not None and item.is_valid
            ]
            sorted_items = sorted(
                items,
                key=lambda item: (
                    item.item_type == ItemType.Unknown,
                    item_type_order.index(item.item_type),
                    item.model_id,
                    -item.rarity.value,
                    -item.quantity,
                    -item.value,
                    item.color.value,
                    item.id,
                ),
            )

            for index, item in enumerate(sorted_items):
                if index >= len(ordered_slots):
                    break

                bag, slot = ordered_slots[index]
                planned_layout[bag][slot] = item

            return planned_layout

        @staticmethod
        def CompactBags(
            bags : list[Bags] = INVENTORY_BAGS,         
            aftercast_ms: int = 150,
        ):
            """
            Build an action node that merges partial stacks across bags.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Compact Bags
              Purpose: Reduce stack fragmentation by combining partial stacks of matching items.
              UserDescription: Use this when you want a BT step that tidies bag stacks and frees space.
              Notes: Operates only on stackable items and succeeds only if at least one move is performed.
            """
            def _compact(node: BehaviorTree.Node):
                snapshot = ItemSnapshot.get_bags_snapshot(bags)
                grouped_items : dict[tuple[ItemType, int, int], list[tuple[Bags, int, ItemSnapshot]]] = {}
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
            bags : list[Bags] = INVENTORY_BAGS,         
            aftercast_ms: int = 150,
        ):
            """
            Build an action node that sorts items across bags using the current default sort order.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Sort Bags
              Purpose: Reorder bag contents according to the current item-type and value-based sorting rules.
              UserDescription: Use this when you want a BT step that applies the current default bag sort order.
              Notes: The sort configuration is still marked as provisional in the implementation comments.
            """
            def _sort(node: BehaviorTree.Node):
                planned_layout = BTNodes.Bags.GetPlannedBagLayout(bags)
                moved_any = False

                for bag in bags:
                    for slot, planned_item in sorted(planned_layout.get(bag, {}).items()):
                        if planned_item is None or not planned_item.is_valid:
                            continue

                        if planned_item.bag == bag and planned_item.slot == slot:
                            continue

                        Inventory.MoveItem(planned_item.id, bag.value, slot, planned_item.quantity)
                        moved_any = True

                return BTNodes._success_if(moved_any)

            return BehaviorTree.ActionNode(name="Inventory.SortBags", action_fn=_sort, aftercast_ms=aftercast_ms)

    class Crafting:
        """
        BT helper group for crafter recipe execution flows.

        Meta:
          Expose: true
          Audience: advanced
          Display: Crafting
          Purpose: Group BT helper routines that issue crafter recipe actions.
          UserDescription: Built-in BT helper group for crafting actions.
          Notes: These routines expect the relevant crafting context to already be open and valid.
        """
        @staticmethod
        def CraftItem(
            output_item_id: int,
            cost: int,
            material_item_ids: list[int],
            material_quantities: list[int],
            aftercast_ms: int = 250,
        ):
            """
            Build an action node that crafts one item recipe.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Craft Item
              Purpose: Issue one crafter recipe request with the provided material ids and quantities.
              UserDescription: Use this when you want a BT step that crafts one configured recipe.
              Notes: Fails when the output item id is invalid or the recipe input arrays are empty.
            """
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
            """
            Build an action node that crafts several recipes in one pass.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Craft Items
              Purpose: Iterate over several recipe definitions and issue crafting requests for each valid one.
              UserDescription: Use this when you want a BT step that crafts multiple configured recipes.
              Notes: Succeeds only if at least one recipe is valid and gets crafted.
            """
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
