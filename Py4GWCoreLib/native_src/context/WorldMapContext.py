import PyMap
from Py4GW import Game
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER
from ..internals.types import Vec2f

#region WorldMapContext
class WorldMapContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("frame_id", c_uint32),     # 0x0000
        ("h0004", c_uint32),        # 0x0004
        ("h0008", c_uint32),        # 0x0008
        ("h000c", c_float),         # 0x000C
        ("h0010", c_float),         # 0x0010
        ("h0014", c_uint32),        # 0x0014
        ("h0018", c_float),         # 0x0018
        ("h001c", c_float),         # 0x001C
        ("h0020", c_float),         # 0x0020
        ("h0024", c_float),         # 0x0024
        ("h0028", c_float),         # 0x0028
        ("h002c", c_float),         # 0x002C
        ("h0030", c_float),         # 0x0030
        ("h0034", c_float),         # 0x0034

        ("zoom", c_float),          # 0x0038

        ("top_left", Vec2f),        # 0x003C
        ("bottom_right", Vec2f),    # 0x0044

        ("h004c", c_uint32 * 7),    # 0x004C → 0x0068

        ("h0068", c_float),         # 0x0068
        ("h006c", c_float),         # 0x006C

        ("params", c_uint32 * 0x6D) # 0x0070 → 0x224
    ]

assert sizeof(WorldMapContextStruct) == 0x224

class WorldMapContext:
    _ptr: int = 0
    _cached_ptr: int = 0
    _cached_ctx: WorldMapContextStruct | None = None
    _callback_name = "WorldMapContext.UpdateWorldMapContextPtr"

    @staticmethod
    def get_ptr() -> int:
        return WorldMapContext._ptr
    
    @staticmethod
    def _update_ptr():
        WorldMapContext._ptr = PyMap.PyMap().GetWorldMapContextPtr()

    @staticmethod
    def enable():
        Game.register_callback(
            WorldMapContext._callback_name,
            WorldMapContext._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(WorldMapContext._callback_name)
        WorldMapContext._ptr = 0
        WorldMapContext._cached_ptr = 0
        WorldMapContext._cached_ctx = None

    @staticmethod
    def get_context() -> WorldMapContextStruct | None:
        ptr = WorldMapContext._ptr
        if not ptr:
            WorldMapContext._cached_ptr = 0
            WorldMapContext._cached_ctx = None
            return None
        
        if ptr != WorldMapContext._cached_ptr:
            WorldMapContext._cached_ptr = ptr
            WorldMapContext._cached_ctx = cast(
                ptr,
                POINTER(WorldMapContextStruct)
            ).contents
            
        return WorldMapContext._cached_ctx

WorldMapContext.enable()