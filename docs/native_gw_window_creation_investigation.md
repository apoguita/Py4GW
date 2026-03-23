# Native GW Window Creation Investigation

## Purpose
This note captures the current verified model for Guild Wars native UI window creation in the Python/C++ stack, separates it from the overlay/ImGui helper layer, and seeds the next REVA/Ghidra passes with a reusable function catalog instead of rediscovering the same targets each time.

This phase assumes:

- DevText is the only stable, proven native clone path.
- DevSound direct proc cloning is not safe yet and is comparison-only.
- New hook or callback targets must be proven in Python via pattern recovery before any C++ hook is trusted.

## Layer Map

### Layer 1: Native Guild Wars UI frame creation
Files:

- `Py4GWCoreLib/UIManager.py`
- `/Py4GW/include/py_ui.h`
- `/Py4GW/vendor/gwca/Source/UIMgr.cpp`

Role:

- Creates GW-managed frame subtrees under an existing parent frame.
- Uses native `GW::UI::CreateUIComponent(...)` callbacks and frame lifecycles.
- Applies frame rect/anchor data and requests redraw after creation.

Key public helpers in this layer:

- `UIManager.CreateWindow(...)`
- `UIManager.CreateWindowByFrameId(...)`
- `UIManager.CreateTextLabelFrameByFrameId(...)`
- `UIManager.CreateScrollableFrameByFrameId(...)`
- `UIManager.DestroyUIComponentByFrameId(...)`
- `UIManager.TriggerFrameRedrawByFrameId(...)`

### Layer 2: Recorded ImGui-style overlay builder
Files:

- `stubs/Py4GW/UI.pyi`
- `/Py4GW/src/Py4GW_UI.cpp`

Role:

- Records ImGui-style commands in C++ and replays them during render.
- Exposes helpers such as `begin`, `button`, `draw_list_add_rect_filled`, `python_callable`, `finalize`, and `render`.
- Does not create Guild Wars native windows or native GW frame subtrees.

Important consequence:

- `draw_list_add_rect_filled` belongs to the overlay-backed recorded UI layer.
- It is not evidence of any Guild Wars native rectangle, frame, or shell creation path.

## Native Creation Wrapper Chain
The current Python wrapper used by the proven DevText path is:

1. `UIManager.CreateWindow(...)` in `Py4GWCoreLib/UIManager.py`
2. `UIManager.CreateWindowByFrameId(...)` in `Py4GWCoreLib/UIManager.py`
3. `UIManager::CreateWindowByFrameId(...)` in `/Py4GW/include/py_ui.h`
4. `UIManager::CreateLabeledFrameByFrameId(...)` in `/Py4GW/include/py_ui.h`
5. `GW::UI::CreateUIComponent(...)` in `/Py4GW/vendor/gwca/Source/UIMgr.cpp`
6. `UIManager::SetFrameControllerAnchorMarginsByFrameIdEx(...)` in `/Py4GW/include/py_ui.h`
7. `UIManager::TriggerFrameRedrawByFrameId(...)` in `/Py4GW/include/py_ui.h`

### Verified wrapper behavior
What the wrapper guarantees:

- It resolves a callback if one is not supplied and DevText fallback is enabled.
- It finds an available child slot when `child_index == 0`.
- It creates a frame with the supplied parent, flags, callback, create param, and label.
- It applies rect/anchor margins after the frame is created.
- It triggers redraw after rect application.

What the wrapper does not guarantee:

- It does not construct shell/content by itself.
- It does not synthesize missing dialog-local runtime state.
- It does not bypass the callback's internal message lifecycle.
- It does not make unsafe procs safe to cold-create.

### Fact table
| Function | Inputs | Native action | Side effects | Failure conditions |
| --- | --- | --- | --- | --- |
| `UIManager.CreateWindow(...)` | desired rect, label, parent, callback, flags | resolves DevText proc when needed, chooses child slot, calls `CreateWindowByFrameId(...)` | may open/close DevText temporarily to resolve source proc | callback unresolved, no free child slot |
| `UIManager.CreateWindowByFrameId(...)` | parent id, child index, callback, rect | forwards to C++ `create_window_by_frame_id` | none in Python | native create failure |
| `UIManager::CreateLabeledFrameByFrameId(...)` | parent id, flags, child, callback, create param, label | calls `GW::UI::CreateUIComponent(...)` | callback becomes the native frame proc | parent missing or not created |
| `UIManager::CreateWindowByFrameId(...)` | same plus rect | creates frame, then sets anchor margins, then redraws | rect is applied after construction | create returns `0` |
| `GW::UI::CreateUIComponent(...)` | parent id, flags, child, callback, name/create param, label | creates native GW frame instance | starts callback-driven lifecycle | native callback/state invalid |
| `UIManager::SetFrameControllerAnchorMarginsByFrameIdEx(...)` | frame id, rect, flags | applies controller anchor margins | updates layout/placement | frame missing, pattern resolution failure |
| `UIManager::TriggerFrameRedrawByFrameId(...)` | frame id | requests native redraw | refresh after create or rect change | frame missing |

## Native Helper Families Already Exposed

### Generic callback-driven frame creation
Source:

- `GW::UI::CreateUIComponent(...)`
- `UIManager::CreateLabeledFrameByFrameId(...)`
- `UIManager::CreateWindowByFrameId(...)`

Properties:

- Fully generic.
- Works only if the callback is a valid runtime-usable native entry.
- Inherits all lifecycle assumptions of the chosen proc.

### Typed component helpers
Source:

- `UIManager.CreateTextLabelFrameByFrameId(...)`
- `UIManager.CreateScrollableFrameByFrameId(...)`
- `InitializeTypedComponentCallbacks()` in `/Py4GW/vendor/gwca/Source/UIMgr.cpp`

