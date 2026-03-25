import PyImGui
import Py4GW
import importlib.util
import os
import sys
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GWCoreLib.enums_src.Texture_enums import get_texture_for_model
from typing import Any, Generator, cast


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
class InventoryInteractionContext:
    # Build this once per frame so colorize and click targeting share the same slot resolution.
    f9_visible: bool = False
    i_visible: bool = False
    storage_visible: bool = False
    item_data_by_bag_slot: dict[tuple[int, int], ItemSlotData] = field(default_factory=dict)
    bag_sizes: dict[int, int] = field(default_factory=dict)
    i_inventory_frame_id: int = 0
    i_bags_bar_bottom: int = 0
    i_slot_frame_ids: dict[tuple[int, int], int] = field(default_factory=dict)
    storage_slot_frame_ids: dict[tuple[int, int], int] = field(default_factory=dict)
    
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
class InventoryWindowSettings:
    enable_i_window: bool = True

    def add_config_vars(self, ini_key: str):
        IniManager().add_bool(key=ini_key, section="InventoryWindow", var_name="enable_i_window", name="enable_i_window", default=self.enable_i_window)

        
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
            if PyImGui.begin_child("ModelIDList", (295, 375), True, PyImGui.WindowFlags.NoFlag):
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
def _get_inventory_item_ids() -> list[int]:
    from Py4GWCoreLib import ItemArray
    from Py4GWCoreLib.enums_src.Item_enums import Bags

    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
    return ItemArray.GetItemArray(bag_list)



def _get_item_id_at_bag_slot(bag_id: int, slot: int) -> int:
    from Py4GWCoreLib import Item, ItemArray

    item_array = ItemArray.GetItemArray(ItemArray.CreateBagList(bag_id))
    for item_id in item_array:
        if int(Item.GetSlot(item_id)) == slot:
            return item_id
    return 0



def _get_salvageable_items_for_rarities(
    rarities: list[str],
    allow_unidentified_nonwhite: bool = False,
) -> list[int]:
    from Py4GWCoreLib import Item, ItemArray
    from Py4GWCoreLib.enums_src.Item_enums import Bags

    salvageable_items: list[int] = []
    rarity_filter = set(rarities)

    for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
        item_array = ItemArray.GetItemArray(ItemArray.CreateBagList(bag_id))
        for item_id in item_array:
            item_instance = Item.item_instance(item_id)
            rarity = item_instance.rarity.name

            if rarity not in rarity_filter:
                continue
            if not item_instance.is_identified:
                if not (allow_unidentified_nonwhite and rarity != "White"):
                    continue
            if not item_instance.is_salvageable:
                continue

            salvageable_items.append(item_id)

    return salvageable_items



def _allows_unidentified_nonwhite_salvage(selected_kit: ItemSlotData | None) -> bool:
    from Py4GWCoreLib.enums_src.Model_enums import ModelID

    if selected_kit is None:
        return False

    return selected_kit.ModelID in {
        ModelID.Expert_Salvage_Kit,
        ModelID.Superior_Salvage_Kit,
    }



def _is_supported_salvage_kit_item(item_id: int, inventory_item_ids: set[int] | None = None) -> bool:
    from Py4GWCoreLib import Item
    from Py4GWCoreLib.enums_src.Model_enums import ModelID

    if item_id == 0:
        return False
    if inventory_item_ids is not None and item_id not in inventory_item_ids:
        return False

    return (
        Item.Usage.IsSalvageKit(item_id)
        and Item.Usage.GetUses(item_id) > 0
        and int(Item.GetModelID(item_id)) in {
            ModelID.Salvage_Kit,
            ModelID.Expert_Salvage_Kit,
            ModelID.Superior_Salvage_Kit,
        }
    )



def _get_supported_salvage_kit_id(selected_kit: ItemSlotData | None = None) -> int:
    from Py4GWCoreLib import Item
    from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

    inventory_item_ids = _get_inventory_item_ids()
    inventory_item_id_set = set(inventory_item_ids)

    if selected_kit is not None:
        selected_kit_item_id = _get_item_id_at_bag_slot(selected_kit.BagID, selected_kit.Slot)
        if (
            _is_supported_salvage_kit_item(selected_kit_item_id, inventory_item_id_set)
            and int(Item.GetModelID(selected_kit_item_id)) == selected_kit.ModelID
        ):
            return selected_kit_item_id

    lesser_kit_item_id = GLOBAL_CACHE.Inventory.GetFirstSalvageKit()
    if _is_supported_salvage_kit_item(lesser_kit_item_id, inventory_item_id_set):
        return lesser_kit_item_id

    supported_kits = [
        item_id
        for item_id in inventory_item_ids
        if _is_supported_salvage_kit_item(item_id, inventory_item_id_set)
    ]
    if not supported_kits:
        return 0

    return min(supported_kits, key=lambda item_id: Item.Usage.GetUses(item_id))



def _call_inventory_bool_method(inventory_instance: Any, method_name: str) -> bool:
    inventory_method = getattr(inventory_instance, method_name, None)
    if not callable(inventory_method):
        return False
    return bool(inventory_method())



def _finish_inventory_salvage(inventory_instance: Any) -> None:
    finish_salvage = getattr(inventory_instance, "FinishSalvage", None)
    if callable(finish_salvage):
        finish_salvage()



def _wait_for_salvage_session_idle(inventory_instance, timeout_ms: int = 1500, poll_ms: int = 50):
    from Py4GWCoreLib.Routines import Routines

    supports_state_tracking = (
        inventory_instance is not None
        and hasattr(inventory_instance, "IsSalvaging")
        and hasattr(inventory_instance, "IsSalvageTransactionDone")
    )
    if not supports_state_tracking:
        return True

    waited_ms = 0
    while waited_ms < max(0, timeout_ms):
        if not _call_inventory_bool_method(inventory_instance, "IsSalvaging") and not _call_inventory_bool_method(inventory_instance, "IsSalvageTransactionDone"):
            return True
        yield from Routines.Yield.wait(max(1, poll_ms))
        waited_ms += max(1, poll_ms)
    return False



def _get_post_salvage_status(item_id: int, item_instance, allowed_rarities: set[str] | None = None) -> str:
    current_inventory_item_ids = set(_get_inventory_item_ids())
    if item_id not in current_inventory_item_ids:
        return "salvaged"

    item_instance.GetContext()
    current_rarity = item_instance.rarity.name
    if allowed_rarities is not None and current_rarity not in allowed_rarities:
        return "processed"
    if not item_instance.is_salvageable:
        return "processed"

    return "retry"



def _normalize_salvage_dialog_strategy(strategy: int) -> int:
    if strategy == 1:
        return 1
    if strategy == 2:
        return 1
    return 0



def _get_salvage_dialog_auto_settings() -> tuple[bool, int, bool, bool]:
    widget_instance = globals().get("InventoryPlusWidgetInstance")
    auto_inventory_handler = getattr(widget_instance, "auto_inventory_handler", None)

    auto_handle = bool(getattr(auto_inventory_handler, "salvage_dialog_auto_handle", False))
    strategy = _normalize_salvage_dialog_strategy(int(getattr(auto_inventory_handler, "salvage_dialog_strategy", 0)))
    auto_confirm_materials_warning = bool(getattr(auto_inventory_handler, "salvage_dialog_auto_confirm_materials", False))
    debug_enabled = bool(getattr(auto_inventory_handler, "salvage_dialog_debug", False))

    return auto_handle, strategy, auto_confirm_materials_warning, debug_enabled



