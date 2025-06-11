from Py4GWCoreLib import *

MODULE_NAME = "Auto Inv"



class WidgetOptions():
    def __init__(self):
        self.name = MODULE_NAME
        self._LOOKUP_TIME:int = 15000
        self.lookup_throttle = ThrottledTimer(self._LOOKUP_TIME)
        self.ini = IniHandler("Auto Inv.ini")
        self.initialized = False
        self.status = "Idle"
        self.outpost_handled = False
        
        self.id_whites = False
        self.id_blues = True
        self.id_purples = True
        self.id_golds = False
        self.id_greens = False
        
        self.salvage_whites = True
        self.salvage_rare_materials = False
        self.salvage_blues = True
        self.salvage_purples = True
        self.salvage_golds = False
        self.salvage_blacklist = []  # Items that should not be salvaged, even if they match the salvage criteria
        self.blacklisted_model_id = 0
        self.model_id_search = ""
        self.model_id_search_mode = 0  # 0 = Contains, 1 = Starts With
        self.show_dialog_popup = False 
        
        self.deposit_trophies = True
        self.deposit_materials = True
        self.deposit_blues = True
        self.deposit_purples = True
        self.deposit_golds = True
        self.deposit_greens = True
        self.keep_gold = 5000
        
        
        
    def save_to_ini(self, section: str = "WidgetOptions"):
        self.ini.write_key(section, "lookup_time", str(self._LOOKUP_TIME))
        self.ini.write_key(section, "id_whites", str(self.id_whites))
        self.ini.write_key(section, "id_blues", str(self.id_blues))
        self.ini.write_key(section, "id_purples", str(self.id_purples))
        self.ini.write_key(section, "id_golds", str(self.id_golds))
        self.ini.write_key(section, "id_greens", str(self.id_greens))

        self.ini.write_key(section, "salvage_whites", str(self.salvage_whites))
        self.ini.write_key(section, "salvage_rare_materials", str(self.salvage_rare_materials))
        self.ini.write_key(section, "salvage_blues", str(self.salvage_blues))
        self.ini.write_key(section, "salvage_purples", str(self.salvage_purples))
        self.ini.write_key(section, "salvage_golds", str(self.salvage_golds))

        self.ini.write_key(section, "salvage_blacklist", ",".join(str(i) for i in sorted(set(self.salvage_blacklist))))

        self.ini.write_key(section, "deposit_trophies", str(self.deposit_trophies))
        self.ini.write_key(section, "deposit_materials", str(self.deposit_materials))
        self.ini.write_key(section, "deposit_blues", str(self.deposit_blues))
        self.ini.write_key(section, "deposit_purples", str(self.deposit_purples))
        self.ini.write_key(section, "deposit_golds", str(self.deposit_golds))
        self.ini.write_key(section, "deposit_greens", str(self.deposit_greens))
        self.ini.write_key(section, "keep_gold", str(self.keep_gold))


    def load_from_ini(self, ini: IniHandler, section: str = "WidgetOptions"):
        self._LOOKUP_TIME = ini.read_int(section, "lookup_time", self._LOOKUP_TIME)
        self.lookup_throttle = ThrottledTimer(self._LOOKUP_TIME)

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

        blacklist_str = ini.read_key(section, "salvage_blacklist", "")
        self.salvage_blacklist = [int(x) for x in blacklist_str.split(",") if x.strip().isdigit()]


        self.deposit_trophies = ini.read_bool(section, "deposit_trophies", self.deposit_trophies)
        self.deposit_materials = ini.read_bool(section, "deposit_materials", self.deposit_materials)
        self.deposit_blues = ini.read_bool(section, "deposit_blues", self.deposit_blues)
        self.deposit_purples = ini.read_bool(section, "deposit_purples", self.deposit_purples)
        self.deposit_golds = ini.read_bool(section, "deposit_golds", self.deposit_golds)
        self.deposit_greens = ini.read_bool(section, "deposit_greens", self.deposit_greens)

        self.keep_gold = ini.read_int(section, "keep_gold", self.keep_gold)



widget_options = WidgetOptions()

