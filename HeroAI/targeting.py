from Py4GWCoreLib import GLOBAL_CACHE, Utils, AgentArray, Routines, Agent, Player, Party
from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
from .constants import (
    Range,
    BLOOD_IS_POWER,
    BLOOD_RITUAL,
    MAX_NUM_PLAYERS,
)


def _filter_blacklisted(agent_id: int) -> int:
    """Return 0 if the agent is blacklisted (by model ID or name), otherwise return agent_id unchanged."""
    if agent_id == 0:
        return 0
    bl = EnemyBlacklist()
    if bl.is_empty():
        return agent_id
    return 0 if bl.is_blacklisted(agent_id) else agent_id

def GetAllAlliesArray(distance=Range.SafeCompass.value):
    #Pets are added here
    ally_array = Routines.Targeting.GetAllAlliesArray(distance)
    return ally_array

def FilterAllyArray(array, distance, other_ally=False, filter_skill_id=0):
    #this is multibox!
    from .utils import CheckForEffect
    array = AgentArray.Filter.ByDistance(array, Player.GetXY(), distance)
    array = AgentArray.Filter.ByCondition(array, lambda agent_id: Agent.IsAlive(agent_id))
        
    if other_ally:
        array = AgentArray.Filter.ByCondition(array, lambda agent_id: Player.GetAgentID() != agent_id)
    
    if filter_skill_id != 0:
        array = AgentArray.Filter.ByCondition(array, lambda agent_id: not CheckForEffect(agent_id, filter_skill_id))
    
    return array

def SortAlliesByPartyPosition(agent_array):
    player_order = {}
    for index, player in enumerate(Party.GetPlayers() or []):
        agent_id = int(Party.Players.GetAgentIDByLoginNumber(player.login_number) or 0)
        if agent_id:
            player_order[agent_id] = index

    hero_order = {}
    hero_start = len(player_order)
    for index, hero in enumerate(Party.GetHeroes() or []):
        agent_id = int(getattr(hero, "agent_id", 0) or 0)
        if agent_id:
            hero_order[agent_id] = hero_start + index

    pet_owner_order = {}
    for owner_agent_id, order in player_order.items():
        pet_id = int(Party.Pets.GetPetID(owner_agent_id) or 0)
        if pet_id:
            pet_owner_order[pet_id] = order

    fallback_index = hero_start + len(hero_order)

    def sort_key(agent_id):
        if agent_id in player_order:
            return (0, player_order[agent_id], agent_id)
        if agent_id in hero_order:
            return (1, hero_order[agent_id], agent_id)
        if agent_id in pet_owner_order:
            return (2, pet_owner_order[agent_id], agent_id)
        return (3, fallback_index, agent_id)

    return sorted(agent_array or [], key=sort_key)

def TargetAllyByPredicate(
    predicate=None,
    other_ally=False,
    filter_skill_id=0,
    include_spirit_pets=False,
    distance=Range.Spellcast.value,
):
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)

    if include_spirit_pets:
        spirit_pet_array = AgentArray.GetSpiritPetArray()
        spirit_pet_array = FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
        spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not Agent.IsSpawned(agent_id))
        ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array)

    if predicate is not None:
        ally_array = AgentArray.Filter.ByCondition(ally_array, predicate)

    ally_array = SortAlliesByPartyPosition(ally_array)
    return Utils.GetFirstFromArray(ally_array)

def TargetLowestAlly(other_ally=False,filter_skill_id=0):
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id) 
     
    
    spirit_pet_array = AgentArray.GetSpiritPetArray()
    spirit_pet_array = FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
    spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not Agent.IsSpawned(agent_id)) #filter spirits
    ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
    
    ally_array = SortAlliesByPartyPosition(ally_array)
    return Utils.GetFirstFromArray(ally_array)
    

