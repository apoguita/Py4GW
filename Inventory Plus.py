from Py4GWCoreLib import (Color, WindowID, UIManager, Bags, ItemArray, Item, MouseButton, ColorPalette, ModelID,
                        FrameInfo)
import PyImGui
import PyPlayer
from dataclasses import dataclass, field


WindowFrames:dict[str, FrameInfo] = {}

InventoryBags = FrameInfo(
    WindowID = WindowID.WindowID_InventoryBags,
    WindowName = "Inventory Bags",
    WindowLabel = "InvAggregate",
    FrameHash = 291586130
)
    
WindowFrames["Inventory Bags"] = InventoryBags

InventorySlots: list[FrameInfo] = []

@dataclass
class ItemSlotData:
    BagID: int
    Slot: int
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

@dataclass
class SettingsNode:
    show_in_menu: bool = True
    enable_auto: bool = False
    
@dataclass
class IdentificationSettings:
    identify_whites: SettingsNode = field(default_factory=SettingsNode)
    identify_blues: SettingsNode = field(default_factory=SettingsNode)
    identify_greens: SettingsNode = field(default_factory=SettingsNode)
    identify_purples: SettingsNode = field(default_factory=SettingsNode)
    identify_golds: SettingsNode = field(default_factory=SettingsNode)
    identify_all: SettingsNode = field(default_factory=SettingsNode)
    
@dataclass
class SalvageSettings:
    salvage_whites: SettingsNode = field(default_factory=SettingsNode)
    salvage_blues: SettingsNode = field(default_factory=SettingsNode)
    salvage_greens: SettingsNode = field(default_factory=SettingsNode)
    salvage_purples: SettingsNode = field(default_factory=SettingsNode)
    salvage_golds: SettingsNode = field(default_factory=SettingsNode)
    salvage_all: SettingsNode = field(default_factory=SettingsNode)
    
@dataclass
class InventoryPlusConfig:
    identification_settings: IdentificationSettings = field(default_factory=IdentificationSettings)
    salvage_settings: SalvageSettings = field(default_factory=SalvageSettings)

config_settings = InventoryPlusConfig()

def _draw_id_kit_menu_item(selected_item: ItemSlotData):
    global show_config_window, config_settings
    cfg = config_settings.identification_settings
    if cfg.identify_whites.show_in_menu:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_White").to_tuple_normalized())
        if PyImGui.menu_item("ID White Items"):
            print(f"ID WHITES with Kit: {selected_item.ModelID}")  # real logic
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.identify_blues.show_in_menu:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Blue").to_tuple_normalized())
        if PyImGui.menu_item("ID Blue Items"):
            print(f"ID BLUES with Kit: {selected_item.ModelID}")  # real logic
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.identify_purples.show_in_menu:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Purple").to_tuple_normalized())
        if PyImGui.menu_item("ID Purple Items"):
            print(f"ID PURPLES with Kit: {selected_item.ModelID}")  # real logic
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.identify_golds.show_in_menu:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Gold").to_tuple_normalized())
        if PyImGui.menu_item("ID Gold Items"):
            print(f"ID GOLDS with Kit: {selected_item.ModelID}")  # real logic
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.identify_greens.show_in_menu:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Green").to_tuple_normalized())
        if PyImGui.menu_item("ID Green Items"):
            print(f"ID GREENS with Kit: {selected_item.ModelID}")  # real logic
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
        
    PyImGui.separator()  
    if PyImGui.menu_item("Config Window"):
        show_config_window = True
        PyImGui.close_current_popup()
        
def _draw_salvage_kit_menu_item(selected_item: ItemSlotData):
    global show_config_window, config_settings
    cfg = config_settings.salvage_settings
    if cfg.salvage_whites.show_in_menu:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_White").to_tuple_normalized())
        if PyImGui.menu_item("Salvage White Items"):
            print(f"SALVAGE WHITES with Kit: {selected_item.ModelID}")  # real logic
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.salvage_blues.show_in_menu:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Blue").to_tuple_normalized())
        if PyImGui.menu_item("Salvage Blue Items"):
            print(f"SALVAGE BLUES with Kit: {selected_item.ModelID}")  # real logic
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.salvage_purples.show_in_menu:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Purple").to_tuple_normalized())
        if PyImGui.menu_item("Salvage Purple Items"):
            print(f"SALVAGE PURPLES with Kit: {selected_item.ModelID}")  # real logic
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
    
    if cfg.salvage_golds.show_in_menu:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("GW_Gold").to_tuple_normalized())
        if PyImGui.menu_item("Salvage Gold Items"):
            print(f"SALVAGE GOLDS with Kit: {selected_item.ModelID}")  # real logic
            PyImGui.close_current_popup()
        PyImGui.pop_style_color(1)
        
    PyImGui.separator()  
    if PyImGui.menu_item("Config Window"):
        show_config_window = True
        PyImGui.close_current_popup()
        
