# Arbitrary Window Creation — WASM Architecture Analysis

Date: 2026-05-30
Source: `/Gw.wasm` via Ghidra MCP
Context: Existing Python path clones DevText; goal is to find a cleaner or more direct way.

## Current Approach: DevText Clone

The Python `CreateWindowClone()` works by:
1. Opening DevText temporarily (keypress 0x25) to "warm up" its global state
2. Resolving `DlgDevTextProc` @ WASM ram:81393b1b via string xref
3. Calling `CreateUIComponent` → `FrameCreate` with DevText's proc
4. DevText's proc receives msg 9 → creates debug text content
5. Clearing children of child 0 to remove unwanted content
6. Redrawing

**Problems:**
- Requires DevText to be open first (global state dependency)
- Creates unwanted content that must be cleared
- Inherits DevText's lifecycle behavior
- The proc assumes certain global state (string table, etc.)

## The Real Window Factory: DialogShow

`IUi::Game::DialogShow(parent, EFloatingDialog, flags, create_param)` @ ram:815cdb8c

This is the game's native window factory. From its callee list:

```
DialogShow(parent, dialog_enum, flags, create_param)
  │
  ├─ 1. Resolve descriptor from compiled table
  │      dialog_enum → {FrameProc*, title, size, layer, ...}
  │
  ├─ 2. FrameGetChild(parent, dialog_enum + 0x13) → destroy if exists
  │
  ├─ 3. FrameCreate(parent, flags, child, proc, param, label)
  ├─ 4. FrameNewSubclass(frame, subclass_proc, flags)
  ├─ 5. FrameSetTitle(frame, title)
  ├─ 6. FrameSetTitleHotkey(frame, hotkey)
  ├─ 7. FrameGamepadEnable / FrameGamepadEnterCursorMode
  ├─ 8. FramePlaceChildren(frame, L"GmView-Dialog")
  ├─ 9. PrefGetWindow → FrameSetPosition (saved position restore)
  ├─10. FrameSetHeight / FrameSetWidth
  ├─11. FrameSetLayer
  ├─12. FrameShow(frame, 1)
  └─13. FrameActivate(frame)
```

### FrameNewSubclass — The Window Chrome Installer

`FrameNewSubclass` @ WASM `ram:809a2ebf` = EXE `Ui_AttachCurrentHandlerSlot` @ `0x00610340` is the function that installs window chrome on a bare frame.

**Signature:** `void*(__cdecl*)(uint32_t frame_id, void* subclass_proc, void* subclass_flags)` — returns pointer to the handler slot (can be ignored). Calls `Ui_SelectFrameContext` → `Ui_GetCurrentHandlerTailSlot` → `Ui_SetHandlerSlot(frame_ctx+0xA8, slot, subclass_proc, subclass_flags)`.

**Scanner patterns (in order of preference):**
1. **Assertion-based** (GWCA convention): `FindAssertion("\\Code\\Engine\\Frame\\FrApi.cpp", "frameId", 0x467, 0)` + `ToFunctionStart(addr, 0x210)`
2. **Fallback byte pattern**: `\xFF\x75\x10\x8B\xF0\x8B\xCF\xFF\x75\x0C\x56` — PUSH subclass_flags; MOV ESI,EAX; MOV ECX,EDI; PUSH subclass_proc; PUSH ESI (Ui_SetHandlerSlot argument setup — unique to this function)
3. **WARNING**: Simple prologue patterns like `\x55\x8B\xEC\x8B\x45\x08\x85\xC0\x75\x18` match thousands of functions. Always use assertion-based or unique internal-instruction patterns.

### Subclass Flags 0x59 — Confirmed

From decompilation of `Ui_CompositeRootControlProc` @ EXE `0x00851180`, subclass flags `0x59 = 0x01 | 0x08 | 0x10 | 0x40`:

| Bit | Value | Effect |
|-----|-------|--------|
| 0 | 0x01 | Title bar + `[X]` close button + drag-to-move hit-test |
| 3 | 0x08 | Right/bottom resize handles |
| 4 | 0x10 | Left/top resize handles |
| 6 | 0x40 | Chrome rendering flag — enables ALL chrome drawing (title bar background, borders, close button image). Auto-set when 0x18 is present via `if (pvVar4 & 0x18) pvVar13 \|= 0x40` |

