import Py4GW
from Py4GWCoreLib import Timer
from Py4GWCoreLib import Utils
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import WindowID
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib import Bags
from Py4GWCoreLib import Inventory
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import Routines
from Py4GWCoreLib import AutoInventoryHandler

from enum import Enum
from typing import Dict
import math
from time import sleep


MODULE_NAME = "ID & Salvage"

COMPACT_WIDTH = 275
MAX_BAGS = 4

#region Types
#ColorizeType
class ColorizeType(Enum):
    colorize = 1
    identification = 2
    salvage = 3
    vault = 4
    
#TabType 
class TabType(Enum):
    hide = 0
    show = 1
    colorize = 2
    identification = 3
    salvage = 4
    search = 5
    xunlai_vault = 6
    mods = 7
    auto_handler = 8
    
#Colorize config
class color_config:
    def __init__(self):
        self.colorize_whites = False
        self.colorize_blues = True
        self.colorize_greens = True
        self.colorize_purples = True
        self.colorize_golds = True
        self.colorize_ignored = True
        
#Xunlai Vault config
class xunlaivault_config:
    def __init__(self):
        self.synch_vault_with_inventory = True
        self.frame_id = 0
        self.xunlai_window_exists = False
    
#id config    
class id_config:
    def __init__(self):
        self.enabled = False
        self.frame_id = 0
        self.inventory_window_exists = False
  
#salvage config      
class salvage_config:
    def __init__(self):
        self.enabled = False
        self.frame_id = 0
        self.inventory_window_exists = False
        
#global config
class config:
    global parent_frame_id, inventory_frame_hash, MAX_BAGS
    
    def __init__(self):
        self.inventory_window_exists = False
        
        self.game_throttle_time = 500
        self.game_throttle_timer = Timer()
        self.game_throttle_timer.Start()
        self.id_vars = id_config()
        self.salvage_vars = salvage_config()
        self.colorize_vars = ColorizeType.colorize
        self.selected_tab = TabType.colorize
        
        
#endregion

#region rarity colors

rarity_colors = {
    "White": {
        "frame": Utils.RGBToColor(255, 255, 255, 125),
        "content": Utils.RGBToColor(255, 255, 255, 25),
        "text": Utils.RGBToColor(255, 255, 255, 255),
    },
    "Blue": {
        "frame": Utils.RGBToColor(0, 170, 255, 125),
        "content": Utils.RGBToColor(0, 170, 255, 25),
        "text": Utils.RGBToColor(0, 170, 255, 255),
    },
    "Green": {
        "frame": Utils.RGBToColor(25, 200, 0, 125),
        "content": Utils.RGBToColor(25, 200, 0, 25),
        "text": Utils.RGBToColor(25, 200, 0, 255),
    },
    "Purple": {
        "frame": Utils.RGBToColor(110, 65, 200, 125),
        "content": Utils.RGBToColor(110, 65, 200, 25),
        "text": Utils.RGBToColor(110, 65, 200, 255),
    },
    "Gold": {
        "frame": Utils.RGBToColor(225, 150, 0, 125),
        "content": Utils.RGBToColor(225, 150, 0, 25),
        "text": Utils.RGBToColor(225, 150, 0, 255),
    },
    "Ignored": {
        "frame": Utils.RGBToColor(26, 26, 26, 225),
        "content": Utils.RGBToColor(26, 26, 26, 225),
        "text": Utils.RGBToColor(26, 26, 26, 255),
    },
}

#endregion


#region Globals
class FrameCoords:
    def __init__(self, frame_id):
        self.frame_id = frame_id
        self.left, self.top, self.right, self.bottom = UIManager.GetFrameCoords(self.frame_id) 
        self.height = self.bottom - self.top
        self.width = self.right - self.left      
        
class GlobalVarsClass:
    def __init__(self):
        self.config = config()

        self.inventory_frame_hash = 291586130
        self.inventory_frame_exists = False
        self.xunlaivault_frame_hash = 2315448754
        self.xunlaivault_frame_exists = False
        self.inventory_frame_coords: FrameCoords

        
        self.game_throttle = Timer()
        self.game_throttle.Start()
        self.game_throttle_time = 100
        
        self.selected_item = TabType.colorize
        self.compact_view = False
        self.hide_ui = False
        self.colorize_config = color_config()
        self.id_selected_item = 0
        self.salv_selected_item = 0
        
        
        
        self.parent_frame_id = 0
        self.total_id_uses = 0
        self.total_salvage_uses = 0
        self.identification_checkbox_states: Dict[int, bool] = {}
        self.salvage_checkbox_states: Dict[int, bool] = {}
        
        self.id_queue_reset_done = False
        self.salv_queue_reset_done = False
        
        self.auto_widget_options = AutoInventoryHandler()
        
    def process_game_throttle(self):
        if self.game_throttle.HasElapsed(self.game_throttle_time):
            if UIManager.IsWindowVisible(WindowID.WindowID_InventoryBags):
                self.parent_frame_id = UIManager.GetFrameIDByHash(self.inventory_frame_hash)
                if self.parent_frame_id != 0:
                    self.inventory_frame_exists = UIManager.FrameExists(self.parent_frame_id)
                else:
                    self.inventory_frame_exists = False
            else:
                self.parent_frame_id = 0
                self.inventory_frame_exists = False

            self.game_throttle.Reset()

global_vars = GlobalVarsClass()

#endregion

#region Floating_Checkbox
@staticmethod
def floating_checkbox(caption, state,x,y, color):
    width=20
    height=20
    # Set the position and size of the floating button
    PyImGui.set_next_window_pos(x, y)
    PyImGui.set_next_window_size(width, height)
    

    flags=( PyImGui.WindowFlags.NoCollapse | 
        PyImGui.WindowFlags.NoTitleBar |
        PyImGui.WindowFlags.NoScrollbar |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.AlwaysAutoResize  ) 
    
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding,0.0,0.0)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, color)
       
    result = state
    if PyImGui.begin(f"##invisible_window{caption}", flags):
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0.2, 0.3, 0.4, 0.1))  # Normal state color
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0.3, 0.4, 0.5, 0.1))  # Hovered state
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0.4, 0.5, 0.6, 0.1))  # Checked state
        PyImGui.push_style_color(PyImGui.ImGuiCol.CheckMark, (1.0, 1.0, 1.0, 1.0))  # White checkmark

        result = PyImGui.checkbox(f"##floating_checkbox{caption}", state)
        PyImGui.pop_style_color(4)
    PyImGui.end()
    PyImGui.pop_style_var(2)
    PyImGui.pop_style_color(1)
    return result

@staticmethod
def floating_button(caption, name, x,y, color):
    width=18
    height=18
    # Set the position and size of the floating button
    PyImGui.set_next_window_pos(x, y)
    PyImGui.set_next_window_size(width, height)
    

    flags=( PyImGui.WindowFlags.NoCollapse | 
        PyImGui.WindowFlags.NoTitleBar |
        PyImGui.WindowFlags.NoScrollbar |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.AlwaysAutoResize  ) 
    
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding,-5,-3)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
       
    result = False
    if PyImGui.begin(f"{caption}##invisible_buttonwindow{name}", flags):
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0.2, 0.3, 0.4, 0.1))  # Normal state color
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0.3, 0.4, 0.5, 0.1))  # Hovered state
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0.4, 0.5, 0.6, 0.1))  # Checked state
        PyImGui.push_style_color(PyImGui.ImGuiCol.CheckMark, (1.0, 1.0, 1.0, 1.0))  # White checkmark
        result = PyImGui.button(caption)
    PyImGui.end()
    PyImGui.pop_style_var(2)
    PyImGui.pop_style_color(1)
    return result
#endregion

#region globals     

xunlai_vault_config = xunlaivault_config()


