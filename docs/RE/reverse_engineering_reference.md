# Reverse Engineering Reference

Comprehensive library reference for the Python-C++-Ghidra interface in the Py4GW project.
Read this first before any RE work. `AGENTS.md` points here for tool paths and mappings.

## How To Use This File

1. Read Sections 1-4 first for architecture, bridging, key function maps, and UI message dispatch.
2. Use Section 13 as the local RE document map.
3. Jump to subsystem-specific documents once you know the problem area.

---

## 1. Three-Layer Architecture

| Layer | Location | Purpose | Interface |
|-------|----------|---------|-----------|
| **C++/GWCA** | `Py4GW\vendor\gwca\` | Original GWCA source, function discovery patterns | `Scanner::Find*`, hooks, structs |
| **Python/Native** | `Py4GWCoreLib\native_src\` | Python port of GWCA primitives | `NativeFunction`, `PlayerMethods`, `Scanner` |
| **Ghidra** | MCP bridge (2 programs loaded) | Static analysis of Gw.exe + Gw.wasm | `mcp__ghidra__*` tools over MCP |

### C++/GWCA Source Layout

```text
Py4GW\vendor\gwca\
|-- Source\               # Implementation files
|   |-- AgentMgr.cpp      # InteractAgent, MoveTo, ChangeTarget, CallTarget
|   |-- PlayerMgr.cpp     # Player operations
|   |-- UIMgr.cpp         # UI message dispatch
|   |-- ItemMgr.cpp       # Inventory/items
|   |-- GameThreadMgr.cpp # Enqueue/execution loop
|   `-- ...
|-- Include\GWCA\
|   |-- Managers\         # Public API headers
|   |   |-- AgentMgr.h    # WorldActionId, CallTargetType, Agent APIs
|   |   `-- ...
|   |-- GameEntities\     # Struct definitions (Agent, NPC, Item, etc.)
|   |-- Constants\        # Enums (Allegiance, etc.)
|   `-- Utilities\
|       `-- Scanner.h     # Find, FindAssertion, ToFunctionStart, FunctionFromNearCall
```

### Python/Native Source Layout

```text
Py4GWCoreLib\
|-- native_src\
|   |-- methods\
|   |   |-- PlayerMethods.py   # InteractAgent, Move, ChangeTarget, SendChat
|   |   |-- MapMethods.py      # Travel, logout
|   |   `-- DatFileMethods.py  # Character data
|   |-- internals\
|   |   |-- native_function.py # NativeFunction class (byte-pattern -> callable)
|   |   |-- prototypes.py      # Function signatures (Void_U32, etc.)
|   |   |-- native_symbol.py   # Symbol resolution helpers
|   |   `-- native_caller.py   # Dynamic call infrastructure
|   |-- context\               # Native context struct accessors
|   `-- __init__.py
|-- Scanner.py                 # Python-facing Scanner (FindAssertion, FindInRange)
|-- Player.py                  # High-level Player wrapper
|-- Agent.py                   # Agent wrapper
|-- UIManager.py               # SendUIMessage, SendUIMessageRaw
`-- enums_src\UI_enums.py      # UIMessage, WorldActionId equivalents
```

### Ghidra Setup

Two programs permanently loaded via MCP bridge:

| Program | Path | Language | Base | Functions |
|---------|------|----------|------|-----------|
| **Gw.exe** (current) | `/Gw.exe(Symbols)` | x86:LE:32 | `0x00400000` | 18,017 |
| **Gw.wasm** | `/Gw.wasm` | Wasm:LE:32 | `ram:80000000` | 18,004 |

- EXE has NO debug symbols except MSVC CRT — functions are `FUN_xxxxxxxx`
- WASM has FULL debug symbols — functions have semantic names like `CharCliPlayerOrderAlertSimple`
- Address spaces: EXE uses flat image-base addressing (`0x00513670`); WASM uses `ram:` prefix (`ram:80c4bada`)

Switch programs with: `mcp__ghidra__switch_program` (all Ghidra tools accept `program` parameter)

---

## 2. Bridging Techniques

The core technique is **string anchoring**: C++ assert/LogMsg string literals survive identically in EXE and WASM because they come from the same source tree.

### CPP -> EXE (finding a GWCA function in the stripped EXE)

```
GWCA: Scanner::FindAssertion("GmCoreAction.cpp", "action < WORLD_ACTIONS", 0, 0)
       -> Scanner::ToFunctionStart(address)
       -> EXE: FUN_0050e5e0
```

Manual: search string -> get xref -> walk to function start.

### WASM -> EXE

Find a string in the WASM function -> search same string in EXE -> xref -> function.

Example: `"CommandMoveToPoint (agent %d, point %f, %f): Hero not activated"` in `CharClient::CHeroMgr::OnCommandMoveToPoint` -> EXE `FUN_00817cf0`.

### EXE → WASM

Find string in EXE function → search in WASM → xref → named WASM function.

### Byte Pattern Scanning

When no string exists, use opcode byte patterns:
```python
pattern = b"\x6A\x0C\xC7\x45\xF0\x23\x00\x00\x00"  # push 0xC; mov [ebp-0x10], 0x23
mask    = "xxxxxxxxx"
```

Always verify pattern has exactly ONE match.

Full procedure in: `docs/RE/CPP_WASM_MAPPING.md`

---

## 3. Key Function Catalog

### Agent / Interaction Functions

| GWCA/CPP Name | WASM Symbol | EXE Address | Technique |
|---------------|-------------|-------------|-----------|
| `DoWorldActon_Func` | `IUi::Game::CoreActionExecuteWorldAction(EWorldAction, uint, int)` | `0x0050e5e0` | assertion `"action < WORLD_ACTIONS"` |
| `CallTarget_Func` | `CharCliPlayerOrderAlertSimple(ECharSimpleAlert, uint)` | `0x00917740` (thunk `0x008102d0`) | byte pattern (opcode 0x23) |
| `ChangeTarget_Func` | `IAgentView::SetSelections(uint, uint)` | `0x007e0f60` | assertion `"!(autoAgentId && !ManagerFindAgent(autoAgentId))"` |
| `MoveTo_Func` | `IUi::Game::Walk*` (typedef mismatch) | `0x00534fa0` | byte pattern `\x83\xc4\x0c\x85\xff\x74\x0b\x56\x6a\x03` |
| `SendAgentDialog_Func` | (thunk) | `0x008105b0` | byte pattern + near-call at `+0x15` |
| `SendGadgetDialog_Func` | (thunk) | `0x00810e00` | byte pattern + near-call at `+0x25` |

### Interaction Sub-Functions (WASM names)

| WASM Symbol | Address | Role |
|-------------|---------|------|
| `CharCliPlayerOrderInteract(uint, int)` | `ram:80c4d1f3` | Client-side interact handler (RemoveClientControl + send packet) |
| `CharMsgSendOrderInteract(uint, int)` | `ram:80a157d2` | Network packet sender (opcode 0x39, 12 bytes) |
| `CharCliPlayerOrderAttack(uint, int)` | EXE `0x007ed5f0` | Attack order + RemoveClientControl + send |
| `CharCliPlayerOrderPickup(uint, int)` | EXE `0x007ed860` | Pickup order |
| `CharCliPlayerOrderUse(uint, int)` | EXE `0x007ee070` | Use item order |
| `CharCliPlayerOrderFollow(uint)` | EXE `0x007ed760` | Follow order |
| `IUi::Game::ExecuteDefaultWorldAction(uint, int, uint)` | `ram:815e996e` | Official interaction dispatch (what UI uses) |
| `IUi::Game::GetDefaultWorldAction(uint, int, uint)` | `ram:815f3fc8` | Action decision logic (sanitization) |
| `IUi::Game::CoreActionGetDefaultWorldAction(uint)` | `ram:8125ff0a` | Simple agent-type-to-action mapping |

### Agent Data

| GWCA Name | WASM/Emscripten Name | EXE Address | Technique |
|-----------|---------------------|-------------|-----------|
| `AgentArrayPtr` | agent array base | `0x00bf05c4` | data pointer scan (array-indexing pattern) |
| `PlayerAgentIdPtr` | player agent id | `0x00bfe7c0` | byte pattern between adjacent functions |

### Data Functions Used Internally

| EXE Address | Guess Name | Role |
|-------------|------------|------|
| `0x007b8ba0` | `AvValidate` | Validate agent exists in manager |
| `0x007b84e0` | `AvGetType` | Get agent type (0xdb=dead, 0x200=gadget, 0x400=item) |
| `0x007b6fe0` | `AvCharGetStatus` | Get character status flags (bit 0x10 = alive/available) |
| `0x005152a0` | `ChatAllowAlert` | Can we call target? |
| `thunk_FUN_007bdbb0` | `AvSelectGetAuto` | Get auto-selection target |
| `0x007b89e0` | `SetPrimaryCombatTarget` | Set primary combat target |
| `0x0047f0e0` | `CharCliAgentGetControlled` | Get controlled character pointer |
| `0x007f3400` | `CharClient::CBase::RemoveClientControl` | Release client input control |
| `FUN_005d9f70` | `AgentGetPoint` | Get agent world position |
| `FUN_0052fa20` | `WalkToPoint` | Walk to point |

### PreGameContext (CScene) Functions (2026-06-06)

The pregame/character-login scene. CScene is a **0x100-byte standalone object** (NOT an IFrame 0x1C8 frame). Global pointer accessible via GWCA `FindAssertion("UiPregame.cpp", "!s_scene", 0, 0x34)`. Full struct layout in gw-data-structs skill.

| WASM Symbol | WASM Address | EXE Address | Role |
|-------------|-------------|-------------|------|
| `CScene::CScene` | `ram:80f59983` | `0x004ac010` | Constructor; allocates 0x100 bytes, initializes all fields |
| `CScene::AdvanceCamera` | `ram:80f54729` | — | Per-frame spring-damper camera animation (5 variable groups) |
| `CScene::UpdateCameraOffset` | `ram:80f56485` | — | Mouse wheel/drag camera offset update |
| `CScene::OnNotifyUpdateSel` | `ram:80f617f9` | `0x004adb00` | Server notification: char selection changed (+0xD8) |
| `CScene::OnCreateCanceled` | `ram:80f5a56c` | `0x004acdd0` | Sets chosen_character_index (+0xD4) and preview (+0xD8) to -1 |
| `CScene::OnCreateInitiated` | `ram:80f5b8da` | `0x004acf20` | Character creation started; reads create_slot_index (+0xF0) |
| `CScene::OnNotifyAdd` | `ram:80f5eec1` | — | Character added to list |
| `CScene::OnNotifyClear` | `ram:80f60422` | — | Character list cleared |
| `IUi::PregameSceneProc` | `ram:80f64cf6` | `0x004ae7e0` | FrameProc; msg 0x09 creates CScene, reads +0xD4 for UI |
| `IUi::CCharSummary::Update` | `ram:80efb872` | — | Character summary panel update (doll, stats) |
| `IUi::CCharSummary::Import` | `ram:80efa77b` | — | Char summary data import |

### Property Table System (2026-06-06)

The game accesses sub-contexts through a central property table at `DAT_ram_0028b200`, indexed by `EProp` enum. No GameContext chain traversal needed for most queries.

| Function | WASM Address | Prototype | Role |
|----------|-------------|-----------|------|
| `PropGet` | `ram:8000ac03` | `void*(int EProp)` → returns ptr | Returns `*(DAT_ram_0028b200 + EProp * 4)` |
| `PropContextSet` | `ram:8000aec4` | `void(int EProp, void* ptr)` | Writes to `DAT_ram_0028b200 + EProp * 4` |

**Known EProp values**: `0x0B` = WorldContext* (verified via 8 offset matches in CharCliVanquish*, CharCliMinion*, CharCliMission*).

**WASM offset recovery methodology**: In decompilation, field offsets appear as `(int)&DAT_ram_XXXXXXXX` where `XXXXXXXX` = offset value. Example: `(int)&DAT_ram_0000084c + worldPtr` means `worldPtr + 0x84C`. Used successfully to verify 8 WorldContext offsets and fully map CScene 0x00–0xFF.

### PreGameContext Assertion Bridge

GWCA access (from `GWCA.cpp:131-133`):
```
FindAssertion("UiPregame.cpp", "!s_scene", 0, 0x34) → EXE 0x004ae83d
→ reads *(uintptr_t*)(address) → PreGameContext** pointer
```
WASM string @ `ram:00113147`.

**EXE↔WASM Bridged Pairs:**
| EXE Address | WASM Symbol |
|-------------|-------------|
| `0x004ae7e0` | `IUi::PregameSceneProc` |
| `0x004ac010` | `CScene::CScene` |
| `0x004adb00` | `CScene::OnNotifyUpdateSel` |
| `0x004acdd0` | `CScene::OnCreateCanceled` |
| `0x004acf20` | `CScene::OnCreateInitiated` |
| `0x004ad5a0` | `CScene::OnNotifyCreate` |

---

## 4. UI Message Dispatch Architecture

Game interaction flows through the UI message system. Most game actions (interaction, targeting, inventory, party, chat, etc.) are dispatched as UI messages rather than direct function calls.

### Message Ranges

| Range | Type | Direction | Examples |
|-------|------|-----------|----------|
| `0x00–0x55` | Base frame messages | Internal frame lifecycle | `kInitFrame=0x9`, `kDestroyFrame=0xB`, `kKeyDown=0x20` |
| `0x10000007–0x100001CC` | Notification/event messages | Server→Client (incoming) | `kEffectAdd`, `kMapLoaded`, `kAgentSkillActivated`, `kQuestAdded` |
| `0x30000002–0x30000022` | Command/send messages | Client→Server (outgoing) | `kSendWorldAction`, `kSendChatMessage`, `kSendInteractNPC` |

### Dispatch Mechanism

The game uses a **hash table** — not a switch statement or array:

```
SendUIMessage(msg_id, wParam, lParam)
    │
    ├─→ FrameMsgSendRegistered(msg_id, wParam, lParam)     [for msg_id > 0x55]
    │       └─→ IFrame::CMsg::DispatchRegistered(msg_id, ...)
    │               └─→ THashTable<CHandler>::Find(&DAT_ram_005a0338, &msg_id)
    │                       └─→ CHandler::Dispatch(wParam, lParam)
    │
    └─→ Ui_BroadcastRegisteredFrameMessage(msg_id)         [GWCA callback layer]
            └─→ registered callbacks (GWCA OnUIMessage hook)
