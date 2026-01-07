
import time
from PyAgent import AttributeClass
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

from .model_data import ModelData
from .native_src.context.AgentContext import AgentStruct, AgentLivingStruct, AgentItemStruct, AgentGadgetStruct
from .native_src.internals.helpers import encoded_wstr_to_str

# Agent
class Agent:
    name_cache: dict[int, tuple[str, float]] = {}  # agent_id -> (name, timestamp)
    name_requested: set[int] = set()
    name_timeout_ms = 1_000

    
    @staticmethod
    def _update_cache() -> None:
        import PyAgent
        """Should be called every frame to resolve names when ready."""
        now = time.time() * 1000
        for agent_id in list(Agent.name_requested):
            name = encoded_wstr_to_str(PyAgent.PyAgent.GetNameByID(agent_id))
            if name is None:
                name = "INVALID"

            Agent.name_cache[agent_id] = (name, now)
            Agent.name_requested.discard(agent_id)
            
    @staticmethod
    def _reset_cache() -> None:
        """Resets the name cache and requested set."""
        Agent.name_cache.clear()
        Agent.name_requested.clear()
        
    @staticmethod
    def IsValid(agent_id: int) -> bool:
        """
        Purpose: Check if the agent is valid.
        Args: agent_id (int): The ID of the agent.
        Returns: bool
        """
        from .AgentArray import AgentArray
        agent = AgentArray.GetAgentByID(agent_id)
        if agent is None:
            return False
        return True
    
    @staticmethod
    def require_valid(func):
        """
        Decorator for safe agent access.
        Ensures the agent_id is valid before calling the function.
        """
        def wrapper(agent_id, *args, **kwargs):
            if not Agent.IsValid(agent_id):
                return None
            return func(agent_id, *args, **kwargs)
        return wrapper

    @staticmethod
    @require_valid
    def GetAgentByID(agent_id: int) -> AgentStruct | None:
        """
        Purpose: Retrieve an agent by its ID.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns: PyAgent
        """
        from .AgentArray import AgentArray
        agent = AgentArray.GetAgentByID(agent_id)
        if agent is None:
            return None
        return agent
    
    @staticmethod
    @require_valid
    def GetLivingAgentByID(agent_id: int) -> AgentLivingStruct | None:
        """
        Purpose: Retrieve a living agent by its ID.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns: PyAgent
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return None
        return agent.GetAsAgentLiving()
    
    @staticmethod
    @require_valid
    def GetItemAgentByID(agent_id: int) -> AgentItemStruct | None:
        """
        Purpose: Retrieve an item agent by its ID.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns: PyAgent
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return None
        return agent.GetAsAgentItem()
    
    @staticmethod
    @require_valid
    def GetGadgetAgentByID(agent_id: int) -> AgentGadgetStruct | None:
        """
        Purpose: Retrieve a gadget agent by its ID.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns: PyAgent
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return None
        return agent.GetAsAgentGadget()
    
    @staticmethod
    def GetNameByID(agent_id : int) -> str:
        import PyAgent
        """Purpose: Get the native name of an agent by its ID."""
        now = time.time() * 1000  # current time in ms
        # Cached and still valid
        if agent_id in Agent.name_cache:
            name, timestamp = Agent.name_cache[agent_id]
            if now - timestamp < Agent.name_timeout_ms:
                return name
            else:
                # Expired; refresh
                if agent_id not in Agent.name_requested:    
                    PyAgent.PyAgent.GetNameByID(agent_id)
                    Agent.name_requested.add(agent_id)
                return name  # Still return old while waiting

        # Already requested but not ready
        if agent_id in Agent.name_requested:
            return ""

        PyAgent.PyAgent.GetNameByID(agent_id)
        Agent.name_requested.add(agent_id)
        return ""

    #aliases for retro compatibility
    RequestName = GetNameByID
        
    @staticmethod
    def IsNameReady(agent_id: int) -> bool:
        """Purpose: Check if the agent name is ready."""
        return Agent.GetNameByID(agent_id) != ""
 
    
    
    @staticmethod
    def GetAgentIDByName(name:str) -> int:
        from .AgentArray import AgentArray
        """
        Purpose: Retrieve the first agent by matching a partial mask of its name.
        Args:
            partial_name (str): The partial name to search for.
        Returns:
            int: The AgentID of the matching agent, or 0 if no match is found.
        """
        agent_array = AgentArray.GetAgentArray()

        for agent_id in agent_array:
            agent_name = Agent.GetNameByID(agent_id)  # Retrieve the full name of the agent
            if name.lower() in agent_name.lower():  # Check for partial match (case-insensitive)
                if Agent.IsValid(agent_id):
                    return agent_id
        return 0
    
    @staticmethod
    def GetAgentEffects(agent_id : int) -> int:
        """
        Purpose: Retrieve the effects of an agent.
        Args:
            agent_id (int): The ID of the agent.
        Returns: int
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        
        return living.effects
    
    @staticmethod
    def GetTypeMap(agent_id : int) -> int:
        """
        Purpose: Retrieve the type map of an agent.
        Args:
            agent_id (int): The ID of the agent.
        Returns: int
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return living.type_map
    
    @staticmethod
    def GetModelState(agent_id : int) -> int:
        """
        Purpose: Retrieve the model state of an agent.
        Args:
            agent_id (int): The ID of the agent.
        Returns: int
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return living.model_state 

    @staticmethod
    def GetModelID(agent_id : int) -> int:
        """Retrieve the model of an agent."""
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return living.player_number

    @staticmethod
    def IsLiving(agent_id : int) -> bool:
        """Check if the agent is living."""
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return False
        return agent.is_living_type

    @staticmethod
    def IsItem(agent_id : int) -> bool:
        """Check if the agent is an item."""
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return False
        return agent.is_item_type
    
    @staticmethod
    def IsGadget(agent_id : int) -> bool:
        """Check if the agent is a gadget."""
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return False
        return agent.is_gadget_type

    @staticmethod
    def GetPlayerNumber(agent_id : int) -> int:
        """Retrieve the player number of an agent."""
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return living.player_number

    @staticmethod
    def GetLoginNumber(agent_id : int) -> int:
        """Retrieve the login number of an agent."""
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return living.login_number

    @staticmethod
    def IsSpirit(agent_id : int) -> bool:
        """Check if the agent is a spirit."""
        from .enums_src.GameData_enums import Allegiance
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        allegiance = Allegiance(living.allegiance)
        return allegiance == Allegiance.SpiritPet

    @staticmethod
    def IsMinion(agent_id : int) -> bool:
        """Check if the agent is a minion."""
        from .enums_src.GameData_enums import Allegiance
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        allegiance = Allegiance(living.allegiance)
        return allegiance == Allegiance.Minion

    @staticmethod
    def GetOwnerID(agent_id : int) -> int:
        """Retrieve the owner ID of an agent."""
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return living.owner

    @staticmethod
    def GetXY(agent_id : int) -> tuple[float, float]:
        """
        Purpose: Retrieve the X and Y coordinates of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0, 0.0
        pos = agent.pos
        return pos.x, pos.y

    @staticmethod
    def GetXYZ(agent_id : int) -> tuple[float, float, float]:
        """
        Purpose: Retrieve the X, Y, and Z coordinates of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0, 0.0, 0.0
        pos = agent.pos
        z = agent.z
        return pos.x, pos.y, z

    @staticmethod
    def GetZPlane(agent_id : int) -> float:
        """
        Purpose: Retrieve the Z plane of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0
        pos = agent.pos
        return pos.zplane
    
    @staticmethod
    def GetNameTagXYZ(agent_id : int) -> tuple[float, float, float]:
        """
        Purpose: Retrieve the name tag X and Y coordinates of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0, 0.0, 0.0
        return agent.name_tag_x, agent.name_tag_y, agent.name_tag_z
    
    @staticmethod
    def GetModelScale1(agent_id : int) -> tuple[float, float]:
        """
        Purpose: Retrieve the model scale of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0, 0.0
        
        return agent.width1, agent.height1
    
    @staticmethod
    def GetModelScale2(agent_id : int) -> tuple[float, float]:
        """
        Purpose: Retrieve the model scale of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0, 0.0
        
        return agent.width2, agent.height2
    
    @staticmethod
    def GetModelScale3(agent_id : int) -> tuple[float, float]:
        """
        Purpose: Retrieve the model scale of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0, 0.0
        
        return agent.width3, agent.height3
    
    @staticmethod
    def GetNameProperties(agent_id : int) -> int:
        """
        Purpose: Retrieve the name properties of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0
        
        return agent.name_properties
        
    @staticmethod
    def GetVisualEffects(agent_id : int) -> int:
        """
        Purpose: Retrieve the visual effects of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0
        
        return agent.visual_effects
    
    @staticmethod
    def GetTerrainNormalXYZ(agent_id : int) -> tuple[float, float, float]:
        """
        Purpose: Retrieve the terrain normal X, Y, and Z of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0, 0.0, 0.0
        
        return agent.terrain_normal.x, agent.terrain_normal.y, agent.terrain_normal.z
    
    @staticmethod
    def GetGround(agent_id : int) -> float:
        """
        Purpose: Retrieve the ground of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0
        
        return agent.ground
    
    @staticmethod
    def GetAnimationCode (agent_id : int) -> int:
        """
        Purpose: Retrieve the animation code of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0
        
        return living_agent.animation_code
    
    @staticmethod
    def GetWeaponItemType(agent_id : int) -> int:
        """
        Purpose: Retrieve the weapon item type of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0
        
        return living_agent.weapon_item_type
    
    @staticmethod
    def GetOffhandItemType(agent_id : int) -> int:
        """
        Purpose: Retrieve the offhand item type of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0
        
        return living_agent.offhand_item_type
    
    @staticmethod
    def GetAnimationType(agent_id : int) -> float:
        """
        Purpose: Retrieve the animation type of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0
        
        return living_agent.animation_type
    
    @staticmethod
    def GetWeaponAttackSpeed(agent_id : int) -> float:
        """
        Purpose: Retrieve the weapon attack speed of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0.0
        
        return living_agent.weapon_attack_speed
    
    @staticmethod
    def GetAttackSpeedModifier(agent_id : int) -> float:
        """
        Purpose: Retrieve the attack speed modifier of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0.0
        
        return living_agent.attack_speed_modifier
    
    @staticmethod
    def GetAgentModelType(agent_id : int) -> int:
        """
        Purpose: Retrieve the agent model type of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0
        
        return living_agent.agent_model_type
    
    @staticmethod
    def GetTransmogNPCID(agent_id : int) -> int:
        """ 
        Purpose: Retrieve the transmog NPC ID of an agent.  
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0
        
        return living_agent.transmog_npc_id
    
    @staticmethod
    def GetGuildID(agent_id : int) -> int:
        """ 
        Purpose: Retrieve the guild ID of an agent.  
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0
        
        tags = living_agent.tags
        if tags is None:
            return 0
        return tags.guild_id
    
    @staticmethod
    def GetTeamID(agent_id : int) -> int:
        """ 
        Purpose: Retrieve the team ID of an agent.  
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0
        
        return living_agent.team_id
    
    @staticmethod
    def GetAnimationSpeed(agent_id : int) -> float:
        """
        Purpose: Retrieve the animation speed of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0.0
        
        return living_agent.animation_speed
    
    @staticmethod
    def GetAnimationID(agent_id : int) -> int:
        """
        Purpose: Retrieve the animation ID of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living_agent = Agent.GetLivingAgentByID(agent_id)
        if living_agent is None:
            return 0
        
        return living_agent.animation_id

    @staticmethod
    def GetRotationAngle(agent_id : int) -> float:
        """
        Purpose: Retrieve the rotation angle of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0
        return agent.rotation_angle
    
    @staticmethod
    def GetRotationCos(agent_id : int) -> float:
        """
        Purpose: Retrieve the cosine of the rotation angle of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0
        return agent.rotation_cos


    @staticmethod
    def GetRotationSin(agent_id : int) -> float:
        """
        Purpose: Retrieve the sine of the rotation angle of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0
        return agent.rotation_sin

    @staticmethod
    def GetVelocityXY(agent_id : int) -> tuple[float, float]:
        """
        Purpose: Retrieve the X and Y velocity of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0.0, 0.0
        velocity = agent.velocity
        
        return velocity.x, velocity.y
    
    @staticmethod
    def GetProfessions(agent_id : int) -> tuple[int, int]:
        """
        Purpose: Retrieve the player's primary and secondary professions.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0, 0

        return living.primary, living.secondary

    @staticmethod
    def GetProfessionNames(agent_id : int) -> tuple[str, str]:
        """
        Purpose: Retrieve the names of the player's primary and secondary professions.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        from .enums_src.GameData_enums import Profession, Profession_Names
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return "", ""

        profession = Profession(living.primary)
        prof_name = Profession_Names[profession]
        secondary_profession = Profession(living.secondary)
        secondary_prof_name = Profession_Names[secondary_profession]
        
        return prof_name  if prof_name is not None else "", secondary_prof_name if secondary_prof_name is not None else ""
    
    @staticmethod
    def GetProfessionShortNames(agent_id : int) -> tuple[str, str]:
        """
        Purpose: Retrieve the short names of the player's primary and secondary professions.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        from .enums_src.GameData_enums import ProfessionShort, ProfessionShort_Names
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return "", ""

        profession = ProfessionShort(living.primary)
        prof_name = ProfessionShort_Names[profession]
        secondary_profession = ProfessionShort(living.secondary)
        secondary_prof_name = ProfessionShort_Names[secondary_profession]
        
        return prof_name , secondary_prof_name
    
    @staticmethod
    def GetProfessionIDs(agent_id : int) -> tuple[int, int]:
        """
        Purpose: Retrieve the IDs of the player's primary and secondary professions.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0, 0
        return living.primary, living.secondary

    @staticmethod
    def GetLevel(agent_id : int) -> int:
        """
        Purpose: Retrieve the level of the agent.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return living.level

    @staticmethod
    def GetEnergy(agent_id: int) -> float:
        """
        Purpose: Retrieve the energy of the agent, only works for players and their heroes.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0.0
        return living.energy
    
    @staticmethod
    def GetMaxEnergy(agent_id: int) -> int:
        """
        Purpose: Retrieve the maximum energy of the agent, only works for players and heroes.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return living.max_energy

    @staticmethod
    def GetEnergyRegen(agent_id: int) -> float:
        """
        Purpose: Retrieve the energy regeneration of the agent, only works for players and heroes.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0.0
        return living.energy_regen
    
    @staticmethod
    def GetEnergyPips(agent_id: int) -> int:
        """
        Purpose: Retrieve the energy pips of the agent, only works for players and heroes.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return Utils.calculate_energy_pips(living.max_energy, living.energy_regen)

    @staticmethod
    def GetHealth(agent_id: int) -> float:
        """
        Purpose: Retrieve the health of the agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0.0
        return living.hp

    @staticmethod
    def GetMaxHealth(agent_id: int) -> int:
        """
        Purpose: Retrieve the maximum health of the agent.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return living.max_hp

    @staticmethod
    def GetHealthRegen(agent_id: int) -> float:
        """
        Purpose: Retrieve the health regeneration of the agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0.0
        return living.hp_pips
    
    @staticmethod
    def GetHealthPips(agent_id: int) -> int:
        """
        Purpose: Retrieve the health pips of the agent.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        
        return Utils.calculate_health_pips(living.max_hp, living.hp_pips)

    @staticmethod
    def IsMoving(agent_id: int) -> bool:
        living  = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_moving

    @staticmethod
    def IsKnockedDown(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_knocked_down

    @staticmethod
    def IsBleeding(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_bleeding

    @staticmethod
    def IsCrippled(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_crippled

    @staticmethod
    def IsDeepWounded(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_deep_wounded

    @staticmethod
    def IsPoisoned(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_poisoned

    @staticmethod
    def IsConditioned(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_conditioned

    @staticmethod
    def IsEnchanted(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_enchanted

    @staticmethod
    def IsHexed(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_hexed

    @staticmethod
    def IsDegenHexed(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_degen_hexed

    @staticmethod
    def IsDead(agent_id: int) -> bool:
        """Check if the agent is dead."""
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        is_dead = living.is_dead
        dead_by_type_map = living.is_dead_by_type_map
        return is_dead or dead_by_type_map

    @staticmethod
    def IsAlive(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        health = living.hp
        return not Agent.IsDead(agent_id) and health > 0.0

    @staticmethod
    def IsWeaponSpelled(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_weapon_spelled

    @staticmethod
    def IsInCombatStance(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_in_combat_stance

    @staticmethod
    def IsAggressive(agent_id: int) -> bool:
        """Check if the agent is attacking or casting."""
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        is_attacking = living.is_attacking
        is_casting = living.is_casting
        return is_attacking or is_casting

    @staticmethod
    def IsAttacking(agent_id:int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_attacking

    @staticmethod
    def IsCasting(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_casting

    @staticmethod
    def IsIdle(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_idle

    @staticmethod
    def HasBossGlow(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.has_boss_glow

    @staticmethod
    def GetWeaponType(agent_id: int) -> tuple[int, str]:
        """Purpose: Retrieve the weapon type of the agent."""
        """Purpose: Retrieve the allegiance of the agent."""
        from .enums_src.GameData_enums import  Weapon, Weapon_Names
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0, "Unknown"
        
        try:
            weapon_type_enum = Weapon(living.weapon_type)
        except ValueError:
            return living.weapon_type, "Unknown"

        name = Weapon_Names.get(weapon_type_enum, "Unknown")
        return living.weapon_type, name

    @staticmethod
    def GetWeaponExtraData(agent_id: int) -> tuple[int, int, int, int]:
        """
        Purpose: Retrieve the weapon extra data of the agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0, 0, 0, 0
        
        return living.weapon_item_id, living.weapon_item_type, living.offhand_item_id, living.offhand_item_type

    @staticmethod
    def IsMartial(agent_id: int) -> bool:
        """
        Purpose: Check if the agent is martial.
        Args: agent_id (int): The ID of the agent.
        Returns: bool
        """
        martial_weapon_types = ["Bow", "Axe", "Hammer", "Daggers", "Scythe", "Spear", "Sword"]
        weapon_type, weapon_name = Agent.GetWeaponType(agent_id)
        return weapon_name in martial_weapon_types

    @staticmethod
    def IsCaster(agent_id: int) -> bool:
        """
        Purpose: Check if the agent is a caster.
        Args: agent_id (int): The ID of the agent.
        Returns: bool
        """
        return not Agent.IsMartial(agent_id)

    @staticmethod
    def IsMelee(agent_id: int) -> bool:
        """
        Purpose: Check if the agent is melee.
        Args: agent_id (int): The ID of the agent.
        Returns: bool
        """
        melee_weapon_types = ["Axe", "Hammer", "Daggers", "Scythe", "Sword"]
        weapon_type, weapon_name = Agent.GetWeaponType(agent_id)
        return weapon_name in melee_weapon_types

    @staticmethod
    def IsRanged(agent_id: int) -> bool:
        """
        Purpose: Check if the agent is ranged.
        Args: agent_id (int): The ID of the agent.
        Returns: bool
        """
        return not Agent.IsMelee(agent_id)

    @staticmethod
    def GetDaggerStatus(agent_id: int) -> int:
        """Purpose: Retrieve the dagger status of the agent."""
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return living.dagger_status
    
    @staticmethod
    def GetAllegiance(agent_id: int) -> tuple[int, str]:
        """Purpose: Retrieve the allegiance of the agent."""
        from .enums_src.GameData_enums import  Allegiance, AllegianceNames
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0, "Unknown"
        
        try:
            allegiance_enum = Allegiance(living.allegiance)
        except ValueError:
            return living.allegiance, "Unknown"

        name = AllegianceNames.get(allegiance_enum, "Unknown")
        return living.allegiance, name
    
    @staticmethod
    def IsPlayer(agent_id: int) -> bool:
        login_number = Agent.GetLoginNumber(agent_id)
        return login_number  != 0

    @staticmethod
    def IsNPC(agent_id: int) -> bool:
        login_number = Agent.GetLoginNumber(agent_id)
        return login_number  == 0

    @staticmethod
    def HasQuest(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.has_quest

    @staticmethod
    def IsDeadByTypeMap(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_dead_by_type_map

    @staticmethod
    def IsFemale(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_female
    
    @staticmethod
    def IsHidingCape(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_hiding_cape

    @staticmethod
    def CanBeViewedInPartyWindow(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.can_be_viewed_in_party_window

    @staticmethod
    def IsSpawned(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_spawned

    @staticmethod
    def IsBeingObserved(agent_id: int) -> bool:
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return False
        return living.is_being_observed

    @staticmethod
    def GetOvercast(agent_id: int) -> float:
        """Retrieve the overcast of the agent."""
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0.0
        return living.h0128
    
    @staticmethod
    def GetProfessionsTexturePaths(agent_id: int) -> tuple[str, str]:
        """
        Purpose: Retrieve the texture paths of the player's primary and secondary professions.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        import Py4GW
        primary, secondary = Agent.GetProfessions(agent_id)
        primary_name, secondary_name = Agent.GetProfessionNames(agent_id)
        projects_base_folder = Py4GW.Console.get_projects_path()
        
        if primary == 0:
            primary_texture = ""
        else:
            primary_texture = f"\\Textures\\Profession_Icons\\[{primary}] - {primary_name}.png"
        if secondary == 0:
            secondary_texture = ""
        else:
            secondary_texture = f"\\Textures\\Profession_Icons\\[{secondary}] - {secondary_name}.png"
            
        return projects_base_folder + primary_texture, projects_base_folder + secondary_texture
    
#region items
    @staticmethod
    def GetItemAgentOwnerID(agent_id: int) -> int:
        #item_owner_cache = ItemOwnerCache()
        """Retrieve the owner ID of the item agent."""
        item = Agent.GetItemAgentByID(agent_id)
        if item is None:
            return 999
        current_owner_id = item.owner
  
        return current_owner_id
    
    @staticmethod
    def GetItemAgentItemID(agent_id: int) -> int:
        """Retrieve the item ID of the item agent."""
        item_data =  Agent.GetItemAgentByID(agent_id)    
        if item_data is None:
            return 0
        return item_data.item_id
    
    @staticmethod
    def GetItemAgentExtraType(agent_id: int) -> int:
        """Retrieve the extra type of the item agent."""
        item_data =  Agent.GetItemAgentByID(agent_id)    
        if item_data is None:
            return 0
        return item_data.extra_type
    
    @staticmethod
    def GetItemAgenth00CC(agent_id: int) -> int:
        """Retrieve the h00CC of the item agent."""
        item_data =  Agent.GetItemAgentByID(agent_id)    
        if item_data is None:
            return 0
        return item_data.h00CC
    
#region gadgets
    @staticmethod
    def GetGadgetID(agent_id : int) -> int:
        """Retrieve the gadget ID of the agent."""
        gadget = Agent.GetGadgetAgentByID(agent_id)
        if gadget is None:
            return 0
        return gadget.gadget_id
    
    @staticmethod
    def GetGadgetAgentID(agent_id: int) -> int:
        """Retrieve the gadget ID of the agent."""
        gadget = Agent.GetGadgetAgentByID(agent_id)
        if gadget is None:
            return 0
        return gadget.agent_id

    @staticmethod
    def GetGadgetAgentExtraType(agent_id: int) -> int:
        """Retrieve the extra type of the gadget agent."""
        gadget = Agent.GetGadgetAgentByID(agent_id)
        if gadget is None:
            return 0
        return gadget.extra_type
    
    @staticmethod
    def GetGadgetAgenth00C4(agent_id: int) -> int:
        """Retrieve the h00CC of the gadget agent."""
        gadget = Agent.GetGadgetAgentByID(agent_id)
        if gadget is None:
            return 0
        return gadget.h00C4
    
    @staticmethod
    def GetGadgetAgenth00C8(agent_id: int) -> int:
        """Retrieve the h00C8 of the gadget agent."""
        gadget = Agent.GetGadgetAgentByID(agent_id)
        if gadget is None:
            return 0
        return gadget.h00C8

    @staticmethod
    def GetGadgetAgenth00D4(agent_id: int) -> list:
        """Retrieve the h00D4 of the gadget agent."""
        gadget = Agent.GetGadgetAgentByID(agent_id)
        if gadget is None:
            return []
        return gadget.h00D4


    #region not worked
    import PyAgent
    @staticmethod
    def agent_instance(agent_id : int) -> PyAgent.PyAgent:
        import PyAgent
        """
        Helper method to create and return a PyAgent instance.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns:
            PyAgent: The PyAgent instance for the given ID.
        """
        return PyAgent.PyAgent(agent_id)

    @staticmethod
    def GetAttributes(agent_id: int) -> list[AttributeClass]:
        import PyAgent
        """
        Purpose: Retrieve the attributes of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """

        def safe_int(value):
            """
            Safely convert a value to an integer.
            Returns 0 if the value is not a valid integer.
            """
            if isinstance(value, int):
                return value  # Already an integer
            if isinstance(value, str) and value.isdigit():
                return int(value)  # Convert valid string integers like '15'
            try:
                # Attempt to extract the first valid integer if possible
                return int(value.split()[0]) if isinstance(value, str) else 0
            except (ValueError, AttributeError):
                return 0  # Default to 0 for any invalid cases

        agent_instance = Agent.agent_instance(agent_id)
        model_id = agent_instance.living_agent.player_number
        attribute_list = []
        if model_id in ModelData:
            attributes = ModelData[model_id].get('attributes', [])
            for attribute in attributes:
                level = safe_int(attribute.get('level', 0))

                name = attribute.get('name', 'N/A')
                attribute_instance = PyAgent.AttributeClass(name, level)
                if attribute_instance.GetName() != "None":
                    attribute_list.append(attribute_instance)
            return attribute_list

        agent = Agent.agent_instance(agent_id)
        return agent.attributes
    
    @staticmethod
    def GetAttributesDict(agent_id: int) -> dict[int, int]:  
        import PyAgent  
        # Get attributes
        attributes_raw:list[PyAgent.AttributeClass] = Agent.GetAttributes(agent_id)
        attributes = {}

        # Convert attributes to dictionary format
        for attr in attributes_raw:
            attr_id = int(attr.attribute_id)  # Convert enum to integer
            attr_level = attr.level_base  # Get attribute level
            if attr_level > 0:  # Only include attributes with points
                attributes[attr_id] = attr_level
                
        return attributes

    @staticmethod
    def GetCastingSkill(agent_id: int) -> int:
        """ Purpose: Retrieve the casting skill of the agent."""
        if not Agent.agent_instance(agent_id).living_agent.is_casting:
            return 0    
        return Agent.agent_instance(agent_id).living_agent.casting_skill_id







