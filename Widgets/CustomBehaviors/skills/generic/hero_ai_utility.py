from typing import List, Any, Generator, Callable, override

from HeroAI.cache_data import CacheData
from HeroAI.combat import CombatClass
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase

class HeroAiUtility(CustomSkillUtilityBase):

    def __init__(
            self, 
            skill: CustomSkill, 
            current_build: list[CustomSkill], 
            score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.GENERIC_SKILL_HERO_AI.value), 
            mana_required_to_cast: int = 0
        ) -> None:

        super().__init__(
            skill=skill, 
            in_game_build=current_build, 
            score_definition=score_definition, 
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states= [BehaviorState.IN_AGGRO, BehaviorState.FAR_FROM_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        
        self.score_definition: ScoreStaticDefinition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        #it complexifies the code, but it's worth it
        cached_data: CacheData = CacheData()

        if cached_data.combat_handler is None: print("combat_handler is None")
        if cached_data.combat_handler.skills is None or len(cached_data.combat_handler.skills) == 0:
            try:
                cached_data.combat_handler.PrioritizeSkills()
            except Exception as e:
                print(f"echec {e}")
        if cached_data.combat_handler.skills is None or len(cached_data.combat_handler.skills) == 0:
            print("combat_handler.skills is None or empty, trying to prioritize skills")
            return None

        def find_order():
            skills = enumerate(cached_data.combat_handler.skills)
            for index, generic_skill in skills:
                if generic_skill.skill_id == self.custom_skill.skill_id:
                    return index  # Returning order (1-based index)
            return -1  # Return -1 if skill_id not found

        order = find_order()
        if order == -1: return None

        is_ooc_skill = cached_data.combat_handler.IsOOCSkill(order)
        if is_ooc_skill and current_state is BehaviorState.IN_AGGRO: return None

        is_ready_to_cast, target_agent_id = cached_data.combat_handler.IsReadyToCast(order)

        if not is_ready_to_cast: return None
        score = self.score_definition.get_score() + ((8 - order) * 0.01) # we do +0.xx only because we want to prioritize the skills that are not in the build based on heroAI
        return score

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill_generic(self.custom_skill)
        return result