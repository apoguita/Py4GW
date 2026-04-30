"""
WorldMap+
=========
Overlay for the GW World Map that renders all map boundaries and their
portal connections.  Open the World Map (default key: M) to see the overlay.

Color coding
  ■ Gold     — current map you are in
  ■ Green    — Explorable zones
  ■ Blue     — Outposts / Cities
  ■ Cyan     — Co-op Missions / Mission Outposts
  ■ Orange   — Challenge / Competitive missions
  Yellow lines connect maps that share a walkable portal (adjacency graph).
"""

import PyImGui
import traceback
import math
import Py4GW
import json
import os
from collections import defaultdict, deque

from Py4GWCoreLib import Map, Utils, Player, AutoPathing, GLOBAL_CACHE, Routines, Range, Party
from Py4GWCoreLib.enums_src.Hero_enums import HeroType as _HeroType
from Py4GWCoreLib.IniManager import IniManager as _IniManager
from Py4GWCoreLib.Pathing import NavMesh as _PathingNavMesh, AStar as _PathingAStar
from Py4GWCoreLib.native_src.methods.MapMethods import MapMethods
from Py4GWCoreLib.native_src.methods.FfnaMapMethods import FfnaMapMethods
from Py4GWCoreLib.Overlay import Overlay as _Overlay
from Py4GWCoreLib.BottingTree import BottingTree as _BottingTree
import PyOverlay

_overlay3d = _Overlay()
_bt_draw_helper = _BottingTree("WorldMap+ Path Draw")

MODULE_NAME = "WorldMap+"

# Script directory – used to pass file paths to WorldPathing.configure()
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
    _GLOBAL_ID_TO_PORTAL, _PORTAL_TO_GLOBAL_ID, _PORTAL_LINKS, _PORTAL_GAME_POS,
    _map_name_cached,
    _load_portal_links,
    _find_map_path,
    invalidate_portal_adj,
    _get_portal_adj,
    get_world_adj        as _wp_get_world_adj,
    invalidate_world_adj as _wp_invalidate_world_adj,
    path_distance        as _wp_path_distance,
    GetNearestUnlockedOutpost  as _WP_GetNearestUnlockedOutpost,
    IsPath               as _WP_IsPath,
    GetPath              as _WP_GetPath,
    MoveToNextWaypoint   as _WP_MoveToNextWaypoint,
    MoveToMapid          as _WP_MoveToMapid,
    MoveToMapID          as _WP_MoveToMapID,
    # movement state (shared so WorldMap+ can read runner flags for its UI)
    _mtnw_runner_active, _mtnw_goal_xy, _mtnw_target_map, _mtnw_path, _mtnw_job_id,
    _mtnw_path_index, _mtnw_path_following, _mtnw_path_computing, _mtnw_paused_danger,
    _mtm_runner_active, _mtm_target_map, _mtm_route, _mtm_job_id,
    _mtnw_clear, _mtm_clear,
    _abort_wp_movement,
    _set_runtime_heartbeat,
)

# ── Overlay-only state dicts (not needed by bots; NOT shared with WorldPathing) ──
# map_id -> (left, top, right, bottom) in icon space, or None
_ICON_BOUNDS:   dict[int, tuple[float, float, float, float] | None] = {}
# map_id -> icon-space center (derived from _ICON_BOUNDS)
_MAP_CENTROIDS: dict[int, tuple[float, float]] = {}
# map_id -> set of adjacent map_ids (derived from _ALL_EDGES in _build_cache)
_MAP_NEIGHBORS: dict[int, set[int]] = {}
# Maps that appear in portal_links.json (gid // 1000).
# Populated in _build_cache() after _load_portal_links() completes.
_CONNECTED_MAP_IDS: set[int] = set()
# Loaded from JSON at startup: map_id -> [dx_icon, dy_icon]
_PMAP_OFFSETS:  dict[int, tuple[float, float]] = {}
# Off-map dungeons: map_id -> (anchor_map_id, side)
# side = "left" | "right" | "above" | "below"
_OFFMAP_PLACEMENTS: dict[int, tuple[int, str]] = {
    604: (639, "left"),   # EotN dungeon – display left of Umbral Grotto
}
# Map IDs whose portal_all.json entries are manually curated and must never be
# overwritten by _rebuild_portal_all_data() or the live-portal cache machinery.
_MANUAL_PORTAL_MAPS: set[int] = {604}
# Portal dot positions in icon space (built lazily per map)
_PORTAL_ICON_POS:  dict[int, list[tuple]] = {}  # map_id -> list of (pix, piy, dest_name, local_idx, gid, gx, gy)
_PORTAL_BUILT:     set[int] = set()
# Loaded from portal_destinations.json: map_id -> [{index, game_x, game_y, dest_map_id, dest_name}]
_PORTAL_DEST_DATA: dict[int, list[dict]] = {}
# Full portal catalog (linked + unlinked), loaded from portal_all.json
_PORTAL_ALL_DATA: dict[int, list[dict]] = {}
# Persistent cache of live portal game-coords for maps without a DAT entry.
_live_portal_cache: dict[int, list[dict]] = {}
_LIVE_PORTAL_CACHE_FILE = os.path.join(_SCRIPT_DIR, "portal_live_cache.json")
_PORTAL_ALL_FILE = os.path.join(_SCRIPT_DIR, "portal_all.json")
_CUSTOM_PLACEMENTS_FILE = os.path.join(_SCRIPT_DIR, "custom_placements.json")


# ── Region type constants ──────────────────────────────────────────────────────
_RT_EXPLORABLE   = 2
_RT_COOP         = 6     # Cooperative Mission
_RT_CHALLENGE    = 7
_RT_COMPETITIVE  = 8
_RT_ELITE        = 9
_RT_OUTPOST      = 10
_RT_MISSION_OUT  = 5
_RT_TOWN         = 13
_RT_CITY         = 14
_RT_HERO_BATTLE  = 15

_MAX_MAP_ID    = 900
_cache_built   = False
# Deduplicated draw groups: (frozenset_of_map_ids, bounds, label, rtype, campaign)
# Built in _build_cache() by collapsing maps that share identical icon bounds.
_DRAW_GROUPS: list[tuple] = []


# ── Campaign grouping ─────────────────────────────────────────────────────
# Campaign values: 0=Core/PvP, 1=Prophecies, 2=Factions, 3=Nightfall, 4=EotN
# EotN is grouped with Prophecies since both share the Tyrian continent.
def _campaign_group(campaign: int) -> int:
    return 1 if campaign == 4 else campaign

_CAMPAIGN_GROUP_NAMES: dict[int, str] = {
    0: "PvP / Core",
    1: "Prophecies / EotN",
    2: "Factions",
    3: "Nightfall",
    5: "Bonus Mission Pack",
}


# ── Overlay rendering helpers (WorldMap+-only; not needed by bots) ─────────────

def _compute_game_bounds(pathing_maps) -> tuple[float, float, float, float] | None:
    """Return (gx_min, gx_max, gy_min, gy_max) from a list of pathing maps, or None if degenerate."""
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


def _zoom_is_default() -> bool:
    """Return True when the World Map zoom is at 100% (the only zoom level we draw at)."""
    return abs(Map.WorldMap.GetZoom() - 1.0) <= 0.001


def _get_panel_flags() -> int:
    """Return the standard floating-panel WindowFlags used by all WorldMap+ panels."""
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


def _traps_to_icon(trapezoids: list, ix1: float, iy1: float, ix2: float, iy2: float,
                   offset: tuple[float, float] = (0.0, 0.0)
                   ) -> list[tuple]:
    """Convert trapezoid list to icon-space quads.  Returns [] if bounds are degenerate."""
    if not trapezoids:
        return []
    _gb = _compute_game_bounds(trapezoids)
    if _gb is None:
        return []
    gx_min, gx_max, gy_min, gy_max = _gb
    gw = gx_max - gx_min
    gh = gy_max - gy_min
    iw_map = ix2 - ix1
    ih_map = iy2 - iy1
    odx, ody = offset

    def _g2i(gx: float, gy: float) -> tuple[float, float]:
        return (ix1 + (gx - gx_min) / gw * iw_map + odx,
                iy1 + (gy_max - gy) / gh * ih_map + ody)  # Y flipped

    result = []
    for trap in trapezoids:
        xtl, ytl = _g2i(trap.XTL, trap.YT)
        xtr, ytr = _g2i(trap.XTR, trap.YT)
        xbr, ybr = _g2i(trap.XBR, trap.YB)
        xbl, ybl = _g2i(trap.XBL, trap.YB)
        result.append((xtl, ytl, xtr, ytr, xbr, ybr, xbl, ybl))
    return result


def _traps_to_icon_with_gxy(trapezoids: list, ix1: float, iy1: float, ix2: float, iy2: float,
                             gx_min: float, gx_max: float, gy_min: float, gy_max: float
                             ) -> list[tuple]:
    """Same as _traps_to_icon but uses pre-computed game bounds."""
    gw = gx_max - gx_min
    gh = gy_max - gy_min
    iw_map = ix2 - ix1
    ih_map = iy2 - iy1

    def _g2i(gx: float, gy: float) -> tuple[float, float]:
        return (ix1 + (gx - gx_min) / gw * iw_map,
                iy1 + (gy_max - gy) / gh * ih_map)

    result = []
    for trap in trapezoids:
        xtl, ytl = _g2i(trap.XTL, trap.YT)
        xtr, ytr = _g2i(trap.XTR, trap.YT)
        xbr, ybr = _g2i(trap.XBR, trap.YB)
        xbl, ybl = _g2i(trap.XBL, trap.YB)
        result.append((xtl, ytl, xtr, ytr, xbr, ybr, xbl, ybl))
    return result


# ── Overlay portal helpers (WorldMap+-only) ───────────────────────────────────

def _portal_dest_name(src_map_id: int, pix: float, piy: float) -> str:
    """Infer portal destination: nearest neighbor centroid in icon space."""
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


def _load_live_portal_cache() -> None:
    """Load portal_live_cache.json into _live_portal_cache."""
    global _live_portal_cache
    if not _LIVE_PORTAL_CACHE_FILE or not os.path.isfile(_LIVE_PORTAL_CACHE_FILE):
        return
    try:
        with open(_LIVE_PORTAL_CACHE_FILE, "r", encoding="utf-8-sig") as fh:
            raw = json.load(fh)
        _live_portal_cache = {int(k): v for k, v in raw.items()}
        Py4GW.Console.Log(MODULE_NAME,
            f"Live portal cache loaded: {len(_live_portal_cache)} maps cached.",
            Py4GW.Console.MessageType.Info)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Live portal cache load error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _save_live_portal_cache() -> None:
    """Persist _live_portal_cache to portal_live_cache.json."""
    if not _LIVE_PORTAL_CACHE_FILE:
        return
    try:
        with open(_LIVE_PORTAL_CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump({str(k): v for k, v in _live_portal_cache.items()}, fh, indent=2)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Live portal cache save error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _load_portal_all_data() -> None:
    """Load portal_all.json into _PORTAL_ALL_DATA (all known portals)."""
    global _PORTAL_ALL_DATA
    _PORTAL_ALL_DATA.clear()
    if not _PORTAL_ALL_FILE or not os.path.isfile(_PORTAL_ALL_FILE):
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
                obj: dict = {
                    "portal_index": idx,
                    "global_id": gid,
                }
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
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Portal-all loaded: {len(_PORTAL_ALL_DATA)} maps, {total} portals.",
            Py4GW.Console.MessageType.Info,
        )
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Portal-all load error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _save_portal_all_data() -> None:
    """Persist _PORTAL_ALL_DATA to portal_all.json."""
    if not _PORTAL_ALL_FILE:
        return
    try:
        out = {
            "_schema": "gw_portal_all",
            "_version": 1,
            "_comment": (
                "Complete portal catalog used by WorldMap+ for drawing dots.\n"
                "Contains linked and unlinked portals per map.\n"
                "global_id uses map_id * 1000 + portal_index."
            ),
            "maps": {str(k): v for k, v in sorted(_PORTAL_ALL_DATA.items())},
        }
        with open(_PORTAL_ALL_FILE, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Portal-all save error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _rebuild_portal_all_data() -> None:
    """Rebuild _PORTAL_ALL_DATA from DAT portals, live cache and portal_links metadata.
    Entries that were manually added to portal_all.json (maps with no DAT portals
    and no live-cache data) are preserved so they are not erased on rebuild."""
    global _PORTAL_ALL_DATA

    # Load what is currently on disk so we can preserve manual entries.
    existing_on_disk: dict[int, list[dict]] = {}
    if _PORTAL_ALL_FILE and os.path.isfile(_PORTAL_ALL_FILE):
        try:
            with open(_PORTAL_ALL_FILE, "r", encoding="utf-8-sig") as fh:
                raw = json.load(fh)
            for k, v in raw.get("maps", {}).items():
                existing_on_disk[int(k)] = v
        except Exception:
            pass

    rebuilt: dict[int, list[dict]] = {}

    for mid, bnd in _ICON_BOUNDS.items():
        if bnd is None:
            continue
        by_index: dict[int, dict] = {}

        # 1) Offline DAT portals (or live-cached fallback)
        portals = []
        # Never overwrite manually-curated maps
        if mid in _MANUAL_PORTAL_MAPS:
            if existing_on_disk.get(mid):
                rebuilt[mid] = existing_on_disk[mid]
            continue
        try:
            portals = FfnaMapMethods.GetTravelPortalsForMap(mid)
        except Exception:
            portals = []
        # For maps without a DAT entry: prefer any manually-curated on-disk entry
        # over the live cache, since live TravelPortals may belong to the previous map.
        if not portals and not FfnaMapMethods.HasDatEntry(mid) and existing_on_disk.get(mid):
            pass   # leave portals empty → fall through to step 2/3 which will use on-disk data
        elif not portals and mid in _live_portal_cache:
            from types import SimpleNamespace
            cached = _live_portal_cache[mid]
            portals = [
                SimpleNamespace(x=e.get("x", 0.0), y=e.get("y", 0.0))
                for e in cached.get("portals", cached)
                if isinstance(e, dict)
            ]

        if portals:
            portals_sorted = sorted(portals, key=lambda p: (round(float(p.x), 1), round(float(p.y), 1)))
            for idx, tp in enumerate(portals_sorted):
                gid = mid * 1000 + idx
                entry = {
                    "portal_index": idx,
                    "global_id": gid,
                    "game_x": float(tp.x),
                    "game_y": float(tp.y),
                }
                linked = _PORTAL_LINKS.get(gid)
                if linked:
                    entry["linked_to"] = int(linked)
                by_index[idx] = entry

        # 2) Linked portal metadata from portal_links.json (authoritative IDs/coords)
        for gid, (gx, gy) in _PORTAL_GAME_POS.items():
            if gid // 1000 != mid:
                continue
            idx = int(gid % 1000)
            entry = by_index.get(idx, {"portal_index": idx, "global_id": int(gid)})
            entry["global_id"] = int(gid)
            entry["game_x"] = float(gx)
            entry["game_y"] = float(gy)
            linked = _PORTAL_LINKS.get(int(gid))
            if linked:
                entry["linked_to"] = int(linked)
            by_index[idx] = entry

        # 3) Ensure every linked gid exists even if coords are missing
        for gid, linked in _PORTAL_LINKS.items():
            if gid // 1000 != mid:
                continue
            idx = int(gid % 1000)
            entry = by_index.get(idx, {"portal_index": idx, "global_id": int(gid)})
            entry["global_id"] = int(gid)
            entry["linked_to"] = int(linked)
            by_index[idx] = entry

        if by_index:
            rebuilt[mid] = [by_index[i] for i in sorted(by_index.keys())]

    # Preserve manually-added entries for maps that produced no data from DAT/live sources.
    for mid, entries in existing_on_disk.items():
        if mid not in rebuilt and entries:
            rebuilt[mid] = entries

    _PORTAL_ALL_DATA = rebuilt
    _save_portal_all_data()
    total = sum(len(v) for v in rebuilt.values())
    Py4GW.Console.Log(
        MODULE_NAME,
        f"Portal-all rebuilt: {len(rebuilt)} maps, {total} portals.",
        Py4GW.Console.MessageType.Info,
    )


def _load_portal_destinations() -> None:
    """Load portal_destinations.json into _PORTAL_DEST_DATA."""
    global _PORTAL_DEST_DATA
    _PORTAL_DEST_DATA.clear()
    _dest_file = os.path.join(_SCRIPT_DIR, "portal_destinations.json")
    if os.path.isfile(_dest_file):
        try:
            with open(_dest_file, "r", encoding="utf-8-sig") as fh:
                raw = json.load(fh)
            for k, entries in raw.get("portals", {}).items():
                _PORTAL_DEST_DATA[int(k)] = entries
            defined = sum(1 for entries in _PORTAL_DEST_DATA.values()
                          for e in entries if e.get("dest_map_id", 0) != 0)
            Py4GW.Console.Log(MODULE_NAME,
                f"Portal destinations loaded: {len(_PORTAL_DEST_DATA)} maps, {defined} resolved.",
                Py4GW.Console.MessageType.Info)
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Portal destinations load error: {e}",
                              Py4GW.Console.MessageType.Warning)
    _load_portal_links()  # always reload links too


