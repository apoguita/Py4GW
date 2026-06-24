# Database Manager And Database Namespace

This document describes the current database architecture used by `Py4GWCoreLib`:

- `DBMgr`: the low-level SQLite database manager
- `Database`: the namespace used by project code
- `Database.Account`: account-focused helpers for `Py4GW_Accounts`
- `Database.Settings`: settings-focused helpers for `Py4GW_Settings`

It reflects the current direct-database-access implementation.

## Overview

The database stack is intentionally split into two layers:

1. `DBMgr`
   - generic database lifecycle and CRUD operations
   - bootstrap and catalog management
   - SQL generation for common operations

2. project subclasses exposed through `Database`
   - project-specific tables
   - project-specific helper methods
   - no raw SQL required from normal callers

In normal usage, project code should prefer:

```python
from Py4GWCoreLib import Database

accounts = Database.Account()
settings = Database.Settings()
```

and only drop to `DBMgr` when generic database operations are actually needed.

## DBMgr

Source:

- [Py4GWCoreLib/database_src/DBMgr.py](C:/Users/Apo/Py4GW_python_files/Py4GWCoreLib/database_src/DBMgr.py)

### Purpose

`DBMgr` is the central SQLite manager for the project.

It is responsible for:

- locating the project `data/` directory
- creating and maintaining the PRIMARY internal database
- registering named databases in the PRIMARY catalog
- discovering setup scripts in `data/db_setup/`
- creating database files from setup SQL
- providing generic CRUD and maintenance APIs

### Database naming model

`DBMgr` works by database alias, not by raw filesystem path.

Example:

```python
db = DBMgr('Py4GW_Accounts')
```

That alias is resolved through the PRIMARY catalog database.

### Bootstrap model

On first use, `DBMgr` bootstraps:

- the projects path
- the `data/` folder
- the PRIMARY database
- setup-defined databases discovered from `data/db_setup/*.sql`

This means project databases can be created automatically from SQL setup scripts without manual runtime initialization code.

### Generic API categories

`DBMgr` exposes generic operations such as:

- table creation and schema inspection
- `Insert`, `Update`, `Delete`, `Select`
- `Merge`
- `Execute` for raw SQL escape-hatch use
- transactions
- backup/export/import/vacuum

The intent is:

- app code should not write SQL for normal CRUD
- app code should provide table names, fields, and values

## Database Namespace

Source:

- [Py4GWCoreLib/Database.py](C:/Users/Apo/Py4GW_python_files/Py4GWCoreLib/Database.py)

### Purpose

`Database` is not a database engine by itself.

It is a namespace facade that exposes the project database classes in one place:

```python
from .database_src import Account, DBMgr, Settings


class Database:
    DBMgr = DBMgr
    Account = Account
    Settings = Settings
```

That allows code such as:

```python
Database.DBMgr(...)
Database.Account()
Database.Settings()
```

### Why it exists

The goal is organization:

- one top-level access point
- clear project-specific subclasses
- no need for callers to know the internal `database_src` package layout

## Database.Account

Source:

- [Py4GWCoreLib/database_src/Account.py](C:/Users/Apo/Py4GW_python_files/Py4GWCoreLib/database_src/Account.py)

### Purpose

`Account` is the project-focused subclass for the `Py4GW_Accounts` database.

It wraps account-domain tables and operations:

- `Account`
- `Character`
- `Team`
- `Team_Name`

### Binding

`Account` subclasses `DBMgr` and binds itself to:

```python
DATABASE_NAME = 'Py4GW_Accounts'
```

So:

```python
Database.Account()
```

is already attached to the accounts database.

### Main responsibilities

`Account` provides typed helpers for:

- account lookup by email
- account key lookup
- account create/update/delete
- character create/update/delete
- character lookup by account or name
- team-name create/update/delete
- team membership create/update/delete

### Important method

The key lookup method used across the project is:

```python
GetAccountKey(email)
```

This resolves the account primary key from an immutable email.

## Database.Settings

Source:

- [Py4GWCoreLib/database_src/Settings.py](C:/Users/Apo/Py4GW_python_files/Py4GWCoreLib/database_src/Settings.py)
- [docs/settings_database_cache_model.md](C:/Users/Apo/Py4GW_python_files/docs/settings_database_cache_model.md)

### Purpose

`Settings` is the project-focused subclass for the `Py4GW_Settings` database.

It manages persistent settings keyed by:

- widget/script identity
- global scope
- current account scope
- section
- key

### Binding

`Settings` subclasses `DBMgr` and binds itself to:

```python
DATABASE_NAME = 'Py4GW_Settings'
```

### Current model

The current implementation is cache-first, not direct-access.

That means:

- widget-global settings are served from an in-memory cache
- current-account settings are served from an in-memory cache
- dirty entries are flushed later through a throttled callback
- widget table helpers still talk directly to the database and keep caches synchronized
- non-current-account account operations still use direct DB access

### Tables

The class is built around three logical tables:

- `Widget`
  - catalogs widgets/scripts by project key
- `Globals`
  - stores global settings per widget
- `Keys`
  - stores per-account settings per widget

### Widget catalog role

Before a setting can exist, its widget identity must exist in `Widget`.

`Settings` handles that through:

- `RegisterWidget`
- `EnsureWidget`
- `GetWidgetData`

### Global settings role

Global settings are shared across all accounts for a widget.

Representative methods:

- `SetGlobalValue`
- `GetGlobalValue`
- `GetGlobalEntry`
- `DeleteGlobalValue`
- `GetGlobalSection`

### Account settings role

Account settings are scoped to one account for a widget.

Representative methods:

- `SetAccountValue`
- `GetAccountValue`
- `SetAccountValueByEmail`
- `GetAccountValueByEmail`
- `DeleteAccountValue`
- `GetAccountSection`

### Current-account helpers

For most widget code, the common path is current-account persistence:

- `SetCurrentAccountValue`
- `GetCurrentAccountValue`
- `GetCurrentAccountEntry`

These resolve the current account from `Player.GetAccountEmail()` and, as a fallback path, the game window `HWND`.

### WidgetSettings wrapper

`Settings` also exposes:

```python
settings = Database.Settings().ForWidget(widget_key, widget_name, description)
```

This returns `WidgetSettings`, a convenience wrapper that binds all future calls to one widget key.

Representative wrapper calls:

- `EnsureBool`
- `GetKey`
- `GetBool`
- `SetKey`
- `SetBool`
- `EnsureInt`
- `GetInt`
- `SetInt`
- `EnsureGlobalBool`
- `GetGlobalKey`
- `GetGlobalBool`
- `SetGlobalKey`
- `SetGlobalBool`

The wrapper is intended to reduce repeated `widget_key` plumbing inside widgets.

### Flush behavior

The cache-backed model is frame-friendly rather than immediately durable.

- setters update cache immediately
- dirty keys are written on a throttled callback tick
- account and global dirty entries are flushed together in one transaction
- newly created cached rows may report `0` as their id until the next successful flush

For the full runtime model, see:

- [docs/settings_database_cache_model.md](C:/Users/Apo/Py4GW_python_files/docs/settings_database_cache_model.md)

## Window Persistence

`Settings` currently also contains lightweight window state helpers used by `ImGui.Begin` and `ImGui.End`.

These methods are:

- `begin_window_config`
- `mark_begin_success`
- `track_window_collapsed`
- `end_window_config`

Their role is to persist:

- window x
- window y
- width
- height
- collapsed state

under the `Window config` section for the window name used as the settings identity.

## Recommended Usage

### Generic database work

Use `Database.DBMgr` only when the work is generic and not tied to one project database subclass.

### Accounts database

Use `Database.Account()` when working with:

- account login/profile data
- characters
- teams

### Settings database

Use `Database.Settings()` or `Database.Settings().ForWidget(...)` when working with:

- persistent widget/script configuration
- current-account settings
- shared/global widget settings
- automatic window state persistence

## Example

```python
from Py4GWCoreLib import Database

WIDGET_KEY = 'Widgets/Coding/Examples/WidgetTemplate'

settings = Database.Settings().ForWidget(
    WIDGET_KEY,
    'Widget Template',
    'Template widget using Database.Settings persistence.',
)

enabled = settings.GetBool('Main', 'enabled', default=False)
settings.SetBool('Main', 'enabled', not enabled)
```

## Design Notes

- `DBMgr` is the generic authority.
- `Database` is the project namespace.
- `Account` and `Settings` are the project subclasses.
- `Account` is keyed around the accounts database domain.
- `Settings` is keyed around widget/global/account setting storage.
- The current `Settings` implementation is cache-driven for globals and the active account, with direct-DB fallbacks for widget metadata and non-current-account access.
