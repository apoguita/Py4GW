# Map Travel — Reverse Engineering Research

EXE builds: 05-30-2026, 06-14-2026 | Scope: Travel-load handshake, owned vs unowned divergence, bypass surface

---

## 1. Packet-Level Comparison: Owned vs Unowned Observer Travel

Both tests from observer mode, target map 81. Same client packets. Different server responses.

### Client-to-Server (IDENTICAL in both scenarios)

| CToS | Packet | Size | Owned | Unowned |
|------|--------|------|:-----:|:-------:|
| `0x00C1` | Travel init | 12 | ✅ | ✅ |
| `0x0091` | INSTANCE_LOAD_REQUEST_ITEMS | 12 | ✅ | ✅ |
| `0x0088` | INSTANCE_LOAD_REQUEST_SPAWN | 4 | ✅ | ✅ |
| `0x0090` | INSTANCE_LOAD_REQUEST_PLAYERS | 20 | ✅ | ✅ |

### Server-to-Client — Owned (SUCCESS)

```
0x017C  INSTANCE_LOAD_HEAD
0x0186  (internal)
0x017D  (internal)
0x0199  INSTANCE_LOAD_INFO
0x0144  (internal)
0x0148  (internal)
...     ~180 agent/entity packets (0x0161, 0x013E, 0x013F, 0x013A, 0x015A)
0x0099  MAP_UPDATE_CURRENT
0x01AB  READY_FOR_MAP_SPAWN
0x0099  MAP_UPDATE_CURRENT
0x008E  INSTANCE_LOAD_FINISH
        → entered_world
```

### Server-to-Client — Unowned (REJECTED)

```
0x017C  INSTANCE_LOAD_HEAD
0x0199  INSTANCE_LOAD_INFO
        → map_data_received (ctx flags190|=0x80)
0x0191  INSTANCE_REDIRECT        ← replaces entire spawn chain
        → OnErrorRedirect → GameRedirectMission(fallback=249)
```

### What Never Arrives for Unowned

| Packet | Purpose | Present in Owned |
|--------|---------|:---:|
| `0x0099` | MAP_UPDATE_CURRENT | ✅ |
| `0x01AB` | READY_FOR_MAP_SPAWN | ✅ |
| `0x0195` | SPAWN_POINT | ✅ |
| `0x0196` | OnLoadMap | ✅ |
| `0x008E` | INSTANCE_LOAD_FINISH | ✅ |

---

## 2. Stage Progression Comparison

### Owned Observer — 16 stages → entered_world

```
game_join
joining_flag_set
pkt_instance_load_head
pkt_instance_load_info
map_data_received
pkt_map_update_current
ui_start_map_load
pkt_ready_for_map_spawn
pkt_spawn_point
ui_load_map_context
msg_send_ready_to_play
pkt_instance_loaded
pkt_map_update_current
ui_start_map_load
ui_map_loaded
entered_world
```

### Unowned Observer — 12 stages before redirect, then fallback cycle

```
game_join
joining_flag_set
pkt_instance_load_head
pkt_instance_load_info
map_data_received
pkt_instance_redirect             ← divergence
redirect_before_spawn_auth
pre_spawn_error_redirect_call
pre_spawn_game_redirect_call
pre_spawn_net_redirect_applied
pre_spawn_game_redirect_applied
pre_spawn_error_redirect_result
  → [fallback cycle: game_join → ... → entered_world on map 249]
```

---

## 3. Divergence Analysis

### The server decides at the TCP session level

No outgoing packet carries forgeable ownership data. The client sends identical CToS packets for owned and unowned travel. The server uses the authenticated TCP session identity to decide: owned → spawn chain, unowned → `0x0191`.

### What triggers the check?

`OnDownloadComplete` @ `0x0084CC60` fires after map data finishes downloading → calls `MsgSendAckAggregate` @ `0x0084CDB0` → sends `{0x88}` (4 bytes). The server receives `0x88`, checks ownership against the session, and responds with either the spawn chain or `0x0191`.

The `0x88` packet is just `{0x88}` — no map ID, no player data, no flags. The decision is purely session-based.

### Timing

In the unowned test, `0x0191` arrived ~235ms after `map_data_received` (tick delta: 1987125046 → 1987125281).

---

## 4. Complete Function Catalog (06-14-2026 EXE)

### Travel Initiation

