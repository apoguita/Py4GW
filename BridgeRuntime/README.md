# Py4GW Bridge Runtime (Daemon + Injected Client + CLI)

This document explains the bridge infrastructure added for Py4GW and how to use it.

It is the runtime/operator document for the bridge stack:

- what the runtime components are
- how to run them
- how to use the daemon, widget client, and CLI
- what control/runtime behaviors are available

It is not the canonical full architecture document.

For the full explicit architecture model, use [docs/Py4GW_Conceptual_Model.md](/c:/Users/Apo/Py4GW_python_files/docs/Py4GW_Conceptual_Model.md).

The bridge lets you talk to **live injected Py4GW clients** from a normal Python process (outside injection) using a local TCP protocol.

It is designed for:

- AI-assisted scripting and code generation
- live runtime introspection
- multi-client orchestration
- stress testing / repeated action execution
- future MCP adapter integration

## Foundational Base

The bridge ultimately sits on top of the game process and the extraction mechanisms used to read from it:

- `Gw.exe`
- C++ binding-backed extraction
  - C++-backed primitives represented by forward declarations in the `stubs` folder
- Native function callers
  - Pure-Python primitives in `Py4GWCoreLib/native_src`

These are the foundational extraction mechanisms. They feed the Python-level source-of-truth libraries in `Py4GWCoreLib`.

The C++ binding-backed primitives and the native function callers are the same conceptual abstraction level implemented through different access paths. The project is migrating from C++-backed primitives to Python-native primitives.

When both primitive paths exist for the same domain, native primitives should be treated as the preferred implementation and C++-backed primitives as secondary.

For UI handling specifically, `PyImGui` stubs are the primitive source-of-truth interface. They should be treated as the low-level immediate-mode UI API, including core window/layout/widget primitives, IO/input state, UI enums/flags, interaction queries, and draw-list primitives. Higher UI-facing passes built on top of that are derivative, even when they remain important.

`ImGui_Py` is legacy and should not be referenced as part of the current conceptual model.

Additional foundational primitive systems also exist at this level:

- `PyScanner` for low-level memory positioning and function resolution used by `native_src`
- `PyPointers` for shared pointer access from C++ into `native_src`
- `PyCallback` for queued/sequenced execution through the library/C++ side
- `Py4GW` for miscellaneous low-level system functions such as window handling, logging, and client/window data
- `PyPathing` for primitive access to the in-game pathing system
- `PyKeystroke` for client-side keypress injection into the game
- `PyTrading` for primitive player-to-player trading flow
- `Py2DRenderer` as the primitive base of `DXOverlay`
- `PyOverlay` as the primitive base of `Overlay`

## Py4GWCoreLib Source-of-Truth Layer

Above the foundational extraction mechanisms, the project uses `Py4GWCoreLib` as the first authoritative Python-facing source-of-truth layer.

For project architecture, this is the single primary Python-facing source-of-truth layer.

This is where Py4GW semantics begin. `stubs` and `native_src` are primitives; `Py4GWCoreLib` is where project/library semantics start.

For UI semantics, this means modules such as `ImGui`, `DXOverlay`, `Overlay`, and `UIManager` are higher-level project-facing layers built on top of the lower-level `PyImGui` primitive interface.

This includes project-facing modules such as:

- `Agent` (typed per-entity property/introspection surface across living, item, and gadget agents)
- `AgentArray` (authoritative classified collection/query layer for world-entity sets)
- `Camera` (project-facing camera-state, camera-motion, and view-control layer over the lower-level `PyCamera` primitive surface)
- `CombatEvents` (combat telemetry plus derived combat-state and reactive callback layer)
- `Context` (typed native-context gateway over `native_src`, exposing structured context domains such as gameplay, world, map, party, cinematic, and pre-game state)
- `DXOverlay` (structured DirectX geometry/texture rendering engine)
- `Effect` (layered status-state plus buff/effect query and limited control surface)
- `ImGui` (higher-level themed UI toolkit over `ImGui_src`, including style/theme management, textured controls, and managed window modules above raw `PyImGui`)
- `Inventory` (bag/storage state, capacity accounting, and item-handling workflow/action layer)
- `Item` (per-item definition, properties, customization, and trade introspection layer)
- `ItemArray` (cross-bag item collection and item-set filtering/manipulation/sorting layer)
- `Map` (instance-state gatekeeper, travel/world-transition surface, and map UI/projection hub)
- `Merchant` (broader NPC trade/crafting/exchange transaction surface)
- `Overlay` (singleton drawlist/UI overlay composition layer)
- `Party` (group-composition state plus party/hero/henchman/pet management and control)
- `Pathing` (project-facing path-planning and route-shaping layer combining native `PyPathing` planning with custom navmesh/A* fallback, smoothing, and map-group caching)
- `Scanner` (structured project-facing binary scanning and address-resolution layer over `PyScanner`)
- `Player` (local-player identity, progression/title state, chat, and queued local actions)
- `Quest` (quest-log state plus staged quest-metadata retrieval interface)
- `Skill` (per-skill definition, metadata, and descriptive knowledge layer)
- `Skillbar` (active combat-loadout state and execution layer)
- `UIManager` (foundational UI frame/message orchestration layer)
- `Routines`
- `IniManager`
- `HotkeyManager`

