import Py4GW
from Py4GWCoreLib import *
import heapq
import math
from typing import List, Dict, Tuple, Optional

MODULE_NAME = "A-Star test module"

class PathingTrapezoid:
    id: int
    XTL: float
    XTR: float
    YT: float
    XBL: float
    XBR: float
    YB: float
    portal_left: int
    portal_right: int
    neighbor_ids: List[int]

Point2D = Tuple[float, float]

def IsOnPathingTrapezoid(trap: PathingTrapezoid, point: Point2D) -> bool:
    x, y = point
    if y > trap.YT or y < trap.YB:
        return False

    ratio = (y - trap.YB) / (trap.YT - trap.YB) if trap.YT != trap.YB else 0
    left_x = trap.XBL + (trap.XTL - trap.XBL) * ratio
    right_x = trap.XBR + (trap.XTR - trap.XBR) * ratio
    return left_x <= x <= right_x

def Touching(t1: PathingTrapezoid, t2: PathingTrapezoid) -> bool:
    """
    Returns True if two trapezoids share a common vertical or horizontal side.
    This replicates the logic of adjacency checks used for proper neighbor validation.
    """

    # Helper to check if two Y ranges overlap
    def y_overlap(y1_top, y1_bot, y2_top, y2_bot):
        return not (y1_bot < y2_top or y2_bot < y1_top)

    # Helper to check if two X ranges overlap
    def x_overlap(x1_left, x1_right, x2_left, x2_right):
        return not (x1_right < x2_left or x2_right < x1_left)

    # Vertical side match (left or right)
    if abs(t1.XTL - t2.XTR) < 1e-4 and abs(t1.XBL - t2.XBR) < 1e-4:
        if y_overlap(t1.YT, t1.YB, t2.YT, t2.YB):
            return True
    if abs(t1.XTR - t2.XTL) < 1e-4 and abs(t1.XBR - t2.XBL) < 1e-4:
        if y_overlap(t1.YT, t1.YB, t2.YT, t2.YB):
            return True

    # Horizontal side match (top or bottom)
    if abs(t1.YT - t2.YB) < 1e-4:
        if x_overlap(min(t1.XTL, t1.XTR), max(t1.XTL, t1.XTR),
                     min(t2.XBL, t2.XBR), max(t2.XBL, t2.XBR)):
            return True
    if abs(t1.YB - t2.YT) < 1e-4:
        if x_overlap(min(t1.XBL, t1.XBR), max(t1.XBL, t1.XBR),
                     min(t2.XTL, t2.XTR), max(t2.XTL, t2.XTR)):
            return True

    return False


