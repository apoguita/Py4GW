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

    def WithdrawGold(self, target_gold: int = 20000, deposit_all: bool = True):
        """Ensure the character has exactly target_gold on hand.
        Deposits excess first (if deposit_all=True), then withdraws the shortfall from storage."""
        self._helpers.Items.withdraw_gold(target_gold, deposit_all)

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

    def UseSummoningStone(self):
        """
        Uses a summoning stone from inventory with priority:
        1. Legionnaire Summoning Crystal (always first)
        2. Igneous Summoning Stone (if player level < 20)
        3. Any other available summoning stone
        """
        self._helpers.Items.use_summoning_stone()

    def UseAllConsumables(self):
        """
        Uses all consumables for the current player only (not multibox).
        Includes: Essence of Celerity, Grail of Might, Armor of Salvation,
        Birthday Cupcake, Golden Egg, Candy Corn, Candy Apple, Pumpkin Pie,
        Drake Kabob, Skalefin Soup, Pahnai Salad, and War Supplies.
        """
        self._helpers.Items.use_all_consumables()

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
        
    def MoveModelToBagSlot(self, model_id:int, target_bag:int, slot:int):
        self._helpers.Items.move_model_to_bag_slot(model_id, target_bag, slot)

    #region Lootcofigs
    #whitelist
    def AddModelToLootWhitelist(self, model_id:int):
        self._helpers.Items.add_model_to_whitelist(model_id)
        
    def RemoveModelFromLootWhitelist(self, model_id:int):
        self._helpers.Items.remove_model_from_whitelist(model_id)
        
    def ClearLootWhitelist(self):
        self._helpers.Items.clear_whitelist()
        
    #blacklist
    def AddModelToLootBlacklist(self, model_id:int):
        self._helpers.Items.add_model_to_blacklist(model_id)
    
    def RemoveModelFromLootBlacklist(self, model_id:int):
        self._helpers.Items.remove_model_from_blacklist(model_id)
    
    def ClearLootBlacklist(self):
        self._helpers.Items.clear_blacklist()
        
    #item id whitelist
    def AddItemIDToLootWhitelist(self, item_id:int):
        self._helpers.Items.add_item_id_to_whitelist(item_id)
        
    def RemoveItemIDFromLootWhitelist(self, item_id:int):
        self._helpers.Items.remove_item_id_from_whitelist(item_id)
        
    def ClearItemIDLootWhitelist(self):      
        self._helpers.Items.clear_item_id_whitelist()
        
    #item id blacklist
    def AddItemIDToLootBlacklist(self, item_id:int):
        self._helpers.Items.add_item_id_to_blacklist(item_id)
        
    def RemoveItemIDFromLootBlacklist(self, item_id:int):
        self._helpers.Items.remove_item_id_from_blacklist(item_id)
        
    def ClearItemIDLootBlacklist(self):
        self._helpers.Items.clear_item_id_blacklist()
        
    #dye whitelist
    def AddDyeToLootWhitelist(self, model_id:int):
        self._helpers.Items.add_dye_to_whitelist(model_id)
        
    def RemoveDyeFromLootWhitelist(self, model_id:int):
        self._helpers.Items.remove_dye_from_whitelist(model_id)
        
    def ClearDyeLootWhitelist(self):
        self._helpers.Items.clear_dye_whitelist()
        
    class _RESTOCK:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers

        def BirthdayCupcake(self):
            self._helpers.Restock.restock_birthday_cupcake()
        
        def CandyApple(self):
            self._helpers.Restock.restock_candy_apple()

        def Honeycomb(self):
            self._helpers.Restock.restock_honeycomb()

        def WarSupplies(self):
            self._helpers.Restock.restock_war_supplies()



