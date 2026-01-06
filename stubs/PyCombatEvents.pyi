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
    SKILL_ACTIVATED: int          # Non-attack skill started
    ATTACK_SKILL_ACTIVATED: int   # Attack skill started
    SKILL_STOPPED: int            # Skill cancelled
    SKILL_FINISHED: int           # Skill completed
    ATTACK_SKILL_FINISHED: int    # Attack skill completed
    INTERRUPTED: int              # Skill interrupted
    INSTANT_SKILL_ACTIVATED: int  # Instant skill (no cast time)
    ATTACK_SKILL_STOPPED: int     # Attack skill cancelled

    # Attack Events (auto-attacks)
    ATTACK_STARTED: int           # Auto-attack started
    ATTACK_STOPPED: int           # Auto-attack stopped
    MELEE_ATTACK_FINISHED: int    # Melee hit completed

    # State Events
    DISABLED: int                 # Disabled state changed (val=1 disabled, val=0 can act)
    KNOCKED_DOWN: int             # Knockdown (fval=duration_seconds)
    CASTTIME: int                 # Cast time info (fval=duration_seconds)

    # Damage Events (NOTE: agent_id=TARGET, target_id=SOURCE)
    DAMAGE: int                   # Normal damage (fval=damage_fraction)
    CRITICAL: int                 # Critical hit (fval=damage_fraction)
    ARMOR_IGNORING: int           # Armor-ignoring damage (can be negative for heals)

    # Effect Events
    EFFECT_APPLIED: int           # Visual effect applied
    EFFECT_REMOVED: int           # Visual effect removed
    EFFECT_ON_TARGET: int         # Skill effect hit target

    # Energy Events
    ENERGY_GAINED: int            # Energy gained
    ENERGY_SPENT: int             # Energy spent

    # Misc
    SKILL_DAMAGE: int             # Pre-damage notification
    SKILL_ACTIVATE_PACKET: int    # Early skill notification

    # Skill Recharge Events
    SKILL_RECHARGE: int           # Skill went on cooldown (fval=recharge_ms)
    SKILL_RECHARGED: int          # Skill came off cooldown


# Alias for backward compatibility
EventTypes = EventType


