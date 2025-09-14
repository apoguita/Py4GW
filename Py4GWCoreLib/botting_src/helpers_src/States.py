from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING

#region STATES
class _States:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        
    def insert_header_step(self, step_name: str) -> None:
        from ...Routines import Routines
        header_name = f"[H]{step_name}_{self._config.get_counter("HEADER_COUNTER")}"
        self._config.FSM.AddYieldRoutineStep(
            name=header_name,
            coroutine_fn=lambda: Routines.Yield.wait(100)
        )
        
    @_yield_step(label="JumpToStepName", counter_key="JUMP_TO_STEP_NAME")
    def jump_to_step_name(self, step_name: str) -> Generator[Any, Any, None]:
        self._config.FSM.pause()
        self._config.FSM.jump_to_state_by_name(step_name)
        self._config.FSM.resume()
        yield