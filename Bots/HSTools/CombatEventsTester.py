"""
CombatEvents Tester - Test and Demo Script for the Combat Events System
========================================================================

This script provides a comprehensive UI to test, visualize, and demonstrate all
CombatEvents functionality. Use it as a reference for implementing combat event
handling in your own bots.

Features:
---------
1. Event Log Tab: Shows real-time combat events as they happen
2. State Queries Tab: Query agent states (casting, attacking, aftercast)
3. Damage Tracker Tab: Track damage dealt/received broken down by skill and target
4. Agent Tracking Tab: Enable effect/state tracking for specific agents

How to Use:
-----------
1. Run this script as a bot
2. The window shows different tabs for different functionality
3. Enter combat to see events being logged in real-time
4. Use the Damage Tracker to analyze your DPS

Example Code Patterns:
----------------------

1. Basic Event Handling:
```python
from Py4GWCoreLib.native_src.events import CombatEvents

# Initialize (call once)
CombatEvents.initialize()

# Register callbacks for events you care about
def on_skill_cast(caster_id, skill_id, target_id):
    print(f"Agent {caster_id} casting skill {skill_id}")

CombatEvents.on_skill_activated(on_skill_cast)

# In your main loop, call update() every frame
def main():
    CombatEvents.update()
```

2. Reacting to Aftercast (Perfect Skill Chaining):
```python
def on_aftercast_done(agent_id):
    if agent_id == my_agent_id:
        # Use next skill immediately - perfect timing!
        use_next_skill()

CombatEvents.on_aftercast_ended(on_aftercast_done)
```

3. Damage Tracking:
```python
def on_damage(target_id, source_id, damage_percent, skill_id):
    # damage_percent is fraction of target's max HP
    actual_damage = damage_percent * Agent.GetMaxHealth(target_id)
    print(f"Dealt {actual_damage:.0f} damage with skill {skill_id}")

CombatEvents.on_damage(on_damage)
CombatEvents.on_critical_hit(on_damage)  # Same signature
```

4. Tracking Enemy Effects:
```python
# Start tracking an enemy
CombatEvents.track_agent_effects(enemy_id)

# Get callbacks when they gain/lose buffs
def on_buff_gained(agent_id, skill_id):
    print(f"Enemy gained buff: {Skill.GetName(skill_id)}")

CombatEvents.on_buff_applied(on_buff_gained)
```

5. Querying Current State:
```python
# Check if an agent is currently casting
if CombatEvents.is_agent_casting(enemy_id):
    skill_id = CombatEvents.get_casting_skill(enemy_id)
    print(f"Enemy is casting {Skill.GetName(skill_id)}")
    # Maybe interrupt them!

# Check if agent can act (not disabled/knocked down)
if CombatEvents.can_agent_act(my_agent_id):
    use_skill()
```

6. Stance Detection:
```python
# Know when enemies use stances
def on_stance_used(agent_id, skill_id, duration):
    print(f"Enemy activated stance for {duration}s")

CombatEvents.on_stance_activated(on_stance_used)

# Query if agent has a stance
if CombatEvents.has_active_stance(enemy_id):
    remaining = CombatEvents.get_stance_time_remaining(enemy_id)
```

See Also:
---------
- CombatEvents.py: Main Python module with full documentation
- py_combat_events.h/.cpp: C++ packet handling (for advanced users)
"""

from Py4GWCoreLib import *
from Py4GWCoreLib.CombatEvents import CombatEvents, EventTypes
from typing import List, Optional
import time

MODULE_NAME = "CombatEvents Tester"

# ============================================================================
# State tracking for the UI
# ============================================================================

class EventLog:
    """Stores recent events for display in the UI"""
    def __init__(self, max_entries: int = 50):
        self.max_entries = max_entries
        self.entries: List[tuple] = []  # (timestamp, event_type, message)

    def add(self, event_type: str, message: str):
        timestamp = time.time()
        self.entries.append((timestamp, event_type, message))
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)

    def clear(self):
        self.entries.clear()

    def get_recent(self, count: int = 20) -> List[tuple]:
        return list(reversed(self.entries[-count:]))


class TesterState:
    """Global state for the tester widget"""
    def __init__(self):
        # Event logging
        self.event_log = EventLog()
        self.callbacks_registered = False
        self.combat_events_initialized = False

        # Filters
        self.show_skill_events = True
        self.show_damage_events = True
        self.show_attack_events = True
        self.show_knockdown_events = True
        self.show_effect_events = True
        self.show_energy_events = True
        self.show_aftercast_events = True

        # Filter by agent
        self.filter_player_only = False

        # Damage tracker state
        self.damage_tracker_running = False
        self.damage_total_dealt: float = 0.0
        self.damage_total_received: float = 0.0
        self.damage_dealt_by_skill: dict = {}  # skill_id -> damage dealt
        self.damage_dealt_by_target: dict = {}  # target_id -> damage dealt to them
        self.damage_received_by_skill: dict = {}  # skill_id -> damage received
        self.damage_received_from_source: dict = {}  # source_id -> damage received from them
        self.critical_hits: int = 0
        self.damage_track_agent_id: Optional[int] = None

        # Selected agent for state queries
        self.selected_agent_id = 0


state = TesterState()

# ============================================================================
# Helper Functions
# ============================================================================

def get_agent_name(agent_id: int) -> str:
    """Get agent name or ID string"""
    if agent_id == 0:
        return "None"
    try:
        name = Agent.GetNameByID(agent_id)
        if name and len(name) > 0:
            return name
        return f"Agent#{agent_id}"
    except:
        return f"Agent#{agent_id}"

