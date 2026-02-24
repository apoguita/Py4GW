def configure():
    _draw_config_ui()


def main():
    _update_runtime()
    _draw_ui()


__all__ = ["main", "configure"]


import math

import PyImGui

from Py4GWCoreLib import Map, Player, Routines, ThrottledTimer, Utils, AutoPathing, GLOBAL_CACHE
from Py4GWCoreLib.Pathing import NavMesh


MODULE_NAME = "Carto Helper"


class _Config:
    def __init__(self):
        self.enabled = True
        self.auto_move = True
        self.show_panel = True
        self.show_markers = True
        self.max_ring_radius = 2800.0
        self.ring_step = 280.0
        self.base_ring_points = 12


class _State:
    def __init__(self):
        self.last_map_id = 0
        self.last_mission_event_normalized: tuple[float, float] | None = None
        self.raw_right_click_norm = (0.0, 0.0)
        self.raw_right_click_screen = (0.0, 0.0)
        self.raw_right_click_game = (0.0, 0.0)
        self.last_ioevent_timestamp = 0
        self.last_detection_mode = "none"
        self.gw_last_mouse_location: tuple[float, float] = (0.0, 0.0)
        self.last_clicked_target: tuple[float, float] | None = None
        self.last_snapped_target: tuple[float, float] | None = None
        self.last_path_points = 0
        self.last_distance_to_click = 0.0
        self.last_query_count = 0
        self.last_status = "Bereit"
        self.navmesh: NavMesh | None = None
        self.navmesh_map_id: int = 0
        self.current_path: list[tuple[float, float]] = []
        self.path_computing: bool = False


cfg = _Config()
state = _State()

input_throttle = ThrottledTimer(35)


def _ui_checkbox(label: str, current: bool) -> bool:
    result = PyImGui.checkbox(label, bool(current))
    if isinstance(result, tuple) and len(result) == 2:
        return bool(result[1])
    return bool(result)


def _ui_slider_int(label: str, current: int, min_v: int, max_v: int) -> int:
    result = PyImGui.slider_int(label, int(current), int(min_v), int(max_v))
    if isinstance(result, tuple) and len(result) == 2:
        return int(result[1])
    return int(result)


def _ui_slider_float(label: str, current: float, min_v: float, max_v: float) -> float:
    result = PyImGui.slider_float(label, float(current), float(min_v), float(max_v))
    if isinstance(result, tuple) and len(result) == 2:
        return float(result[1])
    return float(result)


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _is_inside_bounds(point: tuple[float, float]) -> bool:
    min_x, min_y, max_x, max_y = Map.GetMapBoundaries()
    if min_x > max_x:
        min_x, max_x = max_x, min_x
    if min_y > max_y:
        min_y, max_y = max_y, min_y
    return min_x <= point[0] <= max_x and min_y <= point[1] <= max_y


# ── NavMesh helpers ───────────────────────────────────────────────────

def _get_navmesh() -> NavMesh | None:
    """Return cached NavMesh for the current map, building it if necessary."""
    map_id = int(Map.GetMapID())
    if map_id == 0:
        return None
    if state.navmesh is not None and state.navmesh_map_id == map_id:
        return state.navmesh
    try:
        pathing_maps = Map.Pathing.GetPathingMaps()
        if not pathing_maps:
            return None
        state.navmesh = NavMesh(pathing_maps, map_id)
        state.navmesh_map_id = map_id
        state.last_status = f"NavMesh geladen ({map_id})"
    except Exception as e:
        state.last_status = f"NavMesh Fehler: {e}"
        return None
    return state.navmesh


def _is_on_navmesh(point: tuple[float, float], margin: float = 20.0) -> bool:
    """Return True only if point is strictly inside a navmesh trapezoid (not just near one).

    Uses find_with_margin so snapped points are comfortably inside the mesh,
    not on an edge or in a gap between trapezoids.
    """
    nav = _get_navmesh()
    if nav is None:
        return False
    return nav._bsp.find_with_margin(point[0], point[1], margin)


def _launch_path_computation(goal_x: float, goal_y: float):
    """Coroutine: compute path from player to goal and store in state.current_path."""
    state.path_computing = True
    state.current_path = []
    path = yield from AutoPathing().get_path_to(goal_x, goal_y)
    state.current_path = list(path) if path else []
    state.path_computing = False


