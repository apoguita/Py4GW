from typing import Optional, Tuple, Any, overload
from enum import Enum, IntEnum

class SortDirection(IntEnum):
    NoDirection = 0
    Ascending = 1
    Descending = 2

class TableColumnSortSpecs:
    def __init__(self, column_index: int, sort_direction: SortDirection):
        self.column_index = column_index
        self.sort_direction = sort_direction

    @property
    def ColumnIndex(self) -> int:
        return self.column_index

    @property
    def SortDirection(self) -> SortDirection:
        return self.sort_direction

class TableSortSpecs:
    def __init__(self, specs_count: int, specs_dirty: bool, specs: Optional[TableColumnSortSpecs] = None):
        self.specs_count = specs_count
        self.specs_dirty = specs_dirty
        self.specs = specs

    @property
    def SpecsCount(self) -> int:
        return self.specs_count

    @property
    def SpecsDirty(self) -> bool:
        return self.specs_dirty

    @property
    def Specs(self) -> Optional[TableColumnSortSpecs]:
        return self.specs

class WindowFlags(IntEnum):
    NoFlag = 0
    NoTitleBar = 1 << 0
    NoResize = 1 << 1
    NoMove = 1 << 2
    NoScrollbar = 1 << 3
    NoScrollWithMouse = 1 << 4
    NoCollapse = 1 << 5
    AlwaysAutoResize = 1 << 6
    NoBackground = 1 << 7
    NoSavedSettings = 1 << 8
    NoMouseInputs = 1 << 9
    MenuBar = 1 << 10
    HorizontalScrollbar = 1 << 11
    NoFocusOnAppearing = 1 << 12
    NoBringToFrontOnFocus = 1 << 13
    AlwaysVerticalScrollbar = 1 << 14
    AlwaysHorizontalScrollbar = 1 << 15
    NoNavInputs = 1 << 16
    NoNavFocus = 1 << 17
    UnsavedDocument = 1 << 18

class InputTextFlags(IntEnum):
    NoFlag = 0
    CharsDecimal = 1 << 0
    CharsHexadecimal = 1 << 1
    CharsUppercase = 1 << 2
    CharsNoBlank = 1 << 3
    AutoSelectAll = 1 << 4
    EnterReturnsTrue = 1 << 5
    CallbackCompletion = 1 << 6
    CallbackHistory = 1 << 7
    CallbackAlways = 1 << 8
    CallbackCharFilter = 1 << 9
    AllowTabInput = 1 << 10
    CtrlEnterForNewLine = 1 << 11
    NoHorizontalScroll = 1 << 12
    ReadOnly = 1 << 13
    Password = 1 << 14
    NoUndoRedo = 1 << 15
    CharsScientific = 1 << 16
    CallbackResize = 1 << 17
    CallbackEdit = 1 << 18
    
class TreeNodeFlags(IntEnum):
    NoFlag = 0
    Selected = 1 << 0
    Framed = 1 << 1
    NoTreePushOnOpen = 1 << 2
    NoAutoOpenOnLog = 1 << 3
    DefaultOpen = 1 << 4
    OpenOnDoubleClick = 1 << 5
    OpenOnArrow = 1 << 6
    Leaf = 1 << 7
    Bullet = 1 << 8
    FramePadding = 1 << 9
    SpanAvailWidth = 1 << 10
    SpanFullWidth = 1 << 11
    NavLeftJumpsBackHere = 1 << 12
    CollapsingHeader = 1 << 13

class SelectableFlags(IntEnum):
    NoFlag = 0
    DontClosePopups = 1 << 0
    SpanAllColumns = 1 << 1
    AllowDoubleClick = 1 << 2
    Disabled = 1 << 3

