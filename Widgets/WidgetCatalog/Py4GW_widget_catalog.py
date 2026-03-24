from dataclasses import dataclass, field
import os
import tkinter as tk
import traceback
from tkinter import filedialog

import PyImGui

from Py4GWCoreLib import ColorPalette, IconsFontAwesome5, Py4GW
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.enums_src.IO_enums import ImGuiKey, Key
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import CatalogScope, WidgetCatalog, WidgetCatalogNode, WidgetCatalogQuery, WidgetHandler, get_widget_handler
from typing import Any, Callable, cast

MODULE_NAME = "Widgets"
GLOBAL = True

INI_PATH = "Widgets/WidgetCatalog"
INI_FILENAME = "WidgetCatalog.ini"
FLOATING_INI_FILENAME = "WidgetCatalogFloatingButton.ini"
SETUP_INI_FILENAME = "WidgetCatalogSetup.ini"
INI_KEY = ""
FLOATING_INI_KEY = ""
SETUP_INI_KEY = ""
INI_INIT = False
INITIALIZED = False
DEFAULT_WINDOW_WIDTH = 680.0
DEFAULT_WINDOW_HEIGHT = 430.0


def _default_gw_blue() -> Color:
    return cast(Color, ColorPalette.GetColor("GW_BLUE").copy())


def _default_gw_green() -> Color:
    return cast(Color, ColorPalette.GetColor("GW_GREEN").copy())


@dataclass
class address_bar_vars:
    button_size: int = 25
    gradient_start: Color = field(default_factory=_default_gw_blue)
    gradient_end: Color = field(default_factory=_default_gw_green)
    button_size_min: int = 18
    button_size_max: int = 64


@dataclass
class floating_icon_vars:
    position_x: float = 40.0
    position_y: float = 40.0
    button_size: float = 45.0
    button_size_min: float = 20.0
    button_size_max: float = 96.0
    idle_scale: float = 1.25
    idle_scale_min: float = 0.50
    idle_scale_max: float = 2.00
    hover_scale: float = 1.45
    hover_scale_min: float = 0.50
    hover_scale_max: float = 2.50


@dataclass
class tree_label_vars:
    indent_value: float = 10.0
    row_height_min: float = 16.0
    row_height_padding_y: float = 2.0
    row_padding_x: float = 8.0
    row_width_padding_right: float = 12.0
    row_corner_radius: float = 3.0
    tooltip_icon_spacing: float = 6.0


def _default_tree_label_vars() -> "tree_label_vars":
    return tree_label_vars()


@dataclass
class tree_vars:
    width: float = 150.0
    labels: tree_label_vars = field(default_factory=_default_tree_label_vars)


@dataclass
class detail_header_vars:
    row_height: float = 24.0
    total_width_min: float = 443.0
    favorite_width: float = 40.0
    config_width: float = 40.0
    name_width: float = 355.0


@dataclass
class detail_row_vars:
    row_height: float = 35.0
    icon_padding: float = 6.0
    icon_size_max: float = 28.0
    content_padding_x: float = 8.0
    content_gap_after_icon: float = 16.0


def _default_detail_header_vars() -> "detail_header_vars":
    return detail_header_vars()


def _default_detail_row_vars() -> "detail_row_vars":
    return detail_row_vars()


def _default_address_bar_vars() -> "address_bar_vars":
    return address_bar_vars()


def _default_floating_icon_vars() -> "floating_icon_vars":
    return floating_icon_vars()


def _default_tree_vars() -> "tree_vars":
    return tree_vars()


def _default_detail_vars() -> "detail_vars":
    return detail_vars()


@dataclass
class detail_vars:
    header: detail_header_vars = field(default_factory=_default_detail_header_vars)
    rows: detail_row_vars = field(default_factory=_default_detail_row_vars)


@dataclass
class config_vars:
    address_bar: address_bar_vars = field(default_factory=_default_address_bar_vars)
    floating_icon: floating_icon_vars = field(default_factory=_default_floating_icon_vars)


@dataclass
class ui_catalog_vars:
    tree: tree_vars = field(default_factory=_default_tree_vars)
    detail: detail_vars = field(default_factory=_default_detail_vars)


@dataclass
class browser_state:
    current_path: str = ""
    back_history: list[str] = field(default_factory=list)
    forward_history: list[str] = field(default_factory=list)


def _default_browser_state() -> "browser_state":
    return browser_state()


@dataclass
class browser_view_state:
    view_id: str
    label: str
    browser: browser_state = field(default_factory=_default_browser_state)
    expanded_paths: set[str] = field(default_factory=set)
    search_text: str = ""
    search_entries: list[str] = field(default_factory=list)


@dataclass
class runtime_state:
    show_adavanced: bool = False
    settings_loaded: bool = False
    expand_on_next_show: bool = False
    show_setup_window: bool = False
    setup_snapshot_captured: bool = False
    active_view_id: str = "contents"
    tree_width_pending_apply: bool = False
    tree_layout_revision: int = 0
    tree_layout_instance_id: int = 0


@dataclass
class address_bar_snapshot:
    button_size: int = 25
    gradient_start: Color = field(default_factory=_default_gw_blue)
    gradient_end: Color = field(default_factory=_default_gw_green)


@dataclass
class floating_icon_snapshot:
    icon_x: float = 40.0
    icon_y: float = 40.0
    icon_path: str = ""
    icon_size: float = 45.0
    idle_scale: float = 1.25
    hover_scale: float = 1.45


@dataclass
class tree_label_snapshot:
    width: float = 160.0
    indent_value: float = 10.0
    row_height_min: float = 16.0
    row_height_padding_y: float = 2.0
    row_padding_x: float = 8.0
    row_width_padding_right: float = 12.0
    row_corner_radius: float = 3.0
    tooltip_icon_spacing: float = 6.0


@dataclass
class detail_header_snapshot:
    row_height: float = 24.0
    total_width_min: float = 443.0
    favorite_width: float = 56.0
    config_width: float = 56.0
    name_width: float = 180.0


@dataclass
class detail_row_snapshot:
    row_height: float = 35.0
    icon_padding: float = 6.0
    icon_size_max: float = 28.0
    content_padding_x: float = 8.0
    content_gap_after_icon: float = 16.0


def _default_address_bar_snapshot() -> "address_bar_snapshot":
    return address_bar_snapshot()


def _default_floating_icon_snapshot() -> "floating_icon_snapshot":
    return floating_icon_snapshot()


def _default_tree_label_snapshot() -> "tree_label_snapshot":
    return tree_label_snapshot()


def _default_detail_header_snapshot() -> "detail_header_snapshot":
    return detail_header_snapshot()


def _default_detail_row_snapshot() -> "detail_row_snapshot":
    return detail_row_snapshot()


@dataclass
class setup_snapshot:
    address_bar: address_bar_snapshot = field(default_factory=_default_address_bar_snapshot)
    floating_icon: floating_icon_snapshot = field(default_factory=_default_floating_icon_snapshot)
    tree_labels: tree_label_snapshot = field(default_factory=_default_tree_label_snapshot)
    detail_header: detail_header_snapshot = field(default_factory=_default_detail_header_snapshot)
    detail_rows: detail_row_snapshot = field(default_factory=_default_detail_row_snapshot)


class WidgetCatalogTreeObject:
    pass


@dataclass
class WidgetCatalogTreeNodeObject(WidgetCatalogTreeObject):
    node: WidgetCatalogNode


class WidgetCatalogTreeSeparatorObject(WidgetCatalogTreeObject):
    pass


@dataclass
class WidgetCatalogTreeInputButtonObject(WidgetCatalogTreeObject):
    item_id: str
    text_value: str = ""
    button_caption: str = IconsFontAwesome5.ICON_SEARCH


@dataclass
class WidgetCatalogTreeLabelButtonObject(WidgetCatalogTreeObject):
    item_id: str
    label: str
    path: str = ""
    button_caption: str = IconsFontAwesome5.ICON_CIRCLE_XMARK


class WidgetCatalogTreePanel:
    MIN_RENDER_WIDTH = 25.0

    def __init__(self, window: "WidgetCatalogWindow"):
        self.window = window
        self.search_row = WidgetCatalogTreeInputButtonObject(item_id="tree_search", text_value="", button_caption=IconsFontAwesome5.ICON_SEARCH)

    @staticmethod
    def _clamp_dimension(value: float, minimum: float = 1.0) -> float:
        return max(minimum, float(value))

    def _get_safe_row_height(self) -> float:
        tree_labels = self.window.ui_catalog.tree.labels
        return self._clamp_dimension(
            max(PyImGui.get_text_line_height() + tree_labels.row_height_padding_y, tree_labels.row_height_min)
        )

    def _get_safe_row_width(self, row_width: float) -> float:
        available_width = self._clamp_dimension(PyImGui.get_content_region_avail()[0])
        return max(1.0, min(float(row_width), available_width))

    def _push_outline_row_colors(self, depth: int, max_depth: int, selected: bool) -> None:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Header, (0.0, 0.0, 0.0, 0.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, (0.0, 0.0, 0.0, 0.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, (0.0, 0.0, 0.0, 0.0))

    def _get_row_width(self, label: str, depth: int) -> float:
        tree_labels = self.window.ui_catalog.tree.labels
        indent_width = float(depth * tree_labels.indent_value)
        icon_width = PyImGui.calc_text_size(IconsFontAwesome5.ICON_CARET_DOWN)[0] + tree_labels.tooltip_icon_spacing
        text_width, _ = PyImGui.calc_text_size(label)
        return tree_labels.row_padding_x + indent_width + icon_width + text_width + tree_labels.row_width_padding_right

    def _get_max_width(self, root: WidgetCatalogNode, view: browser_view_state | None = None) -> float:
        expanded_paths = self.window._get_view_expanded_paths(view)
        widths: list[float] = []

        def collect(node: WidgetCatalogNode) -> None:
            if node.path:
                widths.append(self._get_row_width(node.name, node.depth))

            if node.path and node.children and node.path not in expanded_paths:
                return

            for child in WidgetCatalog.tree_children(node):
                collect(child)

        for child in WidgetCatalog.tree_children(root):
            collect(child)

        return max(widths, default=120.0)

    def _draw_selectable(self, item_id: str, depth: int, max_depth: int, selected: bool, row_width: float) -> bool:
        tree_labels = self.window.ui_catalog.tree.labels
        row_height_value = self._get_safe_row_height()
        row_width = self._clamp_dimension(row_width)
        self._push_outline_row_colors(depth, max_depth, selected)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 0.0, 0.0, 0.0))
        clicked = ImGui.selectable(f"##{item_id}", selected=selected, size=(row_width, row_height_value))
        PyImGui.pop_style_color(1)
        PyImGui.pop_style_color(3)

        item_min = PyImGui.get_item_rect_min()
        item_max = PyImGui.get_item_rect_max()
        fill, idle_border, border, hover_border = self.window._get_outline_palette(depth, max_depth)

        PyImGui.draw_list_add_rect_filled(
            item_min[0],
            item_min[1],
            item_max[0],
            item_max[1],
            fill.to_color(),
            tree_labels.row_corner_radius,
            0,
        )

        PyImGui.draw_list_add_rect(
            item_min[0],
            item_min[1],
            item_max[0],
            item_max[1],
            idle_border.to_color(),
            tree_labels.row_corner_radius,
            0,
            1.0,
        )

        if selected:
            PyImGui.draw_list_add_rect(
                item_min[0],
                item_min[1],
                item_max[0],
                item_max[1],
                border.to_color(),
                tree_labels.row_corner_radius,
                0,
                2.0,
            )
        elif PyImGui.is_item_hovered():
            PyImGui.draw_list_add_rect(
                item_min[0],
                item_min[1],
                item_max[0],
                item_max[1],
                hover_border.to_color(),
                tree_labels.row_corner_radius,
                0,
                1.0,
            )

        return clicked

    def _draw_node_object(self, item: WidgetCatalogTreeNodeObject, max_depth: int, row_width: float, view: browser_view_state | None = None) -> None:
        active_view = view or self.window._get_active_view()
        node = item.node
        selected = active_view.browser.current_path == node.path
        if self._draw_selectable(f"outline_{node.path}", node.depth, max_depth, selected, row_width):
            if node.children:
                if node.path in active_view.expanded_paths:
                    active_view.expanded_paths.remove(node.path)
                    self.window._navigate_to(node.path, expand_ancestors=False, view=active_view)
                else:
                    self.window._expand_outline_ancestors(node.path, view=active_view)
                    self.window._navigate_to(node.path, expand_ancestors=False, view=active_view)
            else:
                self.window._navigate_to(node.path, view=active_view)

        item_min = PyImGui.get_item_rect_min()
        item_max = PyImGui.get_item_rect_max()
        text_color = ImGui.get_style().Text.get_current()
        tree_labels = self.window.ui_catalog.tree.labels
        indent_width = float(node.depth * tree_labels.indent_value)
        icon_x = item_min[0] + tree_labels.row_padding_x + indent_width
        text_x = icon_x
        row_height = item_max[1] - item_min[1]
        text_y = item_min[1] + max((row_height - PyImGui.get_text_line_height()) * 0.5, 0.0)
        text_clip_min_x = item_min[0] + tree_labels.row_padding_x
        text_clip_max_x = max(item_max[0] - tree_labels.row_padding_x, text_clip_min_x + 1.0)

        PyImGui.push_clip_rect(
            text_clip_min_x,
            item_min[1],
            text_clip_max_x,
            item_max[1],
            True,
        )
        if node.children:
            icon = IconsFontAwesome5.ICON_CARET_DOWN if node.path in active_view.expanded_paths else IconsFontAwesome5.ICON_CARET_RIGHT
            icon_width, _ = PyImGui.calc_text_size(icon)
            PyImGui.draw_list_add_text(
                icon_x,
                text_y,
                text_color.color_int,
                icon,
            )
            text_x = icon_x + icon_width + tree_labels.tooltip_icon_spacing

        PyImGui.draw_list_add_text(
            text_x,
            text_y,
            text_color.color_int,
            node.name,
        )
        PyImGui.pop_clip_rect()

        if PyImGui.is_item_hovered():
            folder_count = len(WidgetCatalog.tree_children(node))
            widget_count = len(node.widget_ids)
            PyImGui.set_tooltip(f"/{node.path}\nFolders: {folder_count}\nWidgets: {widget_count}")

    def _draw_input_button_object(self, item: WidgetCatalogTreeInputButtonObject, max_depth: int, row_width: float, view: browser_view_state) -> bool:
        row_width = self._get_safe_row_width(row_width)
        row_height = self._get_safe_row_height()
        button_size = min(row_height, max(1.0, row_width))
        remaining_width = max(row_width - button_size, 0.0)
        spacing = min(4.0, remaining_width)
        input_width = max(row_width - button_size - spacing, 1.0)

        PyImGui.push_item_width(input_width)
        _, item.text_value = ImGui.search_field(f"##{item.item_id}_input", item.text_value, placeholder="Search...")
        PyImGui.pop_item_width()
        view.search_text = item.text_value
        submitted = (
            (PyImGui.is_item_active() or PyImGui.is_item_focused())
            and (
                PyImGui.is_key_pressed(ImGuiKey.Enter.value)
                or PyImGui.is_key_pressed(ImGuiKey.KeypadEnter.value)
            )
        )
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Press <Enter> or click the search button to search")
        PyImGui.same_line(0, spacing)
        clicked = ImGui.icon_button(f"{item.button_caption}##{item.item_id}_button", width=button_size, height=button_size)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Search")
        return submitted or clicked

    def _draw_label_button_object(self, item: WidgetCatalogTreeLabelButtonObject, max_depth: int, row_width: float) -> str:
        tree_labels = self.window.ui_catalog.tree.labels
        row_width = self._get_safe_row_width(row_width)
        row_height = self._get_safe_row_height()
        button_size = min(row_height, max(1.0, row_width))
        remaining_width = max(row_width - button_size, 0.0)
        spacing = min(4.0, remaining_width)
        button_right_padding = tree_labels.row_padding_x
        row_selectable_width = max(min(row_width - button_size - spacing - button_right_padding + 6.0, row_width), 1.0)
        row_clicked = self._draw_selectable(item.item_id, 1, max_depth, False, row_selectable_width)

        item_min = PyImGui.get_item_rect_min()
        item_max = PyImGui.get_item_rect_max()
        actual_row_height = item_max[1] - item_min[1]
        text_y = item_min[1] + max((actual_row_height - PyImGui.get_text_line_height()) * 0.5, 0.0)
        text_x = item_min[0] + tree_labels.row_padding_x
        button_x = item_max[0] + spacing
        button_y = item_min[1] + max((actual_row_height - button_size) * 0.5, 0.0)
        text_clip_max_x = max(item_max[0] - tree_labels.row_padding_x, text_x + 1.0)

        PyImGui.push_clip_rect(
            text_x,
            item_min[1],
            text_clip_max_x,
            item_max[1],
            True,
        )
        search_icon_font_size = max(int(PyImGui.get_text_line_height() * 0.8), 10)
        ImGui.push_font("Regular", search_icon_font_size)
        search_icon_width, search_icon_height = PyImGui.calc_text_size(IconsFontAwesome5.ICON_SEARCH)
        search_icon_y = item_min[1] + max((actual_row_height - search_icon_height) * 0.5, 0.0)
        PyImGui.draw_list_add_text(
            text_x,
            search_icon_y,
            ImGui.get_style().Text.get_current().color_int,
            IconsFontAwesome5.ICON_SEARCH,
        )
        ImGui.pop_font()
        PyImGui.draw_list_add_text(
            text_x + search_icon_width + tree_labels.tooltip_icon_spacing,
            text_y,
            ImGui.get_style().Text.get_current().color_int,
            item.label,
        )
        PyImGui.pop_clip_rect()

        PyImGui.set_cursor_screen_pos(button_x, button_y)
        button_clicked = PyImGui.invisible_button(f"##{item.item_id}_button", button_size, button_size)
        button_min = PyImGui.get_item_rect_min()
        button_max = PyImGui.get_item_rect_max()
        button_hovered = PyImGui.is_item_hovered()
        button_active = PyImGui.is_item_active()

        button_fill = Color(120, 26, 26, 180)
        if button_hovered:
            button_fill = Color(165, 36, 36, 210)
        if button_active:
            button_fill = Color(195, 48, 48, 230)
        button_border = Color(220, 90, 90, 235)

        PyImGui.draw_list_add_rect_filled(
            button_min[0],
            button_min[1],
            button_max[0],
            button_max[1],
            button_fill.to_color(),
            tree_labels.row_corner_radius,
            0,
        )
        PyImGui.draw_list_add_rect(
            button_min[0],
            button_min[1],
            button_max[0],
            button_max[1],
            button_border.to_color(),
            tree_labels.row_corner_radius,
            0,
            1.0,
        )

        icon_font_size = max(int(PyImGui.get_text_line_height() * 0.8), 10)
        ImGui.push_font("Regular", icon_font_size)
        icon_width, icon_height = PyImGui.calc_text_size(item.button_caption)
        icon_x = button_min[0] + max(((button_max[0] - button_min[0]) - icon_width) * 0.5, 0.0)
        icon_y = button_min[1] + max(((button_max[1] - button_min[1]) - icon_height) * 0.5, 0.0)
        PyImGui.draw_list_add_text(
            icon_x,
            icon_y,
            Color(255, 230, 230, 255).to_color(),
            item.button_caption,
        )
        ImGui.pop_font()

        if button_hovered:
            PyImGui.set_tooltip("Close search")

        if button_clicked:
            return "close"
        if row_clicked:
            return "select"
        return ""

    def _draw_object(self, item: WidgetCatalogTreeObject, max_depth: int, row_width: float, view: browser_view_state | None = None) -> str | bool:
        if isinstance(item, WidgetCatalogTreeNodeObject):
            self._draw_node_object(item, max_depth, row_width, view=view)
            return False
        elif isinstance(item, WidgetCatalogTreeInputButtonObject):
            return self._draw_input_button_object(item, max_depth, row_width, view=view or self.window._get_active_view())
        elif isinstance(item, WidgetCatalogTreeLabelButtonObject):
            return self._draw_label_button_object(item, max_depth, row_width)
        elif isinstance(item, WidgetCatalogTreeSeparatorObject):
            PyImGui.separator()
            return False
        return False

    def _draw_node_rows(self, node: WidgetCatalogNode, max_depth: int, row_width: float, view: browser_view_state | None = None) -> None:
        active_view = view or self.window._get_active_view()
        if node.path:
            self._draw_object(WidgetCatalogTreeNodeObject(node), max_depth, row_width, view=active_view)

        if node.path and node.children and node.path not in active_view.expanded_paths:
            return

        for child in WidgetCatalog.tree_children(node):
            self._draw_node_rows(child, max_depth, row_width, view=active_view)

    def _build_root_objects(self, browser_root: WidgetCatalogNode) -> list[WidgetCatalogTreeObject]:
        objects: list[WidgetCatalogTreeObject] = []
        active_view = self.window._get_active_view()
        virtual_folders, regular_folders = self.window._get_root_folder_groups(browser_root)

        for index, child in enumerate(virtual_folders):
            if child.path == self.window.SEARCH_PATH:
                self.search_row.text_value = active_view.search_text
                objects.append(self.search_row)
                for entry_index, entry_label in enumerate(active_view.search_entries):
                    objects.append(
                        WidgetCatalogTreeLabelButtonObject(
                            item_id=f"tree_search_entry_{active_view.view_id}_{entry_index}",
                            label=entry_label,
                            path=f"{self.window.SEARCH_ENTRY_PATH_PREFIX}{entry_index}",
                        )
                    )
            else:
                objects.append(WidgetCatalogTreeNodeObject(child))
            if index == 0 and len(virtual_folders) > 1:
                objects.append(WidgetCatalogTreeSeparatorObject())

        if virtual_folders and regular_folders:
            objects.append(WidgetCatalogTreeSeparatorObject())

        for child in regular_folders:
            objects.append(WidgetCatalogTreeNodeObject(child))

        return objects

    def draw(self, browser_root: WidgetCatalogNode, view: browser_view_state | None = None) -> None:
        active_view = view or self.window._get_active_view()
        max_depth = self.window._get_max_path_depth(browser_root)
        available_width = self._clamp_dimension(PyImGui.get_content_region_avail()[0])
        if available_width < self.MIN_RENDER_WIDTH:
            PyImGui.text_disabled("...")
            return
        row_width = max(1.0, min(self._get_max_width(browser_root, view=active_view), available_width))

        for item in self._build_root_objects(browser_root):
            if isinstance(item, WidgetCatalogTreeNodeObject) and not self.window._is_virtual_root_path(item.node.path):
                self._draw_node_rows(item.node, max_depth, row_width, view=active_view)
            else:
                action_triggered = self._draw_object(item, max_depth, row_width, view=active_view)
                if action_triggered and isinstance(item, WidgetCatalogTreeInputButtonObject):
                    search_value = item.text_value.strip()
                    if search_value and search_value not in active_view.search_entries:
                        active_view.search_entries.append(search_value)
                        self.window._save_search_entries(active_view)
                        self.window._navigate_to(
                            f"{self.window.SEARCH_ENTRY_PATH_PREFIX}{len(active_view.search_entries) - 1}",
                            sync_outline=True,
                            view=active_view,
                        )
                elif action_triggered == "select" and isinstance(item, WidgetCatalogTreeLabelButtonObject):
                    if item.path:
                        self.window._navigate_to(item.path, sync_outline=True, view=active_view)
                elif action_triggered == "close" and isinstance(item, WidgetCatalogTreeLabelButtonObject):
                    try:
                        removed_index = active_view.search_entries.index(item.label)
                        active_view.search_entries.remove(item.label)
                        self.window._save_search_entries(active_view)
                        removed_path = f"{self.window.SEARCH_ENTRY_PATH_PREFIX}{removed_index}"
                        if active_view.browser.current_path == removed_path:
                            self.window._navigate_to("", sync_outline=True, view=active_view)
                    except ValueError:
                        pass


