from typing import Any, Generator, override

from Py4GWCoreLib import Agent, AgentArray, Player, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class JununduFeastUtility(CustomSkillUtilityBase):

    def __init__(
        self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(68),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
    ) -> None:
        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Junundu_Feast"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )

        self.score_definition: ScoreStaticDefinition = score_definition
    
    def _get_lock_key(self, agent_id: int) -> str:
        return f"Junundu_Feast_{agent_id}"

    def _get_targets(self) -> list[int]:
        """
        Get nearby corpses that can be consumed.
        Filters for dead agents that are not bosses, spirits, spawns, or minions.
        """
        def _allowed_allegiance(agent_id):
            _, allegiance = Agent.GetAllegiance(agent_id)
            if (allegiance == "Ally" or
                allegiance == "Neutral" or
                allegiance == "Enemy" or
                allegiance == "NPC/Minipet"):
                return True
            return False

        agent_ids: list[int] = AgentArray.GetAgentArray()
        agent_ids = AgentArray.Filter.ByDistance(agent_ids, Player.GetXY(), Range.Spellcast.value)
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: 
                                                  Agent.IsDead(agent_id) and 
                                                  not Agent.HasBossGlow(agent_id) and
                                                  not Agent.IsSpirit(agent_id) and 
                                                  not Agent.IsSpawned(agent_id) and 
                                                  not Agent.IsMinion(agent_id))
        
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, _allowed_allegiance)
        agent_ids = AgentArray.Sort.ByDistance(agent_ids, Player.GetXY())

        return agent_ids

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        targets = self._get_targets()
        if len(targets) == 0: return None
        target_agent_id = targets[0]

        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(self._get_lock_key(target_agent_id)):
            return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        targets = self._get_targets()
        if len(targets) == 0: return BehaviorResult.ACTION_SKIPPED
        target_agent_id = targets[0]

        lock_key = self._get_lock_key(target_agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=200) == False:
            return BehaviorResult.ACTION_SKIPPED

        # Execute the skill - do NOT release lock on success
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)

        if result == BehaviorResult.ACTION_SKIPPED:
            # Release lock only on skip
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)

        return result