class TableFlags(IntEnum):
    NoFlag = 0
    Resizable = 1 << 0
    Reorderable = 1 << 1
    Hideable = 1 << 2
    Sortable = 1 << 3
    NoSavedSettings = 1 << 4
    ContextMenuInBody = 1 << 5
    RowBg = 1 << 6
    BordersInnerH = 1 << 7
    BordersOuterH = 1 << 8
    BordersInnerV = 1 << 9
    BordersOuterV = 1 << 10
    BordersH = 1 << 11
    BordersV = 1 << 12
    Borders = 1 << 13
    NoBordersInBody = 1 << 14
    NoBordersInBodyUntilResize = 1 << 15
    SizingFixedFit = 1 << 16
    SizingFixedSame = 1 << 17
    SizingStretchProp = 1 << 18
    SizingStretchSame = 1 << 19
    NoHostExtendX = 1 << 20
    NoHostExtendY = 1 << 21
    NoKeepColumnsVisible = 1 << 22
    PreciseWidths = 1 << 23
    NoClip = 1 << 24
    PadOuterX = 1 << 25
    NoPadOuterX = 1 << 26
    NoPadInnerX = 1 << 27
    ScrollX = 1 << 28
    ScrollY = 1 << 29
    SortMulti = 1 << 30
    SortTristate = 1 << 31
    
class TableColumnFlags(IntEnum):
    NoFlag = 0
    DefaultHide = 1 << 0
    DefaultSort = 1 << 1
    WidthStretch = 1 << 2
    WidthFixed = 1 << 3
    NoResize = 1 << 4
    NoReorder = 1 << 5
    NoHide = 1 << 6
    NoClip = 1 << 7
    NoSort = 1 << 8
    NoSortAscending = 1 << 9
    NoSortDescending = 1 << 10
    IndentEnable = 1 << 11
    IndentDisable = 1 << 12
    IsEnabled = 1 << 13
    IsVisible = 1 << 14
    IsSorted = 1 << 15
    IsHovered = 1 << 16
    
class TableRowFlags(IntEnum):
    NoFlag = 0
    Headers = 1 << 0


class FocusedFlags(IntEnum):
    NoFlag = 0
    ChildWindows = 1 << 0
    RootWindow = 1 << 1
    AnyWindow = 1 << 2
    RootAndChildWindows = 1 << 3

class HoveredFlags(IntEnum):
    NoFlag = 0
    ChildWindows = 1 << 0
    RootWindow = 1 << 1
    AnyWindow = 1 << 2
    AllowWhenBlockedByPopup = 1 << 3
    AllowWhenBlockedByActiveItem = 1 << 4
    AllowWhenOverlapped = 1 << 5
    AllowWhenDisabled = 1 << 6


class ImGuiIO:
    def __init__(self):
        self.display_size_x = 0.0
        self.display_size_y = 0.0
        self.delta_time = 0.0
        self.ini_saving_rate = 0.0
        self.ini_filename = None
        self.log_filename = None
        self.mouse_double_click_time = 0.0
        self.mouse_double_click_max_dist = 0.0
        self.mouse_drag_threshold = 0.0
        self.mouse_pos_x = 0.0
        self.mouse_pos_y = 0.0
        self.mouse_wheel = 0.0
        self.mouse_wheel_h = 0.0
        self.key_ctrl = False
        self.key_shift = False
        self.key_alt = False
        self.key_super = False
        self.framerate = 0.0
        self.metrics_render_vertices = 0
        self.metrics_render_indices = 0
        self.metrics_active_windows = 0
        self.want_capture_mouse = False
        self.want_capture_keyboard = False
        self.want_text_input = False
        self.want_set_mouse_pos = False
        self.want_save_ini_settings = False
        self.mouse_pos_prev_x = 0.0
        self.mouse_pos_prev_y = 0.0
        self.app_focus_lost = False

@staticmethod
def get_io() -> ImGuiIO: ...