def _ensure_portal_dots(map_id: int, is_live: bool) -> None:
    """Lazily build portal dot positions for map_id (live or offline .dat)."""
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
                                    model_file_id=e["model_file_id"])
                    for e in cached.get("portals", cached) if isinstance(e, dict)
                ]
                Py4GW.Console.Log(MODULE_NAME,
                    f"Map {map_id}: using {len(portals)} live-cached portal(s) (no DAT entry).",
                    Py4GW.Console.MessageType.Info)
    except Exception:
        _PORTAL_ICON_POS[map_id] = []
        return

    def _build_neighbor_fallback_dots() -> list[tuple]:
        neighbors = sorted(_MAP_NEIGHBORS.get(map_id, set()))
        cx = (ix1 + ix2) * 0.5
        cy = (iy1 + iy2) * 0.5
        inset = 1.0
        out: list[tuple] = []
        if not neighbors:
            idx = 0
            gid = map_id * 1000 + idx
            key = (map_id, idx)
            _PORTAL_TO_GLOBAL_ID[key] = gid
            _GLOBAL_ID_TO_PORTAL[gid] = key
            return [(cx, cy, "", idx, gid)]
        for i, nb in enumerate(neighbors):
            nb_center = _MAP_CENTROIDS.get(nb)
            if not nb_center:
                continue
            nx, ny = nb_center
            dx = nx - cx
            dy = ny - cy
            if dx == 0.0 and dy == 0.0:
                continue
            t_candidates: list[float] = []
            if dx > 0.0:
                t_candidates.append((ix2 - cx) / dx)
            elif dx < 0.0:
                t_candidates.append((ix1 - cx) / dx)
            if dy > 0.0:
                t_candidates.append((iy2 - cy) / dy)
            elif dy < 0.0:
                t_candidates.append((iy1 - cy) / dy)
            t_hit = min((t for t in t_candidates if t > 0.0), default=None)
            if t_hit is None:
                continue
            pix = cx + dx * t_hit
            piy = cy + dy * t_hit
            pix = max(ix1 + inset, min(ix2 - inset, pix))
            piy = max(iy1 + inset, min(iy2 - inset, piy))
            idx = i
            gid = map_id * 1000 + idx
            key = (map_id, idx)
            _PORTAL_TO_GLOBAL_ID[key] = gid
            _GLOBAL_ID_TO_PORTAL[gid] = key
            out.append((pix, piy, _map_name_cached(nb), idx, gid))
        if not out:
            idx = 0
            gid = map_id * 1000 + idx
            key = (map_id, idx)
            _PORTAL_TO_GLOBAL_ID[key] = gid
            _GLOBAL_ID_TO_PORTAL[gid] = key
            out.append((cx, cy, "", idx, gid))
        return out

    _cached_extents = None
    if not pathing_maps and map_id in _live_portal_cache:
        ce = _live_portal_cache[map_id]
        if isinstance(ce, dict) and "extents" in ce:
            _cached_extents = ce["extents"]

    # Use portal_all.json (complete linked+unlinked list)
    # - always for non-live maps
    # - for live maps only as fallback when no online portals were found
    # - also for live maps that have no DAT entry (e.g. EotN dungeons), where
    #   GetTravelPortals() may return portals belonging to the previous map
    has_dat = FfnaMapMethods.HasDatEntry(map_id)
    if (not is_live) or (not portals) or (is_live and not has_dat):
        entries = _PORTAL_ALL_DATA.get(map_id, [])
        if entries:
            # Build pathing extents when available (accurate projection)
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

            iw_map = ix2 - ix1
            ih_map = iy2 - iy1
            cx2    = (ix1 + ix2) * 0.5
            cy2    = (iy1 + iy2) * 0.5
            inset2 = 1.0
            radius2 = max(2.0, min(abs(ix2 - ix1), abs(iy2 - iy1)) * 0.22)

            specs: list[tuple[int, int, float | None, float | None, int]] = []
            for e in entries:
                try:
                    pidx = int(e.get("portal_index", e.get("index", -1)))
                except Exception:
                    continue
                if pidx < 0:
                    continue
                gid = int(e.get("global_id", map_id * 1000 + pidx))
                try:
                    gx = float(e["game_x"]) if "game_x" in e else None
                except Exception:
                    gx = None
                try:
                    gy = float(e["game_y"]) if "game_y" in e else None
                except Exception:
                    gy = None
                linked_gid = int(e.get("linked_to", _PORTAL_LINKS.get(gid, 0)) or 0)
                specs.append((pidx, gid, gx, gy, linked_gid))
            specs.sort(key=lambda x: x[0])

            dots_all: list[tuple] = []
            n_specs = max(1, len(specs))
            for order, (pidx, gid, gx, gy, linked_gid) in enumerate(specs):
                has_game = gx is not None and gy is not None
                if has_game and ext_ok:
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
                            if dx > 0.0: t_cands.append((ix2 - cx2) / dx)
                            elif dx < 0.0: t_cands.append((ix1 - cx2) / dx)
                            if dy > 0.0: t_cands.append((iy2 - cy2) / dy)
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
                            ang = (2.0 * 3.141592653589793 * order) / n_specs
                            pdx = cx2 + radius2 * math.cos(ang)
                            pdy = cy2 + radius2 * math.sin(ang)
                            pdx = max(ix1, min(ix2, pdx))
                            pdy = max(iy1, min(iy2, pdy))

                key = (map_id, pidx)
                _PORTAL_TO_GLOBAL_ID[key] = gid
                _GLOBAL_ID_TO_PORTAL[gid] = key
                if has_game:
                    dots_all.append((pdx, pdy, "", pidx, gid, gx, gy))
                else:
                    dots_all.append((pdx, pdy, "", pidx, gid))

            if dots_all:
                _PORTAL_ICON_POS[map_id] = dots_all
                # If live and we have extents, cache them for offline viewing later.
                # Never cache for manually-curated maps.
                if is_live and ext_ok and map_id not in _MANUAL_PORTAL_MAPS:
                    cache_entry = _live_portal_cache.get(map_id, {})
                    if not isinstance(cache_entry, dict):
                        cache_entry = {}
                    cache_entry["extents"] = {
                        "gx_min": gx_min2, "gx_max": gx_max2,
                        "gy_min": gy_min2, "gy_max": gy_max2,
                    }
                    _live_portal_cache[map_id] = cache_entry
                    _save_live_portal_cache()
                return

    if (not pathing_maps and _cached_extents is None) or not portals:
        fallback = _build_neighbor_fallback_dots()
        _PORTAL_ICON_POS[map_id] = fallback
        return
    if _cached_extents is not None:
        gx_min = _cached_extents["gx_min"]
        gx_max = _cached_extents["gx_max"]
        gy_min = _cached_extents["gy_min"]
        gy_max = _cached_extents["gy_max"]
    else:
        _gb3 = _compute_game_bounds(pathing_maps)
        if _gb3:
            gx_min, gx_max, gy_min, gy_max = _gb3
        else:
            gx_min = gx_max = gy_min = gy_max = float('inf')
    if gx_min == float('inf') or gx_max <= gx_min or gy_max <= gy_min:
        cx = (ix1 + ix2) * 0.5
        cy = (iy1 + iy2) * 0.5
        n = max(1, len(portals))
        radius = max(2.0, min(abs(ix2 - ix1), abs(iy2 - iy1)) * 0.22)
        dots: list[tuple] = []
        portals_sorted = sorted(portals, key=lambda p: (round(p.x, 1), round(p.y, 1)))
        json_entries = _PORTAL_DEST_DATA.get(map_id, [])
        n = max(1, len(portals_sorted))
        for idx, tp in enumerate(portals_sorted):
            if n == 1:
                pix, piy = cx, cy
            else:
                ang = (2.0 * 3.141592653589793 * idx) / n
                pix = cx + radius * math.cos(ang)
                piy = cy + radius * math.sin(ang)
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
            dots.append((pix, piy, dest, idx, gid, tp.x, tp.y))
        if not dots:
            dots = _build_neighbor_fallback_dots()
        _PORTAL_ICON_POS[map_id] = dots
        return
    gw = gx_max - gx_min
    gh = gy_max - gy_min
    iw_map = ix2 - ix1
    ih_map = iy2 - iy1
    json_entries = _PORTAL_DEST_DATA.get(map_id, [])
    portals_sorted = sorted(portals, key=lambda p: (round(p.x, 1), round(p.y, 1)))
    dots: list[tuple] = []
    for idx, tp in enumerate(portals_sorted):
        pix = ix1 + (tp.x - gx_min) / gw * iw_map
        piy = iy1 + (gy_max - tp.y) / gh * ih_map
        pix = max(ix1, min(ix2, pix))
        piy = max(iy1, min(iy2, piy))
        json_e = next((e for e in json_entries if e.get("index") == idx), None)
        if json_e and json_e.get("dest_map_id", 0) != 0:
            dest = json_e.get("dest_name") or _map_name_cached(json_e["dest_map_id"])
        else:
            dest = _portal_dest_name(map_id, pix, piy)
        key = (map_id, idx)
        gid = map_id * 1000 + idx
        _PORTAL_TO_GLOBAL_ID[key] = gid
        _GLOBAL_ID_TO_PORTAL[gid] = key
        dots.append((pix, piy, dest, idx, gid, tp.x, tp.y))
    _PORTAL_ICON_POS[map_id] = dots
    # Don't overwrite live cache for maps without a DAT entry or manually-curated maps.
    if is_live and portals and FfnaMapMethods.HasDatEntry(map_id) and map_id not in _MANUAL_PORTAL_MAPS:
        _live_portal_cache[map_id] = {
            "portals": [
                {"x": tp.x, "y": tp.y, "z": getattr(tp, 'z', 0.0),
                 "model_file_id": getattr(tp, 'model_file_id', 0)}
                for tp in portals
            ],
            "extents": {
                "gx_min": gx_min, "gx_max": gx_max,
                "gy_min": gy_min, "gy_max": gy_max,
            },
        }
        _save_live_portal_cache()



# rep_map_id → list of icon-space quad tuples (xtl,ytl,xtr,ytr,xbr,ybr,xbl,ybl)
_PMAP_CACHE: dict[int, list[tuple]] = {}
_PMAP_BUILT: set[int] = set()   # rep_ids already attempted


def _ensure_pmap(rep_id: int, icon_bnd: tuple, is_live: bool) -> None:
    """Lazily build icon-space pmap quads for rep_id if not yet cached."""
    if rep_id in _PMAP_BUILT:
        return
    _PMAP_BUILT.add(rep_id)
    ix1, iy1, ix2, iy2 = icon_bnd
    offset = _PMAP_OFFSETS.get(rep_id, (0.0, 0.0))
    try:
        if is_live:
            pathing_maps = Map.Pathing.GetPathingMaps()
        else:
            pathing_maps = Map.Pathing.GetPathingMaps(rep_id)  # offline .dat
    except Exception:
        _PMAP_CACHE[rep_id] = []
        return
    if not pathing_maps:
        _PMAP_CACHE[rep_id] = []
        return
    all_traps = [t for pm in pathing_maps for t in pm.trapezoids]
    _PMAP_CACHE[rep_id] = _traps_to_icon(all_traps, ix1, iy1, ix2, iy2, offset)


def _portal_link_entry(gid: int) -> dict:
    """Build the portal sub-object for a link entry (used by _save_portal_links)."""
    key = _GLOBAL_ID_TO_PORTAL.get(gid)
    if key is None:
        map_id  = gid // 1000
        loc_idx = gid %  1000
        key = (map_id, loc_idx)
    map_id, loc_idx = key
    meta     = _MAP_META.get(map_id)
    map_name = meta[1] if meta else f"Map {map_id}"

    game_x = game_y = None
    for entry in _PORTAL_ICON_POS.get(map_id, []):
        if entry[3] == loc_idx:
            if len(entry) >= 7:
                game_x = round(float(entry[5]), 2)
                game_y = round(float(entry[6]), 2)
            break

    dest_map_id = 0
    dest_name   = ""
    for e in _PORTAL_DEST_DATA.get(map_id, []):
        if e.get("index") == loc_idx:
            if game_x is None: game_x = e.get("game_x")
            if game_y is None: game_y = e.get("game_y")
            dest_map_id = e.get("dest_map_id", 0)
            dm = _MAP_META.get(dest_map_id)
            dest_name = dm[1] if dm else e.get("dest_name", "")
            break

    obj: dict = {
        "global_id":    gid,
        "map_id":       map_id,
        "map_name":     map_name,
        "portal_index": loc_idx,
    }
    if game_x is not None: obj["game_x"] = game_x
    if game_y is not None: obj["game_y"] = game_y
    if dest_map_id:        obj["leads_to_map_id"] = dest_map_id
    if dest_name:          obj["leads_to_map_name"] = dest_name
    return obj


