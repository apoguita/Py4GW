"""
Combat Events - Real-time combat state tracking for Guild Wars.

This module provides a clean Python API for querying combat state and reacting
to combat events. Data is captured from game packets and processed into
easy-to-use state queries and optional callbacks.

Architecture:
    C++ Layer (py_combat_events.cpp):
        - Hooks game packets via GWCA
        - Captures raw events (timestamp, type, agent, value, target, float_value)
        - Pushes to a thread-safe queue

    Python Layer (this module):
        - Polls queue each frame via update()
        - Mines events to determine current state (is_casting, is_attacking, etc.)
        - Tracks persistent state (skill recharges, stances, disabled status)
        - Provides optional callbacks for reactive code

Quick Start - Query Combat State:
    ```python
    from Py4GWCoreLib import CombatEvents, Player, Skillbar

    # Check if you can use a skill right now
    if CombatEvents.can_act(Player.GetAgentID()):
        Skillbar.UseSkill(1)

    # Check enemy's casting state
    if CombatEvents.is_casting(enemy_id):
        skill = CombatEvents.get_casting_skill(enemy_id)
        progress = CombatEvents.get_cast_progress(enemy_id)
        print(f"Casting skill {skill}, {progress*100:.0f}% done")
    ```

Quick Start - Use Callbacks:
    ```python
    from Py4GWCoreLib import CombatEvents

    def on_can_act_again(agent_id):
        if agent_id == my_player_id:
            use_next_skill()  # Frame-perfect timing!

    CombatEvents.on_aftercast_ended(on_can_act_again)
    ```

State Query Functions (Primary API):
    Casting:
        is_casting(agent_id) -> bool
        get_casting_skill(agent_id) -> int (skill_id or 0)
        get_cast_target(agent_id) -> int (target_id or 0)
        get_cast_progress(agent_id) -> float (0.0-1.0, or -1 if not casting)
        get_cast_time_remaining(agent_id) -> int (milliseconds)

    Attacking:
        is_attacking(agent_id) -> bool
        get_attack_target(agent_id) -> int (target_id or 0)

    Action State:
        can_act(agent_id) -> bool (not disabled, not knocked down)
        is_disabled(agent_id) -> bool (casting or in aftercast)
        is_knocked_down(agent_id) -> bool
        get_knockdown_remaining(agent_id) -> int (milliseconds)

    Skill Recharges:
        is_skill_recharging(agent_id, skill_id) -> bool
        get_skill_recharge_remaining(agent_id, skill_id) -> int (milliseconds)
        get_recharging_skills(agent_id) -> List[(skill_id, remaining_ms, is_estimated)]
        get_observed_skills(agent_id) -> Set[int] (all skills we've seen agent use)
        is_recharge_estimated(agent_id, skill_id) -> bool (true if using base recharge)

    Stances (Estimated):
        has_stance(agent_id) -> bool
        get_stance(agent_id) -> int or None
        get_stance_remaining(agent_id) -> int (milliseconds)

    Targeting:
        get_agents_targeting(target_id) -> List[int] (agents casting/attacking target)

Callback Functions (Optional - for reactive code):
    on_skill_activated(callback)      - callback(caster_id, skill_id, target_id)
    on_skill_finished(callback)       - callback(agent_id, skill_id)
    on_skill_interrupted(callback)    - callback(agent_id, skill_id)
    on_attack_started(callback)       - callback(attacker_id, target_id)
    on_aftercast_ended(callback)      - callback(agent_id) -- AGENT CAN ACT AGAIN!
    on_knockdown(callback)            - callback(agent_id, duration_seconds)
    on_damage(callback)               - callback(target_id, source_id, damage_fraction, skill_id)
    on_skill_recharge_started(callback) - callback(agent_id, skill_id, recharge_ms)
    on_skill_recharged(callback)      - callback(agent_id, skill_id)

Raw Event Access (Advanced):
    get_events() -> List[(timestamp, type, agent, value, target, float_value)]
    get_recent_damage(count) -> List[(ts, target, source, damage, skill, is_crit)]
    get_recent_skills(count) -> List[(ts, caster, skill, target, event_type)]
    clear_events() -> None

Event Types (for raw event processing):
    See EventType class for all event type constants.

Note on Skill Recharges:
    The server only sends recharge packets for agents whose skillbars we can
    directly observe - typically the player and their own heroes. For all other
    agents (enemies, NPCs, other human players in party), recharges are ESTIMATED
    using base skill data from the skill definition.

    Estimated recharges do NOT account for:
    - Fast Casting attribute (reduces recharge for Mesmers)
    - Serpent's Quickness, Quickening Zephyr, etc.
    - Equipment modifiers
    - Skills that reduce/reset recharge

    Use is_recharge_estimated() to check if data is from server or estimated.

Note on Damage Values:
    Damage is reported as a FRACTION of max HP, not absolute numbers.
    To get actual damage: actual = damage_fraction * Agent.GetMaxHealth(target_id)

See Also:
    - CombatEventsTester.py: Interactive widget demonstrating all features
    - CombatEvents_Guide.md: Beginner-friendly tutorial with examples
"""

