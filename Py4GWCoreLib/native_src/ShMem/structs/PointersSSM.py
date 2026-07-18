
from ctypes import Structure, c_float, c_uint32, c_void_p

class Pointers_SHMemStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("MissionMapContext", c_void_p),
        ("WorldMapContext", c_void_p),
        ("GameplayContext", c_void_p),
        ("InstanceInfo", c_void_p),
        ("MapContext", c_void_p),
        ("GameContext", c_void_p),
        ("PreGameContext", c_void_p),
        ("WorldContext", c_void_p),
        ("CharContext", c_void_p),
        ("AgentContext", c_void_p),
        ("CinematicContext", c_void_p),
        ("GuildContext", c_void_p),
        ("AvailableCharacters", c_void_p),
        ("PartyContext", c_void_p),
        ("ServerRegionContext", c_void_p),
    ]

