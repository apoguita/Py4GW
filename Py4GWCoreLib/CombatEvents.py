"""
CombatEventQueue - raw combat event access plus higher-level combat state APIs.

The low-level queue facade stays close to the C++ `PyAgentEvents` binding.
Higher-level combat-state helpers remain segmented under
`CombatEventQueue_src.helpers`, while this module serves as the single public
surface for both layers.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import Py4GW
import PyAgentEvents

from .CombatEventQueue_src import helpers
from .enums import EventType


_initialized = False


def _ensure_init():
    """Ensure the native agent-event listener is enabled on first use."""
    global _initialized
    if _initialized:
        return
    if not PyAgentEvents.is_enabled():
        PyAgentEvents.enable()
    _initialized = True

#region CombatEventQueue
class CombatEventQueue:
    """
    Raw combat event queue facade.

    Use this class when you want direct access to the native combat-event
    stream without any interpreted combat-state logic.
    """

    @staticmethod
    def Initialize():
        _ensure_init()
        if not PyAgentEvents.is_enabled():
            PyAgentEvents.enable()

    @staticmethod
    def Terminate():
        if PyAgentEvents.is_enabled():
            PyAgentEvents.disable()

    @staticmethod
    def IsInitialized() -> bool:
        return bool(PyAgentEvents.is_enabled())

    @staticmethod
    def GetAndClearEvents():
        _ensure_init()
        return PyAgentEvents.get_and_clear_events()

    @staticmethod
    def PeekEvents():
        _ensure_init()
        return PyAgentEvents.peek_events()

    @staticmethod
    def GetAndClearEventTuples() -> List[Tuple[int, int, int, int, int, float]]:
        return [event.as_tuple() for event in CombatEventQueue.GetAndClearEvents()]

    @staticmethod
    def PeekEventTuples() -> List[Tuple[int, int, int, int, int, float]]:
        return [event.as_tuple() for event in CombatEventQueue.PeekEvents()]

    @staticmethod
    def GetMaxEvents() -> int:
        # Reforged native uses a fixed-capacity ring buffer; get_capacity() is the
        # real cap. Legacy SetMaxEvents had no native equivalent and no callers, so
        # it was removed rather than kept as an inert vestige (documented deviation).
        return int(PyAgentEvents.get_capacity())

    @staticmethod
    def GetQueueSize() -> int:
        return int(PyAgentEvents.get_event_count())
    
#region CombatEvents
class CombatEvents:
    """
    Public combat-events manager API.

    Raw event ingestion, state mining, and callback dispatch helpers live in
    `CombatEventQueue_src.helpers`. This class intentionally exposes only the
    external API used by the rest of the codebase.
    """

    _callback_name = "CombatEvents.Update"


    @staticmethod
    def GetEvents() -> List[Tuple[int, int, int, int, int, float]]:
        if not helpers._is_callback_active():
            return []
        return list(helpers._events)

    @staticmethod
    def ClearEvents():
        helpers._events.clear()

    @staticmethod
    def GetRecentDamage(count: int = 20) -> List[Tuple[int, int, int, float, int, bool]]:
        if not helpers._is_callback_active():
            return []
        result = []
        for ts, etype, agent, val, target, fval in reversed(list(helpers._events)):
            if etype in (helpers.EventType.DAMAGE, helpers.EventType.CRITICAL, helpers.EventType.ARMOR_IGNORING):
                result.append((ts, agent, target, fval, val, etype == helpers.EventType.CRITICAL))
                if len(result) >= count:
                    break
        return list(reversed(result))

    @staticmethod
    def GetRecentHealing(count: int = 20) -> List[Tuple[int, int, int, float, int]]:
        return helpers._get_recent_healing(count)

    @staticmethod
    def GetRecentEffectRenewals(count: int = 20) -> List[Tuple[int, int, int]]:
        return helpers._get_recent_effect_renewals(count)

    @staticmethod
    def GetRecentSkills(count: int = 20) -> List[Tuple[int, int, int, int, int]]:
        if not helpers._is_callback_active():
            return []
        skill_types = {
            helpers.EventType.SKILL_ACTIVATED,
            helpers.EventType.ATTACK_SKILL_ACTIVATED,
            helpers.EventType.SKILL_FINISHED,
            helpers.EventType.ATTACK_SKILL_FINISHED,
            helpers.EventType.INTERRUPTED,
            helpers.EventType.INSTANT_SKILL_ACTIVATED,
        }
        result = []
        for ts, etype, agent, val, target, _ in reversed(list(helpers._events)):
            if etype in skill_types:
                result.append((ts, agent, val, target, etype))
                if len(result) >= count:
                    break
        return list(reversed(result))

    @staticmethod
    def OnSkillActivated(cb: Callable[[int, int, int], None]):
        helpers._callbacks.setdefault("skill_activated", []).append(cb)

    @staticmethod
    def OnSkillFinished(cb: Callable[[int, int], None]):
        helpers._callbacks.setdefault("skill_finished", []).append(cb)

    @staticmethod
    def OnSkillInterrupted(cb: Callable[[int, int], None]):
        helpers._callbacks.setdefault("skill_interrupted", []).append(cb)

    @staticmethod
    def OnAttackStarted(cb: Callable[[int, int], None]):
        helpers._callbacks.setdefault("attack_started", []).append(cb)

    @staticmethod
    def OnKnockdown(cb: Callable[[int, float], None]):
        helpers._callbacks.setdefault("knockdown", []).append(cb)

    @staticmethod
    def OnDamage(cb: Callable[[int, int, float, int], None]):
        helpers._callbacks.setdefault("damage", []).append(cb)

    @staticmethod
    def OnHealing(cb: Callable[[int, int, float, int], None]):
        helpers._callbacks.setdefault("healing", []).append(cb)

    @staticmethod
    def OnEffectRenewed(cb: Callable[[int, int], None]):
        helpers._callbacks.setdefault("effect_renewed", []).append(cb)

    @staticmethod
    def OnAftercastEnded(cb: Callable[[int], None]):
        helpers._callbacks.setdefault("aftercast_ended", []).append(cb)

    @staticmethod
    def OnSkillRechargeStarted(cb: Callable[[int, int, int], None]):
        helpers._callbacks.setdefault("skill_recharge_started", []).append(cb)

    @staticmethod
    def OnSkillRecharged(cb: Callable[[int, int], None]):
        helpers._callbacks.setdefault("skill_recharged", []).append(cb)

    @staticmethod
    def ClearCallbacks():
        helpers._callbacks.clear()

    @staticmethod
    def ClearRechargeData(agent_id: int):
        helpers._recharges.pop(agent_id, None)

    @staticmethod
    def Update():
        helpers._process_pending_events(CombatEventQueue)

    @staticmethod
    def Enable():
        #deactivated by design
        helpers._set_callback_active(False)
        import PyCallback
        PyCallback.PyCallback.Register(
             CombatEvents._callback_name,
             PyCallback.Phase.Data,
             CombatEvents.Update,
             priority=7,
             context=PyCallback.Context.Draw
         )

    @staticmethod
    def Disable():
        helpers._set_callback_active(False)
        try:
            import PyCallback

            PyCallback.PyCallback.RemoveByName(CombatEvents._callback_name)
        except Exception:
            pass

COMBAT_EVENTS = CombatEvents()

try:
    CombatEvents.Enable()
except Exception as e:
    Py4GW.Console.Log("CombatEvents", f"Module init error: {e}", Py4GW.Console.MessageType.Error)


EventTypes = EventType
