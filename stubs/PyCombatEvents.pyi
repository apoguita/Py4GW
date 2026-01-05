from __future__ import annotations
from typing import List, Tuple

# ============================
# Module: PyCombatEvents
# ============================

__doc__: str


# ============================
# Submodule: EventType
# ============================

class PyEventType:
    """
    Combat event type constants.

    Values correspond directly to CombatEventTypes in C++.
    """

    SKILL_ACTIVATED: int
    ATTACK_SKILL_ACTIVATED: int
    SKILL_STOPPED: int
    SKILL_FINISHED: int
    ATTACK_SKILL_FINISHED: int
    INTERRUPTED: int
    INSTANT_SKILL_ACTIVATED: int
    ATTACK_SKILL_STOPPED: int
    ATTACK_STARTED: int
    ATTACK_STOPPED: int
    MELEE_ATTACK_FINISHED: int
    DISABLED: int
    KNOCKED_DOWN: int
    CASTTIME: int
    DAMAGE: int
    CRITICAL: int
    ARMOR_IGNORING: int
    EFFECT_APPLIED: int
    EFFECT_REMOVED: int
    EFFECT_ON_TARGET: int
    ENERGY_GAINED: int
    ENERGY_SPENT: int
    SKILL_DAMAGE: int
    SKILL_ACTIVATE_PACKET: int


# ============================
# Struct: RawCombatEvent
# ============================

class PyRawCombatEvent:
    """
    Raw combat event captured from Guild Wars packets.

    This is a low-level data structure mirroring the C++ struct.
    """

    timestamp: int
    event_type: int
    agent_id: int
    value: int
    target_id: int
    float_value: float

    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...

    def as_tuple(self) -> Tuple[int, int, int, int, int, float]:
        """
        Return the event as a tuple:
        (timestamp, event_type, agent_id, value, target_id, float_value)
        """
        ...


# ============================
# Class: CombatEventQueue
# ============================

class PyCombatEventQueue:
    """
    Thread-safe queue that stores combat events captured from packets.

    Typically accessed via GetCombatEventQueue().
    """

    def __init__(self) -> None: ...

    def Initialize(self) -> None:
        """
        Initialize packet callbacks.

        Must be called once before events are collected.
        """
        ...

    def Terminate(self) -> None:
        """
        Remove packet callbacks and stop collecting events.
        """
        ...

    def GetAndClearEvents(self) -> List[PyRawCombatEvent]:
        """
        Return all queued events and clear the queue.

        Intended to be called once per frame.
        """
        ...

    def PeekEvents(self) -> List[PyRawCombatEvent]:
        """
        Return queued events without clearing them.

        Intended for debugging.
        """
        ...

    def SetMaxEvents(self, count: int) -> None:
        """
        Set the maximum number of events allowed in the queue.
        Older events will be dropped when exceeded.
        """
        ...

    def GetMaxEvents(self) -> int:
        """
        Return the maximum queue size.
        """
        ...

    def IsInitialized(self) -> bool:
        """
        Return True if packet callbacks are registered.
        """
        ...

    def GetQueueSize(self) -> int:
        """
        Return the current number of queued events.
        """
        ...


# ============================
# Global functions
# ============================

def GetCombatEventQueue() -> PyCombatEventQueue:
    """
    Return the global CombatEventQueue singleton instance.
    """
    ...
