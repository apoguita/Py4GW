from typing import List, Optional
from ctypes import Structure
from ..internals.types import CPointer
from ..internals.gw_array import GW_Array
from ..internals.gw_list import GW_TList, GW_TLink

class MapDimensionsStruct():
    unk: int
    start_x: int
    start_y: int
    end_x: int
    end_y: int
    unk1: int
    
    
class AreaInfoStruct():
    campaign: int
    continent: int
    region: int
    type: int
    flags: int
    thumbnail_id: int
    min_party_size: int
    max_party_size: int
    min_player_size: int
    max_player_size: int
    controlled_outpost_id: int
    fraction_mission: int
    min_level: int
    max_level: int
    needed_pq: int
    mission_maps_to: int
    x: int
    y: int
    icon_start_x: int
    icon_start_y: int
    icon_end_x: int
    icon_end_y: int
    icon_start_x_dupe: int
    icon_start_y_dupe: int
    icon_end_x_dupe: int
    icon_end_y_dupe: int
    file_id: int
    mission_chronology: int
    ha_map_chronology: int
    name_id: int
    description_id: int

    @property
    def file_id1(self) -> int:...
    @property
    def file_id2(self) -> int:...
    @property
    def has_enter_button(self) -> bool:...
    @property
    def is_on_world_map(self) -> bool:...
    @property
    def is_pvp(self) -> bool:... # 0x40000 = Explorable, 0x1 = Outpost
    @property
    def is_guild_hall(self) -> bool:...
    @property
    def is_vanquishable_area(self) -> bool:...
    @property
    def is_unlockable(self) -> bool:...
    @property
    def has_mission_maps_to(self) -> bool:...

class InstanceInfoStruct():
    terrain_info1_ptr: CPointer[MapDimensionsStruct]
    instance_type: int  # GW::Constants::InstanceType
    current_map_info_ptr: CPointer[AreaInfoStruct]
    terrain_count: int
    terrain_info2_ptr: CPointer[MapDimensionsStruct]

    @property
    def terrain_info1(self) -> Optional[MapDimensionsStruct]:...
    @property
    def current_map_info(self) -> Optional[AreaInfoStruct]:...
    @property
    def terrain_info2(self) -> Optional[MapDimensionsStruct]:...



class InstanceInfo:
    @staticmethod
    def get_ptr() -> int:...
    @staticmethod
    def _update_ptr():...
    @staticmethod
    def enable():...
    @staticmethod
    def disable():...

    @staticmethod
    def get_context() -> InstanceInfoStruct | None:...