Bits NOT set by 0x59 (and not needed for a basic titled window): `0x200` (gamepad mode), `0x100` (bottom exit button), `0x20` (layout override), `0x04` (focus broadcast).

### Mouse Interaction via Ui_CompositeRootControlProc

Mouse handling lives in `Ui_CompositeRootControlProc` @ EXE `0x00851180`, NOT in `CContainerFrame::FrameProc`:

- **msg 0x08** (paint): Renders title bar background, borders, close button image, resize handles. Checks bit `0x40` (chrome rendering flag) and bit `0x01` to draw title bar text and `[X]` close button.
- **msg 0x17** (hit-test): Resolves click targets — title bar region → drag cursor, border regions → resize cursors, close button region → close action.
- **Critical dependency**: These only work AFTER `FrameNewSubclass` installs `Ui_CompositeRootControlProc`. A bare `CContainerFrame` has no chrome-hit logic.

### The Descriptor Table Problem

`IUi::Game::DialogToggle(parent, dialog_enum, param)` @ ram:815ead1e:

```
child = FrameGetChild(parent, dialog_enum + 0x13)
if child exists:
    return  // already open — caller would destroy to toggle off
else:
    DialogShow(parent, dialog_enum, 0, param)  // open with visible flag
```

### Child Slot Convention

Each floating dialog has a fixed child slot: `child_index = dialog_enum + 0x13`
The dialog host container is at child 0x5C.

## The Descriptor Table Problem

The compiled-in descriptor table maps each `EFloatingDialog` value to window parameters.
We currently don't have the WASM address of this table, but each entry likely contains:

```c
struct FloatingDialogDescriptor {
    void*    frame_proc;        // FrameProc function pointer
    wchar_t* title;             // or uint32 title_string_id
    float    default_width;
    float    default_height;
    int      default_layer;
    uint32_t flags;             // creation flags
    wchar_t* hotkey_text;       // optional hotkey for title bar
    void*    subclass_proc;     // optional subclass proc
};
```

## Minimal Window Proc Requirements

`FrameCreate` takes any proc address. The proc receives FrameMsgHdr messages.
For a minimal working window, the proc only needs to handle:

```
Message 0x09 (Create):
  - Enable mouse: FrameTestStyles + bit set
  - Enable gamepad: FrameGamepadEnable
  - Create child 0 as content host: FrameCreate(parent, 0, 0, host_proc, NULL, L"")
  - Set min/max size: FrameSetMinSize / FrameSetMaxSize
  - Register for desired messages: FrameMsgRegister

Message 0x0A (Destroy):
  - Clean up children/resources

Message 0x24 (Mouse down):
  - Forward or ignore

Message 0x0C (Show):
  - Propagate to children

Message 0x0D (Hide):
  - Propagate to children
```

## Potential Cleaner Approaches

### Approach A: Use CContainerFrame::FrameProc — ★ CONFIRMED & IMPLEMENTED

`IUi::Game::CContainerFrame::FrameProc` @ ram:812a7233 / EXE `0x00871b40` is a generic container
that handles basic window lifecycle without creating unwanted content. This approach has been
validated through implementation as `CreateTitledContainerWindow()` in `py_ui.h`. The complete
pipeline: `CreateContainerWindow` → `FrameNewSubclass(Ui_CompositeRootControlProc, 0x59)` → `SetFrameTitleByFrameId` → show/redraw. See `UI_RE/container_window_poc.py` for the Python test harness.

### Approach B: Call DialogShow Pipeline Steps Manually

Since we know all the steps, we could replicate them in C++:
```c
uint32_t CreateMinimalWindow(parent, x, y, w, h, title) {
    // 1. Find free child slot (same as current FindAvailableChildSlot)
    child = FindAvailableChildSlot(parent);
    
    // 2. FrameCreate with minimal proc
    frame = FrameCreate(parent, 0x20, child, MinimalProc, create_param, title);
    
    // 3. Title — already set by FrameCreate's label param
    // 4. Position
    FrameSetPosition(frame, x, y);
    
    // 5. Size
    FrameSetWidth(frame, w);
    FrameSetHeight(frame, h);
    
    // 6. Layout
    FramePlaceChildren(frame, L"GmView-Dialog");
    
    // 7. Show
    FrameShow(frame, 1);
    
    return frame;
}
```

