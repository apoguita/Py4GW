# Native UI Controls — HANDOVER

Last updated: 2026-07-01 | EXE build: **06-14-2026** (Ghidra program `/Gw.exe (06-14)`, base 0x00400000)

> **Read this first.** It is the honest state-of-the-world for creating native Guild Wars UI controls in
> Py4GW: what works, what doesn't, the decompiled root causes, the fixes that stuck, the dead-ends that
> were reverted (so you don't repeat them), and the open problems. Detailed references are cross-linked.

---

## 0. 2026-07-01 SESSION — definitive findings & the path forward (READ BEFORE CODING)

**The definitive answer (high confidence, from a 7-window WASM-first comparison — full spec in
`docs/RE/native_dialog_layout_process.md`, memory `native-dialog-layout-pass`):** the complex interactive
controls (styled **checkbox / slider / edit / droplist**) work in exactly ONE native archetype and NO other:
the **instanced-dialog + direct-child + `CCtlLayout`** pattern (as in `CDlgOptGeneral`, `CDlgOptionSound`,
`CDlgGraphics`, `CDlgGamepad`, the confirmation dialog). The frame-list-item archetype (DevText,
`add_control_item`) is native but safe ONLY for **non-interactive text/button rows**. Every native
control-hosting window shares these **8 setup phases**: (1) create frame with a class `MsgProc`; (2) alloc the
dialog C++ instance into the frame userdata (`frame[2]`), parent = `*(instance+4)`; (3) dispatch to
`OnFrameCreate`; (4) create controls (per-type proc+style); (5) seed values crash-safe (slider range `0x56`
BEFORE value `0x57`; droplist add-then-select; checkbox `CtlBtnCheck`); (6) **`CCtlLayout` size pass**
(msg `0x38` SizeQuery / `0x37` Size); (7) chain leftovers to `IUi::FrameMsgCallBase`; (8) chrome
`IUi::UiCtlDlgProc` flags `0x59`, teardown via msg `0xb → IUi::PopCloser → recursive FrameDestroy`, freeing
the instance. **The 3 pieces Py4GW lacks:** (a) an owning `TCtlInstance` object in `frame[2]`, (b) an embedded
`CCtlLayout` + `SetFrameId`, (c) the size pass. **The one thing to author:** a Py4GW C++ `MsgProc` dispatcher
(the engine calls it) that owns the instance+`CCtlLayout` lifecycle and runs the size pass.

**In-client verified matrix (what actually works / fails, and every hosting tried):**
- ✅ **button** works everywhere (simple self-contained `CtlBtnProc`). ✅ **progress**, ✅ **group header** work.
- ✅ **checkbox glyph** fixed: flags `0x48300`→`0x18000` (the `0x40000` bit was forcing the button face). It now
  renders the correct texture and toggles **as a plain direct child of a normal window** — its ONLY remaining
  failure there is the native `[X]` teardown crash.
- ✅ **hyperlink click** fixed in `GWUI.py` (unique nonzero per-row child codes).
- ❌ Complex controls in every AD-HOC host tried (all crash/blank): `UiCtlContentPageProc` content page
  (crashes — half-initialized standalone); plain-container band member `FUN_0051d8e0` (hides children +
  crashes); frame-list item (renders then crashes); dialog-base-proc window direct child (crashes; button ok);
  owned band frame + our dispatcher (no contents + crash). **Conclusion: no ad-hoc container hosts the complex
  controls — only the full instanced-dialog framework does.**

**Phase 1 PROVEN (banked capability):** Py4GW CAN author a native C++ FrameProc the engine calls without an
ABI crash. See `Py4GW_InstancedDialogProc` (`include/py_ui.h`, `__cdecl(uint32_t* msg, void*, void*)`, forwards
to `ResolveFrameMsgCallBase` = EXE 0x00647170) + `AttachInstancedDispatcherByFrameId` +
`CreateOwnedBandFrameByFrameId` (bound as `attach_instanced_dispatcher_by_frame_id` /
`create_owned_band_frame_by_frame_id`). Forward-only dispatcher renders fine; it just doesn't yet OWN anything.

**RECOMMENDED NEXT STEP — build the host as ONE unit, not incrementally.** Every partial piece crashes because
each layer needs the others already present. Implement the whole **instanced content-dialog host** in one pass
against the 9-step spec in `native_dialog_layout_process.md` §"Reliable pattern": author the dispatcher to
(i) on create MemAlloc an instance embedding a `CCtlLayout`, store in `frame[2]`, `SetFrameId`; (ii) create
controls as direct children of that frame; (iii) build a Row/Column `CCtlLayout` tree and run
`SizeQuery`(0x38)/`Size`(0x37) via `Ui::CLayout::SizeQuery` EXE 0x00602900 / `Ui::CLayout::Size` EXE 0x00602060
(or the terminal `Frame_ApplyLayoutRect` EXE 0x0062e8a0 per child); (iv) edit via the nested `UiCtlDlg` content
child (`IUi::CompositeDlgContentProc` EXE 0x008895d0); (v) teardown via `PopCloser` + free instance on msg 0xb.
The `CCtlLayout` methods are `__thiscall` on a `this` buffer you allocate (WASM: ctor 0x80dfa34c, SetFrameId
0x80dfa3da, Column 0x80dfa95a, Child 0x80dfa5a4/EXE 0x00601880, End 0x80dfacf9, Size 0x80dfa3eb, SizeQuery
0x80dfa4bc, Clear 0x80dfa377).

**Isolated test scaffold:** `UI_RE/native_layout_test.py` (widget "Native Layout Test") — SEPARATE from the
main harness so iterating the host cannot regress working controls; crash-safe log `UI_RE/native_layout_log.txt`.

**Method rules the user enforced (do not violate):** RE on **`/Gw.wasm` FIRST** (named symbols), map to EXE
after; **rename EXE functions** as you identify them (`rename_function_by_address`, ignore style warnings) —
a stream of `FUN_xxxx` means you're doing it backwards. **No bypasses** — the native flow (incl. the `[X]`)
must work; do not remove affordances, self-scrub globals, or dodge into frame-list hosting for interactive
controls. Trust the user's in-client crash reports over any log ("created ok" then silence = a hard crash
AFTER create).

