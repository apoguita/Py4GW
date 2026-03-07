from Py4GWCoreLib import (Color, WindowID, UIManager, Bags, ItemArray, Item, Map,
                          MouseButton, ColorPalette, ModelID,IconsFontAwesome5,
                          Routines, GLOBAL_CACHE,AutoInventoryHandler, ItemType,
                        FrameInfo, WindowFrames, IniHandler, Console, ConsoleLog)
import PyImGui
import Py4GW
from dataclasses import dataclass, field


InventorySlots: list[FrameInfo] = []
auto_handler = AutoInventoryHandler()
projects_path = Py4GW.Console.get_projects_path()
full_path = projects_path + "\\Widgets\\Config\\InventoryPlus.ini"
initialized = False


@dataclass
class ItemSlotData:
    BagID: int
    Slot: int
    ItemID: int
    Rarity: str
    IsIdentified: bool
    IsIDKit : bool
    IsSalvageKit : bool
    ModelID: int
    Quantity: int = 1
    Value : int = 0

hovered_item: ItemSlotData | None = None
selected_item: ItemSlotData | None = None
pop_up_open: bool = False
show_config_window: bool = False

#region dataclasses
@dataclass
class IdentificationSettings:
    identify_whites: bool = field(default_factory=bool)
    identify_blues: bool = field(default_factory=bool)
    identify_greens: bool = field(default_factory=bool)
    identify_purples: bool = field(default_factory=bool)
    identify_golds: bool = field(default_factory=bool)
    identify_all: bool = field(default_factory=bool)
    identify_all_whites: bool = field(default_factory=bool)
    identify_all_blues: bool = field(default_factory=bool)
    identify_all_greens: bool = field(default_factory=bool)
    identify_all_purples: bool = field(default_factory=bool)
    identify_all_golds: bool = field(default_factory=bool)
    
    def load_ini(self, ini: IniHandler):
        s = "IdentificationSettings"

        self.identify_whites = ini.read_bool(s, "identify_whites", False)
        self.identify_blues = ini.read_bool(s, "identify_blues", False)
        self.identify_greens = ini.read_bool(s, "identify_greens", False)
        self.identify_purples = ini.read_bool(s, "identify_purples", False)
        self.identify_golds = ini.read_bool(s, "identify_golds", False)
        self.identify_all = ini.read_bool(s, "identify_all", False)

        self.identify_all_whites  = ini.read_bool(s, "identify_all_whites", False)
        self.identify_all_blues   = ini.read_bool(s, "identify_all_blues", False)
        self.identify_all_greens  = ini.read_bool(s, "identify_all_greens", False)
        self.identify_all_purples = ini.read_bool(s, "identify_all_purples", False)
        self.identify_all_golds   = ini.read_bool(s, "identify_all_golds", False)

    def save_ini(self, ini: IniHandler):
        s = "IdentificationSettings"

        ini.write_key(s, "identify_whites", self.identify_whites)
        ini.write_key(s, "identify_blues", self.identify_blues)
        ini.write_key(s, "identify_greens", self.identify_greens)
        ini.write_key(s, "identify_purples", self.identify_purples)
        ini.write_key(s, "identify_golds", self.identify_golds)
        ini.write_key(s, "identify_all", self.identify_all)

        ini.write_key(s, "identify_all_whites", self.identify_all_whites)
        ini.write_key(s, "identify_all_blues", self.identify_all_blues)
        ini.write_key(s, "identify_all_greens", self.identify_all_greens)
        ini.write_key(s, "identify_all_purples", self.identify_all_purples)
        ini.write_key(s, "identify_all_golds", self.identify_all_golds)
    
    
@dataclass
class SalvageSettings:
    salvage_whites: bool = field(default_factory=bool)
    salvage_blues: bool = field(default_factory=bool)
    salvage_greens: bool = field(default_factory=bool)
    salvage_purples: bool = field(default_factory=bool)
    salvage_golds: bool = field(default_factory=bool)
    salvage_all: bool = field(default_factory=bool)
    salvage_all_whites: bool = field(default_factory=bool)
    salvage_all_blues: bool = field(default_factory=bool)
    salvage_all_greens: bool = field(default_factory=bool)
    salvage_all_purples: bool = field(default_factory=bool)
    salvage_all_golds: bool = field(default_factory=bool)
    
    def load_ini(self, ini: IniHandler):
        s = "SalvageSettings"

        self.salvage_whites = ini.read_bool(s, "salvage_whites", False)
        self.salvage_blues = ini.read_bool(s, "salvage_blues", False)
        self.salvage_greens = ini.read_bool(s, "salvage_greens", False)
        self.salvage_purples = ini.read_bool(s, "salvage_purples", False)
        self.salvage_golds = ini.read_bool(s, "salvage_golds", False)
        self.salvage_all = ini.read_bool(s, "salvage_all", False)


        self.salvage_all_whites  = ini.read_bool(s, "salvage_all_whites", False)
        self.salvage_all_blues   = ini.read_bool(s, "salvage_all_blues", False)
        self.salvage_all_greens  = ini.read_bool(s, "salvage_all_greens", False)
        self.salvage_all_purples = ini.read_bool(s, "salvage_all_purples", False)
        self.salvage_all_golds   = ini.read_bool(s, "salvage_all_golds", False)

    def save_ini(self, ini: IniHandler):
        s = "SalvageSettings"

        ini.write_key(s, "salvage_whites", self.salvage_whites)
        ini.write_key(s, "salvage_blues", self.salvage_blues)
        ini.write_key(s, "salvage_greens", self.salvage_greens)
        ini.write_key(s, "salvage_purples", self.salvage_purples)
        ini.write_key(s, "salvage_golds", self.salvage_golds)
        ini.write_key(s, "salvage_all", self.salvage_all)

        ini.write_key(s, "salvage_all_whites", self.salvage_all_whites)
        ini.write_key(s, "salvage_all_blues", self.salvage_all_blues)
        ini.write_key(s, "salvage_all_greens", self.salvage_all_greens)
        ini.write_key(s, "salvage_all_purples", self.salvage_all_purples)
        ini.write_key(s, "salvage_all_golds", self.salvage_all_golds)
    
