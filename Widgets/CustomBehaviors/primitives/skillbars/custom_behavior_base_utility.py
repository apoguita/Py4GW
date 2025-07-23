from abc import abstractmethod
from collections import deque
from typing import List, Generator, Any, override

from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_skillbar_management import CustomBehaviorSkillbarManagement
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.generic.hero_ai_utility import HeroAiUtility
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.constants import DEBUG

class CustomBehaviorBaseUtility():
    """
    This class serves as a blueprint for creating custom combat behaviors that
    are compatible with specific game builds. Subclasses implementing this class
    should define the template and the combat behavior logic.
    """

    # todo-list :
    # targeting : GetPartyTarget
    # priority behavior if few mana
    # do-not-overlap mode => with shared-memory-lock / or shared-memory-queue


    def __init__(self):
        super().__init__()
        self._generator_handle = self._handle()
        self.__is_enabled:bool = False
        self.__previously_attempted_skills: deque[CustomSkill] = deque(maxlen=40)
        self.skillbar_management: CustomBehaviorSkillbarManagement = CustomBehaviorSkillbarManagement()
        self.__final_skills_list: list[CustomSkillUtilityBase] | None = None

    def enable(self):
        self.__is_enabled = True

    def disable(self):
        self.__is_enabled = False

    # computed

    def get_state(self) -> BehaviorState:
        return self._fetch_state()

    def get_final_state(self) -> BehaviorState:
        party_forced_state:BehaviorState|None = CustomBehaviorParty().get_party_forced_state()
        account_state = self.get_state()
        final_state:BehaviorState = account_state if party_forced_state is None else party_forced_state
        return final_state

    def get_is_enabled(self) -> bool:
        return self.__is_enabled

    def get_final_is_enabled(self) -> bool:
        party_forced_state:bool = CustomBehaviorParty().get_party_is_enable()
        final_is_enabled:bool = party_forced_state and self.__is_enabled
        return final_is_enabled

    # abstract/overridable

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

    @property
    @abstractmethod
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        '''
        just used to detect if a build match current in-game build.
        '''
        pass

    #build management

    def count_matches_between_custom_behavior_and_in_game_build(self) -> int:
            '''
            count the number of skills in the custom behavior (skills_required_in_behavior) that are in the in-game build.
            '''
            result:int = 0
            in_game_build: dict[int, CustomSkill] = self.skillbar_management.get_in_game_build()
            custom_behavior_build: list[CustomSkill] = self.skills_required_in_behavior

            for custom_skill in custom_behavior_build:
                if in_game_build.get(custom_skill.skill_id) is not None:
                    result +=1

            return result

    def get_skills_final_list(self) -> list[CustomSkillUtilityBase]:
        '''
        get the full list of skills that are in game.
        with their utility implementation.
        with the additional autonomous skills (auto-attack)
        calculated once, then cached.
        '''

        if self.__final_skills_list is not None:
            return self.__final_skills_list
        
        in_game_build_by_skill_id: dict[int, CustomSkill] = self.skillbar_management.get_in_game_build()
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

    def is_custom_behavior_match_in_game_build(self) -> bool:
        if not GLOBAL_CACHE.Map.IsOutpost(): return True

        utility_build_full:list[CustomSkillUtilityBase] = self.get_skills_final_list()
        is_completed:bool = self.complete_build_with_generic_skills
        in_game_build:dict[int, CustomSkill] = self.skillbar_management.get_in_game_build()

        # check if ingame slots match our definitions
        for skill in utility_build_full:
            if skill.custom_skill.skill_id != 0: #meaning it's an autonomous skill
                skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(skill.custom_skill.skill_slot)
                if skill_id != skill.custom_skill.skill_id:
                    if DEBUG: print(f"Slot {skill.custom_skill.skill_slot} doesn't match skill {skill.custom_skill.skill_id}, the behavior must be refreshed.")
                    return False

        # two case

        if is_completed:
            # check if all ingame skills are in the behavior.
            for skill_id in in_game_build.keys():
                if skill_id not in [item.custom_skill.skill_id for item in utility_build_full]:
                    if DEBUG: print(f"{skill_id} from in-game build doesn't exist in the behavior, the behavior must be refreshed.")
                    return False

        if not is_completed:
            #  1/ check if all skills in the behavior are part of the in-game build.
            for skill in utility_build_full:
                if skill.custom_skill.skill_id == 0: continue
                if skill.custom_skill.skill_id not in in_game_build.keys():
                    if DEBUG: print(f"{skill.custom_skill.skill_id} that is present in the behavior is not part of the in-game build, the behavior must be refreshed.")
                    return False

            #  2/ check if we added a new ingame skill that should be part of the behavior.
            for skill_id in in_game_build.keys():
                if skill_id not in [item.custom_skill.skill_id for item in utility_build_full]:
                    if skill_id in [item.custom_skill.skill_id for item in self.skills_allowed_in_behavior]:
                        if DEBUG: print(f"{skill_id} should be present in the behavior, the behavior must be refreshed.")
                        return False

        return True

    # orchestration

    def act(self):

        if not self.get_final_is_enabled(): return
        if not Routines.Checks.Map.MapValid(): return
        if not self.is_custom_behavior_match_in_game_build(): 
            print("Custom behavior doesn't match in game build, you are not allowed to perform behavior.act().")
            return

        if self.get_final_is_enabled():
            account_email = GLOBAL_CACHE.Player.GetAccountEmail()
            hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
            if hero_ai_options is not None:
                hero_ai_options.Combat = False
                hero_ai_options.Following = hero_ai_options.Following
                hero_ai_options.Looting = hero_ai_options.Looting

        final_state:BehaviorState = self.get_final_state()

        if final_state == BehaviorState.IDLE:
            return
        else:
            try:
                next(self._generator_handle)
            except StopIteration:
                print(f"act is not expected to StopIteration.")
            except Exception as e:
                print(f"act is not expected to exit : {e}")

    def _fetch_state(self) -> BehaviorState:

        if self.get_final_is_enabled() == False:
            return BehaviorState.IDLE

        if not Routines.Checks.Map.MapValid():
            return BehaviorState.IDLE

        if GLOBAL_CACHE.Map.IsOutpost():
            return BehaviorState.IDLE

        if custom_behavior_helpers.Targets.is_party_in_combat():
            return BehaviorState.IN_AGGRO

        if custom_behavior_helpers.Targets.is_player_in_aggro():
            return BehaviorState.IN_AGGRO

        if custom_behavior_helpers.Targets.is_player_close_to_combat():
            return BehaviorState.CLOSE_TO_AGGRO

        return BehaviorState.FAR_FROM_AGGRO

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

    def _handle(self) -> Generator[Any | None, Any | None, None]:
        
        while True:
            
            utility_scores: list[tuple[CustomSkillUtilityBase, float | None]] = self.get_all_scores()

            # #take highest scoring
            highest_scoring : tuple[CustomSkillUtilityBase, float | None] = utility_scores[0]
            if highest_scoring[1] is None:
                yield
                continue

            # Try to execute the highest scoring utility
            yield from highest_scoring[0].execute(self.get_final_state())
            self.__previously_attempted_skills.append(highest_scoring[0].custom_skill)

            yield