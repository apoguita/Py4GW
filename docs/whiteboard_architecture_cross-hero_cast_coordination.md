# whiteboard architecture — cross-hero cast coordination

## Purpose

This document describes the cross-hero cast-intent whiteboard — a shared-memory
intent registry that lets multiple HeroAI accounts running in the same
multibox team coordinate on `(skill_id, target_agent_id)` claims so they do
not stomp each other's casts.

The system answers a single question per cast attempt:

> Has another hero in my isolation group already claimed this skill against
> this target?

If yes, the local hero skips the cast and continues evaluating the rest of
its bar. If no, the local hero posts its own claim and fires.

Granularity is intentionally `(skill_id, target_agent_id)` — another hero
can still cast the same skill on a different enemy, and any hero can stack
different skills on the same target.

The implementation lives in:

- `Py4GWCoreLib/GlobalCache/shared_memory_src/IntentStruct.py` — slot schema
- `Py4GWCoreLib/GlobalCache/shared_memory_src/AllAccounts.py` — slot array + methods + debug logger
- `Py4GWCoreLib/GlobalCache/shared_memory_src/Globals.py` — capacity + budget constants
- `Py4GWCoreLib/GlobalCache/SharedMemory.py` — manager wrappers + sweep tick
- `Py4GWCoreLib/GlobalCache/Whiteboard.py` — general `(kind, key)` opt-in registry
- `Py4GWCoreLib/Builds/Skills/_whiteboard.py` — thin skill-scoped wrapper (`kind="skill"`) that exposes the decorator + `is_registered(skill_id)` API used by the combat loop
- `HeroAI/custom_skill_src/skill_types.py` — per-skill opt-in flag (`CoordinatesViaWhiteboard`)
- `Py4GWCoreLib/BuildMgr.py` — read-gate + write + owner self-clear inside `CastSkillID`
- `Py4GWCoreLib/py4gwcorelib_src/ActionQueue.py` — `WHITEBOARD_SWEEP` named queue (defined; sweep currently runs inline)

## Motivation

Multibox HeroAI teams running identical or near-identical skill bars
evaluate their combat pipeline in lockstep. When the same trigger appears —
for example a caster begins channeling a spell that all three Energy Surge
mesmers want to interrupt with Power Drain — every hero fires Power Drain
at the same target on the same frame. Only one cast lands; the others
waste recharge and energy.

On Power Drain specifically, each wasted cast also forfeits ~29 energy of
cons-boosted return, so the DPS loss compounds. The same problem appears
on AoE pressure skills like Cry of Pain, Cry of Frustration, Mistrust, and
Overload.

An adjacent solution exists in some custom-behavior frameworks
(string-keyed TTL locks held in a dictionary), but it is a binary
held/not-held ledger with no payload — it cannot express **what** is being
done, on **which** target, or expire before the TTL when a cast finishes
early. A behavior-tree blackboard does not work either because it
propagates per-tree and is not visible across accounts.

The whiteboard is a typed, cross-account, shared-memory intent registry
that solves both shortcomings.

## Architecture

```
                       Process A (hero 1)               Process B (hero 2)
                       ─────────────────                ─────────────────
                       BuildMgr.CastSkillID             BuildMgr.CastSkillID
                            │                                │
                       (1)  ▼ read-gate                  (1) ▼ read-gate
                       IsIntentClaimed?                  IsIntentClaimed?
                            │  no                            │  yes → skip
                       (2)  ▼ post
                       PostIntent(...)
                            │
                       (3)  ▼ UseSkill
                            │
                       (4)  ▼ on cast-finish
                       ClearIntentsByOwner()


                              ┌─────────────────────────────┐
                              │  Py4GW Shared Memory File   │
                              │  (single OS-level mapping)  │
                              │                             │
                              │   AllAccounts.Intents[64]   │
                              │   ┌───────────────────────┐ │
                              │   │ slot 0  IntentStruct  │ │
                              │   │ slot 1  IntentStruct  │ │
                              │   │ ...                   │ │
                              │   │ slot 63 IntentStruct  │ │
                              │   └───────────────────────┘ │
                              │                             │
                              └─────────────────────────────┘

                       ▲                                    ▲
                       │ Process A reads/writes via         │ Process B reads/writes via
                       │ GLOBAL_CACHE.ShMem.*Intent*        │ GLOBAL_CACHE.ShMem.*Intent*
                       │                                    │
                  ─────┴────────────────────────────────────┴─────
                                Periodic sweep (any process)
                              SweepExpiredIntents(now_tick)
                              clears slots past ExpiresAtTick
```