class ImGuiCol(IntEnum):
    Text = 0
    TextDisabled = 1
    WindowBg = 2
    ChildBg = 3
    PopupBg = 4
    Border = 5
    BorderShadow = 6
    FrameBg = 7
    FrameBgHovered = 8
    FrameBgActive = 9
    TitleBg = 10
    TitleBgActive = 11
    TitleBgCollapsed = 12
    MenuBarBg = 13
    ScrollbarBg = 14
    ScrollbarGrab = 15
    ScrollbarGrabHovered = 16
    ScrollbarGrabActive = 17
    CheckMark = 18
    SliderGrab = 19
    SliderGrabActive = 20
    Button = 21
    ButtonHovered = 22
    ButtonActive = 23
    Header = 24
    HeaderHovered = 25
    HeaderActive = 26
    Separator = 27
    SeparatorHovered = 28
    SeparatorActive = 29
    ResizeGrip = 30
    ResizeGripHovered = 31
    ResizeGripActive = 32
    Tab = 33
    TabHovered = 34
    TabActive = 35
    TabUnfocused = 36
    TabUnfocusedActive = 37
    PlotLines = 38
    PlotLinesHovered = 39
    PlotHistogram = 40
    PlotHistogramHovered = 41
    TableHeaderBg = 42
    TableBorderStrong = 43
    TableBorderLight = 44
    TableRowBg = 45
    TableRowBgAlt = 46
    TextSelectedBg = 47
    DragDropTarget = 48
    NavHighlight = 49
    NavWindowingHighlight = 50
    NavWindowingDimBg = 51
    ModalWindowDimBg = 52
    

@staticmethod
def text(text: str) -> None: ...
@staticmethod
def text_wrapped(text: str) -> None: ...
@staticmethod
def text_colored(text: str, color: Tuple[float, float, float, float]) -> None: ...
@staticmethod
def text_disabled(text: str) -> None: ...
@staticmethod
def text_unformatted(text: str) -> None: ...
@staticmethod
def text_scaled(text: str, color: Tuple[float, float, float, float], scale: float) -> None: ...
@staticmethod
def get_text_line_height() -> float: ...
@staticmethod
def get_text_line_height_with_spacing() -> float: ...
@staticmethod
def calc_text_size(text: str) -> Tuple[float, float]: ...
@staticmethod
def button(label: str, width: float = 0, height: float = 0) -> bool: ...
@staticmethod
def small_button(label: str) -> bool: ...
@staticmethod
def invisible_button(label: str, width: float, height: float) -> bool: ...
@staticmethod
def checkbox(label: str, v: bool) -> bool: ...
@staticmethod
def radio_button(label: str, v: int, button_index: int) -> int: ...
@staticmethod
def slider_float(label: str, v: float, v_min: float, v_max: float) -> float: ...
@staticmethod
def slider_int(label: str, v: int, v_min: int, v_max: int) -> int: ...
@overload
def input_text(label: str, text: str) -> str: ...
@overload
def input_text(label: str, text: str, flags: int) -> str: ...
@staticmethod
def input_float(label: str, v: float) -> float: ...
@overload
def input_int(label: str, v: int) -> int: ...
@overload
def input_int(label: str, v: int, min_value: int = 0, step_fast: int = 100000, flags: int = 0) -> int: ...
@staticmethod
def combo(label: str, current_item: int, items: list[str]) -> int: ...
@staticmethod
def selectable(label: str, selected: bool, flags: SelectableFlags = SelectableFlags.NoFlag, size: Tuple[float, float] = (0.0, 0.0)) -> bool: ...

@staticmethod
def color_edit3(label: str, color: Tuple[float, float, float]) -> Tuple[float, float, float]: ...
@staticmethod
def color_edit4(label: str, color: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]: ...

@staticmethod
def get_scroll_max_x() -> float: ...
@staticmethod
def get_scroll_max_y() -> float: ...
@staticmethod
def get_scroll_x() -> float: ...
@staticmethod
def get_scroll_y() -> float: ...
@staticmethod
def set_scroll_x(scroll_x: float) -> None: ...
@staticmethod
def set_scroll_y(scroll_y: float) -> None: ...
@staticmethod
def set_scroll_here_x(center_x_ratio: float = 0.5) -> None: ...
@staticmethod
def set_scroll_here_y(center_y_ratio: float = 0.5) -> None: ...
@staticmethod
def set_scroll_from_pos_x(local_x: float, center_x_ratio: float = 0.5) -> None: ...
@staticmethod
def set_scroll_from_pos_y(local_y: float, center_y_ratio: float = 0.5) -> None: ...



