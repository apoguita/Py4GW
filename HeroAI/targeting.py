from Py4GWCoreLib import GLOBAL_CACHE, Utils, AgentArray, Routines
from .constants import (
    Range,
    BLOOD_IS_POWER,
    BLOOD_RITUAL,
    MAX_NUM_PLAYERS,
)

def GetAllAlliesArray(distance=Range.SafeCompass.value):
    ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
    ally_array = AgentArray.Filter.ByDistance(ally_array, GLOBAL_CACHE.Player.GetXY(), distance)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
    
    spirit_pet_array = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
    spirit_pet_array = AgentArray.Filter.ByDistance(spirit_pet_array, GLOBAL_CACHE.Player.GetXY(), distance)
    spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not GLOBAL_CACHE.Agent.IsSpawned(agent_id)) #filter spirits
    ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
    
    
    return ally_array   

def FilterAllyArray(array, distance, other_ally=False, filter_skill_id=0):
    from .utils import CheckForEffect
    array = AgentArray.Filter.ByDistance(array, GLOBAL_CACHE.Player.GetXY(), distance)
    array = AgentArray.Filter.ByCondition(array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        
    if other_ally:
        array = AgentArray.Filter.ByCondition(array, lambda agent_id: GLOBAL_CACHE.Player.GetAgentID() != agent_id)
    
    if filter_skill_id != 0:
        array = AgentArray.Filter.ByCondition(array, lambda agent_id: not CheckForEffect(agent_id, filter_skill_id))
    
    return array

def TargetLowestAlly(other_ally=False,filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id) 
     
    
    spirit_pet_array = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
    spirit_pet_array = FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
    spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not GLOBAL_CACHE.Agent.IsSpawned(agent_id)) #filter spirits
    ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
    
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
    ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not CheckForEffect(agent_id, BLOOD_IS_POWER))
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not CheckForEffect(agent_id, BLOOD_RITUAL))
    
    ally_array = AgentArray.Sort.ByCondition(ally_array, lambda agent_id: GetEnergyValues(agent_id))
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyCaster(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsCaster(agent_id))

    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyMartial(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsMartial(agent_id))
    
    spirit_pet_array = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
    spirit_pet_array = FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
    spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not GLOBAL_CACHE.Agent.IsSpawned(agent_id)) #filter spirits
    ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
    
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyMelee(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsMelee(agent_id))
    
    spirit_pet_array = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
    spirit_pet_array = FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
    spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not GLOBAL_CACHE.Agent.IsSpawned(agent_id)) #filter spirits
    ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
    
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyRanged(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsRanged(agent_id))
    
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def IsValidItem(item_id):
    if item_id == 0:
        return False
    
    item_data = GLOBAL_CACHE.Agent.GetItemAgent(item_id)
    owner_id = item_data.owner_id
    
    is_assigned = (owner_id == GLOBAL_CACHE.Player.GetAgentID()) or (owner_id == 0)
    return is_assigned
       
def TargetNearestItem():
    distance = Range.Spellcast.value
    item_array = GLOBAL_CACHE.AgentArray.GetItemArray()
    item_array = AgentArray.Filter.ByDistance(item_array, GLOBAL_CACHE.Player.GetXY(), distance)
    item_array = AgentArray.Filter.ByCondition(item_array, lambda item_id: IsValidItem(item_id))
    #IsPointValid implementation goes here
    item_array = AgentArray.Sort.ByDistance(item_array, GLOBAL_CACHE.Player.GetXY())
    return Utils.GetFirstFromArray(item_array)


def TargetClusteredEnemy(area=4500.0):
    distance = area
    enemy_array = GLOBAL_CACHE.AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, GLOBAL_CACHE.Player.GetXY(), distance)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
    
    clustered_agent = AgentArray.Routines.DetectLargestAgentCluster(enemy_array, area)
    return Utils.GetFirstFromArray(clustered_agent)

def GetEnemyAttacking(max_distance=4500.0, aggressive_only = False):
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAttacking(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
    return Utils.GetFirstFromArray(enemy_array)

def GetEnemyCasting(max_distance=4500.0, aggressive_only = False):
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsCasting(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
    return Utils.GetFirstFromArray(enemy_array)

def GetEnemyCastingSpell(max_distance=4500.0, aggressive_only = False):
    def _filter_spells(enemy_array):
        result_array = []
        for enemy_id in enemy_array:
            casting_skill_id = GLOBAL_CACHE.Agent.GetCastingSkill(enemy_id)
            if GLOBAL_CACHE.Skill.Flags.IsSpell(casting_skill_id):
                result_array.append(enemy_id)
        return result_array

                
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsCasting(agent_id))
    enemy_array = _filter_spells(enemy_array)
    
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
    return Utils.GetFirstFromArray(enemy_array)

def GetEnemyInjured(max_distance=4500.0, aggressive_only = False):
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
    enemy_array = AgentArray.Sort.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.GetHealth(agent_id))
    return Utils.GetFirstFromArray(enemy_array)

def GetEnemyConditioned(max_distance=4500.0, aggressive_only = False):
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsConditioned(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
    return Utils.GetFirstFromArray(enemy_array)

def GetEnemyHexed(max_distance=4500.0, aggressive_only = False):
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsHexed(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
    return Utils.GetFirstFromArray(enemy_array)

def GetEnemyDegenHexed(max_distance=4500.0, aggressive_only = False):
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsDegenHexed(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
    return Utils.GetFirstFromArray(enemy_array)

def GetEnemyEnchanted(max_distance=4500.0, aggressive_only = False):
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsEnchanted(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
    return Utils.GetFirstFromArray(enemy_array)

def GetEnemyMoving(max_distance=4500.0, aggressive_only = False):
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsMoving(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
    return Utils.GetFirstFromArray(enemy_array)

def GetEnemyKnockedDown(max_distance=4500.0, aggressive_only = False):
    player_pos = GLOBAL_CACHE.Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsKnockedDown(agent_id))
    enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
    return Utils.GetFirstFromArray(enemy_array)