def get_skill_name(skill_id: int) -> str:
    """Get skill name or ID string"""
    if skill_id == 0:
        return "None"
    try:
        name = Skill.GetName(skill_id)
        if name and len(name) > 0:
            return name
        return f"Skill#{skill_id}"
    except:
        return f"Skill#{skill_id}"

def should_log_agent(agent_id: int) -> bool:
    """Check if we should log events for this agent"""
    if not state.filter_player_only:
        return True
    try:
        return agent_id == Player.GetAgentID()
    except:
        return True

# ============================================================================
# Event Callbacks
# ============================================================================

# Skill events
def on_skill_activated(caster_id: int, skill_id: int, target_id: int):
    if state.show_skill_events and should_log_agent(caster_id):
        caster = get_agent_name(caster_id)
        skill = get_skill_name(skill_id)
        target = get_agent_name(target_id) if target_id else "self"
        # Try to get cast duration from state
        try:
            cast_state = CombatEvents.get_casting_state(caster_id)
            if cast_state and cast_state.duration > 0:
                state.event_log.add("SKILL", f"{caster} casting {skill} ({cast_state.duration:.2f}s) -> {target}")
            else:
                state.event_log.add("SKILL", f"{caster} casting {skill} -> {target}")
        except:
            state.event_log.add("SKILL", f"{caster} casting {skill} -> {target}")

def on_skill_finished(agent_id: int, skill_id: int):
    if state.show_skill_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        skill = get_skill_name(skill_id)
        state.event_log.add("SKILL", f"{agent} FINISHED {skill}")

def on_skill_interrupted(agent_id: int, skill_id: int):
    if state.show_skill_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        skill = get_skill_name(skill_id)
        state.event_log.add("SKILL", f"{agent} INTERRUPTED {skill}")

def on_instant_skill(caster_id: int, skill_id: int, target_id: int):
    if state.show_skill_events and should_log_agent(caster_id):
        caster = get_agent_name(caster_id)
        skill = get_skill_name(skill_id)
        target = get_agent_name(target_id) if target_id else "self"
        state.event_log.add("SKILL", f"{caster} INSTANT {skill} -> {target}")

# Attack events
def on_attack_started(attacker_id: int, target_id: int):
    if state.show_attack_events and should_log_agent(attacker_id):
        attacker = get_agent_name(attacker_id)
        target = get_agent_name(target_id)
        # Check if it's a skill attack
        try:
            attack_state = CombatEvents.get_attack_state(attacker_id)
            if attack_state and attack_state.is_skill_attack and attack_state.skill_id:
                skill = get_skill_name(attack_state.skill_id)
                state.event_log.add("ATTACK", f"{attacker} attack ({skill}) -> {target}")
            else:
                state.event_log.add("ATTACK", f"{attacker} auto-attack -> {target}")
        except:
            state.event_log.add("ATTACK", f"{attacker} attack -> {target}")

def on_attack_finished(attacker_id: int, target_id: int):
    if state.show_attack_events and should_log_agent(attacker_id):
        attacker = get_agent_name(attacker_id)
        target = get_agent_name(target_id)
        state.event_log.add("ATTACK", f"{attacker} attack finished -> {target}")

# Casting lock events (during cast animation)
def on_casting_started(agent_id: int):
    if state.show_aftercast_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        state.event_log.add("STATE", f"{agent} CASTING (disabled)")

def on_casting_ended(agent_id: int):
    if state.show_aftercast_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        state.event_log.add("STATE", f"{agent} CAST DONE")

# True aftercast events (after cast animation)
def on_aftercast_started(agent_id: int):
    if state.show_aftercast_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        state.event_log.add("STATE", f"{agent} AFTERCAST (disabled)")

def on_aftercast_ended(agent_id: int):
    if state.show_aftercast_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        state.event_log.add("STATE", f"{agent} CAN ACT")

# Knockdown events
def on_knockdown(agent_id: int, duration: float):
    if state.show_knockdown_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        state.event_log.add("KD", f"{agent} knocked down for {duration:.2f}s")

# Damage events
def on_damage(target_id: int, source_id: int, value: float, skill_id: int):
    # Note: value is a fraction of max HP (e.g., 0.05 = 5% of max HP)
    # We calculate actual damage by multiplying by target's max HP

    # Calculate actual damage
    actual_dmg = 0.0
    try:
        max_hp = Agent.GetMaxHealth(target_id)
        if max_hp > 0:
            actual_dmg = abs(value) * max_hp
    except:
        actual_dmg = abs(value) * 500  # Fallback estimate

    # Log to event log
    if state.show_damage_events and (should_log_agent(source_id) or should_log_agent(target_id)):
        source = get_agent_name(source_id)
        target = get_agent_name(target_id)
        if skill_id:
            skill = get_skill_name(skill_id)
            state.event_log.add("DMG", f"{source} -> {target}: {actual_dmg:.0f} dmg ({skill})")
        else:
            state.event_log.add("DMG", f"{source} -> {target}: {actual_dmg:.0f} dmg (auto-attack)")

    # Track damage using actual values
    if state.damage_tracker_running:
        # Track damage dealt (when we are the source)
        if state.damage_track_agent_id is None or source_id == state.damage_track_agent_id:
            state.damage_total_dealt += actual_dmg
            state.damage_dealt_by_skill[skill_id] = state.damage_dealt_by_skill.get(skill_id, 0) + actual_dmg
            state.damage_dealt_by_target[target_id] = state.damage_dealt_by_target.get(target_id, 0) + actual_dmg
        # Track damage received (when we are the target)
        if state.damage_track_agent_id is None or target_id == state.damage_track_agent_id:
            state.damage_total_received += actual_dmg
            state.damage_received_by_skill[skill_id] = state.damage_received_by_skill.get(skill_id, 0) + actual_dmg
            state.damage_received_from_source[source_id] = state.damage_received_from_source.get(source_id, 0) + actual_dmg

