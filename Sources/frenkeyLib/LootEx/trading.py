from datetime import datetime
from enum import Enum
import math
from typing import Callable, Generator

from Py4GW import Console
from PyItem import PyItem

from Py4GWCoreLib import Merchant
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.Merchant import Trading
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Sources.frenkeyLib.LootEx import utility
from Sources.frenkeyLib.LootEx.cache import Cached_Item
from Sources.frenkeyLib.LootEx.enum import MAX_CHARACTER_GOLD, MAX_VAULT_GOLD, ActionState, MerchantType
from Sources.frenkeyLib.LootEx.models import Ingredient

DEBUG_TRADING = False
class ActionType(Enum):
    Buy = 1
    Sell = 2

class TraderCoroutine:
    def __init__(self, generator_fn: Callable[[], Generator], timeout_seconds: float = 5.0):
        self.generator_fn = generator_fn
        self.generator = None
        self.state = ActionState.Pending
        self.started_at = datetime.min
        # self.timeout_seconds = timeout_seconds

    def step(self) -> ActionState:
        """
        Advances the coroutine by one 'yield'.
        Returns its current state.
        """
        # Start coroutine if not running yet
        if self.state == ActionState.Pending:
            self.generator = self.generator_fn()
            self.state = ActionState.Running
            self.started_at = datetime.now()

        # # Timeout?
        # if (datetime.now() - self.started_at).total_seconds() > self.timeout_seconds:
        #     self.state = ActionState.Timeout
        #     return self.state

        # Advance generator one step
        try:
            if self.generator is not None:
                next(self.generator)
                return self.state  # still Running
            
            else:
                self.state = ActionState.Completed
                return self.state

        except StopIteration:
            self.state = ActionState.Completed
            return self.state

        except Exception as e:
            ConsoleLog("LootEx", f"Coroutine error: {e}", Console.MessageType.Error)
            self.state = ActionState.Timeout
            return self.state
            
