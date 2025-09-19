#region STATES
from typing import TYPE_CHECKING, Dict, Callable, Any

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

class _STATES:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self.coroutines: Dict[str, Callable[[], Any]] = {}   # queued, name -> factory or generator

    def AddCustomState(self, execute_fn, name: str) -> None:
        self._config.FSM.AddYieldRoutineStep(name=name, coroutine_fn=execute_fn)

    def AddHeader(self, step_name: str) -> None:
        self._helpers.States.insert_header_step(step_name)

    def JumpToStepName(self, step_name: str) -> None:
        self._helpers.States.jump_to_step_name(step_name)

    def AddManagedCoroutine(self, name: str, coroutine_fn: Callable[[], Any]) -> None:
        """Queue a managed coroutine to be attached when the FSM is running."""
        # de-dupe against both queued and already-managed
        #if name in self.coroutines or self._config.FSM.HasManagedCoroutine(name):
        if self._config.FSM.HasManagedCoroutine(name):
            return
        #self.coroutines[name] = coroutine_fn
        self._config.FSM.AddManagedCoroutineStep(name, coroutine_fn)

    # (optional) helpers
    def RemoveManagedCoroutine(self, name: str) -> None:
        #self.coroutines.pop(name, None)
        self._config.FSM.RemoveManagedCoroutineStep(name)

    def HasQueuedCoroutine(self, name: str) -> bool:
        return name in self.coroutines
