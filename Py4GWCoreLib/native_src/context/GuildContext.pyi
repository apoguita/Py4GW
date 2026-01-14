from typing import List, Optional
from ctypes import Structure
from ..internals.types import CPointer
from ..internals.gw_array import GW_Array

class GHKey(Structure):
    key_data: List[int]
    @property
    def as_string(self) -> str: ...
    @classmethod
    def from_hex(cls, hex_string: str) -> "GHKey": ...

        
class CapeDesign():
    cape_bg_color: int
    cape_detail_color: int
    cape_emblem_color: int
    cape_shape: int
    cape_detail: int
    cape_emblem: int
    cape_trim: int

       
class TownAlliance():
    rank: int
    allegiance: int
    faction: int
    name_enc: str
    tag_enc: str
    cape: CapeDesign
    map_id: int

    @property
    def name_encoded_str(self) -> str | None:...
    @property
    def name_str(self) -> str | None:...
    @property
    def tag_encoded_str(self) -> str | None:...
    @property
    def tag_str(self) -> str | None:...
    
class GuildHistoryEvent():
    time1: int
    time2: int
    name_enc: str

    @property
    def name_encoded_str(self) -> str | None:...
    
    @property
    def name_str(self) -> str | None:...
    
    
class Guild ():
    key: GHKey
    h0010: List[int]
    index: int  # Same as PlayerGuildIndex
    rank: int
    features: int
    name_enc: str
    rating: int
    faction: int  # 0=kurzick, 1=luxon
    faction_point: int
    qualifier_point: int
    tag_enc: str
    cape: CapeDesign

    @property
    def name_encoded_str(self) -> str | None:...
    @property
    def name_str(self) -> str | None:...
    @property
    def tag_encoded_str(self) -> str | None:...
    @property
    def tag_str(self) -> str | None:...
    
class GuildPlayer():
    vtable: int
    name_ptr: CPointer[str]
    invited_name_enc: str
    current_name_enc: str
    inviter_name_enc: str
    invite_time: int
    promoter_name_enc: str
    h00AC: List[int]
    offline: int
    member_type: int
    status: int
    h00E8: List[int]

    @property
    def name_encoded_str(self) -> str | None:...
    @property
    def name_str(self) -> str | None:...
    @property
    def invited_name_encoded_str(self) -> str | None:...
    @property
    def invited_name_str(self) -> str | None:...
    @property
    def current_name_encoded_str(self) -> str | None:...
    @property
    def current_name_str(self) -> str | None:...
    @property
    def inviter_name_encoded_str(self) -> str | None:...
    @property
    def inviter_name_str(self) -> str | None:...
    @property
    def promoter_name_encoded_str(self) -> str | None:...
    @property
    def promoter_name_str(self) -> str | None:...


class GuildContextStruct():
    h0000: int
    h0004: int
    h0008: int
    h000C: int
    h0010: int
    h0014: int
    h0018: int
    h001C: int
    h0020_array: GW_Array # Array<void *>
    h0030: int
    player_name_enc: str
    h005C: int
    player_guild_index: int
    player_gh_key: GHKey
    h0074: int
    announcement_enc: str
    announcement_author_enc: str
    player_guild_rank: int
    h02A4: int
    factions_outpost_guilds_array: GW_Array #Array<TownAlliance>
    kurzick_town_count: int
    luxon_town_count: int
    h02C0: int
    h02C4: int
    h02C8: int
    player_guild_history_array: GW_Array #Array<GuildHistoryEvent*>
    h02DC: List[int]
    guild_array_array: int # Array<Guild *> GuildArray;
    h0308: List[int]
    h0318_array: GW_Array # Array<void *>
    h0328: int
    h032C_array: GW_Array # Array<void *>
    h033C: List[int]
    player_roster_array: GW_Array # Array<GuildPlayer *> GuildRoster;

    @property
    def h0020_ptrs(self) -> list[int] | None:...
    @property
    def player_name_encoded_str(self) -> str | None:...
    @property
    def player_name_str(self) -> str | None:...
    @property
    def announcement_encoded_str(self) -> str | None:...
    @property
    def announcement_str(self) -> str | None:...
    @property
    def announcement_author_encoded_str(self) -> str | None:...
    @property
    def announcement_author_str(self) -> str | None:...
    @property
    def factions_outpost_guilds(self) -> List[TownAlliance] | None:...
    @property
    def player_guild_history(self) -> List[GuildHistoryEvent] | None:...
    @property
    def guild_array(self) -> List[Guild] | None:...
    @property
    def h0318_ptrs(self) -> list[int] | None:...
    @property
    def h032C_ptrs(self) -> list[int] | None:...
    @property
    def player_roster(self) -> List[GuildPlayer] | None:...
    
#region Facade
class GuildContext:
    @staticmethod
    def get_ptr() -> int:...
    @staticmethod
    def _update_ptr():...
    @staticmethod
    def enable():...

    @staticmethod
    def disable():...

    @staticmethod
    def get_context() -> GuildContextStruct | None:...
        
        
        
GuildContext.enable()