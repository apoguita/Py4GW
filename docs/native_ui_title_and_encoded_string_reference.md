# Native UI Title And Encoded String Reference

## Purpose
This note captures the current working model for Guild Wars native window titles, text-label encoded strings, and the Python/C++ bridge paths that manipulate them. It is meant to be a durable handoff for future reverse-engineering and cleanup work.

The emphasis here is on:

- how composite window titles are really built in `Gw.exe`
- how text-label encoded strings are constructed and validated
- how the current C++ bridge exposes those paths
- how the Python `GWUI` facade maps to the native layer

---

## Environment Overview

### Python workspace
Path:

- `C:\Users\Apo\Py4GW_python_files`

Main files involved in this session:

- [Py4GWCoreLib/GWUI.py](C:\Users\Apo\Py4GW_python_files\Py4GWCoreLib\GWUI.py)
- [Py4GWCoreLib/UIManager.py](C:\Users\Apo\Py4GW_python_files\Py4GWCoreLib\UIManager.py)
- [window_title_probe_test.py](C:\Users\Apo\Py4GW_python_files\window_title_probe_test.py)

Current role split:

- `GWUI.py` is the intended Python-facing UI API for construction, mutation, titles, rects, and text-label work.
- `UIManager.py` should remain the low-level Python/native bridge surface.
- Experimental and test scaffolding still exists, but the code is now organized enough to reason about ownership.

### Native C++ workspace
Path:

- `C:\Users\Apo\Py4GW`

Main files involved in this session:

- [include/py_ui.h](C:\Users\Apo\Py4GW\include\py_ui.h)
- [src/py_ui.cpp](C:\Users\Apo\Py4GW\src\py_ui.cpp)
- [CMakeLists.txt](C:\Users\Apo\Py4GW\CMakeLists.txt)

Important build note:

- this module is 32-bit
- preferred configure command is `cmake -B build -A Win32`

The project was also updated to use `CONFIGURE_DEPENDS` in `CMakeLists.txt` so file additions/removals are tracked more reliably when the source/header glob changes.

---

## Python To Native Layer Map

The current stack is:

1. Python caller
2. `GWUI.py`
3. embedded `PyUIManager.UIManager` bindings
4. `UIManager` in `py_ui.h`
5. GWCA / native Guild Wars UI functions

Practical meaning:

- `GWUI` is where higher-level Python scripts should live
- `UIManager` in C++ is the reverse-engineered primitive layer
- if a behavior depends on exact game-native semantics, the real implementation is in `py_ui.h`, not in `GWUI.py`

Examples:

- `GWUI.SetFrameTitleByFrameId(...)` maps to `UIManager::SetFrameTitleByFrameId(...)`
- `GWUI.SetNextCreatedWindowTitle(...)` maps to `UIManager::SetNextCreatedWindowTitle(...)`
- `GWUI.CreateWindow(...)` maps to `UIManager::CreateWindowClone(...)`
- `GWUI.CreateTextLabelFrameWithPlainTextByFrameId(...)` maps to `UIManager::CreateTextLabelFrameWithPlainTextByFrameId(...)`

---

## Current Title System Model

## High-level conclusion
Guild Wars composite window titles are not a single string source.

There are two relevant caption channels:

1. dynamic text caption
2. resource-backed caption

Changing only the first one explains the observed partial success:

- the user could add or replace some visible title text
- but the original title was still partially present

That behavior matches the game reading from both caption channels during composite title rendering.

## Native routines identified

The most relevant functions discovered in `Gw.exe` are:

- `Ui_CreateEncodedText`
- `Ui_SetFrameText`
- `Ui_SetFrameEncodedTextResource`
- `Ui_GetFrameResourceCaptionText`
- `Ui_GetFrameTextCaptionText`
- `Ui_PostBuildSetFrameTitleAndResource`
- `Ui_BuildCompositeWindowThenSetTitle`
- `Ui_DevTextDialogProc`

## DevText specimen path

`Ui_DevTextDialogProc` is the proven stable specimen path used for clone-based creation.

