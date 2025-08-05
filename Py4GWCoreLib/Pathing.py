import Py4GW
import PyPathing
import PyOverlay
import PyMap
import math
import heapq
import time
from .enums import name_to_map_id
from typing import List, Tuple, Optional, Dict
from collections import defaultdict

PathingMap = PyPathing.PathingMap
PathingTrapezoid = PyPathing.PathingTrapezoid
PathingPortal = PyPathing.Portal
Point2D = PyOverlay.Point2D

class AABB:
    def __init__(self, t: PathingTrapezoid):
        self.m_t = t
        self.m_min = (min(t.XTL, t.XBL), t.YB)
        self.m_max = (max(t.XTR, t.XBR), t.YT)

class Portal:
    def __init__(self, p1: Point2D, p2: Point2D, a: AABB, b: AABB):
        self.p1 = p1
        self.p2 = p2
        self.a = a
        self.b = b
        
class NavMesh:
    def __init__(self, pathing_maps):
        self.trapezoids: Dict[int, PathingTrapezoid] = {}
        self.portals: List[Portal] = []
        self.portal_graph: Dict[int, List[int]] = {}
        self.trap_id_to_layer: Dict[int, int] = {}         # trap id -> layer z
        self.layer_portals: Dict[int, List[PathingPortal]] = {}

        # Index data
        for layer in pathing_maps:
            z = layer.zplane
            traps = layer.trapezoids
            self.layer_portals[z] = layer.portals

            self.trapezoids.update({t.id: t for t in traps})
            self.trap_id_to_layer.update({t.id: z for t in traps})

        self.create_all_local_portals()
        self.create_all_cross_layer_portals()
        
    def get_adjacent_side(self, a: PathingTrapezoid, b: PathingTrapezoid) -> Optional[str]:
        if abs(a.YB - b.YT) < 1.0: return 'bottom_top'
        if abs(a.YT - b.YB) < 1.0: return 'top_bottom'
        if abs(a.XBR - b.XBL) < 1.0: return 'right_left'
        if abs(a.XBL - b.XBR) < 1.0: return 'left_right'
        return None
    
    def create_portal(self, box1: AABB, box2: AABB, side: Optional[str]) -> bool:
        pt1, pt2 = box1.m_t, box2.m_t
        tolerance = 32.0

        def is_close(a, b): return abs(a - b) < tolerance

        if side == 'bottom_top':
            if not pt1.YB == pt2.YT:
                return False
            x_min = max(pt1.XBL, pt2.XBR)
            x_max = min(pt1.XBR, pt2.XBL)
            if is_close(x_max, x_min): return False
            p1, p2 = (x_min, pt1.YB), (x_max, pt1.YB)

        elif side == 'top_bottom':
            if not pt1.YT == pt2.YB:
                return False
            x_min = max(pt1.XTL, pt2.XTR)
            x_max = min(pt1.XTR, pt2.XTL)
            if is_close(x_max, x_min): return False
            p1, p2 = (x_min, pt1.YT), (x_max, pt1.YT)

        elif side == 'left_right':
            if not pt1.XTR == pt2.XTL:
                return False
            y_min = max(pt1.YT, pt2.YT)
            y_max = min(pt1.YB, pt2.YB)
            if is_close(y_max, y_min): return False
            p1, p2 = (pt1.XTR, y_min), (pt1.XBR, y_max)

        elif side == 'right_left':
            if not pt1.XTL == pt2.XTR:
                return False
            y_min = max(pt1.YT, pt2.YT)
            y_max = min(pt1.YB, pt2.YB)
            if is_close(y_max, y_min): return False
            p1, p2 = (pt1.XTL, y_min), (pt1.XBL, y_max)

        elif side is None:
            # Fallback: center line between boxes
            p1 = ((pt1.XTL + pt1.XTR) / 2, (pt1.YT + pt1.YB) / 2)
            p2 = ((pt2.XTL + pt2.XTR) / 2, (pt2.YT + pt2.YB) / 2)

        else:
            return False

        _p1 = Point2D(int(p1[0]), int(p1[1]))
        _p2 = Point2D(int(p2[0]), int(p2[1]))
        self.portals.append(Portal(_p1, _p2, box1, box2))
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
                        
    def touching(self, a: AABB, b: AABB, vert_tol: float = 100.2, horiz_tol: float = 100.6) -> bool:
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

                        
    def create_all_cross_layer_portals(self):
        from collections import defaultdict

        portal_groups = defaultdict(lambda: defaultdict(list))  # pair_index → zplane → List[Trap]

        # Step 1: group by pair_index and zplane
        for z, portal_list in self.layer_portals.items():
            for p in portal_list:
                for trap_id in p.trapezoid_indices:
                    trap = self.trapezoids.get(trap_id)
                    if not trap:
                        continue
                    portal_groups[p.pair_index][z].append(trap)

        # Step 2: only test across zplane groups
        for zplane_map in portal_groups.values():
            zplanes = list(zplane_map.keys())
            if len(zplanes) < 2:
                continue  # only one side present

            # For each pair of zplanes (usually just 2)
            for i in range(len(zplanes)):
                for j in range(i + 1, len(zplanes)):
                    zi, zj = zplanes[i], zplanes[j]
                    traps_i = zplane_map[zi]
                    traps_j = zplane_map[zj]

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
    
    def find_trapezoid_id_by_coord(self, point:  Tuple[float, float]) -> Optional[int]:
        x, y = point
        for t in self.trapezoids.values():
            if y > t.YT or y < t.YB:
                continue
            ratio = (y - t.YB) / (t.YT - t.YB) if t.YT != t.YB else 0
            left_x = t.XBL + (t.XTL - t.XBL) * ratio
            right_x = t.XBR + (t.XTR - t.XBR) * ratio
            if left_x <= x <= right_x:
                return t.id
        return None
    
    def has_line_of_sight(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> bool:
        """
        Checks if there's a safe line of sight between two trapezoid centers.
        Applies internal margin and adjustment to stay within walkable bounds.
        """
        margin = 100
        steps = int(math.dist(p1, p2) / 100) + 1

        trapezoids = self.trapezoids.values()

        for i in range(1, steps):
            t = i / steps
            x = p1[0] + (p2[0] - p1[0]) * t
            y = p1[1] + (p2[1] - p1[1]) * t

            trap_id = None
            for trap in trapezoids:
                if y > trap.YT or y < trap.YB:
                    continue
                height = trap.YT - trap.YB
                ratio = (y - trap.YB) / height if height != 0 else 0
                left_x = trap.XBL + (trap.XTL - trap.XBL) * ratio
                right_x = trap.XBR + (trap.XTR - trap.XBR) * ratio
                if left_x <= x <= right_x:
                    trap_id = trap.id
                    break

            if trap_id is None:
                return False

            trap = self.trapezoids[trap_id]
            height = trap.YT - trap.YB
            ratio = (y - trap.YB) / height if height != 0 else 0
            left_x = trap.XBL + (trap.XTL - trap.XBL) * ratio
            right_x = trap.XBR + (trap.XTR - trap.XBR) * ratio

            if x < left_x + margin or x > right_x - margin:
                return False

        return True
    
    def smooth_path_by_los(self, path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        if len(path) <= 2:
            return path

        result = [path[0]]
        i = 0
        while i < len(path) - 1:
            j = len(path) - 1
            while j > i + 1:
                if self.has_line_of_sight(path[i], path[j]):
                    break
                j -= 1
            result.append(path[j])
            i = j
        return result

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
            Py4GW.Console.Log("A-Star", "Invalid start or goal trapezoid", Py4GW.Console.MessageType.Error)
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
        self.navmesh: Optional[NavMesh] = None
        self.load_time: float = 0.0
        self.is_ready: bool = False
        self.pathing_map_cache: dict[tuple[int, ...], NavMesh] = {}
        self._initialized = True

    def _get_group_key(self, map_id: int) -> tuple[int, ...]:
        for group in PATHING_MAP_GROUPS:
            if map_id in group:
                return tuple(sorted(group))
        return (map_id,)  # Default: treat each unknown map_id as its own group

    def load_pathing_maps(self):
        import time
        map_id = PyMap.PyMap().map_id.ToInt()
        group_key = self._get_group_key(map_id)

        # Reuse preprocessed navmesh if available
        if group_key in self.pathing_map_cache:
            self.navmesh = self.pathing_map_cache[group_key]
            self.is_ready = True
            yield
            return

        # First-time load and processing
        start_time = time.time()
        yield  # allow UI to refresh

        pathing_maps = PyPathing.get_pathing_maps()
        navmesh = NavMesh(pathing_maps)
        self.pathing_map_cache[group_key] = navmesh
        self.navmesh = navmesh

        yield  # allow next frame

        self.load_time = time.time() - start_time
        self.is_ready = True

    def get_path(self, start: Tuple[float, float], goal: Tuple[float, float]):
        """
        Returns the raw path including exact start and goal positions.
        """
        yield
        if not self.navmesh:
            yield
            return []
        astar = AStar(self.navmesh)
        if astar.search(start, goal):
            yield
            return astar.get_path()
        return []

