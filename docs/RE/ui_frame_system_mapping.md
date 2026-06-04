# UI Frame System — GWCA ↔ WASM ↔ EXE Mapping

Date: 2026-05-30
Programs: `/gwca.dll`, `/Gw.wasm`, `/Gw.exe(Symbols)`

## Overview

This document maps the Guild Wars native UI frame system across three layers:
- **WASM** (`Gw.wasm`): Semantic source of truth — namespace-annotated C++ symbols
- **EXE** (`Gw.exe`): Runtime body — what C++ (GWCA) actually calls/hooks
- **GWCA** (`gwca.dll` + `UIMgr.cpp`): C++ wrapper layer — scanner-recovered addresses

## Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  GWCA.dll (UIMgr.cpp)                                   │
│  • CreateUIComponent / DestroyUIComponent               │
│  • SendUIMessage / SendFrameUIMessage                   │
│  • GetRootFrame / GetChildFrameId / FindRelatedFrame    │
│  • Window positions, preferences, tooltips              │
│  • All hooked: scanner-based recovery at runtime        │
├─────────────────────────────────────────────────────────┤
│  Gw.exe (native runtime)                                │
│  • FrameCreate → addresses resolved via GWCA scanners   │
│  • Thunks to FrameSet* / FrameGet* / FrameMsg*          │
│  • EXE thunk addresses (thunk_FUN_ → WASM function)      │
├─────────────────────────────────────────────────────────┤
│  Gw.wasm (semantic truth)                               │
│  • FrameCreate @ ram:809a13ea                           │
│  • FrameDestroy @ ram:809a1b36                          │
│  • FrameSetTitle @ ram:809b0a9b                         │
│  • FrameMsgSend @ ram:809b861f                          │
│  • DialogShow @ ram:815cdb8c                            │
│  • InventoryAggregateFrameProc @ ram:?                  │
│  • All namespaced: IUi::Game::*, IFrame::*, etc.        │
└─────────────────────────────────────────────────────────┘
```

## Section A: Core Frame Lifecycle

### Creation

| WASM Function | WASM Address | GWCA Alias | Notes |
|--------------|-------------|-----------|-------|
| `FrameCreate(unsigned int parent, unsigned int flags, unsigned int child, void (*proc)(...), void const* create_param, wchar_t const* label)` | `ram:809a13ea` | `CreateUIComponent_Func` (scanner-recovered) | Low-level frame constructor. Allocates frame object, installs callback, emits lifecycle notifications. GWCA scans: `\x33\xd2\x89\x45\x08\xb9\xc8\x01\x00\x00` |
| `FrameNewSubclass(unsigned int frame, void (*proc)(...), unsigned int flags)` = EXE `Ui_AttachCurrentHandlerSlot` | WASM `ram:809a2ebf`, EXE `0x00610340` | Scanner: `FindAssertion("FrApi.cpp","frameId",0x467,0)` + `ToFunctionStart(addr,0x210)`. Fallback: `\xFF\x75\x10\x8B\xF0\x8B\xCF\xFF\x75\x0C\x56` | Installs subclass proc. `__cdecl`, returns handler slot pointer. Used to attach window chrome (`Ui_CompositeRootControlProc`) to bare containers. Calls `Ui_SelectFrameContext` → `Ui_GetCurrentHandlerTailSlot` → `Ui_SetHandlerSlot`. |
| `FrameSetSubclass(unsigned int frame, unsigned int child, void (*proc)(...), unsigned int flags)` | `ram:809a3129` | — | Sets subclass proc for a child |
| `IUi::Game::DialogShow(unsigned int parent, IUi::Game::EFloatingDialog dialog, int, void const*)` | `ram:815cdb8c` | — | **The real floating-dialog factory.** Handles: title, position restore, `FramePlaceChildren(..., L"GmView-Dialog")`, size/width/height, layer policy |

### Destruction

| WASM Function | WASM Address | GWCA Alias | Notes |
|--------------|-------------|-----------|-------|
| `FrameDestroy(unsigned int frame)` | `ram:809a1b36` | `DestroyUIComponent_Func` | Destroys frame. GWCA scans: assertion `"frame->state.Test(FRAME_STATE_CREATED)"` |
| `FrameDestroyChildren(unsigned int frame)` | `ram:809a1c9a` | — | Destroys all children of a frame |

### Lifecycle Messages (received by frame procs)

| Message ID | WASM Constant | Description |
|-----------|--------------|-------------|
| `0x09` | `FRAME_MSG_CREATE` | Frame created — `OnFrameCreate(FrameMsgCreate const&)` |
| `0x0A` | `FRAME_MSG_DESTROY` | Frame destroyed |
| `0x24` | `FRAME_MSG_MOUSE_DOWN` | Mouse click |
| `0x2E` | `FRAME_MSG_HOVER` | Hotkey/context menu trigger |
| `0x56` | `FRAME_MSG_SHOW` | Show frame |
| `0x57` | `FRAME_MSG_HIDE` | Hide frame |
| `0x5A` | `FRAME_MSG_ENABLE` | Enable frame |
| `0x5B` | `FRAME_MSG_DISPATCH` | Generic dispatch message |
| `0x58` | — | Query/state message |

## Section B: Frame Properties (Setters)

### Position & Size

| WASM Function | WASM Address | Signature |
|--------------|-------------|-----------|
| `FrameSetPosition(unsigned int, Coord2f const&)` | `ram:809a97bb` | Set top-left anchor |
| `FrameSetPosition(unsigned int, Coord2f const&, Coord2f const&)` | `ram:809a9448` | Set both anchors |
| `FrameSetPosition(unsigned int, Coord2f const&, Coord2f const&, unsigned int)` | `ram:809a95f0` | Set both anchors + flags |
| `FrameSetPosition(unsigned int, FramePosition const&)` | `ram:809a9f40` | Set from FramePosition struct |
| `FrameSetSize(unsigned int, Coord2f const&)` | `ram:809a9c3e` | Set width and height |
| `FrameSetWidth(unsigned int, float)` | `ram:809a9abd` | Set width only |
| `FrameSetHeight(unsigned int, float)` | `ram:809a993c` | Set height only |
| `FrameSetMinSize(unsigned int, Coord2u const&)` | `ram:809aa44a` | Set minimum size |
| `FrameSetMaxSize(unsigned int, Coord2u const&)` | `ram:809aa5cb` | Set maximum size |
| `FrameSetView(unsigned int, Coord2f const&)` | `ram:809a9dbf` | Set viewport |
| `FrameSetDisplaySafeZone(Rect4u const&, Coord2u const&)` | `ram:809b197c` | Set safe zone |

### Layer & Visibility

| WASM Function | WASM Address | Signature |
|--------------|-------------|-----------|
| `FrameSetLayer(unsigned int, int)` | `ram:809b060f` | Set Z-order layer |
| `FrameSetOpacity(unsigned int, float)` | `ram:809b7f49` | Set opacity/alpha |
| `FrameSetUi(unsigned int, int)` | `ram:809a0f97` | Show/hide UI element |
| `FrameSetManualFading(unsigned int, int)` | `ram:809b7beb` | Enable manual fade control |
| `FrameSetScale(int)` | `ram:809b12c9` | Set UI scale factor |

### Title & Text

| WASM Function | WASM Address | Signature |
|--------------|-------------|-----------|
| `FrameSetTitle(unsigned int, wchar_t const*)` | `ram:809b0a9b` | Set frame title text |
| `FrameSetTitleHotkey(unsigned int, wchar_t const*)` | `ram:809b0c8d` | Set title with hotkey indicator |
| `FrameSetTextScaleAdjust(int)` | `ram:809b1b7e` | Set text scale adjustment |
| `FrameSetDefaultTextStyle(unsigned int, unsigned int)` | `ram:809af48c` | Set default text style |
| `FrameSetLanguage(ELanguage, unsigned int)` | `ram:809af629` | Set language |

### Other

| WASM Function | WASM Address | Signature |
|--------------|-------------|-----------|
| `FrameSetRenderTarget(HGrTexture_tag*, ...)` | `ram:809a11bf` | Set render-to-texture target |
| `FrameSetUserParam(unsigned int, void*)` | `ram:809a5761` | Set user data pointer |
| `FrameSetSubclassFlags(unsigned int, void (*)(...), unsigned int, unsigned int)` | `ram:809a32f4` | Set subclass with flags |

## Section C: Frame Properties (Getters)

| WASM Function | WASM Address | Returns |
|--------------|-------------|---------|
| `FrameGetChild(unsigned int, unsigned int)` | `ram:809afc7e` | Child frame ID by index |
| `FrameGetParent(unsigned int)` | `ram:809afeac` | Parent frame ID |
| `FrameGetCode(unsigned int)` | `ram:809af832` | Frame code/type |
| `FrameGetTitle(unsigned int)` | `ram:809b0790` | Title wchar_t* |
| `FrameGetLayer(unsigned int)` | `ram:809b04aa` | Layer int |
| `FrameGetOpacity(unsigned int)` | `ram:809b7ddf` | Opacity float |
| `FrameGetMinSize(unsigned int)` | `ram:809aa2b3` | Minimum size |
| `FrameGetNativeSize(unsigned int)` | `ram:809a8482` | Native/desired size |
| `FrameGetNativeSize(unsigned int, Coord2f const&)` | `ram:809a86af` | Native size with constraint |
| `FrameGetPosition(unsigned int, Coord2f*, ...)` | `ram:809a886b` | Position (4 out params) |
| `FrameGetPosition(unsigned int, FramePosition*)` | `ram:809aa0c1` | Position struct |
| `FrameGetClipRect(unsigned int)` | `ram:809a830a` | Clip rectangle |
| `FrameGetClientBorder(unsigned int)` | `ram:809a8164` | Client border insets |
| `FrameGetScreenSize()` | `ram:809a8e75` | Total screen size |
| `FrameGetScale()` | `ram:809b0fdb` | UI scale |
| `FrameGetDefaultTextHeight(unsigned int)` | `ram:809af186` | Default text line height |
| `FrameGetTextStyleHeight(unsigned int)` | `ram:809af334` | Text style height |
| `FrameGetEffectiveDpi()` | `ram:809b1b3a` | Effective DPI |
| `FrameGetDisplaySafeZone()` | `ram:809b1a4c` | Display safe zone rect |
| `FrameGetDisplaySafeZoneMargins()` | `ram:809b1abd` | Safe zone margins |

## Section D: Message System

### Core Message Functions

| WASM Function | WASM Address | GWCA Alias | Notes |
|--------------|-------------|-----------|-------|
| `FrameMsgSend(unsigned int frame, unsigned int msg, void const*, void*)` | `ram:809b861f` | `SendFrameUIMessage_Func` / `SendFrameUIMessageById_Func` | Send message to a specific frame. GWCA hooks both paths (array dispatch + by-ID) |
| `FrameMsgSendRegistered(unsigned int msg, void const*, void*)` | `ram:809b8869` | `SendUIMessage_Func` | Send to all frames registered for this message. GWCA scans: `\xB9\x00\x00\x00\x00\xE8...\x5D\xC3` |
| `FrameMsgRegister(unsigned int frame, unsigned int msg)` | `ram:809b8271` | — | Register frame to receive a message type |
| `FrameMsgUnregister(unsigned int frame, unsigned int msg)` | `ram:809b83f2` | — | Unregister from message |
| `FrameKeyRegister(unsigned int frame, unsigned int key, unsigned int flags)` | `ram:809a355d` | — | Register key binding |
| `FrameKeyUnregister(unsigned int frame, unsigned int key, unsigned int flags)` | `ram:809a3d4c` | — | Unregister key |
| `FrameKeyUnregisterAll(unsigned int frame)` | `ram:809a3ea8` | — | Unregister all keys |

### GWCA Message Hooks

From `UIMgr.cpp`:

| GWCA Hook | Target | Hook Type |
|-----------|--------|-----------|
| `OnSendUIMessage` | `SendUIMessage_Func` | `__cdecl (msgid, wParam, lParam)` |
| `OnSendFrameUIMessage` | `SendFrameUIMessage_Func` | `__fastcall (Array<FrameCallbacks>*, edx, msgid, wParam, lParam)` |
| `OnSendFrameUIMessageById` | `SendFrameUIMessageById_Func` | `__cdecl (frame_id, msgid, wParam, lParam)` |
| `OnCreateUIComponent` | `CreateUIComponent_Func` | `__cdecl (frame_id, flags, child, callback, name, label)` |

### GWCA Message Registration

| GWCA Function | GWCA Address | Purpose |
|--------------|-------------|---------|
| `RegisterUIMessageCallback` | `10027790` | Register callback for a UI message type |
| `RegisterFrameUIMessageCallback` | `100273b0` | Register callback for frame-specific messages |
| `RemoveUIMessageCallback` | `10027bb0` | Remove UI message callback |
| `RemoveFrameUIMessageCallback` | `10027a70` | Remove frame message callback |
| `RegisterCreateUIComponentCallback` | `100272c0` | Register callback for component creation |
| `RemoveCreateUIComponentCallback` | `10027970` | Remove creation callback |
| `AddFrameUIInteractionCallback` | `10025b60` | Add interaction callback |

## Section E: UI Component Creation (GWCA-side)

### CreateUIComponent

```
GWCA signature:
  uint32_t CreateUIComponent(
      uint32_t frame_id,           // parent frame ID
      uint32_t component_flags,    // style flags (e.g., 0x20 for title bar, 0x40 for resizable)
      uint32_t tab_index,          // child index (tab order)
      void* event_callback,        // frame proc callback
      wchar_t* name_enc,           // encoded name (or hash?)
      wchar_t* component_label     // visible label/title
  ) -> uint32_t                    // new frame ID
