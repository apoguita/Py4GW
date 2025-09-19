from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING,List

from ...Py4GWcorelib import ConsoleLog, Console
from ...enums_src.Model_enums import ModelID

#region MERCHANT
class _Merchant:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events
        self.MERCHANT_FRAME = 3613855137  # Hash for "MerchantFrame"
        
    def _is_merchant(self):
        from ...Merchant import Trading
        from ...Item import Item
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        salvage_kit = ModelID.Salvage_Kit.value

        if salvage_kit in merchant_item_models:
            return True
        return False
    
    def _is_material_trader(self):
        from ...Merchant import Trading
        from ...Item import Item
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        wood_planks = ModelID.Wood_Plank.value

        if wood_planks in merchant_item_models:
            return True
        return False
    
    def _is_rare_material_trader(self):
        from ...Merchant import Trading
        from ...Item import Item
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        glob_of_ectoplasm = ModelID.Glob_Of_Ectoplasm.value

        if glob_of_ectoplasm in merchant_item_models:
            return True
        return False
    
    def _is_rune_trader(self):
        from ...Merchant import Trading
        from ...Item import Item
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        rune_of_superior_vigor = ModelID.Rune_Of_Superior_Vigor.value

        if rune_of_superior_vigor in merchant_item_models:
            return True
        return False
    
    def _is_scroll_trader(self):
        from ...Merchant import Trading
        from ...Item import Item
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        scroll_of_berserkers_insitght = ModelID.Scroll_Of_Berserkers_Insight.value

        if scroll_of_berserkers_insitght in merchant_item_models:
            return True
        return False
    
    def _is_dye_trader(self):
        from ...Merchant import Trading
        from ...Item import Item
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
        from ...UIManager import UIManager
        merchant_frame_id = UIManager.GetFrameIDByHash(self.MERCHANT_FRAME)
        merchant_frame_exists = UIManager.FrameExists(merchant_frame_id)
        return merchant_frame_exists
    
    def _get_materials_to_sell(self) -> List[int]:
        from ...GlobalCache import GLOBAL_CACHE
        from ...ItemArray import ItemArray
        bags_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
        bag_item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bags_to_check)
        materials_to_sell = ItemArray.Filter.ByCondition(bag_item_array, lambda item_id: GLOBAL_CACHE.Item.Type.IsMaterial(item_id))
        return materials_to_sell
    
    def _count_stacks_of_model(self, model_id: int) -> int:
        from ...ItemArray import ItemArray
        from ...Item import Item
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
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines

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


                
    @_yield_step(label="SellMaterialsToMerchant", counter_key="SELL_MATERIALS_TO_MERCHANT")
    def sell_materials_to_merchant(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        if self._merchant_frame_exists(): # and self._is_merchant():    
            yield from Routines.Yield.Merchant.SellItems(self._get_materials_to_sell(), log=False)
        else:
            ConsoleLog("SellMaterialsToMerchant", "Merchant window is not open.", Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            return


    @_yield_step(label="RestockIdentificationKits", counter_key="RESTOCK_IDENTIFICATION_KITS")
    def restock_identification_kits(self):
        if self._config.upkeep.identify_kits.is_active():
            qty = self._config.upkeep.identify_kits.get("restock_quantity")
            current_stacks = self._count_stacks_of_model(ModelID.Superior_Identification_Kit.value)
            needed_stacks = max(0, qty - current_stacks)
            if needed_stacks > 0:
                yield from self._restock_item(ModelID.Superior_Identification_Kit.value, needed_stacks)

    @_yield_step(label="RestockSalvageKits", counter_key="RESTOCK_SALVAGE_KITS")
    def restock_salvage_kits(self):
        if self._config.upkeep.salvage_kits.is_active():
            qty = self._config.upkeep.salvage_kits.get("restock_quantity")
            current_stacks = self._count_stacks_of_model(ModelID.Salvage_Kit.value)
            needed_stacks = max(0, qty - current_stacks)
            if needed_stacks > 0:
                yield from self._restock_item(ModelID.Salvage_Kit.value, needed_stacks)

