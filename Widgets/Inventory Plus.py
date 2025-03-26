from Py4GWCoreLib import *
from enum import Enum

module_name = "ID & Salvage"

MAX_BAGS = 4

class GlobalVarsClass:
    def __init__(self):
        self.inventory_frame_hash = 291586130
        self.xunlaivault_frame_hash = 2315448754
        self.parent_frame_id = 0
        self.total_id_uses = 0
        self.total_salvage_uses = 0
        self.identification_checkbox_states: Dict[int, bool] = {}
        self.salvage_checkbox_states: Dict[int, bool] = {}
        self.selected_item =0
        self.id_queue_reset_done = False
        self.salv_queue_reset_done = False

global_vars = GlobalVarsClass()
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

#region Types
#ColorizeType
class ColorizeType(Enum):
    colorize = 1
    identification = 2
    salvage = 3
    text_filter = 4
    
#TabType 
class TabType(Enum):
    hide = 0
    colorize = 1
    identification = 2
    salvage = 3
    search = 4
    xunlai_vault = 5
    mods = 6
    
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
#endregion

#region globals     
colorize_config = color_config()
xunlai_vault_config = xunlaivault_config()


widget_config = config()

window_module = ImGui.WindowModule(
    module_name, 
    window_name="ID & Salvage", 
    window_size=(300, 200),
    window_flags=PyImGui.WindowFlags.AlwaysAutoResize
)


#endregion

#region item config
class _item_properties:
    def __init__ (self,item_id):
        global global_vars
        self.item_id = item_id
        _, self.rarity = Item.Rarity.GetRarity(self.item_id)
        self.is_identified = Item.Usage.IsIdentified(self.item_id)
        self.is_salvageable = Item.Usage.IsSalvageable(self.item_id)
        self.is_id_kit = Item.Usage.IsIDKit(self.item_id)
        self.is_salv_kit = Item.Usage.IsLesserKit(self.item_id)
        if self.is_id_kit:
            global_vars.total_id_uses += Item.Usage.GetUses(self.item_id)
        if self.is_salv_kit:
            global_vars.total_salvage_uses += Item.Usage.GetUses(self.item_id)
          
