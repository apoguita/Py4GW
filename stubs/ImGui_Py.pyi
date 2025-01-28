# ImGui_Py.pyi - Auto-generated .pyi file for ImGui_Py module

from typing import Tuple, List, Any

# Enum WindowFlags
class WindowFlags:
    None: int
    NoTitleBar: int
    NoResize: int
    NoMove: int
    NoScrollbar: int
    NoScrollWithMouse: int
    NoCollapse: int
    AlwaysAutoResize: int
    NoBackground: int
    NoSavedSettings: int
    NoMouseInputs: int
    MenuBar: int
    HorizontalScrollbar: int
    NoFocusOnAppearing: int
    NoBringToFrontOnFocus: int
    AlwaysVerticalScrollbar: int
    AlwaysHorizontalScrollbar: int
    AlwaysUseWindowPadding: int
    NoNavInputs: int
    NoNavFocus: int
    UnsavedDocument: int

# Enum InputTextFlags
class InputTextFlags:
    None: int
    CharsDecimal: int
    CharsHexadecimal: int
    CharsUppercase: int
    CharsNoBlank: int
    AutoSelectAll: int
    EnterReturnsTrue: int
    CallbackCompletion: int
    CallbackHistory: int
    CallbackAlways: int
    CallbackCharFilter: int
    AllowTabInput: int
    CtrlEnterForNewLine: int
    NoHorizontalScroll: int
    ReadOnly: int
    Password: int
    NoUndoRedo: int
    CharsScientific: int
    CallbackResize: int
    CallbackEdit: int

# Enum TreeNodeFlags
class TreeNodeFlags:
    None: int
    Selected: int
    Framed: int
    AllowItemOverlap: int
    NoTreePushOnOpen: int
    NoAutoOpenOnLog: int
    DefaultOpen: int
    OpenOnDoubleClick: int
    OpenOnArrow: int
    Leaf: int
    Bullet: int
    FramePadding: int
    SpanAvailWidth: int
    SpanFullWidth: int
    NavLeftJumpsBackHere: int
    CollapsingHeader: int

# Enum SelectableFlags
class SelectableFlags:
    None: int
    DontClosePopups: int
    SpanAllColumns: int
    AllowDoubleClick: int
    Disabled: int
    AllowItemOverlap: int

# Enum TableFlags
class TableFlags:
    None: int
    Resizable: int
    Reorderable: int
    Hideable: int
    Sortable: int
    NoSavedSettings: int
    ContextMenuInBody: int
    RowBg: int
    BordersInnerH: int
    BordersOuterH: int
    BordersInnerV: int
    BordersOuterV: int
	Borders: int
    NoBordersInBody: int
    NoBordersInBodyUntilResize: int
    SizingFixedFit: int
    SizingFixedSame: int
    SizingStretchProp: int
    SizingStretchSame: int
    NoHostExtendX: int
    NoHostExtendY: int
    NoKeepColumnsVisible: int
    PreciseWidths: int
    NoClip: int
    PadOuterX: int
    NoPadOuterX: int
    NoPadInnerX: int
    ScrollX: int
    ScrollY: int
    SortMulti: int
    SortTristate: int

# Enum TableColumnFlags
class TableColumnFlags:
    None: int
    DefaultHide: int
    DefaultSort: int
    WidthStretch: int
    WidthFixed: int
    NoResize: int
    NoReorder: int
    NoHide: int
    NoClip: int
    NoSort: int
    NoSortAscending: int
    NoSortDescending: int
    IndentEnable: int
    IndentDisable: int
    IsEnabled: int
    IsVisible: int
    IsSorted: int
    IsHovered: int

# Enum TableRowFlags
class TableRowFlags:
    None: int
    Headers: int

# Enum FocusedFlags
class FocusedFlags:
    None: int
    ChildWindows: int
    RootWindow: int
    AnyWindow: int
    RootAndChildWindows: int

