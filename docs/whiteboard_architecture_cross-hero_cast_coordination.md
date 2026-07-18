# Whiteboard Architecture - Cross-Hero Locks

## Purpose

The whiteboard is a shared-memory lock table used by multiple Py4GW clients
in the same isolation group to coordinate work. It started as cross-hero
cast coordination for `(skill_id, target_agent_id)`, but the shared-memory
primitive is now generic:

```text
kind + key + target + group + owner + lock_mode + expiry
```

Every whiteboard lock is a lease. A caller must provide `ExpiresAtTick`, and
`PostLock` rejects expired or non-future deadlines. There are no permanent
whiteboard locks by design.

The original skill API still exists:

```python
PostIntent(owner_email, skill_id, target_agent_id, expires_at_tick, group)
IsIntentClaimed(skill_id, target_agent_id, group_id, exclude_email, now_tick)
```

Those methods are compatibility wrappers for:

```text
kind = WhiteboardLockKind.SKILL_TARGET
mode = WhiteboardLockMode.EXCLUSIVE
reentry = WhiteboardReentryPolicy.OWNER_REENTRANT
strength = WhiteboardClaimStrength.HARD
key = skill_id
target = target_agent_id
```

## Implementation Files

- `Py4GWCoreLib/enums_src/Whiteboard_enums.py` - lock kinds, modes, reentry policy, and claim strength.
- `Py4GWCoreLib/GlobalCache/shared_memory_src/IntentStruct.py` - shared-memory slot schema.
- `Py4GWCoreLib/GlobalCache/shared_memory_src/AllAccounts.py` - slot allocator, lock readers, sweeper, debug logger.
- `Py4GWCoreLib/GlobalCache/shared_memory_src/Globals.py` - capacity and sweep constants.
- `Py4GWCoreLib/GlobalCache/SharedMemory.py` - `GLOBAL_CACHE.ShMem` wrappers and sweep tick.
- `Py4GWCoreLib/GlobalCache/Whiteboard.py` - opt-in registry for `(kind, key)` consumers.
- `Py4GWCoreLib/Builds/Skills/_whiteboard.py` - skill-scoped opt-in wrapper.
- `HeroAI/custom_skill_src/skill_types.py` - per-skill `CoordinatesViaWhiteboard` flag.
- `Py4GWCoreLib/BuildMgr.py` - current skill-target read gate, post, and owner self-clear.

## Slot Schema

`AllAccounts.Intents` is a fixed-size `IntentStruct[SHMEM_MAX_INTENTS]` array.
The name `Intents` is kept for compatibility; the slots now represent generic
whiteboard locks.

| Field | Meaning |
| --- | --- |
| `OwnerEmail` | Account email that owns the lock. Used for owner clear and reentry checks. |
| `KindID` | `WhiteboardLockKind` value, such as `SKILL_TARGET` or `MINION_CORPSE`. |
| `LockMode` | `WhiteboardLockMode`: exclusive, shared, semaphore, or barrier. |
| `ReentryPolicy` | Whether the owner ignores its own matching lock. |
| `ClaimStrength` | Hard or soft claim. Current readers default to hard claims. |
| `MaxHolders` | Capacity for shared/semaphore locks. Exclusive locks use `1`. |
| `SkillID` | Compatibility name. Generic callers should treat this as `KeyID`. |
| `TargetAgentID` | Compatibility name. Generic callers should treat this as `TargetID`. |
| `IsolationGroupID` | Team scope. Different groups do not block each other. |
| `PostedAtTick` | `Py4GW.Game.get_tick_count64()` when the lock was posted. |
| `ExpiresAtTick` | Mandatory deadline. Readers ignore locks at or past this tick. |
| `Active` | Slot allocation flag. |

Capacity:

```python
SHMEM_MAX_INTENTS = 64
SHMEM_INTENT_DEFAULT_PING_BUDGET_MS = 150
SHMEM_INTENT_SWEEP_INTERVAL_MS = 100
```

## Lock Modes

