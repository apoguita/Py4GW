import PyPlayer
from Py4GW import Game
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER, c_wchar
from ..internals.types import Vec2f
from ..internals.gw_array import GW_Array


class LoginCharacter(Structure):
    _pack_ = 1
    _fields_ = [
        ("unk0", c_uint32  * 0x13),     # unknown / flags / padding
        ("character_name", c_wchar * 20),
    ]

class PreGameContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("frame_id", c_uint32),            
        ("h0004", c_uint32 * 52),             
        ("chosen_character_index", c_uint32),
        ("UNK01", c_uint32),              
        ("chars", GW_Array),  # (GW::Array<LoginCharacter>)
    ]

class PreGameContext:
    _ptr: int = 0
    _callback_name = "PreGameContext.UpdatePreGameContextPtr"

    @staticmethod
    def get_ptr() -> int:
        return PreGameContext._ptr

    @staticmethod
    def _update_ptr():
        PreGameContext._ptr = PyPlayer.PyPlayer().GetPreGameContextPtr()

    @staticmethod
    def enable():
        Game.register_callback(
            PreGameContext._callback_name,
            PreGameContext._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(PreGameContext._callback_name)
        PreGameContext._ptr = 0

    @staticmethod
    def get_context() -> PreGameContextStruct | None:
        ptr = PreGameContext._ptr
        if not ptr:
            return None
        return cast(
            ptr,
            POINTER(PreGameContextStruct)
        ).contents

PreGameContext.enable()