# ========================================================================
# Frame Showcase — Comprehensive UIManager Feature Explorer & Tester
# ========================================================================
import Py4GW
from Py4GWCoreLib import (UIManager, Color, Utils, ManagedWindowSpec, WindowFactory, WindowVarSpec)
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager
import PyImGui, PyUIManager, PyCallback, PyOverlay
import json, ctypes, os, time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set

# ========================================================================
# Module Constants
# ========================================================================
MODULE_NAME = "Frame Showcase"
MODULE_ICON = "Textures/Module_Icons/Frame Tester.png"

THROTTLE_TREE_MS = 2000
LOG_BUFFER_SIZE = 500
projects_root = Py4GW.Console.get_projects_path()
json_file_name = os.path.join(projects_root, "Py4GWCoreLib", "frame_aliases.json")


# ========================================================================
# WindowFactory Setup
# ========================================================================
_window_factory = WindowFactory("Coding/Debug/Guild Wars")
_window_factory.register_window(
    ManagedWindowSpec(
        identifier="main",
        filename="frame_showcase.ini",
        title="Frame Showcase — UIManager Explorer",
        flags=PyImGui.WindowFlags.NoFlag,
        open_var_name="open",
        open_default=True,
    )
)


# ========================================================================
# ShowcaseConfig — Persistent Configuration via WindowVarSpec
# ========================================================================
@dataclass
class ShowcaseConfig:
    keep_data_updated: bool = False
    recolor_frame_tree: bool = True
    not_created_color: Tuple[float, float, float, float] = field(default_factory=lambda: Utils.RGBToNormal(150, 150, 150, 255))
    not_visible_color: Tuple[float, float, float, float] = field(default_factory=lambda: Utils.RGBToNormal(180, 0, 0, 255))
    no_hash_color: Tuple[float, float, float, float] = field(default_factory=lambda: Utils.RGBToNormal(150, 0, 150, 255))
    identified_color: Tuple[float, float, float, float] = field(default_factory=lambda: Utils.RGBToNormal(200, 180, 0, 255))
    base_color: Tuple[float, float, float, float] = field(default_factory=lambda: Utils.RGBToNormal(255, 255, 255, 255))
    draw_color: Tuple[float, float, float, float] = field(default_factory=lambda: (0.0, 1.0, 0.0, 0.5))
    draw_thickness: float = 1.0
    auto_refresh_logs: bool = True


_config = ShowcaseConfig()


# ========================================================================
# FrameNode — Lazy get_context(), Tree Node Render, Tooltip, Context Menu
# ========================================================================
class FrameNode:
    """Represents a single frame in the hierarchy tree."""

    def __init__(self, frame_id: int, parent_id: int, tree: "FrameTree"):
        self.frame_id = frame_id
        self.parent_id = parent_id
        self.tree = tree
        self._frame_obj = PyUIManager.UIFrame(frame_id)
        self.frame_hash = self._frame_obj.frame_hash
        self.child_offset_id = self._frame_obj.child_offset_id
        self.label = UIManager.GetEntryFromJSON(json_file_name, frame_id) or ""
        self.type = self._frame_obj.type
        self.template_type = self._frame_obj.template_type
        self.parent: Optional["FrameNode"] = None
        self.children: List["FrameNode"] = []
        self._show_inline_data = False
        self._inspector_requested = False

    def choose_frame_color(self) -> Tuple[float, float, float, float]:
        if not self._frame_obj.is_created:
            return _config.not_created_color
        elif not self._frame_obj.is_visible:
            return _config.not_visible_color
        elif self.label:
            return _config.identified_color
        elif not self.frame_hash or self.frame_hash == 0:
            return _config.no_hash_color
        else:
            return _config.base_color

    def _matches_search(self) -> bool:
        query = self.tree._active_filter
        if not query:
            return True
        ql = query.lower()
        if ql in str(self.frame_id):
            return True
        if ql in str(self.frame_hash):
            return True
        if ql in self.label.lower():
            return True
        return False

    def _get_badge_str(self) -> str:
        badges = []
        if not self._frame_obj.is_created:
            badges.append("[!]")
        if not self._frame_obj.is_visible and self._frame_obj.is_created:
            badges.append("[H]")
        if self.children:
            badges.append(f"+{len(self.children)}")
        return " ".join(badges)

    def draw(self):
        """Recursively renders the tree hierarchy using raw PyImGui.tree_node()."""
        col = self.choose_frame_color()
        badge = self._get_badge_str()
        label_text = self.label or "(no label)"
        tree_label = f"Frame:[{self.frame_id}] <{self.frame_hash}> {label_text} {badge}##ftsn_{self.frame_id}"

        has_children = len(self.children) > 0
        expanded = False

        if has_children:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, col)
            expanded = PyImGui.tree_node(tree_label)
            PyImGui.pop_style_color(1)

            if expanded:
                PyImGui.same_line(0, -1)
                self._show_inline_data = ImGui.toggle_button(
                    f"Data##ftsn_{self.frame_id}", self._show_inline_data, width=60, height=17
                )
                if _config.keep_data_updated:
                    if PyImGui.collapsing_header(f"Frame#{self.frame_id}Inline##ftsn_{self.frame_id}"):
                        headers = ["Property", "Value"]
                        data = [
                            ("Parent:", str(self.parent_id)),
                            ("Is Visible:", str(self._frame_obj.is_visible)),
                            ("Is Created:", str(self._frame_obj.is_created)),
                            ("Type:", str(self.type)),
                            ("Template:", str(self.template_type)),
                        ]
                        ImGui.table(f"ftsn_inline_{self.frame_id}", headers, data)
                PyImGui.separator()
                for child in self.children:
                    if not self.tree._active_filter or child._matches_search():
                        child.draw()
                PyImGui.tree_pop()
        else:
            PyImGui.text_colored(tree_label, col)
            PyImGui.same_line(0, -1)
            self._show_inline_data = ImGui.toggle_button(
                f"Data##ftsn_{self.frame_id}", self._show_inline_data, width=60, height=17
            )
            if _config.keep_data_updated:
                if PyImGui.collapsing_header(f"Frame#{self.frame_id}Inline##ftsn_{self.frame_id}"):
                    headers = ["Property", "Value"]
                    data = [
                        ("Parent:", str(self.parent_id)),
                        ("Is Visible:", str(self._frame_obj.is_visible)),
                        ("Is Created:", str(self._frame_obj.is_created)),
                        ("Type:", str(self.type)),
                        ("Template:", str(self.template_type)),
                    ]
                    ImGui.table(f"ftsn_inline_{self.frame_id}", headers, data)
            PyImGui.separator()

        # Right-click detection on the label just rendered (works for both tree_node and text_colored)
        right_clicked = PyImGui.is_item_hovered() and PyImGui.is_mouse_clicked(1)
        item_hovered = PyImGui.is_item_hovered()

        # Context menu (rendered after node, regardless of expand/collapse state)
        popup_id = f"ftsn_ctx_{self.frame_id}"
        if right_clicked:
            PyImGui.open_popup(popup_id)

        if PyImGui.begin_popup(popup_id):
            if PyImGui.menu_item(f"Inspect Frame {self.frame_id}"):
                self.tree._inspector_open_requests.append(self.frame_id)
            if PyImGui.menu_item(f"Copy Frame ID: {self.frame_id}"):
                PyImGui.set_clipboard_text(str(self.frame_id))
            if PyImGui.menu_item(f"Copy Frame Hash: {self.frame_hash}"):
                PyImGui.set_clipboard_text(str(self.frame_hash))
            if PyImGui.menu_item("Draw Outline (Green)"):
                UIManager().DrawFrameOutline(self.frame_id, Utils.RGBToColor(0, 255, 0, 200))
            PyImGui.separator()
            if PyImGui.menu_item("Copy Label"):
                PyImGui.set_clipboard_text(self.label)
            if PyImGui.menu_item("Copy Tree Path"):
                path = UIManager.ConstructFramePath(self.frame_id)
                PyImGui.set_clipboard_text(path if path else str(self.frame_id))
            PyImGui.end_popup()

        # Hover tooltip (uses item_hovered from the label above)
        if item_hovered:
            PyImGui.begin_tooltip()
            PyImGui.text(f"Frame ID: {self.frame_id}")
            PyImGui.text(f"Hash: {self.frame_hash}")
            PyImGui.text(f"Parent ID: {self.parent_id}")
            PyImGui.text(f"Created: {self._frame_obj.is_created}")
            PyImGui.text(f"Visible: {self._frame_obj.is_visible}")
            PyImGui.text(f"Type: {self.type}")
            PyImGui.text(f"Template: {self.template_type}")
            PyImGui.text(f"Children: {len(self.children)}")
            PyImGui.text(f"Label: {self.label}")
            PyImGui.text(f"Offset ID: {self.child_offset_id}")
            if self.label:
                PyImGui.spacing()
                PyImGui.text_colored(f"Alias: {self.label}", (0.5, 0.8, 1.0, 1.0))
            PyImGui.end_tooltip()

        if self._show_inline_data and not self._inspector_requested:
            self._inspector_requested = True
            self._open_inspector_request()


    def _open_inspector_request(self):
        """Request inspector to be opened for this frame."""
        self.tree._inspector_open_requests.append(self.frame_id)


