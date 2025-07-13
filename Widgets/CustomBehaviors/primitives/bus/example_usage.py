"""
Example usage of the EventBus system.

This file demonstrates how to use the event bus for communication between classes.
"""

from typing import Any, Tuple
import time
from .EventBus import EventMessage, subscribe, publish, unsubscribe, get_subscriber_count, DEBUG
from .event_type_constant import EventType


class CombatSystem:
    """Example class that publishes combat events."""
    
    def __init__(self, name: str):
        self.name = name
    
    def player_attacked(self, target_id: int, damage: float):
        """Publish a player attack event."""
        event_data = {
            "attacker": self.name,
            "target_id": target_id,
            "damage": damage,
            "timestamp": time.time()
        }
        publish(EventType.PLAYER_ATTACKED, event_data, f"CombatSystem_{self.name}")
    
    def enemy_died(self, enemy_id: int, position: Tuple[float, float]):
        """Publish an enemy death event."""
        event_data = {
            "enemy_id": enemy_id,
            "position": position,
            "killer": self.name
        }
        publish(EventType.ENEMY_DIED, event_data, f"CombatSystem_{self.name}")


class LootSystem:
    """Example class that subscribes to combat events and publishes loot events."""
    
    def __init__(self, name: str):
        self.name = name
        self.loot_count = 0
        
        # Subscribe to enemy death events
        subscribe(EventType.ENEMY_DIED, self.on_enemy_death, f"LootSystem_{self.name}")
    
    def on_enemy_death(self, message: EventMessage):
        """Handle enemy death events."""
        print(f"[{self.name}] Enemy died! Processing loot...")
        
        # Simulate loot processing
        loot_data = {
            "enemy_id": message.data["enemy_id"],
            "position": message.data["position"],
            "loot_items": ["Gold", "Materials", "Equipment"],
            "loot_count": self.loot_count
        }
        
        self.loot_count += 1
        publish(EventType.LOOT_ENEMY_LOOT, loot_data, f"LootSystem_{self.name}")
    
    def cleanup(self):
        """Unsubscribe from events when cleaning up."""
        unsubscribe(EventType.ENEMY_DIED, self.on_enemy_death, f"LootSystem_{self.name}")


class StatisticsTracker:
    """Example class that tracks statistics from various events."""
    
    def __init__(self, name: str):
        self.name = name
        self.attack_count = 0
        self.total_damage = 0.0
        self.loot_count = 0
        
        # Subscribe to multiple event types
        subscribe(EventType.PLAYER_ATTACKED, self.on_player_attack, f"Stats_{self.name}")
        subscribe(EventType.LOOT_ENEMY_LOOT, self.on_enemy_loot, f"Stats_{self.name}")
    
    def on_player_attack(self, message: EventMessage):
        """Track attack statistics."""
        self.attack_count += 1
        self.total_damage += message.data["damage"]
        
        print(f"[{self.name}] Attack #{self.attack_count}: {message.data['damage']} damage "
              f"to target {message.data['target_id']}")
    
    def on_enemy_loot(self, message: EventMessage):
        """Track loot statistics."""
        self.loot_count += 1
        print(f"[{self.name}] Loot #{self.loot_count}: {len(message.data['loot_items'])} items "
              f"from enemy {message.data['enemy_id']}")
    
    def get_stats(self):
        """Get current statistics."""
        return {
            "attacks": self.attack_count,
            "total_damage": self.total_damage,
            "loot_count": self.loot_count,
            "avg_damage": self.total_damage / self.attack_count if self.attack_count > 0 else 0
        }
    
    def cleanup(self):
        """Unsubscribe from events when cleaning up."""
        unsubscribe(EventType.PLAYER_ATTACKED, self.on_player_attack, f"Stats_{self.name}")
        unsubscribe(EventType.LOOT_ENEMY_LOOT, self.on_enemy_loot, f"Stats_{self.name}")


