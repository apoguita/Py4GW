import PyPlayer
from Py4GW import Game
from ctypes import Structure, c_uint32, c_uint8, c_wchar, POINTER, cast, c_int32
from typing import List, Optional
from ..internals.helpers import read_wstr, encoded_wstr_to_str
from ..internals.gw_array import GW_Array, GW_Array_Value_View
from ..internals.types import Vec2f   # if needed later

# -------------------------------------------------------------
# ObserverMatch::Flags (nested struct)
# -------------------------------------------------------------

class ObserverMatchFlags(Structure):
    _pack_ = 1
    _fields_ = [
        ("type",      c_uint32),  # +0x0010
        ("reserved",  c_uint32),  # +0x0014
        ("version",   c_uint32),  # +0x0018
        ("state",     c_uint32),  # +0x001C
        ("level",     c_uint32),  # +0x0020
        ("config1",   c_uint32),  # +0x0024
        ("config2",   c_uint32),  # +0x0028
        ("score1",    c_uint32),  # +0x002C
        ("score2",    c_uint32),  # +0x0030
        ("score3",    c_uint32),  # +0x0034
        ("stat1",     c_uint32),  # +0x0038
        ("stat2",     c_uint32),  # +0x003C
        ("data1",     c_uint32),  # +0x0040
        ("data2",     c_uint32),  # +0x0044
    ]


# -------------------------------------------------------------
# ObserverMatch main struct
# -------------------------------------------------------------

class ObserverMatch(Structure):
    _pack_ = 1
    _fields_ = [
        ("match_id",       c_uint32),            # +0x0000
        ("match_id_dup",   c_uint32),            # +0x0004
        ("map_id",         c_uint32),            # +0x0008
        ("age",            c_uint32),            # +0x000C
        ("flags",          ObserverMatchFlags),  # +0x0010
        ("team_name1_ptr",     POINTER(c_wchar)),    # +0x0048
        ("unknown1",       c_uint32 * 0xA),      # +0x004C
        ("team_name2_ptr",    POINTER(c_wchar)),    # +0x0074
    ]
    @property
    def team_name1_encoded_str(self) -> str | None:
        """Get team 1 name as a string."""
        if self.team_name1_ptr:
            return read_wstr(self.team_name1_ptr)
        return None
    
    @property
    def team_name1_str(self) -> str | None:
        """Get team 1 name as a decoded string."""
        encoded = self.team_name1_encoded_str
        if encoded:
            return encoded_wstr_to_str(encoded)
        return None
    
    @property
    def team_name2_encoded_str(self) -> str | None:
        """Get team 2 name as a string."""
        if self.team_name2_ptr:
            return read_wstr(self.team_name2_ptr)
        return None
    
    @property
    def team_name2_str(self) -> str | None:
        """Get team 2 name as a decoded string."""
        encoded = self.team_name2_encoded_str
        if encoded:
            return encoded_wstr_to_str(encoded)
        return None
   
    
class ProgressBar(Structure):
    _pack_ = 1
    _fields_ = [
        ("pips", c_uint32),                 # +0x0000
        ("color", c_uint8 * 4),             # +0x0004 RGBA
        ("background", c_uint8 * 4),        # +0x0008 RGBA
        ("unk", c_uint32 * 7),              # +0x000C
        ("progress", c_uint32),             # +0x0028 float 0.0 ... 1.0
        #// possibly more
    ]


class CharContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000_array", GW_Array),          # +0x0000 Array<void*>
        ("h0010", c_uint32),                # +0x0010
        ("h0014_array", GW_Array),          # +0x0014 Array<void*>
        ("h0024", c_uint32 * 4),            # +0x0024
        ("h0034_array", GW_Array),          # +0x0034 Array<void*>
        ("h0044_array", GW_Array),          # +0x0044 Array<void*>
        ("h0054", c_uint32 * 4),            # +0x0054
        ("player_uuid", c_uint32 * 4),      # +0x0064 uuid
        ("player_name_enc", c_wchar * 0x14),    # +0x0074 wchar_t[20]
        ("h009C", c_uint32 * 20),           # +0x009C
        ("h00EC_array", GW_Array),          # +0x00EC Array<void*>
        ("h00FC", c_uint32 * 37),           # +0x00FC
        ("world_flags", c_uint32),          # +0x0190
        ("token1", c_uint32),               # +0x0194 world id
        ("map_id", c_uint32),               # +0x0198 GW::Constants::MapID
        ("is_explorable", c_uint32),        # +0x019C
        ("host", c_uint8 * 0x18),           # +0x01A0
        ("token2", c_uint32),               # +0x01B8 player id
        ("h01BC", c_uint32 * 25),           # +0x01BC
        ("district_number", c_int32),      # +0x0220
        ("language", c_uint32),             # +0x0224 GW::Constants::Language
        ("observe_map_id", c_uint32),       # +0x0228
        ("current_map_id", c_uint32),       # +0x022C
        ("observe_map_type", c_uint32),     # +0x0230
        ("current_map_type", c_uint32),     # +0x0234
        ("h0238", c_uint32 * 5),            # +0x0238
        ("observer_matches_array", GW_Array), # +0x024C Array<ObserverMatch*>
        ("h025C", c_uint32 * 17),           # +0x025C
        ("player_flags", c_uint32),         # +0x02A0
        ("player_number", c_uint32),        # +0x02A4
        ("h02A8", c_uint32 * 40),           # +0x02A8
        ("progress_bar_ptr", POINTER(ProgressBar)),     # +0x0348 ProgressBar*
        ("h034C", c_uint32 * 27),           # +0x034C
        ("player_email_ptr", c_wchar * 0x40),   # +0x03B8 wchar_t[64]
    ]
    @property
    def h0000_ptrs(self) -> list[int] | None:
        """Get the list of pointers from h0000_array."""
        ptrs = GW_Array_Value_View(self.h0000_array, c_uint32).to_list()
        if not ptrs:
            return None
        return [int(p) for p in ptrs]
    @property
    def h0014_ptrs(self) -> list[int] | None:
        """Get the list of pointers from h0014_array."""
        ptrs = GW_Array_Value_View(self.h0014_array, c_uint32).to_list()
        if not ptrs:
            return None
        return [int(p) for p in ptrs]
    @property
    def h0034_ptrs(self) -> list[int] | None:
        """Get the list of pointers from h0034_array."""
        ptrs = GW_Array_Value_View(self.h0034_array, c_uint32).to_list()
        if not ptrs:
            return None
        return [int(p) for p in ptrs]
    @property
    def h0044_ptrs(self) -> list[int] | None:
        """Get the list of pointers from h0044_array."""
        ptrs = GW_Array_Value_View(self.h0044_array, c_uint32).to_list()
        if not ptrs:
            return None
        return [int(p) for p in ptrs]
    @property
    def h00EC_ptrs(self) -> list[int] | None:
        """Get the list of pointers from h00EC_array."""
        ptrs = GW_Array_Value_View(self.h00EC_array, c_uint32).to_list()
        if not ptrs:
            return None
        return [int(p) for p in ptrs]
    @property
    def observer_matches(self) -> List[ObserverMatch] | None:
        """Get the list of ObserverMatch instances."""
        #maybe needs a POINTER(ObserverMatch) instead of ObserverMatch
        array_view = GW_Array_Value_View(self.observer_matches_array,POINTER(ObserverMatch))
        ptrs = array_view.to_list()
        if not ptrs:
            return None
        return [ptr.contents for ptr in ptrs]
    @property
    def progress_bar(self) -> ProgressBar | None:
        """Get the ProgressBar instance."""
        if self.progress_bar_ptr:
            return self.progress_bar_ptr.contents
        return None
    @property
    def player_name_encoded_str(self) -> str | None:
        """Get the player name as an encoded string."""
        return self.player_name_enc
    @property
    def player_name_str(self) -> str | None:
        """Get the player name as a decoded string."""
        encoded = self.player_name_encoded_str
        if encoded:
            return encoded_wstr_to_str(encoded)
        return None
    @property
    def player_email_encoded_str(self) -> str | None:
        """Get the player email as an encoded string."""
        return self.player_email_ptr
    @property
    def player_email_str(self) -> str | None:
        """Get the player email as a decoded string."""
        encoded = self.player_email_encoded_str
        if encoded:
            return encoded_wstr_to_str(encoded)
        return None
    

#region Facade
class CharContext:
    _ptr: int = 0
    _callback_name = "CharContext.UpdateCharContextPtr"

    @staticmethod
    def get_ptr() -> int:
        return CharContext._ptr

    @staticmethod
    def _update_ptr():
        CharContext._ptr = PyPlayer.PyPlayer().GetCharContextPtr()

    @staticmethod
    def enable():
        Game.register_callback(
            CharContext._callback_name,
            CharContext._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(CharContext._callback_name)
        CharContext._ptr = 0

    @staticmethod
    def get_context() -> CharContextStruct | None:
        ptr = CharContext._ptr
        if not ptr:
            return None
        return cast(
            ptr,
            POINTER(CharContextStruct)
        ).contents
        
        
        
CharContext.enable()