# Enum HoveredFlags
class HoveredFlags:
    None: int
    ChildWindows: int
    RootWindow: int
    AnyWindow: int
    AllowWhenBlockedByPopup: int
    AllowWhenBlockedByActiveItem: int
    AllowWhenOverlapped: int
    AllowWhenDisabled: int

# Class ImGuiIO
class ImGuiIO:
    display_size: Tuple[float, float]
    delta_time: float
    ini_saving_rate: float
    ini_filename: str
    log_filename: str
    mouse_double_click_time: float
    mouse_double_click_max_dist: float
    mouse_drag_threshold: float
    mouse_pos: Tuple[float, float]
    mouse_wheel: float
    mouse_wheel_h: float
    key_ctrl: bool
    key_shift: bool
    key_alt: bool
    key_super: bool
    framerate: float
    metrics_render_vertices: int
    metrics_render_indices: int
    metrics_active_windows: int
    metrics_active_allocations: int
    want_capture_mouse: bool
    want_capture_keyboard: bool
    want_text_input: bool
    want_set_mouse_pos: bool
    want_save_ini_settings: bool
    mouse_pos_prev: Tuple[float, float]
    app_focus_lost: bool

from typing import Tuple

# Enum ImGuiCol
class ImGuiCol:
    Text: int
    TextDisabled: int
    WindowBg: int
    ChildBg: int
    PopupBg: int
    Border: int
    BorderShadow: int
    FrameBg: int
    FrameBgHovered: int
    FrameBgActive: int
    TitleBg: int
    TitleBgActive: int
    TitleBgCollapsed: int
    MenuBarBg: int
    ScrollbarBg: int
    ScrollbarGrab: int
    ScrollbarGrabHovered: int
    ScrollbarGrabActive: int
    CheckMark: int
    SliderGrab: int
    SliderGrabActive: int
    Button: int
    ButtonHovered: int
    ButtonActive: int
    Header: int
    HeaderHovered: int
    HeaderActive: int
    Separator: int
    SeparatorHovered: int
    SeparatorActive: int
    ResizeGrip: int
    ResizeGripHovered: int
    ResizeGripActive: int
    Tab: int
    TabHovered: int
    TabActive: int
    TabUnfocused: int
    TabUnfocusedActive: int
    PlotLines: int
    PlotLinesHovered: int
    PlotHistogram: int
    PlotHistogramHovered: int
    TableHeaderBg: int
    TableBorderStrong: int
    TableBorderLight: int
    TableRowBg: int
    TableRowBgAlt: int
    TextSelectedBg: int
    DragDropTarget: int
    NavHighlight: int
    NavWindowingHighlight: int
    NavWindowingDimBg: int
    ModalWindowDimBg: int

# ImGui_Py.pyi - Auto-generated .pyi file for ImGui_Py module

from typing import Tuple, List, Any

# Functions

def get_io() -> ImGuiIO:
    """Retrieves ImGui IO settings.
    Returns: ImGuiIO object with input/output settings.
    """
    pass

def text(label: str) -> None:
    """Displays simple text.
    Args: label (str): Text to display.
    """
    pass

def text_wrapped(label: str) -> None:
    """Displays wrapped text.
    Args: label (str): Text to display.
    """
    pass

def text_colored(label: str, color: List[float]) -> None:
    """Displays colored text.
    Args: label (str): Text, color (List[float]): RGBA color.
    """
    pass

def text_disabled(label: str) -> None:
    """Displays disabled text.
    Args: label (str): Text to display.
    """
    pass

def text_ex(label: str, flags: str) -> None:
    """Displays text with flags.
    Args: label (str): Text, flags (str): Display flags.
    """
    pass

def text_unformatted(label: str) -> None:
    """Displays raw text.
    Args: label (str): Text to display.
    """
    pass

def button(label: str) -> bool:
    """Creates a clickable button.
    Args: label (str): Button text.
    Returns: bool: True if clicked.
    """
    pass

def checkbox(label: str, v: bool) -> bool:
    """Creates a checkbox.
    Args: label (str): Checkbox label, v (bool): Current state.
    Returns: bool: New checkbox state.
    """
    pass

