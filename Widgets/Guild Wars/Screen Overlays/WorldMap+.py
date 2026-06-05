"""
WorldMap+
=========
Overlay for the GW World Map that renders all map boundaries and their
portal connections.  Open the World Map (default key: M) to see the overlay.

Color coding
  Gold     — current map you are in
  Green    — Explorable zones
  Blue     — Outposts / Cities
  Cyan     — Co-op Missions / Mission Outposts
  Orange   — Challenge / Competitive missions
  Yellow lines connect maps that share a walkable portal.
"""

import PyImGui
import traceback
import math
import Py4GW
import json
import os
import sys
import time
from collections import defaultdict

from Py4GWCoreLib import Map, Utils
from Py4GWCoreLib.IniManager import IniManager as _IniManager
from Py4GWCoreLib.native_src.methods.MapMethods import MapMethods
from Py4GWCoreLib.native_src.methods.FfnaMapMethods import FfnaMapMethods
from Py4GWCoreLib.Overlay import Overlay as _Overlay

MODULE_NAME = "WorldMap+"

try:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _SCRIPT_DIR = os.path.join(
        Py4GW.Console.get_projects_path(),
        "Widgets", "Guild Wars", "Screen Overlays"
    )

# Shared adapter directory for all persisted data (portal cache + map boundaries)
_ADAPTER_DIR = os.path.join(
    Py4GW.Console.get_projects_path(),
    "Sources", "sch0l0ka", "adapter", "Worldmap+"
)

# WorldPathing lives in the adapter directory; use sys.path so the + in the
# folder name doesn't interfere with Python import syntax.
if _ADAPTER_DIR not in sys.path:
    sys.path.insert(0, _ADAPTER_DIR)
import WorldPathing as _WP  # type: ignore[import-not-found]
_WP.configure(_SCRIPT_DIR)
from WorldPathing import (  # type: ignore[import-not-found]
    _MAP_ADJACENCY, _ALL_EDGES,
    _MAP_META,
    _GLOBAL_ID_TO_PORTAL, _PORTAL_TO_GLOBAL_ID, _PORTAL_LINKS,
    _map_name_cached,
    _load_portal_links,
    invalidate_world_adj as _wp_invalidate_world_adj,
)

# ── Overlay-only state (not shared with WorldPathing) ─────────────────────────
_ICON_BOUNDS:      dict[int, tuple[float, float, float, float] | None] = {}
_MAP_CENTROIDS:    dict[int, tuple[float, float]] = {}
_MAP_NEIGHBORS:    dict[int, set[int]] = {}
_CONNECTED_MAP_IDS: set[int] = set()

# Off-map dungeons: map_id -> (anchor_map_id, side)
# side = "left" | "right" | "above" | "below"
_OFFMAP_PLACEMENTS: dict[int, tuple[int, str]] = {
    604: (639, "left"),   # EotN dungeon – display left of Umbral Grotto
}
_MANUAL_PORTAL_MAPS: set[int] = {604}

_PORTAL_ICON_POS:  dict[int, list[tuple]] = {}
_PORTAL_BUILT:     set[int] = set()
_PORTAL_DEST_DATA: dict[int, list[dict]] = {}
_PORTAL_ALL_DATA:  dict[int, list[dict]] = {}
_live_portal_cache: dict = {}  # values are either list[dict] or dict with "portals"/"extents" keys
_LIVE_PORTAL_CACHE_FILE = os.path.join(_ADAPTER_DIR, "portal_live_cache.json")
_MAP_RECT_FILE          = os.path.join(_ADAPTER_DIR, "map_boundaries.json")
_PORTAL_ALL_FILE        = os.path.join(_SCRIPT_DIR,  "portal_all.json")
_PORTAL_LINKS_FILE      = os.path.join(_SCRIPT_DIR,  "portal_links.json")

# In-memory cache: map_id -> (gx_min, gx_max, gy_min, gy_max)
_MAP_RECT_CACHE: dict[int, tuple[float, float, float, float]] = {}

# ── Region type constants ──────────────────────────────────────────────────────
_RT_EXPLORABLE   = 2
_RT_COOP         = 6
_RT_CHALLENGE    = 7
_RT_COMPETITIVE  = 8
_RT_ELITE        = 9
_RT_OUTPOST      = 10
_RT_MISSION_OUT  = 5
_RT_TOWN         = 13
_RT_CITY         = 14
_RT_HERO_BATTLE  = 15

_STANDARD_RTYPES = frozenset((
    _RT_EXPLORABLE, _RT_OUTPOST, _RT_TOWN, _RT_CITY,
    _RT_MISSION_OUT, _RT_COOP, _RT_CHALLENGE, _RT_COMPETITIVE, _RT_ELITE,
))

_MAX_MAP_ID  = 900
_cache_built = False
_pmap_built  = False

# Deduplicated draw groups: (frozenset_of_map_ids, bounds, label, rtype, campaign)
_DRAW_GROUPS: list[tuple] = []

# Per-map pathing geometry for rendering:
# value = ((gx_min, gx_max, gy_min, gy_max), [(XTL, XTR, XBL, XBR, YT, YB), ...])
_PMAP_DATA: dict[int, tuple[tuple[float,float,float,float], list[tuple[float,float,float,float,float,float]]]] = {}
_PATHING_MAPS_CACHE: dict[int, list] = {}   # raw pathing-map objects needed by NavMesh/A*

# Screen-space transform updated at the start of every _draw_overlay call:
# [sl, st, il, it, sx, sy]  where sx = sw/iw, sy = sh/ih
_s_transform: list[float] = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0]


def _icon_to_screen(ix: float, iy: float) -> tuple[float, float]:
    """Convert icon-space coordinates to screen pixels using the cached transform."""
    sl, st, il, it, sx, sy = _s_transform
    return sl + (ix - il) * sx, st + (iy - it) * sy


def _screen_to_icon(sx: float, sy: float) -> tuple[float, float]:
    """Inverse of _icon_to_screen: screen pixels → icon-space coordinates."""
    sl, st, il, it, sx_scale, sy_scale = _s_transform
    return il + (sx - sl) / sx_scale, it + (sy - st) / sy_scale

# ── Campaign grouping ──────────────────────────────────────────────────────────
# Campaign values: 0=Core/PvP, 1=Prophecies, 2=Factions, 3=Nightfall, 4=EotN
# EotN is grouped with Prophecies since both share the Tyrian continent.
def _campaign_group(campaign: int) -> int:
    return 1 if campaign == 4 else campaign

# ── Color tables ───────────────────────────────────────────────────────────────
_FILL_RGB: dict[int, tuple[int, int, int]] = {
    _RT_EXPLORABLE:   ( 50, 190,  80),
    _RT_OUTPOST:      ( 70, 130, 245),
    _RT_TOWN:         ( 70, 130, 245),
    _RT_CITY:         ( 70, 130, 245),
    _RT_MISSION_OUT:  ( 50, 200, 200),
    _RT_COOP:         ( 50, 200, 200),
    _RT_CHALLENGE:    (245, 150,  50),
    _RT_COMPETITIVE:  (245, 150,  50),
    _RT_ELITE:        (245, 150,  50),
    _RT_HERO_BATTLE:  (200,  80, 255),
}
_BORDER_RGB: dict[int, tuple[int, int, int]] = {
    _RT_EXPLORABLE:   ( 90, 230, 120),
    _RT_OUTPOST:      (130, 170, 255),
    _RT_TOWN:         (130, 170, 255),
    _RT_CITY:         (130, 170, 255),
    _RT_MISSION_OUT:  ( 90, 230, 230),
    _RT_COOP:         ( 90, 230, 230),
    _RT_CHALLENGE:    (255, 190,  90),
    _RT_COMPETITIVE:  (255, 190,  90),
    _RT_ELITE:        (255, 190,  90),
}

def _type_fill(rtype: int, alpha: int) -> int:
    r, g, b = _FILL_RGB.get(rtype, (150, 150, 150))
    return Utils.RGBToColor(r, g, b, alpha)

def _type_border(rtype: int, alpha: int) -> int:
    r, g, b = _BORDER_RGB.get(rtype, (190, 190, 190))
    return Utils.RGBToColor(r, g, b, alpha)

# ── UI state ───────────────────────────────────────────────────────────────────
_show_frames:      list[bool]  = [True]
_show_portals:     list[bool]  = [True]
_show_connections: list[bool]  = [True]
_show_labels:      list[bool]  = [True]
_show_navmesh:     list[bool]  = [False]
_opacity:          list[float] = [0.75]
_show_ui_settings:   list[bool]  = [False]
_show_debug:         list[bool]  = [False]
_show_experimental:  list[bool]  = [False]  # when False: overlay only active on Prophecies
_show_unconnected:   list[bool]  = [False]  # when False: hide maps with no portal links
_record_portals:     list[bool]  = [True]   # write to portal_live_cache.json
_record_boundaries:  list[bool]  = [True]   # write to map_boundaries.json
_show_portal_editor: list[bool]  = [False]  # open the portal editor window
_pe_gid_a:          list[int]   = [0]       # portal editor: GID input A
_pe_gid_b:          list[int]   = [0]       # portal editor: GID input B
_pe_status:         list[str]   = [""]      # portal editor: last action result
_debug_map_a:      list[int]   = [0]
_debug_map_b:      list[int]   = [0]
_debug_map_a_str:  list[str]   = ["0"]
_debug_map_b_str:  list[str]   = ["0"]
_debug_move_str:   list[str]   = ["0"]
_debug_move_id:    list[int]   = [0]
_debug_coords_map_str: list[str]   = ["0"]
_debug_coords_map_id:  list[int]   = [0]
_debug_coords_x_str:   list[str]   = ["0"]
_debug_coords_x:       list[float] = [0.0]
_debug_coords_y_str:   list[str]   = ["0"]
_debug_coords_y:       list[float] = [0.0]
_rclick_active:        list[bool]  = [False]  # right-click context popup enabled
_active_move_tree: list = [None]   # holds the running MoveToMapID BehaviorTree | None
_active_move_path: list[int] = []  # path list from GetPath() for the active route
# per-hop icon-space polylines: (map_id, [(ix, iy), ...])
_route_hops: list[tuple[int, list[tuple[float, float]]]] = []
_last_map:         list[int]   = [0]
_map_queue:        list[int]   = []    # ordered list of map IDs to visit
_queue_running:    list[bool]  = [False]
# Context popup state: list of (map_id, dest_x, dest_y) for all frames under
# the last right-click.  dest_x/dest_y are 0.0 if MoveToRightClick is off or
# no trapezoid was found.
_ctx_entries:      list[tuple[int, float, float]] = []
_ctx_click_sx:     list[float] = [0.0] # screen-x of right-click
_ctx_click_sy:     list[float] = [0.0] # screen-y of right-click

# ── INI persistence ────────────────────────────────────────────────────────────
_WMP_INI_PATH     = "Widgets/WorldMap+"
_WMP_INI_FILENAME = "WorldMap+.ini"
_wmp_ini_key:   list[str]  = [""]
_wmp_ini_ready: list[bool] = [False]


def _wmp_ini_try_init() -> bool:
    if _wmp_ini_ready[0]:
        return True
    key = _IniManager().ensure_key(_WMP_INI_PATH, _WMP_INI_FILENAME)
    if not key:
        return False
    _wmp_ini_key[0] = key
    ini = _IniManager()
    s = "Settings"
    _show_frames[0]      = ini.read_bool (key, s, "show_frames",      True)
    _show_portals[0]     = ini.read_bool (key, s, "show_portals",     True)
    _show_connections[0] = ini.read_bool (key, s, "show_connections", True)
    _show_labels[0]      = ini.read_bool (key, s, "show_labels",      True)
    _show_navmesh[0]     = ini.read_bool (key, s, "show_navmesh",     False)
    _opacity[0]          = ini.read_float(key, s, "opacity",          0.75)
    _show_experimental[0] = ini.read_bool(key, s, "show_experimental", False)
    _show_unconnected[0]  = ini.read_bool(key, s, "show_unconnected",  False)
    _record_portals[0]    = ini.read_bool(key, s, "record_portals",    True)
    _record_boundaries[0] = ini.read_bool(key, s, "record_boundaries", True)
    _wmp_ini_ready[0] = True
    return True


def _wmp_ini_save() -> None:
    key = _wmp_ini_key[0]
    if not key:
        return
    ini = _IniManager()
    s = "Settings"
    ini.write_key(key, s, "show_frames",      _show_frames[0])
    ini.write_key(key, s, "show_portals",     _show_portals[0])
    ini.write_key(key, s, "show_connections", _show_connections[0])
    ini.write_key(key, s, "show_labels",      _show_labels[0])
    ini.write_key(key, s, "show_navmesh",     _show_navmesh[0])
    ini.write_key(key, s, "opacity",          _opacity[0])
    ini.write_key(key, s, "show_experimental", _show_experimental[0])
    ini.write_key(key, s, "show_unconnected",  _show_unconnected[0])
    ini.write_key(key, s, "record_portals",    _record_portals[0])
    ini.write_key(key, s, "record_boundaries", _record_boundaries[0])

# ── Rendering helpers ──────────────────────────────────────────────────────────

def _load_map_rect_cache() -> None:
    """Load accumulated map boundaries from the adapter file into _MAP_RECT_CACHE."""
    global _MAP_RECT_CACHE
    if not os.path.isfile(_MAP_RECT_FILE):
        return
    try:
        with open(_MAP_RECT_FILE, "r", encoding="utf-8-sig") as fh:
            raw: dict = json.load(fh)
        loaded = 0
        for k, v in raw.items():
            try:
                mid = int(k)
                gx_min = float(v["gx_min"]); gx_max = float(v["gx_max"])
                gy_min = float(v["gy_min"]); gy_max = float(v["gy_max"])
                if gx_max > gx_min and gy_max > gy_min:
                    _MAP_RECT_CACHE[mid] = (gx_min, gx_max, gy_min, gy_max)
                    loaded += 1
            except Exception:
                pass
        Py4GW.Console.Log(MODULE_NAME,
            f"Map-rect cache loaded: {loaded} maps.",
            Py4GW.Console.MessageType.Info)
    except Exception as exc:
        Py4GW.Console.Log(MODULE_NAME, f"Map-rect load error: {exc}",
                          Py4GW.Console.MessageType.Warning)