class ChatSystem:
    """Example class that provides chat functionality based on events."""
    
    def __init__(self, name: str):
        self.name = name
        
        # Subscribe to various events for chat notifications
        subscribe(EventType.PLAYER_ATTACKED, self.on_attack_chat, f"Chat_{self.name}")
        subscribe(EventType.ENEMY_DIED, self.on_death_chat, f"Chat_{self.name}")
        subscribe(EventType.LOOT_ENEMY_LOOT, self.on_loot_chat, f"Chat_{self.name}")
    
    def on_attack_chat(self, message: EventMessage):
        """Send attack chat message."""
        chat_data = {
            "message": f"{message.data['attacker']} attacks for {message.data['damage']:.1f} damage!",
            "channel": "combat",
            "color": "red"
        }
        publish(EventType.CHAT_MESSAGE, chat_data, f"Chat_{self.name}")
    
    def on_death_chat(self, message: EventMessage):
        """Send death chat message."""
        chat_data = {
            "message": f"Enemy {message.data['enemy_id']} has been defeated!",
            "channel": "combat",
            "color": "green"
        }
        publish(EventType.CHAT_MESSAGE, chat_data, f"Chat_{self.name}")
    
    def on_loot_chat(self, message: EventMessage):
        """Send loot chat message."""
        chat_data = {
            "message": f"Looted {len(message.data['loot_items'])} items from enemy {message.data['enemy_id']}",
            "channel": "loot",
            "color": "yellow"
        }
        publish(EventType.CHAT_MESSAGE, chat_data, f"Chat_{self.name}")
    
    def cleanup(self):
        """Unsubscribe from events when cleaning up."""
        unsubscribe(EventType.PLAYER_ATTACKED, self.on_attack_chat, f"Chat_{self.name}")
        unsubscribe(EventType.ENEMY_DIED, self.on_death_chat, f"Chat_{self.name}")
        unsubscribe(EventType.LOOT_ENEMY_LOOT, self.on_loot_chat, f"Chat_{self.name}")


def demo_event_bus():
    """Demonstrate the event bus functionality."""
    import time
    
    print("=== Event Bus Demo ===\n")
    
    # Enable debug mode to see subscription/publishing logs
    # Note: DEBUG is a module-level flag, set it to True in EventBus.py to enable debug output
    
    # Create systems
    combat = CombatSystem("MainCombat")
    loot = LootSystem("MainLoot")
    stats = StatisticsTracker("MainStats")
    chat = ChatSystem("MainChat")
    
    # Create a simple chat message handler
    def handle_chat_message(message: EventMessage):
        print(f"[CHAT] [{message.data['channel'].upper()}] {message.data['message']}")
    
    subscribe(EventType.CHAT_MESSAGE, handle_chat_message, "DemoChatHandler")
    
    print("Systems created and subscribed to events.\n")
    
    # Simulate some combat actions
    print("--- Simulating Combat ---")
    combat.player_attacked(1001, 150.5)
    time.sleep(0.1)
    combat.player_attacked(1001, 200.0)
    time.sleep(0.1)
    combat.enemy_died(1001, (100.0, 200.0))
    time.sleep(0.1)
    
    combat.player_attacked(1002, 175.3)
    time.sleep(0.1)
    combat.enemy_died(1002, (150.0, 250.0))
    time.sleep(0.1)
    
    print(f"\n--- Statistics ---")
    print(f"Stats: {stats.get_stats()}")
    
    print(f"\n--- Subscriber Counts ---")
    print(f"PLAYER_ATTACKED: {get_subscriber_count(EventType.PLAYER_ATTACKED)} subscribers")
    print(f"ENEMY_DIED: {get_subscriber_count(EventType.ENEMY_DIED)} subscribers")
    print(f"LOOT_ENEMY_LOOT: {get_subscriber_count(EventType.LOOT_ENEMY_LOOT)} subscribers")
    print(f"CHAT_MESSAGE: {get_subscriber_count(EventType.CHAT_MESSAGE)} subscribers")
    
    # Cleanup
    print("\n--- Cleaning Up ---")
    loot.cleanup()
    stats.cleanup()
    chat.cleanup()
    unsubscribe(EventType.CHAT_MESSAGE, handle_chat_message, "DemoChatHandler")
    
    print("Demo completed!")


if __name__ == "__main__":
    demo_event_bus() 