window_module = ImGui.WindowModule(
    MODULE_NAME, 
    window_name="ID & Salvage", 
    window_size=(300, 200),
    window_flags=PyImGui.WindowFlags.AlwaysAutoResize
)


#endregion

RGBA = [255, 0, 0, 255]  # Start with red
_color_tick = 0

def advance_rainbow_color():
    global RGBA, _color_tick
    _color_tick += 1

    # Use sine waves offset from each other to create a rainbow pulse
    RGBA[0] = int((math.sin(_color_tick * 0.05) * 0.5 + 0.5) * 255)  # Red wave
    RGBA[1] = int((math.sin(_color_tick * 0.05 + 2.0) * 0.5 + 0.5) * 255)  # Green wave
    RGBA[2] = int((math.sin(_color_tick * 0.05 + 4.0) * 0.5 + 0.5) * 255)  # Blue wave


class TitleClass():
        def __init__(self, tab: TabType):
            self.tab = tab 
            self.name = self._get_name()
            
        def _get_name(self):
            global global_vars
            
            if global_vars.inventory_frame_coords.width > COMPACT_WIDTH:
                compact_view = False
            else:
                compact_view = True
            
            if not compact_view:
                if self.tab == TabType.colorize:
                    return "- [Inventory+]"
                if self.tab == TabType.auto_handler:
                    return "- [Auto Handler]"
                if self.tab == TabType.identification:
                    return "- [Mass ID]"
                if self.tab == TabType.salvage:
                    return "- [Mass Salvage]"
                if self.tab == TabType.search:
                    return "- [Filter]"
                if self.tab == TabType.xunlai_vault:
                    return "- [Xunlai Vault]"
                if self.tab == TabType.mods:
                    return "- [Merchant]"
            else:
                if self.tab == TabType.colorize:
                    return "- [Inv+]"
                if self.tab == TabType.auto_handler:
                    return "- [Auto]"
                if self.tab == TabType.identification:
                    return "- [ID]"
                if self.tab == TabType.salvage:
                    return "- [Salvage]"
                if self.tab == TabType.search:
                    return "- [Filter]"
                if self.tab == TabType.xunlai_vault:
                    return "- [Vault]"
                if self.tab == TabType.mods:
                    return "- [Merch]"
            return ""
                
        
        def draw(self):
            global global_vars
            window_title_x = global_vars.inventory_frame_coords.left + 140
            window_title_y = global_vars.inventory_frame_coords.top + 4
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
            flags= ImGui.PushTransparentWindow()
            
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding,0.0,0.0)
            PyImGui.set_next_window_pos(window_title_x, window_title_y)
            PyImGui.set_next_window_size(0, 15)
            if PyImGui.begin("##titleWindow",True, flags):
                PyImGui.text(self.name)
            PyImGui.end()
            PyImGui.pop_style_var(1)

            ImGui.PopTransparentWindow()

#region Item Routines
def AutoID(item_id):
    global global_vars
    first_id_kit = GLOBAL_CACHE.Inventory.GetFirstIDKit()
    if first_id_kit == 0:
        for item_id in global_vars.identification_checkbox_states:
            global_vars.identification_checkbox_states[item_id] = False
    else:
        Inventory.IdentifyItem(item_id, first_id_kit)
        global_vars.identification_checkbox_states[item_id] = False
    
    # Remove checkbox states that are set to False
    for item_id in list(global_vars.identification_checkbox_states):
        if not global_vars.identification_checkbox_states[item_id]:
            del global_vars.identification_checkbox_states[item_id]
    
def IdentifyItems():
    global global_vars
    ActionQueueManager().ResetQueue("IDENTIFY")
    ActionQueueManager().ResetQueue("SALVAGE")
    for item_id in global_vars.identification_checkbox_states:
        if global_vars.identification_checkbox_states[item_id]:
            ActionQueueManager().AddAction("IDENTIFY", AutoID, item_id)
            
def AutoSalvage(item_id):
    global global_vars
    first_salv_kit = GLOBAL_CACHE.Inventory.GetFirstSalvageKit(use_lesser=True)
    if first_salv_kit == 0:
        for item_id in global_vars.salvage_checkbox_states:
            global_vars.salvage_checkbox_states[item_id] = False
    else:
        Inventory.SalvageItem(item_id, first_salv_kit)
        global_vars.salvage_checkbox_states[item_id] = False
        
    # Remove checkbox states that are set to False
    for item_id in list(global_vars.salvage_checkbox_states):
        if not global_vars.salvage_checkbox_states[item_id]:
            del global_vars.salvage_checkbox_states[item_id]

def SalvageItems():
    ActionQueueManager().ResetQueue("IDENTIFY")
    ActionQueueManager().ResetQueue("SALVAGE")
    for item_id in global_vars.salvage_checkbox_states:
        if global_vars.salvage_checkbox_states[item_id]:
            quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
            for _ in range(quantity):
                ActionQueueManager().AddAction("SALVAGE", AutoSalvage, item_id)
                ActionQueueManager().AddAction("SALVAGE",Inventory.AcceptSalvageMaterialsWindow)
 
#endregion

#region DrawButtonStrip
def DrawButtonStrip():
    global global_vars
    
    advance_rainbow_color()
    r, g, b, a = RGBA[0]/255.0, RGBA[1]/255.0, RGBA[2]/255.0, RGBA[3]/255.0

    flags= ImGui.PushTransparentWindow()

    PyImGui.set_next_window_pos(global_vars.inventory_frame_coords.left+10, global_vars.inventory_frame_coords.top-23)
    PyImGui.set_next_window_size(0 if global_vars.inventory_frame_coords.width > 275 else global_vars.inventory_frame_coords.width, 23)
        
    if PyImGui.begin(window_module.window_name,True, flags):
        ImGui.PopTransparentWindow()
        global_vars.config.colorize_vars = ColorizeType.colorize
        if PyImGui.begin_tab_bar("##TabBar"):
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (r, g, b, a))
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_PALETTE + "##ColorizeTab"):
                global_vars.config.colorize_vars = ColorizeType.colorize
                global_vars.config.selected_tab = TabType.colorize
                PyImGui.end_tab_item()
            PyImGui.pop_style_color(1)
            ImGui.show_tooltip("Inventory+")
            if global_vars.auto_widget_options.module_active:
                active_tooltip = "AutoHandler is active"
            else:
                active_tooltip = "AutoHandler is inactive"
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_CALENDAR_CHECK +  "##AutoHandlerTab"):
                global_vars.config.selected_tab = TabType.auto_handler
                PyImGui.end_tab_item()
            ImGui.show_tooltip(active_tooltip)
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_QUESTION +  "##IDTab"):
                global_vars.config.colorize_vars = ColorizeType.identification
                global_vars.config.selected_tab = TabType.identification
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Mass ID")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_RECYCLE + "##SalvageTab"):
                global_vars.config.colorize_vars = ColorizeType.salvage
                global_vars.config.selected_tab = TabType.salvage
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Mass Salvage")
            if GLOBAL_CACHE.Map.IsOutpost():
                if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_BOX_OPEN + "##XunlaiVaultTab"):
                    global_vars.config.colorize_vars = ColorizeType.vault
                    global_vars.config.selected_tab = TabType.xunlai_vault
                    PyImGui.end_tab_item()
                ImGui.show_tooltip("Xunlai Vault")
            """
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_BALANCE_SCALE + "##merchantTab"):
                global_vars.config.colorize_vars = ColorizeType.colorize
                global_vars.config.selected_tab = TabType.mods
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Merchant")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_SEARCH + "##invsearchTab"):
                global_vars.config.colorize_vars = ColorizeType.colorize
                global_vars.config.selected_tab = TabType.search
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Filter")
            """
            PyImGui.end_tab_bar()
    else:
        ImGui.PopTransparentWindow()    
    
    PyImGui.end()
    
    if not global_vars.hide_ui:
        TitleClass(global_vars.config.selected_tab).draw()
       
 #endregion 
 
