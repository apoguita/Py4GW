from Py4GWCoreLib.AgentArray import  AgentArray
from ..native_src.context.AgentContext import AgentStruct
import PyPlayer

class AgentArrayCache:
    def __init__(self):
        self._raw_agent_array = AgentArray.GetAgentArrayRaw()  
        self._player_instance = PyPlayer.PyPlayer()
        
    def _update_cache(self):
        self._player_instance.GetContext()
        
    def GetAgentArray(self) -> list[int]:
        return AgentArray.GetAgentArray()
    
    def GetAllyArray(self) -> list[int]:
        return AgentArray.GetAllyArray()
    
    def GetNeutralArray(self) -> list[int]:
        return AgentArray.GetNeutralArray()
    
    def GetEnemyArray(self) -> list[int]:
        return AgentArray.GetEnemyArray()
    
    def GetSpiritPetArray(self) -> list[int]:
        return AgentArray.GetSpiritPetArray()
    
    def GetMinionArray(self) -> list[int]:
        return AgentArray.GetMinionArray()
    
    def GetNPCMinipetArray(self) -> list[int]:
        return AgentArray.GetNPCMinipetArray()
    
    def GetItemArray(self) -> list[int]:
        return AgentArray.GetItemArray()
    
    def GetGadgetArray(self) -> list[int]:
        return AgentArray.GetGadgetArray()
    
    def GetAgentArrayRaw(self) -> list[AgentStruct]:
        return AgentArray.GetAgentArrayRaw()
    
    def GetAllyArrayRaw(self) -> list[AgentStruct]:
        return AgentArray.GetAllyArrayRaw()
    
    def GetNeutralArrayRaw(self) -> list[AgentStruct]:
        return AgentArray.GetNeutralArrayRaw()
    
    def GetEnemyArrayRaw(self) -> list[AgentStruct]:
        return AgentArray.GetEnemyArrayRaw()
    
    def GetSpiritPetArrayRaw(self) -> list[AgentStruct]:
        return AgentArray.GetSpiritPetArrayRaw()
    
    def GetMinionArrayRaw(self) -> list[AgentStruct]:
        return AgentArray.GetMinionArrayRaw()
    
    def GetNPCMinipetArrayRaw(self) -> list[AgentStruct]:
        return AgentArray.GetNPCMinipetArrayRaw()
    
    def GetItemArrayRaw(self) -> list[AgentStruct]:
        return AgentArray.GetItemArrayRaw()
    
    def GetGadgetArrayRaw(self) -> list[AgentStruct]:
        return AgentArray.GetGadgetArrayRaw()
    
   