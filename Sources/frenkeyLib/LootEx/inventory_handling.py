from datetime import date, datetime, timedelta
import re
import re
from typing import Any, Callable, Generator, override
from Py4GWCoreLib.Builds.SF_Ass_vaettir import SF_Ass_vaettir
from Py4GWCoreLib.GlobalCache.ItemCache import Bag_enum
from Py4GWCoreLib.botting_src.helpers import BottingHelpers
from Py4GWCoreLib.botting_src.helpers_src.Merchant import _Merchant
from Py4GWCoreLib.botting_src.helpers_src.decorators import yield_step
from Py4GWCoreLib.botting_src.subclases_src.MERCHANT_src import _MERCHANTS
from Py4GWCoreLib.py4gwcorelib_src.MerchantHandler import MerchantHandler
from Sources.frenkeyLib.Core.utility import string_similarity
from Sources.frenkeyLib.LootEx.crafting import BuildCraftingQueueFromCrafter, CraftingAction, CraftingCoroutine
from Sources.frenkeyLib.LootEx.data_collection import DataCollector
from Sources.frenkeyLib.LootEx.enum import ITEM_CONVERSIONS, XUNLAI_STORAGE, ActionState, MaterialType, MerchantType, ModType, SalvageKitOption, SalvageOption, ItemAction
from Py4GWCoreLib import *
from Sources.frenkeyLib.LootEx import loot_handling, models, settings, utility, ui_manager_extensions, item_configuration, cache
from Sources.frenkeyLib.LootEx.instance_manager import InstanceManager
from Sources.frenkeyLib.LootEx.salvaging import SalvageAction
from Sources.frenkeyLib.LootEx.trading import ActionType, TraderAction

# TODO: Collect salvage data for items, so we can make better decisions on what to salvage and what not to salvage.
# TODO: Add sorting options for the inventory and storage.
# TODO: Add options to mark accounts as data collectors and allow salvaging of unknown items on other accounts
# TODO: Fix the bug of items not getting processed fully but handler stopping after a few items
# TODO: Add a way to determine which trader is open and which items are available for trading

salvagetime_results = []
actiontime_results = []
identifytime_results = []
merhcant_time_results = []
actiontime_results = []
time_results = []

