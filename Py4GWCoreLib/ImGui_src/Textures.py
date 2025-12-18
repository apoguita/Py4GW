from dataclasses import dataclass
from enum import IntEnum, Enum, IntFlag, auto
from typing import Optional
from .types import TEXTURE_FOLDER, MINIMALUS_FOLDER, StyleTheme
import os


class TextureState(IntEnum):
    Normal = 0
    Hovered = 1
    Active = 2
    Disabled = 3
    
class TextureSliceMode(IntEnum):
    FULL = 1
    THREE_HORIZONTAL = 3
    THREE_VERTICAL = 4
    NINE = 9

class RegionFlags(IntFlag):
    NONE   = 0
    LEFT   = auto()
    CENTER = auto()
    RIGHT  = auto()
    TOP    = auto()
    MIDDLE = auto()
    BOTTOM = auto()
    FULL   = auto()

class UVRegion:
    __slots__ = ("x0", "y0", "x1", "y1")

    def __init__(self, x0: float, y0: float, x1: float, y1: float):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1

    def uv0(self) -> tuple[float, float]:
        return (self.x0, self.y0)

    def uv1(self) -> tuple[float, float]:
        return (self.x1, self.y1)

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)

class GameTexture:
    """
    Unified class supporting:
    - Atlas state maps (Normal, Hovered, Active, Disabled)
    - 1/3/9-slice scalable rendering
    - Precomputed UVs for all states
    """

    def __init__(
        self,
        texture: str,
        texture_size: tuple[float, float],
        mode: TextureSliceMode = TextureSliceMode.FULL,
        element_size: Optional[tuple[float, float]] = None,
        margin: Optional[tuple[float, ...]] = None,
        state_map: Optional[dict[TextureState, tuple[float, float]]] = None,
    ):
        self.texture = texture
        self.tex_width, self.tex_height = texture_size
        self.mode = mode
        self.element_width, self.element_height = element_size if element_size else (texture_size[0], texture_size[1])
        
        if margin and len(margin) == 4:
            self.margin_left, self.margin_top, self.margin_right, self.margin_bottom = margin
            
        elif margin and len(margin) == 2:
            self.margin_left = self.margin_right = margin[0]
            self.margin_top = self.margin_bottom = margin[1]
            
        elif margin:
            self.margin_left = self.margin_top = self.margin_right = self.margin_bottom = margin[0]
            
        else:
            m = self._compute_margin(self.element_height)
            self.margin_left = self.margin_top = self.margin_right = self.margin_bottom = m


        # atlas state → pixel offset
        self.state_map = state_map or {
            TextureState.Normal: (0, 0),
        }

        # per-state, precomputed uv maps for all regions
        self.slicing_state_uvs: dict[TextureSliceMode, dict[TextureState, dict[RegionFlags, Optional[UVRegion]]]] = {}

        # build all precomputed UVs once
        self._build_all_state_uvs()

    # --- helpers ---------------------------------------------------------------

    def _compute_margin(self, size: float) -> float:
        if size <= 32:
            return 10.0
        elif size >= 64:
            return 40.0
        else:
            return 10.0 + (size - 32.0) * (30.0 / 32.0)

    def _uv(self, x0: float, y0: float, x1: float, y1: float) -> UVRegion:
        """Convert absolute pixel coordinates to normalized UVs."""
        return UVRegion(x0 / self.tex_width, y0 / self.tex_height, x1 / self.tex_width, y1 / self.tex_height)

    def _build_state_uv(self, mode: TextureSliceMode, offset_x: float, offset_y: float) -> dict[RegionFlags, Optional[UVRegion]]:
        """Build UV regions for one atlas state."""

        ml, mt, mr, mb = self.margin_left, self.margin_top, self.margin_right, self.margin_bottom
        w, h = self.element_width, self.element_height
        ox, oy = offset_x, offset_y

        uvs: dict[RegionFlags, Optional[UVRegion]] = {}

        match mode:
            case TextureSliceMode.FULL:
                uvs[RegionFlags.FULL] = self._uv(ox, oy, ox + w, oy + h)

            case TextureSliceMode.THREE_HORIZONTAL:
                uvs[RegionFlags.LEFT] = self._uv(ox, oy, ox + ml, oy + h)
                uvs[RegionFlags.CENTER] = self._uv(ox + ml, oy, ox + w - mr, oy + h)
                uvs[RegionFlags.RIGHT] = self._uv(ox + w - mr, oy, ox + w, oy + h)

            case TextureSliceMode.THREE_VERTICAL:
                uvs[RegionFlags.TOP] = self._uv(ox, oy, ox + w, oy + mt)
                uvs[RegionFlags.MIDDLE] = self._uv(ox, oy + mt, ox + w, oy + h - mb)
                uvs[RegionFlags.BOTTOM] = self._uv(ox, oy + h - mb, ox + w, oy + h)

            case TextureSliceMode.NINE:
                uvs[RegionFlags.TOP | RegionFlags.LEFT] = self._uv(ox, oy, ox + ml, oy + mt)
                uvs[RegionFlags.TOP | RegionFlags.CENTER] = self._uv(ox + ml, oy, ox + w - mr, oy + mt)
                uvs[RegionFlags.TOP | RegionFlags.RIGHT] = self._uv(ox + w - mr, oy, ox + w, oy + mt)
                uvs[RegionFlags.MIDDLE | RegionFlags.LEFT] = self._uv(ox, oy + mt, ox + ml, oy + h - mb)
                uvs[RegionFlags.MIDDLE | RegionFlags.CENTER] = self._uv(ox + ml, oy + mt, ox + w - mr, oy + h - mb)
                uvs[RegionFlags.MIDDLE | RegionFlags.RIGHT] = self._uv(ox + w - mr, oy + mt, ox + w, oy + h - mb)
                uvs[RegionFlags.BOTTOM | RegionFlags.LEFT] = self._uv(ox, oy + h - mb, ox + ml, oy + h)
                uvs[RegionFlags.BOTTOM | RegionFlags.CENTER] = self._uv(ox + ml, oy + h - mb, ox + w - mr, oy + h)
                uvs[RegionFlags.BOTTOM | RegionFlags.RIGHT] = self._uv(ox + w - mr, oy + h - mb, ox + w, oy + h)

        return uvs

    def _build_all_state_uvs(self):
        """Precompute all per-state UV sets."""
        for mode in TextureSliceMode:
            self.slicing_state_uvs[mode] = {}
            
            for state, (ox, oy) in self.state_map.items():
                self.slicing_state_uvs[mode][state] = self._build_state_uv(mode, ox, oy)

    # --- drawing ---------------------------------------------------------------

    def draw_in_drawlist(
        self,
        pos: tuple[float, float],
        size: tuple[float, float],
        state: TextureState = TextureState.Normal,
        tint: tuple[int, int, int, int] = (255, 255, 255, 255),
        mode: Optional[TextureSliceMode] = None,
    ):
        """Draw with precomputed UVs using 4-direction margins."""
        from .ImGuisrc import ImGui
        mode = mode or self.mode
        x, y = pos
        w, h = size
        ml, mt, mr, mb = self.margin_left, self.margin_top, self.margin_right, self.margin_bottom

        state_uvs = self.slicing_state_uvs.get(mode) or {}
        uvs = state_uvs.get(state)
        if not uvs:
            return


        def draw(region: RegionFlags, dx: float, dy: float, dw: float, dh: float):
            uv_region = uvs.get(region)
            if uv_region:
                # Replace with your engine's texture drawing call
                ImGui.DrawTextureInDrawList(
                    pos=(x + dx, y + dy),
                    size=(dw, dh),
                    texture_path=self.texture,
                    uv0=uv_region.uv0(),
                    uv1=uv_region.uv1(),
                    tint=tint
                )

        match mode:
            case TextureSliceMode.FULL:
                draw(RegionFlags.FULL, 0, 0, w, h)

            case TextureSliceMode.THREE_HORIZONTAL:
                lw, rw = ml, mr
                mw = max(0, w - lw - rw)
                draw(RegionFlags.LEFT, 0, 0, lw, h)
                draw(RegionFlags.CENTER, lw, 0, mw, h)
                draw(RegionFlags.RIGHT, lw + mw, 0, rw, h)

            case TextureSliceMode.THREE_VERTICAL:
                th, bh = mt, mb
                mh = max(0, h - th - bh)
                draw(RegionFlags.TOP, 0, 0, w, th)
                draw(RegionFlags.MIDDLE, 0, th, w, mh)
                draw(RegionFlags.BOTTOM, 0, th + mh, w, bh)

            case TextureSliceMode.NINE:
                # Each slice uses individual margin values
                cw, ch = ml, mt
                rw, bh = mr, mb
                mw = max(0, w - cw - rw)
                mh = max(0, h - ch - bh)

                draw(RegionFlags.TOP | RegionFlags.LEFT, 0, 0, cw, ch)
                draw(RegionFlags.TOP | RegionFlags.CENTER, cw, 0, mw, ch)
                draw(RegionFlags.TOP | RegionFlags.RIGHT, cw + mw, 0, rw, ch)
                draw(RegionFlags.MIDDLE | RegionFlags.LEFT, 0, ch, cw, mh)
                draw(RegionFlags.MIDDLE | RegionFlags.CENTER, cw, ch, mw, mh)
                draw(RegionFlags.MIDDLE | RegionFlags.RIGHT, cw + mw, ch, rw, mh)
                draw(RegionFlags.BOTTOM | RegionFlags.LEFT, 0, ch + mh, cw, bh)
                draw(RegionFlags.BOTTOM | RegionFlags.CENTER, cw, ch + mh, mw, bh)
                draw(RegionFlags.BOTTOM | RegionFlags.RIGHT, cw + mw, ch + mh, rw, bh)
                
