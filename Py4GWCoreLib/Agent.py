import PyAgent
from .model_data import ModelData
from .native_src.context.AgentContext import AgentStruct, AgentLivingStruct, AgentItemStruct, AgentGadgetStruct
from .native_src.context.WorldContext import AttributeStruct
from .native_src.internals.string_table import decode as decode_raw


class Agent:

    @staticmethod
    def IsValid(agent_id: int) -> bool:
        """
        Purpose: Check if the agent is valid.
        Args: agent_id (int): The ID of the agent.
        Returns: bool
        """
        return Agent.GetAgentByID(agent_id) is not None

    _agent_cache: dict[int, "AgentStruct"] = {}
    _living_cache: dict[int, "AgentLivingStruct"] = {}
    _item_cache: dict[int, "AgentItemStruct"] = {}
    _gadget_cache: dict[int, "AgentGadgetStruct"] = {}

    @staticmethod
    def _invalidate_property_cache() -> None:
        Agent._agent_cache.clear()
        Agent._living_cache.clear()
        Agent._item_cache.clear()
        Agent._gadget_cache.clear()

    @staticmethod
    def enable() -> None:
        import PyCallback
        PyCallback.PyCallback.Register(
            "Agent.InvalidatePropertyCache",
            PyCallback.Phase.PreUpdate,
            Agent._invalidate_property_cache,
            priority=7
        )

    @staticmethod
    def GetAgentByID(agent_id: int):
        """
        Purpose: Retrieve an agent by its ID.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns: PyAgent
        """
        cached = Agent._agent_cache.get(agent_id)
        if cached is not None:
            return cached
        from .AgentArray import AgentArray
        agent = AgentArray.GetAgentByID(agent_id)
        if agent is not None:
            Agent._agent_cache[agent_id] = agent
        return agent

    @staticmethod
    def GetLivingAgentByID(agent_id: int):
        """
        Purpose: Retrieve a living agent by its ID.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns: PyAgent
        """
        cached = Agent._living_cache.get(agent_id)
        if cached is not None:
            return cached
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return None
        living = agent.GetAsAgentLiving()
        if living is not None:
            Agent._living_cache[agent_id] = living
        return living

    @staticmethod
    def GetItemAgentByID(agent_id: int):
        """
        Purpose: Retrieve an item agent by its ID.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns: PyAgent
        """
        cached = Agent._item_cache.get(agent_id)
        if cached is not None:
            return cached
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return None
        item = agent.GetAsAgentItem()
        if item is not None:
            Agent._item_cache[agent_id] = item
        return item

    @staticmethod
    def GetGadgetAgentByID(agent_id: int):
        """
        Purpose: Retrieve a gadget agent by its ID.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns: PyAgent
        """
        cached = Agent._gadget_cache.get(agent_id)
        if cached is not None:
            return cached
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return None
        gadget = agent.GetAsAgentGadget()
        if gadget is not None:
            Agent._gadget_cache[agent_id] = gadget
        return gadget
    
    @staticmethod
    def GetNameByID(agent_id: int) -> str:
        """Get the decoded display name of an agent by its ID."""
        enc_bytes = PyAgent.PyAgent.GetAgentEncName(agent_id)
        if not enc_bytes:
            return ""
        return decode_raw(bytes(enc_bytes))

    RequestName = GetNameByID

    @staticmethod
    def IsNameReady(agent_id: int) -> bool:
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
    def GetAttributes(agent_id: int) -> list[AttributeStruct]:
        from .Context import GWContext

        if (world_ctx := GWContext.World.GetContext()) is None:
            return []

        attributes = world_ctx.get_attributes_by_agent_id(agent_id)
        return attributes
    
    @staticmethod
    def GetAttributesDict(agent_id: int) -> dict[int, int]:  
        # Get attributes
        attributes_raw:list[AttributeStruct] = Agent.GetAttributes(agent_id)
        attributes = {}

        # Convert attributes to dictionary format
        for attr in attributes_raw:
            attr_id = int(attr.attribute_id)  # Convert enum to integer
            attr_level = attr.level_base  # Get attribute level
            if attr_level > 0:  # Only include attributes with points
                attributes[attr_id] = attr_level
                
        return attributes
        
    @staticmethod
    def GetInstanceFrames(agent_id : int) -> int:
        """
        Purpose: Retrieve the instance timer of an agent in frames.
        Args:
            agent_id (int): The ID of the agent.
        Returns: int
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0
        return agent.timer
    
    @staticmethod
    def GetInstanceUptime(agent_id : int) -> int:
        """
        Purpose: Retrieve the instance timer of an agent in milliseconds.
        Args:
            agent_id (int): The ID of the agent.
        Returns: int
        """
        from .UIManager import UIManager
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0
        fps_limit = UIManager.GetFPSLimit() 
        fps_limit = max(fps_limit, 30)  # Prevent division by zero
        return int(agent.timer / fps_limit * 1000)
    
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
    def GetZPlane(agent_id : int) -> int:
        """
        Purpose: Retrieve the Z plane of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        agent = Agent.GetAgentByID(agent_id)
        if agent is None:
            return 0
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
        from .py4gwcorelib_src.Utils import Utils
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
        from .py4gwcorelib_src.Utils import Utils
        
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
    def GetCastingSkillID(agent_id: int) -> int:
        """ Purpose: Retrieve the casting skill of the agent."""
        if not Agent.IsCasting(agent_id):
            return 0    
        
        living = Agent.GetLivingAgentByID(agent_id)
        if living is None:
            return 0
        return living.skill


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


Agent.enable()

    






