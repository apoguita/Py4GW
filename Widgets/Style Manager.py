from enum import Enum
import math
from pathlib import Path
from types import FunctionType
from typing import Optional, overload
from unittest import case
import Py4GW
import PyImGui

from Py4GWCoreLib import IniHandler, Overlay
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import Timer
from Py4GWCoreLib import SplitTexture
from Py4GWCoreLib import MapTexture
from Py4GWCoreLib import GameTextures
from Py4GWCoreLib import TextureState
from Py4GWCoreLib import Style
from Py4GWCoreLib import ControlAppearance
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
ini_file_location = os.path.join(
    root_directory, "Widgets/Config/Style Manager.ini")
ini_handler = IniHandler(ini_file_location)


save_throttle_time = 1000
save_throttle_timer = Timer()
save_throttle_timer.Start()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

window_x = ini_handler.read_int(module_name + str(" Config"), "x", 100)
window_y = ini_handler.read_int(module_name + str(" Config"), "y", 100)

window_width = ini_handler.read_int(module_name + str(" Config"), "width", 600)
window_height = ini_handler.read_int(
    module_name + str(" Config"), "height", 500)

window_collapsed = ini_handler.read_bool(
    module_name + str(" Config"), "collapsed", False)

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
control_compare = False
theme_compare = True
match_style_vars = False

py4_gw_ini_handler = IniHandler("Py4GW.ini")
selected_theme = Style.StyleTheme[py4_gw_ini_handler.read_key(
    "settings", "style_theme", Style.StyleTheme.ImGui.name)]
themes = [theme.name.replace("_", " ") for theme in Style.StyleTheme]

ImGui.reload_theme(Style.StyleTheme(selected_theme))
ImGui.set_theme(selected_theme)

org_style: Style = ImGui.Selected_Style.copy()

# TODO: Fix collapsing UIs that are not gw themed
# TODO: Remove style pushing on a window level

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
        self.toggle_button_1 = True
        self.toggle_button_2 = False
        self.toggle_button_3 = False
        self.toggle_button_4 = False
        self.image_toggle_button_1 = True
        self.image_toggle_button_2 = False
        self.image_toggle_button_3 = False
        self.image_toggle_button_4 = False
        self.objective_1 = True
        self.objective_2 = False
        self.checkbox = True
        self.checkbox_2 = False
        self.radio_button = 0
        self.slider_int = 25
        self.slider_float = 33.0


preview = preview_states()
TEXTURE_FOLDER = "Textures\\Game UI\\"
MINIMALUS_FOLDER = "Textures\\Themes\\Minimalus\\"


class ThemeTexture:
    PlaceHolderTexture = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "placeholder.png"),
        texture_size = (1, 1),
        size = (1, 1),
        normal=(0, 0)
    )
    
    def __init__(
        self,
        *args: tuple[Style.StyleTheme, SplitTexture | MapTexture]
    ):
        self.textures: dict[Style.StyleTheme, SplitTexture | MapTexture] = {}

        for theme, texture in args:
            self.textures[theme] = texture

    def get_texture(self, theme: Style.StyleTheme | None = None) -> SplitTexture | MapTexture:
        theme = theme or ImGui.get_style().Theme
        return self.textures.get(theme, ThemeTexture.PlaceHolderTexture)

class ThemeTextures(Enum):
    Combo_Arrow = ThemeTexture(
        (Style.StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_combo_arrow.png"),
            texture_size=(128, 32),
            left=(4, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 123, 27)
        )),

        (Style.StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_combo_arrow.png"),
            texture_size=(128, 32),
            left=(1, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 126, 27),
        ))
    )
    
    Combo_Background = ThemeTexture(
        (Style.StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_combo_background.png"),
            texture_size=(128, 32),
            left=(4, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 124, 27)
        )),

        (Style.StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(
                TEXTURE_FOLDER, "ui_combo_background.png"),
            texture_size=(128, 32),
            left=(1, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 126, 27),
        ))
    )

    Combo_Frame = ThemeTexture(
        (Style.StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_combo_frame.png"),
            texture_size=(128, 32),
            left=(4, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 124, 27),
        )),
        
        (Style.StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_combo_frame.png"),
            texture_size=(128, 32),
            left=(1, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 126, 27),
        ))
    )
    
    Button_Frame = ThemeTexture(
        (Style.StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_button_frame.png"),
            texture_size=(32, 32),
            left=(6, 4, 7, 25),
            mid=(8, 4, 24, 25),
            right=(25, 4, 26, 25), 
        )),

        (Style.StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_button_frame.png"),
            texture_size=(32, 32),
            left=(2, 4, 7, 25),
            mid=(8, 4, 24, 25),
            right=(24, 4, 30, 25), 
        ))
    )
    
    Button_Background = ThemeTexture(
        (Style.StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_button_background.png"),
            texture_size=(32, 32),
            left=(6, 4, 7, 25),
            mid=(8, 4, 24, 25),
            right=(25, 4, 26, 25), 
        )),

        (Style.StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_button_background.png"),
            texture_size=(32, 32),
            left=(2, 4, 7, 25),
            mid=(8, 4, 24, 25),
            right=(24, 4, 30, 25), 
        ))
    )

    CheckBox_Unchecked = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 17),
        normal=(2, 2),
        active=(23, 2),
        disabled=(107, 2),
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 17),
        normal=(2, 2),
        active=(23, 2),
        disabled=(107, 2),
    )),
    )
    
    CheckBox_Checked = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 18),
        normal=(44, 1),
        active=(65, 1),
        disabled=(86, 1),
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 18),
        normal=(44, 1),
        active=(65, 1),
        disabled=(86, 1),
    )),
    )
    
    SliderBar = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_slider_bar.png"),
        texture_size=(32, 16),
        left=(0, 0, 7, 16),
        mid=(8, 0, 24, 16),
        right=(25, 0, 32, 16),   
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_slider_bar.png"),
        texture_size=(32, 16),
        left=(0, 0, 7, 16),
        mid=(8, 0, 24, 16),
        right=(25, 0, 32, 16),   
    )),
    )
    
    SliderGrab = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_slider_grab.png"),
        texture_size=(32, 32),
        size=(18, 18),
        normal=(7, 7)
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_slider_grab.png"),
        texture_size=(32, 32),
        size=(18, 18),
        normal=(7, 7)
    )),
    )
    
    Input_Inactive = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_input_inactive.png"),
        texture_size=(32, 16),
        left= (1, 1, 6, 15),
        mid= (7, 1, 26, 15),
        right= (27, 1, 31, 15),
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_input_inactive.png"),
        texture_size=(32, 16),
        left= (1, 1, 6, 15),
        mid= (7, 1, 26, 15),
        right= (27, 1, 31, 15),
    )),
    )
    
    Input_Active = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_input_active.png"),
        texture_size=(32, 16),
        left= (1, 1, 6, 15),
        mid= (7, 1, 26, 15),
        right= (27, 1, 31, 15),
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_input_active.png"),
        texture_size=(32, 16),
        left= (1, 1, 6, 15),
        mid= (7, 1, 26, 15),
        right= (27, 1, 31, 15),
    )),
    )
    
    
    Expand = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (13, 12),
        normal = (0, 3),
        hovered = (16, 3),
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (12, 12),
        normal = (1, 3),
        hovered = (17, 3),
    )),
    )
    
    Collapse = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (13, 12),
        normal = (0, 19),
        hovered = (16, 19),
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (12, 12),
        normal = (1, 19),
        hovered = (17, 19),
    )),
    )        
    
    
    Tab_Frame_Top = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
        left=(1, 1, 4, 5),
        mid=(5, 1, 26, 5),
        right=(27, 1, 31, 5),   
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
        left=(1, 1, 4, 5),
        mid=(5, 1, 26, 5),
        right=(27, 1, 31, 5),   
    )),
    )
    
    Tab_Frame_Body = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
        left=(1, 5, 4, 26),
        mid=(5, 5, 26, 26),
        right=(27, 5, 31, 26), 
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
        left=(1, 5, 4, 26),
        mid=(5, 5, 26, 26),
        right=(27, 5, 31, 26),  
    )),
    )
    
    Tab_Active = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_active.png"),
        texture_size=(32, 32),
        left=(2, 1, 8, 32),
        mid=(9, 1, 23, 32),
        right=(24, 1, 30, 32),   
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_active.png"),
        texture_size=(32, 32),
        left=(2, 1, 8, 32),
        mid=(9, 1, 23, 32),
        right=(24, 1, 30, 32),   
    )),
    )
    
    Tab_Inactive = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_inactive.png"),
        texture_size=(32, 32),
        left=(2, 6, 8, 32),
        mid=(9, 6, 23, 32),
        right=(24, 6, 30, 32),   
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_inactive.png"),
        texture_size=(32, 32),
        left=(2, 6, 8, 32),
        mid=(9, 6, 23, 32),
        right=(24, 6, 30, 32),    
    )),
    )
    
    
