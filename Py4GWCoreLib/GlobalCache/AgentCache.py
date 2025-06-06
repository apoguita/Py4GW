import PyAgent
from Py4GWCoreLib.AgentArray import RawAgentArray
import time

class AgentCache:
    def __init__(self, raw_agent_array):
        self.raw_agent_array:RawAgentArray = raw_agent_array
        self.name_cache: dict[int, tuple[str, float]] = {}  # agent_id -> (name, timestamp)
        self.name_requested: set[int] = set()
        self.name_timeout_ms = 1_000

        
    def _update_cache(self):
        """Should be called every frame to resolve names when ready."""
        now = time.time() * 1000
        for agent_id in list(self.name_requested):
            agent = self.raw_agent_array.get_agent(agent_id)
            if agent.living_agent.IsAgentNameReady():
                name = agent.living_agent.GetName()
                if name in ("Unknown", "Timeout"):
                    name = ""
                self.name_cache[agent_id] = (name, now)
                self.name_requested.discard(agent_id)
                
    def _reset_cache(self):
        """Resets the name cache and requested set."""
        self.name_cache.clear()
        self.name_requested.clear()

    def IsValid(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.IsValid(agent_id)
    
    def GetIdFromAgent(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.id
    
    def GetAgent(self, agent_id):
        return self.raw_agent_array.get_agent(agent_id)
    
    def GetAgentByID(self, agent_id):
        return self.raw_agent_array.get_agent(agent_id)
    
    def GetAgentEffects(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.effects
    
    def GetTypeMap(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.type_map
    
    def GetModelState(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.model_state
    
    def GetAgentIDByName(self, agent_name:str):
        agent_array = self.raw_agent_array.get_array()
        for agent in agent_array:
            if self.GetName(agent.id).lower() in agent_name.lower():
                return agent.id   
        return 0
    
    def GetAttributes(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.attributes

    def GetModelID(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.player_number
    
    def IsLiving(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.is_living
    
    def IsItem(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.is_item
    
    def IsGadget(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.is_gadget
    
    def GetPlayerNumber(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.player_number
    
    def GetLoginNumber(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.login_number

    def IsSpirit(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.allegiance.GetName() == "Spirit/Pet"

    def IsMinion(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.allegiance.GetName() == "Minion"
    
    def GetOwnerID(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.owner_id

    def GetXY(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.x, agent.y
    
    def GetXYZ(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.x, agent.y, agent.z
    
    def GetZPlane(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.zplane
    
    def GetRotationAngle(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.rotation_angle
    
    def GetRotationCos(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.rotation_cos
    
    def GetRotationSin(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.rotation_sin
    
    def GetVelocityXY(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.velocity_x, agent.velocity_y
    
    def RequestName(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        agent.living_agent.RequestName()
        
    def IsNameReady(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.IsAgentNameReady()
    
    def GetName(self, agent_id: int) -> str:
        now = time.time() * 1000  # current time in ms
        agent = self.raw_agent_array.get_agent(agent_id)
        # Cached and still valid
        if agent_id in self.name_cache:
            name, timestamp = self.name_cache[agent_id]
            if now - timestamp < self.name_timeout_ms:
                return name
            else:
                # Expired; refresh
                if agent_id not in self.name_requested:    
                    agent.living_agent.RequestName()
                    self.name_requested.add(agent_id)
                return name  # Still return old while waiting

        # Already requested but not ready
        if agent_id in self.name_requested:
            return ""

        # Request name for the first time
        agent.living_agent.RequestName()
        self.name_requested.add(agent_id)
        return ""
    
    def GetProfessions(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.profession, agent.living_agent.secondary_profession
    
    def GetProfessionNames(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.profession.GetName(), agent.living_agent.secondary_profession.GetName()
    
    def GetProfessionShortNames(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.profession.GetShortName(), agent.living_agent.secondary_profession.GetShortName()
    
    def GetProfessionIDs(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.profession.ToInt(), agent.living_agent.secondary_profession.ToInt()
    
    def GetLevel(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.level
    
    def GetEnergy(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.energy
    
    def GetMaxEnergy(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.max_energy
    
    def GetEnergyRegen(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.energy_regen
    
    def GetEnergyPips(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        pips = 3.0 / 0.99 * agent.living_agent.energy_regen * agent.living_agent.max_energy
        return int(pips) if pips > 0 else 0
    
    def GetHealth(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.hp
    
    def GetMaxHealth(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.max_hp
    
    def GetHealthRegen(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.hp_regen
    
    def IsMoving(self, agent_id):
        model_state = self.GetModelState(agent_id)
        return (model_state == 12) or (model_state == 76) or (model_state == 204)
    
    def IsKnockedDown(self, agent_id):
        model_state = self.GetModelState(agent_id)
        return model_state == 1104
    
    def IsBleeding(self, agent_id):
        effects = self.GetAgentEffects(agent_id)
        return (effects & 0x0001) != 0
    
    def IsCrippled(self, agent_id):
        effects = self.GetAgentEffects(agent_id)
        return (effects & 0x000A) == 0xA
    
    def IsDeepWounded(self, agent_id):
        effects = self.GetAgentEffects(agent_id)
        return (effects & 0x0020) != 0
    
    def IsPoisoned(self, agent_id):
        effects = self.GetAgentEffects(agent_id)
        return (effects & 0x0040) != 0
    
    def IsConditioned(self, agent_id):
        effects = self.GetAgentEffects(agent_id)
        return (effects & 0x0002) != 0
    
    def IsEnchanted(self, agent_id):
        effects = self.GetAgentEffects(agent_id)
        return (effects & 0x0080) != 0
    
    def IsHexed(self, agent_id):
        effects = self.GetAgentEffects(agent_id)
        return (effects & 0x0800) != 0
    
    def IsDegenHexed(self, agent_id):
        effects = self.GetAgentEffects(agent_id)
        return (effects & 0x0400) != 0
    
    def IsDead(self, agent_id):
        effects = self.GetAgentEffects(agent_id)
        return ((effects & 0x0010) != 0) or self.IsDeadByTypeMap(agent_id)
    
    def IsAlive(self, agent_id):
        health = self.GetHealth(agent_id)
        return not self.IsDead(agent_id) and health > 0.0
    
    def IsWeaponSpelled(self, agent_id):
        effects = self.GetAgentEffects(agent_id)
        return (effects & 0x8000) != 0
    
    def IsInCombatStance(self, agent_id):
        type_map = self.GetTypeMap(agent_id)
        return (type_map & 0x000001) != 0
    
    def IsAggressive(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        if agent.living_agent.is_attacking or agent.living_agent.is_casting:
            return True
        else:
            return False
        
    def IsAttacking(self, agent_id):
        model_state = self.GetModelState(agent_id)
        return (model_state == 96) or (model_state == 1088) or (model_state == 1120)
        
    def IsCasting(self, agent_id) -> bool:
        model_state = self.GetModelState(agent_id)
        return (model_state == 65) or (model_state == 581)
        
    def IsIdle(self, agent_id):
        model_state = self.GetModelState(agent_id)
        return (model_state == 68) or (model_state == 64) or (model_state == 100)
        
    def HasBossGlow(self, agent_id):
        type_map = self.GetTypeMap(agent_id)
        return (type_map & 0x000400) != 0
    
    def GetWeaponType(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.weapon_type.ToInt(), agent.living_agent.weapon_type.GetName()
        
    def GetWeaponExtraData(self,agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.weapon_item_id, agent.living_agent.weapon_item_type,  agent.living_agent.offhand_item_id, agent.living_agent.offhand_item_type
  
    def IsMartial(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        martial_weapon_types = ["Bow", "Axe", "Hammer", "Daggers", "Scythe", "Spear", "Sword"]
        return agent.living_agent.weapon_type.GetName() in martial_weapon_types

    def IsCaster(self, agent_id):
        return not self.IsMartial(agent_id)  
    
    def IsMelee(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        melee_weapon_types = ["Axe", "Hammer", "Daggers", "Scythe", "Sword"]
        return agent.living_agent.weapon_type.GetName() in melee_weapon_types
  
    def IsRanged(self, agent_id):
        return not self.IsMelee(agent_id)
    
    def GetCastingSkill(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.casting_skill_id
    
    def GetDaggerStatus(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.dagger_status
    
    def GetAllegiance(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return  agent.living_agent.allegiance.ToInt(), agent.living_agent.allegiance.GetName()
    
    def IsPlayer(self, agent_id):
        login_number = self.GetLoginNumber(agent_id)
        return login_number  != 0
    
    def IsNPC(self, agent_id):
        login_number = self.GetLoginNumber(agent_id)
        return login_number  == 0

    def HasQuest(self, agent_id):
        type_map = self.GetTypeMap(agent_id)
        return (type_map & 0x000002) != 0
        
    def IsDeadByTypeMap(self, agent_id):
        type_map = self.GetTypeMap(agent_id)
        return (type_map & 0x000008) != 0
    
    def IsFemale(self, agent_id):
        type_map = self.GetTypeMap(agent_id)
        return (type_map & 0x000200) != 0
    
    def IsHidingCape(self, agent_id):
        type_map = self.GetTypeMap(agent_id)
        return (type_map & 0x001000) != 0
    
    def CanBeViewedInPartyWindow(self, agent_id):
        type_map = self.GetTypeMap(agent_id)
        return (type_map & 0x20000) != 0
        
    def IsSpawned(self, agent_id):
        type_map = self.GetTypeMap(agent_id)
        return (type_map & 0x040000) != 0
        
    def IsBeingObserved(self, agent_id):
        type_map = self.GetTypeMap(agent_id)
        return (type_map & 0x400000) != 0

    def GetOvercast(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.overcast
    
    def GetItemAgent(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.item_agent
    
    def GetItemAgentOwnerID(self, agent_id):
        from Py4GWCoreLib.Agent import Agent
        agent = Agent.agent_instance(agent_id)
        if agent is None:
            return 999
        item_owner = agent.item_agent.owner_id
        if item_owner is None or item_owner <0:
            return 999
        return item_owner
        
    
    def GetGadgetAgent(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.gadget_agent
    
    def GetGadgetID(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.gadget_agent.gadget_id
    