class WidgetCatalogDetailObject:
    pass


class WidgetCatalogDetailSeparatorObject(WidgetCatalogDetailObject):
    pass


@dataclass
class WidgetCatalogDetailFolderObject(WidgetCatalogDetailObject):
    row_id: str
    label: str
    path: str
    icon_key: str = "folder"
    go_up: bool = False


@dataclass
class WidgetCatalogDetailWidgetObject(WidgetCatalogDetailObject):
    row_id: str
    widget: Any


class WidgetCatalogDetailPanel:
    MIN_RENDER_WIDTH = 25.0
    MIN_RENDER_HEIGHT = 25.0
    MIN_ROW_RENDER_WIDTH = 25.0
    MIN_ROW_RENDER_HEIGHT = 12.0

    def __init__(self, window: "WidgetCatalogWindow"):
        self.window = window

    @staticmethod
    def _clamp_dimension(value: float, minimum: float = 1.0) -> float:
        return max(minimum, float(value))

    @staticmethod
    def _clamp_non_negative(value: float) -> float:
        return max(0.0, float(value))

    @staticmethod
    def _fit_text_to_width(text: str, max_width: float) -> str:
        if max_width <= 0.0 or not text:
            return ""

        text_width, _ = PyImGui.calc_text_size(text)
        if text_width <= max_width:
            return text

        ellipsis = "..."
        ellipsis_width, _ = PyImGui.calc_text_size(ellipsis)
        if ellipsis_width > max_width:
            return ""

        low = 0
        high = len(text)
        best = ""
        while low <= high:
            mid = (low + high) // 2
            candidate = text[:mid] + ellipsis
            candidate_width, _ = PyImGui.calc_text_size(candidate)
            if candidate_width <= max_width:
                best = candidate
                low = mid + 1
            else:
                high = mid - 1

        return best

    def _column_widths(self, total_width: float) -> tuple[float, float, float]:
        detail_header = self.window.ui_catalog.detail.header
        total_width = self._clamp_dimension(total_width)
        favorite_width = min(self._clamp_non_negative(detail_header.favorite_width), max(total_width - 1.0, 0.0))
        config_width = min(self._clamp_non_negative(detail_header.config_width), max(total_width - 1.0 - favorite_width, 0.0))
        name_width = max(total_width - favorite_width - config_width, 1.0)
        return name_width, favorite_width, config_width

    def _draw_header_row(self, total_width: float, row_height: float) -> None:
        total_width = self._clamp_dimension(total_width)
        row_height = self._clamp_dimension(row_height)
        if row_height < self.MIN_ROW_RENDER_HEIGHT:
            ImGui.dummy(total_width, max(row_height, 1.0))
            return
        x, y = PyImGui.get_cursor_screen_pos()
        name_width, favorite_width, config_width = self._column_widths(total_width)
        bg = Color(36, 49, 64, 255)
        border = Color(70, 70, 70, 180)

        PyImGui.draw_list_add_rect_filled(x, y, x + total_width, y + row_height, bg.to_color(), 0.0, 0)
        PyImGui.draw_list_add_rect(x, y, x + total_width, y + row_height, border.to_color(), 0.0, 0, 1.0)

        text_y = y + max((row_height - PyImGui.get_text_line_height()) * 0.5, 0.0)
        text_color = ImGui.get_style().Text.get_current().color_int
        col_x = x
        for label, width in [
            ("Name", name_width),
            ("Fav", favorite_width),
            ("Cfg", config_width),
        ]:
            if width >= 12.0:
                PyImGui.draw_list_add_text(col_x + 6.0, text_y, text_color, label)
            col_x += width

        ImGui.dummy(total_width, row_height)

    def _draw_entry_primary(
        self,
        item_min: tuple[float, float],
        item_max: tuple[float, float],
        content_width: float,
        texture_path: str | None,
        uv0: tuple[float, float],
        uv1: tuple[float, float],
        label: str,
        image_size: float,
    ) -> None:
        detail_rows = self.window.ui_catalog.detail.rows
        text_color = ImGui.get_style().Text.get_current().color_int
        content_width = self._clamp_dimension(content_width)
        content_left = item_min[0] + detail_rows.content_padding_x
        content_right = item_min[0] + max(content_width - detail_rows.content_padding_x, detail_rows.content_padding_x)
        clip_max_x = max(content_right, content_left + 1.0)

        PyImGui.push_clip_rect(
            content_left,
            item_min[1],
            clip_max_x,
            item_max[1],
            True,
        )

        if texture_path and (content_right - content_left) > 2.0:
            safe_image_size = min(
                max(1.0, image_size),
                max(item_max[1] - item_min[1], 1.0),
                max(content_right - content_left, 1.0),
            )
            icon_y = item_min[1] + max((item_max[1] - item_min[1] - safe_image_size) * 0.5, 0.0)
            ImGui.DrawTextureInDrawList(
                pos=(content_left, icon_y),
                size=(safe_image_size, safe_image_size),
                texture_path=texture_path,
                uv0=uv0,
                uv1=uv1,
            )
            text_x = content_left + safe_image_size + detail_rows.content_gap_after_icon
        else:
            text_x = content_left

        text_y = item_min[1] + max((item_max[1] - item_min[1] - PyImGui.get_text_line_height()) * 0.5, 0.0)
        text_max_width = max(content_right - text_x, 0.0)
        display_label = self._fit_text_to_width(label, text_max_width)
        PyImGui.draw_list_add_text(text_x, text_y, text_color, display_label)
        PyImGui.pop_clip_rect()

    def _draw_explorer_row(
        self,
        row_id: str,
        total_width: float,
        row_height: float,
        entry_texture: str | None,
        entry_uv0: tuple[float, float],
        entry_uv1: tuple[float, float],
        entry_label: str,
        on_primary_click,
        active: bool = False,
        favorite_texture: str | None = None,
        favorite_uv0: tuple[float, float] = (0.0, 0.0),
        favorite_uv1: tuple[float, float] = (1.0, 1.0),
        on_favorite_click=None,
        config_texture: str | None = None,
        config_uv0: tuple[float, float] = (0.0, 0.0),
        config_uv1: tuple[float, float] = (1.0, 1.0),
        on_config_click=None,
    ) -> bool:
        detail_rows = self.window.ui_catalog.detail.rows
        total_width = self._clamp_dimension(total_width)
        row_height = self._clamp_dimension(row_height)
        if total_width < self.MIN_ROW_RENDER_WIDTH or row_height < self.MIN_ROW_RENDER_HEIGHT:
            ImGui.dummy(max(total_width, 1.0), max(row_height, 1.0))
            return False
        name_width, favorite_width, config_width = self._column_widths(total_width)
        x, y = PyImGui.get_cursor_screen_pos()
        row_bg = Color(22, 22, 28, 210)
        hover_bg = Color(32, 38, 46, 230)
        active_bg = Color(30, 56, 38, 220)
        active_hover_bg = Color(38, 68, 46, 235)
        border = Color(55, 55, 60, 160)
        active_border = ColorPalette.GetColor("GW_GREEN").copy()

        clicked_primary = ImGui.invisible_button(f"##{row_id}_primary", name_width, row_height)
        item_min = PyImGui.get_item_rect_min()
        item_max = PyImGui.get_item_rect_max()
        hovered = PyImGui.is_item_hovered()
        fill = active_hover_bg if active and hovered else active_bg if active else hover_bg if hovered else row_bg
        row_border = active_border if active else border
        border_thickness = 2.0 if active else 1.0
        PyImGui.draw_list_add_rect_filled(x, y, x + total_width, y + row_height, fill.to_color(), 0.0, 0)
        PyImGui.draw_list_add_rect(x, y, x + total_width, y + row_height, row_border.to_color(), 0.0, 0, border_thickness)
        self._draw_entry_primary(
            item_min,
            item_max,
            name_width,
            entry_texture,
            entry_uv0,
            entry_uv1,
            entry_label,
            min(max(row_height - detail_rows.icon_padding, 1.0), detail_rows.icon_size_max),
        )

        if clicked_primary and on_primary_click:
            on_primary_click()

        current_x = x + name_width

        PyImGui.set_cursor_screen_pos(current_x, y)
        if favorite_texture and on_favorite_click and favorite_width > 1.0:
            button_size = min(max(row_height - detail_rows.icon_padding, 1.0), detail_rows.icon_size_max, favorite_width, row_height)
            favorite_toggled = self.window._draw_centered_texture_toggle_button(
                f"{row_id}_fav",
                False,
                favorite_texture,
                row_height,
                button_size,
                button_size,
                uv0=favorite_uv0,
                uv1=favorite_uv1,
            )
            if favorite_toggled:
                on_favorite_click()
        else:
            ImGui.dummy(max(favorite_width, 0.0), row_height)
        current_x += favorite_width

        PyImGui.set_cursor_screen_pos(current_x, y)
        if config_texture and on_config_click and config_width > 1.0:
            button_size = min(max(row_height - detail_rows.icon_padding, 1.0), detail_rows.icon_size_max, config_width, row_height)
            toggled = self.window._draw_centered_texture_toggle_button(
                f"{row_id}_cfg",
                False,
                config_texture,
                row_height,
                button_size,
                button_size,
                uv0=config_uv0,
                uv1=config_uv1,
            )
            if toggled:
                on_config_click()
        else:
            ImGui.dummy(max(config_width, 0.0), row_height)

        PyImGui.set_cursor_screen_pos(x, y)
        ImGui.dummy(total_width, row_height)
        return hovered

    def _build_objects(
        self,
        snapshot,
        node: WidgetCatalogNode,
        favorite_ids: set[str],
        can_go_up: bool,
        view: browser_view_state,
    ) -> list[WidgetCatalogDetailObject]:
        folders = WidgetCatalog.tree_children(node)
        virtual_folders: list[WidgetCatalogNode] = []
        regular_folders: list[WidgetCatalogNode] = folders
        if not node.path:
            virtual_folders, regular_folders = self.window._get_root_folder_groups(node)
            virtual_folders = [child for child in virtual_folders if child.path != self.window.SEARCH_PATH]
        widgets = [snapshot.widgets_by_id.get(widget_id) for widget_id in node.widget_ids]
        widgets = cast(list[Any], [widget for widget in widgets if widget is not None])

        objects: list[WidgetCatalogDetailObject] = []
        if can_go_up:
            objects.append(
                WidgetCatalogDetailFolderObject(
                    row_id=f"detail_go_up_{view.view_id}",
                    label="..",
                    path="",
                    icon_key="folder_up",
                    go_up=True,
                )
            )

        for index, child in enumerate(virtual_folders):
            objects.append(
                WidgetCatalogDetailFolderObject(
                    row_id=f"detail_virtual_folder_{view.view_id}_{child.path}",
                    label=child.name,
                    path=child.path,
                )
            )
            if index == 0 and len(virtual_folders) > 1:
                objects.append(WidgetCatalogDetailSeparatorObject())

        if virtual_folders and regular_folders:
            objects.append(WidgetCatalogDetailSeparatorObject())

        for child in regular_folders:
            objects.append(
                WidgetCatalogDetailFolderObject(
                    row_id=f"detail_folder_{view.view_id}_{child.path}",
                    label=child.name,
                    path=child.path,
                )
            )

        for widget in widgets:
            objects.append(
                WidgetCatalogDetailWidgetObject(
                    row_id=f"widget_{view.view_id}_{widget.folder_script_name}",
                    widget=widget,
                )
            )

        return objects

    def draw_contents_list(
        self,
        snapshot,
        node: WidgetCatalogNode,
        favorite_ids: set[str],
        can_go_up: bool,
        view: browser_view_state,
    ) -> None:
        detail_header = self.window.ui_catalog.detail.header
        detail_rows = self.window.ui_catalog.detail.rows
        row_height = self._clamp_dimension(detail_rows.row_height)
        objects = self._build_objects(snapshot, node, favorite_ids, can_go_up, view=view)

        if not objects:
            PyImGui.text_disabled("No contents in this location.")
            return

        if not ImGui.begin_child(f"##detail_contents_list_{view.view_id}", (0, 0), False, PyImGui.WindowFlags.HorizontalScrollbar):
            return

        content_avail_width, content_avail_height = PyImGui.get_content_region_avail()
        content_avail_width = self._clamp_non_negative(content_avail_width)
        content_avail_height = self._clamp_non_negative(content_avail_height)
        if content_avail_width < self.MIN_RENDER_WIDTH or content_avail_height < self.MIN_RENDER_HEIGHT:
            PyImGui.text_disabled("...")
            ImGui.end_child()
            return
        if content_avail_width < 8.0 or content_avail_height < max(row_height, self._clamp_dimension(detail_header.row_height)):
            ImGui.end_child()
            return
        configured_total_width = detail_header.name_width + detail_header.favorite_width + detail_header.config_width
        if content_avail_width < 80.0:
            total_width = max(content_avail_width, 1.0)
        else:
            total_width = max(content_avail_width, detail_header.total_width_min, configured_total_width)
        self._draw_header_row(total_width, self._clamp_dimension(detail_header.row_height))

        for item in objects:
            if isinstance(item, WidgetCatalogDetailSeparatorObject):
                PyImGui.separator()
            elif isinstance(item, WidgetCatalogDetailFolderObject):
                folder_uv0, folder_uv1 = self.window.FOLDER_ICON_UVS[item.icon_key]
                self._draw_explorer_row(
                    item.row_id,
                    total_width,
                    row_height,
                    self.window.FOLDER_ICON_ATLAS,
                    folder_uv0,
                    folder_uv1,
                    item.label,
                    on_primary_click=(lambda v=view: self.window._go_up(view=v)) if item.go_up else (lambda path=item.path, v=view: self.window._navigate_to(path, sync_outline=True, view=v)),
                )
            elif isinstance(item, WidgetCatalogDetailWidgetObject):
                widget = item.widget
                label = widget.name if widget.name else widget.folder_script_name
                is_favorite = widget.folder_script_name in favorite_ids
                has_config = bool(widget.has_configure_property)
                has_icon = not WidgetCatalog._has_missing_icon(widget)
                favorite_uv0, favorite_uv1 = self.window.FOLDER_ICON_UVS["heart_full" if is_favorite else "heart_empty"]
                config_uv0, config_uv1 = self.window.FOLDER_ICON_UVS["config_active" if widget.configuring else "config"]
                hovered = self._draw_explorer_row(
                    item.row_id,
                    total_width,
                    row_height,
                    widget.image if has_icon else None,
                    (0.0, 0.0),
                    (1.0, 1.0),
                    label if has_icon else f"{IconsFontAwesome5.ICON_FILE_CODE} {label}",
                    on_primary_click=lambda w=widget: self.window._set_widget_active(w, not w.enabled),
                    active=widget.enabled,
                    favorite_texture=self.window.FOLDER_ICON_ATLAS,
                    favorite_uv0=favorite_uv0,
                    favorite_uv1=favorite_uv1,
                    on_favorite_click=lambda w=widget, fav=is_favorite: self.window._set_widget_favorite(w, not fav),
                    config_texture=self.window.FOLDER_ICON_ATLAS if has_config else None,
                    config_uv0=config_uv0,
                    config_uv1=config_uv1,
                    on_config_click=(lambda w=widget: w.set_configuring(not w.configuring)) if has_config else None,
                )
                if hovered:
                    self.window._draw_widget_hover_card(widget)

        ImGui.end_child()

    def draw_panel(self, snapshot, browser_root: WidgetCatalogNode, view: browser_view_state | None = None) -> None:
        active_view = view or self.window._get_active_view()
        panel_avail_width, panel_avail_height = PyImGui.get_content_region_avail()
        if self._clamp_non_negative(panel_avail_width) < self.MIN_RENDER_WIDTH or self._clamp_non_negative(panel_avail_height) < self.MIN_RENDER_HEIGHT:
            PyImGui.text_disabled("...")
            return
        current_node = self.window._find_node(browser_root, active_view.browser.current_path)
        favorite_ids = self.window._get_favorite_ids()
        can_go_up = bool(active_view.browser.current_path) and active_view.browser.current_path not in {self.window.FAVORITES_PATH, self.window.ACTIVE_PATH}

        if ImGui.begin_child(f"##widget_detail_{active_view.view_id}", (0, 0), True):
            self.draw_contents_list(
                snapshot,
                current_node,
                favorite_ids,
                can_go_up=can_go_up,
                view=active_view,
            )

        ImGui.end_child()