### Approach C: Find a No-Op Proc

Search for a frame proc in the WASM that:
- Handles msg 9 with minimal setup
- Does NOT create content (unlike DevText which creates debug text)
- Does NOT depend on global state (unlike DevText which needs string table)

Candidates:
- `CContainerFrame::FrameProc` @ ram:812a7233
- A simple button/label proc that just passes through
- Any proc from the `Ctl*` family that's known to be minimal

### Approach D: Continue Improving DevText Clone

The current approach works. Improvements:
- Find a proc that doesn't create content → skip the "clear children" step
- Cache the proc address → skip the "open DevText temporarily" step
- Find a window spec that has the right frame flags (title bar, resizable, etc.)

## Key WASM Addresses for Window Creation

| Function | WASM Address | Role |
|----------|-------------|------|
| `FrameCreate` | ram:809a13ea | Low-level frame constructor |
| `FrameDestroy` | ram:809a1b36 | Frame destruction |
| `FrameNewSubclass` (= `Ui_AttachCurrentHandlerSlot`) | ram:809a2ebf, EXE:0x00610340 | Install subclass proc (window chrome). Scanner: `FindAssertion("FrApi.cpp","frameId",0x467,0)` |
| `Ui_CompositeRootControlProc` | EXE:0x00851180 | Window chrome proc. Scanner: `\x81\xEC\x1C\x01\x00\x00\xA1????\x33\xC5...` |
| `FrameSetTitle` | ram:809b0a9b | Set title text |
| `FrameSetTitleHotkey` | ram:809b0c8d | Set title with hotkey |
| `FrameShow` | ram:809a5e39 | Show frame |
| `FrameActivate` | ram:809b0e7f | Activate frame |
| `FramePlaceChildren` | ram:809a7f5e | Layout with policy name |
| `FrameSetPosition` | ram:809a9f40 | Set position |
| `FrameSetSize` | ram:809a9c3e | Set size |
| `FrameSetLayer` | ram:809b060f | Set Z-layer |
| `FrameGamepadEnable` | ram:809a4c8d | Gamepad support |
| `DialogShow` | ram:815cdb8c | Full window factory |
| `DialogToggle` | ram:815ead1e | Toggle pattern |
| `IUi::DlgDevTextProc` | ram:81393b1b | DevText frame proc |
| `CContainerFrame::FrameProc` | ram:812a7233 | Generic container proc |
| `InventoryAggregateFrameProc` | ram:8154ac7f | Inventory aggregate proc |
| `CAggregateInv::FrameProc` | ram:8154ad67 | Inner inventory proc |
| `CAggregateInv::OnFrameCreate` | ram:81549948 | Inventory create handler |

## Recommendation

**Next step:** Decompile `CContainerFrame::FrameProc` to determine if it's minimal enough
to cold-create without side effects. If it handles msg 9 without creating content or
requiring global state, it could replace DevText as the clone source.

If not feasible, improve the DevText clone path by:
1. Caching the proc address (avoid temp open/close)
2. Using a proc from the typed component family that's simpler

---

## ★ Solution Found: CContainerFrame::FrameProc

### Verification

Decompiled `CContainerFrame::FrameProc` @ WASM `ram:812a7233`. Result: **ideal minimal proc.**

Message dispatch behavior:

