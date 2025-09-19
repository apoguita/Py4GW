import importlib

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()

from ..enums_src.GameData_enums import Range

#region Targetting
class Targeting:
    
    @staticmethod
    def InteractTarget():
        from ..GlobalCache import GLOBAL_CACHE
        """Interact with the target"""
        GLOBAL_CACHE.Player.Interact(GLOBAL_CACHE.Player.GetTargetID(), False)
    
    @staticmethod
    def SafeChangeTarget( target_id):
        from ..GlobalCache import GLOBAL_CACHE
        
        if GLOBAL_CACHE.Agent.IsValid(target_id):
            GLOBAL_CACHE.Player.ChangeTarget(target_id)
        
    @staticmethod
    def HasArrivedToTarget():
        from ..Py4GWcorelib import Utils
        from ..GlobalCache import GLOBAL_CACHE
        """Check if the player has arrived at the target."""
        player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        target_id = GLOBAL_CACHE.Player.GetTargetID()
        target_x, target_y = GLOBAL_CACHE.Agent.GetXY(target_id)
        return Utils.Distance((player_x, player_y), (target_x, target_y)) < 100
    
    @staticmethod
    def GetAllAlliesArray(distance=Range.SafeCompass.value):
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE

        ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
        ally_array = AgentArray.Filter.ByDistance(ally_array, GLOBAL_CACHE.Player.GetXY(), distance)
        ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        
        spirit_pet_array = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
        spirit_pet_array = AgentArray.Filter.ByDistance(spirit_pet_array, GLOBAL_CACHE.Player.GetXY(), distance)
        spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not GLOBAL_CACHE.Agent.IsSpawned(agent_id)) #filter spirits
        ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
        
        
        return ally_array   

    @staticmethod
    def FilterAllyArray(array, distance, other_ally=False, filter_skill_id=0):
        from .Checks import Checks
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE

        array = AgentArray.Filter.ByDistance(array, GLOBAL_CACHE.Player.GetXY(), distance)
        array = AgentArray.Filter.ByCondition(array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
            
        if other_ally:
            array = AgentArray.Filter.ByCondition(array, lambda agent_id: GLOBAL_CACHE.Player.GetAgentID() != agent_id)
        
        if filter_skill_id != 0:
            array = AgentArray.Filter.ByCondition(array, lambda agent_id: not Checks.Agents.HasEffect(agent_id, filter_skill_id))
        
        return array

    @staticmethod
    def TargetLowestAlly(other_ally=False,filter_skill_id=0):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE

        distance = Range.Spellcast.value
        ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
        ally_array = Targeting.FilterAllyArray(ally_array, distance, other_ally, filter_skill_id) 
        
        
        spirit_pet_array = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
        spirit_pet_array = Targeting.FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
        spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not GLOBAL_CACHE.Agent.IsSpawned(agent_id)) #filter spirits
        ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
        
        ally_array = AgentArray.Sort.ByHealth(ally_array)   
        return Utils.GetFirstFromArray(ally_array)
        
    @staticmethod
    def TargetLowestAllyEnergy(other_ally=False, filter_skill_id=0):
        from ..Py4GWcorelib import Utils
        from .Checks import Checks
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE

        BLOOD_IS_POWER = GLOBAL_CACHE.Skill.GetID("Blood_is_Power")
        BLOOD_RITUAL = GLOBAL_CACHE.Skill.GetID("Blood_Ritual")

        def GetEnergyValues(agent_id):
            energy = GLOBAL_CACHE.Agent.GetEnergy(agent_id)
            if energy is not None and energy >= 0.0 and energy <= 1.0:
                return energy
            return 1.0 #default return full energy to prevent issues
        
        distance = Range.Spellcast.value
        ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
        ally_array = Targeting.FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
        ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not Checks.Agents.HasEffect(agent_id, BLOOD_IS_POWER))
        ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: not Checks.Agents.HasEffect(agent_id, BLOOD_RITUAL))
        
        ally_array = AgentArray.Sort.ByCondition(ally_array, lambda agent_id: GetEnergyValues(agent_id))
        return Utils.GetFirstFromArray(ally_array)

    @staticmethod
    def TargetLowestAllyCaster(other_ally=False, filter_skill_id=0):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE

        distance = Range.Spellcast.value
        ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
        ally_array = Targeting.FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
        ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsCaster(agent_id))

        ally_array = AgentArray.Sort.ByHealth(ally_array)
        return Utils.GetFirstFromArray(ally_array)

    @staticmethod
    def TargetLowestAllyMartial(other_ally=False, filter_skill_id=0):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE

        distance = Range.Spellcast.value
        ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
        ally_array = Targeting.FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
        ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsMartial(agent_id))
        
        spirit_pet_array = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
        spirit_pet_array = Targeting.FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
        spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not GLOBAL_CACHE.Agent.IsSpawned(agent_id)) #filter spirits
        ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
        
        ally_array = AgentArray.Sort.ByHealth(ally_array)
        return Utils.GetFirstFromArray(ally_array)

    @staticmethod
    def TargetLowestAllyMelee(other_ally=False, filter_skill_id=0):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE

        distance = Range.Spellcast.value
        ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
        ally_array = Targeting.FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
        ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsMelee(agent_id))
        
        spirit_pet_array = GLOBAL_CACHE.AgentArray.GetSpiritPetArray()
        spirit_pet_array = Targeting.FilterAllyArray(spirit_pet_array, distance, other_ally, filter_skill_id)
        spirit_pet_array = AgentArray.Filter.ByCondition(spirit_pet_array, lambda agent_id: not GLOBAL_CACHE.Agent.IsSpawned(agent_id)) #filter spirits
        ally_array = AgentArray.Manipulation.Merge(ally_array, spirit_pet_array) #added Pets
        
        ally_array = AgentArray.Sort.ByHealth(ally_array)
        return Utils.GetFirstFromArray(ally_array)

    @staticmethod
    def TargetLowestAllyRanged(other_ally=False, filter_skill_id=0):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE

        distance = Range.Spellcast.value
        ally_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
        ally_array = Targeting.FilterAllyArray(ally_array, distance, other_ally, filter_skill_id)
        ally_array = AgentArray.Filter.ByCondition(ally_array, lambda agent_id: GLOBAL_CACHE.Agent.IsRanged(agent_id))
        
        ally_array = AgentArray.Sort.ByHealth(ally_array)
        return Utils.GetFirstFromArray(ally_array)

    @staticmethod  
    def TargetNearestItem():
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE

        def IsValidItem(item_id):
            if item_id == 0:
                return False
            
            item_data = GLOBAL_CACHE.Agent.GetItemAgent(item_id)
            owner_id = item_data.owner_id
            
            is_assigned = (owner_id == GLOBAL_CACHE.Player.GetAgentID()) or (owner_id == 0)
            return is_assigned
    
        distance = Range.Spellcast.value
        item_array = GLOBAL_CACHE.AgentArray.GetItemArray()
        item_array = AgentArray.Filter.ByDistance(item_array, GLOBAL_CACHE.Player.GetXY(), distance)
        item_array = AgentArray.Filter.ByCondition(item_array, lambda item_id: IsValidItem(item_id))
        #IsPointValid implementation goes here
        item_array = AgentArray.Sort.ByDistance(item_array, GLOBAL_CACHE.Player.GetXY())
        return Utils.GetFirstFromArray(item_array)

    @staticmethod
    def TargetClusteredEnemy(area=4500.0):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE

        distance = area
        enemy_array = GLOBAL_CACHE.AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, GLOBAL_CACHE.Player.GetXY(), distance)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
        
        clustered_agent = AgentArray.Routines.DetectLargestAgentCluster(enemy_array, area)
        return Utils.GetFirstFromArray(clustered_agent)

    @staticmethod
    def GetEnemyAttacking(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAttacking(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyCasting(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsCasting(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyCastingSpell(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        def _filter_spells(enemy_array):
            result_array = []
            for enemy_id in enemy_array:
                casting_skill_id = GLOBAL_CACHE.Agent.GetCastingSkill(enemy_id)
                if GLOBAL_CACHE.Skill.Flags.IsSpell(casting_skill_id):
                    result_array.append(enemy_id)
            return result_array

                    
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsCasting(agent_id))
        enemy_array = _filter_spells(enemy_array)
        
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyInjured(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Sort.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.GetHealth(agent_id))
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyHealthy(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Sort.ByCondition(enemy_array, lambda agent_id: -GLOBAL_CACHE.Agent.GetHealth(agent_id))
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyConditioned(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsConditioned(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyBleeding(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsBleeding(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyPoisoned(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsPoisoned(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)
     
    @staticmethod   
    def GetEnemyCrippled(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsCrippled(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyHexed(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsHexed(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyDegenHexed(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsDegenHexed(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyEnchanted(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsEnchanted(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyMoving(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsMoving(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyKnockedDown(max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: GLOBAL_CACHE.Agent.IsKnockedDown(agent_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)

    @staticmethod
    def GetEnemyWithEffect(effect_skill_id, max_distance=4500.0, aggressive_only = False):
        from ..Py4GWcorelib import Utils
        from .Checks import Checks
        from ..AgentArray import AgentArray
        from ..GlobalCache import GLOBAL_CACHE
        from .Agents import Agents
        player_pos = GLOBAL_CACHE.Player.GetXY()
        enemy_array = Agents.GetFilteredEnemyArray(player_pos[0], player_pos[1], max_distance, aggressive_only)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Checks.Effects.HasEffect(agent_id, effect_skill_id))
        enemy_array = AgentArray.Sort.ByDistance(enemy_array, player_pos)
        return Utils.GetFirstFromArray(enemy_array)
#endregion