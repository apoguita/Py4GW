# CombatEvents Guide

**Author:** Paul (HSTools)

---

## What is CombatEvents?

CombatEvents provides **real-time combat state data** for Guild Wars. Query any agent's combat state anytime - data is always available, no setup required.

**Key Features:**
- Check if any agent is casting, attacking, knocked down, or disabled
- Track skill cooldowns for any agent (player, enemies, NPCs, heroes)
- Get notified when events happen via callbacks
- Works automatically - just import and use

---

## Quick Start - Query Combat State

The most common use case: check if you can use a skill.

```python
from Py4GWCoreLib import CombatEvents, Player, Skillbar

# Check if you can use a skill right now
if CombatEvents.can_act(Player.GetAgentID()):
    Skillbar.UseSkill(1)

# Check enemy's casting state
enemy_id = Player.GetTargetID()
if CombatEvents.is_casting(enemy_id):
    skill = CombatEvents.get_casting_skill(enemy_id)
    progress = CombatEvents.get_cast_progress(enemy_id)
    print(f"Casting skill {skill}, {progress*100:.0f}% done")
```

---

## State Query Functions (Primary API)

These are the main functions you'll use. Call them anytime to get current state.

### Casting State

| Function | Returns | Description |
|----------|---------|-------------|
| `is_casting(agent_id)` | bool | True if agent is currently casting |
| `get_casting_skill(agent_id)` | int | Skill ID being cast (0 if not casting) |
| `get_cast_target(agent_id)` | int | Target of the cast (0 if none/self) |
| `get_cast_progress(agent_id)` | float | Cast progress 0.0-1.0 (-1 if not casting) |
| `get_cast_time_remaining(agent_id)` | int | Remaining cast time in milliseconds |

### Attack State

| Function | Returns | Description |
|----------|---------|-------------|
| `is_attacking(agent_id)` | bool | True if agent is auto-attacking |
| `get_attack_target(agent_id)` | int | Target of current attack (0 if not attacking) |

### Action State (Most Important!)

| Function | Returns | Description |
|----------|---------|-------------|
| `can_act(agent_id)` | bool | **True if agent can use skills** (not disabled, not knocked down) |
| `is_disabled(agent_id)` | bool | True if agent is disabled (casting or in aftercast) |
| `is_knocked_down(agent_id)` | bool | True if agent is knocked down |
| `get_knockdown_remaining(agent_id)` | int | Remaining knockdown time in ms |

### Skill Recharges

| Function | Returns | Description |
|----------|---------|-------------|
| `is_skill_recharging(agent_id, skill_id)` | bool | True if skill is on cooldown |
| `get_skill_recharge_remaining(agent_id, skill_id)` | int | Remaining recharge time in ms |
| `get_recharging_skills(agent_id)` | List | All skills currently recharging: [(skill_id, remaining_ms, is_estimated), ...] |
| `get_observed_skills(agent_id)` | Set[int] | All skills we've seen agent use |
| `is_recharge_estimated(agent_id, skill_id)` | bool | True if using base recharge (no modifiers) |

> **Note:** The server only sends actual recharge data for agents you directly control (player + your heroes). For everyone else (enemies, NPCs, other party members), recharges are **estimated** from base skill data. Use `is_recharge_estimated()` to check.

### Stance State (Estimated)

| Function | Returns | Description |
|----------|---------|-------------|
| `has_stance(agent_id)` | bool | True if agent has a stance active |
| `get_stance(agent_id)` | int or None | Skill ID of active stance |
| `get_stance_remaining(agent_id)` | int | Estimated time remaining in ms |

### Targeting

| Function | Returns | Description |
|----------|---------|-------------|
| `get_agents_targeting(target_id)` | List[int] | All agents attacking/casting at target |

---

## Common Use Cases

### 1. Smart Skill Usage (Check Before Acting)

```python
from Py4GWCoreLib import CombatEvents, Player, Skillbar

def use_skill_when_ready(skill_slot, target_id=0):
    """Use a skill only when the player can act."""
    player_id = Player.GetAgentID()

    if CombatEvents.can_act(player_id):
        Skillbar.UseSkill(skill_slot, target_id)
        return True
    return False
```

### 2. Interrupt Bot (Query-Based)

```python
from Py4GWCoreLib import CombatEvents, Player, Skillbar, Skill, AgentArray

INTERRUPT_SKILL_SLOT = 5
DANGEROUS_SKILLS = [123, 456, 789]  # Skill IDs to interrupt

def check_for_interrupts():
    """Check if any enemy is casting something we should interrupt."""
    for agent in AgentArray.GetEnemyArray():
        if CombatEvents.is_casting(agent.agent_id):
            skill = CombatEvents.get_casting_skill(agent.agent_id)
            if skill in DANGEROUS_SKILLS:
                Skillbar.UseSkill(INTERRUPT_SKILL_SLOT, agent.agent_id)
                print(f"Interrupting {Skill.GetName(skill)}!")
                return
```