---

## 1. Goal & scope

Create real, native GW UI controls (not ImGui fakes) from Py4GW: button, checkbox, radio, hyperlink/
text-button, edit box, progress bar, tabs, slider, group header — created in-client, styled with the real
GW textures, interactive via the engine's own state, and destroyable without crashing.

Code lives across two repos:
- **C++**: `C:\Users\Apo\Py4GW` — `include/py_ui.h` (creator functions), `src/py_ui.cpp` (pybind bindings).
- **Python**: `C:\Users\Apo\Py4GW_python_files` — `Py4GWCoreLib/GWUI.py` (high-level API),
  `stubs/PyUIManager.pyi` (type stubs), `UI_RE/gwui_controls_test.py` (in-client test harness).

**Build**: `cd C:\Users\Apo\Py4GW && cmake --build build --config RelWithDebInfo` → copy
`bin\RelWithDebInfo\Py4GW.dll` to `C:\Users\Apo\Py4GW_python_files\Py4GW.dll`. (Config is **RelWithDebInfo**,
not Release.) Then reload the widget in-client.

**Test**: run `UI_RE/gwui_controls_test.py` in-client. It creates each control in its own window, polls
live state, has per-control verdict buttons, and **auto-saves crash-safe** to `UI_RE/ui_test_results.txt`
(verdict table) and `UI_RE/ui_test_log.txt` (append+fsync per event; writes `CREATING <x>` BEFORE each
risky create, so a hard crash leaves the culprit on disk).

---

## 2. CURRENT IN-CLIENT STATUS (last verified 2026-07-01)