### Exclusive

Only one matching unexpired lock can exist from another owner.

Use for:

- `SKILL_TARGET`: one coordinated skill on one target.
- `MINION_CORPSE`: one minion cast reserves one corpse.
- `RESURRECT_TARGET`: one resurrection cast reserves one dead ally.
- `LOOT_ITEM`: one account reserves one drop.
- `INTERACT_AGENT`: one account reserves one NPC, gadget, chest, or dialog target.

### Shared

Multiple matching locks are allowed up to `MaxHolders`.

Use for:

- Allowing a limited number of healers or protectors to cover one ally.
- Allowing a limited number of damage skills to join a spike.
- Allowing N interrupts on a high-value cast.

### Semaphore

Count-based lock where the target can be `0` for team-wide capacity. This is
useful when the resource is not a specific agent or item.

Use for:

- Only one account loots at a time.
- Only one account breaks formation for a utility task.
- Only two accounts perform long out-of-combat work.

### Barrier

Barrier locks are readiness claims. `IsLockBlocked` does not block on barriers;
callers use `IsLockSatisfied(..., required_holders=N)` to decide whether enough
participants have arrived.

Use for:

- Coordinated spikes.
- Wait-until-ready transitions.
- Party-wide setup timing.

## Reentry

`OWNER_REENTRANT` means the reader ignores locks owned by `exclude_email`.
This is the default for skill-target coordination so an account does not block
itself when the same cast path evaluates twice.

`NON_REENTRANT` means even the owner counts toward the lock limit. Use this for
strict duplicate suppression inside the same client.

## Claim Strength

`HARD` locks are blocking claims. Current compatibility wrappers and most
coordination should use this.

`SOFT` locks are reservations or planning hints. The shared-memory API can store
them, but a caller must explicitly query soft claims by passing
`claim_strength=WhiteboardClaimStrength.SOFT`.

## Expiry Model

All whiteboard locks expire by time. This is the only universal cleanup path
and is mandatory because clients can disconnect, map, fail a cast, or stop a
routine without clearing their slot.

There are three cleanup paths:

1. Reader-side expiry: `now_tick >= ExpiresAtTick` is treated as empty.
2. Owner clear: `ClearIntentsByOwner(owner_email)` clears all locks owned by an account.
3. Periodic sweep: `SweepExpiredIntents(now_tick)` compacts expired slots every `SHMEM_INTENT_SWEEP_INTERVAL_MS`.

The existing BuildMgr skill-target flow also clears owner locks when local cast
pending transitions from true to false.

## Public API

External callers should use `GLOBAL_CACHE.ShMem`.

| Method | Purpose |
| --- | --- |
| `PostLock(owner_email, kind_id, key_id, target_id, expires_at_tick, group?, lock_mode?, max_holders?, reentry_policy?, claim_strength?)` | Allocate a generic expiring whiteboard lock. |
| `IsLockBlocked(kind_id, key_id, target_id, group_id, exclude_email, now_tick, lock_mode?, max_holders?, reentry_policy?, claim_strength?)` | True when matching active locks should block the caller. |
| `CountLocks(kind_id, key_id, target_id, group_id, exclude_email, now_tick, reentry_policy?, claim_strength?)` | Count matching active locks. |
| `IsLockSatisfied(kind_id, key_id, target_id, group_id, exclude_email, now_tick, required_holders, claim_strength?)` | Barrier helper. |
| `PostIntent(owner_email, skill_id, target_agent_id, expires_at_tick, group?)` | Compatibility wrapper for exclusive skill-target locks. |
| `IsIntentClaimed(skill_id, target_agent_id, group_id, exclude_email, now_tick)` | Compatibility read gate for exclusive skill-target locks. |
| `ClearIntentsByOwner(owner_email)` | Clear all locks owned by an account. Name kept for compatibility. |
| `SweepExpiredIntents(now_tick)` | Clear expired slots. Name kept for compatibility. |
| `GetAllIntents()` | Debug snapshot of active slots. |