def bottom_window_flags():
    return ( PyImGui.WindowFlags.NoCollapse | 
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.HorizontalScrollbar |
            PyImGui.WindowFlags.NoResize |
            PyImGui.WindowFlags.NoScrollWithMouse
    )
    

def colored_button(label: str, button_color=0, hovered_color=0, active_color=0, width=0, height=0):
    clicked = False

    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, Utils.ColorToTuple(button_color))  # On color
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Utils.ColorToTuple(hovered_color))  # Hover color
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, Utils.ColorToTuple(active_color))

    clicked = PyImGui.button(label, width, height)

    PyImGui.pop_style_color(3)
    
    return clicked


def color_toggle_button(label:str, state:bool, button_color=0, hovered_color=0, active_color=0, width=0, height=0):
    clicked = False
        
    if state:
        #clicked = PyImGui.button(IconsFontAwesome5.ICON_CHECK_CIRCLE + f"##{label}", width, height)
        clicked = colored_button(IconsFontAwesome5.ICON_CHECK_CIRCLE + f"##{label}", active_color , active_color, active_color , width, height)
    else:
        #clicked = PyImGui.button(IconsFontAwesome5.ICON_CIRCLE + f"##{label}", width, height)
        clicked = colored_button(IconsFontAwesome5.ICON_CIRCLE + f"##{label}",button_color, active_color , active_color, width, height)
    return clicked
    
def eye_toggle_button(label:str, state:bool, button_color=0, hovered_color=0, active_color=0, width=0, height=0):
    clicked = False
        
    if state:
        #clicked = PyImGui.button(IconsFontAwesome5.ICON_CHECK_CIRCLE + f"##{label}", width, height)
        clicked = colored_button(IconsFontAwesome5.ICON_EYE_SLASH + f"##{label}", active_color , active_color, active_color , width, height)
    else:
        #clicked = PyImGui.button(IconsFontAwesome5.ICON_CIRCLE + f"##{label}", width, height)
        clicked = colored_button(IconsFontAwesome5.ICON_EYE + f"##{label}",button_color, active_color , active_color, width, height)
    return clicked

#region BottomWindows
def DrawColorizeBottomWindow():
    global global_vars

    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    flags=bottom_window_flags()
    
    PyImGui.set_next_window_pos(global_vars.inventory_frame_coords.left, global_vars.inventory_frame_coords.bottom)
    
    if global_vars.inventory_frame_coords.width > COMPACT_WIDTH:
        window_height = 45
    else:
        window_height = 60
    
    PyImGui.set_next_window_size(global_vars.inventory_frame_coords.width, window_height)
    
    if PyImGui.begin("Colorize##ColorizeWindow",True, flags):       
        if eye_toggle_button("ColorizeEyeBtn", global_vars.hide_ui,Utils.RGBToColor(75, 125, 125, 255),Utils.RGBToColor(125, 150, 150, 255),Utils.RGBToColor(125, 150, 150, 255)):
            global_vars.hide_ui = not global_vars.hide_ui
        if global_vars.hide_ui:
            ImGui.show_tooltip("Show UI")
        else:
            ImGui.show_tooltip("Hide UI")
            
        PyImGui.same_line(0,-1)
        PyImGui.text("|")
        PyImGui.same_line(0,-1)
             
        if not global_vars.hide_ui:
            if color_toggle_button("WhiteColorBtn",global_vars.colorize_config.colorize_whites, rarity_colors["White"]["frame"], rarity_colors["White"]["content"], rarity_colors["White"]["text"], 0, 0):
                global_vars.colorize_config.colorize_whites = not global_vars.colorize_config.colorize_whites
            ImGui.show_tooltip("Colorize Whites")   
            PyImGui.same_line(0,-1)
            if color_toggle_button("BlueColorBtn",global_vars.colorize_config.colorize_blues, rarity_colors["Blue"]["frame"], rarity_colors["Blue"]["content"], rarity_colors["Blue"]["text"], 0, 0):
                global_vars.colorize_config.colorize_blues = not global_vars.colorize_config.colorize_blues
            ImGui.show_tooltip("Colorize Blues")    
            PyImGui.same_line(0,-1)
            if color_toggle_button("PurpleColorBtn",global_vars.colorize_config.colorize_purples, rarity_colors["Purple"]["frame"], rarity_colors["Purple"]["content"], rarity_colors["Purple"]["text"], 0, 0):
                global_vars.colorize_config.colorize_purples = not global_vars.colorize_config.colorize_purples
            ImGui.show_tooltip("Colorize Purples")    
            PyImGui.same_line(0,-1)
            if color_toggle_button("GoldColorBtn", global_vars.colorize_config.colorize_golds, rarity_colors["Gold"]["frame"], rarity_colors["Gold"]["content"], rarity_colors["Gold"]["text"], 0, 0):
                global_vars.colorize_config.colorize_golds = not global_vars.colorize_config.colorize_golds
            PyImGui.same_line(0,-1)
            ImGui.show_tooltip("Colorize Golds")
            if color_toggle_button("GreenColorBtn", global_vars.colorize_config.colorize_greens, rarity_colors["Green"]["frame"], rarity_colors["Green"]["content"], rarity_colors["Green"]["text"], 0, 0):
                global_vars.colorize_config.colorize_greens = not global_vars.colorize_config.colorize_greens
            ImGui.show_tooltip("Colorize Greens")
    PyImGui.end()
    PyImGui.pop_style_var(1)
    
    
