# python
from typing import Any, Generator, List, Optional, override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class PreparationTargetedUtility(CustomSkillUtilityBase):
    """
    Cast a preparation skill (via a prep utility) and immediately cast a follow-up
    targeted skill at the same target. The class is intentionally simple:
    - `_evaluate` returns the configured score if any target utility currently has a valid evaluation.
    - `_execute` finds a target from the first available target utility, `yield from`'s the prep cast,
      then `yield from`'s the follow-up targeted cast. Always implemented as a generator to avoid StopIteration.
    """

    def __init__(
        self,
        event_bus: EventBus,
        prep_utility: CustomSkillUtilityBase,
        followup_skill: CustomSkill,
        target_utilities: List[CustomSkillUtilityBase],
        current_build: list[CustomSkill],
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(60),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO],
    ) -> None:
        # Track the prep skill as this utility's skill so helper checks work consistently.
        super().__init__(
            event_bus=event_bus,
            skill=prep_utility.custom_skill,
            in_game_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states,
        )
        self.prep_utility = prep_utility
        self.followup_skill = followup_skill
        self.target_utilities = target_utilities
        self.score_definition = score_definition

    def _find_target_agent_id(self) -> Optional[int]:
        """
        Attempt to extract a target agent id from a utility using common method names.
        Returns the first found valid agent id or None.
        """
        for util in self.target_utilities:
            # prefer utilities that have a dedicated single-target getter
            if hasattr(util, "_get_target"):
                try:
                    t = util._get_target()  # could be int or None
                except Exception:
                    t = None
                if isinstance(t, int):
                    return t

            # utilities that return lists of SortableAgentData
            for fn in ("_get_all_targets", "_get_targets", "_get_targets_list"):
                if hasattr(util, fn):
                    try:
                        lst = getattr(util, fn)()
                    except Exception:
                        lst = None
                    if lst and len(lst) > 0:
                        first = lst[0]
                        # support both raw agent id or SortableAgentData with agent_id attribute
                        if isinstance(first, int):
                            return first
                        if hasattr(first, "agent_id"):
                            return first.agent_id
        return None

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        # If the prep skill isn't present in the in-game build, don't try
        if not any(getattr(s, "skill_id", None) == self.custom_skill.skill_id for s in self.in_game_build):
            return None

        # If any target utility currently evaluates to a usable score, allow the prep skill
        for util in self.target_utilities:
            try:
                score = util._evaluate(current_state, previously_attempted_skills)
            except Exception:
                score = None
            if score is not None:
                return self.score_definition.get_score()
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        # find a valid target agent id from target utilities
        target_agent = self._find_target_agent_id()
        if target_agent is None:
            return BehaviorResult.ACTION_SKIPPED

        # cast the preparation skill (generator-safe)
        prep_result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        # if prep failed or was skipped, skip follow-up
        if prep_result is None or prep_result == BehaviorResult.ACTION_SKIPPED:
            return prep_result if prep_result is not None else BehaviorResult.ACTION_SKIPPED

        # cast the follow-up targeted skill at the same agent
        follow_result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.followup_skill, target_agent_id=target_agent)
        return follow_result
