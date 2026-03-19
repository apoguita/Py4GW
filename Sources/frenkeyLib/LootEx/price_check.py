from Py4GWCoreLib.Routines import Routines
from Sources.frenkeyLib.LootEx import enum
from Py4GWCoreLib import Item, Merchant, Console
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ActionQueueNode, ConsoleLog
from Py4GWCoreLib.enums import ItemType
from Sources.frenkeyLib.LootEx.cache import Cached_Item

from datetime import datetime
from typing import Callable, Generator, Optional

from Py4GW import Console

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Merchant import Trading
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Sources.frenkeyLib.LootEx.cache import Cached_Item
from Sources.frenkeyLib.LootEx.enum import ActionState


trader_queue = ActionQueueNode(175)
checked_items: list[str] = []
#TODO: Refactor to use Cached_Item and data models
#TODO: Change this to be a yield based generator to speed things up while keeping it clean and the UI responsive
class PriceCheck:
    @staticmethod 
    def get_material_prices_from_trader():
        from Sources.frenkeyLib.LootEx.data import Data
        data = Data()
        
        if not trader_queue.action_queue.is_empty():
            trader_queue.clear()
            ConsoleLog(
                "LootEx", "Trader queue is not empty, skipping item check.", Console.MessageType.Error)
            return

        checked_items.clear()
        items = Merchant.Trading.Trader.GetOfferedItems()
        if items is None:
            ConsoleLog(
                "LootEx", "No items found in merchant's inventory.", Console.MessageType.Error)
            return

        ConsoleLog(
            "LootEx", f"Checking {len(items)} items from the merchant's inventory for materials...", Console.MessageType.Info)
        ConsoleLog(
            "LootEx", f"This will take about {round(len(items) * 175 / 1000)} seconds.", Console.MessageType.Info)

        for item in items:
            Item.RequestName(item)

            def create_quotes_for_item(item):
                
                def request_quote_for_item(item):
                    Merchant.Trading.Trader.RequestQuote(item)

                def get_quote_for_item(item):
                    price = Merchant.Trading.Trader.GetQuotedValue()

                    if price is not None:
                        model_id = GLOBAL_CACHE.Item.GetModelID(item)
                        item_type = ItemType(GLOBAL_CACHE.Item.GetItemType(item)[0])
                        item_data = data.Items.get_item(item_type, model_id)
                        
                        if item_data is None:
                            ConsoleLog(
                                "LootEx", f"Item with model ID {model_id} not found in items data.", Console.MessageType.Error)
                            return None
                        
                        material = data.Materials.get(model_id, None)
                        
                        if material:
                            material.vendor_value = int(price / (10 if model_id in enum.COMMON_MATERIALS else 1))
                            material.vendor_updated = datetime.now()
                            data.Materials[model_id] = material
                            
                            data.SaveMaterials()

                            trader_queue.execute_next()
                            return price

                trader_queue.add_action(request_quote_for_item, item)
                trader_queue.add_action(get_quote_for_item, item)
                
            create_quotes_for_item(item)
        
    @staticmethod
    def get_expensive_runes_from_merchant(threshold: int = 1000, mark_to_sell : bool = False, profession: int | None = None) -> None:
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        from Sources.frenkeyLib.LootEx.data import Data
        data = Data()
        
        def format_currency(value: int) -> str:
            platinum = value // 1000
            gold = value % 1000

            parts = []
            if platinum > 0:
                parts.append(f"{platinum} platinum")
            if gold > 0 or platinum == 0:
                parts.append(f"{gold} gold")

            return " ".join(parts)

        if settings.profile is None:
            ConsoleLog(
                "LootEx", "No loot profile selected, skipping item check.", Console.MessageType.Error)
            return

        if not trader_queue.action_queue.is_empty():
            trader_queue.clear()
            ConsoleLog(
                "LootEx", "Trader queue is not empty, skipping item check.", Console.MessageType.Error)
            return

        checked_items.clear()
        item_ids = Merchant.Trading.Trader.GetOfferedItems()
        if item_ids is None:
            ConsoleLog(
                "LootEx", "No items found in merchant's inventory.", Console.MessageType.Error)
            return

        items = [Cached_Item(item_id) for item_id in item_ids]
        
        if profession is not None and profession != 0:
            ConsoleLog(
                "LootEx", f"Checking for runes and insignias for profession {profession}...", Console.MessageType.Info)
            items = [item for item in items if item.profession.value == profession]
           
            for rune in data.Runes.values():
                if rune.profession == profession:
                    if settings.profile and rune.identifier not in checked_items:                        
                        settings.profile.runes.pop(rune.identifier, None)
                        
            settings.profile.save() 
                
        else:
            settings.profile.runes.clear()

        ConsoleLog(
            "LootEx", f"Checking {len(items)} runes and insignias from the merchant's inventory for expensive runes...", Console.MessageType.Info)
        ConsoleLog(
            "LootEx", f"This will take about {round(len(items) * 175 / 1000)} seconds.", Console.MessageType.Info)

        for item in items:            
            def create_quotes_for_item(item : Cached_Item):
                runes = item.runes
                
                if runes is None or len(runes) != 1:
                    ConsoleLog(
                        "LootEx", f"{item.name} has {len(runes)} mods. Skipping...", Console.MessageType.Info)
                    return
                
                mod = runes[0]
                # ConsoleLog("LootEx", f"Checking {mod.full_name}...", Console.MessageType.Info)

                def request_quote_for_item(item : Cached_Item):
                    Merchant.Trading.Trader.RequestQuote(item.id)

                def get_quote_for_item(item: Cached_Item):
                    from Sources.frenkeyLib.LootEx.data import Data
                    data = Data()

                    price = Merchant.Trading.Trader.GetQuotedValue()

                    if price is not None:
                        if mod.Rune.identifier and settings.profile:
                            checked_items.append(mod.Rune.identifier)
                            rune = data.Runes.get(mod.Rune.identifier)
                            
                            if rune:
                                rune.vendor_value = price
                                rune.vendor_updated = datetime.now()
                                data.SaveRunes(False)
                            
                            if price >= threshold:
                                ConsoleLog(
                                    "LootEx",
                                    f"{mod.Rune.full_name} is currently quoted at {format_currency(price)}. Marking it as valuable.",
                                    Console.MessageType.Info,
                                )
                                settings.profile.set_rune(mod.Rune.identifier, True, mark_to_sell)
                                settings.profile.save()

                        trader_queue.execute_next()
                        return price

                trader_queue.add_action(request_quote_for_item, item)
                trader_queue.add_action(get_quote_for_item, item)

            create_quotes_for_item(item)

        def check_for_missing_runes():
            
            for rune in data.Runes.values():
                profession_match = profession is None or rune.profession == profession

                if rune.identifier not in checked_items and settings.profile and profession_match:
                    ConsoleLog(
                        "LootEx",
                        f"{rune.full_name} is currently not available. Marking it as valuable.",
                        Console.MessageType.Info,
                    )
                    
                    settings.profile.set_rune(rune.identifier, True, mark_to_sell)
                    settings.profile.save()
            ConsoleLog(
                "LootEx", "Finished checking for runes and insignias.", Console.MessageType.Success)

        trader_queue.add_action(check_for_missing_runes)

    @staticmethod
    def process_trader_queue() -> bool:
        trader_queue.ProcessQueue()
        return not trader_queue.action_queue.is_empty()

