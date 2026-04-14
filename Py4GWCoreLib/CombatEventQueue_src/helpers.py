from __future__ import annotations

from collections import deque
from typing import List, Set, Tuple, Optional

import Py4GW

from ..enums import EventType


def _get_tick_count() -> int:
    """Get current time in milliseconds from the shared Py4GW game clock."""
    return int(Py4GW.Game.get_tick_count64())


_events: deque = deque(maxlen=2000)
_disabled: Set[int] = set()
_recharges: dict = {}  # agent_id -> {skill_id: (start, duration, end, is_estimated)}
_observed: dict = {}   # agent_id -> set of skill_ids we've seen them use
_stances: dict = {}    # agent_id -> (skill_id, start, end)
_tracked_agents: set = set()  # agent IDs that receive actual recharge packets from server
_callbacks: dict = {}  # event_name -> [callbacks]
_update_registered = False


def _is_disabled(agent_id: int) -> bool:
    return agent_id in _disabled

def _find_cast(agent_id: int) -> tuple[int, int, int, float] | None:
    """Search recent events for an active cast by the agent. 
    Returns (skill_id, target_id, start_time, duration) or None."""
    
    now = _get_tick_count()
    cast_start = None
    skill_id = 0
    target_id = 0
    duration = 0.0
    for ts, etype, agent, val, target, fval in reversed(list(_events)):
        if agent != agent_id:
            continue
        if now - ts > 30000:
            break
        if etype in (
            EventType.SKILL_FINISHED,
            EventType.ATTACK_SKILL_FINISHED,
            EventType.SKILL_STOPPED,
            EventType.ATTACK_SKILL_STOPPED,
            EventType.INTERRUPTED,
        ):
            return None
        if etype in (EventType.SKILL_ACTIVATED, EventType.ATTACK_SKILL_ACTIVATED):
            cast_start = ts
            skill_id = val
            target_id = target
            break
        if etype == EventType.CASTTIME:
            duration = fval
    if cast_start is None:
        return None
    if duration > 0 and now - cast_start > duration * 1000:
        return None
    return (skill_id, target_id, cast_start, duration)

def _is_casting(agent_id: int) -> bool:
        return _find_cast(agent_id) is not None

def _casting_skill_id(agent_id: int) -> int:
    cast = _find_cast(agent_id)
    return cast[0] if cast else 0

def _casting_target_id(agent_id: int) -> int:
    cast = _find_cast(agent_id)
    return cast[1] if cast else 0

def _cast_progress(agent_id: int) -> float:
    cast = _find_cast(agent_id)
    if not cast:
        return -1.0
    _, _, start, duration = cast
    if duration <= 0:
        return 1.0
    elapsed = _get_tick_count() - start
    return min(elapsed / (duration * 1000.0), 1.0)

def _get_remaining_cast_time(agent_id: int) -> int:
    cast = _find_cast(agent_id)
    if not cast:
        return 0
    _, _, start, duration = cast
    if duration <= 0:
        return 0
    return max(0, int(duration * 1000) - (_get_tick_count() - start))

def _get_remaining_recharge_time(agent_id: int, skill_id: int) -> int:
    if agent_id not in _recharges or skill_id not in _recharges[agent_id]:
        return 0
    end = _recharges[agent_id][skill_id][2]
    return max(0, end - _get_tick_count())

def _is_skill_on_cooldown(agent_id: int, skill_id: int) -> bool:
    if agent_id not in _recharges or skill_id not in _recharges[agent_id]:
        return False
    end = _recharges[agent_id][skill_id][2]
    return _get_tick_count() < end

def _get_skills_on_cooldown(agent_id: int) -> List[Tuple[int, int, bool]]:
    """Returns a list of (skill_id, remaining_ms, is_estimated) 
    for all skills currently on cooldown for the agent.
    returns (skill_id, remaining_ms, is_estimated)"""
    
    if agent_id not in _recharges:
        return []
    now = _get_tick_count()
    result = []
    for sid, data in _recharges[agent_id].items():
        if len(data) == 4:
            _, _, end, is_estimated = data
        else:
            _, _, end = data
            is_estimated = False
        if now < end:
            result.append((sid, end - now, is_estimated))
    return result

def _is_cooldown_estimated(agent_id: int, skill_id: int) -> bool:
    if agent_id not in _recharges or skill_id not in _recharges[agent_id]:
        return False
    data = _recharges[agent_id][skill_id]
    return bool(len(data) == 4 and data[3])


def _find_attack(agent_id: int):
    now = _get_tick_count()
    for ts, etype, agent, _, target, _ in reversed(list(_events)):
        if agent != agent_id:
            continue
        if now - ts > 10000:
            break
        if etype in (
            EventType.ATTACK_STOPPED,
            EventType.MELEE_ATTACK_FINISHED,
            EventType.ATTACK_SKILL_FINISHED,
            EventType.ATTACK_SKILL_STOPPED,
        ):
            return None
        if etype in (EventType.ATTACK_STARTED, EventType.ATTACK_SKILL_ACTIVATED):
            return target
    return None

