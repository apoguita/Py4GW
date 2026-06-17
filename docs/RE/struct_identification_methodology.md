# Struct Identification Methodology

> **Status**: Proven on PreGameContext (2026-06-06). Reusable on any GW context struct.
> **Goal**: Take a known-but-incomplete C++ context struct and recover its full layout, field types, sizes, and semantics from Ghidra-compiled WASM + EXE binaries.
> **Running Example**: `PreGameContext` (aka `CScene`) — was wrong in both Python and C++ GWCA; now fully resolved at 0x100 bytes with all 50+ fields named.

---

## 1. Overview

### What This Process Achieves

You have a C++ struct in GWCA that is **partially mapped** — some fields named, others `UnkXX[]` arrays, still others `hXXXX` float placeholders. The goal is to produce a **complete, verified struct layout** with:

- Every offset assigned a field name, type, and initialization value
- Type inference (float vs int32 vs pointer vs inline array vs sub-struct)
- Semantic meaning where possible (e.g., "camera_pitch_current", not "field_0x10")
- Independent verification from both WASM and EXE decompilation
- Size assertion (`static_assert(sizeof(...) == N)`)
- Ready-to-deploy Python ctypes and C++ header updates

### When To Use This Process

| Scenario | Use This? |
|----------|-----------|
| GWCA header has `UnkXX[]` arrays whose layout you want to resolve | ✅ Yes |
| Python struct has `field_N_0xXX` placeholders | ✅ Yes |
| Context size is unknown or disputed between C++/Python | ✅ Yes |
| Sub-struct (like `LoginCharacter` inside `PreGameContext`) needs layout fix | ✅ Yes |
| You want to discover a completely unknown struct from scratch | ⚠️ Partial — this assumes a starting pointer or PropGet access path exists |

### The PreGameContext Case

The `PreGameContext` struct was **wrong in both the C++ GWCA header and the Python ctypes struct** — a post-patch shift of +4 bytes across the 0xD0–0xE0 region went undetected. The `LoginCharacter` sub-struct had `Unk02[8]` instead of the correct `[7]`, and was missing `char_model_ptr` at +0x4C. The struct tail (0xEC–0xFF) was completely unknown. Over 6 rounds of analysis, the full 0x100-byte struct was resolved.

---

## 2. Prerequisites

Before starting, ensure you have:

### Data Sources

| Resource | Path | Role |
|----------|------|------|
| **GWCA C++ headers** | `Py4GW\vendor\gwca\Include\GWCA\Context\` | Current (possibly wrong) struct definitions |
| **Python ctypes structs** | `Py4GWCoreLib\native_src\context\` | Python-facing struct definitions (may differ from C++) |
| **GWCA source** | `Py4GW\vendor\gwca\Source\GWCA.cpp` | Shows how the context pointer is discovered (assertion strings, pattern scans) |
| **Ghidra WASM** | `/Gw.wasm` (via MCP) | Primary RE target — full debug symbols, all function names |
| **Ghidra EXE** | `/Gw.exe(Symbols)` (via MCP) | x86 cross-reference — stripped names but cleaner decompiler output |
| **Assertion string catalog** | `.opencode/skills/gw-bridging/SKILL.md` | Known assertion strings for bridging WASM↔EXE |

### Skills Loaded

- `gw-layer-arch` — Ghidra MCP conventions, address spaces, pitfalls
- `gw-bridging` — string-anchoring, callee comparison, three translation directions
- `gw-data-structs` — known struct patterns (TArray, frame layout, etc.)

### Context Access Path

You must know **how the context pointer is obtained at runtime**. In GWCA source, this is typically one of:

```cpp
// Pattern A: Assertion string scan (PreGameContext, GameplayContext)
address = Scanner::FindAssertion("UiPregame.cpp", "!s_scene", 0, 0x34);
PreGameContext_addr = *(uintptr_t*)address;   // → PreGameContext**
// Then: return *(PreGameContext**)PreGameContext_addr;

// Pattern B: GameContext dereference chain (WorldContext, MapContext, CharContext)
GameContext* g = GetGameContext();
return g ? g->world : nullptr;  // → GameContext + 0x2C