class CombatEvents:
    """
    Query combat state and register callbacks for combat events.

    All methods are static - no instantiation needed. Data is automatically
    updated each frame.

    Most Important Methods:
        can_act(agent_id)      - Can agent use skills right now?
        is_casting(agent_id)   - Is agent currently casting?
        is_attacking(agent_id) - Is agent auto-attacking?
    """

    # ==========================================================================
    # Casting State
    # ==========================================================================

    @staticmethod
    def is_casting(agent_id: int) -> bool:
        """Check if agent is currently casting a skill."""
        ...

    @staticmethod
    def get_casting_skill(agent_id: int) -> int:
        """Get skill ID being cast (0 if not casting)."""
        ...

    @staticmethod
    def get_cast_target(agent_id: int) -> int:
        """Get target of current cast (0 if none/self)."""
        ...

    @staticmethod
    def get_cast_progress(agent_id: int) -> float:
        """Get cast progress 0.0-1.0 (-1 if not casting)."""
        ...

    @staticmethod
    def get_cast_time_remaining(agent_id: int) -> int:
        """Get remaining cast time in milliseconds."""
        ...

    # ==========================================================================
    # Attack State
    # ==========================================================================

    @staticmethod
    def is_attacking(agent_id: int) -> bool:
        """Check if agent is auto-attacking."""
        ...

    @staticmethod
    def get_attack_target(agent_id: int) -> int:
        """Get target of current attack (0 if not attacking)."""
        ...

    # ==========================================================================
    # Action State (Most Important!)
    # ==========================================================================

    @staticmethod
    def can_act(agent_id: int) -> bool:
        """
        Check if agent can use skills right now.

        Returns True if agent is not disabled and not knocked down.
        This is the primary check for skill usage timing.
        """
        ...

    @staticmethod
    def is_disabled(agent_id: int) -> bool:
        """Check if agent is disabled (casting or in aftercast)."""
        ...

    @staticmethod
    def is_knocked_down(agent_id: int) -> bool:
        """Check if agent is knocked down."""
        ...

    @staticmethod
    def get_knockdown_remaining(agent_id: int) -> int:
        """Get remaining knockdown time in milliseconds."""
        ...

    # ==========================================================================
    # Skill Recharges
    # ==========================================================================

    @staticmethod
    def is_skill_recharging(agent_id: int, skill_id: int) -> bool:
        """Check if a specific skill is on cooldown for an agent."""
        ...

    @staticmethod
    def get_skill_recharge_remaining(agent_id: int, skill_id: int) -> int:
        """Get remaining recharge time in milliseconds for a skill."""
        ...

    @staticmethod
    def get_recharging_skills(agent_id: int) -> List[Tuple[int, int]]:
        """
        Get all skills currently recharging for an agent.

        Returns:
            List of (skill_id, remaining_ms) tuples.
        """
        ...

    @staticmethod
    def get_observed_skills(agent_id: int) -> Set[int]:
        """
        Get all skills we've seen an agent use.

        Useful for building enemy skillbars over time.
        """
        ...

    # ==========================================================================
    # Stance State (Estimated)
    # ==========================================================================

    @staticmethod
    def has_stance(agent_id: int) -> bool:
        """Check if agent has an active stance (ESTIMATE - may not be accurate)."""
        ...

    @staticmethod
    def get_stance(agent_id: int) -> Optional[int]:
        """Get skill ID of active stance, or None."""
        ...

    @staticmethod
    def get_stance_remaining(agent_id: int) -> int:
        """Get estimated remaining stance duration in milliseconds."""
        ...

    # ==========================================================================
    # Targeting
    # ==========================================================================

    @staticmethod
    def get_agents_targeting(target_id: int) -> List[int]:
        """Get all agents currently attacking or casting at the target."""
        ...

    # ==========================================================================
    # Raw Event Access
    # ==========================================================================

    @staticmethod
    def get_events() -> List[Tuple[int, int, int, int, int, float]]:
        """
        Get raw events from the buffer.

        Returns:
            List of (timestamp, event_type, agent_id, value, target_id, float_value) tuples.
        """
        ...

    @staticmethod
    def clear_events() -> None:
        """Clear the event buffer."""
        ...

    @staticmethod
    def get_recent_damage(count: int = 20) -> List[Tuple[int, int, int, float, int, bool]]:
        """
        Get recent damage events.

        Returns:
            List of (timestamp, target_id, source_id, damage_fraction, skill_id, is_crit) tuples.

        Note:
            damage_fraction is a fraction of max HP. Multiply by Agent.GetMaxHealth(target_id)
            to get actual damage.
        """
        ...

    @staticmethod
    def get_recent_skills(count: int = 20) -> List[Tuple[int, int, int, int, int]]:
        """
        Get recent skill events.

        Returns:
            List of (timestamp, caster_id, skill_id, target_id, event_type) tuples.
        """
        ...

    # ==========================================================================
    # Callbacks
    # ==========================================================================

    @staticmethod
    def on_skill_activated(callback: Callable[[int, int, int], None]) -> None:
        """
        Register callback for skill activation.

        Args:
            callback: Function(caster_id, skill_id, target_id)
        """
        ...

    @staticmethod
    def on_skill_finished(callback: Callable[[int, int], None]) -> None:
        """
        Register callback for skill completion.

        Args:
            callback: Function(agent_id, skill_id)
        """
        ...

    @staticmethod
    def on_skill_interrupted(callback: Callable[[int, int], None]) -> None:
        """
        Register callback for skill interruption.

        Args:
            callback: Function(agent_id, skill_id)
        """
        ...

    @staticmethod
    def on_attack_started(callback: Callable[[int, int], None]) -> None:
        """
        Register callback for auto-attack start.

        Args:
            callback: Function(attacker_id, target_id)
        """
        ...

    @staticmethod
    def on_aftercast_ended(callback: Callable[[int], None]) -> None:
        """
        Register callback for when an agent can act again.

        THIS IS THE KEY CALLBACK FOR FRAME-PERFECT SKILL CHAINING!

        Args:
            callback: Function(agent_id)
        """
        ...

    @staticmethod
    def on_knockdown(callback: Callable[[int, float], None]) -> None:
        """
        Register callback for knockdown.

        Args:
            callback: Function(agent_id, duration_seconds)
        """
        ...

    @staticmethod
    def on_damage(callback: Callable[[int, int, float, int], None]) -> None:
        """
        Register callback for damage events.

        Args:
            callback: Function(target_id, source_id, damage_fraction, skill_id)

        Note:
            damage_fraction is a fraction of max HP, not absolute damage.
            Multiply by Agent.GetMaxHealth(target_id) to get actual damage.
        """
        ...

    @staticmethod
    def on_skill_recharge_started(callback: Callable[[int, int, int], None]) -> None:
        """
        Register callback for skill going on cooldown.

        Args:
            callback: Function(agent_id, skill_id, recharge_ms)
        """
        ...

    @staticmethod
    def on_skill_recharged(callback: Callable[[int, int], None]) -> None:
        """
        Register callback for skill coming off cooldown.

        Args:
            callback: Function(agent_id, skill_id)
        """
        ...

    @staticmethod
    def clear_callbacks() -> None:
        """Remove all registered callbacks."""
        ...

    @staticmethod
    def clear_recharge_data(agent_id: int) -> None:
        """Clear recharge tracking data for a specific agent."""
        ...

    # ==========================================================================
    # Internal
    # ==========================================================================

    @staticmethod
    def update() -> None:
        """
        Process pending events from the C++ queue.

        Called automatically each frame - you don't need to call this.
        """
        ...
