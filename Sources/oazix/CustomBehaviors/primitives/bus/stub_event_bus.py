from typing import Any, Callable, Generator, List, Optional

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType

class StubEventBus(EventBus):
    """
    Stub EventBus for mocking purposes. Implements the same interface as EventBus but does nothing.
    Useful for testing when you don't want actual event bus behavior.
    """
    def __init__(self):
        # Don't call super().__init__() to avoid initializing locks, dictionaries, etc.
        # Just stub everything out
        pass

    def subscribe(self, event_type: EventType, callback: Callable[[EventMessage], Generator[Any, Any, Any]], subscriber_name: str = "Unknown") -> bool:
        """Stub subscribe - does nothing, always returns True."""
        return True

    def publish(self, event_type: EventType, current_state: BehaviorState, data: Any = None, publisher_name: str = "Unknown") -> Generator[Any, Any, bool]:
        """Stub publish - does nothing, yields nothing, returns True."""
        yield
        return True

    def get_subscriber_count(self, event_type: EventType) -> int:
        """Stub get_subscriber_count - always returns 0."""
        return 0

    def get_all_event_types(self) -> List[EventType]:
        """Stub get_all_event_types - always returns empty list."""
        return []

    def get_subscribers_for_event(self, event_type: EventType) -> List[str]:
        """Stub get_subscribers_for_event - always returns empty list."""
        return []

    def unsubscribe_all(self, subscriber_name: str) -> int:
        """Stub unsubscribe_all - does nothing, always returns 0."""
        return 0

    def clear_subscribers(self, event_type: Optional[EventType] = None):
        """Stub clear_subscribers - does nothing."""
        pass

    def get_message_history(self, event_type: Optional[EventType] = None, limit: Optional[int] = None) -> List[EventMessage]:
        """Stub get_message_history - always returns empty list."""
        return []

    def set_debug_mode(self, enabled: bool):
        """Stub set_debug_mode - does nothing."""
        pass

    def set_max_history_size(self, size: int):
        """Stub set_max_history_size - does nothing."""
        pass

