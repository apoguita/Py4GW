local Skill = {}

function Skill.skill_instance(skill_id)
    return PySkill.Skill(skill_id)
end

function Skill.GetName(skill_id)
    return Skill.skill_instance(skill_id).id:GetName()
end

function Skill.GetID(skill_name)
    return Skill.skill_instance(skill_name).id:id()
end

function Skill.GetType(skill_id)
    return Skill.skill_instance(skill_id).type:id(), Skill.skill_instance(skill_id).type:GetName()
end

function Skill.GetCampaign(skill_id)
    return Skill.skill_instance(skill_id).campaign:ToInt(), Skill.skill_instance(skill_id).campaign:GetName()
end

function Skill.GetProfession(skill_id)
    return Skill.skill_instance(skill_id).profession:ToInt(), Skill.skill_instance(skill_id).profession:GetName()
end

Skill.Data = {}
function Skill.Data.GetCombo(skill_id)
    return Skill.skill_instance(skill_id).combo
end

function Skill.Data.GetComboReq(skill_id)
    return Skill.skill_instance(skill_id).combo_req
end

function Skill.Data.GetWeaponReq(skill_id)
    return Skill.skill_instance(skill_id).weapon_req
end

function Skill.Data.GetOvercast(skill_id)
    return Skill.skill_instance(skill_id).overcast
end

function Skill.Data.GetEnergyCost(skill_id)
    local cost = Skill.skill_instance(skill_id).energy_cost
    if cost == 11 then
        return 15
    elseif cost == 12 then
        return 25
    end
    return cost
end

function Skill.Data.GetHealthCost(skill_id)
    return Skill.skill_instance(skill_id).health_cost
end

function Skill.Data.GetAdrenaline(skill_id)
    return Skill.skill_instance(skill_id).adrenaline
end

function Skill.Data.GetActivation(skill_id)
    return Skill.skill_instance(skill_id).activation
end

function Skill.Data.GetAftercast(skill_id)
    return Skill.skill_instance(skill_id).aftercast
end

function Skill.Data.GetRecharge(skill_id)
    return Skill.skill_instance(skill_id).recharge
end

function Skill.Data.GetRecharge2(skill_id)
    return Skill.skill_instance(skill_id).recharge2
end

function Skill.Data.GetAoERange(skill_id)
    return Skill.skill_instance(skill_id).aoe_range
end

function Skill.Data.GetAdrenalineA(skill_id)
    return Skill.skill_instance(skill_id).adrenaline_a
end

function Skill.Data.GetAdrenalineB(skill_id)
    return Skill.skill_instance(skill_id).adrenaline_b
end

Skill.Attribute = {}
function Skill.Attribute.GetAttribute(skill_id)
    return Skill.skill_instance(skill_id).attribute
end

function Skill.Attribute.GetScale(skill_id)
    return Skill.skill_instance(skill_id).scale_0pts, Skill.skill_instance(skill_id).scale_15pts
end

function Skill.Attribute.GetBonusScale(skill_id)
    return Skill.skill_instance(skill_id).bonus_scale_0pts, Skill.skill_instance(skill_id).bonus_scale_15pts
end

function Skill.Attribute.GetDuration(skill_id)
    return Skill.skill_instance(skill_id).duration_0pts, Skill.skill_instance(skill_id).duration_15pts
end

Skill.Flags = {}
function Skill.Flags.IsTouchRange(skill_id)
    return Skill.skill_instance(skill_id).is_touch_range
end

function Skill.Flags.IsElite(skill_id)
    return Skill.skill_instance(skill_id).is_elite
end

function Skill.Flags.IsHalfRange(skill_id)
    return Skill.skill_instance(skill_id).is_half_range
end

function Skill.Flags.IsPvP(skill_id)
    return Skill.skill_instance(skill_id).is_pvp
end

function Skill.Flags.IsPvE(skill_id)
    return Skill.skill_instance(skill_id).is_pve
end

function Skill.Flags.IsPlayable(skill_id)
    return Skill.skill_instance(skill_id).is_playable
end

function Skill.Flags.IsStacking(skill_id)
    return Skill.skill_instance(skill_id).is_stacking
end

function Skill.Flags.IsNonStacking(skill_id)
    return Skill.skill_instance(skill_id).is_non_stacking
end

function Skill.Flags.IsUnused(skill_id)
    return Skill.skill_instance(skill_id).is_unused
end

function Skill.Flags.IsHex(skill_id)
    return Skill.GetType(skill_id)[2] == "Hex"
end

function Skill.Flags.IsBounty(skill_id)
    return Skill.GetType(skill_id)[2] == "Bounty"
end

function Skill.Flags.IsScroll(skill_id)
    return Skill.GetType(skill_id)[2] == "Scroll"
end

function Skill.Flags.IsStance(skill_id)
    return Skill.GetType(skill_id)[2] == "Stance"
end

function Skill.Flags.IsSpell(skill_id)
    return Skill.GetType(skill_id)[2] == "Spell"
end

function Skill.Flags.IsEnchantment(skill_id)
    return Skill.GetType(skill_id)[2] == "Enchantment"
end

function Skill.Flags.IsSignet(skill_id)
    return Skill.GetType(skill_id)[2] == "Signet"
end

