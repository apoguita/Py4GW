"""Per-follower stuck detection + detour pathing.

When a follower can't make progress toward its FollowPos, this module builds
a detour path and walks it via BT.Move. Two modes:

  - Enemy slalom (primary): if any enemy is within enemy_detection_range,
    cluster overlapping enemy circles into welded shapes (peanut outlines)
    and route around the cluster nearest to the goal via tangent walking on
    the union boundary. Probes both sides, picks the walkable shorter one.

  - Front-of-follower circle (fallback): no enemies in range — generate a
    half-arc around an imaginary obstacle one touch_radius ahead.

Both modes feed waypoints to BT.Movement.MoveDirect; tolerance, radius, and
the detection thresholds are live-tunable via FollowRuntime.ini sliders.

Consumed by HeroAI/follow/follower_runtime.py only. Import exact symbols,
not the package root (per AGENTS.md follow-package rule).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import Py4GW

import HeroAI.globals as hero_globals
from Py4GWCoreLib import Agent, AgentArray, ThrottledTimer, Utils
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT


# Outer-ring radius for waypoint overlay; not a behavior knob.
_OVERLAY_TOUCH_RADIUS: float = 25.0


@dataclass(slots=True)
class SmartUnstuckConfig:
    # BT.Move "advance on approach" threshold. Larger = smoother/cuts corners;
    # smaller = closer to the arc but risks stopping at each waypoint.
    waypoint_smoothing: float = 77.0

    touch_radius: float = 120.0                  # detour-circle radius (live-tunable via INI)
    enemy_detection_range: float = 250.0         # enemy-slalom scan radius (live-tunable via INI)
    progress_sample_interval_ms: int = 500       # idle-mode sample period
    no_progress_close_units: float = 10.0        # < this distance closed per sample → no-progress sample (live-tunable via INI)
    no_progress_move_units: float = 15.0         # < this distance moved per sample → no-progress sample (live-tunable via INI)
    stuck_sample_count: int = 1                  # consecutive no-progress samples to trigger (1 = ~500ms) (live-tunable via INI)
    # Short-circuit detection when the follower is already this close to slot.
    min_distance_activate_unstuck: float = 500.0        # (live-tunable via INI)
    waypoint_count: int = 5                      # front-of-follower mode only; slalom uses adaptive count
    arc_span_rad: float = math.pi                # front-of-follower mode: half-circle per side
    total_detour_timeout_ms: int = 12000         # absolute cap on a single detour
    # Detour exits early when the follower has closed >= this much distance
    # from its starting dist_to_follow.
    obstacle_cleared_delta: float = 500.0        # (live-tunable via INI)
    navmesh_contains_margin: float = 50.0        # margin for navmesh.contains()
    navmesh_snap_tolerance: float = 80.0         # accept snap from find_nearest_reachable within this
    arc_walkability_required_fraction: float = 0.5  # front-of-follower mode side acceptance
    preferred_side_when_both_walkable: int = 1   # +1 right, -1 left


@dataclass(slots=True)
class SmartUnstuckState:
    mode: str = "idle"                                              # "idle" | "detouring"
    progress_timer: ThrottledTimer | None = None
    prev_sample_xy: tuple[float, float] | None = None
    prev_sample_dist: float | None = None
    no_progress_samples: int = 0
    waypoints: tuple[tuple[float, float], ...] = ()
    waypoint_idx: int = 0
    detour_started_ms: int = 0
    waypoint_started_ms: int = 0
    detour_start_dist: float = 0.0
    circle_center: tuple[float, float] | None = None
    # Slalom mode: one entry per accepted enemy (path order). Empty in
    # front-of-follower mode.
    slalom_centers: tuple[tuple[float, float], ...] = ()
    # Slalom mode: closed polyline per cluster — the welded union outline used
    # for tangent walking. Rendered by the 3D overlay so the merged peanut
    # shape is visible instead of separate rings.
    slalom_union_boundaries: tuple[tuple[tuple[float, float], ...], ...] = ()
    # Path index of the waypoint nearest follow_xy. Once BT reaches it the
    # detour exits early; -1 disables.
    abort_waypoint_idx: int = -1
    sides_tried: set[int] = field(default_factory=set)  # front-of-follower mode side bookkeeping
    detour_tree: BehaviorTree | None = None
    # Per-tick diagnostics (verbose-only).
    tick_count: int = 0
    last_tick_ms: int = 0
    last_tick_xy: tuple[float, float] | None = None
    waypoint_enter_ms: int = 0


SMART_UNSTUCK_CFG = SmartUnstuckConfig()

_first_call_logged = False

# Cross-client config sync. The leader's UI writes smart-unstuck knobs to the
# global FollowRuntime.ini; each follower process polls that INI on a 1s
# throttle so slider changes propagate within a second without restart.
_INI_PATH = "HeroAI"
_INI_FILENAME = "FollowRuntime.ini"
_INI_SECTION = "FollowRuntime"
_INI_KEY_TOLERANCE = "waypoint_smoothing"
_INI_KEY_TOUCH_RADIUS = "stuck_touch_radius"
_INI_KEY_ENEMY_RANGE = "stuck_enemy_detection_range"
_INI_KEY_SAMPLE_COUNT = "stuck_sample_count"
_INI_KEY_MIN_DISTANCE = "min_distance_activate_unstuck"
_INI_KEY_MOVE_UNITS = "no_progress_move_units"
_INI_KEY_CLOSE_UNITS = "no_progress_close_units"
_INI_KEY_OVERLAY = "show_followers_unstuck_overlay"
_INI_KEY_EARLY_EXIT = "obstacle_cleared_delta"
# Bounds for the live-tunable radii. Slider UI uses the same range.
_RADIUS_MIN: float = 50.0
_RADIUS_MAX: float = 400.0
# Bounds for the new stuck-detection knobs.
_SAMPLE_COUNT_MIN: int = 1
_SAMPLE_COUNT_MAX: int = 10
_MIN_DISTANCE_MIN: float = 50.0
_MIN_DISTANCE_MAX: float = 600.0
_PROGRESS_UNITS_MIN: float = 1.0
_PROGRESS_UNITS_MAX: float = 100.0
_EARLY_EXIT_MIN: float = 50.0
_EARLY_EXIT_MAX: float = 800.0
_CONFIG_INI_KEY: str = ""
_CONFIG_VARS_REGISTERED: bool = False
_CONFIG_RELOAD_TIMER = ThrottledTimer(1000)


def _clamp_radius(value: float) -> float:
    return max(_RADIUS_MIN, min(_RADIUS_MAX, float(value)))


def _clamp_sample_count(value: int) -> int:
    return max(_SAMPLE_COUNT_MIN, min(_SAMPLE_COUNT_MAX, int(value)))


def _clamp_min_distance(value: float) -> float:
    return max(_MIN_DISTANCE_MIN, min(_MIN_DISTANCE_MAX, float(value)))


def _clamp_progress_units(value: float) -> float:
    return max(_PROGRESS_UNITS_MIN, min(_PROGRESS_UNITS_MAX, float(value)))


def _clamp_early_exit(value: float) -> float:
    return max(_EARLY_EXIT_MIN, min(_EARLY_EXIT_MAX, float(value)))


def _ensure_stuck_config_ini_vars() -> str:
    global _CONFIG_INI_KEY, _CONFIG_VARS_REGISTERED
    if not _CONFIG_INI_KEY:
        try:
            _CONFIG_INI_KEY = IniManager().ensure_global_key(_INI_PATH, _INI_FILENAME)
        except Exception:
            return ""
    if not _CONFIG_INI_KEY:
        return ""
    if not _CONFIG_VARS_REGISTERED:
        try:
            im = IniManager()
            im.add_float(
                _CONFIG_INI_KEY,
                _INI_KEY_TOLERANCE,
                _INI_SECTION,
                _INI_KEY_TOLERANCE,
                SMART_UNSTUCK_CFG.waypoint_smoothing,
            )
            im.add_float(
                _CONFIG_INI_KEY,
                _INI_KEY_TOUCH_RADIUS,
                _INI_SECTION,
                _INI_KEY_TOUCH_RADIUS,
                SMART_UNSTUCK_CFG.touch_radius,
            )
            im.add_float(
                _CONFIG_INI_KEY,
                _INI_KEY_ENEMY_RANGE,
                _INI_SECTION,
                _INI_KEY_ENEMY_RANGE,
                SMART_UNSTUCK_CFG.enemy_detection_range,
            )
            im.add_int(
                _CONFIG_INI_KEY,
                _INI_KEY_SAMPLE_COUNT,
                _INI_SECTION,
                _INI_KEY_SAMPLE_COUNT,
                SMART_UNSTUCK_CFG.stuck_sample_count,
            )
            im.add_float(
                _CONFIG_INI_KEY,
                _INI_KEY_MIN_DISTANCE,
                _INI_SECTION,
                _INI_KEY_MIN_DISTANCE,
                SMART_UNSTUCK_CFG.min_distance_activate_unstuck,
            )
            im.add_float(
                _CONFIG_INI_KEY,
                _INI_KEY_MOVE_UNITS,
                _INI_SECTION,
                _INI_KEY_MOVE_UNITS,
                SMART_UNSTUCK_CFG.no_progress_move_units,
            )
            im.add_float(
                _CONFIG_INI_KEY,
                _INI_KEY_CLOSE_UNITS,
                _INI_SECTION,
                _INI_KEY_CLOSE_UNITS,
                SMART_UNSTUCK_CFG.no_progress_close_units,
            )
            im.add_bool(
                _CONFIG_INI_KEY,
                _INI_KEY_OVERLAY,
                _INI_SECTION,
                _INI_KEY_OVERLAY,
                hero_globals.show_followers_unstuck_overlay,
            )
            im.add_float(
                _CONFIG_INI_KEY,
                _INI_KEY_EARLY_EXIT,
                _INI_SECTION,
                _INI_KEY_EARLY_EXIT,
                SMART_UNSTUCK_CFG.obstacle_cleared_delta,
            )
            _CONFIG_VARS_REGISTERED = True
        except Exception:
            return ""
    return _CONFIG_INI_KEY


def reload_smart_unstuck_config_from_ini(force_reload: bool = False) -> None:
    """Pull live SMART_UNSTUCK_CFG values from FollowRuntime.ini.
    Throttled to once per second; force_reload bypasses the throttle.
    Lets follower processes pick up slider changes made on the leader.
    """
    key = _ensure_stuck_config_ini_vars()
    if not key:
        return
    if not force_reload and not _CONFIG_RELOAD_TIMER.IsExpired():
        return
    _CONFIG_RELOAD_TIMER.Reset()
    im = IniManager()
    try:
        im.reload(key)
    except Exception:
        pass

    try:
        new_waypoint_smoothing = max(1.0, float(
            im.read_float(key, _INI_SECTION, _INI_KEY_TOLERANCE, SMART_UNSTUCK_CFG.waypoint_smoothing)
        ))
    except Exception:
        new_waypoint_smoothing = SMART_UNSTUCK_CFG.waypoint_smoothing
    try:
        new_radius = _clamp_radius(
            im.read_float(key, _INI_SECTION, _INI_KEY_TOUCH_RADIUS, SMART_UNSTUCK_CFG.touch_radius)
        )
    except Exception:
        new_radius = SMART_UNSTUCK_CFG.touch_radius
    try:
        new_enemy_range = _clamp_radius(
            im.read_float(key, _INI_SECTION, _INI_KEY_ENEMY_RANGE, SMART_UNSTUCK_CFG.enemy_detection_range)
        )
    except Exception:
        new_enemy_range = SMART_UNSTUCK_CFG.enemy_detection_range
    try:
        new_sample_count = _clamp_sample_count(
            im.read_int(key, _INI_SECTION, _INI_KEY_SAMPLE_COUNT, SMART_UNSTUCK_CFG.stuck_sample_count)
        )
    except Exception:
        new_sample_count = SMART_UNSTUCK_CFG.stuck_sample_count
    try:
        new_min_distance = _clamp_min_distance(
            im.read_float(key, _INI_SECTION, _INI_KEY_MIN_DISTANCE, SMART_UNSTUCK_CFG.min_distance_activate_unstuck)
        )
    except Exception:
        new_min_distance = SMART_UNSTUCK_CFG.min_distance_activate_unstuck
    try:
        new_move_units = _clamp_progress_units(
            im.read_float(key, _INI_SECTION, _INI_KEY_MOVE_UNITS, SMART_UNSTUCK_CFG.no_progress_move_units)
        )
    except Exception:
        new_move_units = SMART_UNSTUCK_CFG.no_progress_move_units
    try:
        new_close_units = _clamp_progress_units(
            im.read_float(key, _INI_SECTION, _INI_KEY_CLOSE_UNITS, SMART_UNSTUCK_CFG.no_progress_close_units)
        )
    except Exception:
        new_close_units = SMART_UNSTUCK_CFG.no_progress_close_units
    try:
        new_overlay = bool(
            im.read_bool(key, _INI_SECTION, _INI_KEY_OVERLAY, hero_globals.show_followers_unstuck_overlay)
        )
    except Exception:
        new_overlay = hero_globals.show_followers_unstuck_overlay
    try:
        new_early_exit = _clamp_early_exit(
            im.read_float(key, _INI_SECTION, _INI_KEY_EARLY_EXIT, SMART_UNSTUCK_CFG.obstacle_cleared_delta)
        )
    except Exception:
        new_early_exit = SMART_UNSTUCK_CFG.obstacle_cleared_delta

    if abs(new_waypoint_smoothing - SMART_UNSTUCK_CFG.waypoint_smoothing) > 0.01 or force_reload:
        old = SMART_UNSTUCK_CFG.waypoint_smoothing
        SMART_UNSTUCK_CFG.waypoint_smoothing = new_waypoint_smoothing
        _log(f"stuck.cfg_reload waypoint_smoothing {old:.1f}->{new_waypoint_smoothing:.1f} force={force_reload}")
    if abs(new_radius - SMART_UNSTUCK_CFG.touch_radius) > 0.01 or force_reload:
        old = SMART_UNSTUCK_CFG.touch_radius
        SMART_UNSTUCK_CFG.touch_radius = new_radius
        _log(f"stuck.cfg_reload touch_radius {old:.1f}->{new_radius:.1f} force={force_reload}")
    if abs(new_enemy_range - SMART_UNSTUCK_CFG.enemy_detection_range) > 0.01 or force_reload:
        old = SMART_UNSTUCK_CFG.enemy_detection_range
        SMART_UNSTUCK_CFG.enemy_detection_range = new_enemy_range
        _log(
            f"stuck.cfg_reload enemy_detection_range "
            f"{old:.1f}->{new_enemy_range:.1f} force={force_reload}"
        )
    if new_sample_count != SMART_UNSTUCK_CFG.stuck_sample_count or force_reload:
        old_int = SMART_UNSTUCK_CFG.stuck_sample_count
        SMART_UNSTUCK_CFG.stuck_sample_count = new_sample_count
        _log(f"stuck.cfg_reload stuck_sample_count {old_int}->{new_sample_count} force={force_reload}")
    if abs(new_min_distance - SMART_UNSTUCK_CFG.min_distance_activate_unstuck) > 0.01 or force_reload:
        old = SMART_UNSTUCK_CFG.min_distance_activate_unstuck
        SMART_UNSTUCK_CFG.min_distance_activate_unstuck = new_min_distance
        _log(f"stuck.cfg_reload min_distance_activate_unstuck {old:.1f}->{new_min_distance:.1f} force={force_reload}")
    if abs(new_move_units - SMART_UNSTUCK_CFG.no_progress_move_units) > 0.01 or force_reload:
        old = SMART_UNSTUCK_CFG.no_progress_move_units
        SMART_UNSTUCK_CFG.no_progress_move_units = new_move_units
        _log(f"stuck.cfg_reload no_progress_move_units {old:.1f}->{new_move_units:.1f} force={force_reload}")
    if abs(new_close_units - SMART_UNSTUCK_CFG.no_progress_close_units) > 0.01 or force_reload:
        old = SMART_UNSTUCK_CFG.no_progress_close_units
        SMART_UNSTUCK_CFG.no_progress_close_units = new_close_units
        _log(f"stuck.cfg_reload no_progress_close_units {old:.1f}->{new_close_units:.1f} force={force_reload}")
    if new_overlay != hero_globals.show_followers_unstuck_overlay or force_reload:
        old_bool = hero_globals.show_followers_unstuck_overlay
        hero_globals.show_followers_unstuck_overlay = new_overlay
        _log(f"stuck.cfg_reload show_followers_unstuck_overlay {old_bool}->{new_overlay} force={force_reload}")
    if abs(new_early_exit - SMART_UNSTUCK_CFG.obstacle_cleared_delta) > 0.01 or force_reload:
        old = SMART_UNSTUCK_CFG.obstacle_cleared_delta
        SMART_UNSTUCK_CFG.obstacle_cleared_delta = new_early_exit
        _log(f"stuck.cfg_reload obstacle_cleared_delta {old:.1f}->{new_early_exit:.1f} force={force_reload}")


def _now_ms() -> int:
    return int(Py4GW.Game.get_tick_count64())


def _log(message: str) -> None:
    # Gated on the "Draw Followers Unstuck (3D)" toggle so the console stays
    # quiet during normal play. Verbose per-tick / per-sample lines remain
    # gated by hero_globals.show_stuck_avoidance_debug on top of this.
    if not hero_globals.show_followers_unstuck_overlay:
        return
    try:
        Py4GW.Console.Log("HeroAI", message, Py4GW.Console.MessageType.Notice)
    except Exception:
        pass


def _log_first_call_once() -> None:
    global _first_call_logged
    if _first_call_logged:
        return
    # Gated on the "Draw Followers Unstuck (3D)" toggle — same policy as _log.
    if not hero_globals.show_followers_unstuck_overlay:
        return
    _first_call_logged = True
    try:
        Py4GW.Console.Log(
            "HeroAI",
            "smart_unstuck: first follower tick reached (module loaded and update_smart_unstuck is being called)",
            Py4GW.Console.MessageType.Success,
        )
    except Exception:
        pass


def _get_navmesh():
    autopath = AutoPathing()
    nav = autopath.get_navmesh()
    if nav is not None:
        return nav
    try:
        for _ in autopath.load_pathing_maps():
            pass
    except Exception:
        return None
    return autopath.get_navmesh()


def _resolve_navmesh_position(
    navmesh,
    x: float,
    y: float,
    cfg: SmartUnstuckConfig,
) -> tuple[float, float] | None:
    """Resolve an ideal waypoint (x, y) to a reachable navmesh position.

    Returns the original point if it's already on the navmesh (within margin),
    the nearest-reachable snap if within navmesh_snap_tolerance, or None when
    no reachable position exists nearby. None means: don't place a waypoint
    here, the follower can't go there.
    """
    if navmesh is None:
        return (x, y)  # graceful degradation when pathing maps unavailable
    try:
        if navmesh.contains(x, y, cfg.navmesh_contains_margin):
            return (x, y)
        snapped = navmesh.find_nearest_reachable((x, y))
        if snapped is not None:
            sx, sy = float(snapped[0]), float(snapped[1])
            if math.hypot(sx - x, sy - y) <= cfg.navmesh_snap_tolerance:
                return (sx, sy)
    except Exception:
        return (x, y)
    return None


def _segment_walkable_on_navmesh(
    a: tuple[float, float],
    b: tuple[float, float],
    navmesh,
    sample_spacing: float,
    margin: float,
) -> bool:
    """Probe the straight line from `a` to `b` at `sample_spacing` intervals
    and verify each interior sample sits on the navmesh.

    Answers "is this segment between two waypoints actually walkable?" — a
    per-point navmesh check on the endpoints alone misses the case where the
    line in between crosses non-walkable terrain (e.g. props between two
    enemy-circle boundary points). Returns True for an unbroken walkable
    segment, False if any interior sample fails. Graceful when navmesh is None
    (returns True so the system degrades to point-only checks).
    """
    if navmesh is None:
        return True
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 1.0:
        return True
    n_samples = max(1, int(math.ceil(length / max(1.0, sample_spacing))))
    for k in range(1, n_samples):
        t = float(k) / float(n_samples)
        x = a[0] + (t * dx)
        y = a[1] + (t * dy)
        try:
            if not navmesh.contains(x, y, margin):
                return False
        except Exception:
            return False
    return True


def _generate_arc_waypoints(
    current_xy: tuple[float, float],
    follow_xy: tuple[float, float],
    cfg: SmartUnstuckConfig,
    side: int,
    navmesh=None,
) -> tuple[tuple[float, float], tuple[tuple[float, float], ...], int]:
    fx, fy = current_xy
    tx, ty = follow_xy
    forward = math.atan2(ty - fy, tx - fx)
    r = cfg.touch_radius
    cx = fx + (r * math.cos(forward))
    cy = fy + (r * math.sin(forward))
    step = cfg.arc_span_rad / float(2 * max(1, cfg.waypoint_count))
    waypoints: list[tuple[float, float]] = []
    for i in range(cfg.waypoint_count):
        k = (2 * i) + 1
        theta = forward + math.pi + (side * k * step)
        ideal_x = cx + (r * math.cos(theta))
        ideal_y = cy + (r * math.sin(theta))
        resolved = _resolve_navmesh_position(navmesh, ideal_x, ideal_y, cfg)
        if resolved is not None:
            waypoints.append(resolved)
    return ((cx, cy), tuple(waypoints), cfg.waypoint_count)


def _get_enemies_in_range(
    current_xy: tuple[float, float],
    range_units: float,
) -> tuple[tuple[float, float], ...]:
    """Return live enemy (x, y) positions within `range_units`, closest first."""
    if range_units <= 0:
        return ()
    try:
        ids = AgentArray.GetEnemyArray()
    except Exception:
        return ()
    ids = AgentArray.Filter.ByCondition(
        ids,
        lambda aid: Agent.IsValid(int(aid)) and not Agent.IsDead(int(aid)),
    )
    ids = AgentArray.Filter.ByDistance(ids, current_xy, float(range_units))
    ids = AgentArray.Sort.ByDistance(ids, current_xy)
    out: list[tuple[float, float]] = []
    for aid in ids:
        try:
            pos = Agent.GetXY(int(aid))
        except Exception:
            continue
        if pos is None:
            continue
        x, y = float(pos[0]), float(pos[1])
        if abs(x) < 0.001 and abs(y) < 0.001:
            continue
        out.append((x, y))
    return tuple(out)


# Slalom tuning: 1° boundary samples (~2.5u apart at radius 144); waypoints
# emitted every ~80u of arc length.
_BOUNDARY_RESOLUTION_DEG: float = 1.0
_WAYPOINT_SPACING_UNITS: float = 80.0


def _cluster_enemy_indices(
    enemies: tuple[tuple[float, float], ...],
    cfg: SmartUnstuckConfig,
) -> tuple[tuple[int, ...], ...]:
    """Group enemies whose touch_radius circles overlap. Returns one tuple of
    indices per cluster (indices reference the input sequence)."""
    r = float(cfg.touch_radius)
    n = len(enemies)
    if n == 0:
        return ()
    parent = list(range(n))

    def find(i: int) -> int:
        root = i
        while parent[root] != root:
            root = parent[root]
        while parent[i] != root:
            parent[i], i = root, parent[i]
        return root

    threshold_sq = (2.0 * r) * (2.0 * r)
    for i in range(n):
        for j in range(i + 1, n):
            dx = enemies[i][0] - enemies[j][0]
            dy = enemies[i][1] - enemies[j][1]
            if (dx * dx + dy * dy) < threshold_sq:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return tuple(tuple(g) for g in groups.values())


def _build_union_boundary(
    member_circles: tuple[tuple[tuple[float, float], float], ...],
) -> tuple[tuple[float, float], ...]:
    """Outer outline of the union of member circles, sampled by ray-casting
    from the centroid (one ray per `_BOUNDARY_RESOLUTION_DEG`).

    Each ray returns the farthest ray-circle hit across all members — overlap
    regions disappear because the ray exits at the outermost circle's edge.

    Returns a closed CCW polyline around the centroid; first point is not
    duplicated at the end. Assumes star-shaped from the centroid (holds for
    clustered touch-radius circles where centers sit inside the union).
    """
    if not member_circles:
        return ()
    cx_total = sum(mc[0][0] for mc in member_circles) / len(member_circles)
    cy_total = sum(mc[0][1] for mc in member_circles) / len(member_circles)
    centroid = (cx_total, cy_total)
    n_samples = max(8, int(round(360.0 / _BOUNDARY_RESOLUTION_DEG)))
    polyline: list[tuple[float, float]] = []
    for k in range(n_samples):
        theta = 2.0 * math.pi * k / n_samples
        ray_dx = math.cos(theta)
        ray_dy = math.sin(theta)
        max_t = 0.0
        for (cc, cr) in member_circles:
            ex = centroid[0] - cc[0]
            ey = centroid[1] - cc[1]
            # ray_dir is unit, so quadratic in t has a==1
            b = 2.0 * ((ex * ray_dx) + (ey * ray_dy))
            c = (ex * ex) + (ey * ey) - (cr * cr)
            disc = (b * b) - (4.0 * c)
            if disc < 0:
                continue
            sqrt_disc = math.sqrt(disc)
            t_far = (-b + sqrt_disc) / 2.0
            if t_far > max_t:
                max_t = t_far
        if max_t > 0:
            polyline.append((centroid[0] + max_t * ray_dx, centroid[1] + max_t * ray_dy))
    return tuple(polyline)


def _find_boundary_tangent_indices(
    point: tuple[float, float],
    boundary: tuple[tuple[float, float], ...],
) -> tuple[int, int] | None:
    """Return (ccw_idx, cw_idx) of the boundary samples that form the tangent
    from an external `point` — the extremal angular directions, normalized
    around the boundary centroid to avoid wrap. Exact for convex unions; tight
    approximation for the near-convex peanut shapes from clustered circles.
    """
    n = len(boundary)
    if n == 0:
        return None
    px, py = point
    bx = sum(b[0] for b in boundary) / n
    by = sum(b[1] for b in boundary) / n
    base = math.atan2(by - py, bx - px)
    ccw_best_angle = float("-inf")
    cw_best_angle = float("inf")
    ccw_idx = 0
    cw_idx = 0
    for i, b in enumerate(boundary):
        a = math.atan2(b[1] - py, b[0] - px)
        while (a - base) >= math.pi:
            a -= 2.0 * math.pi
        while (a - base) < -math.pi:
            a += 2.0 * math.pi
        if a > ccw_best_angle:
            ccw_best_angle = a
            ccw_idx = i
        if a < cw_best_angle:
            cw_best_angle = a
            cw_idx = i
    return ccw_idx, cw_idx


def _walk_boundary_directed(
    boundary: tuple[tuple[float, float], ...],
    entry_idx: int,
    exit_idx: int,
    arc_direction: int,
) -> tuple[tuple[float, float], ...]:
    """Walk the closed `boundary` from entry_idx to exit_idx in the given
    direction (+1 CCW / increasing index, -1 CW / decreasing). Endpoints
    included; wraps modulo n."""
    n = len(boundary)
    if n == 0:
        return ()
    walk: list[tuple[float, float]] = [boundary[entry_idx]]
    if entry_idx == exit_idx:
        return tuple(walk)
    step = 1 if arc_direction > 0 else -1
    i = entry_idx
    for _ in range(n):
        i = (i + step) % n
        walk.append(boundary[i])
        if i == exit_idx:
            break
    return tuple(walk)


def _build_navmesh_aware_waypoints_with_segments(
    walk: tuple[tuple[float, float], ...],
    cfg: SmartUnstuckConfig,
    navmesh,
    target_spacing: float,
) -> tuple[tuple[tuple[float, float], ...], int, int]:
    """Emit waypoints at uniform arc-length intervals along the boundary,
    each navmesh-snapped and segment-validated against the previous emit.

    Spacing = total_length / ceil(total_length / target_spacing), so it's
    slightly <= target_spacing and never larger. Snap or segment failures
    drop the candidate; gaps between emitted waypoints are always an exact
    multiple of `actual_spacing`, never wider.

    Returns (waypoints, n_failed_segments, n_dropped_candidates).
    """
    if len(walk) < 2:
        return (), 0, 0
    cum: list[float] = [0.0]
    for k in range(1, len(walk)):
        d = math.hypot(walk[k][0] - walk[k - 1][0], walk[k][1] - walk[k - 1][1])
        cum.append(cum[-1] + d)
    total = cum[-1]
    if total < 1.0:
        return (), 0, 0
    n_intervals = max(1, int(math.ceil(total / max(1.0, target_spacing))))
    actual_spacing = total / n_intervals
    segment_sample_spacing = max(20.0, actual_spacing / 4.0)
    waypoints: list[tuple[float, float]] = []
    failed_segs = 0
    dropped_candidates = 0
    walk_idx = 0
    for i in range(n_intervals + 1):
        target_dist = actual_spacing * i if i < n_intervals else total
        while walk_idx < len(walk) - 1 and cum[walk_idx + 1] < target_dist:
            walk_idx += 1
        if walk_idx >= len(walk) - 1:
            ideal_x, ideal_y = walk[-1]
        else:
            seg_a = cum[walk_idx]
            seg_b = cum[walk_idx + 1]
            if seg_b > seg_a:
                alpha = (target_dist - seg_a) / (seg_b - seg_a)
            else:
                alpha = 0.0
            ideal_x = walk[walk_idx][0] + alpha * (walk[walk_idx + 1][0] - walk[walk_idx][0])
            ideal_y = walk[walk_idx][1] + alpha * (walk[walk_idx + 1][1] - walk[walk_idx][1])
        resolved = _resolve_navmesh_position(navmesh, ideal_x, ideal_y, cfg)
        if resolved is None:
            dropped_candidates += 1
            continue
        if waypoints and not _segment_walkable_on_navmesh(
            waypoints[-1],
            resolved,
            navmesh,
            sample_spacing=segment_sample_spacing,
            margin=cfg.navmesh_contains_margin,
        ):
            failed_segs += 1
            continue
        waypoints.append(resolved)
    return tuple(waypoints), failed_segs, dropped_candidates


def _build_path_for_side(
    boundary: tuple[tuple[float, float], ...],
    tan_current: tuple[int, int],
    tan_follow: tuple[int, int],
    arc_dir: int,
    cfg: SmartUnstuckConfig,
    navmesh,
) -> tuple[tuple[tuple[float, float], ...], int, int]:
    """Walk one side (CCW or CW) of a cluster boundary from current's tangent
    to follow's tangent and emit waypoints. Returns (waypoints, failed_segments,
    dropped_candidates) — see `_build_navmesh_aware_waypoints_with_segments`.
    """
    if arc_dir > 0:
        entry_idx = tan_current[1]
        exit_idx = tan_follow[0]
    else:
        entry_idx = tan_current[0]
        exit_idx = tan_follow[1]
    walk = _walk_boundary_directed(boundary, entry_idx, exit_idx, arc_dir)
    if len(walk) < 2:
        return (), 0, 0
    return _build_navmesh_aware_waypoints_with_segments(
        walk, cfg, navmesh, _WAYPOINT_SPACING_UNITS
    )


def _path_length(path: tuple[tuple[float, float], ...]) -> float:
    if len(path) < 2:
        return 0.0
    total = 0.0
    for i in range(len(path) - 1):
        total += math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
    return total


def _segment_circle_blocks(
    seg_start: tuple[float, float],
    seg_end: tuple[float, float],
    center: tuple[float, float],
    radius: float,
    margin: float = 0.0,
) -> bool:
    """True iff the segment passes within radius+margin of `center`."""
    sx, sy = seg_start
    ex, ey = seg_end
    cx, cy = center
    dx = ex - sx
    dy = ey - sy
    seg_len_sq = (dx * dx) + (dy * dy)
    if seg_len_sq < 1e-6:
        return math.hypot(cx - sx, cy - sy) < (radius + margin)
    t = (((cx - sx) * dx) + ((cy - sy) * dy)) / seg_len_sq
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    closest_x = sx + (t * dx)
    closest_y = sy + (t * dy)
    return math.hypot(cx - closest_x, cy - closest_y) < (radius + margin)


def _cluster_blocks_segment(
    seg_start: tuple[float, float],
    seg_end: tuple[float, float],
    member_circles: tuple[tuple[tuple[float, float], float], ...],
) -> bool:
    """True iff the segment is blocked by ANY member circle of the cluster."""
    for (cc, cr) in member_circles:
        if _segment_circle_blocks(seg_start, seg_end, cc, cr):
            return True
    return False


def _cluster_centroid(
    member_circles: tuple[tuple[tuple[float, float], float], ...],
) -> tuple[float, float]:
    n = len(member_circles)
    cx = sum(mc[0][0] for mc in member_circles) / n
    cy = sum(mc[0][1] for mc in member_circles) / n
    return (cx, cy)


def _generate_slalom_waypoints(
    current_xy: tuple[float, float],
    follow_xy: tuple[float, float],
    enemies: tuple[tuple[float, float], ...],
    cfg: SmartUnstuckConfig,
    navmesh,
) -> tuple[
    tuple[tuple[float, float], ...],
    tuple[tuple[float, float], ...],
    tuple[int, ...],
    int,
    tuple[tuple[tuple[float, float], ...], ...],
]:
    """Build a slalom path that walks the outer outline of overlapping enemy
    clusters from current_xy toward follow_xy.

    Returns (waypoints, render_centers, arc_directions, abort_idx, boundaries).

    Per iteration: pick the closest cluster (by projection along current→goal)
    whose union still blocks the direct segment; build its union outline; probe
    BOTH sides via tangent-walk; pick the fully-walkable shorter one (or the
    least-failed if neither is fully walkable). Repeat until no cluster blocks.

    abort_idx = path index of the waypoint nearest follow_xy. render_centers
    are raw enemy positions (one per accepted enemy) for overlay rendering.
    boundaries are one closed polyline per accepted cluster.
    """
    if not enemies:
        return (), (), (), -1, ()
    r = float(cfg.touch_radius)
    cluster_groups = _cluster_enemy_indices(enemies, cfg)
    if not cluster_groups:
        return (), (), (), -1, ()
    member_circles_per_cluster: list[tuple[tuple[tuple[float, float], float], ...]] = []
    member_enemy_pos_per_cluster: list[tuple[tuple[float, float], ...]] = []
    for idx_group in cluster_groups:
        member_circles_per_cluster.append(tuple((enemies[i], r) for i in idx_group))
        member_enemy_pos_per_cluster.append(tuple(enemies[i] for i in idx_group))
    gx, gy = float(follow_xy[0]), float(follow_xy[1])
    waypoints: list[tuple[float, float]] = []
    arc_directions: list[int] = []
    accepted_enemy_positions: list[tuple[float, float]] = []
    accepted_boundaries: list[tuple[tuple[float, float], ...]] = []
    current = (float(current_xy[0]), float(current_xy[1]))
    remaining_idx = list(range(len(member_circles_per_cluster)))
    safety_cap = len(remaining_idx)
    iterations = 0
    while iterations < safety_cap and remaining_idx:
        iterations += 1
        sx, sy = current
        sg_x = gx - sx
        sg_y = gy - sy
        sg_len_sq = (sg_x * sg_x) + (sg_y * sg_y)
        sg_len = math.sqrt(sg_len_sq) if sg_len_sq > 1e-6 else 0.0
        best: tuple[float, int] | None = None
        for list_pos, ci in enumerate(remaining_idx):
            mc = member_circles_per_cluster[ci]
            if not _cluster_blocks_segment(current, follow_xy, mc):
                continue
            cent = _cluster_centroid(mc)
            if sg_len < 1e-6:
                proj = math.hypot(cent[0] - sx, cent[1] - sy)
            else:
                proj = (((cent[0] - sx) * sg_x) + ((cent[1] - sy) * sg_y)) / sg_len
            if proj < 0:
                continue
            if best is None or proj < best[0]:
                best = (proj, list_pos)
        if best is None:
            break
        list_pos = best[1]
        cluster_idx = remaining_idx[list_pos]
        mc = member_circles_per_cluster[cluster_idx]
        boundary = _build_union_boundary(mc)
        if not boundary:
            remaining_idx.pop(list_pos)
            continue
        tan_current = _find_boundary_tangent_indices(current, boundary)
        tan_follow = _find_boundary_tangent_indices(follow_xy, boundary)
        if tan_current is None or tan_follow is None:
            remaining_idx.pop(list_pos)
            continue
        # Probe both sides; each entry: (arc_dir, waypoints, failed_segs, dropped, path_len).
        side_results: list[tuple[int, tuple[tuple[float, float], ...], int, int, float]] = []
        for arc_dir_candidate in (1, -1):
            wps, n_failed, n_dropped = _build_path_for_side(
                boundary, tan_current, tan_follow, arc_dir_candidate, cfg, navmesh
            )
            if len(wps) < 2:
                if hero_globals.show_stuck_avoidance_debug:
                    _log(
                        f"stuck.slalom.probe arc_dir={arc_dir_candidate} "
                        f"waypoints={len(wps)} failed_segs={n_failed} "
                        f"dropped={n_dropped} -> reject (too few)"
                    )
                continue
            length = _path_length(wps)
            side_results.append((arc_dir_candidate, wps, n_failed, n_dropped, length))
            if hero_globals.show_stuck_avoidance_debug:
                _log(
                    f"stuck.slalom.probe arc_dir={arc_dir_candidate} "
                    f"waypoints={len(wps)} failed_segs={n_failed} "
                    f"dropped={n_dropped} path_len={length:.0f}"
                )
        if not side_results:
            remaining_idx.pop(list_pos)
            continue
        # Prefer fully-walkable shorter; fall back to least-failed when neither
        # side is clean (better an imperfect detour than staying stuck).
        fully_walkable = [s for s in side_results if s[2] == 0]
        if fully_walkable:
            fully_walkable.sort(key=lambda s: s[4])
            chosen = fully_walkable[0]
            fallback_used = False
        else:
            side_results.sort(key=lambda s: (s[2], s[4]))
            chosen = side_results[0]
            fallback_used = True
        chosen_arc_dir = chosen[0]
        chosen_wps = chosen[1]
        chosen_failed = chosen[2]
        chosen_len = chosen[4]
        if hero_globals.show_stuck_avoidance_debug:
            _log(
                f"stuck.slalom.cluster_chosen arc_dir={chosen_arc_dir} "
                f"waypoints={len(chosen_wps)} path_len={chosen_len:.0f} "
                f"failed_segs={chosen_failed} fallback={fallback_used} "
                f"fully_walkable_sides={len(fully_walkable)}/{len(side_results)}"
            )
        waypoints.extend(chosen_wps)
        arc_directions.append(chosen_arc_dir)
        accepted_enemy_positions.extend(member_enemy_pos_per_cluster[cluster_idx])
        accepted_boundaries.append(boundary)
        current = chosen_wps[-1]
        remaining_idx.pop(list_pos)
    if not waypoints:
        return (), (), (), -1, ()
    abort_idx = -1
    best_dist = float("inf")
    for i, wp in enumerate(waypoints):
        d = math.hypot(wp[0] - gx, wp[1] - gy)
        if d < best_dist - 1e-3:
            best_dist = d
            abort_idx = i
    return (
        tuple(waypoints),
        tuple(accepted_enemy_positions),
        tuple(arc_directions),
        abort_idx,
        tuple(accepted_boundaries),
    )


def _publish_debug_snapshot(state: SmartUnstuckState, cfg: SmartUnstuckConfig) -> None:
    if state.mode == "idle":
        hero_globals.smart_unstuck_debug_snapshot = None
        return
    # `circles`: one center for front-of-follower mode, N for slalom.
    # `circle_center` retained alongside for the legacy single-center reader.
    if state.slalom_centers:
        circles: tuple[tuple[float, float], ...] = state.slalom_centers
    elif state.circle_center is not None:
        circles = (state.circle_center,)
    else:
        circles = ()
    hero_globals.smart_unstuck_debug_snapshot = {
        "mode": state.mode,
        "circle_center": state.circle_center,
        "circles": circles,
        # One closed polyline per cluster — drawn as a line strip so the
        # merged peanut shape is visible instead of separate rings.
        "union_boundaries": state.slalom_union_boundaries,
        "radius": cfg.touch_radius,
        "waypoints": state.waypoints,
        "current_idx": state.waypoint_idx,
        "touch_radius": _OVERLAY_TOUCH_RADIUS,
    }


def reset_smart_unstuck(state: SmartUnstuckState) -> None:
    state.mode = "idle"
    state.prev_sample_xy = None
    state.prev_sample_dist = None
    state.no_progress_samples = 0
    state.waypoints = ()
    state.waypoint_idx = 0
    state.detour_started_ms = 0
    state.waypoint_started_ms = 0
    state.detour_start_dist = 0.0
    state.circle_center = None
    state.slalom_centers = ()
    state.slalom_union_boundaries = ()
    state.abort_waypoint_idx = -1
    state.sides_tried.clear()
    state.detour_tree = None
    state.tick_count = 0
    state.last_tick_ms = 0
    state.last_tick_xy = None
    state.waypoint_enter_ms = 0
    hero_globals.smart_unstuck_debug_snapshot = None


def _log_detour_init(
    state: SmartUnstuckState,
    cfg: SmartUnstuckConfig,
    current_xy: tuple[float, float],
    follow_xy: tuple[float, float],
    side: int,
    center: tuple[float, float],
    wps: tuple[tuple[float, float], ...],
) -> None:
    if not hero_globals.show_stuck_avoidance_debug:
        return
    _log(
        f"stuck.detour_init "
        f"side={side} "
        f"start_pos=({current_xy[0]:.0f},{current_xy[1]:.0f}) "
        f"follow_xy=({follow_xy[0]:.0f},{follow_xy[1]:.0f}) "
        f"center=({center[0]:.0f},{center[1]:.0f}) "
        f"wp_count={len(wps)}"
    )
    _log(
        f"stuck.detour_init.bt_params "
        f"waypoint_smoothing={cfg.waypoint_smoothing} "
        f"timeout_ms=15000(BT_default) "
        f"stall_threshold_ms=500(BT_default) "
        f"pause_on_combat=True(BT_default)"
    )
    _log(
        f"stuck.detour_init.cfg "
        f"touch_radius={cfg.touch_radius} "
        f"waypoint_count={cfg.waypoint_count} "
        f"arc_span_rad={cfg.arc_span_rad:.4f} "
        f"total_detour_timeout_ms={cfg.total_detour_timeout_ms} "
        f"obstacle_cleared_delta={cfg.obstacle_cleared_delta} "
        f"navmesh_contains_margin={cfg.navmesh_contains_margin} "
        f"navmesh_snap_tolerance={cfg.navmesh_snap_tolerance} "
        f"arc_walkability_required_fraction={cfg.arc_walkability_required_fraction}"
    )
    for i, wp in enumerate(wps):
        dist_from_start = Utils.Distance(current_xy, wp)
        dist_to_next = (
            Utils.Distance(wp, wps[i + 1]) if (i + 1) < len(wps) else -1.0
        )
        _log(
            f"stuck.wp[{i}] pos=({wp[0]:.0f},{wp[1]:.0f}) "
            f"dist_from_start={dist_from_start:.0f} "
            f"dist_to_next={dist_to_next:.0f}"
        )


def _log_tick_detail(
    state: SmartUnstuckState,
    current_xy: tuple[float, float],
    dist_to_follow: float,
    now_ms: int,
    bt_result: BehaviorTree.NodeState | None,
) -> None:
    if not hero_globals.show_stuck_avoidance_debug or state.detour_tree is None:
        return
    detour_elapsed_ms = now_ms - state.detour_started_ms
    if state.last_tick_ms > 0 and state.last_tick_xy is not None:
        dt_ms = now_ms - state.last_tick_ms
        dist_moved = Utils.Distance(state.last_tick_xy, current_xy)
    else:
        dt_ms = 0
        dist_moved = 0.0
    speed = (dist_moved / dt_ms * 1000.0) if dt_ms > 0 else 0.0

    wp_dist = -1.0
    next_wp_dist = -1.0
    cur_wp_str = "(none)"
    if 0 <= state.waypoint_idx < len(state.waypoints):
        cur_wp = state.waypoints[state.waypoint_idx]
        cur_wp_str = f"({cur_wp[0]:.0f},{cur_wp[1]:.0f})"
        wp_dist = Utils.Distance(current_xy, cur_wp)
        next_idx = state.waypoint_idx + 1
        if next_idx < len(state.waypoints):
            next_wp_dist = Utils.Distance(current_xy, state.waypoints[next_idx])

    bb = state.detour_tree.blackboard
    last_move = bb.get("move_last_move_point", None)
    last_move_str = f"({last_move[0]:.0f},{last_move[1]:.0f})" if last_move else "(none)"
    result_str = bt_result.name if bt_result is not None else "None"

    _log(
        f"stuck.tick "
        f"#{state.tick_count} "
        f"t={detour_elapsed_ms}ms "
        f"dt={dt_ms}ms "
        f"pos=({current_xy[0]:.0f},{current_xy[1]:.0f}) "
        f"speed={speed:.1f}u/s "
        f"moved={dist_moved:.1f}u "
        f"wp_idx={state.waypoint_idx}/{len(state.waypoints)} "
        f"wp={cur_wp_str} "
        f"wp_dist={wp_dist:.0f} "
        f"next_wp_dist={next_wp_dist:.0f} "
        f"dist_to_follow={dist_to_follow:.0f} "
        f"bt_state={bb.get('move_state', '?')} "
        f"bt_reason={bb.get('move_reason', '')} "
        f"last_move={last_move_str} "
        f"stall_retries={bb.get('move_stall_retry_count', 0)} "
        f"strafe_active={bb.get('move_strafe_active', False)} "
        f"strafe_side={bb.get('move_strafe_side', '')} "
        f"strafe_phase={bb.get('move_strafe_phase', 0)} "
        f"recovery={bb.get('move_resume_recovery_active', False)} "
        f"recovery_reason={bb.get('move_resume_recovery_reason', '')} "
        f"pause_reason={bb.get('move_current_pause_reason', '')} "
        f"result={result_str}"
    )


def _log_waypoint_advance(
    state: SmartUnstuckState,
    new_idx: int,
    now_ms: int,
    current_xy: tuple[float, float],
) -> None:
    if not hero_globals.show_stuck_avoidance_debug:
        return
    old_idx = state.waypoint_idx
    wp_time_ms = now_ms - state.waypoint_enter_ms if state.waypoint_enter_ms > 0 else 0
    seg_distance = 0.0
    if 0 <= old_idx < len(state.waypoints) and 0 <= new_idx < len(state.waypoints):
        seg_distance = Utils.Distance(state.waypoints[old_idx], state.waypoints[new_idx])
    seg_speed = (seg_distance / wp_time_ms * 1000.0) if wp_time_ms > 0 else 0.0
    dist_to_new_wp = -1.0
    if 0 <= new_idx < len(state.waypoints):
        dist_to_new_wp = Utils.Distance(current_xy, state.waypoints[new_idx])
    _log(
        f"stuck.advance "
        f"from={old_idx} to={new_idx} "
        f"time_on_prev_wp_ms={wp_time_ms} "
        f"seg_dist={seg_distance:.0f}u "
        f"avg_seg_speed={seg_speed:.1f}u/s "
        f"dist_to_new_wp={dist_to_new_wp:.0f}u"
    )


def _build_detour_tree(
    waypoints: tuple[tuple[float, float], ...],
    cfg: SmartUnstuckConfig,
) -> BehaviorTree | None:
    """Build the BT.Movement.MoveDirect tree that walks `waypoints`. The
    tolerance value is captured from cfg at construction; subsequent slider
    changes apply to the next detour, not the in-flight one.
    """
    if not waypoints:
        return None
    return BT.Movement.MoveDirect(
        path_points=[Vec2f(float(x), float(y)) for (x, y) in waypoints],
        tolerance=max(1.0, float(cfg.waypoint_smoothing)),
        log=hero_globals.show_stuck_avoidance_debug,
    )


def _tick_tree_safe(tree: BehaviorTree | None) -> BehaviorTree.NodeState | None:
    if tree is None:
        return None
    try:
        return tree.tick()
    except Exception as exc:
        _log(f"stuck.bt_tick_exception: {exc!r}")
        return BehaviorTree.NodeState.FAILURE


def _enter_detour(
    state: SmartUnstuckState,
    cfg: SmartUnstuckConfig,
    current_xy: tuple[float, float],
    follow_xy: tuple[float, float],
    dist_to_follow: float,
) -> None:
    """Build the detour path, install it on `state`, and fire BT.Move once so
    the first Player.Move issues this frame.

    Slalom mode (preferred): when any enemy is within enemy_detection_range,
    route around the welded union outlines via tangent walking on the cluster
    boundaries. Falls through to single-circle mode if every cluster fails to
    yield a usable arc.

    Single-circle mode (fallback): half-arc around an imaginary obstacle one
    touch_radius ahead, with the follower at the circle's 6 o'clock.

    On total failure (no walkable side), resets state and returns to idle.
    """
    navmesh = _get_navmesh()
    enemies = _get_enemies_in_range(current_xy, cfg.enemy_detection_range)
    if enemies:
        (
            slalom_waypoints,
            accepted_centers,
            arc_directions,
            abort_idx,
            union_boundaries,
        ) = _generate_slalom_waypoints(current_xy, follow_xy, enemies, cfg, navmesh)
        if slalom_waypoints and accepted_centers:
            state.mode = "detouring"
            state.circle_center = accepted_centers[0]
            state.slalom_centers = accepted_centers
            state.slalom_union_boundaries = union_boundaries
            state.waypoints = slalom_waypoints
            state.waypoint_idx = 0
            state.abort_waypoint_idx = abort_idx
            now = _now_ms()
            state.detour_started_ms = now
            state.waypoint_started_ms = now
            state.detour_start_dist = dist_to_follow
            state.sides_tried.clear()
            state.detour_tree = _build_detour_tree(slalom_waypoints, cfg)
            state.tick_count = 0
            state.last_tick_ms = 0
            state.last_tick_xy = None
            state.waypoint_enter_ms = now
            _log(
                f"stuck.detour start mode=slalom enemies={len(accepted_centers)} "
                f"clusters={len(arc_directions)} waypoints={len(slalom_waypoints)} "
                f"abort_idx={abort_idx} arc_dirs={list(arc_directions)} "
                f"dist={dist_to_follow:.0f} waypoint_smoothing={cfg.waypoint_smoothing:.1f} "
                f"radius={cfg.touch_radius:.0f}"
            )
            if hero_globals.show_stuck_avoidance_debug:
                for i, ec in enumerate(accepted_centers):
                    _log(
                        f"stuck.slalom.enemy[{i}] pos=({ec[0]:.0f},{ec[1]:.0f})"
                    )
                _log_detour_init(
                    state, cfg, current_xy, follow_xy, 0, accepted_centers[0], slalom_waypoints
                )
            # Tick once now so Player.Move(first_waypoint) goes out this frame
            # rather than waiting for the next update_smart_unstuck call.
            first_result = _tick_tree_safe(state.detour_tree)
            state.tick_count += 1
            state.last_tick_ms = _now_ms()
            state.last_tick_xy = current_xy
            if state.detour_tree is not None:
                bb_idx = state.detour_tree.blackboard.get("move_current_waypoint_index", -1)
                if isinstance(bb_idx, int) and bb_idx >= 0 and bb_idx != state.waypoint_idx:
                    _log_waypoint_advance(state, bb_idx, state.last_tick_ms, current_xy)
                    state.waypoint_idx = bb_idx
                    state.waypoint_enter_ms = state.last_tick_ms
            _log_tick_detail(state, current_xy, dist_to_follow, state.last_tick_ms, first_result)
            return
        # Enemies present but slalom yielded nothing walkable — fall through
        # to the single-circle path.
        if hero_globals.show_stuck_avoidance_debug:
            _log(
                f"stuck.slalom.empty enemies_in_range={len(enemies)} "
                f"-> falling back to front-of-follower circle"
            )

    candidates: list[tuple[int, tuple[float, float], tuple[tuple[float, float], ...], bool]] = []
    for side in (-1, 1):
        if side in state.sides_tried:
            continue
        center, wps, total = _generate_arc_waypoints(current_xy, follow_xy, cfg, side, navmesh=navmesh)
        walkable_count = len(wps)
        is_walkable = total > 0 and (walkable_count / total) >= cfg.arc_walkability_required_fraction
        if hero_globals.show_stuck_avoidance_debug:
            first_wp_str = f"first_wp=({wps[0][0]:.0f},{wps[0][1]:.0f})" if wps else "first_wp=(none)"
            _log(
                f"stuck.probe side={side} walkable={walkable_count}/{total} "
                f"required>={cfg.arc_walkability_required_fraction:.0%} accepted={is_walkable} "
                f"{first_wp_str} center=({center[0]:.0f},{center[1]:.0f})"
            )
        candidates.append((side, center, wps, is_walkable))

    walkable_candidates = [c for c in candidates if c[3]]
    if not walkable_candidates:
        _log("stuck.no_walkable_side -> idle")
        reset_smart_unstuck(state)
        return

    if len(walkable_candidates) == 2:
        chosen = next(
            (c for c in walkable_candidates if c[0] == cfg.preferred_side_when_both_walkable),
            walkable_candidates[0],
        )
    else:
        chosen = walkable_candidates[0]

    side, center, wps, _ = chosen
    state.mode = "detouring"
    state.circle_center = center
    state.slalom_centers = ()
    state.waypoints = wps
    state.waypoint_idx = 0
    now = _now_ms()
    state.detour_started_ms = now
    state.waypoint_started_ms = now
    state.detour_start_dist = dist_to_follow
    state.sides_tried.add(side)
    state.detour_tree = _build_detour_tree(wps, cfg)
    state.tick_count = 0
    state.last_tick_ms = 0
    state.last_tick_xy = None
    state.waypoint_enter_ms = now
    _log(
        f"stuck.detour start mode=single side={side} center=({center[0]:.0f},{center[1]:.0f}) "
        f"dist={dist_to_follow:.0f} waypoints={len(wps)} waypoint_smoothing={cfg.waypoint_smoothing:.1f} "
        f"radius={cfg.touch_radius:.0f}"
    )
    _log_detour_init(state, cfg, current_xy, follow_xy, side, center, wps)

    # Tick once now so Player.Move(first_waypoint) goes out this frame.
    first_result = _tick_tree_safe(state.detour_tree)
    state.tick_count += 1
    state.last_tick_ms = _now_ms()
    state.last_tick_xy = current_xy
    if state.detour_tree is not None:
        bb_idx = state.detour_tree.blackboard.get("move_current_waypoint_index", -1)
        if isinstance(bb_idx, int) and bb_idx >= 0 and bb_idx != state.waypoint_idx:
            _log_waypoint_advance(state, bb_idx, state.last_tick_ms, current_xy)
            state.waypoint_idx = bb_idx
            state.waypoint_enter_ms = state.last_tick_ms
    _log_tick_detail(state, current_xy, dist_to_follow, state.last_tick_ms, first_result)


def force_front_detour(
    state: SmartUnstuckState,
    cfg: SmartUnstuckConfig,
    *,
    current_xy: tuple[float, float],
    follow_xy: tuple[float, float],
) -> None:
    """Force the front-of-follower circular avoid path, bypassing enemy slalom."""
    navmesh = _get_navmesh()
    dist_to_follow = Utils.Distance(current_xy, follow_xy)
    candidates: list[tuple[int, tuple[float, float], tuple[tuple[float, float], ...], bool]] = []
    for side in (-1, 1):
        if side in state.sides_tried:
            continue
        center, wps, total = _generate_arc_waypoints(current_xy, follow_xy, cfg, side, navmesh=navmesh)
        walkable_count = len(wps)
        is_walkable = total > 0 and (walkable_count / total) >= cfg.arc_walkability_required_fraction
        if hero_globals.show_stuck_avoidance_debug:
            first_wp_str = f"first_wp=({wps[0][0]:.0f},{wps[0][1]:.0f})" if wps else "first_wp=(none)"
            _log(
                f"stuck.force_probe side={side} walkable={walkable_count}/{total} "
                f"required>={cfg.arc_walkability_required_fraction:.0%} accepted={is_walkable} "
                f"{first_wp_str} center=({center[0]:.0f},{center[1]:.0f})"
            )
        candidates.append((side, center, wps, is_walkable))

    walkable_candidates = [c for c in candidates if c[3]]
    if not walkable_candidates:
        _log("stuck.force_no_walkable_side -> idle")
        reset_smart_unstuck(state)
        return

    if len(walkable_candidates) == 2:
        chosen = next(
            (c for c in walkable_candidates if c[0] == cfg.preferred_side_when_both_walkable),
            walkable_candidates[0],
        )
    else:
        chosen = walkable_candidates[0]

    side, center, wps, _ = chosen
    state.mode = "detouring"
    state.circle_center = center
    state.slalom_centers = ()
    state.slalom_union_boundaries = ()
    state.waypoints = wps
    state.waypoint_idx = 0
    state.abort_waypoint_idx = -1
    now = _now_ms()
    state.detour_started_ms = now
    state.waypoint_started_ms = now
    state.detour_start_dist = dist_to_follow
    state.sides_tried.add(side)
    state.detour_tree = _build_detour_tree(wps, cfg)
    state.tick_count = 0
    state.last_tick_ms = 0
    state.last_tick_xy = None
    state.waypoint_enter_ms = now
    _log(
        f"stuck.force_detour start mode=single side={side} center=({center[0]:.0f},{center[1]:.0f}) "
        f"dist={dist_to_follow:.0f} waypoints={len(wps)} waypoint_smoothing={cfg.waypoint_smoothing:.1f} "
        f"radius={cfg.touch_radius:.0f}"
    )
    _log_detour_init(state, cfg, current_xy, follow_xy, side, center, wps)

    first_result = _tick_tree_safe(state.detour_tree)
    state.tick_count += 1
    state.last_tick_ms = _now_ms()
    state.last_tick_xy = current_xy
    if state.detour_tree is not None:
        bb_idx = state.detour_tree.blackboard.get("move_current_waypoint_index", -1)
        if isinstance(bb_idx, int) and bb_idx >= 0 and bb_idx != state.waypoint_idx:
            _log_waypoint_advance(state, bb_idx, state.last_tick_ms, current_xy)
            state.waypoint_idx = bb_idx
            state.waypoint_enter_ms = state.last_tick_ms
    _log_tick_detail(state, current_xy, dist_to_follow, state.last_tick_ms, first_result)


def update_smart_unstuck(
    state: SmartUnstuckState,
    cfg: SmartUnstuckConfig,
    *,
    current_xy: tuple[float, float],
    follow_xy: tuple[float, float],
    assigned_changed: bool,
) -> None:
    """Tick the per-follower smart-unstuck state machine.

    When mode != "idle" after this returns, BT.Move has already issued
    Player.Move this tick. The caller MUST skip its own Player.Move /
    ActionQueueManager().ResetQueue("ACTION") for the tick — otherwise the
    in-flight BT.Move target gets clobbered.
    """
    _log_first_call_once()
    reload_smart_unstuck_config_from_ini()
    dist_to_follow = Utils.Distance(current_xy, follow_xy)

    if assigned_changed:
        if hero_globals.show_stuck_avoidance_debug:
            _log(f"stuck.assigned_changed dist={dist_to_follow:.0f} mode={state.mode}")
        if state.mode != "idle":
            # Active detour was built for the old follow_xy — abandon it.
            _log(f"stuck.exit reason=assigned_changed mode={state.mode}")
            reset_smart_unstuck(state)
            return None
        # Idle: leader moved but the follower may still be physically stuck.
        # Re-baseline prev_sample_dist against the NEW follow_xy so the next
        # `closed` delta is geometrically correct; keep the no-progress counter
        # and prev_sample_xy.
        if state.prev_sample_xy is not None:
            state.prev_sample_dist = Utils.Distance(state.prev_sample_xy, follow_xy)

    if state.mode == "detouring":
        now = _now_ms()
        if (now - state.detour_started_ms) > cfg.total_detour_timeout_ms:
            total_ms = now - state.detour_started_ms
            _log(
                f"stuck.exit reason=total_timeout "
                f"total_time_ms={total_ms} ticks={state.tick_count}"
            )
            reset_smart_unstuck(state)
            return None
        if (state.detour_start_dist - dist_to_follow) >= cfg.obstacle_cleared_delta:
            total_ms = now - state.detour_started_ms
            dropped = state.detour_start_dist - dist_to_follow
            _log(
                f"stuck.exit reason=cleared dropped={dropped:.0f} "
                f"total_time_ms={total_ms} ticks={state.tick_count}"
            )
            reset_smart_unstuck(state)
            return None

        if state.detour_tree is None:
            _log("stuck.detour_tree missing in detouring mode — resetting")
            reset_smart_unstuck(state)
            return None

        # One BT.Move tick per outer call.
        result = _tick_tree_safe(state.detour_tree)
        state.tick_count += 1
        tick_now = _now_ms()
        bb_idx = state.detour_tree.blackboard.get("move_current_waypoint_index", -1)
        if isinstance(bb_idx, int) and bb_idx >= 0 and bb_idx != state.waypoint_idx:
            _log_waypoint_advance(state, bb_idx, tick_now, current_xy)
            state.waypoint_idx = bb_idx
            state.waypoint_enter_ms = tick_now
        _log_tick_detail(state, current_xy, dist_to_follow, tick_now, result)
        state.last_tick_ms = tick_now
        state.last_tick_xy = current_xy

        # Early-abort once BT has reached the closest-to-goal waypoint —
        # remaining waypoints would arc back away from follow_xy.
        if (
            state.abort_waypoint_idx >= 0
            and state.waypoint_idx >= state.abort_waypoint_idx
            and result == BehaviorTree.NodeState.RUNNING
        ):
            total_ms = tick_now - state.detour_started_ms
            _log(
                f"stuck.exit reason=closest_to_goal "
                f"abort_idx={state.abort_waypoint_idx} "
                f"waypoint_idx={state.waypoint_idx}/{len(state.waypoints)} "
                f"total_time_ms={total_ms} ticks={state.tick_count}"
            )
            reset_smart_unstuck(state)
            return None

        if result == BehaviorTree.NodeState.SUCCESS:
            total_ms = tick_now - state.detour_started_ms
            _log(
                f"stuck.bt_finished reason=success "
                f"total_time_ms={total_ms} ticks={state.tick_count}"
            )
            reset_smart_unstuck(state)
            return None
        if result == BehaviorTree.NodeState.FAILURE:
            reason = state.detour_tree.blackboard.get("move_reason", "?")
            total_ms = tick_now - state.detour_started_ms
            _log(
                f"stuck.bt_failed reason={reason} "
                f"total_time_ms={total_ms} ticks={state.tick_count}"
            )
            reset_smart_unstuck(state)
            return None

        _publish_debug_snapshot(state, cfg)
        return None

    # mode == "idle": sample progress toward follow_xy.
    # Short-circuit when the follower is close to slot — otherwise idle samples
    # see moved≈0 / closed≈0 and falsely accumulate no-progress.
    if dist_to_follow < cfg.min_distance_activate_unstuck:
        if state.no_progress_samples > 0 or state.prev_sample_xy is not None:
            if hero_globals.show_stuck_avoidance_debug:
                _log(
                    f"stuck.skip reason=close_to_followpos "
                    f"dist={dist_to_follow:.0f} threshold={cfg.min_distance_activate_unstuck:.0f}"
                )
            state.no_progress_samples = 0
            state.prev_sample_xy = None
            state.prev_sample_dist = None
        return None

    if state.progress_timer is None:
        state.progress_timer = ThrottledTimer(cfg.progress_sample_interval_ms)
        state.progress_timer.Reset()
    if not state.progress_timer.IsExpired():
        if hero_globals.show_stuck_avoidance_debug:
            _log(
                f"stuck.tick (waiting for sample) dist={dist_to_follow:.0f} "
                f"timer_ms_left={state.progress_timer.GetTimeRemaining():.0f}"
            )
        return None
    state.progress_timer.Reset()

    if state.prev_sample_xy is None:
        state.prev_sample_xy = current_xy
        state.prev_sample_dist = dist_to_follow
        if hero_globals.show_stuck_avoidance_debug:
            _log(f"stuck.sample first dist={dist_to_follow:.0f} pos=({current_xy[0]:.0f},{current_xy[1]:.0f})")
        return None

    moved = Utils.Distance(state.prev_sample_xy, current_xy)
    closed = (state.prev_sample_dist if state.prev_sample_dist is not None else dist_to_follow) - dist_to_follow

    if moved < cfg.no_progress_move_units and closed < cfg.no_progress_close_units:
        state.no_progress_samples += 1
        progressed = False
    else:
        state.no_progress_samples = 0
        progressed = True

    if hero_globals.show_stuck_avoidance_debug:
        _log(
            f"stuck.sample moved={moved:.0f} closed={closed:.0f} "
            f"samples={state.no_progress_samples}/{cfg.stuck_sample_count} "
            f"dist={dist_to_follow:.0f} progress={progressed} "
            f"thresholds(move<{cfg.no_progress_move_units:.0f}, closed<{cfg.no_progress_close_units:.0f})"
        )

    state.prev_sample_xy = current_xy
    state.prev_sample_dist = dist_to_follow

    if state.no_progress_samples >= cfg.stuck_sample_count:
        _log(
            f"stuck.detected dist={dist_to_follow:.0f} samples={state.no_progress_samples} "
            f"pos=({current_xy[0]:.0f},{current_xy[1]:.0f})"
        )
        state.no_progress_samples = 0
        state.sides_tried.clear()
        _enter_detour(state, cfg, current_xy, follow_xy, dist_to_follow)
        _publish_debug_snapshot(state, cfg)

    return None
