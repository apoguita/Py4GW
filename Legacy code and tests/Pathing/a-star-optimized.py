import Py4GW
from Py4GWCoreLib import *
from Py4GWCoreLib.native_src.context.MapContext import PathingTrapezoidStruct
import heapq
import math
from typing import List, Tuple, Optional, Dict


PathingTrapezoid = PathingTrapezoidStruct
PathingPortal = PyPathing.Portal
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
 


def Touching(a: AABB, b: AABB, vert_tol: float = 100.2, horiz_tol: float = 100.6) -> bool:
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



class NavMesh:
    def __init__(self, pathing_maps):
        self.trapezoids: Dict[int, PathingTrapezoid] = {}
        self.aabbs: List[AABB] = []
        self.portals: List[Portal] = []
        self.portal_graph: Dict[int, List[int]] = {}
        self.aabbs_per_layer: Dict[int, List[AABB]] = {}  # zplane -> List of AABBs
        self.trap_id_to_layer: Dict[int, int] = {}         # trap id -> layer z
        self.layer_portals: Dict[int, List[PathingPortal]] = {}

        # New: quadrant-based subnodes
        self.subnodes: Dict[Tuple[int, int], Tuple[float, float]] = {}  # (trap_id, quadrant_id) -> position
        self.subnode_neighbors: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
        
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
                
                #self._generate_subnodes(trap)

        self.create_all_local_portals()
        self.create_all_cross_layer_portals()
        #self._generate_subnode_links()

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
                        
    def _generate_subnodes(self, trap: PathingTrapezoid):
        centers = self._get_quadrant_centers(trap)
        for i, center in enumerate(centers):
            self.subnodes[(trap.id, i)] = center
            
    def _get_quadrant_centers(self, t: PathingTrapezoid) -> List[Tuple[float, float]]:
        if t.YT == t.YB:
            # Degenerate height, fallback to midpoint box
            cx = (t.XTL + t.XTR + t.XBL + t.XBR) / 4
            cy = t.YT
            return [
                (cx - 16, cy + 16),
                (cx + 16, cy + 16),
                (cx - 16, cy - 16),
                (cx + 16, cy - 16),
            ]

        mid_y = (t.YT + t.YB) / 2
        top_mid_y = (t.YT + mid_y) / 2
        bottom_mid_y = (t.YB + mid_y) / 2

        # Vertical span
        height = t.YT - t.YB

        # Avoid division by zero (already checked above, but safe)
        if height == 0:
            height = 1e-5

        # Interpolate left/right edges
        def interpolate(x_top, x_bottom, y_target):
            return x_top + (x_bottom - x_top) * ((t.YT - y_target) / height)

        left_top_x = interpolate(t.XTL, t.XBL, top_mid_y)
        left_bottom_x = interpolate(t.XTL, t.XBL, bottom_mid_y)
        right_top_x = interpolate(t.XTR, t.XBR, top_mid_y)
        right_bottom_x = interpolate(t.XTR, t.XBR, bottom_mid_y)

        mid_top_x = (t.XTL + t.XTR) / 2
        mid_bottom_x = (t.XBL + t.XBR) / 2
        mid_x = (mid_top_x + mid_bottom_x) / 2

        return [
            ((left_top_x + mid_x) / 2, top_mid_y),       # 0 - Top-left
            ((right_top_x + mid_x) / 2, top_mid_y),      # 1 - Top-right
            ((left_bottom_x + mid_x) / 2, bottom_mid_y), # 2 - Bottom-left
            ((right_bottom_x + mid_x) / 2, bottom_mid_y) # 3 - Bottom-right
        ]

            
    def _generate_subnode_links(self):
        # Intra-trapezoid connections
        for (trap_id, q1), p1 in self.subnodes.items():
            for q2 in range(4):
                if q1 == q2:
                    continue
                self.subnode_neighbors.setdefault((trap_id, q1), []).append((trap_id, q2))

        # Inter-trapezoid connections (to neighbor trapezoids' subnodes)
        for trap_id, trap in self.trapezoids.items():
            for neighbor_id in trap.neighbor_ids:
                for q1 in range(4):
                    for q2 in range(4):
                        self.subnode_neighbors.setdefault((trap_id, q1), []).append((neighbor_id, q2))

    def get_subnodes(self, trap_id: int) -> List[Tuple[int, int]]:
        return [(trap_id, i) for i in range(4)]

    def get_subnode_position(self, trap_id: int, quadrant_id: int) -> Tuple[float, float]:
        return self.subnodes[(trap_id, quadrant_id)]

    def get_subnode_neighbors(self, node_id: Tuple[int, int]) -> List[Tuple[int, int]]:
        return self.subnode_neighbors.get(node_id, [])

    def find_closest_subnode(self, point: Tuple[float, float]) -> Optional[Tuple[int, int]]:
        trap_id = self.find_trapezoid_id_by_coord(point)
        if trap_id is None:
            return None
        min_dist = float("inf")
        best = None
        for i in range(4):
            pid = (trap_id, i)
            pos = self.subnodes[pid]
            dist = math.hypot(pos[0] - point[0], pos[1] - point[1])
            if dist < min_dist:
                min_dist = dist
                best = pid
        return best


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
                    
                    
        if not self.path:
            ConsoleLog("AStar", f"Path not found from {start_id} to {goal_id}", Console.MessageType.Warning)

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