def on_critical_hit(target_id: int, source_id: int, value: float, skill_id: int):
    # Calculate actual damage
    actual_dmg = 0.0
    try:
        max_hp = Agent.GetMaxHealth(target_id)
        if max_hp > 0:
            actual_dmg = abs(value) * max_hp
    except:
        actual_dmg = abs(value) * 500  # Fallback estimate

    if state.show_damage_events and (should_log_agent(source_id) or should_log_agent(target_id)):
        source = get_agent_name(source_id)
        target = get_agent_name(target_id)
        if skill_id:
            skill = get_skill_name(skill_id)
            state.event_log.add("CRIT", f"{source} -> {target}: {actual_dmg:.0f} CRIT! ({skill})")
        else:
            state.event_log.add("CRIT", f"{source} -> {target}: {actual_dmg:.0f} CRIT! (auto-attack)")

    # Track crits - add damage to totals just like on_damage does
    if state.damage_tracker_running:
        # Track damage dealt (when we are the source)
        if state.damage_track_agent_id is None or source_id == state.damage_track_agent_id:
            state.damage_total_dealt += actual_dmg
            state.damage_dealt_by_skill[skill_id] = state.damage_dealt_by_skill.get(skill_id, 0) + actual_dmg
            state.damage_dealt_by_target[target_id] = state.damage_dealt_by_target.get(target_id, 0) + actual_dmg
            state.critical_hits += 1
        # Track damage received (when we are the target)
        if state.damage_track_agent_id is None or target_id == state.damage_track_agent_id:
            state.damage_total_received += actual_dmg
            state.damage_received_by_skill[skill_id] = state.damage_received_by_skill.get(skill_id, 0) + actual_dmg
            state.damage_received_from_source[source_id] = state.damage_received_from_source.get(source_id, 0) + actual_dmg

# Effect events
def on_effect_applied(agent_id: int, effect_id: int):
    # Note: This is for internal visual/animation effect IDs, not very useful
    # We don't log these by default as they're just internal IDs
    pass

def on_effect_removed(agent_id: int, effect_id: int):
    # Note: This is for internal visual/animation effect IDs, not very useful
    pass

def on_skill_effect_applied(_caster_id: int, _skill_id: int, _target_id: int, _effect_id: int):
    """Called when a skill effect hits a target (from packet)"""
    # This is packet-based - less reliable, kept for backwards compatibility
    # Use on_buff_applied/on_buff_removed for reliable effect tracking
    pass

def on_buff_applied(agent_id: int, skill_id: int):
    """Called when a buff/effect is actually applied to a tracked agent (from polling)"""
    if state.show_effect_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        skill = get_skill_name(skill_id)
        state.event_log.add("BUFF+", f"{agent} gained: {skill}")

def on_buff_removed(agent_id: int, skill_id: int):
    """Called when a buff/effect is removed from a tracked agent (from polling)"""
    if state.show_effect_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        skill = get_skill_name(skill_id)
        state.event_log.add("BUFF-", f"{agent} lost: {skill}")

# Specific callbacks with skill correlation
def on_condition_applied(target_id: int, skill_id: int, caster_id: int):
    """Called when a condition is applied - includes which skill caused it"""
    if state.show_effect_events and should_log_agent(target_id):
        target = get_agent_name(target_id)
        if skill_id:
            skill = get_skill_name(skill_id)
            caster = get_agent_name(caster_id)
            state.event_log.add("COND+", f"{target} gained CONDITION: {skill} (from {caster})")
        else:
            state.event_log.add("COND+", f"{target} gained CONDITION")

def on_hex_applied(target_id: int, skill_id: int, caster_id: int):
    """Called when a hex is applied - includes which skill caused it"""
    if state.show_effect_events and should_log_agent(target_id):
        target = get_agent_name(target_id)
        if skill_id:
            skill = get_skill_name(skill_id)
            caster = get_agent_name(caster_id)
            state.event_log.add("HEX+", f"{target} gained HEX: {skill} (from {caster})")
        else:
            state.event_log.add("HEX+", f"{target} gained HEX")

def on_enchant_applied(target_id: int, skill_id: int, caster_id: int):
    """Called when an enchantment is applied - includes which skill caused it"""
    if state.show_effect_events and should_log_agent(target_id):
        target = get_agent_name(target_id)
        if skill_id:
            skill = get_skill_name(skill_id)
            caster = get_agent_name(caster_id)
            state.event_log.add("ENCH+", f"{target} gained ENCHANT: {skill} (from {caster})")
        else:
            state.event_log.add("ENCH+", f"{target} gained ENCHANTMENT")

def on_condition_removed(agent_id: int):
    """Called when all conditions are removed"""
    if state.show_effect_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        state.event_log.add("COND-", f"{agent} lost all CONDITIONS")

def on_hex_removed(agent_id: int):
    """Called when all hexes are removed"""
    if state.show_effect_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        state.event_log.add("HEX-", f"{agent} lost all HEXES")

def on_enchant_removed(agent_id: int):
    """Called when all enchantments are removed"""
    if state.show_effect_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        state.event_log.add("ENCH-", f"{agent} lost all ENCHANTMENTS")

# Stance events
def on_stance_activated(agent_id: int, skill_id: int, duration: float):
    """Called when an agent activates a stance skill"""
    if state.show_effect_events:
        agent = get_agent_name(agent_id)
        skill = get_skill_name(skill_id)
        state.event_log.add("STANCE+", f"{agent} activated STANCE: {skill} ({duration:.1f}s)")

