from Py4GWCoreLib import Profession
from Py4GWCoreLib import Range, Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate

Breath_of_the_Great_Dwarf_ID = Skill.GetID("Breath_of_the_Great_Dwarf")
Energy_Surge_ID = Skill.GetID("Energy_Surge")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
Flesh_of_My_Flesh_ID = Skill.GetID("Flesh_of_My_Flesh")
Cry_of_Frustration_ID = Skill.GetID("Cry_of_Frustration")
Unnatural_Signet_ID = Skill.GetID("Unnatural_Signet")
Power_Drain_ID = Skill.GetID("Power_Drain")
Shatter_Hex_ID = Skill.GetID("Shatter_Hex")
Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Overload_ID = Skill.GetID("Overload")


class RezEsurge(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Rez Esurge",
            required_primary=Profession.Mesmer,
            required_secondary=Profession.Ritualist,
            template_code="OQhkAwC7gFKUr4JAc5uYGQOwQwFD",
            required_skills=[
                Energy_Surge_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Flesh_of_My_Flesh_ID,
                Cry_of_Frustration_ID,
            ],
            optional_skills=[
                Breath_of_the_Great_Dwarf_ID,
                Unnatural_Signet_ID,
                Power_Drain_ID,
                Shatter_Hex_ID,
                Air_of_Superiority_ID,
                Overload_ID,
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

        if self.IsSkillEquipped(Shatter_Hex_ID) and (yield from self.skills.Mesmer.DominationMagic.Shatter_Hex()):
            return True

        if self.IsSkillEquipped(Air_of_Superiority_ID) and (yield from self.skills.Any.NoAttribute.Air_of_Superiority()):
            return True

        if self.IsSkillEquipped(Flesh_of_My_Flesh_ID):
            dead_ally_id: int = Routines.Agents.GetDeadAlly(Range.Spellcast.value)
            if dead_ally_id and (yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Flesh_of_My_Flesh_ID,
                target_agent_id=dead_ally_id,
                log=False,
                aftercast_delay=250,
            )):
                return True

        if self.IsSkillEquipped(Breath_of_the_Great_Dwarf_ID) and (yield from self.skills.Any.NoAttribute.Breath_of_the_Great_Dwarf()):
            return True

        if not Routines.Checks.Agents.InAggro():
            return False

        if self.IsSkillEquipped(Ebon_Vanguard_Assassin_Support_ID) and (yield from self.skills.Any.NoAttribute.Ebon_Vanguard_Assassin_Support()):
            return True

        if self.IsSkillEquipped(Cry_of_Frustration_ID) and (yield from self.skills.Mesmer.DominationMagic.Cry_of_Frustration()):
            return True

        if self.IsSkillEquipped(Power_Drain_ID) and (yield from self.skills.Mesmer.DominationMagic.Power_Drain()):
            return True
        
        if self.IsSkillEquipped(Energy_Surge_ID) and (yield from self.skills.Mesmer.DominationMagic.Energy_Surge()):
            return True

        if self.IsSkillEquipped(Overload_ID) and (yield from self.skills.Mesmer.DominationMagic.Overload()):
            return True

        if self.IsSkillEquipped(Unnatural_Signet_ID) and (yield from self.skills.Mesmer.DominationMagic.Unnatural_Signet()):
            return True

        yield
