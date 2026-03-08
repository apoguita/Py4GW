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
from collections import defaultdict

from Py4GWCoreLib import Map, Utils, Player, AutoPathing, GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.native_src.methods.MapMethods import MapMethods
from Py4GWCoreLib.native_src.methods.FfnaMapMethods import FfnaMapMethods
from Py4GWCoreLib.Overlay import Overlay as _Overlay
import PyOverlay

_overlay3d = _Overlay()

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
# Loaded from JSON at startup: map_id -> [dx_icon, dy_icon]
_PMAP_OFFSETS:  dict[int, tuple[float, float]] = {}
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

def _traps_to_icon(trapezoids: list, ix1: float, iy1: float, ix2: float, iy2: float,
                   offset: tuple[float, float] = (0.0, 0.0)
                   ) -> list[tuple]:
    """Convert trapezoid list to icon-space quads.  Returns [] if bounds are degenerate."""
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
    """Rebuild _PORTAL_ALL_DATA from DAT portals, live cache and portal_links metadata."""
    global _PORTAL_ALL_DATA
    rebuilt: dict[int, list[dict]] = {}

    for mid, bnd in _ICON_BOUNDS.items():
        if bnd is None:
            continue
        by_index: dict[int, dict] = {}

        # 1) Offline DAT portals (or live-cached fallback)
        portals = []
        try:
            portals = FfnaMapMethods.GetTravelPortalsForMap(mid)
        except Exception:
            portals = []
        if not portals and mid in _live_portal_cache:
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
    debug_map = False

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
                )
            else:
                coord_preview.append(f"portal_id={gid} icon({ix:.1f},{iy:.1f})")
        coord_suffix = "" if len(dots) <= 8 else f" ...(+{len(dots) - 8})"
        Py4GW.Console.Log(MODULE_NAME,
            (f"Map {map_id} portal debug [{stage}] src={'live' if is_live else 'dat'} "
             f"raw_portals={portals_count} dots={len(dots)} gids={sample}{suffix} "
             f"coords={coord_preview}{coord_suffix}"),
            Py4GW.Console.MessageType.Info)

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
    if (not is_live) or (not portals):
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
                for pm in pathing_maps:
                    for trap in pm.trapezoids:
                        for x in (trap.XTL, trap.XTR, trap.XBL, trap.XBR):
                            if x < gx_min2: gx_min2 = x
                            if x > gx_max2: gx_max2 = x
                        for y in (trap.YT, trap.YB):
                            if y < gy_min2: gy_min2 = y
                            if y > gy_max2: gy_max2 = y
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
                _debug_log("portal-all-data", len(specs), dots_all)
                return

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
        _debug_log("fallback-invalid-pathing-extents", len(portals), dots)
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
    _debug_log("normal", len(portals), dots)
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


