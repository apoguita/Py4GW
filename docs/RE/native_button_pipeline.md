# Native Button Pipeline — Complete Specification

Last updated: 2026-06-20 | EXE Build: 06-14-2026 | Project: button-rendering-pipeline

## Overview

This document specifies the COMPLETE process for inserting an arbitrary clickable button with text caption into a native Guild Wars UI window. It covers both the styled GW button (Path A) and the flat engine button (Path B), the rendering pipeline, the click dispatch chain, the type-registry system, and the OnFrameNotify mechanism required for click handling.

## Implementation Status

Implementation was attempted but not completed. The following are confirmed blockers:

1. **FrameCreate callbacks**: GWCA passes raw function pointers but the game's type-registry uses data-section type addresses. Which form is correct for cold-created buttons needs verification.
2. **CContainerFrame children**: `CreateUIComponent` with CContainerFrame as parent crashes for button/text-label FrameProcs. FrameList intermediary required.
3. **FrameNewSubclass double-subclassing**: `GWUI.CreateWindow` already applies CRProc. Calling again crashes.
4. **Styled buttons need DAT textures**: PTR_DAT pointers are runtime BSS. Cold creation without texture loading reads uninitialized memory.
5. **Scanner pattern verification**: Byte patterns that were unique on 05-30 build resolved to different functions on 06-14 build. All patterns need Ghidra decompilation verification against the current EXE.

## Overview

This document specifies the COMPLETE process for inserting an arbitrary clickable button with text caption into a native Guild Wars UI window. It covers both the styled GW button (Path A) and the flat engine button (Path B), the rendering pipeline, the click dispatch chain, the type-registry system, and the OnFrameNotify mechanism required for click handling.

Previous projects (native-button-re, native-window-elements-creation, click-handling, ui-elements, window-contents) attempted button creation but all got blocked. This document captures the deep analysis that finally traced the complete pipeline end-to-end.

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
