from typing import Optional, TypeVar, Type, Generic, Any

# native context structs + facades
from .native_src.context.AccAgentContext import AccAgentContext, AccAgentContextStruct
from .native_src.context.AgentContext import AgentArray, AgentArrayStruct
from .native_src.context.AvailableCharacterContext import AvailableCharacterArray, AvailableCharacterArrayStruct
from .native_src.context.CharContext import CharContext, CharContextStruct
from .native_src.context.CinematicContext import Cinematic, CinematicStruct
from .native_src.context.GameplayContext import GameplayContext, GameplayContextStruct
from .native_src.context.GuildContext import GuildContext, GuildContextStruct
from .native_src.context.InstanceInfoContext import InstanceInfo, InstanceInfoStruct, AreaInfoStruct
from .native_src.context.MapContext import MapContext, MapContextStruct
from .native_src.context.MissionMapContext import MissionMapContext, MissionMapContextStruct
from .native_src.context.PartyContext import PartyContext, PartyContextStruct
from .native_src.context.PreGameContext import PreGameContext, PreGameContextStruct
from .native_src.context.ServerRegionContext import ServerRegion, ServerRegionStruct
from .native_src.context.WorldContext import WorldContext, WorldContextStruct
from .native_src.context.WorldMapContext import WorldMapContext, WorldMapContextStruct



# the struct type
TStruct = TypeVar("TStruct")

class _GWContextBase(Generic[TStruct]):
    """
    Base class for context facades.
    Subclasses must set:
      _struct_type: the ctypes.Structure
      _facade:      facade class w/ get_ptr() and get_context()
    """
    _struct_type: Type[TStruct]
    _facade: Any   # facade like InstanceInfo, MapContext, CharContext...

    @classmethod
    def GetPtr(cls) -> int:
        return cls._facade.get_ptr()

    @classmethod
    def GetContext(cls) -> Optional[TStruct]:
        return cls._facade.get_context()

    @classmethod
    def IsValid(cls) -> bool:
        return cls.GetContext() is not None



class GWContext:
    class AccAgent(_GWContextBase[AccAgentContextStruct]):
        _struct_type = AccAgentContextStruct
        _facade = AccAgentContext
        
    class AgentArray(_GWContextBase[AgentArrayStruct]):
        _struct_type = AgentArrayStruct
        _facade = AgentArray
        
    class AvailableCharacterArray(_GWContextBase[AvailableCharacterArrayStruct]):
        _struct_type = AvailableCharacterArrayStruct
        _facade = AvailableCharacterArray
        
    class Char(_GWContextBase[CharContextStruct]):
        _struct_type = CharContextStruct
        _facade = CharContext
        
    class Cinematic(_GWContextBase[CinematicStruct]):
        _struct_type = CinematicStruct
        _facade = Cinematic

    class Gameplay(_GWContextBase[GameplayContextStruct]):
        _struct_type = GameplayContextStruct
        _facade = GameplayContext
        
    class Guild(_GWContextBase[GuildContextStruct]):
        _struct_type = GuildContextStruct
        _facade = GuildContext

    class InstanceInfo(_GWContextBase[InstanceInfoStruct]):
        _struct_type = InstanceInfoStruct
        _facade = InstanceInfo
        
        def GetMapInfo(self) -> Optional[AreaInfoStruct]:
            instance_info = self.GetContext()
            if not instance_info:
                return None
            return instance_info.current_map_info

    class Map(_GWContextBase[MapContextStruct]):
        _struct_type = MapContextStruct
        _facade = MapContext

    class MissionMap(_GWContextBase[MissionMapContextStruct]):
        _struct_type = MissionMapContextStruct
        _facade = MissionMapContext

    class Party(_GWContextBase[PartyContextStruct]):
        _struct_type = PartyContextStruct
        _facade = PartyContext

    class PreGame(_GWContextBase[PreGameContextStruct]):
        _struct_type = PreGameContextStruct
        _facade = PreGameContext
        
    class ServerRegion(_GWContextBase[ServerRegionStruct]):
        _struct_type = ServerRegionStruct
        _facade = ServerRegion

    class World(_GWContextBase[WorldContextStruct]):
        _struct_type = WorldContextStruct
        _facade = WorldContext

    class WorldMap(_GWContextBase[WorldMapContextStruct]):
        _struct_type = WorldMapContextStruct
        _facade = WorldMapContext