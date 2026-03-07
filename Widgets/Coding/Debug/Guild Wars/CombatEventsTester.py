"""
CombatEvents Tester - Test and Demo Widget for the Combat Events System
========================================================================

Author: Paul (HamsterSerious)

This widget visualizes CombatEvents data and demonstrates the API.
Use it as a reference for implementing combat tracking in your own bots.

Features:
---------
1. Event Log Tab: Shows real-time combat events as they happen
2. State Queries Tab: Query agent states (casting, attacking, aftercast)
3. Damage Tracker Tab: Track damage dealt/received broken down by skill and target
4. Skill Recharges Tab: Track skill cooldowns for ANY agent (player, enemies, NPCs)
5. Debug Tab: Show event type constants

================================================================================
EXAMPLE CODE PATTERNS - Copy these into your own bots!
================================================================================

1. Query Combat State (Primary API - use this most of the time):
----------------------------------------------------------------
```python
from Py4GWCoreLib import CombatEvents, Player, Skillbar

# Check if you can act (not disabled, not knocked down)
if CombatEvents.can_act(Player.GetAgentID()):
    Skillbar.UseSkill(1)

# Check enemy's cast
if CombatEvents.is_casting(enemy_id):
    skill = CombatEvents.get_casting_skill(enemy_id)
    progress = CombatEvents.get_cast_progress(enemy_id)
    print(f"Enemy casting {skill}, {progress*100:.0f}% done")

# Check who's targeting you
attackers = CombatEvents.get_agents_targeting(Player.GetAgentID())
print(f"{len(attackers)} enemies targeting me!")
```

2. Callbacks (For reactive, frame-perfect timing):
--------------------------------------------------
```python
from Py4GWCoreLib import CombatEvents, Player, Skillbar

# React the instant aftercast ends - frame-perfect skill chaining!
def on_aftercast_done(agent_id):
    if agent_id == Player.GetAgentID():
        Skillbar.UseSkill(next_skill_slot)

CombatEvents.on_aftercast_ended(on_aftercast_done)

# React to skill activations
def on_skill_cast(caster_id, skill_id, target_id):
    if caster_id != Player.GetAgentID():  # Enemy cast
        print(f"Enemy casting skill {skill_id}!")

CombatEvents.on_skill_activated(on_skill_cast)
```

3. Damage Tracking:
-------------------
```python
from Py4GWCoreLib import CombatEvents, Agent

# NOTE: Damage value is a FRACTION of max HP, not absolute damage!
def on_damage(target_id, source_id, damage_fraction, skill_id):
    actual_damage = damage_fraction * Agent.GetMaxHealth(target_id)
    print(f"Dealt {actual_damage:.0f} damage")

CombatEvents.on_damage(on_damage)
```

4. Skill Recharge Tracking (Build Enemy Skillbars!):
----------------------------------------------------
```python
from Py4GWCoreLib import CombatEvents, Skill

# See what skills an enemy has used
observed = CombatEvents.get_observed_skills(enemy_id)
print(f"Enemy has used {len(observed)} different skills")

# Check if a specific skill is on cooldown
if CombatEvents.is_skill_recharging(enemy_id, dangerous_skill_id):
    remaining = CombatEvents.get_skill_recharge_remaining(enemy_id, dangerous_skill_id)
    # Check if it's an estimate (enemies) or actual server data (player/heroes)
    is_estimated = CombatEvents.is_recharge_estimated(enemy_id, dangerous_skill_id)
    if is_estimated:
        print(f"Skill on cooldown for ~{remaining}ms (estimated, no modifiers)")
    else:
        print(f"Skill on cooldown for {remaining}ms (exact)")

# React to skill recharges with callbacks
def on_skill_ready(agent_id, skill_id):
    print(f"Agent {agent_id}'s {Skill.GetName(skill_id)} is ready!")

CombatEvents.on_skill_recharged(on_skill_ready)

# NOTE: Enemy recharges are ESTIMATED from base skill data.
# They don't account for Fast Casting, Serpent's Quickness, etc.
# Player/hero recharges use actual server data.
```

5. Stance Detection:
--------------------
```python
from Py4GWCoreLib import CombatEvents, Skill

if CombatEvents.has_stance(enemy_id):
    stance_id = CombatEvents.get_stance(enemy_id)
    remaining = CombatEvents.get_stance_remaining(enemy_id)
    print(f"Enemy has {Skill.GetName(stance_id)} for {remaining}ms")
```

See Also:
---------
- CombatEvents.py: Main module with full API documentation
- CombatEvents_Guide.md: Beginner-friendly guide with more examples
- py_combat_events.h/.cpp: C++ packet handling (for advanced users)
"""

from Py4GWCoreLib import *
from Py4GWCoreLib.CombatEvents import CombatEvents, EventType
from typing import List, Optional
import time