class WidgetCatalogWindow:
    SEARCH_PATH = "@search"
    SEARCH_ENTRY_PATH_PREFIX = "@search_entry_"
    FAVORITES_PATH = "@favorites"
    ACTIVE_PATH = "@active"
    FOLDER_ICON_ATLAS = os.path.join(Py4GW.Console.get_projects_path(),"Widgets","WidgetCatalog", "folder icons.png")
    FOLDER_ICON_UVS = {
        "folder_up": ((0.0, 0.0), (0.5, 0.33)),
        "config_active": ((0.5, 0.0), (1.0, 0.33)),
        "folder": ((0.0, 0.33), (0.5, 0.66)),
        "config": ((0.5, 0.33), (1.0, 0.66)),
        "heart_empty": ((0.0, 0.66), (0.5, 1.0)),
        "heart_full": ((0.5, 0.66), (1.0, 1.0)),
    }

    def __init__(self, ini_key: str, module_name: str, widget_manager: WidgetHandler, floating_ini_key: str = "", setup_ini_key: str = ""):
        self.ini_key = ini_key
        self.floating_ini_key = floating_ini_key or ini_key
        self.setup_ini_key = setup_ini_key or ini_key
        self.module_name = module_name
        self.widget_manager = widget_manager
        self.config = config_vars()
        self.ui_catalog = ui_catalog_vars()
        self.views: dict[str, browser_view_state] = {
            "contents": browser_view_state(view_id="contents", label="Contents"),
        }
        self.runtime = runtime_state()
        self.runtime.tree_layout_instance_id = id(self)
        self.tree_panel = WidgetCatalogTreePanel(self)
        self.detail_panel = WidgetCatalogDetailPanel(self)
        self.setup_snapshot = setup_snapshot()
        self.floating_button = ImGui.FloatingIcon(
            icon_path=os.path.join(Py4GW.Console.get_projects_path(), "python_icon_round.png"),
            window_id="##widget_catalog_floating_button",
            window_name="Widget Catalog Toggle",
            tooltip_visible="Hide UI",
            tooltip_hidden="Show UI",
            toggle_ini_key=self.floating_ini_key,
            toggle_var_name="show_main_window",
            toggle_default=True,
            on_toggle=self._on_window_visibility_toggled,
            draw_callback=lambda: self._draw_window(),
        )
        
        self.max_path_depth = 0

    @staticmethod
    def _projects_root() -> str:
        return os.path.normpath(Py4GW.Console.get_projects_path())

    @classmethod
    def _default_floating_icon_path(cls) -> str:
        return os.path.join(cls._projects_root(), "python_icon_round.png")

    @classmethod
    def _default_floating_icon_relpath(cls) -> str:
        return "python_icon_round.png"

    @classmethod
    def _texture_to_ini_path(cls, path: str) -> str:
        if not path:
            return ""

        normalized = os.path.normpath(path)
        root = cls._projects_root()
        try:
            rel_path = os.path.relpath(normalized, root)
        except ValueError:
            rel_path = normalized

        if not rel_path.startswith(".."):
            return rel_path.replace("\\", "/")
        return normalized.replace("\\", "/")

    @classmethod
    def _texture_from_ini_path(cls, path: str) -> str:
        if not path:
            return cls._default_floating_icon_path()

        normalized = os.path.normpath(path)
        if os.path.isabs(normalized):
            return normalized
        return os.path.normpath(os.path.join(cls._projects_root(), normalized))

    @classmethod
    def _texture_display_path(cls, path: str) -> str:
        return cls._texture_to_ini_path(path)

    def _manager_ini_key(self) -> str:
        manager_ini_key = getattr(self.widget_manager, "MANAGER_INI_KEY", "")
        return manager_ini_key or self.ini_key

    def _parse_color(self, value: object, default: Color) -> Color:
        if isinstance(value, Color):
            return value.copy()
        if isinstance(value, str):
            try:
                return Color.from_rgba_string(value)
            except ValueError:
                return default.copy()
        return default.copy()

    def _ensure_config_vars(self) -> None:
        IniManager().add_bool(self.ini_key, "show_adavanced", "Configuration", "show_adavanced", False)
        IniManager().add_int(self.ini_key, "button_size", "Navigation", "button_size", self.config.address_bar.button_size)
        IniManager().add_str(self.ini_key, "gradient_start", "Navigation", "gradient_start", self.config.address_bar.gradient_start.to_rgba_string())
        IniManager().add_str(self.ini_key, "gradient_end", "Navigation", "gradient_end", self.config.address_bar.gradient_end.to_rgba_string())

    def _ensure_floating_config_vars(self) -> None:
        IniManager().add_str(self.ini_key, "floating_icon_path", "Floating Icon", "icon_path", self._texture_to_ini_path(self.floating_button.icon_path))
        IniManager().add_float(self.ini_key, "floating_button_size", "Floating Icon", "button_size", float(self.config.floating_icon.button_size))
        IniManager().add_float(self.ini_key, "floating_idle_icon_scale", "Floating Icon", "idle_icon_scale", float(self.config.floating_icon.idle_scale))
        IniManager().add_float(self.ini_key, "floating_hover_icon_scale", "Floating Icon", "hover_icon_scale", float(self.config.floating_icon.hover_scale))

    def _ensure_ui_catalog_vars(self) -> None:
        tree_config = self.ui_catalog.tree
        tree_labels = self.ui_catalog.tree.labels
        detail_header = self.ui_catalog.detail.header
        detail_rows = self.ui_catalog.detail.rows

        IniManager().add_float(self.ini_key, "tree_width", "Tree", "width", float(tree_config.width))
        IniManager().add_float(self.ini_key, "tree_indent_value", "Tree", "indent_value", float(tree_labels.indent_value))
        IniManager().add_float(self.ini_key, "tree_row_height_min", "Tree", "row_height_min", float(tree_labels.row_height_min))
        IniManager().add_float(self.ini_key, "tree_row_height_padding_y", "Tree", "row_height_padding_y", float(tree_labels.row_height_padding_y))
        IniManager().add_float(self.ini_key, "tree_row_padding_x", "Tree", "row_padding_x", float(tree_labels.row_padding_x))
        IniManager().add_float(self.ini_key, "tree_row_width_padding_right", "Tree", "row_width_padding_right", float(tree_labels.row_width_padding_right))
        IniManager().add_float(self.ini_key, "tree_row_corner_radius", "Tree", "row_corner_radius", float(tree_labels.row_corner_radius))
        IniManager().add_float(self.ini_key, "tree_tooltip_icon_spacing", "Tree", "tooltip_icon_spacing", float(tree_labels.tooltip_icon_spacing))

        IniManager().add_float(self.ini_key, "detail_header_row_height", "Detail Panel", "header_row_height", float(detail_header.row_height))
        IniManager().add_float(self.ini_key, "detail_total_width_min", "Detail Panel", "total_width_min", float(detail_header.total_width_min))
        IniManager().add_float(self.ini_key, "detail_favorite_width", "Detail Panel", "favorite_width", float(detail_header.favorite_width))
        IniManager().add_float(self.ini_key, "detail_config_width", "Detail Panel", "config_width", float(detail_header.config_width))
        IniManager().add_float(self.ini_key, "detail_name_width", "Detail Panel", "name_width", float(detail_header.name_width))

        IniManager().add_float(self.ini_key, "detail_row_height", "Detail Panel", "row_height", float(detail_rows.row_height))
        IniManager().add_float(self.ini_key, "detail_icon_padding", "Detail Panel", "icon_padding", float(detail_rows.icon_padding))
        IniManager().add_float(self.ini_key, "detail_icon_size_max", "Detail Panel", "icon_size_max", float(detail_rows.icon_size_max))
        IniManager().add_float(self.ini_key, "detail_content_padding_x", "Detail Panel", "content_padding_x", float(detail_rows.content_padding_x))
        IniManager().add_float(self.ini_key, "detail_content_gap_after_icon", "Detail Panel", "content_gap_after_icon", float(detail_rows.content_gap_after_icon))

    def _ensure_search_vars(self) -> None:
        IniManager().add_str(self.ini_key, "saved_entries", "Search", "saved_entries", "")

    def _save_config(self) -> None:
        self._write_ini_value_immediately(self.ini_key, "button_size", self.config.address_bar.button_size, section="Navigation", name="button_size")
        self._write_ini_value_immediately(self.ini_key, "gradient_start", self.config.address_bar.gradient_start.to_rgba_string(), section="Navigation", name="gradient_start")
        self._write_ini_value_immediately(self.ini_key, "gradient_end", self.config.address_bar.gradient_end.to_rgba_string(), section="Navigation", name="gradient_end")

    def _save_floating_config(self) -> None:
        self._write_ini_value_immediately(self.ini_key, "floating_icon_path", self._texture_to_ini_path(self.floating_button.icon_path), section="Floating Icon", name="icon_path")
        self._write_ini_value_immediately(self.ini_key, "floating_button_size", float(self.floating_button.button_size), section="Floating Icon", name="button_size")
        self._write_ini_value_immediately(self.ini_key, "floating_idle_icon_scale", float(self.floating_button.idle_icon_scale), section="Floating Icon", name="idle_icon_scale")
        self._write_ini_value_immediately(self.ini_key, "floating_hover_icon_scale", float(self.floating_button.hover_icon_scale), section="Floating Icon", name="hover_icon_scale")

    def _save_ui_catalog_config(self) -> None:
        tree_config = self.ui_catalog.tree
        tree_labels = self.ui_catalog.tree.labels
        detail_header = self.ui_catalog.detail.header
        detail_rows = self.ui_catalog.detail.rows

        self._write_ini_value_immediately(self.ini_key, "tree_width", float(tree_config.width), section="Tree", name="width")
        self._write_ini_value_immediately(self.ini_key, "tree_indent_value", float(tree_labels.indent_value), section="Tree", name="indent_value")
        self._write_ini_value_immediately(self.ini_key, "tree_row_height_min", float(tree_labels.row_height_min), section="Tree", name="row_height_min")
        self._write_ini_value_immediately(self.ini_key, "tree_row_height_padding_y", float(tree_labels.row_height_padding_y), section="Tree", name="row_height_padding_y")
        self._write_ini_value_immediately(self.ini_key, "tree_row_padding_x", float(tree_labels.row_padding_x), section="Tree", name="row_padding_x")
        self._write_ini_value_immediately(self.ini_key, "tree_row_width_padding_right", float(tree_labels.row_width_padding_right), section="Tree", name="row_width_padding_right")
        self._write_ini_value_immediately(self.ini_key, "tree_row_corner_radius", float(tree_labels.row_corner_radius), section="Tree", name="row_corner_radius")
        self._write_ini_value_immediately(self.ini_key, "tree_tooltip_icon_spacing", float(tree_labels.tooltip_icon_spacing), section="Tree", name="tooltip_icon_spacing")

        self._write_ini_value_immediately(self.ini_key, "detail_header_row_height", float(detail_header.row_height), section="Detail Panel", name="header_row_height")
        self._write_ini_value_immediately(self.ini_key, "detail_total_width_min", float(detail_header.total_width_min), section="Detail Panel", name="total_width_min")
        self._write_ini_value_immediately(self.ini_key, "detail_favorite_width", float(detail_header.favorite_width), section="Detail Panel", name="favorite_width")
        self._write_ini_value_immediately(self.ini_key, "detail_config_width", float(detail_header.config_width), section="Detail Panel", name="config_width")
        self._write_ini_value_immediately(self.ini_key, "detail_name_width", float(detail_header.name_width), section="Detail Panel", name="name_width")

        self._write_ini_value_immediately(self.ini_key, "detail_row_height", float(detail_rows.row_height), section="Detail Panel", name="row_height")
        self._write_ini_value_immediately(self.ini_key, "detail_icon_padding", float(detail_rows.icon_padding), section="Detail Panel", name="icon_padding")
        self._write_ini_value_immediately(self.ini_key, "detail_icon_size_max", float(detail_rows.icon_size_max), section="Detail Panel", name="icon_size_max")
        self._write_ini_value_immediately(self.ini_key, "detail_content_padding_x", float(detail_rows.content_padding_x), section="Detail Panel", name="content_padding_x")
        self._write_ini_value_immediately(self.ini_key, "detail_content_gap_after_icon", float(detail_rows.content_gap_after_icon), section="Detail Panel", name="content_gap_after_icon")

    def _load_saved_search_entries(self, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        saved_entries_value = IniManager().read_key(key=self.ini_key, section="Search", name="saved_entries", default="")

        if isinstance(saved_entries_value, str):
            entries = saved_entries_value.split("|")
        elif isinstance(saved_entries_value, (list, tuple, set)):
            entries = list(saved_entries_value)
        elif saved_entries_value:
            entries = str(saved_entries_value).split("|")
        else:
            entries = []

        seen: set[str] = set()
        active_view.search_entries = []
        for entry in entries:
            normalized_entry = str(entry).strip()
            if normalized_entry and normalized_entry not in seen:
                seen.add(normalized_entry)
                active_view.search_entries.append(normalized_entry)

    def _save_search_entries(self, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        serialized_entries = "|".join(active_view.search_entries)
        self._write_ini_value_immediately(self.ini_key, "saved_entries", serialized_entries, section="Search", name="saved_entries")

    def _save_floating_position(self) -> None:
        self.floating_button.position = (float(self.floating_button.position[0]), float(self.floating_button.position[1]))

    def _capture_setup_snapshot(self) -> None:
        self.setup_snapshot.tree_labels.width = float(self.ui_catalog.tree.width)
        self.setup_snapshot.address_bar.button_size = int(self.config.address_bar.button_size)
        self.setup_snapshot.address_bar.gradient_start = self.config.address_bar.gradient_start.copy()
        self.setup_snapshot.address_bar.gradient_end = self.config.address_bar.gradient_end.copy()
        self.setup_snapshot.floating_icon.icon_x = float(self.floating_button.position[0])
        self.setup_snapshot.floating_icon.icon_y = float(self.floating_button.position[1])
        self.setup_snapshot.floating_icon.icon_path = self.floating_button.icon_path
        self.setup_snapshot.floating_icon.icon_size = float(self.floating_button.button_size)
        self.setup_snapshot.floating_icon.idle_scale = float(self.floating_button.idle_icon_scale)
        self.setup_snapshot.floating_icon.hover_scale = float(self.floating_button.hover_icon_scale)
        self.setup_snapshot.tree_labels.indent_value = float(self.ui_catalog.tree.labels.indent_value)
        self.setup_snapshot.tree_labels.row_height_min = float(self.ui_catalog.tree.labels.row_height_min)
        self.setup_snapshot.tree_labels.row_height_padding_y = float(self.ui_catalog.tree.labels.row_height_padding_y)
        self.setup_snapshot.tree_labels.row_padding_x = float(self.ui_catalog.tree.labels.row_padding_x)
        self.setup_snapshot.tree_labels.row_width_padding_right = float(self.ui_catalog.tree.labels.row_width_padding_right)
        self.setup_snapshot.tree_labels.row_corner_radius = float(self.ui_catalog.tree.labels.row_corner_radius)
        self.setup_snapshot.tree_labels.tooltip_icon_spacing = float(self.ui_catalog.tree.labels.tooltip_icon_spacing)
        self.setup_snapshot.detail_header.row_height = float(self.ui_catalog.detail.header.row_height)
        self.setup_snapshot.detail_header.total_width_min = float(self.ui_catalog.detail.header.total_width_min)
        self.setup_snapshot.detail_header.favorite_width = float(self.ui_catalog.detail.header.favorite_width)
        self.setup_snapshot.detail_header.config_width = float(self.ui_catalog.detail.header.config_width)
        self.setup_snapshot.detail_header.name_width = float(self.ui_catalog.detail.header.name_width)
        self.setup_snapshot.detail_rows.row_height = float(self.ui_catalog.detail.rows.row_height)
        self.setup_snapshot.detail_rows.icon_padding = float(self.ui_catalog.detail.rows.icon_padding)
        self.setup_snapshot.detail_rows.icon_size_max = float(self.ui_catalog.detail.rows.icon_size_max)
        self.setup_snapshot.detail_rows.content_padding_x = float(self.ui_catalog.detail.rows.content_padding_x)
        self.setup_snapshot.detail_rows.content_gap_after_icon = float(self.ui_catalog.detail.rows.content_gap_after_icon)
        self.runtime.setup_snapshot_captured = True

    def _restore_setup_snapshot(self) -> None:
        self.config.address_bar.button_size = max(1, int(self.setup_snapshot.address_bar.button_size))
        self.config.address_bar.gradient_start = self.setup_snapshot.address_bar.gradient_start.copy()
        self.config.address_bar.gradient_end = self.setup_snapshot.address_bar.gradient_end.copy()
        self._save_config()

        self.floating_button.position = (float(self.setup_snapshot.floating_icon.icon_x), float(self.setup_snapshot.floating_icon.icon_y))
        self._save_floating_position()
        self.floating_button.icon_path = self.setup_snapshot.floating_icon.icon_path
        self.floating_button.button_size = max(1.0, float(self.setup_snapshot.floating_icon.icon_size))
        self.floating_button.idle_icon_scale = max(0.1, float(self.setup_snapshot.floating_icon.idle_scale))
        self.floating_button.hover_icon_scale = max(0.1, float(self.setup_snapshot.floating_icon.hover_scale))
        self._save_floating_config()
        self.ui_catalog.tree.labels.indent_value = max(0.0, float(self.setup_snapshot.tree_labels.indent_value))
        self.ui_catalog.tree.labels.row_height_min = max(1.0, float(self.setup_snapshot.tree_labels.row_height_min))
        self.ui_catalog.tree.labels.row_height_padding_y = max(0.0, float(self.setup_snapshot.tree_labels.row_height_padding_y))
        self.ui_catalog.tree.labels.row_padding_x = max(0.0, float(self.setup_snapshot.tree_labels.row_padding_x))
        self.ui_catalog.tree.labels.row_width_padding_right = max(0.0, float(self.setup_snapshot.tree_labels.row_width_padding_right))
        self.ui_catalog.tree.labels.row_corner_radius = max(0.0, float(self.setup_snapshot.tree_labels.row_corner_radius))
        self.ui_catalog.tree.labels.tooltip_icon_spacing = max(0.0, float(self.setup_snapshot.tree_labels.tooltip_icon_spacing))
        self.ui_catalog.tree.width = max(80.0, float(self.setup_snapshot.tree_labels.width))
        self.ui_catalog.detail.header.row_height = max(1.0, float(self.setup_snapshot.detail_header.row_height))
        self.ui_catalog.detail.header.total_width_min = max(1.0, float(self.setup_snapshot.detail_header.total_width_min))
        self.ui_catalog.detail.header.favorite_width = max(1.0, float(self.setup_snapshot.detail_header.favorite_width))
        self.ui_catalog.detail.header.config_width = max(1.0, float(self.setup_snapshot.detail_header.config_width))
        self.ui_catalog.detail.header.name_width = max(1.0, float(self.setup_snapshot.detail_header.name_width))
        self.ui_catalog.detail.rows.row_height = max(1.0, float(self.setup_snapshot.detail_rows.row_height))
        self.ui_catalog.detail.rows.icon_padding = max(0.0, float(self.setup_snapshot.detail_rows.icon_padding))
        self.ui_catalog.detail.rows.icon_size_max = max(1.0, float(self.setup_snapshot.detail_rows.icon_size_max))
        self.ui_catalog.detail.rows.content_padding_x = max(0.0, float(self.setup_snapshot.detail_rows.content_padding_x))
        self.ui_catalog.detail.rows.content_gap_after_icon = max(0.0, float(self.setup_snapshot.detail_rows.content_gap_after_icon))

    @staticmethod
    def _write_ini_value_immediately(ini_key: str, var_name: str, value, *, section: str, name: str) -> None:
        manager = IniManager()
        manager.set(ini_key, var_name, value, section=section)

        node = manager._get_node(ini_key)
        if node is None:
            return

        node.ini_handler.write_key(section, name, value)
        node.cached_values[(section, name)] = str(value)

    def _reset_floating_style(self) -> None:
        floating_defaults = floating_icon_vars()
        self.floating_button.icon_path = self._default_floating_icon_path()
        self.floating_button.button_size = floating_defaults.button_size
        self.floating_button.idle_icon_scale = floating_defaults.idle_scale
        self.floating_button.hover_icon_scale = floating_defaults.hover_scale
        self._save_floating_config()

    def _reset_floating_position(self) -> None:
        floating_defaults = floating_icon_vars()
        self.floating_button.position = (floating_defaults.position_x, floating_defaults.position_y)
        self._save_floating_position()

    @classmethod
    def _pick_texture_path(cls) -> str | None:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            filepath = filedialog.askopenfilename(
                title="Select Floating Icon Texture",
                initialdir=cls._projects_root(),
                filetypes=[
                    ("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tga;*.dds"),
                    ("PNG files", "*.png"),
                    ("All files", "*.*"),
                ],
            )
            return filepath or None
        finally:
            root.destroy()

    def _load_config_if_needed(self) -> None:
        if self.runtime.settings_loaded:
            return

        self._ensure_config_vars()
        self._ensure_floating_config_vars()
        self._ensure_ui_catalog_vars()
        self._ensure_search_vars()
        IniManager().load_once(self.ini_key)
        node = IniManager()._get_node(self.ini_key)

        self.floating_button.load_visibility()
        self.runtime.show_adavanced = bool(IniManager().get(self.ini_key, "show_adavanced", default=False, section="Configuration"))
        self.config.address_bar.button_size = IniManager().getInt(self.ini_key, "button_size", default=self.config.address_bar.button_size, section="Navigation")
        self.config.address_bar.gradient_start = self._parse_color(IniManager().get(self.ini_key, "gradient_start", default=self.config.address_bar.gradient_start.to_rgba_string(), section="Navigation"), self.config.address_bar.gradient_start)
        self.config.address_bar.gradient_end = self._parse_color(IniManager().get(self.ini_key, "gradient_end", default=self.config.address_bar.gradient_end.to_rgba_string(), section="Navigation"), self.config.address_bar.gradient_end)
        self.floating_button.icon_path = self._texture_from_ini_path(
            IniManager().getStr(
                self.ini_key,
                "floating_icon_path",
                default=self._default_floating_icon_relpath(),
                section="Floating Icon",
            )
        )
        self.floating_button.button_size = IniManager().getFloat(self.ini_key, "floating_button_size", default=float(self.config.floating_icon.button_size), section="Floating Icon")
        self.floating_button.idle_icon_scale = IniManager().getFloat(self.ini_key, "floating_idle_icon_scale", default=float(self.config.floating_icon.idle_scale), section="Floating Icon")
        self.floating_button.hover_icon_scale = IniManager().getFloat(self.ini_key, "floating_hover_icon_scale", default=float(self.config.floating_icon.hover_scale), section="Floating Icon")
        if node is not None:
            self.ui_catalog.tree.width = float(node.ini_handler.read_float("Tree", "width", float(self.ui_catalog.tree.width)))
            node.vars_values[("Tree", "tree_width")] = self.ui_catalog.tree.width
        else:
            self.ui_catalog.tree.width = IniManager().getFloat(self.ini_key, "tree_width", default=float(self.ui_catalog.tree.width), section="Tree")
        self.ui_catalog.tree.labels.indent_value = IniManager().getFloat(self.ini_key, "tree_indent_value", default=float(self.ui_catalog.tree.labels.indent_value), section="Tree")
        self.ui_catalog.tree.labels.row_height_min = IniManager().getFloat(self.ini_key, "tree_row_height_min", default=float(self.ui_catalog.tree.labels.row_height_min), section="Tree")
        self.ui_catalog.tree.labels.row_height_padding_y = IniManager().getFloat(self.ini_key, "tree_row_height_padding_y", default=float(self.ui_catalog.tree.labels.row_height_padding_y), section="Tree")
        self.ui_catalog.tree.labels.row_padding_x = IniManager().getFloat(self.ini_key, "tree_row_padding_x", default=float(self.ui_catalog.tree.labels.row_padding_x), section="Tree")
        self.ui_catalog.tree.labels.row_width_padding_right = IniManager().getFloat(self.ini_key, "tree_row_width_padding_right", default=float(self.ui_catalog.tree.labels.row_width_padding_right), section="Tree")
        self.ui_catalog.tree.labels.row_corner_radius = IniManager().getFloat(self.ini_key, "tree_row_corner_radius", default=float(self.ui_catalog.tree.labels.row_corner_radius), section="Tree")
        self.ui_catalog.tree.labels.tooltip_icon_spacing = IniManager().getFloat(self.ini_key, "tree_tooltip_icon_spacing", default=float(self.ui_catalog.tree.labels.tooltip_icon_spacing), section="Tree")
        self.ui_catalog.detail.header.row_height = IniManager().getFloat(self.ini_key, "detail_header_row_height", default=float(self.ui_catalog.detail.header.row_height), section="Detail Panel")
        self.ui_catalog.detail.header.total_width_min = IniManager().getFloat(self.ini_key, "detail_total_width_min", default=float(self.ui_catalog.detail.header.total_width_min), section="Detail Panel")
        self.ui_catalog.detail.header.favorite_width = IniManager().getFloat(self.ini_key, "detail_favorite_width", default=float(self.ui_catalog.detail.header.favorite_width), section="Detail Panel")
        self.ui_catalog.detail.header.config_width = IniManager().getFloat(self.ini_key, "detail_config_width", default=float(self.ui_catalog.detail.header.config_width), section="Detail Panel")
        self.ui_catalog.detail.header.name_width = IniManager().getFloat(self.ini_key, "detail_name_width", default=float(self.ui_catalog.detail.header.name_width), section="Detail Panel")
        self.ui_catalog.detail.rows.row_height = IniManager().getFloat(self.ini_key, "detail_row_height", default=float(self.ui_catalog.detail.rows.row_height), section="Detail Panel")
        self.ui_catalog.detail.rows.icon_padding = IniManager().getFloat(self.ini_key, "detail_icon_padding", default=float(self.ui_catalog.detail.rows.icon_padding), section="Detail Panel")
        self.ui_catalog.detail.rows.icon_size_max = IniManager().getFloat(self.ini_key, "detail_icon_size_max", default=float(self.ui_catalog.detail.rows.icon_size_max), section="Detail Panel")
        self.ui_catalog.detail.rows.content_padding_x = IniManager().getFloat(self.ini_key, "detail_content_padding_x", default=float(self.ui_catalog.detail.rows.content_padding_x), section="Detail Panel")
        self.ui_catalog.detail.rows.content_gap_after_icon = IniManager().getFloat(self.ini_key, "detail_content_gap_after_icon", default=float(self.ui_catalog.detail.rows.content_gap_after_icon), section="Detail Panel")
        self._load_saved_search_entries()
        self.runtime.tree_width_pending_apply = True
        self.runtime.tree_layout_revision += 1
        self.runtime.settings_loaded = True

    def _on_window_visibility_toggled(self, visible: bool) -> None:
        if visible:
            self.runtime.expand_on_next_show = True

    def _get_snapshot(self):
        return WidgetCatalog.snapshot_from_handler(self.widget_manager)

    def _get_favorite_ids(self) -> set[str]:
        ini_key = self._manager_ini_key()
        favorites_value = IniManager().read_key(key=ini_key, section="Favorites", name="favorites", default="")

        if isinstance(favorites_value, str):
            entries = favorites_value.split(",")
        elif isinstance(favorites_value, (list, tuple, set)):
            entries = favorites_value
        elif favorites_value:
            entries = str(favorites_value).split(",")
        else:
            entries = []

        return {str(entry).strip() for entry in entries if str(entry).strip()}

    def _save_favorite_ids(self, favorite_ids: set[str]) -> None:
        ini_key = self._manager_ini_key()
        IniManager().set(key=ini_key, var_name="favorites", value=",".join(sorted(favorite_ids)), section="Favorites")
        IniManager().save_vars(ini_key)

    def _set_widget_favorite(self, widget, favorite: bool) -> None:
        favorite_ids = self._get_favorite_ids()
        widget_id = widget.folder_script_name
        if favorite:
            favorite_ids.add(widget_id)
        else:
            favorite_ids.discard(widget_id)
        self._save_favorite_ids(favorite_ids)

    def _set_widget_active(self, widget, active: bool) -> None:
        if active:
            widget.enable()
        else:
            widget.disable()

        widget_id = widget.folder_script_name
        v_enabled = self.widget_manager._widget_var(widget_id, "enabled")
        cv = self.widget_manager._get_config_var(widget_id, v_enabled)
        if cv:
            IniManager().set(
                key=self.widget_manager.MANAGER_INI_KEY,
                section=cv.section,
                var_name=cv.var_name,
                value=active,
            )
            IniManager().save_vars(self.widget_manager.MANAGER_INI_KEY)

    @staticmethod
    def _center_cursor_y(content_height: float) -> None:
        current_y = PyImGui.get_cursor_pos_y()
        offset = max((content_height - PyImGui.get_text_line_height()) * 0.5, 0.0)
        PyImGui.set_cursor_pos_y(current_y + offset)

    def _draw_centered_text(self, text: str, row_height: float) -> None:
        self._center_cursor_y(row_height)
        PyImGui.text(text)

    def _draw_centered_image(self, texture_path: str, image_size: float, row_height: float) -> None:
        current_y = PyImGui.get_cursor_pos_y()
        offset = max((row_height - image_size) * 0.5, 0.0)
        PyImGui.set_cursor_pos_y(current_y + offset)
        ImGui.image(texture_path, (image_size, image_size))

    def _draw_centered_button(self, label: str, row_height: float, width: float, height: float) -> bool:
        current_y = PyImGui.get_cursor_pos_y()
        offset = max((row_height - height) * 0.5, 0.0)
        PyImGui.set_cursor_pos_y(current_y + offset)
        return ImGui.button(label, width=width, height=height)

    def _draw_centered_toggle_icon_button(self, label: str, value: bool, row_height: float, width: float, height: float) -> bool:
        current_y = PyImGui.get_cursor_pos_y()
        offset = max((row_height - height) * 0.5, 0.0)
        PyImGui.set_cursor_pos_y(current_y + offset)
        return ImGui.toggle_icon_button(label, value, width, height)

    def _draw_centered_texture_icon(self, texture_path: str, image_size: float, row_height: float, uv0: tuple[float, float] = (0.0, 0.0), uv1: tuple[float, float] = (1.0, 1.0)) -> None:
        current_y = PyImGui.get_cursor_pos_y()
        offset = max((row_height - image_size) * 0.5, 0.0)
        PyImGui.set_cursor_pos_y(current_y + offset)
        ImGui.image(texture_path, (image_size, image_size), uv0=uv0, uv1=uv1)

    def _draw_centered_texture_button(self, button_id: str, texture_path: str, row_height: float, width: float, height: float, uv0: tuple[float, float] = (0.0, 0.0), uv1: tuple[float, float] = (1.0, 1.0)) -> bool:
        current_y = PyImGui.get_cursor_pos_y()
        offset = max((row_height - height) * 0.5, 0.0)
        PyImGui.set_cursor_pos_y(current_y + offset)
        clicked = ImGui.invisible_button(f"##{button_id}", width, height)
        item_min = PyImGui.get_item_rect_min()
        ImGui.DrawTextureInDrawList(
            pos=(item_min[0], item_min[1]),
            size=(width, height),
            texture_path=texture_path,
            uv0=uv0,
            uv1=uv1,
        )
        return clicked

    def _draw_centered_texture_icon_button(self, button_id: str, texture_path: str, row_height: float, size: float, uv0: tuple[float, float] = (0.0, 0.0), uv1: tuple[float, float] = (1.0, 1.0)) -> bool:
        return self._draw_centered_texture_button(button_id, texture_path, row_height, size, size, uv0=uv0, uv1=uv1)

    def _draw_centered_texture_toggle_button(self, button_id: str, value: bool, texture_path: str, row_height: float, width: float, height: float, uv0: tuple[float, float] = (0.0, 0.0), uv1: tuple[float, float] = (1.0, 1.0)) -> bool:
        current_y = PyImGui.get_cursor_pos_y()
        offset = max((row_height - height) * 0.5, 0.0)
        PyImGui.set_cursor_pos_y(current_y + offset)
        clicked = ImGui.invisible_button(f"##{button_id}", width, height)
        item_min = PyImGui.get_item_rect_min()
        ImGui.DrawTextureInDrawList(
            pos=(item_min[0], item_min[1]),
            size=(width, height),
            texture_path=texture_path,
            uv0=uv0,
            uv1=uv1,
        )
        return (not value) if clicked else value

    def _draw_texture_cell_button(self, button_id: str, texture_path: str, row_height: float, draw_width: float, draw_height: float, uv0: tuple[float, float] = (0.0, 0.0), uv1: tuple[float, float] = (1.0, 1.0)) -> bool:
        cell_width = max(PyImGui.get_content_region_avail()[0], draw_width)
        clicked = ImGui.invisible_button(f"##{button_id}", cell_width, row_height)
        item_min = PyImGui.get_item_rect_min()
        item_max = PyImGui.get_item_rect_max()
        x = item_min[0] + max((item_max[0] - item_min[0] - draw_width) * 0.5, 0.0)
        y = item_min[1] + max((item_max[1] - item_min[1] - draw_height) * 0.5, 0.0)
        ImGui.DrawTextureInDrawList(
            pos=(x, y),
            size=(draw_width, draw_height),
            texture_path=texture_path,
            uv0=uv0,
            uv1=uv1,
        )
        return clicked

    def _draw_text_cell_button(self, button_id: str, text: str, row_height: float) -> bool:
        cell_width = max(PyImGui.get_content_region_avail()[0], 1.0)
        clicked = ImGui.invisible_button(f"##{button_id}", cell_width, row_height)
        item_min = PyImGui.get_item_rect_min()
        item_max = PyImGui.get_item_rect_max()
        text_y = item_min[1] + max((item_max[1] - item_min[1] - PyImGui.get_text_line_height()) * 0.5, 0.0)
        PyImGui.draw_list_add_text(
            item_min[0] + 6.0,
            text_y,
            ImGui.get_style().Text.get_current().color_int,
            text,
        )
        return clicked

    def _draw_icon_cell_button(self, button_id: str, texture_path: str, cell_width: float, row_height: float, draw_size: float, uv0: tuple[float, float] = (0.0, 0.0), uv1: tuple[float, float] = (1.0, 1.0)) -> bool:
        clicked = ImGui.invisible_button(f"##{button_id}", cell_width, row_height)
        item_min = PyImGui.get_item_rect_min()
        item_max = PyImGui.get_item_rect_max()
        x = item_min[0] + max((item_max[0] - item_min[0] - draw_size) * 0.5, 0.0)
        y = item_min[1] + max((item_max[1] - item_min[1] - draw_size) * 0.5, 0.0)
        ImGui.DrawTextureInDrawList(
            pos=(x, y),
            size=(draw_size, draw_size),
            texture_path=texture_path,
            uv0=uv0,
            uv1=uv1,
        )
        return clicked

    @staticmethod
    def _get_widget_description(widget) -> str:
        module = getattr(widget, "module", None)
        if module is not None:
            for attr_name in ("MODULE_DESCRIPTION", "DESCRIPTION", "description"):
                value = getattr(module, attr_name, "")
                if isinstance(value, str) and value.strip():
                    return value.strip()

            module_doc = getattr(module, "__doc__", "")
            if isinstance(module_doc, str) and module_doc.strip():
                return module_doc.strip()

        return "No description available."

    def _draw_widget_hover_card(self, widget) -> None:
        if getattr(widget, "has_tooltip_property", False) and getattr(widget, "tooltip", None):
            try:
                widget.tooltip()
                return
            except Exception as e:
                Py4GW.Console.Log("WidgetHandler", f"Error during tooltip of widget {widget.folder_script_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

        if not PyImGui.begin_tooltip():
            return

        image_size = 48.0
        has_icon = not WidgetCatalog._has_missing_icon(widget)
        display_name = widget.name if widget.name else widget.cleaned_name()
        description = self._get_widget_description(widget)

        if has_icon:
            ImGui.image(widget.image, (image_size, image_size))
            PyImGui.same_line(0, 8)
        else:
            PyImGui.text(IconsFontAwesome5.ICON_FILE_CODE)
            PyImGui.same_line(0, 8)

        PyImGui.begin_group()
        PyImGui.text(display_name)
        if widget.category:
            PyImGui.text_disabled(widget.category)
        PyImGui.end_group()
        PyImGui.separator()
        PyImGui.text_wrapped(description)
        PyImGui.end_tooltip()

    @staticmethod
    def _fit_text_to_width(text: str, max_width: float) -> str:
        if max_width <= 0.0 or not text:
            return ""

        text_width, _ = PyImGui.calc_text_size(text)
        if text_width <= max_width:
            return text

        ellipsis = "..."
        ellipsis_width, _ = PyImGui.calc_text_size(ellipsis)
        if ellipsis_width > max_width:
            return ""

        low = 0
        high = len(text)
        best = ""
        while low <= high:
            mid = (low + high) // 2
            candidate = text[:mid] + ellipsis
            candidate_width, _ = PyImGui.calc_text_size(candidate)
            if candidate_width <= max_width:
                best = candidate
                low = mid + 1
            else:
                high = mid - 1

        return best

    def _detail_column_widths(self, total_width: float) -> tuple[float, float, float]:
        detail_header = self.ui_catalog.detail.header
        name_width = detail_header.name_width
        favorite_width = detail_header.favorite_width
        config_width = detail_header.config_width
        return name_width, favorite_width, config_width

    def _draw_detail_header_row(self, total_width: float, row_height: float) -> None:
        x, y = PyImGui.get_cursor_screen_pos()
        name_width, favorite_width, config_width = self._detail_column_widths(total_width)
        draw_list = PyImGui
        bg = Color(36, 49, 64, 255)
        border = Color(70, 70, 70, 180)

        draw_list.draw_list_add_rect_filled(x, y, x + total_width, y + row_height, bg.to_color(), 0.0, 0)
        draw_list.draw_list_add_rect(x, y, x + total_width, y + row_height, border.to_color(), 0.0, 0, 1.0)

        text_y = y + max((row_height - PyImGui.get_text_line_height()) * 0.5, 0.0)
        text_color = ImGui.get_style().Text.get_current().color_int
        col_x = x
        for label, width in [
            ("Name", name_width),
            ("Fav", favorite_width),
            ("Cfg", config_width),
        ]:
            PyImGui.draw_list_add_text(col_x + 6.0, text_y, text_color, label)
            col_x += width

        ImGui.dummy(total_width, row_height)

    def _draw_detail_entry_primary(self, item_min: tuple[float, float], item_max: tuple[float, float], content_width: float, texture_path: str | None, uv0: tuple[float, float], uv1: tuple[float, float], label: str, image_size: float) -> None:
        detail_rows = self.ui_catalog.detail.rows
        text_color = ImGui.get_style().Text.get_current().color_int
        content_left = item_min[0] + detail_rows.content_padding_x
        content_right = item_min[0] + max(content_width - detail_rows.content_padding_x, detail_rows.content_padding_x)

        if texture_path:
            icon_y = item_min[1] + max((item_max[1] - item_min[1] - image_size) * 0.5, 0.0)
            ImGui.DrawTextureInDrawList(
                pos=(content_left, icon_y),
                size=(image_size, image_size),
                texture_path=texture_path,
                uv0=uv0,
                uv1=uv1,
            )
            text_x = content_left + image_size + detail_rows.content_gap_after_icon
        else:
            text_x = content_left

        text_y = item_min[1] + max((item_max[1] - item_min[1] - PyImGui.get_text_line_height()) * 0.5, 0.0)
        text_max_width = max(content_right - text_x, 0.0)
        display_label = self._fit_text_to_width(label, text_max_width)
        PyImGui.draw_list_add_text(text_x, text_y, text_color, display_label)

    def _draw_detail_explorer_row(
        self,
        row_id: str,
        total_width: float,
        row_height: float,
        entry_texture: str | None,
        entry_uv0: tuple[float, float],
        entry_uv1: tuple[float, float],
        entry_label: str,
        on_primary_click,
        active: bool = False,
        favorite_texture: str | None = None,
        favorite_uv0: tuple[float, float] = (0.0, 0.0),
        favorite_uv1: tuple[float, float] = (1.0, 1.0),
        on_favorite_click=None,
        config_texture: str | None = None,
        config_uv0: tuple[float, float] = (0.0, 0.0),
        config_uv1: tuple[float, float] = (1.0, 1.0),
        on_config_click=None,
    ) -> None:
        detail_rows = self.ui_catalog.detail.rows
        name_width, favorite_width, config_width = self._detail_column_widths(total_width)
        primary_width = name_width
        x, y = PyImGui.get_cursor_screen_pos()
        row_bg = Color(22, 22, 28, 210)
        hover_bg = Color(32, 38, 46, 230)
        active_bg = Color(30, 56, 38, 220)
        active_hover_bg = Color(38, 68, 46, 235)
        border = Color(55, 55, 60, 160)
        active_border = ColorPalette.GetColor("GW_GREEN").copy()

        clicked_primary = ImGui.invisible_button(f"##{row_id}_primary", primary_width, row_height)
        item_min = PyImGui.get_item_rect_min()
        item_max = PyImGui.get_item_rect_max()
        hovered = PyImGui.is_item_hovered()
        fill = active_hover_bg if active and hovered else active_bg if active else hover_bg if hovered else row_bg
        row_border = active_border if active else border
        border_thickness = 2.0 if active else 1.0
        PyImGui.draw_list_add_rect_filled(x, y, x + total_width, y + row_height, fill.to_color(), 0.0, 0)
        PyImGui.draw_list_add_rect(x, y, x + total_width, y + row_height, row_border.to_color(), 0.0, 0, border_thickness)
        self._draw_detail_entry_primary(
            item_min,
            item_max,
            primary_width,
            entry_texture,
            entry_uv0,
            entry_uv1,
            entry_label,
            min(row_height - detail_rows.icon_padding, detail_rows.icon_size_max),
        )

        if clicked_primary and on_primary_click:
            on_primary_click()

        current_x = x + primary_width

        PyImGui.set_cursor_screen_pos(current_x, y)
        if favorite_texture and on_favorite_click:
            favorite_toggled = self._draw_centered_texture_toggle_button(
                f"{row_id}_fav",
                False,
                favorite_texture,
                row_height,
                min(row_height - detail_rows.icon_padding, detail_rows.icon_size_max),
                min(row_height - detail_rows.icon_padding, detail_rows.icon_size_max),
                uv0=favorite_uv0,
                uv1=favorite_uv1,
            )
            if favorite_toggled:
                on_favorite_click()
        else:
            ImGui.dummy(favorite_width, row_height)
        current_x += favorite_width

        PyImGui.set_cursor_screen_pos(current_x, y)
        if config_texture and on_config_click:
            toggled = self._draw_centered_texture_toggle_button(
                f"{row_id}_cfg",
                False,
                config_texture,
                row_height,
                min(row_height - detail_rows.icon_padding, detail_rows.icon_size_max),
                min(row_height - detail_rows.icon_padding, detail_rows.icon_size_max),
                uv0=config_uv0,
                uv1=config_uv1,
            )
            if toggled:
                on_config_click()
        else:
            ImGui.dummy(config_width, row_height)

        PyImGui.set_cursor_screen_pos(x, y)
        ImGui.dummy(total_width, row_height)

    def _make_virtual_scope_node(self, snapshot, label: str, scope: CatalogScope, path_prefix: str) -> WidgetCatalogNode:
        query = WidgetCatalog.query(
            snapshot,
            WidgetCatalogQuery(
                scope=scope,
                favorite_ids=self._get_favorite_ids(),
            ),
        )
        query.sort(key=lambda widget: widget.cleaned_name().lower())
        return WidgetCatalogNode(
            name=label,
            depth=1,
            parent=None,
            path=path_prefix,
            is_widget_container=True,
            widget_ids=[widget.folder_script_name for widget in query],
        )

    def _make_virtual_search_node(self, snapshot, label: str, path_prefix: str) -> WidgetCatalogNode:
        query = WidgetCatalog.query(
            snapshot,
            WidgetCatalogQuery(
                text=label,
                favorite_ids=self._get_favorite_ids(),
            ),
        )
        query.sort(key=lambda widget: widget.cleaned_name().lower())
        return WidgetCatalogNode(
            name=label,
            depth=1,
            parent=None,
            path=path_prefix,
            is_widget_container=True,
            widget_ids=[widget.folder_script_name for widget in query],
        )

    def _get_browser_tree(self, snapshot) -> WidgetCatalogNode:
        root = WidgetCatalogNode()
        active_view = self._get_active_view()

        search_node = WidgetCatalogNode(
            name="Search",
            depth=1,
            parent=root,
            path=self.SEARCH_PATH,
        )
        root.children[search_node.name] = search_node

        for entry_index, entry_label in enumerate(active_view.search_entries):
            search_entry_node = self._make_virtual_search_node(
                snapshot,
                entry_label,
                f"{self.SEARCH_ENTRY_PATH_PREFIX}{entry_index}",
            )
            search_entry_node.parent = root
            root.children[f"SearchEntry::{entry_index}::{entry_label}"] = search_entry_node

        active_node = self._make_virtual_scope_node(snapshot, "Active", "active", self.ACTIVE_PATH)
        active_node.parent = root
        root.children[active_node.name] = active_node

        favorites_node = self._make_virtual_scope_node(snapshot, "Favorites", "favorites", self.FAVORITES_PATH)
        favorites_node.parent = root
        root.children[favorites_node.name] = favorites_node

        for child in WidgetCatalog.tree_children(snapshot.tree):
            root.children[child.name] = child

        return root

    def _display_path_segment(self, segment: str, view: browser_view_state | None = None) -> str:
        active_view = view or self._get_active_view()
        if segment == self.SEARCH_PATH:
            return "Search"
        if segment == self.FAVORITES_PATH:
            return "Favorites"
        if segment == self.ACTIVE_PATH:
            return "Active"
        if segment.startswith(self.SEARCH_ENTRY_PATH_PREFIX):
            try:
                entry_index = int(segment.removeprefix(self.SEARCH_ENTRY_PATH_PREFIX))
            except ValueError:
                return "Search"
            if 0 <= entry_index < len(active_view.search_entries):
                return active_view.search_entries[entry_index]
            return "Search"
        return segment

    def _get_active_view(self) -> browser_view_state:
        return self.views[self.runtime.active_view_id]

    @classmethod
    def _is_virtual_root_path(cls, path: str) -> bool:
        return path in {cls.SEARCH_PATH, cls.ACTIVE_PATH, cls.FAVORITES_PATH}

    @classmethod
    def _is_virtual_search_entry_path(cls, path: str) -> bool:
        return path.startswith(cls.SEARCH_ENTRY_PATH_PREFIX)

    def _get_root_folder_groups(self, node: WidgetCatalogNode) -> tuple[list[WidgetCatalogNode], list[WidgetCatalogNode]]:
        folders = WidgetCatalog.tree_children(node)
        virtual_paths = [self.SEARCH_PATH, self.ACTIVE_PATH, self.FAVORITES_PATH]
        virtual_lookup = {child.path: child for child in folders}
        virtual_folders = [virtual_lookup[path] for path in virtual_paths if path in virtual_lookup]
        regular_folders = [child for child in folders if not self._is_virtual_root_path(child.path) and not self._is_virtual_search_entry_path(child.path)]
        return virtual_folders, regular_folders

    def _ensure_view(self, view_id: str, label: str | None = None) -> browser_view_state:
        view = self.views.get(view_id)
        if view is None:
            view = browser_view_state(view_id=view_id, label=label or view_id)
            self.views[view_id] = view
        elif label is not None:
            view.label = label
        return view

    def _get_view_path(self, view: browser_view_state | None = None) -> str:
        active_view = view or self._get_active_view()
        return active_view.browser.current_path

    def _set_view_path(self, path: str, *, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        active_view.browser.current_path = path

    def _get_view_expanded_paths(self, view: browser_view_state | None = None) -> set[str]:
        active_view = view or self._get_active_view()
        return active_view.expanded_paths

    def _navigate_to(self, path: str, push_history: bool = True, expand_ancestors: bool = False, sync_outline: bool = False, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        path = path or ""
        if path == self.SEARCH_PATH:
            return
        if path == active_view.browser.current_path:
            if sync_outline:
                self._sync_outline_to_path(path, view=active_view)
            elif expand_ancestors:
                self._expand_outline_ancestors(path, view=active_view)
            return

        if push_history:
            active_view.browser.back_history.append(active_view.browser.current_path)
            active_view.browser.forward_history.clear()

        active_view.browser.current_path = path
        if sync_outline:
            self._sync_outline_to_path(path, view=active_view)
        elif expand_ancestors:
            self._expand_outline_ancestors(path, view=active_view)

    def _toggle_outline_expanded(self, path: str, view: browser_view_state | None = None) -> None:
        if not path:
            return
        expanded_paths = self._get_view_expanded_paths(view)
        if path in expanded_paths:
            expanded_paths.remove(path)
        else:
            expanded_paths.add(path)

    def _expand_outline_ancestors(self, path: str, view: browser_view_state | None = None) -> None:
        if not path:
            return

        expanded_paths = self._get_view_expanded_paths(view)
        current = ""
        for part in [segment for segment in path.split("/") if segment]:
            current = f"{current}/{part}" if current else part
            expanded_paths.add(current)

    def _sync_outline_to_path(self, path: str, view: browser_view_state | None = None) -> None:
        expanded_paths = self._get_view_expanded_paths(view)
        expanded_paths.clear()
        self._expand_outline_ancestors(path, view=view)

    def _go_back(self, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        if not active_view.browser.back_history:
            return
        previous_path = active_view.browser.back_history.pop()
        active_view.browser.forward_history.append(active_view.browser.current_path)
        self._navigate_to(previous_path, push_history=False, sync_outline=True, view=active_view)

    def _go_forward(self, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        if not active_view.browser.forward_history:
            return
        next_path = active_view.browser.forward_history.pop()
        active_view.browser.back_history.append(active_view.browser.current_path)
        self._navigate_to(next_path, push_history=False, sync_outline=True, view=active_view)

    def _go_up(self, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        if not active_view.browser.current_path:
            return
        parent_path = active_view.browser.current_path.rsplit("/", 1)[0] if "/" in active_view.browser.current_path else ""
        self._navigate_to(parent_path, sync_outline=True, view=active_view)

    def _find_node(self, root: WidgetCatalogNode, path: str) -> WidgetCatalogNode:
        if not path:
            return root

        node = root
        current_path = ""
        for part in path.split("/"):
            current_path = f"{current_path}/{part}" if current_path else part
            child = node.children.get(part)
            if child is None:
                child = next((candidate for candidate in node.children.values() if candidate.path == current_path), None)
            if child is None:
                return root
            node = child
        return node

    def _get_max_path_depth(self, root: WidgetCatalogNode) -> int:
        max_depth = 1

        def walk(node: WidgetCatalogNode) -> None:
            nonlocal max_depth
            if node.path:
                max_depth = max(max_depth, len([part for part in node.path.split("/") if part]))
            for child in WidgetCatalog.tree_children(node):
                walk(child)

        walk(root)
        return max_depth

    def _get_depth_color(self, level: int, max_depth: int) -> Color:
        blend_amount = 0.0 if max_depth <= 0 else min(max(level / max_depth, 0.0), 1.0)
        return self.config.address_bar.gradient_start.shift(self.config.address_bar.gradient_end, blend_amount).saturate(0.2)

    def _get_outline_palette(self, depth: int, max_depth: int) -> tuple[Color, Color, Color, Color]:
        base = self._get_depth_color(depth, max_depth)
        fill = base.copy()
        fill.a = 90
        idle_border = ColorPalette.GetColor("black").copy()
        idle_border.a = 210
        active_border = base.shift(ColorPalette.GetColor("white"), 0.22)
        active_border.a = 220
        hover_border = base.shift(ColorPalette.GetColor("white"), 0.35)
        hover_border.a = 255
        return fill, idle_border, active_border, hover_border

    def _push_breadcrumb_colors(self, depth: int, max_depth: int) -> None:
        fill, idle_border, active_border, hover_border = self._get_outline_palette(depth, max_depth)

        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, fill.to_tuple_normalized())
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, fill.to_tuple_normalized())
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, fill.to_tuple_normalized())
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, idle_border.to_tuple_normalized())
        PyImGui.push_style_color(PyImGui.ImGuiCol.BorderShadow, (0.0, 0.0, 0.0, 0.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.Separator, hover_border.to_tuple_normalized())
        PyImGui.push_style_color(PyImGui.ImGuiCol.SeparatorHovered, hover_border.to_tuple_normalized())
        PyImGui.push_style_color(PyImGui.ImGuiCol.SeparatorActive, active_border.to_tuple_normalized())

    def _draw_breadcrumb_button(self, label: str, path: str, depth: int, max_depth: int) -> None:
        self._push_breadcrumb_colors(depth, max_depth)
        if PyImGui.button(label):
            self._navigate_to(path, sync_outline=True)
        PyImGui.pop_style_color(8)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip(f"Go to /{path}" if path else "Go to root")

    def _draw_breadcrumb_bar(self, browser_root: WidgetCatalogNode, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        max_depth = self._get_max_path_depth(browser_root)
        self._push_breadcrumb_colors(0, max_depth)
        if PyImGui.button(f"/Widgets##crumb_root_{active_view.view_id}"):
            self._navigate_to("", sync_outline=True, view=active_view)
        PyImGui.pop_style_color(8)
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip("Go to root")

        current = ""
        for index, part in enumerate([segment for segment in active_view.browser.current_path.split("/") if segment], start=1):
            current = f"{current}/{part}" if current else part
            PyImGui.same_line(0.0, 1)
            self._push_breadcrumb_colors(index, max_depth)
            if PyImGui.button(f"/{self._display_path_segment(part, view=active_view)}##crumb_{active_view.view_id}_{current}"):
                self._navigate_to(current, sync_outline=True, view=active_view)
            PyImGui.pop_style_color(8)
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip(f"Go to /{current}")

    def _draw_nav_button(self, label: str, icon: str, callback: Callable[[], None]) -> None:
        if PyImGui.button(f"{icon}##{label}", width=self.config.address_bar.button_size, height=self.config.address_bar.button_size):
            callback()
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip(label)

    def _draw_nav_buttons(self) -> None:
        style = ImGui.get_style()
        style.CellPadding.push_style_var(2, 0)
        if PyImGui.begin_table(
            "nav_buttons##WidgetCatNavTable",
            3,
            PyImGui.TableFlags.SizingFixedFit | PyImGui.TableFlags.NoHostExtendX,
        ):
            PyImGui.table_setup_column("Back##WidgetCatNavBack", PyImGui.TableColumnFlags.NoSort | PyImGui.TableColumnFlags.WidthFixed, self.config.address_bar.button_size)
            PyImGui.table_setup_column("Forward##WidgetCatNavForward", PyImGui.TableColumnFlags.NoSort | PyImGui.TableColumnFlags.WidthFixed, self.config.address_bar.button_size)
            PyImGui.table_setup_column("Up##WidgetCatNavUp", PyImGui.TableColumnFlags.NoSort | PyImGui.TableColumnFlags.WidthFixed, self.config.address_bar.button_size)

            PyImGui.table_next_row()

            PyImGui.table_next_column()
            self._draw_nav_button("Back", IconsFontAwesome5.ICON_LONG_ARROW_ALT_LEFT, self._go_back)

            PyImGui.table_next_column()
            self._draw_nav_button("Forward", IconsFontAwesome5.ICON_LONG_ARROW_ALT_RIGHT, self._go_forward)

            PyImGui.table_next_column()
            self._draw_nav_button("Up", IconsFontAwesome5.ICON_LEVEL_UP_ALT, self._go_up)

            PyImGui.end_table()
        style.CellPadding.pop_style_var()

    def _draw_tree_node(self, node: WidgetCatalogNode, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        selected = active_view.browser.current_path == node.path
        opened = False

        if node.children:
            opened = PyImGui.tree_node(f"{node.name}##tree_{node.path}")
            if PyImGui.is_item_clicked(0):
                self._navigate_to(node.path, view=active_view)
        else:
            if ImGui.selectable(f"{node.name}##tree_{node.path}", selected=selected):
                self._navigate_to(node.path, view=active_view)

        if opened:
            for child in WidgetCatalog.tree_children(node):
                self._draw_tree_node(child, view=active_view)
            PyImGui.tree_pop()

    def _push_outline_row_colors(self, depth: int, max_depth: int, selected: bool) -> None:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Header, (0.0, 0.0, 0.0, 0.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, (0.0, 0.0, 0.0, 0.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive, (0.0, 0.0, 0.0, 0.0))

    
    def _get_outline_row_width(self, label: str, depth: int) -> float:
        tree_labels = self.ui_catalog.tree.labels
        indent_width = float(depth * tree_labels.indent_value)
        icon_width = PyImGui.calc_text_size(IconsFontAwesome5.ICON_CARET_DOWN)[0] + tree_labels.tooltip_icon_spacing
        text_width, _ = PyImGui.calc_text_size(label)
        return tree_labels.row_padding_x + indent_width + icon_width + text_width + tree_labels.row_width_padding_right

    def _get_outline_max_width(self, root: WidgetCatalogNode, view: browser_view_state | None = None) -> float:
        expanded_paths = self._get_view_expanded_paths(view)
        widths: list[float] = []

        def collect(node: WidgetCatalogNode) -> None:
            if node.path:
                widths.append(self._get_outline_row_width(node.name, node.depth))

            if node.path and node.children and node.path not in expanded_paths:
                return

            for child in WidgetCatalog.tree_children(node):
                collect(child)

        for child in WidgetCatalog.tree_children(root):
            collect(child)

        return max(widths, default=120.0)

    def _draw_outline_selectable(self, label: str, item_id: str, depth: int, max_depth: int, selected: bool, row_width: float) -> bool:
        tree_labels = self.ui_catalog.tree.labels
        row_height_value = max(PyImGui.get_text_line_height() + tree_labels.row_height_padding_y, tree_labels.row_height_min)
        self._push_outline_row_colors(depth, max_depth, selected)
        text_color = ImGui.get_style().Text.get_current()
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 0.0, 0.0, 0.0))
        clicked = ImGui.selectable(f"##{item_id}", selected=selected, size=(row_width, row_height_value))
        PyImGui.pop_style_color(1)
        PyImGui.pop_style_color(3)

        item_min = PyImGui.get_item_rect_min()
        item_max = PyImGui.get_item_rect_max()
        fill, idle_border, border, hover_border = self._get_outline_palette(depth, max_depth)
        row_height = item_max[1] - item_min[1]
        text_y = item_min[1] + max((row_height - PyImGui.get_text_line_height()) * 0.5, 0.0)

        PyImGui.draw_list_add_rect_filled(
            item_min[0],
            item_min[1],
            item_max[0],
            item_max[1],
            fill.to_color(),
            tree_labels.row_corner_radius,
            0,
        )

        PyImGui.draw_list_add_rect(
            item_min[0],
            item_min[1],
            item_max[0],
            item_max[1],
            idle_border.to_color(),
            tree_labels.row_corner_radius,
            0,
            1.0,
        )

        if selected:
            PyImGui.draw_list_add_rect(
                item_min[0],
                item_min[1],
                item_max[0],
                item_max[1],
                border.to_color(),
                tree_labels.row_corner_radius,
                0,
                2.0,
            )
        elif PyImGui.is_item_hovered():
            PyImGui.draw_list_add_rect(
                item_min[0],
                item_min[1],
                item_max[0],
                item_max[1],
                hover_border.to_color(),
                tree_labels.row_corner_radius,
                0,
                1.0,
            )

        return clicked

    def _draw_outline_row(self, node: WidgetCatalogNode, max_depth: int, row_width: float, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        selected = active_view.browser.current_path == node.path
        if self._draw_outline_selectable(node.name, f"outline_{node.path}", node.depth, max_depth, selected, row_width):
            if node.children:
                if node.path in active_view.expanded_paths:
                    active_view.expanded_paths.remove(node.path)
                    self._navigate_to(node.path, expand_ancestors=False, view=active_view)
                else:
                    self._expand_outline_ancestors(node.path, view=active_view)
                    self._navigate_to(node.path, expand_ancestors=False, view=active_view)
            else:
                self._navigate_to(node.path, view=active_view)

        item_min = PyImGui.get_item_rect_min()
        text_color = ImGui.get_style().Text.get_current()
        tree_labels = self.ui_catalog.tree.labels
        indent_width = float(node.depth * tree_labels.indent_value)
        icon_x = item_min[0] + tree_labels.row_padding_x + indent_width
        text_x = icon_x
        item_max = PyImGui.get_item_rect_max()
        row_height = item_max[1] - item_min[1]
        text_y = item_min[1] + max((row_height - PyImGui.get_text_line_height()) * 0.5, 0.0)

        if node.children:
            icon = IconsFontAwesome5.ICON_CARET_DOWN if node.path in active_view.expanded_paths else IconsFontAwesome5.ICON_CARET_RIGHT
            icon_width, _ = PyImGui.calc_text_size(icon)
            PyImGui.draw_list_add_text(
                icon_x,
                text_y,
                text_color.color_int,
                icon,
            )
            text_x = icon_x + icon_width + tree_labels.tooltip_icon_spacing

        PyImGui.draw_list_add_text(
            text_x,
            text_y,
            text_color.color_int,
            node.name,
        )

        if PyImGui.is_item_hovered():
            folder_count = len(WidgetCatalog.tree_children(node))
            widget_count = len(node.widget_ids)
            PyImGui.set_tooltip(f"/{node.path}\nFolders: {folder_count}\nWidgets: {widget_count}")

    def _draw_outline_rows(self, node: WidgetCatalogNode, max_depth: int, row_width: float, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        if node.path:
            self._draw_outline_row(node, max_depth, row_width, view=active_view)

        if node.path and node.children and node.path not in active_view.expanded_paths:
            return

        for child in WidgetCatalog.tree_children(node):
            self._draw_outline_rows(child, max_depth, row_width, view=active_view)

    def _draw_folder_outline(self, browser_root: WidgetCatalogNode, view: browser_view_state | None = None) -> None:
        self.tree_panel.draw(browser_root, view=view)

    def _draw_detail_contents_list(self, snapshot, node: WidgetCatalogNode, favorite_ids: set[str], can_go_up: bool, view: browser_view_state | None = None) -> None:
        active_view = view or self._get_active_view()
        detail_header = self.ui_catalog.detail.header
        detail_rows = self.ui_catalog.detail.rows
        row_height = detail_rows.row_height
        folders = WidgetCatalog.tree_children(node)
        virtual_folders: list[WidgetCatalogNode] = []
        regular_folders: list[WidgetCatalogNode] = folders
        if not node.path:
            virtual_folders, regular_folders = self._get_root_folder_groups(node)
        widgets = [snapshot.widgets_by_id.get(widget_id) for widget_id in node.widget_ids]
        widgets = [widget for widget in widgets if widget is not None]

        if not folders and not widgets:
            PyImGui.text_disabled("No contents in this location.")
            return

        if not ImGui.begin_child(f"##detail_contents_list_{active_view.view_id}", (0, 0), False, PyImGui.WindowFlags.HorizontalScrollbar):
            return

        configured_total_width = detail_header.name_width + detail_header.favorite_width + detail_header.config_width
        total_width = max(PyImGui.get_content_region_avail()[0], detail_header.total_width_min, configured_total_width)
        self._draw_detail_header_row(total_width, detail_header.row_height)

        if can_go_up:
            folder_up_uv0, folder_up_uv1 = self.FOLDER_ICON_UVS["folder_up"]
            self._draw_detail_explorer_row(
                f"detail_go_up_{active_view.view_id}",
                total_width,
                row_height,
                self.FOLDER_ICON_ATLAS,
                folder_up_uv0,
                folder_up_uv1,
                "..",
                on_primary_click=lambda v=active_view: self._go_up(view=v),
            )

        for index, child in enumerate(virtual_folders):
            folder_uv0, folder_uv1 = self.FOLDER_ICON_UVS["folder"]
            self._draw_detail_explorer_row(
                f"detail_virtual_folder_{active_view.view_id}_{child.path}",
                total_width,
                row_height,
                self.FOLDER_ICON_ATLAS,
                folder_uv0,
                folder_uv1,
                child.name,
                on_primary_click=lambda path=child.path, v=active_view: self._navigate_to(path, sync_outline=True, view=v),
            )
            if index == 0 and len(virtual_folders) > 1:
                PyImGui.separator()

        if virtual_folders and regular_folders:
            PyImGui.separator()

        for child in regular_folders:
            folder_uv0, folder_uv1 = self.FOLDER_ICON_UVS["folder"]
            self._draw_detail_explorer_row(
                f"detail_folder_{active_view.view_id}_{child.path}",
                total_width,
                row_height,
                self.FOLDER_ICON_ATLAS,
                folder_uv0,
                folder_uv1,
                child.name,
                on_primary_click=lambda path=child.path, v=active_view: self._navigate_to(path, sync_outline=True, view=v),
            )

        for widget in widgets:
            label = widget.name if widget.name else widget.folder_script_name
            is_favorite = widget.folder_script_name in favorite_ids
            has_config = bool(widget.has_configure_property)
            has_icon = not WidgetCatalog._has_missing_icon(widget)
            favorite_uv0, favorite_uv1 = self.FOLDER_ICON_UVS["heart_full" if is_favorite else "heart_empty"]
            config_uv0, config_uv1 = self.FOLDER_ICON_UVS["config_active" if widget.configuring else "config"]

            self._draw_detail_explorer_row(
                f"widget_{active_view.view_id}_{widget.folder_script_name}",
                total_width,
                row_height,
                widget.image if has_icon else None,
                (0.0, 0.0),
                (1.0, 1.0),
                label if has_icon else f"{IconsFontAwesome5.ICON_FILE_CODE} {label}",
                on_primary_click=lambda w=widget: self._set_widget_active(w, not w.enabled),
                active=widget.enabled,
                favorite_texture=self.FOLDER_ICON_ATLAS,
                favorite_uv0=favorite_uv0,
                favorite_uv1=favorite_uv1,
                on_favorite_click=lambda w=widget, fav=is_favorite: self._set_widget_favorite(w, not fav),
                config_texture=self.FOLDER_ICON_ATLAS if has_config else None,
                config_uv0=config_uv0,
                config_uv1=config_uv1,
                on_config_click=(lambda w=widget: w.set_configuring(not w.configuring)) if has_config else None,
            )
            if PyImGui.is_item_hovered():
                self._draw_widget_hover_card(widget)

        ImGui.end_child()

    def _draw_detail_panel(self, snapshot, browser_root: WidgetCatalogNode, view: browser_view_state | None = None) -> None:
        self.detail_panel.draw_panel(snapshot, browser_root, view=view)

    def _reload_widgets_from_menu(self) -> None:
        self.widget_manager.reload_widgets()
        self.runtime.tree_width_pending_apply = True
        self.runtime.tree_layout_revision += 1

    def _toggle_optional_widgets_from_menu(self) -> None:
        self.widget_manager.toggle_optional_widgets_paused()

    def _draw_menu_bar(self) -> None:
        if ImGui.begin_menu_bar():
            if ImGui.button(f"{IconsFontAwesome5.ICON_RETWEET} Reload"):
                self._reload_widgets_from_menu()
            ImGui.show_tooltip("Reload all widgets from disk.")

            PyImGui.same_line(0, 8)

            pause_label = "Pause" if not self.widget_manager.optional_widgets_paused else "Resume"
            pause_icon = IconsFontAwesome5.ICON_PAUSE if not self.widget_manager.optional_widgets_paused else IconsFontAwesome5.ICON_PLAY
            if ImGui.button(f"{pause_icon} {pause_label}"):
                self._toggle_optional_widgets_from_menu()
            ImGui.show_tooltip(
                "Pause the execution of non-system widgets."
                if not self.widget_manager.optional_widgets_paused
                else "Resume the execution of non-system widgets."
            )

            PyImGui.same_line(0, 8)

            if ImGui.begin_menu("Settings"):
                if ImGui.menu_item("Switch To Advanced UI"):
                    IniManager().set(key=self.ini_key, var_name="show_adavanced", value=True, section="Configuration")
                    IniManager().save_vars(self.ini_key)
                    self.runtime.show_adavanced = True
                ImGui.show_tooltip("Switch from the catalog UI to the advanced widget manager.")
                PyImGui.separator()
                if ImGui.menu_item("Layout Preferences"):
                    self.runtime.show_setup_window = True
                ImGui.show_tooltip("Open the Widget Catalog configuration window.")
                ImGui.end_menu()
            ImGui.end_menu_bar()

    def _draw_setup_window(self) -> None:
        if not self.runtime.show_setup_window:
            self.runtime.setup_snapshot_captured = False
            return

        expanded, open_ = ImGui.BeginWithClose(
            ini_key=self.setup_ini_key,
            name="Widget Catalog Setup",
            p_open=self.runtime.show_setup_window,
            flags=PyImGui.WindowFlags.AlwaysAutoResize,
        )
        self.runtime.show_setup_window = open_
        if not self.runtime.show_setup_window:
            self.runtime.setup_snapshot_captured = False

        if expanded:
            if not self.runtime.setup_snapshot_captured:
                self._capture_setup_snapshot()
            PyImGui.text("Catalog Configuration")
            PyImGui.text_wrapped("Navigation settings apply immediately. Floating icon styling is saved in this catalog, while the floating button position is persisted by its own window config.")
            PyImGui.separator()

            pyimgui_io = PyImGui.get_io()
            max_x = max(float(pyimgui_io.display_size_x), float(self.floating_button.position[0]) + 1.0)
            max_y = max(float(pyimgui_io.display_size_y), float(self.floating_button.position[1]) + 1.0)

            if ImGui.collapsing_header("Address Bar"):
                address_bar = self.config.address_bar
                button_size = ImGui.slider_int("Navigation Button Size", address_bar.button_size, address_bar.button_size_min, address_bar.button_size_max)
                if button_size != address_bar.button_size:
                    address_bar.button_size = max(1, button_size)
                    self._save_config()
                ImGui.show_tooltip("Controls the size of the Back, Forward, and Up buttons.")

                gradient_start = ImGui.color_edit4("Gradient Start", address_bar.gradient_start.color_tuple)
                if gradient_start != address_bar.gradient_start.color_tuple:
                    address_bar.gradient_start = Color.from_tuple_normalized(gradient_start)
                    self._save_config()

                gradient_end = ImGui.color_edit4("Gradient End", address_bar.gradient_end.color_tuple)
                if gradient_end != address_bar.gradient_end.color_tuple:
                    address_bar.gradient_end = Color.from_tuple_normalized(gradient_end)
                    self._save_config()

            if ImGui.collapsing_header("Floating Icon"):
                floating_icon = self.config.floating_icon
                PyImGui.text_wrapped("The icon can be dragged directly in the UI. These controls update its position and appearance immediately.")

                icon_x = ImGui.slider_float("Icon X", float(self.floating_button.position[0]), 0.0, max_x)
                icon_y = ImGui.slider_float("Icon Y", float(self.floating_button.position[1]), 0.0, max_y)
                if icon_x != float(self.floating_button.position[0]) or icon_y != float(self.floating_button.position[1]):
                    self.floating_button.position = (icon_x, icon_y)
                    self._save_floating_position()

                if ImGui.button("Reset Position", width=140):
                    self._reset_floating_position()
                ImGui.show_tooltip("Move the floating icon back to its default position.")

                PyImGui.text(f"Current position: ({self.floating_button.position[0]:.1f}, {self.floating_button.position[1]:.1f})")
                PyImGui.separator()

                icon_path = ImGui.input_text("Icon Texture", self._texture_display_path(self.floating_button.icon_path))
                if icon_path != self._texture_display_path(self.floating_button.icon_path):
                    self.floating_button.icon_path = self._texture_from_ini_path(icon_path)
                    self._save_floating_config()
                ImGui.show_tooltip("Path to the texture used by the floating icon.")

                if ImGui.button("Browse Texture...", width=140):
                    selected = self._pick_texture_path()
                    if selected:
                        self.floating_button.icon_path = self._texture_from_ini_path(selected)
                        self._save_floating_config()
                ImGui.show_tooltip("Select an icon texture from disk.")

                PyImGui.same_line(0, 8)
                if ImGui.button("Use Default Icon", width=140):
                    self.floating_button.icon_path = self._default_floating_icon_path()
                    self._save_floating_config()
                ImGui.show_tooltip("Restore the default Py4GW round python icon.")

                icon_size = ImGui.slider_float("Icon Size", float(self.floating_button.button_size), floating_icon.button_size_min, floating_icon.button_size_max)
                if icon_size != float(self.floating_button.button_size):
                    self.floating_button.button_size = max(1.0, icon_size)
                    self._save_floating_config()
                ImGui.show_tooltip("Base size of the floating icon button.")

                idle_scale = ImGui.slider_float("Idle Scale", float(self.floating_button.idle_icon_scale), floating_icon.idle_scale_min, floating_icon.idle_scale_max)
                if idle_scale != float(self.floating_button.idle_icon_scale):
                    self.floating_button.idle_icon_scale = max(0.1, idle_scale)
                    self._save_floating_config()
                ImGui.show_tooltip("Scale of the icon when it is not being hovered.")

                hover_scale = ImGui.slider_float("Hover Scale", float(self.floating_button.hover_icon_scale), floating_icon.hover_scale_min, floating_icon.hover_scale_max)
                if hover_scale != float(self.floating_button.hover_icon_scale):
                    self.floating_button.hover_icon_scale = max(0.1, hover_scale)
                    self._save_floating_config()
                ImGui.show_tooltip("Scale of the icon while hovered.")

                if ImGui.button("Reset Floating Style", width=160):
                    self._reset_floating_style()
                ImGui.show_tooltip("Restore the floating icon appearance defaults.")

                PyImGui.text(f"Current texture: {self._texture_display_path(self.floating_button.icon_path)}")

            if ImGui.collapsing_header("Tree"):
                tree_config = self.ui_catalog.tree
                tree_labels = self.ui_catalog.tree.labels

                tree_width = ImGui.slider_float("Tree Width", float(tree_config.width), 120.0, 500.0)
                if tree_width != float(tree_config.width):
                    tree_config.width = max(80.0, tree_width)
                    self.runtime.tree_width_pending_apply = True
                    self.runtime.tree_layout_revision += 1
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Controls the fixed width of the tree column in pixels.")

                indent_value = ImGui.slider_float("Indent Step", float(tree_labels.indent_value), 0.0, 40.0)
                if indent_value != float(tree_labels.indent_value):
                    tree_labels.indent_value = indent_value
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Horizontal indent added per tree depth level.")

                row_height_min = ImGui.slider_float("Row Height Min", float(tree_labels.row_height_min), 8.0, 40.0)
                if row_height_min != float(tree_labels.row_height_min):
                    tree_labels.row_height_min = max(1.0, row_height_min)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Minimum selectable row height in the tree.")

                row_height_padding_y = ImGui.slider_float("Row Height Padding", float(tree_labels.row_height_padding_y), 0.0, 12.0)
                if row_height_padding_y != float(tree_labels.row_height_padding_y):
                    tree_labels.row_height_padding_y = max(0.0, row_height_padding_y)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Extra height added on top of text height for tree rows.")

                row_padding_x = ImGui.slider_float("Row Padding X", float(tree_labels.row_padding_x), 0.0, 24.0)
                if row_padding_x != float(tree_labels.row_padding_x):
                    tree_labels.row_padding_x = max(0.0, row_padding_x)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Left padding before the tree row content begins.")

                row_width_padding_right = ImGui.slider_float("Row Width Padding", float(tree_labels.row_width_padding_right), 0.0, 32.0)
                if row_width_padding_right != float(tree_labels.row_width_padding_right):
                    tree_labels.row_width_padding_right = max(0.0, row_width_padding_right)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Extra width reserved to the right of each tree row.")

                row_corner_radius = ImGui.slider_float("Corner Radius", float(tree_labels.row_corner_radius), 0.0, 12.0)
                if row_corner_radius != float(tree_labels.row_corner_radius):
                    tree_labels.row_corner_radius = max(0.0, row_corner_radius)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Rounded corner radius for the custom tree rows.")

                tooltip_icon_spacing = ImGui.slider_float("Icon Spacing", float(tree_labels.tooltip_icon_spacing), 0.0, 16.0)
                if tooltip_icon_spacing != float(tree_labels.tooltip_icon_spacing):
                    tree_labels.tooltip_icon_spacing = max(0.0, tooltip_icon_spacing)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Spacing between the tree caret icon and the label.")

            if ImGui.collapsing_header("Detail Panel"):
                detail_header = self.ui_catalog.detail.header
                detail_rows = self.ui_catalog.detail.rows

                header_row_height = ImGui.slider_float("Header Row Height", float(detail_header.row_height), 12.0, 48.0)
                if header_row_height != float(detail_header.row_height):
                    detail_header.row_height = max(1.0, header_row_height)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Height of the detail list header row.")

                total_width_min = ImGui.slider_float("Minimum List Width", float(detail_header.total_width_min), 200.0, 900.0)
                if total_width_min != float(detail_header.total_width_min):
                    detail_header.total_width_min = max(1.0, total_width_min)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Minimum width used for the right-side detail list layout.")

                favorite_width = ImGui.slider_float("Favorite Column Width", float(detail_header.favorite_width), 16.0, 140.0)
                if favorite_width != float(detail_header.favorite_width):
                    detail_header.favorite_width = max(1.0, favorite_width)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Width of the detail list favorite column.")

                config_width = ImGui.slider_float("Config Column Width", float(detail_header.config_width), 16.0, 140.0)
                if config_width != float(detail_header.config_width):
                    detail_header.config_width = max(1.0, config_width)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Width of the detail list config column.")

                name_width = ImGui.slider_float("Name Column Width", float(detail_header.name_width), 80.0, 400.0)
                if name_width != float(detail_header.name_width):
                    detail_header.name_width = max(1.0, name_width)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Fixed width reserved for the widget/folder name column.")

                PyImGui.separator()

                detail_row_height = ImGui.slider_float("Entry Row Height", float(detail_rows.row_height), 16.0, 64.0)
                if detail_row_height != float(detail_rows.row_height):
                    detail_rows.row_height = max(1.0, detail_row_height)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Height of each folder or widget row in the detail panel.")

                icon_padding = ImGui.slider_float("Icon Padding", float(detail_rows.icon_padding), 0.0, 16.0)
                if icon_padding != float(detail_rows.icon_padding):
                    detail_rows.icon_padding = max(0.0, icon_padding)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Amount removed from row height before computing icon button size.")

                icon_size_max = ImGui.slider_float("Max Icon Size", float(detail_rows.icon_size_max), 8.0, 48.0)
                if icon_size_max != float(detail_rows.icon_size_max):
                    detail_rows.icon_size_max = max(1.0, icon_size_max)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Maximum icon size used inside detail rows.")

                content_padding_x = ImGui.slider_float("Content Padding X", float(detail_rows.content_padding_x), 0.0, 24.0)
                if content_padding_x != float(detail_rows.content_padding_x):
                    detail_rows.content_padding_x = max(0.0, content_padding_x)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Left padding before the main detail row content.")

                content_gap_after_icon = ImGui.slider_float("Gap After Icon", float(detail_rows.content_gap_after_icon), 0.0, 32.0)
                if content_gap_after_icon != float(detail_rows.content_gap_after_icon):
                    detail_rows.content_gap_after_icon = max(0.0, content_gap_after_icon)
                    self._save_ui_catalog_config()
                ImGui.show_tooltip("Horizontal gap between a detail row icon and its label.")

            PyImGui.separator()
            if ImGui.button("Restore", width=140):
                self._restore_setup_snapshot()
            ImGui.show_tooltip("Restore the values from when this setup window was opened and keep the window open.")

            PyImGui.same_line(0, 8)
            if ImGui.button("Restore and Close", width=160):
                self._restore_setup_snapshot()
                self.runtime.setup_snapshot_captured = False
                self.runtime.show_setup_window = False
            ImGui.show_tooltip("Restore the values from when this setup window was opened, then close the window.")

            PyImGui.same_line(0, 8)
            if ImGui.button("Close", width=120):
                self.runtime.setup_snapshot_captured = False
                self.runtime.show_setup_window = False

        ImGui.End(self.setup_ini_key)

    def _draw_window(self) -> None:
        if self.runtime.expand_on_next_show:
            PyImGui.set_next_window_collapsed(False, PyImGui.ImGuiCond.Always)
            self.runtime.expand_on_next_show = False

        min_window_width = DEFAULT_WINDOW_WIDTH
        min_window_height = DEFAULT_WINDOW_HEIGHT
        flags = PyImGui.WindowFlags.NoCollapse | PyImGui.WindowFlags.MenuBar

        expanded, open_ = ImGui.BeginWithClose(
            ini_key=self.ini_key,
            name=f"{self.module_name}",
            p_open=self.floating_button.visible,
            flags= flags,
        )

        if expanded:
            window_size = PyImGui.get_window_size()
            clamped_width = max(min_window_width, float(window_size[0]))
            clamped_height = max(min_window_height, float(window_size[1]))
            if clamped_width != float(window_size[0]) or clamped_height != float(window_size[1]):
                PyImGui.set_window_size(clamped_width, clamped_height, PyImGui.ImGuiCond.Always)

            self._draw_menu_bar()
            snapshot = self._get_snapshot()
            browser_root = self._get_browser_tree(snapshot)
            PyImGui.separator()
            self._draw_breadcrumb_bar(browser_root)
            PyImGui.separator()
            #self._draw_nav_buttons()
            #PyImGui.separator()

            layout_avail_width, layout_avail_height = PyImGui.get_content_region_avail()
            layout_height = max(1.0, float(layout_avail_height))
            if PyImGui.begin_table(
                f"widget_catalog_layout##main_split_{self.runtime.tree_layout_instance_id}_{self.runtime.tree_layout_revision}",
                2,
                PyImGui.TableFlags.Resizable
                | PyImGui.TableFlags.BordersInnerV
                | PyImGui.TableFlags.NoSavedSettings,
                0,
                layout_height,
            ):
                safe_layout_width = max(1.0, float(layout_avail_width))
                tree_width = min(max(1.0, float(self.ui_catalog.tree.width)), safe_layout_width)
                PyImGui.table_setup_column("Tree##layout_tree", PyImGui.TableColumnFlags.WidthFixed, tree_width)
                PyImGui.table_setup_column("Detail##layout_detail", PyImGui.TableColumnFlags.WidthStretch, 1.0)
                PyImGui.table_next_row()

                PyImGui.table_set_column_index(0)
                if self.runtime.tree_width_pending_apply:
                    self.runtime.tree_width_pending_apply = False
                else:
                    live_tree_width = min(max(1.0, float(PyImGui.get_content_region_avail()[0])), safe_layout_width)
                    if abs(live_tree_width - float(self.ui_catalog.tree.width)) > 0.5:
                        self.ui_catalog.tree.width = live_tree_width
                        self._save_ui_catalog_config()
                if ImGui.begin_child("##widget_tree_column", (0, 0), True, PyImGui.WindowFlags.HorizontalScrollbar):
                    self._draw_folder_outline(browser_root)
                ImGui.end_child()

                PyImGui.table_set_column_index(1)
                if ImGui.begin_child("##widget_detail_column", (0, 0), False):
                    detail_avail_width, detail_avail_height = PyImGui.get_content_region_avail()
                    if float(detail_avail_width) >= WidgetCatalogDetailPanel.MIN_RENDER_WIDTH and float(detail_avail_height) >= WidgetCatalogDetailPanel.MIN_RENDER_HEIGHT:
                        self._draw_detail_panel(snapshot, browser_root)
                    else:
                        PyImGui.text_disabled("...")
                ImGui.end_child()

                PyImGui.end_table()

        ImGui.End(self.ini_key)
        self.floating_button.sync_begin_with_close(open_)
        self._draw_setup_window()

    def draw_UI(self) -> None:
        self._load_config_if_needed()
        self.floating_button.draw(self.floating_ini_key)


_default_window: WidgetCatalogWindow | None = None


def _ensure_ini() -> bool:
    global INI_KEY, FLOATING_INI_KEY, SETUP_INI_KEY, INI_INIT
    if INI_INIT:
        return True

    config_defaults = config_vars()
    ui_catalog_defaults = ui_catalog_vars()

    if not os.path.exists(INI_PATH):
        os.makedirs(INI_PATH, exist_ok=True)

    INI_KEY = IniManager().ensure_global_key(INI_PATH, INI_FILENAME)
    FLOATING_INI_KEY = IniManager().ensure_global_key(INI_PATH, FLOATING_INI_FILENAME)
    SETUP_INI_KEY = IniManager().ensure_global_key(INI_PATH, SETUP_INI_FILENAME)
    if not INI_KEY or not FLOATING_INI_KEY or not SETUP_INI_KEY:
        return False

    IniManager().add_bool(INI_KEY, "init", "Window config", "init", default=True)
    IniManager().add_bool(INI_KEY, "show_adavanced", "Configuration", "show_adavanced", default=False)
    IniManager().add_int(INI_KEY, "button_size", "Navigation", "button_size", default=config_defaults.address_bar.button_size)
    IniManager().add_str(INI_KEY, "gradient_start", "Navigation", "gradient_start", default=config_defaults.address_bar.gradient_start.to_rgba_string())
    IniManager().add_str(INI_KEY, "gradient_end", "Navigation", "gradient_end", default=config_defaults.address_bar.gradient_end.to_rgba_string())
    IniManager().add_str(INI_KEY, "floating_icon_path", "Floating Icon", "icon_path", default="python_icon_round.png")
    IniManager().add_float(INI_KEY, "floating_button_size", "Floating Icon", "button_size", default=config_defaults.floating_icon.button_size)
    IniManager().add_float(INI_KEY, "floating_idle_icon_scale", "Floating Icon", "idle_icon_scale", default=config_defaults.floating_icon.idle_scale)
    IniManager().add_float(INI_KEY, "floating_hover_icon_scale", "Floating Icon", "hover_icon_scale", default=config_defaults.floating_icon.hover_scale)
    IniManager().add_float(INI_KEY, "tree_indent_value", "Tree", "indent_value", default=ui_catalog_defaults.tree.labels.indent_value)
    IniManager().add_float(INI_KEY, "tree_width", "Tree", "width", default=ui_catalog_defaults.tree.width)
    IniManager().add_float(INI_KEY, "tree_row_height_min", "Tree", "row_height_min", default=ui_catalog_defaults.tree.labels.row_height_min)
    IniManager().add_float(INI_KEY, "tree_row_height_padding_y", "Tree", "row_height_padding_y", default=ui_catalog_defaults.tree.labels.row_height_padding_y)
    IniManager().add_float(INI_KEY, "tree_row_padding_x", "Tree", "row_padding_x", default=ui_catalog_defaults.tree.labels.row_padding_x)
    IniManager().add_float(INI_KEY, "tree_row_width_padding_right", "Tree", "row_width_padding_right", default=ui_catalog_defaults.tree.labels.row_width_padding_right)
    IniManager().add_float(INI_KEY, "tree_row_corner_radius", "Tree", "row_corner_radius", default=ui_catalog_defaults.tree.labels.row_corner_radius)
    IniManager().add_float(INI_KEY, "tree_tooltip_icon_spacing", "Tree", "tooltip_icon_spacing", default=ui_catalog_defaults.tree.labels.tooltip_icon_spacing)
    IniManager().add_float(INI_KEY, "detail_header_row_height", "Detail Panel", "header_row_height", default=ui_catalog_defaults.detail.header.row_height)
    IniManager().add_float(INI_KEY, "detail_total_width_min", "Detail Panel", "total_width_min", default=ui_catalog_defaults.detail.header.total_width_min)
    IniManager().add_float(INI_KEY, "detail_favorite_width", "Detail Panel", "favorite_width", default=ui_catalog_defaults.detail.header.favorite_width)
    IniManager().add_float(INI_KEY, "detail_config_width", "Detail Panel", "config_width", default=ui_catalog_defaults.detail.header.config_width)
    IniManager().add_float(INI_KEY, "detail_name_width", "Detail Panel", "name_width", default=ui_catalog_defaults.detail.header.name_width)
    IniManager().add_float(INI_KEY, "detail_row_height", "Detail Panel", "row_height", default=ui_catalog_defaults.detail.rows.row_height)
    IniManager().add_float(INI_KEY, "detail_icon_padding", "Detail Panel", "icon_padding", default=ui_catalog_defaults.detail.rows.icon_padding)
    IniManager().add_float(INI_KEY, "detail_icon_size_max", "Detail Panel", "icon_size_max", default=ui_catalog_defaults.detail.rows.icon_size_max)
    IniManager().add_float(INI_KEY, "detail_content_padding_x", "Detail Panel", "content_padding_x", default=ui_catalog_defaults.detail.rows.content_padding_x)
    IniManager().add_float(INI_KEY, "detail_content_gap_after_icon", "Detail Panel", "content_gap_after_icon", default=ui_catalog_defaults.detail.rows.content_gap_after_icon)
    IniManager().add_str(INI_KEY, "saved_entries", "Search", "saved_entries", default="")
    IniManager().load_once(INI_KEY)
    IniManager().set(INI_KEY, "init", True)
    IniManager().save_vars(INI_KEY)

    IniManager().add_bool(FLOATING_INI_KEY, "init", "Window config", "init", default=True)
    IniManager().add_bool(FLOATING_INI_KEY, "show_main_window", "Configuration", "show_main_window", default=True)
    IniManager().load_once(FLOATING_INI_KEY)
    IniManager().set(FLOATING_INI_KEY, "init", True)
    IniManager().save_vars(FLOATING_INI_KEY)

    IniManager().add_bool(SETUP_INI_KEY, "init", "Window config", "init", default=True)
    IniManager().load_once(SETUP_INI_KEY)
    IniManager().set(SETUP_INI_KEY, "init", True)
    IniManager().save_vars(SETUP_INI_KEY)

    INI_INIT = True
    return True


def draw() -> None:
    global _default_window, INITIALIZED
    if not INITIALIZED or _default_window is None:
        return
    _default_window.draw_UI()


def show_adavanced_enabled() -> bool:
    global _default_window, INITIALIZED
    if not INITIALIZED or _default_window is None:
        return False
    _default_window._load_config_if_needed()
    _default_window.runtime.show_adavanced = bool(
        IniManager().get(_default_window.ini_key, "show_adavanced", default=False, section="Configuration")
    )
    return _default_window.runtime.show_adavanced


def main() -> None:
    global _default_window, INITIALIZED
    widget_handler = get_widget_handler()
    if INITIALIZED:
        return
    if not _ensure_ini():
        return

    if _default_window is None:
        _default_window = WidgetCatalogWindow(
            INI_KEY,
            MODULE_NAME,
            widget_handler,
            floating_ini_key=FLOATING_INI_KEY,
            setup_ini_key=SETUP_INI_KEY,
        )

    INITIALIZED = True


if __name__ == "__main__":
    main()
