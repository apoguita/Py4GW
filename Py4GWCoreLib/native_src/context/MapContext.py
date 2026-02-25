from PyImGui import end

import PyPointers
from Py4GW import Game
import math
from typing import ClassVar, Optional
from ctypes import (
    Structure, POINTER,
    c_uint32, c_float, c_void_p, c_wchar, c_uint8,c_uint16,
    cast, sizeof
)
from typing import Optional, List
from dataclasses import dataclass
from ..internals.types import Vec2f, Vec3f, GamePos
from ..internals.gw_array import GW_Array, GW_BaseArray, GW_Array_View, GW_Array_Value_View
from ..internals.gw_list import GW_TList, GW_TList_View, GW_TLink
from ..context.CharContext import CharContext
from ..context.InstanceInfoContext import InstanceInfo
from ..context.WorldContext import WorldContext
from ..context.AccAgentContext import AccAgentContext

# -------------------------------------------------------------
#region Pathing Structures
# -------------------------------------------------------------

from ctypes import Structure, POINTER, c_uint32, c_uint16, c_float

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
    _pack_ = 1

    @property
    def adjacent(self) -> list["PathingTrapezoidStruct | None"]:
        """
        Returns a list of 4 entries:
        - PathingTrapezoid instance if the pointer is non-null
        - None if the pointer is null
        """
        result: list[PathingTrapezoidStruct | None] = []
        for ptr in self.adjacent_ptr:
            if ptr:
                result.append(ptr.contents)
            else:
                result.append(None)
        return result
    
    @property
    def neighbor_ids(self) -> list[int]:
        """
        Return the list of neighbor trapezoid IDs.
        Only non-null adjacent pointers are included
        (faithful to the C++ implementation).
        """
        result: list[int] = []
        for ptr in self.adjacent_ptr:
            if ptr:
                result.append(ptr.contents.id)
        return result

    def snapshot(self) -> PathingTrapezoid:
        return PathingTrapezoid(
            id=int(self.id),
            portal_left=int(self.portal_left),
            portal_right=int(self.portal_right),
            XTL=float(self.XTL),
            XTR=float(self.XTR),
            YT=float(self.YT),
            XBL=float(self.XBL),
            XBR=float(self.XBR),
            YB=float(self.YB),

            neighbor_ids=list(self.neighbor_ids),
        )


# self-referential field layout must be assigned after class creation
PathingTrapezoidStruct._fields_ = [
    ("id", c_uint32),                           # +0x00
    ("adjacent_ptr", POINTER(PathingTrapezoidStruct) * 4),  # +0x04 PathingTrapezoid* adjacent[4]
    ("portal_left", c_uint16),                 # +0x14
    ("portal_right", c_uint16),                # +0x16
    ("XTL", c_float),                          # +0x18
    ("XTR", c_float),                          # +0x1C
    ("YT", c_float),                           # +0x20
    ("XBL", c_float),                          # +0x24
    ("XBR", c_float),                          # +0x28
    ("YB", c_float),                           # +0x2C
]


#region Node Structures
@dataclass(slots=True)
class Node:
    type: int
    id: int
    
class NodeStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("type", c_uint32),  # +0x00
        ("id",   c_uint32),  # +0x04
    ]
    def snapshot(self) -> Node:
        return Node(
            type=int(self.type),
            id=int(self.id),
        )

@dataclass(slots=True)
class SinkNode:
    type: int
    id: int
    trapezoid_ids: list[int]
    
class SinkNodeStruct(NodeStruct):
    _pack_ = 1
    _fields_ = [
        ("trapezoid_ptr_ptr", POINTER(POINTER(PathingTrapezoidStruct))),  # +0x08 PathingTrapezoid**
    ]
    @property
    def trapezoid(self) -> PathingTrapezoidStruct | None:
        """Dereference trapezoid_ptr_ptr to get the actual PathingTrapezoid instance, or None."""
        if not self.trapezoid_ptr_ptr:
            return None
        trapezoid_ptr = self.trapezoid_ptr_ptr.contents
        if not trapezoid_ptr:
            return None
        return trapezoid_ptr.contents
    
    @property
    def trapezoid_ids(self) -> list[int]:
        """
        Faithful to C++:
        - trapezoid_ptr_ptr is a null-terminated PathingTrapezoid**
        - collect ids until nullptr
        """
        result: list[int] = []

        if not self.trapezoid_ptr_ptr:
            return result

        ptr = self.trapezoid_ptr_ptr
        i = 0

        while True:
            trapezoid_ptr = ptr[i]
            if not trapezoid_ptr:
                break
            result.append(int(trapezoid_ptr.contents.id))
            i += 1

        return result

    def snapshot_sinknode(self) -> SinkNode:
        return SinkNode(
            type=int(self.type),
            id=int(self.id),
            trapezoid_ids=list(self.trapezoid_ids),
        )


