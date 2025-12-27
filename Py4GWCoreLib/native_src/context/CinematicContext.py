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
class CinematicStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32),      # +0x0000
        ("h0004", c_uint32),      # +0x0004
    ]

#region facade
class Cinematic:
    _ptr: int = 0
    _callback_name = "Cinematic.UpdateCinematicPtr"

    @staticmethod
    def get_ptr() -> int:
        return Cinematic._ptr    
    @staticmethod
    def _update_ptr():
        Cinematic._ptr = PyPlayer.PyPlayer().GetCinematicPtr()

    @staticmethod
    def enable():
        Game.register_callback(
            Cinematic._callback_name,
            Cinematic._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(Cinematic._callback_name)
        Cinematic._ptr = 0

    @staticmethod
    def get_context() -> CinematicStruct | None:
        ptr = Cinematic._ptr
        if not ptr:
            return None
        return cast(
            ptr,
            POINTER(CinematicStruct)
        ).contents
        
        
        
Cinematic.enable()
