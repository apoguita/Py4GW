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
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_moving
    
    def IsKnockedDown(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_knocked_down
    
    def IsBleeding(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_bleeding
    
    def IsCrippled(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_crippled
    
    def IsDeepWounded(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_deep_wounded
    
    def IsPoisoned(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_poisoned
    
    def IsConditioned(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_conditioned
    
    def IsEnchanted(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_enchanted
    
    def IsHexed(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_hexed
    
    def IsDegenHexed(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_degen_hexed
    
    def IsDead(self, agent_id):
        return not self.IsAlive(agent_id)
    
    def IsAlive(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_alive
    
    def IsWeaponSpelled(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_weapon_spelled
    
    def IsInCombatStance(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.in_combat_stance
    
    def IsAggressive(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        if agent.living_agent.is_attacking or agent.living_agent.is_casting:
            return True
        else:
            return False
        
    def IsAttacking(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_attacking
        
    def IsCasting(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_casting
        
    def IsIdle(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_idle
        
    def HasBossGlow(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.has_boss_glow
    
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
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_player
    
    def IsNPC(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_npc

    def HasQuest(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.has_quest
        
    def IsDeadByTypeMap(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_dead_by_typemap
    
    def IsFemale(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_female
    
    def IsHidingCape(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_hiding_cape
    
    def CanBeViewedInPartyWindow(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.can_be_viewed_in_party_window
        
    def IsSpawned(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_spawned
        
    def IsBeingObserved(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.is_being_observed

    def GetOvercast(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.living_agent.overcast
    
    def GetItemAgent(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.item_agent
    
    def GetItemAgentOwnerID(self, agent_id):
        item_owner = self.raw_agent_array.get_item_owner(agent_id)
        if item_owner is None:
            return 0
        return item_owner
    
    def GetGadgetAgent(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.gadget_agent
    
    def GetGadgetID(self, agent_id):
        agent = self.raw_agent_array.get_agent(agent_id)
        return agent.gadget_agent.agent_id
    