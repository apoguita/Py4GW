import PyImGui

from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib import Color
from Py4GWCoreLib import ColorPalette
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import ImGui
import math

INVENTORY_FRAME_HASH = 291586130   
XUNLAI_VAULT_FRAME_HASH = 2315448754
MERCHANT_FRAME = 3613855137

#region TabIcon  
class TabIcon:
    def __init__(self, 
                    icon_name = "Unknown",
                    icon = IconsFontAwesome5.ICON_QUESTION_CIRCLE,
                    icon_color = Color(255, 255, 255, 255),
                    icon_tooltip = "Unknown",
                    rainbow_color = False):
        self.icon_name = icon_name
        self.icon = icon
        self.icon_color = icon_color
        self.icon_tooltip = icon_tooltip 
        self._color_tick = 0
        self.rainbow_color = rainbow_color
        
    def advance_rainbow_color(self):
        if not self.rainbow_color:
            return
        self._color_tick += 1
        # Use sine waves offset from each other to create a rainbow pulse
        r = int((math.sin(self._color_tick * 0.05) * 0.5 + 0.5) * 255)  # Red wave
        g = int((math.sin(self._color_tick * 0.05 + 2.0) * 0.5 + 0.5) * 255)  # Green wave
        b = int((math.sin(self._color_tick * 0.05 + 4.0) * 0.5 + 0.5) * 255)  # Blue wave
        self.icon_color = Color(r, g, b, 255)
    
    #endregion
    
#region Frame
class Frame:
    def __init__(self, frame_id):
        self.frame_id = frame_id
        if self.frame_id == 0:
            self.left = 0
            self.top = 0
            self.right = 0
            self.bottom = 0
            self.height = 0
            self.width = 0
        else:
            self.update_coords()
            
    def set_frame_id(self, frame_id):
        self.frame_id = frame_id
        if self.frame_id == 0:
            self.left = 0
            self.top = 0
            self.right = 0
            self.bottom = 0
            self.height = 0
            self.width = 0
        else:
            self.update_coords()
            
    def update_coords(self):
        self.left, self.top, self.right, self.bottom = UIManager.GetFrameCoords(self.frame_id) 
        self.height = self.bottom - self.top
        self.width = self.right - self.left   
        
    def draw_frame(self, color=Color(255, 255, 255, 255)):
        if self.frame_id == 0:
            return
        UIManager().DrawFrame(self.frame_id, color.to_color())
        
    def draw_frame_outline(self, color=Color(255, 255, 255, 255)):
        if self.frame_id == 0:
            return
        UIManager().DrawFrameOutline(self.frame_id, color.to_color())

#endregion

#region GameButton
def floating_game_button(caption, name, tooltip,  x, y, width = 18, height = 18 , color: Color = Color(255, 0, 0, 255)):
    PyImGui.set_next_window_pos(x, y)
    PyImGui.set_next_window_size(width, height)

    flags = (
        PyImGui.WindowFlags.NoCollapse |
        PyImGui.WindowFlags.NoTitleBar |
        PyImGui.WindowFlags.NoScrollbar |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.AlwaysAutoResize
    )

    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0, 0)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0.0)
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.ItemInnerSpacing, 0, 0)
    

    result = False
    if PyImGui.begin(f"{caption}##invisible_buttonwindow{name}", flags):
        col_normal = color.to_tuple_normalized()
        col_hovered = color.desaturate(0.50).to_tuple_normalized()
        col_active = color.desaturate(0.75).to_tuple_normalized()

        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, col_normal)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, col_hovered)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, col_active)

        result = PyImGui.button(caption)

        PyImGui.pop_style_color(3)
        ImGui.show_tooltip(tooltip)

    PyImGui.end()
    PyImGui.pop_style_var(4)  # 4 vars were pushed

    return result

