import PyPlayer
from Py4GW import Game
import math
from typing import ClassVar, Optional
from ctypes import (
    Structure, POINTER,
    c_uint32, c_float, c_void_p, c_wchar, c_uint8,c_uint16,
    cast, sizeof
)
from ..internals.helpers import read_wstr, encoded_wstr_to_str
from ..internals.types import Vec2f, Vec3f, GamePos
from ..internals.gw_array import GW_Array, GW_Array_View, GW_Array_Value_View
from ..internals.gw_list import GW_TList, GW_TList_View, GW_TLink

class AgentSummaryInfoSub(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32),                    # +0x0000
        ("h0004", c_uint32),                    # +0x0004
        ("gadget_id", c_uint32),                # +0x0008
        ("h000C", c_uint32),                    # +0x000C
        ("gadget_name_enc", POINTER(c_wchar)),  # +0x0010 wchar_t*
        ("h0014", c_uint32),                    # +0x0014
        ("composite_agent_id", c_uint32),       # +0x0018  // 0x30000000 | player_id, 0x20000000 | npc_id etc
    ]
    @property
    def gadget_name_encoded_str(self) -> str | None:
        """Get gadget name as a string."""
        return read_wstr(self.gadget_name_enc)
    @property
    def gadget_name_str(self) -> str | None:
        """Get gadget name as a decoded string."""
        encoded = self.gadget_name_encoded_str
        if encoded:
            return encoded_wstr_to_str(encoded)
        return None

class AgentSummaryInfo(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32),                           # +0x0000
        ("h0004", c_uint32),                           # +0x0004
        ("extra_info_sub_ptr", POINTER(AgentSummaryInfoSub)),  # +0x0008 AgentSummaryInfoSub*
    ]
    @property
    def extra_info_sub(self) -> Optional[AgentSummaryInfoSub]:
        """Get pointer to AgentSummaryInfoSub struct."""
        if self.extra_info_sub_ptr:
            return self.extra_info_sub_ptr.contents
        return None

class AgentMovement(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32 * 3),    # +0x0000
        ("agent_id", c_uint32),     # +0x000C
        ("h0010", c_uint32 * 3),    # +0x0010
        ("agentDef", c_uint32),     # +0x001C  // GW_AGENTDEF_CHAR = 1
        ("h0020", c_uint32 * 6),    # +0x0020
        ("moving1", c_uint32),      # +0x0038  // tells if you are stuck even if your client doesn't know
        ("h003C", c_uint32 * 2),    # +0x003C
        ("moving2", c_uint32),      # +0x0044  // exactly same as Moving1
        ("h0048", c_uint32 * 7),    # +0x0048
        ("h0064", Vec3f),           # +0x0064
        ("h0070", c_uint32),        # +0x0070
        ("h0074", Vec3f),           # +0x0074
    ]


class AgentContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000_array", GW_Array),               # +0x0000 Array<void *>
        ("h0010", c_uint32 * 5),          # +0x0010
        ("h0024", c_uint32),               # +0x0024 function
        ("h0028", c_uint32 * 2),          # +0x0028
        ("h0030", c_uint32),               # +0x0030 function
        ("h0034", c_uint32 * 2),          # +0x0034
        ("h003C", c_uint32),               # +0x003C function
        ("h0040", c_uint32 * 2),          # +0x0040
        ("h0048", c_uint32),               # +0x0048 function
        ("h004C", c_uint32 * 2),          # +0x004C
        ("h0054", c_uint32),               # +0x0054 function
        ("h0058", c_uint32 * 11),         # +0x0058
        ("h0084_array", GW_Array),               # +0x0084 Array<void *>
        ("h0094", c_uint32),               # +0x0094 this field and the next array are link together in a structure.
        ("agent_summary_info_array", GW_Array),  # +0x0098 Array<AgentSummaryInfo> elements are of size 12. {ptr, func, ptr}
        ("h00A8_array", GW_Array),               # +0x00A8 Array<void *>
        ("h00B8_array", GW_Array),               # +0x00B8 Array<void *>
        ("rand1", c_uint32),               # +0x00C8 Number seems to be randomized quite a bit o.o seems to be accessed by textparser.cpp
        ("rand2", c_uint32),               # +0x00CC
        ("h00D0", c_uint8 * 24),          # +0x00D0
        ("agent_movement_array", GW_Array),      # +0x00E8 Array<AgentMovement *>
        ("h00F8_array", GW_Array),               # +0x00F8 Array<void *>  
        ("h0108", c_uint32 * 0x11),       # +0x0108
        ("h014C_array", GW_Array),               # +0x014C Array<void *>
        ("h015C_array", GW_Array),               # +0x015C Array<void *>
        ("h016C", c_uint32 * 0x10),       # +0x016C
        ("instance_timer", c_uint32),     # +0x01AC
    ]
    @property
    def h0000_ptrs(self) -> list[int] | None:
        """Get list of pointers from h0000_array."""
        array_view = GW_Array_Value_View(self.h0000_array, c_uint32).to_list()
        if array_view is None:
            return None
        return [int(item) for item in array_view]
    @property
    def h0084_ptrs(self) -> list[int] | None:
        """Get list of pointers from h0084_array."""
        array_view = GW_Array_Value_View(self.h0084_array, c_uint32).to_list()
        if array_view is None:
            return None
        return [int(item) for item in array_view]
    @property
    def agent_summary_info_list(self) -> list[AgentSummaryInfo] | None:
        """Get list of AgentSummaryInfo from agent_summary_info_array."""
        array_view = GW_Array_Value_View(self.agent_summary_info_array, AgentSummaryInfo).to_list()
        if array_view is None:
            return None
        return array_view
    @property
    def h00A8_ptrs(self) -> list[int] | None:
        """Get list of pointers from h00A8_array."""
        array_view = GW_Array_Value_View(self.h00A8_array, c_uint32).to_list()
        if array_view is None:
            return None
        return [int(item) for item in array_view]
    @property
    def h00B8_ptrs(self) -> list[int] | None:
        """Get list of pointers from h00B8_array."""
        array_view = GW_Array_Value_View(self.h00B8_array, c_uint32).to_list()
        if array_view is None:
            return None
        return [int(item) for item in array_view]
    @property
    def agent_movement_ptrs(self) -> list[AgentMovement] | None:
        """Get list of AgentMovement from agent_movement_array."""
        array_view = GW_Array_Value_View(self.agent_movement_array, POINTER(AgentMovement)).to_list()
        if array_view is None:
            return None
        return [item.contents for item in array_view]
    @property
    def h00F8_ptrs(self) -> list[int] | None:
        """Get list of pointers from h00F8_array."""
        array_view = GW_Array_Value_View(self.h00F8_array, c_uint32).to_list()
        if array_view is None:
            return None
        return [int(item) for item in array_view]
    @property
    def h014C_ptrs(self) -> list[int] | None:
        """Get list of pointers from h014C_array."""
        array_view = GW_Array_Value_View(self.h014C_array, c_uint32).to_list()
        if array_view is None:
            return None
        return [int(item) for item in array_view]
    @property
    def h015C_ptrs(self) -> list[int] | None:
        """Get list of pointers from h015C_array."""
        array_view = GW_Array_Value_View(self.h015C_array, c_uint32).to_list()
        if array_view is None:
            return None
        return [int(item) for item in array_view]
    
#region facade
class AgentContext:
    _ptr: int = 0
    _callback_name = "AgentContext.UpdateAgentContextPtr"

    @staticmethod
    def get_ptr() -> int:
        return AgentContext._ptr    
    @staticmethod
    def _update_ptr():
        AgentContext._ptr = PyPlayer.PyPlayer().GetAgentContextPtr()

    @staticmethod
    def enable():
        Game.register_callback(
            AgentContext._callback_name,
            AgentContext._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(AgentContext._callback_name)
        AgentContext._ptr = 0

    @staticmethod
    def get_context() -> AgentContextStruct | None:
        ptr = AgentContext._ptr
        if not ptr:
            return None
        return cast(
            ptr,
            POINTER(AgentContextStruct)
        ).contents
        
        
        
AgentContext.enable()