from typing import Any, Generator, Callable, override

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range, Player, Routines
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class DiscordUtility(CustomSkillUtilityBase):

    def __init__(self,
                event_bus: EventBus,
                current_build: list[CustomSkill],
                score_definition: ScoreStaticDefinition = ScoreStaticDefinition(70),
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Discord"),
            in_game_build=current_build,
            score_definition=score_definition)
        
        self.score_definition: ScorePerAgentQuantityDefinition = score_definition

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
         
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
                    within_range=Range.Spellcast,
                    condition=lambda agent_id: Agent.IsHexed(agent_id) and Agent.IsConditioned(agent_id),
                    sort_key=(TargetingOrder.HP_ASC, TargetingOrder.CASTER_THEN_MELEE))

        return targets