class NavMesh:
    def __init__(self, pathing_maps):
        self.pathing_maps = pathing_maps
        self.trapezoids_by_id: Dict[int, PathingTrapezoid] = {}
        self.centers: Dict[int, Point2D] = {}
        self.layer_by_id: Dict[int, int] = {}
        self.neighbors: Dict[int, List[int]] = {}

        # Load all trapezoids and engine-provided neighbor data
        for layer in pathing_maps:
            z = layer.zplane
            for t in layer.trapezoids:
                self.trapezoids_by_id[t.id] = t
                self.layer_by_id[t.id] = z
                self.centers[t.id] = self._compute_center(t)
                self.neighbors[t.id] = list(t.neighbor_ids)  # Copy original engine neighbors

        # Group portals by pair_index (including 0xFFFFFFFF as a valid base group)
        
        portal_groups: Dict[int, List[int]] = defaultdict(list)

        for layer in self.pathing_maps:
            for portal in layer.portals:
                for tid in portal.trapezoid_indices:
                    portal_groups[portal.pair_index].append(tid)

        # Link all trapezoids within each portal group
        for group in portal_groups.values():
            for i in range(len(group)):
                t1 = self.trapezoids_by_id.get(group[i])
                if t1 is None:
                    continue
                for j in range(len(group)):
                    if i == j:
                        continue
                    t2 = self.trapezoids_by_id.get(group[j])
                    if t2 is None:
                        continue
                    if t2.id not in self.neighbors[t1.id] and Touching(t1, t2):
                        self.neighbors[t1.id].append(t2.id)



    def _compute_center(self, t: PathingTrapezoid) -> Point2D:
        cx = (t.XTL + t.XTR + t.XBL + t.XBR) / 4
        cy = (t.YT + t.YB) / 2
        return (cx, cy)

    def get_neighbors(self, t_id: int) -> List[int]:
        return self.neighbors.get(t_id, [])

    def get_position(self, t_id: int) -> Point2D:
        return self.centers[t_id]

    def get_layer(self, t_id: int) -> int:
        return self.layer_by_id.get(t_id, 0)

    def has_trapezoid(self, t_id: int) -> bool:
        return t_id in self.trapezoids_by_id

    def find_trapezoid_id_by_coord(self, point: Point2D) -> Optional[int]:
        for t_id, trap in self.trapezoids_by_id.items():
            if IsOnPathingTrapezoid(trap, point):
                return t_id
        return None

    def get_trapezoid_by_coord(self, point: Point2D) -> Optional[PathingTrapezoid]:
        for trap in self.trapezoids_by_id.values():
            if IsOnPathingTrapezoid(trap, point):
                return trap
        return None

    def get_all_trapezoids_by_coord(self, point: Point2D) -> List[PathingTrapezoid]:
        return [trap for trap in self.trapezoids_by_id.values() if IsOnPathingTrapezoid(trap, point)]
    
    def debug_filtered_trapezoids(self, filter_ids: List[int]):
        print("[Debug] === Trapezoid Filter Report ===")
        for tid in filter_ids:
            if tid not in self.trapezoids_by_id:
                print(f"[Debug] Trapezoid {tid} not found.")
                continue

            engine_neighbors = self.trapezoids_by_id[tid].neighbor_ids
            all_neighbors = self.neighbors.get(tid, [])
            added_neighbors = [n for n in all_neighbors if n not in engine_neighbors]

            trap = self.trapezoids_by_id[tid]
            cx, cy = self.centers[tid]
            z = self.layer_by_id.get(tid, 0)

            print(f"[Debug] Trapezoid {tid}")
            print(f"  Center: ({cx:.2f}, {cy:.2f}) Z: {z}")
            print(f"  Engine neighbors: {engine_neighbors}")
            print(f"  Total neighbors : {all_neighbors}")
            print(f"  Added neighbors : {added_neighbors}")
            print(f"  Portal Left ID  : {trap.portal_left}")
            print(f"  Portal Right ID : {trap.portal_right}")

        print("[Debug] === Matching Portals ===")
        for layer in self.pathing_maps:
            for portal in layer.portals:
                if any(tid in portal.trapezoid_indices for tid in filter_ids):
                    print(f"[Debug] Portal {portal.pair_index}: {portal.trapezoid_indices}")


class AStarNode:
    def __init__(self, node_id: int, g: float, f: float, parent: Optional[int]):
        self.id = node_id
        self.g = g
        self.f = f
        self.parent = parent

    def __lt__(self, other):
        return self.f < other.f

class AStar:
    def __init__(self, navmesh: NavMesh):
        self.navmesh = navmesh
        self.path: List[int] = []
        self.cost: float = 0.0

    def heuristic(self, a: int, b: int) -> float:
        ax, ay = self.navmesh.get_position(a)
        bx, by = self.navmesh.get_position(b)
        return math.hypot(bx - ax, by - ay)


    def search(self, start_id: int, goal_id: int) -> bool:
        print(f"[A*] Start ID: {start_id}, Goal ID: {goal_id}")

        if not (self.navmesh.has_trapezoid(start_id) and self.navmesh.has_trapezoid(goal_id)):
            print("[A*] Invalid start or goal ID")
            return False

        open_list: List[AStarNode] = []
        heapq.heappush(open_list, AStarNode(start_id, 0.0, self.heuristic(start_id, goal_id), None))
        came_from: Dict[int, int] = {}
        cost_so_far: Dict[int, float] = {start_id: 0.0}
        visited = set()

        while open_list:
            current = heapq.heappop(open_list)
            visited.add(current.id)

            print(f"[A*] Visiting: {current.id} (g={current.g:.2f}, f={current.f:.2f})")

            if current.id == goal_id:
                self._reconstruct_path(came_from, goal_id)
                self.cost = current.g
                print(f"[A*] Path found: {len(self.path)} steps, total cost = {self.cost:.2f}")
                return True

            neighbors = self.navmesh.get_neighbors(current.id)
            print(f"[A*]   Neighbors of {current.id}: {neighbors}")

            for neighbor in neighbors:
                if neighbor in visited:
                    continue

                new_cost = cost_so_far[current.id] + self.heuristic(current.id, neighbor)
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self.heuristic(neighbor, goal_id)
                    heapq.heappush(open_list, AStarNode(neighbor, new_cost, priority, current.id))
                    came_from[neighbor] = current.id
                    print(f"[A*]     Queuing neighbor {neighbor} (g={new_cost:.2f}, f={priority:.2f})")

        print("[A*] No path found")
        return False

    def _reconstruct_path(self, came_from: Dict[int, int], end_id: int):
        path = [end_id]
        while end_id in came_from:
            end_id = came_from[end_id]
            path.append(end_id)
        path.reverse()
        self.path = path

    def get_path(self) -> List[int]:
        return self.path

    def get_cost(self) -> float:
        return self.cost

    
