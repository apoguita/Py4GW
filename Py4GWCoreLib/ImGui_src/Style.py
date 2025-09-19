import PyImGui
import json
import os
from enum import IntEnum
from.types import ImGuiStyleVar, StyleColorType, StyleTheme
from ..Py4GWcorelib import Utils, Color

class Style:    
    pyimgui_style = PyImGui.StyleConfig()

    class StyleVar:
        def __init__(self, style: "Style", value1: float, value2: float | None = None, img_style_enum: "ImGuiStyleVar|None" = None):
            self.style = style
            self.img_style_enum: ImGuiStyleVar | None = img_style_enum
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
        def __init__(self, style: "Style", r: int, g: int, b: int, a: int = 255, img_color_enum: PyImGui.ImGuiCol | None = None, color_type: StyleColorType = StyleColorType.Default):
            super().__init__(r, g, b, a)
            self.style = style
            self.img_color_enum = img_color_enum
            self.color_type = color_type
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
            if self.pushed_stack:
                col = self.pushed_stack.pop(0)
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

        self.WindowPadding : Style.StyleVar = Style.StyleVar(self, 10, 10, ImGuiStyleVar.WindowPadding)
        self.CellPadding : Style.StyleVar = Style.StyleVar(self, 5, 5, ImGuiStyleVar.CellPadding)
        self.ChildRounding : Style.StyleVar = Style.StyleVar(self, 0, None, ImGuiStyleVar.ChildRounding)
        self.TabRounding : Style.StyleVar = Style.StyleVar(self, 4, None, ImGuiStyleVar.TabRounding)
        self.PopupRounding : Style.StyleVar = Style.StyleVar(self, 4, None, ImGuiStyleVar.PopupRounding)
        self.WindowRounding : Style.StyleVar = Style.StyleVar(self, 4, None, ImGuiStyleVar.WindowRounding)
        self.FramePadding : Style.StyleVar = Style.StyleVar(self, 5, 5, ImGuiStyleVar.FramePadding)
        self.ButtonPadding : Style.StyleVar = Style.StyleVar(self, 5, 5, ImGuiStyleVar.FramePadding)
        self.FrameRounding : Style.StyleVar = Style.StyleVar(self, 4, None, ImGuiStyleVar.FrameRounding)
        self.ItemSpacing : Style.StyleVar = Style.StyleVar(self, 10, 6, ImGuiStyleVar.ItemSpacing)
        self.ItemInnerSpacing : Style.StyleVar = Style.StyleVar(self, 6, 4, ImGuiStyleVar.ItemInnerSpacing)
        self.IndentSpacing : Style.StyleVar = Style.StyleVar(self, 20, None, ImGuiStyleVar.IndentSpacing)
        self.ScrollbarSize : Style.StyleVar = Style.StyleVar(self, 20, None, ImGuiStyleVar.ScrollbarSize)
        self.ScrollbarRounding : Style.StyleVar = Style.StyleVar(self, 9, None, ImGuiStyleVar.ScrollbarRounding)
        self.GrabMinSize : Style.StyleVar = Style.StyleVar(self, 5, None, ImGuiStyleVar.GrabMinSize)
        self.GrabRounding : Style.StyleVar = Style.StyleVar(self, 3, None, ImGuiStyleVar.GrabRounding)

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

        self.PrimaryButton = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button, StyleColorType.Custom)
        self.PrimaryButtonHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered, StyleColorType.Custom)
        self.PrimaryButtonActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive, StyleColorType.Custom)

        self.DangerButton = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button, StyleColorType.Custom)
        self.DangerButtonHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered, StyleColorType.Custom)
        self.DangerButtonActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive, StyleColorType.Custom)

        self.ToggleButtonEnabled = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button, StyleColorType.Custom)
        self.ToggleButtonEnabledHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered, StyleColorType.Custom)
        self.ToggleButtonEnabledActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive, StyleColorType.Custom)

        self.ToggleButtonDisabled = Style.StyleColor(self, 26, 38, 51, 255, PyImGui.ImGuiCol.Button, StyleColorType.Custom)
        self.ToggleButtonDisabledHovered = Style.StyleColor(self, 51, 76, 102, 255, PyImGui.ImGuiCol.ButtonHovered, StyleColorType.Custom)
        self.ToggleButtonDisabledActive = Style.StyleColor(self, 102, 127, 153, 255, PyImGui.ImGuiCol.ButtonActive, StyleColorType.Custom)

        self.TextCollapsingHeader = Style.StyleColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.Text, StyleColorType.Custom)
        self.TextTreeNode = Style.StyleColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.Text, StyleColorType.Custom)
        self.TextObjectiveCompleted = Style.StyleColor(self, 204, 204, 204, 255, PyImGui.ImGuiCol.Text, StyleColorType.Custom)
        self.Hyperlink = Style.StyleColor(self, 102, 187, 238, 255, PyImGui.ImGuiCol.Text, StyleColorType.Custom)

        self.ComboTextureBackground = Style.StyleColor(self, 26, 23, 30, 255, None, StyleColorType.Texture)
        self.ComboTextureBackgroundHovered = Style.StyleColor(self, 61, 59, 74, 255, None, StyleColorType.Texture)
        self.ComboTextureBackgroundActive = Style.StyleColor(self, 143, 143, 148, 255, None, StyleColorType.Texture)

        self.ButtonTextureBackground = Style.StyleColor(self, 26, 23, 30, 255, None, StyleColorType.Texture)
        self.ButtonTextureBackgroundHovered = Style.StyleColor(self, 61, 59, 74, 255, None, StyleColorType.Texture)
        self.ButtonTextureBackgroundActive = Style.StyleColor(self, 143, 143, 148, 255, None, StyleColorType.Texture)
        self.ButtonTextureBackgroundDisabled = Style.StyleColor(self, 143, 143, 148, 255, None, StyleColorType.Texture)

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
            attribute = getattr(style, color_name)
            if isinstance(attribute, cls.StyleColor):
                attribute.load_from_json(color_data)

        for color_name, color_data in style_data.get("CustomColors", {}).items():
            attribute = getattr(style, color_name)
            if isinstance(attribute, cls.StyleColor):
                attribute.load_from_json(color_data)

        for color_name, color_data in style_data.get("TextureColors", {}).items():
            attribute = getattr(style, color_name)
            if isinstance(attribute, cls.StyleColor):
                attribute.load_from_json(color_data)

        for var_name, var_data in style_data.get("StyleVars", {}).items():
            attribute = getattr(style, var_name)
            if isinstance(attribute, cls.StyleVar):
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