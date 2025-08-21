from enum import Enum
import math
from typing import Optional, overload
from unittest import case
import Py4GW

from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import Timer
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import SplitTexture
from Py4GWCoreLib import MapTexture
from Py4GWCoreLib import GameTextures
from Py4GWCoreLib import TextureState
from Py4GWCoreLib import Style
from Py4GWCoreLib import IconsFontAwesome5

import os
import time

from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, ThrottledTimer, Utils
module_name = "Style Manager"

'''
Roadmap for those interested in contributing:
- Adding theme selection for the recently pushed Themes ('Guild Wars', 'Minimalus', 'ImGUI') [COMPLETED]
- Expand to support styling so users can select colors and values for various elements
    > Add a export / import feature for styles
'''
script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))
ini_file_location = os.path.join(root_directory, "Widgets/Config/Style Manager.ini")
ini_handler = IniHandler(ini_file_location)


save_throttle_time = 1000
save_throttle_timer = Timer()
save_throttle_timer.Start()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

window_x = ini_handler.read_int(module_name +str(" Config"), "x", 100)
window_y = ini_handler.read_int(module_name +str(" Config"), "y", 100)

window_width = ini_handler.read_int(module_name +str(" Config"), "width", 600)
window_height = ini_handler.read_int(module_name +str(" Config"), "height", 500)

window_collapsed = ini_handler.read_bool(module_name +str(" Config"), "collapsed", False)

window_module = ImGui.WindowModule(
    module_name, 
    window_name="Style Manager", 
    window_size=(window_width, window_height),
    window_flags=PyImGui.WindowFlags.NoFlag,
    collapse=window_collapsed,
    can_close=False
)

window_module.window_pos = (window_x, window_y)
window_module.open = False

py4_gw_ini_handler = IniHandler("Py4GW.ini")
selected_theme = Style.StyleTheme[py4_gw_ini_handler.read_key("settings", "style_theme", Style.StyleTheme.ImGui.name)]
themes = [theme.name.replace("_", " ") for theme in Style.StyleTheme]

ImGui.reload_theme(Style.StyleTheme(selected_theme))
ImGui.set_theme(selected_theme)
# ImGui.Selected_Style : Style = ImGui.Styles.get(ImGui.Selected_Theme, Style())
org_style : Style = ImGui.Selected_Style.copy()

##TODO: Fix collapsing UIs that are not gw themed
##TODO: Remove style pushing on a window level 

mouse_down_timer = ThrottledTimer(125)
input_int_value = 150
input_float_value = 150.0
input_text_value = "Text"
search_value = ""

class preview_states:
    def __init__(self):
        self.input_int_value = 150
        self.input_float_value = 150.0
        self.input_text_value = "Text"
        self.search_value = ""
        self.combo = 0
        self.checkbox = True
        self.checkbox_2 = False
        self.slider_int = 25
        self.slider_float = 33.0

preview = preview_states()

def configure():
    window_module.open = True      

def undo_button(label, width : float = 0, height: float = 25) -> bool:
    clicked = False
    remaining_space = PyImGui.get_content_region_avail()
    width = remaining_space[0] if width <= 0 else width
    height = remaining_space[1] - 1 if height <= 0 else height

    match(ImGui.get_style().Theme):
        case Style.StyleTheme.Guild_Wars:
            ImGui.push_font("Regular", 9)
            x,y = PyImGui.get_cursor_screen_pos()
            display_label = label.split("##")[0]

            button_rect = (x, y, width, height)
            
            GameTextures.Button.value.draw_in_drawlist(
                button_rect[0], 
                button_rect[1],
                (button_rect[2], button_rect[3]),
                tint=(255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) else (200, 200, 200, 255),
            )
            
            text_size = PyImGui.calc_text_size(display_label)
            text_x = x + ((width - text_size[0] + 1) / 2)
            text_y = y + ((height - text_size[1] - 2) / 2)

            PyImGui.push_clip_rect(
                button_rect[0] + 1,
                button_rect[1] - 2,
                button_rect[2] - 2,
                button_rect[3] - 4,
                True
            )

            PyImGui.draw_list_add_text(
                text_x,
                text_y,
                Utils.RGBToColor(255, 255, 255, 255),
                display_label,
            )

            PyImGui.pop_clip_rect()

            PyImGui.set_cursor_screen_pos(x, y)
            clicked = PyImGui.invisible_button(label, width, height)
            ImGui.pop_font()

        case Style.StyleTheme.Minimalus:
            clicked = PyImGui.button(label, width, height)
        
        case Style.StyleTheme.ImGui:
            clicked = PyImGui.button(label, width, height)

    return clicked