def has_line_of_sight(navmesh: NavMesh, id1: int, id2: int) -> bool:
    # Sample many points between center of trapezoid A and B
    # For each, check IsOnPathingTrapezoid for some trapezoid (or valid polygon)
    p1 = navmesh.get_position(id1)
    p2 = navmesh.get_position(id2)
    steps = int(math.dist(p1, p2) / 100) + 1
    for i in range(1, steps):
        t = i / steps
        x = p1[0] + (p2[0] - p1[0]) * t
        y = p1[1] + (p2[1] - p1[1]) * t
        if navmesh.find_trapezoid_id_by_coord((x, y)) is None:
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

def debug_portal_connections(navmesh: NavMesh):
    print("[DEBUG] Portal Connectivity Check")
    for layer_index, layer in enumerate(navmesh.pathing_maps):
        print(f"\n[Layer {layer_index}] Total Portals: {len(layer.portals)}")
        for idx, portal in enumerate(layer.portals):
            t_ids = portal.trapezoid_indices
            print(f"  Portal {idx} (Trapezoids: {t_ids})")

            for tid in t_ids:
                if tid not in navmesh.trapezoids_by_id:
                    print(f"    Trapezoid ID {tid} not found in layer!")
                else:
                    trap = navmesh.trapezoids_by_id[tid]
                    print(f"    Trapezoid {tid} neighbors: {trap.neighbor_ids}")


# Runtime globals
pathing_maps = []
navmesh = None
astar = None
path_result = []
start_pos = (-3000.0, 9500.0)
goal_pos = (5000.0, -2500.0)
path_result_points = []

def main():
    global pathing_maps, navmesh, astar, path_result, start_pos, goal_pos, path_result_points
    try:
        if PyImGui.begin("Dx Colors", PyImGui.WindowFlags.AlwaysAutoResize): 
            if PyImGui.button("get pathing map"):
                pathing_maps = Map.Pathing.GetPathingMaps()
                navmesh = NavMesh(pathing_maps)
                if navmesh:
                    filter_ids = [401, 2358, 723]
                    navmesh.debug_filtered_trapezoids(filter_ids)

            if navmesh:
                start_pos = Player.GetXY()
                goal_pos = (0.0, 0.0)
                

                if PyImGui.button("Run A*"):
                    start_id = navmesh.find_trapezoid_id_by_coord(start_pos)
                    goal_id = navmesh.find_trapezoid_id_by_coord(goal_pos)


                    if start_id is None or goal_id is None:
                        Py4GW.Console.Log(MODULE_NAME, "Invalid start/goal position", Py4GW.Console.MessageType.Warning)
                    else:
                        #print(f"Start ID: {start_id}, Goal ID: {goal_id}")
                        #print(f"Start neighbors: {navmesh.get_neighbors(start_id)}")
                        #print(f"Goal neighbors: {navmesh.get_neighbors(goal_id)}")
                        
                        astar = AStar(navmesh)
                        if astar.search(start_id, goal_id):
                            path_result = astar.get_path()
                            path_result = smooth_path_by_los(path_result, navmesh)
                            center_points = [navmesh.get_position(tid) for tid in path_result]

                            # Apply curve smoothing
                            path_result_points = chaikin_smooth_path(center_points, iterations=2)
                            Py4GW.Console.Log(MODULE_NAME, f"Path found: {len(path_result)} steps", Py4GW.Console.MessageType.Success)
                        else:
                            Py4GW.Console.Log(MODULE_NAME, "No path found", Py4GW.Console.MessageType.Warning)

                
                if path_result_points and len(path_result_points) >= 2:
                    for i in range(len(path_result_points) - 1):
                        from_x, from_y = path_result_points[i]
                        to_x, to_y = path_result_points[i + 1]

                        from_z = DXOverlay.FindZ(from_x, from_y) - 125
                        to_z = DXOverlay.FindZ(to_x, to_y) - 125

                        DXOverlay().DrawLine3D(
                            from_x, from_y, from_z,
                            to_x, to_y, to_z,
                            Color(255, 255, 0, 255).to_dx_color(),  # yellow
                            False
                        )


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
