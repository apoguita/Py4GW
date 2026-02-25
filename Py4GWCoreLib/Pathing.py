import Py4GW
import PyPathing
import math
import heapq
import pickle

from .enums import name_to_map_id
from typing import List, Tuple, Optional, Dict
from collections import defaultdict
from Py4GWCoreLib import Utils
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.native_src.context.MapContext import PathingTrapezoid

class AABB:
    """Axis-aligned bounding box for trapezoid geometry checks."""
    def __init__(self, t: PathingTrapezoid):
        self.m_t = t
        self.m_min = (min(t.XTL, t.XBL), t.YB)
        self.m_max = (max(t.XTR, t.XBR), t.YT)

# ─── BSP tree for O(log n) trapezoid point-location ─────────────────────────

# Leaf size balances construction speed vs query performance
_BSP_LEAF_SIZE = 16

class _BspSplit:
    __slots__ = ('split_y', 'above', 'below')
    def __init__(self, split_y: float, above, below):
        self.split_y = split_y
        self.above = above
        self.below = below

class _BspLeaf:
    __slots__ = ('traps',)
    def __init__(self, traps: list):
        self.traps = traps

def _point_in_trapezoid(x: float, y: float, t: PathingTrapezoid, tol: float = 0.0) -> bool:
    if y < t.YB - tol or y > t.YT + tol:
        return False
    height = t.YT - t.YB
    if height == 0:
        return False
    ratio = (y - t.YB) / height
    left_x = t.XBL + (t.XTL - t.XBL) * ratio
    right_x = t.XBR + (t.XTR - t.XBR) * ratio
    return left_x - tol <= x <= right_x + tol

def _build_trap_bsp(traps: list, sorted_indices: list, depth: int = 0):
    """Build BSP recursively using pre-sorted trapezoid indices."""
    n = len(sorted_indices)
    if n <= _BSP_LEAF_SIZE or depth >= 24:
        return _BspLeaf([traps[i] for i in sorted_indices])

    mid = n >> 1
    mid_idx = sorted_indices[mid]
    mid_prev_idx = sorted_indices[mid - 1]
    split_y = (traps[mid_prev_idx].YT + traps[mid_idx].YB) * 0.5

    above = [i for i in sorted_indices if traps[i].YT >= split_y]
    below = [i for i in sorted_indices if traps[i].YB <= split_y]

    if len(above) == n and len(below) == n:
        return _BspLeaf([traps[i] for i in sorted_indices])

    return _BspSplit(split_y,
                     _build_trap_bsp(traps, above, depth + 1),
                     _build_trap_bsp(traps, below, depth + 1))


class TrapezoidBSP:
    """BSP tree for O(log n) trapezoid point-location queries."""

    def __init__(self, trapezoids: List[PathingTrapezoid]):
        if not trapezoids:
            self._root = None
        else:
            sorted_indices = sorted(range(len(trapezoids)),
                                   key=lambda i: (trapezoids[i].YT + trapezoids[i].YB) * 0.5)
            self._root = _build_trap_bsp(trapezoids, sorted_indices)

    def find(self, x: float, y: float, tol: float = 0.0) -> Optional[int]:
        """Return trapezoid ID containing (x, y), or None."""
        if self._root is None:
            return None

        stack = [self._root]
        while stack:
            node = stack.pop()
            if isinstance(node, _BspLeaf):
                for t in node.traps:
                    if _point_in_trapezoid(x, y, t, tol):
                        return t.id
            else:
                if y > node.split_y + tol:
                    stack.append(node.above)
                elif y < node.split_y - tol:
                    stack.append(node.below)
                else:
                    stack.append(node.below)
                    stack.append(node.above)
        return None

    def find_with_margin(self, x: float, y: float, margin: float) -> bool:
        """Return True if (x, y) is inside a trapezoid with margin inset from edges."""
        if self._root is None:
            return False

        stack = [self._root]
        while stack:
            node = stack.pop()
            if isinstance(node, _BspLeaf):
                for t in node.traps:
                    if t.YB <= y <= t.YT:
                        height = t.YT - t.YB
                        if height == 0:
                            continue
                        ratio = (y - t.YB) / height
                        left_x = t.XBL + (t.XTL - t.XBL) * ratio
                        right_x = t.XBR + (t.XTR - t.XBR) * ratio
                        if left_x + margin <= x <= right_x - margin:
                            return True
            else:
                if y > node.split_y:
                    stack.append(node.above)
                elif y < node.split_y:
                    stack.append(node.below)
                else:
                    stack.append(node.below)
                    stack.append(node.above)
        return False


