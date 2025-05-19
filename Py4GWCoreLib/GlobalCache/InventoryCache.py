import PyInventory
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager

class InventoryCache:
    def __init__(self, action_queue_manager):
        self._inventory_instance = PyInventory.PyInventory()
        self._action_queue_manager:ActionQueueManager = action_queue_manager