MODULE_NAME = "CombatEvents Tester"
MODULE_ICON = "Textures/Module_Icons/Combat.png"

# ============================================================================
# State tracking for the UI
# ============================================================================

class EventLog:
    """Stores recent events for display in the UI."""
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
    """Global state for the tester widget."""
    def __init__(self):
        # Event logging
        self.event_log = EventLog()
        self.callbacks_registered = False

        # Filters
        self.show_skill_events = True
        self.show_damage_events = True
        self.show_attack_events = True
        self.show_knockdown_events = True
        self.show_aftercast_events = True
        self.show_recharge_events = True

        # Filter by agent
        self.filter_player_only = False

        # Damage tracker state
        self.damage_tracker_running = False
        self.damage_total_dealt: float = 0.0
        self.damage_total_received: float = 0.0
        self.damage_dealt_by_skill: dict = {}
        self.damage_dealt_by_target: dict = {}
        self.damage_received_by_skill: dict = {}
        self.damage_received_from_source: dict = {}
        self.critical_hits: int = 0
        self.damage_track_agent_id: Optional[int] = None

        # Selected agent for state queries
        self.selected_agent_id = 0


state = TesterState()

# ============================================================================
# Helper Functions
# ============================================================================

def get_agent_name(agent_id: int) -> str:
    """Get agent name or ID string."""
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
    """Get skill name or ID string."""
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
    """Check if we should log events for this agent."""
    if not state.filter_player_only:
        return True
    try:
        return agent_id == Player.GetAgentID()
    except:
        return True


def get_event_type_name(event_type: int) -> str:
    """Convert event type int to readable name."""
    names = {
        EventType.SKILL_ACTIVATED: "CAST",
        EventType.ATTACK_SKILL_ACTIVATED: "ATK_SKILL",
        EventType.SKILL_STOPPED: "STOPPED",
        EventType.SKILL_FINISHED: "FINISHED",
        EventType.ATTACK_SKILL_FINISHED: "ATK_DONE",
        EventType.INTERRUPTED: "INTERRUPT",
        EventType.INSTANT_SKILL_ACTIVATED: "INSTANT",
        EventType.ATTACK_SKILL_STOPPED: "ATK_STOP",
    }
    return names.get(event_type, f"TYPE_{event_type}")


# ============================================================================
# Event Callbacks - These demonstrate how to use the callback API
# ============================================================================

def on_skill_activated(caster_id: int, skill_id: int, target_id: int):
    """Called when any agent starts casting a skill."""
    if state.show_skill_events and should_log_agent(caster_id):
        caster = get_agent_name(caster_id)
        skill = get_skill_name(skill_id)
        target = get_agent_name(target_id) if target_id else "self"
        state.event_log.add("SKILL", f"{caster} casting {skill} -> {target}")


def on_skill_finished(agent_id: int, skill_id: int):
    """Called when a skill cast completes successfully."""
    if state.show_skill_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        skill = get_skill_name(skill_id)
        state.event_log.add("SKILL", f"{agent} FINISHED {skill}")


def on_skill_interrupted(agent_id: int, skill_id: int):
    """Called when a skill cast is interrupted."""
    if state.show_skill_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        skill = get_skill_name(skill_id)
        state.event_log.add("SKILL", f"{agent} INTERRUPTED {skill}")


def on_attack_started(attacker_id: int, target_id: int):
    """Called when an agent starts auto-attacking."""
    if state.show_attack_events and should_log_agent(attacker_id):
        attacker = get_agent_name(attacker_id)
        target = get_agent_name(target_id)
        state.event_log.add("ATTACK", f"{attacker} attack -> {target}")


def on_aftercast_ended(agent_id: int):
    """
    Called when an agent can act again after aftercast.

    THIS IS THE KEY CALLBACK FOR SKILL CHAINING!
    Register this to get frame-perfect skill usage timing.
    """
    if state.show_aftercast_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        state.event_log.add("STATE", f"{agent} CAN ACT")


def on_knockdown(agent_id: int, duration: float):
    """Called when an agent is knocked down."""
    if state.show_knockdown_events and should_log_agent(agent_id):
        agent = get_agent_name(agent_id)
        state.event_log.add("KD", f"{agent} knocked down for {duration:.2f}s")


