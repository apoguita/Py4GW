"""
Raycaster Tester — Line-of-Sight / raycast probe debugger widget.

Draws a ray from the player to the current target: GREEN = clear, RED = blocked.

This is the reference `HasLos` approach, now consuming the Py4GWCoreLib Map.Raycast API
(which wraps the native PyMap bridge and does the math in Python):
  * terrain  Map.Raycast.CastTerrain     -> TerrainQueryIntersection (terrain raycast).
  * props    Map.Raycast.CastInteractive -> IProps::IntersectGeometry over every prop's
             collision geosets (the reference's PropIntersect / PropIntersectMod,
             via the GrModel intersect resolved by a stable assertion anchor).
blocked = terrain OR props; the red line stops at the NEAREST block.

(No navmesh and no combined MapCliQueryIntersection: the navmesh 2D sampling produced
false positives, and the reference HasLos uses terrain + per-prop geometry only.)

Prop debug overlay: Map.Raycast.GetProps() enumerates every map prop. Each prop near the
player is drawn as a 3D ring + ID label so you can see which prop the prop-probe hits
(the blocking prop, by prop_id, is highlighted). Interactive props that carry collision
geosets -- the exact set RayCastInteractive scans -- are cyan; the rest are dimmer.

Live probe debug: per-frame readout of each source + 3D markers at the hit points
(orange = terrain block, blue = prop block).

GUI: master on/off, "Draw 3D line", per-source toggles (terrain / props), prop overlay
toggles, manual Line Z lift slider/field.
"""

import math

import PyImGui
from Py4GWCoreLib import Routines, ImGui, Color, Map
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.AgentArray import AgentArray

MODULE_NAME = "Raycaster Tester"

INI_KEY = ""
INI_PATH = "Widgets/RaycasterTester"
INI_FILENAME = "RaycasterTester.ini"

# Overlay colors are ABGR (0xAABBGGRR), matching ImGui's IM_COL32.
COLOR_CLEAR = 0xFF00FF00      # opaque green
COLOR_BLOCKED = 0xFF0000FF    # opaque red
COLOR_TERRAIN = 0xFF00A5FF    # orange  (terrain block point)
COLOR_PROP = 0xFFFF6000       # blue    (prop block point)
LINE_THICKNESS = 3.0
MARKER_SIZE = 150.0

# Prop overlay colors (ABGR).
COLOR_PROP_COLLIDE = 0xFFFFFF00   # cyan    interactive prop WITH collision geosets
COLOR_PROP_NOMESH = 0xFF00FFFF    # yellow  interactive prop, no geosets
COLOR_PROP_OTHER = 0x80909090     # faint gray  non-interactive prop
COLOR_PROP_HILITE = 0xFFFF00FF    # magenta the prop the ray currently blocks on
PROP_DRAW_RADIUS = 3500.0         # only draw props within this XY range of the player
PROP_RING_RADIUS = 60.0
PROP_RING_BIG = 120.0
PROP_RING_SEGMENTS = 12

# Z lift (world units): positive = up (GW world Z is negative-up, so applied as a
# subtraction in _do_ray). Raises both endpoints so the ray does not graze terrain.
Z_LIFT_DEFAULT = 40.0
Z_LIFT_MAX = 500.0

# Forward cone: a flat horizontal fan of HasLos rays around the player's facing
# direction (no target needed). Each ray green=clear / red=blocked; enemies inside
# the arc are ringed (bright=clear LoS, dim=occluded).
COLOR_CONE_CLEAR = 0xFF00FF00     # green ray (clear)
COLOR_CONE_BLOCKED = 0xFF0000FF   # red ray (blocked)
COLOR_ENEMY_VIS = 0xFF9314FF      # hot pink: enemy in cone, clear LoS
COLOR_ENEMY_OCC = 0x809314FF      # dim hot pink: enemy in cone, LoS occluded
COLOR_ENEMY_UNPROBED = 0x80B0B0B0 # faint gray: in cone but beyond the LoS-probe cap
CONE_RAY_THICKNESS = 2.0
ENEMY_RING_RADIUS = 90.0
ENEMY_RING_SEGMENTS = 10
CONE_MAX_ENEMY_PROBES = 12        # nearest enemies that get a real LoS raycast per frame
CONE_MAX_PROP_MESHES = 12         # distinct cone-hit props whose collision mesh is drawn per frame