import PyCombatEvents
from typing import List, Set, Tuple, Optional, Callable
from collections import deque
import Py4GW


def _get_tick_count() -> int:
    """Get current time in milliseconds."""
    import ctypes
    return ctypes.windll.kernel32.GetTickCount()


# Event type constants
class EventType:
    """
    Combat event type constants - mirrors C++ CombatEventTypes.

    Use these to identify event types when processing raw events:
        for ts, etype, agent, val, target, fval in CombatEvents.get_events():
            if etype == EventType.SKILL_ACTIVATED:
                print(f"Agent {agent} casting skill {val} on {target}")

    Event Categories:
        Skill Events (1-8): Skill activation, completion, interruption
        Attack Events (13-15): Auto-attacks (not skill-based)
        State Events (16-18): Disabled state, knockdown, cast times
        Damage Events (30-32): Damage dealt (normal, critical, armor-ignoring)
        Effect Events (40-42): Visual effects applied/removed
        Energy Events (50-51): Energy gained/spent
        Skill Recharge (80-81): Skill cooldown tracking
    """
    # -- Skill Events --
    SKILL_ACTIVATED = 1           # Non-attack skill started: agent=caster, val=skill_id, target=target
    ATTACK_SKILL_ACTIVATED = 2    # Attack skill started: agent=caster, val=skill_id, target=target
    SKILL_STOPPED = 3             # Skill cancelled (moved, etc.): agent=caster, val=skill_id
    SKILL_FINISHED = 4            # Skill completed: agent=caster, val=skill_id
    ATTACK_SKILL_FINISHED = 5     # Attack skill completed: agent=caster, val=skill_id
    INTERRUPTED = 6               # Skill interrupted: agent=interrupted, val=skill_id
    INSTANT_SKILL_ACTIVATED = 7   # Instant skill (no cast time): agent=caster, val=skill_id, target=target
    ATTACK_SKILL_STOPPED = 8      # Attack skill cancelled: agent=caster, val=skill_id

    # -- Attack Events (auto-attacks) --
    ATTACK_STARTED = 13           # Auto-attack started: agent=attacker, target=target
    ATTACK_STOPPED = 14           # Auto-attack stopped: agent=attacker
    MELEE_ATTACK_FINISHED = 15    # Melee hit completed: agent=attacker

    # -- State Events --
    DISABLED = 16                 # Disabled state changed: agent=agent, val=1(disabled)/0(can act)
    KNOCKED_DOWN = 17             # Knockdown: agent=knocked, fval=duration_seconds
    CASTTIME = 18                 # Cast time info: agent=caster, fval=duration_seconds

    # -- Damage Events --
    # NOTE: For damage, agent_id=TARGET (who receives), target_id=SOURCE (who deals)!
    DAMAGE = 30                   # Normal damage: agent=target, target=source, fval=damage_fraction
    CRITICAL = 31                 # Critical hit: agent=target, target=source, fval=damage_fraction
    ARMOR_IGNORING = 32           # Armor-ignoring (can be negative for heals!)

    # -- Effect Events --
    EFFECT_APPLIED = 40           # Visual effect applied: agent=affected, val=effect_id
    EFFECT_REMOVED = 41           # Visual effect removed: agent=affected, val=effect_id
    EFFECT_ON_TARGET = 42         # Skill effect hit target: agent=caster, val=effect_id, target=target

    # -- Energy Events --
    ENERGY_GAINED = 50            # Energy gained: agent=agent, fval=energy_amount
    ENERGY_SPENT = 51             # Energy spent: agent=agent, fval=energy_fraction

    # -- Misc --
    SKILL_DAMAGE = 60             # Pre-damage notification: agent=target, val=skill_id
    SKILL_ACTIVATE_PACKET = 70    # Early skill notification: agent=caster, val=skill_id

    # -- Skill Recharge Events --
    SKILL_RECHARGE = 80           # Skill went on cooldown: agent=agent, val=skill_id, fval=recharge_ms
    SKILL_RECHARGED = 81          # Skill ready again: agent=agent, val=skill_id