```

**WASM call chain:**
```
CreateUIComponent → FrameCreate(parent, flags, child, callback, create_param, label)
```

**GWCA scanner pattern:** `\x33\xd2\x89\x45\x08\xb9\xc8\x01\x00\x00`

**Hook behavior:** `OnCreateUIComponent` runs pre/post callbacks, logs frame label to `frame_logs`.

### DestroyUIComponent

```
DestroyUIComponent(uint32_t frame_id) → bool
```

**GWCA scanner:** Assertion `"frame->state.Test(FRAME_STATE_CREATED)"` in `\\Code\\Gw\\Ui\\Frame\\FrApi.cpp`

### Typed Component Helpers

From `Ui_InitializeTypedComponentCallbacks` @ GWCA `100164a0`:

| Typed Component | GWCA Pattern | Notes |
|----------------|-------------|-------|
| Text Label | Pattern-based lookup → `TextLabelControlProc` | Creates text display frames |
| Scrollable Frame | Pattern-based lookup → `ScrollbarControlProc` | Creates scrollable containers |
| Button | Pattern-based lookup | Creates clickable buttons |

## Section F: Window/Shell Candidates (from existing RE)

### CContainerFrame + Ui_CompositeRootControlProc — Confirmed Working Approach ★ (2026-05-30)

| Function | Address | Notes |
|----------|---------|-------|
| `IUi::CContainerFrame::FrameProc` | WASM `ram:812a7233`, EXE `0x00871b40` | Minimal container proc. Msg 0x09: mouse enable only. Msg 0x37: child layout. No side effects. |
| `Ui_CompositeRootControlProc` | EXE `0x00851180` | Window chrome proc. Msg 0x08: paint (title bar, borders, close). Msg 0x17: hit-test (drag, resize). Scanner: `\x81\xEC\x1C\x01\x00\x00\xA1????\x33\xC5...` |
| `Ui_AttachCurrentHandlerSlot` (= `FrameNewSubclass`) | WASM `ram:809a2ebf`, EXE `0x00610340` | Installs subclass proc. Scanner: `FindAssertion("FrApi.cpp","frameId",0x467,0)`. Fallback: `\xFF\x75\x10\x8B\xF0\x8B\xCF\xFF\x75\x0C\x56` |

**Key properties:**
- **Confirmed working** via `CreateTitledContainerWindow()` in `py_ui.h` / `PyUIManager.UIManager.create_titled_container_window()` in Python.
- Combines bare `CContainerFrame` (no content) + `FrameNewSubclass(Ui_CompositeRootControlProc, 0x59)` (chrome) + `SetFrameTitleByFrameId` (title).
- **Subclass flags 0x59** = 0x01 (title bar+close+drag) | 0x08 (right/bottom resize) | 0x10 (left/top resize) | 0x40 (chrome rendering).
- **Mouse interaction**: Requires `Ui_CompositeRootControlProc` callbacks — msg 0x08 (paint) and msg 0x17 (hit-test). A bare CContainerFrame has no chrome-hit logic.
- Supersedes: DevText clone path and inventory aggregate shell approach.

### InventoryAggregateFrameProc — Former best candidate (now superseded)

| WASM Function | WASM Address |
|--------------|-------------|
| `IUi::Game::InventoryAggregateFrameProc(FrameMsgHdr const&, void const*, void*)` | *(search WASM)* |
| `IUi::Game::Inventory::CAggregateInv::FrameProc(FrameMsgHdr const&, void const*, void*)` | *(search WASM)* |
| `IUi::Game::Inventory::CAggregateInv::OnFrameCreate(FrameMsgCreate const&)` | *(search WASM)* |
| `IUi::Game::Inventory::CAggregateInv::OnFrameSize(FrameMsgSize const&)` | *(search WASM)* |
| `IUi::Game::Inventory::CAggregateInv::OnFrameSizeQuery(FrameMsgSizeQuery const&)` | *(search WASM)* |
| `IUi::Game::Inventory::CAggregateInv::UpdateBags()` | *(search WASM)* |

**Key properties:**
- Titled, resizable, hosts child UI elements
- Shell/container setup happens BEFORE payload population (`UpdateBags()` is separate)
- The cleanest candidate for an empty reusable native window shell

### DevText — Proven clone path

| WASM Function | WASM Address |
|--------------|-------------|
| `IUi::DlgDevTextProc(FrameMsgHdr const&, void const*, void*)` | *(search WASM)* |
| `IUi::NDlgDevText::CTextDialogFrame::OnCreate(unsigned int)` | *(search WASM)* |

**Key properties:**
- Proven to work via Python `UIManager.CreateWindow(...)` clone path
- Tightly coupled to content at construction time — not ideal for empty shell
- EXE proc addresses: `Ui_DevTextDialogProc` @ `0x00864170`, `Ui_DevTextChildContainerProc` @ `0x008527A0`

### The Python Wrapper Chain (DevText clone path)

```
Python: UIManager.CreateWindow(rect, label, parent, callback, flags)
  → UIManager.CreateWindowByFrameId(parent, child_index, callback, rect)
    → C++: UIManager::CreateWindowByFrameId(...)               [py_ui.h]
      → UIManager::CreateLabeledFrameByFrameId(...)             [py_ui.h]
        → GW::UI::CreateUIComponent(...)                        [UIMgr.cpp]
          → FrameCreate(...)                                    [native/WASM]
    → C++: UIManager::SetFrameControllerAnchorMarginsByFrameIdEx(...)
    → C++: UIManager::TriggerFrameRedrawByFrameId(...)
