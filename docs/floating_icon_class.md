# FloatingIcon Class

## Purpose

`ImGui.FloatingIcon` is a small self-contained UI controller that displays a draggable floating icon and uses that icon as an on/off switch for a callable.

Its job is not to be a generic window manager. Its job is to:

- draw a floating icon
- let the user drag it around
- detect click versus drag
- toggle an internal enabled/visible state
- persist that functional toggle state across reloads
- call a supplied callback only while the toggle state is enabled

The class lives in [Py4GWCoreLib/ImGui_src/ImGuisrc.py]

## What The Class Owns

`FloatingIcon` owns the following runtime behavior:

- `position`
- dragging behavior
- click-to-toggle behavior
- internal `visible` state
- tooltip behavior
- calling `draw_callback()` only when enabled

It also owns the persistence of its functional toggle state through:

- `toggle_ini_key`
- `toggle_section`
- `toggle_var_name`
- `toggle_default`

This persistence is used only for the toggle state that decides whether the callback is executed.

## What The Class Does Not Need To Own Conceptually

Texture, button sizing, margins, and hover scale are appearance inputs, not the core functional identity of the class.

The class exposes those values as properties because it needs them to render itself, but the caller is free to decide:

- where those values come from
- where they are stored
- whether they are configurable in a setup window

For example, a caller may choose to load and save:

- `icon_path`
- `button_size`
- `idle_icon_scale`
- `hover_icon_scale`

from its own INI file.

## Constructor Parameters

Current constructor fields:

- `icon_path`: texture to draw
- `button_size`: base size of the icon button
- `idle_icon_scale`: icon scale when not hovered
- `hover_icon_scale`: icon scale when hovered
- `start_pos`: initial position before window config is restored
- `window_id`: unique id used for the hitbox
- `window_name`: ImGui window name for the floating button window
- `tooltip_visible`: tooltip shown when currently enabled
- `tooltip_hidden`: tooltip shown when currently disabled
- `drag_threshold`: distance before motion is treated as drag instead of click
- `visible`: internal toggle state controlling whether the callback executes
- `toggle_ini_key`: INI handler key used to persist the toggle state
- `toggle_section`: INI section for the toggle bool
- `toggle_var_name`: INI variable name for the toggle bool
- `toggle_default`: default toggle value if no persisted value exists
- `on_toggle`: optional callback invoked when the internal toggle changes
- `draw_callback`: callable executed only while the icon is enabled

## Core Methods

### `load_visibility()`

Loads the internal `visible` flag from `IniManager`.

Behavior:

- registers the boolean variable through `_ensure_visibility_var()`
- calls `IniManager().load_once(toggle_ini_key)`
- reads the persisted bool with `IniManager().get(...)`
- stores the result in `self.visible`

This is the functional persistence path for the class.

### `save_visibility()`

Writes the internal `visible` flag to `IniManager`.

Behavior:

- ensures the variable definition exists
- writes `self.visible` with `IniManager().set(...)`
- flushes it with `IniManager().save_vars(...)`

### `set_visible(value, persist=False, invoke_callback=False)`

Central helper for changing the toggle state.

Behavior:

- no-ops if the value is unchanged
- updates `self.visible`
- optionally persists the new value
- optionally invokes `on_toggle`

### `sync_begin_with_close(open_)`

Helper for callers whose driven window can also be closed from a normal ImGui close button.

If the controlled window is closed externally, the caller can push that new state back into `FloatingIcon` by calling this method.

This keeps the floating icon's internal toggle state synchronized with a driven window that supports close behavior.

### `draw(ini_key)`

This is the main runtime method.

Behavior:

1. Loads toggle state once if needed.
2. Creates a small floating ImGui window for the icon.
3. Lets `ImGui.Begin` and `ImGui.End` persist the floating window position, size, and collapsed state through the supplied `ini_key`.
4. Draws the icon texture.
5. Uses an invisible button as the interactive hitbox.
6. Distinguishes drag from click using `drag_threshold`.
7. Toggles `self.visible` on click and persists that toggle state.
8. Calls `draw_callback()` only if `self.visible` is `True`.

