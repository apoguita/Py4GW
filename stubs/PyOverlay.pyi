# PyOverlay.pyi - Type stub for PyOverlay (PyBind11 bindings)
from typing import List

class Point2D:
    x: int
    y: int

    def __init__(self, x: int, y: int) -> None: ...

class Point3D:
    x: float
    y: float
    z: float

    def __init__(self, x: float, y: float, z: float) -> None: ...

class Overlay:
    def __init__(self) -> None: ...
    def RefreshDrawList(self) -> None: ...
    def GetMouseCoords(self) -> Point2D: ...
    def findZ(self, x: float, y: float, pz: float) -> float: ...
    def WorldToScreen(self, x: float, y: float, z: float) -> Point2D: ...
    def GetMouseWorldPos(self) -> Point3D: ...
    def BeginDraw(self) -> None: ...
    def EndDraw(self) -> None: ...
    def DrawLine(self, from_: Point2D, to: Point2D, color: int = 0xFFFFFFFF, thickness: float = 1.0) -> None: ...
    def DrawLine3D(self, from_: Point3D, to: Point3D, color: int = 0xFFFFFFFF, thickness: float = 1.0) -> None: ...
    def DrawPoly(self, center: Point2D, radius: float, color: int = 0xFFFFFFFF, numSegments: int = 32, thickness: float = 1.0) -> None: ...
    def DrawPoly3D(self, center: Point3D, radius: float, color: int = 0xFFFFFFFF, numSegments: int = 32, thickness: float = 1.0, autoZ: bool = True) -> None: ...
    def DrawText2D(self, position: Point2D, text: str, color: int, centered: bool = True, scale: float = 1.0) -> None: ...
    def DrawText3D(self, position3D: Point3D, text: str, color: int, autoZ: bool = True, centered: bool = True, scale: float = 1.0) -> None: ...
    def DrawFilledTriangle3D(self, p1: Point3D, p2: Point3D, p3: Point3D, color: int) -> None: ...
    def GetDisplaySize(self) -> Point2D: ...
    def IsMouseClicked(self, button: int = 0) -> bool: ...

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