# Inventory Actions

Merchant/storage/material workflows, setup/guard/cleanup orchestration, and widget-mediated routines.

Common runtime keys (all actions):
- `name` (default: auto-generated label)
- `ms` (default: `250`) post-step wait; for `wait`, this is the action duration
- `repeat` (default: `1`) expands registration count in `register_repeated_steps`
- `anchor` (default: `false`) sets runtime anchor after this step

<a id="action-buy_ectoplasm"></a>
## `buy_ectoplasm`
- Action type: `buy_ectoplasm`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `max_ecto_to_buy` (default observed: `0`)
- `multibox` (default observed: `False`)
- `multibox_wait_step_ms` (default observed: `50`)
- `multibox_wait_timeout_ms` (default observed: `30000`)
- `name` (default observed: `'Buy Ectoplasm'`)
- `start_storage_gold_threshold` (default observed: `900000`)
- `stop_storage_gold_threshold` (default observed: `500000`)
- `use_storage_gold` (default observed: `True`)
- Selector support: `npc` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `npc`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "buy_ectoplasm", "name": "Buy Ectos", "npc": "RARE_MATERIAL_TRADER", "use_storage_gold": true, "start_storage_gold_threshold": 900000, "stop_storage_gold_threshold": 500000}
```

<a id="action-deposit_materials"></a>
## `deposit_materials`
- Action type: `deposit_materials`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `deposit_wait_ms` (default observed: `250`)
- `exact_quantity` (default observed: `250`)
- `materials` (default observed: `None`)
- `max_deposit_items` (default observed: `0`)
- `max_passes` (default observed: `2`)
- `multibox` (default observed: `False`)
- `multibox_wait_step_ms` (default observed: `50`)
- `multibox_wait_timeout_ms` (default observed: `30000`)
- `name` (default observed: `'Deposit Materials'`)
- `open_wait_ms` (default observed: `1000`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "deposit_materials", "materials": ["Bone", "Feather"], "exact_quantity": 0, "multibox": true}
```

<a id="action-disable_widgets"></a>
## `disable_widgets`
- Action type: `disable_widgets`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `'Disable Widgets'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "disable_widgets", "name": "Disable Widgets", "widgets": ["InventoryPlus", "CustomBehaviors"], "multibox": true}
```

<a id="action-enable_widgets"></a>
## `enable_widgets`
- Action type: `enable_widgets`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `'Enable Widgets'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "enable_widgets", "name": "Enable Widgets", "widgets": ["InventoryPlus", "CustomBehaviors"], "multibox": true}
```

<a id="action-inventory_cleanup"></a>
## `inventory_cleanup`
- Action type: `inventory_cleanup`
- Aliases: `none`
- Purpose: Run the full GH cleanup sequence (resign/leave/travel/sell/restock/return/summon-invite).
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `batch_size` (default observed: `10`)
- `id_kits` (default observed: `3`)
- `map_id` (default observed: `None`)
- `multibox` (default observed: `True`)
- `salvage_kits` (default observed: `10`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: Registers and executes multiple sub-steps; can travel maps and dispatch multibox party commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "inventory_cleanup", "map_id": 485, "multibox": true}
```

<a id="action-inventory_guard"></a>
## `inventory_guard`
- Action type: `inventory_guard`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `id_kits_min` (default observed: `ctx.step.get('id_kits_target', 3)`)
- `id_kits_target` (default observed: `3`)
- `name` (default observed: `'Inventory Guard'`)
- `salvage_kits_min` (default observed: `ctx.step.get('salvage_kits_target', 10)`)
- `salvage_kits_target` (default observed: `10`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "inventory_guard", "name": "Inventory Guard", "id_kits_min": 3, "salvage_kits_min": 10}
```

<a id="action-inventory_setup"></a>
## `inventory_setup`
- Action type: `inventory_setup`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `'Inventory Setup'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "inventory_setup", "name": "Inventory Setup", "multibox": true, "location": "auto"}
```