def analyze_portals():
    from Py4GWCoreLib import Map
    pathing_maps = Map.Pathing.GetPathingMaps()

    print(f"[INFO] Total layers: {len(pathing_maps)}")

    portal_summary = {}
    total_portals = 0
    total_pairs = set()

    for layer in pathing_maps:
        z = layer.zplane
        print(f"\n=== Layer ZPlane: {z} ===")
        print(f"  Trapezoids: {len(layer.trapezoids)}")
        print(f"  Portals   : {len(layer.portals)}")

        for p in layer.portals:
            total_portals += 1
            total_pairs.add(p.pair_index)

            print(f"\n[Portal] pair_index={p.pair_index}")
            print(f"  trapezoid_indices={p.trapezoid_indices}")
            print(f"  left_layer_id={p.left_layer_id}  right_layer_id={p.right_layer_id}")
            print(f"  h0004={p.h0004}  count={p.count}")

            # Group by pair_index
            group = portal_summary.setdefault(p.pair_index, [])
            group.append({
                "zplane": z,
                "left_layer_id": p.left_layer_id,
                "right_layer_id": p.right_layer_id,
                "trapezoid_indices": p.trapezoid_indices,
                "h0004": p.h0004,
                "count": p.count
            })

    print(f"\n=== Summary ===")
    print(f"  Total portals      : {total_portals}")
    print(f"  Unique portal pairs: {len(total_pairs)}")

    print(f"\n=== Portal Pair Breakdown ===")
    for pair_index, entries in portal_summary.items():
        print(f"\n[Pair {pair_index}]")
        for entry in entries:
            print(f"  z={entry['zplane']}, traps={entry['trapezoid_indices']}, h0004={entry['h0004']}")

def debug_portal_connections():
    from Py4GWCoreLib import Map
    pathing_maps = Map.Pathing.GetPathingMaps()

    # Index all traps by id and store their zplane
    trap_by_id = {}
    trap_layer = {}
    for layer in pathing_maps:
        for trap in layer.trapezoids:
            trap_by_id[trap.id] = trap
            trap_layer[trap.id] = layer.zplane

    # Collect and group portals by pair_index
    pair_portals = {}
    for layer in pathing_maps:
        for portal in layer.portals:
            pair_portals.setdefault(portal.pair_index, []).append((layer.zplane, portal))

    print("\n=== Focused Portal Debug ===")
    for pair_index, portals in pair_portals.items():
        print(f"\n[PAIR {pair_index}] Total sides: {len(portals)}")

        all_traps = []
        for zplane, portal in portals:
            for trap_id in portal.trapezoid_indices:
                trap = trap_by_id.get(trap_id)
                if not trap:
                    print(f"  [!] Missing trapezoid {trap_id}")
                    continue
                cx = (trap.XTL + trap.XTR + trap.XBL + trap.XBR) / 4
                cy = (trap.YT + trap.YB) / 2
                print(f"  zplane={zplane} trap_id={trap.id}  center=({cx:.1f}, {cy:.1f})")
                all_traps.append((trap.id, zplane, cx, cy))

        if len(all_traps) == 2:
            id_a, z_a, xa, ya = all_traps[0]
            id_b, z_b, xb, yb = all_traps[1]
            dx = abs(xa - xb)
            dy = abs(ya - yb)
            dz = abs(z_a - z_b)
            print(f"  ΔX={dx:.1f} ΔY={dy:.1f} ZPlanes={z_a}↔{z_b}")
        elif len(all_traps) > 2:
            print(f"  [!] Portal connects more than 2 traps — complex case")

    
