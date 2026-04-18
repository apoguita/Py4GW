from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate

Ineptitude_ID = Skill.GetID("Ineptitude")
Wandering_Eye_ID = Skill.GetID("Wandering_Eye")
Signet_of_Clumsiness_ID = Skill.GetID("Signet_of_Clumsiness")
Arcane_Conundrum_ID = Skill.GetID("Arcane_Conundrum")
Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
Ebon_Battle_Standard_of_Wisdom_ID = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")
Power_Drain_ID = Skill.GetID("Power_Drain")
Drain_Enchantment_ID = Skill.GetID("Drain_Enchantment")


class Ineptitude(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Ineptitude",
            required_primary=Profession.Mesmer,
            template_code="OQBDAawDSvAIg5ZkAAAAAAAAAA",
            required_skills=[
                Ineptitude_ID,
                Wandering_Eye_ID,
                Signet_of_Clumsiness_ID,
            ],
            optional_skills=[
                Arcane_Conundrum_ID,
                Air_of_Superiority_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Ebon_Battle_Standard_of_Wisdom_ID,
                Power_Drain_ID,
                Drain_Enchantment_ID,
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

        if (
            self.IsSkillEquipped(Air_of_Superiority_ID)
            and (Routines.Checks.Agents.InAggro() or self.IsCloseToAggro())
            and (yield from self.skills.Any.PvE.Air_of_Superiority())
        ):
            return True

        if not Routines.Checks.Agents.InAggro():
            return False

        if (yield from self.skills.Mesmer.InspirationMagic.Power_Drain(energy_threshold_pct=0.30)):
            return True

        if (yield from self.skills.Mesmer.InspirationMagic.Drain_Enchantment(energy_threshold_pct=0.30)):
            return True

        if self.IsSkillEquipped(Ebon_Vanguard_Assassin_Support_ID) and (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()):
            return True
        
        if (yield from self.skills.Mesmer.IllusionMagic.Ineptitude()):
            return True

        if (yield from self.skills.Mesmer.InspirationMagic.Power_Drain(energy_threshold_pct=0.50)):
            return True

        if (yield from self.skills.Mesmer.InspirationMagic.Drain_Enchantment(energy_threshold_pct=0.50)):
            return True

        if (yield from self.skills.Mesmer.IllusionMagic.Wandering_Eye()):
            return True

        if self.IsSkillEquipped(Arcane_Conundrum_ID) and (yield from self.skills.Mesmer.IllusionMagic.Arcane_Conundrum()):
            return True

        if (yield from self.skills.Mesmer.IllusionMagic.Signet_of_Clumsiness()):
            return True

        if (yield from self.skills.Mesmer.InspirationMagic.Power_Drain()):
            return True

        if (yield from self.skills.Mesmer.InspirationMagic.Drain_Enchantment()):
            return True

        if self.IsSkillEquipped(Ebon_Battle_Standard_of_Wisdom_ID) and (yield from self.CastSkillID(
            skill_id=Ebon_Battle_Standard_of_Wisdom_ID,
            log=False,
            aftercast_delay=250,
        )):
            return True

        yield
