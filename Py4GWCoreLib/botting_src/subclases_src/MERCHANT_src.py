#region STATES
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

from ...enums import ModelID

#region ITEMS
class _MERCHANTS:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self.Restock = _MERCHANTS._RESTOCK(parent)
        
    def SellMaterialsToMerchant(self):
        self._helpers.Merchant.sell_materials_to_merchant()
        
    class _RESTOCK:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers

        def IdentifyKits(self):
            self._helpers.Merchant.restock_identification_kits()

        def SalvageKits(self):
            self._helpers.Merchant.restock_salvage_kits()
