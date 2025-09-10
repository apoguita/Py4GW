from typing import Any, Callable, Dict, List, Optional, Union
from collections import defaultdict
import threading
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives import constants


class EventBus:
    """
    Event bus system for communication between classes.
    Allows classes to subscribe to event types and publish messages.
    Uses EventType enum for type safety.
    """
    
    _instance = None  # Singleton instance
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._subscribers: Dict[EventType, List[Callable[[EventMessage], None]]] = defaultdict(list)
            self._subscriber_names: Dict[EventType, List[str]] = defaultdict(list)
            self._lock = threading.RLock()
            self._message_history: List[EventMessage] = []
            self._max_history_size = 1000
            self._debug_mode = False
    
    def subscribe(self, event_type: EventType, callback: Callable[[EventMessage], None], subscriber_name: str = "Unknown") -> bool:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The EventType enum to subscribe to
            callback: Function to call when event is published
            subscriber_name: Name of the subscriber for debugging
            
        Returns:
            True if subscription was successful, False otherwise
        """
        if not isinstance(event_type, EventType) or not callback:
            if constants.DEBUG:
                print(f"Invalid subscription parameters: event_type={event_type}, callback={callback}")
            return False
        
        with self._lock:
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)
                self._subscriber_names[event_type].append(subscriber_name)
                if self._debug_mode:
                    print(f"Subscribed '{subscriber_name}' to event type '{event_type.name}'")
                return True
            else:
                if self._debug_mode:
                    print(f"Subscriber '{subscriber_name}' already subscribed to '{event_type.name}'")
                return False
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[EventMessage], None], subscriber_name: str = "Unknown") -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: The EventType enum to unsubscribe from
            callback: Function to remove from subscribers
            subscriber_name: Name of the subscriber for debugging
            
        Returns:
            True if unsubscription was successful, False otherwise
        """
        if not isinstance(event_type, EventType):
            if constants.DEBUG:
                print(f"Invalid event type: {event_type}")
            return False
        
        with self._lock:
            if event_type in self._subscribers:
                try:
                    index = self._subscribers[event_type].index(callback)
                    self._subscribers[event_type].pop(index)
                    self._subscriber_names[event_type].pop(index)
                    
                    # Clean up empty event types
                    if not self._subscribers[event_type]:
                        del self._subscribers[event_type]
                        del self._subscriber_names[event_type]
                    
                    if self._debug_mode:
                        print(f"Unsubscribed '{subscriber_name}' from event type '{event_type.name}'")
                    return True
                except ValueError:
                    if self._debug_mode:
                        print(f"Subscriber '{subscriber_name}' not found for event type '{event_type.name}'")
                    return False
            return False
    
    def publish(self, event_type: EventType, data: Any = None, publisher_name: str = "Unknown") -> bool:
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
            if constants.DEBUG:
                print(f"Invalid event type from publisher '{publisher_name}': {event_type}")
            return False
        
        message = EventMessage(type=event_type, data=data)
        
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
                callback(message)
                success_count += 1
            except Exception as e:
                subscriber_name = subscriber_names[i] if i < len(subscriber_names) else "Unknown"
                if constants.DEBUG:
                    print(f"Error in subscriber '{subscriber_name}' for event '{event_type.name}': {e}")
        
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
                    if constants.DEBUG:
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
                    if constants.DEBUG:
                        print(f"Invalid event type: {event_type}")
                    return []
                history = [msg for msg in self._message_history if msg.type == event_type]
            
            if limit is not None:
                history = history[-limit:]
            
            return history
    
    def get_messages_by_category(self, category: str, limit: Optional[int] = None) -> List[EventMessage]:
        """
        Get messages by category prefix.
        
        Args:
            category: Category prefix (e.g., 'PLAYER', 'COMBAT', 'LOOT')
            limit: If provided, limit the number of messages returned
            
        Returns:
            List of EventMessage objects
        """
        category_events = EventType.get_event_types_by_category(category)
        with self._lock:
            history = [msg for msg in self._message_history if msg.type in category_events]
            
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


# Global event bus instance
EVENT_BUS = EventBus()


# # Convenience functions for easier usage
# def subscribe(event_type: EventType, callback: Callable[[EventMessage], None], subscriber_name: str = "Unknown") -> bool:
#     """Subscribe to an event type using the global event bus."""
#     return EVENT_BUS.subscribe(event_type, callback, subscriber_name)


# def unsubscribe(event_type: EventType, callback: Callable[[EventMessage], None], subscriber_name: str = "Unknown") -> bool:
#     """Unsubscribe from an event type using the global event bus."""
#     return EVENT_BUS.unsubscribe(event_type, callback, subscriber_name)


# def publish(event_type: EventType, data: Any = None, publisher_name: str = "Unknown") -> bool:
#     """Publish an event using the global event bus."""
#     return EVENT_BUS.publish(event_type, data, publisher_name)


# def get_subscriber_count(event_type: EventType) -> int:
#     """Get subscriber count for an event type."""
#     return EVENT_BUS.get_subscriber_count(event_type)


# def get_all_event_types() -> List[EventType]:
#     """Get all event types with subscribers."""
#     return EVENT_BUS.get_all_event_types()


# def clear_subscribers(event_type: Optional[EventType] = None):
#     """Clear subscribers for an event type or all events."""
#     EVENT_BUS.clear_subscribers(event_type)


# def set_debug_mode(enabled: bool):
#     """Enable or disable debug mode."""
#     EVENT_BUS.set_debug_mode(enabled)


# def get_messages_by_category(category: str, limit: Optional[int] = None) -> List[EventMessage]:
#     """Get messages by category prefix."""
#     return EVENT_BUS.get_messages_by_category(category, limit) 