CONE_HALF_ANGLE_DEFAULT = 45.0    # degrees to each side of facing
CONE_HALF_ANGLE_MAX = 170.0
CONE_RANGE_DEFAULT = 1500.0
CONE_RANGE_MAX = 5000.0
CONE_RAYS_DEFAULT = 11
CONE_RAYS_MIN = 3
CONE_RAYS_MAX = 200

initialized = False
_status = {"text": "idle", "backend": "-", "color": (0.7, 0.7, 0.7, 1.0), "lines": [], "block_prop_id": -1}
_cone_status = {"text": "idle", "color": (0.7, 0.7, 0.7, 1.0), "lines": []}


def _add_config_vars():
    global INI_KEY
    IniManager().add_bool(INI_KEY, "enabled", "RaycasterTester", "enabled", default=True)
    IniManager().add_bool(INI_KEY, "draw_line", "RaycasterTester", "draw_line", default=True)
    IniManager().add_bool(INI_KEY, "ter_blocks", "RaycasterTester", "ter_blocks", default=True)
    IniManager().add_bool(INI_KEY, "prop_blocks", "RaycasterTester", "prop_blocks", default=True)
    IniManager().add_bool(INI_KEY, "draw_props", "RaycasterTester", "draw_props", default=True)
    IniManager().add_bool(INI_KEY, "props_interactive_only", "RaycasterTester", "props_interactive_only", default=True)
    IniManager().add_bool(INI_KEY, "draw_prop_mesh", "RaycasterTester", "draw_prop_mesh", default=True)
    IniManager().add_float(INI_KEY, "z_lift", "RaycasterTester", "z_lift", default=Z_LIFT_DEFAULT)
    IniManager().add_bool(INI_KEY, "cone_enabled", "RaycasterTester", "cone_enabled", default=False)
    IniManager().add_float(INI_KEY, "cone_half_angle", "RaycasterTester", "cone_half_angle", default=CONE_HALF_ANGLE_DEFAULT)
    IniManager().add_float(INI_KEY, "cone_range", "RaycasterTester", "cone_range", default=CONE_RANGE_DEFAULT)
    IniManager().add_int(INI_KEY, "cone_rays", "RaycasterTester", "cone_rays", default=CONE_RAYS_DEFAULT)
    IniManager().add_bool(INI_KEY, "cone_mark_enemies", "RaycasterTester", "cone_mark_enemies", default=True)
    IniManager().add_bool(INI_KEY, "cone_terrain", "RaycasterTester", "cone_terrain", default=True)
    IniManager().add_bool(INI_KEY, "cone_props", "RaycasterTester", "cone_props", default=True)
    IniManager().add_bool(INI_KEY, "cone_draw_prop_mesh", "RaycasterTester", "cone_draw_prop_mesh", default=True)


def _draw_marker(ov, p, color):
    """Draw a small 3D cross at world point p."""
    x, y, z = p
    s = MARKER_SIZE
    ov.DrawLine3D(x - s, y, z, x + s, y, z, color, 2.0)
    ov.DrawLine3D(x, y - s, z, x, y + s, z, color, 2.0)
    ov.DrawLine3D(x, y, z - s, x, y, z + s, color, 2.0)