class ImGuiDev:
    #region WIP
    @staticmethod
    def begin_popup(id: str, flags: PyImGui.WindowFlags = PyImGui.WindowFlags.NoFlag) -> bool:     
        style = ImGui.get_style()
        
        style.push_style()
        open = PyImGui.begin_popup(id, PyImGui.WindowFlags(flags))
        style.pop_style()
        
        return open

    @staticmethod
    def end_popup():
        PyImGui.end_popup()

    @staticmethod
    def begin_tooltip() -> bool:
        style = ImGui.get_style()
        style.push_style()
        open = PyImGui.begin_tooltip()
        style.pop_style()
        
        return open

    @staticmethod
    def end_tooltip():
        ImGui.pop_theme_window_style()
        PyImGui.end_tooltip()

    @staticmethod
    def begin_combo(label: str, preview_value: str, flags: PyImGui.ImGuiComboFlags = PyImGui.ImGuiComboFlags.NoFlag):
        open = PyImGui.begin_combo(label, preview_value, flags)

        return open

    @staticmethod
    def end_combo():
        PyImGui.end_combo()
        
    @staticmethod
    def selectable(label: str, selected: bool, flags: PyImGui.SelectableFlags = PyImGui.SelectableFlags.NoFlag, size: tuple[float, float] = (0.0, 0.0)) -> bool:
        clicked = PyImGui.selectable(label, selected, flags, size)

        return clicked

    @staticmethod
    def color_edit3(label: str, color: tuple[float, float, float]) -> tuple[float, float, float]:
        color = PyImGui.color_edit3(label, color)

        return color

    @staticmethod
    def color_edit4(label: str, color: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        color = PyImGui.color_edit4(label, color)

        return color

    @staticmethod
    def begin_menu_bar() -> bool:
        opened = PyImGui.begin_menu_bar()

        return opened

    @staticmethod
    def end_menu_bar():
        PyImGui.end_menu_bar()
        
    @staticmethod
    def begin_main_menu_bar() -> bool:
        opened = PyImGui.begin_main_menu_bar()

        return opened

    @staticmethod
    def end_main_menu_bar():
        PyImGui.end_main_menu_bar()
        
    @staticmethod
    def begin_menu(label: str) -> bool:
        opened = PyImGui.begin_menu(label)

        return opened

    @staticmethod
    def end_menu():
        PyImGui.end_menu()
        
    @staticmethod
    def menu_item(label: str) -> bool:
        clicked = PyImGui.menu_item(label)

        return clicked

    @staticmethod
    def begin_popup_modal(name: str, p_open: Optional[bool], flags: int) -> bool:
        style = ImGui.get_style()
        style.push_style()

        opened = PyImGui.begin_popup_modal(name, p_open, flags)

        style.pop_style()

        return opened

    @staticmethod
    def end_popup_modal():
        PyImGui.end_popup_modal()

    @staticmethod
    def tree_node_ex(label: str, flags: int, fmt: str) -> bool:
        opened = PyImGui.tree_node_ex(label, flags, fmt)

        return opened

    #endregion WIP
             
    @staticmethod
    def begin(name: str, p_open: Optional[bool] = None, flags: PyImGui.WindowFlags = PyImGui.WindowFlags.NoFlag) -> bool:
            
        style = ImGui.get_style()
        
        style.push_style()
        if name not in ImGui.WindowModule._windows:
            ImGui.WindowModule._windows[name] = ImGui.WindowModule(name, window_flags=flags)

            imgui_ini_reader = ImGui.ImGuiIniReader()
            window = imgui_ini_reader.get(name)
            ImGui.WindowModule._windows[name].window_pos = window.pos if window else (100.0, 100.0)
            ImGui.WindowModule._windows[name].window_size = window.size if window else (800.0, 600.0)
            ImGui.WindowModule._windows[name].collapse = window.collapsed if window else False

        open = ImGui.WindowModule._windows[name].begin(p_open, flags)
        style.pop_style()
        
        return open
    
    @staticmethod
    def begin_with_close(name: str, p_open: Optional[bool] = None, flags: PyImGui.WindowFlags = PyImGui.WindowFlags.NoFlag) -> bool:
        style = ImGui.get_style()

        style.push_style()
        if name not in ImGui.WindowModule._windows:
            ImGui.WindowModule._windows[name] = ImGui.WindowModule(name, window_flags=flags)

            imgui_ini_reader = ImGui.ImGuiIniReader()
            window = imgui_ini_reader.get(name)
            ImGui.WindowModule._windows[name].window_pos = window.pos if window else (100.0, 100.0)
            ImGui.WindowModule._windows[name].window_size = window.size if window else (800.0, 600.0)
            ImGui.WindowModule._windows[name].collapse = window.collapsed if window else False

        ImGui.WindowModule._windows[name].can_close = True
        open = ImGui.WindowModule._windows[name].begin(p_open, flags)
        style.pop_style()
        
        return open

    @staticmethod
    def end():
        PyImGui.end()

    @staticmethod
    def new_line():
        PyImGui.new_line()
        
    @staticmethod
    def text(text : str, font_size : Optional[int] = None, font_style: str = "Regular"):
        if font_size is not None:
            ImGui.push_font(font_style, font_size)
            PyImGui.text(text)
            ImGui.pop_font()
        else:
            PyImGui.text(text)

    @staticmethod
    def text_disabled(text : str, font_size : Optional[int] = None, font_style: str = "Regular"):
        if font_size is not None:
            ImGui.push_font(font_style, font_size)
            PyImGui.text_disabled(text)
            ImGui.pop_font()
        else:
            PyImGui.text_disabled(text)

    @staticmethod
    def text_wrapped(text : str, font_size : Optional[int] = None, font_style: str = "Regular"):
        if font_size is not None:
            ImGui.push_font(font_style, font_size)
            PyImGui.text_wrapped(text)
            ImGui.pop_font()
        else:
            PyImGui.text_wrapped(text)

    @staticmethod
    def text_colored(text : str, color: tuple[float, float, float, float], font_size : Optional[int] = None, font_style: str = "Regular"):
        if font_size is not None:
            ImGui.push_font(font_style, font_size)
            PyImGui.text_colored(text, color)
            ImGui.pop_font()
        else:
            PyImGui.text_colored(text, color)

    @staticmethod
    def text_unformatted(text : str, font_size : Optional[int] = None, font_style: str = "Regular"):
        if font_size is not None:
            ImGui.push_font(font_style, font_size)
            PyImGui.text_unformatted(text)
            ImGui.pop_font()
        else:
            PyImGui.text_unformatted(text)

    @staticmethod
    def text_scaled(text : str, color: tuple[float, float, float, float], scale: float):
        PyImGui.text_scaled(text, color, scale)
        
    @staticmethod
    def small_button(label: str, enabled: bool = True, appearance: ControlAppearance = ControlAppearance.Default) -> bool:
        PyImGui.begin_disabled(not enabled)
        style = ImGui.get_style()
        style.ButtonPadding.get_current().push_style_var()
        style.FrameRounding.get_current().push_style_var()

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.small_button(label)
                PyImGui.pop_style_color(5)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0] + 2
                height = item_rect_max[1] - item_rect_min[1] + 2

                x,y = item_rect_min
                display_label = label.split("##")[0]

                button_rect = (x, y, width, height)
                match (appearance):
                    case ControlAppearance.Primary:
                        tint = ((style.PrimaryButtonActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.PrimaryButtonHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.PrimaryButton.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple

                    case ControlAppearance.Danger:
                        tint = ((style.DangerButtonActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.DangerButtonHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.DangerButton.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple

                    case _:
                        tint = ((style.ButtonTextureBackgroundActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.ButtonTextureBackgroundHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.ButtonTextureBackground.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple
                                
                ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=tint,
                )
                
                frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) and enabled else (200, 200, 200, 255)
                ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=frame_tint,
                )
                
                font_size = int(PyImGui.get_text_line_height()) - 1
                
                ImGui.push_font("Regular", font_size)
                text_size = PyImGui.calc_text_size(display_label)
                text_x = button_rect[0] + (button_rect[2] - text_size[0]) / 2
                text_y = button_rect[1] + (button_rect[3] - text_size[1]) / 2 + 1
            
                PyImGui.push_clip_rect(
                    button_rect[0] + 6,
                    button_rect[1] + 2,
                    width - 12,
                    height - 4,
                    True
                )
                
                PyImGui.draw_list_add_text(
                    text_x,
                    text_y,
                    style.TextDisabled.get_current().color_int if not enabled else style.Text.get_current().color_int,
                    display_label,
                )
                ImGui.pop_font()

                PyImGui.pop_clip_rect()
                
            case _:
                button_colors = []
                
                match (appearance):
                    case ControlAppearance.Primary:
                        button_colors = [
                            style.PrimaryButton,
                            style.PrimaryButtonHovered,
                            style.PrimaryButtonActive,
                        ]

                    case ControlAppearance.Danger:
                        button_colors = [
                            style.DangerButton,
                            style.DangerButtonHovered,
                            style.DangerButtonActive,
                        ]

                if enabled:
                    for button_color in button_colors:
                        button_color.push_color()
                
                clicked = PyImGui.small_button(label)
                
                if enabled:
                    for button_color in button_colors:
                        button_color.pop_color()

        style.ButtonPadding.pop_style_var()
        style.FrameRounding.pop_style_var()
        PyImGui.end_disabled()

        return clicked
   
    @staticmethod
    def icon_button(label: str, width: float = 0, height: float = 0, enabled: bool = True, appearance: ControlAppearance = ControlAppearance.Default) -> bool:
        def group_text_with_icons(text: str):
            """
            Splits the string into groups of (is_icon, run_string).
            Example: "Hi 123X" -> [(False, "Hi "), (True, "123"), (False, "X")]
            """
            if not text:
                return []

            groups = []
            current_type = text[0] in IconsFontAwesome5.ALL_ICONS
            current_run = [text[0]]

            for ch in text[1:]:
                is_icon = ch in IconsFontAwesome5.ALL_ICONS
                if is_icon == current_type:
                    # same type, continue current run
                    current_run.append(ch)
                else:
                    # type switched, flush old run
                    groups.append((current_type, ''.join(current_run)))
                    current_run = [ch]
                    current_type = is_icon

            # flush last run
            if current_run:
                groups.append((current_type, ''.join(current_run)))

            return groups

        PyImGui.begin_disabled(not enabled)
        style = ImGui.get_style()
        style.ButtonPadding.get_current().push_style_var()
        style.FrameRounding.get_current().push_style_var()

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.button(label, width, height)
                PyImGui.pop_style_color(5)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0] + 2
                height = item_rect_max[1] - item_rect_min[1] + 2

                x,y = item_rect_min
                display_label = label.split("##")[0]

                button_rect = (x, y, width, height)
                
                default_font_size = int(PyImGui.get_text_line_height())
                fontawesome_font_size = int(height * 0.42)
                
                groups = group_text_with_icons(display_label)
                font_awesome_string = "".join([run for is_icon, run in groups if is_icon])
                text_string = "".join([run for is_icon, run in groups if not is_icon]) 
                text_size = PyImGui.calc_text_size(text_string)
                
                
                ImGui.push_font("Regular", fontawesome_font_size)
                font_awesome_text_size = PyImGui.calc_text_size(font_awesome_string)
                ImGui.pop_font()
                
                total_text_size = (text_size[0] + font_awesome_text_size[0], max(text_size[1], font_awesome_text_size[1]))

                text_x = button_rect[0] + (button_rect[2] - total_text_size[0]) / 2
                text_y = button_rect[1] + (button_rect[3] - total_text_size[1]) / 2
                
                match (appearance):
                    case ControlAppearance.Primary:
                        tint = ((style.PrimaryButtonActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.PrimaryButtonHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.PrimaryButton.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple

                    case ControlAppearance.Danger:
                        tint = ((style.DangerButtonActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.DangerButtonHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.DangerButton.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple

                    case _:
                        tint = ((style.ButtonTextureBackgroundActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.ButtonTextureBackgroundHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.ButtonTextureBackground.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple
                                
                ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=tint,
                )
                
                frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) and enabled else (200, 200, 200, 255)
                ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=frame_tint,
                )
                
                PyImGui.push_clip_rect(
                    button_rect[0] + 6,
                    button_rect[1] + 2,
                    width - 12,
                    height - 4,
                    True
                )
                
                offset = (0, 0)

                for is_icon, run in groups:
                    if is_icon:
                        ImGui.push_font("Regular", fontawesome_font_size)
                    else:
                        ImGui.push_font("Regular", default_font_size)
                    
                    text_size = PyImGui.calc_text_size(run)    
                    vertical_padding = 0 if is_icon else 1                
                                    
                    PyImGui.draw_list_add_text(
                        text_x + offset[0],
                        text_y + vertical_padding,
                        style.TextDisabled.get_current().color_int if not enabled else style.Text.get_current().color_int,
                        run,
                    )
                    
                    offset = (offset[0] + text_size[0], vertical_padding)
                    
                    ImGui.pop_font()

                PyImGui.pop_clip_rect()
                
            case _:
                button_colors = []
                
                match (appearance):
                    case ControlAppearance.Primary:
                        button_colors = [
                            style.PrimaryButton,
                            style.PrimaryButtonHovered,
                            style.PrimaryButtonActive,
                        ]

                    case ControlAppearance.Danger:
                        button_colors = [
                            style.DangerButton,
                            style.DangerButtonHovered,
                            style.DangerButtonActive,
                        ]

                if enabled:
                    for button_color in button_colors:
                        button_color.push_color()
                
                clicked = PyImGui.button(label, width, height)

                for button_color in button_colors:
                    button_color.pop_color()

        style.ButtonPadding.pop_style_var()
        style.FrameRounding.pop_style_var()
        PyImGui.end_disabled()
        
        return clicked
    
    @staticmethod
    def button(label: str, width: float = 0, height: float = 0, enabled: bool = True, appearance: ControlAppearance = ControlAppearance.Default) -> bool:
        PyImGui.begin_disabled(not enabled)
        style = ImGui.get_style()
        style.ButtonPadding.get_current().push_style_var()
        style.FrameRounding.get_current().push_style_var()

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.button(label, width, height)
                PyImGui.pop_style_color(5)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0] + 2
                height = item_rect_max[1] - item_rect_min[1] + 2

                x,y = item_rect_min
                display_label = label.split("##")[0]

                button_rect = (x, y, width, height)
                match (appearance):
                    case ControlAppearance.Primary:
                        tint = ((style.PrimaryButtonActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.PrimaryButtonHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.PrimaryButton.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple

                    case ControlAppearance.Danger:
                        tint = ((style.DangerButtonActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.DangerButtonHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.DangerButton.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple

                    case _:
                        tint = ((style.ButtonTextureBackgroundActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.ButtonTextureBackgroundHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.ButtonTextureBackground.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple
                                
                ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=tint,
                )
                
                frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) and enabled else (200, 200, 200, 255)
                ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=frame_tint,
                )
                
                text_size = PyImGui.calc_text_size(display_label)
                text_x = button_rect[0] + (button_rect[2] - text_size[0]) / 2
                text_y = button_rect[1] + (button_rect[3] - text_size[1]) / 2 + 1
            
                PyImGui.push_clip_rect(
                    button_rect[0] + 6,
                    button_rect[1] + 2,
                    width - 12,
                    height - 4,
                    True
                )
                
                PyImGui.draw_list_add_text(
                    text_x,
                    text_y,
                    style.TextDisabled.get_current().color_int if not enabled else style.Text.get_current().color_int,
                    display_label,
                )

                PyImGui.pop_clip_rect()
                
            case _:
                button_colors = []
                
                match (appearance):
                    case ControlAppearance.Primary:
                        button_colors = [
                            style.PrimaryButton,
                            style.PrimaryButtonHovered,
                            style.PrimaryButtonActive,
                        ]

                    case ControlAppearance.Danger:
                        button_colors = [
                            style.DangerButton,
                            style.DangerButtonHovered,
                            style.DangerButtonActive,
                        ]

                if enabled:
                    for button_color in button_colors:
                        button_color.push_color()
                
                clicked = PyImGui.button(label, width, height)
                
                if enabled:
                    for button_color in button_colors:
                        button_color.pop_color()
                    

        style.ButtonPadding.pop_style_var()
        style.FrameRounding.pop_style_var()
        PyImGui.end_disabled()
        
        return clicked
    
    @staticmethod
    def toggle_button(label: str, v: bool, width=0, height =0, enabled:bool=True) -> bool:
        PyImGui.begin_disabled(not enabled)
        style = ImGui.get_style()
        style.ButtonPadding.get_current().push_style_var()
        style.FrameRounding.get_current().push_style_var()

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.button(label, width, height)
                PyImGui.pop_style_color(5)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0] + 2
                height = item_rect_max[1] - item_rect_min[1] + 2

                x,y = item_rect_min
                display_label = label.split("##")[0]

                button_rect = (x, y, width, height)
                
                if not v:
                    style.Text.push_color((180, 180, 180, 200))
                
                text_color = style.TextDisabled.get_current().color_int if not enabled else style.Text.get_current().color_int
                
                button_colors = [
                    style.ToggleButtonEnabled.get_current(),
                    style.ToggleButtonEnabledHovered.get_current(),
                    style.ToggleButtonEnabledActive.get_current(),
                ] if v else [
                    style.ToggleButtonDisabled.get_current(),
                    style.ToggleButtonDisabledHovered.get_current(),
                    style.ToggleButtonDisabledActive.get_current(),
                ]

                tint = ((button_colors[2].get_current().rgb_tuple if PyImGui.is_item_active() else button_colors[1].get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else button_colors[0].get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple
                                                
                ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=tint,
                )
                
                frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) and enabled else (200, 200, 200, 255)
                ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=frame_tint,
                )
                
                text_size = PyImGui.calc_text_size(display_label)
                text_x = button_rect[0] + (button_rect[2] - text_size[0]) / 2
                text_y = button_rect[1] + (button_rect[3] - text_size[1]) / 2 
            
                PyImGui.push_clip_rect(
                    button_rect[0] + 6,
                    button_rect[1] + 2,
                    width - 12,
                    height - 4,
                    True
                )
                
                PyImGui.draw_list_add_text(
                    text_x,
                    text_y,
                    text_color,
                    display_label,
                )

                PyImGui.pop_clip_rect()
                style.Text.pop_color()
                
            case _:                
                button_colors = [
                    style.ToggleButtonEnabled,
                    style.ToggleButtonEnabledHovered,
                    style.ToggleButtonEnabledActive,
                ] if v else [
                    style.ToggleButtonDisabled,
                    style.ToggleButtonDisabledHovered,
                    style.ToggleButtonDisabledActive,
                ]
                
                if enabled:
                    for button_color in button_colors:
                        button_color.push_color()
                
                clicked = PyImGui.button(label, width, height)
                
                if enabled:
                    for button_color in button_colors:
                        button_color.pop_color()

        style.ButtonPadding.pop_style_var()
        style.FrameRounding.pop_style_var()
        PyImGui.end_disabled()
        
        if clicked:
            v = not v
        
        return v
    
    @staticmethod
    def image_button(label: str, texture_path: str, width=32, height=32, enabled:bool=True, appearance: ControlAppearance = ControlAppearance.Default) -> bool:
        
        PyImGui.begin_disabled(not enabled)
        style = ImGui.get_style()
        style.ButtonPadding.push_style_var(width / 8, height / 8)
        style.FrameRounding.get_current().push_style_var()

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.button("##image_button " + label, width, height)
                PyImGui.pop_style_color(5)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0]
                height = item_rect_max[1] - item_rect_min[1]

                x,y = item_rect_min
                display_label = label.split("##")[0]

                button_rect = (x, y, width, height)
                match (appearance):
                    case ControlAppearance.Primary:
                        tint = ((style.PrimaryButtonActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.PrimaryButtonHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.PrimaryButton.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple

                    case ControlAppearance.Danger:
                        tint = ((style.DangerButtonActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.DangerButtonHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.DangerButton.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple

                    case _:
                        tint = ((style.ButtonActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.ButtonHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.Button.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple
                              

                ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=tint,
                )
                

                texture_pos = (button_rect[0] + style.ButtonPadding.get_current().value1 + 1, button_rect[1] + (style.ButtonPadding.get_current().value2 or 0))
                texture_size = (width - (style.ButtonPadding.get_current().value1 * 2), height - ((style.ButtonPadding.get_current().value2 or 0) * 2))
                texture_tint = (255, 255, 255, 255) if enabled else (255, 255, 255, 155)
                ImGui.DrawTextureInDrawList(
                    texture_pos,
                    texture_size,
                    texture_path,
                    tint=texture_tint
                )
                                
                frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) and enabled else (200, 200, 200, 255)
                ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=frame_tint,
                )
                PyImGui.push_clip_rect(
                    button_rect[0] + 6,
                    button_rect[1] + 2,
                    width - 12,
                    height - 4,
                    True
                )
                
                PyImGui.pop_clip_rect()
                
            case _:
                button_colors = []
                
                match (appearance):
                    case ControlAppearance.Primary:
                        button_colors = [
                            style.PrimaryButton,
                            style.PrimaryButtonHovered,
                            style.PrimaryButtonActive,
                        ]

                    case ControlAppearance.Danger:
                        button_colors = [
                            style.DangerButton,
                            style.DangerButtonHovered,
                            style.DangerButtonActive,
                        ]

                if enabled:
                    for button_color in button_colors:
                        button_color.push_color()
                
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))
                clicked = PyImGui.button("##image_button " + label, width, height)
                PyImGui.pop_style_color(2)
                
                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0] + 2
                height = item_rect_max[1] - item_rect_min[1] + 2

                x,y = item_rect_min
                button_rect = (x, y, width, height)
                
                texture_pos = (button_rect[0] + style.ButtonPadding.get_current().value1, button_rect[1] + (style.ButtonPadding.get_current().value2 or 0))
                texture_size = (width - (style.ButtonPadding.get_current().value1 * 2), height - ((style.ButtonPadding.get_current().value2 or 0) * 2))
                texture_tint = (255, 255, 255, 255) if enabled else (255, 255, 255, 155)
                ImGui.DrawTextureInDrawList(
                    texture_pos,
                    texture_size,
                    texture_path,
                    tint=texture_tint
                )
                
                if enabled:
                    for button_color in button_colors:
                        button_color.pop_color()

        style.ButtonPadding.pop_style_var()
        style.FrameRounding.pop_style_var()
        PyImGui.end_disabled()
        
        return clicked
    
    @staticmethod
    def image_toggle_button(label: str, texture_path: str, v: bool, width=32, height=32, enabled:bool=True) -> bool:
        PyImGui.begin_disabled(not enabled)
        style = ImGui.get_style()
        style.ButtonPadding.push_style_var(width / 8, height / 8)
        style.FrameRounding.get_current().push_style_var()

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.button("##image_toggle_button " + label, width, height)
                PyImGui.pop_style_color(5)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0]
                height = item_rect_max[1] - item_rect_min[1]

                x,y = item_rect_min
                display_label = label.split("##")[0]

                button_rect = (x, y, width, height)
                
                button_colors = [
                    style.ToggleButtonEnabled.get_current(),
                    style.ToggleButtonEnabledHovered.get_current(),
                    style.ToggleButtonEnabledActive.get_current(),
                ] if v else [
                    style.ToggleButtonDisabled.get_current(),
                    style.ToggleButtonDisabledHovered.get_current(),
                    style.ToggleButtonDisabledActive.get_current(),
                ]

                tint = ((button_colors[2].get_current().rgb_tuple if PyImGui.is_item_active() else button_colors[1].get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else button_colors[0].get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple


                ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=tint,
                )
                

                texture_pos = (button_rect[0] + style.ButtonPadding.get_current().value1 + 1, button_rect[1] + (style.ButtonPadding.get_current().value2 or 0))
                texture_size = (width - (style.ButtonPadding.get_current().value1 * 2), height - ((style.ButtonPadding.get_current().value2 or 0) * 2))
                texture_tint = (255, 255, 255, (255 if enabled else 155)) if v else (128, 128, 128, (255 if enabled else 155))
                
                ImGui.DrawTextureInDrawList(
                    texture_pos,
                    texture_size,
                    texture_path,
                    tint=texture_tint
                )
                                
                frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) and enabled else (200, 200, 200, 255)
                ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
                    button_rect[0], 
                    button_rect[1],
                    (button_rect[2], button_rect[3]),
                    tint=frame_tint,
                )
                PyImGui.push_clip_rect(
                    button_rect[0] + 6,
                    button_rect[1] + 2,
                    width - 12,
                    height - 4,
                    True
                )
                

                PyImGui.pop_clip_rect()
                
            case _:
                button_colors = [
                    style.ToggleButtonEnabled.get_current(),
                    style.ToggleButtonEnabledHovered.get_current(),
                    style.ToggleButtonEnabledActive.get_current(),
                ] if v else [
                    style.ToggleButtonDisabled.get_current(),
                    style.ToggleButtonDisabledHovered.get_current(),
                    style.ToggleButtonDisabledActive.get_current(),
                ]
                                
                if enabled:
                    for button_color in button_colors:
                        button_color.push_color()
                    
                
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))
                clicked = PyImGui.button("##image_toggle_button " + label, width, height)
                PyImGui.pop_style_color(2)
                
                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0] + 2
                height = item_rect_max[1] - item_rect_min[1] + 2

                x,y = item_rect_min
                button_rect = (x, y, width, height)
                
                texture_pos = (button_rect[0] + style.ButtonPadding.get_current().value1, button_rect[1] + (style.ButtonPadding.get_current().value2 or 0))
                texture_size = (width - (style.ButtonPadding.get_current().value1 * 2), height - ((style.ButtonPadding.get_current().value2 or 0) * 2))
                texture_tint = (255, 255, 255, (255 if enabled else 155)) if v else (128, 128, 128, (255 if enabled else 155))
                ImGui.DrawTextureInDrawList(
                    texture_pos,
                    texture_size,
                    texture_path,
                    tint=texture_tint
                )
                    
                if enabled:
                    for button_color in button_colors:
                        button_color.pop_color()

        style.ButtonPadding.pop_style_var()
        style.FrameRounding.pop_style_var()
        PyImGui.end_disabled()
            
        if clicked:
            v = not v
        
        return v
    
    @staticmethod
    def combo(label: str, current_item: int, items: list[str]) -> int:
        index = current_item
        style = ImGui.get_style()
        style.FrameRounding.get_current().push_style_var()
        style.FramePadding.get_current().push_style_var()
        style.ItemInnerSpacing.get_current().push_style_var()

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))

                index = PyImGui.combo(label, current_item, items)
                display_label = label.split("##")[0]
                label_size = PyImGui.calc_text_size(display_label)

                PyImGui.pop_style_color(6)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()

                width = item_rect_max[0] - item_rect_min[0] - \
                    (label_size[0] + 10 if label_size[0] > 0 else 0)
                height = item_rect_max[1] - item_rect_min[1]
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)

                tint = ((style.ComboTextureBackgroundActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.ComboTextureBackgroundHovered.get_current(
                ).rgb_tuple) if ImGui.is_mouse_in_rect(item_rect) else style.ComboTextureBackground.get_current().rgb_tuple) if True else (64, 64, 64, 255)

                frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(
                    item_rect) and True else (200, 200, 200, 255)

                ThemeTextures.Combo_Background.value.get_texture().draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (width, height),
                    tint=tint
                )

                ThemeTextures.Combo_Arrow.value.get_texture().draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (width, height),
                    tint=style.Text.get_current().rgb_tuple
                )

                ThemeTextures.Combo_Frame.value.get_texture().draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (width, height),
                    tint=frame_tint
                )

                text_size = PyImGui.calc_text_size(items[index])
                text_x = item_rect[0] + 10
                text_y = item_rect[1] + 2 + (height - text_size[1]) / 2

                PyImGui.push_clip_rect(
                    text_x,
                    text_y,
                    width - 40,
                    height - 4,
                    True
                )

                PyImGui.draw_list_add_text(
                    text_x,
                    text_y,
                    style.Text.get_current().color_int,
                    items[index],
                )

                PyImGui.pop_clip_rect()

            case _:
                index = PyImGui.combo(label, current_item, items)

        style.FrameRounding.pop_style_var()
        style.FramePadding.pop_style_var()
        style.ItemInnerSpacing.pop_style_var()

        return index

    @staticmethod
    def checkbox(label: str, is_checked: bool, enabled: bool = True) -> bool:
        style = ImGui.get_style()
        style.FrameRounding.get_current().push_style_var()
        style.FramePadding.get_current().push_style_var()
        style.ItemInnerSpacing.get_current().push_style_var()

        new_value = is_checked
        PyImGui.begin_disabled(not enabled)

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.CheckMark, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0,0,0,0))
                new_value = PyImGui.checkbox(label, is_checked)
                PyImGui.pop_style_color(5)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                padding = 4
                width = item_rect_max[0] - item_rect_min[0]
                height = item_rect_max[1] - item_rect_min[1] - (padding * 2)
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                checkbox_rect = (item_rect_min[0] + padding, item_rect_min[1] + padding, height, height)
                line_height = PyImGui.get_text_line_height()
                text_rect = (item_rect[0] + checkbox_rect[2] + 2 + style.ItemInnerSpacing.value1, item_rect[1] + (((item_rect_max[1] - item_rect_min[1]) - line_height) / 2), width - checkbox_rect[2] - 4, item_rect[3])

                state = TextureState.Disabled if not enabled else TextureState.Active if PyImGui.is_item_active() else TextureState.Normal

                (ThemeTextures.CheckBox_Checked if is_checked else ThemeTextures.CheckBox_Unchecked).value.get_texture().draw_in_drawlist(
                    checkbox_rect[0],
                    checkbox_rect[1],
                    (checkbox_rect[2], checkbox_rect[3]),
                    tint=(255, 255, 255, 255),
                    state=state,
                )

                display_label = label.split("##")[0]
                PyImGui.draw_list_add_text(
                    text_rect[0],
                    text_rect[1],
                    style.Text.get_current().color_int,
                    display_label
                )

            case _:
                new_value = PyImGui.checkbox(label, is_checked)

        PyImGui.end_disabled()
        
        style.FrameRounding.pop_style_var()
        style.FramePadding.pop_style_var()
        style.ItemInnerSpacing.pop_style_var()

        return new_value

    @staticmethod
    def radio_button(label: str, v: int, button_index: int):
        style = ImGui.get_style()
        style.FramePadding.get_current().push_style_var()
        style.ItemInnerSpacing.get_current().push_style_var()
        style.ItemSpacing.get_current().push_style_var()
        
        match style.Theme:
            case Style.StyleTheme.Guild_Wars:
                value = PyImGui.radio_button(label, v, button_index)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0]
                height = item_rect_max[1] - item_rect_min[1]
                
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                active = PyImGui.is_item_active()
                GameTextures.CircleButtons.value.draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (item_rect[3], item_rect[3]),
                    state=TextureState.Active if v == button_index else TextureState.Normal,
                    tint= (255, 255, 255, 255) if active else (235, 235, 235, 255) if v == button_index else (180, 180, 180, 255)
                )
                if button_index == v:
                    pad = 5
                    
                    GameTextures.Quest_Objective_Bullet_Point.value.draw_in_drawlist(
                    item_rect[0] + (height / 4),
                    item_rect[1] + (height / 4),
                    (int(height / 2), int(height / 2)),
                    state=TextureState.Normal,
                    tint= (255, 255, 255, 255) if active else (235, 235, 235, 255) if v == button_index else (180, 180, 180, 255)
                )
                    PyImGui.draw_list_add_circle_filled(
                        item_rect[0] + (height / 2),
                        item_rect[1] + (height / 2),
                        (item_rect[3] - (pad * 2)) / 2.5,
                        Utils.RGBToColor(207, 191, 143, 180),
                        int(height / 3)
                    )
                    
                    PyImGui.draw_list_add_circle(
                        item_rect[0] + (height / 2),
                        item_rect[1] + (height / 2),
                        (item_rect[3] - (pad * 2)) / 2.5,
                        Utils.RGBToColor(0,0,0,180),
                        int(height / 3),
                        1
                    )

            case _:
                value = PyImGui.radio_button(label, v, button_index)

        style.FramePadding.pop_style_var()
        style.ItemInnerSpacing.pop_style_var()
        style.ItemSpacing.pop_style_var()
        return value

    @staticmethod
    def input_int(label: str, v: int, min_value: int = 0, step_fast: int = 0, flags: int = 0) -> int:
        style = ImGui.get_style()
        style.FrameRounding.get_current().push_style_var()  

        current_frame_padding = style.FramePadding.get_current()
        current_frame_padding.push_style_var()

        current_inner_spacing = style.ItemInnerSpacing.get_current()
        current_inner_spacing.push_style_var()
        
        style.ItemSpacing.get_current().push_style_var()
        
        if not min_value and not step_fast and not flags:
            match(style.Theme):
                case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                    x,y = PyImGui.get_cursor_screen_pos()
                    
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))
                    
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                    PyImGui.push_clip_rect(0, 0, 0, 0, False)
                    new_value = PyImGui.input_int(label + "##2", v, min_value, step_fast, flags)
                    PyImGui.pop_clip_rect()
                    PyImGui.pop_style_color(1)
                    
                    display_label = label.split("##")[0]
                    display_label = display_label or " "
                    label_size = PyImGui.calc_text_size(display_label)

                    item_rect_min = PyImGui.get_item_rect_min()
                    item_rect_max = PyImGui.get_item_rect_max()
                    height = item_rect_max[1] - item_rect_min[1]

                    label_rect = (item_rect_max[0] - (label_size[0] if label_size[0] > 0 else 0), item_rect_min[1] + ((height - label_size[1]) / 2) + 2, label_size[0], label_size[1])
                    
                    button_size = height
                    increase_rect = (label_rect[0] - current_inner_spacing.value1 - (button_size), item_rect_min[1], button_size, button_size)
                    decrease_rect = (increase_rect[0] - current_inner_spacing.value1 - (button_size), increase_rect[1], button_size, button_size)

                    width = (label_rect[0] - current_inner_spacing.value1) - item_rect_min[0]
                    item_rect = (item_rect_min[0], item_rect_min[1], width, height)

                    inputfield_size = ((decrease_rect[0] - current_inner_spacing.value1) - item_rect_min[0] , item_rect[3])

                    # (GameTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.draw_in_drawlist(
                    (ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
                        item_rect[0],
                        item_rect[1],
                        inputfield_size,
                        tint=(255, 255, 255, 255),
                    )
                    
                    if PyImGui.is_rect_visible(width, height):
                        PyImGui.set_item_allow_overlap()
                        
                        
                    PyImGui.set_cursor_screen_pos(decrease_rect[0], decrease_rect[1])
                    PyImGui.invisible_button(f"{label}##decrease", decrease_rect[2], decrease_rect[3])
                    
                    if PyImGui.is_item_clicked(0):
                        new_value -= 1
                                        
                    PyImGui.set_cursor_screen_pos(increase_rect[0], increase_rect[1])
                    PyImGui.invisible_button(f"{label}##increase", increase_rect[2], increase_rect[3])

                    if PyImGui.is_item_clicked(0):
                        new_value += 1

                    PyImGui.set_cursor_screen_pos(x, y)
                    new_value = PyImGui.input_int(label, new_value, min_value, step_fast, flags)
                    PyImGui.pop_style_color(6)

                    
                    draw_pad = 3
                    ThemeTextures.Collapse.value.get_texture().draw_in_drawlist(
                        decrease_rect[0] + draw_pad,
                        decrease_rect[1] + draw_pad + 1,
                        (button_size - draw_pad*2, button_size - draw_pad*2),
                        state=TextureState.Hovered if ImGui.is_mouse_in_rect(decrease_rect) else TextureState.Normal,
                        tint=(255, 255, 255, 255),
                    )
                    ThemeTextures.Expand.value.get_texture().draw_in_drawlist(
                        increase_rect[0] + draw_pad,
                        increase_rect[1] + draw_pad + 1,
                        (button_size - draw_pad*2, button_size - draw_pad*2),
                        state=TextureState.Hovered if ImGui.is_mouse_in_rect(increase_rect) else TextureState.Normal,
                        tint=(255, 255, 255, 255),
                    )
                    
                case _:
                    new_value = PyImGui.input_int(label, v)
                    
        else:
            match(style.Theme):
                case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                    x,y = PyImGui.get_cursor_screen_pos()
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                    PyImGui.push_clip_rect(0, 0, 0, 0, False)
                    new_value = PyImGui.input_int(label + "##2", v, min_value, step_fast, flags)
                    PyImGui.pop_clip_rect()
                    PyImGui.pop_style_color(1)

                    item_rect_min = PyImGui.get_item_rect_min()
                    item_rect_max = PyImGui.get_item_rect_max()
                    height = item_rect_max[1] - item_rect_min[1]

                    display_label = label.split("##")[0]
                    label_size = PyImGui.calc_text_size(display_label)

                    label_rect = (item_rect_max[0] - (label_size[0] if label_size[0] > 0 else 0), item_rect_min[1] + ((height - label_size[1]) / 2) + 2, label_size[0], label_size[1])

                    width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + 6 if label_size[0] > 0 else 0)
                    item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                    
                    inputfield_size = ((label_rect[0] - current_inner_spacing.value1) - item_rect_min[0] , item_rect[3])
                    
                    # (GameTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.draw_in_drawlist(
                    (ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
                        item_rect[0],
                        item_rect[1],
                        (inputfield_size[0] + 1, inputfield_size[1]),
                        tint=(255, 255, 255, 255),
                    )
                    
                    PyImGui.set_item_allow_overlap()
                    PyImGui.push_clip_rect(item_rect[0], item_rect[1], item_rect_max[0]- item_rect_min[0], item_rect[3] - 2, True)
                    PyImGui.set_cursor_screen_pos(x, y)
                    PyImGui.push_item_width(inputfield_size[0])
                    new_value = PyImGui.input_int(label, new_value, min_value, step_fast, flags)
                    PyImGui.pop_item_width()
                    PyImGui.pop_clip_rect()
                    PyImGui.pop_style_color(6)

                case _:
                    new_value = PyImGui.input_int(label, v, min_value, step_fast, flags)
        
        style.FrameRounding.pop_style_var()
        style.FramePadding.pop_style_var()
        style.ItemInnerSpacing.pop_style_var()
        style.ItemSpacing.pop_style_var()

        return new_value

    @staticmethod
    def input_text(label: str, v: str, flags: int = 0) -> str:
        style = ImGui.get_style()
        style.FrameRounding.get_current().push_style_var()      
        style.ItemSpacing.get_current().push_style_var()

        current_frame_padding = style.FramePadding.get_current()
        current_frame_padding.push_style_var()

        current_inner_spacing = style.ItemInnerSpacing.get_current()
        current_inner_spacing.push_style_var()

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                x,y = PyImGui.get_cursor_screen_pos()
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_clip_rect(0, 0, 0, 0, False)
                new_value = PyImGui.input_text(label + "##2", v, flags)
                PyImGui.pop_clip_rect()
                PyImGui.pop_style_color(1)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                height = item_rect_max[1] - item_rect_min[1]

                display_label = label.split("##")[0]
                label_size = PyImGui.calc_text_size(display_label)

                label_rect = (item_rect_max[0] - (label_size[0] if label_size[0] > 0 else 0), item_rect_min[1] + ((height - label_size[1]) / 2) + 2, label_size[0], label_size[1])

                width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + 6 if label_size[0] > 0 else 0)
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                
                inputfield_size = ((label_rect[0] - current_inner_spacing.value1) - item_rect_min[0] , item_rect[3])
                
                # (GameTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.draw_in_drawlist(
                (ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (inputfield_size[0] + 1, inputfield_size[1]),
                    tint=(255, 255, 255, 255),
                )
                
                PyImGui.set_item_allow_overlap()
                PyImGui.push_clip_rect(item_rect[0], item_rect[1], item_rect_max[0]- item_rect_min[0], item_rect[3] - 2, True)
                PyImGui.set_cursor_screen_pos(x, y)
                PyImGui.push_item_width(inputfield_size[0])
                new_value = PyImGui.input_text(label, new_value, flags)
                PyImGui.pop_item_width()
                PyImGui.pop_clip_rect()
                PyImGui.pop_style_color(6)

            case _: 
                new_value = PyImGui.input_text(label, v, flags)

        style.FrameRounding.pop_style_var()
        style.FramePadding.pop_style_var()
        style.ItemInnerSpacing.pop_style_var()
        style.ItemSpacing.pop_style_var()
        return new_value

    @staticmethod
    def input_float(label: str, v: float) -> float:
        style = ImGui.get_style()
        style.FrameRounding.get_current().push_style_var()      
        style.ItemSpacing.get_current().push_style_var()

        current_frame_padding = style.FramePadding.get_current()
        current_frame_padding.push_style_var()

        current_inner_spacing = style.ItemInnerSpacing.get_current()
        current_inner_spacing.push_style_var()
        
        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                x,y = PyImGui.get_cursor_screen_pos()
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_clip_rect(0, 0, 0, 0, False)
                new_value = PyImGui.input_float(label + "##2", v)
                PyImGui.pop_clip_rect()
                PyImGui.pop_style_color(1)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                height = item_rect_max[1] - item_rect_min[1]

                display_label = label.split("##")[0]
                label_size = PyImGui.calc_text_size(display_label)

                label_rect = (item_rect_max[0] - (label_size[0] if label_size[0] > 0 else 0), item_rect_min[1] + ((height - label_size[1]) / 2) + 2, label_size[0], label_size[1])

                width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + 6 if label_size[0] > 0 else 0)
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                
                inputfield_size = ((label_rect[0] - current_inner_spacing.value1) - item_rect_min[0] , item_rect[3])
                
                # (GameTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.draw_in_drawlist(
                (ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (inputfield_size[0] + 1, inputfield_size[1]),
                    tint=(255, 255, 255, 255),
                )
                
                PyImGui.set_item_allow_overlap()
                PyImGui.push_clip_rect(item_rect[0], item_rect[1], item_rect_max[0]- item_rect_min[0], item_rect[3] - 2, True)
                PyImGui.set_cursor_screen_pos(x, y)
                PyImGui.push_item_width(inputfield_size[0])
                new_value = PyImGui.input_float(label, new_value)
                PyImGui.pop_item_width()
                PyImGui.pop_clip_rect()
                PyImGui.pop_style_color(6)

            case _: 
                new_value = PyImGui.input_float(label, v)

        style.FrameRounding.pop_style_var()
        style.FramePadding.pop_style_var()
        style.ItemInnerSpacing.pop_style_var()
        style.ItemSpacing.pop_style_var()
        
        return new_value
    
    @staticmethod
    def slider_int(label: str, v: int, v_min: int, v_max: int) -> int:
        style = ImGui.get_style()

        style.FrameRounding.get_current().push_style_var()  
        style.FramePadding.get_current().push_style_var()     
        style.GrabRounding.get_current().push_style_var()    
        style.GrabMinSize.get_current().push_style_var() 
        style.ItemInnerSpacing.get_current().push_style_var()          
        style.ItemSpacing.get_current().push_style_var()          
        
        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                pad = style.FramePadding.get_current()
                grab_width = (pad.value2 or 0) + 18 - 5
                
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.GrabMinSize, grab_width)
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0,0,0,0))
                new_value = PyImGui.slider_int(label, v, v_min, v_max)

                PyImGui.pop_style_color(6)

                display_label = label.split("##")[0]
                label_size = PyImGui.calc_text_size(display_label)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + style.ItemInnerSpacing.value1 if label_size[0] > 0 else 0)
                height = item_rect_max[1] - item_rect_min[1]
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)

                ThemeTextures.SliderBar.value.get_texture().draw_in_drawlist(
                    item_rect[0],
                    item_rect[1] + 4,
                    (item_rect[2], item_rect[3] - 8),
                    tint=(255, 255, 255, 255),
                )

                percent = (new_value - v_min) / (v_max - v_min)
                track_width = item_rect[2] - 12 - grab_width
                grab_size = (grab_width, grab_width)
                grab_rect = ((item_rect[0] + 6) + track_width * percent, item_rect[1] + (height - grab_size[1]) / 2, *grab_size)
                PyImGui.draw_list_add_rect(
                    grab_rect[0] - 1,
                    grab_rect[1] - 1,
                    grab_rect[0] + grab_rect[2] + 1,
                    grab_rect[1] + grab_rect[3] + 1,
                    Utils.RGBToColor(0, 0, 0, 170),
                    0,
                    0,
                    1,
                )
                PyImGui.draw_list_add_rect(
                    grab_rect[0] - 2,
                    grab_rect[1] - 2,
                    grab_rect[0] + grab_rect[2] + 2,
                    grab_rect[1] + grab_rect[3] + 2,
                    Utils.RGBToColor(0, 0, 0, 100),
                    0,
                    0,
                    1,
                )
        
                ThemeTextures.SliderGrab.value.get_texture().draw_in_drawlist(
                    grab_rect[0],
                    grab_rect[1],
                    grab_rect[2:],
                )
                
                if display_label:
                    text_x = (item_rect[0] + item_rect[2]) + style.ItemInnerSpacing.value1
                    text_y = item_rect[1] + ((height - label_size[1] - 2) / 2)

                    PyImGui.draw_list_add_text(
                        text_x,
                        text_y,
                        style.Text.color_int,
                        display_label,
                    )

            case _:
                new_value = PyImGui.slider_int(label, v, v_min, v_max)


        style.FrameRounding.pop_style_var()  
        style.FramePadding.pop_style_var()     
        style.GrabRounding.pop_style_var()
        style.GrabMinSize.pop_style_var()
        style.ItemInnerSpacing.pop_style_var()
        style.ItemSpacing.pop_style_var()
        return new_value
    
    @staticmethod
    def slider_float(label: str, v: float, v_min: float, v_max: float) -> float:
        style = ImGui.get_style()

        style.FrameRounding.get_current().push_style_var()  
        style.FramePadding.get_current().push_style_var()     
        style.GrabRounding.get_current().push_style_var()    
        style.GrabMinSize.get_current().push_style_var() 
        style.ItemInnerSpacing.get_current().push_style_var()          
        style.ItemSpacing.get_current().push_style_var()          
        
        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                pad = style.FramePadding.get_current()
                grab_width = (pad.value2 or 0) + 18 - 5
                
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.GrabMinSize, grab_width)
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0,0,0,0))
                new_value = PyImGui.slider_float(label, v, v_min, v_max)

                PyImGui.pop_style_color(6)

                display_label = label.split("##")[0]
                label_size = PyImGui.calc_text_size(display_label)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + style.ItemInnerSpacing.value1 if label_size[0] > 0 else 0)
                height = item_rect_max[1] - item_rect_min[1]
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)

                ThemeTextures.SliderBar.value.get_texture().draw_in_drawlist(
                    item_rect[0],
                    item_rect[1] + 4,
                    (item_rect[2], item_rect[3] - 8),
                    tint=(255, 255, 255, 255),
                )

                percent = (new_value - v_min) / (v_max - v_min)
                track_width = item_rect[2] - 12 - grab_width
                grab_size = (grab_width, grab_width)
                grab_rect = ((item_rect[0] + 6) + track_width * percent, item_rect[1] + (height - grab_size[1]) / 2, *grab_size)
                PyImGui.draw_list_add_rect(
                    grab_rect[0] - 1,
                    grab_rect[1] - 1,
                    grab_rect[0] + grab_rect[2] + 1,
                    grab_rect[1] + grab_rect[3] + 1,
                    Utils.RGBToColor(0, 0, 0, 170),
                    0,
                    0,
                    1,
                )
                PyImGui.draw_list_add_rect(
                    grab_rect[0] - 2,
                    grab_rect[1] - 2,
                    grab_rect[0] + grab_rect[2] + 2,
                    grab_rect[1] + grab_rect[3] + 2,
                    Utils.RGBToColor(0, 0, 0, 100),
                    0,
                    0,
                    1,
                )
        
                ThemeTextures.SliderGrab.value.get_texture().draw_in_drawlist(
                    grab_rect[0],
                    grab_rect[1],
                    grab_rect[2:],
                )
                
                if display_label:
                    text_x = (item_rect[0] + item_rect[2]) + style.ItemInnerSpacing.value1
                    text_y = item_rect[1] + ((height - label_size[1] - 2) / 2)

                    PyImGui.draw_list_add_text(
                        text_x,
                        text_y,
                        style.Text.color_int,
                        display_label,
                    )

            case _:
                new_value = PyImGui.slider_float(label, v, v_min, v_max)


        style.FrameRounding.pop_style_var()  
        style.FramePadding.pop_style_var()     
        style.GrabRounding.pop_style_var()
        style.GrabMinSize.pop_style_var()
        style.ItemInnerSpacing.pop_style_var()
        style.ItemSpacing.pop_style_var()
        
        return new_value

    @staticmethod
    def separator():
        style = ImGui.get_style()

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars:
                PyImGui.push_clip_rect(0,0,0,0,False)
                PyImGui.separator()
                PyImGui.pop_clip_rect()

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0]
                height = item_rect_max[1] - item_rect_min[1]
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)

                GameTextures.Separator.value.draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (item_rect[2], item_rect[3]),
                )

            case _:
                PyImGui.separator()

    @staticmethod
    def hyperlink(text : str) -> bool:
        style = ImGui.get_style()
        
        style.Hyperlink.get_current().push_color()
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0,))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0,))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0,))
        clicked = PyImGui.button(text)
        PyImGui.pop_style_color(3)
        PyImGui.pop_style_var(1)

        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()
        
        width = item_rect_max[0] - item_rect_min[0]
        height = item_rect_max[1] - item_rect_min[1]
        item_rect = (item_rect_min[0], item_rect_min[1], width, height)
        
        PyImGui.draw_list_add_line(
            item_rect[0] - 1,
            item_rect[1] + item_rect[3] - 2,
            item_rect[0] + item_rect[2] + 2,
            item_rect[1] + item_rect[3] - 2,
            style.Hyperlink.get_current().color_int,
            1
        )
        
        style.Hyperlink.pop_color()
        
        return clicked

    @staticmethod
    def search_field(label: str, text : str, placeholder: str = "Search...", flags : int = PyImGui.InputTextFlags.NoFlag) -> tuple[bool, str]:
        style = ImGui.get_style()
        style.FrameRounding.get_current().push_style_var()
        
        current_frame_padding = style.FramePadding.get_current()
        current_frame_padding.push_style_var()

        current_inner_spacing = style.ItemInnerSpacing.get_current()
        current_inner_spacing.push_style_var()

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                x,y = PyImGui.get_cursor_screen_pos()
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_clip_rect(0, 0, 0, 0, False)
                new_value = PyImGui.input_text(label + "##2", text, flags)
                PyImGui.pop_clip_rect()
                PyImGui.pop_style_color(1)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                height = item_rect_max[1] - item_rect_min[1]

                display_label = label.split("##")[0]
                label_size = PyImGui.calc_text_size(display_label)

                label_rect = (item_rect_max[0] - (label_size[0] if label_size[0] > 0 else 0), item_rect_min[1] + ((height - label_size[1]) / 2) + 2, label_size[0], label_size[1])

                width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + 6 if label_size[0] > 0 else 0)
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                
                inputfield_size = ((label_rect[0] - current_inner_spacing.value1) - item_rect_min[0] , item_rect[3])

                # (GameTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.draw_in_drawlist(
                (ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (inputfield_size[0] + 1, inputfield_size[1]),
                    tint=(255, 255, 255, 255),
                )
                
                PyImGui.set_item_allow_overlap()
                PyImGui.push_clip_rect(item_rect[0], item_rect[1], item_rect_max[0]- item_rect_min[0], item_rect[3] - 2, True)
                PyImGui.set_cursor_screen_pos(x, y)
                PyImGui.push_item_width(inputfield_size[0])
                new_value = PyImGui.input_text(label, new_value, flags)
                PyImGui.pop_item_width()
                PyImGui.pop_clip_rect()
                PyImGui.pop_style_color(6)

            case _: 
                new_value = PyImGui.input_text(label, text, flags)
                
                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                display_label = label.split("##")[0]
                label_size = PyImGui.calc_text_size(display_label)
                
                width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + 8 if label_size[0] > 0 else 0)
                height = item_rect_max[1] - item_rect_min[1]
                item_rect = (item_rect_min[0], item_rect_min[1], width, height - 4)


        if not PyImGui.is_item_active() and not PyImGui.is_item_focused() and not text:
            search_font_size = int(height * 0.25) + 1
            padding = (height - search_font_size) / 2
                                
            ImGui.push_font("Regular", search_font_size)
            search_icon_size = PyImGui.calc_text_size(IconsFontAwesome5.ICON_SEARCH)
            PyImGui.draw_list_add_text(
                item_rect[0] + current_frame_padding.value1,
                item_rect[1] + padding,
                style.Text.color_int,
                IconsFontAwesome5.ICON_SEARCH,
            )
            ImGui.pop_font()
            
            if placeholder:
                placeholder_size = PyImGui.calc_text_size(placeholder)
                padding = (height - placeholder_size[1]) / 2
                
                PyImGui.draw_list_add_text(
                    item_rect[0] + current_frame_padding.value1 + search_icon_size[0] + 5,
                    item_rect[1] + padding + 1,
                    style.Text.color_int,
                    placeholder,
                )
                
        style.FrameRounding.pop_style_var()
        style.FramePadding.pop_style_var()
                
        return new_value != text, new_value

    @staticmethod
    def bullet_text(text: str):
        style = ImGui.get_style()
        frame_padding = style.FramePadding.get_current()
        frame_padding.push_style_var()
        
        match(style.Theme):
            case Style.StyleTheme.Guild_Wars:
                height = PyImGui.get_text_line_height()
                text_size = PyImGui.calc_text_size(text)
                cursor = PyImGui.get_cursor_screen_pos()

                PyImGui.push_clip_rect(cursor[0] + frame_padding.value1 + height, cursor[1], cursor[0] + frame_padding.value1 + text_size[0], text_size[1], True)
                PyImGui.bullet_text(text)
                PyImGui.pop_clip_rect()

                item_rect_min = PyImGui.get_item_rect_min()
                
                item_rect = (item_rect_min[0] + frame_padding.value1, item_rect_min[1] -2, height, height)
                GameTextures.BulletPoint.value.draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (item_rect[2], item_rect[3]),
                )

            case _:
                PyImGui.bullet_text(text)
            
        frame_padding.pop_style_var()

    @staticmethod
    def objective_text(text: str, completed: bool = False):
        style = ImGui.get_style()
        frame_padding = style.FramePadding.get_current()
        frame_padding.push_style_var()
        
        if completed:
            style.TextObjectiveCompleted.get_current().push_color()

        height = PyImGui.get_text_line_height()
        
        match(style.Theme):
            case Style.StyleTheme.Guild_Wars:
                text_size = PyImGui.calc_text_size(text)
                cursor = PyImGui.get_cursor_screen_pos()

                PyImGui.push_clip_rect(cursor[0] + frame_padding.value1 + height, cursor[1], cursor[0] + frame_padding.value1 + text_size[0], text_size[1], True)
                PyImGui.bullet_text(text)
                PyImGui.pop_clip_rect()

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()

                item_rect = (item_rect_min[0] + frame_padding.value1, item_rect_min[1] -2, height, height)
                
                GameTextures.Quest_Objective_Bullet_Point.value.draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (item_rect[2], item_rect[3]),
                    state=TextureState.Normal if completed else TextureState.Active,
                )

            case _:
                PyImGui.bullet_text(text)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()

                item_rect = (item_rect_min[0] + 4, item_rect_min[1] -2, height, height)
            
        
        if completed:
            PyImGui.draw_list_add_line(
                item_rect[0] + item_rect[2] + (frame_padding.value1 * 2) - 5,
                item_rect[1] + (item_rect[3] / 2) + 1,
                item_rect_max[0],
                item_rect[1] + (item_rect[3] / 2) + 1,
                style.TextObjectiveCompleted.color_int,
                1,
            )
            style.TextObjectiveCompleted.pop_color()
            
        frame_padding.pop_style_var()
        
        if PyImGui.is_item_clicked(0):
            completed = not completed
        
        return completed

    @staticmethod
    def collapsing_header(label: str, flags: int = 0) -> bool:
        style = ImGui.get_style()
        style.FrameRounding.get_current().push_style_var()
        style.TextCollapsingHeader.get_current().push_color()
        
        frame_padding = style.FramePadding.get_current()
        frame_padding.push_style_var()
        
        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Header, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, (0,0,0,0))
                
                PyImGui.push_clip_rect(PyImGui.get_cursor_screen_pos()[0]+ 20, PyImGui.get_cursor_screen_pos()[1], 1000, 1000, True)
                new_open = PyImGui.collapsing_header(label, flags)
                PyImGui.pop_clip_rect()
                
                PyImGui.pop_style_color(3)
                
                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                height = PyImGui.get_text_line_height()
                padding = ((item_rect_max[1] - item_rect_min[1]) - height) / 2                
                item_rect = (item_rect_min[0] + frame_padding.value1, item_rect_min[1] + padding, height, height)

                (ThemeTextures.Collapse if new_open else ThemeTextures.Expand).value.get_texture().draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (item_rect[2], item_rect[3]),
                    state=TextureState.Hovered if ImGui.is_mouse_in_rect(item_rect) else TextureState.Normal,
                )                           
                
            case _:
                new_open = PyImGui.collapsing_header(label, flags)

        style.TextCollapsingHeader.pop_color()
        style.FramePadding.pop_style_var()
        style.FrameRounding.pop_style_var()

        return new_open
    
    @staticmethod
    def tree_node(label: str) -> bool:
        style = ImGui.get_style()
        style.FrameRounding.get_current().push_style_var()
        style.TextTreeNode.get_current().push_color()
        
        frame_padding = style.FramePadding.get_current()
        frame_padding.push_style_var()
        
        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Header, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, (0,0,0,0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, (0,0,0,0))
                PyImGui.push_clip_rect(PyImGui.get_cursor_screen_pos()[0]+ 20, PyImGui.get_cursor_screen_pos()[1], 1000, 1000, True)
                new_open = PyImGui.tree_node(label)
                PyImGui.pop_clip_rect()

                PyImGui.pop_style_color(3)
                
                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                height = PyImGui.get_text_line_height()
                padding = ((item_rect_max[1] - item_rect_min[1]) - height) / 2                
                item_rect = (item_rect_min[0] + frame_padding.value1, item_rect_min[1] + padding, height, height)

                (ThemeTextures.Collapse if new_open else ThemeTextures.Expand).value.get_texture().draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (item_rect[2], item_rect[3]),
                    state=TextureState.Hovered if ImGui.is_mouse_in_rect(item_rect) else TextureState.Normal,
                )
                                
                
            case _:
                new_open = PyImGui.tree_node(label)

        style.TextTreeNode.pop_color()
        style.FramePadding.pop_style_var()
        style.FrameRounding.pop_style_var()

        return new_open
    
    @staticmethod
    def tree_pop():
        PyImGui.tree_pop()
        
    @staticmethod
    def begin_tab_bar(str_id: str) -> bool:
        style = ImGui.get_style()
        style.TabRounding.get_current().push_style_var()

        match(style.Theme):
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:                
                PyImGui.push_clip_rect(0,0,0,0,False)
                open = PyImGui.begin_tab_bar(str_id)
                PyImGui.pop_clip_rect()

                pos = PyImGui.get_cursor_screen_pos()
                width, height = PyImGui.get_content_region_avail()

                item_rect = (pos[0] - 3, pos[1] -6, width + 4, height + 6)
                
                PyImGui.push_clip_rect(item_rect[0] - 3, item_rect[1]-2, item_rect[2] + 6, item_rect[3] + 4, False)
                
                ThemeTextures.Tab_Frame_Top.value.get_texture().draw_in_drawlist(
                    item_rect[0] - (3 if style.Theme == Style.StyleTheme.Guild_Wars else 0),
                    item_rect[1],
                    (item_rect[2] + (6 if style.Theme == Style.StyleTheme.Guild_Wars else 0),
                    4),
                )
                
                ThemeTextures.Tab_Frame_Body.value.get_texture().draw_in_drawlist(
                    item_rect[0] - (3 if style.Theme == Style.StyleTheme.Guild_Wars else 0),
                    item_rect[1] + 4,
                    (item_rect[2] + (6 if style.Theme == Style.StyleTheme.Guild_Wars else 0),
                    item_rect[3] - 4),
                )
                
                PyImGui.pop_clip_rect()
            case _:
                open = PyImGui.begin_tab_bar(str_id)

        style.TabRounding.pop_style_var()
        return open
                
    @staticmethod
    def end_tab_bar():
        PyImGui.end_tab_bar()

    @staticmethod
    def begin_tab_item(label: str, popen: bool | None = None, flags:int = 0) -> bool:
        style = ImGui.get_style()
        style.TabRounding.get_current().push_style_var()
        
        if popen is None:
            match(style.Theme):
                case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Tab, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.TabActive, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.TabHovered, (0, 0, 0, 0))
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                    open = PyImGui.begin_tab_item(label)
                    PyImGui.pop_style_color(4)

                    item_rect_min = PyImGui.get_item_rect_min()
                    item_rect_max = PyImGui.get_item_rect_max()
                    
                    enlarged_by = 5
                    width = item_rect_max[0] - item_rect_min[0] + 12
                    height = item_rect_max[1] - item_rect_min[1] + 3
                    item_rect = (item_rect_min[0] - 4, item_rect_min[1] - (enlarged_by if open else 0), width, height + (enlarged_by if open else 0))
                    
                    PyImGui.push_clip_rect(
                        item_rect[0],
                        item_rect[1],
                        width,
                        item_rect[3],
                        True
                    )
                    
                    (ThemeTextures.Tab_Active if open else ThemeTextures.Tab_Inactive).value.get_texture().draw_in_drawlist(
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
                    
                    (ThemeTextures.Tab_Active if open else ThemeTextures.Tab_Inactive).value.get_texture().draw_in_drawlist(
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
                    
                case _:
                    open = PyImGui.begin_tab_item(label, popen, flags)

        style.TabRounding.pop_style_var()
        return open

    @staticmethod
    def end_tab_item():
        PyImGui.end_tab_item()

    @staticmethod
    def begin_child(id : str, size : tuple[float, float] = (0, 0), border: bool = False, flags: int = PyImGui.WindowFlags.NoFlag) -> bool:
        style = ImGui.get_style()
        style.ScrollbarSize.get_current().push_style_var()
        style.ScrollbarRounding.get_current().push_style_var()
        
        open = PyImGui.begin_child(id, size, border, flags)
        
        style.ScrollbarSize.pop_style_var()
        style.ScrollbarRounding.pop_style_var()
                
        return open

    @staticmethod
    def end_child():
        PyImGui.end_child()

    @staticmethod
    def draw_vertical_scroll_bar(scroll_bar_size : float, force_scroll_bar : bool = False, window_rect: Optional[tuple[float, float, float, float]] = None, border_padding: bool = False):
        scroll_max_y = PyImGui.get_scroll_max_y()
        scroll_y = PyImGui.get_scroll_y()

        parent_window_size = PyImGui.get_window_size()
        parent_window_pos = PyImGui.get_window_pos()
        window_rect = window_rect or (parent_window_pos[0], parent_window_pos[1], parent_window_pos[0] + parent_window_size[0], parent_window_pos[1] + parent_window_size[1])
        
        if force_scroll_bar or scroll_max_y > 0:
            window_padding = ((2), (5) if border_padding else 0, 0)
            visible_size_y = PyImGui.get_window_height()
            item_rect_min = PyImGui.get_item_rect_min()
            item_rect_max = PyImGui.get_item_rect_max()

            window_clip = (
                window_rect[0],
                window_rect[1],
                window_rect[2] - window_rect[0],
                window_rect[3] - window_rect[1]
            )

            scroll_bar_rect = (item_rect_max[0] - scroll_bar_size - window_padding[0], item_rect_min[1] + window_padding[1], item_rect_max[0] - window_padding[0], item_rect_min[1] + visible_size_y - window_padding[1])

            track_height = scroll_bar_rect[3] - scroll_bar_rect[1]
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

    @staticmethod
    def draw_horizontal_scroll_bar(scroll_bar_size: float, force_scroll_bar: bool = False, window_rect: Optional[tuple[float, float, float, float]] = None, border_padding: bool = False):
        scroll_max_x = PyImGui.get_scroll_max_x()
        scroll_max_y = PyImGui.get_scroll_max_y()
        scroll_x = PyImGui.get_scroll_x()

        parent_window_size = PyImGui.get_window_size()
        parent_window_pos = PyImGui.get_window_pos()
        window_rect = window_rect or (parent_window_pos[0], parent_window_pos[1], parent_window_pos[0] + parent_window_size[0], parent_window_pos[1] + parent_window_size[1])
        
        if force_scroll_bar or scroll_max_x > 0:
            window_padding = ((7), (2) if border_padding else 0, 0)
            visible_size_x = PyImGui.get_window_width()
            visible_size_y = PyImGui.get_window_height()
            
            item_rect_min = PyImGui.get_item_rect_min()

            window_clip = (
                window_rect[0],
                window_rect[1],
                window_rect[2] - window_rect[0],
                window_rect[3] - window_rect[1]
            )
            
            scroll_bar_rect = (
                item_rect_min[0] + window_padding[0], 
                item_rect_min[1] + visible_size_y - scroll_bar_size + window_padding[1] - window_padding[1],
                item_rect_min[0] + visible_size_x - (scroll_bar_size + 2 if scroll_max_y > 0 else 0) - window_padding[0], 
                item_rect_min[1] + visible_size_y - window_padding[1]
                )

            scroll_bar_rect = (
                item_rect_min[0] + window_padding[0], 
                item_rect_min[1] + visible_size_y - scroll_bar_size - window_padding[1],
                item_rect_min[0] + visible_size_x - 10 - (scroll_bar_size + 2 if scroll_max_y > 0 else 0) - window_padding[0], 
                item_rect_min[1] + visible_size_y - window_padding[1]
                )
            
            track_width = scroll_bar_rect[2] - scroll_bar_rect[0] + (window_padding[0] * 2)
            thumb_min = 5.0
            
            if scroll_max_x > 0:
                thumb_width = (track_width * track_width) / (track_width + scroll_max_x)
                thumb_width = max(thumb_width, thumb_min)
            else:
                thumb_width = track_width   # all content fits, thumb covers track
                
            # Thumb size (clamped)
            thumb_width = max(thumb_width, thumb_min)
            
            # Thumb offset
            thumb_offset = 0
            if scroll_max_x > 0:
                thumb_offset = (scroll_x / scroll_max_x) * (track_width - thumb_width)

            scroll_grab_rect = (
                scroll_bar_rect[0] + thumb_offset,
                scroll_bar_rect[1],
                thumb_width - 1,
                scroll_bar_size,
            )

            PyImGui.push_clip_rect(
                window_clip[0] - 5 ,
                window_clip[1] - 5,
                window_clip[2] + 5,
                window_clip[3] + 10,
                False  # intersect with current clip rect (safe, window always bigger than content)
            )
            
                
            GameTextures.Horizontal_Scroll_Bg.value.draw_in_drawlist(
                scroll_bar_rect[0] + 3,
                scroll_bar_rect[1],
                (scroll_bar_rect[2] - scroll_bar_rect[0] - 5, scroll_bar_rect[3] - scroll_bar_rect[1]),
            )
                    
            GameTextures.Horizontal_ScrollGrab_Middle.value.draw_in_drawlist(
                scroll_grab_rect[0] + 5, 
                scroll_grab_rect[1],
                (scroll_grab_rect[2] - 10, scroll_grab_rect[3]),
                tint=(195, 195, 195, 255)
            )
            
            GameTextures.Horizontal_ScrollGrab_Top.value.draw_in_drawlist(
                scroll_grab_rect[0], 
                scroll_grab_rect[1], 
                (7, scroll_grab_rect[3]),
            )
            
            GameTextures.Horizontal_ScrollGrab_Bottom.value.draw_in_drawlist(
                scroll_grab_rect[0] + scroll_grab_rect[2] - 7, 
                scroll_grab_rect[1], 
                (7, scroll_grab_rect[3]),
            )

            
            GameTextures.LeftButton.value.draw_in_drawlist(
                scroll_bar_rect[0] - 5, 
                scroll_bar_rect[1] - 1, 
                (scroll_bar_size, scroll_bar_size + 1),
            )
            
            GameTextures.RightButton.value.draw_in_drawlist(
                scroll_bar_rect[2] - 5 + (0 if scroll_max_y > 0 else 1), 
                scroll_bar_rect[1] - 1, 
                (scroll_bar_size, scroll_bar_size + 1),
            )

            PyImGui.pop_clip_rect()

    @staticmethod
    def begin_table(id: str, columns: int, flags: int = PyImGui.TableFlags.NoFlag, width: float = 0, height: float = 0) -> bool:
        style = ImGui.get_style()
        
        style.ScrollbarSize.get_current().push_style_var()
        style.ScrollbarRounding.get_current().push_style_var()
        
        open = PyImGui.begin_table(id, columns, flags, width, height)
        
        style.ScrollbarSize.pop_style_var()
        style.ScrollbarRounding.pop_style_var()
        
        return open

    @staticmethod
    def end_table():
        PyImGui.end_table()
        
    @staticmethod
    def progress_bar(fraction: float, size_arg_x: float, size_arg_y: float, overlay: str = ""):
        style = ImGui.get_style()
        style.FrameRounding.get_current().push_style_var()
        style.ItemSpacing.get_current().push_style_var()
        
        match(style.Theme):
            case Style.StyleTheme.Guild_Wars:
                PyImGui.push_clip_rect(0,0,0,0,False)
                PyImGui.progress_bar(fraction, size_arg_x, size_arg_y, overlay)
                PyImGui.pop_clip_rect()
                
                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                width = item_rect_max[0] - item_rect_min[0]
                height = item_rect_max[1] - item_rect_min[1]
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)

                progress_rect = (item_rect[0] + 1, item_rect[1] + 1, (width -2) * fraction, height - 2)
                background_rect = (item_rect[0] + 1, item_rect[1] + 1, width - 2, height - 2)
                cursor_rect = (item_rect[0] - 2 + (width - 2) * fraction, item_rect[1] + 1, 4, height - 2) if fraction > 0 else (item_rect[0] + (width - 2) * fraction, item_rect[1] + 1, 4, height - 2)

                tint = style.PlotHistogram.get_current().rgb_tuple
                
                GameTextures.ProgressBarBackground.value.draw_in_drawlist(
                    background_rect[0],
                    background_rect[1],
                    (background_rect[2], background_rect[3]),
                    tint=tint
                )
                
                GameTextures.ProgressBarProgress.value.draw_in_drawlist(
                    progress_rect[0],
                    progress_rect[1],
                    (progress_rect[2], progress_rect[3]),
                    tint=tint
                )
                
                if fraction > 0:
                    GameTextures.ProgressBarProgressCursor.value.draw_in_drawlist(
                        cursor_rect[0],
                        cursor_rect[1],
                        (cursor_rect[2], cursor_rect[3]),
                        tint=(200, 200, 200, 255)
                    )
                
                PyImGui.draw_list_add_rect(
                    item_rect[0],
                    item_rect[1],
                    item_rect[0] + item_rect[2],
                    item_rect[1] + item_rect[3],
                    Utils.RGBToColor(96, 92, 87, 255),
                    0,
                    0,
                    2
                )
                
                if overlay:
                    display_label = overlay.split("##")[0]
                    textsize = PyImGui.calc_text_size(display_label)
                    text_rect = (item_rect[0] + ((width - textsize[0]) / 2), item_rect[1] + ((height - textsize[1]) / 2) + 2, textsize[0], textsize[1])

                    PyImGui.draw_list_add_text(
                        text_rect[0],
                        text_rect[1],
                        style.Text.color_int,
                        display_label,
                    )


            case _:                
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.progress_bar(fraction, size_arg_x, size_arg_y, overlay)
                PyImGui.pop_style_color(1)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()       
                center = item_rect_min[0] + ((item_rect_max[0] - item_rect_min[0]) / 2), item_rect_min[1] + ((item_rect_max[1] - item_rect_min[1]) / 2)    
                
                text_width, text_height = PyImGui.calc_text_size(overlay)
                PyImGui.set_cursor_screen_pos(center[0] - (text_width / 2), center[1] - (text_height / 2))
                
                style.Text.get_current().push_color()
                PyImGui.text(overlay)
                style.Text.pop_color()
                
        style.FrameRounding.pop_style_var()
        style.ItemSpacing.pop_style_var()

    # endregion

    pass


def configure():
    window_module.open = True


textures = [
    ("Textures/Item Models/[17081] - Battle Commendation.png",
     ControlAppearance.Default, True),
    ("Textures/Item Models/[514] - Molten Heart.png",
     ControlAppearance.Primary, True),
    ("Textures/Item Models/[35] - Bag.png", ControlAppearance.Danger, True),
    ("Textures/Item Models/[30855] - Bottle of Grog.png",
     ControlAppearance.Default, False),
]


def draw_button(theme: Style.StyleTheme):

    if ImGuiDev.button("Default" + "##" + theme.name):
        ConsoleLog(module_name, "Button clicked")
    PyImGui.same_line(0, 5)
    ImGuiDev.button("Primary" + "##" + theme.name,
                 appearance=ControlAppearance.Primary)
    PyImGui.same_line(0, 5)
    ImGuiDev.button("Danger" + "##" + theme.name,
                 appearance=ControlAppearance.Danger)
    PyImGui.same_line(0, 5)
    ImGuiDev.button("Disabled" + "##" + theme.name, enabled=False)


def draw_small_button(theme: Style.StyleTheme):
    if ImGuiDev.small_button("Default" + "##" + theme.name):
        ConsoleLog(module_name, "Small Button clicked")
    PyImGui.same_line(0, 5)
    ImGuiDev.small_button("Primary" + "##" + theme.name,
                       appearance=ControlAppearance.Primary)
    PyImGui.same_line(0, 5)
    ImGuiDev.small_button("Danger" + "##" + theme.name,
                       appearance=ControlAppearance.Danger)
    PyImGui.same_line(0, 5)
    ImGuiDev.small_button("Disabled" + "##" + theme.name, enabled=False)


def draw_icon_button(theme: Style.StyleTheme):
    if ImGuiDev.icon_button(IconsFontAwesome5.ICON_SYNC + " With Text" + "##" + theme.name):
        ConsoleLog(module_name, "Icon Button clicked")
    PyImGui.same_line(0, 5)
    ImGuiDev.icon_button(IconsFontAwesome5.ICON_SYNC + "##" + theme.name)
    PyImGui.same_line(0, 5)
    ImGuiDev.icon_button(IconsFontAwesome5.ICON_SYNC + "##" +
                      theme.name, appearance=ControlAppearance.Primary)
    PyImGui.same_line(0, 5)
    ImGuiDev.icon_button(IconsFontAwesome5.ICON_SYNC + "##" +
                      theme.name, appearance=ControlAppearance.Danger)
    PyImGui.same_line(0, 5)
    ImGuiDev.icon_button(
        IconsFontAwesome5.ICON_SYNC, enabled=False)


def draw_toggle_button(theme: Style.StyleTheme):
    preview.toggle_button_1 = ImGuiDev.toggle_button(
        ("On" if preview.toggle_button_1 else "Off") + "##Toggle" + theme.name, preview.toggle_button_1)
    PyImGui.same_line(0, 5)
    preview.toggle_button_2 = ImGuiDev.toggle_button(
        ("On" if preview.toggle_button_2 else "Off") + "##Toggle2" + theme.name, preview.toggle_button_2)
    PyImGui.same_line(0, 5)
    preview.toggle_button_3 = ImGuiDev.toggle_button(
        "Disabled" + "##Toggle3" + theme.name, preview.toggle_button_3, enabled=False)


def draw_image_toggle(theme: Style.StyleTheme):
    preview.image_toggle_button_1 = ImGuiDev.image_toggle_button(
        ("On" if preview.image_toggle_button_1 else "Off") + "##ImageToggle_1" + theme.name, textures[0][0], preview.image_toggle_button_1)
    PyImGui.same_line(0, 5)
    preview.image_toggle_button_2 = ImGuiDev.image_toggle_button(
        ("On" if preview.image_toggle_button_2 else "Off") + "##ImageToggle_2" + theme.name, textures[1][0], preview.image_toggle_button_2)
    PyImGui.same_line(0, 5)
    preview.image_toggle_button_3 = ImGuiDev.image_toggle_button(
        ("On" if preview.image_toggle_button_3 else "Off") + "##ImageToggle_3" + theme.name, textures[2][0], preview.image_toggle_button_3, enabled=False)


def draw_image_button(theme: Style.StyleTheme):
    for (texture, appearance, enabled) in textures:
        ImGuiDev.image_button("Image Button" + "##" + theme.name +
                           texture, texture, appearance=appearance, enabled=enabled)
        PyImGui.same_line(0, 5)


def draw_combo(theme: Style.StyleTheme):
    preview.combo = ImGuiDev.combo("Combo##" + theme.name, preview.combo, [
                                "Option 1", "Option 2", "Option 3"])


def draw_checkbox(theme: Style.StyleTheme):
    preview.checkbox_2 = ImGuiDev.checkbox(
        "##Checkbox 2" + "##" + theme.name, preview.checkbox_2)
    PyImGui.same_line(0, 5)
    preview.checkbox = ImGuiDev.checkbox(
        "Checkbox" + "##" + theme.name, preview.checkbox)


def draw_radio_button(theme: Style.StyleTheme):
    preview.radio_button = ImGuiDev.radio_button(
        "Option 1##Radio Button 1" + "##" + theme.name, preview.radio_button, 0)
    preview.radio_button = ImGuiDev.radio_button(
        "Option 2##Radio Button 2" + "##" + theme.name, preview.radio_button, 1)
    preview.radio_button = ImGuiDev.radio_button(
        "Option 3##Radio Button 3" + "##" + theme.name, preview.radio_button, 2)


def draw_slider(theme: Style.StyleTheme):
    preview.slider_int = ImGuiDev.slider_int(
        "Slider Int##" + theme.name, preview.slider_int, 0, 100)
    preview.slider_float = ImGuiDev.slider_float(
        "Slider Float##" + theme.name, preview.slider_float, 0.0, 100.0)


def draw_input(theme: Style.StyleTheme):
    changed, preview.search_value = ImGuiDev.search_field(
        "Search##" + theme.name, preview.search_value)
    preview.input_text_value = ImGuiDev.input_text(
        "Text##" + theme.name, preview.input_text_value)
    preview.input_float_value = ImGuiDev.input_float(
        "Float##" + theme.name, preview.input_float_value)
    preview.input_int_value = ImGuiDev.input_int(
        "Int##3" + theme.name, preview.input_int_value, 0, 10000, 0)
    preview.input_int_value = ImGuiDev.input_int(
        "Int Buttons##2" + theme.name, preview.input_int_value)


def draw_separator(theme: Style.StyleTheme):
    ImGuiDev.separator()


def draw_progress_bar(theme: Style.StyleTheme):
    ImGuiDev.progress_bar(0.25, 0, 20, "25 points")


def draw_text(theme: Style.StyleTheme):
    ImGuiDev.text("This is some text.")


def draw_hyperlink(theme: Style.StyleTheme):
    ImGuiDev.hyperlink("Click Me")


def draw_bullet_text(theme: Style.StyleTheme):
    ImGuiDev.bullet_text("Bullet Text 1")
    ImGuiDev.bullet_text("Bullet Text 2")


def draw_objective_text(theme: Style.StyleTheme):
    preview.objective_1 = ImGuiDev.objective_text(
        "Objective 1", preview.objective_1)
    preview.objective_2 = ImGuiDev.objective_text(
        "Objective 2", preview.objective_2)


def draw_tree_node(theme: Style.StyleTheme):
    if ImGuiDev.tree_node("Tree Node 1##" + theme.name):
        if ImGuiDev.tree_node("Tree Node 1.1##" + theme.name):
            ImGuiDev.text("This is a tree node content.")
            ImGuiDev.tree_pop()

        ImGuiDev.tree_pop()


def draw_collapsing_header(theme: Style.StyleTheme):
    if ImGuiDev.collapsing_header("Collapsing Header##" + theme.name, 0):
        ImGuiDev.text("This is a collapsible header content.")


def draw_child(theme: Style.StyleTheme):
    if ImGuiDev.begin_child("Child##" + theme.name, (0, 68), True, PyImGui.WindowFlags.AlwaysHorizontalScrollbar):
        ImGuiDev.text("This is a child content.")
        ImGuiDev.text("This is a child content.")
        ImGuiDev.text("This is a child content.")
        ImGuiDev.text("This is a child content.")
        ImGuiDev.text("This is a child content.")
    ImGuiDev.end_child()


def draw_tab_bar(theme: Style.StyleTheme):
    if ImGuiDev.begin_tab_bar("Tab Bar PyImGui##" + theme.name):
        if ImGuiDev.begin_tab_item("Tab 1##" + theme.name):
            ImGuiDev.text("Content for Tab 1")
            PyImGui.end_tab_item()

        if ImGuiDev.begin_tab_item("Tab 2##" + theme.name):
            ImGuiDev.text("Content for Tab 2")
            PyImGui.end_tab_item()

        ImGuiDev.end_tab_bar()


controls = {
    "Button": draw_button,
    "Small Button": draw_small_button,
    "Icon Button": draw_icon_button,
    "Toggle Button": draw_toggle_button,
    "Image Toggle Button": draw_image_toggle,
    "Image Button": draw_image_button,
    "Combo": draw_combo,
    "Checkbox": draw_checkbox,
    "Radio Button": draw_radio_button,
    "Slider": draw_slider,
    "Input": draw_input,
    "Separator": draw_separator,
    "Progress Bar": draw_progress_bar,
    "Text": draw_text,
    "Hyperlink": draw_hyperlink,
    "Bullet Text": draw_bullet_text,
    "Objective Text": draw_objective_text,
    "Tree Node": draw_tree_node,
    "Collapsing Header": draw_collapsing_header,
    "Child & Scrollbars": draw_child,
    "Tab Bar": draw_tab_bar,
}


def DrawThemeCompare():
    global match_style_vars

    if ImGui.begin("Theme Compare"):
        if PyImGui.is_rect_visible(50, 50):
            themes = [style for style in Style.StyleTheme]

            PyImGui.push_item_width(150)
            style = ImGui.get_style()

            # region Header
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.CellPadding, 4, 8)
            if ImGui.begin_table("Control Preview#Header", 4, PyImGui.TableFlags.BordersOuterH, 0, 30):
                PyImGui.table_setup_column(
                    "Control", PyImGui.TableColumnFlags.WidthFixed, 150)
                PyImGui.table_setup_column(
                    "ImGui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Guild Wars", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Minimalus", PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_next_row()
                PyImGui.table_next_column()

                checked = ImGui.checkbox("Match Style Vars", match_style_vars)
                if checked != match_style_vars:
                    match_style_vars = checked

                    for theme in themes:
                        ConsoleLog(
                            module_name, f"Reloading theme {theme.name} to match style vars")
                        ImGui.reload_theme(theme)

                if match_style_vars:
                    for theme in themes:
                        s = ImGui.Styles[theme]

                        for var_enum, var in s.StyleVars.items():
                            var.value1 = style.StyleVars[var_enum].value1
                            var.value2 = style.StyleVars[var_enum].value2

                PyImGui.table_next_column()

                ImGui.text("ImGui")
                PyImGui.table_next_column()

                ImGui.text("Guild Wars")
                PyImGui.table_next_column()

                ImGui.text("Minimalus")
                ImGui.end_table()
            PyImGui.pop_style_var(1)
            # endregion

            if ImGui.begin_table("Control Preview", len(themes) + 1, PyImGui.TableFlags.ScrollX | PyImGui.TableFlags.ScrollY):
                PyImGui.table_setup_column(
                    "Control", PyImGui.TableColumnFlags.WidthFixed, 150)
                PyImGui.table_setup_column(
                    "ImGui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Guild Wars", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Minimalus", PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_next_row()
                PyImGui.table_next_column()

                for control_name, control_draw_func in controls.items():
                    ImGui.text(control_name)
                    PyImGui.table_next_column()

                    for style in themes:
                        ImGui.push_theme(style)
                        control_draw_func(style)
                        PyImGui.table_next_column()
                        ImGui.pop_theme()

                ImGui.end_table()

            PyImGui.pop_item_width()
    ImGui.end()


def DrawControlCompare():
    if ImGui.begin("Control Compare"):
        if PyImGui.is_rect_visible(50, 50):

            PyImGui.push_item_width(150)
            style = ImGui.get_style()

            if ImGui.begin_table("Control Preview", 4, PyImGui.TableFlags.ScrollX):
                PyImGui.table_setup_column(
                    "ControlName", PyImGui.TableColumnFlags.WidthFixed, 150)
                PyImGui.table_setup_column(
                    "PyImgui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "ImGui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "ImGui Style Pushed", PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_next_row()
                PyImGui.table_next_column()

                ImGui.text("Control")
                PyImGui.table_next_column()

                PyImGui.combo("##1", ImGui.Selected_Style.Theme.value, themes)
                ImGui.combo("##2", ImGui.Selected_Style.Theme.value, themes)
                ImGui.push_theme(Style.StyleTheme.Minimalus)
                ImGui.combo("##3", ImGui.Selected_Style.Theme.value, themes)
                ImGui.pop_theme()
                ImGuiDev.combo("##4", ImGui.Selected_Style.Theme.value, themes)

                PyImGui.table_next_column()
                
                ImGui.button("Button")
                ImGuiDev.button("Button")
                ImGui.push_theme(Style.StyleTheme.Minimalus)
                ImGuiDev.button("Button")  
                ImGui.pop_theme()
                
                ImGui.end_table()
            PyImGui.pop_item_width()
    ImGui.end()


def theme_selector(style: Style, func: FunctionType, control_colors: list[str] = []) -> dict[str, Style.CustomColor | Style.StyleColor]:
    PyImGui.push_item_width(200)

    pushed_colors = {}

    value = ImGui.combo(f"Theme##theme_selector{func.__name__}",
                        style.Theme.value, themes)

    if value != style.Theme.value:
        control_styles[func.__name__] = Style.load_theme(
            Style.StyleTheme(value))

    for col_name in control_colors:
        col = style.Colors.get(col_name) or style.CustomColors.get(col_name)

        if not col:
            continue

        color_tuple = ImGui.color_edit4(
            f"{col.img_color_enum.name if col.img_color_enum else "color"}##{func.__name__}", col.color_tuple)

        if color_tuple != col.color_tuple:
            col.set_tuple_color(color_tuple)

        col.push_color()
        pushed_colors[col_name] = col

    PyImGui.pop_item_width()
    PyImGui.table_next_column()
    return pushed_colors


def display_code_with_copy(code):
    if ImGui.button("Copy Code"):
        PyImGui.set_clipboard_text(code)

    ImGui.show_tooltip(code)
    PyImGui.table_next_column()


def format_arg(arg):
    if isinstance(arg, str):
        return f'"{arg}"'   # wrap in quotes
    return str(arg)


def get_code(func: FunctionType, *args, control_colors: list[str] = []) -> str:
    og_style = ImGui.get_style()

    if func.__name__ not in control_styles:
        control_styles[func.__name__] = og_style.copy()

    style = control_styles[func.__name__]
    pushed_colors = theme_selector(style, func, control_colors)

    ImGui.Selected_Style = style
    style.push_style_vars()
    func.__call__(*args)  # Call the function to render the control
    style.pop_style_vars()
    ImGui.Selected_Style = org_style

    for _, col in pushed_colors.items():
        col.pop_color()

    PyImGui.table_next_column()

    code = f"def draw_custom_{func.__name__.lower()}():\n"
    code += f"\t##Only if you need a different theme than current\n"
    code += f"\tImGui.push_theme(Style.StyleTheme.{control_styles[func.__name__].Theme.name})"
    code += f"\n\tstyle = ImGui.get_style()\n"

    for col_name, col in pushed_colors.items():
        r, g, b, a = col.rgb_tuple
        code += f"\tstyle.{col_name}.push_color(({r}, {g}, {b}, {a}))\n"

    code += f"\n\tImGui.{func.__name__}({', '.join(format_arg(a) for a in args)})\n\n"

    for col_name, col in pushed_colors.items():
        code += f"\tstyle.{col_name}.pop_color()\n"

    return code


def customizing_control(func: FunctionType, *args, control_colors: list[str] = []):
    code = get_code(func, *args, control_colors=control_colors)

    display_code_with_copy(code)


control_styles: dict[str, Style] = {}
use_controls = {
    "Button": lambda: customizing_control(ImGui.button, "Button", 100, control_colors=["Button", "ButtonHovered", "ButtonActive"]),
    "Small Button": lambda: customizing_control(ImGui.small_button, "Small Button", control_colors=["Button", "ButtonHovered", "ButtonActive"]),
    "Progress Bar": lambda: customizing_control(ImGui.progress_bar, 0.5, 150, 20, "50% Progress", control_colors=["PlotHistogram"]),
    "Text": lambda: customizing_control(ImGui.text, "This is some text.", control_colors=["Text"]),
    "Bullet Text": lambda: customizing_control(ImGui.bullet_text, "Bullet Text", control_colors=["Text"]),
    "Tree Node": lambda: customizing_control(ImGui.tree_node, "Tree Node", control_colors=["TextTreeNode"]),
}


def DrawUsageTab():
    if PyImGui.is_rect_visible(50, 50):
        # region Header
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.CellPadding, 4, 8)
        if ImGui.begin_table("Control Preview#Header", 4, PyImGui.TableFlags.BordersOuterH, 0, 30):
            PyImGui.table_setup_column(
                "Control", PyImGui.TableColumnFlags.WidthFixed, 100)
            PyImGui.table_setup_column(
                "Color Edit", PyImGui.TableColumnFlags.WidthFixed, 320)
            PyImGui.table_setup_column(
                "Preview", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column(
                "Code", PyImGui.TableColumnFlags.WidthFixed, 100)

            PyImGui.table_next_row()
            PyImGui.table_next_column()

            PyImGui.table_next_column()

            ImGui.text("Edit Colors")
            PyImGui.table_next_column()

            ImGui.text("Preview")
            PyImGui.table_next_column()

            ImGui.text("Code")
            ImGui.end_table()
        PyImGui.pop_style_var(1)
        # endregion

        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.CellPadding, 4, 8)
        if ImGui.begin_table("Control Preview", 4, PyImGui.TableFlags.ScrollX | PyImGui.TableFlags.ScrollY | PyImGui.TableFlags.BordersInnerH):
            PyImGui.table_setup_column(
                "Control", PyImGui.TableColumnFlags.WidthFixed, 100)
            PyImGui.table_setup_column(
                "Color Edit", PyImGui.TableColumnFlags.WidthFixed, 320)
            PyImGui.table_setup_column(
                "Preview", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column(
                "Code", PyImGui.TableColumnFlags.WidthFixed, 100)

            PyImGui.table_next_row()
            PyImGui.table_next_column()

            for control_name, control_draw_func in use_controls.items():
                ImGui.text(control_name)
                PyImGui.table_next_column()

                control_draw_func()

            ImGui.end_table()
        PyImGui.pop_style_var(1)


def DrawWindow():
    global window_module, module_name, ini_handler, window_x, window_y, window_collapsed, control_compare, theme_compare, org_style, window_width, window_height
    global game_throttle_time, game_throttle_timer, save_throttle_time, save_throttle_timer

    # try:
    if not window_module.open:
        return

    if window_module.begin():
        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
        ImGui.text("Selected Theme")
        PyImGui.same_line(0, 5)
        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
        remaining = PyImGui.get_content_region_avail()
        PyImGui.push_item_width(remaining[0] - 30)
        value = ImGui.combo("##theme_selector",
                            ImGui.Selected_Style.Theme.value, themes)

        if value != ImGui.Selected_Style.Theme.value:
            theme = Style.StyleTheme(value)
            ImGui.reload_theme(theme)
            ImGui.set_theme(theme)

            org_style = ImGui.Selected_Style.copy()
            py4_gw_ini_handler.write_key(
                "settings", "style_theme", ImGui.Selected_Style.Theme.name)

        PyImGui.same_line(0, 5)
        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
        theme_compare = ImGui.checkbox(
            "##show_theme_compare", theme_compare)
        ImGui.show_tooltip(
            "Show Theme Compare window")

        PyImGui.spacing()
        ImGui.separator()
        PyImGui.spacing()
        any_changed = False

        if ImGui.begin_tab_bar("Style Customization"):
            if ImGui.begin_tab_item("Style Customization"):
                ImGui.begin_child("Style Customization")

                if ImGui.Selected_Style:
                    remaining = PyImGui.get_content_region_avail()
                    button_width = (remaining[0] - 10) / 2

                    any_changed = any(
                        var != org_style.StyleVars[enum] for enum, var in ImGui.Selected_Style.StyleVars.items())
                    any_changed |= any(
                        col != org_style.Colors[enum] for enum, col in ImGui.Selected_Style.Colors.items())
                    any_changed |= any(
                        col != org_style.CustomColors[enum] for enum, col in ImGui.Selected_Style.CustomColors.items())
                    any_changed |= any(
                        col != org_style.TextureColors[enum] for enum, col in ImGui.Selected_Style.TextureColors.items())

                    if ImGui.button("Save Changes", button_width, enabled=any_changed):
                        ImGui.Selected_Style.save_to_json()
                        ImGui.Selected_Style.apply_to_style_config()
                        org_style = ImGui.Selected_Style.copy()

                    PyImGui.same_line(0, 5)

                    if ImGui.button("Reset to Default", button_width, enabled=any_changed):
                        theme = ImGui.Selected_Style.Theme
                        ImGui.Selected_Style.delete()
                        ImGui.reload_theme(theme)
                        org_style = ImGui.Selected_Style.copy()

                    ImGui.show_tooltip(
                        "Delete the current style and replace it with the default style for the theme.")

                    PyImGui.spacing()

                    if PyImGui.is_rect_visible(50, 50):
                        column_width = 0
                        item_width = 0

                        if ImGui.begin_table("Style Variables", 3, PyImGui.TableFlags.ScrollY):
                            PyImGui.table_setup_column(
                                "Variable", PyImGui.TableColumnFlags.WidthFixed, 150)
                            PyImGui.table_setup_column(
                                "Value", PyImGui.TableColumnFlags.WidthStretch)
                            PyImGui.table_setup_column(
                                "Undo", PyImGui.TableColumnFlags.WidthFixed, 35)

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            
                            ImGui.Selected_Style.Hyperlink.push_color()
                            ImGui.push_font("Regular", 18)
                            PyImGui.separator()
                            PyImGui.text("Style Vars")
                            PyImGui.separator()
                            ImGui.pop_font()
                            ImGui.Selected_Style.Hyperlink.pop_color()
                            PyImGui.table_next_column()
                            PyImGui.table_next_column()
                            PyImGui.table_next_column()

                            for enum, var in ImGui.Selected_Style.StyleVars.items():
                                PyImGui.set_cursor_pos_y(
                                    PyImGui.get_cursor_pos_y() + 5)
                                ImGui.text(f"{enum}")
                                PyImGui.table_next_column()

                                column_width = column_width or PyImGui.get_content_region_avail()[
                                    0]
                                item_width = item_width or (
                                    column_width - 5) / 2
                                PyImGui.push_item_width(item_width)
                                var.value1 = ImGui.input_float(
                                    f"##{enum}_value1", var.value1)

                                if var.value2 is not None:
                                    PyImGui.same_line(0, 5)

                                    PyImGui.push_item_width(item_width)
                                    var.value2 = ImGui.input_float(
                                        f"##{enum}_value2", var.value2)

                                PyImGui.table_next_column()

                                changed = org_style.StyleVars[
                                    enum].value1 != var.value1 or org_style.StyleVars[enum].value2 != var.value2

                                if changed:
                                    if ImGui.icon_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                        var.value1 = org_style.StyleVars[enum].value1
                                        var.value2 = org_style.StyleVars[enum].value2

                                PyImGui.table_next_column()

                            for enum, col in ImGui.Selected_Style.Colors.items():
                                PyImGui.set_cursor_pos_y(
                                    PyImGui.get_cursor_pos_y() + 5)
                                ImGui.text(f"{enum}")
                                PyImGui.table_next_column()

                                column_width = column_width or PyImGui.get_content_region_avail()[
                                    0]

                                PyImGui.push_item_width(column_width)
                                color_tuple = ImGui.color_edit4(
                                    f"##{enum}_color", col.color_tuple)
                                if color_tuple != col.color_tuple:
                                    col.set_tuple_color(color_tuple)

                                PyImGui.table_next_column()

                                changed = col.color_int != org_style.Colors[enum].color_int

                                if changed:
                                    if ImGui.icon_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                        col.color_tuple = org_style.Colors[enum].color_tuple

                                PyImGui.table_next_column()

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            
                            ImGui.Selected_Style.Hyperlink.push_color()
                            ImGui.push_font("Regular", 18)
                            PyImGui.separator()
                            PyImGui.text("Custom Colors")
                            PyImGui.separator()
                            ImGui.pop_font()
                            ImGui.Selected_Style.Hyperlink.pop_color()

                            PyImGui.table_next_column()
                            PyImGui.table_next_column()
                            PyImGui.table_next_column()

                            for enum, col in ImGui.Selected_Style.CustomColors.items():
                                PyImGui.set_cursor_pos_y(
                                    PyImGui.get_cursor_pos_y() + 5)
                                ImGui.text(f"{enum}")
                                PyImGui.table_next_column()

                                column_width = column_width or PyImGui.get_content_region_avail()[
                                    0]

                                PyImGui.push_item_width(column_width)
                                color_tuple = ImGui.color_edit4(
                                    f"##{enum}_color", col.color_tuple)
                                if color_tuple != col.color_tuple:
                                    col.set_tuple_color(color_tuple)

                                PyImGui.table_next_column()

                                changed = col.color_int != org_style.CustomColors[enum].color_int

                                if changed:
                                    if ImGui.icon_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                        col.color_tuple = org_style.CustomColors[enum].color_tuple
                                PyImGui.table_next_column()

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            
                            ImGui.Selected_Style.Hyperlink.push_color()
                            ImGui.push_font("Regular", 18)
                            PyImGui.separator()
                            PyImGui.text("Texture Colors")
                            PyImGui.separator()
                            ImGui.pop_font()
                            ImGui.Selected_Style.Hyperlink.pop_color()
                            PyImGui.table_next_column()
                            PyImGui.table_next_column()
                            PyImGui.table_next_column()
                            
                            for enum, col in ImGui.Selected_Style.TextureColors.items():
                                PyImGui.set_cursor_pos_y(
                                    PyImGui.get_cursor_pos_y() + 5)
                                ImGui.text(f"{enum}")
                                PyImGui.table_next_column()

                                column_width = column_width or PyImGui.get_content_region_avail()[
                                    0]

                                PyImGui.push_item_width(column_width)
                                color_tuple = ImGui.color_edit4(
                                    f"##{enum}_color", col.color_tuple)
                                if color_tuple != col.color_tuple:
                                    col.set_tuple_color(color_tuple)

                                PyImGui.table_next_column()

                                changed = col.color_int != org_style.TextureColors[enum].color_int

                                if changed:
                                    if ImGui.icon_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                        col.color_tuple = org_style.TextureColors[enum].color_tuple
                                PyImGui.table_next_column()
                            
                            ImGui.end_table()

                ImGui.end_child()

                ImGui.end_tab_item()

            if ImGui.begin_tab_item("Control Preview"):
                style = ImGui.get_style()

                if PyImGui.is_rect_visible(50, 50):
                    column_width = 0
                    item_width = 0

                    PyImGui.push_item_width(150)
                    if ImGui.begin_table("Control Preview", 2, PyImGui.TableFlags.ScrollX):
                        PyImGui.table_setup_column(
                            "Control", PyImGui.TableColumnFlags.WidthFixed, 150)
                        PyImGui.table_setup_column(
                            "Preview", PyImGui.TableColumnFlags.WidthStretch)

                        PyImGui.table_next_row()
                        PyImGui.table_next_column()

                        for control_name, control_draw_func in controls.items():
                            ImGui.text(control_name)
                            PyImGui.table_next_column()

                            control_draw_func(style.Theme)
                            PyImGui.table_next_column()

                        ImGui.end_table()
                    PyImGui.pop_item_width()
                ImGui.end_tab_item()

            if ImGui.begin_tab_item("How to Use"):
                DrawUsageTab()
                ImGui.end_tab_item()

            ImGui.end_tab_bar()

            if control_compare:
                DrawControlCompare()

            if theme_compare:
                DrawThemeCompare()

        window_module.process_window()

    window_module.end()

    if save_throttle_timer.HasElapsed(save_throttle_time):
        if window_module.window_pos[0] != window_module.end_pos[0] or window_module.window_pos[1] != window_module.end_pos[1]:
            window_module.window_pos = window_module.end_pos
            ini_handler.write_key(
                module_name + " Config", "x", str(int(window_module.window_pos[0])))
            ini_handler.write_key(
                module_name + " Config", "y", str(int(window_module.window_pos[1])))

        if window_width != window_module.window_size[0] or window_height != window_module.window_size[1]:
            ini_handler.write_key(
                module_name + " Config", "width", str(int(window_module.window_size[0])))
            ini_handler.write_key(
                module_name + " Config", "height", str(int(window_module.window_size[1])))
            window_width, window_height = window_module.window_size

        if window_module.collapsed_status != window_module.collapse:
            window_module.collapse = window_module.collapsed_status
            ini_handler.write_key(
                module_name + " Config", "collapsed", str(window_module.collapse))

        save_throttle_timer.Reset()

    # except Exception as e:
    #     Py4GW.Console.Log(
    #         module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Debug)


def main():
    """Required main function for the widget"""
    global game_throttle_timer, game_throttle_time, window_module

    # try:
    DrawWindow()
    window_module.open = True

    # except Exception as e:
    #     Py4GW.Console.Log(
    #         module_name, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
    #     return False
    return True


# These functions need to be available at module level
__all__ = ['main', 'configure']

if __name__ == "__main__":
    main()
