import PyPointers
from typing import Optional

from ctypes import Structure, POINTER,c_uint32, c_wchar, c_uint8, cast, c_void_p
from ..internals.helpers import read_wstr, encoded_wstr_to_str
from ..internals.types import Vec3f
from ..internals.gw_array import GW_Array, GW_Array_Value_View, GW_Array_View

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

#region AgentSummaryInfo
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

#region AgentMovement
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

#region AgentContextStruct
class AccAgentContextStruct(Structure):
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
    def agent_movement_ptrs(self) -> list[AgentMovement | None] | None:
        """
        Return a Python list parallel to C++ `Array<AgentMovement*> agent_movement`.

        Each element is:
        - AgentMovement instance, or
        - None if the pointer is null.
        """
        arr = self.agent_movement_array
        if not arr.m_buffer or arr.m_size == 0:
            return None

        # T is AgentMovement* in C++ → elem_type = POINTER(AgentMovement)
        view = GW_Array_Value_View(arr, POINTER(AgentMovement))
        ptr_list = view.to_list()  # list[POINTER(AgentMovement)]

        result: list[AgentMovement | None] = []
        for ptr in ptr_list:
            # Safely check the raw pointer value
            addr = c_void_p.from_buffer(ptr).value
            if not addr:
                result.append(None)
                continue
            try:
                result.append(ptr.contents)
            except ValueError:
                # Extremely defensive: if ctypes still complains, treat as None
                result.append(None)

        return result
    
    @property
    def valid_agents_ids(self) -> list[int]:
        """
        Return a list of agent_ids that have valid movement entries,
        equivalent to the C++ check:

            if (movement.size() > id && movement[id]) → valid

        NO AgentArray access. NO struct casting. NO context lookup.
        """
        arr = self.agent_movement_array
        if not arr.m_buffer or arr.m_size == 0:
            return []

        # View raw pointers directly
        movement_ptrs = GW_Array_Value_View(arr, c_void_p).to_list()

        valid_ids: list[int] = []
        for agent_id, raw_ptr in enumerate(movement_ptrs):
            if raw_ptr:                      # non-null pointer → valid
                valid_ids.append(agent_id)

        return valid_ids


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
    
#region AgentContext facade
class AccAgentContext:
    _ptr: int = 0
    _cached_ctx: AccAgentContextStruct | None = None
    _callback_name = "AccAgentContext.UpdatePtr"
    
    
    @staticmethod
    def get_ptr() -> int:
        return AccAgentContext._ptr    
    @staticmethod
    def _update_ptr():
        ptr = PyPointers.PyPointers.GetAgentContextPtr()
        AccAgentContext._ptr = ptr
        if not ptr:
            AccAgentContext._cached_ctx = None
            return
        AccAgentContext._cached_ctx = cast(
            ptr,
            POINTER(AccAgentContextStruct)
        ).contents

    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            AccAgentContext._callback_name,
            PyCallback.Phase.PreUpdate,
            AccAgentContext._update_ptr,
            priority=5,
            context=PyCallback.Context.Draw
        )


    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(AccAgentContext._callback_name)

    @staticmethod
    def get_context() -> AccAgentContextStruct | None:
        return AccAgentContext._cached_ctx
    
    
        
        
        
AccAgentContext.enable()