function Skill.Flags.IsCondition(skill_id)
    return Skill.GetType(skill_id)[2] == "Condition"
end

function Skill.Flags.IsWell(skill_id)
    return Skill.GetType(skill_id)[2] == "Well"
end

function Skill.Flags.IsSkill(skill_id)
    return Skill.GetType(skill_id)[2] == "Skill"
end

function Skill.Flags.IsWard(skill_id)
    return Skill.GetType(skill_id)[2] == "Ward"
end

function Skill.Flags.IsGlyph(skill_id)
    return Skill.GetType(skill_id)[2] == "Glyph"
end

function Skill.Flags.IsTitle(skill_id)
    return Skill.GetType(skill_id)[2] == "Title"
end

function Skill.Flags.IsAttack(skill_id)
    return Skill.GetType(skill_id)[2] == "Attack"
end

function Skill.Flags.IsShout(skill_id)
    return Skill.GetType(skill_id)[2] == "Shout"
end

function Skill.Flags.IsSkill2(skill_id)
    return Skill.GetType(skill_id)[2] == "Skill2"
end

function Skill.Flags.IsPassive(skill_id)
    return Skill.GetType(skill_id)[2] == "Passive"
end

function Skill.Flags.IsEnvironmental(skill_id)
    return Skill.GetType(skill_id)[2] == "Environmental"
end

function Skill.Flags.IsPreparation(skill_id)
    return Skill.GetType(skill_id)[2] == "Preparation"
end

function Skill.Flags.IsPetAttack(skill_id)
    return Skill.GetType(skill_id)[2] == "PetAttack"
end

function Skill.Flags.IsTrap(skill_id)
    return Skill.GetType(skill_id)[2] == "Trap"
end

function Skill.Flags.IsRitual(skill_id)
    return Skill.GetType(skill_id)[2] == "Ritual"
end

function Skill.Flags.IsEnvironmentalTrap(skill_id)
    return Skill.GetType(skill_id)[2] == "EnvironmentalTrap"
end

function Skill.Flags.IsItemSpell(skill_id)
    return Skill.GetType(skill_id)[2] == "ItemSpell"
end

function Skill.Flags.IsWeaponSpell(skill_id)
    return Skill.GetType(skill_id)[2] == "WeaponSpell"
end

function Skill.Flags.IsForm(skill_id)
    return Skill.GetType(skill_id)[2] == "Form"
end

function Skill.Flags.IsChant(skill_id)
    return Skill.GetType(skill_id)[2] == "Chant"
end

function Skill.Flags.IsEchoRefrain(skill_id)
    return Skill.GetType(skill_id)[2] == "EchoRefrain"
end

function Skill.Flags.IsDisguise(skill_id)
    return Skill.GetType(skill_id)[2] == "Disguise"
end

Skill.Animations = {}
function Skill.Animations.GetEffects(skill_id)
    return Skill.skill_instance(skill_id).effect1, Skill.skill_instance(skill_id).effect2
end

function Skill.Animations.GetSpecial(skill_id)
    return Skill.skill_instance(skill_id).special
end

function Skill.Animations.GetConstEffect(skill_id)
    return Skill.skill_instance(skill_id).const_effect
end

function Skill.Animations.GetCasterOverheadAnimationID(skill_id)
    return Skill.skill_instance(skill_id).caster_overhead_animation_id
end

function Skill.Animations.GetCasterBodyAnimationID(skill_id)
    return Skill.skill_instance(skill_id).caster_body_animation_id
end

function Skill.Animations.GetTargetBodyAnimationID(skill_id)
    return Skill.skill_instance(skill_id).target_body_animation_id
end

function Skill.Animations.GetTargetOverheadAnimationID(skill_id)
    return Skill.skill_instance(skill_id).target_overhead_animation_id
end

function Skill.Animations.GetProjectileAnimationID(skill_id)
    return Skill.skill_instance(skill_id).projectile_animation1_id, Skill.skill_instance(skill_id).projectile_animation2_id
end

function Skill.Animations.GetIconFileID(skill_id)
    return Skill.skill_instance(skill_id).icon_file_id, Skill.skill_instance(skill_id).icon_file2_id
end

Skill.ExtraData = {}
function Skill.ExtraData.GetCondition(skill_id)
    return Skill.skill_instance(skill_id).condition
end

function Skill.ExtraData.GetTitle(skill_id)
    return Skill.skill_instance(skill_id).title
end

function Skill.ExtraData.GetIDPvP(skill_id)
    return Skill.skill_instance(skill_id).id_pvp
end

function Skill.ExtraData.GetTarget(skill_id)
    return Skill.skill_instance(skill_id).target
end

function Skill.ExtraData.GetSkillEquipType(skill_id)
    return Skill.skill_instance(skill_id).skill_equip_type
end

function Skill.ExtraData.GetSkillArguments(skill_id)
    return Skill.skill_instance(skill_id).skill_arguments
end

function Skill.ExtraData.GetNameID(skill_id)
    return Skill.skill_instance(skill_id).name_id
end

function Skill.ExtraData.GetConcise(skill_id)
    return Skill.skill_instance(skill_id).concise
end

function Skill.ExtraData.GetDescriptionID(skill_id)
    return Skill.skill_instance(skill_id).description_id
end

return Skill
