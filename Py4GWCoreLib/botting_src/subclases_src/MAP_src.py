#region STATES
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

from ...enums import ModelID

#region MAP
class _MAP:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers

    def Travel(self, target_map_id: int = 0, target_map_name: str = "") -> None:
        from ...GlobalCache import GLOBAL_CACHE
        if target_map_name:
            target_map_id = GLOBAL_CACHE.Map.GetMapIDByName(target_map_name)

        current_map_id = GLOBAL_CACHE.Map.GetMapID()
        if (current_map_id == target_map_id):
            return

        self._helpers.Map.travel(target_map_id)
        self._helpers.Wait.for_time(1000)
        self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)

    def EnterChallenge(self, delay:int= 4500, target_map_id: int = 0, target_map_name: str = "") -> None:
        self._helpers.Map.enter_challenge(wait_for=delay)
        self.parent.Wait.ForMapLoad(target_map_id=target_map_id, target_map_name=target_map_name)

    def TravelGH(self, wait_time:int=4000):
        self._helpers.Map.travel_to_gh(wait_time=wait_time)
        self.parent.Wait.UntilOnOutpost()

    def LeaveGH(self, wait_time:int=4000):
        self._helpers.Map.leave_gh(wait_time=wait_time)
        self.parent.Wait.UntilOnOutpost()
