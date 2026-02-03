from dataclasses import dataclass
import time
from typing import Any
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType

@dataclass
class EventMessage:
    """Data structure for event messages with type and data fields."""
    type: EventType
    current_state: BehaviorState
    data: Any
    timestamp: float| None = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()