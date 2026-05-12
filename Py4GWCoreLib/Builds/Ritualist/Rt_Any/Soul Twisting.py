from dataclasses import dataclass

from Py4GWCoreLib import Agent, Player, Profession, Routines, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import HexRemovalPriority, SkillsTemplate


Soul_Twisting_ID = Skill.GetID("Soul_Twisting")
Boon_of_Creation_ID = Skill.GetID("Boon_of_Creation")
Shelter_ID = Skill.GetID("Shelter")
Union_ID = Skill.GetID("Union")
Displacement_ID = Skill.GetID("Displacement")
Summon_Spirits_kurzick_ID = Skill.GetID("Summon_Spirits_kurzick")
Summon_Spirits_luxon_ID = Skill.GetID("Summon_Spirits_luxon")
Armor_of_Unfeeling_ID = Skill.GetID("Armor_of_Unfeeling")
Spirits_Gift_ID = Skill.GetID("Spirits_Gift")
Breath_of_the_Great_Dwarf_ID = Skill.GetID("Breath_of_the_Great_Dwarf")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
Ebon_Battle_Standard_of_Wisdom_ID = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")
I_Am_Unstoppable_ID = Skill.GetID("I_Am_Unstoppable")
Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Remove_Hex_ID = Skill.GetID("Remove_Hex")


@dataclass(slots=True)
class _SoulTwistingSnapshot:
    in_aggro: bool = False
    close_to_aggro: bool = False
    player_energy_pct: float = 1.0


class Soul_Twisting(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Soul Twisting",
            required_primary=Profession.Ritualist,
            template_code="OAOj4MgMJPYTr3jDAAAAAAAAAA",
            required_skills=[
                Soul_Twisting_ID,
                Shelter_ID,
                Union_ID,
            ],
            optional_skills=[
                Boon_of_Creation_ID,
                Displacement_ID,
                Summon_Spirits_kurzick_ID,
                Summon_Spirits_luxon_ID,
                Armor_of_Unfeeling_ID,
                Spirits_Gift_ID,
                Breath_of_the_Great_Dwarf_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Ebon_Battle_Standard_of_Wisdom_ID,
                I_Am_Unstoppable_ID,
                Air_of_Superiority_ID,
                Remove_Hex_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetBlockedSkills([
            Soul_Twisting_ID,
            Boon_of_Creation_ID,
            Shelter_ID,
            Union_ID,
            Displacement_ID,
            Summon_Spirits_kurzick_ID,
            Summon_Spirits_luxon_ID,
            Armor_of_Unfeeling_ID,
            Spirits_Gift_ID,
            Breath_of_the_Great_Dwarf_ID,
            Ebon_Vanguard_Assassin_Support_ID,
            Ebon_Battle_Standard_of_Wisdom_ID,
            I_Am_Unstoppable_ID,
            Air_of_Superiority_ID,
            Remove_Hex_ID,
        ])
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _get_bar_snapshot(self) -> _SoulTwistingSnapshot:
        snapshot = _SoulTwistingSnapshot()
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

        if (yield from self.skills.Monk.NoAttribute.Remove_Hex(min_priority=HexRemovalPriority.HIGH)):
            return True

        if (
            self.IsSkillEquipped(Air_of_Superiority_ID)
            and (snapshot.in_aggro or self.IsCloseToAggro())
            and (yield from self.skills.Any.PvE.Air_of_Superiority())
        ):
            return True

        if snapshot.in_aggro and (yield from self.skills.Any.NoAttribute.I_Am_Unstoppable()):
            return True

        if (yield from self.skills.Ritualist.SpawningPower.Boon_of_Creation()):
            return True

        if (yield from self.skills.Ritualist.SpawningPower.Soul_Twisting()):
            return True

        if self.IsSkillEquipped(Summon_Spirits_kurzick_ID) and (yield from self.skills.Any.NoAttribute.Summon_Spirits_kurzick()):
            return True

        if self.IsSkillEquipped(Summon_Spirits_luxon_ID) and (yield from self.skills.Any.NoAttribute.Summon_Spirits_luxon()):
            return True

        if (yield from self.skills.Ritualist.Communing.Shelter()):
            return True

        if (yield from self.skills.Ritualist.Communing.Union()):
            return True

        if (yield from self.skills.Ritualist.Communing.Displacement()):
            return True

        if snapshot.player_energy_pct >= 0.50 and (yield from self.skills.Monk.NoAttribute.Remove_Hex(min_priority=HexRemovalPriority.MEDIUM)):
            return True

        if (yield from self.skills.Ritualist.Communing.Armor_of_Unfeeling()):
            return True

        if (yield from self.skills.Ritualist.SpawningPower.Spirits_Gift()):
            return True

        if not snapshot.in_aggro:
            return False

        if snapshot.player_energy_pct >= 0.40 and (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()):
            return True

        if (yield from self.skills.Any.NoAttribute.Ebon_Battle_Standard_of_Wisdom()):
            return True

        if (yield from self.skills.Any.NoAttribute.Breath_of_the_Great_Dwarf()):
            return True

        if snapshot.player_energy_pct >= 0.70 and (yield from self.skills.Monk.NoAttribute.Remove_Hex()):
            return True

        return False
