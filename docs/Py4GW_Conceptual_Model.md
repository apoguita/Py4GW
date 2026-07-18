# Py4GW Conceptual Model

This file is the canonical source-of-truth for the conceptual architecture of the Py4GW project.

It is intended to stabilize terminology before expanding more runtime data, bridge coverage, or MCP tools.

This file should contain the full explicit architecture model:

- layer definitions
- terminology
- system classification
- architectural rules
- relationships between systems

Other documentation files may summarize this model for narrower purposes, but they should not replace it as the primary architecture reference.

## Layer Stack

### 1. Foundational Base

The foundational base is the lowest practical data-manipulation substrate currently modeled.

It starts at the game process and the extraction mechanisms that read from it:

- `Gw.exe`
  - The game process is the true origin of runtime data.
- C++ binding-backed extraction
  - Legacy low-level data extraction exposed to Python.
  - These are the C++-backed primitives.
  - The `stubs` folder acts as the forward declarations of the bound C++ surface.
- Native function callers
  - Native Python-side extraction path replacing C++ primitives with pure-Python primitives.
  - Located in `Py4GWCoreLib/native_src`.
  - This is the lower-level access path in pure Python.

These mechanisms are how data is extracted before it is funneled into the Python library layer.

The C++ binding-backed primitives and the native function callers represent the same level of abstraction. They differ by implementation language and access path, not by conceptual depth.

The project is migrating from C++-backed sources to Python-native sources.

When both primitive paths exist for the same domain, native primitives should be treated as the preferred implementation and C++-backed primitives as secondary. In practice, this is mostly an implementation detail rather than a conceptual split.

For UI handling specifically, `PyImGui` stubs are the primitive source-of-truth interface. They should be treated as the low-level immediate-mode UI API, including:

- core window/layout/widget primitives
- IO/input state (`ImGuiIO`)
- UI enums and flags
- interaction and focus/hover queries
- draw-list primitives for direct shape/text drawing

Higher UI-facing passes built on top of that are derivative, even when they remain architecturally important.

`ImGui_Py` is legacy and should not be referenced as part of the current conceptual model.

### Foundational Primitive Systems (additional classification)

- `PyScanner`
  - Low-level memory positioning and function-resolution system used by `native_src`.
  - Allows the project to locate, read, and execute functions from `Gw.exe`.

- `PyPointers`
  - Shared pointer surface coming from the C++ side into `native_src`.
  - Provides the raw pointers needed to gather game data.

- `PyCallback`
  - Execution scheduling system for queued code inside the library.
  - Callbacks run in sequence and execute code through the C++ side.

- `Py4GW`
  - Miscellaneous low-level system surface coming from C++.
  - Includes window handling, console logging, client/window data, and other system-level functions.

- `PyPathing`
  - Primitive access to the in-game pathing system.
  - This should be treated as the low-level path computation / path-planning primitive surface.

- `PyKeystroke`
  - Input-injection primitive surface.
  - Allows the client to send key presses to the game.

- `PyTrading`
  - Primitive player-to-player trading surface.
  - This should be treated separately from merchant/NPC trading, because it represents direct player trade flow.

- `Py2DRenderer`
  - Primitive rendering surface that acts as the base of `DXOverlay`.
  - This should be treated as a lower-level rendering primitive beneath higher DirectX overlay helpers.

- `PyOverlay`
  - Primitive overlay surface that acts as the base of `Overlay`.
  - This should be treated as the lower-level overlay primitive beneath the higher ImGui-based overlay layer.

### 2. `Py4GWCoreLib` Source-of-Truth Layer

This is the first authoritative Python-facing source-of-truth layer.

For this project, it is also the single primary Python-facing source-of-truth layer.

Even though the embedded Python runtime may contain many active systems, `Py4GWCoreLib` is the only project-ruling Python-level authority in the conceptual model.

Data from the foundational extraction mechanisms funnels into `Py4GWCoreLib` libraries such as `Player`, `Agent`, and `Map`.

This is the point where Py4GW semantics begin. `stubs` and `native_src` are primitives; `Py4GWCoreLib` is where project/library semantics start.

For UI semantics, this means modules such as `ImGui`, `DXOverlay`, `Overlay`, and `UIManager` should be treated as higher-level project-facing layers built on top of the lower-level `PyImGui` primitive interface.

Known modules/surfaces include:

- `Agent`
- `AgentArray`
- `Camera`
- `CombatEvents`
- `Context`
- `DXOverlay`
- `Effect`
- `ImGui`
- `Inventory`
- `Item`
- `ItemArray`
- `Map`
- `Merchant`
- `Overlay`
- `Party`
- `Player`
- `Quest`
- `Skill`
- `Skillbar`
- `UIManager`

### `Py4GWCoreLib` Role Groups (initial classification)

#### World Instance and Spatial Context

- `Map`
  - The core role is to represent the status of the current game instance.
  - It owns data related to where the client is.
  - It also includes broader map-related functionality such as:
    - map / minimap / world map handling
    - pathing and travel methods
    - spatial navigation helpers
    - 2D / 3D projection-related features
  - It is also the primary instance-state gatekeeper, including:
    - map-data loaded vs loading checks
    - map-ready checks
    - instance type classification (outpost / explorable / loading)
    - observing/spectator-state detection
    - cinematic-state detection
  - It exposes richer map/instance metadata than previously captured, including:
    - current map ID and map-name lookup
    - name-to-ID resolution
    - seasonal/base map variant normalization and matching
    - instance uptime
    - region, region type, district, and language
    - campaign and continent
    - player-count and party-size limits
    - vanquish-related kill counters and completion state
  - It is also an important queued world-transition/action surface, including:
    - travel
    - district / region travel
    - guild hall travel
    - cinematic skipping
    - challenge enter/cancel flows
  - These active map operations are routed through the action-queue infrastructure, so `Map` is not only a passive state container.
  - Internally, `Map` contains multiple specialized sub-surfaces that matter conceptually:
    - `MissionMap`
      - mission-map frame state, click capture, viewport/zoom/pan state, and dense coordinate-conversion/projection helpers between game space, world-map space, normalized screen space, and mission-map screen space
    - `MiniMap`
      - minimap frame state, window visibility, click capture, lock/rotation state, and minimap projection helpers
    - `WorldMap`
      - world-map-specific UI/state helpers
    - `Pathing`
      - pathing-map data access, including pathing-map structures and travel-portal/pathing surfaces
  - This means `Map` should be treated as both:
    - the primary world-instance state layer
    - the main spatial-UI/projection hub for map-based interaction and navigation

#### World Entity Model

- `Agent`
  - Generic world-entity abstraction.
  - In the 3D world, anything that is not terrain or scenery is conceptually an agent.
  - This includes players, NPCs, enemies, chests, and some props.
  - It is not just a simple identity wrapper; it is the primary typed-property surface for world entities.
  - It internally exposes typed views over the same entity space:
    - generic agent view
    - living-agent view
    - item-agent view
    - gadget-agent view
  - It also maintains a callback-invalidated property cache for these typed views, so it should be treated as a cached per-agent property-access layer as well as a raw entity accessor.
  - Its feature surface is significantly broader than the earlier summary and includes:
    - name lookup / name readiness / name-to-agent lookup
    - attribute lists and attribute dictionaries
    - type classification (living / item / gadget)
    - ownership and identity links (player number, login number, owner, guild/team IDs)
    - spatial data (XY/XYZ, z-plane, name-tag position, terrain normal, ground)
    - model and presentation data (model ID/state, model scales, visual/name properties, transmog)
    - animation / movement / rotation / velocity data
    - professions, profession names, and profession texture paths
    - combat-resource state (health, energy, regen, pips, overcast)
    - combat/status flags (moving, knocked down, bleeding, crippled, deep wound, poisoned, conditioned, enchanted, hexed, weapon-spelled, combat stance, aggressive, attacking, casting, idle, dead/alive)
    - weapon classification and extra weapon data
    - allegiance and high-level role checks (player, NPC, spirit, minion, spawned, observed, etc.)
    - item-agent and gadget-agent specific metadata
  - This means `Agent` should be treated as the main per-entity state/typing/introspection surface for the game world.

- `AgentArray`
  - The authoritative collection of agents from the game's own agent array.
  - Includes the local player as part of that collection.
  - Acts as the collection layer for world entities.
  - It is more than a plain list accessor; it is the project-facing classified query layer over the game’s agent collection.
  - It exposes both:
    - the raw full agent array
    - many pre-filtered semantic arrays such as allies, enemies, neutrals, spirits/pets, minions, NPC/minipets, items, owned items, gadgets, dead allies, and dead enemies
  - It also provides higher-level collection operations as first-class sublayers:
    - `Manipulation`
      - merge / subtract / intersect operations on agent-ID sets
    - `Sort`
      - sort by attribute, custom condition, distance, or health
    - `Filter`
      - filter by attribute, custom condition, or distance
    - `Routines`
      - collection-oriented helper routines such as cluster detection over agent groups
  - This means `AgentArray` should be treated as both:
    - the authoritative agent collection source
    - the main collection-query/manipulation layer for world-entity sets

#### Local Player Specialization

