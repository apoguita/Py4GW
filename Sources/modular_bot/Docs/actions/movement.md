# Movement Actions

Movement and map-transition actions. These actions mostly enqueue movement/travel/wait states and can pause for party-loot conditions when configured.

Common runtime keys (all actions):
- `name` (default: auto-generated label)
- `ms` (default: `250`) post-step wait; for `wait`, this is the action duration
- `repeat` (default: `1`) expands registration count in `register_repeated_steps`
- `anchor` (default: `false`) sets runtime anchor after this step

<a id="action-auto_path"></a>
## `auto_path`
- Action type: `auto_path`
- Aliases: `none`
- Purpose: Autopath through ordered waypoints with enforced reach verification and retry behavior.
- Required fields: `points`
- Optional fields/defaults:
- `arrival_tolerance` (default observed: `ctx.step.get('tolerance', default_tolerance)`)
- `max_retries` (default observed: `0`)
- `name` (default observed: `f'AutoPath {ctx.step_idx + 1}'`)
- `pause_on_combat` (default observed: `False`)
- `retry_delay_ms` (default observed: `350`)
- `tolerance` (default observed: `default_tolerance`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "auto_path", "name": "AutoPath 1", "points": [[0, 0], [100, 100]]}
```

<a id="action-auto_path_delayed"></a>
## `auto_path_delayed`
- Action type: `auto_path_delayed`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `points`
- Optional fields/defaults:
- `delay_ms` (default observed: `35000`)
- `name` (default observed: `f'AutoPathDelayed {ctx.step_idx + 1}'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "auto_path_delayed", "name": "Delay Path", "points": [[0, 0], [100, 100]], "delay_ms": 35000}
```

<a id="action-auto_path_till_timeout"></a>
## `auto_path_till_timeout`
- Action type: `auto_path_till_timeout`
- Aliases: `auto_path_until_timeout`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `points`
- Optional fields/defaults:
- `lap_wait_ms` (default observed: `0`)
- `name` (default observed: `f'AutoPathTillTimeout {ctx.step_idx + 1}'`)
- `point_wait_ms` (default observed: `0`)
- `timeout_ms` (default observed: `0`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If `timeout_ms <= 0`, step logs and skips itself.
- Runnable example:
```json
{"type": "auto_path_till_timeout", "name": "Patrol Time", "points": [[0, 0], [100, 100]], "timeout_ms": 30000}
```

<a id="action-auto_path_until_enemy"></a>
## `auto_path_until_enemy`
- Action type: `auto_path_until_enemy`
- Aliases: `patrol_until_enemy`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `points`
- Optional fields/defaults:
- `include_dead` (default observed: `False`)
- `lap_wait_ms` (default observed: `0`)
- `max_dist` (default observed: `Range.Compass.value`)
- `max_laps` (default observed: `0`)
- `name` (default observed: `f'AutoPathUntilEnemy {ctx.step_idx + 1}'`)
- `point_wait_ms` (default observed: `0`)
- `set_target` (default observed: `False`)
- `timeout_ms` (default observed: `0`)
- Selector support: `enemy` selector family via `resolve_enemy_agent_id_from_step` (`agent_id`/`id`, `enemy`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "auto_path_until_enemy", "name": "Patrol", "points": [[0, 0], [100, 100]], "max_dist": 5000}
```

<a id="action-auto_path_until_timeout"></a>
## `auto_path_until_timeout`
- Action type: `auto_path_until_timeout`
- Aliases: `auto_path_till_timeout`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `points`
- Optional fields/defaults:
- `lap_wait_ms` (default observed: `0`)
- `name` (default observed: `f'AutoPathTillTimeout {ctx.step_idx + 1}'`)
- `point_wait_ms` (default observed: `0`)
- `timeout_ms` (default observed: `0`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If `timeout_ms <= 0`, step logs and skips itself.
- Runnable example:
```json
{"type": "auto_path_until_timeout", "name": "Patrol Timeout", "points": [[0, 0], [100, 100]], "timeout_ms": 30000}
```

<a id="action-enter_challenge"></a>
## `enter_challenge`
- Action type: `enter_challenge`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `delay` (default observed: `2000`)
- `delay_ms` (default observed: `ctx.step.get('delay', 2000)`)
- `name` (default observed: `'Enter Challenge'`)
- `target_map_id` (default observed: `0`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "enter_challenge", "delay_ms": 3000, "target_map_id": 0}
```

<a id="action-exit_map"></a>
## `exit_map`
- Action type: `exit_map`
- Aliases: `none`
- Purpose: Move to portal coordinates and wait for target map load when `target_map_id` is provided.
- Required fields: `point`
- Optional fields/defaults:
- `name` (default observed: `'Exit Map'`)
- `target_map_id` (default observed: `0`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Temporarily disables auto combat/looting while map-exit move executes, then restores prior state.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "exit_map", "point": [0, 0], "target_map_id": 0}
```

<a id="action-follow_model"></a>
## `follow_model`
- Action type: `follow_model`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `model_id`
- Optional fields/defaults:
- `follow_range` (default observed: `ctx.step.get('range', 600)`)
- `range` (default observed: `600`)
- `timeout_ms` (default observed: `0`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "follow_model", "model_id": 1613, "follow_range": 600}
```

<a id="action-leave_party"></a>
## `leave_party`
- Action type: `leave_party`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `multibox` (default observed: `False`)
- `name` (default observed: `f'Leave Party {ctx.step_idx + 1}'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "leave_party", "ms": 2000}
```

<a id="action-move"></a>
## `move`
- Action type: `move`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `point`
- Optional fields/defaults:
- `name` (default observed: `''`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "move", "name": "Move", "point": [0, 0]}
```

