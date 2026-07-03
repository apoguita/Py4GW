# Guild Wars UI Controls Catalog

> **EXE Version**: 05-30-2026  
> **Project**: UI Elements Universe Discovery (Phases 1–3, 2026-06-04)  
> **Total FrameProc Types Cataloged**: 39

> ## ⚠️ CORRECTION (2026-06-30) — the core creation model in this catalog is wrong
>
> This catalog assumes UI controls are created by passing a single bare FrameProc (e.g. `CtlBtnProc`, `CtlSliderProc`) to `CreateUIComponent`/`FrameCreate`, and that controls "work" if the FrameProc is self-contained. Verification against `Gw.wasm` (tracing real working buttons) shows this is **incorrect** and explains why every cold-creation attempt crashed or failed to render.
>
> **Real model:** GW controls are C++ classes instantiated via the `TCtlInstance<T>` template. The registered FrameProc is the class's `TCtlInstance<T>::MsgProc`, which dispatches to member handlers (`OnFrameCreate`, `OnFrameSizeQuery`, `OnFrameNotify`, …) and self-triggers a one-time `OnFrameClassInitialize()`. The bare procs cataloged here (`CtlBtnProc`, `CtlSliderProc`, etc.) are **engine primitives / paint wrappers**, not the class MsgProcs the game actually registers. Real creation uses style flags **`0x300`** (not `0x300`-as-inferred-default vs `0x8000`/`0x20000` "type flags"; the flag is just F_VISIBLE|F_ENABLED) and relies on the class for sizing/paint.
>
> The "multi-layer FrameProc cannot be created by CreateUIComponent" conclusion (Slider report) is a **symptom** of this: those controls are `TCtlInstance` classes whose base relationships and `OnFrameClassInitialize` are bypassed when you register a raw primitive proc. The `WASM↔EXE FrameProc address` tables and struct layouts below remain useful; the **creation recipe and component_flags interpretation are superseded**. See `native_button_pipeline.md` (top section) for the verified model.

Comprehensive reference of all known Guild Wars engine UI control types, organized by implementation tier. Covers FrameProc addresses, assertion strings, WASM↔EXE mappings, struct layouts, message protocols, and implementation status.

> ## ✅ RESOLVED (2026-07-01) — the "Tier 2 CRASHED" controls are now IMPLEMENTED
>
> The Phase-3 crash narratives below are **historical**. The full control toolkit has since been
> reverse-engineered and implemented in `include/py_ui.h` with the corrected model, and verified
> in-client. **`native_button_pipeline.md` is now the authoritative creation reference** (master
> address/flag/status table + per-control recipes). Current per-control state:
>
> | Control | Was | Now | The fix (Ghidra-verified, 06-14) |
> |---|---|---|---|
> | button (styled) | crashed/blank | ✅ works | styled `UiCtlBtnProc` item + paint gate `0x40000` + `s_btnCheckImageList` |
> | checkbox | crashed | fixed→testing | flags **`0x48300`** (gate `0x40000` + face `0x8000`); warm image list |
> | radio | crashed | fixed→testing | selectable list + **flat-button rows** + select by child KEY `insert_index=i+1` |
> | text-button / hyperlink | click/hover crash | fixed→testing | rows use **`CtlTextSelectable 0x00617df0`** (null-safe 0x57), not `CtlTextBtnProc` |
> | edit | empty | fixed→testing | outer **`CCtlEdit 0x008852e0`** + **anchor-6 sizing** (not `FrameSetSize`) |
> | progress | — | ✅ creates | `SetPercent 0x5B` / `SetValue 0x58` / `SetMax 0x5A` |
> | tabs | crashed | textured→testing | base `CtlPageProc` + layer styled **`UiCtlPageProc 0x00885590`** before AddTab |
> | slider | "cannot create multi-layer" (WRONG) | ✅ works | two-layer create OK; width via anchor-6; **release CTimer via mouse-up `0x2e` before destroy** |
> | group header | crashed | ✅ works | `CGroupHeaderFrame 0x0087ddc0` item in a plain list (self-builds children) |
> | destroy | never worked | fixed→testing | GWCA `DestroyUIComponent` no-ops (resolver path drift) → call native **`FUN_0062c550`** |
>
> Key model corrections vs the tables below: (a) the **selectable frame list** needs create flags
> `0x20128` (not `0x20000`) for its selection state; (b) **direct-child controls** must be sized with
> the anchor-6 setter `0x0062F770`, never `FrameSetSize`; (c) **selectable-list rows** must use a
> NULL-safe row proc; (d) SliderFrame's "conclusive failure" report below is **superseded** — sliders
> create fine via the two-layer typed path.