def _save_portal_links() -> None:
    """Write _PORTAL_LINKS to portal_links.json with full context per entry."""
    try:
        seen:    set[tuple[int, int]] = set()
        entries: list[dict] = []
        link_id = 1
        for a_id, b_id in sorted(_PORTAL_LINKS.items()):
            pair = (min(a_id, b_id), max(a_id, b_id))
            if pair in seen:
                continue
            seen.add(pair)
            entries.append({
                "link_id":  link_id,
                "portal_a": _portal_link_entry(a_id),
                "portal_b": _portal_link_entry(b_id),
            })
            link_id += 1

        out = {
            "_schema":  "gw_portal_links",
            "_version": 1,
            "_comment": (
                "Portal connections for Guild Wars maps.\n"
                "Each link pairs two zone-transition portals.\n"
                "Managed by WorldMap+ widget – portal IDs are stable "
                "(map_id * 1000 + portal_index when no JSON exists, "
                "or sequential IDs from portal_destinations.json).\n"
                "Usable by bots and routing tools: portal_a/b contain "
                "map_id, map_name, game_x/y, and destination info."
            ),
            "links": entries,
        }
        with open(_WP._wp.portal_links_file, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
        Py4GW.Console.Log(MODULE_NAME,
            f"Saved {len(entries)} portal links to portal_links.json.",
            Py4GW.Console.MessageType.Info)
        # Keep full portal catalog in sync (linked/unlinked color state depends on this).
        _rebuild_portal_all_data()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Portal link save error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _apply_custom_dungeon_placement(entrance_gid: int, dungeon_map_id: int, dungeon_name: str) -> None:
    """Register a custom dungeon icon on the world map positioned at entrance_gid,
    and link entrance_gid ⇔ dungeon_map_id*1000 in _PORTAL_LINKS.
    Safe to call at any time (load or runtime).
    """
    entrance_map = entrance_gid // 1000
    dungeon_portal_gid = dungeon_map_id * 1000

    # 1. Map metadata
    # Force rtype = explorable (2) so GetNearestUnlockedOutpost never treats
    # this dungeon as a fast-travel destination (dungeons require walking in).
    if dungeon_map_id not in _MAP_META:
        try:
            info = MapMethods.GetMapInfo(dungeon_map_id)
            camp = int(info.campaign) if info else 4
        except Exception:
            camp = 4
        _MAP_META[dungeon_map_id] = (2, dungeon_name, camp)
    else:
        old = _MAP_META[dungeon_map_id]
        _MAP_META[dungeon_map_id] = (2, dungeon_name, old[2])

    # 2. Find entrance portal icon-space position (needs _PORTAL_ALL_DATA loaded)
    _ensure_portal_dots(entrance_map, is_live=False)
    dots = _PORTAL_ICON_POS.get(entrance_map, [])
    px = py = None
    for dot in dots:
        if len(dot) >= 5 and int(dot[4]) == entrance_gid:
            px, py = float(dot[0]), float(dot[1])
            break
    if px is None:  # fallback: centroid of entrance map
        ctr = _MAP_CENTROIDS.get(entrance_map)
        if ctr:
            px, py = ctr
        else:
            bnd = _ICON_BOUNDS.get(entrance_map)
            if bnd:
                px, py = (bnd[0] + bnd[2]) * 0.5, (bnd[1] + bnd[3]) * 0.5
            else:
                Py4GW.Console.Log(MODULE_NAME,
                    f"Custom dungeon: no icon bounds for entrance map {entrance_map}, skipping.",
                    Py4GW.Console.MessageType.Warning)
                return

    # 3. Icon bounds: small 16×16 box centered on portal dot
    half = 8.0
    icon_bnd = (px - half, py - half, px + half, py + half)
    _ICON_BOUNDS[dungeon_map_id] = icon_bnd

    # 4. Draw group
    if not any(dungeon_map_id in g[0] for g in _DRAW_GROUPS):
        meta = _MAP_META[dungeon_map_id]
        _DRAW_GROUPS.append((frozenset({dungeon_map_id}), icon_bnd, dungeon_name, meta[0], meta[2]))

    # 5. Portal link (bidirectional)
    _PORTAL_LINKS[entrance_gid]       = dungeon_portal_gid
    _PORTAL_LINKS[dungeon_portal_gid] = entrance_gid

    # 6. Global ID lookups
    _GLOBAL_ID_TO_PORTAL[dungeon_portal_gid]          = (dungeon_map_id, 0)
    _PORTAL_TO_GLOBAL_ID[(dungeon_map_id, 0)]         = dungeon_portal_gid

    # 7. Portal catalog entry so the dot is drawn inside the dungeon icon
    _PORTAL_ALL_DATA[dungeon_map_id] = [{
        "portal_index": 0,
        "global_id":    dungeon_portal_gid,
        "linked_to":    entrance_gid,
    }]
    _PORTAL_ICON_POS[dungeon_map_id] = [(px, py, _map_name_cached(entrance_map), 0, dungeon_portal_gid)]
    _PORTAL_BUILT.add(dungeon_map_id)

    # 8. Adjacency for pathing
    edge = (min(entrance_map, dungeon_map_id), max(entrance_map, dungeon_map_id))
    if edge not in _ALL_EDGES:
        _ALL_EDGES.add(edge)
        _MAP_ADJACENCY.setdefault(entrance_map, set()).add(dungeon_map_id)
        _MAP_ADJACENCY.setdefault(dungeon_map_id, set()).add(entrance_map)
        _MAP_NEIGHBORS.setdefault(entrance_map, set()).add(dungeon_map_id)
        _MAP_NEIGHBORS.setdefault(dungeon_map_id, set()).add(entrance_map)
        _wp_invalidate_world_adj()

    # 9. Visibility + tracking
    _MANUAL_PORTAL_MAPS.add(dungeon_map_id)
    _CONNECTED_MAP_IDS.add(dungeon_map_id)
    _CUSTOM_DUNGEON_MAP_IDS.add(dungeon_map_id)
    Py4GW.Console.Log(MODULE_NAME,
        f"Custom dungeon: [{dungeon_map_id}] {dungeon_name} placed at portal {entrance_gid} (map {entrance_map}).",
        Py4GW.Console.MessageType.Info)


def _load_custom_placements() -> None:
    """Load custom_placements.json and apply each dungeon placement.
    Must be called AFTER _load_portal_all_data() so portal dot positions are available.
    """
    if not os.path.isfile(_CUSTOM_PLACEMENTS_FILE):
        return
    try:
        with open(_CUSTOM_PLACEMENTS_FILE, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
        count = 0
        for entry in data.get("placements", []):
            entrance_gid   = int(entry["entrance_portal_gid"])
            dungeon_map_id = int(entry["dungeon_map_id"])
            dungeon_name   = str(entry.get("dungeon_name", f"Dungeon {dungeon_map_id}"))
            _apply_custom_dungeon_placement(entrance_gid, dungeon_map_id, dungeon_name)
            count += 1
        if count:
            Py4GW.Console.Log(MODULE_NAME,
                f"Custom dungeon placements loaded: {count} entries.",
                Py4GW.Console.MessageType.Info)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Custom placements load error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _save_custom_placements() -> None:
    """Persist custom dungeon placements to custom_placements.json."""
    entries = []
    for dungeon_map_id in sorted(_CUSTOM_DUNGEON_MAP_IDS):
        dungeon_portal_gid = dungeon_map_id * 1000
        entrance_gid = _PORTAL_LINKS.get(dungeon_portal_gid)
        if not entrance_gid:
            continue
        meta = _MAP_META.get(dungeon_map_id)
        name = meta[1] if meta else f"Map {dungeon_map_id}"
        entries.append({
            "entrance_portal_gid": entrance_gid,
            "dungeon_map_id":      dungeon_map_id,
            "dungeon_name":        name,
        })
    try:
        out = {
            "_comment": "Custom dungeon placements for WorldMap+. entrance_portal_gid: the portal in the explorable that leads into the dungeon (map_id*1000 + portal_index).",
            "placements": entries,
        }
        with open(_CUSTOM_PLACEMENTS_FILE, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
        Py4GW.Console.Log(MODULE_NAME,
            f"Custom placements saved: {len(entries)} entries.",
            Py4GW.Console.MessageType.Info)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Custom placements save error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _inject_offmap_positions() -> None:
    """Force synthetic icon-space bounds for all maps listed in _OFFMAP_PLACEMENTS."""
    gap = 10   # icon-space pixel gap between the injected box and its anchor
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
        else:  # below
            bnd = (al, ab + gap, ar, ab + gap + h)
        _ICON_BOUNDS[mid] = bnd
        if mid not in _MAP_META:
            try:
                info = MapMethods.GetMapInfo(mid)
                name = Map.GetMapName(mid) or f"Map {mid}"
                rtype = int(info.type) if info else 2
                camp  = int(info.campaign) if info else 4
            except Exception:
                name, rtype, camp = f"Map {mid}", 2, 4
            _MAP_META[mid] = (rtype, name, camp)
        Py4GW.Console.Log(MODULE_NAME,
            f"OffMap: {mid} ({_MAP_META[mid][1]}) placed {side} of {anchor_id} → {bnd}",
            Py4GW.Console.MessageType.Info)


def _build_cache() -> None:
    """Scan all map IDs and populate _ICON_BOUNDS / _MAP_META.  Called once."""
    global _cache_built
    for mid in range(1, _MAX_MAP_ID + 1):
        info = MapMethods.GetMapInfo(mid)
        if info is None:
            _ICON_BOUNDS[mid] = None
            continue

        # Only populate _MAP_META for maps with a recognised name.
        # Maps that return "Unknown Map ID" are internal/special maps that
        # should not appear as fast-travel candidates.
        try:
            _raw_name = Map.GetMapName(mid)
        except Exception:
            _raw_name = None
        if not _raw_name or _raw_name == "Unknown Map ID":
            # No valid name → skip _MAP_META (but still process icon bounds below)
            _name = None
        else:
            _name = _raw_name
            _MAP_META[mid] = (int(info.type), _name, int(info.campaign))

        # Note: flag 0x20 ("hidden from standard world map") is intentionally NOT used
        # as an exclusion criterion here.  Several outposts (e.g. map 30, Ruins of Surmia)
        # carry this flag but still have valid icon-space coordinates and travel portals.
        # Maps that truly have no icon position are handled below by the coords check.

        # Prefer primary icon coords; fall back to dupe
        if info.icon_start_x != 0 or info.icon_end_x != 0:
            l = float(info.icon_start_x)
            t = float(info.icon_start_y)
            r = float(info.icon_end_x)
            b = float(info.icon_end_y)
        elif info.icon_start_x_dupe != 0 or info.icon_end_x_dupe != 0:
            l = float(info.icon_start_x_dupe)
            t = float(info.icon_start_y_dupe)
            r = float(info.icon_end_x_dupe)
            b = float(info.icon_end_y_dupe)
        else:
            _ICON_BOUNDS[mid] = None
            continue

        # Normalise orientation and reject degenerate rects
        if l > r: l, r = r, l
        if t > b: t, b = b, t
        if l == r or t == b:
            _ICON_BOUNDS[mid] = None
            continue

        _ICON_BOUNDS[mid] = (l, t, r, b)

    # ── Inject synthetic positions for built-in off-map dungeons (e.g. map 604) ────
    _inject_offmap_positions()

    # ── Post-process: centroids, neighbor map, draw groups ─────────────────
    _DRAW_GROUPS.clear()
    _PMAP_CACHE.clear()
    _PMAP_BUILT.clear()
    _PORTAL_ICON_POS.clear()
    _PORTAL_BUILT.clear()
    _GLOBAL_ID_TO_PORTAL.clear()
    _PORTAL_TO_GLOBAL_ID.clear()
    _PORTAL_LINKS.clear()
    _MAP_CENTROIDS.clear()
    _MAP_NEIGHBORS.clear()

    # Build icon-space centroids
    for mid, bnd in _ICON_BOUNDS.items():
        if bnd is not None:
            l, t, r, b = bnd
            _MAP_CENTROIDS[mid] = ((l + r) * 0.5, (t + b) * 0.5)

    # Build neighbor lookup from _ALL_EDGES
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
        lbl = "\n".join(m[1] for m in meta_list)
        _DRAW_GROUPS.append((frozenset(mids), bnd, lbl, rtype, camp))

    # Inject mutual edges between pmap-sharing maps into the global adjacency graph.
    # Maps that share the same world-map icon bound are physically co-located and
    # must be treated as directly reachable from each other so that IsPath() and
    # GetNearestUnlockedOutpost() return correct results for all IDs in a group.
    _pmap_new_edges = False
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
                    _pmap_new_edges = True
    if _pmap_new_edges:
        _wp_invalidate_world_adj()

    _cache_built = True
    n = sum(1 for v in _ICON_BOUNDS.values() if v is not None)
    g = len(_DRAW_GROUPS)
    Py4GW.Console.Log(MODULE_NAME,
        f"Cache built: {n} maps, {g} draw groups.",
        Py4GW.Console.MessageType.Info)
    _load_portal_destinations()   # also calls _load_portal_links() at the end
    _load_portal_all_data()
    linked_maps = {int(gid // 1000) for gid in _PORTAL_LINKS.keys()}
    # When Developer mode is off, only maps with known portal links should be
    # shown. Keep _CONNECTED_MAP_IDS limited to portal-linked maps.
    _CONNECTED_MAP_IDS.clear()
    _CONNECTED_MAP_IDS.update(linked_maps)
    # Custom dungeon placements must be applied AFTER portal_all data is loaded
    # so that _ensure_portal_dots can resolve entrance portal icon positions.
    _load_custom_placements()
    missing_linked = [mid for mid in linked_maps if mid not in _PORTAL_ALL_DATA]
    if (not _PORTAL_ALL_DATA) or missing_linked:
        _rebuild_portal_all_data()


# ── Region type → packed color ──────────────────────────────────────────────
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


# ── UI state ──────────────────────────────────────────────────────────────────
_show_frames         = [True]
_show_pmap_current   = [False]
_show_pmap_all       = [False]
_pmap_opacity        = [0.2]
_show_portals        = [False]
_show_portals_3d     = [False]
_show_portal_ids     = [False]
_opacity             = [0.75]
_show_debug          = [False]
_show_developer      = [False]
_show_player_cross        = [False]
_show_mtnw_waypoint_dots  = [False]
_show_reachable_unvisited = [False]
_show_hero_loadout        = [False]

# ── Hero Loadout state ────────────────────────────────────────────────────────
_HL_MAX_SLOTS   = 7
_HL_HERO_IDS: list[int] = [
    int(_HeroType.Norgu), int(_HeroType.Goren), int(_HeroType.Tahlkora),
    int(_HeroType.MasterOfWhispers), int(_HeroType.AcolyteJin), int(_HeroType.Koss),
    int(_HeroType.Dunkoro), int(_HeroType.AcolyteSousuke), int(_HeroType.Melonni),
    int(_HeroType.ZhedShadowhoof), int(_HeroType.GeneralMorgahn), int(_HeroType.MagridTheSly),
    int(_HeroType.Zenmai), int(_HeroType.Olias), int(_HeroType.Razah),
    int(_HeroType.MOX), int(_HeroType.KeiranThackeray), int(_HeroType.Jora),
    int(_HeroType.PyreFierceshot), int(_HeroType.Anton), int(_HeroType.Livia),
    int(_HeroType.Hayda), int(_HeroType.Kahmu), int(_HeroType.Gwen),
    int(_HeroType.Xandra), int(_HeroType.Vekk), int(_HeroType.Ogden),
    int(_HeroType.Miku), int(_HeroType.ZeiRi),
]
_HL_HERO_NAMES: list[str] = [_HeroType(h).name for h in _HL_HERO_IDS]
_HL_COMBO_ITEMS: list[str] = ["(none)"] + _HL_HERO_NAMES
_hl_slot_ids:    list[int]  = [0] * _HL_MAX_SLOTS
_hl_auto_apply:  list[bool] = [False]
_hl_applying:    list[bool] = [False]
_hl_last_map:    list[int]  = [-1]

def _hl_hero_id_to_combo(hero_id: int) -> int:
    try:
        return _HL_HERO_IDS.index(hero_id) + 1
    except ValueError:
        return 0

def _hl_combo_to_hero_id(idx: int) -> int:
    if idx <= 0 or idx > len(_HL_HERO_IDS):
        return 0
    return _HL_HERO_IDS[idx - 1]

def _hl_apply_loadout_coroutine():
    """Kick all heroes, then add the first N slots allowed by the current map."""
    _hl_applying[0] = True
    try:
        if not Map.IsOutpost():
            Py4GW.Console.Log(MODULE_NAME, "Hero Loadout: not in outpost, skipped.",
                              Py4GW.Console.MessageType.Warning)
            return
        max_slots = max(0, Map.GetMaxPartySize())
        heroes_to_add = [_hl_slot_ids[i] for i in range(min(max_slots, _HL_MAX_SLOTS))
                         if _hl_slot_ids[i] != 0]
        Party.Heroes.KickAllHeroes()
        yield from Routines.Yield.wait(600)
        for hero_id in heroes_to_add:
            Party.Heroes.AddHero(hero_id)
            yield from Routines.Yield.wait(250)
        names = [_HeroType(h).name for h in heroes_to_add]
        Py4GW.Console.Log(MODULE_NAME,
            f"Hero Loadout applied ({max_slots} slots): {', '.join(names) if names else 'empty'}",
            Py4GW.Console.MessageType.Info)
    finally:
        _hl_applying[0] = False

def _hl_trigger_apply() -> None:
    if not _hl_applying[0]:
        GLOBAL_CACHE.Coroutines.append(_hl_apply_loadout_coroutine())


def _refresh_hero_slot_owner_ids() -> None:
    """Patch stale OwnerAgentID values in shared memory hero slots after a map change.

    Agent IDs are reassigned on every map transition, so any hero slot written in a
    previous map carries the old OwnerAgentID.  GetHeroSlotByHeroData rejects slots
    where both the stored and live values are non-zero but differ, causing a new slot
    to be submitted every frame until the old one expires (5 s) -> spam.

    This runs once per map change: for each of my heroes, find its slot by
    HeroID + AccountEmail (both stable) and write the fresh OwnerAgentID so the
    regular update_callback finds the slot immediately.
    """
    try:
        from Py4GWCoreLib import Player, Party
        my_email   = str(Player.GetAccountEmail() or "").strip()
        my_agent   = Player.GetAgentID()
        if not my_email or not my_agent:
            return
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccounts()
        shmem_max    = 64  # SHMEM_MAX_PLAYERS
        for hero_data in Party.GetHeroes():
            owner_agent = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
            if owner_agent != my_agent:
                continue  # not my hero
            if owner_agent == 0:
                continue
            hero_id = hero_data.hero_id.GetID()
            for i in range(shmem_max):
                slot = all_accounts.AccountData[i]
                if not slot.IsHero:
                    continue
                if slot.AgentData.HeroID != hero_id:
                    continue
                stored_email = str(slot.AccountEmail).strip()
                if stored_email != my_email:
                    continue
                # Found the slot for my hero - refresh the stale OwnerAgentID
                slot.AgentData.OwnerAgentID = owner_agent
                break
    except Exception:
        pass  # non-critical; update_callback will retry next tick


def _hl_load_current_team() -> bool:
    """Read the currently active heroes from the party and write them into _hl_slot_ids.

    Returns True if at least one hero was found, False otherwise.
    """
    try:
        heroes = GLOBAL_CACHE.Party.GetHeroes()
    except Exception:
        return False
    if not heroes:
        return False
    for i in range(_HL_MAX_SLOTS):
        if i < len(heroes):
            try:
                _hl_slot_ids[i] = heroes[i].hero_id.GetID()
            except Exception:
                _hl_slot_ids[i] = 0
        else:
            _hl_slot_ids[i] = 0
    _wmp_ini_save()
    return True


def _hl_trigger_apply_delayed() -> None:
    """Queue a hero loadout apply with a short settling delay (for on-zone use)."""
    def _delayed():
        yield from Routines.Yield.wait(800)
        yield from _hl_apply_loadout_coroutine()
    if not _hl_applying[0]:
        GLOBAL_CACHE.Coroutines.append(_delayed())

# Auto-explore: iterate through all reachable-but-unvisited outposts
_auto_explore_active: list[bool] = [False]
_auto_explore_target: list[int]  = [0]     # map_id of the outpost currently being visited

# Travel button data: built each frame by _draw_overlay, consumed by _draw_travel_buttons
# Each entry: (rep_map_id, btn_x, btn_y)  – screen pixel coords
_travel_btn_data: list[tuple[int, float, float]] = []
_travel_btn_seen:  set[int] = set()   # dedup by map_id
# Queued map targets added via the '+' button next to green travel buttons.
_travel_queue: deque[int] = deque()
_travel_queue_inflight_target: list[int] = [0]
_travel_queue_dispatch_ms: list[int] = [0]
_travel_coroutine_active: list[bool] = [False]  # True while _travel_button_coroutine is running (before runner activates)

# UI state for link editor
_link_input_a    = [0]
_link_input_b    = [0]
_link_click_mode  = [False]  # click-to-link mode active
_link_pending_gid = [0]     # first selected portal GID (waiting for second click)
_moveto_portal_id = [0]     # portal ID entered for Move To
# Custom dungeon placement editor state
_cp_entrance_gid  = [0]        # entrance portal GID (e.g. 556002)
_cp_dungeon_id    = [0]        # dungeon map ID   (e.g. 581)
_cp_dungeon_name  = [""]       # dungeon display name (mutable string)
# Tracks which map IDs were added via custom dungeon placements (for save filter)
_CUSTOM_DUNGEON_MAP_IDS: set[int] = set()

# ── INI persistence ──────────────────────────────────────────────────────────────
_WMP_INI_PATH     = "Widgets/WorldMap+"
_WMP_INI_FILENAME = "WorldMap+.ini"
_wmp_ini_key: list[str]  = [""]
_wmp_ini_ready: list[bool] = [False]


def _wmp_ini_try_init() -> bool:
    """Register handler and load settings from the account-scoped INI.
    Returns True once ready, False while account is not yet available."""
    if _wmp_ini_ready[0]:
        return True
    key = _IniManager().ensure_key(_WMP_INI_PATH, _WMP_INI_FILENAME)
    if not key:
        return False
    _wmp_ini_key[0] = key
    ini = _IniManager()
    s = "Settings"
    hl = "HeroLoadout"
    # Display settings
    _show_frames[0]              = ini.read_bool(key, s, "show_frames",          True)
    _opacity[0]                  = ini.read_float(key, s, "opacity",             0.75)
    _show_reachable_unvisited[0] = ini.read_bool(key, s, "show_reachable",       False)
    _show_hero_loadout[0]        = ini.read_bool(key, s, "show_hero_loadout",    False)
    # Hero Loadout
    _hl_auto_apply[0] = ini.read_bool(key, hl, "auto_apply", False)
    for _i in range(_HL_MAX_SLOTS):
        _hl_slot_ids[_i] = ini.read_int(key, hl, f"slot_{_i}", 0)
    _wmp_ini_ready[0] = True
    return True


def _wmp_ini_save() -> None:
    """Persist all saveable WorldMap+ settings to the INI file."""
    key = _wmp_ini_key[0]
    if not key:
        return
    ini = _IniManager()
    s = "Settings"
    hl = "HeroLoadout"
    ini.write_key(key, s, "show_frames",       _show_frames[0])
    ini.write_key(key, s, "opacity",           _opacity[0])
    ini.write_key(key, s, "show_reachable",    _show_reachable_unvisited[0])
    ini.write_key(key, s, "show_hero_loadout", _show_hero_loadout[0])
    ini.write_key(key, hl, "auto_apply",       _hl_auto_apply[0])
    for _i in range(_HL_MAX_SLOTS):
        ini.write_key(key, hl, f"slot_{_i}",  _hl_slot_ids[_i])

# ── Route path state (driven by travel buttons / MoveToMapid) ────────────────
_path_gids:       list[int] = []   # ordered GID sequence: [exit1,enter1,exit2,enter2,...]
_path_map_names:  list[str] = []   # map name steps for display

# Cache for IsPath(current_map, target) – invalidated on map change
_is_path_cache: dict[int, bool] = {}  # key = target map_id
# Cache for maps reachable only via fast-travel (ft_id != current_map)
_is_ft_path_cache: dict[int, bool] = {}  # key = target map_id

# Tracks the last map for which 3D portal labels were built live
_portal_3d_last_map: list[int] = [-1]

# Timing state for the active travel route
_travel_route_start_ms:   list[int] = [0]                    # timestamp when route started
_travel_hop_times:        list[tuple[int, int]] = []         # [(start_ms, end_ms|0), ...] per hop; end_ms=0 = still running
_travel_prev_done_count:  list[int] = [-1]                   # done_count from previous frame
_path_name_offset:        list[int] = [0]                    # hops trimmed from _path_map_names front (absolute index correction)


def _path_first_pending_idx() -> int:
    """Return the first gid index in _path_gids that has not yet been traveled.
    Uses _mtm_route[0] and current map to determine progress.
    Returns 0 when no active route (show full path).
    The returned index is adjusted so the 'enter' portal on the current map
    is still shown (drawing starts one segment before first pending hop).
    """
    route = _mtm_route[0]
    if route is None or not route.get("found"):
        return 0
    waypoints = route.get("waypoints", [])
    if not waypoints:
        return 0
    current_map = Map.GetMapID()
    for hop_idx, wp in enumerate(waypoints):
        if int(wp.get("from_map", 0)) == current_map:
            # hop_idx is the first pending hop; gid index = hop_idx * 2
            # subtract 1 so the 'enter' gid of the current map leg is still drawn
            return max(0, hop_idx * 2 - 1)
    # current map not in remaining waypoints → already at destination, show nothing
    return len(_path_gids)


_debug_last_map     = [-1]      # detect map transitions
_debug_last_filter_reason = [""]  # dedupe current-map filter reason logs

# ── WorldPathing demo panel state ────────────────────────────────────────────
_show_wp_demo          = [False]
_wp_demo_start         = [0]
_wp_demo_target        = [0]
_wp_is_path_result:    list[bool | None] = [None]   # None / True / False
_wp_get_path_result:   list      = []   # list of dicts from GetPath waypoints
_wp_get_path_found     = [False]
_wp_get_path_maps:     list[str] = []
_wp_get_path_full:     list[dict | None] = [None]  # full dict returned by GetPath()
_wp_move_result:       list[bool | None] = [None]   # None / True / False
_wp_move_map_result:   list[bool | None] = [None]   # None / True / False
_wp_route_overlay:     list[dict] = []   # per-hop icon-space coords built by _build_route_overlay
_travel_route_overlay: list[dict] = []   # same format, built when a travel button is clicked
_pathfinder_win_h      = [0.0]    # measured height of pathfinder panel for stacking

# MoveToNextWaypoint / MoveToMapid timing constants (used by WorldPathing-owned coroutines)
_MTNW_ARRIVAL_RADIUS         = 200.0
_MTNW_WAYPOINT_RADIUS        = 140.0
_MTNW_PUSHTHROUGH_TIMEOUT_MS = 6000
_MTM_HOP_MAX_ATTEMPTS        = 6
_MTM_HOP_TIMEOUT_MS          = 120000
_MTM_LOAD_TIMEOUT_MS         = 60000


def _abort_worldmap_movement() -> None:
    """Cancel any active movement (delegates to WorldPathing._abort_wp_movement)."""
    _abort_wp_movement()
    _travel_queue.clear()
    _travel_queue_inflight_target[0] = 0
    _travel_queue_dispatch_ms[0] = 0
    _travel_coroutine_active[0] = False


def _enqueue_travel_target(map_id: int) -> None:
    """Append a map target to the travel queue if it is not already queued."""
    if map_id <= 0:
        return
    if map_id in _travel_queue:
        return
    _travel_queue.append(map_id)


def _resort_travel_queue() -> None:
    """Re-sort the travel queue by path distance from the current map (nearest first)."""
    if len(_travel_queue) < 2:
        return
    current_map = Map.GetMapID()
    items = list(_travel_queue)

    def _sort_key(m: int) -> float:
        d = _path_distance(current_map, m)
        return d if d is not None else float('inf')

    items.sort(key=_sort_key)
    _travel_queue.clear()
    _travel_queue.extend(items)


def _process_travel_queue() -> None:
    """Dispatch queued travel targets one by one when no movement runner is active."""
    if not _travel_queue:
        _travel_queue_inflight_target[0] = 0
        _travel_queue_dispatch_ms[0] = 0
        if _auto_explore_active[0]:
            _auto_explore_active[0] = False
            _auto_explore_target[0] = 0
            Py4GW.Console.Log(MODULE_NAME,
                "Unlock All: complete – all queued outposts visited.",
                Py4GW.Console.MessageType.Info)
        return

    now_ms = int(Utils.GetBaseTimestamp())
    current_map = Map.GetMapID()

    # Drop already-reached targets from the head of the queue.
    while _travel_queue and _travel_queue[0] == current_map:
        _travel_queue.popleft()
    if _travel_queue:
        _resort_travel_queue()
    if not _travel_queue:
        _travel_queue_inflight_target[0] = 0
        _travel_queue_dispatch_ms[0] = 0
        if _auto_explore_active[0]:
            _auto_explore_active[0] = False
            _auto_explore_target[0] = 0
            Py4GW.Console.Log(MODULE_NAME,
                "Unlock All: complete – all queued outposts visited.",
                Py4GW.Console.MessageType.Info)
        return

    active = _mtm_runner_active[0] or _mtnw_runner_active[0] or _travel_coroutine_active[0]
    if active:
        return

    head = _travel_queue[0]

    # If a runner or coroutine is still active, stay put regardless of elapsed time.
    # Only check for a stale dispatch when everything is truly idle.
    if _travel_queue_inflight_target[0] == head:
        if active:
            return
        if Map.IsMapLoading():
            return
        if Map.GetMapID() == head:
            _travel_queue.popleft()
        else:
            _head_name = (_MAP_META.get(head) or (None, f"Map {head}"))[1]
            Py4GW.Console.Log(
                MODULE_NAME,
                f"Queue: travel to {_head_name} [{head}] did not start, retrying.",
                Py4GW.Console.MessageType.Warning,
            )
            # Don't skip — reset and retry next frame
            _travel_queue_inflight_target[0] = 0
            _travel_queue_dispatch_ms[0] = 0
        return

    _target_name = (_MAP_META.get(head) or (None, f"Map {head}"))[1]

    # Skip if no portal path exists from any reachable outpost to this target.
    ft = GetNearestUnlockedOutpost(head, current_map)
    if ft is None:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Queue: no path to {_target_name} [{head}], skipping.",
            Py4GW.Console.MessageType.Warning,
        )
        _travel_queue.popleft()
        if _travel_queue:
            _resort_travel_queue()
        return

    GLOBAL_CACHE.Coroutines.append(_travel_button_coroutine(head, fast_travel_first=True))
    _travel_queue_inflight_target[0] = head
    _travel_queue_dispatch_ms[0] = now_ms
    Py4GW.Console.Log(
        MODULE_NAME,
        f"Queue: starting travel to {_target_name} [{head}] ({len(_travel_queue)} queued).",
        Py4GW.Console.MessageType.Info,
    )


def _mtm_log_debug(message: str) -> None:
    if not _show_debug[0]:
        return
    Py4GW.Console.Log(
        MODULE_NAME,
        f"[MoveToMapid] {message}",
        Py4GW.Console.MessageType.Info,
    )


_PMAP_GAME_BOUNDS: dict[int, tuple[float, float, float, float]] = {}
_MAP_GAME_BOUNDS_CACHE: dict[int, tuple[float, float, float, float]] = {}


def _get_player_icon_pos(map_id: int) -> tuple[float, float] | None:
    """Return icon-space (ix, iy) for the current player position on map_id, or None."""
    icon_bnd = _ICON_BOUNDS.get(map_id)
    if not icon_bnd:
        return None
    if map_id not in _PMAP_GAME_BOUNDS:
        try:
            pathing_maps = Map.Pathing.GetPathingMaps()
        except Exception:
            return None
        if not pathing_maps:
            return None
        _gb4 = _compute_game_bounds(pathing_maps)
        if _gb4 is None:
            return None
        _PMAP_GAME_BOUNDS[map_id] = _gb4
    gx_min, gx_max, gy_min, gy_max = _PMAP_GAME_BOUNDS[map_id]
    ix1, iy1, ix2, iy2 = icon_bnd
    gw = gx_max - gx_min
    gh = gy_max - gy_min
    if not gw or not gh:
        return None
    px, py = Player.GetXY()
    return (
        ix1 + (px - gx_min) / gw * (ix2 - ix1),
        iy1 + (gy_max - py) / gh * (iy2 - iy1),
    )


def _mtnw_path_icon_points(map_id: int) -> list[tuple[float, float]]:
    """Convert current _mtnw_path game coords to icon-space points for drawing."""
    if not _mtnw_path:
        return []

    icon_bnd = _ICON_BOUNDS.get(map_id)
    if not icon_bnd:
        return []
    ix1, iy1, ix2, iy2 = icon_bnd

    # Use cached game bounds if available (populated by _get_player_icon_pos or _get_map_game_bounds)
    if map_id not in _PMAP_GAME_BOUNDS:
        try:
            pathing_maps = Map.Pathing.GetPathingMaps()
        except Exception:
            return []
        if not pathing_maps:
            return []
        _gb5 = _compute_game_bounds(pathing_maps)
        if _gb5 is None:
            return []
        _PMAP_GAME_BOUNDS[map_id] = _gb5

    gx_min, gx_max, gy_min, gy_max = _PMAP_GAME_BOUNDS[map_id]
    gw = gx_max - gx_min
    gh = gy_max - gy_min
    if not gw or not gh:
        return []
    iw_map = ix2 - ix1
    ih_map = iy2 - iy1

    out: list[tuple[float, float]] = []
    for gx, gy in _mtnw_path:
        pix = ix1 + (gx - gx_min) / gw * iw_map
        piy = iy1 + (gy_max - gy) / gh * ih_map
        out.append((pix, piy))
    return out


def _get_map_game_bounds(map_id: int) -> tuple[float, float, float, float] | None:
    """Return cached game-space bounds (gx_min, gx_max, gy_min, gy_max) for map_id."""
    bnd = _MAP_GAME_BOUNDS_CACHE.get(map_id)
    if bnd is not None:
        return bnd

    if map_id in _PMAP_GAME_BOUNDS:
        bnd = _PMAP_GAME_BOUNDS[map_id]
        _MAP_GAME_BOUNDS_CACHE[map_id] = bnd
        return bnd

    try:
        if map_id == Map.GetMapID():
            pathing_maps = Map.Pathing.GetPathingMaps()
        else:
            pathing_maps = FfnaMapMethods.GetPathingMapsForMap(map_id)
    except Exception:
        pathing_maps = []

    if pathing_maps:
        _gb6 = _compute_game_bounds(pathing_maps)
        if _gb6 is not None:
            _MAP_GAME_BOUNDS_CACHE[map_id] = _gb6
            return _gb6

    cached = _live_portal_cache.get(map_id)
    if isinstance(cached, dict):
        ext = cached.get("extents")
        if isinstance(ext, dict):
            try:
                gx_min = float(ext["gx_min"])
                gx_max = float(ext["gx_max"])
                gy_min = float(ext["gy_min"])
                gy_max = float(ext["gy_max"])
            except Exception:
                return None
            if gx_max > gx_min and gy_max > gy_min:
                bnd = (gx_min, gx_max, gy_min, gy_max)
                _MAP_GAME_BOUNDS_CACHE[map_id] = bnd
                return bnd

    return None


def _game_to_icon_xy(map_id: int, gx: float, gy: float) -> tuple[float, float] | None:
    """Convert one game-space point to icon-space for a specific map."""
    icon_bnd = _ICON_BOUNDS.get(map_id)
    if not icon_bnd:
        return None

    gb = _get_map_game_bounds(map_id)
    if gb is None:
        return None
    gx_min, gx_max, gy_min, gy_max = gb
    gw = gx_max - gx_min
    gh = gy_max - gy_min
    if gw <= 0.0 or gh <= 0.0:
        return None

    ix1, iy1, ix2, iy2 = icon_bnd
    ix = ix1 + (float(gx) - gx_min) / gw * (ix2 - ix1)
    iy = iy1 + (gy_max - float(gy)) / gh * (iy2 - iy1)
    return (ix, iy)


def _build_segment_icon_path(map_id: int,
                             start_gxy: tuple[float, float] | None,
                             goal_gxy: tuple[float, float] | None) -> list[tuple[float, float]]:
    """Build a local polyline in icon-space for one map segment (start->goal)."""
    if start_gxy is None or goal_gxy is None:
        return []

    try:
        if map_id == Map.GetMapID():
            pathing_maps = Map.Pathing.GetPathingMaps()
        else:
            pathing_maps = FfnaMapMethods.GetPathingMapsForMap(map_id)
    except Exception:
        pathing_maps = []

    game_points: list[tuple[float, float]]
    if pathing_maps:
        try:
            nav = _PathingNavMesh(pathing_maps, map_id)
            astar = _PathingAStar(nav)
            if astar.search(start_gxy, goal_gxy):
                game_points = astar.get_path()
            else:
                game_points = [start_gxy, goal_gxy]
        except Exception:
            game_points = [start_gxy, goal_gxy]
    else:
        game_points = [start_gxy, goal_gxy]

    icon_points: list[tuple[float, float]] = []
    for gx, gy in game_points:
        ip = _game_to_icon_xy(map_id, gx, gy)
        if ip is None:
            continue
        if icon_points and abs(icon_points[-1][0] - ip[0]) < 0.5 and abs(icon_points[-1][1] - ip[1]) < 0.5:
            continue
        icon_points.append(ip)

    return icon_points


def _get_portal_icon_xy(gid: int) -> tuple[float, float] | None:
    """Return icon-space (ix, iy) for a portal GID, building portal dots if needed."""
    key = _GLOBAL_ID_TO_PORTAL.get(gid)
    if key is None:
        key = (gid // 1000, gid % 1000)
    map_id, loc_idx = key
    _ensure_portal_dots(map_id, is_live=False)
    for entry in _PORTAL_ICON_POS.get(map_id, []):
        if int(entry[3]) == loc_idx:
            return float(entry[0]), float(entry[1])
    return None


def _build_route_overlay(result: dict) -> list[dict]:
    """Resolve icon-space coords for all portals in a GetPath result."""
    segs: list[dict] = []
    if not result.get("found"):
        return segs
    prev_enter_gid = 0
    for i, wp in enumerate(result["waypoints"]):
        from_map = int(wp["from_map"])
        to_map = int(wp["to_map"])
        exit_gid = int(wp["exit_gid"])
        enter_gid = int(wp["enter_gid"])

        exit_xy  = _get_portal_icon_xy(wp["exit_gid"])
        enter_xy = _get_portal_icon_xy(wp["enter_gid"])

        start_game: tuple[float, float] | None = None
        if i == 0 and from_map == Map.GetMapID():
            try:
                px, py = Player.GetXY()
                start_game = (float(px), float(py))
            except Exception:
                start_game = None
        if start_game is None and prev_enter_gid:
            pe_key = _GLOBAL_ID_TO_PORTAL.get(prev_enter_gid)
            if pe_key and int(pe_key[0]) == from_map:
                start_game = _get_portal_game_xy(prev_enter_gid)

        goal_game = _get_portal_game_xy(exit_gid)
        path_ixy = _build_segment_icon_path(from_map, start_game, goal_game)

        segs.append({
            "from_map":  from_map,
            "to_map":    to_map,
            "exit_ix":   exit_xy[0]  if exit_xy  else None,
            "exit_iy":   exit_xy[1]  if exit_xy  else None,
            "enter_ix":  enter_xy[0] if enter_xy else None,
            "enter_iy":  enter_xy[1] if enter_xy else None,
            "path_ixy":  path_ixy,
        })
        prev_enter_gid = enter_gid
    return segs


def _get_portal_game_xy(gid: int) -> tuple[float, float] | None:
    """Return (game_x, game_y) for a portal GID, or None if not available."""
    key = _GLOBAL_ID_TO_PORTAL.get(gid)
    if key is None:
        key = (gid // 1000, gid % 1000)
    map_id, loc_idx = key

    for entry in _PORTAL_ICON_POS.get(map_id, []):
        if entry[3] == loc_idx and len(entry) >= 7:
            return float(entry[5]), float(entry[6])

    for e in _PORTAL_DEST_DATA.get(map_id, []):
        if e.get("index") == loc_idx:
            gx = e.get("game_x")
            gy = e.get("game_y")
            if gx is not None and gy is not None:
                return float(gx), float(gy)
    return None


def IsPath(start_map_id: int, target_map_id: int) -> bool:
    """Return True if a portal-linked route exists. Delegates to WorldPathing.IsPath."""
    return _WP_IsPath(start_map_id, target_map_id)


_reachable_list_cache: list[dict] = []
_reachable_list_last_map: list[int] = [-1]

def _path_distance(start_map: int, end_map: int) -> float | None:
    """Game-unit path distance between two maps. Delegates to WorldPathing."""
    return _wp_path_distance(start_map, end_map)


def _get_reachable_adj() -> dict[int, set[int]]:
    """Return cached combined adjacency. Delegates to WorldPathing.get_world_adj()."""
    return _wp_get_world_adj()


def invalidate_reachable_adj() -> None:
    """Call this whenever portal links change so the combined adj is rebuilt."""
    _wp_invalidate_world_adj()        # also invalidate the shared WorldPathing cache
    _reachable_list_last_map[0] = -1  # force list rebuild on next frame
    _reachable_list_cache.clear()


def GetReachableMaps(start_map_id: int) -> list[dict]:
    """Return all maps reachable from start_map_id via portal links OR static adjacency.

    Each entry in the returned list is a dict:
      { "map_id": int, "name": str, "hops": int }

    "hops" is the minimum number of map transitions (portal crossings) needed.
    The start map itself is not included.

    Two data sources are merged:
      1. _MAP_ADJACENCY – static hand-curated adjacency (always available)
      2. portal_links.json – dynamic links recorded via the Diagnostics tool
    """
    from collections import deque as _deque
    combined = _get_reachable_adj()

    if start_map_id not in combined:
        return []

    visited: dict[int, int] = {start_map_id: 0}
    queue: _deque = _deque([(start_map_id, 0)])
    while queue:
        cur_map, hops = queue.popleft()
        for next_map in combined.get(cur_map, set()):
            if next_map not in visited:
                visited[next_map] = hops + 1
                queue.append((next_map, hops + 1))

    return [
        {"map_id": mid, "name": _map_name_cached(mid), "hops": h}
        for mid, h in sorted(visited.items(), key=lambda kv: (kv[1], kv[0]))
        if mid != start_map_id
    ]


def GetFastTravelMaps() -> list[dict]:
    """Return all outposts/towns/cities the current player can fast-travel to.

    Uses the game's unlocked-map bitmap to determine which maps the character
    has previously visited and can instantly travel to via the world map.

    Each entry in the returned list is a dict:
      { "map_id": int, "name": str, "type": int, "campaign": int }

    "type" values (RegionType):
      2  = Explorable (not included – can't fast-travel to explorables)
      5  = Mission Outpost
      6  = Cooperative Mission
      7  = Challenge Mission
      8  = Competitive Mission
      9  = Elite Mission
      10 = Outpost/Town

    Returns an empty list when the world context is not available (loading screen).
    """
    result: list[dict] = []
    for mid, meta in _MAP_META.items():
        rtype, name, campaign = meta
        # Explorables (type 2) cannot be fast-traveled to
        if rtype == _RT_EXPLORABLE:
            continue
        # Check the game's own unlock bitmap for this character
        if Map.IsMapUnlocked(mid):
            result.append({"map_id": mid, "name": name, "type": rtype, "campaign": campaign})
    result.sort(key=lambda m: (m["campaign"], m["name"]))
    return result


def GetNearestUnlockedOutpost(
    target_map_id: int,
    from_map_id: int | None = None,
) -> dict | None:
    """Return the best unlocked outpost to fast-travel to for reaching
    *target_map_id*.  When *from_map_id* is given the cost also accounts
    for how far that outpost is from the player's current position.

    Delegates to WorldPathing.GetNearestUnlockedOutpost.

    Return value:
      { "map_id": int, "name": str, "hops": int, "distance": float | None }
    or None if no unlocked outpost is reachable.
    """
    # Inject live portal game-positions so path_distance can use tp.x/tp.y
    # coordinates (real game units) rather than falling back to None for
    # maps not yet present in portal_links.json.
    _WP._PORTAL_ICON_POS_EXT = _PORTAL_ICON_POS
    _WP._ICON_BOUNDS_EXT = _ICON_BOUNDS  # inject map icon bounds for geographic tiebreaking
    return _WP_GetNearestUnlockedOutpost(target_map_id, from_map_id)


def GetNearestFastTravelTo(
    target_map_id: int,
    from_map_id: int | None = None,
) -> dict | None:
    """Convenience alias for GetNearestUnlockedOutpost.

    Kept for backwards-compatibility and readability in travel-UI code.
    """
    return GetNearestUnlockedOutpost(target_map_id, from_map_id)


def GetPath(start_map_id: int, target_map_id: int) -> dict:
    """Return full inter-map route with map ids, names and portal waypoints.

    Delegates to WorldPathing.GetPath.  Before calling, inject _PORTAL_ICON_POS
    (overlay-only live game coords) so WorldPathing's _get_portal_game_xy can
    use them when portal_links.json does not yet have explicit game coords.
    """
    # Inject live portal icon positions so WorldPathing can resolve game coords
    _WP._PORTAL_ICON_POS_EXT = _PORTAL_ICON_POS
    return _WP_GetPath(start_map_id, target_map_id)


def GetNextWaypointXY(path: dict) -> tuple[float, float] | None:
    """Return (x, y) of the first portal waypoint in a GetPath() result."""
    if not path or not path.get("found") or not path.get("waypoints"):
        return None
    wp = path["waypoints"][0]
    gx, gy = wp.get("game_x"), wp.get("game_y")
    if gx is None or gy is None:
        return None
    return float(gx), float(gy)


def MoveToNextWaypoint(target_map_id: int, path: dict | None = None) -> bool:
    """Start autonomous movement to first portal waypoint. Delegates to WorldPathing."""
    return _WP_MoveToNextWaypoint(target_map_id, path)


def MoveToMapid(target_map_id: int) -> bool:
    """Build and execute a full inter-map route to target_map_id. Delegates to WorldPathing."""
    _WP._PORTAL_ICON_POS_EXT = _PORTAL_ICON_POS  # inject live coords
    return _WP_MoveToMapid(target_map_id)


def MoveToMapID(target_map_id: int) -> bool:
    """Alias for MoveToMapid."""
    return _WP_MoveToMapID(target_map_id)


def _travel_button_coroutine(target_map_id: int, fast_travel_first: bool = False):
    """Coroutine triggered by a Travel button click.

    Steps:
      0. (Loadout) If hero loadout auto-apply is active and heroes are
         configured, kick all heroes before leaving so the party is empty
         during travel.  Auto-apply on zone will re-add them on arrival.
      1. (Queue mode) If fast_travel_first is True and no direct portal path
         exists, fast-travel to the nearest unlocked outpost first.
         When fast_travel_first is False (green button) the route starts from
         the player's current location without any preliminary fast-travel.
      2. Build the route overlay from the current position and start MoveToMapid.
    """
    _travel_coroutine_active[0] = True
    try:
        yield from _travel_button_coroutine_inner(target_map_id, fast_travel_first)
    finally:
        _travel_coroutine_active[0] = False


def _travel_button_coroutine_inner(target_map_id: int, fast_travel_first: bool = False):
    current_map_at_start = Map.GetMapID()

    # ── Step 0: kick heroes before leaving if loadout auto-apply is on ──────
    # (Heroes are always kicked again in Step 1 before any fast-travel, so
    # this step is only needed when starting from the current outpost directly.)
    _hl_has_loadout = _hl_auto_apply[0] and any(h != 0 for h in _hl_slot_ids)
    if _hl_has_loadout and Map.IsOutpost() and not fast_travel_first:
        try:
            Party.Heroes.KickAllHeroes()
            yield from Routines.Yield.wait(600)
        except Exception:
            pass

    # Queue mode: always fast-travel to the nearest staging outpost so that
    # every queue item starts reliably from an outpost, not just when IsPath
    # returns False.  (IsPath may return True for a hop-connected target even
    # when the player is mid-exploration and cannot reach it without FT.)
    if fast_travel_first:
        ft = GetNearestUnlockedOutpost(target_map_id, current_map_at_start)
        ft_id = ft["map_id"] if ft else None
    else:
        ft_id = None

    # ── Step 1: fast-travel to nearest unlocked outpost if needed ───────────
    # In queue mode always FT to the optimal staging outpost.
    # The inner guard (ft_id != current_map_at_start) handles the case where
    # we are already at the best outpost and no FT is needed.
    if fast_travel_first:
        if ft_id and ft_id != current_map_at_start:
            Py4GW.Console.Log(MODULE_NAME,
                f"Travel: fast-traveling to nearest outpost {ft_id} ({ft.get('name','?')}) "
                f"before routing to {target_map_id}.",
                Py4GW.Console.MessageType.Info)
            try:
                Party.Heroes.KickAllHeroes()
                Party.LeaveParty()
                yield from Routines.Yield.wait(600)
            except Exception:
                pass
            Map.TravelToDistrict(ft_id, 0, 0)
            _t0 = int(Utils.GetBaseTimestamp())
            while not Map.IsMapLoading():
                if int(Utils.GetBaseTimestamp()) - _t0 > 10_000:
                    break
                yield from Routines.Yield.wait(150)
            loaded = yield from Routines.Yield.Map.WaitforMapLoad(ft_id, log=False, timeout=60_000)
            if not loaded:
                Py4GW.Console.Log(MODULE_NAME,
                    f"Travel: could not load fast-travel map {ft_id}, aborting.",
                    Py4GW.Console.MessageType.Warning)
                return
            yield from Routines.Yield.wait(500)

    # ── Step 2: build route overlay and start movement ──────────────────────
    current_map = Map.GetMapID()
    route = GetPath(current_map, target_map_id)
    if route.get("found"):
        first_wp   = route["waypoints"][0] if route.get("waypoints") else None
        first_gid  = first_wp.get("exit_gid") if first_wp else "?"
        first_next = first_wp.get("to_map")   if first_wp else "?"
        Py4GW.Console.Log(MODULE_NAME,
            f"Travel step2: map {current_map} -> target {target_map_id} "
            f"({len(route['waypoints'])} hops), first exit_gid={first_gid} -> map {first_next}",
            Py4GW.Console.MessageType.Info)
        _travel_route_overlay[:] = _build_route_overlay(route)
        _path_map_names[:] = route.get("map_names", [])
        gids: list[int] = []
        for wp in route.get("waypoints", []):
            gids.extend([wp["exit_gid"], wp["enter_gid"]])
        _path_gids[:] = gids
        _now = int(Utils.GetBaseTimestamp())
        _num_hops = max(0, len(_path_map_names) - 1)
        _travel_route_start_ms[0] = _now
        _travel_hop_times[:] = [(_now, 0)] + [(0, 0)] * (_num_hops - 1)
        _travel_prev_done_count[0] = 0
        _path_name_offset[0] = 0
    else:
        _travel_route_overlay.clear()
        _path_gids.clear()
        _path_map_names.clear()
        _travel_route_start_ms[0] = 0
        _travel_hop_times.clear()
        _travel_prev_done_count[0] = -1
        _path_name_offset[0] = 0

    # Reset the dispatch timestamp so the 1-frame gap between this coroutine
    # ending and the movement runner activating doesn't trigger a false timeout.
    _travel_queue_dispatch_ms[0] = int(Utils.GetBaseTimestamp())
    MoveToMapid(target_map_id)


def _should_show(rtype: int) -> bool:
    if rtype in (_RT_EXPLORABLE, _RT_OUTPOST, _RT_TOWN, _RT_CITY,
                 _RT_MISSION_OUT, _RT_COOP, _RT_CHALLENGE, _RT_COMPETITIVE, _RT_ELITE):
        return _show_frames[0]
    return False


# ── World-map overlay draw ─────────────────────────────────────────────────────

_PORTAL_3D_LABEL_RADIUS = 1000.0  # kept for reference, no longer used as filter


def _draw_mtnw_path_3d() -> None:
    """Draw the active BottingTree move-path as a 3D overlay in-game."""
    from Py4GWCoreLib.WorldPathing import _wp
    bt_tree = _wp.mtnw_bt_tree
    if bt_tree is None:
        return
    if Map.WorldMap.IsWindowOpen():
        return
    # Mirror relevant BT blackboard keys into the draw helper so DrawMovePath can read them.
    src_bb = bt_tree.blackboard
    dst_bb = _bt_draw_helper.blackboard
    for _key in (
        "move_state", "move_reason", "move_target",
        "move_path_points", "move_path_index", "move_path_count",
        "move_current_waypoint", "move_current_waypoint_index",
        "move_last_move_point", "move_resume_recovery_active",
        "move_resume_recovery_reason", "move_resume_recovery_restart_pending",
        "move_current_pause_reason",
    ):
        if _key in src_bb:
            dst_bb[_key] = src_bb[_key]
    _bt_draw_helper.DrawMovePath()


def _draw_portal_ids_3d() -> None:
    """Draw portal GIDs as 3D world-space labels near the player."""
    if not _show_developer[0]:
        return
    if not _show_portals_3d[0]:
        return
    if Map.IsMapLoading():
        return
    if Map.WorldMap.IsWindowOpen():
        return
    cmap = Map.GetMapID()
    if cmap <= 0:
        return
    # Force a live rebuild whenever the player has entered a new map so that
    # real game coordinates are always used (not stale offline/fallback data).
    if cmap != _portal_3d_last_map[0]:
        _PORTAL_BUILT.discard(cmap)
        _PORTAL_ICON_POS.pop(cmap, None)
        _portal_3d_last_map[0] = cmap
    _ensure_portal_dots(cmap, is_live=True)
    portals = _PORTAL_ICON_POS.get(cmap)
    if not portals:
        return

    _overlay3d.BeginDraw()
    for dot in portals:
        if len(dot) < 7:
            continue
        gx, gy = dot[5], dot[6]
        gid    = dot[4]
        z = _Overlay.FindZ(gx, gy)
        linked = _PORTAL_LINKS.get(int(gid))
        if linked:
            km = _GLOBAL_ID_TO_PORTAL.get(linked)
            dest_map  = km[0] if km else linked // 1000
            dest_name = _map_name_cached(dest_map)
            label = f"[{int(gid)}] \u2192 {linked} ({dest_name})"
            color = 0xFF44EE66   # green – linked
        else:
            label = f"[{int(gid)}] unlinked"
            color = 0xFFAAAAAA   # gray – no link
        _overlay3d.DrawText3D(gx, gy, z + 20.0, label, color, autoZ=False, centered=True, scale=0.9)
    _overlay3d.EndDraw()


def _draw_overlay() -> None:
    """Draw map rects and connection lines on top of the GW World Map."""
    if not Map.WorldMap.IsWindowOpen():
        return

    # Hide all drawings when zoom is not 1.0 (100%)
    if not _zoom_is_default():
        return

    frame_info = Map.WorldMap.GetFrameInfo()
    if frame_info is None:
        return

    # Screen rect of the World Map content area
    sc = frame_info.GetContentCoords()     # (left, top, right, bottom) screen px
    if not sc or sc[2] <= sc[0] or sc[3] <= sc[1]:
        return
    sl, st, sr, sb = float(sc[0]), float(sc[1]), float(sc[2]), float(sc[3])
    sw = sr - sl
    sh = sb - st

    # Currently visible world region in icon space
    il, it, ir, ib = Map.WorldMap.GetWindowCoords()  # (top_left.x, top_left.y, bottom_right.x, bottom_right.y)
    iw = ir - il
    ih = ib - it
    if iw == 0.0 or ih == 0.0:
        return

    # Inline transform: icon coords → screen pixels
    def _i2s(ix: float, iy: float) -> tuple[float, float]:
        return sl + (ix - il) / iw * sw, st + (iy - it) / ih * sh

    alpha        = max(10, min(255, int(_opacity[0] * 255)))
    alpha_border = min(255, alpha + 60)
    current_map  = Map.GetMapID()
    line_color   = Utils.RGBToColor(255, 220, 60, int(alpha * 0.85))
    cur_fill     = Utils.RGBToColor(255, 230, 50, 210)
    cur_border   = Utils.RGBToColor(255, 255, 100, 255)

    # Determine current campaign group for filtering.
    # Default to Prophecies/EotN (group 1) so that Factions and Nightfall maps
    # are hidden until portal links for those campaigns are recorded.
    current_camp_group = 1
    if True:
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

    # Transparent full-screen overlay window (needed so draw_list calls are
    # drawn in front of the World Map UI layer)
    PyImGui.set_next_window_pos(sl, st)
    PyImGui.set_next_window_size(sw, sh)
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
    if not PyImGui.begin("##wm_plus_overlay", ow_flags):
        PyImGui.end()
        return

    # ── Pass 1: collect screen centroids, draw map rectangles ─────────────
    centroids:     dict[int, tuple[float, float]] = {}
    visible_groups: list[tuple] = []   # (rep_id, icon_bnd, is_current, quad_x1y1x2y2)
    current_highlight_drawn = False
    _travel_btn_data.clear()
    _travel_btn_seen.clear()

    for group_ids, bounds, group_label, rtype, camp in _DRAW_GROUPS:
        contains_current = current_map in group_ids

        # Campaign filter
        if current_camp_group != -1 and _campaign_group(camp) != current_camp_group:
            if _show_debug[0] and contains_current:
                reason = (
                    f"filtered current map {current_map}: campaign mismatch "
                    f"(group={_campaign_group(camp)} current={current_camp_group})"
                )
                if _debug_last_filter_reason[0] != reason:
                    Py4GW.Console.Log(MODULE_NAME, reason, Py4GW.Console.MessageType.Info)
                    _debug_last_filter_reason[0] = reason
            continue

        is_standard_type = rtype in (_RT_EXPLORABLE, _RT_OUTPOST, _RT_TOWN, _RT_CITY,
                                       _RT_MISSION_OUT, _RT_COOP, _RT_CHALLENGE, _RT_COMPETITIVE, _RT_ELITE)
        # Standard types are always processed so buttons/labels appear even when frames are off.
        if not is_standard_type:
            if _show_debug[0] and contains_current:
                reason = f"filtered current map {current_map}: type filter disabled (rtype={rtype})"
                if _debug_last_filter_reason[0] != reason:
                    Py4GW.Console.Log(MODULE_NAME, reason, Py4GW.Console.MessageType.Info)
                    _debug_last_filter_reason[0] = reason
            continue

        if _show_debug[0] and contains_current and _debug_last_filter_reason[0]:
            Py4GW.Console.Log(
                MODULE_NAME,
                f"current map {current_map} no longer filtered",
                Py4GW.Console.MessageType.Info,
            )
            _debug_last_filter_reason[0] = ""

        l, t, r, b = bounds
        x1, y1 = _i2s(l, t)
        x2, y2 = _i2s(r, b)

        # Cull: skip if completely outside the visible screen rect.
        # Exception: never cull the group that contains the current map.
        if not contains_current and (x2 < sl or x1 > sr or y2 < st or y1 > sb):
            continue

        cx = (x1 + x2) * 0.5
        cy = (y1 + y2) * 0.5
        # Register centroid for every map ID in this group (used by adjacency lines)
        for gid in group_ids:
            centroids[gid] = (cx, cy)

        rw = x2 - x1
        rh = y2 - y1
        min_dim = min(abs(rw), abs(rh))

        is_current = current_map in group_ids
        # When Developer mode is off, skip the frame for maps that have no
        # portal connections at all (not in _CONNECTED_MAP_IDS).
        has_portals = any(mid in _CONNECTED_MAP_IDS for mid in group_ids)
        if not is_current and not has_portals and not _show_developer[0]:
            continue
        if is_current:
            PyImGui.draw_list_add_rect(x1, y1, x2, y2, cur_border, 2.0, 0, 2.0)
            current_highlight_drawn = True
        elif _show_frames[0]:
            PyImGui.draw_list_add_rect(x1, y1, x2, y2, _type_border(rtype, alpha_border), 1.0, 0, 1.0)

        sorted_ids = sorted(group_ids)
        lines      = group_label.split("\n")
        line_h     = 13.0
        n_lines    = len(lines)
        frames_on  = _show_frames[0]

        # Vertical anchor: top-left when frames on, vertically centered at 2/3 height when off
        if frames_on:
            block_top = y1 + 2.0
            btn_top   = y1 + 1.0
        else:
            center_y  = y1 + (y2 - y1) * (2.0 / 3.0)
            block_top = center_y - (n_lines * line_h) * 0.5
            btn_top   = block_top - 1.0

        # Collect travel buttons FIRST so label drawing knows the horizontal indent.
        btn_ids_here: set[int] = set()
        if rw >= 28.0 and (y2 - y1) >= 14.0:
            for i, mid in enumerate(sorted_ids):
                if mid == current_map or mid in _travel_btn_seen:
                    continue
                if not _show_developer[0] and mid not in _CONNECTED_MAP_IDS:
                    continue
                raw_lbl = f"{lines[i] if i < len(lines) else lines[-1]} [{mid}]"
                if frames_on:
                    bx = x1 + 2.0
                else:
                    # Center the (button + label) block horizontally in the frame
                    bx = cx - (20.0 + len(raw_lbl) * 6.5) * 0.5
                by = btn_top + i * line_h
                _travel_btn_seen.add(mid)
                _travel_btn_data.append((mid, bx, by))
                btn_ids_here.add(mid)

        # Labels: shown for all visible maps regardless of frames_on (size-gated).
        # When frames off: horizontally centered, vertically at 2/3 height.
        if min_dim >= 14 or is_current:
            lbl_color = Utils.RGBToColor(255, 255, 255, min(255, alpha + 80))
            for i, line in enumerate(lines):
                mid     = sorted_ids[i] if i < len(sorted_ids) else -1
                if not _show_developer[0] and mid >= 0 and mid != current_map and mid not in _CONNECTED_MAP_IDS:
                    continue
                raw     = f"{line} [{mid}]" if mid >= 0 else line
                has_btn = mid in btn_ids_here
                if frames_on:
                    lbl_x = x1 + 36.0 if has_btn else x1 + 2.0
                else:
                    raw_w   = len(raw) * 6.5
                    total_w = (36.0 + raw_w) if has_btn else raw_w
                    lbl_x   = cx - total_w * 0.5 + (36.0 if has_btn else 0.0)
                lbl_y = block_top + i * line_h
                PyImGui.draw_list_add_text(lbl_x, lbl_y, lbl_color, raw)

        # Record for pmap pass
        rep_id = min(group_ids)
        visible_groups.append((rep_id, bounds, is_current, group_ids))

    # Fallback: always draw current map highlight even when filtered out
    if not current_highlight_drawn:
        cur_bnd = _ICON_BOUNDS.get(current_map)
        if cur_bnd is not None:
            l, t, r, b = cur_bnd
            x1, y1 = _i2s(l, t)
            x2, y2 = _i2s(r, b)
            if not (x2 < sl or x1 > sr or y2 < st or y1 > sb):
                PyImGui.draw_list_add_rect(x1, y1, x2, y2, cur_border, 2.0, 0, 2.0)
                if _show_frames[0]:
                    lbl_color = Utils.RGBToColor(255, 255, 255, min(255, alpha + 80))
                    cur_meta = _MAP_META.get(current_map)
                    cur_name = cur_meta[1] if cur_meta else (Map.GetMapName(current_map) or f"Map {current_map}")
                    cur_name = f"{cur_name} [{current_map}]"
                    PyImGui.draw_list_add_text(x1 + 2.0, y1 + 2.0, lbl_color, cur_name)

    # ── Pass 2b: draw pmap trapezoids for all visible maps ───────────────
    if (_show_pmap_current[0] or _show_pmap_all[0]) and _show_developer[0]:
        pmap_alpha = max(1, min(255, int(_pmap_opacity[0] * 255)))
        trap_color = Utils.RGBToColor(180, 255, 180, pmap_alpha)
        for rep_id, icon_bnd, is_current, _grp in visible_groups:
            if not _show_pmap_all[0] and not is_current:
                continue
            _ensure_pmap(rep_id, icon_bnd, is_live=is_current)
            traps = _PMAP_CACHE.get(rep_id)
            if not traps:
                continue
            for xtl, ytl, xtr, ytr, xbr, ybr, xbl, ybl in traps:
                sx_tl, sy_tl = _i2s(xtl, ytl)
                sx_tr, sy_tr = _i2s(xtr, ytr)
                sx_br, sy_br = _i2s(xbr, ybr)
                sx_bl, sy_bl = _i2s(xbl, ybl)
                xs = (sx_tl, sx_tr, sx_br, sx_bl)
                ys = (sy_tl, sy_tr, sy_br, sy_bl)
                if max(xs) < sl or min(xs) > sr or max(ys) < st or min(ys) > sb:
                    continue
                # Expand 0.6 px vertically to close sub-pixel gaps between scanline slabs
                sy_tl -= 0.6; sy_tr -= 0.6
                sy_br += 0.6; sy_bl += 0.6
                PyImGui.draw_list_add_quad_filled(
                    sx_tl, sy_tl, sx_tr, sy_tr,
                    sx_br, sy_br, sx_bl, sy_bl,
                    trap_color)

    # ── Pass 3: draw travel portal dots for all visible maps ────────────────
    # visible_portal_sx is populated by Pass 3 and consumed by the custom dungeon
    # button block below; must be declared here so the latter always has access.
    visible_portal_sx: dict[int, tuple[float, float]] = {}  # global_id -> (sx, sy)
    if _show_portals[0] and _show_developer[0]:
        portal_fill          = Utils.RGBToColor(255,  80,  80, 230)
        portal_border        = Utils.RGBToColor(255, 200, 200, 255)
        portal_fill_linked   = Utils.RGBToColor( 60, 210,  60, 230)
        portal_border_linked = Utils.RGBToColor(180, 255, 180, 255)
        portal_fill_pending  = Utils.RGBToColor(255, 230,  50, 230)
        portal_border_pending= Utils.RGBToColor(255, 255, 150, 255)
        id_color             = Utils.RGBToColor(255, 255, 100, 255)
        link_color           = Utils.RGBToColor(255, 200,  50, 200)

        # Click-to-link: detect right click on a portal
        click_hit_gid = 0
        if _link_click_mode[0] and PyImGui.is_mouse_clicked(1):
            io = PyImGui.get_io()
            mx, my = io.mouse_pos_x, io.mouse_pos_y
            best_dist = 12.0   # pixels – click radius
            for rep_id2, icon_bnd2, is_cur2, grp_ids2 in visible_groups:
                for mid2 in grp_ids2:
                    _ensure_portal_dots(mid2, is_live=is_cur2)
                    for pt in _PORTAL_ICON_POS.get(mid2, []):
                        pix2, piy2, _d2, _li2, g2 = pt[0], pt[1], pt[2], pt[3], pt[4]
                        sx2, sy2 = _i2s(pix2, piy2)
                        if sx2 < sl or sx2 > sr or sy2 < st or sy2 > sb:
                            continue
                        dist = ((mx - sx2) ** 2 + (my - sy2) ** 2) ** 0.5
                        if dist < best_dist:
                            best_dist = dist
                            click_hit_gid = g2
            if click_hit_gid:
                if _link_pending_gid[0] == 0:
                    # First portal selected
                    _link_pending_gid[0] = click_hit_gid
                elif _link_pending_gid[0] != click_hit_gid:
                    # Second portal – create link
                    a_id2 = _link_pending_gid[0]
                    b_id2 = click_hit_gid
                    _PORTAL_LINKS[a_id2] = b_id2
                    _PORTAL_LINKS[b_id2] = a_id2
                    invalidate_portal_adj()
                    invalidate_reachable_adj()
                    _save_portal_links()
                    _link_pending_gid[0] = 0
                    _link_click_mode[0]  = False

        # Collect icon positions visible this frame for link-line drawing
        # (dict already declared before Pass 3)

        # Collect all portal dots, group co-located portals by pixel position
        # key = (round(sx), round(sy))  ->  list of (gid, linked, pending)
        pos_clusters: dict[tuple[int,int], list[tuple[int,bool,bool]]] = {}

        processed_dot_maps: set[int] = set()

        def _add_map_portal_dots(mid: int, is_live_mid: bool) -> None:
            if mid in processed_dot_maps:
                return
            processed_dot_maps.add(mid)
            if not is_live_mid:
                linked_gids_mid = {gid for gid in _PORTAL_LINKS.keys() if (gid // 1000) == mid}
                if linked_gids_mid:
                    cached = _PORTAL_ICON_POS.get(mid, [])
                    cached_gids = {
                        int(pt[4]) for pt in cached
                        if isinstance(pt, (list, tuple)) and len(pt) >= 5 and pt[4]
                    }
                    if cached_gids and cached_gids.isdisjoint(linked_gids_mid):
                        _PORTAL_BUILT.discard(mid)
                        _PORTAL_ICON_POS.pop(mid, None)
            _ensure_portal_dots(mid, is_live=is_live_mid)
            dots_for_mid = _PORTAL_ICON_POS.get(mid, [])
            for pix, piy, _dest, _local_idx, gid, *_gc in dots_for_mid:
                sx, sy = _i2s(pix, piy)
                if sx < sl or sx > sr or sy < st or sy > sb:
                    continue
                if gid:
                    visible_portal_sx[gid] = (sx, sy)
                linked  = gid in _PORTAL_LINKS
                pending = gid == _link_pending_gid[0]
                key = (int(round(sx)), int(round(sy)))
                pos_clusters.setdefault(key, []).append((gid, linked, pending))

        # 1) Existing behaviour: all maps currently visible in the world-map window
        current_map_seen = False
        for rep_id, icon_bnd, is_current, group_ids in visible_groups:
            for mid in sorted(group_ids):
                is_mid_live = (mid == current_map)
                if is_mid_live:
                    current_map_seen = True
                _add_map_portal_dots(mid, is_mid_live)

        # 2) Also include all maps known to the portal datasets in the active campaign
        #    (portal_all.json + linked maps), even if not in visible_groups.
        linked_maps: set[int] = set()
        for gid in _PORTAL_LINKS.keys():
            km = _GLOBAL_ID_TO_PORTAL.get(gid)
            mid = km[0] if km else (gid // 1000)
            if mid > 0:
                linked_maps.add(mid)

        all_portal_maps: set[int] = set(linked_maps)
        all_portal_maps.update(int(mid) for mid in _PORTAL_ALL_DATA.keys())

        for mid in sorted(all_portal_maps):
            if current_camp_group != -1:
                meta = _MAP_META.get(mid)
                camp = int(meta[2]) if meta else None
                if camp is None:
                    try:
                        mi = MapMethods.GetMapInfo(mid)
                        camp = int(mi.campaign) if mi else None
                    except Exception:
                        camp = None
                if camp is not None and _campaign_group(camp) != current_camp_group:
                    continue
            _add_map_portal_dots(mid, is_live_mid=(mid == current_map))

        # 3) Keep safety fallback for current map
        if not current_map_seen:
            _add_map_portal_dots(current_map, True)

        # Draw one dot per cluster; always show GIDs when _show_portal_ids is on
        for (psx, psy), cluster in pos_clusters.items():
            fsx, fsy = float(psx), float(psy)
            any_linked  = any(c[1] for c in cluster)
            any_pending = any(c[2] for c in cluster)
            if any_pending:
                fill   = portal_fill_pending
                border = portal_border_pending
            elif any_linked:
                fill   = portal_fill_linked
                border = portal_border_linked
            else:
                fill   = portal_fill
                border = portal_border
            PyImGui.draw_list_add_circle_filled(fsx, fsy, 5.0, fill, 10)
            PyImGui.draw_list_add_circle(fsx, fsy, 5.0, border, 10, 1.0)
            if any_pending:
                PyImGui.draw_list_add_circle(fsx, fsy, 9.0, portal_border_pending, 12, 1.5)
            if _show_portal_ids[0] or _show_debug[0]:
                gid_ids: set[int] = set()
                for c in cluster:
                    gid0 = int(c[0]) if c and c[0] else 0
                    if gid0:
                        gid_ids.add(gid0)
                        linked0 = _PORTAL_LINKS.get(gid0)
                        if linked0:
                            gid_ids.add(int(linked0))
                gid_strs = [str(g) for g in sorted(gid_ids)]
                if gid_strs:
                    lbl = ",".join(gid_strs)
                    PyImGui.draw_list_add_text(fsx + 6.0, fsy - 6.0, id_color, lbl)

        # Hover tooltip: show portal IDs for the icon cluster under the mouse
        hovered_cluster_ids: list[int] = []
        io = PyImGui.get_io()
        mx, my = io.mouse_pos_x, io.mouse_pos_y
        hover_radius = 8.0
        best_d2 = hover_radius * hover_radius
        for (psx, psy), cluster in pos_clusters.items():
            d2 = (mx - float(psx)) ** 2 + (my - float(psy)) ** 2
            if d2 <= best_d2:
                best_d2 = d2
                gid_ids2: set[int] = set()
                for c in cluster:
                    gid1 = int(c[0]) if c and c[0] else 0
                    if gid1:
                        gid_ids2.add(gid1)
                        linked1 = _PORTAL_LINKS.get(gid1)
                        if linked1:
                            gid_ids2.add(int(linked1))
                hovered_cluster_ids = sorted(gid_ids2)

        if hovered_cluster_ids and (_show_portal_ids[0] or _show_debug[0]) and PyImGui.begin_tooltip():
            PyImGui.text("Portal IDs")
            row_h = 18
            list_h = min(200, row_h * len(hovered_cluster_ids) + 8)
            if PyImGui.begin_child(
                "##wm_plus_portal_hover_listbox",
                (260, list_h),
                True,
                PyImGui.WindowFlags.NoScrollbar,
            ):
                for gid in hovered_cluster_ids:
                    linked = _PORTAL_LINKS.get(gid)
                    if linked:
                        km = _GLOBAL_ID_TO_PORTAL.get(linked)
                        dest_map = km[0] if km else linked // 1000
                        dest_name = _map_name_cached(dest_map)
                        label = f"{gid}  \u2192  {linked}  ({dest_name})"
                        PyImGui.text_colored(label, (0.4, 0.95, 0.5, 1.0))
                    else:
                        km_self = _GLOBAL_ID_TO_PORTAL.get(gid)
                        self_map = km_self[0] if km_self else gid // 1000
                        self_name = _map_name_cached(self_map)
                        PyImGui.text_colored(
                            f"{gid}  ({self_name})  — unlinked",
                            (0.65, 0.65, 0.65, 1.0),
                        )
                PyImGui.end_child()
            PyImGui.end_tooltip()

        # Draw link lines between paired portals
        if _PORTAL_LINKS:
            drawn_pairs: set[tuple[int, int]] = set()
            for a_id, b_id in _PORTAL_LINKS.items():
                pair = (min(a_id, b_id), max(a_id, b_id))
                if pair in drawn_pairs:
                    continue
                drawn_pairs.add(pair)
                # Ensure both portals are loaded even if not currently visible
                for pid in (a_id, b_id):
                    mid, lidx = _GLOBAL_ID_TO_PORTAL.get(pid, (0, 0))
                    if mid and mid not in _PORTAL_BUILT:
                        bnd = _ICON_BOUNDS.get(mid)
                        if bnd:
                            _ensure_portal_dots(mid, is_live=(mid == current_map))
                            # cache screen pos
                            for pix2, piy2, _, _, gid2, *_gc2 in _PORTAL_ICON_POS.get(mid, []):
                                if gid2 and gid2 not in visible_portal_sx:
                                    sx2, sy2 = _i2s(pix2, piy2)
                                    visible_portal_sx[gid2] = (sx2, sy2)
                pa = visible_portal_sx.get(a_id)
                pb = visible_portal_sx.get(b_id)
                if pa and pb:
                    PyImGui.draw_list_add_line(pa[0], pa[1], pb[0], pb[1], link_color, 1.5)

    # ── Custom dungeon travel buttons: one green button per entrance portal ───
    # These appear regardless of _show_portals / Developer mode, because the
    # entrance portals are part of normal (non-developer) visible maps.
    for dungeon_mid in _CUSTOM_DUNGEON_MAP_IDS:
        if dungeon_mid in _travel_btn_seen:
            continue
        dungeon_portal_gid = dungeon_mid * 1000
        entrance_gid = _PORTAL_LINKS.get(dungeon_portal_gid)
        if not entrance_gid:
            continue
        # Find screen position of the entrance portal dot
        epos = visible_portal_sx.get(entrance_gid)
        if epos is None:
            # Try to resolve via icon pos even if not in visible_portal_sx
            emap = entrance_gid // 1000
            _ensure_portal_dots(emap, is_live=(emap == current_map))
            for dot in _PORTAL_ICON_POS.get(emap, []):
                if len(dot) >= 5 and int(dot[4]) == entrance_gid:
                    epos = _i2s(float(dot[0]), float(dot[1]))
                    break
        if epos is None:
            continue
        # Place button 8px below the portal dot, horizontally centered on it
        bx = epos[0] - 8.0
        by = epos[1] + 6.0
        _travel_btn_seen.add(dungeon_mid)
        _travel_btn_data.append((dungeon_mid, bx, by))
        # Draw dungeon name label to the right of the button (same style as regular map labels)
        d_meta   = _MAP_META.get(dungeon_mid)
        d_name   = d_meta[1] if d_meta else f"Map {dungeon_mid}"
        raw_lbl  = f"{d_name} [{dungeon_mid}]"
        lbl_col  = Utils.RGBToColor(255, 255, 255, 220)
        PyImGui.draw_list_add_text(bx + 36.0, by, lbl_col, raw_lbl)

    # ── Pass 4: draw computed portal path (always, regardless of _show_portals) ─
    if _path_gids:
        path_done_col  = Utils.RGBToColor( 80,  80,  80, 100)  # dimmed for traveled
        path_dot_col   = Utils.RGBToColor(255, 255, 255, 240)
        path_dot_rim   = Utils.RGBToColor( 30, 150, 200, 255)
        path_done_rim  = Utils.RGBToColor( 80,  80,  80, 120)

        first_pending = _path_first_pending_idx()

        # Collect icon-space positions for every GID in the path
        path_icon: dict[int, tuple[float, float]] = {}
        for pgid in _path_gids:
            km = _GLOBAL_ID_TO_PORTAL.get(pgid)
            if km is None:
                continue
            mid, lidx = km
            if mid not in _PORTAL_BUILT:
                bnd2 = _ICON_BOUNDS.get(mid)
                if bnd2:
                    _ensure_portal_dots(mid, is_live=(mid == current_map))
            for pt in _PORTAL_ICON_POS.get(mid, []):
                if pt[3] == lidx:
                    path_icon[pgid] = (pt[0], pt[1])
                    break

        # Draw dots at each portal position
        for dot_idx, pgid in enumerate(_path_gids):
            pa_ix = path_icon.get(pgid)
            if pa_ix is None:
                continue
            px, py = _i2s(pa_ix[0], pa_ix[1])
            if dot_idx < first_pending:
                PyImGui.draw_list_add_circle_filled(px, py, 5.0, path_done_col, 12)
                PyImGui.draw_list_add_circle(px, py, 5.0, path_done_rim, 12, 1.0)
            else:
                PyImGui.draw_list_add_circle_filled(px, py, 7.0, path_dot_col, 12)
                PyImGui.draw_list_add_circle(px, py, 7.0, path_dot_rim, 12, 1.5)

    # ── Pass 5: draw MoveToNextWaypoint local AutoPathing path (always) ──────
    if _mtnw_path:
        mtnw_icon = _mtnw_path_icon_points(current_map)
        if len(mtnw_icon) >= 2:
            mtnw_line_col = Utils.RGBToColor(255, 110, 255, 230)
            mtnw_dot_col  = Utils.RGBToColor(255, 220, 255, 235)
            mtnw_cur_col  = Utils.RGBToColor(255, 255, 120, 255)

            # Start from current path index (skip already-reached waypoints)
            start_idx = max(0, min(_mtnw_path_index[0], len(mtnw_icon) - 1))

            # Polyline (only future waypoints)
            for i in range(start_idx, len(mtnw_icon) - 1):
                a = _i2s(mtnw_icon[i][0], mtnw_icon[i][1])
                b = _i2s(mtnw_icon[i + 1][0], mtnw_icon[i + 1][1])
                PyImGui.draw_list_add_line(a[0], a[1], b[0], b[1], mtnw_line_col, 2.0)

            # Sparse waypoint dots (only future waypoints, can be hidden)
            if _show_mtnw_waypoint_dots[0]:
                step = 3 if len(mtnw_icon) > 30 else 1
                for i in range(start_idx, len(mtnw_icon), step):
                    s = _i2s(mtnw_icon[i][0], mtnw_icon[i][1])
                    PyImGui.draw_list_add_circle_filled(s[0], s[1], 3.2, mtnw_dot_col, 10)

            # Highlight current target waypoint
            if 0 <= _mtnw_path_index[0] < len(mtnw_icon):
                c = _i2s(mtnw_icon[_mtnw_path_index[0]][0], mtnw_icon[_mtnw_path_index[0]][1])
                PyImGui.draw_list_add_circle(c[0], c[1], 7.0, mtnw_cur_col, 16, 1.8)

    # ── Route overlay: GetPath result drawn on the world map ─────────────────
    if _wp_route_overlay and _show_wp_demo[0]:
        _draw_route_segments(_wp_route_overlay, _i2s)

    # ── Travel button route overlay (always visible) ─────────────────────────
    if _travel_route_overlay:
        _draw_route_segments(_travel_route_overlay, _i2s, draw_link=False)

    # ── Player position cross ─────────────────────────────────────────────────
    if _show_player_cross[0] and _show_developer[0]:
        icon_pos = _get_player_icon_pos(current_map)
        if icon_pos is not None:
            sx, sy = _i2s(icon_pos[0], icon_pos[1])
            cross_col  = Utils.RGBToColor(255, 60, 60, 255)
            shadow_col = Utils.RGBToColor(0, 0, 0, 180)
            arm  = 9.0
            thick = 2.0
            # Shadow for readability
            PyImGui.draw_list_add_line(sx - arm, sy,       sx + arm, sy,       shadow_col, thick + 2.0)
            PyImGui.draw_list_add_line(sx,       sy - arm, sx,       sy + arm, shadow_col, thick + 2.0)
            # Cross
            PyImGui.draw_list_add_line(sx - arm, sy,       sx + arm, sy,       cross_col, thick)
            PyImGui.draw_list_add_line(sx,       sy - arm, sx,       sy + arm, cross_col, thick)
            # Center dot
            PyImGui.draw_list_add_circle_filled(sx, sy, 3.0, cross_col, 8)

    PyImGui.end()


# ── Pathfinder panel (right side) ─────────────────────────────────────────────

def _draw_route_segments(overlay: list[dict], i2s, draw_link: bool = True) -> None:
    """Draw portal-to-portal route lines and dots from a _build_route_overlay result."""
    col_exit  = Utils.RGBToColor(255, 200,  50, 240)
    col_enter = Utils.RGBToColor( 60, 220, 255, 240)
    col_link  = Utils.RGBToColor(255, 200,  50, 140)
    col_trav  = Utils.RGBToColor(120, 200, 255, 160)
    col_dst   = Utils.RGBToColor( 80, 255, 120, 255)

    current_map = Map.GetMapID()
    segments: list[tuple] = []
    for seg in overlay:
        from_map = int(seg.get("from_map", 0) or 0)
        ex = (i2s(seg["exit_ix"],  seg["exit_iy"])  if seg["exit_ix"]  is not None else None)
        en = (i2s(seg["enter_ix"], seg["enter_iy"]) if seg["enter_ix"] is not None else None)
        ipath = seg.get("path_ixy", [])
        spath = [i2s(p[0], p[1]) for p in ipath if isinstance(p, (list, tuple)) and len(p) >= 2]
        segments.append((from_map, ex, en, spath))

    prev_ex: tuple | None = None
    for from_map, ex, en, spath in segments:
        if draw_link and prev_ex is not None and en is not None:
            PyImGui.draw_list_add_line(prev_ex[0], prev_ex[1], en[0], en[1], col_link, 1.5)
        if from_map != current_map and len(spath) >= 2:
            for j in range(len(spath) - 1):
                a = spath[j]
                b = spath[j + 1]
                PyImGui.draw_list_add_line(a[0], a[1], b[0], b[1], col_trav, 2.0)
        prev_ex = ex

    for i, (_from_map, ex, en, _spath) in enumerate(segments):
        is_last = (i == len(segments) - 1)
        if ex is not None:
            PyImGui.draw_list_add_circle_filled(ex[0], ex[1], 5.5, col_exit, 12)
            PyImGui.draw_list_add_circle(ex[0], ex[1], 5.5, Utils.RGBToColor(255, 255, 180, 255), 12, 1.2)
        if en is not None:
            dot_col  = col_dst if is_last else col_enter
            dot_size = 6.5    if is_last else 5.0
            PyImGui.draw_list_add_circle_filled(en[0], en[1], dot_size, dot_col, 12)
            PyImGui.draw_list_add_circle(en[0], en[1], dot_size, Utils.RGBToColor(200, 255, 220, 255), 12, 1.2)


def _draw_travel_buttons() -> None:
    """Draw small per-map Travel buttons on the world map overlay.

    Uses one tiny ImGui window per button so mouse input is not blocked
    across the entire world map area (unlike a full-screen overlay).
    """
    if not Map.WorldMap.IsWindowOpen() or not _travel_btn_data:
        return

    # Hide all drawings when zoom is not 1.0 (100%)
    if not _zoom_is_default():
        return

    current_map = Map.GetMapID()
    if current_map <= 0:
        return

    btn_w, btn_h = 16.0, 13.0
    btn_flags = (
        PyImGui.WindowFlags.NoTitleBar        |
        PyImGui.WindowFlags.NoResize          |
        PyImGui.WindowFlags.NoMove            |
        PyImGui.WindowFlags.NoScrollbar       |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.NoCollapse        |
        PyImGui.WindowFlags.NoBackground      |
        PyImGui.WindowFlags.NoSavedSettings
    )
    # Direct path colors (green)
    btn_col         = (0.10, 0.55, 0.15, 0.88)
    btn_col_hovered = (0.15, 0.75, 0.22, 0.95)
    btn_col_active  = (0.20, 0.90, 0.28, 1.00)
    # Fast-travel-only colors (blue)
    btn_col_ft         = (0.10, 0.35, 0.75, 0.88)
    btn_col_ft_hovered = (0.15, 0.50, 0.90, 0.95)
    btn_col_ft_active  = (0.20, 0.60, 1.00, 1.00)

    for rep_id, btn_x, btn_y in _travel_btn_data:
        # Check direct path from current map
        if rep_id not in _is_path_cache:
            _is_path_cache[rep_id] = IsPath(current_map, rep_id)
        direct = _is_path_cache[rep_id]

        # Check fast-travel path: nearest unlocked outpost → target
        # For custom dungeon maps you cannot fast-travel there directly, but
        # GetNearestUnlockedOutpost finds the nearest outpost from which you *can*
        # walk to the dungeon — the coroutine will FT there first, then walk.
        if not direct and rep_id not in _is_ft_path_cache:
            ft = GetNearestUnlockedOutpost(rep_id, current_map)
            if ft and ft["map_id"] != current_map:
                _is_ft_path_cache[rep_id] = True
            else:
                _is_ft_path_cache[rep_id] = False
        via_ft = not direct and _is_ft_path_cache.get(rep_id, False)

        if not direct and not via_ft:
            continue

        plus_w = (btn_h + 2.0) if direct else 0.0
        PyImGui.set_next_window_pos(btn_x, btn_y)
        PyImGui.set_next_window_size(btn_w + 2.0 + plus_w, btn_h + 2.0)
        if not PyImGui.begin(f"##wm_travel_{rep_id}", btn_flags):
            PyImGui.end()
            continue

        if via_ft:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        btn_col_ft)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, btn_col_ft_hovered)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  btn_col_ft_active)
        else:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        btn_col)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, btn_col_hovered)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  btn_col_active)
        PyImGui.set_cursor_pos(0.0, 0.0)
        if PyImGui.button(f"##t{rep_id}", btn_w, btn_h):
            GLOBAL_CACHE.Coroutines.append(_travel_button_coroutine(rep_id))
        travel_btn_hovered = PyImGui.is_item_hovered()
        PyImGui.pop_style_color(3)

        if direct:
            queued = rep_id in _travel_queue
            PyImGui.same_line(0.0, 2.0)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        (0.08, 0.42, 0.12, 0.90))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.12, 0.58, 0.18, 0.98))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (0.18, 0.72, 0.24, 1.00))
            if queued:
                PyImGui.begin_disabled(True)
            if PyImGui.button(f"+##q{rep_id}", btn_h, btn_h):
                _enqueue_travel_target(rep_id)
            if queued:
                PyImGui.end_disabled()
            if PyImGui.is_item_hovered():
                PyImGui.begin_tooltip()
                if queued:
                    PyImGui.text("Already queued")
                else:
                    PyImGui.text("Queue this travel")
                PyImGui.end_tooltip()
            PyImGui.pop_style_color(3)

        if travel_btn_hovered:
            meta = _MAP_META.get(rep_id)
            name = meta[1] if meta else f"Map {rep_id}"
            PyImGui.begin_tooltip()
            PyImGui.text(f"Travel to: {name}")
            if direct:
                # Green button: direct portal path exists → walking only, no FT needed
                dist = _path_distance(current_map, rep_id)
                if dist is not None:
                    PyImGui.text(f"Distance: {dist:,.0f} units")
                else:
                    PyImGui.text("Distance: unknown")
            else:
                # Blue button: no direct path → show FT outpost info
                ft_info = GetNearestUnlockedOutpost(rep_id, current_map)
                ft_id_tip = ft_info["map_id"] if ft_info else None
                ft_name   = ft_info["name"]   if ft_info else "?"
                ft_dist   = ft_info["distance"] if ft_info else None
                if ft_id_tip == rep_id:
                    # Target itself is an unlocked outpost → direct fast-travel
                    PyImGui.text("(direct fast-travel)")
                elif ft_id_tip and ft_id_tip != current_map:
                    # Need to fast-travel to an intermediate outpost first
                    PyImGui.text(f"via fast-travel: {ft_name}")
                    if ft_dist is not None:
                        PyImGui.text(f"Distance: {ft_dist:,.0f} units")
                    else:
                        PyImGui.text("Distance: unknown")
                else:
                    dist = _path_distance(current_map, rep_id)
                    if dist is not None:
                        PyImGui.text(f"Distance: {dist:,.0f} units")
                    else:
                        PyImGui.text("Distance: unknown")
            PyImGui.end_tooltip()

        PyImGui.end()