def show_dialog_popup():
    global widget_options
    
    if widget_options.show_dialog_popup:
        PyImGui.open_popup("ModelID Lookup")
        widget_options.show_dialog_popup = False  # trigger only once

    if PyImGui.begin_popup_modal("ModelID Lookup", True,PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text("ModelID Lookup")
        PyImGui.separator()

        # Input + filter mode
        widget_options.model_id_search = PyImGui.input_text("Search", widget_options.model_id_search)
        search_lower = widget_options.model_id_search.strip().lower()

        widget_options.model_id_search_mode = PyImGui.radio_button("Contains", widget_options.model_id_search_mode, 0)
        PyImGui.same_line(0, -1)
        widget_options.model_id_search_mode = PyImGui.radio_button("Starts With", widget_options.model_id_search_mode, 1)

        # Build reverse lookup: model_id → name
        model_id_to_name = {member.value: name for name, member in ModelID.__members__.items()}

        PyImGui.separator()

        if PyImGui.begin_table("ModelIDTable", 2):
            PyImGui.table_setup_column("All Models", PyImGui.TableColumnFlags.WidthFixed)
            PyImGui.table_setup_column("Blacklisted Models", PyImGui.TableColumnFlags.WidthStretch)
        
            PyImGui.table_headers_row()
            PyImGui.table_next_column()
            # LEFT: All Models
            if PyImGui.begin_child("ModelIDList", (295, 375), True, PyImGui.WindowFlags.NoFlag):
                sorted_model_ids = sorted(
                    [(name, member.value) for name, member in ModelID.__members__.items()],
                    key=lambda x: x[0].lower()
                )
                for name, model_id in sorted_model_ids:
                    name_lower = name.lower()
                    if search_lower:
                        if widget_options.model_id_search_mode == 0 and search_lower not in name_lower:
                            continue
                        if widget_options.model_id_search_mode == 1 and not name_lower.startswith(search_lower):
                            continue

                    label = f"{name} ({model_id})"
                    if PyImGui.selectable(label, False, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                        if model_id not in widget_options.salvage_blacklist:
                            widget_options.salvage_blacklist.append(model_id)
            PyImGui.end_child()

            # RIGHT: Blacklist
            PyImGui.table_next_column()
            if PyImGui.begin_child("BlacklistModelIDList", (295, 375), True, PyImGui.WindowFlags.NoFlag):
                # Create list of (name, model_id) and sort by name
                sorted_blacklist = sorted(
                    [(model_id_to_name.get(model_id, "Unknown"), model_id)
                    for model_id in widget_options.salvage_blacklist],
                    key=lambda x: x[0].lower()
                )

                for name, model_id in sorted_blacklist:
                    label = f"{name} ({model_id})"
                    if PyImGui.selectable(label, False, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                        widget_options.salvage_blacklist.remove(model_id)
            PyImGui.end_child()



            PyImGui.end_table()

        if PyImGui.button("Close"):
            PyImGui.close_current_popup()

        PyImGui.end_popup_modal()


def ShowWindow():
    global widget_options
    try:
        if PyImGui.begin("Auto ID & Salvager Options##AutoID&Salvage",PyImGui.WindowFlags.AlwaysAutoResize):
            if PyImGui.button(IconsFontAwesome5.ICON_SAVE + "##autosalvsave"):
                widget_options.save_to_ini()
                ConsoleLog(MODULE_NAME, "Settings saved to Auto Inv.ini", Py4GW.Console.MessageType.Success)
            ImGui.show_tooltip("Save Settings")
            PyImGui.same_line(0,-1)
            if PyImGui.button(IconsFontAwesome5.ICON_SYNC + "##autosalvreload"):
                widget_options.load_from_ini(widget_options.ini)
                widget_options.lookup_throttle.SetThrottleTime(widget_options._LOOKUP_TIME)
                widget_options.lookup_throttle.Reset()
                ConsoleLog(MODULE_NAME, "Settings reloaded from Auto Inv.ini", Py4GW.Console.MessageType.Success)
            ImGui.show_tooltip("Reload Settings")
            
            PyImGui.separator()

            PyImGui.text("Lookup Time (ms):")
            PyImGui.same_line(0,-1)
            widget_options._LOOKUP_TIME = PyImGui.input_int("##lookup_time",  widget_options._LOOKUP_TIME)
            ImGui.show_tooltip("Changes will take effect after the next lookup.")
            
            if not GLOBAL_CACHE.Map.IsExplorable():
                PyImGui.text("Auto Lookup only runs in explorable maps.")
            else:
                remaining = widget_options.lookup_throttle.GetTimeRemaining() / 1000  # convert ms to seconds
                PyImGui.text(f"Next Lookup in: {remaining:.1f} s")

            if PyImGui.begin_tab_bar("AutoID&SalvageTabs"):
                if PyImGui.begin_tab_item("Identification"):
                    widget_options.id_whites = PyImGui.checkbox("White Items", widget_options.id_whites)
                    widget_options.id_blues = PyImGui.checkbox("Blue Items", widget_options.id_blues)
                    widget_options.id_purples = PyImGui.checkbox("Purple Items", widget_options.id_purples)
                    widget_options.id_golds = PyImGui.checkbox("Gold Items", widget_options.id_golds)
                    widget_options.id_greens = PyImGui.checkbox("Green Items", widget_options.id_greens)
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Salvage"):
                    widget_options.salvage_whites = PyImGui.checkbox("White Items", widget_options.salvage_whites)
                    widget_options.salvage_rare_materials = PyImGui.checkbox("Rare Materials", widget_options.salvage_rare_materials and widget_options.salvage_whites)
                    widget_options.salvage_blues = PyImGui.checkbox("Blue Items", widget_options.salvage_blues)
                    widget_options.salvage_purples = PyImGui.checkbox("Purple Items", widget_options.salvage_purples)
                    widget_options.salvage_golds = PyImGui.checkbox("Gold Items", widget_options.salvage_golds)
                    
                    if PyImGui.collapsing_header("Ignore Items"):
                        PyImGui.text("Items that should not be salvaged, even if they match the salvage criteria")
                        PyImGui.separator()
                        PyImGui.text("Hover an Item on your Inventory to get its ModelID or add it manually")
                        PyImGui.separator()
                        
                        hovered_item = GLOBAL_CACHE.Inventory.GetHoveredItemID()
                        
                        if hovered_item:
                            widget_options.blacklisted_model_id = hovered_item
                            
                        PyImGui.text(f"{len(widget_options.salvage_blacklist)} Blacklisted ModelIDs")
                        widget_options.blacklisted_model_id = PyImGui.input_int("ModelID", widget_options.blacklisted_model_id, 1, 1000, PyImGui.InputTextFlags.NoFlag)
                        PyImGui.same_line(0,-1)
                        if PyImGui.button("Manage Ignore List"):
                            widget_options.show_dialog_popup = True
                            
                        if PyImGui.button("Add ModelID"):
                            if widget_options.blacklisted_model_id not in widget_options.salvage_blacklist:
                                widget_options.salvage_blacklist.append(widget_options.blacklisted_model_id)

                            widget_options.blacklisted_model_id = 0
                            
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Deposit"):
                    widget_options.deposit_materials = PyImGui.checkbox("Deposit Materials", widget_options.deposit_materials)
                    widget_options.deposit_trophies = PyImGui.checkbox("Deposit Trophies", widget_options.deposit_trophies)
                    widget_options.deposit_blues = PyImGui.checkbox("Deposit Blue Items", widget_options.deposit_blues)
                    widget_options.deposit_purples = PyImGui.checkbox("Deposit Purple Items", widget_options.deposit_purples)
                    widget_options.deposit_golds = PyImGui.checkbox("Deposit Gold Items", widget_options.deposit_golds)
                    widget_options.deposit_greens = PyImGui.checkbox("Deposit Green Items", widget_options.deposit_greens)
                    widget_options.keep_gold = PyImGui.input_int("Keep Gold", widget_options.keep_gold, 1, 1000, PyImGui.InputTextFlags.NoFlag)
            
                    PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
        PyImGui.end()
        
        show_dialog_popup()
            
        


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def AutoID(item_id):
    first_id_kit = Inventory.GetFirstIDKit()
    if first_id_kit == 0:
        ConsoleLog(MODULE_NAME, "No ID Kit found in inventory", Py4GW.Console.MessageType.Warning)
    else:
        Inventory.IdentifyItem(item_id, first_id_kit)
        
def AutoSalvage(item_id):
    first_salv_kit = Inventory.GetFirstSalvageKit(use_lesser=True)
    if first_salv_kit == 0:
        ConsoleLog(MODULE_NAME, "No Salvage Kit found in inventory", Py4GW.Console.MessageType.Warning)
    else:
        Inventory.SalvageItem(item_id, first_salv_kit)
    

            
def IdentifyItems():
    global widget_options
    def _get_total_id_uses():
        total_uses = 0
        for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
            bag_items = GLOBAL_CACHE.ItemArray.GetItemArray(GLOBAL_CACHE.ItemArray.CreateBagList(bag_id))
            for item_id in bag_items:
                if Item.Usage.IsIDKit(item_id):
                    total_uses += Item.Usage.GetUses(item_id)

        return total_uses
    
    total_uses = _get_total_id_uses()
    current_uses = 0
    for bag_id in range(Bags.Backpack, Bags.Bag2+1):
        bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            if total_uses == 0:
                ConsoleLog(MODULE_NAME, f"Identified {current_uses} items, no more ID Kits left in inventory", Py4GW.Console.MessageType.Warning)
                yield
                return
            
            is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)
            
            if is_identified:
                yield
                continue
            
            _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            if ((rarity == "White" and widget_options.id_whites) or
                (rarity == "Blue" and widget_options.id_blues) or
                (rarity == "Green" and widget_options.id_greens) or
                (rarity == "Purple" and widget_options.id_purples) or
                (rarity == "Gold" and widget_options.id_golds)):
                ActionQueueManager().AddAction("IDENTIFY", AutoID, item_id)
                current_uses += 1
                total_uses -= 1
                yield
                
    while not ActionQueueManager().IsEmpty("IDENTIFY"):
        yield from Routines.Yield.wait(100)
                
    if current_uses > 0:
        ConsoleLog(MODULE_NAME, f"Identified {current_uses} items", Py4GW.Console.MessageType.Success)
        
def SalvageItems():
    global widget_options
    def _get_total_salv_uses():
        total_uses = 0
        for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
            bag_items = GLOBAL_CACHE.ItemArray.GetItemArray(GLOBAL_CACHE.ItemArray.CreateBagList(bag_id))
            for item_id in bag_items:
                if Item.Usage.IsLesserKit(item_id):
                    total_uses += Item.Usage.GetUses(item_id)

        return total_uses
    
    total_uses = _get_total_salv_uses()
    current_uses = 0
    for bag_id in range(Bags.Backpack, Bags.Bag2+1):
        bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            if total_uses == 0:
                ConsoleLog(MODULE_NAME, f"Salvaged {current_uses} items, no more Salvage Kits left in inventory", Py4GW.Console.MessageType.Warning)
                yield
                return
            
            quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
            _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            is_white =  rarity == "White"
            is_blue = rarity == "Blue"
            is_green = rarity == "Green"
            is_purple = rarity == "Purple"
            is_gold = rarity == "Gold"
            is_material = GLOBAL_CACHE.Item.Type.IsMaterial(item_id)
            is_material_salvageable = GLOBAL_CACHE.Item.Usage.IsMaterialSalvageable(item_id)
            is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)
            is_salvageable = GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id)
            is_salvage_kit = GLOBAL_CACHE.Item.Usage.IsLesserKit(item_id)
            model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
            
            if not ((is_white and is_salvageable) or (is_identified and is_salvageable)):
                yield
                continue
            
            if model_id in widget_options.salvage_blacklist:
                yield
                continue
            
            if is_white and is_material and is_material_salvageable and not widget_options.salvage_rare_materials:
                yield
                continue
            
            if is_white and not is_material and not widget_options.salvage_whites:
                yield
                continue
            
            if is_blue and not widget_options.salvage_blues:
                yield
                continue
            
            if is_purple and not widget_options.salvage_purples:
                yield
                continue
            
            if is_gold and not widget_options.salvage_golds:
                yield
                continue
            

            for _ in range(quantity):
                ActionQueueManager().AddAction("SALVAGE", AutoSalvage, item_id)
                
                if (is_purple or is_gold):
                    ActionQueueManager().AddAction("SALVAGE", Inventory.AcceptSalvageMaterialsWindow)
                
                current_uses += 1
                total_uses -= 1
                
                while not ActionQueueManager().IsEmpty("SALVAGE"):
                    yield from Routines.Yield.wait(50)
                
                if total_uses == 0:
                    ConsoleLog(MODULE_NAME, f"Salvaged {current_uses} items, no more Salvage Kits left in inventory", Py4GW.Console.MessageType.Warning)
                    yield
                    return

                yield
                
                
    if current_uses > 0:
        ConsoleLog(MODULE_NAME, f"Salvaged {current_uses} items", Py4GW.Console.MessageType.Success)
        
