import PyMap
from Py4GW import Game
from ctypes import Structure, c_uint32, c_float, sizeof, POINTER, cast
from ..internals.types import Vec2f
from ..internals.gw_array import GW_Array, GW_Array_View

#region MissionMapContext

class MissionMapSubContext(Structure):
    _fields_ = [
        ("h0000", c_uint32 * 0x0E),
    ]


class MissionMapSubContext2(Structure):
    _fields_ = [
        ("h0000", c_uint32),
        ("player_mission_map_pos", Vec2f),
        ("h000c", c_uint32),
        ("mission_map_size", Vec2f),
        ("unk", c_float),
        ("mission_map_pan_offset", Vec2f),
        ("mission_map_pan_offset2", Vec2f),
        ("unk2", c_float * 2),
        ("unk3", c_uint32 * 9),
    ]

assert sizeof(MissionMapSubContext2) == 0x58
class MissionMapContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("size", Vec2f),
        ("h0008", c_uint32),
        ("last_mouse_location", Vec2f),
        ("frame_id", c_uint32),
        ("player_mission_map_pos", Vec2f),
        ("h0020", GW_Array),   # GW::Array<MissionMapSubContext*>
        ("h0030", c_uint32),
        ("h0034", c_uint32),
        ("h0038", c_uint32),
        ("h003c", POINTER(MissionMapSubContext2)),
        ("h0040", c_uint32),
        ("h0044", c_uint32),
    ]
    @property
    def subcontexts(self) -> list[MissionMapSubContext]:
        return GW_Array_View(self.h0020, MissionMapSubContext).to_list()
    
    @property
    def subcontext2(self) -> MissionMapSubContext2 | None:
        if not self.h003c:
            return None
        return self.h003c.contents

assert sizeof(MissionMapContextStruct) == 0x48

class MissionMapContext:
    _ptr: int = 0
    _callback_name = "MissionMapContext.UpdateMissionMapContextPtr"

    @staticmethod
    def get_ptr() -> int:
        return MissionMapContext._ptr
    
    @staticmethod
    def _update_ptr():
        MissionMapContext._ptr = PyMap.PyMap().GetMissionMapContextPtr()

    @staticmethod
    def enable():
        Game.register_callback(
            MissionMapContext._callback_name,
            MissionMapContext._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(MissionMapContext._callback_name)
        MissionMapContext._ptr = 0

    @staticmethod
    def get_context() -> MissionMapContextStruct | None:
        ptr = MissionMapContext._ptr
        if not ptr:
            return None
        return cast(
            ptr,
            POINTER(MissionMapContextStruct)
        ).contents

MissionMapContext.enable()