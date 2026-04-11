# IniManager Behavior And Usage Guide

This document explains how `Py4GWCoreLib/IniManager.py` actually works in this repo, what it persists, what it does not persist automatically, and how existing widgets/scripts use it in practice.

It is based on:

- `Py4GWCoreLib/IniManager.py`
- `Py4GWCoreLib/ImGui_src/ImGuisrc.py`
- `Widgets/Coding/ImGui/Icon Explorer.py`
- `Widgets/Coding/Tools/Bridge Client.py`
- `Widgets/Guild Wars/Triggers/Enter character on load.py`
- `Widgets/WidgetCatalog/Py4GW_widget_catalog.py`
- `Widgets/Coding/Examples/WidgetTemplate.py`

## What IniManager Is

`IniManager` is a singleton wrapper around `IniHandler` plus some higher-level state management.

It manages three related but different systems:

1. ini file creation and lookup
2. per-window geometry persistence
3. variable-definition/value persistence

These systems are related, but they are not the same thing.

That distinction is the main source of confusion when a script looks "hooked" to the ini manager but still does not persist correctly.

## The Three Persistence Layers

### 1. File/key creation

This is done through:

- `IniManager().ensure_key(path, filename)`
- `IniManager().ensure_global_key(path, filename)`

These create or retrieve a `ConfigNode` keyed by `path/filename`.

Behavior:

- `ensure_key(...)` is account-scoped
- `ensure_global_key(...)` is global
- account-scoped keys fail and return `""` if the account email is not ready
- global keys do not depend on account email

Resolved storage roots:

- account-scoped: `Settings/<account_email>/...`
- global: `Settings/Global/...`

If the target ini file does not exist, `IniManager` creates it.

Before creating a blank file, it looks for a template:

- specialized: `Settings/Defaults/<path>/<filename>.cfg`
- fallback: `Settings/Defaults/default_template.cfg`

If a template exists, its contents are copied into the new ini file.

Important:

- `ensure_key(...)` / `ensure_global_key(...)` only guarantee a handler/node exists
- they do not automatically register vars
- they do not automatically load vars
- they do not automatically save var values

### 2. Window config persistence

This is the `Window config` section handling:

- `x`
- `y`
- `width`
- `height`
- `collapsed`

This is handled through the `ImGui.Begin(...)` / `ImGui.End(...)` wrapper in `Py4GWCoreLib/ImGui_src/ImGuisrc.py`, not by `load_once()`.

The flow is:

1. `ImGui.Begin(ini_key, ...)` calls `IniManager().begin_window_config(ini_key)`
2. that restores saved position, size, and collapsed state before `Begin`
3. begin result is tracked with:
   - `track_window_collapsed(...)`
   - `mark_begin_success(...)`
4. `ImGui.End(ini_key)` calls:
   - `IniManager().end_window_config(ini_key)`
   - `IniManager().save_vars(ini_key)`

Important:

- this window-state system is separate from registered config vars
- window geometry is written directly through `node.ini_handler.write_key(...)`
- it does not depend on `add_bool` / `add_str` / `load_once`

So a script can have working window position persistence even if its custom vars are not wired correctly.

### 3. Variable-definition/value persistence

This is the higher-level var system:

- register definitions with `add_bool`, `add_int`, `add_float`, `add_str`
- load them with `load_once(key)`
- read them with `get...(...)`
- update them with `set(...)`
- stage them for disk flush with `save_vars(key)`

This is the part most widgets mean when they say they are "using IniManager".

## The Variable System Lifecycle

### Step 1. Create the key

Example pattern:

```python
INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
if not INI_KEY:
    return
```

Or for shared/global state:

```python
INI_KEY = IniManager().ensure_global_key(INI_PATH, INI_FILENAME)
if not INI_KEY:
    return
```

### Step 2. Register variable definitions

Example:

```python
IniManager().add_bool(INI_KEY, "favorites_only", "View", "favorites_only", default=False)
IniManager().add_int(INI_KEY, "grid_columns", "View", "grid_columns", default=4)
IniManager().add_str(INI_KEY, "favorites", "Favorites", "favorites", default="")
```

Meaning of those arguments:

- `key`: the ini handler key returned by `ensure_key`
- `var_name`: internal logical variable id
- `section`: ini section name
- `name`: actual ini key written inside that section
- `default`: default value

### Step 3. Load values once into the var cache

```python
IniManager().load_once(INI_KEY)
```

What this does:

- reads registered vars from disk
- converts them using the registered type
- stores them into `vars_values`
- marks `vars_loaded = True`

