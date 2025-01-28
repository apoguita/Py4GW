from typing import List


class EffectType:
    skill_id: int
    attribute_level: int
    effect_id: int
    agent_id: int
    duration: float
    timestamp: int  # DWORD as int
    time_elapsed: int  # DWORD as int
    time_remaining: int  # DWORD as int

    def __init__(self, 
                 skill_id: int, 
                 attribute_level: int, 
                 effect_id: int, 
                 agent_id: int, 
                 duration: float, 
                 timestamp: int, 
                 time_elapsed: int, 
                 time_remaining: int) -> None: ...
    

class BuffType:
    skill_id: int
    buff_id: int
    target_agent_id: int

    def __init__(self, 
                 skill_id: int, 
                 buff_id: int, 
                 target_agent_id: int) -> None: ...
    

class AgentEffects:
    agent_id: int
    Effects_list: List[EffectType]
    Buffs_list: List[BuffType]

    def __init__(self, agent_id: int) -> None: ...

    def GetEffects(self) -> List[EffectType]: ...
    def GetBuffs(self) -> List[BuffType]: ...
    def GetEffectCount(self) -> int: ...
    def GetBuffCount(self) -> int: ...
    def EffectExists(self, skill_id: int) -> bool: ...
    def BuffExists(self, skill_id: int) -> bool: ...
    def DropBuff(self, skill_id: int) -> None: ...