@dataclass(slots=True)
class XNode:
    type: int
    id: int
    pos: Vec2f
    dir: Vec2f
    left_id: Optional[int]
    right_id: Optional[int]
    

class XNodeStruct(NodeStruct):  # inherits type + id (8 bytes)
    _pack_ = 1
    _fields_ = [
        ("pos",  Vec2f),             # +0x08 (2 floats, 8 bytes)
        ("dir",  Vec2f),             # +0x10 (2 floats, 8 bytes)
        ("left_ptr", POINTER(NodeStruct)),     # +0x18
        ("right_ptr", POINTER(NodeStruct)),    # +0x1C
    ]
    @property
    def left(self) -> Optional[NodeStruct]:
        """Dereference left_ptr to get the actual Node instance, or None."""
        if not self.left_ptr:
            return None
        return self.left_ptr.contents
    @property
    def right(self) -> Optional[NodeStruct]:
        """Dereference right_ptr to get the actual Node instance, or None."""
        if not self.right_ptr:
            return None
        return self.right_ptr.contents
    
    def snapshot_xnode(self) -> XNode:
        return XNode(
            type=int(self.type),
            id=int(self.id),
            pos=self.pos,          
            dir=self.dir,         
            left_id=self.left.id if self.left else None,
            right_id=self.right.id if self.right else None,
        )
        
@dataclass(slots=True)
class YNode:
    type: int
    id: int
    pos: Vec2f
    left_id: Optional[int]
    right_id: Optional[int]

class YNodeStruct(NodeStruct):  # inherits: type + id (8 bytes)
    _pack_ = 1
    _fields_ = [
        ("pos",  Vec2f),          # +0x08 (8 bytes)
        ("left_ptr", POINTER(NodeStruct)),  # +0x10 (4 bytes)
        ("right_ptr", POINTER(NodeStruct)), # +0x14 (4 bytes)
    ]
    @property
    def left(self) -> Optional[NodeStruct]:
        """Dereference left_ptr to get the actual Node instance, or None."""
        if not self.left_ptr:
            return None
        return self.left_ptr.contents
    @property
    def right(self) -> Optional[NodeStruct]:
        """Dereference right_ptr to get the actual Node instance, or None."""
        if not self.right_ptr:
            return None
        return self.right_ptr.contents
    
    def snapshot_ynode(self) -> YNode:
        return YNode(
            type=int(self.type),
            id=int(self.id),
            pos=self.pos,  
            left_id=int(self.left.id) if self.left else None,
            right_id=int(self.right.id) if self.right else None,
        )
    

#region SpawnPoint
@dataclass(slots=True)
class SpawnPoint:
    x: float
    y: float
    angle: float    # radians; 0.0 for spawns3 entries
    tag: str        # 4-char FourCC (e.g. '0558', 'sub1'); '' for untagged

    @property
    def map_id(self) -> Optional[int]:
        """Zone map ID if tag is a numeric reference (e.g. '0558' → 558), else None.
        Tags assign spawns to zones within shared FFNA geometry, not connectivity."""
        if self.tag and self.tag.isdigit():
            return int(self.tag)
        return None

    @property
    def is_default(self) -> bool:
        """True if this is the default/fallback spawn (tag '0000')."""
        return self.tag == '0000'

class SpawnEntryStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("x", c_float),              # +0x00
        ("y", c_float),              # +0x04
        ("angle", c_float),          # +0x08  facing angle in radians
        ("tag_raw", c_uint32),       # +0x0C  big-endian FourCC
    ]

    @property
    def tag(self) -> str:
        import struct as _struct
        tag_be = _struct.pack('>I', self.tag_raw)
        return ''.join(chr(c) if 32 <= c < 127 else '' for c in tag_be)

    def snapshot(self) -> SpawnPoint:
        return SpawnPoint(x=float(self.x), y=float(self.y),
                          angle=float(self.angle), tag=self.tag)
#endregion