def on_stance_ended(agent_id: int, skill_id: int):
    """Called when a stance ends"""
    if state.show_effect_events:
        agent = get_agent_name(agent_id)
        skill = get_skill_name(skill_id)
        state.event_log.add("STANCE-", f"{agent} STANCE ended: {skill}")

# Energy events
def on_energy_gained(agent_id: int, amount: float):
    if state.show_energy_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        # energygain from GenericValue is raw energy points
        state.event_log.add("ENERGY", f"{agent} +{abs(amount):.0f} energy")

def on_energy_spent(agent_id: int, amount: float):
    if state.show_energy_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        # energy_spent from GenericFloat is fraction of max energy
        # Convert to actual energy by multiplying by max energy
        actual_energy = abs(amount)
        try:
            max_energy = Agent.GetMaxEnergy(agent_id)
            if max_energy > 0 and actual_energy < 1.0:
                # It's a fraction, convert to actual value
                actual_energy = actual_energy * max_energy
        except:
            pass
        state.event_log.add("ENERGY", f"{agent} -{actual_energy:.0f} energy")

# ============================================================================
# Callback Registration
# ============================================================================

def initialize_combat_events():
    """Initialize the CombatEvents system"""
    if state.combat_events_initialized:
        return True

    try:
        success = CombatEvents.initialize()
        if success:
            state.combat_events_initialized = True
            state.event_log.add("SYSTEM", "CombatEvents initialized successfully")
            return True
        else:
            state.event_log.add("ERROR", "Failed to initialize CombatEvents")
            return False
    except Exception as e:
        state.event_log.add("ERROR", f"Failed to initialize CombatEvents: {e}")
        return False

def register_callbacks():
    """Register all event callbacks"""
    if state.callbacks_registered:
        return

    # Make sure CombatEvents is initialized first
    if not state.combat_events_initialized:
        if not initialize_combat_events():
            return

    try:
        # Use the new snake_case method names
        CombatEvents.on_skill_activated(on_skill_activated)
        CombatEvents.on_skill_finished(on_skill_finished)
        CombatEvents.on_skill_interrupted(on_skill_interrupted)
        CombatEvents.on_instant_skill_activated(on_instant_skill)

        CombatEvents.on_attack_started(on_attack_started)
        CombatEvents.on_attack_finished(on_attack_finished)

        CombatEvents.on_casting_started(on_casting_started)
        CombatEvents.on_casting_ended(on_casting_ended)
        CombatEvents.on_aftercast_started(on_aftercast_started)
        CombatEvents.on_aftercast_ended(on_aftercast_ended)

        CombatEvents.on_knockdown(on_knockdown)

        CombatEvents.on_damage(on_damage)
        CombatEvents.on_critical_hit(on_critical_hit)

        CombatEvents.on_effect_applied(on_effect_applied)
        CombatEvents.on_effect_removed(on_effect_removed)
        CombatEvents.on_skill_effect_applied(on_skill_effect_applied)
        CombatEvents.on_buff_applied(on_buff_applied)
        CombatEvents.on_buff_removed(on_buff_removed)

        # State change callbacks with skill correlation (requires track_agent_effects())
        CombatEvents.on_condition_applied(on_condition_applied)
        CombatEvents.on_hex_applied(on_hex_applied)
        CombatEvents.on_enchant_applied(on_enchant_applied)
        CombatEvents.on_condition_removed(on_condition_removed)
        CombatEvents.on_hex_removed(on_hex_removed)
        CombatEvents.on_enchant_removed(on_enchant_removed)

        # Stance tracking (works for any agent, no need to track)
        CombatEvents.on_stance_activated(on_stance_activated)
        CombatEvents.on_stance_ended(on_stance_ended)

        CombatEvents.on_energy_gained(on_energy_gained)
        CombatEvents.on_energy_spent(on_energy_spent)

        # Start tracking effects for player and target
        try:
            player_id = Player.GetAgentID()
            if player_id:
                CombatEvents.track_agent_effects(player_id)
                state.event_log.add("SYSTEM", f"Tracking effects for player (Agent#{player_id})")
        except:
            pass

        state.callbacks_registered = True
        state.event_log.add("SYSTEM", "Callbacks registered successfully")
    except Exception as e:
        state.event_log.add("ERROR", f"Failed to register callbacks: {e}")

def unregister_callbacks():
    """Clear all callbacks"""
    try:
        CombatEvents.clear_callbacks()
        state.callbacks_registered = False
        state.event_log.add("SYSTEM", "Callbacks cleared")
    except Exception as e:
        state.event_log.add("ERROR", f"Failed to clear callbacks: {e}")

# ============================================================================
# UI Drawing
# ============================================================================

def get_event_color(event_type: str) -> tuple:
    """Get color for event type"""
    colors = {
        "SKILL": (100, 200, 255, 255),     # Light blue
        "ATTACK": (255, 150, 100, 255),    # Orange
        "STATE": (200, 255, 100, 255),     # Yellow-green (cast/aftercast states)
        "KD": (255, 100, 100, 255),        # Red
        "DMG": (255, 200, 100, 255),       # Gold
        "CRIT": (255, 50, 50, 255),        # Bright red
        "BUFF+": (100, 255, 100, 255),     # Green (buff gained)
        "BUFF-": (255, 100, 255, 255),     # Pink (buff lost)
        "COND+": (255, 150, 50, 255),      # Orange (condition gained)
        "COND-": (255, 200, 150, 255),     # Light orange (condition lost)
        "HEX+": (200, 50, 200, 255),       # Purple (hex gained)
        "HEX-": (200, 150, 200, 255),      # Light purple (hex lost)
        "ENCH+": (50, 200, 255, 255),      # Cyan (enchant gained)
        "ENCH-": (150, 200, 255, 255),     # Light cyan (enchant lost)
        "STANCE+": (255, 255, 100, 255),   # Yellow (stance activated)
        "STANCE-": (200, 200, 100, 255),   # Dim yellow (stance ended)
        "ENERGY": (100, 255, 200, 255),    # Cyan
        "SYSTEM": (150, 150, 150, 255),    # Gray
        "ERROR": (255, 0, 0, 255),         # Red
    }
    return colors.get(event_type, (255, 255, 255, 255))

