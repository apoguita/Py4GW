from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple, List, Optional, Callable

from ...Py4GWcorelib import ConsoleLog, Console
from ...enums_src.Model_enums import ModelID

#region ITEMS
class _Items:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events
        
    @_yield_step(label="LootItems", counter_key="LOOT_ITEMS")
    def loot(self, pickup_timeout = 5000) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...Py4GWcorelib import LootConfig
        from ...enums import Range
        from ...GlobalCache import GLOBAL_CACHE
        
        if not Routines.Checks.Map.MapValid():
            yield from Routines.Yield.wait(1000)  # Wait for map to be valid
            return
            
        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            yield from Routines.Yield.wait(1000)  # Wait if dead
            return 
        
        loot_singleton = LootConfig()
        filtered_agent_ids = loot_singleton.GetfilteredLootArray(distance=Range.Earshot.value, multibox_loot=True, allow_unasigned_loot=True)
        yield from Routines.Yield.Items.LootItems(filtered_agent_ids, pickup_timeout=pickup_timeout)
        
    @_yield_step(label="AddModelToBlacklist", counter_key="ADD_MODEL_TO_BLACKLIST")
    def add_model_to_blacklist(self, model_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.AddToBlacklist(model_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is added

    @_yield_step(label="RemoveModelFromBlacklist", counter_key="REMOVE_MODEL_FROM_BLACKLIST")
    def remove_model_from_blacklist(self, model_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.RemoveFromBlacklist(model_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is removed

    @_yield_step(label="AddModelToWhitelist", counter_key="ADD_MODEL_TO_WHITELIST")
    def add_model_to_whitelist(self, model_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.AddToWhitelist(model_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is added
        
    @_yield_step(label="RemoveModelFromWhitelist", counter_key="REMOVE_MODEL_FROM_WHITELIST")
    def remove_model_from_whitelist(self, model_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.RemoveFromWhitelist(model_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is removed
        
    @_yield_step(label="ClearWhitelist", counter_key="CLEAR_WHITELIST")
    def clear_whitelist(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.ClearWhitelist()
        yield from Routines.Yield.wait(100)  # Small wait to ensure the whitelist is cleared
        
    @_yield_step(label="ClearBlacklist", counter_key="CLEAR_BLACKLIST") 
    def clear_blacklist(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.ClearBlacklist()
        yield from Routines.Yield.wait(100)  # Small wait to ensure the blacklist is cleared
        

    @_yield_step(label="AddItemIDToWhitelist", counter_key="ADD_ITEM_ID_TO_WHITELIST")
    def add_item_id_to_whitelist(self, item_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_whitelist.add(item_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is added
        
    @_yield_step(label="RemoveItemIDFromWhitelist", counter_key="REMOVE_ITEM_ID_FROM_WHITELIST")
    def remove_item_id_from_whitelist(self, item_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_whitelist.discard(item_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is removed
        
    @_yield_step(label="ClearItemIDWhitelist", counter_key="CLEAR_ITEM_ID_WHITELIST")
    def clear_item_id_whitelist(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_whitelist.clear()
        yield from Routines.Yield.wait(100)  # Small wait to ensure the whitelist is cleared
        
    @_yield_step(label="AddItemIDToBlacklist", counter_key="ADD_ITEM_ID_TO_BLACKLIST")
    def add_item_id_to_blacklist(self, item_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_blacklist.add(item_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is added
        
    @_yield_step(label="RemoveItemIDFromBlacklist", counter_key="REMOVE_ITEM_ID_FROM_BLACKLIST")
    def remove_item_id_from_blacklist(self, item_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_blacklist.discard(item_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is removed
        
    @_yield_step(label="ClearItemIDBlacklist", counter_key="CLEAR_ITEM_ID_BLACKLIST")
    def clear_item_id_blacklist(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_blacklist.clear()
        yield from Routines.Yield.wait(100)  # Small wait to ensure the blacklist is cleared
        
        
    @_yield_step(label="AddDyeToWhitelist", counter_key="ADD_DYE_TO_WHITELIST")
    def add_dye_to_whitelist(self, dye_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.dye_whitelist.add(dye_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the dye is added
        
    @_yield_step(label="RemoveDyeFromWhitelist", counter_key="REMOVE_DYE_FROM_WHITELIST")
    def remove_dye_from_whitelist(self, dye_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.dye_whitelist.discard(dye_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the dye is removed
        
    @_yield_step(label="ClearDyeWhitelist", counter_key="CLEAR_DYE_WHITELIST")
    def clear_dye_whitelist(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.dye_whitelist.clear()
        yield from Routines.Yield.wait(100)  # Small wait to ensure the whitelist is cleared

    @_yield_step(label="CraftItem", counter_key="CRAFT_ITEM")
    def craft(self, output_model_id: int, cost: int,
                trade_model_ids: list[int], quantity_list: list[int]):
        from ...Routines import Routines
        from ...Py4GWcorelib import ConsoleLog
        import Py4GW
        result = yield from Routines.Yield.Items.CraftItem(output_model_id=output_model_id,
                                                            cost=cost,
                                                            trade_model_ids=trade_model_ids,
                                                            quantity_list=quantity_list)
        if not result:
            ConsoleLog("CraftItem", f"Failed to craft item ({output_model_id}).", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            return False

        return True

    def _equip(self, model_id: int):
        from ...Routines import Routines
        import Py4GW
        from ...Py4GWcorelib import ConsoleLog
        result = yield from Routines.Yield.Items.EquipItem(model_id)
        if not result:
            ConsoleLog("EquipItem", f"Failed to equip item ({model_id}).", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            return False

        return True

    @_yield_step(label="EquipItem", counter_key="EQUIP_ITEM")
    def equip(self, model_id: int):
        return (yield from self._equip(model_id))
    
        
    @_yield_step(label="DestroyItem", counter_key="DESTROY_ITEM")
    def destroy(self, model_id: int) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        from ...Py4GWcorelib import ConsoleLog
        import Py4GW
        result = yield from Routines.Yield.Items.DestroyItem(model_id)
        if not result:
            ConsoleLog("DestroyItem", f"Failed to destroy item ({model_id}).", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            return False

        return True
    
    def _destroy_bonus_items(self, 
                            exclude_list: List[int] = [ModelID.Igneous_Summoning_Stone.value, 
                                                        ModelID.Bonus_Nevermore_Flatbow.value]
                            ) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        bonus_items = [ModelID.Bonus_Luminescent_Scepter.value,
                        ModelID.Bonus_Nevermore_Flatbow.value,
                        ModelID.Bonus_Rhinos_Charge.value,
                        ModelID.Bonus_Serrated_Shield.value,
                        ModelID.Bonus_Soul_Shrieker.value,
                        ModelID.Bonus_Tigers_Roar.value,
                        ModelID.Bonus_Wolfs_Favor.value,
                        ModelID.Igneous_Summoning_Stone.value
                        ]
        
        #remove excluded items from the list
        for model in exclude_list:
            if model in bonus_items:
                bonus_items.remove(model)

        for model in bonus_items:
            ConsoleLog("DestroyBonusItems", f"Destroying bonus item ({model}).", Console.MessageType.Info, log=False)
            result = yield from Routines.Yield.Items.DestroyItem(model)
        

    @_yield_step(label="DestroyBonusItems", counter_key="DESTROY_BONUS_ITEMS")
    def destroy_bonus_items(self, 
                            exclude_list: List[int] = [ModelID.Igneous_Summoning_Stone.value, 
                                                        ModelID.Bonus_Nevermore_Flatbow.value]
                            ) -> Generator[Any, Any, None]:
        yield from self._destroy_bonus_items(exclude_list)
        

        
    def _spawn_bonus_items(self):
        from ...Routines import Routines
        yield from Routines.Yield.Items.SpawnBonusItems()
        
    @_yield_step(label="SpawnBonusItems", counter_key="SPAWN_BONUS")
    def spawn_bonus_items(self):
        yield from self._spawn_bonus_items()
        
    def _move_model_to_bag_slot(self, model_id:int, bag_id:int, slot:int):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        import Py4GW
        from ...Py4GWcorelib import ConsoleLog
        result = GLOBAL_CACHE.Inventory.MoveModelToBagSlot(model_id, bag_id, slot)
        if not result:
            ConsoleLog("MoveModelToBagSlot", f"Failed to move item ({model_id}) to bag {bag_id} slot {slot}.", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            return False
        yield from Routines.Yield.wait(250)  # Small wait to ensure the item is moved
        return True
    
    @_yield_step(label="MoveModelToBagSlot", counter_key="MOVE_MODEL_TO_BAG_SLOT")
    def move_model_to_bag_slot(self, model_id:int, bag_id:int, slot:int):
        return (yield from self._move_model_to_bag_slot(model_id, bag_id, slot))
        
    @_yield_step(label="AutoIdentifyItems", counter_key="AUTO_IDENTIFY")
    def auto_identify_items(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from inventory_handler.IdentifyItems()
        inventory_handler.module_active = current_state
        
    @_yield_step(label="AutoSalvageItems", counter_key="AUTO_SALVAGE")
    def auto_salvage_items(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from inventory_handler.SalvageItems()
        inventory_handler.module_active = current_state
        
    @_yield_step(label="AutodepositItems", counter_key="AUTO_DEPOSIT")
    def auto_deposit_items(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from inventory_handler.DepositItemsAuto()
        inventory_handler.module_active = current_state
        
    @_yield_step(label="AutodepositGold", counter_key="AUTO_DEPOSIT_GOLD")
    def auto_deposit_gold(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        from ...Routines import Routines
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from Routines.Yield.Items.DepositGold(inventory_handler.keep_gold, log =False)
        inventory_handler.module_active = current_state
        
    @_yield_step(label="AutoIDAndSalvage", counter_key="AUTO_ID_AND_SALVAGE")
    def auto_id_and_salvage(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from inventory_handler.IdentifyItems()
        yield from inventory_handler.SalvageItems()
        inventory_handler.module_active = current_state
        
    @_yield_step(label="AutoIDAndSalvageAndDeposit", counter_key="AUTO_ID_SALVAGE_DEPOSIT")
    def auto_id_and_salvage_and_deposit(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        from ...Routines import Routines
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from inventory_handler.IdentifyItems()
        yield from inventory_handler.SalvageItems()
        yield from inventory_handler.DepositItemsAuto()
        yield from Routines.Yield.Items.DepositGold(inventory_handler.keep_gold, log =False)
        inventory_handler.module_active = current_state
        
    @_yield_step(label="WithdrawItems", counter_key="WITHDRAW_ITEMS")
    def withdraw(self, model_id:int, quantity:int) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        from ...Py4GWcorelib import ConsoleLog
        import Py4GW
        result = yield from Routines.Yield.Items.WithdrawItems(model_id, quantity)
        if not result:
            ConsoleLog("WithdrawItems", f"Failed to withdraw ({quantity}) items from storage.", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            return False

        return True

        
    