- `Player`
  - The local player is an agent, but `Player` is the specialized interface for player-specific state and actions.
  - It exposes player-only functionality that should not be treated as generic agent behavior.
  - This includes account data, movement, and other local-player-specific operations.
  - It is also the project-facing identity layer for the local controlled character, including:
    - player number / login number / party index
    - agent binding for the local player
    - account name and account-email identity
    - player UUID identity data
  - Its account-identity handling includes sanitization/fallback behavior for unsupported email cases, including an HWND-derived fallback identity used for downstream systems such as shared-memory-safe identifiers.
  - It also exposes player-specific progression/state surfaces such as:
    - experience
    - level
    - morale
    - rank / rating / qualifier / win-loss data
    - tournament reward points
    - active title and title-array access
  - Beyond raw state, it is a major local-player action surface, including:
    - targeting and interaction
    - movement
    - faction deposit
    - title selection/removal
    - dialog and skill-trainer interactions
    - chat history requests
    - chat command / chat / whisper / fake-chat methods
  - These active operations are not simple direct writes; they are routed through the action-queue infrastructure, so `Player` should also be treated as an important queued local-action entry point.

#### Inventory and Trade Systems

- `Inventory`
  - Handles inventory bags, slots, and general item movement/management.
  - This includes actions such as salvage, identify, equip, use, and gold handling.
  - It is broader than simple item movement and should be treated as the primary bag/storage management layer.
  - It exposes inventory-space and storage-space accounting, including:
    - total used vs total capacity
    - free-slot counts
    - zero-filled storage slot maps
  - It also provides aggregate item counting/query helpers across bags, storage, and equipped slots, including counts by:
    - exact item ID
    - model ID
  - It includes workflow-oriented helper selection logic for common inventory operations, such as:
    - locating the first identification kit
    - locating the first salvage kit
    - locating the first unidentified item
    - locating the first salvageable item
  - It is also an active inventory-operation surface, including:
    - identifying items
    - salvaging items
    - accepting salvage-material dialogs
    - opening and checking storage
    - picking up items
    - dropping items
    - equipping items
    - using items
    - destroying items
  - This means `Inventory` should be treated as both:
    - the bag/storage state and capacity layer
    - the primary item-handling workflow/action layer

- `Item`
  - Handles each item as an individual object/entity.
  - This is the per-item handling layer.
  - It is not just a thin item-ID wrapper; it is the primary per-item introspection and classification surface.
  - It exposes core item identity and placement information, including:
    - item instance access
    - linked agent identity
    - agent-item identity
    - model ID / model file ID
    - bag slot placement
    - lookup by model ID or linked agent ID
    - item-name request/readiness/name access
  - It also includes item-specific structure and feature groups:
    - `Rarity`
      - rarity classification (white/blue/purple/gold/green)
    - `Properties`
      - customization, value, quantity, equipped state, profession, interaction flags
    - `Type`
      - weapon/armor/inventory/storage/material/rare-material/zcoin/tome classification
    - `Usage`
      - usability, uses, salvageability, kit types, identification state
    - `Customization`
      - inscription/upgradability state
      - dye/formula data
      - stackability and sparkly state
      - nested modifier inspection through `Customization.Modifiers`
    - `Trade`
      - trade-offered and tradable state
  - It also includes lower-level modifier inspection for item upgrades/customization, which makes it an important item-structure analysis layer, not just a convenience wrapper.
  - This means `Item` should be treated as the main per-item definition/properties/customization/trade introspection layer.

- `ItemArray`
  - The collection layer for items.
  - Conceptually similar to `AgentArray`, but for items instead of agents.
  - It is more than a simple array accessor and should be treated as the collection-query layer for items across bags.
  - It provides:
    - bag-list construction from bag identifiers
    - cross-bag item collection
    - bag discovery/access helpers
  - It also includes first-class collection sublayers similar in spirit to `AgentArray`:
    - `Filter`
      - filter by item attribute or arbitrary condition
    - `Manipulation`
      - merge / subtract / intersect item-ID sets
    - `Sort`
      - sort by item attribute or arbitrary condition
  - This means `ItemArray` should be treated as both:
    - the cross-bag item collection source
    - the main item-set filtering/manipulation/sorting layer

- `Merchant`
  - Handles trading-oriented NPC interactions.
  - This includes merchants, collectors, traders, material traders, and related trading flows.
  - The current file structure is conceptually broader than the name suggests: `Merchant.py` actually defines a `Trading` surface with multiple trading-context subcontrollers.
  - This should therefore be treated as the project’s NPC/economy transaction layer, not just a single merchant-only wrapper.
  - It exposes transaction-completion state plus specialized transaction roles:
    - `Trader`
      - quoted item / quoted value
      - offered-item lists
      - buy/sell quote requests
      - buy/sell execution
    - `Merchant`
      - standard merchant buy/sell plus offered-item listing
    - `Crafter`
      - crafting purchases using item requirements and gold cost
    - `Collector`
      - exchange-style purchases using item requirements and optional cost
  - This means the conceptual `Merchant` role should be understood as the broader NPC trade/crafting/exchange transaction surface.

#### Skill, Effect, and Combat State

- `Skillbar`
  - The skillbar state for combat-capable actors.
  - The player, heroes, and other combat-capable agents have a skillbar.
  - Handles skill slots (0 through 8), casting status, currently casting skills, and skillbar-related functions.
  - It is both a state surface and an active execution surface.
  - It exposes:
    - current skillbar composition
    - zero-filled slot mapping
    - per-slot skill lookup
    - reverse lookup from skill ID to slot
    - raw per-slot skill data objects
    - hovered-skill inspection
    - disabled/casting state of the bar
    - owning agent identity
  - It also handles skillbar actions and management operations, including:
    - using a skill
    - targetless skill use
    - hero skill use
    - loading player skill templates
    - loading hero skill templates
    - changing a hero secondary profession
  - It also exposes account progression aspects around skills, such as skill unlocked/learnt checks.
  - This means `Skillbar` should be treated as the active combat-loadout execution layer, not only a passive slot container.

- `Skill`
  - The data of the skill itself.
  - This is the per-skill definition/data layer.
  - It is significantly richer than a simple ID-to-name lookup.
  - It combines:
    - direct bound skill data
    - project-side description metadata loaded from `skill_descriptions.json`
  - It therefore acts as both:
    - the per-skill runtime definition layer
    - a static knowledge/metadata lookup layer for descriptive and progression data
  - Its feature surface includes:
    - names, URLs, concise/full descriptions
    - skill type, campaign, and profession
    - progression/scaling metadata from external description data
    - data/cost/timing fields such as energy, health, adrenaline, activation, aftercast, recharge, AoE, overcast, combo, and weapon requirements
    - attribute-linked scaling, bonus scaling, and duration ranges
    - extensive categorical/type-flag checks (elite, PvE/PvP, spell, stance, enchantment, signet, attack, shout, trap, ritual, chant, disguise, etc.)
    - effect/special/animation/target/equip/argument/name-ID/description-ID/icon/texture-related metadata
  - This means `Skill` should be treated as the primary per-skill definition/introspection/metadata layer, not just “skill data.”

- `Effect`
  - Handles state layered on top of an agent.
  - This includes buffs, debuffs, environmental statuses, status effects, and similar effect-state carried by an agent.
  - The current implementation is exposed through an `Effects` class, and it should be treated as the main active-effect/buff inspection layer for agents.
  - It provides:
    - access to buff lists and effect lists per agent
    - buff/effect counts
    - existence checks by skill ID
    - combined “has effect” checks across buffs and effects
    - effect attribute-level lookup
    - effect remaining-duration lookup
    - buff-ID lookup by skill
  - It is also an active effect-control surface in limited cases, including:
    - dropping/removing a buff from the local player
    - applying drunk-effect visuals
    - reading alcohol level
  - This means `Effect` / `Effects` should be treated as both:
    - the layered status-state inspection layer
    - the primary per-agent buff/effect query surface

- `CombatEvents`
  - Observation/event stream for combat.
  - Represents callback-driven combat data from C++ showing damage and combat packets.
  - This should be treated as an event/observation layer rather than a primary state container.
  - The actual implementation is significantly richer than a raw packet stream.
  - It is a real-time combat-state tracking system built on top of C++ packet hooks and a queued event feed.
  - Architecturally, it combines:
    - a lower C++ hook/queue capture layer
    - a Python polling/mining layer that processes events each frame
  - It is therefore both:
    - a raw combat-event access layer
    - a derived combat-state model built from those events
  - Its primary state/query surface includes:
    - casting state (casting, casting skill, cast target, cast progress, remaining cast time)
    - attack state (is attacking, attack target)
    - action state (can act, disabled, knockdown, knockdown remaining)
    - skill recharge state (live and estimated recharge tracking)
    - observed-skill tracking
    - estimated stance tracking
    - targeting analysis (agents targeting a given target)
  - It also exposes an optional callback system for reactive code, including:
    - skill activated / finished / interrupted
    - attack started
    - aftercast ended
    - knockdown
    - damage
    - skill recharge started / ended
  - It also supports raw event access for advanced consumers, including:
    - full event history
    - recent damage views
    - recent skill-event views
    - clearing event history
  - This means `CombatEvents` should be treated as the project’s combat telemetry and derived combat-state layer, not merely a passive callback feed.

#### UI, Overlay, and Runtime Presentation

