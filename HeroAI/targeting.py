from Py4GWCoreLib import GLOBAL_CACHE, Utils, AgentArray, Routines, Agent
from .constants import (
    Range,
    BLOOD_IS_POWER,
    BLOOD_RITUAL,
    MAX_NUM_PLAYERS,
)

def GetAllAlliesArray(distance=Range.SafeCompass.value):
    #Pets are added here
    ally_array = Routines.Targeting.GetAllAlliesArray(distance)
    return ally_array

def FilterAllyArray(array, distance, other_ally=False, filter_skill_id=0):
    #this is multibox!
    from .utils import CheckForEffect
    array = AgentArray.Filter.ByDistance(array, GLOBAL_CACHE.Player.GetXY(), distance)
    array = AgentArray.Filter.ByCondition(array, lambda agent_id: Agent.IsAlive(agent_id))
        
    if other_ally:
        array = AgentArray.Filter.ByCondition(array, lambda agent_id: GLOBAL_CACHE.Player.GetAgentID() != agent_id)
    
    if filter_skill_id != 0:
        array = AgentArray.Filter.ByCondition(array, lambda agent_id: not CheckForEffect(agent_id, filter_skill_id))
    
    return array

def TargetLowestAlly(other_ally=False,filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id) 
     
    
    spirit_pet_array = AgentArray.GetSpiritPetArray()
    spirit_pet_array = FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
    spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not Agent.IsSpawned(agent_id)) #filter spirits
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
    
    spirit_pet_array = AgentArray.GetSpiritPetArray()
    spirit_pet_array = FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
    spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not Agent.IsSpawned(agent_id)) #filter spirits
    ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
    
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyMelee(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsMelee(agent_id))
    
    spirit_pet_array = AgentArray.GetSpiritPetArray()
    spirit_pet_array = FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
    spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not Agent.IsSpawned(agent_id)) #filter spirits
    ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
    
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyRanged(other_ally=False, filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Agent.IsRanged(agent_id))
    
    ally_array = AgentArray.Sort.ByHealth(ally_array)
    return Utils.GetFirstFromArray(ally_array)

   
def TargetNearestItem():
    return Routines.Targeting.TargetNearestItem()


def TargetClusteredEnemy(area=4500.0):
    return Routines.Targeting.TargetClusteredEnemy(area)

def GetEnemyAttacking(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyAttacking(max_distance, aggressive_only)

def GetEnemyCasting(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyCasting(max_distance, aggressive_only)

def GetEnemyCastingSpell(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyCastingSpell(max_distance, aggressive_only)

def GetEnemyInjured(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyInjured(max_distance, aggressive_only)

def GetEnemyHealthy(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyHealthy(max_distance, aggressive_only)

def GetEnemyConditioned(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyConditioned(max_distance, aggressive_only)

def GetEnemyBleeding(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyBleeding(max_distance, aggressive_only)

def GetEnemyPoisoned(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyPoisoned(max_distance, aggressive_only)
    
def GetEnemyCrippled(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyCrippled(max_distance, aggressive_only)

def GetEnemyHexed(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyHexed(max_distance, aggressive_only)

def GetEnemyDegenHexed(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyDegenHexed(max_distance, aggressive_only)

def GetEnemyEnchanted(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyEnchanted(max_distance, aggressive_only)

def GetEnemyMoving(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyMoving(max_distance, aggressive_only)

def GetEnemyKnockedDown(max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyKnockedDown(max_distance, aggressive_only)

def GetEnemyWithEffect(effect_skill_id, max_distance=4500.0, aggressive_only = False):
    return Routines.Targeting.GetEnemyWithEffect(effect_skill_id, max_distance, aggressive_only)