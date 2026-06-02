# Native GW Window Creation Investigation

## Purpose
This note captures the current verified model for Guild Wars native UI window creation in the Python/C++ stack, separates it from the overlay/ImGui helper layer, and seeds the next REVA/Ghidra passes with a reusable function catalog instead of rediscovering the same targets each time.

This phase assumes:

- `Gw.wasm` is the semantic source of truth for UI creation flow and symbol identity.
- The stripped/symbol EXE remains the runtime body that C++ must actually call or hook.
- `docs/CPP_WASM_MAPPING.md` is the required bridge workflow when promoting WASM findings into C++.
- DevText is still the only clearly proven clone-backed native path, but it is no longer the primary design target for an empty reusable window shell.
- DevSound direct proc cloning is not safe yet and is comparison-only.
- New hook or callback targets must be proven in Python via pattern recovery before any C++ hook is trusted.

## Source-of-Truth Update

The earlier working model in this note leaned too heavily on DevText as the practical specimen path.
That remains useful for proving callback-driven creation, but it is not the cleanest target for the actual goal.

The current goal is narrower and more architectural:

- identify a native Guild Wars window/container shell that is:
  - titled
  - resizable
  - capable of hosting child UI elements
  - as empty or suppressible as possible

That means the primary RE path now starts in `Gw.wasm`, then bridges back to the EXE and finally to C++.

## WASM-First Findings

### 1. Generic frame creation is not enough by itself

Named WASM symbol:

- `FrameCreate(unsigned int, unsigned int, unsigned int, void (*)(FrameMsgHdr const&, void const*, void*), void const*, wchar_t const*)`

This is the low-level frame constructor. It allocates the frame object, installs the callback, emits lifecycle notifications, and dispatches initial messages.

Important limitation:

- `FrameCreate(...)` alone does not produce a complete floating game window shell.
- Higher-level callers still perform title wiring, subclassing, placement, visibility, and other policy setup.

### 2. The real floating-window factory is `IUi::Game::DialogShow(...)`

Named WASM symbol:

- `IUi::Game::DialogShow(unsigned int, IUi::Game::EFloatingDialog, int, void const*)`

This is the real floating-dialog/window creation pipeline currently visible in `Gw.wasm`.

Recovered responsibilities from the decompile/callee map:

- resolves a floating-dialog descriptor record
- destroys or reuses any existing instance in the target child slot
- calls `FrameCreate(...)`
- enables gamepad behavior
- may show and activate the frame
- installs a subclass with `FrameNewSubclass(...)`
- sets title and optional hotkey title text
- calls `FramePlaceChildren(..., L"GmView-Dialog")`
- restores saved window position from preferences
- applies width, height, and layer policy in some cases

Implication:

- The clean empty-window target should be modeled as a window-shell problem, not just a callback-clone problem.
- Any C++ path that wants arbitrary native windows should account for the `DialogShow(...)` contract, not just `CreateUIComponent(...)` or `FrameCreate(...)` in isolation.

### 3. DevText is a valid specimen but not the best shell target

Named WASM symbols:

- `IUi::DlgDevTextProc(FrameMsgHdr const&, void const*, void*)`
- `IUi::NDlgDevText::CTextDialogFrame::OnCreate(unsigned int)`

Current model:

- `IUi::DlgDevTextProc(...)` is a thin dispatcher.
- On `message 9`, it forwards into `CTextDialogFrame::OnCreate(...)`.
- `OnCreate(...)` performs eager content creation for the debug text window.

Implication:

- DevText still proves that native window creation is callback-driven.
- It is not the cleanest specimen for a reusable empty shell because its payload content is tightly coupled to first construction.

### 4. Inventory aggregate is a better empty-shell candidate

Named WASM symbols:

- `IUi::Game::InventoryAggregateFrameProc(FrameMsgHdr const&, void const*, void*)`
- `IUi::Game::Inventory::CAggregateInv::FrameProc(FrameMsgHdr const&, void const*, void*)`
- `IUi::Game::Inventory::CAggregateInv::OnFrameCreate(FrameMsgCreate const&)`
- `IUi::Game::Inventory::CAggregateInv::OnFrameSize(FrameMsgSize const&)`
- `IUi::Game::Inventory::CAggregateInv::OnFrameSizeQuery(FrameMsgSizeQuery const&)`
- `IUi::Game::Inventory::CAggregateInv::UpdateBags()`

