
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER, c_wchar
from ..internals.types import Vec2f
from ..internals.gw_array import GW_Array, GW_Array_View, GW_Array_Value_View
from ..internals.helpers import read_wstr, encoded_wstr_to_str
from ..internals.native_symbol import NativeSymbol
from ...Scanner import Scanner, ScannerSection

class AvailableCharacterStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32 *2),     # unknown / flags / padding
        ("uuid_ptr", c_uint32 *4), # possibly indicates pvp or campaign character
        ("player_name_enc", c_wchar * 20),
        ("props", c_uint32 *17),
    ]
    @property
    def uuid(self) -> tuple[int, int, int, int]:
        return tuple(self.uuid_ptr)
    
    @property
    def player_name_encoded_string(self) -> str | None:
        return self.player_name_enc
    
    @property
    def player_name(self) -> str:
        name =  encoded_wstr_to_str(self.player_name_enc)
        return name if name else ""
    
    @property
    def map_id(self) -> int:
        return (self.props[0] >> 16) & 0xFFFF
    
    @property
    def primary(self) -> int:
        return (self.props[2] >> 20) & 0xF
    
    @property
    def secondary(self) -> int:
        return (self.props[7] >> 10) & 0xF
    
    @property
    def campaign(self) -> int:
        return self.props[7] & 0xF
    
    @property
    def level(self) -> int:
        return (self.props[7] >> 4) & 0x3F
    
    @property
    def is_pvp(self) -> bool:
        return ((self.props[7] >> 9) & 0x1) == 1

class AvailableCharacterArrayStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("available_characters_array", GW_Array),        # +0x00C4 Array<AvailableCharacterInfo*>
    ]
    @property
    def available_characters_list(self) -> list[AvailableCharacterStruct]:
        return GW_Array_Value_View(self.available_characters_array, AvailableCharacterStruct).to_list()

available_chars_ptr = NativeSymbol(
    name="available_chars_ptr",
    pattern=b"\x8b\x35\x00\x00\x00\x00\x57\x69\xF8\x84\x00\x00\x00",
    mask="xx????xxxxxxx",
    offset=0x2,  
    section=ScannerSection.TEXT
)

class AvailableCharacterArray:
    _ptr: int = 0
    _cached_ctx: AvailableCharacterArrayStruct | None = None
    _callback_name = "AvailableCharacterArrayContext.UpdatePtr"

    @staticmethod
    def get_ptr() -> int:
        return AvailableCharacterArray._ptr

    @staticmethod
    def _update_ptr():
        ptr = available_chars_ptr.read_ptr()
        AvailableCharacterArray._ptr = ptr
        if not ptr:
            AvailableCharacterArray._cached_ctx = None
            return
        AvailableCharacterArray._cached_ctx = cast(
            ptr,
            POINTER(AvailableCharacterArrayStruct)
        ).contents
        
    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            AvailableCharacterArray._callback_name,
            PyCallback.Phase.PreUpdate,
            AvailableCharacterArray._update_ptr,
            priority=99
        )

    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(AvailableCharacterArray._callback_name)
        AvailableCharacterArray._ptr = 0
        AvailableCharacterArray._cached_ctx = None

    @staticmethod
    def get_context() -> AvailableCharacterArrayStruct | None:
        return AvailableCharacterArray._cached_ctx
    
AvailableCharacterArray.enable()