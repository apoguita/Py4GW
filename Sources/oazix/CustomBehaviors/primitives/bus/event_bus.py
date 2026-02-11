from typing import Any, Callable, Dict, List, Optional, Union, Generator
from collections.abc import Generator as AbcGenerator
from collections import defaultdict
import threading
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives import constants


class EventBus:
    """
    Event bus system for communication between classes.
    Allows classes to subscribe to event types and publish messages.
    Uses EventType enum for type safety.
    """
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[EventMessage], Generator[Any, Any, Any]]]] = defaultdict(list)
        self._subscriber_names: Dict[EventType, List[str]] = defaultdict(list)
        self._lock = threading.RLock()
        self._message_history: List[EventMessage] = []
        self._max_history_size = 1000
        self._debug_mode = False
    
    def subscribe(self, event_type: EventType, callback:Callable[[EventMessage], Generator[Any, Any, Any]], subscriber_name: str = "Unknown") -> bool:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The EventType enum to subscribe to
            callback: Function to call when event is published
            subscriber_name: Name of the subscriber for debugging
        
        Returns:
            True if subscription was successful, False otherwise
        
        Raises:
            ValueError: If subscriber_name is already registered for this event_type
        """
        if not isinstance(event_type, EventType) or not callback:
            print(f"Invalid subscription parameters: event_type={event_type}, callback={callback}")
            return False
        
        with self._lock:
            # Check if subscriber_name already exists for this event type
            if subscriber_name in self._subscriber_names[event_type]:
                raise ValueError(f"Subscriber '{subscriber_name}' is already registered for event type '{event_type.name}'")
            
            # Add new subscription
            self._subscribers[event_type].append(callback)
            self._subscriber_names[event_type].append(subscriber_name)

            if self._debug_mode:
                print(f"Subscribed '{subscriber_name}' to event type '{event_type.name}'")
            return True
    
    def publish(self, event_type: EventType, current_state: BehaviorState, data: Any = None, publisher_name: str = "Unknown") -> Generator[Any, Any, bool]:
        """
        Publish an event message.
        
        Args:
            event_type: The EventType enum to publish
            data: The data to include with the event
            publisher_name: Name of the publisher for debugging
            
        Returns:
            True if publishing was successful, False otherwise
        """
        if not isinstance(event_type, EventType):
            print(f"Invalid event type from publisher '{publisher_name}': {event_type}")
            return False

        message = EventMessage(type=event_type, current_state=current_state, data=data)

        with self._lock:
            # Add to history
            self._message_history.append(message)
            if len(self._message_history) > self._max_history_size:
                self._message_history.pop(0)
            
            # Get current subscribers for this event type
            subscribers = self._subscribers[event_type].copy()
            subscriber_names = self._subscriber_names[event_type].copy()
        
        if self._debug_mode:
            print(f"Publishing event '{event_type.name}' from '{publisher_name}' with {len(subscribers)} subscribers")
        
        # Notify subscribers (outside of lock to prevent deadlocks)
        success_count = 0
        for i, callback in enumerate(subscribers):
            try:
                gen = callback(message)
                # Validate generator contract explicitly for clearer errors
                if not isinstance(gen, AbcGenerator):
                    subscriber_name = subscriber_names[i] if i < len(subscriber_names) else "Unknown"
                    cb_name = getattr(callback, "__qualname__", repr(callback))
                    cb_mod = getattr(callback, "__module__", "<unknown>")
                    raise TypeError(
                        f"Subscriber '{subscriber_name}' for event '{event_type.name}' must return a generator; "
                        f"got {type(gen).__name__} from {cb_mod}.{cb_name}"
                    )
                # Iterate and propagate errors
                yield from gen  # type: ignore[misc]
                success_count += 1
            except Exception as e:
                subscriber_name = subscriber_names[i] if i < len(subscriber_names) else "Unknown"
                cb_name = getattr(callback, "__qualname__", repr(callback))
                cb_mod = getattr(callback, "__module__", "<unknown>")
                print(
                    f"Error in subscriber '{subscriber_name}' for event '{event_type.name}': "
                    f"{type(e).__name__}: {e} | callback={cb_mod}.{cb_name}"
                )
                # Re-raise the original exception to preserve type and traceback
                raise
        
        if self._debug_mode and subscribers:
            print(f"Event '{event_type.name}' delivered to {success_count}/{len(subscribers)} subscribers")
        
        return True
    
    def get_subscriber_count(self, event_type: EventType) -> int:
        """Get the number of subscribers for a specific event type."""
        if not isinstance(event_type, EventType):
            return 0
        with self._lock:
            return len(self._subscribers.get(event_type, []))
    
    def get_all_event_types(self) -> List[EventType]:
        """Get a list of all event types that have subscribers."""
        with self._lock:
            return list(self._subscribers.keys())
    
    def get_subscribers_for_event(self, event_type: EventType) -> List[str]:
        """Get a list of subscriber names for a specific event type."""
        if not isinstance(event_type, EventType):
            return []
        with self._lock:
            return self._subscriber_names.get(event_type, []).copy()

    def unsubscribe_all(self, subscriber_name: str) -> int:
        """
        Unsubscribe a subscriber from all event types.

        Args:
            subscriber_name: The name of the subscriber to remove

        Returns:
            The number of subscriptions removed
        """
        removed_count = 0
        with self._lock:
            for event_type in list(self._subscriber_names.keys()):
                if subscriber_name in self._subscriber_names[event_type]:
                    idx = self._subscriber_names[event_type].index(subscriber_name)
                    self._subscriber_names[event_type].pop(idx)
                    self._subscribers[event_type].pop(idx)
                    removed_count += 1
                    if self._debug_mode:
                        print(f"Unsubscribed '{subscriber_name}' from event type '{event_type.name}'")

        if self._debug_mode and removed_count > 0:
            print(f"Total unsubscriptions for '{subscriber_name}': {removed_count}")

        return removed_count

    def clear_subscribers(self, event_type: Optional[EventType] = None):
        """
        Clear all subscribers for a specific event type or all events.
        
        Args:
            event_type: If provided, clear only this event type. If None, clear all.
        """
        with self._lock:
            if event_type is None:
                self._subscribers.clear()
                self._subscriber_names.clear()
                if self._debug_mode:
                    print(f"Cleared all event subscribers")
            else:
                if not isinstance(event_type, EventType):
                    print(f"Invalid event type: {event_type}")
                    return
                if event_type in self._subscribers:
                    del self._subscribers[event_type]
                    del self._subscriber_names[event_type]
                    if self._debug_mode:
                        print(f"Cleared subscribers for event type '{event_type.name}'")
    
    def get_message_history(self, event_type: Optional[EventType] = None, limit: Optional[int] = None) -> List[EventMessage]:
        """
        Get message history, optionally filtered by event type.
        
        Args:
            event_type: If provided, return only messages of this type
            limit: If provided, limit the number of messages returned
            
        Returns:
            List of EventMessage objects
        """
        with self._lock:
            if event_type is None:
                history = self._message_history.copy()
            else:
                if not isinstance(event_type, EventType):
                    print(f"Invalid event type: {event_type}")
                    return []
                history = [msg for msg in self._message_history if msg.type == event_type]
            
            if limit is not None:
                history = history[-limit:]
            
            return history
    
    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug logging."""
        self._debug_mode = enabled
        if constants.DEBUG:
            print(f"Debug mode {'enabled' if enabled else 'disabled'}")
    
    def set_max_history_size(self, size: int):
        """Set the maximum number of messages to keep in history."""
        if size < 0:
            if constants.DEBUG:
                print(f"Invalid history size: {size}")
            return
        
        with self._lock:
            self._max_history_size = size
            # Trim history if needed
            while len(self._message_history) > self._max_history_size:
                self._message_history.pop(0)
        
        if constants.DEBUG:
            print(f"Max history size set to {size}")