#@staticmethod
#def get_style() -> ImGuiStyle: ...
@staticmethod
def get_cursor_pos() -> Tuple[float, float]: ...
@staticmethod
def set_cursor_pos(x: float, y: float) -> None: ...
@staticmethod
def get_cursor_pos_x() -> float: ...
@staticmethod
def set_cursor_pos_x(x: float) -> None: ...
@staticmethod
def get_cursor_pos_y() -> float: ...
@staticmethod
def set_cursor_pos_y(y: float) -> None: ...
@staticmethod
def get_cursor_start_pos() -> Tuple[float, float]: ...
@staticmethod
def get_cursor_screen_pos() -> Tuple[float, float]: ...
@staticmethod
def set_cursor_screen_pos(x: float, y: float) -> None: ...
@staticmethod
def is_rect_visible(width: float, height: float) -> bool: ...
@staticmethod
def push_style_color(idx: int, col: Tuple[float, float, float, float]) -> None: ...
@staticmethod
def pop_style_color(count: int = 1) -> None: ...
@staticmethod
def push_style_var(idx: int, val: float) -> None: ...
@staticmethod
def push_style_var2(idx: int, x: float, y: float) -> None: ...
@staticmethod
def pop_style_var(count: int = 1) -> None: ...
@staticmethod
def push_item_width(item_width: float) -> None: ...
@staticmethod
def pop_item_width() -> None: ...
@staticmethod
def push_text_wrap_pos(wrap_pos_x: float = 0.0) -> None: ...
@staticmethod
def pop_text_wrap_pos() -> None: ...
@staticmethod
def push_button_repeat(repeat: bool) -> None: ...
@staticmethod
def pop_button_repeat() -> None: ...

#Windows, Panels, and Groups
@staticmethod
def progress_bar(fraction: float, size_arg: float = -1.0, overlay: str = "") -> None: ...
@staticmethod
def bullet_text(text: str) -> None: ...

# Windows, Panels, and Groups
@overload
def begin(name: str) -> bool: ...
@overload
def begin(name: str, flags: int) -> bool: ...
@overload
def begin(name: str, p_open: Optional[bool], flags: int) -> bool: ...
@staticmethod
def begin_with_close(name: str, p_open: bool, flags: int) -> tuple[bool, bool]: ...
@staticmethod
def end() -> None: ...
@overload
def begin_child(str_id: str) -> bool: ...
@overload
def begin_child(id: str, size: Tuple[float, float], border: bool, flags: int) -> bool: ...
@staticmethod
def end_child() -> None: ...
@staticmethod
def begin_group() -> None: ...
@staticmethod
def end_group() -> None: ...
@staticmethod
def separator() -> None: ...
@staticmethod
def same_line(offset_from_start_x: float = 0.0, spacing: float = -1.0) -> None: ...
@staticmethod
def spacing() -> None: ...
@staticmethod
def indent(indent_w: float = 0.0) -> None: ...
@staticmethod
def unindent(indent_w: float = 0.0) -> None: ...

# Layout
@staticmethod
def columns(count: int = 1, id: str = "", border: bool = True) -> None: ...
@staticmethod
def next_column() -> None: ...
@staticmethod
def end_columns() -> None: ...
@staticmethod
def set_next_window_size(width: float, height: float) -> None: ...
@staticmethod
def set_next_window_pos(x: float, y: float) -> None: ...
@staticmethod
def set_next_window_collapsed(collapsed: bool, cond: int = 0) -> None: ...


