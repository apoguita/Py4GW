from typing import List, Optional
from ctypes import Structure
from ..internals.types import CPointer
from ..internals.gw_array import GW_Array
from ..internals.gw_list import GW_TList, GW_TLink

class ServerRegionStruct():
    region_id: int


class ServerRegion:
    @staticmethod
    def get_ptr() -> int:...   
    @staticmethod
    def _update_ptr():...
    @staticmethod
    def enable():...
    @staticmethod
    def disable():...
    @staticmethod
    def get_context() -> ServerRegionStruct | None:...
        