def _is_attacking(agent_id: int) -> bool:
    return _find_attack(agent_id) is not None

def _attack_target(agent_id: int) -> int:
    return _find_attack(agent_id) or 0

def _can_act(agent_id: int) -> bool:
    if _is_knocked_down(agent_id):
        return False
    if _is_casting(agent_id):
        return False
    if _is_disabled(agent_id):
        return _is_attacking(agent_id)
    return True


def _find_knockdown(agent_id: int):
    now = _get_tick_count()
    for ts, etype, agent, _, _, fval in reversed(list(_events)):
        if agent != agent_id:
            continue
        if now - ts > 10000:
            break
        if etype == EventType.KNOCKED_DOWN:
            if now - ts < fval * 1000:
                return (ts, fval)
            return None
    return None

def _is_knocked_down(agent_id: int) -> bool:
    return _find_knockdown(agent_id) is not None

def _get_knockdown_time_remaining(agent_id: int) -> int:
    kd = _find_knockdown(agent_id)
    if not kd:
        return 0
    start, duration = kd
    return max(0, int(duration * 1000) - (_get_tick_count() - start))

def _get_observed_skillbar(agent_id: int) -> Set[int]:
    return _observed.get(agent_id, set()).copy()

def _has_stance(agent_id: int) -> bool:
    if agent_id not in _stances:
        return False
    _, _, end = _stances[agent_id]
    return _get_tick_count() < end

def _get_stance(agent_id: int) -> int:
    if not _has_stance(agent_id):
        return 0
    return _stances[agent_id][0]

def _get_stance_cooldown(agent_id: int) -> int:
    if agent_id not in _stances:
        return 0
    _, _, end = _stances[agent_id]
    return max(0, end - _get_tick_count())


def _get_recent_healing(count: int = 20) -> List[Tuple[int, int, int, float, int]]:
    result = []
    for ts, etype, agent, val, target, fval in reversed(list(_events)):
        if etype == EventType.HEALING:
            result.append((ts, agent, target, fval, val))
            if len(result) >= count:
                break
    return list(reversed(result))


def _get_recent_effect_renewals(count: int = 20) -> List[Tuple[int, int, int]]:
    result = []
    for ts, etype, agent, val, _, _ in reversed(list(_events)):
        if etype == EventType.EFFECT_RENEWED:
            result.append((ts, agent, val))
            if len(result) >= count:
                break
    return list(reversed(result))


def _has_effect_renewed(agent_id: int, effect_id: int, window_ms: int = 10000) -> bool:
    now = _get_tick_count()
    for ts, etype, agent, val, _, _ in reversed(list(_events)):
        if now - ts > window_ms:
            break
        if etype == EventType.EFFECT_RENEWED and agent == agent_id and val == effect_id:
            return True
    return False


def _get_recent_healing_received(agent_id: int, count: int = 20) -> List[Tuple[int, int, float, int]]:
    result = []
    for ts, target_id, source_id, amount, skill_id in reversed(_get_recent_healing(count=max(count * 4, count))):
        if target_id == agent_id:
            result.append((ts, source_id, amount, skill_id))
            if len(result) >= count:
                break
    return list(reversed(result))


def _get_recent_healing_dealt(agent_id: int, count: int = 20) -> List[Tuple[int, int, float, int]]:
    result = []
    for ts, target_id, source_id, amount, skill_id in reversed(_get_recent_healing(count=max(count * 4, count))):
        if source_id == agent_id:
            result.append((ts, target_id, amount, skill_id))
            if len(result) >= count:
                break
    return list(reversed(result))

def _agets_targetting(target_id: int) -> List[int]:
    result = set()
    now = _get_tick_count()
    for ts, etype, agent, _, target, _ in _events:
        if now - ts > 10000:
            continue
        if target == target_id and etype in (EventType.SKILL_ACTIVATED, EventType.ATTACK_SKILL_ACTIVATED, EventType.ATTACK_STARTED):
            if _is_casting(agent) or _is_attacking(agent):
                result.add(agent)
    return list(result)

def _is_targeted (target_id: int) -> bool:
    return len(_agets_targetting(target_id)) > 0


def _check_stance(ts: int, agent: int, skill_id: int):
    try:
        from ..Skill import Skill

        skill_type, _ = Skill.GetType(skill_id)
        if skill_type == 3:
            dur_0, dur_15 = Skill.Attribute.GetDuration(skill_id)
            dur_0 = dur_0 if dur_0 > 0 else 0
            dur_15 = dur_15 if dur_15 > dur_0 else dur_0
            duration = (dur_0 + (dur_15 - dur_0) * 0.4) * 0.8 if dur_15 > dur_0 else (dur_0 or 5.0)
            _stances[agent] = (skill_id, ts, ts + int(duration * 1000))
    except Exception:
        pass



