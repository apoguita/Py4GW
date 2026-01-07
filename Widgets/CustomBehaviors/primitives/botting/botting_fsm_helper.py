from collections.abc import Callable, Generator
import time
from typing import Any, List
from Py4GWCoreLib import Botting, Routines

from Py4GWCoreLib.py4gwcorelib_src.FSM import FSM
from Widgets.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty

class BottingFsmHelpers:

    @staticmethod
    def __custom_behaviors_botting_daemon(fsm: FSM):
        from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
        print("CustomBehaviors_FSM_Daemon added")
        injected = False
        while True:
            # print("CustomBehaviorsDaemon running")
            try:
                instance = CustomBehaviorLoader().custom_combat_behavior
                if instance is not None:
                    if not injected:
                        injected = True

                    # Pause or resume FSM depending on CB utilities running
                    if instance.is_executing_utility_skills():
                        fsm.pause()
                    else:
                        fsm.resume()
                else:
                    # If CB not available, ensure FSM is not stuck paused
                    fsm.resume()
            except Exception:
                # Loader/widget might not be ready; try again later
                pass
            # yield control so FSM scheduler can run
            yield from Routines.Yield.wait(250)

    @staticmethod
    def _set_botting_behavior_as_pacifist(bot: Botting):
        print("SetBottingBehaviorAsPacifist")
        
        instance = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: raise Exception("CustomBehavior widget is required.")
        # todo we must verify we are under UseCustomBehavior

        # Local imports to avoid circular import with resign_if_needed -> botting_helpers
        from Widgets.CustomBehaviors.skills.botting.move_if_stuck import MoveIfStuckUtility
        from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility

        instance = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: raise Exception("CustomBehavior widget is required.")
        instance.clear_additionnal_utility_skills() # this can introduce issue as  we are not unsubscribing from the event bus.
        CustomBehaviorParty().set_party_is_combat_enabled(False)
        CustomBehaviorParty().set_party_is_looting_enabled(False)
        
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberTooFarUtility(instance.event_bus, instance.in_game_build))

    @staticmethod
    def _set_botting_behavior_as_aggressive(bot: Botting):
        print("SetBottingBehaviorAsAggressive")
        instance = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: raise Exception("CustomBehavior widget is required.")
        # todo we must verify we are under UseCustomBehavior

        # Local imports to avoid circular import with resign_if_needed -> botting_helpers
        from Widgets.CustomBehaviors.skills.botting.move_to_distant_chest_if_path_exists import MoveToDistantChestIfPathExistsUtility
        from Widgets.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
        from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
        from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
        from Widgets.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
        from Widgets.CustomBehaviors.skills.botting.wait_if_lock_taken import WaitIfLockTakenUtility
        from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
        from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
        from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility

        instance = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: raise Exception("CustomBehavior widget is required.")
        instance.clear_additionnal_utility_skills() # this can introduce issue as  we are not unsubscribing from the event bus.
        CustomBehaviorParty().set_party_is_combat_enabled(True)
        CustomBehaviorParty().set_party_is_looting_enabled(True)

        # some are not finalized
        # instance.inject_additionnal_utility_skills(MoveToDistantChestIfPathExistsUtility(instance.event_bus, instance.in_game_build))
        # instance.inject_additionnal_utility_skills(ResignIfNeededUtility(instance.event_bus, instance.in_game_build, on_failure= lambda: BottingHelpers.botting_unrecoverable_issue(fsm)))
        instance.inject_additionnal_utility_skills(MoveToPartyMemberIfInAggroUtility(instance.event_bus, instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToPartyMemberIfInAggroUtility(instance.event_bus, instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToEnemyIfCloseEnoughUtility(instance.event_bus, instance.in_game_build))
        instance.inject_additionnal_utility_skills(MoveToPartyMemberIfDeadUtility(instance.event_bus, instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberManaTooLowUtility(instance.event_bus, instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberTooFarUtility(instance.event_bus, instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfPartyMemberNeedsToLootUtility(instance.event_bus, instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfInAggroUtility(instance.event_bus, instance.in_game_build))
        instance.inject_additionnal_utility_skills(WaitIfLockTakenUtility(instance.event_bus, instance.in_game_build))

    @staticmethod
    def __wrapper_event_bus(callback : Callable[[FSM], Generator[Any, Any, Any]] | None ) -> Callable[[EventMessage], Generator[Any, Any, Any]]:

        def wrapper(event_message: EventMessage) -> Generator[Any, Any, Any]:
            if callback is not None:
                yield from callback(event_message.data)
            else:
                yield from BottingHelpers.botting_unrecoverable_issue(event_message.data)

        return wrapper

    @staticmethod
    def UseCustomBehavior(
            bot: Botting, 
            on_player_critical_stuck: Callable[[FSM], Generator[Any, Any, Any]] | None = None,
            on_player_critical_death: Callable[[FSM], Generator[Any, Any, Any]] | None = None,
            on_party_death: Callable[[FSM], Generator[Any, Any, Any]] | None = None
            ):

        fsm = bot.config.FSM

        instance = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: raise Exception("CustomBehavior widget is required.")

        # Attach to FSM safely across start/reset. If FSM already started, attach now; otherwise add a Step
        if fsm.current_state is not None:
            if not fsm.HasManagedCoroutine("CustomBehaviorsBottingDaemon"):
                print("CustomBehaviorsBottingDaemon AddManagedCoroutine (runtime)")
                fsm.AddManagedCoroutine("CustomBehaviorsDaemon", BottingFsmHelpers.__custom_behaviors_botting_daemon(fsm))
        else:
            # Not started yet: use a step so it attaches during run (start() clears managed_coroutines)
            if not fsm.has_state("CustomBehaviorsBottingDaemon"):
                print("CustomBehaviorsBottingDaemon AddManagedCoroutineStep (pre-start)")
                fsm.AddManagedCoroutineStep("CustomBehaviorsBottingDaemon", BottingFsmHelpers.__custom_behaviors_botting_daemon(fsm))

        event_bus = instance.event_bus
        subscriber_name = "CustomBehaviorsBottingDaemon"
        event_bus.unsubscribe_all(subscriber_name)
        event_bus.subscribe(EventType.PLAYER_CRITICAL_STUCK, BottingFsmHelpers.__wrapper_event_bus(on_player_critical_stuck) , subscriber_name=subscriber_name)
        event_bus.subscribe(EventType.PLAYER_CRITICAL_DEATH, BottingFsmHelpers.__wrapper_event_bus(on_player_critical_death), subscriber_name=subscriber_name)
        event_bus.subscribe(EventType.PARTY_DEATH, BottingFsmHelpers.__wrapper_event_bus(on_party_death), subscriber_name=subscriber_name)
    
    @staticmethod
    def SetBottingBehaviorAsAggressive(bot: Botting):
        instance = CustomBehaviorLoader().custom_combat_behavior
        if instance is not None:
            BottingFsmHelpers.UseCustomBehavior(bot)
            bot.config.FSM.AddManagedCoroutineStep("CustomBehavior_SetBottingBehaviorAsAggressive", lambda: BottingFsmHelpers._set_botting_behavior_as_aggressive(bot))

    @staticmethod
    def SetBottingBehaviorAsPacifist(bot: Botting):
        instance = CustomBehaviorLoader().custom_combat_behavior
        if instance is not None:
            BottingFsmHelpers.UseCustomBehavior(bot)
            bot.config.FSM.AddManagedCoroutineStep("CustomBehavior_SetBottingBehaviorAsPacifist", lambda: BottingFsmHelpers._set_botting_behavior_as_pacifist(bot))