class ItemConfig:
    global global_vars
    def __init__(self, bag_id, item_id):        
        self.item_id = item_id
        self.bag_id = bag_id
        self.slot = Item.GetSlot(self.item_id)
        self.frame_id = UIManager.GetChildFrameID(self.get_parent_hash(), self.get_offsets())
        self.is_visible = UIManager.FrameExists(self.frame_id)
        self.left,self.top, self.right, self.bottom = UIManager.GetFrameCoords(self.frame_id)
        self.item_properties = _item_properties(self.item_id)

    def get_parent_hash (self):
        global global_vars
        if self.bag_id > 0 and self.bag_id <= 4:
            return global_vars.inventory_frame_hash
        
        return global_vars.xunlaivault_frame_hash
            
        
    def get_offsets(self):
        if self.bag_id > 0 and self.bag_id <= 4:
            return [0,0,0,self.bag_id-1,self.slot+2]
        
        if self.bag_id == 6:
            return [0,14,self.slot+2]
        
        xunlai_tab = self.bag_id - 8
        
        return [0,xunlai_tab,self.slot+2]
    
    def can_draw(self):
        global colorize_config
        if not self.is_visible:
            return False
        if self.item_properties.rarity == "White" and not colorize_config.colorize_whites:
            return False
        if self.item_properties.rarity == "Blue" and not colorize_config.colorize_blues:
            return False
        if self.item_properties.rarity == "Green" and not colorize_config.colorize_greens:
            return False
        if self.item_properties.rarity == "Purple" and not colorize_config.colorize_purples:
            return False
        if self.item_properties.rarity == "Gold" and not colorize_config.colorize_golds:
            return False
        return True

    def draw_colorized(self, color_type=ColorizeType.colorize):
        if color_type== ColorizeType.colorize and self.can_draw():
            UIManager().DrawFrame(self.frame_id, rarity_colors[self.item_properties.rarity]["content"])
            UIManager().DrawFrameOutline(self.frame_id, rarity_colors[self.item_properties.rarity]["frame"])
            
    def draw_identification(self):
        global global_vars
        color_content = rarity_colors[self.item_properties.rarity]["content"]
        color_frame = rarity_colors[self.item_properties.rarity]["frame"]
        
        if self.item_properties.is_identified and not self.item_properties.is_id_kit:
            color_content = rarity_colors["Ignored"]["content"]
            color_frame = rarity_colors["Ignored"]["frame"]
            
        UIManager().DrawFrame(self.frame_id, color_content)
        UIManager().DrawFrameOutline(self.frame_id, color_frame)
        
        if self.bag_id > 0 and self.bag_id <= 4:
            #draw the checkbox
            if not self.item_properties.is_identified and not self.item_properties.is_id_kit:
                if self.item_id not in global_vars.identification_checkbox_states:
                    global_vars.identification_checkbox_states[self.item_id] = False  # Set default state

                global_vars.identification_checkbox_states[self.item_id] = floating_checkbox(
                    f"{self.item_id}", 
                    global_vars.identification_checkbox_states[self.item_id], 
                    self.right -20, 
                    self.bottom-20,
                    Utils.ColorToTuple(rarity_colors[self.item_properties.rarity]["frame"])
                )
            
    def draw_salvage(self):
        global global_vars
        color_content = rarity_colors[self.item_properties.rarity]["content"]
        color_frame = rarity_colors[self.item_properties.rarity]["frame"]
        
        is_salvageable = ((self.item_properties.rarity == "White" and self.item_properties.is_salvageable) or 
                         (self.item_properties.is_identified and self.item_properties.is_salvageable))
        
        if not (is_salvageable or self.item_properties.is_salv_kit):
            color_content = rarity_colors["Ignored"]["content"]
            color_frame = rarity_colors["Ignored"]["frame"]
            
        UIManager().DrawFrame(self.frame_id, color_content)
        UIManager().DrawFrameOutline(self.frame_id, color_frame)
        
        if self.bag_id > 0 and self.bag_id <= 4:
            #draw the checkbox
            if is_salvageable and not self.item_properties.is_salv_kit:
                if self.item_id not in global_vars.salvage_checkbox_states:
                    global_vars.salvage_checkbox_states[self.item_id] = False  # Set default state

                global_vars.salvage_checkbox_states[self.item_id] = floating_checkbox(
                    f"{self.item_id}", 
                    global_vars.salvage_checkbox_states[self.item_id], 
                    self.right -20, 
                    self.bottom-20,
                    Utils.ColorToTuple(rarity_colors[self.item_properties.rarity]["frame"])
                )

#endregion

#region ImGuiTemplates
def bottom_window_flags():
    return ( PyImGui.WindowFlags.NoCollapse | 
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoResize |
            PyImGui.WindowFlags.NoScrollWithMouse
    )
  
    
#endregion

#region inventory routines
def AutoID(item_id):
    global global_vars
    first_id_kit = Inventory.GetFirstIDKit()
    if first_id_kit == 0:
        return
    Inventory.IdentifyItem(item_id, first_id_kit)
    global_vars.total_id_uses -= 1
    
def IdentifyItems():
    global global_vars
    ActionQueueManager().ResetQueue("IDENTIFY")
    for item_id in global_vars.identification_checkbox_states:
        if global_vars.identification_checkbox_states[item_id]:
            ActionQueueManager().AddAction("IDENTIFY", AutoID, item_id)
            global_vars.identification_checkbox_states[item_id] = False

    for item_id in global_vars.identification_checkbox_states:
        global_vars.identification_checkbox_states[item_id] = False
            