def TargetLowestAllyEnergy(other_ally=False, filter_skill_id=0, less_energy=1.0):
    global BLOOD_IS_POWER, BLOOD_RITUAL
    from .utils import (CheckForEffect, GetEnergyValues)
    
    
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not CheckForEffect(agent_id, BLOOD_IS_POWER))
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not CheckForEffect(agent_id, BLOOD_RITUAL))
    
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GetEnergyValues(agent_id) <= less_energy)
    ally_array = SortAlliesByPartyPosition(ally_array)
    
    ally = Utils.GetFirstFromArray(ally_array)
    return ally


def TargetLowestAllyCaster(other_ally=False, filter_skill_id=0):
    from Py4GWCoreLib import Routines
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Routines.Checks.Agents.IsCaster(agent_id))

    ally_array = SortAlliesByPartyPosition(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyMartial(other_ally=False, filter_skill_id=0):
    from Py4GWCoreLib import Routines
    from .utils import HasIllusionaryWeaponry
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Routines.Checks.Agents.IsMartial(agent_id))
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not HasIllusionaryWeaponry(agent_id))
    
    spirit_pet_array = AgentArray.GetSpiritPetArray()
    spirit_pet_array = FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
    spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not Agent.IsSpawned(agent_id)) #filter spirits
    ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
    
    ally_array = SortAlliesByPartyPosition(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyMelee(other_ally=False, filter_skill_id=0):
    from Py4GWCoreLib import Routines
    from .utils import HasIllusionaryWeaponry
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Routines.Checks.Agents.IsMelee(agent_id))
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not HasIllusionaryWeaponry(agent_id))
    
    spirit_pet_array = AgentArray.GetSpiritPetArray()
    spirit_pet_array = FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
    spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not Agent.IsSpawned(agent_id)) #filter spirits
    ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
    
    ally_array = SortAlliesByPartyPosition(ally_array)
    return Utils.GetFirstFromArray(ally_array)


def TargetLowestAllyRanged(other_ally=False, filter_skill_id=0):
    from Py4GWCoreLib import Routines
    distance = Range.Spellcast.value
    ally_array = AgentArray.GetAllyArray()
    ally_array = FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
    ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: Routines.Checks.Agents.IsRanged(agent_id))
    
    ally_array = SortAlliesByPartyPosition(ally_array)
    return Utils.GetFirstFromArray(ally_array)

   
def TargetNearestItem():
    return Routines.Targeting.TargetNearestItem()


def TargetClusteredEnemy(area=4500.0):
    return _filter_blacklisted(Routines.Targeting.TargetClusteredEnemy(area))

def GetEnemyAttacking(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyAttacking(max_distance, aggressive_only))

def GetEnemyCasting(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyCasting(max_distance, aggressive_only))

def GetEnemyCastingSpell(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyCastingSpell(max_distance, aggressive_only))

def GetEnemyInjured(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyInjured(max_distance, aggressive_only))

def GetEnemyHealthy(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyHealthy(max_distance, aggressive_only))

def GetEnemyConditioned(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyConditioned(max_distance, aggressive_only))

def GetEnemyBleeding(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyBleeding(max_distance, aggressive_only))

def GetEnemyPoisoned(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyPoisoned(max_distance, aggressive_only))
    
def GetEnemyCrippled(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyCrippled(max_distance, aggressive_only))

def GetEnemyHexed(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyHexed(max_distance, aggressive_only))

def GetEnemyDegenHexed(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyDegenHexed(max_distance, aggressive_only))

def GetEnemyEnchanted(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyEnchanted(max_distance, aggressive_only))

def GetEnemyMoving(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyMoving(max_distance, aggressive_only))

def GetEnemyKnockedDown(max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyKnockedDown(max_distance, aggressive_only))

def GetEnemyWithEffect(effect_skill_id, max_distance=4500.0, aggressive_only = False):
    return _filter_blacklisted(Routines.Targeting.GetEnemyWithEffect(effect_skill_id, max_distance, aggressive_only))