def _draw_travel_roadmap() -> None:
    """Right-side panel showing the active inter-map travel route as a roadmap."""
    map_open = Map.WorldMap.IsWindowOpen()

    # Keep map-overlay behavior when world map is open.
    if map_open and not _zoom_is_default():
        return

    # Show when a route is active/present or queued travel targets exist.
    if not _path_map_names and not _mtm_runner_active[0] and not _mtnw_runner_active[0] and not _travel_queue:
        _pathfinder_win_h[0] = 0.0
        return

    win_w  = 210.0
    margin = 8.0

    if map_open:
        fi = Map.WorldMap.GetFrameInfo()
        if fi is None:
            return
        sc = fi.GetContentCoords()
        if not sc:
            return
        sr, st = float(sc[2]), float(sc[1])
        pos_x = sr - win_w - margin
        pos_y = st + margin
    else:
        io = PyImGui.get_io()
        sr = float(io.display_size_x)
        pos_x = sr - win_w - margin
        pos_y = margin

    panel_flags = _get_panel_flags()
    PyImGui.set_next_window_pos(pos_x, pos_y)
    PyImGui.set_next_window_size(win_w, 0.0)
    if not PyImGui.begin("##wm_travel_roadmap", panel_flags):
        PyImGui.end()
        return

    title_col  = Utils.RGBToColor( 80, 220, 120, 255)
    cur_col    = Utils.RGBToColor(255, 230,  80, 255)
    done_col   = Utils.RGBToColor(110, 110, 110, 200)
    pend_col   = Utils.RGBToColor(210, 210, 210, 255)
    dst_col    = Utils.RGBToColor( 60, 220, 255, 255)
    arrow_col  = Utils.RGBToColor(160, 160, 160, 200)

    tx, ty = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 16)
    status = "Running..." if _mtm_runner_active[0] or _mtnw_runner_active[0] else "Route ready"
    PyImGui.draw_list_add_text(tx, ty, title_col, f"Active Route  [{status}]")
    PyImGui.separator()

    current_map = Map.GetMapID()
    names = _path_map_names

    # Determine how many hops are already done
    done_count = 0
    route = _mtm_route[0]
    if route and route.get("found"):
        waypoints = route.get("waypoints", [])
        for hop_idx, wp in enumerate(waypoints):
            if int(wp.get("from_map", 0)) == current_map:
                done_count = hop_idx
                break
        else:
            done_count = len(waypoints)  # all done / at destination

    now_ms = int(Utils.GetBaseTimestamp())

    # Detect hop transitions and record start/end timestamps
    if _travel_prev_done_count[0] != done_count:
        prev = _travel_prev_done_count[0] if _travel_prev_done_count[0] >= 0 else 0
        for _hi in range(prev, done_count):
            if _hi < len(_travel_hop_times) and _travel_hop_times[_hi][1] == 0:
                _travel_hop_times[_hi] = (_travel_hop_times[_hi][0], now_ms)
        if done_count < len(_travel_hop_times) and _travel_hop_times[done_count][0] == 0:
            _travel_hop_times[done_count] = (now_ms, 0)
        _travel_prev_done_count[0] = done_count

    for i, step in enumerate(names):
        sx2, sy2 = PyImGui.get_cursor_screen_pos()
        PyImGui.dummy(int(win_w - 8), 14)
        is_last = (i == len(names) - 1)
        prefix = "" if i == 0 else "-> "

        # Show elapsed time for the hop that departs from names[i] (hop index = i).
        # hop_idx is absolute (offset-corrected) to index into _travel_hop_times.
        time_str = ""
        hop_idx = i + _path_name_offset[0]
        if 0 <= hop_idx < len(_travel_hop_times):
            ht_s, ht_e = _travel_hop_times[hop_idx]
            if ht_e != 0:
                elapsed = int((ht_e - ht_s) / 1000.0)
                _hm, _hs = divmod(elapsed, 60)
                time_str = f"  ({_hm}m {_hs:02d}s)" if _hm > 0 else f"  ({_hs}s)"
            elif ht_s > 0:
                elapsed = int((now_ms - ht_s) / 1000.0)
                _hm, _hs = divmod(elapsed, 60)
                time_str = f"  ({_hm}m {_hs:02d}s...)" if _hm > 0 else f"  ({_hs}s...)"

        label = f"{prefix}{step}{time_str}"
        if hop_idx == done_count:
            col = cur_col
        elif hop_idx < done_count:
            col = done_col
        elif is_last:
            col = dst_col
        else:
            col = pend_col
        PyImGui.draw_list_add_text(sx2, sy2, col, label)

    if _travel_queue:
        PyImGui.spacing()
        PyImGui.separator()
        q_title_col = Utils.RGBToColor(120, 220, 255, 255)
        q_head_col  = Utils.RGBToColor(220, 220, 220, 255)
        q_wait_col  = Utils.RGBToColor(170, 170, 170, 220)
        q_run_col   = Utils.RGBToColor(120, 255, 160, 255)
        qx, qy = PyImGui.get_cursor_screen_pos()
        PyImGui.dummy(int(win_w - 8), 14)
        PyImGui.draw_list_add_text(qx, qy, q_title_col, f"Queue ({len(_travel_queue)})")

        for qi, qmid in enumerate(_travel_queue):
            qname = (_MAP_META.get(qmid) or (None, f"Map {qmid}"))[1]
            row_x, row_y = PyImGui.get_cursor_screen_pos()
            PyImGui.dummy(int(win_w - 8), 14)
            is_head = (qi == 0)
            is_running = is_head and (_travel_queue_inflight_target[0] == qmid)
            if is_running:
                qcol = q_run_col
                prefix = "> "
                suffix = " (starting...)"
            elif is_head:
                qcol = q_head_col
                prefix = "> "
                suffix = ""
            else:
                qcol = q_wait_col
                prefix = "  "
                suffix = ""
            PyImGui.draw_list_add_text(row_x, row_y, qcol, f"{prefix}{qname} [{qmid}]{suffix}")

    # Total elapsed time since route start
    if _travel_route_start_ms[0] > 0:
        total_s = int((now_ms - _travel_route_start_ms[0]) / 1000.0)
        _mins, _secs = divmod(total_s, 60)
        total_str = f"Total: {_mins}m {_secs:02d}s" if _mins > 0 else f"Total: {_secs}s"
        tx3, ty3 = PyImGui.get_cursor_screen_pos()
        PyImGui.dummy(int(win_w - 8), 14)
        PyImGui.draw_list_add_text(tx3, ty3, Utils.RGBToColor(150, 150, 150, 200), total_str)

    PyImGui.spacing()
    PyImGui.separator()
    btn_w_full = win_w - 16.0
    stop_active = _mtm_runner_active[0] or _mtnw_runner_active[0]
    stop_col    = (0.8, 0.15, 0.15, 1.0) if stop_active else (0.4, 0.4, 0.4, 1.0)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        stop_col)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (min(stop_col[0]+0.15,1.0), stop_col[1], stop_col[2], 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (min(stop_col[0]+0.25,1.0), stop_col[1], stop_col[2], 1.0))
    if PyImGui.button("Stop Travel##rm", btn_w_full, 0):
        _abort_worldmap_movement()
        _auto_explore_active[0] = False
        _auto_explore_target[0] = 0
        _travel_route_overlay.clear()
        _path_gids.clear()
        _path_map_names.clear()
        _travel_route_start_ms[0] = 0
        _travel_hop_times.clear()
        _travel_prev_done_count[0] = -1
    PyImGui.pop_style_color(3)

    if _travel_queue:
        clear_col = (0.55, 0.20, 0.20, 0.90)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        clear_col)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.72, 0.25, 0.25, 1.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (0.80, 0.30, 0.30, 1.0))
        if PyImGui.button("Clear Queue##rm", btn_w_full, 0):
            _travel_queue.clear()
            _travel_queue_inflight_target[0] = 0
            _travel_queue_dispatch_ms[0] = 0
        PyImGui.pop_style_color(3)

    _pathfinder_win_h[0] = PyImGui.get_window_height()
    PyImGui.end()