def DrawIdentifyBottomWindow():
    global global_vars

    def _set_option(state: bool):
        for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
            bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
            item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)

            for item_id in item_array:
                if GLOBAL_CACHE.Item.Usage.IsIdentified(item_id) or GLOBAL_CACHE.Item.Usage.IsIDKit(item_id):
                    continue
                # Ensure checkbox state exists (if it was removed earlier)
                if item_id not in global_vars.identification_checkbox_states:
                    global_vars.identification_checkbox_states[item_id] = False

                # Apply state based on selected filter
                if global_vars.id_selected_item == 0:
                    global_vars.identification_checkbox_states[item_id] = state
                elif global_vars.id_selected_item == 1 and GLOBAL_CACHE.Item.Rarity.IsWhite(item_id):
                    global_vars.identification_checkbox_states[item_id] = state
                elif global_vars.id_selected_item == 2 and GLOBAL_CACHE.Item.Rarity.IsBlue(item_id):
                    global_vars.identification_checkbox_states[item_id] = state
                elif global_vars.id_selected_item == 3 and GLOBAL_CACHE.Item.Rarity.IsPurple(item_id):
                    global_vars.identification_checkbox_states[item_id] = state
                elif global_vars.id_selected_item == 4 and GLOBAL_CACHE.Item.Rarity.IsGold(item_id):
                    global_vars.identification_checkbox_states[item_id] = state
                elif global_vars.id_selected_item == 5 and GLOBAL_CACHE.Item.Rarity.IsGreen(item_id):
                    global_vars.identification_checkbox_states[item_id] = state
                    
        # Remove checkbox states that are set to False
        for item_id in list(global_vars.identification_checkbox_states):
            if not global_vars.identification_checkbox_states[item_id]:
                del global_vars.identification_checkbox_states[item_id]

    def _get_total_id_uses():
        total_uses = 0
        for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
            bag_items = GLOBAL_CACHE.ItemArray.GetItemArray(GLOBAL_CACHE.ItemArray.CreateBagList(bag_id))
            for item_id in bag_items:
                if GLOBAL_CACHE.Item.Usage.IsIDKit(item_id):
                    total_uses += GLOBAL_CACHE.Item.Usage.GetUses(item_id)

        global_vars.total_id_uses = total_uses
        return total_uses
    
    def _get_uses_needed():
        return sum(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
               for item_id, checked in global_vars.identification_checkbox_states.items()
               if checked)


    
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    flags=bottom_window_flags()
    
    PyImGui.set_next_window_pos(global_vars.inventory_frame_coords.left, global_vars.inventory_frame_coords.bottom)
    
    if global_vars.inventory_frame_coords.width > COMPACT_WIDTH:
        window_height = 45
    else:
        window_height = 60
    
    PyImGui.set_next_window_size(global_vars.inventory_frame_coords.width, window_height)
    
    if PyImGui.begin("Identify##IdentifyWindow",True, flags):       
        select_item_list = ["All", "Whites", "Blues", "Purples", "Golds", "Greens"]
        PyImGui.push_item_width(100)
        global_vars.id_selected_item = PyImGui.combo("##IDCombo", global_vars.id_selected_item, select_item_list)
        PyImGui.pop_item_width()
        ImGui.show_tooltip(f"Select {select_item_list[global_vars.id_selected_item]}")
        PyImGui.same_line(0,-1)
        
        if PyImGui.button(IconsFontAwesome5.ICON_CHECK_SQUARE + "##selectidID", 0, 0):
            _set_option(True)
        ImGui.show_tooltip(f"Select {select_item_list[global_vars.id_selected_item]}")   
        PyImGui.same_line(0,-1)
        
        if PyImGui.button(IconsFontAwesome5.ICON_SQUARE + "##unselectID", 0, 0):
            _set_option(False)
        ImGui.show_tooltip(f"Clear {select_item_list[global_vars.id_selected_item]}")
        PyImGui.same_line(0,-1)
        PyImGui.text("|")
        PyImGui.same_line(0,-1)
        total_uses = _get_total_id_uses()
        enough_uses = total_uses - _get_uses_needed()
        if enough_uses>=0:
            PyImGui.text_colored(f"{total_uses} Uses", Utils.ColorToTuple(Utils.RGBToColor(25, 210, 0, 255)))
        else:
            PyImGui.text_colored(f"{total_uses} Uses", Utils.ColorToTuple(Utils.RGBToColor(210, 90, 0, 255)))

        if enough_uses<0:
            ImGui.show_tooltip(f"Need {abs(enough_uses)} more uses to ID all Items.")
        else:
            ImGui.show_tooltip(f"{enough_uses} uses left after IDing all Items.")

        PyImGui.same_line(0,-1)
        PyImGui.text("|")
        PyImGui.same_line(0,-1)
        if ActionQueueManager().IsEmpty("IDENTIFY"):
            if PyImGui.button(IconsFontAwesome5.ICON_QUESTION + " ID Selected##IDStart", 0, 0):
                global_vars.id_queue_reset_done = False
                IdentifyItems()
        else:
            if PyImGui.button("Cancel Operation"):
                global_vars.id_queue_reset_done = False
                ActionQueueManager().ResetQueue("IDENTIFY")
                global_vars.id_queue_reset_done = True
        
            
    PyImGui.end()
    PyImGui.pop_style_var(1)
    
def DrawSalvageBottomWindow():
    global global_vars

    def _set_option(state: bool):
        for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
            bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
            item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)

            for item_id in item_array:
                if not GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id):
                    continue
                
                if GLOBAL_CACHE.Item.Usage.IsSalvageKit(item_id):
                    continue
                
                if not (GLOBAL_CACHE.Item.Rarity.IsWhite(item_id) or GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)):
                    continue
                
                # Ensure checkbox state exists (if it was removed earlier)
                if item_id not in global_vars.salvage_checkbox_states:
                    global_vars.salvage_checkbox_states[item_id] = False

                # Apply state based on selected filter
                if global_vars.salv_selected_item == 0:
                    global_vars.salvage_checkbox_states[item_id] = state
                elif global_vars.salv_selected_item == 1 and GLOBAL_CACHE.Item.Rarity.IsWhite(item_id):
                    global_vars.salvage_checkbox_states[item_id] = state
                elif global_vars.salv_selected_item == 2 and GLOBAL_CACHE.Item.Rarity.IsBlue(item_id):
                    global_vars.salvage_checkbox_states[item_id] = state
                elif global_vars.salv_selected_item == 3 and GLOBAL_CACHE.Item.Rarity.IsPurple(item_id):
                    global_vars.salvage_checkbox_states[item_id] = state
                elif global_vars.salv_selected_item == 4 and GLOBAL_CACHE.Item.Rarity.IsGold(item_id):
                    global_vars.salvage_checkbox_states[item_id] = state
                elif global_vars.salv_selected_item == 5 and GLOBAL_CACHE.Item.Rarity.IsGreen(item_id):
                    global_vars.salvage_checkbox_states[item_id] = state
                    
        # Remove checkbox states that are set to False
        for item_id in list(global_vars.salvage_checkbox_states):
            if not global_vars.salvage_checkbox_states[item_id]:
                del global_vars.salvage_checkbox_states[item_id]

    def _get_total_salv_uses():
        total_uses = 0
        for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
            bag_items = GLOBAL_CACHE.ItemArray.GetItemArray(GLOBAL_CACHE.ItemArray.CreateBagList(bag_id))
            for item_id in bag_items:
                if GLOBAL_CACHE.Item.Usage.IsLesserKit(item_id):
                    total_uses += GLOBAL_CACHE.Item.Usage.GetUses(item_id)

        global_vars.total_salvage_uses = total_uses
        return total_uses
    
    def _get_uses_needed():
        return sum(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
               for item_id, checked in global_vars.salvage_checkbox_states.items()
               if checked)

    
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    flags=bottom_window_flags()
    
    PyImGui.set_next_window_pos(global_vars.inventory_frame_coords.left, global_vars.inventory_frame_coords.bottom)
    
    if global_vars.inventory_frame_coords.width > COMPACT_WIDTH:
        window_height = 45
    else:
        window_height = 60
    
    PyImGui.set_next_window_size(global_vars.inventory_frame_coords.width, window_height)
    
    if PyImGui.begin("Salvage##SalvageWindow",True, flags):       
        select_item_list = ["All", "Whites", "Blues", "Purples", "Golds", "Greens"]
        PyImGui.push_item_width(100)
        global_vars.salv_selected_item = PyImGui.combo("##IDCombo", global_vars.salv_selected_item, select_item_list)
        PyImGui.pop_item_width()
        ImGui.show_tooltip(f"Select {select_item_list[global_vars.salv_selected_item]}")
        PyImGui.same_line(0,-1)
        
        if PyImGui.button(IconsFontAwesome5.ICON_CHECK_SQUARE + "##selectidSalv", 0, 0):
            _set_option(True)
        ImGui.show_tooltip(f"Select {select_item_list[global_vars.salv_selected_item]}")   
        PyImGui.same_line(0,-1)
        
        if PyImGui.button(IconsFontAwesome5.ICON_SQUARE + "##unselectSalv", 0, 0):
            _set_option(False)
        ImGui.show_tooltip(f"Clear {select_item_list[global_vars.salv_selected_item]}")
        PyImGui.same_line(0,-1)
        PyImGui.text("|")
        PyImGui.same_line(0,-1)
        total_uses = _get_total_salv_uses()
        enough_uses = total_uses - _get_uses_needed()
        if enough_uses>=0:
            PyImGui.text_colored(f"{total_uses} Uses", Utils.ColorToTuple(Utils.RGBToColor(25, 210, 0, 255)))
        else:
            PyImGui.text_colored(f"{total_uses} Uses", Utils.ColorToTuple(Utils.RGBToColor(210, 90, 0, 255)))

        if enough_uses<0:
            ImGui.show_tooltip(f"Need {abs(enough_uses)} more uses to salvage all Items.")
        else:
            ImGui.show_tooltip(f"{enough_uses} uses left after salvaging all Items.")

        PyImGui.same_line(0,-1)
        PyImGui.text("|")
        PyImGui.same_line(0,-1)
        if ActionQueueManager().IsEmpty("SALVAGE"):
            if PyImGui.button(IconsFontAwesome5.ICON_RECYCLE + " Salvage Selected##salvageStart", 0, 0):
                global_vars.salv_queue_reset_done = False
                SalvageItems()
        else:
            if PyImGui.button("Cancel Operation"):
                global_vars.salv_queue_reset_done = False
                ActionQueueManager().ResetQueue("SALVAGE")
                global_vars.salv_queue_reset_done = True
        
            
    PyImGui.end()
    PyImGui.pop_style_var(1)
    