---

## Architecture: How UI Components Are Created

The engine uses a **three-registration-layers** approach:

| Layer | Function | Role |
|-------|----------|------|
| **FrameProc (Callback)** | `CtlBtnProc`, `CtlDropListProc`, `CtlSliderProc`, etc. | Message handler that paints, handles mouse input, and creates the internal control instance on msg 0x09 |
| **Universal Factory** | `CreateUIComponent` (native) / `FrameCreate` @ `ram:809a13ea` | Allocates a 0x1C8-byte `Frame` struct, registers the FrameProc, sends lifecycle messages |
| **High-Level Wrapper** | `IUi::UiCtlBtnProc`, `IUi::UiCtlDropListProc`, etc. | Adds default styling, sizing, and configuration before delegating to the low-level FrameProc |

**The existing GWCA pattern** (used for Button, Checkbox, Scrollable, TextLabel):
```cpp
// 1. Resolve callback via scanner
ButtonFrame_Callback = Scanner::FindAssertion("UiCtlBtn.cpp", "!s_btnCheckImageList");
// 2. Call universal factory with type-specific flags
CreateUIComponent(parent_id, component_flags | TYPE_FLAG, child_index, CALLBACK, name, label);
```

**Key insight**: The callback (FrameProc) is the **primary type determinant**. `component_flags` add behavior modifiers — `0x8000` = checkbox behavior, `0x20000` = scrollable. `0x300` is the base default (`F_VISIBLE|F_ENABLED`), not type-identifying.

---

## component_flags Reference Table

| Flag Value | Frame Type | Source |
|------------|------------|--------|
| (none) / 0x300 | ButtonFrame (base default) | UIMgr.cpp default |
| 0x8000 | CheckboxFrame (toggle behavior) | UIMgr.cpp `flags \| 0x8000` |
| 0x20000 | ScrollableFrame | UIMgr.cpp `flags \| 0x20000` |
| 0x128 | Dropdown list (internal child listbox) | `CtlDropList::CreateList` |
| 0xA0000 | Text label (GroupHeader child) | OnFrameCreate at `ram:811921df` |
| 0x0AFD | Checkbox callback index (GroupHeader child) | callback address, not flag |

---

## Tier 1: Wrapped (Create + Manipulate) — 4 Types

These types have fully working GWCA wrappers with both Create and Manipulate functions.

| Control | GWCA Struct | Create Function | Manipulate Functions |
|---------|-------------|-----------------|---------------------|
| **ButtonFrame** | `ButtonFrame` | `CreateButtonFrame` | Click, DoubleClick, MouseAction, GetLabel, SetLabel |
| **CheckboxFrame** | `CheckboxFrame` (via ButtonFrame + 0x8000) | `CreateCheckboxFrame` | IsChecked, SetChecked, GetValue, SetValue |
| **ScrollableFrame** | `ScrollableFrame` | `CreateScrollableFrame` | ClearItems, AddItem, RemoveItem, SetSortHandler |
| **TextLabelFrame** | `TextLabelFrame` | `CreateTextLabelFrame` | GetEncodedLabel, GetDecodedLabel, SetLabel, SetFont |

---

## Tier 2: Struct Exists, Create Attempted But CRASHED — 7 Types

