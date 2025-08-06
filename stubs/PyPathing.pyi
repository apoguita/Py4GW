from typing import List, Tuple

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

    def __init__(self) -> None: ...

class Portal:
    left_layer_id: int
    right_layer_id: int
    h0004: int #LayerID
    pair_index: int
    count: int
    trapezoid_indices: List[int]

    def __init__(self) -> None: ...

class Node:
    type: int
    id: int

    def __init__(self) -> None: ...

class XNode(Node):
    pos: tuple[float, float]
    dir: tuple[float, float]
    left_id: int
    right_id: int

    def __init__(self) -> None: ...

class YNode(Node):
    pos: tuple[float, float]
    left_id: int
    right_id: int

    def __init__(self) -> None: ...

class SinkNode(Node):
    trapezoid_ids: List[int]

    def __init__(self) -> None: ...

class PathingMap:
    zplane: int
    h0004: int
    h0008: int
    h000C: int # This is the layer ID
    h0010: int
    trapezoids: List[PathingTrapezoid]
    sink_nodes: List[SinkNode]
    x_nodes: List[XNode]
    y_nodes: List[YNode]
    h0034: int
    h0038: int
    portals: List[Portal]
    root_node_id: int

    def __init__(self) -> None: ...

# Global functions
def get_map_boundaries() -> List[float]: ...
def get_pathing_maps() -> List[PathingMap]: ...

from typing import List, Tuple
from enum import Enum


class PathStatus(Enum):
    Idle = 0
    Pending = 1
    Ready = 2
    Failed = 3


class PathPlanner:
    def __init__(self) -> None: ...
    """Create a new path planner instance."""

    def plan(self,
             start_x: float,
             start_y: float,
             start_z: float,
             goal_x: float,
             goal_y: float,
             goal_z: float) -> None: ...
    """Submit a path planning task to the game thread."""
    
    def compute_immediate(self, start_x: float, start_y: float, start_z: float,
                                goal_x: float, goal_y: float, goal_z: float) -> list[tuple[float, float, float]]:
        """Compute an immediate path without submitting to the game thread.
        Returns a list of (x, y, z) tuples if successful, or an empty list if failed."""

    def get_status(self) -> PathStatus: ...
    """Get current status of the path planner."""

    def is_ready(self) -> bool: ...
    """Return True if a valid path is ready to retrieve."""

    def was_successful(self) -> bool: ...
    """Return True if the path was successfully planned."""

    def get_path(self) -> List[Tuple[float, float, float]]: ...
    """Retrieve the calculated path as a list of (x, y, z) tuples."""

    def reset(self) -> None: ...
    """Reset the planner to Idle and clear the last result."""
