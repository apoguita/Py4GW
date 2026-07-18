from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple

#region TARGET
class _Target:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events
        
    def _target_model(self, model_id:int):
        from ...Routines import Routines
        agent_id = Routines.Agents.GetAgentIDByModelID(model_id)
        if agent_id == 0:
            self._Events.on_unmanaged_fail()
            return False
        yield from Routines.Yield.Agents.ChangeTarget(agent_id)
        return True
    
    @_yield_step(label="TargetModelID", counter_key="TARGET_MODEL_ID")
    def model(self, model_id: int) -> Generator[Any, Any, bool]:
        return (yield from self._target_model(model_id))
        