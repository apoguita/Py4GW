
from ..Py4GWcorelib import Timer
arrived_timer = Timer()

class Transition:
    
    @staticmethod
    def TravelToOutpost(outpost_id, log_actions=True):
        """
        Purpose: Travel to the specified outpost by ID.
        Args:
            outpost_id (int): The ID of the outpost to travel to.
            log_actions (bool) Optional: Whether to log the action. Default is True.
        Returns: None
        """
        from ..GlobalCache import GLOBAL_CACHE
        from ..Py4GWcorelib import ConsoleLog

        global arrived_timer

        if not GLOBAL_CACHE.Map.IsMapReady():
            return

        if GLOBAL_CACHE.Map.GetMapID() == outpost_id:
            if log_actions and arrived_timer.IsStopped():
                ConsoleLog("TravelToOutpost", f"Already at outpost: {GLOBAL_CACHE.Map.GetMapName(outpost_id)}.")
            return

        if arrived_timer.IsStopped():
            GLOBAL_CACHE.Map.Travel(outpost_id)
            arrived_timer.Start()
            if log_actions:
                ConsoleLog("TravelToOutpost", f"Traveling to outpost: {GLOBAL_CACHE.Map.GetMapName(outpost_id)}.")

    @staticmethod
    def HasArrivedToOutpost(outpost_id, log_actions=True):
        """
        Purpose: Check if the player has arrived at the specified outpost after traveling.
        Args:
            outpost_id (int): The ID of the outpost to check.
            log_actions (bool) Optional: Whether to log the action. Default is True.
        Returns: bool
        """
        from ..GlobalCache import GLOBAL_CACHE
        from ..Py4GWcorelib import ConsoleLog
        global arrived_timer

        has_arrived = GLOBAL_CACHE.Map.GetMapID() == outpost_id and Transition.IsOutpostLoaded()

        if has_arrived:
            arrived_timer.Stop()
            if log_actions:
                ConsoleLog("HasArrivedToOutpost", f"Arrived at outpost: {GLOBAL_CACHE.Map.GetMapName(outpost_id)}.")
            return True

        if arrived_timer.HasElapsed(5000):
            arrived_timer.Stop()
            if log_actions:
                ConsoleLog("HasArrivedToOutpost", f"Timeout reaching outpost: {GLOBAL_CACHE.Map.GetMapName(outpost_id)}.")
            return False

        if log_actions:
            ConsoleLog("HasArrivedToOutpost", f"Still traveling... Waiting to arrive at: {GLOBAL_CACHE.Map.GetMapName(outpost_id)}.")

        return False

    @staticmethod
    def IsOutpostLoaded(log_actions=True):
        """
        Purpose: Check if the outpost map is loaded.
        Args:
            log_actions (bool) Optional: Whether to log the action. Default is True.
        Returns: bool
        """
        from ..GlobalCache import GLOBAL_CACHE
        from ..Py4GWcorelib import ConsoleLog
        map_loaded = GLOBAL_CACHE.Map.IsMapReady() and GLOBAL_CACHE.Map.IsOutpost() and GLOBAL_CACHE.Party.IsPartyLoaded()

        if log_actions:
            if map_loaded:
                ConsoleLog("IsOutpostLoaded", "Outpost Map Loaded.")
            else:
                ConsoleLog("IsOutpostLoaded", "Outpost Map Not Loaded. Retrying.")

        return map_loaded

    @staticmethod
    def IsExplorableLoaded(log_actions=True):
        """
        Purpose: Check if the explorable map is loaded.
        Args:
            log_actions (bool) Optional: Whether to log the action. Default is True.
        Returns: bool
        """
        from ..GlobalCache import GLOBAL_CACHE
        from ..Py4GWcorelib import ConsoleLog
        map_loaded = GLOBAL_CACHE.Map.IsMapReady() and GLOBAL_CACHE.Map.IsExplorable() and GLOBAL_CACHE.Party.IsPartyLoaded()
        
        if log_actions:
            if map_loaded:
                ConsoleLog("IsExplorableLoaded", f"Explorable Map Loaded.")
            else:
                ConsoleLog("IsExplorableLoaded", f"Explorable Map Not Loaded. Retrying.")

        return map_loaded