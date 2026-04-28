# HeroAi Interrupt Feasibility

## Purpose

This document describes the interrupt-feasibility system that decides whether a hero should fire an interrupt skill at a casting enemy. The system answers a single question per cast attempt:

> Will our interrupt actually land before the target's cast completes?

If the answer is no — because the cast is too far along, the target is out of range, or our own activation plus ping plus reaction margin won't fit in the remaining window — the gate skips the cast and the hero conserves the skill for a feasible target later.

The implementation lives in:

- `HeroAI/interrupt.py` — sampler, classifier, decision helper, outcome logger, modifier tables
- `HeroAI/combat.py` — the data-driven evaluator gate (one of two call sites)
- `Py4GWCoreLib/BuildMgr.py` `CastSkillID` — the matched-build evaluator gate (the other call site)
- `HeroAI/custom_skill_src/*.py` — the source-of-truth interrupt classification (`SkillNature.Interrupt` tags)

## Two Evaluator Paths

HeroAI fires interrupts through two independent evaluators. The gate is wired into both.

### Matched-build evaluator

Each matched-build template (`Py4GWCoreLib/Builds/{Profession}/...`) defines a rotation that calls per-skill coroutines in `Py4GWCoreLib/Builds/Skills/{profession}/{attribute}.py`. Those coroutines all funnel through `BuildMgr.CastSkillID`, which is where Gate #2 lives.

Path tag in logs: `EVAL: MATCHED -> 'Skill_Name'`.

### Data-driven (unmatched) evaluator

When a hero's bar doesn't match any template, HeroAI falls back to the data-driven path in `CombatClass.AreCastConditionsMet`. Inside the `Conditions.IsCasting` block, Gate #1 runs the same feasibility check on any skill tagged `SkillNature.Interrupt`.

Path tag in logs: `EVAL: UNMATCHED -> 'Skill_Name'`.

Both gates call the same `is_interrupt_feasible` helper. The verdict is identical regardless of path.

## Classifier

The single source of truth for "is this skill an interrupt?" is the `Nature` field set in `HeroAI/custom_skill_src/{profession}.py`. Every interrupt skill is tagged:

```python
skill.Nature = SkillNature.Interrupt.value
```

`HeroAI/interrupt.py` walks `custom_skill_data_handler.skill_data` once on first use and caches the set of interrupt-classified skill_ids in `_INTERRUPT_SKILL_IDS`. The matched-build gate calls `is_classified_as_interrupt(skill_id)` to decide whether to apply the feasibility check. Non-interrupt skills short-circuit with one set lookup of overhead.

To add a new interrupt skill: tag it `SkillNature.Interrupt.value` in `custom_skill_src/`. The registry picks it up on next process start. No interrupt-side code changes required.

## Decision Math

Two formulas, one for spells/signets and one for attack skills. The branch is on `GLOBAL_CACHE.Skill.Flags.IsAttack(skill_id)`.

### Spell / signet path

```
our_cast_ms = base_activation_ms
            * (0.955 ^ FC_rank)             # Fast Casting (via apply_fast_casting)
            * capped_non_fc_multiplier      # consumables, spirits, hexes
```

Fast Casting is exempt from the cap. The non-FC multiplier is clamped to `[_NON_FC_MIN_MULT, _NON_FC_MAX_MULT]` (0.75 to 2.5) and applied to the FC-reduced activation.

### Attack-skill path

Attack skills don't use Fast Casting or the spell-side modifier table. Per the half-interval rule, they release/connect at half their stated activation; the second half is return-to-neutral and irrelevant for interrupt feasibility.

```
release_ms       = (stated_activation_ms / 2) * IAS_modifier
flight_ms        = distance_gw * _BOW_FLIGHT_MS_PER_GW   (only when wielding a bow)
our_cast_ms      = release_ms + flight_ms
```

