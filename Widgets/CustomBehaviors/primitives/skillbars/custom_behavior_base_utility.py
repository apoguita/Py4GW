from abc import abstractmethod
from collections import deque
from typing import List, Generator, Any, override
import time

from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer, Timer
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.bus.event_bus import EVENT_BUS
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_skillbar_management import CustomBehaviorSkillbarManagement
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_history import UtilitySkillExecutionHistory
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Widgets.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Widgets.CustomBehaviors.skills.deamon.map_changed import MapChangedUtility
from Widgets.CustomBehaviors.skills.deamon.stuck_detection import StuckDetectionUtility
from Widgets.CustomBehaviors.skills.following.follow_flag_utility import FollowFlagUtility
from Widgets.CustomBehaviors.skills.following.follow_party_leader_utility import FollowPartyLeaderUtility
from Widgets.CustomBehaviors.skills.generic.hero_ai_utility import HeroAiUtility
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.constants import DEBUG
from Widgets.CustomBehaviors.skills.looting.loot_utility import LootUtility
from Widgets.CustomBehaviors.skills.looting.open_near_chest_utility import OpenNearChestUtility

class CustomBehaviorBaseUtility():
    """
    This class serves as a blueprint for creating custom combat behaviors that
    are compatible with specific game builds. Subclasses implementing this class
    should define the template and the combat behavior logic.
    """

    def __init__(self):
        super().__init__()
        self._generator_handle = self._handle()
        self.__is_enabled:bool = False
        self.__previously_attempted_skills: deque[CustomSkill] = deque(maxlen=40)
        self.skillbar_management: CustomBehaviorSkillbarManagement = CustomBehaviorSkillbarManagement()
        self.__final_skills_list: list[CustomSkillUtilityBase] | None = None
        self.skill_execution_history: deque[UtilitySkillExecutionHistory] = deque(maxlen=30)

        self.in_game_build: list[CustomSkill] = list(self.skillbar_management.get_in_game_build().values())

        self.__memoized_ordered_scores : list[tuple[CustomSkillUtilityBase, float | None]]
        self.__memoized_state : BehaviorState = BehaviorState.IDLE
        
        self.__injected_additional_utility_skills : list[CustomSkillUtilityBase] = list[CustomSkillUtilityBase]()

    def inject_additionnal_utility_skills(self, skill:CustomSkillUtilityBase):
        for injected_skill in self.__injected_additional_utility_skills:
            if injected_skill.custom_skill.skill_name == skill.custom_skill.skill_name:
                return
        self.__injected_additional_utility_skills.append(skill)
        self.__final_skills_list = None

    def enable(self):
        self.__is_enabled = True

    def disable(self):
        self.__is_enabled = False

    # computed

    def get_state(self) -> BehaviorState:
        return self.__memoized_state

    def get_final_state(self) -> BehaviorState:
        party_forced_state:BehaviorState|None = CustomBehaviorParty().get_party_forced_state()
        account_state = self.get_state()
        final_state:BehaviorState = account_state if party_forced_state is None else party_forced_state
        return final_state

    def get_is_enabled(self) -> bool:
        return self.__is_enabled

    def get_final_is_enabled(self) -> bool:
        party_forced_state:bool = CustomBehaviorParty().get_party_is_enabled()
        final_is_enabled:bool = party_forced_state and self.__is_enabled
        return final_is_enabled

    def is_executing_utility_skills(self) -> bool:
        '''
        used to know if we are executing utility skills, any external bot can use it as condition to run / pause.
        '''

        highest_score: tuple[CustomSkillUtilityBase, float | None] = self.get_highest_score()

        if highest_score[1] is not None: 
            # any skill with positive evaluation are a condition to stop an external script
            return True

        if self.get_final_state() == BehaviorState.IN_AGGRO:
            # in_aggro, even if nothing is done, we must stop  an external script
            return True

        return False

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
        return [
            AutoAttackUtility(current_build=self.in_game_build),

            FollowPartyLeaderUtility(current_build=self.in_game_build),
            FollowFlagUtility(current_build=self.in_game_build),
            
            LootUtility(current_build=self.in_game_build),
            OpenNearChestUtility(self.in_game_build),

            MapChangedUtility(self.in_game_build),
            StuckDetectionUtility(self.in_game_build),
        ]

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

        for skill in self.__injected_additional_utility_skills:
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

    timer = Timer()
    throttler = ThrottledTimer(70)

    def act(self):
        if not self.throttler.IsExpired(): return
        if not Routines.Checks.Map.MapValid(): return
        if not self.get_final_is_enabled(): return

        # if (
        # not cached_data.data.player_is_alive
        # or DistanceFromLeader(cached_data) >= Range.SafeCompass.value
        # or cached_data.data.player_is_knocked_down
        # or cached_data.combat_handler.InCastingRoutine()
        # or cached_data.data.player_is_casting

        self.throttler.Reset()
        self.timer.Reset()

        if not self.is_custom_behavior_match_in_game_build(): 
            print("Custom behavior doesn't match in game build, you are not allowed to perform behavior.act().")
            return

        if self.get_final_is_enabled():
            account_email = GLOBAL_CACHE.Player.GetAccountEmail()
            hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account_email)
            if hero_ai_options is not None:
                hero_ai_options.Combat = False
                hero_ai_options.Following = False
                hero_ai_options.Looting = False

        self.__fetch_and_memoized_state()
        self.__fetch_and_memoized_all_scores()

        # print(f"performance-audit-frame-duration:{self.timer.GetElapsedTime()}")

        try:
            next(self._generator_handle)
        except StopIteration:
            print(f"act is not expected to StopIteration.")
        except Exception as e:
            print(f"act is not expected to exit : {e}")

    # STATES
    
    def __fetch_and_memoized_state(self):
        def compute_state() -> BehaviorState:
            if self.get_final_is_enabled() == False:
                return BehaviorState.IDLE

            if not Routines.Checks.Map.MapValid():
                return BehaviorState.IDLE

            if GLOBAL_CACHE.Map.IsOutpost():
                return BehaviorState.IDLE

            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                return BehaviorState.IDLE

            if custom_behavior_helpers.Targets.is_player_in_aggro():
                return BehaviorState.IN_AGGRO

            if custom_behavior_helpers.Targets.is_party_in_aggro():
                return BehaviorState.CLOSE_TO_AGGRO # no need to be IN_AGGRO, and we want to keep moving to the enemies

            if custom_behavior_helpers.Targets.is_party_leader_in_aggro():
                return BehaviorState.CLOSE_TO_AGGRO # no need to be IN_AGGRO, and we want to keep moving to the enemies

            if custom_behavior_helpers.Targets.is_player_close_to_combat():
                return BehaviorState.CLOSE_TO_AGGRO

            return BehaviorState.FAR_FROM_AGGRO

        result:BehaviorState = compute_state()
        self.__memoized_state = result

    # SCORES 

    def __fetch_and_memoized_all_scores(self):
        # print('Evaluate all utilities')
        # Evaluate all utilities
        utilities: list[CustomSkillUtilityBase] = self.get_skills_final_list()
        # for x in utilities:
        #     print(f"skill {x.custom_skill.skill_name}")
        
        utility_scores: list[tuple[CustomSkillUtilityBase, float | None]] = []
        current_state: BehaviorState = self.get_final_state()
        for utility in utilities:
            score = utility.evaluate(current_state, list(self.__previously_attempted_skills))
            utility_scores.append((utility, score))
        
        # Sort by score (highest first)
        utility_scores.sort(key=lambda x: x[1] if x[1] is not None else 0, reverse=True)
        self.__memoized_ordered_scores = utility_scores

    def get_all_scores(self) -> list[tuple[CustomSkillUtilityBase, float | None]]:
        return self.__memoized_ordered_scores

    def get_highest_score(self) -> tuple[CustomSkillUtilityBase, float | None]:
        utility_scores: list[tuple[CustomSkillUtilityBase, float | None]] = self.get_all_scores()
        highest_score : tuple[CustomSkillUtilityBase, float | None] = utility_scores[0]
        return highest_score

    # HANDLING 

    def _handle(self) -> Generator[Any | None, Any | None, None]:

        # if no aftercast, there is no reason to continue once the score is no more the highest.
        # so lets declare it.
        while True:
            highest_score: tuple[CustomSkillUtilityBase, float | None] = self.get_highest_score()

            if highest_score[1] is None: # score is None
                yield
                continue

            should_run_through_then_end = highest_score[0].execution_strategy == UtilitySkillExecutionStrategy.EXECUTE_THROUGH_THE_END
            result:BehaviorResult
            started_at: float = time.time()
            current_score: float | None = highest_score[1]
            # append placeholder entry at start and keep reference
            history_entry = UtilitySkillExecutionHistory(
                skill=highest_score[0],
                score=current_score,
                result=None,
                started_at=started_at,
                ended_at=None,
            )
            self.skill_execution_history.append(history_entry)

            if should_run_through_then_end:
                # either we want to run through to the end.
                result = yield from self.__execute_until_the_end(highest_score[0])
            else:
                # either we prefer to stop if we are not the highest anymore.
                result = yield from self.__execute_until_condition(highest_score[0])

            ended_at: float = time.time()
            # update the referenced entry
            history_entry.result = result
            history_entry.ended_at = ended_at
            self.__previously_attempted_skills.append(highest_score[0].custom_skill)


            yield  # ← yield control back to the main execution flow

    def __execute_until_the_end(self, utility: CustomSkillUtilityBase) -> Generator[Any | None, Any | None, BehaviorResult]:
        state: BehaviorState = self.get_final_state()
        result: BehaviorResult = yield from utility.execute(state)
        return result

    def __execute_until_condition(self, new_highest_score: CustomSkillUtilityBase) -> Generator[Any | None, Any | None, BehaviorResult]:
        state: BehaviorState = self.get_final_state()
        utility_generator = new_highest_score.execute(state)
        
        # manually iterate through the utility's generator to check priority between yields
        while True:
            # if we lost priority, stop early
            current_highest = self.get_highest_score()
            if current_highest[0].custom_skill.skill_name != new_highest_score.custom_skill.skill_name or current_highest[1] is None:
                yield # required to avoid death-loop
                return BehaviorResult.ACTION_SKIPPED

            try:
                # get the next step from the utility
                result = next(utility_generator)
                yield result  # yield the utility's result back to the caller
            except StopIteration as e:
                # utility completed, return its final result
                return e.value if hasattr(e, 'value') and e.value is not None else BehaviorResult.ACTION_PERFORMED