# ========================================================================
# FrameTree — Hierarchy Builder, Search, Throttled Update
# ========================================================================
class FrameTree:
    def __init__(self):
        self.nodes: Dict[int, FrameNode] = {}
        self.root: Optional[FrameNode] = None
        self._input_query: str = ""
        self._active_filter: str = ""
        self._inspector_open_requests: List[int] = []
        self._last_build_time = 0
        self._built = False

    def build_tree(self, frame_list: List[int]):
        """Build the frame hierarchy from a list of frame IDs."""
        self.nodes.clear()
        self.root = None

        # Phase 1: Create nodes (UIFrame for all, but no get_context())
        for frame_id in frame_list:
            parent_id = UIManager.GetParentFrameID(frame_id)
            if parent_id < 0:
                parent_id = 0
            self.nodes[frame_id] = FrameNode(frame_id, parent_id, self)

        # Phase 2: Assign parent/child relationships
        for frame_id, node in self.nodes.items():
            if node.parent_id == 0 or node.parent_id not in self.nodes:
                self.root = node
            elif node.parent_id in self.nodes:
                node.parent = self.nodes[node.parent_id]
                self.nodes[node.parent_id].children.append(node)

        self._built = True
        self._last_build_time = time.time()

    def get_node(self, frame_id: int) -> Optional[FrameNode]:
        return self.nodes.get(frame_id)

    def drain_inspector_requests(self) -> List[int]:
        """Returns and clears pending inspector open requests."""
        result = list(self._inspector_open_requests)
        self._inspector_open_requests.clear()
        return result

    def update(self):
        """Throttled update: re-reads frame_array and rebuilds if structure changed."""
        now = time.time()
        if now - self._last_build_time < THROTTLE_TREE_MS / 1000.0:
            return
        self._last_build_time = now
        frame_array = UIManager.GetFrameArray()
        self.build_tree(frame_array)

    def apply_filter(self):
        """Apply the input query as the active filter (deferred by one frame)."""
        self._active_filter = self._input_query

    def draw(self):
        """Draws the entire hierarchy."""
        if not self._built:
            return
        if self.root:
            if self._active_filter:
                if not self.root._matches_search() and not any(
                    c._matches_search() for c in self.root.children
                ):
                    PyImGui.text_colored("No frames match the search filter.", (1.0, 0.5, 0.0, 1.0))
                    return
            self.root.draw()


