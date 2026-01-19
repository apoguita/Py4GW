#region STATES
from typing import TYPE_CHECKING, Any, Generator

from Py4GWCoreLib.Map import Map

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

from ..helpers_src.decorators import _yield_step

#region MAP
class _MAP:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        
    #region coroutines (_coro_)
    def _coro_travel(self, target_map_id:int =0, target_map_name:str ="") -> Generator:
        from ...Routines import Routines
        
        if not Map.IsMapReady():
            yield from Routines.Yield.wait(1000)
            return
        
        if target_map_name:
            target_map_id = Map.GetMapIDByName(target_map_name)
        
        current_map_id = Map.GetMapID()

        if current_map_id == target_map_id:
            yield from Routines.Yield.wait(1000)
            return
        
        Map.Travel(target_map_id)
        yield from Routines.Yield.wait(500)
        
        yield from self.parent.Wait._coro_for_map_load(target_map_id=target_map_id, target_map_name=target_map_name)
    
    def _coro_enter_challenge(self, wait_for:int= 3000, target_map_id: int = 0, target_map_name: str = "") -> Generator:
        from ...Routines import Routines
        Map.EnterChallenge()
        yield from Routines.Yield.wait(wait_for)
        yield from self.parent.Wait._coro_for_map_load(target_map_id=target_map_id, target_map_name=target_map_name)
    
    def _coro_travel_to_gh(self, wait_time:int= 1000):
        from ...Routines import Routines
        Map.TravelGH()
        yield from Routines.Yield.wait(wait_time)
        yield from self.parent.Wait._coro_until_on_outpost()
        
    def _coro_leave_gh(self, wait_time:int= 1000):
        from ...Routines import Routines
        Map.LeaveGH()
        yield from Routines.Yield.wait(wait_time)
        yield from self.parent.Wait._coro_until_on_outpost()
            
    #region yield Steps (ys_)
    @_yield_step(label="Travel", counter_key="TRAVEL")
    def ys_travel(self, target_map_id, target_map_name) -> Generator:
        yield from self._coro_travel(target_map_id, target_map_name)
    
    @_yield_step(label="EnterChallenge", counter_key="ENTER_CHALLENGE")
    def ys_enter_challenge(self, wait_for:int= 3000, target_map_id: int = 0, target_map_name: str = "") -> Generator:
        yield from self._coro_enter_challenge(wait_for, target_map_id, target_map_name)

    @_yield_step(label="TravelGH", counter_key="TRAVEL")
    def ys_travel_gh(self, wait_time:int= 1000) -> Generator:
        yield from self._coro_travel_to_gh(wait_time)
        
    @_yield_step(label="LeaveGH", counter_key="TRAVEL")
    def ys_leave_gh(self, wait_time:int= 1000) -> Generator:
        yield from self._coro_leave_gh(wait_time)

    #region public Helpers
    def Travel(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        self.ys_travel(target_map_id, target_map_name)

    def TravelGH(self, wait_time:int=4000):
        self.ys_travel_gh(wait_time=wait_time)

    def LeaveGH(self, wait_time:int=4000):
        self.ys_leave_gh(wait_time=wait_time)

    def EnterChallenge(self, delay:int= 4500, target_map_id: int = 0, target_map_name: str = "") -> None:
        self.ys_enter_challenge(wait_for=delay, target_map_id=target_map_id, target_map_name=target_map_name)