### 3. Stance Detection

```python
from Py4GWCoreLib import CombatEvents, Skill

def should_attack(enemy_id):
    """Check if we should attack (avoid blocking stances)."""
    if CombatEvents.has_stance(enemy_id):
        stance_id = CombatEvents.get_stance(enemy_id)
        stance_name = Skill.GetName(stance_id)
        if "Block" in stance_name:
            remaining = CombatEvents.get_stance_remaining(enemy_id)
            print(f"Enemy blocking for {remaining}ms, waiting...")
            return False
    return True
```

### 4. Track Who's Targeting You

```python
from Py4GWCoreLib import CombatEvents, Player

def get_threat_level():
    """Count how many enemies are targeting the player."""
    player_id = Player.GetAgentID()
    attackers = CombatEvents.get_agents_targeting(player_id)
    return len(attackers)
```

### 5. Track Enemy Skill Cooldowns

```python
from Py4GWCoreLib import CombatEvents, Skill

def analyze_enemy(enemy_id):
    """See what skills an enemy has used and their cooldown status."""
    # Get all skills we've seen this enemy use
    observed = CombatEvents.get_observed_skills(enemy_id)
    print(f"Enemy has used {len(observed)} different skills:")

    for skill_id in observed:
        skill_name = Skill.GetName(skill_id)
        if CombatEvents.is_skill_recharging(enemy_id, skill_id):
            remaining = CombatEvents.get_skill_recharge_remaining(enemy_id, skill_id)
            # Check if this is an estimate or actual server data
            is_estimated = CombatEvents.is_recharge_estimated(enemy_id, skill_id)
            marker = "~" if is_estimated else ""
            print(f"  {skill_name}: {marker}{remaining/1000:.1f}s left")
        else:
            print(f"  {skill_name}: READY")

# Check if a dangerous skill is on cooldown
DANGEROUS_SKILLS = [123, 456]  # e.g., Meteor Shower, Ward Against Foes

def is_safe_to_engage(enemy_id):
    """Check if enemy's dangerous skills are on cooldown."""
    for skill_id in DANGEROUS_SKILLS:
        if skill_id in CombatEvents.get_observed_skills(enemy_id):
            if not CombatEvents.is_skill_recharging(enemy_id, skill_id):
                return False  # Dangerous skill is ready!
    return True
```

> **Note on Enemy Recharges:** Since the server doesn't send recharge packets for enemies, these times are estimated from base skill data. They don't account for Fast Casting, Serpent's Quickness, or other modifiers. The actual recharge may be shorter!

---

## Callbacks (Optional - For Reactive Code)

For event-driven code, register callbacks that fire when events occur.

### Available Callbacks

| Callback | Arguments | When it fires |
|----------|-----------|---------------|
| `on_skill_activated` | (caster_id, skill_id, target_id) | Skill cast starts |
| `on_skill_finished` | (agent_id, skill_id) | Skill cast completes |
| `on_skill_interrupted` | (agent_id, skill_id) | Skill was interrupted |
| `on_attack_started` | (attacker_id, target_id) | Auto-attack begins |
| `on_aftercast_ended` | (agent_id) | **Agent can act again!** |
| `on_knockdown` | (agent_id, duration) | Agent knocked down |
| `on_damage` | (target_id, source_id, damage_fraction, skill_id) | Damage dealt |
| `on_skill_recharge_started` | (agent_id, skill_id, recharge_ms) | Skill went on cooldown |
| `on_skill_recharged` | (agent_id, skill_id) | Skill came off cooldown |

### Example: Frame-Perfect Skill Chaining

```python
from Py4GWCoreLib import CombatEvents, Player, Skillbar

def on_aftercast_end(agent_id):
    """Called the instant an agent can act again."""
    if agent_id == Player.GetAgentID():
        # Use next skill immediately - no wasted frames!
        Skillbar.UseSkill(next_skill_slot)

CombatEvents.on_aftercast_ended(on_aftercast_end)
```

### Example: React to Enemy Casts

```python
from Py4GWCoreLib import CombatEvents, Player, Skill

INTERRUPT_THESE = [123, 456]  # Dangerous skill IDs

def on_enemy_cast(caster_id, skill_id, target_id):
    """React when enemies start casting."""
    if caster_id == Player.GetAgentID():
        return  # Ignore our own casts

    if skill_id in INTERRUPT_THESE:
        print(f"DANGER: Enemy casting {Skill.GetName(skill_id)}!")
        # Could trigger interrupt here

CombatEvents.on_skill_activated(on_enemy_cast)
```

