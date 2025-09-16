from enum import IntEnum, Enum

TEXTURE_FOLDER = "Textures\\Game UI\\"
MINIMALUS_FOLDER = "Textures\\Themes\\Minimalus\\"


class ControlAppearance(Enum):
    Default = 0
    Primary = 1
    Danger = 2


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