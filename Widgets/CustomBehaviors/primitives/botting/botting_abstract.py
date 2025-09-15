from abc import abstractmethod
from typing import Any, Generator

from Widgets.CustomBehaviors.gui import botting
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.skills.botting.move_if_stuck import MoveIfStuckUtility
from Widgets.CustomBehaviors.skills.botting.move_to_distant_chest_if_path_exists import MoveToDistantChestIfPathExistsUtility
from Widgets.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.resign_if_needed import ResignIfNeededUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_lock_taken import WaitIfLockTakenUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility

class BottingAbstract():

    def __init__(self):
        self._generator = self._act()
        instance:CustomBehaviorBaseUtility = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: raise Exception("CustomBehavior widget is required.")

        # some are not finalized
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
        instance.inject_additionnal_utility_skills(WaitIfLockTakenUtility(instance.in_game_build))

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def _act(self) -> Generator[Any | None, Any | None, Any | None]:
        '''
        the method each bot need to implement.
        '''
        pass

    def act(self):
        try:
            next(self._generator)
        except StopIteration:
            print(f"Bot is finished.")
        except Exception as e:
            print(f"act is not expected to exit : {e}")

    def stop(self):
        instance:CustomBehaviorBaseUtility = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: raise Exception("CustomBehavior widget is required.")
        instance.clear_additionnal_utility_skills()
