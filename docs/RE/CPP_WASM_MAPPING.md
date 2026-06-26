# CPP ↔ WASM ↔ EXE Mapping Guide

A manual translation procedure for Guild Wars reverse-engineering.
Lets you locate a function in any of three sources (Py4GW/GWCA cpp source,
the WASM build with symbols, the EXE build that's stripped) and bridge between them.

---

## Why this guide exists

Three sources, none complete on its own:

| Layer | Has names? | Stable across builds? | How addresses are referenced |
|---|---|---|---|
| **WASM** (`Gw.wasm`) | yes — full debug symbols (`CharCliPlayerOrderAlertSimple`) | drifts slowly | `ram:80c4bada` |
| **EXE** (`*.exe`) | no — stripped except MSVC CRT (`FUN_xxxxxxxx`) | rebuilt every patch | absolute `0x00917740` |
| **CPP** (`vendor/gwca/Source/`) | yes — semantic names (`CallTarget_Func`) | stable | runtime-resolved pointers |

The translation problem: GWCA's CPP code wants to call/hook functions in the EXE, but the EXE has no names. The WASM has the names but isn't what's actually running. We need to bridge.

---

## The core insight: string literals are the bridge

C++ source code contains string literals (`assert(...)` text, `LogMsg` format strings, file paths). The MSVC compiler bakes them into `.rdata` of the EXE; Emscripten bakes the **same bytes** into the WASM. They survive identically because they come from the same source tree.

GWCA already uses this technique via `Scanner::FindAssertion(file, expression, ...)`. The same approach lets you walk from any of the three sources to either of the other two.

---

## Manual translation procedure

You need a Ghidra instance with both binaries loaded (see `mcp__ghidra__list_open_programs`).

### Direction A — CPP name → EXE address

You know a GWCA function pointer (e.g. `CallTarget_Func`) and want its address in this EXE.

1. Open `vendor/gwca/Source/*Mgr.cpp` and find the assignment.
2. Look at the `Scanner::Find*` call:
   - **`FindAssertion(file, expr, line, offset)`** — search `expr` as a string in the EXE (`mcp__ghidra__search_strings`), take its xref (`mcp__ghidra__get_xrefs_to`), apply `Scanner::ToFunctionStart` semantically (the xref already points inside the enclosing function — the listed `FUN_xxxxxxxx` is the answer).
   - **`Scanner::Find(pattern, mask, offset)`** — search the bytes in the EXE (`mcp__ghidra__search_byte_patterns`), apply the `offset`, then:
     - `FunctionFromNearCall(addr)` → decode the `CALL` instruction at `addr` to get its target.
     - `ToFunctionStart(addr)` → walk back from `addr` to the enclosing function entry.
     - `*(uintptr_t*)addr` → read 4 bytes at `addr` as a literal pointer (used for global data refs).

### Direction B — WASM symbol → EXE address

You know an Anet symbol from WASM (e.g. `CharCliPlayerOrderAlertSimple`) and want its EXE twin.

1. Find a string literal that the WASM function references — typically an assertion message or a `LogMsg` format string. Look inside the decompile, or list strings near the function. If the function has no strings, find a CALLER that does.
2. Search the same string in the EXE.
3. Take the xref — that's the EXE function.

### Direction C — EXE address → WASM symbol

You have an unnamed `FUN_xxxxxxxx` and want to know what it is.

1. Find a string the EXE function references (look at its decompile).
2. Search that string in the WASM.
3. Take the xref — the WASM symbol that owns it is the identity.

---

## Worked examples (AgentMgr.cpp)

Each entry shows the full triangle: cpp name, wasm symbol, exe address, and the exact technique used.

### 1. `ChangeTarget_Func`

| | |
|---|---|
| **CPP** | `AgentMgr.cpp:162` |
| **Typedef** | `void(*)(uint32_t agent_id)` |
| **WASM symbol** | `IAgentView::SetSelections(unsigned long, unsigned long)` |
| **EXE address** | `0x007e0f60` |
| **Technique** | Assertion string |

GWCA does:
```cpp
ChangeTarget_Func = (ChangeTarget_pt)Scanner::ToFunctionStart(
    Scanner::FindAssertion("AvSelect.cpp", "!(autoAgentId && !ManagerFindAgent(autoAgentId))", 0, 0));
```

Manual procedure:
- Search `"!(autoAgentId && !ManagerFindAgent(autoAgentId))"` in WASM → at `ram:0012a382`
- Get xref in WASM → `From ram:80a5f7e1 in IAgentView::SetSelections(...)`
- Search the same string in EXE → at `0x00a885ac`
- Get xref in EXE → `From 0x007e0fbb in FUN_007e0f60`
- Result: `FUN_007e0f60` = `IAgentView::SetSelections` = GWCA's `ChangeTarget_Func`

### 2. `DoWorldActon_Func`

| | |
|---|---|
| **CPP** | `AgentMgr.cpp:183` |
| **Typedef** | `void(*)(WorldActionId action, uint32_t agent_id, bool suppress_call_target)` |
| **WASM symbol** | `IUi::Game::CoreActionExecuteWorldAction(EWorldAction, unsigned long, int)` |
| **EXE address** | `0x00513670` |
| **Technique** | Assertion string |

```cpp
DoWorldActon_Func = (DoWorldActon_pt)Scanner::ToFunctionStart(
    Scanner::FindAssertion("GmCoreAction.cpp", "action < WORLD_ACTIONS", 0, 0));
// "This hits twice, but we want the first function"
```

Manual procedure:
- Search `"action < WORLD_ACTIONS"` in EXE — two xrefs (`FUN_00513670` and `FUN_005138c0`); take the first.

### 3. `CallTarget_Func` (newly added)

| | |
|---|---|
| **CPP** | `AgentMgr.cpp:193` |
| **Typedef** | `void(*)(CallTargetType type, uint32_t agent_id)` |
| **WASM symbol** | `CharCliPlayerOrderAlertSimple(ECharSimpleAlert, unsigned long)` |
| **EXE address** | `0x00917740` (thunk at `0x008102d0`) |
| **Technique** | Byte pattern (network opcode + packet size) |

```cpp
address = Scanner::Find("\x6A\x0C\xC7\x45\xF0\x23\x00\x00\x00", "xxxxxxxxx", 0);
CallTarget_Func = (CallTarget_pt)Scanner::ToFunctionStart(address);
```

How we found it:
- WASM showed `CharMsgSendOrderAlertSimple` packs `{0x23, type, agent_id}` (12 bytes) and sends it.
- Searched EXE for the literal opcode `0x23` and size `0xC` inside the assembly:
  - `PUSH 0xC` → `6A 0C`
  - `MOV [EBP-0x10], 0x23` → `C7 45 F0 23 00 00 00`
- Unique match in EXE at `0x00917760`; `ToFunctionStart` → `0x00917740`.
- Verified by matching network opcode + packet layout with WASM bit-for-bit.

### 4. `MoveTo_Func` — caveat: pattern resolves, typedef mismatches

| | |
|---|---|
| **CPP** | `AgentMgr.cpp:181` |
| **Typedef** | `void(*)(float* pos)` |
| **EXE address** | `0x00534fa0` (resolves cleanly) |
| **WASM symbol** | likely `IUi::Game::Walk*` (NOT `CharCliPlayerOrderMovePos`) |
| **Technique** | Byte pattern at `-0x5` then `FunctionFromNearCall` |

The function body at `0x00534fa0`:

```asm
PUSH EBP; MOV EBP, ESP
CMP [0x00bfeacc], 0; JZ ret
OR  [0x00bfea64], 2
FLDZ; PUSH ECX; FSTP [ESP]      ; pass 0.0f
MOV [0x00bfea70], 0
CALL 0x00533b30                  ; WalkAdvance(0.0)
ADD ESP, 4
JMP 0x00533a00                   ; tail call
POP EBP; RET
```

This function **does not consume its `float*` argument** — it sets state globals and tail-calls. GWCA's typedef claims `void(float*)` but the resolved function ignores the pointer. `Player.Move(x, y)` likely works because the actual position is set via a different path (the global `DAT_*` writes you see in `IUi::Game::WalkToPoint` come from a different caller chain).

**Lesson**: when a byte pattern resolves but the function body doesn't match the typedef, the pattern has rotted. Verify behaviorally before trusting.

### 5. `SendAgentDialog_Func` / `SendGadgetDialog_Func`

| | |
|---|---|
| **CPP** | `AgentMgr.cpp:176-177` |
| **EXE addresses** | `0x008105b0` and `0x00810e00` (both likely thunks) |
| **Technique** | Byte pattern + `FunctionFromNearCall` at fixed offsets |

```cpp
address = Scanner::Find("\x89\x4b\x24\x8b\x4b\x28\x83\xe9\x00", "xxxxxxxxx");
SendAgentDialog_Func  = (SendDialog_pt)Scanner::FunctionFromNearCall(address + 0x15);
SendGadgetDialog_Func = (SendDialog_pt)Scanner::FunctionFromNearCall(address + 0x25);
```

Pattern hits at `0x00509ba4`. At `+0x15` → `0x00509bb9` = `CALL 0x008105b0`. At `+0x25` → `0x00509bc9` = `CALL 0x00810e00`. The targets are likely JMP thunks (like CallTarget's `0x008102d0` → `0x00917740`); when hooking, find and use the real body.

### 6. `AgentArrayPtr` (data, not function)

| | |
|---|---|
| **CPP** | `AgentMgr.cpp:164` |
| **EXE pointer holder** | `0x007fcfb9` |
| **EXE array base** | `0x00bf05c4` (`*(uintptr_t*)0x007fcfb9`) |
| **Technique** | Byte pattern of array-indexing code |

```cpp
address = Scanner::Find("\x8b\x0c\x90\x85\xc9\x74\x19", "xxxxxxx", -0x4);
if (address && Scanner::IsValidPtr(*(uintptr_t*)address))
    AgentArrayPtr = *(uintptr_t*)address;
```

Pattern `8B 0C 90 85 C9 74 19` = `MOV ECX, [EAX+EDX*4]; TEST ECX,ECX; JZ ...` (canonical array-of-pointers indexing). Offset `-0x4` walks back to the immediate operand of the preceding `MOV EAX, [imm32]` instruction. Reading the 4 bytes there gives `0x00bf05c4` — the agent array base global.

### 7. `PlayerAgentIdPtr` (data)

| | |
|---|---|
| **CPP** | `AgentMgr.cpp:169` |
| **EXE pointer holder** | `0x004f5d5c` |
| **EXE pointer value** | `0x00bfe7c0` |
| **Technique** | Byte pattern straddling end-of-function + start-of-function |

```cpp
address = Scanner::Find("\x5d\xe9\x00\x00\x00\x00\x55\x8b\xec\x56\x57\x8b\x7d", "xx????xxxxxxx", -0xE);
```

Pattern is `POP EBP; JMP rel32; PUSH EBP; MOV EBP, ESP; PUSH ESI; PUSH EDI; MOV EDI, [EBP+8]` — the byte boundary between two adjacent functions, where the second function starts with a specific prologue. `-0xE` walks back into the previous function to a `MOV [imm32], EAX` instruction whose immediate is the global pointer.

### 8. WASM → EXE demo: `CharClient::CHeroMgr::OnCommandMoveToPoint`

| | |
|---|---|
| **WASM symbol** | `CharClient::CHeroMgr::OnCommandMoveToPoint(u32, MapPoint const&)` |
| **WASM address** | `ram:80be4d79` |
| **EXE address** | `FUN_00817cf0` |
| **Technique** | `LogMsg` format string anchor |

Inside the WASM function, `LogMsg` is called with the literal:

```
"CommandMoveToPoint (agent %d, point %f, %f): Hero not activated"
```

This exact string exists in both binaries:

- WASM at `ram:00114398`, xref `ram:80be509d` inside `CharClient::CHeroMgr::OnCommandMoveToPoint`
- EXE at `0x00a8c1d8`, xref `0x00817d1d` inside `FUN_00817cf0`

The EXE decompile confirms the signature and structure (signature shape matches, callees match modulo one inlining: EXE keeps `GetHero` as a separate `FUN_008175c0` callee; WASM/Emscripten inlined it). This is a perfect example of: **strings are stable; structure isn't always 1:1; signature + behavior + string anchor together give high confidence.**

---

## Pitfalls

### Patterns rot, strings don't

The `MoveTo_Func` case above is the canonical illustration. GWCA's byte pattern still uniquely matches in this build, but the function it lands on no longer has the float* signature the typedef claims. Always sanity-check behaviorally.

### Thunks vs bodies

The MSVC build emits JMP thunks. `CallTarget_Func`'s thunk at `0x008102d0` is just `JMP 0x00917740`. **Hook the body, not the thunk** — hooking the thunk only catches calls that go through the thunk, not direct internal calls.

### Inlining differs between toolchains

Emscripten and MSVC make different inlining decisions from the same source. Expect ±1 callee differences when comparing call graphs across the two binaries.

### Address spaces

- **WASM**: code at `ram:8XXXXXXX` (high), strings/data at `ram:00XXXXXX` (low)
- **EXE**: image-base `0x00400000`; code typically `0x00400000–0x00B00000`; `.rdata` strings `0x00A00000+`; mutable globals `0x00B00000+` (`0x00BFXXXX` is the common range)

### Pattern uniqueness

Always confirm a `Scanner::Find` pattern has exactly **one** match before trusting it. Use `mcp__ghidra__search_byte_patterns` with `limit: 10` and check the count.

---

## Quick reference — AgentMgr (this EXE build)

| GWCA name | EXE addr | WASM symbol | Technique |
|---|---|---|---|
| `ChangeTarget_Func` | `0x007e0f60` | `IAgentView::SetSelections` | assertion |
| `DoWorldActon_Func` | `0x00513670` | `IUi::Game::CoreActionExecuteWorldAction` | assertion |
| `CallTarget_Func` | `0x00917740` | `CharCliPlayerOrderAlertSimple` | byte pattern (opcode 0x23) |
| `MoveTo_Func` (caveat) | `0x00534fa0` | likely `IUi::Game::Walk*` (typedef mismatch) | byte pattern |
| `SendAgentDialog_Func` | `0x008105b0` | (TBD; thunk) | byte pattern + near-call |
| `SendGadgetDialog_Func` | `0x00810e00` | (TBD; thunk) | byte pattern + near-call |
| `AgentArrayPtr` (data) | `0x00bf05c4` | agent array base | data pointer scan |
| `PlayerAgentIdPtr` (data) | `0x00bfe7c0` | player agent id | data pointer scan |

---

## UI Control FrameProc Mappings (2026-06-05)

After the UI Elements Universe Discovery project, 11 FrameProc addresses are confirmed via string-anchoring. All addresses valid for EXE build **05-30-2026**.

| Control | WASM FrameProc | WASM Addr | EXE Address | Assertion |
|---------|---------------|-----------|-------------|-----------|
| DropdownFrame | `CtlDropListProc` | `ram:80e3c9a3` | `0x0087f5f0` | `"!FrameGetChild(thisFrame, CTL_LIST_ENTRIES)"` |
| SliderFrame (base) | `CtlSliderProc` | `ram:80fcc337` | `0x00615fe0` | `"value >= m_range.min"` |
| SliderFrame (wrapper) | `IUi::UiCtlSliderProc` | `ram:80fcd65d` | `0x0087f440` | byte pattern: `\x55\x8B\xEC\x83\xEC\x18\x53\x8B\x5D\x08\x56\x57\x8B\x43\x04\x48\x83\xF8\x58` |
| EditableTextFrame | `CtlEditProc` | `ram:80dee7ef` | `0x00888aa0` | `"!s_editCaretMaterial"` |
| ProgressBar | `CtlProgressProc` | `ram:80f6ce9a` | `0x008812e0` | `"!sm_rateArrowImageList"` |
| TabsFrame | `CtlPageProc` | `ram:80e078f3` | `0x0061a950` | `"!IsBtnCode(pageCode)"` |
| MultiLineTextLabel | `CtlTextMlProc` | `ram:80da0629` | `0x00610c40` | `"FrameTestStyles(hdr.frameId, CTLTEXT_STYLE_MODEL)"` |
| GroupHeader | `IUi::CGroupHeaderFrame::FrameProc` | `ram:81192c89` | `0x0087ddc0` | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlGroupHeader.cpp"` |
| TextShy | `IUi::TextShy::CTextShyFrame::FrameProc` | `ram:8149a9a7` | `0x0087f0d0` | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlTextShy.cpp"` |
| Bullet | `IUi::UiCtlBulletProc` | `ram:8134512b` | `0x00884f20` | `"!s_bulletImageList"` |
| BtnExpand | `IUi::UiCtlBtnExpandProc` | `ram:80e7b6f7` | `0x008867f0` | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlBtnExpand.cpp"` |
| BtnToggle | `IUi::UiCtlBtnToggleProc` | `ram:816b67fd` | `0x00886370` | (path assertion) |

**Procedure used**: For each control, the WASM FrameProc was identified by searching WASM for the source file path string (e.g., `"UiCtlDropMenu.cpp"`), then the same string was searched in the EXE and its xref identified the EXE function. Standard Direction B (WASM symbol → EXE address) procedure.

**CRITICAL**: Tier 2 controls (Dropdown, Slider, EditableText, ProgressBar, Tabs, MultiLineTextLabel, GroupHeader) had Phase 3 Create functions implemented but ALL crashed the client. The address mappings are verified correct — the C++ implementation needs rework. DO NOT reuse the Phase 3 C++ code as-is. Full catalog at `docs/RE/ui_controls_catalog.md`.

---

## Cheat sheet: Ghidra MCP tools used in this procedure

| Step | Tool |
|---|---|
| Find a string in either binary | `mcp__ghidra__search_strings` |
| Find a byte pattern in EXE | `mcp__ghidra__search_byte_patterns` |
| Get xrefs to a string/address | `mcp__ghidra__get_xrefs_to` |
| Decompile a function | `mcp__ghidra__decompile_function` (use `address`) |
| Disassemble raw bytes | `mcp__ghidra__disassemble_bytes` |
| List callees / callers | `mcp__ghidra__get_function_callees` / `get_function_callers` |
| Search functions by name | `mcp__ghidra__search_functions` |

For a new function: typically two or three of these is enough.
