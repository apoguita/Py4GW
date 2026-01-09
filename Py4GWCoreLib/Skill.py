import PySkill
import json
import os
from .enums import SkillTextureMap

class Skill:
    _desc_cache = None  # Cache JSON data once loaded
    
    @staticmethod
    def _load_descriptions():
        if Skill._desc_cache is None:
            path = os.path.join(os.path.dirname(__file__), "skill_descriptions.json")
            with open(path, encoding="utf-8") as f:
                Skill._desc_cache = json.load(f)
        return Skill._desc_cache
    
    @staticmethod
    def skill_instance(skill_id):
        return PySkill.Skill(skill_id)

    @staticmethod
    def GetName(skill_id):
        """Purpose: Retrieve the name of a skill by its ID."""
        return Skill.skill_instance(skill_id).id.GetName()
    
    @staticmethod
    def GetNameFromWiki(skill_id):
        """Purpose: Retrieve the name of a skill by its ID from the wiki."""
        data = Skill._load_descriptions()
        return data.get(str(skill_id), {}).get("name", Skill.GetName(skill_id))
    
    @staticmethod
    def GetURL(skill_id):
        """Purpose: Retrieve the URL of a skill by its ID."""
        data = Skill._load_descriptions()
        return data.get(str(skill_id), {}).get("url", "")
    
    @staticmethod
    def GetProgressionData(skill_id):
        """
        Purpose: Retrieve the progression data for a given skill.
        Returns a list of (attribute_name, field_name, values_dict)
        """
        data = Skill._load_descriptions()
        entry = data.get(str(skill_id), {})
        progressions = entry.get("progression")

        if not progressions:
            return []

        if isinstance(progressions, dict):
            progressions = [progressions]

        results = []
        for prog in progressions:
            attr = prog.get("attribute", "")
            field = prog.get("field", "")
            values = {int(k): float(v) for k, v in prog.get("values", {}).items()}
            results.append((attr, field, values))

        return results



    @staticmethod
    def GetID(skill_name:str):
        """Purpose: Retrieve the ID of a skill by its ID."""
        return Skill.skill_instance(skill_name).id.id
    
    @staticmethod
    def GetDescription(skill_id: int) -> str:
        """Return full description from skill_descriptions.json."""
        data = Skill._load_descriptions()
        return data.get(str(skill_id), {}).get("desc_full", "No description available.")

    @staticmethod
    def GetConciseDescription(skill_id: int) -> str:
        """Return concise description from skill_descriptions.json."""
        data = Skill._load_descriptions()
        return data.get(str(skill_id), {}).get("desc_concise", "No description available.")

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
            special = Skill.skill_instance(skill_id).special
            if (special & 0x0001) == 0:
                return 0
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

    # =========================================================================
    # Target Type 
    # =========================================================================

    class Target:
        """
        Skill target/affected entities.

        NOTE: This field indicates which entities are AFFECTED by the skill,
        not necessarily who you can TARGET with the skill UI.

        For example:
            - Death's Charge (5 = Self/Foe): Affects SELF (you teleport) and FOE (destination)
            - Sever Artery (5 = Self/Foe): Attack skill - you attack, foe takes damage
            - Healing Breeze (3 = Self/Ally): Can cast on self or allies

        For actual targeting logic, also consider:
            - Skill type (Attack skills target foes)
            - Skill description
            - IsTouchRange/IsHalfRange flags

        Common values:
            0 = No target / Self only
            1 = Self
            2 = Ally
            4 = Foe/Enemy
            8 = Dead ally (for resurrection)
            16 = Item/Object
            32 = Spirit
        """

        # Target type bitmask values
        NONE = 0
        SELF = 1
        ALLY = 2
        FOE = 4
        DEAD = 8
        ITEM = 16
        SPIRIT = 32

        _TARGET_NAMES = {
            0: "No Target",
            1: "Self",
            2: "Ally",
            3: "Self/Ally",
            4: "Foe",
            5: "Self/Foe",
            6: "Ally/Foe",
            7: "Any",
            8: "Dead Ally",
            10: "Ally/Dead",
            12: "Foe/Dead",
        }

        @staticmethod
        def GetTargetType(skill_id: int) -> int:
            """Get the raw target type bitmask."""
            return Skill.skill_instance(skill_id).target

        @staticmethod
        def GetTargetTypeName(skill_id: int) -> str:
            """Get a human-readable name for the affected entities."""
            target = Skill.Target.GetTargetType(skill_id)
            if target in Skill.Target._TARGET_NAMES:
                return Skill.Target._TARGET_NAMES[target]

            # Build name from flags
            parts = []
            if target & Skill.Target.SELF:
                parts.append("Self")
            if target & Skill.Target.ALLY:
                parts.append("Ally")
            if target & Skill.Target.FOE:
                parts.append("Foe")
            if target & Skill.Target.DEAD:
                parts.append("Dead")
            if target & Skill.Target.ITEM:
                parts.append("Item")
            if target & Skill.Target.SPIRIT:
                parts.append("Spirit")

            return "/".join(parts) if parts else "Unknown"

        @staticmethod
        def RequiresTarget(skill_id: int) -> bool:
            """Check if skill requires selecting a target (not self-only or no-target)."""
            target = Skill.Target.GetTargetType(skill_id)
            # If target is 0 (no target) or 1 (self only), no target required
            return target > 1

        @staticmethod
        def AffectsSelf(skill_id: int) -> bool:
            """Check if skill affects self."""
            target = Skill.Target.GetTargetType(skill_id)
            return (target & Skill.Target.SELF) != 0 or target == 0

        @staticmethod
        def AffectsAlly(skill_id: int) -> bool:
            """Check if skill affects allies."""
            target = Skill.Target.GetTargetType(skill_id)
            return (target & Skill.Target.ALLY) != 0

        @staticmethod
        def AffectsFoe(skill_id: int) -> bool:
            """Check if skill affects enemies."""
            target = Skill.Target.GetTargetType(skill_id)
            return (target & Skill.Target.FOE) != 0

        @staticmethod
        def AffectsDead(skill_id: int) -> bool:
            """Check if skill affects dead allies (resurrection skills)."""
            target = Skill.Target.GetTargetType(skill_id)
            return (target & Skill.Target.DEAD) != 0

        @staticmethod
        def AffectsSpirit(skill_id: int) -> bool:
            """Check if skill affects spirits."""
            target = Skill.Target.GetTargetType(skill_id)
            return (target & Skill.Target.SPIRIT) != 0

        # Keep old names as aliases for backwards compatibility
        CanTargetSelf = AffectsSelf
        CanTargetAlly = AffectsAlly
        CanTargetFoe = AffectsFoe
        CanTargetDead = AffectsDead
        CanTargetSpirit = AffectsSpirit

    # =========================================================================
    # Combo Chain 
    # =========================================================================

    class Combo:
        """
        Assassin combo chain.

        Combo skills must be used in sequence: Lead Attack -> Off-Hand Attack -> Dual Attack.
        - combo: What this skill provides (0=None, 1=Lead, 2=Off-Hand, 3=Dual)
        - combo_req: What this skill requires (0=None, 1=Lead, 2=Off-Hand)
        """

        # Combo types (what the skill provides)
        TYPE_NONE = 0
        TYPE_LEAD = 1
        TYPE_OFFHAND = 2
        TYPE_DUAL = 3

        # Combo requirements (what the skill needs)
        REQ_NONE = 0
        REQ_LEAD = 1
        REQ_OFFHAND = 2

        _COMBO_NAMES = {
            0: "None",
            1: "Lead Attack",
            2: "Off-Hand Attack",
            3: "Dual Attack",
        }

        _REQ_NAMES = {
            0: "None",
            1: "Requires Lead",
            2: "Requires Off-Hand",
        }

        @staticmethod
        def GetComboType(skill_id: int) -> int:
            """Get the combo type this skill provides."""
            return Skill.skill_instance(skill_id).combo

        @staticmethod
        def GetComboTypeName(skill_id: int) -> str:
            """Get human-readable combo type name."""
            combo = Skill.Combo.GetComboType(skill_id)
            return Skill.Combo._COMBO_NAMES.get(combo, "Unknown")

        @staticmethod
        def GetComboRequirement(skill_id: int) -> int:
            """Get the combo requirement for this skill."""
            return Skill.skill_instance(skill_id).combo_req

        @staticmethod
        def GetComboRequirementName(skill_id: int) -> str:
            """Get human-readable combo requirement name."""
            req = Skill.Combo.GetComboRequirement(skill_id)
            return Skill.Combo._REQ_NAMES.get(req, "Unknown")

        @staticmethod
        def IsLeadAttack(skill_id: int) -> bool:
            """Check if skill is a Lead Attack."""
            return Skill.Combo.GetComboType(skill_id) == Skill.Combo.TYPE_LEAD

        @staticmethod
        def IsOffhandAttack(skill_id: int) -> bool:
            """Check if skill is an Off-Hand Attack."""
            return Skill.Combo.GetComboType(skill_id) == Skill.Combo.TYPE_OFFHAND

        @staticmethod
        def IsDualAttack(skill_id: int) -> bool:
            """Check if skill is a Dual Attack."""
            return Skill.Combo.GetComboType(skill_id) == Skill.Combo.TYPE_DUAL

        @staticmethod
        def RequiresLead(skill_id: int) -> bool:
            """Check if skill requires a Lead Attack to have been used."""
            return Skill.Combo.GetComboRequirement(skill_id) == Skill.Combo.REQ_LEAD

        @staticmethod
        def RequiresOffhand(skill_id: int) -> bool:
            """Check if skill requires an Off-Hand Attack to have been used."""
            return Skill.Combo.GetComboRequirement(skill_id) == Skill.Combo.REQ_OFFHAND

        @staticmethod
        def IsComboSkill(skill_id: int) -> bool:
            """Check if skill is part of a combo chain (Lead, Off-Hand, or Dual)."""
            return Skill.Combo.GetComboType(skill_id) != Skill.Combo.TYPE_NONE

    # =========================================================================
    # Weapon Requirement
    # =========================================================================

    class Weapon:
        """
        Skill weapon requirement.

        Some skills require specific weapon types to be equipped.
        These are bitmask values that can be combined.
        """

        # Weapon requirement values (from WeaporReq enum)
        REQ_NONE = 0
        REQ_AXE = 1
        REQ_BOW = 2
        REQ_DAGGER = 8
        REQ_HAMMER = 16
        REQ_SCYTHE = 32
        REQ_SPEAR = 64
        REQ_SWORD = 128
        REQ_MELEE = 185  # Combined melee weapons

        _WEAPON_NAMES = {
            0: "None",
            1: "Axe",
            2: "Bow",
            8: "Daggers",
            16: "Hammer",
            32: "Scythe",
            64: "Spear",
            128: "Sword",
            185: "Melee",
        }

        @staticmethod
        def GetWeaponRequirement(skill_id: int) -> int:
            """Get the raw weapon requirement value."""
            return Skill.skill_instance(skill_id).weapon_req

        @staticmethod
        def GetWeaponRequirementName(skill_id: int) -> str:
            """Get human-readable weapon requirement name."""
            req = Skill.Weapon.GetWeaponRequirement(skill_id)
            return Skill.Weapon._WEAPON_NAMES.get(req, f"Unknown ({req})")

        @staticmethod
        def HasWeaponRequirement(skill_id: int) -> bool:
            """Check if skill has any weapon requirement."""
            return Skill.Weapon.GetWeaponRequirement(skill_id) != Skill.Weapon.REQ_NONE

        @staticmethod
        def RequiresAxe(skill_id: int) -> bool:
            """Check if skill requires an axe."""
            req = Skill.Weapon.GetWeaponRequirement(skill_id)
            return req == Skill.Weapon.REQ_AXE or (req & Skill.Weapon.REQ_AXE) != 0

        @staticmethod
        def RequiresBow(skill_id: int) -> bool:
            """Check if skill requires a bow."""
            req = Skill.Weapon.GetWeaponRequirement(skill_id)
            return req == Skill.Weapon.REQ_BOW or (req & Skill.Weapon.REQ_BOW) != 0

        @staticmethod
        def RequiresDaggers(skill_id: int) -> bool:
            """Check if skill requires daggers."""
            req = Skill.Weapon.GetWeaponRequirement(skill_id)
            return req == Skill.Weapon.REQ_DAGGER or (req & Skill.Weapon.REQ_DAGGER) != 0

        @staticmethod
        def RequiresHammer(skill_id: int) -> bool:
            """Check if skill requires a hammer."""
            req = Skill.Weapon.GetWeaponRequirement(skill_id)
            return req == Skill.Weapon.REQ_HAMMER or (req & Skill.Weapon.REQ_HAMMER) != 0

        @staticmethod
        def RequiresSword(skill_id: int) -> bool:
            """Check if skill requires a sword."""
            req = Skill.Weapon.GetWeaponRequirement(skill_id)
            return req == Skill.Weapon.REQ_SWORD or (req & Skill.Weapon.REQ_SWORD) != 0

        @staticmethod
        def RequiresScythe(skill_id: int) -> bool:
            """Check if skill requires a scythe."""
            req = Skill.Weapon.GetWeaponRequirement(skill_id)
            return req == Skill.Weapon.REQ_SCYTHE or (req & Skill.Weapon.REQ_SCYTHE) != 0

        @staticmethod
        def RequiresSpear(skill_id: int) -> bool:
            """Check if skill requires a spear."""
            req = Skill.Weapon.GetWeaponRequirement(skill_id)
            return req == Skill.Weapon.REQ_SPEAR or (req & Skill.Weapon.REQ_SPEAR) != 0

        @staticmethod
        def RequiresMelee(skill_id: int) -> bool:
            """Check if skill requires a melee weapon (axe, sword, hammer, daggers, scythe)."""
            req = Skill.Weapon.GetWeaponRequirement(skill_id)
            # Check if it's exactly REQ_MELEE or if it matches any melee weapon
            if req == Skill.Weapon.REQ_MELEE:
                return True
            melee_mask = (Skill.Weapon.REQ_AXE | Skill.Weapon.REQ_SWORD |
                         Skill.Weapon.REQ_HAMMER | Skill.Weapon.REQ_DAGGER |
                         Skill.Weapon.REQ_SCYTHE)
            return req != 0 and (req & melee_mask) != 0

        @staticmethod
        def RequiresRanged(skill_id: int) -> bool:
            """Check if skill requires a ranged weapon (bow, spear)."""
            req = Skill.Weapon.GetWeaponRequirement(skill_id)
            ranged_mask = Skill.Weapon.REQ_BOW | Skill.Weapon.REQ_SPEAR
            return req != 0 and (req & ranged_mask) != 0

    # =========================================================================
    # Range Interpretation
    # =========================================================================

    class Range:
        """
        Skill range.

        Guild Wars uses several standard range values (in game units):
            - Touch: ~144 (adjacent)
            - Adjacent: ~166
            - Nearby: ~252
            - In the Area: ~322
            - Earshot: ~1010
            - Half Range (Shortbow): ~1010
            - Full Range (Flatbow): ~1245
            - Spirit Range: ~2500
        """

        # Range constants (in game units, approximate)
        TOUCH = 144
        ADJACENT = 166
        NEARBY = 252
        IN_THE_AREA = 322
        EARSHOT = 1010
        HALF_RANGE = 1010
        FULL_RANGE = 1245
        SPIRIT_RANGE = 2500

        _RANGE_TYPES = {
            "Touch": 144,
            "Adjacent": 166,
            "Nearby": 252,
            "In the Area": 322,
            "Earshot": 1010,
            "Half Range": 1010,
            "Full Range": 1245,
            "Spirit Range": 2500,
        }

        @staticmethod
        def GetRangeType(skill_id: int) -> str:
            """
            Get the range type name for a skill.

            Returns one of: "Touch", "Half Range", "Full Range", "Self"
            """
            if Skill.Flags.IsTouchRange(skill_id):
                return "Touch"
            if Skill.Flags.IsHalfRange(skill_id):
                return "Half Range"

            # Check if it's a self-target only skill
            target = Skill.skill_instance(skill_id).target
            if target == 0 or target == 1:
                return "Self"

            # Default to full range for targeted skills
            return "Full Range"

        @staticmethod
        def GetRangeInUnits(skill_id: int) -> float:
            """
            Get the skill's range in game units.

            Note: This is approximate as exact ranges depend on skill type.
            """
            if Skill.Flags.IsTouchRange(skill_id):
                return Skill.Range.TOUCH
            if Skill.Flags.IsHalfRange(skill_id):
                return Skill.Range.HALF_RANGE

            # Check if it's a self-target only skill
            target = Skill.skill_instance(skill_id).target
            if target == 0 or target == 1:
                return 0.0  # Self-target, no range

            # Default to full range
            return Skill.Range.FULL_RANGE

        @staticmethod
        def GetAoERange(skill_id: int) -> float:
            """
            Get the Area of Effect range for a skill.

            Returns the aoe_range field from skill data.
            """
            return Skill.skill_instance(skill_id).aoe_range

        @staticmethod
        def IsInRange(skill_id: int, distance: float) -> bool:
            """
            Check if a target at the given distance is within skill range.

            Args:
                skill_id: The skill to check
                distance: Distance to target in game units

            Returns:
                True if target is within range.
            """
            skill_range = Skill.Range.GetRangeInUnits(skill_id)
            if skill_range == 0:
                return True  # Self-target skills always "in range"
            return distance <= skill_range

        
