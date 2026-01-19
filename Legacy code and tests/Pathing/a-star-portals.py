import Py4GW
from Py4GWCoreLib import *
import heapq
import math
from typing import List, Tuple, Optional, Dict
from Py4GWCoreLib.native_src.context.MapContext import PortalStruct, PathingTrapezoidStruct

PathingTrapezoid = PathingTrapezoidStruct
PathingPortal = PortalStruct
MODULE_NAME = "Portal Pathfinding"

class AABB:
    def __init__(self, t: PathingTrapezoid):
        self.m_t = t
        self.m_min = (min(t.XTL, t.XBL), t.YB)
        self.m_max = (max(t.XTR, t.XBR), t.YT)

class Portal:
    def __init__(self, p1: Tuple[float, float], p2: Tuple[float, float], a: AABB, b: AABB):
        self.p1 = p1
        self.p2 = p2
        self.a = a
        self.b = b
        
def Touching(a: AABB, b: AABB, tolerance: float = 0.1) -> bool:
    # Same vertical alignment (top-bottom or bottom-top)
    if abs(a.m_t.YB - b.m_t.YT) < tolerance or abs(a.m_t.YT - b.m_t.YB) < tolerance:
        # Overlap horizontally
        left_a = min(a.m_t.XBL, a.m_t.XTL)
        right_a = max(a.m_t.XBR, a.m_t.XTR)
        left_b = min(b.m_t.XBL, b.m_t.XTL)
        right_b = max(b.m_t.XBR, b.m_t.XTR)
        if right_a >= left_b and right_b >= left_a:
            return True

    # Same horizontal alignment (left-right or right-left)
    if abs(a.m_t.XBR - b.m_t.XBL) < tolerance or abs(a.m_t.XBL - b.m_t.XBR) < tolerance:
        # Overlap vertically
        top_a = max(a.m_t.YT, a.m_t.YB)
        bottom_a = min(a.m_t.YT, a.m_t.YB)
        top_b = max(b.m_t.YT, b.m_t.YB)
        bottom_b = min(b.m_t.YT, b.m_t.YB)
        if top_a >= bottom_b and top_b >= bottom_a:
            return True

    return False


class NavMesh:
    def __init__(self, pathing_maps):
        self.trapezoids: Dict[int, PathingTrapezoid] = {}
        self.aabbs: List[AABB] = []
        self.portals: List[Portal] = []
        self.portal_graph: Dict[int, List[int]] = {}
        self.aabbs_per_layer: Dict[int, List[AABB]] = {}  # zplane -> List of AABBs
        self.trap_id_to_layer: Dict[int, int] = {}         # trap id -> layer z
        self.layer_portals: Dict[int, List[PathingPortal]] = {}

        # Index data
        for layer in pathing_maps:
            z = layer.zplane
            self.aabbs_per_layer[z] = []
            self.layer_portals[z] = layer.portals

            for trap in layer.trapezoids:
                self.trapezoids[trap.id] = trap
                self.trap_id_to_layer[trap.id] = z
                aabb = AABB(trap)
                self.aabbs.append(aabb)
                self.aabbs_per_layer[z].append(aabb)

        self.create_all_local_portals()
        self.create_all_cross_layer_portals()

    def create_all_local_portals(self):
        for aabbs in self.aabbs_per_layer.values():
            for a in aabbs:
                for b in aabbs:
                    if a == b:
                        continue
                    if b.m_t.id not in a.m_t.neighbor_ids:
                        continue  # Only declared neighbors
                    side = self.get_adjacent_side(a.m_t, b.m_t)
                    if side:
                        self.create_portal(a, b, side)

    def create_all_cross_layer_portals(self):
        portal_groups: Dict[int, List[Tuple[int, PathingTrapezoid]]] = {}

        for z, portal_list in self.layer_portals.items():
            for p in portal_list:
                for trap_id in p.trapezoid_indices:
                    trap = self.trapezoids.get(trap_id)
                    if not trap:
                        continue
                    portal_groups.setdefault(p.pair_index, []).append((z, trap))

        for pair_index, entries in portal_groups.items():
            for i in range(len(entries)):
                zi, ti = entries[i]
                ai = AABB(ti)
                for j in range(i + 1, len(entries)):
                    zj, tj = entries[j]
                    aj = AABB(tj)
                    if Touching(ai, aj):  # Use actual Touching logic
                        self.create_portal(ai, aj, None)  # no geometric side assumed

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

        self.portals.append(Portal(p1, p2, box1, box2))
        self.portal_graph.setdefault(pt1.id, []).append(pt2.id)
        self.portal_graph.setdefault(pt2.id, []).append(pt1.id)
        return True

    def get_neighbors(self, t_id: int) -> List[int]:
        return self.portal_graph.get(t_id, [])

    def get_position(self, t_id: int) -> Tuple[float, float]:
        t = self.trapezoids[t_id]
        cx = (t.XTL + t.XTR + t.XBL + t.XBR) / 4
        cy = (t.YT + t.YB) / 2
        return (cx, cy)

    def find_trapezoid_id_by_coord(self, point: Tuple[float, float]) -> Optional[int]:
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
        self.path: List[int] = []

    def heuristic(self, a: int, b: int) -> float:
        ax, ay = self.navmesh.get_position(a)
        bx, by = self.navmesh.get_position(b)
        return math.hypot(bx - ax, by - ay)

    def search(self, start_id: int, goal_id: int) -> bool:
        open_list: List[AStarNode] = []
        heapq.heappush(open_list, AStarNode(start_id, 0, self.heuristic(start_id, goal_id)))
        came_from: Dict[int, int] = {}
        cost_so_far: Dict[int, float] = {start_id: 0}

        while open_list:
            current = heapq.heappop(open_list)
            if current.id == goal_id:
                self._reconstruct(came_from, goal_id)
                return True

            for neighbor in self.navmesh.get_neighbors(current.id):
                new_cost = cost_so_far[current.id] + self.heuristic(current.id, neighbor)
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self.heuristic(neighbor, goal_id)
                    heapq.heappush(open_list, AStarNode(neighbor, new_cost, priority, current.id))
                    came_from[neighbor] = current.id

        return False

    def _reconstruct(self, came_from: Dict[int, int], end_id: int):
        self.path = [end_id]
        while end_id in came_from:
            end_id = came_from[end_id]
            self.path.append(end_id)
        self.path.reverse()

    def get_path(self) -> List[int]: return self.path