def debug_cross_layer_portals_near(navmesh: NavMesh, center: Tuple[float, float], radius: float = 1000):
    print("\n--- DEBUG: Cross-layer portal linkage check ---\n")
    px, py = center

    def in_radius(trap: PathingTrapezoid) -> bool:
        cx = (trap.XTL + trap.XTR + trap.XBL + trap.XBR) / 4
        cy = (trap.YT + trap.YB) / 2
        dx, dy = cx - px, cy - py
        return dx * dx + dy * dy <= radius * radius

    portal_groups: Dict[int, List[Tuple[int, PathingTrapezoid]]] = {}

    for z, portals in navmesh.layer_portals.items():
        for portal in portals:
            for trap_id in portal.trapezoid_indices:
                trap = navmesh.trapezoids.get(trap_id)
                if not trap or not in_radius(trap):
                    continue
                portal_groups.setdefault(portal.pair_index, []).append((z, trap))

    if not portal_groups:
        print("No portal trapezoids found near the player.")
        return

    for pair_index, traps in portal_groups.items():
        print(f"\nPortal Pair {pair_index}: {len(traps)} entries")

        for z, t in traps:
            print(f" - Trapezoid ID: {t.id}, Z: {z}")
            print(f"   Coords: XTL={t.XTL}, XTR={t.XTR}, XBL={t.XBL}, XBR={t.XBR}, YT={t.YT}, YB={t.YB}")
            print(f"   Neighbors: {t.neighbor_ids}")
        
        print("  Attempting linkage:")
        for i in range(len(traps)):
            zi, ti = traps[i]
            ai = AABB(ti)
            for j in range(i + 1, len(traps)):
                zj, tj = traps[j]
                aj = AABB(tj)
                print(f"    Trying {ti.id} ↔ {tj.id}: ", end="")
                if Touching(ai, aj):
                    print("✓ Touching → should be linked")
                else:
                    print("✗ NOT touching → no portal created")

    print("\n--- END DEBUG ---\n")
    
def debug_failed_cross_layer_portals_filtered(
    navmesh: 'NavMesh',
    player_pos: tuple[float, float],
    radius: float = 1000.0,
    max_pairs: int = 20
):
    """
    Debug failed portal linkages (Touching failure) near player.
    - Filters trapezoids in portal pairs by distance to `player_pos`.
    - Summarizes only portal pairs whose trapezoids are close and not touching.
    """
    from collections import defaultdict
    import math

    def distance(p1, p2):
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return math.hypot(dx, dy)

    print(f"[DEBUG] Checking failed portal linkages near player @ {player_pos}, radius = {radius}")
    print(f"[DEBUG] reached control point001")

    portal_groups = defaultdict(list)
    for z, portal_list in navmesh.layer_portals.items():
        for p in portal_list:
            for trap_id in p.trapezoid_indices:
                trap = navmesh.trapezoids.get(trap_id)
                if not trap:
                    continue
                cx = (trap.XBL + trap.XBR + trap.XTL + trap.XTR) / 4
                cy = (trap.YT + trap.YB) / 2
                if distance((cx, cy), player_pos) <= radius:
                    portal_groups[p.pair_index].append((z, trap))
    print(f"[DEBUG] reached control point002 - Found {len(portal_groups)} portal pairs near player")

    count = 0
    for pair_index, entries in portal_groups.items():
        if count >= max_pairs:
            break
        if len(entries) < 2:
            continue

        printed_header = False
        for i in range(len(entries)):
            zi, ti = entries[i]
            ai = AABB(ti)
            for j in range(i + 1, len(entries)):
                zj, tj = entries[j]
                aj = AABB(tj)

                if Touching(ai, aj):
                    continue

                if not printed_header:
                    print(f"\n[Group {pair_index}] Trapezoids near player not touching:")
                    printed_header = True

                print(f"  ✖ {ti.id} (Z={zi}) ↔ {tj.id} (Z={zj}) — Touching FAILED")

        count += 1