def IDAndSalvageItems():
    """
    This routine will identify and salvage items in the inventory based on the widget options.
    It will first identify all items that match the identification criteria, then salvage all items that match the salvage criteria.
    """
    widget_options.status = "Identifying"
    yield from IdentifyItems()
    widget_options.status = "Salvaging"
    yield from SalvageItems()
    widget_options.status = "Idle"
    yield
    
    
def DepositItems():
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
            
            if is_tome:
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                yield from Routines.Yield.wait(250)
            
            if is_trophy and widget_options.deposit_trophies and is_white:
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                yield from Routines.Yield.wait(250)
            
            if is_material and widget_options.deposit_materials:
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                yield from Routines.Yield.wait(250)
            
            if is_blue and widget_options.deposit_blues:
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                yield from Routines.Yield.wait(250)
            
            if is_purple and widget_options.deposit_purples:
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                yield from Routines.Yield.wait(250)
            
            if is_gold and widget_options.deposit_golds and not is_usable and not is_trophy:
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                yield from Routines.Yield.wait(250)
            
            if is_green and widget_options.deposit_greens:
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                yield from Routines.Yield.wait(250)
                
def IDSalvageDepositItems():
    ConsoleLog(MODULE_NAME, "Starting ID, Salvage and Deposit routine", Py4GW.Console.MessageType.Info)
    widget_options.status = "Identifying"
    yield from IdentifyItems()
    
    widget_options.status = "Salvaging"
    yield from SalvageItems()
    
    widget_options.status = "Depositing"
    yield from DepositItems()
    
    widget_options.status = "Idle"
    ConsoleLog(MODULE_NAME, "ID, Salvage and Deposit routine completed", Py4GW.Console.MessageType.Success)