# ── WorldPathing API demo panel ───────────────────────────────────────────────

def _draw_worldpathing_demo() -> None:
    """Right-side panel for live testing of IsPath / GetPath / MoveToNextWaypoint."""
    if not _show_developer[0]:
        return
    if not _show_wp_demo[0]:
        return
    if not Map.WorldMap.IsWindowOpen():
        return

    # Hide all drawings when zoom is not 1.0 (100%)
    if not _zoom_is_default():
        return

    fi = Map.WorldMap.GetFrameInfo()
    if fi is None:
        return
    sc = fi.GetContentCoords()
    if not sc:
        return
    sr, st = float(sc[2]), float(sc[1])

    win_w  = 230.0
    margin = 8.0
    gap    = 6.0
    pos_y  = st + margin + _pathfinder_win_h[0] + gap

    panel_flags = (
        PyImGui.WindowFlags.NoTitleBar        |
        PyImGui.WindowFlags.NoResize          |
        PyImGui.WindowFlags.NoMove            |
        PyImGui.WindowFlags.NoCollapse        |
        PyImGui.WindowFlags.AlwaysAutoResize  |
        PyImGui.WindowFlags.NoSavedSettings
    )
    PyImGui.set_next_window_pos(sr - win_w - margin, pos_y)
    PyImGui.set_next_window_size(win_w, 0.0)
    if not PyImGui.begin("##wm_wp_demo", panel_flags):
        PyImGui.end()
        return

    title_col   = Utils.RGBToColor(130, 230, 255, 255)
    ok_col      = Utils.RGBToColor( 80, 230,  80, 255)
    fail_col    = Utils.RGBToColor(255,  80,  80, 255)
    neutral_col = Utils.RGBToColor(200, 200, 200, 255)
    head_col    = Utils.RGBToColor(255, 220, 100, 255)

    # ── Title ─────────────────────────────────────────────────────────────
    tx, ty = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 16)
    PyImGui.draw_list_add_text(tx, ty, title_col, "WorldPathing  API  Demo")
    PyImGui.separator()

    # ── Shared inputs ─────────────────────────────────────────────────────
    # Start map is always the current map – no manual input needed
    _wp_demo_start[0] = Map.GetMapID()
    smeta = _MAP_META.get(_wp_demo_start[0])
    start_name = smeta[1] if smeta else f"Map {_wp_demo_start[0]}"
    PyImGui.text_colored(f"From: [{_wp_demo_start[0]}] {start_name}", (1.0, 0.9, 0.3, 1.0))

    PyImGui.push_item_width(win_w - 16.0)
    _wp_demo_target[0] = PyImGui.input_int("Target map##wpd_t", _wp_demo_target[0])
    PyImGui.pop_item_width()

    tmeta = _MAP_META.get(_wp_demo_target[0])
    if tmeta:
        PyImGui.text(f"  To:   {tmeta[1]}")

    # ── IsPath ────────────────────────────────────────────────────────────
    PyImGui.separator()
    hx, hy = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 14)
    PyImGui.draw_list_add_text(hx, hy, head_col, "IsPath")

    half = (win_w - 20.0) * 0.5
    if PyImGui.button("Check##wpd_ip", half, 0):
        if _wp_demo_start[0] > 0 and _wp_demo_target[0] > 0:
            _wp_is_path_result[0] = IsPath(_wp_demo_start[0], _wp_demo_target[0])
        else:
            _wp_is_path_result[0] = None
    PyImGui.same_line(0.0, 4.0)
    if _wp_is_path_result[0] is None:
        PyImGui.text_colored("(not checked)", (0.5, 0.5, 0.5, 1.0))
    elif _wp_is_path_result[0]:
        PyImGui.text_colored("True  — path exists", (0.3, 0.9, 0.3, 1.0))
    else:
        PyImGui.text_colored("False — no path", (0.9, 0.3, 0.3, 1.0))

    # ── GetPath ───────────────────────────────────────────────────────────
    PyImGui.separator()
    hx2, hy2 = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 14)
    PyImGui.draw_list_add_text(hx2, hy2, head_col, "GetPath")

    if PyImGui.button("Get Path##wpd_gp", half, 0):
        if _wp_demo_start[0] > 0 and _wp_demo_target[0] > 0:
            result = GetPath(_wp_demo_start[0], _wp_demo_target[0])
            _wp_get_path_found[0]  = result["found"]
            _wp_get_path_maps[:]   = result["map_names"]
            _wp_get_path_result[:] = result["waypoints"]
            _wp_get_path_full[0]   = result
            _wp_move_result[0]     = None   # reset move status on new path
            _wp_move_map_result[0] = None
            _wp_route_overlay[:]   = _build_route_overlay(result)
        else:
            _wp_get_path_found[0]  = False
            _wp_get_path_maps.clear()
            _wp_get_path_result.clear()
            _wp_get_path_full[0]   = None
            _wp_move_map_result[0] = None
            _wp_route_overlay.clear()

    if _wp_get_path_maps:
        if _wp_get_path_found[0]:
            PyImGui.text_colored(
                f"{len(_wp_get_path_result)} hop(s)",
                (0.3, 0.9, 0.3, 1.0))
        else:
            PyImGui.text_colored("No path found", (0.9, 0.3, 0.3, 1.0))

        for i, mname in enumerate(_wp_get_path_maps):
            if i == 0:
                lbl = mname
                col = (1.0, 0.9, 0.3, 1.0)
            elif i == len(_wp_get_path_maps) - 1:
                lbl = mname
                col = (0.4, 0.85, 1.0, 1.0)
            else:
                lbl = f"  \u2192 {mname}"
                col = (0.85, 0.85, 0.85, 1.0)
            PyImGui.text_colored(lbl, col)

            # Show exit portal coords + link IDs for this hop
            if i < len(_wp_get_path_result):
                wp = _wp_get_path_result[i]
                gx, gy = wp["game_x"], wp["game_y"]
                eg, ig   = wp["exit_gid"], wp["enter_gid"]
                coord_str = f" ({gx:.0f}, {gy:.0f})" if gx is not None else ""
                PyImGui.text_colored(
                    f"     exit:{eg}  \u2192  enter:{ig}{coord_str}",
                    (0.65, 0.65, 0.65, 1.0))

    # ── MoveToNextWaypoint ────────────────────────────────────────────────
    PyImGui.separator()
    hx3, hy3 = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 14)
    PyImGui.draw_list_add_text(hx3, hy3, head_col, "MoveToNextWaypoint")

    path_ready = _wp_get_path_full[0] is not None and _wp_get_path_found[0]
    if PyImGui.button("Move!##wpd_mv", half, 0):
        if not path_ready:
            _wp_move_result[0] = False
        elif _wp_demo_target[0] > 0:
            _wp_move_result[0] = MoveToNextWaypoint(_wp_demo_target[0], _wp_get_path_full[0])
        else:
            _wp_move_result[0] = None
    PyImGui.same_line(0.0, 4.0)
    if not path_ready:
        PyImGui.text_colored("→ Build path first", (0.9, 0.6, 0.2, 1.0))
    elif _wp_move_result[0] is None:
        PyImGui.text_colored("(not used)", (0.5, 0.5, 0.5, 1.0))
    elif _wp_move_result[0]:
        PyImGui.text_colored("Move issued!", (0.3, 0.9, 0.3, 1.0))
    else:
        PyImGui.text_colored("No move (no coords)", (0.9, 0.3, 0.3, 1.0))

    # ── MoveToMapid ──────────────────────────────────────────────────────
    PyImGui.separator()
    hx4, hy4 = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 14)
    PyImGui.draw_list_add_text(hx4, hy4, head_col, "MoveToMapid")

    btn_w = (win_w - 24.0) * 0.5
    if PyImGui.button("Move Full Route##wpd_mtm", btn_w, 0):
        if _wp_demo_target[0] > 0:
            _wp_move_map_result[0] = MoveToMapid(_wp_demo_target[0])
        else:
            _wp_move_map_result[0] = None
    PyImGui.same_line(0.0, 4.0)
    stop_col = (0.8, 0.15, 0.15, 1.0) if _mtm_runner_active[0] or _mtnw_runner_active[0] else (0.4, 0.4, 0.4, 1.0)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        stop_col)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (min(stop_col[0] + 0.15, 1.0), stop_col[1], stop_col[2], 1.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (min(stop_col[0] + 0.25, 1.0), stop_col[1], stop_col[2], 1.0))
    if PyImGui.button("Stop##wpd_mtm_stop", btn_w, 0):
        _abort_worldmap_movement()
        _wp_move_map_result[0] = False
        _travel_route_overlay.clear()
        _path_gids.clear()
        _path_map_names.clear()
        _travel_route_start_ms[0] = 0
        _travel_hop_times.clear()
        _travel_prev_done_count[0] = -1
    PyImGui.pop_style_color(3)
    if _wp_move_map_result[0] is None:
        PyImGui.text_colored("(not used)", (0.5, 0.5, 0.5, 1.0))
    elif _wp_move_map_result[0]:
        active_txt = "Running..." if _mtm_runner_active[0] or _mtnw_runner_active[0] else "Route started!"
        PyImGui.text_colored(active_txt, (0.3, 0.9, 0.3, 1.0))
    else:
        PyImGui.text_colored("Stopped / no route", (0.9, 0.3, 0.3, 1.0))

    PyImGui.end()