@staticmethod
def begin_tab_item(label: str, popen: bool | None = None, flags:int = 0) -> bool:
    style = ImGui.get_style()

    if popen is None:
        match(style.Theme):
            case Style.StyleTheme.Guild_Wars:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Tab, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TabActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TabHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                open = PyImGui.begin_tab_item(label)
                PyImGui.pop_style_color(4)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0] + 12
                height = item_rect_max[1] - item_rect_min[1] + 3
                item_rect = (item_rect_min[0] - 4, item_rect_min[1], width, height)
                
                PyImGui.push_clip_rect(
                    item_rect[0],
                    item_rect[1],
                    width,
                    height,
                    True
                )
                
                (GameTextures.Tab_Active if open else GameTextures.Tab_Inactive).value.draw_in_drawlist(
                    item_rect[0] + 4,
                    item_rect[1] + 4,
                    (item_rect[2] - 8, item_rect[3] - 8),
                )
                
                PyImGui.pop_clip_rect()

                display_label = label.split("##")[0]
                text_size = PyImGui.calc_text_size(display_label)
                text_x = item_rect[0] + (item_rect[2] - text_size[0] + 2) / 2
                text_y = item_rect[1] + (item_rect[3] - text_size[1] + (5 if open else 7)) / 2

                PyImGui.push_clip_rect(
                    item_rect[0] + 6,
                    item_rect[1] + 2,
                    width - 12,
                    height - 4,
                    True
                )
                
                PyImGui.draw_list_add_text(
                    text_x,
                    text_y,
                    style.Text.color_int,
                    display_label,
                )

                PyImGui.pop_clip_rect()

                if open:
                    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 5, 0)
                    begin_child(f"{label}##_tab_item_content", (0, 0), True, PyImGui.WindowFlags.NoFlag | PyImGui.WindowFlags.NoBackground)
                    PyImGui.pop_style_var(1)
                
            case _:
                open = PyImGui.begin_tab_item(label)
        
    else:
        match(style.Theme):
            case Style.StyleTheme.Guild_Wars:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Tab, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TabActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TabHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                
                open = PyImGui.begin_tab_item(label, popen, flags)

                PyImGui.pop_style_color(4)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0]
                height = item_rect_max[1] - item_rect_min[1]
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                
                (GameTextures.Tab_Active if open else GameTextures.Tab_Inactive).value.draw_in_drawlist(
                    item_rect[0] + 4,
                    item_rect[1] + 4,
                    (item_rect[2] - 8, item_rect[3] - 8),
                )

                PyImGui.draw_list_add_text(
                    item_rect[0] + 4,
                    item_rect[1] + 4,
                    style.Text.color_int,
                    label,
                )

                if open:
                    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 5, 0)
                    begin_child(f"{label}##_tab_item_content", (0, 0), True, PyImGui.WindowFlags.NoFlag | PyImGui.WindowFlags.NoBackground)
                    PyImGui.pop_style_var(1)
            case _:
                open = PyImGui.begin_tab_item(label, popen, flags)

    return open

@staticmethod
def end_tab_item():
    style = ImGui.get_style()
    match(style.Theme):
        case Style.StyleTheme.Guild_Wars:
            end_child()
            PyImGui.end_tab_item()

        case _:
            PyImGui.end_tab_item()

