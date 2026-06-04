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
from collections import defaultdict

from Py4GWCoreLib import Map, Utils
from Py4GWCoreLib.IniManager import IniManager as _IniManager
from Py4GWCoreLib.native_src.methods.MapMethods import MapMethods
from Py4GWCoreLib.native_src.methods.FfnaMapMethods import FfnaMapMethods

MODULE_NAME = "WorldMap+"

try:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _SCRIPT_DIR = os.path.join(
        Py4GW.Console.get_projects_path(),
        "Widgets", "Guild Wars", "Screen Overlays"
    )

import Py4GWCoreLib.WorldPathing as _WP
_WP.configure(_SCRIPT_DIR)
from Py4GWCoreLib.WorldPathing import (
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
_LIVE_PORTAL_CACHE_FILE = os.path.join(_SCRIPT_DIR, "portal_live_cache.json")
_PORTAL_ALL_FILE        = os.path.join(_SCRIPT_DIR, "portal_all.json")

# Shared adapter file that accumulates map_rect (boundaries) across all sessions
_ADAPTER_DIR = os.path.join(
    Py4GW.Console.get_projects_path(),
    "Sources", "sch0l0ka", "adapter", "Worldmap+"
)
_MAP_RECT_FILE = os.path.join(_ADAPTER_DIR, "map_boundaries.json")

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

# Screen-space transform updated at the start of every _draw_overlay call:
# [sl, st, il, it, sx, sy]  where sx = sw/iw, sy = sh/ih
_s_transform: list[float] = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0]


def _icon_to_screen(ix: float, iy: float) -> tuple[float, float]:
    """Convert icon-space coordinates to screen pixels using the cached transform."""
    sl, st, il, it, sx, sy = _s_transform
    return sl + (ix - il) * sx, st + (iy - it) * sy

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
_show_ui_settings: list[bool]  = [False]
_show_debug:       list[bool]  = [False]
_debug_map_a:      list[int]   = [0]
_debug_map_b:      list[int]   = [0]
_debug_map_a_str:  list[str]   = ["0"]
_debug_map_b_str:  list[str]   = ["0"]
_debug_move_str:   list[str]   = ["0"]
_debug_move_id:    list[int]   = [0]
_active_move_tree: list = [None]   # holds the running MoveToMapID BehaviorTree | None
_active_move_path: list[int] = []  # path list from GetPath() for the active route
# per-hop icon-space polylines: (map_id, [(ix, iy), ...])
_route_hops: list[tuple[int, list[tuple[float, float]]]] = []
_last_map:         list[int]   = [0]

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
    """Persist _MAP_RECT_CACHE to the adapter file."""
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


def _zoom_is_default() -> bool:
    return abs(Map.WorldMap.GetZoom() - 1.0) <= 0.001


