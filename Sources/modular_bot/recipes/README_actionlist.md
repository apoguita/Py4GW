# Modular Bot Recipe Action List

This file centralizes the JSON action documentation used by:

- `Sources/modular_bot/recipes/mission.py`
- `Sources/modular_bot/recipes/quest.py`
- `Sources/modular_bot/recipes/route.py`

Step dispatch starts in:

- `Sources/modular_bot/recipes/modular_actions.py`

Step handlers are grouped in:

- `Sources/modular_bot/recipes/actions_movement.py`
- `Sources/modular_bot/recipes/actions_targeting.py`
- `Sources/modular_bot/recipes/actions_interaction.py`
- `Sources/modular_bot/recipes/actions_party.py`
- `Sources/modular_bot/recipes/actions_inventory.py`

Named target registries live in:

- `Sources/modular_bot/recipes/target_enums.py`

## Step Contract

Each step object must include:

- `type`: action name

Every step supports optional:

- `ms`: post-step wait in milliseconds (default: `100`)
- `repeat`: how many times to register/execute that step (default: `1`)

Special case:

- `wait` uses `ms` as the action duration itself.
- `skip_cinematic` also supports `wait_ms` as a pre-wait before skip.
- `travel_gh` uses `ms` for travel wait timing (`wait_time` remains supported for backward compatibility).

## Shared Step Catalog

```json
{"type": "path", "name": "Path 1", "points": [[0, 0], [100, 100]]}
{"type": "auto_path", "name": "AutoPath 1", "points": [[0, 0], [100, 100]]}
{"type": "auto_path_delayed", "name": "Delay Path", "points": [[0, 0], [100, 100]], "delay_ms": 35000}
{"type": "wait", "ms": 1000}
{"type": "wait_out_of_combat"}
{"type": "wait_map_load", "map_id": 72}
{"type": "move", "name": "Move", "x": 0, "y": 0}
{"type": "path_to_target", "target": "Shadow Ranger"}
{"type": "path_to_target", "model_id": 1234}
{"type": "path_to_target", "agent_id": 4567}
{"type": "path_to_target", "enemy": "SHADOW_RANGER"}
{"type": "path_to_target", "target": "Shadow", "model_id": 1234, "max_dist": 5000, "exact_name": false, "required": false}
{"type": "target_enemy", "agent_id": 4567}
{"type": "target_enemy", "enemy": "SHADOW_RANGER"}
{"type": "target_enemy", "target": "Shadow Ranger", "set_party_target": true}
{"type": "debug_nearby_enemies"}
{"type": "debug_nearby_enemies", "max_dist": 15000, "limit": 10}
{"type": "debug_nearby_agents"}
{"type": "debug_nearby_agents", "max_dist": 15000, "limit": 20}
{"type": "add_enemy_blacklist", "enemy_name": "Infernal Wurm"}
{"type": "remove_enemy_blacklist", "enemy_name": "Infernal Wurm"}
{"type": "travel", "target_map_id": 284}
{"type": "travel_gh", "ms": 4000}
{"type": "leave_party", "ms": 2000}
{"type": "exit_map", "x": 0, "y": 0, "target_map_id": 0}
{"type": "interact_npc", "name": "Talk NPC", "x": 0, "y": 0}
{"type": "interact_npc", "target": "Khobay the Betrayer"}
{"type": "interact_npc", "model_id": 1613}
{"type": "interact_npc", "npc": "KHOBAY_THE_BETRAYER"}
{"type": "interact_npc", "nearest": true, "max_dist": 800}
{"type": "interact_gadget"}
{"type": "interact_gadget_at_xy", "x": 0, "y": 0}
{"type": "interact_gadget", "target": "Obelisk"}
{"type": "interact_gadget", "model_id": 987}
{"type": "interact_gadget", "gadget": "OBELISK"}
{"type": "interact_gadget", "nearest": true, "max_dist": 800}
{"type": "loot_chest", "x": 0, "y": 0}
{"type": "loot_chest", "gadget": "CHEST_OF_WOE"}
{"type": "loot_chest", "x": 0, "y": 0, "multibox": true}
{"type": "interact_item"}
{"type": "use_item", "model_id": 22280}
{"type": "use_item", "item": "LOCKPICK"}
{"type": "interact_item", "model_id": 2619}
{"type": "interact_item", "item": "LOCKPICK", "max_dist": 5000}
{"type": "interact_item", "model_id": "0xA3B", "max_dist": 5000}
{"type": "interact_quest_npc"}
{"type": "interact_nearest_npc"}
{"type": "dialog", "name": "Dialog", "x": 0, "y": 0, "id": 0}
{"type": "dialog", "target": "The Wailing Lord", "id": "0x84"}
{"type": "dialog", "model_id": 1613, "id": "0x84"}
{"type": "dialog", "npc": "THE_WAILING_LORD", "id": "0x84"}
{"type": "dialog", "nearest": true, "max_dist": 800, "id": "0x84"}
{"type": "dialog_with_model", "model_id": 1613, "id": "0x84"}
{"type": "dialogs", "name": "Dialogs", "x": 0, "y": 0, "id": ["0x2", "0x15", "0x3"]}
{"type": "dialogs", "target": "Forgotten Seer", "id": ["0x2", "0x15", "0x3"]}
{"type": "dialogs", "npc": "FORGOTTEN_SEER", "id": ["0x2", "0x15", "0x3"]}
{"type": "dialog_multibox", "id": 0}
{"type": "skip_cinematic", "wait_ms": 500}
{"type": "set_title", "id": 0}
{"type": "follow_model", "model_id": 1613, "follow_range": 600}
{"type": "follow_model", "model_id": "0x64D", "follow_range": 600, "timeout_ms": 120000}
{"type": "use_all_consumables"}
{"type": "drop_bundle"}
{"type": "key_press", "key": "F1"}
{"type": "force_hero_state", "state": "fight"}
{"type": "force_hero_state", "state": "guard"}
{"type": "force_hero_state", "state": "avoid"}
{"type": "force_hero_state", "behavior": 2}
{"type": "flag_heroes", "x": 0, "y": 0}
{"type": "flag_all_accounts", "x": 0, "y": 0}
{"type": "unflag_heroes"}
{"type": "unflag_all_accounts"}
{"type": "resign"}
{"type": "summon_all_accounts"}
{"type": "invite_all_accounts"}
{"type": "set_anchor", "phase": "03. Mission: Thunderhead Keep"}
{"type": "wait_map_change", "target_map_id": 0}
{"type": "wait_model_has_quest", "model_id": 1562}
{"type": "set_auto_combat", "enabled": true}
{"type": "set_auto_combat", "enabled": false}
{"type": "set_auto_looting", "enabled": true}
{"type": "set_auto_looting", "enabled": false}
{"type": "set_hard_mode", "enabled": true}
{"type": "set_hard_mode", "enabled": false}
{"type": "restock_kits", "x": 0, "y": 0}
{"type": "restock_kits", "npc": "MERCHANT"}
{"type": "restock_kits", "x": 0, "y": 0, "id_kits": 2, "salvage_kits": 8}
{"type": "restock_kits", "npc": "MERCHANT", "id_kits": 2, "salvage_kits": 8}
{"type": "restock_kits", "x": 0, "y": 0, "id_kits": 1, "salvage_kits": 4, "multibox": true}
{"type": "restock_cons"}
{"type": "sell_nonsalvageable_golds", "npc": "MERCHANT", "multibox": true}
{"type": "sell_leftover_materials", "npc": "MERCHANT", "batch_size": 10, "multibox": true}
{"type": "sell_scrolls", "npc": "MERCHANT", "multibox": true}
{"type": "deposit_materials", "materials": ["Bone", "Feather"], "exact_quantity": 0, "multibox": true}
{"type": "inventory_cleanup", "map_id": 485, "multibox": true}
{"type": "auto_path", "name": "Wait in place", "points": [[0, 0]], "ms": 25000, "repeat": 20}
```