@staticmethod
def begin_child(id : str, size : tuple[float, float] = (0, 0), border: bool = False, flags: int = PyImGui.WindowFlags.NoFlag) -> bool:
    style = ImGui.get_style()
    
    match(style.Theme):
        case Style.StyleTheme.Guild_Wars:
            
            ##get parent window size and screen rect
            parent_window_size = PyImGui.get_window_size()
            parent_window_pos = PyImGui.get_window_pos()
            window_rect = (parent_window_pos[0], parent_window_pos[1], parent_window_pos[0] + parent_window_size[0], parent_window_pos[1] + parent_window_size[1])

            # PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarBg, (0, 0, 0, 0))
            # PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarGrab, (0, 0, 0, 0))
            # PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarGrabActive, (0, 0, 0, 0))
            # PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarGrabHovered, (0, 0, 0, 0))
            open = PyImGui.begin_child(id, size, border, flags)
            # PyImGui.pop_style_color(4)
            
            has_vertical_scroll_bar = int(int(flags) & int(PyImGui.WindowFlags.AlwaysVerticalScrollbar)) != 0 or PyImGui.get_scroll_max_y() > 0
            has_horizontal_scroll_bar = int(int(flags) & int(PyImGui.WindowFlags.AlwaysHorizontalScrollbar)) != 0 or PyImGui.get_scroll_max_x() > 0

            vertical_window_rect = (
                parent_window_pos[0],
                parent_window_pos[1] + ((style.WindowPadding.value2 or 0) if border else 0),
                parent_window_pos[0] + parent_window_size[0] ,
                parent_window_pos[1] + parent_window_size[1] - ((style.WindowPadding.value2 or 0) if border else 0),
            )
            
            horizontal_window_rect = (
                parent_window_pos[0], 
                parent_window_pos[1],
                parent_window_pos[0] + parent_window_size[0] - (style.ScrollbarSize.value1 if has_vertical_scroll_bar else 0),
                parent_window_pos[1] + parent_window_size[1]
            )

            draw_vertical_scroll_bar(style.ScrollbarSize.value1, has_vertical_scroll_bar, vertical_window_rect)
            draw_horizontal_scroll_bar(style.ScrollbarSize.value1, has_horizontal_scroll_bar, horizontal_window_rect)

        case _:
            open = PyImGui.begin_child(id, size, border, flags)
            
    return open

@staticmethod
def end_child():
    PyImGui.end_child()

@staticmethod
def draw_vertical_scroll_bar(scroll_bar_size : float, force_scroll_bar : bool = False, window_rect: Optional[tuple[float, float, float, float]] = None):
    scroll_max_x = PyImGui.get_scroll_max_x()
    scroll_max_y = PyImGui.get_scroll_max_y()
    scroll_x = PyImGui.get_scroll_x()
    scroll_y = PyImGui.get_scroll_y()

    parent_window_size = PyImGui.get_window_size()
    parent_window_pos = PyImGui.get_window_pos()
    window_rect = window_rect or (parent_window_pos[0], parent_window_pos[1], parent_window_pos[0] + parent_window_size[0], parent_window_pos[1] + parent_window_size[1])
    
    if force_scroll_bar or scroll_max_y > 0:
        visible_size_y = PyImGui.get_window_height()
        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()

        window_clip = (
            window_rect[0],
            window_rect[1],
            window_rect[2] - window_rect[0],
            window_rect[3] - window_rect[1]
        )
        
        scroll_bar_rect = (item_rect_max[0] - scroll_bar_size, item_rect_min[1], item_rect_max[0], item_rect_min[1] + visible_size_y)

        track_height = visible_size_y
        thumb_min = 20.0  # example minimum thumb size, depends on ImGui style
        
        if scroll_max_y > 0:
            thumb_height = (visible_size_y * visible_size_y) / (visible_size_y + scroll_max_y)
            thumb_height = max(thumb_height, thumb_min)
        else:
            thumb_height = visible_size_y   # all content fits, thumb covers track
            
        # Thumb size (clamped)
        thumb_height = max(thumb_height, thumb_min)

        # Thumb offset
        thumb_offset = 0.0
        if scroll_max_y > 0:
            thumb_offset = (scroll_y / scroll_max_y) * (track_height - thumb_height)
            
        scroll_grab_rect = (scroll_bar_rect[0], scroll_bar_rect[1] + thumb_offset, scroll_bar_rect[2], scroll_bar_rect[1] + thumb_offset + thumb_height)
        
        PyImGui.push_clip_rect(
            window_clip[0],
            window_clip[1] - 5,
            window_clip[2],
            window_clip[3] + 10,
            False  # intersect with current clip rect (safe, window always bigger than content)
        )
            
        GameTextures.Scroll_Bg.value.draw_in_drawlist(
            scroll_bar_rect[0],
            scroll_bar_rect[1] + 5,
            (scroll_bar_rect[2] - scroll_bar_rect[0], scroll_bar_rect[3] - scroll_bar_rect[1] - 10),
        )

        GameTextures.ScrollGrab_Top.value.draw_in_drawlist(
            scroll_grab_rect[0], 
            scroll_grab_rect[1], 
            (scroll_bar_size, 7),
        )
        
        GameTextures.ScrollGrab_Bottom.value.draw_in_drawlist(
            scroll_grab_rect[0], 
            scroll_grab_rect[3] - 7, 
            (scroll_bar_size, 7),
        )

        px_height = 2
        mid_height = scroll_grab_rect[3] - scroll_grab_rect[1] - 10
        for i in range(math.ceil(mid_height / px_height)):
            GameTextures.ScrollGrab_Middle.value.draw_in_drawlist(
                scroll_grab_rect[0], 
                scroll_grab_rect[1] + 5 + (px_height * i), 
                (scroll_bar_size, px_height),
            tint=(195, 195, 195, 255)
            )
        
        GameTextures.UpButton.value.draw_in_drawlist(
            scroll_bar_rect[0] - 1,
            scroll_bar_rect[1] - 5,
            (scroll_bar_size, scroll_bar_size),
        )

        GameTextures.DownButton.value.draw_in_drawlist(
            scroll_bar_rect[0] - 1,
            scroll_bar_rect[3] - (scroll_bar_size - 5),
            (scroll_bar_size, scroll_bar_size),
        )
            
        PyImGui.pop_clip_rect()
        # ConsoleLog(module_name, f"{id} Scroll Values: X={scroll_x}, Y={scroll_y}, MaxX={scroll_max_x}, MaxY={scroll_max_y}")
        # ConsoleLog(module_name, f"Draw ScrollRegion {scroll_bar_rect}")

