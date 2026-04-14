# Selectors and Target Enums

This reference explains how action steps resolve NPC/enemy/gadget targets and item model IDs.

## Unified Selector Semantics

Common selector keys used by resolver helpers:
- Coordinates: `point` (`[x, y]`) with legacy fallback `x`/`y`
- Named registry key: `npc`, `enemy`, `gadget`
- Name filters: `target`, `name_contains` (plus `enemy_name` / `agent_name` aliases where applicable)
- Explicit model: `model_id`
- Nearest mode: `nearest` (bool)
- Radius: `max_dist` (defaults to `Range.Compass` in most selector actions)
- Name matching mode: `exact_name` (bool)

Enemy-specific direct targeting fields:
- `agent_id` / `id`

## Resolver Functions

- `resolve_agent_xy_from_step(...)`
  - Used for NPC and gadget coordinates.
  - Supports encoded-name matching through target enum entries.
- `resolve_enemy_agent_id_from_step(...)`
  - Used for enemy targeting/pathing.
  - Supports direct id, named enum, model, nearest, and name matching.
- `resolve_item_model_id_from_step(...)`
  - Resolves symbolic/numeric `model_id` (or legacy `item`) to concrete model IDs.

## Target Registry Wiring (`target_enums.py`)

`Sources/modular_bot/recipes/target_enums.py` provides:
- `NPC_TARGETS`
- `ENEMY_TARGETS`
- `GADGET_TARGETS`

These registries are consumed by:
- `get_named_agent_target(kind, key)`

Actions using selectors resolve registry keys at runtime via `step_selectors.py` and then filter nearby agent arrays.

## Authoring Guidance

- Prefer named selectors (`npc`/`enemy`/`gadget`) for stability across map coordinate variance.
- Use `point` when interaction location is deterministic and selector identity is unreliable (legacy `x/y` is still accepted).
- Set `max_dist` explicitly in crowded areas to reduce accidental nearest-target matches.
- Use `exact_name=true` only when strict name equality is required.

