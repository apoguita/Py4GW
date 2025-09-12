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


class SortDirection(Enum):
    No_Sort = 0
    Ascending = 1
    Descending = 2

#region ImGui
class ImGui:
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
    def toggle_button(label: str, v: bool, width=0, height =0) -> bool:
        """
        Purpose: Create a toggle button that changes its state and color based on the current state.
        Args:
            label (str): The label of the button.
            v (bool): The current toggle state (True for on, False for off).
        Returns: bool: The new state of the button after being clicked.
        """
        clicked = False

        if v:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.153, 0.318, 0.929, 1.0))  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.6, 0.6, 0.9, 1.0))  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.6, 0.6, 0.6, 1.0))
            if width != 0 and height != 0:
                clicked = PyImGui.button(label, width, height)
            else:
                clicked = PyImGui.button(label)
            PyImGui.pop_style_color(3)
        else:
            if width != 0 and height != 0:
                clicked = PyImGui.button(label, width, height)
            else:
                clicked = PyImGui.button(label)

        if clicked:
            v = not v

        return v
    
    
    
    @staticmethod
    def image_toggle_button(label: str, texture_path: str, v: bool, width=0, height=0) -> bool:
        """
        Purpose: Create a toggle button that displays an image and changes its state when clicked.
        Args:
            label (str): The label of the button.
            texture_path (str): The path to the image texture.
            v (bool): The current toggle state (True for on, False for off).
        Returns: bool: The new state of the button after being clicked.
        """
        clicked = False

        if v:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, Color(156, 156, 230, 255).to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Color(156, 156, 230, 255).to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, Color(156, 156, 156, 255).to_tuple_normalized())
            if width != 0 and height != 0:
                clicked = ImGui.ImageButton(label, texture_path, width, height)      
            else:
                clicked = ImGui.ImageButton(label, texture_path)
            PyImGui.pop_style_color(3)
        else:
            if width != 0 and height != 0:
                clicked = ImGui.ImageButton(label, texture_path, width, height)
            else:
                clicked = ImGui.ImageButton(label, texture_path) 
        if clicked:
            v = not v
        return v

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
        def __init__(self, module_name="", window_name="", window_size=(100,100), window_pos=(0,0), window_flags=PyImGui.WindowFlags.NoFlag, collapse= False):
            self.module_name = module_name
            if not self.module_name:
                return
            self.window_name = window_name if window_name else module_name
            self.window_size = window_size
            self.collapse = collapse
            if window_pos == (0,0):
                overlay = Overlay()
                screen_width, screen_height = overlay.GetDisplaySize().x, overlay.GetDisplaySize().y
                #set position to the middle of the screen
                self.window_pos = (screen_width / 2 - window_size[0] / 2, screen_height / 2 - window_size[1] / 2)
            else:
                self.window_pos = window_pos
            self.window_flags = window_flags
            self.first_run = True

            #debug variables
            self.collapsed_status = True
            self.tracking_position = self.window_pos

        def initialize(self):
            if not self.module_name:
                return
            if self.first_run:
                PyImGui.set_next_window_size(self.window_size[0], self.window_size[1])     
                PyImGui.set_next_window_pos(self.window_pos[0], self.window_pos[1])
                PyImGui.set_next_window_collapsed(self.collapse, 0)
                self.first_run = False

        def begin(self):
            if not self.module_name:
                return
            self.collapsed_status = True
            self.tracking_position = self.window_pos
            return PyImGui.begin(self.window_name, self.window_flags)

        def process_window(self):
            if not self.module_name:
                return
            self.collapsed_status = PyImGui.is_window_collapsed()
            self.end_pos = PyImGui.get_window_pos()

        def end(self):
            if not self.module_name:
                return
            PyImGui.end()
            """ INI FILE ROUTINES NEED WORK 
            if end_pos[0] != window_module.window_pos[0] or end_pos[1] != window_module.window_pos[1]:
                ini_handler.write_key(module_name + " Config", "config_x", str(int(end_pos[0])))
                ini_handler.write_key(module_name + " Config", "config_y", str(int(end_pos[1])))

            if new_collapsed != window_module.collapse:
                ini_handler.write_key(module_name + " Config", "collapsed", str(new_collapsed))
            """
       
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
        
    #region Styles, Themes and Themed controls

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


        
    #reguion gw_window
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