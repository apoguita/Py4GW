# Build Authoring Handover

This document captures the build design method used in this session so other contributors can replicate it consistently.

## Core Philosophy

Builds should be thin, explicit controllers on top of [`Py4GWCoreLib/BuildMgr.py`](/Py4GWCoreLib/BuildMgr.py).

Use HeroAI custom-skill metadata as the source of truth for:
- target allegiance
- health and energy thresholds
- sacrifice thresholds
- broad behavior flags

Let the build script own the final tactical behavior when the skill description implies nuance that generic shared logic cannot express cleanly.

## Recommended Workflow

1. Read the build file and `BuildMgr` first.
2. Read the custom-skill entry for the next skill to add.
3. Read the in-game skill description.
4. Decide what belongs in shared infrastructure and what belongs in the build.
5. Add one skill at a time.
6. Keep the main build loop readable and in explicit priority order.
7. Compile-check after every change.

## Shared vs Local Logic

Put behavior in `BuildMgr` when it is generic and reusable:
- cast readiness checks
- adrenaline support
- generic ally target resolution from custom skill data
- restoring enemy target after ally casts
- target reset when combat breaks
- generic target selection modes

For ally-facing shared behavior, `BuildMgr` must use party-aware/shared-capable checks rather than raw local `Agent` state whenever the data may come from another party account:
- ally alive/dead state
- ally health
- ally hex / enchantment / condition state
- ally role checks such as caster / martial / melee / ranged
- ally weapon-spell state

Enemy-side behavior is different:
- enemy checks stay local
- do not convert enemy targeting or enemy state evaluation to shared-memory assumptions

Keep behavior in the build when it is skill-specific:
- conditional target preference based on that skill's effect
- special tactical timing
- skill-specific throttling
- custom fallback behavior that is too narrow to generalize

## Main Build Pattern

Each build should generally:
- declare required and optional skill IDs
- cache each `CustomSkill` object with `self.GetCustomSkill(...)`
- define small helper methods for nontrivial skills
- use a single ordered `_run_local_skill_logic()` body
- return immediately after a successful cast

The local loop should stay declarative:
- check `CanCast()` early
- evaluate skills in the desired order
- only retarget when a skill is actually ready
- restore the previous enemy target after ally casts

## Targeting Rules Established

### General

- Only change target when necessary for the skill currently being evaluated.
- If the skill has a conditional bonus, prefer targets that satisfy the bonus.
- If the base effect is still useful, fall back to the lowest valid target.
- Use clustered targeting only when adjacency actually matters for the skill.

### Ally Casts

- Ally-targeted casts should restore the previous enemy target after use.
- Do not break existing ally filtering behavior when improving selection.
- Preserve built-in filtering and only refine final target choice carefully.
- Shared ally checks must stay shared-capable all the way through the selector stack, not only in the final cast helper.

### Enemy Casts

- Prefer dynamic target selection only when the skill can actually be cast.
- Avoid target jitter from pre-emptive retargeting.
- If a local build action succeeds for the tick, fallback should not run afterward in the same phase and retarget again.

### Melee Enemy Selection

- Melee targeting should be stickier than caster targeting.
- Once melee has a live target, prefer keeping it rather than refreshing to a new "better" target mid-approach.
- When melee must pick a new target, value target stability and connectability, not only tactical desirability.
- A slightly less ideal static target can be better than a closer or more tactical target that causes repeated chase behavior.
- Caster targeting can remain more tactical because reach is less punishing.

## Important Infrastructure Decisions

### Adrenaline

Adrenaline checks must use live skillbar slot state, not static skill metadata.

That means runtime readiness should come from the equipped slot's current adrenaline value, not from skill definition fields.

### Fallbacks

`AutoCombat` and `HeroAI` are different automators.

If a build needs true HeroAI fallback behavior, use the HeroAI build fallback directly rather than routing through `AutoCombat`.

### Combat Reset

Builds that cache target state must reset target tracking when aggro breaks, otherwise they may keep referencing a previous pack.

## Skill Authoring Method

For each skill:

1. Read the exact in-game description.
2. Read the HeroAI custom-skill entry.
3. Extract the hard requirements:
   - combat or OOC
   - health threshold
   - energy threshold
   - sacrifice threshold
   - spirit requirement
   - target allegiance
4. Extract the tactical preference:
   - clustered target
   - attacking target
   - hexed target
   - conditioned ally
   - weapon-spelled ally
5. Decide:
   - generic shared helper
   - or build-local resolver
6. Add a dedicated helper if the logic is not trivial.

## Design Patterns Used

### Buff Upkeep

Use for skills that should be maintained broadly:
- keep them high in the local loop
- allow them in or out of combat if the skill supports that

### Combat Windows

Use for skills that enable a short payoff period:
- cast only once combat is detected
- require prerequisite buffs to already be active

### Utility Heals and Cleanses

Use build-local resolvers when the skill has preference logic such as:
- conditioned allies first
- weapon-spelled allies first
- self only if a spirit is present

### Self-Sustain Offense

For skills like conditional drain or sustain signets:
- check your own health and energy thresholds first
- then find a target that satisfies the enemy-side condition

## Examples From This Session

### Seven Weapon Stance Axe

Method:
- replace copied dagger logic skill by skill
- maintain the stance first
- add defensive skill logic from custom thresholds
- use clustered enemy targeting for the AoE attack plan
- rely on shared adrenaline support from `BuildMgr`

### Keystone Signet

Method:
- separate permanent upkeep from combat-only window buffs
- keep `Symbolic Celerity` as always-on upkeep
- cast `Keystone Signet` only after combat starts and the prerequisite buff is active
- make each offensive signet resolve the best target for its own condition

### Bip Resto

Method:
- make each support skill a small explicit resolver
- respect custom thresholds
- add extra build-local requirements where the skill description demands them
- restore enemy target after ally casts
- document helper intent with brief comments

## Common Pitfalls

- confusing equipped-skill state with custom-skill metadata
- solving a generic problem inside one build instead of fixing the base layer
- retargeting before the skill is actually castable
- using target helpers that are too broad for the skill
- reordering skill flow without explicit approval
- breaking existing ally filtering when trying to improve ally ordering
- fixing only the final skill method while leaving the upstream selector layer on local-only ally checks
- letting fallback logic run after a successful local tick and retarget the same frame

## Style Guidelines

- Prefer hard-typed fields like `self.skill_name: CustomSkill`.
- Keep helper names specific to the skill behavior.
- Add short intent comments above nontrivial helpers.
- Keep the main cast loop easy to scan.
- Avoid over-abstracting when the build becomes harder to follow.

## Verification

After each code change:
- run `python -m py_compile` on changed Python files
- confirm the change is behavioral, not accidental refactoring
- preserve user-defined ordering unless explicitly told otherwise
