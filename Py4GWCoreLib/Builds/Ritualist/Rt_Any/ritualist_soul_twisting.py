from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate

Soul_Twisting_ID = Skill.GetID("Soul_Twisting")
Shelter_ID = Skill.GetID("Shelter")
Union_ID = Skill.GetID("Union")
Boon_of_Creation_ID = Skill.GetID("Boon_of_Creation")
Displacement_ID = Skill.GetID("Displacement")
Summon_Spirits_kurzick_ID = Skill.GetID("Summon_Spirits_kurzick")
Summon_Spirits_luxon_ID = Skill.GetID("Summon_Spirits_luxon")
Armor_of_Unfeeling_ID = Skill.GetID("Armor_of_Unfeeling")
Breath_of_the_Great_Dwarf_ID = Skill.GetID("Breath_of_the_Great_Dwarf")
Great_Dwarf_Weapon_ID = Skill.GetID("Great_Dwarf_Weapon")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
Ebon_Battle_Standard_of_Wisdom_ID = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")
I_Am_Unstoppable_ID = Skill.GetID("I_Am_Unstoppable")
Spirits_Gift_ID = Skill.GetID("Spirits_Gift")


class Ritualist_Soul_Twisting(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Soul Twisting",
            required_primary=Profession.Ritualist,
            required_skills=[
                Soul_Twisting_ID,
                Shelter_ID,
                Union_ID,
                Boon_of_Creation_ID,
            ],
            optional_skills=[
                Displacement_ID,
                Summon_Spirits_kurzick_ID,
                Summon_Spirits_luxon_ID,
                Armor_of_Unfeeling_ID,
                Breath_of_the_Great_Dwarf_ID,
                Great_Dwarf_Weapon_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Ebon_Battle_Standard_of_Wisdom_ID,
                I_Am_Unstoppable_ID,
                Spirits_Gift_ID,
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

        if self.IsSkillEquipped(Soul_Twisting_ID) and (yield from self.skills.Ritualist.SpawningPower.Soul_Twisting()):
            return True

        if self.IsSkillEquipped(Boon_of_Creation_ID) and (yield from self.skills.Ritualist.SpawningPower.Boon_of_Creation()):
            return True

        if self.IsSkillEquipped(Armor_of_Unfeeling_ID) and (yield from self.skills.Ritualist.Communing.Armor_of_Unfeeling()):
            return True

        if self.IsSkillEquipped(Summon_Spirits_kurzick_ID) and (yield from self.skills.Any.NoAttribute.Summon_Spirits_kurzick()):
            return True

        if self.IsSkillEquipped(Summon_Spirits_luxon_ID) and (yield from self.skills.Any.NoAttribute.Summon_Spirits_luxon()):
            return True

        if not Routines.Checks.Agents.InAggro():
            return False

        if self.IsSkillEquipped(Shelter_ID) and (yield from self.skills.Ritualist.Communing.Shelter()):
            return True

        if self.IsSkillEquipped(Union_ID) and (yield from self.skills.Ritualist.Communing.Union()):
            return True

        if self.IsSkillEquipped(Displacement_ID) and (yield from self.skills.Ritualist.Communing.Displacement()):
            return True

        if self.IsSkillEquipped(Spirits_Gift_ID) and (yield from self.skills.Ritualist.SpawningPower.Spirits_Gift()):
            return True

        if self.IsSkillEquipped(I_Am_Unstoppable_ID) and (yield from self.skills.Any.NoAttribute.I_Am_Unstoppable()):
            return True

        if self.IsSkillEquipped(Breath_of_the_Great_Dwarf_ID) and (yield from self.skills.Any.NoAttribute.Breath_of_the_Great_Dwarf()):
            return True

        if self.IsSkillEquipped(Ebon_Vanguard_Assassin_Support_ID) and (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()):
            return True

        if self.IsSkillEquipped(Ebon_Battle_Standard_of_Wisdom_ID) and (yield from self.skills.Any.NoAttribute.Ebon_Battle_Standard_of_Wisdom()):
            return True

        if self.IsSkillEquipped(Great_Dwarf_Weapon_ID) and (yield from self.skills.Any.NoAttribute.Great_Dwarf_Weapon()):
            return True

        yield
