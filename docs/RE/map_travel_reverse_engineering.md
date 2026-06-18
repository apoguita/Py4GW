# Guild Wars Map Travel â€” Reverse Engineering (2026-06-08)

EXE build: 05-30-2026 | Scope: Full end-to-end pipeline + travel-back blocking experiments

## 0. Current Status (2026-06-14)

The project is no longer trying to discover where the fallback redirect originates. That part is solved.
The active RE target has shifted earlier in the pipeline: the pre-spawn handover that fails before the client ever reaches spawn authorization on unowned observer travel.

Authoritative comparison matrix:

1. `owned_normal`
   - reaches target `81`
   - uses the normal redirect path
   - shows `OnRedirect` / `TRANSFER_GAME_SERVER_INFO (0x01A5)`

2. `owned_observer`
   - reaches target `81`
   - does not hit the rollback redirect/error family

3. `unowned_observer`
   - starts from observer
   - targets the same map `81`
   - target unlocked state is false
   - receives `INSTANCE_REDIRECT (0x0191)`
   - enters `MissionCliOnErrorRedirect`
   - finishes on fallback mission `249`

Project status:

- Shared native redirect logging is wired through `MapMgr.cpp`, `MapMgr.h`, `Py4GW_UI.cpp`, and `GodTools.py`.
- `RelWithDebInfo` builds successfully with the current instrumentation.
- The loaded DLL now self-identifies in `travel_back_debug` with:
  - `build_id`
  - `build_compiled_at`
  - `build_cookie`
- Current known-good fingerprint:
  - `build_id=travel-re-2026-06-14-build-fingerprint-v1`
  - `build_cookie=0x26061401`
- The rollback application point is confirmed:
  - forward call: `MissionCliGameRedirectMission` at return VA `0x00847DF0`
  - fallback call: `MissionCliOnErrorRedirect` at return VA `0x008492B4`
  - nested auth send: `GameRedirectMission -> NetGameClientGameRedirect` at return VA `0x0084B827`
- The older `MissionCliOnErrorRedirect`-centric framing is now insufficient.
- The active target is:
  - explain why `unowned_observer` reaches `INSTANCE_REDIRECT (0x0191)` immediately after `map_data_received`
  - explain why, despite sending:
    - `0x0088 INSTANCE_LOAD_REQUEST_SPAWN`
    it never receives:
    - `READY_FOR_MAP_SPAWN (0x01AB)`
    - `0x0090 INSTANCE_LOAD_REQUEST_PLAYERS`
  - locate the handover gate between `MissionCliOnLoadMap` / `MissionCliOnMapData` / `PlayerLoadMap` and `READY_FOR_MAP_SPAWN`

### 0.1 Latest Runtime Handover Finding (2026-06-14, target 81)

The newest native-handoff probes move the active diagnosis from "which single field causes the kick" to
"which later handover stages never happen before the disconnect."

Authoritative failing run:

- scenario: `unowned_observer`
- target: `81`
- trigger: `map_data_received`
- native action: `set_ready_gate_only`
- follow-up join: **not** attempted
- result: load begins, then timeout / server disconnect

Live progression after the trigger:

```text
map_data_received
  -> pkt_instance_redirect
  -> redirect_before_spawn_auth
  -> pre_spawn_error_redirect_call
  -> pre_spawn_error_redirect_result
  -> map_state_set
```

Confirmed absent from this failing path:

- `TRANSFER_GAME_SERVER_INFO (0x01A5)`
- `READY_FOR_MAP_SPAWN (0x01AB)`
- `INSTANCE_LOAD_FINISH / INSTANCE_LOADED`
- `map_loaded`
- `entered_world`

The key runtime label is now:

- `redirect_before_spawn_auth detail=load_info_without_ready_for_spawn`

Interpretation:

- the failing path is already on the pre-spawn error-redirect branch before any normal spawn authorization happens
- simply toggling the ready gate (`g4048`) or forcing ready from the current probe harness is **insufficient**
- the disconnect does **not** prove a single bad signature or bad field write by itself
- it proves that the handover never reaches the normal `READY_FOR_MAP_SPAWN` side of the pipeline

Relevant packet summary from the failing run:

- StoC seen:
  - `INSTANCE_LOAD_HEAD (0x017C)`
  - `INSTANCE_LOAD_INFO (0x0199)`
  - `INSTANCE_REDIRECT (0x0191)`
- StoC not seen:
  - `TRANSFER_GAME_SERVER_INFO (0x01A5)`
  - `READY_FOR_MAP_SPAWN (0x01AB)`
- CToS seen:
  - `0x00C1`
  - `0x0091`
- no downstream `0x0090` progression was observed in this trace

Operational conclusion:

- `MissionCliOnErrorRedirect` remains a symptom point, not the recovery point
- the active RE target is the mission-to-char / pre-spawn handover boundary that should lead to
  `READY_FOR_MAP_SPAWN`, but instead falls directly into `INSTANCE_REDIRECT`
- future runtime experiments should compare the first post-`map_data_received` divergence between:
  - `owned_observer`
  - `unowned_observer`
  rather than only testing isolated writes like `g4048=1`

## 1. Pipeline Overview

```
World Map Click â†’ OnLocationTagNotifyDoubleClick â†’ OnTravelAttempt
  â†’ kTravel (0x10000183) â†’ IUi::MapSelect â†’ GameRedirectMission
  â†’ Auth Server â†’ OnRedirect â†’ GameJoin â†’ OnLoadMap
  â†’ PlayerLoadMap â†’ Loading Screen â†’ MissionCliOnEnterWorld
  â†’ GameEnterWorld â†’ [arrived]
```

## 2. Key Functions â€” WASM â†” EXE Mappings

| Function | WASM | EXE | Scanner Pattern |
|----------|------|-----|-----------------|
| `MissionCliOnErrorRedirect` | `ram:80ca0d96` | `0x00849230` | `55 8B EC 8B 45 08 53 56 57 8B 70 04` |
| `MissionCliOnRedirect` | `ram:80ca3ac2` | `0x00849990` | `55 8B EC 8B 45 08 83 EC 08 8B 40 20` |
| `MissionClient::GameJoin` | `ram:80ce01aa` | `0x0084b4f0` | `55 8B EC 83 EC 14` |
| `GameRedirectMission` | `ram:80ce1ad1` | `0x0084b770` | `81 8E 90 01 00 00 00 02 00 00 BA 2C` â†’ `ToFunctionStart` |
| `GameEnterWorld` | `ram:80ce0cdb` | TBD | TBD |
| `MsgSendReadyToPlay` | `ram:80ce82ce` | `0x0084cf80` | `C7 45 E8 90 00 00 00` â†’ `ToFunctionStart` |
| `PropGet` | `ram:8000ac03` | `0x0047f510` | `8B 0D ?? ?? ?? ?? 64 A1 2C 00 00 00 8B 04 88 8B 80 08 00 00 00 C3` |
| `GameLeave` | `ram:80ce1569` | `0x0084b610` | `55 8B EC 8B 45 08 8B 88 90 01 00 00` |
| `NetGameClientGameRedirect` | `ram:80d0d2b3` | `0x0048e970` | TBD |
| `NetGameClientGameJoin` | `ram:80d0d78a` | `0x0048e8e0` | TBD |
| `IUi::MapSelect` | `ram:80fc49cb` | TBD | TBD |
| `MissionCliGameRedirectMission` | `ram:80c9990c` | `0x00847dd0` | String-anchor: caller of `"RedirectMission: %d %08x"` |
| `ConstGetMissionClientData` | `ram:818b39ef` | `0x005a6b00` | String-anchor: `"index < arrsize(s_missionClientData)"` |
| `GmTerritoryCanTravel` | `ram:80d9479a` | TBD | TBD |
| `PartyCliTravelMission` | `ram:80d512c4` | TBD | TBD |

## 3. Context State

### Flags (@ MissionClient::Context +0x190)

| Bit | Mask | Name | Set By |
|-----|------|------|--------|
| 0 | 0x001 | LOADED_ONCE | Initial load |
| 1 | 0x002 | LEAVING | GameLeave |
| 3 | 0x008 | ENTERED_WORLD | GameEnterWorld |
| 4 | 0x010 | REDIRECT_RECEIVED | OnRedirect |
| 5 | 0x020 | JOINING | GameJoin |
| 6 | 0x040 | MAP_DATA_REQUIRED | Login init |
| 7 | 0x080 | MAP_DATA_RCVD | OnMapData |
| 9 | 0x200 | REDIRECTING | GameRedirectMission |

### State Machine

```
IDLE â†’ REDIRECTING(0x200) â†’ REDIRECT_RECEIVED(0x210) â†’ JOINING(0x230) â†’ IN_GAME(0x238) â†’ LEAVING(0x23A) â†’ DISCONNECTED
```

### Redirect Params (@ +0x1FCâ€“0x228)

