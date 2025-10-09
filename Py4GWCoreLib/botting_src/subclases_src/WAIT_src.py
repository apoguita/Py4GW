#region STATES
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass
    
#region WAIT
class _WAIT:
    from ...enums import Range
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers

    def ForTime(self, duration: int= 100) -> None:
        self._helpers.Wait.for_time(duration)

    def UntilCondition(self, condition: Callable[[], bool], duration: int=1000) -> None:
        self._helpers.Wait.until_condition(condition, duration)
        

    def UntilOutOfCombat(self, range: Range = Range.Earshot) -> None:
        from ...Routines import Routines
        wait_condition = lambda: not(Routines.Checks.Agents.InDanger(aggro_area=range))
        self._helpers.Wait.until_condition(wait_condition)

    def UntilOnCombat(self, range: Range = Range.Earshot) -> None:
        from ...Routines import Routines
        wait_condition = lambda: (Routines.Checks.Agents.InDanger(aggro_area=range))
        self._helpers.Wait.until_condition(wait_condition)
        
    def UntilOnOutpost(self) -> None:
        from ...Routines import Routines
        wait_condition = lambda: Routines.Checks.Map.MapValid() and  Routines.Checks.Map.IsOutpost()
        self._helpers.Wait.until_condition(wait_condition)
        
    def UntilModelHasQuest(self, model_id: int) -> None:
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        from ...enums import Range
        wait_function = lambda: (
            not (Routines.Checks.Agents.InDanger(aggro_area=Range.Spirit)) and
            GLOBAL_CACHE.Agent.HasQuest(Routines.Agents.GetAgentIDByModelID(model_id))
        )
        self._helpers.Wait.until_condition(wait_function, duration=1000)
        
        
        
    def UntilOnExplorable(self) -> None:
        from ...Routines import Routines
        wait_condition = lambda: Routines.Checks.Map.MapValid() and  Routines.Checks.Map.IsExplorable()
        self._helpers.Wait.until_condition(wait_condition)

    def ForMapLoad(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        from Py4GWCoreLib import GLOBAL_CACHE
        if target_map_name:
            target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)

        self._helpers.Wait.for_map_load(target_map_id)

    def ForMapToChange(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        """Waits until all action finishes in current map and game sends you to a new one"""
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        if target_map_name:
            target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)

        wait_condition = lambda: (
            Routines.Checks.Map.MapValid() and
            GLOBAL_CACHE.Map.GetMapID() == target_map_id
        )

        self.UntilCondition(wait_condition, duration=3000)
        self.ForTime(1000)  # ensure all map actions finish