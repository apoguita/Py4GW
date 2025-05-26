from unittest import result
import Py4GW
import PyAgent
import PyPlayer
from .model_data import ModelData

class ItemOwnerCache:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ItemOwnerCache, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.cache = {}  # { item_id: original_owner_id }

    def check_and_cache(self, item_id, owner_id):
        if item_id not in self.cache:
            self.cache[item_id] = owner_id
        return self.cache[item_id]

    def clear_all(self):
        self.cache.clear()


# Agent
class Agent:
    @staticmethod
    def IsValid(agent_id):
        """
        Purpose: Check if the agent is valid.
        Args: agent_id (int): The ID of the agent.
        Returns: bool
        """
        return PyAgent.PyAgent(agent_id).IsValid(agent_id)
    
    @staticmethod
    def agent_instance(agent_id):
        """
        Helper method to create and return a PyAgent instance.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns:
            PyAgent: The PyAgent instance for the given ID.
        """
        return PyAgent.PyAgent(agent_id)

    @staticmethod
    def GetIdFromAgent(agent_instance):
        """
        Purpose: Retrieve the ID of an agent.
        Args:
            agent_instance (PyAgent): The agent instance.
        Returns: int
        """
        return agent_instance.id

    @staticmethod
    def GetAgentByID(agent_id):
        """
        Purpose: Retrieve an agent by its ID.
        Args:
            agent_id (int): The ID of the agent to retrieve.
        Returns: PyAgent
        """
        return Agent.agent_instance(agent_id)
    
    @staticmethod
    def GetAgentIDByName(name):
        """
        Purpose: Retrieve the first agent by matching a partial mask of its name.
        Args:
            partial_name (str): The partial name to search for.
        Returns:
            int: The AgentID of the matching agent, or None if no match is found.
        """
        import PyPlayer

        agent_array = PyPlayer.PyPlayer().GetAgentArray()

        for agent_id in agent_array:
            agent_name = Agent.GetName(agent_id)  # Retrieve the full name of the agent
            if name.lower() in agent_name.lower():  # Check for partial match (case-insensitive)
                return agent_id
        
        return 0

        

    @staticmethod
    def GetAttributes(agent_id):
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
    def GetNPCSkillbar(agent_id):
        """
        Purpose: Retrieve the skill bar of an NPC.
        Args: agent_id (int): The ID of the agent.
        Returns: list
        """
        import re
        from .Skill import Skill
        def format_skill_name(skill_name):
            """
            Formats a skill name by removing punctuation, replacing spaces with underscores,
            and preserving capitalization.
            """
            # Remove punctuation using regex
            skill_name = re.sub(r'[^\w\s]', '', skill_name)
            # Replace spaces with underscores
            skill_name = skill_name.replace(' ', '_')
            # Return the formatted skill name
            return skill_name

        def format_skills(skill_list):
            """
            Takes a list of skill names and returns a formatted list with the required structure.
            """
            return [format_skill_name(skill) for skill in skill_list]

        result = []
        agent_instance = Agent.agent_instance(agent_id)
        model_id = agent_instance.living_agent.player_number
        if model_id in ModelData:
            data = ModelData[model_id]
            skills_used = data.get('skills_used', [])
            formatted_skills = format_skills(skills_used)
            for skill in formatted_skills:
                result.append(Skill.GetID(skill))

        return result



    @staticmethod
    def GetModelID(agent_id):
        """Retrieve the model of an agent."""
        return Agent.agent_instance(agent_id).living_agent.player_number

    @staticmethod
    def IsLiving(agent_id):
        """Check if the agent is living."""
        return Agent.agent_instance(agent_id).is_living

    @staticmethod
    def IsItem(agent_id):
        """Check if the agent is an item."""
        return Agent.agent_instance(agent_id).is_item

    @staticmethod
    def IsGadget(agent_id):
        """Check if the agent is a gadget."""
        return Agent.agent_instance(agent_id).is_gadget

    @staticmethod
    def GetPlayerNumber(agent_id):
        """Retrieve the player number of an agent."""
        return Agent.agent_instance(agent_id).living_agent.player_number

    @staticmethod
    def GetLoginNumber(agent_id):
        """Retrieve the login number of an agent."""
        return Agent.agent_instance(agent_id).living_agent.login_number

    @staticmethod
    def IsSpirit(agent_id):
        """Check if the agent is a spirit."""
        return Agent.agent_instance(agent_id).living_agent.allegiance.GetName() == "Spirit/Pet"

    @staticmethod
    def IsMinion(agent_id):
        """Check if the agent is a minion."""
        return Agent.agent_instance(agent_id).living_agent.allegiance.GetName() == "Minion"

    @staticmethod
    def GetOwnerID(agent_id):
        """Retrieve the owner ID of an agent."""
        return Agent.agent_instance(agent_id).living_agent.owner_id

    @staticmethod
    def GetXY(agent_id):
        """
        Purpose: Retrieve the X and Y coordinates of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent = Agent.agent_instance(agent_id)
        return agent.x, agent.y

    @staticmethod
    def GetXYZ(agent_id):
        """
        Purpose: Retrieve the X, Y, and Z coordinates of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent = Agent.agent_instance(agent_id)
        return agent.x, agent.y, agent.z

    @staticmethod
    def GetZPlane(agent_id):
        """
        Purpose: Retrieve the Z plane of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        return Agent.agent_instance(agent_id).zplane

    @staticmethod
    def GetRotationAngle(agent_id):
        """
        Purpose: Retrieve the rotation angle of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        return Agent.agent_instance(agent_id).rotation_angle

    @staticmethod
    def GetRotationCos(agent_id):
        """
        Purpose: Retrieve the cosine of the rotation angle of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        return Agent.agent_instance(agent_id).rotation_cos

    @staticmethod
    def GetRotationSin(agent_id):
        """
        Purpose: Retrieve the sine of the rotation angle of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        return Agent.agent_instance(agent_id).rotation_sin

    @staticmethod
    def GetVelocityXY(agent_id):
        """
        Purpose: Retrieve the X and Y velocity of an agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent = Agent.agent_instance(agent_id)
        return agent.velocity_x, agent.velocity_y
    
    @staticmethod
    def RequestName(agent_id):
        """Purpose: Request the name of an agent."""
        Agent.agent_instance(agent_id).living_agent.RequestName()
        
    @staticmethod
    def IsNameReady(agent_id):
        """Purpose: Check if the agent name is ready."""
        return Agent.agent_instance(agent_id).living_agent.IsAgentNameReady()

    @staticmethod
    def GetName(agent_id):
        """Purpose: Get the name of an agent by its ID."""
        
        #agent_instance = Agent.agent_instance(agent_id)
        #model_id = agent_instance.living_agent.player_number
        #return ModelData.get(model_id, {}).get('name', agent_instance.living_agent.name)

        return Agent.agent_instance(agent_id).living_agent.GetName()


    @staticmethod
    def GetProfessions(agent_id):
        """
        Purpose: Retrieve the player's primary and secondary professions.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent_instance = Agent.agent_instance(agent_id)
        model_id = agent_instance.living_agent.player_number
        if model_id in ModelData:
            professions = ModelData[model_id].get('profession', [])
            primary_profession = PyAgent.Profession(professions[0])
            if len(professions) > 1:
                secondary_profession = PyAgent.Profession(professions[1])
            else:
                secondary_profession =  PyAgent.Profession("None")
            return primary_profession, secondary_profession

        return agent_instance.living_agent.profession, agent_instance.living_agent.secondary_profession

    @staticmethod
    def GetProfessionNames(agent_id):
        """
        Purpose: Retrieve the names of the player's primary and secondary professions.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent_instance = Agent.agent_instance(agent_id)
        # Nikon - comment out wiki data use below returning bad data
        # try:
        #     model_id = agent_instance.living_agent.player_number
        #     if model_id in ModelData:
        #         professions = ModelData[model_id].get('profession', [])
        #         primary_profession = PyAgent.Profession(professions[0])
        #         if len(professions) > 1:
        #             secondary_profession = PyAgent.Profession(professions[1])
        #         else:
        #             secondary_profession = PyAgent.Profession("None")
        #         return primary_profession.GetName(), secondary_profession.GetName()
        # except:
        #     return agent_instance.living_agent.profession.GetName(), agent_instance.living_agent.secondary_profession.GetName()
        return agent_instance.living_agent.profession.GetName(), agent_instance.living_agent.secondary_profession.GetName()

    @staticmethod
    def GetProfessionShortNames(agent_id):
        """
        Purpose: Retrieve the short names of the player's primary and secondary professions.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        
        agent_instance = Agent.agent_instance(agent_id)
        """
        try:
            model_id = agent_instance.living_agent.player_number
            if model_id in ModelData:
                professions = ModelData[model_id].get('profession', [])
                primary_profession = PyAgent.Profession(professions[0])
                if len(professions) > 1:
                    secondary_profession = PyAgent.Profession(professions[1])
                else:
                    secondary_profession = PyAgent.Profession("None")
                return primary_profession.GetShortName(), secondary_profession.GetShortName()
        except:
            return agent_instance.living_agent.profession.GetShortName(), agent_instance.living_agent.secondary_profession.GetShortName()
        """
        return agent_instance.living_agent.profession.GetShortName(), agent_instance.living_agent.secondary_profession.GetShortName()


    @staticmethod
    def GetProfessionIDs(agent_id):
        """
        Purpose: Retrieve the IDs of the player's primary and secondary professions.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent_instance = Agent.agent_instance(agent_id)
        """
        try:
            model_id = agent_instance.living_agent.player_number
            if model_id in ModelData:
                professions = ModelData[model_id].get('profession', [])
                primary_profession = PyAgent.Profession(professions[0])
                if len(professions) > 1:
                    secondary_profession = PyAgent.Profession(professions[1])
                else:
                    secondary_profession = PyAgent.Profession("None")
                return primary_profession.ToInt(), secondary_profession.ToInt()
        except:
            return agent_instance.living_agent.profession.ToInt(), agent_instance.living_agent.secondary_profession.ToInt()
        """
        return agent_instance.living_agent.profession.ToInt(), agent_instance.living_agent.secondary_profession.ToInt()


    @staticmethod
    def GetLevel(agent_id):
        """
        Purpose: Retrieve the level of the agent.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        return Agent.agent_instance(agent_id).living_agent.level

    @staticmethod
    def GetEnergy(agent_id):
        """
        Purpose: Retrieve the energy of the agent, only works for players and their heroes.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        return Agent.agent_instance(agent_id).living_agent.energy

    @staticmethod
    def GetMaxEnergy(agent_id):
        """
        Purpose: Retrieve the maximum energy of the agent, only works for players and heroes.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        return Agent.agent_instance(agent_id).living_agent.max_energy

    @staticmethod
    def GetEnergyRegen(agent_id):
        """
        Purpose: Retrieve the energy regeneration of the agent, only works for players and heroes.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        return Agent.agent_instance(agent_id).living_agent.energy_regen

    @staticmethod
    def GetHealth(agent_id):
        """
        Purpose: Retrieve the health of the agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        return Agent.agent_instance(agent_id).living_agent.hp

    @staticmethod
    def GetMaxHealth(agent_id):
        """
        Purpose: Retrieve the maximum health of the agent.
        Args: agent_id (int): The ID of the agent.
        Returns: int
        """
        return Agent.agent_instance(agent_id).living_agent.max_hp

    @staticmethod
    def GetHealthRegen(agent_id):
        """
        Purpose: Retrieve the health regeneration of the agent.
        Args: agent_id (int): The ID of the agent.
        Returns: float
        """
        return Agent.agent_instance(agent_id).living_agent.hp_regen

    @staticmethod
    def IsMoving(agent_id):
        """Purpose: Check if the agent is moving."""
        return Agent.agent_instance(agent_id).living_agent.is_moving

    @staticmethod
    def IsKnockedDown(agent_id):
        """Check if the agent is knocked down."""
        return Agent.agent_instance(agent_id).living_agent.is_knocked_down

    @staticmethod
    def IsBleeding(agent_id):
        """Check if the agent is bleeding."""
        return Agent.agent_instance(agent_id).living_agent.is_bleeding

    @staticmethod
    def IsCrippled(agent_id):
        """Check if the agent is crippled."""
        return Agent.agent_instance(agent_id).living_agent.is_crippled

    @staticmethod
    def IsDeepWounded(agent_id):
        """Check if the agent is deep wounded."""
        return Agent.agent_instance(agent_id).living_agent.is_deep_wounded

    @staticmethod
    def IsPoisoned(agent_id):
        """Check if the agent is poisoned."""
        return Agent.agent_instance(agent_id).living_agent.is_poisoned

    @staticmethod
    def IsConditioned(agent_id):
        """Check if the agent is conditioned."""
        return Agent.agent_instance(agent_id).living_agent.is_conditioned

    @staticmethod
    def IsEnchanted(agent_id):
        """Check if the agent is enchanted."""
        return Agent.agent_instance(agent_id).living_agent.is_enchanted

    @staticmethod
    def IsHexed(agent_id):
        """Check if the agent is hexed."""
        return Agent.agent_instance(agent_id).living_agent.is_hexed

    @staticmethod
    def IsDegenHexed(agent_id):
        """Check if the agent is degen hexed."""
        return Agent.agent_instance(agent_id).living_agent.is_degen_hexed

    @staticmethod
    def IsDead(agent_id):
        """Check if the agent is dead."""
        return not Agent.agent_instance(agent_id).living_agent.is_alive

    @staticmethod
    def IsAlive(agent_id):
        """Check if the agent is alive."""
        return Agent.agent_instance(agent_id).living_agent.is_alive

    @staticmethod
    def IsWeaponSpelled(agent_id):
        """Check if the agent's weapon is spelled."""
        return Agent.agent_instance(agent_id).living_agent.is_weapon_spelled

    @staticmethod
    def IsInCombatStance(agent_id):
        """Check if the agent is in combat stance."""
        return Agent.agent_instance(agent_id).living_agent.in_combat_stance

    @staticmethod
    def IsAggressive(agent_id):
        """Check if the agent is attacking or casting."""
        if Agent.agent_instance(agent_id).living_agent.is_attacking or Agent.agent_instance(agent_id).living_agent.is_casting:
            return True
        else:
            return False

    @staticmethod
    def IsAttacking(agent_id):
        """Check if the agent is attacking."""
        return Agent.agent_instance(agent_id).living_agent.is_attacking

    @staticmethod
    def IsCasting(agent_id):
        """Check if the agent is casting."""
        return Agent.agent_instance(agent_id).living_agent.is_casting

    @staticmethod
    def IsIdle(agent_id):
        """Check if the agent is idle."""
        return Agent.agent_instance(agent_id).living_agent.is_idle

    @staticmethod
    def HasBossGlow(agent_id):
        """Check if the agent has a boss glow."""
        return Agent.agent_instance(agent_id).living_agent.has_boss_glow


    @staticmethod
    def GetWeaponType(agent_id):
        """Purpose: Retrieve the weapon type of the agent."""
        return Agent.agent_instance(agent_id).living_agent.weapon_type.ToInt(), Agent.agent_instance(agent_id).living_agent.weapon_type.GetName()

    @staticmethod
    def GetWeaponExtraData(agent_id):
        """
        Purpose: Retrieve the weapon extra data of the agent.
        Args: agent_id (int): The ID of the agent.
        Returns: tuple
        """
        agent = Agent.agent_instance(agent_id)
        return agent.living_agent.weapon_item_id, agent.living_agent.weapon_item_type,  agent.living_agent.offhand_item_id, agent.living_agent.offhand_item_type

    @staticmethod
    def IsMartial(agent_id):
        """
        Purpose: Check if the agent is martial.
        Args: agent_id (int): The ID of the agent.
        Returns: bool
        """
        martial_weapon_types = ["Bow", "Axe", "Hammer", "Daggers", "Scythe", "Spear", "Sword"]
        return Agent.agent_instance(agent_id).living_agent.weapon_type.GetName() in martial_weapon_types

    @staticmethod
    def IsCaster(agent_id):
        """
        Purpose: Check if the agent is a caster.
        Args: agent_id (int): The ID of the agent.
        Returns: bool
        """
        return not Agent.IsMartial(agent_id)

    @staticmethod
    def IsMelee(agent_id):
        """
        Purpose: Check if the agent is melee.
        Args: agent_id (int): The ID of the agent.
        Returns: bool
        """
        melee_weapon_types = ["Axe", "Hammer", "Daggers", "Scythe", "Sword"]
        return Agent.agent_instance(agent_id).living_agent.weapon_type.GetName() in melee_weapon_types

    @staticmethod
    def IsRanged(agent_id):
        """
        Purpose: Check if the agent is ranged.
        Args: agent_id (int): The ID of the agent.
        Returns: bool
        """
        return not Agent.IsMelee(agent_id)

    @staticmethod
    def GetCastingSkill(agent_id):
        """ Purpose: Retrieve the casting skill of the agent."""
        return Agent.agent_instance(agent_id).living_agent.casting_skill_id

    @staticmethod
    def GetDaggerStatus(agent_id):
        """Purpose: Retrieve the dagger status of the agent."""
        return Agent.agent_instance(agent_id).living_agent.dagger_status

    @staticmethod
    def GetAllegiance(agent_id):
        """Purpose: Retrieve the allegiance of the agent."""
        return  Agent.agent_instance(agent_id).living_agent.allegiance.ToInt(), Agent.agent_instance(agent_id).living_agent.allegiance.GetName()

    @staticmethod
    def IsPlayer(agent_id):
        """Check if the agent is a player."""
        return Agent.agent_instance(agent_id).living_agent.is_player

    @staticmethod
    def IsNPC(agent_id):
        """Check if the agent is an NPC."""
        return Agent.agent_instance(agent_id).living_agent.is_npc

    @staticmethod
    def HasQuest(agent_id):
        """Check if the agent has a quest."""
        return Agent.agent_instance(agent_id).living_agent.has_quest

    @staticmethod
    def IsDeadByTypeMap(agent_id):
        """Check if the agent is dead by type map."""
        return Agent.agent_instance(agent_id).living_agent.is_dead_by_typemap

    @staticmethod
    def IsFemale(agent_id):
        """Check if the agent is female."""
        return Agent.agent_instance(agent_id).living_agent.is_female

    @staticmethod
    def IsHidingCape(agent_id):
        """Check if the agent is hiding the cape."""
        return Agent.agent_instance(agent_id).living_agent.is_hiding_cape

    @staticmethod
    def CanBeViewedInPartyWindow(agent_id):
        """Check if the agent can be viewed in the party window."""
        return Agent.agent_instance(agent_id).living_agent.can_be_viewed_in_party_window

    @staticmethod
    def IsSpawned(agent_id):
        """Check if the agent is spawned."""
        return Agent.agent_instance(agent_id).living_agent.is_spawned

    @staticmethod
    def IsBeingObserved(agent_id):
        """Check if the agent is being observed."""
        return Agent.agent_instance(agent_id).living_agent.is_being_observed

    @staticmethod
    def GetOvercast(agent_id):
        """Retrieve the overcast of the agent."""
        return Agent.agent_instance(agent_id).living_agent.overcast

    @staticmethod
    def GetItemAgent(agent_id):
        """Retrieve the item agent of the agent."""
        return Agent.agent_instance(agent_id).item_agent
    
    @staticmethod
    def GetItemAgentOwnerID(agent_id):
        item_owner_cache = ItemOwnerCache()
        """Retrieve the owner ID of the item agent."""
        item_data =  Agent.GetItemAgent(agent_id)    
        current_owner_id = item_data.owner_id   
        return item_owner_cache.check_and_cache(item_data.item_id, current_owner_id)
        
    @staticmethod
    def GetGadgetAgent(agent_id):
        """Retrieve the gadget agent of the agent."""
        return Agent.agent_instance(agent_id).gadget_agent

    @staticmethod
    def GetGadgetID(agent_id):
        """Retrieve the gadget ID of the agent."""
        gadget_agent = Agent.GetGadgetAgent(agent_id)
        return gadget_agent.gadget_id


class AgentName:
    """
    Purpose: Requests and Retrieve the name of an agent.
    """
    def __init__(self, agent_id, refresh_rate=1000):
        from .Py4GWcorelib import ThrottledTimer
        self.agent_id = agent_id
        self.name = None
        self.refresh_timer = ThrottledTimer(refresh_rate)
        self.requested = False
        self.name_ready = False

    def request_name(self):
        """Request the agent's name if not already requested."""
        if not self.requested:
            Agent.RequestName(self.agent_id)
            self.requested = True

    def is_name_ready(self):
        """Check if the name is ready."""
        return Agent.IsNameReady(self.agent_id)

    def get_name(self):
        """
        Get the agent's name.
        """
        
        if not self.name_ready or self.refresh_timer.IsExpired():
            self.refresh_timer.Reset()
            if not self.requested:
                self.request_name()
                self.name_ready = False
                return self.name
                
                
        if not self.name_ready and self.is_name_ready():
            self.name = Agent.GetName(self.agent_id)
            self.name_ready = True
            self.requested = False
                    
        return self.name
            