Every call to `GameRedirectMission` does `MemZero(context+0x1FC, 0x2C)` â€” clears all 44 bytes before writing new params. Each call overwrites previous redirect state.

| Offset | Size | Field |
|--------|------|-------|
| 0x1FC | 4 | redirect_state (3 = redirecting) |
| 0x200 | 4 | redirect_map_id |
| 0x204 | 4 | redirect_mission |
| 0x218 | 4 | redirect_territory |
| 0x21C | 4 | redirect_district |
| 0x220 | 4 | redirect_language |

### Server Response Params (@ +0x1C8â€“0x1F8)

Stored separately from redirect params â€” survives `MemZero` at 0x1FC.

| Offset | Size | Field |
|--------|------|-------|
| 0x1C8 | 4 | response_map_id |
| 0x1CC | 4 | response_emission |
| 0x1D4 | 24 | NetAddress (game server IP:port) |
| 0x1EC | 4 | security_token |
| 0x1F0 | 4 | district / guild_seq |

### Join Params (@ +0x194â€“0x1C4)

Stored by `GameJoin`.

| Offset | Size | Field |
|--------|------|-------|
| 0x194 | 4 | join_map_id |
| 0x198 | 4 | join_mission |
| 0x19C | 4 | join_mission_map |
| 0x1A0 | 24 | join_net_address |
| 0x1B8 | 4 | join_security_token |
| 0x1BC | 4 | join_guild_seq |
| 0x1C0 | 4 | join_extra1 |
| 0x1C4 | 4 | join_extra2 |

### Observer State Flag

`context[0x2A8] >> 4 & 1` â€” true when player is in observer mode. Bypasses most travel validation in `IUi::MapSelect`.

## 4. Denial Paths (18 total)

| # | Where | Condition | Effect |
|---|-------|-----------|--------|
| 1 | `OnLocationTagNotifyDoubleClick` | `(tag_flags & 1) == 0` | Silent block |
| 2 | `OnTravelAttempt` | `target_data[0x12] & 1` | Silent block |
| 3 | `IUi::MapSelect` | `!MissionCliIsConnected()` | Silent return |
| 4 | `IUi::MapSelect` | `MissionCliIsCreatingCharacter()` | Silent return |
| 5 | `MapGetMissionTagFlags` | Game type not in allowed set | Tag bit 0 = 0 |
| 6 | `MapGetMissionTagFlags` | Mission not unlocked | Tag bit 0 = 0 |
| 7 | `MapGetMissionTagFlags` | `data[0x40]==0 && data[0x44]==0` | Challenge incomplete |
| 8 | `MapGetMissionTagFlags` | `data[0x10] & 0x20` | Blocking flag |
| 9â€“12 | `GmTerritoryCanTravel` | Territory invalid, cross-region, GH blocked | Return false |
| 13 | `MissionCliOnErrorRedirect` | Server error type 0x11 | Fatal â€” re-redirect |
| 14 | `MissionCliOnErrorRedirect` | Server error non-fatal | Silent re-redirect |
| 15 | `PartyCliOnRedirectCancelError` | Party leader cancels | Chat error + UI msg |
| 16 | `PlayerLoadMap` | File not in .dat archive | Cleanup + fail msg |
| 17 | `GameJoin` | Map system not ready | Early return |
| 18 | `MissionCliObserveGame` | Game not in observe table | Assertion |

### Territory â†’ Region Mapping

| Territory | Region | Guild Hall? |
|-----------|--------|-------------|
| 0â€“4 | 0 | Yes |
| 5 | 6 | No |
| 6 | 7 | No |

`GmTerritoryCanTravel(from, to)`: same region allows travel. GH sentinel `0xFFFFFFFE` only allowed from territories 0â€“4.

## 5. Server-Side Arrival Check

`PlayerLoadMap` â†’ `MsgSendReadyToPlay()` sends `{GUID, 0x90}` via `MsgConnSendStruct(conn, 0x14, &packet)`. Server receives this and checks permissions.

If map is locked: server sends `OnErrorRedirect` with mission code and territory `0xFFFFFFFD`. Client handler calls `GameRedirectMission(context, mission, 0xFFFFFFFD, 0, 0xFFFFFFFF)` â€” sends player back to default territory.

**Multiple MsgSendReadyToPlay paths exist:**
1. `context[0x3C] != 0 && is_first_load && !ad_playing` â†’ direct call
2. `context[0x3C] != 0 && !is_first_load` â†’ falls through to path 3
3. `context[0x3C] == 0 && file_found` â†’ direct call
4. `GameQueueReadyToPlay()` sets flag â†’ deferred call later

## 6. Observer Mode Bypass

When `MissionCliIsObserver()` returns true, `IUi::MapSelect` skips: party checks, territory validation, mission-locked checks, and most game-type validation. A separate path exists via `MsgSendObserveGame(0x8E)` which bypasses `GameRedirectMission` entirely.

## 7. Working Approach: MapTest (MapMgr.cpp)

```python
mt_step0(): send kTravel to TARGET map
  â†’ Wait for loading anchor (kLoadMapContext via OnMapTestUIMessage)
mt_step1(): send 3Ã— kTravel to CANCEL map (795, district 2)
  â†’ Auth server notified â†’ game server disconnect
  â†’ MapTest detects disconnect â†’ retries from step0
```

The cancel redirect pre-empts the server's travel-back. Client disconnects from target, but the retry loop reconnects. Eventually one cycle succeeds.

### Actual Python Binding Surface (2026-06-12)

The active build does not expose this path as `PyUIManager.UIManager.travel_test(...)`.
The real binding is exported from `src/Py4GW_UI.cpp` on `Py4GW.UI.UI`:

- `map_test_start(map_id, alt_map_id, number, count, delay_ms, timeout_ms, message_id)`
- `map_test_stop()`
- `get_map_test_status()`
- `is_map_test_active()`
- `get_map_test_count()`

`GodTools.py` now calls this `map_test_*` surface while keeping the same bot-tree execution model.

### Current Test Process (2026-06-12)

The active test loop is now:

1. Build `RelWithDebInfo` and load the resulting `Py4GW.dll`.
2. Launch `GodTools.py`.
3. Use the bot-tree button in `tree.UI.draw_window()` for the native MapTest path.
4. Use `Start Capture` or rely on auto capture in `_draw_debug_window()` when packet-level RE is needed.
5. Trigger one travel action under test.
6. Let the travel either arrive, roll back, freeze, timeout, or disconnect.
7. Use `Stop + Dump`.
8. Read all three outputs together:
   - packet dump
   - `travel_back_debug`
   - `travel_redirect_log`

The current purpose of each test type:

- native MapTest bot-tree path
  - original working cancel-travel-back harness
  - C++ owns the travel -> bad travel -> wait -> retry loop
- `Plain Probe (445)`
  - baseline for the game's normal behavior
  - used mostly for unowned observer travel analysis
- `Owned Probe (81)`
  - owned control path
  - confirms normal owned travel is still stable
- `Rewrite EXP (445)`
  - targeted rollback rewrite experiment
  - focuses on the second `GameRedirectMission` rollback case

Current interpretation workflow:

1. Check whether the path used `PARTY_TRAVEL` or `0x00C1`.
2. Check whether `INSTANCE_REDIRECT` appears in StoC.
3. Check whether `travel_redirect_log` contains:
   - first `game_redirect_mission`
   - second `game_redirect_mission`
   - `on_error_redirect`
   - `on_redirect`
4. Compare pre/post mission values in the redirect log.
5. If the second `game_redirect_mission` flips target `445 -> 249`, treat that as the rollback pivot.

Current logging behavior:

- `GodTools.py` clears redirect logs when reset or packet capture starts.
- `GodTools.py` prints redirect logs when capture stops.
- `GodTools.py` can also print them during live debug monitoring.
- Shared redirect logs come from native code, not from temporary test scripts.

## 8. Experimental Hooks

### Test Results

| Approach | Result |
|----------|--------|
| Block OnRedirect + OnErrorRedirect together | Immediate kick |
| Block OnErrorRedirect only | ~5s timeout then kick |
| Cancel from OnMapTestUIMessage during loading | Immediate disconnect (authâ†’game server notification) |
| Cancel redirect back to current server | Error's OnRedirect never caught by hook |
| Block MsgSendReadyToPlay (always) | Player stuck in loading forever â€” no error, no kick, frozen |
| Block MsgSendReadyToPlay (first only) | First call blocked, server still sent OnErrorRedirect via another path |
| Redirect error back to target via GameRedirectMission hook | Logging complete; bypass still unresolved |

### 2026-06-12 Runtime Finding

For the normal unowned observer probe to map `445`, the redirect log currently shows:

1. `game_redirect_mission` sets forward travel (`249 -> 445`)
2. a second `game_redirect_mission` rewrites the state back (`445 -> 249`)
3. `on_error_redirect` fires after the rollback rewrite

In this case, `on_redirect` is not observed before rollback completes.

This means:

- `OnErrorRedirect` is too late for the unowned observer path
- `OnRedirect` is not the primary pivot for this failing case
- the second `GameRedirectMission` call is the current highest-value interception point

### 2026-06-12 Late Findings

Later runs established that rewriting the rollback-shaped `GameRedirectMission` call is enough to keep the client redirect context pinned to `445`, but not enough to complete travel.

Observed behavior after the redirect rewrite:

- the client can remain pinned to `445` while still looping in loading
- no successful rewritten run has yet produced `ctos_0090`
- swallowing `OnErrorRedirect` with no continuation causes a network disconnect
- synthetic continuation built from the error packet causes "game was unable to find the mission requested"

Safe baseline from the `2026-06-12 22:27:34` run:

- no kick occurred
- loading did start for `445` (`loading=True`, `observer=False`)
- the run then looped through repeated `INSTANCE_LOAD_HEAD` / `INSTANCE_LOAD_INFO` / `INSTANCE_REDIRECT`
- client-side follow-up was repeated `INSTANCE_LOAD_REQUEST_ITEMS`
- there was still no `ctos_0090`, no spawn progression, and no arrival

The most stable loop shape so far is:

- `GameRedirectMission` forward seed to `445`
- during loading, repeated rollback-shaped `GameRedirectMission` calls with `249 / 0xFFFFFFFD / 0 / 0xFFFFFFFF`
- active rewrite keeps applied mission pinned to `445`
- `OnErrorRedirect` passes through unchanged after each rollback attempt
- StoC `0x0199` currently alternates `1` and `2` before each `0x0191` redirect

Packet-level evidence from the shared redirect log shows that `OnErrorRedirect` is not carrying a reusable `OnRedirect`-style packet:

- `packet_u32_00 = 0x00000191`
- `packet_u32_04 = 0x000000F9` (`249`)
- later dwords contain UTF-16-looking message payload rather than a clean redirect struct

Current interpretation:

- rollback state is no longer the primary blocker once `GameRedirectMission` is rewritten
- the remaining blocker is the load handshake after the client context is already pinned to `445`
- the next RE target is the progression between repeated `INSTANCE_LOAD_REQUEST_ITEMS` and the missing `0x0090`
- the highest-value code paths to inspect next are `GameJoin` early-return conditions and the later `MsgSendReadyToPlay` / queued-ready progression

### 2026-06-13 Scenario Matrix and Fallback Origin

The probe surface now emits its own scenario classification. The three valid comparison cases are:

- `owned_normal`
- `owned_observer`
- `unowned_observer`

All current comparison tests use the same target map: `81`.

Observed behavior:

| Scenario | Start context | Redirect/error family | Terminal map |
|----------|---------------|-----------------------|--------------|
| `owned_normal` | normal | `OnRedirect` / `0x01A5` transfer path | `81` |
| `owned_observer` | observer | no redirect/error hook hit | `81` |
| `unowned_observer` | observer | `INSTANCE_REDIRECT (0x0191)` -> `OnErrorRedirect` | `249` |

This is now the authoritative split. `unowned_observer` is the only current scenario that triggers the rollback machinery.

Validated helper rebasing now makes the mission metadata / selector probe trustworthy:

- `ConstGetMissionClientData` VA `0x005A6B00` is resolved relative to the loaded `Gw.exe` base
- redirect selector VA `0x00921ED0` is resolved relative to the loaded `Gw.exe` base

For the `unowned_observer` rollback:

- server error packet supplies `mission = 249`
- `ConstGetMissionClientData(249)` returns mission entry `0x01330234`
- mission `249` has `game_type = 0x0A`
- selector input bool = `0`
- selector output = `3`

The fallback tuple is therefore directly measured, not inferred:

```text
GameRedirectMission(3, 249, 0xFFFFFFFD, 0, 0xFFFFFFFF)
```

Caller-site logging was also added to each redirect event:

- `caller_label`
- `caller_va`
- `caller_return_address`

The first caller-site run showed:

- forward travel call returns from VA `0x00847DF0` (inside `MissionCliGameRedirectMission`)
- fallback rollback call returns from VA `0x008492B4` (inside `MissionCliOnErrorRedirect`)
- `NetGameClientGameRedirect` returns from VA `0x0084B827` (internal call within `GameRedirectMission`)

The original labeler used exact VAs and therefore printed `unknown` for these first measurements. The RE conclusion is still clear: the rollback is emitted from the `OnErrorRedirect -> GameRedirectMission` chain, not from a later replay/reissue path.

### Active Hooks (MapMgr.cpp)

| Hook | EXE | Toggle |
|------|-----|--------|
| `MissionCliOnErrorRedirect` | `0x00849230` | `SetBlockTravelBack` |
| `MissionCliOnRedirect` | `0x00849990` | (pass-through, always) |
| `MsgSendReadyToPlay` | `0x0084cf80` | `SetBlockReadyToPlay` |
| `GameRedirectMission` | `0x0084b770` | `SetBlockRedirectToTarget` |
| `NetGameClientGameRedirect` | `0x0048e970` | rollback rewrite experiment |

Notes:

- `OnErrorRedirect` consume/replay toggles are now considered archived experiments, not the active path.
- The current safe active experiment is redirect rewrite plus packet logging, not synthetic continuation.

### GodTools.py Surface

Authoritative current surface:

- `Owned Normal (81)`
- `Owned Observer (81)`
- `Unowned Observer (81)`

Authoritative emitted scenario labels:

- `owned_normal`
- `owned_observer`
- `unowned_observer`

Any references in this section to older buttons such as `Plain Probe`, `Owned Probe`, or `Rewrite EXP` should be treated as stale historical notes, not the active workflow.

- **"travel"** â€” full MapTest bot tree (original working approach)
- **"test ready block"** â€” enables `block_ready_to_play`, sends travel
- **"test redirect block"** â€” enables `block_redirect_to_target`, sends travel

Current active surface in the cleaned widget:

- `Plain Probe (445)` Ã¢â‚¬â€ unowned observer baseline
- `Owned Probe (81)` Ã¢â‚¬â€ owned control path
- `Rewrite EXP (445)` Ã¢â‚¬â€ rollback rewrite experiment

### Debug Output Fields

`rtp_calls` / `rtp_blocked` / `rtp_active` â€” MsgSendReadyToPlay counters
`rdr_calls` / `rdr_hits` / `rdr_active` â€” redirect-to-target counters
`reason` / `action` â€” what each hook did on last call
`seq` / `handler` / `blocked` â€” hook call tracking
`mission` / `region_or_type` / `map_or_territory` â€” packet contents

`travel_redirect_log` Ã¢â‚¬â€ shared native redirect-event stream printed by `GodTools.py`

Additional debug fields now in active use:

- `travel_path_summary` - derived outcome line for `ready_to_play_sent`, `redirect_items_loop`, or `load_loop_after_rewrite`
- `load_info_path` - compact view of the observed `INSTANCE_LOAD_INFO` state sequence

- `packet_u32_00` ... `packet_u32_30` Ã¢â‚¬â€ raw packet preview for redirect/error handlers
- these fields were added specifically to classify the OnErrorRedirect packet family
- caller_label / caller_va / caller_return_address - identifies which code path emitted each redirect call

## 9. Key Insights

1. **MemZero at context+0x1FC** is the critical overwrite point. Each `GameRedirectMission` call destroys previous redirect state.
2. **Auth server notifies game server** â€” sending any redirect (even cancel) causes target game server to disconnect client. The disconnect is inevitable.
3. **MsgSendReadyToPlay blocking works** â€” prevents server from checking permissions, prevents OnErrorRedirect. But leaves player stuck in loading (GameEnterWorld never fires).
4. **Multiple MsgSendReadyToPlay paths** â€” blocking only the first call is insufficient; other paths trigger later.
5. **OnErrorRedirect fires during loading** â€” before GameEnterWorld. Server sends it independently of ready signal in some cases.
6. **GameRedirectMission hook can redirect errors back to target** â€” pending test.

Additional current insights:

- `unowned_observer` is the only scenario that currently triggers the fallback rollback.
- The rollback originates from the `MissionCliOnErrorRedirect -> GameRedirectMission` chain.
- `owned_normal` and `owned_observer` both reach `81` without the fallback tuple.
- After rollback rewrite, the client context can remain pinned to `445` without arriving.
- No successful rewritten run has yet produced `ctos_0090`.
- The synthetic `OnErrorRedirect` replay path is invalid because the error packet belongs to the `INSTANCE_REDIRECT` packet family, not the normal redirect-response family.
- The latest safe rewritten baseline is a repeatable loading loop: `INSTANCE_LOAD_INFO (1/2)` -> `INSTANCE_REDIRECT` -> `INSTANCE_LOAD_REQUEST_ITEMS`.

### 2026-06-14 Handover Notes

Treat the following as more authoritative than the older experimental notes above:

- The loaded DLL is confirmed by `travel_back_debug`:
  - `build_id=travel-re-2026-06-14-build-fingerprint-v1`
  - `build_cookie=0x26061401`
- `unowned_observer` on target `81` now has a complete confirmed chain:
  - forward seed: `MissionCliGameRedirectMission` return VA `0x00847DF0`
  - rollback commit: `MissionCliOnErrorRedirect` return VA `0x008492B4`
  - nested auth send: `GameRedirectMission -> NetGameClientGameRedirect` return VA `0x0084B827`
- The rollback tuple is measured, not inferred:
  - mission `249`
  - `meta_ptr=0x01330234`
  - `meta_game_type=0x0A`
  - `selector_out=3`
  - `GameRedirectMission(3, 249, 0xFFFFFFFD, 0, 0xFFFFFFFF)`
- The new owned-vs-unowned trace comparison is more important than the older rollback-only view.
- Successful `owned_observer` progression:
  - `game_join`
  - `joining_flag_set`
  - `pkt_instance_load_head`
  - `pkt_instance_load_info`
  - `map_data_received`
  - `pkt_map_update_current`
  - `ui_start_map_load`
  - `pkt_ready_for_map_spawn`
  - `pkt_spawn_point`
  - `ui_load_map_context`
  - `msg_send_ready_to_play`
  - `pkt_instance_loaded`
  - `ui_map_loaded`
  - `entered_world`
- Failing `unowned_observer` progression:
  - `game_join`
  - `joining_flag_set`
  - `pkt_instance_load_head`
  - `pkt_instance_load_info`
  - `map_data_received`
  - `pkt_instance_redirect`
  - `redirect_before_spawn_auth`
  - `pre_spawn_error_redirect_call`
  - `pre_spawn_error_redirect_result`
  - timeout / freeze / disconnect
- Packet-level divergence:
  - both paths send `0x00C1` and `0x0091`
  - only the successful path continues with:
    - `0x0088 INSTANCE_LOAD_REQUEST_SPAWN`
    - `0x0090 INSTANCE_LOAD_REQUEST_PLAYERS`
  - the failing path never emits either packet
- Important constraint from the trace diff:
  - at `map_data_received`, both paths still match on the currently logged high-signal fields:
    - `flags190`
    - `map230`
    - `state238`
    - `flags2A8`
    - join / redirect mission tuple
  - therefore the deciding state is likely in:
    - packet payload fields not yet logged deeply enough
    - context fields not yet included in the snapshot
    - or adjacent global state outside the current trace surface
- Conclusion:
  - `MissionCliOnErrorRedirect` is a symptom point after the real divergence
  - consuming it is too late to restore a valid handover
- Another agent should not spend time re-proving rollback origin or using stale widget labels as the main workflow.
- The highest-value remaining RE target is now the handover window between:
  - `pkt_instance_load_info` / `map_data_received`
  - and the first divergence at either `READY_FOR_MAP_SPAWN` or `INSTANCE_REDIRECT (0x0191)`

## 10. Entry-Point Analysis (2026-06-12)

The current pipeline now breaks into four distinct control surfaces:

1. **local initiation**
   - `IUi::MapSelect`
   - `MissionCliGameRedirectMission`
   - observer mode bypasses most front-end travel validation here

2. **redirect / join**
   - `MissionClient::GameRedirectMission`
   - `NetGameClientGameRedirect`
   - `MissionCliOnRedirect`
   - `MissionClient::GameJoin`
   - `NetGameClientGameJoin`

3. **load / ready**
   - `MissionCliOnLoadMap`
   - `MissionClient::PlayerLoadMap`
   - `MissionClient::MsgSendReadyToPlay`
   - `MissionClient::GameQueueReadyToPlay`

4. **post-check resolution**
   - success path: `MissionClient::GameEnterWorld`
   - failure path: `MissionCliOnErrorRedirect` -> `GameRedirectMission(..., mission, 0xFFFFFFFD, 0, 0xFFFFFFFF)`

### What Each Entry Point Can Actually Do

#### `IUi::MapSelect`

- only controls local travel initiation
- not the authoritative server permission gate
- observer mode already proves that bypassing local validation is not enough

#### `MissionClient::GameJoin`

Key behavior from decompilation:

- checks `MapIsCreated()`
- posts UI message `0x10000111`
- writes join fields at `+0x194..+0x1C4`
- calls `EventCliContextOnGameLoadMission`
- calls `NetGameClientGameJoin`

Implication:

- `GameJoin` seeds client-side join state and network join state
- it is not the final map-authorization gate
- spoofing `GameJoin` alone would still not fabricate the later server-approved world state

#### `MissionCliOnLoadMap` -> `MissionClient::PlayerLoadMap`

This is now the most important boundary in the entire pipeline.

`MissionCliOnLoadMap`:

- extracts map-file / spawn / angle data from the incoming server message
- calls `PlayerLoadMap(context, map_file_id, spawn, angle, flags, 1)`

`PlayerLoadMap`:

- resolves the map file id to a file path
- posts frame message `0x10000098`
- if local file/load conditions are satisfied:
  - either calls `MsgSendReadyToPlay()` directly
  - or defers with `GameQueueReadyToPlay()`
- if load cannot continue:
  - cleans up files / links
  - calls `MsgSendFailedToLoad()`

Implication:

- if there is a non-server bypass, it must cross this boundary somehow
- the current rewritten `445` path is getting stuck before any successful ready progression
- for the `81` unowned observer failure, this is now the main handover region to instrument before the redirect symptom appears

#### `MissionCliOnMapData`

New decompilation-confirmed behavior:

- writes incoming map-state fields into context:
  - `+0x2AC`
  - `+0x230`
  - `+0x238`
  - `+0x228`
  - `+0x22C`
- if packet field `param1 + 0x18` is non-zero:
  - sets observer flag `ctx[0x2A8] |= 0x10`
- always sets:
  - `ctx[0x190] |= 0x80`
- then calls `MissionClient::PlayerCheckLoginInit(context)`

Implication:

- `map_data_received` is not just a passive marker
- it is a concrete state-write boundary immediately before the owned/unowned split
- any ownership/security-sensitive handover state may be visible here or in what runs immediately after it

#### `MissionClient::GameQueueReadyToPlay`

Decompilation shows this is only:

- `DAT_ram_005a404c = 1`

This is critical because it proves the deferred ready path is real and flag-driven, not magic.

#### `MissionClient::OnNetMsg`

This is the consumer for the queued-ready flag.

Relevant decompilation facts:

- it handles several mission-client network message ids
- on one branch (`0xD7` / `0xD8` handling), it checks two globals:
  - `DAT_ram_005a4048`
  - `DAT_ram_005a404c`
- when the queued-ready flag is set and the message-connection still exists:
  - it clears `DAT_ram_005a404c`
  - it calls `MissionClient::MsgSendReadyToPlay()`

Implication:

- there are at least two real `MsgSendReadyToPlay` paths:
  - direct from `PlayerLoadMap`
  - deferred from `OnNetMsg` after `GameQueueReadyToPlay()`
- this explains why blocking only the first ready call was never enough
- this also gives us a concrete instrumentation / interception target beyond packet sniffing

### Observer Alternate Path

The observer path is deeper than previously documented:

- `MissionClient::MsgSendObserveGetList()` sends opcode `0x8F`
- `MissionClient::MsgSendObserveGame(game_id)` sends opcode `0x8E`
- the game also maintains `MissionClient::CObserveTable`

Implication:

- there is a real alternate observer protocol path
- but it depends on server-seeded observe-table state, not just a synthetic local redirect
- this remains the best candidate for an alternate legitimate protocol path, but not a trivial offline spoof

### Current Feasibility Assessment

#### Prevent the server check entirely

Possible mechanically:

- block all `MsgSendReadyToPlay` paths

But current evidence says:

- this prevents the check
- it does not produce arrival
- the client remains stuck before `GameEnterWorld`

#### Fully synthetic travel without the normal flow

Possible only in theory, but much larger than the current project scope.

To replace the normal flow, we would need to synthesize at least:

- redirect state
- join state (`GameJoin` inputs including net address and token)
- load-map state
- likely later world/spawn state as well

Conclusion:

- a pure local synthetic-travel bypass is currently low-probability
- the more realistic research paths are:
  - instrument / intercept the deferred-ready consumer in `OnNetMsg`
  - compare pre-spawn handover state across owned vs unowned observer loads
  - investigate whether the observer `0x8E` / `0x8F` path can produce a server-accepted route to the target

## 10. Files

| File | Purpose |
|------|---------|
| `Py4GW\vendor\gwca\Source\MapMgr.cpp` | Hooks, toggles, debug counters, shared redirect log |
| `Py4GW\vendor\gwca\Include\GWCA\Managers\MapMgr.h` | Public API |
| `Py4GW\src\Py4GW_UI.cpp` | Python bindings for `map_test_*`, travel debug, and redirect logs |
| `Py4GW_python_files\GodTools.py` | Bot-tree launcher plus RE probes, packet capture, travel debug UI, redirect-log output |
| `.opencode/projects/re/map-travel/` | Full project pool + status |