class TraderAction:
    def __init__(self, item: Cached_Item, trader_type: MerchantType, action: ActionType, desired_quantity: int = -1):
        self.item = item
        self.action = action
        self.trader_type = trader_type
        self.price: int = -1
        self.initial_quantity: int = item.quantity if action == ActionType.Sell else Inventory.GetModelCount(item.model_id)
        self.is_item_valid: bool = True

        # Determine target quantity
        if desired_quantity == -1:
            # Sell until zero
            # Buy until 1
            self.desired_quantity = 0 if action == ActionType.Sell else 1
        else:
            self.desired_quantity = desired_quantity

        self.coroutine: TraderCoroutine | None = None

    # Entry point
    def run(self) -> TraderCoroutine:
        return TraderCoroutine(self._gen_main)

    # Main generator function
    def _gen_main(self) -> Generator:
        """
        Loop until quantity objective is reached:
        - For Buy: item.quantity >= desired_quantity
        - For Sell: item.quantity <= desired_quantity
        """
        ConsoleLog(
            "LootEx",
            f"Starting TraderAction for {self.item.name} ({self.item.id}), "
            f"mode={self.action.name}, desired={self.desired_quantity}, initial={self.initial_quantity}",
            Console.MessageType.Info,
                    DEBUG_TRADING
        )

        while not self._is_done():
            yield from self._request_price()
            yield from self._wait_for_price()
            yield from self._execute_trade()
            yield from self._confirm_trade()

    # Condition to stop the trading action
    def _is_done(self) -> bool:
        self._update_item()
        
        if not self.is_item_valid:
            ConsoleLog(
                "LootEx",
                f"Item {self.item.name} ({self.item.id}) is no longer valid. Ending TraderAction.",
                Console.MessageType.Warning,
                    DEBUG_TRADING
            )
            return True
        
        q = self.item.quantity if self.action == ActionType.Sell else Inventory.GetModelCount(self.item.model_id)
        
        current_gold = Inventory.GetGoldOnCharacter()
        vault_gold = Inventory.GetGoldInStorage()
        
        if self.action == ActionType.Buy and self.price > current_gold:
            if vault_gold + current_gold >= self.price:
                ConsoleLog(
                    "LootEx",
                    f"Withdrawing gold from vault to buy {self.item.name} ({self.item.id}). Current gold: {utility.Util.format_currency(current_gold)}, vault gold: {utility.Util.format_currency(vault_gold)}, needed: {utility.Util.format_currency(self.price)}.",
                    Console.MessageType.Info
                )
                Inventory.WithdrawGold(min((self.price * self.desired_quantity) - current_gold + 1000, MAX_CHARACTER_GOLD - current_gold, vault_gold))
                return False
            
            ConsoleLog(
                "LootEx",
                f"Not enough gold to buy {self.item.name} ({self.item.id}). Current gold: {utility.Util.format_currency(current_gold)}, needed: {utility.Util.format_currency(self.price)}. Ending TraderAction.",
                Console.MessageType.Warning
            )
            
            return True
        
        if self.action == ActionType.Sell and current_gold + self.price > MAX_CHARACTER_GOLD:
            if vault_gold < MAX_VAULT_GOLD:
                ConsoleLog(
                    "LootEx",
                    f"Depositing gold to vault to sell {self.item.name} ({self.item.id}). Current gold: {utility.Util.format_currency(current_gold)}, vault gold: {utility.Util.format_currency(vault_gold)}, after sell: {utility.Util.format_currency(current_gold + self.price)}.",
                    Console.MessageType.Info
                )
                gold_to_deposit = min(math.floor(current_gold / 1000) * 1000, MAX_VAULT_GOLD - vault_gold)
                ConsoleLog(
                    "LootEx",
                    f"Depositing {utility.Util.format_currency(gold_to_deposit)} to vault.",
                    Console.MessageType.Info
                )
                
                Inventory.DepositGold(gold_to_deposit)
                return False
            
            ConsoleLog(
                "LootEx",
                f"Selling {self.item.name} ({self.item.id}) would exceed max gold limit. Current gold: {utility.Util.format_currency(current_gold)}, after sell: {utility.Util.format_currency(current_gold + self.price)}. Ending TraderAction.",
                Console.MessageType.Warning
            )
            return True
              
        # BUY MODE
        if self.action == ActionType.Buy:
            return q >= self.desired_quantity

        # SELL MODE
        if self.item.common_material:
            # cannot stop mid-stack, must stop when <= target
            return q < 10 or q <= self.desired_quantity

        # normal items
        return q <= self.desired_quantity

    # Request a price quote from the merchant
    def _request_price(self) -> Generator:             
        self._update_item()
        
        if not self.is_item_valid:
            ConsoleLog(
                "LootEx",
                f"Item {self.item.name} ({self.item.id}) is no longer valid. Cannot execute trade.",
                Console.MessageType.Warning,
                    DEBUG_TRADING
            )
            return
    
        if self.action == ActionType.Sell and self.item.common_material and self.item.quantity < 10:
            return 
        
        msg = "Requesting quote for buying" if self.action == ActionType.Buy else "Requesting quote for selling"

        ConsoleLog(
            "LootEx",
            f"{msg} {self.item.name} ({self.item.id})",
            Console.MessageType.Info,
                    DEBUG_TRADING
        )

        if self.action == ActionType.Buy:
            Trading.Trader.RequestQuote(self.item.id)
        else:
            Trading.Trader.RequestSellQuote(self.item.id)

        self._start_quote_time = datetime.now()
        yield

    # Wait until we receive a price quote
    def _wait_for_price(self) -> Generator:
        while True:     
            self._update_item()
            if not self.is_item_valid:
                ConsoleLog(
                    "LootEx",
                    f"Item {self.item.name} ({self.item.id}) is no longer valid. Cannot execute trade.",
                    Console.MessageType.Warning
                )
                return
            
            if self.action == ActionType.Sell and self.item.common_material and self.item.quantity < 10:
                return 
            
            quoted_id = Trading.Trader.GetQuotedItemID()
            quoted_value = Trading.Trader.GetQuotedValue()

            if quoted_id == self.item.id and quoted_value >= 0:
                self.price = quoted_value
                ConsoleLog(
                    "LootEx",
                    f"Received quote {quoted_value} for {self.item.name}",
                    Console.MessageType.Info,
                    DEBUG_TRADING
                )
                return

            if (datetime.now() - self._start_quote_time).total_seconds() > 1.0:
                ConsoleLog(
                    "LootEx",
                    f"Quote timeout — requesting new quote for {self.item.name}",
                    Console.MessageType.Warning,
                    DEBUG_TRADING
                )
                if self.action == ActionType.Buy:
                    Trading.Trader.RequestQuote(self.item.id)
                else:
                    Trading.Trader.RequestSellQuote(self.item.id)

                self._start_quote_time = datetime.now()

            yield

    # Execute the trade at the quoted price
    def _execute_trade(self) -> Generator:        
        self._update_item()
        if not self.is_item_valid:
            ConsoleLog(
                "LootEx",
                f"Item {self.item.name} ({self.item.id}) is no longer valid. Cannot execute trade.",
                Console.MessageType.Warning
            )
            return
    
        if self.action == ActionType.Sell and self.item.common_material and self.item.quantity < 10:
            return 
        
        ConsoleLog(
            "LootEx",
            f"Executing {self.action.name} for {self.item.name} at price {self.price}",
            Console.MessageType.Info,
                    DEBUG_TRADING
        )

        if self.action == ActionType.Buy:
            Trading.Trader.BuyItem(self.item.id, self.price)
        else:
            Trading.Trader.SellItem(self.item.id, self.price)

        self._start_trade_time = datetime.now()
        yield
        
    # Update item validity and quantity
    def _update_item(self) -> None:
        item = PyItem(self.item.id)
        self.is_item_valid = item.IsItemValid(self.item.id) and (self.action is not ActionType.Sell or item.is_inventory_item) if item else False
        self.item.quantity = 0 if not self.is_item_valid else item.quantity

    # Confirm that the trade has completed
    def _confirm_trade(self) -> Generator:
        """
        We watch the item's quantity and wait until it changes.
        Then the trade has completed.
        """
        
        if self.action == ActionType.Sell and self.item.common_material and self.item.quantity < 10:
            return 
        
        if  self.action == ActionType.Sell:
            start = datetime.now()

            while True:           
                
                self._update_item()
                
                if self.item.quantity != self.initial_quantity:
                    ConsoleLog(
                        "LootEx",
                        f"Trade confirmed: {self.item.name} quantity changed {self.initial_quantity} -> {self.item.quantity}",
                        Console.MessageType.Info,
                        DEBUG_TRADING
                    )
                    return

                if (datetime.now() - start).total_seconds() > 1.5:
                    ConsoleLog(
                        "LootEx",
                        f"Trade confirmation TIMEOUT for {self.item.name}",
                        Console.MessageType.Warning,
                        DEBUG_TRADING
                    )
                    return

                yield
                
        elif self.action == ActionType.Buy:
            start = datetime.now()

            while True:          
                self._update_item()
                
                if Inventory.GetModelCount(self.item.model_id) != self.initial_quantity:
                    self.initial_quantity = Inventory.GetModelCount(self.item.model_id)
                    return

                if (datetime.now() - start).total_seconds() > 1.5:
                    ConsoleLog(
                        "LootEx",
                        f"Trade confirmation TIMEOUT for {self.item.name}",
                        Console.MessageType.Warning,
                        DEBUG_TRADING
                    )
                    return

                yield

