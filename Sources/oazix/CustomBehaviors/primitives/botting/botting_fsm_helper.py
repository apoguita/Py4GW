from collections.abc import Callable, Generator
import time
from typing import Any, List
from Py4GWCoreLib import Botting, Routines

from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.py4gwcorelib_src.ActionQueue import ActionQueueManager
from Py4GWCoreLib.py4gwcorelib_src.FSM import FSM
from Py4GWCoreLib.py4gwcorelib_src.Keystroke import Keystroke
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty

class BottingFsmHelpers:

    @staticmethod
    def __custom_behaviors_botting_daemon(fsm: FSM):
        from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
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
                        # print("CustomBehaviorsDaemon pausing FSM")
                        fsm.pause()
                        # we press ESC to cancel any movement
                        # ActionQueueManager().AddAction("ACTION", Keystroke.PressAndReleaseCombo, [Key.Escape.value])
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
        if instance is None: pass

        # Local imports to avoid circular import with resign_if_needed -> botting_helpers
        from Sources.oazix.CustomBehaviors.skills.botting.move_if_stuck import MoveIfStuckUtility
        from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility

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
        if instance is None: pass

        # Local imports to avoid circular import with resign_if_needed -> botting_helpers
        from Sources.oazix.CustomBehaviors.skills.botting.move_to_distant_chest_if_path_exists import MoveToDistantChestIfPathExistsUtility
        from Sources.oazix.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
        from Sources.oazix.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
        from Sources.oazix.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
        from Sources.oazix.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
        from Sources.oazix.CustomBehaviors.skills.botting.wait_if_lock_taken import WaitIfLockTakenUtility
        from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
        from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
        from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility

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
    def __reset_botting_behavior(bot: Botting):
        
        properties = bot.Properties
        properties.Disable("pause_on_danger") #engage in combat
        properties.Disable("halt_on_death") 
        properties.Set("movement_timeout", value=-1)
        properties.Disable("auto_combat") #engage in combat
        properties.Disable("hero_ai") #hero combat     
        properties.Disable("auto_loot") #wait for loot
        properties.Disable("auto_inventory_management") #manage inventory

    # ---

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

        BottingFsmHelpers.__reset_botting_behavior(bot)

        # Create the daemon factory and register it with the loader for persistence across FSM restarts
        daemon_factory = lambda: BottingFsmHelpers.__custom_behaviors_botting_daemon(fsm)
        loader = CustomBehaviorLoader()
        loader.register_botting_daemon(fsm, daemon_factory)

        # Try to add immediately if FSM is already running
        if fsm.current_state is not None and not fsm.HasManagedCoroutine("CustomBehaviorsBottingDaemon"):
            print("CustomBehaviorsBottingDaemon AddManagedCoroutine (initial)")
            fsm.AddManagedCoroutine("CustomBehaviorsBottingDaemon", daemon_factory)

        event_bus = instance.event_bus
        subscriber_name = "CustomBehaviorsBottingDaemon"
        event_bus.unsubscribe_all(subscriber_name)
        event_bus.subscribe(EventType.PLAYER_CRITICAL_STUCK, BottingFsmHelpers.__wrapper_event_bus(on_player_critical_stuck) , subscriber_name=subscriber_name)
        event_bus.subscribe(EventType.PLAYER_CRITICAL_DEATH, BottingFsmHelpers.__wrapper_event_bus(on_player_critical_death), subscriber_name=subscriber_name)
        event_bus.subscribe(EventType.PARTY_DEATH, BottingFsmHelpers.__wrapper_event_bus(on_party_death), subscriber_name=subscriber_name)
    
    @staticmethod
    def PauseCustomBehavior(bot: Botting):
        instance = CustomBehaviorLoader().custom_combat_behavior
        if instance is None: raise Exception("CustomBehavior widget is required.")
        instance.clear_additionnal_utility_skills()
        CustomBehaviorParty().set_party_is_combat_enabled(True)
        CustomBehaviorParty().set_party_is_looting_enabled(True)
        BottingFsmHelpers.__reset_botting_behavior(bot)

    @staticmethod
    def SetBottingBehaviorAsAggressive(bot: Botting):
        instance = CustomBehaviorLoader().custom_combat_behavior
        if instance is not None:
            BottingFsmHelpers.UseCustomBehavior(bot)
            bot.config.FSM.AddManagedCoroutineStep("CustomBehavior_SetBottingBehaviorAsAggressive", lambda: BottingFsmHelpers._set_botting_behavior_as_aggressive(bot))
            BottingFsmHelpers.__reset_botting_behavior(bot)

    @staticmethod
    def SetBottingBehaviorAsPacifist(bot: Botting):
        instance = CustomBehaviorLoader().custom_combat_behavior
        if instance is not None:
            BottingFsmHelpers.UseCustomBehavior(bot)
            bot.config.FSM.AddManagedCoroutineStep("CustomBehavior_SetBottingBehaviorAsPacifist", lambda: BottingFsmHelpers._set_botting_behavior_as_pacifist(bot))
            BottingFsmHelpers.__reset_botting_behavior(bot)