These had Create functions implemented across the full stack (GWCA C++ structs, Python bindings, stubs, GWUI wrappers) during Phase 3, but **ALL crashed the client**. The addresses, assertion strings, struct layouts, and component_flags are verified correct — the C++ implementation needs rework.

> **⚠️ SUPERSEDED — see the RESOLVED (2026-07-01) banner above.** Every control in this table has since
> been implemented and no longer crashes (or the crash root cause is fixed and pending in-client
> confirmation). The addresses here remain correct; the "CRASHED/FAILED" verdicts are historical. In
> particular the SliderFrame "conclusive failure / CreateUIComponent cannot create multi-layer FrameProc
> controls" claim is **wrong** — the two-layer typed create (base `CtlSliderProc` + `FrameNewSubclass`
> wrapper) works. `EditableTextFrame` uses the **outer** `CCtlEdit 0x008852e0`, NOT the render subclass
> `0x00888aa0`. `TabsFrame` needs the styled `UiCtlPageProc 0x00885590` layered over base
> `CtlPageProc 0x0061a950`. See `native_button_pipeline.md` for the working recipes.

| Control | EXE FrameProc | Assertion | component_flags | Struct | Status |
|---------|--------------|-----------|-----------------|--------|--------|
| **DropdownFrame** | `0x0087f5f0` | `"!FrameGetChild(thisFrame, CTL_LIST_ENTRIES)"` | 0x128 (child listbox) / 0x300 (wrapper) | `CtlDropList::Prop`, 100 bytes | **CRASHED** |
| **SliderFrame** | `0x00615fe0` (base) + `0x0087f440` (wrapper) | `"value >= m_range.min"` (base) / byte pattern for wrapper | 0 (game uses 0) | `CtlSlider::CInstance`, 0x30 bytes | **FAILED** — Conclusive. CreateUIComponent cannot create multi-layer FrameProc controls. See SliderFrame Failure Report below. |
| **EditableTextFrame** | `0x00888aa0` | `"!s_editCaretMaterial"` | 0x300* | `CCtlEdit`, ~0x4C bytes | **CRASHED** |
| **ProgressBar** | `0x008812e0` | `"!sm_rateArrowImageList"` | 0x300* | Inherits ButtonFrame+FrameWithValue | **CRASHED** |
| **TabsFrame** | `0x0061a950` | `"!IsBtnCode(pageCode)"` | 0x300* | `CtlPage::CCtlPage` | **CRASHED** |
| **MultiLineTextLabel** | `0x00610c40` | `"FrameTestStyles(hdr.frameId, CTLTEXT_STYLE_MODEL)"` | same callback as TextLabelFrame (layout distinguishes) | 0x170 bytes | **CRASHED** |
| **GroupHeader** | `0x0087ddc0` | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlGroupHeader.cpp"` | composite (creates children internally) | new GWCA struct needed | **CRASHED** |

(* = inferred, needs verification from FrameCreate caller)

### DropdownFrame (CtlDropList::Prop)

| Offset | Type | Field |
|--------|------|-------|
| +0x00 | void* | item_list_ptr |
| +0x08 | uint32 | item_count |
| +0x0C | uint32 | max_items |
| +0x10 | uint8[32] | char_flags |
| +0x14 | uint32 | flags (bit 0 = disabled) |
| +0x58 | uint32 | selected_index |

**UIMessage IDs**: 0x01, 0x04, 0x08, 0x09, 0x0B, 0x0C, 0x20, 0x31, 0x56, 0x57, 0x5B, 0x5D, 0x61, 0x68, 0x69  
**Manipulation gaps**: Open list, Close list, Get item text at index, Set sort handler, Set max list height, Set user param

### SliderFrame (CtlSlider::CInstance, 0x30 bytes)

| Offset | Type | Field |
|--------|------|-------|
| +0x00 | float | position |
| +0x04 | float | thumb_size |
| +0x08 | float | bar_start |
| +0x0C | uint32 | min |
| +0x10 | uint32 | max |