- `ImGui`
  - Higher-level UI toolkit and facade layer built on top of `PyImGui`.
  - The top-level `ImGui.py` module is primarily a facade over `ImGui_src`, not the main implementation body.
  - It packages and re-exports higher-level UI systems such as:
    - style and theme management
    - texture and themed-texture helpers
    - window-module abstractions
  - Its `ImGui_src` implementation is a real multi-subsystem toolkit layer, not just a set of aliases. It adds project-facing behavior beyond raw `PyImGui`, including:
    - theme stack management, theme switching, and per-window theme application
    - rich style management through `Style`, including:
      - named style variables
      - default/custom/texture color sets
      - style push/pop stacks
      - JSON theme save/load/delete
      - preview and permanent application into `PyImGui.StyleConfig`
    - textured UI rendering through `Textures`, including:
      - atlas-state textures (`Normal`, `Hovered`, `Active`, `Disabled`)
      - 1/3/9-slice scalable textured controls
      - precomputed UV regions
      - theme-dependent texture selection (`ThemeTexture`, `ThemeTextures`)
    - window orchestration through `WindowModule`, including:
      - managed window creation state
      - geometry tracking
      - themed custom window decorations
      - draggable faux title bars
      - close-button handling
      - overlay-aware centering and sizing
    - alignment, clamping, and display-port layout helpers
    - text helpers, decorators, alignment, scaling, and font-aware rendering
    - higher-level interactive controls such as:
      - styled buttons / icon buttons / toggle buttons
      - textured image buttons
      - combos, checkboxes, radio buttons
      - typed inputs and sliders
      - search fields
      - tables, tab bars, popups, child windows, progress bars
      - custom scroll-bar drawing
  - This means `ImGui` should be treated as the higher-level themed UI toolkit layer. For base immediate-mode widgets, flags, and draw-list primitives, `PyImGui` remains the primitive base.

- `DXOverlay`
  - DirectX helper layer exposed from C++.
  - Primarily used for drawing maps and handling textures.
  - This should be treated as a higher-level rendering/presentation support layer built on top of `Py2DRenderer`.
  - It is specifically a structured DirectX rendering facade rather than a simple one-shot drawing helper.
  - It wraps a renderer instance and organizes rendering into distinct subcontexts:
    - `world_space`
      - world-space zoom/pan/scale/rotation controls
    - `screen_space`
      - screen-space zoom/pan/rotation controls
    - `mask`
      - circular and rectangular masking controls
  - It exposes a large geometry-rendering surface for both 2D and 3D drawing, including:
    - lines
    - triangles
    - quads
    - polygons
    - cubes
    - textured quads / textures
  - It also includes:
    - world-to-screen projection helpers
    - ground-height (`FindZ`) lookup integration
    - occlusion-aware 3D rendering
    - snap-to-ground rendering support
    - pathing geometry build/export support
    - stencil-mask application/reset
  - This means `DXOverlay` should be treated as the higher-level geometric/texture rendering engine for advanced overlay and map rendering work.

- `Overlay`
  - ImGui-based overlay handler.
  - Supports full-screen overlay behavior and drawlist capabilities.
  - Includes world-to-screen and screen-to-world primitives.
  - Can draw and position UI elements in the 3D world.
  - This should be treated as a higher-level overlay layer built on top of `PyOverlay`.
  - It is implemented as a singleton runtime overlay surface rather than a purely stateless helper.
  - It combines:
    - drawlist lifecycle control (`BeginDraw`, `EndDraw`, `RefreshDrawList`)
    - mouse/screen/world position input access
    - world-to-screen and ground-height projection helpers
  - It exposes a broad immediate-style drawing surface, including:
    - 2D and 3D lines, triangles, quads, polygons, cubes
    - stars
    - text and 3D text
    - clipping rectangles
  - It also provides a texture/UI-facing surface beyond pure geometry, including:
    - texture draw helpers
    - textured rectangles
    - foreground/drawlist texture insertion
    - texture upkeep/lifetime helpers
    - image-button helpers
  - This means `Overlay` should be treated as the main singleton drawlist/UI overlay composition layer, distinct from the more renderer-structured `DXOverlay`.

- `UIManager`
  - Low-level game UI interaction/control framework.
  - It is significantly broader than a simple “send UI message” wrapper.
  - It combines several distinct UI subsystems:
    - frame lookup and frame-tree introspection
    - frame geometry / visibility / hierarchy access
    - frame-level IO event capture tied to the callback/draw loop
    - UI message dispatch and raw frame-message dispatch
    - dynamic UI component/frame creation and destruction
    - game UI preferences, key mappings, and window visibility/position control
    - specialized helpers for NPC dialogs and confirmation dialogs
  - It also includes:
    - frame and UI-message logging
    - frame alias/path construction and JSON-backed label mapping
    - compass drawing hooks
    - encoded-string conversion helpers
    - overlay-backed debug drawing of frame bounds
  - The `FrameInfo` abstraction and global `WindowFrames` registry make it a reusable frame-reference system, not just a static utility namespace.
  - This means `UIManager` should be treated as the foundational project-facing UI frame/message orchestration layer that higher UI systems build on.

#### Context, Camera, and Quest State

- `Context`
  - Typed native-context gateway layer over `native_src`.
  - It is not a broad gameplay helper; it is a structural access surface for the project's native context facades and structs.
  - Its internal pattern is a reusable `_GWContextBase` that standardizes:
    - pointer access (`GetPtr`)
    - typed struct retrieval (`GetContext`)
    - validity checks (`IsValid`)
  - It exposes multiple distinct native context domains through the `GWContext` namespace, including:
    - `AccAgent`
    - `AgentArray`
    - `AvailableCharacterArray`
    - `Char`
    - `Cinematic`
    - `Gameplay`
    - `Guild`
    - `InstanceInfo`
    - `Map`
    - `MissionMap`
    - `Party`
    - `PreGame`
    - `ServerRegion`
    - `World`
    - `WorldMap`
  - `InstanceInfo` also adds typed map-info extraction on top of the base context-access pattern.
  - This means `Context` should be treated as the primary typed gateway into the native context graph that higher source-of-truth systems build on, rather than as an end-user domain abstraction by itself.

- `Camera`
  - Camera-state and camera-control layer over the lower-level `PyCamera` primitive surface.
  - It is broader than a simple getter wrapper and should be treated as the project-facing camera manipulation interface.
  - It exposes camera-state and orientation data such as:
    - look-at agent ID
    - yaw, current yaw, and pitch
    - zoom and max-distance values
    - field of view
    - camera-unlock state
  - It also exposes transitional/"to-go" state and camera motion internals, including:
    - yaw / pitch / distance to-go
    - target camera position to-go
    - look-at target to-go
    - acceleration and rotation timing values
    - time-since-last input/selection timing counters
  - It provides full spatial camera geometry access, including:
    - current camera position
    - inverted camera position
    - look-at target position
  - It is also an active camera-control surface, including:
    - set yaw / pitch / max distance / field of view
    - lock/unlock camera
    - forward / vertical / side movement
    - rotational movement
    - explicit camera-position and look-at-target setting
    - fog toggling
    - camera-position compute/update helpers
  - It also includes derived spatial helpers such as `IsPointInFOV`, which makes it relevant for visibility-style checks in higher systems (while the code itself notes cache-backed checks are preferred when available).
  - This means `Camera` should be treated as the project-facing camera-state, camera-motion, and view-control layer rather than only a passive camera-data accessor.
- `Quest`
  - Quest-log state layer.
  - Handles quest-log information and related quest-state data.
  - It is broader than a simple active-quest getter.
  - It acts as both:
    - the quest-log state layer
    - the asynchronous quest-information retrieval layer
  - It exposes:
    - active quest get/set
    - quest abandon
    - completion and primary-quest checks
    - mission-map quest availability
    - full quest-log and quest-log ID access
    - direct quest-data retrieval for a quest ID
  - It also provides request/readiness/get patterns for richer quest metadata, including:
    - quest name
    - description
    - objectives
    - location
    - associated NPC
    - general quest info / marker updates
  - This means `Quest` should be treated as both:
    - the quest-log state surface
    - a staged/async quest-metadata retrieval interface

#### Party Composition and Group State

- `Party`
  - Party-state data layer.
  - Handles information about the full party composition.
  - This includes party players, their heroes, their henchmen, and other NPCs that are part of the party.
  - It is broader than composition alone and should be treated as the full party-management/control layer.
  - In addition to party composition, it exposes:
    - party identity and leader identity
    - the local player’s own party position
    - loaded/defeated/leader state
    - party-size and member-count breakdowns
    - hard-mode unlocked / hard-mode / normal-mode state
    - party morale per member
  - It also includes readiness/tick coordination features:
    - tick-as-toggle mode
    - all-ticked / per-player tick state
    - toggling the local player ready state
  - It is also an active party-control surface, including:
    - switching hard mode / normal mode
    - party search, cancellation, replies, and request responses
    - returning to outpost
    - leaving the party
  - Internally, it has important specialized subgroup controllers:
    - `Players`
      - login-number <-> agent-ID mapping
      - name lookup
      - party-position lookup
      - inviting and kicking players
    - `Heroes`
      - hero identity lookup by party position, name, or agent
      - adding/kicking heroes
      - hero skill use
      - hero flagging/unflagging
      - hero behavior control
    - `Henchmen`
      - adding and kicking henchmen
    - `Pets`
      - pet behavior control, target lock, and pet info lookup
  - This means `Party` should be treated as both:
    - the group-composition state layer
    - the primary group-management and companion-control layer

#### Navigation, Scanning, and Data Definitions