Three layers:

1. **Schema** — A fixed-size `IntentStruct[SHMEM_MAX_INTENTS]` array embedded in
   `AllAccounts`, the existing shared-memory `Structure` every Py4GW process
   already attaches to. No new OS handle, no new lock — same `_pack_ = 1`
   layout pattern used by `Inbox` / `SharedMessageStruct`.
2. **Coordination point** — `BuildMgr.CastSkillID` is the single funnel for
   matched-build casts. Read-gate runs after the interrupt-feasibility check
   and before `UseSkill`; write happens immediately before `UseSkill`;
   owner self-clear runs at the top of `_process_phase` on the local-cast-
   pending True→False transition.
3. **Reclaim** — Three redundant expiry paths (time budget, owner self-clear,
   periodic sweep) prevent stale slots from dead-locking a `(skill, target)`
   combo.

## Slot Schema

Defined in `IntentStruct.py`:

| Field              | Type                            | Meaning                                                           |
|--------------------|---------------------------------|-------------------------------------------------------------------|
| `OwnerEmail`       | `c_wchar * SHMEM_MAX_EMAIL_LEN` | Account email of the hero that posted the claim. Used for owner-side clears and as the read-gate exclude key. |
| `SkillID`          | `c_uint`                        | First half of the granularity key.                                |
| `TargetAgentID`    | `c_uint`                        | Second half of the granularity key. Local agent id from the caster's perspective; safe in multibox because agent ids are stable across clients within a session. |
| `IsolationGroupID` | `c_uint`                        | Scoping key. Heroes only honor claims with the same group id, so separate multibox teams running on the same machine never collide. |
| `PostedAtTick`     | `c_uint`                        | `Py4GW.Game.get_tick_count64()` snapshot at post time. Used for lifetime calculations and debug logs.        |
| `ExpiresAtTick`    | `c_uint`                        | `PostedAtTick + activation + aftercast + ping_budget`. Reader treats `now >= ExpiresAtTick` as empty even if `Active` is still true. |
| `Active`           | `c_bool`                        | Allocation flag. The slot scanner picks the first slot with `Active == False`. |

Capacity (`Globals.py`):

```python
SHMEM_MAX_INTENTS = 64                      # array length
SHMEM_INTENT_DEFAULT_PING_BUDGET_MS = 150   # added to expiry window
SHMEM_INTENT_SWEEP_INTERVAL_MS = 100        # sweep cadence
```

64 slots covers a lot of concurrent claims — even an 8-account team firing
4 short skills each gives only 32 in-flight slots in the worst case, well
under capacity.

## Two Opt-in Surfaces

A skill participates in whiteboard coordination when **either** of the
following is true:

### Surface 1 — Decorator on the skill method

For skills implemented in `Py4GWCoreLib/Builds/Skills/{profession}/{attribute}.py`:

```python
from Py4GWCoreLib.Builds.Skills._whiteboard import coordinates_via_whiteboard

class DominationMagic:
    ...
    @coordinates_via_whiteboard(Skill.GetID("Cry_of_Frustration"))
    def Cry_of_Frustration(self) -> BuildCoroutine:
        ...
```

The decorator calls `register(skill_id)` at import time, populating a
module-level `set[int]`. Zero-cost after first import — the read-gate
checks the set with a single `int` lookup.

### Surface 2 — `CustomSkill` metadata flag

For skills routed through HeroAI's custom-skill table:

```python
# In HeroAI/custom_skill_src/{profession}.py
skill = CustomSkill(skill_id, "Power_Drain", ...)
skill.CoordinatesViaWhiteboard = True
```

`BuildMgr._is_whiteboard_skill` unions both surfaces — a skill enabled by
either path participates. This means a skill module can opt itself in
without touching HeroAI's custom-skill table, and an existing custom-skill
entry can opt in without modifying the skill module.

## Lifecycle

### POST — claim a slot