#region Portal
@dataclass(slots=True)
class Portal:
    left_layer_id: int
    right_layer_id: int
    flags: int               # +0x0004: bit 2 = skip expansion
    pair_index: int          # index of paired portal in right_layer's portal list, or UINT32_MAX
    count: int
    trapezoid_indices: list[int]
    
class PortalStruct(Structure):
    _pack_ = 1
    @property
    def pair(self) -> Optional["PortalStruct"]:
        """Dereference pair_ptr to get the actual Portal instance, or None."""
        if not self.pair_ptr:
            return None
        return self.pair_ptr.contents
    

    @property
    def trapezoids(self) -> PathingTrapezoidStruct | None:
        """Dereference trapezoid_ptr_ptr to get the actual PathingTrapezoid instance, or None."""
        if not self.trapezoids_ptr_ptr:
            return None
        trapezoids_ptr = self.trapezoids_ptr_ptr.contents
        if not trapezoids_ptr:
            return None
        return trapezoids_ptr.contents
    @property
    def trapezoid_indices(self) -> list[int]:
        """
        Return the list of trapezoid IDs connected by this portal.
        Faithful to the C++ implementation.
        """
        result: list[int] = []

        if not self.trapezoids_ptr_ptr or self.count == 0:
            return result

        for i in range(self.count):
            trap_ptr = self.trapezoids_ptr_ptr[i]
            if trap_ptr:
                result.append(trap_ptr.contents.id)

        return result
    
    def snapshot(self) -> Portal:
        return Portal(
            left_layer_id=int(self.left_layer_id),
            right_layer_id=int(self.right_layer_id),
            flags=int(self.flags),
            pair_index=0xFFFFFFFF,  # resolved in post-processing
            count=int(self.count),
            trapezoid_indices=list(self.trapezoid_indices),
        )


            
        
PortalStruct._fields_ = [
    ("left_layer_id",  c_uint16),                           # +0x0000
    ("right_layer_id", c_uint16),                           # +0x0002
    ("flags",          c_uint32),                           # +0x0004  bit 2 = skip expansion
    ("pair_ptr",           POINTER(PortalStruct)),                    # +0x0008 Portal*
    ("count",          c_uint32),                           # +0x000C
    ("trapezoids_ptr_ptr",     POINTER(POINTER(PathingTrapezoidStruct))), # +0x0010 PathingTrapezoid**
]

assert sizeof(PortalStruct) == 20, f"Portal size mismatch: {sizeof(PortalStruct)}"

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

    root_node : Node
    root_node_id: int        # UINT32_MAX if null

    h0048: Optional[int]
    h004C: Optional[int]
    h0050: Optional[int]


#region PathingMap
class PathingMapStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("zplane",          c_uint32),                       # +0x0000
        ("h0004",           c_uint32),                       # +0x0004
        ("h0008",           c_uint32),                       # +0x0008
        ("h000C",           c_uint32),                       # +0x000C
        ("h0010",           c_uint32),                       # +0x0010
        ("trapezoid_count", c_uint32),                       # +0x0014
        ("trapezoids_ptr",  POINTER(PathingTrapezoidStruct)),      # +0x0018 PathingTrapezoid*
        ("sink_node_count", c_uint32),                       # +0x001C
        ("sink_nodes_ptr",  POINTER(SinkNodeStruct)),              # +0x0020 SinkNode*
        ("x_node_count",    c_uint32),                       # +0x0024
        ("x_nodes_ptr",     POINTER(XNodeStruct)),                 # +0x0028 XNode*
        ("y_node_count",    c_uint32),                       # +0x002C
        ("y_nodes_ptr",     POINTER(YNodeStruct)),                 # +0x0030 YNode*
        ("h0034",           c_uint32),                       # +0x0034
        ("h0038",           c_uint32),                       # +0x0038
        ("portal_count",    c_uint32),                       # +0x003C
        ("portals_ptr",     POINTER(PortalStruct)),                # +0x0040 Portal*
        ("root_node_ptr",   POINTER(NodeStruct)),                  # +0x0044 Node*
        ("h0048_ptr",       POINTER(c_uint32)),              # +0x0048 uint32_t*
        ("h004C_ptr",       POINTER(c_uint32)),              # +0x004C uint32_t*
        ("h0050_ptr",       POINTER(c_uint32)),              # +0x0050 uint32_t*
    ]
    @property
    def trapezoids(self) -> list[PathingTrapezoidStruct]:
        if not self.trapezoids_ptr or self.trapezoid_count == 0:
            return []
        return [self.trapezoids_ptr[i] for i in range(self.trapezoid_count)]
    @property
    def sink_nodes(self) -> list[SinkNodeStruct]:
        if not self.sink_nodes_ptr or self.sink_node_count == 0:
            return []
        return [self.sink_nodes_ptr[i] for i in range(self.sink_node_count)]
    @property
    def x_nodes(self) -> list[XNodeStruct]:
        if not self.x_nodes_ptr or self.x_node_count == 0:
            return []
        return [self.x_nodes_ptr[i] for i in range(self.x_node_count)]
    @property
    def y_nodes(self) -> list[YNodeStruct]:
        if not self.y_nodes_ptr or self.y_node_count == 0:
            return []
        return [self.y_nodes_ptr[i] for i in range(self.y_node_count)]
    @property
    def portals(self) -> list[PortalStruct]:
        if not self.portals_ptr or self.portal_count == 0:
            return []
        return [self.portals_ptr[i] for i in range(self.portal_count)]
    @property
    def root_node(self) -> NodeStruct | None:
        if not self.root_node_ptr:
            return None
        return self.root_node_ptr.contents
    @property
    def h0048(self) -> Optional[c_uint32]:
        if not self.h0048_ptr:
            return None
        return self.h0048_ptr.contents
    @property
    def h004C(self) -> Optional[c_uint32]:
        if not self.h004C_ptr:
            return None
        return self.h004C_ptr.contents
    @property
    def h0050(self) -> Optional[c_uint32]:
        if not self.h0050_ptr:
            return None
        return self.h0050_ptr.contents