- `Pathing`
  - Higher-level path-planning and navmesh-routing layer built on top of lower-level pathing primitives.
  - It is significantly broader than a thin wrapper over `PyPathing`.
  - It combines two planning models:
    - native in-game planning through `PyPathing.PathPlanner`
    - project-side fallback planning through a custom navmesh + A* pipeline
  - It contains substantial geometry and navmesh infrastructure, including:
    - trapezoid geometry helpers
    - a BSP-based point-location index for pathing trapezoids
    - `NavMesh` construction from map pathing layers
    - local and cross-layer portal-graph generation
  - Its `NavMesh` layer provides higher-level spatial helpers such as:
    - trapezoid lookup by coordinates
    - nearest trapezoid / nearest reachable position
    - containment checks
    - line-of-sight checks across the navmesh
    - path simplification by line-of-sight
    - navmesh serialization/deserialization
  - It includes an explicit `AStar` solver over the generated portal graph.
  - It also includes path-shaping/post-processing helpers such as:
    - Chaikin smoothing
    - path densification / hop splitting
  - The `AutoPathing` layer adds:
    - per-map/group navmesh caching
    - grouped pathing-map reuse across related maps/outposts
    - coroutine/yield-driven loading and planning
    - automatic fallback from the native path planner to custom navmesh A*
    - player-relative convenience path generation (`get_path_to`)
  - It depends on both lower-level primitives and core source-of-truth systems (`Map`, `enums`, `Routines`, and player state), so it should be treated as the main project-facing path-planning and route-shaping layer rather than as a simple primitive adapter.

- `Scanner`
  - Project-facing scan and symbol-resolution layer built on top of `PyScanner`.
  - It is still relatively low-level, but it adds a cleaner structured surface above the primitive scanner.
  - It defines the project-side section taxonomy through `ScannerSection` (`TEXT`, `RDATA`, `DATA`).
  - Its feature surface includes:
    - scanner initialization against a target module (or the main module)
    - byte-pattern scanning by section
    - byte-pattern scanning over explicit address ranges
    - assertion lookup by file/message/line metadata
    - section address-range lookup
    - near-call / near-jump target resolution into absolute function addresses
    - backwards scan to function prologues (`ToFunctionStart`)
    - pointer validation within section ranges
    - reference lookup for raw addresses in code
    - reference lookup for ANSI and wide strings, including nth-occurrence variants
  - This means `Scanner` should be treated as the structured project-facing binary scanning and address-resolution layer used to support lower-level primitive discovery, not merely as a generic helper wrapper.

- `enums.py`
  - Shared taxonomy and data-mapping layer.
  - It is not just a few convenience enums; it is the central aggregation surface over the `enums_src` packages.
  - It consolidates multiple major enum/data families into one project-facing import surface, including:
    - game-data classifications (ailments, allegiances, attributes, damage types, professions, ranges, skill types, weapons, experience progression)
    - hero and pet behavior types
    - input enums (`Key`, `MouseButton`, character maps)
    - item/storage enums (`Bags`, item types, rarity, identify/salvage modes)
    - map and instance taxonomy (map-name/id maps, outposts, explorables, instance types)
    - model identifiers and spirit/model mapping data
    - multiboxing/shared-command enums
    - console/message enums
    - region/campaign/continent/district/language/server-region taxonomy
    - texture lookup maps
    - title identifiers, names, tiers, and categories
    - UI enums (chat channels, UI messages, preference types, font IDs, window IDs, graphics settings)
    - calendar/event-cycle data
  - It also exposes key lookup tables and mappings used by other systems, not only enum classes.
  - This means `enums.py` should be treated as the project's shared semantic vocabulary and static classification layer, used to normalize mined game data and keep higher systems speaking a consistent type/data language.

#### Account-Aware Configuration Management

- `IniManager`
  - Higher-level multi-account INI configuration manager.
  - Built on top of the lower-level `py4gwcorelib_src.IniHandler`.
  - Organizes config nodes/handlers, account-specific paths, and optional global/shared paths.
  - Uses callback-driven deferred flushing and throttled write behavior for disk persistence.
  - Supports per-account settings rooted by account email, plus global/shared settings where needed.
  - This should be treated as the project-facing multi-account configuration management layer, not just a thin INI reader/writer.

#### Input Binding and Hotkey Dispatch

- `HotkeyManager`
  - Project-facing hotkey registration and dispatch system.
  - Provides a singleton manager plus `HotKey` binding objects keyed by stable identifiers.
  - Tracks key + modifier combinations and executes registered callbacks when matching input is detected.
  - Polls input through `PyImGui` IO state, meaning it is tied to the embedded UI/input loop rather than a standalone OS-level hook.
  - Supports named/identified hotkey bindings, formatting/display of active bindings, and runtime registration/unregistration.
  - This should be treated as the high-level runtime hotkey binding layer used by widgets and other interactive systems.

#### Middle-Tier Routines Layer

- `Routines`
  - Middle-tier routines facade for achieving concrete in-game tasks.
  - `Routines.py` itself is primarily an aggregation/re-export surface over the `routines_src` package.
  - It is not a single routine engine. It is a namespaced task surface that groups multiple execution styles behind one entry point:
    - `Agents`
    - `Items`
    - `Party`
    - `Checks`
    - `Movement`
    - `Targeting`
    - `Transition`
    - `Sequential`
    - `Yield`
    - `BT`
  - This means `Routines` should be treated as the main project-facing routine namespace, while `routines_src` is the real implementation package behind it.
  - It organizes reusable task-oriented routines built on top of the source-of-truth modules and support infrastructure.
  - This should be treated as a practical task/routine layer above raw domain access and below higher application automation.

- `routines_src`
  - The actual implementation package behind `Routines`.
  - It contains multiple routine styles and task families rather than one single execution model.
  - The package is deliberately split by both domain and execution style:
    - domain/task families:
      - `Agents`
      - `Items`
      - `Party`
      - `Checks`
      - `Movement`
      - `Targeting`
      - `Transition`
    - execution-style families:
      - `Sequential`
      - `Yield`
      - `BehaviourTrees`
  - `Checks` is the shared precondition/guard layer for routine code:
    - player-state checks such as dead / casting / knocked down / can act
    - party-state checks such as wiped, loaded, member range, dead members
    - map validity checks to avoid acting while loading/cinematics/invalid map states
    - it should be treated as the common gating layer used by higher routines before they attempt actions
  - `Agents`, `Targeting`, and `Movement` form the main spatial/tactical helper family:
    - `Agents` provides reusable world-query helpers for finding and filtering NPCs, enemies, corpses, spirits, items, gadgets, chests, and best-target candidates
    - `Targeting` builds on those queries to select practical tactical targets such as lowest ally, clustered enemy, enemy with status conditions, or nearest interactable
    - `Movement` provides higher-level path-following helpers that iterate over waypoints, reissue movement when progress stalls, and support custom early-exit conditions
  - `Transition` is the staged map-transition helper family:
    - travel initiation
    - arrival polling
    - outpost/explorable loaded checks
    - timeout-aware travel-state tracking through shared timers
    - it should be treated as routine-level transition state management above the raw `Map` travel primitives
  - `Sequential` is the blocking/imperative routine family:
    - it wraps actions with explicit sleeps and polling loops
    - examples include interaction, dialog, movement, skillbar actions, outpost travel, map-load waits, and target changes
    - it should be treated as the simplest direct routine model when synchronous step-by-step execution is acceptable
  - `Yield` is the cooperative coroutine routine family:
    - it defines a shared `wait()` generator primitive
    - it drives higher-level tasks as generators that yield repeatedly instead of blocking
    - many of its task methods are adapters over behavior-tree routines, using a helper that ticks a tree until success/failure while yielding in between
    - it should be treated as the main cooperative scheduling layer for routines that must coexist with the callback/game loop
  - `BehaviourTrees` is the behavior-tree routine family:
    - it contains concrete task trees for player actions, skills, map transitions, item lookups, agent targeting, and keybind execution
    - it is the task-library layer built on top of the generic `BehaviorTree` framework from `py4gwcorelib_src`
  - Overall, `routines_src` should be treated as the concrete middle-tier task orchestration package for in-game routines, where the same gameplay tasks can be expressed as guards, direct sequential actions, cooperative generators, or behavior-tree-driven flows depending on the higher module's needs.

This layer:

- is the true source of truth at the Python library level
- consumes data extracted from the foundational base
- organizes lower-level access into project-facing Python modules
- can be used directly without `GLOBAL_CACHE`

### 2.5. `py4gwcorelib_src` Support Infrastructure

`Py4GWCoreLib/py4gwcorelib_src` should be treated as the next support/infrastructure layer above the `Py4GWCoreLib` source-of-truth modules.

This is not another primitive layer and not another source-of-truth layer.

It is complementary code that acts as a shared base for higher abstractions built in Python on top of the source-of-truth modules.

This layer:

- provides reusable support systems used by more abstract project code
- serializes, coordinates, transforms, or assists higher-level operations
- should be treated as infrastructure/support code rather than direct domain truth
- sits above `Py4GWCoreLib` source-of-truth semantics and below more abstract automation/application code

### `py4gwcorelib_src` Role Groups (initial classification)

#### Decision and Execution Orchestration