| Function | EXE | WASM | Notes |
|----------|-----|------|-------|
| `MissionCliGameRedirectMission` | `0x00847DD0` | `ram:80c9990c` | Bypasses all UI checks. 5 params: gameType, mission, territory, district, language |
| `GameRedirectMission` | `0x0084B770` | `ram:80ce1ad1` | Constructs auth redirect packet (0x25/0x29), sends via `NetGameClientGameRedirect` |
| `NetGameClientGameRedirect` | `0x0048E970` | `ram:80d0d2b3` | Sends auth redirect to server |
| `IUi::MapSelect` | TBD | `ram:80fc49cb` | World map click handler — full validation chain |
| `PartyCliTravelMission` | TBD | `ram:80d512c4` | Party-coordinated travel |

### Redirect / Join

| Function | EXE | WASM | Notes |
|----------|-----|------|-------|
| `MissionCliOnRedirect` | `0x00849990` | `ram:80ca3ac2` | Handles auth server redirect response |
| `MissionCliOnErrorRedirect` | `0x00849230` | `ram:80ca0d96` | Handles `0x0191` INSTANCE_REDIRECT. Packet[4] = fallback mission |
| `GameJoin` | `0x0084B4F0` | `ram:80ce01aa` | 8 params (EXE). Scanner: `\x83\x8B\x90\x01\x00\x00\x20` mask `xxx??xx` |
| `NetGameClientGameJoin` | `0x0048E8E0` | `ram:80d0d78a` | Connects to game server |

### Map Data / Load

| Function | EXE | WASM | Notes |
|----------|-----|------|-------|
| `OnDownloadComplete` | `0x0084CC60` | `ram:80ce4f78` | 2-state machine. Calls `MsgSendAckAggregate` → sends `0x88` |
| `MissionCliOnMapData` | TBD (G4) | `ram:80ca22df` | Writes context fields from map data packet. Sets observer flag |
| `MissionCliOnLoadMap` | `0x00849400` | `ram:80ca1b5b` | Handles 0x0196/0x0197/0x0198. Calls `PlayerLoadMap` with param6=1 |
| `InstanceLoadFile` handler | `0x008493C0` | — | Handles 0x0195 (spawn point data) |
| `PlayerLoadMap` | `0x0084E290` | `ram:80ceea7b` | 4-path decision tree. See §5 |
| `PlayerCheckLoginInit` | `0x0084E210` | `ram:80cee800` | Guarded by `(ctx[0x190]&0xC0)==0xC0`. Sends 0x89 or 0x91 |
| `GameQueueReadyToPlay` | `0x0084B650` | `ram:80cdee52` | Sets `0x01081964 = 1` |
| `GameIsPlayingAd` | `0x0084B4E0` | `ram:80cdee41` | Returns `0x0108195C` |
| `CharCliOnMapInitStart` | `0x00811B10` | `ram:80c1c9e2` | Allocates compressed map buffer |
| `CharCliOnMapInit` | `0x0080C250` | `ram:80c1bd0e` | Accumulates map chunks → DecompressMap |

### Senders (CToS packet constructors)

| Function | EXE | WASM | Packet | Size |
|----------|-----|------|--------|------|
| `MsgSendAckAggregate` | `0x0084CDB0` | `ram:80ce781e` | `{0x88}` | 4 |
| `MsgSendAckCreationDataBegin` | `0x0084CDE0` | `ram:80ce7a25` | `{0x89}` | 4 |
| `MsgSendFailedToLoad` | `0x0084CEA0` | `ram:80ce7e62` | `{0x8C}` | 4 |
| `MsgSendObserveGame` | `0x0084CF20` | `ram:80ce803e` | `{0x8E, game_id}` | 8 |
| `MsgSendObserveGetList` | `0x0084CF50` | `ram:80ce8191` | `{0x8F}` | 4 |
| `MsgSendReadyToPlay` | `0x0084CF80` | `ram:80ce82ce` | `{0x90, SystemGUID[16]}` | 20 |
| `MsgSendRequestLanguage` | `0x0084CFD0` | `ram:80ce8546` | `{0x91, lang1, lang2}` | 12 |

### Arrival / Exit

