# Native UI Controls — Complete Pipeline & Reference

Last updated: 2026-07-01 | EXE Build: 06-14-2026 | Project: native-ui-controls

> **This is the AUTHORITATIVE doc for creating native GW UI controls in Py4GW.** It started as the
> button pipeline and now covers the full toolkit (button, checkbox, radio, hyperlink/text-button,
> edit, progress, tabs, slider, group header) plus teardown. Every address/flag/message below is
> Ghidra-verified against `Gw.exe` build **06-14-2026** (program `/Gw.exe (06-14)`) unless noted.
> Companion docs: `ui_controls_catalog.md` (per-type FrameProc catalog), `ui_elements_creation_recipes.md`
> (recipe-per-control), `ui_frame_system_mapping.md` (GWCA↔WASM↔EXE frame API), `reverse_engineering_reference.md`
> (global address catalog).
>
> **⚠️ For the CURRENT honest per-control status (what works / what is still broken / dead-ends), see
> `native_ui_controls_handover.md` — it is the source of truth. The recipes here describe the intended
> mechanism; several are not yet working in-client (checkbox, radio, hyperlink, edit, and the native-[X]
> close crash are OPEN).**

## 📇 MASTER REFERENCE — addresses, flags, status (2026-07-01)

**Code locations:** C++ `C:\Users\Apo\Py4GW\include\py_ui.h` (+ `src/py_ui.cpp` bindings); Python API
`Py4GWCoreLib/GWUI.py`; test harness `UI_RE/gwui_controls_test.py`. Build: `cmake --build build --config
RelWithDebInfo` then copy `bin/RelWithDebInfo/Py4GW.dll` → `Py4GW_python_files/Py4GW.dll`.

### Shared primitives (EXE 06-14)

| Primitive | EXE addr | Role |
|---|---|---|
| Frame message dispatcher | `FUN_0062ef40(frame,msg,wparam,out)` | GWCA `SendFrameUIMessage` wraps it |
| Frame create primitive | `FUN_0062bfc0(parent,flags,child,proc,userdata,0)` | returns frame id (`*(frame+0xbc)`) |
| CtlFrameListCreateItem | msg `0x57` on the list | creates a row item with a given item-proc + encoded text |
| **Anchor-6 pos/size setter** | `0x0062F770` `__cdecl(id, Coord2f* pos, Coord2f* size)` | **the only sizing that "sticks" on a direct window child** — beats layout stretch/reset |
| FrameGetNativeSize (sret) | `0x0062D2A0` | item's own native size |
| FrameNewSubclass | `0x0062f150` `__cdecl(id, proc, msg)` | layer a proc over a frame (two-layer controls) |
| Native frame destroyer | `FUN_0062c550(frame_id)` `__cdecl` by value | validates id, tears down tree, frees |

### Per-control FrameProcs, flags & status

| Control | Item/child FrameProc (EXE) | Key flag/message | GWUI API | In-client status (2026-07-01) |
|---|---|---|---|---|
| button (styled) | `UiCtlBtnProc 0x00877e60` | paint gate `0x40000` + `s_btnCheckImageList 0x010819cc` (warm via msg `0x05`); caption msg `0x5E`; click msg `0x59` | `CreateButton/IsButtonClicked` | ✅ works |
| checkbox | `UiCtlBtnProc 0x00877e60` + base flat `CtlBtnProc 0x0060f4f0` | flags `0x18000` (`0x10000` auto-width + `0x8000` checkbox glyph); **NO `0x40000`** (that gate paints the BUTTON face → wrong glyph); state msg `0x57`/`0x58`; list built by proc msg `0x05` | `CreateCheckbox/IsChecked/SetChecked` | recipe corrected 2026-07-01 → testing |
| radio | selectable list + `CtlBtnProc 0x0060f4f0` rows | flat-button rows; select by child KEY `insert_index=i+1`; set msg `0x6A`, get msg `0x69` | `CreateRadioGroup/GetRadioSelection` | fixed → testing |
| hyperlink / text-button | `CtlTextSelectable 0x00617df0` (NOT `CtlTextBtnProc 0x00616c00`) | item flags `0xe001`; click = parent-notify 8 → pollable selection | `CreateHyperlink/GetClickedHyperlink` | fixed → testing |
| edit | outer `CCtlEdit 0x008852e0` (NOT subclass `0x00888aa0`) | flags `0x892e000`; size via anchor-6; caret `s_editCaretMaterial`; text msg `0x5E` | `CreateEditBox/GetEditBoxText/SetEditBoxText` | fixed → testing |
| progress | `ProgressBar 0x008812e0` | percent msg `0x5B`, value `0x58`, max `0x5A` | `CreateProgressBar/SetProgressBar*` | ✅ creates (value-cycle test added) |
| tabs | base `CtlPageProc 0x0061a950` + styled `UiCtlPageProc 0x00885590` (tab-btn `0x00885340`) | keep flags `0x40000`; layer styled proc before AddTab | `CreateTabs/AddTab/GetActiveTab` | textured fix → testing |
| slider | base `CtlSliderProc 0x00615fe0` + wrapper `UiCtlSliderProc 0x0087f440` | SetRange `0x56` before SetValue `0x57`; value get `0x58`; size via anchor-6; **destroy via mouse-up `0x2e` first** | `CreateSlider/GetSliderValue/DestroySlider` | works; leak fix → testing |
| group header | `CGroupHeaderFrame 0x0087ddc0` (self-builds checkbox+caption) | item in a plain list; getIsOpen `0x56`, setIsOpen `0x58`, setText `0x59` | `CreateGroupHeader/IsGroupHeaderOpen` | works (items-inside test added) |
| **destroy** | native `FUN_0062c550` | GWCA `DestroyUIComponent` no-ops on 06-14 (resolver path drift) | `destroy_ui_component_by_frame_id` | fixed → testing |

### Cross-cutting gotchas (read before touching any control)
1. **Direct-child sizing:** `FrameSetSize` is overwritten by the window's composite-root layout each pass → 0×0 (edit invisible) or full-width (slider). Use the **anchor-6 setter `0x0062F770`**.
2. **Captions must be ENCODED** (`BuildStandaloneLiteralEncodedTextPayload`); a raw wide string into an encoded-text path (msg `0x5E`/`0x5F`) crashes. Prefer delivering the caption at create.
3. **Selectable-list rows need a NULL-safe row proc:** highlight sends child msg `0x57` with a NULL out-ptr; `CtlTextBtnProc`/`CtlTextProc` write through it (crash). Use `CtlBtnProc` (radio) or `CtlTextSelectable` (hyperlink). Selectable list needs create flags **`0x20128`** (not `0x20000`).
4. **GWCA resolver path drift:** the 06-14 build renamed engine source paths `\Code\Gw\Ui\Frame\…` → `\Code\Engine\Frame\…`, so any GWCA `FindAssertion` keyed on the old path resolves NULL and its wrapper silently no-ops (this broke `DestroyUIComponent`). Call the native worker directly.
5. **Two-layer controls (slider) leak CTimers** if torn down mid-interaction — release with mouse-up `0x2e` before destroy.

### 🔧 LATEST BUILD STATUS (2026-07-01, post 166-control swarm)