def radio_button(label: str, v: int, button_index: int) -> bool:
    """Creates a radio button.
    Args: label (str): Label, v (int): State, button_index (int): Index.
    Returns: bool: True if selected.
    """
    pass

def slider_float(label: str, v: float, min_val: float, max_val: float) -> bool:
    """Creates a float slider.
    Args: label (str): Label, v (float): Current value, min_val (float): Min, max_val (float): Max.
    Returns: bool: True if value changed.
    """
    pass

def slider_int(label: str, v: int, min_val: int, max_val: int) -> bool:
    """Creates an integer slider.
    Args: label (str): Label, v (int): Current value, min_val (int): Min, max_val (int): Max.
    Returns: bool: True if value changed.
    """
    pass

def input_text(label: str, text: str) -> str:
    """Creates a text input box.
    Args: label (str): Label, text (str): Input value.
    Returns: str: Modified text.
    """
    pass

def input_text(label: str, text: str, flags: int) -> str:
    """Creates a text input box with flags.
    Args: label (str): Label, text (str): Input value, flags (int): Input flags.
    Returns: str: Modified text.
    """
    pass

def input_float(label: str, v: float) -> bool:
    """Creates a float input box.
    Args: label (str): Label, v (float): Input value.
    Returns: bool: True if value changed.
    """
    pass

def input_int(label: str, v: int) -> bool:
    """Creates an integer input box.
    Args: label (str): Label, v (int): Input value.
    Returns: bool: True if value changed.
    """
    pass

def combo(label: str, current_item: int, items: List[str]) -> int:
    """Creates a dropdown combo box.
    Args: label (str): Label, current_item (int): Selected item, items (List[str]): List of items.
    Returns: int: Selected item index.
    """
    pass

def color_edit3(label: str, color: Tuple[float, float, float]) -> bool:
    """Creates a color editor (RGB).
    Args: label (str): Label, color (Tuple[float, float, float]): RGB color.
    Returns: bool: True if color changed.
    """
    pass

def color_edit4(label: str, color: Tuple[float, float, float, float]) -> bool:
    """Creates a color editor (RGBA).
    Args: label (str): Label, color (Tuple[float, float, float, float]): RGBA color.
    Returns: bool: True if color changed.
    """
    pass

def get_scroll_max_x() -> float:
    """
    Returns the maximum scroll value in the x-direction.
    
    :return: The maximum horizontal scroll value.
    """
    pass

def get_scroll_max_y() -> float:
    """
    Returns the maximum scroll value in the y-direction.
    
    :return: The maximum vertical scroll value.
    """
    pass

def get_scroll_x() -> float:
    """
    Returns the current scroll value in the x-direction.
    
    :return: The current horizontal scroll value.
    """
    pass

def get_scroll_y() -> float:
    """
    Returns the current scroll value in the y-direction.
    
    :return: The current vertical scroll value.
    """
    pass

def get_style() -> 'ImGuiStyle':
    """
    Returns the current style settings of the ImGui context.

    :return: A reference to the ImGuiStyle object which can be used to modify style settings.
    """
    pass

class ImGuiStyle:
    """
    ImGuiStyle defines the look and feel of the UI.
    """

    Alpha: float
    """Global alpha applies to everything."""

    WindowPadding: Tuple[float, float]
    """Padding within a window."""

    WindowRounding: float
    """Radius of window corners rounding. Set to 0.0f to have rectangular windows."""

    FramePadding: Tuple[float, float]
    """Padding within a framed region (used by most widgets)."""

    FrameRounding: float
    """Radius of frame corners rounding. Set to 0.0f to have rectangular frames."""

    ItemSpacing: Tuple[float, float]
    """Horizontal and vertical spacing between widgets."""

def get_cursor_pos() -> Tuple[float, float]:
    """
    Returns the current cursor position in ImGui, relative to the current window.

    :return: A tuple containing the x and y position of the cursor in the current window.
    """
    pass