`BuildMgr.CastSkillID` calls `_whiteboard_post_intent` immediately before
`GLOBAL_CACHE.SkillBar.UseSkill`. The expiry budget is computed from the
skill's own activation and aftercast metadata:

```
expires_at = now
           + max(500, activation_ms + aftercast_ms)
           + SHMEM_INTENT_DEFAULT_PING_BUDGET_MS
```

The 500 ms floor protects against zero-activation skills (signets, instants)
that should still hold their claim long enough for the cast to commit.

### READ — gate the cast

Just before posting, `_whiteboard_is_claimed` calls
`GLOBAL_CACHE.ShMem.IsIntentClaimed`, which scans the slot array and
returns true if **any** slot satisfies all of:

- `Active == True`
- `SkillID == skill_id`
- `TargetAgentID == target_agent_id`
- `IsolationGroupID == my_group_id`
- `OwnerEmail != my_email`  (own-account stacking is intentionally allowed)
- `now < ExpiresAtTick`

If true, the cast attempt returns `False` and the skill rotation continues.
The read path is wrapped in `@frame_cache` so multiple skill evaluators on
the same frame share one scan.

### CLEAR — three redundant expiry paths

#### Path 1: time-budget expiry (reader-side)

The reader treats any slot with `now >= ExpiresAtTick` as empty even if
`Active` is still true. This means a stale slot never blocks a cast — at
worst it consumes a slot until the next sweep zeroes it.

#### Path 2: owner self-clear (live release)

`_whiteboard_owner_self_clear` runs at the top of `_process_phase` on every
combat tick. It detects the local-cast-pending True→False transition (the
moment after `UseSkill` resolves) and calls
`GLOBAL_CACHE.ShMem.ClearIntentsByOwner(my_email)` to zero every slot owned
by the local account.

This is the dominant release path in production. Empirically it cuts the
typical claim lifetime to ~390–500 ms for short skills and ~1100–1500 ms
for Mistrust, versus the budget ceiling of ~1156 ms / ~2906 ms.

The transition logic uses two pieces of caster state:

```python
prev = self._wb_prev_cast_pending
pending = self._is_local_cast_pending()
self._wb_prev_cast_pending = pending
if not (prev and not pending):       # only fire on True → False
    return
if not self._wb_posted_this_cast:    # only fire if I actually posted
    return
GLOBAL_CACHE.ShMem.ClearIntentsByOwner(email)
self._wb_posted_this_cast = False
```

#### Path 3: periodic sweep (safety net)

`SweepExpiredIntents(now)` walks the whole array and zeroes every slot
where `Active == True` and `now >= ExpiresAtTick`. It is invoked from
`Py4GWSharedMemoryManager.update_callback` at a cadence of
`SHMEM_INTENT_SWEEP_INTERVAL_MS` (100 ms) via a `ThrottledTimer`.

A `WHITEBOARD_SWEEP` named queue exists in `ActionQueueManager` for future
use, but the sweep currently runs **inline** in the manager callback —
no code path drains named action queues automatically, so dispatching
through the queue would dead-letter the work.

## Public API Surface

External callers should only touch `GLOBAL_CACHE.ShMem.*Intent*`:

| Method                                                                          | Purpose                                                                  |
|---------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| `PostIntent(owner_email, skill_id, target_agent_id, expires_at_tick, group?)`   | Allocate a slot; returns slot index or -1 if full.                       |
| `ClearIntentsByOwner(owner_email)`                                              | Zero every slot whose `OwnerEmail` matches; returns count cleared.       |
| `IsIntentClaimed(skill_id, target_agent_id, group_id, exclude_email, now_tick)` | Read-gate primitive; frame-cached.                                       |
| `SweepExpiredIntents(now_tick)`                                                 | Compact pass; returns count cleared.                                     |
| `GetAllIntents()`                                                               | Debug/probe helper; returns `[(index, IntentStruct), ...]` for active slots. Frame-cached. |

`BuildMgr` keeps four private helpers (`_is_whiteboard_skill`,
`_whiteboard_is_claimed`, `_whiteboard_post_intent`,
`_whiteboard_owner_self_clear`) so the wiring inside `CastSkillID` reads
as four short calls. They are not part of the public surface — outside
code should not reach into them.

## How to Add a New Skill

### Recipe A — decorator (preferred for `Builds/Skills/**`)