This family currently looks like the cleanest titled/resizable native container specimen discovered so far.

#### `CAggregateInv::OnFrameCreate(...)`

Observed responsibilities:

- enables mouse on the root frame
- enables gamepad on the root frame
- creates child `0` as the main hosted view/list frame
- configures view increment and page behavior on child `0`
- installs size and size-query handlers on child `0`
- sets min and max size on the root
- registers multiple frame messages on the root
- only then calls `UpdateBags()`

This is the key architectural difference versus DevText:

- shell/container setup happens first
- payload population happens later in a distinct function

#### `CAggregateInv::OnFrameSize(...)`

Observed responsibilities:

- retrieves child `0`
- repositions child `0` within the resized root

#### `CAggregateInv::OnFrameSizeQuery(...)`

Observed responsibilities:

- retrieves child `0`
- queries child `0` for native size
- propagates that size upward

#### `CAggregateInv::UpdateBags()`

Observed responsibilities:

- retrieves child `0`
- clears the frame list
- reads inventory/bag visibility prefs
- resolves bag ids
- creates list items for bag slots

This is the payload population step, not the shell setup step.

Implication:

- If the objective is an empty native resizable container, `CAggregateInv` is a stronger target than DevText.
- The most promising path is to preserve the shell/root/content-host setup while suppressing or replacing `UpdateBags()`.

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
| Dimension | DevText | DevSound | Inventory Aggregate |
| --- | --- | --- | --- |
| Primary role | Debug text window | Debug sound window | Real game inventory aggregate window |
| Trusted create status | Proven clone-backed specimen | Not proven for direct proc create | Promising WASM shell specimen |
| Core proc model | Thin proc -> eager `OnCreate` payload build | Proc -> structured content builder | Proc/class shell setup -> later `UpdateBags()` payload build |
| Resize support | Present but content-heavy | Present | Explicit `OnFrameSize` and `OnFrameSizeQuery` |
| Child host setup | Mixed into constructor-time content build | Mixed with dialog build path | Explicit child `0` host created before payload fill |
| Best use right now | callback-driven creation reference | comparison/reference specimen | best current candidate for an empty titled resizable host |

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

1. Inventory-family payload refresh/population helpers such as `CAggregateInv::UpdateBags()` after shell setup is complete.
2. Later rebuild/update paths on already-created controls.
3. DevText multiline control rebuild path at `message 0x37`.
4. Family-specific refresh/update helpers that repopulate values or text after construction.
5. Dialog-level post-create refresh paths after shell creation is fully complete.
6. Constructor-time suppression inside dialog `message 9`.

Do not currently target:

- partial early returns from `Ui_DevTextDialogProc` `message 9`
- skipping required child/leaf initialization
- fake shell creation that omits required content-init helpers during first build

## Next REVA/Ghidra Passes
Keep batches small.

### Pass 1: Reconcile named WASM shell targets against runtime-usable EXE entries
For each current known shell candidate:

- confirm static address in Ghidra
- note whether a runtime-usable entry is separately known
- record the proof method
- note any caller-chain or alternate-entry nuance

Goal:

- remove ambiguity between "identified in `Gw.wasm`" and "safe callable runtime EXE target"

### Pass 2: Dialog/window factory map around `DialogShow(...)`
Focus:

- `IUi::Game::DialogShow(...)`
- the floating-dialog descriptor table it indexes

Questions:

- which fields define proc, title, flags, pref window, and subclass policy
- which helpers are generic shell scaffolding
- which helpers are payload-specific

### Pass 3: Inventory aggregate shell isolation
Focus:

- `CAggregateInv::OnFrameCreate(...)`
- `CAggregateInv::OnFrameSize(...)`
- `CAggregateInv::OnFrameSizeQuery(...)`
- `CAggregateInv::UpdateBags()`

Goal:

- determine whether the root plus child `0` host can survive without `UpdateBags()`

### Pass 4: EXE bridge promotion via `CPP_WASM_MAPPING.md`
Focus:

- string/file anchors from WASM inventory symbols
- corresponding EXE xrefs and caller chains
- final scanner/pattern strategy for C++

Goal:

- promote the WASM-derived shell target into a verified EXE/C++ call path

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

## Current Conclusion (Updated 2026-05-31)

### ✅ REGRESSION FIXED (2026-05-31)

**Root cause**: The `ResolveCompositeRootControlProc` byte-pattern scan failed because the EXE was patched on 2026-05-30. The CRProc stack frame changed from `SUB ESP, 0x11C` to `SUB ESP, 0x120` (prologue bytes: `55 8B EC 81 EC 20 01 00 00`). The old Ghidra analysis was stale. Additionally, `FindAssertion` with a non-zero line number fails due to PUSH instruction encoding mismatch in the scanner algorithm.

**Fix**: Replace byte-pattern-only resolution with a two-layer strategy:
1. **Primary**: `FindAssertion("UiCtlDlg.cpp", "!s_imgList", 0, 0)` — string-based, portable across patches
2. **Fallback**: Byte-pattern `\x81\xEC\x20\x01\x00\x00...` with 24-char mask and prologue validation

No hardcoded addresses. Runtime base differs from Ghidra static `0x00400000` — all resolution must use runtime-safe patterns.

**Proven resolution** (from Python diagnostic):
```
Scanner.FindAssertion("UiCtlDlg.cpp", "!s_imgList", 0, 0) → 0x00EB697B
Scanner.ToFunctionStart(assertion, 0x110) → 0x00EB6880 (CRProc)
```
Runtime slide: `0x00EB6880 - 0x00851180 = 0x00665600` (EXE loaded at non-standard base).

### Working (Current — 2026-05-31)
1. **`CreateContainerWindow()`** (existing GWCA) creates a bare `CContainerFrame` — works.
2. **`FrameNewSubclass(frame, Ui_CompositeRootControlProc, 0x59)`** — works via `FindAssertion` resolution.
3. **Mouse interaction**: `FrameMouseEnable(frame, 0xFFFFFFFF, 0)` after `FrameNewSubclass`.
4. **Python-only window creation**: Proven — CRProc resolved via Scanner + NativeFunction, chrome installed with `directCall()` on game thread.

### Resolution Method (Canonical)

| Function | Method | Parameters |
|----------|--------|------------|
| `Ui_CompositeRootControlProc` | `FindAssertion` | `("UiCtlDlg.cpp", "!s_imgList", 0, 0)` |
| `CContainerFrame::FrameProc` | `FindAssertion` | `("UiPlacementContainer.cpp", "itemFrame", 0x43, 0)` |
| `FrameNewSubclass` | `FindAssertion` | `("FrApi.cpp", "frameId", 0x467, 0)` |
| `FrameMouseEnable` | `FindAssertion` | `("FrApi.cpp", "frameId", 0x540, 0)` |

### ⚠️ REGRESSION (2026-05-31 — Old)

**An unauthorized `git checkout` reverted all uncommitted working-tree changes for py_ui.h**, losing the proven mouse-fix code. The functions were reconstructed from documentation but had incorrect byte patterns (stale Ghidra data) and wrong line numbers for FindAssertion. See `docs/RE/title_rendering_research.md` for full regression details.

### Working (Before Regression — 2026-05-30)
1. **`CreateContainerWindow()`** (existing GWCA) creates a bare `CContainerFrame` with no content, no chrome — cold-startable with no state dependencies.
2. **`FrameNewSubclass(frame, Ui_CompositeRootControlProc, 0x59)`** (exposed via `ResolveFrameNewSubclass`) installs the window chrome — title bar, close button, resize handles.
3. **Mouse interaction**: Fixed via `FrameMouseEnable(frame, 0xFFFFFFFF, 0)` called AFTER `FrameNewSubclass`. `CContainerFrame::FrameProc` clears CMouse flags (`frame+0x98`) to 0 on msg 9 (twice: during FrameCreate and forwarded via `Ui_DispatchToFrameHierarchy` in CRProc). `FrameMouseEnable` (= `Ui_UpdateFrameFlagMaskById` at EXE `0x0060ffd0`) restores all flags. Function resolvable via `FindAssertion("FrApi.cpp", "frameId", 0x540, 0)` with byte-pattern fallback.

