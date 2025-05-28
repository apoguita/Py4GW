# PyAgent.pyi - Auto-generated .pyi file for PyAgent module

from typing import List, Tuple

# Enum ProfessionType
class ProfessionType:
    NoProfession: int
    Warrior: int
    Ranger: int
    Monk: int
    Necromancer: int
    Mesmer: int
    Elementalist: int
    Assassin: int
    Ritualist: int
    Paragon: int
    Dervish: int

# Class Profession
class Profession:
    def __init__(self, prof: int | str) -> None: ...
    def Set(self, prof: int) -> None: ...
    def Get(self) -> int: ...
    def ToInt(self) -> int: ...
    def GetName(self) -> str: ...
    def GetShortName(self) -> str: ...

# Enum AllegianceType
class AllegianceType:
    Unknown: int
    Ally: int
    Neutral: int
    Enemy: int
    SpiritPet: int
    Minion: int
    NpcMinipet: int

# Class Allegiance
class Allegiance:
    def __init__(self, value: int) -> None: ...
    def Set(self, value: int) -> None: ...
    def Get(self) -> int: ...
    def ToInt(self) -> int: ...
    def GetName(self) -> str: ...

# Enum PyWeaponType
class PyWeaponType:
    Unknown: int
    Bow: int
    Axe: int
    Hammer: int
    Daggers: int
    Scythe: int
    Spear: int
    Sword: int
    Scepter: int
    Scepter2: int
    Wand: int
    Staff1: int
    Staff: int
    Staff2: int
    Staff3: int
    Unknown1: int
    Unknown2: int
    Unknown3: int
    Unknown4: int
    Unknown5: int
    Unknown6: int
    Unknown7: int
    Unknown8: int
    Unknown9: int
    Unknown10: int

# Class Weapon
class Weapon:
    def __init__(self, value: int) -> None: ...
    def Set(self, value: int) -> None: ...
    def Get(self) -> int: ...
    def ToInt(self) -> int: ...
    def GetName(self) -> str: ...

# Enum SafeAttribute
class SafeAttribute:
    FastCasting: int
    IllusionMagic: int
    DominationMagic: int
    InspirationMagic: int
    BloodMagic: int
    DeathMagic: int
    SoulReaping: int
    Curses: int
    AirMagic: int
    EarthMagic: int
    FireMagic: int
    WaterMagic: int
    EnergyStorage: int
    HealingPrayers: int
    SmitingPrayers: int
    ProtectionPrayers: int
    DivineFavor: int
    Strength: int
    AxeMastery: int
    HammerMastery: int
    Swordsmanship: int
    Tactics: int
    BeastMastery: int
    Expertise: int
    WildernessSurvival: int
    Marksmanship: int
    DaggerMastery: int
    DeadlyArts: int
    ShadowArts: int
    Communing: int
    RestorationMagic: int
    ChannelingMagic: int
    CriticalStrikes: int
    SpawningPower: int
    SpearMastery: int
    Command: int
    Motivation: int
    Leadership: int
    ScytheMastery: int
    WindPrayers: int
    EarthPrayers: int
    Mysticism: int
    NoAttribute: int

# Class AttributeClass
class AttributeClass:
    attribute_id: int
    level_base: int
    level: int
    decrement_points: int
    increment_points: int

    def __init__(self, attr_id: int | str, lvl_base: int = 0, lvl: int = 0, dec_points: int = 0, inc_points: int = 0) -> None: ...
    def GetName(self) -> str: ...

# Class PyLivingAgent
class PyLivingAgent:
    agent_id: int
    owner_id: int
    player_number: int
    profession: Profession
    secondary_profession: Profession
    level: int
    energy: float
    max_energy: float
    energy_regen: float
    hp: float
    max_hp: float
    hp_regen: float
    login_number: int
    name: str
    dagger_status: int
    allegiance: Allegiance
    weapon_type: Weapon
    weapon_item_type: int
    offhand_item_type: int
    weapon_item_id: int
    offhand_item_id: int
    is_bleeding: bool
    is_conditioned: bool
    is_crippled: bool
    is_dead: bool
    is_deep_wounded: bool
    is_poisoned: bool
    is_enchanted: bool
    is_degen_hexed: bool
    is_hexed: bool
    is_weapon_spelled: bool
    in_combat_stance: bool
    has_quest: bool
    is_dead_by_typemap: bool
    is_female: bool
    has_boss_glow: bool
    is_hiding_cape: bool
    can_be_viewed_in_party_window: bool
    is_spawned: bool
    is_being_observed: bool
    is_knocked_down: bool
    is_moving: bool
    is_attacking: bool
    is_casting: bool
    is_idle: bool
    is_alive: bool
    is_player: bool
    is_npc: bool
    casting_skill_id: int
    overcast: float
    
    #h00C8 : int
    #h00CC: int
    #h00D0: int
    #h00D4: list[int]
    animation_type: float
    #h00E4: list[int]
    weapon_attack_speed: float
    attack_speed_modifier: float
    agent_model_type: int
    transmog_npc_id: int
    #h0100: int
    guild_id: int
    team_id: int
    #h0108: int
    #h010E: list[int]
    #h0110: int
    #h0124: int
    #h012C: int
    effects: int
    #h013C: int
    #h0141: list[int]
    model_state: int
    type_map: int
    #h015C: list[int]
    #h017C: int
    animation_speed: float
    animation_code: int
    animation_id: int
    #h0190: list[int]
    #h01B6: int

    def __init__(self, agent_id: int) -> None: ...
    def GetContext(self) -> None: ...
    def RequestName(self) -> None: ...
    def IsAgentNameReady(self) -> bool: ...
    def GetName(self) -> str: ...

# Class PyItemAgent
class PyItemAgent:
    agent_id: int
    owner_id: int
    item_id: int
    h00CC: int
    extra_type: int

    def __init__(self, agent_id: int) -> None: ...
    def GetContext(self) -> None: ...

# Class PyGadgetAgent
class PyGadgetAgent:
    agent_id: int
    h00C4: int
    h00C8: int
    extra_type: int
    gadget_id: int
    h00D4: List[int]

    def __init__(self, agent_id: int) -> None: ...
    def GetContext(self) -> None: ...

# Class PyAgent
class PyAgent:
    id: int
    x: float
    y: float
    z: float
    zplane: int
    rotation_angle: float
    rotation_cos: float
    rotation_sin: float
    velocity_x: float
    velocity_y: float
    is_living: bool
    is_item: bool
    is_gadget: bool
    living_agent: PyLivingAgent
    item_agent: PyItemAgent
    gadget_agent: PyGadgetAgent
    attributes: List[AttributeClass]
    
    #h0004: int
    #h0008: int
    #h000C: list[int]
    instance_timer_in_frames: int
    instance_timer: int
    timer2: int
    model_width1: float
    model_width2: float
    model_width3: float
    model_height1: float
    model_height2: float
    model_height3: float
    name_properties: int
    ground: int
    #h0060: int
    terrain_normal: list[int]
    #h0070: list[int]
    name_tag_x: float
    name_tag_y: float
    name_tag_z: float
    visual_effects: int
    #h0092: int
    #h0094: list[int]
    #_type: int
    #h00B4: list[int]
    #rand1: int
    #rand2: int

    def __init__(self, agent_id: int) -> None: ...
    def Set(self, agent_id: int) -> None: ...
    def GetContext(self) -> None: ...
    def IsValid(self, agent_id: int) -> bool: ...
    
    @staticmethod
    def GetRawAgentArray() -> List[PyAgent]: ...
    @staticmethod
    def GetMovementStuckArray() -> List[Tuple[int, int]]: ...