`IAS_modifier` is the live `Agent.GetAttackSpeedModifier(player_id)` (Frenzy = 0.66, no buff = 1.0). Flight time only applies when the player wields a bow. Bow subtype is not exposed by Py4GW, so every bow is treated as Recurve with the constant `_BOW_FLIGHT_MS_PER_GW = 0.42`.

### Common decision step

```
budget_ms     = our_cast_ms + (ping_ms * 1.2) + reaction_margin_ms
remaining_ms  = enemy_total_ms - elapsed_ms                # observed by sampler
feasible      = remaining_ms >= budget_ms
```

`reaction_margin_ms` defaults to 50.

## Modifier Tables (Spell / Signet path only)

`HeroAI/interrupt.py` holds four tables that drive the non-FC multiplier. Each entry is `(skill_id_name, multiplier)`. All resolved through `_resolve_skill_id` which caches successful lookups and emits a one-shot warning on unresolved names.

| Table | Stack rule | Applies to |
|---|---|---|
| `_CONSUMABLE_CAST_MODS` | multiplicatively with each other | all skills |
| `_SPELL_ONLY_SPEEDUPS` | multiplicatively | spells only (Mindbender) |
| `_SLOWING_HEXES_ALL` | take MAX (hexes don't stack) | all skills |
| `_SLOWING_HEXES_SPELLS` | take MAX, jointly with `_ALL` | spells only |

The raw product of all active modifiers is clamped to `[0.75, 2.5]` before being applied to the FC-reduced activation.

Modifier names refer to the **buff effect** that lands on the agent, not the item or skill that grants it. Example: `Slice_of_Pumpkin_Pie` (the item) does not resolve; `Pie_Induced_Ecstasy` (the buff) does. Most other consumables follow the convention `<Item_Name>_Rush` or `<Item_Name>_item_effect`.

To add a new modifier: append a tuple to the relevant table. If the lookup fails on first use, the one-shot warning will surface in the log so a typo is visible.

## Range Gate

Range cap depends on skill type and wielded weapon:

- Spell / signet → `Range.Spellcast.value` (1248 gw)
- Attack skill + bow → `Range.Spellcast.value` (1248 gw)
- Attack skill + melee → `_MELEE_TOUCH_RANGE_GW` (144 gw)

Resolved by `_max_interrupt_range_gw(our_skill_id)`. Targets past the cap are skipped with a `SKIP: out of {label} range` log line. Melee swings physically can't connect past 144 gw regardless of timing budget; this prevents the gate from green-lighting impossible-to-land melee interrupts.

## Per-Frame Sampler

`CastObserver` is a singleton sampler in `HeroAI/interrupt.py` that runs every frame via a `PyCallback` registration (mirrors the `CombatEvents.Enable()` pattern in `Py4GWCoreLib/CombatEvents.py`).

Each frame it scans `AgentArray.GetEnemyArray()` filtered to `Range.SafeCompass.value` and tracks observed casts in:

```
_OBSERVATIONS: dict[(agent_id, casting_skill_id), first_seen_ms]
```

This gives the gate `elapsed_ms = now_ms() - first_seen_ms` for free when the feasibility helper is called — no projection or "first-sight" estimation. Entries are dropped immediately when the agent stops casting or switches skills, and aged out after 10 seconds of staleness.

This is why the gate doesn't depend on `CombatEvents`: the sampler is our local replacement for the deactivated event stream.

## Outcome Logging

When a feasibility check passes and a cast is queued, the gate calls `_queue_outcome(target, enemy_skill, our_skill)`. The sampler sweeps pending outcomes each frame and logs:

- `[outcome] SUCCESS` — sampler observed the cast end (target dropped that skill or switched)
- `[outcome] FAIL` — the cast ran past its nominal duration plus a 500 ms grace

Note: the current implementation reports SUCCESS whenever the cast ends, including casts that completed naturally. This produces some false-positive SUCCESS lines in logs. Distinguishing a real interrupt (cast ended early) from a natural completion requires comparing actual duration to nominal duration. That refinement is parked for later.

## Debug Logging

Toggled by `INTERRUPT_DEBUG: bool` at module top. `True` during the testing phase; flip to `False` once dialed in.

Each decision emits a multi-line log block at `Info` level (path tag) and `Debug` level (math breakdown):

```
[rupt] Our 'Power_Drain', Margonite Anur Su is casting 'Lightning_Hammer' → FEASIBLE
       distance=945gw (spellcast max 1248gw)
       modifiers: Quickening_Zephyr (x0.75) -> x0.75
       target_remaining=453ms vs our_budget=202ms  [cast=78ms (FC 19, mods x0.75) + ping=62ms*1.2=74ms + margin=50ms]
[rupt] EVAL: MATCHED -> 'Power_Drain'
[outcome] SUCCESS our=Power_Drain(25) target=... elapsed=203ms
```

Skip lines:

```
[rupt] Our '...', ... → SKIP: cast too far along
[rupt] Our '...', ... → SKIP: out of melee touch range (distance=420gw, max=144gw)
[rupt] Our '...', ... → SKIP: target skill is instant (nothing to interrupt)
```

Path tags (`EVAL: MATCHED` / `EVAL: UNMATCHED`) are emitted at `Info` level so they remain visible regardless of `INTERRUPT_DEBUG`.

## Public API Surface

External callers are limited to two files. Both call only:

- `is_interrupt_feasible(target_agent_id, our_skill_id, fast_casting_level, ping_ms, *, reaction_margin_ms=50, debug=None) -> bool`
- `is_classified_as_interrupt(skill_id) -> bool`
- `_queue_outcome(target_id, enemy_skill_id, our_skill_id)` (private but used externally)
- `_log_eval_path(our_skill_id, path)` (same)
- `_get_player_fast_casting_level()`, `_PING_HANDLER` (helpers used by `BuildMgr` only)

## Wiring

### Gate #1 — `HeroAI/combat.py` `AreCastConditionsMet`

Replaces the legacy `>= 0.250s` activation proxy with the feasibility math when `Nature == SkillNature.Interrupt`. Non-interrupt casting features keep the legacy gate. Imports `is_interrupt_feasible`, `_queue_outcome`, `_log_eval_path` at the top of the file.

### Gate #2 — `Py4GWCoreLib/BuildMgr.py` `CastSkillID`

Inserted after `_validate_target_for_skill_cast` and before the whiteboard logic. Imports the helpers lazily from `HeroAI.interrupt` to avoid circular imports at module load. Wrapped in `try/except Exception: pass` so any helper failure degrades gracefully to legacy behavior.

## Known Limitations

- **Bow subtype not detected** — every Bow weapon uses Recurve flight constants (0.42 ms/gw). Longbow / Shortbow / Hornbow / Flatbow not differentiated.
- **Ranged attack skills (non-bow)** — Disrupting Dagger (thrown dagger) and Disrupting Throw (spear) currently get `flight_ms = 0`, slightly underestimating their time-to-impact.
- **`CombatEvents` is deactivated** — we cannot read `OnSkillInterrupted` / `OnSkillFinished` events, so outcome detection is heuristic (any cast end → SUCCESS). Distinguishing real interrupts from natural completions requires comparing actual cast duration to nominal duration; not yet implemented.
- **Pet skills excluded** — `Savage_Pounce` is not classified as an interrupt; the pet's attack speed is its own and our IAS reads the player's modifier. Re-tagged to `SkillNature.Offensive` in `custom_skill_src/ranger.py`.
- **HCT weapon mods not modeled** — 20% HCT prefix/suffix items are probabilistic (20% chance to halve cast); we don't simulate them, so heroes wielding such weapons land slightly faster than the math predicts. Acceptable on the safe side.
- **Duplicate outcome records** — the matched-build rotation may pass multiple skills through the gate within the same frame; each queues an outcome before any actually fires. Only one will cast (the others lose the race to `_is_local_cast_pending`), but all queued outcomes resolve to the same observed cast-end signal. Visible as duplicate SUCCESS lines.