@dataclass
class DepositSettings:
    use_ctrl_click: bool = field(default_factory=bool)
    
    def load_ini(self, ini: IniHandler):
        s = "DepositSettings"
        self.use_ctrl_click = ini.read_bool(s, "use_ctrl_click", False)
        
    def save_ini(self, ini: IniHandler):
        s = "DepositSettings"
        ini.write_key(s, "use_ctrl_click", self.use_ctrl_click)
    
    
@dataclass
class ColorizeSettings:
    enable_colorize: bool = False
    color_whites: bool = False
    color_blues: bool = True
    color_greens: bool = True
    color_purples: bool = True
    color_golds: bool = True
    white_color: Color = field(default_factory=lambda: ColorPalette.GetColor("GW_White"))
    blue_color: Color = field(default_factory=lambda: ColorPalette.GetColor("GW_Blue"))
    green_color: Color = field(default_factory=lambda: ColorPalette.GetColor("GW_Green"))
    purple_color: Color = field(default_factory=lambda: ColorPalette.GetColor("GW_Purple"))
    gold_color: Color = field(default_factory=lambda: ColorPalette.GetColor("GW_Gold"))
    
    def load_ini(self, ini: IniHandler):
        s = "ColorizeSettings"

        self.enable_colorize = ini.read_bool(s, "enable_colorize", False)
        self.color_whites = ini.read_bool(s, "color_whites", False)
        self.color_blues = ini.read_bool(s, "color_blues", True)
        self.color_greens = ini.read_bool(s, "color_greens", True)
        self.color_purples = ini.read_bool(s, "color_purples", True)
        self.color_golds = ini.read_bool(s, "color_golds", True)

        self.white_color = Color(*map(int, ini.read_key(s, "white_color", "255,255,255,255").split(",")))
        self.blue_color = Color(*map(int, ini.read_key(s, "blue_color", "255,255,255,255").split(",")))
        self.green_color = Color(*map(int, ini.read_key(s, "green_color", "255,255,255,255").split(",")))
        self.purple_color = Color(*map(int, ini.read_key(s, "purple_color", "255,255,255,255").split(",")))
        self.gold_color = Color(*map(int, ini.read_key(s, "gold_color", "255,255,255,255").split(",")))

    def save_ini(self, ini: IniHandler):
        s = "ColorizeSettings"

        ini.write_key(s, "enable_colorize", self.enable_colorize)
        ini.write_key(s, "color_whites", self.color_whites)
        ini.write_key(s, "color_blues", self.color_blues)
        ini.write_key(s, "color_greens", self.color_greens)
        ini.write_key(s, "color_purples", self.color_purples)
        ini.write_key(s, "color_golds", self.color_golds)

        ini.write_key(s, "white_color", ",".join(map(str, self.white_color.to_tuple())))
        ini.write_key(s, "blue_color", ",".join(map(str, self.blue_color.to_tuple())))
        ini.write_key(s, "green_color", ",".join(map(str, self.green_color.to_tuple())))
        ini.write_key(s, "purple_color", ",".join(map(str, self.purple_color.to_tuple())))
        ini.write_key(s, "gold_color", ",".join(map(str, self.gold_color.to_tuple())))


    
@dataclass
class InventoryPlusConfig:
    identification_settings: IdentificationSettings = field(default_factory=IdentificationSettings)
    salvage_settings: SalvageSettings = field(default_factory=SalvageSettings)
    deposit_settings: DepositSettings = field(default_factory=DepositSettings)
    colorize_settings: ColorizeSettings = field(default_factory=ColorizeSettings)
    
    def load_ini(self, ini: IniHandler):
        self.identification_settings.load_ini(ini)
        self.salvage_settings.load_ini(ini)
        self.deposit_settings.load_ini(ini)
        self.colorize_settings.load_ini(ini)

    def save_ini(self, ini: IniHandler):
        self.identification_settings.save_ini(ini)
        self.salvage_settings.save_ini(ini)
        self.deposit_settings.save_ini(ini)
        self.colorize_settings.save_ini(ini)
    

config_settings = InventoryPlusConfig()
ini_handler = IniHandler(full_path)

def ReadFromIni(ini: IniHandler):
    global config_settings
    config_settings.load_ini(ini)
    
    auto_handler.load_from_ini()


def WriteToIni(ini: IniHandler):
    global config_settings
    config_settings.save_ini(ini)
    auto_handler.save_to_ini()


