import PyImGui
import json
import os
from enum import IntEnum
from.types import ImGuiStyleVar, StyleColorType, StyleTheme
from ..Py4GWcorelib import Utils, Color

class Style:    
    pyimgui_style = PyImGui.StyleConfig()

    class StyleVar:
        def __init__(self, style: "Style", value1: float, value2: float | None = None, img_style_enum: "ImGuiStyleVar|None" = None, display_name: str | None = None):
            self.style = style
            self.img_style_enum: ImGuiStyleVar | None = img_style_enum
            self.display_name: str | None = display_name if display_name else Utils.split_uppercase(img_style_enum.name) if img_style_enum else None
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
            return {"value1": self.value1, "value2": self.value2} if self.value2 is not None else {"value1": self.value1}

        def load_from_json(self, data):            
            self.value1 = data.get("value1", 0)
            self.value2 = data.get("value2", None)

        def get_current(self):
            return self.pushed_stack[0] if self.pushed_stack else self

        def copy(self):
            return Style.StyleVar(self.style, self.value1, self.value2, self.img_style_enum)

        def __hash__(self): return hash((self.img_style_enum, self.value1, self.value2))
        def __eq__(self, value): return isinstance(value, Style.StyleVar) and (self.img_style_enum, self.value1, self.value2) == (value.img_style_enum, value.value1, value.value2)
        def __ne__(self, value): return not self.__eq__(value)        

    class StyleColor(Color):
        def __init__(self, style: "Style", r: int, g: int, b: int, a: int = 255, img_color_enum: PyImGui.ImGuiCol | None = None, color_type: StyleColorType = StyleColorType.Default, display_name: str | None = None):
            super().__init__(r, g, b, a)
            self.style = style
            self.img_color_enum = img_color_enum
            self.color_type = color_type
            self.display_name = display_name if display_name else Utils.split_uppercase(img_color_enum.name) if img_color_enum else None
            self.pushed_stack: list[Style.StyleColor] = []

        def __hash__(self): return hash((self.img_color_enum, self))
        def __eq__(self, other): return isinstance(other, Style.StyleColor) and self == other
        def __ne__(self, other): return not self.__eq__(other)

        def set_tuple_color(self, color: tuple[float, float, float, float]):
            c = Color.from_tuple(color)
            self.r, self.g, self.b, self.a = c.r, c.g, c.b, c.a 

        def push_color(self, rgba: tuple[int, int, int, int] | None = None):
            col = Style.StyleColor(self.style, *rgba, self.img_color_enum) if rgba else self.get_current()
            if col.img_color_enum is not None:
                PyImGui.push_style_color(col.img_color_enum, col.color_tuple)
            self.pushed_stack.insert(0, col)

        def pop_color(self):
            col = self.get_current()
            
            if self.pushed_stack:
                self.pushed_stack.pop(0)
                
            if col.img_color_enum:
                PyImGui.pop_style_color(1)

        def get_current(self): return self.pushed_stack[0] if self.pushed_stack else self

        def to_json(self):
            return {"img_color_enum": self.img_color_enum.name if self.img_color_enum else None, **dict(zip("rgba", self.to_tuple()))}

        def load_from_json(self, data):
            col = Color.from_json(data)
            self.r, self.g, self.b, self.a = col.r, col.g, col.b, col.a
            img_color_enum = data.get("img_color_enum", None)            
            self.img_color_enum = getattr(PyImGui.ImGuiCol, img_color_enum) if img_color_enum in PyImGui.ImGuiCol.__members__ else None

    def __init__(self, theme: StyleTheme = StyleTheme.ImGui):
        # Set the default style as base so we can push it and cover all
        self.Theme : StyleTheme = theme

        #region Style Vars
        self.Alpha : Style.StyleVar = Style.StyleVar(self, 1.0, None, ImGuiStyleVar.Alpha)
        self.DisabledAlpha : Style.StyleVar = Style.StyleVar(self, 0.6, None, ImGuiStyleVar.DisabledAlpha)
        
        self.WindowPadding : Style.StyleVar = Style.StyleVar(self, 10, 10, ImGuiStyleVar.WindowPadding)
        self.FramePadding : Style.StyleVar = Style.StyleVar(self, 5, 5, ImGuiStyleVar.FramePadding)
        self.CellPadding : Style.StyleVar = Style.StyleVar(self, 4, 2, ImGuiStyleVar.CellPadding)
        self.ItemSpacing : Style.StyleVar = Style.StyleVar(self, 10, 6, ImGuiStyleVar.ItemSpacing)
        self.ItemInnerSpacing : Style.StyleVar = Style.StyleVar(self, 6, 4, ImGuiStyleVar.ItemInnerSpacing)
        # self.TouchExtraPadding : Style.StyleVar = Style.StyleVar(self, 0, 0, ImGuiStyleVar.TouchExtraPadding)
        self.IndentSpacing : Style.StyleVar = Style.StyleVar(self, 20, None, ImGuiStyleVar.IndentSpacing)
        self.ScrollbarSize : Style.StyleVar = Style.StyleVar(self, 20, None, ImGuiStyleVar.ScrollbarSize)
        self.GrabMinSize : Style.StyleVar = Style.StyleVar(self, 5, None, ImGuiStyleVar.GrabMinSize)
                
        self.WindowBorderSize : Style.StyleVar = Style.StyleVar(self, 1, None, ImGuiStyleVar.WindowBorderSize)
        self.ChildBorderSize : Style.StyleVar = Style.StyleVar(self, 1, None, ImGuiStyleVar.ChildBorderSize)
        self.PopupBorderSize : Style.StyleVar = Style.StyleVar(self, 1, None, ImGuiStyleVar.PopupBorderSize)
        self.FrameBorderSize : Style.StyleVar = Style.StyleVar(self, 0, None, ImGuiStyleVar.FrameBorderSize)
        # self.TabBorderSize : Style.StyleVar = Style.StyleVar(self, 0, None, ImGuiStyleVar.TabBorderSize)
        
        self.WindowRounding : Style.StyleVar = Style.StyleVar(self, 5, None, ImGuiStyleVar.WindowRounding)
        self.ChildRounding : Style.StyleVar = Style.StyleVar(self, 0, None, ImGuiStyleVar.ChildRounding)
        self.FrameRounding : Style.StyleVar = Style.StyleVar(self, 4, None, ImGuiStyleVar.FrameRounding)
        self.PopupRounding : Style.StyleVar = Style.StyleVar(self, 0, None, ImGuiStyleVar.PopupRounding)
        self.ScrollbarRounding : Style.StyleVar = Style.StyleVar(self, 9, None, ImGuiStyleVar.ScrollbarRounding)
        self.GrabRounding : Style.StyleVar = Style.StyleVar(self, 3, None, ImGuiStyleVar.GrabRounding)
        self.TabRounding : Style.StyleVar = Style.StyleVar(self, 4, None, ImGuiStyleVar.TabRounding)
        
        self.WindowTitleAlign : Style.StyleVar = Style.StyleVar(self, 0.0, 0.5, ImGuiStyleVar.WindowTitleAlign)
        # self.WindowMenuButtonPosition : Style.StyleVar = Style.StyleVar(self, 1, ImGuiStyleVar.WindowMenuButtonPosition)
        # self.ColorButtonPosition : Style.StyleVar = Style.StyleVar(self, 1, None, ImGuiStyleVar.ColorButtonPosition)
        self.ButtonTextAlign : Style.StyleVar = Style.StyleVar(self, 0.5, 0.5, ImGuiStyleVar.ButtonTextAlign)
        self.SelectableTextAlign : Style.StyleVar = Style.StyleVar(self, 0.0, 0.0, ImGuiStyleVar.SelectableTextAlign)
        self.SeparatorTextBorderSize : Style.StyleVar = Style.StyleVar(self, 3, None, ImGuiStyleVar.SeparatorTextBorderSize)
        self.SeparatorTextAlign : Style.StyleVar = Style.StyleVar(self, 0, 0.5, ImGuiStyleVar.SeparatorTextAlign)
        self.SeparatorTextPadding : Style.StyleVar = Style.StyleVar(self, 20, 3, ImGuiStyleVar.SeparatorTextPadding)
        # self.LogSliderDeadzone : Style.StyleVar = Style.StyleVar(self, 4, None, ImGuiStyleVar.LogSliderDeadzone)
        #endregion
        
        
        #region Special Style Vars
        self.ButtonPadding : Style.StyleVar = Style.StyleVar(self, 5, 5, ImGuiStyleVar.FramePadding, "Button Padding")
        #endregion
        
        #region Colors
        self.Border = Style.StyleColor(self, 204, 204, 212, 225, PyImGui.ImGuiCol.Border)
        self.BorderShadow = Style.StyleColor(self, 26, 26, 26, 128, PyImGui.ImGuiCol.BorderShadow)
        
        self.Button = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button)
        self.ButtonActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive)
        self.ButtonHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered)
        
        self.CheckMark = Style.StyleColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.CheckMark)        
        self.ChildBg = Style.StyleColor(self, 0, 0, 0, 0, PyImGui.ImGuiCol.ChildBg)
        
        # self.CloseButton = Style.StyleColor(self, 102, 99, 96, 40, PyImGui.ImGuiCol.CloseButton)
        # self.CloseButtonHovered = Style.StyleColor(self, 102, 99, 96, 100, PyImGui.ImGuiCol.CloseButtonHovered)
        # self.CloseButtonActive = Style.StyleColor(self, 102, 99, 96, 255, PyImGui.ImGuiCol.CloseButtonActive)
        
        # self.ComboBg = Style.StyleColor(self, 26, 23, 30, 255, PyImGui.ImGuiCol.ComboBg)
        
        # self.Column = Style.StyleColor(self, 143, 143, 148, 255, PyImGui.ImGuiCol.Column)
        # self.ColumnHovered = Style.StyleColor(self, 61, 59, 74, 255, PyImGui.ImGuiCol.ColumnHovered)
        # self.ColumnActive = Style.StyleColor(self, 143, 143, 148, 255, PyImGui.ImGuiCol.ColumnActive)
        
        self.DragDropTarget = Style.StyleColor(self, 255, 255, 0, 230, PyImGui.ImGuiCol.DragDropTarget)
        
        self.FrameBg = Style.StyleColor(self, 26, 23, 30, 255, PyImGui.ImGuiCol.FrameBg)
        self.FrameBgActive = Style.StyleColor(self, 143, 143, 148, 255, PyImGui.ImGuiCol.FrameBgActive)
        self.FrameBgHovered = Style.StyleColor(self, 61, 59, 74, 255, PyImGui.ImGuiCol.FrameBgHovered)
        
        self.Header = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Header)
        self.HeaderActive = Style.StyleColor(self, 15, 13, 18, 255, PyImGui.ImGuiCol.HeaderActive)
        self.HeaderHovered = Style.StyleColor(self, 143, 143, 148, 255, PyImGui.ImGuiCol.HeaderHovered)
        self.MenuBarBg = Style.StyleColor(self, 26, 23, 30, 255, PyImGui.ImGuiCol.MenuBarBg)
        self.ModalWindowDimBg = Style.StyleColor(self, 204, 204, 204, 89, PyImGui.ImGuiCol.ModalWindowDimBg)
        
        self.NavHighlight = Style.StyleColor(self, 66, 150, 250, 255, PyImGui.ImGuiCol.NavHighlight)
        self.NavWindowingDimBg = Style.StyleColor(self, 204, 204, 204, 51, PyImGui.ImGuiCol.NavWindowingDimBg)
        self.NavWindowingHighlight = Style.StyleColor(self, 255, 255, 255, 179, PyImGui.ImGuiCol.NavWindowingHighlight)
        
        self.PlotHistogram = Style.StyleColor(self, 102, 99, 96, 160, PyImGui.ImGuiCol.PlotHistogram)
        self.PlotHistogramHovered = Style.StyleColor(self, 64, 255, 0, 255, PyImGui.ImGuiCol.PlotHistogramHovered)
        self.PlotLines = Style.StyleColor(self, 102, 99, 96, 160, PyImGui.ImGuiCol.PlotLines)
        self.PlotLinesHovered = Style.StyleColor(self, 64, 255, 0, 255, PyImGui.ImGuiCol.PlotLinesHovered)
        self.PopupBg = Style.StyleColor(self, 2, 2, 2, 215, PyImGui.ImGuiCol.PopupBg)
        
        self.ResizeGrip = Style.StyleColor(self, 0, 0, 0, 0, PyImGui.ImGuiCol.ResizeGrip)
        self.ResizeGripActive = Style.StyleColor(self, 15, 13, 18, 255, PyImGui.ImGuiCol.ResizeGripActive)
        self.ResizeGripHovered = Style.StyleColor(self, 143, 143, 148, 255, PyImGui.ImGuiCol.ResizeGripHovered)
        
        self.ScrollbarBg = Style.StyleColor(self, 2, 2, 2, 215, PyImGui.ImGuiCol.ScrollbarBg)
        self.ScrollbarGrab = Style.StyleColor(self, 51, 76, 76, 128, PyImGui.ImGuiCol.ScrollbarGrab)
        self.ScrollbarGrabActive = Style.StyleColor(self, 51, 76, 102, 128, PyImGui.ImGuiCol.ScrollbarGrabActive)
        self.ScrollbarGrabHovered = Style.StyleColor(self, 51, 76, 102, 128, PyImGui.ImGuiCol.ScrollbarGrabHovered)
        
        self.Separator = Style.StyleColor(self, 110, 110, 128, 128, PyImGui.ImGuiCol.Separator)
        self.SeparatorActive = Style.StyleColor(self, 26, 102, 191, 255, PyImGui.ImGuiCol.SeparatorActive)
        self.SeparatorHovered = Style.StyleColor(self, 26, 102, 191, 199, PyImGui.ImGuiCol.SeparatorHovered)
        
        self.SliderGrab = Style.StyleColor(self, 51, 76, 76, 128, PyImGui.ImGuiCol.SliderGrab)
        self.SliderGrabActive = Style.StyleColor(self, 51, 76, 102, 128, PyImGui.ImGuiCol.SliderGrabActive)
        
        self.Tab = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Tab)
        self.TabActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.TabActive)
        self.TabHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.TabHovered)
        self.TabUnfocused = Style.StyleColor(self, 17, 26, 38, 248, PyImGui.ImGuiCol.TabUnfocused)
        self.TabUnfocusedActive = Style.StyleColor(self, 35, 67, 108, 255, PyImGui.ImGuiCol.TabUnfocusedActive)
        
        self.TableBorderLight = Style.StyleColor(self, 204, 204, 212, 225, PyImGui.ImGuiCol.TableBorderLight)
        self.TableBorderStrong = Style.StyleColor(self, 204, 204, 212, 225, PyImGui.ImGuiCol.TableBorderStrong)
        self.TableHeaderBg = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.TableHeaderBg)
        self.TableRowBg = Style.StyleColor(self, 15, 13, 18, 255, PyImGui.ImGuiCol.TableRowBg)
        self.TableRowBgAlt = Style.StyleColor(self, 26, 23, 30, 255, PyImGui.ImGuiCol.TableRowBgAlt)
        
        self.Text = Style.StyleColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.Text)
        self.TextDisabled = Style.StyleColor(self, 51, 51, 51, 255, PyImGui.ImGuiCol.TextDisabled)
        self.TextSelectedBg = Style.StyleColor(self, 26, 255, 26, 110, PyImGui.ImGuiCol.TextSelectedBg)
        
        self.TitleBg = Style.StyleColor(self, 13, 13, 13, 215, PyImGui.ImGuiCol.TitleBg)
        self.TitleBgActive = Style.StyleColor(self, 51, 51, 51, 215, PyImGui.ImGuiCol.TitleBgActive)
        self.TitleBgCollapsed = Style.StyleColor(self, 5, 5, 5, 215, PyImGui.ImGuiCol.TitleBgCollapsed)

        self.WindowBg = Style.StyleColor(self, 2, 2, 2, 215, PyImGui.ImGuiCol.WindowBg)
        #endregion

        #region Custom Colors        
        self.PrimaryButton = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button, StyleColorType.Custom, "Primary Button")
        self.PrimaryButtonHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered, StyleColorType.Custom, "Primary Button Hovered")
        self.PrimaryButtonActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive, StyleColorType.Custom, "Primary Button Active")

        self.DangerButton = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button, StyleColorType.Custom, "Danger Button")
        self.DangerButtonHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered, StyleColorType.Custom, "Danger Button Hovered")
        self.DangerButtonActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive, StyleColorType.Custom, "Danger Button Active")

        self.ToggleButtonEnabled = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button, StyleColorType.Custom, "Toggle Button Enabled")
        self.ToggleButtonEnabledHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered, StyleColorType.Custom, "Toggle Button Enabled Hovered")
        self.ToggleButtonEnabledActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive, StyleColorType.Custom, "Toggle Button Enabled Active")

        self.ToggleButtonDisabled = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button, StyleColorType.Custom, "Toggle Button Disabled")
        self.ToggleButtonDisabledHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered, StyleColorType.Custom, "Toggle Button Disabled Hovered")
        self.ToggleButtonDisabledActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive, StyleColorType.Custom, "Toggle Button Disabled Active")

        self.TextTreeNode = Style.StyleColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.Text, StyleColorType.Custom, "Text Tree Node")
        self.TextObjectiveCompleted = Style.StyleColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.Text, StyleColorType.Custom, "Text Objective Completed")
        self.Hyperlink = Style.StyleColor(self, 102, 187, 238, 255, PyImGui.ImGuiCol.Text, StyleColorType.Custom, "Text Hyperlink")

        self.ComboTextureBackground = Style.StyleColor(self, 26, 23, 30, 255, None, StyleColorType.Texture, "Combo Background (Textured)")
        self.ComboTextureBackgroundHovered = Style.StyleColor(self, 61, 59, 74, 255, None, StyleColorType.Texture, "Combo Background Hovered (Textured)")
        self.ComboTextureBackgroundActive = Style.StyleColor(self, 143, 143, 148, 255, None, StyleColorType.Texture, "Combo Background Active (Textured)")

        self.ButtonTextureBackground = Style.StyleColor(self, 26, 23, 30, 255, None, StyleColorType.Texture, "Button Background (Textured)")
        self.ButtonTextureBackgroundHovered = Style.StyleColor(self, 61, 59, 74, 255, None, StyleColorType.Texture, "Button Background Hovered (Textured)")
        self.ButtonTextureBackgroundActive = Style.StyleColor(self, 143, 143, 148, 255, None, StyleColorType.Texture, "Button Background Active (Textured)")
        self.ButtonTextureBackgroundDisabled = Style.StyleColor(self, 143, 143, 148, 255, None, StyleColorType.Texture, "Button Background Disabled (Textured)")
        #endregion

        # Collect attributes
        attributes = {name: getattr(self, name) for name in dir(self)}
        self.Colors : dict[str, Style.StyleColor] = {name: attributes[name] for name in attributes if isinstance(attributes[name], Style.StyleColor) and attributes[name].color_type == StyleColorType.Default}
        self.TextureColors : dict[str, Style.StyleColor] = {name: attributes[name] for name in attributes if isinstance(attributes[name], Style.StyleColor) and attributes[name].color_type == StyleColorType.Texture}
        self.CustomColors : dict[str, Style.StyleColor] = {name: attributes[name] for name in attributes if isinstance(attributes[name], Style.StyleColor) and  attributes[name].color_type == StyleColorType.Custom}
        self.StyleVars : dict[str, Style.StyleVar] = {name: attributes[name] for name in attributes if isinstance(attributes[name], Style.StyleVar)}

    def copy(self):
        style = Style()
        style.Theme = self.Theme

        for name, c in self.Colors.items():
            attr = getattr(style, name)
            if isinstance(attr, Style.StyleColor):
                attr.set_rgba(*c.to_tuple())

        for name, c in self.CustomColors.items():
            attr = getattr(style, name)
            if isinstance(attr, Style.StyleColor):
                attr.set_rgba(*c.to_tuple())

        for name, c in self.TextureColors.items():
            attr = getattr(style, name)
            if isinstance(attr, Style.StyleColor):
                attr.set_rgba(*c.to_tuple())

        for name, v in self.StyleVars.items():
            attr = getattr(style, name)
            if isinstance(attr, Style.StyleVar):
                attr.value1, attr.value2 = v.value1, v.value2

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

    def save_to_json(self):
        style_data = {
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
                self.pyimgui_style.set_color(attribute.img_color_enum, *attribute.to_tuple_normalized())
                
        for _, attribute in self.StyleVars.items():
            if attribute.img_style_enum:
                pyimgui_style_attribute = getattr(self.pyimgui_style, attribute.img_style_enum.name, None)
                
                if pyimgui_style_attribute is not None:
                    if attribute.value2 is not None:
                        setattr(self.pyimgui_style, attribute.img_style_enum.name, (attribute.value1, attribute.value2))
                    else:
                        setattr(self.pyimgui_style, attribute.img_style_enum.name, attribute.value1)

        self.pyimgui_style.Push()

    @classmethod
    def load_from_json(cls, path: str, theme : StyleTheme) -> "Style":
        style = cls()
        if not os.path.exists(path):
            return style

        with open(path, "r") as f:
            style_data = json.load(f)

        style.Theme = theme

        for color_name, color_data in style_data.get("Colors", {}).items():
            attribute = getattr(style, color_name, None)
            if attribute and isinstance(attribute, cls.StyleColor):
                attribute.load_from_json(color_data)

        for color_name, color_data in style_data.get("CustomColors", {}).items():
            attribute = getattr(style, color_name, None)
            if attribute and isinstance(attribute, cls.StyleColor):
                attribute.load_from_json(color_data)

        for color_name, color_data in style_data.get("TextureColors", {}).items():
            attribute = getattr(style, color_name, None)
            if attribute and isinstance(attribute, cls.StyleColor):
                attribute.load_from_json(color_data)

        for var_name, var_data in style_data.get("StyleVars", {}).items():
            attribute = getattr(style, var_name, None)
            if attribute and isinstance(attribute, cls.StyleVar):
                attribute.load_from_json(var_data)

        return style

    @classmethod
    def load_theme(cls, theme: StyleTheme) -> "Style":
        file_path = os.path.join("Styles", f"{theme.name}.json")
        default_file_path = os.path.join("Styles", f"{theme.name}.default.json")
        path = file_path if os.path.exists(file_path) else default_file_path if os.path.exists(default_file_path) else None
        return cls.load_from_json(path, theme) if path else cls(theme)

    @classmethod
    def load_default_theme(cls, theme: StyleTheme) -> "Style":
        default_file_path = os.path.join("Styles", f"{theme.name}.default.json")
        return cls.load_from_json(default_file_path, theme) if os.path.exists(default_file_path) else cls(theme)

    def preview(self):
        """Temporarily apply this Style into ImGui's live StyleConfig (not permanent)."""
        if not hasattr(self, "pyimgui_style"):
            self.pyimgui_style = PyImGui.StyleConfig()

        # Sync baseline from global
        self.pyimgui_style.Pull()

        # Apply Colors
        for _, attr in self.Colors.items():
            if attr.img_color_enum and isinstance(attr, Style.StyleColor):
                self.pyimgui_style.set_color(attr.img_color_enum, *attr.to_tuple())

        # Apply CustomColors
        for _, attr in self.CustomColors.items():
            if attr.img_color_enum and isinstance(attr, Style.StyleColor):
                self.pyimgui_style.set_color(attr.img_color_enum, *attr.to_tuple())

        # Apply TextureColors
        for _, attr in self.TextureColors.items():
            if attr.img_color_enum and isinstance(attr, Style.StyleColor):
                self.pyimgui_style.set_color(attr.img_color_enum, *attr.to_tuple())

        # StyleVars are handled separately if needed (scalars/vec2s already live in StyleConfig)

    def apply_permanently(self):
        """Commit current preview to ImGui's global StyleConfig (persistent)."""
        if hasattr(self, "pyimgui_style"):
            self.pyimgui_style.Push()