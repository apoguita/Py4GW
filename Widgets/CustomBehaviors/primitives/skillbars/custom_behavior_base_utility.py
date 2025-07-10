from abc import abstractmethod
from collections import deque
from typing import List, Generator, Any, override

from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base import CustomBehaviorBase
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.generic.hero_ai_utility import HeroAiUtility
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.constants import DEBUG

class CustomBehaviorBaseUtility(CustomBehaviorBase):

    def __init__(self, cached_data: CacheData):
        super().__init__(cached_data)
        self.__cache_data = cached_data
        self.__previously_attempted_skills: deque[CustomSkill] = deque(maxlen=40)
        self.__final_skills_list: list[CustomSkillUtilityBase] | None = None

    @property
    @abstractmethod
    def complete_build_with_generic_skills(self) -> bool:
        '''
        if True, the utility behavior will complete the build with generic skills.
        otherwise, it will only use the skills that are allowed in the behavior (skills_allowed_in_behavior)
        '''
        return True

    @property
    @abstractmethod
    def additional_autonomous_skills(self) -> list[CustomSkillUtilityBase]:
        '''
        the list of skills that are autonomous.
        like auto-attack, movement, etc.
        they are not part of the behavior, but are executed by the behavior.
        '''
        return []

    @property
    @abstractmethod
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        '''
        the list of skills that are allowed in the behavior.
        if a skill is not in this list, 2 options : 
            - if complete_build_with_generic_skills is True, the behavior will complete the build with generic skills.
            - if False, the behavior will not use the skill at all.
        '''
        pass

    
    def get_utility_skills_only_final_list(self) -> list[CustomSkillUtilityBase]:
        '''
        get the full list of skills that are in game.
        with their utility implementation.
        without the additional autonomous skills (auto-attack)
        '''

        list = self.get_skills_final_list()
        filtered_list = []
        
        for skill in list:
            if skill in self.additional_autonomous_skills:
                continue
            filtered_list.append(skill)
        
        return filtered_list


    def get_skills_final_list(self) -> list[CustomSkillUtilityBase]:
        '''
        get the full list of skills that are in game.
        with their utility implementation.
        with the additional autonomous skills (auto-attack)
        '''

        if self.__final_skills_list is not None:
            return self.__final_skills_list
        
        in_game_build_by_skill_id: dict[int, CustomSkill] = CustomBehaviorBase.get_in_game_build()
        skills_allowed_in_behavior_by_skill_id: dict[int, CustomSkillUtilityBase] = {x.custom_skill.skill_id: x for x in self.skills_allowed_in_behavior}
        # skills_required_in_behavior: list[CustomSkill] = self.skills_required_in_behavior
        final_list: list[CustomSkillUtilityBase] = []

        for skill in in_game_build_by_skill_id.values():
            if skill is None: raise ValueError(f"Skill is None")
            if skill.skill_id == 0: raise ValueError(f"Skill {skill.skill_id} is not in the build")
            
            if skill.skill_id in skills_allowed_in_behavior_by_skill_id.keys():
                final_list.append(skills_allowed_in_behavior_by_skill_id[skill.skill_id])
            elif self.complete_build_with_generic_skills:
                final_list.append(HeroAiUtility(skill=skill, current_build=list(in_game_build_by_skill_id.values()), score_definition=ScoreStaticDefinition(0)))

        for skill in self.additional_autonomous_skills:
            final_list.append(skill)

        self.__final_skills_list = final_list
        return self.__final_skills_list

    @override
    def _handle_in_aggro(self, cached_data: CacheData) -> Generator[Any | None, Any | None, None]:
        return self._handle(cached_data)

    @override
    def _handle_far_from_aggro(self, cached_data: CacheData) -> Generator[Any | None, Any | None, None]:
        return self._handle(cached_data)

    @override
    def _handle_close_to_aggro(self, cached_data: CacheData) -> Generator[Any | None, Any | None, None]:
        return self._handle(cached_data)

    def get_all_scores(self) -> list[tuple[CustomSkillUtilityBase, float | None]]:
        # Evaluate all utilities
        utilities: list[CustomSkillUtilityBase] = self.get_skills_final_list()
        # for x in utilities:
        #     print(f"skill {x.custom_skill.skill_name}")
        
        utility_scores: list[tuple[CustomSkillUtilityBase, float | None]] = []
        for utility in utilities:
            score = utility.evaluate(self.get_final_state(), list(self.__previously_attempted_skills))
            utility_scores.append((utility, score))
        
        # Sort by score (highest first)
        utility_scores.sort(key=lambda x: x[1] if x[1] is not None else 0, reverse=True)
        return utility_scores

    def _handle(self, cached_data: CacheData) -> Generator[Any | None, Any | None, None]:
        
        while True:
            
            utility_scores: list[tuple[CustomSkillUtilityBase, float | None]] = self.get_all_scores()

            # #take highest scoring
            highest_scoring : tuple[CustomSkillUtilityBase, float | None] = utility_scores[0]
            if highest_scoring[1] is None:
                yield
                continue

            # Try to execute the highest scoring utility
            result = yield from highest_scoring[0].execute(cached_data, self.get_final_state())
            # if result == BehaviorResult.ACTION_PERFORMED:
            self.__previously_attempted_skills.append(highest_scoring[0].custom_skill)

            yield