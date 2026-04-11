from typing import Any, Generator, override


from Py4GWCoreLib import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class SaveYourselvesUtility(CustomSkillUtilityBase):

    LOCK_KEY = f"SaveYourselves"

    def __init__(self,
        event_bus: EventBus,
        skill: CustomSkill,
        current_build: list[CustomSkill],
        allies_health_less_than_percent: float = 2,
        allies_quantity_required: int = 2,
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(90),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScoreStaticDefinition = score_definition
        self.allies_health_less_than_percent: float = allies_health_less_than_percent
        self.allies_quantity_required: int = allies_quantity_required
        self.save_yourselves_duration_in_seconds: int = 6

    def _get_lock_key(self) -> str:
        return f"{SaveYourselvesUtility.LOCK_KEY}"

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(self._get_lock_key()): return None
        

        targets: list[custom_behavior_helpers.SortableAgentData] = custom_behavior_helpers.Targets.get_all_possible_allies_ordered_by_priority_raw(
            within_range=Range.Earshot.value,
            condition=lambda agent_id: Agent.GetHealth(agent_id) < self.allies_health_less_than_percent)
        
        if len(targets) == 0: return None
        if len(targets) < self.allies_quantity_required: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        lock_key = self._get_lock_key()
        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key, timeout_seconds=self.save_yourselves_duration_in_seconds) == False:
            yield
            return BehaviorResult.ACTION_SKIPPED
        
        # we take a lock for the duration of the skill, it's simplest way to ensure we don't overlap save yourselfs
        
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)

        # we do not release the lock, it will be released automatically at the end of the duration
        
        return result