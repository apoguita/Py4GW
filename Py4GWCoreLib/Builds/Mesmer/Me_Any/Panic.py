from dataclasses import dataclass

from Py4GWCoreLib import Agent, Player, Profession, Range, Routines, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import HexRemovalPriority, SkillsTemplate


Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Panic_ID = Skill.GetID("Panic")
Mistrust_ID = Skill.GetID("Mistrust")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
Cry_of_Pain_ID = Skill.GetID("Cry_of_Pain")
Unnatural_Signet_ID = Skill.GetID("Unnatural_Signet")
Cry_of_Frustration_ID = Skill.GetID("Cry_of_Frustration")
Overload_ID = Skill.GetID("Overload")
Power_Drain_ID = Skill.GetID("Power_Drain")
Shatter_Hex_ID = Skill.GetID("Shatter_Hex")
Flesh_of_My_Flesh_ID = Skill.GetID("Flesh_of_My_Flesh")
Breath_of_the_Great_Dwarf_ID = Skill.GetID("Breath_of_the_Great_Dwarf")


@dataclass(slots=True)
class _PanicBarSnapshot:
    in_aggro: bool = False
    enemy_in_spellcast: bool = False
    enemy_casting: bool = False
    enemy_casting_spell: bool = False
    enemy_casting_spell_or_chant: bool = False
    dead_ally_in_spellcast: int = 0
    player_energy_pct: float = 1.0


class Panic(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Panic",
            required_primary=Profession.Mesmer,
            template_code="OQBDAssjJ0QOM9AAAAAAAAA",
            required_skills=[
                Panic_ID,
                Cry_of_Frustration_ID,
                Mistrust_ID,
            ],
            optional_skills=[
                Air_of_Superiority_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                Cry_of_Pain_ID,
                Unnatural_Signet_ID,
                Power_Drain_ID,
                Shatter_Hex_ID,
                Overload_ID,
                Flesh_of_My_Flesh_ID,
                Breath_of_the_Great_Dwarf_ID
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetBlockedSkills([
            Air_of_Superiority_ID,
            Panic_ID,
            Mistrust_ID,
            Ebon_Vanguard_Assassin_Support_ID,
            Cry_of_Pain_ID,
            Unnatural_Signet_ID,
            Cry_of_Frustration_ID,
            Overload_ID,
            Power_Drain_ID,
            Shatter_Hex_ID,
        ])
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _get_bar_snapshot(self) -> _PanicBarSnapshot:
        snapshot = _PanicBarSnapshot()
        snapshot.in_aggro = bool(self.IsInAggro())
        snapshot.dead_ally_in_spellcast = int(Routines.Agents.GetDeadAlly(Range.Spellcast.value) or 0)
        snapshot.player_energy_pct = float(Agent.GetEnergy(Player.GetAgentID()))

        if not snapshot.in_aggro:
            return snapshot

        snapshot.enemy_in_spellcast = bool(Routines.Agents.GetNearestEnemy(Range.Spellcast.value))
        if snapshot.enemy_in_spellcast:
            snapshot.enemy_casting = bool(Routines.Targeting.GetEnemyCasting(Range.Spellcast.value))
            snapshot.enemy_casting_spell = bool(Routines.Targeting.GetEnemyCastingSpell(Range.Spellcast.value))
            snapshot.enemy_casting_spell_or_chant = bool(Routines.Targeting.GetEnemyCastingSpellOrChant(Range.Spellcast.value))

        return snapshot

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return False

        snapshot = self._get_bar_snapshot()

        if (snapshot.in_aggro or self.IsCloseToAggro()) and (yield from self.skills.Any.PvE.Air_of_Superiority()):
            return True

        if (yield from self.skills.Any.NoAttribute.Breath_of_the_Great_Dwarf()):
            return True

        if self.IsSkillEquipped(Flesh_of_My_Flesh_ID):
            dead_ally_id = snapshot.dead_ally_in_spellcast
            if dead_ally_id and (yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Flesh_of_My_Flesh_ID,
                target_agent_id=dead_ally_id,
                log=False,
                aftercast_delay=250,
            )):
                return True

        if not snapshot.in_aggro:
            return False

        if snapshot.enemy_casting_spell_or_chant and (yield from self.skills.Mesmer.InspirationMagic.Power_Drain(energy_threshold_pct=0.30)):
            return True

        if (yield from self.skills.Mesmer.DominationMagic.Shatter_Hex(min_priority=HexRemovalPriority.HIGH)):
            return True

        if snapshot.enemy_in_spellcast and (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()):
            return True

        if snapshot.enemy_in_spellcast and (yield from self.skills.Mesmer.DominationMagic.Panic()):
            return True

        if snapshot.enemy_casting and (yield from self.skills.Mesmer.DominationMagic.Cry_of_Frustration()):
            return True

        if snapshot.enemy_casting_spell_or_chant and (yield from self.skills.Mesmer.InspirationMagic.Power_Drain()):
            return True

        if snapshot.player_energy_pct >= 0.50 and (yield from self.skills.Mesmer.DominationMagic.Shatter_Hex(min_priority=HexRemovalPriority.MEDIUM)):
            return True

        if snapshot.enemy_casting and (yield from self.skills.Mesmer.DominationMagic.Overload()):
            return True

        if snapshot.enemy_casting and (yield from self.skills.Any.PvE.Cry_of_Pain(require_mesmer_hex=True)):
            return True

        if snapshot.enemy_casting_spell and (yield from self.skills.Mesmer.DominationMagic.Mistrust()):
            return True

        if snapshot.enemy_in_spellcast and (yield from self.skills.Mesmer.DominationMagic.Unnatural_Signet()):
            return True

        if snapshot.enemy_in_spellcast and (yield from self.skills.Any.PvE.Cry_of_Pain()):
            return True

        if snapshot.player_energy_pct >= 0.70 and (yield from self.skills.Mesmer.DominationMagic.Shatter_Hex()):
            return True

        yield