These libraries are distinct from the foundational base. They consume or organize lower-level capabilities into the Python-facing surfaces commonly used by the bridge.

Within this layer, `Routines` should be treated as a middle-tier task/routine facade over the `routines_src` package. That package is split by both task family and execution style: guard checks, spatial/task helpers, transition helpers, blocking sequential flows, cooperative yield routines, and task-specific behavior-tree routines.

Within this same layer, `IniManager` should be treated as the higher-level multi-account configuration manager above the lower-level `IniHandler`, including account-specific vs global config paths and callback-driven deferred flushing.

Within this same layer, `HotkeyManager` should be treated as the project-facing runtime hotkey layer: it manages identified key/modifier bindings and dispatches callbacks from the embedded `PyImGui` input state.

## Combat Automation Layer

Above the core library, cache, and shared-memory coordination, the project has a combat automation layer built around two near-parallel systems:

- `Py4GWCoreLib.SkillManager.Autocombat` for single-account local combat automation
- `HeroAI.CombatClass` for the multibox/party-aware analog

Both use the same broad combat scheduler model:

- custom-skill metadata
- skill prioritization
- staged readiness checks
- tactical target selection
- cast-condition evaluation
- aftercast/ping-aware timing
- final skill dispatch through the skillbar

The main difference is context:

- `SkillManager` is the local single-account path
- `HeroAI` wraps the same logic in shared-memory-backed account caches, options, commands, and UI for coordinated multibox behavior

## Bot Orchestration Layer

Above combat automation, the project has a higher bot orchestration layer centered on `Py4GWCoreLib.Botting.BottingClass`.

This is the main automation-composition runtime:

- it owns a named `FSM`
- it builds configured bot step graphs through a main `Routine()`
- it schedules both normal FSM states and coroutine-backed self-managed yield steps
- it attaches long-lived managed background coroutines for upkeep/services
- it exposes grouped wrapper namespaces (`States`, `Move`, `Wait`, `Events`, `Items`, `Party`, `Target`, `Multibox`, etc.) that act as a bot-scripting layer over the scheduler

In practice:

- `Routines` provides reusable task units
- combat automation provides autonomous combat execution
- `Botting` sequences them into a full bot lifecycle with staged and reactive FSM-driven automation

## `py4gwcorelib_src` Support Infrastructure

Above the `Py4GWCoreLib` source-of-truth libraries, the project also uses complementary support infrastructure in `Py4GWCoreLib/py4gwcorelib_src`.

This is not another primitive layer and not another source-of-truth layer. It is shared Python-side infrastructure used by higher abstractions built on top of the source-of-truth modules.

Examples currently identified in this support layer include:

- `BehaviorTree` as a major decision/execution orchestration framework with composite, repeater, wait, decorator, and subtree node families for higher automation logic
- `FSM` as a major finite-state-machine orchestration framework with delayed steps, event transitions, sub-FSMs, and both global and FSM-managed coroutine step models
- `VectorFields` as orchestration-adjacent steering infrastructure that combines attraction/repulsion from agent arrays and custom positions into local movement vectors
- `WidgetManager` as a major callback-driven script orchestration layer for running multiple widgets/scripts through the callback system
- `ActionQueue` for serialized in-game action dispatch
- `Timer` / `ThrottledTimer` for shared timing and throttling infrastructure
- `MultiThreading` for thread lifecycle management and watchdog support
- `IniHandler` for INI-backed configuration infrastructure
- `Lootconfig_src` as specialized shared-file configuration infrastructure for synchronized loot-picking across accounts
- `Keystroke` for higher-level key and key-combo dispatch
- `AutoInventoryHandler` for timer-driven identify/salvage support automation
- `Utils` for miscellaneous shared conversions and helper functions
- `Profiling` as diagnostics/profiling infrastructure used by system-activity tooling
- `Color` for shared color conversion and mutation utilities
- `Console` as a thin interface into `Py4GW` console/system functions