def _draw_props():
    """Draw a ring + ID label for every prop near the player (Map.Raycast.GetProps).

    Cyan = interactive prop with collision geosets (RayCastInteractive scans these),
    yellow = interactive prop with no geosets, gray = other props. The prop the ray
    currently blocks on is drawn larger in magenta.
    """
    try:
        if not Routines.Checks.Map.MapValid():
            return
        player_id = Player.GetAgentID()
        if not player_id or not Agent.IsValid(player_id):
            return
        props = Map.Raycast.GetProps()
        if not props:
            return

        px, py, _pz = Agent.GetXYZ(player_id)
        interactive_only = bool(IniManager().get(INI_KEY, "props_interactive_only", True))
        block_id = _status.get("block_prop_id", -1)
        r2 = PROP_DRAW_RADIUS * PROP_DRAW_RADIUS

        ov = Overlay()
        began = False
        try:
            ov.BeginDraw()
            began = True
            for prop_id, x, y, z, is_interactive, rec_count in props:
                if interactive_only and not is_interactive:
                    continue
                dx, dy = x - px, y - py
                if dx * dx + dy * dy > r2:
                    continue
                if prop_id == block_id:
                    color, radius = COLOR_PROP_HILITE, PROP_RING_BIG
                elif is_interactive and rec_count > 0:
                    color, radius = COLOR_PROP_COLLIDE, PROP_RING_RADIUS
                elif is_interactive:
                    color, radius = COLOR_PROP_NOMESH, PROP_RING_RADIUS
                else:
                    color, radius = COLOR_PROP_OTHER, PROP_RING_RADIUS
                ov.DrawPoly3D(x, y, z, radius, color, PROP_RING_SEGMENTS, 2.0, False)
                ov.DrawText3D(x, y, z, str(prop_id), color, False, True, 1.0)
        finally:
            if began:
                ov.EndDraw()
    except Exception:
        pass


def _draw_prop_mesh(prop_id, color):
    """Draw a prop's full collision mesh as a 3D wireframe (Map.Raycast.GetPropGeometry).

    The triangles come from the exact geosets the prop raycast tests, so this shows
    the real shape that blocks LoS (not just a flat ring at the prop's center).
    """
    try:
        if prop_id is None or prop_id < 0:
            return
        tris = Map.Raycast.GetPropGeometry(int(prop_id))
        if not tris:
            return
        ov = Overlay()
        began = False
        try:
            ov.BeginDraw()
            began = True
            for x1, y1, z1, x2, y2, z2, x3, y3, z3 in tris:
                ov.DrawTriangle3D(x1, y1, z1, x2, y2, z2, x3, y3, z3, color, 1.5)
        finally:
            if began:
                ov.EndDraw()
    except Exception:
        pass