## 11. Addendum: Current Surface and Binding Names (2026-06-12)

This section supersedes older references in this file that mention `travel_test(...)`, `PyUIManager.UIManager.get_travel_test_*()`, or a standalone GodTools travel button.

### Native Python Binding Names

The active build exposes the cancel-travel-back harness through `Py4GW.UI.UI`, not through `PyUIManager.UIManager`.

Actual exported methods from `src/Py4GW_UI.cpp`:

- `map_test_start(map_id, alt_map_id, number, count, delay_ms, timeout_ms, message_id)`
- `map_test_stop()`
- `get_map_test_status()`
- `is_map_test_active()`
- `get_map_test_count()`

These call into `GW::Map::MapTestStart/Stop/GetStatus/IsActive/GetCount` in native code.

### GodTools.py Runtime Surface

Current runtime split:

- `tree.UI.draw_window()`
  - primary user-facing launcher
  - runs the original native MapTest retry harness
  - preserves the old behavior: travel, detect bad travel, wait, repeat until success
- `_draw_debug_window()`
  - supplementary RE panel only
  - contains:
    - `Plain Probe (445)`
    - `Owned Probe (81)`
    - `Rewrite EXP (445)`
    - `Start Capture` / `Stop + Dump`
    - `Dump Focused` / `Clear Buffers`
    - `Reset RE State`
    - `Monitor Travel Hook Debug` / `Print Travel Debug`

### Current Testing Model

- Use the bot-tree path for the real cancel-travel-back harness.
- Use the debug window only for packet capture and targeted redirect experiments.
- Do not treat the debug window probes as replacements for the bot-tree workflow.

### Current Conclusions

- The native cancel-travel-back harness remains the only known working approach for the original retry race.
- For unowned observer travel to `445`, rewriting the rollback-shaped `GameRedirectMission` call can keep local redirect context pinned to `445`, but still does not complete arrival.
- The synthetic `OnErrorRedirect` continuation path is still considered invalid.
- The highest-value next RE targets remain:
  - `GameJoin` early-return conditions
  - queued/deferred `MsgSendReadyToPlay` progression
  - the transition from repeated `INSTANCE_LOAD_REQUEST_ITEMS` to the missing `0x0090`

---

## 12. Complete Arrival Pipeline (20 Stages) [VERIFIED: 2026-06-12]

All 20 stages confirmed via WASM decompilation as of 2026-06-12.

| Stage | Function | WASM Address | Description |
|-------|----------|-------------|-------------|
| 1 | `IUi::MapSelect` / `MissionCliObserveGame` | `ram:80fc49cb` / `ram:80c9a52f` | Travel dispatch bifurcation |
| 2 | `MissionClient::GameRedirectMission` | `ram:80ce1ad1` | Sends 0x25/0x29 to auth server |
| 3 | `MissionCliOnRedirect` | `ram:80ca3ac2` | Receives redirect + NetAddress |
| 4 | `MissionClient::GameJoin` | `ram:80ce01aa` | Universal join point |
| 5 | `NetGameClientGameJoin` | `ram:80d0d78a` | Connects to game server |
| 6 | `MissionCliOnLoadMap` | `ram:80ca1b5b` | Receives spawn + time |
| 7 | `MissionClient::PlayerLoadMap` (step 1) | `ram:80ceea7b` | Sends kLoadMapContext |
| 8 | `MissionClient::PlayerLoadMap` (step 2) | `ram:80ceea7b` | FileFindHardLinks validation |
| 9 | `MissionClient::PlayerLoadMap` (step 3a) | `ram:80ceea7b` | MsgSendReadyToPlay (direct) |
| 10 | `MissionClient::GameQueueReadyToPlay` | `ram:80cdee52` | Defers ready-to-play |
| 11 | `MissionClient::OnNetMsg` (0xD7/0xD8) | `ram:80cdef95` | Consumes queued ready |
| 12 | `MissionClient::MsgSendReadyToPlay` | `ram:80ce82ce` | Sends 0x90 packet |
| 13 | `MissionCliOnMapData` | `ram:80ca22df` | Sets metadata + observer flag |
| 14 | `CharCliOnMapInitStart` | `ram:80c1c9e2` | Map bounds allocation |
| 15 | `CharCliOnMapInit` | `ram:80c1bd0e` | Compressed map data chunks |
| 16 | `CharCliOnMapInit` | `ram:80c1bd0e` | Decompression trigger |
| 17 | `MissionCliOnEnterWorld` | `ram:80ca093e` | Gate check â†’ GameEnterWorld |
| 18 | `MissionClient::GameEnterWorld` | `ram:80ce0cdb` | ENTERED_WORLD commitment |
| 19 | `MissionClient::MsgSendFailedToLoad` | `ram:80ce7d98` | File not found fallback |
| 20 | `MissionClient::Disconnect` | `ram:80cdff99` | Cascade disconnect |

---

## 13. All 7 Travel Paths [VERIFIED: 2026-06-12]

### Path A: Normal (World Map)
```
IUi::MapSelect â†’ PartyCliTravelMission â†’ GameRedirectMission â†’ OnRedirect â†’ GameJoin
```
Checks: territory (`GmTerritoryCanTravel`), party consent, mission_locked, tag_flags.

### Path B: Observer-Bypass (Normal dispatch, reduced checks)
```
IUi::MapSelect â†’ if MissionCliIsObserver() â†’ SKIP PartyCliTravelMission â†’ GameRedirectMission
```
Same auth+redirect pipeline, skips party/territory checks.

### Path C: Observer-Alt (0x8E protocol)
```
MissionCliObserveGame â†’ MsgSendObserveGame(0x8E) â†’ Server 0x1D â†’ OnNetMsg â†’ GameJoin
```
Skips auth server entirely. Converges at GameJoin.

### Path D: Reconnect Travel (BYPASSES AUTH SERVER)
```
IUi::CompleteLogin â†’ if createParams & 2 â†’ GameRedirectReconnectValidate â†’ GameRedirectReconnect â†’ ReadReconnectData(0x0B) â†’ GameJoin DIRECTLY
```
NO auth server redirect. Reads saved reconnect data from archive file 0x0B.

### Path E: Travel-on-Login (0xB2 packet)
```
PartyCliTravelMissionLogin â†’ MsgSendTravelMissionLogin â†’ sends [0xB2 | param] packet
```

### Path F: Sentinel Redirect (0xFFFFFFFD)
```
IUi::MapSelect type=2 â†’ GameRedirectMission(1, 0, 0xFFFFFFFD, 0, 0xFFFFFFFF)
```
Error recovery sentinel territory.

### Path G: GM Within-Map Teleport
```
CWorldMap::OnFrameMsgKeyDown (Ctrl+Shift+T) â†’ CharCliPlayerOrderTeleport
```
Within current map only. Gated on `MissionCliIsGameMaster()`.

---

## 14. Verified Context Flags Map [VERIFIED: 2026-06-12]

### Offset 0x400 (Game State)

| Mask | Name | Set By | Cleared By |
|------|------|--------|------------|
| 0x01 | LOADED_ONCE | `PlayerCheckLoginInit` | `Context::Reset` |
| 0x02 | LEAVING | `GameLeave` | `Context::Reset` |
| 0x08 | ENTERED_WORLD | `GameEnterWorld` | `Context::Reset` |
| 0x10 | REDIRECT_RECEIVED | `MissionCliOnRedirect` | `Context::Reset` |
| 0x20 | JOINING | `GameJoin` | `Context::Reset` |
| 0x40 | LOGIN_INIT_REQUIRED | `OnNetMsg` (0x1E, 0x1F) | â€” |
| 0x80 | MAP_DATA_RCVD | `MissionCliOnMapData` | `Context::Reset` |
| 0x200 | REDIRECTING | `GameRedirectMission` | `Context::Reset` |

### Offset 0x2A8 (Privilege Flags)

| Bit | Mask | Name | Check Function | Set By |
|-----|------|------|---------------|--------|
| 0 | 0x01 | BASE_FLAG | â€” | `MissionCliOnAccessRights` |
| 1 | 0x02 | CONNECTED | `MissionCliIsConnected()` â†’ `(ctx[0x2a8]>>1)&1` | `MissionCliOnAccessRights` |
| 2 | 0x04 | DEVELOPER | `MissionCliIsDeveloper()` â†’ `(ctx[0x2a8]>>2)&1` | `MissionCliOnAccessRights` |
| 3 | 0x08 | GAME_MASTER | `MissionCliIsGameMaster()` â†’ `(ctx[0x2a8]>>3)&1` | `MissionCliOnAccessRights` |
| 4 | 0x10 | OBSERVER | `MissionCliIsObserver()` â†’ `(ctx[0x2a8]>>4)&1` | `MissionCliOnMapData` |