#region PopUpClasses
class ModelPopUp:
    def __init__(self, title: str, model_dictionary: dict[int, str], current_blacklist: list[int]):
        self.is_open = False
        self.initialized = False
        self.Title = title
        self.model_dictionary = model_dictionary
        self.blacklist = current_blacklist  # live reference
        self.result_blacklist: list[int] | None = None
        self.model_id_search: str = ""
        self.model_id_search_mode: int = 0  # 0 = contains, 1 = starts with
        
    def Show(self):
        if not self.initialized:
            self.initialized = True
            self.result_blacklist = None
            PyImGui.open_popup(self.Title)

        #MUST MATCH open_popup(self.Title)
        if not PyImGui.begin_popup_modal(self.Title, True, PyImGui.WindowFlags.AlwaysAutoResize):
            return

        PyImGui.text(self.Title)
        PyImGui.separator()

        # Search
        self.model_id_search = PyImGui.input_text("Search", self.model_id_search)
        search_lower = self.model_id_search.strip().lower()

        self.model_id_search_mode = PyImGui.radio_button("Contains", self.model_id_search_mode, 0)
        PyImGui.same_line(0,-1)
        self.model_id_search_mode = PyImGui.radio_button("Starts With", self.model_id_search_mode, 1)

        PyImGui.separator()
        
        if PyImGui.begin_table(f"ModelIDTable##{self.Title}", 2):
            PyImGui.table_setup_column("All Models", PyImGui.TableColumnFlags.WidthFixed)
            PyImGui.table_setup_column("Blacklisted Models", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_headers_row()

            PyImGui.table_next_column()
            # LEFT: All Models
            if PyImGui.begin_child(f"ModelIDList", (295, 375), True, PyImGui.WindowFlags.NoFlag):
                sorted_models = sorted(
                    self.model_dictionary.items(),
                    key=lambda x: x[1].lower()  # sort by NAME
                )

                for model_id, name in sorted_models:
                    name_lower = name.lower()

                    if search_lower:
                        if self.model_id_search_mode == 0 and search_lower not in name_lower:
                            continue
                        if self.model_id_search_mode == 1 and not name_lower.startswith(search_lower):
                            continue

                    label = f"{name} ({model_id})"
                    if PyImGui.selectable(label, False, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                        if model_id not in self.blacklist:
                            self.blacklist.append(model_id)
            PyImGui.end_child()

            # RIGHT: Blacklist
            PyImGui.table_next_column()
            if PyImGui.begin_child("BlacklistModelIDList", (295, 375), True, PyImGui.WindowFlags.NoFlag):
                # Create list of (name, model_id) and sort by name
                sorted_blacklist = sorted(
                    self.blacklist,
                    key=lambda mid: self.model_dictionary.get(mid, "").lower()
                )

                for model_id in sorted_blacklist:
                    name = self.model_dictionary.get(model_id, "Unknown")
                    label = f"{name} ({model_id})"
                    if PyImGui.selectable(label, False, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                        self.blacklist.remove(model_id)
            PyImGui.end_child()

            PyImGui.end_table()

        if PyImGui.button("Close"):
            self.is_open = False
            self.initialized = False
            self.result_blacklist = self.blacklist.copy()
            PyImGui.close_current_popup()

        PyImGui.end_popup_modal()
        
#region id_helpers
def _id_items(rarity: str):
    white_items = Routines.Items.GetUnidentifiedItems([rarity], [])
    routine = Routines.Yield.Items.IdentifyItems(white_items, log=True)
    GLOBAL_CACHE.Coroutines.append(routine)
    
def _id_whites():
    _id_items("White")
    
def _id_blues():
    _id_items("Blue")
    
def _id_greens():
    _id_items("Green")
    
def _id_purples():
    _id_items("Purple")
    
def _id_golds():
    _id_items("Gold")
    
def _id_all():
    cfg = config_settings.identification_settings
    rarities = []
    if cfg.identify_all_whites:
        rarities.append("White")
    if cfg.identify_all_blues:
        rarities.append("Blue")
    if cfg.identify_all_greens:
        rarities.append("Green")
    if cfg.identify_all_purples:
        rarities.append("Purple")
    if cfg.identify_all_golds:
        rarities.append("Gold")
    all_items = Routines.Items.GetUnidentifiedItems(rarities, [])
    routine = Routines.Yield.Items.IdentifyItems(all_items, log=True)
    GLOBAL_CACHE.Coroutines.append(routine)
    
#region salvage_helpers
def _salvage_items(rarity: str):
    salvageable_items = Routines.Items.GetSalvageableItems([rarity], [])
    routine = Routines.Yield.Items.SalvageItems(salvageable_items, log=True)
    GLOBAL_CACHE.Coroutines.append(routine)
    
def _salvage_whites():
    _salvage_items("White")
    
def _salvage_blues():
    _salvage_items("Blue")
    
def _salvage_purples():
    _salvage_items("Purple")
    
def _salvage_golds():
    _salvage_items("Gold")
    
def _salvage_all():
    cfg = config_settings.salvage_settings
    rarities = []
    if cfg.salvage_all_whites:
        rarities.append("White")
    if cfg.salvage_all_blues:
        rarities.append("Blue")
    if cfg.salvage_all_greens:
        rarities.append("Green")
    if cfg.salvage_all_purples:
        rarities.append("Purple")
    if cfg.salvage_all_golds:
        rarities.append("Gold")
    all_items = Routines.Items.GetSalvageableItems(rarities, [])
    routine = Routines.Yield.Items.SalvageItems(all_items, log=True)
    GLOBAL_CACHE.Coroutines.append(routine)

#region id_kit_menu_items
def _draw_id_kit_menu_item(selected_item: ItemSlotData):
    global show_config_window, config_settings
    cfg = config_settings.identification_settings
    if cfg.identify_whites:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_White").to_tuple_normalized())
        if PyImGui.menu_item("ID White Items"):
            _id_whites()
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.identify_blues:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Blue").to_tuple_normalized())
        if PyImGui.menu_item("ID Blue Items"):
            _id_blues()
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.identify_purples:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Purple").to_tuple_normalized())
        if PyImGui.menu_item("ID Purple Items"):
            _id_purples()
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.identify_golds:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Gold").to_tuple_normalized())
        if PyImGui.menu_item("ID Gold Items"):
            _id_golds()
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.identify_greens:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Green").to_tuple_normalized())
        if PyImGui.menu_item("ID Green Items"):
            _id_greens()
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
        
    if cfg.identify_all:
        if PyImGui.menu_item("ID All Items"):
            _id_all()
            PyImGui.close_current_popup()
        
    PyImGui.separator()  
    _draw_generic_item_menu_item(selected_item)
   
#region salvage_kit_menu_items     
def _draw_salvage_kit_menu_item(selected_item: ItemSlotData):
    global show_config_window, config_settings
    cfg = config_settings.salvage_settings
    if cfg.salvage_whites:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_White").to_tuple_normalized())
        if PyImGui.menu_item("Salvage White Items"):
            _salvage_whites()
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.salvage_blues:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Blue").to_tuple_normalized())
        if PyImGui.menu_item("Salvage Blue Items"):
            _salvage_blues()
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.salvage_purples:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Purple").to_tuple_normalized())
        if PyImGui.menu_item("Salvage Purple Items"):
            _salvage_purples()
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.salvage_golds:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Gold").to_tuple_normalized())
        if PyImGui.menu_item("Salvage Gold Items"):
            _salvage_golds()
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
        
    if cfg.salvage_all:
        if PyImGui.menu_item("Salvage All Items"):
            _salvage_all()
            PyImGui.close_current_popup()
        
    PyImGui.separator()  
    _draw_generic_item_menu_item(selected_item)
  
#region generic_item_menu_items      
def _draw_generic_item_menu_item(selected_item: ItemSlotData | None = None):
    global show_config_window
    
    if selected_item and not selected_item.IsIdentified:
        if PyImGui.menu_item("Identify"):
            routine = Routines.Yield.Items.IdentifyItems([selected_item.ItemID], log=True)
            GLOBAL_CACHE.Coroutines.append(routine)
            PyImGui.close_current_popup()
            
    if  (selected_item and 
        (selected_item.IsIdentified or selected_item.Rarity != "White") and 
        Routines.Checks.Items.IsSalvageable(selected_item.ItemID)):
        if PyImGui.menu_item("Salvage"):
            routine = Routines.Yield.Items.SalvageItems([selected_item.ItemID], log=True)
            GLOBAL_CACHE.Coroutines.append(routine)
            PyImGui.close_current_popup()
    
    if selected_item:
        if PyImGui.menu_item("Deposit"):
            GLOBAL_CACHE.Inventory.DepositItemToStorage(selected_item.ItemID)
            PyImGui.close_current_popup()
    PyImGui.separator()
    if not GLOBAL_CACHE.Inventory.IsStorageOpen():
        if PyImGui.menu_item("Open Xunlai Vault"):
            GLOBAL_CACHE.Inventory.OpenXunlaiWindow()
            PyImGui.close_current_popup()
    PyImGui.separator()
    label = "Disable Colorize" if config_settings.colorize_settings.enable_colorize else "Enable Colorize"
    if PyImGui.menu_item(label):
        config_settings.colorize_settings.enable_colorize = not config_settings.colorize_settings.enable_colorize   
        PyImGui.close_current_popup()
    PyImGui.separator()
    label = "Disable Auto Inventory" if auto_handler.module_active else "Enable Auto Inventory"
    if PyImGui.menu_item(label):
        auto_handler.module_active = not auto_handler.module_active
        PyImGui.close_current_popup()
    if PyImGui.menu_item("Config Window"):
        show_config_window = True
        PyImGui.close_current_popup()
        
#region PopUps

PopUps: dict[str, ModelPopUp] = {}
model_id_to_name = {member.value: name for name, member in ModelID.__members__.items()}

PopUps["Identification ModelID Lookup"] = ModelPopUp(
    "Identification ModelID Lookup",
    model_id_to_name,
    auto_handler.id_model_blacklist
)

item_type_to_name = {member.value: name for name, member in ItemType.__members__.items()}

PopUps["Salvage Item Type Lookup"] = ModelPopUp(
    "Salvage Item Type Lookup",
    item_type_to_name,
    auto_handler.item_type_blacklist
)

PopUps["Salvage ModelID Lookup"] = ModelPopUp(
    "Salvage ModelID Lookup",
    model_id_to_name,
    auto_handler.salvage_blacklist
)

PopUps["Deposit Trophy ModelID Lookup"] = ModelPopUp(
    "Deposit Trophy ModelID Lookup",
    model_id_to_name,
    auto_handler.deposit_trophies_blacklist
)

PopUps["Depostit Material ModelID Lookup"] = ModelPopUp(
    "Deposit Material ModelID Lookup",
    model_id_to_name,
    auto_handler.deposit_materials_blacklist
)

PopUps["Deposit Event Item ModelID Lookup"] = ModelPopUp(
    "Deposit Event Item ModelID Lookup",
    model_id_to_name,
    auto_handler.deposit_event_items_blacklist
)


PopUps["Deposit Dye ModelID Lookup"] = ModelPopUp(
    "Deposit Dye ModelID Lookup",
    model_id_to_name,
    auto_handler.deposit_dyes_blacklist
)

PopUps["Deposit ModelID Lookup"] = ModelPopUp(
    "Deposit ModelID Lookup",
    model_id_to_name,
    auto_handler.deposit_model_blacklist
)

#region DetectInventoryAction
def DetectInventoryAction():
    global selected_item, show_config_window
    
    if not UIManager.IsWindowVisible(WindowID.WindowID_InventoryBags):
        selected_item = None
        return
    
    # refresh slot frames
    InventorySlots.clear()
    hovered_item = None
    
    for bag_id in range(Bags.Backpack, Bags.Bag2+1):
        bag_to_check = ItemArray.CreateBagList(bag_id)
        item_array = ItemArray.GetItemArray(bag_to_check)

        for item_id in item_array:
            item_instance = Item.item_instance(item_id)
            slot = item_instance.slot
            item = ItemSlotData(
                BagID=bag_id,
                Slot=slot,
                ItemID=item_id,
                Rarity=item_instance.rarity.name,
                IsIdentified=item_instance.is_identified,
                IsIDKit=item_instance.is_id_kit,
                IsSalvageKit=item_instance.is_salvage_kit,
                ModelID=item_instance.model_id,
                Quantity=item_instance.quantity,
                Value=item_instance.value,
            )

            frame = FrameInfo(
                WindowName=f"Slot{bag_id}_{slot}",
                ParentFrameHash=WindowFrames["Inventory Bags"].FrameHash,
                ChildOffsets=[0,0,0,bag_id-1,slot+2],
                BlackBoard={"ItemData": item}
            )
            InventorySlots.append(frame)
            
    #Colorize
    if config_settings.colorize_settings.enable_colorize:
        for slot_frame in InventorySlots:
            item_data: ItemSlotData = slot_frame.BlackBoard["ItemData"]
            
            if (item_data.Rarity == "White" and not config_settings.colorize_settings.color_whites) or \
               (item_data.Rarity == "Blue" and not config_settings.colorize_settings.color_blues) or \
                (item_data.Rarity == "Green" and not config_settings.colorize_settings.color_greens) or \
                (item_data.Rarity == "Purple" and not config_settings.colorize_settings.color_purples) or \
                (item_data.Rarity == "Gold" and not config_settings.colorize_settings.color_golds):
                continue
            
            if item_data.Rarity == "White":
                border_color = config_settings.colorize_settings.white_color
            elif item_data.Rarity == "Blue":
                border_color = config_settings.colorize_settings.blue_color
            elif item_data.Rarity == "Green":
                border_color = config_settings.colorize_settings.green_color
            elif item_data.Rarity == "Purple":
                border_color = config_settings.colorize_settings.purple_color
            elif item_data.Rarity == "Gold":
                border_color = config_settings.colorize_settings.gold_color
            else:
                border_color = Color(0, 0, 0, 0)
                
            color:Color = border_color.copy()
            color.set_a(25)
            border_color.set_a(125)

            slot_frame.DrawFrame(color=color.to_color())
            slot_frame.DrawFrameOutline(border_color.to_color())


    io = PyImGui.get_io()

    # Detect right click
    if PyImGui.is_mouse_released(MouseButton.Right.value):

        # Only trigger if user clicked over inventory window
        if WindowFrames["Inventory Bags"].IsMouseOver():
            
            selected_item = None  # first assume empty click
            for slot_frame in InventorySlots:
                if slot_frame.IsMouseOver():
                    selected_item = slot_frame.BlackBoard["ItemData"]
                    break

            PyImGui.open_popup("SlotContextMenu")
            
    # Detect Ctrl + Left Click
    if PyImGui.is_mouse_released(MouseButton.Left.value) and io.key_ctrl:
        if WindowFrames["Inventory Bags"].IsMouseOver():
            for slot_frame in InventorySlots:
                if slot_frame.IsMouseOver():
                    selected_item = slot_frame.BlackBoard["ItemData"]
                    if selected_item and config_settings.deposit_settings.use_ctrl_click:
                        GLOBAL_CACHE.Inventory.DepositItemToStorage(selected_item.ItemID)
                    return


    # Render popup
    if PyImGui.begin_popup("SlotContextMenu"):

        if selected_item:
            if selected_item.IsIDKit:
                _draw_id_kit_menu_item(selected_item)        
            elif selected_item.IsSalvageKit and selected_item.ModelID == ModelID.Salvage_Kit:
                _draw_salvage_kit_menu_item(selected_item)
            else:
                _draw_generic_item_menu_item(selected_item)
        else:
            _draw_generic_item_menu_item()

        PyImGui.end_popup()

    else:
        # popup is not open → clear selection
        selected_item = None




def _colored_checkbox(label: str, value: bool, color: Color) -> bool:
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color.to_tuple_normalized())
    value = PyImGui.checkbox(label, value)
    PyImGui.pop_style_color(1)
    return value

#region ShowConfigWindow
def DrawPopUps():
    for popup in PopUps.values():
        if popup.is_open:
            popup.Show()
            if popup.result_blacklist is not None:
                # Update the corresponding blacklist in auto_handler
                if popup.Title == "Identification ModelID Lookup":
                    auto_handler.id_model_blacklist = popup.result_blacklist
                elif popup.Title == "Salvage Item Type Lookup":
                    auto_handler.item_type_blacklist = popup.result_blacklist
                elif popup.Title == "Salvage ModelID Lookup":
                    auto_handler.salvage_blacklist = popup.result_blacklist
                elif popup.Title == "Deposit Trophy ModelID Lookup":
                    auto_handler.deposit_trophies_blacklist = popup.result_blacklist
                elif popup.Title == "Depostit Material ModelID Lookup":
                    auto_handler.deposit_materials_blacklist = popup.result_blacklist
                elif popup.Title == "Deposit Event Item ModelID Lookup":
                    auto_handler.deposit_event_items_blacklist = popup.result_blacklist
                elif popup.Title == "Deposit Dye ModelID Lookup":
                    auto_handler.deposit_dyes_blacklist = popup.result_blacklist
                elif popup.Title == "Deposit ModelID Lookup":
                    auto_handler.deposit_model_blacklist = popup.result_blacklist
            


def ShowConfigWindow():
    global show_config_window, config_settings
    
    GW_WHITE = ColorPalette.GetColor("GW_White")
    GW_BLUE = ColorPalette.GetColor("GW_Blue")
    GW_PURPLE = ColorPalette.GetColor("GW_Purple")
    GW_GOLD = ColorPalette.GetColor("GW_Gold")
    GW_GREEN = ColorPalette.GetColor("GW_Green")
    
    expanded, show_config_window = PyImGui.begin_with_close("Inventory + Configuration", show_config_window, PyImGui.WindowFlags.AlwaysAutoResize)
    if expanded:
        if PyImGui.begin_tab_bar("InventoryPlusConfigTabs"):
            cfg = config_settings.identification_settings
            if PyImGui.begin_tab_item("Identification"):
                if PyImGui.collapsing_header("Identification Menu Options:"):
                    cfg.identify_whites = _colored_checkbox("Show ID Whites in Menu", cfg.identify_whites, GW_WHITE)
                    cfg.identify_blues = _colored_checkbox("Show ID Blues in Menu", cfg.identify_blues, GW_BLUE)
                    cfg.identify_purples = _colored_checkbox("Show ID Purples in Menu", cfg.identify_purples, GW_PURPLE)
                    cfg.identify_golds = _colored_checkbox("Show ID Golds in Menu", cfg.identify_golds, GW_GOLD)
                    cfg.identify_greens = _colored_checkbox("Show ID Greens in Menu", cfg.identify_greens, GW_GREEN)
                    cfg.identify_all = PyImGui.checkbox("Show ID All in Menu", cfg.identify_all)
                    if cfg.identify_all:
                        PyImGui.indent(20)
                        cfg.identify_all_whites = _colored_checkbox("Include Whites", cfg.identify_all_whites, GW_WHITE)
                        cfg.identify_all_blues = _colored_checkbox("Include Blues", cfg.identify_all_blues, GW_BLUE)
                        cfg.identify_all_greens = _colored_checkbox("Include Greens", cfg.identify_all_greens, GW_GREEN)
                        cfg.identify_all_purples = _colored_checkbox("Include Purples", cfg.identify_all_purples, GW_PURPLE)
                        cfg.identify_all_golds = _colored_checkbox("Include Golds", cfg.identify_all_golds, GW_GOLD)
                        PyImGui.unindent(20)
                PyImGui.separator()
                if PyImGui.collapsing_header("Ignore Models:"):
                    PyImGui.text("List Of Specific Item Model IDs to ignore from Identification")
                    if PyImGui.button("Manage Model Blacklist"):
                        PopUps["Identification ModelID Lookup"].is_open = True
                    if PyImGui.is_item_hovered():
                        PyImGui.begin_tooltip()
                        PyImGui.text(f"{len(auto_handler.id_model_blacklist)} Models Ignored")
                        PyImGui.end_tooltip()
                    PyImGui.same_line(0,-1)
                    PyImGui.text(f"{len(auto_handler.id_model_blacklist)} Models Ignored")
                    
                PyImGui.separator()
                if PyImGui.collapsing_header("Automatic Handling Options:"):
                    color = ColorPalette.GetColor("dark_red")
                    PyImGui.text_colored("This settings will periodically identify items in your inventory based on the options below.", color.to_tuple_normalized())
                    PyImGui.text_colored("Also Used by most Bots and other scripts, this is where they will check to see what to Identify.", color.to_tuple_normalized())
                    auto_handler.id_whites = _colored_checkbox("Automatically ID Whites", auto_handler.id_whites, GW_WHITE)
                    auto_handler.id_blues = _colored_checkbox("Automatically ID Blues", auto_handler.id_blues, GW_BLUE)
                    auto_handler.id_purples = _colored_checkbox("Automatically ID Purples", auto_handler.id_purples, GW_PURPLE)
                    auto_handler.id_golds = _colored_checkbox("Automatically ID Golds", auto_handler.id_golds, GW_GOLD)
                    auto_handler.id_greens = _colored_checkbox("Automatically ID Greens", auto_handler.id_greens, GW_GREEN)
                    PyImGui.separator()
                                 
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Salvage"):
                cfg = config_settings.salvage_settings
                if PyImGui.collapsing_header("Salvage Menu Options:"):
                    color = ColorPalette.GetColor("dark_red")
                    PyImGui.text_colored("This settings will periodically salvage items for MATERIALS in your inventory based on the options below.", color.to_tuple_normalized())
                    PyImGui.text_colored("this script does not handle mods yet.", color.to_tuple_normalized())
                    PyImGui.separator()
                    cfg.salvage_whites = _colored_checkbox("Show Salvage Whites in Menu", cfg.salvage_whites, GW_WHITE)
                    cfg.salvage_blues = _colored_checkbox("Show Salvage Blues in Menu", cfg.salvage_blues, GW_BLUE)
                    cfg.salvage_purples = _colored_checkbox("Show Salvage Purples in Menu", cfg.salvage_purples, GW_PURPLE)
                    cfg.salvage_golds = _colored_checkbox("Show Salvage Golds in Menu", cfg.salvage_golds, GW_GOLD)
                    cfg.salvage_all = PyImGui.checkbox("Show Salvage All in Menu", cfg.salvage_all)
                    if cfg.salvage_all:
                        PyImGui.indent(20)
                        cfg.salvage_all_whites = _colored_checkbox("Include Whites", cfg.salvage_all_whites, GW_WHITE)
                        cfg.salvage_all_blues = _colored_checkbox("Include Blues", cfg.salvage_all_blues, GW_BLUE)
                        cfg.salvage_all_greens = _colored_checkbox("Include Greens", cfg.salvage_all_greens, GW_GREEN)
                        cfg.salvage_all_purples = _colored_checkbox("Include Purples", cfg.salvage_all_purples, GW_PURPLE)
                        cfg.salvage_all_golds = _colored_checkbox("Include Golds", cfg.salvage_all_golds, GW_GOLD)
                        PyImGui.unindent(20)
                PyImGui.separator() 
                if PyImGui.collapsing_header("Ignore Lists:"):
                    if PyImGui.button("Ignore Type"):
                        PopUps["Salvage Item Type Lookup"].is_open = True
                    if PyImGui.is_item_hovered():
                        PyImGui.begin_tooltip()
                        PyImGui.text(f"{len(auto_handler.item_type_blacklist)} Types Ignored. (e.g., Weapons, Armor, etc.)")
                        PyImGui.end_tooltip()
                    PyImGui.same_line(0,-1)
                    PyImGui.text(f"{len(auto_handler.item_type_blacklist)} Types Ignored")
                    if PyImGui.button("Ignore Model"):
                        PopUps["Salvage ModelID Lookup"].is_open = True   
                    if PyImGui.is_item_hovered():
                        PyImGui.begin_tooltip()
                        PyImGui.text(f"{len(auto_handler.salvage_blacklist)} Models Ignored")
                        PyImGui.end_tooltip()
                    PyImGui.same_line(0,-1)
                    PyImGui.text(f"{len(auto_handler.salvage_blacklist)} Models Ignored")
                    

                if PyImGui.collapsing_header("Automatic Handling Options:"):
                    color = ColorPalette.GetColor("dark_red")
                    PyImGui.text_colored("This settings will periodically salvage items in your inventory based on the options below.", color.to_tuple_normalized())
                    PyImGui.text_colored("Also Used by most Bots and other scripts, this is where they will check to see what to salvage.", color.to_tuple_normalized())
                    auto_handler.salvage_whites = _colored_checkbox("Automatically Salvage Whites", auto_handler.salvage_whites, GW_WHITE)
                    auto_handler.salvage_rare_materials = PyImGui.checkbox("Automatically Salvage Rare Materials", auto_handler.salvage_rare_materials)
                    auto_handler.salvage_blues = _colored_checkbox("Automatically Salvage Blues", auto_handler.salvage_blues, GW_BLUE)
                    auto_handler.salvage_purples = _colored_checkbox("Automatically Salvage Purples", auto_handler.salvage_purples, GW_PURPLE)
                    auto_handler.salvage_golds = _colored_checkbox("Automatically Salvage Golds", auto_handler.salvage_golds, GW_GOLD)
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Deposit"):
                cfg = config_settings.deposit_settings
                cfg.use_ctrl_click = PyImGui.checkbox("Use Ctrl + Click to Deposit Items", cfg.use_ctrl_click)
                auto_handler.keep_gold = PyImGui.input_int("Keep Minimum Gold In Inventory", auto_handler.keep_gold)
                PyImGui.separator()
                if PyImGui.collapsing_header("Automatic Handling Options:"):
                    PyImGui.text_wrapped("Automatic deposit of items is handled here.")
                    PyImGui.text_wrapped("This feature is used by Bots and other scripts to automatically manage your inventory.")
                    PyImGui.text_wrapped("Each time you enter Outposts Items matching the criteria will be deposited into your Xunlai Vault.")
                    PyImGui.separator()
                    
                    auto_handler.deposit_materials = PyImGui.checkbox(IconsFontAwesome5.ICON_HAMMER + " Deposit Materials", auto_handler.deposit_materials)
                    auto_handler.deposit_trophies = PyImGui.checkbox(IconsFontAwesome5.ICON_TROPHY + " Deposit Trophies", auto_handler.deposit_trophies)
                    auto_handler.deposit_event_items = PyImGui.checkbox(IconsFontAwesome5.ICON_HAT_WIZARD + " Deposit Event Items", auto_handler.deposit_event_items)
                    auto_handler.deposit_dyes = PyImGui.checkbox(IconsFontAwesome5.ICON_FLASK + " Deposit Dyes", auto_handler.deposit_dyes)
                    auto_handler.deposit_blues = _colored_checkbox("Deposit Blues", auto_handler.deposit_blues, GW_BLUE)
                    auto_handler.deposit_purples = _colored_checkbox("Deposit Purples", auto_handler.deposit_purples, GW_PURPLE)
                    auto_handler.deposit_golds = _colored_checkbox("Deposit Golds", auto_handler.deposit_golds, GW_GOLD)
                    auto_handler.deposit_greens = _colored_checkbox("Deposit Greens", auto_handler.deposit_greens, GW_GREEN)

                
                if PyImGui.collapsing_header("Ignore Lists:"):
                    PyImGui.text("Manage the various blacklists for deposit handling here.")
                    if PyImGui.button("Material Blacklist"):
                        PopUps["Depostit Material ModelID Lookup"].is_open = True
                    PyImGui.same_line(0,-1)
                    PyImGui.text(f"{len(auto_handler.deposit_materials_blacklist)} Models Ignored")
                    if PyImGui.button("Manage Trophy Blacklist"):
                        PopUps["Deposit Trophy ModelID Lookup"].is_open = True
                    PyImGui.same_line(0,-1)
                    PyImGui.text(f"{len(auto_handler.deposit_trophies_blacklist)} Models Ignored")
                    if PyImGui.button("Manage Event Item Blacklist"):
                        PopUps["Deposit Event Item ModelID Lookup"].is_open = True
                    PyImGui.same_line(0,-1)
                    PyImGui.text(f"{len(auto_handler.deposit_event_items_blacklist)} Models Ignored")
                    if PyImGui.button("Manage Dye Blacklist"):
                        PopUps["Deposit Dye ModelID Lookup"].is_open = True
                    PyImGui.same_line(0,-1)
                    PyImGui.text(f"{len(auto_handler.deposit_dyes_blacklist)} Colors Ignored")
                    if PyImGui.button("Model Blacklist"):
                        PopUps["Deposit ModelID Lookup"].is_open = True
                    PyImGui.same_line(0,-1)
                    PyImGui.text(f"{len(auto_handler.deposit_model_blacklist)} Models Ignored")
                    
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Colorize"):
                cfg = config_settings.colorize_settings
                cfg.enable_colorize = PyImGui.checkbox("Enable Colorize Inventory Items", cfg.enable_colorize)
                PyImGui.separator()
                cfg.color_whites = _colored_checkbox("Color White Items", cfg.color_whites, GW_WHITE)
                cfg.color_blues = _colored_checkbox("Color Blue Items", cfg.color_blues, GW_BLUE)
                cfg.color_greens = _colored_checkbox("Color Green Items", cfg.color_greens, GW_GREEN)
                cfg.color_purples = _colored_checkbox("Color Purple Items", cfg.color_purples, GW_PURPLE)
                cfg.color_golds = _colored_checkbox("Color Gold Items", cfg.color_golds, GW_GOLD)
                PyImGui.separator()
                color = PyImGui.color_edit4("White Item Color", cfg.white_color.to_tuple_normalized())
                cfg.white_color = Color(int(255*color[0]), int(255*color[1]), int(255*color[2]), int(255*color[3]))
                color = PyImGui.color_edit4("Blue Item Color", cfg.blue_color.to_tuple_normalized())
                cfg.blue_color = Color(int(255*color[0]), int(255*color[1]), int(255*color[2]), int(255*color[3]))
                color = PyImGui.color_edit4("Green Item Color", cfg.green_color.to_tuple_normalized())
                cfg.green_color = Color(int(255*color[0]), int(255*color[1]), int(255*color[2]), int(255*color[3]))
                color = PyImGui.color_edit4("Purple Item Color", cfg.purple_color.to_tuple_normalized())
                cfg.purple_color = Color(int(255*color[0]), int(255*color[1]), int(255*color[2]), int(255*color[3]))
                color = PyImGui.color_edit4("Gold Item Color", cfg.gold_color.to_tuple_normalized())
                cfg.gold_color = Color(int(255*color[0]), int(255*color[1]), int(255*color[2]), int(255*color[3]))
                    
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Auto Handler"):
                PyImGui.text_wrapped("Automatic Identification, Salvaging and Deposit is handled here.")
                PyImGui.text_wrapped("This feature is used by Bots and other scripts to automatically manage your inventory.")
                PyImGui.text_wrapped("Enable the options in the Identification and Salvage tabs to activate automatic handling for those item rarities.")
                auto_handler.module_active = PyImGui.checkbox("Enable Automatic Inventory Management", auto_handler.module_active)
                auto_handler._LOOKUP_TIME = PyImGui.input_int("Inventory Check Interval (ms)", auto_handler._LOOKUP_TIME)
                color = ColorPalette.GetColor("dark_red")
                if Routines.Checks.Map.IsOutpost():
                    PyImGui.text_colored("Timer is paused in Outposts.", color.to_tuple_normalized())
                PyImGui.text(f"next check in {max(0, auto_handler._LOOKUP_TIME - auto_handler.lookup_throttle.GetTimeElapsed()):.3f} ms")
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()
        PyImGui.separator()
        if PyImGui.button("Cancel"):
            show_config_window = False
        PyImGui.same_line(0,-1)
        if PyImGui.button("Save & Close"):
            WriteToIni(ini_handler)
            ReadFromIni(ini_handler)
            show_config_window = False
    PyImGui.end()

#region auto_handler
def update_auto_handler():
    if not Routines.Checks.Map.MapValid():
        auto_handler.lookup_throttle.Reset()
        auto_handler.outpost_handled = False
        return False
    
    if not auto_handler.initialized:
        auto_handler.load_from_ini()
        auto_handler.lookup_throttle.SetThrottleTime(auto_handler._LOOKUP_TIME)
        auto_handler.lookup_throttle.Reset()
        auto_handler.initialized = True
        ConsoleLog("AutoInventoryHandler", "Auto Handler Options initialized", Py4GW.Console.MessageType.Success)
        
    if not Map.IsExplorable():
        auto_handler.lookup_throttle.Stop()
        auto_handler.status = "Idle"
        if not auto_handler.outpost_handled and auto_handler.module_active:
            GLOBAL_CACHE.Coroutines.append(auto_handler.IDSalvageDepositItems())
            auto_handler.outpost_handled = True
    else:      
        if auto_handler.lookup_throttle.IsStopped():
            auto_handler.lookup_throttle.Start()
            auto_handler.status = "Idle"
            
    if auto_handler.lookup_throttle.IsExpired():
        auto_handler.lookup_throttle.SetThrottleTime(auto_handler._LOOKUP_TIME)
        auto_handler.lookup_throttle.Stop()
        if auto_handler.status == "Idle" and auto_handler.module_active:
            GLOBAL_CACHE.Coroutines.append(auto_handler.IDAndSalvageItems())
        auto_handler.lookup_throttle.Start()       
      

#region main
def configure():
    ShowConfigWindow()

def main():
    global initialized, ini_handler, show_config_window
    
    if not initialized:
        ReadFromIni(ini_handler)
        initialized = True
    
    if auto_handler.module_active:
        update_auto_handler()    
    
    DetectInventoryAction()
    if show_config_window:
        ShowConfigWindow()
        DrawPopUps()


if __name__ == "__main__":
    main()
