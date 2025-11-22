import datetime
from Widgets.frenkey.LootEx import enum, utility
from Py4GWCoreLib import Item, Merchant, Console
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import ActionQueueNode, ConsoleLog
from Py4GWCoreLib.enums import ItemType



trader_queue = ActionQueueNode(175)
checked_items: list[str] = []

class PriceCheck:
    @staticmethod 
    def get_material_prices_from_trader():
        from Widgets.frenkey.LootEx.data import Data
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
                            material.vendor_updated = datetime.datetime.now()
                            data.Materials[model_id] = material
                            
                            data.SaveMaterials()

                            trader_queue.execute_next()
                            return price

                trader_queue.add_action(request_quote_for_item, item)
                trader_queue.add_action(get_quote_for_item, item)
                
            create_quotes_for_item(item)
        
    @staticmethod
    def get_expensive_runes_from_merchant(threshold: int = 1000, mark_to_sell : bool = False, profession: int = 0) -> None:
        from Widgets.frenkey.LootEx.settings import Settings
        settings = Settings()
        
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
        items = Merchant.Trading.Trader.GetOfferedItems()
        if items is None:
            ConsoleLog(
                "LootEx", "No items found in merchant's inventory.", Console.MessageType.Error)
            return

        settings.profile.runes.clear()
        if profession is not None and profession != 0:
            ConsoleLog(
                "LootEx", f"Checking for runes and insignias for profession {profession}...", Console.MessageType.Info)
            items = [item for item in items if Item.Properties.GetProfession(
                item) == int(profession)] if profession else items

        ConsoleLog(
            "LootEx", f"Checking {len(items)} runes and insignias from the merchant's inventory for expensive runes...", Console.MessageType.Info)
        ConsoleLog(
            "LootEx", f"This will take about {round(len(items) * 175 / 1000)} seconds.", Console.MessageType.Info)

        for item in items:
            Item.RequestName(item)
            
            def create_quotes_for_item(item):
                mods, _, _ = utility.Util.GetMods(item)
                
                if mods is None or len(mods) != 1:
                    ConsoleLog(
                        "LootEx", f"{Item.GetName(item)} has {len(mods)} mods. Skipping...", Console.MessageType.Info)
                    return
                
                mod = mods[0]
                # ConsoleLog("LootEx", f"Checking {mod.full_name}...", Console.MessageType.Info)

                def request_quote_for_item(item):
                    Merchant.Trading.Trader.RequestQuote(item)

                def get_quote_for_item(item):
                    from Widgets.frenkey.LootEx.data import Data
                    data = Data()

                    price = Merchant.Trading.Trader.GetQuotedValue()

                    if price is not None:
                        if mod.identifier and settings.profile:
                            checked_items.append(mod.identifier)
                            rune = data.Runes.get(mod.identifier)
                            
                            if rune:
                                rune.vendor_value = price
                                rune.vendor_updated = datetime.datetime.now()
                                data.SaveRunes(False)
                            
                            if price >= threshold:
                                ConsoleLog(
                                    "LootEx",
                                    f"{mod.full_name} is currently quoted at {format_currency(price)}. Marking it as valuable.",
                                    Console.MessageType.Info,
                                )
                                settings.profile.set_rune(mod.identifier, True, mark_to_sell)
                                settings.profile.save()

                        trader_queue.execute_next()
                        return price

                trader_queue.add_action(request_quote_for_item, item)
                trader_queue.add_action(get_quote_for_item, item)

            create_quotes_for_item(item)

        def check_for_missing_runes():
            from Widgets.frenkey.LootEx.data import Data
            data = Data()
            
            for rune in data.Runes.values():
                profession_match = profession is not None and rune.profession == profession

                if rune.identifier not in checked_items and settings.profile and profession_match:
                    ConsoleLog(
                        "LootEx",
                        f"{rune.full_name} is currently not available. Marking it as valuable.",
                        Console.MessageType.Info,
                    )
                    
                    settings.profile.set_rune(rune.identifier, True)
                    settings.profile.save()
            ConsoleLog(
                "LootEx", "Finished checking for runes and insignias.", Console.MessageType.Success)

        trader_queue.add_action(check_for_missing_runes)

    @staticmethod
    def process_trader_queue() -> bool:
        trader_queue.ProcessQueue()
        return not trader_queue.action_queue.is_empty()
