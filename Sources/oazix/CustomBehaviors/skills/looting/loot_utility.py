from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Agent, AutoPathing, Routines, Range, Player
from Py4GWCoreLib.Py4GWcorelib import LootConfig, ThrottledTimer, Utils
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.parties.memory_cache_manager import MemoryCacheManager
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class LootUtility(CustomSkillUtilityBase):
    PICKUP_RETRY_ATTEMPTS = 2
    PICKUP_TIMEOUT_MS = 3500
    REINTERACT_EVERY_TICKS = 5
    REPOSITION_AT_TICK = 10

    def __init__(
            self,
            event_bus:EventBus,
            current_build: list[CustomSkill],
            allowed_states: list[BehaviorState] = [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
            # CLOSE_TO_AGGRO is required to avoid infinite-loop, if when approching an item to loot, player is aggroing.
            # otherwise once approching enemies, player will infinitely loop between loot & follow_party_leader
        ) -> None:
        score_definition = ScoreStaticDefinition(CommonScore.LOOT.value)

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("loot"),
            in_game_build=current_build,
            score_definition=score_definition,
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.LOOTING,
            execution_strategy=UtilitySkillExecutionStrategy.STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST)

        self._score_definition = score_definition
        self.throttle_timer: ThrottledTimer = ThrottledTimer(1_000)
        self._eval_throttler: ThrottledTimer = ThrottledTimer(1_500)  # Only scan loot every 1.5s
        self._last_eval_score: float | None = None

    _LOOT_CACHE_KEY = "filtered_loot_earshot"

    def _get_cached_loot_array(self) -> list[int]:
        """Get filtered loot array, cached per evaluation cycle via MemoryCacheManager."""
        return MemoryCacheManager.get_or_set(
            self._LOOT_CACHE_KEY,
            lambda: LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
        )

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True


    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        # Eval throttle: return cached score if not expired
        if not self._eval_throttler.IsExpired():
            return self._last_eval_score
        self._eval_throttler.Reset()

        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1:
            self._last_eval_score = None
            return None

        if custom_behavior_helpers.Targets.is_party_leader_in_aggro():
            self._last_eval_score = None
            return None

        if custom_behavior_helpers.Targets.is_party_in_aggro():
            self._last_eval_score = None
            return None

        loot_array = self._get_cached_loot_array()
        # print(f"Loot array: {loot_array}")
        if len(loot_array) == 0:
            self._last_eval_score = None
            return None

        self._last_eval_score = self._score_definition.get_score()
        return self._last_eval_score

    def _approach_item(self, item_id: int) -> Generator[Any, None, bool]:
        if not Agent.IsValid(item_id):
            return False

        item_pos = Agent.GetXY(item_id)
        follow_success = yield from Routines.Yield.Movement.FollowPath(
            [item_pos],
            timeout=6_000,
            tolerance=120,
        )
        if follow_success and Utils.Distance(Player.GetXY(), item_pos) <= Range.Touch.value * 2.2:
            return True

        try:
            path3d = yield from AutoPathing().get_path_to(
                item_pos[0],
                item_pos[1],
                smooth_by_los=True,
                margin=100.0,
                step_dist=300.0,
            )
        except Exception:
            path3d = []

        path2d = [(x, y) for (x, y, *_) in list(path3d or [])]
        if len(path2d) == 0:
            return False

        routed_success = yield from Routines.Yield.Movement.FollowPath(
            path_points=path2d,
            timeout=10_000,
            tolerance=120,
        )

        if not routed_success:
            return False

        return Utils.Distance(Player.GetXY(), item_pos) <= Range.Touch.value * 2.2

    def _wait_for_pickup(self, item_id: int) -> Generator[Any, None, bool]:
        pickup_timer = ThrottledTimer(self.PICKUP_TIMEOUT_MS)
        wait_tick = 0

        while not pickup_timer.IsExpired():
            loot_array = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
            if item_id not in loot_array or len(loot_array) == 0:
                return True

            wait_tick += 1
            if wait_tick % self.REINTERACT_EVERY_TICKS == 0 and Agent.IsValid(item_id):
                Player.Interact(item_id, call_target=False)

            if wait_tick == self.REPOSITION_AT_TICK and Agent.IsValid(item_id):
                yield from self._approach_item(item_id)
                if Agent.IsValid(item_id):
                    Player.Interact(item_id, call_target=False)

            yield from custom_behavior_helpers.Helpers.wait_for(100)

        return False

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if not self.throttle_timer.IsExpired():
            yield
            return BehaviorResult.ACTION_SKIPPED

        # Use per-cycle cache for entry check (deduplicates with _evaluate scan)
        loot_array = self._get_cached_loot_array()
        if len(loot_array) == 0:
            yield
            return BehaviorResult.ACTION_SKIPPED

        self.throttle_timer.Reset()

        while True:

            if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < 1: break
            loot_array:list[int] = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)
            if len(loot_array) == 0: break
            item_id = loot_array.pop(0)
            if item_id is None or item_id == 0:
                yield from custom_behavior_helpers.Helpers.wait_for(100)
                continue
            if not Agent.IsValid(item_id):
                yield from custom_behavior_helpers.Helpers.wait_for(100)
                continue

            picked_up = False
            for _ in range(self.PICKUP_RETRY_ATTEMPTS):
                if not Agent.IsValid(item_id):
                    picked_up = True
                    break

                if not (yield from self._approach_item(item_id)):
                    continue

                Player.Interact(item_id, call_target=False)
                yield from custom_behavior_helpers.Helpers.wait_for(100)

                if (yield from self._wait_for_pickup(item_id)):
                    picked_up = True
                    break

            if not picked_up and Agent.IsValid(item_id):
                # Filter uses item-agent IDs, so blacklist the same agent_id.
                LootConfig().AddItemIDToBlacklist(item_id)
                yield from custom_behavior_helpers.Helpers.wait_for(100)

        yield from custom_behavior_helpers.Helpers.wait_for(100)
        return BehaviorResult.ACTION_PERFORMED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        PyImGui.bullet_text(f"loot_array : {LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot=True)}")
        return
