import PyImGui
import json
import os
from enum import IntEnum
from.types import ImGuiStyleVar
from ..Py4GWcorelib import Utils, Color

class Style:    
    pyimgui_style = PyImGui.StyleConfig()

    class StyleTheme(IntEnum):
        ImGui = 0
        Guild_Wars = 1
        Minimalus = 2

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

        def from_json(self, img_style_enum: str, data):
            # self.img_style_enum = getattr(ImGuiStyleVar, img_style_enum) if img_style_enum in ImGuiStyleVar.__members__ else None
            self.value1 = data["value1"]
            self.value2 = data.get("value2", None)

        def get_current(self):
            return self.pushed_stack[0] if self.pushed_stack else self

        def copy(self):
            return Style.StyleVar(self.style, self.value1, self.value2, self.img_style_enum)

        def __hash__(self): return hash((self.img_style_enum, self.value1, self.value2))
        def __eq__(self, value): return isinstance(value, Style.StyleVar) and (self.img_style_enum, self.value1, self.value2) == (value.img_style_enum, value.value1, value.value2)
        def __ne__(self, value): return not self.__eq__(value)        

    class CustomColor:
        def __init__(self, style: "Style", r: int, g: int, b: int, a: int = 255, img_color_enum: PyImGui.ImGuiCol | None = None):
            self.style = style
            self.color: Color = Color(r, g, b, a)
            self.img_color_enum = img_color_enum
            self.pushed_stack: list[Style.CustomColor] = []

        def __hash__(self): return hash((self.img_color_enum, self.color))
        def __eq__(self, other): return isinstance(other, Style.CustomColor) and self.color == other.color
        def __ne__(self, other): return not self.__eq__(other)

        def set_rgb_color(self, r: int, g: int, b: int, a: int = 255):
            self.color = Color(r, g, b, a)

        def set_tuple_color(self, color: tuple[float, float, float, float]):
            self.color = Color.from_tuple(color)

        def push_color(self, rgba: tuple[int, int, int, int] | None = None):
            col = Style.CustomColor(self.style, *rgba, self.img_color_enum) if rgba else self.get_current()
            if self.img_color_enum is not None:
                PyImGui.push_style_color(self.img_color_enum, col.color.color_tuple)
            self.pushed_stack.insert(0, col)

        def pop_color(self):
            if self.pushed_stack:
                col = self.pushed_stack.pop(0)
                if col.img_color_enum:
                    PyImGui.pop_style_color(1)

        def get_current(self): return self.pushed_stack[0] if self.pushed_stack else self

        def to_json(self):
            return {"img_color_enum": self.img_color_enum.name if self.img_color_enum else None, **dict(zip("rgba", self.color.to_tuple()))}

        def from_json(self, data):
            img_color_enum = data.get("img_color_enum", None)
            self.img_color_enum = getattr(PyImGui.ImGuiCol, img_color_enum) if img_color_enum in PyImGui.ImGuiCol.__members__ else None
            self.color = Color(data["r"], data["g"], data["b"], data.get("a", 255))


    class StyleColor:
        def __init__(self, style: "Style", r: int, g: int, b: int, a: int = 255, img_color_enum: PyImGui.ImGuiCol | None = None):
            self.style = style
            self.img_color_enum = img_color_enum
            self.color: Color = Color(r, g, b, a)
            self.pushed_stack: list[Style.StyleColor] = []

        def __hash__(self): return hash((self.img_color_enum, self.color))
        def __eq__(self, other): return isinstance(other, Style.StyleColor) and self.color == other.color and self.img_color_enum == other.img_color_enum
        def __ne__(self, other): return not self.__eq__(other)

        def set_rgb_color(self, r: int, g: int, b: int, a: int = 255): self.color = Color(r, g, b, a)
        def set_tuple_color(self, color: tuple[float, float, float, float]): self.color = Color.from_tuple(color)

        def push_color(self, rgba: tuple[int, int, int, int] | None = None):
            col = Style.StyleColor(self.style, *rgba, self.img_color_enum) if rgba else self.get_current()
            if col.img_color_enum is not None:
                PyImGui.push_style_color(col.img_color_enum, col.color.color_tuple)
            self.pushed_stack.insert(0, col)

        def pop_color(self):
            if self.pushed_stack:
                col = self.pushed_stack.pop(0)
                if col.img_color_enum:
                    PyImGui.pop_style_color(1)

        def get_current(self): return self.pushed_stack[0] if self.pushed_stack else self

        def to_json(self):
            return {"img_color_enum": self.img_color_enum.name if self.img_color_enum else None, **dict(zip("rgba", self.color.to_tuple()))}

        def from_json(self, data):
            img_color_enum = data.get("img_color_enum", None)
            self.img_color_enum = getattr(PyImGui.ImGuiCol, img_color_enum) if img_color_enum in PyImGui.ImGuiCol.__members__ else None
            self.color = Color(data["r"], data["g"], data["b"], data.get("a", 255))

    def __init__(self):
        # Set the default style as base so we can push it and cover all
        self.Theme : Style.StyleTheme = Style.StyleTheme.ImGui

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

        for name, c in self.Colors.items():
            attr = getattr(style, name)
            if isinstance(attr, Style.StyleColor):
                attr.color = Color(*c.color.to_tuple())

        for name, c in self.CustomColors.items():
            attr = getattr(style, name)
            if isinstance(attr, Style.CustomColor):
                attr.color = Color(*c.color.to_tuple())

        for name, c in self.TextureColors.items():
            attr = getattr(style, name)
            if isinstance(attr, Style.CustomColor):
                attr.color = Color(*c.color.to_tuple())

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
                self.pyimgui_style.set_color(attribute.img_color_enum, *attribute.color.to_tuple_normalized())
        self.pyimgui_style.Push()

    @classmethod
    def load_from_json(cls, path: str) -> "Style":
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
    def load_theme(cls, theme: StyleTheme) -> "Style":
        file_path = os.path.join("Styles", f"{theme.name}.json")
        default_file_path = os.path.join("Styles", f"{theme.name}.default.json")
        path = file_path if os.path.exists(file_path) else default_file_path
        return cls.load_from_json(path)

    @classmethod
    def load_default_theme(cls, theme: StyleTheme) -> "Style":
        default_file_path = os.path.join("Styles", f"{theme.name}.default.json")
        return cls.load_from_json(default_file_path)

    def preview(self):
        """Temporarily apply this Style into ImGui's live StyleConfig (not permanent)."""
        if not hasattr(self, "pyimgui_style"):
            self.pyimgui_style = PyImGui.StyleConfig()

        # Sync baseline from global
        self.pyimgui_style.Pull()

        # Apply Colors
        for _, attr in self.Colors.items():
            if attr.img_color_enum and isinstance(attr.color, Color):
                self.pyimgui_style.set_color(attr.img_color_enum, *attr.color.to_tuple())

        # Apply CustomColors
        for _, attr in self.CustomColors.items():
            if attr.img_color_enum and isinstance(attr.color, Color):
                self.pyimgui_style.set_color(attr.img_color_enum, *attr.color.to_tuple())

        # Apply TextureColors
        for _, attr in self.TextureColors.items():
            if attr.img_color_enum and isinstance(attr.color, Color):
                self.pyimgui_style.set_color(attr.img_color_enum, *attr.color.to_tuple())

        # StyleVars are handled separately if needed (scalars/vec2s already live in StyleConfig)

    def apply_permanently(self):
        """Commit current preview to ImGui's global StyleConfig (persistent)."""
        if hasattr(self, "pyimgui_style"):
            self.pyimgui_style.Push()