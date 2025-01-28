# PyParty.pyi - Auto-generated .pyi file for PyParty module

from typing import List, Any

# Enum HeroType
class HeroType:
    None: int
    Norgu: int
    Goren: int
    Tahlkora: int
    MasterOfWhispers: int
    AcolyteJin: int
    Koss: int
    Dunkoro: int
    AcolyteSousuke: int
    Melonni: int
    ZhedShadowhoof: int
    GeneralMorgahn: int
    MagridTheSly: int
    Zenmai: int
    Olias: int
    Razah: int
    MOX: int
    KeiranThackeray: int
    Jora: int
    PyreFierceshot: int
    Anton: int
    Livia: int
    Hayda: int
    Kahmu: int
    Gwen: int
    Xandra: int
    Vekk: int
    Ogden: int
    MercenaryHero1: int
    MercenaryHero2: int
    MercenaryHero3: int
    MercenaryHero4: int
    MercenaryHero5: int
    MercenaryHero6: int
    MercenaryHero7: int
    MercenaryHero8: int
    Miku: int
    ZeiRi: int
	
#class PetInfo
class PetInfo :
    agent_id: int
    owner_agent_id : int
    pet_name : str
    model_file_id1 : int
    model_file_id2 : int
    behavior : int
    locked_target_id : int

    def __init__(self, owner_agent_id: int = 0)->None : ...
	
# Class Hero
class Hero:
    def __init__(self, hero_id: int) -> None: ...
	def __init__(self, hero_name: str) -> None: ...
    
    def GetId(self) -> int: ...
    def GetName(self) -> str: ...
    def GetProfession(self) -> int: ...
    
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...

# Class PartyTick
class PartyTick:
    def __init__(self, ticked: bool) -> None: ...
    
    def IsTicked(self) -> bool: ...
    def SetTicked(self, ticked: bool) -> None: ...
    def ToggleTicked(self) -> None: ...
    def SetTickToggle(self, toggle: bool) -> None: ...

# Class PlayerPartyMember
class PlayerPartyMember:
    login_number: int
    called_target_id: int
    is_connected: bool
    is_ticked: bool
    
    def __init__(self, login_number: int, called_target_id: int, is_connected: bool, is_ticked: bool) -> None: ...

# Class HeroPartyMember
class HeroPartyMember:
    agent_id: int
    owner_player_id: int
    hero_id: int
    level: int
    primary: int
    secondary: int
    
    def __init__(self, agent_id: int, owner_player_id: int, hero_id: int, level: int) -> None: ...

# Class HenchmanPartyMember
class HenchmanPartyMember:
    agent_id: int
    profession: int
    level: int
    
    def __init__(self, agent_id: int, profession: int, level: int) -> None: ...

# Class PyParty
class PyParty:
    party_id: int
    players: List[PlayerPartyMember]
    heroes: List[HeroPartyMember]
    henchmen: List[HenchmanPartyMember]
    is_in_hard_mode: bool
    is_hard_mode_unlocked: bool
    party_size: int
    party_player_count: int
    party_hero_count: int
    party_henchman_count: int
    is_party_defeated: bool
    is_party_loaded: bool
    is_party_leader: bool
    tick: PartyTick
    
    def __init__(self) -> None: ...
    
    def GetContext(self) -> None: ...
    def ReturnToOutpost(self) -> None: ...
    def SetHardMode(self, flag: bool) -> None: ...
    def RespondToPartyRequest(self, party_id: int, accept: bool) -> None: ...
    def AddHero(self, hero_id: int) -> None: ...
    def KickHero(self, hero_id: int) -> None: ...
    def KickAllHeroes(self) -> None: ...
    def AddHenchman(self, henchman_id: int) -> None: ...
    def KickHenchman(self, henchman_id: int) -> None: ...
    def KickPlayer(self, player_id: int) -> None: ...
    def InvitePlayer(self, player_id: int) -> None: ...
    def LeaveParty(self) -> None: ...
    def FlagHero(self, agent_id: int, x: float, y: float) -> None: ...
    def FlagAllHeroes(self, x: float, y: float) -> None: ...
    def UnflagHero(self, agent_id: int) -> None: ...
    def GetHeroAgentID(self, hero_index: int) -> int: ...
    def GetAgentHeroID(self, agent_id: int) -> int: ...
    def SearchParty(self, search_type: int, advertisement: str) -> None: ...
    def SearchPartyCancel(self) -> None: ...
    def SearchPartyReply(self, accept: bool) -> None: ...
	def GetAgentByPlayerID(self, accept: int) -> Int: ...
	def GetPlayerNameByLoginNumber(self, accept: int) -> str: ...
	def GetPetInfo(self, accept: int) -> PetInfo: ...
	def SetHeroBehavior(agent_id,behavior) -> None ...
	def SetPetBehavior (self,behavior, lock_target_id) -> None ...
	def GetIsPlayerTicked (self, player_id) -> None: ...

class EffectType:
    skill_id: int
    attribute_level: int
    effect_id: int
    agent_id: int
    duration: float
    timestamp: int
    time_elapsed: int
    time_remaining: int

    def __init__(self, skill_id: int, attribute_level: int, effect_id: int, agent_id: int, duration: float, 
                 timestamp: int, time_elapsed: int, time_remaining: int) -> None:
        """
        Constructor for the EffectType class.

        Args:
            skill_id (int): The ID of the skill associated with the effect.
            attribute_level (int): The attribute level of the effect.
            effect_id (int): The ID of the effect.
            agent_id (int): The ID of the agent.
            duration (float): The duration of the effect.
            timestamp (int): The timestamp of when the effect was applied.
            time_elapsed (int): Time elapsed since the effect was applied.
            time_remaining (int): Time remaining for the effect.
        """
        ...

class BuffType:
    skill_id: int
    buff_id: int
    target_agent_id: int

    def __init__(self, skill_id: int, buff_id: int, target_agent_id: int) -> None:
        """
        Constructor for the BuffType class.

        Args:
            skill_id (int): The ID of the skill associated with the buff.
            buff_id (int): The ID of the buff.
            target_agent_id (int): The ID of the target agent for the buff.
        """
        ...

class AgentEffects:
    def __init__(self, agent_id: int) -> None:
        """
        Constructor for the AgentEffects class, which initializes effects and buffs for a given agent.

        Args:
            agent_id (int): The ID of the agent to fetch effects and buffs for.
        """
        ...

    def GetEffects(self) -> List[EffectType]:
        """
        Get a list of effects for the agent.

        Returns:
            List[EffectType]: A list of EffectType objects representing the effects applied to the agent.
        """
        ...

    def GetBuffs(self) -> List[BuffType]:
        """
        Get a list of buffs for the agent.

        Returns:
            List[BuffType]: A list of BuffType objects representing the buffs applied to the agent.
        """
        ...

    def GetEffectCount(self) -> int:
        """
        Get the number of effects for the agent.

        Returns:
            int: The number of effects applied to the agent.
        """
        ...

    def GetBuffCount(self) -> int:
        """
        Get the number of buffs for the agent.

        Returns:
            int: The number of buffs applied to the agent.
        """
        ...

    def EffectExists(self, skill_id: int) -> bool:
        """
        Check if a specific effect exists for the agent.

        Args:
            skill_id (int): The skill ID of the effect to check.

        Returns:
            bool: True if the effect exists, False otherwise.
        """
        ...

    def BuffExists(self, skill_id: int) -> bool:
        """
        Check if a specific buff exists for the agent.

        Args:
            skill_id (int): The skill ID of the buff to check.

        Returns:
            bool: True if the buff exists, False otherwise.
        """
        ...
