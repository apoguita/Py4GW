from ctypes import Structure

class Pointers_SHMemStruct(Structure):	
    MissionMapContext: int
    WorldMapContext: int
    GameplayContext: int
    InstanceInfo: int
    MapContext: int
    GameContext: int
    PreGameContext: int
    WorldContext: int
    CharContext: int
    AgentContext: int
    CinematicContext: int
    GuildContext: int
    AvailableCharacters: int
    PartyContext: int
    ServerRegionContext: int