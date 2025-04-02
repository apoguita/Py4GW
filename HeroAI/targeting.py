from Py4GWCoreLib import *
from .constants import (
    Range,
    BLOOD_IS_POWER,
    BLOOD_RITUAL,
    MAX_NUM_PLAYERS,
)


def FilterAllyArray(array, distance, other_ally=False, filter_skill_id=0):
    from .utils import CheckForEffect
    array = AgentArray.Filter.ByDistance(array, Player.GetXY(), distance)
    array = AgentArray.Filter.ByCondition(array, lambda agent_id: Agent.IsAlive(agent_id))
        
    if other_ally:
        array = AgentArray.Filter.ByCondition(array, lambda agent_id: Player.GetAgentID() != agent_id)
    
    if filter_skill_id != 0:
        array = AgentArray.Filter.ByCondition(array, lambda agent_id: not CheckForEffect(agent_id, filter_skill_id))
    
    return array

def TargetLowestAlly(other_ally=False,filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id) 
    ally_array = AgentArray.Sort.ByHealth(ally_array)     
    return Utils.GetFirstFromArray(ally_array)
    

def TargetLowestAllyEnergy(other_ally=False, filter_skill_id=0):
    global BLOOD_IS_POWER, BLOOD_RITUAL
    from .utils import (CheckForEffect)
    def GetEnergyValues(agent_id):
        import HeroAI.shared_memory_manager as shared_memory_manager
        shared_memory_handler = shared_memory_manager.SharedMemoryManager()

        for i in range(MAX_NUM_PLAYERS):
            player_data = shared_memory_handler.get_player(i)
            if player_data and player_data["IsActive"] and player_data["PlayerID"] == agent_id:
                return player_data["Energy"]
        return 1.0 #default return full energy to prevent issues
    
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not CheckForEffect(agent_id, BLOOD_IS_POWER))
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not CheckForEffect(agent_id, BLOOD_RITUAL))
    ally_array = AgentArray.Sort.ByCondition(ally_array, lambda agent_id: GetEnergyValues(agent_id))
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyCaster(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsCaster(agent_id))
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyMartial(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsMartial(agent_id))
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyMelee(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsMelee(agent_id))
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyRanged(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsRanged(agent_id))
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def IsValidItem(item_id):
    if item_id == 0:
        return False
    
    item_data = Agent.GetItemAgent(item_id)
    owner_id = item_data.owner_id
    
    is_assigned = (owner_id == Player.GetAgentID()) or (owner_id == 0)
    return is_assigned
       
def TargetNearestItem():
    distance = Range.Spellcast.value
    item_array = AgentArray.GetItemArray()
    item_array = AgentArray.Filter.ByDistance(item_array, Player.GetXY(), distance)
    item_array = AgentArray.Filter.ByCondition(item_array, lambda item_id: IsValidItem(item_id))
    #IsPointValid implementation goes here
    item_array = AgentArray.Sort.ByDistance(item_array, Player.GetXY())
    return Utils.GetFirstFromArray(item_array)

