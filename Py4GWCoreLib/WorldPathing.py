"""
WorldPathing
============
Shared pathing data layer for Guild Wars World Map overlays and bots.

Provides:
  - Map adjacency graph (_MAP_ADJACENCY, _ALL_EDGES)
  - Icon-space coordinate caches (_ICON_BOUNDS, _MAP_META, etc.)
  - Portal dot positions (_PORTAL_ICON_POS, _PORTAL_BUILT)
  - Pathing-map trapezoid caches (_PMAP_CACHE, _PMAP_BUILT)
  - Portal link persistence (portal_links.json)
  - BFS map path finder (_find_map_path)
  - Coordinate transform helpers (_traps_to_icon, etc.)
  - pmap offset calibration (_record_calibration)

Call configure(script_dir) once before using any functions that access JSON
files (portal_destinations.json, portal_links.json, pmap_offset_debug.json).
"""

import Py4GW
import json
import os
import math
from collections import defaultdict, deque

from Py4GWCoreLib import Map, Utils, Player
from Py4GWCoreLib.native_src.methods.MapMethods import MapMethods
from Py4GWCoreLib.native_src.methods.FfnaMapMethods import FfnaMapMethods

MODULE_NAME = "WorldPathing"


# ── File paths (set by configure()) ──────────────────────────────────────────
_OFFSET_FILE            = ""
_PORTAL_DEST_FILE       = ""
_PORTAL_LINKS_FILE      = ""
_LIVE_PORTAL_CACHE_FILE = ""


def configure(script_dir: str) -> None:
    """Set JSON file paths relative to the calling widget's script directory.
    Must be called once (e.g. at module load of the widget) before any function
    that reads/writes portal_destinations.json, portal_links.json, or
    pmap_offset_debug.json."""
    global _OFFSET_FILE, _PORTAL_DEST_FILE, _PORTAL_LINKS_FILE, _LIVE_PORTAL_CACHE_FILE
    _OFFSET_FILE            = os.path.join(script_dir, "pmap_offset_debug.json")
    _PORTAL_DEST_FILE       = os.path.join(script_dir, "portal_destinations.json")
    _PORTAL_LINKS_FILE      = os.path.join(script_dir, "portal_links.json")
    _LIVE_PORTAL_CACHE_FILE = os.path.join(script_dir, "portal_live_cache.json")
    _load_live_portal_cache()


# ── Hardcoded walkable-portal adjacency graph ─────────────────────────────────
# Copy of the same graph used in Caravan.py.  Extend as you discover new edges.
_MAP_ADJACENCY: dict[int, set[int]] = {
    # ── EotN: Norn region ────────────────────────────────────────────────────
    642: {482, 513, 546, 548, 553, 589, 590, 591, 592},
    482: {642, 513, 546},
    513: {642, 482, 546, 548},
    546: {642, 482, 513},
    548: {642, 513, 553},
    553: {642, 548, 647, 649},
    647: {553, 649, 651},
    649: {553, 647, 651},
    651: {647, 649},
    589: {642, 553},
    590: {642, 482},
    591: {642, 548},
    592: {642, 546},
    # ── EotN: Asura region ───────────────────────────────────────────────────
    572: {642, 558, 566, 501},
    558: {572, 566, 501, 569},
    501: {572, 558, 569},
    566: {572, 558},
    569: {558, 501},
    594: {572, 558},
    595: {501, 572},
    596: {566, 572},
    598: {569, 558},
    # ── Nightfall: Istan region ──────────────────────────────────────────────
    449: {430, 431, 432, 483, 484, 486, 488},
    543: {430, 449},
    430: {449, 543, 431, 432, 484, 486},
    431: {449, 430, 432, 483},
    432: {449, 430, 431, 484},
    483: {431, 449, 484, 485},
    484: {430, 432, 449, 483, 486},
    485: {483, 486, 488},
    486: {430, 449, 484, 485, 488},
    488: {449, 485, 486, 490},
    490: {488},
    450: {430, 449},
    451: {430, 449},
    452: {430, 449, 431},
    427: {449},
    # ── Nightfall: Kourna region ─────────────────────────────────────────────
    371: {369, 373, 375, 377, 379, 380},
    369: {371, 373, 375, 379, 392, 394},
    373: {371, 369, 375, 385},
    375: {371, 373, 377, 379, 384, 385},
    377: {371, 375, 379},
    379: {371, 369, 375, 377, 380, 382},
    380: {371, 379, 384},
    382: {379, 380},
    384: {375, 380},
    385: {373, 375},
    392: {369, 394, 397, 404},
    394: {369, 392, 395, 397},
    # ── Nightfall: Vabbi region ───────────────────────────────────────────────
    395: {394, 397, 399, 406},
    397: {392, 394, 395, 399, 402},
    399: {395, 397, 402, 404, 406},
    402: {394, 397, 399, 406},
    404: {392, 399},
    406: {395, 399, 402},
    # ── Prophecies: Kryta ────────────────────────────────────────────────────
    58:  {59, 62, 63, 64},
    59:  {58, 60, 61},
    60:  {59, 61, 64},
    61:  {59, 60, 63},
    62:  {58, 63},
    63:  {58, 61, 62, 64},
    64:  {58, 60, 63},
    # ── Factions: Shing Jea ──────────────────────────────────────────────────
    235: {236, 237, 238},
    236: {235, 237, 246},
    237: {235, 236, 238},
    238: {235, 237},
}