// Pattern C: PropGet system (WASM-only, alternative path)
// PropGet(0x0B) → WorldContext*  (see context pool)
```

For PreGameContext: `FindAssertion("UiPregame.cpp", "!s_scene", 0, 0x34)` → reads a global pointer → `*(PreGameContext**)global`.

---

## 3. Phase A: Locate the Context

### Step A1: Find the Constructor

The constructor is the single most valuable function because it **initializes every field** — giving you field count, types, and initialization values all in one place.

**WASM approach** (primary):

1. Use the GWCA assertion string to find the WASM function that references it.
   - PreGameContext: `Scanner::FindAssertion("UiPregame.cpp", "!s_scene", ...)` — the assertion string is `"!s_scene"`.
2. Search for this string in WASM:
   ```
   mcp__ghidra__search_strings("!s_scene", program="Gw.wasm")
   ```
3. Get xrefs to the string address:
   ```
   mcp__ghidra__get_xrefs_to("ram:XXXXXXXX", program="Gw.wasm")
   ```
4. Among the xref'd functions, look for functions with names like `CScene::CScene`, `CScene::Init`, or `IUi::Pregame*`.
5. Decompile each candidate and look for `MemAlloc(0x100, ...)` — the allocation size **is the struct size**.

**Result for PreGameContext**:
- Constructor: `CScene::CScene` @ `ram:80f59983`
- Allocation: `MemAlloc(0x100, ...)` in `IUi::PregameSceneProc` msg 0x09 handler
- **Struct size confirmed: 0x100 (256 bytes)**

### Step A2: Identify the FrameProc / Message Dispatcher

The FrameProc function (`IUi::PregameSceneProc` @ `ram:80f64cf6`) is the second-most-valuable function — it handles UI messages and accesses fields at runtime, giving you field semantics through message handler names.

### Step A3: String-Anchor to Bridge EXE ↔ WASM

For independent verification in Phase D, find the EXE counterparts:

1. Find a string in the WASM function (e.g., `"!s_scene"` in `PregameSceneProc`)
2. Search the **same string** in the EXE:
   ```
   mcp__ghidra__search_strings("!s_scene", program="Gw.exe(Symbols)")
   ```
3. Get xrefs to find the EXE function:
   ```
   mcp__ghidra__get_xrefs_to("0x00XXXXXXXX", program="Gw.exe(Symbols)")
   ```

**PreGameContext WASM↔EXE bridge**:

| EXE Address | WASM Symbol |
|-------------|-------------|
| `0x004ae7e0` (FrameProc) | `IUi::PregameSceneProc` @ `ram:80f64cf6` |
| `0x004ac010` (Constructor) | `CScene::CScene` @ `ram:80f59983` |
| `0x004adb00` (OnNotify) | `CScene::OnNotifyUpdateSel` @ `ram:80f617f9` |
| `0x004acdd0` (OnCreateCanceled) | `CScene::OnCreateCanceled` @ `ram:80f5a56c` |
| `0x004acf20` (OnCreateInitiated) | `CScene::OnCreateInitiated` @ `ram:80f5b8da` |

### Step A4: Check the Property Table System (Optional)

Some contexts are accessible via `PropGet(EProp)` in WASM, which provides an alternative access path. For PreGameContext, the property table wasn't needed because the assertion-string path was sufficient.

---

## 4. Phase B: Map the Constructor

### Step B1: Decompile the Constructor in WASM

```
mcp__ghidra__decompile_function("ram:80f59983", program="Gw.wasm")
```

### Step B2: Map Every `param1[N] = value` to Extract Field Count

The constructor body is a series of assignments. In WASM decompilation, these appear as:

```c
*(undefined4 *)(param1 + 0x04) = 4;     // uint32 field at offset +0x04 = 4
*(undefined4 *)(param1 + 0x0C) = 0x3f800000;  // ??? at offset +0x0C = ...
```

**Extract every assignment** into a table:

| Offset | Raw Init Value | Type Hint | Notes |
|--------|---------------|-----------|-------|
| +0x00 | `param_2` (ctor arg) | — | Not initialized to constant |
| +0x04 | `4` | uint32 | `scene_type` |
| +0x08 | `0` | uint32 | `scene_controller_iface` |
| +0x0C | `0x3f800000` | **float?** | See Step B3 |

### Step B3: Identify float vs int by Init Value Patterns

This is subtle but critical. WASM constants that represent floats need special interpretation:

| Raw Hex Value | If int32, means... | If float, means... | Verdict |
|---------------|-------------------|-------------------|---------|
| `0x3f800000` | 1065353216 | **1.0f** | Float (canonical IEEE 754 for 1.0) |
| `0x00000000` | 0 | **0.0f** | Ambiguous (both valid) |
| `0x42c80000` | 1120403456 | **100.0f** | Float (clean round number) |
| `0x428c0000` | 1116733440 | **70.0f** | Float (clean round number) |
| `0x3fa66666` | 1067869798 | **~1.3f** | Float (non-round int) |
| `0xbd1eb852` | — | **~-0.0386f** | Float (negative, non-int) |
| `0x42960000` | 1117782016 | **75.0f** | Float (clean round number) |
| `0xbdb851ec` | — | **~-0.09f** | Float (negative, non-int) |
| `0xFFFFFFFF` | -1 (int32) / 4294967295 (uint32) | **NaN** (float) | int32 (-1 sentinel) |
| `0x00000004` | 4 | tiny float | uint32 count |
| `0x00000040` | 64 | tiny float | uint32 count |

**Rule of thumb**: If the hex value decodes to a clean float (1.0, 0.0, 100.0, 70.0) but a nonsensical integer (>1M), it's a float. If it's a small integer (0, 1, 2, 4, 64) and also a trivial float, use **context from neighboring fields** to decide.

**PreGameContext example — the spring-damper groups**:

```c
// Offset +0x0C: 0x3f800000 = 1.0f → camera_pitch_frequency (float)
// Offset +0x10: 0x00000000 → zero (both 0 and 0.0f valid; but context = float)
// Offset +0x14: 0x00000000 → zero
// Offset +0x18: 0x00000000 → zero
// These form a group: frequency, current, target, velocity → all floats
```

### Step B4: Note RESERVED Blocks

If the constructor has a gap of **dozens of bytes** with no assignments, mark it as RESERVED. These are dead/unused space that may have been fields in an earlier game version but are never accessed by any current CScene method.

**PreGameContext RESERVED blocks** (76 bytes total, ~30% of struct):

| Offset Range | Bytes | Status |
|-------------|-------|--------|
| 0x1C–0x4B | 48 bytes (12 dwords) | Never initialized, never read by any CScene method |
| 0x50–0x64 | 20 bytes (5 dwords) | Initialized to 0 but never read |
| 0xC0–0xCF | 16 bytes (4 dwords) | Mixed init (some zero, some uninit), never read |

---

## 5. Phase C: Trace Runtime Access

### Step C1: Decompile the FrameProc / Message Dispatcher

The FrameProc is a switch statement on UI message IDs. Each handler reads/writes fields dynamically, revealing **which fields go together** and **what they mean**.

```
mcp__ghidra__decompile_function("ram:80f64cf6", program="Gw.wasm")
```

### Step C2: Map Each Message Handler to Offsets

For each handler in the switch statement, trace which offsets are read/written:

**PreGameContext FrameProc message handler map**:

| Msg ID | Handler | Offsets Accessed | What It Does |
|--------|---------|-----------------|-------------|
| 0x09 | Create/Init | Writes entire 0x00–0xFF region | Calls constructor, allocates struct |
| 0x10000189 | `OnNotifyUpdateSel` | Reads 0xD4 (index), reads 0xE0+0xE8 (chars array) | Character selection notification |
| 0x100000?? | `OnCreateCanceled` | Reads 0xD4, writes 0xD4=-1 and 0xD8=-1 | Cancel character creation |
| 0x100000?? | `OnCreateInitiated` | Reads 0xF0 (`create_slot_index`) | Start character creation |
| 0x08 | Render/Paint | Reads camera fields 0x0C–0xBF | Spring-damper animation update |
| 0x03 | Mouse input | Reads/writes 0x10 (camera_pitch), 0x88 (scroll_offset) | User input handling |

### Step C3: Identify Semantic Groups

Once you have offset→handler mapping, group fields by functional themes:

**PreGameContext groups discovered**:

1. **Spring-Damper Systems** (5 groups of 4 floats each = `{frequency, current, target, velocity}`):
   - 0x0C–0x1B: Camera Pitch
   - 0x68–0x83: Camera Limits (min/max pair — 8 floats)
   - 0x84–0x93: Scroll Offset
   - 0x94–0xA3: Scroll Speed
   - 0xB0–0xBF: Camera Rotation

2. **Camera Height Triple**: 0xA4/0xA8/0xAC — current computed height / model min / model max (from `GetHeightRange`)

3. **Character Selection Tail** (0xD0–0xFF):
   - 0xD0: `max_characters` (0x40 = 64)
   - 0xD4: `chosen_character_index` (PRIMARY, -1 sentinel)
   - 0xD8: `preview_character_index` (UI notification mirror, -1 sentinel)
   - 0xDC: `pending_character_index` (-1 sentinel)
   - 0xE0–0xE8: `chars_array` (data/capacity/count — 3-field TArray)
   - 0xEC: `char_creation_flag` (2)
   - 0xF0: `create_slot_index` (-1 sentinel)
   - 0xF4: `sentinel_guard` (4)
   - 0xF8: `self_link` (self-pointer)
   - 0xFC: `list_head` (linked-list head)

### Step C4: Cross-Reference Function Names for Semantic Hints

The WASM symbol names contain rich semantic information:

| Function Name | Semantic Clue |
|---------------|---------------|
| `OnNotifyUpdateSel` | "UpdateSel" → selection update → field at 0xD4 is the selected character index |
| `OnCreateInitiated` | "Create" → character creation → field at 0xF0 is the creation slot |
| `OnCreateCanceled` | "Canceled" → sets indices to -1 → sentinel pattern |
| `AdvanceCamera` | "Camera" → camera spring-damper update → all camera fields |

---

## 6. Phase D: Cross-Verify EXE

### Step D1: Decompile the EXE Counterpart Functions

WASM is the primary source, but the **EXE x86 decompiler sometimes produces cleaner output** because it doesn't have WASM's shadow-stack checks and `(int)&DAT_ram_XXXXXXXX` noise.

For each key WASM function, decompile its EXE counterpart:

```
mcp__ghidra__decompile_function("0x004ac010", program="Gw.exe(Symbols)")  // Constructor
mcp__ghidra__decompile_function("0x004ae7e0", program="Gw.exe(Symbols)")  // FrameProc
```

### Step D2: Verify Offsets Independently

The EXE decompiler uses direct byte offsets:

```c
// EXE Constructor (0x004ac010):
*(int *)(param_1 + 0xd4) = -1;    // chosen_character_index = -1 ✓
*(undefined4 *)(param_1 + 0xd8) = -1;  // preview_character_index = -1 ✓
*(undefined4 *)(param_1 + 0xdc) = 0;   // pending_character_index = 0 (EXE shows 0, WASM shows -1 — discrepancy to resolve!)
*(undefined4 *)(param_1 + 0xe0) = 0;   // chars_array.data = nullptr ✓
*(undefined4 *)(param_1 + 0xe4) = 0;   // chars_array.capacity = 0 ✓
*(undefined4 *)(param_1 + 0xe8) = 0;   // chars_array.count = 0 ✓
```

### Step D3: Resolve WASM vs EXE Discrepancies

When WASM and EXE differ, the EXE is usually correct for init values because the WASM Ghidra decompiler sometimes misinterprets constants.

Example: `pending_character_index` at 0xDC:
- WASM decompile showed `-1` (possibly a decompiler artifact)
- EXE decompile showed `0`
- Runtime analysis (OnCreateCanceled only writes to 0xD4 and 0xD8, not 0xDC) confirmed EXE → field is 0 at init

---

## 7. Phase E: Resolve Sub-Structs

### Step E1: Find Sub-Struct Accessors

Sub-structs are accessed through a **stride-based offset calculation**:

```c
// WASM OnNotifyUpdateSel:
// chars_array[chosen_character_index] → &chars_array.data + index * 0x78
iVar2 = StrCmp_wchar_t_const(
    *(int*)(param1 + 0xE0) + uVar1 * 0x78 + 0x50,  // chars[].name
    param2, 0xFFFFFFFF
);
```

The stride `0x78` (= 120 bytes) tells you the **sub-struct element size**.

### Step E2: Trace From Known Fields Outward

Start with fields you're confident about (e.g., `character_name` at +0x50) and trace outward:

1. **Find the stride**: Look for `i32.mul` with a large constant in field access expressions
2. **Identify all field accesses**: For each `+N` offset within the stride, determine:
   - Is it a read or write?
   - What type? (wchar_t write = `i32.store16`, pointer dereference = `i32.load`)
   - What function accesses it?

### Step E3: Determine Type from Access Pattern

The WASM opcode reveals the type:

| WASM Opcode | C Type | Evidence |
|-------------|--------|----------|
| `i32.store16` at +0x50 | `wchar_t` (16-bit) | Writes 2 bytes → inline wchar_t array |
| `i32.store` at +0x50 | `void*` or `uint32_t` | Would write 4 bytes → pointer or scalar |
| `i32.load` then `call` as `this` | `void*` (pointer to object) | Dereference → pointer field |
| `i32.add offset=0x50` (no load) | field offset | Used as base for sub-field access → inline struct/array |

### E4: The Pointer vs Inline Trap (Critical!)

This trap caused a 2-day false conclusion. **Do not trust Ghidra's WASM decompiler rendering alone — always check the raw WASM opcodes.**

**The trap**: Ghidra's WASM decompiler renders offset arithmetic as `(int)&DAT_ram_00000050 + ptr`, which visually resembles a pointer lookup when it's actually just adding a field offset to a base pointer.

**The resolution for LoginCharacter +0x50**:

1. **WASM decompiler showed**: `StrCmp_wchar_t_const((int)&DAT_ram_00000050 + ptr, ...)` — analyst A concluded "pointer field"
2. **WASM opcodes checked**: `i32.add` not `i32.load` — the +0x50 is pointer arithmetic, NOT a dereference → **inline array, not pointer**
3. **EXE confirmed**: `*(undefined2 *)(param_1[0x38] + 0x50 + param_1[0x35] * 0x78) = 0` — 16-bit write (= wchar_t), not 32-bit
4. **Python/C++ were correct** all along: `wchar_t character_name[20]` (40 bytes inline)

**The rule**: If accessing `struct + N` requires ONE memory load (to get the base pointer), the field at `+N` is inline. If it requires TWO loads (one for the pointer, one to dereference it), the field is a pointer.

---

## 8. Phase F: Consensus & Implement

### Step F1: Cross-Reference All Analysts' Findings

Create a master offset table comparing findings from all sources:

| Offset | WASM Analyst | EXE Analyst | GWCA C++ | Python | **CONSENSUS** |
|--------|-------------|------------|----------|--------|---------------|
| 0xD4 | `chosen_character_index` = -1 | Same | `Unk08` (-1 sentinel noted) | `chosen_character_index` (offset correct!) | **chosen_character_index (int32, -1)** |
| 0xD8 | secondary index | Same | `chosen_character_index` (WRONG!) | `Unk08` | **preview_character_index (int32, -1)** |
| 0xDC | unknown | `pending_character_index` = 0 | `pad_0xDC` | (inside chars_array — WRONG!) | **pending_character_index (int32, 0)** |
| 0xE0 | `chars` data pointer | Same | `chars` starts | (offset 0xDC — WRONG!) | **chars data pointer (void*)** |

### Step F2: Resolve Conflicts

Decision rules:
- **WASM + EXE agree** → high confidence, implement
- **WASM + EXE disagree** → resolve via WASM opcodes (ground truth)
- **Single-source finding** → mark with ⚠️, implement cautiously
- **No source has data** → mark as RESERVED, keep as dead space

### Step F3: Update Both Python and C++

**Python ctypes** (`PreGameContext.py`):

```python
class PreGameContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("frame_id", c_uint32),
        ("scene_type", c_uint32),
        # ... all fields with exact offsets and types ...
        ("list_head", c_uint32),
    ]