def game_button(caption, name, tooltip, width = 18, height = 18 , color: Color = Color(255, 0, 0, 255)):
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0, 0)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0.0)
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.ItemInnerSpacing, 0, 0)

    result = False

    #color.set_a(255)
    col_normal = color.to_tuple_normalized()

    col_hovered = color.desaturate(0.50).to_tuple_normalized()
    col_active = color.desaturate(0.75).to_tuple_normalized()

    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, col_normal)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, col_hovered)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, col_active)

    result = PyImGui.button(caption + name, width, height)

    PyImGui.pop_style_color(3)
    ImGui.show_tooltip(tooltip)

    PyImGui.pop_style_var(4)  # 4 vars were pushed

    return result

def game_toggle_button(name, tooltip, state, width=18, height=18, color: Color = Color(255, 0, 0, 255)):
    if state:
        caption = IconsFontAwesome5.ICON_CHECK_CIRCLE
        clicked = game_button(caption, name, tooltip, width, height, color)
    else:
        caption = IconsFontAwesome5.ICON_CIRCLE
        _color = Color(color.r, color.g, color.b, 125)
        clicked = game_button(caption, name, tooltip, width, height, _color)
    return clicked
    

#endregion



def _get_parent_hash():
    return INVENTORY_FRAME_HASH

def _get_offsets(bag_id:int, slot:int):
    return [0,0,0,bag_id-1,slot+2]

def _get_frame_color(rarity:str):
    rarity_colors = {
        "White": ColorPalette.GetColor("GW_White"),
        "Blue": ColorPalette.GetColor("GW_Blue"),
        "Green": ColorPalette.GetColor("GW_Green"),
        "Purple": ColorPalette.GetColor("GW_Purple"),
        "Gold": ColorPalette.GetColor("GW_Gold"),
        "Disabled": ColorPalette.GetColor("GW_Disabled")
    }
    color =  rarity_colors.get(rarity, Color(255, 255, 255, 255))
    _color = Color(color.r, color.g, color.b, color.a)
    if rarity != "Disabled":
        _color.a = 25
    else:
        _color.a = 200
    return _color.to_color()
    
def _get_frame_outline_color(rarity:str):
    rarity_colors = {
        "White": ColorPalette.GetColor("GW_White"),
        "Blue": ColorPalette.GetColor("GW_Blue"),
        "Green": ColorPalette.GetColor("GW_Green"),
        "Purple": ColorPalette.GetColor("GW_Purple"),
        "Gold": ColorPalette.GetColor("GW_Gold"),
        "Disabled": ColorPalette.GetColor("GW_Disabled")
    }
    color =  rarity_colors.get(rarity, Color(255, 255, 255, 255))
    _color = Color(color.r, color.g, color.b, color.a)
    if rarity != "Disabled":
        _color.a = 125
    else:
        _color.a = 255
    return _color.to_color()

def _get_checkbox_color(rarity:str):
    rarity_colors = {
        "White": ColorPalette.GetColor("GW_White"),
        "Blue": ColorPalette.GetColor("GW_Blue"),
        "Green": ColorPalette.GetColor("GW_Green"),
        "Purple": ColorPalette.GetColor("GW_Purple"),
        "Gold": ColorPalette.GetColor("GW_Gold"),
        "Disabled": ColorPalette.GetColor("GW_Disabled")
    }
    color = rarity_colors.get(rarity, Color(255, 255, 255, 255))
    _color = Color(color.r, color.g, color.b, color.a)
    return _color

def _get_floating_button_color(rarity:str):
    rarity_colors = {
        "White": ColorPalette.GetColor("GW_White"),
        "Blue": ColorPalette.GetColor("GW_Blue"),
        "Green": ColorPalette.GetColor("GW_Green"),
        "Purple": ColorPalette.GetColor("GW_Purple"),
        "Gold": ColorPalette.GetColor("GW_Gold"),
        "Disabled": ColorPalette.GetColor("GW_Disabled")
    }
    color = rarity_colors.get(rarity, Color(255, 255, 255, 255))
    _color = Color(color.r, color.g, color.b, 150)
    return _color
    