What it does not do:

- it does not save anything
- it does not update your script variables automatically
- it does not reload repeatedly after the first call

After `load_once`, your script usually copies values from `IniManager` into normal Python state.

Example from `Icon Explorer.py`:

```python
favorites_only = IniManager().getBool(INI_KEY, "favorites_only", False, section="View")
grid_columns = IniManager().getInt(INI_KEY, "grid_columns", 4, section="View")
```

### Step 4. Read values

Read helpers:

- `get(...)`
- `getBool(...)`
- `getInt(...)`
- `getFloat(...)`
- `getStr(...)`

These read from the in-memory var cache, not directly from disk.

If the var is not in `vars_values`, they fall back to the registered default.

### Step 5. Change values

To change a registered variable:

```python
IniManager().set(INI_KEY, "favorites_only", favorites_only, section="View")
```

Important:

- `set(...)` only updates in-memory state
- `set(...)` marks the var dirty
- `set(...)` does not write immediately to disk

### Step 6. Request persistence

To persist dirty registered vars:

```python
IniManager().save_vars(INI_KEY)
```

What `save_vars(...)` actually does:

- it walks `vars_dirty`
- it looks up the registered var definition
- it calls `write_key(...)` for each dirty var
- `write_key(...)` stages pending writes in `pending_writes`
- actual disk flush happens later in the callback registered by `IniManager.enable()`

Important:

- `save_vars(...)` is not the same thing as "write the file right now"
- it stages writes through the manager's callback-driven flush path
- in practice this is usually fine because `IniManager.enable()` is called at the bottom of `IniManager.py`

## Important Internal Details

### Callback-driven flushing

At import time, `IniManager.enable()` registers a callback:

- callback name: `ConfigManager.FlushDiskData`
- phase: `PyCallback.Phase.Data`
- context: `PyCallback.Context.Update`

The callback flushes `pending_writes` when:

- `needs_flush` is true
- there are pending writes
- `write_time` has expired

This means regular variable writes are intentionally throttled and staged.

### Window config writes are different

Window geometry writes in `end_window_config(...)` go straight to `node.ini_handler.write_key(...)`.

That bypasses the staged var system.

So:

- window geometry persistence is more direct
- custom var persistence is staged

### Section handling is stricter than it looks

Registered vars are defined by `var_name`, but runtime values are stored by `(section, var_name)`.

This matters because:

- `get(...)` and `set(...)` should use the same `section`
- if you omit the section on a var registered in a non-empty section, you may read/write the wrong in-memory slot

Example:

```python
IniManager().add_str(INI_KEY, "active_tab", "Tabs", "active_tab", default="Untitled")
```

Then this is correct:

```python
IniManager().getStr(INI_KEY, "active_tab", "Untitled", section="Tabs")
IniManager().set(INI_KEY, "active_tab", "Untitled", section="Tabs")
```

And this is mismatched:

```python
IniManager().get(INI_KEY, "active_tab", "Untitled")
IniManager().set(INI_KEY, "active_tab", "Untitled")
```

The repo contains examples that do this correctly and examples that are looser.

Best practice:

- always pass the section explicitly for registered vars unless the section is intentionally `""`

### Variable names should be unique per ini key

`vars_defs` is keyed only by `var_name`.

That means:

- two vars with the same `var_name` in different sections will collide
- last registered definition wins

Best practice:

- treat `var_name` as globally unique within one ini file/key
- do not rely on section names to disambiguate duplicate `var_name`s

### `load_once()` is exactly once

After a node's vars are loaded, `load_once()` returns without reloading.

So if you need a fresh disk read later, `load_once()` is not enough by itself.

## Real Usage Patterns In The Repo

### Pattern A. Simple local widget settings with immediate save on change

Representative file:

- `Widgets/Coding/ImGui/Icon Explorer.py`

Pattern:

1. `ensure_key(...)`
2. register vars
3. `load_once(...)`
4. copy values into normal Python globals
5. on UI change:
   - `IniManager().set(...)`
   - `IniManager().save_vars(...)`

This is the clearest general-purpose widget pattern.

### Pattern B. Tool settings stored in a state object

Representative file:

- `Widgets/Coding/Tools/Bridge Client.py`

Pattern:

1. register config vars
2. load them into a long-lived state object
3. keep temporary UI state separate from applied runtime state
4. when the user applies changes:
   - update runtime state
   - `set(...)`
   - `save_vars(...)`

This is a good pattern for tools with apply/reconnect/restart semantics.

