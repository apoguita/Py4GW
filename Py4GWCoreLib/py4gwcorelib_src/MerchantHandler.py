from typing import Any, Generator, List

from Py4GW import Console

from Py4GWCoreLib import Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Item import Item
from Py4GWCoreLib.ItemArray import ItemArray
from Py4GWCoreLib.Merchant import Trading
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.botting_src.config import BotConfig
from Py4GWCoreLib.botting_src.helpers_src.Events import _Events
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog


class MerchantHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MerchantHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        self.MERCHANT_FRAME = 3613855137  # Hash for "MerchantFrame"
        
    def _is_merchant(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        salvage_kit = ModelID.Salvage_Kit.value

        if salvage_kit in merchant_item_models:
            return True
        return False
    
    def _is_material_trader(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        wood_planks = ModelID.Wood_Plank.value

        if wood_planks in merchant_item_models:
            return True
        return False
    
    def _is_rare_material_trader(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        glob_of_ectoplasm = ModelID.Glob_Of_Ectoplasm.value

        if glob_of_ectoplasm in merchant_item_models:
            return True
        return False
    
    def _is_rune_trader(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        rune_of_superior_vigor = ModelID.Rune_Of_Superior_Vigor.value

        if rune_of_superior_vigor in merchant_item_models:
            return True
        return False
    
    def _is_scroll_trader(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        scroll_of_berserkers_insitght = ModelID.Scroll_Of_Berserkers_Insight.value

        if scroll_of_berserkers_insitght in merchant_item_models:
            return True
        return False
    
    def _is_dye_trader(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        vial_of_dye = ModelID.Vial_Of_Dye.value

        if vial_of_dye in merchant_item_models and not self._is_material_trader():
            return True
        return False
    
    def _get_merchant_minimum_quantity(self) -> int:
        required_quantity = 10 #if is_material_trader else 1
        if not self._is_material_trader():
            required_quantity = 1
            
        return required_quantity
    
    def _merchant_frame_exists(self) -> bool:
        merchant_frame_id = UIManager.GetFrameIDByHash(self.MERCHANT_FRAME)
        merchant_frame_exists = UIManager.FrameExists(merchant_frame_id)
        return merchant_frame_exists
    
    def _get_materials_to_sell(self) -> List[int]:
        bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
        bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
        materials_to_sell = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: GLOBAL_CACHE.Item.Type.IsMaterial(item_id))
        return materials_to_sell
    
    def _count_stacks_of_model(self, model_id: int) -> int:
        bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
        item_array = ItemArray.GetItemArray(bags_to_check)

        # Filter items by the given model_id
        matching_items = ItemArray.Filter.ByCondition(
            item_array,
            lambda item_id: Item.GetModelID(item_id) == model_id
        )

        # Return the number of stacks found (full or partial)
        return len(matching_items)

    def _restock_item(self, model_id: int, desired_quantity: int) -> Generator[Any, Any, None]:
        if self._merchant_frame_exists(): # and self._is_merchant(): 
            offered_items = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
            for item in offered_items:
                item_model = GLOBAL_CACHE.Item.GetModelID(item)
                if item_model == model_id:
                    value = GLOBAL_CACHE.Item.Properties.GetValue(item) * 2
                    bought = 0
                    while bought < desired_quantity:
                        GLOBAL_CACHE.Trading.Merchant.BuyItem(item, value)
                        bought += 1
                        yield from Routines.Yield.wait(75)  # wait between purchases
                    break

    def _buy_item(self, model_id: int, desired_quantity: int) -> Generator[Any, Any, None]:
        if self._merchant_frame_exists(): # and self._is_merchant(): 
            offered_items = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
            for item in offered_items:
                item_model = GLOBAL_CACHE.Item.GetModelID(item)
                if item_model == model_id:
                    value = GLOBAL_CACHE.Item.Properties.GetValue(item) * 2
                    bought = 0
                    while bought < desired_quantity:
                        GLOBAL_CACHE.Trading.Merchant.BuyItem(item, value)
                        bought += 1
                        yield from Routines.Yield.wait(75)  # wait between purchases
                    break
                
    def _sell_item(self, item_id: int, quantity: int) -> Generator[Any, Any, None]:
        if self._merchant_frame_exists(): # and self._is_merchant(): 
            value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
            sold = 0
            while sold < quantity:
                GLOBAL_CACHE.Trading.Merchant.SellItem(item_id, value)
                sold += 1
                yield from Routines.Yield.wait(75)  # wait between sales
                                
    def sell_materials_to_merchant(self, _events : _Events) -> Generator[Any, Any, None]:
        if self._merchant_frame_exists(): # and self._is_merchant():    
            yield from Routines.Yield.Merchant.SellItems(self._get_materials_to_sell(), log=False)
        else:
            ConsoleLog("SellMaterialsToMerchant", "Merchant window is not open.", Console.MessageType.Error)
            _events.on_unmanaged_fail()
            return

    def restock_identification_kits(self, _config : BotConfig) -> Generator[Any, Any, None]:
        if _config.upkeep.identify_kits.is_active():
            qty = _config.upkeep.identify_kits.get("restock_quantity")
            current_stacks = self._count_stacks_of_model(ModelID.Superior_Identification_Kit.value)
            needed_stacks = max(0, qty - current_stacks)
            if needed_stacks > 0:
                yield from self._restock_item(ModelID.Superior_Identification_Kit.value, needed_stacks)

    def restock_salvage_kits(self, _config) -> Generator[Any, Any, None]:
        if _config.upkeep.salvage_kits.is_active():
            qty = _config.upkeep.salvage_kits.get("restock_quantity")
            current_stacks = self._count_stacks_of_model(ModelID.Salvage_Kit.value)
            needed_stacks = max(0, qty - current_stacks)
            if needed_stacks > 0:
                yield from self._restock_item(ModelID.Salvage_Kit.value, needed_stacks)
                
    def buy_item(self, model_id: int, quantity: int) -> Generator[Any, Any, None]:
        yield from self._buy_item(model_id, quantity)
        
    def sell_item(self, item_id: int, quantity: int) -> Generator[Any, Any, None]:
        yield from self._sell_item(item_id, quantity)
        
    