def AutoSalvage(item_id):
    global global_vars
    first_salv_kit = Inventory.GetFirstSalvageKit()
    if first_salv_kit == 0:
        return
    Inventory.SalvageItem(item_id, first_salv_kit)
    global_vars.total_salvage_uses -= 1

def SalvageItems():
    global total_salvage_uses
    ActionQueueManager().ResetQueue("SALVAGE")
    for item_id in global_vars.salvage_checkbox_states:
        if global_vars.salvage_checkbox_states[item_id]:
            quantity = Item.Properties.GetQuantity(item_id)
            if global_vars.total_salvage_uses < quantity:
                quantity = global_vars.total_salvage_uses
            for _ in range(quantity):
                ActionQueueManager().AddAction("SALVAGE", AutoSalvage, item_id)
                ActionQueueManager().AddAction("SALVAGE",Inventory.AcceptSalvageMaterialsWindow)

            global_vars.salvage_checkbox_states[item_id] = False
    
    for item_id in global_vars.salvage_checkbox_states:
        global_vars.salvage_checkbox_states[item_id] = False
        
#endregion
    
#region colorize options
def DrawColorizeBottomWindow():
    global colorize_config, rarity_colors
    left, top, right, bottom = UIManager.GetFrameCoords(parent_frame_id)  
    title_offset = 20
    frame_offset = 5
    height = bottom - top - title_offset
    width = right - left - frame_offset

    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    flags=bottom_window_flags()
    
    PyImGui.set_next_window_pos(left, bottom)
    PyImGui.set_next_window_size(width, 40)
    
    if PyImGui.begin("Colorize##ColorizeWindow",True, flags):
    
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(rarity_colors["White"]["text"]))
        colorize_config.colorize_whites = PyImGui.checkbox("Whites", colorize_config.colorize_whites)
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(rarity_colors["Blue"]["text"]))
        colorize_config.colorize_blues = PyImGui.checkbox("Blues", colorize_config.colorize_blues)
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(rarity_colors["Purple"]["text"]))
        colorize_config.colorize_purples = PyImGui.checkbox("Purples", colorize_config.colorize_purples)
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(rarity_colors["Gold"]["text"]))
        colorize_config.colorize_golds = PyImGui.checkbox("Golds", colorize_config.colorize_golds)
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(rarity_colors["Green"]["text"]))
        colorize_config.colorize_greens = PyImGui.checkbox("Greens", colorize_config.colorize_greens)
        PyImGui.pop_style_color(4)
    PyImGui.end()
    PyImGui.pop_style_var(1)
    
# endregion

#region ID options
  

def DrawIDBottomWindow():
    global global_vars
    left, top, right, bottom = UIManager.GetFrameCoords(parent_frame_id)  
    title_offset = 20
    frame_offset = 5
    height = bottom - top - title_offset
    width = right - left - frame_offset

    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    flags=bottom_window_flags()
    
    PyImGui.set_next_window_pos(left, bottom)
    PyImGui.set_next_window_size(width, 40)
    
    if PyImGui.begin("Identify##IdentifyWindow",True, flags):
        select_item_list = ["All", "Whites", "Blues", "Purples", "Golds", "None"]
        PyImGui.push_item_width(100)
        global_vars.selected_item = PyImGui.combo("##IDCombo", global_vars.selected_item, select_item_list)
        PyImGui.pop_item_width()
        PyImGui.same_line(0,-1)
        if PyImGui.button(f"Select {select_item_list[global_vars.selected_item]}"):
            if global_vars.selected_item == 0:
                for item_id in global_vars.identification_checkbox_states:
                    global_vars.identification_checkbox_states[item_id] = True
            elif global_vars.selected_item == 1:
                for item_id in global_vars.identification_checkbox_states:
                    if item_id in global_vars.identification_checkbox_states:
                        if Item.Rarity.IsWhite(item_id):
                            global_vars.identification_checkbox_states[item_id] = True                 
            elif global_vars.selected_item == 2:
                for item_id in global_vars.identification_checkbox_states:
                    if item_id in global_vars.identification_checkbox_states:
                        if Item.Rarity.IsBlue(item_id):
                            global_vars.identification_checkbox_states[item_id] = True
            elif global_vars.selected_item == 3:
                for item_id in global_vars.identification_checkbox_states:
                    if item_id in global_vars.identification_checkbox_states:
                        if Item.Rarity.IsPurple(item_id):
                            global_vars.identification_checkbox_states[item_id] = True
            elif global_vars.selected_item == 4:
                for item_id in global_vars.identification_checkbox_states:
                    if item_id in global_vars.identification_checkbox_states:
                        if Item.Rarity.IsGold(item_id):
                            global_vars.identification_checkbox_states[item_id] = True                
            elif global_vars.selected_item == 5:
                for item_id in global_vars.identification_checkbox_states:
                    global_vars.identification_checkbox_states[item_id] = False

        PyImGui.same_line(0,-1)
        PyImGui.text(f"{global_vars.total_id_uses} ID uses remaining")
        PyImGui.same_line(0,-1)
        available_width= PyImGui.get_window_width()
    
        PyImGui.set_cursor_pos_x(available_width -100)
            
        id_queue = ActionQueueManager().GetQueue("IDENTIFY")
        if id_queue.is_empty():
            if PyImGui.button("ID Selected"):
                IdentifyItems()
        else:
            if PyImGui.button("Cancel Operation"):
                ResetInventoryEnvironment()

    
