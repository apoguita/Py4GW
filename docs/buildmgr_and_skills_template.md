# BuildMgr And SkillsTemplate

This document describes the current contract between `BuildMgr` and the shared skill scaffold under `Py4GWCoreLib/Builds/Skills`.

## Purpose

`BuildMgr` owns build behavior and shared casting helpers.

`SkillsTemplate` owns the reusable skill namespace layout:

- profession groups
- attribute groups
- per-attribute skill classes

The intended call style from a build is:

```python
self.skills: SkillsTemplate = SkillsTemplate(self)

if (yield from self.skills.Monk.HealingPrayers.Healing_Burst()):
    return
```

## Ownership Rules

### BuildMgr owns

- build identity and match metadata
- required and optional skills
- fallback selection and fallback handlers
- custom skill retrieval through `GetCustomSkill`
- target resolution helpers such as `ResolveAllyTarget`
- cast validation such as `CanCastSkillID`
- shared cast execution such as `CastSkillID`
- shared targeted cast flow through `CastSkillIDAndRestoreTarget`

If a behavior is broadly reusable across builds, it belongs in `BuildMgr`.

For ally-aware shared behavior, `BuildMgr` also owns the data-source rule:
- ally and party-member evaluation must use shared-capable checks when available
- enemy evaluation remains local-only

This applies to:
- ally target resolution
- ally role checks
- ally health/state checks
- party-wide threshold evaluation
- party spike / health-delta monitoring

### SkillsTemplate owns

- the root scaffold for reusable skill modules
- profession containers like `Monk`, `Necromancer`, `Ritualist`
- attribute containers like `HealingPrayers`, `Communing`, `Curses`

`SkillsTemplate` is not meant to replace `BuildMgr`. It is only the structured access point for reusable skill implementations.

### Attribute skill classes own

- the actual skill method
- any skill-local target resolver
- any skill-local thresholds or preference rules
- exact casting behavior for that skill

Example:

- `Monk/HealingPrayers.py` owns `Healing_Burst()`
- the build just calls it

If a skill needs very special behavior that should not affect the rest of the system, keep that logic inside the skill method or inside the build that uses it.

## Current Package Shape

Root file:

- `Py4GWCoreLib/Builds/Skills/SkillsTemplate.py`

Profession packages:

- `any`
- `warrior`
- `ranger`
- `Monk`
- `necromancer`
- `mesmer`
- `elementalist`
- `assassin`
- `ritualist`
- `paragon`
- `dervish`

Each profession package contains:

- one module per enum-defined attribute
- `NoAttribute.py`
- a package `__init__.py` that instantiates all attribute classes

Example:

```python
self.skills.Monk.HealingPrayers
self.skills.Ritualist.Communing
self.skills.Necromancer.Curses
```

## NoAttribute

Every profession has a `NoAttribute` class.

This is the bucket for:

- profession skills with no attribute line
- profession-specific helper skills that should still live under that profession

There is also `self.skills.Any.NoAttribute` for shared non-profession-specific skills.

## Authoring Pattern

### 1. Put reusable skills in the matching profession and attribute file

Examples:

- Monk healing skill: `Py4GWCoreLib/Builds/Skills/Monk/HealingPrayers.py`
- Ritualist communing skill: `Py4GWCoreLib/Builds/Skills/ritualist/Communing.py`
- Necromancer curse skill: `Py4GWCoreLib/Builds/Skills/necromancer/Curses.py`

### 2. Keep the build lean

The build should mainly:

- define the build metadata
- instantiate `SkillsTemplate(self)`
- call skill methods in priority order

### 3. Use BuildMgr helpers from inside the skill class

Preferred helpers:

- `self.build.GetCustomSkill(...)`
- `self.build.ResolveAllyTarget(...)`
- `self.build.IsSkillEquipped(...)`
- `self.build.CanCastSkillID(...)`
- `self.build.CastSkillIDAndRestoreTarget(...)`