# Make bidirectional
for _src, _dsts in list(_MAP_ADJACENCY.items()):
    for _dst in _dsts:
        _MAP_ADJACENCY.setdefault(_dst, set()).add(_src)

# Deduplicated edge set (each pair stored once as (min, max))
_ALL_EDGES: set[tuple[int, int]] = set()
for _a, _bs in _MAP_ADJACENCY.items():
    for _b in _bs:
        _ALL_EDGES.add((min(_a, _b), max(_a, _b)))


# ── Map metadata / icon-space caches ─────────────────────────────────────────
# Populated by WorldMap+._build_cache() on startup.

# Loaded from JSON at startup: map_id(str) → [dx_icon, dy_icon]
# These are additive corrections applied to every trapezoid icon-space coord.
_PMAP_OFFSETS: dict[int, tuple[float, float]] = {}

# map_id -> (left, top, right, bottom) in icon space, or None
_ICON_BOUNDS:  dict[int, tuple[float, float, float, float] | None] = {}
# map_id -> (type:int, name:str, campaign:int)
_MAP_META:     dict[int, tuple[int, str, int]] = {}
# map_id -> icon-space center (derived from _ICON_BOUNDS)
_MAP_CENTROIDS: dict[int, tuple[float, float]] = {}
# map_id -> set of adjacent map_ids (derived from _ALL_EDGES)
_MAP_NEIGHBORS: dict[int, set[int]] = {}


# ── Portal + pmap cache (game coords → icon space) ───────────────────────────
# _PMAP_CACHE: rep_map_id → list of icon-space quad tuples (xtl,ytl,xtr,ytr,xbr,ybr,xbl,ybl)
# Built lazily per map; live for current map, offline (.dat) for all others.
_PMAP_CACHE:        dict[int, list[tuple]] = {}
_PMAP_BUILT:        set[int] = set()          # rep_ids already attempted
# Persistent cache of live portal game-coords for maps without a DAT entry.
# map_id → [{"x": float, "y": float, "z": float, "model_file_id": int}]
_live_portal_cache: dict[int, list[dict]] = {}
_PORTAL_ICON_POS:   dict[int, list[tuple]] = {}  # map_id → list of (pix, piy, dest_name, local_idx, global_id, gx, gy)
_PORTAL_BUILT:      set[int] = set()              # maps already processed
# Loaded from portal_destinations.json: map_id → [{index, game_x, game_y, dest_map_id, dest_name}]
_PORTAL_DEST_DATA:  dict[int, list[dict]] = {}
# Global sequential portal IDs (built when JSON is loaded)
_GLOBAL_ID_TO_PORTAL: dict[int, tuple[int, int]] = {}  # global_id → (map_id, local_idx)
_PORTAL_TO_GLOBAL_ID: dict[tuple[int, int], int] = {}  # (map_id, local_idx) → global_id
_PORTAL_LINKS:        dict[int, int] = {}             # global_id → linked global_id (both dirs)
_PORTAL_GAME_POS:     dict[int, tuple[float, float]] = {}  # global_id → (game_x, game_y)
# Cached adjacency: map_id → [(exit_gid, enter_gid, dest_map_id)]  (None = stale)
_portal_adj_cache: dict[int, list[tuple[int, int, int]]] | None = None


def invalidate_portal_adj() -> None:
    """Mark the portal adjacency cache as stale. Call whenever _PORTAL_LINKS changes."""
    global _portal_adj_cache
    _portal_adj_cache = None