def add_ingredients_to_buy(all_ingredients: list[Ingredient]) -> None:
    from Sources.frenkeyLib.LootEx.inventory_handling import InventoryHandler
    from Sources.frenkeyLib.LootEx.settings import Settings
    from Sources.frenkeyLib.LootEx.data import Data
    
    data = Data()
    settings = Settings()
    inventory_handler = InventoryHandler()
    
    if not settings or not data or not settings.profile:
        return
        
    for ingredient in all_ingredients:
        if ingredient.item is None:
            ingredient.get_item_data()
        
        if ingredient.item is None:
            continue
        
        is_material = ingredient.item.item_type is ItemType.Materials_Zcoins          
        trader_type = MerchantType.RareMaterialTrader if is_material else MerchantType.Merchant
        
        if (is_material and ingredient.model_id in data.Common_Materials):
            trader_type = MerchantType.MaterialTrader
            
        offerd_items = Merchant.Trading.Trader.GetOfferedItems()
        merchant_item = next((Cached_Item(item_id) for item_id in offerd_items if Cached_Item(item_id).model_id == ingredient.model_id), None)
        if merchant_item is None:
            ConsoleLog("LootEx", f"Material {ingredient.item.name} is not offered by the merchant.", Console.MessageType.Warning)
            continue
        
        current_amount = Inventory.GetModelCountInMaterialStorage(ingredient.model_id) if settings.profile.include_storage_materials else 0
        current_amount += Inventory.GetModelCountInStorage(ingredient.model_id) if settings.profile.include_storage_materials else 0
        current_amount += Inventory.GetModelCount(ingredient.model_id)
        
        if current_amount >= ingredient.amount:
            continue                                                                    
            
        ConsoleLog("LootEx", f"Adding to trading queue: Buy {ingredient.amount - current_amount}x {ingredient.item.name}. Currently have {current_amount}.", Console.MessageType.Info)
        inventory_handler.trading_queue.append(TraderAction(merchant_item, trader_type, ActionType.Buy, ingredient.amount - current_amount))