# endregion      
 
#region Colorize
def ColorizeInventoryBags():
    def _can_draw_item(rarity:str):
        global global_vars
        if rarity == "White":
            return global_vars.colorize_config.colorize_whites
        elif rarity == "Blue":
            return global_vars.colorize_config.colorize_blues
        elif rarity == "Green":
            return global_vars.colorize_config.colorize_greens
        elif rarity == "Purple":
            return global_vars.colorize_config.colorize_purples
        elif rarity == "Gold":
            return global_vars.colorize_config.colorize_golds
        else:
            return False
    
    def _get_parent_hash():
        global global_vars
        return global_vars.inventory_frame_hash
    
    def _get_offsets(bag_id:int, slot:int):
        return [0,0,0,bag_id-1,slot+2]

    for bag_id in range(Bags.Backpack, Bags.Bag2+1):
        bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            slot = GLOBAL_CACHE.Item.GetSlot(item_id)
            if not _can_draw_item(rarity):
                continue
            frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
            is_visible = UIManager.FrameExists(frame_id)
            if not is_visible:
                continue
            UIManager().DrawFrame(frame_id, rarity_colors[rarity]["content"])
            UIManager().DrawFrameOutline(frame_id, rarity_colors[rarity]["frame"])
            
def ColorizeVaultTabs():   
    def _can_draw_item(rarity:str):
        global global_vars
        if rarity == "White":
            return global_vars.colorize_config.colorize_whites
        elif rarity == "Blue":
            return global_vars.colorize_config.colorize_blues
        elif rarity == "Green":
            return global_vars.colorize_config.colorize_greens
        elif rarity == "Purple":
            return global_vars.colorize_config.colorize_purples
        elif rarity == "Gold":
            return global_vars.colorize_config.colorize_golds
        else:
            return False
     
    def _get_parent_hash():
        global global_vars
        return global_vars.xunlaivault_frame_hash
    
    def _get_offsets(bag_id:int, slot:int):        
        return [0,bag_id-8,slot+2]
    
    if not GLOBAL_CACHE.Inventory.IsStorageOpen():
        return

    for bag_id in range(Bags.Storage1, Bags.Storage14+1):
        bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            slot = GLOBAL_CACHE.Item.GetSlot(item_id)
            if not _can_draw_item(rarity):
                continue
            frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
            is_visible = UIManager.FrameExists(frame_id)
            if not is_visible:
                continue
            UIManager().DrawFrame(frame_id, rarity_colors[rarity]["content"])
            UIManager().DrawFrameOutline(frame_id, rarity_colors[rarity]["frame"])
            
#region Storage Module
def DrawInventoryBagsStorageMasks():    
    def _get_parent_hash():
        global global_vars
        return global_vars.inventory_frame_hash
    
    def _get_offsets(bag_id:int, slot:int):
        return [0,0,0,bag_id-1,slot+2]

    for bag_id in range(Bags.Backpack, Bags.Bag2+1):
        bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            slot = GLOBAL_CACHE.Item.GetSlot(item_id)

            frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
            is_visible = UIManager.FrameExists(frame_id)
            if not is_visible:
                continue
            UIManager().DrawFrame(frame_id, rarity_colors[rarity]["content"])
            UIManager().DrawFrameOutline(frame_id, rarity_colors[rarity]["frame"])
            
            left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
            if floating_button(
                    IconsFontAwesome5.ICON_CARET_SQUARE_RIGHT,  
                    item_id,
                    right -20, 
                    bottom-20,
                    Utils.ColorToTuple(rarity_colors[rarity]["frame"])
                ):
                GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
            
def DrawVaultStorageMasks():        
    def _get_parent_hash():
        global global_vars
        return global_vars.xunlaivault_frame_hash
    
    def _get_offsets(bag_id:int, slot:int):        
        return [0,bag_id-8,slot+2]
    
    if not GLOBAL_CACHE.Inventory.IsStorageOpen():
        return

    for bag_id in range(Bags.Storage1, Bags.Storage14+1):
        bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            slot = GLOBAL_CACHE.Item.GetSlot(item_id)

            frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
            is_visible = UIManager.FrameExists(frame_id)
            if not is_visible:
                continue
            UIManager().DrawFrame(frame_id, rarity_colors[rarity]["content"])
            UIManager().DrawFrameOutline(frame_id, rarity_colors[rarity]["frame"])
            left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
            if floating_button(
                    IconsFontAwesome5.ICON_CARET_SQUARE_LEFT,  
                    item_id,
                    right -20, 
                    bottom-20,
                    Utils.ColorToTuple(rarity_colors[rarity]["frame"])
                ):
                GLOBAL_CACHE.Inventory.WithdrawItemFromStorage(item_id)

#endregion
    
#region Identify        
def DrawIdentifyInventoryMasks():
    def _get_parent_hash():
        global global_vars
        return global_vars.inventory_frame_hash
    
    def _get_offsets(bag_id:int, slot:int):
        return [0,0,0,bag_id-1,slot+2]

    for bag_id in range(Bags.Backpack, Bags.Bag2+1):
        bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            slot = GLOBAL_CACHE.Item.GetSlot(item_id)

            frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
            is_visible = UIManager.FrameExists(frame_id)
            if not is_visible:
                continue
            
            color_content = rarity_colors[rarity]["content"]
            color_frame = rarity_colors[rarity]["frame"]
            
            if GLOBAL_CACHE.Item.Usage.IsIdentified(item_id) and not GLOBAL_CACHE.Item.Usage.IsIDKit(item_id):
                color_content = rarity_colors["Ignored"]["content"]
                color_frame = rarity_colors["Ignored"]["frame"]
            
            UIManager().DrawFrame(frame_id, color_content)
            UIManager().DrawFrameOutline(frame_id, color_frame)
            
            if not GLOBAL_CACHE.Item.Usage.IsIdentified(item_id) and not GLOBAL_CACHE.Item.Usage.IsIDKit(item_id):
                color_content = rarity_colors["Ignored"]["content"]
                color_frame = rarity_colors["Ignored"]["frame"]
                if item_id not in global_vars.identification_checkbox_states:
                    global_vars.identification_checkbox_states[item_id] = False
                
                left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
                global_vars.identification_checkbox_states[item_id] = floating_checkbox(
                    f"{item_id}", 
                    global_vars.identification_checkbox_states[item_id], 
                    right -20, 
                    bottom-20,
                    Utils.ColorToTuple(rarity_colors[rarity]["frame"])
                )
                          
            # Remove checkbox states that are set to False
            for item_id in list(global_vars.identification_checkbox_states):
                if not global_vars.identification_checkbox_states[item_id]:
                    del global_vars.identification_checkbox_states[item_id]

                    
            