class GameTextures2(Enum): 
    RightButton = MapTexture(
        texture = os.path.join("Textures\\Game UI\\", "ui_left_right.png"),
        texture_size=(64, 16),
        size=(14, 16),
        normal=(1, 0)
    )
    
    LeftButton = MapTexture(
        texture = os.path.join("Textures\\Game UI\\", "ui_left_right.png"),
        texture_size=(64, 16),
        size=(14, 16),
        normal = (17, 0),
        active = (49, 0),
    )
    
    Horizontal_ScrollGrab_Top = MapTexture(
        texture = os.path.join("Textures\\Game UI\\", "ui_horizontal_scrollgrab.png"),
        texture_size=(16, 16),
        size=(7, 16),
        normal=(0, 0),
    )
    
    Horizontal_ScrollGrab_Middle = MapTexture(
        texture = os.path.join("Textures\\Game UI\\", "ui_horizontal_scrollgrab.png"),
        texture_size=(16, 16),
        size=(2, 16),
        normal=(7, 0)
    )

    Horizontal_ScrollGrab_Bottom = MapTexture(
        texture = os.path.join("Textures\\Game UI\\", "ui_horizontal_scrollgrab.png"),
        texture_size=(16, 16),
        size=(7, 16),
        normal=(9, 0),   
    )   
    
    Horizontal_Scroll_Bg = MapTexture(
        texture = os.path.join("Textures\\Game UI\\", "ui_horizontal_scroll_background.png"),
        texture_size=(16, 16),
        size=(16, 16),
        normal=(0, 0)
    )                         

