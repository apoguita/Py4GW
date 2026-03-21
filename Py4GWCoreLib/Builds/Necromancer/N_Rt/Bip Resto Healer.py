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


class Bip_Resto(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Bip Resto Healer",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Ritualist,
            template_code="OAhkQoGIoFmzdoqKNncAAAAAAAA",
            required_skills=[
                Blood_is_Power_ID,
                Signet_of_Lost_Souls_ID,
                Mend_Body_and_Soul_ID,
                Spirit_Light_ID,
            ],
            optional_skills=[
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

        if (yield from self.skills.Ritualist.RestorationMagic.Mend_Body_and_Soul()):
            return True

        if (yield from self.skills.Necromancer.BloodMagic.Blood_is_Power()):
            return True

        if self.IsSkillEquipped(Wielders_Boon_ID) and (yield from self.skills.Ritualist.RestorationMagic.Wielders_Boon()):
            return True

        if self.IsSkillEquipped(Mending_Grip_ID) and (yield from self.skills.Ritualist.RestorationMagic.Mending_Grip()):
            return True

        if self.IsSkillEquipped(Spirit_Transfer_ID) and (yield from self.skills.Ritualist.RestorationMagic.Spirit_Transfer()):
            return True

        if not Routines.Checks.Agents.InAggro():
            return False

        if self.IsSkillEquipped(Vital_Weapon_ID) and (yield from self.skills.Ritualist.Communing.Vital_Weapon()):
            return True

        if self.IsSkillEquipped(Life_ID) and (yield from self.skills.Ritualist.RestorationMagic.Life()):
            return True

        if self.IsSkillEquipped(Recovery_ID) and (yield from self.skills.Ritualist.RestorationMagic.Recovery()):
            return True

        if self.IsSkillEquipped(Recuperation_ID) and (yield from self.skills.Ritualist.RestorationMagic.Recuperation()):
            return True

        if self.IsSkillEquipped(Breath_of_the_Great_Dwarf_ID) and (yield from self.skills.Any.NoAttribute.Breath_of_the_Great_Dwarf()):
            return True

        if self.IsSkillEquipped(You_Are_All_Weaklings_ID) and (yield from self.skills.Any.NoAttribute.You_Are_All_Weaklings()):
            return True

        if self.IsSkillEquipped(Enfeebling_Blood_ID) and (yield from self.skills.Necromancer.Curses.Enfeebling_Blood()):
            return True

        if (yield from self.skills.Necromancer.SoulReaping.Signet_of_Lost_Souls()):
            return True

        if (yield from self.skills.Ritualist.RestorationMagic.Spirit_Light()):
            return True

        return False
