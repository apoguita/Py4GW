
import PyEffects

from .Player import Player

class Effects:

    @staticmethod
    def DropBuff(buff_id):
        """
        Purpose: Drop a specific buff by Buff Id.
        Args:
            skill_id (int): The skill ID of the buff to drop.
        Returns: None
        """
        agent_effects = PyEffects.PyEffects(Player.GetAgentID())
        agent_effects.DropBuff(buff_id)
    
    @staticmethod
    def GetBuffs(agent_id: int):
        """
        Purpose: Get the list of active buffs for a specific agent.
        Args:
            agent_id (int): The agent ID of the party member.
        Returns: list: A list of BuffType objects for the specified agent.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        buff_list = agent_effects.GetBuffs()
        return buff_list

    @staticmethod
    def GetEffects(agent_id: int):
        """
        Purpose: Get the list of active effects for a specific agent.
        Args:
            agent_id (int): The agent ID of the party member.
        Returns: list: A list of EffectType objects for the specified agent.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        effects_list = agent_effects.GetEffects()
        return effects_list

    @staticmethod
    def GetBuffCount(agent_id: int):
        """
        Purpose: Get the count of active buffs for a specific agent.
        Args:
            agent_id (int): The agent ID of the party member.
        Returns: int: The number of buffs applied to the agent.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        buff_count = agent_effects.GetBuffCount()
        return buff_count

    @staticmethod
    def GetEffectCount(agent_id: int):
        """
        Purpose: Get the count of active effects for a specific agent.
        Args:
            agent_id (int): The agent ID of the party member.
        Returns: int: The number of effects applied to the agent.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        effect_count = agent_effects.GetEffectCount()
        return effect_count

    @staticmethod
    def BuffExists(agent_id: int, skill_id: int):
        """
        Purpose: Check if a specific buff exists for a given agent and skill ID.
        Args:
            agent_id (int): The agent ID of the party member.
            skill_id (int): The skill ID of the buff.
        Returns: bool: True if the buff exists, False otherwise.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        buff_exists = agent_effects.BuffExists(skill_id)
        return buff_exists

    @staticmethod
    def EffectExists(agent_id: int, skill_id: int):
        """
        Purpose: Check if a specific effect exists for a given agent and skill ID.
        Args:
            agent_id (int): The agent ID of the party member.
            skill_id (int): The skill ID of the effect.
        Returns: bool: True if the effect exists, False otherwise.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        effect_exists = agent_effects.EffectExists(skill_id)
        return effect_exists

    @staticmethod
    def EffectAttributeLevel(agent_id: int, skill_id: int):
        """
        Purpose: Get the attribute level of a specific effect.
        Args:
            agent_id (int): The agent ID of the party member.
            skill_id (int): The skill ID of the effect.
        Returns: int: The attribute level of the effect, or 0 if effect doesn't exist.
        """
        agent_effects = PyEffects.PyEffects(agent_id)
        effects_list = agent_effects.GetEffects()
        for effect in effects_list:
            if effect.skill_id == skill_id:
                return effect.attribute_level  
        return 0