def _get_portal_adj() -> dict[int, list[tuple[int, int, int]]]:
    """Return (cached) adjacency dict built from _PORTAL_LINKS."""
    global _portal_adj_cache
    if _portal_adj_cache is not None:
        return _portal_adj_cache
    adj: dict[int, list[tuple[int, int, int]]] = {}
    seen: set[tuple[int, int]] = set()
    for gid_a, gid_b in _PORTAL_LINKS.items():
        pair = (min(gid_a, gid_b), max(gid_a, gid_b))
        if pair in seen:
            continue
        seen.add(pair)
        ka = _GLOBAL_ID_TO_PORTAL.get(gid_a)
        kb = _GLOBAL_ID_TO_PORTAL.get(gid_b)
        map_a = ka[0] if ka else gid_a // 1000
        map_b = kb[0] if kb else gid_b // 1000
        adj.setdefault(map_a, []).append((gid_a, gid_b, map_b))
        adj.setdefault(map_b, []).append((gid_b, gid_a, map_a))
    _portal_adj_cache = adj
    return adj


# ── Helper functions ──────────────────────────────────────────────────────────

def _map_name_cached(mid: int) -> str:
    meta = _MAP_META.get(mid)
    return meta[1] if meta else f"Map {mid}"


def _portal_dest_name(src_map_id: int, pix: float, piy: float) -> str:
    """Infer portal destination: nearest neighbor centroid in icon space."""
    neighbors = _MAP_NEIGHBORS.get(src_map_id, set())
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


def _traps_to_icon(trapezoids: list, ix1: float, iy1: float, ix2: float, iy2: float,
                   offset: tuple[float, float] = (0.0, 0.0)
                   ) -> list[tuple]:
    """Convert trap list to icon-space quads.  Returns [] if bounds are degenerate."""
    if not trapezoids:
        return []
    gx_min = float('inf');  gx_max = float('-inf')
    gy_min = float('inf');  gy_max = float('-inf')
    for trap in trapezoids:
        for x in (trap.XTL, trap.XTR, trap.XBL, trap.XBR):
            if x < gx_min: gx_min = x
            if x > gx_max: gx_max = x
        for y in (trap.YT, trap.YB):
            if y < gy_min: gy_min = y
            if y > gy_max: gy_max = y
    if gx_min == float('inf') or gx_max <= gx_min or gy_max <= gy_min:
        return []
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