Generic locks allow `target_id=0` for team-wide semaphores or barriers.
Compatibility `PostIntent` / `IsIntentClaimed` still require a real target.

## Skill-Target Compatibility Flow

`BuildMgr.CastSkillID` still uses the original skill-target coordination flow:

```python
if self._is_whiteboard_skill(skill_id) and self._whiteboard_is_claimed(skill_id, target_agent_id):
    return False

slot = SkillBar.GetSlotBySkillID(skill_id)

if self._is_whiteboard_skill(skill_id):
    self._whiteboard_post_intent(skill_id, target_agent_id)

GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=target_agent_id, aftercast_delay=aftercast_delay)
```

`_whiteboard_post_intent` computes:

```text
expires_at = now
           + max(500, activation_ms + aftercast_ms)
           + SHMEM_INTENT_DEFAULT_PING_BUDGET_MS
```

The 500 ms floor protects instant and near-instant skills long enough for the
cast to commit.

## Skill Opt-In

A skill participates in current BuildMgr skill-target coordination when either
surface opts in.

Decorator surface:

```python
from Py4GWCoreLib.Builds.Skills._whiteboard import coordinates_via_whiteboard

@coordinates_via_whiteboard(Skill.GetID("Power_Drain"))
def Power_Drain(self) -> BuildCoroutine:
    ...
```

CustomSkill metadata surface:

```python
skill.CoordinatesViaWhiteboard = True
```

`BuildMgr._is_whiteboard_skill` unions both surfaces.

## Lock Kind Guidance

Current lock kinds live in `WhiteboardLockKind`:

| Kind | Suggested key | Suggested target | Notes |
| --- | --- | --- | --- |
| `SKILL_TARGET` | `skill_id` | `target_agent_id` | Existing BuildMgr behavior. |
| `MINION_CORPSE` | `0` or minion family id | corpse agent id | Prevents multiple minion skills from consuming the same corpse. |
| `CORPSE_EXPLOIT` | consumer family id | corpse agent id | Stronger generic corpse claim if all corpse consumers must conflict. |
| `WELL_CORPSE` | `0` or well family id | corpse agent id | Separate from minions so policies can differ. |
| `RESURRECT_TARGET` | rez skill id or `0` | dead ally id | Prevents duplicate resurrections. |
| `LOOT_ITEM` | model id or `0` | item id | Prevents duplicate pickup routing. |
| `INTERACT_AGENT` | interaction type | agent/gadget id | NPCs, chests, gadgets, dialog targets. |
| `MOVEMENT_OBJECTIVE` | objective id | `0` or agent id | Formation and utility movement claims. |
| `CALL_TARGET` | caller role | target agent id | Prevents call-target thrashing. |
| `BUFF_TARGET` | buff category or skill id | ally id | Use shared mode when limited stacking is acceptable. |
| `INTERRUPT_TARGET` | `0` or interrupt family id | enemy agent id | Looser than skill-target; only one interrupt family on a target. |
| `COOLDOWN` | cooldown family id | target id or `0` | Suppression locks that intentionally outlive the action. |

this Kinds are mere suggestions, the system can support any kind as long as its correctly configured.

## Adding a New Consumer

1. Pick a `WhiteboardLockKind`.
2. Pick the key and target shape. Keep it stable and documented.
3. Choose mode, reentry, strength, and expiry budget.
4. Query `IsLockBlocked` at the consumer's single action funnel.
5. Call `PostLock` immediately before committing the action.
6. Clear by owner if the action has a reliable completion signal; otherwise rely on timeout and sweep.

For the current corpse-exploit/minion protection path, callers do not maintain
a hand-written list of animate skills. The lock is encapsulated in the
exploitable-corpse dispatch layer:

- `Routines.Agents.GetExploitableCorpses(...)` filters out corpses already held
  by the Minion Lock.
- `Routines.Agents.GetNearestExploitableCorpse(..., reserve=True, skill_id=...)`
  selects the nearest unlocked exploitable corpse and posts the Minion Lock.