# ── Combined legend + settings panel ──────────────────────────────────────────

def _draw_legend() -> None:
    """Fixed panel at the left edge of the world map containing legend and settings."""
    if not Map.WorldMap.IsWindowOpen():
        return

    # Hide all drawings when zoom is not 1.0 (100%)
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
        ("Walkable area",       Utils.RGBToColor(180, 255, 180, 200), Utils.RGBToColor(120, 210, 120, 255)),
        ("Linked Portal",       Utils.RGBToColor( 60, 210,  60, 230), Utils.RGBToColor(180, 255, 180, 255)),
        ("Unlinked Portal",     Utils.RGBToColor(255,  80,  80, 230), Utils.RGBToColor(255, 200, 200, 255)),
    ]

    panel_flags = _get_panel_flags()
    PyImGui.set_next_window_pos(sl + margin, st + margin)
    PyImGui.set_next_window_size(win_w, 0.0)   # width fixed, height auto
    if not PyImGui.begin("##wm_plus_panel", panel_flags):
        PyImGui.end()
        return

    # ── Title ──────────────────────────────────────────────────────────────
    title_col = Utils.RGBToColor(255, 230, 140, 255)
    tx, ty = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 16)
    PyImGui.draw_list_add_text(tx, ty, title_col, "WorldMap+  Legend")

    # ── Legend swatches ────────────────────────────────────────────────────
    text_col = Utils.RGBToColor(230, 230, 230, 255)
    for label, fill_col, border_col in legend_entries:
        sx, sy = PyImGui.get_cursor_screen_pos()
        PyImGui.dummy(int(win_w), int(row_h))

        bx = sx
        by = sy + (row_h - box_size) * 0.5
        if label == "Portal connection":
            line_y = by + box_size * 0.5
            PyImGui.draw_list_add_line(bx, line_y, bx + box_size, line_y, fill_col, 2.0)
        elif label == "Walkable area":
            PyImGui.draw_list_add_quad_filled(
                bx,            by,
                bx + box_size, by,
                bx + box_size, by + box_size,
                bx,            by + box_size,
                fill_col)
            PyImGui.draw_list_add_quad(
                bx,            by,
                bx + box_size, by,
                bx + box_size, by + box_size,
                bx,            by + box_size,
                border_col, 1.0)
        elif label in ("Linked Portal", "Unlinked Portal"):
            cx_dot = bx + box_size * 0.5
            cy_dot = by + box_size * 0.5
            PyImGui.draw_list_add_circle_filled(cx_dot, cy_dot, 5.0, fill_col, 10)
            PyImGui.draw_list_add_circle(cx_dot, cy_dot, 5.0, border_col, 10, 1.0)
        else:
            PyImGui.draw_list_add_rect(bx, by, bx + box_size, by + box_size, border_col, 2.0, 0, 1.5)
        PyImGui.draw_list_add_text(bx + box_size + 5.0, sy + (row_h - 13.0) * 0.5, text_col, label)

    # ── Settings ───────────────────────────────────────────────────────────
    PyImGui.separator()
    PyImGui.push_item_width(win_w - 16.0)
    _new_frames      = PyImGui.checkbox("Draw all Frames##wmp",          _show_frames[0])
    _new_opacity     = PyImGui.slider_float("Opacity##wmp",              _opacity[0], 0.1, 1.0)
    _new_reachable   = PyImGui.checkbox(
        "  Reachable (not visited)##wmp", _show_reachable_unvisited[0])
    _new_hero_loadout = PyImGui.checkbox("  Setup Team##wmp", _show_hero_loadout[0])
    if (_new_frames != _show_frames[0] or
            _new_opacity != _opacity[0] or
            _new_reachable != _show_reachable_unvisited[0] or
            _new_hero_loadout != _show_hero_loadout[0]):
        _show_frames[0]              = _new_frames
        _opacity[0]                  = _new_opacity
        _show_reachable_unvisited[0] = _new_reachable
        _show_hero_loadout[0]        = _new_hero_loadout
        _wmp_ini_save()
    PyImGui.pop_item_width()

    PyImGui.separator()
    _show_developer[0] = PyImGui.checkbox("Developer##wmp", _show_developer[0])
    if _show_developer[0]:
        PyImGui.push_item_width(win_w - 16.0)
        _show_portals[0]     = PyImGui.checkbox("  Draw Portals##wmp",    _show_portals[0])
        if _show_portals[0]:
            _show_portals_3d[0] = PyImGui.checkbox("    Draw 3D Portals##wmp", _show_portals_3d[0])
            _show_portal_ids[0] = PyImGui.checkbox("    Show Portal IDs##wmp",  _show_portal_ids[0])
        _show_pmap_current[0] = PyImGui.checkbox("  Navmap Current Map##wmp", _show_pmap_current[0])
        _show_pmap_all[0]     = PyImGui.checkbox("  Navmap All##wmp",         _show_pmap_all[0])
        if _show_pmap_current[0] or _show_pmap_all[0]:
            _pmap_opacity[0] = PyImGui.slider_float("  Navmap opacity##wmp", _pmap_opacity[0], 0.01, 1.0)
        _show_player_cross[0] = PyImGui.checkbox("  Player position##wmp", _show_player_cross[0])
        _show_wp_demo[0] = PyImGui.checkbox("  WorldPathing Demo##wmp", _show_wp_demo[0])
        _show_debug[0] = PyImGui.checkbox("  Portal Editor##wmp", _show_debug[0])
        if _show_debug[0]:
            _draw_diagnostics()
        PyImGui.pop_item_width()