def snapshot(self) -> PathingMap:
    # materialize struct lists once (prevents repeated pointer deref)
    UINT32_MAX = 0xFFFFFFFF
    trapezoid_structs: list[PathingTrapezoidStruct] = self.trapezoids
    #sink_structs: list[SinkNodeStruct] = self.sink_nodes
    #x_structs: list[XNodeStruct] = self.x_nodes
    #y_structs: list[YNodeStruct] = self.y_nodes
    portal_structs: list[PortalStruct] = self.portals

    # snapshots (python-owned)
    trapezoids = [t.snapshot() for t in trapezoid_structs]
    #sink_nodes = [s.snapshot_sinknode() for s in sink_structs]
    #x_nodes = [x.snapshot_xnode() for x in x_structs]
    #y_nodes = [y.snapshot_ynode() for y in y_structs]
    portals = [p.snapshot() for p in portal_structs]

    # root node id (C++ uses root_node_id in PathingMap; you have root_node_ptr)
    root = self.root_node
    root_node = root.snapshot()
    root_node_id = int(root.id) if root is not None else UINT32_MAX

    # pointer-backed uint32_t values (read now; store python ints / None)
    h0048 = int(self.h0048.value) if self.h0048 is not None else None
    h004C = int(self.h004C.value) if self.h004C is not None else None
    h0050 = int(self.h0050.value) if self.h0050 is not None else None

    return PathingMap(
        zplane=int(self.zplane),
        h0004=int(self.h0004),
        h0008=int(self.h0008),
        h000C=int(self.h000C),
        h0010=int(self.h0010),

        trapezoid_count=int(self.trapezoid_count),
        sink_node_count=int(self.sink_node_count),
        x_node_count=int(self.x_node_count),
        y_node_count=int(self.y_node_count),
        portal_count=int(self.portal_count),

        trapezoids=trapezoids,
        sink_nodes=[], #sink_nodes,
        x_nodes=[], #x_nodes,
        y_nodes=[], #y_nodes,
        portals=portals,

        h0034=int(self.h0034),
        h0038=int(self.h0038),

        root_node=root_node,
        root_node_id=root_node_id,

        h0048=h0048,
        h004C=h004C,
        h0050=h0050,
    )

#region Props Structures
class PropModelInfoStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32),  # +0x00
        ("h0004", c_uint32),  # +0x04
        ("h0008", c_uint32),  # +0x08
        ("h000C", c_uint32),  # +0x0C
        ("h0010", c_uint32),  # +0x10
        ("h0014", c_uint32),  # +0x14
    ]


class RecObjectStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000",    c_uint32),  # +0x00
        ("h0004",    c_uint32),  # +0x04
        ("accessKey", c_uint32), # +0x08
        # ... additional fields unknown / unused
    ]

class PropByTypeStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("object_id",  c_uint32),  # +0x00
        ("prop_index", c_uint32),  # +0x04
    ]

class MapPropStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000",            c_uint32 * 5),          # +0x0000
        ("uptime_seconds",   c_uint32),              # +0x0014
        ("h0018",            c_uint32),              # +0x0018
        ("prop_index",       c_uint32),              # +0x001C
        ("position",         Vec3f),                 # +0x0020 (X,Y,Z float vector)
        ("model_file_id",    c_uint32),              # +0x002C
        ("h0030",            c_uint32 * 2),          # +0x0030
        ("rotation_angle",   c_float),               # +0x0038
        ("rotation_cos",     c_float),               # +0x003C
        ("rotation_sin",     c_float),               # +0x0040
        ("h0034",            c_uint32 * 5),          # +0x0044  *** (5 * 4 = 20 bytes)
        ("interactive_model_ptr",POINTER(RecObjectStruct)),    # +0x0058
        ("h005C",            c_uint32 * 4),          # +0x005C
        ("appearance_bitmap",c_uint32),              # +0x006C
        ("animation_bits",   c_uint32),              # +0x0070
        ("h0064",            c_uint32 * 5),          # +0x0074 ← C++ text was out of order, layout fixed
        ("prop_object_info_ptr", POINTER(PropByTypeStruct)),   # +0x0088
        ("h008C",            c_uint32),              # +0x008C
    ]
    @property
    def interactive_model(self) -> Optional[RecObjectStruct]:
        """Dereference interactive_model_ptr to get the actual RecObject instance, or None."""
        if not self.interactive_model_ptr:
            return None
        return self.interactive_model_ptr.contents
    @property
    def prop_object_info(self) -> Optional[PropByTypeStruct]:
        """Dereference prop_object_info_ptr to get the actual PropByType instance, or None."""
        if not self.prop_object_info_ptr:
            return None
        return self.prop_object_info_ptr.contents
    
class PropsContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("pad1", c_uint32 * 0x1B),   # +0x0000  (0x6C bytes)
        ("propsByType_array", GW_Array), # +0x006C # Array<TList<PropByType>>
        ("h007C", c_uint32 * 0x0A),  # +0x007C
        ("propModels_array", GW_Array),    # +0x00A4  # Array<PropModelInfo>
        ("h00B4", c_uint32 * 0x38),  # +0x00B4
        ("propArray_array", GW_Array),     # +0x0194 # Array<MapProp*>
    ]
    @property
    def props_by_type(self) -> list[list[PropByTypeStruct]]:
        """
        C++: Array<TList<PropByType>> propsByType;
        Python:
          1) GW_Array_Value_View(..., GW_TList) -> [GW_TList, GW_TList, ...]
          2) For each GW_TList -> GW_TList_View(tlist, PropByType).to_list()
        """
        result: list[list[PropByTypeStruct]] = []

        # Step 1: get the array of TList<PropByType> heads
        tlist_heads = GW_Array_Value_View(self.propsByType_array, GW_TList).to_list()
        if not tlist_heads:
            return result

        # Step 2: for each TList head, walk the list into a python list[PropByType]
        for tlist in tlist_heads:
            group = GW_TList_View(tlist, PropByTypeStruct).to_list()
            result.append(group)

        return result
    
    @property
    def prop_models(self) -> list[PropModelInfoStruct]:
        ptrs = GW_Array_Value_View(self.propModels_array, PropModelInfoStruct).to_list()
        if not ptrs:
            return []
        return [ptr for ptr in ptrs]
    
    @property
    def props(self) -> list[MapPropStruct]:
        # propArray_array is Array<MapProp*> (pointer array), not value array
        ptrs = GW_Array_View(self.propArray_array, MapPropStruct).to_list()
        if not ptrs:
            return []
        return [ptr for ptr in ptrs]

 
# Nested structs first, as per layout
# ---------------------------------------

class BlockingPropStruct(Structure):
    """Props with collision that aren't on the pathing map (mostly trees)."""
    _pack_ = 1
    _fields_ = [
        ("pos", Vec2f),      # +0x000
        ("radius", c_float), # +0x008
    ]


