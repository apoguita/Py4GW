# Build Prompting Guide

This document captures the prompting style used in this session so other people can request build work in a way that produces reliable results.

## Prompting Philosophy

The most effective prompts for build authoring are:
- incremental
- behavior-first
- grounded in actual skill descriptions
- explicit about combat state, targeting, and priorities
- clear about whether logic belongs in shared code or the build itself

Avoid asking for a whole build in one vague step when the bar contains many nuanced skills.

## Best Prompt Structure

Use this structure whenever possible:

1. Name the build and file.
2. Name the next skill or system to add.
3. Provide the full in-game skill description.
4. Provide the custom-skill config if one exists.
5. Explain the intended gameplay behavior in plain terms.
6. Explain whether the logic should be generic or local.
7. State any ordering or placement constraints.

## Recommended Prompt Template

```text
We are working on [build file].

Add [skill name].

Skill description:
[full skill description]

Custom skill entry:
[relevant CustomSkill fields]

Desired behavior:
- [when it should cast]
- [who it should target]
- [what it should prefer]
- [what it should fall back to]
- [combat or OOC rule]
- [safety or throttle rule]

If this behavior is generic, put it in shared code.
If it is skill-specific, keep it in the build.
Do not reorder the existing skill flow unless I ask.
```

## Prompt Types That Worked Well

### 1. Analysis Prompts

Use these first when starting a build or shared refactor.

Examples:
- analyze the build and `BuildMgr`
- analyze the current targeting helper
- compare build fallback with HeroAI fallback

These prompts work because they establish the real current behavior before changes are made.

### 2. Skill-by-Skill Prompts

Use these to add one skill at a time.

Examples:
- add `Executioner's Strike`
- add `Smite Hex`
- add `Spirit Transfer`

These prompts work best when they include the skill description and expected tactical use.

### 3. Tactical Correction Prompts

Use these when the code technically works but chooses the wrong targets or uses the wrong abstraction.

Examples:
- this should prefer lowest enemy unless the bonus condition matters
- only retarget when necessary
- the cluster does not need the condition, only the desired target

These prompts are critical because many build bugs are logic-quality bugs, not syntax bugs.

### 4. Infrastructure Prompts

Use these when a problem affects more than one build.

Examples:
- add adrenaline support to cast functions
- make `BuildMgr` strongly typed
- add helpers for equipped optional skills

These prompts are useful when a build bug reveals a missing shared capability.

### 5. Architecture Prompts

Use these when the wrong subsystem is being used.

Examples:
- use HeroAI as fallback, not AutoCombat
- fix this from the base, not with a skill-specific failsafe

These prompts stop temporary patches from becoming long-term design debt.

## Guidance on What to Include

The most useful details to include are:
- whether the skill is required or optional
- whether it is combat-only or OOC
- whether it is upkeep, burst, utility, heal, cleanse, or offense
- what condition makes it higher value
- what fallback target should be used if the preferred condition is missing
- any safety constraints like sacrifice health or spam throttling
- whether ally-side logic must use shared party data
- whether the target-selection issue is melee-specific or general

## Strong Prompt Patterns From This Session

These patterns produced good results:

- “This skill is optional, use the custom skill values, and only cast if equipped.”
- “This is a heal, but it should prefer conditioned allies when spirits are nearby.”
- “This is a damage skill, but clustered targeting only matters if the conditional splash is active.”
- “This belongs in the base layer, not as a per-skill workaround.”
- “Leave the order where I set it.”
- “Make the code more declarative.”

## Correction Patterns That Helped

When an implementation drifts, direct corrections are useful.

Examples:
- “that helper is wrong”
- “you’re checking the current player target, but you need to scan the agent array”
- “you changed the wrong automator”
- “this is too abstract”
- “your solution is not aware of future skills”

These are good prompts because they describe the exact design mistake rather than only saying the result is bad.

## Shared vs Local Prompting

When asking for a change, say which category it belongs to:

- Shared:
  - BuildMgr
  - target helpers
  - cast helpers
  - fallback plumbing
  - shared-capable ally checks

- Local:
  - one build's target preference
  - one skill's resolver
  - one build's skill order

If you are unsure, you can phrase it like this:

```text
If this is generic, put it in BuildMgr.
If it is specific to this skill, keep it in the build.
```

## How to Prevent Regressions Through Prompting

Include constraints explicitly:
- do not reorder existing logic
- preserve current filters
- restore enemy target after ally casts
- only change target if the skill is ready
- keep the helper intent obvious
- ally-facing shared methods must use shared-capable party data
- enemy checks stay local
- if local logic succeeds, fallback must not run afterward in the same phase
- melee target changes should be sticky and stability-aware, not only distance- or tactic-driven

These instructions are especially important in a codebase with layered automation like this one.

## Anti-Patterns to Avoid

Avoid prompts like:
- “make the build smarter”
- “just add all the skills”
- “fix the targeting”

Those are too vague and force the implementer to guess intent.

Also avoid omitting:
- the skill description
- combat vs OOC expectations
- fallback target behavior
- whether the logic should be shared or local

## Practical Prompting Sequence

For a new build or large build update, this sequence worked well:

1. Ask for analysis of the build and shared manager.
2. Add shared missing infrastructure if needed.
3. Add the first core skill.
4. Add each next skill one by one.
5. Correct target logic when the first implementation is too broad.
6. Refine architecture if fallback or shared systems are wrong.
7. Add comments and typing once the behavior is stable.

## One-Line Prompt Formula

If you want a compact prompt that still works well, use:

```text
Add [skill] to [build]. Description: [text]. Custom skill: [fields]. Intended behavior: [rules]. Keep shared logic generic and local logic skill-specific. Do not reorder the existing flow.
```

## Useful Constraint Phrases

These additional phrases are especially useful in this codebase:

- "For allies, use shared-capable party checks, not raw local Agent checks."
- "Do not change enemy checks to shared-memory logic."
- "Do not bypass BuildMgr for ally target resolution."
- "If this affects melee targeting, keep the current target sticky and avoid mid-approach ping-pong."
- "Do not let fallback retarget after a successful local tick."