| Function | EXE | WASM | Notes |
|----------|-----|------|-------|
| `MissionCliOnEnterWorld` | TBD | `ram:80ca093e` | Gate check → `GameEnterWorld` |
| `GameEnterWorld` | TBD | `ram:80ce0cdb` | Sets `ctx[0x190] \|= 0x08` |
| `GameLeave` | `0x0084B610` | `ram:80ce1569` | Sets leaving flag |

### Network Dispatch

| Function | EXE | Notes |
|----------|-----|-------|
| `GcGameCmdNotifyProc` | `0x00491490` | Entry point for incoming TCP |
| `MsgConnDispatch` | `0x007D6930` | Packet dispatch to handler table |
| `OnNetMsg` | `0x0084BA40` | Handles 0x1D/0x1E/0x1F/0xD6/0xD7/0xD8 |
| `GetMsgConn` | `0x00491770` | Returns MsgConn |
| `MsgConnSendStruct` | `0x007D76D0` | Sends structured packet |

### Misc

| Function | EXE | WASM | Notes |
|----------|-----|------|-------|
| `ConstGetMissionClientData` | `0x005A6B00` | `ram:818b39ef` | Returns `MissionClientData*` (0x7C bytes × 882 entries) |
| `PropGet` | `0x0047F510` | `ram:8000ac03` | Returns context by property enum |
| `EventCliContextOnGameLoadMission` | `0x00626010` | — | Asserts TLS+0x0C != NULL (GameJoin crash point #1) |
| `GuildCliGetSequence` | `0x0083A5B0` | — | TLS+0x3C → +0x2A4 (crash point #2) |
| `CObserveTable::Find` | `0x0084E190` | — | Looks up game in observe table |
| `MissionCliObserveGame` | `0x008486E0` | — | UI handler → `MsgSendObserveGame` |
| `IUi::GameFrameProc` | `0x004A62C0` | `ram:80fbce63` | Handles `kLoadMapContext` (0x10000098) |
| `Gatekeeper` | `0x00702C20` | — | Loads map context from file; returns 0 on failure |

---

## 5. PlayerLoadMap Decision Tree

```
PlayerLoadMap(context, map_id, MapPoint*, angle, param5, param6):

  STEP 1 — FileConvertIdToPath(map_id) → path_buffer
  STEP 2 — FrameMsgSendRegistered(0x10000098, &struct)  // kLoadMapContext
            Handler: IUi::GameFrameProc @ 0x004A62C0
            Gatekeeper: FUN_00702c20 — loads map from file, returns 0 on failure
  STEP 3 — IF result == 0:
              FileFindHardLinks → FileDelete (cleanup)
              MsgSendFailedToLoad() → {0x8C} → RETURN       ⛔ PATH A (map file failed)
  STEP 4 — IF param6 == 0: → RETURN                          ⛔ PATH B (reconnect silent)
            (param6 is HARDCODED to 1 from MissionCliOnLoadMap)
  STEP 5 — IF GameIsPlayingAd() != 0:
              GameQueueReadyToPlay() → set 0x01081964=1      ⏸️ PATH C (deferred)
              → RETURN (OnNetMsg 0xD7/0xD8 consumes later)
  STEP 6 — MsgSendReadyToPlay() → {0x90, GUID}              ✅ PATH D (direct)
```

---

## 6. Context State

### Flags at +0x190

| Bit | Mask | Name | Set By | Cleared By |
|-----|------|------|--------|------------|
| 0 | 0x01 | LOADED_ONCE | PlayerCheckLoginInit | Context::Reset |
| 1 | 0x02 | LEAVING | GameLeave | Context::Reset |
| 3 | 0x08 | ENTERED_WORLD | GameEnterWorld | Context::Reset |
| 4 | 0x10 | REDIRECT_RECEIVED | MissionCliOnRedirect | Context::Reset |
| 5 | 0x20 | JOINING | GameJoin | Context::Reset |
| 6 | 0x40 | LOGIN_INIT_REQUIRED | OnNetMsg 0x1E/0x1F | Context::Reset |
| 7 | 0x80 | MAP_DATA_RCVD | MissionCliOnMapData | Context::Reset |
| 9 | 0x200 | REDIRECTING | GameRedirectMission | Context::Reset |

### Flags at +0x2A8

| Bit | Mask | Name | Check Function | Set By |
|-----|------|------|---------------|--------|
| 0 | 0x01 | BASE_FLAG | — | MissionCliOnAccessRights |
| 1 | 0x02 | CONNECTED | `MissionCliIsConnected()` → `(ctx[0x2A8]>>1)&1` | MissionCliOnAccessRights |
| 2 | 0x04 | DEVELOPER | `MissionCliIsDeveloper()` → `(ctx[0x2A8]>>2)&1` | MissionCliOnAccessRights |
| 3 | 0x08 | GAME_MASTER | `MissionCliIsGameMaster()` → `(ctx[0x2A8]>>3)&1` | MissionCliOnAccessRights |
| 4 | 0x10 | OBSERVER | `MissionCliIsObserver()` → `(ctx[0x2A8]>>4)&1` | MissionCliOnMapData (packet[0x18]!=0) |

### Context Fields Written by OnMapData

| Offset | Source | Condition |
|--------|--------|-----------|
| +0x2AC | packet[4] | Unconditional |
| +0x230 | packet[8] | Unconditional |
| +0x238 | packet[0xC] | Unconditional |
| +0x228 | packet[0x10] | Unconditional |
| +0x22C | packet[0x14] | Unconditional |
| +0x234 | mirror of 0x230 | IF `packet[0x18] == 0` |
| +0x23C | mirror of 0x238 | IF `packet[0x18] == 0` |
| +0x2A8 bit 0x10 | OBSERVER | IF `packet[0x18] != 0` |
| +0x190 bit 0x80 | MAP_DATA_RCVD | Unconditional |

### Join Params (+0x194–0x1C4)

Written by `GameJoin`.

| Offset | Size | Field |
|--------|------|-------|
| 0x194 | 4 | join_map_id |
| 0x198 | 4 | join_mission |
| 0x19C | 4 | join_mission_map |
| 0x1A0 | 24 | join_net_address |
| 0x1B8 | 4 | join_security_token |
| 0x1BC | 4 | join_guild_seq (from GuildCliGetSequence) |
| 0x1C0 | 4 | join_extra1 |
| 0x1C4 | 4 | join_extra2 |

### Redirect Params (+0x1FC–0x228)

Cleared by `MemZero(context+0x1FC, 0x2C)` at start of every `GameRedirectMission`.

| Offset | Size | Field |
|--------|------|-------|
| 0x1FC | 4 | redirect_state (3 = redirecting) |
| 0x200 | 4 | redirect_map_id |
| 0x204 | 4 | redirect_mission |
| 0x218 | 4 | redirect_territory |
| 0x21C | 4 | redirect_district |
| 0x220 | 4 | redirect_language |

### Server Response Params (+0x1C8–0x1F8)

Stored separately — survives the `MemZero` at +0x1FC.

| Offset | Size | Field |
|--------|------|-------|
| 0x1C8 | 4 | response_map_id |
| 0x1CC | 4 | response_emission |
| 0x1D4 | 24 | NetAddress (game server IP:port) |
| 0x1EC | 4 | security_token |
| 0x1F0 | 4 | district / guild_seq |

---

## 7. Two-Global System

| Global | EXE Address | WASM Address | Set By | Cleared By | Purpose |
|--------|-------------|-------------|--------|------------|---------|
| Ready Gate | `0x0108195C` | `DAT_ram_005a4048` | OnNetMsg 0xD6 handler | Never explicitly | Server says "map data complete" |
| Queued Ready | `0x01081964` | `DAT_ram_005a404c` | `GameQueueReadyToPlay()` | OnNetMsg 0xD7/0xD8 handler | Client has map but waiting |

**Observed runtime values during unowned travel: `g4048_set=0, g404c_set=0`** — neither global is ever engaged.

---

## 8. OnNetMsg Handler Dispatch

| Server Msg | Handler Action |
|-----------|----------------|
| **0xD6** | `0x0108195C = 1` — server says map ready, wait for 0xD7/D8 |
| **0xD7** | IF `0x0108195C && 0x01081964` → clear 0x01081964 → `MsgSendReadyToPlay()` |
| **0xD8** | Identical to 0xD7 |
| **0x1E** | Normal: `ctx[0x190] \|= 0x40` + `PlayerCheckLoginInit`. Observer: `GameJoin(param9=1)` |
| **0x1D** | Observer response. Status==0 → `GameJoin(param9=1)`. Error → redirect |
| **0x1F** | Game exit. errCode==7 && ENTERED_WORLD → `WriteReconnectData`. Else → `FileDelete(0, 0x0B)` |

---

## 9. All Travel Paths

### Path A: Normal (World Map)
```
IUi::MapSelect → PartyCliTravelMission → GameRedirectMission → OnRedirect → GameJoin
```
Full validation: territory, party, mission_locked, tag_flags.

### Path B: Observer-Bypass
```
IUi::MapSelect → if MissionCliIsObserver() → SKIP PartyCliTravelMission → GameRedirectMission
```
Same auth pipeline, skips party/territory checks.

### Path C: Observer-Alt (0x8E protocol)
```
MissionCliObserveGame → MsgSendObserveGame(0x8E) → Server 0x1D → OnNetMsg → GameJoin(param9=1)
```
Bypasses auth server entirely. Converges at GameJoin.

### Path D: Reconnect
```
IUi::CompleteLogin → if createParams & 2 → GameRedirectReconnectValidate
  → GameRedirectReconnect → ReadReconnectData(0x0B) → GameJoin
```
Reads forgeable archive file 0x0B. All validation client-side.

### Path E: Travel-on-Login
```
PartyCliTravelMissionLogin → MsgSendTravelMissionLogin → {0xB2}
```

### Path F: Sentinel Redirect
```
IUi::MapSelect type=2 → GameRedirectMission(1, 0, 0xFFFFFFFD, 0, 0xFFFFFFFF)
```

### Path G: GM Teleport
```
Ctrl+Shift+T → CharCliPlayerOrderTeleport
```
Within current map only. Gated on `MissionCliIsGameMaster()`.

---

## 10. Reconnect Data Forge (Archive 0x0B)

### File Format (0x49 = 73 bytes)

| Offset | Size | Field | Source |
|--------|------|-------|--------|
| 0x00 | 1 | version | Hardcoded 1 |
| 0x01 | 4 | build_id | `BuildId__()` → `*0x000096be` |
| 0x05 | 4 | map_id | context[0x194] |
| 0x09 | 4 | mission | context[0x198] |
| 0x0D | 4 | mission_map | context[0x19C] |
| 0x11 | 24 | net_address | context[0x1A0] (3× uint64) |
| 0x29 | 4 | security_token | context[0x1B8] |
| 0x2D | 4 | extra | context[0x1C0] |
| 0x31 | 16 | GUID | context[0x64] (16 bytes) |
| 0x41 | 4 | timestamp | `TimeGetMinutesSince2001Utc()` |
| 0x45 | 4 | CRC32 | `Crc32(0, data, 0x45)` — IEEE 802.3, poly 0xEDB88320 |

### Validation (ALL client-side)

1. `version == 1`
2. `build_id == BuildId()`
3. `CRC32` matches
4. `timestamp` ≤ 11 minutes old

### WriteReconnectData Guards

- `context[0x19C] == 0` → RETURN (never entered world)
- `context[0x190] & 1` (LOADED_ONCE) → RETURN

### Lifecycle

In the EXE (MSVC production build), `WriteReconnectData` and `FileDelete(0, 0x0B)` are **IF/ELSE — mutually exclusive**:
- errCode==7 && ENTERED_WORLD → **WriteReconnectData ONLY** (file persists)
- Otherwise → **FileDelete ONLY**

---

## 11. GameJoin Crash (G9)

### Root Cause

`GameJoin` is designed for network **transition** state, not stable connected map state. Calling it from injected code violates multiple preconditions.

### Crash Points

| # | Location | EXE Address | Mechanism | SEH-Catchable? |
|---|----------|-------------|-----------|:---:|
| 1 | `EventCliContextOnGameLoadMission` | `0x00626010` | Asserts TLS+0x0C != NULL → hard termination | ❌ |
| 2 | `GuildCliGetSequence` | `0x0083A5B0` | NULL deref if TLS+0x3C == NULL → ACCESS_VIOLATION | ✅ |
| 3 | GC object init | `0x0048BDA0` | Sentinel check on `DAT_00bfcfc4` → assertion | ❌ |

### Precondition Mismatch

| Property | Normal Path (auth transition) | Injected Call (stable state) |
|----------|------------------------------|------------------------------|
| Map state | LOADING | STABLE |
| Context flags | Sanitized | Unchanged |
| NetAddress source | Server packet | Live connection |
| GC system | No active connection | Active connection |

---

## 12. IMsgChannel Handler Table (from GWCA StoCMgr.cpp)

### Structure

```
GameServer → gs_codec → handlers (StoCHandlerArray)

StoCHandlerArray:
  +0x00: uint32_t size        (= 0x1E7 = 487 entries)
  +0x04: uint32_t capacity
  +0x08: StoCHandler* data

StoCHandler (12 bytes each):
  +0x00: uint32_t* packet_template
  +0x04: uint32_t  template_size
  +0x08: StoCHandler_pt handler_func
```

The array is **indexed by packet header** — `handlers->at(0x0191)` gives the INSTANCE_REDIRECT handler. No search loop.

### Dispatch Chain

```
TCP bytes → GcGameCmdNotifyProc (0x00491490)
  → MsgConnDispatch (0x007D6930)
    → handler table lookup by packet_id
    → handler call(context, packet_data, packet_size)
```

### Known Handler Mappings

| Packet | Handler | EXE Address |
|--------|---------|-------------|
| 0x0191 | MissionCliOnErrorRedirect | `0x00849230` |
| 0x0195 | InstanceLoadFile (spawn point) | `0x008493C0` |
| 0x0196 | MissionCliOnLoadMap | `0x00849400` |
| 0x0197 | MissionCliOnLoadMap | `0x00849400` |
| 0x0198 | MissionCliOnLoadMap | `0x00849400` |
| 0xD6 | OnNetMsg | `0x0084BA40` |
| 0xD7 | OnNetMsg | `0x0084BA40` |
| 0xD8 | OnNetMsg | `0x0084BA40` |
| 0x1D | OnNetMsg | `0x0084BA40` |
| 0x1E | OnNetMsg | `0x0084BA40` |
| 0x1F | OnNetMsg | `0x0084BA40` |

### GWCA Packet Callback System

GWCA's `StoCMgr.cpp` exposes `StoC::RegisterPacketCallback(&entry, header, callback)`. Callbacks fire **before** the original handler. Setting `status.blocked = true` prevents the original handler from executing. Currently used in `MapMgr.cpp` for `0x0191` monitoring.

---

## 13. MissionCliOnErrorRedirect

### Signature

```c
int __cdecl OnErrorRedirect(void* packet, void* dispatch);
```

### Packet Structure at Entry

| Offset | Value |
|--------|-------|
| 0x00 | `0x00000191` (INSTANCE_REDIRECT header) |
| 0x04 | `mission_id` (fallback mission, e.g., 249) |
| 0x08–0x18 | UTF-16 message text |
| 0x1C | territory (0xFFFFFFFD = sentinel) |
| 0x20 | region_or_type |

### Behavior

1. Reads `packet[4]` as mission_id
2. Calls `ConstGetMissionClientData(mission_id)` → gets `MissionClientData*`
3. Reads `game_type` from `data[0x0C]`
4. Calls `GameGetType(0, game_type)` → selector output
5. If result == 0x11 → fatal re-redirect path
6. Calls `PropGet(0x11)` → context
7. Calls `GameRedirectMission(context, selector, mission_from_packet, 0xFFFFFFFD, 0, 0xFFFFFFFF)`

### Caller Return Address

`MissionCliOnErrorRedirect` → `GameRedirectMission` returns from VA `0x008492B4`.

---

## 14. Observer Protocol (0x8E → 0x1D → GameJoin)

### Full Chain

```
MsgSendObserveGame(game_id) @ 0x0084CF20
  → sends {0x8E, game_id} (8 bytes)
  → Server responds 0x1D
    → OnNetMsg 0x1D handler @ 0x0084BA40
      → Status == 0: GameJoin(context, map_id, mission, game_type_flag,
                              &net_address, guild_seq, context[0x224], 0, 1)
      → Status error: redirect
```

### Prerequisites

- Valid `game_id` required — obtained via `MsgSendObserveGetList` (0x8F) → server populates `CObserveTable` at `context+0x254`
- `CObserveTable` is a THashTable with 0xA4-byte entries containing game_id, map_id, mission, game_type, server data
- Or found via `CObserveTable::Find` @ `0x0084E190`

### Why Direct GameJoin Crashes But Observer Path Doesn't

The observer path's `GameJoin` call runs inside the `OnNetMsg` handler on the **network dispatch thread**, with correct TLS context. Direct `GameJoin` from injected Python runs on `Game.enqueue()` thread — TLS pointers differ, causing the G9 crashes.

---

## 15. Unresolved Gaps

| # | Gap | Impact |
|---|------|--------|
| G4 | `MissionCliOnMapData` EXE address | Medium — needed for pre-0x88 interception |
| G6 | Server criteria for 0x0191 vs 0xD6 | Black box — session-based, no client-visible trigger |
| G10 | Observer flag effect on server 0x88 response | Medium — unclear if server checks observer status |
| G11 | Does server accept 0x90 after 0x0191 was sent? | High — untested, determines minimal bypass viability |
| G12 | Does `FUN_00702C20` gatekeeper succeed for unowned maps? | Medium — blocks full synthetic PlayerLoadMap |
| G13 | IMsgChannel pointer location at runtime | Medium — needed for handler table replacement |
| G16 | Exact context state at 0x0191 arrival for unowned observer | Low — mostly captured in existing traces |
| G17 | Archive file write from injected code | Medium — needed for reconnect forge |

---

## 16. Bypass Approaches Evaluated

### A. Make server send spawn instead of redirect
**Feasibility: 15-25%** — Server decides by TCP session. No packet carries forgeable ownership data. Only sub-approach with potential: observer `0x8E`→`0x1D`→`GameJoin` chain, blocked by G9 crash.

### B. Block 0x0191 + send 0x90 (minimal intervention)
**Feasibility: 15-30%** — Untested (G11). Risk: server already tore down game instance after sending 0x0191, ignores 0x90.

### C. Full synthetic client-side load
**Feasibility: 5-15%** — Requires: block normal travel, locally load map assets, simulate all server packets (0x0099, 0x01AB, 0x0195, 0x008E), call PlayerLoadMap → MsgSendReadyToPlay. Many unknowns (G12, G13).

### D. Reconnect forge
**Feasibility: 25-35%** — All validation client-side. Requires: archive file write, GUID from context, trigger CompleteLogin with bit 2. Blocked by G17 and GameJoin crash.

### E. Observer-as-transport
**Feasibility: dependent on G9 fix** — Use `MsgSendObserveGame` to get server to call `GameJoin` safely. Requires valid `game_id` for target map.

---

## 17. Key Runtime Observations

### From owned_observer probe (target=81, success)
- Duration: 1689ms
- CToS: `0x00C1, 0x0091, 0x0088, 0x0090`
- StoC: 2116 packets total, focused capture shows `0x017C, 0x0199, 0x0099, 0x01AB, 0x0099, 0x008E`
- `pkt_redirect=0, redirect_pre_spawn=0`
- `g4048_set=0, g404c_set=0`
- 16 stages → `entered_world`

### From unowned_observer probe (target=81, rejected)
- Duration: 2821ms
- CToS: `0x00C1, 0x0091×2, 0x0088, 0x0090`
- StoC focused: `0x017C, 0x0199, 0x0191` (3 packets, last is kill)
- `pkt_redirect=1, redirect_pre_spawn=1`
- `g4048_set=0, g404c_set=0`
- 12 stages in cycle 1 → redirect → 15 stages in cycle 2 (fallback 249) → `entered_world`

### Critical Finding
The client sends the **same CToS packets** for both owned and unowned travel. The `0x0191` replaces the entire server-side spawn chain (`0x0099, 0x01AB, 0x0195, 0x0196, 0x008E`). The ready gate globals are **never set** in either path (both show `g4048_set=0`).

---

## 18. Files

| File | Purpose |
|------|---------|
| `Py4GW\vendor\gwca\Source\MapMgr.cpp` | C++ hooks, redirect logging, travel probes |
| `Py4GW\vendor\gwca\Include\GWCA\Managers\MapMgr.h` | Public API for travel bypass |
| `Py4GW\vendor\gwca\Source\StoCMgr.cpp` | Packet dispatch, callback registration |
| `Py4GW\src\Py4GW_UI.cpp` | Python bindings for travel debug, redirect logs |
| `Py4GW_python_files\GodTools.py` | Test harness, packet capture, probe launcher |
| `Py4GW_python_files\Py4GWCoreLib\native_src\methods\MapTravelBypassMethods.py` | G8 prototype (send_ready_to_play, force_spawn) |
| `Py4GW_python_files\docs\RE\map_travel_research.md` | This document |