```

## Section G: Text/Encoding Helpers

| WASM Function | WASM Address | GWCA Alias | Notes |
|--------------|-------------|-----------|-------|
| `Ui_CreateEncodedTextFromStringId` | EXE: `0x007A1540` | — | String ID → encoded text payload |
| `Ui_CreateEncodedText` | EXE: `0x007A1560` | — | Build encoded text from params |
| `Ui_GetEncodedTextResourceById` | EXE: `0x005A1F90` | — | Get text resource by ID |
| `UInt32ToEncStr` | — | `10028c70` (gwca.dll) | Convert uint → encoded string format |
| `EncStrToUInt32` | — | `10026080` (gwca.dll) | Convert encoded string → uint |
| `AsyncDecodeStr` | — | `AsyncDecodeStringPtr` (UIMgr: `\x57\x83\x7e\x30\x00\x74\x14\x68\xc9`) | Decode encoded string asynchronously |

## Section H: Miscellaneous UI Functions

| Function | WASM/EXE | GWCA | Notes |
|----------|----------|------|-------|
| `FramePlaceChildren(unsigned int, wchar_t const*)` | `ram:809a7f5e` | — | Layout children with layout policy name (e.g. `"GmView-Dialog"`) |
| `FrameTestStyles(unsigned int, unsigned int)` | `ram:809a7325` | — | Test if frame has specific styles |
| `GetRootFrame()` | — | `GetRootFrame_Func` (scanner: `\x05\xd8\xfe\xff\xff\xc3`) | Get root frame ID |
| `GetChildFrameId(parent, child)` | — | `GetChildFrameId_Func` (scanner: assertion `"pageId"` in `CtlView.cpp`) | Get child frame by index |
| `FindRelatedFrame(parent, type, flags)` | — | `FindRelatedFrame_Func` (EXE: `0x0062c790`) | Find related frame by type |
| `GetChildFromNameHash(frame, hash)` | `ram:80983fda` (WASM) | DISABLED in GWCA (crashes) | O(1) hash lookup for child |
| `CreateHashFromWchar(wcs, seed)` | — | `CreateHashFromWchar_Func` (`\x85\xc0\x74\x10\x6a\xff\x50`) | Hash wchar string for frame names |
| `SetTooltip(tooltip**)` | — | `SetTooltip_Func` (assertion: `"CMsg::Validate(id)"` in `FrTip.cpp`) | Set tooltip info |
| `SetWindowVisible(window_id, visible, ...)` | — | `SetWindowVisible_Func` (`\x8B\x75\x08\x83\xFE\x00\x7C\x19\x68`) | Show/hide window by index |
| `SetWindowPosition(window_id, WindowPosition*, ...)` | — | `SetWindowPosition_Func` (offset -0xE0 from SetWindowVisible) | Set window position |
| `Ui_BroadcastRegisteredFrameMessage` | — | via `SendUIMessage_Func` | Broadcast message to all registered frames |

## Section I: Frame State / Flags Reference

Common frame style flags (from decompilation patterns):

| Flag | Value | Meaning |
|------|-------|---------|
| `FRAME_STATE_CREATED` | `0x01` | Frame has been created |
| `FRAME_STYLE_VISIBLE` | `0x2000` | Frame is visible/enabled (tested in UseSkillSlot) |
| `FRAME_STYLE_INTERACTIVE` | `0x4000` | Frame accepts input (tested in UseSkillSlot) |
| Title bar | `0x20` | Frame has a title bar |
| Resizable | `0x40` | Frame is resizable |

### Subclass Flags (passed to FrameNewSubclass, processed by Ui_CompositeRootControlProc)

| Flag | Value | Meaning |
|------|-------|---------|
| Title bar + close + drag | `0x01` | Enables caption rendering, `[X]` close button, drag-to-move hit-test (msg 0x08/0x17) |
| Right/bottom resize handles | `0x08` | Enables resize cursors on right and bottom edges |
| Left/top resize handles | `0x10` | Enables resize cursors on left and top edges |
| Chrome rendering | `0x40` | Enables all chrome drawing. Auto-set when `0x18` is present. |
| Composite root default | `0x59` | = `0x01 \| 0x08 \| 0x10 \| 0x40` — standard titled/resizable window chrome |
| Gamepad cursor mode | `0x200` | Enables gamepad-specific behavior (not needed for mouse interaction) |

## Section J: GWCA.dll Internals (for context)

### UI-related exports from gwca.dll:

| Export | Address | Description |
|--------|---------|-------------|
| `CreateUIComponent` | `10025fd0` | Frame creation wrapper → native FrameCreate |
| `DestroyUIComponent` | `10026020` | Frame destruction → native FrameDestroy |
| `SendUIMessage` | `10028050` | Send UI message to all registered frames |
| `SendFrameUIMessage` | `10027ea0` | Send UI message to a specific frame |
| `RegisterUIMessageCallback` | `10027790` | Register for UI message callbacks |
| `RegisterFrameUIMessageCallback` | `100273b0` | Register for frame-specific message callbacks |
| `RegisterCreateUIComponentCallback` | `100272c0` | Register for component creation callbacks |
| `RemoveUIMessageCallback` | `10027bb0` | Remove UI message callback |
| `RemoveFrameUIMessageCallback` | `10027a70` | Remove frame message callback |
| `RemoveCreateUIComponentCallback` | `10027970` | Remove creation callback |
| `AddFrameUIInteractionCallback` | `10025b60` | Add interaction callback |
| `Ui_InitializeTypedComponentCallbacks` | `100164a0` | Initialize typed components (text, scroll, button) |
| `EncStrToUInt32` | `10026080` | Convert encoded string to uint32 |
| `UInt32ToEncStr` | `10028c70` | Convert uint32 to encoded string |
| `GetIsUIDrawn` | `10026850` | Check if UI is currently drawn |
| `GetEquipmentVisibility` | `1001b950` | Get equipment visibility state |
| `SetEquipmentVisibility` | `1001ccb0` | Set equipment visibility state |

### Key GWCA global pointers:

| GWCA Internal | Description |
|---------------|-------------|
| `s_FrameArray` | Array of all active UI Frame objects |
| `CurrentTooltipPtr` | Pointer to current tooltip |
| `window_positions_array` | Array of saved window positions (66 built-in windows) |
| `WorldMapState_Addr` | World map UI state |
| `GameSettings_Addr` | Game settings context |
| `PreferencesInitialised_Addr` | Preferences loaded flag |
| `ui_drawn_addr` | UI drawn counter |

## Section K: Remaining to Map

Functions not yet fully mapped EXE→WASM:

1. `IUi::Game::InventoryAggregateFrameProc` — need exact WASM address
2. `IUi::Game::Inventory::CAggregateInv::OnFrameCreate` — need WASM address  
3. `IUi::Game::DialogShow` internals — what descriptor records drive it
4. `SendUIMessage_Func` — actual native address (GWCA scans for it)
5. `GetRootFrame_Func` — actual native address

### Mapped Since Last Update

- `FrameNewSubclass` / `Ui_AttachCurrentHandlerSlot` — **MAPPED** (WASM `ram:809a2ebf`, EXE `0x00610340`)
- `Ui_CompositeRootControlProc` — **MAPPED** (EXE `0x00851180`)
- `CContainerFrame::FrameProc` — **MAPPED** (WASM `ram:812a7233`, EXE `0x00871b40`)
6. Frame messaging constants (0x100000xx range) — full catalog
7. `FrameCreate` EXE thunk address in `/Gw.exe(Symbols)` — for direct C++ calls

## Section L: Py4GW UI Class — Additional Wrappers (from py_ui.h)

The `UIManager` class in `C:\Users\Apo\Py4GW\include\py_ui.h` exposes these additional
functions, which wrap GWCA calls and ultimately map to WASM native functions.

### Frame Navigation & Discovery

| Python Method | Underlying GWCA/WASM |
|--------------|---------------------|
| `GetFrameIDByLabel(label)` | Frame tree walk + label comparison |
| `GetFrameIDByHash(hash)` | Frame tree walk + hash comparison |
| `GetChildFrameByFrameId(parent, child)` | `FrameGetChild` @ ram:809afc7e |
| `GetChildFramePathByFrameId(parent, offsets)` | Multiple `FrameGetChild` calls |
| `GetParentFrameID(frame)` | `FrameGetParent` @ ram:809afeac |
| `GetFrameContext(frame)` | Direct struct read (vtable lookup) |
| `GetChildFrameIDs(parent)` | Iterates `s_FrameArray` with parent filter |
| `GetFirstChildFrameID / GetLastChildFrameID / GetNextChildFrameID / GetPrevChildFrameID` | Sorted child array walk |
| `GetItemFrameID(parent, index)` | Nth child by index |
| `GetRelatedFrameID(frame, relation_kind)` | Native sibling/child walker |
| `GetFrameHierarchy()` | Full tree snapshot |
| `GetChildFrameIdFromNameHash(parent, hash)` | `FrRelation` hash table lookup @ WASM ram:80983fda |
| `GetOverlayFrameIDs / GetPopupFrameIDs` | Global overlay/popup linked lists |

### Frame Properties

| Python Method | Underlying GWCA/WASM |
|--------------|---------------------|
| `GetFrameLayerByFrameId / SetFrameLayerByFrameId` | Direct `Frame` struct field access (`+0x28`) |
| `GetFrameCodeByFrameId` | `FrameGetCode` @ ram:809af832 |
| `GetFrameMinSizeByFrameId` | `FrameGetMinSize` @ ram:809aa2b3 |
| `GetFrameClientBorderByFrameId` | `FrameGetClientBorder` @ ram:809a8164 |
| `GetFrameClipRectByFrameId` | `FrameGetClipRect` @ ram:809a830a |
| `GetFramePositionExByFrameId` | Native FrApi function (scanner-recovered) |
| `GetFrameTitleByFrameId` | `FrameGetTitle` @ ram:809b0790 |
| `GetFrameNativeSizeByFrameId` | `FrameGetNativeSize` @ ram:809a8482 |
| `GetFrameOpacityByFrameId` | Direct struct read |
| `GetFrameUserParamByFrameId` | Direct struct read |
| `GetFrameStateBitByFrameId(frame, bit)` | Direct `frame_state` field test |

### Frame Manipulation

| Python Method | Underlying GWCA/WASM |
|--------------|---------------------|
| `SetFrameVisibleByFrameId(frame, visible)` | Direct `frame_state` bit toggle (`|= / &= ~0x200`) |
| `SetFrameDisabledByFrameId(frame, disabled)` | Direct `frame_state` bit toggle (`|= / &= ~0x10`) |
| `SetFrameOpacityByFrameId(frame, opacity, fade)` | GWCA `SetFrameOpacity` → `FrameSetOpacity` @ ram:809b7f49 |
| `ShowFrameByFrameId(frame, show)` | GWCA `ShowFrame` → `FrameMsgSend(msg 0xC)` |

### Window Creation

| Python Method | Underlying GWCA/WASM |
|--------------|---------------------|
| `CreateUIComponentByFrameId(parent, flags, child, cb, name, label)` | `CreateUIComponent` → `FrameCreate` @ ram:809a13ea |
| `CreateUIComponentRawByFrameId(...)` | Same, with raw `wparam` as create param |
| `CreateLabeledFrameByFrameId(parent, flags, child, cb, param, label)` | `CreateUIComponent` wrapper |
| `CreateWindowByFrameId(parent, child, cb, x, y, w, h, flags, ...)` | CreateLabeledFrameByFrameId + SetAnchorMargins + Redraw |
| `CreateWindowClone(x, y, w, h, label, ...)` | DevText-backed clone path with title hook |
| `CreateEmptyWindowClone(...)` | Clone + ClearWindowContents + Redraw |
| `DestroyUIComponentByFrameId(frame)` | `DestroyUIComponent` → `FrameDestroy` @ ram:809a1b36 |

### Layout / Anchor

| Python Method | Underlying GWCA/WASM |
|--------------|---------------------|
| `SetFrameControllerAnchorMarginsByFrameIdEx(frame, x, y, w, h, flags)` | Scanner-recovered native function: `\x50\xe8...\x8d\x88\xd0\x00\x00\x00` |
| `QueueFrameControllerUpdateByFrameId(frame)` | Scanner: `\x6a\x01\xe8...\x5d\xc3` |
| `ProcessFrameControllerUpdateByFrameId(frame)` | Scanner: `\xe8...\x5d\xc3` |
| `ChooseAnchorFlagsForDesiredRect(x, y, w, h, pw, ph)` | Scanner: `\x55\x8b\xec\x8b\x45\x10\xba\x02...` |
| `CollapseWindowByFrameId / RestoreWindowRectByFrameId / SetFrameMarginsByFrameId` | Composed from above |

### Title System

| Python Method | Underlying GWCA/WASM |
|--------------|---------------------|
| `SetFrameTitleByFrameId(frame, title)` | `Ui_CreateEncodedText` → `Ui_SetFrameText` (scanner-recovered: `\x55\x8B\xEC\x8B\x45\x10\x53\x56\x57` and `\x55\x8B\xEC\x56\x8B\x75\x08`) |
| `SetNextCreatedWindowTitle(title)` | Hook on `Ui_CreateEncodedText` + `Ui_SetFrameText` + `Ui_SetFrameEncodedTextResource` |
| `GetFrameLabelByFrameId(frame)` | `FrameGetTitle` + `WCharToUTF8` |

### Typed Component Creation

| Python Method | GWCA Underlying | WASM Proc Used |
|--------------|----------------|---------------|
| `CreateButtonFrameByFrameId(...)` | `GW::UI::CreateButtonFrame` | `ButtonControlProc` (scanner-resolved) |
| `CreateCheckboxFrameByFrameId(...)` | `GW::UI::CreateCheckboxFrame` | `CheckboxControlProc` (scanner-resolved) |
| `CreateScrollableFrameByFrameId(...)` | `GW::UI::CreateScrollableFrame` | `ScrollbarControlProc` (scanner-resolved) |
| `CreateTextLabelFrameByFrameId(...)` | `GW::UI::CreateTextLabelFrame` | `TextLabelControlProc` @ EXE 0x005F28D0 |
| `CreateTextLabelFrameWithPlainTextByFrameId(...)` | Same, with pre-encoded literal payload | Same |
| `CreateTextLabelFrameFromTemplateByFrameId(...)` | Same, copies encoded label from template | Same |

### Typed Component Manipulation

| Python Method | Component Type |
|--------------|---------------|
| `GetButtonLabelByFrameId / SetButtonLabelByFrameId` | `ButtonFrame` |
| `ButtonMouseActionByFrameId(frame, action)` | `ButtonFrame` |
| `ButtonClick(frame) / ButtonDoubleClick(frame)` | `ButtonFrame` |
| `IsCheckboxCheckedByFrameId / SetCheckboxCheckedByFrameId` | `CheckboxFrame` |
| `GetCheckboxValueByFrameId / SetCheckboxValueByFrameId` | `CheckboxFrame` |
| `AddTabByFrameId / DisableTabByFrameId / EnableTabByFrameId / RemoveTabByFrameId` | `TabsFrame` |
| `GetCurrentTabIndexByFrameId / GetTabFrameIdByFrameId / GetIsTabEnabledByFrameId` | `TabsFrame` |
| `GetTabByLabelByFrameId / GetCurrentTabByFrameId / GetTabButtonByFrameId` | `TabsFrame` |
| `ChooseTabByTabFrameId / ChooseTabByIndexByFrameId` | `TabsFrame` |
| `SetScrollableSortHandlerByFrameId / GetScrollableSortHandlerByFrameId` | `ScrollableFrame` |
| `ClearScrollableItemsByFrameId / RemoveScrollableItemByFrameId / AddScrollableItemByFrameId` | `ScrollableFrame` |
| `GetScrollableItemFrameIdByFrameId / GetScrollableSelectedValueByFrameId` | `ScrollableFrame` |
| `GetScrollableFirstChildFrameIdByFrameId / GetScrollableLastChildFrameIdByFrameId` | `ScrollableFrame` |
| `GetScrollableNextChildFrameIdByFrameId / GetScrollablePrevChildFrameIdByFrameId` | `ScrollableFrame` |
| `GetScrollableItemRectByFrameId / GetScrollableCountByFrameId / GetScrollableItemsByFrameId` | `ScrollableFrame` |
| `GetScrollablePageByFrameId / SetScrollablePageByFrameId` | `ScrollableFrame` |
| `GetEditableTextValueByFrameId / SetEditableTextValueByFrameId` | `EditableTextFrame` |
| `SetEditableTextMaxLengthByFrameId / IsEditableTextReadOnlyByFrameId` | `EditableTextFrame` |
| `SetEditableTextReadOnlyByFrameId` | `EditableTextFrame` |
| `GetProgressBarValueByFrameId / SetProgressBarValueByFrameId` | `ProgressBar` |
| `SetProgressBarMaxByFrameId / SetProgressBarColorIdByFrameId / SetProgressBarStyleByFrameId` | `ProgressBar` |
| `GetDropdownOptionsByFrameId / SelectDropdownOptionByFrameId / SelectDropdownIndexByFrameId` | `DropdownFrame` |
| `AddDropdownOptionByFrameId / GetDropdownCountByFrameId` | `DropdownFrame` |
| `GetDropdownOptionValueByFrameId / GetDropdownOptionIndexByFrameId` | `DropdownFrame` |
| `GetDropdownSelectedIndexByFrameId / DropdownHasValueMappingByFrameId` | `DropdownFrame` |
| `GetDropdownValueByFrameId / SetDropdownValueByFrameId` | `DropdownFrame` |
| `GetSliderValueByFrameId / SetSliderValueByFrameId` | `SliderFrame` |
| `GetTextLabelEncodedByFrameId / SetTextLabelByFrameId / GetTextLabelDecodedByFrameId` | `TextLabelFrame` |
| `SetTextLabelBytesByFrameId / AppendTextLabelEncodedSuffixByFrameId / AppendTextLabelPlainSuffixByFrameId` | `TextLabelFrame` |
| `SetTextLabelFontByFrameId` | `TextLabelFrame` |
| `SetMultilineLabelByFrameId` | `MultiLineTextLabelFrame` |
| `SetReadOnlyByFrameId / IsReadOnlyByFrameId` | Generic (msg 0x5B / 0x56) |

### Interaction / Callbacks

| Python Method | Underlying GWCA/WASM |
|--------------|---------------------|
| `SendUIMessage(msgid, values, skip_hooks)` | `SendUIMessage_Func` → `FrameMsgSendRegistered` @ ram:809b8869 |
| `SendUIMessageRaw(msgid, wparam, lparam, skip_hooks)` | Same with raw params |
| `SendFrameUIMessage(frame, msgid, wparam, lparam)` | `SendFrameUIMessage_Func` → `FrameMsgSend` @ ram:809b861f |
| `SendFrameUIMessageWString(frame, msgid, text)` | Same with temporary wstring payload |
| `AddFrameUIInteractionCallbackByFrameId(frame, cb, wparam)` | `AddFrameUIInteractionCallback` |
| `TriggerFrameRedrawByFrameId(frame)` | GWCA `TriggerFrameRedraw` |
| `TestMouseAction(frame, state, wparam, lparam)` | `GW::UI::TestMouseAction` |
| `TestMouseClickAction(frame, state, wparam, lparam)` | `GW::UI::TestMouseClickAction` |

### Text Encoding/Decoding

| Python Method | Underlying GWCA/WASM |
|--------------|---------------------|
| `AsyncDecodeStr(enc_str)` | `AsyncDecodeStringPtr` → WASM `AsyncDecodeStr` |
| `IsValidEncStr(enc_str) / IsValidEncBytes(bytes)` | `GW::UI::IsValidEncStr` |
| `UInt32ToEncStr(value)` | `UInt32ToEncStr` @ gwca.dll 10028c70 |
| `EncStrToUInt32(enc_str)` | `EncStrToUInt32` @ gwca.dll 10026080 |
| `GetTextLanguage()` | `GW::UI::GetTextLanguage` |

### Miscellaneous

| Python Method | Description |
|--------------|-------------|
| `GetRootFrameID()` | `GetRootFrame_Func` (scanner: `\x05\xd8\xfe\xff\xff\xc3`) |
| `IsWorldMapShowing()` | `WorldMapState_Addr` check |
| `IsUIDrawn()` | `ui_drawn_addr` check |
| `SetOpenLinks(toggle)` | Toggles browser link opening behavior |
| `DrawOnCompass(session, points)` | `DrawOnCompass_Func` |
| `GetCurrentTooltipAddress()` | `CurrentTooltipPtr` dereference |
| `GetPreferenceOptions / GetEnumPreference / GetIntPreference / GetStringPreference / GetBoolPreference` | Preference system |
| `SetEnumPreference / SetIntPreference / SetStringPreference / SetBoolPreference` | Preference setter (game thread) |
| `GetFrameLimit / SetFrameLimit` | Global frame limit |
| `GetKeyMappings / SetKeyMappings` | Key remapping table |
| `GetFrameLogs / ClearFrameLogs` | GWCA frame creation log instrumentation |
| `GetUIPayloads / ClearUIPayloads` | GWCA UI message payload log |
| `FindAvailableChildSlot(parent)` | Scans child_offset_ids 0x20-0xFE |
| `ResolveDevTextDialogProc()` | String xref to `"DlgDevText"` → ToFunctionStart |
| `EnsureDevTextSource / OpenDevTextWindow / GetDevTextFrameID / RestoreDevTextSource` | DevText specimen window management |
| `ResolveObservedContentHostByFrameId(root)` | Path `{0, 0, 0}` under root |
| `ClearFrameChildrenRecursiveByFrameId(frame)` | Scanner: `\x55\x8B\xEC\x83\xEC\x08\x56\x8B\x75\x08\x85\xF6\x75\x19` |
| `ClearWindowContentsByFrameId(root)` | ResolveContentHost + ClearChildren + Redraw |
| `HasNextCreatedWindowTitle / IsWindowTitleHookInstalled / GetLastAppliedWindowTitleFrameId` | Title hook state queries |
