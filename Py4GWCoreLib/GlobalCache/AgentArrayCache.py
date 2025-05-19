from Py4GWCoreLib.AgentArray import RawAgentArray
import PyPlayer

class AgentArrayCache:
    def __init__(self, raw_agent_array: RawAgentArray):
        self._raw_agent_array = raw_agent_array  
        self._player_instance = PyPlayer.PyPlayer()
        
    def _update_cache(self):
        self._player_instance.GetContext()
        
    def GetAgentArray(self):
        return self._player_instance.GetAgentArray()
    
    def GetAllyArray(self):
        return self._player_instance.GetAllyArray()
    
    def GetNeutralArray(self):
        return self._player_instance.GetNeutralArray()
    
    def GetEnemyArray(self):
        return self._player_instance.GetEnemyArray()
    
    def GetSpiritPetArray(self):
        return self._player_instance.GetSpiritPetArray()
    
    def GetMinionArray(self):
        return self._player_instance.GetMinionArray()
    
    def GetNPCMinipetArray(self):
        return self._player_instance.GetNPCMinipetArray()
    
    def GetItemArray(self):
        return self._player_instance.GetItemArray()
    
    def GetGadgetArray(self):
        return self._player_instance.GetGadgetArray()
    
    def GetRawAgentArray(self):
        return self._raw_agent_array.get_array()
    
    def GetRawAllyArray(self):
        return self._raw_agent_array.get_ally_array()
    
    def GetRawNeutralArray(self):
        return self._raw_agent_array.get_neutral_array()
    
    def GetRawEnemyArray(self):
        return self._raw_agent_array.get_enemy_array()
    
    def GetRawSpiritPetArray(self):
        return self._raw_agent_array.get_spirit_pet_array()
    
    def GetRawMinionArray(self):
        return self._raw_agent_array.get_minion_array()
    
    def GetRawNPCMinipetArray(self):
        return self._raw_agent_array.get_npc_minipet_array()
    
    def GetRawItemArray(self):
        return self._raw_agent_array.get_item_array()
    
    def GetRawGadgetArray(self):
        return self._raw_agent_array.get_gadget_array()
    
   