Properties:

- They recover typed callbacks by assertion/pattern-based lookup.
- They then call the same underlying generic creation path.
- They are a proven example of the correct philosophy: recover runtime-usable callbacks by pattern, not by static-address assumptions.

Implication for future work:

- If a future native shell-only builder exists, it will likely resemble a small, validated set of typed or semi-typed helper callbacks plus rect/redraw handling, not a blind call to an arbitrary dialog proc start address.

## Ghidra-to-Runtime Reconciliation Workflow
Before any new RE pass or hook candidate:

1. Check the seeded catalog in `docs/native_gw_ui_function_catalog.json`.
2. If the target already exists in Ghidra, record its static address and meaning first.
3. Decide whether the callable target is:
   - static function start
   - pattern-recovered runtime entry
   - validated alternate entry such as the previously observed `+0x30` case
4. Record the recovery method:
   - string xref plus `ToFunctionStart`
   - assertion/pattern lookup
   - caller-chain recovery
   - live runtime observation
5. Mark confidence:
   - `python_proven`
   - `runtime_observed`
   - `ghidra_inferred`
   - `unverified`

Rules:

- Never promote a Ghidra static address directly into a C++ hook target without a Python/runtime proof path.
- Never treat `static + slide` as sufficient on its own.
- Never hardcode `+0x30` as a rule; only record it when independently validated for that target.

## Current Window Family Comparison
| Dimension | DevText | DevSound |
| --- | --- | --- |
| Trusted clone status | Proven | Not proven |
| Dialog proc | `Ui_DevTextDialogProc` at `0x00864170` | `Ui_DevSoundDialogProc` at `0x00863700` |
| Cold create via `UIManager.CreateWindow(...)` | Stable | Crashes client |
| Message `9` role | Builds children directly and attaches handler/title | Calls structured content builder |
| Child creation shape | Repeated label + multiline controls | Fixed table of labels, sliders, value labels |
| Later refresh separation | Weak at constructor, better candidate later in multiline `0x37` | Stronger architectural separation via separate updaters |
| Best use right now | Baseline creation specimen | Comparison/reference specimen |

### DevText specifics already established
- `message 9` creates child `0` with `Ui_DevTextChildContainerProc`.
- It loops through repeated label control creation and multiline text control creation.
- It attaches a handler slot and sets root text to `DlgDevText`.
- Early suppression attempts at constructor time crash.
- Skipping `FUN_004BF910` crashes.
- Suppressing multiline leaf control `message 9` crashes.
- `Ui_MultiLineTextControlProc` `message 0x37` looks like a more promising post-create clear/rebuild boundary.

### DevSound specifics already established
- `message 9` delegates to `Ui_BuildDevSoundDialogContents(...)`.
- The dialog is more table-driven than DevText.
- It appears architecturally cleaner for shell/content separation.
- Direct proc instantiation still crashes, which strongly suggests missing dialog-open state or other external setup before the content builder runs.

## Candidate Suppression Boundaries
Ranked safest-first based on current evidence:

1. Later rebuild/update paths on already-created controls.
2. DevText multiline control rebuild path at `message 0x37`.
3. Family-specific refresh/update helpers that repopulate values or text after construction.
4. Dialog-level post-create refresh paths after shell creation is fully complete.
5. Constructor-time suppression inside dialog `message 9`.

Do not currently target:

- partial early returns from `Ui_DevTextDialogProc` `message 9`
- skipping required child/leaf initialization
- fake shell creation that omits required content-init helpers during first build

## Next REVA/Ghidra Passes
Keep batches small.

### Pass 1: Reconcile existing labeled functions against runtime-usable entries
For each current known DevText/DevSound function:

- confirm static address in Ghidra
- note whether a runtime-usable entry is separately known
- record the proof method
- note any caller-chain or alternate-entry nuance

Goal:

- remove ambiguity between "identified in Ghidra" and "safe callable runtime target"

### Pass 2: Caller/callee map around the two dialog procs
Focus:

- `Ui_DevTextDialogProc`
- `Ui_DevSoundDialogProc`

Questions:

- which helpers are shared scaffolding
- which helpers are family-specific content builders
- what runs before the first child create
- what runs after the last child create

### Pass 3: Shared helpers before and after child creation
Focus on helpers that look like:

- proc install/setup
- root title/name assignment
- child container creation
- handler list/callback attachment
- refresh or redraw signaling

Goal:

- isolate a common shell pattern that exists across both families

### Pass 4: Later rebuild/update boundaries
Focus:

- DevText multiline `message 0x37`
- DevSound updater/value refresh helpers

Goal:

- identify the earliest safe point where content can be minimized or cleared without invalidating initial construction

## Validation Checklist

### DevText baseline must remain true
- create succeeds
- frame exists by label
- move works
- resize works
- close destroys the frame

### DevSound must remain comparison-only unless disproven
- proc resolution path documented
- crash not blamed on wrapper chain without new evidence
- any future experiment must explain what missing state is being supplied

### Every new target must carry these tags
- static address
- runtime-usable address if known
- recovery method
- confidence level
- notes on alternate entry behavior if observed

## Current Conclusion
The current `CreateWindow(...)` path is a thin native construction wrapper, not a shell builder. It creates a frame, applies rect, and triggers redraw, but the chosen dialog proc remains responsible for its own lifecycle and required content setup. That is why DevText works only as a fully initialized native specimen and why DevSound can still crash despite using the same wrapper.

The most promising next direction is not constructor-time suppression. It is identifying a post-create rebuild/update boundary, while maintaining a disciplined Ghidra-to-runtime catalog so previously identified UI-process functions can be reused safely instead of rediscovered or miscalled.