- `BehaviorTree`
  - Full behavior-tree implementation for higher-level logic.
  - Provides a full tree runtime with:
    - a shared `NodeState` model (`RUNNING`, `SUCCESS`, `FAILURE`)
    - a base `Node` abstraction with unified `tick()` wrapping over `_tick_impl()`
    - shared blackboard propagation
    - a single tree-level execution entry point
  - The base node layer also tracks rich execution metadata, including:
    - per-node tick count
    - last/total/average execution time
    - logical running-duration tracking (`run_last_duration_ms`, `run_accumulated_ms`)
    - persistent metrics with resettable transient state
  - It includes built-in structure inspection and visualization helpers:
    - ASCII tree printing
    - PyImGui tree rendering
    - state-colored node display with timing metadata
  - It exposes multiple concrete node families, not just a generic tree shell:
    - leaf/action nodes:
      - `ActionNode`
      - `ConditionNode`
      - `SucceederNode`
      - `FailerNode`
    - composite flow-control nodes:
      - `SequenceNode`
      - `SelectorNode`
      - `ChoiceNode`
      - `ParallelNode`
    - repeater/loop nodes:
      - `RepeaterNode`
      - `RepeaterUntilSuccessNode`
      - `RepeaterUntilFailureNode`
      - `RepeaterForeverNode`
    - decorator / transformation nodes:
      - `InverterNode`
    - dynamic composition:
      - `SubtreeNode` for lazy runtime tree construction from a factory
    - wait / timing nodes:
      - `WaitNode`
      - `WaitUntilNode`
      - `WaitUntilSuccessNode`
      - `WaitUntilFailureNode`
      - `WaitForTimeNode`
  - Several node types support callable signature introspection, allowing callbacks/conditions to receive the node itself when needed, which makes blackboard-aware logic and dynamic runtime state injection a first-class pattern.
  - Wait/retry nodes include both throttled and unthrottled variants, plus timeout-aware behavior, making the framework suitable for polling game state without forcing every higher layer to reinvent timing logic.
  - This should be treated as a major orchestration framework for higher automation and behavior-driven code, not as a simple utility helper.

- `FSM`
  - Full finite-state-machine implementation for higher-level sequential control flow, built around an ordered `states` list, an explicit `current_state`, step numbering, and a single `update()` loop that executes, tests exit, and performs the transition.
  - The base `State` model is a first-class step abstraction with:
    - `execute_fn`
    - `exit_condition`
    - `transition_delay_ms`
    - `run_once`
    - `on_enter`
    - `on_exit`
    - `next_state`
    - a per-state `Timer`
  - That means every normal step is explicitly gated by both execution semantics and a transition timer, rather than being just a name plus a callback.
  - The standard `State` lifecycle is:
    - enter via `enter()`
    - run through `execute()`
    - wait until `can_exit()` returns true after the delay window
    - leave through `exit()`
    - then transition into the linked `next_state`
  - It supports event-driven branching in addition to normal linear chaining:
    - each state can register named `event_transitions`
    - `trigger_event()` can force an immediate transition to a named target state
    - transition callbacks are invoked for both event-driven jumps and normal polling transitions
  - It exposes multiple specialized step types, not just one flat state primitive:
    - `State` for normal execute/exit-condition steps
    - `ConditionState` for condition-gated steps that can run a nested `sub_fsm`
    - `YieldRoutineState` for yield/coroutine steps managed through `GLOBAL_CACHE.Coroutines`
    - `SelfManagedYieldState` for yield/coroutine steps owned directly by the FSM itself
  - `ConditionState` is especially important because it can run a sub-FSM as a staged subroutine:
    - it evaluates `condition_fn`
    - when the condition path requires it, it resets and starts the child FSM
    - it then keeps updating that child FSM until it finishes
    - only after the sub-FSM completes does the parent step become eligible to exit
  - Coroutine handling is a major part of the framework and exists in two distinct execution models:
    - global coroutine steps:
      - `AddYieldRoutineStep()`
      - registers the yielded routine into `GLOBAL_CACHE.Coroutines`
      - the step waits until that routine is no longer present in the global coroutine list
    - FSM-local coroutine steps:
      - `AddSelfManagedYieldStep()`
      - stores the yielded routine inside `managed_coroutines`
      - the FSM advances these generators itself each `update()`
      - the step waits until the routine is no longer tracked in that local list
  - In addition to state-bound coroutine steps, the FSM also supports named externally managed coroutines:
    - `AddManagedCoroutine()`
    - `RemoveManagedCoroutine()`
    - `AddManagedCoroutineStep()`
    - `RemoveManagedCoroutineStep()`
    - `HasManagedCoroutine()`
    - `AdoptGlobalCoroutine()`
  - This makes the FSM usable not only for step-to-step progression, but also for starting, stopping, and owning side routines as part of the same control-flow graph.
  - The main builder APIs are:
    - `AddState()` for normal steps
    - `AddSubroutine()` for conditional sub-FSM steps
    - `AddYieldRoutineStep()` for global coroutine-backed steps
    - `AddSelfManagedYieldStep()` for FSM-owned coroutine-backed steps
    - `AddManagedCoroutineStep()` / `RemoveManagedCoroutineStep()` for side-routine lifecycle control
    - `AddWaitState()` for timeout-aware blocking/polling steps
  - Lifecycle and recovery controls are also first-class:
    - `start()`
    - `stop()`
    - `reset()`
    - `restart()`
    - `terminate()`
    - `pause()` / `resume()`
    - `ResetAndStartAtStep()`
    - `jump_to_state_by_name()`
    - `jump_to_state_by_step_number()`
  - `ResetAndStartAtStep()` and the explicit jump helpers are especially important for recovery-oriented designs, because they allow an FSM to resume from a known stage instead of always restarting from the first step.
  - The framework also includes orchestration-facing introspection and control helpers:
    - state counts and indices
    - current/next/previous step names
    - `run_until()`
    - transition callbacks
    - completion callbacks
    - runtime interruption hooks
    - optional console logging
  - Overall, this should be treated as a major orchestration framework for staged routines, sequential workflows, coroutine-aware step machines, and recoverable state-driven automation logic.

- `VectorFields`
  - Important higher-level control/steering support system.
  - It is specifically a probe-centered force-synthesis helper for movement steering:
    - it starts from a `probe_position`
    - it computes unit vectors toward or away from nearby influences
    - it sums those influences into a final combined movement vector
  - It supports two influence sources:
    - configured agent arrays
      - each with its own radius
      - each marked as either dangerous (repulsion) or safe (attraction)
    - custom world positions
      - custom repulsion positions
      - custom attraction positions
      - each with configurable radii
  - Its core workflow is:
    - register agent arrays and/or custom positions
    - inspect positions through `Agent.GetXY()` and `Utils.Distance()`
    - compute per-source attraction/repulsion vectors
    - merge them in `compute_combined_vector()`
    - optionally produce a one-shot result through `generate_escape_vector()`
  - In practice, this makes it a lightweight steering-field generator rather than a full path planner:
    - it does not replace `Pathing`
    - it complements `Pathing`, `FSM`, and `BehaviorTree` by giving higher layers a directional bias or avoidance vector
  - This should be classified alongside `BehaviorTree` and `FSM` as part of the broader decision/execution orchestration family rather than as a generic utility.
  - It should be treated as orchestration-adjacent infrastructure for higher automation and movement/behavior logic, especially local avoidance, attraction, and escape steering.

- `WidgetManager`
  - Major callback-driven script orchestration layer.
  - Acts as an orchestrator for setting up and managing callback-based execution in the system.
  - Allows multiple scripts/widgets to run in the system through the callback infrastructure.
  - Includes widget discovery/loading, lifecycle handling, and script-management responsibilities.
  - This should be treated as one of the key higher-level runtime orchestration systems in the support layer.

#### Action Dispatch and Sequencing

- `ActionQueue`
  - Serializes in-game actions and dispatches them one by one.
  - This should be treated as a sequencing/dispatch infrastructure layer for action execution.

#### Timing, Concurrency, and Configuration Infrastructure

- `Timer`
  - Provides timer and throttled-timer implementations.
  - This should be treated as shared timing infrastructure used by higher orchestration and scheduling systems.

- `MultiThreading`
  - Handles multithreading in the system.
  - Includes watchdog behavior and thread lifecycle management.
  - This should be treated as concurrency/lifecycle infrastructure rather than domain logic.

- `IniHandler`
  - Handles INI-backed configuration.
  - This should be treated as configuration persistence infrastructure for higher-level systems.

- `Lootconfig_src`
  - Base layer for the loot-picking configuration system.
  - Supports configuration data that can be shared/synced across multiple accounts through the same files.
  - This should be treated as specialized configuration infrastructure for coordinated loot behavior, not as a general loot-domain source-of-truth layer.

- `Keystroke`
  - Sends keys and key combinations to the system.
  - This should be treated as a higher-level input-dispatch support layer above the lower-level keystroke primitive surface.

#### Automated Inventory Support

- `AutoInventoryHandler`
  - Handles identify/salvage flows based on whitelist/blacklist rules.
  - Operates on a timer-driven basis.
  - This should be treated as support automation built on top of the lower inventory systems, not as a new inventory source-of-truth layer.

#### Presentation Utility Support

- `Color`
  - Utility layer for color conversions and color mutation/transformation.
  - This should be treated as shared presentation/support infrastructure for rendering and UI-adjacent systems.

#### Miscellaneous Shared Utilities and Diagnostics

