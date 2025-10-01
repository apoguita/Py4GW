from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple, List, Optional, Callable

#region MAP
class _Map:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events      

    def _travel(self, target_map_id):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        
        current_map_id = GLOBAL_CACHE.Map.GetMapID()
        if current_map_id == target_map_id:
            return
        
        GLOBAL_CACHE.Map.Travel(target_map_id)
        yield from Routines.Yield.wait(1000)
        
    @_yield_step(label="Travel", counter_key="TRAVEL")
    def travel(self, target_map_id):
        yield from self._travel(target_map_id)
    
    @_yield_step(label="TravelToGH", counter_key="TRAVEL") 
    def travel_to_gh(self, wait_time:int= 1000):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        GLOBAL_CACHE.Map.TravelGH()
        yield from Routines.Yield.wait(wait_time)

    @_yield_step(label="LeaveGH", counter_key="TRAVEL")
    def leave_gh(self, wait_time:int= 1000):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        GLOBAL_CACHE.Map.LeaveGH()
        yield from Routines.Yield.wait(wait_time)
        
    @_yield_step(label="EnterChallenge", counter_key="ENTER_CHALLENGE")
    def enter_challenge(self, wait_for:int= 3000):
        from ...GlobalCache import GLOBAL_CACHE
        from ...Routines import Routines
        GLOBAL_CACHE.Map.EnterChallenge()
        yield from Routines.Yield.wait(wait_for)