# Menus and Toolbars
@staticmethod
def begin_menu_bar() -> bool: ...
@staticmethod
def end_menu_bar() -> None: ...
@staticmethod
def begin_main_menu_bar() -> bool: ...
@staticmethod
def end_main_menu_bar() -> None: ...
@staticmethod
def begin_menu(label: str) -> bool: ...
@staticmethod
def end_menu() -> None: ...
@staticmethod
def menu_item(label: str) -> bool: ...

# Popups and Modals
@staticmethod
def open_popup(str_id: str) -> None: ...
@staticmethod
def begin_popup(str_id: str) -> bool: ...
@staticmethod
def end_popup() -> None: ...
@overload
def begin_popup_modal(name: str, p_open: Optional[bool]) -> bool: ...
@overload
def begin_popup_modal(name: str, p_open: Optional[bool], flags: int) -> bool: ...
@staticmethod
def end_popup_modal() -> None: ...
@staticmethod
def close_current_popup() -> None: ...

# Tables
@overload
def begin_table(id: str, columns: int) -> bool: ...
@overload
def begin_table(id: str, columns: int, flags: int) -> bool: ...
@overload
def begin_table(id: str, columns: int, flags: int, width: float, height: float) -> bool: ...
@staticmethod
def end_table() -> None: ...
@staticmethod
def table_next_row() -> None: ...
@staticmethod
def table_next_column() -> None: ...
@overload
def table_setup_column(label: str) -> None: ...
@overload
def table_setup_column(label: str, flags: int) -> None: ...
@overload 
def table_setup_column(label: str, flags: int, init_width_or_weight: float) -> None: ...
@staticmethod
def table_set_column_index(column_index: int) -> None: ...
@staticmethod
def table_get_sort_specs() -> Optional[Any]: ...
@staticmethod
def table_headers_row() -> None: ...
@staticmethod
def table_get_column_count() -> int: ...
@staticmethod
def table_get_column_index() -> int: ...
@staticmethod
def table_get_row_index() -> int: ...
@staticmethod
def table_set_bg_color(target: int, color: int, column_index: int = -1) -> None: ...
@staticmethod
def table_set_column_width(column_index: int, width: float) -> None: ...
@staticmethod
def table_set_column_enabled(column_index: int, enabled: bool) -> None: ...
@staticmethod
def table_set_column_offset(column_index: int, offset_x: float) -> None: ...

# Tabs
@staticmethod
def begin_tab_bar(str_id: str) -> bool: ...
@staticmethod
def end_tab_bar() -> None: ...
@overload
def begin_tab_item(label: str) -> bool: ...
@overload
def begin_tab_item(label: str, popen: bool) -> bool: ...
@overload
def begin_tab_item(label: str, popen: bool, flags:int) -> bool: ...
@staticmethod
def end_tab_item() -> None: ...


# Drawing
@staticmethod
def draw_list_add_line(x1: float, y1: float, x2: float, y2: float, col: int, thickness: float) -> None: ...
@staticmethod
def draw_list_add_rect(x1: float, y1: float, x2: float, y2: float, col: int, rounding: float, rounding_corners_flags: int, thickness: float) -> None: ...
@staticmethod
def draw_list_add_circle(x: float, y: float, radius: float, col: int, num_segments: int, thickness: float) -> None: ...
@staticmethod
def draw_list_add_text(x: float, y: float, col: int, text: str) -> None: ...
@staticmethod
def draw_list_add_rect_filled(x1: float, y1: float, x2: float, y2: float, col: int, rounding: float, rounding_corners_flags: int) -> None: ...
@staticmethod
def draw_list_add_circle_filled(x: float, y: float, radius: float, col: int, num_segments: int) -> None: ...
@staticmethod
def draw_list_add_triangle(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, col: int, thickness: float) -> None: ...
@staticmethod
def draw_list_add_triangle_filled(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, col: int) -> None: ...
@staticmethod
def draw_list_add_quad(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, x4: float, y4: float, col: int, thickness: float) -> None: ...
@staticmethod
def draw_list_add_quad_filled(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, x4: float, y4: float, col: int) -> None: ...