def _draw_reachable_list_panel() -> None:
    """Floating panel listing reachable-but-unvisited outposts, shown when the checkbox is active."""
    if not _zoom_is_default():
        return
    if not Map.WorldMap.IsWindowOpen() or not _show_reachable_unvisited[0]:
        return

    fi = Map.WorldMap.GetFrameInfo()
    if fi is None:
        return
    sc = fi.GetContentCoords()
    if not sc:
        return
    sl, st = float(sc[0]), float(sc[1])

    legend_w = 190.0
    margin   = 8.0
    win_w    = 360.0

    cmap = Map.GetMapID()
    if cmap != _reachable_list_last_map[0]:
        _reachable_list_last_map[0] = cmap
        _reachable_list_cache.clear()
        # Determine current campaign group so we only show outposts from the
        # same campaign as the player's current map.
        cur_meta_rv = _MAP_META.get(cmap)
        cur_camp_rv = _campaign_group(cur_meta_rv[2]) if cur_meta_rv else 1
        seen_ids: set[int] = set()

        # Phase 1: directly reachable on foot from the current map.
        for m in GetReachableMaps(cmap):
            if Map.IsMapUnlocked(m["map_id"]):
                continue
            meta = _MAP_META.get(m["map_id"])
            if meta is None or meta[0] == _RT_EXPLORABLE:
                continue
            if _campaign_group(meta[2]) != cur_camp_rv:
                continue
            dist  = _path_distance(cmap, m["map_id"])
            ft    = GetNearestFastTravelTo(m["map_id"], cmap)
            entry = dict(m)
            entry["distance"] = dist
            entry["nearest_ft"] = ft
            _reachable_list_cache.append(entry)
            seen_ids.add(m["map_id"])

        # Phase 2: reachable via fast-travel to an unlocked outpost + walk.
        # Multi-source BFS from every unlocked outpost through portal adjacency.
        # For each reachable target, the BFS records which source (FT outpost)
        # reaches it first (fewest portal hops).
        _portal_adj_rv = _get_portal_adj()
        # seed: every unlocked non-explorable outpost is a FT source
        _rv_visited: dict[int, tuple[int, str, int]] = {}  # map_id -> (ft_map_id, ft_name, hops)
        _rv_queue: deque[int] = deque()
        for _mid, _meta in _MAP_META.items():
            if _meta[0] == _RT_EXPLORABLE:
                continue
            if not Map.IsMapUnlocked(_mid):
                continue
            _rv_visited[_mid] = (_mid, _meta[1], 0)
            _rv_queue.append(_mid)
        while _rv_queue:
            _cur = _rv_queue.popleft()
            _ft_id, _ft_name, _hops = _rv_visited[_cur]
            for _eg, _ig, _nb in _portal_adj_rv.get(_cur, []):
                if _nb not in _rv_visited:
                    _rv_visited[_nb] = (_ft_id, _ft_name, _hops + 1)
                    _rv_queue.append(_nb)
        for _target, (_ft_id, _ft_name, _ft_hops) in _rv_visited.items():
            if _target in seen_ids:
                continue
            if Map.IsMapUnlocked(_target):
                continue
            _meta = _MAP_META.get(_target)
            if _meta is None or _meta[0] == _RT_EXPLORABLE:
                continue
            if _campaign_group(_meta[2]) != cur_camp_rv:
                continue
            _ft_dist = _path_distance(_ft_id, _target)
            _entry: dict = {
                "map_id":   _target,
                "name":     _meta[1],
                "hops":     _ft_hops,
                "distance": _ft_dist,
                "nearest_ft": {
                    "map_id":   _ft_id,
                    "name":     _ft_name,
                    "hops":     _ft_hops,
                    "distance": _ft_dist,
                },
            }
            _reachable_list_cache.append(_entry)
            seen_ids.add(_target)

        _reachable_list_cache.sort(key=lambda e: (
            e["nearest_ft"]["hops"] if e.get("nearest_ft") else e["hops"],
            e["nearest_ft"]["distance"] if e.get("nearest_ft") and e["nearest_ft"].get("distance") is not None else float("inf"),
            e["hops"],
            e["name"]
        ))
    rv_list = _reachable_list_cache

    panel_flags = _get_panel_flags()
    PyImGui.set_next_window_pos(sl + margin + legend_w + margin, st + margin)
    PyImGui.set_next_window_size(win_w, 0.0)
    if not PyImGui.begin("##wm_rv_list_panel", panel_flags):
        PyImGui.end()
        return

    title_col = Utils.RGBToColor(255, 230, 140, 255)
    tx, ty = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 16)
    PyImGui.draw_list_add_text(tx, ty, title_col, "Reachable Outposts (not visited)")
    PyImGui.separator()

    if not rv_list and not _auto_explore_active[0]:
        PyImGui.text_disabled("None found from current map.")
    else:
        # ── Unlock All buttons ─────────────────────────────────────────────
        if _auto_explore_active[0]:
            target_name = _map_name_cached(_travel_queue_inflight_target[0]) if _travel_queue_inflight_target[0] else "..."
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        (0.60, 0.15, 0.10, 0.90))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.80, 0.20, 0.15, 0.95))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (0.90, 0.25, 0.20, 1.00))
            if PyImGui.button(f"Stop Unlock All  ({target_name})##ae_stop", win_w - 16.0, 0):
                _abort_worldmap_movement()
                _auto_explore_active[0] = False
                _auto_explore_target[0] = 0
                _travel_route_overlay.clear()
                _path_gids.clear()
                _path_map_names.clear()
                _travel_route_start_ms[0] = 0
                _travel_hop_times.clear()
                _travel_prev_done_count[0] = -1
            PyImGui.pop_style_color(3)
        elif rv_list:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        (0.10, 0.45, 0.15, 0.90))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.15, 0.60, 0.20, 0.95))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (0.20, 0.75, 0.28, 1.00))
            if PyImGui.button(f"Start Unlock All  ({len(rv_list)} remaining)##ae_start",
                              win_w - 16.0, 0):
                _travel_queue.clear()
                for _m in rv_list:
                    _travel_queue.append(_m["map_id"])
                _travel_queue_inflight_target[0] = 0
                _travel_queue_dispatch_ms[0] = 0
                _auto_explore_active[0] = True
                _auto_explore_target[0] = 0
            PyImGui.pop_style_color(3)
            if PyImGui.is_item_hovered():
                first = rv_list[0]
                ft    = first.get("nearest_ft")
                ft_name = ft["name"] if ft else "(current map)"
                PyImGui.begin_tooltip()
                PyImGui.text(f"Visits all {len(rv_list)} reachable unvisited outpost(s).")
                PyImGui.text(f"Next: {first['name']}  via FT: {ft_name}")
                PyImGui.end_tooltip()
        PyImGui.separator()

        text_col  = Utils.RGBToColor(230, 230, 230, 255)
        hop_col   = Utils.RGBToColor(180, 210, 255, 255)
        list_h    = min(len(rv_list) * 32.0 + 4.0, 400.0)
        PyImGui.begin_child("##rv_scroll", (win_w - 8.0, list_h), False, 0)
        ft_col    = Utils.RGBToColor(160, 255, 160, 255)
        for m in rv_list:
            hops = m["hops"]
            dist = m.get("distance")
            ft   = m.get("nearest_ft")
            if dist is not None:
                dist_k = dist / 1000.0
                meta_str = f"({dist_k:.1f}k  {hops}h)"
            else:
                meta_str = f"({hops}h)"
            sx, sy = PyImGui.get_cursor_screen_pos()
            PyImGui.draw_list_add_text(sx, sy, hop_col, meta_str)
            PyImGui.dummy(100, 14)
            PyImGui.same_line(0.0, 0.0)
            PyImGui.text(f" [{m['map_id']}] {m['name']}")
            if ft:
                ft_hops = ft['hops']
                ft_dist = ft.get('distance')
                if ft_dist is not None:
                    ft_str = f"    → FT: {ft['name']}  ({ft_dist/1000.0:.1f}k  {ft_hops}h)"
                else:
                    ft_str = f"    → FT: {ft['name']}  ({ft_hops}h)"
                fsx, fsy = PyImGui.get_cursor_screen_pos()
                PyImGui.draw_list_add_text(fsx, fsy, ft_col, ft_str)
                PyImGui.dummy(10, 13)
        PyImGui.end_child()

    PyImGui.end()