# ========================================================================
# FrameTreeExplorer — Tab 1: Hierarchical Frame Tree
# ========================================================================
class FrameTreeExplorer:
    def __init__(self, tree: FrameTree):
        self.tree = tree

    def render(self):
        if PyImGui.collapsing_header("Options", PyImGui.TreeNodeFlags.DefaultOpen):
            _config.keep_data_updated = PyImGui.checkbox("Keep Frame Data Updated", _config.keep_data_updated)
            _config.recolor_frame_tree = PyImGui.checkbox("Recolor Frame Tree", _config.recolor_frame_tree)

        # Search bar
        self.tree._input_query = PyImGui.input_text("##ft_search", self.tree._input_query, 128)
        PyImGui.same_line(0, -1)
        if PyImGui.button("Clear##ft_search_clear"):
            self.tree._input_query = ""
            self.tree._active_filter = ""
        PyImGui.same_line(0, -1)
        PyImGui.text_disabled("(applies next frame)")

        # Build/Rebuild button
        build_text = "Rebuild Frame Tree" if self.tree._built else "Build Frame Tree"
        if PyImGui.button(build_text):
            frame_array = UIManager.GetFrameArray()
            self.tree.build_tree(frame_array)

        # Apply filter on button click (deferred search)
        PyImGui.same_line(0, -1)
        if PyImGui.button("Apply Filter##ft_search_apply"):
            self.tree.apply_filter()

        # Color legend
        if _config.recolor_frame_tree:
            PyImGui.text_colored("Not Created", _config.not_created_color)
            PyImGui.same_line(0, -1)
            PyImGui.text_colored(" Not Visible", _config.not_visible_color)
            PyImGui.same_line(0, -1)
            PyImGui.text_colored(" No Hash", _config.no_hash_color)
            PyImGui.same_line(0, -1)
            PyImGui.text_colored(" Identified", _config.identified_color)
            PyImGui.same_line(0, -1)
            PyImGui.text_colored(" Base", _config.base_color)

        PyImGui.separator()

        # Tree view in scrollable child region
        if PyImGui.begin_child("FTTreeRegion", size=(0, 0), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
            if self.tree._built:
                self.tree.draw()
            else:
                PyImGui.text_colored("Click 'Build Frame Tree' to populate the hierarchy.", (0.7, 0.7, 0.7, 1.0))
        PyImGui.end_child()


# ========================================================================
# UIManagerAPITester — Tab 2: Exercise UIManager Methods
# ========================================================================
class UIManagerAPITester:
    def __init__(self):
        self._result_cache: Dict[str, str] = {}
        self._input_frame_id: int = 0
        self._input_hash: int = 0
        self._input_label: str = ""
        self._input_offset: int = 0
        self._input_offsets: str = ""
        self._input_layer: int = 0
        self._input_opacity: float = 1.0
        self._input_fade: float = 0.0
        self._input_visible: bool = True
        self._input_disabled: bool = False
        self._input_show: bool = True
        self._input_window_id: int = 0
        self._input_key: int = 0
        self._input_msgid: int = 0
        self._input_wparam: int = 0
        self._input_lparam: int = 0
        self._input_pref: int = 0
        self._input_enum_val: int = 0
        self._input_int_val: int = 0
        self._input_str_val: str = ""
        self._input_bool_val: bool = False
        self._input_relation_kind: int = 0
        self._input_start_after: int = 0
        self._input_state_bit: int = 0
        self._input_ancestor_id: int = 0
        self._input_fps_limit: int = 60
        self._input_pos_left: int = 100
        self._input_pos_top: int = 100
        self._input_pos_right: int = 300
        self._input_pos_bottom: int = 300
        self._last_result: str = ""

    def _exec(self, label: str, fn, *args) -> str:
        try:
            result = fn(*args)
            self._last_result = str(result)
            return self._last_result
        except Exception as e:
            self._last_result = f"ERROR: {e}"
            return self._last_result

    def _section_header(self, title: str) -> bool:
        return PyImGui.collapsing_header(title, PyImGui.TreeNodeFlags.NoFlag)

    def _run_button(self, label: str, fn, *args) -> str:
        """Draws a button that executes fn and caches the result."""
        cache_key = label
        PyImGui.same_line(0, -1)
        if PyImGui.button(f"Run##api_{hash(label) & 0xFFFF}"):
            self._result_cache[cache_key] = self._exec(label, fn, *args)
        result = self._result_cache.get(cache_key, "")
        if result:
            PyImGui.same_line(0, -1)
            if result.startswith("ERROR"):
                PyImGui.text_colored(result, (1.0, 0.3, 0.3, 1.0))
            else:
                PyImGui.text_colored(result, (0.3, 1.0, 0.3, 1.0))
        return result

    def render(self):
        PyImGui.text("Exercise all UIManager methods. Enter parameters, click Run.")
        PyImGui.separator()

        # --- Shared Inputs ---
        if PyImGui.collapsing_header("Shared Input Parameters", PyImGui.TreeNodeFlags.DefaultOpen):
            self._input_frame_id = PyImGui.input_int("Frame ID##api_fid", self._input_frame_id)
            self._input_hash = PyImGui.input_int("Hash##api_hash", self._input_hash)
            self._input_label = PyImGui.input_text("Label##api_label", self._input_label)
            self._input_offset = PyImGui.input_int("Child Offset##api_off", self._input_offset)
            self._input_offsets = PyImGui.input_text("Child Offsets (comma-sep)##api_offs", self._input_offsets)
            self._input_layer = PyImGui.input_int("Layer##api_layer", self._input_layer)
            self._input_opacity = PyImGui.input_float("Opacity##api_opacity", self._input_opacity)
            self._input_fade = PyImGui.input_float("Fade Time##api_fade", self._input_fade)
            self._input_key = PyImGui.input_int("Key Code##api_key", self._input_key)
            self._input_msgid = PyImGui.input_int("Message ID##api_msgid", self._input_msgid)
            self._input_wparam = PyImGui.input_int("wParam##api_wp", self._input_wparam)
            self._input_lparam = PyImGui.input_int("lParam##api_lp", self._input_lparam)
            self._input_pref = PyImGui.input_int("Preference ID##api_pref", self._input_pref)
            self._input_enum_val = PyImGui.input_int("Enum Value##api_ev", self._input_enum_val)
            self._input_int_val = PyImGui.input_int("Int Value##api_iv", self._input_int_val)
            self._input_str_val = PyImGui.input_text("String Value##api_sv", self._input_str_val)
            self._input_state_bit = PyImGui.input_int("State Bit##api_sb", self._input_state_bit)
            self._input_ancestor_id = PyImGui.input_int("Ancestor ID##api_aid", self._input_ancestor_id)
            self._input_relation_kind = PyImGui.input_int("Relation Kind##api_rk", self._input_relation_kind)
            self._input_start_after = PyImGui.input_int("Start After##api_sa", self._input_start_after)
            self._input_window_id = PyImGui.input_int("Window ID##api_wid", self._input_window_id)
            self._input_visible = PyImGui.checkbox("Visible##api_vis", self._input_visible)
            PyImGui.same_line(0, -1)
            self._input_disabled = PyImGui.checkbox("Disabled##api_dis", self._input_disabled)
            PyImGui.same_line(0, -1)
            self._input_show = PyImGui.checkbox("Show##api_show", self._input_show)
            PyImGui.same_line(0, -1)
            self._input_bool_val = PyImGui.checkbox("Bool Value##api_bv", self._input_bool_val)
            self._input_fps_limit = PyImGui.input_int("FPS Limit##api_fpslim", self._input_fps_limit)
            PyImGui.text("Window Position (Left,Top,Right,Bottom):")
            self._input_pos_left = PyImGui.input_int("##api_posl", self._input_pos_left)
            PyImGui.same_line(0, -1)
            self._input_pos_top = PyImGui.input_int("##api_post", self._input_pos_top)
            PyImGui.same_line(0, -1)
            self._input_pos_right = PyImGui.input_int("##api_posr", self._input_pos_right)
            PyImGui.same_line(0, -1)
            self._input_pos_bottom = PyImGui.input_int("##api_posb", self._input_pos_bottom)

        PyImGui.separator()

        # NOTE: All sections default-closed for scroll friendliness.
        # Configuration: open first highlight section, rest closed.

        # --- Section: Navigation ---
        if self._section_header("Navigation (GetFrameByID, GetFrameIDByLabel/Hash, etc.)"):
            PyImGui.text("GetFrameByID(frame_id) -> UIFrame")
            self._run_button("GetFrameByID", UIManager.GetFrameByID, self._input_frame_id)
            PyImGui.text("GetFrameIDByLabel(label) -> int")
            self._run_button("GetFrameIDByLabel", UIManager.GetFrameIDByLabel, self._input_label)
            PyImGui.text("GetFrameIDByHash(hash) -> int")
            self._run_button("GetFrameIDByHash", UIManager.GetFrameIDByHash, self._input_hash)
            PyImGui.text("GetChildFrameByFrameId(parent_id, offset) -> int")
            self._run_button("GetChildFrameByFrameId", UIManager.GetChildFrameByFrameId, self._input_frame_id, self._input_offset)
            PyImGui.text("GetChildFramePathByFrameId(parent_id, offsets) -> int")
            offs = [int(x.strip()) for x in self._input_offsets.split(",") if x.strip()] if self._input_offsets else []
            self._run_button("GetChildFramePathByFrameId", UIManager.GetChildFramePathByFrameId, self._input_frame_id, offs)
            PyImGui.text("GetChildFrameIdFromNameHash(parent_id, name_hash) -> int")
            self._run_button("GetChildFrameIdFromNameHash", UIManager.GetChildFrameIdFromNameHash, self._input_frame_id, self._input_hash)
            PyImGui.text("GetAllChildFrameIDs(parent_hash, offsets) -> list")
            self._run_button("GetAllChildFrameIDs", UIManager.GetAllChildFrameIDs, self._input_hash, offs)

        # --- Section: Tree Walkers ---
        if self._section_header("Tree Walkers (First/Last/Next/Prev Child, Parent)"):
            PyImGui.text("GetFirstChildFrameID(parent_id) -> int")
            self._run_button("GetFirstChildFrameID", UIManager.GetFirstChildFrameID, self._input_frame_id)
            PyImGui.text("GetLastChildFrameID(parent_id) -> int")
            self._run_button("GetLastChildFrameID", UIManager.GetLastChildFrameID, self._input_frame_id)
            PyImGui.text("GetNextChildFrameID(frame_id) -> int")
            self._run_button("GetNextChildFrameID", UIManager.GetNextChildFrameID, self._input_frame_id)
            PyImGui.text("GetPrevChildFrameID(frame_id) -> int")
            self._run_button("GetPrevChildFrameID", UIManager.GetPrevChildFrameID, self._input_frame_id)
            PyImGui.text("GetParentFrameID(frame_id) -> int")
            self._run_button("GetParentFrameID", UIManager.GetParentFrameID, self._input_frame_id)
            PyImGui.text("GetParentFrameIdDirect(frame_id) -> int")
            self._run_button("GetParentFrameIdDirect", UIManager.GetParentFrameIdDirect, self._input_frame_id)
            PyImGui.text("GetRelatedFrameID(frame_id, kind, start_after) -> int")
            self._run_button("GetRelatedFrameID", UIManager.GetRelatedFrameID, self._input_frame_id, self._input_relation_kind, self._input_start_after)

        # --- Section: Properties ---
        if self._section_header("Properties (Layer, Code, Opacity, State, UserParam, Title)"):
            PyImGui.text("GetFrameLayer(frame_id) -> int")
            self._run_button("GetFrameLayer", UIManager.GetFrameLayer, self._input_frame_id)
            PyImGui.text("SetFrameLayer(frame_id, layer) -> bool")
            self._run_button("SetFrameLayer", UIManager.SetFrameLayer, self._input_frame_id, self._input_layer)
            PyImGui.text("GetFrameCode(frame_id) -> int")
            self._run_button("GetFrameCode", UIManager.GetFrameCode, self._input_frame_id)
            PyImGui.text("GetOpacity(frame_id) -> float")
            self._run_button("GetOpacity", UIManager.GetOpacity, self._input_frame_id)
            PyImGui.text("SetOpacity(frame_id, opacity, fade_time) -> bool")
            self._run_button("SetOpacity", UIManager.SetOpacity, self._input_frame_id, self._input_opacity, self._input_fade)
            PyImGui.text("GetUserParam(frame_id) -> int")
            self._run_button("GetUserParam", UIManager.GetUserParam, self._input_frame_id)
            PyImGui.text("GetFrameTitleText(frame_id) -> str")
            self._run_button("GetFrameTitleText", UIManager.GetFrameTitleText, self._input_frame_id)
            PyImGui.text("GetStateBit(frame_id, bit) -> bool")
            self._run_button("GetStateBit", UIManager.GetStateBit, self._input_frame_id, self._input_state_bit)

        # --- Section: Geometry ---
        if self._section_header("Geometry (MinSize, NativeSize, ClientBorder, ClipRect, PositionEx)"):
            PyImGui.text("GetFrameMinSize(frame_id) -> tuple")
            self._run_button("GetFrameMinSize", UIManager.GetFrameMinSize, self._input_frame_id)
            PyImGui.text("GetFrameNativeSize(frame_id) -> tuple")
            self._run_button("GetFrameNativeSize", UIManager.GetFrameNativeSize, self._input_frame_id)
            PyImGui.text("GetFrameClientBorder(frame_id) -> tuple")
            self._run_button("GetFrameClientBorder", UIManager.GetFrameClientBorder, self._input_frame_id)
            PyImGui.text("GetFrameClipRect(frame_id) -> tuple")
            self._run_button("GetFrameClipRect", UIManager.GetFrameClipRect, self._input_frame_id)
            PyImGui.text("GetFramePositionEx(frame_id) -> tuple")
            self._run_button("GetFramePositionEx", UIManager.GetFramePositionEx, self._input_frame_id)

        # --- Section: Visibility/State ---
        if self._section_header("Visibility / State (SetVisible, SetDisabled, ShowFrame, Exists)"):
            PyImGui.text("SetVisible(frame_id, visible) -> bool")
            self._run_button("SetVisible", UIManager.SetVisible, self._input_frame_id, self._input_visible)
            PyImGui.text("SetDisabled(frame_id, disabled) -> bool")
            self._run_button("SetDisabled", UIManager.SetDisabled, self._input_frame_id, self._input_disabled)
            PyImGui.text("ShowFrame(frame_id, show) -> bool")
            self._run_button("ShowFrame", UIManager.ShowFrame, self._input_frame_id, self._input_show)
            PyImGui.text("IsVisible(frame_id) -> bool")
            self._run_button("IsVisible", UIManager.IsVisible, self._input_frame_id)
            PyImGui.text("IsFrameCreated(frame_id) -> bool")
            self._run_button("IsFrameCreated", UIManager.IsFrameCreated, self._input_frame_id)
            PyImGui.text("FrameExists(frame_id) -> bool")
            self._run_button("FrameExists", UIManager.FrameExists, self._input_frame_id)
            PyImGui.text("IsAncestorOf(frame_id, ancestor_id) -> bool")
            self._run_button("IsAncestorOf", UIManager.IsAncestorOf, self._input_frame_id, self._input_ancestor_id)

        # --- Section: Label / Text ---
        if self._section_header("Label / Text (NameHash, Label, Encoded, Decoded)"):
            PyImGui.text("GetFrameNameHash(frame_id) -> int")
            self._run_button("GetFrameNameHash", UIManager.GetFrameNameHash, self._input_frame_id)
            PyImGui.text("GetFrameLabel(frame_id) -> str")
            self._run_button("GetFrameLabel", UIManager.GetFrameLabel, self._input_frame_id)
            PyImGui.text("GetTextLabelEncoded(frame_id) -> str")
            self._run_button("GetTextLabelEncoded", UIManager.GetTextLabelEncoded, self._input_frame_id)
            PyImGui.text("GetTextLabelDecoded(frame_id) -> str")
            self._run_button("GetTextLabelDecoded", UIManager.GetTextLabelDecoded, self._input_frame_id)
            PyImGui.text("GetHashByLabel(label) -> int")
            self._run_button("GetHashByLabel", UIManager.GetHashByLabel, self._input_label)
            PyImGui.text("ConstructFramePath(frame_id) -> str")
            self._run_button("ConstructFramePath", UIManager.ConstructFramePath, self._input_frame_id)

        # --- Section: Lists ---
        if self._section_header("Lists (Overlay, Popup, FrameArray)"):
            PyImGui.text("GetOverlayFrameIDs() -> list")
            self._run_button("GetOverlayFrameIDs", UIManager.GetOverlayFrameIDs)
            PyImGui.text("GetPopupFrameIDs() -> list")
            self._run_button("GetPopupFrameIDs", UIManager.GetPopupFrameIDs)
            PyImGui.text("GetFrameArray() -> list")
            self._run_button("GetFrameArray", UIManager.GetFrameArray)

        # --- Section: Messages ---
        if self._section_header("Messages (SendUIMessage, SendFrameUIMessage, etc.)"):
            PyImGui.text("SendUIMessage(msgid, values, skip_hooks) -> bool")
            self._run_button("SendUIMessage", UIManager.SendUIMessage, self._input_msgid, [self._input_wparam, self._input_lparam], False)
            PyImGui.text("SendUIMessageRaw(msgid, wparam, lparam, skip_hooks) -> bool")
            self._run_button("SendUIMessageRaw", UIManager.SendUIMessageRaw, self._input_msgid, self._input_wparam, self._input_lparam, False)
            PyImGui.text("SendFrameUIMessage(frame_id, msgid, wparam, lparam) -> bool")
            self._run_button("SendFrameUIMessage", UIManager.SendFrameUIMessage, self._input_frame_id, self._input_msgid, self._input_wparam, self._input_lparam)
            PyImGui.text("SendFrameUIMessageWString(frame_id, msgid, text) -> bool")
            self._run_button("SendFrameUIMessageWString", UIManager.SendFrameUIMessageWString, self._input_frame_id, self._input_msgid, self._input_str_val or "test")

        # --- Section: IO Events ---
        if self._section_header("IO Events (Register, Unregister, GetIOEvents, IsMouseOver)"):
            PyImGui.text("RegisterFrameIOEventCallback(frame_id)")
            self._run_button("RegisterFrameIOEventCallback", UIManager.RegisterFrameIOEventCallback, self._input_frame_id)
            PyImGui.text("UnregisterFrameIOEventCallback(frame_id)")
            self._run_button("UnregisterFrameIOEventCallback", UIManager.UnregisterFrameIOEventCallback, self._input_frame_id)
            PyImGui.text("GetIOEventsForFrame(frame_id) -> list")
            self._run_button("GetIOEventsForFrame", UIManager.GetIOEventsForFrame, self._input_frame_id)
            PyImGui.text("IsMouseOver(frame_id) -> bool")
            self._run_button("IsMouseOver", UIManager.IsMouseOver, self._input_frame_id)

        # --- Section: Preferences ---
        if self._section_header("Preferences (Get/Set Enum, Int, String, Bool)"):
            PyImGui.text("GetPreferenceOptions(pref) -> list")
            self._run_button("GetPreferenceOptions", UIManager.GetPreferenceOptions, self._input_pref)
            PyImGui.text("GetEnumPreference(pref) -> int")
            self._run_button("GetEnumPreference", UIManager.GetEnumPreference, self._input_pref)
            PyImGui.text("SetEnumPreference(pref, value)")
            self._run_button("SetEnumPreference", UIManager.SetEnumPreference, self._input_pref, self._input_enum_val)
            PyImGui.text("GetIntPreference(pref) -> int")
            self._run_button("GetIntPreference", UIManager.GetIntPreference, self._input_pref)
            PyImGui.text("SetIntPreference(pref, value)")
            self._run_button("SetIntPreference", UIManager.SetIntPreference, self._input_pref, self._input_int_val)
            PyImGui.text("GetStringPreference(pref) -> str")
            self._run_button("GetStringPreference", UIManager.GetStringPreference, self._input_pref)
            PyImGui.text("SetStringPreference(pref, value)")
            self._run_button("SetStringPreference", UIManager.SetStringPreference, self._input_pref, self._input_str_val)
            PyImGui.text("GetBoolPreference(pref) -> bool")
            self._run_button("GetBoolPreference", UIManager.GetBoolPreference, self._input_pref)
            PyImGui.text("SetBoolPreference(pref, value)")
            self._run_button("SetBoolPreference", UIManager.SetBoolPreference, self._input_pref, self._input_bool_val)

        # --- Section: Windows ---
        if self._section_header("Windows (GetPosition, IsVisible, SetVisible, SetPosition)"):
            # Note: matches upstream typo in UIManager.py
            PyImGui.text("GetWindoPosition(window_id) -> list")
            self._run_button("GetWindoPosition", UIManager.GetWindoPosition, self._input_window_id)
            PyImGui.text("IsWindowVisible(window_id) -> bool")
            self._run_button("IsWindowVisible", UIManager.IsWindowVisible, self._input_window_id)
            PyImGui.text("SetWindowVisible(window_id, visible)")
            self._run_button("SetWindowVisible", UIManager.SetWindowVisible, self._input_window_id, self._input_visible)
            PyImGui.text("SetWindowPosition(window_id, position)")
            self._run_button("SetWindowPosition", UIManager.SetWindowPosition, self._input_window_id, [self._input_pos_left, self._input_pos_top, self._input_pos_right, self._input_pos_bottom])

        # --- Section: Key Input ---
        if self._section_header("Key Input (Keydown, Keyup, Keypress)"):
            PyImGui.text("Keydown(key, frame_id)")
            self._run_button("Keydown", UIManager.Keydown, self._input_key, self._input_frame_id)
            PyImGui.text("Keyup(key, frame_id)")
            self._run_button("Keyup", UIManager.Keyup, self._input_key, self._input_frame_id)
            PyImGui.text("Keypress(key, frame_id)")
            self._run_button("Keypress", UIManager.Keypress, self._input_key, self._input_frame_id)

        # --- Section: Interaction ---
        if self._section_header("Interaction (FrameClick, TestMouseAction, TestMouseClickAction)"):
            PyImGui.text("FrameClick(frame_id)")
            self._run_button("FrameClick", UIManager.FrameClick, self._input_frame_id)
            PyImGui.text("TestMouseAction(frame_id, state, wparam, lparam)")
            self._run_button("TestMouseAction", UIManager.TestMouseAction, self._input_frame_id, 0, self._input_wparam, self._input_lparam)
            PyImGui.text("TestMouseClickAction(frame_id, state, wparam, lparam)")
            self._run_button("TestMouseClickAction", UIManager.TestMouseClickAction, self._input_frame_id, 0, self._input_wparam, self._input_lparam)

        # --- Section: Coords ---
        if self._section_header("Coordinates (GetFrameCoords, GetContentFrameCoords, GetFrameCoordsByHash)"):
            PyImGui.text("GetFrameCoords(frame_id) -> (l,t,r,b)")
            self._run_button("GetFrameCoords", UIManager.GetFrameCoords, self._input_frame_id)
            PyImGui.text("GetContentFrameCoords(frame_id) -> (l,t,r,b)")
            self._run_button("GetContentFrameCoords", UIManager.GetContentFrameCoords, self._input_frame_id)
            PyImGui.text("GetFrameCoordsByHash(hash) -> tuple")
            self._run_button("GetFrameCoordsByHash", UIManager.GetFrameCoordsByHash, self._input_hash)

        # --- Section: Misc ---
        if self._section_header("Miscellaneous (Root, Hierarchy, UIDrawn, FPS, Settings)"):
            PyImGui.text("GetRootFrameID() -> int")
            self._run_button("GetRootFrameID", UIManager.GetRootFrameID)
            PyImGui.text("GetFrameHierarchy() -> dict")
            self._run_button("GetFrameHierarchy", UIManager.GetFrameHierarchy)
            PyImGui.text("IsUIDrawn() -> bool")
            self._run_button("IsUIDrawn", UIManager.IsUIDrawn)
            PyImGui.text("GetFPSLimit() -> int")
            self._run_button("GetFPSLimit", UIManager.GetFPSLimit)
            PyImGui.text("SetFPSLimit(limit)")
            self._run_button("SetFPSLimit", UIManager.SetFPSLimit, self._input_fps_limit)


# ========================================================================
# LogMonitor — Tab 3: Diff-based Frame/UI Message/IO Event Logs
# ========================================================================
class LogMonitor:
    def __init__(self):
        self._frame_logs: deque = deque(maxlen=LOG_BUFFER_SIZE)
        self._ui_msg_logs: deque = deque(maxlen=LOG_BUFFER_SIZE)
        self._io_event_logs: deque = deque(maxlen=LOG_BUFFER_SIZE)
        self._last_frame_count: int = 0
        self._last_ui_msg_count: int = 0
        self._show_frame_logs: bool = True
        self._show_ui_msg_logs: bool = False
        self._show_io_events: bool = False
        self._last_refresh = 0

    def refresh(self):
        now = time.time()
        if not _config.auto_refresh_logs:
            return
        if now - self._last_refresh < 1.0:
            return
        self._last_refresh = now

        # Frame logs (diff-based)
        try:
            frame_logs = UIManager.GetFrameLogs()
            new_entries = frame_logs[self._last_frame_count:]
            for entry in new_entries:
                self._frame_logs.append(entry)
            self._last_frame_count = len(frame_logs)
        except Exception:
            pass

        # UI message logs (diff-based)
        try:
            ui_msg_logs = UIManager.GetUIMessageLogs()
            new_entries = ui_msg_logs[self._last_ui_msg_count:]
            for entry in new_entries:
                self._ui_msg_logs.append(entry)
            self._last_ui_msg_count = len(ui_msg_logs)
        except Exception:
            pass

        # IO events (collect from registered frames)
        # IO events are managed internally by UIManager; we display what's available

    def clear_frame_logs(self):
        self._frame_logs.clear()
        self._last_frame_count = 0
        UIManager.ClearFrameLogs()

    def clear_ui_msg_logs(self):
        self._ui_msg_logs.clear()
        self._last_ui_msg_count = 0
        UIManager.ClearUIMessageLogs()

    def render(self):
        self.refresh()

        _config.auto_refresh_logs = PyImGui.checkbox("Auto-Refresh Logs (1s)", _config.auto_refresh_logs)

        # Log type toggles
        self._show_frame_logs = PyImGui.checkbox("Frame Logs", self._show_frame_logs)
        PyImGui.same_line(0, -1)
        self._show_ui_msg_logs = PyImGui.checkbox("UI Message Logs", self._show_ui_msg_logs)
        PyImGui.same_line(0, -1)
        self._show_io_events = PyImGui.checkbox("IO Events", self._show_io_events)

        PyImGui.separator()

        # Frame Logs
        if self._show_frame_logs:
            PyImGui.text_colored(f"Frame Logs ({len(self._frame_logs)})", (1.0, 1.0, 0.6, 1.0))
            PyImGui.same_line(0, -1)
            if PyImGui.button("Clear##clr_fl"):
                self.clear_frame_logs()

            if PyImGui.begin_child("LogFrameLogs", size=(0, 200), border=True):
                headers = ["Timestamp", "Frame ID", "Label"]
                if PyImGui.begin_table("tbl_frame_logs", 3, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.ScrollY):
                    PyImGui.table_setup_column("Timestamp")
                    PyImGui.table_setup_column("Frame ID")
                    PyImGui.table_setup_column("Label")
                    PyImGui.table_headers_row()
                    for entry in reversed(list(self._frame_logs)[-200:]):
                        PyImGui.table_next_row()
                        for i, val in enumerate(entry[:3]):
                            PyImGui.table_set_column_index(i)
                            PyImGui.text(str(val))
                    PyImGui.end_table()
            PyImGui.end_child()

        # UI Message Logs
        if self._show_ui_msg_logs:
            PyImGui.text_colored(f"UI Message Logs ({len(self._ui_msg_logs)})", (1.0, 0.8, 0.4, 1.0))
            PyImGui.same_line(0, -1)
            if PyImGui.button("Clear##clr_uml"):
                self.clear_ui_msg_logs()

            if PyImGui.begin_child("LogUIMsgLogs", size=(0, 200), border=True):
                headers = ["Timestamp", "MsgID", "Incoming", "FrameMsg", "FrameID"]
                if PyImGui.begin_table("tbl_ui_msg_logs", 5, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.ScrollY):
                    for h in headers:
                        PyImGui.table_setup_column(h)
                    PyImGui.table_headers_row()
                    for entry in reversed(list(self._ui_msg_logs)[-200:]):
                        PyImGui.table_next_row()
                        for i in range(min(5, len(entry))):
                            PyImGui.table_set_column_index(i)
                            PyImGui.text(str(entry[i]))
                    PyImGui.end_table()
            PyImGui.end_child()

        # IO Events
        if self._show_io_events:
            PyImGui.text_colored("IO Events (registered frames)", (0.6, 1.0, 0.6, 1.0))
            PyImGui.same_line(0, -1)
            if PyImGui.button("Clear##clr_ioe"):
                self._io_event_logs.clear()
            if PyImGui.begin_child("LogIOEvents", size=(0, 200), border=True):
                from Py4GWCoreLib.UIManager import UIManager as UM
                for fid in list(UM.frame_id_callbacks):
                    events = UM.GetIOEventsForFrame(fid)
                    if events:
                        PyImGui.text_colored(f"Frame {fid} ({len(events)} events):", (0.7, 0.7, 1.0, 1.0))
                        for ev in events[-10:]:
                            PyImGui.bullet_text(f"{ev.get('event_type','?')} @ {ev.get('timestamp',0)}")
            PyImGui.end_child()


# ========================================================================
# VisualToolkit — Tab 4: Drawing, Overlay/Popup Browsers
# ========================================================================
class VisualToolkit:
    def __init__(self):
        self._draw_frame_id: int = 0
        self._fill_enabled: bool = False
        self._outline_enabled: bool = False
        self._show_overlays: bool = False
        self._show_popups: bool = False

    def render(self):
        # Drawing section
        if PyImGui.collapsing_header("Drawing Tools", PyImGui.TreeNodeFlags.DefaultOpen):
            self._draw_frame_id = PyImGui.input_int("Target Frame ID##vtk_fid", self._draw_frame_id)

            # Color picker (RGBA float → ABGR int for DrawFrame)
            draw_color = list(_config.draw_color)
            PyImGui.color_edit4("Draw Color##vtk_color", draw_color)
            _config.draw_color = tuple(draw_color)
            abgr_color = Utils.TupleToColor(_config.draw_color)

            self._fill_enabled = PyImGui.checkbox("Draw Filled##vtk_fill", self._fill_enabled)
            PyImGui.same_line(0, -1)
            self._outline_enabled = PyImGui.checkbox("Draw Outline##vtk_outline", self._outline_enabled)

            _config.draw_thickness = PyImGui.slider_float("Outline Thickness##vtk_thick", _config.draw_thickness, 0.5, 10.0)

            if self._draw_frame_id > 0:
                if PyImGui.button("Draw Now##vtk_draw"):
                    if self._fill_enabled:
                        UIManager().DrawFrame(self._draw_frame_id, abgr_color)
                    if self._outline_enabled:
                        UIManager().DrawFrameOutline(self._draw_frame_id, abgr_color, _config.draw_thickness)

        PyImGui.separator()

        # Overlay Browser
        if PyImGui.collapsing_header("Overlay Browser", PyImGui.TreeNodeFlags.NoFlag):
            if PyImGui.button("Refresh Overlay List##vtk_ovr"):
                self._show_overlays = True

            if self._show_overlays:
                overlay_ids = UIManager.GetOverlayFrameIDs()
                PyImGui.text(f"Overlay Frames: {len(overlay_ids)}")
                if PyImGui.begin_child("VTKOverlayList", size=(0, 150), border=True):
                    for oid in overlay_ids[:200]:
                        alias = UIManager.GetEntryFromJSON(json_file_name, oid) or ""
                        label = f"Overlay [{oid}]"
                        if alias:
                            label += f' "{alias}"'
                        if PyImGui.selectable(label, False):
                            pass
                        if PyImGui.is_item_hovered() and PyImGui.is_mouse_clicked(1):
                            PyImGui.open_popup(f"vtk_ovr_ctx_{oid}")
                        if PyImGui.begin_popup(f"vtk_ovr_ctx_{oid}"):
                            if PyImGui.menu_item("Inspect"):
                                self._draw_frame_id = oid
                            if PyImGui.menu_item("Draw Outline"):
                                UIManager().DrawFrameOutline(oid, Utils.RGBToColor(0, 255, 0, 200))
                            PyImGui.end_popup()
                PyImGui.end_child()

        # Popup Browser
        if PyImGui.collapsing_header("Popup Browser", PyImGui.TreeNodeFlags.NoFlag):
            if PyImGui.button("Refresh Popup List##vtk_pop"):
                self._show_popups = True

            if self._show_popups:
                popup_ids = UIManager.GetPopupFrameIDs()
                PyImGui.text(f"Popup Frames: {len(popup_ids)}")
                if PyImGui.begin_child("VTKPopupList", size=(0, 150), border=True):
                    for pid in popup_ids[:200]:
                        alias = UIManager.GetEntryFromJSON(json_file_name, pid) or ""
                        label = f"Popup [{pid}]"
                        if alias:
                            label += f' "{alias}"'
                        if PyImGui.selectable(label, False):
                            pass
                        if PyImGui.is_item_hovered() and PyImGui.is_mouse_clicked(1):
                            PyImGui.open_popup(f"vtk_pop_ctx_{pid}")
                        if PyImGui.begin_popup(f"vtk_pop_ctx_{pid}"):
                            if PyImGui.menu_item("Inspect"):
                                self._draw_frame_id = pid
                            if PyImGui.menu_item("Draw Outline"):
                                UIManager().DrawFrameOutline(pid, Utils.RGBToColor(255, 255, 0, 200))
                            PyImGui.end_popup()
                PyImGui.end_child()


# ========================================================================
# FrameInspector — Per-Frame Detail (6 Sub-Tabs, ~105 Raw Fields)
# ========================================================================
class FrameInspector:
    """Deep inspection of a single frame, modeled after Frame_Tester's InfoWindow + RawFrame_Tester."""

    def __init__(self, frame_id: int):
        self.frame_id = frame_id
        self._frame_obj = PyUIManager.UIFrame(frame_id)
        self.auto_update: bool = True
        self.draw_frame: bool = False
        self.draw_color: int = Utils.RGBToColor(0, 255, 0, 125)
        self.frame_alias: str = UIManager.GetEntryFromJSON(json_file_name, frame_id) or ""
        self.submit_value: str = self.frame_alias
        self.current_state: int = 0
        self.wparam: int = 0
        self.lparam: int = 0

    def _to_hex(self, value: int) -> str:
        return f"0x{value:X}"

    def _to_bin(self, value: int) -> str:
        return bin(value)

    def _to_char(self, value: int) -> str:
        byte_values = value.to_bytes(4, byteorder="little", signed=False)
        return "".join(chr(b) if 32 <= b <= 126 else "." for b in byte_values)

    def _is_frame_valid(self) -> bool:
        try:
            return UIManager.FrameExists(self.frame_id)
        except Exception:
            return False

    def _refresh_context(self):
        """Lazy get_context() — only called when needed."""
        try:
            self._frame_obj.get_context()
        except Exception:
            pass

    def render(self, ini_key: str, title: str):
        """Render the inspector window content."""
        if not self._is_frame_valid():
            PyImGui.text_colored(f"WARNING: Frame {self.frame_id} no longer exists or is not visible.", (1.0, 0.3, 0.3, 1.0))
            return

        # Top controls
        self.auto_update = PyImGui.checkbox(f"Auto Update##finsp_au_{self.frame_id}", self.auto_update)
        self.draw_frame = PyImGui.checkbox(f"Draw Frame##finsp_df_{self.frame_id}", self.draw_frame)

        if self.draw_frame:
            PyImGui.same_line(0, -1)
            color_tuple = Utils.ColorToTuple(self.draw_color)
            color_list = list(color_tuple)
            PyImGui.color_edit4(f"Color##finsp_dfc_{self.frame_id}", color_list)
            self.draw_color = Utils.TupleToColor(tuple(color_list))
            UIManager().DrawFrame(self.frame_id, self.draw_color)

        if self.auto_update:
            self._refresh_context()

        PyImGui.separator()

        if PyImGui.begin_child(f"finsp_child_{self.frame_id}", size=(0, 0), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
            if PyImGui.begin_tab_bar(f"finsp_tabbar_{self.frame_id}"):
                # --- Tab: Overview ---
                if PyImGui.begin_tab_item(f"Overview##finsp_ov_{self.frame_id}"):
                    self._render_overview()
                    PyImGui.end_tab_item()

                # --- Tab: Position ---
                if PyImGui.begin_tab_item(f"Position##finsp_pos_{self.frame_id}"):
                    self._render_position()
                    PyImGui.end_tab_item()

                # --- Tab: Relations ---
                if PyImGui.begin_tab_item(f"Relations##finsp_rel_{self.frame_id}"):
                    self._render_relations()
                    PyImGui.end_tab_item()

                # --- Tab: Callbacks ---
                if PyImGui.begin_tab_item(f"Callbacks##finsp_cb_{self.frame_id}"):
                    self._render_callbacks()
                    PyImGui.end_tab_item()

                # --- Tab: Raw Fields ---
                if PyImGui.begin_tab_item(f"Raw Fields##finsp_rf_{self.frame_id}"):
                    self._render_raw_fields()
                    PyImGui.end_tab_item()

                # --- Tab: Alias ---
                if PyImGui.begin_tab_item(f"Alias##finsp_al_{self.frame_id}"):
                    self._render_alias()
                    PyImGui.end_tab_item()

                PyImGui.end_tab_bar()
        PyImGui.end_child()

    def _render_overview(self):
        f = self._frame_obj
        PyImGui.text(f"Frame ID: {self.frame_id}")
        PyImGui.text(f"Frame Hash: {f.frame_hash}")
        PyImGui.text(f"Parent ID: {f.parent_id}")
        PyImGui.text(f"Visibility Flags: {f.visibility_flags}")
        PyImGui.text(f"Is Visible: {f.is_visible}")
        PyImGui.text(f"Is Created: {f.is_created}")
        PyImGui.text(f"Type: {f.type}")
        PyImGui.text(f"Template Type: {f.template_type}")
        PyImGui.text(f"Frame Layout: {f.frame_layout}")
        PyImGui.text(f"Child Offset ID: {f.child_offset_id}")
        PyImGui.text(f"Alias: {self.frame_alias or '(none)'}")
        PyImGui.separator()
        PyImGui.text("Actions:")
        if PyImGui.button(f"Click Frame##finsp_clk_{self.frame_id}"):
            UIManager.FrameClick(self.frame_id)
        PyImGui.same_line(0, -1)
        if PyImGui.button(f"Draw Outline##finsp_do_{self.frame_id}"):
            UIManager().DrawFrameOutline(self.frame_id, Utils.RGBToColor(0, 255, 0, 200))

    def _render_position(self):
        p = self._frame_obj.position
        fields = [
            ("Top", p.top), ("Left", p.left), ("Bottom", p.bottom), ("Right", p.right),
            ("Content Top", p.content_top), ("Content Left", p.content_left),
            ("Content Bottom", p.content_bottom), ("Content Right", p.content_right),
            ("Unknown", p.unknown), ("Scale Factor", p.scale_factor),
            ("Viewport Width", p.viewport_width), ("Viewport Height", p.viewport_height),
            ("Screen Top", p.screen_top), ("Screen Left", p.screen_left),
            ("Screen Bottom", p.screen_bottom), ("Screen Right", p.screen_right),
            ("Top on Screen", p.top_on_screen), ("Left on Screen", p.left_on_screen),
            ("Bottom on Screen", p.bottom_on_screen), ("Right on Screen", p.right_on_screen),
            ("Width on Screen", p.width_on_screen), ("Height on Screen", p.height_on_screen),
            ("Viewport Scale X", p.viewport_scale_x), ("Viewport Scale Y", p.viewport_scale_y),
        ]
        headers = ["Field", "Value"]
        data = [(name, str(val)) for name, val in fields]
        ImGui.table(f"finsp_pos_tbl_{self.frame_id}", headers, data)

    def _render_relations(self):
        r = self._frame_obj.relation
        PyImGui.text(f"Parent ID: {r.parent_id}")
        PyImGui.text(f"Field67_0x124: {r.field67_0x124}")
        PyImGui.text(f"Field68_0x128: {r.field68_0x128}")
        PyImGui.text(f"Frame Hash ID: {r.frame_hash_id}")
        if PyImGui.collapsing_header("Siblings"):
            for i, sibling in enumerate(r.siblings):
                PyImGui.text(f"Siblings[{i}]: {sibling}")

    def _render_callbacks(self):
        for i, callback in enumerate(self._frame_obj.frame_callbacks):
            addr = callback.get_address()
            PyImGui.text(f"{i}: {addr} - {self._to_hex(addr)}")

    def _render_alias(self):
        self.submit_value = PyImGui.input_text(f"Alias##finsp_ae_{self.frame_id}", self.submit_value)
        PyImGui.same_line(0, -1)
        if PyImGui.button(f"Save Alias##finsp_sa_{self.frame_id}"):
            UIManager.SaveEntryToJSON(json_file_name, self.frame_id, self.submit_value)
            self.frame_alias = UIManager.GetEntryFromJSON(json_file_name, self.frame_id) or ""

        PyImGui.separator()
        PyImGui.text(f"Current Alias: {self.frame_alias or '(none)'}")
        PyImGui.text(f"Resolved Path: {UIManager.ConstructFramePath(self.frame_id)}")

    def _raw_field_row(self, name: str, value: int):
        return (name, str(value), self._to_hex(value), self._to_bin(value), self._to_char(value))

    def _render_raw_fields(self):
        # Performance note: this table renders ~80+ raw fields every frame when auto-update is enabled.
        # Consider throttling if frame times degrade.
        f = self._frame_obj
        headers = ["Field", "Dec", "Hex", "Bin", "Char"]
        data = [
            self._raw_field_row("Field1_0x0", f.field1_0x0),
            self._raw_field_row("Field2_0x4", f.field2_0x4),
            self._raw_field_row("Field3_0xC", f.field3_0xc),
            self._raw_field_row("Field4_0x10", f.field4_0x10),
            self._raw_field_row("Field5_0x14", f.field5_0x14),
            self._raw_field_row("Field7_0x1C", f.field7_0x1c),
            self._raw_field_row("Field10_0x28", f.field10_0x28),
            self._raw_field_row("Field11_0x2C", f.field11_0x2c),
            self._raw_field_row("Field12_0x30", f.field12_0x30),
            self._raw_field_row("Field13_0x34", f.field13_0x34),
            self._raw_field_row("Field14_0x38", f.field14_0x38),
            self._raw_field_row("Field15_0x3C", f.field15_0x3c),
            self._raw_field_row("Field16_0x40", f.field16_0x40),
            self._raw_field_row("Field17_0x44", f.field17_0x44),
            self._raw_field_row("Field18_0x48", f.field18_0x48),
            self._raw_field_row("Field19_0x4C", f.field19_0x4c),
            self._raw_field_row("Field20_0x50", f.field20_0x50),
            self._raw_field_row("Field21_0x54", f.field21_0x54),
            self._raw_field_row("Field22_0x58", f.field22_0x58),
            self._raw_field_row("Field23_0x5C", f.field23_0x5c),
            self._raw_field_row("Field24_0x60", f.field24_0x60),
            self._raw_field_row("Field24a_0x64", f.field24a_0x64),
            self._raw_field_row("Field24b_0x68", f.field24b_0x68),
            self._raw_field_row("Field25_0x6C", f.field25_0x6c),
            self._raw_field_row("Field26_0x70", f.field26_0x70),
            self._raw_field_row("Field27_0x74", f.field27_0x74),
            self._raw_field_row("Field28_0x78", f.field28_0x78),
            self._raw_field_row("Field29_0x7C", f.field29_0x7c),
            self._raw_field_row("Field30_0x80", f.field30_0x80),
        ]

        # Field31 parameter list
        try:
            param_list = f.field31_0x84
            for i, param in enumerate(param_list):
                data.append(self._raw_field_row(f"Field31_0x84[{i}]", param))
        except Exception:
            pass

        data.extend([
            self._raw_field_row("Field32_0x94", f.field32_0x94),
            self._raw_field_row("Field33_0x98", f.field33_0x98),
            self._raw_field_row("Field34_0x9C", f.field34_0x9c),
            self._raw_field_row("Field35_0xA0", f.field35_0xa0),
            self._raw_field_row("Field36_0xA4", f.field36_0xa4),
            self._raw_field_row("Field40_0xC0", f.field40_0xc0),
            self._raw_field_row("Field41_0xC4", f.field41_0xc4),
            self._raw_field_row("Field42_0xC8", f.field42_0xc8),
            self._raw_field_row("Field43_0xCC", f.field43_0xcc),
            self._raw_field_row("Field44_0xD0", f.field44_0xd0),
            self._raw_field_row("Field45_0xD4", f.field45_0xd4),
            self._raw_field_row("Field63_0x11C", f.field63_0x11c),
            self._raw_field_row("Field64_0x120", f.field64_0x120),
            self._raw_field_row("Field65_0x124", f.field65_0x124),
            self._raw_field_row("Field73_0x144", f.field73_0x144),
            self._raw_field_row("Field74_0x148", f.field74_0x148),
            self._raw_field_row("Field75_0x14C", f.field75_0x14c),
            self._raw_field_row("Field76_0x150", f.field76_0x150),
            self._raw_field_row("Field77_0x154", f.field77_0x154),
            self._raw_field_row("Field78_0x158", f.field78_0x158),
            self._raw_field_row("Field79_0x15C", f.field79_0x15c),
            self._raw_field_row("Field80_0x160", f.field80_0x160),
            self._raw_field_row("Field81_0x164", f.field81_0x164),
            self._raw_field_row("Field82_0x168", f.field82_0x168),
            self._raw_field_row("Field83_0x16C", f.field83_0x16c),
            self._raw_field_row("Field84_0x170", f.field84_0x170),
            self._raw_field_row("Field85_0x174", f.field85_0x174),
            self._raw_field_row("Field86_0x178", f.field86_0x178),
            self._raw_field_row("Field87_0x17C", f.field87_0x17c),
            self._raw_field_row("Field88_0x180", f.field88_0x180),
            self._raw_field_row("Field89_0x184", f.field89_0x184),
            self._raw_field_row("Field90_0x188", f.field90_0x188),
            self._raw_field_row("Field92_0x190", f.field92_0x190),
            self._raw_field_row("Field93_0x194", f.field93_0x194),
            self._raw_field_row("Field94_0x198", f.field94_0x198),
            self._raw_field_row("Field95_0x19C", f.field95_0x19c),
            self._raw_field_row("Field96_0x1A0", f.field96_0x1a0),
            self._raw_field_row("Field97_0x1A4", f.field97_0x1a4),
            self._raw_field_row("Field98_0x1A8", f.field98_0x1a8),
            self._raw_field_row("Field100_0x1B0", f.field100_0x1b0),
            self._raw_field_row("Field101_0x1B4", f.field101_0x1b4),
            self._raw_field_row("Field102_0x1B8", f.field102_0x1b8),
            self._raw_field_row("Field103_0x1BC", f.field103_0x1bc),
            self._raw_field_row("Field104_0x1C0", f.field104_0x1c0),
            self._raw_field_row("Field105_0x1C4", f.field105_0x1c4),
        ])

        ImGui.table(f"finsp_rf_tbl_{self.frame_id}", headers, data)


# ========================================================================
# InspectorManager — Dynamic Inspector Windows via ImGui.BeginWithClose
# ========================================================================
class InspectorManager:
    """Manages N dynamic inspector windows, one per frame_id."""

    def __init__(self):
        self._inspectors: Dict[int, FrameInspector] = {}
        self._open_fids: Set[int] = set()
        # Track INI keys per frame_id (one global INI per inspector)
        self._ini_keys: Dict[int, str] = {}

    def open_inspector(self, frame_id: int):
        if frame_id <= 0:
            return
        if frame_id not in self._inspectors:
            self._inspectors[frame_id] = FrameInspector(frame_id)
        self._open_fids.add(frame_id)
        # Ensure INI for this inspector
        if frame_id not in self._ini_keys:
            ini_key = IniManager().ensure_global_key("Coding/Debug/Guild Wars", f"inspector_{frame_id}.ini")
            if ini_key:
                IniManager().add_bool(ini_key, "open", "Window", "open", default=True)
                IniManager().load_once(ini_key)
                self._ini_keys[frame_id] = ini_key

    def close_inspector(self, frame_id: int):
        self._open_fids.discard(frame_id)
        self._inspectors.pop(frame_id, None)

    def is_open(self, frame_id: int) -> bool:
        return frame_id in self._open_fids

    def render_all(self):
        """Render all open inspector windows (called OUTSIDE main window Begin/End)."""
        closed = []
        for fid in list(self._open_fids):
            ini_key = self._ini_keys.get(fid, "")
            if not ini_key:
                closed.append(fid)
                continue

            alias = UIManager.GetEntryFromJSON(json_file_name, fid) or ""
            title = f"Frame Inspector [{fid}]"
            if alias:
                title += f' "{alias}"'
            title += f"###finsp_win_{fid}"

            initial_open = IniManager().getBool(ini_key, "open", True, section="Window")
            expanded, open_ = ImGui.BeginWithClose(ini_key, title, p_open=initial_open)

            if expanded and open_:
                if fid in self._inspectors:
                    self._inspectors[fid].render(ini_key, title)

            ImGui.End(ini_key)

            if not open_:
                IniManager().set(ini_key, "open", False, section="Window")
                IniManager().save_vars(ini_key)
                closed.append(fid)

        for fid in closed:
            self.close_inspector(fid)


# ========================================================================
# FrameShowcase — Main Controller (Singleton)
# ========================================================================
class FrameShowcase:
    """Main controller: owns all subsystems, manages PyCallback, renders main window."""

    def __init__(self):
        self.tree = FrameTree()
        self.explorer = FrameTreeExplorer(self.tree)
        self.api_tester = UIManagerAPITester()
        self.log_monitor = LogMonitor()
        self.visual_toolkit = VisualToolkit()
        self.inspector_mgr = InspectorManager()
        self._active_tab: int = 0
        self._last_tree_update = 0
        self._callbacks_registered = False
        self._ini_ready = False

    def _ensure_ini(self) -> bool:
        """Retry INI init on each render() call until account is ready."""
        if self._ini_ready:
            return True
        try:
            _window_factory.ensure_ini()
            self._ini_ready = True
            return True
        except Exception:
            return False

    def register_callbacks(self):
        """Register PyCallback for throttled tree update and log refresh."""
        if self._callbacks_registered:
            return

        def _on_data(*args, **kwargs):
            if _config.keep_data_updated:
                self.tree.update()
            self.log_monitor.refresh()

        try:
            PyCallback.PyCallback.Register(
                "FrameShowcase.Data",
                PyCallback.Phase.Data,
                _on_data,
                priority=50,
                context=PyCallback.Context.Update,
            )
            self._callbacks_registered = True
        except Exception:
            pass

    def unregister_callbacks(self):
        if self._callbacks_registered:
            try:
                PyCallback.PyCallback.RemoveByName("FrameShowcase.Data")
            except Exception:
                pass
            self._callbacks_registered = False

    def render(self):
        if not self._ensure_ini():
            return

        # Process inspector open requests from tree context menus
        requests = self.tree.drain_inspector_requests()
        for fid in requests:
            self.inspector_mgr.open_inspector(fid)

        # Main window
        expanded, open_ = _window_factory.begin("main")

        if expanded:
            if PyImGui.begin_tab_bar("FSMainTabBar"):
                if PyImGui.begin_tab_item("Frame Tree"):
                    self.explorer.render()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("UIManager API"):
                    self.api_tester.render()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Log Monitor"):
                    self.log_monitor.render()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Visual Tools"):
                    self.visual_toolkit.render()
                    PyImGui.end_tab_item()

                PyImGui.end_tab_bar()

        ImGui.End(_window_factory.key("main"))

        # Clean up callbacks when main window is closed
        if not open_:
            self.unregister_callbacks()

        # Render inspector windows OUTSIDE main window scope
        self.inspector_mgr.render_all()


# ========================================================================
# Global Instance
# ========================================================================
_showcase: Optional[FrameShowcase] = None


def _get_showcase() -> FrameShowcase:
    global _showcase
    if _showcase is None:
        _showcase = FrameShowcase()
        _showcase.register_callbacks()
    return _showcase


# ========================================================================
# Widget Integration
# ========================================================================
def main():
    sc = _get_showcase()
    sc.render()


def tooltip():
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Frame Showcase", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text("Comprehensive UIManager Feature Explorer & Tester.")
    PyImGui.spacing()
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Frame Tree: Hierarchical visualization with search, tooltips, context menus")
    PyImGui.bullet_text("UIManager API: Exercise ~110 methods across 12 collapsible sections")
    PyImGui.bullet_text("Log Monitor: Diff-based frame/UI message/IO event logs")
    PyImGui.bullet_text("Visual Tools: Frame drawing, overlay/popup browsers")
    PyImGui.bullet_text("Frame Inspector: Per-frame detail with 105 raw fields, 6 sub-tabs")
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    PyImGui.end_tooltip()


def configure():
    """Widget configuration stub — all configuration is inline via INI-backed checkboxes and color pickers."""
    pass


if __name__ == "__main__":
    main()
