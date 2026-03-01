import PyImGui
import Py4GW
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GWCoreLib.enums_src.Texture_enums import get_texture_for_model


from dataclasses import dataclass, field

INI_PATH = "Inventory/InventoryPlus" #path to save ini key
INI_FILENAME = "InventoryPlus.ini" #ini file name

MODULE_NAME = "Inventory Plus"
MODULE_ICON = "Textures\\Module_Icons\\inventory_plus.png"

#region dataclasses
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
    
@dataclass
class IdentificationSettings:
    identify_whites: bool = field(default_factory=bool)
    identify_blues: bool = field(default_factory=bool)
    identify_greens: bool = field(default_factory=bool)
    identify_purples: bool = field(default_factory=bool)
    identify_golds: bool = field(default_factory=bool)
    show_identify_all: bool = field(default_factory=bool)
    identify_all_whites: bool = field(default_factory=bool)
    identify_all_blues: bool = field(default_factory=bool)
    identify_all_greens: bool = field(default_factory=bool)
    identify_all_purples: bool = field(default_factory=bool)
    identify_all_golds: bool = field(default_factory=bool)
    
    def add_config_vars(self, ini_key: str):
        IniManager().add_bool(key=ini_key, section="Identification", var_name="identify_whites", name="identify_whites", default=self.identify_whites)
        IniManager().add_bool(key=ini_key, section="Identification", var_name="identify_blues", name="identify_blues", default=self.identify_blues)
        IniManager().add_bool(key=ini_key, section="Identification", var_name="identify_greens", name="identify_greens", default=self.identify_greens)
        IniManager().add_bool(key=ini_key, section="Identification", var_name="identify_purples", name="identify_purples", default=self.identify_purples)
        IniManager().add_bool(key=ini_key, section="Identification", var_name="identify_golds", name="identify_golds", default=self.identify_golds)
        IniManager().add_bool(key=ini_key, section="Identification", var_name="show_identify_all", name="show_identify_all", default=self.show_identify_all)

        IniManager().add_bool(key=ini_key, section="Identification", var_name="identify_all_whites", name="identify_all_whites", default=self.identify_all_whites)
        IniManager().add_bool(key=ini_key, section="Identification", var_name="identify_all_blues", name="identify_all_blues", default=self.identify_all_blues)
        IniManager().add_bool(key=ini_key, section="Identification", var_name="identify_all_greens", name="identify_all_greens", default=self.identify_all_greens)
        IniManager().add_bool(key=ini_key, section="Identification", var_name="identify_all_purples", name="identify_all_purples", default=self.identify_all_purples)
        IniManager().add_bool(key=ini_key, section="Identification", var_name="identify_all_golds", name="identify_all_golds", default=self.identify_all_golds)
        
        
@dataclass
class SalvageSettings:
    salvage_whites: bool = field(default_factory=bool)
    salvage_blues: bool = field(default_factory=bool)
    salvage_greens: bool = field(default_factory=bool)
    salvage_purples: bool = field(default_factory=bool)
    salvage_golds: bool = field(default_factory=bool)
    show_salvage_all: bool = field(default_factory=bool)
    salvage_all_whites: bool = field(default_factory=bool)
    salvage_all_blues: bool = field(default_factory=bool)
    salvage_all_greens: bool = field(default_factory=bool)
    salvage_all_purples: bool = field(default_factory=bool)
    salvage_all_golds: bool = field(default_factory=bool)
    
    def add_config_vars(self, ini_key: str):
        IniManager().add_bool(key=ini_key, section="Salvage", var_name="salvage_whites", name="salvage_whites", default=self.salvage_whites)
        IniManager().add_bool(key=ini_key, section="Salvage", var_name="salvage_blues", name="salvage_blues", default=self.salvage_blues)
        IniManager().add_bool(key=ini_key, section="Salvage", var_name="salvage_greens", name="salvage_greens", default=self.salvage_greens)
        IniManager().add_bool(key=ini_key, section="Salvage", var_name="salvage_purples", name="salvage_purples", default=self.salvage_purples)
        IniManager().add_bool(key=ini_key, section="Salvage", var_name="salvage_golds", name="salvage_golds", default=self.salvage_golds)
        IniManager().add_bool(key=ini_key, section="Salvage", var_name="show_salvage_all", name="show_salvage_all", default=self.show_salvage_all)
        # Legacy compatibility for older config files.
        IniManager().add_bool(key=ini_key, section="Salvage", var_name="salvage_all", name="salvage_all", default=self.show_salvage_all)

        IniManager().add_bool(key=ini_key, section="Salvage", var_name="salvage_all_whites", name="salvage_all_whites", default=self.salvage_all_whites)
        IniManager().add_bool(key=ini_key, section="Salvage", var_name="salvage_all_blues", name="salvage_all_blues", default=self.salvage_all_blues)
        IniManager().add_bool(key=ini_key, section="Salvage", var_name="salvage_all_greens", name="salvage_all_greens", default=self.salvage_all_greens)
        IniManager().add_bool(key=ini_key, section="Salvage", var_name="salvage_all_purples", name="salvage_all_purples", default=self.salvage_all_purples)
        IniManager().add_bool(key=ini_key, section="Salvage", var_name="salvage_all_golds", name="salvage_all_golds", default=self.salvage_all_golds)
        
 
@dataclass
class DepositSettings:
    use_ctrl_click: bool = field(default_factory=bool)
    
    def add_config_vars(self, ini_key: str):
        IniManager().add_bool(key=ini_key, section="Deposit", var_name="use_ctrl_click", name="use_ctrl_click", default=self.use_ctrl_click)

        
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
    
    def add_config_vars(self, ini_key: str):
        IniManager().add_bool(key=ini_key, section="Colorize", var_name="enable_colorize", name="enable_colorize", default=self.enable_colorize)
        IniManager().add_bool(key=ini_key, section="Colorize", var_name="color_whites", name="color_whites", default=self.color_whites)
        IniManager().add_bool(key=ini_key, section="Colorize", var_name="color_blues", name="color_blues", default=self.color_blues)
        IniManager().add_bool(key=ini_key, section="Colorize", var_name="color_greens", name="color_greens", default=self.color_greens)
        IniManager().add_bool(key=ini_key, section="Colorize", var_name="color_purples", name="color_purples", default=self.color_purples)
        IniManager().add_bool(key=ini_key, section="Colorize", var_name="color_golds", name="color_golds", default=self.color_golds)
        
        str_color = f"{self.white_color.r},{self.white_color.g},{self.white_color.b},{self.white_color.a}"
        IniManager().add_str(key=ini_key, section="Colorize", var_name="white_color", name="white_color", default=str_color)
        str_color = f"{self.blue_color.r},{self.blue_color.g},{self.blue_color.b},{self.blue_color.a}"
        IniManager().add_str(key=ini_key, section="Colorize", var_name="blue_color", name="blue_color", default=str_color)
        str_color = f"{self.green_color.r},{self.green_color.g},{self.green_color.b},{self.green_color.a}"
        IniManager().add_str(key=ini_key, section="Colorize", var_name="green_color", name="green_color", default=str_color)
        str_color = f"{self.purple_color.r},{self.purple_color.g},{self.purple_color.b},{self.purple_color.a}"
        IniManager().add_str(key=ini_key, section="Colorize", var_name="purple_color", name="purple_color", default=str_color)
        str_color = f"{self.gold_color.r},{self.gold_color.g},{self.gold_color.b},{self.gold_color.a}"
        IniManager().add_str(key=ini_key, section="Colorize", var_name="gold_color", name="gold_color", default=str_color)
        
#region PopUpClasses
class ModelPopUp:
    def __init__(self, title: str, model_dictionary: dict[int, str], current_blacklist: list[int]):
        self.is_open = False
        self.initialized = False
        self.Title = title
        self.model_dictionary = model_dictionary
        self._source_blacklist = current_blacklist
        self.blacklist = list(current_blacklist)
        self.result_blacklist: list[int] | None = None

        self.model_id_search: str = ""
        self.model_id_search_mode: int = 0  # 0 = contains, 1 = starts with

        
    def Show(self):
        if not self.initialized:
            self.initialized = True
            self.result_blacklist = None
            self.blacklist = list(self._source_blacklist)
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
            self.result_blacklist = list(self.blacklist)
            PyImGui.close_current_popup()

        PyImGui.end_popup_modal()
        

        
#region id_helpers
def _id_items(rarity: str):
    from Py4GWCoreLib.Routines import Routines
    from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
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
    
def _id_all(cfg: IdentificationSettings):
    from Py4GWCoreLib.Routines import Routines
    from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
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
    from Py4GWCoreLib.Routines import Routines
    from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
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
    
