from typing import Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Player, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.sortable_agent_data import SortableAgentData
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class LeechSignetUtility(CustomSkillUtilityBase):

    def __init__(self,
                    event_bus: EventBus,
                    current_build: list[CustomSkill],
                    score_definition: ScoreStaticDefinition = ScoreStaticDefinition(82),
            ) -> None:

            super().__init__(
                event_bus=event_bus,
                skill=CustomSkill("Leech_Signet"),
                in_game_build=current_build,
                score_definition=score_definition)
            
            self.score_definition: ScoreStaticDefinition = score_definition

    def detect_casting_enemies(self) -> list[SortableAgentData]:
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=lambda agent_id: Agent.IsCasting(agent_id) and GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkillID(agent_id)) >= 1.00, # only skills that are longer than 1s. too much changes to fail otherwise
            sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.CASTER_THEN_MELEE),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id)
        )
        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if Agent.GetEnergy(Player.GetAgentID()) > 0.6: return None
        targets = self.detect_casting_enemies()
        if len(targets) == 0: return None
        return self.score_definition.get_score()
    
    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        targets = self.detect_casting_enemies()
        if len(targets) == 0: return BehaviorResult.ACTION_SKIPPED
        target_id = targets[0].agent_id

        # https://wiki.guildwars.com/wiki/Game_updates:2023
        # The odds that the skill will perform the interrupt are higher the longer you have targeted the player before executing the skill, up to approximately ¼ second (depending on latency). 
        # The reasoning behind this change is to make these skills more strategic in nature and, not coincidentally, more difficult for bots to execute. 

        Player.ChangeTarget(target_id)
        yield from custom_behavior_helpers.Helpers.wait_for(251)
        
        if not Agent.IsCasting(target_id): return BehaviorResult.ACTION_SKIPPED
        Player.ChangeTarget(target_id)
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        # result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target_id)
        
        return result