"""
Combat Events System for Py4GW
==============================

This module provides a comprehensive event-driven combat tracking system for Guild Wars.
It captures game packets via C++ hooks and exposes them through Python callbacks, allowing
you to react to combat events in real-time.

Architecture
------------
The system follows a two-layer design:
- C++ Layer (PyCombatEvents): Hooks game packets and pushes raw events to a thread-safe queue.
  This runs in the game thread and must be fast, so it does minimal processing.
- Python Layer (this module): Polls the C++ queue each frame, maintains state tracking,
  and dispatches callbacks to user-registered handlers. All game logic lives here.

Quick Start
-----------
    from Py4GWCoreLib.native_src.events import CombatEvents

    # 1. Initialize the system (call once at startup)
    CombatEvents.initialize()

    # 2. Register callbacks for events you care about
    def on_skill_cast(caster_id, skill_id, target_id):
        print(f"Agent {caster_id} is casting skill {skill_id}")

    CombatEvents.on_skill_activated(on_skill_cast)

    # 3. Call update() every frame in your main loop
    def main():
        CombatEvents.update()  # Process events and dispatch callbacks

    # 4. Optionally query state at any time
    if CombatEvents.is_agent_casting(player_id):
        skill = CombatEvents.get_casting_skill(player_id)

Available Callbacks
-------------------
Skill Events:
    - on_skill_activated(caster_id, skill_id, target_id) - Skill cast started
    - on_skill_finished(agent_id, skill_id) - Skill cast completed successfully
    - on_skill_interrupted(agent_id, skill_id) - Skill was interrupted
    - on_instant_skill_activated(caster_id, skill_id, target_id) - Instant cast skill used

Attack Events:
    - on_attack_started(attacker_id, target_id) - Auto-attack started
    - on_attack_finished(attacker_id, target_id) - Auto-attack finished

Aftercast Events (KEY FOR COMBAT ROUTINES):
    - on_casting_started(agent_id) - Agent became disabled (casting animation)
    - on_casting_ended(agent_id) - Cast animation finished (brief enabled moment)
    - on_aftercast_started(agent_id) - True aftercast began (disabled again)
    - on_aftercast_ended(agent_id) - Aftercast ended, agent CAN ACT NOW

Damage Events:
    - on_damage(target_id, source_id, amount, skill_id) - Damage dealt
    - on_critical_hit(target_id, source_id, amount, skill_id) - Critical hit damage

Effect Events:
    - on_buff_applied(agent_id, skill_id) - Buff/effect gained (requires track_agent_effects)
    - on_buff_removed(agent_id, skill_id) - Buff/effect lost (requires track_agent_effects)
    - on_condition_applied(target_id, skill_id, caster_id) - Condition gained
    - on_hex_applied(target_id, skill_id, caster_id) - Hex gained
    - on_enchant_applied(target_id, skill_id, caster_id) - Enchantment gained

Stance Events:
    - on_stance_activated(agent_id, skill_id, duration) - Stance skill used
    - on_stance_ended(agent_id, skill_id) - Stance expired or was replaced

Other Events:
    - on_knockdown(agent_id, duration) - Agent knocked down
    - on_energy_gained(agent_id, amount) - Energy gained
    - on_energy_spent(agent_id, amount) - Energy spent

State Query Functions
---------------------
    - is_agent_casting(agent_id) -> bool
    - get_casting_skill(agent_id) -> int (skill_id or 0)
    - get_cast_progress(agent_id) -> float (0.0-1.0, -1 if not casting)
    - is_agent_attacking(agent_id) -> bool
    - is_agent_in_aftercast(agent_id) -> bool
    - can_agent_act(agent_id) -> bool (not disabled, not knocked down)
    - is_agent_knocked_down(agent_id) -> bool
    - has_active_stance(agent_id) -> bool
    - get_agents_targeting(target_id) -> List[int]

Effect Tracking
---------------
To receive buff/condition/hex/enchant callbacks for an agent, you must track them:

    # Track player and current target
    CombatEvents.track_agent_effects(player_id)
    CombatEvents.track_agent_effects(target_id)

    # Now you'll receive callbacks when their effects change
    CombatEvents.on_buff_applied(lambda agent, skill: print(f"Buff {skill} applied!"))

Damage Attribution
------------------
The system attempts to attribute damage to the skill that caused it. This works well for:
- Direct damage skills (Flare, Lightning Orb, etc.)
- Attack skills (Jagged Strike, Wild Blow, etc.)
- Delayed damage (Lightning Surge hex damage after 3 seconds)

Note: If multiple skills are cast quickly, attribution may not be 100% accurate for
delayed damage effects, as we cannot track individual effect instances.

See Also
--------
- CombatEventsTester.py in Bots/HSTools for a complete usage example with damage tracking
- py_combat_events.h/.cpp for C++ packet handling details
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple
from collections import deque
import time

# Import the C++ module
try:
    from Py4GWCoreLib.CombatEvents import EventType, RawCombatEvent, GetCombatEventQueue
    _CPP_AVAILABLE = True
except ImportError:
    _CPP_AVAILABLE = False
    print("[CombatEvents] Warning: PyCombatEvents C++ module not available")


# ============================================================================
# Event Type Constants (mirrored from C++ for convenience)
# ============================================================================

class EventTypes:
    """Combat event type constants - mirrors C++ CombatEventTypes"""
    # Skill events
    SKILL_ACTIVATED = 1
    ATTACK_SKILL_ACTIVATED = 2
    SKILL_STOPPED = 3
    SKILL_FINISHED = 4
    ATTACK_SKILL_FINISHED = 5
    INTERRUPTED = 6
    INSTANT_SKILL_ACTIVATED = 7
    ATTACK_SKILL_STOPPED = 8

    # Attack events
    ATTACK_STARTED = 13
    ATTACK_STOPPED = 14
    MELEE_ATTACK_FINISHED = 15

    # State events
    DISABLED = 16           # Aftercast: value=1 start, value=0 end
    KNOCKED_DOWN = 17       # float_value = duration
    CASTTIME = 18           # float_value = cast time modifier

    # Damage events
    DAMAGE = 30
    CRITICAL = 31
    ARMOR_IGNORING = 32

    # Effect events
    EFFECT_APPLIED = 40
    EFFECT_REMOVED = 41
    EFFECT_ON_TARGET = 42

    # Energy events
    ENERGY_GAINED = 50
    ENERGY_SPENT = 51

    # Skill damage attribution
    SKILL_DAMAGE = 60

    # Pre-notification
    SKILL_ACTIVATE_PACKET = 70


# Skill type constants for stance detection
class SkillTypes:
    """Skill type constants from GWCA"""
    STANCE = 3  # Stance skills


# ============================================================================
# Data Classes for State Tracking
# ============================================================================

@dataclass
class CastingState:
    """Tracks an agent's current casting state"""
    agent_id: int
    skill_id: int
    target_id: int = 0
    start_time: int = 0  # GetTickCount timestamp
    duration: float = 0.0
    is_attack_skill: bool = False


@dataclass
class AttackState:
    """Tracks an agent's current attack state"""
    attacker_id: int
    target_id: int
    start_time: int = 0
    is_skill_attack: bool = False
    skill_id: int = 0


