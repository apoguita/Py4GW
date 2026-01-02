import PyPlayer
from Py4GW import Game
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER, c_wchar
from ..internals.types import Vec2f
from ..internals.gw_array import GW_Array, GW_Array_View, GW_Array_Value_View
from ..internals.helpers import read_wstr, encoded_wstr_to_str


class LoginCharacter(Structure):
    _pack_ = 1
    _fields_ = [
        ("Unk00", c_uint32),     # unknown / flags / padding
        ("pvp_or_campaign", c_uint32), # possibly indicates pvp or campaign character
        ("UnkPvPData01", c_uint32),
        ("UnkPvPData02", c_uint32),
        ("UnkPvPData03", c_uint32),
        ("UnkPvPData04", c_uint32),
        ("Unk01", c_uint32  * 0x4),
        ("level", c_uint32),
        ("current_map_id", c_uint32),
        ("Unk02", c_uint32  * 0x7),     # unknown / flags / padding
        ("character_name_enc", c_wchar * 20),
    ]
    @property
    def character_name_encoded_string(self) -> str | None:
        return self.character_name_enc
    
    @property
    def character_name(self) -> str | None:
        return encoded_wstr_to_str(self.character_name_enc)


class PreGameContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("frame_id", c_uint32), 
        ("Unk01", c_uint32 * 20),  
        ("h0054", c_float), #20
        ("h0058", c_float), #21
        ("Unk02", c_uint32 * 2),
        ("h0060", c_float), #24
        ("Unk03", c_uint32 * 2),
        ("h0068", c_float), #27
        ("Unk04", c_uint32),
        ("h0070", c_float), #29
        ("Unk05", c_uint32),
        ("h0078", c_float), #31
        ("Unk06", c_uint32 * 8),
        ("h00a0", c_float), #40
        ("h00a4", c_float), #41
        ("h00a8", c_float), #42
        ("Unk07", c_uint32 * 9),             
        ("chosen_character_index", c_uint32),
        ("Unk08", c_uint32),              
        ("chars_array", GW_Array),  # (GW::Array<LoginCharacter>)
    ]
    
    @property
    def chars_list(self) -> list[LoginCharacter]:
        return GW_Array_Value_View(self.chars_array, LoginCharacter).to_list()

class PreGameContext:
    _ptr: int = 0
    _cached_ptr: int = 0
    _cached_ctx: PreGameContextStruct | None = None
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
        PreGameContext._cached_ptr = 0
        PreGameContext._cached_ctx = None

    @staticmethod
    def get_context() -> PreGameContextStruct | None:
        ptr = PreGameContext._ptr
        if not ptr:
            PreGameContext._cached_ptr = 0
            PreGameContext._cached_ctx = None
            return None
        
        if ptr != PreGameContext._cached_ptr:
            PreGameContext._cached_ptr = ptr
            PreGameContext._cached_ctx = cast(
                ptr,
                POINTER(PreGameContextStruct)
            ).contents
            
        return PreGameContext._cached_ctx
PreGameContext.enable()