def DrawIdentifyVaultMasks():        
    def _get_parent_hash():
        global global_vars
        return global_vars.xunlaivault_frame_hash
    
    def _get_offsets(bag_id:int, slot:int):        
        return [0,bag_id-8,slot+2]
    
    if not GLOBAL_CACHE.Inventory.IsStorageOpen():
        return

    for bag_id in range(Bags.Storage1, Bags.Storage14+1):
        bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            slot = GLOBAL_CACHE.Item.GetSlot(item_id)

            frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
            is_visible = UIManager.FrameExists(frame_id)
            if not is_visible:
                continue
            color_content = rarity_colors[rarity]["content"]
            color_frame = rarity_colors[rarity]["frame"]
            
            if GLOBAL_CACHE.Item.Usage.IsIdentified(item_id) and not GLOBAL_CACHE.Item.Usage.IsIDKit(item_id):
                color_content = rarity_colors["Ignored"]["content"]
                color_frame = rarity_colors["Ignored"]["frame"]
            
            UIManager().DrawFrame(frame_id, color_content)
            UIManager().DrawFrameOutline(frame_id, color_frame)
            
def DrawInventoryToStorageMasks():
    def _can_draw_item(rarity:str):
        global global_vars
        if rarity == "White":
            return global_vars.colorize_config.colorize_whites
        elif rarity == "Blue":
            return global_vars.colorize_config.colorize_blues
        elif rarity == "Green":
            return global_vars.colorize_config.colorize_greens
        elif rarity == "Purple":
            return global_vars.colorize_config.colorize_purples
        elif rarity == "Gold":
            return global_vars.colorize_config.colorize_golds
        else:
            return False
    
    def _get_parent_hash():
        global global_vars
        return global_vars.inventory_frame_hash
    
    def _get_offsets(bag_id:int, slot:int):
        return [0,0,0,bag_id-1,slot+2]

    for bag_id in range(Bags.Backpack, Bags.Bag2+1):
        bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            slot = GLOBAL_CACHE.Item.GetSlot(item_id)
            if not _can_draw_item(rarity):
                continue
            frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
            is_visible = UIManager.FrameExists(frame_id)
            if not is_visible:
                continue
            UIManager().DrawFrame(frame_id, rarity_colors[rarity]["content"])
            UIManager().DrawFrameOutline(frame_id, rarity_colors[rarity]["frame"])
#endregion
            
#region Salgave
def DrawSalvageInventoryMasks():
    def _get_parent_hash():
        global global_vars
        return global_vars.inventory_frame_hash
    
    def _get_offsets(bag_id:int, slot:int):
        return [0,0,0,bag_id-1,slot+2]

    for bag_id in range(Bags.Backpack, Bags.Bag2+1):
        bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            slot = GLOBAL_CACHE.Item.GetSlot(item_id)

            frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
            is_visible = UIManager.FrameExists(frame_id)
            if not is_visible:
                continue
            
            color_content = rarity_colors[rarity]["content"]
            color_frame = rarity_colors[rarity]["frame"]
            
            is_white =  rarity == "White"
            is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)
            is_salvageable = GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id)
            is_salvage_kit = GLOBAL_CACHE.Item.Usage.IsLesserKit(item_id)
            
            if not (((is_white and is_salvageable) or (is_identified and is_salvageable)) or is_salvage_kit):
                color_content = rarity_colors["Ignored"]["content"]
                color_frame = rarity_colors["Ignored"]["frame"]
            
            UIManager().DrawFrame(frame_id, color_content)
            UIManager().DrawFrameOutline(frame_id, color_frame)
            
            if (((is_white and is_salvageable) or (is_identified and is_salvageable)) and not is_salvage_kit):
                if item_id not in global_vars.salvage_checkbox_states:
                    global_vars.salvage_checkbox_states[item_id] = False
                
                left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
                global_vars.salvage_checkbox_states[item_id] = floating_checkbox(
                    f"{item_id}", 
                    global_vars.salvage_checkbox_states[item_id], 
                    right -20, 
                    bottom-20,
                    Utils.ColorToTuple(rarity_colors[rarity]["frame"])
                )
                          
            # Remove checkbox states that are set to False
            for item_id in list(global_vars.salvage_checkbox_states):
                if not global_vars.salvage_checkbox_states[item_id]:
                    del global_vars.salvage_checkbox_states[item_id]

def DrawSalvageVaultMasks():        
    def _get_parent_hash():
        global global_vars
        return global_vars.xunlaivault_frame_hash
    
    def _get_offsets(bag_id:int, slot:int):        
        return [0,bag_id-8,slot+2]
    
    if not GLOBAL_CACHE.Inventory.IsStorageOpen():
        return

    for bag_id in range(Bags.Storage1, Bags.Storage14+1):
        bag_to_check = GLOBAL_CACHE.ItemArray.CreateBagList(bag_id)
        item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            _,rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
            slot = GLOBAL_CACHE.Item.GetSlot(item_id)

            frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
            is_visible = UIManager.FrameExists(frame_id)
            if not is_visible:
                continue
            color_content = rarity_colors[rarity]["content"]
            color_frame = rarity_colors[rarity]["frame"]
            
            is_white =  rarity == "White"
            is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(item_id)
            is_salvageable = GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id)
            is_salvage_kit = GLOBAL_CACHE.Item.Usage.IsLesserKit(item_id)
            
            if not (((is_white and is_salvageable) or (is_identified and is_salvageable)) or is_salvage_kit):
                color_content = rarity_colors["Ignored"]["content"]
                color_frame = rarity_colors["Ignored"]["frame"]
            
            UIManager().DrawFrame(frame_id, color_content)
            UIManager().DrawFrameOutline(frame_id, color_frame)

#endregion
#region AtuoHandler

