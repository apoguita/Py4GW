#region STATES
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass
    
from ..helpers_src.decorators import _yield_step
    
#region WAIT
class _WAIT:
    from ...enums import Range
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self._Events = parent.helpers.Events
        
    #region coroutines (_coro_)
    def _coro_for_time(self, duration: int = 100):
        from ...Routines import Routines
        yield from Routines.Yield.wait(duration)
        
    def _coro_for_map_load(self, target_map_id, target_map_name=""):
        from ...Routines import Routines
        import Py4GW
        wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(target_map_id,log=True, timeout=10000, map_name=target_map_name)
        if not wait_of_map_load:
            Py4GW.Console.Log("Wait for map load", "Map load failed.", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            
    def _coro_until_condition(self, condition: Callable[[], bool], duration: int=1000):
        from ...Routines import Routines
        while True:
            yield from Routines.Yield.wait(duration)
            if condition():
                break
                    
    def _coro_until_out_of_combat(self, range: Range = Range.Earshot):
        from ...Routines import Routines
        wait_condition = lambda: not(Routines.Checks.Agents.InDanger(aggro_area=range))
        yield from self._coro_until_condition(wait_condition)
        
    def _coro_until_on_combat(self, range: Range = Range.Earshot):
        from ...Routines import Routines
        wait_condition = lambda: Routines.Checks.Agents.InDanger(aggro_area=range)
        yield from self._coro_until_condition(wait_condition)
        
    def _coro_until_on_outpost(self):
        from ...Routines import Routines
        wait_condition = lambda: Routines.Checks.Map.MapValid() and  Routines.Checks.Map.IsOutpost()
        yield from self._coro_until_condition(wait_condition)
    
    def _coro_until_on_explorable(self):
        from ...Routines import Routines
        wait_condition = lambda: Routines.Checks.Map.MapValid() and  Routines.Checks.Map.IsExplorable()
        yield from self._coro_until_condition(wait_condition)
        
    def _coro_until_model_has_quest(self, model_id: int):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        from ...enums import Range
        wait_function = lambda: (
            not (Routines.Checks.Agents.InDanger(aggro_area=Range.Spirit)) and
            GLOBAL_CACHE.Agent.HasQuest(Routines.Agents.GetAgentIDByModelID(model_id))
        )
        yield from self._coro_until_condition(wait_function, duration=1000)
        
    def _coro_for_map_to_change(self, target_map_id: int = 0, target_map_name: str = ""):
        """Waits until all action finishes in current map and game sends you to a new one"""
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE

        wait_condition = lambda: (
            not GLOBAL_CACHE.Map.IsMapLoading()
            and Routines.Checks.Map.MapValid()
            and GLOBAL_CACHE.Map.GetMapID() == (
                target_map_id if target_map_id else GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)
            )
        )

        yield from self._coro_until_condition(wait_condition, duration=3000)
        yield from self._coro_for_time(1000)  # ensure all map actions finish
        
        
    #region Yield Steps (ys_)
    @_yield_step(label="WasteTime", counter_key="WASTE_TIME")
    def _ys_for_time(self, duration: int = 100):
        yield from self._coro_for_time(duration)
        
    @_yield_step(label="WaitForMapLoad", counter_key="WAIT_FOR_MAP_LOAD")
    def ys_for_map_load(self, target_map_id, target_map_name=""):
        yield from self._coro_for_map_load(target_map_id, target_map_name=target_map_name)

    @_yield_step(label="WasteTimeUntilConditionMet", counter_key="WASTE_TIME")
    def ys_until_condition(self, condition: Callable[[], bool], duration: int=1000):
        yield from self._coro_until_condition(condition, duration)
        
    @_yield_step(label="WasteTimeUntilOutOfCombat", counter_key="WASTE_TIME_UNTIL_OUT_OF_COMBAT")
    def ys_until_out_of_combat(self, range: Range = Range.Earshot):
        yield from self._coro_until_out_of_combat(range)
        
    @_yield_step(label="WasteTimeUntilOnCombat", counter_key="WASTE_TIME_UNTIL_ON_COMBAT")
    def ys_until_on_combat(self, range: Range = Range.Earshot):
        yield from self._coro_until_on_combat(range)

    @_yield_step(label="WasteTimeUntilOnOutpost", counter_key="WASTE_TIME_UNTIL_ON_OUTPOST")
    def ys_until_on_outpost(self):
        yield from self._coro_until_on_outpost()
        
    @_yield_step(label="WasteTimeUntilOnExplorable", counter_key="WASTE_TIME_UNTIL_ON_EXPLORABLE")
    def ys_until_on_explorable(self):
        yield from self._coro_until_on_explorable()
        
    @_yield_step(label="WasteTimeUntilModelHasQuest", counter_key="WASTE_TIME_UNTIL_MODEL_HAS_QUEST")
    def ys_until_model_has_quest(self, model_id: int):
        yield from self._coro_until_model_has_quest(model_id)
        
    @_yield_step(label="WaitForMapToChange", counter_key="WAIT_FOR_MAP_TO_CHANGE")
    def ys_for_map_to_change(self, target_map_id: int = 0, target_map_name: str = ""):
        yield from self._coro_for_map_to_change(target_map_id, target_map_name=target_map_name)
        
    #region public helpers
    def ForTime(self, duration: int= 100) -> None:
        self._ys_for_time(duration)

    def UntilCondition(self, condition: Callable[[], bool], duration: int=1000) -> None:
        self.ys_until_condition(condition, duration)
        
    def UntilOutOfCombat(self, range: Range = Range.Earshot) -> None:
        self.ys_until_out_of_combat(range)

    def UntilOnCombat(self, range: Range = Range.Earshot) -> None:
        self.ys_until_on_combat(range)
        
    def UntilOnOutpost(self) -> None:
        self.ys_until_on_outpost()
        
    def UntilModelHasQuest(self, model_id: int) -> None:
        self.ys_until_model_has_quest(model_id)
          
    def UntilOnExplorable(self) -> None:
        self.ys_until_on_explorable()

    def ForMapLoad(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        self.ys_for_map_load(target_map_id, target_map_name=target_map_name)

    def ForMapToChange(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        self.ys_for_map_to_change(target_map_id, target_map_name=target_map_name)