When a skill is ally-targeted, prefer `BuildMgr` helpers over ad hoc direct selector calls so the shared-capable ally checks are preserved end to end.

### 4. Keep skill methods self-contained

Preferred style:

- local `skill_id`
- local `CustomSkill`
- local nested resolver when needed
- local thresholds when needed

Example shape:

```python
def Vigorous_Spirit(self) -> BuildCoroutine:
    vigorous_spirit_id: int = Skill.GetID("Vigorous_Spirit")
    vigorous_spirit: CustomSkill = cast(CustomSkill, self.build.GetCustomSkill(vigorous_spirit_id))

    def _resolve_vigorous_spirit_target() -> int:
        return self.build.ResolveAllyTarget(
            vigorous_spirit_id,
            vigorous_spirit,
        )

    if not self.build.IsSkillEquipped(vigorous_spirit_id):
        return False
    if not Routines.Checks.Agents.InAggro():
        return False

    target_agent_id = _resolve_vigorous_spirit_target()
    return (yield from self.build.CastSkillIDAndRestoreTarget(
        vigorous_spirit_id,
        target_agent_id,
    ))
```

## Typing Guidance

For skill modules, prefer strong typing on:

- `self.build`
- skill method return values
- local `skill_id`
- local `CustomSkill` handles
- local resolver return values

This keeps IntelliSense useful without forcing extra registration steps.

## Data-Source Constraints

These constraints are now part of the `BuildMgr` contract:

- Ally-facing shared methods must be party-aware.
- Enemy-facing shared methods must remain local.
- Base `Agent` is not the place to add shared-memory-specific party logic.
- Shared-memory-capable logic belongs in higher layers such as `Checks`, `Targeting`, and `BuildMgr`.

If a skill or selector bypasses `BuildMgr` and talks directly to local-only `Agent` role/state checks for allies, that is a contract violation unless the target is explicitly local-only.

## Fallback Contract

Fallback is a second-stage execution path, not a co-owner of the same tick.

- Run local build logic first.
- If the local logic succeeded for the tick, do not run fallback afterward in the same phase.
- Only use fallback when the local build did not produce a successful action for that tick.

This is especially important for melee builds, where fallback retargeting in the same tick can create left-right ping-pong behavior.

## Melee Targeting Contract

`BuildMgr` melee enemy targeting is intentionally different from caster targeting:

- keep the current live melee target when possible
- avoid swapping targets mid-approach just because a new tactical preference appeared
- when selecting a new target, include target stability/connectability, not just tactical value
- a reachable static target can be preferable to a more tactical moving target

Caster targeting can remain more tactical because the cost of retargeting is lower.

## When To Keep Logic In The Build

Keep logic in the build only when the behavior is build-specific rather than skill-specific.

Examples:

- unusual priority ordering between otherwise reusable skills
- bar-specific sequencing rules
- special interactions that should not become the default implementation of a shared skill

If the behavior is the normal intended behavior of the skill, it belongs in the attribute skill class.

## Relationship To Matching

`BuildRegistry` and build matching are separate from this skill scaffold.

The registry should only identify and return the correct build.

Once a build is active, `BuildMgr` plus `SkillsTemplate` handle execution.

## Practical Example

`Healing Burst` currently demonstrates the pattern:

- build file: `Py4GWCoreLib/Builds/Monk/Mo_Any/Healing Burst.py`
- shared skill file: `Py4GWCoreLib/Builds/Skills/Monk/HealingPrayers.py`

The build calls:

```python
self.skills.Monk.HealingPrayers.Healing_Burst()
self.skills.Monk.HealingPrayers.Dwaynas_Kiss()
self.skills.Monk.HealingPrayers.Seed_of_Life()
self.skills.Monk.HealingPrayers.Draw_Conditions()
self.skills.Monk.HealingPrayers.Vigorous_Spirit()
```

That is the reference pattern for new shared skill modules.