def _build_cache() -> None:
    """Scan all map IDs and populate _ICON_BOUNDS / _MAP_META.  Called once."""
    global _cache_built
    for mid in range(1, _MAX_MAP_ID + 1):
        info = MapMethods.GetMapInfo(mid)
        if info is None:
            _ICON_BOUNDS[mid] = None
            continue

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

        try:
            name = Map.GetMapName(mid) or f"Map {mid}"
        except Exception:
            name = f"Map {mid}"
        _MAP_META[mid] = (int(info.type), name, int(info.campaign))

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

    _cache_built = True
    n = sum(1 for v in _ICON_BOUNDS.values() if v is not None)
    g = len(_DRAW_GROUPS)
    Py4GW.Console.Log(MODULE_NAME,
        f"Cache built: {n} maps, {g} draw groups.",
        Py4GW.Console.MessageType.Info)
    _load_portal_destinations()   # also calls _load_portal_links() at the end
    _load_portal_all_data()
    linked_maps = {int(gid // 1000) for gid in _PORTAL_LINKS.keys()}
    missing_linked = [mid for mid in linked_maps if mid not in _PORTAL_ALL_DATA]
    if (not _PORTAL_ALL_DATA) or missing_linked:
        _rebuild_portal_all_data()


# ── Region type → packed color ──────────────────────────────────────────────
def _type_fill(rtype: int, alpha: int) -> int:
    if rtype == _RT_EXPLORABLE:                               return Utils.RGBToColor( 50, 190,  80, alpha)
    if rtype in (_RT_OUTPOST, _RT_TOWN, _RT_CITY):           return Utils.RGBToColor( 70, 130, 245, alpha)
    if rtype in (_RT_MISSION_OUT, _RT_COOP):                 return Utils.RGBToColor( 50, 200, 200, alpha)
    if rtype in (_RT_CHALLENGE, _RT_COMPETITIVE, _RT_ELITE): return Utils.RGBToColor(245, 150,  50, alpha)
    if rtype == _RT_HERO_BATTLE:                             return Utils.RGBToColor(200,  80, 255, alpha)
    return Utils.RGBToColor(150, 150, 150, alpha)


def _type_border(rtype: int, alpha: int) -> int:
    if rtype == _RT_EXPLORABLE:                               return Utils.RGBToColor( 90, 230, 120, alpha)
    if rtype in (_RT_OUTPOST, _RT_TOWN, _RT_CITY):           return Utils.RGBToColor(130, 170, 255, alpha)
    if rtype in (_RT_MISSION_OUT, _RT_COOP):                 return Utils.RGBToColor( 90, 230, 230, alpha)
    if rtype in (_RT_CHALLENGE, _RT_COMPETITIVE, _RT_ELITE): return Utils.RGBToColor(255, 190,  90, alpha)
    return Utils.RGBToColor(190, 190, 190, alpha)


# ── UI state ──────────────────────────────────────────────────────────────────
_show_frames         = [True]
_show_other          = [False]
_show_pmap_current   = [False]
_show_pmap_all       = [False]
_pmap_opacity        = [0.2]
_show_portals        = [True]
_show_portals_3d     = [True]
_show_portal_ids     = [True]
_show_labels         = [True]
_opacity             = [0.75]
_show_debug          = [False]
_show_player_cross        = [False]
_show_reachable_unvisited = [False]

# Travel button data: built each frame by _draw_overlay, consumed by _draw_travel_buttons
# Each entry: (rep_map_id, btn_x, btn_y)  – screen pixel coords
_travel_btn_data: list[tuple[int, float, float]] = []
_travel_btn_seen:  set[int] = set()   # dedup by map_id

# UI state for link editor
_link_input_a    = [0]
_link_input_b    = [0]
_link_click_mode  = [False]  # click-to-link mode active
_link_pending_gid = [0]     # first selected portal GID (waiting for second click)
_moveto_portal_id = [0]     # portal ID entered for Move To

# ── Route path state (driven by travel buttons / MoveToMapid) ────────────────
_path_gids:       list[int] = []   # ordered GID sequence: [exit1,enter1,exit2,enter2,...]
_path_map_names:  list[str] = []   # map name steps for display

# Cache for IsPath(current_map, target) – invalidated on map change
_is_path_cache: dict[int, bool] = {}  # key = target map_id

# Tracks the last map for which 3D portal labels were built live
_portal_3d_last_map: list[int] = [-1]

# Timing state for the active travel route
_travel_route_start_ms:   list[int] = [0]                    # timestamp when route started
_travel_hop_times:        list[tuple[int, int]] = []         # [(start_ms, end_ms|0), ...] per hop; end_ms=0 = still running
_travel_prev_done_count:  list[int] = [-1]                   # done_count from previous frame


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


def _mtm_log_debug(message: str) -> None:
    if not _show_debug[0]:
        return
    Py4GW.Console.Log(
        MODULE_NAME,
        f"[MoveToMapid] {message}",
        Py4GW.Console.MessageType.Info,
    )


_PMAP_GAME_BOUNDS: dict[int, tuple[float, float, float, float]] = {}


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
        _PMAP_GAME_BOUNDS[map_id] = (gx_min, gx_max, gy_min, gy_max)
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

    try:
        pathing_maps = Map.Pathing.GetPathingMaps()
    except Exception:
        return []
    if not pathing_maps:
        return []

    gx_min = float('inf'); gx_max = float('-inf')
    gy_min = float('inf'); gy_max = float('-inf')
    for pm in pathing_maps:
        for trap in pm.trapezoids:
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

    out: list[tuple[float, float]] = []
    for gx, gy in _mtnw_path:
        pix = ix1 + (gx - gx_min) / gw * iw_map
        piy = iy1 + (gy_max - gy) / gh * ih_map
        out.append((pix, piy))
    return out


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
    for wp in result["waypoints"]:
        exit_xy  = _get_portal_icon_xy(wp["exit_gid"])
        enter_xy = _get_portal_icon_xy(wp["enter_gid"])
        segs.append({
            "from_map":  wp["from_map"],
            "to_map":    wp["to_map"],
            "exit_ix":   exit_xy[0]  if exit_xy  else None,
            "exit_iy":   exit_xy[1]  if exit_xy  else None,
            "enter_ix":  enter_xy[0] if enter_xy else None,
            "enter_iy":  enter_xy[1] if enter_xy else None,
        })
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


_reachable_adj_cache: dict[int, set[int]] | None = None
_reachable_list_cache: list[dict] = []
_reachable_list_last_map: list[int] = [-1]

def _path_distance(start_map: int, end_map: int) -> float | None:
    """Game-unit path distance between two maps. Delegates to WorldPathing."""
    return _wp_path_distance(start_map, end_map)


def _build_reachable_adj() -> dict[int, set[int]]:
    """Delegates to WorldPathing._build_world_adj()."""
    return _wp_get_world_adj()


def _get_reachable_adj() -> dict[int, set[int]]:
    """Return cached combined adjacency. Delegates to WorldPathing.get_world_adj()."""
    return _wp_get_world_adj()


def invalidate_reachable_adj() -> None:
    """Call this whenever portal links change so the combined adj is rebuilt."""
    global _reachable_adj_cache
    _reachable_adj_cache = None
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


def GetNearestUnlockedOutpost(target_map_id: int) -> dict | None:
    """Return the nearest unlocked non-explorable map to target_map_id.

    Delegates to WorldPathing.GetNearestUnlockedOutpost — see that function for
    full documentation.  Available here so widget-local code can call it without
    importing WorldPathing directly.

    Return value:
      { "map_id": int, "name": str, "hops": int, "distance": float | None }
    or None if no unlocked outpost is reachable.
    """
    return _WP_GetNearestUnlockedOutpost(target_map_id)


def GetNearestFastTravelTo(target_map_id: int) -> dict | None:
    """Convenience alias for GetNearestUnlockedOutpost(target_map_id).

    Kept for backwards-compatibility and readability in travel-UI code.
    """
    return GetNearestUnlockedOutpost(target_map_id)


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


def _should_show(rtype: int) -> bool:
    if rtype in (_RT_EXPLORABLE, _RT_OUTPOST, _RT_TOWN, _RT_CITY,
                 _RT_MISSION_OUT, _RT_COOP, _RT_CHALLENGE, _RT_COMPETITIVE, _RT_ELITE):
        return _show_frames[0]
    return _show_other[0]


# ── World-map overlay draw ─────────────────────────────────────────────────────

_PORTAL_3D_LABEL_RADIUS = 1000.0  # kept for reference, no longer used as filter


def _draw_portal_ids_3d() -> None:
    """Draw portal GIDs as 3D world-space labels near the player."""
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

    # Determine current campaign group for optional filtering
    current_camp_group = -1
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
        # Non-standard (Other/PvP) types are fully skipped when _show_other is off.
        # Standard types are always processed so buttons/labels appear even when frames are off.
        if not is_standard_type and not _show_other[0]:
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

        # Cull: skip if completely outside the visible screen rect
        if x2 < sl or x1 > sr or y2 < st or y1 > sb:
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
        if not is_current and rw >= 28.0 and (y2 - y1) >= 14.0:
            for i, mid in enumerate(sorted_ids):
                if mid == current_map or mid in _travel_btn_seen:
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
                raw     = f"{line} [{mid}]" if mid >= 0 else line
                has_btn = mid in btn_ids_here
                if frames_on:
                    lbl_x = x1 + 20.0 if has_btn else x1 + 2.0
                else:
                    raw_w   = len(raw) * 6.5
                    total_w = (20.0 + raw_w) if has_btn else raw_w
                    lbl_x   = cx - total_w * 0.5 + (20.0 if has_btn else 0.0)
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
    if _show_pmap_current[0] or _show_pmap_all[0]:
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
    if _show_portals[0]:
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
        visible_portal_sx: dict[int, tuple[float, float]] = {}  # global_id -> (sx, sy)

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
            for pix, piy, _dest, _local_idx, gid, *_gc in _PORTAL_ICON_POS.get(mid, []):
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

        # ── Pass 4: draw computed portal path ──────────────────────────────
        if _path_gids:
            path_line_col  = Utils.RGBToColor( 50, 220, 255, 220)
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

            # Draw segments between consecutive GIDs
            for seg_idx in range(len(_path_gids) - 1):
                gid_a = _path_gids[seg_idx]
                gid_b = _path_gids[seg_idx + 1]
                pa_ix = path_icon.get(gid_a)
                pb_ix = path_icon.get(gid_b)
                if pa_ix is None or pb_ix is None:
                    continue
                sa = _i2s(pa_ix[0], pa_ix[1])
                sb = _i2s(pb_ix[0], pb_ix[1])
                if seg_idx < first_pending:
                    PyImGui.draw_list_add_line(sa[0], sa[1], sb[0], sb[1], path_done_col, 1.5)
                else:
                    PyImGui.draw_list_add_line(sa[0], sa[1], sb[0], sb[1], path_line_col, 2.5)

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

        # ── Pass 5: draw MoveToNextWaypoint local AutoPathing path ──────────
        if _mtnw_path:
            mtnw_icon = _mtnw_path_icon_points(current_map)
            if len(mtnw_icon) >= 2:
                mtnw_line_col = Utils.RGBToColor(255, 110, 255, 230)
                mtnw_dot_col  = Utils.RGBToColor(255, 220, 255, 235)
                mtnw_cur_col  = Utils.RGBToColor(255, 255, 120, 255)

                # Polyline
                for i in range(len(mtnw_icon) - 1):
                    a = _i2s(mtnw_icon[i][0], mtnw_icon[i][1])
                    b = _i2s(mtnw_icon[i + 1][0], mtnw_icon[i + 1][1])
                    PyImGui.draw_list_add_line(a[0], a[1], b[0], b[1], mtnw_line_col, 2.0)

                # Sparse waypoint dots
                step = 3 if len(mtnw_icon) > 30 else 1
                for i in range(0, len(mtnw_icon), step):
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
    if _show_player_cross[0]:
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

    segments: list[tuple] = []
    for seg in overlay:
        ex = (i2s(seg["exit_ix"],  seg["exit_iy"])  if seg["exit_ix"]  is not None else None)
        en = (i2s(seg["enter_ix"], seg["enter_iy"]) if seg["enter_ix"] is not None else None)
        segments.append((ex, en))

    prev_ex: tuple | None = None
    for ex, en in segments:
        if draw_link and prev_ex is not None and en is not None:
            PyImGui.draw_list_add_line(prev_ex[0], prev_ex[1], en[0], en[1], col_link, 1.5)
        if en is not None and ex is not None:
            PyImGui.draw_list_add_line(en[0], en[1], ex[0], ex[1], col_trav, 2.0)
        prev_ex = ex

    for i, (ex, en) in enumerate(segments):
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
    btn_col         = (0.10, 0.55, 0.15, 0.88)
    btn_col_hovered = (0.15, 0.75, 0.22, 0.95)
    btn_col_active  = (0.20, 0.90, 0.28, 1.00)

    for rep_id, btn_x, btn_y in _travel_btn_data:
        if rep_id not in _is_path_cache:
            _is_path_cache[rep_id] = IsPath(current_map, rep_id)
        if not _is_path_cache[rep_id]:
            continue

        PyImGui.set_next_window_pos(btn_x, btn_y)
        PyImGui.set_next_window_size(btn_w + 2.0, btn_h + 2.0)
        if not PyImGui.begin(f"##wm_travel_{rep_id}", btn_flags):
            PyImGui.end()
            continue

        PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        btn_col)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, btn_col_hovered)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  btn_col_active)
        PyImGui.set_cursor_pos(0.0, 0.0)
        if PyImGui.button(f"##t{rep_id}", btn_w, btn_h):
            route = GetPath(current_map, rep_id)
            if route.get("found"):
                _travel_route_overlay[:] = _build_route_overlay(route)
                _path_map_names[:] = route.get("map_names", [])
                gids: list[int] = []
                for wp in route.get("waypoints", []):
                    gids.extend([wp["exit_gid"], wp["enter_gid"]])
                _path_gids[:] = gids
                # Initialise hop timers
                _now = int(Utils.GetBaseTimestamp())
                _num_hops = max(0, len(_path_map_names) - 1)
                _travel_route_start_ms[0] = _now
                _travel_hop_times[:] = [(_now, 0)] + [(0, 0)] * (_num_hops - 1)
                _travel_prev_done_count[0] = 0
            else:
                _travel_route_overlay.clear()
                _path_gids.clear()
                _path_map_names.clear()
                _travel_route_start_ms[0] = 0
                _travel_hop_times.clear()
                _travel_prev_done_count[0] = -1
            MoveToMapid(rep_id)
        PyImGui.pop_style_color(3)

        if PyImGui.is_item_hovered():
            meta = _MAP_META.get(rep_id)
            name = meta[1] if meta else f"Map {rep_id}"
            PyImGui.begin_tooltip()
            PyImGui.text(f"Travel to: {name}")
            PyImGui.end_tooltip()

        PyImGui.end()