@dataclass
class KnockdownState:
    """Tracks an agent's knockdown state"""
    agent_id: int
    duration: float  # seconds
    start_time: int = 0  # GetTickCount timestamp


@dataclass
class SkillEventData:
    """Detailed skill event for history"""
    timestamp: int
    caster_id: int
    target_id: int
    skill_id: int
    cast_duration: float
    is_attack_skill: bool
    event_type: int


@dataclass
class DamageEventData:
    """Detailed damage event for history"""
    timestamp: int
    target_id: int
    source_id: int
    value: float
    skill_id: int
    is_critical: bool


@dataclass
class TrackedEffect:
    """Represents an effect being tracked on an agent"""
    skill_id: int
    agent_id: int  # Who has the effect
    attribute_level: int
    duration: float
    time_remaining: int


# ============================================================================
# Callback Type Definitions
# ============================================================================

# Callback signatures:
# SkillCallback = Callable[[caster_id, skill_id, target_id], None]
# SkillFinishCallback = Callable[[agent_id, skill_id], None]
# AttackCallback = Callable[[attacker_id, target_id], None]
# AftercastCallback = Callable[[agent_id], None]
# KnockdownCallback = Callable[[agent_id, duration], None]
# DamageCallback = Callable[[target_id, source_id, amount, skill_id], None]
# EffectCallback = Callable[[agent_id, effect_id], None]
# EnergyCallback = Callable[[agent_id, amount], None]


# ============================================================================
# Main CombatEvents Class
# ============================================================================