```

**Key facts:**
- **Hash table** at `DAT_ram_005a0338` (`THashTable<IFrame::Msg::CHandler, THashKeyVal<uint>>`) — the handler registry
- **Registration** flows through: `FrameMsgRegister(msg_id, flags)` → `IFrame::CMsg::Register(msg_id)` → `TBaseHashTable<IFrame::Msg::CHandler>::Add(handler, msg_id)`
- **Sending** flows through: each caller calls `FrameMsgSendRegistered(CONSTANT_msg_id, ...)` with a hard-coded message ID
- The hash table is zero-initialized at compile time and **populated at runtime** by init code — it cannot be dumped statically

### How GWCA Hooks the System

GWCA hooks two entry points:

| Hooked Function | Pattern | Address |
|-----------------|---------|---------|
| `SendUIMessage_Func` | `\xB9\x00\x00\x00\x00\xE8\x00\x00\x00\x00\x5D\xC3\x89\x45\x08` | `0x006102a5` → ToFunctionStart |
| `SendFrameUIMessageById_Func` | `\x83\xfb\x56\x73\x14` (-0x34) | `0x00610130` |

GWCA's `OnSendUIMessage` receives **every** message passing through the system. It logs them to `ui_payload_logs` and dispatches to `UIMessage_callbacks` (per-message callback registry at GWCA level).

### Message Discovery Methods

**Method A: Runtime logging (GWCA approach)**
Hook `SendUIMessage_Func`, play through game states, log every message ID + wParam payload. GWCA already does this in `UIMgr.cpp:375`. The `ui_payload_logs` buffer records incoming (server→client) and outgoing (client→server) messages.

**Method B: Static analysis (WASM)**
Every message is sent by a named WASM function calling `FrameMsgSendRegistered(CONSTANT_ID, ...)`. Enumerate all callers, extract the constant `i32.const` first argument, cross-reference with the handler function name. Requires a Ghidra script (see Appendix).

**Message IDs found via WASM that GWCA's enum doesn't name:**

| Message ID | WASM Handler | Probable Meaning |
|-----------|-------------|------------------|
| `0x10000035` | `CharCliOnHardModeIsAllowed` | Hard mode permission state change |
| `0x10000036` | `CharCliOnHenchmanAgent` | Henchman agent added/updated |
| `0x100000c6` | `AccountCliOnPromotionWarning` | Account promotion notification |

**GWCA entries needing identification** (~15 unknowns):
`kInventoryRelated1/2/3` (0x1A8–0x1AA), `kItemRelated_1/3/4` (0x1AD–0x1B0), `kInventoryRelated_1/2` (0x1C2–0x1C3), `kMissionStatusRelated` (0x1C4), `kUnused_1c2` (0x1C5), `kTemplateRelated_1/2/3/4` (0x1C7–0x1CC), `kUnknownQuestRelated` (0x154).

### Per-Type Interaction Messages (0x3000000D–0x30000011)

```python
kSendInteractNPC    = 0x3000000D  # wparam = UIPacket::kInteractAgent*
kSendInteractGadget = 0x3000000E  # wparam = UIPacket::kInteractAgent*
kSendInteractItem   = 0x3000000F  # wparam = UIPacket::kInteractAgent*
kSendInteractEnemy  = 0x30000010  # wparam = UIPacket::kInteractAgent*
kSendInteractPlayer = 0x30000011  # wparam = uint32_t agent_id
```

These route through: handler → `ExecuteDefaultWorldAction` → `GetDefaultWorldAction` → `CoreActionExecuteWorldAction`.
This is the **official game UI path** with full validation.

### Unified World Action Message (0x30000020)

```python
kSendWorldAction = 0x30000020  # wparam = UIPacket::kSendWorldAction*
# Packet: { WorldActionId action_id, uint32_t agent_id, bool suppress_call_target }
```

Routes directly to: `CoreActionExecuteWorldAction`. Simpler path, fewer checks.
This is what both GWCA and the Python code use.

### WorldActionId Values

```python
InteractEnemy        = 0
InteractPlayerOrOther = 1
InteractNPC          = 2
InteractItem         = 3
InteractTrade        = 4
InteractGadget       = 5
```

### Other Key Messages

```python
kSendChangeTarget = 0x3000000B  # { target_id, auto_target_id }
kSendCallTarget   = 0x30000013  # { call_type, agent_id }
kSendAgentDialog  = 0x30000014  # dialog_id
kSendGadgetDialog = 0x30000015  # dialog_id
kSendDialog       = 0x30000016  # dialog_id (internal)
```

### Complete GWCA UIMessage Catalog

The authoritative enum is at `Py4GW\vendor\gwca\Include\GWCA\Managers\UIMgr.h:294` (~120 entries). The Python port is at `Py4GWCoreLib\enums_src\UI_enums.py`.

### UI Message Infrastructure Functions

| Function | Address (EXE) | Role |
|----------|---------------|------|
| `SendUIMessage_Func` | via pattern `\xB9...\x5D\xC3\x89\x45\x08` | Main entry point: takes `(msg_id, wParam, lParam)` |
| `SendFrameUIMessageById_Func` | `0x00610130` | Frame-targeted message dispatch (validates frame != 0, msg_id >= 0x56) |
| `Ui_BroadcastRegisteredFrameMessage` | `0x00610290` | Fires all GWCA-registered callbacks for a message |
| `Ui_DispatchFrameMessageToActiveNode` | — | Internal: routes message to active frame node's handler |
| `FrameMsgSendRegistered` | WASM `ram:809b8869` | WASM-side: dispatches high-bit messages via hash table lookup |
| `IFrame::CMsg::DispatchRegistered` | WASM `ram:80978e1a` | Core dispatch: `THashTable::Find(DAT_ram_005a0338, &msg_id)` |
| `IFrame::CMsg::Register` | WASM `ram:80975458` | Registers a handler for a message ID |
| `TBaseHashTable<CHandler>::Add` | WASM `ram:8097658b` | Inserts handler into hash table (used by Register) |

### Appendix: Ghidra Script to Dump All Message IDs

```java
// Finds all callers of FrameMsgSendRegistered in WASM, extracts constant msg_id
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;

public class DumpMsgIds extends GhidraScript {
    public void run() throws Exception {
        Function target = null;
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            if (f.getName().contains("FrameMsgSendRegistered")) {
                target = f; break;
            }
        }
        if (target == null) { println("Not found"); return; }
        Set<String> seen = new HashSet<>();
        for (Reference ref : currentProgram.getReferenceManager()
                .getReferenceAddressesTo(target.getEntryPoint())) {
            Function caller = currentProgram.getFunctionManager()
                .getFunctionContaining(ref.getFromAddress());
            if (caller == null || !seen.add(caller.getName())) continue;
            Instruction prev = currentProgram.getListing()
                .getInstructionBefore(ref.getFromAddress());
            if (prev == null) continue;
            byte[] b = new byte[5];
            currentProgram.getMemory().getBytes(prev.getAddress(), b);
            if ((b[0] & 0xff) != 0x41) continue; // not i32.const
            long val = 0; int shift = 0;
            for (int i = 1; i < 5; i++) {
                int byteVal = b[i] & 0xff;
                val |= (long)(byteVal & 0x7f) << shift;
                shift += 7;
                if ((byteVal & 0x80) == 0) break;
            }
            if (val >= 0x10000000 && val <= 0x3FFFFFFF)
                println(String.format("0x%08X  <-  %s", val, caller.getName()));
        }
    }
}
```

Run with: `mcp__ghidra__run_script_inline` (requires `GHIDRA_MCP_ALLOW_SCRIPTS=1`)

---

## 5. Runtime Packet Sniffers

Py4GW already has live packet capture surfaces for both directions. The dedicated reference for this topic is:

- `docs/RE/packet_sniffers_reference.md`

Use that file for:

- StoC/CToS sniffer architecture
- Python and C++ sniffer file locations
- what `tick`, `header`, `size`, and `data` actually mean
- packet dump tooling and its current limitations

Keep this file as the high-level entry point; put future sniffer-specific detail in the dedicated sniffer reference instead.
- `Py4GWCoreLib/PacketSniffer.py`
- `Py4GWCoreLib/PacketSniffer.py`
- `capture_name_surfaces.py`
- `Widgets/Coding/Debug/Guild Wars/PacketSnifferTester.py`

### FrApi Function Mapping (Updated 2026-06-03)

The Frame API functions (FrApi.cpp) in `UIMgr.cpp` map WASM symbols to EXE addresses.
After 4+ rounds of window-polish RE, all core positioning/chrome functions are now bridged:

| FrApi Function | WASM Symbol | WASM Address | EXE Address (05-30-2026) | Status |
|---------------|-------------|-------------|--------------------------|--------|
| FrameSetLayer | `FrameSetLayer` | `ram:809b060f` | **`0x0062f5a0`** | **Bridged** — `FindAssertion("FrApi.cpp","frameId",0xbfb,0)` |
| FrameSetPosition | `FrameSetPosition` | `ram:809a9f40` | **`0x0062f7f0`** | **Bridged** — `FindAssertion("FrApi.cpp","frameId",0x85c,0)`. ⚠️ Takes Coord2f* not two floats. |
| FrameSetSize | `FrameSetSize` | `ram:809a9c3e` | **`0x0062f9a0`** | **Bridged** — `FindAssertion("FrApi.cpp","frameId",0x880,0)` |
| FrameGetClientBorder | `FrameGetClientBorder` | `ram:809a8164` | **`0x0062D000`** | **Bridged** — `FindAssertion("FrApi.cpp","frameId",0x7dd,0)`. Returns Rect4f* |
| FrameActivate | `FrameActivate` | `ram:809b0e7f` | **`0x0062b000`** | **Bridged** — `FindAssertion("FrApi.cpp","frameId",0xC3E,0)` |
| FrameGetTitle | `FrameGetTitle` | `ram:809b0790` | `0x0062????` (TBD) | **Stub** — vtable `CNonclient::GetTitle()`, no struct field |
| FrameGetCode | `FrameGetCode` | `ram:809af832` | `0x0062????` (TBD) | **Struct** — `frame->frame_id` |
| FrameGetMinSize | `FrameGetMinSize` | `ram:809aa2b3` | `0x0062????` (TBD) | **Stub** — msg 0x15 via controller |
| FrameGetClipRect | `FrameGetClipRect` | `ram:809a830a` | `0x0062????` (TBD) | **Stub** — msg 0x15 dispatch |
| FrameGetPosition | `FrameGetPosition` | `ram:809a886b` | `0x0062????` (TBD) | **Partial** — screen w/h/flags from struct, x/y stubbed |
| FrameGetNativeSize | `FrameGetNativeSize` | `ram:809a8482` | `0x0062????` (TBD) | **Stub** — method call on CRect |
| FrameSetOpacity | `FrameSetOpacity` | `ram:809b7f49` | `0x0062????` (TBD) | **Struct** — writes `frame+0x30` float (no fade anim) |
| FrameShow | `FrameShow` | `ram:809a5e39` | `0x0062????` (TBD) | **Delegate** → `SetFrameVisible` (msg 0x36 skipped) |
| GetOverlays | `IFrame::CRelation::GetOverlays` | `ram:80984909` | `0x0062d960` | **Hardcoded** — needs Scanner pattern |
| GetPopups | `IFrame::CRelation::GetPopups` | `ram:80984be8` | `0x0062daa0` | **Hardcoded** — needs Scanner pattern |
| GetChildFromNameHash | `IFrame::CRelation::GetChildFromNameHash` | `ram:80983fda` | `0x0062ccb0` | **Hardcoded** — needs Scanner pattern |

**⚠️ Key finding:** Previous code used addresses in `0x0060eXXX` range (e.g., FrameGetTitle at `0x0060e810`).
These addresses all land inside function `FUN_0060e290` (a layout/render function), NOT FrApi functions.
The real FrApi functions are in the `0x0062XXXX` range, verified via the `"Engine\\Frame\\FrApi.cpp"` 
assertion string at `0x00a4e36c` which has 100+ xrefs from functions at `0x0062a6e0` through `0x0062d010`.
The remaining hardcoded addresses (`0x0062ccb0`, `0x0062d960`, `0x0062daa0`) are in the correct range 
but should be replaced with `Scanner::Find` patterns for resilience across game updates.

---

## 5. InteractAgent Flow (Case Study)

### What happens when you call `PlayerMethods.InteractAgent(agent_id, call_target=True)`

1. **Python** ([PlayerMethods.py:87](Py4GW_python_files/Py4GWCoreLib/native_src/methods/PlayerMethods.py:87)):
   - Gets agent by ID, determines `WorldActionId` from type + allegiance
   - Sends `kSendWorldAction` UI message with `[action_id, agent_id, call_target]`

2. **EXE/WASM** (`CoreActionExecuteWorldAction` at `0x0050e5e0` / `ram:81260cda`):
   - `AvValidate(agent_id)` — assert agent exists
   - `ChatAllowAlert()` — assert call target is allowed
   - For action=0 (Enemy):
     - `CharCliPlayerOrderAttack(agent, suppress)`
     - If auto-select matches target: `SetPrimaryCombatTarget(agent)`
     - Check agent type/status → Follow or WalkToPoint
     - If call_target: `CharCliPlayerOrderAlertSimple(3, agent)` (CallTarget)
     - `CharCliPlayerOrderInteract(agent, suppress)`
   - For action=2 (NPC): `CharCliPlayerOrderPickup(agent, suppress)`
   - For action=5 (Gadget): `CharCliPlayerOrderUse(agent, suppress)`

3. **Network**: `CharMsgSendOrderInteract` sends opcode 0x39 with `[agent_id, suppress]` (12 bytes)

### What the official UI path adds (NOT taken by current code)

`GetDefaultWorldAction` (`ram:815f3fc8`) checks:
- Observer mode (`MissionCliIsObserver`)
- Agent type mapping: 0x400→Item, 0x200→Gadget, 0xdb→dead special handling
- Dead agent (0xdb): status bit 0x10 + relation-based action selection
- Self-target prevention
- Controlled character liveness

### GWCA Source Match

GWCA's `InteractAgent` at [AgentMgr.cpp:409](Py4GW/vendor/gwca/Source/AgentMgr.cpp:409) uses the same `kSendWorldAction` approach. The Python code is a 1:1 port.

---

## 6. Workflow: Finding and Adding a New Function

### Step 1: Find it in GWCA C++ (or WASM)

```bash
# Search GWCA sources for the function name
grep -r "FunctionName" Py4GW\vendor\gwca\
```

Look for the `Scanner::Find*` call that resolves it. This gives you the technique (assertion, byte pattern, near-call).

### Step 2: Locate in Ghidra

```python
# If you have a WASM name:
mcp__ghidra__search_functions("CharCliPlayerOrderXxx", program="Gw.wasm")
mcp__ghidra__decompile_function("ram:80xxxxxx", program="Gw.wasm")