### NOT Working (Fundamental Issue — Unresolved)
4. **Title/caption text**: Text IS stored correctly (`SetFrameTitleByFrameId` returns ok=True), but the CRProc's msg 0x08 handler never renders it. Root cause identified: `Ui_SetFrameText` stores text in the attached-text table but invalidation goes to a GLOBAL context (not the frame-specific CContent). The frame is never enqueued into the per-frame CContent dirty linked list (`DAT_ram_005a02f8`), so the paint loop never dispatches msg 0x08. See `docs/RE/title_rendering_research.md` for comprehensive analysis.

### Title Rendering Pipeline (2026-05-31 Findings)

The title rendering chain has 4 requirements:
1. ✅ Text stored via `Ui_SetFrameText` → attached-text table (Path B)
2. ✅ CRProc installed on frame via `FrameNewSubclass`
3. ❌ **CContent element 4 invalidation + per-frame dirty list enqueue** — MISSING
4. ✅ Frame shown via GWCA `ShowFrame` or native `Ui_ShowFrame`

Step 3 requires `CContent::Invalidate(frame+4, element=4, flags=0xFFFFFFFF)` which both sets the paint mask AND enqueues the frame into the per-frame dirty linked list. `Ui_SetFrameText` uses `Ui_QueueGlobalUiUpdate` which writes to the GLOBAL context (`DAT_00bb55e0`), not the frame-specific CContent.

The only native path that performs per-frame CContent invalidation is `CNonclient::OnTitleResolved`, which is triggered by `CNonclient::SetTitle` during `FrameCreate`. DevText clones get this automatically; cold-created containers do not.

### Proven Portable Patterns (No Absolute Addresses)

| Function | Method | Parameters |
|----------|--------|------------|
| `Ui_CompositeRootControlProc` | `FindAssertion` | `("UiCtlDlg.cpp", "!s_imgList", 0, 0)` |
| `Ui_CreateEncodedText` | `Find` | `\x55\x8B\xEC\x51\x56\x57\xE8\x00\x00\x00\x00\x8B\x48\x18\xE8\x00\x00\x00\x00\x8B\xF8` / `xxxxxxx????xxxx????xx` |
| `Ui_SetFrameText` | `Find` | `\x55\x8B\xEC\x53\x56\x57\x8B\x7D\x08\x8B\xF7\xF7\xDE\x1B\xF6\x85` / `xxxxxxxxxxxxxxxx` |
| `FrameMouseEnable` | `FindAssertion` | `("FrApi.cpp", "frameId", 0x540, 0)` |
| `FrameNewSubclass` | `FindAssertion` | `("FrApi.cpp", "frameId", 0x467, 0)` |
| `CContainerFrame::FrameProc` | `FindAssertion` | `("UiPlacementContainer.cpp", "itemFrame", 0x43, 0)` |

**IMPORTANT**: Byte-pattern scans on function prologues are fragile across EXE patches (e.g., stack frame size can change: `0x11C`→`0x120`). **Always prefer `FindAssertion` as the primary strategy**. Byte patterns should only be fallbacks.

### Known Issues

- **`[X]` close button**: Works — handled by CNonclient framework, not msg 0x0A.
- **Mouse interaction**: Works — fixed via `FrameMouseEnable(0xFFFFFFFF, 0)` after `FrameNewSubclass`.
- **Title rendering**: NOT WORKING — ongoing. Text stored but paint mask bit 8 never set. See `docs/RE/title_rendering_research.md`.
- **Byte pattern fragility**: Byte patterns encoding stack frame sizes break across EXE patches. `FindAssertion` is immune. The 2026-05-30 EXE patch changed CRProc from `SUB ESP, 0x11C` to `SUB ESP, 0x120`, breaking all byte-pattern-based resolution.