#endregion

#region Salv options
def DrawSalvBottomWindow():
    global global_vars
    left, top, right, bottom = UIManager.GetFrameCoords(parent_frame_id)  
    title_offset = 20
    frame_offset = 5
    height = bottom - top - title_offset
    width = right - left - frame_offset

    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    flags=bottom_window_flags()
    
    PyImGui.set_next_window_pos(left, bottom)
    PyImGui.set_next_window_size(width, 40)
    
    if PyImGui.begin("Salvage##SalvageWindow",True, flags):
        select_item_list = ["All", "Whites", "Blues", "Purples", "Golds", "None"]
        PyImGui.push_item_width(100)
        selected_item = PyImGui.combo("##SalvCombo", global_vars.selected_item, select_item_list)
        PyImGui.pop_item_width()
        PyImGui.same_line(0,-1)
        if PyImGui.button(f"Select {select_item_list[selected_item]}"):
            if selected_item == 0:
                for item_id in global_vars.salvage_checkbox_states:
                    global_vars.salvage_checkbox_states[item_id] = True
            elif selected_item == 1:
                for item_id in global_vars.salvage_checkbox_states:
                    if item_id in global_vars.salvage_checkbox_states:
                        if Item.Rarity.IsWhite(item_id):
                            global_vars.salvage_checkbox_states[item_id] = True                 
            elif selected_item == 2:
                for item_id in global_vars.salvage_checkbox_states:
                    if item_id in global_vars.salvage_checkbox_states:
                        if Item.Rarity.IsBlue(item_id):
                            global_vars.salvage_checkbox_states[item_id] = True
            elif selected_item == 3:
                for item_id in global_vars.salvage_checkbox_states:
                    if item_id in global_vars.salvage_checkbox_states:
                        if Item.Rarity.IsPurple(item_id):
                            global_vars.salvage_checkbox_states[item_id] = True
            elif selected_item == 4:
                for item_id in global_vars.salvage_checkbox_states:
                    if item_id in global_vars.salvage_checkbox_states:
                        if Item.Rarity.IsGold(item_id):
                            global_vars.salvage_checkbox_states[item_id] = True                
            elif selected_item == 5:
                for item_id in global_vars.salvage_checkbox_states:
                    global_vars.salvage_checkbox_states[item_id] = False

        PyImGui.same_line(0,-1)
        PyImGui.text(f"{global_vars.total_salvage_uses} Salvage uses remaining")
        PyImGui.same_line(0,-1)
        available_width= PyImGui.get_window_width()
                
        salv_queue = ActionQueueManager().GetQueue("IDENTIFY")
        if salv_queue.is_empty():
            if PyImGui.button("Salvage Selected"):
                SalvageItems()
        else:
            if PyImGui.button("Cancel Operation"):
                ResetInventoryEnvironment()
        
    PyImGui.end()
    PyImGui.pop_style_var(1)
    