def _get_panel_flags() -> int:
    return (
        PyImGui.WindowFlags.NoTitleBar        |
        PyImGui.WindowFlags.NoResize          |
        PyImGui.WindowFlags.NoMove            |
        PyImGui.WindowFlags.NoScrollbar       |
        PyImGui.WindowFlags.NoScrollWithMouse |
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


_pmap_load_queue: list[int] = []   # map IDs still to be loaded
_PMAP_LOAD_PER_FRAME = 3           # how many maps to parse per frame


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
        if not pmaps:
            _PMAP_DATA[map_id] = ((0.0, 0.0, 0.0, 0.0), [])
            return

        # 1. Adapter file cache (correct live bounds from any previous session)
        gb: tuple[float, float, float, float] | None = _MAP_RECT_CACHE.get(map_id)

        # 2. FFNA trapezoid bounds – always valid, trapezoids project within [0,1]
        if gb is None:
            gb = _compute_game_bounds(pmaps)
        if gb is None:
            _PMAP_DATA[map_id] = ((0.0, 0.0, 0.0, 0.0), [])
            return

        traps: list[tuple[float,float,float,float,float,float]] = []
        for pm in pmaps:
            for t in pm.trapezoids:
                traps.append((t.XTL, t.XTR, t.XBL, t.XBR, t.YT, t.YB))
        _PMAP_DATA[map_id] = (gb, traps) if traps else ((0.0, 0.0, 0.0, 0.0), [])
    except Exception:
        _PMAP_DATA[map_id] = ((0.0, 0.0, 0.0, 0.0), [])


def _tick_pmap_loader() -> None:
    """Load up to _PMAP_LOAD_PER_FRAME maps from _pmap_load_queue each frame.

    This spreads the DAT-file parsing across many frames so no single frame
    becomes heavy enough to crash or stall the game.
    """
    global _pmap_built
    if _pmap_built:
        return
    for _ in range(_PMAP_LOAD_PER_FRAME):
        if not _pmap_load_queue:
            _pmap_built = True
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


def _best_pmap_id_for_group(group_ids: frozenset | set, prefer: int = 0) -> int:
    """Return the best map_id from the group to draw pmap for.

    Prefers `prefer` (e.g. current_map) if in the group.
    Falls back to the first group member that has non-empty pmap data.
    Falls back to any group member as a last resort (on-demand load will fire).
    """
    if prefer and prefer in group_ids:
        return prefer
    # Prefer any member that already has loaded non-empty trapezoids
    for mid in sorted(group_ids):
        e = _PMAP_DATA.get(mid)
        if e and e[1]:   # e[1] = traps list, non-empty means real data
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
    try:
        with open(_LIVE_PORTAL_CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump({str(k): v for k, v in _live_portal_cache.items()}, fh, indent=2)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Live portal cache save error: {e}",
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
            if _cached_extents is not None:
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

    if _cached_extents is not None:
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
        try:
            pmaps = FfnaMapMethods.GetPathingMapsForMap(map_id)
            if pmaps:
                gb = _compute_game_bounds(pmaps)
        except Exception:
            pass
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

    Results are written to _route_hops as (map_id, [(ix, iy), ...]).
    Icon-space points are converted immediately so Pass 4b only needs _i2s().
    Falls back to a direct icon-space line when A* is unavailable.
    """
    from Py4GWCoreLib.Pathing import NavMesh, AStar

    _route_hops.clear()
    current_map = Map.GetMapID()

    # Pre-populate portal dots for every map on the route
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

            # Determine pathing maps for A*
            gb: tuple[float, float, float, float] | None = _best_gb_for(map_id)
            if map_id == current_map:
                pmaps = Map.Pathing.GetPathingMaps()
                if gb is None:
                    gb = _compute_game_bounds(pmaps) if pmaps else None
            else:
                pmaps = FfnaMapMethods.GetPathingMapsForMap(map_id)
                if gb is None and pmaps:
                    gb = _compute_game_bounds(pmaps)

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
        auto_loot=False,
        auto_resurrection_scroll=False,
        auto_start=True,
    )

    Py4GW.Console.Log(MODULE_NAME,
        f"MoveToMapID: started {len(steps)}-step BottingTree to [{target_map_id}] {t_name}. "
        f"HeroAI active, pause_on_combat={pause_on_combat}.",
        Py4GW.Console.MessageType.Info)
    return bt


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

        has_portals = any(mid in _CONNECTED_MAP_IDS for mid in group_ids)
        if not is_current and not has_portals:
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
                if mid >= 0 and mid != current_map and mid not in _CONNECTED_MAP_IDS:
                    continue
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

    box_size = 12.0
    row_h    = box_size + 5.0
    win_w    = 190.0
    margin   = 8.0

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
    PyImGui.set_next_window_size(win_w, 0.0)
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
    _show_debug[0] = PyImGui.checkbox("Show Debug##wmp", _show_debug[0])

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
            _last_map[0] = cmap

        # Tick active MoveToMapID BottingTree every frame
        if _active_move_tree[0] is not None:
            bt = _active_move_tree[0]
            bt.tick()
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

        _draw_overlay()
        _draw_legend_and_settings()

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"{e}\n{traceback.format_exc()}",
                          Py4GW.Console.MessageType.Error)


if __name__ == "__main__":
    main()