@staticmethod
def draw_horizontal_scroll_bar(scroll_bar_size: float, force_scroll_bar: bool = False, window_rect: Optional[tuple[float, float, float, float]] = None):
    scroll_max_x = PyImGui.get_scroll_max_x()
    scroll_max_y = PyImGui.get_scroll_max_y()
    scroll_x = PyImGui.get_scroll_x()
    scroll_y = PyImGui.get_scroll_y()

    parent_window_size = PyImGui.get_window_size()
    parent_window_pos = PyImGui.get_window_pos()
    window_rect = window_rect or (parent_window_pos[0], parent_window_pos[1], parent_window_pos[0] + parent_window_size[0], parent_window_pos[1] + parent_window_size[1])
    
    if force_scroll_bar or scroll_max_x > 0:
        visible_size_x = PyImGui.get_window_width()
        visible_size_y = PyImGui.get_window_height()
        
        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()

        window_clip = (
            window_rect[0],
            window_rect[1],
            window_rect[2] - window_rect[0],
            window_rect[3] - window_rect[1]
        )
        
        scroll_bar_rect = (
            item_rect_min[0], 
            item_rect_min[1] + visible_size_y - scroll_bar_size,
            item_rect_min[0] + visible_size_x - (scroll_bar_size + 2 if scroll_max_y > 0 else 0), 
            item_rect_min[1] + visible_size_y
            )

        track_width = scroll_bar_rect[2] - scroll_bar_rect[0]
        thumb_min = 20.0
        
        if scroll_max_x > 0:
            thumb_width = (visible_size_x * visible_size_x) / (visible_size_x + scroll_max_x)
            thumb_width = max(thumb_width, thumb_min)
        else:
            thumb_width = visible_size_x   # all content fits, thumb covers track
            
        # Thumb size (clamped)
        thumb_width = max(thumb_width, thumb_min)
        
        # Thumb offset
        thumb_offset = 0
        if scroll_max_x > 0:
            thumb_offset = (scroll_x / scroll_max_x) * (track_width - thumb_width)

        scroll_grab_rect = (
            scroll_bar_rect[0] + thumb_offset,
            scroll_bar_rect[1],
            thumb_width,
            scroll_bar_size,
        )

        PyImGui.push_clip_rect(
            window_clip[0] - 5,
            window_clip[1] - 5,
            window_clip[2],
            window_clip[3] + 10,
            False  # intersect with current clip rect (safe, window always bigger than content)
        )
        
        scroll_bar_rect = (
            item_rect_min[0] + 5, 
            item_rect_min[1] + visible_size_y - scroll_bar_size,
            item_rect_min[0] + visible_size_x - 10 - (scroll_bar_size + 2 if scroll_max_y > 0 else 0), 
            item_rect_min[1] + visible_size_y
            )
            
        GameTextures2.Horizontal_Scroll_Bg.value.draw_in_drawlist(
            scroll_bar_rect[0] + 3,
            scroll_bar_rect[1],
            (scroll_bar_rect[2] - scroll_bar_rect[0] - 5, scroll_bar_rect[3] - scroll_bar_rect[1]),
        )
        
        
        GameTextures2.Horizontal_ScrollGrab_Middle.value.draw_in_drawlist(
            scroll_grab_rect[0] + 5, 
            scroll_grab_rect[1],
            (scroll_grab_rect[2] - 10, scroll_grab_rect[3]),
            tint=(195, 195, 195, 255)
        )
        
        GameTextures2.Horizontal_ScrollGrab_Top.value.draw_in_drawlist(
            scroll_grab_rect[0], 
            scroll_grab_rect[1], 
            (7, scroll_grab_rect[3]),
        )
        
        GameTextures2.Horizontal_ScrollGrab_Bottom.value.draw_in_drawlist(
            scroll_grab_rect[0] + scroll_grab_rect[2] - 7, 
            scroll_grab_rect[1], 
            (7, scroll_grab_rect[3]),
        )

        
        GameTextures2.LeftButton.value.draw_in_drawlist(
            scroll_bar_rect[0] - 5, 
            scroll_bar_rect[1] - 1, 
            (scroll_bar_size, scroll_bar_size + 1),
        )

        
        GameTextures2.RightButton.value.draw_in_drawlist(
            scroll_bar_rect[2] - 5, 
            scroll_bar_rect[1] - 1, 
            (scroll_bar_size, scroll_bar_size + 1),
        )

        PyImGui.pop_clip_rect()

@staticmethod
def begin_table(id: str, columns: int, flags: int = PyImGui.TableFlags.NoFlag, width: float = 0, height: float = 0) -> bool:
    style = ImGui.get_style()
    
    match(style.Theme):
        case Style.StyleTheme.Guild_Wars:
            
            x,y = PyImGui.get_cursor_screen_pos()
            # PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarBg, (0, 0, 0, 0))
            # PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarGrab, (0, 0, 0, 0))
            # PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarGrabActive, (0, 0, 0, 0))
            # PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarGrabHovered, (0, 0, 0, 0))
            opened = PyImGui.begin_table(id, columns, flags, width, height)
            # PyImGui.pop_style_color(1)
                    
            scroll_bar_size = style.ScrollbarSize.value1
            draw_vertical_scroll_bar(scroll_bar_size)
            draw_horizontal_scroll_bar(scroll_bar_size)            

        case _:
            opened = PyImGui.begin_table(id, columns, flags, width, height)

    
    return opened

