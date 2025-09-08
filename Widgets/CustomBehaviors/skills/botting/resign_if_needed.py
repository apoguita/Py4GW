from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.enums import SharedCommandType
from Widgets.CustomBehaviors.primitives.bus.event_bus import EVENT_BUS
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class ResignIfNeededUtility(CustomSkillUtilityBase):
    def __init__(
            self, 
            current_build: list[CustomSkill], 
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("resign_if_needed"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(CommonScore.BOTTING.value), 
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.BOTTING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BOTTING.value)
        self.__is_resign_asked = False
        self.death_timer_timer = ThrottledTimer(120_000)
        self.__death_timer_started = False
        self.resign_timeout_timer = ThrottledTimer(15_000)  # 15 second timeout for resignation process

        EVENT_BUS.subscribe(EventType.PLAYER_CRITICAL_STUCK, self.player_critical_stuck)
        EVENT_BUS.subscribe(EventType.MAP_CHANGED, self.map_changed)

    def player_critical_stuck(self, message: EventMessage):
        self.__is_resign_asked = True

    def map_changed(self, message: EventMessage):
        self.__is_resign_asked = False
        self.death_timer_timer.Reset()
        self.__death_timer_started = False
        self.resign_timeout_timer.Reset()

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        # either PLAYER_CRITICAL_STUCK
        # either player is dead for > 120s

        if not GLOBAL_CACHE.Map.IsExplorable(): return None

        if self.__is_resign_asked == True:
            return self.score_definition.get_score()

        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()): 
            if not self.__death_timer_started:
                self.death_timer_timer.Reset()
                self.__death_timer_started = True
                return None
            if self.death_timer_timer.IsExpired():
                return self.score_definition.get_score()
            return None
        
        # Player is alive again; clear any pending death timer
        self.__death_timer_started = False
        self.death_timer_timer.Reset()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        # Reset the timeout timer when starting execution
        self.resign_timeout_timer.Reset()
        
        loop_counter = 0
        
        while not GLOBAL_CACHE.Party.IsPartyDefeated():
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
            for account in accounts:
                print("Resigning account: " + account.AccountEmail)
                GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0,0,0,0))
            yield from Routines.Yield.wait(8_000)
            
            loop_counter += 1
            if loop_counter > 4:
                print("Loop counter Resign is too high, the script is stuck...")
                break

        print("Party is defeated")

        # Wait for resignation to complete using ThrottledTimer
        while not self.resign_timeout_timer.IsExpired():
            is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
            is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
            is_explorable = GLOBAL_CACHE.Map.IsExplorable()
            is_party_defeated = GLOBAL_CACHE.Party.IsPartyDefeated()

            if is_map_ready and is_party_loaded and is_explorable and is_party_defeated:
                print(f"Party resigned.")
                GLOBAL_CACHE.Party.ReturnToOutpost()
                yield
                self.__is_resign_asked = False
                return BehaviorResult.ACTION_PERFORMED

            yield from Routines.Yield.wait(500)
        else:
            print(f"Something failed, i am not able to recover - stopping bot.")

        self.__is_resign_asked = False
        yield
        return BehaviorResult.ACTION_PERFORMED