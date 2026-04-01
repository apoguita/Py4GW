from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Healing_Burst_ID = Skill.GetID("Healing_Burst")
Dwaynas_Kiss_ID = Skill.GetID("Dwaynas_Kiss")
Seed_of_Life_ID = Skill.GetID("Seed_of_Life")
Draw_Conditions_ID = Skill.GetID("Draw_Conditions")
Vigorous_Spirit_ID = Skill.GetID("Vigorous_Spirit")


class Healing_Burst(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Healing Burst",
            required_primary=Profession.Monk,
            template_code="OwUUMoG/CoSeRbE5g3EAAAAAAAAA",
            required_skills=[
                Healing_Burst_ID,
                Dwaynas_Kiss_ID,
                Seed_of_Life_ID,
                Draw_Conditions_ID,
            ],
            optional_skills=[ 
                Vigorous_Spirit_ID,
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

        if (yield from self.skills.Monk.HealingPrayers.Healing_Burst()):
            return True

        if (yield from self.skills.Monk.HealingPrayers.Dwaynas_Kiss()):
            return True

        if (yield from self.skills.Monk.NoAttribute.Seed_of_Life()):
            return True

        if (yield from self.skills.Monk.ProtectionPrayers.Draw_Conditions()):
            return True
        
        if not (Routines.Checks.Agents.InAggro()):
            return False
        
        if self.IsSkillEquipped(Vigorous_Spirit_ID) and (yield from self.skills.Monk.HealingPrayers.Vigorous_Spirit()):
            return True

        return False