**Manipulation gaps**: SetRange(min,max), GetRange, SetOrientation

### EditableTextFrame (CCtlEdit, ~0x4C+ bytes)

| Offset | Type | Field |
|--------|------|-------|
| +0x00 | void* | text_buffer |
| +0x04 | uint32 | text_length |
| +0x08 | uint32 | max_chars |
| +0x14 | uint8 | read_only |
| +0x18 | void* | prompt_text |
| +0x48 | wchar_t* | text_value |

**UIMessage IDs**: 0x03, 0x10-0x14, 0x38, 0x3A, 0x56, 0x5A, 0x5B, 0x5E, 0x62-0x64  
**Manipulation gaps**: SetPromptText, Get/SetSelection, SetCharMarkups, GetTextLen, Cut/Copy/Paste

### ProgressBar

Inherits: `ButtonFrame` + `FrameWithValue`  
**Manipulation gaps**: SetText, SetIncrementsPerSecond, GetMax, GetPercent

### TabsFrame (CtlPage::CCtlPage)

| Offset | Type | Field |
|--------|------|-------|
| +0x00 | void* | active_frame |
| +0x04 | uint32 | active_index |
| +0x08 | uint32 | tab_count |
| +0x0C | void* | items_array |

**Manipulation gaps**: HideButtons, ShowButtons, SetTabLabel

### MultiLineTextLabelFrame (CtlTextMl, 0x170 bytes)

| Offset | Type | Field |
|--------|------|-------|
| +0x00 | void* | m_encodedText |
| +0x08 | uint32 | m_textLen |
| +0x10 | uint32 | m_sourceIndex |
| +0x14 | uint8 | m_separateLines |
| +0x148 | void* | m_anchorParams |
| +0x158 | void* | m_imageRects |

**Note**: Same callback as TextLabelFrame. Distinction is in layout template, not flags.

### GroupHeader (Composite Control)

**EXE FrameProc**: `0x0087ddc0`  
**WASM**: `IUi::CGroupHeaderFrame::FrameProc` @ `ram:81192c89`  
**Assertion**: `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlGroupHeader.cpp"` @ `0x00b96100`

**Composite design**: Creates 2 children internally on msg 0x09:
- Child 0: Checkbox (callback 0x0AFD)
- Child 1: Text label (callback 0x0A56, flags 0xA0000)

**Message protocol** (validated):
| Message ID | Command | Direction |
|-----------|---------|-----------|
| 0x56 | GetIsOpen | Query |
| 0x57 | SetIsOpen | Command |
| 0x58 | GetText | Query |
| 0x59 | SetText | Command |

**Priority**: HIGHEST — most useful unwrapped control for custom UI panels.

---

## Tier 3: Cosmetic/Internal — 6 Types with Addresses

| Control | EXE FrameProc | WASM Symbol | Assertion | Utility |
|---------|--------------|-------------|-----------|---------|
| **TextShy** | `0x0087f0d0` | `IUi::TextShy::CTextShyFrame::FrameProc` @ `ram:8149a9a7` | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlTextShy.cpp"` | LOW-MEDIUM (cosmetic hover effect) |
| **Bullet** | `0x00884f20` | `IUi::UiCtlBulletProc` @ `ram:8134512b` | `"!s_bulletImageList"` | LOW (cosmetic bullet marker) |
| **BtnExpand** | `0x008867f0` | `IUi::UiCtlBtnExpandProc` @ `ram:80e7b6f7` | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlBtnExpand.cpp"` | MEDIUM (expand/collapse toggle, 0x57/0x58 protocol) |
| **BtnToggle** | `0x00886370` | `IUi::UiCtlBtnToggleProc` @ `ram:816b67fd` | (path assertion) | HIGH (already wrapped as CheckboxFrame with 0x8000 flag) |
| **BtnFloating** | — | — | — | LOW |
| **BtnGlass** | — | — | — | LOW |

