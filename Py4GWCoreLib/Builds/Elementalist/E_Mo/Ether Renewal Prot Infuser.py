from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Aura_of_Restoration_ID = Skill.GetID("Aura_of_Restoration")
Ether_Renewal_ID = Skill.GetID("Ether_Renewal")
Protective_Spirit_ID = Skill.GetID("Protective_Spirit")
Reversal_of_Fortune_ID = Skill.GetID("Reversal_of_Fortune")
Breath_of_the_Great_Dwarf_ID = Skill.GetID("Breath_of_the_Great_Dwarf")
Great_Dwarf_Weapon_ID = Skill.GetID("Great_Dwarf_Weapon")
Vital_Blessing_ID = Skill.GetID("Vital_Blessing")
Infuse_Health_ID = Skill.GetID("Infuse_Health")


class Ether_Renewal_Prot_Infuser(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Ether Renewal Prot Infuser",
            required_primary=Profession.Elementalist,
            required_secondary=Profession.Monk,
            template_code="OgNDwaTPHzse1iWAAAAAAA",
            required_skills=[
                Aura_of_Restoration_ID,
                Ether_Renewal_ID,
                Protective_Spirit_ID,
                Reversal_of_Fortune_ID,
            ],
            optional_skills=[
                Breath_of_the_Great_Dwarf_ID,
                Great_Dwarf_Weapon_ID,
                Vital_Blessing_ID,
                Infuse_Health_ID,
            ],
        )

        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _vital_blessing_self_upkeep(self):
        not_has_vital_blessing = lambda: not Routines.Checks.Effects.HasBuff(Player.GetAgentID(), Vital_Blessing_ID)

        if not self.IsSkillEquipped(Vital_Blessing_ID):
            return False
        if not not_has_vital_blessing():
            return False

        return (yield from self.CastSkillID(
            skill_id=Vital_Blessing_ID,
            extra_condition=not_has_vital_blessing,
            log=False,
            aftercast_delay=250,
            target_agent_id=Player.GetAgentID(),
        ))

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        if (yield from self.skills.Elementalist.EnergyStorage.Aura_of_Restoration()):
            return True

        if self.IsSkillEquipped(Vital_Blessing_ID) and (yield from self._vital_blessing_self_upkeep()):
            return True

        if self.IsSkillEquipped(Breath_of_the_Great_Dwarf_ID) and (yield from self.skills.Any.NoAttribute.Breath_of_the_Great_Dwarf()):
            return True

        if not Routines.Checks.Agents.InAggro():
            return False

        self.UpdatePartyHealthMonitor(sample_interval_ms=150)

        if self.IsSkillEquipped(Infuse_Health_ID) and (yield from self.skills.Monk.HealingPrayers.Infuse_Health()):
            return True

        if self.IsSkillEquipped(Great_Dwarf_Weapon_ID) and (yield from self.skills.Any.NoAttribute.Great_Dwarf_Weapon()):
            return True

        if (yield from self.skills.Monk.ProtectionPrayers.Protective_Spirit()):
            return True

        if (yield from self.skills.Monk.ProtectionPrayers.Reversal_of_Fortune()):
            return True

        if (yield from self.skills.Elementalist.EnergyStorage.Ether_Renewal()):
            return True

        return False
