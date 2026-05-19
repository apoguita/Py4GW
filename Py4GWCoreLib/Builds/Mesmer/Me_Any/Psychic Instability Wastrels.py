from dataclasses import dataclass

from Py4GWCoreLib import Agent, Player, Profession, Range, Routines, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Psychic_Instability_ID = Skill.GetID("Psychic_Instability")
Wastrels_Demise_ID = Skill.GetID("Wastrels_Demise")
Wastrels_Worry_ID = Skill.GetID("Wastrels_Worry")
Power_Spike_ID = Skill.GetID("Power_Spike")
Cry_of_Frustration_ID = Skill.GetID("Cry_of_Frustration")
Power_Drain_ID = Skill.GetID("Power_Drain")
Mistrust_ID = Skill.GetID("Mistrust")
Cry_of_Pain_ID = Skill.GetID("Cry_of_Pain")


@dataclass(slots=True)
class _PsychicInstabilityWastrelsBarSnapshot:
    in_aggro: bool = False
    enemy_in_spellcast: bool = False
    enemy_casting: bool = False
    enemy_casting_spell: bool = False
    enemy_casting_spell_or_chant: bool = False
    player_energy_pct: float = 1.0


class Psychic_Instability_Wastrels(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Psychic Instability Wastrel's",
            required_primary=Profession.Mesmer,
            template_code="OQBTAUBPwJEeTlBXgcQGAAAAA",
            required_skills=[
                Psychic_Instability_ID,
                Wastrels_Demise_ID,
                Wastrels_Worry_ID,
            ],
            optional_skills=[
                Power_Spike_ID,
                Cry_of_Frustration_ID,
                Power_Drain_ID,
                Mistrust_ID,
                Cry_of_Pain_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAIBuild(standalone_fallback=True))
        self.SetBlockedSkills([
            Psychic_Instability_ID,
            Wastrels_Demise_ID,
            Wastrels_Worry_ID,
            Power_Spike_ID,
            Cry_of_Frustration_ID,
            Power_Drain_ID,
            Mistrust_ID,
            Cry_of_Pain_ID,
        ])
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _get_bar_snapshot(self) -> _PsychicInstabilityWastrelsBarSnapshot:
        snapshot = _PsychicInstabilityWastrelsBarSnapshot()
        snapshot.in_aggro = bool(self.IsInAggro())
        snapshot.player_energy_pct = float(Agent.GetEnergy(Player.GetAgentID()))

        if not snapshot.in_aggro:
            return snapshot

        snapshot.enemy_in_spellcast = bool(Routines.Agents.GetNearestEnemy(Range.Spellcast.value))
        if snapshot.enemy_in_spellcast:
            snapshot.enemy_casting = bool(Routines.Targeting.GetEnemyCasting(Range.Spellcast.value))
            snapshot.enemy_casting_spell = bool(Routines.Targeting.GetEnemyCastingSpell(Range.Spellcast.value))
            snapshot.enemy_casting_spell_or_chant = bool(
                Routines.Targeting.GetEnemyCastingSpellOrChant(Range.Spellcast.value)
            )

        return snapshot

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return False

        snapshot = self._get_bar_snapshot()

        if not snapshot.in_aggro:
            return False

        # 1 + 2 – Wastrel's hexes on knocked-down enemies (highest priority).
        # Per-second AoE ticks of Demise are more time-sensitive so it goes first.
        if (yield from self.skills.Mesmer.DominationMagic.Wastrels_Demise(require_knockdown=True)):
            return True

        if (yield from self.skills.Mesmer.DominationMagic.Wastrels_Worry(require_knockdown=True)):
            return True

        # 3 – Interrupt + AoE knockdown to create the next KD window.
        # PI interrupts any skill or spell; method handles the casting check internally.
        if snapshot.enemy_casting and (yield from self.skills.Mesmer.DominationMagic.Psychic_Instability()):
            return True

        # 4 – Cry of Frustration on any casting enemy.
        if snapshot.enemy_casting and (yield from self.skills.Mesmer.DominationMagic.Cry_of_Frustration()):
            return True

        # 5 – Cry of Pain (prefer targets already hexed with a mesmer hex).
        if snapshot.enemy_casting and (yield from self.skills.Any.PvE.Cry_of_Pain(require_mesmer_hex=True)):
            return True

        if snapshot.enemy_in_spellcast and (yield from self.skills.Any.PvE.Cry_of_Pain()):
            return True

        # 6 – Mistrust on a spell caster.
        if snapshot.enemy_casting_spell and (yield from self.skills.Mesmer.DominationMagic.Mistrust()):
            return True

        # 7 – Power Spike interrupt.
        if snapshot.enemy_casting_spell_or_chant and (yield from self.skills.Mesmer.InspirationMagic.Power_Spike()):
            return True

        # 8 – Power Drain for energy refill.
        if snapshot.enemy_casting_spell_or_chant and (yield from self.skills.Mesmer.InspirationMagic.Power_Drain()):
            return True

        # 9 – Wastrel's hexes on non-KD enemies as low-priority damage.
        # Require at least 10 energy so the build does not drain itself dry.
        if (yield from self.skills.Mesmer.DominationMagic.Wastrels_Demise(min_energy_abs=10)):
            return True

        if (yield from self.skills.Mesmer.DominationMagic.Wastrels_Worry(min_energy_abs=10)):
            return True

        yield