#region NavMesh

# Portal creation tolerances
_PORTAL_TOLERANCE = 32.0
_PORTAL_VERT_TOL = 100.2
_PORTAL_HORIZ_TOL = 100.6

class NavMesh:
    def __init__(self, pathing_maps, map_id: int):
        self.map_id = map_id
        self.trapezoids: Dict[int, PathingTrapezoid] = {}
        self.portal_graph: Dict[int, List[int]] = {}  # Adjacency graph for pathfinding
        self.trap_id_to_layer: Dict[int, int] = {}  # Trap ID -> layer index

        for i, layer in enumerate(pathing_maps):
            traps = layer.trapezoids
            self.trapezoids.update({t.id: t for t in traps})
            self.trap_id_to_layer.update({t.id: i for t in traps})

        self._bsp = TrapezoidBSP(list(self.trapezoids.values()))

        self.create_all_local_portals()
        self._create_cross_layer_portals_from_snapshots(pathing_maps)

    def get_adjacent_side(self, a: PathingTrapezoid, b: PathingTrapezoid) -> Optional[str]:
        if abs(a.YB - b.YT) < 1.0: return 'bottom_top'
        if abs(a.YT - b.YB) < 1.0: return 'top_bottom'
        if abs(a.XBR - b.XBL) < 1.0: return 'right_left'
        if abs(a.XBL - b.XBR) < 1.0: return 'left_right'
        return None

    def create_portal(self, box1: AABB, box2: AABB, side: Optional[str]) -> bool:
        """Create portal connection between two trapezoids in portal_graph."""
        pt1, pt2 = box1.m_t, box2.m_t

        def is_close(a, b): return abs(a - b) < _PORTAL_TOLERANCE

        # Validate geometric adjacency based on side
        if side == 'bottom_top':
            if not pt1.YB == pt2.YT:
                return False
            x_min = max(pt1.XBL, pt2.XBR)
            x_max = min(pt1.XBR, pt2.XBL)
            if is_close(x_max, x_min): return False

        elif side == 'top_bottom':
            if not pt1.YT == pt2.YB:
                return False
            x_min = max(pt1.XTL, pt2.XTR)
            x_max = min(pt1.XTR, pt2.XTL)
            if is_close(x_max, x_min): return False

        elif side == 'left_right':
            if not pt1.XTR == pt2.XTL:
                return False
            y_min = max(pt1.YT, pt2.YT)
            y_max = min(pt1.YB, pt2.YB)
            if is_close(y_max, y_min): return False

        elif side == 'right_left':
            if not pt1.XTL == pt2.XTR:
                return False
            y_min = max(pt1.YT, pt2.YT)
            y_max = min(pt1.YB, pt2.YB)
            if is_close(y_max, y_min): return False

        elif side is None:
            # Cross-layer portal - no geometric validation needed
            pass

        else:
            return False

        # Add bidirectional adjacency to portal graph
        self.portal_graph.setdefault(pt1.id, []).append(pt2.id)
        self.portal_graph.setdefault(pt2.id, []).append(pt1.id)
        return True

    def create_all_local_portals(self):
        # Group traps by zplane
        zplane_traps = defaultdict(list)
        for trap_id, z in self.trap_id_to_layer.items():
            zplane_traps[z].append(self.trapezoids[trap_id])

        for traps in zplane_traps.values():
            trap_by_id = {t.id: t for t in traps}

            for ti in traps:
                for nid in ti.neighbor_ids:
                    tj = trap_by_id.get(nid)
                    if not tj or ti.id == tj.id:
                        continue
                    ai = AABB(ti)
                    aj = AABB(tj)
                    side = self.get_adjacent_side(ti, tj)
                    if side:
                        self.create_portal(ai, aj, side)

    def touching(self, a: AABB, b: AABB, vert_tol: float = _PORTAL_VERT_TOL, horiz_tol: float = _PORTAL_HORIZ_TOL) -> bool:
        """Check if two trapezoid bounding boxes are geometrically adjacent."""
        # Same vertical alignment
        if abs(a.m_t.YB - b.m_t.YT) < vert_tol or abs(a.m_t.YT - b.m_t.YB) < vert_tol:
            left_a = min(a.m_t.XBL, a.m_t.XTL)
            right_a = max(a.m_t.XBR, a.m_t.XTR)
            left_b = min(b.m_t.XBL, b.m_t.XTL)
            right_b = max(b.m_t.XBR, b.m_t.XTR)
            if right_a >= left_b and right_b >= left_a:
                return True

        # Same horizontal alignment
        if abs(a.m_t.XBR - b.m_t.XBL) < horiz_tol or abs(a.m_t.XBL - b.m_t.XBR) < horiz_tol:
            top_a = max(a.m_t.YT, a.m_t.YB)
            bottom_a = min(a.m_t.YT, a.m_t.YB)
            top_b = max(b.m_t.YT, b.m_t.YB)
            bottom_b = min(b.m_t.YT, b.m_t.YB)
            if top_a >= bottom_b and top_b >= bottom_a:
                return True

        return False

    def _create_cross_layer_portals_from_snapshots(self, pathing_maps):
        """Build cross-layer portal connections from snapshot portal data."""
        cross_groups: Dict[Tuple[int, int], Dict[int, List[PathingTrapezoid]]] = defaultdict(lambda: defaultdict(list))

        for plane_idx, pmap in enumerate(pathing_maps):
            for portal in pmap.portals:
                if portal.left_layer_id == portal.right_layer_id:
                    continue

                layer_pair = (min(portal.left_layer_id, portal.right_layer_id),
                              max(portal.left_layer_id, portal.right_layer_id))

                for trap_id in portal.trapezoid_indices:
                    trap = self.trapezoids.get(trap_id)
                    if trap:
                        cross_groups[layer_pair][plane_idx].append(trap)

        for plane_map in cross_groups.values():
            planes = list(plane_map.keys())
            if len(planes) < 2:
                continue

            for i in range(len(planes)):
                for j in range(i + 1, len(planes)):
                    traps_i = plane_map[planes[i]]
                    traps_j = plane_map[planes[j]]

                    for ti in traps_i:
                        ai = AABB(ti)
                        for tj in traps_j:
                            if ti.id == tj.id:
                                continue
                            aj = AABB(tj)
                            if self.touching(ai, aj):
                                self.create_portal(ai, aj, None)


    def get_position(self, t_id: int) -> Tuple[float, float]:
        t = self.trapezoids[t_id]
        cx = (t.XTL + t.XTR + t.XBL + t.XBR) / 4
        cy = (t.YT + t.YB) / 2
        return (cx, cy)

    def get_neighbors(self, t_id: int) -> List[int]:
        return self.portal_graph.get(t_id, [])

    def find_trapezoid_id_by_coord(self, point: Tuple[float, float], tol: float = 20.0) -> Optional[int]:
        """Return trapezoid ID containing point, or None."""
        return self._bsp.find(point[0], point[1], tol)

    def contains(self, x: float, y: float, margin: float = 20.0) -> bool:
        """Return True if (x, y) lies on the NavMesh with the given inset margin."""
        return self._bsp.find_with_margin(x, y, margin)

    def find_nearest_reachable(
        self,
        origincoords: Tuple[float, float],
        boundaries: Tuple[float, float, float, float],
        max_radius: float = 2800.0,
        ring_step: float = 280.0,
        base_ring_points: int = 12,
        margin: float = 20.0,
    ) -> Optional[Tuple[float, float]]:
        """Find the nearest NavMesh point to origincoords within max_radius.

        Returns origincoords itself if it already lies on the mesh.  Otherwise
        performs an outward ring search (ring_step increments up to
        max_radius) and returns the closest reachable candidate, or None
        if nothing is found.

        Can be used for any position query – player location, click
        coordinates, waypoints, etc.
        """
        if self.contains(origincoords[0], origincoords[1], margin):
            return origincoords

        min_x, min_y, max_x, max_y = boundaries
        if min_x > max_x: min_x, max_x = max_x, min_x
        if min_y > max_y: min_y, max_y = max_y, min_y

        best: Optional[Tuple[float, float]] = None
        best_dist = float("inf")
        radius = ring_step
        while radius <= max_radius:
            count = max(8, int(base_ring_points + radius / 280.0))
            for i in range(count):
                angle = (2.0 * math.pi * i) / count
                cx = origincoords[0] + math.cos(angle) * radius
                cy = origincoords[1] + math.sin(angle) * radius
                if not (min_x <= cx <= max_x and min_y <= cy <= max_y):
                    continue
                if self.contains(cx, cy, margin):
                    d = math.hypot(cx - origincoords[0], cy - origincoords[1])
                    if d < best_dist:
                        best_dist = d
                        best = (cx, cy)
            radius += ring_step
        return best

    def has_line_of_sight(self,
                          p1: Tuple[float, float],
                          p2: Tuple[float, float],
                          margin: float = 100,
                          step_dist: float = 200.0) -> bool:

        total_dist = math.dist(p1, p2)
        steps = int(total_dist / step_dist) + 1
        dx = (p2[0] - p1[0]) / steps
        dy = (p2[1] - p1[1]) / steps

        for i in range(1, steps):
            x = p1[0] + dx * i
            y = p1[1] + dy * i
            if not self._bsp.find_with_margin(x, y, margin):
                return False
        return True



    def smooth_path_by_los(self,
                           path: List[Tuple[float, float]],
                           margin: float = 100,
                           step_dist: float = 200.0) -> List[Tuple[float, float]]:
        if len(path) <= 2:
            return path

        result = [path[0]]
        i = 0
        while i < len(path) - 1:
            j = len(path) - 1
            while j > i + 1:
                if self.has_line_of_sight(path[i], path[j], margin, step_dist):
                    break
                j -= 1
            result.append(path[j])
            i = j
        return result

    def save_to_file(self, folder: str):
        """Serialize NavMesh portal graph and metadata to disk."""
        filepath = f"{folder}/navmesh_{self.map_id}.bin"
        data = {
            "map_id": self.map_id,
            "portal_graph": self.portal_graph,
            "trap_id_to_layer": self.trap_id_to_layer
        }
        with open(filepath, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


    @staticmethod
    def load_from_file(pathing_maps, map_id: int, folder: str) -> "NavMesh":
        """Load serialized NavMesh portal graph and rebuild BSP from current trapezoid data."""
        filepath = f"{folder}/navmesh_{map_id}.bin"

        nav = NavMesh.__new__(NavMesh)
        nav.map_id = map_id
        nav.trapezoids = {}
        nav.portal_graph = {}
        nav.trap_id_to_layer = {}

        for i, layer in enumerate(pathing_maps):
            traps = layer.trapezoids
            nav.trapezoids.update({t.id: t for t in traps})
            nav.trap_id_to_layer.update({t.id: i for t in traps})

        nav._bsp = TrapezoidBSP(list(nav.trapezoids.values()))

        with open(filepath, "rb") as f:
            data = pickle.load(f)

        nav.portal_graph = data["portal_graph"]
        if "trap_id_to_layer" in data:
            nav.trap_id_to_layer = data["trap_id_to_layer"]

        Py4GW.Console.Log("NavMesh", f"Loaded NavMesh for map {map_id} with {len(nav.portal_graph)} connections and {len(nav.trapezoids)} trapezoids.", Py4GW.Console.MessageType.Info)
        return nav



#region AStar

class AStarNode:
    def __init__(self, node_id, g, f, parent=None):
        self.id = node_id
        self.g = g
        self.f = f
        self.parent = parent
    def __lt__(self, other): return self.f < other.f

class AStar:
    def __init__(self, navmesh: NavMesh):
        self.navmesh = navmesh
        self.path: List[Tuple[float, float]] = []

    def heuristic(self, a: int, b: int) -> float:
        ax, ay = self.navmesh.get_position(a)
        bx, by = self.navmesh.get_position(b)
        return math.hypot(bx - ax, by - ay)

    def search(self, start_pos: Tuple[float, float], goal_pos: Tuple[float, float]) -> bool:
        start_id = self.navmesh.find_trapezoid_id_by_coord(start_pos)
        goal_id = self.navmesh.find_trapezoid_id_by_coord(goal_pos)

        if start_id is None or goal_id is None:
            Py4GW.Console.Log("A-Star", f"Invalid start or goal trapezoid: {start_id}, {goal_id}", Py4GW.Console.MessageType.Error)
            return False

        open_list: List[AStarNode] = []
        heapq.heappush(open_list, AStarNode(start_id, 0, self.heuristic(start_id, goal_id)))
        came_from: Dict[int, int] = {}
        cost_so_far: Dict[int, float] = {start_id: 0}

        while open_list:
            current = heapq.heappop(open_list)
            if current.id == goal_id:
                self._reconstruct(came_from, goal_id)
                # Prepend exact start position, append exact goal position
                self.path.insert(0, start_pos)
                self.path.append(goal_pos)
                return True

            for neighbor in self.navmesh.get_neighbors(current.id):
                new_cost = cost_so_far[current.id] + self.heuristic(current.id, neighbor)
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self.heuristic(neighbor, goal_id)
                    heapq.heappush(open_list, AStarNode(neighbor, new_cost, priority, current.id))
                    came_from[neighbor] = current.id

        Py4GW.Console.Log("A-Star", f"Path not found from {start_id} to {goal_id}", Py4GW.Console.MessageType.Warning)
        return False

    def _reconstruct(self, came_from: Dict[int, int], end_id: int):
        self.path = []
        while end_id in came_from:
            self.path.append(self.navmesh.get_position(end_id))
            end_id = came_from[end_id]
        self.path.append(self.navmesh.get_position(end_id))  # Add start node
        self.path.reverse()

    def get_path(self) -> List[Tuple[float, float]]:
        return self.path


def chaikin_smooth_path(points: List[Tuple[float, float]], iterations: int = 1) -> List[Tuple[float, float]]:
    for _ in range(iterations):
        new_points = [points[0]]
        for i in range(len(points) - 1):
            p0 = points[i]
            p1 = points[i + 1]
            q = (0.75 * p0[0] + 0.25 * p1[0], 0.75 * p0[1] + 0.25 * p1[1])
            r = (0.25 * p0[0] + 0.75 * p1[0], 0.25 * p0[1] + 0.75 * p1[1])
            new_points.extend([q, r])
        new_points.append(points[-1])
        points = new_points
    return points

def densify_path2d(points: List[Tuple[float, float]], threshold: float = 500.0) -> List[Tuple[float, float]]:
    """Split path segments longer than threshold into smaller steps."""
    if threshold <= 0 or len(points) <= 1:
        return points.copy()

    out: List[Tuple[float, float]] = [points[0]]
    eps = 1e-6

    for i in range(1, len(points)):
        x0, y0 = out[-1]
        x1, y1 = points[i]

        # distance between the two points (2D)
        dist = Utils.Distance((x0, y0), (x1, y1))
        if dist <= threshold + eps:
            out.append((x1, y1))
            continue

        # direction (unit vector)
        dx, dy = x1 - x0, y1 - y0
        ux, uy = dx / dist, dy / dist

        s = threshold
        while s < dist - eps:
            out.append((x0 + ux * s, y0 + uy * s))
            s += threshold

        out.append((x1, y1))

    return out


PATHING_MAP_GROUPS = [
    [
        name_to_map_id["Great Temple of Balthazar"],
        name_to_map_id["Isle of the Nameless"],
    ],
    [
        name_to_map_id["Minister Chos Estate outpost"],
        name_to_map_id["Minister Chos Estate (explorable area)"],
    ],
    [
        name_to_map_id["Shing Jea Monastery"],
        212,  # Monastery Overlook
        285,  # Monastery Overlook
        name_to_map_id["Linnok Courtyard"],
        name_to_map_id["Saoshang Trail"],
        name_to_map_id["Seitung Harbor"],
    ],
    [
        name_to_map_id["Zen Daijun outpost"],
        name_to_map_id["Zen Daijun (explorable area)"],
    ],
    [
        name_to_map_id["Ran Musu Gardens"],
        name_to_map_id["Kinya Province"],
    ],
    [
        name_to_map_id["Tsumei Village"],
        name_to_map_id["Sunqua Vale"],
    ],#Nightfall Region - Istan Island - Below - aC
    [
        name_to_map_id["Kamadan Jewel of Istan - Halloween"],
        name_to_map_id["Kamadan Jewel of Istan - Wintersday"],
        name_to_map_id["Kamadan Jewel of Istan - Canthan New Year"],
        name_to_map_id["Kamadan Jewel of Istan"],
        name_to_map_id["Consulate"],
        name_to_map_id["Consulate Docks outpost"],
        name_to_map_id["Sun Docks"],
    ],
    [
        name_to_map_id["Sunspear Great Hall"],
        name_to_map_id["Plains of Jarin"],
    ], #Nightfall Region - Kourna - Below - aC
    [
        name_to_map_id["Nundu Bay outpost"],
        name_to_map_id["Marga Coast"],
    ],
    [
        name_to_map_id["Camp Hojanu"],
        name_to_map_id["Barbarous Shore"],
    ],
    [
        name_to_map_id["Venta Cemetery outpost"],
        name_to_map_id["Sunward Marches"],
    ],
    [
        name_to_map_id["Rilohn Refuge outpost"],
        name_to_map_id["The Floodplain of Mahnkelon"],
    ],
    [
        name_to_map_id["Chantry of Secrets"],
        name_to_map_id["Yatendi Canyons"],
    ], #Nightfall Region - Vabbi - Below - aC
    [
        name_to_map_id["Honur Hill"],
        name_to_map_id["Resplendent Makuun"],
        name_to_map_id["Bokka Amphitheatre"],
    ],
    [
        name_to_map_id["Tihark Orchard outpost"],
        name_to_map_id["Forum Highlands"],
    ],
    [
        name_to_map_id["Grand Court of Sebelkeh outpost"],
        name_to_map_id["The Mirror of Lyss"],
    ],
    [
        name_to_map_id["Dasha Vestibule outpost"],
        name_to_map_id["The Hidden City of Ahdashim"],
    ], #Nightfall Region - The Desolation - Below - aC
    [
        name_to_map_id["Bone Palace"],
        name_to_map_id["Joko's Domain"],
    ],
    [
        name_to_map_id["Ruins of Morah outpost"],
        name_to_map_id["The Alkali Pan"],
    ],
    [
        name_to_map_id["The Mouth of Torment"],
        name_to_map_id["The Ruptured Heart"]
    ],
]

class AutoPathing:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutoPathing, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.load_time: float = 0.0
        self.is_ready: bool = False
        self.pathing_map_cache: dict[tuple[int, ...], NavMesh] = {}
        self._last_group_key: Optional[tuple[int, ...]] = None
        self._initialized = True

    def _get_group_key(self, map_id: int) -> tuple[int, ...]:
        for group in PATHING_MAP_GROUPS:
            if map_id in group:
                return tuple(sorted(group))
        return (map_id,)  # Default: treat each unknown map_id as its own group

    def load_pathing_maps(self):
        map_id = Map.GetMapID()
        if not map_id:
            yield
            return

        group_key = self._get_group_key(map_id)
        yield

        cached = self.pathing_map_cache.get(group_key)
        if cached is not None and cached.map_id == map_id:
            yield
            return
        pathing_maps = Map.Pathing.GetPathingMaps()
        navmesh = NavMesh(pathing_maps, map_id)
        self.pathing_map_cache[group_key] = navmesh
        yield


    def get_navmesh(self) -> Optional[NavMesh]:
        map_id = Map.GetMapID()
        if not map_id:
            return None

        group_key = self._get_group_key(map_id)
        nav = self.pathing_map_cache.get(group_key)

        if nav is None or nav.map_id != map_id:
            return None

        return nav


    def get_path(self,
                 start: Tuple[float, float, float],
                 goal: Tuple[float, float, float],
                 smooth_by_los: bool = True,
                 margin: float = 100,
                 step_dist: float = 200.0,
                 smooth_by_chaikin: bool = False,
                 chaikin_iterations: int = 1):
        from . import Routines

        def _prepend_start(path2d, sx, sy):
            if not path2d:
                return [(sx, sy)]

            dx = path2d[0][0] - sx
            dy = path2d[0][1] - sy
            d2 = dx*dx + dy*dy

            # Only prepend if it is REALLY far (path clearly doesn't start at player)
            if d2 > 750*750:
                return [(sx, sy)] + path2d

            return path2d

        map_id = Map.GetMapID()
        if not map_id:
            yield
            return []
        group_key = self._get_group_key(map_id)

        # --- Try fast planner first ---
        path_planner = PyPathing.PathPlanner()
        path_planner.reset()
        path_planner.plan(
            start_x=start[0], start_y=start[1], start_z=start[2],
            goal_x=goal[0], goal_y=goal[1], goal_z=goal[2]
        )

        while True:
            yield from Routines.Yield.wait(100)
            status = path_planner.get_status()
            if status == PyPathing.PathStatus.Ready:
                yield
                raw_path = path_planner.get_path()
                path2d = [(pt[0], pt[1]) for pt in raw_path]

                path2d = _prepend_start(path2d, start[0], start[1])

                if smooth_by_chaikin:
                    path2d = chaikin_smooth_path(path2d, chaikin_iterations)

                path2d = densify_path2d(path2d)
                return [(x, y, start[2]) for (x, y) in path2d]

            elif status == PyPathing.PathStatus.Failed:
                break
            yield

        navmesh = self.get_navmesh()
        if not navmesh:
            yield from self.load_pathing_maps()
            navmesh = self.get_navmesh()
            if not navmesh:
                yield
                return []


        yield
        astar = AStar(navmesh)
        success = astar.search((start[0], start[1]), (goal[0], goal[1]))
        yield

        if success:
            raw_path = astar.get_path()
            yield
            raw_path = _prepend_start(raw_path, start[0], start[1])
            if smooth_by_los:
                smoothed = navmesh.smooth_path_by_los(raw_path, margin, step_dist)
            else:
                smoothed = raw_path

            if smooth_by_chaikin:
                smoothed = chaikin_smooth_path(smoothed, chaikin_iterations)

            path2d = densify_path2d(smoothed)  # split long hops into ≤750

            return [(x, y, start[2]) for (x, y) in path2d]

        return []

    def get_path_to(self, x: float, y: float,
                    smooth_by_los: bool = True,
                    margin: float = 100,
                    step_dist: float = 200.0,
                    smooth_by_chaikin: bool = False,
                    chaikin_iterations: int = 1):
        from .Agent import Agent
        from .Player import Player

        _player = Player.GetAgent()
        if not _player:
            yield
            return []

        pos = (_player.pos.x, _player.pos.y)
        zplane = _player.pos.zplane
        start = (pos[0], pos[1], zplane)
        goal = (x, y, zplane)

        path = yield from self.get_path(start, goal,
                                        smooth_by_los=smooth_by_los,
                                        margin=margin,
                                        step_dist=step_dist,
                                        smooth_by_chaikin=smooth_by_chaikin,
                                        chaikin_iterations=chaikin_iterations)
        return [(x, y) for (x, y, _) in path]
