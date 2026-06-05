"""
WorldPathing
============
Data layer for inter-map routing used by the WorldMap+ overlay.

Provides:
  - _MAP_ADJACENCY / _ALL_EDGES / _MAP_META   world-graph data (populated at runtime)
  - _PORTAL_LINKS / _GLOBAL_ID_TO_PORTAL / _PORTAL_TO_GLOBAL_ID / _PORTAL_GAME_POS
  - configure(adapter_dir)    load portal_links.json
  - invalidate_world_adj()    call after portal-link changes
  - _map_name_cached(mid)     map-name helper
  - _load_portal_links()      reload portal_links.json

Navigation only works for maps with recorded portal links.
Maps without portal links in portal_links.json are not reachable.
"""

import Py4GW
import json
import os

from Py4GWCoreLib.Map import Map

MODULE_NAME = "WorldPathing"


class WorldPathing:
    """Singleton that holds world-graph data and portal-link state for WorldMap+."""

    _instance = None

    # ── Class-level data (populated at runtime by WorldMap+._build_cache) ────────

    # Map-level adjacency graph. Populated at runtime from co-located map groups
    # and portal_links.json. No hardcoded entries — navigation only works for
    # maps with recorded portal links.
    _MAP_ADJACENCY: dict[int, set[int]] = {}

    # Deduplicated edge set (each pair stored once as (min, max)).
    _ALL_EDGES: set[tuple[int, int]] = set()

    # Map metadata: map_id -> (type:int, name:str, campaign:int)
    # Populated by WorldMap+._build_cache() on startup.
    _MAP_META: dict[int, tuple[int, str, int]] = {}

    # ──────────────────────────────────────────────────────────────────────────

    def __new__(cls) -> "WorldPathing":
        if cls._instance is None:
            cls._instance = super(WorldPathing, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

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
