from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers

# Internal decorator factory (class-scope function)
def yield_step(label: str,counter_key: str):
    def deco(coro_method):
        @wraps(coro_method)
        def wrapper(self:"BottingHelpers", *args, **kwargs):
            step_name = f"{label}_{self._config.get_counter(counter_key)}"
            self._config.FSM.AddSelfManagedYieldStep(
                name=step_name,
                coroutine_fn=lambda: coro_method(self, *args, **kwargs)
            )
            # Return immediately; FSM will run the coroutine later
        return wrapper
    return deco

_yield_step = staticmethod(yield_step)

def fsm_step(label: str,counter_key: str):
    def deco(fn):
        @wraps(fn)
        def wrapper(self:"BottingHelpers", *args, **kwargs) -> None:
            step_name = f"{label}_{self._config.get_counter(counter_key)}"
            # Schedule a NORMAL FSM state (non-yield)
            self._config.FSM.AddState(
                name=step_name,
                execute_fn=lambda: fn(self, *args, **kwargs)
            )
        return wrapper
    return deco

_fsm_step = staticmethod(fsm_step)