def _load_offsets() -> None:
    """Read pmap_offset_debug.json 'offsets' section and apply to _PMAP_OFFSETS."""
    if not os.path.isfile(_OFFSET_FILE):
        return
    try:
        with open(_OFFSET_FILE, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
        overrides = data.get("offsets", {})
        count = 0
        for k, v in overrides.items():
            _PMAP_OFFSETS[int(k)] = (float(v[0]), float(v[1]))
            count += 1
        if count:
            Py4GW.Console.Log(MODULE_NAME,
                f"Applied {count} manual pmap offset overrides from JSON.",
                Py4GW.Console.MessageType.Info)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Offset load error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _ensure_portal_dots(map_id: int, is_live: bool) -> None:
    """Lazily build portal dot positions for map_id (live or offline .dat)."""
    debug_map = False  # set to True and add map_id to enable portal debug logging

    def _debug_log(stage: str, portals_count: int, dots: list[tuple]) -> None:
        if not debug_map:
            return
        gids = [int(d[4]) for d in dots if len(d) >= 5]
        sample = gids[:12]
        suffix = "" if len(gids) <= 12 else f" ...(+{len(gids) - 12})"
        coord_preview: list[str] = []
        for d in dots[:8]:
            if len(d) < 5:
                continue
            gid = int(d[4])
            ix = float(d[0]) if len(d) >= 1 else 0.0
            iy = float(d[1]) if len(d) >= 2 else 0.0
            if len(d) >= 7:
                gx = float(d[5])
                gy = float(d[6])
                coord_preview.append(
                    f"portal_id={gid} icon({ix:.1f},{iy:.1f}) game({gx:.1f},{gy:.1f})"
                    f" moveto({gx:.0f},{gy:.0f})"
                )
            else:
                coord_preview.append(f"portal_id={gid} icon({ix:.1f},{iy:.1f})")
        coord_suffix = "" if len(dots) <= 8 else f" ...(+{len(dots) - 8})"
        Py4GW.Console.Log(
            MODULE_NAME,
            (
                f"Map {map_id} portal debug [{stage}] src={'live' if is_live else 'dat'} "
                f"raw_portals={portals_count} dots={len(dots)} gids={sample}{suffix} "
                f"coords={coord_preview}{coord_suffix}"
            ),
            Py4GW.Console.MessageType.Info,
        )

    if map_id in _PORTAL_BUILT:
        existing = _PORTAL_ICON_POS.get(map_id, [])
        if existing:
            # If we now have live data but the cache was built from offline fallback
            # (all dots are 5-tuples without game coords), force a rebuild so that
            # real game coordinates are stored and 3D labels can be shown.
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
        _debug_log("no-icon-bounds", 0, [])
        return
    ix1, iy1, ix2, iy2 = icon_bnd
    try:
        if is_live:
            pathing_maps = Map.Pathing.GetPathingMaps()
            portals      = Map.Pathing.GetTravelPortals()
        else:
            pathing_maps = FfnaMapMethods.GetPathingMapsForMap(map_id)
            portals      = FfnaMapMethods.GetTravelPortalsForMap(map_id)
            # Fallback: use previously cached live portal data for maps with no DAT entry
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
        _debug_log("read-exception", 0, [])
        return
    def _build_neighbor_fallback_dots() -> list[tuple]:
        """Create synthetic portal dots from map adjacency when travel portal data is missing."""
        neighbors = sorted(_MAP_NEIGHBORS.get(map_id, set()))
        cx = (ix1 + ix2) * 0.5
        cy = (iy1 + iy2) * 0.5
        inset = 1.0
        out: list[tuple] = []

        # Always produce at least one stable fallback portal ID for this map.
        # This keeps ID expectations deterministic (e.g. map 25 -> portal 25000).
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

    # Try to recover extents from live cache when pathing_maps is unavailable
    _cached_extents = None
    if not pathing_maps and map_id in _live_portal_cache:
        ce = _live_portal_cache[map_id]
        if isinstance(ce, dict) and "extents" in ce:
            _cached_extents = ce["extents"]

    if (not pathing_maps and _cached_extents is None) or not portals:
        fallback = _build_neighbor_fallback_dots()
        _PORTAL_ICON_POS[map_id] = fallback
        _debug_log("fallback-missing-pathing-or-portals", len(portals) if portals else 0, fallback)
        return
    if _cached_extents is not None:
        gx_min = _cached_extents["gx_min"]
        gx_max = _cached_extents["gx_max"]
        gy_min = _cached_extents["gy_min"]
        gy_max = _cached_extents["gy_max"]
    else:
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
        # Some maps can expose TravelPortals but have unusable/empty pathing extents.
        # Keep portal IDs visible by projecting from icon center as a deterministic fallback.
        cx = (ix1 + ix2) * 0.5
        cy = (iy1 + iy2) * 0.5
        n = max(1, len(portals))
        radius = max(2.0, min(abs(ix2 - ix1), abs(iy2 - iy1)) * 0.22)
        dots: list[tuple] = []
        # Sort by game coords for stable GID assignment across sessions
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
        _debug_log("fallback-invalid-pathing-extents", len(portals), dots)
        return
    gw = gx_max - gx_min
    gh = gy_max - gy_min
    iw_map = ix2 - ix1
    ih_map = iy2 - iy1
    json_entries = _PORTAL_DEST_DATA.get(map_id, [])
    # Sort by game coords for stable GID assignment across sessions
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
        # Always use stable fallback ID: map_id * 1000 + local_idx
        gid = map_id * 1000 + idx
        _PORTAL_TO_GLOBAL_ID[key] = gid
        _GLOBAL_ID_TO_PORTAL[gid] = key
        dots.append((pix, piy, dest, idx, gid, tp.x, tp.y))
    _PORTAL_ICON_POS[map_id] = dots
    _debug_log("normal", len(portals), dots)
    # Persist live portal coords + pathing extents so maps without a DAT entry show portals offline
    if is_live and portals:
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


def _load_portal_destinations() -> None:
    """Load portal_destinations.json into _PORTAL_DEST_DATA."""
    global _PORTAL_DEST_DATA
    _PORTAL_DEST_DATA.clear()
    if os.path.isfile(_PORTAL_DEST_FILE):
        try:
            with open(_PORTAL_DEST_FILE, "r", encoding="utf-8-sig") as fh:
                raw = json.load(fh)
            for k, entries in raw.get("portals", {}).items():
                _PORTAL_DEST_DATA[int(k)] = entries
            defined = sum(1 for entries in _PORTAL_DEST_DATA.values()
                          for e in entries if e.get("dest_map_id", 0) != 0)
            Py4GW.Console.Log(MODULE_NAME,
                f"Portal destinations loaded: {len(_PORTAL_DEST_DATA)} maps, "
                f"{defined} resolved.",
                Py4GW.Console.MessageType.Info)
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Portal destinations load error: {e}",
                              Py4GW.Console.MessageType.Warning)
    # Always load links – GIDs use map_id*1000+idx (stable, no JSON dependency)
    _load_portal_links()


