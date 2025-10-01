from typing import Any, Callable, Generator, List, Tuple

from Py4GWCoreLib import Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.auto_mover.path_helper import PathHelper
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.skills.botting.move_if_stuck import MoveIfStuckUtility
from Widgets.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_lock_taken import WaitIfLockTakenUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility


class FollowPathExecutor:

    def __init__(self):
        self.generator: Generator[Any, None, Any] | None = None
        self.movement_progress: float = 0
        self.is_active: bool = False
        self.current_path: list[tuple[float, float]] = []

    def start(self, waypoints: list[tuple[float, float]]):
        if not waypoints:
            print("FollowPathExecutor: No path provided")
            return

        self.is_active = True
        self.movement_progress = 0
        self.generator = self.__create_generator(waypoints)

    def __create_generator(self, waypoints: list[tuple[float, float]]) -> Generator[None, None, None]:
        
        try:
            path = yield from PathHelper.build_valid_path(waypoints)
            self.current_path = path
            if constants.DEBUG: print(f"generate_autopathing completed with {len(waypoints)} waypoints")
        except Exception as e:
            if constants.DEBUG: print(f"generate_autopathing error: {e}")
            self.current_path = []
        
        if constants.DEBUG:
            print(f"FollowPathExecutor: Starting movement with {len(waypoints)} waypoints, is_active={self.is_active}")
        
         # Setup combat behavior utilities
        instance: CustomBehaviorBaseUtility | None = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: 
            print("FollowPathExecutor: No combat behavior instance available")
            return

        # Inject utility skills for movement
        instance.inject_additionnal_utility_skills(MoveIfStuckUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToPartyMemberIfInAggroUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToEnemyIfCloseEnoughUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToPartyMemberIfDeadUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberManaTooLowUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberTooFarUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberNeedsToLootUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfInAggroUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfLockTakenUtility(instance.in_game_build))

        # Create movement generator
        custom_pause_fn: Callable[[], bool] = lambda: instance.is_executing_utility_skills() == True

        if constants.DEBUG: print(f"FollowPathExecutor: Started movement with {len(self.current_path)} waypoints, generator={self.generator is not None}")

        result = yield from Routines.Yield.Movement.FollowPath(
            path_points=self.current_path,
            custom_exit_condition=lambda: GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()),
            tolerance=150,
            log=constants.DEBUG,
            timeout=-1,
            progress_callback=self.on_progress,
            custom_pause_fn=custom_pause_fn
        )

        if constants.DEBUG: print(f"FollowPathExecutor: Started movement with {len(self.current_path)} waypoints, generator={self.generator is not None}")

    def stop(self):
        """Stop movement and cleanup."""
        self.generator = None
        self.is_active = False
        self.current_path = []
        
        # Clear utility skills
        instance: CustomBehaviorBaseUtility | None = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: 
            return
        instance.clear_additionnal_utility_skills()
        
        if constants.DEBUG: 
            print("FollowPathExecutor: Stopped movement")
    
    def resume(self):
        self.is_active = True

    def pause(self):
        self.is_active = False

    def act(self):
        """Execute one step of movement. Called by root.py."""
        if not self.is_active or self.generator is None:
            return
            
        try:
            next(self.generator)
            if constants.DEBUG: print(f"FollowPathExecutor: Movement step completed")
        except StopIteration:
            if constants.DEBUG: print("FollowPathExecutor: Movement completed")
            self.stop()
        except Exception as e:
            print(f"FollowPathExecutor: Movement error: {e}")
            self.stop()

    def on_progress(self, progress: float) -> None:
        """Callback for movement progress updates."""
        self.movement_progress = round(progress * 100, 1)
        if constants.DEBUG: print(f"FollowPathExecutor: Progress {self.movement_progress}%")

    def is_paused(self) -> bool:
        if self.generator is not None and not self.is_active:
            return True
        return False

    def is_running(self) -> bool:
        """Check if movement is currently active."""
        if self.generator is not None:
            return True
        return False