@staticmethod
def end_table():
    PyImGui.end_table()
    

def DrawWindow():
    global window_module, module_name, ini_handler, window_x, window_y, window_collapsed, window_open, org_style, window_width, window_height
    global game_throttle_time, game_throttle_timer, save_throttle_time, save_throttle_timer
    
    try:                        
        if not window_module.open:
            return
                
        if window_module.begin():
            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
            ImGui.text("Selected Theme")
            PyImGui.same_line(0, 5)
            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
            remaining = PyImGui.get_content_region_avail()
            PyImGui.push_item_width(remaining[0])
            value = ImGui.combo("##theme_selector", ImGui.Selected_Style.Theme.value, themes)
            
            if value != ImGui.Selected_Style.Theme.value:
                theme = Style.StyleTheme(value)
                ImGui.reload_theme(theme)
                ImGui.set_theme(theme)
                
                org_style = ImGui.Selected_Style.copy()
                py4_gw_ini_handler.write_key("settings", "style_theme", ImGui.Selected_Style.Theme.name)
                
                
            PyImGui.spacing()
            ImGui.separator()
            PyImGui.spacing()
            any_changed = False

            if ImGui.begin_tab_bar("Style Customization"):
                if begin_tab_item("Styling"):
                    begin_child("Style Customization")
                    
                    
                    if ImGui.Selected_Style:
                        remaining = PyImGui.get_content_region_avail()
                        button_width = (remaining[0] - 10) / 2
                        
                        any_changed = any(var != org_style.StyleVars[enum] for enum, var in ImGui.Selected_Style.StyleVars.items())
                        any_changed |= any(col != org_style.Colors[enum] for enum, col in ImGui.Selected_Style.Colors.items())
                        any_changed |= any(col != org_style.CustomColors[enum] for enum, col in ImGui.Selected_Style.CustomColors.items())
                        
                        if ImGui.button("Save Changes", button_width, active=any_changed):
                            ImGui.Selected_Style.save_to_json()
                            org_style = ImGui.Selected_Style.copy()
                        
                        PyImGui.same_line(0, 5)

                        if ImGui.button("Reset to Default", button_width, active=any_changed):
                            theme = ImGui.Selected_Style.Theme
                            ImGui.Selected_Style.delete()
                            ImGui.reload_theme(theme)
                            org_style = ImGui.Selected_Style.copy()

                        ImGui.show_tooltip("Delete the current style and replace it with the default style for the theme.")

                        PyImGui.spacing()

                        if PyImGui.is_rect_visible(50, 50):
                            column_width = 0
                            item_width = 0

                            if begin_table("Style Variables", 3, PyImGui.TableFlags.ScrollY):
                                PyImGui.table_setup_column("Variable", PyImGui.TableColumnFlags.WidthFixed, 150)
                                PyImGui.table_setup_column("Value", PyImGui.TableColumnFlags.WidthStretch)
                                PyImGui.table_setup_column("Undo", PyImGui.TableColumnFlags.WidthFixed, 35)

                                PyImGui.table_next_row()
                                PyImGui.table_next_column()
                                    
                                for enum, var in ImGui.Selected_Style.StyleVars.items():
                                    PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
                                    ImGui.text(f"{enum}")
                                    PyImGui.table_next_column()

                                    column_width = column_width or PyImGui.get_content_region_avail()[0]
                                    item_width = item_width or (column_width - 5) / 2
                                    PyImGui.push_item_width(item_width)
                                    var.value1 = ImGui.input_float(f"##{enum}_value1", var.value1)
                                    
                                    if var.value2 is not None:
                                        PyImGui.same_line(0, 5)
                                        
                                        PyImGui.push_item_width(item_width)
                                        var.value2 = ImGui.input_float(f"##{enum}_value2", var.value2)
                                        
                                    PyImGui.table_next_column()

                                    changed = org_style.StyleVars[enum].value1 != var.value1 or org_style.StyleVars[enum].value2 != var.value2

                                    if changed:
                                        if undo_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                            var.value1 = org_style.StyleVars[enum].value1
                                            var.value2 = org_style.StyleVars[enum].value2

                                    PyImGui.table_next_column()
                                    
                                for enum, col in ImGui.Selected_Style.Colors.items():
                                    PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
                                    ImGui.text(f"{enum}")
                                    PyImGui.table_next_column()

                                    column_width = column_width or PyImGui.get_content_region_avail()[0]

                                    PyImGui.push_item_width(column_width)
                                    color_tuple = ImGui.color_edit4(f"##{enum}_color", col.color_tuple)
                                    if color_tuple != col.color_tuple:
                                        col.set_tuple_color(color_tuple)    
                                        
                                    PyImGui.table_next_column()

                                    changed = col.color_int != org_style.Colors[enum].color_int

                                    if changed:
                                        if undo_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                            col.color_tuple = org_style.Colors[enum].color_tuple
                                    
                                    PyImGui.table_next_column()

                                for enum, col in ImGui.Selected_Style.CustomColors.items():
                                    PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
                                    ImGui.text(f"{enum}")
                                    PyImGui.table_next_column()

                                    column_width = column_width or PyImGui.get_content_region_avail()[0]

                                    PyImGui.push_item_width(column_width)
                                    color_tuple = ImGui.color_edit4(f"##{enum}_color", col.color_tuple)
                                    if color_tuple != col.color_tuple:
                                        col.set_tuple_color(color_tuple)    
                                        
                                    PyImGui.table_next_column()

                                    changed = col.color_int != org_style.CustomColors[enum].color_int

                                    if changed:
                                        if undo_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                            col.color_tuple = org_style.CustomColors[enum].color_tuple
                                    PyImGui.table_next_column()

                                end_table()

                    end_child()
                    end_tab_item()

                if ImGui.begin_tab_item("Test Preview"):
                    ImGui.end_tab_item()       
                    
                if ImGui.begin_tab_item("Control Preview"):
                    if PyImGui.is_rect_visible(50, 50):
                        column_width = 0
                        item_width = 0

                        PyImGui.push_item_width(150)
                        if begin_table("Control Preview", 2, PyImGui.TableFlags.ScrollX):
                            PyImGui.table_setup_column("Control", PyImGui.TableColumnFlags.WidthFixed, 150)
                            PyImGui.table_setup_column("Preview", PyImGui.TableColumnFlags.WidthStretch)
                            
                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            
                            ImGui.text("Button")
                            PyImGui.table_next_column()
                            if ImGui.button("Button", 0, 25):
                                ConsoleLog(module_name, "Button clicked")
                            PyImGui.same_line(0,5)
                            ImGui.button("Disabled Button", 0, 25, False)
                            PyImGui.table_next_column()
                            
                            ImGui.text("Primary Button")
                            PyImGui.table_next_column()
                            if ImGui.primary_button("Primary Button", 0, 25):
                                ConsoleLog(module_name, "Primary Button clicked")
                            PyImGui.same_line(0,5)
                            ImGui.primary_button("Disabled Primary Button", 0, 25, False)
                            PyImGui.table_next_column()
                            
                            ImGui.text("Combo")
                            PyImGui.table_next_column()
                            preview.combo = ImGui.combo("Combo", preview.combo, ["Option 1", "Option 2", "Option 3"])
                            PyImGui.table_next_column()
                            
                            ImGui.text("Checkbox")
                            PyImGui.table_next_column()
                            preview.checkbox_2 = ImGui.checkbox("##Checkbox 2", preview.checkbox_2)                                
                            PyImGui.same_line(0, 5)
                            preview.checkbox = ImGui.checkbox("Checkbox", preview.checkbox)                                
                            PyImGui.table_next_column()

                            ImGui.text("Slider")
                            PyImGui.table_next_column()
                            preview.slider_int = ImGui.slider_int("Slider Int", preview.slider_int, 0, 100)
                            preview.slider_float = ImGui.slider_float("Slider Float", preview.slider_float, 0.0, 100.0)
                            PyImGui.table_next_column()
                            
                            ImGui.text("Input")
                            PyImGui.table_next_column()
                            preview.input_text_value = ImGui.input_text("Input Text", preview.input_text_value)
                            preview.input_int_value = ImGui.input_int("Input Int##2", preview.input_int_value)
                            preview.input_int_value = ImGui.input_int("Input Int##3", preview.input_int_value, 0, 10000, 0)
                            preview.input_float_value = ImGui.input_float("Input Float", preview.input_float_value)

                            PyImGui.table_next_column()

                            ImGui.text("Search")
                            PyImGui.table_next_column()
                            changed, preview.search_value = ImGui.search_field("Search Field", preview.search_value, "Search...")
                            PyImGui.table_next_column()

                            ImGui.text("Separator")
                            PyImGui.table_next_column()
                            ImGui.separator()
                            PyImGui.table_next_column()
                            
                            ImGui.text("Progress Bar")
                            PyImGui.table_next_column()
                            
                            current_style = ImGui.get_style()
                            ImGui.progress_bar(0.25, 0, 20, "25 points")
                                                      
                            current_style.PlotHistogram.push_color((219, 150, 251, 255))  
                            ImGui.progress_bar(0.25, 0, 20, "25 points")
                            current_style.PlotHistogram.pop_color()                            
                            PyImGui.table_next_column()
                            
                            ImGui.text("Hyperlink")
                            PyImGui.table_next_column()
                            if ImGui.hyperlink("Click Me"):
                                ConsoleLog(module_name, "Hyperlink clicked")
                            PyImGui.table_next_column()

                            ImGui.text("Bullet Text")
                            PyImGui.table_next_column()
                            ImGui.bullet_text("Bullet Text 1")
                            ImGui.bullet_text("Bullet Text 2")
                            PyImGui.table_next_column()

                            ImGui.text("Collapsing Header")
                            PyImGui.table_next_column()
                            if ImGui.collapsing_header("Collapsing Header", 0):
                                ImGui.text("This is a collapsible header content.")
                            PyImGui.table_next_column()

                            ImGui.text("Child")
                            PyImGui.table_next_column()
                            
                            if begin_child("Child##1", (0, 150), True, PyImGui.WindowFlags.NoFlag):
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                                ImGui.text("This is a child content.")
                            end_child()
                            
                            PyImGui.table_next_column()
                            
                            ImGui.text("Tab Bar")
                            PyImGui.table_next_column()

                            if ImGui.begin_tab_bar("Tab Bar"):
                                if ImGui.begin_tab_item("Tab 1"):
                                    ImGui.text("Content for Tab 1")
                                    ImGui.end_tab_item()

                                if ImGui.begin_tab_item("Tab 2"):
                                    ImGui.text("Content for Tab 2")
                                    ImGui.end_tab_item()

                                ImGui.end_tab_bar()

                            end_table()
                        PyImGui.pop_item_width()
                    ImGui.end_tab_item()                
                ImGui.end_tab_bar()
                
            window_module.process_window()
            
        window_module.end()

        if save_throttle_timer.HasElapsed(save_throttle_time):
            if window_module.window_pos[0] != window_module.end_pos[0] or window_module.window_pos[1] != window_module.end_pos[1]:
                window_module.window_pos = window_module.end_pos
                ini_handler.write_key(module_name + " Config", "x", str(int(window_module.window_pos[0])))
                ini_handler.write_key(module_name + " Config", "y", str(int(window_module.window_pos[1])))

            if window_width != window_module.window_size[0] or window_height != window_module.window_size[1]:
                ini_handler.write_key(module_name + " Config", "width", str(int(window_module.window_size[0])))
                ini_handler.write_key(module_name + " Config", "height", str(int(window_module.window_size[1])))
                window_width, window_height = window_module.window_size

            if window_module.collapsed_status != window_module.collapse:
                window_module.collapse = window_module.collapsed_status
                ini_handler.write_key(module_name + " Config", "collapsed", str(window_module.collapse))

            save_throttle_timer.Reset()


    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Debug)

def main():
    """Required main function for the widget"""
    global game_throttle_timer, game_throttle_time, window_module
    
    try:            
        DrawWindow()
        window_module.open  = False
            
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
        return False
    return True

# These functions need to be available at module level
__all__ = ['main', 'configure']

if __name__ == "__main__":
    main()
