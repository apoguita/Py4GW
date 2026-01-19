import PyEffects
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager

class EffectsCache:
    _buff_cache: dict[int, list] = {}
    _effect_cache: dict[int, list] = {}

    @classmethod
    def _update_or_insert(cls, agent_id: int):
        """Insert or update cache for agent."""
        effects = PyEffects.PyEffects(agent_id)
        cls._buff_cache[agent_id] = effects.GetBuffs()
        cls._effect_cache[agent_id] = effects.GetEffects()

    @classmethod
    def _reset_cache(cls, agent_id = None):
        """Clear one or all agents from the cache."""
        if agent_id is None:
            cls._buff_cache.clear()
            cls._effect_cache.clear()
        else:
            cls._buff_cache.pop(agent_id, None)
            cls._effect_cache.pop(agent_id, None)

    @classmethod
    def DropBuff(cls, buff_id: int):
        from ..Player import Player
        _action_queue_manager:ActionQueueManager = ActionQueueManager()
        agent_id = Player.GetAgentID()
        effect_instance = PyEffects.PyEffects(agent_id)

        def drop_and_update():
            effect_instance.DropBuff(buff_id)
            cls._update_or_insert(agent_id)

        _action_queue_manager.AddAction("ACTION", drop_and_update)

    @classmethod
    def GetBuffs(cls, agent_id: int):
        cls._update_or_insert(agent_id)
        return cls._buff_cache[agent_id]

    @classmethod
    def GetEffects(cls, agent_id: int):
        cls._update_or_insert(agent_id)
        return cls._effect_cache[agent_id]

    @classmethod
    def GetBuffCount(cls, agent_id: int):
        return len(cls.GetBuffs(agent_id))

    @classmethod
    def GetEffectCount(cls, agent_id: int):
        return len(cls.GetEffects(agent_id))

    @classmethod
    def BuffExists(cls, agent_id: int, skill_id: int):
        return any(buff.skill_id == skill_id for buff in cls.GetBuffs(agent_id))

    @classmethod
    def EffectExists(cls, agent_id: int, skill_id: int):
        return any(effect.skill_id == skill_id for effect in cls.GetEffects(agent_id))
    
    @classmethod
    def HasEffect(cls,agent_id: int, skill_id: int):
        return cls.EffectExists(agent_id, skill_id) or cls.BuffExists(agent_id, skill_id)

    @classmethod
    def EffectAttributeLevel(cls, agent_id: int, skill_id: int):
        for effect in cls.GetEffects(agent_id):
            if effect.skill_id == skill_id:
                return effect.attribute_level
        return 0

    @classmethod
    def GetEffectTimeRemaining(cls, agent_id: int, skill_id: int):
        for effect in cls.GetEffects(agent_id):
            if effect.skill_id == skill_id:
                return effect.time_remaining
        return 0

    @classmethod
    def GetBuffID(cls, skill_id: int) -> int:
        from ..Player import Player
        agent_id = Player.GetAgentID()
        for buff in cls.GetBuffs(agent_id):
            if buff.skill_id == skill_id:
                return buff.buff_id
        return 0