def _portal_link_entry(gid: int) -> dict:
    """Build the portal sub-object for a link entry (used by save)."""
    key = _GLOBAL_ID_TO_PORTAL.get(gid)
    if key is None:
        # Fallback-ID: decode map_id * 1000 + idx
        map_id  = gid // 1000
        loc_idx = gid %  1000
        key = (map_id, loc_idx)
    map_id, loc_idx = key
    meta     = _MAP_META.get(map_id)
    map_name = meta[1] if meta else f"Map {map_id}"

    # Look up game coordinates from _PORTAL_ICON_POS (set when portal dots are built)
    game_x = game_y = None
    for entry in _PORTAL_ICON_POS.get(map_id, []):
        if entry[3] == loc_idx:          # index 3 = local_idx
            if len(entry) >= 7:
                game_x = round(float(entry[5]), 2)
                game_y = round(float(entry[6]), 2)
            break

    # Fallback: portal_destinations.json (for pre-generated data)
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


def _load_portal_links() -> None:
    """Load portal_links.json into _PORTAL_LINKS and _PORTAL_GAME_POS."""
    _PORTAL_LINKS.clear()
    _PORTAL_GAME_POS.clear()
    invalidate_portal_adj()
    if not os.path.isfile(_PORTAL_LINKS_FILE):
        return
    try:
        with open(_PORTAL_LINKS_FILE, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
        count = 0
        for entry in data.get("links", []):
            a = int(entry["portal_a"]["global_id"])
            b = int(entry["portal_b"]["global_id"])
            _PORTAL_LINKS[a] = b
            _PORTAL_LINKS[b] = a
            for side in ("portal_a", "portal_b"):
                p = entry[side]
                gid = int(p["global_id"])
                gx  = float(p.get("game_x", 0.0))
                gy  = float(p.get("game_y", 0.0))
                if gx != 0.0 or gy != 0.0:
                    _PORTAL_GAME_POS[gid] = (gx, gy)
            count += 1
        if count:
            Py4GW.Console.Log(MODULE_NAME,
                f"Portal links loaded: {count} connections.",
                Py4GW.Console.MessageType.Info)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Portal links load error: {e}",
                          Py4GW.Console.MessageType.Warning)


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
        with open(_PORTAL_LINKS_FILE, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
        Py4GW.Console.Log(MODULE_NAME,
            f"Saved {len(entries)} portal links to portal_links.json.",
            Py4GW.Console.MessageType.Info)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Portal link save error: {e}",
                          Py4GW.Console.MessageType.Warning)


def _find_map_path(start_map: int, end_map: int) -> tuple[list[int], list[str]]:
    """BFS from start_map to end_map through linked portals.
    Returns (gid_sequence, map_name_sequence).
    gid_sequence: [exit_gid_1, enter_gid_1, exit_gid_2, enter_gid_2, ...]
    map_name_sequence: [start_name, map2_name, ..., end_name]
    BFS guarantees the path with the fewest map hops (waypoints) is always returned.
    """
    if start_map == end_map or not _PORTAL_LINKS:
        return [], []

    adj = _get_portal_adj()  # cached; rebuilt only when links change

    if start_map not in adj or end_map not in adj:
        return [], []

    # BFS – explores level-by-level so the first path found to end_map is always shortest.
    queue: deque = deque([(start_map, [])])
    visited: set[int] = {start_map}
    while queue:
        cur_map, hops = queue.popleft()
        for exit_gid, enter_gid, next_map in adj.get(cur_map, []):
            if next_map in visited:
                continue
            new_hops = hops + [(exit_gid, enter_gid)]
            if next_map == end_map:
                gids: list[int] = []
                mnames: list[str] = [_map_name_cached(start_map)]
                for eg, ig in new_hops:
                    gids.extend([eg, ig])
                    km = _GLOBAL_ID_TO_PORTAL.get(ig)
                    mnames.append(_map_name_cached(km[0]) if km else f"Map {ig // 1000}")
                return gids, mnames
            visited.add(next_map)
            queue.append((next_map, new_hops))
    return [], []