<a id="action-merchant_rules_execute"></a>
## `merchant_rules_execute`
- Action type: `merchant_rules_execute`
- Aliases: `none`
- Purpose: Dispatch Merchant Rules execute command locally and/or multibox accounts.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `auto_enable_widget` (default observed: `True`)
- `enable_wait_ms` (default observed: `350`)
- `include_protected` (default observed: `False`)
- `instant_destroy` (default observed: `False`)
- `local` (default observed: `True`)
- `ms` (default observed: `0`)
- `multibox` (default observed: `True`)
- `multibox_wait_step_ms` (default observed: `50`)
- `multibox_wait_timeout_ms` (default observed: `90000`)
- `name` (default observed: `'Merchant Rules Execute'`)
- `request_id` (default observed: `''`)
- `widget_names` (default observed: `['MerchantRules', 'Merchant Rules']`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "merchant_rules_execute", "name": "Merchant Rules Execute", "multibox": true}
```

<a id="action-restock_cons"></a>
## `restock_cons`
- Action type: `restock_cons`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `name` (default observed: `'Restock Consumables'`)
- Selector support: `none` (no selector resolver helper used directly).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "restock_cons"}
```

<a id="action-restock_kits"></a>
## `restock_kits`
- Action type: `restock_kits`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `id_kits` (default observed: `2`)
- `multibox` (default observed: `False`)
- `multibox_wait_step_ms` (default observed: `50`)
- `multibox_wait_timeout_ms` (default observed: `30000`)
- `name` (default observed: `'Restock Kits'`)
- `salvage_kits` (default observed: `8`)
- Selector support: `npc` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `npc`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "restock_kits", "point": [0, 0]}
```

<a id="action-sell_leftover_materials"></a>
## `sell_leftover_materials`
- Action type: `sell_leftover_materials`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `batch_size` (default observed: `10`)
- `multibox` (default observed: `False`)
- `multibox_wait_step_ms` (default observed: `50`)
- `multibox_wait_timeout_ms` (default observed: `30000`)
- `name` (default observed: `'Sell Leftover Materials'`)
- Selector support: `npc` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `npc`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "sell_leftover_materials", "npc": "MERCHANT", "batch_size": 10, "multibox": true}
```

<a id="action-sell_materials"></a>
## `sell_materials`
- Action type: `sell_materials`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `materials` (default observed: `None`)
- `multibox` (default observed: `False`)
- `multibox_wait_step_ms` (default observed: `50`)
- `multibox_wait_timeout_ms` (default observed: `30000`)
- `name` (default observed: `'Sell Materials'`)
- Selector support: `npc` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `npc`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "sell_materials", "name": "Sell Materials", "npc": "CRAFTING_MATERIAL_TRADER", "materials": ["Bone", "Feather"], "multibox": true}
```

<a id="action-sell_nonsalvageable_golds"></a>
## `sell_nonsalvageable_golds`
- Action type: `sell_nonsalvageable_golds`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `multibox` (default observed: `False`)
- `multibox_wait_step_ms` (default observed: `50`)
- `multibox_wait_timeout_ms` (default observed: `30000`)
- `name` (default observed: `'Sell Non-Salvageable Golds'`)
- Selector support: `npc` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `npc`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "sell_nonsalvageable_golds", "npc": "MERCHANT", "multibox": true}
```

<a id="action-sell_scrolls"></a>
## `sell_scrolls`
- Action type: `sell_scrolls`
- Aliases: `none`
- Purpose: Execute inventory/merchant/storage workflow behavior.
- Required fields: `none` (beyond `type`).
- Optional fields/defaults:
- `multibox` (default observed: `False`)
- `multibox_wait_step_ms` (default observed: `50`)
- `multibox_wait_timeout_ms` (default observed: `30000`)
- `name` (default observed: `'Sell Scrolls'`)
- `scroll_models` (default observed: `[5594, 5595, 5611, 5853, 5975, 5976, 21233]`)
- Selector support: `npc` selector family via `resolve_agent_xy_from_step` (`point`, legacy `x/y`, `npc`, `target`/`name_contains`, `model_id`, `nearest`, `max_dist`, `exact_name`).
- Side effects: May move/interact with merchants/storage, buy/sell/deposit items, toggle widgets, and dispatch multibox commands.
- Failure/skip behavior: If validation/selector resolution/prerequisites fail, the step logs context and returns safely without fatal exceptions.
- Runnable example:
```json
{"type": "sell_scrolls", "npc": "MERCHANT", "multibox": true}
```