def _get_pending_skill(agent_id: int) -> int:
    for _, etype, agent, val, _, _ in reversed(list(_events)):
        if agent != agent_id:
            continue
        if etype in (EventType.SKILL_ACTIVATED, EventType.ATTACK_SKILL_ACTIVATED, EventType.SKILL_ACTIVATE_PACKET):
            return val
    return 0


def _cleanup_expired_stances():
    now = _get_tick_count()
    expired = [aid for aid, (_, _, end) in _stances.items() if now >= end]
    for aid in expired:
        del _stances[aid]


def _process_pending_events(queue_cls):
    for event in queue_cls.GetAndClearEvents():
        _process_event(event)
    _cleanup_expired_stances()


def _process_event(event):
    ts = event.timestamp
    etype = event.event_type
    agent = event.agent_id
    val = event.value
    target = event.target_id
    fval = event.float_value
    _events.append((ts, etype, agent, val, target, fval))

    if etype in (EventType.SKILL_ACTIVATED, EventType.ATTACK_SKILL_ACTIVATED):
        _observed.setdefault(agent, set())
        if val > 0:
            _observed[agent].add(val)
        _check_stance(ts, agent, val)
        _create_estimated_recharge(ts, agent, val)
        _fire("skill_activated", agent, val, target)
    elif etype == EventType.INSTANT_SKILL_ACTIVATED:
        _observed.setdefault(agent, set())
        if val > 0:
            _observed[agent].add(val)
        _create_estimated_recharge(ts, agent, val)
        _fire("skill_activated", agent, val, target)
    elif etype in (EventType.SKILL_FINISHED, EventType.ATTACK_SKILL_FINISHED):
        _fire("skill_finished", agent, _get_pending_skill(agent))
    elif etype == EventType.INTERRUPTED:
        _fire("skill_interrupted", agent, _get_pending_skill(agent))
    elif etype == EventType.ATTACK_STARTED:
        _fire("attack_started", agent, target)
    elif etype == EventType.DISABLED:
        was_disabled = agent in _disabled
        if val == 1:
            _disabled.add(agent)
        else:
            _disabled.discard(agent)
            if was_disabled:
                _fire("aftercast_ended", agent)
    elif etype == EventType.KNOCKED_DOWN:
        _fire("knockdown", agent, fval)
    elif etype in (EventType.DAMAGE, EventType.CRITICAL, EventType.ARMOR_IGNORING):
        _fire("damage", agent, target, fval, _get_pending_skill(target))
    elif etype == EventType.HEALING:
        _fire("healing", agent, target, fval, _get_pending_skill(target))
    elif etype == EventType.EFFECT_RENEWED:
        _fire("effect_renewed", agent, val)
    elif etype == EventType.SKILL_RECHARGE:
        recharge_ms = int(fval * 1000)
        _recharges.setdefault(agent, {})
        _recharges[agent][val] = (ts, recharge_ms, ts + recharge_ms, False)
        _tracked_agents.add(agent)
        _fire("skill_recharge_started", agent, val, recharge_ms)
    elif etype == EventType.SKILL_RECHARGED:
        if agent in _recharges:
            _recharges[agent].pop(val, None)
        _fire("skill_recharged", agent, val)


def _create_estimated_recharge(ts: int, agent: int, skill_id: int):
    if skill_id <= 0 or agent in _tracked_agents:
        return
    try:
        from ..Skill import Skill

        base_recharge = Skill.Data.GetRecharge(skill_id)
        if base_recharge <= 0:
            return
        recharge_ms = base_recharge * 1000
        _recharges.setdefault(agent, {})
        _recharges[agent][skill_id] = (ts, recharge_ms, ts + recharge_ms, True)
        _fire("skill_recharge_started", agent, skill_id, recharge_ms)
    except Exception:
        pass


def _fire(event_name: str, *args):
    for cb in _callbacks.get(event_name, []):
        try:
            cb(*args)
        except Exception as e:
            Py4GW.Console.Log("CombatEvents", f"Callback error in '{event_name}': {e}", Py4GW.Console.MessageType.Error)


def _enable_updates(manager_cls):
    global _update_registered
    if _update_registered:
        return
    try:
        import PyCallback

        """PyCallback.PyCallback.Register(
            "CombatEvents.Update",
            PyCallback.Phase.Data,
            manager_cls.update,
            priority=99
        )"""
        _update_registered = True
    except Exception as e:
        Py4GW.Console.Log("CombatEvents", f"Failed to register update callback: {e}", Py4GW.Console.MessageType.Error)
