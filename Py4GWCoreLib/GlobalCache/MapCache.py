
from ..Map import Map
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
from Py4GWCoreLib.enums import outposts, explorables

class MapCache:
    def __init__(self, action_queue_manager: ActionQueueManager):
        self._name = ""
        self._action_queue_manager = action_queue_manager
        
    def _update_cache(self):
        pass
        
