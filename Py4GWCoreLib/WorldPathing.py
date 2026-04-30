"""
WorldPathing
============
Bot-usable pathing / routing layer for Guild Wars.

Public API (usable from any bot, no WorldMap+ required):
  IsPath(start, target)            -> bool
  GetPath(start, target)           -> dict
  MoveToNextWaypoint(target, path) -> bool
  MoveToMapid(target)              -> bool
  MoveToMapID(target)              -> bool  (alias)
  GetNearestUnlockedOutpost(map)   -> dict | None
  get_world_adj()                  -> dict[int, set[int]]
  path_distance(start, end)        -> float | None
  invalidate_world_adj()           -> None

Call configure(script_dir) once at startup to point at the JSON data folder
(portal_links.json).
"""

import Py4GW
import json
import os
import math
from collections import deque

from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.native_src.methods.MapMethods import MapMethods
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

MODULE_NAME = "WorldPathing"


class WorldPathing:
    """Singleton that manages inter-map routing and autonomous map travel."""

    _instance = None

    # ── Class-level static data (shared across all callers) ────────────────────

    # Hardcoded walkable-portal adjacency graph.
    _MAP_ADJACENCY: dict[int, set[int]] = {
        # ── EotN: Norn region ──────────────────────────────────────────────────
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
        # ── EotN: Asura region ─────────────────────────────────────────────────
        572: {642, 558, 566, 501},
        558: {572, 566, 501, 569},
        501: {572, 558, 569},
        566: {572, 558},
        569: {558, 501},
        594: {572, 558},
        595: {501, 572},
        596: {566, 572},
        598: {569, 558},
        # ── Nightfall: Istan region ────────────────────────────────────────────
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
        # ── Nightfall: Kourna region ───────────────────────────────────────────
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
        # ── Nightfall: Vabbi region ────────────────────────────────────────────
        395: {394, 397, 399, 406},
        397: {392, 394, 395, 399, 402},
        399: {395, 397, 402, 404, 406},
        402: {394, 397, 399, 406},
        404: {392, 399},
        406: {395, 399, 402},
        # ── Prophecies: Kryta ──────────────────────────────────────────────────
        58:  {59, 62, 63, 64},
        59:  {58, 60, 61},
        60:  {59, 61, 64},
        61:  {59, 60, 63},
        62:  {58, 63},
        63:  {58, 61, 62, 64},
        64:  {58, 60, 63},
        # ── Factions: Shing Jea ────────────────────────────────────────────────
        235: {236, 237, 238},
        236: {235, 237, 246},
        237: {235, 236, 238},
        238: {235, 237},
    }

    # Will be set to True after bidirectional edges + _ALL_EDGES are built once.
    _ADJACENCY_READY = False

    # Deduplicated edge set (each pair stored once as (min, max)).
    _ALL_EDGES: set[tuple[int, int]] = set()

    # Map metadata: map_id -> (type:int, name:str, campaign:int)
    # Populated by WorldMap+._build_cache() on startup.
    _MAP_META: dict[int, tuple[int, str, int]] = {}

    # Region-type constant (matches WorldMap+ widget).
    _RT_EXPLORABLE = 2

    # ──────────────────────────────────────────────────────────────────────────

    def __new__(cls) -> "WorldPathing":
        if cls._instance is None:
            cls._instance = super(WorldPathing, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        # Build bidirectional adjacency and edge set exactly once.
        if not WorldPathing._ADJACENCY_READY:
            for _src, _dsts in list(WorldPathing._MAP_ADJACENCY.items()):
                for _dst in _dsts:
                    WorldPathing._MAP_ADJACENCY.setdefault(_dst, set()).add(_src)
            for _a, _bs in WorldPathing._MAP_ADJACENCY.items():
                for _b in _bs:
                    WorldPathing._ALL_EDGES.add((min(_a, _b), max(_a, _b)))
            WorldPathing._ADJACENCY_READY = True

        # ── Per-instance portal data ───────────────────────────────────────────
        self.portal_links_file: str = ""
        #   global_id -> linked global_id
        self.portal_links:        dict[int, int]                 = {}
        #   global_id -> (game_x, game_y)
        self.portal_game_pos:     dict[int, tuple[float, float]] = {}
        #   global_id -> (map_id, local_index)
        self.global_id_to_portal: dict[int, tuple[int, int]]     = {}
        #   (map_id, local_index) -> global_id
        self.portal_to_global_id: dict[tuple[int, int], int]     = {}

        self._portal_adj_cache: dict | None = None
        self._world_adj_cache:  dict | None = None

        # ── Movement constants ─────────────────────────────────────────────────
        self.MTNW_ARRIVAL_RADIUS         = 200.0
        self.MTNW_WAYPOINT_RADIUS        = 140.0
        self.MTNW_PUSHTHROUGH_TIMEOUT_MS = 6000
        self.MTNW_NUDGE_STEP             = 200.0   # units per forward nudge after pushthrough timeout
        self.MTNW_NUDGE_MAX_STEPS        = 5        # max forward nudges before giving up
        self.MTM_HOP_MAX_ATTEMPTS        = 6
        self.MTM_HOP_TIMEOUT_MS          = 120_000
        self.MTM_LOAD_TIMEOUT_MS         = 60_000
        self.WP_HEARTBEAT_TIMEOUT_MS     = 2_500

        self._instance_token: str = (
            f"wp-{Utils.GetBaseTimestamp()}-{id(object())}"
        )

        # ── MoveToNextWaypoint state ───────────────────────────────────────────
        self.mtnw_goal_xy:        list[tuple[float, float] | None] = [None]
        self.mtnw_target_map:     list[int]  = [0]
        self.mtnw_path:           list[tuple[float, float]]        = []
        self.mtnw_path_index:     list[int]  = [0]
        self.mtnw_path_following: list[bool] = [False]
        self.mtnw_path_computing: list[bool] = [False]
        self.mtnw_runner_active:  list[bool] = [False]
        self.mtnw_job_id:         list[int]  = [0]
        self.mtnw_paused_danger:  list[bool] = [False]
        # Active BottingTree move tree (set during coroutine; None when idle).
        self.mtnw_bt_tree: "BehaviorTree | None" = None
        # Pause-on-danger configuration
        self.mtnw_pause_on_danger: bool  = True
        self.mtnw_danger_radius:   float = float(Range.Earshot.value)

        # ── MoveToMapid state ──────────────────────────────────────────────────
        self.mtm_runner_active: list[bool]        = [False]
        self.mtm_target_map:    list[int]         = [0]
        self.mtm_route:         list[dict | None] = [None]
        self.mtm_job_id:        list[int]         = [0]

        self._initialized = True

        # Register heartbeat so stale module instances are invalidated on import.
        self._set_runtime_heartbeat()

    # ── Configuration ──────────────────────────────────────────────────────────

    def configure(self, script_dir: str) -> None:
        """Set the portal_links.json path and load the data.
        Must be called once before GetPath / IsPath / MoveToMapid."""
        self.portal_links_file = os.path.join(script_dir, "portal_links.json")
        self._load_portal_links()

    # ── Portal adjacency ───────────────────────────────────────────────────────

    def invalidate_portal_adj(self) -> None:
        """Mark adjacency caches as stale.  Call whenever portal_links changes."""
        self._portal_adj_cache = None
        self._world_adj_cache  = None

    def _get_portal_adj(self) -> dict[int, list[tuple[int, int, int]]]:
        """Return (cached) adjacency dict built from portal_links."""
        if self._portal_adj_cache is not None:
            return self._portal_adj_cache
        adj: dict[int, list[tuple[int, int, int]]] = {}
        seen: set[tuple[int, int]] = set()
        for gid_a, gid_b in self.portal_links.items():
            pair = (min(gid_a, gid_b), max(gid_a, gid_b))
            if pair in seen:
                continue
            seen.add(pair)
            ka = self.global_id_to_portal.get(gid_a)
            kb = self.global_id_to_portal.get(gid_b)
            map_a = ka[0] if ka else gid_a // 1000
            map_b = kb[0] if kb else gid_b // 1000
            adj.setdefault(map_a, []).append((gid_a, gid_b, map_b))
            adj.setdefault(map_b, []).append((gid_b, gid_a, map_a))
        self._portal_adj_cache = adj
        return adj

    # ── Combined adjacency (static graph + portal links) ──────────────────────

    def _build_world_adj(self) -> dict[int, set[int]]:
        """Merge _MAP_ADJACENCY (static) + portal adjacency (portal_links.json)."""
        combined: dict[int, set[int]] = {}
        for m, neighbours in WorldPathing._MAP_ADJACENCY.items():
            combined.setdefault(m, set()).update(neighbours)
            for nb in neighbours:
                combined.setdefault(nb, set()).add(m)
        for m, edges in self._get_portal_adj().items():
            for _eg, _en, nb in edges:
                combined.setdefault(m, set()).add(nb)
                combined.setdefault(nb, set()).add(m)
        return combined

    def get_world_adj(self) -> dict[int, set[int]]:
        """Return cached combined adjacency; rebuilt when invalidate_world_adj() is called."""
        if self._world_adj_cache is None:
            self._world_adj_cache = self._build_world_adj()
        return self._world_adj_cache

    def invalidate_world_adj(self) -> None:
        """Invalidate the combined adjacency cache."""
        self._world_adj_cache = None

    # ── Path queries ───────────────────────────────────────────────────────────

    def path_distance(self, start_map: int, end_map: int) -> float | None:
        """BFS from start_map to end_map; returns summed game-unit distance along
        the route portals, or None when coordinates are unavailable."""
        combined = self.get_world_adj()
        if start_map not in combined or end_map not in combined:
            return None
        if start_map == end_map:
            return 0.0

        portal_adj = self._get_portal_adj()
        gid_map: dict[int, dict[int, tuple[int, int]]] = {}
        for m, edges in portal_adj.items():
            for eg, ig, nb in edges:
                gid_map.setdefault(m, {})[nb] = (eg, ig)

        queue: deque = deque([(start_map, [])])
        visited: set[int] = {start_map}
        while queue:
            cur, path = queue.popleft()
            for nb in combined.get(cur, set()):
                if nb in visited:
                    continue
                edge     = gid_map.get(cur, {}).get(nb)
                new_path = path + [(cur, nb, edge)]
                if nb == end_map:
                    # Direct adjacency (1 hop, no intermediate map to measure through):
                    # the player is at the portal entrance — cost is essentially zero.
                    if len(new_path) == 1:
                        return 0.0
                    total       = 0.0
                    has_coords  = False
                    prev_enter: int | None = None
                    for _src, _dst, e in new_path:
                        exit_gid  = e[0] if e else None
                        enter_gid = e[1] if e else None
                        if prev_enter is not None and exit_gid is not None:
                            # Use _get_portal_game_xy so that live coords from
                            # _PORTAL_ICON_POS_EXT (WorldMap+ tp.x/tp.y entries) are
                            # consulted as fallback, not just portal_links.json.
                            pa = self._get_portal_game_xy(prev_enter)
                            pb = self._get_portal_game_xy(exit_gid)
                            if pa and pb:
                                total += math.hypot(pb[0] - pa[0], pb[1] - pa[1])
                                has_coords = True
                        prev_enter = enter_gid
                    return round(total) if has_coords else None
                visited.add(nb)
                queue.append((nb, new_path))
        return None

    def GetNearestUnlockedOutpost(
        self,
        target_map_id: int,
        from_map_id: int | None = None,
    ) -> dict | None:
        """Return the best unlocked non-explorable outpost to fast-travel to
        in order to reach *target_map_id* on foot after the FT.

        Fast-travel is always instant (zero travel time) so the player's
        current location is irrelevant for the primary ranking.  The only
        metric that matters is: after FT'ing to this outpost, how far do I
        still need to walk to reach the target?

        Ranking (ascending = better):
          1. hops_to_target   – BFS portal-hop count from outpost to target
          2. walk_distance    – game-unit walking distance (path_distance);
                                0.0 is returned for direct 1-hop neighbours,
                                so within the 1-hop tier use icon_distance as
                                tiebreaker (geographic outpost→target dist)
          3. icon_distance    – Euclidean distance between map icon centres
                                (available when _ICON_BOUNDS is set via EXT)
          4. map_id           – deterministic fallback

        The *from_map_id* parameter is ignored for ranking (FT is free) but
        is kept for API compatibility.

        Return value:
          { "map_id": int, "name": str, "hops": int, "distance": float | None }
        or None when no unlocked outpost is reachable.
        """
        combined = self.get_world_adj()
        if target_map_id not in combined:
            return None

        # ── Special case: target itself is an unlocked outpost ────────────────
        meta0 = WorldPathing._MAP_META.get(target_map_id)
        if (meta0
                and meta0[0] != WorldPathing._RT_EXPLORABLE
                and Map.IsMapUnlocked(target_map_id)):
            return {
                "map_id":   target_map_id,
                "name":     meta0[1],
                "hops":     0,
                "distance": 0.0,
            }

        # ── Build portal-only adjacency set for the hop-distance BFS ─────────
        # Using portal_adj (not the broader world_adj) ensures the hop count
        # matches the actual portal-linked route that MoveToMapid will walk.
        # Candidates reachable only via static _MAP_ADJACENCY (no portal links)
        # are naturally excluded, making the IsPath filter redundant.
        portal_adj_raw = self._get_portal_adj()
        portal_sets: dict[int, set[int]] = {}
        for m, edges in portal_adj_raw.items():
            for _, _, nb in edges:
                portal_sets.setdefault(m, set()).add(nb)
                portal_sets.setdefault(nb, set()).add(m)

        # ── BFS from target → portal-hop distance to every map ───────────────
        hops_to_target: dict[int, int] = {target_map_id: 0}
        bfs_q: deque = deque([(target_map_id, 0)])
        while bfs_q:
            cur, d = bfs_q.popleft()
            for nb in portal_sets.get(cur, set()):
                if nb not in hops_to_target:
                    hops_to_target[nb] = d + 1
                    bfs_q.append((nb, d + 1))

        # ── Icon-centre lookup for geographic tiebreaking ─────────────────────
        # _ICON_BOUNDS_EXT is optionally injected by WorldMap+ (the same
        # mechanism used for _PORTAL_ICON_POS_EXT).
        icon_bounds: dict = getattr(self, "_ICON_BOUNDS_EXT", None) or {}

        def _icon_centre(mid: int) -> tuple[float, float] | None:
            bnd = icon_bounds.get(mid)
            if bnd:
                return ((bnd[0] + bnd[2]) * 0.5, (bnd[1] + bnd[3]) * 0.5)
            return None

        target_centre = _icon_centre(target_map_id)

        def _icon_dist(mid: int) -> float:
            """Euclidean icon-space distance from outpost centre to target centre."""
            if target_centre is None:
                return 0.0
            oc = _icon_centre(mid)
            if oc is None:
                return 0.0
            return math.hypot(oc[0] - target_centre[0], oc[1] - target_centre[1])

        # ── Collect all unlocked outposts reachable from the target ───────────
        # Only accept candidates for which a real portal-linked path exists
        # (IsPath uses portal_adj, not the broader world_adj, so candidates
        # reachable only via static _MAP_ADJACENCY entries are filtered out).
        candidates: list[dict] = []
        for mid, meta in WorldPathing._MAP_META.items():
            if meta[0] == WorldPathing._RT_EXPLORABLE:
                continue
            if meta[1] == "Unknown Map ID":
                continue
            if not Map.IsMapUnlocked(mid):
                continue
            if mid not in hops_to_target:
                continue
            hops = hops_to_target[mid]
            dist = self.path_distance(mid, target_map_id)
            candidates.append({
                "map_id":        mid,
                "name":          meta[1],
                "hops":          hops,
                "distance":      dist,
                "_walk":         dist if dist is not None else float("inf"),
                "_icon_dist":    _icon_dist(mid),
            })

        if not candidates:
            return None

        # Sort: fewest walking hops → then game-unit distance → then icon
        # distance → then map_id for determinism.
        candidates.sort(key=lambda c: (
            c["hops"],
            c["_walk"],
            c["_icon_dist"],
            c["map_id"],
        ))
        best = candidates[0]
        best.pop("_walk",      None)
        best.pop("_icon_dist", None)
        return best

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _map_name_cached(self, mid: int) -> str:
        meta = WorldPathing._MAP_META.get(mid)
        if meta:
            return meta[1]
        try:
            name = Map.GetMapName(mid)
            if name and name != "Unknown Map ID":
                WorldPathing._MAP_META[mid] = (0, name, 0)
                return name
        except Exception:
            pass
        return f"Map {mid}"

    def _load_portal_links(self) -> None:
        """Load portal_links.json into portal_links, portal_game_pos, and ID→location maps."""
        self.portal_links.clear()
        self.portal_game_pos.clear()
        self.global_id_to_portal.clear()
        self.portal_to_global_id.clear()
        self.invalidate_portal_adj()
        if not os.path.isfile(self.portal_links_file):
            return
        try:
            with open(self.portal_links_file, "r", encoding="utf-8-sig") as fh:
                data = json.load(fh)
            count = 0
            for entry in data.get("links", []):
                a = int(entry["portal_a"]["global_id"])
                b = int(entry["portal_b"]["global_id"])
                self.portal_links[a] = b
                self.portal_links[b] = a
                for side in ("portal_a", "portal_b"):
                    p   = entry[side]
                    gid = int(p["global_id"])
                    gx  = float(p.get("game_x", 0.0))
                    gy  = float(p.get("game_y", 0.0))
                    if gx != 0.0 or gy != 0.0:
                        self.portal_game_pos[gid] = (gx, gy)
                    # Populate reverse-lookup dicts so the world-map overlay can
                    # resolve portals from ALL maps, not just maps already visited.
                    map_id  = int(p.get("map_id",       gid // 1000))
                    loc_idx = int(p.get("portal_index",  gid %  1000))
                    key = (map_id, loc_idx)
                    self.global_id_to_portal[gid] = key
                    self.portal_to_global_id[key] = gid
                count += 1
            if count:
                Py4GW.Console.Log(
                    MODULE_NAME,
                    f"Portal links loaded: {count} connections.",
                    Py4GW.Console.MessageType.Info,
                )
        except Exception as e:
            Py4GW.Console.Log(
                MODULE_NAME,
                f"Portal links load error: {e}",
                Py4GW.Console.MessageType.Warning,
            )

    def _find_map_path(self, start_map: int, end_map: int) -> tuple[list[int], list[str]]:
        """BFS from start_map to end_map through linked portals.

        Returns (gid_sequence, map_name_sequence).
        gid_sequence: [exit_gid_1, enter_gid_1, exit_gid_2, enter_gid_2, ...]
        map_name_sequence: [start_name, map2_name, ..., end_name]
        """
        if start_map == end_map or not self.portal_links:
            return [], []

        adj = self._get_portal_adj()

        # Bridge case: start_map is not in portal_adj (e.g. an outpost not listed in
        # portal_links.json that is co-located with its explorable).  Find the first
        # world_adj neighbour that IS in portal_adj and use it as the effective start.
        # The waypoint's from_map will still be reported as start_map so that
        # _mtm_autorun_coroutine correctly picks the hop from the actual current map.
        effective_start = start_map
        if start_map not in adj:
            world_adj = self.get_world_adj()
            bridge = next(
                (nb for nb in sorted(world_adj.get(start_map, set()))
                 if nb in adj and nb != start_map),
                None,
            )
            if bridge is None:
                return [], []
            # Co-located direct case (bridge == end): no portal waypoints possible;
            # IsPath handles this via world_adj check, GetPath returns no waypoints.
            if bridge == end_map:
                return [], []
            effective_start = bridge

        if end_map not in adj:
            return [], []

        queue:   deque    = deque([(effective_start, [])])
        visited: set[int] = {start_map, effective_start}
        while queue:
            cur_map, hops = queue.popleft()
            for exit_gid, enter_gid, next_map in adj.get(cur_map, []):
                if next_map in visited:
                    continue
                new_hops = hops + [(exit_gid, enter_gid)]
                if next_map == end_map:
                    gids: list[int]  = []
                    mnames: list[str] = [self._map_name_cached(start_map)]
                    for eg, ig in new_hops:
                        gids.extend([eg, ig])
                        km = self.global_id_to_portal.get(ig)
                        mnames.append(
                            self._map_name_cached(km[0]) if km
                            else f"Map {ig // 1000}"
                        )
                    return gids, mnames
                visited.add(next_map)
                queue.append((next_map, new_hops))
        return [], []

    def _get_portal_game_xy(self, gid: int) -> tuple[float, float] | None:
        """Return (game_x, game_y) for a portal GID, trying every available source."""
        # 1. portal_links.json recorded coordinates (best quality)
        pos = self.portal_game_pos.get(gid)
        if pos:
            return pos

        key = self.global_id_to_portal.get(gid)
        if key is None:
            key = (gid // 1000, gid % 1000)
        map_id, loc_idx = key

        # 2. Overlay coords injected by WorldMap+ via the module-level attribute
        _pip = globals().get("_PORTAL_ICON_POS_EXT")
        if _pip:
            for entry in _pip.get(map_id, []):
                if entry[3] == loc_idx and len(entry) >= 7:
                    return float(entry[5]), float(entry[6])

        # 3. Live game engine — only works when the player is on this map now
        try:
            if Map.GetMapID() == map_id:
                portals = Map.Pathing.GetTravelPortals()
                if portals:
                    portals_sorted = sorted(
                        portals,
                        key=lambda p: (round(p.x, 1), round(p.y, 1)),
                    )
                    if loc_idx < len(portals_sorted):
                        tp = portals_sorted[loc_idx]
                        xy = (float(tp.x), float(tp.y))
                        # Cache so subsequent calls are instant
                        self.portal_game_pos[gid] = xy
                        return xy
        except Exception:
            pass

        return None

    # ── Bot API: IsPath / GetPath ──────────────────────────────────────────────

    def IsPath(self, start_map_id: int, target_map_id: int) -> bool:
        """Return True if a portal-linked route exists from start to target."""
        if start_map_id == target_map_id:
            return True
        # Direct world-adj check handles co-located maps not in portal_adj
        # (e.g. an outpost that shares icon bounds with its adjacent explorable).
        adj = self._get_portal_adj()
        if start_map_id not in adj:
            if target_map_id in self.get_world_adj().get(start_map_id, set()):
                return True
        gids, _ = self._find_map_path(start_map_id, target_map_id)
        return len(gids) > 0

    def GetPath(self, start_map_id: int, target_map_id: int) -> dict:
        """Return full inter-map route with map ids, names and portal waypoints.

        Return value::
          {
            "found":     bool,
            "maps":      list[int],
            "map_names": list[str],
            "waypoints": [{"from_map", "exit_gid", "enter_gid", "to_map",
                           "game_x", "game_y"}, ...]
          }
        """
        if start_map_id == target_map_id:
            return {
                "found":     True,
                "maps":      [start_map_id],
                "map_names": [self._map_name_cached(start_map_id)],
                "waypoints": [],
            }

        gids, map_names = self._find_map_path(start_map_id, target_map_id)
        if not gids:
            return {"found": False, "maps": [], "map_names": [], "waypoints": []}

        map_ids:   list[int]  = [start_map_id]
        waypoints: list[dict] = []
        hop_count = len(gids) // 2

        for i in range(hop_count):
            exit_gid  = gids[i * 2]
            enter_gid = gids[i * 2 + 1]
            from_map  = map_ids[-1]

            km     = self.global_id_to_portal.get(enter_gid)
            to_map = km[0] if km else enter_gid // 1000
            map_ids.append(to_map)

            xy = self._get_portal_game_xy(exit_gid)
            waypoints.append({
                "from_map":  from_map,
                "exit_gid":  exit_gid,
                "enter_gid": enter_gid,
                "to_map":    to_map,
                "game_x":    xy[0] if xy else None,
                "game_y":    xy[1] if xy else None,
            })

        return {
            "found":     True,
            "maps":      map_ids,
            "map_names": map_names,
            "waypoints": waypoints,
        }

    # ── Runtime heartbeat ──────────────────────────────────────────────────────

    def _set_runtime_heartbeat(self) -> None:
        setattr(GLOBAL_CACHE, "_wp_runtime_token", self._instance_token)
        setattr(GLOBAL_CACHE, "_wp_runtime_hb_ms", int(Utils.GetBaseTimestamp()))

    def _runtime_is_active(self, token: str) -> bool:
        active = getattr(GLOBAL_CACHE, "_wp_runtime_token", None)
        hb     = int(getattr(GLOBAL_CACHE, "_wp_runtime_hb_ms", 0) or 0)
        return (
            active == token
            and (int(Utils.GetBaseTimestamp()) - hb) <= self.WP_HEARTBEAT_TIMEOUT_MS
        )

    # ── Movement state management ──────────────────────────────────────────────

    def _mtnw_clear(self) -> None:
        self.mtnw_goal_xy[0]        = None
        self.mtnw_target_map[0]     = 0
        self.mtnw_path.clear()
        self.mtnw_path_index[0]     = 0
        self.mtnw_path_following[0] = False
        self.mtnw_path_computing[0] = False
        self.mtnw_runner_active[0]  = False
        self.mtnw_paused_danger[0]  = False
        self.mtnw_bt_tree           = None

    def _mtm_clear(self) -> None:
        self.mtm_runner_active[0] = False
        self.mtm_target_map[0]    = 0
        self.mtm_route[0]         = None

    def _abort_wp_movement(self) -> None:
        self.mtnw_job_id[0] += 1
        self.mtm_job_id[0]  += 1
        self._mtnw_clear()
        self._mtm_clear()
        try:
            px, py = Player.GetXY()
            Player.Move(px, py)
        except Exception:
            pass

    # ── Danger check ───────────────────────────────────────────────────────────

    def _mtnw_is_danger_nearby(self) -> bool:
        """Return True when hostile agents are within mtnw_danger_radius of the player."""
        try:
            px, py = Player.GetXY()
            enemies = Routines.Agents.GetFilteredEnemyArray(px, py, self.mtnw_danger_radius)
            return len(enemies) > 0
        except Exception:
            return False

    # ── Movement coroutines ────────────────────────────────────────────────────

    def _mtnw_autorun_coroutine(
        self,
        target_map_id: int,
        goal_x: float,
        goal_y: float,
        job_id: int,
        runtime_token: str,
    ):
        """Compute and follow a local AutoPathing path to a portal waypoint."""
        self.mtnw_runner_active[0] = True
        self.mtnw_path.clear()

        while True:
            if not self._runtime_is_active(runtime_token):
                self._abort_wp_movement()
                return
            if job_id != self.mtnw_job_id[0]:
                return
            if Map.GetMapID() == target_map_id:
                self._mtnw_clear()
                return

            px, py = Player.GetXY()
            dx = px - goal_x
            dy = py - goal_y
            if (dx * dx + dy * dy) <= (self.MTNW_ARRIVAL_RADIUS ** 2):
                _pt_start = Utils.GetBaseTimestamp()
                _pt_map   = Map.GetMapID()
                while True:
                    if job_id != self.mtnw_job_id[0]:
                        return
                    if Map.IsMapLoading() or Map.GetMapID() != _pt_map:
                        self._mtnw_clear()
                        return
                    if Utils.GetBaseTimestamp() - _pt_start > self.MTNW_PUSHTHROUGH_TIMEOUT_MS:
                        break
                    Player.Move(goal_x, goal_y)
                    yield from Routines.Yield.wait(100)
                # Pushthrough timeout: nudge forward in steps until portal triggers
                _nudge_map = Map.GetMapID()
                for _nudge_idx in range(self.MTNW_NUDGE_MAX_STEPS):
                    if job_id != self.mtnw_job_id[0]:
                        return
                    if Map.IsMapLoading() or Map.GetMapID() != _nudge_map:
                        self._mtnw_clear()
                        return
                    try:
                        _fcos = Agent.GetRotationCos(Player.GetAgentID())
                        _fsin = Agent.GetRotationSin(Player.GetAgentID())
                        _nx, _ny = Player.GetXY()
                        Player.Move(_nx + _fcos * self.MTNW_NUDGE_STEP, _ny + _fsin * self.MTNW_NUDGE_STEP)
                    except Exception:
                        break
                    _nd_start = Utils.GetBaseTimestamp()
                    while Utils.GetBaseTimestamp() - _nd_start < 500:
                        if Map.IsMapLoading() or Map.GetMapID() != _nudge_map:
                            self._mtnw_clear()
                            return
                        yield from Routines.Yield.wait(100)
                self._mtnw_clear()
                return

            # Use BottingTree BT for movement (handles autopathing, stall recovery,
            # pause-on-combat internally).
            move_tree = RoutinesBT.Player.Move(goal_x, goal_y, log=False)
            self.mtnw_bt_tree = move_tree
            while True:
                if job_id != self.mtnw_job_id[0]:
                    move_tree.blackboard["PAUSE_MOVEMENT"] = False
                    return
                if Map.GetMapID() == target_map_id:
                    move_tree.blackboard["PAUSE_MOVEMENT"] = False
                    self._mtnw_clear()
                    return

                # Sync path data to mtnw_path/index so WorldMap+ overlay still works.
                bb_path = move_tree.blackboard.get("move_path_points")
                if bb_path is not None:
                    self.mtnw_path[:] = [(float(p[0]), float(p[1])) for p in bb_path]
                    self.mtnw_path_index[0] = int(
                        move_tree.blackboard.get("move_path_index", 0)
                    )
                    self.mtnw_path_following[0] = len(self.mtnw_path) > 0

                # Sync danger state and set PAUSE_MOVEMENT flag.
                if self.mtnw_pause_on_danger:
                    in_danger = self._mtnw_is_danger_nearby()
                else:
                    in_danger = False
                if in_danger != self.mtnw_paused_danger[0]:
                    self.mtnw_paused_danger[0] = in_danger
                move_tree.blackboard["PAUSE_MOVEMENT"] = in_danger

                bt_result = BehaviorTree.Node._normalize_state(move_tree.tick())
                if bt_result in (RoutinesBT.NodeState.SUCCESS, RoutinesBT.NodeState.FAILURE):
                    move_tree.blackboard["PAUSE_MOVEMENT"] = False
                    self.mtnw_bt_tree = None
                    break
                yield from Routines.Yield.wait(100)

            if job_id != self.mtnw_job_id[0]:
                return
            if Map.GetMapID() == target_map_id:
                self._mtnw_clear()
                return

            cx, cy = Player.GetXY()
            ddx = cx - goal_x
            ddy = cy - goal_y
            if (ddx * ddx + ddy * ddy) <= (self.MTNW_ARRIVAL_RADIUS ** 2):
                _pt_start = Utils.GetBaseTimestamp()
                _pt_map   = Map.GetMapID()
                while True:
                    if job_id != self.mtnw_job_id[0]:
                        return
                    if Map.IsMapLoading() or Map.GetMapID() != _pt_map:
                        self._mtnw_clear()
                        return
                    if Utils.GetBaseTimestamp() - _pt_start > self.MTNW_PUSHTHROUGH_TIMEOUT_MS:
                        break
                    Player.Move(goal_x, goal_y)
                    yield from Routines.Yield.wait(100)
                # Pushthrough timeout: nudge forward in steps until portal triggers
                _nudge_map = Map.GetMapID()
                for _nudge_idx in range(self.MTNW_NUDGE_MAX_STEPS):
                    if job_id != self.mtnw_job_id[0]:
                        return
                    if Map.IsMapLoading() or Map.GetMapID() != _nudge_map:
                        self._mtnw_clear()
                        return
                    try:
                        _fcos = Agent.GetRotationCos(Player.GetAgentID())
                        _fsin = Agent.GetRotationSin(Player.GetAgentID())
                        _nx, _ny = Player.GetXY()
                        Player.Move(_nx + _fcos * self.MTNW_NUDGE_STEP, _ny + _fsin * self.MTNW_NUDGE_STEP)
                    except Exception:
                        break
                    _nd_start = Utils.GetBaseTimestamp()
                    while Utils.GetBaseTimestamp() - _nd_start < 500:
                        if Map.IsMapLoading() or Map.GetMapID() != _nudge_map:
                            self._mtnw_clear()
                            return
                        yield from Routines.Yield.wait(100)
                self._mtnw_clear()
                return

            yield from Routines.Yield.wait(150)

    def _mtm_autorun_coroutine(
        self,
        target_map_id: int,
        route: dict,
        job_id: int,
        runtime_token: str,
    ):
        """Traverse a full inter-map route by chaining MoveToNextWaypoint hop-by-hop."""
        self.mtm_runner_active[0] = True
        try:
            while True:
                if not self._runtime_is_active(runtime_token):
                    self._abort_wp_movement()
                    return
                if job_id != self.mtm_job_id[0]:
                    return

                current_map = Map.GetMapID()
                if current_map == target_map_id:
                    return

                hop = None
                for wp in route.get("waypoints", []):
                    if int(wp.get("from_map", 0)) == current_map:
                        hop = wp
                        break

                if hop is None:
                    Py4GW.Console.Log(
                        MODULE_NAME,
                        f"MoveToMapid: no hop from map {current_map} toward {target_map_id}.",
                        Py4GW.Console.MessageType.Warning,
                    )
                    return

                next_map = int(hop.get("to_map", 0))
                if next_map <= 0:
                    return

                Py4GW.Console.Log(
                    MODULE_NAME,
                    f"MoveToMapid: hop {current_map}->{next_map} "
                    f"exit_gid={hop.get('exit_gid')} "
                    f"game_pos=({hop.get('game_x')}, {hop.get('game_y')})",
                    Py4GW.Console.MessageType.Info,
                )

                # Refresh coords if missing (player is on current_map, live data available)
                if hop.get("game_x") is None or hop.get("game_y") is None:
                    exit_gid = hop.get("exit_gid", 0)
                    if exit_gid:
                        xy = self._get_portal_game_xy(exit_gid)
                        if xy:
                            hop["game_x"] = xy[0]
                            hop["game_y"] = xy[1]

                hop_path = {
                    "found":     True,
                    "maps":      [current_map, next_map],
                    "map_names": [],
                    "waypoints": [hop],
                }

                hop_completed = False
                for _attempt in range(self.MTM_HOP_MAX_ATTEMPTS):
                    if not self._runtime_is_active(runtime_token):
                        self._abort_wp_movement()
                        return
                    if job_id != self.mtm_job_id[0]:
                        return

                    _started = self.MoveToNextWaypoint(next_map, hop_path)
                    if not _started:
                        yield from Routines.Yield.wait(250)
                        continue

                    start_ts            = Utils.GetBaseTimestamp()
                    transition_detected = False

                    while True:
                        if not self._runtime_is_active(runtime_token):
                            self._abort_wp_movement()
                            return
                        if job_id != self.mtm_job_id[0]:
                            return

                        cmap = Map.GetMapID()
                        if cmap == next_map or cmap == target_map_id:
                            hop_completed = True
                            break
                        if cmap != current_map:
                            transition_detected = True
                            break
                        if Utils.GetBaseTimestamp() - start_ts > self.MTM_HOP_TIMEOUT_MS:
                            break
                        yield from Routines.Yield.wait(250)

                    if not hop_completed and transition_detected:
                        _loaded = yield from Routines.Yield.Map.WaitforMapLoad(
                            next_map, log=False, timeout=self.MTM_LOAD_TIMEOUT_MS
                        )
                        if job_id != self.mtm_job_id[0]:
                            return
                        cmap_after = Map.GetMapID()
                        if cmap_after == next_map or cmap_after == target_map_id:
                            hop_completed = True
                            break
                        if _loaded and cmap_after != current_map:
                            break

                    if hop_completed:
                        break
                    if Map.GetMapID() != current_map:
                        break

                    self.mtnw_job_id[0] += 1
                    self._mtnw_clear()
                    yield from Routines.Yield.wait(200)

                if Map.GetMapID() == target_map_id:
                    return
                if not hop_completed and Map.GetMapID() == current_map:
                    Py4GW.Console.Log(
                        MODULE_NAME,
                        f"MoveToMapid: failed to transition from {current_map} to {next_map}.",
                        Py4GW.Console.MessageType.Warning,
                    )
                    return

                yield from Routines.Yield.wait(150)
        finally:
            self._mtm_clear()

    # ── Public movement API ────────────────────────────────────────────────────

    def MoveToNextWaypoint(self, target_map_id: int, path: dict | None = None) -> bool:
        """Start autonomous movement to the first portal waypoint in *path*.

        Queues a coroutine into GLOBAL_CACHE that follows the AutoPathing route
        to the exit portal on the current map.  Returns True while movement is
        active, False if already at destination or path is missing.

        *path* must be the dict returned by GetPath().
        """
        current_map = Map.GetMapID()
        if current_map == target_map_id:
            self._mtnw_clear()
            return False

        if path is None or not path.get("found") or not path.get("waypoints"):
            Py4GW.Console.Log(
                MODULE_NAME,
                "MoveToNextWaypoint: no path provided. Call GetPath() first.",
                Py4GW.Console.MessageType.Warning,
            )
            return False

        wp = path["waypoints"][0]
        gx, gy = wp["game_x"], wp["game_y"]
        if gx is None or gy is None:
            Py4GW.Console.Log(
                MODULE_NAME,
                f"MoveToNextWaypoint: no game coords for exit portal GID {wp['exit_gid']}",
                Py4GW.Console.MessageType.Warning,
            )
            return False

        goal_xy = (float(gx), float(gy))

        if (
            self.mtnw_runner_active[0]
            and self.mtnw_goal_xy[0] == goal_xy
            and self.mtnw_target_map[0] == target_map_id
        ):
            return True

        self._mtnw_clear()
        self.mtnw_goal_xy[0]       = goal_xy
        self.mtnw_target_map[0]    = target_map_id
        self.mtnw_runner_active[0] = True
        self.mtnw_job_id[0]       += 1
        self._set_runtime_heartbeat()

        GLOBAL_CACHE.Coroutines.append(
            self._mtnw_autorun_coroutine(
                target_map_id,
                goal_xy[0],
                goal_xy[1],
                self.mtnw_job_id[0],
                self._instance_token,
            )
        )
        return True

    def MoveToMapid(self, target_map_id: int) -> bool:
        """Build a full route from the current map to target_map_id and execute it.

        Returns True while movement is active, False if already there or no path.
        Re-entrant: calling again with the same target while active is a no-op.
        """
        current_map = Map.GetMapID()
        if current_map == target_map_id:
            return False

        if self.mtm_runner_active[0] and self.mtm_target_map[0] == target_map_id:
            return True

        if not self.IsPath(current_map, target_map_id):
            Py4GW.Console.Log(
                MODULE_NAME,
                f"MoveToMapid: no path from map {current_map} to map {target_map_id}.",
                Py4GW.Console.MessageType.Warning,
            )
            return False

        route = self.GetPath(current_map, target_map_id)
        if not route.get("found"):
            return False

        self.mtm_target_map[0]    = target_map_id
        self.mtm_route[0]         = route
        self.mtm_runner_active[0] = True
        self.mtm_job_id[0]       += 1
        self._set_runtime_heartbeat()

        GLOBAL_CACHE.Coroutines.append(
            self._mtm_autorun_coroutine(
                target_map_id,
                route,
                self.mtm_job_id[0],
                self._instance_token,
            )
        )
        return True

    def MoveToMapID(self, target_map_id: int) -> bool:
        """Alias for MoveToMapid (capitalisation variant)."""
        return self.MoveToMapid(target_map_id)


# ══════════════════════════════════════════════════════════════════════════════
# Module-level singleton + backward-compatible aliases
# All existing importers (WorldMap+.py, WorldMap+Debug.py, __init__.py, bots)
# continue to work without any changes.
# ══════════════════════════════════════════════════════════════════════════════

# Overlay injection point: WorldMap+.py writes its _PORTAL_ICON_POS dict here
# so that _get_portal_game_xy() can read live screen-mapped portal coordinates.
_PORTAL_ICON_POS_EXT: dict | None = None

# Module-level singleton instance
_wp = WorldPathing()

# ── Class-level static data ───────────────────────────────────────────────────
_MAP_ADJACENCY = WorldPathing._MAP_ADJACENCY
_ALL_EDGES     = WorldPathing._ALL_EDGES
_MAP_META      = WorldPathing._MAP_META

# ── Per-instance dicts (same objects — mutations are reflected everywhere) ─────
_GLOBAL_ID_TO_PORTAL = _wp.global_id_to_portal
_PORTAL_TO_GLOBAL_ID = _wp.portal_to_global_id
_PORTAL_LINKS        = _wp.portal_links
_PORTAL_GAME_POS     = _wp.portal_game_pos

# ── Movement state list containers (same list objects) ────────────────────────
_mtnw_goal_xy        = _wp.mtnw_goal_xy
_mtnw_target_map     = _wp.mtnw_target_map
_mtnw_path           = _wp.mtnw_path
_mtnw_path_index     = _wp.mtnw_path_index
_mtnw_path_following = _wp.mtnw_path_following
_mtnw_path_computing = _wp.mtnw_path_computing
_mtnw_runner_active  = _wp.mtnw_runner_active
_mtnw_job_id         = _wp.mtnw_job_id
_mtnw_paused_danger  = _wp.mtnw_paused_danger

_mtm_runner_active   = _wp.mtm_runner_active
_mtm_target_map      = _wp.mtm_target_map
_mtm_route           = _wp.mtm_route
_mtm_job_id          = _wp.mtm_job_id

# ── Module-level function aliases ─────────────────────────────────────────────

def configure(script_dir: str) -> None:
    _wp.configure(script_dir)

def invalidate_portal_adj() -> None:
    _wp.invalidate_portal_adj()

def _get_portal_adj():
    return _wp._get_portal_adj()

def get_world_adj() -> dict:
    return _wp.get_world_adj()

def invalidate_world_adj() -> None:
    _wp.invalidate_world_adj()

def path_distance(start_map: int, end_map: int):
    return _wp.path_distance(start_map, end_map)

def GetNearestUnlockedOutpost(target_map_id: int, from_map_id: int | None = None):
    return _wp.GetNearestUnlockedOutpost(target_map_id, from_map_id)

def _map_name_cached(mid: int) -> str:
    return _wp._map_name_cached(mid)

def _load_portal_links() -> None:
    _wp._load_portal_links()

def _find_map_path(start_map: int, end_map: int):
    return _wp._find_map_path(start_map, end_map)

def _get_portal_game_xy(gid: int):
    return _wp._get_portal_game_xy(gid)

def IsPath(start_map_id: int, target_map_id: int) -> bool:
    return _wp.IsPath(start_map_id, target_map_id)

def GetPath(start_map_id: int, target_map_id: int) -> dict:
    return _wp.GetPath(start_map_id, target_map_id)

def _set_runtime_heartbeat() -> None:
    _wp._set_runtime_heartbeat()

def _mtnw_clear() -> None:
    _wp._mtnw_clear()

def _mtm_clear() -> None:
    _wp._mtm_clear()

def _abort_wp_movement() -> None:
    _wp._abort_wp_movement()

def MoveToNextWaypoint(target_map_id: int, path: dict | None = None) -> bool:
    return _wp.MoveToNextWaypoint(target_map_id, path)

def MoveToMapid(target_map_id: int) -> bool:
    return _wp.MoveToMapid(target_map_id)

def MoveToMapID(target_map_id: int) -> bool:
    return _wp.MoveToMapid(target_map_id)