def on_damage(target_id: int, source_id: int, damage_fraction: float, skill_id: int):
    """
    Called when damage is dealt.

    NOTE: damage_fraction is a FRACTION of max HP (e.g., 0.05 = 5% of max HP).
    To get actual damage: actual_dmg = damage_fraction * Agent.GetMaxHealth(target_id)
    """
    # Calculate actual damage
    actual_dmg = 0.0
    try:
        max_hp = Agent.GetMaxHealth(target_id)
        if max_hp > 0:
            actual_dmg = abs(damage_fraction) * max_hp
    except:
        actual_dmg = abs(damage_fraction) * 500  # Fallback estimate

    # Log to event log
    if state.show_damage_events and (should_log_agent(source_id) or should_log_agent(target_id)):
        source = get_agent_name(source_id)
        target = get_agent_name(target_id)
        if skill_id:
            skill = get_skill_name(skill_id)
            state.event_log.add("DMG", f"{source} -> {target}: {actual_dmg:.0f} dmg ({skill})")
        else:
            state.event_log.add("DMG", f"{source} -> {target}: {actual_dmg:.0f} dmg (auto-attack)")

    # Track damage for statistics
    if state.damage_tracker_running:
        # Track damage dealt
        if state.damage_track_agent_id is None or source_id == state.damage_track_agent_id:
            state.damage_total_dealt += actual_dmg
            state.damage_dealt_by_skill[skill_id] = state.damage_dealt_by_skill.get(skill_id, 0) + actual_dmg
            state.damage_dealt_by_target[target_id] = state.damage_dealt_by_target.get(target_id, 0) + actual_dmg
        # Track damage received
        if state.damage_track_agent_id is None or target_id == state.damage_track_agent_id:
            state.damage_total_received += actual_dmg
            state.damage_received_by_skill[skill_id] = state.damage_received_by_skill.get(skill_id, 0) + actual_dmg
            state.damage_received_from_source[source_id] = state.damage_received_from_source.get(source_id, 0) + actual_dmg


def on_skill_recharge_started(agent_id: int, skill_id: int, recharge_ms: int):
    """Called when a skill goes on cooldown."""
    if state.show_recharge_events:
        agent = get_agent_name(agent_id)
        skill = get_skill_name(skill_id)
        # Check if this is an estimated recharge
        is_estimated = CombatEvents.is_recharge_estimated(agent_id, skill_id)
        if is_estimated:
            state.event_log.add("RECHARGE", f"{agent} {skill} on cooldown (~{recharge_ms/1000:.1f}s estimated)")
        else:
            state.event_log.add("RECHARGE", f"{agent} {skill} on cooldown ({recharge_ms/1000:.1f}s)")


def on_skill_recharged(agent_id: int, skill_id: int):
    """Called when a skill comes off cooldown."""
    if state.show_recharge_events:
        agent = get_agent_name(agent_id)
        skill = get_skill_name(skill_id)
        state.event_log.add("READY", f"{agent} {skill} READY")


# ============================================================================
# Callback Registration
# ============================================================================

def register_callbacks():
    """
    Register all event callbacks.

    This demonstrates the callback API. In your own code, you only need
    to register the callbacks you actually want to use.
    """
    if state.callbacks_registered:
        return

    try:
        # Skill events
        CombatEvents.on_skill_activated(on_skill_activated)
        CombatEvents.on_skill_finished(on_skill_finished)
        CombatEvents.on_skill_interrupted(on_skill_interrupted)

        # Attack events
        CombatEvents.on_attack_started(on_attack_started)

        # State events - THIS IS THE KEY ONE FOR SKILL CHAINING!
        CombatEvents.on_aftercast_ended(on_aftercast_ended)

        # Knockdown events
        CombatEvents.on_knockdown(on_knockdown)

        # Damage events
        CombatEvents.on_damage(on_damage)

        # Skill recharge tracking
        CombatEvents.on_skill_recharge_started(on_skill_recharge_started)
        CombatEvents.on_skill_recharged(on_skill_recharged)

        state.callbacks_registered = True
        state.event_log.add("SYSTEM", "Callbacks registered successfully")
    except Exception as e:
        state.event_log.add("ERROR", f"Failed to register callbacks: {e}")


def unregister_callbacks():
    """Clear all callbacks."""
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
    """Get color for event type."""
    colors = {
        "SKILL": (100, 200, 255, 255),     # Light blue
        "ATTACK": (255, 150, 100, 255),    # Orange
        "STATE": (200, 255, 100, 255),     # Yellow-green
        "KD": (255, 100, 100, 255),        # Red
        "DMG": (255, 200, 100, 255),       # Gold
        "CRIT": (255, 50, 50, 255),        # Bright red
        "RECHARGE": (180, 130, 255, 255),  # Light purple
        "READY": (100, 255, 150, 255),     # Light green
        "SYSTEM": (150, 150, 150, 255),    # Gray
        "ERROR": (255, 0, 0, 255),         # Red
    }
    return colors.get(event_type, (255, 255, 255, 255))


