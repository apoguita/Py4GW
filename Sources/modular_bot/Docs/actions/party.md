# Party Actions

Party control, engine toggles, consumables, anchor/recovery control, and multibox account coordination.

Common runtime keys (all actions):
- `name` (default: auto-generated label)
- `ms` (default: `250`) post-step wait; for `wait`, this is the action duration
- `repeat` (default: `1`) expands registration count in `register_repeated_steps`
- `anchor` (default: `false`) sets runtime anchor after this step

<a id="action-disable_party_member_hooks"></a>
## `disable_party_member_hooks`
- Action type: `disable_party_member_hooks`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "disable_party_member_hooks", "name": "Disable Party Member Hooks"}
```

<a id="action-drop_bundle"></a>
## `drop_bundle`
- Action type: `drop_bundle`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "drop_bundle"}
```

<a id="action-enable_party_member_hooks"></a>
## `enable_party_member_hooks`
- Action type: `enable_party_member_hooks`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "enable_party_member_hooks", "name": "Enable Party Member Hooks"}
```

<a id="action-flag_all_accounts"></a>
## `flag_all_accounts`
- Action type: `flag_all_accounts`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `point`
- Optional fields/defaults:
- `name` (default observed: `'Flag All Accounts'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "flag_all_accounts", "point": [0, 0]}
```

<a id="action-flag_heroes"></a>
## `flag_heroes`
- Action type: `flag_heroes`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `point`
- Optional fields/defaults:
- `name` (default observed: `'Flag Heroes'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "flag_heroes", "point": [0, 0]}
```

<a id="action-force_hero_state"></a>
## `force_hero_state`
- Action type: `force_hero_state`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `behavior`
- Optional fields/defaults:
- `name` (default observed: `f'Force Hero State ({raw_state or behavior})'`)
- `state` (default observed: `''`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "force_hero_state", "state": "fight"}
```

<a id="action-heroes_use_skill"></a>
## `heroes_use_skill`
- Action type: `heroes_use_skill`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `f'Heroes Use Skill {slot}'`)
- `slot` (default observed: `0`, `None`)
- `target_id` (default observed: `0`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "heroes_use_skill", "name": "Heroes Skill", "slot": 1, "target_id": 0}
```

<a id="action-invite_all_accounts"></a>
## `invite_all_accounts`
- Action type: `invite_all_accounts`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "invite_all_accounts"}
```

<a id="action-load_party"></a>
## `load_party`
- Action type: `load_party`
- Aliases: `none`
- Purpose: Load heroes/henchmen using team config or priority rules with optional template application.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `add_delay_ms` (default observed: `150`)
- `apply_templates` (default observed: `True`)
- `clear_existing` (default observed: `True`)
- `fill_with_henchmen` (default observed: `False`)
- `henchman_ids` (default observed: `ctx.step.get('henchmen', [])`)
- `henchmen` (default observed: `[]`)
- `hero_team` (default observed: `''`)
- `max_heroes` (default observed: `0`)
- `minionless` (default observed: `False`)
- `name` (default observed: `'Load Party'`)
- `required_hero` (default observed: `None`)
- `team` (default observed: `ctx.step.get('hero_team', '')`)
- `team_mode` (default observed: `ctx.step.get('team_selection', '')`)
- `team_selection` (default observed: `''`)
- `use_priority` (default observed: `True`)
- `wait_poll_ms` (default observed: `250`)
- `wait_timeout_ms` (default observed: `12000`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "load_party"}
```

<a id="action-resign"></a>
## `resign`
- Action type: `resign`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "resign"}
```

<a id="action-set_anchor"></a>
## `set_anchor`
- Action type: `set_anchor`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `''`)
- `phase` (default observed: `ctx.step.get('target', ctx.step.get('name', ''))`)
- `target` (default observed: `ctx.step.get('name', '')`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "set_anchor", "phase": "03. Mission: Thunderhead Keep"}
```

<a id="action-set_auto_combat"></a>
## `set_auto_combat`
- Action type: `set_auto_combat`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `enabled` (default observed: `True`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Toggles combat state across active backend and may adjust `pause_on_danger`, `hero_ai`, and template behavior.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "set_auto_combat", "enabled": true}
```

<a id="action-set_auto_looting"></a>
## `set_auto_looting`
- Action type: `set_auto_looting`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `enabled` (default observed: `True`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Toggles looting state across active backend and syncs `auto_loot` where applicable.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "set_auto_looting", "enabled": true}
```

<a id="action-set_hard_mode"></a>
## `set_hard_mode`
- Action type: `set_hard_mode`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `enabled` (default observed: `True`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "set_hard_mode", "enabled": true}
```

<a id="action-set_party_member_hooks"></a>
## `set_party_member_hooks`
- Action type: `set_party_member_hooks`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `enabled` (default observed: `True`)
- `name` (default observed: `f'{('Enable' if enabled else 'Disable')} Party Member Hooks'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "set_party_member_hooks", "name": "Set Party Member Hooks", "enabled": false}
```

<a id="action-set_title"></a>
## `set_title`
- Action type: `set_title`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `id`
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "set_title", "id": 0}
```

<a id="action-summon_all_accounts"></a>
## `summon_all_accounts`
- Action type: `summon_all_accounts`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- None beyond common runtime keys.
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "summon_all_accounts"}
```

<a id="action-suppress_recovery"></a>
## `suppress_recovery`
- Action type: `suppress_recovery`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `max_events` (default observed: `20`)
- `ms` (default observed: `45000`)
- `name` (default observed: `'Suppress Recovery'`)
- `until_outpost` (default observed: `False`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "suppress_recovery", "name": "Suppress Recovery", "ms": 45000, "max_events": 20}
```

<a id="action-unflag_all_accounts"></a>
## `unflag_all_accounts`
- Action type: `unflag_all_accounts`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `'Unflag All Accounts'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "unflag_all_accounts"}
```

<a id="action-unflag_heroes"></a>
## `unflag_heroes`
- Action type: `unflag_heroes`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `'Unflag Heroes'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "unflag_heroes"}
```

<a id="action-use_all_consumables"></a>
## `use_all_consumables`
- Action type: `use_all_consumables`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `multibox` (default observed: `False`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "use_all_consumables"}
```

<a id="action-use_armor_of_salvation"></a>
## `use_armor_of_salvation`
- Action type: `use_armor_of_salvation`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `multibox` (default observed: `False`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "use_armor_of_salvation"}
```

<a id="action-use_conset"></a>
## `use_conset`
- Action type: `use_conset`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `multibox` (default observed: `False`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "use_conset"}
```

<a id="action-use_consumables"></a>
## `use_consumables`
- Action type: `use_consumables`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `mode` (default observed: `ctx.step.get('selector', 'all')`)
- `selector` (default observed: `'all'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "use_consumables", "mode": "all", "multibox": true}
```

<a id="action-use_essence_of_celerity"></a>
## `use_essence_of_celerity`
- Action type: `use_essence_of_celerity`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `multibox` (default observed: `False`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "use_essence_of_celerity"}
```

<a id="action-use_grail_of_might"></a>
## `use_grail_of_might`
- Action type: `use_grail_of_might`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `multibox` (default observed: `False`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "use_grail_of_might"}
```

<a id="action-use_pcons"></a>
## `use_pcons`
- Action type: `use_pcons`
- Aliases: `none`
- Purpose: Execute party/engine/control behavior affecting team state.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `multibox` (default observed: `False`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May modify party behavior/flags/recovery anchors, consume items, or dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "use_pcons"}
```