def _do_ray(draw_line):
    """Compute reference HasLos player -> target, update _status, and draw ray + probes."""
    global _status
    try:
        if not Routines.Checks.Map.MapValid():
            _status = {"text": "not in an explorable map", "backend": "-", "color": (0.6, 0.6, 0.6, 1.0), "lines": [], "block_prop_id": -1}
            return
        player_id = Player.GetAgentID()
        if not player_id or not Agent.IsValid(player_id):
            _status = {"text": "no player agent", "backend": "-", "color": (0.6, 0.6, 0.6, 1.0), "lines": [], "block_prop_id": -1}
            return
        target_id = Player.GetTargetID()
        if not target_id or target_id == player_id or not Agent.IsValid(target_id):
            _status = {"text": "no target selected", "backend": "-", "color": (0.8, 0.8, 0.4, 1.0), "lines": [], "block_prop_id": -1}
            return

        z_lift = IniManager().getFloat(INI_KEY, "z_lift", Z_LIFT_DEFAULT)
        px, py, pz = Agent.GetXYZ(player_id)
        tx, ty, tz = Agent.GetXYZ(target_id)
        # GW world Z is negative-up, so a positive lift is SUBTRACTED to raise the ray.
        start = (px, py, pz - z_lift)
        end = (tx, ty, tz - z_lift)
        seg_len = math.dist(start, end)

        ter_on = bool(IniManager().get(INI_KEY, "ter_blocks", True))
        prop_on = bool(IniManager().get(INI_KEY, "prop_blocks", True))

        # terrain probe (Map.Raycast.CastTerrain -> TerrainQueryIntersection)
        ter = Map.Raycast.CastTerrain(start, end)
        ter_ok = ter.source != "unavailable"   # source=='unavailable' => probe could not run
        ter_block = (ter.point, ter.distance) if (ter_ok and ter.blocked and ter.point) else None

        # per-prop mesh probe (Map.Raycast.CastInteractive -> reference PropIntersect)
        prop = Map.Raycast.CastInteractive(start, end)
        prop_ok = prop.n_scanned >= 0          # n_scanned==-1 => probe could not run
        prop_id, prop_n = prop.prop_id, prop.n_scanned
        prop_block = (prop.point, prop.distance) if (prop_ok and prop.blocked and prop.point) else None

        # combine (reference HasLos): blocked if terrain OR a prop; nearest block wins
        candidates = [b for b in (ter_block if ter_on else None,
                                  prop_block if prop_on else None) if b is not None]
        if candidates:
            block_point, _ = min(candidates, key=lambda b: b[1])
            blocked = True
        else:
            block_point, blocked = None, False

        srcs = []
        if ter_ok:
            srcs.append("terrain")
        if prop_ok:
            srcs.append("props")
        backend = "+".join(srcs) if srcs else "none"

        # status + debug readout
        lines = []
        if not ter_ok:
            lines.append(("terrain: unavailable (rebuild DLL)", (0.7, 0.7, 0.7, 1.0)))
        elif ter_block is not None:
            tag = "  <BLOCK" if ter_on else "  (ignored: source off)"
            col = (1.0, 0.45, 0.45, 1.0) if ter_on else (0.7, 0.7, 0.5, 1.0)
            lines.append(("terrain: %s @%.0f / tgt %.0f%s"
                          % ("BLOCKED" if ter_on else "hit", ter_block[1], seg_len, tag), col))
        else:
            lines.append(("terrain: clear (tgt %.0f)" % seg_len, (0.7, 0.8, 0.7, 1.0)))
        if not prop_ok:
            lines.append(("props: unavailable (rebuild DLL)", (0.7, 0.7, 0.7, 1.0)))
        elif prop_block is not None:
            tag = "  <BLOCK" if prop_on else "  (ignored: source off)"
            col = (1.0, 0.45, 0.45, 1.0) if prop_on else (0.7, 0.7, 0.5, 1.0)
            lines.append(("props: %s prop=%d @%.0f%s"
                          % ("BLOCKED" if prop_on else "hit", prop_id, prop_block[1], tag), col))
        else:
            lines.append(("props: clear (scanned %d)" % prop_n, (0.7, 0.8, 0.7, 1.0)))

        block_prop_id = prop_id if prop_block is not None else -1
        if blocked:
            _status = {"text": "BLOCKED  (no line of sight)", "backend": backend, "color": (1.0, 0.3, 0.3, 1.0), "lines": lines, "block_prop_id": block_prop_id}
        else:
            _status = {"text": "CLEAR  (line of sight)", "backend": backend, "color": (0.3, 1.0, 0.3, 1.0), "lines": lines, "block_prop_id": block_prop_id}

        if draw_line:
            ov = Overlay()
            began = False
            try:
                ov.BeginDraw()
                began = True
                far = block_point if (blocked and block_point is not None) else end
                ov.DrawLine3D(start[0], start[1], start[2], far[0], far[1], far[2],
                              COLOR_BLOCKED if blocked else COLOR_CLEAR, LINE_THICKNESS)
                if ter_block is not None:
                    _draw_marker(ov, ter_block[0], COLOR_TERRAIN)
                if prop_block is not None:
                    _draw_marker(ov, prop_block[0], COLOR_PROP)
            finally:
                if began:
                    ov.EndDraw()
    except Exception as e:
        _status = {"text": "error: %s" % e, "backend": "-", "color": (1.0, 0.5, 0.0, 1.0), "lines": [], "block_prop_id": -1}