| Control | Status | Detail |
|---|---|---|
| **button** | ✅ WORKS | textured, clickable — simple `CtlBtnProc`; hosts fine as a frame-list item AND as a direct child on the dialog-base window |
| **tabs** | ✅ WORKS | real tab texture + switching (styled `UiCtlPageProc` 0x00885590 as PRIMARY proc) |
| **group section** | ✅ WORKS | header + collapsible member rows (app-side collapse via ShowItem msg 0x67) |
| **progress** | ✅ renders + animates | value-cycle works; close crash shared with the complex-control teardown (§0) |
| **checkbox** | ✅ glyph fixed / ❌ close crash | flags `0x48300`→`0x18000` (the `0x40000` bit was forcing the button face). Renders CORRECT texture + toggles as a plain direct child; ONLY failure is the native `[X]` teardown crash. Crashes/blanks in every non-direct-child host tried (§0) |
| **hyperlink** | ✅ click fixed / ❌ z-order | click now detected (unique nonzero per-row child codes in `GWUI.py`); still z-fights/buried as a selectable list — needs the instanced-dialog host |
| **slider** | ⚠️ drags / ❌ wide+blank | too wide (range→pixel; needs the `CCtlLayout` clamp); blank without the layout pass |
| **edit** | ❌ blank | needs BOTH the sibling `UiCtlBorderProc` box AND the layout pass — i.e. the instanced-dialog host (or ConfirmDialog nested `UiCtlDlg` child) |
| **radio** | ❌ generic/z-order | selectable-list rows render generic + buried; needs the host/layout |
| **native [X] close** | ❌ the dominant blocker | closing a window that hosts a complex control crashes (dangling hover hot-item); the native fix is `PopCloser` on a real content page, which needs the instanced-dialog framework (§0) |
| **destroy (our path)** | ✅ WORKS | `GWUI.DestroyWindow` = scrub input targets + native destroy (the safe close button, not `[X]`) |

**The single dominant open problem is the native `[X]` close crash** (dangling hover hot-item after freeing a
direct-child control). See §0: the real fix is the instanced-dialog + `CCtlLayout` host (which routes `[X]`
through `PopCloser`), NOT any ad-hoc container — all of which were tried and crash.

---

## 3. Doc map (where the detail lives)

| Doc | Contents |
|---|---|
| **`native_button_pipeline.md`** | ★ authoritative creation reference: master address/flag/status table, per-control recipes, the working-button pipeline, cross-cutting gotchas, the foundational model. |
| `ui_controls_master_catalog.md` | The UI creation/dispatch **model** + **166 discovered control FrameProcs** (addresses/roles) + 120 deep per-control RE writeups (from two Ghidra swarms). |
| `ui_elements_creation_recipes.md` | Per-control recipe deep-dives (root cause / recipe / fix). |
| `ui_controls_catalog.md` | Per-type FrameProc inventory (addresses, struct layouts, assertion strings, tiers). |
| `reverse_engineering_reference.md` | Global address catalog incl. the "Native UI Control FrameProcs & Helpers" table. |
| `ui_frame_system_mapping.md` | GWCA ↔ WASM ↔ EXE frame API mapping. |
| **this file** | Honest handover: status, root causes, fixes-that-stuck, dead-ends, open problems. |

---

## 4. The authoritative model (decompiler-verified)

- **One create primitive, one destroyer.** `FUN_0062bfc0(parent,flags,childId,proc,userdata,name)` mints a
  frame, links it into the parent's relation-3 child list, installs the proc, and RETURNS the registry
  handle at `frame+0xbc` — **that returned handle is the id you keep** (no offset, no childId). Destroy =
  `FUN_0062c550(id)` → `FUN_0062ab40` recursively frees the subtree AND delivers each control's own
  `case 0xb`. **Teardown is uniform; a "direct child" free is NOT inherently unsafe.**