#endregion


#region ResetInventoryEnvironment
def ResetInventoryEnvironment():
    global global_vars
    global widget_config

    
    global_vars.total_id_uses = 0
    global_vars.total_salvage_uses = 0
    
    global_vars.identification_checkbox_states.clear()
    global_vars.salvage_checkbox_states.clear()
    
#endregion

import math

RGBA = [255, 0, 0, 255]  # Start with red
_color_tick = 0

def advance_rainbow_color():
    global RGBA, _color_tick
    _color_tick += 1

    # Use sine waves offset from each other to create a rainbow pulse
    RGBA[0] = int((math.sin(_color_tick * 0.05) * 0.5 + 0.5) * 255)  # Red wave
    RGBA[1] = int((math.sin(_color_tick * 0.05 + 2.0) * 0.5 + 0.5) * 255)  # Green wave
    RGBA[2] = int((math.sin(_color_tick * 0.05 + 4.0) * 0.5 + 0.5) * 255)  # Blue wave



#region DrawWindow
def DrawWindow():
    global parent_frame_id, MAX_BAGS
    global colorize_config, rarity_colors
    global xunlai_vault_config
    global global_vars
    left, top, right, bottom = UIManager.GetFrameCoords(parent_frame_id)  
    title_offset = 20
    frame_offset = 5
    height = bottom - top - title_offset
    width = right - left - frame_offset
    
    window_title_x = left + 140
    window_title_y = top + 4
    
    advance_rainbow_color()
    r, g, b, a = RGBA[0]/255.0, RGBA[1]/255.0, RGBA[2]/255.0, RGBA[3]/255.0

    flags= ImGui.PushTransparentWindow()

    PyImGui.set_next_window_pos(left+10, top-23)
    PyImGui.set_next_window_size(0 if width > 275 else width, 23)
    if PyImGui.begin(window_module.window_name,True, flags):
        widget_config.colorize_vars = ColorizeType.colorize
        if PyImGui.begin_tab_bar("InventoryTabs"):
            ImGui.PopTransparentWindow()
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_EYE_SLASH + "##HideTab"):
                widget_config.selected_tab = TabType.hide
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Hide UI")
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (r, g, b, a))
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_PAINT_BRUSH + "##ColorizeTab"):
                widget_config.colorize_vars = ColorizeType.colorize
                widget_config.selected_tab = TabType.colorize
                PyImGui.end_tab_item()
            PyImGui.pop_style_color(1)
            ImGui.show_tooltip("Colorize")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_QUESTION +  "##IDTab"):
                widget_config.colorize_vars = ColorizeType.identification
                widget_config.selected_tab = TabType.identification
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Mass ID")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_RECYCLE + "##SalvageTab"):
                widget_config.colorize_vars = ColorizeType.salvage
                widget_config.selected_tab = TabType.salvage
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Mass Salvage")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_SEARCH + "##invsearchTab"):
                widget_config.colorize_vars = ColorizeType.colorize
                widget_config.selected_tab = TabType.search
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Filter")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_BOX_OPEN + "##XunlaiVaultTab"):
                widget_config.colorize_vars = ColorizeType.colorize
                widget_config.selected_tab = TabType.xunlai_vault
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Xunlai Vault")
            if PyImGui.begin_tab_item(IconsFontAwesome5.ICON_BALANCE_SCALE + "##merchantTab"):
                widget_config.colorize_vars = ColorizeType.colorize
                widget_config.selected_tab = TabType.mods
                PyImGui.end_tab_item()
            ImGui.show_tooltip("Merchant")
            PyImGui.end_tab_bar()
        else:
            ImGui.PopTransparentWindow()
    PyImGui.end()
    
    window_title = "- [Inventory+] "
    
    if widget_config.selected_tab == TabType.colorize:
        window_title = "- [Colorize]"
        DrawColorizeBottomWindow()

    if widget_config.selected_tab == TabType.identification:
        window_title = "- [Mass Identification]"
        DrawIDBottomWindow()
        
    if widget_config.selected_tab == TabType.salvage:
        window_title = "- [Mass Salvage]"
        DrawSalvBottomWindow()
        
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    flags= ImGui.PushTransparentWindow()
    
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding,0.0,0.0)
    PyImGui.set_next_window_pos(window_title_x, window_title_y)
    PyImGui.set_next_window_size(0, 15)
    if PyImGui.begin("##titleWindow",True, flags):
        PyImGui.text(window_title)
    PyImGui.end()
    PyImGui.pop_style_var(1)

    ImGui.PopTransparentWindow()
     
    if widget_config.selected_tab == TabType.hide:
        return   
    
    inventory_items : List[ItemConfig] = []
    global_vars.total_id_uses = 0
    global_vars.total_salvage_uses = 0
    
    #GetInventory items
    for bag_id in range(1, MAX_BAGS+1):
        bag_to_check = ItemArray.CreateBagList(bag_id)
        item_array = ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            inventory_items.append(ItemConfig(bag_id, item_id))
                    
    #get Xunlai Vault items
    for bag_id in range(8, 12 + 1):
        bag_to_check = ItemArray.CreateBagList(bag_id)
        item_array = ItemArray.GetItemArray(bag_to_check)
        for item_id in item_array:
            inventory_items.append(ItemConfig(bag_id, item_id))
     

    for item in inventory_items:
        if widget_config.colorize_vars == ColorizeType.colorize:
            item.draw_colorized()
        elif widget_config.colorize_vars == ColorizeType.identification:
            item.draw_identification()
        elif widget_config.colorize_vars == ColorizeType.salvage:
            item.draw_salvage()
 
 #endregion       
 

