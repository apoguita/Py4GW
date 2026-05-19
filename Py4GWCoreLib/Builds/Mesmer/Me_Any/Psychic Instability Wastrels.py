import time
from dataclasses import dataclass

from Py4GWCoreLib import Agent, Player, Profession, Range, Routines, BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.Py4GWcorelib import Utils
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI as HeroAIBuild
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


_WASTRELS_DEMISE_COOLDOWN_S: float = 5.0
_WASTRELS_WORRY_COOLDOWN_S: float = 3.0


def _agent_is_knocked_down(agent_id: int) -> bool:
    model_state = Agent.GetModelState(agent_id)
    if model_state == 1104 or (model_state & 0x400):
        return True
    return bool(Agent.IsKnockedDown(agent_id))


def _pick_wastrels_target(
    skill_id: int,
    last_cast: dict[int, float],
    cooldown_s: float,
    *,
    require_knockdown: bool = False,
    exclude_knockdown: bool = False,
    min_energy_abs: int = 0,
) -> int:
    if require_knockdown and exclude_knockdown:
        return 0

    if min_energy_abs > 0:
        player_id = Player.GetAgentID()
        current_energy = Agent.GetEnergy(player_id) * Agent.GetMaxEnergy(player_id)
        if current_energy < min_energy_abs:
            return 0

    aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(skill_id) or Range.Adjacent.value
    now = time.monotonic()

    def _not_on_cooldown(agent_id: int) -> bool:
        last = last_cast.get(agent_id)
        return last is None or now - last >= cooldown_s

    player_pos = Player.GetXY()
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Spellcast.value)
    enemy_array = AgentArray.Filter.ByCondition(
        enemy_array,
        lambda agent_id: Agent.IsValid(agent_id) and Agent.IsAlive(agent_id) and _not_on_cooldown(agent_id),
    )
    if not enemy_array:
        return 0

    def _cluster_sort_key(agent_id: int) -> tuple[int, float]:
        return (
            -Routines.Targeting.CountNearbyEnemies(agent_id, aoe_range),
            Utils.Distance(player_pos, Agent.GetXY(agent_id)),
        )

    if require_knockdown:
        kd_enemies = [a for a in enemy_array if _agent_is_knocked_down(a)]
        if not kd_enemies:
            return 0
        return sorted(kd_enemies, key=_cluster_sort_key)[0]

    if exclude_knockdown:
        enemy_array = [a for a in enemy_array if not _agent_is_knocked_down(a)]
        if not enemy_array:
            return 0

    non_casting = [a for a in enemy_array if not Agent.IsCasting(a)]
    if non_casting:
        return sorted(non_casting, key=_cluster_sort_key)[0]

    return sorted(enemy_array, key=_cluster_sort_key)[0]


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

        self._wastrels_demise_last_cast: dict[int, float] = {}
        self._wastrels_worry_last_cast: dict[int, float] = {}

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

    def _pick_demise(self, *, require_knockdown: bool = False, exclude_knockdown: bool = False, min_energy_abs: int = 0) -> int:
        now = time.monotonic()
        self._wastrels_demise_last_cast = {a: t for a, t in self._wastrels_demise_last_cast.items() if now - t < _WASTRELS_DEMISE_COOLDOWN_S}
        return _pick_wastrels_target(Wastrels_Demise_ID, self._wastrels_demise_last_cast, _WASTRELS_DEMISE_COOLDOWN_S, require_knockdown=require_knockdown, exclude_knockdown=exclude_knockdown, min_energy_abs=min_energy_abs)

    def _pick_worry(self, *, require_knockdown: bool = False, exclude_knockdown: bool = False, min_energy_abs: int = 0) -> int:
        now = time.monotonic()
        self._wastrels_worry_last_cast = {a: t for a, t in self._wastrels_worry_last_cast.items() if now - t < _WASTRELS_WORRY_COOLDOWN_S}
        return _pick_wastrels_target(Wastrels_Worry_ID, self._wastrels_worry_last_cast, _WASTRELS_WORRY_COOLDOWN_S, require_knockdown=require_knockdown, exclude_knockdown=exclude_knockdown, min_energy_abs=min_energy_abs)

    def _track_demise(self, target_agent_id: int) -> None:
        self._wastrels_demise_last_cast[target_agent_id] = time.monotonic()

    def _track_worry(self, target_agent_id: int) -> None:
        self._wastrels_worry_last_cast[target_agent_id] = time.monotonic()

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return False

        snapshot = self._get_bar_snapshot()

        if not snapshot.in_aggro:
            return False

        # 1 + 2 – Wastrel's hexes on knocked-down enemies (highest priority).
        # Per-second AoE ticks of Demise are more time-sensitive so it goes first.
        target = self._pick_demise(require_knockdown=True)
        if target and (yield from self.skills.Mesmer.DominationMagic.Wastrels_Demise(target_agent_id=target)):
            self._track_demise(target)
            return True

        target = self._pick_worry(require_knockdown=True)
        if target and (yield from self.skills.Mesmer.DominationMagic.Wastrels_Worry(target_agent_id=target)):
            self._track_worry(target)
            return True

        # 3 – Power Drain before PI when energy is critical (<=30%).
        if snapshot.enemy_casting_spell_or_chant and (
            yield from self.skills.Mesmer.InspirationMagic.Power_Drain(energy_threshold_pct=0.30)
        ):
            return True

        # 4 – Interrupt + AoE knockdown to create the next KD window.
        # PI interrupts any skill or spell; method handles the casting check internally.
        if snapshot.enemy_casting and (yield from self.skills.Mesmer.DominationMagic.Psychic_Instability()):
            return True

        # 5 – Cry of Frustration on any casting enemy.
        if snapshot.enemy_casting and (yield from self.skills.Mesmer.DominationMagic.Cry_of_Frustration()):
            return True

        # 6 – Cry of Pain (prefer targets already hexed with a mesmer hex).
        if snapshot.enemy_casting and (yield from self.skills.Any.PvE.Cry_of_Pain(require_mesmer_hex=True)):
            return True

        if snapshot.enemy_in_spellcast and (yield from self.skills.Any.PvE.Cry_of_Pain()):
            return True

        # 7 – Mistrust on a spell caster.
        if snapshot.enemy_casting_spell and (yield from self.skills.Mesmer.DominationMagic.Mistrust()):
            return True

        # 8 – Power Spike interrupt.
        if snapshot.enemy_casting_spell_or_chant and (yield from self.skills.Mesmer.InspirationMagic.Power_Spike()):
            return True

        # 9 – Power Drain for energy refill when below 70%.
        if snapshot.enemy_casting_spell_or_chant and (yield from self.skills.Mesmer.InspirationMagic.Power_Drain()):
            return True

        # 10 – Wastrel's hexes on non-KD enemies as low-priority damage.
        # Require at least 10 energy so the build does not drain itself dry.
        target = self._pick_demise(min_energy_abs=10, exclude_knockdown=True)
        if target and (yield from self.skills.Mesmer.DominationMagic.Wastrels_Demise(target_agent_id=target)):
            self._track_demise(target)
            return True

        target = self._pick_worry(min_energy_abs=10, exclude_knockdown=True)
        if target and (yield from self.skills.Mesmer.DominationMagic.Wastrels_Worry(target_agent_id=target)):
            self._track_worry(target)
            return True

        yield
