# Interaction Actions

NPC/gadget/item/dialog/input actions. Selector resolution is centralized in `step_selectors.py`, and dialog-class actions use temporary combat/looting guards.

Common runtime keys (all actions):
- `name` (default: auto-generated label)
- `ms` (default: `250`) post-step wait; for `wait`, this is the action duration
- `repeat` (default: `1`) expands registration count in `register_repeated_steps`
- `anchor` (default: `false`) sets runtime anchor after this step

<a id="action-dialog"></a>
## `dialog`
- Action type: `dialog`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `id`
- Optional fields/defaults:
- `name` (default observed: `''`)
- Selector support: `npc` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `npc`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: Temporarily disables auto combat/looting while dialog executes, then restores prior state.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "dialog", "name": "Dialog", "point": [0, 0], "id": 0}
```

<a id="action-dialog_multibox"></a>
## `dialog_multibox`
- Action type: `dialog_multibox`
- Aliases: `none`
- Purpose: Send one or more dialog IDs locally and mirror them to other accounts via shared commands.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `id` (default observed: `[]`)
- `interval_ms` (default observed: `200`)
- `multibox_timeout_ms` (default observed: `5000`)
- `multibox_wait_step_ms` (default observed: `50`)
- `name` (default observed: `f'Dialog Multibox {ctx.step_idx + 1}'`)
- Selector support: `npc` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `npc`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: Temporarily disables auto combat/looting while dialog chain executes, then restores prior state.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "dialog_multibox", "id": 0}
```

<a id="action-dialog_with_model"></a>
## `dialog_with_model`
- Action type: `dialog_with_model`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `id`, `model_id`
- Optional fields/defaults:
- `name` (default observed: `''`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "dialog_with_model", "model_id": 1613, "id": "0x84"}
```

<a id="action-dialogs"></a>
## `dialogs`
- Action type: `dialogs`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `id` (default observed: `[]`)
- `interval_ms` (default observed: `200`)
- `name` (default observed: `f'Dialogs {ctx.step_idx + 1}'`)
- Selector support: `npc` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `npc`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: Temporarily disables auto combat/looting while dialog chain executes, then restores prior state.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "dialogs", "name": "Dialogs", "point": [0, 0], "id": ["0x2", "0x15", "0x3"]}
```

<a id="action-emote"></a>
## `emote`
- Action type: `emote`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `command` (default observed: `ctx.step.get('emote', ctx.step.get('value', 'kneel'))`)
- `emote` (default observed: `ctx.step.get('value', 'kneel')`)
- `name` (default observed: `f'Emote /{command}'`)
- `value` (default observed: `'kneel'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "emote", "command": "kneel"}
```

<a id="action-interact_gadget"></a>
## `interact_gadget`
- Action type: `interact_gadget`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `'Interact Gadget'`)
- Selector support: `gadget` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `gadget`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "interact_gadget"}
```

<a id="action-interact_gadget_at_xy"></a>
## `interact_gadget_at_xy`
- Action type: `interact_gadget_at_xy`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `'Interact Gadget'`)
- Selector support: `gadget` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `gadget`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "interact_gadget_at_xy", "point": [0, 0]}
```

<a id="action-interact_item"></a>
## `interact_item`
- Action type: `interact_item`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `max_dist` (default observed: `Range.Compass.value`)
- `name` (default observed: `'Interact Item'`)
- Selector support: model-id resolution via `resolve_item_model_id_from_step` (symbolic/numeric `model_id`, legacy `item` alias).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "interact_item"}
```

<a id="action-interact_nearest_npc"></a>
## `interact_nearest_npc`
- Action type: `interact_nearest_npc`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `'Interact Nearest NPC'`)
- Selector support: `npc` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `npc`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "interact_nearest_npc"}
```

<a id="action-interact_npc"></a>
## `interact_npc`
- Action type: `interact_npc`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `''`)
- Selector support: `npc` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `npc`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "interact_npc", "name": "Talk NPC", "point": [0, 0]}
```

<a id="action-interact_quest_npc"></a>
## `interact_quest_npc`
- Action type: `interact_quest_npc`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "interact_quest_npc"}
```

<a id="action-key_press"></a>
## `key_press`
- Action type: `key_press`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `key`
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "key_press", "key": "F1"}
```

<a id="action-loot_chest"></a>
## `loot_chest`
- Action type: `loot_chest`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `max_dist` (default observed: `Range.Compass.value`)
- `multibox` (default observed: `False`)
- `name` (default observed: `'Loot Chest'`)
- Selector support: `gadget` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `gadget`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "loot_chest", "point": [0, 0]}
```

<a id="action-skip_cinematic"></a>
## `skip_cinematic`
- Action type: `skip_cinematic`
- Aliases: `skip_cutscene`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `wait_ms` (default observed: `500`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "skip_cinematic", "wait_ms": 500}
```

<a id="action-skip_cutscene"></a>
## `skip_cutscene`
- Action type: `skip_cutscene`
- Aliases: `skip_cinematic`
- Purpose: Alias of `skip_cinematic`; skip cinematic after optional pre-wait.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `wait_ms` (default observed: `500`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: Same runtime behavior as `skip_cinematic`.
- Runnable example:
```json
{"type": "skip_cutscene", "wait_ms": 500}
```

<a id="action-use_item"></a>
## `use_item`
- Action type: `use_item`
- Aliases: `none`
- Purpose: Execute an interaction/dialog/input step against in-game entities or UI.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: model-id resolution via `resolve_item_model_id_from_step` (symbolic/numeric `model_id`, legacy `item` alias).
- Side effects: May move player, interact with targets, send dialog/input commands, and/or emit multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "use_item", "model_id": 22280}
```



