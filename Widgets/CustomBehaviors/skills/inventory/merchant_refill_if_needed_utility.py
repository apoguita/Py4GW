import random
from re import DEBUG
from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, AgentArray, ItemArray, Routines, Range
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, Keystroke, ThrottledTimer, Utils
from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_strategy import UtilitySkillExecutionStrategy
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class MerchantRefillIfNeededUtility(CustomSkillUtilityBase):
    def __init__(self, 
    current_build: list[CustomSkill], 
    ) -> None:

        super().__init__(
            skill=CustomSkill("merchant_refill_if_needed_utility"), 
            in_game_build=current_build, 
            score_definition=ScoreStaticDefinition(1), 
            allowed_states=[BehaviorState.IDLE],
            utility_skill_typology=UtilitySkillTypology.INVENTORY,
            execution_strategy=UtilitySkillExecutionStrategy.STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(99.991)
        self.expected_items: dict[ModelID, int] = {
            ModelID.Salvage_Kit: 4,
            ModelID.Expert_Salvage_Kit: 1,
            ModelID.Superior_Identification_Kit: 2,
        }

        self.inventory_slot_to_keep_empty = 3
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if not GLOBAL_CACHE.Map.IsOutpost(): return False
        return True

    def _is_merchant_agent(self, agent_id: int) -> bool:
        """Check if the agent is a merchant by checking for merchant tags in multiple languages."""
        merchant_tags = ['[Merchant]', '[Marchand]', 'Kauffrau']
        agent_name = GLOBAL_CACHE.Agent.GetName(agent_id)
        return any(merchant_tag in agent_name for merchant_tag in merchant_tags)

    def _get_target(self) -> int | None:
        
        agent_ids = GLOBAL_CACHE.AgentArray.GetNPCMinipetArray()
        agent_ids = AgentArray.Filter.ByDistance(agent_ids, GLOBAL_CACHE.Player.GetXY(), Range.Compass.value)
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id) and GLOBAL_CACHE.Agent.IsValid(agent_id))
        agent_ids = AgentArray.Filter.ByCondition(agent_ids, self._is_merchant_agent)
        if len(agent_ids) == 0: return None
        return agent_ids[0]
        
    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        if not self.should_refill_some_items():
            return None
            
        agent_id = self._get_target()
        if agent_id is not None:
            return self.score_definition.get_score()

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        # -----MOVE & INTERRACT NPC PHASE
        # 1) take lock
        # 2) move close to NPC [with some random time to not lock suspect.]
        # 3) interract with NPC

        # -----BUYING PHASE
        # 1) buy phase
        # 2) press ESC
        # 3) release lock

        agent_id = self._get_target()
        if agent_id is None:
            yield
            return BehaviorResult.ACTION_SKIPPED

        lock_key = f"merchant_refill_if_needed_utility_{GLOBAL_CACHE.Player.GetAgentID()}" # on key per player, and we wait no one is locking.
        yield from custom_behavior_helpers.Helpers.wait_for(random.randint(1_000, 5_000))

        try:
            lock_aquired = yield from CustomBehaviorParty().get_shared_lock_manager().wait_aquire_lock(lock_key, timeout_seconds=30)
            if not lock_aquired:
                # todo cooldown
                if constants.DEBUG: print(f"Fail acquiring lock {lock_key}.")
                yield
                return BehaviorResult.ACTION_SKIPPED
            yield from self.move_and_interract_with_merchant(agent_id)
            
            # Buy all needed items
            for model_id, expected_quantity in self.expected_items.items():
                current_count = GLOBAL_CACHE.Inventory.GetModelCount(model_id.value)
                needed_quantity = expected_quantity - current_count
                if needed_quantity > 0:
                    yield from self.buy_items(model_id, needed_quantity)
            
            return BehaviorResult.ACTION_PERFORMED
        finally:
            Keystroke.PressAndRelease(Key.Escape.value)
            CustomBehaviorParty().get_shared_lock_manager().release_lock(lock_key)

    def move_and_interract_with_merchant(self, agent_id:int) -> Generator[None, None, None]:
        target_position : tuple[float, float] = GLOBAL_CACHE.Agent.GetXY(agent_id)
        if Utils.Distance(target_position, GLOBAL_CACHE.Player.GetXY()) > 150:
            path3d = yield from AutoPathing().get_path_to(target_position[0], target_position[1], smooth_by_los=True, margin=100.0, step_dist=300.0)
            path2d:list[tuple[float, float]]  = [(x, y) for (x, y, *_ ) in path3d]

            yield from Routines.Yield.Movement.FollowPath(
                    path_points= path2d, 
                    custom_exit_condition=lambda: GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()),
                    tolerance=150, 
                    log=constants.DEBUG, 
                    timeout=10_000, 
                    progress_callback=lambda progress: print(f"FollowPath merchant_refill_if_needed_utility: progress: {progress}") if constants.DEBUG else None,
                    custom_pause_fn=lambda: False)

        if constants.DEBUG: print(f"Merchant reached.")
        GLOBAL_CACHE.Player.Interact(agent_id, call_target=False)
        yield from custom_behavior_helpers.Helpers.wait_for(1_000)

    def buy_items(self, model_id: ModelID, quantity_to_buy: int) -> Generator[None, None, None]:

        if quantity_to_buy <= 0:
            ActionQueueManager().ResetQueue("MERCHANT")
            return

        # Check if we have enough inventory space
        free_slots = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
        if free_slots < self.inventory_slot_to_keep_empty:
            if constants.DEBUG:print(f"Not enough inventory space to buy {quantity_to_buy} {model_id}. Free slots: {free_slots}, required: {self.inventory_slot_to_keep_empty}")
            ActionQueueManager().ResetQueue("MERCHANT")
            return

        # Limit quantity to available space (keeping the minimum slots free)
        max_can_buy = free_slots - self.inventory_slot_to_keep_empty
        actual_quantity_to_buy = min(quantity_to_buy, max_can_buy)
        
        if actual_quantity_to_buy <= 0:
            if constants.DEBUG:print(f"Cannot buy {model_id}: would exceed inventory space limit")
            ActionQueueManager().ResetQueue("MERCHANT")
            return

        merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
        merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: GLOBAL_CACHE.Item.GetModelID(item_id) == model_id)

        if len(merchant_item_list) == 0:
            if constants.DEBUG:print(f"Merchant doesn't sell {model_id}")
            ActionQueueManager().ResetQueue("MERCHANT")
            return
        
        for i in range(actual_quantity_to_buy):
            item_id = merchant_item_list[0]
            value = GLOBAL_CACHE.Item.Properties.GetValue(item_id) * 2
            GLOBAL_CACHE.Trading.Merchant.BuyItem(item_id, value)
            
        while not ActionQueueManager().IsEmpty("MERCHANT"):
            yield from custom_behavior_helpers.Helpers.wait_for(50)
        
        if constants.DEBUG:print(f"Bought {actual_quantity_to_buy} {model_id} (requested: {quantity_to_buy})")

    def should_refill_some_items(self) -> bool:
        """Check if we need to refill any items based on expected quantities."""
        if GLOBAL_CACHE.Inventory.GetFreeSlotCount() < self.inventory_slot_to_keep_empty:
            return False
            
        for model_id, expected_quantity in self.expected_items.items():
            current_count = GLOBAL_CACHE.Inventory.GetModelCount(model_id.value)
            if current_count < expected_quantity:
                return True
                
        return False

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        free_slots = GLOBAL_CACHE.Inventory.GetFreeSlotCount()
        PyImGui.bullet_text(f"Free inventory slots: {free_slots}/{self.inventory_slot_to_keep_empty} (min required)")
        
        PyImGui.bullet_text("Expected items:")
        for model_id, expected_quantity in self.expected_items.items():
            current_count = GLOBAL_CACHE.Inventory.GetModelCount(model_id.value)
            PyImGui.bullet_text(f"{model_id.name}: {current_count}/{expected_quantity}")
        
        PyImGui.bullet_text(f"Should go to merchant: {self.should_refill_some_items()}")
        
        agent_id = self._get_target()
        if agent_id is not None:
            PyImGui.bullet_text(f"Merchant found: {GLOBAL_CACHE.Agent.GetName(agent_id)}")
        else:
            PyImGui.bullet_text("No merchant found nearby")