def _draw_travel_roadmap() -> None:
    """Right-side panel showing the active inter-map travel route as a roadmap."""
    if not Map.WorldMap.IsWindowOpen():
        return
    # Only show when a route is active or route data is present
    if not _path_map_names and not _mtm_runner_active[0]:
        _pathfinder_win_h[0] = 0.0
        return

    fi = Map.WorldMap.GetFrameInfo()
    if fi is None:
        return
    sc = fi.GetContentCoords()
    if not sc:
        return
    sr, st = float(sc[2]), float(sc[1])

    win_w  = 210.0
    margin = 8.0

    panel_flags = (
        PyImGui.WindowFlags.NoTitleBar        |
        PyImGui.WindowFlags.NoResize          |
        PyImGui.WindowFlags.NoMove            |
        PyImGui.WindowFlags.NoScrollbar       |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.NoCollapse        |
        PyImGui.WindowFlags.AlwaysAutoResize  |
        PyImGui.WindowFlags.NoSavedSettings
    )
    PyImGui.set_next_window_pos(sr - win_w - margin, st + margin)
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

        # Show elapsed time for the hop that departs from names[i] (hop index = i)
        time_str = ""
        hop_idx = i
        if 0 <= hop_idx < len(_travel_hop_times):
            ht_s, ht_e = _travel_hop_times[hop_idx]
            if ht_e != 0:
                elapsed = (ht_e - ht_s) / 1000.0
                time_str = f"  ({elapsed:.0f}s)"
            elif ht_s > 0:
                elapsed = (now_ms - ht_s) / 1000.0
                time_str = f"  ({elapsed:.0f}s...)"

        label = f"{prefix}{step}{time_str}"
        if i == 0 and current_map == (route.get("maps", [0])[0] if route else 0):
            col = cur_col
        elif i < done_count:
            col = done_col
        elif is_last:
            col = dst_col
        else:
            col = pend_col
        PyImGui.draw_list_add_text(sx2, sy2, col, label)

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
        _travel_route_overlay.clear()
        _path_gids.clear()
        _path_map_names.clear()
        _travel_route_start_ms[0] = 0
        _travel_hop_times.clear()
        _travel_prev_done_count[0] = -1
    PyImGui.pop_style_color(3)

    _pathfinder_win_h[0] = PyImGui.get_window_height()
    PyImGui.end()