def _salvage_all(cfg: SalvageSettings):
    from Py4GWCoreLib.Routines import Routines
    from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
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
    

    
class InventoryPlusWidget:
    def __init__(self):
        from Py4GWCoreLib.UIManager import FrameInfo
        from Py4GWCoreLib.enums_src.Model_enums import ModelID
        from Py4GWCoreLib.enums_src.Item_enums import ItemType
        self.module_name = "Inventory Plus"
        self.ini_key = ""
        
        self.initialized = False
        self.auto_inventory_handler = AutoInventoryHandler()
        
        self.identification_settings = IdentificationSettings()
        self.salvage_settings = SalvageSettings()
        self.colorize_settings = ColorizeSettings()
        self.deposit_settings = DepositSettings()
        
        self.InventorySlots: list[FrameInfo] = []
        self.hovered_item: ItemSlotData | None = None
        self.selected_item: ItemSlotData | None = None
        self.pop_up_open: bool = False
        self.show_config_window: bool = False
        
        self.PopUps: dict[str, ModelPopUp] = {}
        self.model_id_to_name = {member.value: name for name, member in ModelID.__members__.items()}
        self.item_type_to_name = {member.value: name for name, member in ItemType.__members__.items()}

        # Merchant handling UI/runtime state
        self.merchant_frame_exists: bool = False
        self.merchant_sell_checkboxes: dict[int, bool] = {}
        self.selected_combo_merchant: int = 0
        self.merchant_buy_quantity: int = 1
        self.merchant_sell_quantities: dict[int, int] = {}
        
        self._init_popups()

    def _init_popups(self):
        self.PopUps["Identification ModelID Lookup"] = ModelPopUp(
            "Identification ModelID Lookup",
            self.model_id_to_name,
            self.auto_inventory_handler.id_model_blacklist
        )

        
        self.PopUps["Salvage Item Type Lookup"] = ModelPopUp(
            "Salvage Item Type Lookup",
            self.item_type_to_name,
            self.auto_inventory_handler.item_type_blacklist
        )

        self.PopUps["Salvage ModelID Lookup"] = ModelPopUp(
            "Salvage ModelID Lookup",
            self.model_id_to_name,
            self.auto_inventory_handler.salvage_blacklist
        )

        self.PopUps["Deposit Trophy ModelID Lookup"] = ModelPopUp(
            "Deposit Trophy ModelID Lookup",
            self.model_id_to_name,
            self.auto_inventory_handler.deposit_trophies_blacklist
        )

        self.PopUps["Deposit Material ModelID Lookup"] = ModelPopUp(
            "Deposit Material ModelID Lookup",
            self.model_id_to_name,
            self.auto_inventory_handler.deposit_materials_blacklist
        )

        self.PopUps["Deposit Event Item ModelID Lookup"] = ModelPopUp(
            "Deposit Event Item ModelID Lookup",
            self.model_id_to_name,
            self.auto_inventory_handler.deposit_event_items_blacklist
        )


        self.PopUps["Deposit Dye ModelID Lookup"] = ModelPopUp(
            "Deposit Dye ModelID Lookup",
            self.model_id_to_name,
            self.auto_inventory_handler.deposit_dyes_blacklist
        )

        self.PopUps["Deposit ModelID Lookup"] = ModelPopUp(
            "Deposit ModelID Lookup",
            self.model_id_to_name,
            self.auto_inventory_handler.deposit_model_blacklist
        )
        
    def _sync_popups_with_handler(self):
        self.PopUps["Identification ModelID Lookup"]._source_blacklist = \
            self.auto_inventory_handler.id_model_blacklist

        self.PopUps["Salvage Item Type Lookup"]._source_blacklist = \
            self.auto_inventory_handler.item_type_blacklist

        self.PopUps["Salvage ModelID Lookup"]._source_blacklist = \
            self.auto_inventory_handler.salvage_blacklist

        self.PopUps["Deposit Trophy ModelID Lookup"]._source_blacklist = \
            self.auto_inventory_handler.deposit_trophies_blacklist

        self.PopUps["Deposit Material ModelID Lookup"]._source_blacklist = \
            self.auto_inventory_handler.deposit_materials_blacklist

        self.PopUps["Deposit Event Item ModelID Lookup"]._source_blacklist = \
            self.auto_inventory_handler.deposit_event_items_blacklist

        self.PopUps["Deposit Dye ModelID Lookup"]._source_blacklist = \
            self.auto_inventory_handler.deposit_dyes_blacklist

        self.PopUps["Deposit ModelID Lookup"]._source_blacklist = \
            self.auto_inventory_handler.deposit_model_blacklist


    def _ensure_ini_key(self) -> bool:
        if not self.ini_key:
            self.ini_key = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not self.ini_key:
                return False
        self.initialized = True   
        return True
    
    def _add_config_vars(self):
        self.identification_settings.add_config_vars(self.ini_key)
        self.salvage_settings.add_config_vars(self.ini_key)
        self.colorize_settings.add_config_vars(self.ini_key)
        self.deposit_settings.add_config_vars(self.ini_key)
        
    def _add_auto_handler_config_vars(self):
        _section = "AutoManager"
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="module_active", name="module_active", default=False)
        IniManager().add_int(key=self.ini_key, section=_section, var_name="lookup_time", name="lookup_time", default=15000)
           
        _section = "AutoIdentify"
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="id_whites", name="id_whites", default=False)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="id_blues", name="id_blues", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="id_purples", name="id_purples", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="id_golds", name="id_golds", default=False)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="id_greens", name="id_greens", default=False)
        IniManager().add_str(key=self.ini_key, section=_section, var_name="id_model_blacklist", name="id_model_blacklist", default="")
        
        _section = "AutoSalvage"
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="salvage_whites", name="salvage_whites", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="salvage_rare_materials", name="salvage_rare_materials", default=False)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="salvage_blues", name="salvage_blues", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="salvage_purples", name="salvage_purples", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="salvage_golds", name="salvage_golds", default=False)
        IniManager().add_str(key=self.ini_key, section=_section, var_name="item_type_blacklist", name="item_type_blacklist", default="")
        IniManager().add_str(key=self.ini_key, section=_section, var_name="salvage_blacklist", name="salvage_blacklist", default="")
        
        _section = "AutoDeposit"
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="deposit_trophies", name="deposit_trophies", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="deposit_materials", name="deposit_materials", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="deposit_event_items", name="deposit_event_items", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="deposit_dyes", name="deposit_dyes", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="deposit_blues", name="deposit_blues", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="deposit_purples", name="deposit_purples", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="deposit_golds", name="deposit_golds", default=True)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="deposit_greens", name="deposit_greens", default=True)
        IniManager().add_int(key=self.ini_key, section=_section, var_name="keep_gold", name="keep_gold", default=5000)
        IniManager().add_str(key=self.ini_key, section=_section, var_name="deposit_trophies_blacklist", name="deposit_trophies_blacklist", default="")
        IniManager().add_str(key=self.ini_key, section=_section, var_name="deposit_materials_blacklist", name="deposit_materials_blacklist", default="")
        IniManager().add_str(key=self.ini_key, section=_section, var_name="deposit_event_items_blacklist", name="deposit_event_items_blacklist", default="")
        IniManager().add_str(key=self.ini_key, section=_section, var_name="deposit_dyes_blacklist", name="deposit_dyes_blacklist", default="")
        IniManager().add_str(key=self.ini_key, section=_section, var_name="deposit_model_blacklist", name="deposit_model_blacklist", default="")
     
    def load_settings(self):
        def _parse_color(value: str, default_color: Color) -> Color:
            try:
                parts = [
                    int(c.strip())
                    for c in value.strip("()").split(",")
                ]

                if len(parts) != 4:
                    raise ValueError

                return Color(*parts)

            except:
                return default_color

        def _get_bool_with_legacy(section: str, primary_var_name: str, legacy_var_name: str, default: bool) -> bool:
            legacy_value = IniManager().getBool(key=self.ini_key, section=section, var_name=legacy_var_name, default=default)
            return IniManager().getBool(key=self.ini_key, section=section, var_name=primary_var_name, default=legacy_value)
        
        cfg = self.identification_settings
        cfg.identify_whites = IniManager().getBool(key=self.ini_key, section="Identification", var_name="identify_whites", default=cfg.identify_whites)
        cfg.identify_blues = IniManager().getBool(key=self.ini_key, section="Identification", var_name="identify_blues", default=cfg.identify_blues)
        cfg.identify_greens = IniManager().getBool(key=self.ini_key, section="Identification", var_name="identify_greens", default=cfg.identify_greens)
        cfg.identify_purples = IniManager().getBool(key=self.ini_key, section="Identification", var_name="identify_purples", default=cfg.identify_purples)
        cfg.identify_golds = IniManager().getBool(key=self.ini_key, section="Identification", var_name="identify_golds", default=cfg.identify_golds)
        cfg.show_identify_all = IniManager().getBool(key=self.ini_key, section="Identification", var_name="show_identify_all", default=cfg.show_identify_all)
        cfg.identify_all_whites = IniManager().getBool(key=self.ini_key, section="Identification", var_name="identify_all_whites", default=cfg.identify_all_whites)
        cfg.identify_all_blues = IniManager().getBool(key=self.ini_key, section="Identification", var_name="identify_all_blues", default=cfg.identify_all_blues)
        cfg.identify_all_greens = IniManager().getBool(key=self.ini_key, section="Identification", var_name="identify_all_greens", default=cfg.identify_all_greens)
        cfg.identify_all_purples = IniManager().getBool(key=self.ini_key, section="Identification", var_name="identify_all_purples", default=cfg.identify_all_purples)
        cfg.identify_all_golds = IniManager().getBool(key=self.ini_key, section="Identification", var_name="identify_all_golds", default=cfg.identify_all_golds)
        
        cfg = self.salvage_settings
        cfg.salvage_whites = IniManager().getBool(key=self.ini_key, section="Salvage", var_name="salvage_whites", default=cfg.salvage_whites)
        cfg.salvage_blues = IniManager().getBool(key=self.ini_key, section="Salvage", var_name="salvage_blues", default=cfg.salvage_blues)
        cfg.salvage_greens = IniManager().getBool(key=self.ini_key, section="Salvage", var_name="salvage_greens", default=cfg.salvage_greens)
        cfg.salvage_purples = IniManager().getBool(key=self.ini_key, section="Salvage", var_name="salvage_purples", default=cfg.salvage_purples)
        cfg.salvage_golds = IniManager().getBool(key=self.ini_key, section="Salvage", var_name="salvage_golds", default=cfg.salvage_golds)
        cfg.show_salvage_all = _get_bool_with_legacy("Salvage", "show_salvage_all", "salvage_all", cfg.show_salvage_all)
        cfg.salvage_all_whites = IniManager().getBool(key=self.ini_key, section="Salvage", var_name="salvage_all_whites", default=cfg.salvage_all_whites)
        cfg.salvage_all_blues = IniManager().getBool(key=self.ini_key, section="Salvage", var_name="salvage_all_blues", default=cfg.salvage_all_blues)
        cfg.salvage_all_greens = IniManager().getBool(key=self.ini_key, section="Salvage", var_name="salvage_all_greens", default=cfg.salvage_all_greens)
        cfg.salvage_all_purples = IniManager().getBool(key=self.ini_key, section="Salvage", var_name="salvage_all_purples", default=cfg.salvage_all_purples)
        cfg.salvage_all_golds = IniManager().getBool(key=self.ini_key, section="Salvage", var_name="salvage_all_golds", default=cfg.salvage_all_golds)
        
        cfg = self.colorize_settings
        cfg.enable_colorize = IniManager().getBool(key=self.ini_key, section="Colorize", var_name="enable_colorize", default=cfg.enable_colorize)
        cfg.color_whites = IniManager().getBool(key=self.ini_key, section="Colorize", var_name="color_whites", default=cfg.color_whites)
        cfg.color_blues = IniManager().getBool(key=self.ini_key, section="Colorize", var_name="color_blues", default=cfg.color_blues)
        cfg.color_greens = IniManager().getBool(key=self.ini_key, section="Colorize", var_name="color_greens", default=cfg.color_greens)
        cfg.color_purples = IniManager().getBool(key=self.ini_key, section="Colorize", var_name="color_purples", default=cfg.color_purples)
        cfg.color_golds = IniManager().getBool(key=self.ini_key, section="Colorize", var_name="color_golds", default=cfg.color_golds)
        
        white_str = IniManager().getStr(
            key=self.ini_key, section="Colorize", var_name="white_color",
            default=str(cfg.white_color.to_tuple())
        )
        cfg.white_color = _parse_color(white_str, cfg.white_color)

        blue_str = IniManager().getStr(
            key=self.ini_key, section="Colorize", var_name="blue_color",
            default=str(cfg.blue_color.to_tuple())
        )
        cfg.blue_color = _parse_color(blue_str, cfg.blue_color)

        green_str = IniManager().getStr(
            key=self.ini_key, section="Colorize", var_name="green_color",
            default=str(cfg.green_color.to_tuple())
        )
        cfg.green_color = _parse_color(green_str, cfg.green_color)

        purple_str = IniManager().getStr(
            key=self.ini_key, section="Colorize", var_name="purple_color",
            default=str(cfg.purple_color.to_tuple())
        )
        cfg.purple_color = _parse_color(purple_str, cfg.purple_color)

        gold_str = IniManager().getStr(
            key=self.ini_key, section="Colorize", var_name="gold_color",
            default=str(cfg.gold_color.to_tuple())
        )
        cfg.gold_color = _parse_color(gold_str, cfg.gold_color)
        
        cfg = self.deposit_settings
        cfg.use_ctrl_click = IniManager().getBool(key=self.ini_key, section="Deposit", var_name="use_ctrl_click", default=cfg.use_ctrl_click)
    
    def load_auto_handler_settings(self):
        self.auto_inventory_handler.module_active = IniManager().getBool(key=self.ini_key, section="AutoManager", var_name="module_active", default=False)
        self.auto_inventory_handler._LOOKUP_TIME = IniManager().getInt(key=self.ini_key, section="AutoManager", var_name="lookup_time", default=15000)
        
        self.auto_inventory_handler.id_whites = IniManager().getBool(key=self.ini_key, section="AutoIdentify", var_name="id_whites", default=False)
        self.auto_inventory_handler.id_blues = IniManager().getBool(key=self.ini_key, section="AutoIdentify", var_name="id_blues", default=True)
        self.auto_inventory_handler.id_greens = IniManager().getBool(key=self.ini_key, section="AutoIdentify", var_name="id_greens", default=False)
        self.auto_inventory_handler.id_purples = IniManager().getBool(key=self.ini_key, section="AutoIdentify", var_name="id_purples", default=True)
        self.auto_inventory_handler.id_golds = IniManager().getBool(key=self.ini_key, section="AutoIdentify", var_name="id_golds", default=False)
        
        self.auto_inventory_handler.salvage_whites = IniManager().getBool(key=self.ini_key, section="AutoSalvage", var_name="salvage_whites", default=True)
        self.auto_inventory_handler.salvage_blues = IniManager().getBool(key=self.ini_key, section="AutoSalvage", var_name="salvage_blues", default=True)
        self.auto_inventory_handler.salvage_purples = IniManager().getBool(key=self.ini_key, section="AutoSalvage", var_name="salvage_purples", default=True)
        self.auto_inventory_handler.salvage_golds = IniManager().getBool(key=self.ini_key, section="AutoSalvage", var_name="salvage_golds", default=False)
        
        self.auto_inventory_handler.deposit_trophies = IniManager().getBool(key=self.ini_key, section="AutoDeposit", var_name="deposit_trophies", default=True)
        self.auto_inventory_handler.deposit_materials = IniManager().getBool(key=self.ini_key, section="AutoDeposit", var_name="deposit_materials", default=True)
        self.auto_inventory_handler.deposit_event_items = IniManager().getBool(key=self.ini_key, section="AutoDeposit", var_name="deposit_event_items", default=True)
        self.auto_inventory_handler.deposit_dyes = IniManager().getBool(key=self.ini_key, section="AutoDeposit", var_name="deposit_dyes", default=True)
        self.auto_inventory_handler.deposit_blues = IniManager().getBool(key=self.ini_key, section="AutoDeposit", var_name="deposit_blues", default=True)
        self.auto_inventory_handler.deposit_purples = IniManager().getBool(key=self.ini_key, section="AutoDeposit", var_name="deposit_purples", default=True)
        self.auto_inventory_handler.deposit_golds = IniManager().getBool(key=self.ini_key, section="AutoDeposit", var_name="deposit_golds", default=True)
        self.auto_inventory_handler.deposit_greens = IniManager().getBool(key=self.ini_key, section="AutoDeposit", var_name="deposit_greens", default=True)
        self.auto_inventory_handler.keep_gold = IniManager().getInt(key=self.ini_key, section="AutoDeposit", var_name="keep_gold", default=5000)
       
       
    def load_blacklists_from_ini(self):
        id_model_blacklist = IniManager().getStr(key=self.ini_key, section="AutoIdentify", var_name="id_model_blacklist", default="")
        self.auto_inventory_handler.id_model_blacklist = [int(x) for x in id_model_blacklist.split(",") if x.strip().isdigit()]
        item_type_blacklist = IniManager().getStr(key=self.ini_key, section="AutoSalvage", var_name="item_type_blacklist", default="")
        self.auto_inventory_handler.item_type_blacklist = [int(x) for x in item_type_blacklist.split(",") if x.strip().isdigit()]
        salvage_blacklist = IniManager().getStr(key=self.ini_key, section="AutoSalvage", var_name="salvage_blacklist", default="")
        self.auto_inventory_handler.salvage_blacklist = [int(x) for x in salvage_blacklist.split(",") if x.strip().isdigit()]
        deposit_trophies_blacklist = IniManager().getStr(key=self.ini_key, section="AutoDeposit", var_name="deposit_trophies_blacklist", default="")
        self.auto_inventory_handler.deposit_trophies_blacklist = [int(x) for x in deposit_trophies_blacklist.split(",") if x.strip().isdigit()]
        deposit_materials_blacklist = IniManager().getStr(key=self.ini_key, section="AutoDeposit", var_name="deposit_materials_blacklist", default="")
        self.auto_inventory_handler.deposit_materials_blacklist = [int(x) for x in deposit_materials_blacklist.split(",") if x.strip().isdigit()]
        deposit_event_items_blacklist = IniManager().getStr(key=self.ini_key, section="AutoDeposit", var_name="deposit_event_items_blacklist", default="")
        self.auto_inventory_handler.deposit_event_items_blacklist = [int(x) for x in deposit_event_items_blacklist.split(",") if x.strip().isdigit()]
        deposit_dyes_blacklist = IniManager().getStr(key=self.ini_key, section="AutoDeposit", var_name="deposit_dyes_blacklist", default="")
        self.auto_inventory_handler.deposit_dyes_blacklist = [int(x) for x in deposit_dyes_blacklist.split(",") if x.strip().isdigit()]
        deposit_model_blacklist = IniManager().getStr(key=self.ini_key, section="AutoDeposit", var_name="deposit_model_blacklist", default="")
        self.auto_inventory_handler.deposit_model_blacklist = [int(x) for x in deposit_model_blacklist.split(",") if x.strip().isdigit()]
        
        self._sync_popups_with_handler()
        
    #region auto_handler
    def update_auto_handler(self):
        from Py4GWCoreLib.Routines import Routines
        from Py4GWCoreLib.Map import Map
        from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
        
        if not Routines.Checks.Map.MapValid():
            self.auto_inventory_handler.lookup_throttle.Reset()
            self.auto_inventory_handler.outpost_handled = False
            return False

        
        if not self.auto_inventory_handler.runtime_initialized:
            self.auto_inventory_handler.lookup_throttle.SetThrottleTime(self.auto_inventory_handler._LOOKUP_TIME)
            self.auto_inventory_handler.lookup_throttle.Reset()
            self.auto_inventory_handler.runtime_initialized = True
            ConsoleLog("AutoInventoryHandler", "Auto Handler Options initialized", Py4GW.Console.MessageType.Success)
            
        if not Map.IsExplorable():
            self.auto_inventory_handler.lookup_throttle.Stop()
            self.auto_inventory_handler.status = "Idle"
            if not self.auto_inventory_handler.outpost_handled and self.auto_inventory_handler.module_active:
                GLOBAL_CACHE.Coroutines.append(self.auto_inventory_handler.IDSalvageDepositItems())
                self.auto_inventory_handler.outpost_handled = True
        else:      
            if self.auto_inventory_handler.lookup_throttle.IsStopped():
                self.auto_inventory_handler.lookup_throttle.Start()
                self.auto_inventory_handler.status = "Idle"
                
        if self.auto_inventory_handler.lookup_throttle.IsExpired():
            self.auto_inventory_handler.lookup_throttle.SetThrottleTime(self.auto_inventory_handler._LOOKUP_TIME)
            self.auto_inventory_handler.lookup_throttle.Stop()
            if self.auto_inventory_handler.status == "Idle" and self.auto_inventory_handler.module_active:
                GLOBAL_CACHE.Coroutines.append(self.auto_inventory_handler.IDAndSalvageItems())
            self.auto_inventory_handler.lookup_throttle.Start()    
            
    #region generic_item_menu_items      
    def _draw_generic_item_menu_item(self, selected_item: ItemSlotData | None = None):
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
        from Py4GWCoreLib.Routines import Routines
        
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
        label = "Disable Colorize" if self.colorize_settings.enable_colorize else "Enable Colorize"
        if PyImGui.menu_item(label):
            self.colorize_settings.enable_colorize = not self.colorize_settings.enable_colorize   
            PyImGui.close_current_popup()
        PyImGui.separator()
        label = "Disable Auto Inventory" if self.auto_inventory_handler.module_active else "Enable Auto Inventory"
        if PyImGui.menu_item(label):
            self.auto_inventory_handler.module_active = not self.auto_inventory_handler.module_active
            PyImGui.close_current_popup()
        if PyImGui.menu_item("Config Window"):
            self.show_config_window = True
            PyImGui.close_current_popup()
        
    #region id_kit_menu_items
    def _draw_id_kit_menu_item(self, selected_item: ItemSlotData):
        cfg = self.identification_settings
        id_shown = False
        if cfg.identify_whites:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_White").to_tuple_normalized())
            if PyImGui.menu_item("ID White Items"):
                _id_whites()
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            id_shown = True
        
        if cfg.identify_blues:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Blue").to_tuple_normalized())
            if PyImGui.menu_item("ID Blue Items"):
                _id_blues()
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            id_shown = True
        
        if cfg.identify_purples:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Purple").to_tuple_normalized())
            if PyImGui.menu_item("ID Purple Items"):
                _id_purples()
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            id_shown = True
        
        if cfg.identify_golds:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Gold").to_tuple_normalized())
            if PyImGui.menu_item("ID Gold Items"):
                _id_golds()
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            id_shown = True
            
        if cfg.identify_greens:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Green").to_tuple_normalized())
            if PyImGui.menu_item("ID Green Items"):
                _id_greens()
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            id_shown = True
            
        if cfg.show_identify_all:
            if PyImGui.menu_item("ID All Items"):
                _id_all(self.identification_settings)
                PyImGui.close_current_popup()
            id_shown = True
         
        if id_shown:   
            PyImGui.separator()  
        self._draw_generic_item_menu_item(selected_item)
        
    #region salvage_kit_menu_items     
    def _draw_salvage_kit_menu_item(self,selected_item: ItemSlotData):
        cfg = self.salvage_settings
        salv_shown = False
        if cfg.salvage_whites:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_White").to_tuple_normalized())
            if PyImGui.menu_item("Salvage White Items"):
                _salvage_whites()
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            salv_shown = True
            
        if cfg.salvage_blues:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Blue").to_tuple_normalized())
            if PyImGui.menu_item("Salvage Blue Items"):
                _salvage_blues()
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            salv_shown = True
        
        if cfg.salvage_purples:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Purple").to_tuple_normalized())
            if PyImGui.menu_item("Salvage Purple Items"):
                _salvage_purples()
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            salv_shown = True
        
        if cfg.salvage_golds:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Gold").to_tuple_normalized())
            if PyImGui.menu_item("Salvage Gold Items"):
                _salvage_golds()
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            salv_shown = True
            
        if cfg.show_salvage_all:
            if PyImGui.menu_item("Salvage All Items"):
                _salvage_all(self.salvage_settings)
                PyImGui.close_current_popup()
            salv_shown = True
            
        if salv_shown:
            PyImGui.separator()  
        self._draw_generic_item_menu_item(selected_item)
        
        
    def DetectInventoryAction(self):
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
        from Py4GWCoreLib.UIManager import UIManager, WindowID, FrameInfo, WindowFrames
        from Py4GWCoreLib.ItemArray import ItemArray
        from Py4GWCoreLib.Item import Item
        from Py4GWCoreLib.enums_src.Item_enums import Bags
        from Py4GWCoreLib.enums_src.IO_enums import MouseButton
        from Py4GWCoreLib.enums_src.Model_enums import ModelID
        
        if not UIManager.IsWindowVisible(WindowID.WindowID_InventoryBags):
            self.selected_item = None
            return
        
        # refresh slot frames
        self.InventorySlots.clear()
        self.hovered_item = None
        
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
                self.InventorySlots.append(frame)
                
        #Colorize
        if self.colorize_settings.enable_colorize:
            for slot_frame in self.InventorySlots:
                item_data: ItemSlotData = slot_frame.BlackBoard["ItemData"]
                
                if (item_data.Rarity == "White" and not self.colorize_settings.color_whites) or \
                (item_data.Rarity == "Blue" and not self.colorize_settings.color_blues) or \
                    (item_data.Rarity == "Green" and not self.colorize_settings.color_greens) or \
                    (item_data.Rarity == "Purple" and not self.colorize_settings.color_purples) or \
                    (item_data.Rarity == "Gold" and not self.colorize_settings.color_golds):
                    continue
                
                if item_data.Rarity == "White":
                    border_color = self.colorize_settings.white_color
                elif item_data.Rarity == "Blue":
                    border_color = self.colorize_settings.blue_color
                elif item_data.Rarity == "Green":
                    border_color = self.colorize_settings.green_color
                elif item_data.Rarity == "Purple":
                    border_color = self.colorize_settings.purple_color
                elif item_data.Rarity == "Gold":
                    border_color = self.colorize_settings.gold_color
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
                self.selected_item = None  # first assume empty click
                for slot_frame in self.InventorySlots:
                    if slot_frame.IsMouseOver():
                        self.selected_item = slot_frame.BlackBoard["ItemData"]
                        break

                PyImGui.open_popup("SlotContextMenu")
                
        # Detect Ctrl + Left Click
        if PyImGui.is_mouse_released(MouseButton.Left.value) and io.key_ctrl:
            if WindowFrames["Inventory Bags"].IsMouseOver():
                for slot_frame in self.InventorySlots:
                    if slot_frame.IsMouseOver():
                        self.selected_item = slot_frame.BlackBoard["ItemData"]
                        if self.selected_item and self.deposit_settings.use_ctrl_click:
                            GLOBAL_CACHE.Inventory.DepositItemToStorage(self.selected_item.ItemID)
                        return


        # Render popup
        if PyImGui.begin_popup("SlotContextMenu"):

            if self.selected_item:
                if self.selected_item.IsIDKit:
                    self._draw_id_kit_menu_item(self.selected_item)        
                elif self.selected_item.IsSalvageKit and self.selected_item.ModelID == ModelID.Salvage_Kit:
                    self._draw_salvage_kit_menu_item(self.selected_item)
                else:
                    self._draw_generic_item_menu_item(self.selected_item)
            else:
                self._draw_generic_item_menu_item()

            PyImGui.end_popup()

        else:
            # popup is not open → clear selection
            self.selected_item = None
    
    #region ShowConfigWindow
    def DrawPopUps(self):
        for popup in self.PopUps.values():
            if popup.is_open:
                popup.Show()
                if popup.result_blacklist is not None:
                    # Update the corresponding blacklist in auto_handler
                    if popup.Title == "Identification ModelID Lookup":
                        new_blacklist = popup.result_blacklist
                        if new_blacklist != self.auto_inventory_handler.id_model_blacklist:
                            self.auto_inventory_handler.id_model_blacklist = new_blacklist
                            id_model_blacklist_str = ",".join(str(mid) for mid in new_blacklist)
                            IniManager().set(key=self.ini_key, section="AutoIdentify", var_name="id_model_blacklist", value=id_model_blacklist_str)
                    elif popup.Title == "Salvage Item Type Lookup":
                        new_blacklist = popup.result_blacklist
                        if new_blacklist != self.auto_inventory_handler.item_type_blacklist:
                            self.auto_inventory_handler.item_type_blacklist = new_blacklist
                            item_type_blacklist_str = ",".join(str(mid) for mid in new_blacklist)
                            IniManager().set(key=self.ini_key, section="AutoSalvage", var_name="item_type_blacklist", value=item_type_blacklist_str)
                    elif popup.Title == "Salvage ModelID Lookup":
                        new_blacklist = popup.result_blacklist
                        if new_blacklist != self.auto_inventory_handler.salvage_blacklist:
                            self.auto_inventory_handler.salvage_blacklist = popup.result_blacklist
                            salvage_blacklist_str = ",".join(str(mid) for mid in new_blacklist)
                            IniManager().set(key=self.ini_key, section="AutoSalvage", var_name="salvage_blacklist", value=salvage_blacklist_str)
                    elif popup.Title == "Deposit Trophy ModelID Lookup":
                        new_blacklist = popup.result_blacklist
                        if new_blacklist != self.auto_inventory_handler.deposit_trophies_blacklist:
                            self.auto_inventory_handler.deposit_trophies_blacklist = new_blacklist
                            deposit_trophies_blacklist_str = ",".join(str(mid) for mid in new_blacklist)
                            IniManager().set(key=self.ini_key, section="AutoDeposit", var_name="deposit_trophies_blacklist", value=deposit_trophies_blacklist_str)
                    elif popup.Title == "Deposit Material ModelID Lookup":
                        new_blacklist = popup.result_blacklist
                        if new_blacklist != self.auto_inventory_handler.deposit_materials_blacklist:
                            self.auto_inventory_handler.deposit_materials_blacklist = new_blacklist
                            deposit_materials_blacklist_str = ",".join(str(mid) for mid in new_blacklist)
                            IniManager().set(key=self.ini_key, section="AutoDeposit", var_name="deposit_materials_blacklist", value=deposit_materials_blacklist_str)
                    elif popup.Title == "Deposit Event Item ModelID Lookup":
                        new_blacklist = popup.result_blacklist
                        if new_blacklist != self.auto_inventory_handler.deposit_event_items_blacklist:
                            self.auto_inventory_handler.deposit_event_items_blacklist = new_blacklist
                            deposit_event_items_blacklist_str = ",".join(str(mid) for mid in new_blacklist)
                            IniManager().set(key=self.ini_key, section="AutoDeposit", var_name="deposit_event_items_blacklist", value=deposit_event_items_blacklist_str)
                    elif popup.Title == "Deposit Dye ModelID Lookup":
                        new_blacklist = popup.result_blacklist
                        if new_blacklist != self.auto_inventory_handler.deposit_dyes_blacklist:
                            self.auto_inventory_handler.deposit_dyes_blacklist = new_blacklist
                            deposit_dyes_blacklist_str = ",".join(str(mid) for mid in new_blacklist)
                            IniManager().set(key=self.ini_key, section="AutoDeposit", var_name="deposit_dyes_blacklist", value=deposit_dyes_blacklist_str)
                    elif popup.Title == "Deposit ModelID Lookup":
                        new_blacklist = popup.result_blacklist
                        if new_blacklist != self.auto_inventory_handler.deposit_model_blacklist:
                            self.auto_inventory_handler.deposit_model_blacklist = new_blacklist
                            deposit_model_blacklist_str = ",".join(str(mid) for mid in new_blacklist)
                            IniManager().set(key=self.ini_key, section="AutoDeposit", var_name="deposit_model_blacklist", value=deposit_model_blacklist_str)
                
 
 
    #region MerchantWindow
    def _ensure_legacy_merchant_module(self):
        if hasattr(self, '_legacy_merchant_module') and self._legacy_merchant_module is not None:
            return
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
        from Sources.ApoSource.InvPlus.GUI_Helpers import Frame
        import Sources.ApoSource.InvPlus.Coroutines as LegacyMerchantCoroutines
        import Sources.ApoSource.InvPlus.MerchantModule as LegacyMerchantModule
        from Sources.ApoSource.InvPlus.MerchantModule import MerchantModule

        # Keep the old implementation path, but bind Trading to GLOBAL_CACHE.Trading.
        # This matches the py4gw demo usage path and ensures offered lists/quotes populate.
        LegacyMerchantModule.Trading = GLOBAL_CACHE.Trading
        LegacyMerchantCoroutines.Trading = GLOBAL_CACHE.Trading

        self._legacy_inventory_frame = Frame(0)
        self._legacy_merchant_module = MerchantModule(self._legacy_inventory_frame)

    def _get_merchant_batch_size(self) -> int:
        try:
            if bool(self._legacy_merchant_module._is_material_trader()):
                return 10
        except Exception:
            pass
        try:
            if bool(self._legacy_merchant_module._is_rare_material_trader()):
                return 1
        except Exception:
            pass
        return 1

    def _resolve_merchant_item_name(self, item_id):
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

        resolved_item_id = item_id
        if hasattr(resolved_item_id, "item_id"):
            resolved_item_id = resolved_item_id.item_id

        try:
            resolved_item_id = int(resolved_item_id)
        except Exception:
            pass

        try:
            item_name = Utils.StripMarkup(GLOBAL_CACHE.Item.GetName(resolved_item_id))
            if isinstance(item_name, str) and item_name.strip():
                return item_name
        except Exception:
            pass

        try:
            model_id = int(GLOBAL_CACHE.Item.GetModelID(resolved_item_id))
        except Exception:
            model_id = 0

        model_name = self.model_id_to_name.get(model_id)
        if model_name:
            return model_name.replace("_", " ")
        return f"ModelID {model_id}" if model_id else "Unknown Item"

    def _set_merchant_checkbox_state(self, tick_state: bool):
        from Py4GWCoreLib import Item, ItemArray, Bags
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

        merchant_item_list = GLOBAL_CACHE.Trading.Trader.GetOfferedItems()
        merchant_item_models = {
            int(GLOBAL_CACHE.Item.GetModelID(item_id))
            for item_id in merchant_item_list
        }
        required_quantity = self._get_merchant_batch_size()

        for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)

            for item_id in item_array:
                model = int(Item.GetModelID(item_id))
                quantity = int(Item.Properties.GetQuantity(item_id))
                item_value = int(Item.Properties.GetValue(item_id))

                if bool(self._legacy_merchant_module._is_merchant()) and item_value >= 1:
                    is_on_list = True
                else:
                    is_on_list = model in merchant_item_models

                if not is_on_list or quantity < required_quantity:
                    continue

                self._legacy_merchant_module.merchant_checkboxes[item_id] = tick_state

        for item_id in list(self._legacy_merchant_module.merchant_checkboxes):
            if not self._legacy_merchant_module.merchant_checkboxes[item_id]:
                del self._legacy_merchant_module.merchant_checkboxes[item_id]
                normalized_item_id = self._normalize_item_id(item_id)
                if normalized_item_id in self.merchant_sell_quantities:
                    del self.merchant_sell_quantities[normalized_item_id]

    def _normalize_item_id(self, item_id):
        resolved_item_id = item_id
        if hasattr(resolved_item_id, "item_id"):
            resolved_item_id = resolved_item_id.item_id
        try:
            return int(resolved_item_id)
        except Exception:
            return resolved_item_id

    def _get_max_sell_quantity(self, item_id: int, batch_size: int) -> int:
        from Py4GWCoreLib import Item

        try:
            current_qty = int(Item.Properties.GetQuantity(item_id))
        except Exception:
            return 0
        if batch_size <= 1:
            return max(0, current_qty)
        return max(0, (current_qty // batch_size) * batch_size)

    def _sell_selected_material_items(self, sell_plan: dict[int, int]):
        from Py4GWCoreLib import Trading
        from Py4GWCoreLib import Item
        from Py4GWCoreLib.Routines import Routines
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

        batch_size = self._get_merchant_batch_size()
        for item_id, target_quantity in sell_plan.items():
            remaining = max(0, int(target_quantity))
            while remaining >= batch_size:
                try:
                    current_qty = int(Item.Properties.GetQuantity(item_id))
                except Exception:
                    break
                if current_qty < batch_size:
                    break

                GLOBAL_CACHE.Trading.Trader.RequestSellQuote(item_id)
                quoted_value = -1
                waited_ms = 0
                while quoted_value < 0 and waited_ms < 3000:
                    yield from Routines.Yield.wait(50)
                    waited_ms += 50
                    quoted_value = Trading.Trader.GetQuotedValue()

                if quoted_value <= 0:
                    break

                GLOBAL_CACHE.Trading.Trader.SellItem(item_id, quoted_value)
                waited_ms = 0
                while waited_ms < 3000:
                    yield from Routines.Yield.wait(50)
                    waited_ms += 50
                    if Trading.IsTransactionComplete():
                        break

                remaining -= batch_size

    def _draw_merchant_trade_window(self, merchant_frame_rect: tuple[float, float, float, float] | None = None):
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
        from Sources.ApoSource.InvPlus.Coroutines import BuyMerchantItems
        from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
        from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5

        merchant_item_list = list(GLOBAL_CACHE.Trading.Trader.GetOfferedItems())
        combo_items = [self._resolve_merchant_item_name(item_id) for item_id in merchant_item_list]
        selected_count = len(self._legacy_merchant_module.merchant_checkboxes)
        batch_size = self._get_merchant_batch_size()
        batch_label = "10" if batch_size == 10 else "1"

        if self.selected_combo_merchant >= len(combo_items):
            self.selected_combo_merchant = 0
        if self.selected_combo_merchant < 0:
            self.selected_combo_merchant = 0

        if self.merchant_buy_quantity < batch_size:
            self.merchant_buy_quantity = batch_size

        selected_item_ids = [
            self._normalize_item_id(item_id)
            for item_id, checked in self._legacy_merchant_module.merchant_checkboxes.items()
            if checked
        ]
        selected_item_ids = [item_id for item_id in selected_item_ids if isinstance(item_id, int) and item_id > 0]
        selected_item_ids = list(dict.fromkeys(selected_item_ids))
        for item_id in selected_item_ids:
            if item_id not in self.merchant_sell_quantities:
                self.merchant_sell_quantities[item_id] = self._get_max_sell_quantity(item_id, batch_size)

        is_rare_material_trader = False
        try:
            is_rare_material_trader = bool(self._legacy_merchant_module._is_rare_material_trader())
        except Exception:
            is_rare_material_trader = False
        window_title = "Rare Material bulk trade" if is_rare_material_trader else "Material bulk trader"

        window_flags = PyImGui.WindowFlags.NoFlag
        if merchant_frame_rect is not None:
            left, top, right, bottom = merchant_frame_rect
            top = top + 25
            width = max(420, int(right - left))
            height = max(260, int(bottom - top))
            PyImGui.set_next_window_pos(float(left), float(top))
            PyImGui.set_next_window_size(float(width), float(height))
        else:
            window_flags |= PyImGui.WindowFlags.AlwaysAutoResize

        if PyImGui.begin(window_title, True, window_flags):
            if PyImGui.begin_tab_bar("MaterialTraderTabs"):
                if PyImGui.begin_tab_item("Sell"):
                    if PyImGui.button(f"{IconsFontAwesome5.ICON_SQUARE_CHECK}##Select All"):
                        self._set_merchant_checkbox_state(True)
                    ImGui.show_tooltip("Mark all sell-eligible stacks in bags 1-4.")
                    
                    PyImGui.same_line(0, -1)
                    if PyImGui.button(f"{IconsFontAwesome5.ICON_SQUARE}##Clear All"):
                        self._set_merchant_checkbox_state(False)
                    ImGui.show_tooltip("Clear all currently selected stacks.")
                    
                    if not selected_item_ids:
                        PyImGui.text("No material available for sale.")  
                    else:
                        PyImGui.separator()
                        PyImGui.text("Selected Material Stacks")
                        if PyImGui.begin_table("SelectedMaterialStacksTable", 4):
                            PyImGui.table_setup_column("Item", PyImGui.TableColumnFlags.WidthStretch, 220)
                            PyImGui.table_setup_column("Max Available", PyImGui.TableColumnFlags.WidthFixed, 90)
                            PyImGui.table_setup_column("Sell Qty", PyImGui.TableColumnFlags.WidthFixed, 130)
                            PyImGui.table_setup_column("Planned", PyImGui.TableColumnFlags.WidthFixed, 70)
                            PyImGui.table_headers_row()

                            for item_id in selected_item_ids:
                                max_qty = self._get_max_sell_quantity(item_id, batch_size)
                                if max_qty < batch_size:
                                    continue

                                current_qty = int(self.merchant_sell_quantities.get(item_id, max_qty))
                                if current_qty > max_qty:
                                    current_qty = max_qty
                                if batch_size > 1:
                                    current_qty = (current_qty // batch_size) * batch_size
                                    if current_qty < batch_size:
                                        current_qty = batch_size

                                PyImGui.table_next_row()
                                PyImGui.table_next_column()
                                try:
                                    item_model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
                                except Exception:
                                    item_model_id = 0
                                texture_file = get_texture_for_model(item_model_id)
                                ImGui.DrawTexture(texture_file, 30, 30)
                                PyImGui.same_line(0, -1)
                                PyImGui.text(self._resolve_merchant_item_name(item_id))
                                PyImGui.table_next_column()
                                PyImGui.text(str(max_qty))
                                PyImGui.table_next_column()
                                old_qty = current_qty
                                PyImGui.push_item_width(120)
                                updated_qty = PyImGui.input_int(f"##SellQty_{item_id}", current_qty, batch_size, batch_size, PyImGui.InputTextFlags.NoFlag)
                                PyImGui.pop_item_width()
                                if updated_qty < batch_size:
                                    updated_qty = batch_size
                                if updated_qty > max_qty:
                                    updated_qty = max_qty
                                if batch_size > 1:
                                    updated_qty = (updated_qty // batch_size) * batch_size
                                    if updated_qty < batch_size:
                                        updated_qty = batch_size
                                if updated_qty != old_qty:
                                    ConsoleLog(
                                        self.module_name,
                                        f"[SellQty] apply item={item_id} old={old_qty} new={updated_qty} max={max_qty} batch={batch_size}",
                                        Py4GW.Console.MessageType.Info
                                    )
                                if updated_qty != old_qty:
                                    self.merchant_sell_quantities[item_id] = updated_qty
                                else:
                                    self.merchant_sell_quantities[item_id] = int(self.merchant_sell_quantities.get(item_id, updated_qty))
                                PyImGui.table_next_column()
                                PyImGui.text(str(self.merchant_sell_quantities.get(item_id, updated_qty)))

                            PyImGui.end_table()
                        
                        PyImGui.text(f"Selected stacks: {selected_count}")    

                        if PyImGui.button(f"{IconsFontAwesome5.ICON_FILE_INVOICE_DOLLAR} Sell Selected Stacks", 220, 42):
                            sell_plan: dict[int, int] = {}
                            for item_id in selected_item_ids:
                                max_qty = self._get_max_sell_quantity(item_id, batch_size)
                                requested_qty = int(self.merchant_sell_quantities.get(item_id, max_qty))
                                if batch_size > 1:
                                    requested_qty = (requested_qty // batch_size) * batch_size
                                requested_qty = max(0, min(requested_qty, max_qty))
                                if requested_qty >= batch_size:
                                    sell_plan[item_id] = requested_qty
                            if sell_plan:
                                GLOBAL_CACHE.Coroutines.append(self._sell_selected_material_items(sell_plan))
                        ImGui.show_tooltip("Sell all checked stacks.")

                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Buy"):
                    PyImGui.text("Material Trader: Bulk Buy")
                    if batch_size == 10:
                        PyImGui.text_wrapped("Pick an offered material, then enter quantity in multiples of 10.")
                    else:
                        PyImGui.text_wrapped("Pick an offered material, then enter quantity in units of 1.")

                    if combo_items:
                        PyImGui.push_item_width(420)
                        self.selected_combo_merchant = PyImGui.combo("Offered Item", self.selected_combo_merchant, combo_items)
                        PyImGui.pop_item_width()
                    else:
                        PyImGui.text_colored("No offered items detected.", ColorPalette.GetColor("dark_red").to_tuple_normalized())

                    self.merchant_buy_quantity = PyImGui.input_int("Buy Quantity", self.merchant_buy_quantity, batch_size, batch_size, PyImGui.InputTextFlags.NoFlag)
                    if self.merchant_buy_quantity < batch_size:
                        self.merchant_buy_quantity = batch_size
                    if batch_size == 10:
                        self.merchant_buy_quantity = (self.merchant_buy_quantity // 10) * 10
                        if self.merchant_buy_quantity < 10:
                            self.merchant_buy_quantity = 10

                    if PyImGui.button("Buy Selected Item", 180, 42):
                        if combo_items:
                            GLOBAL_CACHE.Coroutines.append(
                                BuyMerchantItems(
                                    merchant_item_list.copy(),
                                    self.selected_combo_merchant,
                                    self.merchant_buy_quantity
                                )
                            )
                    ImGui.show_tooltip("Buy the selected offered item using the configured quantity.")
                    PyImGui.end_tab_item()

                PyImGui.end_tab_bar()
        PyImGui.end()

    def DrawMerchantWindow(self):
        from Py4GWCoreLib.UIManager import UIManager
        from Sources.ApoSource.InvPlus.GUI_Helpers import MERCHANT_FRAME

        self._ensure_legacy_merchant_module()

        inventory_frame_id = UIManager.GetFrameIDByHash(291586130)
        if inventory_frame_id == 0 or not UIManager.FrameExists(inventory_frame_id):
            self.merchant_frame_exists = False
            return

        merchant_frame_id = UIManager.GetFrameIDByHash(MERCHANT_FRAME)
        if merchant_frame_id == 0 or not UIManager.FrameExists(merchant_frame_id):
            self.merchant_frame_exists = False
            return

        self._legacy_inventory_frame.set_frame_id(inventory_frame_id)
        is_material_trader = False
        try:
            is_material_trader = bool(self._legacy_merchant_module._is_material_trader())
        except Exception:
            is_material_trader = False
        try:
            is_material_trader = is_material_trader or bool(self._legacy_merchant_module._is_rare_material_trader())
        except Exception:
            pass
        if not is_material_trader:
            self.merchant_frame_exists = False
            return

        merchant_left, merchant_top, merchant_right, merchant_bottom = UIManager.GetFrameCoords(merchant_frame_id)
        merchant_frame_rect: tuple[float, float, float, float] | None = None
        if merchant_right > merchant_left and merchant_bottom > merchant_top:
            merchant_frame_rect = (merchant_left, merchant_top, merchant_right, merchant_bottom)

        self._legacy_merchant_module.colorize_merchants()
        if self._legacy_merchant_module.merchant_frame_exists:
            if not self.merchant_frame_exists:
                self._set_merchant_checkbox_state(True)
            self.merchant_frame_exists = True
            self._draw_merchant_trade_window(merchant_frame_rect)
        else:
            self.merchant_frame_exists = False
    def ShowConfigWindow(self):
        GW_WHITE = ColorPalette.GetColor("GW_White")
        GW_BLUE = ColorPalette.GetColor("GW_Blue")
        GW_PURPLE = ColorPalette.GetColor("GW_Purple")
        GW_GOLD = ColorPalette.GetColor("GW_Gold")
        GW_GREEN = ColorPalette.GetColor("GW_Green")
        
        def ini_colored_checkbox(label: str,section: str, var_name: str,cfg_obj,color: Color,default: bool) -> bool:
            # --- load from ini ---
            cfg_attr = var_name
            val = IniManager().getBool(key=self.ini_key,section=section,var_name=var_name,default=default)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text,color.to_tuple_normalized())
            new_val = PyImGui.checkbox(label, val)
            PyImGui.pop_style_color(1)
            
            if new_val != val:
                setattr(cfg_obj, cfg_attr, new_val)
                IniManager().set(key=self.ini_key,section=section,var_name=var_name,value=new_val)
                
            return new_val

        
        expanded = ImGui.Begin(ini_key=self.ini_key, name="Inventory Plus Configuration", p_open=self.show_config_window, flags=PyImGui.WindowFlags.AlwaysAutoResize)
        if expanded:
            auto_state_color = GW_GREEN if self.auto_inventory_handler.module_active else ColorPalette.GetColor("dark_red")
            auto_state_label = "Enabled" if self.auto_inventory_handler.module_active else "Disabled"
            total_ignored = (
                len(self.auto_inventory_handler.id_model_blacklist) +
                len(self.auto_inventory_handler.item_type_blacklist) +
                len(self.auto_inventory_handler.salvage_blacklist) +
                len(self.auto_inventory_handler.deposit_trophies_blacklist) +
                len(self.auto_inventory_handler.deposit_materials_blacklist) +
                len(self.auto_inventory_handler.deposit_event_items_blacklist) +
                len(self.auto_inventory_handler.deposit_dyes_blacklist) +
                len(self.auto_inventory_handler.deposit_model_blacklist)
            )
            if PyImGui.begin_child("InventoryPlusOverview", (0, 88), True, PyImGui.WindowFlags.NoFlag):
                PyImGui.text("Overview")
                if PyImGui.begin_table("InventoryPlusOverviewTable", 3):
                    PyImGui.table_next_column()
                    PyImGui.text("Auto Handler")
                    PyImGui.text_colored(auto_state_label, auto_state_color.to_tuple_normalized())
                    PyImGui.table_next_column()
                    PyImGui.text("Check Interval")
                    PyImGui.text(f"{self.auto_inventory_handler._LOOKUP_TIME} ms")
                    PyImGui.table_next_column()
                    PyImGui.text("Ignored Entries")
                    PyImGui.text(str(total_ignored))
                    PyImGui.end_table()
            PyImGui.end_child()
            PyImGui.separator()
            if PyImGui.begin_tab_bar("InventoryPlusConfigTabs"):
                cfg = self.identification_settings
                if PyImGui.begin_tab_item("Identification"):
                    if PyImGui.collapsing_header("Identification Menu Options:"):

                        cfg.identify_whites = ini_colored_checkbox(label="Show ID Whites in Menu",section="Identification",var_name="identify_whites",cfg_obj=cfg,color=GW_WHITE,default=cfg.identify_whites)   
                        cfg.identify_blues = ini_colored_checkbox(label="Show ID Blues in Menu",section="Identification",var_name="identify_blues",cfg_obj=cfg,color=GW_BLUE,default=cfg.identify_blues)
                        cfg.identify_purples = ini_colored_checkbox(label="Show ID Purples in Menu",section="Identification",var_name="identify_purples",cfg_obj=cfg,color=GW_PURPLE,default=cfg.identify_purples)
                        cfg.identify_golds = ini_colored_checkbox(label="Show ID Golds in Menu",section="Identification",var_name="identify_golds",cfg_obj=cfg,color=GW_GOLD,default=cfg.identify_golds)
                        cfg.identify_greens = ini_colored_checkbox(label="Show ID Greens in Menu",section="Identification",var_name="identify_greens",cfg_obj=cfg,color=GW_GREEN,default=cfg.identify_greens)
                        cfg.show_identify_all = ini_colored_checkbox(label="Show Identify All in Menu",section="Identification",var_name="show_identify_all",cfg_obj=cfg,color=GW_WHITE,default=cfg.show_identify_all)
                        if cfg.show_identify_all:
                            PyImGui.indent(20)
                            cfg.identify_all_whites = ini_colored_checkbox("Include Whites", "Identification", "identify_all_whites", cfg, GW_WHITE, default=cfg.identify_all_whites)
                            cfg.identify_all_blues = ini_colored_checkbox("Include Blues", "Identification", "identify_all_blues", cfg, GW_BLUE, default=cfg.identify_all_blues)
                            cfg.identify_all_greens = ini_colored_checkbox("Include Greens", "Identification", "identify_all_greens", cfg, GW_GREEN, default=cfg.identify_all_greens)
                            cfg.identify_all_purples = ini_colored_checkbox("Include Purples", "Identification", "identify_all_purples", cfg, GW_PURPLE, default=cfg.identify_all_purples)
                            cfg.identify_all_golds = ini_colored_checkbox("Include Golds", "Identification", "identify_all_golds", cfg, GW_GOLD, default=cfg.identify_all_golds)
                            PyImGui.unindent(20)
                    PyImGui.separator()
                    if PyImGui.collapsing_header("Ignore Models:"):
                        PyImGui.text("List Of Specific Item Model IDs to ignore from Identification")
                        if PyImGui.button("Manage Model Blacklist"):
                            self.PopUps["Identification ModelID Lookup"].is_open = True
                        if PyImGui.is_item_hovered():
                            PyImGui.begin_tooltip()
                            PyImGui.text(f"{len(self.auto_inventory_handler.id_model_blacklist)} Models Ignored")
                            PyImGui.end_tooltip()
                        PyImGui.same_line(0,-1)
                        PyImGui.text(f"{len(self.auto_inventory_handler.id_model_blacklist)} Models Ignored")
                        
                    PyImGui.separator()
                    if PyImGui.collapsing_header("Automatic Handling Options:"):
                        color = ColorPalette.GetColor("dark_red")
                        PyImGui.text_colored("These settings periodically identify items in your inventory based on the options below.", color.to_tuple_normalized())
                        PyImGui.text_colored("Used by bots/scripts as the shared auto-identification policy.", color.to_tuple_normalized())
                        self.auto_inventory_handler.id_whites = ini_colored_checkbox("Automatically ID Whites", "AutoIdentify", "id_whites", self.auto_inventory_handler, GW_WHITE, default=self.auto_inventory_handler.id_whites)
                        self.auto_inventory_handler.id_blues = ini_colored_checkbox("Automatically ID Blues", "AutoIdentify", "id_blues", self.auto_inventory_handler, GW_BLUE, default=self.auto_inventory_handler.id_blues)
                        self.auto_inventory_handler.id_purples = ini_colored_checkbox("Automatically ID Purples", "AutoIdentify", "id_purples", self.auto_inventory_handler, GW_PURPLE, default=self.auto_inventory_handler.id_purples)
                        self.auto_inventory_handler.id_golds = ini_colored_checkbox("Automatically ID Golds", "AutoIdentify", "id_golds", self.auto_inventory_handler, GW_GOLD, default=self.auto_inventory_handler.id_golds)
                        self.auto_inventory_handler.id_greens = ini_colored_checkbox("Automatically ID Greens", "AutoIdentify", "id_greens", self.auto_inventory_handler, GW_GREEN, default=self.auto_inventory_handler.id_greens)

                        PyImGui.separator()
                                    
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Salvage"):
                    cfg = self.salvage_settings
                    if PyImGui.collapsing_header("Salvage Menu Options:"):
                        color = ColorPalette.GetColor("dark_red")
                        PyImGui.text_colored("These settings periodically salvage items for materials based on the options below.", color.to_tuple_normalized())
                        PyImGui.text_colored("This script does not handle mods yet.", color.to_tuple_normalized())
                        PyImGui.separator()
                        cfg.salvage_whites = ini_colored_checkbox(label="Show Salvage Whites in Menu",section="Salvage",var_name="salvage_whites",cfg_obj=cfg,color=GW_WHITE,default=cfg.salvage_whites)
                        cfg.salvage_blues = ini_colored_checkbox(label="Show Salvage Blues in Menu",section="Salvage",var_name="salvage_blues",cfg_obj=cfg,color=GW_BLUE,default=cfg.salvage_blues)
                        cfg.salvage_purples = ini_colored_checkbox(label="Show Salvage Purples in Menu",section="Salvage",var_name="salvage_purples",cfg_obj=cfg,color=GW_PURPLE,default=cfg.salvage_purples)
                        cfg.salvage_golds = ini_colored_checkbox(label="Show Salvage Golds in Menu",section="Salvage",var_name="salvage_golds",cfg_obj=cfg,color=GW_GOLD,default=cfg.salvage_golds)
                        cfg.show_salvage_all = ini_colored_checkbox(label="Show Salvage All in Menu",section="Salvage",var_name="show_salvage_all",cfg_obj=cfg,color=GW_WHITE,default=cfg.show_salvage_all)
                        if cfg.show_salvage_all:
                            PyImGui.indent(20)
                            cfg.salvage_all_whites = ini_colored_checkbox("Include Whites", "Salvage", "salvage_all_whites", cfg, GW_WHITE, default=cfg.salvage_all_whites)
                            cfg.salvage_all_blues = ini_colored_checkbox("Include Blues", "Salvage", "salvage_all_blues", cfg, GW_BLUE, default=cfg.salvage_all_blues)
                            cfg.salvage_all_purples = ini_colored_checkbox("Include Purples", "Salvage", "salvage_all_purples", cfg, GW_PURPLE, default=cfg.salvage_all_purples)
                            cfg.salvage_all_golds = ini_colored_checkbox("Include Golds", "Salvage", "salvage_all_golds", cfg, GW_GOLD, default=cfg.salvage_all_golds)
                            PyImGui.text_colored("Green items cannot be salvaged.", GW_GREEN.to_tuple_normalized())
                            PyImGui.unindent(20)
                    PyImGui.separator() 
                    if PyImGui.collapsing_header("Ignore Lists:"):
                        if PyImGui.button("Ignore Type"):
                            self.PopUps["Salvage Item Type Lookup"].is_open = True
                        if PyImGui.is_item_hovered():
                            PyImGui.begin_tooltip()
                            PyImGui.text(f"{len(self.auto_inventory_handler.item_type_blacklist)} Types Ignored. (e.g., Weapons, Armor, etc.)")
                            PyImGui.end_tooltip()
                        PyImGui.same_line(0,-1)
                        PyImGui.text(f"{len(self.auto_inventory_handler.item_type_blacklist)} Types Ignored")
                        if PyImGui.button("Ignore Model"):
                            self.PopUps["Salvage ModelID Lookup"].is_open = True   
                        if PyImGui.is_item_hovered():
                            PyImGui.begin_tooltip()
                            PyImGui.text(f"{len(self.auto_inventory_handler.salvage_blacklist)} Models Ignored")
                            PyImGui.end_tooltip()
                        PyImGui.same_line(0,-1)
                        PyImGui.text(f"{len(self.auto_inventory_handler.salvage_blacklist)} Models Ignored")
                        

                    if PyImGui.collapsing_header("Automatic Handling Options:"):
                        color = ColorPalette.GetColor("dark_red")
                        PyImGui.text_colored("These settings periodically salvage items in your inventory based on the options below.", color.to_tuple_normalized())
                        PyImGui.text_colored("Used by bots/scripts as the shared auto-salvage policy.", color.to_tuple_normalized())
                        self.auto_inventory_handler.salvage_whites = ini_colored_checkbox("Automatically Salvage Whites", "AutoSalvage", "salvage_whites", self.auto_inventory_handler, GW_WHITE, default=self.auto_inventory_handler.salvage_whites)
                        self.auto_inventory_handler.salvage_rare_materials = ini_colored_checkbox("Automatically Salvage Rare Materials", "AutoSalvage", "salvage_rare_materials", self.auto_inventory_handler, GW_WHITE, default=self.auto_inventory_handler.salvage_rare_materials)
                        self.auto_inventory_handler.salvage_blues = ini_colored_checkbox("Automatically Salvage Blues", "AutoSalvage", "salvage_blues", self.auto_inventory_handler, GW_BLUE, default=self.auto_inventory_handler.salvage_blues)
                        self.auto_inventory_handler.salvage_purples = ini_colored_checkbox("Automatically Salvage Purples", "AutoSalvage", "salvage_purples", self.auto_inventory_handler, GW_PURPLE, default=self.auto_inventory_handler.salvage_purples)
                        self.auto_inventory_handler.salvage_golds = ini_colored_checkbox("Automatically Salvage Golds", "AutoSalvage", "salvage_golds", self.auto_inventory_handler, GW_GOLD, default=self.auto_inventory_handler.salvage_golds)
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Deposit"):
                    from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
                    cfg = self.deposit_settings
                    cfg.use_ctrl_click = ini_colored_checkbox(label="Use Ctrl + Left Click To Deposit Items",section="Deposit",var_name="use_ctrl_click",cfg_obj=cfg,color=GW_WHITE,default=cfg.use_ctrl_click)
                    
                    val = IniManager().getInt(key=self.ini_key,section="AutoDeposit",var_name="keep_gold",default=5000)
                    new_val = PyImGui.input_int("Keep Minimum Gold In Inventory", val)
                    if new_val != val:
                        self.auto_inventory_handler.keep_gold = new_val
                        IniManager().set(key=self.ini_key,section="AutoDeposit",var_name="keep_gold",value=new_val)
                    
                    PyImGui.separator()
                    if PyImGui.collapsing_header("Automatic Handling Options:"):
                        PyImGui.text_wrapped("Automatic deposit of items is handled here.")
                        PyImGui.text_wrapped("This feature is used by Bots and other scripts to automatically manage your inventory.")
                        PyImGui.text_wrapped("Each time you enter Outposts Items matching the criteria will be deposited into your Xunlai Vault.")
                        PyImGui.separator()
                        
                        self.auto_inventory_handler.deposit_materials = ini_colored_checkbox(IconsFontAwesome5.ICON_HAMMER + " Deposit Materials", "AutoDeposit", "deposit_materials", self.auto_inventory_handler, GW_WHITE, default=self.auto_inventory_handler.deposit_materials)
                        self.auto_inventory_handler.deposit_trophies = ini_colored_checkbox(IconsFontAwesome5.ICON_TROPHY + " Deposit Trophies", "AutoDeposit", "deposit_trophies", self.auto_inventory_handler, GW_WHITE, default=self.auto_inventory_handler.deposit_trophies)
                        self.auto_inventory_handler.deposit_event_items = ini_colored_checkbox(IconsFontAwesome5.ICON_HAT_WIZARD + " Deposit Event Items", "AutoDeposit", "deposit_event_items", self.auto_inventory_handler, GW_WHITE, default=self.auto_inventory_handler.deposit_event_items)
                        self.auto_inventory_handler.deposit_dyes = ini_colored_checkbox(IconsFontAwesome5.ICON_FLASK + " Deposit Dyes", "AutoDeposit", "deposit_dyes", self.auto_inventory_handler, GW_WHITE, default=self.auto_inventory_handler.deposit_dyes)
                        self.auto_inventory_handler.deposit_blues = ini_colored_checkbox("Deposit Blues", "AutoDeposit", "deposit_blues", self.auto_inventory_handler, GW_BLUE, default=self.auto_inventory_handler.deposit_blues)
                        self.auto_inventory_handler.deposit_purples = ini_colored_checkbox("Deposit Purples", "AutoDeposit", "deposit_purples", self.auto_inventory_handler, GW_PURPLE, default=self.auto_inventory_handler.deposit_purples)
                        self.auto_inventory_handler.deposit_golds = ini_colored_checkbox("Deposit Golds", "AutoDeposit", "deposit_golds", self.auto_inventory_handler, GW_GOLD, default=self.auto_inventory_handler.deposit_golds)
                        self.auto_inventory_handler.deposit_greens = ini_colored_checkbox("Deposit Greens", "AutoDeposit", "deposit_greens", self.auto_inventory_handler, GW_GREEN, default=self.auto_inventory_handler.deposit_greens)

                    
                    if PyImGui.collapsing_header("Ignore Lists:"):
                        PyImGui.text("Manage the various blacklists for deposit handling here.")
                        if PyImGui.begin_table("DepositBlacklistTable", 2):
                            PyImGui.table_setup_column("Action", PyImGui.TableColumnFlags.WidthFixed, 280.0)
                            PyImGui.table_setup_column("Count", PyImGui.TableColumnFlags.WidthStretch)

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            if PyImGui.button("Material Blacklist"):
                                self.PopUps["Deposit Material ModelID Lookup"].is_open = True
                            PyImGui.table_next_column()
                            PyImGui.text(f"{len(self.auto_inventory_handler.deposit_materials_blacklist)} Models Ignored")

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            if PyImGui.button("Manage Trophy Blacklist"):
                                self.PopUps["Deposit Trophy ModelID Lookup"].is_open = True
                            PyImGui.table_next_column()
                            PyImGui.text(f"{len(self.auto_inventory_handler.deposit_trophies_blacklist)} Models Ignored")

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            if PyImGui.button("Manage Event Item Blacklist"):
                                self.PopUps["Deposit Event Item ModelID Lookup"].is_open = True
                            PyImGui.table_next_column()
                            PyImGui.text(f"{len(self.auto_inventory_handler.deposit_event_items_blacklist)} Models Ignored")

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            if PyImGui.button("Manage Dye Blacklist"):
                                self.PopUps["Deposit Dye ModelID Lookup"].is_open = True
                            PyImGui.table_next_column()
                            PyImGui.text(f"{len(self.auto_inventory_handler.deposit_dyes_blacklist)} Colors Ignored")

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            if PyImGui.button("Model Blacklist"):
                                self.PopUps["Deposit ModelID Lookup"].is_open = True
                            PyImGui.table_next_column()
                            PyImGui.text(f"{len(self.auto_inventory_handler.deposit_model_blacklist)} Models Ignored")

                            PyImGui.end_table()
                        
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Colorize"):
                    cfg = self.colorize_settings
                    cfg.enable_colorize = ini_colored_checkbox(label="Enable Item Colorize",section="Colorize",var_name="enable_colorize",cfg_obj=cfg,color=GW_WHITE,default=cfg.enable_colorize)
                    PyImGui.separator()
                    cfg.color_whites = ini_colored_checkbox(label="Color White Items",section="Colorize",var_name="color_whites",cfg_obj=cfg,color=GW_WHITE,default=cfg.color_whites)
                    cfg.color_blues = ini_colored_checkbox(label="Color Blue Items",section="Colorize",var_name="color_blues",cfg_obj=cfg,color=GW_BLUE,default=cfg.color_blues)
                    cfg.color_greens = ini_colored_checkbox(label="Color Green Items",section="Colorize",var_name="color_greens",cfg_obj=cfg,color=GW_GREEN,default=cfg.color_greens)
                    cfg.color_purples = ini_colored_checkbox(label="Color Purple Items",section="Colorize",var_name="color_purples",cfg_obj=cfg,color=GW_PURPLE,default=cfg.color_purples)
                    cfg.color_golds = ini_colored_checkbox(label="Color Gold Items",section="Colorize",var_name="color_golds",cfg_obj=cfg,color=GW_GOLD,default=cfg.color_golds)
                    PyImGui.separator()
                    
                    # -------------------------------------------------
                    # Helper: tuple string -> RGBA ints
                    # -------------------------------------------------
                    def _parse_color(value: str, default: tuple[int,int,int,int]):
                        try:
                            return tuple(
                                int(c.strip())
                                for c in value.strip("()").split(",")
                            )
                        except:
                            return default

                    white_color_str = IniManager().getStr(key=self.ini_key,section="Colorize",var_name="white_color",default="(255, 255, 255, 255)")
                    white_color = _parse_color(white_color_str, (255,255,255,255))
                    tmp_color = Color(*white_color)
                    color = PyImGui.color_edit4("White Item Color", tmp_color.to_tuple_normalized())
                    if color != cfg.white_color.to_tuple_normalized():
                        cfg.white_color = Color(int(255*color[0]), int(255*color[1]), int(255*color[2]), int(255*color[3]))
                        IniManager().set(key=self.ini_key,section="Colorize",var_name="white_color",value=cfg.white_color.to_tuple())
                    
                    blue_color_str = IniManager().getStr(key=self.ini_key,section="Colorize",var_name="blue_color",default="(0, 0, 255, 255)")
                    blue_color = _parse_color(blue_color_str, (0,0,255,255))
                    tmp_color = Color(*blue_color)
                    color = PyImGui.color_edit4("Blue Item Color", tmp_color.to_tuple_normalized())
                    if color != cfg.blue_color.to_tuple_normalized():
                        cfg.blue_color = Color(int(255*color[0]), int(255*color[1]), int(255*color[2]), int(255*color[3]))
                        IniManager().set(key=self.ini_key,section="Colorize",var_name="blue_color",value=cfg.blue_color.to_tuple())
                    
                    green_color_str = IniManager().getStr(key=self.ini_key,section="Colorize",var_name="green_color",default="(0, 255, 0, 255)")
                    green_color = _parse_color(green_color_str, (0,255,0,255))
                    tmp_color = Color(*green_color)
                    color = PyImGui.color_edit4("Green Item Color", tmp_color.to_tuple_normalized())
                    if color != cfg.green_color.to_tuple_normalized():
                        cfg.green_color = Color(int(255*color[0]), int(255*color[1]), int(255*color[2]), int(255*color[3]))
                        IniManager().set(key=self.ini_key,section="Colorize",var_name="green_color",value=cfg.green_color.to_tuple())
                       
                    purple_color_str = IniManager().getStr(key=self.ini_key,section="Colorize",var_name="purple_color",default="(128, 0, 128, 255)")
                    purple_color = _parse_color(purple_color_str, (128,0,128,255))
                    tmp_color = Color(*purple_color)
                    color = PyImGui.color_edit4("Purple Item Color", tmp_color.to_tuple_normalized())
                    if color != cfg.purple_color.to_tuple_normalized():
                        cfg.purple_color = Color(int(255*color[0]), int(255*color[1]), int(255*color[2]), int(255*color[3]))
                        IniManager().set(key=self.ini_key,section="Colorize",var_name="purple_color",value=cfg.purple_color.to_tuple())
                        
                    gold_color_str = IniManager().getStr(key=self.ini_key,section="Colorize",var_name="gold_color",default="(255, 215, 0, 255)")
                    gold_color = _parse_color(gold_color_str, (255,215,0,255))
                    tmp_color = Color(*gold_color)
                    color = PyImGui.color_edit4("Gold Item Color", tmp_color.to_tuple_normalized())
                    if color != cfg.gold_color.to_tuple_normalized():
                        cfg.gold_color = Color(int(255*color[0]), int(255*color[1]), int(255*color[2]), int(255*color[3]))
                        IniManager().set(key=self.ini_key,section="Colorize",var_name="gold_color",value=cfg.gold_color.to_tuple())
                        
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Auto Handler"):
                    from Py4GWCoreLib.Routines import Routines
                    PyImGui.text_wrapped("Automatic Identification, Salvaging and Deposit is handled here.")
                    PyImGui.text_wrapped("This feature is used by Bots and other scripts to automatically manage your inventory.")
                    PyImGui.text_wrapped("Enable the options in the Identification and Salvage tabs to activate automatic handling for those item rarities.")
                    old_val = IniManager().getBool(key=self.ini_key, section="AutoManager", var_name="module_active", default=self.auto_inventory_handler.module_active)
                    new_val = PyImGui.checkbox("Enable Auto Inventory Handler", old_val)
                    if new_val != old_val:
                        self.auto_inventory_handler.module_active = new_val
                        IniManager().set(key=self.ini_key, section="AutoManager", var_name="module_active", value=new_val) 
              
                    old_val = IniManager().getInt(key=self.ini_key, section="AutoManager", var_name="lookup_time", default=self.auto_inventory_handler._LOOKUP_TIME)
                    new_val = PyImGui.input_int("Inventory Check Interval (ms)", old_val)
                    if new_val != old_val:
                        self.auto_inventory_handler._LOOKUP_TIME = new_val
                        self.auto_inventory_handler.lookup_throttle.SetThrottleTime(new_val)
                        IniManager().set(key=self.ini_key,section="AutoManager",var_name="lookup_time",value=new_val)
                    
                    color = ColorPalette.GetColor("dark_red")
                    if Routines.Checks.Map.IsOutpost():
                        PyImGui.text_colored("Timer is paused in Outposts.", color.to_tuple_normalized())
                    PyImGui.text(f"next check in {max(0, self.auto_inventory_handler._LOOKUP_TIME - self.auto_inventory_handler.lookup_throttle.GetTimeElapsed()):.3f} ms")
                    PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
            PyImGui.separator()
            if PyImGui.button("Close"):
                self.show_config_window = False
            """PyImGui.same_line(0,-1)
            if PyImGui.button("Save & Close"):
                self.save_to_ini()
                self.load_from_ini()
                self.show_config_window = False"""
        ImGui.End(self.ini_key)



InventoryPlusWidgetInstance = InventoryPlusWidget()

def configure():
    if not InventoryPlusWidgetInstance.initialized: return
    if InventoryPlusWidgetInstance.show_config_window: return
    InventoryPlusWidgetInstance.show_config_window = True


def main():
    if not InventoryPlusWidgetInstance.initialized:
        if not InventoryPlusWidgetInstance._ensure_ini_key(): return

        InventoryPlusWidgetInstance._add_config_vars()
        InventoryPlusWidgetInstance._add_auto_handler_config_vars()
        IniManager().load_once(InventoryPlusWidgetInstance.ini_key)
        InventoryPlusWidgetInstance.load_settings()
        InventoryPlusWidgetInstance.load_auto_handler_settings()
        InventoryPlusWidgetInstance.load_blacklists_from_ini()
        InventoryPlusWidgetInstance.initialized = True
        
    InventoryPlusWidgetInstance.update_auto_handler()
    
    InventoryPlusWidgetInstance.DetectInventoryAction()
    InventoryPlusWidgetInstance.DrawMerchantWindow()
    if InventoryPlusWidgetInstance.show_config_window:
        InventoryPlusWidgetInstance.ShowConfigWindow()
        InventoryPlusWidgetInstance._sync_popups_with_handler()
        InventoryPlusWidgetInstance.DrawPopUps()


if __name__ == "__main__":
    main()


