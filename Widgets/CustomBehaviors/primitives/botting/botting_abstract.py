from abc import abstractmethod
from enum import Enum
from tracemalloc import stop
from typing import Any, Generator

import PyImGui

from Py4GWCoreLib import Botting
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

class StickPosition(Enum):
    Left        = 1,
    Right       = 2,
    Bottom      = 3,

class BottingAbstract():

    def __init__(self):
        self._is_ui_visible = False
        self.is_botting_behavior_injected = False
        self.ui_stick_position = StickPosition.Left

        self.__bot_instance : Botting | None = None

    @abstractmethod
    def bot_routine(self, bot_instance: Botting):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass


    def is_openned_bot(self):
        return self.__bot_instance is not None 

    def open_bot(self):
        if self.__bot_instance is None:
            # print(f"bot {self.name} opening.")
            self.__bot_instance = Botting(self.name)
            self.__bot_instance.Properties.Set("movement_timeout",value=-1) # required as utility skills take relay when moving.
            # bot.Properties.ApplyNow("halt_on_death","active", True) todo remove that
            self.__bot_instance.SetMainRoutine(self.bot_routine)

    def close_bot(self):
        # print(f"bot {self.name} closing.")
        self.__bot_instance = None

    def toggle_ui(self):
        self._is_ui_visible = not self._is_ui_visible

    def act(self):
        if self.__bot_instance is None:
            raise Exception("Bot must be openned first.")

        try:
            if self.__bot_instance is not None:
                # print("State names:", [state.name for state in self.bot.config.FSM.states] if self.bot.config.FSM.states else "No states found")
                self.__bot_instance.Update()
        except Exception as e:
            print(f"[Writer {id}] ERROR: {e}")
            # traceback.print_exc()
        yield

    def render(self, widget_window_size:tuple[float, float], widget_window_pos:tuple[float, float]):
        if self.__bot_instance is not None:
            if self._is_ui_visible: 
                if self.ui_stick_position == StickPosition.Left:
                    PyImGui.set_next_window_pos(widget_window_pos[0] - 370, widget_window_pos[1])

                if self.ui_stick_position == StickPosition.Right:
                    PyImGui.set_next_window_pos(widget_window_pos[0] + widget_window_size[0], widget_window_pos[1])
                    
                if self.ui_stick_position == StickPosition.Bottom:
                    PyImGui.set_next_window_pos(widget_window_pos[0], widget_window_pos[1] + widget_window_size[1])

                self.__bot_instance.UI.draw_window(main_child_dimensions= (350, 275))

    def inject_botting_behavior(self):
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
        self.is_botting_behavior_injected = True

    def remove_botting_behavior(self):
        instance:CustomBehaviorBaseUtility = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: raise Exception("CustomBehavior widget is required.")
        instance.clear_additionnal_utility_skills()
        self.is_botting_behavior_injected = False
