# Window Title Rendering — Investigation Summary (2026-06-02)

## ✅ WORKING SOLUTION (2026-06-02)

After 11 failed approaches across 3 RE sessions, the title rendering pipeline has been resolved.

### Working Pipeline: `send_title_msg_5e`

```
Python:  UIManager.send_title_msg_5e(frame_id, "My Title")
  → C++: UIManager::SetFrameTitleAndInvalidate(frame_id, title)
    → Ui_CreateEncodedText(8, 7, "My Title", 0)   @ pattern-resolved
    → Ui_SetFrameText(frame, encoded_text)          @ DevText call-site derived
    → PerFrameInvalidate(frame_id, 0xFFFFFFFF)     @ 0x0062bd80 (05-30-2026)
  → Title renders in title bar ✅
```

### Key Insight: Byte Pattern Resolution Failure

The root cause of ALL prior failures was non-unique byte patterns for `Ui_SetFrameText`. The function prologue (`55 8B EC 53 56 57 ... 75 14 68 XX XX XX XX`) is shared by **16 functions** in FrApi.cpp. `Scanner::Find` returns the first (lowest-address) match, which is NEVER `Ui_SetFrameText`.

**Solution**: Derive `Ui_SetFrameText` from DevText's call site. The DevText proc at `FUN_0088a870` calls `Ui_CreateEncodedText(8, 7, "DlgDevText", 0)` followed by `Ui_SetFrameText(frame, result)`. By resolving "DlgDevText" string use → scanning forward for the first CALL (Ui_CreateEncodedText) → next CALL = Ui_SetFrameText. This structural relationship is stable across EXE builds.

### 05-30-2026 Key Addresses

| Function | Address | Resolution |
|----------|---------|------------|
| `Ui_CreateEncodedText` | `0x007c3be0` | Wildcarded pattern: `55 8B EC 51 56 57 E8 ?? ?? ?? ?? 8B 48 18 E8 ?? ?? ?? ?? 8B F8` (2 matches, first=correct) |
| `Ui_SetFrameText` | `0x0062fab0` | Derived from DevText call site (NOT byte pattern — matches 16 locations) |
| `PerFrameInvalidate` | `0x0062bd80` | Pattern: `8D 48 04 53 6A 04 E8` → ToFunctionStart(-0x57) |
| DevText proc | `0x0088a870` | `FindNthUseOfString(L"DlgDevText", ...)` |
| DlgDevText string | `0x00b9743c` | String reference in DevText proc |
| CALL UiCreateEncodedText | `0x0088a9fc` | Return address: `0x0088aa01` |
| CALL UiSetFrameText | `0x0088aa03` | Return address: `0x0088aa08` |

### Python API

```python
# Cold container + title
frame_id = PyUIManager.UIManager.create_titled_container_window(
    x, y, w, h, "", 9, 0, 0x20, 0x6, 0x59)
PyUIManager.UIManager.send_title_msg_5e(frame_id, "My Custom Title")
```

### C++ Implementation

`py_ui.h` — `UIManagerCNonclient::SendTitleMsg5E()` delegates to `UIManager::SetFrameTitleAndInvalidate()` which calls:
1. `SetFrameTitleByFrameId()` — resolves `Ui_CreateEncodedText` (wildcarded) and `Ui_SetFrameText` (DevText-derived), creates encoded text, stores on frame
2. `FrameContentInvalidate(0xFFFFFFFF)` — per-frame CContent invalidation, sets paint mask, enqueues dirty list

---

## Original Investigation (2026-05-31 to 2026-06-02)

### What Works

1. **Window Creation** ✅: `CContainerFrame` + `FrameNewSubclass(CRProc, 0x59)` + `FrameMouseEnable`
2. **Per-Frame CContent Invalidation** ✅: `Ui_InvalidateFrameContent` sets paint mask + dirty list enqueue
3. **DevText Clone Creation** ✅: Creates with working mask, default "DlgDevText" title renders

### What Failed (11 Approaches)