# ── WorldPathing API demo panel ───────────────────────────────────────────────

def _draw_worldpathing_demo() -> None:
    """Right-side panel for live testing of IsPath / GetPath / MoveToNextWaypoint."""
    if not _show_wp_demo[0]:
        return
    if not Map.WorldMap.IsWindowOpen():
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

    panel_flags = (
        PyImGui.WindowFlags.NoTitleBar        |
        PyImGui.WindowFlags.NoResize          |
        PyImGui.WindowFlags.NoMove            |
        PyImGui.WindowFlags.NoScrollbar       |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.NoCollapse        |
        PyImGui.WindowFlags.AlwaysAutoResize  |
        PyImGui.WindowFlags.NoSavedSettings
    )
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
    _show_frames[0]      = PyImGui.checkbox("Draw all Frames##wmp",   _show_frames[0])
    _show_portals[0]     = PyImGui.checkbox("Draw Portals##wmp",    _show_portals[0])
    if _show_portals[0]:
        _show_portals_3d[0] = PyImGui.checkbox("  Draw 3D Portals##wmp", _show_portals_3d[0])
        _show_portal_ids[0] = PyImGui.checkbox("  Show Portal IDs##wmp",  _show_portal_ids[0])
    #_show_other[0]       = PyImGui.checkbox("Other / PvP##wmp",   _show_other[0])
    _show_pmap_current[0] = PyImGui.checkbox("Navmap Current Map##wmp", _show_pmap_current[0])
    _show_pmap_all[0]     = PyImGui.checkbox("Navmap All##wmp",         _show_pmap_all[0])
    if _show_pmap_current[0] or _show_pmap_all[0]:
        _pmap_opacity[0] = PyImGui.slider_float("Navmap opacity##wmp", _pmap_opacity[0], 0.01, 1.0)
    _show_player_cross[0] = PyImGui.checkbox("Player position##wmp", _show_player_cross[0])
    _show_reachable_unvisited[0] = PyImGui.checkbox(
        "  Reachable (not visited)##wmp", _show_reachable_unvisited[0])
    PyImGui.pop_item_width()

    PyImGui.separator()
    _show_wp_demo[0] = PyImGui.checkbox("WorldPathing Demo##wmp", _show_wp_demo[0])
    _show_debug[0] = PyImGui.checkbox("Diagnostics##wmp", _show_debug[0])
    if _show_debug[0]:
        _draw_diagnostics()


