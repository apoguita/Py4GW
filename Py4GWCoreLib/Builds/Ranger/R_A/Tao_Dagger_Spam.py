from Py4GWCoreLib import Profession
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Jagged_Strike_ID = Skill.GetID("Jagged_Strike")
Fox_Fangs_ID = Skill.GetID("Fox_Fangs")
Death_Blossom_ID = Skill.GetID("Death_Blossom")
Together_as_one_ID = Skill.GetID("Together_as_one")
Breath_of_the_Great_Dwarf_ID = Skill.GetID("Breath_of_the_Great_Dwarf")


class Tao_Dagger_Spam(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="TaO Dagger Spam",
            required_primary=Profession.Ranger,
            required_secondary=Profession.Assassin,
            template_code="OgcTYr72Xyhhh5gZsGAAAAAAAAA",
            required_skills=[
                Jagged_Strike_ID,
                Fox_Fangs_ID,
                Death_Blossom_ID,
                Together_as_one_ID,
            ],
            optional_skills=[
                Breath_of_the_Great_Dwarf_ID,
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

        if self.IsSkillEquipped(Breath_of_the_Great_Dwarf_ID) and (yield from self.skills.Any.NoAttribute.Breath_of_the_Great_Dwarf()):
            return True

        if not Routines.Checks.Agents.InAggro():
            return False

        if (yield from self.skills.Ranger.Expertise.Together_as_One()):
            return True

        if (yield from self.skills.Assassin.DaggerMastery.Death_Blossom()):
            return True
        if (yield from self.skills.Assassin.DaggerMastery.Fox_Fangs()):
            return True
        if (yield from self.skills.Assassin.DaggerMastery.Jagged_Strike()):
            return True

        return False
