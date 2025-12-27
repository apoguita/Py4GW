import PyParty
from Py4GW import Game
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER, c_wchar, c_uint8
from ..internals.types import Vec2f
from ..internals.gw_array import GW_Array, GW_Array_Value_View, GW_Array_View
from ..internals.gw_list import GW_TList, GW_TList_View, GW_TLink
from typing import List, Optional
from ..internals.helpers import read_wstr, encoded_wstr_to_str

class PlayerPartyMember(Structure):
    _pack_ = 1
    _fields_ = [
        ("login_number", c_uint32),      # +0x00
        ("called_target_id", c_uint32),  # +0x04
        ("state", c_uint32),             # +0x08
    ]
    @property
    def is_connected(self) ->  bool:
        return (self.state & 1) > 0
    @property
    def is_ticked(self) ->  bool:
        return (self.state & 2) > 0
    
class HeroPartyMember(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),          # +0x00
        ("owner_player_id", c_uint32),   # +0x04
        ("hero_id", c_uint32),           # +0x08
        ("h000C", c_uint32),             # +0x0C
        ("h0010", c_uint32),             # +0x10
        ("level", c_uint32),             # +0x14
    ]  
    
class HenchmanPartyMember(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),          # +0x00
        ("h0004", c_uint32 * 10),       # +0x04
        ("profession", c_uint32),       # +0x2C
        ("level", c_uint32),             # +0x30
    ]




class PartyInfoStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("party_id", c_uint32),  # 0x00
        ("players_array", GW_Array),  # 0x04 Array<PlayerPartyMember>
        ("henchmen_array", GW_Array),  # 0x14 Array<HenchmanPartyMember>
        ("heroes_array", GW_Array),  # 0x24 Array<HeroPartyMember>
        ("others_array", GW_Array),  # 0x34 Array<AgentID>
        ("h0044", c_uint32 * 14),  # 0x44
        ("invite_link", GW_TLink),  # 0x7C TLink<PartyInfo>
    ]


    @property
    def players(self) -> list[PlayerPartyMember]:
        ptrs = GW_Array_Value_View(self.players_array, PlayerPartyMember).to_list()
        if not ptrs:
            return []
        return [ptr for ptr in ptrs]
    
    @property
    def henchmen(self) -> list[HenchmanPartyMember]:
        ptrs = GW_Array_Value_View(self.henchmen_array, HenchmanPartyMember).to_list()
        if not ptrs:
            return []
        return [ptr for ptr in ptrs]
    
    @property
    def heroes(self) -> list[HeroPartyMember]:
        ptrs = GW_Array_Value_View(self.heroes_array, HeroPartyMember).to_list()
        if not ptrs:
            return []
        return [ptr for ptr in ptrs]
    
    @property
    def others(self) -> list[int]:
        ptrs = GW_Array_Value_View(self.others_array, c_uint32).to_list()
        if not ptrs:
            return []
        return [int(ptr) for ptr in ptrs]
    
    @property
    def invite_links(self) -> List["PartyInfoStruct"]:
        """
        Returns forward chain of PartyInfoStructs starting from THIS node,
        same style as array properties -> returns a list.
        Does NOT require the list head.
        """
        result: List[PartyInfoStruct] = []
        visited = set()

        # start from this node's invite_link
        curr_link = self.invite_link

        while True:
            next_addr = int(curr_link.next_node)

            # termination checks
            if next_addr == 0 or (next_addr & 1) or next_addr in visited:
                break

            visited.add(next_addr)
            next_addr &= ~1  # mask flag bit

            # cast to PartyInfoStruct*
            next_node = cast(next_addr, POINTER(PartyInfoStruct)).contents
            result.append(next_node)

            # move forward to linked node's invite_link
            curr_link = next_node.invite_link

        return result
    

class PartySearchStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("party_search_id", c_uint32),        # +0x0000
        ("party_search_type", c_uint32),      # +0x0004
        ("hardmode", c_uint32),               # +0x0008
        ("district", c_uint32),               # +0x000C
        ("language", c_uint32),               # +0x0010
        ("party_size", c_uint32),             # +0x0014
        ("hero_count", c_uint32),             # +0x0018
        ("message", c_wchar * 32),            # +0x001C  wchar_t[32]
        ("party_leader", c_wchar * 20),       # +0x005C  wchar_t[20]
        ("primary", c_uint32),                # +0x0084  Profession enum
        ("secondary", c_uint32),              # +0x0088  Profession enumNativeParty
        ("level", c_uint32),                  # +0x008C
        ("timestamp", c_uint32),              # +0x0090
    ]

    @property
    def message_encoded_str(self) -> str:
        return self.message
    
    @property
    def message_str(self) -> str | None:
        return encoded_wstr_to_str(self.message_encoded_str)
    
    @property
    def party_leader_encoded_str(self) -> str:
        return self.party_leader
    @property
    def party_leader_str(self) -> str | None:
        return encoded_wstr_to_str(self.party_leader_encoded_str)

class PartyContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32),                     # +0x00
        ("h0004_array", GW_Array),               # +0x04 Array<void*>
        ("flag", c_uint32),                      # +0x14
        ("h0018", c_uint32),                     # +0x18
        ("request_list", GW_TList),                  # +0x1C TList<PartyInfoStruct>
        ("requests_count", c_uint32),            # +0x28
        ("sending_list", GW_TList),                   # +0x2C TList<PartyInfoStruct>
        ("sending_count", c_uint32),             # +0x38
        ("h003C", c_uint32),                     # +0x3C
        ("parties_array", GW_Array),             # +0x40 Array<PartyInfoStruct*>
        ("h0050", c_uint32),                     # +0x50
        ("player_party_ptr", POINTER(PartyInfoStruct)),  # +0x54 PartyInfoStruct*
        ("h0058", c_uint8 * 104),                # +0x58 uint8_t[104]
        ("party_search_array", GW_Array),        # +0xC0 Array<PartySearch*>
    ]
    @property
    def in_hard_mode(self) -> bool:
        return (self.flag & 0x10) > 0
    @property
    def is_defeated(self) -> bool:
        return (self.flag & 0x20) > 0
    @property
    def is_party_leader(self) -> bool:
        return (self.flag >> 0x7) & 1
    @property
    def h0004_ptrs(self) -> list[int]:
        ptrs = GW_Array_Value_View(self.h0004_array, c_uint32).to_list()
        if not ptrs:
            return []
        return [int(ptr) for ptr in ptrs]
    @property
    def request(self) -> List[PartyInfoStruct]:
        return GW_TList_View(self.request_list, PartyInfoStruct).to_list()
    @property
    def sending(self) -> List[PartyInfoStruct]:
        return GW_TList_View(self.sending_list, PartyInfoStruct).to_list()
    @property
    def parties(self) -> List[PartyInfoStruct] | None:
        parties = GW_Array_Value_View(self.parties_array, PartyInfoStruct).to_list()
        if not parties:
            return []
        return [party for party in parties]
    @property
    def player_party(self) -> Optional[PartyInfoStruct]:
        ptr = self.player_party_ptr
        if not ptr:
            return None
        return ptr.contents
    @property
    def party_searches(self) -> List[PartySearchStruct] | None:
        searches = GW_Array_Value_View(self.party_search_array, PartySearchStruct).to_list()
        if not searches:
            return []
        return [search for search in searches]

class PartyContext:
    _ptr: int = 0
    _callback_name = "PartyContext.UpdatePartyContextPtr"

    @staticmethod
    def get_ptr() -> int:
        return PartyContext._ptr

    @staticmethod
    def _update_ptr():
        PartyContext._ptr = PyParty.PyParty().GetPartyContextPtr()

    @staticmethod
    def enable():
        Game.register_callback(
            PartyContext._callback_name,
            PartyContext._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(PartyContext._callback_name)
        PartyContext._ptr = 0

    @staticmethod
    def get_context() -> PartyContextStruct | None:
        ptr = PartyContext._ptr
        if not ptr:
            return None
        return cast(
            ptr,
            POINTER(PartyContextStruct)
        ).contents

PartyContext.enable()