### Offset 0x2A8 Access Rights Mapping

`MissionCliOnAccessRights` reads server packet[4] and maps:
- Packet bit 0 â†’ `ctx[0x2a8]` bit 0 (BASE_FLAG)
- Packet bit 1 â†’ `ctx[0x2a8]` bit 2 (DEVELOPER)
- Packet bit 2 â†’ `ctx[0x2a8]` bit 3 (GAME_MASTER)

Bits 1 and 4 are set by separate handlers:
- Bit 1 (CONNECTED) also set by `OnNetMsg` (0x1E)
- Bit 4 (OBSERVER) set by `MissionCliOnMapData` from packet[0x18]

---

## 15. The Arrival Gate: MissionCliOnEnterWorld [VERIFIED: 2026-06-12]

The sole caller of `GameEnterWorld`. Location: `ram:80ca093e` (428 bytes).

### Gate Logic

Two conditions, either is sufficient:

1. **`ctx[0x238] != 0`** â€” map metadata present (set by `MissionCliOnMapData`, packet[0x0C])
2. **`ctx[0x2A8] & 0x10`** â€” observer flag set (set by `MissionCliOnMapData`, packet[0x18])

If **NEITHER** is true, `GameEnterWorld` is NOT called â€” arrival is blocked.

### Pseudocode

```python
def OnEnterWorld(packet, dispatchParam):
    context = PropGet(0x11)  # EProp::MissionClient

    # GATE CHECK
    if context[0x238] != 0:              # Map metadata present?
        pass  # proceed
    elif (context[0x2a8] & 0x10) != 0:   # Observer flag set?
        pass  # proceed (uses context for prefetch)
    else:
        return EARLY                     # ðŸš« DENIAL: neither flag set

    ManifestStartPrefetch(context)        # Start content download
    GameEnterWorld(context)               # ðŸŽ¯ Commit arrival
```

### Key Insight

The observer flag acts as a bypass: if `ctx[0x2A8] & 0x10` is set, the `ctx[0x238] != 0` check is skipped entirely. This means observer-mode travel has a different gating path than normal travel.

### 2026-06-14 Correction

Fresh decompilation of `MissionCliOnEnterWorld` shows the section above is incomplete.

- `ctx[0x238] != 0` and observer bit `0x10` are still fast-path conditions.
- But if neither is set, the function does not simply hard-fail.
- It calls `MissionClient::ManifestStartPrefetch(context)` and can still proceed into `GameEnterWorld(context)` if that path does not suspend.

Practical implication:

- `ctx[0x238]` / observer bit are not the full explanation for arrival success or failure.
- This matches the owned-observer runtime trace, which still reached `entered_world` while the logged snapshot showed:
  - `state238=0`
  - no observer bit `0x10` in `flags2A8`
- Therefore the unowned-observer failure point is still earlier than `MissionCliOnEnterWorld`, in the missing progression to `READY_FOR_MAP_SPAWN` and the absent `0x0088` / `0x0090` follow-up.

### 2026-06-14 Static Handoff Clarification

Additional Ghidra work narrows the unresolved gate further:

- `MissionCliOnLoadMap` at `ram:80ca1b5b`
  - copies the spawn/time payload from the mission packet
  - computes the load timing delta
  - calls `MissionClient::PlayerLoadMap(context, map_id, spawn_point, angle, region, 1)`
- `MissionClient::PlayerLoadMap` at `ram:80ceeb00`
  - resolves the map file path
  - posts UI message `0x10000098`
  - if local load conditions are satisfied, it sends `MsgSendReadyToPlay()` (`0x0090`) or defers through `GameQueueReadyToPlay()`
  - otherwise it deletes any temporary hardlinks and sends `MsgSendFailedToLoad()` (`0x008C`)
- `MissionCliOnMapData` at `ram:80ca22df`
  - seeds `ctx+0x228/0x22c/0x230/0x238/0x2ac`
  - mirrors `0x230 -> 0x234` and `0x238 -> 0x23c` when packet[0x18] is zero
  - otherwise sets observer bit `ctx[0x2a8] |= 0x10`
  - sets `ctx[0x190] |= 0x80`
  - immediately calls `MissionClient::PlayerCheckLoginInit(context)`
- `MissionClient::PlayerCheckLoginInit` at `ram:80cee800`
  - returns unless `(ctx[0x190] & 0xC0) == 0xC0`
  - if `(ctx[0x190] & 1) != 0`, sends `0x0089`
  - otherwise sends the language request packet, which matches the observed `0x0091`

What this rules out:

- `0x0088 INSTANCE_LOAD_REQUEST_SPAWN` is not emitted by `MissionCliOnLoadMap`
- `0x0088` is not emitted by `MissionCliOnMapData`
- `0x0088` is not emitted by `PlayerCheckLoginInit`

So the current unresolved boundary is now explicit:

- the good path has already crossed out of the mission setup slice before `0x0088` appears
- the failing path dies before that boundary is reached
- the live handoff target is the transition between:
  - mission-side setup (`OnLoadMap`, `OnMapData`, `PlayerCheckLoginInit`)
  - and the later spawn/map-init side that eventually consumes `READY_FOR_MAP_SPAWN` and `SPAWN_POINT`

The likely downstream consumers already identified in Ghidra are:

- `CharCliOnMapInitStart_Coord2u_const___unsigned_int_` at `ram:80c1c9e2`
  - stores the initial map bounds / allocation state
  - reallocates the compressed map buffer if needed
- `CharCliOnMapInit_unsigned_int__unsigned_long_const__` at `ram:80c1bd0e`
  - appends compressed map chunks into the allocated buffer
  - triggers `DecompressMap__()` once the full payload has arrived

This does not yet prove which packet number calls those `CharCli` handlers, but it does prove the mission-side branch we were instrumenting is already exhausted before the missing `0x0088` step.

---

## 16. Reconnect Travel Bypass [VERIFIED: 2026-06-12]

The reconnect path reads saved data from archive file 0x0B (0x49 bytes) and calls `GameJoin()` directly, bypassing the entire auth server redirect chain.

### ReconnectData Format (0x49 bytes)

| Offset | Size | Field | Notes |
|--------|------|-------|-------|
| 0x00 | 1 | version | Must be 0x01 |
| 0x01 | 4 | build_id | Must match `BuildId()` |
| 0x05 | 51 | mission_data | Context state from last `GameEnterWorld` (offsets 0x194â€“0x1C0) |
| 0x38 | 16 | guid | 4Ã— uint32 character GUID |
| 0x41 | 4 | timestamp | UTC minutes since 2001 |
| 0x45 | 4 | crc32 | CRC32 over bytes 0x00â€“0x44 |

### Validation Chain (all client-side, forgeable)

1. `version == 1`
2. `build_id == BuildId()` (global constant)
3. `CRC32(0, data, 0x45) == stored_crc32` (standard IEEE 802.3, reflected polynomial, table at `ram:001317e0`)
4. `timestamp` within 11 minutes of current time UTC

### Trigger

`IUi::CompleteLogin` checks `(*UiGetCreateParams() & 2)`. If set:

```
â†’ GameRedirectReconnectValidate(GUID) â€” checks reconnect GUID matches
â†’ if valid â†’ GameRedirectReconnect()
  â†’ ReadReconnectData() â†’ GameJoin() directly
```

`UiGetCreateParams()` returns `&DAT_ram_005a8770` (global).

### Functions Involved

| Function | WASM Symbol | WASM Address |
|----------|-------------|-------------|
| `ReadReconnectData` | `MissionClient::ReadReconnectData` | `ram:80ce0fbe` |
| `GameRedirectReconnect` | `MissionClient::GameRedirectReconnect` | `ram:80ce22e5` |
| `GameRedirectReconnectValidate` | `MissionClient::GameRedirectReconnectValidate` | `ram:80ce2665` |
| `CompleteLogin` | `IUi::CompleteLogin` | `ram:80fc7ec0` |
| `CRC32` | `crc32` | `ram:80036914` |

### Exploit Potential

If we can:
1. Write arbitrary reconnect data to archive file 0x0B (0x49 bytes, CRC32 + GUID + timestamp)
2. Force the reconnect GUID validation to pass
3. Set `createParams` bit 2

We could force `GameJoin()` with ANY map_id, EMission, and NetAddress. The reconnect data contains the full game server address + mission params. The CRC32 and GUID check are the only guards â€” **both are client-side and forgeable**. This is the highest-ranked exploit vector.

---

## 17. Client-Side Travel Bypass via Direct Function Call (2026-06-12)

`MissionCliGameRedirectMission` at `0x00847dd0` is the simplest callable entry point for programmatic travel from injected code. It bypasses ALL world-map UI checks including territory validation, party consent, mission-locked flags, and tag_flags.

### Entry Point

**Function**: `MissionCliGameRedirectMission`  
**EXE**: `0x00847dd0`  
**WASM**: `ram:80c9990c`  
**Prototype**: `void(uint gameType, EMission mission, ETerritory territory, uint district, ELanguage language)`  
**Self-contained**: fetches context via `PropGet(0x11)` â€” no context pointer argument needed

