from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate

Ineptitude_ID = Skill.GetID("Ineptitude")
Judges_Insight_ID = Skill.GetID("Judges_Insight")
Wandering_Eye_ID = Skill.GetID("Wandering_Eye")
Arcane_Conundrum_ID = Skill.GetID("Arcane_Conundrum")
Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
Ebon_Battle_Standard_of_Wisdom_ID = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")
Signet_of_Clumsiness_ID = Skill.GetID("Signet_of_Clumsiness")
Power_Drain_ID = Skill.GetID("Power_Drain")

class HolyInept(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Holy Inept",
            required_primary=Profession.Mesmer,
            required_secondary=Profession.Monk,
            template_code="OQNDAcsuRvAIg5ZkA4i7iwlLEA",
            required_skills=[
                Ineptitude_ID,
                Judges_Insight_ID,
                Wandering_Eye_ID,
                Arcane_Conundrum_ID,
            ],
            optional_skills=[
                Air_of_Superiority_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Ebon_Battle_Standard_of_Wisdom_ID,
                Signet_of_Clumsiness_ID,
                Power_Drain_ID
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return False

        if self.IsSkillEquipped(Air_of_Superiority_ID) and (yield from self.skills.Any.PvE.Air_of_Superiority()):
            return True

        if not Routines.Checks.Agents.InAggro():
            return False

        if self.IsSkillEquipped(Ebon_Vanguard_Assassin_Support_ID) and (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()):
            return True

        if (yield from self.skills.Mesmer.DominationMagic.Power_Drain()):
            return True

        if (yield from self.skills.Mesmer.IllusionMagic.Ineptitude()):
            return True

        if (yield from self.skills.Mesmer.IllusionMagic.Wandering_Eye()):
            return True

        if self.IsSkillEquipped(Arcane_Conundrum_ID) and (yield from self.skills.Mesmer.IllusionMagic.Arcane_Conundrum()):
            return True

        if (yield from self.skills.Monk.SmitingPrayers.Judges_Insight()):
            return True

        if self.IsSkillEquipped(Signet_of_Clumsiness_ID) and (yield from self.skills.Mesmer.IllusionMagic.Signet_of_Clumsiness()):
            return

        if self.IsSkillEquipped(Ebon_Battle_Standard_of_Wisdom_ID) and (yield from self.CastSkillID(
            skill_id=Ebon_Battle_Standard_of_Wisdom_ID,
            log=False,
            aftercast_delay=250,
        )):
            return True

        yield
