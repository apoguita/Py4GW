import PyPlayer
from Py4GW import Game
import math
from typing import ClassVar, Optional
from ctypes import (
    Structure, POINTER,
    c_uint32, c_float, c_void_p, c_wchar, c_uint8,c_uint16,c_int32,
    cast
)

from Py4GWCoreLib.native_src.context.InstanceInfoContext import InstanceInfo
from ..internals.helpers import read_wstr, encoded_wstr_to_str
from ..internals.types import Vec2f, Vec3f, GamePos
from ..internals.gw_array import GW_Array, GW_Array_View, GW_Array_Value_View
from ..internals.native_symbol import NativeSymbol
from ...Scanner import Scanner, ScannerSection
from ..internals.prototypes import Prototypes

#region_id_addr
class ServerRegionStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("region_id", c_int32),      # +0x0000
    ]
    
ServerRegion_GetPtr = NativeSymbol(
    name="ServerRegion_GetPtr",
    pattern=b"\x6a\x54\x8d\x46\x24\x89\x08",
    mask="xxxxxxx",
    offset=-0x4,  
    section=ScannerSection.TEXT
)

#region facade
class ServerRegion:
    _ptr: int = 0
    _cached_ctx: ServerRegionStruct | None = None
    _callback_name = "ServerRegion.UpdatePtr"

    @staticmethod
    def get_ptr() -> int:
        return ServerRegion._ptr    
    @staticmethod
    def _update_ptr():
        ptr = ServerRegion_GetPtr.read_ptr()
        ServerRegion._ptr = ptr
        if not ptr:
            ServerRegion._cached_ctx = None
            return
        
        ServerRegion._cached_ctx = cast(
            ptr,
            POINTER(ServerRegionStruct)
        ).contents

    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            ServerRegion._callback_name,
            PyCallback.Phase.PreUpdate,
            ServerRegion._update_ptr,
            priority = 0,
            context=PyCallback.Context.Draw
        )

    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(ServerRegion._callback_name)
        ServerRegion._ptr = 0
        ServerRegion._cached_ctx = None

    @staticmethod
    def get_context() -> ServerRegionStruct | None:
        return ServerRegion._cached_ctx
        
        
        
ServerRegion.enable()