- **Controls are `TCtlInstance<T>` classes; the proc is a MsgProc** switching on `msgframe[1]`: case 4 =
  install base proc, case 9 = alloc instance (`FUN_0047f340("<Ctl>.cpp",size)`), case 0xb = destroy,
  case 1 = paint (sub-pass `*payload`), case 0x15 = size-query, 0x56+ = control-specific get/set.
  Class inheritance is a **proc chain** (case 4 writes the parent proc into `payload[3]`), not a vtable.
- **Two-layer controls (slider, tabs) MUST be created with the WRAPPER proc as PRIMARY** via a single
  `CreateUIComponent` — the wrapper's case 4 installs the base. A post-create `FrameNewSubclass(wrapper)`
  never receives msg 4 and re-fires msg 9/0xb on garbage → crash. (This is why the slider and tabs create
  crashed before, and why wrapper-primary fixed both.)
- **The game hosts controls under an owned content frame** (a `CtlView` scroll page, a `CtlFrameList`, or
  a plain container), never bare on the CtlDlg chrome root — BUT reproducing this naively regressed
  everything (see §6). The composite root `FUN_00876880` is window CHROME ONLY; its close handler
  `FUN_008766e0` tears down only the tab-page id band 10000..0x2718 and **does not scrub input globals**.
- **The close crash — attribution corrected (2026-07-01).** The engine's native teardown DOES scrub the
  frame INPUT-FOCUS globals: `FrameDestroy` (WASM `809a1b36`) → `DestroyRecursive` (`8099c0ae`) calls,
  per frame, `IFrame::CMouse::Destroy(frame+0x94)` → `CMouse::Reset` (`8092a9f9`), which nulls hover
  (`DAT_0059fa94`), mouse-focus (`DAT_0059fa8c`) and nonclient-focus (`DAT_0059fa88`) when they point at
  the frame being freed. So "teardown never scrubs" is FALSE for the CMouse focus system. The EXE global
  the safe-close path scrubs — `DAT_00c0ad54` via `FUN_00630cd0` — is a DIFFERENT, secondary "hot
  sub-item" used for msg `0x46` (rollover/tooltip highlight), not CMouse frame-focus. So the residual
  close crash is most likely (a) that secondary hot-item not being cleared, or (b) a subclass mishandling
  the destroy messages (`Notify 3`, `msg 0xb`) — needs one in-client confirmation rather than the
  assumed "focus isn't scrubbed" cause. (`DAT_00c0ad58` sub-item, `DAT_00c0ba10` focus/tooltip cleared by
  `FUN_0064e920`.)

---

## 5. Root causes + FIXES THAT STUCK (in the current DLL)

- **slider create crash → FIXED.** Was base-primary + `FrameNewSubclass`. Now single `CreateUIComponent`
  with **`UiCtlSliderProc` 0x0087f440 as PRIMARY** (`ResolveUiCtlSliderProc`, flags 0x40000), then
  SetRange(0x56)→SetValue(0x57)→size. `CreateSliderControlByFrameId`.
- **tabs generic → FIXED.** `GWUI.CreateTabs` now creates a direct-child container with **styled
  `UiCtlPageProc` 0x00885590 as PRIMARY** (`ResolveUiCtlPageProc`); `AddTab` passes tab flag 0x20000.
- **destroy silently no-ops → FIXED.** GWCA `DestroyUIComponent` resolver scans an old source path
  (`\Code\Gw\Ui\Frame\FrApi.cpp`) that the 06-14 build renamed to `\Code\Engine\Frame\FrApi.cpp`. Now calls
  the native id-destroyer **`FUN_0062c550`** directly. `DestroyUIComponentByFrameId`.
- **edit id=0 discarded → FIXED (but still blank, see §5.2).** id 0 is a VALID handle (recycled slot 0);
  the `if(!id) return 0` guard threw it away. Now `0xFFFFFFFF` is the only failure sentinel; seeds the
  value store post-create with SetMaxLength(0x5A)+SetText(0x5E). `CreateEditBoxChildByFrameId`.