class CombatEvents:
    """
    Main combat events handler.

    Polls C++ event queue each frame and:
    - Updates internal state tracking
    - Dispatches callbacks to registered handlers
    - Maintains event history for queries
    """

    # Singleton state
    _initialized: bool = False
    _queue = None  # CombatEventQueue from C++

    # State tracking
    _current_casts: Dict[int, CastingState] = {}
    _current_attacks: Dict[int, AttackState] = {}
    _knockdowns: Dict[int, KnockdownState] = {}
    _disabled_state: Dict[int, bool] = {}  # agent_id -> is_disabled (can't act)
    _in_aftercast: Dict[int, bool] = {}  # agent_id -> is_in_true_aftercast (after skill finished)
    _pending_skill_ids: Dict[int, int] = {}  # agent_id -> skill_id
    _last_damage_skill: Dict[int, int] = {}  # target_agent_id -> skill_id (from skill_damage packet)

    # Event history
    _skill_history: deque = deque(maxlen=500)
    _damage_history: deque = deque(maxlen=500)

    # Callbacks
    _on_skill_activated: List[Callable] = []
    _on_skill_finished: List[Callable] = []
    _on_skill_interrupted: List[Callable] = []
    _on_instant_skill: List[Callable] = []
    _on_attack_started: List[Callable] = []
    _on_attack_finished: List[Callable] = []
    _on_casting_started: List[Callable] = []  # Agent started casting (disabled during cast)
    _on_casting_ended: List[Callable] = []    # Agent finished casting (brief enabled moment)
    _on_aftercast_started: List[Callable] = []  # True aftercast started (disabled after cast)
    _on_aftercast_ended: List[Callable] = []    # True aftercast ended (can act now)
    _on_knockdown: List[Callable] = []
    _on_damage: List[Callable] = []
    _on_critical_hit: List[Callable] = []
    _on_effect_applied: List[Callable] = []  # Internal visual effect IDs (not very useful)
    _on_effect_removed: List[Callable] = []  # Internal visual effect IDs (not very useful)
    _on_skill_effect_applied: List[Callable] = []  # From effect_on_target packet
    _on_buff_applied: List[Callable] = []   # Actual buff/effect gained (from EffectArray polling)
    _on_buff_removed: List[Callable] = []   # Actual buff/effect lost (from EffectArray polling)
    _on_energy_gained: List[Callable] = []
    _on_energy_spent: List[Callable] = []
    _on_condition_applied: List[Callable] = []  # Specific skill caused condition
    _on_hex_applied: List[Callable] = []  # Specific skill caused hex
    _on_enchant_applied: List[Callable] = []  # Specific skill caused enchantment
    _on_condition_removed: List[Callable] = []  # Agent lost all conditions
    _on_hex_removed: List[Callable] = []  # Agent lost all hexes
    _on_enchant_removed: List[Callable] = []  # Agent lost all enchantments
    _on_stance_activated: List[Callable] = []  # Agent used a stance skill
    _on_stance_ended: List[Callable] = []  # Stance expired or was replaced

    # Effect tracking state (for polling-based detection)
    _tracked_agents: Set[int] = set()  # Agents we're tracking effects for
    _agent_effects: Dict[int, Set[int]] = {}  # agent_id -> set of skill_ids currently active

    # Agent state tracking (condition/hex/enchant) - polled from Agent.py
    _agent_condition_state: Dict[int, bool] = {}  # agent_id -> has_condition
    _agent_hex_state: Dict[int, bool] = {}  # agent_id -> has_hex
    _agent_enchant_state: Dict[int, bool] = {}  # agent_id -> has_enchant

    # Stance tracking - active stances on enemies
    # Format: {agent_id: (skill_id, timestamp, estimated_end_time)}
    _active_stances: Dict[int, Tuple[int, int, int]] = {}

    # Skill-to-state correlation tracking
    # When a skill finishes on a target, we record it here to correlate with state changes
    # Format: {target_id: [(timestamp, skill_id, caster_id), ...]}
    _recent_skills_on_target: Dict[int, List[Tuple[int, int, int]]] = {}
    _skill_correlation_window_ms: int = 500  # Time window to correlate skill->state change

    # Recent skills cast by each agent (for damage attribution)
    # Format: {agent_id: [(timestamp, skill_id, target_id, is_attack_skill), ...]}
    _recent_skills_by_caster: Dict[int, List[Tuple[int, int, int, bool]]] = {}
    _damage_attribution_window_ms: int = 5000  # 5 seconds for delayed damage skills like hexes

    # ========================================================================
    # Lifecycle
    # ========================================================================

    @classmethod
    def initialize(cls) -> bool:
        import PyCombatEvents
        """Initialize the combat events system. Call once at startup."""
        if cls._initialized:
            return True

        if not _CPP_AVAILABLE:
            print("[CombatEvents] Cannot initialize - C++ module not available")
            return False

        cls._queue = PyCombatEvents.GetCombatEventQueue()
        cls._queue.Initialize()
        cls._initialized = True
        cls._clear_state()
        return True

    @classmethod
    def terminate(cls):
        """Terminate the combat events system."""
        if cls._queue:
            cls._queue.Terminate()
        cls._initialized = False
        cls._clear_state()

    @classmethod
    def _clear_state(cls):
        """Clear all tracked state."""
        cls._current_casts = {}
        cls._current_attacks = {}
        cls._knockdowns = {}
        cls._disabled_state = {}
        cls._in_aftercast = {}
        cls._pending_skill_ids = {}
        cls._last_damage_skill = {}
        cls._skill_history = deque(maxlen=500)
        cls._damage_history = deque(maxlen=500)
        cls._tracked_agents = set()
        cls._agent_effects = {}
        cls._agent_condition_state = {}
        cls._agent_hex_state = {}
        cls._agent_enchant_state = {}
        cls._active_stances = {}
        cls._recent_skills_on_target = {}
        cls._recent_skills_by_caster = {}

    @classmethod
    def clear_callbacks(cls):
        """Clear all registered callbacks."""
        cls._on_skill_activated = []
        cls._on_skill_finished = []
        cls._on_skill_interrupted = []
        cls._on_instant_skill = []
        cls._on_attack_started = []
        cls._on_attack_finished = []
        cls._on_casting_started = []
        cls._on_casting_ended = []
        cls._on_aftercast_started = []
        cls._on_aftercast_ended = []
        cls._on_knockdown = []
        cls._on_damage = []
        cls._on_critical_hit = []
        cls._on_effect_applied = []
        cls._on_effect_removed = []
        cls._on_skill_effect_applied = []
        cls._on_buff_applied = []
        cls._on_buff_removed = []
        cls._on_energy_gained = []
        cls._on_energy_spent = []
        cls._on_condition_applied = []
        cls._on_hex_applied = []
        cls._on_enchant_applied = []
        cls._on_condition_removed = []
        cls._on_hex_removed = []
        cls._on_enchant_removed = []
        cls._on_stance_activated = []
        cls._on_stance_ended = []

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the combat events system is initialized."""
        return cls._initialized

    # ========================================================================
    # Main Update Loop - Call Each Frame
    # ========================================================================

    @classmethod
    def update(cls):
        """
        Process all pending combat events. Call this each frame.

        This is the core method that:
        1. Gets events from C++ queue
        2. Updates internal state
        3. Dispatches callbacks
        4. Polls effect arrays for tracked agents
        5. Polls agent states for condition/hex/enchant changes
        6. Checks for expired stances
        """
        if not cls._initialized or not cls._queue:
            return

        events = cls._queue.GetAndClearEvents()

        for event in events:
            cls._process_event(event)

        # Poll effect arrays for tracked agents
        cls._poll_effects()

        # Poll agent states for condition/hex/enchant changes
        cls._poll_agent_states()

        # Check for expired stances
        cls._check_expired_stances()

    @classmethod
    def _process_event(cls, event):
        """Process a single raw combat event."""
        ts = event.timestamp
        etype = event.event_type
        agent_id = event.agent_id
        value = event.value
        target_id = event.target_id
        float_val = event.float_value

        # ---- Skill Activation Events ----
        if etype == EventTypes.SKILL_ACTIVATE_PACKET:
            # Pre-notification of skill activation
            cls._pending_skill_ids[agent_id] = value

        elif etype == EventTypes.SKILL_ACTIVATED:
            skill_id = value
            cls._current_casts[agent_id] = CastingState(
                agent_id=agent_id,
                skill_id=skill_id,
                target_id=target_id,
                start_time=ts,
                duration=0.0,
                is_attack_skill=False
            )
            cls._pending_skill_ids[agent_id] = skill_id

            # Record skill for damage attribution (works for delayed damage like hexes)
            cls._record_skill_by_caster(ts, agent_id, skill_id, target_id, False)

            # Add to history
            cls._skill_history.append(SkillEventData(
                timestamp=ts, caster_id=agent_id, target_id=target_id,
                skill_id=skill_id, cast_duration=0.0, is_attack_skill=False,
                event_type=etype
            ))

            # Check if this is a stance skill (track enemy stances)
            cls._check_stance_activation(ts, agent_id, skill_id)

            # Dispatch callbacks
            cls._invoke_callbacks(cls._on_skill_activated, agent_id, skill_id, target_id)

        elif etype == EventTypes.ATTACK_SKILL_ACTIVATED:
            skill_id = value
            cls._current_casts[agent_id] = CastingState(
                agent_id=agent_id,
                skill_id=skill_id,
                target_id=target_id,
                start_time=ts,
                duration=0.0,
                is_attack_skill=True
            )
            cls._current_attacks[agent_id] = AttackState(
                attacker_id=agent_id,
                target_id=target_id,
                start_time=ts,
                is_skill_attack=True,
                skill_id=skill_id
            )
            cls._pending_skill_ids[agent_id] = skill_id

            # Record attack skill for damage attribution
            cls._record_skill_by_caster(ts, agent_id, skill_id, target_id, True)

            cls._skill_history.append(SkillEventData(
                timestamp=ts, caster_id=agent_id, target_id=target_id,
                skill_id=skill_id, cast_duration=0.0, is_attack_skill=True,
                event_type=etype
            ))

            cls._invoke_callbacks(cls._on_skill_activated, agent_id, skill_id, target_id)

        elif etype == EventTypes.INSTANT_SKILL_ACTIVATED:
            skill_id = value

            # Record instant skill for damage attribution
            cls._record_skill_by_caster(ts, agent_id, skill_id, target_id, False)

            cls._skill_history.append(SkillEventData(
                timestamp=ts, caster_id=agent_id, target_id=target_id,
                skill_id=skill_id, cast_duration=0.0, is_attack_skill=False,
                event_type=etype
            ))
            # Stances are often instant cast, so check here too
            cls._check_stance_activation(ts, agent_id, skill_id)
            cls._invoke_callbacks(cls._on_instant_skill, agent_id, skill_id, target_id)

        # ---- Skill Finish Events ----
        elif etype == EventTypes.SKILL_FINISHED:
            skill_id = cls._get_pending_skill_id(agent_id)
            cls._current_casts.pop(agent_id, None)

            cls._skill_history.append(SkillEventData(
                timestamp=ts, caster_id=agent_id, target_id=0,
                skill_id=skill_id, cast_duration=0.0, is_attack_skill=False,
                event_type=etype
            ))
            cls._invoke_callbacks(cls._on_skill_finished, agent_id, skill_id)

        elif etype == EventTypes.ATTACK_SKILL_FINISHED:
            skill_id = cls._get_pending_skill_id(agent_id)
            cls._current_casts.pop(agent_id, None)
            cls._current_attacks.pop(agent_id, None)

            cls._skill_history.append(SkillEventData(
                timestamp=ts, caster_id=agent_id, target_id=0,
                skill_id=skill_id, cast_duration=0.0, is_attack_skill=True,
                event_type=etype
            ))
            cls._invoke_callbacks(cls._on_skill_finished, agent_id, skill_id)

        elif etype == EventTypes.SKILL_STOPPED:
            skill_id = cls._get_pending_skill_id(agent_id)
            cls._current_casts.pop(agent_id, None)

            cls._skill_history.append(SkillEventData(
                timestamp=ts, caster_id=agent_id, target_id=0,
                skill_id=skill_id, cast_duration=0.0, is_attack_skill=False,
                event_type=etype
            ))

        elif etype == EventTypes.ATTACK_SKILL_STOPPED:
            skill_id = cls._get_pending_skill_id(agent_id)
            cls._current_casts.pop(agent_id, None)
            cls._current_attacks.pop(agent_id, None)

        elif etype == EventTypes.INTERRUPTED:
            skill_id = cls._get_pending_skill_id(agent_id)
            cls._current_casts.pop(agent_id, None)
            cls._current_attacks.pop(agent_id, None)

            cls._skill_history.append(SkillEventData(
                timestamp=ts, caster_id=agent_id, target_id=0,
                skill_id=skill_id, cast_duration=0.0, is_attack_skill=False,
                event_type=etype
            ))
            cls._invoke_callbacks(cls._on_skill_interrupted, agent_id, skill_id)

        # ---- Attack Events ----
        elif etype == EventTypes.ATTACK_STARTED:
            cls._current_attacks[agent_id] = AttackState(
                attacker_id=agent_id,
                target_id=target_id,
                start_time=ts,
                is_skill_attack=False,
                skill_id=0
            )
            cls._invoke_callbacks(cls._on_attack_started, agent_id, target_id)

        elif etype in (EventTypes.ATTACK_STOPPED, EventTypes.MELEE_ATTACK_FINISHED):
            attack = cls._current_attacks.pop(agent_id, None)
            attack_target = attack.target_id if attack else 0
            cls._invoke_callbacks(cls._on_attack_finished, agent_id, attack_target)

        # ---- Disabled Events (Cast-lock and Aftercast) ----
        # The DISABLED packet fires multiple times during a skill:
        # 1. disabled=1 when cast starts (cast-lock)
        # 2. disabled=0 when cast finishes (brief enabled moment)
        # 3. disabled=1 when aftercast starts (true aftercast)
        # 4. disabled=0 when aftercast ends (can truly act)
        elif etype == EventTypes.DISABLED:
            is_disabled = (value == 1)
            was_disabled = cls._disabled_state.get(agent_id, False)
            is_casting = agent_id in cls._current_casts
            was_in_aftercast = cls._in_aftercast.get(agent_id, False)

            cls._disabled_state[agent_id] = is_disabled

            if is_disabled:
                # Becoming disabled
                if is_casting:
                    # We're casting, so this is cast-lock (not aftercast yet)
                    cls._in_aftercast[agent_id] = False
                    cls._invoke_callbacks(cls._on_casting_started, agent_id)
                else:
                    # Not casting, so this is true aftercast starting
                    cls._in_aftercast[agent_id] = True
                    cls._invoke_callbacks(cls._on_aftercast_started, agent_id)
            else:
                # Becoming enabled
                if was_in_aftercast:
                    # We were in aftercast, now we can truly act
                    cls._in_aftercast[agent_id] = False
                    cls._invoke_callbacks(cls._on_aftercast_ended, agent_id)
                elif is_casting or was_disabled:
                    # Cast just finished (brief enabled moment before aftercast)
                    cls._invoke_callbacks(cls._on_casting_ended, agent_id)

        # ---- Knockdown Events ----
        elif etype == EventTypes.KNOCKED_DOWN:
            duration = float_val
            cls._knockdowns[agent_id] = KnockdownState(
                agent_id=agent_id,
                duration=duration,
                start_time=ts
            )
            cls._invoke_callbacks(cls._on_knockdown, agent_id, duration)

        # ---- Cast Time Modifier ----
        elif etype == EventTypes.CASTTIME:
            if agent_id in cls._current_casts:
                cls._current_casts[agent_id].duration = float_val

        # ---- Damage Events ----
        # For GenericModifier damage packets:
        #   agent_id = target (who receives damage)
        #   target_id = source (who deals damage)
        #   float_val = damage as fraction of max HP
        elif etype == EventTypes.DAMAGE:
            source_id = target_id  # target_id in the event is actually the source
            actual_target_id = agent_id  # agent_id is who receives damage
            skill_id = cls._get_damage_skill_id(actual_target_id, source_id)
            cls._damage_history.append(DamageEventData(
                timestamp=ts, target_id=actual_target_id, source_id=source_id,
                value=float_val, skill_id=skill_id, is_critical=False
            ))
            cls._invoke_callbacks(cls._on_damage, actual_target_id, source_id, float_val, skill_id)

        elif etype == EventTypes.CRITICAL:
            source_id = target_id
            actual_target_id = agent_id
            skill_id = cls._get_damage_skill_id(actual_target_id, source_id)
            cls._damage_history.append(DamageEventData(
                timestamp=ts, target_id=actual_target_id, source_id=source_id,
                value=float_val, skill_id=skill_id, is_critical=True
            ))
            cls._invoke_callbacks(cls._on_critical_hit, actual_target_id, source_id, float_val, skill_id)

        elif etype == EventTypes.ARMOR_IGNORING:
            source_id = target_id
            actual_target_id = agent_id
            skill_id = cls._get_damage_skill_id(actual_target_id, source_id)
            cls._damage_history.append(DamageEventData(
                timestamp=ts, target_id=actual_target_id, source_id=source_id,
                value=float_val, skill_id=skill_id, is_critical=False
            ))
            cls._invoke_callbacks(cls._on_damage, actual_target_id, source_id, float_val, skill_id)

        # ---- Effect Events ----
        elif etype == EventTypes.EFFECT_APPLIED:
            cls._invoke_callbacks(cls._on_effect_applied, agent_id, value)

        elif etype == EventTypes.EFFECT_REMOVED:
            cls._invoke_callbacks(cls._on_effect_removed, agent_id, value)

        elif etype == EventTypes.EFFECT_ON_TARGET:
            # This is when an effect hits a target
            # agent_id = caster, value = effect_id (NOT skill_id!), target_id = target
            effect_id = value

            # Look up the actual skill ID from the caster's current/recent cast
            skill_id = 0
            if agent_id in cls._current_casts:
                cast = cls._current_casts[agent_id]
                skill_id = cast.skill_id
                # Update target info for ongoing casts
                if cast.target_id == 0:
                    cast.target_id = target_id
            elif agent_id in cls._pending_skill_ids:
                skill_id = cls._pending_skill_ids[agent_id]

            # Record this skill hitting this target for state change correlation
            if skill_id and target_id:
                cls._record_skill_on_target(ts, target_id, skill_id, agent_id)

            # Dispatch callback with the actual skill_id (0 if unknown)
            # Also pass effect_id as additional info
            cls._invoke_callbacks(cls._on_skill_effect_applied, agent_id, skill_id, target_id, effect_id)

        # ---- Energy Events ----
        elif etype == EventTypes.ENERGY_GAINED:
            cls._invoke_callbacks(cls._on_energy_gained, agent_id, float_val)

        elif etype == EventTypes.ENERGY_SPENT:
            cls._invoke_callbacks(cls._on_energy_spent, agent_id, float_val)

        # ---- Skill Damage Attribution ----
        elif etype == EventTypes.SKILL_DAMAGE:
            cls._last_damage_skill[agent_id] = value

    @classmethod
    def _get_pending_skill_id(cls, agent_id: int) -> int:
        """Get the pending skill ID for an agent."""
        if agent_id in cls._pending_skill_ids:
            return cls._pending_skill_ids[agent_id]
        if agent_id in cls._current_casts:
            return cls._current_casts[agent_id].skill_id
        return 0

    @classmethod
    def _get_damage_skill_id(cls, target_id: int, source_id: int) -> int:
        """Get the skill ID that caused damage.

        Args:
            target_id: The agent receiving damage
            source_id: The agent dealing damage

        The skill_damage packet is sent to the TARGET with the skill ID,
        so we look up by target first. As fallback, check source's current cast/attack,
        then check recent skills for delayed damage attribution.
        """
        import ctypes
        kernel32 = ctypes.windll.kernel32
        now = kernel32.GetTickCount()

        # Check last_damage_skill by TARGET (skill_damage packet is sent to target)
        if target_id in cls._last_damage_skill and cls._last_damage_skill[target_id] != 0:
            skill_id = cls._last_damage_skill[target_id]
            # Clear it after use to avoid stale attribution
            cls._last_damage_skill[target_id] = 0
            return skill_id

        # Fallback: Check source's current attacks (for skills still in progress)
        if source_id in cls._current_attacks:
            attack = cls._current_attacks[source_id]
            if attack.is_skill_attack and attack.skill_id:
                return attack.skill_id

        # Fallback: Check source's current casts (for skills still in progress)
        if source_id in cls._current_casts:
            cast = cls._current_casts[source_id]
            if cast.skill_id:
                return cast.skill_id

        # Fallback: Check recent skills by this source for delayed damage attribution
        # This handles attack skills (damage arrives after skill finishes) and
        # delayed damage skills like Lightning Surge (hex damage after 3 seconds)
        recent_skill = cls._get_recent_skill_by_caster(now, source_id, target_id)
        if recent_skill:
            return recent_skill

        return 0

    @classmethod
    def _invoke_callbacks(cls, callbacks: List[Callable], *args):
        """Safely invoke all callbacks in a list."""
        for cb in callbacks:
            try:
                cb(*args)
            except Exception as e:
                print(f"[CombatEvents] Callback error: {e}")

    @classmethod
    def _check_stance_activation(cls, timestamp: int, caster_id: int, skill_id: int):
        """Check if a skill is a Stance and track it."""
        try:
            # Import Skill module to check skill type
            from .Skill import Skill
            skill_type_id, skill_type_name = Skill.GetType(skill_id)

            if skill_type_id == SkillTypes.STANCE:
                # Get stance duration from skill data
                # GetDuration returns (duration_0pts, duration_15pts)
                duration_tuple = Skill.Attribute.GetDuration(skill_id)
                # Use duration at 15 pts as estimate (most stances scale with attribute)
                duration_seconds = duration_tuple[1] if duration_tuple[1] > 0 else duration_tuple[0]
                if duration_seconds <= 0:
                    duration_seconds = 10.0  # Default estimate if no duration found

                # Convert to ms and calculate end time
                duration_ms = int(duration_seconds * 1000)
                estimated_end = timestamp + duration_ms

                # Check if agent already has a stance (it will be replaced)
                if caster_id in cls._active_stances:
                    old_stance = cls._active_stances[caster_id]
                    cls._invoke_callbacks(cls._on_stance_ended, caster_id, old_stance[0])

                # Record new stance
                cls._active_stances[caster_id] = (skill_id, timestamp, estimated_end)
                cls._invoke_callbacks(cls._on_stance_activated, caster_id, skill_id, duration_seconds)
        except Exception as e:
            # Skill module might not be available, silently ignore
            pass

    @classmethod
    def _record_skill_on_target(cls, timestamp: int, target_id: int, skill_id: int, caster_id: int):
        """Record that a skill was applied to a target for state change correlation."""
        if target_id not in cls._recent_skills_on_target:
            cls._recent_skills_on_target[target_id] = []

        cls._recent_skills_on_target[target_id].append((timestamp, skill_id, caster_id))

        # Cleanup: Keep only recent entries (within correlation window)
        cutoff = timestamp - cls._skill_correlation_window_ms
        cls._recent_skills_on_target[target_id] = [
            entry for entry in cls._recent_skills_on_target[target_id]
            if entry[0] >= cutoff
        ]

    @classmethod
    def _record_skill_by_caster(cls, timestamp: int, caster_id: int, skill_id: int, target_id: int, is_attack_skill: bool):
        """Record a skill cast by an agent for damage attribution."""
        if caster_id not in cls._recent_skills_by_caster:
            cls._recent_skills_by_caster[caster_id] = []

        cls._recent_skills_by_caster[caster_id].append((timestamp, skill_id, target_id, is_attack_skill))

        # Cleanup: Keep only recent entries (within damage attribution window)
        cutoff = timestamp - cls._damage_attribution_window_ms
        cls._recent_skills_by_caster[caster_id] = [
            entry for entry in cls._recent_skills_by_caster[caster_id]
            if entry[0] >= cutoff
        ]

    @classmethod
    def _get_recent_skill_by_caster(cls, timestamp: int, caster_id: int, target_id: int = 0) -> int:
        """Get the most recent skill cast by an agent within the damage attribution window.

        Args:
            timestamp: Current timestamp
            caster_id: The agent who cast the skill
            target_id: Optional - if provided, prefer skills that targeted this agent

        Returns:
            Skill ID or 0 if no recent skill found
        """
        if caster_id not in cls._recent_skills_by_caster:
            return 0

        cutoff = timestamp - cls._damage_attribution_window_ms
        recent = [
            entry for entry in cls._recent_skills_by_caster[caster_id]
            if entry[0] >= cutoff
        ]

        if not recent:
            return 0

        # If target_id is provided, prefer skills that hit that target
        if target_id:
            # First look for skills that hit this specific target
            for ts, skill_id, skill_target, is_attack in reversed(recent):
                if skill_target == target_id:
                    return skill_id

        # Return the most recent skill (last entry)
        return recent[-1][1]

    @classmethod
    def _get_recent_skill_on_target(cls, timestamp: int, target_id: int) -> Optional[Tuple[int, int]]:
        """Get the most recent skill that hit a target within the correlation window.

        Returns:
            Tuple of (skill_id, caster_id) or None if no recent skill found
        """
        if target_id not in cls._recent_skills_on_target:
            return None

        cutoff = timestamp - cls._skill_correlation_window_ms
        recent = [
            entry for entry in cls._recent_skills_on_target[target_id]
            if entry[0] >= cutoff
        ]

        if not recent:
            return None

        # Return the most recent (last) entry
        most_recent = recent[-1]
        return (most_recent[1], most_recent[2])  # (skill_id, caster_id)

    @classmethod
    def _poll_effects(cls):
        """Poll effect arrays for tracked agents and detect changes."""
        if not cls._tracked_agents:
            return

        try:
            import PyEffects
        except ImportError:
            return

        for agent_id in list(cls._tracked_agents):
            try:
                effects = PyEffects.PyEffects(agent_id)
                current_effects = set()

                # Get all current effect skill IDs
                for effect in effects.GetEffects():
                    current_effects.add(effect.skill_id)
                for buff in effects.GetBuffs():
                    current_effects.add(buff.skill_id)

                # Get previous effects
                previous_effects = cls._agent_effects.get(agent_id, set())

                # Detect new effects (applied)
                new_effects = current_effects - previous_effects
                for skill_id in new_effects:
                    cls._invoke_callbacks(cls._on_buff_applied, agent_id, skill_id)

                # Detect removed effects
                removed_effects = previous_effects - current_effects
                for skill_id in removed_effects:
                    cls._invoke_callbacks(cls._on_buff_removed, agent_id, skill_id)

                # Update stored state
                cls._agent_effects[agent_id] = current_effects

            except Exception:
                # Agent might be invalid, remove from tracking
                pass

    @classmethod
    def _poll_agent_states(cls):
        """Poll agent states for condition/hex/enchant changes using Agent.py.

        This polls tracked agents for state changes and fires callbacks when
        conditions, hexes, or enchantments are applied or removed.
        """
        if not cls._tracked_agents:
            return

        try:
            from .Agent import Agent
        except ImportError:
            return

        import ctypes
        kernel32 = ctypes.windll.kernel32
        now = kernel32.GetTickCount()

        for agent_id in list(cls._tracked_agents):
            try:
                # Get current state from Agent.py
                has_cond = Agent.IsConditioned(agent_id)
                has_hex = Agent.IsHexed(agent_id)
                has_ench = Agent.IsEnchanted(agent_id)

                # Get previous state
                had_cond = cls._agent_condition_state.get(agent_id, False)
                had_hex = cls._agent_hex_state.get(agent_id, False)
                had_ench = cls._agent_enchant_state.get(agent_id, False)

                # Try to find which skill caused the state change
                recent_skill = cls._get_recent_skill_on_target(now, agent_id)
                skill_id = recent_skill[0] if recent_skill else 0
                caster_id = recent_skill[1] if recent_skill else 0

                # Fire callbacks for state changes
                if has_cond and not had_cond:
                    cls._invoke_callbacks(cls._on_condition_applied, agent_id, skill_id, caster_id)
                elif had_cond and not has_cond:
                    cls._invoke_callbacks(cls._on_condition_removed, agent_id)

                if has_hex and not had_hex:
                    cls._invoke_callbacks(cls._on_hex_applied, agent_id, skill_id, caster_id)
                elif had_hex and not has_hex:
                    cls._invoke_callbacks(cls._on_hex_removed, agent_id)

                if has_ench and not had_ench:
                    cls._invoke_callbacks(cls._on_enchant_applied, agent_id, skill_id, caster_id)
                elif had_ench and not has_ench:
                    cls._invoke_callbacks(cls._on_enchant_removed, agent_id)

                # Update stored state
                cls._agent_condition_state[agent_id] = has_cond
                cls._agent_hex_state[agent_id] = has_hex
                cls._agent_enchant_state[agent_id] = has_ench

            except Exception:
                # Agent might be invalid
                pass

    @classmethod
    def _check_expired_stances(cls):
        """Check for stances that have expired based on estimated duration."""
        if not cls._active_stances:
            return

        import ctypes
        kernel32 = ctypes.windll.kernel32
        now = kernel32.GetTickCount()

        expired = []
        for agent_id, (skill_id, start_time, estimated_end) in cls._active_stances.items():
            if now >= estimated_end:
                expired.append((agent_id, skill_id))

        for agent_id, skill_id in expired:
            del cls._active_stances[agent_id]
            cls._invoke_callbacks(cls._on_stance_ended, agent_id, skill_id)

    # ========================================================================
    # Effect Tracking Management
    # ========================================================================

    @classmethod
    def track_agent_effects(cls, agent_id: int):
        """Start tracking effects for an agent. Call this to receive buff_applied/buff_removed callbacks."""
        cls._tracked_agents.add(agent_id)
        # Initialize with current effects
        try:
            import PyEffects
            effects = PyEffects.PyEffects(agent_id)
            current_effects = set()
            for effect in effects.GetEffects():
                current_effects.add(effect.skill_id)
            for buff in effects.GetBuffs():
                current_effects.add(buff.skill_id)
            cls._agent_effects[agent_id] = current_effects
        except Exception:
            cls._agent_effects[agent_id] = set()

    @classmethod
    def untrack_agent_effects(cls, agent_id: int):
        """Stop tracking effects for an agent."""
        cls._tracked_agents.discard(agent_id)
        cls._agent_effects.pop(agent_id, None)

    @classmethod
    def get_tracked_agents(cls) -> Set[int]:
        """Get the set of agents being tracked for effect changes."""
        return cls._tracked_agents.copy()

    @classmethod
    def is_tracking_agent(cls, agent_id: int) -> bool:
        """Check if an agent is being tracked for effect changes."""
        return agent_id in cls._tracked_agents

    # ========================================================================
    # Callback Registration
    # ========================================================================

    @classmethod
    def on_skill_activated(cls, callback: Callable[[int, int, int], None]):
        """Register callback for skill activation. Args: (caster_id, skill_id, target_id)"""
        cls._on_skill_activated.append(callback)

    @classmethod
    def on_skill_finished(cls, callback: Callable[[int, int], None]):
        """Register callback for skill completion. Args: (agent_id, skill_id)"""
        cls._on_skill_finished.append(callback)

    @classmethod
    def on_skill_interrupted(cls, callback: Callable[[int, int], None]):
        """Register callback for skill interruption. Args: (agent_id, skill_id)"""
        cls._on_skill_interrupted.append(callback)

    @classmethod
    def on_instant_skill_activated(cls, callback: Callable[[int, int, int], None]):
        """Register callback for instant skills. Args: (caster_id, skill_id, target_id)"""
        cls._on_instant_skill.append(callback)

    @classmethod
    def on_attack_started(cls, callback: Callable[[int, int], None]):
        """Register callback for attack start. Args: (attacker_id, target_id)"""
        cls._on_attack_started.append(callback)

    @classmethod
    def on_attack_finished(cls, callback: Callable[[int, int], None]):
        """Register callback for attack finish. Args: (attacker_id, target_id)"""
        cls._on_attack_finished.append(callback)

    @classmethod
    def on_casting_started(cls, callback: Callable[[int], None]):
        """Register callback for when agent becomes disabled during casting. Args: (agent_id,)

        This fires when an agent starts casting and becomes unable to use other skills.
        """
        cls._on_casting_started.append(callback)

    @classmethod
    def on_casting_ended(cls, callback: Callable[[int], None]):
        """Register callback for when casting animation finishes. Args: (agent_id,)

        This fires when the cast animation completes, but BEFORE aftercast.
        The agent is briefly enabled but will immediately enter aftercast.
        """
        cls._on_casting_ended.append(callback)

    @classmethod
    def on_aftercast_started(cls, callback: Callable[[int], None]):
        """Register callback for TRUE aftercast start. Args: (agent_id,)

        This fires when the actual aftercast begins (after casting is complete).
        The agent cannot use skills during this time.
        """
        cls._on_aftercast_started.append(callback)

    @classmethod
    def on_aftercast_ended(cls, callback: Callable[[int], None]):
        """
        Register callback for TRUE aftercast end. Args: (agent_id,)

        KEY FOR PERFECT COMBAT ROUTINES:
        When this fires, the agent can TRULY use skills again.
        Use this to chain skills with frame-perfect timing.

        This only fires after the real aftercast, not after every disabled state change.
        """
        cls._on_aftercast_ended.append(callback)

    @classmethod
    def on_knockdown(cls, callback: Callable[[int, float], None]):
        """Register callback for knockdown. Args: (agent_id, duration)"""
        cls._on_knockdown.append(callback)

    @classmethod
    def on_damage(cls, callback: Callable[[int, int, float, int], None]):
        """Register callback for damage. Args: (target_id, source_id, amount, skill_id)"""
        cls._on_damage.append(callback)

    @classmethod
    def on_critical_hit(cls, callback: Callable[[int, int, float, int], None]):
        """Register callback for critical hits. Args: (target_id, source_id, amount, skill_id)"""
        cls._on_critical_hit.append(callback)

    @classmethod
    def on_effect_applied(cls, callback: Callable[[int, int], None]):
        """Register callback for visual effect applied. Args: (agent_id, effect_id)

        NOTE: This is for internal visual/animation effect IDs, NOT skill effects.
        For actual skill effects (Bleeding, Burning, etc.), use on_skill_effect_applied().
        """
        cls._on_effect_applied.append(callback)

    @classmethod
    def on_effect_removed(cls, callback: Callable[[int, int], None]):
        """Register callback for visual effect removed. Args: (agent_id, effect_id)

        NOTE: This is for internal visual/animation effect IDs, NOT skill effects.
        """
        cls._on_effect_removed.append(callback)

    @classmethod
    def on_skill_effect_applied(cls, callback: Callable[[int, int, int, int], None]):
        """Register callback for skill effect applied to a target. Args: (caster_id, skill_id, target_id, effect_id)

        This is the useful callback for tracking actual game effects like:
        - Conditions (Bleeding, Burning, Poison, etc.)
        - Hexes
        - Enchantments applied to others
        - Any skill that affects a target

        The skill_id is derived from the caster's current/recent cast (may be 0 if unknown).
        The effect_id is the internal game effect ID (usually not useful directly).
        The skill_id can be looked up with Skill.GetName(skill_id) to get the skill name.
        """
        cls._on_skill_effect_applied.append(callback)

    @classmethod
    def on_buff_applied(cls, callback: Callable[[int, int], None]):
        """Register callback for when a buff/effect is applied to a tracked agent. Args: (agent_id, skill_id)

        This uses polling of the EffectArray to detect actual buff/effect changes.
        Much more reliable than packet-based detection for conditions, hexes, enchantments.

        IMPORTANT: You must call track_agent_effects(agent_id) for agents you want to monitor.
        The skill_id is the actual skill that created the effect (e.g., Bleeding, Burning, etc.)
        """
        cls._on_buff_applied.append(callback)

    @classmethod
    def on_buff_removed(cls, callback: Callable[[int, int], None]):
        """Register callback for when a buff/effect is removed from a tracked agent. Args: (agent_id, skill_id)

        This uses polling of the EffectArray to detect actual buff/effect changes.

        IMPORTANT: You must call track_agent_effects(agent_id) for agents you want to monitor.
        """
        cls._on_buff_removed.append(callback)

    @classmethod
    def on_energy_gained(cls, callback: Callable[[int, float], None]):
        """Register callback for energy gain. Args: (agent_id, amount)"""
        cls._on_energy_gained.append(callback)

    @classmethod
    def on_energy_spent(cls, callback: Callable[[int, float], None]):
        """Register callback for energy spent. Args: (agent_id, amount)"""
        cls._on_energy_spent.append(callback)

    @classmethod
    def on_condition_applied(cls, callback: Callable[[int, int, int], None]):
        """Register callback for when a condition is applied. Args: (target_id, skill_id, caster_id)

        This fires when a TRACKED agent gains any condition (Bleeding, Burning, Poison, etc.).
        Works for enemies too - uses Agent.IsConditioned() which reads the agent's effects bitmap.

        IMPORTANT: You must call track_agent_effects(agent_id) for agents you want to monitor.

        The skill_id and caster_id are determined by correlating with recent skill casts.
        If we can't determine which skill caused it, skill_id and caster_id will be 0.
        """
        cls._on_condition_applied.append(callback)

    @classmethod
    def on_hex_applied(cls, callback: Callable[[int, int, int], None]):
        """Register callback for when a hex is applied. Args: (target_id, skill_id, caster_id)

        This fires when a TRACKED agent gains any hex.
        Works for enemies too - uses Agent.IsHexed() which reads the agent's effects bitmap.

        IMPORTANT: You must call track_agent_effects(agent_id) for agents you want to monitor.

        The skill_id and caster_id are determined by correlating with recent skill casts.
        If we can't determine which skill caused it, skill_id and caster_id will be 0.
        """
        cls._on_hex_applied.append(callback)

    @classmethod
    def on_enchant_applied(cls, callback: Callable[[int, int, int], None]):
        """Register callback for when an enchantment is applied. Args: (target_id, skill_id, caster_id)

        This fires when a TRACKED agent gains any enchantment.
        Works for enemies too - uses Agent.IsEnchanted() which reads the agent's effects bitmap.

        IMPORTANT: You must call track_agent_effects(agent_id) for agents you want to monitor.

        The skill_id and caster_id are determined by correlating with recent skill casts.
        If we can't determine which skill caused it, skill_id and caster_id will be 0.
        """
        cls._on_enchant_applied.append(callback)

    @classmethod
    def on_condition_removed(cls, callback: Callable[[int], None]):
        """Register callback for when all conditions are removed. Args: (agent_id,)

        This fires when a TRACKED agent loses all conditions (none remaining).
        Works for enemies too.

        IMPORTANT: You must call track_agent_effects(agent_id) for agents you want to monitor.
        """
        cls._on_condition_removed.append(callback)

    @classmethod
    def on_hex_removed(cls, callback: Callable[[int], None]):
        """Register callback for when all hexes are removed. Args: (agent_id,)

        This fires when a TRACKED agent loses all hexes (none remaining).
        Works for enemies too.

        IMPORTANT: You must call track_agent_effects(agent_id) for agents you want to monitor.
        """
        cls._on_hex_removed.append(callback)

    @classmethod
    def on_enchant_removed(cls, callback: Callable[[int], None]):
        """Register callback for when all enchantments are removed. Args: (agent_id,)

        This fires when a TRACKED agent loses all enchantments (none remaining).
        Works for enemies too.

        IMPORTANT: You must call track_agent_effects(agent_id) for agents you want to monitor.
        """
        cls._on_enchant_removed.append(callback)

    @classmethod
    def on_stance_activated(cls, callback: Callable[[int, int, float], None]):
        """Register callback for when a stance skill is used. Args: (agent_id, skill_id, duration)

        This fires when ANY agent (including enemies) uses a Stance skill.
        Useful for knowing when an enemy has activated a blocking/defensive stance.

        The duration is estimated from the skill's max duration (at 15 attribute points).
        Stances are self-targeting, so agent_id is who has the stance active.
        """
        cls._on_stance_activated.append(callback)

    @classmethod
    def on_stance_ended(cls, callback: Callable[[int, int], None]):
        """Register callback for when a stance ends. Args: (agent_id, skill_id)

        This fires when:
        1. A stance duration expires (estimated based on skill data)
        2. An agent uses a new stance (ends the previous one)

        Note: The duration is estimated. Use has_active_stance() to check current status.
        """
        cls._on_stance_ended.append(callback)

    # ========================================================================
    # State Query Functions
    # ========================================================================

    @classmethod
    def is_agent_casting(cls, agent_id: int) -> bool:
        """Check if an agent is currently casting."""
        return agent_id in cls._current_casts

    @classmethod
    def get_casting_state(cls, agent_id: int) -> Optional[CastingState]:
        """Get the casting state for an agent."""
        return cls._current_casts.get(agent_id)

    @classmethod
    def get_all_casting(cls) -> List[CastingState]:
        """Get all agents currently casting."""
        return list(cls._current_casts.values())

    @classmethod
    def get_casting_skill(cls, agent_id: int) -> int:
        """Get the skill ID being cast (0 if not casting)."""
        cast = cls._current_casts.get(agent_id)
        return cast.skill_id if cast else 0

    @classmethod
    def get_cast_target(cls, agent_id: int) -> int:
        """Get the target of the current cast (0 if none)."""
        cast = cls._current_casts.get(agent_id)
        return cast.target_id if cast else 0

    @classmethod
    def get_cast_progress(cls, agent_id: int) -> float:
        """Get cast progress 0.0-1.0 (-1 if not casting)."""
        cast = cls._current_casts.get(agent_id)
        if not cast:
            return -1.0
        if cast.duration <= 0:
            return 1.0
        # Use GetTickCount equivalent - this needs the C++ timestamp
        # For now, we can use Python time as approximation
        import ctypes
        kernel32 = ctypes.windll.kernel32
        now = kernel32.GetTickCount()
        elapsed = now - cast.start_time
        progress = elapsed / (cast.duration * 1000.0)
        return min(progress, 1.0)

    @classmethod
    def get_cast_time_remaining(cls, agent_id: int) -> int:
        """Get remaining cast time in milliseconds."""
        cast = cls._current_casts.get(agent_id)
        if not cast or cast.duration <= 0:
            return 0
        import ctypes
        kernel32 = ctypes.windll.kernel32
        now = kernel32.GetTickCount()
        duration_ms = int(cast.duration * 1000)
        elapsed = now - cast.start_time
        return max(0, duration_ms - elapsed)

    @classmethod
    def is_agent_attacking(cls, agent_id: int) -> bool:
        """Check if an agent is currently attacking."""
        return agent_id in cls._current_attacks

    @classmethod
    def get_attack_state(cls, agent_id: int) -> Optional[AttackState]:
        """Get the attack state for an agent."""
        return cls._current_attacks.get(agent_id)

    @classmethod
    def get_attack_target(cls, agent_id: int) -> int:
        """Get the attack target (0 if not attacking)."""
        attack = cls._current_attacks.get(agent_id)
        return attack.target_id if attack else 0

    @classmethod
    def is_agent_in_aftercast(cls, agent_id: int) -> bool:
        """Check if an agent is in TRUE aftercast (after skill finished, can't use skills)."""
        return cls._in_aftercast.get(agent_id, False)

    @classmethod
    def is_agent_disabled(cls, agent_id: int) -> bool:
        """Check if an agent is disabled (can't use skills - either casting or in aftercast)."""
        return cls._disabled_state.get(agent_id, False)

    @classmethod
    def can_agent_act(cls, agent_id: int) -> bool:
        """Check if an agent can use skills (not disabled, not knocked down)."""
        if cls._disabled_state.get(agent_id, False):
            return False
        if cls.is_agent_knocked_down(agent_id):
            return False
        return True

    @classmethod
    def is_agent_knocked_down(cls, agent_id: int) -> bool:
        """Check if an agent is knocked down."""
        kd = cls._knockdowns.get(agent_id)
        if not kd:
            return False
        import ctypes
        kernel32 = ctypes.windll.kernel32
        now = kernel32.GetTickCount()
        elapsed = now - kd.start_time
        return elapsed < int(kd.duration * 1000)

    @classmethod
    def get_knockdown_state(cls, agent_id: int) -> Optional[KnockdownState]:
        """Get the knockdown state for an agent."""
        return cls._knockdowns.get(agent_id)

    @classmethod
    def get_knockdown_time_remaining(cls, agent_id: int) -> int:
        """Get remaining knockdown time in milliseconds."""
        kd = cls._knockdowns.get(agent_id)
        if not kd:
            return 0
        import ctypes
        kernel32 = ctypes.windll.kernel32
        now = kernel32.GetTickCount()
        duration_ms = int(kd.duration * 1000)
        elapsed = now - kd.start_time
        return max(0, duration_ms - elapsed)

    @classmethod
    def get_agents_targeting(cls, target_id: int) -> List[int]:
        """Get all agents targeting (casting at or attacking) a specific agent."""
        result = set()
        for agent_id, cast in cls._current_casts.items():
            if cast.target_id == target_id:
                result.add(agent_id)
        for agent_id, attack in cls._current_attacks.items():
            if attack.target_id == target_id:
                result.add(agent_id)
        return list(result)

    @classmethod
    def get_agents_casting_at(cls, target_id: int) -> List[int]:
        """Get agents casting skills at a specific agent."""
        return [agent_id for agent_id, cast in cls._current_casts.items()
                if cast.target_id == target_id]

    @classmethod
    def get_agents_attacking(cls, target_id: int) -> List[int]:
        """Get agents attacking a specific agent."""
        return [agent_id for agent_id, attack in cls._current_attacks.items()
                if attack.target_id == target_id]

    @classmethod
    def has_active_stance(cls, agent_id: int) -> bool:
        """Check if an agent has an active stance (based on tracking, not game state)."""
        if agent_id not in cls._active_stances:
            return False
        # Check if stance has expired
        import ctypes
        kernel32 = ctypes.windll.kernel32
        now = kernel32.GetTickCount()
        skill_id, start_time, estimated_end = cls._active_stances[agent_id]
        return now < estimated_end

    @classmethod
    def get_active_stance(cls, agent_id: int) -> Optional[int]:
        """Get the skill ID of the agent's active stance (0 if none/expired)."""
        if not cls.has_active_stance(agent_id):
            return None
        return cls._active_stances[agent_id][0]

    @classmethod
    def get_stance_time_remaining(cls, agent_id: int) -> int:
        """Get estimated remaining stance time in milliseconds (0 if none)."""
        if agent_id not in cls._active_stances:
            return 0
        import ctypes
        kernel32 = ctypes.windll.kernel32
        now = kernel32.GetTickCount()
        skill_id, start_time, estimated_end = cls._active_stances[agent_id]
        return max(0, estimated_end - now)

    @classmethod
    def get_all_agents_with_stances(cls) -> List[int]:
        """Get list of agent IDs that have active stances."""
        import ctypes
        kernel32 = ctypes.windll.kernel32
        now = kernel32.GetTickCount()
        return [agent_id for agent_id, (skill_id, start, end) in cls._active_stances.items()
                if now < end]

    # ========================================================================
    # Event History
    # ========================================================================

    @classmethod
    def get_recent_skill_events(cls, count: int = 20) -> List[SkillEventData]:
        """Get recent skill events."""
        events = list(cls._skill_history)
        return events[-count:] if len(events) > count else events

    @classmethod
    def get_recent_damage_events(cls, count: int = 20) -> List[DamageEventData]:
        """Get recent damage events."""
        events = list(cls._damage_history)
        return events[-count:] if len(events) > count else events

    @classmethod
    def set_max_event_history(cls, count: int):
        """Set maximum number of events to store in history."""
        cls._skill_history = deque(cls._skill_history, maxlen=count)
        cls._damage_history = deque(cls._damage_history, maxlen=count)
        
    @staticmethod
    def enable_callbacks():
        """Enable or disable all callbacks globally."""
        from Py4GW import Game
        Game.register_callback(
            "CombatEvents.Callbacks",
            CombatEvents().update)
        

    @staticmethod
    def disable_callbacks():
        """Disable all callbacks globally."""
        from Py4GW import Game
        Game.remove_callback("CombatEvents.Callbacks")
        
CombatEvents.enable_callbacks()