class MapStaticDataStruct(Structure):
    """GWCA: MapStaticData (0xA0 bytes)."""
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32 * 6),            # +0x000
        ("pmaps_array", GW_Array),          # +0x018  Array<PathingMap>
        ("h0028", c_uint32 * 4),            # +0x028
        ("blocking_props", GW_BaseArray),   # +0x038  BaseArray<BlockingProp> — collision-only props (trees etc.)
        ("h0044", c_uint32 * 16),           # +0x044
        ("trapezoid_count", c_uint32),      # +0x084  GWCA: nextTrapezoidId. Starts at 0, incremented per trap — equals total count.
        ("h0088", c_uint32),                # +0x088
        ("map_id", c_uint32),               # +0x08C  GW::Constants::MapID
        ("h0090", c_uint32 * 4),            # +0x090
    ]
    @property
    def pathing_maps(self) -> list[PathingMapStruct]:
        ptrs = GW_Array_Value_View(self.pmaps_array, PathingMapStruct).to_list()
        if not ptrs:
            return []
        return [ptr for ptr in ptrs]
    
    @property
    def pathing_maps_snapshot(self) -> list[PathingMap]:
        ptrs = GW_Array_Value_View(self.pmaps_array, PathingMapStruct).to_list()
        if not ptrs:
            return []

        # First pass: snapshot all planes (pair_index unresolved)
        result: list[PathingMap] = []
        for pmap_struct in ptrs:
            pmap_snapshot = snapshot(pmap_struct)
            result.append(pmap_snapshot)

        # Second pass: resolve pair_index across planes via pair_ptr addresses
        import ctypes as _ct
        portal_size = _ct.sizeof(PortalStruct)

        # Build address → (plane_idx, portal_idx) map
        addr_map: dict[int, tuple[int, int]] = {}
        for pi, pmap_struct in enumerate(ptrs):
            if not pmap_struct.portals_ptr or pmap_struct.portal_count == 0:
                continue
            base = _ct.cast(pmap_struct.portals_ptr, _ct.c_void_p).value
            for idx in range(pmap_struct.portal_count):
                if base is None:
                    continue
                addr_map[base + idx * portal_size] = (pi, idx)

        # Resolve each portal's pair_index
        for pi, pmap_struct in enumerate(ptrs):
            if not pmap_struct.portals_ptr or pmap_struct.portal_count == 0:
                continue
            for idx in range(pmap_struct.portal_count):
                p = pmap_struct.portals_ptr[idx]
                if not p.pair_ptr:
                    continue
                pair_addr = _ct.cast(p.pair_ptr, _ct.c_void_p).value
                if pair_addr is None:
                    continue
                loc = addr_map.get(pair_addr)
                if loc is not None:
                    result[pi].portals[idx].pair_index = loc[1]

        return result


class PathContextStruct(Structure):
    """GWCA: PathContext (0x94 bytes). Holds pathfinding state for the current map."""
    _pack_ = 1
    _fields_ = [
        ("static_data_ptr", POINTER(MapStaticDataStruct)),  # +0x000  MapStaticData*
        ("blocked_planes", GW_BaseArray),    # +0x004  BaseArray<uint32_t> (0x0C)
        ("path_nodes", GW_BaseArray),        # +0x010  BaseArray<PathNode*> — indexed by trapezoid id
        ("node_cache", c_uint32 * 5),        # +0x01C  NodeCache (0x14): cachedCount*, m_mask, BaseArray<uint32_t>
        ("open_list", c_uint32 * 5),         # +0x030  PrioQ<PathNode> (0x14)
        ("free_ipath_node", c_uint32 * 3),   # +0x044  ObjectPool (0x0C)
        ("allocated_path_nodes", GW_BaseArray),  # +0x050  BaseArray<PathNode*> — cleanup array
        ("h005C", c_uint32),                 # +0x05C
        ("h0060", c_uint32),                 # +0x060
        ("waypoints", GW_Array),             # +0x064  Array<PathWaypoint>
        ("node_stack", GW_Array),            # +0x074  Array<struct Node*>
        ("h0084", c_uint32 * 4),             # +0x084
    ]

    @property
    def static_data(self) -> Optional[MapStaticDataStruct]:
        if not self.static_data_ptr:
            return None
        return self.static_data_ptr.contents

    # backward compat alias
    sub2 = static_data
    
# ---------------------------------------
#Region MapContextStruct
# ---------------------------------------