### Clearing Callbacks

```python
# Remove all registered callbacks
CombatEvents.clear_callbacks()
```

---

## Important Notes

### Damage Values

Damage callbacks give you a **fraction of max HP**, not absolute numbers:

```python
from Py4GWCoreLib import CombatEvents, Agent

def on_damage(target_id, source_id, damage_fraction, skill_id):
    # damage_fraction might be 0.05 (5% of max HP)
    actual_damage = damage_fraction * Agent.GetMaxHealth(target_id)
    print(f"Actual damage: {actual_damage:.0f}")

CombatEvents.on_damage(on_damage)
```

### When to Use Queries vs Callbacks

**Use Queries when:**
- You need to check state at specific moments
- Your main loop already runs every frame
- You want simpler, more readable code

**Use Callbacks when:**
- You need frame-perfect timing (like skill chaining)
- You want to react immediately to events
- You need to track events over time (damage totals)

### Skill Recharge: Actual vs Estimated

The server only sends recharge packets for agents whose skillbars you can observe:
- **Player**: Actual recharge data from server
- **Your Heroes**: Actual recharge data from server
- **Everyone else**: Estimated from base skill data

Estimated recharges do NOT account for:
- Fast Casting attribute (reduces recharge for Mesmers)
- Serpent's Quickness, Quickening Zephyr, etc.
- Equipment modifiers
- Skills that reduce/reset recharge

```python
# Check if recharge data is estimated
if CombatEvents.is_recharge_estimated(enemy_id, skill_id):
    print("Recharge is estimated - actual may be shorter!")
```

### Stance Detection Limitations

Stance detection is **estimated** based on skill data:
- We don't know the agent's attribute levels
- Duration is estimated conservatively
- May not be accurate for all stances

---

## Raw Event Access (Advanced)

For custom processing, access raw packet data directly:

```python
from Py4GWCoreLib.CombatEvents import CombatEvents, EventType

# Get raw event tuples
for ts, etype, agent, val, target, fval in CombatEvents.get_events():
    if etype == EventType.DAMAGE:
        print(f"Damage: {fval*100:.1f}% to agent {agent}")
    elif etype == EventType.SKILL_ACTIVATED:
        print(f"Agent {agent} casting skill {val}")

# Get recent damage events (formatted)
# Returns: [(timestamp, target, source, damage_frac, skill_id, is_crit), ...]
damage_events = CombatEvents.get_recent_damage(count=20)

# Get recent skill events (formatted)
# Returns: [(timestamp, caster, skill_id, target, event_type), ...]
skill_events = CombatEvents.get_recent_skills(count=20)

# Clear the event log
CombatEvents.clear_events()
```

---

## Testing Your Code

Enable the **CombatEventsTester** widget to see events in real-time:

1. Open Widget Manager
2. Go to **Widgets**
3. Enable **CombatEventsTester**

This shows all events as they happen and lets you test the query functions.

---

## Complete Example: Skill Rotation Bot

Using callbacks for frame-perfect skill chaining:

```python
from Py4GWCoreLib import CombatEvents, Player, Skillbar

class SkillRotation:
    """Execute a skill rotation with frame-perfect timing."""

    def __init__(self):
        self.queue = []
        self.waiting = False
        CombatEvents.on_aftercast_ended(self.on_can_act)

    def set_rotation(self, skill_slots):
        """Set the skill rotation (list of skill bar slots 1-8)."""
        self.queue = list(skill_slots)

    def start(self):
        """Start the rotation."""
        if self.queue:
            self._use_next_skill()

    def _use_next_skill(self):
        if not self.queue:
            return
        slot = self.queue.pop(0)
        Skillbar.UseSkill(slot, Player.GetTargetID())
        self.waiting = True

    def on_can_act(self, agent_id):
        """Called when any agent can act again."""
        if agent_id != Player.GetAgentID():
            return
        if not self.waiting:
            return
        self.waiting = False
        if self.queue:
            self._use_next_skill()
        else:
            print("Rotation complete!")

# Usage:
rotation = SkillRotation()
rotation.set_rotation([1, 2, 3, 4, 5])  # Skills in slots 1-5
rotation.start()
```

This creates frame-perfect skill chains with zero wasted aftercast time!

---

## Full Documentation

For complete API documentation, see:
- [CombatEvents.py](../Py4GWCoreLib/CombatEvents.py) - Main module with docstrings
- [CombatEventsTester.py](../Widgets/CombatEventsTester.py) - Working example widget
