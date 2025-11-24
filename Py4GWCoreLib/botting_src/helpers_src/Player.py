from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple

#region TARGET
class _Player:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events
    
    @_yield_step(label="SetTitle", counter_key="SET_TITLE")
    def set_title(self, title: int) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        yield from Routines.Yield.Player.SetTitle(title, False)
        
    @_yield_step(label="CallTarget", counter_key="CALL_TARGET")
    def call_target(self) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        yield from Routines.Yield.Keybinds.CallTarget(False)