def _draw_generic_item_menu_item(selected_item: ItemSlotData | None = None):
    global show_config_window
    PyImGui.text("No item selected.")
    PyImGui.separator()
    if PyImGui.menu_item("Config Window"):
        show_config_window = True
        PyImGui.close_current_popup()

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

    io = PyImGui.get_io()
    mouse_x, mouse_y = io.mouse_pos_x, io.mouse_pos_y

    # Detect right click
    if PyImGui.is_mouse_released(MouseButton.Right.value):

        # Only trigger if user clicked over inventory window
        if WindowFrames["Inventory Bags"].IsMouseOver(mouse_x, mouse_y):
            
            selected_item = None  # first assume empty click
            for slot_frame in InventorySlots:
                if slot_frame.IsMouseOver(mouse_x, mouse_y):
                    selected_item = slot_frame.BlackBoard["ItemData"]
                    break

            PyImGui.open_popup("SlotContextMenu")

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
            if PyImGui.begin_tab_item("Identification Settings"):
                PyImGui.text("Identification Menu Options:")
                PyImGui.separator()
                cfg = config_settings.identification_settings
                cfg.identify_whites.show_in_menu = _colored_checkbox("Show ID Whites in Menu", cfg.identify_whites.show_in_menu, GW_WHITE)
                cfg.identify_blues.show_in_menu = _colored_checkbox("Show ID Blues in Menu", cfg.identify_blues.show_in_menu, GW_BLUE)
                cfg.identify_purples.show_in_menu = _colored_checkbox("Show ID Purples in Menu", cfg.identify_purples.show_in_menu, GW_PURPLE)
                cfg.identify_golds.show_in_menu = _colored_checkbox("Show ID Golds in Menu", cfg.identify_golds.show_in_menu, GW_GOLD)
                cfg.identify_greens.show_in_menu = _colored_checkbox("Show ID Greens in Menu", cfg.identify_greens.show_in_menu, GW_GREEN)
                cfg.identify_all.show_in_menu = PyImGui.checkbox("Show ID All in Menu", cfg.identify_all.show_in_menu)
                PyImGui.separator()
                PyImGui.text("Automatic Handling Options:")
                cfg.identify_whites.enable_auto = _colored_checkbox("Automatically ID Whites", cfg.identify_whites.enable_auto, GW_WHITE)
                cfg.identify_blues.enable_auto = _colored_checkbox("Automatically ID Blues", cfg.identify_blues.enable_auto, GW_BLUE)
                cfg.identify_purples.enable_auto = _colored_checkbox("Automatically ID Purples", cfg.identify_purples.enable_auto, GW_PURPLE)
                cfg.identify_golds.enable_auto = _colored_checkbox("Automatically ID Golds", cfg.identify_golds.enable_auto, GW_GOLD)
                cfg.identify_greens.enable_auto = _colored_checkbox("Automatically ID Greens", cfg.identify_greens.enable_auto, GW_GREEN)
                PyImGui.separator()
                                 
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Salvage Settings"):
                PyImGui.text("Salvage Menu Options:")
                PyImGui.separator()
                cfg = config_settings.salvage_settings
                cfg.salvage_whites.show_in_menu = _colored_checkbox("Show Salvage Whites in Menu", cfg.salvage_whites.show_in_menu, GW_WHITE)
                cfg.salvage_blues.show_in_menu = _colored_checkbox("Show Salvage Blues in Menu", cfg.salvage_blues.show_in_menu, GW_BLUE)
                cfg.salvage_purples.show_in_menu = _colored_checkbox("Show Salvage Purples in Menu", cfg.salvage_purples.show_in_menu, GW_PURPLE)
                cfg.salvage_golds.show_in_menu = _colored_checkbox("Show Salvage Golds in Menu", cfg.salvage_golds.show_in_menu, GW_GOLD)
                cfg.salvage_all.show_in_menu = PyImGui.checkbox("Show Salvage All in Menu", cfg.salvage_all.show_in_menu)
                PyImGui.separator() 
                PyImGui.text("Automatic Handling Options:")
                cfg.salvage_whites.enable_auto = _colored_checkbox("Automatically Salvage Whites", cfg.salvage_whites.enable_auto, GW_WHITE)
                cfg.salvage_blues.enable_auto = _colored_checkbox("Automatically Salvage Blues", cfg.salvage_blues.enable_auto, GW_BLUE)
                cfg.salvage_purples.enable_auto = _colored_checkbox("Automatically Salvage Purples", cfg.salvage_purples.enable_auto, GW_PURPLE)
                cfg.salvage_golds.enable_auto = _colored_checkbox("Automatically Salvage Golds", cfg.salvage_golds.enable_auto, GW_GOLD)
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()
        PyImGui.separator()
        if PyImGui.button("Close"):
            show_config_window = False
    PyImGui.end()

def main():
    DetectInventoryAction()
    if show_config_window:
        ShowConfigWindow()


if __name__ == "__main__":
    main()
