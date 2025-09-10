import json
import math
import os
from pathlib import Path
from typing import Optional
from unittest import case
import Py4GW
import PyImGui
from enum import Enum, IntEnum


from .Overlay import Overlay
from Py4GWCoreLib.Py4GWcorelib import Color, ColorPalette, ConsoleLog, IniHandler
from Py4GWCoreLib.enums import get_texture_for_model, ImguiFonts
from Py4GWCoreLib import IconsFontAwesome5, Utils

from enum import IntEnum

class SortDirection(Enum):
    No_Sort = 0
    Ascending = 1
    Descending = 2


from enum import IntEnum


TEXTURE_FOLDER = "Textures\\Game UI\\"
MINIMALUS_FOLDER = "Textures\\Themes\\Minimalus\\"

class Style:    
    pyimgui_style = PyImGui.StyleConfig()
    
    class StyleTheme(IntEnum):
        ImGui = 0
        Guild_Wars = 1
        Minimalus = 2
        
    class StyleVar:
        def __init__(self, style : "Style", value1: float, value2: float | None = None, img_style_enum : "ImGui.ImGuiStyleVar|None" = None):
            self.style = style
            self.img_style_enum: ImGui.ImGuiStyleVar | None = img_style_enum
            self.value1: float = value1
            self.value2: float | None = value2
            self.pushed_stack = []
            
        def push_style_var(self, value1: float | None = None, value2: float | None = None):
            var = Style.StyleVar(
                style=self.style,
                value1=value1,
                value2=value2,
                img_style_enum=self.img_style_enum
            ) if value1 is not None else self.get_current()
            
            if var.img_style_enum:                
                if var.value2 is not None:
                    PyImGui.push_style_var2(var.img_style_enum, var.value1, var.value2)
                else:
                    PyImGui.push_style_var(var.img_style_enum, var.value1)

            self.pushed_stack.insert(0, var)

        def pop_style_var(self):
            if self.pushed_stack:
                self.pushed_stack.pop(0)

            if self.img_style_enum:
                PyImGui.pop_style_var(1)

        def to_json(self):
            return {
                "value1": self.value1,
                "value2": self.value2
            } if self.value2 is not None else {
                "value1": self.value1
            }

        def from_json(self, img_style_enum: str, data):
            # self.img_style_enum = getattr(ImGui.ImGuiStyleVar, img_style_enum) if img_style_enum in ImGui.ImGuiStyleVar.__members__ else None
            self.value1 = data["value1"]
            self.value2 = data.get("value2", None)
        
        def get_current(self):
            return self.pushed_stack[0] if self.pushed_stack else self

        def copy(self):
            return Style.StyleVar(
                style=self.style,
                value1=self.value1,
                value2=self.value2,
                img_style_enum=self.img_style_enum
            )

        def __hash__(self):
            return hash((self.img_style_enum, self.value1, self.value2))
        
        def __ne__(self, value):
            if not isinstance(value, Style.StyleVar):
                return True

            return (self.img_style_enum != value.img_style_enum or
                    self.value1 != value.value1 or
                    self.value2 != value.value2)

        def __eq__(self, value):
            if not isinstance(value, Style.StyleVar):
                return False

            return (self.img_style_enum == value.img_style_enum and
                    self.value1 == value.value1 and
                    self.value2 == value.value2)        

    class CustomColor:
        def __init__(self, style : "Style", r: int, g: int, b: int, a: int = 255, img_color_enum : PyImGui.ImGuiCol | None = None):
            self.style = style
            self.set_rgb_color(r, g, b, a)
            self.img_color_enum = img_color_enum
            self.pushed_stack = []

        def __hash__(self):
            return hash((self.r, self.g, self.b, self.a))

        def __eq__(self, other):
            if not isinstance(other, Style.CustomColor):
                return False

            return (self.r == other.r and
                    self.g == other.g and
                    self.b == other.b and
                    self.a == other.a)        
        
        def __ne__(self, value):
            if not isinstance(value, Style.CustomColor):
                return True

            return (self.r != value.r or
                    self.g != value.g or
                    self.b != value.b or
                    self.a != value.a)

        def set_rgb_color(self, r: int, g: int, b: int, a: int = 255):
            self.r = r
            self.g = g
            self.b = b
            self.a = a

            self.rgb_tuple = (r, g, b, a)
            self.color_tuple = r / 255.0, g / 255.0, b / 255.0, a / 255.0  # Convert to RGBA float
            self.color_int = Utils.RGBToColor(r, g, b, a)

        def set_tuple_color(self, color: tuple[float, float, float, float]):
            #convert from color tuple
            self.r = int(color[0] * 255)
            self.g = int(color[1] * 255)
            self.b = int(color[2] * 255)
            self.a = int(color[3] * 255)

            self.rgb_tuple = (self.r, self.g, self.b, self.a)
            self.color_tuple = color
            self.color_int = Utils.RGBToColor(self.r, self.g, self.b, self.a)

        def push_color(self, rgba: tuple[int, int, int, int] | None = None):
            col = Style.StyleColor(self.style, *rgba, self.img_color_enum) if rgba else self.get_current()
            
            if self.img_color_enum is not None:
                PyImGui.push_style_color(self.img_color_enum, col.color_tuple)

            self.pushed_stack.insert(0, col)
            
        def pop_color(self):
            if self.pushed_stack:
                color = self.pushed_stack.pop(0)
                
                if color.img_color_enum:
                    PyImGui.pop_style_color(1)
                    
        def get_current(self) -> "Style.CustomColor":
            """
            Method to use for manual drawing.\n
            Returns the current Style.CustomColor from the pushed stack if available, otherwise returns self.
            Returns:
                Style.CustomColor: The first Style.CustomColor in the pushed_stack if it exists, otherwise self.
            """
        
            return self.pushed_stack[0] if self.pushed_stack else self
        
        def to_json(self):
            return {
                "img_color_enum": self.img_color_enum.name if self.img_color_enum else None,
                "r": self.r,
                "g": self.g,
                "b": self.b,
                "a": self.a
            }

        def from_json(self, data):
            img_color_enum = data.get("img_color_enum", None)
            self.img_color_enum = getattr(PyImGui.ImGuiCol, img_color_enum) if img_color_enum in PyImGui.ImGuiCol.__members__ else None
            r, g, b, a = data["r"], data["g"], data["b"], data.get("a", 255)
            self.set_rgb_color(r, g, b, a)

    class StyleColor:
        def __init__(self, style : "Style", r: int, g: int, b: int, a: int = 255, img_color_enum : PyImGui.ImGuiCol | None = None):
            self.style = style
            self.img_color_enum = img_color_enum
            self.set_rgb_color(r, g, b, a)
            self.pushed_stack : list[Style.StyleColor] = []

        def __eq__(self, other):
            if not isinstance(other, "Style.StyleColor"):
                return False
            
            return (
                self.img_color_enum == other.img_color_enum and
                self.r == other.r and
                self.g == other.g and
                self.b == other.b and
                self.a == other.a
            )

        def __hash__(self):
            # Use an immutable tuple of all values used in equality
            return hash((self.img_color_enum, self.r, self.g, self.b, self.a))      
            
        def __ne__(self, value):
            if not isinstance(value, Style.StyleColor):
                return True

            return (self.img_color_enum != value.img_color_enum or
                    self.r != value.r or
                    self.g != value.g or
                    self.b != value.b or
                    self.a != value.a)

        def set_rgb_color(self, r: int, g: int, b: int, a: int = 255):
            self.r = r
            self.g = g
            self.b = b
            self.a = a

            self.rgb_tuple = (r, g, b, a)
            self.color_tuple = r / 255.0, g / 255.0, b / 255.0, a / 255.0  # Convert to RGBA float
            self.color_int = Utils.RGBToColor(r, g, b, a)

        def set_tuple_color(self, color: tuple[float, float, float, float]):
            #convert from color tuple
            self.r = int(color[0] * 255)
            self.g = int(color[1] * 255)
            self.b = int(color[2] * 255)
            self.a = int(color[3] * 255)

            self.rgb_tuple = (self.r, self.g, self.b, self.a)
            self.color_tuple = color
            self.color_int = Utils.RGBToColor(self.r, self.g, self.b, self.a)

        def push_color(self, rgba: tuple[int, int, int, int] | None = None):
            col = Style.StyleColor(self.style, *rgba, self.img_color_enum) if rgba != None else self.get_current()
            
            if col.img_color_enum is not None:
                PyImGui.push_style_color(col.img_color_enum, col.color_tuple)

            self.pushed_stack.insert(0, col)

        def pop_color(self):
            if self.pushed_stack:
                color = self.pushed_stack[0]
                self.pushed_stack.pop(0)
                
                if color.img_color_enum is not None:
                    PyImGui.pop_style_color(1)

        def get_current(self) -> "Style.StyleColor":
            """
            Method to use for manual drawing.\n
            Returns the current Style.StyleColor from the pushed stack if available, otherwise returns self.
            Returns:
                Style.StyleColor: The first Style.StyleColor in the pushed_stack if it exists, otherwise self.
            """
            
            return self.pushed_stack[0] if self.pushed_stack else self
        
        def to_json(self):
            return {
                "img_color_enum": self.img_color_enum.name if self.img_color_enum else None,
                "r": self.r,
                "g": self.g,
                "b": self.b,
                "a": self.a
            }

        def from_json(self, data):
            img_color_enum = data.get("img_color_enum", None)
            self.img_color_enum = getattr(PyImGui.ImGuiCol, img_color_enum) if img_color_enum in PyImGui.ImGuiCol.__members__ else None
            r, g, b, a = data["r"], data["g"], data["b"], data.get("a", 255)
            self.set_rgb_color(r, g, b, a)
            
    def __init__(self):
        # Set the default style as base so we can push it and cover all
        self.Theme : Style.StyleTheme = Style.StyleTheme.ImGui

        self.WindowPadding : Style.StyleVar = Style.StyleVar(self, 10, 10, ImGui.ImGuiStyleVar.WindowPadding)
        self.CellPadding : Style.StyleVar = Style.StyleVar(self, 5, 5, ImGui.ImGuiStyleVar.CellPadding)
        self.ChildRounding : Style.StyleVar = Style.StyleVar(self, 0, None, ImGui.ImGuiStyleVar.ChildRounding)
        self.TabRounding : Style.StyleVar = Style.StyleVar(self, 4, None, ImGui.ImGuiStyleVar.TabRounding)
        self.PopupRounding : Style.StyleVar = Style.StyleVar(self, 4, None, ImGui.ImGuiStyleVar.PopupRounding)
        self.WindowRounding : Style.StyleVar = Style.StyleVar(self, 4, None, ImGui.ImGuiStyleVar.WindowRounding)
        self.FramePadding : Style.StyleVar = Style.StyleVar(self, 5, 5, ImGui.ImGuiStyleVar.FramePadding)
        self.ButtonPadding : Style.StyleVar = Style.StyleVar(self, 5, 5, ImGui.ImGuiStyleVar.FramePadding)
        self.FrameRounding : Style.StyleVar = Style.StyleVar(self, 4, None, ImGui.ImGuiStyleVar.FrameRounding)
        self.ItemSpacing : Style.StyleVar = Style.StyleVar(self, 10, 6, ImGui.ImGuiStyleVar.ItemSpacing)
        self.ItemInnerSpacing : Style.StyleVar = Style.StyleVar(self, 6, 4, ImGui.ImGuiStyleVar.ItemInnerSpacing)
        self.IndentSpacing : Style.StyleVar = Style.StyleVar(self, 20, None, ImGui.ImGuiStyleVar.IndentSpacing)
        self.ScrollbarSize : Style.StyleVar = Style.StyleVar(self, 20, None, ImGui.ImGuiStyleVar.ScrollbarSize)
        self.ScrollbarRounding : Style.StyleVar = Style.StyleVar(self, 9, None, ImGui.ImGuiStyleVar.ScrollbarRounding)
        self.GrabMinSize : Style.StyleVar = Style.StyleVar(self, 5, None, ImGui.ImGuiStyleVar.GrabMinSize)
        self.GrabRounding : Style.StyleVar = Style.StyleVar(self, 3, None, ImGui.ImGuiStyleVar.GrabRounding)

        self.Text = Style.StyleColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.Text)
        self.TextDisabled = Style.StyleColor(self, 51, 51, 51, 255, PyImGui.ImGuiCol.TextDisabled)
        self.TextSelectedBg = Style.StyleColor(self, 26, 255, 26, 110, PyImGui.ImGuiCol.TextSelectedBg)

        self.WindowBg = Style.StyleColor(self, 2, 2, 2, 215, PyImGui.ImGuiCol.WindowBg)
        self.ChildBg = Style.StyleColor(self, 0, 0, 0, 0, PyImGui.ImGuiCol.ChildBg)
        # self.ChildWindowBg = StyleColor(self, 18, 18, 23, 255, PyImGui.ImGuiCol.ChildWindowBg)
        self.Tab = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Tab)
        self.TabHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.TabHovered)
        self.TabActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.TabActive)

        self.PopupBg = Style.StyleColor(self, 2, 2, 2, 215, PyImGui.ImGuiCol.PopupBg)
        self.Border = Style.StyleColor(self, 204, 204, 212, 225, PyImGui.ImGuiCol.Border)
        self.BorderShadow = Style.StyleColor(self, 26, 26, 26, 128, PyImGui.ImGuiCol.BorderShadow)
        self.FrameBg = Style.StyleColor(self, 26, 23, 30, 255, PyImGui.ImGuiCol.FrameBg)
        self.FrameBgHovered = Style.StyleColor(self, 61, 59, 74, 255, PyImGui.ImGuiCol.FrameBgHovered)
        self.FrameBgActive = Style.StyleColor(self, 143, 143, 148, 255, PyImGui.ImGuiCol.FrameBgActive)
        self.TitleBg = Style.StyleColor(self, 13, 13, 13, 215, PyImGui.ImGuiCol.TitleBg)
        self.TitleBgCollapsed = Style.StyleColor(self, 5, 5, 5, 215, PyImGui.ImGuiCol.TitleBgCollapsed)
        self.TitleBgActive = Style.StyleColor(self, 51, 51, 51, 215, PyImGui.ImGuiCol.TitleBgActive)
        self.MenuBarBg = Style.StyleColor(self, 26, 23, 30, 255, PyImGui.ImGuiCol.MenuBarBg)
        self.ScrollbarBg = Style.StyleColor(self, 2, 2, 2, 215, PyImGui.ImGuiCol.ScrollbarBg)
        self.ScrollbarGrab = Style.StyleColor(self, 51, 76, 76, 128, PyImGui.ImGuiCol.ScrollbarGrab)
        self.ScrollbarGrabHovered = Style.StyleColor(self, 51, 76, 102, 128, PyImGui.ImGuiCol.ScrollbarGrabHovered)
        self.ScrollbarGrabActive = Style.StyleColor(self, 51, 76, 102, 128, PyImGui.ImGuiCol.ScrollbarGrabActive)
        # self.ComboBg = StyleColor(self, 26, 23, 30, 255, PyImGui.ImGuiCol.ComboBg)

        self.CheckMark = Style.StyleColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.CheckMark)
        self.SliderGrab = Style.StyleColor(self, 51, 76, 76, 128, PyImGui.ImGuiCol.SliderGrab)
        self.SliderGrabActive = Style.StyleColor(self, 51, 76, 102, 128, PyImGui.ImGuiCol.SliderGrabActive)
        self.Button = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button)
        self.ButtonHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered)
        self.ButtonActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive)

        self.Header = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Header)
        self.HeaderHovered = Style.StyleColor(self, 143, 143, 148, 255, PyImGui.ImGuiCol.HeaderHovered)
        self.HeaderActive = Style.StyleColor(self, 15, 13, 18, 255, PyImGui.ImGuiCol.HeaderActive)
        # self.Column = Style.StyleColor(self, 143, 143, 148, 255, PyImGui.ImGuiCol.Column)
        # self.ColumnHovered = Style.StyleColor(self, 61, 59, 74, 255, PyImGui.ImGuiCol.ColumnHovered)
        # self.ColumnActive = Style.StyleColor(self, 143, 143, 148, 255, PyImGui.ImGuiCol.ColumnActive)

        self.ResizeGrip = Style.StyleColor(self, 0, 0, 0, 0, PyImGui.ImGuiCol.ResizeGrip)
        self.ResizeGripHovered = Style.StyleColor(self, 143, 143, 148, 255, PyImGui.ImGuiCol.ResizeGripHovered)
        self.ResizeGripActive = Style.StyleColor(self, 15, 13, 18, 255, PyImGui.ImGuiCol.ResizeGripActive)
        # self.CloseButton = Style.StyleColor(self, 102, 99, 96, 40, PyImGui.ImGuiCol.CloseButton)
        # self.CloseButtonHovered = Style.StyleColor(self, 102, 99, 96, 100, PyImGui.ImGuiCol.CloseButtonHovered)
        # self.CloseButtonActive = Style.StyleColor(self, 102, 99, 96, 255, PyImGui.ImGuiCol.CloseButtonActive)

        self.PlotLines = Style.StyleColor(self, 102, 99, 96, 160, PyImGui.ImGuiCol.PlotLines)
        self.PlotLinesHovered = Style.StyleColor(self, 64, 255, 0, 255, PyImGui.ImGuiCol.PlotLinesHovered)
        self.PlotHistogram = Style.StyleColor(self, 102, 99, 96, 160, PyImGui.ImGuiCol.PlotHistogram)
        self.PlotHistogramHovered = Style.StyleColor(self, 64, 255, 0, 255, PyImGui.ImGuiCol.PlotHistogramHovered)
        # self.ModalWindowDarkening = Style.StyleColor(self, 255, 250, 242, 186, PyImGui.ImGuiCol.ModalWindowDarkening)
        
        self.PrimaryButton = Style.CustomColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button)
        self.PrimaryButtonHovered = Style.CustomColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered)
        self.PrimaryButtonActive = Style.CustomColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive)
        
        self.DangerButton = Style.CustomColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button)
        self.DangerButtonHovered = Style.CustomColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered)
        self.DangerButtonActive = Style.CustomColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive)
        
        self.ToggleButtonEnabled = Style.CustomColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button)
        self.ToggleButtonEnabledHovered = Style.CustomColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered)
        self.ToggleButtonEnabledActive = Style.CustomColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive)
        
        self.ToggleButtonDisabled = Style.CustomColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button)
        self.ToggleButtonDisabledHovered = Style.CustomColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered)
        self.ToggleButtonDisabledActive = Style.CustomColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive)

        self.TextCollapsingHeader = Style.CustomColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.Text)
        self.TextTreeNode = Style.CustomColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.Text)
        self.TextObjectiveCompleted = Style.CustomColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.Text)
        self.Hyperlink = Style.CustomColor(self, 102, 187, 238, 255, PyImGui.ImGuiCol.Text)
        
        self.ComboTextureBackground = Style.CustomColor(self, 26, 23, 30, 255)
        self.ComboTextureBackgroundHovered = Style.CustomColor(self, 61, 59, 74, 255)
        self.ComboTextureBackgroundActive = Style.CustomColor(self, 143, 143, 148, 255)

        self.ButtonTextureBackground = Style.CustomColor(self, 26, 23, 30, 255)
        self.ButtonTextureBackgroundHovered = Style.CustomColor(self, 61, 59, 74, 255)
        self.ButtonTextureBackgroundActive = Style.CustomColor(self, 143, 143, 148, 255)
        self.ButtonTextureBackgroundDisabled = Style.CustomColor(self, 143, 143, 148, 255)

        attributes = {name: getattr(self, name) for name in dir(self)}
        self.Colors : dict[str, Style.StyleColor] = {name: attributes[name] for name in attributes if isinstance(attributes[name], Style.StyleColor)}
        self.TextureColors : dict[str, Style.CustomColor] = {
            "ComboTextureBackground" : self.ComboTextureBackground,
            "ComboTextureBackgroundHovered" : self.ComboTextureBackgroundHovered,
            "ComboTextureBackgroundActive" : self.ComboTextureBackgroundActive,
            "ButtonTextureBackground" : self.ButtonTextureBackground,
            "ButtonTextureBackgroundHovered" : self.ButtonTextureBackgroundHovered,
            "ButtonTextureBackgroundActive" : self.ButtonTextureBackgroundActive,
            "ButtonTextureBackgroundDisabled" : self.ButtonTextureBackgroundDisabled,
        }
        self.CustomColors : dict[str, Style.CustomColor] = {name: attributes[name] for name in attributes if isinstance(attributes[name], Style.CustomColor) and name not in self.TextureColors}
        self.StyleVars : dict[str, Style.StyleVar] = {name: attributes[name] for name in attributes if isinstance(attributes[name], Style.StyleVar)}
        
    def copy(self):
        style = Style()
        
        style.Theme = self.Theme
        
        for color_name, c in self.Colors.items():
            attribute = getattr(style, color_name)
            if isinstance(attribute, Style.StyleColor):
                attribute.set_rgb_color(c.r, c.g, c.b, c.a)

        for color_name, c in self.CustomColors.items():
            attribute = getattr(style, color_name)
            if isinstance(attribute, Style.CustomColor):
                attribute.set_rgb_color(c.r, c.g, c.b, c.a)

        for color_name, c in self.TextureColors.items():
            attribute = getattr(style, color_name)
            if isinstance(attribute, Style.CustomColor):
                attribute.set_rgb_color(c.r, c.g, c.b, c.a)
                
        for var_name, v in self.StyleVars.items():
            attribute = getattr(style, var_name)
            if isinstance(attribute, Style.StyleVar):
                attribute.value1 = v.value1
                attribute.value2 = v.value2

        return style

    def push_style(self):
        for var in self.Colors.values():
            var.push_color()
            
        for var in self.StyleVars.values():
            var.push_style_var()
            
        pass

    def pop_style(self):
        for var in self.Colors.values():
            var.pop_color()
            
        for var in self.StyleVars.values():
            var.pop_style_var()
            
        pass
    
    def push_style_vars(self):
        for var in self.StyleVars.values():
            var.push_style_var()
            
        pass

    def pop_style_vars(self):
        for var in self.StyleVars.values():
            var.pop_style_var()
            
        pass

    def save_to_json(self):
        style_data = {
            "Theme": self.Theme.name,
            "Colors": {k: c.to_json() for k, c in self.Colors.items()},
            "CustomColors": {k: c.to_json() for k, c in self.CustomColors.items()},
            "TextureColors": {k: c.to_json() for k, c in self.TextureColors.items()},
            "StyleVars": {k: v.to_json() for k, v in self.StyleVars.items()}
        }

        with open(os.path.join("Styles", f"{self.Theme.name}.json"), "w") as f:
            json.dump(style_data, f, indent=4)

    def delete(self) -> bool:
        file_path = os.path.join("Styles", f"{self.Theme.name}.json")

        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        
        return False

    def apply_to_style_config(self):                
        for _, attribute in self.Colors.items():                
            if attribute.img_color_enum:
                self.pyimgui_style.set_color(attribute.img_color_enum, *attribute.color_tuple)

        self.pyimgui_style.Push()

    @classmethod
    def load_from_json(cls, path : str) -> 'Style':
        style = cls()
        
        if not os.path.exists(path):
            return style
        
        with open(path, "r") as f:
            style_data = json.load(f)

        theme_name = style_data.get("Theme", cls.StyleTheme.ImGui.name)
        style.Theme = cls.StyleTheme[theme_name] if theme_name in cls.StyleTheme.__members__ else cls.StyleTheme.ImGui

        for color_name, color_data in style_data.get("Colors", {}).items():
            attribute = getattr(style, color_name)
            if isinstance(attribute, cls.StyleColor):
                attribute.from_json(color_data)
                
        for color_name, color_data in style_data.get("CustomColors", {}).items():
            attribute = getattr(style, color_name)
            if isinstance(attribute, cls.CustomColor):
                attribute.from_json(color_data)

        for color_name, color_data in style_data.get("TextureColors", {}).items():
            attribute = getattr(style, color_name)
            if isinstance(attribute, cls.CustomColor):
                attribute.from_json(color_data)
                
        for var_name, var_data in style_data.get("StyleVars", {}).items():
            attribute = getattr(style, var_name)
            if isinstance(attribute, cls.StyleVar):
                attribute.from_json(var_name, var_data)

        return style
    
    @classmethod
    def load_theme(cls, theme : StyleTheme) -> 'Style':
        file_path = os.path.join("Styles", f"{theme.name}.json")
        default_file_path = os.path.join("Styles", f"{theme.name}.default.json")
        path = file_path if os.path.exists(file_path) else default_file_path

        return cls.load_from_json(path)

    @classmethod
    def load_default_theme(cls, theme : StyleTheme) -> 'Style':
        default_file_path = os.path.join("Styles", f"{theme.name}.default.json")
        return cls.load_from_json(default_file_path)