## `GLOBAL_CACHE` Consumer Layer

`GLOBAL_CACHE` sits above `Py4GWCoreLib` and consumes those source-of-truth libraries.

It is desirable because it provides caching support, but it is optional. The bridge can validly expose either `Py4GWCoreLib` libraries directly or `GLOBAL_CACHE` projections.

When a corresponding cache getter exists, `GLOBAL_CACHE` should be preferred for read access. When no corresponding cache surface exists, direct `Py4GWCoreLib` access remains valid.

The same preference rule applies to actions and mutating operations when a corresponding cache-backed operation exists.

`GLOBAL_CACHE` is derivative of `Py4GWCoreLib`, not a parallel peer source-of-truth layer.

It is also a managed cache-runtime layer, not only a loose set of mirrors: the root `GlobalCache` singleton owns shared throttled update cadence, a shared action queue, and shared cache substrates such as the raw item cache.

Beyond the cache surfaces currently exposed by the bridge, the actual cache layer also includes additional important domains such as `Camera`, `Item`, `ItemArray`, `Trading`, and `Skill`.

## Shared Memory / Multiboxing Coordination Layer

In the multiboxing environment, multiple clients can be interacted with through a shared-memory-driven coordination layer.

This layer lives inside `GLOBAL_CACHE`, centered around shared memory support.

It supports multi-client interaction, provides pushed cross-account data so accounts can read data from other accounts, and handles account messaging. It also has a large typed `shared_memory_src` schema for account, agent, party, map, quest, skillbar, title, and message data. It should be treated as a coordination layer built on top of the data-access stack.

## Components

### 1. Injected Bridge Client (widget)

Current widget path in this repo:

- `Widgets/Coding/Tools/Bridge Client.py`

This runs inside each injected GW/Py4GW client and:

- connects to the daemon over TCP
- executes requests on the injected/runtime side
- exposes selected capabilities from the `Py4GWCoreLib` source-of-truth layer and `GLOBAL_CACHE` over TCP
- tracks async operations (queued actions, shmem commands)

The current bridge-facing handle into the shared memory / multiboxing coordination layer is the `shmem` namespace.

### 2. Bridge Daemon (server)

File:

- `bridge_daemon.py`

This runs outside injection and:

- accepts connections from multiple injected clients
- identifies clients by `HWND` (primary) and `PID` (fallback)
- exposes a control API for tools/CLI/MCP
- routes requests to a specific target client

### 3. Bridge CLI (tester/operator tool)

File:

- `bridge_cli.py`

This is a local CLI for testing and using the daemon without writing raw socket code.

## Architecture (brief)

```text
[bridge_cli.py / future MCP adapter]
            |
            v
      [bridge_daemon.py]
            |
   (routes by HWND / PID)
            |
            v
[Injected Bridge Client widget]  (one per GW client/account)
            |
            +--> binding-backed runtime surface
            +--> native migration surface
            +--> GLOBAL_CACHE-backed state and shared memory
```

## Protocol notes (implementation)

- Local TCP
- Length-prefixed JSON (4-byte little-endian length + UTF-8 JSON)
- Request/response protocol
- Immediate ack for async/queued operations + status polling

## Prerequisites

- Py4GW environment working (injection already working)
- Python (same Win32 Python runtime is recommended for consistency)
- At least one injected client with the bridge widget enabled

## Start the server (daemon)

Run outside injection:

```powershell
python bridge_daemon.py --token mytoken
```

Defaults:

- Widget ingress server: `127.0.0.1:47811`
- Control API server (CLI/MCP talks here): `127.0.0.1:47812`

Optional flags:

- `--widget-host`
- `--widget-port`
- `--control-host`
- `--control-port`
- `--token`

Example custom ports:

```powershell
python bridge_daemon.py --widget-port 50011 --control-port 50012 --token mytoken
```

## Connect the injected bridge client (widget)