- **radio rows didn't highlight → row-proc corrected.** Rows now use `CtlTextSelectable` 0x00617df0
  (its case 0x57 sets the selected flag) instead of flat `CtlBtnProc` (whose 0x57 only clears a bit).
  Still broken in-client (§2) — needs more work.
- **group has no native collapse → FIXED app-side.** Added `CtlFrameListShowItemByFrameId` (msg 0x67,
  by child code) + `GWUI.RegisterGroupSection` / `UpdateGroupSections`.
- **poll-after-free crashes → MITIGATED.** `FrameExistsByFrameId` (GetFrameById != null); the test poll
  and `UpdateGroupSections` skip/drop controls whose window was closed.
- **safe close → ADDED.** `ClearUiInputTargets()` = `FUN_00630cd0(0,-1)` + `FUN_0064e920(0)`, and
  `DestroyWindowSafelyByFrameId` scrubs then destroys. `GWUI.DestroyWindow` / harness "Destroy All" use it.
  **Fixes the close crash ONLY for our destroy path — NOT the native [X] (§5.1).**

### 5.1 OPEN — the close crash (dominant)
Closing a window that hosts checkbox/progress/hyperlink/radio/slider crashes via the native title-bar
**[X]**, because that runs the engine's own teardown (`FUN_008766e0` → `FUN_0062c550`) which does NOT scrub
the hover global, leaving the freed control dangling in `DAT_00c0ad54`. Our `DestroyWindow` scrubs and is
safe, but we cannot intercept the native [X]. Frame-LIST-item controls (button, section) survive [X] for a
reason not fully pinned down (hover likely routes to the list frame, not the item). **Recommended fixes
(unvalidated):** (a) create windows WITHOUT a native close box so all closing goes through the safe scrub
path; or (b) find/replicate the game's dialog-closer (IUi::PopCloser) that scrubs before destroy and wire
the window's [X] to it. See §6 for the approach that did NOT work.

### 5.2 OPEN — per-control rendering / function
- **checkbox glyph → ROOT-CAUSED + FIXED (2026-07-01).** The "cancel/X button" glyph was NOT an
  image-list or handle problem — it was the create flags. `0x48300` includes `0x40000`, which in
  `UiCtlBtnProc` (`FUN_00877e60`) gates the raised BUTTON FACE (msg `0x01` sub-pass 0); with it set the
  checkbox paints as a button. GW's own checkboxes (`CDlgOptGeneral::OnFrameCreate` @ WASM `80fcf105`)
  use flags `0x10000` only (auto-size-width layout) + `0x8000` (glyph) with the SAME `UiCtlBtnProc` — no
  `0x40000`. Fix: pass `0x10000` to `CreateCheckboxFrame` → effective `0x18000`. The check glyph itself
  is drawn by sub-pass 1 (ungated) from `s_btnCheckImageList`, which `EnsureBtnCheckImageList` builds
  safely (guarded on the global being null). The `frame->frame_id`/`-4 offset` question was a red herring
  — `frame->frame_id` is the correct handle. **Close-crash is separate (§5.1); verify checkbox in isolation.**
- **edit**: blank. Correct outer proc (`CCtlEdit` 0x008852e0) and the id=0/seed fixes are in. The
  "needs the game's intermediate container" theory is likely WRONG: GW's email form (`CEmail::OnFrameCreate`
  @ WASM `80faf332`) creates edit boxes DIRECTLY as dialog-content children —
  `FrameCreate(dialogContent, 0 /*or 0x1000000 password*/, childId, EditProc→UiCtlEditProc(base 0xab0), 0, name)`
  plus a sibling `UiCtlBorderProc` "Border" frame — no special hosting container. So a blank edit is almost
  certainly the same direct-child ZERO-SIZE problem documented for other controls (an edit has no intrinsic
  size; without the anchor-6/layout size pass it collapses), not a container problem.
