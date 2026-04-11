from Py4GWCoreLib import Profession, Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Soul_Twisting_ID = Skill.GetID("Soul_Twisting")
Boon_of_Creation_ID = Skill.GetID("Boon_of_Creation")
Shelter_ID = Skill.GetID("Shelter")
Union_ID = Skill.GetID("Union")
Displacement_ID = Skill.GetID("Displacement")
Armor_of_Unfeeling_ID = Skill.GetID("Armor_of_Unfeeling")
Spirits_Gift_ID = Skill.GetID("Spirits_Gift")
Summon_Spirits_Kurzick_ID = Skill.GetID("Summon_Spirits_kurzick")
Summon_Spirits_Luxon_ID = Skill.GetID("Summon_Spirits_luxon")


class Soul_Twisting(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Soul Twisting",
            required_primary=Profession.Ritualist,
            template_code="OACiAyk8gNtePOAAAAAAAAAA",
            required_skills=[
                Soul_Twisting_ID,
                Shelter_ID,
                Union_ID,
            ],
            optional_skills=[
                Displacement_ID,
                Boon_of_Creation_ID,
                Armor_of_Unfeeling_ID,
                Spirits_Gift_ID,
                Summon_Spirits_Kurzick_ID,
                Summon_Spirits_Luxon_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetOOCFn(self._run_ooc)
        self.SetCombatFn(self._run_combat)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _run_ooc(self):
        """Out of combat: maintain self-buffs only."""
        if not Routines.Checks.Skills.CanCast():
            return False

        if self.IsSkillEquipped(Soul_Twisting_ID) and (yield from self.skills.Ritualist.SpawningPower.Soul_Twisting()):
            return True
        if self.IsSkillEquipped(Boon_of_Creation_ID) and (yield from self.skills.Ritualist.SpawningPower.Boon_of_Creation()):
            return True
        if self.IsSkillEquipped(Spirits_Gift_ID) and (yield from self.skills.Ritualist.SpawningPower.Spirits_Gift()):
            return True

        return False

    def _run_combat(self):
        """In combat: full rotation — buffs, spirits, PvE skills."""
        if not Routines.Checks.Skills.CanCast():
            return False

        # Maintain self buffs (highest priority)
        if (yield from self.skills.Ritualist.SpawningPower.Soul_Twisting()):
            return True
        if (yield from self.skills.Ritualist.SpawningPower.Boon_of_Creation()):
            return True
        if (yield from self.skills.Ritualist.SpawningPower.Spirits_Gift()):
            return True

        # Summon spirits to regroup
        if self.IsSkillEquipped(Summon_Spirits_Kurzick_ID) and (yield from self.skills.Ritualist.ChannelingMagic.Summon_Spirits()):
            return True
        if self.IsSkillEquipped(Summon_Spirits_Luxon_ID) and (yield from self.skills.Ritualist.ChannelingMagic.Summon_Spirits()):
            return True

        # Protective spirits (Soul Twisting must be active — gated inside Communing)
        if (yield from self.skills.Ritualist.Communing.Shelter()):
            return True
        if (yield from self.skills.Ritualist.Communing.Union()):
            return True
        if (yield from self.skills.Ritualist.Communing.Displacement()):
            return True

        # Armor spirits
        if (yield from self.skills.Ritualist.Communing.Armor_of_Unfeeling()):
            return True

        # Common PvE
        if (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()):
            return True

        return False
