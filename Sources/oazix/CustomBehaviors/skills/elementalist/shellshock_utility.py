# File: `Sources.oazix.CustomBehaviors/skills/elementalist/shellshock_utility.py`
from typing import Any, Generator, override, List
import time

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.helpers.trackers import cracked_armor_tracker, glimmer_tracker
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class ShellShockUtility(CustomSkillUtilityBase):
    """
    Single-target Shell Shock utility.
    - Avoids hexed targets (won't remove hex).
    - Ignores targets that currently have the Glimmering_Mark buff.
    - Uses a short per-agent lock only while casting.
    """

    def __init__(self,
                 event_bus: EventBus,
                 current_build: list[CustomSkill],
                 score_definition: ScoreStaticDefinition = ScoreStaticDefinition(54),
                 mana_required_to_cast: int = 10,
                 allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
                 ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("Shell_Shock"),
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)

        self.score_definition: ScoreStaticDefinition = score_definition

    def _get_lock_key(self, agent_id: int) -> str:
        return f"ShellShock_{agent_id}"

    def _get_all_targets(self) -> List[custom_behavior_helpers.SortableAgentData]:
        # single-target selection: avoid hexed foes and targets with Glimmering_Mark
        return custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
            within_range=Range.Spellcast,
            condition=lambda agent_id: (not glimmer_tracker.had_glimmer_recently(agent_id) and not cracked_armor_tracker.has_cracked_armor(agent_id)),
            sort_key=(TargetingOrder.HP_DESC,),
            range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id)
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        targets = self._get_all_targets()
        if len(targets) == 0:
            return None

        chosen = targets[0]

        lock_key = self._get_lock_key(chosen.agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().is_lock_taken(lock_key):
            return None

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        enemies = self._get_all_targets()
        if len(enemies) == 0:
            return BehaviorResult.ACTION_SKIPPED

        target = enemies[0]

        lock_key = self._get_lock_key(target.agent_id)
        if CustomBehaviorParty().get_shared_lock_manager().try_aquire_lock(lock_key) == False:
            return BehaviorResult.ACTION_SKIPPED

        try:
            result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
            if result == BehaviorResult.ACTION_PERFORMED:
                cracked_armor_tracker.record_cracked_armor(target.agent_id, 17) # it's for 12 air magic
        finally:
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
        return result