def get_cursor_pos_x() -> float:
    """
    Returns the current cursor position in the x-direction, relative to the current window.

    :return: The x-coordinate of the cursor position.
    """
    pass

def get_cursor_pos_y() -> float:
    """
    Returns the current cursor position in the y-direction, relative to the current window.

    :return: The y-coordinate of the cursor position.
    """
    pass

def get_cursor_start_pos() -> Tuple[float, float]:
    """
    Returns the initial cursor position at the start of the window's content region.

    :return: A tuple containing the x and y position of the cursor at the start of the content region.
    """
    pass

def is_rect_visible(size: Tuple[float, float]) -> bool:
    """
    Checks if a rectangle of the given size is visible in ImGui.

    This function takes a tuple representing the size (width, height) of a rectangle 
    and checks whether it is currently visible in the ImGui window.

    :param size: A tuple containing the width and height of the rectangle.
    :return: Returns True if the rectangle is visible, False otherwise.
    """
    pass


def push_style_color(idx: int, col: float) -> None:
    """Pushes a style color.
    Args: idx (int): Style color index, col (float): Color value.
    """
    pass

def pop_style_color(count: int = 1) -> None:
    """Pops a style color.
    Args: count (int): Number of style colors to pop.
    """
    pass

def push_style_var(idx: int, val: float) -> None:
    """Pushes a style variable.
    Args: idx (int): Style variable index, val (float): Variable value.
    """
    pass

def pop_style_var(count: int = 1) -> None:
    """Pops a style variable.
    Args: count (int): Number of style variables to pop.
    """
    pass

def push_item_width(item_width: float) -> None:
    """Pushes an item width.
    Args: item_width (float): Width to set.
    """
    pass

def pop_item_width() -> None:
    """Pops the item width."""
    pass

def push_text_wrap_pos(wrap_local_pos_x: float = 0.0) -> None:
    """Pushes text wrap position.
    Args: wrap_local_pos_x (float): Wrapping position.
    """
    pass

def pop_text_wrap_pos() -> None:
    """Pops the text wrap position."""
    pass

def push_allow_keyboard_focus(allow_keyboard_focus: bool) -> None:
    """Pushes keyboard focus setting.
    Args: allow_keyboard_focus (bool): Whether to allow keyboard focus.
    """
    pass

def pop_allow_keyboard_focus() -> None:
    """Pops the keyboard focus setting."""
    pass

def push_button_repeat(repeat: bool) -> None:
    """Pushes button repeat setting.
    Args: repeat (bool): Whether to enable repeat for button.
    """
    pass

def pop_button_repeat() -> None:
    """Pops the button repeat setting."""
    pass

def progress_bar(fraction: float) -> None:
    """Displays a progress bar.
    Args: fraction (float): Completion fraction.
    """
    pass

def bullet_text(text: str) -> None:
    """Displays bullet-point text.
    Args: text (str): Text to display.
    """
    pass

def begin(name: str) -> bool:
    """Begins a window.
    Args: name (str): Window name.
    Returns: bool: True if the window is open.
    """
    pass

def begin(name: str, flags: int) -> bool:
    """Begins a window with flags.
    Args: name (str): Window name, flags (int): Window flags.
    Returns: bool: True if the window is open.
    """
    pass

def begin(name: str, open: bool, flags: int) -> bool:
    """Begins a window with open state and flags.
    Args: name (str): Window name, open (bool): Window open state, flags (int): Window flags.
    Returns: bool: True if the window is open.
    """
    pass

def end() -> None:
    """Ends a window."""
    pass

def begin_child(str_id: str) -> bool:
    """Begins a child window.
    Args: str_id (str): Child window ID.
    Returns: bool: True if the child window is open.
    """
    pass

def end_child() -> None:
    """Ends a child window."""
    pass

def begin_group() -> None:
    """Begins a group."""
    pass

def end_group() -> None:
    """Ends a group."""
    pass

def separator() -> None:
    """Inserts a separator line."""
    pass

def same_line() -> None:
    """Moves the cursor to the same line."""
    pass

