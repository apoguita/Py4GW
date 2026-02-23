from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, AgentArray, Player, Range, Utils
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.trackers import corpse_exploited_tracker
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class PutridExplosionUtility(CustomSkillUtilityBase):
    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScorePerAgentQuantityDefinition = ScorePerAgentQuantityDefinition(
            lambda enemy_qte: 83 if enemy_qte >= 2 else 35
        ),
        mana_required_to_cast: int = 5,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Putrid_Explosion"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition = score_definition

    def _get_corpses(self) -> list[tuple[int, int, float]]:
        corpses = AgentArray.GetAgentArray()
        corpses = AgentArray.Filter.ByDistance(corpses, Player.GetXY(), Range.Spellcast.value)
        corpses = AgentArray.Filter.ByCondition(
            corpses,
            lambda agent_id: Agent.IsDead(agent_id)
            and not Agent.HasBossGlow(agent_id)
            and not Agent.IsSpirit(agent_id)
            and not Agent.IsSpawned(agent_id)
            and not Agent.IsMinion(agent_id)
            and not corpse_exploited_tracker.was_corpse_exploited_recently(agent_id),
        )

        enemies = AgentArray.GetEnemyArray()
        enemies = AgentArray.Filter.ByDistance(enemies, Player.GetXY(), Range.Spellcast.value)
        enemies = AgentArray.Filter.ByCondition(enemies, lambda agent_id: Agent.IsAlive(agent_id))

        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id)
        player_pos = Player.GetXY()
        result: list[tuple[int, int, float]] = []

        for corpse_id in corpses:
            corpse_pos = Agent.GetXY(corpse_id)
            enemy_count = 0
            for enemy_id in enemies:
                if Utils.Distance(corpse_pos, Agent.GetXY(enemy_id)) <= aoe_range:
                    enemy_count += 1
            corpse_distance = Utils.Distance(player_pos, corpse_pos)
            result.append((corpse_id, enemy_count, corpse_distance))

        result.sort(key=lambda x: (-x[1], x[2]))
        return result

    def _get_best_target(self) -> tuple[int, int] | None:
        corpses = self._get_corpses()
        if len(corpses) == 0:
            return None
        corpse_id, enemy_count, _ = corpses[0]
        return corpse_id, enemy_count

    @override
    def _evaluate(
        self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]
    ) -> float | None:
        best_target = self._get_best_target()
        if best_target is None:
            return None

        _, enemy_count = best_target
        return self.score_definition.get_score(enemy_count)

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        best_target = self._get_best_target()
        if best_target is None:
            return BehaviorResult.ACTION_SKIPPED

        corpse_id, _ = best_target
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(
            self.custom_skill, corpse_id
        )

        # Record that this corpse was exploited
        if result == BehaviorResult.ACTION_PERFORMED:
            corpse_exploited_tracker.record_corpse_exploited(corpse_id)

        return result