class TextureState(IntEnum):
    Normal = 0
    Hovered = 1
    Active = 2
    Disabled = 3

class SplitTexture:
    """
    Represents a texture that is split into left, mid, and right parts.
    Used for drawing scalable UI elements with sliced borders.
    """

    def __init__(
        self,
        texture: str,
        texture_size: tuple[float, float],
        mid: tuple[float, float, float, float] | None = None,
        left: tuple[float, float, float, float] | None = None,
        right: tuple[float, float, float, float] | None = None,
    ):
        self.texture = texture
        self.width, self.height = texture_size

        self.left = left
        self.left_width = (left[2] - left[0]) if left else 0
        self.left_offset = self._calc_uv(left, texture_size) if left else (0, 0, 0, 0)

        self.mid = mid
        self.mid_width = (mid[2] - mid[0]) if mid else 0
        self.mid_offset = self._calc_uv(mid, texture_size) if mid else (0, 0, 0, 0)

        self.right = right
        self.right_width = (right[2] - right[0]) if right else 0
        self.right_offset = self._calc_uv(right, texture_size) if right else (0, 0, 0, 0)

    @staticmethod
    def _calc_uv(region: tuple[float, float, float, float], size: tuple[float, float]) -> tuple[float, float, float, float]:
        x0, y0, x1, y1 = region
        w, h = size
        return x0 / w, y0 / h, x1 / w, y1 / h

    def draw_in_drawlist(self, x: float, y: float, size: tuple[float, float], tint=(255, 255, 255, 255), state: TextureState = TextureState.Normal):
        # Draw left part
        ImGui.DrawTextureInDrawList(
            pos=(x, y),
            size=(self.left_width, size[1]),
            texture_path=self.texture,
            uv0=self.left_offset[:2],
            uv1=self.left_offset[2:],
            tint=tint
        )

        # Draw mid part
        mid_x = x + self.left_width
        mid_width = size[0] - self.left_width - self.right_width
        ImGui.DrawTextureInDrawList(
            pos=(mid_x, y),
            size=(mid_width, size[1]),
            texture_path=self.texture,
            uv0=self.mid_offset[:2],
            uv1=self.mid_offset[2:],
            tint=tint
        )

        # Draw right part
        right_x = x + size[0] - self.right_width
        ImGui.DrawTextureInDrawList(
            pos=(right_x, y),
            size=(self.right_width, size[1]),
            texture_path=self.texture,
            uv0=self.right_offset[:2],
            uv1=self.right_offset[2:],
            tint=tint
        )

    def draw_in_background_drawlist(self, x: float, y: float, size: tuple[float, float], tint=(255, 255, 255, 255), overlay_name : str = ""):        
        Overlay().BeginDraw(overlay_name)
        
        # Draw left part
        Overlay().DrawTexturedRectExtended((x, y), (self.left_width, size[1]), self.texture, self.left_offset[:2], self.left_offset[2:], tint)
        
        # Draw mid part
        mid_x = x + self.left_width
        mid_width = size[0] - self.left_width - self.right_width
        Overlay().DrawTexturedRectExtended((mid_x, y), (mid_width, size[1]), self.texture, self.mid_offset[:2], self.mid_offset[2:], tint)

        # Draw right part
        right_x = x + size[0] - self.right_width
        Overlay().DrawTexturedRectExtended((right_x, y), (self.right_width, size[1]), self.texture, self.right_offset[:2], self.right_offset[2:], tint)


        Overlay().EndDraw()

