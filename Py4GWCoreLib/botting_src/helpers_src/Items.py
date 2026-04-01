from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple, List, Optional, Callable

from ...Py4GWcorelib import ConsoleLog, Console
from ...Player import Player
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
        from ...Agent import Agent
        
        if not Routines.Checks.Map.MapValid():
            yield from Routines.Yield.wait(1000)  # Wait for map to be valid
            return
            
        if Agent.IsDead(Player.GetAgentID()):
            yield from Routines.Yield.wait(1000)  # Wait if dead
            return 
        
        loot_singleton = LootConfig()
        filtered_agent_ids = loot_singleton.GetfilteredLootArray(distance=Range.Earshot.value, multibox_loot=True, allow_unasigned_loot=True)
        yield from Routines.Yield.Items.LootItems(filtered_agent_ids, pickup_timeout=pickup_timeout)
        
    @_yield_step(label="AddModelToBlacklist", counter_key="ADD_MODEL_TO_BLACKLIST")
    def add_model_to_blacklist(self, model_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.AddToBlacklist(model_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is added

    @_yield_step(label="RemoveModelFromBlacklist", counter_key="REMOVE_MODEL_FROM_BLACKLIST")
    def remove_model_from_blacklist(self, model_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.RemoveFromBlacklist(model_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is removed

    @_yield_step(label="AddModelToWhitelist", counter_key="ADD_MODEL_TO_WHITELIST")
    def add_model_to_whitelist(self, model_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.AddToWhitelist(model_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is added
        
    @_yield_step(label="RemoveModelFromWhitelist", counter_key="REMOVE_MODEL_FROM_WHITELIST")
    def remove_model_from_whitelist(self, model_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.RemoveFromWhitelist(model_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is removed
        
    @_yield_step(label="ClearWhitelist", counter_key="CLEAR_WHITELIST")
    def clear_whitelist(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.ClearWhitelist()
        yield from Routines.Yield.wait(100)  # Small wait to ensure the whitelist is cleared
        
    @_yield_step(label="ClearBlacklist", counter_key="CLEAR_BLACKLIST") 
    def clear_blacklist(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.ClearBlacklist()
        yield from Routines.Yield.wait(100)  # Small wait to ensure the blacklist is cleared
        

    @_yield_step(label="AddItemIDToWhitelist", counter_key="ADD_ITEM_ID_TO_WHITELIST")
    def add_item_id_to_whitelist(self, item_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_whitelist.add(item_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is added
        
    @_yield_step(label="RemoveItemIDFromWhitelist", counter_key="REMOVE_ITEM_ID_FROM_WHITELIST")
    def remove_item_id_from_whitelist(self, item_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_whitelist.discard(item_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is removed
        
    @_yield_step(label="ClearItemIDWhitelist", counter_key="CLEAR_ITEM_ID_WHITELIST")
    def clear_item_id_whitelist(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_whitelist.clear()
        yield from Routines.Yield.wait(100)  # Small wait to ensure the whitelist is cleared
        
    @_yield_step(label="AddItemIDToBlacklist", counter_key="ADD_ITEM_ID_TO_BLACKLIST")
    def add_item_id_to_blacklist(self, item_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_blacklist.add(item_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is added
        
    @_yield_step(label="RemoveItemIDFromBlacklist", counter_key="REMOVE_ITEM_ID_FROM_BLACKLIST")
    def remove_item_id_from_blacklist(self, item_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_blacklist.discard(item_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the item is removed
        
    @_yield_step(label="ClearItemIDBlacklist", counter_key="CLEAR_ITEM_ID_BLACKLIST")
    def clear_item_id_blacklist(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.item_id_blacklist.clear()
        yield from Routines.Yield.wait(100)  # Small wait to ensure the blacklist is cleared
        
        
    @_yield_step(label="AddDyeToWhitelist", counter_key="ADD_DYE_TO_WHITELIST")
    def add_dye_to_whitelist(self, dye_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.dye_whitelist.add(dye_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the dye is added
        
    @_yield_step(label="RemoveDyeFromWhitelist", counter_key="REMOVE_DYE_FROM_WHITELIST")
    def remove_dye_from_whitelist(self, dye_id:int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
        loot_singleton = LootConfig()
        loot_singleton.dye_whitelist.discard(dye_id)
        yield from Routines.Yield.wait(100)  # Small wait to ensure the dye is removed
        
    @_yield_step(label="ClearDyeWhitelist", counter_key="CLEAR_DYE_WHITELIST")
    def clear_dye_whitelist(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        from ...py4gwcorelib_src.Lootconfig_src import LootConfig
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

    def _equip_inventory_bag(self, model_id: int, target_bag: int, timeout_ms: int = 2500):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        from ...enums import Bags
        import Py4GW

        def _bag_is_populated() -> bool:
            target_container_item = GLOBAL_CACHE.Inventory.GetBagContainerItem(target_bag)
            target_bag_size = GLOBAL_CACHE.Inventory.GetBagSize(target_bag)
            return target_container_item != 0 or target_bag_size > 0

        if _bag_is_populated():
            return True

        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if not item_id:
            ConsoleLog(
                "EquipInventoryBag",
                f"Item model {model_id} not found in inventory.",
                Py4GW.Console.MessageType.Error,
            )
            self._Events.on_unmanaged_fail()
            return False

        GLOBAL_CACHE.Inventory.UseItem(item_id)

        poll_interval_ms = 125
        native_attempt_timeout_ms = min(timeout_ms, 250)
        elapsed_ms = 0
        while elapsed_ms <= native_attempt_timeout_ms:
            if _bag_is_populated():
                return True
            if elapsed_ms >= native_attempt_timeout_ms:
                break
            yield from Routines.Yield.wait(poll_interval_ms)
            elapsed_ms += poll_interval_ms

        if GLOBAL_CACHE.Inventory.MoveModelToBagSlot(model_id, Bags.Backpack, 0):
            ConsoleLog(
                "EquipInventoryBag",
                f"Native UseItem did not populate bag {target_bag}; trying backpack slot double-click fallback for model {model_id}.",
                Py4GW.Console.MessageType.Warning,
                log=False,
            )
            yield from Routines.Yield.wait(250)
            yield from self.parent.helpers.UI.iter_open_all_bags()
            yield from Routines.Yield.wait(125)
            yield from self.parent.helpers.UI.iter_bag_item_double_click(Bags.Backpack, 0)
            if _bag_is_populated():
                return True
        else:
            ConsoleLog(
                "EquipInventoryBag",
                f"Fallback move to backpack slot 0 failed for model {model_id}.",
                Py4GW.Console.MessageType.Warning,
                log=False,
            )

        elapsed_ms = 0
        while elapsed_ms <= timeout_ms:
            if _bag_is_populated():
                return True
            if elapsed_ms >= timeout_ms:
                break
            yield from Routines.Yield.wait(poll_interval_ms)
            elapsed_ms += poll_interval_ms

        ConsoleLog(
            "EquipInventoryBag",
            (
                f"Failed to equip model {model_id} item {item_id} into bag {target_bag} within {timeout_ms}ms. "
                f"container_item={GLOBAL_CACHE.Inventory.GetBagContainerItem(target_bag)} "
                f"size={GLOBAL_CACHE.Inventory.GetBagSize(target_bag)}."
            ),
            Py4GW.Console.MessageType.Error,
        )
        self._Events.on_unmanaged_fail()
        return False

    @_yield_step(label="EquipInventoryBag", counter_key="EQUIP_INVENTORY_BAG")
    def equip_inventory_bag(self, model_id: int, target_bag: int, timeout_ms: int = 2500):
        return (yield from self._equip_inventory_bag(model_id, target_bag, timeout_ms))

    def _equip_on_hero(self, hero_type, model_id: int):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        import Py4GW
        from ...Py4GWcorelib import ConsoleLog
        from ...enums_src.Hero_enums import HeroType

        hero_count = GLOBAL_CACHE.Party.GetHeroCount()
        for position in range(1, hero_count + 1):
            hero_agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(position)
            if hero_agent_id <= 0:
                continue
            hero_id = GLOBAL_CACHE.Party.Heroes.GetHeroIDByAgentID(hero_agent_id)
            if hero_id <= 0:
                continue
            try:
                found_hero_type = HeroType(hero_id)
            except ValueError:
                continue
            if found_hero_type == hero_type:
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                if not item_id:
                    ConsoleLog("EquipOnHero", f"Item model {model_id} not found in inventory.", Py4GW.Console.MessageType.Error)
                    self._Events.on_unmanaged_fail()
                    return False
                GLOBAL_CACHE.Inventory.EquipItem(item_id, hero_agent_id)
                yield from Routines.Yield.wait(750)
                return True

        ConsoleLog("EquipOnHero", f"Hero {hero_type} not found in party.", Py4GW.Console.MessageType.Warning)
        return False

    @_yield_step(label="EquipOnHero", counter_key="EQUIP_ON_HERO")
    def equip_on_hero(self, hero_type, model_id: int):
        return (yield from self._equip_on_hero(hero_type, model_id))


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
        
    @_yield_step(label="WithdrawGold", counter_key="WITHDRAW_GOLD")
    def withdraw_gold(self, target_gold: int = 20000, deposit_all: bool = True) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        yield from Routines.Yield.Items.WithdrawGold(target_gold, deposit_all)

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

    @_yield_step(label="WithdrawUpTo", counter_key="WITHDRAW_UP_TO")
    def withdraw_up_to(self, model_id: int, max_quantity: int) -> Generator[Any, Any, None]:
        """Withdraw up to max_quantity of model_id from storage. No-op if none available."""
        from ...Routines import Routines
        yield from Routines.Yield.Items.WithdrawUpTo(model_id, max_quantity)

    @_yield_step(label="WithdrawFirstAvailable", counter_key="WITHDRAW_FIRST_AVAILABLE")
    def withdraw_first_available(self, model_ids: list, max_quantity: int) -> Generator[Any, Any, None]:
        """Withdraw up to max_quantity from the first model_id in the list that has stock in storage."""
        from ...Routines import Routines
        yield from Routines.Yield.Items.WithdrawFirstAvailable(model_ids, max_quantity)

    @_yield_step(label="DepositAllInventory", counter_key="DEPOSIT_ALL_INVENTORY")
    def deposit_all_inventory(self) -> Generator[Any, Any, None]:
        """Deposits all items from inventory bags to storage."""
        from ...Routines import Routines
        yield from Routines.Yield.Items.DepositAllInventory()

    @_yield_step(label="DepositItem", counter_key="DEPOSIT_ITEM")
    def deposit_item(self, model_id: int) -> Generator[Any, Any, bool]:
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if not item_id:
            return True  # nothing to deposit
        GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
        yield from Routines.Yield.wait(350)
        return True

    def _deposit_model_list(self, model_ids: list[int]) -> Generator[Any, Any, bool]:
        """Deposit all inventory stacks matching any model ID in the list."""
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        deposited_any = False
        for model_id in model_ids:
            while True:
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                if not item_id:
                    break
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                deposited_any = True
                yield from Routines.Yield.wait(350)
        return deposited_any

    @_yield_step(label="DepositConset", counter_key="DEPOSIT_CONSET")
    def deposit_conset(self) -> Generator[Any, Any, bool]:
        conset_models = [
            ModelID.Essence_Of_Celerity.value,
            ModelID.Grail_Of_Might.value,
            ModelID.Armor_Of_Salvation.value,
        ]
        return (yield from self._deposit_model_list(conset_models))

    @_yield_step(label="DepositPcons", counter_key="DEPOSIT_PCONS")
    def deposit_pcons(self) -> Generator[Any, Any, bool]:
        pcons_models = [
            ModelID.Birthday_Cupcake.value,
            ModelID.Candy_Apple.value,
            ModelID.Golden_Egg.value,
            ModelID.Candy_Corn.value,
            ModelID.Honeycomb.value,
            ModelID.War_Supplies.value,
            ModelID.Slice_Of_Pumpkin_Pie.value,
            ModelID.Drake_Kabob.value,
            ModelID.Bowl_Of_Skalefin_Soup.value,
            ModelID.Pahnai_Salad.value,
            ModelID.Scroll_Of_Resurrection.value,
        ]
        return (yield from self._deposit_model_list(pcons_models))

    @_yield_step(label="DepositSummoningStones", counter_key="DEPOSIT_SUMMONING_STONES")
    def deposit_summoning_stones(self) -> Generator[Any, Any, bool]:
        summoning_models = [
            ModelID.Legionnaire_Summoning_Crystal.value,
            ModelID.Igneous_Summoning_Stone.value,
            ModelID.Amber_Summon.value,
            ModelID.Arctic_Summon.value,
            ModelID.Automaton_Summon.value,
            ModelID.Celestial_Summon.value,
            ModelID.Chitinous_Summon.value,
            ModelID.Demonic_Summon.value,
            ModelID.Fossilized_Summon.value,
            ModelID.Frosty_Summon.value,
            ModelID.Gelatinous_Summon.value,
            ModelID.Ghastly_Summon.value,
            ModelID.Imperial_Guard_Summon.value,
            ModelID.Jadeite_Summon.value,
            ModelID.Merchant_Summon.value,
            ModelID.Mischievous_Summon.value,
            ModelID.Mysterious_Summon.value,
            ModelID.Mystical_Summon.value,
            ModelID.Shining_Blade_Summon.value,
            ModelID.Tengu_Summon.value,
            ModelID.Zaishen_Summon.value,
        ]
        return (yield from self._deposit_model_list(summoning_models))

    @_yield_step(label="DepositCitySpeedBoost", counter_key="DEPOSIT_CITY_SPEED_BOOST")
    def deposit_city_speed_boost(self) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        city_speed_models = [
            model.value if hasattr(model, "value") else int(model)
            for model in Routines.Yield.Upkeepers.CITY_SPEED_ITEMS
        ]
        return (yield from self._deposit_model_list(city_speed_models))

    @_yield_step(label="DepositConsetPconsSummoningStonesCitySpeed", counter_key="DEPOSIT_CONSET_PCONS_SUMMON_STONES_CITY_SPEED")
    def deposit_conset_pcons_summoning_stones_city_speed(self) -> Generator[Any, Any, bool]:
        """Deposit conset, pcons, summoning stones, and city speed boost items."""
        from ...Routines import Routines
        deposited = False

        conset_models = [
            ModelID.Essence_Of_Celerity.value,
            ModelID.Grail_Of_Might.value,
            ModelID.Armor_Of_Salvation.value,
        ]
        if (yield from self._deposit_model_list(conset_models)):
            deposited = True

        pcons_models = [
            ModelID.Birthday_Cupcake.value,
            ModelID.Candy_Apple.value,
            ModelID.Golden_Egg.value,
            ModelID.Candy_Corn.value,
            ModelID.Honeycomb.value,
            ModelID.War_Supplies.value,
            ModelID.Slice_Of_Pumpkin_Pie.value,
            ModelID.Drake_Kabob.value,
            ModelID.Bowl_Of_Skalefin_Soup.value,
            ModelID.Pahnai_Salad.value,
            ModelID.Scroll_Of_Resurrection.value,
        ]
        if (yield from self._deposit_model_list(pcons_models)):
            deposited = True

        summoning_models = [
            ModelID.Legionnaire_Summoning_Crystal.value,
            ModelID.Igneous_Summoning_Stone.value,
            ModelID.Amber_Summon.value,
            ModelID.Arctic_Summon.value,
            ModelID.Automaton_Summon.value,
            ModelID.Celestial_Summon.value,
            ModelID.Chitinous_Summon.value,
            ModelID.Demonic_Summon.value,
            ModelID.Fossilized_Summon.value,
            ModelID.Frosty_Summon.value,
            ModelID.Gelatinous_Summon.value,
            ModelID.Ghastly_Summon.value,
            ModelID.Imperial_Guard_Summon.value,
            ModelID.Jadeite_Summon.value,
            ModelID.Merchant_Summon.value,
            ModelID.Mischievous_Summon.value,
            ModelID.Mysterious_Summon.value,
            ModelID.Mystical_Summon.value,
            ModelID.Shining_Blade_Summon.value,
            ModelID.Tengu_Summon.value,
            ModelID.Zaishen_Summon.value,
        ]
        if (yield from self._deposit_model_list(summoning_models)):
            deposited = True

        city_speed_models = [
            model.value if hasattr(model, "value") else int(model)
            for model in Routines.Yield.Upkeepers.CITY_SPEED_ITEMS
        ]
        if (yield from self._deposit_model_list(city_speed_models)):
            deposited = True

        return deposited

    @_yield_step(label="UseAllConsumables", counter_key="USE_ALL_CONSUMABLES")
    def use_all_consumables(self) -> Generator[Any, Any, None]:
        """
        Uses all consumables for the current player only (not multibox).
        Only uses a consumable if its effect is not already active.
        """
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE

        # Map consumable model_id to their effect skill_id (as used in multibox)
        consumable_effects = [
            (ModelID.Essence_Of_Celerity.value, GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect")),
            (ModelID.Grail_Of_Might.value, GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect")),
            (ModelID.Armor_Of_Salvation.value, GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect")),
            (ModelID.Birthday_Cupcake.value, GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill")),
            (ModelID.Golden_Egg.value, GLOBAL_CACHE.Skill.GetID("Golden_Egg_skill")),
            (ModelID.Candy_Corn.value, GLOBAL_CACHE.Skill.GetID("Candy_Corn_skill")),
            (ModelID.Candy_Apple.value, GLOBAL_CACHE.Skill.GetID("Candy_Apple_skill")),
            (ModelID.Slice_Of_Pumpkin_Pie.value, GLOBAL_CACHE.Skill.GetID("Pie_Induced_Ecstasy")),
            (ModelID.Drake_Kabob.value, GLOBAL_CACHE.Skill.GetID("Drake_Skin")),
            (ModelID.Bowl_Of_Skalefin_Soup.value, GLOBAL_CACHE.Skill.GetID("Skale_Vigor")),
            (ModelID.Pahnai_Salad.value, GLOBAL_CACHE.Skill.GetID("Pahnai_Salad_item_effect")),
            (ModelID.War_Supplies.value, GLOBAL_CACHE.Skill.GetID("Well_Supplied")),
        ]
        
        # Wait for any prior game action to finish before using items
        yield from Routines.Yield.wait(500)

        # Check for each consumable if the effect is already active
        for consumable_model_id, effect_skill_id in consumable_effects:
            # Check if effect is already active
            if hasattr(GLOBAL_CACHE, "Effects") and callable(getattr(GLOBAL_CACHE.Effects, "HasEffect", None)):
                if GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), effect_skill_id):
                    continue
            # Fallback: try Inventory.HasEffect if Effects is not available
            elif hasattr(GLOBAL_CACHE.Inventory, "HasEffect") and callable(getattr(GLOBAL_CACHE.Inventory, "HasEffect", None)):
                if GLOBAL_CACHE.Inventory.HasEffect(Player.GetAgentID(), effect_skill_id):
                    continue
            # Otherwise, just proceed (may overuse if no effect check is available)
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(consumable_model_id)
            if item_id:
                GLOBAL_CACHE.Inventory.UseItem(item_id)
                yield from Routines.Yield.wait(500)

    @_yield_step(label="UseConset", counter_key="USE_CONSET")
    def use_conset(self) -> Generator[Any, Any, None]:
        """
        Uses only conset items (Essence of Celerity, Grail of Might, Armor of Salvation)
        for the current player. Skips any whose effect is already active.
        """
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE

        conset_effects = [
            (ModelID.Essence_Of_Celerity.value, GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect")),
            (ModelID.Grail_Of_Might.value,       GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect")),
            (ModelID.Armor_Of_Salvation.value,   GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect")),
        ]

        yield from Routines.Yield.wait(500)

        for consumable_model_id, effect_skill_id in conset_effects:
            if hasattr(GLOBAL_CACHE, "Effects") and callable(getattr(GLOBAL_CACHE.Effects, "HasEffect", None)):
                if GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), effect_skill_id):
                    continue
            elif hasattr(GLOBAL_CACHE.Inventory, "HasEffect") and callable(getattr(GLOBAL_CACHE.Inventory, "HasEffect", None)):
                if GLOBAL_CACHE.Inventory.HasEffect(Player.GetAgentID(), effect_skill_id):
                    continue
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(consumable_model_id)
            if item_id:
                GLOBAL_CACHE.Inventory.UseItem(item_id)
                yield from Routines.Yield.wait(500)

    @_yield_step(label="UsePcons", counter_key="USE_PCONS")
    def use_pcons(self) -> Generator[Any, Any, None]:
        """
        Uses only pcon items (Birthday Cupcake, Golden Egg, Candy Corn, Candy Apple,
        Pumpkin Pie, Drake Kabob, Skalefin Soup, Pahnai Salad, War Supplies)
        for the current player. Skips any whose effect is already active.
        """
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE

        pcon_effects = [
            (ModelID.Birthday_Cupcake.value,      GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill")),
            (ModelID.Golden_Egg.value,             GLOBAL_CACHE.Skill.GetID("Golden_Egg_skill")),
            (ModelID.Candy_Corn.value,             GLOBAL_CACHE.Skill.GetID("Candy_Corn_skill")),
            (ModelID.Candy_Apple.value,            GLOBAL_CACHE.Skill.GetID("Candy_Apple_skill")),
            (ModelID.Slice_Of_Pumpkin_Pie.value,  GLOBAL_CACHE.Skill.GetID("Pie_Induced_Ecstasy")),
            (ModelID.Drake_Kabob.value,            GLOBAL_CACHE.Skill.GetID("Drake_Skin")),
            (ModelID.Bowl_Of_Skalefin_Soup.value, GLOBAL_CACHE.Skill.GetID("Skale_Vigor")),
            (ModelID.Pahnai_Salad.value,           GLOBAL_CACHE.Skill.GetID("Pahnai_Salad_item_effect")),
            (ModelID.War_Supplies.value,           GLOBAL_CACHE.Skill.GetID("Well_Supplied")),
        ]

        yield from Routines.Yield.wait(500)

        for consumable_model_id, effect_skill_id in pcon_effects:
            if hasattr(GLOBAL_CACHE, "Effects") and callable(getattr(GLOBAL_CACHE.Effects, "HasEffect", None)):
                if GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), effect_skill_id):
                    continue
            elif hasattr(GLOBAL_CACHE.Inventory, "HasEffect") and callable(getattr(GLOBAL_CACHE.Inventory, "HasEffect", None)):
                if GLOBAL_CACHE.Inventory.HasEffect(Player.GetAgentID(), effect_skill_id):
                    continue
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(consumable_model_id)
            if item_id:
                GLOBAL_CACHE.Inventory.UseItem(item_id)
                yield from Routines.Yield.wait(500)

    @_yield_step(label="UseSummoningStone", counter_key="USE_SUMMONING_STONE")
    def use_summoning_stone(self) -> Generator[Any, Any, None]:
        """
        Uses a summoning stone from inventory with priority:
        1. Legionnaire Summoning Crystal (always first)
        2. Igneous Summoning Stone (if player level < 20)
        3. Any other available summoning stone
        """
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        from ...Player import Player
        from ...Map import Map
        from ...Py4GWcorelib import ConsoleLog
        import Py4GW

        # Never use summoning stones in The Norn Fighting Tournament.
        if Map.GetMapID() == 700:
            return
        
        # Priority 1: Legionnaire Summoning Crystal
        legionnaire_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Legionnaire_Summoning_Crystal.value)
        if legionnaire_id:
            GLOBAL_CACHE.Inventory.UseItem(legionnaire_id)
            ConsoleLog("UseSummoningStone", "Used Legionnaire Summoning Crystal", Py4GW.Console.MessageType.Info, log=False)
            yield from Routines.Yield.wait(500)
            return
        
        # Priority 2: Igneous Summoning Stone (if under level 20)
        player_level = Player.GetLevel()
        if player_level < 20:
            igneous_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Igneous_Summoning_Stone.value)
            if igneous_id:
                GLOBAL_CACHE.Inventory.UseItem(igneous_id)
                ConsoleLog("UseSummoningStone", "Used Igneous Summoning Stone", Py4GW.Console.MessageType.Info, log=False)
                yield from Routines.Yield.wait(500)
                return
        
        # Priority 3: Other summoning stones
        other_summons = [
            ModelID.Amber_Summon.value,
            ModelID.Arctic_Summon.value,
            ModelID.Automaton_Summon.value,
            ModelID.Celestial_Summon.value,
            ModelID.Chitinous_Summon.value,
            ModelID.Demonic_Summon.value,
            ModelID.Fossilized_Summon.value,
            ModelID.Frosty_Summon.value,
            ModelID.Gelatinous_Summon.value,
            ModelID.Ghastly_Summon.value,
            ModelID.Imperial_Guard_Summon.value,
            ModelID.Jadeite_Summon.value,
            ModelID.Merchant_Summon.value,
            ModelID.Mischievous_Summon.value,
            ModelID.Mysterious_Summon.value,
            ModelID.Mystical_Summon.value,
            ModelID.Shining_Blade_Summon.value,
            ModelID.Tengu_Summon.value,
            ModelID.Zaishen_Summon.value,
        ]
        
        for summon_model in other_summons:
            item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(summon_model)
            if item_id:
                GLOBAL_CACHE.Inventory.UseItem(item_id)
                ConsoleLog("UseSummoningStone", f"Used summoning stone (model_id: {summon_model})", Py4GW.Console.MessageType.Info, log=False)
                yield from Routines.Yield.wait(500)
                return
        
        # No summoning stones found
        ConsoleLog("UseSummoningStone", "No summoning stones found in inventory", Py4GW.Console.MessageType.Debug)

    @_yield_step(label="UseItemByModelID", counter_key="USE_ITEM_BY_MODEL_ID")
    def use_item_by_model_id(self, model_id: int) -> Generator[Any, Any, None]:
        """Find the first item with the given model_id in inventory and use it."""
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if item_id:
            GLOBAL_CACHE.Inventory.UseItem(item_id)
            yield from Routines.Yield.wait(1000)
