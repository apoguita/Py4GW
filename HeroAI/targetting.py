from Py4GWCoreLib import *
from .constants import (
    Range,
    BLOOD_IS_POWER,
    BLOOD_RITUAL,
)



def FilterEnemyArray(array, distance):
    array = AgentArray.Filter.ByCondition(array, lambda agent_id: Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)) <= distance)
    array = AgentArray.Filter.ByCondition(array, lambda agent_id: Agent.IsAlive(agent_id))
    array = AgentArray.Filter.ByCondition(array, lambda agent_id: Player.GetAgentID() != agent_id)
    return array

def FilterAllyArray(array, distance, other_ally=False, filter_skill_id=0):
    from .utils import CheckForEffect
    array = AgentArray.Filter.ByDistance(array, Player.GetXY(), distance)
    array = AgentArray.Filter.ByCondition(array, lambda agent_id: Agent.IsAlive(agent_id))
    
    if other_ally:
        array = AgentArray.Filter.ByCondition(array, lambda agent_id: Player.GetAgentID() != agent_id)
    
    if filter_skill_id != 0:
        array = AgentArray.Filter.ByCondition(array, lambda agent_id: not CheckForEffect(agent_id, filter_skill_id))
    
    return array


def GetFirstFromArray(array):
    if array is None:
        return 0
    
    if len(array) > 0:
        return array[0]
    return 0
    

def TargetNearestEnemy(distance=Range.Earshot.value):
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = FilterEnemyArray(enemy_array, distance)
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, Player.GetXY())
    return GetFirstFromArray(enemy_array)


def TargetNearestEnemyCaster(distance=Range.Earshot.value):
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = FilterEnemyArray(enemy_array, distance)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsCaster(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, Player.GetXY())
    return GetFirstFromArray(enemy_array)


def TargetNearestEnemyMartial(distance=Range.Earshot.value):
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = FilterEnemyArray(enemy_array, distance)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsMartial(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, Player.GetXY())
    return GetFirstFromArray(enemy_array)


def TargetNearestEnemyMelee(distance=Range.Earshot.value):
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = FilterEnemyArray(enemy_array, distance)
    enemy_array = AgentArray.Filter.ByCondition(
        enemy_array, lambda agent_id: Agent.IsMelee(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, Player.GetXY())
    return GetFirstFromArray(enemy_array)


def TargetNearestEnemyRanged(distance=Range.Earshot.value):
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = FilterEnemyArray(enemy_array, distance)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsRanged(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, Player.GetXY())
    return GetFirstFromArray(enemy_array)


def TargetLowestAlly(other_ally=False,filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id) 
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return GetFirstFromArray(ally_array)
    

def TargetLowestAllyEnergy(other_ally=False, filter_skill_id=0):
    from .utils import (GetEnergyValues, CheckForEffect)
    global BLOOD_IS_POWER, BLOOD_RITUAL

    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not CheckForEffect(agent_id, BLOOD_IS_POWER))
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not CheckForEffect(agent_id, BLOOD_RITUAL))
    ally_array = AgentArray.Sort.ByCondition(ally_array, lambda agent_id: GetEnergyValues(agent_id))
    return GetFirstFromArray(ally_array)


def TargetLowestAllyCaster(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsCaster(agent_id))
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return GetFirstFromArray(ally_array)


def TargetLowestAllyMartial(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsMartial(agent_id))
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return GetFirstFromArray(ally_array)


def TargetLowestAllyMelee(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsMelee(agent_id))
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return GetFirstFromArray(ally_array)


def TargetLowestAllyRanged(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsRanged(agent_id))
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return GetFirstFromArray(ally_array)


def TargetDeadAllyInAggro():
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = AgentArray.Filter.ByDistance(ally_array, Player.GetXY(), distance)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsDead(agent_id))
    ally_array = AgentArray.Sort.ByDistance(ally_array, Player.GetXY())
    return GetFirstFromArray(ally_array)


def AllowedAlliegance(agent_id):
    _, alliegance = Agent.GetAlliegance(agent_id)

    if (alliegance == "Ally" or
        alliegance == "Neutral" or 
        alliegance == "Enemy" or 
        alliegance == "NPC/Minipet"
        ):
        return True
    return False

def TargetNearestCorpse():
    distance = Range.Spellcast.value
    corpse_array = AgentArray.GetAgentArray()
    corpse_array = AgentArray.Filter.ByDistance(corpse_array, Player.GetXY(), distance)
    corpse_array = AgentArray.Filter.ByCondition(corpse_array, lambda agent_id: Agent.IsDead(agent_id))
    corpse_array = AgentArray.Filter.ByCondition(corpse_array, lambda agent_id: AllowedAlliegance(agent_id))
    corpse_array = AgentArray.Sort.ByDistance(corpse_array, Player.GetXY())
    return GetFirstFromArray(corpse_array)


def IsValidItem(item_id):
    return (Agent.agent_instance(item_id).item_agent.owner_id == Player.GetAgentID()) or (Agent.agent_instance(item_id).item_agent.owner_id == 0)

def TargetNearestItem():
    distance = Range.Spellcast.value
    item_array = AgentArray.GetItemArray()
    item_array = AgentArray.Filter.ByDistance(item_array, Player.GetXY(), distance)
    item_array = AgentArray.Filter.ByCondition(item_array, lambda item_id: IsValidItem(item_id))
    #IsPointValid implementation goes here
    item_array = AgentArray.Sort.ByDistance(item_array, Player.GetXY())
    return GetFirstFromArray(item_array)

def TargetNearestNpc():
    distance = Range.Earshot.value
    npc_array = AgentArray.GetNPCMinipetArray()
    npc_array = AgentArray.Filter.ByDistance(npc_array, Player.GetXY(), distance)
    npc_array = AgentArray.Filter.ByCondition(npc_array, lambda agent_id: Agent.IsAlive(agent_id))
    npc_array = AgentArray.Sort.ByDistance(npc_array, Player.GetXY())
    return GetFirstFromArray(npc_array)

def TargetNearestSpirit():
    distance = Range.Earshot.value
    spirit_array = AgentArray.GetSpiritPetArray()
    spirit_array = AgentArray.Filter.ByDistance(spirit_array, Player.GetXY(), distance)
    spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: Agent.IsAlive(agent_id))
    spirit_array = AgentArray.Sort.ByDistance(spirit_array, Player.GetXY())
    return GetFirstFromArray(spirit_array)


def TargetLowestMinion():
    distance = Range.Spellcast.value
    minion_array = AgentArray.GetMinionArray()
    minion_array = AgentArray.Filter.ByDistance(minion_array, Player.GetXY(), distance)
    minion_array = AgentArray.Filter.ByCondition(minion_array, lambda agent_id: Agent.IsAlive(agent_id))
    minion_array = AgentArray.Sort.ByHealth(minion_array)
    return GetFirstFromArray(minion_array)


def TargetPet(agent_id):
    return Party.Pets.GetPetInfo(agent_id).agent_id