# CRITICAL: Add size assertion
assert sizeof(PreGameContextStruct) == 0x100, \
    f"PreGameContextStruct size mismatch: {sizeof(PreGameContextStruct)} != 0x100"
```

**C++ GWCA** (`PreGameContext.h`):
```cpp
struct PreGameContext {
    // ... all fields with inline offset comments ...
};
static_assert(sizeof(PreGameContext) == 0x100, "PreGameContext size must be 0x100");
```

### Step F4: Size Assertions (MANDATORY)

Every struct definition **must** include a size assertion verified against the WASM `MemAlloc` call:

```python
assert sizeof(LoginCharacter) == 0x78
assert sizeof(PreGameContextStruct) == 0x100
```

This catches misalignment, missing padding, and type-size bugs immediately.

### Step F5: Handle TArray Compatibility

The game uses a **3-field TArray** (`data`, `capacity`, `count` = 0x0C bytes). GWCA's `GW::Array<T>` is **4-field** (`data`, `capacity`, `count`, `m_param` = 0x10 bytes). This mismatch will silently corrupt adjacent fields.

**Solution used for PreGameContext**:
- In C++: Use raw fields (`chars_buffer`, `chars_capacity`, `chars_count`) instead of `GW::Array<LoginCharacter> chars`
- In Python: Use `GW_BaseArray` (0x0C = 3 fields) instead of `GW_Array` (0x10 = 4 fields)

### Step F6: Check Caller Compatibility

Verify all existing callers still work:
- Python: Check `cast(ptr, POINTER(Struct)).contents` paths
- C++: Check all `pgc->field` access patterns, especially for renamed/moved fields
- Build and test

---

## 9. Common Pitfalls

### Pitfall 1: WASM `(int)&DAT_ram_XXXXXXXX` Patterns Are Offsets, Not Addresses

```c
// Ghidra WASM decompiler output:
*(undefined4 *)((int)&DAT_ram_0000084c + iVar1);
// This means: WorldContextPtr + 0x84C — NOT dereferencing address 0x84C!
```

The `DAT_ram_XXXXXXXX` where `XXXXXXXX` is a small value is Ghidra's way of rendering a constant offset in a context with many address spaces. Always interpret `(int)&DAT_ram_00000XXX` as `+offset 0xXXX`, not a pointer to address 0xXXX.

### Pitfall 2: Pointer Arithmetic vs Dereference

```wat
;; This is pointer arithmetic (i32.add), NOT a load:
i32.add offset=0x50   ;; → compute &struct.field