## Notes

- `kind`-specific recipe wrappers still exist (`Mission(...)`, `Quest(...)`) but action handling is shared.
- `path` and `auto_path` both autopath each listed waypoint independently via `get_path_to(...)`.
- `repeat <= 0` skips that source step.
- `key_press` supported keys: `F1`, `F2`, `SPACE`, `ENTER`, `ESCAPE`/`ESC`.
- `force_hero_state` values: `fight`, `guard`, `avoid`.
  Numeric override: `behavior` = `0`/`1`/`2`.
- `flag_all_accounts` applies account flagging for the active combat engine:
  CustomBehaviors uses shared formation flags; HeroAI sets shared HeroAI flag positions.
- `unflag_all_accounts` clears account-level flags for the active combat engine.
- `set_auto_combat enabled` toggles combat for the active combat engine.
- `set_auto_looting enabled` toggles Botting `auto_loot` and looting for the active combat engine.
- `set_hard_mode enabled` toggles party Hard Mode on/off.
- `interact_item` supports optional `model_id` (int or `"0x..."`) and `max_dist`.
  It also supports `item` for a named item target from `target_enums.py`.
  If `model_id` is set, only matching ground items owned by self/unowned are interacted.
- `interact_npc`, `dialog`, and `dialogs` can resolve the NPC by:
  `x` + `y`, `npc`, `target`/`name_contains`, `model_id`, or `nearest=true`.
  Optional: `max_dist` (default `Range.Compass` = `5000`), `exact_name` (default `false`).
