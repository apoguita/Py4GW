from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range, Agent, Player
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.Py4GWcorelib import Keystroke, Utils
from Py4GWCoreLib.enums import Key
from Widgets.CustomBehaviors.primitives import constants

from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.helpers import blessing_helper, custom_behavior_helpers
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

class TakeNearBlessingUtility(CustomSkillUtilityBase):
    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            mana_limit: float = 0.5,
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("take_near_blessing"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.BLESSING.value),
            allowed_states= [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.BLESSING,
            execution_strategy = UtilitySkillExecutionStrategy.STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.BLESSING.value)
        self.mana_limit = mana_limit
        self.agent_ids_already_interracted: set[int] = set()
        self.event_bus.subscribe(EventType.MAP_CHANGED, self.map_changed, subscriber_name=self.custom_skill.skill_name)

    def map_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        self.agent_ids_already_interracted = set()
        yield
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        # 1) If blessing_npc agent_id close enough
        #    - we can't check if blessing is already obtained (some of them are random)
        #    - we can add a closed list  for agent_id we already interracted with.

        blessing_npc : tuple[blessing_helper.BlessingNpc,int] | None = blessing_helper.find_first_blessing_npc(Range.Earshot.value)
        if blessing_npc is None: return None
        agent_id:int = blessing_npc[1]
        if agent_id in self.agent_ids_already_interracted: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        # -----MOVE & INTERRACT NPC PHASE
        # 1) move close to NPC
        # 2) Take a lock if possible [on npc_agent_id], else loop until timeout (30s) and add a cooldown (10s)
        # 3) interract with NPC

        # -----BLESSING PHASE
        # Using Blessing_dialog_helper
        # A) wait until is_npc_dialog_visible or timeout.
        # B) run_dialog_sequences with waits
        # C) add agent_ids_already_interracted & release lock

        # -------------------------------------------------------------------------------------------------

        # MOVE & INTERRACT NPC PHASE

        blessing_npc : tuple[blessing_helper.BlessingNpc,int] | None = blessing_helper.find_first_blessing_npc(Range.Earshot.value)

        if blessing_npc is None: 
            # todo cooldown
            yield
            return BehaviorResult.ACTION_SKIPPED

        agent_id:int = blessing_npc[1]
        yield from self.move_to_npc(agent_id)

        lock_key = f"take_near_blessing_{agent_id}"

        try:
            lock_aquired = yield from CustomBehaviorParty().get_shared_lock_manager().wait_aquire_lock(lock_key, timeout_seconds=30)
            if not lock_aquired:
                # todo cooldown
                if constants.DEBUG:print(f"Fail acquiring lock {lock_key}.")
                yield
                return BehaviorResult.ACTION_SKIPPED

            Player.Interact(agent_id, call_target=False)
            yield from custom_behavior_helpers.Helpers.wait_for(1000)

            result:bool = yield from self.run_dialog_sequence(agent_id)
            # we don't care about the result, we have interracted, we bypass now
            self.agent_ids_already_interracted.add(agent_id)
            return BehaviorResult.ACTION_PERFORMED
        finally:
            Keystroke.PressAndRelease(Key.Escape.value)
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)
    
    def run_dialog_sequence(self, agent_id:int) -> Generator[None, None, bool]:
        npc_dialog_visible = yield from blessing_helper.wait_npc_dialog_visible(timeout_ms=3_500)
        if not npc_dialog_visible:
            if constants.DEBUG: print("npc_dialog_visible FALSE")
            # we don't need cooldown, let's just ignore that NPC
            Keystroke.PressAndRelease(Key.Escape.value)
            return False

        result = yield from blessing_helper.run_dialog_sequences(timeout_ms=3_500)
        if not result:
            if constants.DEBUG: print("run_dialog_sequences FALSE.")
            Keystroke.PressAndRelease(Key.Escape.value)
            return False

        return True

    def move_to_npc(self, agent_id:int) -> Generator[None, None, None]:
        target_position : tuple[float, float] = Agent.GetXY(agent_id)

        if Utils.Distance(target_position, Player.GetXY()) > 150:
            path3d = yield from AutoPathing().get_path_to(target_position[0], target_position[1], smooth_by_los=True, margin=100.0, step_dist=300.0)
            path2d:list[tuple[float, float]]  = [(x, y) for (x, y, *_ ) in path3d]

            yield from Routines.Yield.Movement.FollowPath(
                    path_points= path2d, 
                    custom_exit_condition=lambda: Agent.IsDead(Player.GetAgentID()),
                    tolerance=150, 
                    log=constants.DEBUG, 
                    timeout=10_000, 
                    progress_callback=lambda progress: print(f"FollowPath take_near_blessing: progress: {progress}") if constants.DEBUG else None,
                    custom_pause_fn=lambda: False)

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"agent_ids_already_interracted : {self.agent_ids_already_interracted}")
        return
