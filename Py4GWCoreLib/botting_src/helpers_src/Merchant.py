from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step
from typing import Any, Generator, TYPE_CHECKING,List


#region MERCHANT
class _Merchant:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events
        self.MERCHANT_FRAME = 3613855137  # Hash for "MerchantFrame"
        
    def _is_merchant(self):
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        return merchant_handler._is_merchant()
    
    def _is_material_trader(self):
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        return merchant_handler._is_material_trader()
    
    def _is_rare_material_trader(self):
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
                
        return merchant_handler._is_rare_material_trader()
    
    def _is_rune_trader(self):
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()        
        
        return merchant_handler._is_rune_trader()
    
    def _is_scroll_trader(self):
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        return merchant_handler._is_scroll_trader()
    
    def _is_dye_trader(self):
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        return merchant_handler._is_dye_trader()
    
    def _get_merchant_minimum_quantity(self) -> int:
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        return merchant_handler._get_merchant_minimum_quantity()
    
    def _merchant_frame_exists(self) -> bool:
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        return merchant_handler._merchant_frame_exists()
    
    def _get_materials_to_sell(self) -> List[int]:
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        return merchant_handler._get_materials_to_sell()
    
    def _count_stacks_of_model(self, model_id: int) -> int:
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        return merchant_handler._count_stacks_of_model(model_id)

    def _restock_item(self, model_id: int, desired_quantity: int) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        return merchant_handler._restock_item(model_id, desired_quantity)

    def _buy_item(self, model_id: int, desired_quantity: int) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        return merchant_handler._buy_item(model_id, desired_quantity)
    
    def _sell_item(self, item_id: int, quantity: int) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        return merchant_handler._sell_item(item_id, quantity)

                
    @_yield_step(label="SellMaterialsToMerchant", counter_key="SELL_MATERIALS_TO_MERCHANT")
    def sell_materials_to_merchant(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        yield from merchant_handler.sell_materials_to_merchant(self._Events)

    @_yield_step(label="RestockIdentificationKits", counter_key="RESTOCK_IDENTIFICATION_KITS")
    def restock_identification_kits(self):
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        yield from merchant_handler.restock_identification_kits(self._config)
        
    @_yield_step(label="RestockSalvageKits", counter_key="RESTOCK_SALVAGE_KITS")
    def restock_salvage_kits(self):
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        yield from merchant_handler.restock_salvage_kits(self._config)
        
    @_yield_step(label="BuyItem", counter_key="BUY_ITEM")
    def buy_item(self, model_id: int, quantity: int) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        yield from merchant_handler.buy_item(model_id, quantity)
        
    @_yield_step(label="SellItem", counter_key="SELL_ITEM")
    def sell_item(self, item_id: int, quantity: int) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.MerchantHandler import MerchantHandler
        merchant_handler = MerchantHandler()
        
        yield from merchant_handler.sell_item(item_id, quantity)