# Windows
@staticmethod
def get_window_pos() -> Tuple[float, float]: ...
@staticmethod
def get_window_size() -> Tuple[float, float]: ...
@staticmethod
def get_window_width() -> float: ...
@staticmethod
def get_window_height() -> float: ...
@staticmethod
def get_content_region_avail() -> Tuple[float, float]: ...
@staticmethod
def get_content_region_max() -> Tuple[float, float]: ...
@staticmethod
def get_window_content_region_min() -> Tuple[float, float]: ...
@staticmethod
def get_window_content_region_max() -> Tuple[float, float]: ...

#Tables
@staticmethod
def get_column_index() -> int: ...
@staticmethod
def get_column_width(column_index: int = -1) -> float: ...
@staticmethod
def get_column_offset(column_index: int = -1) -> float: ...
@staticmethod
def get_columns_count() -> int: ...

# Input Handling
@staticmethod
def set_mouse_cursor(cursor_type: int) -> None: ...
@staticmethod
def is_mouse_clicked(button: int) -> bool: ...
@staticmethod
def is_mouse_double_clicked(button: int) -> bool: ...
@staticmethod
def is_mouse_down(button: int) -> bool: ...
@staticmethod
def is_mouse_released(button: int) -> bool: ...
@staticmethod
def is_mouse_dragging(button: int, lock_threshold: float = -1.0) -> bool: ...
@staticmethod
def is_item_hovered() -> bool: ...
@staticmethod
def is_item_clicked(button:int=0) -> bool: ...
@staticmethod
def is_window_collapsed() -> bool: ...
@staticmethod
def is_window_focused() -> bool: ...
@staticmethod
def is_window_hovered() -> bool: ...
@staticmethod
def is_window_appearing() -> bool: ...
@staticmethod
def is_item_active() -> bool: ...
@staticmethod
def is_item_focused() -> bool: ...
@staticmethod
def is_item_visible() -> bool: ...
@staticmethod
def is_item_edited() -> bool: ...
@staticmethod
def is_item_deactivated() -> bool: ...
@staticmethod
def is_item_deactivated_after_edit() -> bool: ...
@staticmethod
def is_item_activated() -> bool: ...
@staticmethod
def is_item_toggled_open() -> bool: ...
@staticmethod
def is_key_pressed(key: int) -> bool: ...


# Miscellaneous
@staticmethod
def show_demo_window() -> None: ...
@staticmethod
def set_tooltip(text: str) -> None: ...
@staticmethod
def show_tooltip(tooltip_text: str) -> None: ...
@staticmethod
def begin_tooltip() -> None: ...
@staticmethod
def end_tooltip() -> None: ...
@staticmethod
def log_to_clipboard() -> None: ...
@staticmethod
def log_finish() -> None: ...
@staticmethod
def get_clipboard_text() -> str: ...
@staticmethod
def set_clipboard_text(text: str) -> None: ...
@staticmethod
def push_id(id_str: str) -> None: ...
@staticmethod
def pop_id() -> None: ...

@staticmethod
def push_clip_rect(x,y,w,h, intersect_with_current_clip_rect: bool) -> None: ...
@staticmethod
def pop_clip_rect() -> None: ...

# Tree Nodes
@staticmethod
def tree_node(label: str) -> bool: ...
@overload
def tree_node_ex(label: str, flags: int) -> bool: ...
@overload
def tree_node_ex(label: str, flags: int, fmt: str) -> bool: ...
@staticmethod
def tree_pop() -> None: ...
@staticmethod
def get_tree_node_to_label_spacing() -> float: ...
@staticmethod
def set_next_item_open(is_open: bool, cond: int = 0) -> None: ...
@staticmethod
def set_next_item_width(item_width: float) -> None: ...
@overload
def collapsing_header(label: str) -> bool: ...
@overload
def collapsing_header(label: str, flags: int) -> bool: ...
@staticmethod
def dummy(width:int, height:int) -> None: ...
