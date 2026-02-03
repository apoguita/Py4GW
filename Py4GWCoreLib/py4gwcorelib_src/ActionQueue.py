#region ActionQueue
from collections import namedtuple, deque
from datetime import datetime
from .Timer import Timer
from enum import Enum

class ActionQueue:
    def __init__(self):
        """Initialize the action queue."""
        self.queue = deque() # Use deque for efficient FIFO operations
        self.history = deque(maxlen=100)  # Store recent action history with a cap
        self._step_ids = deque()          # Step ID queue (internal use)
        self._step_counter = 0            # Unique step ID tracker
        self._last_step_id = None         # Last executed step ID


    def add_action(self, action, *args, **kwargs):
        """
        Add an action to the queue.

        :param action: Function to execute.
        :param args: Positional arguments for the function.
        :param kwargs: Keyword arguments for the function.
        """
        self.queue.append((action, args, kwargs))
        self._step_ids.append(self._step_counter)  # Track step ID
        self._step_counter += 1
        
    def execute_next(self):
        if self.queue:
            action, args, kwargs = self.queue.popleft()
            self._last_step_id = self._step_ids.popleft()  # Extract step ID
            action(*args, **kwargs)
            self.history.append((datetime.now(), action, args, kwargs))
            return True
        return False

    def get_last_step_id(self):
        """Return the step ID of the last executed action"""
        return self._last_step_id

    def get_next_step_id(self):
        """Peek the step ID of the next action (non-invasive)"""
        return self._step_ids[0] if self._step_ids else None
            
    def is_empty(self):
        """Check if the action queue is empty."""
        return not bool(self.queue)
    
    def clear(self):
        """Clear all actions from the queue."""
        self.queue.clear()
        self._step_ids.clear()
        
    def clear_history(self):
        """Clear the action history."""
        self.history.clear()
        
    def get_next_action_name(self):
        """
        Get the name of the next action function in the queue, or None if empty.
        :return: String with function name or None.
        """
        if self.queue:
            action, args, kwargs = self.queue[0]
            parts = [action.__name__]
            parts.extend(str(arg) for arg in args)
            parts.extend(f"{k}={v}" for k, v in kwargs.items())
            return ','.join(parts)
        return None
    
    def get_all_action_names(self):
        """
        Get a list of all action names with arguments concatenated.
        :return: List of concatenated action strings.
        """
        action_strings = []
        for action, args, kwargs in self.queue:
            parts = [action.__name__]
            parts.extend(str(arg) for arg in args)
            parts.extend(f"{k}={v}" for k, v in kwargs.items())
            action_strings.append(','.join(parts))
        return action_strings
    
    def get_history(self):
        """
        Return the raw history queue: list of (datetime, function, args, kwargs).
        """
        return list(self.history)

    def get_history_names(self):
        formatted = []
        for i, entry in enumerate(self.history):
            if not isinstance(entry, tuple) or len(entry) != 4:
                formatted.append(f"[INVALID ENTRY #{i}]: {repr(entry)}")
                continue
            ts, func, args, kwargs = entry
            try:
                parts = [f"{ts.strftime('%H:%M:%S')} - {func.__name__}"]
                parts.extend(str(arg) for arg in args)
                parts.extend(f"{k}={v}" for k, v in kwargs.items())
                formatted.append(', '.join(parts))
            except Exception as e:
                formatted.append(f"[ERROR formatting entry #{i}]: {e}")
        return formatted