class MapTexture:
    """
    Represents a UI element with multiple states (Normal, Hovered, etc.)
    mapped to different regions of a texture atlas.
    """

    def __init__(
        self,
        texture: str,
        texture_size: tuple[float, float],
        size: tuple[float, float],
        normal: tuple[float, float] = (0, 0),
        hovered: tuple[float, float] | None = None,
        active: tuple[float, float] | None = None,
        disabled: tuple[float, float] | None = None,
    ):
        self.texture = texture
        self.texture_size = texture_size
        self.size = size
        self.width, self.height = size

        self.normal_offset = self._make_uv(normal)
        self.hovered_offset = self._make_uv(hovered) if hovered else (0, 0, 1, 1)
        self.active_offset = self._make_uv(active) if active else (0, 0, 1, 1)
        self.disabled_offset = self._make_uv(disabled) if disabled else (0, 0, 1, 1)

    def _make_uv(self, pos: tuple[float, float]) -> tuple[float, float, float, float]:
        x, y = pos
        w, h = self.texture_size
        sx, sy = self.size
        return x / w, y / h, (x + sx) / w, (y + sy) / h

    def get_uv(self, state: TextureState) -> tuple[float, float, float, float]:
        match state:
            case TextureState.Normal: return self.normal_offset
            case TextureState.Hovered: return self.hovered_offset
            case TextureState.Active: return self.active_offset
            case TextureState.Disabled: return self.disabled_offset
        return self.normal_offset  # Fallback in case of unexpected state

    def draw_in_drawlist(
        self,
        x: float,
        y: float,
        size: tuple[float, float],
        state: TextureState = TextureState.Normal,
        tint=(255, 255, 255, 255)
    ):
        uv = self.get_uv(state)
        ImGui.DrawTextureInDrawList(
            pos=(x, y),
            size=size,
            texture_path=self.texture,
            uv0=uv[:2],
            uv1=uv[2:],
            tint=tint,
        )

    def draw_in_background_drawlist(
        self,
        x: float,
        y: float,
        size: tuple[float, float],
        state: TextureState = TextureState.Normal,
        tint=(255, 255, 255, 255),
        overlay_name: str = ""
    ):
        uv = self.get_uv(state)
        Overlay().BeginDraw(overlay_name)

        Overlay().DrawTexturedRectExtended((x, y), size, self.texture, uv[:2], uv[2:], tint)

        Overlay().EndDraw()

class ThemeTexture:
    PlaceHolderTexture = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "placeholder.png"),
        texture_size = (1, 1),
        size = (1, 1),
        normal=(0, 0)
    )
    
    def __init__(
        self,
        *args: tuple[Style.StyleTheme, SplitTexture | MapTexture],
    ):
        self.textures: dict[Style.StyleTheme, SplitTexture | MapTexture] = {}

        for theme, texture in args:
            self.textures[theme] = texture

    def get_texture(self, theme: Style.StyleTheme | None = None) -> SplitTexture | MapTexture:
        theme = theme or ImGui.get_style().Theme
        return self.textures.get(theme, ThemeTexture.PlaceHolderTexture)

class ThemeTextures(Enum):  
    Empty_Pixel = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "empty_pixel.png"),
        texture_size = (1, 1),
        size = (1, 1),
        normal=(0, 0)
    )
    
    TravelCursor = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "travel_cursor.png"),
        texture_size=(32, 32),
        size=(32, 32),
        normal=(0, 0)
    )

    ScrollGrab_Top = SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_scrollgrab.png"),
        texture_size=(16, 16),
        left=(0, 0, 5, 7),
        mid=(5, 0, 10, 7),
        right=(10, 0, 16, 7),   
    )
    
    ScrollGrab_Middle = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_scrollgrab.png"),
        texture_size=(16, 16),
        size=(16, 2),
        normal=(0, 7)
    )
    
    Scroll_Bg = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_scroll_background.png"),
        texture_size=(16, 16),
        size=(16, 16),
        normal=(0, 0)
    )

    ScrollGrab_Bottom = SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_scrollgrab.png"),
        texture_size=(16, 16),
        left=(0, 9, 5, 16),
        mid=(5, 9, 10, 16),
        right=(10, 9, 16, 16),    
    )            
    
    RightButton = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_left_right.png"),
        texture_size=(64, 16),
        size=(14, 16),
        normal=(1, 0)
    )
    
    LeftButton = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_left_right.png"),
        texture_size=(64, 16),
        size=(14, 16),
        normal = (17, 0),
        active = (49, 0),
    )
    
    Horizontal_ScrollGrab_Top = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_horizontal_scrollgrab.png"),
        texture_size=(16, 16),
        size=(7, 16),
        normal=(0, 0),
    )
    
    Horizontal_ScrollGrab_Middle = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_horizontal_scrollgrab.png"),
        texture_size=(16, 16),
        size=(2, 16),
        normal=(7, 0)
    )

    Horizontal_ScrollGrab_Bottom = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_horizontal_scrollgrab.png"),
        texture_size=(16, 16),
        size=(7, 16),
        normal=(9, 0),   
    )   
    
    Horizontal_Scroll_Bg = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_horizontal_scroll_background.png"),
        texture_size=(16, 16),
        size=(16, 16),
        normal=(0, 0)
    )                         
    
    CircleButtons = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_profession_circle_buttons.png"),
        texture_size=(256, 128),
        size=(32, 32),
        active=(192, 96),
        normal=(224, 96)
    )
    
    UpButton = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_up_down.png"),
        texture_size=(64, 16),
        size=(14, 16),
        normal=(1, 0)
    )
    
    DownButton = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_up_down.png"),
        texture_size=(64, 16),
        size=(14, 16),
        normal = (17, 0),
        active = (49, 0),
    )
    
    
        
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
        left= (1, 0, 6, 16),
        mid= (7, 0, 26, 16),
        right= (27, 0, 31, 16),
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_input_inactive.png"),
        texture_size=(32, 16),
        left= (1, 0, 6, 16),
        mid= (7, 0, 26, 16),
        right= (27, 0, 31, 16),
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
    
    Quest_Objective_Bullet_Point = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_quest_objective_bullet_point.png"),
        texture_size = (32, 16),
        size = (13, 13),
        normal=(0, 0),
        active=(13, 0),
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_quest_objective_bullet_point.png"),
        texture_size = (32, 16),
        size = (13, 13),
        normal=(0, 0),
        active=(13, 0),
    )),
    )
    
    Close_Button = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_close_button_atlas.png"),
        texture_size = (64, 16),
        size = (12, 12),
        normal=(1, 1),
        hovered=(17, 1),
        active=(33, 1),
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_close_button_atlas.png"),
        texture_size = (64, 16),
        size = (12, 12),
        normal=(1, 1),
        hovered=(17, 1),
        active=(33, 1),
    )),
    )
    
    Title_Bar = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_title_frame_atlas.png"),
        texture_size=(128, 32),
        left=(0, 6, 18, 32),
        mid=(19, 6, 109, 32),
        right=(110, 6, 128, 32)
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_title_frame_atlas.png"),
        texture_size=(128, 32),
        left=(0, 6, 18, 32),
        mid=(19, 6, 109, 32),
        right=(110, 6, 128, 32)
    )),
    )
    
    Window_Frame_Top = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 0, 18, 40),
        right=(110, 0, 128, 40),
        mid=(19, 0, 109, 40)
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 0, 18, 40),
        right=(110, 0, 128, 40),
        mid=(19, 0, 109, 40)
    )),
    )
    
    Window_Frame_Center = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 40, 18, 68),
        mid=(19, 40, 109, 68),
        right=(110, 40, 128, 68),
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 40, 18, 68),
        mid=(19, 40, 109, 68),
        right=(110, 40, 128, 68),
    )),
    )
    
    Window_Frame_Bottom = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 68, 18, 128),
        mid=(19, 68, 77, 128),
        right=(78, 68, 128, 128),
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 68, 18, 128),
        mid=(19, 68, 77, 128),
        right=(78, 68, 128, 128),
    )),
    )
    
    Window_Frame_Top_NoTitleBar = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_frame_atlas_no_titlebar.png"),
        texture_size=(128, 128),
        left=(0, 0, 18, 51),
        right=(110, 0, 128, 51),
        mid=(19, 0, 109, 51)
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas_no_titlebar.png"),
        texture_size=(128, 128),
        left=(0, 0, 18, 51),
        right=(110, 0, 128, 51),
        mid=(19, 0, 109, 51)
    )),
    )
    
    Window_Frame_Bottom_No_Resize = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_frame_atlas_no_resize.png"),
        texture_size=(128, 128),
        left=(0, 68, 18, 128),
        mid=(19, 68, 77, 128),
        right=(78, 68, 128, 128),
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas_no_resize.png"),
        texture_size=(128, 128),
        left=(0, 68, 18, 128),
        mid=(19, 68, 77, 128),
        right=(78, 68, 128, 128),
    )),
    )
    
    Separator = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_separator.png"),
        texture_size = (32, 4),
        size = (32, 4),
        normal = (0, 0),
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_separator.png"),
        texture_size = (32, 4),
        size = (32, 4),
        normal = (0, 0),
    )),
    )
    
    ProgressBarFrame = ThemeTexture(
    (Style.StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_frame.png"),
        texture_size=(16, 16),
        left= (1, 1, 2, 14),
        mid= (3, 1, 12, 14),
        right= (13, 1, 14, 14),
    )),
    (Style.StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_frame.png"),
        texture_size=(16, 16),
        left= (1, 1, 2, 14),
        mid= (3, 1, 12, 14),
        right= (13, 1, 14, 14),
    )),
    )
    
    ProgressBarProgressCursor = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_highlight.png"),
        texture_size=(16, 16),
        size= (16, 16),
        normal = (0, 0)
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_highlight.png"),
        texture_size=(16, 16),
        size= (16, 16),
        normal = (0, 0)
    )),
    )
    
    ProgressBarProgress = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (0, 0),
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (0, 0),
    )),
    )
    
    ProgressBarBackground = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (6, 0),
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (6, 0),
    )),
    )   
    
    BulletPoint = ThemeTexture(
    (Style.StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_bullet_point.png"),
        texture_size = (16, 16),
        size = (16, 16),
        normal = (0, 0),
    )),
    (Style.StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_bullet_point.png"),
        texture_size = (16, 16),
        size = (16, 16),
        normal = (0, 0),
    )),
    )   
    
class ControlAppearance(Enum):
    Default = 0
    Primary = 1
    Danger = 2
    
