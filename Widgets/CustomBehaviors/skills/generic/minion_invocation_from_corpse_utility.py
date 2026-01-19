from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Agent, AgentArray, Range, Player
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class MinionInvocationFromCorpseUtility(CustomSkillUtilityBase):

    def __init__(self,
    event_bus: EventBus,
    skill: CustomSkill,
    current_build: list[CustomSkill],
    score_definition: ScoreStaticDefinition = ScoreStaticDefinition(65),
    mana_required_to_cast: int = 5,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
    ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScoreStaticDefinition = score_definition

    def _get_targets(self) -> list[int]:

        def _AllowedAlliegance(agent_id):
            _, alliegance = Agent.GetAllegiance(agent_id)

            if (alliegance == "Ally" or
                alliegance == "Neutral" or
                alliegance == "Enemy" or
                alliegance == "NPC/Minipet"
                ):
                return True
            return False

        agent_ids: list[int] = AgentArray.GetAgentArray()
        agent_ids = AgentArray.Filter.ByDistance(agent_ids, Player.GetXY(), Range.Spellcast.value)
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: not Agent.HasBossGlow(agent_id)) # filter out boss minions (that corpses never disappear)
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: Agent.IsDead(agent_id) and not Agent.IsSpirit(agent_id) and not Agent.IsSpawned(agent_id))
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, _AllowedAlliegance)

        # we order by distance ASC
        agent_ids = AgentArray.Sort.ByDistance(agent_ids, Player.GetXY())

        return agent_ids

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        targets = self._get_targets()
        if len(targets) == 0: return None
        target = targets[0]
        if target is None: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        targets = self._get_targets()
        if len(targets) == 0: return BehaviorResult.ACTION_SKIPPED
        target = targets[0]
        if target is None: return BehaviorResult.ACTION_SKIPPED
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result
    
    @override
    def customized_debug_ui(self, current_state):
        targets = self._get_targets()

        for agent_id in targets:
            PyImGui.bullet_text(f"agent_id : {agent_id} | name : {Agent.GetNameByID(agent_id)} | is_spawned : {Agent.IsSpawned(agent_id)}")

        return