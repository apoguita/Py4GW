# Reverse Engineering Handover

Comprehensive library reference for Python↔C++↔Ghidra interface in the Py4GW project.
Read this first before any RE work. AGENTS.md points here for tool paths and mappings.

---

## 1. Three-Layer Architecture

| Layer | Location | Purpose | Interface |
|-------|----------|---------|-----------|
| **C++/GWCA** | `C:\Users\Apo\Py4GW\vendor\gwca\` | Original GWCA source, function discovery patterns | `Scanner::Find*`, hooks, structs |
| **Python/Native** | `Py4GWCoreLib\native_src\` | Python port of GWCA primitives | `NativeFunction`, `PlayerMethods`, `Scanner` |
| **Ghidra** | MCP bridge (2 programs loaded) | Static analysis of Gw.exe + Gw.wasm | `mcp__ghidra__*` tools over MCP |

### C++/GWCA Source Layout

```
C:\Users\Apo\Py4GW\vendor\gwca\
├── Source\               # Implementation files
│   ├── AgentMgr.cpp      # InteractAgent, MoveTo, ChangeTarget, CallTarget
│   ├── PlayerMgr.cpp     # Player operations
│   ├── UIMgr.cpp         # UI message dispatch
│   ├── ItemMgr.cpp       # Inventory/items
│   ├── GameThreadMgr.cpp # Enqueue/execution loop
│   └── ...
├── Include\GWCA\
│   ├── Managers\         # Public API headers
│   │   ├── AgentMgr.h    # WorldActionId, CallTargetType, Agent APIs
│   │   └── ...
│   ├── GameEntities\     # Struct definitions (Agent, NPC, Item, etc.)
│   ├── Constants\        # Enums (Allegiance, etc.)
│   └── Utilities\
│       └── Scanner.h     # Find, FindAssertion, ToFunctionStart, FunctionFromNearCall
```

### Python/Native Source Layout

```
Py4GWCoreLib\
├── native_src\
│   ├── methods\
│   │   ├── PlayerMethods.py   # InteractAgent, Move, ChangeTarget, SendChat
│   │   ├── MapMethods.py      # Travel, logout
│   │   └── DatFileMethods.py  # Character data
│   ├── internals\
│   │   ├── native_function.py # NativeFunction class (byte-pattern → callable)
│   │   ├── prototypes.py      # Function signatures (Void_U32, etc.)
│   │   ├── native_symbol.py   # Symbol resolution helpers
│   │   └── native_caller.py   # Dynamic call infrastructure
│   ├── context\               # Native context struct accessors
│   └── __init__.py
├── Scanner.py                 # Python-facing Scanner (FindAssertion, FindInRange)
├── Player.py                  # High-level Player wrapper
├── Agent.py                   # Agent wrapper
├── UIManager.py               # SendUIMessage, SendUIMessageRaw
└── enums_src\UI_enums.py      # UIMessage, WorldActionId equivalents
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

### CPP → EXE (finding a GWCA function in the stripped EXE)

```
GWCA: Scanner::FindAssertion("GmCoreAction.cpp", "action < WORLD_ACTIONS", 0, 0)
       → Scanner::ToFunctionStart(address)
       → EXE: FUN_0050e5e0
```

Manual: search string → get xref → walk to function start.

### WASM → EXE

Find a string in the WASM function → search same string in EXE → xref → function.

Example: `"CommandMoveToPoint (agent %d, point %f, %f): Hero not activated"` in `CharClient::CHeroMgr::OnCommandMoveToPoint` → EXE `FUN_00817cf0`.

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

The authoritative enum is at `C:\Users\Apo\Py4GW\vendor\gwca\Include\GWCA\Managers\UIMgr.h:294` (~120 entries). The Python port is at `Py4GWCoreLib\enums_src\UI_enums.py`.

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

1. **Python** ([PlayerMethods.py:87](file:///C:/Users/Apo/Py4GW_python_files/Py4GWCoreLib/native_src/methods/PlayerMethods.py:87)):
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

GWCA's `InteractAgent` at [AgentMgr.cpp:409](file:///C:/Users/Apo/Py4GW/vendor/gwca/Source/AgentMgr.cpp:409) uses the same `kSendWorldAction` approach. The Python code is a 1:1 port.

---

## 6. Workflow: Finding and Adding a New Function

### Step 1: Find it in GWCA C++ (or WASM)

```bash
# Search GWCA sources for the function name
grep -r "FunctionName" C:\Users\Apo\Py4GW\vendor\gwca\
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
| `CContainerFrame::FrameProc` | `0x00871b40` | (handover.md Section 10) |
| `DlgDevTextProc` | `0x0088a870` | String `"DlgDevText"` @ `0x00b9743c` |

### Implementation Reference

Python repo (`C:\Users\Apo\Py4GW_python_files\`):
- `Py4GWCoreLib/native_src/internals/prototypes.py` — added `U32_U32_U32_U32_U32_U32` and `U32_U32_U32_U32` prototypes
- `Py4GWCoreLib/native_src/methods/PlayerMethods.py` — added `CtlFrameListCreateItem_Func` and `FrameNewSubclass_Func` NativeFunctions
- `Py4GWCoreLib/GWUI.py` — complete rewrite (204 lines): `CreateScrollableContent`, `AddTextItem`, `CreateScrollableWindow`, `_encode_text_literal`, `_resolve_text_label_callback`
- `stubs/PyUIManager.pyi` — type stubs for 5 new C++ bindings
- `UI_RE/window_contents_test.py` — 249-line test widget

C++ repo (`C:\Users\Apo\Py4GW\`):
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
| `handover.md` | This file — library reference and interface guide |
| `CPP_WASM_MAPPING.md` | Full procedure for CPP↔WASM↔EXE translation |
| `gw_combat_ai_reverse_engineering.md` | Combat AI reverse engineering analysis |
| `native_gw_ui_function_catalog.json` | Catalog of native GW UI functions with addresses |
| `native_gw_window_creation_investigation.md` | Window creation/proc RE investigation |
| `native_ui_title_and_encoded_string_reference.md` | Native UI title and encoding reference |
| `rosetta_stone.txt` | GwA2 (AutoIt) to Py4GW function mapping |
| `title_rendering_research.md` | Title rendering investigation & working solution (11 approaches) |
| `ui_controls_catalog.md` | Complete UI controls catalog — 39 types, tiers, structs, addresses, Phase 3 crash documentation (2026-06-05) |
| `window_creation_architecture.md` | CContainerFrame window creation architecture reference |

Other project docs remain in `docs/`:
- `Py4GW_Conceptual_Model.md` — canonical architecture
- `widget_manager_and_catalog.md` — widget discovery metadata
- `MCP_bridge.md` — MCP bridge planning
- `ui_controls_catalog.md` — Complete UI controls catalog (39 types, 2026-06-05)
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
