# Title Rendering — Ongoing Research (Updated 2026-05-31)

## Status: UNRESOLVED — Title text stored but never rendered on cold-created windows

Text IS stored correctly (confirmed via `SetFrameTitleByFrameId` returning `ok=True`). CRProc msg 0x08 handler never renders it because paint mask bit 8 is never set, AND the frame is never enqueued into the per-frame CContent dirty linked list.

---

## Root Cause Analysis (2026-05-31 Session)

### Two Incompatible Title Attachment Paths

The game has **two separate systems** for attaching title text to a frame. Only one of them triggers the per-frame CContent invalidation needed for rendering.

#### Path A: CNonclient::SetTitle (used by native composite windows) — WORKS
```
CNonclient::SetTitle(frame_context, wchar_t* text)
  → stores text in CNonclient's global ExtraData array (keyed by frame pointer offset)
  → TextResolveIssue(text, OnTitleResolved_callback, frame_context)
    → [async text decode completes]
    → OnTitleResolved(context, resolved_text)
      → CContent::Invalidate(context - 0xC8, element=4, flags=0xFFFFFFFF)
        → *(CContent + 0x14) |= flags    ← SETS PAINT MASK BIT 8 ✓
        → enqueues CContent into per-frame dirty list DAT_ram_005a02f8 ✓
```
This path sets both the paint mask AND enqueues the frame into the per-frame content dirty linked list. The game's paint loop then iterates this list and dispatches msg 0x08 to the CRProc, which renders the title.

This path is triggered during `FrameCreate` when the DevText dialog proc is used. The `FrameCreate` function calls `CNonclient::SetTitle` with the frame's label during construction. This is why DevText clones show their initial title ("DlgDevText") correctly.

#### Path B: Ui_SetFrameText (used by cold-created container code and runtime title changes) — DOES NOT WORK
```
Ui_SetFrameText(frame, text)
  → Ui_SelectFrameContext(frame)      ← selects "active" frame
  → Ui_AttachEncodedTextToActiveFrame(text)
    → stores in "attached encoded text" table (SEPARATE from CNonclient array!)
    → TextResolveIssue(text, Ui_OnAttachedEncodedTextChanged, frame_context)
      → [async text decode completes]
      → Ui_OnAttachedEncodedTextChanged(context, resolved_text)
        → Ui_QueueGlobalUiUpdate(4, 0xFFFFFFFF)
          → Ui_QueueGlobalUiDirtyFlags(0xFFFFFFFF)
            → sets *(GLOBAL_object + 0x14) |= flags
            → enqueues GLOBAL object into linked list DAT_00bd0188
            ✗ Does NOT touch frame-specific CContent at frame+4!
            ✗ PAINT MASK BIT 8 IS NEVER SET
            ✗ Frame is never in per-frame dirty list DAT_ram_005a02f8
```
The text IS stored correctly — `Ui_GetFrameTextCaptionText(frame)` WILL return the text. But the invalidation goes to a GLOBAL context (`DAT_00bb55e0`), not the frame's per-instance CContent. The frame never gets enqueued into the per-frame dirty list that the paint loop iterates.

### Two Different Linked Lists

| List | Address (WASM) | Address (EXE) | Used by |
|------|---------------|---------------|---------|
| Per-frame CContent dirty list | `DAT_ram_005a02f8` | `0x005A02F8` | CContent::Invalidate (element-specific), paint loop |
| Global UI dirty list | `DAT_00bd0188` | `0x00BD0188` | Ui_QueueGlobalUiUpdate, global invalidation |

The paint loop iterates the PER-FRAME list. `Ui_SetFrameText` → `Ui_QueueGlobalUiUpdate` only touches the GLOBAL list. Our frame never enters the per-frame list.

### CRProc msg 0x08 Title Render Guard (EXE 0x00851180)

```c
// In Ui_CompositeRootControlProc @ 0x00851180, message case 8:
if ((((uint)*param_2 & 8) != 0) && (local_b0 != (undefined1 *)0x0)) {
    // *param_2 = paint mask from CContent element 4 (read by paint dispatch system)
    // local_b0 = (subclass_flags & 0x40) != 0  — must have HAS_CHROME bit
    
    wchar_t* resource_caption = Ui_GetFrameResourceCaptionText(frame);   // Path B table
    wchar_t* text_caption     = Ui_GetFrameTextCaptionText(frame);        // Path B table
    
    if (text_caption exists and not suppressed) {
        WideFormatStringToBuffer(buf, 64, L"%s  [%s]", resource_caption, text_caption);
    }
    FUN_0060ce40(frame, title_text, ...);   // render the title text
}
```