def draw_event_log_tab():
    """Draw the event log tab - shows real-time events from callbacks."""
    # Status display
    try:
        import PyCombatEvents
        queue = PyCombatEvents.GetCombatEventQueue()
        is_init = queue.IsInitialized()
        raw_events = CombatEvents.get_events()

        if is_init:
            PyImGui.text_colored(f"Combat Events: ACTIVE ({len(raw_events)} events captured)", (100, 255, 100, 255))
        else:
            PyImGui.text_colored("Combat Events: NOT INITIALIZED", (255, 100, 100, 255))
            if PyImGui.button("Initialize"):
                queue.Initialize()
                state.event_log.add("SYSTEM", "C++ hooks initialized")
    except Exception as e:
        PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))

    PyImGui.separator()
    PyImGui.text("Event Filters:")

    # Filter checkboxes
    state.show_skill_events = PyImGui.checkbox("Skills", state.show_skill_events)
    PyImGui.same_line(0, -1)
    state.show_damage_events = PyImGui.checkbox("Damage", state.show_damage_events)
    PyImGui.same_line(0, -1)
    state.show_attack_events = PyImGui.checkbox("Attacks", state.show_attack_events)
    PyImGui.same_line(0, -1)
    state.show_aftercast_events = PyImGui.checkbox("Aftercast", state.show_aftercast_events)

    state.show_knockdown_events = PyImGui.checkbox("Knockdown", state.show_knockdown_events)
    PyImGui.same_line(0, -1)
    state.show_recharge_events = PyImGui.checkbox("Recharge", state.show_recharge_events)
    PyImGui.same_line(0, -1)
    state.filter_player_only = PyImGui.checkbox("Player Only", state.filter_player_only)

    PyImGui.separator()

    # Control buttons
    if not state.callbacks_registered:
        if PyImGui.button("Register Callbacks"):
            register_callbacks()
    else:
        PyImGui.text_colored("Callbacks: ACTIVE", (100, 255, 100, 255))
        PyImGui.same_line(0, -1)
        if PyImGui.button("Unregister"):
            unregister_callbacks()

    PyImGui.same_line(0, -1)
    if PyImGui.button("Clear Log"):
        state.event_log.clear()

    PyImGui.separator()

    # Event log display
    if PyImGui.begin_child("EventLogChild", size=(0, 300), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
        for timestamp, event_type, message in state.event_log.get_recent(50):
            color = get_event_color(event_type)
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            PyImGui.text_colored(f"[{time_str}] [{event_type:8}] {message}", color)
        PyImGui.end_child()


def draw_state_queries_tab():
    """
    Draw the state queries tab - demonstrates querying combat state.

    This shows how to use the query API to check agent states.
    """
    try:
        player_id = Player.GetAgentID()
    except:
        player_id = 0

    try:
        target_id = Player.GetTargetID()
    except:
        target_id = 0

    # Auto-select player on first load
    if state.selected_agent_id == 0 and player_id > 0:
        state.selected_agent_id = player_id

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

    agent_id = state.selected_agent_id if state.selected_agent_id > 0 else player_id
    agent_name = get_agent_name(agent_id)

    PyImGui.separator()
    PyImGui.text(f"Querying: {agent_name} (ID: {agent_id})")
    PyImGui.separator()

    # Show warning if no valid agent
    if agent_id <= 0:
        PyImGui.text_colored("No valid agent selected. Click 'Player' or enter an agent ID.", (255, 200, 100, 255))
        return

    if PyImGui.begin_child("StateQueriesChild", (0, 350), True, 0):
        try:
            # === CASTING STATE ===
            if PyImGui.collapsing_header("Casting State", PyImGui.TreeNodeFlags.DefaultOpen):
                is_casting = CombatEvents.is_casting(agent_id)
                PyImGui.text(f"is_casting(): {is_casting}")

                if is_casting:
                    skill_id = CombatEvents.get_casting_skill(agent_id)
                    target = CombatEvents.get_cast_target(agent_id)
                    progress = CombatEvents.get_cast_progress(agent_id)
                    remaining = CombatEvents.get_cast_time_remaining(agent_id)

                    PyImGui.text(f"  get_casting_skill(): {get_skill_name(skill_id)} ({skill_id})")
                    PyImGui.text(f"  get_cast_target(): {get_agent_name(target) if target else 'none'}")
                    if progress >= 0:
                        PyImGui.text(f"  get_cast_progress(): {progress*100:.1f}%")
                        PyImGui.text(f"  get_cast_time_remaining(): {remaining}ms")
                        PyImGui.progress_bar(progress, 200.0, 0.0, "")

            # === ATTACK STATE ===
            if PyImGui.collapsing_header("Attack State", PyImGui.TreeNodeFlags.DefaultOpen):
                is_attacking = CombatEvents.is_attacking(agent_id)
                PyImGui.text(f"is_attacking(): {is_attacking}")

                if is_attacking:
                    attack_target = CombatEvents.get_attack_target(agent_id)
                    PyImGui.text(f"  get_attack_target(): {get_agent_name(attack_target)}")

            # === ACTION STATE (Most Important!) ===
            if PyImGui.collapsing_header("Action State (IMPORTANT)", PyImGui.TreeNodeFlags.DefaultOpen):
                can_act = CombatEvents.can_act(agent_id)
                is_disabled = CombatEvents.is_disabled(agent_id)

                PyImGui.text(f"can_act(): {can_act}")
                PyImGui.text(f"is_disabled(): {is_disabled}")

                if can_act:
                    PyImGui.text_colored("  --> AGENT CAN USE SKILLS NOW!", (100, 255, 100, 255))
                else:
                    PyImGui.text_colored("  --> Agent cannot act", (255, 100, 100, 255))

            # === KNOCKDOWN STATE ===
            if PyImGui.collapsing_header("Knockdown State", PyImGui.TreeNodeFlags.DefaultOpen):
                is_kd = CombatEvents.is_knocked_down(agent_id)
                PyImGui.text(f"is_knocked_down(): {is_kd}")

                if is_kd:
                    kd_remaining = CombatEvents.get_knockdown_remaining(agent_id)
                    PyImGui.text(f"  get_knockdown_remaining(): {kd_remaining}ms")

            # === STANCE STATE ===
            if PyImGui.collapsing_header("Stance State (Estimated)", PyImGui.TreeNodeFlags.DefaultOpen):
                has_stance = CombatEvents.has_stance(agent_id)
                PyImGui.text(f"has_stance(): {has_stance}")

                if has_stance:
                    stance_id = CombatEvents.get_stance(agent_id)
                    stance_remaining = CombatEvents.get_stance_remaining(agent_id)
                    if stance_id:
                        PyImGui.text(f"  get_stance(): {get_skill_name(stance_id)}")
                        PyImGui.text(f"  get_stance_remaining(): {stance_remaining}ms")

            # === TARGETING INFO ===
            if PyImGui.collapsing_header("Targeting Info"):
                agents_targeting = CombatEvents.get_agents_targeting(agent_id)
                PyImGui.text(f"get_agents_targeting(): {len(agents_targeting)} agents")
                if agents_targeting:
                    for aid in agents_targeting[:5]:
                        PyImGui.text(f"    - {get_agent_name(aid)}")

        except Exception as e:
            PyImGui.text_colored(f"Error querying state: {e}", (255, 0, 0, 255))

        PyImGui.end_child()


def draw_damage_tracker_tab():
    """Draw tab for damage tracking - demonstrates damage callback usage."""
    PyImGui.text("Damage Tracker")
    PyImGui.text_colored("Uses on_damage() callback to track all damage", (150, 150, 150, 255))
    PyImGui.separator()

    # Show warning if callbacks not registered
    if not state.callbacks_registered:
        PyImGui.text_colored("Note: Register callbacks in Event Log tab for damage tracking to work!", (255, 200, 100, 255))
        if PyImGui.button("Register Callbacks Now"):
            register_callbacks()
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
            # Auto-register callbacks if not already done
            if not state.callbacks_registered:
                register_callbacks()
            state.event_log.add("SYSTEM", "Damage tracker started (player only)")
        PyImGui.same_line(0, -1)
        if PyImGui.button("Start Tracking (All)"):
            state.damage_track_agent_id = None
            state.damage_tracker_running = True
            # Auto-register callbacks if not already done
            if not state.callbacks_registered:
                register_callbacks()
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

        PyImGui.text_colored(f"Total Damage Dealt: {state.damage_total_dealt:.0f}", (255, 200, 100, 255))
        PyImGui.text_colored(f"Total Damage Received: {state.damage_total_received:.0f}", (255, 100, 100, 255))

        PyImGui.separator()

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

        PyImGui.end_child()


def draw_skill_recharges_tab():
    """Draw tab showing skill recharge tracking for any agent."""
    PyImGui.text("Skill Recharge Tracking")
    PyImGui.text_colored("Track skill cooldowns for ANY agent (player, enemies, NPCs)", (150, 150, 150, 255))
    PyImGui.separator()

    # Show warning if callbacks not registered (needed for SKILL_RECHARGE events)
    if not state.callbacks_registered:
        PyImGui.text_colored("Note: Register callbacks for skill recharge tracking to work!", (255, 200, 100, 255))
        if PyImGui.button("Register Callbacks##recharge"):
            register_callbacks()
        PyImGui.separator()

    try:
        player_id = Player.GetAgentID()
    except:
        player_id = 0

    try:
        target_id = Player.GetTargetID()
    except:
        target_id = 0

    # Auto-select player on first load
    if state.selected_agent_id == 0 and player_id > 0:
        state.selected_agent_id = player_id

    # Agent selector
    PyImGui.text("View Recharges For:")
    PyImGui.same_line(0, -1)
    if PyImGui.button("Player##recharge"):
        state.selected_agent_id = player_id
    PyImGui.same_line(0, -1)
    if PyImGui.button("Target##recharge"):
        state.selected_agent_id = target_id if target_id else player_id

    agent_id = state.selected_agent_id if state.selected_agent_id > 0 else player_id
    agent_name = get_agent_name(agent_id)

    PyImGui.separator()

    if PyImGui.begin_child("SkillRechargesChild", (0, 400), True, 0):
        # Debug: Show current tick count
        try:
            import ctypes
            current_tick = ctypes.windll.kernel32.GetTickCount()
            PyImGui.text_colored(f"Current tick: {current_tick}", (150, 150, 150, 255))
        except:
            pass

        # Show info about estimated recharges
        PyImGui.text_colored("(~) = Estimated from base skill data, no modifiers applied", (255, 200, 100, 255))
        PyImGui.separator()

        # Show observed skills
        if PyImGui.collapsing_header(f"Observed Skills - {agent_name}", PyImGui.TreeNodeFlags.DefaultOpen):
            try:
                observed = CombatEvents.get_observed_skills(agent_id)
                if not observed:
                    PyImGui.text("  No skills observed yet")
                    PyImGui.text_colored("  (Skills appear when the agent uses them)", (150, 150, 150, 255))
                else:
                    PyImGui.text(f"  Seen {len(observed)} different skills:")
                    for skill_id in sorted(observed):
                        skill_name = get_skill_name(skill_id)
                        if CombatEvents.is_skill_recharging(agent_id, skill_id):
                            remaining = CombatEvents.get_skill_recharge_remaining(agent_id, skill_id)
                            is_estimated = CombatEvents.is_recharge_estimated(agent_id, skill_id)
                            if is_estimated:
                                # Yellow for estimated recharges
                                PyImGui.text_colored(f"    {skill_name}: ~{remaining/1000:.1f}s remaining (estimated)", (255, 200, 100, 255))
                            else:
                                # Purple for actual server data
                                PyImGui.text_colored(f"    {skill_name}: {remaining/1000:.1f}s remaining", (180, 130, 255, 255))
                        else:
                            PyImGui.text_colored(f"    {skill_name}: READY", (100, 255, 150, 255))
            except Exception as e:
                PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))

        # Show currently recharging
        if PyImGui.collapsing_header(f"Currently Recharging - {agent_name}", PyImGui.TreeNodeFlags.DefaultOpen):
            try:
                recharging = CombatEvents.get_recharging_skills(agent_id)
                if not recharging:
                    PyImGui.text("  No skills on cooldown")
                else:
                    for skill_id, remaining_ms, is_estimated in recharging:
                        skill_name = get_skill_name(skill_id)
                        if is_estimated:
                            PyImGui.text_colored(
                                f"    {skill_name}: ~{remaining_ms/1000:.1f}s (estimated)",
                                (255, 200, 100, 255),
                            )
                        else:
                            PyImGui.text(f"    {skill_name}: {remaining_ms/1000:.1f}s")
            except Exception as e:
                PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))

        # Debug: Show raw recharge data
        if PyImGui.collapsing_header("Debug: Raw Recharge Data"):
            try:
                from Py4GWCoreLib.CombatEvents import _recharges, _tracked_agents
                import ctypes
                now = ctypes.windll.kernel32.GetTickCount()

                # Show tracked agents (those that receive actual recharge packets)
                PyImGui.text(f"  Tracked agents (server data): {list(_tracked_agents)}")

                if agent_id in _recharges:
                    for sid, data in _recharges[agent_id].items():
                        skill_name = get_skill_name(sid)
                        if len(data) == 4:
                            start, dur, end, is_est = data
                        else:
                            start, dur, end = data
                            is_est = False
                        time_left = end - now
                        est_marker = " (EST)" if is_est else ""
                        PyImGui.text(f"  {skill_name}{est_marker}: start={start}, dur={dur}, end={end}")
                        PyImGui.text(f"    now={now}, time_left={time_left}ms")
                else:
                    PyImGui.text("  No recharge data for this agent")
            except Exception as e:
                PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))

        # Utility buttons
        PyImGui.separator()
        if PyImGui.button("Clear Recharge Data"):
            try:
                CombatEvents.clear_recharge_data(agent_id)
                state.event_log.add("SYSTEM", f"Cleared recharge data for {agent_name}")
            except Exception as e:
                state.event_log.add("ERROR", f"Failed to clear recharge data: {e}")

        PyImGui.end_child()