def _save_map_rect_cache() -> None:
    """Persist _MAP_RECT_CACHE to the adapter file (no-op when recording is off)."""
    if not _record_boundaries[0]:
        return
    try:
        os.makedirs(_ADAPTER_DIR, exist_ok=True)
        out = {
            str(mid): {
                "gx_min": gb[0], "gx_max": gb[1],
                "gy_min": gb[2], "gy_max": gb[3],
            }
            for mid, gb in sorted(_MAP_RECT_CACHE.items())
        }
        with open(_MAP_RECT_FILE, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
    except Exception as exc:
        Py4GW.Console.Log(MODULE_NAME, f"Map-rect save error: {exc}",
                          Py4GW.Console.MessageType.Warning)


def _record_map_rect(map_id: int, gx_min: float, gx_max: float,
                     gy_min: float, gy_max: float) -> None:
    """Store boundaries for map_id and persist if it is a new/changed entry.

    Also invalidates any pmap entry that was cached with different (e.g. FFNA-derived)
    bounds, so that the next draw will reload using the correct live bounds.
    """
    if gx_max <= gx_min or gy_max <= gy_min:
        return
    existing = _MAP_RECT_CACHE.get(map_id)
    new_val  = (gx_min, gx_max, gy_min, gy_max)
    if existing == new_val:
        return
    _MAP_RECT_CACHE[map_id] = new_val
    _save_map_rect_cache()
    # If pmap was previously cached with different bounds (e.g. FFNA local-space),
    # drop it so _draw_pmap_for_map will reload with the now-correct live bounds.
    pmap_entry = _PMAP_DATA.get(map_id)
    if pmap_entry and pmap_entry[0] != new_val:
        _PMAP_DATA.pop(map_id, None)
        # Portal dots are also projected using game bounds — invalidate so they
        # are recomputed with the updated live bounds on the next draw frame.
        _PORTAL_BUILT.discard(map_id)
        _PORTAL_ICON_POS.pop(map_id, None)
        # Also invalidate route hops if this map is part of the active path —
        # they were computed with the old bounds and need to be recalculated.
        if map_id in _active_move_path:
            _route_hops.clear()


def _zoom_is_default() -> bool:
    return abs(Map.WorldMap.GetZoom() - 1.0) <= 0.001


def _get_panel_flags() -> int:
    return (
        PyImGui.WindowFlags.NoTitleBar        |
        PyImGui.WindowFlags.NoResize          |
        PyImGui.WindowFlags.NoMove            |
        PyImGui.WindowFlags.NoCollapse        |
        PyImGui.WindowFlags.AlwaysAutoResize  |
        PyImGui.WindowFlags.NoSavedSettings
    )


def _compute_game_bounds(pathing_maps) -> tuple[float, float, float, float] | None:
    gx_min = float('inf');  gx_max = float('-inf')
    gy_min = float('inf');  gy_max = float('-inf')
    for pm in pathing_maps:
        for trap in pm.trapezoids:
            for x in (trap.XTL, trap.XTR, trap.XBL, trap.XBR):
                if x < gx_min: gx_min = x
                if x > gx_max: gx_max = x
            for y in (trap.YT, trap.YB):
                if y < gy_min: gy_min = y
                if y > gy_max: gy_max = y
    if gx_min == float('inf') or gx_max <= gx_min or gy_max <= gy_min:
        return None
    return (gx_min, gx_max, gy_min, gy_max)


_pmap_load_queue:       list[int]   = []   # map IDs still to be loaded
_PMAP_LOAD_PER_TICK     = 2                 # maps parsed per allowed tick
_PMAP_LOAD_INTERVAL_S   = 0.033            # minimum seconds between ticks (33 ms ≈ 60/s)
_PMAP_LOG_INTERVAL_S    = 1.0              # seconds between progress log lines
_pmap_last_load_t:      list[float] = [0.0]
_pmap_last_log_t:       list[float] = [0.0]
_pmap_total:            list[int]   = [0]  # total maps to load (set at queue init)


def _nearest_trap_game_xy(map_id: int, gx_click: float, gy_click: float
                           ) -> tuple[float, float] | None:
    """Return the center of the trapezoid in map_id's pmap closest to (gx_click, gy_click).

    Returns None when no pmap data is available for the map.
    """
    entry = _PMAP_DATA.get(map_id)
    if not entry or not entry[1]:
        return None
    best_dist2 = float('inf')
    best: tuple[float, float] | None = None
    for XTL, XTR, XBL, XBR, YT, YB in entry[1]:
        cx = (XTL + XTR + XBL + XBR) / 4.0
        cy = (YT + YB) / 2.0
        d2 = (cx - gx_click) ** 2 + (cy - gy_click) ** 2
        if d2 < best_dist2:
            best_dist2 = d2
            best = (cx, cy)
    return best


def _pmap_cache_for(map_id: int) -> None:
    """Parse and store pmap data for a single map_id (no-op if already cached).

    Bounds priority:
      1. _MAP_RECT_CACHE  – live Map.GetMapBoundaries() accumulated across sessions
      2. _compute_game_bounds() from FFNA trapezoids – always produces a valid
         self-consistent projection (trapezoids fill their own bounds exactly).

    Real-time Map.GetMapBoundaries() is intentionally NOT called here to avoid a
    race condition during map transitions (the live value can be degenerate on the
    same frame the map ID changes).  Instead, _record_map_rect() is called from
    _ensure_portal_dots() once the map is fully rendered, and it invalidates this
    cache entry so the next draw reloads with the correct live bounds.
    """
    if map_id in _PMAP_DATA:
        return
    try:
        pmaps = FfnaMapMethods.GetPathingMapsForMap(map_id)

        # Some maps have no DAT entry (e.g. map 27).  When the player is
        # currently inside one of those maps we can fall back to the live
        # in-memory pathing data instead.
        if not pmaps and map_id == Map.GetMapID():
            try:
                pmaps = Map.Pathing.GetPathingMaps()
            except Exception:
                pass

        if not pmaps:
            _PMAP_DATA[map_id] = ((0.0, 0.0, 0.0, 0.0), [])
            return

        # 1. Adapter file cache (correct live bounds from any previous session).
        #    _record_map_rect() is called every frame in _draw_overlay for the
        #    current map, so this entry is always up-to-date when the player is in-map.
        gb: tuple[float, float, float, float] | None = _MAP_RECT_CACHE.get(map_id)

        # 2. FFNA/live trapezoid bounds – always valid, trapezoids project within [0,1]
        if gb is None:
            gb = _compute_game_bounds(pmaps)
        if gb is None:
            _PMAP_DATA[map_id] = ((0.0, 0.0, 0.0, 0.0), [])
            return

        traps: list[tuple[float,float,float,float,float,float]] = []
        for pm in pmaps:
            for t in pm.trapezoids:
                traps.append((t.XTL, t.XTR, t.XBL, t.XBR, t.YT, t.YB))
        if traps:
            _PMAP_DATA[map_id] = (gb, traps)
            _PATHING_MAPS_CACHE[map_id] = pmaps   # raw objects for NavMesh/A*
        else:
            _PMAP_DATA[map_id] = ((0.0, 0.0, 0.0, 0.0), [])
    except Exception:
        _PMAP_DATA[map_id] = ((0.0, 0.0, 0.0, 0.0), [])


def _tick_pmap_loader() -> None:
    """Load one map per tick, at most once every _PMAP_LOAD_INTERVAL_S seconds.

    Spreading the DAT-file I/O over time keeps individual frames cheap and
    avoids FPS drops from bursts of disk reads.
    """
    global _pmap_built
    if _pmap_built:
        return
    now = time.perf_counter()

    # Progress log once per second
    if now - _pmap_last_log_t[0] >= _PMAP_LOG_INTERVAL_S and _pmap_total[0] > 0:
        _pmap_last_log_t[0] = now
        loaded = _pmap_total[0] - len(_pmap_load_queue)
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Pmap cache: {loaded}/{_pmap_total[0]} maps loaded ...",
            Py4GW.Console.MessageType.Info,
        )

    if now - _pmap_last_load_t[0] < _PMAP_LOAD_INTERVAL_S:
        return
    _pmap_last_load_t[0] = now
    for _ in range(_PMAP_LOAD_PER_TICK):
        if not _pmap_load_queue:
            _pmap_built = True
            loaded = _pmap_total[0]
            Py4GW.Console.Log(
                MODULE_NAME,
                f"Pmap cache complete: {loaded}/{loaded} maps loaded.",
                Py4GW.Console.MessageType.Success,
            )
            return
        mid = _pmap_load_queue.pop()
        _pmap_cache_for(mid)


def _init_pmap_queue() -> None:
    """Populate the load queue with all map IDs not yet in _PMAP_DATA."""
    global _pmap_built
    if _pmap_built:
        return
    # Current map and its neighbours get priority (put them at the end of the
    # stack so they are popped first).
    all_ids  = [m for m in _ICON_BOUNDS if m not in _PMAP_DATA]
    cur      = Map.GetMapID()
    priority = {cur} | _MAP_NEIGHBORS.get(cur, set())
    deferred = [m for m in all_ids if m not in priority]
    urgent   = [m for m in all_ids if m in priority]
    _pmap_load_queue.clear()
    _pmap_load_queue.extend(deferred)   # loaded last (bottom of stack)
    _pmap_load_queue.extend(urgent)     # loaded first (top of stack)
    _pmap_total[0] = len(_pmap_load_queue)
    if _pmap_total[0] > 0:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Pmap cache: starting background load of {_pmap_total[0]} maps ...",
            Py4GW.Console.MessageType.Info,
        )


def _best_pmap_id_for_group(group_ids: frozenset | set, prefer: int = 0) -> int:
    """Return the best map_id from the group to draw pmap for.

    Priority:
      1. `prefer` (e.g. current_map) if in the group
      2. Explorable-type member with non-empty pmap data
      3. Any member with non-empty pmap data
      4. Smallest ID as deterministic last resort
    """
    if prefer and prefer in group_ids:
        return prefer
    # Pass 1: explorable maps with loaded data take priority over outposts/towns
    for mid in sorted(group_ids):
        meta = _MAP_META.get(mid)
        if meta and meta[0] == _RT_EXPLORABLE:
            e = _PMAP_DATA.get(mid)
            if e and e[1]:
                return mid
    # Pass 2: any member with loaded non-empty trapezoids
    for mid in sorted(group_ids):
        e = _PMAP_DATA.get(mid)
        if e and e[1]:
            return mid
    # Fall back to smallest ID (deterministic)
    return min(group_ids)


def _draw_pmap_for_map(map_id: int, fill_a: int = 60) -> None:
    """Draw pathing trapezoids for *map_id* using the current _s_transform.

    Renders each trapezoid as a filled quad only (no outlines) — at WorldMap
    scale the individual borders are too small to add visual clarity and just
    create noise.  The filled mesh gives a clean "walkable area" silhouette.

    Call this only while a PyImGui draw list is active (i.e. inside _draw_overlay).
    """
    # On-demand load: if this map hasn't been processed by the queue yet,
    # load it immediately so hover always shows data.
    if map_id not in _PMAP_DATA:
        _pmap_cache_for(map_id)

    entry = _PMAP_DATA.get(map_id)
    if not entry:
        return
    bnd = _ICON_BOUNDS.get(map_id)
    if not bnd:
        return
    (gx_min, gx_max, gy_min, gy_max), traps = entry
    gw = gx_max - gx_min
    gh = gy_max - gy_min
    if gw <= 0 or gh <= 0:
        return
    ix1, iy1, ix2, iy2 = bnd
    iw_map = ix2 - ix1
    ih_map = iy2 - iy1

    fill_col = Utils.RGBToColor(80, 160, 255, fill_a)

    # Expand each trapezoid by half a pixel in Y so adjacent rows share no gap.
    _E = 0.6
    for XTL, XTR, XBL, XBR, YT, YB in traps:
        ax, ay = _icon_to_screen(ix1 + (XTL - gx_min) / gw * iw_map,
                                  iy1 + (gy_max - YT) / gh * ih_map)
        bx, by = _icon_to_screen(ix1 + (XTR - gx_min) / gw * iw_map,
                                  iy1 + (gy_max - YT) / gh * ih_map)
        cx, cy = _icon_to_screen(ix1 + (XBR - gx_min) / gw * iw_map,
                                  iy1 + (gy_max - YB) / gh * ih_map)
        dx, dy = _icon_to_screen(ix1 + (XBL - gx_min) / gw * iw_map,
                                  iy1 + (gy_max - YB) / gh * ih_map)
        # Pull top edge up, push bottom edge down
        PyImGui.draw_list_add_quad_filled(ax, ay - _E, bx, by - _E,
                                          cx, cy + _E, dx, dy + _E, fill_col)


def _portal_dest_name(src_map_id: int, pix: float, piy: float) -> str:
    neighbors  = _MAP_NEIGHBORS.get(src_map_id, set())
    best_name  = ""
    best_dist2 = float('inf')
    for nb in neighbors:
        cx, cy = _MAP_CENTROIDS.get(nb, (0.0, 0.0))
        d2 = (cx - pix) ** 2 + (cy - piy) ** 2
        if d2 < best_dist2:
            best_dist2 = d2
            meta = _MAP_META.get(nb)
            best_name = meta[1] if meta else f"Map {nb}"
    return best_name

# ── Portal data loading ────────────────────────────────────────────────────────