- **radio / hyperlink**: render generic / no confirmed click, and crash on close. The selectable-list
  click read (msg 0x69/0x67) and the row proc need in-client iteration.
- **slider width**: intrinsic/range-driven (measured width = `(max-min) × unit × scale`); there is NO
  set-width message, and the anchor-6 setter asserts on the slider. True width control needs decoupling
  the logical range from a pixel span (rescale in Get/SetSliderValue) — not done.

---

## 6. DEAD ENDS — reverted, DO NOT REPEAT

- **Checkbox id from `frame + sizeof(void*)`** (the "-4 offset" theory): caused an IMMEDIATE checkbox
  crash in-client. Reverted to `frame->frame_id`. The real checkbox handle question is still open.
- **Content-panel hosting** (parent controls to a plain `FUN_0051d8e0` container instead of the window):
  intended to fix the [X] close per the model — **regressed EVERYTHING, even the button stopped working.**
  Fully reverted (the C++ helpers `CreateContentPanelByFrameId` / `ResolvePlainContainerProc` /
  `GWUI.CreatePanel` remain in the code but are UNUSED/dormant). A plain container as implemented is NOT a
  viable host; if revisited, validate the exact container type (CtlView page vs CtlFrameList item vs plain)
  and the child flags in-client one control at a time.
- **Anchor-6 setter (0x0062F770) on the slider**: asserts inverted-rect (0x238) on the self-measuring
  slider container → immediate crash. Reverted; slider uses plain `FrameSetSize` (renders wide).
- **Post-create `FrameNewSubclass(styled)` for tabs**: crashed on display (wrapper never gets msg 4).
  Replaced by wrapper-as-primary (the working fix).

---

## 7. Recommended next steps (for the next owner)

1. **Nail the close model empirically.** The RE says the crash is the dangling hover global; the safe path
   (our `DestroyWindow` scrub) works. The cheapest robust win is likely **removing the native close box**
   from `CreateNativeWindow` so ALL closing routes through the safe scrub. Investigate the window/subclass
   flags in `AttachCompositeRootToFrame` for a no-close-box option.
2. **Then** revisit per-control rendering (checkbox glyph/id, edit blank, radio/hyperlink) one at a time,
   rebuilding + testing each in isolation via the harness verdict buttons — do NOT batch unverified changes.
3. Keep the crash-safe logging loop (`ui_test_log.txt`) — the `CREATING <x>` trail is how we localize hard
   crashes with no Python exception.

---

## 8. Key addresses (condensed — full tables in `native_button_pipeline.md` / `reverse_engineering_reference.md`)

| Symbol | EXE | Role |
|---|---|---|
| create primitive | `FUN_0062bfc0` | mint frame → returns handle at `frame+0xbc` |
| destroyer (by id) | `FUN_0062c550` | recursive subtree free + each control's case 0xb |
| dispatcher | `FUN_0062ef40` | send msg to a frame |
| hover setter (scrub) | `FUN_00630cd0` | `(0,-1)` clears `DAT_00c0ad54`; **the close-crash global** |
| focus/tooltip clear | `FUN_0064e920` | `(0)` clears `DAT_00c0ba10` |
| composite-root (chrome) | `FUN_00876880` | window chrome; close `FUN_008766e0` (no scrub) |
| plain container proc | `FUN_0051d8e0` | pass-through content container (dead-end host — §6) |
| styled button / checkbox | `0x00877e60` | `UiCtlBtnProc` (checkbox face 0x8000, paint gate 0x40000, imglist DAT_010819cc) |
| flat base button | `0x0060f4f0` | `CtlBtnProc` |
| text button | `0x00616c00` | `CtlTextBtnProc` (unsafe 0x57 for selectable rows) |
| selectable text row | `0x00617df0` | `CtlTextSelectable` (null-safe 0x57; radio/hyperlink rows) |
| selectable list proc | `0x00613850` | needs create flags 0x20128 |
| outer edit | `0x008852e0` | `CCtlEdit` (render subclass 0x00888aa0) |
| progress | `0x008812e0` | ProgressBar |
| slider wrapper / base | `0x0087f440` / `0x00615fe0` | create wrapper-as-PRIMARY |
| styled page / tab-btn | `0x00885590` / `0x00885340` | tabs; create styled-as-PRIMARY |
| group header | `0x0087ddc0` | `CGroupHeaderFrame` |
| anchor-6 pos/size | `0x0062F770` | sizes direct children (asserts on slider) |