def has_line_of_sight(navmesh: NavMesh, id1: int, id2: int) -> bool:
    """
    Checks if there's a safe line of sight between two trapezoid centers.
    Applies internal margin and adjustment to stay within walkable bounds.
    """
    # Configuration (internal only)
    margin = 100         # Trigger if too close to trapezoid edge
    adjust_amount = 100  # Shift left/right to stay safe

    p1 = navmesh.get_position(id1)
    p2 = navmesh.get_position(id2)
    steps = int(math.dist(p1, p2) / 100) + 1

    for i in range(1, steps):
        t = i / steps
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        pos = (x, y)

        trap_id = navmesh.find_trapezoid_id_by_coord(pos)
        if trap_id is None:
            return False

        trap = navmesh.trapezoids[trap_id]

        ratio = (y - trap.YB) / (trap.YT - trap.YB) if trap.YT != trap.YB else 0
        left_x = trap.XBL + (trap.XTL - trap.XBL) * ratio
        right_x = trap.XBR + (trap.XTR - trap.XBR) * ratio

        if x < left_x + margin:
            x += adjust_amount
        elif x > right_x - margin:
            x -= adjust_amount

        if not (left_x + margin <= x <= right_x - margin):
            return False

    return True




def smooth_path_by_los(path: List[int], navmesh: NavMesh) -> List[int]:
    if len(path) <= 2:
        return path

    result = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1:
            if has_line_of_sight(navmesh, path[i], path[j]):
                break
            j -= 1
        result.append(path[j])
        i = j
    return result

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



# Globals for testing
navmesh = None
astar = None
path = []
path_result_points = []

# Global variables for each variant
raw_path_points = []
los_path_points = []
los_chaikin_path_points = []
chaikin_only_path_points = []

def main():
    def draw_path(points, rgba):
        if points and len(points) >= 2:
            color = Color(*rgba).to_dx_color()
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                z1 = DXOverlay.FindZ(x1, y1) - 125
                z2 = DXOverlay.FindZ(x2, y2) - 125
                DXOverlay().DrawLine3D(x1, y1, z1, x2, y2, z2, color, False)
            
    global navmesh, astar
    global raw_path_points, los_path_points, los_chaikin_path_points, chaikin_only_path_points

    if PyImGui.begin("Pathing Test", PyImGui.WindowFlags.AlwaysAutoResize):
        if PyImGui.button("Load Maps"):
            navmesh = NavMesh(Map.Pathing.GetPathingMaps())

        if navmesh:
            start_pos = Player.GetXY()
            goal_pos = (0, 0)

            if PyImGui.button("Search Path (Raw A*)"):
                astar = AStar(navmesh)
                start = navmesh.find_trapezoid_id_by_coord(start_pos)
                goal = navmesh.find_trapezoid_id_by_coord(goal_pos)
                if start and goal and astar.search(start, goal):
                    ids = astar.get_path()
                    raw_path_points = [navmesh.get_position(tid) for tid in ids]

            if PyImGui.button("Search Path + LOS"):
                astar = AStar(navmesh)
                start = navmesh.find_trapezoid_id_by_coord(start_pos)
                goal = navmesh.find_trapezoid_id_by_coord(goal_pos)
                if start and goal and astar.search(start, goal):
                    ids = smooth_path_by_los(astar.get_path(), navmesh)
                    los_path_points = [navmesh.get_position(tid) for tid in ids]

            if PyImGui.button("Search Path + LOS + Chaikin"):
                astar = AStar(navmesh)
                start = navmesh.find_trapezoid_id_by_coord(start_pos)
                goal = navmesh.find_trapezoid_id_by_coord(goal_pos)
                if start and goal and astar.search(start, goal):
                    ids = smooth_path_by_los(astar.get_path(), navmesh)
                    pts = [navmesh.get_position(tid) for tid in ids]
                    los_chaikin_path_points = chaikin_smooth_path(pts, iterations=2)

            if PyImGui.button("Search Path + Chaikin Only"):
                astar = AStar(navmesh)
                start = navmesh.find_trapezoid_id_by_coord(start_pos)
                goal = navmesh.find_trapezoid_id_by_coord(goal_pos)
                if start and goal and astar.search(start, goal):
                    ids = astar.get_path()
                    pts = [navmesh.get_position(tid) for tid in ids]
                    chaikin_only_path_points = chaikin_smooth_path(pts, iterations=2)

        PyImGui.end()

    # Draw all variants in different colors
    draw_path(raw_path_points, (255, 255, 0, 255))         # Yellow
    draw_path(los_path_points, (0, 255, 255, 255))          # Cyan
    draw_path(los_chaikin_path_points, (0, 255, 0, 255))    # Green
    draw_path(chaikin_only_path_points, (255, 0, 255, 255)) # Magenta






if __name__ == "__main__":
    main()
