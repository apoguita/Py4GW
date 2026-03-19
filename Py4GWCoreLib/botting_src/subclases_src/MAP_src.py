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
    def _normalize_region_pool(self, region_pool: str) -> str:
        mode = (region_pool or "eu").strip().lower()
        mode = mode.replace("+", "_").replace("-", "_").replace(" ", "_")
        aliases = {
            "euasia": "eu_asia",
            "eu_asia": "eu_asia",
            "asia_only": "asia",
            "eu_only": "eu",
        }
        mode = aliases.get(mode, mode)
        if mode not in ("eu", "eu_asia", "asia"):
            return "eu"
        return mode

    def _get_random_district_candidates(self, region_pool: str) -> list[int]:
        from ...enums_src.Region_enums import District

        eu = [
            District.EuropeItalian.value,
            District.EuropeSpanish.value,
            District.EuropePolish.value,
            District.EuropeRussian.value,
        ]
        asia = [
            District.AsiaKorean.value,
            District.AsiaChinese.value,
            District.AsiaJapanese.value,
        ]

        mode = self._normalize_region_pool(region_pool)
        if mode == "asia":
            return asia
        if mode == "eu_asia":
            return eu + asia
        return eu

    def _coro_travel(self, target_map_id:int =0, target_map_name:str ="") -> Generator:
        from ...Routines import Routines
        
        if not Map.IsMapReady():
            yield from Routines.Yield.wait(1000)
            return
        
        if target_map_name:
            target_map_id = Map.GetMapIDByName(target_map_name)
        
        current_map_id = Map.GetMapID()

        # Check if we're already in the target map (or a variant of it)
        if Map.IsMapIDMatch(current_map_id, target_map_id):
            yield from Routines.Yield.wait(1000)
            return
        
        Map.Travel(target_map_id)
        yield from Routines.Yield.wait(500)
        
        yield from self.parent.Wait._coro_for_map_load(target_map_id=target_map_id, target_map_name=target_map_name)

    def _coro_travel_random_district(
        self,
        target_map_id: int = 0,
        target_map_name: str = "",
        region_pool: str = "eu",
    ) -> Generator:
        import random
        from ...Routines import Routines

        if not Map.IsMapReady():
            yield from Routines.Yield.wait(1000)
            return

        if target_map_name:
            target_map_id = Map.GetMapIDByName(target_map_name)

        if target_map_id <= 0:
            yield from Routines.Yield.wait(500)
            return

        current_map_id = Map.GetMapID()
        if Map.IsMapIDMatch(current_map_id, target_map_id):
            yield from Routines.Yield.wait(500)
            return

        allowed_districts = self._get_random_district_candidates(region_pool)
        district = random.choice(allowed_districts)

        Map.TravelToDistrict(target_map_id, district)
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

    @_yield_step(label="TravelRandomDistrict", counter_key="TRAVEL")
    def ys_travel_random_district(
        self,
        target_map_id: int = 0,
        target_map_name: str = "",
        region_pool: str = "eu",
    ) -> Generator:
        yield from self._coro_travel_random_district(target_map_id, target_map_name, region_pool)
    
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

    def Travel_To_Random_District(
        self,
        target_map_id: int = 0,
        target_map_name: str = "",
        region_pool: str = "eu",
    ) -> None:
        """Travel to an outpost using a random allowed district.
        region_pool: 'eu', 'eu_asia', or 'asia'
        """
        self.ys_travel_random_district(target_map_id, target_map_name, region_pool)

    def TravelGH(self, wait_time:int=4000):
        self.ys_travel_gh(wait_time=wait_time)

    def LeaveGH(self, wait_time:int=4000):
        self.ys_leave_gh(wait_time=wait_time)

    def EnterChallenge(self, delay:int= 4500, target_map_id: int = 0, target_map_name: str = "") -> None:
        self.ys_enter_challenge(wait_for=delay, target_map_id=target_map_id, target_map_name=target_map_name)

    def IsMapUnlocked(self, map_id: int) -> bool:
        """Returns True if the given map ID is unlocked for the current character."""
        return Map.IsMapUnlocked(map_id)
