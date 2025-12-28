from typing import List, Optional
from ..internals.types import CPointer
from ..internals.gw_array import GW_Array
from ..internals.types import Vec3f

class AgentSummaryInfoSub():
    h0000: int
    h0004: int
    gadget_id: int
    h000C: int
    gadget_name_enc: CPointer[str]
    h0014: int
    composite_agent_id: int

    @property
    def gadget_name_encoded_str(self) -> str | None:...
    @property
    def gadget_name_str(self) -> str | None:...
    
class AgentSummaryInfo():
    h0000: int
    h0004: int
    extra_info_sub_ptr: CPointer[AgentSummaryInfoSub]
    @property
    def extra_info_sub(self) -> Optional[AgentSummaryInfoSub]:...
    
   
class AgentMovement():
    h0000: List[int]
    agent_id: int
    h0010: List[int]
    agentDef: int
    h0020: List[int]
    moving1: int
    h003C: List[int]
    moving2: int
    h0048: List[int]
    h0064: Vec3f
    h0070: int
    h0074: Vec3f
    
class AgentContextStruct():
    h0000_array: GW_Array
    h0010: List[int]
    h0024: int
    h0028: List[int]
    h0030: int
    h0034: List[int]
    h003C: int
    h0040: List[int]
    h0048: int
    h004C: List[int]
    h0054: int
    h0058: List[int]
    h0084_array: GW_Array
    h0094: int
    agent_summary_info_array: GW_Array
    h00A8_array: GW_Array
    h00B8_array: GW_Array
    rand1: int
    rand2: int
    h00D0: List[int]
    agent_movement_array: GW_Array
    h00F8_array: GW_Array
    h0108: List[int]
    h014C_array: GW_Array
    h015C_array: GW_Array
    h016C: List[int]
    instance_timer: int

    @property
    def h0000_ptrs(self) -> list[int] | None:...
    @property
    def h0084_ptrs(self) -> list[int] | None:...
    @property
    def agent_summary_info_list(self) -> list[AgentSummaryInfo] | None:...
    @property
    def h00A8_ptrs(self) -> list[int] | None:...
    @property
    def h00B8_ptrs(self) -> list[int] | None:...
    @property
    def agent_movement_ptrs(self) -> list[AgentMovement] | None:...
    @property
    def h00F8_ptrs(self) -> list[int] | None:...
    @property
    def h014C_ptrs(self) -> list[int] | None:...
    @property
    def h015C_ptrs(self) -> list[int] | None:...
    
    
    
class AgentContext:
    @staticmethod
    def get_ptr() -> int:... 
    @staticmethod
    def _update_ptr():...
    @staticmethod
    def enable():...
    @staticmethod
    def disable():...
    @staticmethod
    def get_context() -> AgentContextStruct | None:...
        