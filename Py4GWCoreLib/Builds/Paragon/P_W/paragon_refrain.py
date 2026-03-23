from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate

Heroic_Refrain_ID = Skill.GetID("Heroic_Refrain")
Theyre_on_Fire_ID = Skill.GetID("Theyre_on_Fire")
Hasty_Refrain_ID = Skill.GetID("Hasty_Refrain")
Aggressive_Refrain_ID = Skill.GetID("Aggressive_Refrain")
Stand_Your_Ground_ID = Skill.GetID("Stand_Your_Ground")
For_Great_Justice_ID = Skill.GetID("For_Great_Justice")
Theres_Nothing_to_Fear_ID = Skill.GetID("Theres_Nothing_to_Fear")
Save_Yourselves_luxon_ID = Skill.GetID("Save_Yourselves_luxon")
Save_Yourselves_kurzick_ID = Skill.GetID("Save_Yourselves_kurzick")
Never_Surrender_ID = Skill.GetID("Never_Surrender")
Blazing_Finale_ID = Skill.GetID("Blazing_Finale")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
Ebon_Battle_Standard_of_Wisdom_ID = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")
Protectors_Defense_ID = Skill.GetID("Protectors_Defense")


class Paragon_Refrain(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Defensive Refrain",
            required_primary=Profession.Paragon,
            required_secondary=Profession.Warrior,
            template_code="OQGkUNlnpiy0ZNQYPWNm72G4VhoH",
            required_skills=[
                Heroic_Refrain_ID,
                Theyre_on_Fire_ID,
                Theres_Nothing_to_Fear_ID,
                Aggressive_Refrain_ID

            ],
            optional_skills=[
                Save_Yourselves_luxon_ID,
                Save_Yourselves_kurzick_ID,
                Hasty_Refrain_ID,
                Never_Surrender_ID,
                Aggressive_Refrain_ID,
                Stand_Your_Ground_ID,
                For_Great_Justice_ID,
                Blazing_Finale_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Ebon_Battle_Standard_of_Wisdom_ID,
                Protectors_Defense_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return False
        yield from self.AutoAttack()

        if self.IsSkillEquipped(Heroic_Refrain_ID) and (yield from self.skills.Paragon.Leadership.Heroic_Refrain()):
            return True

        if self.IsSkillEquipped(Theyre_on_Fire_ID) and (yield from self.skills.Paragon.Leadership.Theyre_on_Fire()):
            return True

        if not Routines.Checks.Agents.InAggro():
            return False

        if self.IsSkillEquipped(Theres_Nothing_to_Fear_ID) and (yield from self.skills.Any.NoAttribute.Theres_Nothing_to_Fear()):
            return True

        if self.IsSkillEquipped(Aggressive_Refrain_ID) and (yield from self.skills.Paragon.Leadership.Aggressive_Refrain()):
            return True

        if self.IsSkillEquipped(For_Great_Justice_ID) and (yield from self.skills.Warrior.NoAttribute.For_Great_Justice()):
            return True

        if self.IsSkillEquipped(Stand_Your_Ground_ID) and (yield from self.skills.Paragon.Command.Stand_Your_Ground()):
            return True

        if self.IsSkillEquipped(Save_Yourselves_luxon_ID) and (yield from self.skills.Any.NoAttribute.Save_Yourselves_luxon()):
            return True

        if self.IsSkillEquipped(Save_Yourselves_kurzick_ID) and (yield from self.skills.Any.NoAttribute.Save_Yourselves_kurzick()):
            return True

        if self.IsSkillEquipped(Hasty_Refrain_ID) and (yield from self.skills.Paragon.Motivation.Hasty_Refrain()):
            return True

        if self.IsSkillEquipped(Never_Surrender_ID) and (yield from self.skills.Paragon.Motivation.Never_Surrender()):
            return True

        if self.IsSkillEquipped(Blazing_Finale_ID) and (yield from self.skills.Paragon.Motivation.Blazing_Finale()):
            return True

        if self.IsSkillEquipped(Protectors_Defense_ID) and (yield from self.skills.Warrior.NoAttribute.Protectors_Defense()):
            return True

        if self.IsSkillEquipped(Ebon_Vanguard_Assassin_Support_ID) and (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()):
            return True

        if self.IsSkillEquipped(Ebon_Battle_Standard_of_Wisdom_ID) and (yield from self.skills.Any.NoAttribute.Ebon_Battle_Standard_of_Wisdom()):
            return True

        if (yield from self.AutoAttack()):
            return True

        yield
