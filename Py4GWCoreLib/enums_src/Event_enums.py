from dataclasses import dataclass
from enum import Enum, IntEnum

class EventType(IntEnum):
    """
    Raw combat event discriminator.

    This enum only identifies what kind of raw combat event was received from
    the C++ queue. Field meaning is described separately by
    `CombatEventDescriptor` and `EVENT_TYPE_DESCRIPTORS`.
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
    HEALING = 33                  # Healing/lifesteal gain: agent=target, target=source, fval=heal_fraction

    # -- Effect Events --
    EFFECT_APPLIED = 40           # Visual effect applied: agent=affected, val=effect_id
    EFFECT_REMOVED = 41           # Visual effect removed: agent=affected, val=effect_id
    EFFECT_ON_TARGET = 42         # Skill effect hit target: agent=caster, val=effect_id, target=target
    EFFECT_RENEWED = 43           # Existing effect reapplied before removal: agent=affected, val=effect_id

    # -- Energy Events --
    ENERGY_GAINED = 50            # Energy gained: agent=agent, fval=energy_amount
    ENERGY_SPENT = 51             # Energy spent: agent=agent, fval=energy_fraction

    # -- Misc --
    SKILL_DAMAGE = 60             # Pre-damage notification: agent=target, val=skill_id
    SKILL_ACTIVATE_PACKET = 70    # Early skill notification: agent=caster, val=skill_id

    # -- Skill Recharge Events --
    SKILL_RECHARGE = 80           # Skill went on cooldown: agent=agent, val=skill_id, fval=recharge_ms
    SKILL_RECHARGED = 81          # Skill ready again: agent=agent, val=skill_id


class EventFieldRole(str, Enum):
    """Meaning of a raw combat event payload field."""

    UNUSED = "unused"
    AGENT = "agent"
    CASTER = "caster"
    ATTACKER = "attacker"
    TARGET = "target"
    SOURCE = "source"
    SKILL_ID = "skill_id"
    EFFECT_ID = "effect_id"
    DISABLED_FLAG = "disabled_flag"
    DAMAGE_FRACTION = "damage_fraction"
    HEAL_FRACTION = "heal_fraction"
    DURATION_SECONDS = "duration_seconds"
    RECHARGE_MS = "recharge_ms"
    ENERGY_GAINED = "energy_gained"
    ENERGY_SPENT = "energy_spent"


@dataclass(frozen=True)
class CombatEventDescriptor:
    """Schema metadata for one raw combat event type."""

    label: str
    short_label: str
    category: str
    agent_role: EventFieldRole
    value_role: EventFieldRole
    target_role: EventFieldRole
    float_role: EventFieldRole
    notes: str = ""


EVENT_TYPE_DESCRIPTORS: dict[EventType, CombatEventDescriptor] = {
    EventType.SKILL_ACTIVATED: CombatEventDescriptor("Skill Activated", "CAST", "skill", EventFieldRole.CASTER, EventFieldRole.SKILL_ID, EventFieldRole.TARGET, EventFieldRole.UNUSED),
    EventType.ATTACK_SKILL_ACTIVATED: CombatEventDescriptor("Attack Skill Activated", "ATK_SKILL", "skill", EventFieldRole.CASTER, EventFieldRole.SKILL_ID, EventFieldRole.TARGET, EventFieldRole.UNUSED),
    EventType.SKILL_STOPPED: CombatEventDescriptor("Skill Stopped", "STOPPED", "skill", EventFieldRole.CASTER, EventFieldRole.SKILL_ID, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.SKILL_FINISHED: CombatEventDescriptor("Skill Finished", "FINISHED", "skill", EventFieldRole.CASTER, EventFieldRole.SKILL_ID, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.ATTACK_SKILL_FINISHED: CombatEventDescriptor("Attack Skill Finished", "ATK_DONE", "skill", EventFieldRole.CASTER, EventFieldRole.SKILL_ID, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.INTERRUPTED: CombatEventDescriptor("Interrupted", "INTERRUPT", "skill", EventFieldRole.AGENT, EventFieldRole.SKILL_ID, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.INSTANT_SKILL_ACTIVATED: CombatEventDescriptor("Instant Skill Activated", "INSTANT", "skill", EventFieldRole.CASTER, EventFieldRole.SKILL_ID, EventFieldRole.TARGET, EventFieldRole.UNUSED),
    EventType.ATTACK_SKILL_STOPPED: CombatEventDescriptor("Attack Skill Stopped", "ATK_STOP", "skill", EventFieldRole.CASTER, EventFieldRole.SKILL_ID, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.ATTACK_STARTED: CombatEventDescriptor("Attack Started", "ATTACK", "attack", EventFieldRole.ATTACKER, EventFieldRole.UNUSED, EventFieldRole.TARGET, EventFieldRole.UNUSED),
    EventType.ATTACK_STOPPED: CombatEventDescriptor("Attack Stopped", "ATK_STOP", "attack", EventFieldRole.ATTACKER, EventFieldRole.UNUSED, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.MELEE_ATTACK_FINISHED: CombatEventDescriptor("Melee Attack Finished", "MELEE_DONE", "attack", EventFieldRole.ATTACKER, EventFieldRole.UNUSED, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.DISABLED: CombatEventDescriptor("Disabled", "DISABLED", "state", EventFieldRole.AGENT, EventFieldRole.DISABLED_FLAG, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.KNOCKED_DOWN: CombatEventDescriptor("Knocked Down", "KD", "state", EventFieldRole.AGENT, EventFieldRole.UNUSED, EventFieldRole.UNUSED, EventFieldRole.DURATION_SECONDS),
    EventType.CASTTIME: CombatEventDescriptor("Cast Time", "CASTTIME", "state", EventFieldRole.CASTER, EventFieldRole.UNUSED, EventFieldRole.UNUSED, EventFieldRole.DURATION_SECONDS),
    EventType.DAMAGE: CombatEventDescriptor("Damage", "DMG", "damage", EventFieldRole.TARGET, EventFieldRole.SKILL_ID, EventFieldRole.SOURCE, EventFieldRole.DAMAGE_FRACTION, "For damage packets, agent_id is the target and target_id is the source."),
    EventType.CRITICAL: CombatEventDescriptor("Critical Damage", "CRIT", "damage", EventFieldRole.TARGET, EventFieldRole.SKILL_ID, EventFieldRole.SOURCE, EventFieldRole.DAMAGE_FRACTION, "For damage packets, agent_id is the target and target_id is the source."),
    EventType.ARMOR_IGNORING: CombatEventDescriptor("Armor Ignoring", "ARMOR_IGN", "damage", EventFieldRole.TARGET, EventFieldRole.SKILL_ID, EventFieldRole.SOURCE, EventFieldRole.DAMAGE_FRACTION, "Can be negative for heals."),
    EventType.HEALING: CombatEventDescriptor("Healing", "HEAL", "healing", EventFieldRole.TARGET, EventFieldRole.SKILL_ID, EventFieldRole.SOURCE, EventFieldRole.HEAL_FRACTION),
    EventType.EFFECT_APPLIED: CombatEventDescriptor("Effect Applied", "EFFECT_ON", "effect", EventFieldRole.AGENT, EventFieldRole.EFFECT_ID, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.EFFECT_REMOVED: CombatEventDescriptor("Effect Removed", "EFFECT_OFF", "effect", EventFieldRole.AGENT, EventFieldRole.EFFECT_ID, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.EFFECT_ON_TARGET: CombatEventDescriptor("Effect On Target", "EFFECT_HIT", "effect", EventFieldRole.CASTER, EventFieldRole.EFFECT_ID, EventFieldRole.TARGET, EventFieldRole.UNUSED),
    EventType.EFFECT_RENEWED: CombatEventDescriptor("Effect Renewed", "EFFECT_RE", "effect", EventFieldRole.AGENT, EventFieldRole.EFFECT_ID, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.ENERGY_GAINED: CombatEventDescriptor("Energy Gained", "E_GAIN", "energy", EventFieldRole.AGENT, EventFieldRole.UNUSED, EventFieldRole.UNUSED, EventFieldRole.ENERGY_GAINED),
    EventType.ENERGY_SPENT: CombatEventDescriptor("Energy Spent", "E_SPENT", "energy", EventFieldRole.AGENT, EventFieldRole.UNUSED, EventFieldRole.UNUSED, EventFieldRole.ENERGY_SPENT),
    EventType.SKILL_DAMAGE: CombatEventDescriptor("Skill Damage", "SKILL_DMG", "damage", EventFieldRole.TARGET, EventFieldRole.SKILL_ID, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.SKILL_ACTIVATE_PACKET: CombatEventDescriptor("Skill Activate Packet", "SKILL_PKT", "skill", EventFieldRole.CASTER, EventFieldRole.SKILL_ID, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
    EventType.SKILL_RECHARGE: CombatEventDescriptor("Skill Recharge", "RECHARGE", "recharge", EventFieldRole.AGENT, EventFieldRole.SKILL_ID, EventFieldRole.UNUSED, EventFieldRole.RECHARGE_MS),
    EventType.SKILL_RECHARGED: CombatEventDescriptor("Skill Recharged", "READY", "recharge", EventFieldRole.AGENT, EventFieldRole.SKILL_ID, EventFieldRole.UNUSED, EventFieldRole.UNUSED),
}


def coerce_event_type(event_type: int | EventType) -> EventType | None:
    """Convert an int-like event type into EventType, or return None if unknown."""
    try:
        return event_type if isinstance(event_type, EventType) else EventType(int(event_type))
    except (TypeError, ValueError):
        return None


def get_event_descriptor(event_type: int | EventType) -> CombatEventDescriptor | None:
    """Return schema metadata for a raw combat event type."""
    normalized = coerce_event_type(event_type)
    if normalized is None:
        return None
    return EVENT_TYPE_DESCRIPTORS.get(normalized)


def get_event_type_name(event_type: int | EventType) -> str:
    """Return the short display label for a raw combat event type."""
    descriptor = get_event_descriptor(event_type)
    if descriptor is not None:
        return descriptor.short_label
    return f"TYPE_{event_type}"


def get_event_type_label(event_type: int | EventType) -> str:
    """Return the human-readable label for a raw combat event type."""
    descriptor = get_event_descriptor(event_type)
    if descriptor is not None:
        return descriptor.label
    return f"Unknown Event Type {event_type}"