class ThemeTexture:
    PlaceHolderTexture = GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "missing_texture.png"),
        texture_size = (64, 64),
        element_size = (64, 64),
    )

    def __init__(
        self,
        *args: tuple[StyleTheme, GameTexture],
    ):
        self.textures: dict[StyleTheme, GameTexture] = {}

        for theme, texture in args:
            self.textures[theme] = texture

    def get_texture(self, theme: StyleTheme | None = None) -> GameTexture:
        from .ImGuisrc import ImGui
        theme = theme or ImGui.get_style().Theme
        return self.textures.get(theme, self.textures.get(StyleTheme.Guild_Wars, ThemeTexture.PlaceHolderTexture))

class ThemeTextures(Enum):  
    
    ScrollGrab_Top = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_scrollgrab.png"),
            texture_size=(16, 16),
        ))
    )

    ScrollGrab_Middle = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_scrollgrab.png"),
            texture_size=(16, 16),
            element_size=(16, 2),
            state_map={
                TextureState.Normal: (0, 7)
            }
        ))
    )

    Scroll_Bg = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_scroll_background.png"),
            texture_size=(16, 16),
            element_size=(16, 16),
            state_map={
                TextureState.Normal: (0, 0)
            }
        ))
    )

    ScrollGrab_Bottom = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_scrollgrab.png"),
            texture_size=(16, 16),
        ))
    )

    RightButton = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_left_right.png"),
            texture_size=(64, 16),
            element_size=(14, 16),
            state_map={
                TextureState.Normal: (1, 0)
            }
        ))
    )

    LeftButton = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_left_right.png"),
            texture_size=(64, 16),
            element_size=(14, 16),
            state_map={
                TextureState.Normal: (17, 0),
                TextureState.Active: (49, 0),
            }
        ))
    )

    Horizontal_ScrollGrab_Top = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_horizontal_scrollgrab.png"),
            texture_size=(16, 16),
            element_size=(7, 16),
            state_map={
                TextureState.Normal: (0, 0)
            }
        ))
    )

    Horizontal_ScrollGrab_Middle = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_horizontal_scrollgrab.png"),
            texture_size=(16, 16),
            element_size=(2, 16),
            state_map={
                TextureState.Normal: (7, 0)
            }
        ))
    )

    Horizontal_ScrollGrab_Bottom = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_horizontal_scrollgrab.png"),
            texture_size=(16, 16),
            element_size=(7, 16),
            state_map={
                TextureState.Normal: (9, 0)
            }
        ))
    )

    Horizontal_Scroll_Bg = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_horizontal_scroll_background.png"),
            texture_size=(16, 16),
            element_size=(16, 16),
            state_map={
                TextureState.Normal: (0, 0)
            }
        ))
    )

    CircleButtons = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_profession_circle_buttons.png"),
            texture_size=(256, 128),
            element_size=(32, 32),
            state_map={
                TextureState.Normal: (224, 96),
                TextureState.Active: (192, 96)
            }
        ))
    )
    
    UpButton = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_up_down.png"),
            texture_size=(64, 16),
            element_size=(14, 16),
            state_map={
                TextureState.Normal: (1, 0)
            }
        ))
    )

    DownButton = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_up_down.png"),
            texture_size=(64, 16),
            element_size=(14, 16),
            state_map={
                TextureState.Normal: (17, 0),
                TextureState.Active: (49, 0),
        }
        ))
    )


    TravelCursor = ThemeTexture(
        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "Cursor", "travel_cursor.png"),
            texture_size=(32, 32),
            element_size=(32, 32),
            state_map={
                TextureState.Normal: (0, 0)
            }
        ))
    )

    Combo_Background = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_combo_background.png"),
            texture_size=(128, 32),
            margin=(36, 8),
            mode=TextureSliceMode.THREE_HORIZONTAL,
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(
                TEXTURE_FOLDER, "ui_combo_background.png"),
            texture_size=(128, 32),
            margin=(36, 8),
            mode=TextureSliceMode.THREE_HORIZONTAL,
        ))
    )

    Combo_Frame = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_combo_frame.png"),
            texture_size=(128, 32),
            margin=(36, 8),
            mode=TextureSliceMode.THREE_HORIZONTAL,
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_combo_frame.png"),
            texture_size=(128, 32),
            margin=(36, 8),
            mode=TextureSliceMode.THREE_HORIZONTAL,
        ))
    )
    
    ArrowCollapsed = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        element_size = (16, 16),
        state_map = {
            TextureState.Normal: (16, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        element_size = (16, 16),
        state_map = {
            TextureState.Normal: (16, 0),
        }
    )),
    )  

    ArrowExpanded = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        element_size = (16, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_arrow_collapse_expand.png"),
        texture_size = (32, 16),
        element_size = (16, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    )    
    
    CollapsingHeader_Background = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_collapsing_header_background.png"),
            texture_size=(128, 32),
            mode=TextureSliceMode.THREE_HORIZONTAL,
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(
                TEXTURE_FOLDER, "ui_collapsing_header_background.png"),
            texture_size=(128, 32),
            mode=TextureSliceMode.THREE_HORIZONTAL,
        ))
    )

    CollapsingHeader_Frame = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_collapsing_header_frame.png"),
            texture_size=(128, 32),
            mode=TextureSliceMode.THREE_HORIZONTAL,
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_collapsing_header_frame.png"),
            texture_size=(128, 32),
            mode=TextureSliceMode.THREE_HORIZONTAL,
        ))
    )

    Button_Frame = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_button_frame.png"),
            texture_size=(32, 32),
            mode=TextureSliceMode.NINE,
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_button_frame.png"),
            texture_size=(32, 32),
            mode=TextureSliceMode.NINE,
        ))
    )

    Button_Background = ThemeTexture(
        (StyleTheme.Minimalus, GameTexture(
            texture=os.path.join(MINIMALUS_FOLDER, "ui_button_background.png"),
            texture_size=(32, 32),
            mode=TextureSliceMode.NINE,
        )),

        (StyleTheme.Guild_Wars, GameTexture(
            texture=os.path.join(TEXTURE_FOLDER, "ui_button_background.png"),
            texture_size=(32, 32),
            mode=TextureSliceMode.NINE,
        ))
    )

    CheckBox_Unchecked = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        element_size = (17, 17),
        state_map = {
            TextureState.Normal: (2, 2),
            TextureState.Active: (23, 2),
            TextureState.Disabled: (107, 2),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        element_size = (17, 17),
        state_map = {
            TextureState.Normal: (2, 2),
            TextureState.Active: (23, 2),
            TextureState.Disabled: (107, 2),
        }
    )),
    )

    CheckBox_Checked = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        element_size = (17, 18),
        state_map = {
            TextureState.Normal: (44, 1),
            TextureState.Active: (65, 1),
            TextureState.Disabled: (86, 1),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_checkbox.png"),
        texture_size = (128, 32),
        element_size = (17, 18),
        state_map = {
            TextureState.Normal: (44, 1),
            TextureState.Active: (65, 1),
            TextureState.Disabled: (86, 1),
        }
    )),
    )

    SliderBar = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_slider_bar.png"),
        texture_size=(32, 16),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_slider_bar.png"),
        texture_size=(32, 16),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    )

    SliderGrab = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_slider_grab.png"),
        texture_size=(32, 32),
        element_size=(18, 18),
        state_map = {
            TextureState.Normal: (7, 7),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_slider_grab.png"),
        texture_size=(32, 32),
        element_size=(18, 18),
        state_map = {
            TextureState.Normal: (7, 7),
        }
    )),
    )

    Input_Inactive = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_input_inactive.png"),
        texture_size=(32, 16),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_input_inactive.png"),
        texture_size=(32, 16),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    )

    Input_Active = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_input_active.png"),
        texture_size=(32, 16),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_input_active.png"),
        texture_size=(32, 16),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    )

    InputMultiline_Inactive = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_input_inactive.png"),
        texture_size=(32, 16),
        mode=TextureSliceMode.NINE,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_input_inactive.png"),
        texture_size=(32, 16),
        mode=TextureSliceMode.NINE,
    )),
    )

    InputMultiline_Active = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_input_active.png"),
        texture_size=(32, 16),
        mode=TextureSliceMode.NINE,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_input_active.png"),
        texture_size=(32, 16),
        mode=TextureSliceMode.NINE,
    )),
    )

    Expand = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        element_size = (13, 12),
        state_map = {
            TextureState.Normal: (0, 3),
            TextureState.Hovered: (16, 3),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        element_size = (13, 12),
        state_map = {
            TextureState.Normal: (0, 3),
            TextureState.Hovered: (16, 3),
        }
    )),
    )

    Collapse = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        element_size = (13, 12),
        state_map = {
            TextureState.Normal: (0, 19),
            TextureState.Hovered: (16, 19),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_collapse_expand.png"),
        texture_size = (32, 32),
        element_size = (12, 12),
        state_map = {
            TextureState.Normal: (1, 19),
            TextureState.Hovered: (17, 19),
        }
    )),
    )        

    Tab_Frame = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
        mode=TextureSliceMode.NINE,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_tab_bar_frame.png"),
        texture_size=(32, 32),
        mode=TextureSliceMode.NINE,
    )),
    )
    
    Tab_Active = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_tab_active.png"),
        texture_size=(32, 32),
        margin=(8, 0),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_tab_active.png"),
        texture_size=(32, 32),
        margin=(8, 0),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    )

    Tab_Inactive = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_tab_inactive.png"),
        texture_size=(32, 32),
        margin=(8, 0),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_tab_inactive.png"),
        texture_size=(32, 32),
        margin=(8, 0),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    )

    Quest_Objective_Bullet_Point = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_quest_objective_bullet_point.png"),
        texture_size = (32, 16),
        element_size = (13, 13),
        state_map = {
            TextureState.Normal: (0, 0),
            TextureState.Active: (13, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_quest_objective_bullet_point.png"),
        texture_size = (32, 16),
        element_size = (13, 13),
        state_map = {
            TextureState.Normal: (0, 0),
            TextureState.Active: (13, 0),
        }
    )),
    )

    Pip_Regen = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_pips.png"),
        texture_size = (32, 16),
        element_size = (10, 16),
        state_map = {
            TextureState.Normal: (10, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_pips.png"),
        texture_size = (32, 16),
        element_size = (10, 16),
        state_map = {
            TextureState.Normal: (10, 0),
        }
    )),
    )

    Pip_Degen = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_pips.png"),
        texture_size = (32, 16),
        element_size = (10, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_pips.png"),
        texture_size = (32, 16),
        element_size = (10, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    )

    Close_Button = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_close_button_atlas.png"),
        texture_size = (64, 16),
        element_size = (12, 12),
        state_map = {
            TextureState.Normal: (1, 1),
            TextureState.Hovered: (17, 1),
            TextureState.Active: (33, 1),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_close_button_atlas.png"),
        texture_size = (64, 16),
        element_size = (12, 12),
        state_map = {
            TextureState.Normal: (1, 1),
            TextureState.Hovered: (17, 1),
            TextureState.Active: (33, 1),
        }
    )),
    )

    Title_Bar = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_titlebar.png"),
        texture_size=(128, 32),
        margin=(18, 0),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_titlebar.png"),
        texture_size=(128, 32),
        margin=(18, 0),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    )
    
    Title_Bar_Collapsed = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_titlebar_collapsed.png"),
        texture_size=(128, 32),
        margin=(18, 0),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_titlebar_collapsed.png"),
        texture_size=(128, 32),
        margin=(18, 0),
        mode=TextureSliceMode.THREE_HORIZONTAL,
    )),
    )

    Window = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
        mode=TextureSliceMode.NINE,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
        mode=TextureSliceMode.NINE,
    )),
    )
    
    Window_NoResize_NoTitleBar = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_window_notitlebar_noresize.png"),
        texture_size=(128, 128),
        mode=TextureSliceMode.NINE,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_window_notitlebar_noresize.png"),
        texture_size=(128, 128),
        mode=TextureSliceMode.NINE,
    )),
    )

    Window_NoResize = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_window_noresize.png"),
        texture_size=(128, 128),
        mode=TextureSliceMode.NINE,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_window_noresize.png"),
        texture_size=(128, 128),
        mode=TextureSliceMode.NINE,
    )),
    )

    Window_NoTitleBar = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_window_notitlebar.png"),
        texture_size=(128, 128),
        mode=TextureSliceMode.NINE,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_window_notitlebar.png"),
        texture_size=(128, 128),
        mode=TextureSliceMode.NINE,
    )),
    )

    Window_NoResize_NoTitlebar = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
        mode=TextureSliceMode.NINE,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_window.png"),
        texture_size=(128, 128),
        mode=TextureSliceMode.NINE,
    )),
    )

    Separator = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_separator.png"),
        texture_size = (32, 4),
        element_size = (32, 4),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    )
    
    HealthBarFill = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    )
    
    HealthBarCursor = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    )
    
    HealthBarEmpty = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),
    )
    
    HealthBarBleedingFill = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_bleeding.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health_bleeding.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    )
    
    HealthBarBleedingCursor = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_bleeding.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "Progressbar", "ui_progress_health_bleeding.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    )
    
    HealthBarBleedingEmpty = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_bleeding.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health_bleeding.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),    
    )
    
    HealthBarPoisonedFill = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_poisoned.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health_poisoned.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    )
    
    HealthBarPoisonedCursor = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_poisoned.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "Progressbar", "ui_progress_health_poisoned.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    )
    
    HealthBarPoisonedEmpty = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_poisoned.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health_poisoned.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),    
    )
    
    HealthBarDeepWound = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_health_deep_wound.png"),
        texture_size=(16, 16),
        element_size=(10, 16),
        state_map = {
            TextureState.Normal: (6, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_health_deep_wound.png"),
        texture_size=(16, 16),
        element_size=(10, 16),
        state_map = {
            TextureState.Normal: (6, 0),
        }
    )),
    )
    
    HealthBarDeepWoundCursor = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_health_deep_wound.png"),
        texture_size=(16, 16),
        element_size=(1, 16),
        state_map = {
            TextureState.Normal: (5, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_health_deep_wound.png"),
        texture_size=(16, 16),
        element_size=(1, 16),
        state_map = {
            TextureState.Normal: (5, 0),
        }
    )),
    )
    
    HealthBarHexedFill = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_hexed.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health_hexed.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    )
    
    HealthBarHexedCursor = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_hexed.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "Progressbar", "ui_progress_health_hexed.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    )
    
    HealthBarHexedEmpty = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_hexed.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health_hexed.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),
    )
    
    HealthBarDisconnectedFill = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_disconnected.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health_disconnected.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    )
    
    HealthBarDisconnectedCursor = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_disconnected.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "Progressbar", "ui_progress_health_disconnected.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    )
    
    HealthBarDisconnectedEmpty = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_health_disconnected.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_health_disconnected.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),
    )
    
    HealthIdenticator_Enchanted = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_health_identicator.png"),
        texture_size=(32, 32),
        element_size=(16, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_health_identicator.png"),
        texture_size=(32, 32),
        element_size=(16, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    )
    
    HealthIdenticator_Conditioned = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_health_identicator.png"),
        texture_size=(32, 32),
        element_size=(16, 16),
        state_map = {
            TextureState.Normal: (16, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_health_identicator.png"),
        texture_size=(32, 32),
        element_size=(16, 16),
        state_map = {
            TextureState.Normal: (16, 0),
        }
    )),
    )
    
    HealthIdenticator_Hexed = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_health_identicator.png"),
        texture_size=(32, 32),
        element_size=(16, 16),
        state_map = {
            TextureState.Normal: (0, 16),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_health_identicator.png"),
        texture_size=(32, 32),
        element_size=(16, 16),
        state_map = {
            TextureState.Normal: (0, 16),
        }
    )),
    )
    
    HealthIdenticator_WeaponSpell = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_health_identicator.png"),
        texture_size=(32, 32),
        element_size=(16, 16),
        state_map = {
            TextureState.Normal: (16, 16),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_health_identicator.png"),
        texture_size=(32, 32),
        element_size=(16, 16),
        state_map = {
            TextureState.Normal: (16, 16),
        }
    )),
    )
    
    EnergyBarFill = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        element_size=(3, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    )
    
    EnergyBarCursor = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        element_size=(4, 16),
        state_map = {
            TextureState.Normal: (3, 0),
        }
    )),
    )
    
    EnergyBarEmpty = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER,"Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER,"Progressbar", "ui_progress_energy.png"),
        texture_size=(16, 16),
        element_size=(9, 16),
        state_map = {
            TextureState.Normal: (7, 0),
        }
    )),
    )
    
    ProgressBarProgressFill = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_progress_highlight.png"),
        texture_size=(16, 16),
        element_size= (5, 16),
        margin=(0, 0, 11, 0),
        mode=TextureSliceMode.NINE,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_progress_highlight.png"),
        texture_size=(16, 16),
        element_size= (5, 16),
        margin=(0, 0, 11, 0),
        mode=TextureSliceMode.NINE,
    )),
    )
    
    ProgressBarProgressCursor = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_progress_highlight.png"),
        texture_size=(16, 16),
        element_size= (1, 16),
        margin=(0,0,0,0),
        state_map = {
            TextureState.Normal: (0, 0)
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_progress_highlight.png"),
        texture_size=(16, 16),
        element_size= (1, 16),
        margin=(0,0,0,0),
        state_map = {
            TextureState.Normal: (0, 0)
        }
    )),
    )

    ProgressBarBackground = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        element_size=(10, 16),
        margin=(3,0,0,0),
        state_map= {
            TextureState.Normal: (6, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_progress_default.png"),
        texture_size=(16, 16),
        element_size=(10, 16),
        margin=(3,0,0,0),
        state_map= {
            TextureState.Normal: (6, 0),
        }
    )),
    )   
    
    ProgressBarFrame = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_progress_frame.png"),
        texture_size=(16, 16),
        mode=TextureSliceMode.NINE,
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_progress_frame.png"),
        texture_size=(16, 16),
        mode=TextureSliceMode.NINE,
    )),
    )   

    BulletPoint = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_bullet_point.png"),
        texture_size = (16, 16),
        element_size = (16, 16),
        state_map = {
            TextureState.Normal: (0, 0),
        }
    )),
    )   

    #Skill
    Skill_Slot_Empty = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_empty_skill_slot.png"),
        texture_size = (64, 64),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (4, 4),
        }
    )),
    )
    
    Skill_Frame = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (0, 0),
            TextureState.Active: (56, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (0, 0),
            TextureState.Active: (56, 0),
        }
    )),
    )
    
    Effect_Frame_Skill = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (112, 0),
            TextureState.Active: (168, 0),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (112, 0),
            TextureState.Active: (168, 0),
        }
    )),
    )
    
    Effect_Frame_Condition = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (0, 56),
            TextureState.Active: (56, 56),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (0, 56),
            TextureState.Active: (56, 56),
        }
    )),
    )
    
    Effect_Frame_Enchantment = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (112, 56),
            TextureState.Active: (168, 56),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (112, 56),
            TextureState.Active: (168, 56),
        }
    )),
    )

    Effect_Frame_Hex = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (0, 112),
            TextureState.Active: (56, 112),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (0, 112),
            TextureState.Active: (56, 112),
        }
    )),
    )
    
    Effect_Frame_Blue = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (112, 112),
            TextureState.Active: (168, 112),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_skill_frames.png"),
        texture_size = (256, 256),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (112, 112),
            TextureState.Active: (168, 112),
        }
    )),
    )

    Dropdown_Button_Base = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_dropdown_button.png"),
        texture_size = (64, 32),
        element_size= (21, 21),
        state_map = {
            TextureState.Normal: (1, 1),
            TextureState.Active: (25, 1),
        }
    )),
    )
    
    Hero_Panel_Toggle_Base = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_hero_panel_toggle.png"),
        texture_size = (64, 32),
        element_size= (17, 17),
        state_map = {
            TextureState.Normal: (1, 2),
            TextureState.Active: (22, 2),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_hero_panel_toggle.png"),
        texture_size = (64, 32),
        element_size= (17, 17),
        state_map = {
            TextureState.Normal: (1, 2),
            TextureState.Active: (22, 2),
        }
    )),
    )
    
    Check = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_check_cancel.png"),
        texture_size = (64, 64),
        element_size= (32, 32),
        state_map = {
            TextureState.Normal: (0, 0),
            TextureState.Hovered: (32, 0),
        }
    )),
    )
    
    Cancel = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_check_cancel.png"),
        texture_size = (64, 64),
        element_size= (32, 32),
        state_map = {
            TextureState.Normal: (0, 32),
            TextureState.Hovered: (32, 32),
        }
    )),
    )
    
    TemplateAction = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        element_size= (21, 21),
        state_map = {
            TextureState.Normal: (1, 1),
            TextureState.Hovered: (25, 1),
        }
    )),
    )
    
    TemplateLoad = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        element_size= (21, 21),
        state_map = {
            TextureState.Normal: (49, 1),
            TextureState.Hovered: (74, 1),
        },
    )),
    )
    
    TemplateSave = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        element_size= (21, 21),
        state_map = {
            TextureState.Normal: (97, 1),
            TextureState.Hovered: (2, 25),
        }
    )),
    )
    
    TemplateManage = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        element_size= (21, 21),
        state_map = {
            TextureState.Normal: (50, 25),
            TextureState.Hovered: (25, 25),
        }
    )),
    )
    
    TemplateCode = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_template_actions.png"),
        texture_size = (128, 64),
        element_size= (22, 22),
        state_map = {
            TextureState.Normal: (97, 23),
            TextureState.Hovered: (72, 23),
        }
    )),
    )
    
    HeroPanelButtonBase = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "ui_aggression.png"),
        texture_size = (128, 64),
        element_size= (27, 29),
        state_map = {
            TextureState.Normal: (67, 34),
            TextureState.Active: (99, 34),
        }
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_aggression.png"),
        texture_size = (128, 64),
        element_size= (27, 29),
        state_map = {
            TextureState.Normal: (67, 34),
            TextureState.Active: (99, 34),
        }
    )),
    )

    HeaderLabelBackground = ThemeTexture(
    (StyleTheme.Minimalus,  GameTexture(
        texture=os.path.join(MINIMALUS_FOLDER, "header_label.png"),
        texture_size = (128, 32),
    )),
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "header_label.png"),
        texture_size = (128, 32),
    )),
    )
    
    AdrenalineBarFill = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_adrenaline_effect.png"),
        texture_size = (64, 64),
        element_size = (64, 64),
    )),
    )
    
    Inventory_Slots = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_iventory_slots.png"),
        texture_size = (128, 128),
        element_size = (52, 64),
        state_map = {
            TextureState.Normal: (0, 0),
            TextureState.Active: (0, 64),
        }
    )),
    )
    
    Inventory_Slot_Blue = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_iventory_slots.png"),
        texture_size = (128, 128),
        element_size = (52, 64),
        state_map = {
            TextureState.Normal: (52, 0),
        }
    )),
    )
    
    Inventory_Slot_Red = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_iventory_slots.png"),
        texture_size = (128, 128),
        element_size = (52, 64),
        state_map = {
            TextureState.Normal: (52, 64),
        }
    )),
    )
    
    MoraleBoost = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "morale_boost_effect.png"),
        texture_size = (64, 64),
        element_size = (64, 64),
    )),
    )
    
    DeathPenalty = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "death_penalty_effect.png"),
        texture_size = (64, 64),
        element_size = (64, 64),
    )),
    )

    HardMode = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_hardmode_atlas.png"),
        texture_size = (128, 64),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (0, 0)
        }
    )),
    )
    
    HardModeCompleted = ThemeTexture(
    (StyleTheme.Guild_Wars,  GameTexture(
        texture=os.path.join(TEXTURE_FOLDER, "ui_hardmode_atlas.png"),
        texture_size = (128, 64),
        element_size = (56, 56),
        state_map = {
            TextureState.Normal: (56, 0)
        }
    )),
    )