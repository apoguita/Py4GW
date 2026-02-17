from Py4GWCoreLib import *
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5 as Icons
from Py4GWCoreLib.enums import Key
import PyImGui

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
import math
import re


MODULE_NAME = "Route Builder"

__widget__ = {
    "name": "Route Builder",
    "enabled": True,
    "category": "Coding",
    "subcategory": "Tools",
    "icon": "ICON_ROUTE",
    "quickdock": False,
    "hidden": False,
}

# region Data Model

@dataclass
class Waypoint:
    x: float
    y: float
    on_mesh: bool = True
    z_ambiguous: bool = False


class InteractionState(Enum):
    IDLE = auto()
    PENDING_DOWN = auto()
    DRAGGING_PAN = auto()
    DRAGGING_WP = auto()


@dataclass
class MapBounds:
    x_min: float
    x_max: float
    y_min: float
    y_max: float

# endregion

# region Widget Class

class RouteBuilderWidget:
    DRAG_THRESHOLD = 5.0
    WAYPOINT_HIT_RADIUS = 8.0
    LINE_HIT_THRESHOLD = 10.0
    TRAP_Y_PAD = 2.5  # game-unit vertical expansion to fill inter-trapezoid gaps
    CULL_AREA_THRESHOLD = 6.0  # skip quads below this screen-space area (px²)
    PANEL_WIDTH = 220.0
    BOTTOM_PANEL_H = 65
    HELP_TEXT_H = 40
    BTN_W = 30.0
    BTN_H = 26.0
    BTN_INDENT = 20.0
    UNDO_MAX = 50

    # Colors
    COLOR_WP_DEFAULT = Color(110, 160, 220, 255)
    COLOR_WP_HOVERED = Color(140, 190, 240, 255)
    COLOR_WP_SELECTED = Color(90, 140, 220, 255)
    COLOR_WP_AMBIGUOUS = Color(220, 170, 80, 255)
    COLOR_WP_OFF_MESH = Color(200, 70, 70, 255)
    COLOR_RING_ENDPOINT = Color(200, 210, 240, 200)
    COLOR_RING_INTERIOR = Color(140, 160, 210, 140)
    COLOR_RING_START = Color(80, 200, 130, 200)
    COLOR_RING_END = Color(200, 100, 100, 200)
    COLOR_PLAYER = Color(80, 210, 120, 255)
    COLOR_LABEL = Color(255, 255, 255, 255)
    COLOR_CONNECTOR = Color(120, 150, 220, 160)
    COLOR_NAVMESH_PRIMARY = Color(130, 130, 130, 255)
    COLOR_NAVMESH_SECONDARY = Color(120, 60, 140, 255)

    def __init__(self):
        # Canvas state
        self.zoom_factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.canvas_w = 600
        self.canvas_h = 600

        # Map state
        min_x, min_y, max_x, max_y = Map.GetMapBoundaries()
        self.map_bounds = MapBounds(min_x, max_x, min_y, max_y)
        self.map_id = Map.GetMapID()         # currently viewed map (dropdown)
        self._game_map_id = self.map_id      # last known in-game map
        self.map_name = Map.GetMapName(self.map_id)
        self.pathing_map = []
        self.quad_cache = {}

        # Map selector state
        self._build_map_selector()
        self.selected_map_index = self._find_selector_index(self.map_id)

        # Waypoint state
        self.waypoints: list[Waypoint] = []

        # Selection: contiguous range [sel_start, sel_end] inclusive
        # sel_anchor is the click origin for shift-extend
        self.sel_start: int = -1
        self.sel_end: int = -1
        self.sel_anchor: int = -1

        # Interaction state
        self.interaction = InteractionState.IDLE
        self.mouse_down_pos = (0.0, 0.0)
        self.drag_target_index = -1
        self.hovered_wp_index = -1

        # Player position (cached in update())
        self.player_pos: tuple[float, float] | None = None

        # Manual coordinate input
        self._input_x = "0"
        self._input_y = "0"

        # Navmesh validation
        self.navmesh = None
        self._navmesh_loading = False
        self._load_navmesh_object()

        # Auto-path
        self.auto_path_computing = False

        # Undo
        self._undo_stack: deque[tuple] = deque(maxlen=self.UNDO_MAX)

        # Scroll-to flag: set when canvas selection changes
        self._scroll_to_sel = False

        # Cached text/style metrics (font and style don't change at runtime)
        self._char_w, self._char_h = PyImGui.calc_text_size("0")
        _style = PyImGui.StyleConfig()
        _style.Pull()
        _frame_pad_x = _style.FramePadding[0]
        _item_spacing_x = _style.ItemSpacing[0]
        self._lbl_x_w = PyImGui.calc_text_size("X")[0] + _item_spacing_x
        _import_label = f"{Icons.ICON_PASTE} Import from Clipboard##import"
        _export_label = f"{Icons.ICON_COPY} Export to Clipboard##export"
        self._import_btn_w = PyImGui.calc_text_size(_import_label)[0] + _frame_pad_x * 2
        self._export_btn_w = PyImGui.calc_text_size(_export_label)[0] + _frame_pad_x * 2

    # region Selection

    def _is_selected(self, i: int) -> bool:
        return self.sel_start >= 0 and self.sel_start <= i <= self.sel_end

    def _has_selection(self) -> bool:
        return self.sel_start >= 0

    def _sel_count(self) -> int:
        return (self.sel_end - self.sel_start + 1) if self.sel_start >= 0 else 0

    def _select_one(self, i: int) -> None:
        self.sel_anchor = i
        self.sel_start = i
        self.sel_end = i
        self._scroll_to_sel = True

    def _extend_selection(self, i: int) -> None:
        if self.sel_anchor < 0:
            self._select_one(i)
        else:
            self.sel_start = min(self.sel_anchor, i)
            self.sel_end = max(self.sel_anchor, i)
            self._scroll_to_sel = True

    def _clear_selection(self) -> None:
        self.sel_start = -1
        self.sel_end = -1
        self.sel_anchor = -1

    def _clamp_selection(self) -> None:
        """Clamp selection to valid range after waypoints change."""
        n = len(self.waypoints)
        if n == 0:
            self._clear_selection()
            return
        if self.sel_start >= 0:
            self.sel_start = max(0, min(self.sel_start, n - 1))
            self.sel_end = max(0, min(self.sel_end, n - 1))
            self.sel_anchor = max(0, min(self.sel_anchor, n - 1))
            if self.sel_start > self.sel_end:
                self._clear_selection()

    # endregion

    # region Undo

    def _snapshot(self) -> None:
        """Push current waypoint + selection state onto undo stack."""
        state = (
            [Waypoint(wp.x, wp.y, wp.on_mesh, wp.z_ambiguous) for wp in self.waypoints],
            self.sel_start, self.sel_end, self.sel_anchor,
        )
        self._undo_stack.append(state)

    def _undo(self) -> None:
        """Restore previous state from undo stack."""
        if not self._undo_stack:
            return
        wps, s, e, a = self._undo_stack.pop()
        self.waypoints = wps
        self.sel_start, self.sel_end, self.sel_anchor = s, e, a

    # endregion

    # region Nav Loading

    def _build_map_selector(self) -> None:
        """Build the map selector dropdown, filtered to maps with available pathing data."""
        available = Map.Pathing.GetAvailableMapIds()
        entries = []
        for mid, name in outposts.items():
            if mid in available:
                entries.append((name, mid))
        for mid, name in explorables.items():
            if mid not in outposts and mid in available:
                entries.append((name, mid))
        entries.sort(key=lambda e: e[0].lower())
        self._selector_ids = [mid for _, mid in entries]
        self._selector_labels = [f"{name} ({mid})" for name, mid in entries]

    def _find_selector_index(self, map_id: int) -> int:
        """Find the selector index for a map_id, or 0 if not found."""
        if map_id in self._selector_ids:
            return self._selector_ids.index(map_id)
        return 0

    def _apply_pathing(self, layers) -> None:
        """Apply loaded pathing data, computing map bounds from trapezoids."""
        x_min = float('inf')
        x_max = float('-inf')
        y_min = float('inf')
        y_max = float('-inf')
        for layer in layers:
            for t in layer.trapezoids:
                x_min = min(x_min, t.XTL, t.XBL)
                x_max = max(x_max, t.XTR, t.XBR)
                y_min = min(y_min, t.YB)
                y_max = max(y_max, t.YT)
        self.map_bounds = MapBounds(x_min, x_max, y_min, y_max)
        self.pathing_map = layers
        self.quad_cache = {}

    def _load_navmesh_object(self) -> None:
        """Try to get the NavMesh for validation. If not cached yet, schedule async load."""
        try:
            nav = AutoPathing().get_navmesh()
            if nav is not None:
                self.navmesh = nav
                self._validate_all_waypoints()
                return
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Navmesh load failed: {e}", Py4GW.Console.MessageType.Warning)
        self._navmesh_loading = True
        def _load_coro():
            yield from AutoPathing().load_pathing_maps()
            nav = AutoPathing().get_navmesh()
            if nav is not None:
                self.navmesh = nav
                self._validate_all_waypoints()
            self._navmesh_loading = False
        GLOBAL_CACHE.Coroutines.append(_load_coro())

    # endregion

    # region Validation

    def _point_in_trapezoid(self, px: float, py: float, trap) -> bool:
        """Test if point (px, py) falls inside a trapezoid."""
        if py < trap.YB or py > trap.YT:
            return False
        span = trap.YT - trap.YB
        if span == 0:
            t = 0.5
        else:
            t = (py - trap.YB) / span
        xl = trap.XBL + t * (trap.XTL - trap.XBL)
        xr = trap.XBR + t * (trap.XTR - trap.XBR)
        return xl <= px <= xr

    def _point_on_mesh(self, px: float, py: float) -> bool:
        """Test if point is on any trapezoid in pathing_map."""
        for layer in self.pathing_map:
            for trap in layer.trapezoids:
                if self._point_in_trapezoid(px, py, trap):
                    return True
        return False

    def _planes_at_point(self, px: float, py: float) -> set[int]:
        """Return the set of layer indices that contain (px, py)."""
        planes = set()
        for i, layer in enumerate(self.pathing_map):
            for trap in layer.trapezoids:
                if self._point_in_trapezoid(px, py, trap):
                    planes.add(i)
                    break
        return planes

    def _validate_waypoint(self, wp: Waypoint) -> None:
        # Validate against the displayed pathing mesh (dat or live).
        if self.pathing_map:
            planes = self._planes_at_point(wp.x, wp.y)
            wp.on_mesh = len(planes) > 0
            wp.z_ambiguous = len(planes) > 1
        else:
            wp.on_mesh = True
            wp.z_ambiguous = False

    def _validate_all_waypoints(self) -> None:
        for wp in self.waypoints:
            self._validate_waypoint(wp)

    # endregion

    # region Coordinates
    # Game coords and canvas-world coords are identity-mapped.
    # _scale_coords flips Y so that high game Y (north) maps to low screen Y (top).

    def _fit_params(self, w: float, h: float) -> tuple[float, float, float, float]:
        """Shared aspect-fit + zoom parameters."""
        world_w = self.map_bounds.x_max - self.map_bounds.x_min
        world_h = self.map_bounds.y_max - self.map_bounds.y_min
        if world_w == 0 or world_h == 0:
            return 0, 0, 0, 1.0
        aspect_world = world_w / world_h
        aspect_window = w / h if h != 0 else aspect_world
        if aspect_world > aspect_window:
            fit_scale = w / world_w
            offset_x = 0
            offset_y = (h - world_h * fit_scale) / 2
        else:
            fit_scale = h / world_h
            offset_x = (w - world_w * fit_scale) / 2
            offset_y = 0
        return offset_x, offset_y, fit_scale * self.zoom_factor, fit_scale

    def _scale_coords(self, x: float, y: float, w: float, h: float) -> tuple[float, float]:
        """Scale game coords to screen coords with pan+zoom.
        Y is flipped: game Y increases northward, screen Y increases downward."""
        offset_x, offset_y, scale, _ = self._fit_params(w, h)
        if scale == 0:
            return 0.0, 0.0
        sx = (x - self.map_bounds.x_min) * scale + offset_x
        sy = (self.map_bounds.y_max - y) * scale + offset_y  # flip Y
        return sx + self.pan_x, sy + self.pan_y

    def _screen_to_world(self, sx: float, sy: float, w: float, h: float) -> tuple[float, float]:
        """Convert screen coords to game coords (inverse of _scale_coords)."""
        offset_x, offset_y, scale, _ = self._fit_params(w, h)
        if scale == 0:
            return 0.0, 0.0
        sx -= self.pan_x
        sy -= self.pan_y
        wx = (sx - offset_x) / scale + self.map_bounds.x_min
        wy = self.map_bounds.y_max - (sy - offset_y) / scale  # flip Y
        return wx, wy

    # endregion

    # region Trapezoids
    # Quads are cached WITHOUT pan so the cache survives panning (the most
    # frequent state change).  Pan + window_pos are applied at draw time.

    def _build_layer_quads(self, layer, w: float, h: float) -> list[tuple]:
        """Build pan-free screen quads for a layer.  Each entry includes
        the 8 coord floats plus a screen-space bounding-box area for culling."""
        offset_x, offset_y, scale, _ = self._fit_params(w, h)
        if scale == 0:
            return []
        pad = max(self.TRAP_Y_PAD, 1.0 / scale)
        xmin = self.map_bounds.x_min
        ymax = self.map_bounds.y_max
        quads = []
        for t in layer.trapezoids:
            yt = t.YT + pad
            yb = t.YB - pad
            tl_x = (t.XTL - xmin) * scale + offset_x
            tl_y = (ymax - yt) * scale + offset_y
            tr_x = (t.XTR - xmin) * scale + offset_x
            br_x = (t.XBR - xmin) * scale + offset_x
            br_y = (ymax - yb) * scale + offset_y
            bl_x = (t.XBL - xmin) * scale + offset_x
            # Screen-space bounding-box area for sub-pixel culling
            qw = max(tl_x, tr_x, br_x, bl_x) - min(tl_x, tr_x, br_x, bl_x)
            qh = br_y - tl_y
            area = qw * qh
            quads.append((tl_x, tl_y, tr_x, tl_y, br_x, br_y, bl_x, br_y, area))
        return quads

    def _get_layer_quads(self, index: int, layer, w: float, h: float) -> list[tuple]:
        cur_zoom = round(self.zoom_factor, 3)
        cache_key = (index, w, h, cur_zoom)

        if cache_key not in self.quad_cache:
            # Zoom or resize changed — clear stale entries
            self.quad_cache = {k: v for k, v in self.quad_cache.items() if k[3] == cur_zoom and k[1] == w and k[2] == h}
            self.quad_cache[cache_key] = self._build_layer_quads(layer, w, h)

        return self.quad_cache[cache_key]

    def _draw_trapezoids(self, index: int, layer, clip_rect: tuple, color: Color) -> None:
        x1, y1, x2, y2 = clip_rect
        quads = self._get_layer_quads(index, layer, self.canvas_w, self.canvas_h)
        ox = x1 + self.pan_x
        oy = y1 + self.pan_y
        col = color.to_color()
        thresh = self.CULL_AREA_THRESHOLD
        for tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y, area in quads:
            if area < thresh:
                continue
            r = tl_x + ox; l = bl_x + ox; t = tl_y + oy; b = br_y + oy
            if r < x1 and (tr_x + ox) < x1:
                continue
            if l > x2 and (br_x + ox) > x2:
                continue
            if b < y1 or t > y2:
                continue
            PyImGui.draw_list_add_quad_filled(
                tl_x + ox, tl_y + oy, tr_x + ox, tr_y + oy,
                br_x + ox, br_y + oy, bl_x + ox, bl_y + oy, col
            )

    # endregion

    # region Hit Testing

    def _wp_screen_pos(self, wp: Waypoint, child_pos: tuple) -> tuple[float, float]:
        sx, sy = self._scale_coords(wp.x, wp.y, self.canvas_w, self.canvas_h)
        return sx + child_pos[0], sy + child_pos[1]

    def _hit_test_waypoint(self, child_pos: tuple, mx: float, my: float) -> int:
        radius = max(self.WAYPOINT_HIT_RADIUS, min(16.0, 6 * self.zoom_factor))
        best_dist = radius
        best_idx = -1
        for i, wp in enumerate(self.waypoints):
            sx, sy = self._wp_screen_pos(wp, child_pos)
            dist = math.hypot(mx - sx, my - sy)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        return best_idx

    def _point_to_segment_dist(self, px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-6:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
        proj_x = ax + t * dx
        proj_y = ay + t * dy
        return math.hypot(px - proj_x, py - proj_y)

    def _hit_test_line(self, child_pos: tuple, mx: float, my: float) -> int:
        threshold = self.LINE_HIT_THRESHOLD
        for i in range(len(self.waypoints) - 1):
            ax, ay = self._wp_screen_pos(self.waypoints[i], child_pos)
            bx, by = self._wp_screen_pos(self.waypoints[i + 1], child_pos)
            dist = self._point_to_segment_dist(mx, my, ax, ay, bx, by)
            if dist < threshold:
                return i
        return -1

    # endregion

    # region Auto-Path

    def _auto_path_between(self, take_snapshot: bool = True) -> None:
        if self._sel_count() < 2:
            return

        wp_a = self.waypoints[self.sel_start]
        wp_b = self.waypoints[self.sel_end]
        start = (wp_a.x, wp_a.y, 0)
        goal = (wp_b.x, wp_b.y, 0)
        self.auto_path_computing = True

        s_start = self.sel_start
        s_end = self.sel_end
        do_snapshot = take_snapshot

        def _coro():
            path_points = yield from AutoPathing().get_path(start, goal)
            if path_points:
                if do_snapshot:
                    self._snapshot()
                new_wps = [Waypoint(px, py) for (px, py, _) in path_points]
                # Replace everything between first and last selected (exclusive of endpoints)
                self.waypoints[s_start + 1:s_end] = new_wps
                self._validate_all_waypoints()
                new_end = s_start + len(new_wps)
                self.sel_start = s_start
                self.sel_end = new_end
                self.sel_anchor = s_start
            self.auto_path_computing = False

        GLOBAL_CACHE.Coroutines.append(_coro())

    # endregion

    # region Group Ops

    def _move_selection_up(self) -> None:
        if not self._has_selection() or self.sel_start <= 0:
            return
        self._snapshot()
        # Take the item above the block and insert it after the block
        item = self.waypoints.pop(self.sel_start - 1)
        self.waypoints.insert(self.sel_end, item)
        self.sel_start -= 1
        self.sel_end -= 1
        self.sel_anchor = max(0, self.sel_anchor - 1)

    def _move_selection_down(self) -> None:
        if not self._has_selection() or self.sel_end >= len(self.waypoints) - 1:
            return
        self._snapshot()
        # Take the item below the block and insert it before the block
        item = self.waypoints.pop(self.sel_end + 1)
        self.waypoints.insert(self.sel_start, item)
        self.sel_start += 1
        self.sel_end += 1
        self.sel_anchor = min(len(self.waypoints) - 1, self.sel_anchor + 1)

    def _delete_selection(self) -> None:
        if not self._has_selection():
            return
        self._snapshot()
        del self.waypoints[self.sel_start:self.sel_end + 1]
        self._clear_selection()

    def _import_from_clipboard(self) -> None:
        """Parse coordinate tuples from clipboard text, e.g. [(x,y), (x,y), ...]."""
        text = PyImGui.get_clipboard_text()
        if not text:
            return
        # Strip comments so commented-out tuples like '# (x,y)' are skipped
        text = re.sub(r'#[^\n]*', '', text)
        pairs = re.findall(r'\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)', text)
        if not pairs:
            return
        self._snapshot()
        self.waypoints.clear()
        self._clear_selection()
        for xs, ys in pairs:
            wp = Waypoint(float(xs), float(ys))
            self._validate_waypoint(wp)
            self.waypoints.append(wp)

    # endregion

    # region Input

    def _process_canvas_input(self, child_pos: tuple) -> None:
        if not PyImGui.is_window_hovered():
            return

        io = PyImGui.get_io()

        # Zoom (always active)
        if io.mouse_wheel != 0.0:
            local_x = io.mouse_pos_x - child_pos[0]
            local_y = io.mouse_pos_y - child_pos[1]
            world_x, world_y = self._screen_to_world(local_x, local_y, self.canvas_w, self.canvas_h)

            zoom_step = 1.25
            if io.mouse_wheel > 0:
                self.zoom_factor *= zoom_step
            else:
                self.zoom_factor /= zoom_step
            self.zoom_factor = max(0.1, min(self.zoom_factor, 100.0))

            new_sx, new_sy = self._scale_coords(world_x, world_y, self.canvas_w, self.canvas_h)
            self.pan_x += local_x - new_sx
            self.pan_y += local_y - new_sy

        # Ctrl+Z undo
        if io.key_ctrl and PyImGui.is_key_pressed(Key.Z.value):
            self._undo()

        self._process_left_button(child_pos, io)
        self._process_right_click(child_pos, io)
        self._update_hover(child_pos, io)

    def _process_left_button(self, child_pos: tuple, io) -> None:
        mx, my = io.mouse_pos_x, io.mouse_pos_y

        if self.interaction == InteractionState.IDLE:
            if PyImGui.is_mouse_clicked(0):
                self.mouse_down_pos = (mx, my)
                self.drag_target_index = self._hit_test_waypoint(child_pos, mx, my)
                self.interaction = InteractionState.PENDING_DOWN
                PyImGui.reset_mouse_drag_delta(0)

        elif self.interaction == InteractionState.PENDING_DOWN:
            dx = mx - self.mouse_down_pos[0]
            dy = my - self.mouse_down_pos[1]
            dist = math.hypot(dx, dy)

            if dist > self.DRAG_THRESHOLD:
                if self.drag_target_index >= 0:
                    self._snapshot()
                    self.interaction = InteractionState.DRAGGING_WP
                else:
                    self.interaction = InteractionState.DRAGGING_PAN
                PyImGui.reset_mouse_drag_delta(0)
            elif not PyImGui.is_mouse_down(0):
                # Released without dragging = click
                self._handle_click(child_pos, io)
                self.interaction = InteractionState.IDLE
            else:
                # Still pending, consume drag delta
                PyImGui.reset_mouse_drag_delta(0)

        elif self.interaction == InteractionState.DRAGGING_PAN:
            if PyImGui.is_mouse_down(0):
                delta = PyImGui.get_mouse_drag_delta(0, 0.0)
                self.pan_x += delta[0]
                self.pan_y += delta[1]
                PyImGui.reset_mouse_drag_delta(0)
            else:
                self.interaction = InteractionState.IDLE

        elif self.interaction == InteractionState.DRAGGING_WP:
            if PyImGui.is_mouse_down(0):
                local_x = mx - child_pos[0]
                local_y = my - child_pos[1]
                wx, wy = self._screen_to_world(local_x, local_y, self.canvas_w, self.canvas_h)
                wp = self.waypoints[self.drag_target_index]
                wp.x = wx
                wp.y = wy
                PyImGui.reset_mouse_drag_delta(0)
            else:
                # Finalize drag - validate and select the dragged item
                self._validate_waypoint(self.waypoints[self.drag_target_index])
                self._select_one(self.drag_target_index)
                self.interaction = InteractionState.IDLE

    def _handle_click(self, child_pos: tuple, io) -> None:
        mx, my = io.mouse_pos_x, io.mouse_pos_y

        # Clicked on a waypoint: select/extend
        if self.drag_target_index >= 0:
            if io.key_shift and self.sel_anchor >= 0:
                self._extend_selection(self.drag_target_index)
            else:
                self._select_one(self.drag_target_index)
            return

        # Clicked empty space: check if near a line segment first
        local_x = mx - child_pos[0]
        local_y = my - child_pos[1]
        game_x, game_y = self._screen_to_world(local_x, local_y, self.canvas_w, self.canvas_h)

        line_idx = self._hit_test_line(child_pos, mx, my)
        if line_idx >= 0:
            self._snapshot()
            wp = Waypoint(game_x, game_y)
            self._validate_waypoint(wp)
            self.waypoints.insert(line_idx + 1, wp)
            self._select_one(line_idx + 1)
        else:
            self._snapshot()
            prev_idx = len(self.waypoints) - 1 if self.waypoints else -1
            wp = Waypoint(game_x, game_y)
            self._validate_waypoint(wp)
            self.waypoints.append(wp)
            new_idx = len(self.waypoints) - 1
            # Ctrl+click: auto-path from previous last waypoint to the new one
            if io.key_ctrl and prev_idx >= 0 and self.map_id == self._game_map_id:
                self.sel_start = prev_idx
                self.sel_end = new_idx
                self.sel_anchor = prev_idx
                self._auto_path_between(take_snapshot=False)
            else:
                self._select_one(new_idx)

    def _process_right_click(self, child_pos: tuple, io) -> None:
        if PyImGui.is_mouse_clicked(1):
            hit = self._hit_test_waypoint(child_pos, io.mouse_pos_x, io.mouse_pos_y)
            if hit >= 0:
                self._snapshot()
                self.waypoints.pop(hit)
                # Adjust selection after removing an item
                if self.sel_start >= 0:
                    if hit < self.sel_start:
                        self.sel_start -= 1
                        self.sel_end -= 1
                        self.sel_anchor -= 1
                    elif hit <= self.sel_end:
                        # Removed item was in the selection
                        self.sel_end -= 1
                        if self.sel_start > self.sel_end:
                            self._clear_selection()
                    self._clamp_selection()

    def _update_hover(self, child_pos: tuple, io) -> None:
        if self.interaction == InteractionState.IDLE:
            self.hovered_wp_index = self._hit_test_waypoint(child_pos, io.mouse_pos_x, io.mouse_pos_y)
        else:
            self.hovered_wp_index = -1

    # endregion

    # region Drawing

    def _draw_disabled_button(self, label: str, width: float = 0, height: float = 0) -> None:
        """Draw a visually disabled (dimmed) button that doesn't respond to clicks."""
        dim = (0.3, 0.3, 0.3, 0.4)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, dim)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, dim)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, dim)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.5, 0.5, 0.5, 0.6))
        PyImGui.button(label, width, height)
        PyImGui.pop_style_color(4)

    def draw(self) -> None:
        if not Map.IsMapReady():
            return
        if ImGui.Begin(INI_KEY, MODULE_NAME,
                       flags=PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
            self._draw_header()
            self._draw_main_area()
        ImGui.End(INI_KEY)

    def _switch_to_map(self, new_map_id: int) -> None:
        """Switch the viewed map, clearing waypoints and resetting view."""
        self._snapshot()
        self.map_id = new_map_id
        self.selected_map_index = self._find_selector_index(new_map_id)
        self.map_name = Map.GetMapName(new_map_id)
        self.pathing_map = []
        self.quad_cache = {}
        self.waypoints.clear()
        self._clear_selection()
        self.zoom_factor = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

    def _draw_header(self) -> None:
        full_w = PyImGui.get_content_region_avail()[0]

        # Map selector — left ~1/3 + "Current" button
        if self._selector_labels:
            PyImGui.push_item_width(full_w * 0.33)
            new_index = PyImGui.combo("##mapsel", self.selected_map_index, self._selector_labels)
            PyImGui.pop_item_width()
            if new_index != self.selected_map_index:
                self._switch_to_map(self._selector_ids[new_index])

            # "Current" button — switch to player's game map
            PyImGui.same_line(0, 4)
            already_current = self.map_id == self._game_map_id
            if already_current:
                self._draw_disabled_button(f"{Icons.ICON_CROSSHAIRS} Current##gotocur")
            else:
                if PyImGui.button(f"{Icons.ICON_CROSSHAIRS} Current##gotocur"):
                    self._switch_to_map(self._game_map_id)
            if PyImGui.is_item_hovered():
                PyImGui.begin_tooltip()
                game_name = Map.GetMapName(self._game_map_id)
                PyImGui.text(f"Switch to player's map: {game_name} ({self._game_map_id})")
                PyImGui.end_tooltip()
        else:
            PyImGui.text(f"{self.map_name} ({self.map_id})")

        # Import / Export buttons — right-justified
        import_label = f"{Icons.ICON_PASTE} Import from Clipboard##import"
        export_label = f"{Icons.ICON_COPY} Export to Clipboard##export"
        import_w = self._import_btn_w
        export_w = self._export_btn_w
        gap = 4
        PyImGui.same_line(full_w - import_w - gap - export_w, 0)
        if PyImGui.button(import_label, import_w):
            self._import_from_clipboard()
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.text("Replace waypoints from clipboard text.")
            PyImGui.text("Format: (x,y), (x,y), ...")
            PyImGui.text("Brackets optional. Comments (#) and blank lines ignored.")
            PyImGui.end_tooltip()
        PyImGui.same_line(0, gap)
        if PyImGui.button(export_label, export_w):
            if self.waypoints:
                coords = [(wp.x, wp.y) for wp in self.waypoints]
                text = "[" + ", ".join(f"({x:.0f},{y:.0f})" for x, y in coords) + "]"
                PyImGui.set_clipboard_text(text)
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.text("Copy waypoints to clipboard.")
            PyImGui.text("Format: [(x,y), (x,y), ...]")
            PyImGui.end_tooltip()

        PyImGui.separator()

    def _draw_main_area(self) -> None:
        avail_w, avail_h = PyImGui.get_content_region_avail()
        canvas_w = max(100, avail_w - self.PANEL_WIDTH - 8)
        canvas_h = avail_h - self.HELP_TEXT_H

        # Left column: canvas + help text
        if PyImGui.begin_child("LeftCol", (canvas_w, avail_h), border=False):
            # Canvas
            canvas_flags = (PyImGui.WindowFlags.NoScrollbar |
                            PyImGui.WindowFlags.NoScrollWithMouse |
                            PyImGui.WindowFlags.NoMove)
            if PyImGui.begin_child("CanvasChild", (canvas_w, canvas_h), border=True, flags=canvas_flags):
                child_pos = PyImGui.get_window_pos()
                child_min = PyImGui.get_window_content_region_min()
                child_max = PyImGui.get_window_content_region_max()

                origin = (child_pos[0] + child_min[0], child_pos[1] + child_min[1])
                self.canvas_w = int(child_max[0] - child_min[0])
                self.canvas_h = int(child_max[1] - child_min[1])

                clip_rect = (origin[0], origin[1],
                             child_pos[0] + child_max[0], child_pos[1] + child_max[1])

                self._process_canvas_input(origin)

                for idx, layer in enumerate(self.pathing_map):
                    color = self.COLOR_NAVMESH_PRIMARY if idx == 0 else self.COLOR_NAVMESH_SECONDARY
                    self._draw_trapezoids(idx, layer, clip_rect, color)

                self._draw_waypoints_on_canvas(origin)
                self._draw_player_on_canvas(origin)
                self._draw_hover_tooltip(origin)
            PyImGui.end_child()

            # Interaction help text
            self._draw_canvas_help()
        PyImGui.end_child()

        PyImGui.same_line(0, 8)

        # Right: Panel
        if PyImGui.begin_child("PanelChild", (self.PANEL_WIDTH, avail_h), border=True):
            self._draw_waypoint_panel()
        PyImGui.end_child()

    def _draw_canvas_help(self) -> None:
        dim = (0.6, 0.6, 0.6, 1.0)
        gap = 20
        PyImGui.text_colored("L-Click", dim)
        PyImGui.same_line(0, 4)
        PyImGui.text("Add waypoint")
        PyImGui.same_line(0, gap)
        PyImGui.text_colored("R-Click", dim)
        PyImGui.same_line(0, 4)
        PyImGui.text("Delete waypoint")
        PyImGui.same_line(0, gap)
        if self.map_id == self._game_map_id:
            PyImGui.text_colored("Ctrl+Click", dim)
            PyImGui.same_line(0, 4)
            PyImGui.text("Add + auto-path")
        else:
            disabled = (0.35, 0.35, 0.35, 0.5)
            red = (1.0, 0.3, 0.3, 1.0)
            PyImGui.text_colored("Ctrl+Click", disabled)
            PyImGui.same_line(0, 4)
            PyImGui.text_colored("Add + auto-path", disabled)
            PyImGui.same_line(0, 4)
            PyImGui.text_colored("(Must be in map)", red)
        PyImGui.text_colored("Drag", dim)
        PyImGui.same_line(0, 4)
        PyImGui.text("Pan / move")
        PyImGui.same_line(0, gap)
        PyImGui.text_colored("Shift+Click", dim)
        PyImGui.same_line(0, 4)
        PyImGui.text("Range select")
        PyImGui.same_line(0, gap)
        PyImGui.text_colored("Scroll", dim)
        PyImGui.same_line(0, 4)
        PyImGui.text("Zoom")

    def _draw_waypoints_on_canvas(self, child_pos: tuple) -> None:
        n_wps = len(self.waypoints)
        if n_wps == 0:
            return

        # Pre-compute transform once (avoids _fit_params per waypoint)
        offset_x, offset_y, scale, _ = self._fit_params(self.canvas_w, self.canvas_h)
        if scale == 0:
            return
        x_min = self.map_bounds.x_min
        y_max = self.map_bounds.y_max
        pan_x, pan_y = self.pan_x, self.pan_y
        cp_x, cp_y = child_pos

        # Pre-compute all screen positions in one pass
        screen_pos = []
        for wp in self.waypoints:
            sx = (wp.x - x_min) * scale + offset_x + pan_x + cp_x
            sy = (y_max - wp.y) * scale + offset_y + pan_y + cp_y
            screen_pos.append((sx, sy))

        # Pre-pack constant colors (avoid per-frame bit-packing)
        c_default = self.COLOR_WP_DEFAULT.to_color()
        c_hovered = self.COLOR_WP_HOVERED.to_color()
        c_selected = self.COLOR_WP_SELECTED.to_color()
        c_ambiguous = self.COLOR_WP_AMBIGUOUS.to_color()
        c_off_mesh = self.COLOR_WP_OFF_MESH.to_color()
        c_ring_endpoint = self.COLOR_RING_ENDPOINT.to_color()
        c_ring_interior = self.COLOR_RING_INTERIOR.to_color()
        c_ring_start = self.COLOR_RING_START.to_color()
        c_ring_end = self.COLOR_RING_END.to_color()
        c_label = self.COLOR_LABEL.to_color()

        # Path lines — colored by worst status of the two endpoints
        wps = self.waypoints
        for i in range(n_wps - 1):
            a, b = wps[i], wps[i + 1]
            if not a.on_mesh or not b.on_mesh:
                lc = c_off_mesh
            elif a.z_ambiguous or b.z_ambiguous:
                lc = c_ambiguous
            else:
                lc = c_default
            PyImGui.draw_list_add_line(
                screen_pos[i][0], screen_pos[i][1],
                screen_pos[i + 1][0], screen_pos[i + 1][1], lc, 2.0)

        # Waypoint circles
        base_radius = max(4.0, min(10.0, 6.0 * self.zoom_factor))
        sel_radius = base_radius * 1.4

        # Hoist selection state
        sel_start = self.sel_start
        sel_end = self.sel_end
        hovered = self.hovered_wp_index
        sel_count = (sel_end - sel_start + 1) if sel_start >= 0 else 0

        # Label layout
        CHAR_W = self._char_w
        CHAR_H = self._char_h
        LABEL_PAD = 2
        half_ch = CHAR_H / 2
        pending_labels = []
        occupied = []

        # Pass 1: circles and rings
        for i in range(n_wps):
            wp = wps[i]
            sx, sy = screen_pos[i]
            is_sel = sel_start >= 0 and sel_start <= i <= sel_end
            is_endpoint = is_sel and (i == sel_start or i == sel_end)

            if not wp.on_mesh:
                color = c_off_mesh
            elif is_sel:
                color = c_selected
            elif i == hovered:
                color = c_hovered
            elif wp.z_ambiguous:
                color = c_ambiguous
            else:
                color = c_default

            radius = sel_radius if is_sel else base_radius
            PyImGui.draw_list_add_circle_filled(sx, sy, radius, color, 12)

            # Selection ring
            if is_sel:
                ring_color = c_ring_endpoint if is_endpoint else c_ring_interior
                PyImGui.draw_list_add_circle(sx, sy, radius + 3, ring_color, 12, 2.0)

            # Start/end route markers (drawn outside selection ring)
            marker_r = radius + 6
            if i == 0:
                PyImGui.draw_list_add_circle(sx, sy, marker_r, c_ring_start, 12, 2.5)
            if i == n_wps - 1 and n_wps > 1:
                PyImGui.draw_list_add_circle(sx, sy, marker_r, c_ring_end, 12, 2.5)

            # Greedy non-overlapping label placement (decide now, draw later)
            label_text = str(i + 1)
            lx = sx + radius + 3
            ly = sy - half_ch
            lw = CHAR_W * len(label_text)
            label_rect = (lx, ly - LABEL_PAD, lx + lw + LABEL_PAD, ly + CHAR_H + LABEL_PAD)

            force_draw = i == hovered or (is_endpoint and sel_count <= 10)
            overlaps = False
            if not force_draw:
                for pr in occupied:
                    if label_rect[0] < pr[2] and label_rect[2] > pr[0] and label_rect[1] < pr[3] and label_rect[3] > pr[1]:
                        overlaps = True
                        break

            if force_draw or not overlaps:
                pending_labels.append((lx, ly, label_text))
                occupied.append(label_rect)

        # Pass 2: labels (drawn on top of all circles)
        for lx, ly, label_text in pending_labels:
            PyImGui.draw_list_add_text(lx, ly, c_label, label_text)

    def _draw_player_on_canvas(self, child_pos: tuple) -> None:
        if self.player_pos is None or self.map_id != self._game_map_id:
            return
        try:
            px, py = self.player_pos
            sx, sy = self._scale_coords(px, py, self.canvas_w, self.canvas_h)
            sx += child_pos[0]
            sy += child_pos[1]
            radius = max(5.0, min(20.0, 5.0 * self.zoom_factor))
            PyImGui.draw_list_add_circle_filled(sx, sy, radius, self.COLOR_PLAYER.to_color(), 12)
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Player draw error: {e}", Py4GW.Console.MessageType.Debug)

    def _draw_hover_tooltip(self, child_pos: tuple) -> None:
        if 0 <= self.hovered_wp_index < len(self.waypoints) and self.interaction == InteractionState.IDLE:
            wp = self.waypoints[self.hovered_wp_index]
            PyImGui.begin_tooltip()
            PyImGui.text(f"({wp.x:.0f}, {wp.y:.0f})")
            PyImGui.end_tooltip()

    def _draw_waypoint_panel(self) -> None:
        PyImGui.text("Waypoints")
        PyImGui.separator()

        avail_h = PyImGui.get_content_region_avail()[1]
        list_h = max(50, avail_h - self.BOTTOM_PANEL_H)

        # Brighter highlight for selected items
        PyImGui.push_style_color(PyImGui.ImGuiCol.Header, (0.35, 0.55, 0.86, 0.5))
        PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered, (0.4, 0.6, 0.9, 0.6))

        if PyImGui.begin_child("WPList", (0, list_h), border=True):
            for i, wp in enumerate(self.waypoints):
                is_sel = self._is_selected(i)
                is_last_selected = is_sel and i == self.sel_end
                label = f"{i + 1}. ({wp.x:.0f}, {wp.y:.0f})"

                style_count = 0
                if not wp.on_mesh:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.8, 0.28, 0.28, 1.0))
                    style_count += 1
                elif wp.z_ambiguous:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.86, 0.67, 0.31, 1.0))
                    style_count += 1

                clicked = PyImGui.selectable(f"{label}##{i}", is_sel, PyImGui.SelectableFlags.NoFlag, (0, 0))

                if not wp.on_mesh and PyImGui.is_item_hovered():
                    PyImGui.begin_tooltip()
                    PyImGui.text("Point outside of navigable area.")
                    PyImGui.end_tooltip()
                elif wp.z_ambiguous and PyImGui.is_item_hovered():
                    PyImGui.begin_tooltip()
                    PyImGui.text("Multiple z-planes overlap at this point.")
                    PyImGui.text("(x,y) pathing will assume the highest plane.")
                    PyImGui.end_tooltip()

                # Auto-scroll list to show canvas-selected item
                if is_last_selected and self._scroll_to_sel:
                    PyImGui.set_scroll_here_y(0.5)
                    self._scroll_to_sel = False

                if clicked:
                    io = PyImGui.get_io()
                    if io.key_shift and self.sel_anchor >= 0:
                        self._extend_selection(i)
                    else:
                        self._select_one(i)

                if is_last_selected:
                    self._draw_selection_actions(i)

                if style_count > 0:
                    PyImGui.pop_style_color(style_count)
        PyImGui.end_child()

        PyImGui.pop_style_color(2)  # Header, HeaderHovered

        # Bottom action buttons — three across
        full_w = PyImGui.get_content_region_avail()[0]
        gap = 4
        third_w = (full_w - gap * 2) / 3
        in_map = self.map_id == self._game_map_id
        if not in_map:
            self._draw_disabled_button(f"{Icons.ICON_PLUS} Player##addplayer", third_w)
        elif PyImGui.button(f"{Icons.ICON_PLUS} Player##addplayer", third_w):
            self._snapshot()
            px, py = self.player_pos if self.player_pos is not None else (0.0, 0.0)
            wp = Waypoint(px, py)
            self._validate_waypoint(wp)
            self.waypoints.append(wp)
            self._select_one(len(self.waypoints) - 1)
        PyImGui.same_line(0, gap)
        if PyImGui.button(f"{Icons.ICON_UNDO} Undo##undo", third_w):
            self._undo()
        PyImGui.same_line(0, gap)
        if PyImGui.button(f"{Icons.ICON_ERASER} Clear All##clear", third_w):
            self._snapshot()
            self.waypoints.clear()
            self._clear_selection()

        # Manual coordinate entry row: [___] X  [___] Y  [+]
        btn_add_w = self.BTN_W
        lbl_w = self._lbl_x_w
        input_w = (full_w - lbl_w * 2 - btn_add_w - gap * 2) / 2

        PyImGui.push_item_width(input_w)
        self._input_x = PyImGui.input_text("X##inX", self._input_x)
        PyImGui.pop_item_width()
        PyImGui.same_line(0, gap)
        PyImGui.push_item_width(input_w)
        self._input_y = PyImGui.input_text("Y##inY", self._input_y)
        PyImGui.pop_item_width()
        PyImGui.same_line(0, gap)
        if PyImGui.button(f"{Icons.ICON_PLUS}##addcoord", btn_add_w, self.BTN_H):
            try:
                wx, wy = float(self._input_x), float(self._input_y)
                self._snapshot()
                wp = Waypoint(wx, wy)
                self._validate_waypoint(wp)
                self.waypoints.append(wp)
                self._select_one(len(self.waypoints) - 1)
            except ValueError:
                pass

    def _draw_selection_actions(self, i: int) -> None:
        """Draw move/delete/auto-path buttons below the last selected item."""
        sel_min = PyImGui.get_item_rect_min()
        sel_max = PyImGui.get_item_rect_max()
        n_sel = self._sel_count()
        plural = n_sel > 1

        PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos()[0] + self.BTN_INDENT)
        if PyImGui.button(f"{Icons.ICON_ARROW_UP}##up{i}", self.BTN_W, self.BTN_H):
            self._move_selection_up()
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.text(f"Move {n_sel} waypoints up" if plural else "Move waypoint up")
            PyImGui.end_tooltip()

        btn_min = PyImGui.get_item_rect_min()
        btn_max = PyImGui.get_item_rect_max()

        PyImGui.same_line(0, 3)
        if PyImGui.button(f"{Icons.ICON_ARROW_DOWN}##dn{i}", self.BTN_W, self.BTN_H):
            self._move_selection_down()
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.text(f"Move {n_sel} waypoints down" if plural else "Move waypoint down")
            PyImGui.end_tooltip()

        PyImGui.same_line(0, 3)
        if PyImGui.button(f"{Icons.ICON_TRASH}##rm{i}", self.BTN_W, self.BTN_H):
            self._delete_selection()
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.text(f"Delete {n_sel} waypoints" if plural else "Delete waypoint")
            PyImGui.end_tooltip()

        # Auto-path button (only when 2+ selected)
        if n_sel >= 2:
            in_map = self.map_id == self._game_map_id
            PyImGui.same_line(0, 3)
            if not in_map:
                self._draw_disabled_button(f"{Icons.ICON_ROUTE}##ap{i}", self.BTN_W, self.BTN_H)
            elif self.auto_path_computing:
                PyImGui.button(f"...##ap{i}", self.BTN_W, self.BTN_H)
            else:
                if PyImGui.button(f"{Icons.ICON_ROUTE}##ap{i}", self.BTN_W, self.BTN_H):
                    self._auto_path_between()
            if PyImGui.is_item_hovered():
                PyImGui.begin_tooltip()
                PyImGui.text("Auto-path between first and last selected")
                if not in_map:
                    PyImGui.text_colored("Must be in map", (1.0, 0.3, 0.3, 1.0))
                PyImGui.end_tooltip()

        # L-shaped connector from item to buttons
        connector_color = self.COLOR_CONNECTOR.to_color()
        corner_x = sel_min[0] + 8
        corner_y = (btn_min[1] + btn_max[1]) / 2
        PyImGui.draw_list_add_line(corner_x, sel_max[1], corner_x, corner_y, connector_color, 1.5)
        PyImGui.draw_list_add_line(corner_x, corner_y, btn_min[0], corner_y, connector_color, 1.5)

    # endregion

    # region Update

    def update(self) -> None:
        if not Map.IsMapReady():
            self.player_pos = None
            return

        # Load pathing (sync dat read with live fallback for current map)
        layers = Map.Pathing.GetPathingMapsForMap(self.map_id)
        if layers and layers is not self.pathing_map:
            self._apply_pathing(layers)

        # Cache player position
        try:
            x, y = Player.GetXY()
            if x != 0.0 or y != 0.0:
                self.player_pos = (x, y)
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Player position read error: {e}", Py4GW.Console.MessageType.Debug)

        # Track game map (no auto-switch — user controls dropdown)
        current_id = Map.GetMapID()
        if current_id != 0 and current_id != self._game_map_id:
            self._game_map_id = current_id
            # Reload live navmesh for the new game map
            self.navmesh = None
            self._load_navmesh_object()

    # endregion