def spacing() -> None:
    """Inserts spacing."""
    pass

def indent() -> None:
    """Increases the indentation level."""
    pass

def unindent() -> None:
    """Decreases the indentation level."""
    pass

def is_window_collapsed() -> bool:
    """Checks if the window is collapsed.
    Returns: bool: True if collapsed.
    """
    pass

def columns(count: int) -> None:
    """Creates a column layout.
    Args: count (int): Number of columns.
    """
    pass

def next_column() -> None:
    """Moves to the next column."""
    pass

def end_columns() -> None:
    """Ends the column layout."""
    pass

def set_next_window_size(size: Tuple[float, float]) -> None:
    """Sets the next window size.
    Args: size (Tuple[float, float]): Width and height.
    """
    pass

def set_next_window_pos(pos: Tuple[float, float]) -> None:
    """Sets the next window position.
    Args: pos (Tuple[float, float]): X and Y position.
    """
    pass

def begin_menu_bar() -> bool:
    """Begins a menu bar.
    Returns: bool: True if menu bar is open.
    """
    pass

def end_menu_bar() -> None:
    """Ends a menu bar."""
    pass

def begin_main_menu_bar() -> bool:
    """Begins the main menu bar.
    Returns: bool: True if main menu bar is open.
    """
    pass

def end_main_menu_bar() -> None:
    """Ends the main menu bar."""
    pass

def begin_menu(label: str) -> bool:
    """Begins a menu.
    Args: label (str): Menu label.
    Returns: bool: True if the menu is open.
    """
    pass

def end_menu() -> None:
    """Ends a menu."""
    pass

def menu_item(label: str) -> bool:
    """Creates a menu item.
    Args: label (str): Item label.
    Returns: bool: True if the item is selected.
    """
    pass

def open_popup(str_id: str) -> None:
    """Opens a popup.
    Args: str_id (str): Popup ID.
    """
    pass

def begin_popup(str_id: str) -> bool:
    """Begins a popup.
    Args: str_id (str): Popup ID.
    Returns: bool: True if the popup is open.
    """
    pass

def end_popup() -> None:
    """Ends a popup."""
    pass

def begin_popup_modal(label: str) -> bool:
    """Begins a modal popup.
    Args: label (str): Modal label.
    Returns: bool: True if the modal is open.
    """
    pass

def end_popup_modal() -> None:
    """Ends a modal popup."""
    pass

def close_current_popup() -> None:
    """Closes the current popup."""
    pass

def begin_table(label: str, column: int) -> bool:
    """Begins a table.
    Args: label (str): Table label, column (int): Number of columns.
    Returns: bool: True if the table is open.
    """
    pass

def begin_table(label: str, column: int, flags: int) -> bool:
    """Begins a table with flags.
    Args: label (str): Table label, column (int): Number of columns, flags (int): Table flags.
    Returns: bool: True if the table is open.
    """
    pass

def end_table() -> None:
    """Ends a table."""
    pass

def table_setup_column(label: str) -> None:
    """Sets up a table column.
    Args: label (str): Column label.
    """
    pass

def table_setup_column(label: str, flags: str) -> None:
    """Sets up a table column with flags.
    Args: label (str): Column label, flags (str): Column flags.
    """
    pass

def table_headers_row() -> None:
    """Creates a row of table headers."""
    pass

def table_next_row() -> None:
    """Moves to the next row in a table."""
    pass

def table_next_column() -> bool:
    """Moves to the next column in a table.
    Returns: bool: True if successful.
    """
    pass

def table_set_column_index(index: int) -> bool:
    """Sets the current column index.
    Args: index (int): Column index.
    Returns: bool: True if successful.
    """
    pass

def begin_tab_bar(str_id: str) -> bool:
    """Begins a tab bar.
    Args: str_id (str): Tab bar ID.
    Returns: bool: True if successful.
    """
    pass

def end_tab_bar() -> None:
    """Ends a tab bar."""
    pass