def draw_event_log_tab():
    """Draw the event log tab"""
    PyImGui.text("Event Filters:")

    # Filter checkboxes in a row
    state.show_skill_events = PyImGui.checkbox("Skills", state.show_skill_events)
    PyImGui.same_line(0, -1)
    state.show_damage_events = PyImGui.checkbox("Damage", state.show_damage_events)
    PyImGui.same_line(0, -1)
    state.show_attack_events = PyImGui.checkbox("Attacks", state.show_attack_events)
    PyImGui.same_line(0, -1)
    state.show_aftercast_events = PyImGui.checkbox("Aftercast", state.show_aftercast_events)

    state.show_knockdown_events = PyImGui.checkbox("Knockdown", state.show_knockdown_events)
    PyImGui.same_line(0, -1)
    state.show_effect_events = PyImGui.checkbox("Effects", state.show_effect_events)
    PyImGui.same_line(0, -1)
    state.show_energy_events = PyImGui.checkbox("Energy", state.show_energy_events)
    PyImGui.same_line(0, -1)
    state.filter_player_only = PyImGui.checkbox("Player Only", state.filter_player_only)

    PyImGui.separator()

    # Control buttons
    if not state.combat_events_initialized:
        if PyImGui.button("Initialize CombatEvents"):
            initialize_combat_events()
    else:
        PyImGui.text_colored("CombatEvents: INITIALIZED", (100, 255, 100, 255))

    PyImGui.same_line(0, -1)

    if not state.callbacks_registered:
        if PyImGui.button("Register Callbacks"):
            register_callbacks()
    else:
        if PyImGui.button("Unregister Callbacks"):
            unregister_callbacks()

    PyImGui.same_line(0, -1)
    if PyImGui.button("Clear Log"):
        state.event_log.clear()

    PyImGui.separator()

    # Effect tracking controls
    PyImGui.text("Effect Tracking:")
    PyImGui.same_line(0, -1)
    if PyImGui.button("Track Target"):
        try:
            target_id = Player.GetTargetID()
            if target_id and not CombatEvents.is_tracking_agent(target_id):
                CombatEvents.track_agent_effects(target_id)
                state.event_log.add("SYSTEM", f"Now tracking effects for {get_agent_name(target_id)}")
        except Exception as e:
            state.event_log.add("ERROR", f"Failed to track target: {e}")

    PyImGui.same_line(0, -1)
    tracked = CombatEvents.get_tracked_agents() if state.combat_events_initialized else set()
    PyImGui.text(f"Tracking: {len(tracked)} agents")

    PyImGui.separator()

    # Event log display
    if PyImGui.begin_child("EventLogChild", size=(0, 300), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
        for timestamp, event_type, message in state.event_log.get_recent(50):
            color = get_event_color(event_type)
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            PyImGui.text_colored(f"[{time_str}] [{event_type:8}] {message}", color)
        PyImGui.end_child()

def draw_state_queries_tab():
    """Draw the state queries tab"""
    try:
        player_id = Player.GetAgentID()
    except:
        player_id = 0

    try:
        target_id = Player.GetTargetID()
    except:
        target_id = 0

    # Agent selector
    PyImGui.text("Query Agent:")
    PyImGui.same_line(0, -1)
    if PyImGui.button("Player"):
        state.selected_agent_id = player_id
    PyImGui.same_line(0, -1)
    if PyImGui.button("Target"):
        state.selected_agent_id = target_id if target_id else player_id
    PyImGui.same_line(0, -1)
    state.selected_agent_id = PyImGui.input_int("Agent ID", state.selected_agent_id)

    agent_id = state.selected_agent_id if state.selected_agent_id else player_id
    agent_name = get_agent_name(agent_id)

    PyImGui.separator()
    PyImGui.text(f"Querying: {agent_name} (ID: {agent_id})")
    PyImGui.separator()

    if PyImGui.begin_child("StateQueriesChild", (0, 350), True, 0):
        try:
            # Casting state
            if PyImGui.collapsing_header("Casting State", PyImGui.TreeNodeFlags.DefaultOpen):
                is_casting = CombatEvents.is_agent_casting(agent_id)
                PyImGui.text(f"Is Casting: {is_casting}")

                if is_casting:
                    skill_id = CombatEvents.get_casting_skill(agent_id)
                    target = CombatEvents.get_cast_target(agent_id)
                    progress = CombatEvents.get_cast_progress(agent_id)
                    remaining = CombatEvents.get_cast_time_remaining(agent_id)

                    PyImGui.text(f"  Skill: {get_skill_name(skill_id)} ({skill_id})")
                    PyImGui.text(f"  Target: {get_agent_name(target) if target else 'none'}")
                    if progress >= 0:
                        PyImGui.text(f"  Progress: {progress*100:.1f}% ({remaining}ms remaining)")
                        PyImGui.progress_bar(progress, 200.0, 0.0, "")
                    else:
                        PyImGui.text(f"  Progress: N/A")

            # Attack state
            if PyImGui.collapsing_header("Attack State", PyImGui.TreeNodeFlags.DefaultOpen):
                is_attacking = CombatEvents.is_agent_attacking(agent_id)
                PyImGui.text(f"Is Attacking: {is_attacking}")

                if is_attacking:
                    attack_target = CombatEvents.get_attack_target(agent_id)
                    PyImGui.text(f"  Target: {get_agent_name(attack_target)}")

            # Action state
            if PyImGui.collapsing_header("Action State", PyImGui.TreeNodeFlags.DefaultOpen):
                is_disabled = CombatEvents.is_agent_disabled(agent_id)
                in_aftercast = CombatEvents.is_agent_in_aftercast(agent_id)
                can_act = CombatEvents.can_agent_act(agent_id)

                PyImGui.text(f"Is Disabled: {is_disabled}")
                PyImGui.text(f"In True Aftercast: {in_aftercast}")

                if can_act:
                    PyImGui.text_colored("  CAN ACT!", (100, 255, 100, 255))
                elif in_aftercast:
                    PyImGui.text_colored("  In aftercast (waiting...)", (255, 200, 100, 255))
                elif is_disabled:
                    PyImGui.text_colored("  Casting (disabled)", (255, 150, 100, 255))
                else:
                    PyImGui.text_colored("  Cannot act", (255, 100, 100, 255))

            # Knockdown state
            if PyImGui.collapsing_header("Knockdown State", PyImGui.TreeNodeFlags.DefaultOpen):
                is_kd = CombatEvents.is_agent_knocked_down(agent_id)
                PyImGui.text(f"Is Knocked Down: {is_kd}")

                if is_kd:
                    kd_remaining = CombatEvents.get_knockdown_time_remaining(agent_id)
                    PyImGui.text(f"  Time Remaining: {kd_remaining}ms")

            # Stance state
            if PyImGui.collapsing_header("Stance State", PyImGui.TreeNodeFlags.DefaultOpen):
                has_stance = CombatEvents.has_active_stance(agent_id)
                PyImGui.text(f"Has Active Stance: {has_stance}")

                if has_stance:
                    stance_id = CombatEvents.get_active_stance(agent_id)
                    stance_remaining = CombatEvents.get_stance_time_remaining(agent_id)
                    if stance_id:
                        PyImGui.text(f"  Stance: {get_skill_name(stance_id)}")
                        PyImGui.text(f"  Time Remaining: {stance_remaining}ms ({stance_remaining/1000:.1f}s)")

            # Condition/Hex/Enchant state (from Agent.py)
            if PyImGui.collapsing_header("Condition/Hex/Enchant State", PyImGui.TreeNodeFlags.DefaultOpen):
                try:
                    is_conditioned = Agent.IsConditioned(agent_id)
                    is_hexed = Agent.IsHexed(agent_id)
                    is_degen_hexed = Agent.IsDegenHexed(agent_id)
                    is_enchanted = Agent.IsEnchanted(agent_id)
                    is_tracked = CombatEvents.is_tracking_agent(agent_id)

                    # Show specific conditions
                    if is_conditioned:
                        PyImGui.text_colored("Has Condition: YES", (255, 150, 50, 255))
                        # Show which specific conditions
                        conditions = []
                        if Agent.IsBleeding(agent_id):
                            conditions.append("Bleeding")
                        if Agent.IsPoisoned(agent_id):
                            conditions.append("Poisoned")
                        if Agent.IsCrippled(agent_id):
                            conditions.append("Crippled")
                        if Agent.IsDeepWounded(agent_id):
                            conditions.append("Deep Wound")
                        if conditions:
                            PyImGui.text_colored(f"  Conditions: {', '.join(conditions)}", (255, 180, 100, 255))
                        else:
                            PyImGui.text("  (Other condition)")
                    else:
                        PyImGui.text("Has Condition: No")

                    if is_hexed:
                        PyImGui.text_colored("Has Hex: YES", (200, 50, 200, 255))
                        if is_degen_hexed:
                            PyImGui.text_colored("  Has Degen Hex", (200, 100, 200, 255))
                    else:
                        PyImGui.text("Has Hex: No")

                    if is_enchanted:
                        PyImGui.text_colored("Has Enchantment: YES", (50, 200, 255, 255))
                    else:
                        PyImGui.text("Has Enchantment: No")

                    PyImGui.separator()
                    PyImGui.text(f"Tracked for callbacks: {is_tracked}")
                    if not is_tracked:
                        PyImGui.text_colored("  (Use 'Track Target' to receive callbacks)", (150, 150, 150, 255))
                except Exception as e:
                    PyImGui.text(f"Error: {e}")

            # Targeting info
            if PyImGui.collapsing_header("Targeting Info"):
                agents_targeting = CombatEvents.get_agents_targeting(agent_id)
                casting_at = CombatEvents.get_agents_casting_at(agent_id)
                attacking = CombatEvents.get_agents_attacking(agent_id)

                PyImGui.text(f"Agents targeting this agent: {len(agents_targeting)}")
                PyImGui.text(f"  Casting at: {len(casting_at)}")
                PyImGui.text(f"  Attacking: {len(attacking)}")

                if agents_targeting:
                    PyImGui.text("  Agents:")
                    for aid in agents_targeting[:5]:  # Show max 5
                        PyImGui.text(f"    - {get_agent_name(aid)}")

        except Exception as e:
            PyImGui.text_colored(f"Error querying state: {e}", (255, 0, 0, 255))

        PyImGui.end_child()

def draw_all_casting_tab():
    """Draw tab showing all currently casting agents"""
    PyImGui.text("All agents currently casting:")
    PyImGui.separator()

    if PyImGui.begin_child("AllCastingChild", size=(0, 350), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
        try:
            all_casting = CombatEvents.get_all_casting()

            if not all_casting:
                PyImGui.text("No agents currently casting")
            else:
                if PyImGui.begin_table("CastingTable", 4, PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame):
                    # Header row
                    PyImGui.table_setup_column("Agent")
                    PyImGui.table_setup_column("Skill")
                    PyImGui.table_setup_column("Target")
                    PyImGui.table_setup_column("Progress")
                    PyImGui.table_headers_row()

                    for casting_state in all_casting:
                        PyImGui.table_next_row()

                        PyImGui.table_set_column_index(0)
                        PyImGui.text(get_agent_name(casting_state.agent_id))

                        PyImGui.table_set_column_index(1)
                        PyImGui.text(get_skill_name(casting_state.skill_id))

                        PyImGui.table_set_column_index(2)
                        target_name = get_agent_name(casting_state.target_id) if casting_state.target_id else "-"
                        PyImGui.text(target_name)

                        PyImGui.table_set_column_index(3)
                        progress = CombatEvents.get_cast_progress(casting_state.agent_id)
                        if progress >= 0:
                            PyImGui.progress_bar(progress, 100.0, 0.0, f"{progress*100:.0f}%")
                        else:
                            PyImGui.text("-")

                    PyImGui.end_table()

        except Exception as e:
            PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))

        PyImGui.end_child()

