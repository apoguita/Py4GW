#region CONFIG_TEMPLATES
from email import message
from typing import TYPE_CHECKING, List

from Py4GWCoreLib.routines_src.Agents import Routines

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass
    
#region TARGET
class _TEMPLATES:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self.Routines = self._Routines(parent)
        
    #region Property configuration

    def Pacifist(self):
        properties = self.parent.Properties
        properties.Disable("pause_on_danger") #avoid combat
        properties.Enable("halt_on_death") 
        properties.Set("movement_timeout",value=15000)
        properties.Disable("auto_combat") #avoid combat
        properties.Disable("hero_ai") #no hero combat     
        properties.Disable("auto_loot") #no waiting for loot
        properties.Disable("imp")

    def Aggressive(self, pause_on_danger: bool = True,
                   halt_on_death: bool = False,
                   movement_timeout: int = -1,
                   auto_combat: bool = True, 
                   auto_loot: bool = True,
                   enable_imp: bool = True):
        properties = self.parent.Properties
        if pause_on_danger:
            properties.Enable("pause_on_danger") #engage in combat
        else:
            properties.Disable("pause_on_danger") #avoid combat

        if halt_on_death:
            properties.Enable("halt_on_death")
        else:
            properties.Disable("halt_on_death")

        properties.Set("movement_timeout", value=movement_timeout)
        if auto_combat:
            properties.Enable("auto_combat") #engage in combat
            properties.Disable("hero_ai") #hero combat 
        else:
            properties.Disable("auto_combat") #avoid combat
         
        if auto_loot:   
            properties.Enable("auto_loot") #wait for loot
        else:
            properties.Disable("auto_loot") #no waiting for loot
            
        if enable_imp:
            properties.Enable("imp")
        else:
            properties.Disable("imp")
        
    def Multibox_Aggressive(self):
        properties = self.parent.Properties
        properties.Enable("pause_on_danger") #engage in combat
        properties.Disable("halt_on_death") 
        properties.Set("movement_timeout",value=-1)
        properties.Disable("auto_combat") #engage in combat
        properties.Enable("hero_ai") #hero combat     
        properties.Enable("auto_loot") #wait for loot
        properties.Enable("auto_inventory_management") #manage inventory



#region Routines
    class _Routines:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers

        def UseCustomBehaviors(self, map_id_to_travel:int | None = None):
            bot = self.parent
            fsm = self.parent.config.FSM
            bot.States.AddHeader("UseCustomBehaviors")

            def _custom_behaviors_daemon():
                from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
                print("CustomBehaviorsDaemon added")
                from ...Py4GWcorelib import ConsoleLog
                ConsoleLog("CustomBehaviorsDaemon", "added")
                injected = False
                while True:
                    # print("CustomBehaviorsDaemon running")
                    try:
                        instance = CustomBehaviorLoader().custom_combat_behavior
                        if instance is not None:
                            if not injected:
                                # some are not finalized
                                # from Widgets.CustomBehaviors.skills.botting.move_to_distant_chest_if_path_exists import MoveToDistantChestIfPathExistsUtility
                                from Widgets.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
                                from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
                                from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
                                from Widgets.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
                                from Widgets.CustomBehaviors.skills.botting.wait_if_lock_taken import WaitIfLockTakenUtility
                                from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
                                from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
                                from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility
                                # Optionally: ResignIfNeededUtility (enable when ready)
                                # from Widgets.CustomBehaviors.skills.botting.resign_if_needed import ResignIfNeededUtility
                                # instance.inject_additionnal_utility_skills(ResignIfNeededUtility(instance.event_bus, instance.in_game_build, on_failure=lambda: BottingHelpers.botting_unrecoverable_issue(bot.config.FSM)))

                                instance.inject_additionnal_utility_skills(MoveToPartyMemberIfInAggroUtility(instance.event_bus, instance.in_game_build))
                                instance.inject_additionnal_utility_skills(MoveToEnemyIfCloseEnoughUtility(instance.event_bus, instance.in_game_build))
                                instance.inject_additionnal_utility_skills(MoveToPartyMemberIfDeadUtility(instance.event_bus, instance.in_game_build))
                                instance.inject_additionnal_utility_skills(WaitIfPartyMemberManaTooLowUtility(instance.event_bus, instance.in_game_build))
                                instance.inject_additionnal_utility_skills(WaitIfPartyMemberTooFarUtility(instance.event_bus, instance.in_game_build))
                                instance.inject_additionnal_utility_skills(WaitIfPartyMemberNeedsToLootUtility(instance.event_bus, instance.in_game_build))
                                instance.inject_additionnal_utility_skills(WaitIfInAggroUtility(instance.event_bus, instance.in_game_build))
                                instance.inject_additionnal_utility_skills(WaitIfLockTakenUtility(instance.event_bus, instance.in_game_build))
                                injected = True

                            # Pause or resume FSM depending on CB utilities running
                            if instance.is_executing_utility_skills():
                                bot.config.FSM.pause()
                            else:
                                bot.config.FSM.resume()
                        else:
                            # If CB not available, ensure FSM is not stuck paused
                            bot.config.FSM.resume()
                    except Exception:
                        # Loader/widget might not be ready; try again later
                        pass
                    # yield control so FSM scheduler can run
                    yield from Routines.Yield.wait(250)

            # Attach to FSM safely across start/reset. If FSM already started, attach now; otherwise add a Step
            if fsm.current_state is not None:
                if not fsm.HasManagedCoroutine("CustomBehaviorsDaemon"):
                    print("CustomBehaviorsDaemon AddManagedCoroutine (runtime)")
                    fsm.AddManagedCoroutine("CustomBehaviorsDaemon", _custom_behaviors_daemon())
            else:
                # Not started yet: use a step so it attaches during run (start() clears managed_coroutines)
                if not fsm.has_state("CustomBehaviorsDaemon"):
                    print("CustomBehaviorsDaemon AddManagedCoroutineStep (pre-start)")
                    fsm.AddManagedCoroutineStep("CustomBehaviorsDaemon", _custom_behaviors_daemon)

            if map_id_to_travel is not None:
                bot.Map.Travel(target_map_id=map_id_to_travel)


        def OnPartyMemberBehind(self):
            bot = self.parent
            print ("Party Member behind, Triggered")
            fsm = bot.config.FSM
            fsm.pause()
            fsm.AddManagedCoroutine("OnBehind_OPD", self.parent.Events._on_party_member_behind())
            

        def OnPartyMemberDeathBehind(self):
            from ...Py4GWcorelib import ConsoleLog
            bot = self.parent
            ConsoleLog("on_party_member_dead_behind","event triggered")
            fsm = bot.config.FSM
            fsm.pause()
            fsm.AddManagedCoroutine("OnDeathBehind_OPD", lambda: self.parent.Events._on_party_member_death_behind())
                    
            
        def PrepareForFarm(self, map_id_to_travel:int):
            bot = self.parent
            bot.States.AddHeader("Prepare For Farm")
            bot.Events.OnPartyMemberBehindCallback(lambda: self.OnPartyMemberBehind())
            bot.Events.OnPartyMemberDeadBehindCallback(lambda: self.OnPartyMemberDeathBehind())
            bot.Multibox.KickAllAccounts()
            bot.Map.Travel(target_map_id=map_id_to_travel)
            bot.Multibox.SummonAllAccounts()
            bot.Wait.ForTime(4000)
            bot.Multibox.InviteAllAccounts()


       