1. Open the relevant attribute file, e.g.
   `Py4GWCoreLib/Builds/Skills/mesmer/InspirationMagic.py`.
2. Import the decorator at the top of the file:

   ```python
   from Py4GWCoreLib.Builds.Skills._whiteboard import coordinates_via_whiteboard
   ```

3. Decorate the skill method:

   ```python
   @coordinates_via_whiteboard(Skill.GetID("Power_Drain"))
   def Power_Drain(self) -> BuildCoroutine:
       ...
   ```

4. No other changes. Restart the process; the registry picks it up at
   import time.

### Recipe B — `CustomSkill` flag (for HeroAI's table-driven path)

1. Open the relevant profession file under `HeroAI/custom_skill_src/`.
2. Find the `CustomSkill` definition for the skill.
3. Set the flag:

   ```python
   skill.CoordinatesViaWhiteboard = True
   ```

4. Done. The flag is read from `BuildMgr._is_whiteboard_skill` on every
   matched-build cast attempt.

### Recipe C — opt out

Decorator: remove the `@coordinates_via_whiteboard(...)` line.
Custom-skill flag: set `CoordinatesViaWhiteboard = False` (or remove the
line — the default is `False`).

To rip a skill from a registry programmatically (e.g., from a test harness
or a feature toggle):

```python
from Py4GWCoreLib.Builds.Skills._whiteboard import unregister
unregister(skill_id)
```

## When To Opt In

A skill is a good candidate when **all** of the following are true:

- Multiple heroes on the team can fire it on the same frame against the
  same target.
- Only one cast actually lands or matters.
- The skill has meaningful recharge or energy cost — a wasted cast is a
  real loss.

Examples that fit:

- Interrupts (Power Drain, Power Spike, Cry of Frustration, Mistrust)
- AoE pressure / energy denial (Cry of Pain, Overload, Energy Surge)
- Hex / enchantment removal where one removal is enough (Shatter Hex,
  Drain Enchantment)

Examples that do **not** fit:

- Self-buffs and self-targeted upkeep (no `target_agent_id`).
- Ally-targeted heals where stacking is desirable.
- Single-account paths (`SkillManager.Autocombat`) — there's nothing to
  stomp.
- Skills tagged with `SkillNature.Resurrection` and similar where the
  team **wants** redundant casting.

## Performance Characteristics

Measured across four-account teams during live combat (Energy Surge x2,
Ineptitude x1, Energy Surge x1, all in the same isolation group):

| Skill class                         | Old expired-only baseline | New median (owner_clear) | Floor (BT-tick-bound) |
|-------------------------------------|---------------------------|--------------------------|-----------------------|
| Short skills (PD, CoF, CoP, Overload) | ~1156 ms                  | ~470 ms                  | ~390 ms               |
| Mistrust                            | ~2906 ms                  | ~1300 ms                 | ~672 ms               |

The 390 ms floor is the BT tick rate — the minimum time to detect
`_is_local_cast_pending` going True→False and write the clear into
shared memory. To go lower would require a synchronous post-cast clear
inside `CastSkillID` itself, or a callback-driven clear hooked into the
engine's `Player.IsCasting()` transition.

The reader path (`IsIntentClaimed`) is cheap enough to call per-slot per
skill evaluation: one O(N) scan over 64 slots, frame-cached so multiple
evaluators on the same frame share one pass.

## Scaling

### More slots

`SHMEM_MAX_INTENTS = 64` is sized for typical 4–8 account teams with each
account holding 1–4 in-flight claims. To raise the ceiling, change the
constant in `Globals.py` — the `IntentStruct[N]` array resizes
automatically and `AllAccounts.reset()` already iterates the full array.
Cost is linear: each slot is `64 + 4 + 4 + 4 + 4 + 4 + 1 + padding ≈ 88`
bytes, so 256 slots is ~22 KB.

### More teams on the same machine

`IsolationGroupID` already partitions claims by team. Two multibox teams
running on the same machine with different group ids never see each
other's slots. The group id resolution lives in
`AllAccounts._get_local_group_id` and is keyed off the existing
party-isolation logic.

### More skill classes

The two opt-in surfaces are independent and additive. New skill modules
under `Py4GWCoreLib/Builds/Skills/**` can decorate methods at import time
without touching HeroAI; new HeroAI custom-skill entries can flip
`CoordinatesViaWhiteboard = True` without touching the build modules.

