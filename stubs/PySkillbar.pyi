# PySkill.pyi - Auto-generated .pyi file for PySkill module

from typing import List, Any

# Class SkillID
class SkillID:
    id: int

    def __init__(self, skill_id: int) -> None: ...
    def __init__(self) -> None: ...
    
    def GetName(self) -> str: ...
    
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...

# Class SkillType
class SkillType:
    id: int

    def __init__(self, skill_type: int) -> None: ...
    def __init__(self) -> None: ...
    
    def GetName(self) -> str: ...
    
    def __eq__(self, other: Any) -> bool: ...
    def __ne__(self, other: Any) -> bool: ...

# Class Skill
class Skill:
    id: int
    campaign: int
    type: 'SkillType'
    special: int
    combo_req: int
    effect1: int
    condition: int
    effect2: int
    weapon_req: int
    profession: int
    attribute: int
    title: int
    id_pvp: int
    combo: int
    target: int
    skill_equip_type: int
    overcast: int
    energy_cost: int
    health_cost: int
    adrenaline: int
    activation: float
    aftercast: float
    duration_0pts: float
    duration_15pts: float
    recharge: float
    skill_arguments: List[Any]
    scale_0pts: float
    scale_15pts: float
    bonus_scale_0pts: float
    bonus_scale_15pts: float
    aoe_range: float
    const_effect: int
    caster_overhead_animation_id: int
    caster_body_animation_id: int
    target_body_animation_id: int
    target_overhead_animation_id: int
    projectile_animation1_id: int
    projectile_animation2_id: int
    icon_file_id: int
    icon_file2_id: int
    name_id: int
    concise: str
    description_id: int
    is_touch_range: bool
    is_elite: bool
    is_half_range: bool
    is_pvp: bool
    is_pve: bool
    is_playable: bool
    is_stacking: bool
    is_non_stacking: bool
    is_unused: bool
    adrenaline_a: int
    adrenaline_b: int
    recharge: float

    def __init__(self) -> None: ...
    def __init__(self, skill_id: int) -> None: ...
    
    def GetContext(self) -> None: ...

# PySkillbar.pyi - Auto-generated .pyi file for PySkillbar module

# Class SkillbarSkill
class SkillbarSkill:
    id: 'SkillID'
    adrenaline_a: int
    adrenaline_b: int
    recharge: int
    event: int

    def __init__(self, id: 'SkillID', adrenaline_a: int = 0, adrenaline_b: int = 0, recharge: int = 0, event: int = 0) -> None: ...

# Class Skillbar
class Skillbar:
    skills: List['SkillbarSkill']

    def __init__(self) -> None: ...
    
    def GetContext(self) -> None: ...
    def GetSkill(self, slot: int) -> 'SkillbarSkill': ...
    def LoadSkillTemplate(self, skill_template: str) -> bool: ...
	def LoadHeroSkillTemplate(self, hero_index:int, skill_template: str) -> bool: ...
    def UseSkill(self, slot: int, target: int) -> None: ...
	def HeroUseSkill(self, target_agent_id: int, skill_idx : int) -> bool: ...
	def ChangeHeroSecondary(self, hero_index:int, profession:int) -> bool: ...
	def GetHeroSkillbar(her_index:int) -> List['SkillbarSkill']: ...
	def GetHoveredSkill(self) -> int: ...
	def IsSkillUnlocked(self) -> bool: ...