- `Utils`
  - Miscellaneous shared helper layer.
  - Includes conversions and general-purpose support helpers used across the codebase.
  - This should be treated as broad shared infrastructure, not as a domain-specific system.

- `Profiling`
  - Profiling support base used by a widget that profiles system activity.
  - This should be treated as diagnostics/observability infrastructure for higher-level tooling.

#### Console and System Bridging

- `Console`
  - Interface layer to `Py4GW` console/system functions.
  - This should be treated as a thin support bridge into the lower-level `Py4GW` primitive system.

### 3. `GLOBAL_CACHE` Consumer Layer

`GLOBAL_CACHE` consumes `Py4GWCoreLib` functions and libraries.

This layer:

- is desirable because it provides caching support
- depends on `Py4GWCoreLib`
- is important, but optional
- is not required in order to use the `Py4GWCoreLib` source-of-truth libraries directly
- is derivative of `Py4GWCoreLib`, not a peer source-of-truth system
- should be the preferred read interface when a corresponding cache getter exists
- should follow the same preference rule for actions/mutating operations when a corresponding cache-backed operation exists
- should fall back to direct `Py4GWCoreLib` usage when no corresponding cache surface exists
- is itself still only partially mapped; additional `GLOBAL_CACHE` modules remain to be modeled

It is also more than a loose collection of cached helpers. The `GlobalCache` root is a singleton cache orchestrator that:

- owns shared support state such as:
  - a shared `ActionQueueManager`
  - shared throttled update timers at multiple cadences
  - a coroutine list
  - a shared raw item cache used by higher item/inventory caches
- instantiates and coordinates the cache namespaces
- runs staged cache refreshes on different throttle intervals
- forces partial cache refreshes during map loading / cinematics to keep dependent state in a safe defaultable condition

This means `GLOBAL_CACHE` should be treated as a managed cache-runtime layer, not only as a set of independent mirror objects.

### `GLOBAL_CACHE` Role Rule (initial classification)

`GLOBAL_CACHE` should inherit the same conceptual role groups as the corresponding `Py4GWCoreLib` source-of-truth libraries.

The distinction is not conceptual domain. The distinction is that `GLOBAL_CACHE` provides cached versions of those same concepts.

For the currently visible party-related cache surfaces:

- `GLOBAL_CACHE.Party`
  - Same conceptual role as `Py4GWCoreLib.Party`, but cached.

- `GLOBAL_CACHE.Party.Players`
  - Same conceptual role as the player-members portion of party state, but cached.

- `GLOBAL_CACHE.Party.Heroes`
  - Same conceptual role as the hero-members portion of party state, but cached.

- `GLOBAL_CACHE.Party.Henchmen`
  - Same conceptual role as the henchman-members portion of party state, but cached.

- `GLOBAL_CACHE.Party.Pets`
  - Same conceptual role as the pet-members portion of party state, but cached.

For the currently visible common cache surfaces:

- `GLOBAL_CACHE.Camera`
  - Same conceptual role as `Py4GWCoreLib.Camera`, but cached/project-managed.
  - In cache form, camera mutations are action-queue-backed rather than direct calls.

- `GLOBAL_CACHE.Item`
  - Same conceptual role as `Py4GWCoreLib.Item`, but cached/project-managed.
  - Built on top of a shared raw item cache plus asynchronous item-name caching.

- `GLOBAL_CACHE.ItemArray`
  - Same conceptual role as `Py4GWCoreLib.ItemArray`, but cached/project-managed.
  - Built on top of the shared raw item cache.

- `GLOBAL_CACHE.SkillBar`
  - Same conceptual role as `Py4GWCoreLib.Skillbar`, but cached.

- `GLOBAL_CACHE.Inventory`
  - Same conceptual role as `Py4GWCoreLib.Inventory`, but cached.

- `GLOBAL_CACHE.Quest`
  - Same conceptual role as `Py4GWCoreLib.Quest`, but cached.

- `GLOBAL_CACHE.Effects`
  - Same conceptual role as `Py4GWCoreLib.Effect`, but cached.

- `GLOBAL_CACHE.Trading`
  - Same conceptual role as the `Py4GWCoreLib` NPC trading/crafting/exchange surface, but cached/project-managed.

- `GLOBAL_CACHE.Skill`
  - Same conceptual role as `Py4GWCoreLib.Skill`, but cached/project-managed.

Several cache implementations also add cache-specific behavior beyond simple mirroring:

- `RawItemCache`
  - singleton bag/item snapshot layer
  - tracks live bag contents plus transitory items not currently in bags
  - acts as the foundational substrate for `GLOBAL_CACHE.Item`, `GLOBAL_CACHE.ItemArray`, and `GLOBAL_CACHE.Inventory`
- `GLOBAL_CACHE.Item`
  - adds asynchronous item-name request/result caching with timeout handling
- `GLOBAL_CACHE.Skill`
  - memoizes `PySkill.Skill` instances and preserves the same nested conceptual groupings (`Data`, `Attribute`, `Flags`, `Animations`, `ExtraData`)
- `GLOBAL_CACHE.Camera`
  - mirrors the broader `Camera` state surface, but routes mutating actions through the shared action queue
- `GLOBAL_CACHE.Party`, `GLOBAL_CACHE.SkillBar`, `GLOBAL_CACHE.Quest`, and `GLOBAL_CACHE.Trading`
  - similarly preserve their core domain meaning while routing active operations through the queue-backed cache runtime

- `GLOBAL_CACHE.ShMem`
  - This is not just a cached mirror of a `Py4GWCoreLib` domain.
  - It is the implementation handle for the shared memory / multiboxing coordination layer.
  - It acts as:
    - a pushed data layer so other accounts can read account data from other clients
    - a messaging layer so other accounts can communicate with other accounts
  - It also has substantially more internal structure than the current bridge exposure suggests:
    - a dedicated `shared_memory_src` schema layer with many typed shared-memory structs
    - an `AllAccounts` aggregate shared-memory layout
    - producer/consumer coordination logic over Python `shared_memory`
    - throttled publication for hero and pet updates
    - integration with `IniManager` for multi-account follow-formation configuration and runtime follow settings

### 4. Shared Memory / Multiboxing Coordination Layer

In the multiboxing environment, multiple clients can be interacted with through a shared-memory-driven coordination layer.

This layer lives inside `GLOBAL_CACHE`, centered around its shared memory support.

This layer:

- uses `GLOBAL_CACHE` shared memory facilities
- supports coordination across multiple clients/accounts
- provides pushed cross-account data so other accounts can read account data from other clients
- handles messaging between accounts
- is the first explicitly modeled higher layer above the base data-access stack
- is backed by a large typed shared-memory schema for account, agent, party, map, quest, skillbar, title, and message data

It should be treated as a coordination layer built on top of the data-access stack, not as a new foundational source of truth.

### 5. Combat Automation Layer

On top of the source-of-truth, cache, and shared execution infrastructure, the project has a combat automation layer built around two closely related systems:

- `Py4GWCoreLib.SkillManager.Autocombat`
- `HeroAI.CombatClass`

These two systems should be treated as parallel automation engines with almost the same combat core.

#### Shared Combat Core

Both systems implement the same broad combat pipeline:

- read the current skillbar into a local 8-slot skill model
- load custom skill metadata from the shared `CustomSkillClass` definitions
- build a priority order over the skillbar
- advance through that order with a rotating skill pointer
- decide whether the current slot is ready to cast
- resolve an appropriate target for the selected skill
- validate detailed cast conditions
- compute aftercast timing
- issue the actual skill use through `GLOBAL_CACHE.SkillBar.UseSkill`

This means both systems are not simple “auto use next skill” helpers. They are full rule-driven combat schedulers.

#### Shared Decision Model

The shared decision model includes:

- priority sorting by:
  - custom skill `Nature`
  - skill `SkillType`
  - assassin combo ordering
  - then remaining fallback skills
- target resolution by target category:
  - enemy
  - enemy subtypes such as caster / martial / melee / clustered / moving / conditioned / enchanted / hexed
  - ally and ally subtypes
  - self
  - pet
  - dead ally
  - spirit
  - minion
  - corpse
- cheap pre-cast checks before expensive target selection:
  - current casting state
  - recharge
  - energy cost
  - health sacrifice
  - adrenaline
  - spirit-buff duplication
  - vow-of-silence style hard blocks
- target-dependent checks after a candidate target is found:
  - combo requirements
  - detailed cast-condition evaluation
  - duplicate-effect prevention

This is a two-stage evaluator: cheap gate first, expensive tactical evaluation second.

#### Shared Condition Engine

Both systems have a large cast-condition engine, not just one or two checks.

That engine combines:

- unique per-skill logic for special-case skills
- generic condition flags for:
  - health / energy thresholds
  - condition / hex / enchantment / weapon-spell presence
  - movement / attack / casting / knockdown state
  - party-wide requirements
  - counts of nearby enemies, allies, spirits, and minions
- status/effect checks derived from:
  - `Agent`
  - `Effects`
  - `Routines.Checks`
  - custom shared-effect metadata

This should be treated as a rules engine for “should this skill be cast now,” not merely as a few hardcoded exceptions.

#### Shared Timing and Execution Model

Both systems also share the same timing model:

- they track an “in casting routine” state
- they calculate aftercast windows from:
  - activation
  - aftercast
  - weapon-attack timing when relevant
  - current ping
- they support profession-specific timing modifiers such as:
  - Fast Casting
  - Expertise
