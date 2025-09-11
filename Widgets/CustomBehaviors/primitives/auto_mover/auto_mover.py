from typing import Any, Callable, Generator

from Py4GWCoreLib import Routines
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Pathing import AutoPathing
from Widgets.CustomBehaviors.primitives import constants
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.skills.botting.move_if_stuck import MoveIfStuckUtility
from Widgets.CustomBehaviors.skills.botting.move_to_distant_chest_if_path_exists import MoveToDistantChestIfPathExistsUtility
from Widgets.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.resign_if_needed import ResignIfNeededUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility


class AutoMover:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutoMover, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.generator:Generator[Any, None, Any] | None = None
            self.movement_progress:float = 0

    def act(self):
        if self.generator is not None:
            # Run one step of the generator
            try:
                next(self.generator)
            except StopIteration:
                if constants.DEBUG: print(f"AutoMover finalized StopIteration.")
                generator = None

    def define_destination(self, target_position: tuple[float, float]) -> Generator[Any, None, Any]:

        instance:CustomBehaviorBaseUtility = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: return

        # instance.inject_additionnal_utility_skills(ResignIfNeededUtility(instance.in_game_build))
        # instance.inject_additionnal_utility_skills(MoveToDistantChestIfPathExistsUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveIfStuckUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToPartyMemberIfInAggroUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToEnemyIfCloseEnoughUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToPartyMemberIfDeadUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberManaTooLowUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberTooFarUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberNeedsToLootUtility(instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfInAggroUtility(instance.in_game_build))

        path3d = yield from AutoPathing().get_path_to(target_position[0], target_position[1], smooth_by_los=True, margin=100.0, step_dist=300.0)
        path2d:list[tuple[float, float]]  = [(x, y) for (x, y, *_ ) in path3d]

        custom_pause_fn: Callable[[], bool] | None = lambda: instance.is_executing_utility_skills() == True # meaning we pause moving across coords, if we have any action that is higher priority

        move_generator = Routines.Yield.Movement.FollowPath(
                path_points= path2d, 
                custom_exit_condition=lambda: GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()), # todo change to party is dead.
                tolerance=150, 
                log=constants.DEBUG, 
                timeout=-1, 
                progress_callback=self.on_progress,
                custom_pause_fn=custom_pause_fn)

        print("move generator set")
        self.generator = move_generator

    def on_progress(self, progress: float) -> None:
        self.movement_progress = round(progress * 100, 1)
        if constants.DEBUG: print(f"AutoMover progress {self.movement_progress}")

