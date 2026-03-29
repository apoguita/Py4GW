from collections.abc import Generator
from typing import Any, Callable, override

import PyImGui

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.parties.shared_lock_manager import ShareLockType
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.plugins.utility_skill_watchdog import UtilitySkillWatchdog

class ShouldLockUntilBuffCompletion(UtilitySkillWatchdog):
    """
    Extension that manages lock acquisition and release based on buff configuration fulfillment.

    When enabled:
    - Checks if buff is complete during evaluation (hook_pre_evaluate)
    - Acquires a lock and waits for buff completion during execution (hook_pre_execution)
    - Releases the lock when buff is complete

    This ensures only one agent can execute the buff skill at a time and prevents
    other agents from executing until the buff is fully applied.
    """

    def __init__(self, parent_skill: CustomSkill, is_buff_config_fulfilled: Callable[[], bool], default_value: bool = False):
        super().__init__(parent_skill, "should_lock_until_buff_completion")
        from_persistence = self.load_from_persistence(str(int(default_value)))
        self.should_wait_for_buff_completion: bool = bool(int(from_persistence))
        self.is_fulfilled = is_buff_config_fulfilled
        self.lock_key = f"buff_completion_lock_{parent_skill.skill_name}"

    @property
    @override
    def data(self) -> str:
        return str(int(self.should_wait_for_buff_completion))

    @override
    def render_debug_ui(self):
        hash_id = f"should_wait_for_buff_completion##should_wait_for_buff_completion{self.parent_skill_name}"
        self.should_wait_for_buff_completion = PyImGui.checkbox(f"Lock Until Buff Complete##{hash_id}", self.should_wait_for_buff_completion)

        # Show lock status
        lock_manager = CustomBehaviorParty().get_shared_lock_manager()
        PyImGui.text(f"Any Action Lock Taken: {lock_manager.is_any_lock_taken(ShareLockType.ACTIONS)}")
        PyImGui.text(f"Buff Config Fulfilled: {self.is_fulfilled()}")

    @override
    def act(self) -> Generator[Any | None, Any | None, None]:
        """
        Logic:
        - If disabled, do nothing
        - If buff is fulfilled, do nothing (already complete)
        - If buff is not fulfilled, try to acquire lock and wait for completion
        """
        if not self.should_wait_for_buff_completion:
            yield
            return

        lock_manager = CustomBehaviorParty().get_shared_lock_manager()

        # If buff is fulfilled, release lock if we have it
        if self.is_fulfilled() and lock_manager.is_any_lock_taken(ShareLockType.ACTIONS):
            lock_manager.release_lock(self.lock_key)

        # If buff is not fulfilled and no lock is taken, allow execution to take a lock
        if not self.is_fulfilled() and not lock_manager.is_any_lock_taken(ShareLockType.ACTIONS):
            # Try to acquire lock
            if not lock_manager.try_aquire_lock(self.lock_key, timeout_seconds=30, lock_type=ShareLockType.ACTIONS):
                # Someone else has the lock, skip
                yield
                return

        # Lock acquired - wait for buff completion
        yield