def show_model_id_dialog_popup():
    global widget_options
    
    if global_vars.auto_widget_options.show_dialog_popup:
        PyImGui.open_popup("ModelID Lookup")
        global_vars.auto_widget_options.show_dialog_popup = False  # trigger only once

    if PyImGui.begin_popup_modal("ModelID Lookup", True,PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text("ModelID Lookup")
        PyImGui.separator()

        # Input + filter mode
        global_vars.auto_widget_options.model_id_search = PyImGui.input_text("Search", global_vars.auto_widget_options.model_id_search)
        search_lower = global_vars.auto_widget_options.model_id_search.strip().lower()

        global_vars.auto_widget_options.model_id_search_mode = PyImGui.radio_button("Contains", global_vars.auto_widget_options.model_id_search_mode, 0)
        PyImGui.same_line(0, -1)
        global_vars.auto_widget_options.model_id_search_mode = PyImGui.radio_button("Starts With", global_vars.auto_widget_options.model_id_search_mode, 1)

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
                        if global_vars.auto_widget_options.model_id_search_mode == 0 and search_lower not in name_lower:
                            continue
                        if global_vars.auto_widget_options.model_id_search_mode == 1 and not name_lower.startswith(search_lower):
                            continue

                    label = f"{name} ({model_id})"
                    if PyImGui.selectable(label, False, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                        if model_id not in global_vars.auto_widget_options.salvage_blacklist:
                            global_vars.auto_widget_options.salvage_blacklist.append(model_id)
            PyImGui.end_child()

            # RIGHT: Blacklist
            PyImGui.table_next_column()
            if PyImGui.begin_child("BlacklistModelIDList", (295, 375), True, PyImGui.WindowFlags.NoFlag):
                # Create list of (name, model_id) and sort by name
                sorted_blacklist = sorted(
                    [(model_id_to_name.get(model_id, "Unknown"), model_id)
                    for model_id in global_vars.auto_widget_options.salvage_blacklist],
                    key=lambda x: x[0].lower()
                )

                for name, model_id in sorted_blacklist:
                    label = f"{name} ({model_id})"
                    if PyImGui.selectable(label, False, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                        global_vars.auto_widget_options.salvage_blacklist.remove(model_id)
            PyImGui.end_child()



            PyImGui.end_table()

        if PyImGui.button("Close"):
            PyImGui.close_current_popup()

        PyImGui.end_popup_modal()

def DrawAutoHandler():
    global global_vars
    
    content_frame = UIManager.GetChildFrameID(global_vars.inventory_frame_hash, [0])
    left, top, right, bottom = UIManager.GetFrameCoords(content_frame)
    y_offset = 2
    x_offset = 0
    height = bottom - top + y_offset
    width = right - left + x_offset
    if width < 100:
        width = 100
    if height < 100:
        height = 100
        
    UIManager().DrawFrame(content_frame, Utils.RGBToColor(0, 0, 0, 255))
    
    #flags= ImGui.PushTransparentWindow()
    
    flags = ( PyImGui.WindowFlags.NoCollapse | 
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoResize
    )
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    
    PyImGui.set_next_window_pos(left, top)
    PyImGui.set_next_window_size(width, height)
    
    if PyImGui.begin("Embedded AutoHandler",True, flags):
        if global_vars.auto_widget_options.module_active:
            active_button = IconsFontAwesome5.ICON_TOGGLE_ON
            active_tooltip = "AutoHandler is active"
        else:
            active_button = IconsFontAwesome5.ICON_TOGGLE_OFF
            active_tooltip = "AutoHandler is inactive"
            
        global_vars.auto_widget_options.module_active = ImGui.toggle_button(active_button + "##AutoHandlerActive", global_vars.auto_widget_options.module_active)
        ImGui.show_tooltip(active_tooltip)
        
        PyImGui.same_line(0,-1)
        PyImGui.text("|")
        PyImGui.same_line(0,-1)
        
        if PyImGui.button(IconsFontAwesome5.ICON_SAVE + "##autosalvsave"):
            global_vars.auto_widget_options.save_to_ini()
            ConsoleLog(MODULE_NAME, "Settings saved to Auto Inv.ini", Py4GW.Console.MessageType.Success)
        ImGui.show_tooltip("Save Settings")
        PyImGui.same_line(0,-1)
        if PyImGui.button(IconsFontAwesome5.ICON_SYNC + "##autosalvreload"):
            global_vars.auto_widget_options.load_from_ini(global_vars.auto_widget_options.ini)
            global_vars.auto_widget_options.lookup_throttle.SetThrottleTime(global_vars.auto_widget_options._LOOKUP_TIME)
            global_vars.auto_widget_options.lookup_throttle.Reset()
            ConsoleLog(MODULE_NAME, "Settings reloaded from Auto Inv.ini", Py4GW.Console.MessageType.Success)
        ImGui.show_tooltip("Reload Settings")
        
        PyImGui.separator()
        
        PyImGui.text("Lookup Time (ms):")
        PyImGui.same_line(0,-1)
        
        PyImGui.push_item_width(150)
        global_vars.auto_widget_options._LOOKUP_TIME = PyImGui.input_int("##lookup_time",  global_vars.auto_widget_options._LOOKUP_TIME)
        PyImGui.pop_item_width()
        ImGui.show_tooltip("Changes will take effect after the next lookup.")
        
        if not GLOBAL_CACHE.Map.IsExplorable():
            PyImGui.text("Auto Lookup only runs in explorable.")
        else:
            remaining = global_vars.auto_widget_options.lookup_throttle.GetTimeRemaining() / 1000  # convert ms to seconds
            PyImGui.text(f"Next Lookup in: {remaining:.1f} s")
        
        PyImGui.separator()
        
        if PyImGui.begin_tab_bar("AutoID&SalvageTabs"):
            if PyImGui.begin_tab_item("Identification"):
                if color_toggle_button("WhiteColorBtn",global_vars.auto_widget_options.id_whites, rarity_colors["White"]["frame"], rarity_colors["White"]["content"], rarity_colors["White"]["text"], 0, 0):
                    global_vars.auto_widget_options.id_whites = not global_vars.auto_widget_options.id_whites
                ImGui.show_tooltip("Identify White Items")
                PyImGui.same_line(0,-1)
                if color_toggle_button("BlueColorBtn",global_vars.auto_widget_options.id_blues, rarity_colors["Blue"]["frame"], rarity_colors["Blue"]["content"], rarity_colors["Blue"]["text"], 0, 0):
                    global_vars.auto_widget_options.id_blues = not global_vars.auto_widget_options.id_blues
                ImGui.show_tooltip("Identify Blue Items")
                PyImGui.same_line(0,-1)
                if color_toggle_button("PurpleColorBtn",global_vars.auto_widget_options.id_purples, rarity_colors["Purple"]["frame"], rarity_colors["Purple"]["content"], rarity_colors["Purple"]["text"], 0, 0):
                    global_vars.auto_widget_options.id_purples = not global_vars.auto_widget_options.id_purples
                ImGui.show_tooltip("Identify Purple Items")
                PyImGui.same_line(0,-1)
                if color_toggle_button("GoldColorBtn",global_vars.auto_widget_options.id_golds, rarity_colors["Gold"]["frame"], rarity_colors["Gold"]["content"], rarity_colors["Gold"]["text"], 0, 0):
                    global_vars.auto_widget_options.id_golds = not global_vars.auto_widget_options.id_golds
                ImGui.show_tooltip("Identify Gold Items")
                PyImGui.same_line(0,-1)
                if color_toggle_button("GreenColorBtn",global_vars.auto_widget_options.id_greens, rarity_colors["Green"]["frame"], rarity_colors["Green"]["content"], rarity_colors["Green"]["text"], 0, 0):
                    global_vars.auto_widget_options.id_greens = not global_vars.auto_widget_options.id_greens
                ImGui.show_tooltip("Identify Green Items")

                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Salvage"):
                if color_toggle_button("WhiteColorBtn",global_vars.auto_widget_options.salvage_whites, rarity_colors["White"]["frame"], rarity_colors["White"]["content"], rarity_colors["White"]["text"], 0, 0):
                    global_vars.auto_widget_options.salvage_whites = not global_vars.auto_widget_options.salvage_whites
                ImGui.show_tooltip("Salvage White Items")
                PyImGui.same_line(0,-1)
                global_vars.auto_widget_options.salvage_rare_materials = ImGui.toggle_button("Rare Mats##salvageRareMaterials", global_vars.auto_widget_options.salvage_rare_materials and global_vars.auto_widget_options.salvage_whites)
                ImGui.show_tooltip("Salvage Rare Materials")
                PyImGui.same_line(0,-1)
                if color_toggle_button("BlueColorBtn",global_vars.auto_widget_options.salvage_blues, rarity_colors["Blue"]["frame"], rarity_colors["Blue"]["content"], rarity_colors["Blue"]["text"], 0, 0):
                    global_vars.auto_widget_options.salvage_blues = not global_vars.auto_widget_options.salvage_blues
                ImGui.show_tooltip("Salvage Blue Items")
                PyImGui.same_line(0,-1)
                if color_toggle_button("PurpleColorBtn",global_vars.auto_widget_options.salvage_purples, rarity_colors["Purple"]["frame"], rarity_colors["Purple"]["content"], rarity_colors["Purple"]["text"], 0, 0):
                    global_vars.auto_widget_options.salvage_purples = not global_vars.auto_widget_options.salvage_purples
                ImGui.show_tooltip("Salvage Purple Items")
                PyImGui.same_line(0,-1)
                if color_toggle_button("GoldColorBtn",global_vars.auto_widget_options.salvage_golds, rarity_colors["Gold"]["frame"], rarity_colors["Gold"]["content"], rarity_colors["Gold"]["text"], 0, 0):
                    global_vars.auto_widget_options.salvage_golds = not global_vars.auto_widget_options.salvage_golds
                ImGui.show_tooltip("Salvage Gold Items")
                PyImGui.separator()
                
                if PyImGui.collapsing_header("Ignore Items"):
                    PyImGui.text(f"{len(global_vars.auto_widget_options.salvage_blacklist)} Blacklisted ModelIDs")

                    if PyImGui.button("Manage Ignore List"):
                        global_vars.auto_widget_options.show_dialog_popup = True

                        
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Deposit"):
                global_vars.auto_widget_options.deposit_materials = ImGui.toggle_button("Materials", global_vars.auto_widget_options.deposit_materials)
                ImGui.show_tooltip("Deposit Materials")
                PyImGui.same_line(0,-1)
                global_vars.auto_widget_options.deposit_trophies = ImGui.toggle_button("Trophies", global_vars.auto_widget_options.deposit_trophies)
                ImGui.show_tooltip("Deposit Trophies")
                PyImGui.same_line(0,-1)
                if color_toggle_button("DepositBlueColorBtn",global_vars.auto_widget_options.deposit_blues, rarity_colors["Blue"]["frame"], rarity_colors["Blue"]["content"], rarity_colors["Blue"]["text"], 0, 0):
                    global_vars.auto_widget_options.deposit_blues = not global_vars.auto_widget_options.deposit_blues
                ImGui.show_tooltip("Deposit Blue Items")
                PyImGui.same_line(0,-1)
                if color_toggle_button("DepositPurpleColorBtn",global_vars.auto_widget_options.deposit_purples, rarity_colors["Purple"]["frame"], rarity_colors["Purple"]["content"], rarity_colors["Purple"]["text"], 0, 0):
                    global_vars.auto_widget_options.deposit_purples = not global_vars.auto_widget_options.deposit_purples
                ImGui.show_tooltip("Deposit Purple Items")
                PyImGui.same_line(0,-1)
                if color_toggle_button("DepositGoldColorBtn",global_vars.auto_widget_options.deposit_golds, rarity_colors["Gold"]["frame"], rarity_colors["Gold"]["content"], rarity_colors["Gold"]["text"], 0, 0):
                    global_vars.auto_widget_options.deposit_golds = not global_vars.auto_widget_options.deposit_golds
                ImGui.show_tooltip("Deposit Gold Items")
                PyImGui.same_line(0,-1)
                if color_toggle_button("DepositGreenColorBtn",global_vars.auto_widget_options.deposit_greens, rarity_colors["Green"]["frame"], rarity_colors["Green"]["content"], rarity_colors["Green"]["text"], 0, 0):
                    global_vars.auto_widget_options.deposit_greens = not global_vars.auto_widget_options.deposit_greens
                ImGui.show_tooltip("Deposit Green Items")

                PyImGui.separator()
                PyImGui.text("Keep Gold:")
                PyImGui.same_line(0,-1)
                global_vars.auto_widget_options.keep_gold = PyImGui.input_int("##keep_gold", global_vars.auto_widget_options.keep_gold, 1, 1000, PyImGui.InputTextFlags.NoFlag)
                ImGui.show_tooltip("Keep Gold in inventory, deposit the rest")
                
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()
    PyImGui.end() 
    PyImGui.pop_style_var(1)
    
    show_model_id_dialog_popup()
    

def GetMainInventoryWindowCoords():
    global global_vars
    if global_vars.parent_frame_id != 0:
        global_vars.inventory_frame_coords = FrameCoords(global_vars.parent_frame_id)
        title_offset = 20
        frame_offset = 5
        global_vars.inventory_frame_coords.height = global_vars.inventory_frame_coords.bottom - global_vars.inventory_frame_coords.top - title_offset
        global_vars.inventory_frame_coords.width = global_vars.inventory_frame_coords.right - global_vars.inventory_frame_coords.left - frame_offset
    

def configure():
    pass

#region main
def main():
    global global_vars
    
    
    if not Routines.Checks.Map.MapValid():
        global_vars.auto_widget_options.lookup_throttle.Reset()
        global_vars.auto_widget_options.outpost_handled = False
        return
    
    if not global_vars.auto_widget_options.initialized:
        global_vars.auto_widget_options.load_from_ini(global_vars.auto_widget_options.ini)
        global_vars.auto_widget_options.lookup_throttle.SetThrottleTime(global_vars.auto_widget_options._LOOKUP_TIME)
        global_vars.auto_widget_options.lookup_throttle.Reset()
        global_vars.auto_widget_options.initialized = True
        ConsoleLog(MODULE_NAME, "Auto Widget Options initialized", Py4GW.Console.MessageType.Success)
        
    if not GLOBAL_CACHE.Map.IsExplorable():
        global_vars.auto_widget_options.lookup_throttle.Stop()
        global_vars.auto_widget_options.status = "Idle"
        if not global_vars.auto_widget_options.outpost_handled and global_vars.auto_widget_options.module_active:
            GLOBAL_CACHE.Coroutines.append(global_vars.auto_widget_options.IDSalvageDepositItems())
            global_vars.auto_widget_options.outpost_handled = True

    
    if global_vars.auto_widget_options.lookup_throttle.IsStopped():
            global_vars.auto_widget_options.lookup_throttle.Start()
            global_vars.auto_widget_options.status = "Idle"
 
        
    if global_vars.auto_widget_options.lookup_throttle.IsExpired():
        global_vars.auto_widget_options.lookup_throttle.SetThrottleTime(global_vars.auto_widget_options._LOOKUP_TIME)
        global_vars.auto_widget_options.lookup_throttle.Stop()
        if global_vars.auto_widget_options.status == "Idle" and global_vars.auto_widget_options.module_active:
            GLOBAL_CACHE.Coroutines.append(global_vars.auto_widget_options.IDAndSalvageItems())
        global_vars.auto_widget_options.lookup_throttle.Start()
        
          
    global_vars.process_game_throttle()
    
    if not global_vars.inventory_frame_exists:
        return
        
    GetMainInventoryWindowCoords()
    if not global_vars.hide_ui:
        DrawButtonStrip()           
        if (global_vars.config.colorize_vars == ColorizeType.colorize):
            ColorizeInventoryBags()
            ColorizeVaultTabs()
       
    if global_vars.config.selected_tab == TabType.colorize:
        DrawColorizeBottomWindow()
    elif global_vars.config.selected_tab == TabType.auto_handler:
        DrawAutoHandler()
    elif global_vars.config.selected_tab == TabType.identification:
        DrawIdentifyBottomWindow()
    elif global_vars.config.selected_tab == TabType.salvage:
        DrawSalvageBottomWindow()
    elif global_vars.config.selected_tab == TabType.xunlai_vault:
        if GLOBAL_CACHE.Map.IsOutpost():
            if not GLOBAL_CACHE.Inventory.IsStorageOpen():
                GLOBAL_CACHE.Inventory.OpenXunlaiWindow()
            else:
                DrawInventoryBagsStorageMasks()
                DrawVaultStorageMasks()
        else:
            global_vars.config.selected_tab = TabType.colorize

    if global_vars.config.colorize_vars == ColorizeType.identification:
        DrawIdentifyInventoryMasks()
            
    if global_vars.config.colorize_vars == ColorizeType.salvage:
        DrawSalvageInventoryMasks()      
      
 
    if ActionQueueManager().IsEmpty("IDENTIFY") and not global_vars.id_queue_reset_done:
        global_vars.id_queue_reset_done = True
        global_vars.identification_checkbox_states.clear()
        
    if ActionQueueManager().IsEmpty("SALVAGE") and not global_vars.salv_queue_reset_done:
        global_vars.salv_queue_reset_done = True
        global_vars.salvage_checkbox_states.clear()

#endregion    

if __name__ == "__main__":
    main()