### Python NativeFunction Usage

```python
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction
from Py4GWCoreLib.native_src.internals.prototypes import Prototypes
from Py4GWCoreLib.Game import Game

Travel = NativeFunction.from_address(
    name="MissionCliGameRedirectMission",
    address=0x00847dd0,
    prototype=Prototypes["Void_U32_U32_U32_U32_U32"],  # 5Ã— uint32
)

# In a frame-safe context:
def travel_direct(mission_id, territory=0xFFFFFFFD, game_type=1):
    Game.enqueue(Travel, game_type, mission_id, territory, 0, 0xFFFFFFFF)
```

### Known Working Sentinel Call

```python
Travel(1, 0, 0xFFFFFFFD, 0, 0xFFFFFFFF)
# gameType=1, EMission=0, ETerritory=sentinel, district=0, ELanguage=any
```

This is identical to what `IUi::MapSelect` does as a type-2 error-recovery fallback. Territory `0xFFFFFFFD` tells `NetGameClientGameRedirect` to use the currently cached territory rather than a specific one.

### What Checks Are Bypassed

| Check | Normal World-Map Path | Direct Call |
|-------|----------------------|-------------|
| `MapGetMissionTagFlags & 1` (tag_flags) | âœ… Enforced â€” blocks travel if unset | âŒ **SKIPPED** |
| `target_data[0x12] & 1` (mission_locked) | âœ… Enforced in `OnTravelAttempt` | âŒ **SKIPPED** |
| `GmTerritoryCanTravel` (territory validation) | âœ… Enforced in `IUi::MapSelect` | âŒ **SKIPPED** |
| Party leader consent (`PartyCliTravelMission`) | âœ… Enforced â€” server-coordinated | âŒ **SKIPPED** |
| `MissionCliIsConnected()` | âœ… Enforced | âŒ **SKIPPED** |
| `MissionCliIsCreatingCharacter()` | âœ… Enforced | âŒ **SKIPPED** |
| Observer-mode game type validation | âœ… Full mask check (`0x64004`) | ðŸŸ¡ **Minimal** (gameType â‰¤ 0x10 only) |
| Auth server redirect | âœ… `NetGameClientGameRedirect` | âœ… **SAME** |

### Territory Mapping

| Territory | Region | Guild Hall Access? | Notes |
|-----------|--------|--------------------|-------|
| 0â€“4 | 0 | Yes (0xFFFFFFFE sentinel) | Interchangeable within region |
| 5 | 6 | No | |
| 6 | 7 | No | |

Territories 0-4 are functionally equivalent â€” any will work for region 0 maps. The `GmTerritoryCanTravel` restriction (same-region only) is bypassed entirely by the direct call.

### GameType

- Valid range: â‰¤ 0x10 (the ONLY check enforced)
- Values sourced from `ConstGetMissionClientData(EMission)` â†’ `MissionClientData*` at offset `+0x0C`
- `MissionClientData` struct is 0x7C bytes Ã— 882 entries
- For most outposts: `gameType = 1`
- For guild halls: `gameType = 4`

### âš ï¸ Server-Side Validation Warning

**This bypass is client-side only.** The server still validates the redirect when it processes the auth server redirect packet (`0x25`/`0x29`). If the server rejects the map/territory combination:

1. Server sends `MissionCliOnErrorRedirect` with the mission code and territory `0xFFFFFFFD`
2. Client calls `GameRedirectMission(mission, 0xFFFFFFFD, 0, 0xFFFFFFFF)` â€” sends player back to fallback
3. Player arrives at default outpost for that territory

