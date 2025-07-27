import os
import Py4GW
import PyImGui
from enum import Enum, IntEnum

from PyOverlay import Point2D
from .Overlay import Overlay
from Py4GWCoreLib.Py4GWcorelib import Color, ColorPalette, ConsoleLog, ThrottledTimer
from Py4GWCoreLib.enums import get_texture_for_model, ImguiFonts
from Py4GWCoreLib import Utils

from enum import IntEnum

class SortDirection(Enum):
    No_Sort = 0
    Ascending = 1
    Descending = 2


from enum import IntEnum


TEXTURE_FOLDER = "Textures\\Game UI\\"

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

    def draw_in_drawlist(self, x: float, y: float, size: tuple[float, float], tint=(255, 255, 255, 255)):
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

class GameTextures(Enum):    
    Empty_Pixel = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "empty_pixel.png"),
        texture_size = (1, 1),
        size = (1, 1),
        normal=(0, 0)
    )
    
    Down_Arrows = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_up_down_arrow_atlas.png"),
        texture_size = (128, 64),
        size = (32, 32),
        normal=(0, 0),
        hovered=(32, 0),
        active=(64, 0),
        disabled=(96, 0),
    )
    
    Up_Arrows = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_up_down_arrow_atlas.png"),
        texture_size = (128, 64),
        size = (32, 32),
        normal=(0, 32),
        hovered=(32, 32),
        active=(64, 32),
        disabled=(96, 32),
    )
    
    Close_Button = MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_close_button_atlas.png"),
        texture_size = (64, 16),
        size = (12, 12),
        normal=(1, 1),
        hovered=(17, 1),
        active=(33, 1),
    )
    
    Title_Bar = SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_title_frame_atlas.png"),
        texture_size=(128, 32),
        left=(0, 6, 18, 32),
        mid=(19, 6, 109, 32),
        right=(110, 6, 128, 32)
    )

    Window_Frame_Top = SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 0, 18, 40),
        right=(110, 0, 128, 40),
        mid=(19, 0, 109, 40)
    )
    
    Window_Frame_Center = SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 40, 18, 68),
        mid=(19, 40, 109, 68),
        right=(110, 40, 128, 68),
    )
    
    Window_Frame_Bottom = SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 68, 18, 128),
        mid=(19, 68, 77, 128),
        right=(78, 68, 128, 128),
    )
    
    Window_Frame_Bottom_No_Resize = SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas_no_resize.png"),
        texture_size=(128, 128),
        left=(0, 68, 18, 128),
        mid=(19, 68, 77, 128),
        right=(78, 68, 128, 128),
    )
   
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
        
    class StyleTheme(IntEnum):
        ImGui = 0
        Guild_Wars = 1
        Minimalus = 2
        
    Theme : StyleTheme = StyleTheme.Guild_Wars
    
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
        _windows : dict[str, 'ImGui.WindowModule'] = {}
        
        def __init__(self, module_name="", window_name="", window_size=(100,100), window_pos=(0,0), window_flags=PyImGui.WindowFlags.NoFlag, collapse= False, can_close=False, forced_theme : "ImGui.StyleTheme | None" = None):
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
            
            self.theme : ImGui.StyleTheme | None = forced_theme
            self.__current_theme = self.theme if self.theme is not None else ImGui.Theme # Internal use only
            
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

        def begin(self) -> bool:
            if not self.module_name:
                return False
                        
            self.__current_theme = self.get_theme()
            ImGui.push_style(self.__current_theme)                            
        
            is_expanded = self.expanded
            is_first_run = self.first_run
            
            self.can_resize = (int(self.window_flags) & int(PyImGui.WindowFlags.NoResize)) == 0 and (int(self.window_flags) & int(PyImGui.WindowFlags.AlwaysAutoResize)) == 0
            
            if self.first_run:
                self.initialize()
                
            match (self.__current_theme):
                case ImGui.StyleTheme.Guild_Wars:
                    has_always_auto_resize = (int(self.window_flags) & int(PyImGui.WindowFlags.AlwaysAutoResize)) != 0
                    
                    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 10, 10)
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
                        
                    PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 0, 0, 0.85))
                        
                    if not is_expanded:
                        # Remove PyImGui.WindowFlags.MenuBar and PyImGui.WindowFlags.AlwaysAutoResize from internal_flags when not expanded
                        internal_flags &= ~int(PyImGui.WindowFlags.MenuBar)
                        internal_flags &= ~int(PyImGui.WindowFlags.AlwaysAutoResize)
                        internal_flags |= int(PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse| PyImGui.WindowFlags.NoResize| PyImGui.WindowFlags.NoMouseInputs)
                        
                    _, open = PyImGui.begin_with_close(name = self.window_name, p_open=self.open, flags=internal_flags)

                    PyImGui.pop_style_color(1)
                                            
                    self.open = open               
                                    
                    if self.__set_focus and not self.__dragging and not self.__drag_started:
                        PyImGui.set_window_focus(self.window_name)
                        self.__set_focus = False
                    
                    if self.__dragging:
                        PyImGui.set_window_focus(self.window_name)
                        PyImGui.set_window_focus(f"{self.window_name}##titlebar_fake")
                        
                    self.__draw_decorations() 
                    
                    PyImGui.pop_style_var(1)
                    
                    if has_always_auto_resize:                    
                        cursor = PyImGui.get_cursor_pos()
                        PyImGui.dummy(int(self.window_name_size[0] + 20), 0)
                        PyImGui.set_cursor_pos(cursor[0], cursor[1])
                                    
                case ImGui.StyleTheme.ImGui | ImGui.StyleTheme.Minimalus:  
                    if self.can_close:              
                        self.expanded, self.open = PyImGui.begin_with_close(name = self.window_name, p_open=self.open, flags=self.window_flags)
                    else:
                        self.open = PyImGui.begin(self.window_name, self.open, self.window_flags) 
                        self.expanded = PyImGui.is_window_collapsed() == False   
            
            if is_expanded and self.expanded and self.open:
                self.window_size = PyImGui.get_window_size()
            
            return self.open
        
        def process_window(self):
            if not self.module_name:
                return
            
            self.collapsed_status = PyImGui.is_window_collapsed()
            self.end_pos = PyImGui.get_window_pos()

        def end(self):
            if not self.module_name:
                return
            
            ImGui.pop_style(self.__current_theme)
            
            match (self.__current_theme):
                case ImGui.StyleTheme.Guild_Wars:      
                    PyImGui.end()

                case ImGui.StyleTheme.ImGui | ImGui.StyleTheme.Minimalus:
                    PyImGui.end()

            
            """ INI FILE ROUTINES NEED WORK 
            if end_pos[0] != window_module.window_pos[0] or end_pos[1] != window_module.window_pos[1]:
                ini_handler.write_key(module_name + " Config", "config_x", str(int(end_pos[0])))
                ini_handler.write_key(module_name + " Config", "config_y", str(int(end_pos[1])))

            if new_collapsed != window_module.collapse:
                ini_handler.write_key(module_name + " Config", "collapsed", str(new_collapsed))
            """
        
        def get_theme(self) -> "ImGui.StyleTheme":
            """
            Returns the current theme of the ImGui module.
            """

            theme = self.theme if self.theme else ImGui.Theme

            return theme
             
        def __draw_decorations(self):  
            if self.expanded and self.open:
                window_pos = PyImGui.get_window_pos()
                window_size = PyImGui.get_window_size()            
                                                    
                self.__decorators_left = window_pos[0] - 15
                self.__decorators_top = window_pos[1] - (26)
                
                self.__decorators_right = self.__decorators_left + window_size[0] + 30
                self.__decorators_bottom = self.__decorators_top + window_size[1] + 14 + (26)
                
                self.__decorators_width = self.__decorators_right - self.__decorators_left
                self.__decorators_height = self.__decorators_bottom - self.__decorators_top
                self.__close_button_rect = (self.__decorators_right - 29, self.__decorators_top + 9, 11, 11)
                

                PyImGui.push_clip_rect(self.__decorators_left, self.__decorators_top, self.__decorators_width, self.__decorators_height, False)   
                state = TextureState.Normal
                                
                if ImGui.is_mouse_in_rect(self.__close_button_rect):
                    if PyImGui.is_mouse_down(0):
                        state = TextureState.Active
                        open = False
                    else:
                        state = TextureState.Hovered
                                        
                GameTextures.Empty_Pixel.value.draw_in_drawlist(
                    x=self.__decorators_left + 15,
                    y=self.__decorators_top + 15,
                    size=(self.__decorators_width - 30, self.__decorators_height - 15 - 10),
                    tint=(0,0,0,215)
                )

                if self.can_resize:
                    GameTextures.Window_Frame_Bottom.value.draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_bottom - 57,
                        size=(self.__decorators_width - 10, 60)
                    )
                else:
                    GameTextures.Window_Frame_Bottom_No_Resize.value.draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_bottom - 57,
                        size=(self.__decorators_width - 10, 60)
                    )
                
                GameTextures.Window_Frame_Center.value.draw_in_drawlist(
                    x=self.__decorators_left + 5,
                    y=self.__decorators_top + 26 + 35,
                    size=(self.__decorators_width - 10, self.__decorators_height - 35 - 60)
                )
                
                GameTextures.Window_Frame_Top.value.draw_in_drawlist(
                    x=self.__decorators_left + 5,
                    y=self.__decorators_top + 26,
                    size=(self.__decorators_width - 10, 35)
                )
                                                    
                GameTextures.Title_Bar.value.draw_in_drawlist(
                    x=self.__decorators_left + 5,
                    y=self.__decorators_top,
                    size=(self.__decorators_width - 10, 26)
                )
                
                if self.can_close:
                    GameTextures.Empty_Pixel.value.draw_in_drawlist(
                        x=self.__close_button_rect[0] - 1,
                        y=self.__close_button_rect[1] - 1,
                        size=(self.__close_button_rect[2] + 2, self.__close_button_rect[3] + 2),
                        tint=(0,0,0,255)
                    )
                
                    GameTextures.Close_Button.value.draw_in_drawlist(
                        x=self.__close_button_rect[0],
                        y=self.__close_button_rect[1],
                        size=self.__close_button_rect[2:],
                        state=state
                    )
                        
                self.__title_bar_rect = (self.__decorators_left + 10, self.__decorators_top + 2, self.__decorators_width - 10, 26)
                
                # Draw the title text
                PyImGui.draw_list_add_text(self.__title_bar_rect[0] + 15, self.__title_bar_rect[1] + 7, Utils.RGBToColor(255,255,255,255), self.window_display_name)
                self.__draw_title_bar_fake(self.__title_bar_rect)
                            
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
                GameTextures.Empty_Pixel.value.draw_in_drawlist(
                    x=self.__decorators_left + 15,
                    y=self.__decorators_top + 15,
                    size=(self.__decorators_width - 30, 14),
                    tint=(0,0,0,215)
                )
                
                # PyImGui.push_clip_rect(self.__decorators_left, self.__decorators_top, self.__decorators_width - 15, self.__decorators_height + 30, False)   
                GameTextures.Window_Frame_Bottom_No_Resize.value.draw_in_drawlist(
                    x=self.__decorators_left + 2,
                    y=self.__decorators_top - 12 + 8,
                    size=(self.__decorators_width - 5 , 40)
                )

                PyImGui.push_clip_rect(self.__decorators_left, self.__decorators_top, self.__decorators_width, self.__decorators_height + 30, False)

                GameTextures.Title_Bar.value.draw_in_drawlist(
                    x=self.__decorators_left + 5,
                    y=self.__decorators_top,
                    size=(self.__decorators_width - 10, 26)
                )

                if self.can_close:
                    GameTextures.Empty_Pixel.value.draw_in_drawlist(
                        x=self.__close_button_rect[0] - 1,
                        y=self.__close_button_rect[1] - 1,
                        size=(self.__close_button_rect[2] + 2, self.__close_button_rect[3] + 2),
                        tint=(0,0,0,255)
                    )
                    
                    GameTextures.Close_Button.value.draw_in_drawlist(
                        x=self.__close_button_rect[0],
                        y=self.__close_button_rect[1],
                        size=(self.__close_button_rect[2:]),
                        state=state
                    )

                self.__title_bar_rect = (self.__decorators_left + 10, self.__decorators_top + 2, self.__decorators_width - 10, 26)
                PyImGui.draw_list_add_text(self.__title_bar_rect[0] + 15, self.__title_bar_rect[1] + 7, Utils.RGBToColor(255,255,255,255), self.window_display_name)
                self.__draw_title_bar_fake(self.__title_bar_rect)

            PyImGui.pop_clip_rect()
            
        def __draw_title_bar_fake(self, __title_bar_rect):            
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
            PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 1, 0, 0.0))  # Fully transparent
            PyImGui.begin(f"{self.window_name}##titlebar_fake", flags)
            PyImGui.invisible_button("##titlebar_dragging_area_1", __title_bar_rect[2] - (30 if self.can_close else 0), __title_bar_rect[3])
            self.__dragging = PyImGui.is_item_active() or self.__dragging
                    
            if PyImGui.is_item_focused():
                self.__set_focus = True
                
            # Handle Double Click to Expand/Collapse
            if PyImGui.is_mouse_double_clicked(0) and PyImGui.is_item_focused():
                self.expanded = not self.expanded
                
                if self.expanded:
                    self.__resize = True
                
            if self.can_close:
                x = self.__decorators_right - 35
                y = self.__decorators_top + 10         
                PyImGui.set_cursor_screen_pos(x, y)
                
                if PyImGui.invisible_button(f"##Close", 15, 15):              
                    self.open = False
                    self.__set_focus = False
                    
                PyImGui.set_cursor_screen_pos(x + 15, y - 10)
                PyImGui.invisible_button("##titlebar_dragging_area_2", 15, __title_bar_rect[3])
                self.__dragging = PyImGui.is_item_active() or self.__dragging
                    
            PyImGui.end()
            PyImGui.pop_style_color(1)
            PyImGui.pop_style_var(1)
                                
            # Handle dragging
            if self.__dragging:
                if self.__drag_started:                    
                    delta = PyImGui.get_mouse_drag_delta(0, 0.0)
                    new_window_pos = (__title_bar_rect[0] + 5 + delta[0], __title_bar_rect[1] + __title_bar_rect[3] - 2 + delta[1])
                    PyImGui.reset_mouse_drag_delta(0)
                    PyImGui.set_window_pos(new_window_pos[0], new_window_pos[1], PyImGui.ImGuiCond.Always)
                    # self.__set_focus = False
                else:
                    self.__drag_started = True
       
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
    
    @staticmethod
    def set_theme(theme: StyleTheme):
        ImGui.Theme = theme

    @staticmethod
    def push_style(theme: "ImGui.StyleTheme"):
        
        match (theme):
            case ImGui.StyleTheme.ImGui:
                ## Default Style    
                PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 10, 10)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 5.0)                
                PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 5, 5)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameRounding, 4.0)
                PyImGui.push_style_var2(ImGui.ImGuiStyleVar.ItemSpacing, 10, 6)
                PyImGui.push_style_var2(ImGui.ImGuiStyleVar.ItemInnerSpacing, 6, 4)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.IndentSpacing, 20.0)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.ScrollbarSize, 20.0)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.ScrollbarRounding, 9.0)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.GrabMinSize, 5.0)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.GrabRounding, 3.0)
                
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(Utils.RGBToColor(204, 204, 204, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TextDisabled, Utils.ColorToTuple(Utils.RGBToColor(51, 51, 51, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, Utils.ColorToTuple(Utils.RGBToColor(2, 2, 2, 215)))
                # PyImGui.push_style_color(PyImGui.ImGuiCol.ChildWindowBg, Utils.ColorToTuple(Utils.RGBToColor(18, 18, 23, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Tab, Utils.ColorToTuple(Utils.RGBToColor(26, 38, 51, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TabHovered, Utils.ColorToTuple(Utils.RGBToColor(51, 76, 102, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TabActive, Utils.ColorToTuple(Utils.RGBToColor(102, 127, 153, 255)))
                
                PyImGui.push_style_color(PyImGui.ImGuiCol.PopupBg, Utils.ColorToTuple(Utils.RGBToColor(2, 2, 2, 215)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(204, 204, 212, 225)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.BorderShadow, Utils.ColorToTuple(Utils.RGBToColor(26, 26, 26, 128)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, Utils.ColorToTuple(Utils.RGBToColor(26, 23, 30, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, Utils.ColorToTuple(Utils.RGBToColor(61, 59, 74, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, Utils.ColorToTuple(Utils.RGBToColor(143, 143, 148, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TitleBg, Utils.ColorToTuple(Utils.RGBToColor(13, 13, 13, 215)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TitleBgCollapsed, Utils.ColorToTuple(Utils.RGBToColor(5, 5, 5, 215)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TitleBgActive, Utils.ColorToTuple(Utils.RGBToColor(51, 51, 51, 215)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.MenuBarBg, Utils.ColorToTuple(Utils.RGBToColor(26, 23, 30, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarBg, Utils.ColorToTuple(Utils.RGBToColor(2, 2, 2, 215)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarGrab, Utils.ColorToTuple(Utils.RGBToColor(51, 76, 76, 128)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarGrabHovered, Utils.ColorToTuple(Utils.RGBToColor(51, 76, 102, 128)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarGrabActive, Utils.ColorToTuple(Utils.RGBToColor(51, 76, 102, 128)))
                # PyImGui.push_style_color(PyImGui.ImGuiCol.ComboBg, Utils.ColorToTuple(Utils.RGBToColor(26, 23, 30, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.CheckMark, Utils.ColorToTuple(Utils.RGBToColor(204, 204, 204, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, Utils.ColorToTuple(Utils.RGBToColor(51, 76, 76, 128)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, Utils.ColorToTuple(Utils.RGBToColor(51, 76, 102, 128)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, Utils.ColorToTuple(Utils.RGBToColor(26, 38, 51, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Utils.ColorToTuple(Utils.RGBToColor(51, 76, 102, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, Utils.ColorToTuple(Utils.RGBToColor(102, 127, 153, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Header, Utils.ColorToTuple(Utils.RGBToColor(26, 23, 30, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, Utils.ColorToTuple(Utils.RGBToColor(143, 143, 148, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, Utils.ColorToTuple(Utils.RGBToColor(15, 13, 18, 255))) 
                # PyImGui.push_style_color(PyImGui.ImGuiCol.Column, Utils.ColorToTuple(Utils.RGBToColor(143, 143, 148, 255)))
                # PyImGui.push_style_color(PyImGui.ImGuiCol.ColumnHovered, Utils.ColorToTuple(Utils.RGBToColor(61, 59, 74, 255)))
                # PyImGui.push_style_color(PyImGui.ImGuiCol.ColumnActive, Utils.ColorToTuple(Utils.RGBToColor(143, 143, 148, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ResizeGrip, Utils.ColorToTuple(Utils.RGBToColor(0, 0, 0, 0)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ResizeGripHovered, Utils.ColorToTuple(Utils.RGBToColor(143, 143, 148, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ResizeGripActive, Utils.ColorToTuple(Utils.RGBToColor(15, 13, 18, 255)))
                # PyImGui.push_style_color(PyImGui.ImGuiCol.CloseButton, Utils.ColorToTuple(Utils.RGBToColor(102, 99, 96, 40)))
                # PyImGui.push_style_color(PyImGui.ImGuiCol.CloseButtonHovered, Utils.ColorToTuple(Utils.RGBToColor(102, 99, 96, 100)))
                # PyImGui.push_style_color(PyImGui.ImGuiCol.CloseButtonActive, Utils.ColorToTuple(Utils.RGBToColor(102, 99, 96, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.PlotLines, Utils.ColorToTuple(Utils.RGBToColor(102, 99, 96, 160)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.PlotLinesHovered, Utils.ColorToTuple(Utils.RGBToColor(64, 255, 0, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogram, Utils.ColorToTuple(Utils.RGBToColor(102, 99, 96, 160)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogramHovered, Utils.ColorToTuple(Utils.RGBToColor(64, 255, 0, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TextSelectedBg, Utils.ColorToTuple(Utils.RGBToColor(26, 255, 26, 110)))
                # PyImGui.push_style_color(PyImGui.ImGuiCol.ModalWindowDarkening, Utils.ColorToTuple(Utils.RGBToColor(255, 250, 242, 186)))
                pass
            
            case ImGui.StyleTheme.Guild_Wars:
                ## Guild Wars Style -- Work in progress | Placeholder for now
                PyImGui.push_style_color(PyImGui.ImGuiCol.MenuBarBg, Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 0)))
                pass
            
            case ImGui.StyleTheme.Minimalus:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, Utils.ColorToTuple(Utils.RGBToColor(29, 62, 106, 100)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Utils.ColorToTuple(Utils.RGBToColor(29, 62, 106, 200)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, Utils.ColorToTuple(Utils.RGBToColor(29, 62, 106, 140)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Tab, Utils.ColorToTuple(Utils.RGBToColor(29, 62, 106, 100)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TabHovered, Utils.ColorToTuple(Utils.RGBToColor(29, 62, 106, 250)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TabActive, Utils.ColorToTuple(Utils.RGBToColor(29, 62, 106, 200)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, Utils.ColorToTuple(Utils.RGBToColor(29, 62, 106, 100)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, Utils.ColorToTuple(Utils.RGBToColor(29, 62, 106, 140)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TitleBg, Utils.ColorToTuple(Utils.RGBToColor(0, 0, 0, 150)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TitleBgActive, Utils.ColorToTuple(Utils.RGBToColor(0, 0, 0, 200)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.TitleBgCollapsed, Utils.ColorToTuple(Utils.RGBToColor(0, 0, 0, 225)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 50)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ScrollbarBg, Utils.ColorToTuple(Utils.RGBToColor(0, 0, 0, 150)))
                
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.TabRounding, 0.0)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.GrabRounding, 0.0)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.ChildRounding, 0.0)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameRounding, 0.0)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.PopupRounding, 0.0)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0.0)
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.ScrollbarRounding, 0.0)
    
    @staticmethod
    def pop_style(theme: "ImGui.StyleTheme"):
        match (theme):
            case ImGui.StyleTheme.ImGui:
                PyImGui.pop_style_var(11)
                PyImGui.pop_style_color(37)                
                pass
            
            case ImGui.StyleTheme.Guild_Wars:
                ## Guild Wars Style -- Work in progress | Placeholder for now
                PyImGui.pop_style_color(1)
                pass
            
            case ImGui.StyleTheme.Minimalus:
                PyImGui.pop_style_color(14)
                PyImGui.pop_style_var(7)
          
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