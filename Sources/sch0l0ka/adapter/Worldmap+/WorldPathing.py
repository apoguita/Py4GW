"""
WorldPathing
============
Data layer for inter-map routing used by the WorldMap+ overlay.

Provides:
  - _MAP_ADJACENCY / _ALL_EDGES / _MAP_META   world-graph static data
  - _PORTAL_LINKS / _GLOBAL_ID_TO_PORTAL / _PORTAL_TO_GLOBAL_ID / _PORTAL_GAME_POS
  - configure(script_dir)     load portal_links.json
  - invalidate_world_adj()    call after portal-link changes
  - _map_name_cached(mid)     map-name helper
  - _load_portal_links()      reload portal_links.json
"""

import Py4GW
import json
import os

from Py4GWCoreLib.Map import Map

MODULE_NAME = "WorldPathing"


class WorldPathing:
    """Singleton that holds world-graph data and portal-link state for WorldMap+."""

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

        # ── Portal data (per-instance, loaded from portal_links.json) ─────────
        self.portal_links_file: str = ""
        #   global_id -> linked global_id
        self.portal_links:        dict[int, int]                 = {}
        #   global_id -> (game_x, game_y)
        self.portal_game_pos:     dict[int, tuple[float, float]] = {}
        #   global_id -> (map_id, local_index)
        self.global_id_to_portal: dict[int, tuple[int, int]]     = {}
        #   (map_id, local_index) -> global_id
        self.portal_to_global_id: dict[tuple[int, int], int]     = {}

        self._world_adj_cache: dict | None = None

        self._initialized = True

    # ── Configuration ──────────────────────────────────────────────────────────

    def configure(self, script_dir: str) -> None:
        """Set the portal_links.json path and load the data."""
        self.portal_links_file = os.path.join(script_dir, "portal_links.json")
        self._load_portal_links()

    # ── Cache invalidation ─────────────────────────────────────────────────────

    def invalidate_portal_adj(self) -> None:
        """Invalidate adjacency caches. Call whenever portal_links changes."""
        self._world_adj_cache = None

    def invalidate_world_adj(self) -> None:
        """Invalidate the combined adjacency cache."""
        self._world_adj_cache = None

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
        """Load portal_links.json into portal_links, portal_game_pos, and ID->location maps."""
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


# ══════════════════════════════════════════════════════════════════════════════
# Module-level singleton + aliases
# ══════════════════════════════════════════════════════════════════════════════

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

# ── Module-level function aliases ─────────────────────────────────────────────

def configure(script_dir: str) -> None:
    _wp.configure(script_dir)

def invalidate_portal_adj() -> None:
    _wp.invalidate_portal_adj()

def invalidate_world_adj() -> None:
    _wp.invalidate_world_adj()

def _map_name_cached(mid: int) -> str:
    return _wp._map_name_cached(mid)

def _load_portal_links() -> None:
    _wp._load_portal_links()
