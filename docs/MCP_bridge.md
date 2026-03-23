# Py4GW MCP Bridge Notes

This file is the MCP-facing summary and planning note for bridge integration.

It tracks the architecture assumptions relevant to MCP, the bridge-to-MCP mapping, and the missing work required to finish the MCP-facing model.

It is not the canonical full architecture document.

For the full explicit architecture model, use [docs/Py4GW_Conceptual_Model.md](/docs/Py4GW_Conceptual_Model.md).

## Architectural Baseline

The project foundation starts at the game process and the extraction mechanisms:

1. `Gw.exe`
   - The game process is the true origin of runtime data.

2. C++ binding-backed extraction
   - Legacy low-level data extraction exposed to Python.
   - These are the C++-backed primitives.
   - The `stubs` folder represents the forward declarations of that bound surface.

3. Native function callers
   - Native Python-side extraction path replacing C++ primitives with pure-Python primitives.
   - Located in `Py4GWCoreLib/native_src`.

These mechanisms feed the first authoritative Python-facing source-of-truth layer: `Py4GWCoreLib`.

The C++ binding-backed primitives and the native function callers are the same conceptual abstraction level implemented through different access paths. The project is migrating from the former to the latter.

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

Above the foundational extraction mechanisms, there is a distinct `Py4GWCoreLib` source-of-truth layer.

For project architecture, this is the single primary Python-facing source-of-truth layer.

This is where Py4GW semantics begin. `stubs` and `native_src` are primitives; `Py4GWCoreLib` is where project/library semantics start.

For UI semantics, this means modules such as `ImGui`, `DXOverlay`, `Overlay`, and `UIManager` are higher-level project-facing layers built on top of the lower-level `PyImGui` primitive interface.

This layer includes modules and wrapper surfaces such as:

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
- `Routines` as a middle-tier routines facade over `routines_src`, combining guard checks, spatial/task helpers, blocking sequential flows, cooperative yield routines, and task-specific behavior-tree routines
- `IniManager` as a higher-level multi-account configuration manager over the lower-level INI handler
- `HotkeyManager` as the project-facing hotkey registration and callback-dispatch layer tied to the embedded `PyImGui` input loop

This layer is important because it is the first authoritative Python-facing layer:

- it receives data from the lower-level extraction mechanisms
- it organizes that access into Python-facing modules/classes used by the rest of the project
- it is part of the practical API surface the bridge currently exposes

Within this layer, `Routines` should be treated as a middle-tier task/routine surface rather than a raw domain primitive. Its backing `routines_src` package is split by both task family and execution style: guard checks, spatial/task helpers, transition helpers, blocking sequential flows, cooperative yield routines, and task-specific behavior-tree routines.

Within this same layer, `IniManager` should be treated as the project-facing multi-account configuration manager: it sits above the lower-level `IniHandler`, manages account-specific vs global config paths, and uses callback-driven deferred flush behavior.

Within this same layer, `HotkeyManager` should be treated as the project-facing runtime hotkey layer: it manages identified key/modifier bindings and dispatches callbacks from the embedded `PyImGui` input state.

For MCP and bridge modeling, this layer should be treated separately from both the foundational extraction mechanisms and `GLOBAL_CACHE`.

## Combat Automation Layer

Above the core library, cache, and shared-memory coordination, the project has a combat automation layer built around two near-parallel systems:

- `Py4GWCoreLib.SkillManager.Autocombat` for single-account local combat automation
- `HeroAI.CombatClass` for the multibox/party-aware analog

These two systems share essentially the same combat engine shape:

- skillbar ingestion and custom-skill metadata
- priority sorting by skill nature/type/combos
- staged readiness checks
- target resolution by tactical target category
- detailed cast-condition evaluation
- aftercast/ping-aware scheduling
- final dispatch through `GLOBAL_CACHE.SkillBar.UseSkill`

The key difference is operational context, not combat reasoning:

- `SkillManager` runs directly against the local account
- `HeroAI` wraps the same combat logic in shared-memory-backed party/account caches, per-account options, remote commands, and UI

## Bot Orchestration Layer

Above combat automation, the project has a higher bot orchestration layer centered on `Py4GWCoreLib.Botting.BottingClass`.

This layer should be treated as the main automation-composition runtime:

- it owns a named `FSM`
- it builds configured step graphs through a bot `Routine()`
- it schedules both:
  - normal FSM states
  - coroutine-backed self-managed yield steps
- it attaches long-lived managed background coroutines for upkeep/services
- it exposes grouped wrapper namespaces (`States`, `Move`, `Wait`, `Events`, `Items`, `Party`, `Target`, `Multibox`, etc.) that behave like a bot-scripting DSL over the scheduler

Conceptually:

- `Routines` provides reusable task units
- combat automation provides autonomous combat execution
- `Botting` composes them into a full bot lifecycle and reactive FSM-driven automation flow

## `py4gwcorelib_src` Support Infrastructure

Above the `Py4GWCoreLib` source-of-truth modules, there is a support/infrastructure layer in `Py4GWCoreLib/py4gwcorelib_src`.

This layer is not a new primitive source and not a new source-of-truth layer. It is complementary support code used as the shared base for more abstract Python-side systems.