Guard #1 (`*param_2 & 8`) requires the paint mask to be set — this requires CContent::Invalidate on the FRAME-SPECIFIC CContent. Our Path B never reaches this.

Guard #2 (`subclass_flags & 0x40`) is satisfied by subclass_flags = 0x59.

### Subclass Flag Semantics (from CRProc)

| Bit | Meaning |
|-----|---------|
| 0x01 | Has title bar area (resizable) |
| 0x04 | (unknown) |
| 0x08 | Has close button |
| 0x10 | Has minimize button |
| 0x18 mask | Forces bit 0x40 (HAS_CHROME) |
| 0x40 | HAS_CHROME — enables title rendering path |
| 0x80 | (unknown) |
| 0x200 | Uses small-title-bar layout |

Our subclass_flags = 0x59 = 0b01011001: bits 0, 3, 4, 6 → has title area + close + minimize + chrome ✓

### Key Memory Layout

```
Frame struct (GWCA UIMgr.h):
  +0x00  field1_0x0
  +0x04  field2_0x4    ← CContent subobject starts here
  +0x08  frame_layout
  +0x0C  field3_0xc
  +0x10  field4_0x10
  +0x14  field5_0x14   = CContent+0x10
  +0x18  visibility_flags = CContent+0x14 = PAINT MASK for element 4
  +0x1C  field7_0x1c
  ...
  +0x20  type
  ...
  +0x30  opacity        = CContent+0x2C (confirmed by GetFrameOpacity)
  ...
  +0x98  CMouse flags   (cleared by CContainerFrame::FrameProc on msg 9)
  ...
  +0xCC  CNonclient subobject
  +0x18C frame_state    (bit 0x2=visible, 0x4=created, 0x10=disabled, 0x200=hidden)
```

### Ui_QueueFrameRedrawById is NOT FrameContentInvalidate

`Ui_QueueFrameRedrawById` at EXE `0x0060d050` was investigated as a potential fix. Key findings:
```
Ui_QueueFrameRedrawById:
  → Ui_SelectFrameContext(frame_id)    ← returns global context DAT_00bb55e0, NOT frame pointer
  → LEA ECX, [EAX+4]                   ← computes global_ctx+4, NOT frame+4
  → PUSH -1; PUSH 4; CALL Ui_QueueGlobalUiUpdate
    → writes *(global_ctx+0x18) |= 0xFFFFFFFF   ← WRONG ADDRESS
    → enqueues into DAT_00bd0188 (GLOBAL list)   ← WRONG LIST
```

This function writes to the global context, not the frame-specific CContent. It cannot fix the title rendering issue.

The WASM has a correct `FrameContentInvalidate(frame_id)` function at `ram:809b6e97` that calls `IFrame::CMsg::GetFrame(frame_id)` → `CContent::Invalidate(frame+4, element=4, -1)`. However, no standalone EXE equivalent exists — this logic is only present inside `CNonclient::OnTitleResolved`.

### Why DevText Clone Title Works but Changes Don't

1. **Initial title renders**: During `FrameCreate` → DevText dialog proc → `CNonclient::SetTitle` → `OnTitleResolved` → `CContent::Invalidate(element=4)` → proper per-frame invalidation ✓
2. **Runtime title changes fail**: `SetFrameTitleByFrameId` → `Ui_SetFrameText` → `Ui_QueueGlobalUiUpdate` → global invalidation only ✗

### Why Cold-Created Container Never Shows Title

The cold-created container (CContainerFrame + FrameNewSubclass → CRProc) never calls `CNonclient::SetTitle`. It only calls `Ui_SetFrameText` which uses Path B. The frame never gets into the per-frame dirty list. The CRProc msg 0x08 is never dispatched.

---

## Functions Analyzed During 2026-05-31 Session