def _load_live_portal_cache() -> None:
    global _live_portal_cache
    if not os.path.isfile(_LIVE_PORTAL_CACHE_FILE):
        return
    try:
        with open(_LIVE_PORTAL_CACHE_FILE, "r", encoding="utf-8-sig") as fh:
            raw = json.load(fh)
        _live_portal_cache = {int(k): v for k, v in raw.items()}
        Py4GW.Console.Log(MODULE_NAME,
            f"Live portal cache loaded: {len(_live_portal_cache)} maps.",
            Py4GW.Console.MessageType.Info)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Live portal cache load error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _save_live_portal_cache() -> None:
    """Persist _live_portal_cache to portal_live_cache.json (no-op when recording is off)."""
    if not _record_portals[0]:
        return
    try:
        with open(_LIVE_PORTAL_CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump({str(k): v for k, v in _live_portal_cache.items()}, fh, indent=2)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Live portal cache save error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _portal_link_game_xy(gid: int) -> tuple[float, float]:
    """Return stored game (x, y) for a portal GID, or (0.0, 0.0) if unknown."""
    mid = gid // 1000
    idx = gid %  1000
    dots = _PORTAL_ICON_POS.get(mid, [])
    for dot in dots:
        if len(dot) >= 7 and dot[4] == gid:
            return float(dot[5]), float(dot[6])
    return 0.0, 0.0


def _save_portal_links() -> None:
    """Persist the current _PORTAL_LINKS dict back to portal_links.json and reload."""
    seen: set[tuple[int, int]] = set()
    entries = []
    for a_gid, b_gid in _PORTAL_LINKS.items():
        pair = (min(a_gid, b_gid), max(a_gid, b_gid))
        if pair in seen:
            continue
        seen.add(pair)
        for gid_x, key in ((a_gid, "portal_a"), (b_gid, "portal_b")):
            pass  # built below
        ax, ay = _portal_link_game_xy(a_gid)
        bx, by = _portal_link_game_xy(b_gid)
        entries.append({
            "portal_a": {
                "global_id":    a_gid,
                "map_id":       a_gid // 1000,
                "portal_index": a_gid %  1000,
                "game_x":       ax,
                "game_y":       ay,
            },
            "portal_b": {
                "global_id":    b_gid,
                "map_id":       b_gid // 1000,
                "portal_index": b_gid %  1000,
                "game_x":       bx,
                "game_y":       by,
            },
        })
    try:
        with open(_PORTAL_LINKS_FILE, "w", encoding="utf-8") as fh:
            json.dump({"links": entries}, fh, indent=2)
        _load_portal_links()
        # Re-populate _CONNECTED_MAP_IDS so the overlay reflects the change immediately
        linked_maps = {int(gid // 1000) for gid in _PORTAL_LINKS.keys()}
        _CONNECTED_MAP_IDS.clear()
        _CONNECTED_MAP_IDS.update(linked_maps)
        Py4GW.Console.Log(MODULE_NAME, f"portal_links.json saved ({len(entries)} links).",
                          Py4GW.Console.MessageType.Success)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"portal_links.json save error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _load_portal_all_data() -> None:
    global _PORTAL_ALL_DATA
    _PORTAL_ALL_DATA.clear()
    if not os.path.isfile(_PORTAL_ALL_FILE):
        return
    try:
        with open(_PORTAL_ALL_FILE, "r", encoding="utf-8-sig") as fh:
            raw = json.load(fh)
        maps_raw = raw.get("maps", raw)
        for mk, entries in maps_raw.items():
            try:
                mid = int(mk)
            except Exception:
                continue
            if not isinstance(entries, list):
                continue
            norm_entries: list[dict] = []
            for e in entries:
                if not isinstance(e, dict):
                    continue
                try:
                    idx = int(e.get("portal_index", e.get("index", -1)))
                except Exception:
                    idx = -1
                if idx < 0:
                    continue
                gid = int(e.get("global_id", mid * 1000 + idx))
                obj: dict = {"portal_index": idx, "global_id": gid}
                if "game_x" in e:
                    try: obj["game_x"] = float(e["game_x"])
                    except Exception: pass
                if "game_y" in e:
                    try: obj["game_y"] = float(e["game_y"])
                    except Exception: pass
                if "linked_to" in e:
                    try: obj["linked_to"] = int(e["linked_to"])
                    except Exception: pass
                norm_entries.append(obj)
            if norm_entries:
                norm_entries.sort(key=lambda x: int(x.get("portal_index", 0)))
                _PORTAL_ALL_DATA[mid] = norm_entries
        total = sum(len(v) for v in _PORTAL_ALL_DATA.values())
        Py4GW.Console.Log(MODULE_NAME,
            f"Portal-all loaded: {len(_PORTAL_ALL_DATA)} maps, {total} portals.",
            Py4GW.Console.MessageType.Info)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Portal-all load error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _load_portal_destinations() -> None:
    global _PORTAL_DEST_DATA
    _PORTAL_DEST_DATA.clear()
    dest_file = os.path.join(_SCRIPT_DIR, "portal_destinations.json")
    if os.path.isfile(dest_file):
        try:
            with open(dest_file, "r", encoding="utf-8-sig") as fh:
                raw = json.load(fh)
            for k, entries in raw.get("portals", {}).items():
                _PORTAL_DEST_DATA[int(k)] = entries
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Portal destinations load error: {e}",
                              Py4GW.Console.MessageType.Warning)
    _load_portal_links()

# ── Portal dot builder (lazy, per-map) ────────────────────────────────────────

def _ensure_portal_dots(map_id: int, is_live: bool) -> None:
    if map_id in _PORTAL_BUILT:
        existing = _PORTAL_ICON_POS.get(map_id, [])
        if existing:
            if is_live and not any(len(d) >= 7 for d in existing):
                _PORTAL_BUILT.discard(map_id)
            else:
                return
        else:
            _PORTAL_BUILT.discard(map_id)
    _PORTAL_BUILT.add(map_id)

    icon_bnd = _ICON_BOUNDS.get(map_id)
    if not icon_bnd:
        _PORTAL_ICON_POS[map_id] = []
        return
    ix1, iy1, ix2, iy2 = icon_bnd

    try:
        if is_live:
            pathing_maps = Map.Pathing.GetPathingMaps()
            portals      = Map.Pathing.GetTravelPortals()
        else:
            pathing_maps = FfnaMapMethods.GetPathingMapsForMap(map_id)
            portals      = FfnaMapMethods.GetTravelPortalsForMap(map_id)
            if not portals and map_id in _live_portal_cache:
                from types import SimpleNamespace
                cached = _live_portal_cache[map_id]
                portals = [
                    SimpleNamespace(x=e["x"], y=e["y"], z=e.get("z", 0.0),
                                    model_file_id=e.get("model_file_id", 0))
                    for e in cached.get("portals", cached) if isinstance(e, dict)
                ]
    except Exception:
        _PORTAL_ICON_POS[map_id] = []
        return

    _cached_extents = None
    if map_id in _live_portal_cache:
        ce = _live_portal_cache[map_id]
        if isinstance(ce, dict) and "extents" in ce:
            _cached_extents = ce["extents"]

    has_dat = FfnaMapMethods.HasDatEntry(map_id)

    # Prefer portal_all.json for offline maps, or live maps without a DAT entry
    if (not is_live) or (not portals) or (is_live and not has_dat):
        entries = _PORTAL_ALL_DATA.get(map_id, [])
        if entries:
            ext_ok = False
            gx_min2 = gy_min2 = float('inf')
            gx_max2 = gy_max2 = float('-inf')
            # _MAP_RECT_CACHE has the same live bounds used by the pmap — use it
            # first so portal positions stay in sync with the pmap rendering.
            _rect_gb2 = _MAP_RECT_CACHE.get(map_id)
            if _rect_gb2 is not None:
                gx_min2, gx_max2, gy_min2, gy_max2 = _rect_gb2
                ext_ok = gx_max2 > gx_min2 and gy_max2 > gy_min2
            elif _cached_extents is not None:
                gx_min2 = _cached_extents["gx_min"]; gx_max2 = _cached_extents["gx_max"]
                gy_min2 = _cached_extents["gy_min"]; gy_max2 = _cached_extents["gy_max"]
                ext_ok = gx_max2 > gx_min2 and gy_max2 > gy_min2
            elif pathing_maps:
                _gb2 = _compute_game_bounds(pathing_maps)
                if _gb2:
                    gx_min2, gx_max2, gy_min2, gy_max2 = _gb2
                    ext_ok = gx_max2 > gx_min2 and gy_max2 > gy_min2

            iw_map  = ix2 - ix1
            ih_map  = iy2 - iy1
            cx2     = (ix1 + ix2) * 0.5
            cy2     = (iy1 + iy2) * 0.5
            inset2  = 1.0
            radius2 = max(2.0, min(abs(ix2 - ix1), abs(iy2 - iy1)) * 0.22)

            specs: list[tuple] = []
            for e in entries:
                try:
                    pidx = int(e.get("portal_index", e.get("index", -1)))
                except Exception:
                    continue
                if pidx < 0:
                    continue
                gid = int(e.get("global_id", map_id * 1000 + pidx))
                gx: float | None = float(e["game_x"]) if "game_x" in e else None
                gy: float | None = float(e["game_y"]) if "game_y" in e else None
                linked_gid = int(e.get("linked_to", _PORTAL_LINKS.get(gid, 0)) or 0)
                specs.append((pidx, gid, gx, gy, linked_gid))
            specs.sort(key=lambda x: x[0])

            n_specs  = max(1, len(specs))
            dots_all: list[tuple] = []
            for order, (pidx, gid, gx, gy, linked_gid) in enumerate(specs):
                has_game = gx is not None and gy is not None
                if gx is not None and gy is not None and ext_ok:
                    pdx = ix1 + (gx - gx_min2) / (gx_max2 - gx_min2) * iw_map
                    pdy = iy1 + (gy_max2 - gy) / (gy_max2 - gy_min2) * ih_map
                    pdx = max(ix1, min(ix2, pdx))
                    pdy = max(iy1, min(iy2, pdy))
                else:
                    nb = (linked_gid // 1000) if linked_gid else None
                    nb_center = _MAP_CENTROIDS.get(nb) if nb else None
                    if nb_center:
                        nx, ny = nb_center
                        dx = nx - cx2
                        dy = ny - cy2
                        if dx != 0.0 or dy != 0.0:
                            t_cands: list[float] = []
                            if dx > 0.0:  t_cands.append((ix2 - cx2) / dx)
                            elif dx < 0.0: t_cands.append((ix1 - cx2) / dx)
                            if dy > 0.0:  t_cands.append((iy2 - cy2) / dy)
                            elif dy < 0.0: t_cands.append((iy1 - cy2) / dy)
                            t_hit = min((t for t in t_cands if t > 0.0), default=None)
                            if t_hit is not None:
                                pdx = max(ix1 + inset2, min(ix2 - inset2, cx2 + dx * t_hit))
                                pdy = max(iy1 + inset2, min(iy2 - inset2, cy2 + dy * t_hit))
                            else:
                                pdx, pdy = cx2, cy2
                        else:
                            pdx, pdy = cx2, cy2
                    else:
                        if n_specs == 1:
                            pdx, pdy = cx2, cy2
                        else:
                            ang  = 2.0 * math.pi * order / n_specs
                            pdx = max(ix1, min(ix2, cx2 + radius2 * math.cos(ang)))
                            pdy = max(iy1, min(iy2, cy2 + radius2 * math.sin(ang)))

                key = (map_id, pidx)
                _PORTAL_TO_GLOBAL_ID[key] = gid
                _GLOBAL_ID_TO_PORTAL[gid] = key
                dots_all.append((pdx, pdy, "", pidx, gid, gx, gy) if has_game
                                 else (pdx, pdy, "", pidx, gid))
            if dots_all:
                _PORTAL_ICON_POS[map_id] = dots_all
                return

    if not portals:
        _PORTAL_ICON_POS[map_id] = []
        return

    # Use the same bounds as the pmap so portal positions stay in sync:
    # _MAP_RECT_CACHE > cached extents > FFNA compute
    _rect_gb3 = _MAP_RECT_CACHE.get(map_id)
    if _rect_gb3 is not None:
        gx_min, gx_max, gy_min, gy_max = _rect_gb3
    elif _cached_extents is not None:
        gx_min = _cached_extents["gx_min"]; gx_max = _cached_extents["gx_max"]
        gy_min = _cached_extents["gy_min"]; gy_max = _cached_extents["gy_max"]
    else:
        _gb3 = _compute_game_bounds(pathing_maps) if pathing_maps else None
        if _gb3:
            gx_min, gx_max, gy_min, gy_max = _gb3
        else:
            _PORTAL_ICON_POS[map_id] = []
            return

    if gx_min == float('inf') or gx_max <= gx_min or gy_max <= gy_min:
        _PORTAL_ICON_POS[map_id] = []
        return

    gw     = gx_max - gx_min
    gh     = gy_max - gy_min
    iw_map = ix2 - ix1
    ih_map = iy2 - iy1
    json_entries = _PORTAL_DEST_DATA.get(map_id, [])
    portals_sorted = sorted(portals, key=lambda p: (round(float(p.x), 1), round(float(p.y), 1)))
    dots: list[tuple] = []
    for idx, tp in enumerate(portals_sorted):
        pix = ix1 + (float(tp.x) - gx_min) / gw * iw_map
        piy = iy1 + (gy_max - float(tp.y)) / gh * ih_map
        pix = max(ix1, min(ix2, pix))
        piy = max(iy1, min(iy2, piy))
        json_e = next((e for e in json_entries if e.get("index") == idx), None)
        if json_e and json_e.get("dest_map_id", 0) != 0:
            dest = json_e.get("dest_name") or _map_name_cached(json_e["dest_map_id"])
        else:
            dest = _portal_dest_name(map_id, pix, piy)
        gid = map_id * 1000 + idx
        key = (map_id, idx)
        _PORTAL_TO_GLOBAL_ID[key] = gid
        _GLOBAL_ID_TO_PORTAL[gid] = key
        dots.append((pix, piy, dest, idx, gid, float(tp.x), float(tp.y)))
    _PORTAL_ICON_POS[map_id] = dots
    if is_live and dots and map_id not in _MANUAL_PORTAL_MAPS:
        cache_entry = _live_portal_cache.get(map_id, {})
        if not isinstance(cache_entry, dict):
            cache_entry = {}
        cache_entry["extents"] = {
            "gx_min": gx_min, "gx_max": gx_max,
            "gy_min": gy_min, "gy_max": gy_max,
        }
        # Save the actual map boundaries (start_pos/end_pos) for accurate pmap scaling
        try:
            bx1, by1, bx2, by2 = Map.GetMapBoundaries()
            if bx2 > bx1 and by2 > by1:
                cache_entry["map_rect"] = {
                    "gx_min": float(bx1), "gx_max": float(bx2),
                    "gy_min": float(by1), "gy_max": float(by2),
                }
                # Also persist to the shared adapter file
                _record_map_rect(map_id, float(bx1), float(bx2),
                                 float(by1), float(by2))
        except Exception:
            pass
        _live_portal_cache[map_id] = cache_entry
        _save_live_portal_cache()

# ── Off-map dungeon placement ──────────────────────────────────────────────────

def _inject_offmap_positions() -> None:
    gap = 10
    for mid, (anchor_id, side) in _OFFMAP_PLACEMENTS.items():
        anchor_bnd = _ICON_BOUNDS.get(anchor_id)
        if anchor_bnd is None:
            continue
        al, at, ar, ab = anchor_bnd
        w, h = ar - al, ab - at
        if side == "left":
            bnd = (al - gap - w, at, al - gap, ab)
        elif side == "right":
            bnd = (ar + gap, at, ar + gap + w, ab)
        elif side == "above":
            bnd = (al, at - gap - h, ar, at - gap)
        else:
            bnd = (al, ab + gap, ar, ab + gap + h)
        _ICON_BOUNDS[mid] = bnd
        if mid not in _MAP_META:
            try:
                info  = MapMethods.GetMapInfo(mid)
                name  = Map.GetMapName(mid) or f"Map {mid}"
                rtype = int(info.type) if info else 2
                camp  = int(info.campaign) if info else 4
            except Exception:
                name, rtype, camp = f"Map {mid}", 2, 4
            _MAP_META[mid] = (rtype, name, camp)
        Py4GW.Console.Log(MODULE_NAME,
            f"OffMap: [{mid}] {_MAP_META.get(mid, (None, f'Map {mid}'))[1]} "
            f"placed {side} of {anchor_id}.",
            Py4GW.Console.MessageType.Info)

# ── Cache builder ──────────────────────────────────────────────────────────────

def _build_cache() -> None:
    global _cache_built

    for mid in range(1, _MAX_MAP_ID + 1):
        info = MapMethods.GetMapInfo(mid)
        if info is None:
            _ICON_BOUNDS[mid] = None
            continue

        try:
            raw_name = Map.GetMapName(mid)
        except Exception:
            raw_name = None
        if raw_name and raw_name != "Unknown Map ID":
            _MAP_META[mid] = (int(info.type), raw_name, int(info.campaign))

        if info.icon_start_x != 0 or info.icon_end_x != 0:
            l = float(info.icon_start_x); t = float(info.icon_start_y)
            r = float(info.icon_end_x);   b = float(info.icon_end_y)
        elif info.icon_start_x_dupe != 0 or info.icon_end_x_dupe != 0:
            l = float(info.icon_start_x_dupe); t = float(info.icon_start_y_dupe)
            r = float(info.icon_end_x_dupe);   b = float(info.icon_end_y_dupe)
        else:
            _ICON_BOUNDS[mid] = None
            continue

        if l > r: l, r = r, l
        if t > b: t, b = b, t
        if l == r or t == b:
            _ICON_BOUNDS[mid] = None
            continue
        _ICON_BOUNDS[mid] = (l, t, r, b)

    _inject_offmap_positions()

    # Reset derived data
    _DRAW_GROUPS.clear()
    _PORTAL_ICON_POS.clear()
    _PORTAL_BUILT.clear()
    _GLOBAL_ID_TO_PORTAL.clear()
    _PORTAL_TO_GLOBAL_ID.clear()
    _PORTAL_LINKS.clear()
    _MAP_CENTROIDS.clear()
    _MAP_NEIGHBORS.clear()

    for mid, bnd in _ICON_BOUNDS.items():
        if bnd is not None:
            l, t, r, b = bnd
            _MAP_CENTROIDS[mid] = ((l + r) * 0.5, (t + b) * 0.5)

    for a, b in _ALL_EDGES:
        _MAP_NEIGHBORS.setdefault(a, set()).add(b)
        _MAP_NEIGHBORS.setdefault(b, set()).add(a)

    _bounds_groups: dict[tuple, list[int]] = defaultdict(list)
    for mid, bnd in _ICON_BOUNDS.items():
        if bnd is not None:
            _bounds_groups[bnd].append(mid)

    for bnd, mids in _bounds_groups.items():
        mids.sort()
        meta_list = [_MAP_META[m] for m in mids if m in _MAP_META]
        if not meta_list:
            continue
        rtype = meta_list[0][0]
        camp  = meta_list[0][2]
        lbl   = "\n".join(m[1] for m in meta_list)
        _DRAW_GROUPS.append((frozenset(mids), bnd, lbl, rtype, camp))

    # Inject pmap-shared edges (co-located maps reachable from each other)
    pmap_new_edges = False
    for group_ids, *_ in _DRAW_GROUPS:
        ids = sorted(group_ids)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                edge = (min(a, b), max(a, b))
                if edge not in _ALL_EDGES:
                    _ALL_EDGES.add(edge)
                    _MAP_ADJACENCY.setdefault(a, set()).add(b)
                    _MAP_ADJACENCY.setdefault(b, set()).add(a)
                    _MAP_NEIGHBORS.setdefault(a, set()).add(b)
                    _MAP_NEIGHBORS.setdefault(b, set()).add(a)
                    pmap_new_edges = True
    if pmap_new_edges:
        _wp_invalidate_world_adj()

    _load_map_rect_cache()         # load accumulated boundaries from adapter file
    _load_live_portal_cache()
    _load_portal_destinations()   # also calls _load_portal_links() at the end
    _load_portal_all_data()

    linked_maps = {int(gid // 1000) for gid in _PORTAL_LINKS.keys()}
    _CONNECTED_MAP_IDS.clear()
    _CONNECTED_MAP_IDS.update(linked_maps)

    # Inject map-level edges from portal_links.json into _MAP_NEIGHBORS so
    # that GetPath() can traverse connections that are not in _MAP_ADJACENCY.
    for exit_gid, enter_gid in _PORTAL_LINKS.items():
        m_from = exit_gid  // 1000
        m_to   = enter_gid // 1000
        if m_from != m_to:
            _MAP_NEIGHBORS.setdefault(m_from, set()).add(m_to)
            _MAP_NEIGHBORS.setdefault(m_to,   set()).add(m_from)

    _cache_built = True
    n = sum(1 for v in _ICON_BOUNDS.values() if v is not None)
    Py4GW.Console.Log(MODULE_NAME,
        f"Cache built: {n} maps with icon bounds, {len(_DRAW_GROUPS)} draw groups.",
        Py4GW.Console.MessageType.Info)

# ── Path query ────────────────────────────────────────────────────────────────

def GetPath(map_id_a: int, map_id_b: int) -> list | bool:
    """Return the portal path from map_id_a to map_id_b, or False if none exists.

    Return format (alternating map IDs and portal GID pairs):
        [map_a, exit_gid, enter_gid, map_2, exit_gid_2, enter_gid_2, ..., map_b]

    The first element is always map_id_a, the last is always map_id_b.
    Each hop contributes: exit portal GID (from current map), enter portal GID
    (into next map).  Portal GIDs are map_id * 1000 + portal_index.

    Returns False if no path exists or the cache has not been built yet.
    Returns [map_id_a] if map_id_a == map_id_b.

    Only traverses edges that have real portal GIDs (no 0-placeholders).
    """
    if map_id_a == map_id_b:
        return [map_id_a]
    if not _MAP_NEIGHBORS:
        return False

    # Build edge→portal lookup from ALL available data sources:
    # 1. _PORTAL_LINKS (portal_links.json, bidirectional)
    # 2. _PORTAL_ALL_DATA (portal_all.json, linked_to field)
    # This maximises coverage beyond what either file alone provides.
    edge_portals: dict[tuple[int, int], tuple[int, int]] = {}

    for exit_gid, enter_gid in _PORTAL_LINKS.items():
        m_from = exit_gid  // 1000
        m_to   = enter_gid // 1000
        if (m_from, m_to) not in edge_portals:
            edge_portals[(m_from, m_to)] = (exit_gid, enter_gid)

    for mid, entries in _PORTAL_ALL_DATA.items():
        for e in entries:
            exit_gid  = e.get("global_id", 0)
            enter_gid = e.get("linked_to", 0)
            if not exit_gid or not enter_gid:
                continue
            m_from = exit_gid  // 1000
            m_to   = enter_gid // 1000
            if m_from != mid:
                continue
            if (m_from, m_to) not in edge_portals:
                edge_portals[(m_from, m_to)] = (exit_gid, enter_gid)

    if not edge_portals:
        return False

    def _edge(m_from: int, m_to: int) -> tuple[int, int] | None:
        ep = edge_portals.get((m_from, m_to))
        if ep:
            return ep
        ep = edge_portals.get((m_to, m_from))
        if ep:
            return ep[1], ep[0]   # reverse: enter becomes exit
        return None

    # BFS; only traverse edges that have real portal GIDs.
    # Edges without GID data are skipped so we never produce a path with
    # placeholder zeros that would cause MoveToMapID to fail.
    visited: set[int] = {map_id_a}
    queue: list[tuple[int, list]] = [(map_id_a, [map_id_a])]

    while queue:
        current, path = queue.pop(0)
        for neighbor in _MAP_NEIGHBORS.get(current, ()):
            if neighbor in visited:
                continue
            ep = _edge(current, neighbor)
            if ep is None:
                continue   # no portal data → skip this edge
            exit_g, enter_g = ep
            new_path = path + [exit_g, enter_g, neighbor]
            if neighbor == map_id_b:
                return new_path
            visited.add(neighbor)
            queue.append((neighbor, new_path))

    return False


def _get_portal_game_xy(gid: int) -> tuple[float, float] | tuple[None, None]:
    """Return (game_x, game_y) for a portal GID.

    Checks _PORTAL_ICON_POS first (live/rendered maps), then falls back to
    _PORTAL_ALL_DATA (portal_all.json, loaded at startup) so that remote
    maps along a route can also provide portal coordinates.
    """
    mid = gid // 1000
    for dot in _PORTAL_ICON_POS.get(mid, []):
        if len(dot) >= 7 and dot[4] == gid and dot[5] is not None and dot[6] is not None:
            return float(dot[5]), float(dot[6])
    # Fallback: pre-loaded portal_all.json
    for entry in _PORTAL_ALL_DATA.get(mid, []):
        if entry.get("global_id") == gid and "game_x" in entry and "game_y" in entry:
            return float(entry["game_x"]), float(entry["game_y"])
    return None, None


def _best_gb_for(map_id: int) -> tuple[float, float, float, float] | None:
    """Return the best available game bounds for map_id (same priority as _draw_pmap_for_map)."""
    gb = _MAP_RECT_CACHE.get(map_id)
    if gb:
        return gb
    pmap_e = _PMAP_DATA.get(map_id)
    if pmap_e:
        gx_min, gx_max, gy_min, gy_max = pmap_e[0]
        if gx_max > gx_min and gy_max > gy_min:
            return pmap_e[0]
    return None


def _game_to_icon(map_id: int, gx: float, gy: float) -> tuple[float, float] | None:
    """Convert a single game-space point to icon-space for map_id.

    Uses _MAP_RECT_CACHE > _PMAP_DATA > FfnaMapMethods for game bounds.
    Returns None when no valid bounds exist for the map.
    """
    icon_bnd = _ICON_BOUNDS.get(map_id)
    if not icon_bnd:
        return None
    ix1, iy1, ix2, iy2 = icon_bnd
    iw = ix2 - ix1
    ih = iy2 - iy1

    gb = _best_gb_for(map_id)
    if gb is None:
        _gti_cached = _PMAP_DATA.get(map_id)
        if _gti_cached and _gti_cached[0][0] != 0.0:
            gb = _gti_cached[0]
    if gb is None:
        return None

    gx_min, gx_max, gy_min, gy_max = gb
    gw = gx_max - gx_min
    gh = gy_max - gy_min
    if gw <= 0.0 or gh <= 0.0:
        return None

    return (ix1 + (gx - gx_min) / gw * iw,
            iy1 + (gy_max - gy) / gh * ih)


def _portal_icon_xy(gid: int) -> tuple[float, float] | None:
    """Return icon-space (ix, iy) for portal GID, loading dot data if needed."""
    mid = gid // 1000
    if mid not in _PORTAL_BUILT:
        try:
            _ensure_portal_dots(mid, is_live=(mid == Map.GetMapID()))
        except Exception:
            pass
    for dot in _PORTAL_ICON_POS.get(mid, []):
        if len(dot) >= 5 and dot[4] == gid:
            return float(dot[0]), float(dot[1])
    return None


def _compute_route_hops(path: list[int]) -> None:
    """Compute A* walking paths for every hop and store icon-space polylines.

    Uses ONLY already-cached pmap data (_PMAP_DATA / live pathing maps) —
    never loads from disk synchronously.  Hops whose pmap is not yet cached
    are skipped; _tick_pmap_loader will set _route_hops_dirty when that data
    arrives so the hop is filled in on the next recompute.
    """
    from Py4GWCoreLib.Pathing import NavMesh, AStar

    _route_hops.clear()
    current_map = Map.GetMapID()

    # Pre-populate portal dots using already-cached data only
    for item in path:
        if 0 < item < 1000 and item not in _PORTAL_BUILT:
            try:
                _ensure_portal_dots(item, is_live=(item == current_map))
            except Exception:
                pass

    # Start position: player game XY on current map
    try:
        from Py4GWCoreLib.Player import Player as _Player
        px, py = _Player.GetXY()
        start_game: tuple[float, float] | None = (float(px), float(py))
    except Exception:
        start_game = None

    i = 0
    while i < len(path):
        item = path[i]
        if 0 < item < 1000 and i + 2 < len(path):
            map_id   = item
            exit_gid = path[i + 1]

            goal_gx, goal_gy = _get_portal_game_xy(exit_gid)
            goal_game: tuple[float, float] | None = (
                (float(goal_gx), float(goal_gy))
                if goal_gx is not None and goal_gy is not None else None
            )

            # Use cached pmap data only — no synchronous disk loads
            gb: tuple[float, float, float, float] | None = _best_gb_for(map_id)
            if map_id == current_map:
                pmaps = Map.Pathing.GetPathingMaps()
                if gb is None:
                    gb = _compute_game_bounds(pmaps) if pmaps else None
            else:
                pmaps = _PATHING_MAPS_CACHE.get(map_id, [])
                if pmaps and gb is None:
                    cached_entry = _PMAP_DATA.get(map_id)
                    if cached_entry:
                        gb = cached_entry[0]

            # Compute icon-space polyline
            icon_pts: list[tuple[float, float]] = []

            if gb and pmaps and start_game and goal_game:
                try:
                    nm    = NavMesh(pmaps, map_id)
                    astar = AStar(nm)
                    if astar.search(start_game, goal_game):
                        game_pts = [(float(p[0]), float(p[1])) for p in astar.path]
                    else:
                        game_pts = [start_game, goal_game]
                    for gx2, gy2 in game_pts:
                        ip = _game_to_icon(map_id, gx2, gy2)
                        if ip is not None:
                            if not icon_pts or abs(icon_pts[-1][0]-ip[0]) > 0.3 or abs(icon_pts[-1][1]-ip[1]) > 0.3:
                                icon_pts.append(ip)
                except Exception as exc:
                    Py4GW.Console.Log(MODULE_NAME,
                        f"_compute_route_hops A* map {map_id}: {exc}",
                        Py4GW.Console.MessageType.Warning)

            # Fallback: straight icon-space line between portal positions
            if len(icon_pts) < 2:
                icon_pts = []
                if start_game:
                    ip_s = _game_to_icon(map_id, start_game[0], start_game[1])
                    if ip_s:
                        icon_pts.append(ip_s)
                ip_g = _portal_icon_xy(exit_gid)
                if ip_g:
                    icon_pts.append(ip_g)

            if len(icon_pts) >= 2:
                _route_hops.append((map_id, icon_pts))

            # Advance start to enter portal of next map
            enter_gid = path[i + 2]
            ex, ey = _get_portal_game_xy(enter_gid)
            start_game = (float(ex), float(ey)) if ex is not None and ey is not None else goal_game
            i += 3
        else:
            i += 1


def MoveToMapID(target_map_id: int, pause_on_combat: bool = True):
    """Build and start a BottingTree that walks the player to target_map_id.

    Uses BottingTree so that HeroAI runs during travel and combat pauses
    movement automatically when pause_on_combat=True.

    Returns a started BottingTree instance, or False on failure.
    The caller should call bt.tick() every frame and stop when bt.started==False.
    """
    from Py4GWCoreLib.BottingTree import BottingTree
    from Py4GWCoreLib.routines_src.behaviourtrees_src.movement import BTMovement
    from Py4GWCoreLib.routines_src.behaviourtrees_src.composite import BTComposite

    if not _cache_built:
        Py4GW.Console.Log(MODULE_NAME, "MoveToMapID: cache not built yet.",
                          Py4GW.Console.MessageType.Warning)
        return False

    current_map = Map.GetMapID()
    path = GetPath(current_map, target_map_id)

    if not isinstance(path, list):
        t_name = (_MAP_META.get(target_map_id) or (None, f"Map {target_map_id}"))[1]
        Py4GW.Console.Log(MODULE_NAME,
            f"MoveToMapID: no path from map {current_map} to [{target_map_id}] {t_name}.",
            Py4GW.Console.MessageType.Warning)
        return False

    t_name = (_MAP_META.get(target_map_id) or (None, f"Map {target_map_id}"))[1]

    if len(path) == 1:
        Py4GW.Console.Log(MODULE_NAME, f"MoveToMapID: already at [{target_map_id}] {t_name}.",
                          Py4GW.Console.MessageType.Info)
        return False

    steps: list = []
    i = 0
    while i < len(path):
        item = path[i]
        if 0 < item < 1000 and i + 3 < len(path):
            exit_gid = path[i + 1]
            next_mid = path[i + 3]
            if exit_gid == 0:
                Py4GW.Console.Log(MODULE_NAME,
                    f"MoveToMapID: missing portal GID between map {item} and {next_mid}.",
                    Py4GW.Console.MessageType.Warning)
                return False
            gx, gy = _get_portal_game_xy(exit_gid)
            if gx is None or gy is None:
                Py4GW.Console.Log(MODULE_NAME,
                    f"MoveToMapID: no game coords for portal {exit_gid} in map {item}.",
                    Py4GW.Console.MessageType.Warning)
                return False
            steps.append(
                BTMovement.MoveAndExitMap(
                    x=gx,
                    y=gy,
                    target_map_id=next_mid,
                    pause_on_combat=pause_on_combat,
                )
            )
            i += 3
        else:
            i += 1

    if not steps:
        Py4GW.Console.Log(MODULE_NAME, "MoveToMapID: path produced no movement steps.",
                          Py4GW.Console.MessageType.Warning)
        return False

    movement_sequence = BTComposite.Sequence(
        *steps, name=f"MoveToMapID [{target_map_id}] {t_name}"
    )

    bt = BottingTree.Create(
        bot_name=f"WorldMap+ Nav → {t_name}",
        main_routine=movement_sequence,
        routine_name=f"Route to [{target_map_id}]",
        pause_on_combat=pause_on_combat,
        auto_loot=True,
        auto_resurrection_scroll=False,
        auto_start=True,
    )

    Py4GW.Console.Log(MODULE_NAME,
        f"MoveToMapID: started {len(steps)}-step BottingTree to [{target_map_id}] {t_name}. "
        f"HeroAI active, pause_on_combat={pause_on_combat}.",
        Py4GW.Console.MessageType.Info)
    return bt


def MoveToMapIDCoords(
    target_map_id: int,
    dest_x: float,
    dest_y: float,
    tolerance: float = 200.0,
    pause_on_combat: bool = True,
):
    """Navigate to target_map_id and then walk to (dest_x, dest_y) within that map.

    Builds a BottingTree Sequence of:
      1-N. MoveAndExitMap steps along the portal route  (same as MoveToMapID)
      N+1. BTMovement.Move to the final in-map coordinates

    Returns a started BottingTree, or False on failure.
    """
    from Py4GWCoreLib.BottingTree import BottingTree
    from Py4GWCoreLib.routines_src.behaviourtrees_src.movement import BTMovement
    from Py4GWCoreLib.routines_src.behaviourtrees_src.composite import BTComposite

    if not _cache_built:
        Py4GW.Console.Log(MODULE_NAME, "MoveToMapIDCoords: cache not built yet.",
                          Py4GW.Console.MessageType.Warning)
        return False

    current_map = Map.GetMapID()
    t_name = (_MAP_META.get(target_map_id) or (None, f"Map {target_map_id}"))[1]

    steps: list = []

    # ── Inter-map travel steps (skipped when already on target map) ────────────
    if current_map != target_map_id:
        path = GetPath(current_map, target_map_id)
        if not isinstance(path, list):
            Py4GW.Console.Log(MODULE_NAME,
                f"MoveToMapIDCoords: no path from map {current_map} to [{target_map_id}] {t_name}.",
                Py4GW.Console.MessageType.Warning)
            return False

        i = 0
        while i < len(path):
            item = path[i]
            if 0 < item < 1000 and i + 3 < len(path):
                exit_gid = path[i + 1]
                next_mid  = path[i + 3]
                if exit_gid == 0:
                    Py4GW.Console.Log(MODULE_NAME,
                        f"MoveToMapIDCoords: missing portal GID between map {item} and {next_mid}.",
                        Py4GW.Console.MessageType.Warning)
                    return False
                gx, gy = _get_portal_game_xy(exit_gid)
                if gx is None or gy is None:
                    Py4GW.Console.Log(MODULE_NAME,
                        f"MoveToMapIDCoords: no game coords for portal {exit_gid} in map {item}.",
                        Py4GW.Console.MessageType.Warning)
                    return False
                steps.append(
                    BTMovement.MoveAndExitMap(
                        x=gx,
                        y=gy,
                        target_map_id=next_mid,
                        pause_on_combat=pause_on_combat,
                    )
                )
                i += 3
            else:
                i += 1

        if not steps:
            Py4GW.Console.Log(MODULE_NAME,
                "MoveToMapIDCoords: path produced no movement steps.",
                Py4GW.Console.MessageType.Warning)
            return False

    # ── Final in-map walk step ─────────────────────────────────────────────────
    steps.append(
        BTMovement.Move(
            x=dest_x,
            y=dest_y,
            tolerance=tolerance,
            pause_on_combat=pause_on_combat,
        )
    )

    movement_sequence = BTComposite.Sequence(
        *steps, name=f"MoveToMapIDCoords [{target_map_id}] {t_name} ({dest_x:.0f},{dest_y:.0f})"
    )

    bt = BottingTree.Create(
        bot_name=f"WorldMap+ Nav → {t_name} ({dest_x:.0f},{dest_y:.0f})",
        main_routine=movement_sequence,
        routine_name=f"Route to [{target_map_id}] + walk",
        pause_on_combat=pause_on_combat,
        auto_loot=False,
        auto_resurrection_scroll=False,
        auto_start=True,
    )

    Py4GW.Console.Log(MODULE_NAME,
        f"MoveToMapIDCoords: started {len(steps)}-step BottingTree to "
        f"[{target_map_id}] {t_name} then walk to ({dest_x:.0f},{dest_y:.0f}). "
        f"pause_on_combat={pause_on_combat}.",
        Py4GW.Console.MessageType.Info)
    return bt


# ── Context-popup helpers ──────────────────────────────────────────────────────

def _ctx_do_move_to_coords(mid: int, dx: float, dy: float) -> None:
    """Start MoveToMapIDCoords + build path visualization for the context popup."""
    cur = Map.GetMapID()
    if _active_move_tree[0] is not None:
        try:
            _active_move_tree[0].Stop()
        except Exception:
            pass
    tree = MoveToMapIDCoords(mid, dx, dy)
    if tree is False:
        return
    _active_move_tree[0] = tree
    path = GetPath(cur, mid)
    _active_move_path[:] = path if isinstance(path, list) else []
    _compute_route_hops(_active_move_path)  # safe: uses cached data only
    dest_ip = _game_to_icon(mid, dx, dy)
    if dest_ip is None:
        return
    if _route_hops:
        # Cross-map: A* from entry portal into target map → clicked dest
        enter_gx: float | None = None
        enter_gy: float | None = None
        enter_ip: tuple[float, float] | None = None
        if len(_active_move_path) >= 2:
            eg = _active_move_path[-2]
            if isinstance(eg, int) and eg > 999:
                enter_gx, enter_gy = _get_portal_game_xy(eg)
                enter_ip = _portal_icon_xy(eg)
        xpts: list[tuple[float, float]] = []
        try:
            from Py4GWCoreLib.Pathing import NavMesh, AStar
            # Use cached pmap data only — no synchronous disk load
            xpmaps = _PATHING_MAPS_CACHE.get(mid, [])
            xgb = _best_gb_for(mid)
            if xgb is None:
                _xcached = _PMAP_DATA.get(mid)
                if _xcached:
                    xgb = _xcached[0]
            if xgb and xpmaps and enter_gx is not None and enter_gy is not None:
                xnm    = NavMesh(xpmaps, mid)
                xastar = AStar(xnm)
                xstart = (float(enter_gx), float(enter_gy))
                xgoal  = (dx, dy)
                if xastar.search(xstart, xgoal):
                    xgpts = [(float(p[0]), float(p[1])) for p in xastar.path]
                else:
                    xgpts = [xstart, xgoal]
                for xgx, xgy in xgpts:
                    xip = _game_to_icon(mid, xgx, xgy)
                    if xip is not None:
                        if not xpts or abs(xpts[-1][0]-xip[0]) > 0.3 or abs(xpts[-1][1]-xip[1]) > 0.3:
                            xpts.append(xip)
        except Exception:
            pass
        if len(xpts) < 2:
            xpts = [enter_ip, dest_ip] if enter_ip else [dest_ip]
        if xpts:
            _route_hops.append((mid, xpts))
    else:
        # Same map: A* from player position → clicked dest
        try:
            from Py4GWCoreLib.Pathing import NavMesh, AStar
            from Py4GWCoreLib.Player import Player as _CtxPlayer
            px, py = _CtxPlayer.GetXY()
            pmaps  = Map.Pathing.GetPathingMaps()
            gb     = _best_gb_for(mid)
            if gb is None and pmaps:
                gb = _compute_game_bounds(pmaps)
            ipts: list[tuple[float, float]] = []
            if gb and pmaps:
                nm    = NavMesh(pmaps, mid)
                astar = AStar(nm)
                if astar.search((float(px), float(py)), (dx, dy)):
                    for gx, gy in [(float(p[0]), float(p[1])) for p in astar.path]:
                        ip = _game_to_icon(mid, gx, gy)
                        if ip is not None:
                            if not ipts or abs(ipts[-1][0]-ip[0]) > 0.3 or abs(ipts[-1][1]-ip[1]) > 0.3:
                                ipts.append(ip)
            if len(ipts) < 2:
                sip  = _game_to_icon(mid, float(px), float(py))
                ipts = [sip, dest_ip] if sip else [dest_ip]
            if ipts:
                _route_hops.append((mid, ipts))
        except Exception:
            _route_hops.append((mid, [dest_ip]))


def _apply_path_to_map(target_mid: int) -> None:
    """Store the WorldMap path for a single target map and compute hops once."""
    path = GetPath(Map.GetMapID(), target_mid)
    _active_move_path[:] = path if isinstance(path, list) else []
    _compute_route_hops(_active_move_path)


def _apply_queue_path(queue: list[int]) -> None:
    """Build and store a chained WorldMap path for all maps in the queue.

    Produces a single continuous _active_move_path by stitching together
    GetPath segments: current_map -> queue[0] -> queue[1] -> ...
    Hops are computed once with currently cached pmap data; no recompute later.
    """
    if not queue:
        _active_move_path.clear()
        _route_hops.clear()
        return
    combined: list = []
    prev = Map.GetMapID()
    for qmid in queue:
        if qmid == prev:
            continue
        seg = GetPath(prev, qmid)
        if not isinstance(seg, list) or not seg:
            break
        if combined:
            start = 1 if seg[0] == combined[-1] else 0
            combined.extend(seg[start:])
        else:
            combined.extend(seg)
        prev = qmid
    _active_move_path[:] = combined
    _compute_route_hops(_active_move_path)


# ── Overlay draw ───────────────────────────────────────────────────────────────

def _draw_overlay() -> None:
    if not Map.WorldMap.IsWindowOpen():
        return
    if not _zoom_is_default():
        return

    frame_info = Map.WorldMap.GetFrameInfo()
    if frame_info is None:
        return
    sc = frame_info.GetContentCoords()
    if not sc or sc[2] <= sc[0] or sc[3] <= sc[1]:
        return
    sl, st, sr, sb = float(sc[0]), float(sc[1]), float(sc[2]), float(sc[3])
    sw = sr - sl
    sh = sb - st

    il, it, ir, ib = Map.WorldMap.GetWindowCoords()
    iw = ir - il
    ih = ib - it
    if iw == 0.0 or ih == 0.0:
        return

    def _i2s(ix: float, iy: float) -> tuple[float, float]:
        return sl + (ix - il) / iw * sw, st + (iy - it) / ih * sh

    # Update the module-level transform so _draw_pmap_for_map can use it
    _s_transform[0] = sl
    _s_transform[1] = st
    _s_transform[2] = il
    _s_transform[3] = it
    _s_transform[4] = sw / iw if iw else 1.0
    _s_transform[5] = sh / ih if ih else 1.0

    alpha        = max(10, min(255, int(_opacity[0] * 255)))
    alpha_border = min(255, alpha + 60)
    current_map  = Map.GetMapID()

    # Refresh live map boundaries every frame for the current map.
    # _record_map_rect is a no-op when bounds are unchanged, but when they differ
    # it invalidates the stale pmap cache entry so the next draw uses correct scaling.
    try:
        _bx1, _by1, _bx2, _by2 = Map.GetMapBoundaries()
        if _bx2 > _bx1 and _by2 > _by1:
            _record_map_rect(current_map, float(_bx1), float(_bx2), float(_by1), float(_by2))
    except Exception:
        pass

    cur_border   = Utils.RGBToColor(255, 255, 100, 255)
    link_color   = Utils.RGBToColor(255, 220, 60, int(alpha * 0.85))
    lbl_color    = Utils.RGBToColor(255, 255, 255, min(255, alpha + 80))

    current_camp_group = 1
    cur_meta = _MAP_META.get(current_map)
    if cur_meta:
        current_camp_group = _campaign_group(cur_meta[2])
    else:
        try:
            ci = MapMethods.GetMapInfo(current_map)
            if ci:
                current_camp_group = _campaign_group(int(ci.campaign))
        except Exception:
            pass

    ow_flags = (
        PyImGui.WindowFlags.NoTitleBar        |
        PyImGui.WindowFlags.NoResize          |
        PyImGui.WindowFlags.NoMove            |
        PyImGui.WindowFlags.NoScrollbar       |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.NoCollapse        |
        PyImGui.WindowFlags.NoBackground      |
        PyImGui.WindowFlags.NoMouseInputs     |
        PyImGui.WindowFlags.NoSavedSettings
    )
    PyImGui.set_next_window_pos(sl, st)
    PyImGui.set_next_window_size(sw, sh)
    if not PyImGui.begin("##wm_plus_overlay", ow_flags):
        PyImGui.end()
        return

    current_highlight_drawn = False
    _io = PyImGui.get_io()
    mx, my = _io.mouse_pos_x, _io.mouse_pos_y

    # ── Right-click → context popup ───────────────────────────────────────
    # Collect ALL overlapping map frames under the cursor and open a popup.
    # The heavy movement logic runs only when the user picks an action inside.
    if PyImGui.is_mouse_clicked(1):
        _rc2_ix, _rc2_iy = _screen_to_icon(mx, my)
        _rc2_hits: list[tuple[int, float, float]] = []  # (map_id, dest_x, dest_y)
        _rc2_seen_mids: set[int] = set()
        for _rc2_gids, _rc2_bounds, _, _rc2_rtype, _rc2_camp in _DRAW_GROUPS:
            if _rc2_rtype not in _STANDARD_RTYPES:
                continue
            if _campaign_group(_rc2_camp) != current_camp_group:
                continue
            _rc2_l, _rc2_t, _rc2_r, _rc2_b = _rc2_bounds
            if not (_rc2_l <= _rc2_ix <= _rc2_r and _rc2_t <= _rc2_iy <= _rc2_b):
                continue
            _rc2_camp_ids = [
                mid for mid in _rc2_gids
                if _campaign_group((_MAP_META.get(mid) or (None, None, _rc2_camp))[2])
                   == current_camp_group
            ]
            if not _rc2_camp_ids:
                continue

            # Add every individual map ID from this group separately
            for _rc2_mid2 in _rc2_camp_ids:
                if _rc2_mid2 in _rc2_seen_mids:
                    continue
                _rc2_seen_mids.add(_rc2_mid2)

                # Pre-compute nearest trapezoid; prefer own pmap, fall back to group best
                _rc2_dx2, _rc2_dy2 = 0.0, 0.0
                _rc2_lookup = _rc2_mid2
                _rc2_e2 = _PMAP_DATA.get(_rc2_lookup)
                if not (_rc2_e2 and _rc2_e2[1]):
                    # No pmap for this individual ID — try the best representative
                    _rc2_lookup = _best_pmap_id_for_group(frozenset(_rc2_camp_ids))
                    _rc2_e2 = _PMAP_DATA.get(_rc2_lookup)
                if _rc2_e2 and _rc2_e2[1]:
                    (_rc2_gxmn, _rc2_gxmx, _rc2_gymn, _rc2_gymx), _ = _rc2_e2
                    _rc2_gw2 = _rc2_gxmx - _rc2_gxmn
                    _rc2_gh2 = _rc2_gymx - _rc2_gymn
                    _rc2_iw2 = _rc2_r - _rc2_l
                    _rc2_ih2 = _rc2_b - _rc2_t
                    if _rc2_gw2 > 0 and _rc2_gh2 > 0 and _rc2_iw2 > 0 and _rc2_ih2 > 0:
                        _rc2_gxc = _rc2_gxmn + (_rc2_ix - _rc2_l) / _rc2_iw2 * _rc2_gw2
                        _rc2_gyc = _rc2_gymx - (_rc2_iy - _rc2_t) / _rc2_ih2 * _rc2_gh2
                        _rc2_dest2 = _nearest_trap_game_xy(_rc2_lookup, _rc2_gxc, _rc2_gyc)
                        if _rc2_dest2 is not None:
                            _rc2_dx2, _rc2_dy2 = _rc2_dest2
                # Skip maps that are not reachable from the current map via portals
                _rc2_cur_map = Map.GetMapID()
                if _rc2_mid2 != _rc2_cur_map and not GetPath(_rc2_cur_map, _rc2_mid2):
                    continue
                _rc2_hits.append((_rc2_mid2, _rc2_dx2, _rc2_dy2))

        if _rc2_hits:
            _ctx_entries[:] = _rc2_hits
            _ctx_click_sx[0] = mx
            _ctx_click_sy[0] = my
            if _rclick_active[0]:
                PyImGui.open_popup("##wmp_map_ctx")

    # ── Pass 1: map rectangles + labels ───────────────────────────────────
    for group_ids, bounds, group_label, rtype, camp in _DRAW_GROUPS:
        if _campaign_group(camp) != current_camp_group:
            continue
        if rtype not in _STANDARD_RTYPES:
            continue

        l, t, r, b = bounds
        x1, y1 = _i2s(l, t)
        x2, y2 = _i2s(r, b)
        is_current = current_map in group_ids

        if not is_current and (x2 < sl or x1 > sr or y2 < st or y1 > sb):
            continue

        if not is_current and not _show_unconnected[0]:
            has_portals = any(mid in _CONNECTED_MAP_IDS for mid in group_ids)
            if not has_portals:
                continue

        is_hovered = x1 <= mx <= x2 and y1 <= my <= y2

        if is_current:
            if _show_navmesh[0]:
                _pmap_mid = _best_pmap_id_for_group(group_ids, current_map)
                _draw_pmap_for_map(_pmap_mid, fill_a=70)
            PyImGui.draw_list_add_rect(x1, y1, x2, y2, cur_border, 2.0, 0, 2.0)
            current_highlight_drawn = True
        else:
            if is_hovered:
                if _show_navmesh[0]:
                    _pmap_mid = _best_pmap_id_for_group(group_ids)
                    _draw_pmap_for_map(_pmap_mid, fill_a=55)
                if _show_frames[0]:
                    PyImGui.draw_list_add_rect(x1, y1, x2, y2,
                                               _type_border(rtype, alpha_border), 1.0, 0, 1.0)

        if _show_labels[0] and (min(abs(x2 - x1), abs(y2 - y1)) >= 14 or is_current):
            sorted_ids = sorted(group_ids)
            for i, line in enumerate(group_label.split("\n")):
                mid = sorted_ids[i] if i < len(sorted_ids) else -1
                raw = f"{line} [{mid}]" if mid >= 0 else line
                PyImGui.draw_list_add_text(x1 + 2.0, y1 + 2.0 + i * 13.0, lbl_color, raw)

    # Fallback: always draw current map highlight even when filtered
    if not current_highlight_drawn:
        cur_bnd = _ICON_BOUNDS.get(current_map)
        if cur_bnd is not None:
            l, t, r, b = cur_bnd
            x1, y1 = _i2s(l, t)
            x2, y2 = _i2s(r, b)
            if not (x2 < sl or x1 > sr or y2 < st or y1 > sb):
                if _show_navmesh[0]:
                    _draw_pmap_for_map(_best_pmap_id_for_group({current_map}, current_map), fill_a=70)
                PyImGui.draw_list_add_rect(x1, y1, x2, y2, cur_border, 2.0, 0, 2.0)
                if _show_labels[0]:
                    cur_meta2 = _MAP_META.get(current_map)
                    cur_name  = cur_meta2[1] if cur_meta2 else f"Map {current_map}"
                    PyImGui.draw_list_add_text(
                        x1 + 2.0, y1 + 2.0, lbl_color,
                        f"{cur_name} [{current_map}]")

    # ── Pass 2: connection lines between linked portal pairs ───────────────
    if _show_connections[0] and _PORTAL_LINKS:
        visible_portal_sx: dict[int, tuple[float, float]] = {}

        for group_ids, bounds, _, _, camp in _DRAW_GROUPS:
            if _campaign_group(camp) != current_camp_group:
                continue
            l, t, r, b = bounds
            x1, y1 = _i2s(l, t)
            x2, y2 = _i2s(r, b)
            if x2 < sl or x1 > sr or y2 < st or y1 > sb:
                continue
            for mid in group_ids:
                _ensure_portal_dots(mid, is_live=(mid == current_map))
                for dot in _PORTAL_ICON_POS.get(mid, []):
                    if len(dot) >= 5:
                        gid2 = dot[4]
                        if gid2 and gid2 not in visible_portal_sx:
                            sx2, sy2 = _i2s(float(dot[0]), float(dot[1]))
                            visible_portal_sx[gid2] = (sx2, sy2)

        # Also resolve off-screen portals – but only within the current campaign
        for a_id, b_id in list(_PORTAL_LINKS.items()):
            for pid in (a_id, b_id):
                if pid not in visible_portal_sx:
                    mid2 = pid // 1000
                    meta2 = _MAP_META.get(mid2)
                    if meta2 and _campaign_group(meta2[2]) != current_camp_group:
                        continue
                    bnd2 = _ICON_BOUNDS.get(mid2)
                    if bnd2:
                        _ensure_portal_dots(mid2, is_live=(mid2 == current_map))
                        for dot in _PORTAL_ICON_POS.get(mid2, []):
                            if len(dot) >= 5 and dot[4] == pid:
                                sx2, sy2 = _i2s(float(dot[0]), float(dot[1]))
                                visible_portal_sx[pid] = (sx2, sy2)
                                break

        drawn_pairs: set[tuple[int, int]] = set()
        for a_id, b_id in _PORTAL_LINKS.items():
            pair = (min(a_id, b_id), max(a_id, b_id))
            if pair in drawn_pairs:
                continue
            drawn_pairs.add(pair)
            pa = visible_portal_sx.get(a_id)
            pb = visible_portal_sx.get(b_id)
            if pa and pb:
                PyImGui.draw_list_add_line(pa[0], pa[1], pb[0], pb[1], link_color, 1.5)

    # ── Pass 3: portal dots ────────────────────────────────────────────────
    if _show_portals[0]:
        linked_col   = Utils.RGBToColor( 60, 210,  60, 230)
        linked_rim   = Utils.RGBToColor(180, 255, 180, 255)
        unlinked_col = Utils.RGBToColor(255, 180,  30, 200)
        unlinked_rim = Utils.RGBToColor(255, 230, 120, 255)

        # (sx, sy, gid) for tooltip proximity check
        drawn_dots: list[tuple[float, float, int]] = []

        for group_ids, bounds, _, _, camp in _DRAW_GROUPS:
            if _campaign_group(camp) != current_camp_group:
                continue
            l, t, r, b = bounds
            x1, y1 = _i2s(l, t)
            x2, y2 = _i2s(r, b)
            if x2 < sl or x1 > sr or y2 < st or y1 > sb:
                continue
            for mid in group_ids:
                mid_meta = _MAP_META.get(mid)
                mid_camp = _campaign_group(mid_meta[2]) if mid_meta else current_camp_group
                _ensure_portal_dots(mid, is_live=(mid == current_map))
                for dot in _PORTAL_ICON_POS.get(mid, []):
                    if len(dot) < 5:
                        continue
                    pix, piy, _, _, gid2 = dot[:5]
                    is_linked = gid2 in _PORTAL_LINKS
                    if not is_linked and not _show_debug[0]:
                        continue
                    if not is_linked and mid_camp != current_camp_group:
                        continue
                    sx_, sy_ = _i2s(pix, piy)
                    fill = linked_col   if is_linked else unlinked_col
                    rim  = linked_rim   if is_linked else unlinked_rim
                    r_dot = 4.0         if is_linked else 3.0
                    PyImGui.draw_list_add_circle_filled(sx_, sy_, r_dot, fill, 10)
                    PyImGui.draw_list_add_circle(sx_, sy_, r_dot, rim, 10, 1.0)
                    drawn_dots.append((sx_, sy_, gid2))

        # Tooltip: show all portal IDs within 8px of the mouse
        if drawn_dots:
            near: list[tuple[float, int]] = []
            for sx_, sy_, gid2 in drawn_dots:
                d2 = (mx - sx_) ** 2 + (my - sy_) ** 2
                if d2 <= 64.0:   # 8px radius
                    near.append((d2, gid2))
            if near and PyImGui.begin_tooltip():
                near.sort(key=lambda x: x[0])
                for _, gid2 in near:
                    partner = _PORTAL_LINKS.get(gid2)
                    if partner:
                        map_a  = gid2   // 1000
                        map_b  = partner // 1000
                        name_a = (_MAP_META.get(map_a) or (None, f"Map {map_a}"))[1]
                        name_b = (_MAP_META.get(map_b) or (None, f"Map {map_b}"))[1]
                        PyImGui.text(f"Portal ID: {gid2}  (linked)  {name_a} - {name_b}")
                    else:
                        map_a  = gid2 // 1000
                        name_a = (_MAP_META.get(map_a) or (None, f"Map {map_a}"))[1]
                        PyImGui.text(f"Portal ID: {gid2}  (unlinked)  {name_a}")
                PyImGui.end_tooltip()

    # ── Pass 4: active route overlay ──────────────────────────────────────
    if _active_move_path:
        route_map_border = Utils.RGBToColor(120, 230, 255, 255)
        route_line_col   = Utils.RGBToColor(255,  60,  60, 220)
        route_dot_fill   = Utils.RGBToColor(255, 255, 100, 255)
        route_dot_rim    = Utils.RGBToColor(200, 200,  50, 255)

        # ── 4a: highlight maps along the route ────────────────────────────
        i = 0
        path = _active_move_path
        while i < len(path):
            item = path[i]
            if 0 < item < 1000:
                bnd = _ICON_BOUNDS.get(item)
                if bnd:
                    rx1, ry1 = _i2s(bnd[0], bnd[1])
                    rx2, ry2 = _i2s(bnd[2], bnd[3])
                    PyImGui.draw_list_add_rect(rx1, ry1, rx2, ry2,
                                               route_map_border, 2.0, 0, 2.0)
            i += 1

        # ── 4b: draw A* walking path per hop ──────────────────────────────
        # _route_hops are pre-computed; recompute is triggered by _tick_pmap_loader
        # when new pmap data arrives for a map in the active path (not every frame).
        # _route_hops stores pre-computed icon-space points; no game bounds needed.
        for map_id, icon_pts in _route_hops:
            if len(icon_pts) < 2:
                continue
            prev_sx: float | None = None
            prev_sy: float | None = None
            for ix, iy in icon_pts:
                sx3, sy3 = _i2s(ix, iy)
                if prev_sx is not None and prev_sy is not None:
                    PyImGui.draw_list_add_line(prev_sx, prev_sy, sx3, sy3, route_line_col, 2.5)
                prev_sx, prev_sy = sx3, sy3

        # ── 4c: portal dots at each hop boundary ──────────────────────────
        i = 0
        while i < len(path):
            item = path[i]
            if 1000 <= item:
                gid = item
                mid2 = gid // 1000
                for dot in _PORTAL_ICON_POS.get(mid2, []):
                    if len(dot) >= 5 and dot[4] == gid:
                        sx4, sy4 = _i2s(float(dot[0]), float(dot[1]))
                        PyImGui.draw_list_add_circle_filled(sx4, sy4, 5.5, route_dot_fill, 12)
                        PyImGui.draw_list_add_circle(sx4, sy4, 5.5, route_dot_rim, 12, 1.5)
                        break
            i += 1

    # ── Context popup (right-click on map frame) ───────────────────────────
    if PyImGui.begin_popup("##wmp_map_ctx"):
        _ctx_cur2 = Map.GetMapID()
        for _ctx_i, (_ctx_mid2, _ctx_dx2, _ctx_dy2) in enumerate(_ctx_entries):
            if _ctx_i > 0:
                PyImGui.separator()
            _ctx_meta2 = _MAP_META.get(_ctx_mid2)
            _ctx_name2 = _ctx_meta2[1] if _ctx_meta2 else f"Map {_ctx_mid2}"
            PyImGui.text_disabled(f"{_ctx_name2}  [{_ctx_mid2}]")
            if _ctx_dx2 != 0.0:
                PyImGui.text_disabled(f"  x={_ctx_dx2:.0f}  y={_ctx_dy2:.0f}")
            PyImGui.separator()

            if PyImGui.menu_item(f"+ Add to Queue##{_ctx_mid2}"):
                _map_queue.append(_ctx_mid2)
                _apply_queue_path(_map_queue)

            if _ctx_mid2 != _ctx_cur2:
                if PyImGui.menu_item(f"Move to Map##{_ctx_mid2}"):
                    if _active_move_tree[0] is not None:
                        try:
                            _active_move_tree[0].Stop()
                        except Exception:
                            pass
                    _bt2 = MoveToMapID(_ctx_mid2)
                    if _bt2:
                        _active_move_tree[0] = _bt2
                    _apply_path_to_map(_ctx_mid2)

            if _ctx_dx2 != 0.0:
                if PyImGui.menu_item(f"Move to Click Position##{_ctx_mid2}"):
                    _ctx_do_move_to_coords(_ctx_mid2, _ctx_dx2, _ctx_dy2)

        PyImGui.end_popup()

    PyImGui.end()

# ── Map Queue / Navigation window (right side) ────────────────────────────────

def _draw_map_queue_window() -> None:
    if not Map.WorldMap.IsWindowOpen():
        return
    if not _zoom_is_default():
        return

    fi = Map.WorldMap.GetFrameInfo()
    if fi is None:
        return
    sc = fi.GetContentCoords()
    if not sc:
        return
    sl, st = float(sc[0]), float(sc[1])
    sr, sb = float(sc[2]), float(sc[3])

    # Only show when there is something to display
    has_nav   = bool(_active_move_path and _active_move_tree[0] is not None)
    has_queue = bool(_map_queue)
    if not has_nav and not has_queue:
        return

    win_w  = 210.0
    margin = 8.0
    max_h  = sb - st - margin * 2
    btn_w  = win_w - 16.0

    flags = (
        PyImGui.WindowFlags.NoTitleBar        |
        PyImGui.WindowFlags.NoResize          |
        PyImGui.WindowFlags.NoMove            |
        PyImGui.WindowFlags.NoCollapse        |
        PyImGui.WindowFlags.AlwaysAutoResize  |
        PyImGui.WindowFlags.NoSavedSettings
    )

    PyImGui.set_next_window_pos(sr - win_w - margin, st + margin)
    PyImGui.set_next_window_size_constraints((win_w, 0.0), (win_w, max_h))
    if not PyImGui.begin("##wmp_queue_win", flags):
        PyImGui.end()
        return

    title_col = Utils.RGBToColor(255, 230, 140, 255)

    # ── Navigation progress ────────────────────────────────────────────────
    if has_nav:
        tx, ty = PyImGui.get_cursor_screen_pos()
        PyImGui.dummy(int(win_w), 16)
        PyImGui.draw_list_add_text(tx, ty, title_col, "Navigation")

        col_done    = (0.45, 0.45, 0.45, 0.80)
        col_current = (0.31, 0.86, 0.31, 1.0)
        col_pending = (0.78, 0.78, 0.78, 0.87)

        cmap_nav    = Map.GetMapID()
        route_maps  = [item for item in _active_move_path if 0 < item < 1000]
        cur_idx_nav = next((i for i, m in enumerate(route_maps) if m == cmap_nav), -1)

        for _ni, _nmid in enumerate(route_maps):
            _nmeta = _MAP_META.get(_nmid)
            _nname = _nmeta[1] if _nmeta else f"Map {_nmid}"
            if cur_idx_nav >= 0 and _ni < cur_idx_nav:
                PyImGui.text_colored(f"  v  {_nname}", col_done)
            elif _ni == cur_idx_nav:
                PyImGui.text_colored(f"  >> {_nname}", col_current)
            else:
                PyImGui.text_colored(f"  -  {_nname}", col_pending)

        PyImGui.spacing()
        if PyImGui.button("Stop Navigation##wmp_nav_stop2", btn_w, 0):
            try:
                _active_move_tree[0].Stop()
            except Exception:
                pass
            _active_move_tree[0] = None
            _active_move_path.clear()
            _route_hops.clear()
            _queue_running[0] = False
            _map_queue.clear()
            Py4GW.Console.Log(MODULE_NAME, "Navigation stopped.",
                              Py4GW.Console.MessageType.Warning)

    # ── Map Queue ──────────────────────────────────────────────────────────
    if has_queue:
        if has_nav:
            PyImGui.separator()
        tx2, ty2 = PyImGui.get_cursor_screen_pos()
        PyImGui.dummy(int(win_w), 16)
        PyImGui.draw_list_add_text(tx2, ty2, title_col, "Map Queue")
        PyImGui.text_disabled("  (right-click a map frame)")

        PyImGui.separator()
        _remove_idx = -1
        _queue_child_h = min(len(_map_queue) * 19.0 + 4.0, max_h * 0.5)
        if PyImGui.begin_child("##wmpq_list2", (btn_w, _queue_child_h), False):
            for _qi, _qmid in enumerate(_map_queue):
                _qmeta = _MAP_META.get(_qmid)
                _qname = _qmeta[1] if _qmeta else f"Map {_qmid}"
                _is_active = (_queue_running[0] and _qi == 0
                              and _active_move_tree[0] is not None)
                if _is_active:
                    PyImGui.text_colored(f">> {_qname} [{_qmid}]", (0.31, 0.86, 0.31, 1.0))
                else:
                    PyImGui.text(f"   {_qname} [{_qmid}]")
                PyImGui.same_line(0.0, -1.0)
                if PyImGui.small_button(f"x##wmpq2_{_qi}"):
                    _remove_idx = _qi
        PyImGui.end_child()
        if _remove_idx >= 0:
            _map_queue.pop(_remove_idx)

        PyImGui.separator()
        _nav_busy = _active_move_tree[0] is not None
        if _queue_running[0]:
            if PyImGui.button("Stop Queue##wmpq_stop2", btn_w, 0):
                try:
                    if _active_move_tree[0] is not None:
                        _active_move_tree[0].Stop()
                except Exception:
                    pass
                _active_move_tree[0] = None
                _active_move_path.clear()
                _route_hops.clear()
                _queue_running[0] = False
                _map_queue.clear()
                Py4GW.Console.Log(MODULE_NAME, "Map queue stopped.",
                                  Py4GW.Console.MessageType.Warning)
        else:
            _half = (win_w - 20.0) / 2.0
            if _nav_busy:
                PyImGui.begin_disabled(True)
            if PyImGui.button("Start Queue##wmpq_start2", _half, 0):
                _queue_running[0] = True
                _apply_queue_path(_map_queue)
            if _nav_busy:
                PyImGui.end_disabled()
            PyImGui.same_line(0.0, -1.0)
            if PyImGui.button("Clear##wmpq_clear2", _half, 0):
                _map_queue.clear()
                _queue_running[0] = False

    PyImGui.end()


# ── Legend + settings panel ───────────────────────────────────────────────────


def _draw_legend_and_settings() -> None:
    if not Map.WorldMap.IsWindowOpen():
        return
    if not _zoom_is_default():
        return

    fi = Map.WorldMap.GetFrameInfo()
    if fi is None:
        return
    sc = fi.GetContentCoords()
    if not sc:
        return
    sl, st = float(sc[0]), float(sc[1])
    sb     = float(sc[3])

    box_size   = 12.0
    row_h      = box_size + 5.0
    win_w      = 190.0
    margin     = 8.0
    max_panel_h = sb - st - margin * 2

    legend_entries = [
        ("Explorable Zone",     _type_fill(_RT_EXPLORABLE,  200), _type_border(_RT_EXPLORABLE,  255)),
        ("Outpost / City",      _type_fill(_RT_OUTPOST,     200), _type_border(_RT_OUTPOST,     255)),
        ("Mission / Challenge", _type_fill(_RT_MISSION_OUT, 200), _type_border(_RT_MISSION_OUT, 255)),
        ("Current Map",         Utils.RGBToColor(255, 230,  50, 210), Utils.RGBToColor(255, 255, 100, 255)),
        ("Portal connection",   Utils.RGBToColor(255, 220,  60, 200), 0),
        ("Linked Portal",       Utils.RGBToColor( 60, 210,  60, 230), Utils.RGBToColor(180, 255, 180, 255)),
    ]

    panel_flags = _get_panel_flags()
    PyImGui.set_next_window_pos(sl + margin, st + margin)
    PyImGui.set_next_window_size_constraints((win_w, 0.0), (win_w, max_panel_h))
    if not PyImGui.begin("##wm_plus_panel", panel_flags):
        PyImGui.end()
        return

    title_col = Utils.RGBToColor(255, 230, 140, 255)
    tx, ty = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 16)
    PyImGui.draw_list_add_text(tx, ty, title_col, "WorldMap+")

    text_col = Utils.RGBToColor(230, 230, 230, 255)
    for label, fill_col, border_col in legend_entries:
        sx, sy = PyImGui.get_cursor_screen_pos()
        PyImGui.dummy(int(win_w), int(row_h))
        bx = sx
        by = sy + (row_h - box_size) * 0.5
        if label == "Portal connection":
            line_y = by + box_size * 0.5
            PyImGui.draw_list_add_line(bx, line_y, bx + box_size, line_y, fill_col, 2.0)
        elif label == "Linked Portal":
            cx_dot = bx + box_size * 0.5
            cy_dot = by + box_size * 0.5
            PyImGui.draw_list_add_circle_filled(cx_dot, cy_dot, 5.0, fill_col, 10)
            PyImGui.draw_list_add_circle(cx_dot, cy_dot, 5.0, border_col, 10, 1.0)
        else:
            PyImGui.draw_list_add_rect(bx, by, bx + box_size, by + box_size,
                                       border_col, 2.0, 0, 1.5)
        PyImGui.draw_list_add_text(
            bx + box_size + 5.0, sy + (row_h - 13.0) * 0.5, text_col, label)

    # ── Settings ───────────────────────────────────────────────────────────
    PyImGui.separator()
    _show_ui_settings[0] = PyImGui.checkbox("Show UI Settings##wmp", _show_ui_settings[0])

    if _show_ui_settings[0]:
        PyImGui.push_item_width(win_w - 16.0)

        new_frames      = PyImGui.checkbox("  Draw Frames##wmp",      _show_frames[0])
        new_portals     = PyImGui.checkbox("  Draw Portals##wmp",     _show_portals[0])
        new_connections = PyImGui.checkbox("  Draw Connections##wmp", _show_connections[0])
        new_labels      = PyImGui.checkbox("  Show Labels##wmp",      _show_labels[0])
        new_navmesh     = PyImGui.checkbox("  Draw NavMesh##wmp",     _show_navmesh[0])
        new_opacity     = PyImGui.slider_float("  Opacity##wmp",      _opacity[0], 0.1, 1.0)

        if (new_frames      != _show_frames[0]      or
                new_portals     != _show_portals[0]     or
                new_connections != _show_connections[0] or
                new_labels      != _show_labels[0]      or
                new_navmesh     != _show_navmesh[0]     or
                new_opacity     != _opacity[0]):
            _show_frames[0]      = new_frames
            _show_portals[0]     = new_portals
            _show_connections[0] = new_connections
            _show_labels[0]      = new_labels
            _show_navmesh[0]     = new_navmesh
            _opacity[0]          = new_opacity
            _wmp_ini_save()

        PyImGui.pop_item_width()

    # ── Debug ───────────────────────────────────────────────────────────────
    PyImGui.separator()
    _rclick_active[0] = PyImGui.checkbox("Activate Rightclick##wmp", _rclick_active[0])

    _show_debug[0] = PyImGui.checkbox("Show Debug##wmp", _show_debug[0])

    if _show_debug[0]:
        new_exp = PyImGui.checkbox("  Show Experimental##wmp", _show_experimental[0])
        if new_exp != _show_experimental[0]:
            _show_experimental[0] = new_exp
            _wmp_ini_save()

        new_unc = PyImGui.checkbox("  Show Unconnected##wmp", _show_unconnected[0])
        if new_unc != _show_unconnected[0]:
            _show_unconnected[0] = new_unc
            _wmp_ini_save()

        new_rp = PyImGui.checkbox("  Record Portals##wmp", _record_portals[0])
        if new_rp != _record_portals[0]:
            _record_portals[0] = new_rp
            _wmp_ini_save()

        new_rb = PyImGui.checkbox("  Record Map Boundaries##wmp", _record_boundaries[0])
        if new_rb != _record_boundaries[0]:
            _record_boundaries[0] = new_rb
            _wmp_ini_save()

        PyImGui.separator()
        _show_portal_editor[0] = PyImGui.checkbox("  Show Portal Editor##wmp", _show_portal_editor[0])

    if _show_debug[0] and not _show_experimental[0]:
        PyImGui.text_disabled("  (Prophecies only)")

    if _show_debug[0]:
        btn_w   = 70.0
        gap     = 4.0
        field_w = (win_w - 16.0 - btn_w - gap * 2) / 2.0
        PyImGui.push_item_width(field_w)
        new_a = PyImGui.input_text("##wmp_dbg_a", _debug_map_a_str[0], 8)
        PyImGui.pop_item_width()
        PyImGui.same_line(0.0, gap)
        PyImGui.push_item_width(field_w)
        new_b = PyImGui.input_text("##wmp_dbg_b", _debug_map_b_str[0], 8)
        PyImGui.pop_item_width()
        PyImGui.same_line(0.0, gap)
        if new_a != _debug_map_a_str[0]:
            _debug_map_a_str[0] = new_a
            try: _debug_map_a[0] = int(new_a)
            except ValueError: pass
        if new_b != _debug_map_b_str[0]:
            _debug_map_b_str[0] = new_b
            try: _debug_map_b[0] = int(new_b)
            except ValueError: pass
        if PyImGui.button("GetPath##wmp_dbg", btn_w, 0):
            if not _cache_built:
                Py4GW.Console.Log(MODULE_NAME, "Cache not ready.",
                                  Py4GW.Console.MessageType.Warning)
            else:
                path = GetPath(_debug_map_a[0], _debug_map_b[0])
                if not isinstance(path, list):
                    Py4GW.Console.Log(MODULE_NAME,
                        f"GetPath({_debug_map_a[0]}, {_debug_map_b[0]}): NO PATH",
                        Py4GW.Console.MessageType.Warning)
                    _active_move_path.clear()
                    _route_hops.clear()
                else:
                    Py4GW.Console.Log(MODULE_NAME,
                        f"GetPath({_debug_map_a[0]}, {_debug_map_b[0]}):",
                        Py4GW.Console.MessageType.Info)
                    i = 0
                    while i < len(path):
                        item = path[i]
                        if 0 < item < 1000:
                            name = (_MAP_META.get(item) or (None, f"Map {item}"))[1]
                            Py4GW.Console.Log(MODULE_NAME,
                                f"  Map  [{item}] {name}",
                                Py4GW.Console.MessageType.Info)
                            i += 1
                        elif i + 1 < len(path):
                            exit_g  = path[i]
                            enter_g = path[i + 1]
                            if exit_g != 0 or enter_g != 0:
                                Py4GW.Console.Log(MODULE_NAME,
                                    f"  Portal  {exit_g}  ->  Portal  {enter_g}",
                                    Py4GW.Console.MessageType.Info)
                            i += 2
                        else:
                            i += 1
                    # Visualise path on WorldMap immediately (no movement started)
                    _active_move_path[:] = path
                    _route_hops.clear()
                    _compute_route_hops(path)

        if _active_move_path and _active_move_tree[0] is None:
            if PyImGui.button("Clear Path##wmp_dbg_clear", win_w - 16.0, 0):
                _active_move_path.clear()
                _route_hops.clear()

        PyImGui.spacing()
        PyImGui.push_item_width(field_w * 2 + gap)
        new_move = PyImGui.input_text("##wmp_dbg_move", _debug_move_str[0], 8)
        PyImGui.pop_item_width()
        if new_move != _debug_move_str[0]:
            _debug_move_str[0] = new_move
            try: _debug_move_id[0] = int(new_move)
            except ValueError: pass
        PyImGui.same_line(0.0, gap)
        if PyImGui.button("MoveToMapID##wmp_dbg_move", btn_w, 0):
            tree = MoveToMapID(_debug_move_id[0])
            if tree is False:
                Py4GW.Console.Log(MODULE_NAME,
                    f"MoveToMapID({_debug_move_id[0]}): failed to build route.",
                    Py4GW.Console.MessageType.Warning)
                _active_move_tree[0] = None
            else:
                Py4GW.Console.Log(MODULE_NAME,
                    f"MoveToMapID({_debug_move_id[0]}): route built — starting.",
                    Py4GW.Console.MessageType.Info)
                _active_move_tree[0] = tree
                p = GetPath(Map.GetMapID(), _debug_move_id[0])
                _active_move_path[:] = p if isinstance(p, list) else []
                Py4GW.Console.Log(MODULE_NAME,
                    f"GetPath result: {_active_move_path}",
                    Py4GW.Console.MessageType.Info)
                if _active_move_path:
                    _compute_route_hops(_active_move_path)
                    Py4GW.Console.Log(MODULE_NAME,
                        f"Route hops computed: {len(_route_hops)} hop(s) — "
                        + "; ".join(f"map {h[0]} pts={len(h[1])}" for h in _route_hops),
                        Py4GW.Console.MessageType.Info)

        # ── MoveToMapIDCoords ──────────────────────────────────────────────
        PyImGui.spacing()
        PyImGui.separator()
        PyImGui.text("MoveToMapIDCoords")

        # Row 1: MapID  X  Y
        PyImGui.push_item_width(field_w)
        new_cmap = PyImGui.input_text("##wmp_dbg_cmap", _debug_coords_map_str[0], 8)
        PyImGui.pop_item_width()
        if new_cmap != _debug_coords_map_str[0]:
            _debug_coords_map_str[0] = new_cmap
            try: _debug_coords_map_id[0] = int(new_cmap)
            except ValueError: pass
        PyImGui.same_line(0.0, gap)

        PyImGui.push_item_width(field_w)
        new_cx = PyImGui.input_text("##wmp_dbg_cx", _debug_coords_x_str[0], 10)
        PyImGui.pop_item_width()
        if new_cx != _debug_coords_x_str[0]:
            _debug_coords_x_str[0] = new_cx
            try: _debug_coords_x[0] = float(new_cx)
            except ValueError: pass
        PyImGui.same_line(0.0, gap)

        PyImGui.push_item_width(field_w)
        new_cy = PyImGui.input_text("##wmp_dbg_cy", _debug_coords_y_str[0], 10)
        PyImGui.pop_item_width()
        if new_cy != _debug_coords_y_str[0]:
            _debug_coords_y_str[0] = new_cy
            try: _debug_coords_y[0] = float(new_cy)
            except ValueError: pass

        # Row 2: button (full width)
        if PyImGui.button("MoveToMapIDCoords##wmp_dbg_coords", win_w - 16.0, 0):
            if _active_move_tree[0] is None:
                tree = MoveToMapIDCoords(
                    _debug_coords_map_id[0],
                    _debug_coords_x[0],
                    _debug_coords_y[0],
                )
                if tree is False:
                    Py4GW.Console.Log(MODULE_NAME,
                        f"MoveToMapIDCoords({_debug_coords_map_id[0]}, "
                        f"{_debug_coords_x[0]:.0f}, {_debug_coords_y[0]:.0f}): failed.",
                        Py4GW.Console.MessageType.Warning)
                    _active_move_tree[0] = None
                else:
                    _active_move_tree[0] = tree
                    p = GetPath(Map.GetMapID(), _debug_coords_map_id[0])
                    _active_move_path[:] = p if isinstance(p, list) else []
                    if _active_move_path:
                        _compute_route_hops(_active_move_path)

        if _active_move_tree[0] is not None:
            PyImGui.text_colored("Moving...", (0.4, 1.0, 0.4, 1.0))
            if PyImGui.button("Cancel##wmp_dbg_cancel", win_w - 16.0, 0):
                try:
                    _active_move_tree[0].Stop()
                except Exception:
                    pass
                _active_move_tree[0] = None
                _active_move_path.clear(); _route_hops.clear()
                Py4GW.Console.Log(MODULE_NAME, "MoveToMapID: cancelled.",
                                  Py4GW.Console.MessageType.Warning)

    PyImGui.end()

# ── Portal Editor 3D in-game overlay ──────────────────────────────────────────

def _draw_portal_editor_3d() -> None:
    """Draw portal positions of the current map in-game as 3D circles + labels."""
    if not _show_portal_editor[0]:
        return
    if not Map.IsMapReady():
        return

    cur_map = Map.GetMapID()
    _ensure_portal_dots(cur_map, is_live=True)
    dots = _PORTAL_ICON_POS.get(cur_map, [])
    if not dots:
        return

    col_linked   = Utils.RGBToColor( 60, 220,  60, 220)
    col_unlinked = Utils.RGBToColor(220,  60,  60, 220)
    col_text_lnk = Utils.RGBToColor(180, 255, 180, 255)
    col_text_unl = Utils.RGBToColor(255, 180, 180, 255)

    overlay = _Overlay()
    overlay.BeginDraw()
    try:
        for dot in dots:
            if len(dot) < 7:
                continue
            _, _, dest_name, idx, gid, gx, gy = dot[:7]

            linked_gid  = _PORTAL_LINKS.get(gid)
            is_linked   = linked_gid is not None
            fill_col    = col_linked   if is_linked else col_unlinked
            text_col    = col_text_lnk if is_linked else col_text_unl

            gz = float(_Overlay.FindZ(float(gx), float(gy)))

            # Circle on the ground
            overlay.DrawPolyFilled3D(float(gx), float(gy), gz, 80.0, fill_col, 24)

            # Label: index, GID and destination / linked portal
            if is_linked:
                partner_mid  = linked_gid // 1000
                partner_idx  = linked_gid %  1000
                partner_meta = _MAP_META.get(partner_mid)
                partner_name = partner_meta[1] if partner_meta else f"Map {partner_mid}"
                label = f"[{idx}] GID {gid}\n-> [{partner_idx}] {partner_name}"
            else:
                label = f"[{idx}] GID {gid}\n(unlinked)"

            overlay.DrawText3D(float(gx), float(gy), gz - 100.0,
                               label, text_col, False, True, 1.0)
    finally:
        overlay.EndDraw()


# ── Portal Editor window ───────────────────────────────────────────────────────

def _draw_portal_editor() -> None:
    if not _show_portal_editor[0]:
        return

    flags = (
        PyImGui.WindowFlags.NoCollapse  |
        PyImGui.WindowFlags.NoScrollbar
    )
    PyImGui.set_next_window_size(480.0, 500.0)
    if not PyImGui.begin("Portal Editor##wmp_pe", flags):
        PyImGui.end()
        return

    cur_map = Map.GetMapID()
    cur_meta = _MAP_META.get(cur_map)
    cur_name = cur_meta[1] if cur_meta else f"Map {cur_map}"

    PyImGui.text(f"Map: {cur_name}  [{cur_map}]")
    PyImGui.separator()

    # ── Link / Unlink controls ─────────────────────────────────────────────
    PyImGui.text("Link portals:")
    PyImGui.set_next_item_width(120.0)
    _pe_gid_a[0] = PyImGui.input_int("GID A##pe_a", _pe_gid_a[0])
    PyImGui.same_line(0.0, 6.0)
    PyImGui.set_next_item_width(120.0)
    _pe_gid_b[0] = PyImGui.input_int("GID B##pe_b", _pe_gid_b[0])

    PyImGui.same_line(0.0, 10.0)
    if PyImGui.button("Link##pe_link", 50.0, 0.0):
        a, b = _pe_gid_a[0], _pe_gid_b[0]
        if a > 0 and b > 0 and a != b:
            _PORTAL_LINKS[a] = b
            _PORTAL_LINKS[b] = a
            _save_portal_links()
            _pe_status[0] = f"Linked GID {a} <-> {b}"
        else:
            _pe_status[0] = "Invalid GIDs — must be two different positive values."

    PyImGui.same_line(0.0, 4.0)
    if PyImGui.button("Unlink##pe_unlink", 60.0, 0.0):
        a, b = _pe_gid_a[0], _pe_gid_b[0]
        removed = False
        for gid in (a, b):
            if gid in _PORTAL_LINKS:
                partner = _PORTAL_LINKS.pop(gid)
                _PORTAL_LINKS.pop(partner, None)
                removed = True
        if removed:
            _save_portal_links()
            _pe_status[0] = f"Unlinked GID {a} / {b}"
        else:
            _pe_status[0] = "No link found for those GIDs."

    if _pe_status[0]:
        PyImGui.text_disabled(_pe_status[0])

    PyImGui.separator()

    # Ensure portal dots are built for the current map
    _ensure_portal_dots(cur_map, is_live=True)
    dots = _PORTAL_ICON_POS.get(cur_map, [])

    if not dots:
        PyImGui.text_disabled("No portal data available for this map.")
        PyImGui.end()
        return

    col_linked   = (0.25, 0.90, 0.25, 1.0)
    col_unlinked = (0.90, 0.25, 0.25, 1.0)
    col_label    = (0.85, 0.85, 0.85, 1.0)
    col_partner  = (0.55, 0.85, 1.00, 1.0)

    PyImGui.begin_child("##pe_list", (0.0, 0.0), False)

    for dot in dots:
        pix, piy, dest_name, idx, gid, gx, gy = dot[:7] if len(dot) >= 7 else (*dot[:6], 0.0)

        linked_gid = _PORTAL_LINKS.get(gid)
        is_linked  = linked_gid is not None

        # ── Portal header row ──────────────────────────────────────────────
        status_col  = col_linked if is_linked else col_unlinked
        status_text = "LINKED" if is_linked else "UNLINKED"
        PyImGui.text_colored(f"[{idx}]  GID {gid}  —  {status_text}", status_col)
        PyImGui.same_line(0.0, 8.0)
        PyImGui.text_colored(f"  game ({gx:.1f}, {gy:.1f})", col_label)


        # ── Linked partner info ────────────────────────────────────────────
        if is_linked:
            partner_map_id  = linked_gid // 1000
            partner_idx     = linked_gid %  1000
            partner_meta    = _MAP_META.get(partner_map_id)
            partner_name    = partner_meta[1] if partner_meta else f"Map {partner_map_id}"

            # Look up partner's game coords if available
            partner_dots = _PORTAL_ICON_POS.get(partner_map_id, [])
            partner_dot  = next((d for d in partner_dots if len(d) >= 5 and d[4] == linked_gid), None)
            if partner_dot and len(partner_dot) >= 7:
                pgx, pgy = partner_dot[5], partner_dot[6]
                PyImGui.text_colored(
                    f"     -> [{partner_idx}] GID {linked_gid}  {partner_name} [{partner_map_id}]"
                    f"  ({pgx:.1f}, {pgy:.1f})",
                    col_partner,
                )
            else:
                PyImGui.text_colored(
                    f"     -> [{partner_idx}] GID {linked_gid}  {partner_name} [{partner_map_id}]",
                    col_partner,
                )

        PyImGui.separator()

    PyImGui.end_child()
    PyImGui.end()


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    global _cache_built
    try:
        _wmp_ini_try_init()
        if not _cache_built:
            _build_cache()
            _init_pmap_queue()   # prime the per-frame loader (non-blocking)

        # Load a few pmap entries per frame — avoids stalling/crashing the game
        _tick_pmap_loader()

        cmap = Map.GetMapID()
        if cmap != _last_map[0]:
            # Invalidate cached portal data for the old and new map on transition
            old = _last_map[0]
            if old > 0:
                _PORTAL_BUILT.discard(old)
                _PORTAL_ICON_POS.pop(old, None)
            _PORTAL_BUILT.discard(cmap)
            _PORTAL_ICON_POS.pop(cmap, None)
            # If the new map has an empty pmap (no DAT entry, stored as placeholder
            # by the queue), drop it now so the on-demand loader in _draw_pmap_for_map
            # can repopulate it from live pathing data on the very next draw frame.
            pmap_entry = _PMAP_DATA.get(cmap)
            if pmap_entry is not None and not pmap_entry[1]:  # empty trap list
                _PMAP_DATA.pop(cmap, None)
            _last_map[0] = cmap

        # Tick active MoveToMapID BottingTree every frame
        if _active_move_tree[0] is not None:
            bt = _active_move_tree[0]
            bt.tick()
            bt.DrawMovePathIfEnabled()
            if not bt.started:
                # BottingTree sets started=False on planner SUCCESS or FAILURE
                status = bt.tree.blackboard.get("PLANNER_STATUS", "")
                if "Failed" in str(status):
                    Py4GW.Console.Log(MODULE_NAME, "MoveToMapID: route failed.",
                                      Py4GW.Console.MessageType.Warning)
                else:
                    Py4GW.Console.Log(MODULE_NAME, "MoveToMapID: arrived at destination.",
                                      Py4GW.Console.MessageType.Info)
                _active_move_tree[0] = None
                _active_move_path.clear(); _route_hops.clear()

        # ── Map queue executor ─────────────────────────────────────────────
        if _queue_running[0] and _active_move_tree[0] is None:
            if _map_queue:
                _q_target = _map_queue[0]
                if _q_target == Map.GetMapID():
                    # Already here — pop and move to the next entry immediately
                    _map_queue.pop(0)
                    Py4GW.Console.Log(MODULE_NAME,
                        f"Queue: already at [{_q_target}], skipping.",
                        Py4GW.Console.MessageType.Info)
                    _apply_queue_path(_map_queue)
                else:
                    _map_queue.pop(0)
                    _bt = MoveToMapID(_q_target)
                    if _bt:
                        _active_move_tree[0] = _bt
                        _apply_path_to_map(_q_target)
                    else:
                        Py4GW.Console.Log(MODULE_NAME,
                            f"Queue: no path to [{_q_target}], skipping.",
                            Py4GW.Console.MessageType.Warning)
                        _apply_queue_path(_map_queue)
            else:
                _queue_running[0] = False
                Py4GW.Console.Log(MODULE_NAME, "Map queue complete.",
                                  Py4GW.Console.MessageType.Info)

        # Campaign gate: when Show Experimental is off, only draw on Prophecies / EotN
        _gate_meta = _MAP_META.get(cmap)
        _gate_camp  = _gate_meta[2] if _gate_meta else 1
        _gate_ok    = _show_experimental[0] or _campaign_group(_gate_camp) == 1

        if _gate_ok:
            _draw_overlay()
            _draw_legend_and_settings()
            _draw_map_queue_window()

        _draw_portal_editor_3d()
        _draw_portal_editor()

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"{e}\n{traceback.format_exc()}",
                          Py4GW.Console.MessageType.Error)


if __name__ == "__main__":
    main()
