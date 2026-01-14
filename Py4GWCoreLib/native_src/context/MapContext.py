from PyImGui import end
import PyMap
from Py4GW import Game
import math
from typing import ClassVar, Optional
from ctypes import (
    Structure, POINTER,
    c_uint32, c_float, c_void_p, c_wchar, c_uint8,c_uint16,
    cast, sizeof
)
from ..internals.types import Vec2f, Vec3f, GamePos
from ..internals.gw_array import GW_Array, GW_Array_View, GW_Array_Value_View
from ..internals.gw_list import GW_TList, GW_TList_View, GW_TLink

# -------------------------------------------------------------
#region Pathing Structures
# -------------------------------------------------------------

from ctypes import Structure, POINTER, c_uint32, c_uint16, c_float

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
class NodeStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("type", c_uint32),  # +0x00
        ("id",   c_uint32),  # +0x04
    ]

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

#region Portal
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
        
        
PortalStruct._fields_ = [
    ("left_layer_id",  c_uint16),                           # +0x0000
    ("right_layer_id", c_uint16),                           # +0x0002
    ("h0004",          c_uint32),                           # +0x0004
    ("pair_ptr",           POINTER(PortalStruct)),                    # +0x0008 Portal*
    ("count",          c_uint32),                           # +0x000C
    ("trapezoids_ptr_ptr",     POINTER(POINTER(PathingTrapezoidStruct))), # +0x0010 PathingTrapezoid**
]

assert sizeof(PortalStruct) == 20, f"Portal size mismatch: {sizeof(PortalStruct)}"


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
        ptrs = GW_Array_Value_View(self.propArray_array, MapPropStruct).to_list()
        if not ptrs:
            return []
        return [ptr for ptr in ptrs]

 
# Nested structs first, as per layout
# ---------------------------------------

class MapContext_sub1_sub2Struct(Structure):
    _pack_ = 1
    _fields_ = [
        ("pad1", c_uint32 * 6),     # +0x0000
        ("pmaps_array", GW_Array),        # +0x0018 -> Array<PathingMap>
    ]
    @property
    def pathing_maps(self) -> list[PathingMapStruct]:
        ptrs = GW_Array_Value_View(self.pmaps_array, PathingMapStruct).to_list()
        if not ptrs:
            return []
        return [ptr for ptr in ptrs]


class MapContext_sub1Struct(Structure):
    _pack_ = 1
    _fields_ = [
        ("sub2_ptr", POINTER(MapContext_sub1_sub2Struct)),  # +0x0000
        ("pathing_map_block_array", GW_Array), # +0x0004 Array<uint32_t> pathing_map_block
        ("total_trapezoid_count", c_uint32),      # +0x0018
        ("0x001C", c_uint32 * 0x12),               # +0x001C (0x12 * 4 = 72 bytes)
        ("something_else_for_props_array", GW_Array),   # +0x0060 Array<TList<void*>> 
    ]
    @property
    def sub2(self) -> Optional[MapContext_sub1_sub2Struct]:
        if not self.sub2_ptr:
            return None
        return self.sub2_ptr.contents
    @property
    def pathing_map_block(self) -> list[int]:
        ptrs = GW_Array_Value_View(self.pathing_map_block_array, c_uint32).to_list()
        if not ptrs:
            return []
        return [int(ptr) for ptr in ptrs]
    @property
    def something_else_for_props(self) -> list[list[int]]:
        """
        C++: Array<TList<void*>> something_else_for_props;
        Python:
          1) GW_Array_Value_View(..., GW_TList) -> [GW_TList, GW_TList, ...]
          2) For each GW_TList -> GW_TList_View(tlist, c_uint32).to_list()
        """
        result: list[list[int]] = []

        # Step 1: get the array of TList<void*> heads
        tlist_heads = GW_Array_Value_View(self.something_else_for_props_array, GW_TList).to_list()
        if not tlist_heads:
            return result

        # Step 2: for each TList head, walk the list into a python list[int]
        for tlist in tlist_heads:
            group_ptrs = GW_TList_View(tlist, c_uint32).to_list()
            group = [int(ptr) for ptr in group_ptrs]
            result.append(group)

        return result
    
# ---------------------------------------
#Region MapContextStruct
# ---------------------------------------

class MapContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("map_boundaries", c_float * 5),          # +0x0000 (5 floats)
        ("h0014", c_uint32 * 6),                  # +0x0014
        ("spawns1_array", GW_Array),              # +0x002C # Array<void*>// Seem to be arena spawns. struct is X,Y,unk 4 byte value,unk 4 byte value.
        ("spawns2_array", GW_Array),              # +0x003C # Array<void*>// Same as above
        ("spawns3_array", GW_Array),              # +0x004C # Array<void*>// Same as above
        ("h005C", c_float * 6),                   # +0x005C
        ("sub1_ptr", POINTER(MapContext_sub1Struct)),   # +0x0074
        ("pad1", c_uint8 * 4),                    # +0x0078
        ("props_ptr", POINTER(PropsContextStruct)),     # +0x007C
        ("h0080", c_uint32),                      # +0x0080
        ("terrain", c_void_p),                    # +0x0084 (unknown struct)
        ("h0088", c_uint32 * 42),                 # +0x0088
        ("zones", c_void_p),                      # +0x0130
    ]
    @property
    def spawns1(self) -> list[int]:
        ptrs = GW_Array_Value_View(self.spawns1_array, c_uint32).to_list()
        if not ptrs:
            return []
        return [int(ptr) for ptr in ptrs]
    @property
    def spawns2(self) -> list[int]:
        ptrs = GW_Array_Value_View(self.spawns2_array, c_uint32).to_list()
        if not ptrs:
            return []
        return [int(ptr) for ptr in ptrs]
    @property
    def spawns3(self) -> list[int]:
        ptrs = GW_Array_Value_View(self.spawns3_array, c_uint32).to_list()
        if not ptrs:
            return []
        return [int(ptr) for ptr in ptrs]
    @property
    def sub1(self) -> Optional[MapContext_sub1Struct]:
        if not self.sub1_ptr:
            return None
        return self.sub1_ptr.contents
    
    @property
    def pathing_maps(self) -> list[PathingMapStruct]:
        sub1 = self.sub1
        if not sub1:
            return []
        sub2 = sub1.sub2
        if not sub2:
            return []
        return sub2.pathing_maps
    
    @property
    def props(self) -> Optional[PropsContextStruct]:
        if not self.props_ptr:
            return None
        return self.props_ptr.contents
    
#region MapContext Facade
class MapContext:
    _ptr: int = 0
    _cached_ptr: int = 0
    _cached_ctx: MapContextStruct | None = None
    _callback_name = "MapContext.UpdateMapContextPtr"

    @staticmethod
    def get_ptr() -> int:
        return MapContext._ptr
    @staticmethod
    def _update_ptr():
        MapContext._ptr = PyMap.PyMap().GetMapContextPtr()

    @staticmethod
    def enable():
        Game.register_callback(
            MapContext._callback_name,
            MapContext._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(MapContext._callback_name)
        MapContext._ptr = 0
        MapContext._cached_ptr = 0
        MapContext._cached_ctx = None

    @staticmethod
    def get_context() -> MapContextStruct | None:
        ptr = MapContext._ptr
        if not ptr:
            MapContext._cached_ptr = 0
            MapContext._cached_ctx = None
            return None
        
        if ptr != MapContext._cached_ptr:
            MapContext._cached_ptr = ptr
            MapContext._cached_ctx = cast(
                ptr,
                POINTER(MapContextStruct)
            ).contents
            
        return MapContext._cached_ctx

              
MapContext.enable()