def _salvage_single_item_with_supported_kit(item_id: int, label: str, selected_kit: ItemSlotData | None = None, allowed_rarities: set[str] | None = None):
    import PyInventory
    import PyItem
    from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, ConsoleLog, Console
    from Py4GWCoreLib import Item
    from Py4GWCoreLib.enums_src.Model_enums import ModelID
    from Py4GWCoreLib.Inventory import Inventory
    from Py4GWCoreLib.Routines import Routines

    queue_wait_timeout_ms = 5000
    salvage_wait_timeout_ms = 10000
    salvage_poll_ms = 50
    salvage_dialog_auto_handle, salvage_dialog_strategy, salvage_dialog_auto_confirm_materials, salvage_dialog_debug = _get_salvage_dialog_auto_settings()

    if item_id not in set(_get_inventory_item_ids()):
        return "missing_item"

    salvage_kit_item_id = _get_supported_salvage_kit_id(selected_kit)
    if salvage_kit_item_id == 0:
        ConsoleLog("SalvageItems", "No salvage kits found.", Console.MessageType.Warning)
        return "no_kit"

    item_instance = PyItem.PyItem(item_id)
    item_instance.GetContext()
    starting_quantity = item_instance.quantity
    if starting_quantity == 0:
        return "missing_item"

    _, rarity = Item.Rarity.GetRarity(item_id)
    Inventory._salvage_choice_debug_log(
        salvage_dialog_debug,
        "SalvageItems",
        f"begin item item_id={item_id} label='{label}' rarity={rarity} qty={starting_quantity} kit={salvage_kit_item_id} auto_handle={salvage_dialog_auto_handle} auto_confirm_warning={salvage_dialog_auto_confirm_materials}.",
    )
    if allowed_rarities is not None and rarity not in allowed_rarities:
        return "filtered_out"
    if not item_instance.is_salvageable:
        return "filtered_out"

    require_materials_confirmation = rarity == "Purple" or rarity == "Gold"
    advanced_kit_tracking = int(Item.GetModelID(salvage_kit_item_id)) in {
        ModelID.Expert_Salvage_Kit,
        ModelID.Superior_Salvage_Kit,
    }
    manual_choice_required = require_materials_confirmation and advanced_kit_tracking

    inventory_instance = PyInventory.PyInventory() if advanced_kit_tracking else None
    supports_state_tracking = (
        inventory_instance is not None
        and hasattr(inventory_instance, "IsSalvaging")
        and hasattr(inventory_instance, "IsSalvageTransactionDone")
    )
    supports_finish_salvage = inventory_instance is not None and hasattr(inventory_instance, "FinishSalvage")

    if advanced_kit_tracking and inventory_instance is not None:
        try:
            inventory_instance.Salvage(salvage_kit_item_id, item_id)
            yield from Routines.Yield.wait(salvage_poll_ms)
        except Exception:
            ConsoleLog("SalvageItems", f"Advanced salvage start failed (item_id={item_id}).", Console.MessageType.Warning)
            return "failed"
    else:
        ActionQueueManager().AddAction("SALVAGE", Inventory.SalvageItem, item_id, salvage_kit_item_id)
        queue_drained = yield from Routines.Yield.Items._wait_for_empty_queue("SALVAGE", timeout_ms=queue_wait_timeout_ms)
        if not queue_drained:
            ConsoleLog("SalvageItems", f"Timed out waiting for salvage queue after starting salvage (item_id={item_id}).", Console.MessageType.Warning)
            return "failed"

    if require_materials_confirmation and not manual_choice_required:
        found_confirm_window = yield from Routines.Yield.Items._wait_for_salvage_materials_window(
            timeout_ms=1500,
            poll_ms=salvage_poll_ms,
            initial_wait_ms=150,
        )
        if not found_confirm_window:
            ConsoleLog("SalvageItems", f"Timed out waiting for salvage confirmation window (item_id={item_id}).", Console.MessageType.Warning)
            return "failed"

        ActionQueueManager().AddAction("SALVAGE", Inventory.AcceptSalvageMaterialsWindow)
        queue_drained = yield from Routines.Yield.Items._wait_for_empty_queue("SALVAGE", timeout_ms=queue_wait_timeout_ms)
        if not queue_drained:
            ConsoleLog("SalvageItems", f"Timed out waiting for salvage queue after confirmation (item_id={item_id}).", Console.MessageType.Warning)
            return "failed"

    result_wait_timeout_ms = 30000 if advanced_kit_tracking else salvage_wait_timeout_ms
    saw_salvage_state = False
    item_progressed = False
    waited_ms = 0
    handled_salvage_dialog = False
    handled_dialog_settle_ms = 0
    handled_dialog_post_check_ms = max(250, salvage_poll_ms * 6)

    while waited_ms < result_wait_timeout_ms:
        try:
            if salvage_dialog_auto_handle:
                dialog_status = yield from Inventory.HandleSalvageChoiceDialog(
                    auto_handle=True,
                    strategy=salvage_dialog_strategy,
                    auto_confirm_materials_warning=salvage_dialog_auto_confirm_materials,
                    queue_name="SALVAGE",
                    log_module="SalvageItems",
                    queue_wait_timeout_ms=queue_wait_timeout_ms,
                    poll_ms=salvage_poll_ms,
                    close_timeout_ms=1500,
                    debug_enabled=salvage_dialog_debug,
                    item_id=item_id,
                )
                if dialog_status == "handled":
                    handled_salvage_dialog = True
                    handled_dialog_settle_ms = 0
                    waited_ms = 0
                    continue
                if dialog_status not in {"not_visible", "disabled", "confirm_pending"}:
                    ConsoleLog(
                        "SalvageItems",
                        f"Stopping salvage because the salvage choice dialog could not be handled safely (item_id={item_id}, status={dialog_status}).",
                        Console.MessageType.Warning,
                    )
                    return "popup_failed"

            yield from Routines.Yield.wait(salvage_poll_ms)
            waited_ms += salvage_poll_ms
            if handled_salvage_dialog:
                handled_dialog_settle_ms += salvage_poll_ms

            is_salvaging = False
            transaction_done = False
            if advanced_kit_tracking and supports_state_tracking and inventory_instance is not None:
                is_salvaging = _call_inventory_bool_method(inventory_instance, "IsSalvaging")
                transaction_done = _call_inventory_bool_method(inventory_instance, "IsSalvageTransactionDone")
                if is_salvaging or transaction_done:
                    saw_salvage_state = True

            current_inventory_item_ids = set(_get_inventory_item_ids())
            if item_id not in current_inventory_item_ids:
                if not advanced_kit_tracking:
                    return "salvaged"
                item_progressed = True
            else:
                item_instance.GetContext()
                if item_instance.quantity < starting_quantity:
                    if not advanced_kit_tracking:
                        return "salvaged"
                    item_progressed = True

            if handled_salvage_dialog and not supports_state_tracking and handled_dialog_settle_ms >= handled_dialog_post_check_ms:
                post_status = "salvaged" if item_progressed else _get_post_salvage_status(item_id, item_instance, allowed_rarities)
                Inventory._salvage_choice_debug_log(
                    salvage_dialog_debug,
                    "SalvageItems",
                    f"re-evaluate item item_id={item_id} after handled dialog settle={handled_dialog_settle_ms}ms status={post_status}.",
                )
                return post_status

            if advanced_kit_tracking and inventory_instance is not None:
                if transaction_done or (item_progressed and not is_salvaging):
                    if (transaction_done or saw_salvage_state) and supports_finish_salvage:
                        _finish_inventory_salvage(inventory_instance)
                        yield from _wait_for_salvage_session_idle(
                            inventory_instance,
                            timeout_ms=max(1500, salvage_poll_ms * 10),
                            poll_ms=salvage_poll_ms,
                        )
                        yield from Routines.Yield.wait(salvage_poll_ms * 2)

                    if item_progressed:
                        return "salvaged"

                    return _get_post_salvage_status(item_id, item_instance, allowed_rarities)

                if saw_salvage_state and not is_salvaging:
                    return _get_post_salvage_status(item_id, item_instance, allowed_rarities)
        except Exception:
            ConsoleLog("SalvageItems", f"Salvage loop failed (item_id={item_id}).", Console.MessageType.Warning)
            return "failed"

    if manual_choice_required:
        Inventory._salvage_choice_debug_log(
            salvage_dialog_debug,
            "SalvageItems",
            f"manual timeout item_id={item_id} item_progressed={item_progressed} saw_salvage_state={saw_salvage_state} supports_state_tracking={supports_state_tracking} supports_finish_salvage={supports_finish_salvage}.",
        )
        ConsoleLog("SalvageItems", f"Timed out waiting for manual salvage completion (item_id={item_id}).", Console.MessageType.Warning)
        return "manual_timeout"

    ConsoleLog("SalvageItems", f"Timed out waiting for salvage result (item_id={item_id}).", Console.MessageType.Warning)
    return "failed"



