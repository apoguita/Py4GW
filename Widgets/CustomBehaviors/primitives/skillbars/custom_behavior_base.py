from abc import abstractmethod
from typing import List, Generator, Any

from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.constants import DEBUG


class CustomBehaviorBase:
    """
    This class serves as a blueprint for creating custom combat behaviors that
    are compatible with specific game builds. Subclasses implementing this class
    should define the template and the combat behavior logic.
    """

    # todo-list :
    # targeting : GetPartyTarget
    # priority behavior if few mana
    # do-not-overlap mode => with shared-memory-lock / or shared-memory-queue

    def __init__(self, cached_data: CacheData):
        self._generator_handle_in_aggro = self._handle_in_aggro(cached_data)
        self._generator_handle_close_to_aggro = self._handle_close_to_aggro(cached_data)
        self._generator_handle_far_from_aggro = self._handle_far_from_aggro(cached_data)
        self.__cache_data = cached_data
        self.__is_enabled:bool = False

    def enable(self):
        self.__is_enabled = True

    def disable(self):
        self.__is_enabled = False

    # override & computed

    def get_state(self) -> BehaviorState:
        return self._fetch_state(self.__cache_data)

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

    # build

    @staticmethod
    def get_in_game_build() -> dict[int, "CustomSkill"]:
        """
        return in-game build of the player as a dictionary.
        list length can vary.
        """
        ordered_skills_by_skill_id: dict[int, "CustomSkill"] = {}
        for i in range(8):
            skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(i + 1)
            if skill_id == 0: continue
            skill_name =  GLOBAL_CACHE.Skill.GetName(skill_id)
            custom_skill = CustomSkill(skill_name)
            ordered_skills_by_skill_id[skill_id] = custom_skill

        return ordered_skills_by_skill_id

    @property
    @abstractmethod
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        '''
        just used to detect if a build match current in-game build.
        '''
        pass

    def get_generic_behavior_build(self) -> List["CustomSkill"]:
        """
        get skills that are not customized, they'll use classic heroAI behavior.
        ordered by HeroAI.priority
        """

        def __get_custom_behavior_build() -> dict[int, "CustomSkill"]:
            custom_behavior_build = self.skills_required_in_behavior
            skills_by_skill_id: dict[int, "CustomSkill"] = {}
            for custom_behavior_build_skill in custom_behavior_build:
                skills_by_skill_id[custom_behavior_build_skill.skill_id] = custom_behavior_build_skill

            return skills_by_skill_id

        from Widgets import HeroAI
        self.__cache_data.combat_handler.PrioritizeSkills()
        generic_skills:List["HeroAI.CombatClass.SkillData"] = self.__cache_data.combat_handler.skills

        custom_skills:dict[int, "CustomSkill"] = __get_custom_behavior_build()
        not_customized_skills: List["CustomSkill"] = []

        for skill in generic_skills:
            if custom_skills.get(skill.skill_id) is None:
                not_customized_skills.append(CustomSkill(GLOBAL_CACHE.Skill.GetName(skill.skill_id)))

        return not_customized_skills

    def count_matches_between_custom_behavior_match_in_game_build(self) -> int:
        result:int = 0
        in_game_build: dict[int, "CustomSkill"] = self.get_in_game_build()
        custom_behavior_build: List["CustomSkill"] = self.skills_required_in_behavior

        for custom_skill in custom_behavior_build:
            print(f"custom_skill: {custom_skill.skill_id} {custom_skill.skill_name}")
            if in_game_build.get(custom_skill.skill_id) is not None:
                print(f"match: {custom_skill.skill_id} {custom_skill.skill_name}")
                result +=1

        return result

    #orchestration

    def act(self, cached_data: CacheData):

        if not self.get_final_is_enabled(): return
        if not Routines.Checks.Map.MapValid(): return

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
        elif final_state == BehaviorState.IN_AGGRO:
            try:
                next(self._generator_handle_in_aggro)
            except StopIteration:
                print(f"act.IN_AGGRO is not expected to StopIteration.")
            except Exception as e:
                print(f"act.IN_AGGRO is not expected to exit : {e}")
        elif final_state == BehaviorState.CLOSE_TO_AGGRO:
            try:
                next(self._generator_handle_close_to_aggro)
            except StopIteration:
                print(f"act.CLOSE_TO_AGGRO is not expected to StopIteration.")
            except Exception as e:
                print(f"act.CLOSE_TO_AGGRO is not expected to exit : {e}")
        elif final_state == BehaviorState.FAR_FROM_AGGRO:
            try:
                next(self._generator_handle_far_from_aggro)
            except StopIteration:
                print(f"act.FAR_FROM_AGGRO is not expected to StopIteration.")
            except Exception as e:
                print(f"act.FAR_FROM_AGGRO is not expected to exit : {e}")
        else:
            print(f"State {final_state} is not managed.")

    #abstract/overridable

    def _fetch_state(self, cached_data: CacheData) -> BehaviorState:

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

    @abstractmethod
    def _handle_in_aggro(self, cached_data: CacheData) -> Generator[Any | None, Any | None, None]:
        pass

    @abstractmethod
    def _handle_far_from_aggro(self, cached_data: CacheData) -> Generator[Any | None, Any | None, None]:
        pass

    @abstractmethod
    def _handle_close_to_aggro(self, cached_data: CacheData) -> Generator[Any | None, Any | None, None]:
        pass