# endregion

# region Lifecycle

INI_KEY = ""
INI_PATH = "Widgets/RouteBuilder"
INI_FILENAME = "RouteBuilder.ini"

initialized = False
widget = None


def main():
    global INI_KEY, initialized, widget
    if initialized:
        return
    if not Routines.Checks.Map.MapValid():
        return

    if not INI_KEY:
        INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
        if not INI_KEY:
            return

    IniManager().load_once(INI_KEY)
    widget = RouteBuilderWidget()
    initialized = True


def draw():
    global initialized, widget
    if initialized and widget:
        try:
            widget.draw()
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Draw error: {e}", Py4GW.Console.MessageType.Error)


def update():
    global initialized, widget
    if initialized and widget:
        try:
            widget.update()
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Update error: {e}", Py4GW.Console.MessageType.Error)


def tooltip():
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()
    PyImGui.text("Visual editor for designing waypoint routes on any game map.")
    PyImGui.text("Build, refine, and export coordinate paths for bots and scripts.")
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Interactive canvas with navmesh overlay for any map")
    PyImGui.bullet_text("Auto-pathing between waypoints via the navigation mesh")
    PyImGui.bullet_text("Off-mesh and z-plane ambiguity warnings")
    PyImGui.bullet_text("Range selection, reordering, and undo history")
    PyImGui.bullet_text("Import/export coordinate lists to clipboard")
    PyImGui.end_tooltip()

# endregion

if __name__ == "__main__":
    main()
