from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Generator

from Py4GW import Console
from PyItem import PyItem
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.enums_src.Item_enums import Rarity
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

from Sources.frenkeyLib.LootEx.cache import Cached_Item
from Sources.frenkeyLib.LootEx.enum import ALL_BAGS, CHARACTER_INVENTORY, ActionState, ModType, SalvageOption
from Sources.frenkeyLib.LootEx import ui_manager_extensions

LOG_SALVAGING = False

class SalvageCoroutine:
    def __init__(self, generator_fn: Callable[[], Generator], timeout_seconds: float = 6.0):
        self.generator_fn = generator_fn
        self.generator = None
        self.state = ActionState.Pending
        self.started_at = datetime.min
        self.timeout_seconds = timeout_seconds

    def step(self) -> ActionState:
        if self.state == ActionState.Pending:
            self.generator = self.generator_fn()
            self.state = ActionState.Running
            self.started_at = datetime.now()

        if (datetime.now() - self.started_at).total_seconds() > self.timeout_seconds:
            ConsoleLog("LootEx", "Salvage coroutine timed out.", Console.MessageType.Warning)
            self.state = ActionState.Timeout
            return self.state

        try:
            if self.generator is not None:
                next(self.generator)
                return self.state

            else:
                self.state = ActionState.Completed
                return self.state
            
        except StopIteration:
            self.state = ActionState.Completed
            return self.state

        except Exception as e:
            ConsoleLog("LootEx", f"Salvage coroutine exception: {e}", Console.MessageType.Error)
            self.state = ActionState.Timeout
            return self.state

