from ctypes import Array, Structure, addressof, c_int, c_uint, c_float, c_bool, c_wchar, memmove, c_uint64, sizeof


class MapStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("MapID", c_uint),
        ("Region", c_int),
        ("District", c_uint),
        ("Language", c_int),
    ]
    
    MapID: int
    Region: int
    District: int
    Language: int

    def reset(self) -> None:
        """Reset all fields to zero."""
        self.MapID = 0
        self.Region = 0
        self.District = 0
        self.Language = 0
        
    def from_context(self) -> None:
        from ...Map import Map
        self.MapID = Map.GetMapID()
        self.Region = Map.GetRegion()[0]
        self.District = Map.GetDistrict()
        self.Language = Map.GetLanguage()[0]