In the Py4GW Widget Manager:

1. Enable `Bridge Client`
2. Set:
   - `Host`: `127.0.0.1`
   - `Port`: `47811`
   - `Token`: `mytoken`
3. Click `Apply Connection Settings`

The widget UI should show:

- connection status
- daemon endpoint
- `HWND`
- `PID`
- session id
- pending op count / request counts

## CLI quick start

The CLI talks to the daemon **control API** (default `47812`).

### Ping the daemon

```powershell
python bridge_cli.py ping
```

### List connected clients

```powershell
python bridge_cli.py list-clients
```

This returns connected injected clients with:

- `hwnd`
- `pid`
- `account_email`
- `character_name`
- session metadata

## Typical workflow

1. Start daemon
2. Connect one or more injected clients (via widget)
3. Get `HWND` from `list-clients`
4. Query data or call methods on that client using `bridge_cli.py request`

## CLI command reference

### `ping`

Ping the daemon.

```powershell
python bridge_cli.py ping
```

### `list-clients`

List all connected injected clients.

```powershell
python bridge_cli.py list-clients
```

### `namespaces`

List bridge namespaces available on a specific client.

The CLI uses the daemon control command `client.list_namespaces`, which normalizes the target client's `system.list_namespaces` response into a top-level control API result.

By `HWND` (preferred):

```powershell
python bridge_cli.py namespaces --hwnd 123456
```

By `PID` (fallback):

```powershell
python bridge_cli.py namespaces --pid 12340
```

### `commands`

List bridge command metadata available on a specific client.

The CLI uses the daemon control command `client.list_commands`, which normalizes the target client's `system.list_commands` response into a top-level control API result.

By `HWND` (preferred):

```powershell
python bridge_cli.py commands --hwnd 123456
```

By `PID` (fallback):

```powershell
python bridge_cli.py commands --pid 12340
```

### `request`

Send a bridge request to a target client.

```powershell
python bridge_cli.py request --hwnd 123456 --cmd player.get_state
```

Parameters:

- `--hwnd` or `--pid`
- `--cmd` bridge command
- `--params-json` JSON object for payload params
- `--request-id` optional custom request id
- `--poll` poll async status after request
- `--poll-timeout`
- `--poll-interval`

### `status`

Poll the status of a previously submitted async/queued request.

```powershell
python bridge_cli.py status --hwnd 123456 --tracked-request-id abc123
```

## First Safe Control Subset

The daemon now exposes a first stable, validated control-layer subset intended for higher-level tooling (including a future MCP adapter) to prefer over generic `client.request`:

- `client.describe_runtime`
- `client.get_map_state`
- `client.get_player_state`
- `client.list_agents`
- `client.list_namespaces`
- `client.list_commands`

These commands:

- resolve the target client at the daemon layer
- validate simple inputs where applicable
- return normalized top-level results
- keep the underlying bridge response attached for traceability

Use generic `client.request` for broader access, but prefer the validated subset when a matching control command exists.

## Testing plan (recommended)

Run these in order.

### 1. Infrastructure test

```powershell
python bridge_cli.py ping
python bridge_cli.py list-clients
```

Expected:

- daemon responds
- at least one client appears

### 2. Basic runtime state reads

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd player.get_state
python bridge_cli.py request --hwnd <HWND> --cmd map.get_state
python bridge_cli.py request --hwnd <HWND> --cmd agent.list --params-json "{\"group\":\"enemy\"}"
```

### 3. Namespace discovery

```powershell
python bridge_cli.py namespaces --hwnd <HWND>
```

### 4. Method introspection (whole layer)

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd player.list_methods
python bridge_cli.py request --hwnd <HWND> --cmd agent.list_methods
python bridge_cli.py request --hwnd <HWND> --cmd agent_array.list_methods
python bridge_cli.py request --hwnd <HWND> --cmd party.list_methods
python bridge_cli.py request --hwnd <HWND> --cmd inventory.list_methods
python bridge_cli.py request --hwnd <HWND> --cmd shmem.list_methods
```