class PriceCheckCoroutine:
    def __init__(self, generator_fn: Callable[[], Generator], timeout_seconds: float = 5.0):
        self.generator_fn = generator_fn
        self.generator = None
        self.state = ActionState.Pending
        self.started_at = datetime.min

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

        # Advance generator one step
        try:
            
            # Check for timeout
            elapsed = (datetime.now() - self.started_at).total_seconds()
            if elapsed > 5.0:
                self.state = ActionState.Timeout
                return self.state
            
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
            self.state = ActionState.Failed
            return self.state
            
class PriceCheckAction:
    LOG_PRICE_ACTIONS = False
        
    def __init__(self, item_id: int, on_complete: Optional[Callable[[int, int], None]] = None):
        self.item_id = item_id
        self.price: int | None = None
        self.on_complete = on_complete

        self.coroutine: PriceCheckCoroutine | None = None

    # Entry point
    def run(self) -> PriceCheckCoroutine:
        return PriceCheckCoroutine(self._gen_main)

    # Main generator function
    def _gen_main(self) -> Generator:
        """
        Loop until quantity objective is reached:
        - For Buy: item.quantity >= desired_quantity
        - For Sell: item.quantity <= desired_quantity
        """
        ConsoleLog(
            "LootEx",
            f"Starting TraderAction for {self.item_id}",
            Console.MessageType.Info,
                    self.LOG_PRICE_ACTIONS
        )

        yield from self._request_price()
        yield from self._wait_for_price()
        
        ConsoleLog(
            "LootEx",
            f"TraderAction for {self.item_id} COMPLETED. Price: {self.price}",
            Console.MessageType.Info,
                    self.LOG_PRICE_ACTIONS
        )

    # Condition to stop the trading action
    def _is_done(self) -> bool:
        return self.price is not None
    
    # Request a price quote from the merchant
    def _request_price(self) -> Generator:     
        offered_items = Trading.Trader.GetOfferedItems()
        
        if offered_items is None or self.item_id not in offered_items:
            ConsoleLog(
                "LootEx",
                f"Item {self.item_id} no longer offered by trader.",
                Console.MessageType.Warning,
                self.LOG_PRICE_ACTIONS
            )
            return   
                     
        ConsoleLog(
            "LootEx",
            f"Requesting quote for {self.item_id}",
            Console.MessageType.Info,
                    self.LOG_PRICE_ACTIONS
        )

        Trading.Trader.RequestQuote(self.item_id)

        self._start_quote_time = datetime.now()
        yield Routines.Yield.wait(25)

    # Wait until we receive a price quote
    def _wait_for_price(self) -> Generator:
        while True:     
            offered_items = Trading.Trader.GetOfferedItems()
            if offered_items is None or self.item_id not in offered_items:
                ConsoleLog(
                    "LootEx",
                    f"Item {self.item_id} no longer offered by trader.",
                    Console.MessageType.Warning,
                    self.LOG_PRICE_ACTIONS
                )
                return
            
            quoted_id = Trading.Trader.GetQuotedItemID()
            quoted_value = Trading.Trader.GetQuotedValue()
            
            if quoted_id == self.item_id:
                self.price = quoted_value
                ConsoleLog(
                    "LootEx",
                    f"Received quote {quoted_value} for {self.item_id}",
                    Console.MessageType.Info,
                    self.LOG_PRICE_ACTIONS
                )
                
                if self.on_complete:
                    self.on_complete(self.item_id, self.price)
                    
                return

            if (datetime.now() - self._start_quote_time).total_seconds() > 2.0:
                ConsoleLog(
                    "LootEx",
                    f"Quote request for {self.item_id} timed out.",
                    Console.MessageType.Warning,
                    self.LOG_PRICE_ACTIONS
                )
                return
            
            yield Routines.Yield.wait(100)
                    
