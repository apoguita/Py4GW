# Modular Bot Recipe Action List

This file centralizes the JSON action documentation used by:

- `Sources/modular_bot/recipes/mission.py`
- `Sources/modular_bot/recipes/quest.py`

All step execution is handled by:

- `Sources/modular_bot/recipes/modular_actions.py`

## Step Contract

Each step object must include:

- `type`: action name

Every step supports optional:

- `ms`: post-step wait in milliseconds (default: `500`)
- `repeat`: how many times to register/execute that step (default: `1`)

Special case:

- `wait` uses `ms` as the action duration itself.
- `skip_cinematic` also supports `wait_ms` as a pre-wait before skip.

## Shared Step Catalog

```json
{"type": "path", "name": "Path 1", "points": [[0, 0], [100, 100]]}
{"type": "auto_path", "name": "AutoPath 1", "points": [[0, 0], [100, 100]]}
{"type": "auto_path_delayed", "name": "Delay Path", "points": [[0, 0], [100, 100]], "delay_ms": 35000}
{"type": "wait", "ms": 1000}
{"type": "wait_out_of_combat"}
{"type": "wait_map_load", "map_id": 72}
{"type": "move", "name": "Move", "x": 0, "y": 0}
{"type": "exit_map", "x": 0, "y": 0, "target_map_id": 0}
{"type": "interact_npc", "name": "Talk NPC", "x": 0, "y": 0}
{"type": "interact_gadget"}
{"type": "interact_item"}
{"type": "interact_quest_npc"}
{"type": "interact_nearest_npc"}
{"type": "dialog", "name": "Dialog", "x": 0, "y": 0, "id": 0}
{"type": "dialogs", "name": "Dialogs", "x": 0, "y": 0, "id": ["0x2", "0x15", "0x3"]}
{"type": "dialog_multibox", "id": 0}
{"type": "skip_cinematic", "wait_ms": 500}
{"type": "set_title", "id": 0}
{"type": "drop_bundle"}
{"type": "key_press", "key": "F1"}
{"type": "force_hero_state", "state": "fight"}
{"type": "force_hero_state", "state": "guard"}
{"type": "force_hero_state", "state": "avoid"}
{"type": "force_hero_state", "behavior": 2}
{"type": "flag_heroes", "x": 0, "y": 0}
{"type": "unflag_heroes"}
{"type": "resign"}
{"type": "wait_map_change", "target_map_id": 0}
{"type": "set_auto_combat", "enabled": true}
{"type": "set_auto_combat", "enabled": false}
{"type": "auto_path", "name": "Wait in place", "points": [[0, 0]], "ms": 25000, "repeat": 20}
```

## Notes

- `kind`-specific recipe wrappers still exist (`Mission(...)`, `Quest(...)`) but action handling is shared.
- `repeat <= 0` skips that source step.
- `key_press` supported keys: `F1`, `F2`, `SPACE`, `ENTER`, `ESCAPE`/`ESC`.
- `force_hero_state` values: `fight`, `guard`, `avoid`.
  Numeric override: `behavior` = `0`/`1`/`2`.
- `set_auto_combat enabled` toggles CustomBehaviors combat.

## Mission Entry Block (mission.json only)

```json
{"type": "enter_challenge", "delay": 3000, "target_map_id": 0}
{"type": "dialog", "x": 0, "y": 0, "id": 0}
```

## Quest `take_quest` Block (quest.json only)

```json
"take_quest": {
  "outpost_id": 30,
  "quest_npc_location": [0, 0],
  "dialog_id": "0x00000000",
  "wait_ms": 2000,
  "name": "Take Quest"
}
```

Options:

- `outpost_id`: optional
- `quest_npc_location`: required `[x, y]`
- `dialog_id`: required; int, `"0x..."`, or list of them
- `wait_ms`: optional
- `name`: optional