def _draw_hero_loadout_panel() -> None:
    """Floating panel for configuring and applying the hero loadout."""
    if not _zoom_is_default():
        return
    if not Map.WorldMap.IsWindowOpen() or not _show_hero_loadout[0]:
        return

    fi = Map.WorldMap.GetFrameInfo()
    if fi is None:
        return
    sc = fi.GetContentCoords()
    if not sc:
        return
    sl, st = float(sc[0]), float(sc[1])

    legend_w = 190.0
    margin   = 8.0
    win_w    = 240.0
    rv_win_w = 360.0  # width of the reachable-list panel

    # If the reachable-not-visited panel is also open, place the loadout panel
    # to the right of it; otherwise fall back to the default position (next to
    # the legend).
    if _show_reachable_unvisited[0]:
        panel_x = sl + margin + legend_w + margin + rv_win_w + margin
    else:
        panel_x = sl + margin + legend_w + margin

    max_slots = 0
    try:
        if Map.IsOutpost():
            max_slots = max(0, Map.GetMaxPartySize())
    except Exception:
        pass

    panel_flags = _get_panel_flags()
    PyImGui.set_next_window_pos(panel_x, st + margin)
    PyImGui.set_next_window_size(win_w, 0.0)
    if not PyImGui.begin("##wm_hero_loadout_panel", panel_flags):
        PyImGui.end()
        return

    title_col = Utils.RGBToColor(255, 230, 140, 255)
    tx, ty = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 16)
    PyImGui.draw_list_add_text(tx, ty, title_col, "Setup Team")
    PyImGui.separator()

    changed = False
    for i in range(_HL_MAX_SLOTS):
        active = (i < max_slots)
        if active:
            PyImGui.text_colored(f"{i + 1}.", (0.4, 0.9, 0.4, 1.0))
        else:
            PyImGui.text_colored(f"{i + 1}.", (0.4, 0.4, 0.4, 1.0))
        PyImGui.same_line(0, 4)
        if not active:
            PyImGui.begin_disabled(True)
        PyImGui.push_item_width(win_w - 80.0)
        combo_idx = _hl_hero_id_to_combo(_hl_slot_ids[i])
        new_idx   = PyImGui.combo(f"##hl_{i}", combo_idx, _HL_COMBO_ITEMS)
        PyImGui.pop_item_width()
        if new_idx != combo_idx:
            _hl_slot_ids[i] = _hl_combo_to_hero_id(new_idx)
            changed = True
        if not active:
            PyImGui.end_disabled()
        PyImGui.same_line(0, 4)
        if i > 0:
            if PyImGui.small_button(f"^##hl_u{i}"):
                _hl_slot_ids[i], _hl_slot_ids[i - 1] = _hl_slot_ids[i - 1], _hl_slot_ids[i]
                changed = True
        else:
            PyImGui.dummy(19, 0)
        PyImGui.same_line(0, 2)
        if i < _HL_MAX_SLOTS - 1:
            if PyImGui.small_button(f"v##hl_d{i}"):
                _hl_slot_ids[i], _hl_slot_ids[i + 1] = _hl_slot_ids[i + 1], _hl_slot_ids[i]
                changed = True
        else:
            PyImGui.dummy(19, 0)

    if changed:
        _wmp_ini_save()

    PyImGui.separator()

    can_load = Map.IsOutpost() and not _hl_applying[0]
    if not can_load:
        PyImGui.begin_disabled(True)
    if PyImGui.button("Load Current Team##hl_load", win_w - 16.0, 0):
        _hl_load_current_team()
    if not can_load:
        PyImGui.end_disabled()
    if PyImGui.is_item_hovered():
        PyImGui.begin_tooltip()
        PyImGui.text("Read the heroes currently in your party")
        PyImGui.text("and fill the slots above with them.")
        PyImGui.end_tooltip()

    PyImGui.separator()

    if max_slots > 0:
        PyImGui.text_colored(f"Map allows {max_slots} hero slot(s).", (0.7, 0.9, 0.7, 1.0))
    else:
        PyImGui.text_disabled("Not in an outpost.")
    PyImGui.spacing()

    _new_auto = PyImGui.checkbox("Auto-apply on zone##hl", _hl_auto_apply[0])
    if _new_auto != _hl_auto_apply[0]:
        _hl_auto_apply[0] = _new_auto
        _wmp_ini_save()
    PyImGui.spacing()

    can_apply = Map.IsOutpost() and not _hl_applying[0]
    if not can_apply:
        PyImGui.begin_disabled(True)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        (0.15, 0.45, 0.20, 0.90))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.20, 0.60, 0.28, 0.95))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (0.25, 0.75, 0.35, 1.00))
    label = "Applying..." if _hl_applying[0] else "Apply Loadout"
    if PyImGui.button(f"{label}##hl_apply", win_w - 16.0, 0):
        _hl_trigger_apply()
    PyImGui.pop_style_color(3)
    if not can_apply:
        PyImGui.end_disabled()

    PyImGui.end()


def _draw_portal_link_editor() -> None:
    """Dedicated panel for portal linking, positioned right of the legend panel."""
    if not _zoom_is_default():
        return
    if not Map.WorldMap.IsWindowOpen() or not _show_developer[0] or not _show_debug[0]:
        return

    fi = Map.WorldMap.GetFrameInfo()
    if fi is None:
        return
    sc = fi.GetContentCoords()
    if not sc:
        return
    sl, st = float(sc[0]), float(sc[1])

    legend_w = 190.0
    margin = 8.0
    win_w = 260.0

    panel_flags = _get_panel_flags()

    PyImGui.set_next_window_pos(sl + margin + legend_w + margin, st + margin)
    PyImGui.set_next_window_size(win_w, 0.0)
    if not PyImGui.begin("##wm_plus_portal_link_panel", panel_flags):
        PyImGui.end()
        return

    title_col = Utils.RGBToColor(255, 230, 140, 255)
    tx, ty = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 16)
    PyImGui.draw_list_add_text(tx, ty, title_col, "Portal Link Editor")
    PyImGui.separator()

    if _link_click_mode[0]:
        btn_label = "Cancel click-link##wmp_clm"
    else:
        btn_label = "Click portals to link##wmp_clm"
    if PyImGui.button(btn_label, win_w - 16.0, 0):
        _link_click_mode[0] = not _link_click_mode[0]
        _link_pending_gid[0] = 0
    if _link_click_mode[0]:
        if _link_pending_gid[0] == 0:
            PyImGui.text("  > Click first portal...")
        else:
            p_info = _GLOBAL_ID_TO_PORTAL.get(_link_pending_gid[0])
            if p_info:
                p_name = (_MAP_META.get(p_info[0]) or (None, f"Map {p_info[0]}"))[1]
                PyImGui.text(f"  > Selected: {p_name} P{p_info[1]}")
            else:
                PyImGui.text(f"  > Selected: GID {_link_pending_gid[0]}")
            PyImGui.text("  > Click second portal...")
        PyImGui.spacing()

    PyImGui.separator()
    PyImGui.text("Move to Portal:")
    PyImGui.push_item_width(win_w - 16.0)
    _moveto_portal_id[0] = PyImGui.input_int("##wmp_moveto_id", _moveto_portal_id[0])
    PyImGui.pop_item_width()
    mt_id = _moveto_portal_id[0]
    mt_key = _GLOBAL_ID_TO_PORTAL.get(mt_id)
    if mt_key is None and mt_id > 0:
        mt_key = (mt_id // 1000, mt_id % 1000)
    if mt_id > 0 and mt_key:
        mt_map_id, mt_local_idx = mt_key
        mt_meta = _MAP_META.get(mt_map_id)
        mt_map_name = mt_meta[1] if mt_meta else f"Map {mt_map_id}"
        PyImGui.text(f"  Portal {mt_id}: {mt_map_name} P{mt_local_idx}")
        # Ensure dots are built for that map so game coords are available
        cmap = Map.GetMapID()
        _ensure_portal_dots(mt_map_id, is_live=(cmap == mt_map_id))
        mt_dots = _PORTAL_ICON_POS.get(mt_map_id, [])
        mt_gxy: tuple[float, float] | None = None
        for _d in mt_dots:
            if len(_d) >= 7 and int(_d[4]) == mt_id:
                mt_gxy = (float(_d[5]), float(_d[6]))
                break
        if mt_gxy:
            PyImGui.text(f"  game({mt_gxy[0]:.0f}, {mt_gxy[1]:.0f})")
            on_map = (cmap == mt_map_id)
            if not on_map:
                PyImGui.begin_disabled(True)
            if PyImGui.button("Move To##wmp_moveto", win_w - 16.0, 0):
                Player.Move(mt_gxy[0], mt_gxy[1])
            if not on_map:
                PyImGui.end_disabled()
                PyImGui.text_disabled(f"  (not on map {mt_map_id})")
        else:
            PyImGui.text_disabled("  (no game coords)")
            if PyImGui.button("Move To##wmp_moveto", win_w - 16.0, 0):
                pass  # no-op, coords unknown
    elif mt_id > 0:
        PyImGui.text_disabled("  unknown portal ID")

    PyImGui.separator()
    PyImGui.text("Or link by ID:")
    half_w = (win_w - 24.0) * 0.5
    PyImGui.push_item_width(half_w)
    _link_input_a[0] = PyImGui.input_int("##wmp_link_a", _link_input_a[0])
    PyImGui.same_line(0.0, -1.0)
    _link_input_b[0] = PyImGui.input_int("##wmp_link_b", _link_input_b[0])
    PyImGui.pop_item_width()
    a_id = _link_input_a[0]
    b_id = _link_input_b[0]
    a_ok = a_id in _GLOBAL_ID_TO_PORTAL
    b_ok = b_id in _GLOBAL_ID_TO_PORTAL
    already = _PORTAL_LINKS.get(a_id) == b_id
    if PyImGui.button("Link##wmp_link", (win_w - 20.0) * 0.5, 0):
        if a_ok and b_ok and a_id != b_id and not already:
            _PORTAL_LINKS[a_id] = b_id
            _PORTAL_LINKS[b_id] = a_id
            invalidate_portal_adj()
            invalidate_reachable_adj()
            _save_portal_links()
    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Unlink##wmp_unlink", (win_w - 20.0) * 0.5, 0):
        if a_id in _PORTAL_LINKS:
            b2 = _PORTAL_LINKS.pop(a_id)
            _PORTAL_LINKS.pop(b2, None)
            invalidate_portal_adj()
            invalidate_reachable_adj()
            _save_portal_links()
    if a_id > 0 or b_id > 0:
        a_info = _GLOBAL_ID_TO_PORTAL.get(a_id)
        b_info = _GLOBAL_ID_TO_PORTAL.get(b_id)
        hint_a = f"ID {a_id}: map {a_info[0]} P{a_info[1]}" if a_info else (f"ID {a_id}: unknown" if a_id else "")
        hint_b = f"ID {b_id}: map {b_info[0]} P{b_info[1]}" if b_info else (f"ID {b_id}: unknown" if b_id else "")
        if hint_a:
            PyImGui.text(hint_a)
        if hint_b:
            PyImGui.text(hint_b)
        if already:
            PyImGui.text("  (already linked)")
    if _PORTAL_LINKS:
        filter_ids = {x for x in (a_id, b_id) if x > 0}
        if filter_ids:
            seen_pairs: set[tuple[int, int]] = set()
            filtered: list[tuple[int, int]] = []
            for aid, bid in sorted(_PORTAL_LINKS.items()):
                p = (min(aid, bid), max(aid, bid))
                if p in seen_pairs:
                    continue
                seen_pairs.add(p)
                if aid in filter_ids or bid in filter_ids:
                    filtered.append((aid, bid))
            PyImGui.text(f"Links ({len(filtered)}):")
            for aid, bid in filtered:
                am = _GLOBAL_ID_TO_PORTAL.get(aid, (0, 0))
                bm = _GLOBAL_ID_TO_PORTAL.get(bid, (0, 0))
                PyImGui.text(f"  {aid}(m{am[0]}) ↔ {bid}(m{bm[0]})")

    # ── Map info ───────────────────────────────────────────────────────────
    PyImGui.separator()
    try:
        cmap  = Map.GetMapID()
        cname = Map.GetMapName(cmap) or f"Map {cmap}"
        PyImGui.text_colored(f"[{cmap}] {cname}", (0.8, 0.9, 1.0, 1.0))
        cur_meta = _MAP_META.get(cmap)
        if cur_meta:
            grp = _campaign_group(cur_meta[2])
            camp_label = _CAMPAIGN_GROUP_NAMES.get(grp, f"Campaign {grp}")
            PyImGui.text(f"Campaign: {camp_label}")
    except Exception:
        pass
    n = sum(1 for v in _ICON_BOUNDS.values() if v is not None)
    PyImGui.text(f"Maps: {n}  Edges: {len(_ALL_EDGES)}")

    # ── Custom Dungeon Placements ──────────────────────────────────────────
    PyImGui.separator()
    title_col2 = Utils.RGBToColor(180, 255, 180, 255)
    tx2, ty2 = PyImGui.get_cursor_screen_pos()
    PyImGui.dummy(int(win_w), 16)
    PyImGui.draw_list_add_text(tx2, ty2, title_col2, "Custom Dungeon Placements")
    PyImGui.text_disabled("Portal GID         Dungeon Map ID")

    PyImGui.push_item_width((win_w - 24.0) * 0.5)
    _cp_entrance_gid[0] = PyImGui.input_int("##cp_egid", _cp_entrance_gid[0])
    PyImGui.same_line(0.0, -1.0)
    _cp_dungeon_id[0]   = PyImGui.input_int("##cp_dmid", _cp_dungeon_id[0])
    PyImGui.pop_item_width()
    PyImGui.push_item_width(win_w - 16.0)
    _cp_dungeon_name[0] = PyImGui.input_text("##cp_dname", _cp_dungeon_name[0], 64)
    PyImGui.pop_item_width()

    # Hint: resolve entrance portal
    egid = _cp_entrance_gid[0]
    if egid > 0:
        emap = egid // 1000
        en   = (_MAP_META.get(emap) or (None, f"Map {emap}"))[1]
        PyImGui.text_disabled(f"  Entrance: {en} p{egid % 1000} (map {emap})")

    can_add = (
        _cp_entrance_gid[0] > 0
        and _cp_dungeon_id[0] > 0
        and _cp_entrance_gid[0] // 1000 != _cp_dungeon_id[0]
        and _cp_dungeon_name[0].strip() != ""
        and _ICON_BOUNDS.get(_cp_entrance_gid[0] // 1000) is not None
    )
    if not can_add:
        PyImGui.begin_disabled(True)
    if PyImGui.button("Add##cp_add", (win_w - 20.0) * 0.5, 0):
        _apply_custom_dungeon_placement(
            _cp_entrance_gid[0], _cp_dungeon_id[0], _cp_dungeon_name[0].strip()
        )
        _save_custom_placements()
        invalidate_portal_adj()
        invalidate_reachable_adj()
        _save_portal_links()
    if not can_add:
        PyImGui.end_disabled()

    PyImGui.same_line(0.0, -1.0)
    can_remove = (
        _cp_dungeon_id[0] > 0
        and _cp_dungeon_id[0] in _CUSTOM_DUNGEON_MAP_IDS
    )
    if not can_remove:
        PyImGui.begin_disabled(True)
    if PyImGui.button("Remove##cp_rem", (win_w - 20.0) * 0.5, 0):
        dmid = _cp_dungeon_id[0]
        dportal = dmid * 1000
        epid = _PORTAL_LINKS.pop(dportal, None)
        if epid:
            _PORTAL_LINKS.pop(epid, None)
        _PORTAL_ALL_DATA.pop(dmid, None)
        _PORTAL_ICON_POS.pop(dmid, None)
        _PORTAL_BUILT.discard(dmid)
        _MANUAL_PORTAL_MAPS.discard(dmid)
        _CONNECTED_MAP_IDS.discard(dmid)
        _CUSTOM_DUNGEON_MAP_IDS.discard(dmid)
        _DRAW_GROUPS[:] = [g for g in _DRAW_GROUPS if dmid not in g[0]]
        _ICON_BOUNDS.pop(dmid, None)
        for nb in list(_MAP_NEIGHBORS.get(dmid, [])):
            _MAP_NEIGHBORS.get(nb, set()).discard(dmid)
            _MAP_ADJACENCY.get(nb, set()).discard(dmid)
        _MAP_NEIGHBORS.pop(dmid, None)
        _MAP_ADJACENCY.pop(dmid, None)
        if epid:
            edge = (min(dmid, epid // 1000), max(dmid, epid // 1000))
            _ALL_EDGES.discard(edge)
        _wp_invalidate_world_adj()
        invalidate_portal_adj()
        invalidate_reachable_adj()
        _save_custom_placements()
        _save_portal_links()
    if not can_remove:
        PyImGui.end_disabled()

    # List existing custom placements
    if _CUSTOM_DUNGEON_MAP_IDS:
        PyImGui.spacing()
        for dmid in sorted(_CUSTOM_DUNGEON_MAP_IDS):
            dportal = dmid * 1000
            epid    = _PORTAL_LINKS.get(dportal, 0)
            cn      = (_MAP_META.get(dmid) or (None, f"Map {dmid}"))[1]
            emap    = epid // 1000 if epid else 0
            en      = (_MAP_META.get(emap) or (None, f"Map {emap}"))[1] if emap else "?"
            PyImGui.text_disabled(f"  [{dmid}] {cn} ← portal {epid} ({en})")

    PyImGui.end()


def _draw_diagnostics() -> None:
    """Dump raw WorldMap context values to help calibrate the coordinate transform."""
    try:
        ic = Map.WorldMap.GetWindowCoords()
        PyImGui.text(f"GetWindowCoords: ({ic[0]:.1f},{ic[1]:.1f},{ic[2]:.1f},{ic[3]:.1f})")
        fi = Map.WorldMap.GetFrameInfo()
        if fi:
            sc = fi.GetContentCoords()
            PyImGui.text(f"GetContentCoords: ({sc[0]:.1f},{sc[1]:.1f},{sc[2]:.1f},{sc[3]:.1f})")
        PyImGui.text(f"Zoom: {Map.WorldMap.GetZoom():.4f}")

        # Live portal/pathing diagnostics for current map
        cmap = Map.GetMapID()
        live_pmaps = 0
        live_portals = 0
        try:
            pm_list = Map.Pathing.GetPathingMaps()
            live_pmaps = len(pm_list) if pm_list else 0
        except Exception:
            live_pmaps = 0
        try:
            portal_list = Map.Pathing.GetTravelPortals()
            live_portals = len(portal_list) if portal_list else 0
        except Exception:
            live_portals = 0

        _ensure_portal_dots(cmap, is_live=True)
        portal_dots = len(_PORTAL_ICON_POS.get(cmap, []))

        PyImGui.text(f"Current map: {cmap}")
        PyImGui.text(f"PathingMaps (live): {live_pmaps}")
        PyImGui.text(f"TravelPortals (live): {live_portals}")
        PyImGui.text(f"Portal dots (built): {portal_dots}")

        extra = Map.WorldMap.GetExtraData()
        if extra:
            pairs = [(k, extra[k]) for k in ("h000c","h0010","h0018","h001c","h0020","h0024",
                                              "h0028","h002c","h0030","h0034","h0068","h006c") if k in extra]
            for k, v in pairs:
                PyImGui.text(f"  {k}: {v:.4f}")
    except Exception as e:
        PyImGui.text(f"diag err: {e}")


# ── Entry point (called every frame by Py4GW) ─────────────────────────────────

def main() -> None:
    global _cache_built
    try:
        _set_runtime_heartbeat()
        _wmp_ini_try_init()
        if not _cache_built:
            _build_cache()

        # Invalidate live portal cache on map change
        cmap = Map.GetMapID()
        if cmap != _debug_last_map[0]:
            if _debug_last_map[0] > 0:
                # Remove old map's portal entry so it rebuilds as offline next visit
                _PORTAL_BUILT.discard(_debug_last_map[0])
                _PORTAL_ICON_POS.pop(_debug_last_map[0], None)
                _PMAP_GAME_BOUNDS.pop(_debug_last_map[0], None)
            # Also remove new map's entry in case we have stale offline data for it
            _PORTAL_BUILT.discard(cmap)
            _PORTAL_ICON_POS.pop(cmap, None)
            _PMAP_GAME_BOUNDS.pop(cmap, None)
            _is_path_cache.clear()
            _is_ft_path_cache.clear()
            _debug_last_map[0] = cmap
            # Patch stale hero OwnerAgentID values in shared memory.
            # Agent IDs change on every map transition. Any hero slot written in a
            # previous map has the old (now-wrong) OwnerAgentID stored, causing
            # GetHeroSlotByHeroData to reject it and spam "No slot found" every frame.
            # Fix: scan all slots by HeroID + AccountEmail and refresh OwnerAgentID.
            _refresh_hero_slot_owner_ids()
            # Hero Loadout: auto-apply when zoning into an outpost during an active route.
            _has_active_route = (_mtm_runner_active[0] or _mtnw_runner_active[0]
                                 or _travel_coroutine_active[0] or bool(_travel_queue)
                                 or _auto_explore_active[0])
            if _hl_auto_apply[0] and Map.IsOutpost() and _has_active_route:
                _hl_trigger_apply_delayed()
            # Only wipe route data when no runner is active.
            # While the bot is travelling, the route must stay visible.
            # Also keep when Unlock All is running (it rebuilds the overlay itself).
            if not _mtm_runner_active[0] and not _mtnw_runner_active[0] and not _auto_explore_active[0]:
                _travel_route_overlay.clear()
                _path_gids.clear()
                _path_map_names.clear()
                _travel_route_start_ms[0] = 0
                _travel_hop_times.clear()
                _travel_prev_done_count[0] = -1
                _path_name_offset[0] = 0
            elif _auto_explore_active[0] and _mtm_target_map[0]:
                # Unlock All active: rebuild overlay from the current map toward the target
                # so the remaining route lines stay accurate on every hop.
                _new_route = GetPath(cmap, _mtm_target_map[0])
                if _new_route.get("found"):
                    _travel_route_overlay[:] = _build_route_overlay(_new_route)
                    _old_name_len = len(_path_map_names)
                    _path_map_names[:] = _new_route.get("map_names", [])
                    _path_name_offset[0] += max(0, _old_name_len - len(_path_map_names))
                    gids: list[int] = []
                    for _wp in _new_route.get("waypoints", []):
                        gids.extend([_wp["exit_gid"], _wp["enter_gid"]])
                    _path_gids[:] = gids

            # Reset demo results when map changes
            _wp_is_path_result[0]  = None
            _wp_get_path_found[0]  = False
            _wp_get_path_maps.clear()
            _wp_get_path_result.clear()
            _wp_get_path_full[0]   = None
            _wp_move_result[0]     = None
            _wp_move_map_result[0] = None

        _process_travel_queue()

        _draw_overlay()
        _draw_travel_buttons()
        _draw_legend()
        _draw_reachable_list_panel()
        _draw_hero_loadout_panel()
        _draw_portal_link_editor()
        _draw_travel_roadmap()
        _draw_worldpathing_demo()
        _draw_mtnw_path_3d()
        _draw_portal_ids_3d()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"{e}\n{traceback.format_exc()}",
                          Py4GW.Console.MessageType.Error)


if __name__ == "__main__":
    main()
