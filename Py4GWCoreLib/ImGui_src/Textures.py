from enum import IntEnum, Enum
from .types import TEXTURE_FOLDER, MINIMALUS_FOLDER, StyleTheme
from ..Overlay import Overlay
import os


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
        from .ImGuisrc import ImGui
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
        from .ImGuisrc import ImGui
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
        *args: tuple[StyleTheme, SplitTexture | MapTexture],
    ):
        self.textures: dict[StyleTheme, SplitTexture | MapTexture] = {}

        for theme, texture in args:
            self.textures[theme] = texture

    def get_texture(self, theme: StyleTheme | None = None) -> SplitTexture | MapTexture:
        from .ImGuisrc import ImGui
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
        (StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_combo_arrow.png"),
            texture_size=(128, 32),
            left=(4, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 123, 27)
        )),

        (StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_combo_arrow.png"),
            texture_size=(128, 32),
            left=(1, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 126, 27),
        ))
    )

    Combo_Background = ThemeTexture(
        (StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_combo_background.png"),
            texture_size=(128, 32),
            left=(4, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 124, 27)
        )),

        (StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(
                TEXTURE_FOLDER, "ui_combo_background.png"),
            texture_size=(128, 32),
            left=(1, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 126, 27),
        ))
    )

    Combo_Frame = ThemeTexture(
        (StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_combo_frame.png"),
            texture_size=(128, 32),
            left=(4, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 124, 27),
        )),

        (StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_combo_frame.png"),
            texture_size=(128, 32),
            left=(1, 4, 14, 27),
            mid=(15, 4, 92, 27),
            right=(93, 4, 126, 27),
        ))
    )
    ArrowCollapsed = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        size = (16, 16),
        normal = (16, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        size = (16, 16),
        normal = (16, 0),
    )),
    )  

    ArrowExpanded = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        size = (16, 16),
        normal = (0, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        size = (16, 16),
        normal = (0, 0),
    )),
    )    
    
    CollapsingHeader_Background = ThemeTexture(
        (StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_collapsing_header_background.png"),
            texture_size=(128, 32),
            left=(4, 5, 14, 26),
            mid=(15, 5, 92, 26),
            right=(93, 5, 124, 26),
        )),

        (StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(
                TEXTURE_FOLDER, "ui_collapsing_header_background.png"),
            texture_size=(128, 32),
            left=(3, 5, 14, 26),
            mid=(15, 5, 92, 26),
            right=(93, 5, 125, 26),
        ))
    )

    CollapsingHeader_Frame = ThemeTexture(
        (StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_collapsing_header_frame.png"),
            texture_size=(128, 32),
            left=(4, 5, 14, 26),
            mid=(15, 5, 92, 26),
            right=(93, 5, 124, 26),
        )),

        (StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_collapsing_header_frame.png"),
            texture_size=(128, 32),
            left=(3, 5, 14, 26),
            mid=(15, 5, 92, 26),
            right=(93, 5, 125, 26),
        ))
    )

    Button_Frame = ThemeTexture(
        (StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_button_frame.png"),
            texture_size=(32, 32),
            left=(6, 4, 7, 25),
            mid=(8, 4, 24, 25),
            right=(25, 4, 26, 25), 
        )),

        (StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_button_frame.png"),
            texture_size=(32, 32),
            left=(2, 4, 7, 25),
            mid=(8, 4, 24, 25),
            right=(24, 4, 30, 25), 
        ))
    )

    Button_Background = ThemeTexture(
        (StyleTheme.Minimalus, SplitTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_button_background.png"),
            texture_size=(32, 32),
            left=(6, 4, 7, 25),
            mid=(8, 4, 24, 25),
            right=(25, 4, 26, 25), 
        )),

        (StyleTheme.Guild_Wars, SplitTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_button_background.png"),
            texture_size=(32, 32),
            left=(2, 4, 7, 25),
            mid=(8, 4, 24, 25),
            right=(24, 4, 30, 25), 
        ))
    )

    CheckBox_Unchecked = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 17),
        normal=(2, 2),
        active=(23, 2),
        disabled=(107, 2),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 17),
        normal=(2, 2),
        active=(23, 2),
        disabled=(107, 2),
    )),
    )

    CheckBox_Checked = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 18),
        normal=(44, 1),
        active=(65, 1),
        disabled=(86, 1),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        size = (17, 18),
        normal=(44, 1),
        active=(65, 1),
        disabled=(86, 1),
    )),
    )

    SliderBar = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_slider_bar.png"),
        texture_size=(32, 16),
        left=(0, 0, 7, 16),
        mid=(8, 0, 24, 16),
        right=(25, 0, 32, 16),   
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_slider_bar.png"),
        texture_size=(32, 16),
        left=(0, 0, 7, 16),
        mid=(8, 0, 24, 16),
        right=(25, 0, 32, 16),   
    )),
    )

    SliderGrab = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_slider_grab.png"),
        texture_size=(32, 32),
        size=(18, 18),
        normal=(7, 7)
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_slider_grab.png"),
        texture_size=(32, 32),
        size=(18, 18),
        normal=(7, 7)
    )),
    )

    Input_Inactive = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_input_inactive.png"),
        texture_size=(32, 16),
        left= (1, 0, 6, 16),
        mid= (7, 0, 26, 16),
        right= (27, 0, 31, 16),
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_input_inactive.png"),
        texture_size=(32, 16),
        left= (1, 0, 6, 16),
        mid= (7, 0, 26, 16),
        right= (27, 0, 31, 16),
    )),
    )

    Input_Active = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_input_active.png"),
        texture_size=(32, 16),
        left= (1, 1, 6, 15),
        mid= (7, 1, 26, 15),
        right= (27, 1, 31, 15),
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_input_active.png"),
        texture_size=(32, 16),
        left= (1, 1, 6, 15),
        mid= (7, 1, 26, 15),
        right= (27, 1, 31, 15),
    )),
    )

    Expand = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (13, 12),
        normal = (0, 3),
        hovered = (16, 3),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (12, 12),
        normal = (1, 3),
        hovered = (17, 3),
    )),
    )

    Collapse = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (13, 12),
        normal = (0, 19),
        hovered = (16, 19),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        size = (12, 12),
        normal = (1, 19),
        hovered = (17, 19),
    )),
    )        

    Tab_Frame_Top = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
        left=(1, 1, 4, 5),
        mid=(5, 1, 26, 5),
        right=(27, 1, 31, 5),   
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
        left=(1, 1, 4, 5),
        mid=(5, 1, 26, 5),
        right=(27, 1, 31, 5),   
    )),
    )

    Tab_Frame_Body = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
        left=(1, 5, 4, 26),
        mid=(5, 5, 26, 26),
        right=(27, 5, 31, 26), 
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
        left=(1, 5, 4, 26),
        mid=(5, 5, 26, 26),
        right=(27, 5, 31, 26),  
    )),
    )

    Tab_Active = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_active.png"),
        texture_size=(32, 32),
        left=(2, 1, 8, 32),
        mid=(9, 1, 23, 32),
        right=(24, 1, 30, 32),   
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_active.png"),
        texture_size=(32, 32),
        left=(2, 1, 8, 32),
        mid=(9, 1, 23, 32),
        right=(24, 1, 30, 32),   
    )),
    )

    Tab_Inactive = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_tab_inactive.png"),
        texture_size=(32, 32),
        left=(2, 6, 8, 32),
        mid=(9, 6, 23, 32),
        right=(24, 6, 30, 32),   
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_tab_inactive.png"),
        texture_size=(32, 32),
        left=(2, 6, 8, 32),
        mid=(9, 6, 23, 32),
        right=(24, 6, 30, 32),    
    )),
    )

    Quest_Objective_Bullet_Point = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_quest_objective_bullet_point.png"),
        texture_size = (32, 16),
        size = (13, 13),
        normal=(0, 0),
        active=(13, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_quest_objective_bullet_point.png"),
        texture_size = (32, 16),
        size = (13, 13),
        normal=(0, 0),
        active=(13, 0),
    )),
    )

    Close_Button = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_close_button_atlas.png"),
        texture_size = (64, 16),
        size = (12, 12),
        normal=(1, 1),
        hovered=(17, 1),
        active=(33, 1),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_close_button_atlas.png"),
        texture_size = (64, 16),
        size = (12, 12),
        normal=(1, 1),
        hovered=(17, 1),
        active=(33, 1),
    )),
    )

    Title_Bar = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_title_frame_atlas.png"),
        texture_size=(128, 32),
        left=(0, 6, 18, 32),
        mid=(19, 6, 109, 32),
        right=(110, 6, 128, 32)
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_title_frame_atlas.png"),
        texture_size=(128, 32),
        left=(0, 6, 18, 32),
        mid=(19, 6, 109, 32),
        right=(110, 6, 128, 32)
    )),
    )

    Window_Frame_Top = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 0, 18, 40),
        right=(110, 0, 128, 40),
        mid=(19, 0, 109, 40)
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 0, 18, 40),
        right=(110, 0, 128, 40),
        mid=(19, 0, 109, 40)
    )),
    )

    Window_Frame_Center = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 40, 18, 68),
        mid=(19, 40, 109, 68),
        right=(110, 40, 128, 68),
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 40, 18, 68),
        mid=(19, 40, 109, 68),
        right=(110, 40, 128, 68),
    )),
    )

    Window_Frame_Bottom = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 68, 18, 128),
        mid=(19, 68, 77, 128),
        right=(78, 68, 128, 128),
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas.png"),
        texture_size=(128, 128),
        left=(0, 68, 18, 128),
        mid=(19, 68, 77, 128),
        right=(78, 68, 128, 128),
    )),
    )

    Window_Frame_Top_NoTitleBar = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_frame_atlas_no_titlebar.png"),
        texture_size=(128, 128),
        left=(0, 0, 18, 51),
        right=(110, 0, 128, 51),
        mid=(19, 0, 109, 51)
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas_no_titlebar.png"),
        texture_size=(128, 128),
        left=(0, 0, 18, 51),
        right=(110, 0, 128, 51),
        mid=(19, 0, 109, 51)
    )),
    )

    Window_Frame_Bottom_No_Resize = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(MINIMALUS_FOLDER, "ui_window_frame_atlas_no_resize.png"),
        texture_size=(128, 128),
        left=(0, 68, 18, 128),
        mid=(19, 68, 77, 128),
        right=(78, 68, 128, 128),
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_window_frame_atlas_no_resize.png"),
        texture_size=(128, 128),
        left=(0, 68, 18, 128),
        mid=(19, 68, 77, 128),
        right=(78, 68, 128, 128),
    )),
    )

    Separator = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_separator.png"),
        texture_size = (32, 4),
        size = (32, 4),
        normal = (0, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_separator.png"),
        texture_size = (32, 4),
        size = (32, 4),
        normal = (0, 0),
    )),
    )

    ProgressBarFrame = ThemeTexture(
    (StyleTheme.Minimalus,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_frame.png"),
        texture_size=(16, 16),
        left= (1, 1, 2, 14),
        mid= (3, 1, 12, 14),
        right= (13, 1, 14, 14),
    )),
    (StyleTheme.Guild_Wars,  SplitTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_frame.png"),
        texture_size=(16, 16),
        left= (1, 1, 2, 14),
        mid= (3, 1, 12, 14),
        right= (13, 1, 14, 14),
    )),
    )

    ProgressBarProgressCursor = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_highlight.png"),
        texture_size=(16, 16),
        size= (16, 16),
        normal = (0, 0)
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_highlight.png"),
        texture_size=(16, 16),
        size= (16, 16),
        normal = (0, 0)
    )),
    )

    ProgressBarProgress = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (0, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (0, 0),
    )),
    )

    ProgressBarBackground = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (6, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        size=(6, 16),
        normal= (6, 0),
    )),
    )   

    BulletPoint = ThemeTexture(
    (StyleTheme.Minimalus,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_bullet_point.png"),
        texture_size = (16, 16),
        size = (16, 16),
        normal = (0, 0),
    )),
    (StyleTheme.Guild_Wars,  MapTexture(
        texture = os.path.join(TEXTURE_FOLDER, "ui_bullet_point.png"),
        texture_size = (16, 16),
        size = (16, 16),
        normal = (0, 0),
    )),
    )   
