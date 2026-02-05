import math
from ..Overlay import Overlay
from ..enums import get_texture_for_model, ImguiFonts
from ..Py4GWcorelib import Color, ColorPalette, ConsoleLog, Utils
from typing import Tuple, TypeAlias, Optional, overload
from .types import Alignment, HorizontalAlignment, ImGuiStyleVar, StyleTheme, ControlAppearance, TextDecorator, VerticalAlignment
from .types import ImGuiStyleVar, StyleTheme, ControlAppearance, TextDecorator
from .Style import Style
from .Textures import TextureSliceMode, ThemeTextures, TextureState
from .WindowModule import WindowModule
from .IconsFontAwesome5 import IconsFontAwesome5
import PyImGui
import Py4GW

#region ImGui
class ImGui:
    WindowModule: TypeAlias = WindowModule
    ImGuiStyleVar: TypeAlias  = ImGuiStyleVar
    style = PyImGui.StyleConfig()
    
    #region Styles

    Styles : dict[StyleTheme, Style] = {}
    __style_stack : list[Style] = []
    Selected_Style : Style = Style()
     #we need a better way of categorizing this
     #cannot be hard coded
     #same as adding new styles, cannot be hard coded
    Textured_Themes = [StyleTheme.Guild_Wars,
                       StyleTheme.Minimalus]
    overlay_instance = Overlay()

    @staticmethod
    def get_style() -> Style:
        return ImGui.__style_stack[0] if ImGui.__style_stack else ImGui.Selected_Style

    @staticmethod
    def push_theme(theme: StyleTheme):
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
    def set_theme(theme: StyleTheme):
        ConsoleLog("ImGui Style", f"Setting theme to {theme.name}")

        if not theme in ImGui.Styles:
            ImGui.Styles[theme] = Style.load_theme(theme)

        ImGui.Selected_Style = ImGui.Styles[theme]
        ImGui.Selected_Style.apply_to_style_config()

    @staticmethod
    def reload_theme(theme: StyleTheme):
        set_style = ImGui.get_style().Theme == theme

        ImGui.Styles[theme] = Style.load_theme(theme)        

        if set_style:
            ImGui.Selected_Style = ImGui.Styles[theme]

    @staticmethod
    def push_theme_window_style(theme: StyleTheme = StyleTheme.ImGui):
        if not theme in ImGui.Styles:
            ImGui.Styles[theme] = Style.load_theme(theme)

        if theme not in ImGui.Styles:
            ConsoleLog("Style", f"Style {theme.name} not found.")
            return

        ImGui.Styles[theme].push_style()

    @staticmethod
    def pop_theme_window_style(theme: StyleTheme = StyleTheme.ImGui):
        if theme not in ImGui.Styles:
            return
        ImGui.Styles[theme].pop_style()

    #region overloads
    @staticmethod
    def push_style_color(idx: int, col: tuple[float, float, float, float]): return PyImGui.push_style_color(idx, col)

    @staticmethod
    def pop_style_color(count: int = 1): return PyImGui.pop_style_color(count)

    @staticmethod
    def get_x_position_aligned(alignment: Alignment, parent_pos: tuple[float, float], parent_size: tuple[float, float], child_size: tuple[float, float], offset: tuple[float, float]=(0,0)) -> float: 
        '''Get X position aligned within/in relation to a parent rectangle.'''
        
        match alignment.horizontal:
            case HorizontalAlignment.LeftOf:
                return parent_pos[0] - child_size[0] + offset[0]
            
            case HorizontalAlignment.Left:
                return parent_pos[0] + offset[0]
            
            case HorizontalAlignment.Center:
                return parent_pos[0] + (parent_size[0] - child_size[0]) // 2 + offset[0]
            
            case HorizontalAlignment.Right:
                return parent_pos[0] + parent_size[0] - child_size[0] + offset[0]
            
            case HorizontalAlignment.RightOf:
                return parent_pos[0] + parent_size[0] + offset[0]
        
    @staticmethod
    def get_y_position_aligned(alignment: Alignment, parent_pos: tuple[float, float], parent_size: tuple[float, float], child_size: tuple[float, float], offset: tuple[float, float]=(0,0)) -> float: 
        '''Get Y position aligned within/in relation to a parent rectangle.'''
        
        match alignment.vertical:
            case VerticalAlignment.Above:
                return parent_pos[1] - child_size[1] + offset[1]
            
            case VerticalAlignment.Top:
                return parent_pos[1] + offset[1]
            
            case VerticalAlignment.Middle:
                return parent_pos[1] + (parent_size[1] - child_size[1]) // 2 + offset[1]
            
            case VerticalAlignment.Bottom:
                return parent_pos[1] + parent_size[1] - child_size[1] + offset[1]
            
            case VerticalAlignment.Below:
                return parent_pos[1] + parent_size[1] + offset[1]
            
    @staticmethod
    def get_position_aligned(alignment: Alignment, parent_pos: tuple[float, float], parent_size: tuple[float, float], child_size: tuple[float, float], offset: tuple[float, float]=(0,0)) -> tuple[float, float]:  
        '''Get position (x,y) aligned within/in relation to a parent rectangle.'''  
                       
        x = ImGui.get_x_position_aligned(alignment, parent_pos, parent_size, child_size, offset)
        y = ImGui.get_y_position_aligned(alignment, parent_pos, parent_size, child_size, offset)
        
        return x, y

    @staticmethod
    def is_mouse_in_rect(rect: tuple[float, float, float, float], mouse_pos: Optional[tuple[float, float]] = None) -> bool:
        '''Check if mouse is within given rectangle (x, y, width, height).'''
        pyimgui_io = PyImGui.get_io()
        mouse_pos = (pyimgui_io.mouse_pos_x, pyimgui_io.mouse_pos_y) if mouse_pos is None else mouse_pos
        
        return (rect[0] <= mouse_pos[0] <= rect[0] + rect[2] and
                rect[1] <= mouse_pos[1] <= rect[1] + rect[3])

    @staticmethod
    def get_clamped_to_displayport(
        pos: tuple[float, float],
        size: tuple[float, float],
        min_visible_x: float | None = None,
        min_visible_y: float | None = None,
        *,
        relative: bool = False,
    ) -> tuple[float, float]:
        """
        Clamp a position and size so that it stays (mostly) visible within displayport bounds.
        Optionally specify how much of the window must remain visible.

        Args:
            min_visible_x: minimal visible width in pixels or fraction (0–1).
            min_visible_y: minimal visible height in pixels or fraction (0–1).
            relative: if True, interpret min_visible_* as relative (0–1 of window size).

        Returns:
            New clamped (x, y) position tuple.
        """        
        x, y = pos
        w, h = size
        
        py_io = PyImGui.get_io()
        display_size_x = py_io.display_size_x
        display_size_y = py_io.display_size_y

        # Compute required visible margin in pixels
        if min_visible_x is None:
            min_visible_x = 0
        if min_visible_y is None:
            min_visible_y = 0

        if relative:
            min_visible_x = w * min_visible_x
            min_visible_y = h * min_visible_y

        # Ensure the window remains at least partially visible
        min_x = -w + min_visible_x
        min_y = -h + min_visible_y
        max_x = display_size_x - min_visible_x
        max_y = display_size_y - min_visible_y

        # Clamp position
        clamped_x = max(min_x, min(x, max_x))
        clamped_y = max(min_y, min(y, max_y))
        
        return (clamped_x, clamped_y)
            
    @staticmethod
    def is_window_within_displayport() -> bool:
        pos = PyImGui.get_window_pos()
        size = PyImGui.get_window_size()
        
        clamped_x, clamped_y = ImGui.get_clamped_to_displayport(pos=pos, size=size)        
        return (clamped_x, clamped_y) != pos
            
    @staticmethod
    def set_window_within_displayport(
        min_visible_x: float | None = None,
        min_visible_y: float | None = None,
        cond: PyImGui.ImGuiCond = PyImGui.ImGuiCond.Always,
        *,
        relative: bool = False,
    ):
        """
        Set a window position so that it stays (mostly) visible within display bounds.
        Optionally specify how much of the window must remain visible.

        Args:
            min_visible_x: minimal visible width in pixels or fraction (0–1).
            min_visible_y: minimal visible height in pixels or fraction (0–1).
            relative: if True, interpret min_visible_* as relative (0–1 of window size).

        Returns:
            New clamped (x, y) position tuple.
        """
        
        pos = PyImGui.get_window_pos()
        size = PyImGui.get_window_size()
        clamped_x, clamped_y = ImGui.get_clamped_to_displayport(pos=pos, size=size, min_visible_x=min_visible_x, min_visible_y=min_visible_y, relative=relative)
        
        if (clamped_x, clamped_y) != pos:
            PyImGui.set_window_pos(clamped_x, clamped_y, cond)
    
    @staticmethod
    def get_item_rect() -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        '''Returns (min, max, size) of the last item rect.'''
        min_ = PyImGui.get_item_rect_min()
        max_ = PyImGui.get_item_rect_max()
        width = max_[0] - min_[0]
        height = max_[1] - min_[1]

        return min_, max_, (width, height)

    @staticmethod
    def trim_text_to_width(text: str, max_width: float, ellipsis: str = "..."):
        """
        Safe incremental version, trimming character-by-character from the end
        until the string fits.
        """

        # Need at least 1 character + ellipsis
        if len(text) == 0:
            return ""

        w, _ = PyImGui.calc_text_size(text)
        if w <= max_width:
            return text

        trimmed = text
        while len(trimmed) > 1:
            w, _ = PyImGui.calc_text_size(trimmed + ellipsis)
            if w <= max_width:
                return trimmed + ellipsis
            trimmed = trimmed[:-1]

        return trimmed or ""
    
    @staticmethod
    def _is_textured_theme() -> bool: return ImGui.get_style().Theme in ImGui.Textured_Themes
    
    @staticmethod
    def Begin(ini_key: str, name: str, p_open=None, flags=PyImGui.WindowFlags.NoFlag) -> bool:
        from Py4GWCoreLib.IniManager import IniManager
        IniManager().begin_window_config(ini_key)

        result = ImGui.begin(name, p_open, flags)

        # mark only if window is active
        IniManager().track_window_collapsed(ini_key, result)
        if result:
            IniManager().mark_begin_success(ini_key)

        return result
    
    @staticmethod
    def begin (name: str, p_open: Optional[bool] = None, flags: PyImGui.WindowFlags = PyImGui.WindowFlags.NoFlag) -> bool:
        if not ImGui._is_textured_theme(): 
            return PyImGui.begin(name, p_open, flags)
        
        if name not in WindowModule._windows:
            WindowModule._windows[name] = WindowModule(name, window_flags=flags)

            #imgui_ini_reader = ImGuiIniReader()
            window = None #imgui_ini_reader.get(name)
            screen_width, screen_height = ImGui.overlay_instance.GetDisplaySize().x, ImGui.overlay_instance.GetDisplaySize().y
            #set position to the middle of the screen
            window_pos = (screen_width / 2 - 800 / 2, screen_height / 2 - 600 / 2)   
            WindowModule._windows[name].window_pos = window.pos if window else window_pos
            WindowModule._windows[name].window_size = window.size if window else (800.0, 600.0)
            WindowModule._windows[name].collapse = window.collapsed if window else False

        return WindowModule._windows[name].begin(p_open, flags)
    
    @staticmethod
    def begin_with_close(name: str, p_open: Optional[bool] = None, flags: PyImGui.WindowFlags = PyImGui.WindowFlags.NoFlag) -> tuple[bool, bool]:
        if not ImGui._is_textured_theme():
            return PyImGui.begin_with_close(name, p_open if p_open is not None else True, flags)
        
        if name not in WindowModule._windows:
            WindowModule._windows[name] = WindowModule(name, window_flags=flags)

            #imgui_ini_reader = ImGuiIniReader()
            window = None #imgui_ini_reader.get(name)
            WindowModule._windows[name].window_pos = window.pos if window else (100.0, 100.0)
            WindowModule._windows[name].window_size = window.size if window else (800.0, 600.0)
            WindowModule._windows[name].collapse = window.collapsed if window else False

        WindowModule._windows[name].can_close = True
        open = WindowModule._windows[name].begin(p_open, flags)

        return open, open
    
    @staticmethod
    def end(): return PyImGui.end()
    
    @staticmethod
    def End(ini_key: str):
        from Py4GWCoreLib.IniManager import IniManager
        # End must be callable always, but IniManager.end_window_config will no-op if Begin was not active
        IniManager().end_window_config(ini_key)
        PyImGui.end()
        IniManager().save_vars(ini_key)

    @staticmethod
    def new_line(): return PyImGui.new_line()
    
    @staticmethod
    def get_text_line_height() : return PyImGui.get_text_line_height()
    
    @staticmethod
    def get_text_line_height_with_spacing() : return PyImGui.get_text_line_height_with_spacing()
    
    @staticmethod
    def calc_text_size(text : str) : return PyImGui.calc_text_size(text)
    
    @staticmethod
    def invisible_button(label: str, width: float, height: float) : return PyImGui.invisible_button(label, int(width), int(height))

    @staticmethod
    def selectable(label: str, selected: bool, flags: PyImGui.SelectableFlags = PyImGui.SelectableFlags.NoFlag, size: Tuple[float, float] = (0.0, 0.0)) : return PyImGui.selectable(label, selected, flags, (int(size[0]), int(size[1])))
        
    @staticmethod
    def color_edit3(label: str, color: Tuple[float, float, float]) : return PyImGui.color_edit3(label, color)
    
    @staticmethod
    def color_edit4(label: str, color: Tuple[float, float, float, float]): return PyImGui.color_edit4(label, color)

    @staticmethod
    def dummy(width: float, height: float) : return PyImGui.dummy(int(width), int(height))

    @staticmethod
    def _draw_decorator(decorator : TextDecorator, color_int : int | None = None) -> None:
        if decorator is TextDecorator.None_:
            return
        
        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()
        font_size = PyImGui.get_text_line_height()
        height = item_rect_max[1] - item_rect_min[1]
        
        match decorator:
            case TextDecorator.Underline:
                thickness = math.ceil(font_size / 14)
                offset = thickness * 1.5
                
                PyImGui.draw_list_add_rect_filled(
                    item_rect_min[0],
                    item_rect_max[1] - offset,
                    item_rect_max[0],
                    item_rect_max[1] - offset + thickness,
                    color_int if color_int else ImGui.get_style().Text.color_int,
                    0,
                    0,
                )
                
            case TextDecorator.Strikethrough:
                thickness = math.ceil(font_size / 14)
                offset = thickness * 1.5
                
                PyImGui.draw_list_add_rect_filled(
                    item_rect_min[0],
                    item_rect_min[1] + (height / 2) - offset,
                    item_rect_max[0],
                    item_rect_min[1] + (height / 2) - offset + thickness,
                    color_int if color_int else ImGui.get_style().Text.color_int,
                    0,
                    0,
                )
                
            case TextDecorator.Highlight:
                offset = math.ceil(font_size / 14)
                
                PyImGui.draw_list_add_rect_filled(
                    item_rect_min[0] - offset,
                    item_rect_min[1] - offset,
                    item_rect_max[0] + offset,
                    item_rect_max[1] + offset,
                    color_int if color_int else ImGui.get_style().Text.color_int,
                    0,
                    0,
                )
                    
    @staticmethod
    def _with_font(fn, text: str, font_size: int | None = None, font_style: str | None = None) -> None:
        if font_style is None: font_style = "Regular"
        if font_size is not None: ImGui.push_font(font_style, font_size)
        fn(text)
        if font_size is not None: ImGui.pop_font()

    @staticmethod
    def text(text: str, font_size: int | None = None, font_style: str | None = None) -> None:
        ImGui._with_font(PyImGui.text, text, font_size, font_style)

    @staticmethod        
    def text_aligned(
        text: str,
        width: float = 0.0,
        height: float = 0.0,
        alignment: Alignment = Alignment.MidCenter,
        font_size: int | None = None,
        font_style: str | None = None
    ):
        """Draws text aligned inside a given width/height box."""
        width = PyImGui.get_content_region_avail()[0] if width == 0 else width
        
        def _draw(text: str):
            text_w, text_h = PyImGui.calc_text_size(text)
            x, y = PyImGui.get_cursor_pos()

            horiz = alignment.horizontal
            vert = alignment.vertical

            if horiz == HorizontalAlignment.Center:  # center
                x += (width - text_w) * 0.5
                
            elif horiz == HorizontalAlignment.Right:  # right
                x += width - text_w

            if vert == VerticalAlignment.Middle:  # middle
                y += (height - text_h) * 0.5
                
            elif vert == VerticalAlignment.Bottom:  # bottom
                y += height - text_h

            x0, y0 = PyImGui.get_cursor_pos()
            
            PyImGui.set_cursor_pos(x, y)
            PyImGui.text(text)
            _, _, item_rect_size = ImGui.get_item_rect()
            
            #Restore cursor position
            PyImGui.set_cursor_pos(x0, y0)
            ImGui.dummy(*item_rect_size)

        ImGui._with_font(_draw, text, font_size, font_style)
        
    @staticmethod
    def text_centered(text: str, width: float = 0, height: float = 0, font_size: int | None = None, font_style: str | None = None) -> None:
        width = PyImGui.get_content_region_avail()[0] if width == 0 else width
        
        def _centered_text(text: str):
            text_size = PyImGui.calc_text_size(text)
            
            if height > 0:
                cursor_y = (height - text_size[1]) / 2
                PyImGui.set_cursor_pos_y(cursor_y)
                
            if width >= 0:
                cursor_x = (width - text_size[0]) / 2
                PyImGui.set_cursor_pos_x(cursor_x)
            
            PyImGui.text(text)
            
        ImGui._with_font(_centered_text, text, font_size, font_style)        

    @staticmethod
    def text_disabled(text: str, font_size: int | None = None, font_style: str | None = None) -> None:
        ImGui._with_font(PyImGui.text_disabled, text, font_size, font_style)

    @staticmethod
    def text_wrapped(text: str, font_size: int | None = None, font_style: str | None = None) -> None:
        ImGui._with_font(PyImGui.text_wrapped, text, font_size, font_style)

    @staticmethod
    def text_colored(text : str, color: tuple[float, float, float, float], font_size : int | None = None, font_style: str | None = None):
        ImGui._with_font(lambda t: PyImGui.text_colored(t, color), text, font_size, font_style)

    @staticmethod
    def text_decorated(text: str, decorator : TextDecorator = TextDecorator.None_, font_size: int | None = None, font_style: str | None = None, color: tuple[float, float, float, float] | None = None) -> None:
        decorator_color = Color.from_tuple(color) if color else (ImGui.get_style().TextSelectedBg if decorator == TextDecorator.Highlight else ImGui.get_style().Text)
        is_highlight = decorator is TextDecorator.Highlight
                              
        if is_highlight:
            ImGui._with_font(lambda t: PyImGui.text_colored(t, (1,0,0,1)), text, font_size, font_style)
            ImGui._draw_decorator(decorator, decorator_color.color_int)
            item_rect_min = PyImGui.get_item_rect_min()
            PyImGui.set_cursor_screen_pos(item_rect_min[0], item_rect_min[1])
                  
        if color is not None:
            ImGui._with_font(lambda t: PyImGui.text_colored(t, color), text, font_size, font_style)
        else:
            ImGui._with_font(PyImGui.text, text, font_size, font_style)
            
        if decorator is not TextDecorator.Highlight:
            ImGui._draw_decorator(decorator, decorator_color.color_int)
            
    @staticmethod
    def text_unformatted(text : str, font_size : int | None = None, font_style: str | None = None):
        ImGui._with_font(PyImGui.text_unformatted, text, font_size, font_style)
               
    @staticmethod
    def button(label: str, width=0.0, height=0.0, disabled: bool=False, appearance: ControlAppearance=ControlAppearance.Default) -> bool:
        #MATCHING IMGUI SIGNATURES AND USAGE
        enabled = not disabled
        clicked = False

        if disabled: PyImGui.begin_disabled(disabled)
        style = ImGui.get_style()
        
        current_style_var = style.ButtonPadding.get_current()
        btn_padding = (current_style_var.value1, current_style_var.value2 or 0)
        
        if current_style_var.img_style_enum:
            PyImGui.push_style_var2(current_style_var.img_style_enum, btn_padding[0], btn_padding[1]) 

        if style.Theme not in ImGui.Textured_Themes:
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
                    
            if current_style_var.img_style_enum:
                PyImGui.pop_style_var(1)
                
            if disabled: PyImGui.end_disabled()
            
            return clicked
        
        #THEMED

        ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
        clicked = PyImGui.button(label, width, height)
        ImGui.pop_style_color(5)

        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        display_label = label.split("##")[0]

        button_texture_rect = (item_rect_min[0] - 3, item_rect_min[1] - 4, item_rect_size[0] + 9, item_rect_size[1] + 11) if style.Theme is StyleTheme.Guild_Wars else (item_rect_min[0] - 6, item_rect_min[1] - 4, item_rect_size[0] + 12, item_rect_size[1] + 11)
        item_rect = (*item_rect_min, *item_rect_size)
        
        def get_button_color() -> Style.StyleColor:
            match (appearance):
                case ControlAppearance.Primary:
                    return style.PrimaryButtonActive if PyImGui.is_item_active() else style.PrimaryButtonHovered if PyImGui.is_item_hovered() else style.PrimaryButton
                case ControlAppearance.Danger:
                    return style.DangerButtonActive if PyImGui.is_item_active() else style.DangerButtonHovered if PyImGui.is_item_hovered() else style.DangerButton
                case _:
                    return style.ButtonTextureBackgroundActive if PyImGui.is_item_active() else style.ButtonTextureBackgroundHovered if PyImGui.is_item_hovered() else style.ButtonTextureBackground

        tint = get_button_color().rgb_tuple if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple
     
        ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2],
            button_texture_rect[2:],
            tint=tint,
        )
        
        frame_tint = (255, 255, 255, 255) if PyImGui.is_item_hovered() and enabled else (200, 200, 200, 255)
        ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2],
            button_texture_rect[2:],
            tint=frame_tint,
        )
        
        text_size = PyImGui.calc_text_size(display_label)
        text_x = button_texture_rect[0] + ((button_texture_rect[2] - text_size[0]) / 2)
        text_y = item_rect[1] + ((item_rect[3] - text_size[1]) / 2) + 2
    
        PyImGui.push_clip_rect(
            *item_rect_min,
            *item_rect_size,
            True
        )
        
        PyImGui.draw_list_add_text(
            text_x,
            text_y,
            style.TextDisabled.get_current().color_int if disabled else style.Text.get_current().color_int,
            display_label,
        )

        PyImGui.pop_clip_rect()
                
        if current_style_var.img_style_enum:
            PyImGui.pop_style_var(1)
            
        if disabled: PyImGui.end_disabled()
        
        return clicked
             
    @staticmethod
    def small_button(label: str, disabled: bool=False, appearance: ControlAppearance=ControlAppearance.Default) -> bool:
        #MATCHING IMGUI SIGNATURES AND USAGE
        enabled = not disabled
        if disabled: PyImGui.begin_disabled(disabled)
        
        style = ImGui.get_style()
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:
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

            if disabled: PyImGui.end_disabled()
            return clicked

        #THEMED
        ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
        clicked = PyImGui.small_button(label)
        ImGui.pop_style_color(5)

        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        button_texture_rect = (item_rect_min[0] - 3, item_rect_min[1] - 4, item_rect_size[0] + 9, item_rect_size[1] + 11) if style.Theme is StyleTheme.Guild_Wars else (item_rect_min[0] - 6, item_rect_min[1] - 4, item_rect_size[0] + 12, item_rect_size[1] + 11)
        item_rect = (*item_rect_min, *item_rect_size)  
              
        display_label = label.split("##")[0]

        def get_button_color() -> Style.StyleColor:
            match (appearance):
                case ControlAppearance.Primary:
                    return style.PrimaryButtonActive if PyImGui.is_item_active() else style.PrimaryButtonHovered if PyImGui.is_item_hovered() else style.PrimaryButton
                case ControlAppearance.Danger:
                    return style.DangerButtonActive if PyImGui.is_item_active() else style.DangerButtonHovered if PyImGui.is_item_hovered() else style.DangerButton
                case _:
                    return style.ButtonTextureBackgroundActive if PyImGui.is_item_active() else style.ButtonTextureBackgroundHovered if PyImGui.is_item_hovered() else style.ButtonTextureBackground

        tint = get_button_color().rgb_tuple if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple
         
        ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2], 
            button_texture_rect[2:],
            tint=tint,
            mode=TextureSliceMode.THREE_HORIZONTAL
        )
        
        frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_texture_rect) and enabled else (200, 200, 200, 255)
        ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2],
            button_texture_rect[2:],
            tint=frame_tint,
            mode=TextureSliceMode.THREE_HORIZONTAL
        )
        
        font_size = int(PyImGui.get_text_line_height()) - 1
        
        ImGui.push_font("Regular", font_size)
        text_size = PyImGui.calc_text_size(display_label)
        text_x = button_texture_rect[0] + ((button_texture_rect[2] - text_size[0]) / 2)
        text_y = item_rect[1] + ((item_rect[3] - text_size[1]) / 2) + 1
    
        PyImGui.push_clip_rect(
            *item_rect,
            True
        )
        
        PyImGui.draw_list_add_text(
            text_x,
            text_y,
            style.TextDisabled.get_current().color_int if disabled else style.Text.get_current().color_int,
            display_label,
        )
        ImGui.pop_font()

        PyImGui.pop_clip_rect()
                
        if disabled: PyImGui.end_disabled()

        return clicked
    
    @staticmethod
    def icon_button(label: str, width: float=0.0, height: float=0.0, disabled: bool=False, appearance: ControlAppearance=ControlAppearance.Default) -> bool:
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

        #MATCHING IMGUI SIGNATURES AND USAGE
        enabled = not disabled
        
        if disabled: PyImGui.begin_disabled(disabled)
        style = ImGui.get_style()
        current_style_var = style.ButtonPadding.get_current()
        
        if current_style_var.img_style_enum:
            PyImGui.push_style_var2(current_style_var.img_style_enum, current_style_var.value1, current_style_var.value2 or 0) 
            
        clicked = False
    
        default_font_size = int(PyImGui.get_text_line_height())
        fontawesome_font_size = int(default_font_size * 0.8)
        offset_size = round((default_font_size - fontawesome_font_size) / 2)
        
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:
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
            
            style.Text.push_color((0,0,0,0))
            clicked = PyImGui.button(label, width, height)
            style.Text.pop_color()

            for button_color in button_colors:
                button_color.pop_color()

            if current_style_var.img_style_enum:
                PyImGui.pop_style_var(1)
                
            item_rect_min = PyImGui.get_item_rect_min()
            item_rect_max = PyImGui.get_item_rect_max()
                    
            width = item_rect_max[0] - item_rect_min[0] + 2
            height = item_rect_max[1] - item_rect_min[1] + 2

            x,y = item_rect_min
            display_label = label.split("##")[0]

            button_texture_rect = (x, y, width, height)
            
            groups = group_text_with_icons(display_label)
            font_awesome_string = "".join([run for is_icon, run in groups if is_icon])
            text_string = "".join([run for is_icon, run in groups if not is_icon]) 
            text_size = PyImGui.calc_text_size(text_string)
            
            ImGui.push_font("Regular", fontawesome_font_size)
            font_awesome_text_size = PyImGui.calc_text_size(font_awesome_string)
            ImGui.pop_font()
            
            total_text_size = (text_size[0] + font_awesome_text_size[0], max(text_size[1], font_awesome_text_size[1]))

            text_x = button_texture_rect[0] + (button_texture_rect[2] - total_text_size[0]) / 2
            text_y = button_texture_rect[1] + (button_texture_rect[3] - total_text_size[1]) / 2
                
            offset = (0, 0)

            for is_icon, run in groups:
                if is_icon:
                    ImGui.push_font("Regular", fontawesome_font_size)
                else:
                    ImGui.push_font("Regular", default_font_size)
                
                text_size = PyImGui.calc_text_size(run)    
                vertical_padding = 1 if is_icon else offset_size
                                
                PyImGui.draw_list_add_text(
                    text_x + offset[0],
                    text_y + vertical_padding,
                    style.TextDisabled.get_current().color_int if disabled else style.Text.get_current().color_int,
                    run,
                )
                
                offset = (offset[0] + text_size[0], vertical_padding)
                
                ImGui.pop_font()
            
            if disabled:PyImGui.end_disabled()
            return clicked

        ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
        clicked = PyImGui.button(label, width, height)
        ImGui.pop_style_color(5)

        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        button_texture_rect = (item_rect_min[0] - 3, item_rect_min[1] - 4, item_rect_size[0] + 9, item_rect_size[1] + 11) if style.Theme is StyleTheme.Guild_Wars else (item_rect_min[0] - 6, item_rect_min[1] - 4, item_rect_size[0] + 12, item_rect_size[1] + 11)
        item_rect = (*item_rect_min, *item_rect_size)  
              
        display_label = label.split("##")[0]
                
        groups = group_text_with_icons(display_label)
        font_awesome_string = "".join([run for is_icon, run in groups if is_icon])
        text_string = "".join([run for is_icon, run in groups if not is_icon]) 
        text_size = PyImGui.calc_text_size(text_string)        
        
        ImGui.push_font("Regular", fontawesome_font_size)
        font_awesome_text_size = PyImGui.calc_text_size(font_awesome_string)
        ImGui.pop_font()
        
        total_text_size = (text_size[0] + font_awesome_text_size[0], max(text_size[1], font_awesome_text_size[1]))

        text_x = item_rect[0] + 2 + ((item_rect[2] - total_text_size[0]) / 2)
        text_y = item_rect[1] + ((item_rect[3] - total_text_size[1]) / 2)
        
        def get_button_color() -> Style.StyleColor:
            match (appearance):
                case ControlAppearance.Primary:
                    return style.PrimaryButtonActive if PyImGui.is_item_active() else style.PrimaryButtonHovered if PyImGui.is_item_hovered() else style.PrimaryButton
                case ControlAppearance.Danger:
                    return style.DangerButtonActive if PyImGui.is_item_active() else style.DangerButtonHovered if PyImGui.is_item_hovered() else style.DangerButton
                case _:
                    return style.ButtonTextureBackgroundActive if PyImGui.is_item_active() else style.ButtonTextureBackgroundHovered if PyImGui.is_item_hovered() else style.ButtonTextureBackground

        tint = get_button_color().rgb_tuple if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple
              
        ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2], 
            button_texture_rect[2:],
            tint=tint,
        )
        
        frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_texture_rect) and enabled else (200, 200, 200, 255)
        ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2],
            button_texture_rect[2:],
            tint=frame_tint,
        )
        
        PyImGui.push_clip_rect(
            *item_rect,
            True
        )
        
        offset = (0, 0)

        for is_icon, run in groups:
            if is_icon:
                ImGui.push_font("Regular", fontawesome_font_size)
            else:
                ImGui.push_font("Regular", default_font_size)
            
            text_size = PyImGui.calc_text_size(run)                
            vertical_padding = 1 if is_icon else offset_size
                            
            PyImGui.draw_list_add_text(
                text_x + offset[0],
                text_y + vertical_padding,
                style.TextDisabled.get_current().color_int if disabled else style.Text.get_current().color_int,
                run,
            )
            
            offset = (offset[0] + text_size[0], vertical_padding)
            
            ImGui.pop_font()

        PyImGui.pop_clip_rect()

        if current_style_var.img_style_enum:
            PyImGui.pop_style_var(1)
            
        if disabled:PyImGui.end_disabled()
        
        return clicked
    
    @staticmethod
    def toggle_button(label: str, v: bool, width:float =0.0, height:float =0.0, disabled:bool =False) -> bool:
        """
        Purpose: Create a toggle button that changes its state and color based on the current state.
        Args:
            label (str): The label of the button.
            v (bool): The current toggle state (True for on, False for off).
        Returns: bool: The new state of the button after being clicked.
        """
        enabled = not disabled
        clicked = False
        if disabled: PyImGui.begin_disabled(disabled)
        style = ImGui.get_style()
        current_style_var = style.ButtonPadding.get_current()
        btn_padding = (current_style_var.value1, current_style_var.value2 or 0)
        
        if current_style_var.img_style_enum:
            PyImGui.push_style_var2(current_style_var.img_style_enum, btn_padding[0], btn_padding[1]) 
        
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:
            
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
            
            if disabled: PyImGui.end_disabled()

            if clicked:
                v = not v
                
            if current_style_var.img_style_enum:
                PyImGui.pop_style_var(1)
            return v
        
        #THEMED
        ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
        clicked = PyImGui.button(label, width, height)
        ImGui.pop_style_color(5)

        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        button_texture_rect = (item_rect_min[0] - 3, item_rect_min[1] - 4, item_rect_size[0] + 9, item_rect_size[1] + 11) if style.Theme is StyleTheme.Guild_Wars else (item_rect_min[0] - 6, item_rect_min[1] - 4, item_rect_size[0] + 12, item_rect_size[1] + 11)
        item_rect = (*item_rect_min, *item_rect_size)  
              
        display_label = label.split("##")[0]
        
        if not v:
            style.Text.push_color((180, 180, 180, 200))
        
        text_color = style.TextDisabled.get_current().color_int if disabled else style.Text.get_current().color_int
        
        def get_button_color() -> Style.StyleColor:
            if v:
                return style.ToggleButtonEnabledActive if PyImGui.is_item_active() else style.ToggleButtonEnabledHovered if PyImGui.is_item_hovered() else style.ToggleButtonEnabled
            else:
                return style.ToggleButtonDisabledActive if PyImGui.is_item_active() else style.ToggleButtonDisabledHovered if PyImGui.is_item_hovered() else style.ToggleButtonDisabled

        tint = get_button_color().rgb_tuple if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple
                       
        ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2], 
            button_texture_rect[2:],
            tint=tint,
        )
        
        frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_texture_rect) and enabled else (200, 200, 200, 255)
        ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2], 
            button_texture_rect[2:],
            tint=frame_tint,
        )
        
        text_size = PyImGui.calc_text_size(display_label)
        text_x = button_texture_rect[0] + ((button_texture_rect[2] - text_size[0]) / 2)
        text_y = item_rect[1] + ((item_rect[3] - text_size[1]) / 2) + 2
    
        PyImGui.push_clip_rect(
            *item_rect,
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

        if current_style_var.img_style_enum:
            PyImGui.pop_style_var(1)
            
        if disabled:PyImGui.end_disabled()
        
        if clicked:
            v = not v
        
        return v                         
          
    @staticmethod
    def toggle_icon_button(label: str, v : bool, width: float=0.0, height: float=0.0, disabled: bool=False) -> bool:
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

        #MATCHING IMGUI SIGNATURES AND USAGE
        enabled = not disabled
        
        if disabled: PyImGui.begin_disabled(disabled)
        style = ImGui.get_style()
        current_style_var = style.ButtonPadding.get_current()
        if current_style_var.img_style_enum:
            PyImGui.push_style_var2(current_style_var.img_style_enum, current_style_var.value1, current_style_var.value2 or 0)
            
        clicked = False
    
        default_font_size = int(PyImGui.get_text_line_height())
        fontawesome_font_size = int(default_font_size * 0.8)
        offset_size = round((default_font_size - fontawesome_font_size) / 2)
        
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:   
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
                
            style.Text.push_color((0,0,0,0))     
            clicked = PyImGui.button(label, width, height)
            style.Text.pop_color()

            for button_color in button_colors:
                button_color.pop_color()

            if current_style_var.img_style_enum:
                PyImGui.pop_style_var(1)
                
            item_rect_min = PyImGui.get_item_rect_min()
            item_rect_max = PyImGui.get_item_rect_max()
                    
            width = item_rect_max[0] - item_rect_min[0] + 2
            height = item_rect_max[1] - item_rect_min[1] + 2

            x,y = item_rect_min
            display_label = label.split("##")[0]

            button_texture_rect = (x, y, width, height)
            
            groups = group_text_with_icons(display_label)
            font_awesome_string = "".join([run for is_icon, run in groups if is_icon])
            text_string = "".join([run for is_icon, run in groups if not is_icon]) 
            text_size = PyImGui.calc_text_size(text_string)
            
            ImGui.push_font("Regular", fontawesome_font_size)
            font_awesome_text_size = PyImGui.calc_text_size(font_awesome_string)
            ImGui.pop_font()
            
            total_text_size = (text_size[0] + font_awesome_text_size[0], max(text_size[1], font_awesome_text_size[1]))

            text_x = button_texture_rect[0] + ((button_texture_rect[2] - total_text_size[0]) / 2)
            text_y = button_texture_rect[1] + (button_texture_rect[3] - total_text_size[1]) / 2
                
            offset = (0, 0)

            for is_icon, run in groups:
                if is_icon:
                    ImGui.push_font("Regular", fontawesome_font_size)
                else:
                    ImGui.push_font("Regular", default_font_size)
                
                text_size = PyImGui.calc_text_size(run)   
                vertical_padding = 1 if is_icon else offset_size
                                
                PyImGui.draw_list_add_text(
                    text_x + offset[0],
                    text_y + vertical_padding,
                    style.TextDisabled.get_current().color_int if disabled else style.Text.get_current().color_int,
                    run,
                )
                
                offset = (offset[0] + text_size[0], vertical_padding)
                
                ImGui.pop_font()
            
            if disabled:PyImGui.end_disabled()
        
            if clicked:
                v = not v
                
            return v

        ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
        clicked = PyImGui.button(label, width, height)
        ImGui.pop_style_color(5)

        
        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        button_texture_rect = (item_rect_min[0] - 3, item_rect_min[1] - 4, item_rect_size[0] + 9, item_rect_size[1] + 11) if style.Theme is StyleTheme.Guild_Wars else (item_rect_min[0] - 6, item_rect_min[1] - 4, item_rect_size[0] + 12, item_rect_size[1] + 11)
        item_rect = (*item_rect_min, *item_rect_size)  
              
        display_label = label.split("##")[0]
                
        groups = group_text_with_icons(display_label)
        font_awesome_string = "".join([run for is_icon, run in groups if is_icon])
        text_string = "".join([run for is_icon, run in groups if not is_icon]) 
        text_size = PyImGui.calc_text_size(text_string)        
        
        ImGui.push_font("Regular", fontawesome_font_size)
        font_awesome_text_size = PyImGui.calc_text_size(font_awesome_string)
        ImGui.pop_font()
        
        total_text_size = (text_size[0] + font_awesome_text_size[0], max(text_size[1], font_awesome_text_size[1]))

        text_x = item_rect[0] + 2 + ((item_rect[2] - total_text_size[0]) / 2)
        text_y = item_rect[1] + ((item_rect[3] - total_text_size[1]) / 2)
       
        def get_button_color() -> Style.StyleColor:
            if v:
                return style.ToggleButtonEnabledActive if PyImGui.is_item_active() else style.ToggleButtonEnabledHovered if PyImGui.is_item_hovered() else style.ToggleButtonEnabled
            else:
                return style.ToggleButtonDisabledActive if PyImGui.is_item_active() else style.ToggleButtonDisabledHovered if PyImGui.is_item_hovered() else style.ToggleButtonDisabled

        tint = get_button_color().rgb_tuple if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple

        ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2], 
            button_texture_rect[2:],
            tint=tint,
        )
        
        frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_texture_rect) and enabled else (200, 200, 200, 255)
        ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2],
            button_texture_rect[2:],
            tint=frame_tint,
        )
        
        PyImGui.push_clip_rect(
            *item_rect,
            True
        )
        
        offset = (0, 0)

        for is_icon, run in groups:
            if is_icon:
                ImGui.push_font("Regular", fontawesome_font_size)
            else:
                ImGui.push_font("Regular", default_font_size)
            
            text_size = PyImGui.calc_text_size(run)                
            vertical_padding = 1 if is_icon else offset_size
                            
            PyImGui.draw_list_add_text(
                text_x + offset[0],
                text_y + vertical_padding,
                style.TextDisabled.get_current().color_int if disabled else style.Text.get_current().color_int,
                run,
            )
            
            offset = (offset[0] + text_size[0], vertical_padding)
            
            ImGui.pop_font()

        PyImGui.pop_clip_rect()
                
        if current_style_var.img_style_enum:
            PyImGui.pop_style_var(1)
            
        if disabled:PyImGui.end_disabled()
        
        if clicked:
            v = not v
            
        return v
                            
    @staticmethod
    def image(texture_path: str, size: tuple[float, float],
                            uv0: tuple[float, float] = (0.0, 0.0),
                            uv1: tuple[float, float] = (1.0, 1.0),
                            tint: tuple[int, int, int, int] = (255, 255, 255, 255),
                            border_color: tuple[int, int, int, int] = (0, 0, 0, 0)):
        
        return ImGui.DrawTextureExtended(texture_path, size, uv0, uv1, tint, border_color)
                                        
    @staticmethod
    def image_button(label: str, texture_path: str, width: float=32, height: float=32, disabled: bool=False, appearance: ControlAppearance=ControlAppearance.Default) -> bool:
        #MATCHING IMGUI SIGNATURES AND USAGE
        enabled = not disabled
        clicked = False
        
        if disabled: PyImGui.begin_disabled(disabled)
        style = ImGui.get_style()
        
        current_style_var = style.ButtonPadding.get_current()
        btn_padding = (width / 8, height / 8)
        
        if current_style_var.img_style_enum:
            PyImGui.push_style_var2(current_style_var.img_style_enum, btn_padding[0], btn_padding[1])             
        
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:
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
            button_texture_rect = (x, y, width, height)

            texture_pos = (button_texture_rect[0] + btn_padding[0], button_texture_rect[1] + (btn_padding[1] or 0))
            texture_size = (width - (btn_padding[0] * 2), height - ((btn_padding[1] or 0) * 2))
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

            if current_style_var.img_style_enum:
                PyImGui.pop_style_var(1)
                
            if disabled: PyImGui.end_disabled()
            return clicked

        #THEMED
        ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
        clicked = PyImGui.button("##image_button " + label, width, height)
        ImGui.pop_style_color(5)

        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        button_texture_rect = (item_rect_min[0] - 3, item_rect_min[1] - 4, item_rect_size[0] + 9, item_rect_size[1] + 11) if style.Theme is StyleTheme.Guild_Wars else (item_rect_min[0] - 6, item_rect_min[1] - 4, item_rect_size[0] + 12, item_rect_size[1] + 11)
        item_rect = (*item_rect_min, *item_rect_size)
        
        def get_button_color() -> Style.StyleColor:
            match (appearance):
                case ControlAppearance.Primary:
                    return style.PrimaryButtonActive if PyImGui.is_item_active() else style.PrimaryButtonHovered if PyImGui.is_item_hovered() else style.PrimaryButton
                case ControlAppearance.Danger:
                    return style.DangerButtonActive if PyImGui.is_item_active() else style.DangerButtonHovered if PyImGui.is_item_hovered() else style.DangerButton
                case _:
                    return style.ButtonTextureBackgroundActive if PyImGui.is_item_active() else style.ButtonTextureBackgroundHovered if PyImGui.is_item_hovered() else style.ButtonTextureBackground

        tint = get_button_color().rgb_tuple if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple
     
        ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2], 
            button_texture_rect[2:],
            tint=tint,
        )
        
        texture_pos = (item_rect[0] + 2 + btn_padding[0] + 1, item_rect[1] + (btn_padding[1] or 0))
        texture_size = (item_rect_size[0] - (btn_padding[0] * 2), item_rect_size[1] - ((btn_padding[1] or 0) * 2))
        texture_tint = (255, 255, 255, 255) if enabled else (255, 255, 255, 155)
        ImGui.DrawTextureInDrawList(
            texture_pos,
            texture_size,
            texture_path,
            tint=texture_tint
        )
                        
        frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_texture_rect) and enabled else (200, 200, 200, 255)
        ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2],
            button_texture_rect[2:],
            tint=frame_tint,
        )
        PyImGui.push_clip_rect(
            button_texture_rect[0] + 6,
            button_texture_rect[1] + 2,
            width - 12,
            height - 4,
            True
        )
        
        PyImGui.pop_clip_rect()
                

        if current_style_var.img_style_enum:
            PyImGui.pop_style_var(1)
            
        if disabled: PyImGui.end_disabled()
        
        return clicked
    
    @staticmethod
    def image_toggle_button(label: str, texture_path: str, v: bool, width=32.0, height=32.0, disabled:bool=False) -> bool:
        #MATCHING IMGUI SIGNATURES AND USAGE
        enabled = not disabled
        clicked = False
        if disabled: PyImGui.begin_disabled(disabled)
        style = ImGui.get_style()
        
        current_style_var = style.ButtonPadding.get_current()
        btn_padding = (width / 8, height / 8)
        
        if current_style_var.img_style_enum:
            PyImGui.push_style_var2(current_style_var.img_style_enum, btn_padding[0], btn_padding[1])   
            
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:
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
            button_texture_rect = (x, y, width, height)

            texture_pos = (item_rect_min[0] + btn_padding[0], button_texture_rect[1] + (btn_padding[1] or 0))
            texture_size = (width - (btn_padding[0] * 2), height - ((btn_padding[1] or 0) * 2))
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

            if current_style_var.img_style_enum:
                PyImGui.pop_style_var(1)
                
            if disabled: PyImGui.end_disabled()
                
            if clicked:
                v = not v
            
            return v

        #THEMED
        ImGui.push_style_color(PyImGui.ImGuiCol.Button, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
        ImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, (0, 0, 0, 0))                
        clicked = PyImGui.button("##image_toggle_button " + label, width, height)
        ImGui.pop_style_color(5)

        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        button_texture_rect = (item_rect_min[0] - 3, item_rect_min[1] - 4, item_rect_size[0] + 9, item_rect_size[1] + 11) if style.Theme is StyleTheme.Guild_Wars else (item_rect_min[0] - 6, item_rect_min[1] - 4, item_rect_size[0] + 12, item_rect_size[1] + 11)
        item_rect = (*item_rect_min, *item_rect_size)
        
        def get_button_color() -> Style.StyleColor:
            if v:
                return style.ToggleButtonEnabledActive if PyImGui.is_item_active() else style.ToggleButtonEnabledHovered if PyImGui.is_item_hovered() else style.ToggleButtonEnabled
            else:
                return style.ToggleButtonDisabledActive if PyImGui.is_item_active() else style.ToggleButtonDisabledHovered if PyImGui.is_item_hovered() else style.ToggleButtonDisabled

        tint = get_button_color().rgb_tuple if enabled else style.ButtonTextureBackgroundDisabled.get_current().rgb_tuple
     

        ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2],
            button_texture_rect[2:],
            tint=tint,
        )
        

        texture_pos = (item_rect[0] + 2 + btn_padding[0] + 1, item_rect[1] + (btn_padding[1] or 0))
        texture_size = (item_rect_size[0] - (btn_padding[0] * 2), item_rect_size[1] - ((btn_padding[1] or 0) * 2))
        texture_tint = (255, 255, 255, 255) if enabled else (255, 255, 255, 155)
        
        ImGui.DrawTextureInDrawList(
            texture_pos,
            texture_size,
            texture_path,
            tint=texture_tint
        )
                        
        frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_texture_rect) and enabled else (200, 200, 200, 255)
        ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
            button_texture_rect[:2],
            button_texture_rect[2:],
            tint=frame_tint,
        )
        PyImGui.push_clip_rect(
            button_texture_rect[0] + 6,
            button_texture_rect[1] + 2,
            width - 12,
            height - 4,
            True
        )
        

        PyImGui.pop_clip_rect()
                

        if current_style_var.img_style_enum:
            PyImGui.pop_style_var(1)
            
        if disabled:PyImGui.end_disabled()
            
        if clicked:
            v = not v
        
        return v
       
    @staticmethod
    def combo(label: str, current_item: int, items: list[str]) -> int:
        #NON THEMED 
        style = ImGui.get_style()
        if style.Theme not in ImGui.Textured_Themes:
            return PyImGui.combo(label, current_item, items)
        #THEMED

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
        ImGui.pop_style_color(6)

        frame_padding = style.FramePadding.get_current()
        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        display_label = label.split("##")[0]
        label_size = PyImGui.calc_text_size(display_label)

        combo_texture_rect = (item_rect_min[0] - 4, item_rect_min[1] - 6, item_rect_size[0] + 6 - (label_size[0] + frame_padding.value1 if label_size[0] > 0 else 0), item_rect_size[1] + 13)
        item_rect = (*item_rect_min, *item_rect_size)

        text_size = PyImGui.calc_text_size(items[index])
        text_x = item_rect[0] + frame_padding.value1
        text_y = item_rect[1] + ((item_rect[3] - text_size[1]) / 2) + 2

        text_clip_rect = (text_x, text_y, combo_texture_rect[2] - 32 - 6, item_rect[3])
                
        tint = ((style.ComboTextureBackgroundActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.ComboTextureBackgroundHovered.get_current(
        ).rgb_tuple) if PyImGui.is_item_hovered() else style.ComboTextureBackground.get_current().rgb_tuple) if True else (64, 64, 64, 255)
        frame_tint = (255, 255, 255, 255) if PyImGui.is_item_hovered() and True else (200, 200, 200, 255)

                    
        ThemeTextures.Combo_Background.value.get_texture().draw_in_drawlist(
            combo_texture_rect[:2],
            combo_texture_rect[2:],
            tint=tint
        )

        ThemeTextures.Combo_Frame.value.get_texture().draw_in_drawlist(
            combo_texture_rect[:2],
            combo_texture_rect[2:],
            tint=frame_tint
        )
        
        PyImGui.push_clip_rect(
            *text_clip_rect,
            True
        )

        PyImGui.draw_list_add_text(
            text_x,
            text_y,
            style.Text.get_current().color_int,
            items[index],
        )

        PyImGui.pop_clip_rect()

        return index
    
    @staticmethod
    def checkbox(label: str, is_checked: bool, disabled: bool = False) -> bool:
        enabled = not disabled
         #NON THEMED
        style = ImGui.get_style()
        new_value = is_checked
        if disabled : PyImGui.begin_disabled(disabled)
        if style.Theme not in ImGui.Textured_Themes:
            new_value = PyImGui.checkbox(label, is_checked)
            if disabled : PyImGui.end_disabled()
            return new_value
        #THEMED
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
        checkbox_rect = (item_rect_min[0] + padding, item_rect_min[1] + (padding if style.Theme == StyleTheme.Guild_Wars else 2), height, height)
        line_height = PyImGui.get_text_line_height()
        text_rect = (item_rect[0] + checkbox_rect[2] + 2 + style.ItemInnerSpacing.value1, item_rect[1] + (((item_rect_max[1] - item_rect_min[1]) - line_height) / 2), width - checkbox_rect[2] - 4, item_rect[3])

        state = TextureState.Disabled if not enabled else TextureState.Active if PyImGui.is_item_active() else TextureState.Normal

        (ThemeTextures.CheckBox_Checked if is_checked else ThemeTextures.CheckBox_Unchecked).value.get_texture().draw_in_drawlist(
            checkbox_rect[:2],
            checkbox_rect[2:],
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

        if disabled: PyImGui.end_disabled()
        
        return new_value
    
    @staticmethod
    def radio_button(label: str, v: int, button_index: int):
        style = ImGui.get_style()
        value = PyImGui.radio_button(label, v, button_index)
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes or style.Theme == StyleTheme.Minimalus:
            return value
        #THEMED
        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()
        
        width = item_rect_max[0] - item_rect_min[0]
        height = item_rect_max[1] - item_rect_min[1]
        
        item_rect = (item_rect_min[0], item_rect_min[1], width, height)
        active = PyImGui.is_item_active()
        ThemeTextures.CircleButtons.value.get_texture().draw_in_drawlist(
            item_rect[:2],
            item_rect[2:],
            state=TextureState.Active if v == button_index else TextureState.Normal,
            tint= (255, 255, 255, 255) if active else (235, 235, 235, 255) if v == button_index else (180, 180, 180, 255)
        )
        if button_index == v:
            pad = 5
            
            ThemeTextures.Quest_Objective_Bullet_Point.value.get_texture().draw_in_drawlist(
            (item_rect[0] + (height / 4), item_rect[1] + (height / 4)),
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

        return value
    
    @staticmethod
    def input_int(label: str, v: int, min_value: int = 0, step_fast: int = 100_000, flags: int = 0) -> int:
        #NON THEMED
        style = ImGui.get_style()
        if style.Theme not in ImGui.Textured_Themes:
            
            if min_value==0 and step_fast==100_000 and flags==0:
                return PyImGui.input_int(label, v)
            else:
                return PyImGui.input_int(label, v, min_value, step_fast, flags)

        #THEMED
        current_inner_spacing = style.ItemInnerSpacing.get_current()

        if min_value==0 and step_fast==100_000 and flags==0:
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

            # (ThemeTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
            (ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
                item_rect[:2],
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
                (decrease_rect[0] + draw_pad, decrease_rect[1] + draw_pad + 1),
                (button_size - draw_pad*2, button_size - draw_pad*2),
                state=TextureState.Hovered if ImGui.is_mouse_in_rect(decrease_rect) else TextureState.Normal,
                tint=(255, 255, 255, 255),
            )
            ThemeTextures.Expand.value.get_texture().draw_in_drawlist(
                (increase_rect[0] + draw_pad, increase_rect[1] + draw_pad + 1),
                (button_size - draw_pad*2, button_size - draw_pad*2),
                state=TextureState.Hovered if ImGui.is_mouse_in_rect(increase_rect) else TextureState.Normal,
                tint=(255, 255, 255, 255),
            )    
        else:
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
            
            # (ThemeTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
            (ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
                item_rect[:2],
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

        return new_value
    
    @staticmethod
    def input_text(label: str, text: str, flags: int = 0) -> str:
        style = ImGui.get_style()
        if style.Theme not in ImGui.Textured_Themes:
            return PyImGui.input_text(label, text, flags)

        current_inner_spacing = style.ItemInnerSpacing.get_current()

        #THEMED
        new_value = text
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
        
        # (ThemeTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
        (ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
            item_rect[:2],
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

        return new_value
    
    @staticmethod
    def input_float(label: str, v: float) -> float:
        style = ImGui.get_style()
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:
            return PyImGui.input_float(label, v)

        current_inner_spacing = style.ItemInnerSpacing.get_current()
        #THEMED
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
        
        # (ThemeTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
        (ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
            item_rect[:2],
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
        return new_value

    @staticmethod
    def search_field(label: str, text : str, placeholder: str = "Search...", flags : int = PyImGui.InputTextFlags.NoFlag) -> tuple[bool, str]:
        def _functions_tail():
            if not PyImGui.is_item_active() and not PyImGui.is_item_focused() and not text:    
                search_font_size = int(height * 0.25) + 1
                padding = (height - search_font_size) / 2
                                    
                                    
                placeholder_rect = (item_rect[0] + current_frame_padding.value1, item_rect[1], inputfield_size[0] - (current_frame_padding.value1 * 2), inputfield_size[1])
                PyImGui.push_clip_rect(
                    placeholder_rect[0],
                    placeholder_rect[1],
                    placeholder_rect[2],
                    placeholder_rect[3],
                    True,
                )
                
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
                    
                PyImGui.pop_clip_rect()
                    
        #NON THEMED
        style = ImGui.get_style()
        current_frame_padding = style.FramePadding.get_current()
        current_inner_spacing = style.ItemInnerSpacing.get_current()
        if style.Theme not in ImGui.Textured_Themes:
            new_value = PyImGui.input_text(label, text, flags)
                
            item_rect_min = PyImGui.get_item_rect_min()
            item_rect_max = PyImGui.get_item_rect_max()
            
            display_label = label.split("##")[0]
            label_size = PyImGui.calc_text_size(display_label)
            
            width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + 8 if label_size[0] > 0 else 0)
            height = item_rect_max[1] - item_rect_min[1]
            item_rect = (item_rect_min[0], item_rect_min[1], width, height - 4)
            
            label_rect = (item_rect_max[0] - (label_size[0] if label_size[0] > 0 else 0), item_rect_min[1] + ((height - label_size[1]) / 2) + 2, label_size[0], label_size[1])
            inputfield_size = ((label_rect[0] - current_inner_spacing.value1) - item_rect_min[0] , item_rect[3])
        
            
            label_rect = (item_rect_max[0] - (label_size[0] if label_size[0] > 0 else 0), item_rect_min[1] + ((height - label_size[1]) / 2) + 2, label_size[0], label_size[1])
            inputfield_size = ((label_rect[0] - current_inner_spacing.value1) - item_rect_min[0] , item_rect[3])
        
            _functions_tail()
            return new_value != text, new_value
           
        #THEMED     
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

        # (ThemeTextures.Input_Active if PyImGui.is_item_focused() else ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
        (ThemeTextures.Input_Inactive).value.get_texture().draw_in_drawlist(
            item_rect[:2],
            (inputfield_size[0] + 1, inputfield_size[1]),
            tint=(255, 255, 255, 255),
        )
        PyImGui.push_clip_rect(item_rect[0], item_rect[1], item_rect_max[0]- item_rect_min[0], item_rect[3] - 2, True)    
        PyImGui.set_item_allow_overlap()
        PyImGui.set_cursor_screen_pos(x, y)    
        PyImGui.push_item_width(inputfield_size[0])
        new_value = PyImGui.input_text(label, new_value, flags)
        PyImGui.pop_item_width()
        PyImGui.pop_clip_rect()
        ImGui.pop_style_color(6)
        _functions_tail()
                                 
        return new_value != text, new_value
    
    @staticmethod
    def slider_int(label: str, v: int, v_min: int, v_max: int) -> int:
        style = ImGui.get_style()
        if style.Theme not in ImGui.Textured_Themes:
            return PyImGui.slider_int(label, v, v_min, v_max)
        
        current_inner_spacing = style.ItemInnerSpacing.get_current()
          
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
        PyImGui.pop_style_var(1)

        display_label = label.split("##")[0]
        label_size = PyImGui.calc_text_size(display_label)

        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()
        
        width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + current_inner_spacing.value1 if label_size[0] > 0 else 0)
        height = item_rect_max[1] - item_rect_min[1]
        item_rect = (item_rect_min[0], item_rect_min[1], width, height)

        ThemeTextures.SliderBar.value.get_texture().draw_in_drawlist(
            (item_rect[0], item_rect[1] + 4),
            (item_rect[2], item_rect[3] - 8),
            tint=(255, 255, 255, 255),
        )

        percent = (new_value - v_min) / (v_max - v_min)
        track_width = item_rect[2] - 12 - grab_width
        grab_size = (grab_width, grab_width)
        grab_rect = ((item_rect[0] + 6) + track_width * percent, item_rect[1] + (height - grab_size[1]) / 2, *grab_size)

        ThemeTextures.SliderGrab.value.get_texture().draw_in_drawlist(
            grab_rect[:2],
            grab_rect[2:],
        )
        
        if display_label:
            text_x = (item_rect[0] + item_rect[2]) + current_inner_spacing.value1
            text_y = item_rect[1] + ((height - label_size[1] - 2) / 2)

            PyImGui.draw_list_add_text(
                text_x,
                text_y,
                style.Text.color_int,
                display_label,
            )

        return new_value
    
    @staticmethod
    def slider_float(label: str, v: float, v_min: float, v_max: float) -> float:
        style = ImGui.get_style()
        if style.Theme not in ImGui.Textured_Themes:
            return PyImGui.slider_float(label, v, v_min, v_max)
        
        current_inner_spacing = style.ItemInnerSpacing.get_current()
          
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
        PyImGui.pop_style_var(1)

        display_label = label.split("##")[0]
        label_size = PyImGui.calc_text_size(display_label)

        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()
        
        width = item_rect_max[0] - item_rect_min[0] - (label_size[0] + current_inner_spacing.value1 if label_size[0] > 0 else 0)
        height = item_rect_max[1] - item_rect_min[1]
        item_rect = (item_rect_min[0], item_rect_min[1], width, height)

        ThemeTextures.SliderBar.value.get_texture().draw_in_drawlist(
            (item_rect[0], item_rect[1] + 4),
            (item_rect[2], item_rect[3] - 8),
            tint=(255, 255, 255, 255),
        )

        percent = (new_value - v_min) / (v_max - v_min)
        track_width = item_rect[2] - 12 - grab_width
        grab_size = (grab_width, grab_width)
        grab_rect = ((item_rect[0] + 6) + track_width * percent, item_rect[1] + (height - grab_size[1]) / 2, *grab_size)

        ThemeTextures.SliderGrab.value.get_texture().draw_in_drawlist(
            grab_rect[:2],
            grab_rect[2:],
        )
        
        if display_label:
            text_x = (item_rect[0] + item_rect[2]) + current_inner_spacing.value1
            text_y = item_rect[1] + ((height - label_size[1] - 2) / 2)

            PyImGui.draw_list_add_text(
                text_x,
                text_y,
                style.Text.color_int,
                display_label,
            )

        return new_value
    
    @staticmethod
    def separator():
        style = ImGui.get_style()
        if style.Theme not in ImGui.Textured_Themes or style.Theme == StyleTheme.Minimalus:
            PyImGui.separator()
            return

        PyImGui.push_clip_rect(0,0,0,0,False)
        PyImGui.separator()
        PyImGui.pop_clip_rect()

        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()
        
        width = item_rect_max[0] - item_rect_min[0]
        height = item_rect_max[1] - item_rect_min[1]
        item_rect = (item_rect_min[0], item_rect_min[1], width, height)

        ThemeTextures.Separator.value.get_texture().draw_in_drawlist(
            item_rect[:2],
            item_rect[2:]
        )
        
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
    def bullet_text(text: str):
        style = ImGui.get_style()
        if style.Theme not in ImGui.Textured_Themes:
            PyImGui.bullet_text(text)
            return
        frame_padding = style.FramePadding.get_current()

        height = PyImGui.get_text_line_height()
        text_size = PyImGui.calc_text_size(text)
        cursor = PyImGui.get_cursor_screen_pos()

        PyImGui.push_clip_rect(cursor[0] + frame_padding.value1 + height, cursor[1], cursor[0] + frame_padding.value1 + text_size[0], text_size[1], True)
        PyImGui.bullet_text(text)
        PyImGui.pop_clip_rect()

        item_rect_min = PyImGui.get_item_rect_min()
        
        item_rect = (item_rect_min[0] + frame_padding.value1, item_rect_min[1] -2, height, height)
        ThemeTextures.BulletPoint.value.get_texture().draw_in_drawlist(
            item_rect[:2],
            (item_rect[2], item_rect[3]),
        )

    @staticmethod
    def objective_text(text: str, completed: bool = False):
        style = ImGui.get_style()
        frame_padding = style.FramePadding.get_current()
        height = PyImGui.get_text_line_height()
        
        if completed:
            style.TextObjectiveCompleted.get_current().push_color()
        
        def _functions_tail(completed: bool) -> bool:      
            control_rect = (item_rect[0],
                    item_rect[1],
                    item_rect_max[0] - item_rect[0],
                    item_rect_max[1] - item_rect[1])  
            
            style.TextObjectiveCompleted.pop_color()
                
            if PyImGui.is_mouse_clicked(0) and ImGui.is_mouse_in_rect(control_rect):
                completed = not completed
                
            if completed:
                PyImGui.draw_list_add_line(
                    item_rect[0] + item_rect[2] + (frame_padding.value1 * 2) - 5,
                    item_rect[1] + (item_rect[3] / 2) + 1,
                    item_rect_max[0],
                    item_rect[1] + (item_rect[3] / 2) + 1,
                    style.TextObjectiveCompleted.color_int,
                    1,
                )
                                        
                return completed
            return completed
        
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:
            PyImGui.bullet_text(text)            
            item_rect_min = PyImGui.get_item_rect_min()
            item_rect_max = PyImGui.get_item_rect_max()
            item_rect = (item_rect_min[0] + 4, item_rect_min[1] -2, height, height)
            
            return _functions_tail(completed)
        #THEMED
        text_size = PyImGui.calc_text_size(text)
        cursor = PyImGui.get_cursor_screen_pos()

        PyImGui.push_clip_rect(cursor[0] + frame_padding.value1 + height, cursor[1], cursor[0] + frame_padding.value1 + text_size[0], text_size[1], True)
        PyImGui.bullet_text(text)
        PyImGui.pop_clip_rect()
        
        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()
        item_rect = (item_rect_min[0] + 4, item_rect_min[1] -2, height, height)

        texture_rect = (item_rect_min[0] + frame_padding.value1, item_rect_min[1] -2, height, height)
        
        ThemeTextures.Quest_Objective_Bullet_Point.value.get_texture().draw_in_drawlist(
            texture_rect[:2],
            (texture_rect[2], texture_rect[3]),
            state=TextureState.Normal if completed else TextureState.Active,
        )
        
        return _functions_tail(completed)
        
    @staticmethod
    def collapsing_header(label: str, flags: int = 0) -> bool:
        style = ImGui.get_style()
        frame_padding = style.FramePadding.get_current()
        
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:
            new_open = PyImGui.collapsing_header(label, flags)
            return new_open
        
        #THEMED
        ImGui.push_style_color(PyImGui.ImGuiCol.Header, (0,255,0,0))
        ImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, (0,0,0,0))
        ImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, (0,0,0,0))
        ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0,180,255,0))
        
        
        new_open = PyImGui.collapsing_header(label, flags)
        
        ImGui.pop_style_color(4)
        
        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()
        width = item_rect_max[0] - item_rect_min[0]
        height = item_rect_max[1] - item_rect_min[1]
        
        line_height = int(PyImGui.get_text_line_height())
        padding = ((item_rect_max[1] - item_rect_min[1]) - line_height) / 2                
        arrow_rect = (item_rect_min[0] + 2 + frame_padding.value1, item_rect_min[1] + (frame_padding.value2 or 0), line_height, line_height)
        item_rect = (item_rect_min[0] - 2, item_rect_min[1] - 6, width + 4, height + 13)                     
        
        tint = ((style.ComboTextureBackgroundActive.get_current().rgb_tuple if PyImGui.is_item_active() else style.ComboTextureBackgroundHovered.get_current(
        ).rgb_tuple) if ImGui.is_mouse_in_rect(item_rect) else style.ComboTextureBackground.get_current().rgb_tuple) if True else (64, 64, 64, 255)
        
        tint = (tint[0], tint[1], tint[2], 255)

        frame_tint = (255, 255, 255, 255) if ImGui.is_mouse_in_rect(
            item_rect) and True else (200, 200, 200, 255)

        ThemeTextures.CollapsingHeader_Background.value.get_texture().draw_in_drawlist(
            item_rect[:2],
            (item_rect[2], item_rect[3]),
            tint=tint
        )

        ThemeTextures.CollapsingHeader_Frame.value.get_texture().draw_in_drawlist(
            item_rect[:2],
            (item_rect[2], item_rect[3]),
            tint=frame_tint
        )

        
        (ThemeTextures.ArrowExpanded if new_open else ThemeTextures.ArrowCollapsed).value.get_texture().draw_in_drawlist(
            arrow_rect[:2],
            arrow_rect[2:],
            tint=style.Text.get_current().rgb_tuple
        )  
    
        display_label = label.split("##")[0]         
        text_x = (arrow_rect[0] + arrow_rect[2]) + (frame_padding.value1 * 2)
        text_y = item_rect_min[1] + padding

        PyImGui.push_clip_rect(
            item_rect[0],
            item_rect[1],
            width - 5,
            height,
            True
        )

        PyImGui.draw_list_add_text(
            text_x,
            text_y,
            style.Text.get_current().color_int,
            display_label,
        )

        PyImGui.pop_clip_rect()
        
        return new_open

    @staticmethod
    def tree_node(label: str) -> bool:
        style = ImGui.get_style()
        style.TextTreeNode.get_current().push_color()
        
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:
            new_open = PyImGui.tree_node(label)
            style.TextTreeNode.pop_color()
            return new_open
        #THEMED
        frame_padding = style.FramePadding.get_current()
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
            item_rect[:2],
            item_rect[2:],
            state=TextureState.Hovered if ImGui.is_mouse_in_rect(item_rect) else TextureState.Normal,
        )
                                
        style.TextTreeNode.pop_color()  
        return new_open
    
    @staticmethod
    def tree_pop():
        PyImGui.tree_pop()
        
    @staticmethod
    def begin_child(id : str, size : tuple[float, float] = (0, 0), border: bool = False, flags: int = PyImGui.WindowFlags.NoFlag) -> bool:
        return  PyImGui.begin_child(id, size, border, flags)

    @staticmethod
    def end_child(): PyImGui.end_child()
        
    @staticmethod
    def begin_tab_bar(str_id: str) -> bool:
        style = ImGui.get_style()
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:
            return PyImGui.begin_tab_bar(str_id)
        #THEMED
        open = False               
        PyImGui.push_clip_rect(0,0,0,0,False)
        open = PyImGui.begin_tab_bar(str_id)
        PyImGui.pop_clip_rect()

        pos = PyImGui.get_cursor_screen_pos()
        width, height = PyImGui.get_content_region_avail()

        item_rect = (pos[0] - 6, pos[1] - 8, width + 12, height)
        clip_rect = (item_rect[0] - 3, item_rect[1]-2, item_rect[2] + 6, item_rect[3] + 4)
        
        PyImGui.push_clip_rect(*clip_rect, False)
        
        ThemeTextures.Tab_Frame.value.get_texture().draw_in_drawlist(
            item_rect[:2],
            item_rect[2:],
        )
        
        PyImGui.pop_clip_rect()
        return open

    @staticmethod
    def end_tab_bar():
        PyImGui.end_tab_bar()
            
    @staticmethod
    def begin_tab_item(label: str, popen: bool | None = None, flags:int = 0) -> bool:
        style = ImGui.get_style()
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:
            if popen is None:
                return PyImGui.begin_tab_item(label)
            else:
                return PyImGui.begin_tab_item(label, popen, flags)
            
        #THEMED
        open = False
        if popen is None:
            ImGui.push_style_color(PyImGui.ImGuiCol.Tab, (0, 0, 0, 0))
            ImGui.push_style_color(PyImGui.ImGuiCol.TabActive, (0, 0, 0, 0))
            ImGui.push_style_color(PyImGui.ImGuiCol.TabHovered, (0, 0, 0, 0))
            ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
            open = PyImGui.begin_tab_item(label)
            ImGui.pop_style_color(4)            
            
        else:
            ImGui.push_style_color(PyImGui.ImGuiCol.Tab, (0, 0, 0, 0))
            ImGui.push_style_color(PyImGui.ImGuiCol.TabActive, (0, 0, 0, 0))
            ImGui.push_style_color(PyImGui.ImGuiCol.TabHovered, (0, 0, 0, 0))
            ImGui.push_style_color(PyImGui.ImGuiCol.Text, (0, 0, 0, 0))
            
            open = PyImGui.begin_tab_item(label, popen, flags)

            ImGui.pop_style_color(4)
        

        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        tab_texture_rect = (item_rect_min[0] - 5, item_rect_min[1], item_rect_size[0] + 10, item_rect_size[1] - 1)
        item_rect = (*item_rect_min, *item_rect_size)
        
        PyImGui.push_clip_rect(
            *tab_texture_rect,
            True
        )
        
        (ThemeTextures.Tab_Active if open else ThemeTextures.Tab_Inactive).value.get_texture().draw_in_drawlist(
            tab_texture_rect[:2],
            tab_texture_rect[2:],
        )
        
        PyImGui.pop_clip_rect()

        display_label = ImGui.trim_text_to_width(label.split("##")[0], item_rect_size[0] - 2)        
        final_size = PyImGui.calc_text_size(display_label)
        final_w, final_h = final_size

        text_x = item_rect[0] + (item_rect[2] - final_w) / 2
        text_y = item_rect[1] + (item_rect[3] - final_h + (5 if open else 7)) / 2
        text_rect = (text_x, text_y, item_rect_size[0], item_rect_size[1])

        PyImGui.push_clip_rect(
            *text_rect,
            True
        )

        PyImGui.draw_list_add_text(
            text_x,
            text_y,
            style.Text.color_int,
            display_label,
        )

        PyImGui.pop_clip_rect()  
                    
        return open
    
    @staticmethod
    def end_tab_item(): PyImGui.end_tab_item()
    
    @staticmethod
    def draw_vertical_scroll_bar(scroll_bar_size : float, force_scroll_bar : bool = False, window_rect: Optional[tuple[float, float, float, float]] = None, border_padding: bool = False):
        import math
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
                
            ThemeTextures.Scroll_Bg.value.get_texture().draw_in_drawlist(
                (scroll_bar_rect[0], scroll_bar_rect[1] + 5),
                (scroll_bar_rect[2] - scroll_bar_rect[0], scroll_bar_rect[3] - scroll_bar_rect[1] - 10),
            )

            ThemeTextures.ScrollGrab_Top.value.get_texture().draw_in_drawlist(
                (scroll_grab_rect[0], scroll_grab_rect[1]), 
                (scroll_bar_size, 7),
            )
            
            ThemeTextures.ScrollGrab_Bottom.value.get_texture().draw_in_drawlist(
                (scroll_grab_rect[0], scroll_grab_rect[3] - 7), 
                (scroll_bar_size, 7),
            )

            px_height = 2
            mid_height = scroll_grab_rect[3] - scroll_grab_rect[1] - 10
            for i in range(math.ceil(mid_height / px_height)):
                ThemeTextures.ScrollGrab_Middle.value.get_texture().draw_in_drawlist(
                    (scroll_grab_rect[0], scroll_grab_rect[1] + 5 + (px_height * i)), 
                    (scroll_bar_size, px_height),
                tint=(195, 195, 195, 255)
                )
            
            ThemeTextures.UpButton.value.get_texture().draw_in_drawlist(
                (scroll_bar_rect[0] - 1, scroll_bar_rect[1] - 5),
                (scroll_bar_size, scroll_bar_size),
            )

            ThemeTextures.DownButton.value.get_texture().draw_in_drawlist(
                (scroll_bar_rect[0] - 1, scroll_bar_rect[3] - (scroll_bar_size - 5)),
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
            
                
            ThemeTextures.Horizontal_Scroll_Bg.value.get_texture().draw_in_drawlist(
                (scroll_bar_rect[0] + 3, scroll_bar_rect[1]),
                (scroll_bar_rect[2] - scroll_bar_rect[0] - 5, scroll_bar_rect[3] - scroll_bar_rect[1]),
            )
                    
            ThemeTextures.Horizontal_ScrollGrab_Middle.value.get_texture().draw_in_drawlist(
                (scroll_grab_rect[0] + 5, scroll_grab_rect[1]),
                (scroll_grab_rect[2] - 10, scroll_grab_rect[3]),
                tint=(195, 195, 195, 255)
            )
            
            ThemeTextures.Horizontal_ScrollGrab_Top.value.get_texture().draw_in_drawlist(
                (scroll_grab_rect[0], scroll_grab_rect[1]),
                (7, scroll_grab_rect[3]),
            )
            
            ThemeTextures.Horizontal_ScrollGrab_Bottom.value.get_texture().draw_in_drawlist(
                (scroll_grab_rect[0] + scroll_grab_rect[2] - 7, scroll_grab_rect[1]),
                (7, scroll_grab_rect[3]),
            )

            
            ThemeTextures.LeftButton.value.get_texture().draw_in_drawlist(
                (scroll_bar_rect[0] - 5, scroll_bar_rect[1] - 1),
                (scroll_bar_size, scroll_bar_size + 1),
            )
            
            ThemeTextures.RightButton.value.get_texture().draw_in_drawlist(
                (scroll_bar_rect[2] - 5 + (0 if scroll_max_y > 0 else 1), scroll_bar_rect[1] - 1),
                (scroll_bar_size, scroll_bar_size + 1),
            )

            PyImGui.pop_clip_rect()
            
    @staticmethod
    def begin_table(id: str, columns: int, flags: int = PyImGui.TableFlags.NoFlag, width: float = 0, height: float = 0) -> bool:
        return PyImGui.begin_table(id, columns, flags, width, height)

    @staticmethod
    def end_table(): PyImGui.end_table()
    
    @staticmethod
    def progress_bar(fraction: float, size_arg_x: float, size_arg_y: float, overlay: str = ""):
        style = ImGui.get_style()
        #NON THEMED
        if style.Theme not in ImGui.Textured_Themes:            
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
            return
        #THEMED
        PyImGui.push_clip_rect(0,0,0,0,False)
        PyImGui.progress_bar(fraction, size_arg_x, size_arg_y, overlay)
        PyImGui.pop_clip_rect()
        
        item_rect_min, item_rect_max, item_rect_size = ImGui.get_item_rect()
        
        
        width = item_rect_max[0] - item_rect_min[0]
        height = item_rect_max[1] - item_rect_min[1]
        item_rect = (*item_rect_min, *item_rect_size)

        progress_rect = (item_rect[0] + 1, item_rect[1] + 1, (width -2) * fraction, height - 2)
        background_rect = (item_rect[0] + (width -2) * fraction - 3, item_rect[1] + 1, width - ((width -2) * fraction + 7) + 6, height - 2)
        cursor_rect = (
            item_rect[0] - 1 + (width - 2) * fraction,
            item_rect[1] + 1,  
            1, 
            height - 2)

        tint = style.PlotHistogram.get_current().rgb_tuple
        
        ThemeTextures.ProgressBarBackground.value.get_texture().draw_in_drawlist(
            background_rect[:2],
            background_rect[2:],
            tint=tint
        )
        
        ThemeTextures.ProgressBarProgressFill.value.get_texture().draw_in_drawlist(
            progress_rect[:2],
            progress_rect[2:],
            tint=tint
        )
        
        if fraction > 0:
            ThemeTextures.ProgressBarProgressCursor.value.get_texture().draw_in_drawlist(
                cursor_rect[:2],
                cursor_rect[2:],
                tint=(200, 200, 200, 255)
            )
        
        ThemeTextures.ProgressBarFrame.value.get_texture().draw_in_drawlist(
            item_rect[:2],
            item_rect[2:], 
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

    
    #region wrappers
            
    @staticmethod
    def text_scaled(text : str, color: tuple[float, float, float, float], scale: float):
        PyImGui.text_scaled(text, color, scale)

    @staticmethod
    def begin_popup(id: str, flags: PyImGui.WindowFlags = PyImGui.WindowFlags.NoFlag) -> bool:     

        open = PyImGui.begin_popup(id, PyImGui.WindowFlags(flags))
        
        return open

    @staticmethod
    def end_popup():
        PyImGui.end_popup()

    @staticmethod
    def begin_tooltip() -> bool:
        open = PyImGui.begin_tooltip()        
        return open

    @staticmethod
    def end_tooltip():
        PyImGui.end_tooltip()

    @staticmethod
    def begin_combo(label: str, preview_value: str, flags: PyImGui.ImGuiComboFlags = PyImGui.ImGuiComboFlags.NoFlag):
        open = PyImGui.begin_combo(label, preview_value, flags)

        return open

    @staticmethod
    def end_combo():
        PyImGui.end_combo()
        
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

        opened = PyImGui.begin_popup_modal(name, p_open, flags)

        return opened

    @staticmethod
    def end_popup_modal():
        PyImGui.end_popup_modal()

    @staticmethod
    def tree_node_ex(label: str, flags: int, fmt: str) -> bool:
        opened = PyImGui.tree_node_ex(label, flags, fmt)

        return opened



    #region Custom
    @staticmethod
    def DrawTexture(texture_path: str, width: float = 32.0, height: float = 32.0):
         ImGui.overlay_instance.DrawTexture(texture_path, width, height)
        
    @staticmethod
    def DrawTextureExtended(texture_path: str, size: tuple[float, float],
                            uv0: tuple[float, float] = (0.0, 0.0),
                            uv1: tuple[float, float] = (1.0, 1.0),
                            tint: tuple[int, int, int, int] = (255, 255, 255, 255),
                            border_color: tuple[int, int, int, int] = (0, 0, 0, 0)):
         ImGui.overlay_instance.DrawTextureExtended(texture_path, size, uv0, uv1, tint, border_color)
     
    @staticmethod   
    def DrawTexturedRect(x: float, y: float, width: float, height: float, texture_path: str):
         ImGui.overlay_instance.BeginDraw()
         ImGui.overlay_instance.DrawTexturedRect(x, y, width, height, texture_path)
         ImGui.overlay_instance.EndDraw()
        
    @staticmethod
    def DrawTexturedRectExtended(pos: tuple[float, float], size: tuple[float, float], texture_path: str,
                                    uv0: tuple[float, float] = (0.0, 0.0),  
                                    uv1: tuple[float, float] = (1.0, 1.0),
                                    tint: tuple[int, int, int, int] = (255, 255, 255, 255)):
         ImGui.overlay_instance.BeginDraw()
         ImGui.overlay_instance.DrawTexturedRectExtended(pos, size, texture_path, uv0, uv1, tint)
         ImGui.overlay_instance.EndDraw()
        
    @staticmethod
    def ImageButton(caption: str, texture_path: str, width: float = 32.0, height: float = 32.0, disabled: bool = False, appearance: ControlAppearance = ControlAppearance.Default) -> bool:
        if disabled: 
            PyImGui.begin_disabled(disabled)
            
        result = ImGui.overlay_instance.ImageButton(caption, texture_path, width, height, frame_padding=-1)
        if PyImGui.is_item_hovered():
            ImGui.show_tooltip(caption)
            

        if disabled:
            PyImGui.end_disabled()
            
        return result
    
        #return ImGui.image_button(caption, texture_path, width, height, disabled, appearance)

    @staticmethod
    def ImageButtonExtended(caption: str, texture_path: str, size: tuple[float, float],
                            uv0: tuple[float, float] = (0.0, 0.0),
                            uv1: tuple[float, float] = (1.0, 1.0),
                            bg_color: tuple[int, int, int, int] = (0, 0, 0, 0),
                            tint_color: tuple[int, int, int, int] = (255, 255, 255, 255),
                            frame_padding: int = -1) -> bool:
        return  ImGui.overlay_instance.ImageButtonExtended(caption, texture_path, size, uv0, uv1, bg_color, tint_color, frame_padding)
    
    @staticmethod
    def DrawTextureInForegound(pos: tuple[float, float], size: tuple[float, float], texture_path: str,
                       uv0: tuple[float, float] = (0.0, 0.0),
                       uv1: tuple[float, float] = (1.0, 1.0),
                       tint: tuple[int, int, int, int] = (255, 255, 255, 255)):
         ImGui.overlay_instance.DrawTextureInForegound(pos, size, texture_path, uv0, uv1, tint)
      
    @staticmethod  
    def DrawTextureInDrawList(pos: tuple[float, float], size: tuple[float, float], texture_path: str,
                       uv0: tuple[float, float] = (0.0, 0.0),
                       uv1: tuple[float, float] = (1.0, 1.0),
                       tint: tuple[int, int, int, int] = (255, 255, 255, 255)):
         ImGui.overlay_instance.DrawTextureInDrawList(pos, size, texture_path, uv0, uv1, tint)
    
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

        PyImGui.push_style_var2(ImGuiStyleVar.WindowPadding, -1, -0)
        PyImGui.push_style_var(ImGuiStyleVar.WindowRounding,0.0)
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

        PyImGui.push_style_var2(ImGuiStyleVar.WindowPadding, -1, -0)
        PyImGui.push_style_var(ImGuiStyleVar.WindowRounding, 0.0)

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
        
        PyImGui.push_style_var2(ImGuiStyleVar.WindowPadding,0.0,0.0)
        PyImGui.push_style_var(ImGuiStyleVar.WindowRounding,0.0)
        PyImGui.push_style_var2(ImGuiStyleVar.FramePadding, 3, 5)
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
    
    @staticmethod
    def render_wrapped_bullet(text: str, max_width: float = 400.0):
            """
            Custom bullet renderer that allows wrapped text.
            The bullet is rendered in the left column; text wraps in the right column.
            """
            bullet_col_width = PyImGui.get_text_line_height()
            text_col_width = max_width - bullet_col_width

            if PyImGui.begin_table("bullet_table", 2, PyImGui.TableFlags.NoBordersInBody):
                PyImGui.table_setup_column("bullet", PyImGui.TableColumnFlags.WidthFixed, bullet_col_width)
                PyImGui.table_setup_column("text", PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.bullet_text("")  # draw bullet using ImGui's bullet
                PyImGui.table_set_column_index(1)

                PyImGui.push_text_wrap_pos(PyImGui.get_cursor_pos_x() + text_col_width)
                PyImGui.text_wrapped(text)
                PyImGui.pop_text_wrap_pos()

                PyImGui.end_table()
            
    @staticmethod
    def render_tokenized_markup(tokenized_lines: list[list[dict]], max_width: float, COLOR_MAP: dict[str, tuple[float, float, float, float]]):
        """
        Render pre-tokenized Guild Wars markup lines produced by the tokenizer.
        Each element in tokenized_lines is a list of token dicts for a single line.
        """
        style = PyImGui.StyleConfig()
        style.Pull()
        _orig_cell = style.CellPadding
        _orig_item = style.ItemSpacing
        style.CellPadding = (_orig_cell[0], 0.0)   # vertical padding inside table rows
        style.ItemSpacing = (_orig_item[0], 0.0)   # spacing between stacked rows
        style.Push()
        
        color_stack, inside_bullet, gray_bullet = [], False, False
        for tokens in tokenized_lines:  # iterate through lines
            for token in tokens:
                t = token["type"]
                v = token.get("value")
                v = v.strip() if isinstance(v, str) else v
                if not v:
                    v = ""
                if t == "text":
                    if inside_bullet:
                        PyImGui.push_style_color(
                            PyImGui.ImGuiCol.Text,
                            (0.6, 0.6, 0.6, 1.0) if gray_bullet else (1.0, 1.0, 1.0, 1.0),
                        )
                        ImGui.render_wrapped_bullet(v, max_width=max_width)
                        PyImGui.pop_style_color(1)
                        inside_bullet = False
                        gray_bullet = False
                    elif color_stack:
                        current_color = color_stack[-1]
                        color = COLOR_MAP.get(current_color, (1, 1, 1, 1))
                        PyImGui.text_colored(v, color)
                        PyImGui.same_line(0, 2)
                    else:
                        PyImGui.text(v)
                        PyImGui.same_line(0, 2)

                elif t == "color_start":
                    color_stack.append(v)
                elif t == "color_end" and color_stack:
                    color_stack.pop()
                elif t in ("paragraph", "line_break"):
                    PyImGui.new_line()
                elif t == "bullet":
                    inside_bullet = True
                    gray_bullet = token.get("gray", False)

            PyImGui.new_line()
        style.CellPadding = _orig_cell
        style.ItemSpacing = _orig_item
        style.Push()

    @staticmethod     
    def PushTransparentWindow():
        PyImGui.push_style_var(ImGuiStyleVar.WindowRounding,0.0)
        PyImGui.push_style_var(ImGuiStyleVar.WindowPadding,0.0)
        PyImGui.push_style_var(ImGuiStyleVar.WindowBorderSize,0.0)
        PyImGui.push_style_var2(ImGuiStyleVar.WindowPadding,0.0,0.0)
        
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


        
    #region gw_window
    class gw_window():
        _state = {}
        
        projects_path = Py4GW.Console.get_projects_path()
        
        TEXTURE_FOLDER = projects_path + "\\Textures\\Game UI\\"
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
                
        
            PyImGui.push_style_var2(ImGuiStyleVar.WindowPadding, 0, 0)
            
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
            PyImGui.push_style_var(ImGuiStyleVar.ChildRounding, 6.0)

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
            