# Internal storage - minimal state
_queue = None
_initialized = False
_events: deque = deque(maxlen=2000)
_disabled: Set[int] = set()
_recharges: dict = {}  # agent_id -> {skill_id: (start, duration, end, is_estimated)}
_observed: dict = {}   # agent_id -> set of skill_ids we've seen them use
_stances: dict = {}    # agent_id -> (skill_id, start, end)
_tracked_agents: set = set()  # agent IDs that receive actual recharge packets from server
_callbacks: dict = {}  # event_name -> [callbacks]


def _ensure_init():
    """Initialize on first use."""
    global _queue, _initialized
    if _initialized:
        return
    _queue = PyCombatEvents.GetCombatEventQueue()
    # Explicitly initialize the C++ hooks if not already done
    if not _queue.IsInitialized():
        _queue.Initialize()
    _initialized = True


class CombatEvents:
    """
    Query combat state and register callbacks for combat events.

    All methods are static - no instantiation needed. Data is automatically
    updated each frame via update() which is registered on module load.

    Usage Patterns:
        1. QUERY STATE (check conditions in your main loop):
            if CombatEvents.can_act(player_id):
                Skillbar.UseSkill(1)

        2. CALLBACKS (react to events as they happen):
            def on_ready(agent_id):
                if agent_id == player_id:
                    use_next_skill()
            CombatEvents.on_aftercast_ended(on_ready)

    Most Important Methods:
        can_act(agent_id)      - Can agent use skills right now?
        is_casting(agent_id)   - Is agent currently casting?
        is_attacking(agent_id) - Is agent auto-attacking?

    See module docstring for complete API reference.
    """

    # ==========================================================================
    # Casting State
    # ==========================================================================

    @staticmethod
    def is_casting(agent_id: int) -> bool:
        """Check if agent is currently casting."""
        return CombatEvents._find_cast(agent_id) is not None

    @staticmethod
    def get_casting_skill(agent_id: int) -> int:
        """Get skill ID being cast (0 if not casting)."""
        cast = CombatEvents._find_cast(agent_id)
        return cast[0] if cast else 0

    @staticmethod
    def get_cast_target(agent_id: int) -> int:
        """Get target of current cast (0 if none)."""
        cast = CombatEvents._find_cast(agent_id)
        return cast[1] if cast else 0

    @staticmethod
    def get_cast_progress(agent_id: int) -> float:
        """Get cast progress 0.0-1.0 (-1 if not casting)."""
        cast = CombatEvents._find_cast(agent_id)
        if not cast:
            return -1.0
        _, _, start, duration = cast
        if duration <= 0:
            return 1.0
        elapsed = _get_tick_count() - start
        return min(elapsed / (duration * 1000.0), 1.0)

    @staticmethod
    def get_cast_time_remaining(agent_id: int) -> int:
        """Get remaining cast time in milliseconds."""
        cast = CombatEvents._find_cast(agent_id)
        if not cast:
            return 0
        _, _, start, duration = cast
        if duration <= 0:
            return 0
        return max(0, int(duration * 1000) - (_get_tick_count() - start))

    # ==========================================================================
    # Attack State
    # ==========================================================================

    @staticmethod
    def is_attacking(agent_id: int) -> bool:
        """Check if agent is auto-attacking."""
        return CombatEvents._find_attack(agent_id) is not None

    @staticmethod
    def get_attack_target(agent_id: int) -> int:
        """Get attack target (0 if not attacking)."""
        return CombatEvents._find_attack(agent_id) or 0

    # ==========================================================================
    # Disabled / Knockdown State
    # ==========================================================================

    @staticmethod
    def can_act(agent_id: int) -> bool:
        """Check if agent can use skills (not disabled, not knocked down)."""
        return agent_id not in _disabled and not CombatEvents.is_knocked_down(agent_id)

    @staticmethod
    def is_disabled(agent_id: int) -> bool:
        """Check if agent is disabled (casting or aftercast)."""
        return agent_id in _disabled

    @staticmethod
    def is_knocked_down(agent_id: int) -> bool:
        """Check if agent is knocked down."""
        kd = CombatEvents._find_knockdown(agent_id)
        return kd is not None

    @staticmethod
    def get_knockdown_remaining(agent_id: int) -> int:
        """Get remaining knockdown time in ms."""
        kd = CombatEvents._find_knockdown(agent_id)
        if not kd:
            return 0
        start, duration = kd
        return max(0, int(duration * 1000) - (_get_tick_count() - start))

    # ==========================================================================
    # Skill Recharge
    # ==========================================================================

    @staticmethod
    def is_skill_recharging(agent_id: int, skill_id: int) -> bool:
        """Check if skill is on cooldown."""
        if agent_id not in _recharges or skill_id not in _recharges[agent_id]:
            return False
        data = _recharges[agent_id][skill_id]
        end = data[2]  # (start, duration, end, is_estimated)
        return _get_tick_count() < end

    @staticmethod
    def get_skill_recharge_remaining(agent_id: int, skill_id: int) -> int:
        """Get remaining recharge time in ms."""
        if agent_id not in _recharges or skill_id not in _recharges[agent_id]:
            return 0
        data = _recharges[agent_id][skill_id]
        end = data[2]  # (start, duration, end, is_estimated)
        return max(0, end - _get_tick_count())

    @staticmethod
    def get_recharging_skills(agent_id: int) -> List[Tuple[int, int, bool]]:
        """Get all recharging skills. Returns [(skill_id, remaining_ms, is_estimated), ...]

        is_estimated=True means we're using base recharge from skill definition
        (no modifiers applied). is_estimated=False means actual server data.
        """
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

    @staticmethod
    def is_recharge_estimated(agent_id: int, skill_id: int) -> bool:
        """Check if recharge data is estimated (from skill definition, no modifiers).

        Returns True if we're using base skill recharge time (enemies, NPCs).
        Returns False if we have actual server data (player, heroes).
        """
        if agent_id not in _recharges or skill_id not in _recharges[agent_id]:
            return False
        data = _recharges[agent_id][skill_id]
        if len(data) == 4:
            return data[3]
        return False

    @staticmethod
    def get_observed_skills(agent_id: int) -> Set[int]:
        """Get all skills we've seen agent use."""
        return _observed.get(agent_id, set()).copy()

    # ==========================================================================
    # Stance (ESTIMATES)
    # ==========================================================================

    @staticmethod
    def has_stance(agent_id: int) -> bool:
        """Check if agent has active stance (ESTIMATE)."""
        if agent_id not in _stances:
            return False
        _, _, end = _stances[agent_id]
        return _get_tick_count() < end

    @staticmethod
    def get_stance(agent_id: int) -> Optional[int]:
        """Get active stance skill ID (None if none)."""
        if not CombatEvents.has_stance(agent_id):
            return None
        return _stances[agent_id][0]

    @staticmethod
    def get_stance_remaining(agent_id: int) -> int:
        """Get estimated stance time remaining in ms."""
        if agent_id not in _stances:
            return 0
        _, _, end = _stances[agent_id]
        return max(0, end - _get_tick_count())

    # ==========================================================================
    # Targeting
    # ==========================================================================

    @staticmethod
    def get_agents_targeting(target_id: int) -> List[int]:
        """Get all agents casting/attacking target."""
        result = set()
        now = _get_tick_count()
        for ts, etype, agent, _, target, _ in _events:
            if now - ts > 10000:
                continue
            if target == target_id and etype in (EventType.SKILL_ACTIVATED, EventType.ATTACK_SKILL_ACTIVATED, EventType.ATTACK_STARTED):
                if CombatEvents.is_casting(agent) or CombatEvents.is_attacking(agent):
                    result.add(agent)
        return list(result)

    # ==========================================================================
    # Raw Event Access
    # ==========================================================================

    @staticmethod
    def get_events() -> List[Tuple[int, int, int, int, int, float]]:
        """Get raw event log. Returns [(timestamp, type, agent, value, target, float), ...]"""
        return list(_events)

    @staticmethod
    def clear_events():
        """Clear the event log."""
        _events.clear()

    @staticmethod
    def get_recent_damage(count: int = 20) -> List[Tuple[int, int, int, float, int, bool]]:
        """Get recent damage. Returns [(timestamp, target, source, damage, skill, is_crit), ...]"""
        result = []
        for ts, etype, agent, val, target, fval in reversed(list(_events)):
            if etype in (EventType.DAMAGE, EventType.CRITICAL, EventType.ARMOR_IGNORING):
                result.append((ts, agent, target, fval, val, etype == EventType.CRITICAL))
                if len(result) >= count:
                    break
        return list(reversed(result))

    @staticmethod
    def get_recent_skills(count: int = 20) -> List[Tuple[int, int, int, int, int]]:
        """Get recent skills. Returns [(timestamp, caster, skill, target, type), ...]"""
        skill_types = {EventType.SKILL_ACTIVATED, EventType.ATTACK_SKILL_ACTIVATED,
                       EventType.SKILL_FINISHED, EventType.ATTACK_SKILL_FINISHED,
                       EventType.INTERRUPTED, EventType.INSTANT_SKILL_ACTIVATED}
        result = []
        for ts, etype, agent, val, target, _ in reversed(list(_events)):
            if etype in skill_types:
                result.append((ts, agent, val, target, etype))
                if len(result) >= count:
                    break
        return list(reversed(result))

    # ==========================================================================
    # Callbacks (Optional)
    # ==========================================================================

    @staticmethod
    def on_skill_activated(cb: Callable[[int, int, int], None]):
        """Callback: (caster_id, skill_id, target_id)"""
        _callbacks.setdefault('skill_activated', []).append(cb)

    @staticmethod
    def on_skill_finished(cb: Callable[[int, int], None]):
        """Callback: (agent_id, skill_id)"""
        _callbacks.setdefault('skill_finished', []).append(cb)

    @staticmethod
    def on_skill_interrupted(cb: Callable[[int, int], None]):
        """Callback: (agent_id, skill_id)"""
        _callbacks.setdefault('skill_interrupted', []).append(cb)

    @staticmethod
    def on_attack_started(cb: Callable[[int, int], None]):
        """Callback: (attacker_id, target_id)"""
        _callbacks.setdefault('attack_started', []).append(cb)

    @staticmethod
    def on_knockdown(cb: Callable[[int, float], None]):
        """Callback: (agent_id, duration)"""
        _callbacks.setdefault('knockdown', []).append(cb)

    @staticmethod
    def on_damage(cb: Callable[[int, int, float, int], None]):
        """Callback: (target_id, source_id, amount, skill_id)"""
        _callbacks.setdefault('damage', []).append(cb)

    @staticmethod
    def on_aftercast_ended(cb: Callable[[int], None]):
        """Callback: (agent_id) - agent can act again"""
        _callbacks.setdefault('aftercast_ended', []).append(cb)

    @staticmethod
    def on_skill_recharge_started(cb: Callable[[int, int, int], None]):
        """Callback: (agent_id, skill_id, recharge_ms)"""
        _callbacks.setdefault('skill_recharge_started', []).append(cb)

    @staticmethod
    def on_skill_recharged(cb: Callable[[int, int], None]):
        """Callback: (agent_id, skill_id)"""
        _callbacks.setdefault('skill_recharged', []).append(cb)

    @staticmethod
    def clear_callbacks():
        """Clear all callbacks."""
        _callbacks.clear()

    @staticmethod
    def clear_recharge_data(agent_id: int):
        """Clear recharge data for agent."""
        _recharges.pop(agent_id, None)

    # ==========================================================================
    # Internal: Event Mining
    # ==========================================================================

    @staticmethod
    def _find_cast(agent_id: int) -> Optional[Tuple[int, int, int, float]]:
        """Find active cast. Returns (skill, target, start, duration) or None."""
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
            if etype in (EventType.SKILL_FINISHED, EventType.ATTACK_SKILL_FINISHED,
                        EventType.SKILL_STOPPED, EventType.ATTACK_SKILL_STOPPED,
                        EventType.INTERRUPTED):
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

    @staticmethod
    def _find_attack(agent_id: int) -> Optional[int]:
        """Find active attack. Returns target_id or None."""
        now = _get_tick_count()
        for ts, etype, agent, _, target, _ in reversed(list(_events)):
            if agent != agent_id:
                continue
            if now - ts > 10000:
                break
            if etype in (EventType.ATTACK_STOPPED, EventType.MELEE_ATTACK_FINISHED,
                        EventType.ATTACK_SKILL_FINISHED, EventType.ATTACK_SKILL_STOPPED):
                return None
            if etype in (EventType.ATTACK_STARTED, EventType.ATTACK_SKILL_ACTIVATED):
                return target
        return None

    @staticmethod
    def _find_knockdown(agent_id: int) -> Optional[Tuple[int, float]]:
        """Find active knockdown. Returns (start, duration) or None."""
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

    @staticmethod
    def _get_pending_skill(agent_id: int) -> int:
        """Get skill being cast."""
        for _, etype, agent, val, _, _ in reversed(list(_events)):
            if agent != agent_id:
                continue
            if etype in (EventType.SKILL_ACTIVATED, EventType.ATTACK_SKILL_ACTIVATED, EventType.SKILL_ACTIVATE_PACKET):
                return val
        return 0

    # ==========================================================================
    # Internal: Update (called each frame)
    # ==========================================================================

    @staticmethod
    def update():
        """Process pending events. Called automatically each frame."""
        _ensure_init()
        if not _queue:
            return

        for event in _queue.GetAndClearEvents():
            CombatEvents._process(event)

        # Check expired stances
        now = _get_tick_count()
        expired = [(aid, sid) for aid, (sid, _, end) in _stances.items() if now >= end]
        for aid, sid in expired:
            del _stances[aid]

    @staticmethod
    def _process(event):
        """Process a single event."""
        ts = event.timestamp
        etype = event.event_type
        agent = event.agent_id
        val = event.value
        target = event.target_id
        fval = event.float_value

        _events.append((ts, etype, agent, val, target, fval))

        # Fire callbacks based on event type
        if etype == EventType.SKILL_ACTIVATED or etype == EventType.ATTACK_SKILL_ACTIVATED:
            # Track observed skills
            if agent not in _observed:
                _observed[agent] = set()
            if val > 0:
                _observed[agent].add(val)
            CombatEvents._check_stance(ts, agent, val)
            # Create estimated recharge for agents we don't get server packets for
            CombatEvents._create_estimated_recharge(ts, agent, val)
            CombatEvents._fire('skill_activated', agent, val, target)

        elif etype == EventType.INSTANT_SKILL_ACTIVATED:
            # Track observed skills for instant skills too
            if agent not in _observed:
                _observed[agent] = set()
            if val > 0:
                _observed[agent].add(val)
            # Create estimated recharge for agents we don't get server packets for
            CombatEvents._create_estimated_recharge(ts, agent, val)
            CombatEvents._fire('skill_activated', agent, val, target)

        elif etype == EventType.SKILL_FINISHED or etype == EventType.ATTACK_SKILL_FINISHED:
            skill = CombatEvents._get_pending_skill(agent)
            CombatEvents._fire('skill_finished', agent, skill)

        elif etype == EventType.INTERRUPTED:
            skill = CombatEvents._get_pending_skill(agent)
            CombatEvents._fire('skill_interrupted', agent, skill)

        elif etype == EventType.ATTACK_STARTED:
            CombatEvents._fire('attack_started', agent, target)

        elif etype == EventType.DISABLED:
            was_disabled = agent in _disabled
            if val == 1:
                _disabled.add(agent)
            else:
                _disabled.discard(agent)
                if was_disabled:
                    CombatEvents._fire('aftercast_ended', agent)

        elif etype == EventType.KNOCKED_DOWN:
            CombatEvents._fire('knockdown', agent, fval)

        elif etype == EventType.DAMAGE or etype == EventType.CRITICAL or etype == EventType.ARMOR_IGNORING:
            # All damage types: DAMAGE (30), CRITICAL (31), ARMOR_IGNORING (32)
            # Note: For damage events, agent_id = target (who receives), target_id = source (who deals)
            skill = CombatEvents._get_pending_skill(target)  # target is source in damage packets
            CombatEvents._fire('damage', agent, target, fval, skill)

        elif etype == EventType.SKILL_RECHARGE:
            # fval from C++ is in seconds (e.g., 30.0 = 30 seconds), convert to ms
            recharge_ms = int(fval * 1000)
            if agent not in _recharges:
                _recharges[agent] = {}
            _recharges[agent][val] = (ts, recharge_ms, ts + recharge_ms, False)  # False = actual server data
            # Track that this agent receives recharge packets (typically player + own heroes)
            _tracked_agents.add(agent)
            CombatEvents._fire('skill_recharge_started', agent, val, recharge_ms)

        elif etype == EventType.SKILL_RECHARGED:
            if agent in _recharges:
                _recharges[agent].pop(val, None)
            CombatEvents._fire('skill_recharged', agent, val)

    @staticmethod
    def _check_stance(ts: int, agent: int, skill_id: int):
        """Check if skill is a stance and track it."""
        try:
            from .Skill import Skill
            skill_type, _ = Skill.GetType(skill_id)
            if skill_type == 3:  # STANCE
                dur_0, dur_15 = Skill.Attribute.GetDuration(skill_id)
                dur_0 = dur_0 if dur_0 > 0 else 0
                dur_15 = dur_15 if dur_15 > 0 else dur_0
                # Conservative estimate
                duration = (dur_0 + (dur_15 - dur_0) * 0.4) * 0.8 if dur_15 > dur_0 else (dur_0 or 5.0)
                _stances[agent] = (skill_id, ts, ts + int(duration * 1000))
        except:
            pass

    @staticmethod
    def _create_estimated_recharge(ts: int, agent: int, skill_id: int):
        """Create estimated recharge using base skill data for untracked agents.

        The server only sends SkillRecharge/SkillRecharged packets for agents whose
        skillbars we can directly observe - typically just the player and their own
        heroes. For everyone else (enemies, NPCs, other human players in party),
        we estimate recharge using the base skill definition.

        NOTE: Estimated recharge does NOT account for modifiers:
        - Fast Casting attribute (reduces recharge for Mesmers)
        - Serpent's Quickness, Quickening Zephyr, etc.
        - Equipment modifiers (weapon mods, inscriptions)
        - Skills that reduce/reset recharge

        This is a best-effort estimate - actual recharge may differ.
        """
        if skill_id <= 0:
            return

        # Skip if this agent receives actual recharge packets from server
        if agent in _tracked_agents:
            return

        try:
            from .Skill import Skill
            # Get base recharge from skill definition (returns seconds as int)
            base_recharge = Skill.Data.GetRecharge(skill_id)
            if base_recharge <= 0:
                return

            # Convert to milliseconds
            recharge_ms = base_recharge * 1000

            if agent not in _recharges:
                _recharges[agent] = {}

            # Store with is_estimated=True
            _recharges[agent][skill_id] = (ts, recharge_ms, ts + recharge_ms, True)
            CombatEvents._fire('skill_recharge_started', agent, skill_id, recharge_ms)

        except Exception:
            pass  # Silently fail if skill data unavailable

    @staticmethod
    def _fire(event_name: str, *args):
        """Fire callbacks."""
        for cb in _callbacks.get(event_name, []):
            try:
                cb(*args)
            except Exception as e:
                Py4GW.Console.Log("CombatEvents", f"Callback error in '{event_name}': {e}", Py4GW.Console.MessageType.Error)


# Aliases for backward compatibility
EventTypes = EventType


# Auto-register update
_update_registered = False

def _enable():
    """Register the update callback. Safe to call multiple times."""
    global _update_registered
    if _update_registered:
        return
    try:
        from Py4GW import Game
        Game.register_callback("CombatEvents.Update", CombatEvents.update)
        _update_registered = True
    except Exception as e:
        Py4GW.Console.Log("CombatEvents", f"Failed to register update callback: {e}", Py4GW.Console.MessageType.Error)

# Try to register at module load
try:
    _enable()
except Exception as e:
    Py4GW.Console.Log("CombatEvents", f"Module init error: {e}", Py4GW.Console.MessageType.Error)