- they distinguish between:
  - in-combat skills
  - out-of-combat preparation/maintenance skills
- when no skill can be cast, they can fall back to target acquisition / auto-attack-oriented behavior

So this layer is explicitly scheduler-based and aftercast-aware, not just event-triggered.

#### `SkillManager.Autocombat`

`SkillManager.Autocombat` should be treated as the single-account local combat automation surface.

It is important that `SkillManager` is not fully independent from `HeroAI`: the file directly reuses `HeroAI` pieces for:

- custom skill definitions
- shared combat enums/types
- targeting helpers

So architecturally, `SkillManager.Autocombat` is a local/single-account adaptation of the same broader combat-automation logic family, not a completely separate design.

Its defining characteristics are:

- local account only
- local targeting and local party-target interpretation
- direct reliance on `Routines`, `GLOBAL_CACHE`, and local `Player`/`Agent` state
- no party/account shared-memory cache layer required to operate
- simpler runtime envelope than `HeroAI`

It should be treated as the minimal core combat automation entry point for one client.

#### `HeroAI.CombatClass`

`HeroAI.CombatClass` should be treated as the multibox combat analog of `SkillManager.Autocombat`.

Its combat logic is intentionally near-isomorphic to the single-account version, but it is embedded in a larger multibox control package with:

- `CacheData`
  - per-frame local cache state
  - game throttling
  - local account options
  - a `CombatClass` instance
- `PartyCache`
  - shared-memory-backed view of active accounts in the same map or party
- `Settings`
  - persistent global and per-account HeroAI configuration
- `commands`
  - command fanout through `GLOBAL_CACHE.ShMem.SendMessage`
- `ui` / `windows`
  - multibox control and party/hero panels

This means `HeroAI` is not only an autocombat engine. It is a multibox automation package whose combat component is one subsystem inside a broader account-coordination runtime.

#### Single-Account vs Multibox Difference

The key conceptual difference is not the combat reasoning itself. It is the runtime context around that reasoning.

- `SkillManager.Autocombat`
  - single local account
  - uses the shared combat logic directly against local state

- `HeroAI.CombatClass`
  - multi-account / party-aware
  - uses shared memory, per-account options, shared account snapshots, and remote command/messaging infrastructure
  - can reason about party members using shared-memory-backed data paths that do not exist in the purely local path

For example, `HeroAI` uses multibox-aware helpers for:

- party/account discovery
- shared effect visibility on party members
- shared option toggles (combat, targeting, skill enables, following, avoidance, looting)
- remote command dispatch to other accounts

So the right architectural model is:

- one common combat-automation core
- two operational contexts:
  - local single-account (`SkillManager`)
  - coordinated multibox package (`HeroAI`)

### 6. Bot Orchestration Layer

Above the combat automation layer, the project has a higher bot orchestration layer centered on:

- `Py4GWCoreLib.Botting.BottingClass`

This should be treated as the main bot-construction and bot-scheduling surface, not as a raw routine helper.

This same architectural tier also contains a newer BehaviorTree-oriented orchestration path centered on:

- `Py4GWCoreLib.BottingTree.BottingTree`

The two systems are related, but they are not the same runtime:

- `BottingClass` is the FSM/coroutine bot orchestration stack
- `BottingTree` is the BehaviorTree/planner/service orchestration stack

Both belong to the broader bot orchestration layer because both sit above task helpers and combat automation and are responsible for composing larger automation flows.

#### Core Purpose

`BottingClass` is a bot runtime wrapper that:

- owns a named `FSM`
- builds a bot-specific execution graph
- schedules both normal FSM states and coroutine-backed steps
- attaches long-lived managed upkeep coroutines
- exposes grouped helper namespaces for assembling bot behavior

Its core job is to sequence bot actions as a staged state machine while also running parallel upkeep/background routines.

#### Layered Wrapper Structure

`Botting` is explicitly composed of multiple wrapper layers, not one monolithic class:

- `BottingClass`
  - the top-level bot facade
  - owns lifecycle (`Start`, `Stop`, `Update`, `StartAtStep`)
  - owns the configurable main `Routine()`
- `BotConfig`
  - the internal runtime/configuration container
  - owns:
    - the bot `FSM`
    - `build_handler`
    - path/path-drawing state
    - config properties
    - upkeep configuration
    - event container
    - state counters for unique step naming
- `BottingHelpers`
  - the helper aggregation layer
  - groups helper families used to actually construct/schedule bot behavior
- `subclases_src` wrappers
  - the project-facing grouped bot namespaces exposed on the bot instance itself
  - these wrap helper/config behavior into user-facing “bot scripting” surfaces

So `BottingClass` should be understood as a façade over config, helpers, and grouped scripting namespaces.

#### Adjacent `BottingTree` Orchestration Stack

The project also includes a second high-level bot orchestration surface in `Py4GWCoreLib.BottingTree`.

This stack should be modeled as a parallel orchestration family, not as a subcomponent of `BottingClass`.

Its core structure is:

- `BehaviorTree`
  - the generic node runtime and execution semantics
- `RoutinesBT` from `routines_src/BehaviourTrees.py`
  - reusable task-specific subtree builders
- `BottingTree`
  - the runtime wrapper that owns:
    - one planner tree
    - one root parallel tree
    - optional upkeep/service trees
    - optional headless HeroAI participation

So while `BottingClass` sequences work through `FSM` plus coroutine scheduling, `BottingTree` sequences work through planner and service `BehaviorTree` instances.

That means these two orchestration families should be distinguished as:

- `BottingClass`
  - FSM-first orchestration
  - wrapper namespaces schedule steps into the classic bot runtime
- `BottingTree`
  - BehaviorTree-first orchestration
  - planner and upkeep helpers are composed as explicit trees

Neither replaces the other conceptually. They are two different high-level automation composition models in the same project.

#### Script-Local BT Wrapper Facades

Above `RoutinesBT`, some script families introduce an additional local authoring facade, for example:

- `Sources/ApoSource/ApoBottingLib/wrappers.py`

This layer should not be treated as a new orchestration runtime.

Instead, it is a script-facing convenience facade that sits between authored sequence modules and the shared BT helper catalog.

Its purpose is to:

- present shorter or more domain-friendly helper names
- adapt local parameter conventions such as `Vec2f`-based movement inputs
- curate a smaller helper surface for one script family
- hide repetitive `RoutinesBT` call shapes from high-level authored sequence code

Conceptually, the layering is:

- `BehaviorTree`
  - execution kernel
- `RoutinesBT`
  - reusable shared BT helper library
- `ApoSource` wrappers
  - script-local facade over shared BT helpers
- authored sequence modules such as `beautiful_pre_searing_src/getting_started.py`
  - compose the actual quest or planner flow
- `BottingTree`
  - owns runtime orchestration of those trees

This is analogous in spirit to the older `subclases_src` bot wrappers in the `BottingClass` stack:

- both provide an ergonomic scripting surface
- but `subclases_src` targets the FSM/coroutine bot runtime
- while `ApoSource` wrappers target the BehaviorTree/`BottingTree` stack

#### FSM-Centered Scheduling Model

At the center of the system is `BotConfig.FSM`, which is instantiated as an `FSM(bot_name)`.

`Botting` uses this FSM as the main execution spine:

- configured steps are added into the FSM
- the main `Routine()` is responsible for constructing the FSM graph
- `Update()` calls `self.config.FSM.update()` while the bot is running
- `StartAtStep()` can stop/reset and jump to a named FSM step

This means `Botting` is fundamentally an FSM-driven bot runtime, not a free-form polling loop.

#### Two Step Models

`Botting` uses two distinct step-scheduling models:

- normal FSM steps
  - scheduled through `FSM.AddState()`
  - used for immediate/non-yield actions
- self-managed yield steps
  - scheduled through `FSM.AddSelfManagedYieldStep()`
  - used for coroutine-based actions that run until completion

The helper decorator layer makes this explicit:

- `fsm_step(...)`
  - wraps a helper method and schedules it as a normal `AddState()` call
- `yield_step(...)`
  - wraps a helper coroutine and schedules it as an `AddSelfManagedYieldStep()` call

So a large part of the `Botting` abstraction is translating friendly helper calls into the correct FSM step type.

#### Managed Coroutine Model

In addition to step-bound FSM states, `Botting` also uses the FSM-managed coroutine system for long-lived background routines.

This happens through:

- `FSM.AddManagedCoroutine(...)`
- `FSM.AddManagedCoroutineStep(...)`
- `FSM.RemoveAllManagedCoroutines()`

The `Botting` layer uses this for:

- perpetual upkeep loops
- side behaviors that should run while the main FSM keeps progressing
- externally configured coroutine routines

This is one of the key reasons `Botting` sits above plain `FSM`: it combines staged foreground execution with persistent background upkeep.

#### Upkeep Scheduler

The `_start_coroutines()` path wires in the background upkeep scheduler.

It registers a large set of named managed coroutines, including:

- consumable upkeep
- morale/alcohol upkeep
- summoning/boon upkeep
- auto-combat upkeep
- HeroAI upkeep
- auto-inventory-management upkeep
- auto-loot upkeep

These are implemented through `helpers.Upkeepers`, and each upkeep routine is a long-running generator that repeatedly:

- checks whether its feature is enabled
- executes the relevant maintenance action when needed
- otherwise yields/waits

This means `Botting` should be treated as a supervisor over persistent automation services, not only a scripted path of steps.