### 5. Generic method calls (read-only first)

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd player.call --params-json "{\"method\":\"GetName\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd player.call --params-json "{\"method\":\"GetAgentID\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd map.call --params-json "{\"method\":\"GetMapID\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd agent_array.call --params-json "{\"method\":\"GetEnemyArray\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd party.call --params-json "{\"method\":\"GetPartyID\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd inventory.call --params-json "{\"method\":\"GetFreeSlotCount\",\"args\":[]}"
```

### 6. Curated queued action test (safe)

Travel example (polls until completion/timeout):

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd map.travel --params-json "{\"map_id\":55}" --poll
```

Skip cinematic (only when in cinematic):

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd map.skip_cinematic --poll
```

### 7. Async status polling (manual)

If you want to control request IDs yourself:

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd map.travel --params-json "{\"map_id\":55}" --request-id travel_test_001
python bridge_cli.py status --hwnd <HWND> --tracked-request-id travel_test_001
```

## Curated bridge commands (stable helpers)

These are explicitly implemented and useful for common tasks.

- `system.ping`
- `system.list_namespaces`
- `system.list_commands`
- `client.describe`
- `map.get_state`
- `player.get_state`
- `agent.list`
- `agent.get_info`
- `map.travel`
- `map.skip_cinematic`
- `ops.get_status`
- `shmem.send_command`

`system.list_namespaces` now returns both:

- `namespaces`: the ordered list of bridge namespace handles
- `details`: per-namespace metadata including source (`Py4GWCoreLib` vs `GLOBAL_CACHE`), kind (`corelib` vs `cache`), and whether the label is historically ambiguous

The daemon also exposes:

- `client.list_namespaces` for normalized namespace metadata at the control layer

`system.list_commands` returns structured command metadata including:

- `command`
- `access` (`read`, `write`, or `dynamic`)
- `safety` (`safe`, `guarded`, or `restricted`)
- `kind` (`curated` or `reflection`)
- `scope`
- optional `guards`

The daemon also exposes:

- `client.list_commands` for normalized command metadata at the control layer

## Bridge Namespaces (generic access)

The bridge exposes namespace projections via `<namespace>.list_methods` and `<namespace>.call`.

These names are bridge-facing handles. They are not the authoritative architectural layer definitions for the underlying library.

### Bridge namespaces mapped to `Py4GWCoreLib` source-of-truth libraries

- `map`
- `player`
- `agent`
- `agent_array`
- `party_raw`
- `party_corelib`
- `party_wrapper`
- `skill`
- `skillbar_raw`
- `skillbar_corelib`
- `skillbar_wrapper`
- `inventory_raw`
- `inventory_corelib`
- `inventory_wrapper`
- `quest_raw`
- `quest_corelib`
- `quest_wrapper`
- `effects_raw`
- `effects_corelib`
- `effects_wrapper`

### Bridge namespaces mapped to `GLOBAL_CACHE`

- `party`
- `party.players`
- `party.heroes`
- `party.henchmen`
- `party.pets`
- `skillbar`
- `inventory`
- `quest`
- `effects`
- `shmem`

In practical terms:

- `map`, `player`, `agent`, `agent_array`, `party_raw`, `skill`, `skillbar_raw`, `inventory_raw`, `quest_raw`, and `effects_raw` are bridge projections over `Py4GWCoreLib` source-of-truth libraries.
- Those `Py4GWCoreLib` libraries themselves sit above the foundational base (`Gw.exe` plus the primitive extraction paths).
- `party`, `party.players`, `party.heroes`, `party.henchmen`, `party.pets`, `skillbar`, `inventory`, `quest`, `effects`, and `shmem` are bridge projections over `GLOBAL_CACHE`.
- The `_raw` suffixes in bridge namespace names are historical bridge labels and do not mean the bridge is bypassing `Py4GWCoreLib` and exposing the lowest-level base directly.
- Preferred clear aliases are now `party_corelib`, `skillbar_corelib`, `inventory_corelib`, `quest_corelib`, and `effects_corelib`.
- Older compatibility aliases remain available: `party_wrapper`, `skillbar_wrapper`, `inventory_wrapper`, `quest_wrapper`, and `effects_wrapper`.
- These bridge namespaces are implementation handles for remote access, not a canonical statement of the full Py4GW architecture.

## Generic call examples by layer

### Player

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd player.call --params-json "{\"method\":\"GetXY\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd player.call --params-json "{\"method\":\"GetTargetID\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd player.call --params-json "{\"method\":\"IsPlayerLoaded\",\"args\":[]}"
```

### Agent / AgentArray

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd agent_array.call --params-json "{\"method\":\"GetAllyArray\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd agent.call --params-json "{\"method\":\"GetXY\",\"args\":[12345]}"
python bridge_cli.py request --hwnd <HWND> --cmd agent.call --params-json "{\"method\":\"IsDead\",\"args\":[12345]}"
```

### Party (cache/service layer)

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd party.call --params-json "{\"method\":\"GetPartyID\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd party.call --params-json "{\"method\":\"GetPartySize\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd party.call --params-json "{\"method\":\"IsPartyLoaded\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd party.players.call --params-json "{\"method\":\"GetAgentIDByLoginNumber\",\"args\":[1]}"
```

### Inventory (cache/service layer)

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd inventory.call --params-json "{\"method\":\"GetFreeSlotCount\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd inventory.call --params-json "{\"method\":\"GetGoldOnCharacter\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd inventory.call --params-json "{\"method\":\"GetModelCount\",\"args\":[2992]}"
```

### Skillbar (cache/service layer)

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd skillbar.call --params-json "{\"method\":\"GetZeroFilledSkillbar\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd skillbar.call --params-json "{\"method\":\"GetCasting\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd skillbar.call --params-json "{\"method\":\"GetHoveredSkillID\",\"args\":[]}"
```

### Quest

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd quest.call --params-json "{\"method\":\"GetActiveQuest\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd quest_raw.call --params-json "{\"method\":\"GetQuestLogIds\",\"args\":[]}"
```

### Shared Memory / Multibox state

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd shmem.call --params-json "{\"method\":\"GetNumActivePlayers\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd shmem.call --params-json "{\"method\":\"GetAllMessages\",\"args\":[]}"
python bridge_cli.py request --hwnd <HWND> --cmd shmem.call --params-json "{\"method\":\"GetAllAccountData\",\"args\":[]}"
```

## Cross-account command examples (shmem)

Use the curated `shmem.send_command` helper when you want to send commands through the existing Messaging/shared-memory pipeline.

### Example: Send a remote message (generic)

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd shmem.send_command --params-json "{\"receiver_email\":\"alt@example.com\",\"command\":\"TravelToMap\",\"msg_params\":[55,0,1,0]}" --poll
```

Notes:

- `command` can be enum name (string) or numeric enum value
- `msg_params` maps to `SharedMessageStruct.Params` (up to 4 numbers)
- `extra_data` can be provided as a list of strings

With `extra_data`:

```powershell
python bridge_cli.py request --hwnd <HWND> --cmd shmem.send_command --params-json "{\"receiver_email\":\"alt@example.com\",\"command\":\"LoadSkillTemplate\",\"msg_params\":[0,0,0,0],\"extra_data\":[\"OQhjUxmM5QAA\"]}" --poll
```

## Async / status model

For queued or shmem-backed operations:

- the bridge returns an immediate response
- the daemon request id is the tracked operation id
- poll with `status` or `request --poll`

States typically include:

- `queued`
- `running`
- `completed`
- `failed`
- `expired`

## What this is useful for (practical)

### AI-assisted scripting

An AI tool (later MCP adapter) can:

- inspect methods on real runtime layers
- read live state
- test generated calls against a real client
- iterate faster with less guesswork

### Multi-client orchestration

One daemon can manage multiple clients and route by `HWND`.

### Stress testing (live)

You can script repeated calls via CLI or a future adapter and collect structured responses/status from real clients.

## Troubleshooting

### `list-clients` is empty

- Ensure daemon is running
- Ensure the Bridge Client widget is enabled
- Verify host/port/token match in widget UI
- Click `Apply Connection Settings`

### Auth token mismatch

- The daemon token and widget token must match exactly
- If daemon runs without `--token`, token check is effectively disabled

### `client_not_found`

- The target `HWND`/`PID` is not currently connected
- Run `list-clients` again and use the current value

### `guard_*` errors (e.g., map loading/cinematic)

- These are runtime guard checks from the bridge/action layer
- Retry when the client is in a valid state

### Generic `.call` returns `repr(...)`

- Some return values are complex native/Python objects
- Use curated endpoints for stable structured output where available
- Or call smaller methods that return primitives/lists

## Next steps (recommended)

1. Build an MCP adapter on top of `bridge_daemon.py` control API
2. Add more curated commands for common workflows (`party.*`, `inventory.*`, `skillbar.*`)
3. Add `test.*` namespace for stress/repeat/analyze helpers
4. Add logging/capture tools for automated test runs
