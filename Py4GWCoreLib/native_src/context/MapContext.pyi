from typing import Optional, List
from ctypes import Structure, POINTER, c_uint32, c_uint16, c_float, c_uint8, c_void_p
import ctypes

from ..internals.types import Vec2f, Vec3f, CPointer
from ..internals.gw_array import GW_Array
from ..internals.gw_list import GW_TList
from dataclasses import dataclass
# (scanner_facade import is just symbolic; replace with your actual location)


# -------------------------------------------------------------
# Core Pathing Types
# -------------------------------------------------------------
@dataclass(slots=True)
class PathingTrapezoid:
    id: int
    portal_left: int
    portal_right: int
    XTL: float
    XTR: float
    YT: float
    XBL: float
    XBR: float
    YB: float
    neighbor_ids: list[int]
    
class PathingTrapezoidStruct(Structure):
    id: int
    adjacent_ptr: list[CPointer["PathingTrapezoidStruct"]]   # PathingTrapezoid* adjacent[4]
    portal_left: int
    portal_right: int
    XTL: float
    XTR: float
    YT: float
    XBL: float
    XBR: float
    YB: float

    @property
    def adjacent(self) -> List[Optional["PathingTrapezoidStruct"]]: ...
    @property
    def neighbor_ids(self) -> list[int]: ...
    def snapshot(self) -> PathingTrapezoid: ...

@dataclass(slots=True)
class Node:
    type: int
    id: int

class NodeStruct(Structure):
    type: c_uint32
    id:   c_uint32
    def snapshot(self) -> Node: ...

@dataclass(slots=True)
class SinkNode:
    type: int
    id: int
    trapezoid_ids: list[int]
    
class SinkNodeStruct(NodeStruct):
    trapezoid_ptr_ptr: Optional[CPointer[PathingTrapezoidStruct]]

    @property
    def trapezoid(self) -> Optional[PathingTrapezoidStruct]: ...
    @property
    def trapezoid_ids(self) -> list[int]: ...
    def snapshot_sinknode(self) -> SinkNode: ...

@dataclass(slots=True)
class XNode:
    type: int
    id: int
    pos: Vec2f
    dir: Vec2f
    left_id: Optional[int]
    right_id: Optional[int]
    
class XNodeStruct(NodeStruct):
    pos: Vec2f
    dir: Vec2f
    left_ptr: Optional[CPointer[NodeStruct]]
    right_ptr: Optional[CPointer[NodeStruct]]

    @property
    def left(self) -> Optional[NodeStruct]: ...
    @property
    def right(self) -> Optional[NodeStruct]: ...
    def snapshot_xnode(self) -> XNode: ...

@dataclass(slots=True)
class YNode:
    type: int
    id: int
    pos: Vec2f
    left_id: Optional[int]
    right_id: Optional[int]

class YNodeStruct(NodeStruct):
    pos: Vec2f
    left_ptr: Optional[CPointer[NodeStruct]]
    right_ptr: Optional[CPointer[NodeStruct]]

    @property
    def left(self) -> Optional[NodeStruct]: ...
    @property
    def right(self) -> Optional[NodeStruct]: ...
    def snapshot_ynode(self) -> YNode: ...

class SpawnPoint:
    x: float
    y: float
    angle: float    # radians; 0.0 for spawns3 entries
    tag: str        # 4-char FourCC (e.g. '0558', 'sub1'); '' for untagged. Map ID tags assign spawns to zones, not connectivity.
    @property
    def map_id(self) -> Optional[int]:
        """Zone map ID if numeric tag, else None. Assigns spawn to a zone, not connectivity."""
        ...
    @property
    def is_default(self) -> bool: ...

class SpawnEntryStruct(Structure):
    x: float
    y: float
    angle: float    # facing angle in radians
    tag_raw: int    # uint32, big-endian FourCC
    @property
    def tag(self) -> str: ...
    def snapshot(self) -> SpawnPoint: ...

class Portal:
    left_layer_id: int
    right_layer_id: int
    flags: int               # +0x0004: bit 2 = skip expansion
    pair_index: int          # index of paired portal in right_layer's portal list, or UINT32_MAX
    count: int
    trapezoid_indices: list[int]

