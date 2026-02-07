#region AutoInventory
from typing import Optional, Callable
from .Console import ConsoleLog, Console
from ..IniManager import IniManager
from .Timer import ThrottledTimer
from .ActionQueue import ActionQueueManager
from .Lootconfig_src import LootConfig

class AutoInventoryHandler():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutoInventoryHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._LOOKUP_TIME:int = 15000
        self.lookup_throttle = ThrottledTimer(self._LOOKUP_TIME)

        self.initialized = False
        self.status = "Idle"
        self.outpost_handled = False
        self.module_active:bool = False
        self.module_name:str = "AutoInventoryHandler"
        
        self.id_whites:bool = False
        self.id_blues:bool = False
        self.id_purples:bool = False
        self.id_golds:bool = False
        self.id_greens:bool = False
        self.id_model_blacklist:list[int] = []  # Items that should not be identified, even if they match the ID criteria
        
        self.salvage_whites:bool = False
        self.salvage_rare_materials:bool = False
        self.salvage_blues:bool = False
        self.salvage_purples:bool = False
        self.salvage_golds:bool = False
        self.item_type_blacklist:list[int] = [] # Item types that should not be salvaged, even if they match the salvage criteria
        self.salvage_blacklist:list[int] = []  # Items that should not be salvaged, even if they match the salvage criteria
        self.blacklisted_model_id:int = 0
        self.model_id_search:str = ""
        self.item_type_search:str = ""
        self.model_id_search_mode:int = 0  # 0 = Contains, 1 = Starts With
        self.item_type_search_mode:int = 0  # 0 = Contains, 1 = Starts With
        self.show_dialog_popup:bool = False 
        self.show_item_type_dialog:bool = False
        
        self.deposit_trophies:bool = False
        self.deposit_materials:bool = False
        self.deposit_blues:bool = False
        self.deposit_purples:bool = False
        self.deposit_golds:bool = False
        self.deposit_greens:bool = False
        self.deposit_event_items:bool = False
        self.deposit_dyes:bool = False
        self.keep_gold:int = 5000
        self.deposit_trophies_blacklist:list[int] = []  # Model IDs of trophies that should not be deposited
        self.deposit_materials_blacklist:list[int] = []  # Model IDs of materials that should not be deposited
        self.deposit_event_items_blacklist:list[int] = []  # Model IDs of event items that should not
        self.deposit_dyes_blacklist:list[int] = []  # Model IDs of dyes that should not be deposited
        self.deposit_model_blacklist:list[int] = []  # Model IDs of items that should not be deposited

        self._initialized = True

                
    def IdentifyItems(self,progress_callback: Optional[Callable[[float], None]] = None, log: bool = False):
        from ..ItemArray import ItemArray
        from ..enums import Bags
        from ..Inventory import Inventory
        import PyItem
        from ..Item import Item
        from ..Routines import Routines
        
        bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
        item_array = ItemArray.GetItemArray(bag_list)
        
        identified_items = 0
            
        for item_id in item_array:
            first_id_kit = Inventory.GetFirstIDKit()
             
            if first_id_kit == 0:
                Console.Log("AutoIdentify", "No ID Kit found in inventory.", Console.MessageType.Warning)
                return   
                
            item_instance = PyItem.PyItem(item_id)
            is_identified = item_instance.is_identified
                
            if is_identified:
                continue
                
            _,rarity = Item.Rarity.GetRarity(item_id)
            if ((rarity == "White" and self.id_whites) or
                (rarity == "Blue" and self.id_blues) or
                (rarity == "Green" and self.id_greens) or
                (rarity == "Purple" and self.id_purples) or
                (rarity == "Gold" and self.id_golds)):
                ActionQueueManager().AddAction("ACTION", Inventory.IdentifyItem,item_id, first_id_kit)
                identified_items += 1
                while True:
                    yield from Routines.Yield.wait(50)
                    item_instance.GetContext()
                    if item_instance.is_identified:
                        break
                    
        if identified_items > 0 and log:
            ConsoleLog(self.module_name, f"Identified {identified_items} items", Console.MessageType.Success)
            
    def SalvageItems(self, progress_callback: Optional[Callable[[float], None]] = None, log: bool = False):
        from ..ItemArray import ItemArray
        from ..enums import Bags
        from ..Inventory import Inventory
        import PyItem
        from ..GlobalCache import GLOBAL_CACHE
        from ..Routines import Routines

        bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
        item_array = ItemArray.GetItemArray(bag_list)

        salvaged_items = 0

        for item_id in item_array:
            item_instance = PyItem.PyItem(item_id)
            item_instance.GetContext()
            quantity = item_instance.quantity
            if quantity == 0:
                continue

            is_customized = GLOBAL_CACHE.Item.Properties.IsCustomized(item_id)
            if is_customized:
                # Skip customized items
                continue
            _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            is_white = rarity == "White"
            is_blue = rarity == "Blue"
            is_green = rarity == "Green"
            is_purple = rarity == "Purple"
            is_gold = rarity == "Gold"

            is_material = GLOBAL_CACHE.Item.Type.IsMaterial(item_id)
            is_material_salvageable = GLOBAL_CACHE.Item.Usage.IsMaterialSalvageable(item_id)
            is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)
            is_salvageable = GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id)
            model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
            item_type,_ = GLOBAL_CACHE.Item.GetItemType(item_id)

            # Filtering logic
            if not ((is_white and is_salvageable) or (is_identified and is_salvageable)):
                continue
            if item_type in self.item_type_blacklist:
                continue
            if model_id in self.salvage_blacklist:
                continue
            if is_white and is_material and is_material_salvageable and not self.salvage_rare_materials:
                continue
            if is_white and not is_material and not self.salvage_whites:
                continue
            if is_blue and not self.salvage_blues:
                continue
            if is_purple and not self.salvage_purples:
                continue
            if is_gold and not self.salvage_golds:
                continue

            require_materials_confirmation = is_purple or is_gold

            # Repeat until item no longer exists
            while True:
                
                bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
                item_array = ItemArray.GetItemArray(bag_list)
                if item_id not in item_array:
                    break  # Fully consumed / disappeared
    
                item_instance.GetContext()
                quantity = item_instance.quantity
                if quantity == 0:
                    break

                salvage_kit = Inventory.GetFirstSalvageKit(use_lesser=True)
                if salvage_kit == 0:
                    Console.Log("AutoSalvage", "No Salvage Kit found in inventory.", Console.MessageType.Warning)
                    return

                ActionQueueManager().AddAction("ACTION", Inventory.SalvageItem, item_id, salvage_kit)
                if require_materials_confirmation:
                    yield from Routines.Yield.wait(150)
                    yield from Routines.Yield.Items._wait_for_salvage_materials_window()
                    for i in range(3):
                        ActionQueueManager().AddAction("ACTION", Inventory.AcceptSalvageMaterialsWindow)
                        yield from Routines.Yield.wait(50)

                while True:
                    yield from Routines.Yield.wait(50)

                    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
                    item_array = ItemArray.GetItemArray(bag_list)

                    if item_id not in item_array:
                        salvaged_items += 1
                        break  # Fully consumed

                    item_instance.GetContext()
                    if item_instance.quantity < quantity:
                        salvaged_items += 1
                        break  # Successfully salvaged one item

                yield from Routines.Yield.wait(50)

        if salvaged_items > 0 and log:
            ConsoleLog(self.module_name, f"Salvaged {salvaged_items} items", Console.MessageType.Success)

            
            
    def DepositItemsAuto(self):
        from ..enums import Bags, ModelID
        from ..GlobalCache import GLOBAL_CACHE
        from ..Routines import Routines
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
            item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                # Check if the item is a trophy or material
                is_trophy = GLOBAL_CACHE.Item.Type.IsTrophy(item_id)
                is_tome = GLOBAL_CACHE.Item.Type.IsTome(item_id)
                _, item_type = GLOBAL_CACHE.Item.GetItemType(item_id)
                is_usable = (item_type == "Usable")
                
                is_material = GLOBAL_CACHE.Item.Type.IsMaterial(item_id)
                _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
                is_white =  rarity == "White"
                is_blue = rarity == "Blue"
                is_green = rarity == "Green"
                is_purple = rarity == "Purple"
                is_gold = rarity == "Gold"
                
                model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
                
                is_dye = model_id == ModelID.Vial_Of_Dye.value
                
                if model_id in self.deposit_model_blacklist:
                    continue
                
                if is_material and model_id in self.deposit_materials_blacklist:
                    continue
                
                if is_trophy and model_id in self.deposit_trophies_blacklist:
                    continue
                
                is_dye = (model_id == ModelID.Vial_Of_Dye.value)
                dye1_to_match = None
                if is_dye:
                    dye_info = GLOBAL_CACHE.Item.Customization.GetDyeInfo(item_id)
                    dye1_to_match = dye_info.dye1.ToInt()
                    
                if is_dye and dye1_to_match in self.deposit_dyes_blacklist:
                    continue
                
                
                if is_tome:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_trophy and self.deposit_trophies and is_white:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_material and self.deposit_materials:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_blue and self.deposit_blues:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_purple and self.deposit_purples:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_gold and self.deposit_golds and not is_usable and not is_trophy:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                
                if is_green and self.deposit_greens:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    
                if model_id == ModelID.Vial_Of_Dye.value and self.deposit_dyes:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
                    
                event_items = set()
    
                selected_filters = {
                    "Alcohol": None,          # include ALL subcategories
                    "Sweets": None,           # include ALL subcategories
                    "Party": None,             # include ALL subcategories
                    "Death Penalty Removal": None,  # include ALL subcategories
                    "Reward Trophies" : {"Special Events"},
                }

                # apply filters flexibly
                for category, subcats in LootConfig().LootGroups.items():
                    if category not in selected_filters:
                        continue  # skip whole category

                    allowed_subcats = selected_filters[category]
                    for subcat, items in subcats.items():
                        if allowed_subcats is not None and subcat not in allowed_subcats:
                            continue  # skip this subcategory

                        event_items.update(m.value for m in items)
                        
                if ((model_id in event_items) and 
                    self.deposit_event_items and
                    model_id not in self.deposit_event_items_blacklist):
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    yield from Routines.Yield.wait(350)
            
            
    def IDAndSalvageItems(self, progress_callback: Optional[Callable[[float], None]] = None):
        self.status = "Identifying"
        yield from self.IdentifyItems()
        if progress_callback:
            progress_callback(0.5)
        self.status = "Salvaging"
        yield from self.SalvageItems()
        self.status = "Idle"
        yield
        
    def IDSalvageDepositItems(self):
        from ..Routines import Routines

        #ConsoleLog("AutoInventoryHandler", "Starting ID, Salvage and Deposit routine", Console.MessageType.Info)
        self.status = "Identifying"
        yield from self.IdentifyItems()
        
        self.status = "Salvaging"
        yield from self.SalvageItems()
        
        self.status = "Depositing"
        yield from self.DepositItemsAuto()
        
        self.status = "Depositing Gold"
        
        yield from Routines.Yield.Items.DepositGold(self.keep_gold, log =False)
        
        self.status = "Idle"
        #ConsoleLog("AutoInventoryHandler", "ID, Salvage and Deposit routine completed", Console.MessageType.Success)


#endregion