def LogTouchingFailureDeltasNearPlayer(player_pos: tuple[float, float], radius: float = 1000.0):
    from itertools import combinations

    layers = Map.Pathing.GetPathingMaps()
    all_trapezoids = [trap for layer in layers for trap in layer.trapezoids]

    print(f"[DEBUG] Evaluating touching deltas near player @ {player_pos}, radius = {radius}")

    def dist2(a: tuple[float, float], b: tuple[float, float]) -> float:
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

    def get_trap_center(t):
        # Approximate center as average of corners
        avg_x = (t.XTL + t.XTR + t.XBL + t.XBR) / 4
        avg_y = (t.YT + t.YB) / 2
        return (avg_x, avg_y)

    near = [
        t for t in all_trapezoids
        if dist2(get_trap_center(t), player_pos) <= radius * radius
    ]

    failure_deltas = []

    for t1, t2 in combinations(near, 2):
        a = AABB(t1)
        b = AABB(t2)
        if Touching(a, b):
            continue

        dy_topbot = min(abs(a.m_t.YB - b.m_t.YT), abs(a.m_t.YT - b.m_t.YB))
        dx_leftright = min(abs(a.m_t.XBR - b.m_t.XBL), abs(a.m_t.XBL - b.m_t.XBR))

        failure_deltas.append((dy_topbot, dx_leftright))

        print(f"[FAIL] {a.m_t.id} ↔ {b.m_t.id}")
        print(f"       ΔY (top-bottom) = {dy_topbot:.3f}")
        print(f"       ΔX (left-right) = {dx_leftright:.3f}")

    if failure_deltas:
        all_dy = [d[0] for d in failure_deltas]
        all_dx = [d[1] for d in failure_deltas]
        print(f"\n[SUMMARY] Vertical ΔY min/avg/max: {min(all_dy):.3f} / {sum(all_dy)/len(all_dy):.3f} / {max(all_dy):.3f}")
        print(f"[SUMMARY] Horizontal ΔX min/avg/max: {min(all_dx):.3f} / {sum(all_dx)/len(all_dx):.3f} / {max(all_dx):.3f}")
    else:
        print("[SUMMARY] No failed touching cases found.")



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

x,y = 0, 0

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
    global raw_path_points, los_path_points, los_chaikin_path_points, chaikin_only_path_points,x,y

    if PyImGui.begin("Pathing Test", PyImGui.WindowFlags.AlwaysAutoResize):
        if PyImGui.button("Analyze Portals"):
            analyze_portals()
            
        if PyImGui.button("Debug Portal Connections"):
            debug_portal_connections()
            
        
        if PyImGui.button("Load Maps"):
            navmesh = NavMesh(Map.Pathing.GetPathingMaps())

        if navmesh:
            start_pos = GLOBAL_CACHE.Player.GetXY()
        
            x = PyImGui.input_int("Start X", x)
            y = PyImGui.input_int("Start Y", y)
            goal_pos = (x, y)

            if PyImGui.button("Debug Cross-Layer Portals"):
                debug_cross_layer_portals_near(navmesh, start_pos, radius=1000)
                
            if PyImGui.button("Debug FAILED Cross-Layer Portals"):
                debug_failed_cross_layer_portals_filtered(navmesh, player_pos=start_pos, radius=1000)

            if PyImGui.button("Log Touching Failures Near Player"):
                LogTouchingFailureDeltasNearPlayer(player_pos=start_pos, radius=1000)    


            if PyImGui.button("Search Path (Raw A*)"):
                astar = AStar(navmesh)
                start = navmesh.find_trapezoid_id_by_coord(start_pos)
                goal = navmesh.find_trapezoid_id_by_coord(goal_pos)
                if start is None or goal is None:
                    print(f"[ERROR] Trapezoid resolution failed.")
                    print(f"  start_pos = {start_pos}, resolved = {start}")
                    print(f"  goal_pos  = {goal_pos}, resolved = {goal}")
                    return

                if start and goal and astar.search(start, goal):
                    ids = astar.get_path()
                    raw_path_points = [navmesh.get_position(tid) for tid in ids]
                    
                resolved_goal_pos = navmesh.get_position(goal)
                dx = abs(resolved_goal_pos[0] - goal_pos[0])
                dy = abs(resolved_goal_pos[1] - goal_pos[1])
                if dx > 100 or dy > 100:
                    print(f"[WARN] Goal trapezoid {goal} is far from intended target:")
                    print(f"  Goal input : ({goal_pos[0]:.1f}, {goal_pos[1]:.1f})")
                    print(f"  Trap center: ({resolved_goal_pos[0]:.1f}, {resolved_goal_pos[1]:.1f})")
                    print(f"  ΔX = {dx:.1f}, ΔY = {dy:.1f}")
                    
                

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