def _segment_block(start, end, ter_on, prop_on):
    """Reference HasLos for one segment -> (blocked, hit_xyz|None, dist|None, source|None, prop_id).
    source is 'terrain' or 'props' for the nearest block; prop_id is the hit prop index when
    source=='props' (else -1). Probes a source only when it is enabled, so toggling one off both
    skips its native raycast and excludes it from blocking. Uses the Map.Raycast library
    primitives for the per-segment terrain+prop combine; enemy/cone detection stays in this widget."""
    candidates = []
    if ter_on:
        ter = Map.Raycast.CastTerrain(start, end)
        if ter.blocked and ter.point:
            candidates.append((ter.point, ter.distance, "terrain", -1))
    if prop_on:
        prop = Map.Raycast.CastInteractive(start, end)
        if prop.blocked and prop.point:
            candidates.append((prop.point, prop.distance, "props", prop.prop_id))
    if candidates:
        pt, dist, source, prop_id = min(candidates, key=lambda b: b[1])
        return True, pt, dist, source, prop_id
    return False, None, None, None, -1


def _angle_diff(a, b):
    """Signed smallest difference (a - b) wrapped to [-pi, pi]."""
    return (a - b + math.pi) % (2.0 * math.pi) - math.pi


def _cone_ray_endpoints(apex, facing, half_rad, rng, n):
    """Flat horizontal fan: n endpoints spread across [facing-half, facing+half] at apex height."""
    ax, ay, az = apex
    ends = []
    for i in range(n):
        t = 0.5 if n == 1 else i / (n - 1)
        ang = facing - half_rad + t * (2.0 * half_rad)
        ends.append((ax + rng * math.cos(ang), ay + rng * math.sin(ang), az))
    return ends


def _mark_enemies_in_cone(ov, apex, facing, half_rad, rng, z_lift, ter_on, prop_on):
    """Ring living enemies inside the cone arc+range. The nearest CONE_MAX_ENEMY_PROBES get a real
    LoS raycast (bright=clear, dim=occluded); farther ones are ringed faint-gray with no probe, so
    the per-frame native cost stays bounded in crowds. Returns (in_cone, visible, probed)."""
    ax, ay, az = apex
    try:
        enemies = AgentArray.GetEnemyArray()
    except Exception:
        return 0, 0, 0
    rng2 = rng * rng

    # cheap XY + arc filter first (no native raycasts); collect (dist2, lifted xyz)
    in_arc = []
    for eid in enemies:
        try:
            if not Agent.IsValid(eid) or not Agent.IsAlive(eid):
                continue
            ex, ey, ez = Agent.GetXYZ(eid)
            if ex == 0.0 and ey == 0.0 and ez == 0.0:
                continue  # GetXYZ sentinel for an agent invalidated mid-frame
            dx, dy = ex - ax, ey - ay
            d2 = dx * dx + dy * dy
            if d2 > rng2:
                continue
            if abs(_angle_diff(math.atan2(dy, dx), facing)) > half_rad:
                continue
            in_arc.append((d2, ex, ey, ez - z_lift))  # lifted to match ray/apex height
        except Exception:
            continue

    in_arc.sort(key=lambda e: e[0])
    visible = probed = 0
    for i, (_d2, ex, ey, ez_lift) in enumerate(in_arc):
        try:
            if i < CONE_MAX_ENEMY_PROBES:
                blocked, _pt, _d, _src, _pid = _segment_block(apex, (ex, ey, ez_lift), ter_on, prop_on)
                probed += 1
                if not blocked:
                    visible += 1
                color = COLOR_ENEMY_OCC if blocked else COLOR_ENEMY_VIS
            else:
                color = COLOR_ENEMY_UNPROBED
            ov.DrawPoly3D(ex, ey, ez_lift, ENEMY_RING_RADIUS, color, ENEMY_RING_SEGMENTS, 2.0, False)
            ov.DrawLine3D(ax, ay, az, ex, ey, ez_lift, color, CONE_RAY_THICKNESS)
        except Exception:
            continue
    return len(in_arc), visible, probed