class LootExAutoInventoryHandler(AutoInventoryHandler):
    LOG_LOOTEX_AUTO_INVENTORY_HANDLER = True
    _lootex_instance = None

    def __new__(cls, inventory_handler: 'InventoryHandler|None' = None):
        # create only once
        if cls._lootex_instance is None:
            # force creation of subclass instance — bypass parent __new__
            ConsoleLog("LootExAutoInventoryHandler", "Creating new LootExAutoInventoryHandler instance.", Console.MessageType.Debug, cls.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
            obj = object.__new__(cls)
            obj._initialized = False

            cls._lootex_instance = obj

        return cls._lootex_instance

    def __init__(self, inventory_handler: 'InventoryHandler|None' = None):
        if self._initialized:
            return
        
        ConsoleLog("LootExAutoInventoryHandler", "Initializing LootExAutoInventoryHandler instance.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
        super().__init__()        

        self.inventory_handler = inventory_handler
        self._initialized = True
        
        
    # @override
    # def AutoID(self, item_id):
    #     # Let LootEx handle identification
    #     ConsoleLog("LootExAutoInventoryHandler", f"AutoID called for item_id: {item_id}. Let LootEx handle identification.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
    #     pass       
    
    # @override
    # def AutoSalvage(self, item_id):
    #     # Let LootEx handle salvaging
    #     ConsoleLog("LootExAutoInventoryHandler", f"AutoSalvage called for item_id: {item_id}. Let LootEx handle salvaging.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
    #     pass
    
    @override
    def IdentifyItems(self, progress_callback: Optional[Callable[[float], None]] = None, log: bool = False):
        if not self.inventory_handler or not self.inventory_handler.IsActive:
            ConsoleLog("LootExAutoInventoryHandler", "IdentifyItems called but inventory handler is not active.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
            return
        
        if not self.inventory_handler.identification_kits:
            ConsoleLog("LootExAutoInventoryHandler", "IdentifyItems called but no identification kits available.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
            return
        
        while True:
            items_to_identify = [item for item in self.inventory_handler.actions.values() if item.action == ItemAction.Identify and not item.is_identified]
            
            if not items_to_identify:
                ConsoleLog("LootExAutoInventoryHandler", "No items left to identify.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
                return
            
            ConsoleLog("LootExAutoInventoryHandler", f"Identifying {len(items_to_identify)} items.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
            
            for item in items_to_identify:
                ConsoleLog("LootExAutoInventoryHandler", f"Item to identify: {item.data.name if item.data else item.name}.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
                
            yield from Routines.Yield.wait(250)
                
    @override
    def SalvageItems(self, progress_callback: Optional[Callable[[float], None]] = None, log: bool = False):
        if not self.inventory_handler or not self.inventory_handler.IsActive:
            ConsoleLog("LootExAutoInventoryHandler", "SalvageItems called but inventory handler is not active.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
            return
        
        while True:            
            salvage_queue = self.inventory_handler.salvaging_queue
            
            if not salvage_queue:
                ConsoleLog("LootExAutoInventoryHandler", "No items left to salvage.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
                return
            
            salvages_with_expert_kit = [salvage for salvage in salvage_queue.values() if salvage.item.salvage_option in [SalvageOption.RareCraftingMaterials, SalvageOption.Prefix, SalvageOption.Suffix, SalvageOption.Inherent]]
            salvages_with_lesser_kit = [salvage for salvage in salvage_queue.values() if salvage.item.salvage_option in [SalvageOption.LesserCraftingMaterials]]
            salvages_with_any_kit = [salvage for salvage in salvage_queue.values() if salvage.item.salvage_option in [SalvageOption.CraftingMaterials]]
            
            can_salvage = bool(salvages_with_expert_kit and self.inventory_handler.expert_salvage_kits)
            can_salvage |= bool(salvages_with_lesser_kit and self.inventory_handler.lesser_salvage_kits)
            can_salvage |= bool(salvages_with_any_kit and (self.inventory_handler.lesser_salvage_kits or self.inventory_handler.expert_salvage_kits))
            
            if not can_salvage:
                ConsoleLog("LootExAutoInventoryHandler", "No salvage kits available for the items left to salvage.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
                return
            
            ConsoleLog("LootExAutoInventoryHandler", f"Salvaging {len(salvage_queue)} items.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)            
            
            yield from Routines.Yield.wait(250)
        
    @override
    def DepositItemsAuto(self):
        if not self.inventory_handler or not self.inventory_handler.IsActive:
            ConsoleLog("LootExAutoInventoryHandler", "DepositItemsAuto called but inventory handler is not active.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
            return
        
        if not self.inventory_handler.identification_kits:
            ConsoleLog("LootExAutoInventoryHandler", "DepositItemsAuto called but no identification kits available.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
            return
        
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        while True:
            items_to_stash = [item for item in self.inventory_handler.actions.values() if item.action == ItemAction.Deposit_Material or item.action == ItemAction.Stash]
            
            if not items_to_stash:
                ConsoleLog("LootExAutoInventoryHandler", "No items left to deposit.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
                return
            
            
            storage, _ = utility.Util.GetZeroFilledBags(
                Bag.Storage_1, Bag(settings.max_xunlai_storage.value))
            
            free_slot = any(id == 0 for id in storage)
            if not free_slot:
                ConsoleLog("LootExAutoInventoryHandler", "No free slots in storage to deposit items.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
                return
            
            ConsoleLog("LootExAutoInventoryHandler", f"Depositing {len(items_to_stash)} items.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
            
            yield from Routines.Yield.wait(250)
    
    @override
    def IDAndSalvageItems(self, progress_callback: Optional[Callable[[float], None]] = None):
        ConsoleLog("LootExAutoInventoryHandler", "IDAndSalvageItems called.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
        
        yield from self.IdentifyItems(progress_callback)
        yield from self.SalvageItems(progress_callback)
    
    @override
    def IDSalvageDepositItems(self):
        ConsoleLog("LootExAutoInventoryHandler", "IDSalvageDepositItems called.", Console.MessageType.Debug, self.LOG_LOOTEX_AUTO_INVENTORY_HANDLER)
        
        yield from self.IdentifyItems()
        yield from self.SalvageItems()
        yield from self.DepositItemsAuto()    

class LootEx_Merchant_Handler(MerchantHandler):
    _lootex_instance = None
    _initialized = False
    
    LOG_LOOTEX_MERCHANT_HANDLER = True
    
    def __new__(cls, inventory_handler : 'InventoryHandler|None' = None):
        if cls._lootex_instance is None:
            # force creation of subclass instance — bypass parent __new__
            obj = object.__new__(cls)
            obj._initialized = False
            ConsoleLog("LootEx_Merchant_Handler", "Creating new LootEx_Merchant_Handler instance.", Console.MessageType.Debug, cls.LOG_LOOTEX_MERCHANT_HANDLER)
            
            cls._lootex_instance = obj
        return cls._lootex_instance
    
    def __init__(self, inventory_handler : 'InventoryHandler|None' = None) -> None:
        if self._initialized:
            return
        
        ConsoleLog("LootEx_Merchant_Handler", "Initializing LootEx_Merchant_Handler instance.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
        super().__init__()

        self.inventory_handler = inventory_handler
        self._initialized = True
        
        LootEx_Merchant_Handler._initialized = True

    @override
    def sell_materials_to_merchant(self, _events) -> Generator[Any, Any, None]:
        if not self.inventory_handler or not self.inventory_handler.IsActive:
            ConsoleLog("LootEx_Merchant_Handler", "Sell materials to merchant called but inventory handler is not active.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
            return
        
        while True:
            items_to_sell = [item for item in self.inventory_handler.actions.values() if item.action == ItemAction.Sell_To_Merchant and item.item_type == ItemType.Materials_Zcoins]
            
            if not items_to_sell:
                ConsoleLog("LootEx_Merchant_Handler", "No materials to sell to merchant.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
                return
            
            yield
    
    @override
    def restock_identification_kits(self, config) -> Generator[Any, Any, None]:
        if not self.inventory_handler or not self.inventory_handler.IsActive:
            ConsoleLog("LootEx_Merchant_Handler", "Restock identification kits called but inventory handler is not active.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
            return
        
        while True:            
            items_to_buy = self.inventory_handler.GetMissingItems()
            identification_kits = items_to_buy.get(ModelID.Superior_Identification_Kit, None)
            
            if identification_kits is None or identification_kits[1] <= 0:
                ConsoleLog("LootEx_Merchant_Handler", "No identification kits to restock.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
                return
            
            
            merchant_item_list = Trading.Merchant.GetOfferedItems()
            gold_on_character = Inventory.GetGoldOnCharacter()
            model_id = ModelID.Superior_Identification_Kit.value
            item_type = ItemType.Kit
            item_id = next((
                item for item in merchant_item_list if Item.GetModelID(item) == model_id and Item.GetItemType(item)[0] == item_type.value), None)
            
            if item_id is not None:
                value = Item.Properties.GetValue(item_id) * 2
                if gold_on_character <= value:
                    ConsoleLog("LootEx_Merchant_Handler", "Cannot afford identification kits to restock.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
                    return
                
                ConsoleLog("LootEx_Merchant_Handler", f"Restocking {identification_kits[1]} Identification Kits.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
                yield
            
            else:
                # Fallback to normal identification kits if superior kits are not available
                model_id = ModelID.Identification_Kit.value
                item_id = next((
                    item for item in merchant_item_list if Item.GetModelID(item) == model_id and Item.GetItemType(item)[0] == item_type.value), None)
                if item_id is not None:
                    value = Item.Properties.GetValue(item_id) * 2
                    if gold_on_character <= value:
                        ConsoleLog("LootEx_Merchant_Handler", "Cannot afford identification kits to restock.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
                        return
                    
                    ConsoleLog("LootEx_Merchant_Handler", f"Restocking {identification_kits[1]} Identification Kits.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
                    yield
                
            
    @override
    def restock_salvage_kits(self, config) -> Generator[Any, Any, None]:
        if not self.inventory_handler or not self.inventory_handler.IsActive:
            ConsoleLog("LootEx_Merchant_Handler", "Restock salvage kits called but inventory handler is not active.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
            return
        
        while True:
            items_to_buy = self.inventory_handler.GetMissingItems()
            salvage_kits = items_to_buy.get(ModelID.Salvage_Kit, None)
            expert_salvage_kits = items_to_buy.get(ModelID.Expert_Salvage_Kit, None)
            
            if (salvage_kits is None or salvage_kits[1] <= 0) and (expert_salvage_kits is None or expert_salvage_kits[1] <= 0):
                ConsoleLog("LootEx_Merchant_Handler", "No salvage kits to restock.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
                return
                
            merchant_item_list = Trading.Merchant.GetOfferedItems()
            gold_on_character = Inventory.GetGoldOnCharacter()
            can_afford = False
            
            if salvage_kits is not None and salvage_kits[1] > 0:
                model_id = ModelID.Salvage_Kit.value
                item_type = ItemType.Kit

                item_id = next((
                item for item in merchant_item_list if Item.GetModelID(item) == model_id and Item.GetItemType(item)[0] == item_type.value), None)
                if item_id is not None:
                    value = Item.Properties.GetValue(item_id) * 2
                    if gold_on_character >= value:
                        can_afford = True
                        ConsoleLog("LootEx_Merchant_Handler", f"Restocking {salvage_kits[1]} Salvage Kits.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
                        yield
                        
            if expert_salvage_kits is not None and expert_salvage_kits[1] > 0:
                model_id = ModelID.Expert_Salvage_Kit.value
                item_type = ItemType.Kit

                item_id = next((
                item for item in merchant_item_list if Item.GetModelID(item) == model_id and Item.GetItemType(item)[0] == item_type.value), None)
                if item_id is not None:
                    value = Item.Properties.GetValue(item_id) * 2
                    if gold_on_character >= value:
                        can_afford = True
                        ConsoleLog("LootEx_Merchant_Handler", f"Restocking {expert_salvage_kits[1]} Expert Salvage Kits.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
                        yield
            
            if not can_afford:
                ConsoleLog("LootEx_Merchant_Handler", "Cannot afford any salvage kits to restock.", Console.MessageType.Debug, self.LOG_LOOTEX_MERCHANT_HANDLER)
                return



def DefensiveActions(self):
    player_agent_id = Player.GetAgentID()
    has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id, self.deadly_paradox)
    has_shroud_of_distress = Routines.Checks.Effects.HasBuff(player_agent_id, self.shroud_of_distress)
    
    if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.shadow_form)):
        if (yield from self._CastSkillID(self.deadly_paradox,extra_condition=(not has_deadly_paradox), log=False, aftercast_delay=100)):
            ConsoleLog(self.build_name, "Casting Deadly Paradox.", Py4GW.Console.MessageType.Info, log=False)
            
        if (yield from self._CastSkillID(self.shadow_form, log=False, aftercast_delay=1750)):
            ConsoleLog(self.build_name, "Casting Shadow Form.", Py4GW.Console.MessageType.Info, log=False)
            
        if (yield from self._CastSkillID(self.shroud_of_distress,extra_condition=(not has_shroud_of_distress), log=False, aftercast_delay=1750)):
            ConsoleLog(self.build_name, "Casting Shroud of Distress.", Py4GW.Console.MessageType.Info, log=False)
            
SF_Ass_vaettir.DefensiveActions = DefensiveActions

class InventoryHandler:
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(InventoryHandler, cls).__new__(cls)
            cls.instance._initialized = False
        return cls.instance

    def __init__(self, reset: bool = False):
        if self._initialized and not reset:
            return
    
        from Sources.frenkeyLib.LootEx.data import Data
        self.data = Data()
            
        self.instance_manager = InstanceManager(self)
        
        self._initialized = True
        self.run_once = False

        self.inventory_changed: bool = False
        self.deposited = False
        self.can_deposit = True
        
        self.capacity_checked = False
        self.material_capacity = 2500
        
        self.storage_check_timer = ThrottledTimer(2500)
        
        self.scraped_items : dict[tuple[ItemType, int], bool] = {}
        self.actions: dict[int, cache.Cached_Item] = {}

        # Initialize timers and action queues
        self.salvage_timer = ThrottledTimer(750)
        self.identification_timer = ThrottledTimer(500)
        self.merchant_timer = ThrottledTimer(1000)
        self.deposit_timer = ThrottledTimer(5000)
        self.inventory_timer = ThrottledTimer(250)
        self.compact_inventory_timer = ThrottledTimer(250)

        self.salvage_action_queue = ActionQueueNode(150)
        self.inventory_array: list[int] | None = []
        self.inventory_sizes: dict[Bag, int] | None = {}
        self.inventory_materials: list[cache.Cached_Item] = []
        self.material_storage: list[tuple[int, int]] | None = []
        self.item_storage: list[tuple[int, ItemType, int, int]] | None = []

        self.empty_slots: int = -1
        self.cached_inventory: list[cache.Cached_Item] = []
        self.lesser_salvage_kits : list[cache.Cached_Item] = []
        self.expert_salvage_kits : list[cache.Cached_Item] = []
        self.perfect_salvage_kits : list[cache.Cached_Item] = []
        self.identification_kits: list[cache.Cached_Item] = []

        self.merchant_open: bool | None = False
        self.merchant_type: MerchantType = MerchantType.None_
        self.checked_storage_for_merchant_items: bool = False

        self.salvage_queue: dict[int, cache.Cached_Item] = {}
        
        self._active_salvage_action : SalvageAction | None = None
        self.salvaging_queue: dict[int, SalvageAction] = {}
        
        self._active_trader_action : TraderAction | None = None
        self.trading_queue: list[TraderAction] = []
        
        self._active_crafting: CraftingAction | None = None
        self.auto_crafting_queue: list[CraftingAction] = []
        self.crafting_queue: list[CraftingAction] = []
        self.process_crafting = False
        
        self.salvaged = False
        self.salvage_windows_updated: bool = False
        self.salvage_option: SalvageOption = SalvageOption.None_
        self.salvage_requires_confirmation: bool = False
        self.is_confirm_materials_window_open: bool = False
        self.is_salvage_window_open: bool = False
        self.upgrade_open: bool | None = False
        
        self.custom_throttle : ThrottledTimer = ThrottledTimer(1000)
    
    def soft_reset(self):
        self.empty_slots: int = -1
        self.merchant_open = None
        self.salvaged = False
        self.inventory_array = None
        self.item_storage = None
        self.inventory_materials = []
        self.material_storage = None
        self.salvage_windows_updated = False

    def reset(self):
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        self.ResetSalvageWindow()
        self.__init__(reset=True)
        
        self.inventory_changed = True
        self.actions.clear()
        self.cached_inventory.clear()
        
        
        self.SetPollingInterval(
            settings.profile.polling_interval if settings.profile else 1)

    def SetPollingInterval(self, interval: float):
        self.inventory_timer.SetThrottleTime(interval * 1000)

    def GetMaterialStorage(self) -> list[tuple[int, int]]:
        if self.material_storage is None:
            material_storage, _ = utility.Util.GetZeroFilledBags(
                Bag.Material_Storage, Bag.Material_Storage)
            self.material_storage = [
                (item_id, 0)
                for item_id in material_storage
            ]

        return self.material_storage

    def GetItemStorage(self) -> Tuple[list[tuple[int, ItemType, int, int]], list[tuple[int, ItemType, int, int]]]:
        """Get the item storage, which is a list of tuples containing item_id, ItemType, model_id and quantity.
        The list is sorted by item_id, with empty slots (item_id == 0) at the end.

        Returns:
            list[tuple[int, int, int]]: A list of tuples containing item_id, ItemType, model_id and quantity.
        """

        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        if self.item_storage is None:
            storage, _ = utility.Util.GetZeroFilledBags(
                Bag.Storage_1, Bag(settings.max_xunlai_storage.value))
            
            self.item_storage = [
                (item_id, ItemType(Item.GetItemType(item_id)[0]), Item.GetModelID(
                    item_id), Item.Properties.GetQuantity(item_id))
                for item_id in storage
            ]

        sorted = self.item_storage.copy()
        sorted.sort(key=lambda x: (
            x[0] == 0,  # Ensure empty slots are at the end
            x[1],  # Sort by ItemType
            x[2],  # Then by model_id
            -x[3]  # Then by quantity in descending order
        ), reverse=False)

        return self.item_storage, sorted

    def ResetSalvageWindow(self):
        if ui_manager_extensions.UIManagerExtensions.IsSalvageWindowOpen():
            ui_manager_extensions.UIManagerExtensions.CancelSalvageOption()

        elif ui_manager_extensions.UIManagerExtensions.IsConfirmMaterialsWindowOpen():
            ui_manager_extensions.UIManagerExtensions.CancelLesserSalvage()

    def GetSalvageOption(self, item: cache.Cached_Item) -> Optional[SalvageOption]:
        if item.action == ItemAction.Salvage:
            if item.data is None:
                return None

            common_salvage = (item.data.common_salvage.get_average_value(
                item.is_highly_salvageable) if item.data.common_salvage else 0) - 4
            rare_salvage = ((item.data.rare_salvage.get_average_value(
                item.is_highly_salvageable) if item.data.rare_salvage else 0) + common_salvage) - 12
            rare_salvage = rare_salvage / \
                max(1, len(item.data.rare_salvage) +
                    len(item.data.common_salvage))

            # multiplier = 1.5
            # if item.value >= rare_salvage * multiplier and item.value >= common_salvage * multiplier:
            #     return None
            # else:
            return SalvageOption.LesserCraftingMaterials if common_salvage > rare_salvage else SalvageOption.RareCraftingMaterials
        else:
            match item.action:
                case ItemAction.Salvage_Common_Materials:
                    return SalvageOption.LesserCraftingMaterials

                case ItemAction.Salvage_Rare_Materials:
                    return SalvageOption.RareCraftingMaterials

                case _:
                    return SalvageOption.None_

    def GetSalvageKit(self, option: SalvageKitOption = SalvageKitOption.Lesser) -> cache.Cached_Item | None:        
        if option == SalvageKitOption.Lesser:            
            for kit in self.lesser_salvage_kits:
                if kit.is_inventory_item and kit.uses > 0:
                    instance = Item.item_instance(kit.id)
                    if instance and instance.is_inventory_item and instance.uses > 0:
                        return kit          

        if option == SalvageKitOption.LesserOrExpert:                     
            for kit in self.lesser_salvage_kits:
                if kit.is_inventory_item and kit.uses > 0:
                    instance = Item.item_instance(kit.id)
                    if instance and instance.is_inventory_item and instance.uses > 0:
                        return kit 
                                      
            for kit in self.expert_salvage_kits:
                if kit.is_inventory_item and kit.uses > 0:
                    instance = Item.item_instance(kit.id)
                    if instance and instance.is_inventory_item and instance.uses > 0:
                        return kit                    

        if option == SalvageKitOption.Expert:
            for kit in self.expert_salvage_kits:
                if kit.is_inventory_item and kit.uses > 0:
                    instance = Item.item_instance(kit.id)
                    if instance and instance.is_inventory_item and instance.uses > 0:
                        return kit  

        if option == SalvageKitOption.Perfect:
            for kit in self.perfect_salvage_kits:
                if kit.is_inventory_item and kit.uses > 0:
                    instance = Item.item_instance(kit.id)
                    if instance and instance.is_inventory_item and instance.uses > 0:
                        return kit
        
        return None

    def GetIdentificationKit(self) -> cache.Cached_Item | None:
        if not self.identification_kits:
            return None

        for kit in self.identification_kits:
            if kit.is_inventory_item and kit.uses > 0:
                instance = Item.item_instance(kit.id)
                
                if instance and instance.is_inventory_item and instance.uses > 0:
                    return kit

        return None
    
    def GetSalvageKitOption(self, option: SalvageOption) -> SalvageKitOption:
        match option:
            case SalvageOption.Prefix:
                return SalvageKitOption.Expert

            case SalvageOption.Suffix:
                return SalvageKitOption.Expert

            case SalvageOption.Inherent:
                return SalvageKitOption.Expert

            case SalvageOption.LesserCraftingMaterials:
                return SalvageKitOption.Lesser

            case SalvageOption.RareCraftingMaterials:
                return SalvageKitOption.Expert

            case _:
                # Default to Lesser or Expert for any other option which implies crafting materials
                return SalvageKitOption.LesserOrExpert

    def ResetSalvageConfirmation(self):
        # self.salvage_requires_confirmation = False
        pass

    def __Get_Empty_Storage_Slot(self, stash: list[tuple[int, ItemType, int, int]]) -> tuple[int, int, int]:
        for index, (id, _, _, _) in enumerate(stash):
            if id == 0:
                return index, Bag.Storage_1.value + math.floor(index / 25), index % 25

        return -1, -1, -1

    def __Move_Item_To_Empty_Slot(self, stash: list[tuple[int, ItemType, int, int]], item: cache.Cached_Item, amount):
        if amount > 0:
            index, storage_index, storage_slot = self.__Get_Empty_Storage_Slot(
                stash)

            if index == -1:
                # ConsoleLog(
                #     "LootEx", "No empty slot found in stash, cannot stash item.", Console.MessageType.Warning)
                return False

            move_amount = min(250, amount)

            ConsoleLog(
                "LootEx", f"Stashing item {move_amount} '{item.name}' {item.id} to storage {Bag(storage_index)} slot {storage_slot}", Console.MessageType.Info)

            stash[index] = (item.id, item.item_type,
                            item.model_id, move_amount)
            Inventory.MoveItem(item.id, storage_index,
                               storage_slot, move_amount)

    def DropItem(self, item: cache.Cached_Item) -> bool:
        if item.is_inventory_item:
            ConsoleLog(
                "LootEx", f"Dropping {item.quantity}x {item.name} ({item.id})", Console.MessageType.Info)
            GLOBAL_CACHE.Inventory.DropItem(item.id, item.quantity)
            return True
        else:
            ConsoleLog(
                "LootEx", f"Cannot drop item {item.name} ({item.id}), it is not an inventory item.", Console.MessageType.Warning)
            return False
        
    def WithdrawItem(self, item: cache.Cached_Item) -> bool:
        if item.is_stackable and not item.is_inventory_item:
            inventory_item_ids, bag_sizes = utility.Util.GetZeroFilledBags(
                Bag.Backpack, Bag.Bag_2)
            
            inventory = [
                cache.Cached_Item(item_id, slot)
                for slot, item_id in enumerate(inventory_item_ids)
            ]
            
            shared_model_items = [
                inv_item for inv_item in inventory if inv_item.model_id == item.model_id and item.item_type == inv_item.item_type and inv_item.is_stackable
            ]
            
            if shared_model_items:
                for inv_item in shared_model_items:
                    move_amount = min(250 - inv_item.quantity, item.quantity)
                    
                    if move_amount > 0:
                        bag, slot = self.GetBagFromSlot(inv_item.slot, bag_sizes)
                        
                        ConsoleLog(
                            "LootEx", f"Withdrawing {move_amount}x {item.name} ({item.id}) to {inv_item.quantity}x {inv_item.name} in {bag.name} at slot {slot}", Console.MessageType.Info)                            
                        
                        Inventory.MoveItem(
                            item.id, bag.value, slot, move_amount)
                        item.quantity -= move_amount
                        inv_item.quantity += move_amount
                        
                        if item.quantity <= 0:
                            break
            
            if item.quantity > 0:                
                for inv_item in inventory:
                    if inv_item is None or inv_item.id == 0:
                        bag, slot = self.GetBagFromSlot(inv_item.slot, bag_sizes)                        
                        ConsoleLog(
                            "LootEx", f"Withdrawing {item.name} ({item.id}) to {bag.name} slot {slot}", Console.MessageType.Info)    
                        Inventory.MoveItem(item.id, bag.value, slot, item.quantity)
                        return True
                            
        else:
            # Move item to an empty slot in the inventory
            inventory, bag_sizes = utility.Util.GetZeroFilledBags(
                Bag.Backpack, Bag.Bag_2)
            
            for index, item_id in enumerate(inventory):
                if item_id == 0:
                    bag, slot = self.GetBagFromSlot(index, bag_sizes)
                    
                    ConsoleLog(
                        "LootEx", f"Withdrawing {item.name} ({item.id}) to {bag.name} slot {slot}", Console.MessageType.Info)    
                    Inventory.MoveItem(item.id, bag.value, slot, item.quantity)
                    return True                                    
        
        return True
    
    def DepositItem(self, item: cache.Cached_Item, respect_keep_amount : bool = True  ) -> bool:
        if not self.can_deposit:
            return False
        
        stash, sorted_stash = self.GetItemStorage()
        
        if item.material:
            if not respect_keep_amount:
                self.UpdateMaterialCapacity()
                
                if self.DepositMaterial(item):
                    return True            
        
        if item.is_stackable:
            ##TODO Implement the By Weapon Type etc here
            config_condition = None
            keep_amount = 0 if not respect_keep_amount else (config_condition.keep_in_inventory if config_condition else 0)

            amount = item.quantity - keep_amount
            
            for e in sorted_stash:
                slot = stash.index(e)
                id, item_type, model_id, quantity = e

                storage_index = Bag.Storage_1.value + math.floor(slot / 25)
                storage_slot = slot % 25

                if id == 0:
                    continue

                if model_id == item.model_id:
                    slot_quantity = Item.Properties.GetQuantity(
                        id)

                    if slot_quantity == 250:
                        continue

                    if model_id == ModelID.Vial_Of_Dye:
                        if utility.Util.get_color(id) == item.color:
                            move_amount = min(250 - slot_quantity, amount)
                            ConsoleLog(
                                "LootEx", f"Stashing item  {move_amount} '{item.name}' {item.id} to storage {Bag(storage_index)} slot {storage_slot}", Console.MessageType.Info)
                            Inventory.MoveItem(
                                item.id, storage_index, storage_slot, move_amount)
                            amount -= move_amount

                            if amount <= 0:
                                break

                    else:
                        move_amount = min(250 - slot_quantity, amount)
                        ConsoleLog(
                            "LootEx", f"Stashing item {move_amount}x '{item.name}' {item.id} to storage {Bag(storage_index)} slot {storage_slot}", Console.MessageType.Info)
                        Inventory.MoveItem(
                            item.id, storage_index, storage_slot, move_amount)
                        amount -= move_amount

                        if amount <= 0:
                            break

            # If we still have items left to stash, find an empty slot
            if amount > 0:
                self.__Move_Item_To_Empty_Slot(stash, item, amount)

        else:
            # Move item to an empty slot
            self.__Move_Item_To_Empty_Slot(stash, item, item.quantity)

        return True

    def TrackTime(self, time_delta: timedelta, action_times: list[timedelta], name="Action"):
        action_times.append(time_delta)

        if len(action_times) > 100:
            action_times.pop(0)

        average_time = sum(action_times, timedelta()) / len(action_times)
        # ConsoleLog(f"LootEx [{name}]", f"Current: {time_delta.microseconds * 0.000001} sec | Average processing time: {average_time.microseconds * 0.000001} sec. | {len(action_times)} entries", Console.MessageType.Debug)

    def GetItemsFromStorage(self, items: dict[int, tuple[ItemType, int]], force: bool = False) -> bool:
        withdrawn_items = False
        if not force and self.checked_storage_for_merchant_items:
            return False

        if not items:
            ConsoleLog("LootEx", "No items to withdraw from storage.",
                       Console.MessageType.Warning)
            return False

        if not self.cached_inventory:
            ConsoleLog("LootEx", "No cached inventory available, cannot withdraw items from storage.",
                       Console.MessageType.Warning)
            return False

        _, sorted_storage = self.GetItemStorage()

        for model_id, (item_type, quantity) in items.items():
            # find a matching item in the sorted_storage
            storage_item_id = next(
                (item[0] for item in sorted_storage if item[2] == model_id and item[1] == item_type), 0)

            if not storage_item_id:
                continue

            occupies_slot = True

            # get slot from the self.cached_inventory for the first item that has id == 0
            inventory_slot = next(
                (index for index, item in enumerate(self.cached_inventory) if item.id == 0), None)

            if Item.Customization.IsStackable(storage_item_id):
                existing_slot = next(
                    (index for index, item in enumerate(self.cached_inventory) if item.item_type == item_type and item.quantity < 250), None)

                if existing_slot:
                    inventory_slot = existing_slot
                    occupies_slot = False

            if inventory_slot is None:
                continue

            if self.inventory_sizes is None:
                return False

            bag, slot = self.GetBagFromSlot(
                inventory_slot, self.inventory_sizes)
            item_data = self.data.Items.get_item_data(storage_item_id)
            item_name = item_data.name if item_data else "Item Name Unavailable"

            if occupies_slot:
                self.cached_inventory[inventory_slot] = cache.Cached_Item(
                    storage_item_id, inventory_slot)

            else:
                self.cached_inventory[inventory_slot].quantity += quantity

            ConsoleLog(
                "LootEx", f"Withdrawing {quantity}x '{item_name}' ({storage_item_id})", Console.MessageType.Info)
            Inventory.MoveItem(storage_item_id, bag.value, slot, quantity)
            withdrawn_items = True

        self.checked_storage_for_merchant_items = True
        return withdrawn_items

    def CompactStash(self) -> bool:
        return self.CondenseStacks(Bag.Storage_1, Bag.Storage_14) or self.SortBags(Bag.Storage_1, Bag.Storage_10)

    def GetBagFromSlot(self, slot: int, bag_sizes: dict[Bag, int]) -> tuple[Bag, int]:
        offset = 0

        for bag, size in bag_sizes.items():
            if slot < offset + size:
                return bag, slot - offset
            offset += size

        return Bag.NoBag, -1

    def CondenseStacks(self, bag_start: Bag, bag_end: Bag) -> bool:
        if bag_end.value < bag_start.value:
            return False

        class SlotInfo:
            def __init__(self, item_id: int, bag: Bag, slot: int):
                self.item_id = item_id
                self.bag = bag
                self.slot = slot
                self.model_id = Item.GetModelID(item_id)
                self.item_type = ItemType(Item.GetItemType(item_id)[
                                          0]) if item_id else ItemType.Unknown
                self.stackable = Item.Customization.IsStackable(
                    item_id)
                self.quantity = Item.Properties.GetQuantity(
                    item_id)
                self.color = utility.Util.get_color(item_id)

        item_array, bag_sizes = utility.Util.GetZeroFilledBags(
            bag_start, bag_end)

        slot_infos = [
            SlotInfo(item_id, bag, local_slot)
            for index, item_id in enumerate(item_array)
            for bag, local_slot in [self.GetBagFromSlot(index, bag_sizes)]
            if item_id > 0 and Item.Customization.IsStackable(item_id) and (Item.Properties.GetQuantity(item_id) > 0 < 250)
        ]

        condensed = False
        slot_infos.sort(key=lambda x: (
            x.model_id, x.quantity, x.bag.value, x.slot))

        lookup: dict[ItemType, dict[int, list[SlotInfo]]] = {}
        for slot_info in slot_infos:
            if slot_info.item_type not in lookup:
                lookup[slot_info.item_type] = {}

            if slot_info.model_id not in lookup[slot_info.item_type]:
                lookup[slot_info.item_type][slot_info.model_id] = []

            lookup[slot_info.item_type][slot_info.model_id].append(slot_info)
            lookup[slot_info.item_type][slot_info.model_id].sort(
                key=lambda x: x.quantity, reverse=True)

        # sort the slot_infos in lookup by quantity

        for slot_info in slot_infos:
            if slot_info.stackable and slot_info.quantity < 250:
                for next_slot_info in lookup[slot_info.item_type][slot_info.model_id]:
                    if next_slot_info.item_id == slot_info.item_id or next_slot_info.item_id == 0:
                        continue

                    if next_slot_info.quantity >= 250:
                        continue

                    if next_slot_info.bag == slot_info.bag and next_slot_info.slot == slot_info.slot:
                        continue
                    
                    if slot_info.model_id == ModelID.Vial_Of_Dye:
                        if next_slot_info.color != slot_info.color:
                            continue

                    # Check if the next slot info is not the same item
                    if next_slot_info.item_id != slot_info.item_id:
                        move_amount = min(
                            250 - next_slot_info.quantity, slot_info.quantity)
                        next_slot_info.quantity += move_amount
                        slot_info.quantity -= move_amount

                        Inventory.MoveItem(
                            slot_info.item_id, next_slot_info.bag.value, next_slot_info.slot, move_amount)
                        condensed = True

                        if slot_info.quantity <= 0:
                            slot_info.item_id = 0
                            break

        return condensed

    def CompactInventory(self) -> bool:
        return self.CondenseStacks(Bag.Backpack, Bag.Bag_2) or self.SortBags(Bag.Backpack, Bag.Bag_2)

    def SortBags(self, bag_start: Bag, bag_end: Bag) -> bool:
        if bag_end.value < bag_start.value:
            return False

        # Sort the inventory and comapct it
        # We sort in the following order:
        item_typeOrder = [
            int(ItemType.Kit),
            int(ItemType.Key),
            int(ItemType.Usable),
            int(ItemType.Trophy),
            int(ItemType.Quest_Item),
            int(ItemType.Materials_Zcoins)
        ]

        # then everything else
        item_typeOrder += [int(item)
                           for item in ItemType if int(item) not in item_typeOrder]
        
        item_array, bag_sizes = utility.Util.GetZeroFilledBags(
            bag_start, bag_end)

        desired_item_array = sorted(
            item_array,
            key=lambda item_id: (
                item_id == 0,
                item_typeOrder.index(
                    Item.GetItemType(item_id)[0]),
                Item.GetModelID(item_id),
                -Item.Properties.GetQuantity(item_id),
                -Item.Rarity.GetRarity(item_id)[0],
                -Item.Properties.GetValue(item_id),
                utility.Util.get_color(item_id),
                item_id
            )
        )

        for target_slot, item_id in enumerate(desired_item_array):
            if item_id == 0:
                continue

            if target_slot is not None:
                bag, slot = self.GetBagFromSlot(target_slot, bag_sizes)

                Inventory.MoveItem(item_id, bag.value, slot,
                                   Item.Properties.GetQuantity(item_id))

        return False

    def HasModToKeep(self, item: cache.Cached_Item) -> tuple[bool, list[models.WeaponModInfo], list[models.RuneModInfo]]:
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        runes_to_keep: list[models.RuneModInfo] = []
        mods_to_keep: list[models.WeaponModInfo] = []

        if settings.profile is not None and settings.profile.weapon_mods is not None:

            for rune in item.max_runes:
                if rune.Rune.identifier in settings.profile.runes:
                    if settings.profile.runes[rune.Rune.identifier]:
                        runes_to_keep.append(rune)

            for mod in item.max_weapon_mods:
                if mod.WeaponMod.identifier in settings.profile.weapon_mods:
                    if settings.profile.weapon_mods[mod.WeaponMod.identifier].get(item.item_type.name, False):
                        mods_to_keep.append(mod)

        return True if runes_to_keep or mods_to_keep else False, mods_to_keep, runes_to_keep

    def CanProcessItem(self, item: cache.Cached_Item) -> bool:
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        if settings.profile and settings.profile.is_blacklisted(item.item_type, item.model_id):
            return False

        # Item is customized, do not process it
        if item.is_customized:
            return False

        return True

    def GetMissingItems(self) -> dict[int, tuple[ItemType, int]]:
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        if settings.profile is None:
            return {}

        missing_items: dict[int, tuple[ItemType, int]] = {}

        if settings.profile.identification_kits > 0:
            identificationKits = Inventory.GetModelCount(
                ModelID.Superior_Identification_Kit)
            identificationKits += Inventory.GetModelCount(
                ModelID.Identification_Kit)
            if identificationKits < settings.profile.identification_kits:
                missing_items[ModelID.Superior_Identification_Kit] = (
                    ItemType.Kit, settings.profile.identification_kits - identificationKits)

        if settings.profile.salvage_kits > 0:
            salvageKits = Inventory.GetModelCount(ModelID.Salvage_Kit)
            if salvageKits < settings.profile.salvage_kits:
                missing_items[ModelID.Salvage_Kit] = (
                    ItemType.Kit, settings.profile.salvage_kits - salvageKits)

        if settings.profile.expert_salvage_kits > 0:
            expertSalvageKits = Inventory.GetModelCount(
                ModelID.Expert_Salvage_Kit)
            expertSalvageKits += Inventory.GetModelCount(
                ModelID.Superior_Salvage_Kit)
            if expertSalvageKits < settings.profile.expert_salvage_kits:
                missing_items[ModelID.Expert_Salvage_Kit] = (
                    ItemType.Kit, settings.profile.expert_salvage_kits - expertSalvageKits)

        if settings.profile.lockpicks > 0:
            lockpicks = Inventory.GetModelCount(ModelID.Lockpick)
            if lockpicks < settings.profile.lockpicks:
                missing_items[ModelID.Lockpick] = (
                    ItemType.Key, settings.profile.lockpicks - lockpicks)

        return missing_items

    def BuyItemsFromMerchant(self, items_to_buy: dict[int, tuple[ItemType, int]]):
        if not ui_manager_extensions.UIManagerExtensions.IsMerchantWindowOpen():
            ConsoleLog("LootEx", "Merchant window is not open, cannot buy items.",
                       Console.MessageType.Warning)
            return

        merchant_item_list = Trading.Merchant.GetOfferedItems()
        gold_on_character = Inventory.GetGoldOnCharacter()

        for model_id, (item_type, amount) in items_to_buy.items():
            item_id = next((
                item for item in merchant_item_list if Item.GetModelID(item) == model_id and Item.GetItemType(item)[0] == item_type.value), None)

            if item_id is None:
                if model_id == ModelID.Superior_Identification_Kit:
                    item_id = next((
                        item for item in merchant_item_list if Item.GetModelID(item) == ModelID.Identification_Kit and Item.GetItemType(item)[0] == item_type.value), None)
            
            if item_id is None:
                continue

            value = Item.Properties.GetValue(item_id) * 2
            amount = math.floor(min(amount, gold_on_character / value))
            if amount <= 0:
                continue
            
            item_data = self.data.Items.get_item_data(item_id)
            item_name = item_data.name if item_data else "Item Name Unavailable"
            ConsoleLog(
                "LootEx", f"Buying {amount}x '{item_name}' ({item_id}) from merchant for {utility.Util.format_currency(value * amount)}.", Console.MessageType.Info)

            for i in range(amount):
                if value <= gold_on_character:
                    gold_on_character -= value
                    Trading.Merchant.BuyItem(item_id, value)

                if gold_on_character <= 0:
                    break

            if gold_on_character <= 0:
                break

    def UpdateMaterialCapacity(self):        
        material_storage = ItemArray.GetItemArray(
            [Bag.Material_Storage])
        
        max_quantity = max([Item.Properties.GetQuantity(item_id) for item_id in material_storage])
        
        ## calculate the estimated capacity based on the max quantity by rounding it up to the nearest 250 if it is not already a multiple of 250        
        estimated_capacity = (max_quantity // 250) * 250
        
        if max_quantity % 250 != 0:
            ## if it is not a multiple of 250, add 250 to the estimated capacity
            ## this ensures that the material storage capacity is always a multiple of 250
            estimated_capacity += 250
        ConsoleLog("LootEx", f"Estimated material storage capacity: {estimated_capacity}", Console.MessageType.Info)

        
        if estimated_capacity != self.material_capacity:
            self.material_capacity = estimated_capacity
            ConsoleLog("LootEx", f"Material storage capacity set to {self.material_capacity}", Console.MessageType.Info)
            
    def DepositMaterial(self, item: cache.Cached_Item) -> bool:
        if not self.can_deposit:
            return False
        
        if not self.material_capacity:
            ConsoleLog(
                "LootEx", "Material storage capacity is not set, cannot deposit materials.", Console.MessageType.Warning)
            return False

        if not item.material:
            ConsoleLog(
                "LootEx", f"Item {item.name} ({item.id}) does not have a material associated with it, cannot deposit to material storage.", Console.MessageType.Warning)
            return False

        material_storage = self.GetMaterialStorage()
        material_item_id, material_amount = material_storage[item.material.material_storage_slot]

        if material_item_id > 0 and material_amount == 0:
            material_storage[item.material.material_storage_slot] = (
                material_item_id, Item.Properties.GetQuantity(material_item_id))
            material_item_id, material_amount = material_storage[item.material.material_storage_slot]

        max_move_amount = self.material_capacity - material_amount
        move_amount = min(
            max_move_amount, item.quantity)

        if move_amount <= 0:
            # ConsoleLog(
            #     "LootEx", f"Item {item.name} ({item.id}) cannot be deposited to material storage, not enough space.", Console.MessageType.Warning)
            return False

        material_storage[item.material.material_storage_slot] = (
            material_item_id, material_amount + move_amount)

        # ConsoleLog(
        #     "LootEx", f"Depositing item {move_amount}x '{item.material.name}' ({item.id}) to material storage.", Console.MessageType.Info)
        Inventory.MoveItem(item.id, Bags.MaterialStorage,
                           item.material.material_storage_slot, move_amount)

        return True

    def UpdateSalvageWindows(self):
        if not self.salvage_windows_updated:
            self.is_salvage_window_open = ui_manager_extensions.UIManagerExtensions.IsSalvageWindowOpen()
            self.is_confirm_materials_window_open = ui_manager_extensions.UIManagerExtensions.IsConfirmMaterialsWindowOpen()
            self.salvage_windows_updated = True

    def UpdateMerchantWindow(self):
        merchant_open = ui_manager_extensions.UIManagerExtensions.IsMerchantWindowOpen()        
        
        if self.merchant_open != merchant_open:
            self.merchant_open = merchant_open
            
        if not self.merchant_open:
            self.merchant_type = MerchantType.None_
            
        else:                
            if ui_manager_extensions.UIManagerExtensions.IsCrafterOpen():
                self.merchant_type = MerchantType.Crafter
                return
            
            if ui_manager_extensions.UIManagerExtensions.IsCollectorOpen():
                self.merchant_type = MerchantType.Collector
                return
            
            if ui_manager_extensions.UIManagerExtensions.IsSkillTrainerOpen():
                self.merchant_type = MerchantType.None_
                return
                            
            item_ids = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
                            
            if item_ids:                    
                item_type = ItemType(Item.GetItemType(item_ids[0])[0])              
                
                if item_type == ItemType.Rune_Mod:
                    self.merchant_type = MerchantType.RuneTrader
                    return
                
                elif item_type == ItemType.Scroll:
                    self.merchant_type = MerchantType.ScrollTrader
                    return
                
                elif item_type == ItemType.Dye and utility.Util.get_color(item_ids[0]) > DyeColor.NoColor != DyeColor.Gray:
                    self.merchant_type = MerchantType.DyeTrader
                    return
                
                elif item_type == ItemType.Materials_Zcoins:
                    model_id = Item.GetModelID(item_ids[0])
                    material = self.data.Materials.get(model_id, None)
                    
                    if material:
                        if material.material_type == MaterialType.Rare:
                            self.merchant_type = MerchantType.RareMaterialTrader
                            return
                        
                        elif material.material_type == MaterialType.Common:                                    
                            self.merchant_type = MerchantType.MaterialTrader
                            return
                else:
                    self.merchant_type = MerchantType.Merchant
                    return
       
    def IsSalvageAction(self, action: ItemAction) -> bool:
        return action in (ItemAction.Salvage_Common_Materials, ItemAction.Salvage_Rare_Materials, ItemAction.Salvage, ItemAction.Salvage_Mods)
        
    def ProcessSalvageListX(self):        
        
        if self.salvage_queue and len(self.salvage_queue) > 0:            
            self.salvage_queue = {
                item_id: item for item_id, item in self.salvage_queue.items() if not item.IsSalvaged()[0]
            } 
                        
        if Inventory.GetFreeSlotCount() <= 0:
            return False
        
        salvage_item = next(iter(self.salvage_queue.values()), None)
        
        if salvage_item is None:
            return

        salvaged, remaining = salvage_item.IsSalvaged()
        if salvaged:
            if remaining <= 0:
                ConsoleLog(
                    f"LootEx", f"Salvaged {salvage_item.name} ({salvage_item.id})!", Console.MessageType.Debug)
                
                self.salvage_queue.pop(salvage_item.id)  # Remove from salvage queue
                
                if salvage_item in self.cached_inventory:
                    self.cached_inventory.remove(salvage_item)  # Remove from cached inventory
                
                self.inventory_changed = True                
                return True

            else:
                ConsoleLog(
                    f"LootEx", f"Salvaged {salvage_item.name} ({salvage_item.id}), but still has {remaining} remaining.", Console.MessageType.Debug)
                salvage_item.salvage_started = None
                return False

        elif not salvage_item.salvage_started:
            kit = self.GetSalvageKit(
                self.GetSalvageKitOption(salvage_item.salvage_option))

            if kit is None or kit.uses <= 0:
                # ConsoleLog(
                #     "LootEx", f"No salvage kit for salvage option {salvage_item.salvage_option.name} found, cannot salvage item.", Console.MessageType.Warning)
                return False

            salvage_item.salvage_started = datetime.now()
            Inventory.SalvageItem(salvage_item.id, kit.id)
            salvage_item.savlage_tries += 1
            kit.uses -= 1            
            ConsoleLog(
                "LootEx", f"Salvage {salvage_item.quantity}x {salvage_item.name} ({salvage_item.id}) with kit {kit.name} ({kit.id}) with salvage option {salvage_item.salvage_option.name}", Console.MessageType.Info)
            return True

        elif salvage_item.salvage_started:
        
            time_since_salvage = datetime.now() - (salvage_item.salvage_started or datetime.now())
            salvage_item.Update()
             
            if time_since_salvage.total_seconds() > 3:
                ConsoleLog(
                    "LootEx", f"Salvage operation for {salvage_item.name} has timed out after {time_since_salvage.total_seconds()} seconds.", Console.MessageType.Warning)
                self.ResetSalvageWindow()
                salvage_item.salvage_started = None

                if salvage_item.savlage_tries >= 3:
                    self.salvage_queue.pop(salvage_item.id)
                    return False

                return True

            if salvage_item.salvage_requires_confirmation:
                self.UpdateSalvageWindows()

                if salvage_item.salvage_confirmed:
                    if ui_manager_extensions.UIManagerExtensions.ConfirmModMaterialSalvageVisible():
                        ConsoleLog(
                            "LootEx", f"Confirming 'Salvage for Materials and destroy Mods' Option for {salvage_item.name} ({salvage_item.id})", Console.MessageType.Info)
                        ui_manager_extensions.UIManagerExtensions.ConfirmModMaterialSalvage()  
                        salvage_item.Update()
                        return True
                    
                elif not salvage_item.salvage_confirmed:
                    match salvage_item.salvage_option:
                        case SalvageOption.LesserCraftingMaterials:
                            if self.is_confirm_materials_window_open:  
                                ConsoleLog(
                                    "LootEx", f"Confirming lesser salvage option: {salvage_item.salvage_option.name} for {salvage_item.name} ({salvage_item.id})", Console.MessageType.Info)
                                
                                ui_manager_extensions.UIManagerExtensions.ConfirmLesserSalvage()
                                # salvage_item.salvage_requires_confirmation = False
                                salvage_item.Update()
                                return True

                        case SalvageOption.RareCraftingMaterials | SalvageOption.Prefix | SalvageOption.Suffix | SalvageOption.Inherent:
                            if self.is_salvage_window_open:                             
                                if salvage_item.salvage_option == SalvageOption.Prefix:
                                    prefix = None
                                    
                                    if salvage_item.is_weapon:
                                        prefix = next(
                                            (mod for mod in salvage_item.max_weapon_mods if mod.WeaponMod.mod_type == ModType.Prefix), None)
                                    elif salvage_item.is_armor:
                                        prefix = next(
                                            (rune for rune in salvage_item.max_runes if rune.Rune.mod_type == ModType.Prefix), None)
                                    
                                    if prefix:
                                        ConsoleLog(
                                            "LootEx", f"Confirming salvage option: {salvage_item.salvage_option.name} for {salvage_item.name} ({salvage_item.id}) to extract {prefix.Mod.name}", Console.MessageType.Info)
                                    else:
                                        ConsoleLog(
                                            "LootEx", f"Confirming salvage option: {salvage_item.salvage_option.name} for {salvage_item.name} ({salvage_item.id}) to extract 'Unkown Upgrade'", Console.MessageType.Info)
                                elif salvage_item.salvage_option == SalvageOption.Suffix:
                                    suffix = None
                                    
                                    if salvage_item.is_weapon:
                                        suffix = next(
                                            (mod for mod in salvage_item.max_weapon_mods if mod.WeaponMod.mod_type == ModType.Suffix), None)
                                    elif salvage_item.is_armor:
                                        suffix = next(
                                            (rune for rune in salvage_item.max_runes if rune.Rune.mod_type == ModType.Suffix), None)
                                    
                                    if suffix:
                                        ConsoleLog(
                                            "LootEx", f"Confirming salvage option: {salvage_item.salvage_option.name} for {salvage_item.name} ({salvage_item.id}) to extract {suffix.Mod.name}", Console.MessageType.Info)
                                    else:
                                        ConsoleLog(
                                            "LootEx", f"Confirming salvage option: {salvage_item.salvage_option.name} for {salvage_item.name} ({salvage_item.id}) to extract 'Unkown Upgrade'", Console.MessageType.Info)
                                elif salvage_item.salvage_option == SalvageOption.Inherent:
                                    inherent = None
                                    
                                    if salvage_item.is_weapon:
                                        inherent = next(
                                            (mod for mod in salvage_item.max_weapon_mods if mod.WeaponMod.mod_type == ModType.Inherent), None)
                                        
                                    elif salvage_item.is_armor:
                                        ConsoleLog(
                                            "LootEx", f"Armors don't have a inherent mod to extract.", Console.MessageType.Info)
                                        return False
                                    
                                    if inherent:
                                        ConsoleLog(
                                            "LootEx", f"Confirming salvage option: {salvage_item.salvage_option.name} for {salvage_item.name} ({salvage_item.id}) to extract {inherent.Mod.name}", Console.MessageType.Info)
                                    else:
                                        ConsoleLog(
                                            "LootEx", f"Confirming salvage option: {salvage_item.salvage_option.name} for {salvage_item.name} ({salvage_item.id}) to extract 'Unkown Upgrade'", Console.MessageType.Info)
                                else:
                                    ConsoleLog(
                                        "LootEx", f"Confirming salvage option: {salvage_item.salvage_option.name} for {salvage_item.name}", Console.MessageType.Info)
                                    
                                ui_manager_extensions.UIManagerExtensions.SelectSalvageOptionAndSalvage(
                                    salvage_item.salvage_option)
                                
                                salvage_item.salvage_confirmed = True
                                salvage_item.Update()
                                return True

        return False

    def ProcessTraderList(self):  
        if not self.trading_queue:
            return False
        
        for action in self.trading_queue:
            if action.trader_type == self.merchant_type != MerchantType.None_:
                # Start coroutine if not already started
                if action.coroutine is None:
                    action.coroutine = action.run()

                state = action.coroutine.step()

                if state in (ActionState.Completed, ActionState.Timeout):
                    self.trading_queue.remove(action)

                return True

        return False
    
    def ProcessCraftingList(self):        
        if not self.crafting_queue:
            self.process_crafting = False
            return
                    
        if not self.process_crafting:
            return
                    
        for action in self.crafting_queue:  
            if not action._is_available():
                continue
                      
            if action.coroutine is None:
                action.coroutine = action.run()
                
            state = action.coroutine.step()
            if state in (ActionState.Completed, ActionState.Timeout):
                self.crafting_queue.remove(action)
                
            return True
    
        return False
    
    def ProcessAutoCraftingList(self):        
        if not self.auto_crafting_queue:
            return
                    
        for action in self.auto_crafting_queue:  
            if not action._is_available():
                continue
                      
            if action.coroutine is None:
                action.coroutine = action.run()
                
            state = action.coroutine.step()
            if state in (ActionState.Completed, ActionState.Timeout):
                self.auto_crafting_queue.remove(action)
                
            return True
    
        return False

    def ProcessSalvageList(self):
        if not self.salvaging_queue or len(self.salvaging_queue) == 0:
            return False
        
        if not self.lesser_salvage_kits and not self.expert_salvage_kits:
            return False
        
        
        if self._active_salvage_action is None:
            items_to_salvage = list(self.salvaging_queue.items())
            # Begin with lowest quantity to free up inventory space faster
            items_to_salvage.sort(key=lambda x: x[1].item.quantity)
            
            for _, action in items_to_salvage:
                if action.item.salvage_option == SalvageOption.LesserCraftingMaterials and not self.lesser_salvage_kits:
                    continue
                
                if action.item.salvage_option in (SalvageOption.RareCraftingMaterials, SalvageOption.Prefix, SalvageOption.Suffix, SalvageOption.Inherent) and not self.expert_salvage_kits:
                    continue
                
                self._active_salvage_action = action
                break
        
        if self._active_salvage_action is None:
            return False
        
        # Start coroutine if not already started
        if self._active_salvage_action.coroutine is None:
            self._active_salvage_action.coroutine = self._active_salvage_action.run()

        state = self._active_salvage_action.coroutine.step()

        if state in (ActionState.Completed, ActionState.Timeout):
            del self.salvaging_queue[self._active_salvage_action.item_id]
            self._active_salvage_action = None

        return True                
    
    def ExchangeItems(self):
        if not self.merchant_open:
            return False
    
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        if not settings.profile:
            return False
                        
        for (to_model_id, to_item_type), (from_model_id, from_item_type, rate, item_price) in ITEM_CONVERSIONS.items():
            if not settings.conversions.get(f"{from_model_id.name}>>{to_model_id.name}", False):  
                continue
            
            from_item = next((
                item for item in self.cached_inventory if item.model_id == from_model_id and item.quantity >= rate), None)
            
            
            if from_item is None:
                continue
            
            exchangeable_amount = from_item.quantity // rate
            
            if exchangeable_amount <= 0:
                continue
        
            to_item_data = self.data.Items.get_item(to_item_type, to_model_id)
            exchanged = 0
            
            for _i in range(exchangeable_amount):                        
                offered_items = Trading.Crafter.GetOfferedItems()
                offered_item = next((
                    item for item in offered_items if Item.GetModelID(item) == to_model_id), None)   
                
                if offered_item is None:
                    continue
                                    
                gold_on_character = Inventory.GetGoldOnCharacter()
                
                if item_price > gold_on_character:
                    continue
                              
                Merchant.Trading.Crafter.CraftItem(offered_item, item_price, [from_item.id], [rate])
                exchanged += 1
            
            
            ConsoleLog(
                "LootEx", f"Exchanged {exchanged * rate}x '{from_item.data.name if from_item.data else from_item.name}' ({from_item.id}) for {exchanged}x '{to_item_data.name if to_item_data else to_model_id.name}' via crafter for {utility.Util.format_currency(item_price * exchanged)}.", Console.MessageType.Info)  
        
        pass

    def GetTraderType(self, item: cache.Cached_Item) -> MerchantType:
        if item.item_type == ItemType.Rune_Mod:
            return MerchantType.RuneTrader

        if item.item_type == ItemType.Materials_Zcoins:
            if item.material: 
                if item.material.material_type == MaterialType.Rare:
                    return MerchantType.RareMaterialTrader
                else:            
                    return MerchantType.MaterialTrader

        if item.item_type == ItemType.Scroll:
            return MerchantType.ScrollTrader
        
        if item.item_type == ItemType.Dye:
            if item.color and item.color > DyeColor.NoColor != DyeColor.Gray:
                return MerchantType.DyeTrader

        return MerchantType.None_
    
    class ActionsSummary:
        def __init__(self, inventory_handler):            
            self.inventory_handler = inventory_handler
            self.salvage_queue: dict[int, cache.Cached_Item] = {}
            self.inventory_array: list[int] = []
            self.inventory_sizes: dict[Bag, int] = {}
            self.inventory_changed: bool = False
            
            self.inventory_materials: list[cache.Cached_Item] = []
            
            self.salvage_kits: list[cache.Cached_Item] = []
            self.lesser_salvage_kits: list[cache.Cached_Item] = []
            self.expert_salvage_kits: list[cache.Cached_Item] = []
            self.perfect_salvage_kits: list[cache.Cached_Item] = []
            
            self.identification_kits: list[cache.Cached_Item] = []
            self.cached_inventory: list[cache.Cached_Item] = []
            self.actions: dict[int, cache.Cached_Item] = {}
                    
    def GetActions(self, start_bag : Bag = Bag.Backpack, end_bag : Bag = Bag.Bag_2, item_ids : list[int] = [], preview : bool = False) -> ActionsSummary:
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        result = InventoryHandler.ActionsSummary(self)
        if not settings.profile:
            return result
        def ShouldHandleNickItem(item: cache.Cached_Item) -> bool:
            if item.data and item.data.next_nick_week:
                weeks_until = (item.data.next_nick_week -
                               date.today()).days // 7

                if weeks_until <= settings.profile.nick_weeks_to_keep if settings.profile else False:
                    return True
            
            return False
                
        def ShouldDepositItem(item: cache.Cached_Item) -> bool:         
            if item.IsVial_Of_DyeToKeep():
                return True

            if item.is_weapon:
                if item.weapon_mods_to_keep and len(item.weapon_mods_to_keep) > 1:
                    return True
                
            elif item.is_armor:
                if item.runes_to_keep and len(item.runes_to_keep) > 1:
                    return True  

            if item.is_rare_weapon_to_keep:
                return True
            
            if item.matches_weapon_rule:
                return True
            
            return False

        def ShouldIdentifyItem(item: cache.Cached_Item) -> bool:
            if not item.is_identified:

                if item.is_weapon or item.is_armor:
                    if (item.rarity > Rarity.White or item.value >= 25) and item.rarity < Rarity.Green:
                        return True

            return False

        def ShouldExtractMods(item: cache.Cached_Item) -> bool:
            if item.is_blacklisted:
                return False

            if item.is_salvageable:
                if item.is_weapon:
                    if item.weapon_mods_to_keep and len(item.weapon_mods_to_keep) >= 1:
                        return True
                    
                elif item.item_type == ItemType.Salvage:
                    if item.runes_to_keep and len(item.runes_to_keep) >= 1:
                        return True   
                                    
            if item.item_type == ItemType.Rune_Mod:
                if item.runes_to_keep:
                    return True
                
                if item.weapon_mods_to_keep:
                    return True
                
            return False

        def ShouldSalvageItem(item: cache.Cached_Item) -> bool:
            if not settings.profile:
                return False

            if item.is_blacklisted:
                return False

            if not item.is_salvageable:
                return False

            return self.IsSalvageAction(item.action)

        def ShouldSellItemToMerchant(item: cache.Cached_Item) -> bool:
            if not settings.profile:
                return False

            if item.is_blacklisted:
                return False

            if item.value <= 0:
                return False
            
            # If the item is a material, we should not sell it to the merchant, instead we should deposit it to the material storage or visit the material trader
            if item.item_type == ItemType.Materials_Zcoins:
                return False

            # Runes and Insignias should not be sold to the merchant, instead we should visit the rune trader to sell them
            if item.item_type == ItemType.Rune_Mod:
                if item.is_rune:
                    return False

            return item.action == ItemAction.Sell_To_Merchant

        def ShouldDestroyItem(item: cache.Cached_Item) -> bool:
            if not settings.profile:
                return False

            if item.is_blacklisted:
                return False

            return item.action == ItemAction.Destroy
        
        def ShouldSellToTrader(item: cache.Cached_Item) -> bool:
            if not settings.profile:
                return False

            if item.is_blacklisted:
                return False
                               
            if item.item_type == ItemType.Rune_Mod:
                return len(item.runes_to_sell) > 0                

            return item.action == ItemAction.Sell_To_Trader

        inventory_array, inventory_sizes = utility.Util.GetZeroFilledBags(
            start_bag, end_bag) if not item_ids else (item_ids, {})
        
        result.inventory_array = inventory_array
        result.inventory_sizes = inventory_sizes
        data_collector = DataCollector()
        
        has_empty_slot = False
        for slot, item_id in enumerate(inventory_array):
            item = cache.Cached_Item(item_id, slot)
            result.cached_inventory.append(item)
            
            has_empty_slot = item.id == 0 or has_empty_slot
            if item.id == 0:
                continue
        
            ## Collect ingame data
            if not item.data or not item.data.has_name(settings.language):
                item.action = ItemAction.Collect_Data
                result.actions[item_id] = item
                data_collector.collect_item(item_id, settings.language)
                continue
                         
            ## Collect the inventory icon and the minimum data required for processing
            if not item.data.is_minimum_complete():  
                ## Collect the inventory icon
                if not item.data.inventory_icon:
                    item.action = ItemAction.Collect_Data
                    result.actions[item_id] = item
                    
                    if not (item.item_type, item.model_id) in self.scraped_items:
                        data_collector.auto_assign_scraped_data(item.data)
                        self.scraped_items[(item.item_type, item.model_id)] = True
                            
                    if not item.data.inventory_icon:
                        continue
                
                ## Collect salvage data for salvageable items
                if item.is_salvageable and not item.data.rare_salvage and not item.data.common_salvage:
                    item.action = ItemAction.Collect_Data
                    result.actions[item_id] = item
                    
                    if not (item.item_type, item.model_id) in self.scraped_items:
                        data_collector.auto_assign_scraped_data(item.data)
                        self.scraped_items[(item.item_type, item.model_id)] = True
                        
                    if not item.data.rare_salvage and not item.data.common_salvage:
                        continue
                             
                ## Collect the english name at least, since we can not automate this, it stays until the user changes the language settings
                if not item.data.has_name(ServerLanguage.English):
                    item.action = ItemAction.Collect_Data
                    result.actions[item_id] = item
                    continue
                
                continue
            
            if item.is_blacklisted:
                continue
            
            if has_empty_slot and item.id > 0:
                result.inventory_changed = True
            
            if (not item.is_inventory_item or item.quantity <= 0):
                continue
            
            if not self.CanProcessItem(item):                
                continue
            
            if item.is_salvage_kit:
                if item.uses > 0:
                    result.salvage_kits.append(item)
                    
            if item.is_identification_kit:
                if item.uses > 0:
                    result.identification_kits.append(item)

            def get_from_existing(existing_item: cache.Cached_Item | None) -> bool:
                if not existing_item:
                    return False
                
                if not item.is_inventory_item:
                    return False
                
                if existing_item.action == ItemAction.Collect_Data:
                    return False
                
                if existing_item.quantity != item.quantity:
                    return False
                
                if existing_item.rarity != item.rarity:
                    return False
                
                if item.is_identified and existing_item.action == ItemAction.Identify:
                    return False
                
                if existing_item.action == ItemAction.Deposit_Material and self.deposited:
                    return False
                
                if item.mods != existing_item.mods:
                    return False
                                                         
                item.action = existing_item.action
                item.salvage_option = existing_item.salvage_option
                item.salvage_requires_confirmation = existing_item.salvage_requires_confirmation
                item.salvage_requires_material_confirmation = existing_item.salvage_requires_material_confirmation
                item.savlage_tries = existing_item.savlage_tries
                item.salvage_started = existing_item.salvage_started
                item.is_blacklisted = existing_item.is_blacklisted
                
                result.actions[item_id] = item
                result.inventory_changed = result.inventory_changed or existing_item.slot != item.slot or has_empty_slot
                return True
                        
            existing_item = next(
                (item for item in self.cached_inventory if item.id == item_id), None)
            
            # Soft action set for materials to deposit them to the material storage, may be overridden later through filters or item config
            if item.item_type == ItemType.Materials_Zcoins:                
                if item.model_id in self.data.Materials:                    
                    result.inventory_materials.append(item)
                
                    if item.action == ItemAction.NONE:                                
                        item.action = ItemAction.Hold

            if get_from_existing(existing_item):
                continue
            
            if not item.is_inventory_item:
                if item_id in result.actions:
                    del result.actions[item_id]

                result.cached_inventory.remove(item)
                # ConsoleLog(
                #     "LootEx", f"Item {item.name} ({item.id}) is not an inventory item, skipping.", Console.MessageType.Debug)
                continue
            
            if has_empty_slot:
                result.inventory_changed = True

            result.actions[item_id] = item

            if ShouldIdentifyItem(item) or (self.IsSalvageAction(item.action) and not item.is_identified):
                item.action = ItemAction.Identify
                continue
            
            if ShouldHandleNickItem(item):
                item.action = settings.profile.nick_action if settings.profile else ItemAction.Hold
                continue
                                    
            if ShouldDepositItem(item):
                # ConsoleLog(
                #     "LootEx", f"Item '{item.name}' ({item.id}) should be deposited to storage.", Console.MessageType.Info)
                item.action = ItemAction.Stash
                continue
                            
            if item.matches_skin_rule and item.skin_rule:
                if item.skin_rule.action != ItemAction.NONE and (not item.is_inventory_item or item.skin_rule.action != ItemAction.Loot):
                    item.action = item.skin_rule.get_action(item)

                    if self.IsSalvageAction(item.action):
                        if not item.is_identified:
                            item.action = ItemAction.Identify
                            continue
                        
                        salvage_option = self.GetSalvageOption(item)

                        if salvage_option is not None:
                            item.salvage_option = salvage_option
                            rarity_requires_confirmation = item.rarity >= Rarity.Blue
                            mods_require_confirmation = item.has_mods and salvage_option is not SalvageOption.LesserCraftingMaterials
                            item.salvage_requires_confirmation = rarity_requires_confirmation or mods_require_confirmation
                            item.salvage_requires_material_confirmation = item.has_mods and (salvage_option is SalvageOption.RareCraftingMaterials or salvage_option is SalvageOption.CraftingMaterials)
                            
                            if not item in result.salvage_queue:
                                result.salvage_queue[item.id] = item
                    continue
            
            if ShouldExtractMods(item):
                if item.item_type == ItemType.Rune_Mod:
                    if item.runes_to_sell:
                        item.action = ItemAction.Sell_To_Trader
                        continue
                    
                    if item.runes_to_keep:
                        item.action = settings.profile.rune_action
                        continue
                    
                    if item.weapon_mods_to_keep:
                        item.action = settings.profile.weapon_mod_action
                        continue
                
                if not item.is_salvageable:
                    item.action = ItemAction.NONE
                    continue
                
                if not item.is_identified:
                    item.action = ItemAction.Identify
                    continue
                
                elif item.is_weapon:
                    if item.weapon_mods_to_keep and len(item.weapon_mods_to_keep) == 1:
                        if not item.weapon_mods_to_keep[0].WeaponMod.upgrade_exists:
                            item.action = settings.profile.weapon_mod_action if settings.profile else ItemAction.Hold
                            continue
                        
                        item.action = ItemAction.Salvage_Mods
                        item.salvage_option = utility.Util.GetSalvageOptionFromModType(
                            item.weapon_mods_to_keep[0].WeaponMod.mod_type)
                        item.salvage_requires_confirmation = True
                        
                        if not item in result.salvage_queue:
                            result.salvage_queue[item.id] = item
                            
                    elif item.weapon_mods_to_keep and len(item.weapon_mods_to_keep) > 1:
                        item.action = settings.profile.weapon_mod_action if settings.profile else ItemAction.Hold

                elif item.is_armor:
                    if item.runes_to_keep and len(item.runes_to_keep) == 1:
                        item.action = ItemAction.Salvage_Mods
                        item.salvage_option = utility.Util.GetSalvageOptionFromModType(
                            item.runes_to_keep[0].Rune.mod_type)
                        item.salvage_requires_confirmation = True
                        
                        if not item in result.salvage_queue:
                            result.salvage_queue[item.id] = item
                    elif item.runes_to_keep and len(item.runes_to_keep) > 1:
                        item.action = settings.profile.rune_action if settings.profile else ItemAction.Hold
                
                # ConsoleLog(
                #     "LootEx", f"Extracting mods from item {item.name} ({item.id}) with option {item.salvage_option.name}", Console.MessageType.Debug)
                continue
            
            if ShouldSellToTrader(item):
                item.action = ItemAction.Sell_To_Trader
                continue
                
            for filter in settings.profile.filters:
                action = filter.get_action(item)

                if action != ItemAction.NONE:
                    if ((item.is_inventory_item and action != ItemAction.Loot) or (not item.is_inventory_item and action == ItemAction.Loot)):
                        item.action = action
                        
                        if self.IsSalvageAction(item.action):
                            if not item.is_identified:
                                item.action = ItemAction.Identify
                                break
                            
                            salvage_option = self.GetSalvageOption(item)

                            if salvage_option is not None:
                                item.salvage_option = salvage_option
                                rarity_requires_confirmation = item.rarity >= Rarity.Blue
                                mods_require_confirmation = item.has_mods and salvage_option is not SalvageOption.LesserCraftingMaterials
                                item.salvage_requires_confirmation = rarity_requires_confirmation or mods_require_confirmation
                                item.salvage_requires_material_confirmation = item.has_mods and (salvage_option is SalvageOption.RareCraftingMaterials or salvage_option is SalvageOption.CraftingMaterials)
                                
                                if not item in result.salvage_queue:
                                    result.salvage_queue[item.id] = item
                        break
            
            if (self.IsSalvageAction(item.action) and not item.is_identified):
                item.action = ItemAction.Identify
                continue

            if ShouldSellItemToMerchant(item):
                item.action = ItemAction.Sell_To_Merchant
                continue

            if ShouldDestroyItem(item):
                continue

        result.salvage_kits.sort(
            key=lambda x: x.uses) if result.salvage_kits else []
        
        result.lesser_salvage_kits = [kit for kit in result.salvage_kits if kit.model_id == ModelID.Salvage_Kit]
        result.expert_salvage_kits = [kit for kit in result.salvage_kits if kit.model_id in (ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit)]
        result.perfect_salvage_kits = [kit for kit in result.salvage_kits if kit.model_id == ModelID.Perfect_Salvage_Kit]
        
        
        result.identification_kits.sort(
            key=lambda x: x.uses) if result.identification_kits else []
           
            
        return result

    def ClaimItems(self) -> bool:
        claimed = False
        
        if self.is_outpost and self.empty_slots > 0:               
            items = utility.Util.GetZeroFilledBags(Bag.Unclaimed_Items, Bag.Unclaimed_Items)[0]
            if not items:
                return claimed
            
            loothandler = loot_handling.LootHandler()
            
            for i in range(len(items)):
                if items[i] == 0:
                    continue
                
                if loothandler.Should_Loot_Item(items[i]):
                    item = cache.Cached_Item(items[i], i)

                    if not item.is_inventory_item:
                        self.WithdrawItem(item)
                        claimed = True

        return claimed


                    
    @property
    def IsActive(self) -> bool:
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        return settings.automatic_inventory_handling and settings.profile is not None
    
    def Run(self):
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        global time_results, actiontime_results
        self.run_once = False
        self.soft_reset()

        self.is_outpost = Map.IsOutpost() or utility.Util.IsGuildHall(Map.GetMapID())
        
        if not settings.profile or not settings.automatic_inventory_handling:
            return
        
        if self.storage_check_timer.IsExpired():
            self.storage_check_timer.Reset()
            increased = False
            
            for bag in XUNLAI_STORAGE:
                items = ItemArray.GetItemArray([bag])
                if any(item_id != 0 for item_id in items):
                    max_xunlai_storage = Bag_enum(max(settings.max_xunlai_storage.value, bag.value))
                    increased = settings.max_xunlai_storage.value < max_xunlai_storage.value
                    settings.max_xunlai_storage = max_xunlai_storage
                    
            if increased:
                ConsoleLog(
                    "LootEx", f"Updated max xunlai storage to {settings.max_xunlai_storage.name} based on current storage usage.", Console.MessageType.Info)
                settings.save()
                
        if settings.profile.changed:
            settings.profile.changed = False
            self.reset()
            return

        global_time = datetime.now()

        self.ProcessSalvageList()
        
        if Map.IsOutpost():
            self.can_deposit = True
            
            stop_deposit = self.ProcessTraderList()
            stop_deposit = self.ProcessCraftingList() or stop_deposit
            stop_deposit = self.ProcessAutoCraftingList() or stop_deposit
            
            
            if stop_deposit:
                self.can_deposit = False

        if self.inventory_timer.IsExpired():
            self.inventory_timer.Reset()

            self.UpdateSalvageWindows()
            self.UpdateMerchantWindow()
            self.upgrade_open = ui_manager_extensions.UIManagerExtensions.IsUpgradeWindowOpen()

            if self.upgrade_open:
                self.reset()
                return
            
            self.empty_slots = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
            
            if self.ClaimItems(): 
                return

            result = self.GetActions()
            if not result:
                return            
            
            self.cached_inventory = result.cached_inventory
            self.lesser_salvage_kits = result.lesser_salvage_kits
            self.expert_salvage_kits = result.expert_salvage_kits
            self.perfect_salvage_kits = result.perfect_salvage_kits
            self.identification_kits = result.identification_kits
            self.inventory_materials = result.inventory_materials
            self.inventory_changed = result.inventory_changed or self.inventory_changed
            self.inventory_array = result.inventory_array
            self.inventory_sizes = result.inventory_sizes
            self.actions = result.actions
                        
            for item in self.actions.values():
                if item.id == 0:
                    continue
                
                if self.IsSalvageAction(item.action):
                    if item.id not in self.salvaging_queue:
                        self.salvaging_queue[item.id] = SalvageAction(item)
                
                if item.action == ItemAction.Sell_To_Trader:
                    existing_action = next((action for action in self.trading_queue if action.item.id == item.id), None)
                    if existing_action is None and (not item.material or item.model_id not in self.data.Common_Materials or item.quantity >= 10):
                        ConsoleLog(
                            "LootEx", f"Queuing item: '{item.name}' ({item.id}) to sell to trader.", Console.MessageType.Info)
                        self.trading_queue.append(TraderAction(item, self.GetTraderType(item), ActionType.Sell)) 

            if self.merchant_timer.IsExpired():
                self.merchant_timer.Reset()

                self.auto_crafting_queue = BuildCraftingQueueFromCrafter() if not self.auto_crafting_queue and settings.auto_crafting_enabled else self.auto_crafting_queue
                
                items_to_buy = self.GetMissingItems()
                if items_to_buy:
                    if self.is_outpost and not self.GetItemsFromStorage(items_to_buy):
                        if self.merchant_open and self.merchant_type == MerchantType.Merchant:
                            self.BuyItemsFromMerchant(items_to_buy)

            for _, item in self.actions.items():
                time = datetime.now()
                time_delta = datetime.now() - time
                self.TrackTime(time_delta, actiontime_results, "Action")

                if item.id == -1:
                    ConsoleLog(
                        "LootEx", f"Processing item: '{item.name}' {item.id} with action: {item.action.name}", Console.MessageType.Debug)


                match item.action:
                    case ItemAction.Collect_Data:
                        continue

                    case ItemAction.Deposit_Material:
                        if self.is_outpost and (self.inventory_changed or not self.deposited):
                            if self.DepositMaterial(item):
                                self.inventory_changed = True
                        continue                           

                    case ItemAction.Identify:
                        if item.is_identified:
                            item.action = ItemAction.NONE
                            self.cached_inventory.remove(item)
                            continue
                        
                        identificationKit = self.GetIdentificationKit()

                        if identificationKit is None or identificationKit.uses <= 0:
                            continue

                        ConsoleLog(
                            "LootEx", f"Identifying item: '{item.name} [{item.model_id}]' ({item.id}) with kit {identificationKit.name} ({identificationKit.id})", Console.MessageType.Info)
                        Inventory.IdentifyItem(item.id, identificationKit.id)
                        identificationKit.uses -= 1

                    case ItemAction.Stash:
                        if self.is_outpost:
                            self.DepositItem(item)
                            self.inventory_changed = True
                            
                    case ItemAction.Salvage | ItemAction.Salvage | ItemAction.Salvage_Common_Materials | ItemAction.Salvage_Rare_Materials:
                        ## This is handled in the salvage queue
                        continue

                    case ItemAction.Salvage_Mods:
                        ## This is handled in the salvage queue
                        continue

                    case ItemAction.Sell_To_Merchant:
                        if self.merchant_open and self.merchant_type == MerchantType.Merchant:
                            ConsoleLog(
                                "LootEx", f"Selling item: '{item.name}' ({item.id}) to merchant for {utility.Util.format_currency(item.value * item.quantity)}", Console.MessageType.Info)
                            Trading.Merchant.SellItem(
                                item.id, item.quantity * item.value)
                            self.inventory_changed = True
                    
                    case ItemAction.Sell_To_Trader:
                        ## This is handled in the trader queue
                        continue
                    
                    case ItemAction.Destroy:
                        ConsoleLog(
                            "LootEx", f"Destroying item: '{item.name}' ({item.id})", Console.MessageType.Info)
                        Inventory.DestroyItem(item.id)
                        self.inventory_changed = True

                    case _:
                        pass

            if not self.deposited and self.inventory_materials:
                for material_item in self.inventory_materials:
                    if self.DepositMaterial(material_item):
                        self.inventory_changed = True
                self.deposited = True
                
            if self.inventory_changed and self.can_deposit:
                if not self.CompactInventory():
                    self.inventory_changed = False

            time_delta = datetime.now() - global_time
            # self.TrackTime(time_delta, time_results, "Global")
            # ConsoleLog(
            #     "LootEx", f"Processed {len(self.actions)} items in {time_delta.microseconds * 0.000001} sec.", Console.MessageType.Debug)

    def Stop(self):
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        ConsoleLog("LootEx", "Stopping inventory handling",
                   Console.MessageType.Info)

        # self.reset()
        settings.automatic_inventory_handling = False
        settings.save()

        MerchantHandler._instance = self.instance_manager.merchant_handler
        ConsoleLog("LootEx", f"Restored MerchantHandler instance to {MerchantHandler._instance.__class__.__name__}", Console.MessageType.Info)
        
        AutoInventoryHandler._instance = self.instance_manager.auto_inventory_handler
        ConsoleLog("LootEx", f"Restored AutoInventoryHandler instance to {AutoInventoryHandler._instance.__class__.__name__}", Console.MessageType.Info)
        
        return True

    def Start(self) -> bool:
        from Sources.frenkeyLib.LootEx.settings import Settings
        settings = Settings()
        
        ConsoleLog("LootEx", "Starting inventory handling",
                   Console.MessageType.Info)

        self.reset()
        settings.automatic_inventory_handling = True
        settings.save()

        MerchantHandler._instance = self.instance_manager.lootex_merchant_handler
        ConsoleLog("LootEx", f"Hijacked MerchantHandler instance to {MerchantHandler._instance.__class__.__name__}", Console.MessageType.Info)

        AutoInventoryHandler._instance = self.instance_manager.lootex_auto_inventory_handler
        ConsoleLog("LootEx", f"Hijacked AutoInventoryHandler instance to {AutoInventoryHandler._instance.__class__.__name__}", Console.MessageType.Info)
        
        return True

# endregion
