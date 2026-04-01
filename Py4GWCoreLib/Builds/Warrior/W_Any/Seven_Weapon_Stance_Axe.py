from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate

Cyclone_Axe_ID = Skill.GetID("Cyclone_Axe")
Whirlwind_Attack_ID = Skill.GetID("Whirlwind_Attack")
Executioners_Strike_ID = Skill.GetID("Executioners_Strike")
Seven_Weapon_Stance_ID = Skill.GetID("Seven_Weapon_Stance")
Endure_Pain_ID = Skill.GetID("Endure_Pain")


class Seven_Weapon_Stance_Axe(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Seven Weapon Stance Axe",
            required_primary=Profession.Warrior,
            template_code="OQITEZJZVSpYHEqQsGAAAAAAAAA",
            required_skills=[
                Cyclone_Axe_ID,
                Whirlwind_Attack_ID,
                Executioners_Strike_ID,
                Seven_Weapon_Stance_ID,
            ],
            optional_skills=[
                Endure_Pain_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _run_local_skill_logic(self):
        if not Routines.Checks.Agents.InAggro():
            return False

        if not Routines.Checks.Skills.CanCast():
            return False

        if (yield from self.skills.Warrior.Strength.Seven_Weapon_Stance()):
            return True

        if self.IsSkillEquipped(Endure_Pain_ID) and (yield from self.skills.Warrior.Strength.Endure_Pain()):
            return True

        if (yield from self.skills.Warrior.AxeMastery.Executioners_Strike()):
            return True

        if (yield from self.skills.Warrior.AxeMastery.Cyclone_Axe()):
            return True

        if (yield from self.skills.Warrior.NoAttribute.Whirlwind_Attack()):
            return True

        return False