Currently identified examples:

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
- `Color` for shared color conversion/mutation utilities
- `Console` as a thin interface into `Py4GW` console/system functions

## `GLOBAL_CACHE` Consumer Layer

`GLOBAL_CACHE` sits above `Py4GWCoreLib` and consumes those source-of-truth libraries.

It is desirable because it provides caching support, but it is optional. It is valid to use `Py4GWCoreLib` directly without `GLOBAL_CACHE`.

When a corresponding cache getter exists, `GLOBAL_CACHE` should be treated as the preferred read interface. When no corresponding cache surface exists, fall back to direct `Py4GWCoreLib` usage.

The same preference rule applies to actions and mutating operations when a corresponding cache-backed operation exists.

`GLOBAL_CACHE` is derivative of `Py4GWCoreLib`, not a parallel peer source-of-truth layer.

It is also a managed cache-runtime layer, not only a loose set of mirrors: the root `GlobalCache` singleton owns shared throttled update cadence, a shared action queue, and shared cache substrates such as the raw item cache.

Beyond the cache surfaces already exposed by the bridge, the actual cache layer also includes additional important domains such as `Camera`, `Item`, `ItemArray`, `Trading`, and `Skill`.

## Shared Memory / Multiboxing Coordination Layer

In the multiboxing environment, multiple clients can be interacted with through a shared-memory-driven coordination layer.

This layer lives inside `GLOBAL_CACHE`, centered around shared memory support.

It:

- supports multi-client interaction
- provides pushed cross-account data so accounts can read data from other accounts
- handles messaging between accounts
- has a large typed `shared_memory_src` schema for account, agent, party, map, quest, skillbar, title, and message data
- should be treated as a higher coordination layer built on top of the data-access stack

## Bridge Layer

The bridge stack is an exposure/remoting layer over the `Py4GWCoreLib` source-of-truth layer and derivative `GLOBAL_CACHE` projections:

- Injected widget client: `Widgets/Coding/Tools/Bridge Client.py`
- External daemon: `bridge_daemon.py`
- CLI tester/operator: `bridge_cli.py`

This layer does not define the architecture of the underlying library. It only exposes selected capabilities from the wrapper/base systems over a local TCP protocol.

In the current implementation, the bridge's generic namespace map primarily projects:

- `Py4GWCoreLib` source-of-truth libraries such as `Map`, `Player`, `Agent`, `AgentArray`, `Party`, `Skill`, `SkillBar`, `Inventory`, `Quest`, and `Effects`
- `GLOBAL_CACHE` namespaces for party, skillbar, inventory, quest, effects, and shared memory

The `shmem` bridge namespace is the currently modeled bridge-facing handle into this shared memory / multiboxing coordination layer. It represents both the pushed cross-account data layer and the account-to-account messaging layer.

This means the bridge should currently be modeled as exposing project-facing `Py4GWCoreLib` surfaces plus derivative `GLOBAL_CACHE` projections, not the lowest-level binding/native base directly.

## Current State

What exists today:

- The bridge transport protocol (`BridgeRuntime/protocol.py`)
- The injected bridge client widget
- The bridge daemon with routing by `HWND` / `PID`
- The CLI for testing daemon control calls

What is still missing:

- Structured MCP tool schemas instead of raw command strings and ad hoc JSON payloads
- Capability filtering stronger than "public method and not underscore-prefixed"
- Daemon-side log/history endpoints for `_forward_log`

## Current MCP Adapter Baseline

A first MCP stdio adapter now exists:

- `py4gw_mcp_server.py`

This adapter currently exposes a narrow safe tool set over the daemon control API:

- `list_clients`
- `list_namespaces`
- `list_commands`
- `describe_runtime`
- `get_map_state`
- `get_player_state`
- `list_agents`

It is intentionally built on the normalized daemon control surface rather than generic `client.request`.

This is the baseline adapter layer, not the finished MCP surface. The next iterations should tighten tool schemas, expand safe coverage, and add stronger enforcement around reflective or mutating operations.

At the conceptual level, the remaining architecture work is upward expansion: the current lower stack is established, and the major unresolved layers are additional higher layers not yet modeled.

## Documentation Corrections

The bridge documentation must stay aligned with the real architecture:

- `docs/Py4GW_Conceptual_Model.md` is the current source-of-truth for the conceptual architecture.
- `MCP_bridge.md` is the architecture note for MCP planning.
- `BridgeRuntime/README.md` is the bridge runtime usage reference.
- The actual bridge widget path in this repo is `Widgets/Coding/Tools/Bridge Client.py`.

## Design Rule Going Forward

When modeling or exposing functionality for MCP:

- Treat the foundational base as `Gw.exe` plus the extraction mechanisms (`stubs` + `Py4GWCoreLib/native_src`).
- Treat `Py4GWCoreLib` as the first authoritative Python-facing source-of-truth layer.
- Treat `GLOBAL_CACHE` as a separate consumer layer above `Py4GWCoreLib`.
- Treat the bridge as a transport/exposure layer over those project-facing surfaces.
- Add new architectural layers only when they are explicitly defined or required by the task at hand.