def main():
    global widget_options
    try:
        if not Routines.Checks.Map.MapValid():
            widget_options.lookup_throttle.Reset()
            return
        
        
        # Load initial settings from INI file
        if not widget_options.initialized:
            widget_options.load_from_ini(widget_options.ini)
            widget_options.lookup_throttle.SetThrottleTime(widget_options._LOOKUP_TIME)
            widget_options.lookup_throttle.Reset()
            widget_options.initialized = True

        ShowWindow()
        
        if not GLOBAL_CACHE.Map.IsExplorable():
            widget_options.lookup_throttle.Stop()
            widget_options.status = "Idle"
            if not widget_options.outpost_handled:
                GLOBAL_CACHE.Coroutines.append(IDSalvageDepositItems())
                widget_options.outpost_handled = True
            return

        
        if widget_options.lookup_throttle.IsStopped():
            widget_options.lookup_throttle.Start()
            widget_options.status = "Idle"
 
        
        if widget_options.lookup_throttle.IsExpired():
            widget_options.lookup_throttle.SetThrottleTime(widget_options._LOOKUP_TIME)
            widget_options.lookup_throttle.Stop()
            if widget_options.status == "Idle":
                GLOBAL_CACHE.Coroutines.append(IDAndSalvageItems())
            widget_options.lookup_throttle.Start()
                

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error during initialization: {str(e)}", Py4GW.Console.MessageType.Error)

    
if __name__ == "__main__":
    main()