def _draw_reachable_list_panel() -> None:
    """Floating panel listing reachable-but-unvisited outposts, shown when the checkbox is active."""
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
        for m in GetReachableMaps(cmap):
            if Map.IsMapUnlocked(m["map_id"]):
                continue
            meta = _MAP_META.get(m["map_id"])
            if meta is None or meta[0] == _RT_EXPLORABLE:
                continue
            dist  = _path_distance(cmap, m["map_id"])
            ft    = GetNearestFastTravelTo(m["map_id"])
            entry = dict(m)
            entry["distance"] = dist
            entry["nearest_ft"] = ft
            _reachable_list_cache.append(entry)
        _reachable_list_cache.sort(key=lambda e: (
            e["distance"] if e["distance"] is not None else float("inf"),
            e["hops"],
            e["name"]
        ))
    rv_list = _reachable_list_cache

    panel_flags = (
        PyImGui.WindowFlags.NoTitleBar        |
        PyImGui.WindowFlags.NoResize          |
        PyImGui.WindowFlags.NoMove            |
        PyImGui.WindowFlags.NoScrollbar       |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.NoCollapse        |
        PyImGui.WindowFlags.AlwaysAutoResize  |
        PyImGui.WindowFlags.NoSavedSettings
    )
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

    if not rv_list:
        PyImGui.text_disabled("None found from current map.")
    else:
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


