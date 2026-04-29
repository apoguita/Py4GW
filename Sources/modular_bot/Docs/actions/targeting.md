# Targeting Actions

Target acquisition, diagnostics, and blacklist utilities for route debugging and control.

Common runtime keys (all actions):
- `name` (default: auto-generated label)
- `ms` (default: `250`) post-step wait; for `wait`, this is the action duration
- `repeat` (default: `1`) expands registration count in `register_repeated_steps`
- `anchor` (default: `false`) sets runtime anchor after this step

<a id="action-add_enemy_blacklist"></a>
## `add_enemy_blacklist`
- Action type: `add_enemy_blacklist`
- Aliases: `none`
- Purpose: Execute target resolution or targeting utility behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `enemy_name` (default observed: `''`)
- `name` (default observed: `f'Add Enemy Blacklist: {enemy_name}'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May update player target, blacklist entries, or emit diagnostic logs.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "add_enemy_blacklist", "enemy_name": "Infernal Wurm"}
```

<a id="action-debug_nearby_agents"></a>
## `debug_nearby_agents`
- Action type: `debug_nearby_agents`
- Aliases: `none`
- Purpose: Execute target resolution or targeting utility behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `include_dead` (default observed: `True`)
- `limit` (default observed: `25`)
- `max_dist` (default observed: `5000.0`)
- `name` (default observed: `'Debug Nearby Agents'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May update player target, blacklist entries, or emit diagnostic logs.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "debug_nearby_agents"}
```

<a id="action-debug_nearby_enemies"></a>
## `debug_nearby_enemies`
- Action type: `debug_nearby_enemies`
- Aliases: `none`
- Purpose: Execute target resolution or targeting utility behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `include_dead` (default observed: `False`)
- `limit` (default observed: `25`)
- `max_dist` (default observed: `5000.0`)
- `name` (default observed: `'Debug Nearby Enemies'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May update player target, blacklist entries, or emit diagnostic logs.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "debug_nearby_enemies"}
```

<a id="action-remove_enemy_blacklist"></a>
## `remove_enemy_blacklist`
- Action type: `remove_enemy_blacklist`
- Aliases: `none`
- Purpose: Execute target resolution or targeting utility behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `enemy_name` (default observed: `''`)
- `name` (default observed: `f'Remove Enemy Blacklist: {enemy_name}'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May update player target, blacklist entries, or emit diagnostic logs.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "remove_enemy_blacklist", "enemy_name": "Infernal Wurm"}
```

<a id="action-target_enemy"></a>
## `target_enemy`
- Action type: `target_enemy`
- Aliases: `none`
- Purpose: Execute target resolution or targeting utility behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `'Target Enemy'`)
- `set_party_target` (default observed: `False`)
- Selector support: `enemy` selector family via `resolve_enemy_agent_id_from_step` (`agent_id`/`id`, `enemy`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May update player target, blacklist entries, or emit diagnostic logs.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "target_enemy", "agent_id": 4567}
```

<a id="action-wait_model_has_quest"></a>
## `wait_model_has_quest`
- Action type: `wait_model_has_quest`
- Aliases: `none`
- Purpose: Execute target resolution or targeting utility behavior.
- Required fields: `model_id`
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May update player target, blacklist entries, or emit diagnostic logs.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "wait_model_has_quest", "model_id": 1562}
```
