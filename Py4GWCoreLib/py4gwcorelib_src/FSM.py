#region FSM

import Py4GW
import traceback
from typing import Optional

from .Timer import Timer, ThrottledTimer
from .Console import ConsoleLog, Console

class FSM:

    def __init__(self, name, log_actions=False):
        """
        Initialize the FSM with a name and track its states and transitions.
        :param name: The name of the FSM (for logging and identification purposes).
        """
        self.name = name  # Store the FSM name
        self.states = []  # List to store all states in order
        self.current_state = None  # Track the current state
        self.state_counter = 0  # Internal counter for state IDs
        self.log_actions = log_actions  # Whether to log state transitions and actions
        self.finished = False  # Track whether the FSM has completed all states
        self.paused = False
        self.on_transition = None
        self.on_complete = None
        self.managed_coroutines = []   # already added for self-managed coroutines
        self._named_managed = {}       # key -> generator instance
        self.delay_timer = ThrottledTimer()
    
    #region State
    class State:
        def __init__(self, id, name=None, execute_fn=None, exit_condition=None, transition_delay_ms=0, run_once=True, on_enter=None, on_exit=None):
            """
            :param id: Internal ID of the state.
            :param name: Optional name of the state (for debugging purposes).
            :param execute_fn: A function representing the block of code to be executed in this state.
            :param exit_condition: A function that returns True/False to determine if it can transition to the next state.
            :param run_once: Whether the execution function should run only once (default: True).
            :param transition_delay_ms: Delay in milliseconds before checking the exit condition (default: 0).
            """
            self.id = id
            self.name = name or f"State-{id}"  # If no name is provided, use "State-ID"
            self.execute_fn = execute_fn or (lambda: None)  # Default to no action if not provided
            self.exit_condition = exit_condition or (lambda: True)  # Default to False if not provided
            self.run_once = run_once  # Flag to control whether the action runs once or repeatedly
            self.executed = False  # Track whether the state's execute function has been run
            self.transition_delay_ms = transition_delay_ms  # Delay before transitioning to the next state
            self.transition_timer = Timer()  # Timer to manage the delay
            self.on_enter = on_enter or (lambda: None)
            self.on_exit = on_exit or (lambda: None)
            self.next_state = None
            self.event_transitions = {}

        def enter(self):
            self.on_enter()

        def exit(self):
            self.on_exit()

        def reset_transition_timer(self):
            self.transition_timer.Reset()

        def execute(self):
            """Run the state's block of code. If `run_once` is True, run it only once."""
            if not self.run_once or not self.executed:
                self.execute_fn()
                if not self.executed:  # Only reset timer on first execution
                    self.reset_transition_timer()
                self.executed = True

        def can_exit(self):
            """
            Check if the exit condition is met and if the transition delay has passed.
            """
            if not self.transition_timer.HasElapsed(self.transition_delay_ms):
                return False
            
            return self.exit_condition()
            
        def reset(self):
            """Reset the state so it can be re-entered, if needed."""
            self.executed = False
            self.transition_timer.Stop()  # Reset timer when resetting the state

        def set_next_state(self, next_state):
            """Set the next state for transitions."""
            self.next_state = next_state
        
        def add_event_transition(self, event_name: str, target_state_name: str):
            """
            Define a transition triggered by a specific event.

            :param event_name: The name of the event that triggers this transition.
            :param target_state_name: The name of the state to transition to.
            """
            if not isinstance(event_name, str) or not isinstance(target_state_name, str):
                raise TypeError("Event name and target state name must be strings.")
            self.event_transitions[event_name] = target_state_name
     
    #region ConditionState  
    class ConditionState(State):
        def __init__(self, id, name=None, condition_fn=None, sub_fsm=None,
                 on_enter=None, on_exit=None, log_actions=False):
            """
            A state that evaluates a condition and decides whether to continue or run a sub-FSM.

            :param condition_fn: Function that returns True/False. If True,
                                 it runs the sub_fsm and waits for it to finish before transitioning.
            :param sub_fsm: An optional sub-FSM that will be run if condition_fn returns False.
            """
            super().__init__(id, name, on_enter=on_enter, on_exit=on_exit)
            self.condition_fn = condition_fn or (lambda: True)  # Default to True if no condition provided
            self.sub_fsm = sub_fsm
            self.sub_fsm_active = False
            self.log_actions = log_actions

        def execute(self):
            """
            Execute the condition function. If it returns False, mark the state as completed.
            If it returns True, start the subroutine FSM (if provided).
            """
            if self.sub_fsm_active:
                # If the sub-FSM is running, update it and check if it is finished
                if self.sub_fsm and not self.sub_fsm.is_finished():
                    self.sub_fsm.update()
                    return
                self.sub_fsm_active = False  # Sub-FSM finished, can continue execution
                self.executed = True
                self.reset_transition_timer()  # Fix missing timer reset
                return

                # Evaluate the condition
            if not self.condition_fn():
                self.executed = True  # Condition not met, continue to the next state
                self.reset_transition_timer()  # Fix missing timer reset
                return
            
            if self.sub_fsm and not self.sub_fsm_active:
                # Condition met, start the sub-FSM
                if self.log_actions:
                    ConsoleLog("FSM", f"Starting FSM Subroutine", Console.MessageType.Success)
                self.sub_fsm.reset()
                self.sub_fsm.start()
                self.sub_fsm_active = True
            else:
                self.executed = True  # Ensure exit is possible if no sub_fsm
                self.reset_transition_timer()  # Fix missing timer reset
            
        def can_exit(self):
            """
            The node can exit only if the condition is met or the sub-FSM has finished running.
            """
            return self.executed and not self.sub_fsm_active
        
        def reset(self):
            super().reset()
            self.sub_fsm_active = False
            if self.sub_fsm:
                self.sub_fsm.reset()
      
    #region YieldRoutineState  
    class YieldRoutineState(State):
        def __init__(self, id, name=None, coroutine_fn=None):
            """
            A state that runs a yield-based coroutine and waits for it to complete.

            :param coroutine_fn: A function that returns a generator (yield-based coroutine)
            """
            super().__init__(id=id, name=name or f"YieldRoutine-{id}")
            self.coroutine_fn = coroutine_fn
            self.coroutine_instance = None

        def execute(self):
            from Py4GWCoreLib import GLOBAL_CACHE
            if not self.executed:
                if self.coroutine_fn:
                    try:
                        self.coroutine_instance = self.coroutine_fn()
                        if self.coroutine_instance:
                            GLOBAL_CACHE.Coroutines.append(self.coroutine_instance)
                    except Exception as e:
                        ConsoleLog("FSM", f"Error starting coroutine for state '{self.name}': {e}", Console.MessageType.Error)
                self.reset_transition_timer()
                self.executed = True

        def can_exit(self):
            from Py4GWCoreLib import GLOBAL_CACHE
            """
            Exit only if coroutine is finished.
            """
            if not self.transition_timer.HasElapsed(self.transition_delay_ms):
                return False

            # Check if coroutine is no longer running
            if self.coroutine_instance and self.coroutine_instance in GLOBAL_CACHE.Coroutines:
                return False  # Still running

            return True
        
        def reset(self):
            super().reset()
            from Py4GWCoreLib import GLOBAL_CACHE
            if self.coroutine_instance and self.coroutine_instance in GLOBAL_CACHE.Coroutines:
                try:
                    GLOBAL_CACHE.Coroutines.remove(self.coroutine_instance)
                except ValueError:
                    pass
            self.coroutine_instance = None
  
    #region SelfManagedYieldState
    class SelfManagedYieldState(State):
        def __init__(self, id, fsm, name=None, coroutine_fn=None):
            super().__init__(id=id, name=name or f"SelfYield-{id}")
            self._fsm = fsm
            self.coroutine_fn = coroutine_fn
            self.coroutine_instance = None

        def execute(self):
            # Exactly like YieldRoutineState's start, but register into FSM list (not GLOBAL_CACHE)
            if not self.executed:
                if self.coroutine_fn:
                    try:
                        self.coroutine_instance = self.coroutine_fn()
                        if self.coroutine_instance:
                            self._fsm.managed_coroutines.append(self.coroutine_instance)
                    except Exception as e:
                        ConsoleLog("FSM", f"Error starting self-managed coroutine for state '{self.name}': {e}", Console.MessageType.Error)
                self.reset_transition_timer()
                self.executed = True

        def can_exit(self):
            # Wait until the coroutine finishes (i.e., is no longer in the FSM list),
            # and the transition delay (if any) has elapsed.
            if not self.transition_timer.HasElapsed(self.transition_delay_ms):
                return False
            if self.coroutine_instance and self.coroutine_instance in self._fsm.managed_coroutines:
                return False
            return True

        def reset(self):
            super().reset()
            # If we jump back or reset while the gen is still tracked, detach it
            if self.coroutine_instance and self.coroutine_instance in self._fsm.managed_coroutines:
                try:
                    self._fsm.managed_coroutines.remove(self.coroutine_instance)
                except ValueError:
                    pass
            self.coroutine_instance = None

        
    #region FSM Methods 
    def SetLogBehavior(self, log_actions=False):
        """
        Set whether to log state transitions and actions.
        :param log_actions: Whether to log state transitions and actions (default: False).
        """
        self.log_actions = log_actions

    def GetLogBehavior(self):
        """Get the current logging behavior setting."""
        return self.log_actions

    def AddState(self, name=None, execute_fn=None, exit_condition=None, transition_delay_ms=0, run_once=True, on_enter=None, on_exit=None):
        """Add a state with an optional name, execution function, and exit condition."""
        state = FSM.State(
            id=self.state_counter,
            name=name,
            execute_fn=execute_fn,
            exit_condition=exit_condition,
            run_once=run_once,
            transition_delay_ms=transition_delay_ms,
            on_enter=on_enter,
            on_exit=on_exit
        )
        
        if self.states:
            self.states[-1].set_next_state(state)
        
        self.states.append(state)
        self.state_counter += 1
        
    def AddYieldRoutineStep(self, name, coroutine_fn, transition_delay_ms=0):
        """
        Add a yield-based coroutine step to the FSM.
        The coroutine is added to GLOBAL_CACHE.Coroutines and the FSM waits until it finishes.

        :param name: Name of the state.
        :param coroutine_fn: Function that returns a yield-based generator.
        """
        step = self.YieldRoutineState(
            id=self.state_counter,
            name=name,
            coroutine_fn=coroutine_fn
        )
        step.transition_delay_ms = transition_delay_ms
        if self.states:
            self.states[-1].set_next_state(step)
        self.states.append(step)
        self.state_counter += 1

    def AddSelfManagedYieldStep(self, name, coroutine_fn, transition_delay_ms=0):
        step = FSM.SelfManagedYieldState(
            id=self.state_counter,
            fsm=self,
            name=name,
            coroutine_fn=coroutine_fn
        )
        step.transition_delay_ms = transition_delay_ms
        if self.states:
            self.states[-1].set_next_state(step)
        self.states.append(step)
        self.state_counter += 1



    def AddSubroutine(self, name=None, condition_fn=None, sub_fsm=None,
                  on_enter=None, on_exit=None):
        """Add a condition node that evaluates a condition and can run a subroutine FSM."""
        condition_node = FSM.ConditionState(
            id=self.state_counter,
            name=name,
            condition_fn=condition_fn,
            sub_fsm=sub_fsm,
            on_enter=on_enter,
            on_exit=on_exit,
            log_actions=self.log_actions
        )
        if self.states:
            self.states[-1].set_next_state(condition_node)
        self.states.append(condition_node)
        self.state_counter += 1
            
    def _cleanup_coroutines(self):
        """Detach any generators this FSM started, to avoid duplicates on start/reset/stop."""
        # clear the central list
        self.managed_coroutines.clear()
        # clear per-state handles (SelfManagedYieldState only)
        for s in self.states:
            if hasattr(FSM, "SelfManagedYieldState") and isinstance(s, FSM.SelfManagedYieldState):
                s.coroutine_instance = None


    def start(self):
        """Start the FSM by setting the initial state."""
        if not self.states:
            raise ValueError(f"{self.name}: No states have been added to the FSM.")
        self._cleanup_coroutines()
        self.current_state = self.states[0]
        self.finished = False
        ConsoleLog("FSM", f"{self.name}: Starting FSM with initial state: {self.current_state.name}", Console.MessageType.Success)

    def stop(self):
        """Stop the FSM and mark it as finished."""
        self._cleanup_coroutines()
        self.current_state = None
        self.finished = True

        if self.log_actions:
            ConsoleLog("FSM", f"{self.name}: FSM has been stopped by user.", Console.MessageType.Info)

    def reset(self):
        """Reset the FSM to the initial state without starting it."""
        if not self.states:
            raise ValueError(f"{self.name}: No states have been added to the FSM.")
        self._cleanup_coroutines()
        self.current_state = self.states[0]  # Reset to the first state
        self.finished = False
        for state in self.states:
            state.reset()  # Reset all states

        if self.log_actions:
            ConsoleLog("FSM", f"{self.name}: FSM has been reset.", Console.MessageType.Info)
            
    def ResetAndStartAtStep(self, state_name: str):
        """
        Fully reset the FSM, clear all managed coroutines, and jump directly to the specified step.

        This is especially useful for recovery situations (e.g. party wipe) where
        the FSM must restart cleanly but resume execution at a specific entry point.
        """
        if not self.states:
            raise ValueError(f"{self.name}: No states have been added to the FSM.")

        # --- Step 1: Clean up all coroutine and state references ---
        #self._cleanup_coroutines()
        #for state in self.states:
        #    state.reset()

        # --- Step 2: Reset finished/paused flags ---
        self.finished = False
        self.paused = False

        # --- Step 3: Find and jump to the desired state ---
        target_state = None
        for s in self.states:
            if s.name == state_name:
                target_state = s
                break

        if not target_state:
            raise ValueError(f"{self.name}: State '{state_name}' not found.")

        self.current_state = target_state
        self.current_state.reset()
        self.current_state.enter()

        # --- Step 4: Logging and resume ---
        if self.log_actions:
            ConsoleLog("FSM",
                    f"{self.name}: Reset and started at step '{state_name}'",
                    Console.MessageType.Success)

        # Ensure FSM resumes execution after being paused
        self.paused = False


    def get_state_names(self):
        return [s.name for s in self.states]

    def terminate(self):
        if self.log_actions:
            ConsoleLog("FSM", f"{self.name}: Terminated forcefully.", Console.MessageType.Warning)
        self.current_state = None
        self.finished = True

    def run_until(self, condition_fn):
        while not self.finished and not condition_fn():
            self.update()
    
    def set_completion_callback(self, callback_fn):
        self.on_complete = callback_fn
    
    def get_current_state_index(self):
        if not self.current_state or self.current_state not in self.states:
            return -1
        return self.states.index(self.current_state)

    def get_next_state_index(self):
        if not self.current_state:
            return -1
        next_state = getattr(self.current_state, 'next_state', None)
        if not next_state or next_state not in self.states:
            return -1
        return self.states.index(next_state)

    def interrupt(self, fn):
        if not self.current_state:
            return
        original_exit = self.current_state.exit

        def wrapped_exit():
            original_exit()
            fn()

        self.current_state.exit = wrapped_exit
    
    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def is_paused(self):
        return self.paused

    def set_transition_callback(self, callback_fn):
        self.on_transition = callback_fn

    def has_state(self, name):
        return any(s.name == name for s in self.states)

    def restart(self):
        self.reset()
        self.start()

    def AddWaitState(self, name, condition_fn, timeout_ms=10000, on_timeout=None, on_enter=None, on_exit=None):
        timer = Timer()
        def exit_fn():
            if condition_fn():
                return True
            if timer.HasElapsed(timeout_ms):
                if on_timeout:
                    try:
                        on_timeout()
                    except Exception as e:
                        if self.log_actions:
                            ConsoleLog("FSM", f"Error in on_timeout for state '{name}': {e}", Py4GW.Console.MessageType.Error)
                return True
            return False

        wait_state = FSM.State(
            id=self.state_counter,
            name=name,
            execute_fn=lambda: None,
            exit_condition=exit_fn,
            run_once=True,
            on_enter=on_enter,      # <-- PASS on_enter
            on_exit=on_exit 
        )
        wait_state.transition_timer = timer
        if self.states:
            self.states[-1].set_next_state(wait_state)

        self.states.append(wait_state)
        self.state_counter += 1

    def trigger_event(self, event_name: str) -> bool:
        """
        Triggers an event, potentially causing an immediate state transition
        if the current state is configured to handle it.

        :param event_name: The name of the event to trigger.
        :return: True if the event caused a transition, False otherwise.
        """
        if self.paused or self.finished or not self.current_state:
            return False # Cannot transition if paused, finished, or not started

        target_state_name = self.current_state.event_transitions.get(event_name)

        if target_state_name:
            target_state = self._get_state_by_name(target_state_name)
            if target_state:
                if self.log_actions:
                    ConsoleLog("FSM", f"{self.name}: Event '{event_name}' triggered transition from '{self.current_state.name}' to '{target_state.name}'", Py4GW.Console.MessageType.Info)

                # --- Perform Transition ---
                original_state_name = self.current_state.name
                self.current_state.exit()

                if self.on_transition:
                    try:
                        self.on_transition(original_state_name, target_state.name)
                    except Exception as e:
                         ConsoleLog("FSM", f"Error in on_transition callback during event '{event_name}': {e}", Py4GW.Console.MessageType.Error)


                self.current_state = target_state
                self.current_state.reset() # Reset the new state
                self.current_state.enter()
                # --- End Transition ---

                return True
            else:
                # Log error: target state name defined but not found
                ConsoleLog("FSM", f"{self.name}: Event '{event_name}' defined transition to unknown state '{target_state_name}' from state '{self.current_state.name}'", Py4GW.Console.MessageType.Error)
                return False
        else:
            # Event not handled by the current state
            if self.log_actions:
                 ConsoleLog("FSM", f"{self.name}: Event '{event_name}' triggered but not handled by current state '{self.current_state.name}'", Py4GW.Console.MessageType.Debug)
            return False

    def update(self):
        
        if not self.current_state:
            if self.log_actions:
                ConsoleLog("FSM", f"{self.name}: FSM has not been started.", Py4GW.Console.MessageType.Warning)
            return
        
        if self.finished:
            if self.log_actions:
                ConsoleLog("FSM", f"{self.name}: FSM has finished.", Py4GW.Console.MessageType.Warning)
            return
        
        # Advance self-managed coroutines (same pattern as GLOBAL_CACHE.Coroutines)
        for routine in self.managed_coroutines[:]:
            try:
                next(routine)
            except StopIteration:
                self.managed_coroutines.remove(routine)
            except Exception as e:
                state_name = self.current_state.name if self.current_state else "Unknown"
                tb = traceback.format_exc()
                ConsoleLog(
                    "FSM",
                    f"Error in self-managed coroutine at state '{state_name}': {e}\nTraceback:\n{tb}",
                    Console.MessageType.Error
                )
                try:
                    self.managed_coroutines.remove(routine)
                except ValueError:
                    pass
                
        if self.paused:
            if self.log_actions:
                ConsoleLog("FSM", f"{self.name}: FSM is paused.", Py4GW.Console.MessageType.Warning)
            return
        

        if self.log_actions:
            ConsoleLog("FSM", f"{self.name}: Executing state: {self.current_state.name}", Py4GW.Console.MessageType.Info)
        self.current_state.execute()

        if not self.current_state.can_exit():
            return

        self.current_state.exit()
        next_state_polling = getattr(self.current_state, 'next_state', None) # Get the *original* next_state
        
        if next_state_polling:
            original_state_name = self.current_state.name # Store name before changing
            if self.on_transition:
                 try:
                     self.on_transition(original_state_name, next_state_polling.name)
                 except Exception as e:
                     ConsoleLog("FSM", f"Error in on_transition callback during polling transition: {e}", Py4GW.Console.MessageType.Error)
            
            self.current_state = next_state_polling
            self.current_state.reset()
            self.current_state.enter()

            if self.log_actions:
                ConsoleLog("FSM", f"{self.name}: Transitioning to state: {self.current_state.name}", Py4GW.Console.MessageType.Info)
            return

        final_state_name = self.current_state.name
        self.current_state = None
        self.finished = True

        if self.log_actions:
            ConsoleLog("FSM", f"{self.name}: Reached the final state: {final_state_name}. FSM has completed.", Py4GW.Console.MessageType.Success)
        
        if self.on_complete:
            try:
                self.on_complete()
            except Exception as e:
                ConsoleLog("FSM", f"Error in on_complete callback: {e}", Py4GW.Console.MessageType.Error)

    def is_started(self):
        """Check whether the FSM has been started."""
        return self.current_state is not None and not self.finished
                
    def is_finished(self):
        """Check whether the FSM has finished executing all states."""
        return self.finished

    def jump_to_state_by_name(self, state_name):
        """Jump to a specific state by its name."""
        for state in self.states:
            if state.name == state_name:
                self.current_state = state
                self.current_state.reset() # Reset the state upon jumping to it
                self.current_state.enter()
                if self.log_actions:
                    Py4GW.Console.Log("FSM", f"{self.name}: Jumped to state: {self.current_state.name}", Py4GW.Console.MessageType.Info)
                return
        raise ValueError(f"State with name '{state_name}' not found.")
    
    def jump_to_state_by_step_number(self, index):
        """Jump to a specific state by its index (0-based)."""
        if 0 <= index < len(self.states):
            self.current_state = self.states[index]
            self.current_state.reset() # Reset the state upon jumping to it
            self.current_state.enter()
            if self.log_actions:
                Py4GW.Console.Log("FSM", f"{self.name}: Jumped to state: {self.current_state.name}", Py4GW.Console.MessageType.Info)
            return
        raise IndexError(f"State index '{index}' is out of range.")

    def get_current_state_number(self):
        """Get the current state number (index) in the FSM."""
        if self.current_state is None:
            return 0
        return self.states.index(self.current_state) + 1

    def get_state_count (self):
        """Get the total number of states in the FSM."""
        return len(self.states)

    def get_state_number_by_name(self, state_name):
        """Get the step number (index) by the state name."""
        for idx, state in enumerate(self.states):
            if state.name == state_name:
                return idx + 1
        return 0
    
    def get_state_name_by_number(self, state_number):
        """Get the state name by its number (index)."""
        if 1 <= state_number <= len(self.states):
            return self.states[state_number - 1].name
        return None

    def get_current_step_name(self):
        """Get the name of the current step (state) in the FSM."""
        if self.current_state is None:
            return f"{self.name}: FSM not started or finished"
        return self.current_state.name

    def get_next_step_name(self):
        """Get the name of the next step (state) in the FSM."""
        if self.current_state is None:
            return f"{self.name}: FSM not started or finished"
        if hasattr(self.current_state, 'next_state') and self.current_state.next_state:
            return self.current_state.next_state.name
        return f"{self.name}: No next state (final state reached)"

    def get_previous_step_name(self):
        """Get the name of the previous step (state) in the FSM."""
        if self.current_state is None:
            return f"{self.name}: FSM not started or finished"
        current_index = self.states.index(self.current_state)
        if current_index > 0:
            return self.states[current_index - 1].name
        return f"{self.name}: No previous state (first state)"
    
    def _get_state_by_name(self, state_name: str) -> Optional[State]:
        """Finds a state object by its name."""
        for state in self.states:
            if state.name == state_name:
                return state
        return None

    #Self managed external Coroutine handling
    # these coroutines are not scheduled in the FSM
    # we are managing their lifecycle manually
    # using the automatic yield of the FSM
    
    def _as_generator(self, obj):
        """Return a generator from obj (call if callable), or None on failure."""
        try:
            gen = obj() if callable(obj) else obj
            if gen is None:
                return None
            # rudimentary generator protocol check
            if hasattr(gen, "__next__") and hasattr(gen, "send"):
                return gen
        except Exception as e:
            ConsoleLog("FSM", f"{self.name}: Error creating generator: {e}", Py4GW.Console.MessageType.Error)
        return None

    def _add_managed(self, gen):
        """Attach generator to FSM-managed list (no duplicates)."""
        if gen and gen not in self.managed_coroutines:
            self.managed_coroutines.append(gen)
            return True
        return False

    def _remove_managed(self, gen):
        """Detach generator from FSM-managed list."""
        try:
            self.managed_coroutines.remove(gen)
            return True
        except ValueError:
            return False

    def AddManagedCoroutine(self, name: str, routine_or_fn) -> bool:
        """
        Attach a generator (or factory) under a required name.
        - No-ops if the same name is already attached and still managed.
        """
        # de-dupe by name
        existing = self._named_managed.get(name)
        if existing and existing in self.managed_coroutines:
            return False  # already attached under this name
        
        gen = self._as_generator(routine_or_fn)
        if not gen:
            return False

        # drop stale mapping if any
        if existing and existing not in self.managed_coroutines:
            self._named_managed.pop(name, None)

        if not self._add_managed(gen):
            return False

        self._named_managed[name] = gen
        return True
    
    def AddManagedCoroutineStep(self, name: str, coroutine_fn, transition_delay_ms=0):
        """
        Add a state that will attach a managed coroutine at runtime.
        This allows coroutines to start only when the FSM reaches this step.
        """
        def _starter():
            self.AddManagedCoroutine(name, coroutine_fn)

        step = FSM.State(
            id=self.state_counter,
            name=name,
            execute_fn=_starter,
            exit_condition=lambda: True,  # move on immediately
            run_once=True
        )
        step.transition_delay_ms = transition_delay_ms

        if self.states:
            self.states[-1].set_next_state(step)

        self.states.append(step)
        self.state_counter += 1


    def RemoveManagedCoroutine(self, name: str) -> bool:
        """
        Detach the coroutine registered under 'name'.
        """
        gen = self._named_managed.pop(name, None)
        if not gen:
            return False
        return self._remove_managed(gen)
    
    def RemoveManagedCoroutineStep(self, name: str):
        """
        Add a state that will detach a managed coroutine at runtime.
        This allows coroutines to stop only when the FSM reaches this step.
        """
        def _stopper():
            self.RemoveManagedCoroutine(name)

        step = FSM.State(
            id=self.state_counter,
            name=f"Remove-{name}",
            execute_fn=_stopper,
            exit_condition=lambda: True,  # move on immediately
            run_once=True
        )

        if self.states:
            self.states[-1].set_next_state(step)

        self.states.append(step)
        self.state_counter += 1

    def RemoveAllManagedCoroutines(self) -> int:
        n = len(self.managed_coroutines)
        self.managed_coroutines.clear()
        self._named_managed.clear()
        return n

    def HasManagedCoroutine(self, name: str) -> bool:
        gen = self._named_managed.get(name)
        return bool(gen and gen in self.managed_coroutines)

    def AdoptGlobalCoroutine(self, routine, remove_from_global: bool = True) -> bool:
        from ..GlobalCache import GLOBAL_CACHE
        """
        Move (or copy) a generator from GLOBAL_CACHE.Coroutines into FSM-managed list.
        """
        if routine is None:
            return False
        if remove_from_global:
            try:
                GLOBAL_CACHE.Coroutines.remove(routine)
            except ValueError:
                pass
        return self._add_managed(routine)


#endregion