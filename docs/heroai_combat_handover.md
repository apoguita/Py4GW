# HeroAI Combat Handover

## Scope

This document is the working handover for the HeroAI combat pipeline centered on:

- `HeroAI/combat.py`
- `HeroAI/targeting.py`
- `HeroAI/utils.py`
- `Py4GWCoreLib/routines_src/Agents.py`
- `Py4GWCoreLib/routines_src/Checks.py`
- shared-memory and effect cache reads used by combat decisions

The focus is performance-sensitive decision making during per-frame combat evaluation.

## Current Direction

Recent work has been pushing the combat path toward:

- frame-local caching for repeated reads
- single-pass scans instead of filter-then-sort chains
- cheaper early exits before expensive target resolution
- delaying shared-memory and effect checks until they are truly needed

Examples already moved in that direction:

- `Routines.Agents.GetNearestEnemy*` now use single-pass nearest selection helpers
- `HeroAI/targeting.py` lowest-ally selectors now sort by real values and defer expensive effect checks
- shared-memory getters and effect getters now use `frame_cache`
- `Checks.Skills.GetEnergyCostWithEffects(...)` is frame-cached
- `Checks.Skills.apply_expertise_reduction(...)` now exits early for non-primary-Rangers, with the `Ranger of Melandru` exception

## Combat Flow

High-level per-skill path:

1. `CombatClass.IsReadyToCast(slot)`
2. `CombatClass.GetAppropiateTarget(slot)`
3. `CombatClass.AreCastConditionsMet(slot, vTarget)`
4. `CombatClass.HasEffect(vTarget, skill_id)`
5. cast / aftercast flow

`IsReadyToCast(...)` has already had a first optimization pass:

- cheap target-independent rejects moved earlier
- repeated local references cached
- expensive target resolution kept later

The main heavy remaining caller is `AreCastConditionsMet(...)`.

## AreCastConditionsMet Analysis

Location:

- `HeroAI/combat.py`

Why it is heavy:

- it mixes many distinct condition families in one very long function
- it repeatedly queries the same player/target state through helpers
- it eagerly computes many target-state booleans even when the current skill does not need them
- it performs multiple same-frame scans for enemies, allies, spirits, minions, pets, and shared-memory effect lists

### Main Hotspots

1. Repeated expensive helper calls on the same target

- `self.HasEffect(vTarget, ...)` is called many times
- `Routines.Checks.Agents.GetHealth(vTarget)` is called multiple times
- `self.IsPartyMember(vTarget)` can repeat
- `GetEffectAndBuffIds(vTarget)` is fetched in more than one branch

2. Unique-property branch duplication

The `UniqueProperty` block contains many branches that repeatedly fetch:

- `Player.GetAgentID()`
- player health
- player energy
- nearest spirit
- nearest enemy
- pet info / pet id

Several of those values should be lazy locals so they are only computed once if needed.

3. Eager target-condition bundle

The function currently computes a broad set of booleans up front:

- conditioned
- bleeding
- blind
- burning
- cracked armor
- crippled
- dazed
- deep wound
- disease
- poison
- weakness

That work is wasted for skills that only care about a small subset.

4. `feature_count` is rebuilt every call

The enabled condition count is derived from static skill metadata every time. That count should ideally be precomputed once per skill profile and reused.

5. Range/count scans are still expensive

These branches trigger filtered array scans:

- `EnemiesInRange`
- `AlliesInRange`
- `SpiritsInRange`
- `MinionsInRange`
- `IsPartyWide`
- `RequiresSpiritInEarshot`

These are valid checks, but they should remain as late as possible and only run when the specific condition flag is active.

### Best Improvement Points

1. Add lazy locals for repeated state

Good candidates:

- `player_id`
- player health
- player energy
- target health
- `is_party_member`
- `buff_list`
- nearest spirit in earshot
- nearest spirit in spellcast
- nearest enemy in earshot
- pet id / pet info

2. Make target condition checks lazy

Only compute `is_blind`, `is_burning`, `is_dazed`, etc. if the current skill actually requires that condition.

3. Reuse one effect/buff snapshot per target

If a branch needs target effect IDs, fetch once and reuse inside:

- dervish enchantment checks
- chant checks
- specific enchantment/hex list checks where possible

4. Precompute static per-skill metadata

Good candidates:

- `feature_count`
- whether any condition requires target effect IDs
- whether any condition requires party-wide scans
- whether any condition requires pet data

5. Keep heavy scans late

The list/count scans should stay near the end, after cheap state checks have already failed whenever possible.

## Suggested Next Refactor Order

1. `HeroAI/combat.py::AreCastConditionsMet`

- add lazy locals
- stop eager condition bundle evaluation
- keep behavior unchanged

2. `HeroAI/combat.py::GetAppropiateTarget`

- continue collapsing repeated target acquisition into lazy locals
- audit branches that still call multiple targeting helpers per slot

3. Shared target/effect helper extraction

- if `AreCastConditionsMet(...)` keeps growing, pull local lazy getters into private helpers inside `CombatClass`

## Guardrails

When optimizing this area:

- preserve skill-specific behavior exactly unless explicitly requested otherwise
- avoid broad structural changes without validating branch behavior
- prefer moving heavy checks later over changing gameplay logic
- prefer single-pass scans and frame-local caching for repeated reads
- be careful with pets, spirits, and party-member shared-memory rules

## Useful Files

- `HeroAI/combat.py`
- `HeroAI/targeting.py`
- `HeroAI/utils.py`
- `Py4GWCoreLib/routines_src/Agents.py`
- `Py4GWCoreLib/routines_src/Checks.py`
- `Py4GWCoreLib/GlobalCache/SharedMemory.py`
- `Py4GWCoreLib/GlobalCache/EffectCache.py`