Important distinction:

- `toggle_ini_key` persists the functional on/off state
- `ini_key` in `draw()` persists the floating button window itself through `ImGui.Begin/End`

## Persistence Model

There are two different persistence concerns involved when using `FloatingIcon`.

### 1. Functional toggle persistence

Owned by `FloatingIcon`.

This controls whether the callback should execute after reload.

Stored through:

- `toggle_ini_key`
- `toggle_section`
- `toggle_var_name`

### 2. Floating window persistence

Handled by the normal ImGui window wrapper and `IniManager` window config flow.

This controls:

- floating button window position
- floating button window size
- collapsed state

Stored through:

- the `ini_key` passed to `draw()`

This comes from `ImGui.Begin` / `ImGui.End`, not from `save_visibility()`.

## How Drag And Click Work

The icon is rendered inside a small floating window. After drawing the image, the class places an invisible button over the icon area.

It then uses:

- `PyImGui.get_mouse_drag_delta(...)`
- `PyImGui.is_mouse_dragging(...)`
- `drag_threshold`

to determine whether the user is dragging or just clicking.

Rules:

- if movement exceeds the threshold, the interaction is treated as drag
- while dragging, the floating window position is updated
- on mouse release without drag, the class toggles `visible`

This is what makes the control usable as both a draggable floating button and a toggle.

## Caller Responsibilities

The caller is expected to provide the integration around the class.

The caller must decide:

- what callback should be controlled
- what INI key should store the floating button window position
- what INI key and variable should store the functional toggle state
- whether appearance values should be loaded and saved externally

In practice, a caller usually needs to do these things:

### 1. Construct the icon

Provide:

- icon texture
- tooltips
- callback to execute when enabled
- visibility persistence target

### 2. Provide a window-config INI key to `draw()`

The caller must pass an `ini_key` to `draw()` for the floating icon window itself.

That key is what lets `ImGui.Begin/End` restore and persist:

- floating icon position
- floating icon size
- collapsed state

### 3. Optionally own appearance persistence

If the caller wants to expose a setup window later, the caller should load and save appearance inputs itself, for example:

- `icon_path`
- `button_size`
- `idle_icon_scale`
- `hover_icon_scale`

The caller can write those values directly into the `FloatingIcon` instance before calling `draw()`.

### 4. Sync closeable driven windows if needed

If the callback draws a normal closeable window and that window can be closed independently, the caller should push the resulting close state back into the icon through:

- `sync_begin_with_close(open_)`

This keeps the floating icon's internal toggle state consistent with the controlled window.

## Minimal Usage Pattern

```python
floating_button = ImGui.FloatingIcon(
    icon_path="my_icon.png",
    window_name="My Floating Button",
    tooltip_visible="Hide UI",
    tooltip_hidden="Show UI",
    toggle_ini_key=my_toggle_ini_key,
    toggle_var_name="show_main_window",
    toggle_default=True,
    draw_callback=lambda: draw_my_window(),
)

# Caller-managed style loading, if desired
floating_button.icon_path = loaded_icon_path
floating_button.button_size = loaded_button_size
floating_button.idle_icon_scale = loaded_idle_scale
floating_button.hover_icon_scale = loaded_hover_scale

# Runtime draw
floating_button.draw(my_floating_window_ini_key)
```

## Design Summary

`FloatingIcon` is best understood as a floating toggle controller for code execution.

It owns:

- its drag behavior
- its internal on/off state
- persistence of that on/off state
- the decision to call or not call the supplied callback

The caller owns:

- styling decisions
- optional appearance persistence
- setup UI
- broader application behavior around the controlled window

That separation keeps the class focused on its actual purpose while still making it easy for callers to customize how the icon looks.