### Tier 3 Evaluated But Not Cataloged with Addresses

| Control | Utility | Create Feasible |
|---------|---------|-----------------|
| Hint | LOW | NO |
| Tip (Tooltip) | LOW | NO (GWCA has GetCurrentTooltip) |
| AnimSelection | MEDIUM | UNKNOWN (3D rendering) |
| ModeIcon | LOW | NO |
| Url | MEDIUM | NO (browser launch) |
| WebLink | HIGH | YES (wiki binding protocol) |
| HideUi | LOW | NO |
| Place | MEDIUM | UNKNOWN |
| District | HIGH | NO (manipulate existing dialog) |
| Stat | LOW | NO |
| ImeCand | NONE | NO |

---

## Tier 4: Infrastructure/Layout (Never Create Directly) — 16 Types

These are internal primitives used by the engine for layout, decoration, and infrastructure. They should never be created directly by injected code.

Border, Fade, Gap, Header, ImageList, LabelText, LabeledEdit, List, PageBtn, PageItem, Scroll, TextHeader, TextSelectable, TitleFrame, View, EditAutoComplete

---

## WASM↔EXE FrameProc Mappings (All 11 Confirmed)

| Control | WASM FrameProc | WASM Addr | EXE Address |
|---------|---------------|-----------|-------------|
| ButtonFrame | `CtlBtnProc` | `ram:80dbe9be` | (already in GWCA) |
| DropdownFrame | `CtlDropListProc` | `ram:80e3c9a3` | `0x0087f5f0` |
| SliderFrame | `CtlSliderProc` | `ram:80fcc337` | `0x00615fe0` |
| EditableTextFrame | `CtlEditProc` | `ram:80dee7ef` | `0x00888aa0` |
| ProgressBar | `CtlProgressProc` | `ram:80f6ce9a` | `0x008812e0` |
| TabsFrame | `CtlPageProc` | `ram:80e078f3` | `0x0061a950` |
| MultiLineTextLabel | `CtlTextMlProc` | `ram:80da0629` | `0x00610c40` |
| GroupHeader | `IUi::CGroupHeaderFrame::FrameProc` | `ram:81192c89` | `0x0087ddc0` |
| TextShy | `IUi::TextShy::CTextShyFrame::FrameProc` | `ram:8149a9a7` | `0x0087f0d0` |
| Bullet | `IUi::UiCtlBulletProc` | `ram:8134512b` | `0x00884f20` |
| BtnExpand | `IUi::UiCtlBtnExpandProc` | `ram:80e7b6f7` | `0x008867f0` |
| BtnToggle | `IUi::UiCtlBtnToggleProc` | `ram:816b67fd` | `0x00886370` |

---

## Assertion String Catalog for UI Controls

| Control | Assertion String | EXE String Address |
|---------|-----------------|--------------------|
| DropdownFrame | `"!FrameGetChild(thisFrame, CTL_LIST_ENTRIES)"` | `0x00b963fc` |
| SliderFrame | `"value >= m_range.min"` | `0x00a5045c` |
| EditableTextFrame | `"!s_editCaretMaterial"` | `0x00b96c00` |
| ProgressBar | `"!sm_rateArrowImageList"` | `0x00b964f4` |
| TabsFrame | `"!IsBtnCode(pageCode)"` | `0x00a506c0` |
| MultiLineTextLabel | `"FrameTestStyles(hdr.frameId, CTLTEXT_STYLE_MODEL)"` | `0x00a50110` |
| GroupHeader | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlGroupHeader.cpp"` | `0x00b96100` |
| TextShy | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlTextShy.cpp"` | `0x00b9636c` |
| Bullet | `"!s_bulletImageList"` | `0x00b9693c` |
| BtnExpand | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlBtnExpand.cpp"` | `0x00b96b68` |

---

## Phase 3 Implementation Crash — Critical Documentation

**What was built**: Phase 3 added Create functions for all 5 Tier 1 controls (DropdownFrame, SliderFrame, EditableTextFrame, ProgressBar, TabsFrame) across the full stack:

- **GWCA C++**: 5 callback globals + `Scanner::FindAssertion → ToFunctionStart` resolutions in `UIMgr.cpp`, 10 Create overloads, 5 public static Create methods in `UIMgr.h`
- **Python bindings**: 5 `Create*ByFrameId` functions in `py_ui.h`, `.def_static()` in `py_ui.cpp`, type stubs in `PyUIManager.pyi`
- **Python GWUI**: 5 high-level wrappers in `GWUI.py` (`create_dropdown`, `create_slider`, `create_editable_text`, `create_progress_bar`, `create_tabs`)

**Assertion strings used** (no hardcoded addresses):
| Control | Assertion | Source File |
|---------|-----------|-------------|
| DropdownFrame | `"!FrameGetChild(thisFrame, CTL_LIST_ENTRIES)"` | `UiCtlDropMenu.cpp` |
| SliderFrame | `"value >= m_range.min"` | `CtlSlider.cpp` |
| EditableTextFrame | `"!s_editCaretMaterial"` | `UiCtlEditBox.cpp` |
| ProgressBar | `"!sm_rateArrowImageList"` | `UiCtlProgress.cpp` |
| TabsFrame | `"!IsBtnCode(pageCode)"` | `CtlPage.cpp` |

**Result**: ALL 5 Create functions **crashed the client**.

### Possible Causes (NOT verified — hypotheses for future work):
1. **component_flags may be wrong** for some types (0x300 was inferred/inherited, not verified from FrameCreate callers)
2. **Context struct initialization may be required** — the FrameProc msg 0x09 handler may expect a pre-allocated context struct for certain types (like how CtlSliderProc allocates `CtlSlider::CInstance` on msg 0x09)
3. **The CreateUIComponent call pattern differs** from what GWCA uses for Button/Checkbox/Scrollable/TextLabel — some types may need pre-initialization or specific call ordering

**DO NOT reuse the Phase 3 C++ code as-is.** The research (addresses, assertions, structs, component_flags) is verified correct, but the C++ implementation needs rework.

---

## SliderFrame — Conclusive Failure Report (2026-06-06)

### Outcome

After 4 implementation attempts (Phases 3, 7, 10, 11) across 3 analysis rounds, **SliderFrame creation conclusively failed**. The control never rendered on screen.

### Root Cause

**CreateUIComponent cannot create multi-layer FrameProc controls.** The slider uses a two-layer FrameProc architecture:

| Layer | Name | EXE Address | Role |
|-------|------|-------------|------|
| Paint wrapper | `IUi::UiCtlSliderProc` | **`0x0087f440`** | Textured slider bar+thumb via `FrameContentAddImageTemplate`. Handles paint (0x01), invalidation (0x0C). Delegates all other messages to base. |
| Engine base | `CtlSliderProc` | **`0x00615fe0`** | Allocates `CtlSlider::CInstance` (0x30 bytes) on msg 0x09. Handles range/value (0x56-0x58), mouse/keyboard, animation. |

The game creates sliders through the layout/template system, which knows the C++ class hierarchy (`IUi::UiCtlSliderProc` inherits from `CtlSliderProc`). `CreateUIComponent` registers a single raw function pointer — it does NOT establish base class relationships.

### Failed Approaches

| # | Approach | Result |
|---|----------|--------|
| 1 | `CtlSliderProc` alone as primary FrameProc | Renders plain gray rectangle — no textured slider visuals |
| 2 | `IUi::UiCtlSliderProc` as primary FrameProc via `CreateUIComponent` | Crashes — wrapper delegates msg 0x09 to `FrameMsgCallBase`, no base registered → `CtlSlider::CInstance` never allocated → null deref on SetValue |
| 3 | `CtlSliderProc` primary + `FrameNewSubclass` wrapper | No visible effect — subclass does not properly intercept paint in this architecture |
| 4 | Various flag values (0x300, 0) | No difference — flag is not the issue |