class MapContextStruct(Structure):
    """GWCA: MapContext (0x138 bytes)."""
    _pack_ = 1
    _fields_ = [
        ("map_type", c_uint32),                   # +0x000  "less than 4"
        ("start_pos", Vec2f),                     # +0x004
        ("end_pos", Vec2f),                       # +0x00C
        ("h0014", c_uint32 * 6),                  # +0x014
        ("spawns1_array", GW_Array),              # +0x02C  Array<SpawnEntryStruct>
        ("spawns2_array", GW_Array),              # +0x03C  Array<SpawnEntryStruct>
        ("spawns3_array", GW_Array),              # +0x04C  Array<SpawnEntryStruct>
        ("h005C", c_float * 6),                   # +0x05C  "Some trapezoid i think" — GWCA
        ("path_ptr", POINTER(PathContextStruct)),    # +0x074  PathContext*
        ("path_engine_ptr", c_void_p),            # +0x078  PathEngineContext* (optional DLL-based pathfinder)
        ("props_ptr", POINTER(PropsContextStruct)),      # +0x07C  PropsContext*
        ("h0080", c_uint32),                      # +0x080
        ("terrain", c_void_p),                    # +0x084
        ("h0088", c_uint32),                      # +0x088
        ("map_id", c_uint32),                     # +0x08C  GW::Constants::MapID
        ("h0090", c_uint32 * 40),                 # +0x090
        ("zones", c_void_p),                      # +0x130
        ("h0134", c_uint32),                      # +0x134
    ]
    @property
    def spawns1(self) -> list[SpawnPoint]:
        entries = GW_Array_Value_View(self.spawns1_array, SpawnEntryStruct).to_list()
        return [e.snapshot() for e in entries] if entries else []
    @property
    def spawns2(self) -> list[SpawnPoint]:
        entries = GW_Array_Value_View(self.spawns2_array, SpawnEntryStruct).to_list()
        return [e.snapshot() for e in entries] if entries else []
    @property
    def spawns3(self) -> list[SpawnPoint]:
        entries = GW_Array_Value_View(self.spawns3_array, SpawnEntryStruct).to_list()
        return [e.snapshot() for e in entries] if entries else []
    @property
    def path(self) -> Optional[PathContextStruct]:
        """PathContext — pathfinding state for the current map."""
        if not self.path_ptr:
            return None
        return self.path_ptr.contents

    # backward compat alias
    sub1 = path

    @property
    def pathing_maps(self) -> list[PathingMapStruct]:
        pc = self.path
        if not pc:
            return []
        sd = pc.static_data
        if not sd:
            return []
        return sd.pathing_maps

    @property
    def pathing_maps_snapshot(self) -> list[PathingMap]:
        pc = self.path
        if not pc:
            return []
        sd = pc.static_data
        if not sd:
            return []
        return sd.pathing_maps_snapshot
    
    @property
    def props(self) -> Optional[PropsContextStruct]:
        if not self.props_ptr:
            return None
        return self.props_ptr.contents
    
# ── Travel portal types & detection ──────────────────────────────────────

@dataclass(slots=True)
class TravelPortal:
    x: float
    y: float
    z: float
    model_file_id: int

# Model file IDs for travel portal props (from GWToolbox++)
_PORTAL_MODEL_FILE_IDS: dict[int, str] = {
    0x4E6B2: "EotN Asura Gate",
    0x3C5AC: "EotN/Nightfall",
    0x0A825: "Prophecies/Factions",
}


def _file_hash_to_file_id(hash_ptr: int) -> int:
    """Replicate ArenaNetFileParser::FileHashToFileId from GW client.

    Converts wchar_t* file hash in game memory to a .dat file ID.
    """
    if hash_ptr < 0x10000:
        return 0
    wchars = cast(hash_ptr, POINTER(c_uint16))
    w0, w1, w2 = wchars[0], wchars[1], wchars[2]
    w3 = wchars[3] if w2 != 0 else 0
    if not (w0 > 0xFF and w1 > 0xFF and (w2 == 0 or (w2 > 0xFF and w3 == 0))):
        return 0
    temp = (w0 - 0xFF00FF) & 0xFFFFFFFF
    return (temp + w1 * 0xFF00) & 0xFFFFFFFF


def _get_prop_model_file_id(prop: MapPropStruct) -> int:
    """Extract model file ID from a MapProp via h0034[4] → sub[1] pointer chain."""
    ptr4 = prop.h0034[4]
    if ptr4 < 0x10000:
        return 0
    try:
        sub = cast(ptr4, POINTER(c_uint32))
        hash_ptr = sub[1]
        return _file_hash_to_file_id(hash_ptr)
    except Exception:
        return 0


