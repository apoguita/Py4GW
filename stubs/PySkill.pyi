from typing import List, overload
from PyMap import Campaign
from PyAgent import Profession, AttributeClass

class SkillID:
    id: int

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, skillid: int) -> None: ...
    @overload
    def __init__(self, skillname: str) -> None: ...
    def GetName(self) -> str: ...


class SkillType:
    id: int

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, skilltype: int) -> None: ...
    def GetName(self) -> str: ...

class Skill:
    id: SkillID
    campaign: Campaign
    type: SkillType
    special: int
    combo_req: int
    effect1: int
    condition: int
    effect2: int
    weapon_req: int
    profession: Profession
    attribute: AttributeClass
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
    duration_0pts: int
    duration_15pts: int
    recharge: int
    skill_arguments: int
    scale_0pts: int
    scale_15pts: int
    bonus_scale_0pts: int
    bonus_scale_15pts: int
    aoe_range: float
    const_effect: float
    caster_overhead_animation_id: int
    caster_body_animation_id: int
    target_body_animation_id: int
    target_overhead_animation_id: int
    projectile_animation1_id: int
    projectile_animation2_id: int
    icon_file_hi_res_id: int
    icon_file_id: int
    icon_file2_id: int
    name_id: int
    concise: int
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
    recharge2: int
    h0004: int
    h0032: int
    h0037: int

    @overload
    def __init__(self) -> None: ...
    @overload
    def __init__(self, skillid: int) -> None: ...
    @overload
    def __init__(self, skillname: str) -> None: ...
    def GetContext(self) -> None: ...