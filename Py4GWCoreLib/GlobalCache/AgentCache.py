import PyAgent
from Py4GWCoreLib.native_src.context.AgentContext import AgentStruct, AgentLivingStruct, AgentItemStruct, AgentGadgetStruct
from Py4GWCoreLib.AgentArray import RawAgentArray, AgentArray
from Py4GWCoreLib.Agent import Agent
import time

from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

class AgentCache:
    def __init__(self, raw_agent_array):
        #self.raw_agent_array:RawAgentArray = raw_agent_array
        self.name_cache: dict[int, tuple[str, float]] = {}  # agent_id -> (name, timestamp)
        self.name_requested: set[int] = set()
        self.name_timeout_ms = 1_000

        
    def _update_cache(self):
        """Should be called every frame to resolve names when ready."""
        now = time.time() * 1000
        for agent_id in list(self.name_requested):
            #agent = self.raw_agent_array.get_agent(agent_id)
            #if agent.living_agent.IsAgentNameReady():
            
            name = Agent.GetNameByID(agent_id)
            #name = agent.living_agent.GetName()
            if name in ("Unknown", "Timeout"):
                name = ""
            self.name_cache[agent_id] = (name, now)
            self.name_requested.discard(agent_id)
                
    def _reset_cache(self):
        """Resets the name cache and requested set."""
        self.name_cache.clear()
        self.name_requested.clear()

    def IsValid(self, agent_id):
        return Agent.IsValid(agent_id)
    
    def GetIDFromAgent(self, agent_id):
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0
        return agent.agent_id
    
    def GetAgent(self, agent_id) -> AgentStruct | None:
        return Agent.GetAgentByID(agent_id)
    
    def GetAgentByID(self, agent_id) -> AgentStruct | None:
        return Agent.GetAgentByID(agent_id)
    
    def GetLivingAgentByID(self, agent_id) -> AgentLivingStruct | None:
        return Agent.GetLivingAgentByID(agent_id)
    
    def GetItemAgentByID(self, agent_id) -> AgentItemStruct | None:
        return Agent.GetItemAgentByID(agent_id)
    
    def GetGadgetAgentByID(self, agent_id) -> AgentGadgetStruct | None:
        return Agent.GetGadgetAgentByID(agent_id)

    def GetAgentEffects(self, agent_id):
        return Agent.GetAgentEffects(agent_id)
    
    def GetTypeMap(self, agent_id):
        return Agent.GetTypeMap(agent_id)
    
    def GetModelState(self, agent_id):
        return Agent.GetModelState(agent_id)
    
    def GetAgentIDByName(self, agent_name:str):
        agent_array = AgentArray.GetAgentArray()
        for agent_id in agent_array:
            if self.GetName(agent_id).lower() in agent_name.lower():
                return agent_id 
        return 0
    
    def GetAttributes(self, agent_id):
        return Agent.GetAttributes(agent_id)

    def GetAttributesDict(self, agent_id):    
        # Get attributes
        attributes_raw:list[PyAgent.AttributeClass] = self.GetAttributes(agent_id)
        attributes = {}

        # Convert attributes to dictionary format
        for attr in attributes_raw:
            attr_id = int(attr.attribute_id)  # Convert enum to integer
            attr_level = attr.level_base  # Get attribute level
            if attr_level > 0:  # Only include attributes with points
                attributes[attr_id] = attr_level
                
        return attributes

    def GetModelID(self, agent_id):
        return Agent.GetModelID(agent_id)
    
    def IsLiving(self, agent_id):
        return Agent.IsLiving(agent_id)
    
    def IsItem(self, agent_id):
        return Agent.IsItem(agent_id)
    
    def IsGadget(self, agent_id):
        return Agent.IsGadget(agent_id)
    
    def GetPlayerNumber(self, agent_id):
        return Agent.GetPlayerNumber(agent_id)
    
    def GetLoginNumber(self, agent_id):
        return Agent.GetLoginNumber(agent_id)
    
    def IsSpirit(self, agent_id):
        return Agent.IsSpirit(agent_id)

    def IsMinion(self, agent_id):
        return Agent.IsMinion(agent_id)
    
    def GetOwnerID(self, agent_id):
        return Agent.GetOwnerID(agent_id)
    
    def GetXY(self, agent_id):
        return Agent.GetXY(agent_id)
    
    def GetXYZ(self, agent_id):
        return Agent.GetXYZ(agent_id)
    
    def GetZPlane(self, agent_id):
        return Agent.GetZPlane(agent_id)
    
    def GetRotationAngle(self, agent_id):
        return Agent.GetRotationAngle(agent_id)
    
    def GetRotationCos(self, agent_id):
        return Agent.GetRotationCos(agent_id)
    
    def GetRotationSin(self, agent_id):
        return Agent.GetRotationSin(agent_id)
    
    def GetVelocityXY(self, agent_id):
        return Agent.GetVelocityXY(agent_id)
    
    def RequestName(self, agent_id):
        Agent.GetNameByID(agent_id)

    def IsNameReady(self, agent_id):
        return Agent.GetNameByID(agent_id) != ""

    def GetName(self, agent_id: int) -> str:
        now = time.time() * 1000  # current time in ms
        # Cached and still valid
        if agent_id in self.name_cache:
            name, timestamp = self.name_cache[agent_id]
            if now - timestamp < self.name_timeout_ms:
                return name
            else:
                # Expired; refresh
                if agent_id not in self.name_requested:    
                    Agent.GetNameByID(agent_id)
                    self.name_requested.add(agent_id)
                return name  # Still return old while waiting

        # Already requested but not ready
        if agent_id in self.name_requested:
            return ""

        Agent.GetNameByID(agent_id)
        self.name_requested.add(agent_id)
        return ""
    
    def GetProfessions(self, agent_id):
        return Agent.GetProfessions(agent_id)
    
    def GetProfessionNames(self, agent_id):
        return Agent.GetProfessionNames(agent_id)
    
    def GetProfessionShortNames(self, agent_id):
        return Agent.GetProfessionShortNames(agent_id)
    
    def GetProfessionIDs(self, agent_id):
        return Agent.GetProfessionIDs(agent_id)
    
    def GetProfessionsTexturePaths(self,agent_id):
        return Agent.GetProfessionsTexturePaths(agent_id)

    def GetLevel(self, agent_id):
        return Agent.GetLevel(agent_id)
    
    def GetEnergy(self, agent_id):
        return Agent.GetEnergy(agent_id)
    
    def GetMaxEnergy(self, agent_id):
        return Agent.GetMaxEnergy(agent_id)
    
    def GetEnergyRegen(self, agent_id):
        return Agent.GetEnergyRegen(agent_id)
    
    def GetEnergyPips(self, agent_id):
        return Agent.GetEnergyPips(agent_id)
    
    def GetHealth(self, agent_id):
        return Agent.GetHealth(agent_id)
    
    def GetMaxHealth(self, agent_id):
        return Agent.GetMaxHealth(agent_id)
    
    def GetHealthRegen(self, agent_id):
        return Agent.GetHealthRegen(agent_id)
    
    def GetHealthPips(self, agent_id):
        return Agent.GetHealthPips(agent_id)
    
    def IsMoving(self, agent_id):
        return Agent.IsMoving(agent_id)
        
    def IsKnockedDown(self, agent_id):
        return Agent.IsKnockedDown(agent_id)
    
    def IsBleeding(self, agent_id):
        return Agent.IsBleeding(agent_id)
    
    def IsCrippled(self, agent_id):
        return Agent.IsCrippled(agent_id)
    
    def IsDeepWounded(self, agent_id):
        return Agent.IsDeepWounded(agent_id)
    
    def IsPoisoned(self, agent_id):
        return Agent.IsPoisoned(agent_id)
    
    def IsConditioned(self, agent_id):
        return Agent.IsConditioned(agent_id)
    
    def IsEnchanted(self, agent_id):
        return Agent.IsEnchanted(agent_id)
    
    def IsHexed(self, agent_id):
        return Agent.IsHexed(agent_id)
    
    def IsDegenHexed(self, agent_id):
        return Agent.IsDegenHexed(agent_id)
    
    def IsDead(self, agent_id):
        return Agent.IsDead(agent_id)
    
    def IsAlive(self, agent_id):
        return Agent.IsAlive(agent_id)
    
    def IsWeaponSpelled(self, agent_id):
        return Agent.IsWeaponSpelled(agent_id)
    
    def IsInCombatStance(self, agent_id):
        return Agent.IsInCombatStance(agent_id)
    
    def IsAggressive(self, agent_id):
        return Agent.IsAggressive(agent_id)
        
    def IsAttacking(self, agent_id):
        return Agent.IsAttacking(agent_id)
        
    def IsCasting(self, agent_id) -> bool:
        return Agent.IsCasting(agent_id)
        
    def IsIdle(self, agent_id):
        return Agent.IsIdle(agent_id)
        
    def HasBossGlow(self, agent_id):
        return Agent.HasBossGlow(agent_id)
    
    def GetWeaponType(self, agent_id):
        return Agent.GetWeaponType(agent_id)
        
    def GetWeaponExtraData(self,agent_id):
        return Agent.GetWeaponExtraData(agent_id)
  
    def IsMartial(self, agent_id):
        return Agent.IsMartial(agent_id)

    def IsCaster(self, agent_id):
        return Agent.IsCaster(agent_id) 
    
    def IsMelee(self, agent_id):
        return Agent.IsMelee(agent_id)
  
    def IsRanged(self, agent_id):
        return Agent.IsRanged(agent_id)
    
    def GetCastingSkill(self, agent_id):
        return Agent.GetCastingSkill(agent_id)
    
    def GetDaggerStatus(self, agent_id):
        return Agent.GetDaggerStatus(agent_id)
    
    def GetAllegiance(self, agent_id):
        return Agent.GetAllegiance(agent_id)
    
    def IsPlayer(self, agent_id):
        return Agent.IsPlayer(agent_id)
    
    def IsNPC(self, agent_id):
        return Agent.IsNPC(agent_id)

    def HasQuest(self, agent_id):
        return Agent.HasQuest(agent_id)
        
    def IsDeadByTypeMap(self, agent_id):
        return Agent.IsDeadByTypeMap(agent_id)
    
    def IsFemale(self, agent_id):
        return Agent.IsFemale(agent_id)
    
    def IsHidingCape(self, agent_id):
        return Agent.IsHidingCape(agent_id)
    
    def CanBeViewedInPartyWindow(self, agent_id):
        return Agent.CanBeViewedInPartyWindow(agent_id)
        
    def IsSpawned(self, agent_id):
        return Agent.IsSpawned(agent_id)
        
    def IsBeingObserved(self, agent_id):
        return Agent.IsBeingObserved(agent_id)

    def GetOvercast(self, agent_id):
        return Agent.GetOvercast(agent_id)
    
    def GetItemAgent(self, agent_id):
        return Agent.GetItemAgentByID(agent_id)
    
    def GetItemAgentItemID(self, agent_id):
        item_agent = Agent.GetItemAgentByID(agent_id)
        if item_agent is None:
            return 0
        return item_agent.item_id
    
    def GetItemAgentOwnerID(self, agent_id):
        return Agent.GetItemAgentOwnerID(agent_id)
    
    def GetItemAgentExtraType(self, agent_id):
        return Agent.GetItemAgentExtraType(agent_id)
        
    def GetGadgetAgent(self, agent_id):
        return Agent.GetGadgetAgentByID(agent_id)
    
    def GetGadgetID(self, agent_id):
        return Agent.GetGadgetID(agent_id)
    