def draw_event_history_tab():
    """Draw tab showing raw event history from CombatEvents."""
    PyImGui.text("Recent Events from CombatEvents")
    PyImGui.text_colored("Raw event data - for debugging and advanced use", (150, 150, 150, 255))
    PyImGui.separator()

    if PyImGui.begin_tab_bar("HistoryTabs"):
        # Skill events
        if PyImGui.begin_tab_item("Skill Events"):
            if PyImGui.begin_child("SkillHistoryChild", size=(0, 300), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
                try:
                    events = CombatEvents.get_recent_skills(count=20)
                    if not events:
                        PyImGui.text("No recent skill events")
                    else:
                        for ts, caster_id, skill_id, target_id, event_type in events:
                            caster = get_agent_name(caster_id)
                            skill = get_skill_name(skill_id)
                            target = get_agent_name(target_id) if target_id else "-"
                            event_name = get_event_type_name(event_type)
                            PyImGui.text(f"[{event_name}] {caster} | {skill} | -> {target}")
                except Exception as e:
                    PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))
                PyImGui.end_child()
            PyImGui.end_tab_item()

        # Damage events
        if PyImGui.begin_tab_item("Damage Events"):
            if PyImGui.begin_child("DamageHistoryChild", size=(0, 300), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
                try:
                    events = CombatEvents.get_recent_damage(count=20)
                    if not events:
                        PyImGui.text("No recent damage events")
                    else:
                        for ts, target_id, source_id, damage_frac, skill_id, is_crit in events:
                            source = get_agent_name(source_id)
                            target = get_agent_name(target_id)
                            skill = get_skill_name(skill_id) if skill_id else "auto"
                            crit = " CRIT" if is_crit else ""
                            # Calculate actual damage
                            try:
                                max_hp = Agent.GetMaxHealth(target_id)
                                actual_dmg = abs(damage_frac) * max_hp if max_hp > 0 else abs(damage_frac) * 500
                            except:
                                actual_dmg = abs(damage_frac) * 500
                            PyImGui.text(f"{source} -> {target}: {actual_dmg:.0f}{crit} ({skill})")
                except Exception as e:
                    PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))
                PyImGui.end_child()
            PyImGui.end_tab_item()

        PyImGui.end_tab_bar()