### Byte Pattern for IUi::UiCtlSliderProc

Verified unique in 05-30-2026 EXE, resolves to `0x0087f440`:
```
\x55\x8B\xEC\x83\xEC\x18\x53\x8B\x5D\x08\x56\x57\x8B\x43\x04\x48\x83\xF8\x58
```

### Why Button/TextLabel/Checkbox/Scrollable Work

These types use **single self-contained FrameProcs** — they handle all messages internally without base class delegation. `CreateUIComponent` is compatible with this pattern. Slider, Dropdown, ProgressBar, Tabs, and EditableText all use multi-layer architectures that `CreateUIComponent` cannot replicate.

### Recommendations

1. **Abandon `CreateUIComponent`** for multi-layer controls
2. Investigate the **layout/template system** (`CCtlLayout::Child`, `.frame` templates)
3. Investigate **frame cloning** — copy an existing slider's frame tree from the Options dialog
4. Investigate **C++ RTTI/vtable setup** — what `CreateUIComponent` is missing for base class resolution

### Cleanup

- **`UI_RE/debug_slider.py`** — should be deleted manually by the user. Debugging artifact.

---

## Source Files Referenced

| File | Role |
|------|------|
| `Py4GW\vendor\gwca\Include\GWCA\Managers\UIMgr.h` | GWCA struct hierarchy, API declarations |
| `Py4GW\vendor\gwca\Source\UIMgr.cpp` | C++ implementations for all wrapped controls |
| `Py4GW\include\py_ui.h` | C++ Python bindings |
| `Py4GW\src\py_ui.cpp` | Python `.def_static()` registrations |
| `Py4GW_python_files\stubs\PyUIManager.pyi` | Python type stubs |
| `Py4GW_python_files\Py4GWCoreLib\GWUI.py` | High-level Python GWUI wrapper |
| `Py4GW_python_files\docs\RE\ui_controls_catalog.md` | This file |
| `Py4GW_python_files\docs\RE\reverse_engineering_reference.md` | Section 14 — UI Controls |
| `Py4GW_python_files\.opencode\projects\re\ui-elements\context_pool.md` | Full project history (Phases 0–3) |

---

## Button Creation Research (2026-06-16) — ALL APPROACHES CRASH

Three FrameProc candidates tested for native button creation via `CreateUIComponent`. All crash. See `docs/RE/reverse_engineering_reference.md` §14.2 for full details.

### Newly Discovered: `CtlTextBtnProc`

| Property | Value |
|----------|-------|
| **WASM** | `ram:80d9ce76` |
| **EXE (06-14)** | `FUN_00616c00` @ `0x00616c00` |
| **Type** | Engine-level text button (no `IUi::` prefix) |
| **Scanner pattern** | `\x83\xC0\xFC\x83\xF8\x5C\x0F\x87` (jump table, unique max msg 0x5C) |
| **Create** | msg 0x09 case 9 — allocates 0x38-byte state, copies caption from name_enc |
| **SetText** | msg 0x5F |
| **SetColor** | msg 0x5B |
| **SetHoverColor** | msg 0x5D |
| **Default text color** | 0xFF64BEEB |
| **Default hover color** | 0xFF78D2FF |
| **Status** | ❌ CRASHES on CreateUIComponent (same as all other button FrameProcs) |

### Also Confirmed (06-14 EXE)
- `IUi::UiCtlBtnProc` @ `0x00877e60` — same address in both 05-30 and 06-14 builds
- `CreateUIComponent` / `FrameCreate` @ `0x0062bfc0`
- `s_btnCheckImageList` global @ `0x010819cc`

---

## Document Version

- **Updated**: 2026-06-06 — SliderFrame conclusive failure report, IUi::UiCtlSliderProc wrapper discovered (0x0087f440), CreateUIComponent incompatibility documented
- **Source**: UI Elements Universe Discovery — Phases 1–11
- **EXE Build**: 05-30-2026