def _do_cone():
    """Cast a flat horizontal fan of HasLos rays in front of the player; highlight enemies inside it."""
    global _cone_status
    try:
        if not Routines.Checks.Map.MapValid():
            _cone_status = {"text": "not in an explorable map", "color": (0.6, 0.6, 0.6, 1.0), "lines": []}
            return
        player_id = Player.GetAgentID()
        if not player_id or not Agent.IsValid(player_id):
            _cone_status = {"text": "no player agent", "color": (0.6, 0.6, 0.6, 1.0), "lines": []}
            return

        z_lift = IniManager().getFloat(INI_KEY, "z_lift", Z_LIFT_DEFAULT)
        half_deg = IniManager().getFloat(INI_KEY, "cone_half_angle", CONE_HALF_ANGLE_DEFAULT)
        rng = IniManager().getFloat(INI_KEY, "cone_range", CONE_RANGE_DEFAULT)
        n_rays = max(CONE_RAYS_MIN, min(CONE_RAYS_MAX, int(IniManager().getInt(INI_KEY, "cone_rays", CONE_RAYS_DEFAULT))))
        ter_on = bool(IniManager().get(INI_KEY, "cone_terrain", True))
        prop_on = bool(IniManager().get(INI_KEY, "cone_props", True))
        mark_enemies = bool(IniManager().get(INI_KEY, "cone_mark_enemies", True))
        draw_mesh = bool(IniManager().get(INI_KEY, "cone_draw_prop_mesh", True))

        px, py, pz = Agent.GetXYZ(player_id)
        facing = float(Agent.GetRotationAngle(player_id))
        half_rad = math.radians(half_deg)
        # GW world Z is negative-up, so a positive lift is SUBTRACTED to raise the fan.
        apex = (px, py, pz - z_lift)

        blocked_count = 0
        ter_hits = prop_hits = 0
        hit_prop_ids = set()
        nearest = None
        in_cone = visible = probed = 0
        ov = Overlay()
        began = False
        try:
            ov.BeginDraw()
            began = True
            for end in _cone_ray_endpoints(apex, facing, half_rad, rng, n_rays):
                blocked, pt, dist, source, hit_prop_id = _segment_block(apex, end, ter_on, prop_on)
                if blocked and pt is not None:
                    blocked_count += 1
                    if source == "terrain":
                        ter_hits += 1
                    elif source == "props":
                        prop_hits += 1
                        if hit_prop_id >= 0:
                            hit_prop_ids.add(hit_prop_id)
                    nearest = dist if nearest is None else min(nearest, dist)
                    ov.DrawLine3D(apex[0], apex[1], apex[2], pt[0], pt[1], pt[2],
                                  COLOR_CONE_BLOCKED, CONE_RAY_THICKNESS)
                else:
                    ov.DrawLine3D(apex[0], apex[1], apex[2], end[0], end[1], end[2],
                                  COLOR_CONE_CLEAR, CONE_RAY_THICKNESS)
            if mark_enemies:
                in_cone, visible, probed = _mark_enemies_in_cone(
                    ov, apex, facing, half_rad, rng, z_lift, ter_on, prop_on)
        finally:
            if began:
                ov.EndDraw()

        # draw the collision mesh of each distinct prop a cone ray hit (own BeginDraw/EndDraw)
        if draw_mesh and hit_prop_ids:
            for pid in list(hit_prop_ids)[:CONE_MAX_PROP_MESHES]:
                _draw_prop_mesh(pid, COLOR_PROP_HILITE)

        lines = [("rays: %d/%d blocked%s"
                  % (blocked_count, n_rays,
                     ("  nearest @%.0f" % nearest) if nearest is not None else ""),
                  (0.8, 0.7, 0.6, 1.0))]
        lines.append(("  by source: terrain %d, props %d%s%s"
                      % (ter_hits, prop_hits,
                         "" if ter_on else "  (terrain off)",
                         "" if prop_on else "  (props off)"),
                      (0.7, 0.75, 0.7, 1.0)))
        if mark_enemies:
            note = "enemies: %d in cone, %d with LoS" % (in_cone, visible)
            if probed < in_cone:
                note += "  (nearest %d probed)" % probed
            lines.append((note, (0.9, 0.6, 0.85, 1.0)))
        _cone_status = {
            "text": "cone: %d clear / %d blocked" % (n_rays - blocked_count, blocked_count),
            "color": (0.3, 1.0, 0.3, 1.0) if blocked_count == 0 else (1.0, 0.7, 0.3, 1.0),
            "lines": lines,
        }
    except Exception as e:
        _cone_status = {"text": "cone error: %s" % e, "color": (1.0, 0.5, 0.0, 1.0), "lines": []}