class SalvageAction:
    def __init__(self, item: Cached_Item, desired_quantity: int = -1):
        self.item = item
        self.item_id = item.id
        self.coroutine: SalvageCoroutine | None = None

        self.salvage_kit = None
        self.is_item_valid: bool = self.item.is_valid and self.item.is_inventory_item if self.item else False
        
        self.initial_quantity = item.quantity
        self.desired_quantity = desired_quantity if desired_quantity > 0 else 0 # Salvage all by default
                
        self.available_mods : dict[ModType, bool] = {}

        rarity_requires_confirmation = item.rarity > Rarity.Blue
        has_salvageable_mods = any(mod.Mod.mod_type is ModType.Prefix or mod.Mod.mod_type is ModType.Suffix or (mod.Mod.mod_type is ModType.Inherent and item.is_inscribable) for mod in item.mods) if item.mods else False
        mods_require_confirmation = has_salvageable_mods and self.item.salvage_option is not SalvageOption.LesserCraftingMaterials
        item.salvage_requires_confirmation = rarity_requires_confirmation or mods_require_confirmation
        
        self._update()

    # Entry point
    def run(self) -> SalvageCoroutine:
        return SalvageCoroutine(self._gen_main)

    # Main generator function
    def _gen_main(self) -> Generator:
        ConsoleLog(
            "LootEx",
            f"Starting SalvageAction for {self.item.name} ({self.item.id}), option={self.item.salvage_option.name}",
            Console.MessageType.Info,
            LOG_SALVAGING
        )

        while not self._is_done():
            yield from self._salvage()
            yield from self._confirm_salvage_windows()
            yield from self._wait_for_completion()

        ConsoleLog(
            "LootEx",
            f"SalvageAction COMPLETED for {self.item.name} ({self.item.id}). Remaining: {self.item.quantity}",
            Console.MessageType.Info,
            LOG_SALVAGING
        )

    # Condition to stop the salvaging action
    def _is_done(self) -> bool:
        self._update()
        
        if not self.is_item_valid or self.item.quantity <= 0:
            ConsoleLog("LootEx", f"Item {self.item.name} is no longer valid or has zero quantity.", Console.MessageType.Warning, LOG_SALVAGING)
            return True
        
        if self.item.quantity <= self.desired_quantity:
            ConsoleLog("LootEx", f"Desired quantity reached for {self.item.name}. Initial: {self.initial_quantity}, Current: {self.item.quantity}, Desired: {self.desired_quantity}", Console.MessageType.Info, LOG_SALVAGING)
            return True   
        
        if not self.item.is_salvageable:
            ConsoleLog("LootEx", f"Item {self.item.name} is not salvageable.", Console.MessageType.Warning, LOG_SALVAGING)
            return True
        
        if self.salvage_kit is None:
            ConsoleLog("LootEx", f"No salvage kit available for {self.item.name}.", Console.MessageType.Warning, LOG_SALVAGING)
            return True
        
        # Check if the selected salvage option is still valid 
        match(self.item.salvage_option):
            case SalvageOption.Inherent:
                if ModType.Inherent not in self.available_mods:
                    ConsoleLog("LootEx", f"Inherent mod no longer available on {self.item.name}.", Console.MessageType.Info, LOG_SALVAGING)
                    return True
            case SalvageOption.Prefix:
                if ModType.Prefix not in self.available_mods:
                    ConsoleLog("LootEx", f"Prefix mod no longer available on {self.item.name}.", Console.MessageType.Info, LOG_SALVAGING)
                    return True
                
            case SalvageOption.Suffix:
                if ModType.Suffix not in self.available_mods:
                    ConsoleLog("LootEx", f"Suffix mod no longer available on {self.item.name}.", Console.MessageType.Info, LOG_SALVAGING)
                    return True

        # Check for empty inventory slots
        empty_slots = Inventory.GetFreeSlotCount()
        if empty_slots <= 0:
            ConsoleLog("LootEx", f"No free inventory slots left to continue salvaging {self.item.name}.", Console.MessageType.Warning, LOG_SALVAGING)
            return True       

        return False
        
    # Start the salvage by using Inventory.SalvageItem
    def _salvage(self) -> Generator:
        if self._is_done():
            return

        if self.salvage_kit is None or self.salvage_kit.uses <= 0:
            return
        
        self.initial_quantity = self.item.quantity
        Inventory.SalvageItem(self.item.id, self.salvage_kit.id)
        self.salvage_kit.uses -= 1
        return
    
        yield

    # Confirm salvage windows if needed
    def _confirm_salvage_windows(self) -> Generator:
        start_wait = datetime.now()

        while True:
            self.item.Update()

            # direct salvage (no confirmation)
            if not self.item.salvage_requires_confirmation:
                return
            
            match(self.item.salvage_option):
                case SalvageOption.LesserCraftingMaterials:
                    if ui_manager_extensions.UIManagerExtensions.IsConfirmMaterialsWindowOpen():
                        ui_manager_extensions.UIManagerExtensions.ConfirmLesserSalvage()
                        return
                    
                case SalvageOption.RareCraftingMaterials | SalvageOption.Prefix | SalvageOption.Suffix | SalvageOption.Inherent:
                    if ui_manager_extensions.UIManagerExtensions.ConfirmModMaterialSalvageVisible():
                        self._print_salvage_confirmation()
                        ui_manager_extensions.UIManagerExtensions.ConfirmModMaterialSalvage() 
                        return
                    
                    if ui_manager_extensions.UIManagerExtensions.IsSalvageWindowOpen():
                        ui_manager_extensions.UIManagerExtensions.SelectSalvageOptionAndSalvage(self.item.salvage_option)

            if (datetime.now() - start_wait).total_seconds() > 3:
                ConsoleLog("LootEx", "No confirmation received — salvage timeout.", Console.MessageType.Warning)
                self.started = False
                return

            yield

    def _print_salvage_confirmation(self) -> None:
        match(self.item.salvage_option):
            case SalvageOption.Prefix:
                prefix = next((mod for mod in self.item.mods if mod.Mod.mod_type == ModType.Prefix), None)
                if prefix:
                    ConsoleLog("LootEx", f"Extract '{prefix.Mod.name}' from item '{self.item.name}'.", Console.MessageType.Info)
                    
            case SalvageOption.Suffix:
                suffix = next((mod for mod in self.item.mods if mod.Mod.mod_type == ModType.Suffix), None)
                if suffix:
                    ConsoleLog("LootEx", f"Extract '{suffix.Mod.name}' from item '{self.item.name}'.", Console.MessageType.Info)
        
            case SalvageOption.Inherent:
                inherent = next((mod for mod in self.item.mods if mod.Mod.mod_type == ModType.Inherent), None)
                if inherent:
                    ConsoleLog("LootEx", f"Extract '{inherent.Mod.name}' from item '{self.item.name}'.", Console.MessageType.Info)
                    
        pass

    # Update item state
    def _update(self) -> None:
        self.item.Update()
        
        self.salvage_kit = None
        self.is_item_valid = self.item.is_valid and self.item.is_inventory_item if self.item else False
        self.item.quantity = 0 if not self.is_item_valid else self.item.quantity
        
        self.available_mods = {}
        if self.item.mods is not None:
            
            for mod in self.item.mods:
                self.available_mods[mod.Mod.mod_type] = True
                
        opt = self.item.salvage_option
        inventory = [Cached_Item(id) for id in ItemArray.GetItemArray(CHARACTER_INVENTORY)]
        salvage_kits = [itm for itm in inventory if itm.is_salvage_kit]
        salvage_kits.sort(key=lambda x: x.uses)
        
        match(opt):
            case SalvageOption.RareCraftingMaterials | SalvageOption.Prefix | SalvageOption.Suffix | SalvageOption.Inherent:
                model_ids = [ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit]                
                for kit in salvage_kits:
                    if kit.model_id in model_ids and kit.uses > 0:
                        self.salvage_kit = kit
                        return
            
            case SalvageOption.LesserCraftingMaterials:
                model_ids = [ModelID.Salvage_Kit]
                for kit in salvage_kits:
                    if kit.model_id in model_ids and kit.uses > 0:
                        self.salvage_kit = kit
                        return
            
            case SalvageOption.CraftingMaterials:
                model_ids = [ModelID.Salvage_Kit, ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit]
                for kit in salvage_kits:
                    if kit.model_id in model_ids and kit.uses > 0:
                        self.salvage_kit = kit
                        return
        
        return

    # Wait for the salvage action to complete
    def _wait_for_completion(self) -> Generator:
        start = datetime.now()

        while True:
            if self._is_done():
                return
            
            if self.initial_quantity > self.item.quantity:
                return
                        
            if (datetime.now() - start).total_seconds() > 3:
                ConsoleLog("LootEx", "Salvage completion timeout.", Console.MessageType.Warning, LOG_SALVAGING)
                return
                
            yield