def draw_debug_tab():
    """Draw debug information tab - shows event type constants."""
    PyImGui.text("Debug Information")
    PyImGui.separator()

    if PyImGui.begin_child("DebugChild", (0, 550), True, 0):
        PyImGui.text(f"Callbacks Registered: {state.callbacks_registered}")

        # Show event type distribution in buffer
        if PyImGui.collapsing_header("Event Type Distribution (ALL events)", PyImGui.TreeNodeFlags.DefaultOpen):
            try:
                all_events = CombatEvents.get_events()
                PyImGui.text(f"  Total events in buffer: {len(all_events)}")

                if all_events:
                    # Count by event type
                    type_counts = {}
                    for _, etype, _, _, _, _ in all_events:
                        type_counts[etype] = type_counts.get(etype, 0) + 1

                    # Map event type IDs to names
                    type_names = {
                        1: "SKILL_ACTIVATED", 2: "ATTACK_SKILL_ACTIVATED", 3: "SKILL_STOPPED",
                        4: "SKILL_FINISHED", 5: "ATTACK_SKILL_FINISHED", 6: "INTERRUPTED",
                        7: "INSTANT_SKILL", 8: "ATTACK_SKILL_STOPPED",
                        13: "ATTACK_STARTED", 14: "ATTACK_STOPPED", 15: "MELEE_FINISHED",
                        16: "DISABLED", 17: "KNOCKED_DOWN", 18: "CASTTIME",
                        30: "DAMAGE", 31: "CRITICAL", 32: "ARMOR_IGNORING",
                        40: "EFFECT_APPLIED", 41: "EFFECT_REMOVED", 42: "EFFECT_ON_TARGET",
                        50: "ENERGY_GAINED", 51: "ENERGY_SPENT",
                        60: "SKILL_DAMAGE", 70: "SKILL_ACTIVATE_PACKET",
                        80: "SKILL_RECHARGE", 81: "SKILL_RECHARGED"
                    }

                    PyImGui.text("  Event types captured:")
                    for etype, count in sorted(type_counts.items()):
                        name = type_names.get(etype, f"UNKNOWN_{etype}")
                        PyImGui.text(f"    {name} ({etype}): {count}")
                else:
                    PyImGui.text_colored("  No events captured yet!", (255, 200, 100, 255))
                    PyImGui.text("  Make sure you're in an explorable area and using skills.")
            except Exception as e:
                PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))

        # Show raw SKILL_RECHARGE events from the event buffer
        if PyImGui.collapsing_header("Raw SKILL_RECHARGE Events", PyImGui.TreeNodeFlags.DefaultOpen):
            try:
                all_events = CombatEvents.get_events()
                recharge_events = [(ts, etype, agent, val, target, fval)
                                   for ts, etype, agent, val, target, fval in all_events
                                   if etype == EventType.SKILL_RECHARGE or etype == EventType.SKILL_RECHARGED]
                if not recharge_events:
                    PyImGui.text("  No SKILL_RECHARGE events in buffer")
                else:
                    PyImGui.text(f"  Found {len(recharge_events)} recharge events:")
                    import ctypes
                    now = ctypes.windll.kernel32.GetTickCount()
                    for ts, etype, agent, val, _, fval in recharge_events[-10:]:  # Show last 10
                        etype_name = "RECHARGE" if etype == EventType.SKILL_RECHARGE else "RECHARGED"
                        skill_name = get_skill_name(val)
                        agent_name = get_agent_name(agent)
                        # Show raw values for debugging
                        PyImGui.text(f"    [{etype_name}] {agent_name}: {skill_name}")
                        PyImGui.text(f"      ts={ts}, fval={fval}, now={now}, age={now-ts}ms")
            except Exception as e:
                PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))

        # Show raw DAMAGE events
        if PyImGui.collapsing_header("Raw DAMAGE Events"):
            try:
                all_events = CombatEvents.get_events()
                damage_events = [(ts, etype, agent, val, target, fval)
                                 for ts, etype, agent, val, target, fval in all_events
                                 if etype in (EventType.DAMAGE, EventType.CRITICAL, EventType.ARMOR_IGNORING)]
                if not damage_events:
                    PyImGui.text("  No DAMAGE events in buffer")
                else:
                    PyImGui.text(f"  Found {len(damage_events)} damage events:")
                    for _, etype, agent, val, target, fval in damage_events[-10:]:
                        etype_name = {30: "DAMAGE", 31: "CRITICAL", 32: "ARMOR_IGN"}.get(etype, "?")
                        PyImGui.text(f"    [{etype_name}] target={agent} source={target} dmg={fval:.4f}")
            except Exception as e:
                PyImGui.text_colored(f"Error: {e}", (255, 0, 0, 255))

        PyImGui.separator()
        PyImGui.text("Event Type Constants (from EventType class):")

        if PyImGui.collapsing_header("Skill Events"):
            PyImGui.text(f"  SKILL_ACTIVATED = {EventType.SKILL_ACTIVATED}")
            PyImGui.text(f"  SKILL_FINISHED = {EventType.SKILL_FINISHED}")
            PyImGui.text(f"  INTERRUPTED = {EventType.INTERRUPTED}")
            PyImGui.text(f"  INSTANT_SKILL_ACTIVATED = {EventType.INSTANT_SKILL_ACTIVATED}")
            PyImGui.text(f"  ATTACK_SKILL_ACTIVATED = {EventType.ATTACK_SKILL_ACTIVATED}")

        if PyImGui.collapsing_header("Combat Events"):
            PyImGui.text(f"  ATTACK_STARTED = {EventType.ATTACK_STARTED}")
            PyImGui.text(f"  ATTACK_STOPPED = {EventType.ATTACK_STOPPED}")
            PyImGui.text(f"  DAMAGE = {EventType.DAMAGE}")
            PyImGui.text(f"  CRITICAL = {EventType.CRITICAL}")

        if PyImGui.collapsing_header("State Events"):
            PyImGui.text(f"  DISABLED = {EventType.DISABLED}")
            PyImGui.text(f"  KNOCKED_DOWN = {EventType.KNOCKED_DOWN}")

        if PyImGui.collapsing_header("Skill Recharge Events"):
            PyImGui.text(f"  SKILL_RECHARGE = {EventType.SKILL_RECHARGE}")
            PyImGui.text(f"  SKILL_RECHARGED = {EventType.SKILL_RECHARGED}")

        PyImGui.end_child()