;; This IS a dereference (i32.load):
i32.load offset=0x50  ;; → read value from struct.field
```

**Always check the raw WASM opcodes** when Ghidra decompiler output is ambiguous. Use `mcp__ghidra__disassemble_function` to see the raw instructions.

### Pitfall 3: Ghidra WASM Decompiler Noise

The WASM decompiler injects shadow-stack checks, Emscripten runtime calls, and global variable accesses that don't exist in the original source. Ignore:
- `__wasm_stack_*` calls
- `__emscripten_*` runtime calls  
- `GLOBAL_BASE` / `STACKTOP` references
- `unknown_*` temporaries from Wasm-to-C decompilation artifacts

Focus on the actual field accesses (`*(type *)(param1 + offset)`).

### Pitfall 4: GW_Array (4-field) vs GW_BaseArray (3-field)

See Phase F Step F5. The game's internal TArray is 0x0C bytes (3 dwords). GWCA adds a 4th field. When replacing a GW_Array with GW_BaseArray, verify that adjacent fields' offsets are correct — the 4th field of GW_Array silently overlaps with whatever follows in the struct.

### Pitfall 5: Single-Source vs Multi-Source Confidence

| Evidence Sources | Confidence | Action |
|-----------------|-----------|--------|
| WASM constructor + EXE constructor + runtime access | **High** | Implement directly |
| WASM runtime access + EXE runtime access | **High** | Implement directly |
| Only WASM constructor | **Medium** | Implement, mark as provisional |
| Only EXE constructor | **Medium** | Implement, mark as provisional |
| Only WASM decompiler (no raw opcodes checked) | **Low** | Verify with opcodes first |
| Field appears once, never read/written by any known method | **Dead space** | Mark as RESERVED |

### Pitfall 6: init-value Discrepancies

The constructor init value might not match runtime behavior. Example: `pending_character_index` at 0xDC — WASM decompile showed `-1` but EXE showed `0`. Resolution: EXE was correct (runtime handlers only write to 0xD4 and 0xD8, not 0xDC).

### Pitfall 7: INIT vs 0 vs -1 Sentinels

Some init values carry semantic meaning:

| Init Value | Typical Meaning |
|-----------|----------------|
| 0 | Empty/null/default |
| -1 (0xFFFFFFFF) | "none selected" / "invalid" / sentinel |
| 4 | Count/hardcoded constant |
| 0x40 (64) | Max capacity |
| 1.0f (0x3f800000) | Multiplicative identity / frequency default |

---

## 10. Tools Reference

### Key Ghidra MCP Tools

| Operation | Tool | Notes |
|-----------|------|-------|
| Find string in binary | `mcp__ghidra__search_strings` | Bridge step. Search assertion strings. |
| Get xrefs to address | `mcp__ghidra__get_xrefs_to` | Bridge step. Find functions referencing a string. |
| Decompile function | `mcp__ghidra__decompile_function` | Primary analysis. Always pass `program=` |
| Disassemble function | `mcp__ghidra__disassemble_function` | Raw opcode verification. Use when decompiler output is ambiguous. |
| Search functions by name | `mcp__ghidra__search_functions` | Find WASM functions by semantic name (e.g., `"*Pregame*"`) |
| Get function callers/callees | `mcp__ghidra__get_function_callers` / `get_function_callees` | Understand who touches a field |
| Analyze function complete | `mcp__ghidra__analyze_function_complete` | Full analysis with xrefs, callees, variables |
| Force decompile | `mcp__ghidra__force_decompile` | Bypass stale decompiler cache |
| Cross-binary fuzzy match | `mcp__ghidra__find_similar_functions_fuzzy` | ⚠️ Unreliable. Prefer string-anchoring. |
| Get struct layout | `mcp__ghidra__get_struct_layout` | Check existing Ghidra struct definitions |
| Analyze struct field usage | `mcp__ghidra__analyze_struct_field_usage` | Find all functions accessing a known offset |

### Key Constant Patterns

| Pattern | Meaning |
|---------|---------|
| `0x3f800000` | `1.0f` (float) |
| `0xFFFFFFFF` | `-1` (int32 sentinel) |
| `0x00000040` | `64` (typical capacity constant) |
| `0x00000078` | `120` (typical sub-struct stride) |
| `i32.mul` with large constant | Array stride calculation |
| `i32.store16` | 16-bit write (wchar_t, not pointer) |
| `i32.store` | 32-bit write (pointer or uint32) |

### Workflow Checklist

```
☐ Phase A1: Find constructor → get struct size from MemAlloc
☐ Phase A2: Identify FrameProc → get message handler list
☐ Phase A3: String-anchor WASM↔EXE for all key functions
☐ Phase B1-B2: Map every constructor assignment
☐ Phase B3: Classify float vs int by init value patterns
☐ Phase B4: Note gaps → RESERVED blocks
☐ Phase C1-C2: Map each message handler to offsets accessed
☐ Phase C3: Group fields into semantic clusters
☐ Phase C4: Extract semantic hints from function names
☐ Phase D1: Decompile EXE counterparts independently
☐ Phase D2: Verify all offsets independently
☐ Phase D3: Resolve WASM vs EXE discrepancies
☐ Phase E1-E3: Resolve sub-structs (stride, type, inline vs pointer)
☐ Phase F1-F2: Cross-reference, resolve conflicts
☐ Phase F3: Update Python ctypes + C++ header
☐ Phase F4: Add size assertions
☐ Phase F5: TArray compatibility check
☐ Phase F6: Caller compatibility, build, test
```

---

## Appendix: PreGameContext Resolution Summary

### Source References

| Artifact | Path |
|----------|------|
| Python struct (final) | `Py4GWCoreLib\native_src\context\PreGameContext.py` |
| C++ header (final) | `Py4GW\vendor\gwca\Include\GWCA\Context\PreGameContext.h` |
| GWCA access pattern | `Py4GW\vendor\gwca\Source\GWCA.cpp:131-133` |
| WASM constructor | `CScene::CScene` @ `ram:80f59983` |
| WASM FrameProc | `IUi::PregameSceneProc` @ `ram:80f64cf6` |
| EXE constructor | `0x004ac010` |
| EXE FrameProc | `0x004ae7e0` |
| Assertion anchor | `"!s_scene"` in `UiPregame.cpp` |

### Key Numbers

| Item | Value |
|------|-------|
| Struct size | 0x100 (256 bytes) |
| LoginCharacter stride | 0x78 (120 bytes) |
| Max characters | 0x40 (64) |
| RESERVED bytes | 76 bytes (30% dead space) |
| Spring-damper groups | 5 groups (pitch, limits, scroll_offset, scroll_speed, rotation) |
| Camera height triple | current / min / max (3 floats at 0xA4–0xAC) |
| Rounds of analysis | 6 (from initial discovery to full resolution) |

### Key Lesson

The two hardest parts of struct identification are **(1) distinguishing floats from ints** (use IEEE 754 decode to check for clean float values) and **(2) distinguishing inline arrays from pointers** (check WASM opcodes — `i32.add` vs `i32.load`). The Ghidra WASM decompiler is a powerful tool but **its rendering is not trustworthy** for type inference. Always verify against raw opcodes or against the EXE decompiler (which produces cleaner x86 output).
