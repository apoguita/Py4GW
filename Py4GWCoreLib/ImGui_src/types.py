from enum import IntEnum, Enum

TEXTURE_FOLDER = "Textures\\Game UI\\"
MINIMALUS_FOLDER = "Textures\\Themes\\Minimalus\\"


class ControlAppearance(Enum):
    Default = 0
    Primary = 1
    Danger = 2

class StyleTheme(IntEnum):
    ImGui = 0
    Guild_Wars = 1
    Minimalus = 2
    Smoke = 3
    Contrast = 4
    Negative = 5
    
class VerticalAlignment(IntEnum):
    '''
    Vertical Alignment Options
    '''
    Above = 0
    Top = 1
    Middle = 2
    Bottom = 3
    Below = 4


class HorizontalAlignment(IntEnum):
    '''
    Horizontal Alignment Options
    '''
    LeftOf = 0
    Left = 1
    Center = 2
    Right = 3
    RightOf = 4


_H_SHIFT = 0
_V_SHIFT = 3

_H_MASK = 0b111 << _H_SHIFT
_V_MASK = 0b111 << _V_SHIFT

class Alignment(IntEnum):
    '''
    All Combinations of VerticalAlignment and HorizontalAlignment
    as bit-packed enum values.
    Allows easy extraction of vertical and horizontal components.
    
    Properties:
        vertical: VerticalAlignment
        horizontal: HorizontalAlignment
    
    Example:
        alignment = Alignment.TopRight
        alignment.vertical      --> VerticalAlignment.Top
        alignment.horizontal    --> HorizontalAlignment.Right
    '''
    
    # bit layout:
    # bits 0–2 : horizontal (0–4)
    # bits 3–5 : vertical   (0–4)

    AboveLeftOf    = (VerticalAlignment.Above  << _V_SHIFT) | HorizontalAlignment.LeftOf
    AboveLeft      = (VerticalAlignment.Above  << _V_SHIFT) | HorizontalAlignment.Left
    AboveCenter    = (VerticalAlignment.Above  << _V_SHIFT) | HorizontalAlignment.Center
    AboveRight     = (VerticalAlignment.Above  << _V_SHIFT) | HorizontalAlignment.Right
    AboveRightOf   = (VerticalAlignment.Above  << _V_SHIFT) | HorizontalAlignment.RightOf

    TopLeftOf      = (VerticalAlignment.Top    << _V_SHIFT) | HorizontalAlignment.LeftOf
    TopLeft        = (VerticalAlignment.Top    << _V_SHIFT) | HorizontalAlignment.Left
    TopCenter      = (VerticalAlignment.Top    << _V_SHIFT) | HorizontalAlignment.Center
    TopRight       = (VerticalAlignment.Top    << _V_SHIFT) | HorizontalAlignment.Right
    TopRightOf     = (VerticalAlignment.Top    << _V_SHIFT) | HorizontalAlignment.RightOf

    MidLeftOf      = (VerticalAlignment.Middle << _V_SHIFT) | HorizontalAlignment.LeftOf
    MidLeft        = (VerticalAlignment.Middle << _V_SHIFT) | HorizontalAlignment.Left
    MidCenter      = (VerticalAlignment.Middle << _V_SHIFT) | HorizontalAlignment.Center
    MidRight       = (VerticalAlignment.Middle << _V_SHIFT) | HorizontalAlignment.Right
    MidRightOf     = (VerticalAlignment.Middle << _V_SHIFT) | HorizontalAlignment.RightOf

    BottomLeftOf   = (VerticalAlignment.Bottom << _V_SHIFT) | HorizontalAlignment.LeftOf
    BottomLeft     = (VerticalAlignment.Bottom << _V_SHIFT) | HorizontalAlignment.Left
    BottomCenter   = (VerticalAlignment.Bottom << _V_SHIFT) | HorizontalAlignment.Center
    BottomRight    = (VerticalAlignment.Bottom << _V_SHIFT) | HorizontalAlignment.Right
    BottomRightOf  = (VerticalAlignment.Bottom << _V_SHIFT) | HorizontalAlignment.RightOf

    BelowLeftOf    = (VerticalAlignment.Below  << _V_SHIFT) | HorizontalAlignment.LeftOf
    BelowLeft      = (VerticalAlignment.Below  << _V_SHIFT) | HorizontalAlignment.Left
    BelowCenter    = (VerticalAlignment.Below  << _V_SHIFT) | HorizontalAlignment.Center
    BelowRight     = (VerticalAlignment.Below  << _V_SHIFT) | HorizontalAlignment.Right
    BelowRightOf   = (VerticalAlignment.Below  << _V_SHIFT) | HorizontalAlignment.RightOf

    @property
    def vertical(self) -> VerticalAlignment:
        return VerticalAlignment((self.value & _V_MASK) >> _V_SHIFT)

    @property
    def horizontal(self) -> HorizontalAlignment:
        return HorizontalAlignment((self.value & _H_MASK) >> _H_SHIFT)

    @classmethod
    def from_parts(
        cls,
        vertical: VerticalAlignment,
        horizontal: HorizontalAlignment,
    ) -> "Alignment":
        return cls((vertical << _V_SHIFT) | horizontal)
    
class TextDecorator(IntEnum):
    None_ = 0
    Underline = 1
    Strikethrough = 2
    Highlight = 3
    
class StyleColorType(IntEnum):
    Default = 0
    Custom = 1
    Texture = 2

class SortDirection(Enum):
    No_Sort = 0
    Ascending = 1
    Descending = 2    

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