For unowned maps (maps the player doesn't own), the server will always reject via this error path. The most reliable approach combines this direct call with the existing cancel-race `MapTest` harness exposed through `Py4GW.UI.UI.map_test_*`.

### Bridging Method Used

String-anchoring from WASM assertion strings to their EXE counterparts:
- `"RedirectMission: %d %08x"` â†’ `FUN_0084b770` (GameRedirectMission) @ `0x0084b770`
- `"gameType < GAME_TYPES"` â†’ same function, confirms identity
- Caller of `FUN_0084b770` â†’ `FUN_00847dd0` (MissionCliGameRedirectMission) @ `0x00847dd0`
- `"index < arrsize(s_missionClientData)"` â†’ `FUN_005a6b00` (ConstGetMissionClientData) @ `0x005a6b00`

---

## 18. Pre-Spawn Handover Gate — Complete Analysis (2026-06-14)

EXE build: 06-14-2026 | Scope: Full pipeline from map download through spawn authorization — 3 parallel analysts converged with consensus.

### 18.1 Divergence Point — Confirmed

The server makes a single go/no-go decision: its response to `0x0088` (INSTANCE_LOAD_REQUEST_SPAWN), sent by `MsgSendAckAggregate` after map download completes.

```
                    === SERVER DECISION (authenticated by TCP session) ===
                                    |
            ┌───────────────────────┴───────────────────────┐
            ▼ OWNED                                          ▼ UNOWNED
  Server → 0xD6 (ready gate)                      Server → 0x0191 (INSTANCE_REDIRECT)
  Server → 0x01AB (READY_FOR_MAP_SPAWN)            OnErrorRedirect @ 0x00849230
  Server → 0x0195 (SPAWN_POINT data)               GameRedirectMission(fallback 249)
  Server → 0x0196/0x0197/0x0198 (OnLoadMap)        ⛔ 0x0108195C NEVER SET
  PlayerLoadMap → MsgSendReadyToPlay → {0x90}       ⛔ No 0x0090 → no arrival
  GameEnterWorld ✅
```

**G3 confirmed**: The LoadMap packet chain (0x0195→0x0196→0x0197→0x0198) NEVER arrives for unowned observer. The server replaces the entire spawn authorization pipeline with a single `0x0191`.

### 18.2 Complete Packet Catalog (CToS, 0x80-0x9F Range)

| Packet | Name | EXE Sender | EXE Address | Size | Called By |
|--------|------|------------|-------------|------|-----------|
| **0x88** | INSTANCE_LOAD_REQUEST_SPAWN | `MsgSendAckAggregate` | `0x0084CDB0` | 4 bytes | `OnDownloadComplete` @ `0x0084CC60` |
| **0x89** | ACK_CREATION_DATA_BEGIN | `MsgSendAckCreationDataBegin` | `0x0084CDE0` | 4 bytes | `PlayerCheckLoginInit` (LOADED_ONCE) |
| **0x8C** | FAILED_TO_LOAD | `MsgSendFailedToLoad` | `0x0084CEA0` | 4 bytes | `PlayerLoadMap` Path A |
| **0x8E** | OBSERVE_GAME | `MsgSendObserveGame` | TBD | 8 bytes | `MissionCliObserveGame` |
| **0x8F** | OBSERVE_GET_LIST | `MsgSendObserveGetList` | TBD | 4 bytes | Observer init |
| **0x90** | INSTANCE_LOAD_REQUEST_PLAYERS | `MsgSendReadyToPlay` | `0x0084CF80` | 20 bytes | `PlayerLoadMap` (direct) or `OnNetMsg` 0xD7/D8 (deferred) |
| **0x91** | REQUEST_LANGUAGE | `MsgSendRequestLanguage` | `0x0084CFD0` | 12 bytes | `PlayerCheckLoginInit` (first-time) |

### 18.3 Function Address Catalog (06-14-2026 EXE)

| Function | EXE Address | WASM Address | Role |
|----------|-------------|-------------|------|
| **OnDownloadComplete** | `0x0084CC60` | `ram:80ce4f78` | 2-state machine; calls `MsgSendAckAggregate` → sends 0x88 |
| **MsgSendAckAggregate** | `0x0084CDB0` | `ram:80ce781e` | Sends `{0x88}` (4 bytes) |
| **MsgSendReadyToPlay** | `0x0084CF80` | `ram:80ce82ce` | Sends `{0x90, GUID}` (20 bytes) |
| **MsgSendRequestLanguage** | `0x0084CFD0` | `ram:80ce8546` | Sends `{0x91, lang1, lang2}` (12 bytes) |
| **MsgSendAckCreationDataBegin** | `0x0084CDE0` | `ram:80ce7a25` | Sends `{0x89}` (4 bytes) |
| **MsgSendFailedToLoad** | `0x0084CEA0` | `ram:80ce7e62` | Sends `{0x8C}` (4 bytes) |
| **PlayerLoadMap** | `0x0084E290` | `ram:80ceea7b` | 4-path decision: A(0x8C), B(silent), C(defer), D(direct 0x90) |
| **PlayerCheckLoginInit** | `0x0084E210` | `ram:80cee800` | Guard: `(ctx[0x190]&0xC0)==0xC0`; sends 0x89 or 0x91 |
| **GameQueueReadyToPlay** | `0x0084B650` | `ram:80cdee52` | Sets `0x01081964 = 1` |
| **GameIsPlayingAd** | `0x0084B4E0` | `ram:80cdee41` | Returns `0x0108195C` |
| **OnNetMsg** | `0x0084BA40` | `ram:80cdef95` | Dispatches 0x1D/0x1E/0x1F/0xD6/0xD7/0xD8 |
| **MissionCliOnLoadMap** | `0x00849400` | `ram:80ca1b5b` | Handles 0x0196/0x0197/0x0198; calls PlayerLoadMap with param6=1 |
| **InstanceLoadFile handler** | `0x008493C0` | — | Handles 0x0195 (spawn point data) — newly discovered |
| **CharCliOnMapInitStart** | `0x00811B10` | `ram:80c1c9e2` | Allocates compressed map buffer |
| **CharCliOnMapInit** | `0x0080C250` | `ram:80c1bd0e` | Accumulates map chunks → DecompressMap |
| **EventCliContextOnGameLoadMission** | `0x00626010` | — | Asserts if TLS+0x0C NULL (GameJoin crash point #1) |
| **GuildCliGetSequence** | `0x0083A5B0` | — | TLS+0x3C→+0x2A4 double deref (crash point #2) |
| **GameJoin** | `0x0084B4F0` | `ram:80ce01aa` | 9 params; crashes from stable map state (G9 diagnosed) |
| **CPrefetchCache::Mark** | `0x0084CBA0` | `ram:80ce43a0` | Mark mission in prefetch cache |
| **CPrefetchCache::Export** | `0x0084C2A0` | `ram:80ce2c94` | Export prefetch cache |

### 18.4 Two-Global System

| Global | EXE Address | Set By | Cleared By | Purpose |
|--------|-------------|--------|------------|---------|
| Ready Gate | `0x0108195C` | OnNetMsg 0xD6 handler | Never explicitly | Server says "map data complete, wait for 0xD7/D8" |
| Queued Ready | `0x01081964` | `GameQueueReadyToPlay()` | OnNetMsg 0xD7/D8 handler | Client has map but waiting for ad/deferred condition |

### 18.5 PlayerLoadMap Complete Decision Tree

```
PlayerLoadMap(context, map_id, MapPoint*, angle, param5, param6):

  STEP 1 — FileConvertIdToPath(map_id)
  STEP 2 — FrameMsgSendRegistered(0x10000098, &struct)  // kLoadMapContext
  STEP 3 — IF result == 0: MsgSendFailedToLoad(0x8C) + cleanup → RETURN  ⛔ PATH A
  STEP 4 — IF param6 == 0: → RETURN                                      ⛔ PATH B
           (param6 is HARDCODED to 1 from MissionCliOnLoadMap)
           (param6 is 0 only from MissionCliOnReconnect)
  STEP 5 — IF GameIsPlayingAd() != 0: GameQueueReadyToPlay() → RETURN    ⏸️ PATH C
           (later: OnNetMsg 0xD7/D8 checks both globals → MsgSendReadyToPlay)
  STEP 6 — MsgSendReadyToPlay() → NETWORK SEND                            ✅ PATH D
```

### 18.6 OnMapData Context Field Map

| Context Offset | Source | Condition | Meaning |
|---|---|---|---|
| +0x2AC | packet[4] | Unconditional | Map instance ID |
| +0x230 | packet[8] | Unconditional | Mission ID |
| +0x238 | packet[0xC] | Unconditional | Mission map |
| +0x228 | packet[0x10] | Unconditional | — |
| +0x22C | packet[0x14] | Unconditional | — |
| +0x234 | mirror of 0x230 | IF `packet[0x18] == 0` | Normal mode mirror |
| +0x23C | mirror of 0x238 | IF `packet[0x18] == 0` | Normal mode mirror |
| +0x2A8 bit 0x10 | OBSERVER | IF `packet[0x18] != 0` | Observer flag SET |
| +0x190 bit 0x80 | MAP_DATA_RCVD | Unconditional | — |

### 18.7 PlayerCheckLoginInit Guard

```
PlayerCheckLoginInit(ctx):
  IF (ctx[0x190] & 0xC0) != 0xC0 → RETURN
    (needs bit 0x40 from OnNetMsg 0x1E + bit 0x80 from OnMapData)
  IF (ctx[0x190] & 1) != 0 → MsgSendAckCreationDataBegin → {0x89}
  ELSE → MsgSendRequestLanguage(lang1, lang2) → {0x91}
```

On observer path: 0x1E handler calls `GameJoin(param9=1)` instead of setting bit 0x40 → PlayerCheckLoginInit guard fails → returns immediately.

### 18.8 OnNetMsg Handler Dispatch

| Server Msg | Handler Action |
|-----------|----------------|
| **0xD6** | `0x0108195C = 1` — server says "map ready, wait for 0xD7/D8" |
| **0xD7** | IF `0x0108195C && 0x01081964` → clear 0x01081964 → `MsgSendReadyToPlay()` |
| **0xD8** | Identical to 0xD7 (dual trigger for race-safety) |
| **0x1E** | IF normal: `ctx[0x190] \|= 0x40` + `PlayerCheckLoginInit`. IF observer: `GameJoin(param9=1)` |
| **0x1D** | Observer response. Status==0 → `GameJoin(param9=1)`. Error → redirect |

### 18.9 GameJoin Direct-Call Crash Diagnosis (G9)

Root cause: **Precondition violation** — GameJoin is designed for network TRANSITION state, not stable connected map state.

| Crash Point | Mechanism | SEH-Catchable? |
|-------------|-----------|:---:|
| `EventCliContextOnGameLoadMission` (0x00626010) | Asserts TLS+0x0C != NULL; creates Crash.dmp → TerminateProcess | ❌ |
| `GuildCliGetSequence` (0x0083A5B0) | NULL deref if TLS+0x3C NULL → ACCESS_VIOLATION | ✅ |
| GC object init (0x0048BDA0) | Sentinel check on DAT_00bfcfc4 → assertion | ❌ |

EXE GameJoin does NOT early-return on `MapIsCreated()==false` (unlike WASM version). Three fix options: A) call `NetGameClientGameLeave` first + clear context flags, B) use `MsgSendObserveGame(0x8E)` protocol instead, C) pre-sanitize context before call.

### 18.10 Implemented Tools (Python)

**`Py4GWCoreLib/native_src/methods/MapTravelBypassMethods.py`**:
- `send_ready_to_play()` — sends 0x90 directly via `MsgSendReadyToPlay` @ `0x0084CF80`
- `force_spawn()` — sets ready gate (`0x0108195C=1`) + sends 0x90 atomically
- `read_ready_gate()` / `write_ready_gate(value)` — global manipulation
- `get_status()` — diagnostic dict

### 18.10A Ownership Correction (2026-06-14)

The Python implementation above is now considered a misplaced prototype, not the target architecture.

Why this is a problem:

- it writes live game-state globals from `native_src`
- it duplicates authoritative travel/handover logic outside GWCA
- it splits the experiment across:
  - `MapMgr.cpp`
  - `Py4GW_UI.cpp`
  - `GodTools.py`
  - and now a separate Python-native method file
- that makes the real control flow and state ownership harder to audit during RE

Current project direction:

- **authoritative travel-bypass / handover logic belongs in C++**
  - `Py4GW\vendor\gwca\Source\MapMgr.cpp`
  - `Py4GW\vendor\gwca\Include\GWCA\Managers\MapMgr.h`
- **Python should only expose thin bindings**
  - `Py4GW\src\Py4GW_UI.cpp`
- **`GodTools.py` should remain a test harness / UI surface**
  - start probes
  - dump counters / logs
  - invoke exported C++ controls
- **`Py4GWCoreLib/native_src/methods/MapTravelBypassMethods.py` should not become the primary home**
  - it may remain temporarily as a record of the G8 experiment
  - but new handover work should not be implemented there first

Practical rule going forward:

- if a feature changes runtime handover behavior, touches packet timing, flips mission globals, or sends mission packets as part of this project, implement it in `MapMgr.cpp` first and only bind it upward after the C++ path is stable
- do not add new authoritative bypass behavior in Python-native wrappers

### 18.11 Remaining Open Gaps

| # | Gap | Status |
|---|-----|--------|
| G2 | kLoadMapContext (0x10000098) handler identity | Open |
| G4 | OnMapData EXE address | Open |
| G5 | OnNetMsg confirmed via WASM cross-ref | Open |
| G6 | Server criteria for 0x0191 vs 0xD6 | Black box |
| G7 | Full packet trace for owned_observer | Open |
| G8 | Server response to lone 0x90 | Prototype exists, but Python-side implementation is now considered architectural debt; migrate to C++ control path before further expansion |
| G9 | GameJoin crash fix via MsgSendObserveGame protocol | Needs `MsgSendObserveGame` EXE address |
| G10 | Observer flag effect on server 0x88 response | Open |