### More consumer kinds (loot, resurrection, dialog, etc.)

The opt-in registry at `Py4GWCoreLib/GlobalCache/Whiteboard.py` is keyed
by `(kind, key)`, not just skill id. Any cross-hero coordination problem
that can be expressed as "one hero claims, the others skip" can plug in
without touching the schema, the slot allocator, or the expiry paths.

Examples that fit the same shape:

| Use case             | Suggested `kind`  | `key`        | Read-gate question                          |
|----------------------|-------------------|--------------|---------------------------------------------|
| Loot pickup          | `"loot"`          | `item_id`    | Has another hero already claimed this drop? |
| Resurrection         | `"resurrect"`     | `agent_id`   | Has another hero already taken this rez?    |
| NPC dialog           | `"dialog"`        | `npc_id`     | Has another hero already started this turn-in? |
| Consumable usage     | `"consumable"`    | `model_id`   | Has another hero already popped a cons?     |
| Pull / aggro lead    | `"pull"`          | `pack_id`    | Has another hero already pulled this pack?  |

To wire a new consumer:

1. **Pick a `kind` string.** Lowercase, snake-case, unique. Add it to the
   table above so future contributors see it.
2. **Add a thin wrapper module.** Mirror `Py4GWCoreLib/Builds/Skills/_whiteboard.py`:
   pre-fill `KIND = "loot"` (or whatever) and re-export `register`,
   `is_registered`, `coordinates_via_whiteboard`, etc. with the
   consumer-specific argument shape (`item_id` instead of `skill_id`).
   This keeps the call sites readable and prevents accidental
   cross-kind collisions.
3. **Wire the read-gate and write at the consumer's funnel.** For loot
   that funnel is wherever pickup is dispatched; for resurrection it's
   the resurrection routine; etc. Pattern is the same four-call shape
   `BuildMgr.CastSkillID` uses today: `is_registered` → `IsIntentClaimed`
   → action → `ClearIntentsByOwner` (or rely on the time-budget path).
4. **Pick an expiry budget.** Skills derive theirs from
   `activation + aftercast + ping_budget`. Other kinds need a
   kind-appropriate budget — for loot, "time to walk and pick up"; for
   resurrection, the cast time of the rez skill plus margin. The
   `expires_at_tick` argument to `PostIntent` is set by the caller, so
   each consumer picks its own.

The shared-memory layer does not need to change for any of this. Slot
capacity (`SHMEM_MAX_INTENTS = 64`) is the only thing that might need
revisiting if the team is running many simultaneous consumers — bump
`Globals.py` if the slot array starts running hot.

### More aggressive coordination

