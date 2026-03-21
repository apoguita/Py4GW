from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Energy_Surge_ID = Skill.GetID("Energy_Surge")
Mistrust_ID = Skill.GetID("Mistrust")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
Cry_of_Pain_ID = Skill.GetID("Cry_of_Pain")
Unnatural_Signet_ID = Skill.GetID("Unnatural_Signet")
Cry_of_Frustration_ID = Skill.GetID("Cry_of_Frustration")
Overload_ID = Skill.GetID("Overload")


class Energy_Surge_Mistrust(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Energy Surge",
            required_primary=Profession.Mesmer,
            template_code="OQBCAswEc5Jw0zuoNopTOggD",
            required_skills=[
                Air_of_Superiority_ID,
                Energy_Surge_ID,
                Mistrust_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Cry_of_Pain_ID,
                Unnatural_Signet_ID,
                Cry_of_Frustration_ID,
                Overload_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetBlockedSkills([
            Air_of_Superiority_ID,
            Energy_Surge_ID,
            Mistrust_ID,
            Ebon_Vanguard_Assassin_Support_ID,
            Cry_of_Pain_ID,
            Unnatural_Signet_ID,
            Cry_of_Frustration_ID,
        ])
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return

        if Routines.Checks.Agents.InAggro() and (yield from self.skills.Any.NoAttribute.Air_of_Superiority()):
            return

        if Routines.Checks.Agents.InAggro() and (yield from self.skills.Mesmer.DominationMagic.Mistrust()):
            return

        if Routines.Checks.Agents.InAggro() and (yield from self.skills.Any.NoAttribute.Cry_of_Pain(allow_hex_fallback=False)):
            return

        if Routines.Checks.Agents.InAggro() and (yield from self.skills.Mesmer.DominationMagic.Cry_of_Frustration()):
            return

        if Routines.Checks.Agents.InAggro() and (yield from self.skills.Mesmer.DominationMagic.Overload()):
            return

        if Routines.Checks.Agents.InAggro() and (yield from self.skills.Any.NoAttribute.Ebon_Vanguard_Assassin_Support()):
            return

        if Routines.Checks.Agents.InAggro() and (yield from self.skills.Any.NoAttribute.Cry_of_Pain()):
            return

        if Routines.Checks.Agents.InAggro() and (yield from self.skills.Mesmer.DominationMagic.Energy_Surge()):
            return

        if Routines.Checks.Agents.InAggro() and (yield from self.skills.Mesmer.DominationMagic.Unnatural_Signet()):
            return

        if not Routines.Checks.Agents.InAggro():
            return

        yield