def draw_event_history_tab():
    """Draw tab showing event history from CombatEvents"""
    PyImGui.text("Recent events from CombatEvents history:")
    PyImGui.separator()

    if PyImGui.begin_tab_bar("HistoryTabs"):
        # Skill events
        if PyImGui.begin_tab_item("Skill Events"):
            if PyImGui.begin_child("SkillHistoryChild", size=(0, 300), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
                try:
                    events = CombatEvents.get_recent_skill_events(20)
                    if not events:
                        PyImGui.text("No recent skill events")
                    else:
                        for event in events:
                            caster = get_agent_name(event.caster_id)
                            skill = get_skill_name(event.skill_id)
                            target = get_agent_name(event.target_id) if event.target_id else "-"
                            event_type_name = get_event_type_name(event.event_type)
                            PyImGui.text(f"[{event_type_name}] {caster} | {skill} | Target: {target}")
                except Exception as e:
                    PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))
                PyImGui.end_child()
            PyImGui.end_tab_item()

        # Damage events
        if PyImGui.begin_tab_item("Damage Events"):
            if PyImGui.begin_child("DamageHistoryChild", size=(0, 300), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
                try:
                    events = CombatEvents.get_recent_damage_events(20)
                    if not events:
                        PyImGui.text("No recent damage events")
                    else:
                        for event in events:
                            source = get_agent_name(event.source_id)
                            target = get_agent_name(event.target_id)
                            skill = get_skill_name(event.skill_id) if event.skill_id else "auto"
                            crit = " CRIT" if event.is_critical else ""
                            # Calculate actual damage
                            actual_dmg = 0.0
                            try:
                                max_hp = Agent.GetMaxHealth(event.target_id)
                                if max_hp > 0:
                                    actual_dmg = abs(event.value) * max_hp
                                else:
                                    actual_dmg = abs(event.value) * 500
                            except:
                                actual_dmg = abs(event.value) * 500
                            PyImGui.text(f"{source} -> {target}: {actual_dmg:.0f}{crit} ({skill})")
                except Exception as e:
                    PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))
                PyImGui.end_child()
            PyImGui.end_tab_item()

        PyImGui.end_tab_bar()

