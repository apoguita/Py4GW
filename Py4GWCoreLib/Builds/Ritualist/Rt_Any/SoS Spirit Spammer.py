from dataclasses import dataclass

from Py4GWCoreLib import Agent, Player, Profession, Routines, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Signet_of_Spirits_ID = Skill.GetID("Signet_of_Spirits")
Bloodsong_ID = Skill.GetID("Bloodsong")
Painful_Bond_ID = Skill.GetID("Painful_Bond")
Vampirism_ID = Skill.GetID("Vampirism")
Summon_Spirits_kurzick_ID = Skill.GetID("Summon_Spirits_kurzick")
Summon_Spirits_luxon_ID = Skill.GetID("Summon_Spirits_luxon")
Spirit_Siphon_ID = Skill.GetID("Spirit_Siphon")
Great_Dwarf_Weapon_ID = Skill.GetID("Great_Dwarf_Weapon")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
Technobabble_ID = Skill.GetID("Technobabble")
Armor_of_Unfeeling_ID = Skill.GetID("Armor_of_Unfeeling")


@dataclass(slots=True)
class _SoSSpiritSpammerBarSnapshot:
    in_aggro: bool = False
    close_to_aggro: bool = False
    player_energy_pct: float = 1.0


class SoS_Spirit_Spammer(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="SoS Spirit Spammer",
            required_primary=Profession.Ritualist,
            template_code="OACiIyk8cNLnVTAAAAAAAAAA",
            required_skills=[
                Signet_of_Spirits_ID,
                Bloodsong_ID,
                Painful_Bond_ID,
            ],
            optional_skills=[
                Vampirism_ID,
                Summon_Spirits_kurzick_ID,
                Summon_Spirits_luxon_ID,
                Spirit_Siphon_ID,
                Great_Dwarf_Weapon_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Technobabble_ID,
                Armor_of_Unfeeling_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetBlockedSkills([
            Signet_of_Spirits_ID,
            Bloodsong_ID,
            Painful_Bond_ID,
            Vampirism_ID,
            Summon_Spirits_kurzick_ID,
            Summon_Spirits_luxon_ID,
            Spirit_Siphon_ID,
            Great_Dwarf_Weapon_ID,
            Ebon_Vanguard_Assassin_Support_ID,
            Technobabble_ID,
            Armor_of_Unfeeling_ID,
        ])
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _get_bar_snapshot(self) -> _SoSSpiritSpammerBarSnapshot:
        snapshot = _SoSSpiritSpammerBarSnapshot()
        snapshot.in_aggro = bool(self.IsInAggro())
        snapshot.close_to_aggro = snapshot.in_aggro or self.IsCloseToAggro()
        snapshot.player_energy_pct = float(Agent.GetEnergy(Player.GetAgentID()))
        return snapshot

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return False

        snapshot = self._get_bar_snapshot()
        if not snapshot.close_to_aggro:
            return False

        # Emergency energy refill: cast Spirit Siphon when below 30% energy
        # before committing to the rest of the rotation.
        if self.IsSkillEquipped(Spirit_Siphon_ID) and (yield from self.skills.Ritualist.ChannelingMagic.Spirit_Siphon(max_self_energy_pct=0.30)):
            return True

        if self.IsSkillEquipped(Ebon_Vanguard_Assassin_Support_ID) and (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()):
            return True

        if self.IsSkillEquipped(Technobabble_ID) and (yield from self.skills.Any.PvE.Technobabble()):
            return True

        if self.IsSkillEquipped(Great_Dwarf_Weapon_ID) and (yield from self.skills.Any.NoAttribute.Great_Dwarf_Weapon()):
            return True

        if (yield from self.skills.Ritualist.ChannelingMagic.Painful_Bond()):
            return True

        if (yield from self.skills.Ritualist.ChannelingMagic.Signet_of_Spirits()):
            return True

        if self.IsSkillEquipped(Vampirism_ID) and (yield from self.skills.Any.PvE.Vampirism()):
            return True

        if (yield from self.skills.Ritualist.ChannelingMagic.Bloodsong()):
            return True

        if self.IsSkillEquipped(Armor_of_Unfeeling_ID) and (yield from self.skills.Ritualist.ChannelingMagic.Armor_of_Unfeeling()):
            return True

        if (yield from self.skills.Any.NoAttribute.Summon_Spirits()):
            return True

        # Opportunistic energy refill: skip when at or above 70% energy.
        if self.IsSkillEquipped(Spirit_Siphon_ID) and (yield from self.skills.Ritualist.ChannelingMagic.Spirit_Siphon(max_self_energy_pct=0.70)):
            return True

        return False