- `Skilltarget.ExploitableCorpse` callers should use that routine instead of
  manually collecting corpses in combat/build code.

The colloquial lock name is still "Minion Lock" because the first live use case
is preventing multiple minion casts from spending the same corpse.

```text
kind = MINION_CORPSE
key = 0
target = corpse_agent_id
mode = EXCLUSIVE
reentry = OWNER_REENTRANT
strength = HARD
expiry = activation + aftercast + ping budget
```

For the current resurrection protection path, plain dead-ally reads remain
available through `Routines.Agents.GetDeadAlly(...)`. Non-resurrection skills
that merely require a dead ally should keep using `Skilltarget.DeadAlly`.
Actual resurrection skills should use `Skilltarget.ResurrectionAlly`, which is
the locked cast target.

- `Routines.Agents.GetResurrectionTarget(...)` filters out dead allies already
  held by the Resurrection Lock.
- `Routines.Agents.GetResurrectionTarget(..., reserve=True, skill_id=...)`
  selects the nearest unlocked dead ally and posts the Resurrection Lock.
- `Skilltarget.ResurrectionAlly` callers use that routine when they are choosing
  a target for a resurrection skill.

```text
kind = RESURRECT_TARGET
key = 0
target = dead_ally_agent_id
mode = EXCLUSIVE
reentry = OWNER_REENTRANT
strength = HARD
expiry = activation + aftercast + ping budget
```

## Debug Logging

Set `WHITEBOARD_DEBUG = True` in
`Py4GWCoreLib/GlobalCache/shared_memory_src/AllAccounts.py`.

Example lines now include kind and mode:

```text
[Whiteboard] POST  slot=0 email='a@mail.com' kind=SKILL_TARGET mode=EXCLUSIVE 'Power_Drain'(id=25) target=55 group=7 holders=1 expires_in=1150ms
[Whiteboard] CLEAR slot=0 email='a@mail.com' kind=SKILL_TARGET mode=EXCLUSIVE 'Power_Drain'(id=25) target=55 group=7 lifetime=438ms reason=owner_clear
[Whiteboard] SWEEP slot=1 email='b@mail.com' kind=MINION_CORPSE mode=EXCLUSIVE key=0 target=336 group=7 lifetime=1200ms reason=expired
```

## Known Limitations

- Existing skill-target coordination only covers paths routed through
  `BuildMgr.CastSkillID`. HeroAI's direct `SkillBar.UseSkill` path must be
  wired separately for non-BuildMgr locks such as minion corpse claims.
- There is still a frame-grain race window: two clients can pass a read gate
  before either posts. The lock reduces collisions; it does not provide a
  kernel-level compare-and-swap.
- `ClearIntentsByOwner` clears every lock owned by that account, not only one
  kind. That matches current cast cleanup but may need narrower clear helpers
  if long-lived cooldown locks are added.
- Shared-memory layout changed when generic lock fields were added. All live
  clients must restart together before testing.

## Verification

Compile the changed modules:

```powershell
python -m py_compile `
  "Py4GWCoreLib/enums_src/Whiteboard_enums.py" `
  "Py4GWCoreLib/enums.py" `
  "Py4GWCoreLib/GlobalCache/shared_memory_src/IntentStruct.py" `
  "Py4GWCoreLib/GlobalCache/shared_memory_src/AllAccounts.py" `
  "Py4GWCoreLib/GlobalCache/SharedMemory.py" `
  "Py4GWCoreLib/BuildMgr.py"
```

Runtime checks:

- `PostIntent` / `IsIntentClaimed` still block duplicate skill-target casts.
- `PostLock` rejects locks with `expires_at_tick <= now`.
- `IsLockBlocked` blocks exclusive locks after another owner posts.
- `IsLockBlocked` allows shared/semaphore locks until `MaxHolders` is reached.
- `IsLockSatisfied` returns true only after enough barrier participants post.
- Expired locks stop blocking immediately and are later removed by sweep.