class PortalStruct(Structure):
    left_layer_id: int
    right_layer_id: int
    flags: int
    pair_ptr: Optional[CPointer["PortalStruct"]]
    count: int
    trapezoids_ptr_ptr: Optional[CPointer[PathingTrapezoidStruct]]

    @property
    def pair(self) -> Optional["PortalStruct"]: ...

    @property
    def trapezoids(self) -> Optional[PathingTrapezoidStruct]: ...
    def snapshot(self, all_portals: list["PortalStruct"]) -> Portal: ...

@dataclass(slots=True)
class PathingMap:
    # ---- exact fields from PathingMapStruct ----
    zplane: int
    h0004: int
    h0008: int
    h000C: int
    h0010: int

    trapezoid_count: int
    sink_node_count: int
    x_node_count: int
    y_node_count: int
    portal_count: int

    trapezoids: list[PathingTrapezoid]
    sink_nodes: list[SinkNode]
    x_nodes: list[XNode]
    y_nodes: list[YNode]
    portals: list[Portal]

    h0034: int
    h0038: int

    root_node: Node
    root_node_id: int        # UINT32_MAX if null

    h0048: Optional[int]
    h004C: Optional[int]
    h0050: Optional[int]


class PathingMapStruct(Structure):
    zplane: int
    h0004: int
    h0008: int
    h000C: int
    h0010: int
    trapezoid_count: int
    trapezoids_ptr: Optional[CPointer[PathingTrapezoidStruct]]
    sink_node_count: int
    sink_nodes_: Optional[CPointer[SinkNodeStruct]]
    x_node_count: int
    x_nodes_ptr: Optional[CPointer[XNodeStruct]]
    y_node_count: int
    y_nodes_ptr: Optional[CPointer[YNodeStruct]]
    h0034: int
    h0038: int
    portal_count: int
    portals_ptr: Optional[CPointer[PortalStruct]]
    root_node_ptr: Optional[CPointer[NodeStruct]]
    h0048_ptr: Optional[CPointer[int]]
    h004C_ptr: Optional[CPointer[int]]
    h0050_ptr: Optional[CPointer[int]]

    @property
    def trapezoids(self) -> list[PathingTrapezoidStruct]: ...
    @property
    def sink_nodes(self) -> list[SinkNodeStruct]: ...
    @property
    def x_nodes(self) -> list[XNodeStruct]: ...
    @property
    def y_nodes(self) -> list[YNodeStruct]: ...
    @property
    def portals(self) -> list[PortalStruct]: ...
    @property
    def root_node(self) -> Optional[NodeStruct]: ...
    @property
    def h0048(self) -> Optional[c_uint32]: ...
    @property
    def h004C(self) -> Optional[c_uint32]: ...
    @property
    def h0050(self) -> Optional[c_uint32]: ...
    def snapshot(self) -> PathingMap: ...


# -------------------------------------------------------------
# Prop & Object Types
# -------------------------------------------------------------

class PropModelInfoStruct(Structure):
    h0000: c_uint32
    h0004: c_uint32
    h0008: c_uint32
    h000C: c_uint32
    h0010: c_uint32
    h0014: c_uint32


class RecObjectStruct(Structure):
    h0000:    c_uint32
    h0004:    c_uint32
    accessKey: c_uint32


class PropByTypeStruct(Structure):
    object_id:  c_uint32
    prop_index: c_uint32


class MapPropStruct(Structure):
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
    interactive_model_ptr: Optional[CPointer[RecObjectStruct]]
    h005C: list[int]               # length 4
    appearance_bitmap: int
    animation_bits: int
    h0064: list[int]               # length 5
    prop_object_info_ptr: Optional[CPointer[PropByTypeStruct]]
    h008C: int

    @property
    def interactive_model(self) -> Optional[RecObjectStruct]: ...
    @property
    def prop_object_info(self) -> Optional[PropByTypeStruct]: ...


class PropsContextStruct(Structure):
    pad1: list[int]                     # length 0x1B
    propsByType_array: GW_Array         # Array<TList<PropByType>>
    h007C: list[int]                    # length 0x0A
    propModels_array: GW_Array          # Array<PropModelInfo>
    h00B4: list[int]                    # length 0x38
    propArray_array: GW_Array           # Array[MapProp*]

    @property
    def props_by_type(self) -> List[List[PropByTypeStruct]]: ...
    @property
    def prop_models(self) -> List[PropModelInfoStruct]: ...
    @property
    def props(self) -> List[MapPropStruct]: ...


