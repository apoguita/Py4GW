import PyPointers
from ctypes import Structure, c_uint32, c_uint8, c_wchar, POINTER, cast, c_int32, c_void_p
from typing import List, Optional
from ..internals.helpers import read_wstr, encoded_wstr_to_str
from ..internals.gw_array import GW_Array, GW_Array_Value_View
from ..internals.types import Vec2f   # if needed later



class GHKey(Structure):
    _pack_ = 1
    _fields_ = [
        ("key_data", c_uint8 * 4),
    ]
    @property
    def as_string(self) -> str:
        return ''.join(f'{byte:02X}' for byte in self.key_data)
    
    @classmethod
    def from_hex(cls, hex_string: str) -> "GHKey":
        """Create a GHKey instance from a hexadecimal string."""
        if len(hex_string) != 8:
            raise ValueError("Hex string must be exactly 8 characters long.")
        key_bytes = bytes.fromhex(hex_string)
        key_instance = cls()
        for i in range(4):
            key_instance.key_data[i] = key_bytes[i]
        return key_instance
        
class CapeDesign(Structure):
    _pack_ = 1
    _fields_ = [
        ("cape_bg_color", c_uint32),
        ("cape_detail_color", c_uint32),
        ("cape_emblem_color", c_uint32),
        ("cape_shape", c_uint32),
        ("cape_detail", c_uint32),
        ("cape_emblem", c_uint32),
        ("cape_trim", c_uint32),
    ]
       
class TownAlliance(Structure):
    _pack_ = 1
    _fields_ = [
        ("rank", c_uint32),  
        ("allegiance", c_uint32), 
        ("faction", c_uint32), 
        ("name_enc", c_wchar * 32),
        ("tag_enc", c_wchar * 5),
        ("_padding", c_uint8 *2),
        ("cape", CapeDesign), 
        ("map_id", c_uint32),
    ]
    @property
    def name_encoded_str(self) -> str | None:
        return self.name_enc
    @property
    def name_str(self) -> str | None:
        return encoded_wstr_to_str(self.name_enc)
    @property
    def tag_encoded_str(self) -> str | None:
        return self.tag_enc
    @property
    def tag_str(self) -> str | None:
        return encoded_wstr_to_str(self.tag_enc)
    
class GuildHistoryEvent(Structure):
    _pack_ = 1
    _fields_ = [
        ("time1", c_uint32),  # Guessing one of these is time in ms
        ("time2", c_uint32),
        ("name_enc", c_wchar * 256),  # Name of added/kicked person, then the adder/kicker, they seem to be in the same array
    ]
    @property
    def name_encoded_str(self) -> str | None:
        return self.name_enc
    
    @property
    def name_str(self) -> str | None:
        return encoded_wstr_to_str(self.name_enc)
    
    
class Guild (Structure):
    _pack_ = 1
    _fields_ = [
        ("key", GHKey),  
        ("h0010", c_uint32 * 5), 
        ("index", c_uint32), # Same as PlayerGuildIndex
        ("rank", c_uint32), 
        ("features", c_uint32), 
        ("name_enc", c_wchar * 32), 
        ("rating", c_uint32), 
        ("faction", c_uint32), # 0=kurzick, 1=luxon
        ("faction_point", c_uint32), 
        ("qualifier_point", c_uint32), 
        ("tag_enc", c_wchar * 8), 
        ("cape", CapeDesign), 
    ]
    @property
    def name_encoded_str(self) -> str | None:
        return self.name_enc
    @property
    def name_str(self) -> str | None:
        return encoded_wstr_to_str(self.name_enc)
    @property
    def tag_encoded_str(self) -> str | None:
        return self.tag_enc
    @property
    def tag_str(self) -> str | None:
        return encoded_wstr_to_str(self.tag_enc)
    
class GuildPlayer(Structure):
    _pack_ = 1
    _fields_ = [
        ("vtable",          c_void_p),           # +0x0000
        ("name_ptr",        POINTER(c_wchar)),   # +0x0004 (wchar_t*)
        ("invited_name_enc",    c_wchar * 20),       # +0x0008
        ("current_name_enc",    c_wchar * 20),       # +0x0030
        ("inviter_name_enc",    c_wchar * 20),       # +0x0058
        ("invite_time",     c_uint32),           # +0x0080
        ("promoter_name_enc",   c_wchar * 20),       # +0x0084
        ("h00AC",           c_uint32 * 12),      # +0x00AC
        ("offline",         c_uint32),           # +0x00DC
        ("member_type",     c_uint32),           # +0x00E0
        ("status",          c_uint32),           # +0x00E4
        ("h00E8",           c_uint32 * 35),      # +0x00E8
    ]
    @property
    def name_encoded_str(self) -> str | None:
        if self.name_ptr:
            return read_wstr(self.name_ptr)
        return None
    @property
    def name_str(self) -> str | None:
        encoded = self.name_encoded_str
        if self.name_ptr:
            return encoded_wstr_to_str(encoded)
        return None
    @property
    def invited_name_encoded_str(self) -> str | None:
        return self.invited_name_enc
    @property
    def invited_name_str(self) -> str | None:
        return encoded_wstr_to_str(self.invited_name_enc)
    @property
    def current_name_encoded_str(self) -> str | None:
        return self.current_name_enc
    @property
    def current_name_str(self) -> str | None:
        return encoded_wstr_to_str(self.current_name_enc)
    @property
    def inviter_name_encoded_str(self) -> str | None:
        return self.inviter_name_enc
    @property
    def inviter_name_str(self) -> str | None:
        return encoded_wstr_to_str(self.inviter_name_enc)
    @property
    def promoter_name_encoded_str(self) -> str | None:
        return self.promoter_name_enc
    @property
    def promoter_name_str(self) -> str | None:
        return encoded_wstr_to_str(self.promoter_name_enc)


class GuildContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32),  
        ("h0004", c_uint32), 
        ("h0008", c_uint32), 
        ("h000C", c_uint32), 
        ("h0010", c_uint32),
        ("h0014", c_uint32),  
        ("h0018", c_uint32), 
        ("h001C", c_uint32), 
        ("h0020_array", GW_Array), # Array<void *>
        ("h0030", c_uint32),
        ("player_name_enc", c_wchar * 20),
        ("h005C", c_uint32),  
        ("player_guild_index", c_uint32), 
        ("player_gh_key", GHKey), 
        ("h0074", c_uint32), 
        ("announcement_enc", c_wchar * 256),
        ("announcement_author_enc", c_wchar * 20),
        ("player_guild_rank", c_uint32),
        ("h02A4", c_uint32),
        ("factions_outpost_guilds_array", GW_Array), #Array<TownAlliance>
        ("kurzick_town_count", c_uint32),
        ("luxon_town_count", c_uint32),
        ("h02C0", c_uint32),
        ("h02C4", c_uint32),
        ("h02C8", c_uint32),
        ("player_guild_history_array", GW_Array), #Array<GuildHistoryEvent*>
        ("h02DC", c_uint32 * 7),
        ("guild_array_array", GW_Array), # Array<Guild *> GuildArray;
        ("h0308", c_uint32 * 4),
        ("h0318_array", GW_Array), # Array<void *>
        ("h0328", c_uint32),
        ("h032C_array", GW_Array), # Array<void *>
        ("h033C", c_uint32 *7),
        ("player_roster_array", GW_Array), # Array<GuildPlayer *> GuildRoster;
    ]
    @property
    def h0020_ptrs(self) -> list[int] | None:
        """Get the list of pointers from h0020_array."""
        ptrs = GW_Array_Value_View(self.h0020_array, c_uint32).to_list()
        if not ptrs:
            return None
        return [int(p) for p in ptrs]
    @property
    def player_name_encoded_str(self) -> str | None:
        return self.player_name_enc
    @property
    def player_name_str(self) -> str | None:
        encoded = self.player_name_encoded_str
        if encoded:
            return encoded_wstr_to_str(encoded)
        return None
    @property
    def announcement_encoded_str(self) -> str | None:
        return self.announcement_enc
    @property
    def announcement_str(self) -> str | None:
        encoded = self.announcement_encoded_str
        if encoded:
            return encoded_wstr_to_str(encoded)
        return None
    @property
    def announcement_author_encoded_str(self) -> str | None:
        return self.announcement_author_enc
    @property
    def announcement_author_str(self) -> str | None:
        encoded = self.announcement_author_encoded_str
        if encoded:
            return encoded_wstr_to_str(encoded)
        return None
    @property
    def factions_outpost_guilds(self) -> List[TownAlliance] | None:
        """Get the list of TownAlliance instances."""
        array_view = GW_Array_Value_View(self.factions_outpost_guilds_array,POINTER(TownAlliance))
        ptrs = array_view.to_list()
        if not ptrs:
            return None
        return [ptr.contents for ptr in ptrs]
    @property
    def player_guild_history(self) -> List[GuildHistoryEvent] | None:
        """Get the list of GuildHistoryEvent instances."""
        array_view = GW_Array_Value_View(self.player_guild_history_array,POINTER(GuildHistoryEvent))
        ptrs = array_view.to_list()
        if not ptrs:
            return None
        return [ptr.contents for ptr in ptrs]
    @property
    def guild_array(self) -> List[Guild] | None:
        """Get the list of Guild instances."""
        array_view = GW_Array_Value_View(self.guild_array_array,POINTER(Guild))
        ptrs = array_view.to_list()
        if not ptrs:
            return None
        return [ptr.contents for ptr in ptrs]
    
    @property
    def h0318_ptrs(self) -> list[int] | None:
        """Get the list of pointers from h0318_array."""
        ptrs = GW_Array_Value_View(self.h0318_array, c_uint32).to_list()
        if not ptrs:
            return None
        return [int(p) for p in ptrs]
    @property
    def h032C_ptrs(self) -> list[int] | None:
        """Get the list of pointers from h032C_array."""
        ptrs = GW_Array_Value_View(self.h032C_array, c_uint32).to_list()
        if not ptrs:
            return None
        return [int(p) for p in ptrs]
    @property
    def player_roster(self) -> List[GuildPlayer] | None:
        """Get the list of GuildPlayer instances."""
        array_view = GW_Array_Value_View(self.player_roster_array,POINTER(GuildPlayer))
        ptrs = array_view.to_list()
        if not ptrs:
            return None
        return [ptr.contents for ptr in ptrs]
    
#region Facade
class GuildContext:
    _ptr: int = 0
    _cached_ctx: GuildContextStruct | None = None
    _callback_name = "GuildContext.UpdatePtr"

    @staticmethod
    def get_ptr() -> int:
        return GuildContext._ptr
    @staticmethod
    def _update_ptr():
        ptr = PyPointers.PyPointers.GetGuildContextPtr()
        GuildContext._ptr = ptr
        if not ptr:
            GuildContext._cached_ctx = None
            return
        GuildContext._cached_ctx = cast(
            ptr,
            POINTER(GuildContextStruct)
        ).contents

    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            GuildContext._callback_name,
            PyCallback.Phase.PreUpdate,
            GuildContext._update_ptr,
            priority=99
        )

    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(GuildContext._callback_name)
        GuildContext._ptr = 0
        GuildContext._cached_ctx = None

    @staticmethod
    def get_context() -> GuildContextStruct | None:
        return GuildContext._cached_ctx
        
        
        
GuildContext.enable()