- `interact_gadget` and `interact_gadget_at_xy` can resolve the gadget by:
  `x` + `y`, `gadget`, `target`/`name_contains`, `model_id`, or `nearest=true`.
  Optional: `max_dist` (default `Range.Compass` = `5000`), `exact_name` (default `false`).
- `path_to_target` scans enemies within `max_dist` (default `Range.Compass` = `5000`) and moves to the nearest match.
  Match by `agent_id`, `enemy`, partial `target`/`name_contains`/`enemy_name`, `model_id`, or combinations of these.
  Optional: `exact_name` (default `false`), `required` (default `true`), `tolerance` (default `150`).
- `target_enemy` changes your current target to the resolved enemy.
  Resolve by `agent_id`, `enemy`, `target`/`name_contains`, `model_id`, or `nearest=true`.
  Optional: `max_dist` (default `Range.Compass` = `5000`), `exact_name` (default `false`), `set_party_target` (default `false`).
- Any modular action using `npc`, `enemy`, or `gadget` selectors now defaults `max_dist` to `Range.Compass`
  when that field is omitted.
- `debug_nearby_enemies` logs nearby enemies to console with `agent_id`, `model_id`, distance, alive, and name.
  Optional: `max_dist` (default `5000`), `limit` (default `25`), `include_dead` (default `false`).
- `debug_nearby_agents` logs nearby agents to console with `agent_id`, `model_id`, distance, alive, type flags, allegiance, and name.
  Optional: `max_dist` (default `5000`), `limit` (default `25`), `include_dead` (default `true`).
- `add_enemy_blacklist` adds `enemy_name` (case-insensitive) to `EnemyBlacklist` name entries.
  Required: `enemy_name` (non-empty string).
- `remove_enemy_blacklist` removes `enemy_name` (case-insensitive) from `EnemyBlacklist` name entries.
  Required: `enemy_name` (non-empty string).
- `restock_kits` requires merchant position `x` + `y`.
  It can also resolve the merchant using `npc`.
  Optional: `id_kits` (default `2`), `salvage_kits` (default `8`), `multibox` (default `false`).
- `restock_cons` restocks consumables from storage using bot upkeep config.
  It always attempts to open Xunlai storage first.
  It calls restock for all currently available consumable helpers in `bot.Items.Restock`:
  Birthday Cupcake, Candy Apple, Honeycomb, War Supplies, Essence of Celerity,
  Grail of Might, Armor of Salvation, Golden Egg, Candy Corn, Slice of Pumpkin Pie,
  Drake Kabob, Bowl of Skalefin Soup, and Pahnai Salad.
  The recipe step enables each matching property when that property exists, is currently disabled,
  and its `restock_quantity` is greater than `0`.
  The `OpenXunlaiWindow()` attempt uses a fixed `1000ms` wait.
- `deposit_materials` accepts optional `exact_quantity` (default `250`).
  Set `exact_quantity` to `0` to deposit any stack size.
- `sell_nonsalvageable_golds` sells identified, non-salvageable gold items at merchant.
  Optional: `multibox` (default `false`).
- `sell_leftover_materials` sells non-rare common material stacks below `batch_size` (default `10`) at merchant.
  Optional: `multibox` (default `false`).
- `sell_scrolls` sells configurable scroll model IDs at merchant.
  Optional: `scroll_models` list (default BDS scroll set), `multibox` (default `false`).
- `inventory_cleanup` is a composite step that runs:
  resign -> leave_party -> travel_gh -> deposit crafting mats -> sell trader mats ->
  sell non-salvageable golds -> sell leftover common mats -> sell scrolls -> restock kits ->
  (optional) travel to `map_id` -> summon/invite alts.
  Parameters:
  `map_id` (optional, default `None`; when omitted/`null`/`"none"` it returns to the map where cleanup was triggered),
  `multibox` (default `true`),
  `id_kits` (default `3`),
  `salvage_kits` (default `10`),
  `batch_size` (default `10`).
- `follow_model` follows an NPC/agent model ID at `follow_range`.
  Optional `timeout_ms` exits after that duration.
- `set_anchor` updates ModularBot runtime recovery anchor.
  Accepts `phase` (phase/header name). If omitted, uses current FSM state name.
- `dialog_with_model` remains supported, but `dialog` can now also resolve by `model_id`.
- `interact_gadget_at_xy` remains supported as a gadget interaction alias; it now also accepts selectors.
- `loot_chest` moves to a chest selector, finds nearest chest, and interacts.
  It accepts `x` + `y`, `gadget`, `target`/`name_contains`, `model_id`, or `nearest=true`.
  Optional: `multibox` (default `false`) dispatches `InteractWithTarget` to alts and waits per account, BDS-style.
  Optional: `max_dist` (default `5000`) for chest search radius.
- `wait_model_has_quest` blocks until the NPC model has a quest marker.

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