# ── Public routing API was moved to WorldMap+.py ────────────────────────────


# ── pmap offset calibration recording ────────────────────────────────────────
def _record_calibration(map_id: int) -> None:
    """
    Save calibration record for map_id to pmap_offset_debug.json.
    Collects: icon bounds, pmap game bounds, AreaInfoStruct.x/y,
    player game pos, player computed icon pos.
    The JSON also has an 'offsets' section that can be edited manually
    (or auto-computed) and is re-read on next _build_cache.
    """
    try:
        icon_bnd = _ICON_BOUNDS.get(map_id)
        if not icon_bnd:
            return
        ix1, iy1, ix2, iy2 = icon_bnd

        # AreaInfoStruct data
        info = MapMethods.GetMapInfo(map_id)
        struct_x  = int(info.x)  if info else 0
        struct_y  = int(info.y)  if info else 0

        # pmap game bounds
        pm_list = Map.Pathing.GetPathingMaps()
        if not pm_list:
            return
        gx_min = float('inf');  gx_max = float('-inf')
        gy_min = float('inf');  gy_max = float('-inf')
        for pm in pm_list:
            for trap in pm.trapezoids:
                for x in (trap.XTL, trap.XTR, trap.XBL, trap.XBR):
                    if x < gx_min: gx_min = x
                    if x > gx_max: gx_max = x
                for y in (trap.YT, trap.YB):
                    if y < gy_min: gy_min = y
                    if y > gy_max: gy_max = y
        if gx_min == float('inf'):
            return

        gw     = gx_max - gx_min
        gh     = gy_max - gy_min
        iw_map = ix2 - ix1
        ih_map = iy2 - iy1

        # Player position
        px, py = Player.GetXY()

        # Player icon pos via our formula
        plr_ix = ix1 + (px - gx_min) / gw * iw_map  if gw else 0.0
        plr_iy = iy1 + (gy_max - py) / gh * ih_map  if gh else 0.0

        # Game center → icon (should equal icon rect center exactly if mapping is perfect)
        gc_ix = ix1 + 0.5 * iw_map
        gc_iy = iy1 + 0.5 * ih_map

        name = Map.GetMapName(map_id) or f"Map {map_id}"

        record = {
            "map_id":            map_id,
            "map_name":          name,
            "icon_start_x":      ix1,  "icon_start_y": iy1,
            "icon_end_x":        ix2,  "icon_end_y":   iy2,
            "icon_center_x":     gc_ix, "icon_center_y": gc_iy,
            "struct_icon_x":     struct_x, "struct_icon_y": struct_y,
            "pmap_gx_min":       round(gx_min, 1), "pmap_gy_min": round(gy_min, 1),
            "pmap_gx_max":       round(gx_max, 1), "pmap_gy_max": round(gy_max, 1),
            "pmap_game_center_x": round((gx_min + gx_max) * 0.5, 1),
            "pmap_game_center_y": round((gy_min + gy_max) * 0.5, 1),
            "player_gx":         round(px, 1),  "player_gy": round(py, 1),
            "player_icon_x":     round(plr_ix, 3), "player_icon_y": round(plr_iy, 3),
            "offset_dx":         _PMAP_OFFSETS.get(map_id, (0.0, 0.0))[0],
            "offset_dy":         _PMAP_OFFSETS.get(map_id, (0.0, 0.0))[1],
        }

        # Load existing file
        if os.path.isfile(_OFFSET_FILE):
            with open(_OFFSET_FILE, "r", encoding="utf-8-sig") as fh:
                data = json.load(fh)
        else:
            data = {"offsets": {}, "calibration": {}}

        data.setdefault("offsets",     {})
        data.setdefault("calibration", {})
        data["calibration"][str(map_id)] = record

        with open(_OFFSET_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

        Py4GW.Console.Log(MODULE_NAME,
            f"Calibration saved for [{map_id}] {name}  "
            f"player=({px:.0f},{py:.0f}) icon=({plr_ix:.1f},{plr_iy:.1f})",
            Py4GW.Console.MessageType.Info)

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Calibration error: {e}",
                          Py4GW.Console.MessageType.Warning)
