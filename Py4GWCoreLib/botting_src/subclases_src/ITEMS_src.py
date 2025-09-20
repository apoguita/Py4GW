#region STATES
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

from ...enums import ModelID

#region ITEMS
class _ITEMS:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self.Restock = _ITEMS._RESTOCK(parent)
        
    def AutoIdentifyItems(self):
        "Uses the AutoLoot Handler to identify items automatically."
        self._helpers.Items.auto_identify_items()

    def AutoSalvageItems(self):
        "Uses the AutoLoot Handler to salvage items automatically."
        self._helpers.Items.auto_salvage_items()

    def AutoDepositItems(self):
        "Uses the AutoLoot Handler to deposit items automatically."
        self._helpers.Items.auto_deposit_items()

    def AutoDepositGold(self):
        "Uses the AutoLoot Handler to deposit gold automatically."
        self._helpers.Items.auto_deposit_gold()
        
    def AutoIDAndSalvageItems(self):
        "Uses the AutoLoot Handler to identify and salvage items automatically."
        self._helpers.Items.auto_id_and_salvage()
        
    def AutoIDAndSalvageAndDepositItems(self):
        "Uses the AutoLoot Handler to identify, salvage, and deposit items automatically."
        self._helpers.Items.auto_id_and_salvage_and_deposit()
        
    def LootItems(self, pickup_timeout = 5000 ):
        self._helpers.Items.loot(pickup_timeout)

    def Craft(self, model_id: int, value: int, trade_items_models: list[int], quantity_list: list[int]):
        self._helpers.Items.craft(model_id, value, trade_items_models, quantity_list)

    def Withdraw(self, model_id:int, quantity:int):
        self._helpers.Items.withdraw(model_id, quantity)

    def Equip(self, model_id: int):
        self._helpers.Items.equip(model_id)

    def Destroy(self, model_id: int):
        self._helpers.Items.destroy(model_id)

    def DestroyBonusItems(self,
                            exclude_list: List[int] = [ModelID.Igneous_Summoning_Stone.value,
                                                        ModelID.Bonus_Nevermore_Flatbow.value]):
        self._helpers.Items.destroy_bonus_items(exclude_list)

    def SpawnBonusItems(self):
        self._helpers.Items.spawn_bonus_items()
        
    def SpawnAndDestroyBonusItems(self,
                                    exclude_list: List[int] = [ModelID.Igneous_Summoning_Stone.value,
                                                                ModelID.Bonus_Nevermore_Flatbow.value]):
        self._helpers.Items.spawn_bonus_items()
        self._helpers.Items.destroy_bonus_items(exclude_list)
        
        
        
    class _RESTOCK:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers

        def BirthdayCupcake(self):
            self._helpers.Restock.restock_birthday_cupcake()

        def Honeycomb(self):
            self._helpers.Restock.restock_honeycomb()