def _draw_window():
    global INI_KEY, _status
    if ImGui.Begin(INI_KEY, MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        enabled = bool(IniManager().get(INI_KEY, "enabled", True))
        new_enabled = PyImGui.checkbox("Enabled", enabled)
        if new_enabled != enabled:
            IniManager().set(INI_KEY, "enabled", new_enabled)

        draw_line = bool(IniManager().get(INI_KEY, "draw_line", True))
        new_draw_line = PyImGui.checkbox("Draw 3D line", draw_line)
        if new_draw_line != draw_line:
            IniManager().set(INI_KEY, "draw_line", new_draw_line)

        ter_on = bool(IniManager().get(INI_KEY, "ter_blocks", True))
        new_ter_on = PyImGui.checkbox("Terrain blocks LoS", ter_on)
        if new_ter_on != ter_on:
            IniManager().set(INI_KEY, "ter_blocks", new_ter_on)

        prop_on = bool(IniManager().get(INI_KEY, "prop_blocks", True))
        new_prop_on = PyImGui.checkbox("Props block LoS", prop_on)
        if new_prop_on != prop_on:
            IniManager().set(INI_KEY, "prop_blocks", new_prop_on)

        draw_props = bool(IniManager().get(INI_KEY, "draw_props", True))
        new_draw_props = PyImGui.checkbox("Draw props", draw_props)
        if new_draw_props != draw_props:
            IniManager().set(INI_KEY, "draw_props", new_draw_props)

        int_only = bool(IniManager().get(INI_KEY, "props_interactive_only", True))
        new_int_only = PyImGui.checkbox("Interactive props only", int_only)
        if new_int_only != int_only:
            IniManager().set(INI_KEY, "props_interactive_only", new_int_only)

        mesh_on = bool(IniManager().get(INI_KEY, "draw_prop_mesh", True))
        new_mesh_on = PyImGui.checkbox("Draw blocking prop mesh", mesh_on)
        if new_mesh_on != mesh_on:
            IniManager().set(INI_KEY, "draw_prop_mesh", new_mesh_on)

        z_lift = IniManager().getFloat(INI_KEY, "z_lift", Z_LIFT_DEFAULT)
        new_z_lift = PyImGui.slider_float("Line Z lift", z_lift, 0.0, Z_LIFT_MAX)
        if new_z_lift != z_lift:
            IniManager().set(INI_KEY, "z_lift", new_z_lift)
            z_lift = new_z_lift
        # typeable field for exact values (drag the slider above, or type here)
        typed_z = PyImGui.input_float("Line Z lift (type)", z_lift)
        if typed_z != z_lift:
            IniManager().set(INI_KEY, "z_lift", typed_z)

        PyImGui.separator()
        cone_on = bool(IniManager().get(INI_KEY, "cone_enabled", False))
        new_cone_on = PyImGui.checkbox("Forward cone (facing dir)", cone_on)
        if new_cone_on != cone_on:
            IniManager().set(INI_KEY, "cone_enabled", new_cone_on)
        if cone_on:
            cone_ter = bool(IniManager().get(INI_KEY, "cone_terrain", True))
            new_cone_ter = PyImGui.checkbox("Cone: terrain blocks", cone_ter)
            if new_cone_ter != cone_ter:
                IniManager().set(INI_KEY, "cone_terrain", new_cone_ter)

            cone_prop = bool(IniManager().get(INI_KEY, "cone_props", True))
            new_cone_prop = PyImGui.checkbox("Cone: props block", cone_prop)
            if new_cone_prop != cone_prop:
                IniManager().set(INI_KEY, "cone_props", new_cone_prop)

            cone_mesh = bool(IniManager().get(INI_KEY, "cone_draw_prop_mesh", True))
            new_cone_mesh = PyImGui.checkbox("Cone: draw hit prop mesh", cone_mesh)
            if new_cone_mesh != cone_mesh:
                IniManager().set(INI_KEY, "cone_draw_prop_mesh", new_cone_mesh)

            half_deg = IniManager().getFloat(INI_KEY, "cone_half_angle", CONE_HALF_ANGLE_DEFAULT)
            new_half = PyImGui.slider_float("Cone half-angle (deg)", half_deg, 5.0, CONE_HALF_ANGLE_MAX)
            if new_half != half_deg:
                IniManager().set(INI_KEY, "cone_half_angle", new_half)

            cone_range = IniManager().getFloat(INI_KEY, "cone_range", CONE_RANGE_DEFAULT)
            new_range = PyImGui.slider_float("Cone range", cone_range, 100.0, CONE_RANGE_MAX)
            if new_range != cone_range:
                IniManager().set(INI_KEY, "cone_range", new_range)

            cone_rays = IniManager().getInt(INI_KEY, "cone_rays", CONE_RAYS_DEFAULT)
            new_rays = PyImGui.slider_int("Cone rays", cone_rays, CONE_RAYS_MIN, CONE_RAYS_MAX)
            if new_rays != cone_rays:
                IniManager().set(INI_KEY, "cone_rays", new_rays)

            mark_enemies = bool(IniManager().get(INI_KEY, "cone_mark_enemies", True))
            new_mark = PyImGui.checkbox("Mark enemies in cone", mark_enemies)
            if new_mark != mark_enemies:
                IniManager().set(INI_KEY, "cone_mark_enemies", new_mark)

            PyImGui.text_colored(_cone_status["text"], _cone_status["color"])
            for _t, _c in _cone_status.get("lines", []):
                PyImGui.text_colored(_t, _c)

        PyImGui.separator()
        PyImGui.text("Player -> Target line of sight")
        PyImGui.text_colored(_status["text"], _status["color"])
        PyImGui.text("backend: " + str(_status["backend"]))
        for _t, _c in _status.get("lines", []):
            PyImGui.text_colored(_t, _c)
    ImGui.End(INI_KEY)


def draw():
    """Runs every frame (draw phase)."""
    global initialized
    if not initialized:
        return
    enabled = bool(IniManager().get(INI_KEY, "enabled", True))
    if enabled:
        draw_line = bool(IniManager().get(INI_KEY, "draw_line", True))
        _do_ray(draw_line)
        if bool(IniManager().get(INI_KEY, "draw_props", True)):
            _draw_props()
        if bool(IniManager().get(INI_KEY, "draw_prop_mesh", True)):
            _draw_prop_mesh(_status.get("block_prop_id", -1), COLOR_PROP_HILITE)
        if bool(IniManager().get(INI_KEY, "cone_enabled", False)):
            _do_cone()
    else:
        _status.update({"text": "disabled", "backend": "-", "color": (0.6, 0.6, 0.6, 1.0), "lines": [], "block_prop_id": -1})
    _draw_window()


def tooltip():
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.text("Reference HasLos tester (terrain + props):")
    PyImGui.bullet_text("Green = clear, Red = blocked (terrain OR prop geometry)")
    PyImGui.bullet_text("Markers: orange=terrain block, blue=prop block")
    PyImGui.bullet_text("Draw props: cyan=collision prop, yellow=no mesh, magenta=blocking")
    PyImGui.bullet_text("Blocking prop is drawn as a full magenta wireframe mesh")
    PyImGui.bullet_text("Raise Line Z lift to chest height so the ray clears the ground")
    PyImGui.end_tooltip()


def main():
    """Runs once to initialize."""
    global INI_KEY, initialized
    if initialized:
        return
    if not Routines.Checks.Map.MapValid():
        return
    if not INI_KEY:
        INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
        if not INI_KEY:
            return
        _add_config_vars()
        IniManager().load_once(INI_KEY)
        initialized = True


if __name__ == "__main__":
    main()