def begin_tab_item(label: str) -> bool:
    """Begins a tab item.
    Args: label (str): Tab label.
    Returns: bool: True if successful.
    """
    pass

def end_tab_item() -> None:
    """Ends a tab item."""
    pass

def get_window_draw_list() -> Any:
    """Gets the current window's draw list.
    Returns: Any: Window draw list.
    """
    pass

def draw_list_add_line() -> None:
    """Adds a line to the draw list."""
    pass

def draw_list_add_rect() -> None:
    """Adds a rectangle to the draw list."""
    pass

def draw_list_add_circle() -> None:
    """Adds a circle to the draw list."""
    pass

def draw_list_add_text() -> None:
    """Adds text to the draw list."""
    pass

def get_window_pos() -> None:
    """Gets the current window position."""
    pass

def get_window_size() -> None:
    """Gets the current window size."""
    pass

def get_window_width() -> None:
    """Gets the current window width."""
    pass

def get_window_height() -> None:
    """Gets the current window height."""
    pass

def get_content_region_avail() -> None:
    """Gets the available content region."""
    pass

def get_content_region_max() -> None:
    """Gets the maximum content region."""
    pass

def get_window_content_region_min() -> None:
    """Gets the minimum content region in the window."""
    pass

def get_window_content_region_max() -> None:
    """Gets the maximum content region in the window."""
    pass

def is_mouse_clicked(button: int) -> bool:
    """Checks if the mouse button was clicked.
    Args: button (int): Mouse button index.
    Returns: bool: True if clicked.
    """
    pass

def is_item_hovered() -> bool:
    """Checks if the current item is hovered.
    Returns: bool: True if hovered.
    """
    pass

def is_item_active() -> bool:
    """Checks if the current item is active.
    Returns: bool: True if active.
    """
    pass

def is_key_pressed(key: int) -> bool:
    """Checks if a key is pressed.
    Args: key (int): Key index.
    Returns: bool: True if pressed.
    """
    pass

def show_demo_window() -> None:
    """Displays the demo window."""
    pass

def set_tooltip(text: str) -> None:
    """Sets a tooltip.
    Args: text (str): Tooltip text.
    """
    pass

def show_tooltip(text: str) -> None:
    """Displays a tooltip.
    Args: text (str): Tooltip text.
    """
    pass

def log_to_clipboard() -> None:
    """Logs content to the clipboard."""
    pass

def tree_node(label: str) -> bool:
    """Creates a tree node.
    Args: label (str): Tree node label.
    Returns: bool: True if the node is open.
    """
    pass

def tree_node(label: str, label_end: str) -> bool:
    """Creates a tree node with an end label.
    Args: label (str): Tree node label, label_end (str): End label.
    Returns: bool: True if the node is open.
    """
    pass

def tree_node_ex(label: str, flags: int) -> bool:
    """Creates an extended tree node.
    Args: label (str): Tree node label, flags (int): Tree node flags.
    Returns: bool: True if the node is open.
    """
    pass

def tree_node_ex(label: str, flags: int, label_end: str) -> bool:
    """Creates an extended tree node with an end label.
    Args: label (str): Tree node label, flags (int): Tree node flags, label_end (str): End label.
    Returns: bool: True if the node is open.
    """
    pass

def tree_pop() -> None:
    """Pops the current tree node."""
    pass

def get_tree_node_to_label_spacing() -> float:
    """Gets the spacing to the label in the tree node.
    Returns: float: Spacing value.
    """
    pass

def set_next_item_open(is_open: bool, cond: int = 0) -> None:
    """Sets the next item open state.
    Args: is_open (bool): Whether the item is open, cond (int): Conditions.
    """
    pass

def collapsing_header(label: str) -> bool:
    """Creates a collapsing header.
    Args: label (str): Header label.
    Returns: bool: True if open.
    """
    pass

def collapsing_header(label: str, flags: int) -> bool:
    """Creates a collapsing header with flags.
    Args: label (str): Header label, flags (int): Header flags.
    Returns: bool: True if open.
    """
    pass