def get_event_type_name(event_type: int) -> str:
    """Convert event type int to readable name"""
    names = {
        EventTypes.SKILL_ACTIVATED: "CAST",
        EventTypes.ATTACK_SKILL_ACTIVATED: "ATK_SKILL",
        EventTypes.SKILL_STOPPED: "STOPPED",
        EventTypes.SKILL_FINISHED: "FINISHED",
        EventTypes.ATTACK_SKILL_FINISHED: "ATK_DONE",
        EventTypes.INTERRUPTED: "INTERRUPT",
        EventTypes.INSTANT_SKILL_ACTIVATED: "INSTANT",
        EventTypes.ATTACK_SKILL_STOPPED: "ATK_STOP",
    }
    return names.get(event_type, f"TYPE_{event_type}")

def draw_damage_tracker_tab():
    """Draw tab for damage tracking"""
    PyImGui.text("Damage Tracker")
    PyImGui.separator()

    try:
        player_id = Player.GetAgentID()
    except:
        player_id = 0

    # Controls
    if not state.damage_tracker_running:
        if PyImGui.button("Start Tracking (Player)"):
            state.damage_track_agent_id = player_id
            state.damage_tracker_running = True
            state.event_log.add("SYSTEM", "Damage tracker started (player only)")
        PyImGui.same_line(0, -1)
        if PyImGui.button("Start Tracking (All)"):
            state.damage_track_agent_id = None
            state.damage_tracker_running = True
            state.event_log.add("SYSTEM", "Damage tracker started (all agents)")
    else:
        if PyImGui.button("Stop Tracking"):
            state.damage_tracker_running = False
            state.event_log.add("SYSTEM", "Damage tracker stopped")
        PyImGui.same_line(0, -1)
        if PyImGui.button("Reset Stats"):
            state.damage_total_dealt = 0.0
            state.damage_total_received = 0.0
            state.damage_dealt_by_skill.clear()
            state.damage_dealt_by_target.clear()
            state.damage_received_by_skill.clear()
            state.damage_received_from_source.clear()
            state.critical_hits = 0

    PyImGui.separator()

    # Display stats
    if PyImGui.begin_child("DamageTrackerChild", (0, 400), True, 0):
        tracking_text = "All Agents" if state.damage_track_agent_id is None else f"Agent {state.damage_track_agent_id}"
        PyImGui.text(f"Tracking: {tracking_text}")
        PyImGui.text(f"Status: {'RUNNING' if state.damage_tracker_running else 'STOPPED'}")
        PyImGui.separator()

        # Show accumulated damage values
        PyImGui.text_colored(f"Total Damage Dealt: {state.damage_total_dealt:.0f}", (255, 200, 100, 255))
        PyImGui.text_colored(f"Total Damage Received: {state.damage_total_received:.0f}", (255, 100, 100, 255))
        PyImGui.text(f"Critical Hits: {state.critical_hits}")

        PyImGui.separator()

        # Damage DEALT breakdown
        if PyImGui.collapsing_header("Damage Dealt by Skill"):
            if state.damage_dealt_by_skill:
                for skill_id, dmg in sorted(state.damage_dealt_by_skill.items(), key=lambda x: -x[1]):
                    skill_name = get_skill_name(skill_id) if skill_id else "Auto-attack"
                    PyImGui.text(f"  {skill_name}: {dmg:.0f}")
            else:
                PyImGui.text("  No damage dealt")

        if PyImGui.collapsing_header("Damage Dealt by Target"):
            if state.damage_dealt_by_target:
                for target_id, dmg in sorted(state.damage_dealt_by_target.items(), key=lambda x: -x[1]):
                    target_name = get_agent_name(target_id)
                    PyImGui.text(f"  {target_name}: {dmg:.0f}")
            else:
                PyImGui.text("  No damage dealt")

        # Damage RECEIVED breakdown
        if PyImGui.collapsing_header("Damage Received by Skill"):
            if state.damage_received_by_skill:
                for skill_id, dmg in sorted(state.damage_received_by_skill.items(), key=lambda x: -x[1]):
                    skill_name = get_skill_name(skill_id) if skill_id else "Auto-attack"
                    PyImGui.text(f"  {skill_name}: {dmg:.0f}")
            else:
                PyImGui.text("  No damage received")

        if PyImGui.collapsing_header("Damage Received from Source"):
            if state.damage_received_from_source:
                for source_id, dmg in sorted(state.damage_received_from_source.items(), key=lambda x: -x[1]):
                    source_name = get_agent_name(source_id)
                    PyImGui.text(f"  {source_name}: {dmg:.0f}")
            else:
                PyImGui.text("  No damage received")

        PyImGui.end_child()