#region ActionQueueNode
class ActionQueueNode:
    def __init__(self,throttle_time=250):
        self.action_queue = ActionQueue()
        self.action_queue_timer = Timer()
        self.action_queue_timer.Start()
        self.action_queue_time = throttle_time
        self._aftercast_delays = deque()
        

    def execute_next(self):
        delay = self._aftercast_delays[0] if self._aftercast_delays else 0
        if self.action_queue_timer.HasElapsed(self.action_queue_time + delay):      
            result = self.action_queue.execute_next()
            self.action_queue_timer.Reset()
            if self._aftercast_delays:
                self._aftercast_delays.popleft()
            return result
        return False
    
    def AftercastDelay(self):
        """Dummy action used to enforce a delay step in the queue."""
        pass
                
    def add_action(self, action, *args, **kwargs):
        self.action_queue.add_action(action, *args, **kwargs)
        self._aftercast_delays.append(0)
        
    def add_action_with_delay(self, delay, action, *args, **kwargs):
        self.action_queue.add_action(action, *args, **kwargs)
        self._aftercast_delays.append(0)  # Real action runs immediately

        self.action_queue.add_action(self.AftercastDelay)
        self._aftercast_delays.append(delay)  # Delay applies to this no-op step
        
    def is_empty(self):
        return self.action_queue.is_empty()
    
    def clear(self):
        self.action_queue.clear()
        self._aftercast_delays.clear()
        
    def clear_history(self):
        self.action_queue.clear_history()
        
    def IsExpired(self):
        delay = self._aftercast_delays[0] if self._aftercast_delays else 0
        return self.action_queue_timer.HasElapsed(self.action_queue_time + delay)
    
    def ProcessQueue(self):
        if self.IsExpired():
            return self.execute_next()
        return False
    
    def GetNextActionName(self):
        return self.action_queue.get_next_action_name()
    
    def GetAllActionNames(self):
        return self.action_queue.get_all_action_names()
    
    def GetHistory(self):
        return self.action_queue.get_history()
    
    def GetHistoryNames(self):
        return self.action_queue.get_history_names()

#region QueueTypes
class QueueTypes(Enum):
    Action = "ACTION"
    Loot = "LOOT"
    Merchant = "MERCHANT"
    Salvage = "SALVAGE"
    Identify = "IDENTIFY"

    @classmethod
    def list(cls):
        return [member.value for member in cls]

#region ActionQueueManager
class ActionQueueManager:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ActionQueueManager, cls).__new__(cls)
            cls._instance._initialize_queues()
        return cls._instance

    def _initialize_queues(self):
        self.queues = {
            "ACTION": ActionQueueNode(50),
            "LOOT": ActionQueueNode(1250),
            "MERCHANT": ActionQueueNode(750),
            "SALVAGE": ActionQueueNode(125),
            "IDENTIFY": ActionQueueNode(150),
            "FAST": ActionQueueNode(20),
            "TRANSITION": ActionQueueNode(50),
            # Add more queues here if needed
        }
        
    def AddAction(self, queue_name, action, *args, **kwargs):
        """Add an action to a specific queue by name."""
        if queue_name in self.queues:
            self.queues[queue_name].add_action(action, *args, **kwargs)
        else:
            raise ValueError(f"Queue '{queue_name}' does not exist.")
        
    def AddActionWithDelay(self, queue_name, delay, action, *args, **kwargs):
        """Add an action with a delay to a specific queue by name."""
        if queue_name in self.queues:
            self.queues[queue_name].add_action_with_delay(delay, action, *args, **kwargs)
        else:
            raise ValueError(f"Queue '{queue_name}' does not exist.")

    # Reset specific queue
    def ResetQueue(self, queue_name):
        if queue_name in self.queues:
            self.queues[queue_name].clear()

    # Reset all queues
    def ResetNonTransitionQueues(self):
        for queue_name, queue in self.queues.items():
            if queue_name != "TRANSITION":
                queue.clear()

    # Reset all queues
    def ResetAllQueues(self):
        for queue in self.queues.values():
            queue.clear()

    # Process specific queue
    def ProcessQueue(self, queue_name):
        if queue_name in self.queues:
            return self.queues[queue_name].ProcessQueue()
        return False

    # Process all queues
    def ProcessAll(self):
        for queue in self.queues.values():
            queue.ProcessQueue()

    # Getters (optional if you prefer direct dict access)
    def GetQueue(self, queue_name) -> ActionQueueNode:
        queue = self.queues.get(queue_name)
        if queue is None:
            raise ValueError(f"Queue '{queue_name}' does not exist.")
        return queue
    
    def IsEmpty(self, queue_name) -> bool:
        queue = self.GetQueue(queue_name)
        return queue.is_empty()
    
    def GetNextActionName(self, queue_name) -> str:
        queue = self.GetQueue(queue_name)
        return queue.GetNextActionName() or ""
    
    def GetAllActionNames(self, queue_name) -> list:
        queue = self.GetQueue(queue_name)
        return queue.GetAllActionNames()
    
    def GetHistory(self, queue_name) -> list:
        queue = self.GetQueue(queue_name)
        return queue.GetHistory()
    
    def GetHistoryNames(self, queue_name) -> list:
        queue = self.GetQueue(queue_name)
        return queue.GetHistoryNames()

    def ClearHistory(self, queue_name) -> None:
        queue = self.GetQueue(queue_name)
        queue.clear_history()

           
            
#endregion