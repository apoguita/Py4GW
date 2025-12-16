#region AutoInventory
from typing import Optional, Callable
from .Console import ConsoleLog, Console
from .IniHandler import IniHandler
from .Timer import ThrottledTimer
from .ActionQueue import ActionQueueManager
from .Lootconfig_src import LootConfig
import Py4GW

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
        projects_path = Py4GW.Console.get_projects_path()
        full_path = projects_path + "\\Widgets\\Config\\InventoryPlus.ini"
        self.ini = IniHandler(full_path)
        self.initialized = False
        self.status = "Idle"
        self.outpost_handled = False
        self.module_active = False
        self.module_name = "AutoInventoryHandler"
        
        self.id_whites = False
        self.id_blues = True
        self.id_purples = True
        self.id_golds = False
        self.id_greens = False
        self.id_model_blacklist = []  # Items that should not be identified, even if they match the ID criteria
        
        self.salvage_whites = True
        self.salvage_rare_materials = False
        self.salvage_blues = True
        self.salvage_purples = True
        self.salvage_golds = False
        self.item_type_blacklist = [] # Item types that should not be salvaged, even if they match the salvage criteria
        self.salvage_blacklist = []  # Items that should not be salvaged, even if they match the salvage criteria
        self.blacklisted_model_id = 0
        self.model_id_search = ""
        self.item_type_search = ""
        self.model_id_search_mode = 0  # 0 = Contains, 1 = Starts With
        self.item_type_search_mode = 0  # 0 = Contains, 1 = Starts With
        self.show_dialog_popup = False 
        self.show_item_type_dialog = False
        
        self.deposit_trophies = True
        self.deposit_materials = True
        self.deposit_blues = True
        self.deposit_purples = True
        self.deposit_golds = True
        self.deposit_greens = True
        self.deposit_event_items = True
        self.deposit_dyes = True
        self.keep_gold = 5000
        self.deposit_trophies_blacklist = []  # Model IDs of trophies that should not be deposited
        self.deposit_materials_blacklist = []  # Model IDs of materials that should not be deposited
        self.deposit_event_items_blacklist = []  # Model IDs of event items that should not
        self.deposit_dyes_blacklist = []  # Model IDs of dyes that should not be deposited
        self.deposit_model_blacklist = []  # Model IDs of items that should not be deposited
        
        self.load_from_ini(self.ini, "AutoLootOptions")
        self._initialized = True
           
    def save_to_ini(self, section: str = "AutoLootOptions"):
        self.ini.write_key(section, "module_active", str(self.module_active))
        self.ini.write_key(section, "lookup_time", str(self._LOOKUP_TIME))
        self.ini.write_key(section, "id_whites", str(self.id_whites))
        self.ini.write_key(section, "id_blues", str(self.id_blues))
        self.ini.write_key(section, "id_purples", str(self.id_purples))
        self.ini.write_key(section, "id_golds", str(self.id_golds))
        self.ini.write_key(section, "id_greens", str(self.id_greens))
        self.ini.write_key(section, "id_model_blacklist", ",".join(str(x) for x in sorted(set(self.id_model_blacklist))))

        self.ini.write_key(section, "salvage_whites", str(self.salvage_whites))
        self.ini.write_key(section, "salvage_rare_materials", str(self.salvage_rare_materials))
        self.ini.write_key(section, "salvage_blues", str(self.salvage_blues))
        self.ini.write_key(section, "salvage_purples", str(self.salvage_purples))
        self.ini.write_key(section, "salvage_golds", str(self.salvage_golds))

        self.ini.write_key(section, "item_type_blacklist", ",".join(str(i) for i in sorted(set(self.item_type_blacklist))))
        self.ini.write_key(section, "salvage_blacklist", ",".join(str(i) for i in sorted(set(self.salvage_blacklist))))

        self.ini.write_key(section, "deposit_trophies", str(self.deposit_trophies))
        self.ini.write_key(section, "deposit_materials", str(self.deposit_materials))
        self.ini.write_key(section, "deposit_event_items", str(self.deposit_event_items))
        self.ini.write_key(section, "deposit_dyes", str(self.deposit_dyes))
        self.ini.write_key(section, "deposit_blues", str(self.deposit_blues))
        self.ini.write_key(section, "deposit_purples", str(self.deposit_purples))
        self.ini.write_key(section, "deposit_golds", str(self.deposit_golds))
        self.ini.write_key(section, "deposit_greens", str(self.deposit_greens))
        self.ini.write_key(section, "keep_gold", str(self.keep_gold))
        
        self.ini.write_key(section, "deposit_trophies_blacklist", ",".join(str(x) for x in sorted(set(self.deposit_trophies_blacklist))))
        self.ini.write_key(section, "deposit_materials_blacklist", ",".join(str(x) for x in sorted(set(self.deposit_materials_blacklist))))
        self.ini.write_key(section, "deposit_event_items_blacklist", ",".join(str(x) for x in sorted(set(self.deposit_event_items_blacklist))))
        self.ini.write_key(section, "deposit_dyes_blacklist", ",".join(str(x) for x in sorted(set(self.deposit_dyes_blacklist))))
        self.ini.write_key(section, "deposit_model_blacklist", ",".join(str(x) for x in sorted(set(self.deposit_model_blacklist))))


    def load_from_ini(self, ini:IniHandler | None, section: str = "AutoLootOptions"):
        if not ini:
            ini = self.ini
        self._LOOKUP_TIME = ini.read_int(section, "lookup_time", self._LOOKUP_TIME)
        self.lookup_throttle = ThrottledTimer(self._LOOKUP_TIME)

        self.module_active = ini.read_bool(section, "module_active", self.module_active)
        self.id_whites = ini.read_bool(section, "id_whites", self.id_whites)
        self.id_blues = ini.read_bool(section, "id_blues", self.id_blues)
        self.id_purples = ini.read_bool(section, "id_purples", self.id_purples)
        self.id_golds = ini.read_bool(section, "id_golds", self.id_golds)
        self.id_greens = ini.read_bool(section, "id_greens", self.id_greens)

        self.salvage_whites = ini.read_bool(section, "salvage_whites", self.salvage_whites)
        self.salvage_rare_materials = ini.read_bool(section, "salvage_rare_materials", self.salvage_rare_materials)
        self.salvage_blues = ini.read_bool(section, "salvage_blues", self.salvage_blues)
        self.salvage_purples = ini.read_bool(section, "salvage_purples", self.salvage_purples)
        self.salvage_golds = ini.read_bool(section, "salvage_golds", self.salvage_golds)

        item_type_blacklist_str = ini.read_key(section, "item_type_blacklist", "")
        self.item_type_blacklist = [int(x) for x in item_type_blacklist_str.split(",") if x.strip().isdigit()]

        blacklist_str = ini.read_key(section, "salvage_blacklist", "")
        self.salvage_blacklist = [int(x) for x in blacklist_str.split(",") if x.strip().isdigit()]


        self.deposit_trophies = ini.read_bool(section, "deposit_trophies", self.deposit_trophies)
        self.deposit_materials = ini.read_bool(section, "deposit_materials", self.deposit_materials)
        self.deposit_event_items = ini.read_bool(section, "deposit_event_items", self.deposit_event_items)
        self.deposit_dyes = ini.read_bool(section, "deposit_dyes", self.deposit_dyes)
        self.deposit_blues = ini.read_bool(section, "deposit_blues", self.deposit_blues)
        self.deposit_purples = ini.read_bool(section, "deposit_purples", self.deposit_purples)
        self.deposit_golds = ini.read_bool(section, "deposit_golds", self.deposit_golds)
        self.deposit_greens = ini.read_bool(section, "deposit_greens", self.deposit_greens)

        self.keep_gold = ini.read_int(section, "keep_gold", self.keep_gold)
                
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
            item_model = item_instance.model_id
            if item_model in self.id_model_blacklist:
                continue
                
            if is_identified:
                continue
                
            _,rarity = Item.Rarity.GetRarity(item_id)
            if ((rarity == "White" and self.id_whites) or
                (rarity == "Blue" and self.id_blues) or
                (rarity == "Green" and self.id_greens) or
                (rarity == "Purple" and self.id_purples) or
                (rarity == "Gold" and self.id_golds)):
                yield from Routines.Yield.Items.IdentifyItems([item_id], first_id_kit)
                    
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

                yield from Routines.Yield.Items.SalvageItems([item_id], salvage_kit)

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

        ConsoleLog("AutoInventoryHandler", "Starting ID, Salvage and Deposit routine", Console.MessageType.Info)
        self.status = "Identifying"
        yield from self.IdentifyItems()
        
        self.status = "Salvaging"
        yield from self.SalvageItems()
        
        self.status = "Depositing"
        yield from self.DepositItemsAuto()
        
        self.status = "Depositing Gold"
        
        yield from Routines.Yield.Items.DepositGold(self.keep_gold, log =False)
        
        self.status = "Idle"
        ConsoleLog("AutoInventoryHandler", "ID, Salvage and Deposit routine completed", Console.MessageType.Success)


#endregion