def _draw_portal_link_editor() -> None:
    """Dedicated panel for portal linking, positioned right of the legend panel."""
    if not Map.WorldMap.IsWindowOpen() or not _show_debug[0] or not _show_portals[0]:
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

    panel_flags = (
        PyImGui.WindowFlags.NoTitleBar        |
        PyImGui.WindowFlags.NoResize          |
        PyImGui.WindowFlags.NoMove            |
        PyImGui.WindowFlags.NoScrollbar       |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.NoCollapse        |
        PyImGui.WindowFlags.AlwaysAutoResize  |
        PyImGui.WindowFlags.NoSavedSettings
    )

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
            _debug_last_map[0] = cmap
            # Only wipe route data when no runner is active.
            # While the bot is travelling, the route must stay visible.
            if not _mtm_runner_active[0] and not _mtnw_runner_active[0]:
                _travel_route_overlay.clear()
                _path_gids.clear()
                _path_map_names.clear()
                _travel_route_start_ms[0] = 0
                _travel_hop_times.clear()
                _travel_prev_done_count[0] = -1

            # Reset demo results when map changes
            _wp_is_path_result[0]  = None
            _wp_get_path_found[0]  = False
            _wp_get_path_maps.clear()
            _wp_get_path_result.clear()
            _wp_get_path_full[0]   = None
            _wp_move_result[0]     = None
            _wp_move_map_result[0] = None

        _draw_overlay()
        _draw_travel_buttons()
        _draw_legend()
        _draw_reachable_list_panel()
        _draw_portal_link_editor()
        _draw_travel_roadmap()
        _draw_worldpathing_demo()
        _draw_portal_ids_3d()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"{e}\n{traceback.format_exc()}",
                          Py4GW.Console.MessageType.Error)


if __name__ == "__main__":
    main()