The current granularity is `(skill_id, target_agent_id)`. Tighter
coordination (e.g., "only one PD on this target this *second*") could be
layered on by adding a per-skill cooldown field to `IntentStruct` and
checking it in the reader. Looser coordination (e.g., "only one
interrupt of any kind on this target") could be layered by adding a
`CoordinationGroup` enum and treating slots in the same group as
mutually-exclusive in the reader.

Both extensions only require changes to `IntentStruct` + the reader; the
write path and lifecycle do not change.

### Cross-account ownership transfer

Not supported and not needed. Each slot is owned by exactly one email
and only that email can clear it via `ClearIntentsByOwner`. The reader
ignores own-email slots so within-account stacking still works.

## Known Limitations

- **Single combat funnel** — Coordination only kicks in inside
  `BuildMgr.CastSkillID`. Skill paths that bypass it (legacy direct
  `SkillBar.UseSkill` calls in widgets, custom bots, or single-account
  HeroAI fallbacks) are not coordinated. Adding coverage to a new path
  means routing it through `_whiteboard_post_intent` /
  `_whiteboard_is_claimed`.

- **Frame-grain race window** — Two heroes can both pass the read-gate on
  the same frame if neither has posted yet. At worst both cast; the
  whiteboard makes the situation strictly better than today, never worse.
  The window is bounded by one BT tick and shrinks as tick rate
  increases.

- **Owner self-clear depends on `_is_local_cast_pending`** — If a cast
  fails between `UseSkill` and the next tick (e.g., target dies, player
  knocked down), the cast-pending timer may never flip True, in which
  case the slot rides the time-budget expiry. Sweep catches it on the
  next 100 ms cycle.

- **No cross-team coordination** — Teams with different `IsolationGroupID`
  stay isolated by design. If a future use case wants global
  coordination, swap the group filter for a wildcard in
  `IsIntentClaimed`.

- **Sweep is inline, not queued** — `WHITEBOARD_SWEEP` is registered in
  `ActionQueueManager` but the sweep runs synchronously inside
  `update_callback` because no code drains named queues automatically in
  this repo. If a queue-drainer ever gets added, switch the call site.

## Debug Logging

Toggled by `WHITEBOARD_DEBUG: bool` in
`Py4GWCoreLib/GlobalCache/shared_memory_src/AllAccounts.py`. `False` by
default; flip to `True` while testing.

When enabled, every POST / CLEAR / SWEEP emits a single ConsoleLog line
tagged `Whiteboard`:

```
[Whiteboard] POST  slot=0 email='alice@mail.com' 'Power_Drain'(id=25) target=55 group=7 expires_in=1150ms
[Whiteboard] CLEAR slot=0 email='alice@mail.com' 'Power_Drain'(id=25) target=55 lifetime=438ms reason=owner_clear
[Whiteboard] SWEEP slot=1 email='bob@mail.com'   'Mistrust'(id=979) target=336 lifetime=2906ms reason=expired
```

Skill names are resolved through `GLOBAL_CACHE.Skill.GetName(skill_id)`
with a fallback to `skill={id}` on lookup failure. The flag can also be
flipped at runtime:

```python
from Py4GWCoreLib.GlobalCache.shared_memory_src import AllAccounts as _wb
_wb.WHITEBOARD_DEBUG = True
```

## Verification

A standalone probe script lives at the project root: `whiteboard_probe.py`.
It exercises the four primitives end to end:

1. Posts two intents with different emails / targets.
2. Confirms `IsIntentClaimed` returns true for one email and false for
   the other.
3. Advances `now_tick` past `ExpiresAtTick` and confirms the reader
   treats expired slots as empty.
4. Calls `SweepExpiredIntents(future_now)` and confirms slots go
   `Active = False`.

Run it from a Py4GW REPL or import-and-call to verify the shared-memory
plumbing in isolation from combat.

For live verification, set `WHITEBOARD_DEBUG = True`, run a 2+ account
team, and confirm:

- POST lines outnumber SWEEP lines (owner_clear is dominant).
- No `(skill_id, target_agent_id)` collision posts within an unexpired
  window from a different `OwnerEmail`.
- Cross-account SWEEP lines appear (any account observes other accounts'
  stale slots), confirming the shared-memory mapping is healthy.

## Wiring Reference

### Read-gate + write — `Py4GWCoreLib/BuildMgr.py::CastSkillID`

```python
# Whiteboard read gate — skip if another hero in my isolation group
# already claimed this (skill_id, target_agent_id). Opt-in per skill.
if self._is_whiteboard_skill(skill_id) and self._whiteboard_is_claimed(skill_id, target_agent_id):
    return False

slot = SkillBar.GetSlotBySkillID(skill_id)

# Whiteboard write — claim (skill_id, target_agent_id) so other heroes
# in my isolation group skip this combo until my cast resolves.
if self._is_whiteboard_skill(skill_id):
    self._whiteboard_post_intent(skill_id, target_agent_id)

GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=target_agent_id, aftercast_delay=aftercast_delay)
self._mark_local_cast_pending(aftercast_delay)
```

### Owner self-clear — `Py4GWCoreLib/BuildMgr.py::_process_phase`

```python
def _process_phase(self, handler, is_in_combat):
    # Whiteboard owner self-clear — release my (skill, target) slots on
    # the cast-finish transition so sibling accounts can reuse them
    # immediately.
    self._whiteboard_owner_self_clear()
    if not self.CanProcess():
        ...
```

### Sweep tick — `Py4GWCoreLib/GlobalCache/SharedMemory.py::update_callback`

```python
if self._intent_sweep_timer.IsExpired():
    now = Py4GW.Game.get_tick_count64()
    self.SweepExpiredIntents(now)
    self._intent_sweep_timer.Reset()
```