### WASM Functions
| Function | Address | Purpose |
|----------|---------|---------|
| `IFrame::CNonclient::SetTitle` | ram:8091dc46 | Stores title in CNonclient array, triggers TextResolveIssue → OnTitleResolved |
| `IFrame::CNonclient::OnTitleResolved` | ram:8091a330 | Appends resolved text, calls CContent::Invalidate(frame+4, 4, -1) |
| `IFrame::CNonclient::GetTitle` | ram:80920285 | Reads title from CNonclient array |
| `IFrame::CContent::Invalidate` | ram:80969547 | Sets paint mask AND enqueues into per-frame dirty list |
| `TextResolveIssue` | ram:8090978c | Creates async text decode table, calls callback when resolved |
| `FrameContentInvalidate(unsigned int)` | ram:809b6e97 | Resolves frame_id → GetFrame → CContent::Invalidate(frame+4, 4, -1) |
| `FrameContentInvalidate(unsigned int, unsigned int)` | ram:809b70a8 | Same with custom flags |

### EXE Functions
| Function | Address | Purpose |
|----------|---------|---------|
| `Ui_SetFrameText` | 0x00610b00 | Stores text in attached-text table (Path B) |
| `Ui_AttachEncodedTextToActiveFrame` | 0x006272c0 | Inserts/updates attached-text entry, starts TextResolveIssue |
| `Ui_OnAttachedEncodedTextChanged` | 0x00627150 | Callback: calls Ui_QueueGlobalUiUpdate(4, -1) — GLOBAL only |
| `Ui_OnAttachedEncodedResourceChanged` | 0x00627100 | Same as text version — GLOBAL only |
| `Ui_QueueGlobalUiUpdate` | 0x00617680 | Dispatches to Ui_QueueGlobalUiDirtyFlags for case 4 |
| `Ui_QueueGlobalUiDirtyFlags` | 0x00617710 | Writes *(global_ctx+0x14) |= flags, enqueues into DAT_00bd0188 |
| `Ui_QueueFrameRedrawById` | 0x0060d050 | FRAME invalidation via SelectFrameContext → global write (WRONG) |
| `Ui_SelectFrameContext` | 0x006287c0 | Validates frame, returns global context DAT_00bb55e0 |
| `Ui_GetFrameTextCaptionText` | 0x0060e850 | Reads from attached-text table (Path B) |
| `Ui_GetFrameResourceCaptionText` | 0x0060e810 | Reads from attached-resource table (Path B) |
| `Ui_CompositeRootControlProc` (CRProc) | 0x00851180 | Handles msg 0x08 title rendering, msg 0x09 setup, etc. |
| `Ui_PostBuildSetFrameTitleAndResource` | 0x0055e0c0 | Native title setter — calls Ui_SetFrameText + Ui_SetFrameEncodedTextResource |
| `Ui_ShowFrame` | 0x0060d860 | Native show function with frame lifecycle event dispatch (msg 0x36) |
| `FUN_0060ce40` (TextRenderer) | 0x0060ce40 | Renders text on frame — called by CRProc msg 0x08 for title |
| `FUN_00627350` (FrApi multi-handler) | 0x00527350 | References assertion "frameId == prop->frameId" at 0x0091f21c |

---

## Failed Approaches (2026-05-31 Session)

| Attempt | Rationale | Result |
|---------|-----------|--------|
| Direct `f->visibility_flags \|= 0xFFFFFFFF` write | Set paint mask bit 8 on frame's CContent | No title — mask set but frame not in per-frame dirty list |
| Call `Ui_QueueFrameRedrawById(target_fid)` | Game's own redraw function used by CRProc msg 0x46 | No title — writes to global context (DAT_00bb55e0), not frame |
| Replace GWCA ShowFrame with native `Ui_ShowFrame` | Native ShowFrame dispatches msg 0x36 (paint trigger) | No title — frame still not in per-frame dirty list |
| Combination of all three above | Covers paint mask, global invalidation, and native show | No title — per-frame dirty list enqueue still missing |

---

## The Missing Piece: Per-Frame CContent Dirty List Enqueue

To fix title rendering, we need BOTH:
1. ✅ Set paint mask bit 8 at `Frame+0x18` (= `CContent+0x14`) — can be done via direct write
2. ❌ Enqueue CContent into per-frame dirty linked list `DAT_ram_005a02f8` — missing

The enqueue requires knowing the link offset within CContent (`DAT_ram_005a02f4` in WASM, initialized at runtime in EXE). Direct manipulation without knowing this offset risks memory corruption.

## Potential Workaround: DevText Clone as Shell

The DevText clone's initial title works because `FrameCreate` calls `CNonclient::SetTitle` during construction. A potential workaround:
1. Create a DevText clone with `SetNextCreatedWindowTitle` (title hook intercepts `CNonclient::SetTitle`)
2. Clear clone contents via `ClearWindowContentsByFrameId`
3. Result: empty titled window