# If you have an assertion string:
mcp__ghidra__search_strings("assertion text", program="Gw.exe")
mcp__ghidra__get_xrefs_to("0x00xxxxxx")
mcp__ghidra__decompile_function("0x00xxxxxx")
```

### Step 3: Cross-reference EXE ↔ WASM

Use string anchoring (see CPP_WASM_MAPPING.md) or byte patterns.

### Step 4: Add to Python

In the appropriate file under `Py4GWCoreLib/native_src/methods/`:

```python
MyFunc = NativeFunction(
    name="MyFunc",
    pattern=b"\x...",
    mask="xxxxx",
    offset=0,
    section=ScannerSection.TEXT,
    prototype=Prototypes["Void_U32"],
)
```

Or for direct address:
```python
MyFunc = NativeFunction.from_address(
    name="MyFunc",
    address=0x005XXXXX,
    prototype=Prototypes["Void_U32"],
)
```

### Step 5: Create high-level wrapper

In the corresponding `Py4GWCoreLib/*.py` file, wrap the native call through `Game.enqueue()`.

---

## 7. Scanner API Reference

### Python Scanner (`Py4GWCoreLib/Scanner.py`)

```python
Scanner.FindAssertion(file, expression, line, offset) → address or None
Scanner.FindInRange(pattern, mask, offset, start, end) → address or None
Scanner.ToFunctionStart(address) → function_entry
Scanner.FunctionFromNearCall(address) → call_target
Scanner.IsValidPtr(address) → bool
```

### GWCA C++ Scanner

```cpp
Scanner::Find(pattern, mask, offset)           → byte pattern scan
Scanner::FindAssertion(file, expr, line, off)  → find assertion string
Scanner::ToFunctionStart(addr)                 → walk back to function prologue
Scanner::FunctionFromNearCall(addr)            → decode CALL at addr to target
Scanner::IsValidPtr(addr, section)             → pointer validation
*(uintptr_t*)addr                              → read 4-byte pointer (data globals)
```

---

## 8. Common Ghidra MCP Tool Calls

| Operation | Tool |
|-----------|------|
| Find function by name | `mcp__ghidra__search_functions` |
| Decompile function | `mcp__ghidra__decompile_function` |
| Find string in binary | `mcp__ghidra__search_strings` |
| Get xrefs to address | `mcp__ghidra__get_xrefs_to` |
| Search byte pattern | `mcp__ghidra__search_byte_patterns` |
| List callees/callers | `mcp__ghidra__get_function_callees` / `get_function_callers` |
| Disassemble function | `mcp__ghidra__disassemble_function` |
| Get function at address | `mcp__ghidra__get_function_by_address` |
| Switch active program | `mcp__ghidra__switch_program` |
| Debugger attach to Gw.exe | `mcp__ghidra__debugger_attach` |

Always pass `program="Gw.wasm"` or `program="Gw.exe"` explicitly when both programs are loaded.

---

## 9. Pitfalls and Gotchas

- **Patterns rot**: byte patterns can match the wrong function after patches. Always verify behaviorally. The `MoveTo_Func` case is the canonical example — the pattern resolves but the function body doesn't match the typedef.
- **Thunks vs bodies**: MSVC emits JMP thunks. `CallTarget_Func`'s thunk at `0x008102d0` is just `JMP 0x00917740`. **Hook/decompile the body, not the thunk.**
- **Inlining differs**: Emscripten and MSVC make different inlining decisions. Expect ±1 callee differences.
- **WASM address spaces**: code at `ram:8XXXXXXX` (high), strings/data at `ram:00XXXXXX` (low).
- **EXE address ranges**: code at `0x00400000–0x00B00000`, `.rdata` strings at `0x00A00000+`, globals at `0x00BFXXXX`.
- **Pattern uniqueness**: always confirm single match before trusting.
- **Python 3.13.0 32-bit**: the runtime target. Don't switch interpreters casually.
- **`Game.enqueue()`**: all native calls must be queued through the game loop, not called directly.

---

## 10. Window Positioning System (2026-06-03)

After 4+ rounds of RE, the cold-created window pipeline is fully functional. This section documents the complete coordinate system, chrome dimensions, and function catalog for correct window positioning.

### Coordinate Spaces

1. **Overlay (PIXEL)**: Top-left origin, (0,0) = top-left of render target
2. **Game engine (LOGICAL)**: CRect stores position in top-left convention (flags=0x06), but **BuildRect inverts Y during rendering** — positions appear bottom-left on screen
3. **Viewport scale**: `pixels / logical` from `IScaleSetWindowDims` — NOT always 1.0 (windowed mode, DPI scaling)

### Chrome Dimensions (subclass 0x59, bit 9 NOT set)

| Dimension | Value | Source |
|-----------|-------|--------|
| Title bar height | 20 px | CRProc 0x00876E05 |
| Left/right border | 32 px | CRProc 0x00877148 |
| Bottom border | 32 px | CRProc 0x00877148 |

Frame dimensions from content dimensions:
```
frame_w = content_w + 64   // L+R borders
frame_h = content_h + 52   // title + bottom border
```

### Coordinate Conversion Formula

```python
pixel_w, pixel_h = Overlay().GetDisplaySize()
scale_x, scale_y = UIManager.GetViewPortScale(root_id)

engine_px_x = content_x - LEFT_BORDER                          # 32
engine_px_y = pixel_h - content_y - content_h - BOTTOM_BORDER   # 32
frame_px_w = content_w + LEFT_BORDER + RIGHT_BORDER             # +64
frame_px_h = content_h + TOP_TITLE + BOTTOM_BORDER              # +52

engine_x = engine_px_x / scale_x
engine_y = engine_px_y / scale_y
engine_w = frame_px_w / scale_x
engine_h = frame_px_h / scale_y
```

### Subclass and Frame Flags

| Flag | Value | Effect |
|------|-------|--------|
| Subclass 0x59 | 0x01\|0x08\|0x10\|0x40 | Title bar, resize, chrome rendering |
| frame_flags=0x20 | bit 5 | Popup registration in CRelation::Create() — required for click-to-raise |
| frame_flags=0 | default | NO popup registration → click-to-raise silently fails |

### Correct Lambda Order (game thread)

```
FrameNewSubclass → FrameMouseEnable → SetFrameText →
ProcessFrameControllerUpdateByFrameId → FrameSetPosition →
FrameSetLayer → FrameActivate → ShowFrame → TriggerFrameRedraw
```

### Bridged Functions

| Function | EXE Address | Prototype | Assertion Line |
|----------|-------------|-----------|---------------|
| `FrameSetLayer` | **`0x0062f5a0`** | `void(uint frameId, int layer)` | FrApi.cpp line 0xbfb |
| `FrameSetPosition` | **`0x0062f7f0`** | `void(uint frameId, Coord2f* pos)` | FrApi.cpp line 0x85c |
| `FrameSetSize` | **`0x0062f9a0`** | `void(uint frameId, Coord2f* size)` | FrApi.cpp line 0x880 |
| `FrameGetClientBorder` | **`0x0062D000`** | `Rect4f*(Rect4f* out, uint frameId)` | FrApi.cpp line 0x7dd |
| `FrameActivate` | **`0x0062b000`** | `void(uint frameId)` | FrApi.cpp line 0xC3E |

All resolved via `FindAssertion("P:\\Code\\Engine\\Frame\\FrApi.cpp", "frameId", <line>, 0)` + `ToFunctionStart`.

### Pitfalls

1. **FrameSetPosition takes `Coord2f*`** (pointer to packed `{float x, float y}`), NOT two floats
2. **BuildRect inverts Y** — Y-inversion IS required despite CRect Normal-mode flags
3. **Viewport scale ≠ 1.0** in windowed mode — divide by scale to convert pixel→logical
4. **CRect flags 0x06 are STORAGE convention**, not rendering convention
5. **UiGenerateFramePositionLockFlags** dynamically removes TOP anchor — bypass with FrameSetPosition
6. **Without frame_flags=0x20**, click-to-raise silently fails (no popup hash table registration)

### Full investigation in:
- `.opencode/projects/re/window-polish/context_pool.md` — all 4 analysis reports + implementation
- `docs/RE/window_creation_architecture.md` — Positioning and Chrome section

---

## 11. Window Title Rendering System (2026-06-02 RESOLVED)

After 3 RE sessions and 11 failed approaches, the window title rendering pipeline for cold-created containers has been resolved.

### Working Pipeline

```
send_title_msg_5e(frame_id, "title")
  → SetFrameTitleAndInvalidate()
    → Ui_CreateEncodedText(8, 7, title, 0) → encoded wchar_t*
    → Ui_SetFrameText(frame, encoded)        → stores text at frame+0xCC
    → PerFrameInvalidate(frame_id, 0xFFFFFFFF) → sets paint mask + dirty list
  → CRProc msg 0x08 renders title ✅
```

### 05-30-2026 Key Addresses

| Function | Address | Resolution |
|----------|---------|------------|
| `Ui_CreateEncodedText` | `0x007c3be0` | Wildcarded pattern (2 matches, first=correct) |
| `Ui_SetFrameText` | `0x0062fab0` | **DevText call-site derived** — do NOT use byte pattern |
| `PerFrameInvalidate` | `0x0062bd80` | Pattern: `8D 48 04 53 6A 04 E8` → ToFunctionStart(-0x57) |
| DevText proc | `0x0088a870` | `FindNthUseOfString(L"DlgDevText")` |
| CALL UiCreateEncodedText | `0x0088a9fc` | Return: `0x0088aa01` |
| CALL UiSetFrameText | `0x0088aa03` | Return: `0x0088aa08` |

### Critical Pattern Pitfall

The `Ui_SetFrameText` prologue pattern (`55 8B EC 53 56 57 ... 75 14 68 ?? ?? ?? ??`) matches **16 functions** in `FrApi.cpp`. `Scanner::Find` always returns the wrong function (lowest address match). **Always derive `Ui_SetFrameText` from DevText's call site** — find the "DlgDevText" string use, scan forward for CALLs: first CALL = `Ui_CreateEncodedText`, second CALL = `Ui_SetFrameText`.

### Python API (Canonical, 2026-06-03)

```python
# Canonical one-call titled container window:
fid = PyUIManager.UIManager.create_container_window_with_title(
    x=100, y=100, width=400, height=300, title="My Custom Title")

# Or the older two-step equivalent:
# fid = PyUIManager.UIManager.create_titled_container_window(
#     x, y, w, h, "", 9, 0, 0x20, 0x6, 0x59)
# PyUIManager.UIManager.send_title_msg_5e(fid, "My Custom Title")
```

### 2026-06-03 Cleanup — Shared Resolver Consolidation

The resolution logic was consolidated into shared helpers in `py_ui.h`:
- **`ResolveCreateEncodedText()`** — single shared resolver for `Ui_CreateEncodedText` with prologue validation.
- **`ResolveSetFrameText()`** — shared helper for DevText call-site derived `Ui_SetFrameText`.

All hardcoded address comments in `py_ui.h` were removed. All missing bindings added to `stubs/PyUIManager.pyi`.

### Complete investigation in:
- `docs/RE/title_rendering_research.md` — all 11 failed approaches + working solution
- `docs/RE/native_gw_window_creation_investigation.md` — window creation pipeline

---

## 12. Frame List Architecture (2026-06-04)

After the window-contents RE cycle, the frame list system is fully mapped. Frame lists (type `0xAEA`, `CCtlFrameList::FrameProc`) are the game's reusable scrollable container component, used by **81 windows** across 12 game domains.

### Frame Hierarchy

```
Root Window (e.g., DlgDevTextProc @ EXE 0x0088a870)
  └─ child N: FrameList (type 0xAEA = CCtlFrameList::FrameProc @ EXE 0x00612c80)
       │  Created: FrameCreate(parent, 0x20000|0x380, N, 0xAEA, {0, &page_size, 0}, null)
       │  Subclass: FrameNewSubclass(list, &chrome_proc, 0x59)  ← adds scrollbar chrome
       │
       ├─ item 0: TextLabel (CtlTextProc @ EXE 0x00610c40)
       ├─ item 1: TextLabel
       └─ ... N items (e.g., DevText has 30)
```

The frame list is NOT always child 0. Its position varies by window:
- **Child 0**: DevText, InventoryAggregate, FriendsList
- **Child 1**: PartySearch (inside tab page)
- **Child 2**: VendorBuy, SelectMission

Three architectural patterns identified:

| Pattern | Structure | Example Windows |
|---------|-----------|----------------|
| **A (simple)** | Root → [decorative children] → FrameList (child N) → Items | DevText, InventoryAggregate, FriendsList, VendorBuy, SelectMission |
| **B (nested)** | Root → CategoryFrame → FrameList → Items | Party, Guild, AutoTourn |
| **C (scrollable)** | Pattern A + `FrameNewSubclass(list, &proc, 0x59)` for scrollbars | DevText, InventoryAggregate, PartySearch |

Common frame list creation flags:
- `0x20000` — scrollable wrapper (most windows)
- `0x380` — additional scroll/auto-sizing (DevText only)
- `0x20080` — variant (FriendsList)

### Key Message Map: CCtlFrameList::FrameProc @ EXE 0x00612c80

| Msg Hex | Msg Dec | Handler | Effect |
|---------|---------|---------|--------|
| 0x09 | 9 | Create | Allocates internal data block (6×4 bytes) |
| 0x0B | 11 | Destroy | Frees internal data |
| 0x13 | 19 | GetFirstChild | Returns first child frame ID |
| 0x37 | 55 | **OnFrameMsgSize** | **Stacks children vertically** (bottom-to-top) — THE layout engine |
| 0x38 | 56 | **OnFrameMsgSizeQuery** | Reports cumulative child native size |
| 0x56 | 86 | FrameDestroyChildren | Destroys all item children |
| 0x57 | 87 | **FrameCreate** | **Creates item child frame** — used by CtlFrameListCreateItem. ORs flags with `\|0x300` |
| 0x59 | 89 | OnThisMsgEnumItem | Enumerates items (4 relation types: first/next/prev/last) |
| 0x5C | 92 | GetItemRect | Gets item bounding rect |
| 0x5F | 95 | OnThisMsgMoveItem | Moves/reorders items |
| 0x62 | 98 | SetSizeHandler | Sets CtlFrameListSetSizeHandler |
| 0x63 | 99 | SetSizeQueryHandler | Sets CtlFrameListSetSizeQueryHandler |
| 0x65 | 101 | OnThisMsgShowItem | Show/hide item → triggers relayout |

### CCtlFrameList::OnFrameMsgSize — The Stacking Engine

Algorithm (@ WASM `ram:80e7d758`):
1. Check **style `0x2000`** on frame — if set, **skip automatic layout** (items positioned manually)
2. `BuildItemFrameIdArray` — collect all child frame IDs
3. If custom sort handler exists → delegate
4. Otherwise: iterate array, stacking from bottom to top:
   - Starting Y = parent height
   - For each child: `Y = Y - child_native_height`, X = 0
   - `FrameSetPosition(child, {0, Y}, {0, 0})`

### CtlFrameListCreateItem @ EXE 0x00612900

**Prototype**: `uint32 CtlFrameListCreateItem(uint32 parentFrameId, uint32 flags, uint32 insertIndex, void (*itemProc)(...), void* userData)`

Builds a 4-field create-param struct, sends message **0x57** to the parent frame list via `FrameMsgSend(parent, 0x57, &createParam, &result)`. The frame list's msg 0x57 handler creates the child via `FrameCreate` with flags `| 0x300`. Returns new item frame ID.

**Byte pattern**: `\xC7\x45\x0C\x00\x00\x00\x00\x50\x6A\x57\xFF\x75\x08` at offset `-0x25`.

### FrameNewSubclass @ EXE 0x0062f150

**Prototype**: `void* FrameNewSubclass(uint32 frameId, void* subclassProc, uint32 msgId)`

Performs: `GetFrame(frameId)` → `NewSubclass()` → `SetSubclass(frame, proc, msgId, ...)`. Registers a subclass handler for a specific message ID. Used to add scrollbar chrome to frame lists (e.g., DevText uses `FrameNewSubclass(list, &proc, 0x59)`).

**Byte pattern**: `\x8D\xB8\xA8\x00\x00\x00\x8B\xCF` at offset `-0x2D`.

### DevText Reference Model

- **30 items total**: 15 plain + 15 rich-text (looped with style_id 0–14)
- **Frame list flags**: `0x20380` = `0x20000 | 0x380`
- **Item proc**: `CtlTextProc` (table index `0xA81`)
- **Subclass proc**: `proc_0xAED` (table index 2797, CtlViewProc-related) applied via `FrameNewSubclass`
- NO `CtlViewSetIncrement` — relies on default scroll stepping
- NO `CtlViewSetPage` — no explicit page size handler

### Size Propagation Chain

```
Window Resize → parent FrameProc msg 0x38 (SizeQuery)
  → FrameGetChild(root, N) → frameListId
  → FrameGetNativeSize(frameListId)
    → CCtlFrameList::FrameProc msg 0x38 (OnFrameMsgSizeQuery)
      → BuildItemFrameIdArray
      → Accumulate native widths/heights for all items
      → Report total size

Frame List Size Change → msg 0x37 (OnFrameMsgSize)
  → BuildItemFrameIdArray
  → For each item: stack bottom-to-top
  → FrameSetPosition(item, {0, Y}, {0, 0})
```

### Style 0x2000 — Manual Positioning Mode

When style `0x2000` is set on a frame list child, `OnFrameMsgSize` **skips** that child entirely — the child is responsible for its own positioning. This allows mixed auto-stacked + manually positioned items.

### InventoryAggregate — Complete Reference Model

The inventory is the full-featured scrollable reference:

```
CAggregateInv::OnFrameCreate @ WASM ram:81549948:
  1. FrameMouseEnable(frame, 8, 0)
  2. FrameGamepadEnable(frame, 8, 0)
  3. FrameCreate(frame, 0x20000, 0, 0xAEA, null, null)
  4. CtlViewSetIncrement(child, 2)          → scroll step = 2px
  5. CtlViewSetPage(child, 0, &handler, 0)  → page size handler
  6. CtlFrameListSetSizeHandler(child, &handler)  → custom size handler
  7. CtlFrameListSetSizeQueryHandler(child, handler) → size query handler
  8. FrameSetMinSize / FrameSetMaxSize
  9. UpdateBags(frame) → content population
```

All additional operations missing from DevText's minimal setup.

### Bridged EXE Addresses

| Function | EXE Address | Resolution |
|----------|-------------|------------|
| `CCtlFrameList::FrameProc` | `0x00612c80` | Assertion `"No valid case for switch variable 'msg.relation'"` @ `0x00a50290` |
| `CtlTextProc` | `0x00610c40` | Assertion `"FrameTestStyles(hdr.frameId, CTLTEXT_STYLE_MODEL)"` @ `0x00a50110` |
| `CtlFrameListCreateItem` | `0x00612900` | Byte pattern `\xC7\x45\x0C\x00\x00\x00\x00\x50\x6A\x57\xFF\x75\x08` offset -0x25 |
| `FrameNewSubclass` | `0x0062f150` | Byte pattern `\x8D\xB8\xA8\x00\x00\x00\x8B\xCF` offset -0x2D |
| `CContainerFrame::FrameProc` | `0x00871b40` | (`reverse_engineering_reference.md` Section 10) |
| `DlgDevTextProc` | `0x0088a870` | String `"DlgDevText"` @ `0x00b9743c` |

### Implementation Reference

Python repo (`Py4GW_python_files\`):
- `Py4GWCoreLib/native_src/internals/prototypes.py` — added `U32_U32_U32_U32_U32_U32` and `U32_U32_U32_U32` prototypes
- `Py4GWCoreLib/native_src/methods/PlayerMethods.py` — added `CtlFrameListCreateItem_Func` and `FrameNewSubclass_Func` NativeFunctions
- `Py4GWCoreLib/GWUI.py` — complete rewrite (204 lines): `CreateScrollableContent`, `AddTextItem`, `CreateScrollableWindow`, `_encode_text_literal`, `_resolve_text_label_callback`
- `stubs/PyUIManager.pyi` — type stubs for 5 new C++ bindings
- `UI_RE/window_contents_test.py` — 249-line test widget

C++ repo (`Py4GW\`):
- `include/py_ui.h` — added 3 shared resolvers + 5 UIManager methods: `CtlFrameListCreateItemByFrameId`, `FrameNewSubclassByFrameId`, `CreateScrollableContentByFrameId`, `AddTextItemToFrameListByFrameId`, `CreateScrollableTextWindow`
- `src/py_ui.cpp` — added 5 `.def_static()` Python bindings

### Known Limitations

| # | Issue | Impact |
|---|-------|--------|
| 1 | Scrollbar chrome proc unresolved (proc_0xAED) | Scrollbars may not render; use GWCA's CtlViewProc wrapper which handles it |
| 2 | Async return values — `Game.enqueue()` returns 0 until processed | Use polling or C++ bindings for sync |
| 3 | Style 0x2000 for manual positioning not in convenience API | Use low-level `CtlFrameListCreateItem` + `FrameSetPosition` |
| 4 | C++ rebuild required | Build DLL, restart injected client |
| 5 | Pattern rot possible on EXE patches | Patterns use structurally stable function-body internals |

---

## 13. Document Index

All files in `docs/RE/`:

| File | Content |
|------|---------|
| `README.md` | Index of RE documents by purpose |
| `reverse_engineering_reference.md` | This file - canonical library reference and interface guide |
| `CPP_WASM_MAPPING.md` | Full procedure for CPP-to-WASM-to-EXE translation |
| `gw_combat_ai_reverse_engineering.md` | Combat AI reverse engineering analysis |
| `name_obfuscation_reverse_engineering.md` | Name-obfuscation subsystem reference: packet rewrite hook, timing behavior, capture workflow, unresolved surfaces, and the current friend/guild/comm split |
| `native_gw_ui_function_catalog.json` | Catalog of native GW UI functions with addresses |
| `native_gw_window_creation_investigation.md` | Window creation/proc RE investigation |
| `native_ui_title_and_encoded_string_reference.md` | Native UI title and encoding reference |
| `rosetta_stone.txt` | GwA2 (AutoIt) to Py4GW function mapping |
| `title_rendering_research.md` | Title rendering investigation and working solution (11 approaches) |
| `ui_controls_catalog.md` | Complete UI controls catalog - 39 types, tiers, structs, addresses, and Phase 3 crash documentation (2026-06-05) |
| `native_button_pipeline.md` | **Complete button pipeline specification** — rendering, type registry, click dispatch, OnFrameNotify, 2-path comparison, gap inventory. 2026-06-19. |
| `window_creation_architecture.md` | CContainerFrame window creation architecture reference |

Other project docs remain in `docs/`:
- `Py4GW_Conceptual_Model.md` - canonical architecture
- `widget_manager_and_catalog.md` - widget discovery metadata
- `MCP_bridge.md` - MCP bridge planning
- `ui_controls_catalog.md` - Complete UI controls catalog (39 types, 2026-06-05)
- Build, bot, AI, and UI-specific docs

---

## 14. UI Controls Catalog (2026-06-05)

Complete universe discovery of all 39 Guild Wars engine UI control types. Full standalone reference: `docs/RE/ui_controls_catalog.md`. This section covers the essentials.

### Architecture: Three Registration Layers

The engine creates UI components through a three-layer registration system:

| Layer | Function | Role |
|-------|----------|------|
| **FrameProc (Callback)** | `CtlBtnProc`, `CtlDropListProc`, `CtlSliderProc`, etc. | Message handler — paints, handles mouse, creates internal control instance on msg 0x09 |
| **Universal Factory** | `CreateUIComponent` / `FrameCreate` @ `ram:809a13ea` | Allocates 0x1C8-byte `Frame` struct, registers FrameProc, sends lifecycle messages |
| **High-Level Wrapper** | `IUi::UiCtlBtnProc`, `IUi::UiCtlDropListProc`, etc. | Adds default styling, sizing, configuration before delegating to FrameProc |

**The callback is the primary type determinant.** `component_flags` add behavior modifiers:
- `0x8000` = checkbox toggle behavior
- `0x20000` = scrollable wrapper
- `0x300` = base default (`F_VISIBLE|F_ENABLED`), NOT type-identifying
- `0x128` = dropdown listbox (child of dropdown wrapper)

The existing GWCA pattern:
```cpp
ButtonFrame_Callback = Scanner::FindAssertion("UiCtlBtn.cpp", "!s_btnCheckImageList");
CreateUIComponent(parent_id, component_flags | TYPE_FLAG, child_index, CALLBACK, name, label);
```

### Tiered Catalog (39 Types)

**Tier 1 — Wrapped (Create + Manipulate) — 4 types:**
ButtonFrame, CheckboxFrame, ScrollableFrame, TextLabelFrame

**Tier 2 — Struct Exists, Create Attempted But CRASHED — 7 types:**

All had Phase 3 Create functions implemented across the full stack but **all crashed the client**. Research (addresses, assertions, structs, component_flags) is verified — C++ implementation needs rework.

| Control | EXE FrameProc | Assertion | component_flags | Struct |
|---------|--------------|-----------|-----------------|--------|
| **DropdownFrame** | `0x0087f5f0` | `"!FrameGetChild(thisFrame, CTL_LIST_ENTRIES)"` @ `0x00b963fc` | 0x128 (child listbox) / 0x300 (wrapper) | `CtlDropList::Prop`, 100 bytes |
| **SliderFrame** | `0x00615fe0` (base) + `0x0087f440` (wrapper) | `"value >= m_range.min"` @ `0x00a5045c` (base) / byte pattern for wrapper | 0x300* → 0 (game uses 0) | `CtlSlider::CInstance`, 0x30 bytes | **FAILED** — See below |
| **EditableTextFrame** | `0x00888aa0` | `"!s_editCaretMaterial"` @ `0x00b96c00` | 0x300* | `CCtlEdit`, ~0x4C bytes |
| **ProgressBar** | `0x008812e0` | `"!sm_rateArrowImageList"` @ `0x00b964f4` | 0x300* | Inherits ButtonFrame+FrameWithValue |
| **TabsFrame** | `0x0061a950` | `"!IsBtnCode(pageCode)"` @ `0x00a506c0` | 0x300* | `CtlPage::CCtlPage` |
| **MultiLineTextLabel** | `0x00610c40` | `"FrameTestStyles(hdr.frameId, CTLTEXT_STYLE_MODEL)"` @ `0x00a50110` | same callback as TextLabelFrame | 0x170 bytes |
| **GroupHeader** | `0x0087ddc0` | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlGroupHeader.cpp"` @ `0x00b96100` | composite (creates children internally) | new struct needed |

(* = inferred, needs verification from FrameCreate caller)

### GroupHeader — Composite Control Design

**EXE FrameProc**: `0x0087ddc0`  
**WASM**: `IUi::CGroupHeaderFrame::FrameProc` @ `ram:81192c89`  
**WASM OnFrameCreate**: `IUi::CGroupHeaderFrame::OnFrameCreate` @ `ram:811921df`

Creates 2 children internally on msg 0x09:
- Child 0: Checkbox (callback 0x0AFD) — expand/collapse toggle
- Child 1: Text label (callback 0x0A56, flags 0xA0000) — section title

**Message protocol**:
| Msg ID | Command | Direction |
|--------|---------|-----------|
| 0x56 | GetIsOpen | Query |
| 0x57 | SetIsOpen | Command |
| 0x58 | GetText | Query |
| 0x59 | SetText | Command |

### Tier 3 — Cosmetic/Internal — 6 types with confirmed addresses:

| Control | EXE Address | Assertion |
|---------|------------|-----------|
| TextShy | `0x0087f0d0` | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlTextShy.cpp"` |
| Bullet | `0x00884f20` | `"!s_bulletImageList"` |
| BtnExpand | `0x008867f0` | `"P:\\Code\\Gw\\Ui\\Controls\\UiCtlBtnExpand.cpp"` |
| BtnToggle | `0x00886370` | (path assertion — already wrapped as CheckboxFrame with 0x8000 flag) |

### Tier 4 — Infrastructure/Layout (never create directly) — 16 types:
Border, Fade, Gap, Header, ImageList, LabelText, LabeledEdit, List, PageBtn, PageItem, Scroll, TextHeader, TextSelectable, TitleFrame, View, EditAutoComplete

### WASM↔EXE FrameProc Mappings

| Control | WASM FrameProc | WASM Addr | EXE Addr |
|---------|---------------|-----------|----------|
| ButtonFrame | CtlBtnProc | ram:80dbe9be | (in GWCA) |
| DropdownFrame | CtlDropListProc | ram:80e3c9a3 | 0x0087f5f0 |
| SliderFrame | CtlSliderProc (base) | ram:80fcc337 | 0x00615fe0 |
| SliderFrame (wrapper) | IUi::UiCtlSliderProc | ram:80fcd65d | 0x0087f440 |
| EditableTextFrame | CtlEditProc | ram:80dee7ef | 0x00888aa0 |
| ProgressBar | CtlProgressProc | ram:80f6ce9a | 0x008812e0 |
| TabsFrame | CtlPageProc | ram:80e078f3 | 0x0061a950 |
| MultiLineTextLabel | CtlTextMlProc | ram:80da0629 | 0x00610c40 |
| GroupHeader | IUi::CGroupHeaderFrame::FrameProc | ram:81192c89 | 0x0087ddc0 |
| TextShy | IUi::TextShy::CTextShyFrame::FrameProc | ram:8149a9a7 | 0x0087f0d0 |
| Bullet | IUi::UiCtlBulletProc | ram:8134512b | 0x00884f20 |
| BtnExpand | IUi::UiCtlBtnExpandProc | ram:80e7b6f7 | 0x008867f0 |
| BtnToggle | IUi::UiCtlBtnToggleProc | ram:816b67fd | 0x00886370 |

### Phase 3 Crash — CRITICAL NOTE

The Tier 2 Create functions (DropdownFrame, SliderFrame, EditableTextFrame, ProgressBar, TabsFrame) were implemented in C++ and Python across the full stack but ALL crashed the client. DO NOT reuse the Phase 3 C++ code as-is. Full investigation below.

### SliderFrame — Conclusive Failure (2026-06-06)

After 4 implementation attempts across 3 analysis rounds, **SliderFrame creation conclusively failed**. The root cause is fundamental:

**CreateUIComponent cannot create multi-layer FrameProc controls.** The engine's `CreateUIComponent` / `FrameCreate` registers a single raw callback address. Controls like Slider, Dropdown, ProgressBar, Tabs, and EditableText use a **two-layer FrameProc architecture** (paint wrapper → engine base) that depends on the C++ class hierarchy. `CreateUIComponent` does NOT set up this hierarchy — it only registers one callback.

**What was discovered:**

| Layer | Name | EXE Address | Role |
|-------|------|-------------|------|
| Paint wrapper | `IUi::UiCtlSliderProc` | **`0x0087f440`** | Textured slider bar+thumb via `FrameContentAddImageTemplate`. Handles paint (0x01), invalidation (0x0C), native size (0x59). Delegates ALL other messages to base. |
| Engine base | `CtlSliderProc` | **`0x00615fe0`** | Allocates `CtlSlider::CInstance` (0x30 bytes) on msg 0x09. Handles SetRange (0x56), SetValue (0x57), GetValue (0x58), mouse/keyboard input, animation. |

**Attempts that failed:**

| Attempt | Approach | Result |
|---------|----------|--------|
| CtlSliderProc alone | Primary FrameProc, no wrapper | Renders plain gray rectangle (no textured slider visuals) |
| IUi::UiCtlSliderProc as primary | Wrapper as FrameProc via CreateUIComponent | Crashes — wrapper delegates msg 0x09 to FrameMsgCallBase, but no base class registered → CInstance never allocated → null deref on SetValue |
| CtlSliderProc + FrameNewSubclass | Base as primary, wrapper as subclass | No visible effect — subclass may not properly intercept paint in this architecture |

**Root cause**: The game creates sliders through the layout/template system, which knows the C++ class hierarchy (wrapper inherits from base). `CreateUIComponent` bypasses this — it registers raw function pointers without class relationship metadata.

**Byte pattern for IUi::UiCtlSliderProc** (verified unique in 05-30-2026 EXE):
```
\x55\x8B\xEC\x83\xEC\x18\x53\x8B\x5D\x08\x56\x57\x8B\x43\x04\x48\x83\xF8\x58
```
Resolves to `0x0087f440`. Useful for future approaches that can establish the base class chain.

**Working types for comparison**: Button, TextLabel, Checkbox, Scrollable all use **single self-contained FrameProcs** — no base class delegation needed. This is why they work with CreateUIComponent.

**Recommendation**: Abandon CreateUIComponent for multi-layer controls. Investigate the layout/template system (`CCtlLayout::Child`) or frame cloning from existing game windows.

### 14.2 Button Creation Research (2026-06-16) — ALL APPROACHES CRASH

Attempted to create a native GW button as a child of CContainerFrame+CRProc window. **All three FrameProc candidates crash** on `CreateUIComponent`. The crash is NOT FrameProc-specific — a deeper pipeline issue.

#### Failed Attempts

| # | FrameProc | EXE Address | Properties | Result |
|---|-----------|-------------|------------|--------|
| 1 | `IUi::UiCtlBtnProc` | `0x00877e60` | GW UI wrapper, styled rendering | CRASH |
| 2 | `IUi::UiCtlBtnProc` + global clear | `0x00877e60` | Cleared `s_btnCheckImageList` singleton guard | CRASH |
| 3 | `CtlTextBtnProc` | `0x00616c00` | Engine-level, text-only, no IUi:: wrapper, no image lists | CRASH |

#### CtlTextBtnProc — Newly Discovered (06-14 EXE)

| Property | Value |
|----------|-------|
| **WASM** | `CtlTextBtnProc(FrameMsgHdr const&, void const*, void*)` @ `ram:80d9ce76` |
| **EXE** | `FUN_00616c00` @ `0x00616c00` |
| **Bridged via** | WASM string `"../../../../Engine/Controls/CtlTextBtn.cpp"` → EXE `0x00a50488` → xref |
| **Scanner pattern** | `\x83\xC0\xFC\x83\xF8\x5C\x0F\x87` (unique: max msg 0x5C vs 0x5F for UiCtlBtnProc) |
| **Message protocol** | Create: msg 0x09; SetText: 0x5F; SetColor: 0x5B; SetHoverColor: 0x5D |
| **Internal state** | 0x38 bytes allocated on msg 0x09; default text color 0xFF64BEEB, hover 0xFF78D2FF |

#### Key Insight
All three FrameProcs crash identically. The crash root cause IS NOT:
- FrameProc-specific behavior
- Singleton assertion on `s_btnCheckImageList`
- Image list / texture dependencies
- `IUi::` wrapper vs engine-level proc

The issue is likely in `CreateUIComponent` / `FrameCreate` (`FUN_0062bfc0` @ `0x0062bfc0`) when creating button-type FrameProcs. Text labels and scrollable frames work, but button FrameProcs don't — suggesting the pipeline handles different FrameProc families differently.

#### Research Gaps (for next session)
1. **G3**: Test button creation on root frame or frame 9 (parent frame hypothesis)
2. **G6**: Test text label as direct child of CContainerFrame (not inside scrollable)
3. **G2**: Hook-based crash callstack tracing (hook FrameCreate entry/exit + FrameProc entry)
4. **G5**: Frame cloning — clone an existing game button's frame tree
5. **G1**: Find actual game `FrameCreate` calls that create buttons — check component_flags used

#### Project
`.opencode/projects/re/native-window-elements-creation/` — context pool, status, lock files.

---

## 15. Context System (2026-06-06)

### Architecture

The game exposes runtime state through a struct-of-arrays context system. A root `GameContext` struct (0x5C bytes) holds pointers to 13 subsystem contexts. Each context is a fixed-size struct at a known offset within the game's memory — accessed by scanning for byte-pattern signatures.

```
GameContext (root pointer table, 0x5C)
├── agent_context       (+0x00) → AgentContext (AgentSummaryInfo, AgentMovement)
├── map_context         (+0x04) → MapContext (pathing maps, spawns, portals, props)
├── text_parser         (+0x08) → TextParser (string table cache, language slots)
├── account_context     (+0x28) → AccountContext (unlocks, storage panes)
├── world_context       (+0x2C) → WorldContext (players, quests, titles, skillbars)
├── cinematic           (+0x30) → Cinematic (opaque, 8+ bytes)
├── gadget_context      (+0x38) → GadgetContext (GadgetInfo array)
├── guild_context       (+0x3C) → GuildContext (guild roster, history, alliances)
├── item_context        (+0x40) → ItemContext (bags, items, inventory)
├── char_context        (+0x44) → CharContext (player name, map_id, district)
├── party_context       (+0x48) → PartyContext (party members, search)
├── trade_context       (+0x58) → TradeContext (trade state machine)
└── ... (+0x08, +0x0C, +0x10, +0x1C, +0x24, +0x34, +0x48, +0x50, +0x54 = other pointer slots)
```

### Python Facade Layer

The `GWContext` class in `Py4GWCoreLib/Context.py` provides typed accessors:

```python
from Py4GWCoreLib.Context import GWContext

char_ctx = GWContext.Char.GetContext()       # → CharContextStruct | None
world_ctx = GWContext.World.GetContext()     # → WorldContextStruct | None
guild_ctx = GWContext.Guild.GetContext()     # → GuildContextStruct | None
```

Each context facade uses a `NativeSymbol` byte-pattern scan to locate the struct in game memory, then casts raw bytes to a `ctypes.Structure`.

### Context Inventory

#### Registered in GWContext Facade (15 contexts)

| # | Facade Key | Python File | C++ Header | Completeness |
|---|-----------|-------------|------------|--------------|
| 1 | `GWContext.AccAgent` | `AccAgentContext.py` | `AgentContext.h` | 🔶 SKELETON |
| 2 | `GWContext.AgentArray` | `AgentContext.py` | *(agent iteration, not context/)* | 🟡 PARTIAL |
| 3 | `GWContext.AvailableCharacterArray` | `AvailableCharacterContext.py` | *(no C++ header)* | 🔶 SKELETON |
| 4 | `GWContext.Char` | `CharContext.py` | `CharContext.h` | 🟡 PARTIAL |
| 5 | `GWContext.Cinematic` | `CinematicContext.py` | `Cinematic.h` | 🔶 SKELETON |
| 6 | `GWContext.Gameplay` | `GameplayContext.py` | `GameplayContext.h` | 🔶 SKELETON |
| 7 | `GWContext.Guild` | `GuildContext.py` | `GuildContext.h` | 🟡 PARTIAL |
| 8 | `GWContext.InstanceInfo` | `InstanceInfoContext.py` | *(MapMgr)* | ✅ FULL |
| 9 | `GWContext.Map` | `MapContext.py` | `MapContext.h` | ✅ FULL |
| 10 | `GWContext.MissionMap` | `MissionMapContext.py` | `MapMgr.h` | 🟡 PARTIAL |
| 11 | `GWContext.Party` | `PartyContext.py` | `PartyContext.h` | 🟡 PARTIAL |
| 12 | `GWContext.PreGame` | `PreGameContext.py` | `PreGameContext.h` | ✅ FULL |
| 13 | `GWContext.ServerRegion` | `ServerRegionContext.py` | *(MapMgr)* | 🔹 WRAPPER_ONLY |
| 14 | `GWContext.World` | `WorldContext.py` | `WorldContext.h` | 🟡 PARTIAL |
| 15 | `GWContext.WorldMap` | `WorldMapContext.py` | `MapMgr.h` | 🔶 SKELETON |

#### Python Files Outside GWContext Facade

| Python File | Notes |
|-------------|-------|
| `GameContext.py` | Root pointer table struct — used internally, no `GetContext()` facade |
| `TextContext.py` | Has struct + facade but not exposed via `GWContext.*` — used by `Chat.py` |

#### MISSING — C++ Contexts Without Python Counterparts

| C++ Header | Struct | Size | Impact |
|------------|--------|------|--------|
| `ItemContext.h` | `ItemContext` | 0x10C | **Most impactful gap** — `bags_array`, `item_array`, `inventory` pointer |
| `AccountContext.h` | `AccountContext` | 0x138 | Account-wide unlocks, storage panes, PvP items, account skills |
| `TradeContext.h` | `TradeContext` | 0x38 | Trade state machine (flags, gold, items for both sides) |
| `GadgetContext.h` | `GadgetContext` | small | Array of `GadgetInfo` (id + encoded name) |

> The Python `GameContextStruct` already has pointer fields at correct offsets for all four missing contexts — no facade/struct to dereference them yet.

### Context Completeness Legend
- ✅ **FULL**: All fields named/meaningful, size validated with `assert(sizeof(...))`, sub-structs decomposed. Gold standard: `PreGameContext`.
- 🟡 **PARTIAL**: Most key fields named but significant hXXXX placeholders remain. Examples: `WorldContext`, `CharContext`, `GuildContext`.
- 🔶 **SKELETON**: Predominantly hXXXX placeholders, few named fields. Examples: `AccAgentContext`, `WorldMapContext`.
- 🔹 **WRAPPER_ONLY**: Trivial struct (1–2 fields), minimal utility. Example: `ServerRegionContext`.

### Context Completion Pipeline

Active project: `.opencode/projects/re/context-completion/`. One context at a time. See `status.md` for current target and phase.

### Key Source Paths

| Layer | Path |
|-------|------|
| Python contexts | `Py4GWCoreLib/native_src/context/*.py` |
| Python context type stubs | `Py4GWCoreLib/native_src/context/*.pyi` |
| Python facade | `Py4GWCoreLib/Context.py` |
| C++ context headers | `Py4GW\vendor\gwca\Include\GWCA\Context\*.h` |
| C++ map manager contexts | `Py4GW\vendor\gwca\Include\GWCA\Managers\MapMgr.h` |

---

## 16. Map Travel Pipeline (2026-06-12)

Complete RE of the Guild Wars map travel pipeline, server-side arrival check, travel-back mechanism, and experimental hook-based approaches. Full details in dedicated document:

→ **`docs/RE/map_travel_reverse_engineering.md`**

Key EXE addresses (06-14-2026):

| Function | EXE (06-14) | WASM Address | Pattern/Method | Notes |
|----------|-------------|--------------|----------------|-------|
| `MissionCliOnErrorRedirect` | `0x00849230` | `ram:80ca0d96` | `55 8B EC 8B 45 08 53 56 57 8B 70 04` | Hook fires on 0x0191 |
| `MissionCliOnRedirect` | `0x00849990` | `ram:80ca3ac2` | `55 8B EC 8B 45 08 83 EC 08 8B 40 20` | |
| `GameJoin` | **`0x0084b4f0`** | `ram:80ce01aa` | `83 8B 90 01 00 00 20` mask=`xxx??xx` → `ToFunctionStart` | ⚠️ Crashes from stable state. 9 params. |
| `GameRedirectMission` | `0x0084b770` | `ram:80ce1ad1` | `81 8E 90 01 00 00 00 02 00 00 BA 2C` → `ToFunctionStart` | |
| `MsgSendReadyToPlay` | **`0x0084cf80`** | `ram:80ce82ce` | `C7 45 E8 90 00 00 00` → `ToFunctionStart` | Sends {0x90, GUID} 20 bytes |
| `PropGet` | `0x0047f510` | `ram:8000ac03` | `8B 0D ?? ?? ?? ?? 64 A1 2C 00 00 00 8B 04 88 8B 80 08 00 00 00 C3` | |

\* Runtime addresses shown from debug log (trampoline or actual — see note below)

### Additional Functions (WASM-Verified, updated 2026-06-14)

| GWCA Name | WASM Symbol | WASM Address | EXE Address | Prototype | Role |
|-----------|-------------|-------------|-------------|-----------|------|
| `ReconnectDataRead_Func` | `MissionClient::ReadReconnectData` | `ram:80ce0fbe` | TBD | `int(ReconnectData* out)` | Reads + validates reconnect file 0x0B |
| `ReconnectRedirect_Func` | `MissionClient::GameRedirectReconnect` | `ram:80ce22e5` | TBD | `int(Context* ctx)` | Bypasses auth server → GameJoin |
| `ReconnectValidate_Func` | `MissionClient::GameRedirectReconnectValidate` | `ram:80ce2665` | TBD | `uint(Guid const&)` | GUID match check |
| `EnterWorld_Func` | `MissionCliOnEnterWorld` | `ram:80ca093e` | TBD | `int(packet, dispatchParam)` | Arrival gate — sole caller of GameEnterWorld |
| `MapData_Func` | `MissionCliOnMapData` | `ram:80ca22df` | TBD | `int(packet, dispatchParam)` | Sets metadata + observer flag |
| `IsDeveloper_Func` | `MissionCliIsDeveloper` | `ram:80c98884` | TBD | `uint()` | Dev flag check: `(ctx[0x2a8]>>2)&1` |
| `AccessRights_Func` | `MissionCliOnAccessRights` | `ram:80c9bb66` | TBD | `int(packet, dispatchParam)` | Sets dev/GM/connected flags |
| `ObserveGame_Func` | `MissionCliObserveGame` | `ram:80c9a52f` | TBD | `void(uint game_id)` | Observer join entry |
| `SendObserveGame_Func` | `MissionClient::MsgSendObserveGame` | `ram:80ce803e` | TBD | `void(uint game_id)` | Sends 0x8E packet (8 bytes) |
| `ReadyToPlay_Func` | `MissionClient::MsgSendReadyToPlay` | `ram:80ce82ce` | **`0x0084cf80`** | `void()` | Sends 0x90 ready packet |
| `QueueReady_Func` | `MissionClient::GameQueueReadyToPlay` | `ram:80cdee52` | **`0x0084b650`** | `void()` | Sets `DAT_ram_005a404c = 1` |
| `TravelLogin_Func` | `PartyClient::MsgSendTravelMissionLogin` | `ram:80d54cab` | TBD | `void(int param)` | Sends 0xB2 packet (8 bytes) |
| `TravelMission_Func` | `PartyClient::MsgSendTravelMission` | `ram:80d54af5` | TBD | `void(EMission, ETerritory, uint, ELanguage, int)` | Sends 0xB1 packet |
| `RedirectMission_Func` | `MissionCliGameRedirectMission` | `ram:80c9990c` | `0x00847dd0` | `void(uint gameType, EMission, ETerritory, uint district, ELanguage)` | Travel entry point — bypasses all UI checks |
| `ConstMissionData_Func` | `ConstGetMissionClientData` | `ram:818b39ef` | `0x005a6b00` | `MissionClientData*(EMission)` | Mission database lookup (882 entries × 0x7C) |
| **NEW** `OnDownloadComplete` | `MissionClient::OnDownloadComplete` | `ram:80ce4f78` | **`0x0084cc60`** | `void()` | 2-state machine; calls MsgSendAckAggregate → sends 0x88 |
| **NEW** `AckAggregate` | `MissionClient::MsgSendAckAggregate` | `ram:80ce781e` | **`0x0084cdb0`** | `void()` | Sends 0x88 INSTANCE_LOAD_REQUEST_SPAWN (4 bytes) |
| **NEW** `PlayerLoadMap` | `MissionClient::PlayerLoadMap` | `ram:80ceea7b` | **`0x0084e290`** | `void(ctx, map_id, MapPoint*, angle, param5, param6)` | 4-path decision tree (A/B/C/D) |
| **NEW** `CheckLoginInit` | `MissionClient::PlayerCheckLoginInit` | `ram:80cee800` | **`0x0084e210`** | `void(ctx)` | Guard `(0x190&0xC0)==0xC0`; sends 0x89 or 0x91 |
| **NEW** `OnNetMsg` | `MissionClient::OnNetMsg` | `ram:80cdef95` | **`0x0084ba40`** | `void(eventHdr, param)` | Dispatches 0x1D/0x1E/0x1F/0xD6/0xD7/0xD8 |
| **NEW** `OnLoadMap` | `MissionCliOnLoadMap` | `ram:80ca1b5b` | **`0x00849400`** | `int(packet, dispatchParam)` | Handles 0x0196-0x0198; calls PlayerLoadMap |
| **NEW** `LoadSpawnHandler` | (unnamed FUN_008493c0) | — | **`0x008493C0`** | `int(packet, dispatchParam)` | Handles 0x0195 InstanceLoadFile (spawn point) |
| **NEW** `FailedToLoad` | `MissionClient::MsgSendFailedToLoad` | `ram:80ce7e62` | **`0x0084cea0`** | `void()` | Sends 0x8C (4 bytes) |
| **NEW** `AckCreationBegin` | `MissionClient::MsgSendAckCreationDataBegin` | `ram:80ce7a25` | **`0x0084cde0`** | `void()` | Sends 0x89 (4 bytes) |
| **NEW** `RequestLanguage` | `MissionClient::MsgSendRequestLanguage` | `ram:80ce8546` | **`0x0084cfd0`** | `void(ELanguage, ELanguage)` | Sends 0x91 (12 bytes) |
| **NEW** `GameIsPlayingAd` | `MissionClient::GameIsPlayingAd` | `ram:80cdee41` | **`0x0084b4e0`** | `uint()` | Returns ready gate global |
| **NEW** `MapInitStart` | `CharCliOnMapInitStart` | `ram:80c1c9e2` | **`0x00811b10`** | `void(Coord2u const&, uint)` | Allocates compressed map buffer |
| **NEW** `MapInit` | `CharCliOnMapInit` | `ram:80c1bd0e` | **`0x0080c250`** | `void(uint, void const*)` | Accumulates map chunks → DecompressMap |
| **NEW** `EventGameLoadMission` | `EventCliContextOnGameLoadMission` | — | **`0x00626010`** | `void(mission)` | ⚠️ Asserts if TLS+0x0C NULL — GameJoin crash point |
| **NEW** `GuildGetSequence` | `GuildCliGetSequence` | — | **`0x0083a5b0`** | `uint()` | TLS+0x3C→+0x2A4 double deref |
| **NEW** `PrefetchMark` | `CPrefetchCache::Mark` | `ram:80ce43a0` | **`0x0084cba0`** | — | Mark mission in prefetch cache |
| **NEW** `PrefetchExport` | `CPrefetchCache::Export` | `ram:80ce2c94` | **`0x0084c2a0`** | — | Export prefetch cache |
| **NEW** `ObserveSend` | `MissionClient::MsgSendObserveGame` | `ram:80ce803e` | **`0x0084cf20`** | `void(uint game_id)` | Sends 0x8E (8 bytes) |
| **NEW** `ObserveGetList` | `MissionClient::MsgSendObserveGetList` | `ram:80ce8191` | **`0x0084cf50`** | `void()` | Sends 0x8F (4 bytes) |
| **NEW** `CliObserveGame` | `MissionCliObserveGame` | `ram:80c9a52f` | **`0x008486e0`** | `void(uint game_id)` | UI handler → Find → MsgSendObserveGame |
| **NEW** `GameFrameProc` | `IUi::GameFrameProc` | `ram:80fbce63` | **`0x004a62c0`** | — | Handler for kLoadMapContext (0x10000098) |
| **NEW** `MapLoader` | (unnamed) | — | **`0x00702c20`** | `int(wchar_t* path, 0, 0, 0)` | Gatekeeper — loads map from path |

### Verified Context Flags

#### Offset 0x400 (Game State)

| Mask | Name | Set By | Cleared By |
|------|------|--------|------------|
| 0x01 | LOADED_ONCE | `PlayerCheckLoginInit` | `Context::Reset` |
| 0x02 | LEAVING | `GameLeave` | `Context::Reset` |
| 0x08 | ENTERED_WORLD | `GameEnterWorld` | `Context::Reset` |
| 0x10 | REDIRECT_RECEIVED | `MissionCliOnRedirect` | `Context::Reset` |
| 0x20 | JOINING | `GameJoin` | `Context::Reset` |
| 0x40 | LOGIN_INIT_REQUIRED | `OnNetMsg` (0x1E, 0x1F) | — |
| 0x80 | MAP_DATA_RCVD | `MissionCliOnMapData` | `Context::Reset` |
| 0x200 | REDIRECTING | `GameRedirectMission` | `Context::Reset` |

#### Offset 0x2A8 (Privilege Flags)

| Bit | Mask | Name | Check Function | Set By |
|-----|------|------|---------------|--------|
| 0 | 0x01 | BASE_FLAG | — | `MissionCliOnAccessRights` |
| 1 | 0x02 | CONNECTED | `MissionCliIsConnected()` | `MissionCliOnAccessRights` |
| 2 | 0x04 | DEVELOPER | `MissionCliIsDeveloper()` | `MissionCliOnAccessRights` |
| 3 | 0x08 | GAME_MASTER | `MissionCliIsGameMaster()` | `MissionCliOnAccessRights` |
| 4 | 0x10 | OBSERVER | `MissionCliIsObserver()` | `MissionCliOnMapData` (packet[0x18]) |

### Map Arrival Pipeline (20 Stages)

All 20 stages confirmed in WASM as of 2026-06-12. See `docs/RE/map_travel_reverse_engineering.md` §12 for full table.

The pipeline proceeds: **Travel Dispatch** → **Auth Redirect** → **Game Join** → **Map Loading** → **Map Data + Init** → **Arrival Gate** → **Enter World**. `MissionCliOnEnterWorld` (`ram:80ca093e`) still uses `ctx[0x238]` and observer bit `0x10` as fast-path conditions, but fresh 2026-06-14 decompilation shows they are not a complete hard gate: if neither is set, the function can still proceed through `MissionClient::ManifestStartPrefetch(...)` and then `GameEnterWorld(...)`. The reconnect path (file 0x0B) bypasses auth server entirely, calling `GameJoin()` directly.

### The 7 Travel Paths

1. **Path A (Normal)**: `IUi::MapSelect → PartyCliTravelMission → GameRedirectMission → OnRedirect → GameJoin` — full validation
2. **Path B (Observer-Bypass)**: Same as A but skips `PartyCliTravelMission` and territory/party checks when `MissionCliIsObserver()` is true
3. **Path C (Observer-Alt)**: `MissionCliObserveGame → MsgSendObserveGame(0x8E) → Server 0x1D → OnNetMsg → GameJoin` — skips auth server
4. **Path D (Reconnect)**: `CompleteLogin → GameRedirectReconnect → ReadReconnectData(0x0B) → GameJoin` — bypasses auth server entirely
5. **Path E (Travel-on-Login)**: `PartyCliTravelMissionLogin → MsgSendTravelMissionLogin → [0xB2 | param]`
6. **Path F (Sentinel)**: `IUi::MapSelect type=2 → GameRedirectMission(1, 0, 0xFFFFFFFD, 0, 0xFFFFFFFF)` — error recovery
7. **Path G (GM Teleport)**: `Ctrl+Shift+T → CharCliPlayerOrderTeleport` — within-map only, gated on `MissionCliIsGameMaster()`

Implementation in `MapMgr.cpp` with toggles exposed via `GW::Map::SetBlockTravelBack`, `SetBlockReadyToPlay`, `SetBlockRedirectToTarget`, and the newer rollback-rewrite instrumentation. Test UI in `GodTools.py`.

Current resume point (2026-06-14, authoritative handover):

- The project is no longer in the "find the rollback origin" phase. That question is answered.
- The loaded DLL can now be identified from in-game output. `travel_back_debug` prints:
  - `build_id`
  - `build_compiled_at`
  - `build_cookie`
- Current known-good fingerprint:
  - `build_id=travel-re-2026-06-14-build-fingerprint-v1`
  - `build_cookie=0x26061401`
- The project now uses shared native redirect logs exposed through `Py4GW_UI` and printed by `GodTools.py`.
- The real native retry harness binding names are on `Py4GW.UI.UI`, not `PyUIManager.UIManager`:
  - `map_test_start`
  - `map_test_stop`
  - `get_map_test_status`
  - `is_map_test_active`
  - `get_map_test_count`

Authoritative probe matrix:

- `_draw_debug_window()` exposes exactly three scenario buttons, all pointed at target map `81`:
  - `Owned Normal (81)`
  - `Owned Observer (81)`
  - `Unowned Observer (81)`
- The probe emits its own classification; treat this metadata as the source of truth:
  - `owned_normal`
  - `owned_observer`
  - `unowned_observer`
- `unowned_observer` is the only scenario that triggers the fallback rollback machinery.

Confirmed scenario outcomes:

- `owned_normal`
  - reaches `81`
  - uses the normal redirect path
  - shows `OnRedirect` / `TRANSFER_GAME_SERVER_INFO (0x01A5)`
- `owned_observer`
  - reaches `81`
  - no rollback redirect/error hook hit
  - shortest path of the three
- `unowned_observer`
  - starts in observer
  - target unlocked state is false
  - hits `INSTANCE_REDIRECT (0x0191)`
  - enters `MissionCliOnErrorRedirect`
  - ends on fallback mission `249`

Confirmed fallback tuple for the locked-map case:

- Helper VA rebasing is valid against the live `Gw.exe` base:
  - `ConstGetMissionClientData` VA `0x005A6B00`
  - redirect selector VA `0x00921ED0`
- For the `unowned_observer` rollback:
  - server supplies `mission 249`
  - `ConstGetMissionClientData(249)` resolves mission entry `0x01330234`
  - `game_type = 0x0A`
  - selector input bool = `0`
  - selector output = `3`
- Resulting measured call:
  - `GameRedirectMission(3, 249, 0xFFFFFFFD, 0, 0xFFFFFFFF)`

Confirmed caller chain:

- Caller-site logging now records:
  - `caller_label`
  - `caller_va`
  - `caller_return_address`
- The active range-based classifier is working and confirmed by the fingerprinted DLL.
- Forward travel seed:
  - `game_redirect_mission`
  - caller `MissionCliGameRedirectMission`
  - `caller_va = 0x00847DF0`
- Fallback rollback application:
  - `game_redirect_mission`
  - caller `MissionCliOnErrorRedirect`
  - `caller_va = 0x008492B4`
- Outbound auth send beneath each redirect:
  - `net_game_redirect`
  - caller `GameRedirectMission`
  - `caller_va = 0x0084B827`
- Conclusion:
  - the rollback is applied directly in the `MissionCliOnErrorRedirect -> GameRedirectMission` chain
  - it is not coming from a later replay, reconnect, or deferred continuation path

Confirmed arrival timeline for `unowned_observer`:

- first load starts toward mission `81`
- `pkt_instance_redirect (0x0191)` arrives before `READY_FOR_MAP_SPAWN`
- arrival logs show, in order:
  - `redirect_before_spawn_auth`
  - `pre_spawn_error_redirect_call`
  - `pre_spawn_game_redirect_call`
  - `pre_spawn_net_redirect_applied`
  - `pre_spawn_game_redirect_applied`
  - `pre_spawn_error_redirect_result`
- after that pivot, the load completes successfully into `249`
- terminal result from the latest fingerprinted run:
  - `end_map=249`
  - `outcome=entered_world`
  - `terminal=entered_world`

Important negative conclusions:

- Do not spend more time trying to prove where the rollback originates. That is solved.
- Do not use stale widget labels such as `Plain Probe`, `Owned Probe`, or `Rewrite EXP` as the assumed active surface. The authoritative surface is the three-button `81` matrix described above.
- Do not assume `OnErrorRedirect` uses the normal `OnRedirect` packet family. Packet preview proves it belongs to the `INSTANCE_REDIRECT (0x0191)` family.
- Do not assume the rollback comes from `GameRedirectReplay`, `Reconnect`, or a later `OnRedirect` branch unless new evidence contradicts the caller log.

Latest runtime refinement (2026-06-14, target `81`, native handoff probes):

- The newest failing probe was:
  - `label=native_handoff_ready_probe`
  - `scenario=unowned_observer`
  - `trigger=map_data_received`
  - `action=set_ready_gate_only`
  - `join_after_ready=False`
  - `outcome=timeout`
- The important result is not "ready gate caused the kick" by itself.
- The important result is that after the trigger, the load never reaches the normal spawn-authorization path.

Observed post-trigger progression:

```text
map_data_received
  -> pkt_instance_redirect
  -> redirect_before_spawn_auth
  -> pre_spawn_error_redirect_call
  -> pre_spawn_error_redirect_result
  -> map_state_set
```

Confirmed absent after the trigger:

- `TRANSFER_GAME_SERVER_INFO (0x01A5)`
- `READY_FOR_MAP_SPAWN (0x01AB)`
- `INSTANCE_LOADED`
- `map_loaded`
- `entered_world`

Key runtime evidence:

- `redirect_before_spawn_auth`
  - `detail=load_info_without_ready_for_spawn`
- `travel_post_trigger`
  - `post_unique=map_data_received,pkt_instance_redirect,redirect_before_spawn_auth,pre_spawn_error_redirect_call,pre_spawn_error_redirect_result,map_state_set`
  - `xfer=False`
  - `ready_spawn=False`
  - `instance_loaded=False`
  - `map_loaded=False`
  - `entered_world=False`

Current interpretation:

- `MissionCliOnErrorRedirect` is still a symptom point after the real divergence.
- The newer handoff probes do **not** prove a single bad field write or bad signature by themselves.
- They prove that the probe path never recreates the missing handover steps needed to reach
  `READY_FOR_MAP_SPAWN` and the later spawn/map-init pipeline.
- The active RE boundary is therefore:
  - after `MissionCliOnMapData`
  - before `READY_FOR_MAP_SPAWN`
  - at the branch that chooses `INSTANCE_REDIRECT (0x0191)` instead of normal spawn authorization

What remains unresolved (2026-06-14 update — many items now resolved):

- ✅ ~~Why the `unowned_observer` path receives `INSTANCE_REDIRECT (0x0191)` before the load reaches `READY_FOR_MAP_SPAWN`.~~ **RESOLVED**: Server replaces entire spawn chain (0x01AB→0x0195→0x0196→0x0197→0x0198) with single 0x0191. Decision is server-side based on TCP-authenticated map ownership.
- ✅ ~~Whether `0x0088 INSTANCE_LOAD_REQUEST_SPAWN` is actually sent on unowned observer.~~ **CONFIRMED**: 0x88 IS sent via `OnDownloadComplete` (0x0084cc60) → `MsgSendAckAggregate` (0x0084cdb0). Server receives it, then decides 0xD6 vs 0x0191.
- 🟡 G8: What happens if we send `0x0090 INSTANCE_LOAD_REQUEST_PLAYERS` directly (without the full LoadMap pipeline)? Python wrapper implemented at `MapTravelBypassMethods.py` — ready to test.
- 🟡 G9: Why does calling `GameJoin` directly crash? **DIAGNOSED**: Precondition violation — stable map state vs loading transition state. Crash point #1: `EventCliContextOnGameLoadMission` (0x00626010) asserts TLS+0x0C != NULL. Fix option B (use MsgSendObserveGame protocol) needs EXE address resolution.
- ⬜ G2: Identity of `kLoadMapContext` (0x10000098) handler.
- ⬜ G4: `OnMapData` EXE address (dispatched through IMsgChannel, not OnNetMsg).
- ⬜ G10: Whether setting observer flag (ctx[0x2A8] |= 0x10) before 0x88 is sent changes server response from 0x0191 to 0xD6.

High-value next RE work for another agent (2026-06-14 updated):

1. ~~Treat `MissionCliOnErrorRedirect` as a confirmed symptom point, not the primary pivot.~~ ✅ DONE
2. ~~Compare the successful `owned_observer` handover window against `unowned_observer`~~ ✅ DONE — diverges at server response to 0x88
3. ~~Focus on `MissionCliOnLoadMap`, `OnMapData`, `PlayerLoadMap`, deferred ready consumer in `OnNetMsg`~~ ✅ DONE — all decompiled, EXE addresses found
4. 🟡 **G8**: Test `MsgSendReadyToPlay` directly during unowned observer loading. Python wrapper ready.
5. 🟡 **G9**: Resolve `MsgSendObserveGame` EXE address (WASM: `ram:80ce803e`) to test observer protocol bypass.
6. 🟡 **G2**: Find `kLoadMapContext` (0x10000098) handler — use `FrameMsgSendRegistered` xrefs filtered to that constant.
7. 🟡 **G4**: Find `OnMapData` EXE address — dispatched through IMsgChannel handler table, not OnNetMsg. Search for the MAP_DATA message ID registration.

Minimal reproducible evidence set to hand to the next agent:

- fingerprinted DLL output showing:
  - `build_id=travel-re-2026-06-14-build-fingerprint-v1`
  - `build_cookie=0x26061401`
- `travel_probe_result` for `unowned_observer` ending on `249`
- redirect log entries showing:
  - `MissionCliGameRedirectMission @ 0x00847DF0`
  - `MissionCliOnErrorRedirect @ 0x008492B4`
  - `GameRedirectMission -> NetGameClientGameRedirect @ 0x0084B827`
- arrival log entries around:
  - `pkt_instance_redirect`
  - `pre_spawn_error_redirect_call`
  - `pre_spawn_game_redirect_call`
  - `pre_spawn_game_redirect_applied`
  - `entered_world`

---

## 17. Chat Command Dispatch Architecture (2026-06-12)

`CChatFrame::SendMessage()` at `ram:8123d44f` implements a 3-tier chat command dispatch. Only 16 client-side commands exist — all other commands (`.s`, `.map`, `.who`, `.die`, `.gm`, `.dev`, `.guildhall`, `.ip`, etc.) are sent to the server as raw chat text and processed server-side.

### Dispatch Flow

```
CChatFrame::SendMessage()
  ├─ 1. GmProcessMessage()     — 3 GM commands (requires IS_GM flag)
  │     .examine → sends UIMsg 0x1000019c to server
  │     .togglexamine → toggles DAT_005aa62c ^= 8
  │     .chatDump → ChatLogWriteShot()
  ├─ 2. LocalProcessMessage()  — 13 help/wiki commands (no privilege)
  │     wiki, report, help (×10 language variants)
  └─ 3. CommCliSendText()      — EVERYTHING ELSE → sent to SERVER
```

### Tier 1 — GM Commands (GmProcessMessage @ ram:8123817b)

Requires `MissionCliIsGameMaster()` — `(ctx[0x2a8] >> 3) & 1`. Only 3 commands:

| Command | Action |
|---------|--------|
| `.examine` | Sends UI message `0x1000019c` to server for agent examine |
| `.togglexamine` | Toggles `DAT_ram_005aa62c ^= 8` (debug examine overlay) |
| `.chatDump` | Calls `ChatLogWriteShot()` — dumps chat log snapshot |

**Key finding**: ZERO travel commands exist client-side in GmProcessMessage. The `.s` travel command, `.gm`, `.dev`, and all other dev commands are NOT here.

### Tier 2 — Local Commands (LocalProcessMessage @ ram:812386bd)

No privilege required — 13 help/wiki commands:

| Command | Action |
|---------|--------|
| `wiki` | Opens guild wars wiki |
| `report` | Opens report dialog |
| `help` (×10 languages) | Shows help article for each supported language |

### Tier 3 — Server Commands (CommCliSendText @ ram:80b0950e)

**Everything else** — all dev commands — fall through here. The raw chat text (including `.s 123`, `.map`, `.who`, `.die`, `.gm`, `.dev`, `.guildhall`, `.ip`, `.dp`, `.event`, `.m`, `.mark`, `.monitor`, `.partysize`, `.time`, `.w`) is sent verbatim to the server via `CommCliSendText()`. The server checks privilege flags and processes the command.

**Dev/GM flag setting**: The server sets developer/GM flags via `MissionCliOnAccessRights` (`ram:80c9bb66`):
- Reads server packet[4]
- Packet bit 1 → `ctx[0x2a8]` bit 2 (DEVELOPER)
- Packet bit 2 → `ctx[0x2a8]` bit 3 (GAME_MASTER)

### WASM String Search Result

Searched WASM string table for all ~20 known dev/GM command prefixes (`.gm`, `.dev`, `.s`, `.die`, `.who`, `.map`, `.guildhall`, `.fireworks`, `.guildtrim`, `.joinguild`, `.mute`, `.unmute`, `.write`, `.dp`, `.event`, `.ip`, `.m`, `.mark`, `.monitor`, `.partysize`, `.time`, `.w`). **ZERO matches found.** Confirms no client-side handlers exist for these commands.

---

## 18. Direct Travel Bypass (2026-06-12)

The travel system can be called directly from injected code via `MissionCliGameRedirectMission`, bypassing ALL world-map UI checks. This is the simplest travel entry point discovered so far.

### Callable Entry Point

**`MissionCliGameRedirectMission` @ `0x00847dd0`** (WASM: `ram:80c9990c`)
- **5 parameters**: `(uint gameType, EMission mission, ETerritory territory, uint district, ELanguage language)`
- **Self-contained**: fetches context internally via `PropGet(0x11)` — no context pointer needed
- **Minimal checks**: only `gameType <= 0x10` (warning, non-blocking). NO territory check, NO party check, NO mission_locked check, NO tag_flags check
- **What it does**: sets `ctx[0x400] |= 0x200` (REDIRECTING), stores params in context at `0x1FC–0x220`, calls `GameRedirectMission → NetGameClientGameRedirect`

### Call Chain

```
MissionCliGameRedirectMission(gameType, EMission, ETerritory, district, ELanguage)
  → GameRedirectMission(context, ...) @ 0x0084b770
    → MemZero(context+0x1FC, 0x2C)        # clear previous redirect state
    → Stores params at ctx[0x1FC–0x220]    # redirect_map_id, redirect_mission, etc.
    → ctx[0x400] |= 0x200                   # REDIRECTING flag
    → NetGameClientGameRedirect() @ 0x0048e970  # sends 0x25/0x29 to auth server
```

### Checks BYPASSED vs Normal World-Map Path

| Check | Normal Path | Direct Call |
|-------|------------|-------------|
| `MapGetMissionTagFlags & 1` (tag_flags) | ✅ Enforced | ❌ SKIPPED |
| `target_data[0x12] & 1` (mission_locked) | ✅ Enforced | ❌ SKIPPED |
| `GmTerritoryCanTravel` (territory validation) | ✅ Enforced | ❌ SKIPPED |
| Party leader consent (`PartyCliTravelMission`) | ✅ Enforced | ❌ SKIPPED |
| `MissionCliIsConnected()` | ✅ Enforced | ❌ SKIPPED |
| `MissionCliIsCreatingCharacter()` | ✅ Enforced | ❌ SKIPPED |
| Game type validation (`0x64004` mask) | ✅ Full | 🟡 Minimal (gameType ≤ 0x10 only) |
| Auth server redirect (`NetGameClientGameRedirect`) | ✅ | ✅ SAME |

### Simplest Call — Sentinel Territory Path

```python
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction

Travel = NativeFunction.from_address(
    name="MissionCliGameRedirectMission",
    address=0x00847dd0,
    prototype=Prototypes["Void_U32_U32_U32_U32_U32"],  # 5x uint32 params
)

# Simplest test — sentinel territory fallback:
Travel(1, 0, 0xFFFFFFFD, 0, 0xFFFFFFFF)
# gameType=1, EMission=0, ETerritory=sentinel, district=0, ELanguage=any
```

This is exactly what `IUi::MapSelect` does as a type-2 fallback. Territory `0xFFFFFFFD` tells `NetGameClientGameRedirect` to use the currently cached territory.

### Territory → Region Mapping

| Territory | Region | Guild Hall? |
|-----------|--------|-------------|
| 0–4 | 0 (interchangeable) | Yes |
| 5 | 6 | No |
| 6 | 7 | No |

Territories 0–4 are interchangeable within region 0. `GmTerritoryCanTravel` only allows travel within same region (verified in the normal path, skipped in direct call).

### GameType

`gameType` ≤ 0x10 is the only enforced bound. Values come from `ConstGetMissionClientData(EMission)` which returns a `MissionClientData*` (0x7C bytes per entry, 882 total entries) with `game_type` at offset `+0x0C`.

### Warning: Server-Side Validation Still Applies

The direct call bypasses ALL client-side checks, but the **server still validates the redirect**. If the server rejects the map/territory combination, it will send `MissionCliOnErrorRedirect` which triggers a rollback to the fallback territory. The most reliable approach is to combine this direct call with the existing cancel-race `MapTest` harness (`map_test_*` on `Py4GW.UI.UI`).

### Bridging Method

These EXE addresses were found via **string anchoring** from WASM assertion strings:
- `"RedirectMission: %d %08x"` → `FUN_0084b770` (GameRedirectMission) @ `0x0084b770`
- `"gameType < GAME_TYPES"` → same function, confirms identity
- Caller of `FUN_0084b770` → `FUN_00847dd0` (MissionCliGameRedirectMission) @ `0x00847dd0`
- `"index < arrsize(s_missionClientData)"` → `FUN_005a6b00` (ConstGetMissionClientData) @ `0x005a6b00`

### Why NOT Other Functions

- **`GameJoin` @ `0x00828040` (05-30) / `0x0084b4f0` (06-14)**: blocked by `MapIsCreated()` — can't call while in a map? Actually, Observer Join Bypass project is actively testing calling GameJoin directly with observer flag (param_8/param9=1). **Currently crashes the client on 06-14** — cause unknown. Requires 24-byte NetAddress from context+0x1A0. Requires security_token. 9 params in 06-14 (was 8 in 05-30).
- **`PartyCliTravelMission`**: sends packet 0xB1 through PARTY system — requires party leader consent, server-coordinated. NOT solo travel.
- **`GameRedirectMission` @ `0x0084b770`**: requires context pointer as first parameter — harder to call from Python.

---

## 18. Observer Join Bypass — Archived Direction (2026-06-14)

### Goal
This project direction attempted to bypass the unowned rollback by forcing `GameJoin()` with observer semantics during the loading window.

### EXE Build History

| Build | GameJoin Address | Params | Notes |
|-------|-----------------|--------|-------|
| **05-30-2026** | `0x00828040` | 8 (guild_seq computed internally) | Observer flag at [EBP+0x24] = typedef extra1. Pattern `83 8F 90 01 00 00 20` (OR [EDI+0x190]). **Pattern never found in user's EXE — Ghidra vs running EXE mismatch.** |
| **06-14-2026** | **`0x0084b4f0`** | 9 (observer flag at [EBP+0x24] = param_8, stored to context+0x1C4) | Pattern `83 8B 90 01 00 00 20` mask=`xxx??xx` (OR [EBX+0x190]). **Unique match verified in Ghidra.** |

### Implementation (MapMgr.cpp)

**`ObserverJoinTarget(map_id, mission, mission_map)`:**
1. Gets context via `PropGet(0x11) → +0x44`
2. Validates `GameJoin_Hook_Ret` is non-null
3. Copies net_address (24 bytes) from context+0x1A0
4. **06-14-2026**: Validates net_address is not all zeros (should prevent crash)
5. Calls `GameJoin_Hook_Ret(ctx, map_id, mission, mission_map, net_address, 0, 0, 1, 0)` — observer flag=1 at typedef extra1 position

**Scanner Pattern (06-14):**
```cpp
Scanner::Find("\x83\x8B\x90\x01\x00\x00\x20", "xxx??xx", 0); // OR [EBX+0x190], 0x20
→ Scanner::ToFunctionStart(address) → 0x0084b4f0
```
Unique match. Wildcards the null displacement bytes. Pattern exists in user's 06-14 EXE (verified via Ghidra direct search on `/Gw.exe (06-14)`).

**Python Interface (Py4GW_UI.cpp bindings):**
- `observer_join(map_id, mission, mission_map)` → bool
- `get_observer_join_status()` → ObserverJoinResult struct
- `get_observer_join_logs()` / `clear_observer_join_logs()`

**GodTools UI:**
- "Observer Join Bypass" section with Target Map, Mission, MissionMap inputs
- "Observer Join (TARGET)" and "Observer Join (81)" buttons
- Inline status display, log drain every frame

### Why This Direction Was Archived (2026-06-14)

The original flaw was real: calling `GameJoin` from a stable in-world state is invalid. Travel must already be in progress.

That corrected the timing model, but the newer packet/log evidence invalidated the main idea anyway.

Authoritative reasons this direction is now archived:

1. The failing path diverges before spawn authorization completes.
2. `INSTANCE_REDIRECT (0x0191)` lands immediately after `map_data_received`.
3. The failing path never emits:
   - server-side `READY_FOR_MAP_SPAWN`
   - `0x0090 INSTANCE_LOAD_REQUEST_PLAYERS`
4. Consuming or replacing `MissionCliOnErrorRedirect` does not restore the missing handover progression.
5. The practical result is a frozen load followed by disconnect, not a recovered join.

### Current Status

What still stands from this work:
- Scanner pattern resolves GameJoin at `0x0084b4f0` in 06-14 EXE ✓
- CreateHook installs hook and creates trampoline ✓
- Context/PropGet/net_address all valid ✓
- Normal travel initiation works (ctos_00C1 sends correctly) ✓
- `OnErrorRedirect` hook still fires during unowned travel ✓

What no longer stands:
- `OnErrorRedirect` is not the right place to recover the load.
- Replacing the fallback redirect with `GameJoin(target, observer=1)` is not a justified next step.
- The active problem is earlier than that hook.

### Active Follow-Up Instead
1. Use the owned/unowned observer trace diff as the primary evidence set.
2. RE the handover path from `MissionCliOnLoadMap` through `PlayerLoadMap` and the early post-map-data window.
3. Find the gate that determines whether the client proceeds to:
   - `READY_FOR_MAP_SPAWN`
   - `INSTANCE_LOAD_REQUEST_SPAWN`
   - `INSTANCE_LOAD_REQUEST_PLAYERS`
   or is instead pushed straight into `INSTANCE_REDIRECT (0x0191)`.

### 2026-06-14 Static RE Progress

The mission-side setup slice is now materially clearer:

- `MissionCliOnLoadMap` (`ram:80ca1b5b`)
  - copies the incoming spawn/time payload
  - computes the time delta
  - calls `MissionClient::PlayerLoadMap(...)`
- `MissionClient::PlayerLoadMap` (`ram:80ceeb00`)
  - resolves the map file path
  - posts frame message `0x10000098`
  - either sends `MsgSendReadyToPlay()` (`0x0090`) / queues it, or sends `MsgSendFailedToLoad()` (`0x008C`) on local failure
- `MissionCliOnMapData` (`ram:80ca22df`)
  - seeds `ctx+0x228/0x22c/0x230/0x238/0x2ac`
  - mirrors `0x230 -> 0x234` and `0x238 -> 0x23c` when packet[0x18] is zero
  - otherwise sets observer bit `ctx[0x2a8] |= 0x10`
  - sets `ctx[0x190] |= 0x80`
  - calls `MissionClient::PlayerCheckLoginInit(context)`
- `MissionClient::PlayerCheckLoginInit` (`ram:80cee800`)
  - returns unless `(ctx[0x190] & 0xC0) == 0xC0`
  - sends `0x0089` when creation-data mode is active
  - otherwise sends the language request packet that matches the observed `0x0091`

What this proves:

- `0x0088 INSTANCE_LOAD_REQUEST_SPAWN` is not generated inside:
  - `MissionCliOnLoadMap`
  - `MissionCliOnMapData`
  - `MissionClient::PlayerCheckLoginInit`
- So the unresolved divergence is now best described as the mission-to-char handoff boundary, not a missing branch inside those mission handlers.

The first downstream char/map handlers already pinned are:

- `CharCliOnMapInitStart_Coord2u_const___unsigned_int_` (`ram:80c1c9e2`)
  - stores the initial map bounds / size state
  - reallocates the compressed map buffer if needed
- `CharCliOnMapInit_unsigned_int__unsigned_long_const__` (`ram:80c1bd0e`)
  - copies compressed map chunks into the destination buffer
  - triggers `DecompressMap__()` when the full payload arrives

This does not yet name the exact caller that emits `0x0088`, but it does eliminate the earlier mission dispatch slice as the source.

### Project Files
- `.opencode/projects/re/map-travel-bypass/` — project pool, status, lock
- `Py4GW\vendor\gwca\Source\MapMgr.cpp` — ObserverJoinTarget implementation (lines 2222-2290)
- `Py4GW\vendor\gwca\Include\GWCA\Managers\MapMgr.h` — ObserverJoinResult/LogEntry structs (lines 383-404)
- `Py4GW\src\Py4GW_UI.cpp` — Python bindings (observer_join, get_observer_join_status, etc.)
- `Py4GW_python_files\GodTools.py` — UI section and log display
- `Py4GWCoreLib/native_src/methods/MapTravelBypassMethods.py` — Python-side G8 prototype; keep for reference only, not as the primary implementation home

### Key Globals

| Global | EXE Address | WASM Address | Purpose |
|--------|-------------|-------------|---------|
| Ready Gate | `0x0108195C` | `DAT_ram_005a4048` | Set by OnNetMsg 0xD6. Blocks direct MsgSendReadyToPlay in PlayerLoadMap Path C. |

### Integration Boundary Correction (2026-06-14)

Part of the travel/handover work was accidentally implemented primarily on the Python-native side. That has made the active experiment hard to follow because the authoritative behavior is now split across too many layers.

For this project, the intended ownership is:

- **C++ / GWCA is authoritative**
  - packet sends
  - hook installation
  - global-state manipulation
  - travel/handover toggles
  - structured debug counters and logs
- **`src/Py4GW_UI.cpp` is a thin export surface**
  - expose C++ controls to Python
  - do not recreate control logic here
- **`GodTools.py` is an operator UI / probe runner**
  - start tests
  - display counters, logs, packet summaries
  - no primary bypass logic
- **`Py4GWCoreLib/native_src` is not the right primary home for this handover work**
  - direct memory writes and packet-driving helpers there are difficult to audit
  - they duplicate logic that should remain centralized in `MapMgr.cpp`

Concrete implication:

- new work on travel bypass, spawn authorization, redirect suppression, ready gating, `0x0088` / `0x0090` experiments, or observer handoff should be integrated into:
  - `Py4GW\vendor\gwca\Source\MapMgr.cpp`
  - `Py4GW\vendor\gwca\Include\GWCA\Managers\MapMgr.h`
  - then exported upward through `Py4GW\src\Py4GW_UI.cpp`
- avoid expanding `Py4GWCoreLib/native_src/methods/MapTravelBypassMethods.py` beyond archival/prototype reference value

Working rule:

- if the feature changes client handover behavior or mutates native mission state, it belongs in C++ first
- Python should only trigger and observe that C++ path
| Queued Ready | `0x01081964` | `DAT_ram_005a404c` | Set by `GameQueueReadyToPlay()`. Consumed by OnNetMsg 0xD7/D8 for deferred send. |