#### Build Handler Integration

`BotConfig` also owns a `build_handler`.

By default this is an `AutoCombat()` build, but it can be overridden with a custom `BuildMgr`.

That means the bot runtime is designed to plug a combat/build execution policy into the larger bot scheduler, rather than hardwiring one combat implementation.

So the combat automation layer is a dependency of `Botting`, not the entirety of `Botting`.

#### Bot Scripting Namespaces

The bot exposes a wide set of grouped scripting wrappers through `subclases_src`, including:

- `States`
- `Properties`
- `UI`
- `Items`
- `Merchant`
- `Dialogs`
- `Wait`
- `Move`
- `Map`
- `Interact`
- `Party`
- `Player`
- `Events`
- `Target`
- `SkillBar`
- `Multibox`
- `Templates`
- `Quest`

These are not independent engines. They are structured scripting façades that schedule work into the bot runtime.

For example:

- `States` exposes custom-state insertion, named-step jumps, and managed coroutine step helpers
- `Events` exposes event callback registration and event-driven coroutine routines
- `Wait`, `Move`, `Interact`, `Items`, and similar namespaces provide domain-specific bot scripting steps

So the bot API surface is intentionally organized as a DSL-like wrapper over the underlying scheduler.

#### Event Integration

`Botting` also integrates an event layer through `BotConfig.events` and the `Events` wrappers.

This event side can:

- register callbacks
- trigger event-specific coroutine routines
- pause/resume the FSM around exceptional handling flows
- coordinate recovery/reactive behaviors such as party-member-behind or death-handling sequences

This means `Botting` is not purely linear scripting. It has reactive orchestration layered on top of the main FSM.

#### Operational Model

Putting the pieces together, `Botting` should be modeled as:

- a high-level bot runtime
- built on top of `FSM`
- using:
  - normal FSM states for immediate steps
  - self-managed yield steps for coroutine steps
  - managed coroutines for background upkeep/services
- with helper and wrapper namespaces that act as a scripting DSL for building bots

In practice, this makes `Botting` the main “automation composition” layer:

- `Routines` gives reusable task units
- combat automation gives autonomous combat execution
- `Botting` sequences those pieces into a full bot lifecycle

### 7. Bridge Exposure Layer

This is the remoting layer that exposes selected project-facing surfaces over a local TCP protocol.

Current components:

- injected widget client: `Widgets/Coding/Tools/Bridge Client.py`
- external daemon: `bridge_daemon.py`
- CLI operator/tester: `bridge_cli.py`

This layer is not the architecture of the library itself. It is a transport/exposure layer over the `Py4GWCoreLib` source-of-truth layer and the `GLOBAL_CACHE` consumer layer.

### 8. MCP Adapter Layer

This is the AI/tool-facing layer that sits above the daemon control API.

Current baseline:

- stdio adapter: `py4gw_mcp_server.py`

Current exposed safe subset:

- `list_clients`
- `list_namespaces`
- `list_commands`
- `describe_runtime`
- `get_map_state`
- `get_player_state`
- `list_agents`

## Canonical Naming Map

This section exists to keep the different naming systems aligned.

### Architectural Terms

- Foundational base
  - Means: `Gw.exe` plus the extraction mechanisms (`stubs` bindings + `Py4GWCoreLib/native_src`)
  - Does not mean: `Py4GWCoreLib`, `GLOBAL_CACHE`, bridge namespaces, or MCP tools
- `Py4GWCoreLib` source-of-truth layer
  - Means: the first authoritative Python-facing libraries such as `Player`, `Agent`, and `Map`
  - Does not mean: the lowest-level extraction mechanisms or `GLOBAL_CACHE`
- `GLOBAL_CACHE` consumer layer
  - Means: a cache-backed consumer of `Py4GWCoreLib`
  - Does not mean: the primary Python-level source of truth
- Shared memory / multiboxing coordination layer
  - Means: the coordination layer built on `GLOBAL_CACHE` shared memory for multi-client interaction and account messaging
  - Does not mean: a foundational extraction layer or a primary source-of-truth layer
- Combat automation layer
  - Means: higher-level rule-driven combat scheduling built around `SkillManager.Autocombat` and `HeroAI.CombatClass`
  - Does not mean: a foundational data source or a simple utility wrapper
- Bot orchestration layer
  - Means: high-level automation composition built around `BottingClass`, its FSM scheduler, helper wrappers, and managed background coroutines
  - Does not mean: a raw task library or a direct primitive-access layer
- Bridge layer
  - Means: remote exposure over TCP
  - Does not mean: the authoritative definition of project architecture
- MCP layer
  - Means: tool-facing abstraction over daemon control commands
  - Does not mean: direct access to the raw base

### Bridge Namespace Map

The current bridge namespace registry splits into two conceptual groups.

Bridge handles that currently project `Py4GWCoreLib` source-of-truth libraries:

- `map` -> `Py4GWCoreLib.Map`
- `player` -> `Py4GWCoreLib.Player`
- `agent` -> `Py4GWCoreLib.Agent`
- `agent_array` -> `Py4GWCoreLib.AgentArray`
- `party_raw` -> `Py4GWCoreLib.Party`
- `party_corelib` -> preferred alias of `party_raw`
- `party_wrapper` -> alias of `party_raw`
- `skill` -> `Py4GWCoreLib.Skill`
- `skillbar_raw` -> `Py4GWCoreLib.SkillBar`
- `skillbar_corelib` -> preferred alias of `skillbar_raw`
- `skillbar_wrapper` -> alias of `skillbar_raw`
- `inventory_raw` -> `Py4GWCoreLib.Inventory`
- `inventory_corelib` -> preferred alias of `inventory_raw`
- `inventory_wrapper` -> alias of `inventory_raw`
- `quest_raw` -> `Py4GWCoreLib.Quest`
- `quest_corelib` -> preferred alias of `quest_raw`
- `quest_wrapper` -> alias of `quest_raw`
- `effects_raw` -> `Py4GWCoreLib.Effects`
- `effects_corelib` -> preferred alias of `effects_raw`
- `effects_wrapper` -> alias of `effects_raw`

Bridge handles that currently project `GLOBAL_CACHE` directly:

- `party` -> `GLOBAL_CACHE.Party`
- `party.players` -> `GLOBAL_CACHE.Party.Players`
- `party.heroes` -> `GLOBAL_CACHE.Party.Heroes`
- `party.henchmen` -> `GLOBAL_CACHE.Party.Henchmen`
- `party.pets` -> `GLOBAL_CACHE.Party.Pets`
- `skillbar` -> `GLOBAL_CACHE.SkillBar`
- `inventory` -> `GLOBAL_CACHE.Inventory`
- `quest` -> `GLOBAL_CACHE.Quest`
- `effects` -> `GLOBAL_CACHE.Effects`
- `shmem` -> `GLOBAL_CACHE.ShMem`

The `shmem` bridge namespace is the currently modeled bridge-facing handle into the shared memory / multiboxing coordination layer.

### Ambiguous Historical Labels

These names are still supported in the bridge but are conceptually misleading because they suggest low-level/raw access when they currently resolve to `Py4GWCoreLib` source-of-truth libraries:

- `party_raw`
- `skillbar_raw`
- `inventory_raw`
- `quest_raw`
- `effects_raw`

Preferred clearer aliases now exist:

- `party_corelib`
- `skillbar_corelib`
- `inventory_corelib`
- `quest_corelib`
- `effects_corelib`

Older compatibility aliases still exist, but are no longer preferred:

- `party_wrapper`
- `skillbar_wrapper`
- `inventory_wrapper`
- `quest_wrapper`
- `effects_wrapper`

## MCP Boundary Rule

The current preferred conceptual boundary for MCP is:

- MCP should primarily model daemon-level safe control commands
- those daemon commands should primarily wrap bridge commands that project `Py4GWCoreLib` wrappers and `GLOBAL_CACHE`
- MCP should not treat the bridge as if it were the foundational base
- MCP should not expose the foundational base directly unless that is later made explicit and intentionally designed

This keeps the MCP layer attached to stable, normalized, project-facing abstractions.

## Known Unknowns

The conceptual model is still incomplete. The major unresolved gaps are:

- there are additional architectural layers above the currently modeled stack that have not been defined yet
- there are no additional layers below the current foundational base in this model
- the full relationship between every `Py4GWCoreLib` library and the foundational extraction mechanisms is not mapped
- the exact conceptual boundaries between some `Py4GWCoreLib` modules and `GLOBAL_CACHE` may still overlap
- the full internal structure of the shared memory / multiboxing coordination layer is not yet mapped
- the complete project-facing role of modules like `Camera` and `Context` may still need deeper classification beyond the current summaries
- the full conceptual role of reflective bridge access (`<namespace>.call`) is not yet settled for long-term MCP design

These unknowns are explicitly recorded so they remain visible while the model is expanded.

## Next Conceptual Steps

To finish the conceptual model before expanding more runtime data:

1. Identify the remaining major architectural layers above the currently modeled stack that are not yet represented here.
2. Classify the currently known `Py4GWCoreLib` modules by role, not just by name.
3. Define where `GLOBAL_CACHE` should be modeled directly versus where `Py4GWCoreLib` concepts should take priority.
4. Decide whether any foundational-base extraction concepts should ever be modeled directly in MCP.
5. Expand this document domain-by-domain as new systems are clarified.
