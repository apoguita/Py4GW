from typing import Any, Callable, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Utils
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
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
import time
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class MoveToDistantChestIfPathExistsUtility(CustomSkillUtilityBase):
    def __init__(
            self, 
            current_build: list[CustomSkill], 
            allowed_states: list[BehaviorState] = [BehaviorState.FAR_FROM_AGGRO]
        ) -> None:
        
        super().__init__(
            skill=CustomSkill("move_to_distant_chest_if_path_exists"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(CommonScore.LOOT.value - 0.0002), # this cannont pass before my own loot
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.BOTTING,
            execution_strategy=UtilitySkillExecutionStrategy.STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST)

        self.score_definition: ScoreStaticDefinition =ScoreStaticDefinition(CommonScore.LOOT.value - 0.0002)
        self.throttle_timer = ThrottledTimer(5_000)
        self.opened_chest_agent_ids: set[int] = set()
        EVENT_BUS.subscribe(EventType.MAP_CHANGED, self.area_changed)
        EVENT_BUS.subscribe(EventType.CHEST_OPENED, self.chest_opened)

    def chest_opened(self, message: EventMessage):
        self.opened_chest_agent_ids.add(message.data)
        self.throttle_timer.Reset()

    def area_changed(self, message: EventMessage):
        self.opened_chest_agent_ids = set()
        self.throttle_timer.Reset()
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    def _get_path_distance(self, path :list[tuple[float, float]]) -> float:
        total_distance = 0
        for i in range(len(path) - 1):
            segment1 = path[i]
            segment2 = path[i + 1]
            distance = Utils.Distance(segment1, segment2)
            total_distance += distance
        return total_distance

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:   

        if not self.throttle_timer.IsExpired(): return None
        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1: return None #"No free slots in inventory, halting."
        if GLOBAL_CACHE.Inventory.GetModelCount(22751) < 1: return None #"No lockpicks in inventory, halting."

        chest_agent_id = Routines.Agents.GetNearestChest(3000)
        if chest_agent_id is None or chest_agent_id == 0: return None
        if chest_agent_id in self.opened_chest_agent_ids: return None

        player_position = GLOBAL_CACHE.Agent.GetXY(GLOBAL_CACHE.Player.GetAgentID())
        chest_position = GLOBAL_CACHE.Agent.GetXY(chest_agent_id)
        if Utils.Distance(player_position, chest_position) < 600: return None # we don't care about close chests

        # we can't evaluate path is really reachable there. (not yieldable)
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        chest_agent_id = Routines.Agents.GetNearestChest(3000)
        player_position = GLOBAL_CACHE.Agent.GetXYZ(GLOBAL_CACHE.Player.GetAgentID())
        chest_position = GLOBAL_CACHE.Agent.GetXY(chest_agent_id)
        print(f"chest_agent_id {chest_agent_id}")

        zplane = GLOBAL_CACHE.Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID())
        path3d = yield from AutoPathing().get_path((player_position[0], player_position[1], zplane), (chest_position[0], chest_position[1], zplane),smooth_by_los=True, margin=100.0, step_dist=300.0)
        path_flatten:list[tuple[float, float]] = [(px, py) for (px, py, pz) in path3d]

        print(f"path found {path3d}")

        if(self._get_path_distance(path_flatten) > 2500):
            print(f"path too long... we don't want to move so far.")
            # todo we must give that chest another chance. but with a throttle
            self.throttle_timer.Reset()
            return BehaviorResult.ACTION_SKIPPED

        print("MoveToCloseChestIfPathExistsUtility")
        exit_condition: Callable[[], bool] = lambda: False

        # exit condition must be done differently, we need to know, if something else is scoring higher.

        result : bool = yield from Routines.Yield.Movement.FollowPath(
            path_points=path_flatten, 
            custom_exit_condition=exit_condition, 
            tolerance=100, 
            log=True, 
            timeout=5_000, 
            progress_callback=lambda progress: print(f"xx: progress: {progress}"))

        if result == False:
            self.throttle_timer.Reset()
            return BehaviorResult.ACTION_SKIPPED

        print(f"chest reached:{chest_agent_id}")
        self.throttle_timer.Reset()
        return BehaviorResult.ACTION_PERFORMED