def _run_salvage_routine(item_ids: list[int], label: str, rarities: list[str] | None = None, selected_kit: ItemSlotData | None = None):
    from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, Console
    from Py4GWCoreLib.Routines import Routines

    item_ids = list(dict.fromkeys(item_ids))
    allow_unidentified_nonwhite = _allows_unidentified_nonwhite_salvage(selected_kit)

    salvaged_count = 0
    failed_item_ids: set[int] = set()
    aborted = False

    if rarities is None:
        for item_id in item_ids:
            while True:
                status = yield from _salvage_single_item_with_supported_kit(item_id, label, selected_kit=selected_kit)
                if status in {"salvaged", "processed"}:
                    salvaged_count += 1
                    break
                if status == "retry":
                    yield from Routines.Yield.wait(150)
                    continue
                if status in {"missing_item", "filtered_out"}:
                    break
                if status in {"no_kit", "manual_timeout", "popup_failed"}:
                    aborted = True
                    break
                failed_item_ids.add(item_id)
                break
            if aborted:
                break
    else:
        allowed_rarities = set(rarities)
        while True:
            matching_items = [
                item_id
                for item_id in _get_salvageable_items_for_rarities(
                    rarities,
                    allow_unidentified_nonwhite=allow_unidentified_nonwhite,
                )
                if item_id not in failed_item_ids
            ]
            if not matching_items:
                break

            item_id = matching_items[0]
            while True:
                status = yield from _salvage_single_item_with_supported_kit(
                    item_id,
                    label,
                    selected_kit=selected_kit,
                    allowed_rarities=allowed_rarities,
                )
                if status in {"salvaged", "processed"}:
                    salvaged_count += 1
                    break
                if status == "retry":
                    yield from Routines.Yield.wait(150)
                    continue
                if status in {"missing_item", "filtered_out"}:
                    break
                if status in {"no_kit", "manual_timeout", "popup_failed"}:
                    aborted = True
                    break
                failed_item_ids.add(item_id)
                break
            if aborted:
                break

    if salvaged_count > 0:
        ConsoleLog("SalvageItems", f"Salvaged {salvaged_count} items.", Console.MessageType.Info)

    return salvaged_count



def _queue_salvage_routine(item_ids: list[int], label: str, rarities: list[str] | None = None, selected_kit: ItemSlotData | None = None):
    from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

    routine = cast(Generator[Any, None, None], _run_salvage_routine(item_ids, label, rarities=rarities, selected_kit=selected_kit))
    GLOBAL_CACHE.Coroutines.append(routine)


# ---------------------------------------------------------------------------
# NEW: Stack salvage — repeatedly salvage the same bag+slot until depleted
# ---------------------------------------------------------------------------

def _run_salvage_stack_routine(bag_id: int, slot: int, label: str, selected_kit: ItemSlotData | None = None):
    """Coroutine: salvage every item in a stacked slot (same bag+slot) until gone."""
    from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, Console
    from Py4GWCoreLib.Routines import Routines

    salvaged_count = 0
    aborted = False
    max_iterations = 250  # safety cap — no real stack exceeds this

    for _ in range(max_iterations):
        # Re-resolve the item at this slot each iteration (quantity decreases or item vanishes)
        item_id = _get_item_id_at_bag_slot(bag_id, slot)
        if item_id == 0:
            break  # stack fully consumed

        while True:
            status = yield from _salvage_single_item_with_supported_kit(item_id, label, selected_kit=selected_kit)
            if status in {"salvaged", "processed"}:
                salvaged_count += 1
                break
            if status == "retry":
                yield from Routines.Yield.wait(150)
                continue
            if status in {"missing_item", "filtered_out"}:
                # Item gone or became unsalvageable — stop
                aborted = True
                break
            if status in {"no_kit", "manual_timeout", "popup_failed"}:
                aborted = True
                break
            # Any other failure: stop to avoid infinite loop
            aborted = True
            break

        if aborted:
            break

    if salvaged_count > 0:
        ConsoleLog("SalvageItems", f"Salvaged stack: {salvaged_count} items from bag {bag_id} slot {slot}.", Console.MessageType.Info)

    return salvaged_count


def _queue_salvage_stack(item: ItemSlotData, selected_kit: ItemSlotData | None = None):
    """Queue a full-stack salvage coroutine for a single inventory slot."""
    from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

    routine = cast(
        Generator[Any, None, None],
        _run_salvage_stack_routine(item.BagID, item.Slot, f"Salvage Stack [{item.Rarity}]", selected_kit=selected_kit),
    )
    GLOBAL_CACHE.Coroutines.append(routine)


# ---------------------------------------------------------------------------

def _salvage_items(rarity: str, selected_kit: ItemSlotData | None = None):
    salvageable_items = _get_salvageable_items_for_rarities(
        [rarity],
        allow_unidentified_nonwhite=_allows_unidentified_nonwhite_salvage(selected_kit),
    )
    _queue_salvage_routine(
        salvageable_items,
        label=f"Salvage {rarity}",
        rarities=[rarity],
        selected_kit=selected_kit,
    )



def _salvage_whites(selected_kit: ItemSlotData | None = None):
    _salvage_items("White", selected_kit=selected_kit)



def _salvage_blues(selected_kit: ItemSlotData | None = None):
    _salvage_items("Blue", selected_kit=selected_kit)



def _salvage_purples(selected_kit: ItemSlotData | None = None):
    _salvage_items("Purple", selected_kit=selected_kit)



def _salvage_golds(selected_kit: ItemSlotData | None = None):
    _salvage_items("Gold", selected_kit=selected_kit)



def _salvage_all(cfg: SalvageSettings, selected_kit: ItemSlotData | None = None):
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

    all_items = _get_salvageable_items_for_rarities(
        rarities,
        allow_unidentified_nonwhite=_allows_unidentified_nonwhite_salvage(selected_kit),
    )
    _queue_salvage_routine(
        all_items,
        label="Salvage All",
        rarities=rarities,
        selected_kit=selected_kit,
    )


def _withdraw_all_matching_model_from_storage(model_id: int):
    from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
    from Py4GWCoreLib.Py4GWcorelib import Console, ConsoleLog
    from Py4GWCoreLib.Routines import Routines

    if model_id <= 0:
        return

    while GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id) > 0:
        storage_item_id = GLOBAL_CACHE.Inventory.GetfirstModelIDInStorage(model_id)
        if storage_item_id == 0:
            break

        if not GLOBAL_CACHE.Inventory.WithdrawItemFromStorage(storage_item_id):
            ConsoleLog(
                "Inventory Plus",
                f"Stopped bulk withdraw for model_id={model_id}; inventory may be full.",
                Console.MessageType.Warning,
            )
            break

        yield from Routines.Yield.wait(200)