# -------------------------------------------------------------
# Map Context (nested)
# -------------------------------------------------------------

class BlockingPropStruct(Structure):
    """Props with collision not on the pathing map (trees etc.)."""
    pos: Vec2f
    radius: float

class MapStaticDataStruct(Structure):
    """GWCA: MapStaticData (0xA0)."""
    h0000: list[int]                     # length 6
    pmaps_array: GW_Array                # Array<PathingMap>
    h0028: list[int]                     # length 4
    blocking_props: GW_Array             # BaseArray<BlockingProp>
    h0044: list[int]                     # length 16
    trapezoid_count: int                 # +0x084  GWCA: nextTrapezoidId. Equals total count.
    h0088: int
    map_id: int                          # GW::Constants::MapID
    h0090: list[int]                     # length 4

    @property
    def pathing_maps(self) -> List[PathingMapStruct]: ...
    @property
    def pathing_maps_snapshot(self) -> list[PathingMap]: ...


class PathContextStruct(Structure):
    """GWCA: PathContext (0x94)."""
    static_data_ptr: Optional[CPointer[MapStaticDataStruct]]
    blocked_planes: GW_Array             # BaseArray<uint32_t>
    path_nodes: GW_Array                 # BaseArray<PathNode*>
    node_cache: list[int]                # NodeCache (0x14)
    open_list: list[int]                 # PrioQ<PathNode> (0x14)
    free_ipath_node: list[int]           # ObjectPool (0x0C)
    allocated_path_nodes: GW_Array       # BaseArray<PathNode*>
    h005C: int
    h0060: int
    waypoints: GW_Array                  # Array<PathWaypoint>
    node_stack: GW_Array                 # Array<struct Node*>
    h0084: list[int]                     # length 4

    @property
    def static_data(self) -> Optional[MapStaticDataStruct]: ...
    @property
    def sub2(self) -> Optional[MapStaticDataStruct]: ...


class MapContextStruct(Structure):
    """GWCA: MapContext (0x138)."""
    map_type: int                        # "less than 4"
    start_pos: Vec2f
    end_pos: Vec2f
    h0014: list[int]                     # length 6
    spawns1_array: GW_Array              # Array<SpawnEntryStruct>
    spawns2_array: GW_Array              # Array<SpawnEntryStruct>
    spawns3_array: GW_Array              # Array<SpawnEntryStruct>
    h005C: list[float]                   # length 6, "Some trapezoid i think" — GWCA
    path_ptr: Optional[CPointer[PathContextStruct]]   # PathContext*
    path_engine_ptr: int                 # PathEngineContext* (optional DLL-based pathfinder)
    props_ptr: Optional[CPointer[PropsContextStruct]]
    h0080: int
    terrain: int                         # void*
    h0088: int
    map_id: int                          # GW::Constants::MapID
    h0090: list[int]                     # length 40
    zones: int                           # void*
    h0134: int

    @property
    def spawns1(self) -> List[SpawnPoint]: ...
    @property
    def spawns2(self) -> List[SpawnPoint]: ...
    @property
    def spawns3(self) -> List[SpawnPoint]: ...
    @property
    def path(self) -> Optional[PathContextStruct]: ...
    @property
    def sub1(self) -> Optional[PathContextStruct]: ...
    @property
    def pathing_maps(self) -> list[PathingMapStruct]: ...
    @property
    def pathing_maps_snapshot(self) -> list[PathingMap]: ...
    @property
    def props(self) -> Optional[PropsContextStruct]: ...


# -------------------------------------------------------------
# Travel Portal Types
# -------------------------------------------------------------

@dataclass(slots=True)
class TravelPortal:
    x: float
    y: float
    z: float
    model_file_id: int

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
    @staticmethod
    def GetPathingMaps() -> list[PathingMap]: ...
    @staticmethod
    def GetPathingMapsRaw() -> list[PathingMapStruct]: ...
    @staticmethod
    def GetTravelPortals() -> list[TravelPortal]: ...
    @staticmethod
    def GetSpawns() -> tuple[list[SpawnPoint], list[SpawnPoint], list[SpawnPoint]]: ...