def draw_main_window():
    """Draw the main tester window."""
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        # Status bar
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

            if PyImGui.begin_tab_item("Event History"):
                draw_event_history_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Damage Tracker"):
                draw_damage_tracker_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Skill Recharges"):
                draw_skill_recharges_tab()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Debug"):
                draw_debug_tab()
                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

        PyImGui.separator()
        PyImGui.text_colored("by Paul (HSTools)", (150, 150, 150, 255))

    PyImGui.end()


# ============================================================================
# Main Entry Points
# ============================================================================

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Combat Events Tester", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An advanced visualization and debugging tool for the Combat Events system.")
    PyImGui.text("It monitors real-time combat data, including skill casting, damage")
    PyImGui.text("tracking, and agent state transitions for players and NPCs.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Event Log: Live feed of combat actions (Damage, Heals, Skill start/end)")
    PyImGui.bullet_text("Damage Tracker: Detailed breakdown of DPS/HPS by skill and target")
    PyImGui.bullet_text("State Queries: Real-time inspection of Casting, Attacking, and Aftercast states")
    PyImGui.bullet_text("Skill Recharges: Global tracking of skill cooldowns for any agent in range")
    PyImGui.bullet_text("API Reference: Demonstrates standard patterns for implementing combat logic")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by HamsterSerious")

    PyImGui.end_tooltip()


def main():
    """Main function (called every frame by widget system)."""
    if not Routines.Checks.Map.MapValid():
        return

    # Ensure CombatEvents.update() is called every frame
    # (It should be auto-registered, but call it explicitly as backup)
    try:
        CombatEvents.update()
    except Exception:
        pass  # Silently ignore if already updating

    draw_main_window()


if __name__ == "__main__":
    main()
