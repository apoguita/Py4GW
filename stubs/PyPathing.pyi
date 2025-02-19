from typing import List

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
    h0004: int
    pair_index: int
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
    h000C: int
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