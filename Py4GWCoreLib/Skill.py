import PySkill
from .enums import SkillTextureMap

class Skill:
    @staticmethod
    def skill_instance(skill_id):
        return PySkill.Skill(skill_id)

    @staticmethod
    def GetName(skill_id):
        """Purpose: Retrieve the name of a skill by its ID."""
        return Skill.skill_instance(skill_id).id.GetName()

    @staticmethod
    def GetID(skill_name:str):
        """Purpose: Retrieve the ID of a skill by its ID."""
        return Skill.skill_instance(skill_name).id.id

    @staticmethod
    def GetType(skill_id):
        """Purpose: Retrieve the type of a skill by its ID. (tuple)"""
        return Skill.skill_instance(skill_id).type.id, Skill.skill_instance(skill_id).type.GetName()

    def GetCampaign(skill_id):
        """Purpose: Retrieve the campaign of a skill by its ID."""
        return Skill.skill_instance(skill_id).campaign.ToInt(), Skill.skill_instance(skill_id).campaign.GetName()

    @staticmethod
    def GetProfession(skill_id):
        """Purpose: Retrieve the profession of a skill by its ID."""
        return Skill.skill_instance(skill_id).profession.ToInt(), Skill.skill_instance(skill_id).profession.GetName() 
    
    class Data:
        @staticmethod
        def GetCombo(skill_id):
            """Purpose: Retrieve the combo of a skill by its ID."""
            return Skill.skill_instance(skill_id).combo

        @staticmethod
        def GetComboReq(skill_id):
            """Purpose: Retrieve the combo requirement of a skill by its ID."""
            return Skill.skill_instance(skill_id).combo_req

        @staticmethod
        def GetWeaponReq(skill_id):
            """Purpose: Retrieve the weapon requirement of a skill by its ID."""
            return Skill.skill_instance(skill_id).weapon_req

        @staticmethod
        def GetOvercast(skill_id):
            """Purpose: Retrieve the overcast of a skill by its ID."""
            return Skill.skill_instance(skill_id).overcast

        @staticmethod
        def GetEnergyCost(skill_id):
            """Purpose: Retrieve the actual energy cost of a skill by its ID"""
            cost = Skill.skill_instance(skill_id).energy_cost
            if cost == 11:
                return 15
            elif cost == 12:
                return 25
            return cost

        @staticmethod
        def GetHealthCost(skill_id):
            """Purpose: Retrieve the health cost of a skill by its ID."""
            return Skill.skill_instance(skill_id).health_cost
    
        @staticmethod
        def GetAdrenaline(skill_id):
            """Purpose: Retrieve the adrenaline cost of a skill by its ID."""
            return Skill.skill_instance(skill_id).adrenaline
    
        @staticmethod
        def GetActivation(skill_id):
            """Purpose: Retrieve the activation time of a skill by its ID."""
            return Skill.skill_instance(skill_id).activation

        @staticmethod
        def GetAftercast(skill_id):
            """Purpose: Retrieve the aftercast of a skill by its ID."""
            return Skill.skill_instance(skill_id).aftercast
        
        @staticmethod
        def GetRecharge(skill_id):
            """Purpose: Retrieve the recharge time of a skill by its ID.
            GWCA has 2 properties named the same, recharge & Recharge"""
            return Skill.skill_instance(skill_id).recharge

        @staticmethod
        def GetRecharge2(skill_id):
            """Purpose: Retrieve the recharge time of a skill by its ID.
            GWCA has 2 properties named the same, recharge & Recharge"""
            return Skill.skill_instance(skill_id).recharge2
    
        @staticmethod
        def GetAoERange(skill_id):
            """Purpose: Retrieve the AoE range of a skill by its ID."""
            return Skill.skill_instance(skill_id).aoe_range

        @staticmethod
        def GetAdrenalineA(skill_id):
            """Purpose: Retrieve the adrenaline A value of a skill by its ID."""
            return Skill.skill_instance(skill_id).adrenaline_a

        @staticmethod
        def GetAdrenalineB(skill_id):
            """Purpose: Retrieve the adrenaline B value of a skill by its ID."""
            return Skill.skill_instance(skill_id).adrenaline_b

    class Attribute:
        @staticmethod
        def GetAttribute(skill_id):
            """Purpose: Retrieve the attribute of a skill by its ID."""
            return Skill.skill_instance(skill_id).attribute 

        @staticmethod
        def GetScale(skill_id):
            """
            Purpose: Retrieve the scale of a skill at 0 and 15 points by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: tuple
            """
            return Skill.skill_instance(skill_id).scale_0pts, Skill.skill_instance(skill_id).scale_15pts

        @staticmethod
        def GetBonusScale(skill_id):
            """
            Purpose: Retrieve the bonus scale of a skill at 0 and 15 points by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: float
            """
            return Skill.skill_instance(skill_id).bonus_scale_0pts, Skill.skill_instance(skill_id).bonus_scale_15pts

        @staticmethod
        def GetDuration(skill_id):
            """
            Purpose: Retrieve the duration of a skill at 0 and 15 points by its ID.
            Args:
                skill_id (int): The ID of the skill to retrieve.
            Returns: int
            """
            return Skill.skill_instance(skill_id).duration_0pts, Skill.skill_instance(skill_id).duration_15pts

    class Flags:
        @staticmethod
        def IsTouchRange(skill_id):
            """Purpose: Check if a skill has touch range."""
            return Skill.skill_instance(skill_id).is_touch_range

        @staticmethod
        def IsElite(skill_id):
            """Purpose: Check if a skill is elite."""
            return Skill.skill_instance(skill_id).is_elite

        @staticmethod
        def IsHalfRange(skill_id):
            """Purpose: Check if a skill has half range."""
            return Skill.skill_instance(skill_id).is_half_range

        @staticmethod
        def IsPvP(skill_id):
            """Purpose: Check if a skill is PvP."""
            return Skill.skill_instance(skill_id).is_pvp

        @staticmethod
        def IsPvE(skill_id):
            """Purpose: Check if a skill is PvE."""
            return Skill.skill_instance(skill_id).is_pve

        @staticmethod
        def IsPlayable(skill_id):
            """Purpose: Check if a skill is playable."""
            return Skill.skill_instance(skill_id).is_playable

        @staticmethod
        def IsStacking(skill_id):
            """Purpose: Check if a skill is stacking."""
            return Skill.skill_instance(skill_id).is_stacking
        
        @staticmethod
        def IsNonStacking(skill_id):
            """Purpose: Check if a skill is non-stacking."""
            return Skill.skill_instance(skill_id).is_non_stacking

        @staticmethod
        def IsUnused(skill_id):
            """Purpose: Check if a skill is unused."""
            return Skill.skill_instance(skill_id).is_unused

        @staticmethod
        def IsHex(skill_id):
            """Purpose: Check if a skill is a Hex."""
            return Skill.GetType(skill_id)[1] == "Hex"

        @staticmethod
        def IsBounty(skill_id):
            """Purpose: Check if a skill is a Bounty."""
            return Skill.GetType(skill_id)[1] == "Bounty"

        @staticmethod
        def IsScroll(skill_id):
            """Purpose: Check if a skill is a Scroll."""
            return Skill.GetType(skill_id)[1] == "Scroll"

        @staticmethod
        def IsStance(skill_id):
            """ Purpose: Check if a skill is a Stance."""
            return Skill.GetType(skill_id)[1] == "Stance"

        @staticmethod
        def IsSpell(skill_id):
            """Purpose: Check if a skill is a Spell."""
            return Skill.GetType(skill_id)[1] == "Spell"

        @staticmethod
        def IsEnchantment(skill_id):
            """Purpose: Check if a skill is an Enchantment."""
            return Skill.GetType(skill_id)[1] == "Enchantment"

        @staticmethod
        def IsSignet(skill_id):
            """Purpose: Check if a skill is a Signet."""
            return Skill.GetType(skill_id)[1] == "Signet"

        @staticmethod
        def IsCondition(skill_id):
            """Purpose: Check if a skill is a Condition."""
            return Skill.GetType(skill_id)[1] == "Condition"

        @staticmethod
        def IsWell(skill_id):
            """ Purpose: Check if a skill is a Well."""
            return Skill.GetType(skill_id)[1] == "Well"

        @staticmethod
        def IsSkill(skill_id):
            """Purpose: Check if a skill is a Skill."""
            return Skill.GetType(skill_id)[1] == "Skill"

        @staticmethod
        def IsWard(skill_id):
            """Purpose: Check if a skill is a Ward."""
            return Skill.GetType(skill_id)[1] == "Ward"

        @staticmethod
        def IsGlyph(skill_id):
            """Purpose: Check if a skill is a Glyph."""
            return Skill.GetType(skill_id)[1] == "Glyph"

        @staticmethod
        def IsTitle(skill_id):
            """Purpose: Check if a skill is a Title."""
            return Skill.GetType(skill_id)[1] == "Title"

        @staticmethod
        def IsAttack(skill_id):
            """Purpose: Check if a skill is an Attack."""
            return Skill.GetType(skill_id)[1] == "Attack"

        @staticmethod
        def IsShout(skill_id):
            """Purpose: Check if a skill is a Shout."""
            return Skill.GetType(skill_id)[1] == "Shout"

        @staticmethod
        def IsSkill2(skill_id):
            """Purpose: Check if a skill is a Skill2."""
            return Skill.GetType(skill_id)[1] == "Skill2"

        @staticmethod
        def IsPassive(skill_id):
            """Purpose: Check if a skill is Passive."""
            return Skill.GetType(skill_id)[1] == "Passive"

        @staticmethod
        def IsEnvironmental(skill_id):
            """Purpose: Check if a skill is Environmental."""
            return Skill.GetType(skill_id)[1] == "Environmental"

        @staticmethod
        def IsPreparation(skill_id):
            """Purpose: Check if a skill is a Preparation."""
            return Skill.GetType(skill_id)[1] == "Preparation"

        @staticmethod
        def IsPetAttack(skill_id):
            """Purpose: Check if a skill is a PetAttack."""
            return Skill.GetType(skill_id)[1] == "PetAttack"

        @staticmethod
        def IsTrap(skill_id):
            """Purpose: Check if a skill is a Trap."""
            return Skill.GetType(skill_id)[1] == "Trap"

        @staticmethod
        def IsRitual(skill_id):
            """Purpose: Check if a skill is a Ritual."""
            return Skill.GetType(skill_id)[1] == "Ritual"

        @staticmethod
        def IsEnvironmentalTrap(skill_id):
            """Purpose: Check if a skill is an EnvironmentalTrap."""
            return Skill.GetType(skill_id)[1] == "EnvironmentalTrap"

        @staticmethod
        def IsItemSpell(skill_id):
            """Purpose: Check if a skill is an ItemSpell."""
            return Skill.GetType(skill_id)[1] == "ItemSpell"

        @staticmethod
        def IsWeaponSpell(skill_id):
            """Purpose: Check if a skill is a WeaponSpell."""
            return Skill.GetType(skill_id)[1] == "WeaponSpell"

        @staticmethod
        def IsForm(skill_id):
            """Purpose: Check if a skill is a Form."""
            return Skill.GetType(skill_id)[1] == "Form"

        @staticmethod
        def IsChant(skill_id):
            """Purpose: Check if a skill is a Chant."""
            return Skill.GetType(skill_id)[1] == "Chant"

        @staticmethod
        def IsEchoRefrain(skill_id):
            """Purpose: Check if a skill is an EchoRefrain."""
            return Skill.GetType(skill_id)[1] == "EchoRefrain"

        @staticmethod
        def IsDisguise(skill_id):
            """Purpose: Check if a skill is a Disguise."""
            return Skill.GetType(skill_id)[1] == "Disguise"

    class Animations:
        @staticmethod
        def GetEffects(skill_id):
            """Purpose: Retrieve the first effect of a skill by its ID."""
            return Skill.skill_instance(skill_id).effect1, Skill.skill_instance(skill_id).effect2

        @staticmethod
        def GetSpecial(skill_id):
            """ Purpose: Retrieve the special field."""
            return Skill.skill_instance(skill_id).special

        @staticmethod
        def GetConstEffect(skill_id):
            """Purpose: Retrieve the constant effect of a skill by its ID."""
            return Skill.skill_instance(skill_id).const_effect
        
        @staticmethod
        def GetCasterOverheadAnimationID(skill_id):
            """Purpose: Retrieve the caster overhead animation ID of a skill by its ID."""
            return Skill.skill_instance(skill_id).caster_overhead_animation_id

        @staticmethod
        def GetCasterBodyAnimationID(skill_id):
            """Purpose: Retrieve the caster body animation ID of a skill by its ID."""
            return Skill.skill_instance(skill_id).caster_body_animation_id

        @staticmethod
        def GetTargetBodyAnimationID(skill_id):
            """Purpose: Retrieve the target body animation ID of a skill by its ID."""
            return Skill.skill_instance(skill_id).target_body_animation_id

        @staticmethod
        def GetTargetOverheadAnimationID(skill_id):
            """Purpose: Retrieve the target overhead animation ID of a skill by its ID."""
            return Skill.skill_instance(skill_id).target_overhead_animation_id

        @staticmethod
        def GetProjectileAnimationID(skill_id):
            """Purpose: Retrieve the first projectile animation ID of a skill by its ID."""
            return Skill.skill_instance(skill_id).projectile_animation1_id, Skill.skill_instance(skill_id).projectile_animation2_id

        @staticmethod
        def GetIconFileID(skill_id):
            """Purpose: Retrieve the icon file ID of a skill by its ID."""
            return Skill.skill_instance(skill_id).icon_file_id, Skill.skill_instance(skill_id).icon_file2_id

    class ExtraData:
        @staticmethod
        def GetCondition(skill_id):
            """Purpose: Retrieve the condition of a skill by its ID."""
            return Skill.skill_instance(skill_id).condition

        @staticmethod
        def GetTitle(skill_id):
            """Purpose: Retrieve the title of a skill by its ID."""
            return Skill.skill_instance(skill_id).title

        @staticmethod
        def GetIDPvP(skill_id):
            """Purpose: Retrieve the PvP ID of a skill by its ID."""
            return Skill.skill_instance(skill_id).id_pvp

        @staticmethod
        def GetTarget(skill_id):
            """Purpose: Retrieve the target of a skill by its ID."""
            return Skill.skill_instance(skill_id).target

        @staticmethod
        def GetSkillEquipType(skill_id):
            """Purpose: Retrieve the skill equip type of a skill by its ID."""
            return Skill.skill_instance(skill_id).skill_equip_type
            
        @staticmethod
        def GetSkillArguments(skill_id):
            """Purpose: Retrieve the skill arguments of a skill by its ID."""
            return Skill.skill_instance(skill_id).skill_arguments

        @staticmethod
        def GetNameID(skill_id):
            """Purpose: Retrieve the name ID of a skill by its ID."""
            return Skill.skill_instance(skill_id).name_id

        @staticmethod
        def GetConcise(skill_id):
            """Purpose: Retrieve the concise description of a skill by its ID."""
            return Skill.skill_instance(skill_id).concise

        @staticmethod
        def GetDescriptionID(skill_id):
            """Purpose: Retrieve the description ID of a skill by its ID."""
            return Skill.skill_instance(skill_id).description_id

        @staticmethod
        def GetTexturePath(skill_id: int) -> str:
            filename = SkillTextureMap.get(skill_id)
            full_path = f"Textures\\Skill_Icons\\{filename}" if filename else ""
            return full_path


        


        

        
