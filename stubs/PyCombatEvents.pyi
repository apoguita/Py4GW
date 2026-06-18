"""
Combat Events - Real-time combat state tracking for Guild Wars.

This module provides a clean Python API for querying combat state and reacting
to combat events. Data is captured from game packets and processed into
easy-to-use state queries and optional callbacks.

Usage:
    from Py4GWCoreLib import CombatEvents

    # Check if you can use a skill
    if CombatEvents.can_act(player_id):
        Skillbar.UseSkill(1)

    # Register a callback for frame-perfect skill chaining
    def on_ready(agent_id):
        if agent_id == player_id:
            use_next_skill()
    CombatEvents.on_aftercast_ended(on_ready)
"""

from __future__ import annotations
from typing import List, Set, Tuple, Optional, Callable


class EventType:
    """
    Combat event type constants.

    Use these to identify event types when processing raw events:
        for ts, etype, agent, val, target, fval in CombatEvents.get_events():
            if etype == EventType.SKILL_ACTIVATED:
                print(f"Agent {agent} casting skill {val}")
    """
    # Skill Events
    SKILL_ACTIVATED: int = 1          # Non-attack skill started
    ATTACK_SKILL_ACTIVATED: int = 2   # Attack skill started
    SKILL_STOPPED: int = 3            # Skill cancelled
    SKILL_FINISHED: int = 4           # Skill completed
    ATTACK_SKILL_FINISHED: int = 5    # Attack skill completed
    INTERRUPTED: int = 6              # Skill interrupted
    INSTANT_SKILL_ACTIVATED: int = 7  # Instant skill (no cast time)
    ATTACK_SKILL_STOPPED: int = 8     # Attack skill cancelled

    # Attack Events (auto-attacks)
    ATTACK_STARTED: int  = 13         # Auto-attack started
    ATTACK_STOPPED: int = 14          # Auto-attack stopped
    MELEE_ATTACK_FINISHED: int = 15   # Melee hit completed

    # State Events
    DISABLED: int  = 16               # Disabled state changed (val=1 disabled, val=0 can act)
    KNOCKED_DOWN: int = 17             # Knockdown (fval=duration_seconds)
    CASTTIME: int = 18                 # Cast time info (fval=duration_seconds)

    # Damage Events (NOTE: agent_id=TARGET, target_id=SOURCE)
    DAMAGE: int  = 30                 # Normal damage (fval=damage_fraction)
    CRITICAL: int = 31                # Critical hit (fval=damage_fraction)
    ARMOR_IGNORING: int = 32          # Armor-ignoring damage (can be negative for heals)
    HEALING: int = 33                  # Healing/lifesteal gain (fval=heal_fraction)

    # Effect Events
    EFFECT_APPLIED: int = 40           # Visual effect applied
    EFFECT_REMOVED: int = 41           # Visual effect removed
    EFFECT_ON_TARGET: int = 42         # Skill effect hit target
    EFFECT_RENEWED: int = 43           # Existing effect reapplied before removal

    # Energy Events
    ENERGY_GAINED: int = 50            # Energy gained
    ENERGY_SPENT: int = 51             # Energy spent

    # Misc
    SKILL_DAMAGE: int = 60             # Pre-damage notification
    SKILL_ACTIVATE_PACKET: int = 70    # Early skill notification

    # Skill Recharge Events
    SKILL_RECHARGE: int = 80           # Skill went on cooldown (fval=recharge_ms)
    SKILL_RECHARGED: int = 81          # Skill came off cooldown

# ============================================================================
# RawCombatEvent Struct
# ============================================================================

class PyRawCombatEvent:
    """
    Raw combat event captured from GW packets.

    Fields:
        timestamp   : uint32 (GetTickCount / GetTickCount64)
        event_type  : int (PyEventType.*)
        agent_id    : int (caster / source)
        value       : int (skill_id, effect_id, etc.)
        target_id   : int (target / victim)
        float_value : float (damage fraction, duration, energy fraction, etc.)
    """

    timestamp: int
    event_type: int
    agent_id: int
    value: int
    target_id: int
    float_value: float

    def __init__(self) -> None: ...

    def as_tuple(self) -> Tuple[int, int, int, int, int, float]: ...

# ============================================================================
# CombatEventQueue Class
# ============================================================================

class PyCombatEventQueue:
    """
    Thread-safe queue of RawCombatEvent objects.
    """

    def __init__(self) -> None: ...

    # Lifecycle
    def Initialize(self) -> None: ...
    def Terminate(self) -> None: ...

    # Queue access
    def GetAndClearEvents(self) -> List[PyRawCombatEvent]: ...
    def PeekEvents(self) -> List[PyRawCombatEvent]: ...

    def GetQueueSize(self) -> int: ...

    # Configuration
    def SetMaxEvents(self, count: int) -> None: ...
    def GetMaxEvents(self) -> int: ...

    # State
    def IsInitialized(self) -> bool: ...
    
# ============================================================================
# Global Singleton Accessor
# ============================================================================

def GetCombatEventQueue() -> PyCombatEventQueue: ...
