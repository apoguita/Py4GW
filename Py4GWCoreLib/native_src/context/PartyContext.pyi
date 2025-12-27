from typing import List, Optional
from ctypes import Structure
from ..internals.types import CPointer
from ..internals.gw_array import GW_Array
from ..internals.gw_list import GW_TList, GW_TLink


# ------------------------------------------------------------
# Party info
# ------------------------------------------------------------
class PlayerPartyMember:
    login_number: int
    called_target_id: int
    state : int
    @property
    def is_connected(self) ->  bool: ...
    @property
    def is_ticked(self) ->  bool: ...
    
class HeroPartyMember:
    agent_id: int
    owner_player_id: int
    hero_id: int
    h000C: int
    h0010: int
    level: int
    
class HenchmanPartyMember:
    agent_id: int
    h0004: list[int]
    profession: int
    level: int

class PartyInfoStruct(Structure):
    party_id: int
    players_array: GW_Array
    henchmen_array: GW_Array
    heroes_array: GW_Array
    others_array: GW_Array
    h0044: list[int]
    invite_link: GW_TLink

    @property
    def players(self) -> List[PlayerPartyMember]: ...
    @property
    def henchmen(self) -> List[HenchmanPartyMember]: ...
    @property
    def heroes(self) -> List[HeroPartyMember]: ...
    @property
    def others(self) -> List[int]: ...
    @property
    def invite_links(self) -> List["PartyInfoStruct"]: ...


# ------------------------------------------------------------
# Party search structs
# ------------------------------------------------------------

class PartySearchStruct(Structure):
    party_search_id: int
    party_search_type: int
    hardmode: int
    district: int
    language: int
    party_size: int
    hero_count: int
    message: str      # wchar_t[32]
    party_leader: str # wchar_t[20]
    primary: int
    secondary: int
    level: int
    timestamp: int
    
    @property
    def message_encoded_str(self) -> str: ...
    
    @property
    def message_str(self) -> str | None:...
    
    @property
    def party_leader_encoded_str(self) -> str:...
    @property
    def party_leader_str(self) -> str | None:...


# ------------------------------------------------------------
# Party context
# ------------------------------------------------------------

class PartyContextStruct(Structure):
    h0000: int
    h0004_array: GW_Array
    flag: int
    h0018: int
    request_list: GW_TList
    requests_count: int
    sending_list: GW_TList
    sending_count: int
    h003C: int
    parties_array: GW_Array
    h0050: int
    player_party_ptr: Optional[CPointer[PartyInfoStruct]]
    h0058: list[int]
    party_search_array: GW_Array

    @property
    def in_hard_mode(self) -> bool: ...
    @property
    def is_defeated(self) -> bool: ...
    @property
    def is_party_leader(self) -> bool: ...

    @property
    def h0004_ptrs(self) -> List[int]: ...
    @property
    def request(self) -> List[PartyInfoStruct]: ...
    @property
    def sending(self) -> List[PartyInfoStruct]: ...
    @property
    def parties(self) -> List[PartyInfoStruct]: ...
    @property
    def player_party(self) -> Optional[PartyInfoStruct]: ...
    @property
    def party_searches(self) -> List[PartySearchStruct]: ...


# ------------------------------------------------------------
# Context facade
# ------------------------------------------------------------

class PartyContext:
    @staticmethod
    def get_ptr() -> int: ...
    @staticmethod
    def enable() -> None: ...
    @staticmethod
    def disable() -> None: ...
    @staticmethod
    def get_context() -> Optional[PartyContextStruct]: ...