---

## 9. New py_ui.h functions this effort added (all bound + in GWUI)

`CreateSliderControlByFrameId` (wrapper-primary), `ResolveUiCtlSliderProc`, `CreateTabsFrameByFrameId`
(styled-primary), `ResolveUiCtlPageProc`, `CreateEditBoxChildByFrameId` (id=0 sentinel + seed),
`AddClickableTextButtonToSelectableList` (CtlTextSelectable), `ResolveCtlTextSelectableProc`,
`CtlFrameListShowItemByFrameId`, `DestroyUIComponentByFrameId` (FUN_0062c550), `ClearUiInputTargets`,
`ResolveSetHoverTarget`, `ResolveClearFocusFrame`, `DestroyWindowSafelyByFrameId`, `FrameExistsByFrameId`,
`DestroySliderControlByFrameId`, plus the **dormant/unused** `CreateContentPanelByFrameId` /
`ResolvePlainContainerProc` (dead-end, §6). GWUI: `CreateSlider/DestroySlider`, `CreateTabs`, `CreateEditBox`,
`CreateRadioGroup`, `CreateGroupHeader`+`RegisterGroupSection`/`UpdateGroupSections`, `DestroyWindow`,
`ClearInputTargets`, `CreatePanel` (dormant).

### 9b. 2026-07-01 session additions (the instanced-dialog groundwork)
- **`Py4GW_InstancedDialogProc`** (file-scope, `__cdecl(uint32_t* msg, void*, void*)`) — the authored native
  FrameProc the engine calls. PHASE 1 = forward-only (calls `ResolveFrameMsgCallBase`). This is where the
  real owner logic (MemAlloc instance + `CCtlLayout` + size pass on msg 0x38/0x37 + free on 0xb) must go.
- **`ResolveFrameMsgCallBase`** → `IUi_FrameMsgCallBase` EXE 0x00647170 (byte-pattern; walks the proc chain).
- **`AttachInstancedDispatcherByFrameId`** (bound `attach_instanced_dispatcher_by_frame_id`) — `FrameNewSubclass`
  the dispatcher onto a frame. PROVEN: engine calls it, renders, no ABI crash.
- **`CreateOwnedBandFrameByFrameId`** (bound `create_owned_band_frame_by_frame_id`) — band-0x2710 plain
  container + dispatcher. **Result: no contents + crash** (plain container is not a viable host — same dead-end
  as §6; kept only as scaffolding).
- **`ResolveUiCtlContentPageProc`** (composite-root − 0x140 = EXE 0x00876740) + **`CreateContentPageByFrameId`**
  (bound `create_content_page_by_frame_id`) — the REAL content-page proc. **Result: crashes standalone**
  (half-initialized without the dialog framework's activation). Do not use raw.
- **`ResolveUiCtlDlgMsgProc`** (composite-root − 0x270 = EXE 0x00876610) + **`CreateNativeDialogWindow`**
  (bound `create_native_dialog_window`) — window created with the dialog BASE proc (mimics
  `CompositeDlgBuilder` case 1: style 0x254000, childId 0xd) + chained chrome. **Result: window + a BUTTON
  work and close cleanly, but a direct-child CHECKBOX still crashes** (needs the full instance+layout).
- **`EnsureContentFrameForWindow`** — DISABLED (returns window_id); the band-content nesting it drove
  regressed rendering. Left as `#if 0` scaffolding.
Isolated test: `UI_RE/native_layout_test.py`. None of these touch the working-control code paths.
