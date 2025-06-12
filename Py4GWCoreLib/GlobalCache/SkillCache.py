import PySkill
from typing import Dict
from ..enums import SkillTextureMap

class SkillCache:
    def __init__(self):
        self.skill_cache: Dict[int, PySkill.Skill] = {}
        self.Data = self._Data(self)
        self.Attribute = self._Attribute(self)
        self.Flags = self._Flags(self)
        self.Animations = self._Animations(self)
        self.ExtraData = self._ExtraData(self)

    def _get_skill_instance(self, skill_id: int) -> PySkill.Skill:
        if skill_id in self.skill_cache:
            return self.skill_cache[skill_id]

        skill = PySkill.Skill(skill_id)
        if skill.id.id != 0:  # invalid = 0
            self.skill_cache[skill_id] = skill
            return skill

        return PySkill.Skill(0)
    
    def GetName(self, skill_id: int) -> str:
        skill = self._get_skill_instance(skill_id)
        if skill.id.id == 0:
            return ""
        return skill.id.GetName()
        
    def GetID(self, skill_name: str) -> int:
        skill = PySkill.Skill(skill_name)
        cached_skill = self._get_skill_instance(skill.id.id)
        return cached_skill.id.id
        
    def GetType(self, skill_id):
        skill = self._get_skill_instance(skill_id)
        return skill.type.id, skill.type.GetName()
    
    def GetCampaign(self, skill_id):
        skill = self._get_skill_instance(skill_id)
        return skill.campaign.ToInt(), skill.campaign.GetName()
    
    def GetProfession(self, skill_id):
        skill = self._get_skill_instance(skill_id)
        if skill is None:
            return 0, ""
        return skill.profession.ToInt(), skill.profession.GetName()
    
    class _Data:
        def __init__(self, parent):
            self._parent = parent
            
        def _get_skill_instance(self, skill_id) -> PySkill.Skill:
            return self._parent._get_skill_instance(skill_id)
            
        def GetCombo(self, skill_id) -> int:
            skill = self._get_skill_instance(skill_id)
            return skill.combo
    
        def GetComboReq(self, skill_id) -> int:
            skill = self._get_skill_instance(skill_id)
            return skill.combo_req
        
        def GetWeaponReq(self, skill_id) -> int:
            skill = self._get_skill_instance(skill_id)
            return skill.weapon_req
        
        def GetOvercast(self, skill_id) -> int:
            skill = self._get_skill_instance(skill_id)
            return skill.overcast
        
        def GetEnergyCost(self, skill_id) -> int:
            skill = self._get_skill_instance(skill_id)
            cost = skill.energy_cost
            if cost == 11:
                return 15
            elif cost == 12:
                return 25
            return cost
        
        def GetHealthCost(self, skill_id) -> int:
            skill = self._get_skill_instance(skill_id)
            return skill.health_cost

        def GetAdrenaline(self, skill_id) -> int:
            skill = self._get_skill_instance(skill_id)
            return skill.adrenaline
        
        def GetActivation(self, skill_id) -> float:
            skill = self._get_skill_instance(skill_id)
            return skill.activation
        
        def GetAftercast(self, skill_id) -> float:
            skill = self._get_skill_instance(skill_id)
            return skill.aftercast
        
        def GetRecharge(self, skill_id) -> int:
            skill = self._get_skill_instance(skill_id)
            return skill.recharge
        
        def GetRecharge2(self, skill_id) -> int:
            skill = self._get_skill_instance(skill_id)
            return skill.recharge2
        
        def GetAoERange(self, skill_id) -> float:
            skill = self._get_skill_instance(skill_id)
            return skill.aoe_range
        
        def GetAdrenalineA(self, skill_id) -> int:
            skill = self._get_skill_instance(skill_id)
            return skill.adrenaline_a
        
        def GetAdrenalineB(self, skill_id) -> int:
            skill = self._get_skill_instance(skill_id)
            return skill.adrenaline_b
        
    class _Attribute:
        def __init__(self, parent):
            self._parent = parent
            
        def _get_skill_instance(self, skill_id) -> PySkill.Skill:
            return self._parent._get_skill_instance(skill_id)
            
        def GetAttribute(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.attribute
        
        def GetScale(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.scale_0pts, skill.scale_15pts
        
        def GetBonusScale(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.bonus_scale_0pts, skill.bonus_scale_15pts
        
        def GetDuration(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.duration_0pts, skill.duration_15pts
        
    class _Flags:
        def __init__(self, parent):
            self._parent = parent
            
        def _get_skill_instance(self, skill_id) -> PySkill.Skill:
            return self._parent._get_skill_instance(skill_id)
            
        def IsTouchRange(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.is_touch_range
        
        def IsElite(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.is_elite
        
        def IsHalfRange(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.is_half_range
        
        def IsPvP(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.is_pvp
        
        def IsPvE(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.is_pve
        
        def IsPlayable(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.is_playable
        
        def IsStacking(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.is_stacking
        
        def IsNonStacking(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.is_non_stacking
        
        def IsUnused(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.is_unused
        
        def IsHex(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Hex"
            
        def IsBounty(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Bounty"
        
        def IsScroll(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Scroll"
        
        def IsStance(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Stance"
        
        def IsSpell(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Spell"
        
        def IsEnchantment(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Enchantment"
        
        def IsSignet(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Signet"
        
        def IsCondition(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Condition"
        
        def IsWell(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Well"
        
        def IsSkill(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Skill"
        
        def IsWard(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Ward"
        
        def IsGlyph(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Glyph"
        
        def IsTitle(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Title"
        
        def IsAttack(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Attack"
        
        def IsShout(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Shout"
        
        def IsSkill2(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Skill2"
        
        def IsPassive(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Passive"
        
        def IsEnvironmental(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Environmental"
        
        def IsPreparation(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Preparation"
        
        def IsPetAttack(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "PetAttack"
        
        def IsTrap(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Trap"
        
        def IsRitual(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Ritual"
        
        def IsEnvironmentalTrap(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "EnvironmentalTrap"
        
        def IsItemSpell(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "ItemSpell"
        
        def IsWeaponSpell(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "WeaponSpell"
        
        def IsForm(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Form"
        
        def IsChant(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Chant"
        
        def IsEchoRefrain(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "EchoRefrain"
        
        def IsDisguise(self, skill_id) -> bool:
            skill = self._get_skill_instance(skill_id)
            return skill.type.GetName() == "Disguise"
        
    class _Animations:
        def __init__(self, parent):
            self._parent = parent
            
        def _get_skill_instance(self, skill_id) -> PySkill.Skill:
            return self._parent._get_skill_instance(skill_id)
            
        def GetEffects(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.effect1, skill.effect2
        
        def GetSpecial(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.special
        
        def GetConstEffect(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.const_effect
        
        def GetCasterOverheadAnimationID(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.caster_overhead_animation_id
        
        def GetCasterBodyAnimationID(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.caster_body_animation_id
        
        def GetTargetBodyAnimationID(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.target_body_animation_id
        
        def GetTargetOverheadAnimationID(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.target_overhead_animation_id
        
        def GetProjectileAnimationID(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.projectile_animation1_id, skill.projectile_animation2_id
        
        def GetIconFileID(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.icon_file_id, skill.icon_file2_id
        
    class _ExtraData:
        def __init__(self, parent):
            self._parent = parent
            
        def _get_skill_instance(self, skill_id) -> PySkill.Skill:
            return self._parent._get_skill_instance(skill_id)
            
        def GetCondition(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.condition
        
        def GetTitle(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.title
        
        def GetIDPvP(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.id_pvp
        
        def GetTarget(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.target
        
        def GetSkillEquipType(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.skill_equip_type
        
        def GetSkillArguments(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.skill_arguments
        
        def GetNameID(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.name_id
        
        def GetConcise(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.concise
        
        def GetDescriptionID(self, skill_id):
            skill = self._get_skill_instance(skill_id)
            return skill.description_id

        def GetTexturePath(self,skill_id: int) -> str:
            filename = SkillTextureMap.get(skill_id)
            full_path = f"Textures\\Skill_Icons\\{filename}" if filename else ""
            return full_path


        
        
        