Confirmed working: **button ✅, progress ✅, destroy ✅, group header ✅**. Fixes applied this build (from the swarm's decompiler-backed recipes — retest):
- **radio** → rows now use `CtlTextSelectable` (0x00617df0), not flat `CtlBtnProc`. The list highlights via child msg `0x57`; CtlBtnProc's `0x57` only *clears* its bit (row never highlights), CtlTextSelectable's `0x57` *sets* the selected flag + redraws. (`GWUI.CreateRadioGroup`)
- **hyperlink** → verified correct with `item_flags=0` (the `0xe001` regression carried bit `0x2000` = manual-position → invisible row + close-crash). No functional change needed.
- **tabs** → `GWUI.CreateTabs` now creates a **direct-child** container with styled `UiCtlPageProc` (0x00885590) as the **PRIMARY** proc (mirrors the game's `FUN_00889950`), not the base-proc list-item path. The engine sends msg `4` (install base/vtable) only at create, so the styled proc MUST be primary — a post-create `FrameNewSubclass` crashes on display. `AddTab` already passes styled tab-flag `0x20000`.
- **edit** → seeds the value store post-create with `SetMaxLength` (msg `0x5A`) + `SetText` (msg `0x5E`, encoded space); without a non-empty store `CtlEditProc` paints nothing (the "empty window").
- **group items** → the engine has **no native grouping**; added `CtlFrameListShowItemByFrameId` (msg `0x67`, by child code) + app-side `GWUI.RegisterGroupSection`/`UpdateGroupSections` that hide/show member rows on header toggle. List must be `0x20000` (no `0x2000`) to reflow.
- **checkbox** → **CORRECTED 2026-07-01 (was `0x48300`, wrong).** Ground truth = how GW builds its own checkboxes (`CDlgOptGeneral::OnFrameCreate` @ WASM `80fcf105`: `CheckShowKoreanRatings`, `CheckMouseDisableWalk`, …): `FrameCreate(parent, 0x10000, childId, UiCtlBtnProc, textId, name)` — style word `0x10000` ONLY (`0x10000`/`0x20000` are auto-size-width/height LAYOUT flags, per `IFrame::Layout::CCmdAdd::Execute`, not control styles). `CreateCheckboxFrame` ORs `0x8000` (checkbox glyph) → effective `0x18000`. **`0x40000` must NOT be set**: in `UiCtlBtnProc` (`FUN_00877e60`) the raised button FACE is drawn by msg `0x01` sub-pass 0 *only when* `FrameTestStyles(frame,0x40000)!=0`; setting it on a checkbox paints a button (the "cancel-button / wrong glyph" symptom). The CHECK glyph is drawn by sub-pass 1, which is **not** gated by `0x40000` and pulls from `s_btnCheckImageList`. (Radio = same proc + `0x804000`.) The image list is engine-owned: the proc builds it on msg `0x05` (asserting `!s_btnCheckImageList`); `EnsureBtnCheckImageList` safely triggers that build only when the global is still null.
- **slider** → width is **intrinsic/range-driven** (no set-width message: measured width = `(max-min) × unit × scale`); the anchor-6 setter asserts (inverted-rect `0x238`) on the self-measuring slider container. Kept functional (`FrameSetSize`, renders wide, no crash). Proper width control requires decoupling logical range from a pixel span (rescale in Get/SetSliderValue) — deferred (changes value semantics).

Full model + all 166 discovered control procs: `ui_controls_master_catalog.md`.

### 🔧 BUILD STATUS (2026-07-01, crash-fix swarm)

In-client retest confirmed: **button ✅, tabs (textured) ✅, group section ✅, progress renders ✅**. A
crash-fix swarm root-caused the rest. Fixes applied this build:
- **checkbox** — `CreateCheckboxFrame` returns a pointer **4 bytes below** the real frame, so
  `frame->frame_id` (0xbc) read `child_offset_id` (0xb8) = the child_index (=1). All warm-up/SetChecked/
  redraw targeted the WRONG frame (→ `id=1`, no tick). Fixed: read id from `frame + sizeof(void*)`. The
  tick is checked-state-gated (an unchecked box legitimately shows empty); with the right id, `SetChecked`
  now reaches the real frame.
- **edit** — `id=0` is a **valid** GW frame handle (0-based, recycled slot 0); the `if(!id) return 0`
  guard discarded it and skipped size+seed → blank. Fixed: `0xFFFFFFFF` is now the only failure sentinel;
  id 0 renders. (`GWUI.CreateEditBox` no longer collapses valid 0.)
- **slider** — was created base-primary + `FrameNewSubclass(wrapper)` (same bug class as tabs): the wrapper
  never gets msg 4 and the subclass re-fires msg 9/0xb → freed+garbage instance → crash on create. Fixed:
  single `CreateUIComponent` with the **wrapper `UiCtlSliderProc 0x0087f440` as PRIMARY** (new resolver),
  flags `0x40000`, then SetRange→SetValue→size.

**Open — the dominant "crash on closing the host window"** (checkbox / progress / hyperlink / radio):
a composite-root (CtlDlg) **use-after-free** — `FUN_0062c550` frees the window's direct children while the
still-attached composite root relayouts/hit-tests against them (and against the stale hover/selection
global). Frame-LIST items (button, section) are safe because the composite root manages a single list
child. **Fix (next):** parent these controls through a plain frame list instead of directly under the
window (mirrors the safe button/section path); or a children-first window destroy that clears the
hover/selection globals before freeing the window frame.

### 🧭 FOUNDATIONAL MODEL — how the game builds/tears down multi-control windows (2026-07-01)

A 7-agent swarm decompiled REAL in-game dialogs (the Options window `DlgOptionProc` @ WASM 0x810190f1;
the GmChat name/whisper edit builder `FUN_0051b580`). Ground truth (EXE 06-14):

- **One create primitive / one destroyer.** `FUN_0062bfc0(parent,flags,childId,proc,userdata,name)` mints
  a frame, links it into the parent's relation-3 child list, and returns the registry handle at
  `frame+0xbc` — **that returned handle is the id you keep** (no offset, no childId). `FUN_0062c550(id)`
  → `FUN_0062ab40` recursively frees the subtree AND delivers each control's own `case 0xb`. So teardown
  is uniform and a "direct child" free is **not** inherently unsafe.
- **THE crash = a dangling hover global.** Hover state is `DAT_00c0ad54` (hovered frame ptr, sole writer
  `FUN_00630cd0`), `DAT_00c0ad58` (sub-item), plus focus/tooltip `DAT_00c0ba10` (cleared by `FUN_0064e920`).
  The teardown chain **never scrubs these**. Close a window whose control is the current hover/focus
  target → the frame is freed but `DAT_00c0ad54` still points at it → next mouse-move/paint dereferences
  freed memory → crash. This is the real "crash on closing the window."
- **The game's structure.** The CtlDlg composite root (`FUN_00876880`) is **window chrome only** (title/
  drag/close, tab-page band 10000..0x2718). Real controls live under a dedicated **owned content frame** —
  a plain no-visual container (GmChat `FUN_0051d8e0`, child-index 1 of the window), or a `CtlView` scroll
  page, or a `CtlFrameList`. Inside that content frame, leaf controls are **flat direct children** arranged
  by a transient `CCtlLayout` pass (Row/Column/Child(childId)/Gap/End). The game never hangs a bare
  interactive control on the chrome root.

**Fix applied (2026-07-01):** `ClearUiInputTargets()` = `FUN_00630cd0(0,-1)` + `FUN_0064e920(0)` (new
resolvers), and `DestroyWindowSafelyByFrameId(window_id)` scrubs then destroys. `GWUI.DestroyWindow()` /
test "Destroy All" now route through it. **Still to do:** the owned content-frame layer so controls aren't
bare children of the chrome root (needed for the native-[X] close path, which doesn't run our scrub).

---

## ✅ THE WORKING BUTTON — CONFIRMED IN-CLIENT (2026-06-30)

**A real, textured, clickable Guild Wars button now renders and reports its clicks natively.**
This is the definitive working recipe — use it.

**What works:** a **STYLED** button (`IUi::UiCtlBtnProc`, EXE `0x00877e60`) created as an item in
a **NO-STRETCH scrollable frame list**. It draws the real 9-slice GW button texture, sizes to its
content, and its clicks come from the engine's own button state — no ImGui, no hit-test.

### The recipe (every step Ghidra-verified)
1. **Window** — `CreateNativeWindow` (composite root).
2. **Scrollable frame list** child — `create_scrollable_content_by_frame_id`.
3. **Install the no-stretch size handlers** — `set_frame_list_no_stretch_by_frame_id(list)`.
   Native `size` (msg **`0x62`** → ctx+0x04) + `size-query` (msg **`0x64`** → ctx+0x10) callbacks,
   `__cdecl(TArray<uint>* items, msg*)`, that keep each item at its **own native width** instead of
   stretching to the list width. Without this **every control is "extremely wide."**
   (`CCtlFrameList::OnFrameMsgSize`/`OnFrameMsgSizeQuery`; the default overwrites item width unless
   list style `0x4000` is set.) Geometry primitives: `FrameSetPosition(id,pos,size)` EXE `0x0062F770`
   (anchor forced 6), `FrameGetNativeSize` EXE `0x0062D2A0` (sret).
4. **Add the button item** — `add_control_item_by_frame_id(list, "styled_button", caption)`, which:
   - resolves `UiCtlBtnProc` via assertion `UiCtlBtn.cpp` / `!s_btnCheckImageList`;
   - **ORs `0x40000` into the item flags** — the paint sub-0 does `if(!(style&0x40000)) return;`, so
     without it the button draws **nothing**;
   - sets the caption via msg **`0x5E`**;
   - **ensures `s_btnCheckImageList`** (EXE `0x010819cc`): if null (no store opened this session),
     sends the item msg **`0x05`** to run `FrameImageListCreate` (guarded on null — the proc asserts
     `!s_btnCheckImageList`, so double-create would assert).
5. **Read clicks each frame** — `is_button_pushed_by_frame_id(btn)` (msg **`0x59`**), the engine's own
   pushed state; a rising edge = a click.

### Easy Python API — `Py4GWCoreLib/GWUI.py`
```python
win   = GWUI.CreateWindow(x, y, w, h, "Title")
blist = GWUI.CreateButtonList(win)            # scrollable list + no-stretch handlers
btn   = GWUI.CreateButton(blist, "Click Me")  # real styled, textured button
# every frame:
if GWUI.IsButtonClicked(btn):                 # rising-edge native click
    do_something()
```
`GWUI.IsButtonPushed(btn)` = held-down state; `GWUI.IsButtonClicked(btn)` = one True per click.

### C++ (all in `include/py_ui.h` + bound in `src/py_ui.cpp`)
`ResolveCtlBtnProc` (flat), `UiCtlBtnProc` via assertion (styled), `AddControlItemByFrameId`
(styled → `0x40000` + `EnsureBtnCheckImageList`), `SetFrameListNoStretchByFrameId` +
`NoStretchSizeHandler`/`NoStretchSizeQueryHandler` + `ResolveFrameSetPositionPosSize` /
`ResolveFrameGetNativeSize`.

### Key addresses (Gw.exe 06-14)
`UiCtlBtnProc` 0x00877e60 · `CtlBtnProc` 0x0060f4f0 · `s_btnCheckImageList` 0x010819cc ·
`FrameSetPosition(pos,size)` 0x0062F770 · `FrameGetNativeSize` 0x0062D2A0 · frame-list size msg
0x62 / size-query msg 0x64 · caption msg 0x5E · pushed-state msg 0x59.

### Not yet solved (separate follow-up)
`slider`/`edit`/`progress`/`tabs` create but render at 0×0 (they don't self-size and are multi-layer);
`groupheader` proc unresolved. These need the direct-child re-architecture — see
`docs/RE/ui_elements_creation_recipes.md`. **The BUTTON is done.**

### 📋 CONTROL STATUS — IN-CLIENT VERIFIED (2026-07-01)

Full GWUI toolkit implemented + compiled; tested in-client. Actual results:

| Control | Status | Notes |
|---|---|---|
| **button** | ✅ works | textured, sized, clickable (native pushed state) |
| **progress** | ✅ created | good values shown; changing value in-game not yet verified |
| **tabs** | ⚠️ works, WRONG texture | tabs function, but render as a **generic element**, not the real GW tab texture |
| **group header** | ⚠️ creates | open/close appears to work; child elements not yet tested |
| **edit** | ⚠️ empty window | window created but the edit control is **not visible** |
| **checkbox** | ❌ no display + **CRASH** | direct-child `CreateCheckboxFrame` — no box drawn, then client crash |
| **radio** | ❌ **immediate CRASH** | selectable-list create path (default selection / selection-state) |
| **hyperlink** | ⚠️/❌ renders then **CRASH** | displays correctly, but the per-frame selection **poll (msg 0x67 GetSelection) crashes** |
| **slider** | ❌ empty window + **CRASH on interact** | multi-layer; slider not visible, interacting crashes |
| **Destroy All** | ❌ **NEVER WORKED** | `destroy_ui_component_by_frame_id` does not tear these frames down — a real open gap; the correct native destroy/close path is unresolved |

**Recurring root causes to fix:**
1. **Selectable-list selection read/write (msg 0x66/0x67) crashes** → breaks radio (create) + hyperlink (poll). The `GetSelection` native handler derefs a selection-state that isn't set up on an empty/plain-item list.
2. **Direct-child + multi-layer controls crash** (checkbox on create, slider on interact) — the single-proc creation still doesn't establish the full class context these need.
3. **No working teardown** — `destroy_ui_component_by_frame_id` doesn't destroy these native frames; the real close/destroy path needs RE.

### 🔬 SELECTABLE-LIST CRASH — ROOT CAUSE + NATIVE RECIPE (radio + hyperlink)

**Confirmed via Ghidra (`/Gw.exe (06-14)`):** the selectable frame-list selection state is a
per-instance struct allocated ONLY by the selectable proc's **init (msg 9)** case:

```
CCtlFrameListSelectable::FrameProc  FUN_00613850
  case 9 (init):  if (*(prop) == 0) { p = alloc(CtlFrameList.cpp:0x3e6); *p=frame; p[1]=0; *(prop)=p; }
                  else FUN_00487a80(0x3e5)   // assert if already inited
  case 0x69 (GetSel): s = FUN_00613b30(prop); *out = s[+4]; out[1] = s[+8];   // s[+8] = selected code
  case 0x6A (SetSel): s = FUN_00613b30(prop); FUN_00613b60(s, code);          // highlights row
FUN_00613b30(prop):  if (*(*prop) == 0) FUN_00487a80(CtlFrameList.cpp:0x3f8) NO-RETURN;  // ← THE CRASH
```

If init (msg 9) never runs for the inner selectable proc, `*(prop)` stays 0 and the **first**
`GetSel`/`SetSel` triggers the `0x3f8` assert → hard crash. This is exactly:
- **radio** → `SetFrameListSelection` (apply default) at create → crash immediately.
- **hyperlink** → renders fine, then the per-frame `GetFrameListSelection` poll → crash.

**Native constructor (authoritative) — `CCtlFrameListSelectable` create @ `FUN_00619b70`:**
```
copy 7-dword page-context template from PTR_thunk_FUN_00617df0_00a50600
FUN_0062ef40(parent, 0x64, 0, tmpl)                 // parent size-query → layout param tmpl[1]
pageCtx = { 0, &LAB_00612b90 /*sel proc thunk*/, 0 }  // == our PageCtx {field_0,field_4,field_8}
frame = FUN_0062bfc0(parent, 0x20128, 0, tmpl[1], &pageCtx, 0)   // ← FLAGS 0x20128, not 0x20000
FUN_0062f5a0(frame, 0xffffffff)                     // finalize (FUN_00647db0 + FUN_0064d670)
… add items …
FUN_00612c30(frame, FUN_00617940)                   // install selection-changed handler
```

The `{0, sel_proc, 0}` page context we already build is **correct**. The gap is the create
**flags**: native uses **`0x20128`** (`0x20000 | 0x100 | 0x20 | 0x08`); those extra bits drive
the create to dispatch **init (msg 9)** to the inner selectable proc → state allocated → selection
read/write safe. **Fix applied (2026-07-01):** `CreateSelectableScrollableContentByFrameId` now
forces `component_flags | 0x128`. If radio/hyperlink still crash after this, the remaining recipe
pieces (parent size-query `tmpl[1]`, `FUN_0062f5a0` finalize, `FUN_00612c30` handler) must also be
replicated — they are documented above.

### 🛠️ SWARM RE FIXES — ALL REMAINING CONTROLS (2026-07-01, Ghidra-driven)

A 21-agent Ghidra swarm root-caused every remaining broken control. All fixes decompiler-backed,
compiled, shipped. Root cause → fix, per control:

- **checkbox** (`CreateCheckboxChildByFrameId`): **the `0x40000` "paint-gate" theory was WRONG and is
  the actual bug (corrected 2026-07-01).** `0x40000` gates only the raised BUTTON FACE (msg `0x01`
  sub-pass 0 in `FUN_00877e60`); the CHECK glyph is drawn by sub-pass 1 and is NOT gated by it. So
  `0x48300` made the checkbox render as a *button* — the "cancel-button / wrong glyph" seen in-client.
  Ground truth: GW's own Options checkboxes (`CDlgOptGeneral::OnFrameCreate` @ WASM `80fcf105`) use
  `FrameCreate(parent, 0x10000, childId, UiCtlBtnProc, textId, name)` — `0x10000` is an auto-size-width
  LAYOUT flag, no `0x40000`, no `0x8000` (default glyph). **Fix:** pass `0x10000` to `CreateCheckboxFrame`
  (which ORs `0x8000`) → effective `0x18000`. `EnsureBtnCheckImageList` is KEPT (guarded on `*g==0`, it
  triggers the proc's own msg-`0x05` build so pass-1's `DAT_010819cc` deref is safe on a cold session).
- **radio** (`GWUI.CreateRadioGroup`): two asserts. (1) selected by the AddItem **frame-id**, but the
  selectable list looks up by the create-time **child KEY = insert_index** → `FUN_00613b60` assert 0x428.
  (2) rows were **text labels**; the highlight sends child msg 0x57 with a null out-ptr → CtlTextProc
  asserts 0xcc. **Fix:** rows are now **flat buttons** (CtlBtnProc, null-safe 0x57) added with
  `insert_index = i+1`, and selection uses those keys (`codes[i]=i+1`).
- **hyperlink** (`AddClickableTextButtonToSelectableList`): rows used **CtlTextBtnProc** (0x00616c00),
  whose case 0x57 **writes through the null wparam** the list passes on hover-highlight → hover crash.
  **Fix:** build rows with **CtlTextSelectable** (FUN_00617df0, null-safe 0x57, still notifies parent 8),
  item flags `0xe001` — the engine's own selectable-row proc. New resolver `ResolveCtlTextSelectableProc`.
- **edit** (`CreateEditBoxChildByFrameId`): correct proc (0x008852e0) but `FrameSetSize` is overwritten
  to 0×0 by the window layout → nothing draws. **Fix:** size via the **anchor-6 setter** (0x0062F770),
  same as the slider.
- **tabs** (`CreateTabsFrameByFrameId`): `TabsFrame::Create` installs only the **base** CtlPageProc,
  whose add-item config table has zero styling slots → flat tab buttons. **Fix:** layer the **styled page
  proc** UiCtlPageProc (FUN_00885590) via `FrameNewSubclass` before AddTab (keeps flags `0x40000`, NOT
  the game's count-gated `0x42300`); it subclasses each tab button with the textured proc FUN_00885340.
  New resolver `ResolveUiCtlPageProc`.
- **slider leak** (new `DestroySliderControlByFrameId`): CtlSliderProc registers an **auto-scroll CTimer**
  on a groove click (case 0x24) that the destroy path (case 0xb) never unregisters → orphaned repeating
  timer on freed memory = crash after fiddling. **Fix:** send synthetic mouse-up (msg 0x2e) to release
  the timer BEFORE destroy. (Value polling msg 0x58 is a pure read — untouched. Width fix stays.)
  *Open:* an in-drag leak may persist if the window doesn't deliver mouse-up during a groove drag.
- **destroy all** (`DestroyUIComponentByFrameId`): GWCA's `DestroyUIComponent_Func` **never resolves** on
  this build — its resolver scans for file path `\Code\Gw\Ui\Frame\FrApi.cpp` but the build renamed it to
  `\Code\Engine\Frame\FrApi.cpp` → NULL func ptr → silent no-op. **Fix:** call the public id-based native
  destroyer **FUN_0062c550** (`__cdecl(frame_id)`) directly.

---

## ⚠️ CORRECTED MODEL (2026-06-30) — READ THIS FIRST; IT SUPERSEDES THE OLD MODEL BELOW

This document's original model (Sections 1–10 below) is **faulted**. It was derived largely from WASM symbol *interpretation* and led to many failed button attempts (no button ever rendered). The corrected model here was verified by tracing a **real, working in-game button** — the NPC dialog choice buttons (`IUi::Game::Npc::CInteractTextFrame::ButtonCreate` @ WASM `ram:815623f8`) — and its supporting functions, decompiled against `Gw.wasm` (the symbol-bearing twin of the 06-14 EXE).

### ✅ CONFIRMED WORKING IN-CLIENT (2026-06-30)

A clickable native element was rendered in-client for the first time, by creating a
frame-list **ITEM** whose item proc is `CtlTextBtnProc` (engine text-button), via the same
`CtlFrameListCreateItem` path the working text label uses. Confirmed live:

- **The frame-list item path is the correct way to place a control.** The frame list
  internally performs the `FrameCreate` (msg `0x57`) with flags|`0x300` **in its managed
  parent context**. A **bare `FrameCreate` of a control directly into a window CRASHES the
  client** (no parent context) — verified by crash. Never create standalone controls with a
  bare `FrameCreate`.
- **The caption must be an ENCODED payload** (`BuildStandaloneLiteralEncodedTextPayload`),
  never a raw wide string — raw text crashes.
- **`CtlTextBtnProc` renders as a hyperlink-style text button** (light-blue text `0xff64beeb`,
  hover `0xff78d2ff`); clickable, but no pressed visual.
- **C++ piping added:** `UIManager::ResolveCtlTextButtonProc` + `AddButtonItemToFrameListByFrameId`
  (`include/py_ui.h`), bound to Python as `add_button_item_to_frame_list_by_frame_id`
  (`src/py_ui.cpp`).

**Non-hyperlink button (RESOLVED 2026-06-30):** the flat engine button `CtlBtnProc`
(EXE `0x0060f4f0`, WASM `ram:80dbe9be`) paints a **solid rectangle** (msg `0x01` →
`GrBuildSolidMaterial`), is a single self-contained proc (no multi-layer crash), and has
**no `s_btnCheckImageList` dependency**. Created as a frame-list item, caption set via msg
`0x5E`, sized via `FrameSetSize`. Its pushed/checked state is read via msg `0x59`
(`is_button_pushed_by_frame_id`) — the engine's own click state, no overlay hit-test.
`item_flags` `0x10000` = toggle, `0x80000` = momentary. C++: `ResolveCtlBtnProc` +
`AddFlatButtonItemToFrameListByFrameId` + generic `AddControlItemByFrameId` (py_ui.h).

**All controls:** see **`docs/RE/ui_elements_creation_recipes.md`** — a per-element
creation-recipe reference (proc, resolver, render verdict, interaction, risks) produced by a
12-agent research swarm, covering flat/styled button, checkbox, radio, slider, scrollbar,
editable text, progress, tabs, group header, text label — all from this frame-list-item
primitive. Test harness: `UI_RE/ui_elements_test.py`.

### The real architecture: controls are C++ classes, not bare FrameProcs

GW UI controls (buttons included) are **C++ classes instantiated through the `TCtlInstance<T>` template**. The thing you register with `FrameCreate` is the class's `TCtlInstance<T>::MsgProc`, which dispatches engine messages to the class's member handlers. Each control class provides:

- `OnFrameClassInitialize()` — one-time, assertion-guarded class-level resource setup (e.g. image lists). **Self-triggered from the class's own `MsgProc`** (verified: `CInteractButtonFrame::OnFrameClassInitialize` @ `ram:81560a1a` is called from `TCtlInstance<CInteractButtonFrame>::MsgProc` @ `ram:815627c8`). The game's own classes are therefore already initialized from normal play.
- `TCtlInstance<T>::MsgProc` — **the FrameProc** registered with `FrameCreate`.
- `OnFrameCreate / OnFrameSize / OnFrameSizeQuery / OnFrameNotify / OnFrameMouseFocusChanged / OnCtlLayout …` — member handlers.

### The real creation call (verified, working button)

```c
// from CInteractTextFrame::ButtonCreate
uint btn = FrameCreate(parentFrameId, 0x300, childId, classMsgProcIndex, userDataStruct, /*name*/0);
FrameSetUserParam(btn, payload);
FrameSort(btn, 1, prevSibling);   // layout sizes it — NO FrameSetSize
```

- **Style flags = `0x300`** (F_VISIBLE | F_ENABLED). NOT `0x40300` / `0x40302` / `0x40000`.
- **FrameProc = the class MsgProc** (a function pointer). In the working button it is table index `0xfd2` = `TCtlInstance<CInteractButtonFrame>::MsgProc`. NOT `CtlBtnProc` / `UiCtlBtnProc`.
- **No `FrameSetSize`** — control classes self-size via `OnFrameSizeQuery` / `OnCtlLayout`.
- `userData` carries the control payload; `childId` identifies it for click dispatch.

### Function pointers, not "type addresses" (the central correction)

`FrameCreate`'s 4th param and `FrameNewSubclass`'s 2nd param are both typed `void (*)(FrameMsgHdr const&, void const*, void*)` — **function pointers**. In WASM a function pointer is encoded as an **indirect-call table index**, so every `&DAT_ram_0000XXXX` in the old model is just such an index = a function pointer. There is **no separate "type-address registry".**

Index ↔ function mapping (table byte offset = index × 4), verified by xref:

| Symbol / index | Function | Table byte |
|---|---|---|
| `0xa9d` | `IUi::UiCtlBtnProc` (styled wrapper) | `0x2a74` |
| `0xa7c` | `CtlBtnProc` (engine primitive) | `0x29f0` |
| `0xa56` | `CtlTextBtnProc` (text button) | `0x2958` |
| `0xfd2` | `TCtlInstance<CInteractButtonFrame>::MsgProc` (a real button) | `0x3f48` |

### Verified EXE addresses (Gw.exe 06-14 build) + runtime resolvers

| Symbol | EXE addr | Runtime resolver (Scanner) |
|---|---|---|
| `CtlTextBtnProc` (self-rendering text button — USE THIS) | `0x00616c00` | `Find("\x83\xC0\xFC\x83\xF8\x5C\x0F\x87") → ToFunctionStart(0x20)` (pattern unique) |
| `UiCtlDlgProc` (the real OnFrameNotify dialog subclass — for clicks) | `0x00876880` | `Find("\x55\x8B\xEC\x81\xEC\x20\x01\x00\x00\xA1????\x33\xC5\x89\x45\xFC\x8B\x45\x10\x53\x56\x8B\x75\x08\x57")` (unique; wildcard = security cookie). Fallback: `FindAssertion("UiCtlDlg.cpp", …)` |
| `FrameCreate` / `CreateUIComponent` | `~0x0062bfc0` | existing pattern `33 d2 89 45 08 b9 c8 01 00 00` → ToFunctionStart |
| `FrameNewSubclass` | resolved | existing `FindAssertion("FrApi.cpp","frameId",0x467)` |
| ~~`0x00851180`~~ **(the old `DIALOG_SUBCLASS_TYPE_ADDR` — DELETE IT)** | — | **NOT a proc.** It is `0x20` bytes *into* `FUN_00851160`, a 38-byte stub (`0x00851160–0x00851186`). Installing it as a subclass jumps mid-stub → garbage/crash. This is the click bug. |

To enable clicks on a custom window: `FrameNewSubclass(parentWindow, UiCtlDlgProc[0x00876880], 0)` — NOT `0x00851180`.

### Why every previous attempt failed

- Registered the **wrong object**: `CtlBtnProc` (0xa7c) is the bare engine primitive; `UiCtlBtnProc` (0xa9d) is a multi-layer paint wrapper that needs `s_btnCheckImageList` (built lazily only when a Store window opens → cold creation reads an uninitialized handle, producing the "header texture"/garbage). Neither is a complete control-class MsgProc, so neither renders cold.
- Used **wrong flags** (`0x40000` etc.) instead of `0x300`.
- Chased the **nonexistent "type address vs function pointer" gap** (a WASM table-index misread) instead of the real issue.
- Wired clicks to `DIALOG_SUBCLASS_TYPE_ADDR = 0x00851180`, which is **CRProc** — already installed by `GWUI.CreateWindow` → double-subclass crash. The real dialog OnFrameNotify proc is the EXE equivalent of `&DAT_ram_00000aed` (a *different* function; see §3, still to be resolved/mapped).

### What was already correct

The **click dispatch chain** (§6) is verified accurate: `ICtlBtn::Click` (`ram:80dc36b3`) ends in `FrameMsgNotifyParent(parent, 7/8/9, userData)`; the parent must carry an OnFrameNotify handler. `DialogShow` (`ram:815cdb8c`) installs that handler via `FrameNewSubclass(frame, &DAT_ram_00000aed, userData)`. For control classes, the class's own `OnFrameNotify` member serves this role.

### Viable paths forward (in order of simplicity)

1. **Reuse the engine primitive correctly** — `FrameCreate(parent, 0x300, childId, CtlBtnProc(0xa7c), userData, name)` into a parent that already dispatches OnFrameNotify (a real game window/dialog), shown + sized via the engine. Simplest renderable + clickable button; CtlBtnProc msg 0x01 paints a flat solid rect (`GrBuildSolidMaterial`) self-contained.
2. **Reuse a real control class** — `FrameCreate` with an existing already-initialized class MsgProc; must satisfy that class's `userData` contract and parent expectations.
3. **Frame cloning** — clone an existing button subtree from a live window (Trade/Options); inherits correct class, initialized resources, and a click-dispatching parent.

> Everything below this line is the ORIGINAL faulted model, retained only for its verified low-level data (addresses, struct layouts, click chain). Treat its "Path A / Path B", "type registry", flag values, and "GWCA Gap" framing as **superseded**.

---

## Overview (ORIGINAL — superseded)

This document specifies the COMPLETE process for inserting an arbitrary clickable button with text caption into a native Guild Wars UI window. It covers both the styled GW button (Path A) and the flat engine button (Path B), the rendering pipeline, the click dispatch chain, the type-registry system, and the OnFrameNotify mechanism required for click handling.

Previous projects (native-button-re, native-window-elements-creation, click-handling, ui-elements, window-contents) attempted button creation but all got blocked.

---

## 1. The Two Dispatch Systems

Every frame has TWO independent dispatch mechanisms:

| | FrameProc (Messages) | OnFrameNotify (Notifications) |
|---|---|---|
| **Where** | FrameProc function at `frame+0x08` | CMsg dispatch table at `frame+0xA8` |
| **Trigger** | `FrameMsgSend(frame, msgId, ...)` | `FrameMsgNotifyParent(frame, notifyId, ...)` |
| **Message IDs** | `0x01`–`0x58` | `7` (push), `8` (checked/click), `9` (unchecked) |
| **CContainerFrame** | ✅ Has it | ❌ **Empty** — zero entries |
| **Party Formation** | ✅ Has it | ✅ Has it (type `0x10b1`) |
| **Trade Window** | ✅ Has it | ✅ Has it (type `0x0a4c`) |

**Critical**: CContainerFrame has NO OnFrameNotify. When a child button calls `FrameMsgNotifyParent(7/8/9)`, the parent's CMsg::Notify walks the empty dispatch table and returns silently. Clicks are swallowed with zero feedback.

---

## 2. Architecture: Type Registry & Frame Creation

### 2.1 FrameCreate — The Universal Factory

**WASM**: `FrameCreate` @ `ram:809a13ea`  
**Signature**: `uint FrameCreate(uint parentId, uint style, uint childId, void* callback, void const* userData, wchar_t const* name)`

Internal flow (7 steps):
1. Resolve parent (gets root if `parentId == 0`)
2. `MemAlloc(0x1C8 = 456 bytes)` — allocates frame struct
3. `IFrame::Frame()` constructor
4. `IFrame::CMsg::Create(callback, userData)` — registers FrameProc
5. `IFrame::CState::Set(4, 0, 0)` — initial state
6. `IFrame::CMsg::Notify(2)` — triggers `OnFrameCreate` (msg `0x02`)
7. `IFrame::CMsg::Dispatch(10)` — self-registration (msg `0x0A`, type registry)

### 2.2 The GWCA Gap — Fatal Flaw

GWCA passes a **function pointer** (`IUi::UiCtlBtnProc`) as the `callback` parameter. The game passes a **type address** (`&DAT_ram_00000a9d`) — a compile-time BSS sentinel that serves as a type-registry key. This single difference cascades into every failure:

| What | GWCA (Crashes) | Game (Works) |
|------|---------------|--------------|
| FrameCreate callback | `IUi::UiCtlBtnProc` function ptr | `&DAT_ram_00000a9d` type address |
| Type registry | Bypassed entirely | Type → msg 0x0A → msg 0x04 → self-registration |
| s_btnCheckImageList | Never created | Created by msg 0x05 broadcast at startup |
| Image paths | PTR_DAT pointers uninitialized | Runtime-initialized from DAT |
| Subclasses | None applied | FrameNewSubclass(type, flags) per-window |

### 2.3 Key Type Addresses

| Address (WASM) | Numeric Value | Role | References |
|---|---|---|---|
| `&DAT_ram_00000a9d` | `0x0a9d` (2717) | **BUTTON type** — primary styled button identifier | 37+ FrameProcs |
| `&DAT_ram_00000a7c` | `0x0a7c` (2684) | **CtlBtn class** — returned by msg 0x04 self-registration | 15 refs |
| `&DAT_ram_00004300` | `0x4300` (17152) | **IME/alternate button type** | 25 refs |
| `&DAT_ram_00000aed` | `0x0aed` (2797) | **Dialog subclass** — adds OnFrameNotify | Used by DialogShow |

All are BSS (zero-value at load). They serve as compile-time type IDs — NEVER modified at runtime. In WASM, these resolve to function table indices for `call_indirect`.

### 2.4 The Universal Button Creation Pattern

From analyzing 10 game windows:
```c
FrameCreate(
    parent,              // window frame ID
    0x40300,            // style flags (varies: Store=0x40302)
    childIndex,         // unique child ID → used as click identifier!
    &DAT_ram_00000a9d,  // TYPE ADDRESS
    TextEncode(stringId), // encoded label text
    L"BtnName"          // debug name
);
```

Style flags vary by window: Trade=`0x40300`, Store=`0x40302`, and some windows use custom types (`0x10ad`–`0x10b0`) instead of the standard button type.

---

## 3. OnFrameNotify: The Click Handler System

### 3.1 What It Is

OnFrameNotify is a **CMsg-level callback** — NOT a FrameProc message handler. It's registered in the frame's CMsg dispatch table at `frame+0xA8`.

**Signature**: `void OnFrameNotify(FrameMsgNotify const& notify)`

**FrameMsgNotify struct** (12 bytes):
```
+0x00: uint frameId    — sender's frame ID
+0x04: uint childId    — sender's child ID (FrameCreate param3)
+0x08: uint notifyId   — 7=push, 8=checked/click, 9=unchecked
+0x0C: void* userData  — additional data
```

### 3.2 How It's Registered

```c
FrameNewSubclass(parentFrameId, &DAT_ram_00000aed, 0);
```

Internal chain:
1. `IFrame::CMsg::GetFrame(parentFrameId)` — validates frame
2. `IFrame::CMsg::NewSubclass(frame+0xA8)` — allocates 12-byte entry
3. `IFrame::CMsg::SetSubclass(frame+0xA8, index, &DAT_ram_00000aed, 0)` — stores `{handlerId=0x0aed, data=0, flags|0x80000000}`

`&DAT_ram_00000aed` is the "dialog subclass" type — used by `DialogShow` for EVERY floating dialog window. It's a function table index (2797) pointing to `DlgMsgProc`, the monolithic dialog handler that includes OnFrameNotify.

### 3.3 Dispatch Flow

```
ICtlBtn::Click(buttonId)
  → FrameMsgNotifyParent(buttonId, notifyId=8, 0, 0)
    → parent's frame+0xA8 → CMsg
    → CMsg::Notify(parentCmsg, notifyId=8, ...)
      → handlerId = DAT_ram_005a036c[8]  // global notifyId→handlerId table
      → walk CMsg entries matching handlerId
      → call table[handlerId](FrameMsgNotify{childId=X, notifyId=8, ...})
        → DlgMsgProc dispatches → action
```

Dispatch by childId pattern:
```cpp
void OnFrameNotify(FrameMsgNotify const& notify) {
    switch (notify.childId) {
        case 0: handleAccept(); break;
        case 1: handleCancel(); break;
        // ...
    }
}
```

### 3.4 Key Addresses

| Function | WASM | Role |
|----------|------|------|
| `FrameNewSubclass` | `ram:809a2ebf` | Register subclass handler |
| `CMsg::NewSubclass` | `ram:80972189` | Allocate CMsg entry |
| `CMsg::SetSubclass` | `ram:809771b5` | Store handler in entry |
| `CMsg::Notify` | `ram:80974c3c` | Resolve notifyId → dispatch |
| `FrameMsgNotifyParent` | `ram:809b899e` | Validate notifyId≥7, call Notify |
| `DAT_ram_005a036c` | (BSS) | Global notifyId→handlerId table |
| `DAT_ram_005a038c` | (BSS) | Global sorted handler registry |
| `DAT_ram_005a0338` | (BSS) | Registration hash table |

---

## 4. Path A: Styled GW Button (IUi::UiCtlBtnProc)

### 4.1 FrameProc

**WASM**: `IUi::UiCtlBtnProc` @ `ram:80df1d1e`  
**Type**: `&DAT_ram_00000a9d` (BUTTON type)  
**Class**: `&DAT_ram_00000a7c` (CtlBtn class, self-registered via msg 0x04)

28-message state machine. Key handlers:

| Msg | What It Does |
|-----|-------------|
| `0x01` | **PAINT** — Sub-0 (background template, `*param2==0`) or Sub-1 (state images + text, `*param2==1`) |
| `0x04` | Self-registers class type `&DAT_ram_00000a7c` |
| `0x05` | **CREATE IMAGE LIST** — `FrameImageListCreate` → `s_btnCheckImageList` |
| `0x09` | Create — delegates to CtlBtnProc base (allocates Property) |
| `0x38` | Min-size enforcement (100px or 120px depending on style) |
| `0x5F` | Sub-1 paint (state images + text) |

### 4.2 Rendering Pipeline

**Sub-0 (Background Template):**
```
FrameContentAddImageTemplate(frame, rect, &PTR_DAT_ram_0102112b,
    &DAT_ram_005a8520{32,32}, texOp=7, layer=0, &modelHandle)
  → 9-slice grid (3×3 corners)
  → IModelBuildCorners (UV computation + 108-byte vertex buffer)
  → GrGeosetCreate → GrModelCreate
  → CContent::AddModels
```

**Sub-1 (State Images + Text):**
```
State = 6-index lookup into s_btnCheckImageList:
  Index 0: Disabled + checked/pushed
  Index 1: Disabled + normal
  Index 2: Enabled + checked + pushed
  Index 3: Enabled + checked + not pushed
  Index 4: Enabled + not checked + pushed
  Index 5: Enabled + normal (default)

FrameContentAddImage(frame, rect, s_btnCheckImageList[stateIdx], layer, &modelHandle)
FrameContentAddText(frame, text, ..., color=0xffa0a0a0, ..., layer=6)
```

### 4.3 s_btnCheckImageList

**Handle stored at**: `_DAT_ram_005a857c` (WASM), `0x010819cc` (EXE)  
**Created by**: `IUi::UiCtlBtnProc` msg `0x05` handler via `FrameImageListCreate`:
```
FrameImageListCreate(
    0x11,        // EGrPixelFormat
    7,           // EGrTexOp
    0x12,        // 18 sub-images
    {0x15, 0x15}, // subImageSize = 21×21 pixels
    {0x80, 0x20}, // artDims = 128×32 pixels
    &PTR_DAT_ram_0102112a, // wchar_t* image path (BSS, runtime from DAT)
    6            // flags
);
```

**Initialization timing**: Created LAZILY when the first store window opens (`CShop::OnFrameCreate` step 10 → `FrameMsgSendRegistered(0x20000004, ...)`). Assertion `!s_btnCheckImageList` guards against double-creation.

### 4.4 Prerequisites (must exist before Path A button creation)

1. `s_btnCheckImageList` — created by msg `0x05` at game startup
2. Static dimension data — `_DAT_ram_005a84f8` area (0x90 bytes of float constants)
3. Template sub-image size — `_DAT_ram_005a8520` = `Coord2u{32, 32}`
4. Texture image paths — loaded into BSS from DAT at game boot

### 4.5 Key Rendering Functions

| Function | WASM | Role |
|----------|------|------|
| `FrameContentAddImageTemplate` | `ram:809b59c0` | 9-slice template engine |
| `IModelBuildCorners` | `ram:808b3411` | 9-slice geometry builder |
| `CContent::AddModels` | `ram:808ae1a8` | Attach models to frame content |
| `FrameContentAddImage` (HFrameImageList) | `ram:809b2b97` | Render sub-image from image list |
| `FrameContentAddText` | `ram:809b1d48` | Render text on frame |
| `FrameImageListCreate` | `ram:809aca67` | Load texture + create image list |
| `GrBuildSolidMaterial` | `ram:802bc726` | Create solid-color material |
| `GrGeosetCreate` | (in Gr subsystem) | Create geometry set |
| `GrModelCreate` | (in Gr subsystem) | Create render model |

---

## 5. Path B: Flat Engine Button (CtlBtnProc)

### 5.1 FrameProc

**WASM**: `CtlBtnProc` @ `ram:80dbe9be`  
**Type**: `&DAT_ram_00000a7c` (CtlBtn class)

Key handlers:
- `0x01`: Paint — `GrBuildSolidMaterial(Color4b)` → flat rectangle
- `0x09`: Create — allocates `ICtlBtn::Property` (0x2C bytes)
- `0x24`: Mouse down → `ICtlBtn::Click`
- `0x5E`: Set text literal → `FrameContentAddText`
- `0x56`: Programmatic click (same path as mouse)

### 5.2 Why It Renders as Thin Strip

`CtlBtnProc` has **NO msg 0x38 (min-size) handler**. IUi::UiCtlBtnProc enforces 100-120px minimum width. Without it, the frame's CRect stays at `{0,0 → 0,0}` → zero dimensions → renders as 1px strip.

**Fix**: Call `FrameSetSize(buttonId, {width, height})` after creation.

### 5.3 ICtlBtn::Property Struct (0x2C bytes)

| Offset | Type | Field |
|--------|------|-------|
| `+0x00` | `uint32` | `stateFlags` — bit 0 = checked/pushed |
| `+0x04` | `HFrameImageList` | `imageList` |
| `+0x08` | `uint32` | `imageSubIndex` |
| `+0x0C` | `TArray<wchar_t>` | `textBuffer` |
| `+0x1C` | `uint32` | `textColor` |

### 5.4 What's Missing vs Path A

| Feature | Path A | Path B |
|---------|--------|--------|
| 9-slice template | ✅ | ❌ |
| State images (hover/push/check) | ✅ (6-state lookup) | ❌ |
| Min-size enforcement | ✅ (msg 0x38) | ❌ (must call FrameSetSize) |
| Text integrated in paint | ✅ (Sub-1) | ✅ (msg 0x5E) |
| Click pipeline | ✅ | ✅ (shared ICtlBtn::Click) |
| DAT texture dependency | ✅ (crash if missing) | ❌ (solid color only) |

---

## 6. The Click Pipeline

### 6.1 ICtlBtn::Click

**WASM**: `ICtlBtn::Click` @ `ram:80dc36b3`  
**Signature**: `void ICtlBtn::Click(uint frameId, ICtlBtn::Property* prop)`

```
1. FrameIsEnabled(frame) → bail if disabled
2. FrameTestStyles(frame, 0x10000) → TOGGLE:
     *property ^= 1, invalidate, schedule size
     FrameMsgNotifyParent(frame, 8 or 9, 0, 0)
3. FrameTestStyles(frame, 0x80000) → MOMENTARY:
     *property |= 1, invalidate, schedule size
     FrameMsgNotifyParent(frame, 8, 0, 0)
4. If parent has style 0x100000 (CHECKBOX parent):
     Enumerate children with class &DAT_ram_00000a7c → send msg 0x57
5. FALLBACK: FrameMsgNotifyParent(frame, 7, 0, 0) — push notice
```

Notify IDs: **7** = push (always sent), **8** = checked/click, **9** = unchecked.

### 6.2 Programmatic Click

**WASM**: `CtlBtnClick` @ `ram:80dc46b0`  
Sends `FrameMsgSend(buttonId, 0x56, 0, 0)` — identical code path to real mouse click, bypasses bounds check.

### 6.3 Reference Windows

**Party Formation**: `CFormationFrame::OnFrameNotify` @ `ram:816d6577`
- notifyId 8 + childId X → GetChild(0) → msg 0x61 → invite action

**Trade Window**: `CTradeFrame::OnFrameNotify` @ `ram:815a4a4e`
- childId 0 + notifyId 7 → SubmitOrModify
- childId 1 + notifyId 7 → FrameClose (Cancel)
- childId 2 + notifyId 7 → TradeCliConfirm (Accept)

**Options Dialog**: `CDlgOptGeneral::OnFrameNotify` @ `ram:80fd7cb5`
- childId 8 → PrefSetFlag(ON), childId 9 → PrefSetFlag(OFF)

---

## 7. Complete Button Insertion Pipeline

### Phase 1: Parent Window + OnFrameNotify

```c
// Step 1A: Create parent window
uint windowId = FrameCreate(0, chromeStyle, childIdx, CContainerFrameProc, 0, L"Window");

// Step 1B: Add OnFrameNotify (CRITICAL — skip this and clicks silently die)
FrameNewSubclass(windowId, &DAT_ram_00000aed, 0);
```

### Phase 2: Create Button

```c
// Path A (Styled):
uint buttonId = FrameCreate(windowId, 0x40300, childId, &DAT_ram_00000a9d, textStr, L"Btn");

// Path B (Flat):
uint buttonId = FrameCreate(windowId, styleFlags, childId, &DAT_ram_00000a7c, userData, L"Btn");
```

### Phase 3: Post-Creation

```c
FrameSetSize(buttonId, {width, height});        // CRITICAL for Path B
FrameSetPosition(buttonId, {x, y});
FrameMouseEnable(buttonId, flags, 0);
FrameEnable(buttonId, 1);
FrameShow(buttonId, 1);
```

### Phase 4: Text

```c
// Path A: text provided as userData to FrameCreate (rendered in Sub-1 paint)
// Path B:
CtlBtnSetTextLiteral(buttonId, L"Click Me");  // sends msg 0x5E
```

### Phase 5: Render

```c
FrameContentInvalidate(buttonId);   // trigger paint
FrameScheduleSize(buttonId);        // recalculate layout
```

---

## 8. s_btnCheckImageList Initialization Timing

The image list is NOT created during game boot. It's created LAZILY:

1. Game boot → DAT loading → PTR_DAT pointers populated (BSS, from DAT files)
2. `s_btnCheckImageList = NULL` (BSS initial)
3. User opens store → `CShop::OnFrameCreate` step 10
4. `FrameMsgSendRegistered(0x20000004, 0, &{0})` → broadcast to all CtlBtn-class frames
5. `IUi::UiCtlBtnProc(msg 0x05)` → assert !s_btnCheckImageList → `FrameImageListCreate`
6. `s_btnCheckImageList` = result → all subsequent buttons can use it

**Manual trigger safety**: 
- ✅ Safe if `_DAT_ram_005a857c == NULL` 
- ❌ CRASH (assertion) if already created
- Can destroy first via msg 0x06 if re-creation needed

**Registration mechanism**: `FrameMsgRegister(frameId, 0x20000004)` → `THashTable::Insert(DAT_ram_005a0338, 0x20000004, frame)`.

---

## 9. Gap Inventory

### HIGH Confidence (17 items)
All key function signatures, type addresses, struct layouts, message IDs, and the complete click dispatch chain have been verified through WASM decompilation and cross-referenced across 10 game windows.

### MEDIUM Confidence (6 items)
- Exact style flags for Path B flat button appearance
- FrameCreate callback: function pointer vs type address (decompiled both — runtime behavior differs)
- Exact handler IDs in `&DAT_ram_00000aed`'s monolithic FrameProc (119KB decompilation)
- `DAT_ram_005a036c[7/8/9]` → handlerId mapping (runtime-initialized)
- Whether we can call msg 0x05 manually with custom image path
- CtlBtnProc's `sm_buttonImageList` contents

### UNKNOWN (5 items) — requires runtime debugging
- DAT texture image file paths (BSS, runtime from DAT)
- Type-registry boot state at Python execution time
- Exact crash point for GWCA CreateUIComponent (needs debugger)
- Whether custom minimal OnFrameNotify type can be built
- Exact CtlBtnProc msg 0x01 sub-branch behavior with explicit dimensions

### Runtime-Only (6 items)
DAT texture paths, s_btnCheckImageList runtime state, type registry state, actual pixel dimensions, CMsg handler ID resolution, color values for button states.

---

## 10. Key Address Catalog

### Frame Creation & Registration
| Function | WASM Address | EXE Address (06-14-2026) |
|----------|-------------|--------------------------|
| `FrameCreate` | `ram:809a13ea` | **`0x0060d2d0`** (Ui_CreateLabeledFrame) |
| `FrameNewSubclass` | `ram:809a2ebf` | **`0x00610340`** (Ui_AttachCurrentHandlerSlot) |
| `CMsg::NewSubclass` | `ram:80972189` | — |
| `CMsg::SetSubclass` | `ram:809771b5` | — |
| `CMsg::Notify` | `ram:80974c3c` | — |
| `FrameMsgNotifyParent` | `ram:809b899e` | TBD |
| `FrameMsgSendRegistered` | `ram:809b8869` | TBD |

### Button FrameProcs
| Function | WASM Address | EXE Address (06-14-2026) |
|----------|-------------|--------------------------|
| `IUi::UiCtlBtnProc` (Styled) | `ram:80df1d1e` | TBD |
| `CtlBtnProc` (Flat) | `ram:80dbe9be` | **`0x0060f4f0`** (pattern) |
| `CtlTextBtnProc` (Text-only) | `ram:80d9ce76` | TBD |
| `ICtlBtn::Click` | `ram:80dc36b3` | TBD |
| `CtlBtnClick` | `ram:80dc46b0` | TBD |
| `CtlBtnSetTextLiteral` | `ram:80dc4d8f` | **`0x0060fe60`** (pattern) |

### Type Addresses
| Symbol | WASM | EXE (06-14-2026) |
|--------|------|------------------|
| BUTTON type | `&DAT_ram_00000a9d` | TBD |
| CtlBtn class | `&DAT_ram_00000a7c` | TBD |
| **Dialog subclass** | `&DAT_ram_00000aed` | **`0x00851180`** ← OnFrameNotify! |
| IME alt button | `&DAT_ram_00004300` | TBD |
| CFormationFrame type | `&DAT_ram_000010b1` | TBD |
| CTradeFrame type | `&DAT_ram_00000a4c` | TBD |

### Position/Size/State
| Function | WASM Address | EXE Address (06-14-2026) |
|----------|-------------|--------------------------|
| `FrameSetPosition` | `ram:809a9f40` | FindAssertion FrApi.cpp:0x85c |
| `FrameSetSize` | `ram:809a9c3e` | FindAssertion FrApi.cpp:0x880 |
| `FrameMouseEnable` | `ram:809a44a5` | **`0x0060ffd0`** |
| `FrameEnable` | `ram:809a59f7` | FindAssertion FrApi.cpp:0x683 |
| `FrameShow` | `ram:809a5e39` | **`0x00610d00`** |
| `FrameSetLayer` | `ram:809b060f` | TBD |
| `FrameContentInvalidate` | `ram:809b6dc6` | **`0x0060d090`** |
| `FrameScheduleSize` | `ram:809a92ea` | TBD |

### Rendering
| Function | WASM Address | EXE Address (06-14-2026) |
|----------|-------------|--------------------------|
| `FrameContentAddImageTemplate` (9-slice) | `ram:809b59c0` | TBD |
| `IModelBuildCorners` | `ram:808b3411` | TBD |
| `CContent::AddModels` | `ram:808ae1a8` | TBD |
| `FrameContentAddImage` (HFrameImageList) | `ram:809b2b97` | TBD |
| `FrameContentAddText` | `ram:809b1d48` | TBD |
| `FrameImageListCreate` | `ram:809aca67` | TBD |
| `GrBuildSolidMaterial` | `ram:802bc726` | TBD |

### Global Data (BSS)
| Symbol | WASM | EXE (06-14-2026) |
|--------|------|------------------|
| `_DAT_ram_005a857c` | s_btnCheckImageList handle | TBD |
| `_DAT_ram_005a8520` | Template sub-image size (32×32) | TBD |
| `_DAT_ram_005a84f8` | Dimension data area (0x90 bytes) | TBD |
| `DAT_ram_005a036c` | notifyId→handlerId table | TBD |
| `DAT_ram_005a038c` | Global handler registry | TBD |
| `DAT_ram_005a0338` | Registration hash table | TBD |

### Reference Windows
| Window | OnFrameNotify | FrameProc |
|--------|--------------|-----------|
| Party Formation | `ram:816d6577` | `ram:816dc5d4` |
| Trade | `ram:815a4a4e` | `ram:815a9560` |
| Options General | `ram:80fd7cb5` | — |
| Store (CShop) | — | `ram:81098270` |
| DialogShow (EXE) | — | **`0x004dc1b0`** |
| CContainerFrame | (none) | `ram:812a7233` |