<a id="action-nudge"></a>
## `nudge`
- Action type: `nudge`
- Aliases: `nudge_move`
- Purpose: Alias of `nudge_move`; pulse movement command toward `(x, y)` for micro-adjustment/unstuck.
- Required fields: `point`
- Optional fields/defaults:
- `move_ms` (default observed: `250`)
- `name` (default observed: `f'Nudge {ctx.step_idx + 1}'`)
- `pulse_ms` (default observed: `ctx.step.get('move_ms', 250)`)
- `pulses` (default observed: `1`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: Same runtime behavior as `nudge_move`.
- Runnable example:
```json
{"type": "nudge", "name": "Nudge Forward", "point": [0, 0], "pulses": 2, "pulse_ms": 250}
```

<a id="action-nudge_move"></a>
## `nudge_move`
- Action type: `nudge_move`
- Aliases: `nudge`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `point`
- Optional fields/defaults:
- `move_ms` (default observed: `250`)
- `name` (default observed: `f'Nudge {ctx.step_idx + 1}'`)
- `pulse_ms` (default observed: `ctx.step.get('move_ms', 250)`)
- `pulses` (default observed: `1`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "nudge_move", "name": "Nudge Forward", "point": [0, 0], "pulses": 2, "pulse_ms": 250}
```

<a id="action-path"></a>
## `path`
- Action type: `path`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `points`
- Optional fields/defaults:
- `name` (default observed: `f'Path {ctx.step_idx + 1}'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "path", "name": "Path 1", "points": [[0, 0], [100, 100]]}
```

<a id="action-path_to_target"></a>
## `path_to_target`
- Action type: `path_to_target`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `max_dist` (default observed: `Range.Compass.value`)
- `name` (default observed: `'Path To Target'`)
- `required` (default observed: `True`)
- `tolerance` (default observed: `150.0`)
- Selector support: `enemy` selector family via `resolve_enemy_agent_id_from_step` (`agent_id`/`id`, `enemy`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If target cannot be resolved and `required=true`, the step logs and returns; with `required=false`, it safely continues.
- Runnable example:
```json
{"type": "path_to_target", "target": "Shadow Ranger"}
```

<a id="action-patrol_until_enemy"></a>
## `patrol_until_enemy`
- Action type: `patrol_until_enemy`
- Aliases: `auto_path_until_enemy`
- Purpose: Alias of `auto_path_until_enemy`; patrol until enemy detection criteria match.
- Required fields: `points`
- Optional fields/defaults:
- `include_dead` (default observed: `False`)
- `lap_wait_ms` (default observed: `0`)
- `max_dist` (default observed: `Range.Compass.value`)
- `max_laps` (default observed: `0`)
- `name` (default observed: `f'AutoPathUntilEnemy {ctx.step_idx + 1}'`)
- `point_wait_ms` (default observed: `0`)
- `set_target` (default observed: `False`)
- `timeout_ms` (default observed: `0`)
- Selector support: `enemy` selector family via `resolve_enemy_agent_id_from_step` (`agent_id`/`id`, `enemy`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: Same runtime behavior as `auto_path_until_enemy`.
- Runnable example:
```json
{"type": "patrol_until_enemy", "name": "Patrol", "points": [[0, 0], [100, 100]], "max_dist": 5000}
```

<a id="action-random_travel"></a>
## `random_travel`
- Action type: `random_travel`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `allowed_districts` (default observed: `None`)
- `districts` (default observed: `ctx.step.get('allowed_districts')`)
- `leave_party` (default observed: `True`)
- `name` (default observed: `f'Random Travel {ctx.step_idx + 1}'`)
- `target_map_id` (default observed: `0`)
- `target_map_name` (default observed: `''`)
- `travel_wait_ms` (default observed: `500`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "random_travel", "name": "Random District Travel", "target_map_id": 642, "districts": ["EuropeItalian", "EuropeSpanish"]}
```

<a id="action-travel"></a>
## `travel`
- Action type: `travel`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `leave_party` (default observed: `True`)
- `target_map_id` (default observed: `0`)
- `target_map_name` (default observed: `''`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "travel", "target_map_id": 284}
```

<a id="action-travel_gh"></a>
## `travel_gh`
- Action type: `travel_gh`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `multibox` (default observed: `False`)
- `name` (default observed: `f'Travel GH {ctx.step_idx + 1}'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "travel_gh", "ms": 4000}
```

<a id="action-wait"></a>
## `wait`
- Action type: `wait`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "wait", "ms": 1000}
```

<a id="action-wait_for_map_load"></a>
## `wait_for_map_load`
- Action type: `wait_for_map_load`
- Aliases: `wait_map_load`
- Purpose: Alias of `wait_map_load`; wait until target map is fully loaded.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `map_id` (default observed: `ctx.step.get('target_map_id', 0)`)
- `target_map_id` (default observed: `0`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: Same runtime behavior as `wait_map_load`.
- Runnable example:
```json
{"type": "wait_for_map_load", "map_id": 72}
```

<a id="action-wait_map_change"></a>
## `wait_map_change`
- Action type: `wait_map_change`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `target_map_id`
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "wait_map_change", "target_map_id": 0}
```

<a id="action-wait_map_load"></a>
## `wait_map_load`
- Action type: `wait_map_load`
- Aliases: `wait_for_map_load`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `map_id` (default observed: `ctx.step.get('target_map_id', 0)`)
- `target_map_id` (default observed: `0`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "wait_map_load", "map_id": 72}
```

<a id="action-wait_out_of_combat"></a>
## `wait_out_of_combat`
- Action type: `wait_out_of_combat`
- Aliases: `none`
- Purpose: Execute a movement/map-control step in the FSM pipeline.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Adds movement/travel/wait states to FSM; may alter map, target, or party flow.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "wait_out_of_combat"}
```