def configure():
    pass

#region main
def main():
    global parent_frame_id
    global widget_config
    global global_vars
    
    if Map.IsMapLoading():
        return
    
    if not (Map.IsMapReady() and Party.IsPartyLoaded()):
        return
    
    if widget_config.game_throttle_timer.HasElapsed(widget_config.game_throttle_time):
        parent_frame_id = UIManager.GetFrameIDByHash(global_vars.inventory_frame_hash)
        if parent_frame_id != 0:
            widget_config.inventory_window_exists = UIManager.FrameExists(parent_frame_id)                         
        else:
            widget_config.inventory_window_exists = False

        widget_config.game_throttle_timer.Reset()
        
    if not (widget_config.inventory_window_exists):
        ResetInventoryEnvironment()
        return
    
    if xunlai_vault_config.synch_vault_with_inventory and not Inventory.IsStorageOpen():
        Inventory.OpenXunlaiWindow()
        
    DrawWindow()

    
    ActionQueueManager().ProcessQueue("IDENTIFY")
    ActionQueueManager().ProcessQueue("SALVAGE")
    
    id_queue = ActionQueueManager().GetQueue("IDENTIFY")
    salv_queue = ActionQueueManager().GetQueue("SALVAGE")

    # IDENTIFY reset
    if id_queue.is_empty():
        if not global_vars.id_queue_reset_done:
            ResetInventoryEnvironment()
            global_vars.id_queue_reset_done = True
    else:
        global_vars.id_queue_reset_done = False

    # SALVAGE reset
    if salv_queue.is_empty():
        if not global_vars.salv_queue_reset_done:
            ResetInventoryEnvironment()
            global_vars.salv_queue_reset_done = True
    else:
        global_vars.salv_queue_reset_done = False
    
        
#endregion    

if __name__ == "__main__":
    main()