class PriceCheckManager:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PriceCheckManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.queue: list[PriceCheckAction] = []
        self.retried_items: set[int] = set()
        self.prices : dict[int, int] = {}
        
    
    def request_prices(self, item_ids: list[int], on_complete: Optional[Callable[[int, int], None]] = None) -> None:
        self.prices.clear()
        self.retried_items.clear()
        
        ConsoleLog(
            "LootEx",
            f"Requesting prices for items: {item_ids}",
            Console.MessageType.Info,
            PriceCheckAction.LOG_PRICE_ACTIONS
        )
        
        for item_id in item_ids:
            action = PriceCheckAction(item_id, on_complete)
            self.queue.append(action)
    
    def Run(self) -> bool:
        if not self.queue:
            return False
        
        current_action = self.queue[0]
        
        if current_action.coroutine is None:
            current_action.coroutine = current_action.run()
        
        state = current_action.coroutine.step()
        
        if state == ActionState.Completed or state == ActionState.Failed:
            if current_action.price is not None and current_action.price > 0:
                self.prices[current_action.item_id] = current_action.price
                
            self.queue.pop(0)
        elif state == ActionState.Timeout:
            if current_action.item_id not in self.retried_items:
                ConsoleLog(
                    "LootEx",
                    f"Price check for item {current_action.item_id} timed out. Retrying...",
                    Console.MessageType.Warning,
                    PriceCheckAction.LOG_PRICE_ACTIONS
                )
                
                self.retried_items.add(current_action.item_id)
                action = PriceCheckAction(current_action.item_id, current_action.on_complete)
                self.queue.append(action)
            else:
                ConsoleLog(
                    "LootEx",
                    f"Price check for item {current_action.item_id} timed out again. Skipping...",
                    Console.MessageType.Error,
                    True
                )
                self.queue.pop(0)
            
        if not self.queue:
            ConsoleLog(
                "LootEx",
                f"PriceCheckManager completed all price checks.",
                Console.MessageType.Info,
                True
            )            
        
        return True