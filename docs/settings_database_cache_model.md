# Database.Settings Cache Model

This document describes the current behavior of `Py4GWCoreLib/database_src/Settings.py`.

It is specifically about the live `Database.Settings` implementation, which is now a cache-first settings manager layered on top of `DBMgr`.

Source:

- [Py4GWCoreLib/database_src/Settings.py](C:/Users/Apo/Py4GW_python_files/Py4GWCoreLib/database_src/Settings.py)

## Purpose

`Settings` is the persistence layer for widget and script configuration stored in the `Py4GW_Settings` database.

It manages three logical domains:

- widget registration in `Widget`
- widget-global settings in `Globals`
- widget-per-account settings in `Keys`

The class is designed to make repeated settings access cheap during runtime. Instead of hitting SQLite on every read and write, it keeps the active state in memory and flushes dirty entries on a timed callback.

## High-Level Model

`Settings` is not just a CRUD wrapper. It combines five responsibilities:

1. `DBMgr` binding to `Py4GW_Settings`
2. singleton-style shared runtime instance
3. in-memory caches for widget/global/current-account settings
4. deferred persistence through a throttled flush callback
5. convenience helpers for widget code and ImGui window persistence

The important architectural split is:

- `Widget` table operations remain effectively direct-DB operations, with cache mirrors kept in sync
- `Globals` operations are cache-backed
- current-account `Keys` operations are cache-backed
- non-current-account `Keys` operations fall back to direct DB access

## Singleton Behavior

`Settings` is implemented as a process-wide singleton:

- `__new__` reuses `_settings_instance`
- `Instance()` returns `cls()`
- `__init__` is guarded by `_settings_initialized`

That means widget code generally shares one cache, one callback registration, and one view of the currently active account.

## Database Tables And In-Memory Mirrors

The class uses three table constants:

- `WIDGET_TABLE = 'Widget'`
- `GLOBALS_TABLE = 'Globals'`
- `KEYS_TABLE = 'Keys'`

It mirrors them into these in-memory structures:

- `_widget_cache: dict[str, int]`
  Maps normalized `widget_key -> widget_id`.
- `_widget_id_cache: dict[int, str]`
  Reverse lookup `widget_id -> widget_key`.
- `_widget_info_cache: dict[str, tuple[str, Optional[str]]]`
  Tracks known widget name and description metadata.
- `_global_cache: dict[(widget_key, section, key), _CacheEntry]`
  Holds all cached global settings.
- `_account_cache: dict[(widget_key, section, key), _CacheEntry]`
  Holds settings for the current resolved account only.
- `_dirty_global_keys` and `_dirty_account_keys`
  Track pending writes/deletes for the next flush.
- `_widget_metadata`
  Temporarily stores widget name/description updates until flush time.

Each cached setting entry is represented by `_CacheEntry`:

- `value`: serialized DB value as `str`
- `key_type`: one of `bool`, `int`, `float`, `str`
- `dirty`: pending write flag
- `deleted`: tombstone flag for deferred delete
- `db_id`: row id, or `0` if not yet persisted

## Cache Population And Refresh

First access to settings calls `_ensure_cache_populated()`, which immediately delegates to `_refresh_cache_from_disk()` unless all three caches are already marked loaded.

`_refresh_cache_from_disk()` does three things in order:

1. resolves the current account identity
2. reloads widget metadata
3. reloads global settings and current-account settings

### Current account resolution

The active account is resolved from:

- `Player.GetAccountEmail()`
- `Py4GW.Console.get_gw_window_handle()`

Resolution order:

1. try account email via `Account().GetAccountKey(email)`
2. if that fails and HWND exists, look up the account row by `HWND`

The class stores:

- `_cached_email`
- `_cached_hwnd`
- `_cached_account_id`

If email changes, or if both old and new HWND values are non-zero and differ, the current-account cache is invalidated and rebuilt.

### Refresh scope

Refresh loads:

- all widgets from `Widget`
- all globals from `Globals`
- only `Keys` rows for `_cached_account_id`

That is an important design point: `_account_cache` is intentionally not a cache for every account in the database. It is only the live account cache.

## Flush Lifecycle

Dirty changes are persisted by a throttled callback rather than immediately.

### Callback registration

During initialization, `Settings` tries to register a `PyCallback` handler:

- callback name: `Settings.FlushDirtyCache`
- phase: `PyCallback.Phase.Data`
- context: `PyCallback.Context.Update`
- priority: `99`

If the runtime is missing `PyCallback`, registration is skipped rather than failing construction.

`enable()` re-registers the callback, and `disable()` removes it.

### Timers

Two `ThrottledTimer(1000)` instances are used:

- `_flush_timer`
- `_refresh_timer`

The effective write model is:

- cache mutations happen immediately
- disk writes happen on the next flush timer expiration
- a successful flush is followed by a cache refresh from disk

### Flush contents

`_flush_dirty()` wraps the whole batch in a single transaction and performs:

1. widget metadata forwarding through `EnsureWidget`
2. dirty current-account `Keys` deletes, updates, and inserts
3. dirty `Globals` deletes, updates, and inserts
4. `COMMIT` on success or `ROLLBACK` on failure

For new cached rows, `db_id == 0` until insert succeeds during flush.

### Failure handling

The class includes a simple circuit breaker:

- `_flush_failure_count` increments on exception
- after 3 consecutive failures, all dirty flags are cleared and pending metadata is dropped

This prevents an endless error loop inside the frame callback.

## Commit Parameter Semantics

This class still exposes `commit: bool = True` on most public methods, but the meaning is no longer uniform.

### Cache-backed paths

For these operations, `commit` is effectively ignored because the write is staged in memory:

- `SetGlobalValue`
- `SetAccountValue` when targeting the current account
- `SetCurrentAccountValue`
- the corresponding `WidgetSettings` helpers
- deferred deletes for cached entries

On these paths, persistence happens at flush time.

### Direct-DB paths

For these operations, `commit` still matters:

- widget table helpers like `EnsureWidget`
- non-current-account account operations
- direct lookup fallbacks when cache data is not available

## Widget Table Responsibilities

`Widget` acts as the identity catalog for settings owners.

Important methods:

- `RegisterWidget`
- `EnsureWidget`
- `GetWidgetData`
- `GetWidgetDataByID`
- `GetAllWidgets`
- `SetWidgetData`
- `DeleteWidget`

Even though these methods still work directly against the `Widget` table, they also synchronize:

- `_widget_cache`
- `_widget_id_cache`
- `_widget_info_cache`

This keeps later cache-backed settings operations aligned with database row ids.

## Global Settings Behavior

Global settings are widget-scoped and shared across accounts.

Public API:

- `SetGlobalValue`
- `GetGlobalValue`
- `GetGlobalEntry`
- `DeleteGlobalValue`
- `GetGlobalSection`

Behavior:

- reads prefer `_global_cache`
- writes update `_global_cache` and mark entries dirty
- deletes tombstone persisted rows or remove never-persisted rows from cache
- section reads are assembled from cache when available

If a requested global key is missing from cache, the code may probe the DB first to avoid inserting a duplicate later during flush.

## Account Settings Behavior

Account settings have two execution modes.

### Current account

If the supplied account id matches `_cached_account_id`, the code uses `_account_cache`.

That applies to:

- `SetAccountValue`
- `GetAccountValue`
- `GetAccountEntry`
- `DeleteAccountValue`
- `GetAccountSection`

and, by extension, to:

- `SetCurrentAccountValue`
- `GetCurrentAccountValue`
- `GetCurrentAccountEntry`

### Non-current account

If the requested account is not the active cached account, the class falls back to direct DB reads and writes.

That means `Settings` is optimized for the live in-client account, not for bulk multi-account editing.

## WidgetSettings Wrapper

`ForWidget(widget_key, widget_name=None, description=None)` returns a `WidgetSettings` wrapper that pre-binds a widget identity.

This wrapper is the intended ergonomic API for most widget code.

It provides:

- typed ensure helpers like `EnsureBool`, `EnsureInt`, `EnsureGlobalStr`
- typed get helpers like `GetBool`, `GetFloat`, `GetGlobalInt`
- typed set helpers like `SetBool`, `SetStr`, `SetGlobalBool`
- deletion and section helpers

The wrapper does not add a separate storage model. It delegates to the parent `Settings` instance.

## Serialization Rules

Stored values are serialized to strings by `_serialize_value()`:

- `bool -> '1'` or `'0'`
- `int -> str(int(value))`
- `float -> str(float(value))`
- `str -> str(value)`

`_deserialize_value()` reverses that according to the declared key type.

Supported key types are strictly:

- `bool`
- `int`
- `float`
- `str`

Any other type raises `ValueError`.

## Window Persistence Helpers

The class also contains an ImGui window persistence layer built on top of normal settings storage.

Relevant APIs:

- `begin_window_config`
- `mark_begin_success`
- `track_window_collapsed`
- `end_window_config`

These methods store state under the `Window config` section using the widget key as the identity. Persisted fields are:

- `x`
- `y`
- `width`
- `height`
- `collapsed`

`WindowState` keeps transient runtime information so the class can avoid redundant writes and only persist actual changes after a successful `Begin`/`End` cycle.

## Operational Characteristics

A few behaviors matter when reasoning about this class:

- newly created cached rows may return `0` as their row id until the next successful flush
- a `Get...Value(..., default=...)` on a missing key seeds the cache with the default value, but usually does not mark it dirty by itself
- widget metadata (`widget_name`, `description`) can be supplied by callers and is forwarded to `EnsureWidget` during flush
- when Py4GW runtime components are unavailable, callback registration and current-account resolution degrade defensively instead of crashing the constructor

## Recommended Usage

Prefer:

```python
from Py4GWCoreLib import Database

settings = Database.Settings().ForWidget(
    'Widgets/MyWidget',
    'My Widget',
    'Widget settings owner',
)

enabled = settings.GetBool('Main', 'enabled', default=False)
settings.SetBool('Main', 'enabled', not enabled)
```

Prefer direct `Settings` calls only when you genuinely need:

- cross-widget operations
- direct access by explicit `account_id` or email
- widget catalog management
- window persistence helpers

## What This Class Is Optimized For

The implementation is clearly optimized for:

- many repeated reads/writes from the currently running widget set
- low per-frame settings overhead
- batching SQLite writes into fewer transactions
- preserving the old public API while changing the underlying persistence strategy

It is not optimized for:

- arbitrary multi-account batch edits
- immediate durability after every setter call
- being a neutral import in environments where current-account runtime hooks matter