Observed behavior:

- it creates an encoded text payload using `Ui_CreateEncodedText`
- it assigns that payload with `Ui_SetFrameText`

This proved two important things:

1. title text can be created dynamically
2. there is a native, reproducible title-building path that can be intercepted

## Why direct title setting was only partially successful

The direct setter path exposed in C++:

- creates an encoded text payload
- calls `Ui_SetFrameText`

That affects the dynamic text-caption channel only.

However, composite title rendering can also consult:

- `Ui_GetFrameResourceCaptionText(frame)`

If the resource-caption remains present, the visible title can still include the original resource-backed name even after the dynamic title text has been changed.

That is why:

- `SetFrameTitleByFrameId(...)` is useful
- but it is not sufficient for guaranteed full composite title replacement

## Post-build title setup in `Gw.exe`

One of the important discoveries was that native title assignment is sometimes a two-step operation, not a single `SetFrameText(...)` call.

`Ui_PostBuildSetFrameTitleAndResource` performs:

1. `Ui_SetFrameText(frame, payload)`
2. conditional `Ui_SetFrameEncodedTextResource(frame, resource_ptr)`

That is the exact reason clone-time interception had to expand from:

- `Ui_CreateEncodedText`
- `Ui_SetFrameText`

to also include:

- `Ui_SetFrameEncodedTextResource`

---

## Current Clone-Time Title Override Design

## Final design choice
The session compared two possible approaches:

1. expose `Ui_SetFrameEncodedTextResource(frame, resource_ptr)` directly
2. hook `Ui_SetFrameEncodedTextResource` during clone creation, the same way `Ui_SetFrameText` was already being hooked

The chosen path was the second one.

Reasons:

- raw `resource_ptr` is unsafe and opaque
- exposing the setter alone does not solve how to obtain/build a valid resource pointer
- clone-time hook behavior is scoped to the exact native path being tested
- it solves the real rename problem without opening a very dangerous public API

## Current hook location

The hook logic used to live in standalone files:

- `window_title_hook.h`
- `window_title_hook.cpp`

It was migrated into:

- [include/py_ui.h](C:\Users\Apo\Py4GW\include\py_ui.h)

under:

- `namespace UIManagerTitleHook`

That namespace now owns:

- pending title override state
- hook install state
- last-applied title/frame bookkeeping
- native function scanning
- interception logic for title creation and attachment

## What is currently intercepted

The clone-time title override path now intercepts:

- `Ui_CreateEncodedText`
- `Ui_SetFrameText`
- `Ui_SetFrameEncodedTextResource`

Behavior summary:

1. Python arms a pending title override for the next created DevText-backed clone.
2. Clone creation begins.
3. When the DevText title string is created, the hook substitutes the requested title.
4. When the dynamic title text is attached, the frame id is recorded.
5. When the resource-caption would be attached, the hook suppresses it for that armed creation.

This is the current best model for full title replacement on cloned windows.

## Public native API exposed for titles

Current native-facing title methods:

- `SetFrameTitleByFrameId(...)`
- `SetNextCreatedWindowTitle(...)`
- `ClearNextCreatedWindowTitle()`
- `HasNextCreatedWindowTitle()`
- `IsWindowTitleHookInstalled()`
- `GetLastAppliedWindowTitleFrameId()`
- `GetLastAppliedWindowTitle()`

Operational distinction:

- `SetFrameTitleByFrameId(...)` is a post-create dynamic text-caption setter
- `SetNextCreatedWindowTitle(...)` is the clone-time full override path for DevText-backed creations

---

## Encoded String Model For Text Labels

## Core conclusion
Guild Wars text labels do not primarily operate on plain text.

They operate on encoded wide-string payloads containing:

- literal text control markers
- escape handling
- terminators
- possibly other pre-existing encoded markup from the game

The important practical consequence is:

- writing a plain Python string directly is not the same as constructing a valid GW encoded string payload

## Native helpers involved

Current native helpers related to text labels include:

- `GetTextLabelEncodedByFrameId(...)`
- `GetTextLabelEncodedBytesByFrameId(...)`
- `GetTextLabelDecodedByFrameId(...)`
- `SetTextLabelByFrameId(...)`
- `SetTextLabelBytesByFrameId(...)`
- `AppendTextLabelEncodedSuffixByFrameId(...)`
- `AppendTextLabelPlainSuffixByFrameId(...)`
- `BuildStandaloneLiteralEncodedTextPayload(...)`
- `CreateTextLabelFrameByFrameId(...)`
- `CreateTextLabelFrameWithPlainTextByFrameId(...)`
- `CreateTextLabelFrameFromTemplateByFrameId(...)`
- `GetTextLabelCreatePayloadDiagnosticsByTemplateFrameId(...)`
- `GetTextLabelLiteralCreatePayloadDiagnostics(...)`

These are implemented in `py_ui.h` and wrapped in `GWUI.py`.

## Literal plain-text payload structure

The key builder is:

- `BuildStandaloneLiteralEncodedTextPayload(const std::wstring& plain_text)`

Its current structure is:

1. prepend `0x0108`
2. prepend `0x0107`
3. copy plain text, escaping reserved characters
4. append `0x0001`

Reserved characters currently escaped:

- `[` -> `\[`
- `]` -> `\]`
- `\` -> `\\`

This means a literal plain-text payload is not just:

- `"hello"`

It is structurally closer to:

- literal-text-open marker
- escaped character stream
- literal-text-close marker

## Appending plain text to existing encoded labels

The append path is slightly different.

`AppendTextLabelPlainSuffixByFrameId(...)` builds:

1. existing encoded payload
2. `0x0002`
3. `0x0108`
4. `0x0107`
5. escaped plain text
6. `0x0001`

This strongly suggests:

- `0x0108 0x0107 ... 0x0001` is the literal-text encoded block
- `0x0002` is a separator/control opcode used when appending another encoded segment

This is one of the most useful discoveries from the session because it explains why direct concatenation of plain text into encoded labels is not safe.

## Encoded vs decoded views

There are three distinct representations to keep in mind:

1. encoded payload as a `wstring`
2. encoded payload as raw wchar bytes
3. decoded rendered text

Current helpers by layer:

- encoded `wstring`: `GetTextLabelEncodedByFrameId(...)`
- encoded raw bytes: `GetTextLabelEncodedBytesByFrameId(...)`
- decoded visible text: `GetTextLabelDecodedByFrameId(...)`

These are not interchangeable.

For debugging:

- if the structure is wrong, the encoded payload can still exist but fail validation
- decoded text is useful for sanity checks, but it hides the control markers
- raw bytes are the most exact representation when validating payload construction

## Raw bytes path

`SetTextLabelBytesByFrameId(...)` and `GetTextLabelEncodedBytesByFrameId(...)` are especially important because they allow exact round-tripping of the encoded wchar payload.

Current native validation in `SetTextLabelBytesByFrameId(...)`:

- payload must not be empty
- byte length must be divisible by `sizeof(wchar_t)`
- final wchar must be `0x0000`

That gives a clean way to compare:

- exact constructed payload
- exact native payload
- exact bytes passed from Python

## Template-derived payloads

Some text labels are safer to build from a native template than to construct from scratch.

`CreateTextLabelFrameFromTemplateByFrameId(...)` does this:

1. reads the template frame's current encoded label
2. copies that encoded payload
3. optionally appends a literal-text suffix
4. uses the result as the new encoded payload

This matters because some native labels may contain:

- non-literal encoded content
- formatting markers
- resource-derived content
- control codes not yet fully documented

The template-derived path preserves the original game-generated structure instead of replacing it with a guessed payload.

## Diagnostic helpers

Two diagnostic helpers were added to make payload formation inspectable from Python:

- `GetTextLabelCreatePayloadDiagnosticsByTemplateFrameId(...)`
- `GetTextLabelLiteralCreatePayloadDiagnostics(...)`

They report:

- template existence
- template-created status
- template encoded text
- constructed encoded text
- `GW::UI::IsValidEncStr(...)` result
- decoded text produced via `GW::UI::AsyncDecodeStr(...)`

These are scaffolding/diagnostic helpers rather than final public API, but they are currently valuable because they make encoded-string experimentation observable.

## Practical encoded-string rules learned this session

1. Plain text should not be treated as a final label payload.
2. Literal text insertion requires encoded wrapper markers.
3. Appending plain text to an existing encoded payload uses a separator/control marker first.
4. Escaping of `[`, `]`, and `\` currently matters.
5. Raw bytes matter when validating payload correctness.
6. Template-based derivation is often safer than full reconstruction.
7. Decoded text is helpful for verification but does not show the actual payload structure.

---

## Current Native Window Creation Model

The stable clone path still depends on DevText.

Relevant helpers:

- `ResolveDevTextDialogProc()`
- `EnsureDevTextSource()`
- `OpenDevTextWindow()`
- `GetDevTextFrameID()`
- `RestoreDevTextSource(...)`
- `CreateWindowClone(...)`
- `CreateEmptyWindowClone(...)`
- `ClearWindowContentsByFrameId(...)`

Current understanding:

1. DevText is the proven specimen window.
2. Cloned native windows reuse that dialog-proc path.
3. The wrapper can open DevText temporarily if needed.
4. Window creation resolves a child slot, creates a labeled frame, applies anchor margins, and redraws.
5. Empty-window creation is currently just clone-plus-clear-content.

The creation wrapper does not itself synthesize all dialog-local runtime state. It relies on the specimen proc and native lifecycle remaining compatible.

---

## Python Testing Surface Added This Session

New test harness:

- [window_title_probe_test.py](C:\Users\Apo\Py4GW_python_files\window_title_probe_test.py)

Purpose:

- compare clone-time title override vs direct text-caption replacement
- record hook status and last-applied frame/title
- make title behavior observable without reusing a larger, more cluttered legacy script

UI actions:

- `Create Window`
- `Create With Override`
- `Apply Direct Title`
- `Snapshot`
- `Destroy Window`

Interpretation:

- `Create With Override` exercises the full clone-time override path
- `Apply Direct Title` exercises the post-create `SetFrameText`-only path

This script should be the first runtime validation harness to use when continuing title work.

---

## Documentation And Codebase Improvements Made

### Python organization

- `GWUI` now owns the Python-side UI mutation and construction surface
- circular compatibility wrappers in `UIManager.py` were removed

### Native title hook integration

- standalone `window_title_hook` files were removed
- hook logic was moved into `py_ui.h`
- resource-caption suppression was added to the hook path

### Native code commentary

`py_ui.h` and `py_ui.cpp` now contain per-function commentary explaining:

- frame lookup helpers
- message dispatch
- clone creation helpers
- title behavior
- encoded text-label helpers
- preferences, keyboard, and window-state helpers

---

## Current Risks And Open Questions

1. The title override logic is compile-verified, but runtime behavior still needs in-client confirmation after the latest changes.
2. DevText remains the only clearly stable specimen path for clone-backed native windows.
3. Some `GWUI` helpers are still experimental/test-oriented and should later be separated from stable API.
4. The encoded string model is much clearer now, but not every control code has been cataloged.
5. There may still be additional post-build title paths in `Gw.exe` beyond the currently hooked DevText-derived route.

---

## Recommended Next Steps

1. Run `window_title_probe_test.py` in-client and compare:
- clone-time override result
- direct title-set result

2. If any original title text still survives after clone-time override:
- inspect whether another resource/title path is invoked after the current hook point
- compare call sites against the DevText-derived return addresses already used

3. Continue splitting `GWUI` into:
- stable public API
- experimental/DevText-specific helpers
- removable diagnostics and test scaffolding

4. If stronger native documentation is needed:
- convert the current per-function comments in `py_ui.h` to Doxygen-style comments
- preserve this note as the high-level conceptual reference

