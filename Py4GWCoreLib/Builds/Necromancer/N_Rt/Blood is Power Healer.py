from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate

Blood_is_Power_ID = Skill.GetID("Blood_is_Power")
Signet_of_Lost_Souls_ID = Skill.GetID("Signet_of_Lost_Souls")
Mend_Body_and_Soul_ID = Skill.GetID("Mend_Body_and_Soul")
Spirit_Light_ID = Skill.GetID("Spirit_Light")
Vital_Weapon_ID = Skill.GetID("Vital_Weapon")
Wielders_Boon_ID = Skill.GetID("Wielders_Boon")
Mending_Grip_ID = Skill.GetID("Mending_Grip")
Spirit_Transfer_ID = Skill.GetID("Spirit_Transfer")
Life_ID = Skill.GetID("Life")
You_Are_All_Weaklings_ID = Skill.GetID("You_Are_All_Weaklings")
Enfeebling_Blood_ID = Skill.GetID("Enfeebling_Blood")
Recovery_ID = Skill.GetID("Recovery")
Breath_of_the_Great_Dwarf_ID = Skill.GetID("Breath_of_the_Great_Dwarf")
Recuperation_ID = Skill.GetID("Recuperation")
Blood_Bond_ID = Skill.GetID("Blood_Bond")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")


class Blood_is_Power_Healer(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Blood is Power Healer",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Ritualist,
            template_code="OAhjQkGZIP3hqq0EAAAAAAAAAA",
            required_skills=[
                Blood_is_Power_ID,
                Signet_of_Lost_Souls_ID,
                Mend_Body_and_Soul_ID,
            ],
            optional_skills=[
                Spirit_Light_ID,
                Vital_Weapon_ID,
                Wielders_Boon_ID,
                Mending_Grip_ID,
                Spirit_Transfer_ID,
                Life_ID,
                You_Are_All_Weaklings_ID,
                Enfeebling_Blood_ID,
                Recovery_ID,
                Breath_of_the_Great_Dwarf_ID,
                Recuperation_ID,
                Blood_Bond_ID,
                Ebon_Vanguard_Assassin_Support_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        # emergency: Spirit Transfer when a spirit is in range and any ally is at or below 30% HP.
        if (yield from self.skills.Ritualist.RestorationMagic.Spirit_Transfer(health_threshold=0.30)):
            return True

        # emergency: spirit-gated burst heal when any ally is at or below 30% HP.
        if (yield from self.skills.Ritualist.RestorationMagic.Spirit_Light(health_threshold=0.30)):
            return True

        # emergency: any ally at or below 40% HP preempts everything.
        if (yield from self.skills.Ritualist.RestorationMagic.Mend_Body_and_Soul(health_threshold=0.40)):
            return True

        # Signet of Lost Souls: emergency energy refill when caster < 30%.
        if (yield from self.skills.Necromancer.SoulReaping.Signet_of_Lost_Souls(max_self_energy_pct=0.30)):
            return True

        # Recuperation 6+ allies below 75% HP OR 6+ allies degenning.
        if self.IsSkillEquipped(Recuperation_ID) and (yield from self.skills.Ritualist.RestorationMagic.Recuperation(
            min_party_damaged_count=6,
        )):
            return True
        if self.IsSkillEquipped(Recuperation_ID) and (yield from self.skills.Ritualist.RestorationMagic.Recuperation(
            min_degen_count=6,
        )):
            return True

        if (yield from self.skills.Necromancer.BloodMagic.Blood_is_Power()):
            return True

        if self.IsSkillEquipped(Wielders_Boon_ID) and (yield from self.skills.Ritualist.RestorationMagic.Wielders_Boon()):
            return True

        if self.IsSkillEquipped(Mending_Grip_ID) and (yield from self.skills.Ritualist.RestorationMagic.Mending_Grip()):
            return True

        if self.IsSkillEquipped(Spirit_Transfer_ID) and (yield from self.skills.Ritualist.RestorationMagic.Spirit_Transfer()):
            return True

        # spirit-gated cleanse: blind on a martial (melee/ranger/paragon).
        if (yield from self.skills.Ritualist.RestorationMagic.Mend_Body_and_Soul(cleanse_blind_martial=True)):
            return True

        # spirit-gated cleanse: cripple on a melee ally.
        if (yield from self.skills.Ritualist.RestorationMagic.Mend_Body_and_Soul(cleanse_cripple_melee=True)):
            return True

        # Recuperation: 6+ allies below 75% HP OR 4+ allies degenning.
        if self.IsSkillEquipped(Recuperation_ID) and (yield from self.skills.Ritualist.RestorationMagic.Recuperation(
            min_party_damaged_count=6,
        )):
            return True
        if self.IsSkillEquipped(Recuperation_ID) and (yield from self.skills.Ritualist.RestorationMagic.Recuperation(
            min_degen_count=4,
        )):
            return True

        if self.IsSkillEquipped(Ebon_Vanguard_Assassin_Support_ID) and (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support(min_self_energy_pct=0.40)):
            return True

        # Signet of Lost Souls : energy refill when caster < 60%.
        if (yield from self.skills.Necromancer.SoulReaping.Signet_of_Lost_Souls(max_self_energy_pct=0.60)):
            return True

        if self.IsSkillEquipped(Blood_Bond_ID) and (yield from self.skills.Necromancer.BloodMagic.Blood_Bond()):
            return True

        # damaged: any ally at or below 75% HP, before combat skills.
        if (yield from self.skills.Ritualist.RestorationMagic.Mend_Body_and_Soul(health_threshold=0.75)):
            return True

        if not self.IsInAggro():
            return False

        if self.IsSkillEquipped(Vital_Weapon_ID) and (yield from self.skills.Ritualist.Communing.Vital_Weapon()):
            return True

        if self.IsSkillEquipped(Life_ID) and (yield from self.skills.Ritualist.RestorationMagic.Life()):
            return True

        if self.IsSkillEquipped(Recovery_ID) and (yield from self.skills.Ritualist.RestorationMagic.Recovery()):
            return True

        # Signet of Lost Souls: opportunistic refill, no caster energy gate.
        if (yield from self.skills.Necromancer.SoulReaping.Signet_of_Lost_Souls()):
            return True

        # Recuperation: 6+ allies below 75% HP OR 2+ allies degenning.
        if self.IsSkillEquipped(Recuperation_ID) and (yield from self.skills.Ritualist.RestorationMagic.Recuperation(
            min_party_damaged_count=6,
        )):
            return True
        if self.IsSkillEquipped(Recuperation_ID) and (yield from self.skills.Ritualist.RestorationMagic.Recuperation(
            min_degen_count=2,
        )):
            return True

        # preventive: any ally at or below 85% HP, after Recuperation.
        if (yield from self.skills.Ritualist.RestorationMagic.Mend_Body_and_Soul(health_threshold=0.85)):
            return True

        if self.IsSkillEquipped(Breath_of_the_Great_Dwarf_ID) and (yield from self.skills.Any.NoAttribute.Breath_of_the_Great_Dwarf()):
            return True

        if self.IsSkillEquipped(You_Are_All_Weaklings_ID) and (yield from self.skills.Any.NoAttribute.You_Are_All_Weaklings()):
            return True

        if self.IsSkillEquipped(Enfeebling_Blood_ID) and (yield from self.skills.Necromancer.Curses.Enfeebling_Blood()):
            return True

        if (yield from self.skills.Ritualist.RestorationMagic.Spirit_Light()):
            return True

        return False