| Message | WASM Code Path | Effect |
|---------|---------------|--------|
| `0x09` (Create) | `FrameMouseEnable(frame, 0, 0xFFFFFFFF)` | Enables mouse input — **only action, no side effects** |
| `0x34` | Position lock calculation → `FrameScheduleSize` | Layout lock |
| `0x35-0x36` | Returns immediately | No-op |
| `0x37` (Size) | `CContainerFrame::OnFrameSize(frame, flags, size)` | Repositions children based on alignment (left/right/center/top/bottom) |
| `0x38` | Copies size data | Size passthrough |
| `0x39-0x55` | Returns immediately | No-op (20+ messages ignored) |
| `0x56` | `FrameCreate(parent, flags, child, proc, param, label)` | Creates child frames on demand |
| `0x57` | `FrameGetChild(frame, child_index)` then `FrameDestroy(child)` | Destroys a child |
| `0x58` | `FrameGetChild(frame, child_index)` | Returns child frame ID |
| All others | Returns immediately | No-op |

**`OnFrameSize`** @ ram:812a660d iterates all child frames and repositions them:
- `flags & 2` → right-aligned
- `flags & 4` → vertically centered
- `flags & 8` → right-aligned variant  
- `flags & 0x10` → bottom-aligned
- Gets native size → `FrameSetPosition(child, x, y)` → enumerates next child
- **Pure layout logic — no state dependencies, no content creation.**

### Confirmed Addresses

| Layer | Function | Address |
|-------|----------|---------|
| WASM | `IUi::CContainerFrame::FrameProc` | `ram:812a7233` |
| EXE | `FUN_00871b40` (CContainerFrame::FrameProc) | `0x00871b40` |
| WASM | `IUi::CContainerFrame::OnFrameSize` | `ram:812a660d` |
| WASM | `IUi::PlacementContainerFrameProc` (caller) | `ram:812a714b` |

**Address confirmed via string anchoring:**
- WASM string `"../../../../Gw/Ui/UiPlacementContainer.cpp"` @ `ram:00109e6b`
- EXE string `"P:\\Code\\Gw\\Ui\\UiPlacementContainer.cpp"` @ `0x00b6600c`
- Both referenced by assertions in CContainerFrame::FrameProc

### How to Use in Python/GWCA

```python
# Replace DevText clone with CContainerFrame
frame_id = UIManager.CreateWindowByFrameId(
    parent_frame_id=9,
    child_index=child_slot,
    frame_callback=0x00871b40,    # ★ CContainerFrame::FrameProc
    x=100, y=100,
    width=400, height=300,
    frame_flags=0x20,              # title bar
    frame_label="My Window"
)
# Frame is now a clean empty container — ready for children
UIManager.TriggerFrameRedrawByFrameId(frame_id)
```

### Comparison: DevText Clone vs. CContainerFrame

| Aspect | DevText Clone | CContainerFrame |
|--------|-------------|-----------------|
| Needs source window open first | Yes (keypress 0x25) | **No** |
| Creates unwanted content | Yes (debug text, child 0 content) | **No** |
| Requires ClearChildren after | Yes | **No** |
| Handles child sizing | Manual | **Automatic (OnFrameSize)** |
| Proc address stability | Resolved at runtime via string xref | **Fixed at 0x00871b40** |
| Cold-startable | No (needs warm global state) | **Yes** |
| Child creation | Manual via FrameCreate | Via msg 0x56 or direct FrameCreate |
| Can set title | Via hook | **Via FrameCreate label or FrameSetTitle** |

### Remaining Unknowns

1. **`[X]` close button** — KNOWN UNKNOWN. No evidence the CNonclient handles msg 0x0A (Destroy). The title bar's `[X]` button may not work. Test at runtime; fall back to Python-side `DestroyUIComponentByFrameId`.
2. **Byte pattern stability** — `Ui_CompositeRootControlProc`'s primary byte pattern will break if the `SUB ESP` immediate changes between patches. A fallback callee-anchor scan exists.
3. **Title rendering** — `SetFrameTitleByFrameId` must be called AFTER `FrameNewSubclass` installs the CNonclient (which reads the text payload in msg 0x08). The deferred lambda enforces this ordering.

### Resolved (Previously Unknown)

- ~~Does CContainerFrame need any special create_param?~~ → No — passes through to CreateUIComponent. Verified.
- ~~What frame_flags?~~ → Use `0` for chrome-free; subclass_flags `0x59` provides all chrome.
- ~~Does it need FramePlaceChildren?~~ → No — CContainerFrame::FrameProc handles msg 0x37 child layout directly.
