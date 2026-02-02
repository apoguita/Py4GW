from typing import Callable, Generator, Any


class PartyCommandHandlerManager:
    """
    Handles command execution with generator-based actions.
    Provides a safe way to schedule and execute generator actions with proper
    error handling and state management.
    """
    
    def __init__(self):
        self._next_action: Generator | None = None
        self._action_finished: bool = True
    
    def schedule_action(self, action_gen: Callable[[], Generator]) -> bool:
        """
        Schedule a generator action. Returns True if accepted, False if busy.

        Args:
            action_gen: A callable that returns a generator when called

        Returns:
            True if the action was scheduled successfully, False if already busy
        """
        if self._action_finished and self._next_action is None:
            self._next_action = action_gen()
            self._action_finished = False
            return True
        return False
    
    def is_ready_for_action(self) -> bool:
        """
        Check if it's safe to schedule another action.
        
        Returns:
            True if no action is currently running, False otherwise
        """
        return self._action_finished and self._next_action is None
    
    def execute_next_step(self) -> None:
        """
        Execute the next step of the currently scheduled action.
        Handles StopIteration and other exceptions automatically.
        """
        if self._next_action:
            try:
                next(self._next_action)
            except StopIteration:
                # Action finished, clear slot
                self._next_action = None
                self._action_finished = True
            except Exception as e:
                print(f"Action failed: {e}")
                self._next_action = None
                self._action_finished = True
    
    def force_finish_current_action(self) -> None:
        """
        Forcefully finish the current action and reset state.
        Useful for emergency stops or when actions need to be cancelled.
        """
        self._next_action = None
        self._action_finished = True
    
    def get_current_action_status(self) -> tuple[Generator | None, bool]:
        """
        Get the current state of the command handler.
        
        Returns:
            A tuple containing (current_action_generator, is_finished)
        """
        return self._next_action, self._action_finished