class ImGui:           
    class ImGuiIniReader:
        class ImGuiWindowConfig:
            def __init__(self, pos=(0.0, 0.0), size=(0.0, 0.0), collapsed=False):
                self.pos = pos              # tuple[float, float]
                self.size = size            # tuple[float, float]
                self.collapsed = collapsed  # bool

            def __repr__(self):
                return f"ImGuiWindowConfig(pos={self.pos}, size={self.size}, collapsed={self.collapsed})"
            
        def __init__(self):
            self.path = Path("imgui.ini")
            self.windows: dict[str, "ImGui.ImGuiIniReader.ImGuiWindowConfig"] = {}
            self._parse()

        def _parse(self):
            current_window = None
            current_data = {}

            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(";"):
                        continue

                    # section header: [Window][WindowName]
                    if line.startswith("[Window]"):
                        # save last window before starting new
                        if current_window and current_data:
                            self._store_window(current_window, current_data)
                            current_data = {}

                        start = line.find("][") + 2
                        end = line.rfind("]")
                        current_window = line[start:end]

                    elif "=" in line and current_window:
                        key, value = line.split("=", 1)
                        current_data[key.strip()] = value.strip()

                # save last one
                if current_window and current_data:
                    self._store_window(current_window, current_data)

        def _store_window(self, name: str, data: dict[str, str]):
            pos = tuple(map(float, data.get("Pos", "0,0").split(",")))
            size = tuple(map(float, data.get("Size", "0,0").split(",")))
            collapsed = data.get("Collapsed", "0") == "1"

            self.windows[name] = ImGui.ImGuiIniReader.ImGuiWindowConfig(pos, size, collapsed)

        def get(self, window: str) -> "ImGui.ImGuiIniReader.ImGuiWindowConfig | None":
            return self.windows.get(window)
    
    class ImGuiStyleVar(IntEnum):
        Alpha = 0
        DisabledAlpha = 1
        WindowPadding = 2
        WindowRounding = 3
        WindowBorderSize = 4
        WindowMinSize = 5
        WindowTitleAlign = 6
        ChildRounding = 7
        ChildBorderSize = 8
        PopupRounding = 9
        PopupBorderSize = 10
        FramePadding = 11
        FrameRounding = 12
        FrameBorderSize = 13
        ItemSpacing = 14
        ItemInnerSpacing = 15
        IndentSpacing = 16
        CellPadding = 17
        ScrollbarSize = 18
        ScrollbarRounding = 19
        GrabMinSize = 20
        GrabRounding = 21
        TabRounding = 22
        ButtonTextAlign = 23
        SelectableTextAlign = 24
        SeparatorTextBorderSize = 25
        SeparatorTextAlign = 26
        SeparatorTextPadding = 27
        COUNT = 28

    class ImGuiTabItemFlags(IntEnum):
        NoFlag = 0
        UnsavedDocument               = 1 << 0   ## Display a dot next to the title + tab is selected when clicking the X + closure is not assumed (will wait for user to stop submitting the tab). Otherwise closure is assumed when pressing the X, so if you keep submitting the tab may reappear at end of tab bar.
        SetSelected                   = 1 << 1   ## Trigger flag to programmatically make the tab selected when calling BeginTabItem()
        NoCloseWithMiddleMouseButton  = 1 << 2   ## Disable behavior of closing tabs (that are submitted with p_open != NULL) with middle mouse button. You can still repro this behavior on user's side with if (IsItemHovered() && IsMouseClicked(2)) *p_open = false.
        NoPushId                      = 1 << 3   ## Don't call PushID(tab->ID)/PopID() on BeginTabItem()/EndTabItem()
        NoTooltip                     = 1 << 4   ## Disable tooltip for the given tab
        NoReorder                     = 1 << 5   ## Disable reordering this tab or having another tab cross over this tab
        Leading                       = 1 << 6   ## Enforce the tab position to the left of the tab bar (after the tab list popup button)
        Trailing                      = 1 << 7   ## Enforce the tab position to the right of the tab bar (before the scrolling buttons)

    @staticmethod
    def push_style_color(idx: int, col: tuple[float, float, float, float]):
        PyImGui.push_style_color(idx, col)
        pass
    
    @staticmethod
    def pop_style_color(count: int = 1):
        PyImGui.pop_style_color(count)
        pass

    @staticmethod
    def is_mouse_in_rect(rect: tuple[float, float, float, float]) -> bool:
        """
        Check if the mouse cursor is within a specified rectangle.
        Args:
            rect (tuple[float, float, float, float]): The rectangle defined by (x, y, width, height).
        """
        pyimgui_io = PyImGui.get_io()
        mouse_pos = (pyimgui_io.mouse_pos_x, pyimgui_io.mouse_pos_y)
        
        return (rect[0] <= mouse_pos[0] <= rect[0] + rect[2] and
                rect[1] <= mouse_pos[1] <= rect[1] + rect[3])
        
    @staticmethod
    def DrawTexture(texture_path: str, width: float = 32.0, height: float = 32.0):
        Overlay().DrawTexture(texture_path, width, height)
        
    @staticmethod
    def DrawTextureExtended(texture_path: str, size: tuple[float, float],
                            uv0: tuple[float, float] = (0.0, 0.0),
                            uv1: tuple[float, float] = (1.0, 1.0),
                            tint: tuple[int, int, int, int] = (255, 255, 255, 255),
                            border_color: tuple[int, int, int, int] = (0, 0, 0, 0)):
        Overlay().DrawTextureExtended(texture_path, size, uv0, uv1, tint, border_color)
     
    @staticmethod   
    def DrawTexturedRect(x: float, y: float, width: float, height: float, texture_path: str):
        Overlay().BeginDraw()
        Overlay().DrawTexturedRect(x, y, width, height, texture_path)
        Overlay().EndDraw()
        
    @staticmethod
    def DrawTexturedRectExtended(pos: tuple[float, float], size: tuple[float, float], texture_path: str,
                                    uv0: tuple[float, float] = (0.0, 0.0),  
                                    uv1: tuple[float, float] = (1.0, 1.0),
                                    tint: tuple[int, int, int, int] = (255, 255, 255, 255)):
        Overlay().BeginDraw()
        Overlay().DrawTexturedRectExtended(pos, size, texture_path, uv0, uv1, tint)
        Overlay().EndDraw()
        
    @staticmethod
    def ImageButton(caption: str, texture_path: str, width: float = 32.0, height: float = 32.0, frame_padding: int = -1) -> bool:
        return Overlay().ImageButton(caption, texture_path, width, height, frame_padding)
    
    @staticmethod
    def ImageButtonExtended(caption: str, texture_path: str, size: tuple[float, float],
                            uv0: tuple[float, float] = (0.0, 0.0),
                            uv1: tuple[float, float] = (1.0, 1.0),
                            bg_color: tuple[int, int, int, int] = (0, 0, 0, 0),
                            tint_color: tuple[int, int, int, int] = (255, 255, 255, 255),
                            frame_padding: int = -1) -> bool:
        return Overlay().ImageButtonExtended(caption, texture_path, size, uv0, uv1, bg_color, tint_color, frame_padding)
    
    @staticmethod
    def DrawTextureInForegound(pos: tuple[float, float], size: tuple[float, float], texture_path: str,
                       uv0: tuple[float, float] = (0.0, 0.0),
                       uv1: tuple[float, float] = (1.0, 1.0),
                       tint: tuple[int, int, int, int] = (255, 255, 255, 255)):
        Overlay().DrawTextureInForegound(pos, size, texture_path, uv0, uv1, tint)
      
    @staticmethod  
    def DrawTextureInDrawList(pos: tuple[float, float], size: tuple[float, float], texture_path: str,
                       uv0: tuple[float, float] = (0.0, 0.0),
                       uv1: tuple[float, float] = (1.0, 1.0),
                       tint: tuple[int, int, int, int] = (255, 255, 255, 255)):
        Overlay().DrawTextureInDrawList(pos, size, texture_path, uv0, uv1, tint)
    
    @staticmethod
    def GetModelIDTexture(model_id: int) -> str:
        """
        Purpose: Get the texture path for a given model_id.
        Args:
            model_id (int): The model ID to get the texture for.
        Returns: str: The texture path or a fallback image path if not found.
        """
        return get_texture_for_model(model_id)
        
    @staticmethod
    def show_tooltip(text: str):
        """
        Purpose: Display a tooltip with the provided text.
        Args:
            text (str): The text to display in the tooltip.
        Returns: None
        """
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.text(text)
            PyImGui.end_tooltip()
    
    @staticmethod
    def colored_button(label: str, button_color:Color, hovered_color:Color, active_color:Color, width=0, height=0):
        clicked = False

        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, button_color.to_tuple_normalized())  # On color
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hovered_color.to_tuple_normalized())  # Hover color
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, active_color.to_tuple_normalized())

        clicked = PyImGui.button(label, width, height)

        PyImGui.pop_style_color(3)
        
        return clicked

    @staticmethod
    def floating_button(caption, x, y, width = 18, height = 18 , color: Color = Color(255, 255, 255, 255), name = ""):
        if not name:
            name = caption
        
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(width, height)

        flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize |
            PyImGui.WindowFlags.NoBackground
        )

        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, -1, -0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
        PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 0, 0, 0))  # Fully transparent
        
        # Transparent button face
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.0, 0.0, 0.0, 0.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.0, 0.0, 0.0, 0.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.0, 0.0, 0.0, 0.0))

        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color.to_tuple_normalized())
        result = False
        if PyImGui.begin(f"{caption}##invisible_buttonwindow{name}", flags):
            result = PyImGui.button(f"{caption}##floating_button{name}", width=width, height=height)

            
        PyImGui.end()
        PyImGui.pop_style_color(5)  # Button, Hovered, Active, Text, WindowBg
        PyImGui.pop_style_var(2)

        return result
    
    @staticmethod
    def floating_toggle_button(
        caption: str,
        x: float,
        y: float,
        v: bool,
        width: int = 18,
        height: int = 18,
        color: Color = Color(255, 255, 255, 255),
        name: str = ""
    ) -> bool:
        """
        Purpose: Create a floating toggle button with custom position and styling.
        Args:
            caption (str): Text to display on the button.
            x (float): X position on screen.
            y (float): Y position on screen.
            v (bool): Current toggle state.
            width (int): Button width.
            height (int): Button height.
            color (Color): Text color.
            name (str): Unique suffix name to avoid ID conflicts.
        Returns:
            bool: New toggle state.
        """
        if not name:
            name = caption

        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(width, height)

        flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize |
            PyImGui.WindowFlags.NoBackground
        )

        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, -1, -0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0.0)

        PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 0, 0, 0))  # Fully transparent
        #PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color.to_tuple_normalized())

        if v:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.153, 0.318, 0.929, 1.0))  # ON color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.6, 0.6, 0.9, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.6, 0.6, 0.6, 1.0))
        else:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, color.to_tuple_normalized()) 
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered,  color.desaturate(0.9).to_tuple_normalized())
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  color.saturate(0.9).to_tuple_normalized())

        new_state = v
        if PyImGui.begin(f"{caption}##toggle_window{name}", flags):
            if PyImGui.button(f"{caption}##toggle_button{name}", width=width, height=height):
                new_state = not v
        PyImGui.end()

        PyImGui.pop_style_color(4)
        PyImGui.pop_style_var(2)

        return new_state

    @staticmethod
    def floating_checkbox(caption, state,  x, y, width = 18, height = 18 , color: Color = Color(255, 255, 255, 255)):
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
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 3, 5)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, color.to_tuple_normalized())
        
        result = state
        
        white = ColorPalette.GetColor("White")
        
        if PyImGui.begin(f"##invisible_window{caption}", flags):
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0.2, 0.3, 0.4, 0.1))  # Normal state color
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0.3, 0.4, 0.5, 0.1))  # Hovered state
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0.4, 0.5, 0.6, 0.1))  # Checked state
            PyImGui.push_style_color(PyImGui.ImGuiCol.CheckMark, color.shift(white, 0.5).to_tuple_normalized())  # Checkmark color

            result = PyImGui.checkbox(f"##floating_checkbox{caption}", state)
            PyImGui.pop_style_color(4)
        PyImGui.end()
        PyImGui.pop_style_var(3)
        PyImGui.pop_style_color(1)
        return result
            
    _last_font_scaled = False  # Module-level tracking flag
    @staticmethod
    def push_font(font_family: str, pixel_size: int):
        _available_sizes = [14, 22, 30, 46, 62, 124]
        _font_map = {
                "Regular": {
                    14: ImguiFonts.Regular_14,
                    22: ImguiFonts.Regular_22,
                    30: ImguiFonts.Regular_30,
                    46: ImguiFonts.Regular_46,
                    62: ImguiFonts.Regular_62,
                    124: ImguiFonts.Regular_124,
                },
                "Bold": {
                    14: ImguiFonts.Bold_14,
                    22: ImguiFonts.Bold_22,
                    30: ImguiFonts.Bold_30,
                    46: ImguiFonts.Bold_46,
                    62: ImguiFonts.Bold_62,
                    124: ImguiFonts.Bold_124,
                },
                "Italic": {
                    14: ImguiFonts.Italic_14,
                    22: ImguiFonts.Italic_22,
                    30: ImguiFonts.Italic_30,
                    46: ImguiFonts.Italic_46,
                    62: ImguiFonts.Italic_62,
                    124: ImguiFonts.Italic_124,
                },
                "BoldItalic": {
                    14: ImguiFonts.BoldItalic_14,
                    22: ImguiFonts.BoldItalic_22,
                    30: ImguiFonts.BoldItalic_30,
                    46: ImguiFonts.BoldItalic_46,
                    62: ImguiFonts.BoldItalic_62,
                    124: ImguiFonts.BoldItalic_124,
                }
            }

        global _last_font_scaled
        _last_font_scaled = False  # Reset the flag each time a font is pushed
        if pixel_size < 1:
            raise ValueError("Pixel size must be a positive integer")
        
        family_map = _font_map.get(font_family)
        if not family_map:
            raise ValueError(f"Unknown font family '{font_family}'")

        # Exact match
        if pixel_size in _available_sizes:
            font_enum = family_map[pixel_size]
            PyImGui.push_font(font_enum.value)
            _last_font_scaled = False
            return

        # Scale down using the next available size
        for defined_size in _available_sizes:
            if defined_size > pixel_size:
                font_enum = family_map[defined_size]
                scale = pixel_size / defined_size
                PyImGui.push_font_scaled(font_enum.value, scale)
                _last_font_scaled = True
                return

        # If requested size is larger than the largest available, scale up
        largest_size = _available_sizes[-1]
        font_enum = family_map[largest_size]
        scale = pixel_size / largest_size
        PyImGui.push_font_scaled(font_enum.value, scale)
        _last_font_scaled = True

    @staticmethod
    def pop_font():
        global _last_font_scaled
        if _last_font_scaled:
            PyImGui.pop_font_scaled()
        else:
            PyImGui.pop_font()

    @staticmethod
    def table(title:str, headers, data):
        """
        Purpose: Display a table using PyImGui.
        Args:
            title (str): The title of the table.
            headers (list of str): The header names for the table columns.
            data (list of values or tuples): The data to display in the table. 
                - If it's a list of single values, display them in one column.
                - If it's a list of tuples, display them across multiple columns.
            row_callback (function): Optional callback function for each row.
        Returns: None
        """
        if len(data) == 0:
            return  # No data to display

        first_row = data[0]
        if isinstance(first_row, tuple):
            num_columns = len(first_row)
        else:
            num_columns = 1  # Single values will be displayed in one column

        # Start the table with dynamic number of columns
        if PyImGui.begin_table(title, num_columns, PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable):
            for i, header in enumerate(headers):
                PyImGui.table_setup_column(header)
            PyImGui.table_headers_row()

            for row in data:
                PyImGui.table_next_row()
                if isinstance(row, tuple):
                    for i, cell in enumerate(row):
                        PyImGui.table_set_column_index(i)
                        PyImGui.text(str(cell))
                else:
                    PyImGui.table_set_column_index(0)
                    PyImGui.text(str(row))

            PyImGui.end_table()

    @staticmethod
    def DrawTextWithTitle(title, text_content, lines_visible=10):
        """
        Display a title and a scrollable text area with proper wrapping.
        """
        margin = 20
        line_padding = 4

        # Display title
        PyImGui.text(title)
        PyImGui.spacing()

        # Get window width with margin adjustments
        window_width = max(PyImGui.get_window_size()[0] - margin, 100)

        # Calculate content height based on number of visible lines
        line_height = PyImGui.get_text_line_height() + line_padding
        content_height = max(lines_visible * line_height, 100)

        # Set up a scrollable child window
        if PyImGui.begin_child(f"ScrollableTextArea_{title}", size=(window_width, content_height), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
            PyImGui.text_wrapped(text_content + "\n" + Py4GW.Console.GetCredits())
            PyImGui.end_child()

    class WindowModule:
        _windows : dict[str, 'ImGui.WindowModule'] = {}
        
        def __init__(self, module_name="", window_name="", window_size=(100,100), window_pos=(0,0), window_flags=PyImGui.WindowFlags.NoFlag, collapse= False, can_close=False, forced_theme : Style.StyleTheme | None = None):
            self.module_name = module_name
            if not self.module_name:
                return
            
            self.can_close = can_close
            self.can_resize = True  # Default to True, can be set to False later
            self.window_name = window_name if window_name else module_name
            ## Remove everything after '##'
            self.window_display_name = self.window_name.split("##")[0]
            self.window_size : tuple[float, float] = window_size
            self.window_name_size : tuple[float, float] = PyImGui.calc_text_size(self.window_display_name)
            
            self.__decorated_window_min_size = (self.window_name_size[0] + 40, 32.0) # Internal use only
            self.__decorators_left = window_pos[0] - 15 # Internal use only
            self.__decorators_top = window_pos[1] - (26) # Internal use only
            
            self.__decorators_right = self.__decorators_left + window_size[0] + 30 # Internal use only
            self.__decorators_bottom = self.__decorators_top + window_size[1] + 14 + (26) # Internal use only
            
            self.__decorators_width = self.__decorators_right - self.__decorators_left # Internal use only
            self.__decorators_height = self.__decorators_bottom - self.__decorators_top # Internal use only
            
            self.__close_button_rect = (self.__decorators_right - 29, self.__decorators_top + 9, 11, 11) # Internal use only
            self.__title_bar_rect = (self.__decorators_left + 5, self.__decorators_top + 2, self.__decorators_width - 10, 26) # Internal use only
            
            self.__resize = False # Internal use only
            self.__set_focus = False # Internal use only

            self.__dragging = False # Internal use only
            self.__drag_started = False # Internal use only

            self.theme : Style.StyleTheme | None = forced_theme
            self.__current_theme = self.theme if self.theme is not None else ImGui.get_style().Theme # Internal use only
            
            self.open = True  # Default to open
            self.collapse = collapse
            self.expanded = not collapse  # Default to expanded if not collapsed
            self.open = True  # Default to open
            
            if window_pos == (0,0):
                overlay = Overlay()
                screen_width, screen_height = overlay.GetDisplaySize().x, overlay.GetDisplaySize().y
                #set position to the middle of the screen
                self.window_pos = (screen_width / 2 - window_size[0] / 2, screen_height / 2 - window_size[1] / 2)
            else:
                self.window_pos = window_pos
                
            self.end_pos = window_pos  # Initialize end_pos to window_pos
            self.window_flags = window_flags
            self.first_run = True

            #debug variables
            self.collapsed_status = True
            self.tracking_position = self.window_pos
            ImGui.WindowModule._windows[self.window_name] = self

        def initialize(self):
            if not self.module_name:
                return
            
            if self.first_run:
                PyImGui.set_next_window_size(self.window_size[0], self.window_size[1])     
                PyImGui.set_next_window_pos(self.window_pos[0], self.window_pos[1])
                PyImGui.set_next_window_collapsed(self.collapse, 0)
                self.first_run = False

        def begin(self, p_open: Optional[bool] = None, flags: PyImGui.WindowFlags = PyImGui.WindowFlags.NoFlag) -> bool:            
            self.__current_theme = self.get_theme()
            ImGui.push_theme_window_style(self.__current_theme)      
                                  
            if p_open is not None:
                self.open = p_open
                
            if flags != PyImGui.WindowFlags.NoFlag:
                self.window_flags = flags
        
            is_expanded = self.expanded
            is_first_run = self.first_run
            
            self.can_resize = (int(self.window_flags) & int(PyImGui.WindowFlags.NoResize)) == 0 and (int(self.window_flags) & int(PyImGui.WindowFlags.AlwaysAutoResize)) == 0
            
            if self.first_run:
                self.initialize()
                
            match (self.__current_theme):
                case Style.StyleTheme.Guild_Wars:
                    has_always_auto_resize = (int(self.window_flags) & int(PyImGui.WindowFlags.AlwaysAutoResize)) != 0
                    
                    # PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 10, 10)
                    internal_flags = int(PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoBackground) | int(self.window_flags)
                    self.__dragging = PyImGui.is_mouse_dragging(0, -1) and self.__dragging and self.__drag_started
                    if not PyImGui.is_mouse_dragging(0, -1) and not PyImGui.is_mouse_down(0):
                        self.__drag_started = False
                                
                    if self.open and is_expanded: 
                        if not is_first_run:
                            if self.__resize or self.window_size[0] < self.__decorated_window_min_size[0] or self.window_size[1] < self.__decorated_window_min_size[1]:
                                if not has_always_auto_resize:
                                    self.window_size = (max(self.__decorated_window_min_size[0], self.window_size[0]), max(self.__decorated_window_min_size[1], self.window_size[1]))
                                    PyImGui.set_next_window_size((self.window_size[0], self.window_size[1]), PyImGui.ImGuiCond.Always)            
                                self.__resize = False
                        
                    # ImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 0, 0, 0.85))
                        
                    if not is_expanded:
                        # Remove PyImGui.WindowFlags.MenuBar and PyImGui.WindowFlags.AlwaysAutoResize from internal_flags when not expanded
                        internal_flags &= ~int(PyImGui.WindowFlags.MenuBar)
                        internal_flags &= ~int(PyImGui.WindowFlags.AlwaysAutoResize)
                        internal_flags |= int(PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse| PyImGui.WindowFlags.NoResize| PyImGui.WindowFlags.NoMouseInputs)
                        
                    if self.__set_focus:
                        internal_flags &= ~int(PyImGui.WindowFlags.AlwaysAutoResize)
                        
                    _, open = PyImGui.begin_with_close(name = self.window_name, p_open=self.open, flags=internal_flags)

                    # ImGui.pop_style_color(1)
                                            
                    self.open = open               
                                    
                    if self.__set_focus and not self.__dragging and not self.__drag_started:
                        PyImGui.set_window_focus(self.window_name)
                        self.__set_focus = False
                    
                    if self.__dragging:
                        PyImGui.set_window_focus(self.window_name)
                        PyImGui.set_window_focus(f"{self.window_name}##titlebar_fake")

                    if self.open:
                        self.__draw_decorations()

                    # PyImGui.pop_style_var(1)
                    
                    if has_always_auto_resize:                    
                        cursor = PyImGui.get_cursor_pos()
                        PyImGui.dummy(int(self.window_name_size[0] + 20), 0)
                        PyImGui.set_cursor_pos(cursor[0], cursor[1])
                                    
                case Style.StyleTheme.ImGui | Style.StyleTheme.Minimalus:  
                    if self.can_close:              
                        self.expanded, self.open = PyImGui.begin_with_close(name = self.window_name, p_open=self.open, flags=self.window_flags)
                    else:
                        self.open = PyImGui.begin(self.window_name, self.window_flags) 
                        self.expanded = PyImGui.is_window_collapsed() == False   
            
            if is_expanded and self.expanded and self.open and not self.__dragging:
                self.window_size = PyImGui.get_window_size()
                          
            ImGui.pop_theme_window_style(self.__current_theme)    
            
            return self.open
        
        def process_window(self):
            if not self.module_name:
                return
            
            self.collapsed_status = PyImGui.is_window_collapsed()
            self.end_pos = PyImGui.get_window_pos()

        def end(self):
            PyImGui.end()

             
            
            """ INI FILE ROUTINES NEED WORK 
            if end_pos[0] != window_module.window_pos[0] or end_pos[1] != window_module.window_pos[1]:
                ini_handler.write_key(module_name + " Config", "config_x", str(int(end_pos[0])))
                ini_handler.write_key(module_name + " Config", "config_y", str(int(end_pos[1])))

            if new_collapsed != window_module.collapse:
                ini_handler.write_key(module_name + " Config", "collapsed", str(new_collapsed))
            """
        
        def get_theme(self) -> "Style.StyleTheme":
            """
            Returns the current theme of the ImGui module.
            """

            theme = self.theme if self.theme else ImGui.get_style().Theme

            return theme
             
        def __draw_decorations(self):                  
            has_title_bar = (int(self.window_flags) & int(PyImGui.WindowFlags.NoTitleBar)) == 0
            
            if self.expanded and self.open:
                window_pos = PyImGui.get_window_pos()
                window_size = PyImGui.get_window_size()            
                                                    
                self.__decorators_left = window_pos[0] - 15
                self.__decorators_top = window_pos[1] - (26 if has_title_bar else 5)
                
                self.__decorators_right = self.__decorators_left + window_size[0] + 30
                self.__decorators_bottom = self.__decorators_top + window_size[1] + 14 + (26 if has_title_bar else 5)
                
                self.__decorators_width = self.__decorators_right - self.__decorators_left
                self.__decorators_height = self.__decorators_bottom - self.__decorators_top
                self.__close_button_rect = (self.__decorators_right - 29, self.__decorators_top + 9, 11, 11)

                PyImGui.push_clip_rect(self.__decorators_left, self.__decorators_top, self.__decorators_width, self.__decorators_height, False)   
                state = TextureState.Normal
                                
                if ImGui.is_mouse_in_rect(self.__close_button_rect) and ((int(self.window_flags) & int(PyImGui.WindowFlags.NoMouseInputs)) == 0):
                    if PyImGui.is_mouse_down(0):
                        state = TextureState.Active
                        open = False
                    else:
                        state = TextureState.Hovered
                                        
                # Draw the background
                has_background = not self.window_flags or ((int(self.window_flags) & int(PyImGui.WindowFlags.NoBackground)) == 0)                
                if has_background:
                    ThemeTextures.Empty_Pixel.value.draw_in_drawlist(
                        x=self.__decorators_left + 15,
                        y=self.__decorators_top + 5,
                        size=(self.__decorators_width - 30, self.__decorators_height - 15),
                        tint=(0,0,0,215)
                    )

                if self.can_resize:
                    ThemeTextures.Window_Frame_Bottom.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_bottom - 57,
                        size=(self.__decorators_width - 10, 60)
                    )
                else:
                    ThemeTextures.Window_Frame_Bottom_No_Resize.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_bottom - 57,
                        size=(self.__decorators_width - 10, 60)
                    )

                ThemeTextures.Window_Frame_Center.value.get_texture().draw_in_drawlist(
                    x=self.__decorators_left + 5,
                    y=self.__decorators_top + (26 if has_title_bar else 11) + 35,
                    size=(self.__decorators_width - 10, self.__decorators_height - 35 - 60)
                )
                
                
                if has_title_bar:      
                    ThemeTextures.Window_Frame_Top.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_top + 26,
                        size=(self.__decorators_width - 10, 35)
                    )

                    ThemeTextures.Title_Bar.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_top,
                        size=(self.__decorators_width - 10, 26)
                    )
                
                    if self.can_close:
                        ThemeTextures.Empty_Pixel.value.draw_in_drawlist(
                            x=self.__close_button_rect[0] - 1,
                            y=self.__close_button_rect[1] - 1,
                            size=(self.__close_button_rect[2] + 2, self.__close_button_rect[3] + 2),
                            tint=(0,0,0,255)
                        )

                        ThemeTextures.Close_Button.value.get_texture().draw_in_drawlist(
                            x=self.__close_button_rect[0],
                            y=self.__close_button_rect[1],
                            size=self.__close_button_rect[2:],
                            state=state
                        )
                        
                    self.__title_bar_rect = (self.__decorators_left + 10, self.__decorators_top + 2, self.__decorators_width - 10, 26)
                  
                    # Draw the title text
                    PyImGui.push_clip_rect(
                        self.__title_bar_rect[0] + 15,
                        self.__title_bar_rect[1] + 7,
                        self.__title_bar_rect[2] - 15 - 29,
                        self.__title_bar_rect[3] - 7,
                        False
                    )
                    PyImGui.draw_list_add_text(self.__title_bar_rect[0] + 15, self.__title_bar_rect[1] + 7, Utils.RGBToColor(255,255,255,255), self.window_display_name)
                    PyImGui.pop_clip_rect()
                    
                    self.__draw_title_bar_fake(self.__title_bar_rect)
                else:
                    ThemeTextures.Window_Frame_Top_NoTitleBar.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_top,
                        size=(self.__decorators_width - 10, 50)
                    )

            else:
                window_pos = PyImGui.get_window_pos()
                
                self.__decorators_left = window_pos[0] - 15
                self.__decorators_top = window_pos[1] - (26)

                self.__decorators_right = self.__decorators_left + self.__decorated_window_min_size[0] + 30
                self.__decorators_bottom = window_pos[1]

                self.__decorators_width = self.__decorators_right - self.__decorators_left
                self.__decorators_height = self.__decorators_bottom - self.__decorators_top
                self.__close_button_rect = (self.__decorators_right - 29, self.__decorators_top + 9, 11, 11)

                PyImGui.set_window_size(1, 1, PyImGui.ImGuiCond.Always)
    
                state = TextureState.Normal

                if ImGui.is_mouse_in_rect(self.__close_button_rect): 
                    if PyImGui.is_mouse_down(0):         
                        state = TextureState.Active
                    else:
                        state = TextureState.Hovered

                PyImGui.push_clip_rect(self.__decorators_left, self.__decorators_top + 5, self.__decorators_width, self.__decorators_height , False)
                ThemeTextures.Empty_Pixel.value.draw_in_drawlist(
                    x=self.__decorators_left + 15,
                    y=self.__decorators_top,
                    size=(self.__decorators_width - 30, 14),
                    tint=(0,0,0,215)
                )
                
                # PyImGui.push_clip_rect(self.__decorators_left, self.__decorators_top, self.__decorators_width - 15, self.__decorators_height + 30, False)   
                ThemeTextures.Window_Frame_Bottom_No_Resize.value.get_texture().draw_in_drawlist(
                    x=self.__decorators_left + 2,
                    y=self.__decorators_top - 12 + 8,
                    size=(self.__decorators_width - 5 , 40)
                )

                PyImGui.push_clip_rect(self.__decorators_left, self.__decorators_top, self.__decorators_width, self.__decorators_height + 30, False)

                if has_title_bar:
                    ThemeTextures.Title_Bar.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_top,
                        size=(self.__decorators_width - 10, 26)
                    )

                    if self.can_close:
                        ThemeTextures.Empty_Pixel.value.draw_in_drawlist(
                            x=self.__close_button_rect[0] - 1,
                            y=self.__close_button_rect[1] - 1,
                            size=(self.__close_button_rect[2] + 2, self.__close_button_rect[3] + 2),
                            tint=(0,0,0,255)
                        )

                        ThemeTextures.Close_Button.value.get_texture().draw_in_drawlist(
                            x=self.__close_button_rect[0],
                            y=self.__close_button_rect[1],
                            size=(self.__close_button_rect[2:]),
                            state=state
                        )

                    self.__title_bar_rect = (self.__decorators_left + 10, self.__decorators_top + 2, self.__decorators_width - 10, 26)
                 
                    PyImGui.push_clip_rect(
                        self.__title_bar_rect[0] + 15,
                        self.__title_bar_rect[1] + 7,
                        self.__title_bar_rect[2] - 15 - 29,
                        self.__title_bar_rect[3] - 7,
                        False
                    )
                    PyImGui.draw_list_add_text(self.__title_bar_rect[0] + 15, self.__title_bar_rect[1] + 7, Utils.RGBToColor(255,255,255,255), self.window_display_name)
                    PyImGui.pop_clip_rect()

                    self.__draw_title_bar_fake(self.__title_bar_rect)
                else:
                    ThemeTextures.Window_Frame_Top_NoTitleBar.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_top + 11,
                        size=(self.__decorators_width - 10, 50)
                    )

            PyImGui.pop_clip_rect()
            
        def __draw_title_bar_fake(self, __title_bar_rect):            
            can_interact = (int(self.window_flags) & int(PyImGui.WindowFlags.NoMouseInputs)) == 0
            
            PyImGui.set_next_window_pos(__title_bar_rect[0], __title_bar_rect[1])
            PyImGui.set_next_window_size(__title_bar_rect[2], __title_bar_rect[3])

            flags = (
                    PyImGui.WindowFlags.NoCollapse |
                    PyImGui.WindowFlags.NoTitleBar |
                    PyImGui.WindowFlags.NoScrollbar |
                    PyImGui.WindowFlags.NoScrollWithMouse |
                    PyImGui.WindowFlags.AlwaysAutoResize 
                    | PyImGui.WindowFlags.NoBackground
                )
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, -1, -0)
            ImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 1, 0, 0.0))  # Fully transparent
            PyImGui.begin(f"{self.window_name}##titlebar_fake", flags)
            PyImGui.invisible_button("##titlebar_dragging_area_1", __title_bar_rect[2] - (30 if self.can_close else 0), __title_bar_rect[3])
            self.__dragging = (PyImGui.is_item_active() or self.__dragging) and can_interact
                        
            if PyImGui.is_item_focused():
                self.__set_focus = True
                
            PyImGui.set_cursor_screen_pos(self.__close_button_rect[0] + self.__close_button_rect[2], self.__close_button_rect[1] + self.__close_button_rect[3])
            PyImGui.invisible_button("##titlebar_dragging_area_2", 15, __title_bar_rect[3])
            self.__dragging = (PyImGui.is_item_active() or self.__dragging) and can_interact
                    
            if PyImGui.is_item_focused():
                self.__set_focus = True
                
            # Handle Double Click to Expand/Collapse
            if PyImGui.is_mouse_double_clicked(0) and self.__set_focus:
                can_collapse = (int(self.window_flags) & int(PyImGui.WindowFlags.NoCollapse)) == 0                
                if can_collapse and can_interact:
                    self.expanded = not self.expanded
                    
                    if self.expanded:
                        self.__resize = True

            if self.can_close:
                PyImGui.set_cursor_screen_pos(self.__close_button_rect[0], self.__close_button_rect[1])
                if PyImGui.invisible_button(f"##Close", self.__close_button_rect[2] + 1, self.__close_button_rect[3] + 1) and can_interact:
                    self.open = False
                    self.__set_focus = False
                    
                    
            PyImGui.end()
            ImGui.pop_style_color(1)
            PyImGui.pop_style_var(1)
                                
            # Handle dragging
            if self.__dragging:   
                can_drag = (int(self.window_flags) & int(PyImGui.WindowFlags.NoMove)) == 0
        
                if can_drag:
                    if self.__drag_started:                    
                        delta = PyImGui.get_mouse_drag_delta(0, 0.0)
                        new_window_pos = (__title_bar_rect[0] + 5 + delta[0], __title_bar_rect[1] + __title_bar_rect[3] - 2 + delta[1])
                        PyImGui.reset_mouse_drag_delta(0)
                        PyImGui.set_window_pos(new_window_pos[0], new_window_pos[1], PyImGui.ImGuiCond.Always)
                    else:
                        self.__drag_started = True
                else:
                    self.__dragging = False
                    self.__drag_started = False
         
    @staticmethod     
    def PushTransparentWindow():
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowPadding,0.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowBorderSize,0.0)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding,0.0,0.0)
        
        flags=( PyImGui.WindowFlags.NoCollapse | 
                PyImGui.WindowFlags.NoTitleBar |
                PyImGui.WindowFlags.NoScrollbar |
                PyImGui.WindowFlags.NoScrollWithMouse |
                PyImGui.WindowFlags.AlwaysAutoResize |
                PyImGui.WindowFlags.NoResize |
                PyImGui.WindowFlags.NoBackground 
            ) 
        
        return flags

    @staticmethod
    def PopTransparentWindow():
        PyImGui.pop_style_var(4)

    # region Styles, Themes and Themed controls

    Styles : dict[Style.StyleTheme, Style] = {}
    __style_stack : list[Style] = []
    Selected_Style : Style

    @staticmethod
    def get_style() -> Style:
        return ImGui.__style_stack[0] if ImGui.__style_stack else ImGui.Selected_Style

    @staticmethod
    def push_theme(theme: Style.StyleTheme):
        if not theme in ImGui.Styles:
            ImGui.Styles[theme] = Style.load_theme(theme)
            
        style = ImGui.Styles[theme]
        ImGui.__style_stack.insert(0, style)
        style.push_style()

    @staticmethod
    def pop_theme():
        style = ImGui.get_style()
        style.pop_style()
        
        if ImGui.__style_stack:
            ImGui.__style_stack.pop(0)

    @staticmethod
    def set_theme(theme: Style.StyleTheme):
        ConsoleLog("ImGui Style", f"Setting theme to {theme.name}")
        
        if not theme in ImGui.Styles:
            ImGui.Styles[theme] = Style.load_theme(theme)
            
        ImGui.Selected_Style = ImGui.Styles[theme]
        ImGui.Selected_Style.apply_to_style_config()

    @staticmethod
    def reload_theme(theme: Style.StyleTheme):
        set_style = ImGui.get_style().Theme == theme
        
        ImGui.Styles[theme] = Style.load_theme(theme)        

        if set_style:
            ImGui.Selected_Style = ImGui.Styles[theme]

    @staticmethod
    def push_theme_window_style(theme: Style.StyleTheme = Style.StyleTheme.ImGui):
        if not theme in ImGui.Styles:
            ImGui.Styles[theme] = Style.load_theme(theme)

        if theme not in ImGui.Styles:
            ConsoleLog("Style", f"Style {theme.name} not found.")
            return
        
        ImGui.Styles[theme].push_style()

    @staticmethod
    def pop_theme_window_style(theme: Style.StyleTheme = Style.StyleTheme.ImGui):
        if theme not in ImGui.Styles:
            return

        ImGui.Styles[theme].pop_style()


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
                ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.small_button(label)
                ImGui.pop_style_color(5)

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
                ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.button(label, width, height)
                ImGui.pop_style_color(5)

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
                ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.button(label, width, height)
                ImGui.pop_style_color(5)

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
                ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.button(label, width, height)
                ImGui.pop_style_color(5)

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
                ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.button("##image_button " + label, width, height)
                ImGui.pop_style_color(5)

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
                        tint = ((style.ButtonTextureBackgroundActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.ButtonTextureBackgroundHovered.get_current().rgb_tuple) if ImGui.is_mouse_in_rect(button_rect) else style.ButtonTextureBackground.get_current().rgb_tuple) if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple


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
                
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))
                clicked = PyImGui.button("##image_button " + label, width, height)
                ImGui.pop_style_color(2)
                
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
                ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
                clicked = PyImGui.button("##image_toggle_button " + label, width, height)
                ImGui.pop_style_color(5)

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
                    
                
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))
                clicked = PyImGui.button("##image_toggle_button " + label, width, height)
                ImGui.pop_style_color(2)
                
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
                ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                ImGui.push_style_color(
                    PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                ImGui.push_style_color(
                    PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                ImGui.push_style_color(
                    PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                ImGui.push_style_color(
                    PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                ImGui.push_style_color(
                    PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))

                index = PyImGui.combo(label, current_item, items)
                display_label = label.split("##")[0]
                label_size = PyImGui.calc_text_size(display_label)

                ImGui.pop_style_color(6)

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
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.CheckMark, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0,0,0,0))
                new_value = PyImGui.checkbox(label, is_checked)
                ImGui.pop_style_color(5)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                
                padding = 4
                width = item_rect_max[0] - item_rect_min[0]
                height = item_rect_max[1] - item_rect_min[1] - (padding * 2)
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                checkbox_rect = (item_rect_min[0] + padding, item_rect_min[1] + (padding if style.Theme == Style.StyleTheme.Guild_Wars else 2), height, height)
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
                ThemeTextures.CircleButtons.value.draw_in_drawlist(
                    item_rect[0],
                    item_rect[1],
                    (item_rect[3], item_rect[3]),
                    state=TextureState.Active if v == button_index else TextureState.Normal,
                    tint= (255, 255, 255, 255) if active else (235, 235, 235, 255) if v == button_index else (180, 180, 180, 255)
                )
                if button_index == v:
                    pad = 5
                    
                    ThemeTextures.Quest_Objective_Bullet_Point.value.get_texture().draw_in_drawlist(
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
                    
                    ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))
                    
                    ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                    PyImGui.push_clip_rect(0, 0, 0, 0, False)
                    new_value = PyImGui.input_int(label + "##2", v, min_value, step_fast, flags)
                    PyImGui.pop_clip_rect()
                    ImGui.pop_style_color(1)
                    
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

                    # (ThemeTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.draw_in_drawlist(
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
                    ImGui.pop_style_color(6)

                    
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
                    ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                    PyImGui.push_clip_rect(0, 0, 0, 0, False)
                    new_value = PyImGui.input_int(label + "##2", v, min_value, step_fast, flags)
                    PyImGui.pop_clip_rect()
                    ImGui.pop_style_color(1)

                    item_rect_min = PyImGui.get_item_rect_min()
                    item_rect_max = PyImGui.get_item_rect_max()
                    height = item_rect_max[1] - item_rect_min[1]

                    display_label = label.split("##")[0]
                    label_size = PyImGui.calc_text_size(display_label)

                    label_rect = (item_rect_max[0] - (label_size[0] if label_size[0] > 0 else 0), item_rect_min[1] + ((height - label_size[1]) / 2) + 2, label_size[0], label_size[1])

                    width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + 6 if label_size[0] > 0 else 0)
                    item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                    
                    inputfield_size = ((label_rect[0] - current_inner_spacing.value1) - item_rect_min[0] , item_rect[3])
                    
                    # (ThemeTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.draw_in_drawlist(
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
                    ImGui.pop_style_color(6)

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
                ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_clip_rect(0, 0, 0, 0, False)
                new_value = PyImGui.input_text(label + "##2", v, flags)
                PyImGui.pop_clip_rect()
                ImGui.pop_style_color(1)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                height = item_rect_max[1] - item_rect_min[1]

                display_label = label.split("##")[0]
                label_size = PyImGui.calc_text_size(display_label)

                label_rect = (item_rect_max[0] - (label_size[0] if label_size[0] > 0 else 0), item_rect_min[1] + ((height - label_size[1]) / 2) + 2, label_size[0], label_size[1])

                width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + 6 if label_size[0] > 0 else 0)
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                
                inputfield_size = ((label_rect[0] - current_inner_spacing.value1) - item_rect_min[0] , item_rect[3])
                
                # (ThemeTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.draw_in_drawlist(
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
                ImGui.pop_style_color(6)

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
                ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_clip_rect(0, 0, 0, 0, False)
                new_value = PyImGui.input_float(label + "##2", v)
                PyImGui.pop_clip_rect()
                ImGui.pop_style_color(1)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                height = item_rect_max[1] - item_rect_min[1]

                display_label = label.split("##")[0]
                label_size = PyImGui.calc_text_size(display_label)

                label_rect = (item_rect_max[0] - (label_size[0] if label_size[0] > 0 else 0), item_rect_min[1] + ((height - label_size[1]) / 2) + 2, label_size[0], label_size[1])

                width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + 6 if label_size[0] > 0 else 0)
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                
                inputfield_size = ((label_rect[0] - current_inner_spacing.value1) - item_rect_min[0] , item_rect[3])
                
                # (ThemeTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.draw_in_drawlist(
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
                ImGui.pop_style_color(6)

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
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0,0,0,0))
                new_value = PyImGui.slider_int(label, v, v_min, v_max)

                ImGui.pop_style_color(6)

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
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0,0,0,0))
                new_value = PyImGui.slider_float(label, v, v_min, v_max)

                ImGui.pop_style_color(6)

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

                ThemeTextures.Separator.value.get_texture().draw_in_drawlist(
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
        ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0,))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0,))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0,))
        clicked = PyImGui.button(text)
        ImGui.pop_style_color(3)
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
                ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0, 0, 0, 0))
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.push_clip_rect(0, 0, 0, 0, False)
                new_value = PyImGui.input_text(label + "##2", text, flags)
                PyImGui.pop_clip_rect()
                ImGui.pop_style_color(1)

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()
                height = item_rect_max[1] - item_rect_min[1]

                display_label = label.split("##")[0]
                label_size = PyImGui.calc_text_size(display_label)

                label_rect = (item_rect_max[0] - (label_size[0] if label_size[0] > 0 else 0), item_rect_min[1] + ((height - label_size[1]) / 2) + 2, label_size[0], label_size[1])

                width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + 6 if label_size[0] > 0 else 0)
                item_rect = (item_rect_min[0], item_rect_min[1], width, height)
                
                inputfield_size = ((label_rect[0] - current_inner_spacing.value1) - item_rect_min[0] , item_rect[3])

                # (ThemeTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.draw_in_drawlist(
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
                ImGui.pop_style_color(6)

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
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                height = PyImGui.get_text_line_height()
                text_size = PyImGui.calc_text_size(text)
                cursor = PyImGui.get_cursor_screen_pos()

                PyImGui.push_clip_rect(cursor[0] + frame_padding.value1 + height, cursor[1], cursor[0] + frame_padding.value1 + text_size[0], text_size[1], True)
                PyImGui.bullet_text(text)
                PyImGui.pop_clip_rect()

                item_rect_min = PyImGui.get_item_rect_min()
                
                item_rect = (item_rect_min[0] + frame_padding.value1, item_rect_min[1] -2, height, height)
                ThemeTextures.BulletPoint.value.get_texture().draw_in_drawlist(
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
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
                text_size = PyImGui.calc_text_size(text)
                cursor = PyImGui.get_cursor_screen_pos()

                PyImGui.push_clip_rect(cursor[0] + frame_padding.value1 + height, cursor[1], cursor[0] + frame_padding.value1 + text_size[0], text_size[1], True)
                PyImGui.bullet_text(text)
                PyImGui.pop_clip_rect()

                item_rect_min = PyImGui.get_item_rect_min()
                item_rect_max = PyImGui.get_item_rect_max()

                item_rect = (item_rect_min[0] + frame_padding.value1, item_rect_min[1] -2, height, height)
                
                ThemeTextures.Quest_Objective_Bullet_Point.value.get_texture().draw_in_drawlist(
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
                ImGui.push_style_color(PyImGui.ImGuiCol.Header, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, (0,0,0,0))
                
                PyImGui.push_clip_rect(PyImGui.get_cursor_screen_pos()[0]+ 20, PyImGui.get_cursor_screen_pos()[1], 1000, 1000, True)
                new_open = PyImGui.collapsing_header(label, flags)
                PyImGui.pop_clip_rect()
                
                ImGui.pop_style_color(3)
                
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
                ImGui.push_style_color(PyImGui.ImGuiCol.Header, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, (0,0,0,0))
                ImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, (0,0,0,0))
                PyImGui.push_clip_rect(PyImGui.get_cursor_screen_pos()[0]+ 20, PyImGui.get_cursor_screen_pos()[1], 1000, 1000, True)
                new_open = PyImGui.tree_node(label)
                PyImGui.pop_clip_rect()

                ImGui.pop_style_color(3)
                
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
                    item_rect[0] - (3 if style.Theme == Style.StyleTheme.Guild_Wars else 3),
                    item_rect[1],
                    (item_rect[2] + (6 if style.Theme == Style.StyleTheme.Guild_Wars else 6),
                    4),
                )
                
                ThemeTextures.Tab_Frame_Body.value.get_texture().draw_in_drawlist(
                    item_rect[0] - (3 if style.Theme == Style.StyleTheme.Guild_Wars else 3),
                    item_rect[1] + 4,
                    (item_rect[2] + (6 if style.Theme == Style.StyleTheme.Guild_Wars else 6),
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
                    ImGui.push_style_color(PyImGui.ImGuiCol.Tab, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.TabActive, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.TabHovered, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                    open = PyImGui.begin_tab_item(label)
                    ImGui.pop_style_color(4)

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
                    ImGui.push_style_color(PyImGui.ImGuiCol.Tab, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.TabActive, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.TabHovered, (0, 0, 0, 0))
                    ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                    
                    open = PyImGui.begin_tab_item(label, popen, flags)

                    ImGui.pop_style_color(4)

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
                
            ThemeTextures.Scroll_Bg.value.draw_in_drawlist(
                scroll_bar_rect[0],
                scroll_bar_rect[1] + 5,
                (scroll_bar_rect[2] - scroll_bar_rect[0], scroll_bar_rect[3] - scroll_bar_rect[1] - 10),
            )

            ThemeTextures.ScrollGrab_Top.value.draw_in_drawlist(
                scroll_grab_rect[0], 
                scroll_grab_rect[1], 
                (scroll_bar_size, 7),
            )
            
            ThemeTextures.ScrollGrab_Bottom.value.draw_in_drawlist(
                scroll_grab_rect[0], 
                scroll_grab_rect[3] - 7, 
                (scroll_bar_size, 7),
            )

            px_height = 2
            mid_height = scroll_grab_rect[3] - scroll_grab_rect[1] - 10
            for i in range(math.ceil(mid_height / px_height)):
                ThemeTextures.ScrollGrab_Middle.value.draw_in_drawlist(
                    scroll_grab_rect[0], 
                    scroll_grab_rect[1] + 5 + (px_height * i), 
                    (scroll_bar_size, px_height),
                tint=(195, 195, 195, 255)
                )
            
            ThemeTextures.UpButton.value.draw_in_drawlist(
                scroll_bar_rect[0] - 1,
                scroll_bar_rect[1] - 5,
                (scroll_bar_size, scroll_bar_size),
            )

            ThemeTextures.DownButton.value.draw_in_drawlist(
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
            
                
            ThemeTextures.Horizontal_Scroll_Bg.value.draw_in_drawlist(
                scroll_bar_rect[0] + 3,
                scroll_bar_rect[1],
                (scroll_bar_rect[2] - scroll_bar_rect[0] - 5, scroll_bar_rect[3] - scroll_bar_rect[1]),
            )
                    
            ThemeTextures.Horizontal_ScrollGrab_Middle.value.draw_in_drawlist(
                scroll_grab_rect[0] + 5, 
                scroll_grab_rect[1],
                (scroll_grab_rect[2] - 10, scroll_grab_rect[3]),
                tint=(195, 195, 195, 255)
            )
            
            ThemeTextures.Horizontal_ScrollGrab_Top.value.draw_in_drawlist(
                scroll_grab_rect[0], 
                scroll_grab_rect[1], 
                (7, scroll_grab_rect[3]),
            )
            
            ThemeTextures.Horizontal_ScrollGrab_Bottom.value.draw_in_drawlist(
                scroll_grab_rect[0] + scroll_grab_rect[2] - 7, 
                scroll_grab_rect[1], 
                (7, scroll_grab_rect[3]),
            )

            
            ThemeTextures.LeftButton.value.draw_in_drawlist(
                scroll_bar_rect[0] - 5, 
                scroll_bar_rect[1] - 1, 
                (scroll_bar_size, scroll_bar_size + 1),
            )
            
            ThemeTextures.RightButton.value.draw_in_drawlist(
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
            case Style.StyleTheme.Guild_Wars | Style.StyleTheme.Minimalus:
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
                
                ThemeTextures.ProgressBarBackground.value.get_texture().draw_in_drawlist(
                    background_rect[0],
                    background_rect[1],
                    (background_rect[2], background_rect[3]),
                    tint=tint
                )
                
                ThemeTextures.ProgressBarProgress.value.get_texture().draw_in_drawlist(
                    progress_rect[0],
                    progress_rect[1],
                    (progress_rect[2], progress_rect[3]),
                    tint=tint
                )
                
                if fraction > 0:
                    ThemeTextures.ProgressBarProgressCursor.value.get_texture().draw_in_drawlist(
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
                ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
                PyImGui.progress_bar(fraction, size_arg_x, size_arg_y, overlay)
                ImGui.pop_style_color(1)

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
    
    class gw_window():
        _state = {}
        
        TEXTURE_FOLDER = "Textures\\Game UI\\"
        FRAME_ATLAS = "ui_window_frame_atlas.png"
        FRAME_ATLAS_DIMENSIONS = (128,128)
        TITLE_ATLAS = "ui_window_title_frame_atlas.png"
        TITLE_ATLAS_DIMENSIONS = (128, 32)
        CLOSE_BUTTON_ATLAS = "close_button.png"
        
        LOWER_BORDER_PIXEL_MAP = (11,110,78,128)
        LOWER_RIGHT_CORNER_TAB_PIXEL_MAP = (78,110,117,128)

        # Pixel maps for title bar
        LEFT_TITLE_PIXEL_MAP = (0,0,18,32)
        RIGHT_TITLE_PIXEL_MAP = (110,0,128,32)
        TITLE_AREA_PIXEL_MAP = (19,0,109,32)

        # Pixel maps for LEFT side
        UPPER_LEFT_TAB_PIXEL_MAP = (0,0,17,35)
        LEFT_BORDER_PIXEL_MAP = (0,36,17,74)
        LOWER_LEFT_TAB_PIXEL_MAP = (0,75,11,110)
        LOWER_LEFT_CORNER_PIXEL_MAP = (0,110,11,128)

        # Pixel maps for RIGHT side
        UPPER_RIGHT_TAB_PIXEL_MAP = (113,0,128,35)
        RIGHT_BORDER_PIXEL_MAP = (111,36,128,74)
        LOWER_RIGHT_TAB_PIXEL_MAP = (117,75,128,110)
        LOWER_RIGHT_CORNER_PIXEL_MAP = (117,110,128,128)

        CLOSE_BUTTON_PIXEL_MAP = (0, 0, 15,15)
        CLOSE_BUTTON_HOVERED_PIXEL_MAP = (16, 0, 31, 15)
        
        @staticmethod
        def draw_region_in_drawlist(x: float, y: float,
                            width: int, height: int,
                            pixel_map: tuple[int, int, int, int],
                            texture_path: str,
                            atlas_dimensions: tuple[int, int],
                            tint: tuple[int, int, int, int] = (255, 255, 255, 255)):
            """
            Draws a region defined by pixel_map into the current window's draw list at (x, y).
            """
            x0, y0, x1, y1 = pixel_map
            _width = x1 - x0 if width == 0 else width
            _height = y1 - y0 if height == 0 else height
            
            source_width = x1 - x0
            source_height = y1 - y0

            uv0, uv1 = Utils.PixelsToUV(x0, y0, source_width, source_height, atlas_dimensions[0], atlas_dimensions[1])

            ImGui.DrawTextureInDrawList(
                pos=(x, y),
                size=(_width, _height),
                texture_path=texture_path,
                uv0=uv0,
                uv1=uv1,
                tint=tint
            )
         
        @staticmethod
        def begin(name: str,
            pos: tuple[float, float] = (0.0, 0.0),
            size: tuple[float, float] = (0.0, 0.0),
            collapsed: bool = False,
            pos_cond: int = PyImGui.ImGuiCond.FirstUseEver, 
            size_cond: int = PyImGui.ImGuiCond.FirstUseEver) -> bool:
            if name not in ImGui.gw_window._state:
                ImGui.gw_window._state[name] = {
                    "collapsed": collapsed
                }
            
            state = ImGui.gw_window._state[name]

            if size != (0.0, 0.0):
                PyImGui.set_next_window_size(size, size_cond)
            if pos != (0.0, 0.0):
                PyImGui.set_next_window_pos(pos, pos_cond)
                
            PyImGui.set_next_window_collapsed(state["collapsed"], pos_cond)

            if state["collapsed"]:
                internal_flags  = (PyImGui.WindowFlags.NoFlag)
            else:
                internal_flags =  PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoBackground
                
        
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0, 0)
            
            opened = PyImGui.begin(name, internal_flags)
            state["collapsed"] = PyImGui.is_window_collapsed()
            state["_active"] = opened
            
            if not opened:
                PyImGui.end()
                PyImGui.pop_style_var(1)
                return False
            
            # Window position and size
            window_pos = PyImGui.get_window_pos()
            window_size = PyImGui.get_window_size()
                
            window_left, window_top = window_pos
            window_width, window_height = window_size
            window_right = window_left + window_width
            window_bottom = window_top + window_height
            
            #TITLE AREA
            #LEFT TITLE
            x0, y0, x1, y1 = ImGui.gw_window.LEFT_TITLE_PIXEL_MAP
            LT_width = x1 - x0
            LT_height = y1 - y0
            ImGui.gw_window.draw_region_in_drawlist(
                x=window_left,
                y=window_top-5,
                width=LT_width,
                height=LT_height,
                pixel_map=ImGui.gw_window.LEFT_TITLE_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.TITLE_ATLAS,
                atlas_dimensions=ImGui.gw_window.TITLE_ATLAS_DIMENSIONS,
                tint=(255, 255, 255, 255)
            )
            
            # RIGHT TITLE
            x0, y0, x1, y1 = ImGui.gw_window.RIGHT_TITLE_PIXEL_MAP
            rt_width = x1 - x0
            rt_height = y1 - y0
            ImGui.gw_window.draw_region_in_drawlist(
                x=window_right - rt_width,
                y=window_top - 5,
                width=rt_width,
                height=rt_height,
                pixel_map=ImGui.gw_window.RIGHT_TITLE_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.TITLE_ATLAS,
                atlas_dimensions=ImGui.gw_window.TITLE_ATLAS_DIMENSIONS
            )
            
            # CLOSE BUTTON
            x0, y0, x1, y1 = ImGui.gw_window.CLOSE_BUTTON_PIXEL_MAP
            cb_width = x1 - x0
            cb_height = y1 - y0

            x = window_right - cb_width - 13
            y = window_top + 8

            # Position the interactive region
            PyImGui.draw_list_add_rect(
                x,                    # x1
                y,                    # y1
                x + cb_width,         # x2
                y + cb_height,        # y2
                Color(255, 0, 0, 255).to_color(),  # col in ABGR
                0.0,                  # rounding
                0,                    # rounding_corners_flags
                1.0                   # thickness
            )

            PyImGui.set_cursor_screen_pos(x-1, y-1)
            if PyImGui.invisible_button("##close_button", cb_width+2, cb_height+2):
                state["collapsed"] = not state["collapsed"]
                PyImGui.set_window_collapsed(state["collapsed"], PyImGui.ImGuiCond.Always)

            # Determine UV range based on state
            if PyImGui.is_item_active():
                uv0 = (0.666, 0.0)  # Pushed
                uv1 = (1.0, 1.0)
            elif PyImGui.is_item_hovered():
                uv0 = (0.333, 0.0)  # Hovered
                uv1 = (0.666, 1.0)
            else:
                uv0 = (0.0, 0.0)     # Normal
                uv1 = (0.333, 1.0)

            #Draw close button is done after the title bar
            #TITLE BAR
            x0, y0, x1, y1 = ImGui.gw_window.TITLE_AREA_PIXEL_MAP
            title_width = int(window_width - 36)
            title_height = y1 - y0
            ImGui.gw_window.draw_region_in_drawlist(
                x=window_left + 18,
                y=window_top - 5,
                width=title_width,
                height=title_height,
                pixel_map=ImGui.gw_window.TITLE_AREA_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.TITLE_ATLAS,
                atlas_dimensions=ImGui.gw_window.TITLE_ATLAS_DIMENSIONS,
                tint=(255, 255, 255, 255)
            )
            
            # FLOATING BUTTON: Title bar behavior (drag + double-click collapse)
            titlebar_x = window_left + 18
            titlebar_y = window_top - 5
            titlebar_width = window_width - 36
            titlebar_height = title_height

            PyImGui.set_cursor_screen_pos(titlebar_x, titlebar_y)
            PyImGui.invisible_button("##titlebar_fake", titlebar_width, 32)

            # Handle dragging
            if PyImGui.is_item_active():
                delta = PyImGui.get_mouse_drag_delta(0, 0.0)
                new_window_pos = (window_left + delta[0], window_top + delta[1])
                PyImGui.reset_mouse_drag_delta(0)
                PyImGui.set_window_pos(new_window_pos[0], new_window_pos[1], PyImGui.ImGuiCond.Always)

            # Handle double-click to collapse
            if PyImGui.is_item_hovered() and PyImGui.is_mouse_double_clicked(0):
                state["collapsed"] = not state["collapsed"]
                PyImGui.set_window_collapsed(state["collapsed"], PyImGui.ImGuiCond.Always)
                
            # Draw CLOSE BUTTON in the title bar
            ImGui.DrawTextureInDrawList(
                pos=(x, y),
                size=(cb_width, cb_height),
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.CLOSE_BUTTON_ATLAS,
                uv0=uv0,
                uv1=uv1,
                tint=(255, 255, 255, 255)
            )
            
            # Draw title text
            text_x = window_left + 32
            text_y = window_top + 10
            
            PyImGui.draw_list_add_text(
                text_x,
                text_y,
                Color(225, 225, 225, 225).to_color(),  # White text (ABGR)
                name
            )
            
            # Draw the frame around the window
            # LEFT SIDE
            #LEFT UPPER TAB
            x0, y0, x1, y1 = ImGui.gw_window.UPPER_LEFT_TAB_PIXEL_MAP
            lut_tab_width = x1 - x0
            lut_tab_height = y1 - y0
            ImGui.gw_window.draw_region_in_drawlist(
                x=window_left,
                y=window_top + LT_height - 5,
                width= lut_tab_width,
                height= lut_tab_height,
                pixel_map=ImGui.gw_window.UPPER_LEFT_TAB_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.FRAME_ATLAS,
                atlas_dimensions=ImGui.gw_window.FRAME_ATLAS_DIMENSIONS,
                tint=(255, 255, 255, 255)
            )
            
            #LEFT CORNER
            x0, y0, x1, y1 = ImGui.gw_window.LOWER_LEFT_CORNER_PIXEL_MAP
            lc_width = x1 - x0
            lc_height = y1 - y0
            ImGui.gw_window.draw_region_in_drawlist(
                x=window_left,
                y=window_bottom - lc_height,
                width= lc_width,
                height= lc_height,
                pixel_map=ImGui.gw_window.LOWER_LEFT_CORNER_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.FRAME_ATLAS,
                atlas_dimensions=ImGui.gw_window.FRAME_ATLAS_DIMENSIONS,
                tint=(255, 255, 255, 255)
            )
            
            
            #LEFT LOWER TAB
            x0, y0, x1, y1 = ImGui.gw_window.LOWER_LEFT_TAB_PIXEL_MAP
            ll_tab_width = x1 - x0
            ll_tab_height = y1 - y0
            ImGui.gw_window.draw_region_in_drawlist(
                x=window_left,
                y=window_bottom - lc_height -ll_tab_height,
                width=ll_tab_width,
                height=ll_tab_height,
                pixel_map=ImGui.gw_window.LOWER_LEFT_TAB_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.FRAME_ATLAS,
                atlas_dimensions=ImGui.gw_window.FRAME_ATLAS_DIMENSIONS,
                tint=(255, 255, 255, 255)
            )
            
            #LEFT BORDER
            x0, y0, x1, y1 = ImGui.gw_window.LEFT_BORDER_PIXEL_MAP
            left_border_width = x1 - x0
            left_border_height = y1 - y0
            ImGui.gw_window.draw_region_in_drawlist(
                x=window_left,
                y=window_top + LT_height - 5 + lut_tab_height,
                width= left_border_width,
                height= int(window_height - (LT_height + lut_tab_height + ll_tab_height + lc_height) +5),
                pixel_map=ImGui.gw_window.LEFT_BORDER_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.FRAME_ATLAS,
                atlas_dimensions=ImGui.gw_window.FRAME_ATLAS_DIMENSIONS,
                tint=(255, 255, 255, 255)
            )
        
            # RIGHT SIDE
            # UPPER RIGHT TAB
            x0, y0, x1, y1 = ImGui.gw_window.UPPER_RIGHT_TAB_PIXEL_MAP
            urt_width = x1 - x0
            urt_height = y1 - y0
            ImGui.gw_window.draw_region_in_drawlist(
                x=window_right - urt_width,
                y=window_top + rt_height - 5,
                width=urt_width,
                height=urt_height,
                pixel_map=ImGui.gw_window.UPPER_RIGHT_TAB_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.FRAME_ATLAS,
                atlas_dimensions=ImGui.gw_window.FRAME_ATLAS_DIMENSIONS
            )

            # LOWER RIGHT CORNER
            x0, y0, x1, y1 = ImGui.gw_window.LOWER_RIGHT_CORNER_PIXEL_MAP
            rc_width = x1 - x0
            rc_height = y1 - y0
            corner_x = window_right - rc_width
            corner_y = window_bottom - rc_height
            ImGui.gw_window.draw_region_in_drawlist(
                x=window_right - rc_width,
                y=window_bottom - rc_height,
                width=rc_width,
                height=rc_height,
                pixel_map=ImGui.gw_window.LOWER_RIGHT_CORNER_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.FRAME_ATLAS,
                atlas_dimensions=ImGui.gw_window.FRAME_ATLAS_DIMENSIONS
            )
            # DRAG: Resize from corner
            PyImGui.set_cursor_screen_pos(corner_x-10, corner_y-10)
            PyImGui.invisible_button("##resize_corner", rc_width+10, rc_height+10)
            if PyImGui.is_item_active():
                delta = PyImGui.get_mouse_drag_delta(0, 0.0)
                new_window_size = (window_size[0] + delta[0], window_size[1] + delta[1])
                PyImGui.reset_mouse_drag_delta(0)
                PyImGui.set_window_size(new_window_size[0], new_window_size[1], PyImGui.ImGuiCond.Always)

            # LOWER RIGHT TAB
            x0, y0, x1, y1 = ImGui.gw_window.LOWER_RIGHT_TAB_PIXEL_MAP
            lrt_width = x1 - x0
            lrt_height = y1 - y0
            tab_x = window_right - lrt_width
            tab_y = window_bottom - rc_height - lrt_height
            ImGui.gw_window.draw_region_in_drawlist(
                x=window_right - lrt_width,
                y=window_bottom - rc_height - lrt_height,
                width=lrt_width,
                height=lrt_height,
                pixel_map=ImGui.gw_window.LOWER_RIGHT_TAB_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.FRAME_ATLAS,
                atlas_dimensions=ImGui.gw_window.FRAME_ATLAS_DIMENSIONS
            )
            PyImGui.set_cursor_screen_pos(tab_x-10, tab_y)
            PyImGui.invisible_button("##resize_tab_above", lrt_width+10, lrt_height)
            if PyImGui.is_item_active():
                delta = PyImGui.get_mouse_drag_delta(0, 0.0)
                new_window_size = (window_size[0] + delta[0], window_size[1] + delta[1])
                PyImGui.reset_mouse_drag_delta(0)
                PyImGui.set_window_size(new_window_size[0], new_window_size[1], PyImGui.ImGuiCond.Always)

            # RIGHT BORDER
            x0, y0, x1, y1 = ImGui.gw_window.RIGHT_BORDER_PIXEL_MAP
            right_border_width = x1 - x0
            right_border_height = y1 - y0
            ImGui.gw_window.draw_region_in_drawlist(
                x=window_right - right_border_width,
                y=window_top + rt_height - 5 + urt_height,
                width=right_border_width,
                height=int(window_height - (rt_height + urt_height + lrt_height + rc_height) + 5),
                pixel_map=ImGui.gw_window.RIGHT_BORDER_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.FRAME_ATLAS,
                atlas_dimensions=ImGui.gw_window.FRAME_ATLAS_DIMENSIONS
            )

            #BOTTOM BORDER
            # Tab to the left of LOWER_RIGHT_CORNER
            x0, y0, x1, y1 = ImGui.gw_window.LOWER_RIGHT_CORNER_TAB_PIXEL_MAP
            tab_width = x1 - x0
            tab_height = y1 - y0
            
            tab_x = window_right - rc_width - tab_width
            tab_y = window_bottom - rc_height

            ImGui.gw_window.draw_region_in_drawlist(
                x=window_right - rc_width - tab_width,       # left of the corner
                y=window_bottom - rc_height,                 # same vertical alignment as corner
                width=tab_width,
                height=tab_height,
                pixel_map=ImGui.gw_window.LOWER_RIGHT_CORNER_TAB_PIXEL_MAP,
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.FRAME_ATLAS,
                atlas_dimensions=ImGui.gw_window.FRAME_ATLAS_DIMENSIONS
            )
            
            # DRAG: Resize from left tab
            PyImGui.set_cursor_screen_pos(tab_x, tab_y-10)
            PyImGui.invisible_button("##resize_tab_left", tab_width, tab_height+10)
            PyImGui.set_item_allow_overlap()
            if PyImGui.is_item_active():
                delta = PyImGui.get_mouse_drag_delta(0,0.0)
                new_window_size = (window_size[0] + delta[0], window_size[1] + delta[1])
                PyImGui.reset_mouse_drag_delta(0)
                PyImGui.set_window_size(new_window_size[0], new_window_size[1], PyImGui.ImGuiCond.Always)
            
            x0, y0, x1, y1 = ImGui.gw_window.LOWER_BORDER_PIXEL_MAP
            border_tex_width = x1 - x0
            border_tex_height = y1 - y0
            border_start_x = window_left + lc_width
            border_end_x = window_right - rc_width - tab_width  # ← use the actual width of LOWER_RIGHT_CORNER_TAB
            border_draw_width = border_end_x - border_start_x

            uv0, uv1 = Utils.PixelsToUV(x0, y0, border_tex_width, border_tex_height,
                                        ImGui.gw_window.FRAME_ATLAS_DIMENSIONS[0], ImGui.gw_window.FRAME_ATLAS_DIMENSIONS[1])

            ImGui.DrawTextureInDrawList(
                pos=(border_start_x, window_bottom - border_tex_height),
                size=(border_draw_width, border_tex_height),
                texture_path=ImGui.gw_window.TEXTURE_FOLDER + ImGui.gw_window.FRAME_ATLAS,
                uv0=uv0,
                uv1=uv1,
                tint=(255, 255, 255, 255)
            )
        
            content_margin_top = title_height  # e.g. 32
            content_margin_left = lc_width     # left corner/border
            content_margin_right = rc_width    # right corner/border
            content_margin_bottom = border_tex_height  # bottom border height
            
            content_x = window_left + content_margin_left -1
            content_y = window_top + content_margin_top -5
            content_width = window_width - content_margin_left - content_margin_right +2
            content_height = window_height - content_margin_top - content_margin_bottom +10

            PyImGui.set_cursor_screen_pos(content_x, content_y)

            color = Color(0, 0, 0, 200)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, color.to_tuple_normalized())
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.ChildRounding, 6.0)

            # Create a child window for the content area
            padding = 8.0
            PyImGui.begin_child("ContentArea",(content_width, content_height), False, PyImGui.WindowFlags.NoFlag)

            PyImGui.set_cursor_pos(padding, padding)  # Manually push content in from top-left
            PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, (0, 0, 0, 0)) 
            
            inner_width = content_width - (padding * 2)
            inner_height = content_height - (padding * 2)

            PyImGui.begin_child("InnerLayout",(inner_width, inner_height), False, PyImGui.WindowFlags.NoFlag)
        
            return True
        
        @staticmethod
        def end(name: str):
            state = ImGui.gw_window._state.get(name)
            if not state or not state.get("_active", False):
                return  # this window was not successfully begun, do not call end stack

            PyImGui.end_child()  # InnerLayout
            PyImGui.pop_style_color(1)
            PyImGui.end_child()  # ContentArea
            PyImGui.pop_style_var(1)
            PyImGui.pop_style_color(1)
            PyImGui.end()
            PyImGui.pop_style_var(1)
            
            state["_active"] = False


py4_gw_ini_handler = IniHandler("Py4GW.ini")
ImGui.set_theme(Style.StyleTheme[py4_gw_ini_handler.read_key("settings", "style_theme", Style.StyleTheme.ImGui.name)])
