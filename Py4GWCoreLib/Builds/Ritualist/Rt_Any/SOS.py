from Py4GWCoreLib import Profession, Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Signet_of_Spirits_ID = Skill.GetID("Signet_of_Spirits")
Bloodsong_ID = Skill.GetID("Bloodsong")
Vampirism_ID = Skill.GetID("Vampirism")
Gaze_of_Fury_ID = Skill.GetID("Gaze_of_Fury")
Painful_Bond_ID = Skill.GetID("Painful_Bond")
Armor_of_Unfeeling_ID = Skill.GetID("Armor_of_Unfeeling")
Summon_Spirits_Kurzick_ID = Skill.GetID("Summon_Spirits_kurzick")
Summon_Spirits_Luxon_ID = Skill.GetID("Summon_Spirits_luxon")


class SOS(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Signet of Spirits",
            required_primary=Profession.Ritualist,
            template_code="OACiIykMdNVO5DOACAAAAAAAAA",  # placeholder — needs in-game verification
            required_skills=[
                Signet_of_Spirits_ID,
                Bloodsong_ID,
                Vampirism_ID,
            ],
            optional_skills=[
                Gaze_of_Fury_ID,
                Painful_Bond_ID,
                Armor_of_Unfeeling_ID,
                Summon_Spirits_Kurzick_ID,
                Summon_Spirits_Luxon_ID,
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

        # Summon spirits to regroup (highest priority)
        if self.IsSkillEquipped(Summon_Spirits_Kurzick_ID) and (yield from self.skills.Ritualist.ChannelingMagic.Summon_Spirits()):
            return True
        if self.IsSkillEquipped(Summon_Spirits_Luxon_ID) and (yield from self.skills.Ritualist.ChannelingMagic.Summon_Spirits()):
            return True

        # Core spirits
        if (yield from self.skills.Ritualist.ChannelingMagic.Signet_of_Spirits()):
            return True
        if (yield from self.skills.Ritualist.ChannelingMagic.Vampirism()):
            return True
        if (yield from self.skills.Ritualist.ChannelingMagic.Bloodsong()):
            return True

        if not Routines.Checks.Agents.InAggro():
            return False

        # Combat optional
        if (yield from self.skills.Ritualist.ChannelingMagic.Gaze_of_Fury()):
            return True
        if (yield from self.skills.Ritualist.ChannelingMagic.Painful_Bond()):
            return True

        # Defensive
        if (yield from self.skills.Ritualist.Communing.Armor_of_Unfeeling()):
            return True

        # Common PvE
        if (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()):
            return True

        return False