def draw_debug_tab():
    """Draw debug information tab"""
    PyImGui.text("Debug Information")
    PyImGui.separator()

    if PyImGui.begin_child("DebugChild", (0, 300), True, 0):
        PyImGui.text(f"CombatEvents Initialized: {state.combat_events_initialized}")
        PyImGui.text(f"Callbacks Registered: {state.callbacks_registered}")

        if state.combat_events_initialized:
            try:
                PyImGui.text(f"CombatEvents.is_initialized(): {CombatEvents.is_initialized()}")
            except Exception as e:
                PyImGui.text_colored(f"Error checking initialized: {e}", (255, 0, 0, 255))

        PyImGui.separator()
        PyImGui.text("Event Types:")
        PyImGui.text(f"  SKILL_ACTIVATED = {EventTypes.SKILL_ACTIVATED}")
        PyImGui.text(f"  SKILL_FINISHED = {EventTypes.SKILL_FINISHED}")
        PyImGui.text(f"  INTERRUPTED = {EventTypes.INTERRUPTED}")
        PyImGui.text(f"  DISABLED (aftercast) = {EventTypes.DISABLED}")
        PyImGui.text(f"  KNOCKED_DOWN = {EventTypes.KNOCKED_DOWN}")
        PyImGui.text(f"  DAMAGE = {EventTypes.DAMAGE}")
        PyImGui.text(f"  CRITICAL = {EventTypes.CRITICAL}")

        PyImGui.end_child()

def draw_main_window():
    """Draw the main tester window"""
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        # Status bar
        init_color = (100, 255, 100, 255) if state.combat_events_initialized else (255, 100, 100, 255)
        init_text = "INITIALIZED" if state.combat_events_initialized else "NOT INITIALIZED"
        PyImGui.text("CombatEvents: ")
        PyImGui.same_line(0, -1)
        PyImGui.text_colored(init_text, init_color)

        PyImGui.same_line(0, 20)

        cb_color = (100, 255, 100, 255) if state.callbacks_registered else (255, 100, 100, 255)
        cb_text = "ACTIVE" if state.callbacks_registered else "INACTIVE"
        PyImGui.text("Callbacks: ")
        PyImGui.same_line(0, -1)
        PyImGui.text_colored(cb_text, cb_color)

        PyImGui.separator()

        # Main tab bar
        if PyImGui.begin_tab_bar("MainTabBar"):
            if PyImGui.begin_tab_item("Event Log"):
                draw_event_log_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("State Queries"):
                draw_state_queries_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("All Casting"):
                draw_all_casting_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Event History"):
                draw_event_history_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Damage Tracker"):
                draw_damage_tracker_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Debug"):
                draw_debug_tab()
                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

    PyImGui.end()

# ============================================================================
# Main Entry Points
# ============================================================================

def configure():
    """Configure function (called by widget system)"""
    pass

def main():
    """Main function (called every frame by widget system)"""
    if not Routines.Checks.Map.MapValid():
        return

    # Process combat events each frame (IMPORTANT!)
    if state.combat_events_initialized:
        try:
            CombatEvents.update()
        except Exception as e:
            state.event_log.add("ERROR", f"CombatEvents.update() failed: {e}")

    draw_main_window()

if __name__ == "__main__":
    main()
