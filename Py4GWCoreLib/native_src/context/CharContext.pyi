from typing import List, Optional
from ctypes import Structure
from ..internals.types import CPointer
from ..internals.gw_array import GW_Array


class ObserverMatchFlags():
    type: int
    reserved: int
    version: int
    state: int
    level: int
    config1: int
    config2: int
    score1: int
    score2: int
    score3: int
    stat1: int
    stat2: int
    data1: int
    data2: int
    

class ObserverMatch():
    match_id: int
    match_id_dup: int
    map_id: int
    age: int
    flags: ObserverMatchFlags
    team_name1_ptr: CPointer[str]
    unknown1: List[int]
    team_name2_ptr: CPointer[str]
    @property
    def team_name1_encoded_str(self) -> str | None:...
    
    @property
    def team_name1_str(self) -> str | None:...
    
    @property
    def team_name2_encoded_str(self) -> str | None:...
    
    @property
    def team_name2_str(self) -> str | None:...
   
    
class ProgressBar():
    pips: int
    color: List[int]
    background: List[int]
    unk: List[int]
    progress: int


class CharContextStruct():
    h0000_array: GW_Array
    h0010: int
    h0014_array: GW_Array
    h0024: List[int]
    h0034_array: GW_Array
    h0044_array: GW_Array
    h0054: List[int]
    player_uuid: List[int]
    player_name_enc: str
    h009C: List[int]
    h00EC_array: GW_Array
    h00FC: List[int]
    world_flags: int
    token1: int
    map_id: int
    is_explorable: int
    host: List[int]
    token2: int
    h01BC: List[int]
    district_number: int
    language: int
    observe_map_id: int
    current_map_id: int
    observe_map_type: int
    current_map_type: int
    h0238: List[int]
    observer_matches_array: GW_Array
    h025C: List[int]
    player_flags: int
    player_number: int
    h02A8: List[int]
    progress_bar_ptr: CPointer[ProgressBar]
    h034C: List[int]
    player_email_ptr: str

    @property
    def h0000_ptrs(self) -> list[int] | None:...
    @property
    def h0014_ptrs(self) -> list[int] | None:...
    @property
    def h0034_ptrs(self) -> list[int] | None:...
    @property
    def h0044_ptrs(self) -> list[int] | None:...
    @property
    def h00EC_ptrs(self) -> list[int] | None:...
    @property
    def observer_matches(self) -> List[ObserverMatch] | None:...
    @property
    def progress_bar(self) -> ProgressBar | None:...
    @property
    def player_name_encoded_str(self) -> str | None:...
    @property
    def player_name_str(self) -> str | None:...
    @property
    def player_email_encoded_str(self) -> str | None:...
    @property
    def player_email_str(self) -> str | None: ...
    

class CharContext:
    @staticmethod
    def get_ptr() -> int:...
    @staticmethod
    def _update_ptr():...
    @staticmethod
    def enable():...
    @staticmethod
    def disable():...
    @staticmethod
    def get_context() -> CharContextStruct | None:...
        
        