| # | Approach | Root Cause |
|---|----------|------------|
| 1 | `Ui_SetFrameText` alone | Path B — global invalidation, no per-frame dirty list |
| 2 | `Ui_SetFrameText` + `Ui_InvalidateFrameContent` | Text stored but CRProc can't read it on cold containers |
| 3 | DevText clone + title hook (SetNextCreatedWindowTitle) | Return address comparison failed, then byte patterns broken |
| 4 | Direct ctypes calls to Ui_CreateEncodedText | Returned null payload or crashed |
| 5 | Byte pattern fixes (extended unique bytes) | Hardcoded CALL displacements + assertion lines changed in 05-30-2026 |
| 6 | Deferred invalidation (separate tick) | Async decode timing unpredictable |
| 7 | Deferred ShowFrame | Frame already shown by CreateContainerWindow |
| 8 | CNonclient proc install via FrameNewSubclass | Proc installed but never received msg 0x09 init |
| 9 | Custom frame proc during FrameCreate | Broke mouse interaction |
| 10 | Manual msg 0x09 via SendFrameUIMessageWString | Client crash — re-sending lifecycle message |
| 11 | Text label child as title workaround | Text renders inside content area, not title bar |

### The Two-Path Problem

| | Path A (WORKS) | Path B (BROKEN) |
|---|---|---|
| Entry | `FrameSetTitle` → `CNonclient::SetTitle` | `Ui_SetFrameText` |
| Invalidation | `CContent::Invalidate(frame+4, element=4, 0xFFFFFFFF)` — per-frame dirty list | `Ui_QueueGlobalUiUpdate` — GLOBAL context |
| Used by | DevText, DialogShow, all native windows | Runtime title changes |
| Cold container | NOT available (FrameSetTitle EXE address unknown) | Text stores but doesn't render |

### Byte Pattern Anti-Patterns

**DON'T USE** these byte patterns for `Ui_SetFrameText`:
```
55 8B EC 53 56 57 8B 7D 08 8B F7 F7 DE 1B F6 85 FF 75 14 68 ?? ?? ?? ??
```
Matches **16 functions** in 05-30-2026 EXE. Scanner returns wrong function. Use DevText call-site derivation instead.

**DON'T USE** hardcoded assertion line numbers:
```
68 C3 0B 00 00  → PUSH 0xBC3 (Symbols) ≠ PUSH 0xC22 (05-30-2026)
68 D2 0B 00 00  → PUSH 0xBD2 (Symbols) ≠ PUSH 0xC31 (05-30-2026)
```
These change with every EXE patch.

### Frame Layout

```
+0x00  field1_0x0
+0x04  CContent subobject start
+0x14  paint_mask (CContent element 4 flags)
+0x18  visibility_flags (= CContent+0x14)
+0xA8  CMsg message handler
+0xBC  frame_id
+0xCC  CNonclient subobject
+0x18C frame_state
Size:  0x1C8
```

### CRProc msg 0x08 Title Render Guard

```c
if ((paint_mask & 8) && (subclass_flags & 0x40)) {
    // title rendering path
    text_caption = Ui_GetFrameTextCaptionText(frame);
    resource_caption = Ui_GetFrameResourceCaptionText(frame);
    // format and render...
}
```

### Subclass Flags

| Bit | Value | Meaning |
|-----|-------|---------|
| 0 | 0x01 | Has title bar area (resizable) |
| 3 | 0x08 | Has close button |
| 4 | 0x10 | Has minimize button |
| 6 | 0x40 | HAS_CHROME — enables title rendering |
| 7 | 0x80 | Has maximize/restore? |

`0x59 = 0x01 | 0x08 | 0x10 | 0x40`

### Per-Frame Dirty List

| List | WASM | 05-30-2026 EXE |
|------|------|----------------|
| CContent dirty list head | `DAT_ram_005a02f8` | Different (CODE bytes at that address) |
| Link offset | `DAT_ram_005a02f4` | Different |
| Global UI dirty list | — | `0x00BD0188` |