### Pattern C. Global key used to force file creation / shared flags

Representative file:

- `Widgets/Guild Wars/Triggers/Enter character on load.py`

Pattern:

1. `ensure_global_key(...)`
2. register at least one var
3. `load_once(...)`
4. `set(...)`
5. `save_vars(...)`

This pattern is often used when the script mainly wants a guaranteed ini file or shared global marker, even if it does not have much UI.

### Pattern D. Large global manager with several ini files

Representative file:

- `Widgets/WidgetCatalog/Py4GW_widget_catalog.py`

Pattern:

1. create multiple global keys
2. register many vars
3. call `load_once(...)`
4. set bootstrap/init markers
5. call `save_vars(...)`
6. save individual settings explicitly when they change

This is the most complete example of the system being used as a real configuration layer.

### Pattern E. Window-state persistence through `ImGui.Begin` / `ImGui.End`

Representative file:

- `Py4GWCoreLib/ImGui_src/ImGuisrc.py`

Pattern:

1. pass `ini_key` into `ImGui.Begin(...)`
2. pass the same `ini_key` into `ImGui.End(...)`
3. let the wrapper manage window geometry

This is separate from your own custom `add_*` vars.

## Global vs Non-Global

Use `ensure_key(...)` when the data should be account-specific.

Use `ensure_global_key(...)` when the data should be shared across accounts or available before account identity exists.

From the class behavior:

- local/account keys depend on `Player.GetAccountEmail()`
- global keys do not

Examples of global usage:

- widget catalog
- enter-on-load trigger
- enemy blacklist
- multiboxing/following shared config

Examples of account-scoped usage:

- Bridge Client
- Icon Explorer
- InventoryPlus
- many bot/widget configs

## Common Misunderstandings

### "I called `load_once()`, so it should save"

False.

`load_once()` only loads registered vars into memory.

### "I called `set()`, so it should save"

False.

`set()` only updates cached vars and marks them dirty.

### "I called `save_vars()`, so the file is written immediately"

Not exactly.

`save_vars()` stages writes through `write_key(...)`, and the callback flushes them later.

In practice this is still the correct API to call for registered vars.

### "The window remembers its size, so my custom settings must be wired correctly too"

False.

Window geometry uses a different path through `begin_window_config(...)` / `end_window_config(...)`.

### "Section names make duplicate var names safe"

False.

Definitions are keyed only by `var_name`.

## Recommended Usage Pattern

For a normal widget/tool:

1. Create the key with `ensure_key(...)` or `ensure_global_key(...)`
2. Register all vars exactly once
3. Call `load_once(...)`
4. Copy loaded values into your own widget/app state
5. On user changes:
   - call `IniManager().set(...)`
   - then call `IniManager().save_vars(...)`
6. If using the shared window wrapper, pair `ImGui.Begin(ini_key, ...)` with `ImGui.End(ini_key)`
7. Pass explicit `section=...` when reading and writing registered vars
8. Keep `var_name` unique within the ini key

## Recommended Pattern For Bot Factory

For Bot Factory specifically:

- decide whether config should be account-scoped or global
- register vars for explicit UI/app state only
- do not assume tab state is saved unless both `section="Tabs"` and `save_vars(INI_KEY)` are used correctly
- if using `ImGui.Begin(INI_KEY, ...)` and `ImGui.End(INI_KEY)`, that only covers window geometry plus any dirty vars flushed by `ImGui.End`
- keep reusable UI component state separate from persisted config state

For a tab label example, the correct form is:

```python
IniManager().add_str(INI_KEY, "active_tab", "Tabs", "active_tab", default="Untitled")
IniManager().load_once(INI_KEY)

tab_label = IniManager().getStr(INI_KEY, "active_tab", "Untitled", section="Tabs")

IniManager().set(INI_KEY, "active_tab", tab_label, section="Tabs")
IniManager().save_vars(INI_KEY)
```

## Practical Takeaways

- `ensure_*_key()` creates/opens the file handler
- `add_*()` defines vars
- `load_once()` loads defs into memory once
- `get*()` reads memory
- `set()` only marks dirty
- `save_vars()` is required for registered vars to persist
- `ImGui.Begin/End` handles window geometry separately
- global and account-scoped keys are intentionally different systems
- section mismatches and duplicate `var_name`s are easy failure modes

If a script looks "hooked" but does not actually persist, the usual causes are:

- wrong key scope
- missing `load_once()`
- missing `save_vars()`
- wrong `section=...`
- duplicate `var_name`
- relying on window persistence to imply var persistence
