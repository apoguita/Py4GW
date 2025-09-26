from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple, List, Optional, Callable

#region WAIT             
class _Wait:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events
                
    def _for_time(self, duration: int = 100):
        from ...Routines import Routines
        yield from Routines.Yield.wait(duration)
        
    @_yield_step(label="WasteTime", counter_key="WASTE_TIME")
    def for_time(self, duration: int = 100):
        yield from self._for_time(duration)

    @_yield_step(label="WasteTimeUntilConditionMet", counter_key="WASTE_TIME")
    def until_condition(self, condition: Callable[[], bool], duration: int=1000):
        from ...Routines import Routines
        while True:
            yield from Routines.Yield.wait(duration)
            if condition():
                break
    
    def _for_map_load(self, target_map_id):
        from ...Routines import Routines
        import Py4GW
        wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(target_map_id,log=True, timeout=6000)
        if not wait_of_map_load:
            Py4GW.Console.Log("Wait for map load", "Map load failed.", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
                    
    @_yield_step(label="WaitForMapLoad", counter_key="WAIT_FOR_MAP_LOAD")
    def for_map_load(self, target_map_id):
        yield from self._for_map_load(target_map_id)