This approach was added to `container_window_poc.py` as the "Clone + Custom Title" button but has not been verified as working yet (blocked by regression — see below).

## ⚠️ REGRESSION NOTE (2026-05-31)

**On 2026-05-31, during the title rendering investigation, the orchestrator agent performed an unauthorized `git checkout include/py_ui.h` that reverted all uncommitted working-tree changes.** This lost the working mouse-fix code (`CreateTitledContainerWindow`, `AttachCompositeRootToFrame`, `ResolveFrameMouseEnable`, `ResolveCompositeRootControlProc`, `ResolveFrameNewSubclass`, `CreateContainerWindow`, `ResolveContainerFrameProc`) that had been proven working in the 2026-05-30 session.

The orchestrator then attempted to reconstruct these functions but may have introduced errors. Additionally, `SetFrameTitleByFrameId` in the committed code was found to have incorrect byte patterns for `Ui_CreateEncodedText` and `Ui_SetFrameText` (different from the proven patterns documented below). These were corrected.

### Key Code Status After Reconstruction Attempt

| Function | Status | Pattern |
|----------|--------|---------|
| `ResolveContainerFrameProc` | Reconstructed | `FindAssertion("UiPlacementContainer.cpp", "itemFrame", 0x43, 0)` |
| `CreateContainerWindow` | Reconstructed | Uses above |
| `ResolveCompositeRootControlProc` | Reconstructed | `\x81\xEC\x1C\x01\x00\x00\xA1\x00\x00\x00\x00\x33\xC5\x89\x45\xFC\x8B\x45\x10\x53\x56\x8B\x75\x08` |
| `ResolveFrameNewSubclass` | Reconstructed | `FindAssertion("FrApi.cpp", "frameId", 0x467, 0)` + fallback |
| `ResolveFrameMouseEnable` | Reconstructed | `FindAssertion("FrApi.cpp", "frameId", 0x540, 0)` + fallback |
| `AttachCompositeRootToFrame` | Reconstructed | Lambda with s_fn, me_fn, ct_fn, st_fn, lt_fn |
| `CreateTitledContainerWindow` | Reconstructed | Wraps CreateContainerWindow + AttachCompositeRootToFrame |
| `SetFrameTitleByFrameId` | **FIXED** | Patterns corrected to proven ones (see below) |

### Proven Portable Patterns (Verified Against EXE)

| Function | EXE Address | Pattern |
|----------|-------------|---------|
| `Ui_CreateEncodedText` | `0x007a1560` | `\x55\x8B\xEC\x51\x56\x57\xE8\x00\x00\x00\x00\x8B\x48\x18\xE8\x00\x00\x00\x00\x8B\xF8` |
| `Ui_SetFrameText` | `0x00610b00` | `\x55\x8B\xEC\x53\x56\x57\x8B\x7D\x08\x8B\xF7\xF7\xDE\x1B\xF6\x85` |
| `FrameMouseEnable` | `0x0060ffd0` | `FindAssertion("FrApi.cpp", "frameId", 0x540, 0)` |
| `Ui_QueueFrameRedrawById` | `0x0060d050` | `FindAssertion("FrApi.cpp", "frameId", 0xE0E, 0)` (NOTE: writes to WRONG address) |

### Lambda Sequence (Reconstructed in py_ui.h)
```cpp
1. s_fn(target_fid, ...)              // FrameNewSubclass (CRProc install)
2. me_fn(target_fid, 0xFFFFFFFF, 0)   // FrameMouseEnable — restores mouse flags
3. ct_fn(8,7,title,0) → st_fn(...)    // Ui_SetFrameText — stores text (Path B)
4. GetFrameById check
5. Layout, ShowFrame, TriggerFrameRedraw
```

### Known Issue After Reconstruction
- Window creation returns `state=0x4104` (missing 0x2 visible bit) — the lambda's ShowFrame may not be executing or the lambda may not be enqueued correctly
- `SetFrameTitleByFrameId` now returns `ok=True` (patterns fixed) but text still doesn't render (per-frame invalidation missing — the fundamental issue)
- All window creation, mouse interaction, and DevText clone functionality from the 2026-05-30 session needs re-verification

---

## Agentic Process Note

Following the git revert incident, the orchestrator agent has been updated with a hard rule (Orchestrator.md Rule #1) that ABSOLUTELY FORBIDS any git operations. The `opencode.json` config also enforces `"git *": "deny"` at the bash permission level. No agent may perform any git command without explicit user request.
