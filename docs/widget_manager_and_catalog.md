# Widget Manager And Catalog

This document explains how widget handling currently works in Py4GW, and how the newer `WidgetCatalog` layer fits on top of the existing widget runtime.

The goal is to make it easy to build alternate widget UIs without having to re-derive discovery rules, folder structure, metadata, and filtering logic each time.

## High-Level Structure

Widget handling now lives in one module:

- [`Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py)

That file currently contains three distinct concerns:

1. `Widget`
2. `WidgetHandler`
3. `WidgetCatalog`

There is also UI code in the same file for the existing widget manager window:

- `Py4GWLibrary`
- legacy/simple tree UI helpers in `WidgetHandler.draw_ui()`

So conceptually:

- `Widget` = one live widget instance and its runtime metadata
- `WidgetHandler` = discovery, loading, enable/disable, callback registration, runtime control
- `WidgetCatalog` = a read/query layer over discovered widgets for explorer-style UIs
- `Py4GWLibrary` = one particular UI that consumes widget data

## Widget Discovery

The authoritative discovery logic is in [`WidgetHandler._scan_widget_folders()`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py#L2212).

The rule is exact:

- walk the entire `Widgets` tree
- if a folder contains a file named `.widget`
- load every `.py` file in that same folder

Important implications:

- Discovery is folder-based, not file-based across the whole tree
- A folder without `.widget` is not itself a widget container
- Intermediate folders may appear in the hierarchy even if they are not discovery roots
- A widget's widget_path is the relative folder path of the folder that contained the .widget marker

Example:

- `Widgets/Automation/Bots/Farmers/Trophies/War Supply/.widget` exists
- every `.py` file in `Widgets/Automation/Bots/Farmers/Trophies/War Supply/` is discovered as a widget
- the discovered widgets get `widget_path == "Automation/Bots/Farmers/Trophies/War Supply"`

Discovery is implemented by:

- [`WidgetHandler.discover()`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py#L2192)
- [`WidgetHandler._scan_widget_folders()`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py#L2212)
- [`WidgetHandler._load_widget_module()`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py#L2223)

## The `Widget` Class

`Widget` is the runtime representation of one discovered widget script.

Defined at:

- [`Widget`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py#L1760)

It stores:

- identity
  - `folder_script_name`
  - `plain_name`
  - `widget_path`
  - `script_path`
- callback presence and callback functions
  - `main`
  - `update`
  - `draw`
  - `configure`
  - `tooltip`
  - `minimal`
  - `on_enable`
  - `on_disable`
- extracted metadata
  - `name`
  - `category`
  - `tags`
  - `aliases`
  - `image`
  - `optional`
- runtime state
  - enabled
  - paused
  - configuring

`Widget.load_module()` imports the script, extracts callback functions and metadata, and registers callbacks if available.

Metadata defaults matter:

- `MODULE_NAME` falls back to a cleaned script name
- `MODULE_CATEGORY` falls back to the first folder segment of `widget_path`
- `MODULE_TAGS` falls back to all folder segments in `widget_path`
- `OPTIONAL` defaults to `False` for `System` and `Py4GW`, otherwise `True`

## The `WidgetHandler` Class

`WidgetHandler` is the authoritative runtime manager.

Defined at:

- [`WidgetHandler`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py#L2092)

It is responsible for:

- discovering widgets
- storing all discovered widgets in `self.widgets`
- reading and writing widget enabled state through the manager INI
- enabling and disabling widgets
- pausing and resuming widgets
- executing configuring UIs
- registering and resuming callback execution

Important runtime responsibilities:

- `discover()` rebuilds the set of widgets
- `_apply_ini_configuration()` restores saved enabled states and forces system widgets on
- `enable_widget()` and `disable_widget()` change persistent state through the manager INI
- `execute_configuring_widgets()` runs open configuration panels

Other code in the repo should generally treat `WidgetHandler` as the runtime API.

## Existing UI Behavior

The current widget manager UI is not a true filesystem explorer.

The richer browser UI is `Py4GWLibrary`, defined near the top of the same file.

There is also a simpler tree UI in:

- [`WidgetHandler.draw_ui()`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py#L2422)

One important detail from the current implementation:

- the left-side tree in the current manager is primarily a path filter
- widgets are not fundamentally modeled there as leaf nodes in the same way a real file explorer would
- widgets are rendered separately from filtered widget lists

That is why building alternate UIs directly against `WidgetHandler.widgets` usually forces each UI to reconstruct hierarchy and filter logic for itself.

## Why `WidgetCatalog` Exists

`WidgetCatalog` was introduced to separate:

- runtime concerns
from
- structural/query concerns needed by explorer UIs

Defined at:

- [`WidgetCatalog`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py#L141)

`WidgetCatalog` does not discover widgets by walking the filesystem itself.

Instead, it consumes the already-discovered widgets from `WidgetHandler` and builds a stable snapshot for UI use.

This keeps one source of truth for discovery while still giving alternate UIs a clean model to render.

## `WidgetCatalog` Data Types

### `WidgetCatalogNode`

Defined at:

- [`WidgetCatalogNode`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py#L96)

Represents one folder node in the catalog tree.

Fields:

- `name`
- `depth`
- `parent`
- `path`
- `is_widget_container`
- `children`
- `widget_ids`

`is_widget_container` is important:

- `True` means this node corresponds to a real discovered widget folder, meaning a folder that had a `.widget` file
- `False` means the node is only an intermediate hierarchy segment

### `WidgetCatalogSnapshot`

Defined at:

- [`WidgetCatalogSnapshot`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py#L120)

This is the immutable UI-facing view of the discovered widgets.

It contains:

- `widgets_by_id`
- `tree`
- `categories`
- `tags`
- `paths`
- `widget_container_paths`

Meaning of each:

- `widgets_by_id`
  - the live discovered widgets keyed by `folder_script_name`
- `tree`
  - the hierarchical folder structure built from `widget_path`
- `categories`
  - all unique widget categories
- `tags`
  - all unique widget tags
- `paths`
  - all path segments implied by discovered widgets
- `widget_container_paths`
  - only the exact paths that correspond to actual widget container folders

The distinction between `paths` and `widget_container_paths` matters:

- `paths` includes intermediate folders like `Automation/Bots/Farmers`
- `widget_container_paths` includes only actual `.widget` folders like `Automation/Bots/Farmers/Trophies/War Supply`

### `WidgetCatalogQuery`

Defined at:

- [`WidgetCatalogQuery`](/Py4GWCoreLib/py4gwcorelib_src/WidgetManager.py#L130)

This is a simple filter request object used by UIs.

Fields:

- `text`
- `category`
- `path`
- `tag`
- `scope`
- `sort_by`
- `favorite_ids`

Supported scopes:

- `all`
- `favorites`
- `active`
- `inactive`

Supported sorting:

- `name`
- `category`
- `status`

## `WidgetCatalog` Methods

### `snapshot_from_handler(handler)`

Entry point when you already have a `WidgetHandler`.

It reads `handler.widgets` and builds a `WidgetCatalogSnapshot`.

### `snapshot_from_widgets(widgets)`

Builds the snapshot directly from a widget dictionary.

This method:

- builds the folder tree
- collects all category values
- collects all tag values
- collects all path segments
- records actual widget container paths
- attaches widget ids to the node matching each widget’s `widget_path`

### `query(snapshot, query)`

Filters a snapshot into a widget list.

It supports:

- semicolon-separated search terms
- scope filters
- category/path/tag filters
- special tokens
- sorting

Current special tokens:

- `#enabled`
- `#disabled`
- `#favorites`
- `#system`
- `#no_image`

### `tree_children(node)`

Returns child nodes in sorted order.

Useful for rendering explorer UIs without each UI needing to understand the internal `children` map.

## Relationship Between `WidgetHandler` And `WidgetCatalog`

The clean mental model is:

- `WidgetHandler` answers: what widgets exist, are they enabled, and how do they run?
- `WidgetCatalog` answers: how should those discovered widgets be organized and queried for a UI?

So:

- use `WidgetHandler` for runtime actions
  - enable
  - disable
  - configure
  - pause
  - resume
- use `WidgetCatalog` for UI structure
  - build folder trees
  - show exact widget container folders
  - filter by text/path/category/tag
  - generate flat or tree views

## Why This Helps Alternate UIs

Without `WidgetCatalog`, each new widget UI would need to independently:

- rebuild tree structure from `widget_path`
- distinguish real `.widget` folders from intermediate folders
- derive categories and tags
- duplicate search/filter logic

With `WidgetCatalog`, a new UI can:

1. ask `WidgetHandler` for the discovered widgets
2. build a snapshot through `WidgetCatalog`
3. render that snapshot however it wants
4. send enable/disable/configure actions back to `WidgetHandler`

That gives a much better separation of concerns while keeping the actual widget runtime untouched.

## Current Test Script

The minimal test UI is:

- [`Py4GW_widget_catalog_test.py`](/Py4GW_widget_catalog_test.py)

It is intentionally small and exists to validate the catalog layer.

It currently shows:

- total discovered widgets
- exact widget container paths
- all expanded paths
- a tree view
- a flat list
- widget enable/disable checkboxes
- a debug dump button

It is not intended to replace the current widget manager UI.

## Recommended Usage Going Forward

If you want to build a true explorer-style widget UI, the intended flow is:

1. Use `WidgetHandler` to ensure discovery has happened
2. Build a `WidgetCatalogSnapshot`
3. Render folder nodes from `snapshot.tree`
4. Mark nodes with `is_widget_container` when needed
5. Render widgets from `widget_ids` at the appropriate node
6. Use `WidgetHandler` to perform enable/disable/configure actions

That keeps discovery and runtime behavior aligned with the existing system while making the UI layer much easier to evolve.