def _ring_candidates(target_xy: tuple[float, float]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    radius = float(cfg.ring_step)
    while radius <= float(cfg.max_ring_radius):
        point_count = max(8, int(cfg.base_ring_points + radius / 280.0))
        for i in range(point_count):
            angle = (2.0 * math.pi * i) / point_count
            x = target_xy[0] + math.cos(angle) * radius
            y = target_xy[1] + math.sin(angle) * radius
            out.append((x, y))
        radius += float(cfg.ring_step)
    return out


def _find_best_reachable(click_xy: tuple[float, float]) -> tuple[tuple[float, float] | None, int, int]:
    """Find the nearest navmesh point to click_xy, independent of player position.

    Strategy:
      1. If click itself is on the navmesh → return it directly.
      2. Otherwise expand rings outward from the click and return the
         candidate with the smallest distance to click_xy that is on the navmesh.
    """
    query_count = 0

    # 1. Direct hit
    query_count += 1
    if _is_on_navmesh(click_xy):
        return click_xy, 0, query_count

    # 2. Ring search centred on click – pick closest navmesh hit
    best_point: tuple[float, float] | None = None
    best_dist = float("inf")
    for candidate in _ring_candidates(click_xy):
        if not _is_inside_bounds(candidate):
            continue
        query_count += 1
        if _is_on_navmesh(candidate):
            d = _distance(candidate, click_xy)
            if d < best_dist:
                best_dist = d
                best_point = candidate

    return best_point, 0, query_count


def _on_mission_map_right_click(click_game: tuple[float, float]) -> None:
    state.last_clicked_target = click_game

    if not Map.IsExplorable():
        state.last_status = "Outpost/Non-explorable – kein Pathing"
        state.last_snapped_target = None
        return

    snapped, path_points, query_count = _find_best_reachable(click_game)
    state.last_query_count = query_count

    if snapped is None:
        state.last_snapped_target = None
        state.last_path_points = 0
        state.last_distance_to_click = 0.0
        state.last_status = "Kein erreichbarer Punkt gefunden"
        return

    state.last_snapped_target = snapped
    state.last_path_points = path_points
    state.last_distance_to_click = _distance(snapped, click_game)
    state.last_status = "Erreichbarer Punkt gefunden"

    if cfg.auto_move:
        state.current_path = []
        GLOBAL_CACHE.Coroutines.append(_launch_path_computation(snapped[0], snapped[1]))
        Player.Move(snapped[0], snapped[1])
        state.last_status = "Pfad wird berechnet …"


def _try_get_mission_right_click_game_pos() -> tuple[bool, tuple[float, float] | None]:
    """Detect a new right-click on the mission map via Map.MissionMap.GetLastRightClickCoords().

    Returns the last click coords as game-space (gwinches) when a new click is detected.
    Uses timestamp-deduplicated event from Map.MissionMap which reads GWContext internally.
    """
    nx, ny = Map.MissionMap.GetLastRightClickCoords()
    new_pos = (float(nx), float(ny))

    if new_pos == (0.0, 0.0):
        return False, None
    if new_pos == state.gw_last_mouse_location:
        return False, None

    state.gw_last_mouse_location = new_pos
    gx, gy = Map.MissionMap.MapProjection.NormalizedScreenToGamePos(nx, ny)
    sx, sy = Map.MissionMap.MapProjection.NormalizedScreenToScreen(nx, ny)
    state.raw_right_click_norm = new_pos
    state.raw_right_click_screen = (float(sx), float(sy))
    state.raw_right_click_game = (float(gx), float(gy))
    state.last_mission_event_normalized = new_pos
    state.last_detection_mode = "mission_map_event"
    return True, state.raw_right_click_game


def _update_runtime() -> None:
    if not cfg.enabled:
        return
    if not Routines.Checks.Map.MapValid():
        return

    map_id = int(Map.GetMapID())
    if map_id != state.last_map_id:
        state.last_map_id = map_id
        state.last_mission_event_normalized = None
        state.raw_right_click_norm = (0.0, 0.0)
        state.raw_right_click_screen = (0.0, 0.0)
        state.raw_right_click_game = (0.0, 0.0)
        state.last_ioevent_timestamp = 0
        state.last_detection_mode = "none"
        state.navmesh = None
        state.navmesh_map_id = 0
        state.current_path = []
        state.path_computing = False
        # Seed detect-state so we don't fire spuriously on the first click after map load
        _seed = Map.MissionMap.GetLastRightClickCoords()
        state.gw_last_mouse_location = (float(_seed[0]), float(_seed[1]))
        state.last_clicked_target = None
        state.last_snapped_target = None
        state.last_path_points = 0
        state.last_distance_to_click = 0.0
        state.last_query_count = 0
        state.last_status = "Map gewechselt"

    clicked, click_game = _try_get_mission_right_click_game_pos()
    if clicked and click_game is not None:
        _on_mission_map_right_click(click_game)


def _draw_config_ui() -> None:
    PyImGui.text("MissionMap RightClick -> Reachable")
    PyImGui.separator()
    cfg.enabled = _ui_checkbox("Enabled", cfg.enabled)
    cfg.auto_move = _ui_checkbox("Auto MoveTo on mission right click", cfg.auto_move)
    cfg.show_panel = _ui_checkbox("Show status panel", cfg.show_panel)
    cfg.show_markers = _ui_checkbox("Show mission map markers", cfg.show_markers)
    cfg.max_ring_radius = _ui_slider_float("Max search radius", cfg.max_ring_radius, 600.0, 6000.0)
    cfg.ring_step = _ui_slider_float("Ring step", cfg.ring_step, 120.0, 800.0)
    cfg.base_ring_points = _ui_slider_int("Base ring points", cfg.base_ring_points, 8, 40)

    if PyImGui.button("Open Mission Map"):
        Map.MissionMap.OpenWindow()

    if PyImGui.button("Clear markers"):
        state.last_mission_event_normalized = None
        state.last_clicked_target = None
        state.last_snapped_target = None
        state.current_path = []
        state.path_computing = False
        state.last_path_points = 0
        state.last_distance_to_click = 0.0
        state.last_query_count = 0
        state.last_status = "Marker gelöscht"


def _draw_status_panel() -> None:
    if not cfg.show_panel:
        return
    PyImGui.set_next_window_size((380.0, 0.0), int(PyImGui.ImGuiCond.FirstUseEver))
    if PyImGui.begin("Carto Helper##mission_snap"):
        PyImGui.text("Mission map right click -> nearest reachable point")
        PyImGui.separator()
        PyImGui.text(f"Mission Map open: {Map.MissionMap.IsWindowOpen()}")
        PyImGui.text(f"Map explorable: {Map.IsExplorable()}")
        PyImGui.text(f"Mouse over: {Map.MissionMap.IsMouseOver()}")
        PyImGui.text(f"Detect mode: {state.last_detection_mode}")
        PyImGui.text(f"Status: {state.last_status}")
        _live_nx, _live_ny = Map.MissionMap.GetLastRightClickCoords()
        PyImGui.text(f"Last RC (map event):  ({_live_nx:.4f}, {_live_ny:.4f})")
        PyImGui.text(f"State gw_last:        ({state.gw_last_mouse_location[0]:.4f}, {state.gw_last_mouse_location[1]:.4f})")
        PyImGui.text(f"Values differ: {(_live_nx, _live_ny) != state.gw_last_mouse_location}")
        PyImGui.text(f"Path points: {len(state.current_path)} {'(computing…)' if state.path_computing else ''}")
        PyImGui.text(f"Path queries: {state.last_query_count}")
        PyImGui.text(f"Distance click->snap: {state.last_distance_to_click:.1f}")
        nm = state.navmesh
        PyImGui.text(f"NavMesh: {'OK (' + str(len(nm.trapezoids)) + ' traps)' if nm else 'nicht geladen'}")
        if state.last_mission_event_normalized is not None:
            PyImGui.text(
                f"Last mission right click norm: ({state.last_mission_event_normalized[0]:.3f}, {state.last_mission_event_normalized[1]:.3f})"
            )
        PyImGui.text(
            f"Raw right click norm: ({state.raw_right_click_norm[0]:.3f}, {state.raw_right_click_norm[1]:.3f})"
        )
        PyImGui.text(
            f"Raw right click screen: ({state.raw_right_click_screen[0]:.1f}, {state.raw_right_click_screen[1]:.1f})"
        )
        if state.last_clicked_target is not None:
            PyImGui.text(f"Clicked: {state.last_clicked_target[0]:.0f}, {state.last_clicked_target[1]:.0f}")
        if state.last_snapped_target is not None:
            PyImGui.text(f"Snapped: {state.last_snapped_target[0]:.0f}, {state.last_snapped_target[1]:.0f}")
    PyImGui.end()


def _begin_mission_map_overlay() -> bool:
    left, top, right, bottom = Map.MissionMap.GetMissionMapContentsCoords()
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return False

    PyImGui.set_next_window_pos(left, top)
    PyImGui.set_next_window_size(width, height)
    flags = (
        PyImGui.WindowFlags.NoTitleBar
        | PyImGui.WindowFlags.NoScrollbar
        | PyImGui.WindowFlags.NoMove
        | PyImGui.WindowFlags.NoSavedSettings
        | PyImGui.WindowFlags.NoBackground
        | PyImGui.WindowFlags.NoInputs
    )
    return PyImGui.begin("##carto_missionmap_overlay", flags)


def _draw_mission_markers() -> None:
    if not cfg.show_markers:
        return
    if state.last_clicked_target is None and state.last_snapped_target is None:
        return
    if not Map.MissionMap.IsWindowOpen():
        return

    if not _begin_mission_map_overlay():
        PyImGui.end()
        return

    # Where you clicked on the map (small white dot)
    click_color         = Utils.RGBToColor(220, 220, 220, 200)
    # Nearest reachable navmesh point → RED, prominent
    navmesh_color       = Utils.RGBToColor(255, 50, 50, 255)
    navmesh_color_inner = Utils.RGBToColor(255, 160, 160, 200)
    line_color          = Utils.RGBToColor(255, 255, 255, 160)

    click_screen = None
    snap_screen  = None

    # Calculate projected positions first
    if state.last_clicked_target is not None:
        click_screen = Map.MissionMap.MapProjection.GameMapToScreen(
            state.last_clicked_target[0], state.last_clicked_target[1])

    if state.last_snapped_target is not None:
        snap_screen = Map.MissionMap.MapProjection.GameMapToScreen(
            state.last_snapped_target[0], state.last_snapped_target[1])

    # Computed navmesh path (player → snapped point)
    if len(state.current_path) >= 2:
        path_color = Utils.RGBToColor(80, 160, 255, 210)
        prev_s: tuple[float, float] | None = None
        for px, py in state.current_path:
            cur_s = Map.MissionMap.MapProjection.GameMapToScreen(px, py)
            if prev_s is not None:
                PyImGui.draw_list_add_line(prev_s[0], prev_s[1], cur_s[0], cur_s[1], path_color, 2.5)
            prev_s = cur_s

    # Thin line from click to snap (draw first, markers on top)
    if click_screen is not None and snap_screen is not None:
        PyImGui.draw_list_add_line(click_screen[0], click_screen[1], snap_screen[0], snap_screen[1], line_color, 1.0)

    # Click marker: hide when almost on top of snapped marker
    draw_click_marker = click_screen is not None
    if click_screen is not None and snap_screen is not None:
        if _distance(click_screen, snap_screen) <= 12.0:
            draw_click_marker = False

    if draw_click_marker and click_screen is not None:
        PyImGui.draw_list_add_circle_filled(click_screen[0], click_screen[1], 2.5, click_color, 12)
        PyImGui.draw_list_add_circle(click_screen[0], click_screen[1], 4.0, click_color, 12, 1.0)

    # Nearest navmesh point: draw last so it always stays visible
    if snap_screen is not None:
        sx, sy   = snap_screen[0], snap_screen[1]
        r_inner  = 6.0
        r_outer  = 11.0
        cross    = 15.0  # half-length of crosshair arms beyond outer ring
        strong_red = Utils.RGBToColor(255, 0, 0, 255)
        PyImGui.draw_list_add_circle_filled(sx, sy, r_inner, strong_red, 20)
        PyImGui.draw_list_add_circle(sx, sy, r_outer, navmesh_color, 24, 2.5)
        PyImGui.draw_list_add_line(sx - cross, sy, sx - r_outer, sy, navmesh_color, 1.5)
        PyImGui.draw_list_add_line(sx + r_outer, sy, sx + cross, sy, navmesh_color, 1.5)
        PyImGui.draw_list_add_line(sx, sy - cross, sx, sy - r_outer, navmesh_color, 1.5)
        PyImGui.draw_list_add_line(sx, sy + r_outer, sx, sy + cross, navmesh_color, 1.5)

    PyImGui.end()


def _draw_ui() -> None:
    _draw_status_panel()
    _draw_mission_markers()
