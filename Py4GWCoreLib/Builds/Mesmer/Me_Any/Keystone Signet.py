from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate

Symbolic_Celerity_ID = Skill.GetID("Symbolic_Celerity")
Keystone_Signet_ID = Skill.GetID("Keystone_Signet")
Unnatural_Signet_ID = Skill.GetID("Unnatural_Signet")
Signet_of_Clumsiness_ID = Skill.GetID("Signet_of_Clumsiness")
Smite_Hex_ID = Skill.GetID("Smite_Hex")
Hex_Eater_Signet_ID = Skill.GetID("Hex_Eater_Signet")
Castigation_Signet_ID = Skill.GetID("Castigation_Signet")
Bane_Signet_ID = Skill.GetID("Bane_Signet")
Breath_of_the_Great_Dwarf_ID = Skill.GetID("Breath_of_the_Great_Dwarf")


class KeystoneSignet(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Keystone Signet",
            required_primary=Profession.Mesmer,
            template_code="OQITEZJZVSpYHEqQsGAAAAAAAAA",
            required_skills=[
                Symbolic_Celerity_ID,
                Keystone_Signet_ID,
                Unnatural_Signet_ID,
                Signet_of_Clumsiness_ID,
            ],
            optional_skills=[
                Smite_Hex_ID,
                Hex_Eater_Signet_ID,
                Castigation_Signet_ID,
                Bane_Signet_ID,
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

        if (yield from self.skills.Mesmer.FastCasting.Symbolic_Celerity()):
            return True
        
        if self.IsSkillEquipped(Hex_Eater_Signet_ID):
            if (yield from self.skills.Mesmer.InspirationMagic.Hex_Eater_Signet()):
                return True

        if self.IsSkillEquipped(Smite_Hex_ID):
            if (yield from self.skills.Monk.SmitingPrayers.Smite_Hex()):
                return True

        if self.IsSkillEquipped(Breath_of_the_Great_Dwarf_ID) and (yield from self.skills.Any.NoAttribute.Breath_of_the_Great_Dwarf()):
            return True

        if not Routines.Checks.Agents.InAggro():
            return False

        if (yield from self.skills.Mesmer.FastCasting.Keystone_Signet()):
            return True

        if (yield from self.skills.Mesmer.DominationMagic.Unnatural_Signet()):
            return True

        if (yield from self.skills.Mesmer.IllusionMagic.Signet_of_Clumsiness()):
            return True

        if self.IsSkillEquipped(Castigation_Signet_ID) and (yield from self.skills.Monk.SmitingPrayers.Castigation_Signet()):
            return True

        if self.IsSkillEquipped(Bane_Signet_ID) and (yield from self.skills.Monk.SmitingPrayers.Bane_Signet()):
            return True

        return False
