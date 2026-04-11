from __future__ import annotations

from ..BehaviourTrees import BT
from .helpers import _run_bt_tree


class Map:
    @staticmethod
    def SetHardMode(hard_mode=True, log=False):
        """
        Purpose: Set the map to hard mode.
        Args: None
        Returns: None
        """
        tree = BT.Map.SetHardMode(hard_mode, log)
        yield from _run_bt_tree(tree, return_bool=False, throttle_ms=100)
            
    @staticmethod
    def TravelToOutpost(outpost_id, log=False, timeout:int=10000):
        """
        Purpose: Positions yourself safely on the outpost.
        Args:
            outpost_id (int): The ID of the outpost to travel to.
            log (bool) Optional: Whether to log the action. Default is False.
        Returns: None
        """
        
        tree = BT.Map.TravelToOutpost(outpost_id, log, timeout)
        result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=100)
        return result


    @staticmethod
    def TravelToRegion(outpost_id, region, district, language=0, log=False):
        """
        Purpose: Positions yourself safely on the outpost.
        Args:
            outpost_id (int): The ID of the outpost to travel to.
            region (int): The region ID to travel to.
            district (int): The district ID to travel to.
            language (int): The language ID to travel to. Default is 0.
            log (bool) Optional: Whether to log the action. Default is True.
        Returns: None
        """
        
        tree = BT.Map.TravelToRegion(outpost_id, region, district, language, log)
        result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=100)
        return result


    @staticmethod
    def WaitforMapLoad(map_id, log=False, timeout: int = 10000, map_name: str =""):
        """
        Purpose: Wait for the map to load completely.
        Args:
            map_id (int): The ID of the map to wait for.
            log (bool) Optional: Whether to log the action. Default is False.
            timeout (int) Optional: Timeout in milliseconds. Default is 10000.
            map_name (str) Optional: The name of the map to wait for. Default is "".
        Returns: bool: True if the map loaded successfully, False if timed out.
        """
        
        tree = BT.Map.WaitforMapLoad(map_id, log, timeout, map_name)
        result = yield from _run_bt_tree(tree, return_bool=True, throttle_ms=500)
        return result
