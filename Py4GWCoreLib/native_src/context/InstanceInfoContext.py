
from typing import ClassVar, Optional
from ctypes import (
    Structure, POINTER,
    c_uint32, c_float, c_void_p, c_wchar, c_uint8,c_uint16,
    cast
)
from ..internals.helpers import read_wstr, encoded_wstr_to_str
from ..internals.types import Vec2f, Vec3f, GamePos
from ..internals.gw_array import GW_Array, GW_Array_View, GW_Array_Value_View
from ..internals.native_symbol import NativeSymbol
from ...Scanner import Scanner, ScannerSection
from ..internals.prototypes import Prototypes

#region InstanceInfo
class MapDimensionsStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("unk", c_uint32),
        ("start_x", c_uint32),
        ("start_y", c_uint32),
        ("end_x", c_uint32),
        ("end_y", c_uint32),
        ("unk1", c_uint32),
    ]
    
class AreaInfoStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("campaign", c_uint32),            # +0x0000 Constants::Campaign
        ("continent", c_uint32),           # +0x0004 Continent
        ("region", c_uint32),              # +0x0008 Region
        ("type", c_uint32),                # +0x000C RegionType
        ("flags", c_uint32),               # +0x0010
        ("thumbnail_id", c_uint32),        # +0x0014
        ("min_party_size", c_uint32),      # +0x0018
        ("max_party_size", c_uint32),      # +0x001C
        ("min_player_size", c_uint32),     # +0x0020
        ("max_player_size", c_uint32),     # +0x0024
        ("controlled_outpost_id", c_uint32), # +0x0028
        ("fraction_mission", c_uint32),    # +0x002C
        ("min_level", c_uint32),           # +0x0030
        ("max_level", c_uint32),           # +0x0034
        ("needed_pq", c_uint32),           # +0x0038
        ("mission_maps_to", c_uint32),     # +0x003C
        ("x", c_uint32),                   # +0x0040 icon position on map.
        ("y", c_uint32),                   # +0x0044
        ("icon_start_x", c_uint32),       # +0x0048
        ("icon_start_y", c_uint32),       # +0x004C
        ("icon_end_x", c_uint32),         # +0x0050
        ("icon_end_y", c_uint32),         # +0x0054
        ("icon_start_x_dupe", c_uint32),  # +0x0058
        ("icon_start_y_dupe", c_uint32),  # +0x005C
        ("icon_end_x_dupe", c_uint32),    # +0x0060
        ("icon_end_y_dupe", c_uint32),    # +0x0064
        ("file_id", c_uint32),               # +0x0068
        ("mission_chronology", c_uint32),    # +0x006C
        ("ha_map_chronology", c_uint32),     # +0x0070
        ("name_id", c_uint32),                # +0x0074
        ("description_id", c_uint32),         # +0x0078
    ]
    @property
    def file_id1(self) -> int:
        return ((self.file_id - 1) % 0xff00) + 0x100
    @property
    def file_id2(self) -> int:
        return ((self.file_id - 1) // 0xff00) + 0x100
    @property
    def has_enter_button(self) -> bool:
        return (self.flags & 0x100) != 0 or (self.flags & 0x40000) != 0
    @property
    def is_on_world_map(self) -> bool:
        return (self.flags & 0x20) == 0
    @property
    def is_pvp(self) -> bool:
        return (self.flags & 0x40001) != 0  # 0x40000 = Explorable, 0x1 = Outpost
    @property
    def is_guild_hall(self) -> bool:
        return (self.flags & 0x800000) != 0
    @property
    def is_vanquishable_area(self) -> bool:
        return (self.flags & 0x10000000) != 0
    @property
    def is_unlockable(self) -> bool:
        return (self.flags & 0x10000) != 0
    @property
    def has_mission_maps_to(self) -> bool:
        return (self.flags & 0x8000000) != 0

class InstanceInfoStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("terrain_info1_ptr", POINTER(MapDimensionsStruct)),  # +0x0000
        ("instance_type", c_uint32),                      # +0x0004 GW::Constants::InstanceType
        ("current_map_info_ptr", POINTER(AreaInfoStruct)),    # +0x0008
        ("terrain_count", c_uint32),                      # +0x000C
        ("terrain_info2_ptr", POINTER(MapDimensionsStruct)),  # +0x0010
    ]
    @property
    def terrain_info1(self) -> Optional[MapDimensionsStruct]:
        if not self.terrain_info1_ptr:
            return None
        return self.terrain_info1_ptr.contents
    
    @property
    def current_map_info(self) -> Optional[AreaInfoStruct]:
        if not self.current_map_info_ptr:
            return None
        return self.current_map_info_ptr.contents
    
    @property
    def terrain_info2(self) -> Optional[MapDimensionsStruct]:
        if not self.terrain_info2_ptr:
            return None
        return self.terrain_info2_ptr.contents

# -------------------------------------------------------------
# Native function locating InstanceInfoPtr
# -------------------------------------------------------------
    
InstanceInfo_GetPtr = NativeSymbol(
    name="GetInstanceInfoPtr",
    pattern=b"\x6A\x2C\x50\xE8\x00\x00\x00\x00\x83\xC4\x08\xC7",
    mask="xxxx????xxxx",
    offset=0x0D,  
    section=ScannerSection.TEXT
)


#region facade
class InstanceInfo:
    _ptr: int = 0
    _cached_ctx: InstanceInfoStruct | None = None
    _callback_name = "InstanceInfoContext.UpdatePtr"

    @staticmethod
    def get_ptr() -> int:
        return InstanceInfo._ptr    
    @staticmethod
    def _update_ptr():
        ptr = InstanceInfo_GetPtr.read_ptr()
        InstanceInfo._ptr = ptr
        if not ptr:
            InstanceInfo._cached_ctx = None
            return
        InstanceInfo._cached_ctx = cast(
            ptr,
            POINTER(InstanceInfoStruct)
        ).contents

    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            InstanceInfo._callback_name,
            PyCallback.Phase.PreUpdate,
            InstanceInfo._update_ptr,
            priority=3
        )


    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(InstanceInfo._callback_name)
        InstanceInfo._ptr = 0
        InstanceInfo._cached_ctx = None

    @staticmethod
    def get_context() -> InstanceInfoStruct | None:
        return InstanceInfo._cached_ctx
 
InstanceInfo.enable()

