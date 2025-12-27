from typing import Optional, List
from ctypes import Structure, POINTER, c_uint32, c_uint16, c_float, c_uint8, c_void_p
import ctypes

from ..internals.types import Vec2f, Vec3f, CPointer
from ..internals.gw_array import GW_Array
from ..internals.gw_list import GW_TList
# (scanner_facade import is just symbolic; replace with your actual location)


# -------------------------------------------------------------
# Core Pathing Types
# -------------------------------------------------------------

class PathingTrapezoid(Structure):
    id: int
    adjacent_ptr: list[CPointer["PathingTrapezoid"]]   # PathingTrapezoid* adjacent[4]
    portal_left: int
    portal_right: int
    XTL: float
    XTR: float
    YT: float
    XBL: float
    XBR: float
    YB: float

    @property
    def adjacent(self) -> List[Optional["PathingTrapezoid"]]: ...


class Node(Structure):
    type: c_uint32
    id:   c_uint32


class SinkNode(Node):
    trapezoid_ptr_ptr: Optional[CPointer[PathingTrapezoid]]

    @property
    def trapezoid(self) -> Optional[PathingTrapezoid]: ...


class XNode(Node):
    pos: Vec2f
    dir: Vec2f
    left_ptr: Optional[CPointer[Node]]
    right_ptr: Optional[CPointer[Node]]

    @property
    def left(self) -> Optional[Node]: ...
    @property
    def right(self) -> Optional[Node]: ...


class YNode(Node):
    pos: Vec2f
    left_ptr: Optional[CPointer[Node]]
    right_ptr: Optional[CPointer[Node]]

    @property
    def left(self) -> Optional[Node]: ...
    @property
    def right(self) -> Optional[Node]: ...


class Portal(Structure):
    left_layer_id: int
    right_layer_id: int
    h0004: int
    pair_ptr: Optional[CPointer["Portal"]]
    count: int
    trapezoids_ptr_ptr: Optional[CPointer[PathingTrapezoid]]

    @property
    def pair(self) -> Optional["Portal"]: ...

    @property
    def trapezoids(self) -> Optional[PathingTrapezoid]: ...


class PathingMap(Structure):
    zplane: int
    h0004: int
    h0008: int
    h000C: int
    h0010: int
    trapezoid_count: int
    trapezoids_ptr: Optional[CPointer[PathingTrapezoid]]
    sink_node_count: int
    sink_nodes_: Optional[CPointer[SinkNode]]
    x_node_count: int
    x_nodes_ptr: Optional[CPointer[XNode]]
    y_node_count: int
    y_nodes_ptr: Optional[CPointer[YNode]]
    h0034: int
    h0038: int
    portal_count: int
    portals_ptr: Optional[CPointer[Portal]]
    root_node_ptr: Optional[CPointer[Node]]
    h0048_ptr: Optional[CPointer[int]]
    h004C_ptr: Optional[CPointer[int]]
    h0050_ptr: Optional[CPointer[int]]

    @property
    def trapezoids(self) -> Optional[PathingTrapezoid]: ...
    @property
    def sink_nodes(self) -> Optional[SinkNode]: ...
    @property
    def x_nodes(self) -> Optional[XNode]: ...
    @property
    def y_nodes(self) -> Optional[YNode]: ...
    @property
    def portals(self) -> Optional[Portal]: ...
    @property
    def root_node(self) -> Optional[Node]: ...
    @property
    def h0048(self) -> Optional[c_uint32]: ...
    @property
    def h004C(self) -> Optional[c_uint32]: ...
    @property
    def h0050(self) -> Optional[c_uint32]: ...


# -------------------------------------------------------------
# Prop & Object Types
# -------------------------------------------------------------

class PropModelInfo(Structure):
    h0000: c_uint32
    h0004: c_uint32
    h0008: c_uint32
    h000C: c_uint32
    h0010: c_uint32
    h0014: c_uint32


class RecObject(Structure):
    h0000:    c_uint32
    h0004:    c_uint32
    accessKey: c_uint32


class PropByType(Structure):
    object_id:  c_uint32
    prop_index: c_uint32


class MapProp(Structure):
    h0000: list[int]               # length 5
    uptime_seconds: int
    h0018: int
    prop_index: int
    position: Vec3f
    model_file_id: int
    h0030: list[int]               # length 2
    rotation_angle: float
    rotation_cos: float
    rotation_sin: float
    h0034: list[int]               # length 5
    interactive_model_ptr: Optional[CPointer[RecObject]]
    h005C: list[int]               # length 4
    appearance_bitmap: int
    animation_bits: int
    h0064: list[int]               # length 5
    prop_object_info_ptr: Optional[CPointer[PropByType]]
    h008C: int

    @property
    def interactive_model(self) -> Optional[RecObject]: ...
    @property
    def prop_object_info(self) -> Optional[PropByType]: ...


class PropsContext(Structure):
    pad1: list[int]                     # length 0x1B
    propsByType_array: GW_Array         # Array<TList<PropByType>>
    h007C: list[int]                    # length 0x0A
    propModels_array: GW_Array          # Array<PropModelInfo>
    h00B4: list[int]                    # length 0x38
    propArray_array: GW_Array           # Array[MapProp*]

    @property
    def props_by_type(self) -> List[List[PropByType]]: ...
    @property
    def prop_models(self) -> List[PropModelInfo]: ...
    @property
    def props(self) -> List[MapProp]: ...


# -------------------------------------------------------------
# Map Context (nested)
# -------------------------------------------------------------

class MapContext_sub1_sub2(Structure):
    pad1: list[int]           # length 6
    pmaps: GW_Array    # Array<PathingMap>

    @property
    def pathing_maps(self) -> List[PathingMap]: ...


class MapContext_sub1(Structure):
    sub2_ptr: Optional[CPointer[MapContext_sub1_sub2]]
    pathing_map_block_array: GW_Array          # Array<uint32_t>
    total_trapezoid_count: int
    h0014: list[int]                     # length 0x12
    something_else_for_props_array: GW_Array   # Array<TList<void*>>

    @property
    def sub2(self) -> Optional[MapContext_sub1_sub2]: ...
    @property
    def pathing_map_block(self) -> List[int]: ...
    @property
    def something_else_for_props(self) -> List[List[int]]: ...


class MapContextStruct(Structure):
    map_boundaries: list[float]          # length 5
    h0014: list[int]                     # length 6
    spawns1_array: GW_Array                    # Array<void*>
    spawns2_array: GW_Array                    # Array<void*>
    spawns3_array: GW_Array                    # Array<void*>
    h005C: list[float]                   # length 6
    sub1_ptr: Optional[CPointer[MapContext_sub1]]
    pad1: list[int]                      # uint8_t[4] as list[int]
    props_ptr: Optional[CPointer[PropsContext]]
    h0080: int
    terrain: int                         # void*
    h0088: list[int]                     # length 42
    zones: int                           # void*

    @property
    def spawns1(self) -> List[int]: ...
    @property
    def spawns2(self) -> List[int]: ...
    @property
    def spawns3(self) -> List[int]: ...
    @property
    def sub1(self) -> Optional[MapContext_sub1]: ...
    @property
    def props(self) -> Optional[PropsContext]: ...


# -------------------------------------------------------------
# Facade Types
# -------------------------------------------------------------

class MapContext:
    _ptr: int
    _callback_name: str

    @staticmethod
    def get_ptr() -> int: ...
    @staticmethod
    def _update_ptr() -> None: ...
    @staticmethod
    def enable() -> None: ...
    @staticmethod
    def disable() -> None: ...
    @staticmethod
    def get_context() -> Optional[MapContextStruct]: ...