class InventoryPlusWidget:
    XUNLAI_WINDOW_FRAME_HASH = 2315448754

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
        self.inventory_window_settings = InventoryWindowSettings()
        
        self.InventorySlots: list[FrameInfo] = []
        self.hovered_item: ItemSlotData | None = None
        self.selected_item: ItemSlotData | None = None
        self._i_window_was_forced_closed: bool = False
        # The I-window wraps bag slots in extra containers, so remember the working prefix after the first hit.
        self.i_inventory_slot_prefix_cache: list[tuple[int, ...]] = []
        self.pop_up_open: bool = False
        self.show_config_window: bool = False
        # Tracks WidgetManager-driven configure() sessions so Close can end config mode cleanly.
        self._configure_session_active: bool = False
        self._xunlai_manager_bridge = None
        self._xunlai_manager_bridge_error: str | None = None
        self._xunlai_manager_bridge_path: str | None = None
        self._xunlai_manager_bridge_mtime: float | None = None
        self._source_mtime: float | None = None
        self._xunlai_sort_anchor_side: str | None = None
        self._xunlai_storage_visible_last_frame: bool = False
        self._xunlai_sort_icon_path = os.path.join(
            Py4GW.Console.get_projects_path(),
            "Sources",
            "frenkeyLib",
            "LootEx",
            "textures",
            "xunlai_chest.png",
        )
        
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

    def _get_xunlai_manager_bridge(self):
        from Py4GWCoreLib.Py4GWcorelib import Console, ConsoleLog

        module_name = "_inventoryplus_xunlai_manager_bridge"

        candidate_paths = []
        current_file = globals().get("__file__", "")
        if current_file:
            candidate_paths.append(os.path.join(os.path.dirname(current_file), "Xunlaimanager.py"))
        candidate_paths.append(
            os.path.join(
                Py4GW.Console.get_projects_path(),
                "Widgets",
                "Guild Wars",
                "Items & Loot",
                "Xunlaimanager.py",
            )
        )

        module_path = ""
        for candidate_path in candidate_paths:
            if candidate_path and os.path.exists(candidate_path):
                module_path = candidate_path
                break

        if not module_path:
            self._xunlai_manager_bridge_error = "Xunlaimanager.py not found"
            ConsoleLog("Inventory Plus", self._xunlai_manager_bridge_error, Console.MessageType.Warning)
            return None

        try:
            module_mtime = os.path.getmtime(module_path)
        except OSError:
            module_mtime = None

        if (
            self._xunlai_manager_bridge is not None
            and self._xunlai_manager_bridge_path == module_path
            and self._xunlai_manager_bridge_mtime == module_mtime
        ):
            return self._xunlai_manager_bridge

        sys.modules.pop(module_name, None)

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            self._xunlai_manager_bridge_error = f"Failed to load import spec for {module_path}"
            ConsoleLog("Inventory Plus", self._xunlai_manager_bridge_error, Console.MessageType.Warning)
            return None

        try:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            self._xunlai_manager_bridge = module
            self._xunlai_manager_bridge_path = module_path
            self._xunlai_manager_bridge_mtime = module_mtime
            self._xunlai_manager_bridge_error = None
        except Exception as exc:
            sys.modules.pop(module_name, None)
            self._xunlai_manager_bridge = None
            self._xunlai_manager_bridge_path = None
            self._xunlai_manager_bridge_mtime = None
            self._xunlai_manager_bridge_error = f"Failed to load Xunlai Manager bridge: {exc}"
            ConsoleLog("Inventory Plus", self._xunlai_manager_bridge_error, Console.MessageType.Error)
        return self._xunlai_manager_bridge

    def _refresh_runtime_if_source_changed(self) -> None:
        current_file = globals().get("__file__", "")
        if not current_file or not os.path.exists(current_file):
            return

        try:
            current_mtime = os.path.getmtime(current_file)
        except OSError:
            return

        if self._source_mtime is None:
            self._source_mtime = current_mtime
            return

        if current_mtime == self._source_mtime:
            return

        self._source_mtime = current_mtime
        self._xunlai_manager_bridge = None
        self._xunlai_manager_bridge_error = None
        self._xunlai_manager_bridge_path = None
        self._xunlai_manager_bridge_mtime = None

    def _draw_xunlai_sort_button(self, context: InventoryInteractionContext) -> None:
        from Py4GWCoreLib.UIManager import UIManager

        if not context.storage_visible:
            self._xunlai_storage_visible_last_frame = False
            self._xunlai_sort_anchor_side = None
            return

        left, top, right, bottom = UIManager.GetFrameCoords(self.XUNLAI_WINDOW_FRAME_HASH)
        if right <= left or bottom <= top:
            return
        if (right - left) < 100 or (bottom - top) < 100:
            return

        bridge = self._get_xunlai_manager_bridge()
        if bridge is None:
            return

        ensure_loaded = getattr(bridge, "_ensure_account_settings_loaded", None)
        if callable(ensure_loaded):
            ensure_loaded()

        get_bags = getattr(bridge, "_get_available_storage_bags", None)
        start_sort = getattr(bridge, "_start_sort_task", None)
        process_sort = getattr(bridge, "_process_sort_task", None)
        if not callable(get_bags) or not callable(start_sort) or not callable(process_sort):
            return

        if getattr(bridge, "_sort_task_state", None) is not None:
            process_sort()

        anniversary_unlocked = bool(getattr(bridge, "ANNIVERSARY_SLOT_UNLOCKED", False))
        available_storage_bags = get_bags(anniversary_unlocked)
        sort_running = getattr(bridge, "_sort_task_state", None) is not None
        progress_text = str(getattr(bridge, "_sort_progress_text", "") or "")
        progress_ratio = float(getattr(bridge, "_sort_progress_ratio", 0.0) or 0.0)
        icon_label = "XunlaiChestSort"
        icon_button_size = 22
        progress_width = 84
        icon_window_width = 30
        progress_window_width = 96
        outer_gap = 18
        io = PyImGui.get_io()
        display_width = float(getattr(io, "display_size_x", 0.0) or 0.0)
        if not self._xunlai_storage_visible_last_frame or self._xunlai_sort_anchor_side is None:
            required_width = progress_window_width if sort_running else icon_window_width
            right_space = max(0.0, display_width - right) if display_width > 0 else right
            left_space = max(0.0, left)
            if right_space >= required_width + outer_gap:
                self._xunlai_sort_anchor_side = "right"
            elif left_space >= required_width + outer_gap:
                self._xunlai_sort_anchor_side = "left"
            else:
                self._xunlai_sort_anchor_side = "right" if right_space >= left_space else "left"
            self._xunlai_storage_visible_last_frame = True

        icon_x = right + outer_gap
        if self._xunlai_sort_anchor_side == "left":
            icon_x = left - icon_window_width - outer_gap

        icon_x = max(0.0, icon_x)
        icon_y = max(0.0, top)
        window_flags = (
            PyImGui.WindowFlags.AlwaysAutoResize |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoResize |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse
        )

        PyImGui.set_next_window_pos(icon_x, icon_y)
        PyImGui.set_next_window_size(icon_window_width, 0)
        if PyImGui.begin("##InventoryPlusXunlaiSortButton", True, window_flags):
            PyImGui.push_style_var2(PyImGui.ImGuiStyleVar.FramePadding, 1, 1)
            use_texture_button = os.path.exists(self._xunlai_sort_icon_path)
            if sort_running:
                PyImGui.begin_disabled(True)
                if use_texture_button:
                    PyImGui.invisible_button(f"##{icon_label}_disabled", icon_button_size, icon_button_size)
                    item_rect_min = PyImGui.get_item_rect_min()
                    ImGui.DrawTextureInDrawList(
                        item_rect_min,
                        (icon_button_size, icon_button_size),
                        self._xunlai_sort_icon_path,
                        tint=(220, 220, 220, 255),
                    )
                else:
                    PyImGui.button("S##SortChest", icon_button_size, icon_button_size)
                PyImGui.end_disabled()
                if PyImGui.is_item_hovered():
                    tooltip_text = progress_text if progress_text else "Sorting Chest"
                    PyImGui.set_tooltip(tooltip_text)
            else:
                clicked = False
                if use_texture_button:
                    clicked = PyImGui.invisible_button(f"##{icon_label}", icon_button_size, icon_button_size)
                    item_rect_min = PyImGui.get_item_rect_min()
                    tint = (255, 255, 255, 255) if PyImGui.is_item_hovered() else (235, 235, 235, 255)
                    ImGui.DrawTextureInDrawList(
                        item_rect_min,
                        (icon_button_size, icon_button_size),
                        self._xunlai_sort_icon_path,
                        tint=tint,
                    )
                else:
                    clicked = PyImGui.button("S##SortChest", icon_button_size, icon_button_size)
                if clicked and len(available_storage_bags) > 0:
                    start_sort(available_storage_bags)
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("Sort Chest")
            PyImGui.pop_style_var(1)
        PyImGui.end()

        if not sort_running:
            return

        progress_x = right + outer_gap
        if self._xunlai_sort_anchor_side == "left":
            progress_x = left - progress_window_width - outer_gap

        progress_x = max(0.0, progress_x)
        progress_y = icon_y + icon_window_width + 6
        PyImGui.set_next_window_pos(progress_x, progress_y)
        PyImGui.set_next_window_size(progress_window_width, 0)

        if PyImGui.begin("##InventoryPlusXunlaiSortProgress", True, window_flags):
            if progress_text:
                PyImGui.text_wrapped(progress_text)
            PyImGui.progress_bar(progress_ratio, progress_width, 0, "")
        PyImGui.end()

    def _close_config_window(self) -> None:
        """Close the config window and clear WidgetManager configure mode."""
        self.show_config_window = False
        self._configure_session_active = False
        try:
            from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
            get_widget_handler().set_widget_configuring("InventoryPlus", False)
        except Exception:
            pass

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
        self.inventory_window_settings.add_config_vars(self.ini_key)
        
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
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="salvage_dialog_auto_handle", name="salvage_dialog_auto_handle", default=False)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="salvage_dialog_auto_confirm_materials", name="salvage_dialog_auto_confirm_materials", default=False)
        IniManager().add_bool(key=self.ini_key, section=_section, var_name="salvage_dialog_debug", name="salvage_dialog_debug", default=False)
        IniManager().add_int(key=self.ini_key, section=_section, var_name="salvage_dialog_strategy", name="salvage_dialog_strategy", default=0)
        IniManager().add_int(key=self.ini_key, section=_section, var_name="salvage_dialog_fallback_index", name="salvage_dialog_fallback_index", default=1)
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

    def _set_colorize_enabled(self, enabled: bool) -> None:
        self.colorize_settings.enable_colorize = enabled
        IniManager().set(key=self.ini_key, section="Colorize", var_name="enable_colorize", value=enabled)

    def _toggle_colorize_enabled(self) -> None:
        self._set_colorize_enabled(not self.colorize_settings.enable_colorize)

    def _set_auto_inventory_enabled(self, enabled: bool) -> None:
        self.auto_inventory_handler.module_active = enabled
        IniManager().set(key=self.ini_key, section="AutoManager", var_name="module_active", value=enabled)

    def _toggle_auto_inventory_enabled(self) -> None:
        self._set_auto_inventory_enabled(not self.auto_inventory_handler.module_active)

    def _set_i_window_enabled(self, enabled: bool) -> None:
        from Py4GWCoreLib.UIManager import UIManager, WindowID

        self.inventory_window_settings.enable_i_window = enabled
        if enabled:
            if self._i_window_was_forced_closed:
                UIManager.SetWindowVisible(WindowID.WindowID_Inventory, True)
            self._i_window_was_forced_closed = False
        else:
            self.selected_item = None
            if UIManager.IsWindowVisible(WindowID.WindowID_Inventory):
                UIManager.SetWindowVisible(WindowID.WindowID_Inventory, False)
                self._i_window_was_forced_closed = True
            else:
                self._i_window_was_forced_closed = False
        IniManager().set(key=self.ini_key, section="InventoryWindow", var_name="enable_i_window", value=enabled)

    def _toggle_i_window_enabled(self) -> None:
        self._set_i_window_enabled(not self.inventory_window_settings.enable_i_window)

    def _enforce_i_window_setting(self) -> None:
        from Py4GWCoreLib.UIManager import UIManager, WindowID

        if self.inventory_window_settings.enable_i_window:
            return

        if UIManager.IsWindowVisible(WindowID.WindowID_Inventory):
            UIManager.SetWindowVisible(WindowID.WindowID_Inventory, False)
            self._i_window_was_forced_closed = True
     
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

            except Exception:
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

        cfg = self.inventory_window_settings
        cfg.enable_i_window = IniManager().getBool(key=self.ini_key, section="InventoryWindow", var_name="enable_i_window", default=cfg.enable_i_window)
    
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
        self.auto_inventory_handler.salvage_dialog_auto_handle = IniManager().getBool(key=self.ini_key, section="AutoSalvage", var_name="salvage_dialog_auto_handle", default=False)
        self.auto_inventory_handler.salvage_dialog_auto_confirm_materials = IniManager().getBool(key=self.ini_key, section="AutoSalvage", var_name="salvage_dialog_auto_confirm_materials", default=False)
        self.auto_inventory_handler.salvage_dialog_debug = IniManager().getBool(key=self.ini_key, section="AutoSalvage", var_name="salvage_dialog_debug", default=False)
        salvage_dialog_strategy = IniManager().getInt(key=self.ini_key, section="AutoSalvage", var_name="salvage_dialog_strategy", default=0)
        self.auto_inventory_handler.salvage_dialog_strategy = _normalize_salvage_dialog_strategy(salvage_dialog_strategy)
        self.auto_inventory_handler.salvage_dialog_fallback_index = max(1, IniManager().getInt(key=self.ini_key, section="AutoSalvage", var_name="salvage_dialog_fallback_index", default=1))
        
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
        from Py4GWCoreLib.enums_src.Item_enums import Bags

        is_storage_item = (
            selected_item is not None
            and Bags.Storage1 <= selected_item.BagID <= Bags.Storage14
        )

        if is_storage_item:
            withdraw_label = "Withdraw Item"
            if selected_item.Quantity > 1:
                withdraw_label = f"Withdraw Stack ({selected_item.Quantity})"

            if PyImGui.menu_item(withdraw_label):
                GLOBAL_CACHE.Inventory.WithdrawItemFromStorage(selected_item.ItemID)
                PyImGui.close_current_popup()

            if PyImGui.menu_item("Withdraw All Same ModelID"):
                routine = cast(
                    Generator[Any, None, None],
                    _withdraw_all_matching_model_from_storage(selected_item.ModelID),
                )
                GLOBAL_CACHE.Coroutines.append(routine)
                PyImGui.close_current_popup()

            PyImGui.separator()
        
        if is_storage_item:
            label = "Disable Colorize" if self.colorize_settings.enable_colorize else "Enable Colorize"
            if PyImGui.menu_item(label):
                self._toggle_colorize_enabled()
                PyImGui.close_current_popup()
            label = "Disable 'I' Window" if self.inventory_window_settings.enable_i_window else "Enable 'I' Window"
            if PyImGui.menu_item(label):
                self._toggle_i_window_enabled()
                PyImGui.close_current_popup()
            PyImGui.separator()
            label = "Disable Auto Inventory" if self.auto_inventory_handler.module_active else "Enable Auto Inventory"
            if PyImGui.menu_item(label):
                self._toggle_auto_inventory_enabled()
                PyImGui.close_current_popup()
            if PyImGui.menu_item("Config Window"):
                self.show_config_window = True
                PyImGui.close_current_popup()
            return
        
        if selected_item and not selected_item.IsIdentified:
            if PyImGui.menu_item("Identify"):
                routine = Routines.Yield.Items.IdentifyItems([selected_item.ItemID], log=True)
                GLOBAL_CACHE.Coroutines.append(routine)
                PyImGui.close_current_popup()

        if (selected_item and
            (selected_item.IsIdentified or selected_item.Rarity != "White") and
            Routines.Checks.Items.IsSalvageable(selected_item.ItemID)):
            # ---------------------------------------------------------------
            # Stack-aware salvage menu entries
            # ---------------------------------------------------------------
            if selected_item.Quantity > 1:
                # Single salvage (consume one item from the stack)
                if PyImGui.menu_item("Salvage (\u00d71)"):
                    _queue_salvage_routine([selected_item.ItemID], label="Salvage Single")
                    PyImGui.close_current_popup()
                # Full-stack salvage (loop until slot is empty)
                if PyImGui.menu_item(f"Salvage All (stack off {selected_item.Quantity})"):
                    _queue_salvage_stack(selected_item)
                    PyImGui.close_current_popup()
            else:
                # Original behaviour for non-stacked items
                if PyImGui.menu_item("Salvage"):
                    _queue_salvage_routine([selected_item.ItemID], label="Salvage Single")
                    PyImGui.close_current_popup()
            # ---------------------------------------------------------------

        if selected_item:
            destroy_label = "Destroy Item"
            if selected_item.Quantity > 1:
                destroy_label = f"Destroy Stack ({selected_item.Quantity})"

            if PyImGui.menu_item(destroy_label):
                GLOBAL_CACHE.Inventory.DestroyItem(selected_item.ItemID)
                PyImGui.close_current_popup()

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
            self._toggle_colorize_enabled()
            PyImGui.close_current_popup()
        label = "Disable 'I' Window" if self.inventory_window_settings.enable_i_window else "Enable 'I' Window"
        if PyImGui.menu_item(label):
            self._toggle_i_window_enabled()
            PyImGui.close_current_popup()
        PyImGui.separator()
        label = "Disable Auto Inventory" if self.auto_inventory_handler.module_active else "Enable Auto Inventory"
        if PyImGui.menu_item(label):
            self._toggle_auto_inventory_enabled()
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
                _salvage_whites(selected_item)
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            salv_shown = True
            
        if cfg.salvage_blues:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Blue").to_tuple_normalized())
            if PyImGui.menu_item("Salvage Blue Items"):
                _salvage_blues(selected_item)
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            salv_shown = True
        
        if cfg.salvage_purples:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Purple").to_tuple_normalized())
            if PyImGui.menu_item("Salvage Purple Items"):
                _salvage_purples(selected_item)
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            salv_shown = True
        
        if cfg.salvage_golds:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Gold").to_tuple_normalized())
            if PyImGui.menu_item("Salvage Gold Items"):
                _salvage_golds(selected_item)
                PyImGui.close_current_popup()
            PyImGui.pop_style_color(1)
            salv_shown = True
            
        if cfg.show_salvage_all:
            if PyImGui.menu_item("Salvage All Items"):
                _salvage_all(self.salvage_settings, selected_item)
                PyImGui.close_current_popup()
            salv_shown = True
            
        if salv_shown:
            PyImGui.separator()  
        self._draw_generic_item_menu_item(selected_item)
        
        
    I_INVENTORY_FRAME_HASH = 2874675009
    I_BAGS_BAR_OFFSETS = (6,)

    def _build_inventory_interaction_context(self) -> InventoryInteractionContext:
        from Py4GWCoreLib.UIManager import UIManager, WindowID, FrameInfo, WindowFrames
        from Py4GWCoreLib.ItemArray import ItemArray
        from Py4GWCoreLib.Item import Item
        from Py4GWCoreLib.enums_src.Item_enums import Bags
        import PyInventory

        context = InventoryInteractionContext(
            f9_visible=UIManager.IsWindowVisible(WindowID.WindowID_InventoryBags),
            i_visible=self.inventory_window_settings.enable_i_window and UIManager.IsWindowVisible(WindowID.WindowID_Inventory),
            storage_visible=UIManager.FrameExists(self.XUNLAI_WINDOW_FRAME_HASH),
        )
        if not context.f9_visible and not context.i_visible and not context.storage_visible:
            return context

        self.InventorySlots.clear()
        self.hovered_item = None

        for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
            try:
                bag_instance = PyInventory.Bag(bag_id, str(bag_id))
                bag_instance.GetContext()
                context.bag_sizes[bag_id] = bag_instance.GetSize()
            except Exception:
                context.bag_sizes[bag_id] = 0

            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)

            for item_id in item_array:
                item_instance = Item.item_instance(item_id)
                item = ItemSlotData(
                    BagID=bag_id,
                    Slot=item_instance.slot,
                    ItemID=item_id,
                    Rarity=item_instance.rarity.name,
                    IsIdentified=item_instance.is_identified,
                    IsIDKit=item_instance.is_id_kit,
                    IsSalvageKit=item_instance.is_salvage_kit,
                    ModelID=item_instance.model_id,
                    Quantity=item_instance.quantity,
                    Value=item_instance.value,
                )
                context.item_data_by_bag_slot[(bag_id, item.Slot)] = item

                if not context.f9_visible:
                    continue

                self.InventorySlots.append(
                    FrameInfo(
                        WindowName=f"Slot{bag_id}_{item.Slot}",
                        ParentFrameHash=WindowFrames["Inventory Bags"].FrameHash,
                        ChildOffsets=[0, 0, 0, bag_id - 1, item.Slot + 2],
                        BlackBoard={"ItemData": item},
                    )
                )

        if context.storage_visible:
            for bag_id in range(Bags.Storage1, Bags.Storage14 + 1):
                try:
                    bag_instance = PyInventory.Bag(bag_id, str(bag_id))
                    bag_instance.GetContext()
                    context.bag_sizes[bag_id] = bag_instance.GetSize()
                except Exception:
                    context.bag_sizes[bag_id] = 0

                bag_to_check = ItemArray.CreateBagList(bag_id)
                item_array = ItemArray.GetItemArray(bag_to_check)

                for item_id in item_array:
                    item_instance = Item.item_instance(item_id)
                    item = ItemSlotData(
                        BagID=bag_id,
                        Slot=item_instance.slot,
                        ItemID=item_id,
                        Rarity=item_instance.rarity.name,
                        IsIdentified=item_instance.is_identified,
                        IsIDKit=item_instance.is_id_kit,
                        IsSalvageKit=item_instance.is_salvage_kit,
                        ModelID=item_instance.model_id,
                        Quantity=item_instance.quantity,
                        Value=item_instance.value,
                    )
                    context.item_data_by_bag_slot[(bag_id, item.Slot)] = item

                    slot_frame_id = self._resolve_storage_slot_frame_id(bag_id, item.Slot)
                    if slot_frame_id != 0:
                        context.storage_slot_frame_ids[(bag_id, item.Slot)] = slot_frame_id

        self._populate_i_inventory_context(context)
        return context

    def _resolve_storage_slot_frame_id(self, bag_id: int, slot: int) -> int:
        from Py4GWCoreLib.enums_src.Item_enums import Bags
        from Py4GWCoreLib.UIManager import UIManager

        if bag_id < Bags.Storage1 or bag_id > Bags.Storage14:
            return 0

        tab_index = bag_id - Bags.Storage1
        slot_frame_id = UIManager.GetChildFrameID(
            self.XUNLAI_WINDOW_FRAME_HASH,
            [0, tab_index, slot + 2],
        )
        if slot_frame_id == 0 or not UIManager.FrameExists(slot_frame_id):
            return 0
        return slot_frame_id

    def _populate_i_inventory_context(self, context: InventoryInteractionContext) -> None:
        from Py4GWCoreLib.UIManager import FrameInfo
        from Py4GWCoreLib.enums_src.Item_enums import Bags

        if not context.i_visible:
            return

        # Wrap the fixed I-layout containers in FrameInfo so later logic can query them consistently.
        i_inventory_frame = FrameInfo(WindowName="InventoryWindowI", FrameHash=self.I_INVENTORY_FRAME_HASH)
        if not i_inventory_frame.FrameExists():
            return

        context.i_inventory_frame_id = i_inventory_frame.GetFrameID()
        i_bags_bar_frame = FrameInfo(
            WindowName="InventoryWindowIBagsBar",
            ParentFrameHash=self.I_INVENTORY_FRAME_HASH,
            ChildOffsets=list(self.I_BAGS_BAR_OFFSETS),
        )
        if i_bags_bar_frame.FrameExists():
            _, _, _, context.i_bags_bar_bottom = i_bags_bar_frame.GetCoords()

        # Resolve a single working slot prefix for the current I-layout frame.
        # If no regular inventory prefix is valid (e.g., unsupported tabs), skip I-slot mapping this frame.
        resolved_prefix = self._resolve_i_regular_bag_prefix(context)
        if resolved_prefix is None:
            return

        for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
            for slot in range(context.bag_sizes.get(bag_id, 0)):
                slot_frame_id = self._resolve_i_slot_frame_id(
                    context,
                    bag_id,
                    slot,
                    prefix=resolved_prefix,
                )
                if slot_frame_id != 0:
                    context.i_slot_frame_ids[(bag_id, slot)] = slot_frame_id

    def _get_colorized_slot_colors(self, item_data: ItemSlotData) -> tuple[Color, Color] | None:
        if (
            (item_data.Rarity == "White" and not self.colorize_settings.color_whites) or
            (item_data.Rarity == "Blue" and not self.colorize_settings.color_blues) or
            (item_data.Rarity == "Green" and not self.colorize_settings.color_greens) or
            (item_data.Rarity == "Purple" and not self.colorize_settings.color_purples) or
            (item_data.Rarity == "Gold" and not self.colorize_settings.color_golds)
        ):
            return None

        if item_data.Rarity == "White":
            base_color = self.colorize_settings.white_color
        elif item_data.Rarity == "Blue":
            base_color = self.colorize_settings.blue_color
        elif item_data.Rarity == "Green":
            base_color = self.colorize_settings.green_color
        elif item_data.Rarity == "Purple":
            base_color = self.colorize_settings.purple_color
        elif item_data.Rarity == "Gold":
            base_color = self.colorize_settings.gold_color
        else:
            base_color = Color(0, 0, 0, 0)

        fill_color = base_color.copy()
        fill_color.set_a(25)
        outline_color = base_color.copy()
        outline_color.set_a(125)
        return fill_color, outline_color

    def _remember_i_inventory_slot_prefix(self, prefix: list[int] | tuple[int, ...]) -> None:
        prefix_key = tuple(prefix)
        if prefix_key not in self.i_inventory_slot_prefix_cache:
            self.i_inventory_slot_prefix_cache.insert(0, prefix_key)
            del self.i_inventory_slot_prefix_cache[8:]
        elif self.i_inventory_slot_prefix_cache and self.i_inventory_slot_prefix_cache[0] != prefix_key:
            self.i_inventory_slot_prefix_cache.remove(prefix_key)
            self.i_inventory_slot_prefix_cache.insert(0, prefix_key)

    def _iter_i_slot_offset_prefixes(self):
        from itertools import product

        seen: set[tuple[int, ...]] = set()
        preferred_prefixes = [
            (),
            (0,),
            (0, 0),
            (0, 0, 0),
            (1,),
            (1, 0),
            (1, 0, 0),
            (2,),
            (2, 0),
            (2, 0, 0),
        ]

        for prefix in self.i_inventory_slot_prefix_cache:
            if prefix in seen:
                continue
            seen.add(prefix)
            yield list(prefix)

        for prefix in preferred_prefixes:
            if prefix in seen:
                continue
            seen.add(prefix)
            yield list(prefix)

        for length in range(1, 4):
            for prefix in product(range(6), repeat=length):
                if prefix in seen:
                    continue
                seen.add(prefix)
                yield list(prefix)

    def _resolve_i_regular_bag_prefix(self, context: InventoryInteractionContext) -> tuple[int, ...] | None:
        from Py4GWCoreLib.enums_src.Item_enums import Bags

        if context.i_inventory_frame_id == 0:
            return None

        probe_slots: list[tuple[int, int]] = []
        for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
            if context.bag_sizes.get(bag_id, 0) <= 0:
                continue
            probe_slots.append((bag_id, 0))

        if not probe_slots:
            return None

        for prefix in self._iter_i_slot_offset_prefixes():
            prefix_key = tuple(prefix)
            for bag_id, slot in probe_slots:
                if self._resolve_i_slot_frame_id(context, bag_id, slot, prefix=prefix_key) == 0:
                    continue
                self._remember_i_inventory_slot_prefix(prefix_key)
                return prefix_key

        return None

    def _resolve_i_slot_frame_id(
        self,
        context: InventoryInteractionContext,
        bag_id: int,
        slot: int,
        prefix: tuple[int, ...] | None = None,
    ) -> int:
        from Py4GWCoreLib.UIManager import UIManager

        if context.i_inventory_frame_id == 0:
            return 0

        if prefix is None:
            prefixes = self._iter_i_slot_offset_prefixes()
        else:
            prefixes = [list(prefix)]

        for candidate_prefix in prefixes:
            slot_frame_id = UIManager.GetChildFrameID(
                self.I_INVENTORY_FRAME_HASH,
                [*candidate_prefix, bag_id - 1, slot + 2],
            )
            if slot_frame_id == 0 or not UIManager.FrameExists(slot_frame_id):
                continue

            _, top, _, _ = UIManager.GetFrameCoords(slot_frame_id)
            if context.i_bags_bar_bottom and top < context.i_bags_bar_bottom - 2:
                continue

            if prefix is None:
                self._remember_i_inventory_slot_prefix(candidate_prefix)
            return slot_frame_id

        return 0

    def _draw_colorized_inventory_slots(self, context: InventoryInteractionContext) -> None:
        from Py4GWCoreLib.UIManager import UIManager

        if not self.colorize_settings.enable_colorize:
            return

        for slot_frame in self.InventorySlots:
            item_data: ItemSlotData = slot_frame.BlackBoard["ItemData"]
            slot_colors = self._get_colorized_slot_colors(item_data)
            if slot_colors is None:
                continue

            fill_color, outline_color = slot_colors
            slot_frame.DrawFrame(color=fill_color.to_color())
            slot_frame.DrawFrameOutline(outline_color.to_color())

        if context.i_inventory_frame_id == 0:
            return

        ui_manager = UIManager()
        for bag_slot, slot_frame_id in context.i_slot_frame_ids.items():
            if bag_slot not in context.item_data_by_bag_slot:
                continue

            item_data = context.item_data_by_bag_slot[bag_slot]
            slot_colors = self._get_colorized_slot_colors(item_data)
            if slot_colors is None:
                continue

            fill_color, outline_color = slot_colors
            ui_manager.DrawFrame(slot_frame_id, fill_color.to_color())
            ui_manager.DrawFrameOutline(slot_frame_id, outline_color.to_color())

    def _resolve_f9_inventory_hit(self, context: InventoryInteractionContext) -> tuple[ItemSlotData | None, bool, str]:
        from Py4GWCoreLib.UIManager import WindowFrames

        if not context.f9_visible:
            return None, False, ""

        for slot_frame in self.InventorySlots:
            if slot_frame.IsMouseOver():
                return slot_frame.BlackBoard["ItemData"], True, "f9"

        if WindowFrames["Inventory Bags"].IsMouseOver():
            return None, True, "f9"

        return None, False, ""

    def _resolve_i_inventory_hit(
        self,
        context: InventoryInteractionContext,
        mouse_x: float,
        mouse_y: float,
    ) -> tuple[ItemSlotData | None, bool, str]:
        from Py4GWCoreLib.UIManager import UIManager

        if context.i_inventory_frame_id == 0:
            return None, False, ""

        if not UIManager.IsMouseOver(context.i_inventory_frame_id):
            return None, False, ""

        for bag_slot, slot_frame_id in context.i_slot_frame_ids.items():
            left, top, right, bottom = UIManager.GetFrameCoords(slot_frame_id)
            if mouse_x < left or mouse_x > right or mouse_y < top or mouse_y > bottom:
                continue

            return context.item_data_by_bag_slot.get(bag_slot), True, "i"

        return None, False, ""

    def _resolve_inventory_hit(
        self,
        context: InventoryInteractionContext,
        mouse_x: float,
        mouse_y: float,
    ) -> tuple[ItemSlotData | None, bool, str]:
        item, hit, source = self._resolve_f9_inventory_hit(context)
        if hit:
            return item, hit, source
        item, hit, source = self._resolve_i_inventory_hit(context, mouse_x, mouse_y)
        if hit:
            return item, hit, source
        return self._resolve_storage_hit(context, mouse_x, mouse_y)

    def _resolve_storage_hit(
        self,
        context: InventoryInteractionContext,
        mouse_x: float,
        mouse_y: float,
    ) -> tuple[ItemSlotData | None, bool, str]:
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
        from Py4GWCoreLib.UIManager import UIManager

        if not context.storage_visible:
            return None, False, ""

        if not UIManager.IsMouseOver(self.XUNLAI_WINDOW_FRAME_HASH):
            return None, False, ""

        hovered_item_id = GLOBAL_CACHE.Inventory.GetHoveredItemID()
        if hovered_item_id and GLOBAL_CACHE.Item.Type.IsStorageItem(hovered_item_id):
            for item_data in context.item_data_by_bag_slot.values():
                if item_data.ItemID == hovered_item_id:
                    return item_data, True, "storage"

        for bag_slot, slot_frame_id in context.storage_slot_frame_ids.items():
            left, top, right, bottom = UIManager.GetFrameCoords(slot_frame_id)
            if mouse_x < left or mouse_x > right or mouse_y < top or mouse_y > bottom:
                continue

            return context.item_data_by_bag_slot.get(bag_slot), True, "storage"

        return None, False, ""

    def DetectInventoryAction(self):
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
        from Py4GWCoreLib.enums_src.IO_enums import MouseButton
        from Py4GWCoreLib.enums_src.Model_enums import ModelID

        self._enforce_i_window_setting()

        # Build shared inventory state first so slot colors and click targeting stay in sync.
        context = self._build_inventory_interaction_context()
        if not context.f9_visible and not context.i_visible and not context.storage_visible:
            self.selected_item = None
            return

        self._draw_colorized_inventory_slots(context)
        self._draw_xunlai_sort_button(context)

        io = PyImGui.get_io()
        mouse_x = io.mouse_pos_x
        mouse_y = io.mouse_pos_y

        # Capture the clicked item before the popup can steal hover.
        if PyImGui.is_mouse_clicked(MouseButton.Right.value):
            clicked_item, inventory_hit, _source = self._resolve_inventory_hit(context, mouse_x, mouse_y)
            self.hovered_item = clicked_item
            self.selected_item = clicked_item if inventory_hit else None

            if inventory_hit:
                PyImGui.open_popup("SlotContextMenu")

        # Detect Ctrl + Left Click
        if PyImGui.is_mouse_released(MouseButton.Left.value) and io.key_ctrl:
            clicked_item, inventory_hit, _source = self._resolve_inventory_hit(context, mouse_x, mouse_y)
            self.hovered_item = clicked_item
            if inventory_hit and clicked_item:
                self.selected_item = clicked_item
                if self.deposit_settings.use_ctrl_click:
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(self.selected_item.ItemID)
                return

        # Render popup
        if PyImGui.begin_popup("SlotContextMenu"):

            if self.selected_item:
                if self.selected_item.IsIDKit:
                    self._draw_id_kit_menu_item(self.selected_item)
                elif self.selected_item.IsSalvageKit and self.selected_item.ModelID in (ModelID.Salvage_Kit, ModelID.Expert_Salvage_Kit, ModelID.Superior_Salvage_Kit):
                    self._draw_salvage_kit_menu_item(self.selected_item)
                else:
                    self._draw_generic_item_menu_item(self.selected_item)
            else:
                self._draw_generic_item_menu_item()

            PyImGui.end_popup()

        else:
            # popup is not open -> clear selection
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
            cfg_attr = var_name
            val = bool(getattr(cfg_obj, cfg_attr, default))
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
                window_cfg = self.inventory_window_settings
                if PyImGui.begin_tab_item("Windows"):
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, GW_WHITE.to_tuple_normalized())
                    new_enable_i_window = PyImGui.checkbox("Enable 'I' Inventory Window", window_cfg.enable_i_window)
                    PyImGui.pop_style_color(1)
                    if new_enable_i_window != window_cfg.enable_i_window:
                        self._set_i_window_enabled(new_enable_i_window)

                    if window_cfg.enable_i_window:
                        PyImGui.text_wrapped("When enabled, InventoryPlus handles slot highlighting and context actions for the game's 'I' inventory window.")
                    else:
                        color = ColorPalette.GetColor("dark_red")
                        PyImGui.text_colored("Disabled: InventoryPlus forces the game's 'I' inventory window closed.", color.to_tuple_normalized())
                        PyImGui.text_colored("I-window slot mapping, coloring, and click handling are skipped.", color.to_tuple_normalized())
                    PyImGui.end_tab_item()

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
                        PyImGui.text_colored("Upgrade/component salvage prompts can be auto-handled in the dialog section below.", color.to_tuple_normalized())
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

                    if PyImGui.collapsing_header("Upgrade/Component Dialog:"):
                        color = ColorPalette.GetColor("dark_red")
                        PyImGui.text_colored("Handles the salvage popup that appears when upgrades or components can be salvaged.", color.to_tuple_normalized())
                        PyImGui.text_colored("If text cannot be read reliably, InventoryPlus falls back to the visible order under child[5].", color.to_tuple_normalized())
                        self.auto_inventory_handler.salvage_dialog_auto_handle = ini_colored_checkbox("Auto Handle Salvage Choice Dialog", "AutoSalvage", "salvage_dialog_auto_handle", self.auto_inventory_handler, GW_WHITE, default=self.auto_inventory_handler.salvage_dialog_auto_handle)
                        self.auto_inventory_handler.salvage_dialog_auto_confirm_materials = ini_colored_checkbox("Auto Confirm Crafting Materials Warning", "AutoSalvage", "salvage_dialog_auto_confirm_materials", self.auto_inventory_handler, GW_WHITE, default=self.auto_inventory_handler.salvage_dialog_auto_confirm_materials)
                        self.auto_inventory_handler.salvage_dialog_debug = ini_colored_checkbox("Debug Salvage Choice Dialog", "AutoSalvage", "salvage_dialog_debug", self.auto_inventory_handler, GW_WHITE, default=self.auto_inventory_handler.salvage_dialog_debug)
                        PyImGui.text_wrapped("The crafting materials warning destroys upgrades. Leave auto-confirm off if you want to approve that prompt manually.")
                        if self.auto_inventory_handler.salvage_dialog_auto_handle:
                            salvage_dialog_strategy_labels = [
                                "Prefer Crafting Materials",
                                "Prefer Upgrades/Components",
                            ]
                            current_dialog_strategy = _normalize_salvage_dialog_strategy(int(self.auto_inventory_handler.salvage_dialog_strategy))
                            if current_dialog_strategy != int(self.auto_inventory_handler.salvage_dialog_strategy):
                                self.auto_inventory_handler.salvage_dialog_strategy = current_dialog_strategy
                                IniManager().set(key=self.ini_key, section="AutoSalvage", var_name="salvage_dialog_strategy", value=current_dialog_strategy)
                            new_dialog_strategy = PyImGui.combo("Salvage Choice Strategy", current_dialog_strategy, salvage_dialog_strategy_labels)
                            if new_dialog_strategy != current_dialog_strategy:
                                self.auto_inventory_handler.salvage_dialog_strategy = new_dialog_strategy
                                IniManager().set(key=self.ini_key, section="AutoSalvage", var_name="salvage_dialog_strategy", value=new_dialog_strategy)
                                current_dialog_strategy = new_dialog_strategy

                            if current_dialog_strategy == 0:
                                PyImGui.text_wrapped("Crafting Materials prefers a materials text match when available, otherwise the last visible option.")
                            else:
                                PyImGui.text_wrapped("Upgrades/Components prefers a non-material text match when available, otherwise the first visible option.")
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
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, GW_WHITE.to_tuple_normalized())
                    new_enable_colorize = PyImGui.checkbox("Enable Item Colorize", cfg.enable_colorize)
                    PyImGui.pop_style_color(1)
                    if new_enable_colorize != cfg.enable_colorize:
                        self._set_colorize_enabled(new_enable_colorize)
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
                        except Exception:
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
                    old_val = self.auto_inventory_handler.module_active
                    new_val = PyImGui.checkbox("Enable Auto Inventory Handler", old_val)
                    if new_val != old_val:
                        self._set_auto_inventory_enabled(new_val)
              
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
                self._close_config_window()
            """PyImGui.same_line(0,-1)
            if PyImGui.button("Save & Close"):
                self.save_to_ini()
                self.load_from_ini()
                self.show_config_window = False"""
        ImGui.End(self.ini_key)



InventoryPlusWidgetInstance = InventoryPlusWidget()

def configure():
    if not InventoryPlusWidgetInstance.initialized:
        return

    # WidgetManager calls configure() every frame while "configuring" is active.
    # Open only once per configure-session so the in-window Close button can persist.
    if not InventoryPlusWidgetInstance._configure_session_active:
        InventoryPlusWidgetInstance._configure_session_active = True
        InventoryPlusWidgetInstance.show_config_window = True
        return

    # When user closes the config window, stop WidgetManager configure mode.
    if not InventoryPlusWidgetInstance.show_config_window:
        InventoryPlusWidgetInstance._close_config_window()


def main():
    InventoryPlusWidgetInstance._refresh_runtime_if_source_changed()

    if not InventoryPlusWidgetInstance.initialized:
        if not InventoryPlusWidgetInstance._ensure_ini_key():
            return

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