def _get_travel_portals(mc: 'MapContextStruct') -> list[TravelPortal]:
    """Get travel portal positions from runtime map props."""
    props_ctx = mc.props
    if props_ctx is None:
        return []

    prop_view = GW_Array_View(props_ctx.propArray_array, MapPropStruct)
    if not prop_view.valid():
        return []

    portals: list[TravelPortal] = []
    for i in range(len(prop_view)):
        p = prop_view[i]
        fid = _get_prop_model_file_id(p)
        if fid in _PORTAL_MODEL_FILE_IDS:
            pos = p.position
            portals.append(TravelPortal(x=pos.x, y=pos.y, z=pos.z, model_file_id=fid))
    return portals


#region MapContext Facade
class MapContext:
    _ptr: int = 0
    _cached_ctx: MapContextStruct | None = None
    _callback_name = "MapContext.UpdatePtr"
    _pathing_maps_cache: dict[int, list[PathingMap]] = {}
    _pathing_maps_cache_raw: dict[int, list[PathingMapStruct]] = {}

    @staticmethod
    def get_ptr() -> int:
        return MapContext._ptr

    @staticmethod
    def _update_ptr():
        ptr = PyPointers.PyPointers.GetMapContextPtr()
        MapContext._ptr = ptr

        if not ptr:
            MapContext._cached_ctx = None
            return

        MapContext._cached_ctx = cast(
            ptr,
            POINTER(MapContextStruct)
        ).contents

    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            MapContext._callback_name,
            PyCallback.Phase.PreUpdate,
            MapContext._update_ptr,
            priority=1,
            context=PyCallback.Context.Draw
        )

    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(MapContext._callback_name)
    
        MapContext._ptr = 0
        MapContext._cached_ctx = None

    @staticmethod
    def get_context() -> MapContextStruct | None:
        return MapContext._cached_ctx
    
    @staticmethod
    def GetPathingMaps() -> list[PathingMap]:
        map_ctx = MapContext._cached_ctx
        char_ctx = CharContext.get_context()
        instance_info_ctx = InstanceInfo.get_context()
        world_ctx = WorldContext.get_context()
        acc_agent_ctx = AccAgentContext.get_context()

        if not (map_ctx and char_ctx and instance_info_ctx and world_ctx and acc_agent_ctx):
            return []
        
        instance_type = instance_info_ctx.instance_type
        if instance_type not in (0, 1):  # explorable, story, pvp
            return []

        map_id = char_ctx.current_map_id
        if map_id in MapContext._pathing_maps_cache:
            return MapContext._pathing_maps_cache[map_id]
        pathing_maps = map_ctx.pathing_maps_snapshot
        MapContext._pathing_maps_cache[map_id] = pathing_maps
        return pathing_maps
    
    @staticmethod
    def GetPathingMapsRaw() -> list[PathingMapStruct]:
        map_ctx = MapContext._cached_ctx
        char_ctx = CharContext.get_context()
        instance_info_ctx = InstanceInfo.get_context()
        world_ctx = WorldContext.get_context()
        acc_agent_ctx = AccAgentContext.get_context()

        if not (map_ctx and char_ctx and instance_info_ctx and world_ctx and acc_agent_ctx):
            return []
        
        instance_type = instance_info_ctx.instance_type
        if instance_type not in (0, 1):  # explorable, story, pvp
            return []

        map_id = char_ctx.current_map_id
        if map_id in MapContext._pathing_maps_cache_raw:
            return MapContext._pathing_maps_cache_raw[map_id]

        pathing_maps = map_ctx.pathing_maps
        MapContext._pathing_maps_cache_raw[map_id] = pathing_maps
        return pathing_maps

    @staticmethod
    def GetTravelPortals() -> list[TravelPortal]:
        """Get travel portal positions from current map's runtime props."""
        mc = MapContext._cached_ctx
        if not mc:
            return []
        return _get_travel_portals(mc)

    @staticmethod
    def GetSpawns() -> tuple[list[SpawnPoint], list[SpawnPoint], list[SpawnPoint]]:
        """Return (spawns1, spawns2, spawns3) for the current map."""
        mc = MapContext._cached_ctx
        if not mc:
            return [], [], []
        return mc.spawns1, mc.spawns2, mc.spawns3


MapContext.enable()
