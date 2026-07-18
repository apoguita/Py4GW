# Guild Wars Combat AI Reverse Engineering

Date: 2026-05-20 (updated with WASM pass — 2026-05-30: combat agent data structures, EXE↔WASM mapping, callback system, pressure state)
Program: `/Gw.exe(Symbols)` and `/Gw.wasm`
Tooling: REVA / Ghidra MCP

## Objective

This document summarizes the current reverse-engineering state of the client-side combat AI-related systems in `Gw.exe` and `Gw.wasm`.

The practical goal is not to fully rewrite the AI.

The practical goal is to identify the smallest native decision/output boundary that could later be hooked so a player-controlled account can consume game-owned combat decisions and translate them into player-safe actions.

In short:

- preferred outcome: let the game decide, capture the output, adapt it
- less desirable outcome: replicate the logic manually

## Source-of-Truth Update

As of May 2026, `Gw.wasm` is the semantic source of truth for combat AI function identity.
The EXE naming and addresses in earlier sections of this doc remain useful as bridge anchors,
but the WASM-side symbols should be treated as the authoritative names.

WASM naming conventions differ substantially from the stripped EXE:
- EXE uses flat `FUN_xxxxxxxx` / renamed names
- WASM uses namespaced C++ names like `IAgentView::CCharAgent::*`, `CharClient::CHeroMgr::*`, `AvSelect::*`

The bridging workflow for any new target follows `docs/CPP_WASM_MAPPING.md`:
1. find the WASM symbol name
2. use string anchors or assertion/caller patterns to locate the corresponding EXE body
3. only then encode the scanner/pattern for C++ hooking

## Executive Summary

The investigation started from heroes, pets, skills, and movement, but the strongest result is a shared `CombatAgentView` system for generic combat-capable agents.

The most important current finding is that the client appears to contain:

- a real shared combat-agent registry
- a per-tick combat subsystem
- a per-agent update method
- internal action codes and action-state transitions
- action-record dispatchers
- a planner that turns chosen actions into timed internal execution records
- a timed trigger / timed phase system that appears to stage execution over time

Current best reusable output chain:

`UpdateCombatAgentView`
-> action-specific record handlers
-> `PlanCombatActionTimeline`
-> `ApplyCombatAgentActionState`
-> `QueueCombatTimedActionRecord`
-> timed trigger buckets
-> `HandleCombatAgentActionEvent`

That chain currently looks more promising for hooking than the public skill-use or movement entry points.

## WASM-First Combat AI Findings (May 2026)

### Agent Manager Master Tick

- `IAgentView::ManagerAdvance(float)` — `ram:80ba1628`

This is the per-frame agent system tick. It:
1. processes pending agent cleanup via `HandleClose`
2. checks sequence queue congestion
3. iterates agent arrays, dispatching virtual-function-based per-agent updates
4. delegates to partition-based spatial updates

This is the highest-level tick wrapper for all agent advancement including combat agent evaluation.

### Per-Agent Visual/Animation Advance

- `IAgentView::CCharAgent::Advance(float)` — `ram:80b5a875`

This handles per-agent animation, opacity, model state, and visual updates.
It is NOT the combat AI decision function — it processes the results of AI decisions,
not the decisions themselves.

Callees include:
- `CBaseAgent::Advance(float)`
- `ProcessActions()`
- `ProcessEffect(EffectChar*)`
- `UpdateSound()`
- `CCharAgent::LipSyncUpdate()`
- `CCharAgent::SetAnimation(EActionChar, ...)`
- `CCharAgent::ProcessActionBatch()`

### Action Dispatch System

- `IAgentView::CCharAgent::ProcessActionBatch()` — `ram:80b62abc`

This is the action-record dispatcher. It iterates through enqueued `ActionChar` records
(linked-list at `agent + 0xCC`) and dispatches each record to the appropriate per-type handler:

Action type → handler map:
- 0: `ProcessActionExecute`
- 1: `ProcessActionExecutePost`
- 2: `ProcessActionAttackFizzle`
- 3: `ProcessActionAttackWarmup`
- 4: (assertion — invalid action)
- 5: `ProcessActionEmote`
- 6: `ProcessActionEmoteAion`
- 7: `ProcessActionEmoteRank`
- 8: `ProcessActionEmoteZaishen`
- 9: `Equip(slot, itemId)`
- 10: ActionDequeue (self-dequeue)
- 11: `ProcessActionPickup`
- 12: `ProcessActionMissileLand`
- 13: `CompositeRefreshGeometry`
- 14: ActionDequeue (self-dequeue)
- 15: (assertion)
- 16: `ProcessActionExecute` (alternate path)
- 17: `ProcessActionSpellWarmup`
- 18: `ProcessActionSpellFizzle`
- 19: `ProcessActionSkillWarmup`
- 20: `ProcessActionSkillFizzle`
- 21: `SetAnimation(0x28, ...)`

This is the output-side action execution pipeline, not the decision side.

### Hero/Henchman/NPC AI Mode System

Key symbols in `Gw.wasm`:

Command entry points:
- `CharCliCommandAiMode(unsigned long, ECharAiMode)` — `ram:80c44017`
- `CharMsgSendCommandAiMode(unsigned long, ECharAiMode)` — `ram:80a123e5`

Hero-specific manager:
- `CharClient::CHeroMgr::OnCommandAiMode(unsigned long, ECharAiMode)` — `ram:80be4815`
- `CharClient::CHeroMgr::OnCommandAiPriorityTarget(unsigned long, unsigned long)` — `ram:80be4ac7`
- `CharClient::CHeroMgr::OnCommandMoveToPoint(unsigned long, MapPoint const&)` — `ram:80be4d79`
- `CharClient::CHeroMgr::OnHeroActivate(EHero, unsigned long, unsigned int, ECharAiMode)` — `ram:80be51ed`

Pet-specific manager:
- `CharClient::CPetMgr::OnCommandAiMode(unsigned long, ECharAiMode)` — `ram:80beb99c`
- `CharClient::CPetMgr::OnCommandAiPriorityTarget(unsigned long, unsigned long)` — `ram:80bebcd1`

Classification:
- `AvCharIsHenchman(unsigned long)` — `ram:80bbba66`

Target Selection:
- `AvSelectSetAutoEnabledForCombat(int)` — `ram:80bc33a9`
- `AvSelectGetActive()` — `ram:80bc29ef`
- `AvSelectGetAuto()` — `ram:80bc2a0a`
- `AvSelectSetAutoTargetMode(EAvAutoTargetMode)` — `ram:80bc291d`

UI Hero AI mode handler:
- `IUi::Game::OnCharacterHeroAiMode(unsigned int, CharHeroActive const&)` — `ram:815d6e23`

### Observed Combat AI Architecture in WASM

The WASM-side architecture differs from the earlier EXE-only model in these ways:

1. The combat agent view system (EXE's `CombatAgentView`) does NOT appear under that name in WASM.
   The naming is entirely under `IAgentView::` — e.g., `IAgentView::CCharAgent::*`, not `CombatAgentView::*`.

2. The hero/henchmen AI decision loop is NOT yet located with a single clear symbol name.
   The chain is probably:
   - `ManagerAdvance` → agent vtable dispatch → per-agent evaluation → action enqueue → `ProcessActionBatch`

3. The per-agent combat evaluation (equivalent of EXE's `UpdateCombatAgentView`) is dispatched
   through virtual function tables in the agent objects, so the actual combat evaluation function
   likely appears in WASM under a concrete class override that we have not yet identified.

4. The action execution pipeline is fully mapped under `IAgentView::CCharAgent::ProcessActionBatch()`
   with all 17+ action type handlers identified.

5. `OnCommandAiMode` in `CHeroMgr` merely stores the AI mode value and sends a frame message (0x1000003a).
   It does not itself perform combat evaluation.

### Where the Combat AI Decision Likely Lives

The combat AI evaluation (the "brain" that decides which skill to use, which target, etc.)
is most likely:

- a virtual function on `IAgentView::CCharAgent` or a subclass
- called during `ManagerAdvance` via the agent vtable
- possibly `IAgentView::AutoSelectionUpdateAgent(float)` — `ram:80a600e6`
- or a not-yet-named function inside a hero/pet/npc-specific vtable implementation

The remaining unknown is specifically:
- which vtable slot/function on a combat-capable agent performs skill/target/movement selection
- where that function enqueues actions into the `ActionChar` linked list at `agent+0xCC`

### Best Current Hook Candidates (WASM-side)

Decision-side:
- `ManagerAdvance(float)` — `ram:80ba1628` (master tick, dispatch point)
- `IAgentView::AutoSelectionUpdateAgent(float)` — `ram:80a600e6` (likely target evaluation, needs confirmation)

Output/execution-side (well mapped):
- `CCharAgent::ProcessActionBatch()` — `ram:80b62abc` (action dispatch)
- `CCharAgent::ProcessActionExecute(IAgentView::ActionChar*)` — `ram:80b74105` (skill cast execution)
- `CCharAgent::ProcessActionAttackWarmup(IAgentView::ActionChar*)` — `ram:80b6a228`
- `CCharAgent::ProcessActionSkillWarmup(IAgentView::ActionChar*)` — `ram:80b6f15c

## Investigation Path

### Hero and pet command layer

Early passes found client-side activation, commander, and mode handling for heroes and pets.

Important renamed functions:

- `0x008e9270` `RecvHeroActivatePacket`
- `0x007e8c70` `HandleHeroActivatePacket`
- `0x007f5090` `HeroActivate`
- `0x007f5170` `HeroDataAdd`
- `0x007f52a0` `HeroDeactivate`
- `0x007f5380` `HeroDisable`
- `0x007f4ff0` `HeroCommandMoveToPoint`
- `0x007f48c0` `HeroPoolFindByAgentId`
- `0x007f4970` `HeroPoolFindByHeroId`
- `0x004f59c0` `GmAgentCommander_FrameMsgHandler`
- `0x007e56f0` `SendAgentCommanderAiMode`
- `0x008eacd0` `SendAgentCommanderAiModePacket`
- `0x00508130` `PetCommander_InitFrames`
- `0x00507650` `PetCommander_FrameMsgHandler`
- `0x00508060` `PetCommander_CommitSelection`

Interpretation:

- real client-side command/state logic exists
- useful as context, but not yet the tactical combat brain

### Shared combat-agent context layer

This was the first strong generic pivot.

Renamed functions:

- `0x004f56f0` `IsAgentCommanderEligible`
- `0x005075d0` `IsPetCommanderEligibleAgent`
- `0x0050e290` `BuildAgentContextActions`
- `0x0050e830` `ExecuteAgentContextAction`

Repeated checks:

- `FUN_007b8ba0(agent)` validates an agent
- `FUN_007b84e0(agent) == 0xdb` strongly looks like a combat-capable/living agent type
- `FUN_007b6fb0(agent)` and `FUN_007b6fe0(agent)` look like classification/state helpers

Interpretation:

- heroes, henchmen, pets, and likely enemies converge on a shared combat-agent layer

### Shared skill and movement execution layers

Skill-side:

- `0x004f4d00` `TryUseSkillOnBestAvailableTarget`
- `0x007edbc0` `TryUseCombatSkillBySlot`
- `0x008eb900` `SendUseCombatSkillPacket`

Movement-side:

- `0x005da310` `AgentMovementStateSetTargetPoint`
- `0x007f23f0` `IssueMoveToWorldPoint`
- `0x007eda20` `IssueMoveToClickedPoint`
- `0x007ed900` `IssueMoveByDirectionOrOffset`
- `0x007f1f30` `TryPlanMoveWithHeadingMode`
- `0x007f2bc0` `AdvanceAgentQueuedMovement`
- `0x008eb740` `SendMoveToPointPacket`
- `0x008eb6f0` `SendDirectionalMovePacket`

Interpretation:

- both movement and skill usage clearly have shared client-side execution paths
- however, later passes suggest the shared combat-agent AI layer sits above these and does not directly emit them yet

### Native target-selection layer

Renamed functions:

- `0x007be000` `SetAutoTargetMode`
- `0x007bd610` `UpdateAutoTargetSelection`
- `0x007bd7b0` `UpdateAutoTargetSelectionMode1`
- `0x007be240` `SetCombatTargetSelection`
- `0x007be0e0` `SetPrimaryCombatTarget`

Interpretation:

- target selection is native, shared, and sits above raw execution
- this was the first strong "brain-adjacent" subsystem

### Combat subsystem wrapper

Renamed functions:

- `0x007b69c0` `UpdateCombatSubsystemTick`
- `0x007bda80` `TickAutoTargetSelection`
- `0x007bdef0` `SetAutoTargetNearestEnabled`
- `0x007bdf30` `SetAutoTargetPriorityEnabled`
- `0x007bddb0` `RefreshLockedCombatTarget`
- `0x007c0880` `RunScheduledCombatCallbacks`
- `0x007d8dc0` `UpdateCombatAgentSequences`
- `0x007cb070` `AdvanceCombatSequenceQueues`
- `0x007cdb10` `IsCombatSequenceQueueCongested`
- `0x007c5730` `UpdateCombatPressureState`
- `0x007b8dd0` `UpdateCombatTimedEffects`
- `0x007cb0c0` `DispatchCombatSequenceSetupQueue`
- `0x007c78c0` `FlushCombatSequenceVisualState`

Interpretation:

- `UpdateCombatSubsystemTick` is the high-level per-tick wrapper
- `UpdateCombatAgentSequences` is the most important behavior-side branch under it

### Shared combat-agent registry validation

Renamed functions:

- `0x007d8c00` `RegisterCombatAgentView`
- `0x007d9890` `GetAgentViewByAgentId`
- `0x007d98b0` `GetCombatAgentViewByAgentId`
- `0x007d9120` `EnumerateMatchingCombatAgents`
- `0x007d9450` `SelectBestCombatAgentView`
- `0x007b83f0` `FindBestCombatAgentId`
- `0x007d8f10` `ResetCombatAgentViewSystem`
- `0x007d9e70` `QueueCombatAgentViewCleanup`
- `0x007b8090` `InitializeCombatAgentViewSystem`
- `0x007da670` `AdvanceCombatAgentFocusGeneration`

Interpretation:

- the branch is real and shared
- this is not just UI or commander code
- `0xdb` combat-agent views are being registered, filtered, enumerated, scored, and updated

### Concrete combat-agent class

Renamed functions:

- `0x007c96f0` `ConstructCombatAgentView`
- `0x007c9e60` `DestructCombatAgentView`
- `0x007caa00` `UpdateCombatAgentView`
- `0x007cce20` `ProcessCombatAgentQueuedActions`
- `0x007cda20` `EvaluateCombatAgentSelectionScore`
- `0x007d3c60` `MatchCombatAgentSelectionFilter`
- `0x007d3e50` `HandleCombatAgentActionEvent`

Interpretation:

- this was the main structural breakthrough
- `UpdateCombatAgentView` became the best decision-side hook candidate
- `HandleCombatAgentActionEvent` became the best downstream action/event-side hook candidate

### Internal action-state layer

Renamed functions:

- `0x007d30e0` `ComputeCombatAgentMovementActionCode`
- `0x007d32a0` `SelectCombatAgentFallbackActionCode`
- `0x007c9270` `ResolveCombatActionVariant`
- `0x007d3370` `ApplyCombatAgentActionState`
- `0x007d3940` `UpdateCombatAgentActionVisuals`
- `0x007d14e0` `TickCombatActionCharQueue`
- `0x007cfc70` `DispatchCombatActionCharQueue`
- `0x007d16c0` `DispatchCombatQueuedActionRecord`

Interpretation:

- the combat-agent branch computes and applies internal action state before reaching lower public execution layers

### Action-specific record handlers

Renamed functions:

- `0x007d0d10` `ProcessCombatSkillActionRecord`
- `0x007cfa20` `ProcessCombatAttackActionRecord`
- `0x007d1070` `ProcessCombatTimedSkillActionRecord`

Interpretation:

- skills and attacks are clearly handled inside the same shared internal record pipeline
- this was a major positive sign for hookability

### Internal planner and timed trigger queue

Renamed functions:

- `0x007cb500` `PlanCombatActionTimeline`
- `0x007d2ff0` `QueueCombatTimedActionRecord`
- `0x007c11f0` `CreateCombatTimedActionTrigger`
- `0x007ccd80` `FindCombatTimedActionTriggerByType`
- `0x007d0920` `AttachCombatRecordToTimedTriggerPhaseA`
- `0x007d0a60` `AttachCombatRecordToTimedTriggerPhaseB`
- `0x007d4860` `ProcessCombatLinkedEffectActionEvent`
- `0x007d4a70` `MergeCombatActionEventIntoTimedPhases`

Interpretation:

- `PlanCombatActionTimeline` is one of the most important functions found
- it turns a chosen action into immediate state plus staged follow-up records
- timed ids such as `6`, `7`, and `8` look like shared trigger buckets / phase buckets

### Combat Agent VTable Layout (New — 2026-05-30)

Decompiled from `UpdateCombatAgentSequences` (0x007d8dc0), `EnumerateMatchingCombatAgents` (0x007b8110), and `RunScheduledCombatCallbacks` (0x007c0880):

```
CombatAgentVTable:
  +0x0C    AI_Tick(float delta_time)          — Called EVERY frame per agent; decision-making entry
  +0x10    CongestionHandler()                — Called when sequence queue backs up (type==0xDB only)
  +0x1C    MatchFilter(uint flags, void*)     — Returns bool: does agent match enumeration flags?
  +0x20    CallbackHandler(void* callback)    — Handles scheduled callbacks for this agent
```

### Combat Agent Data Structure (New — 2026-05-30)

Inferred layout from multiple decompilations of `UpdateCombatAgentSequences`, `EnumerateMatchingCombatAgents`, `UpdateCombatPressureState`, and `SetCombatTargetSelection`:

```
CombatAgentView (size ≥ ~0x1C0 bytes):
  +0x00    vtable*                  → CombatAgentVTable
  +0x2C    agent_id                 → (offset 0xB*4, from EnumerateMatchingCombatAgents)
  +0x84    position.x               → world position (FUN_007b8c20 called at 0x84 in pressure)
  +0x88    position.y
  +0x8C    position.z               
  +0x9C    type?                    → checked for 0xDB in congestion handler (likely "combat-capable agent")
  +0x110   threat_value             → (byte) contribution to combat pressure calculation
  +0x15C   flags                    → (uint) tested for 0x20000 (enemy?), 0x800 (ranged?)
  +0x1B5   combat_category          → (byte) 0x03 check in SetCombatTargetSelection (boss/elite?)
```

### RunScheduledCombatCallbacks — The AI Action Dispatcher (New — 2026-05-30)

`RunScheduledCombatCallbacks` @ `0x007c0880` is the execution engine for scheduled AI actions.
Every skill cast, movement command, and combat action initiated by the AI flows through here.

**Callback structure** (inferred from decompilation):
```
CombatCallback (size 0x28+):
  +0x00    next*              → linked list pointer (priority queue)
  +0x0C    timestamp          → float: execution time (compared against DAT_01045ee8 accumulator)
  +0x18    agent_id           → if non-zero, dispatch via GetAgentViewByAgentId → IAgentView::vtable[+0x20]
  +0x1C    executed_flag      → set to 1 after execution
  +0x24    func_ptr           → function to call when agent_id == 0
```

**Dispatch logic:**
```
If agent_id != 0:
    agent_view = GetAgentViewByAgentId(agent_id)
    agent_view->vtable[0x20](callback)    // Per-agent callback handler
else:
    callback->func_ptr(callback)           // Direct function call
```

**Key globals:**
- `DAT_00bb9060` / `DAT_00bb9068` — Priority queue of pending callbacks
- `DAT_01045ee8` — Cumulative time accumulator

### UpdateCombatPressureState — Threat Evaluation (New — 2026-05-30)

`UpdateCombatPressureState` @ `0x007c5730` evaluates combat pressure to drive combat music transitions
and behavioral state changes.

**Algorithm:**
1. Enumerate enemy agents via flags `0x1f981`
2. Count enemy threat: sum `agent[+0x110]` for each enemy (double weight for ranged, at `+0x15C & 0x800`)
3. Enumerate friendly agents via flags `0x1f808`
4. Count friendly strength: distance-adjusted sum of `agent[+0x110]` values
5. Compute ratio: `friendly_strength / enemy_threat`
6. Compare against thresholds to enter/exit combat music state

**Key globals:**
- `DAT_01046464` — Current pressure ratio
- `DAT_01046468` — Combat music active flag
- `DAT_010463e4` — Time accumulator for pressure evaluation
- `DAT_01046460` — Frame accumulator (triggers evaluation at 1.0 sec intervals)

### Updated Combat Subsystem Tick Pipeline (New — 2026-05-30)

```
UpdateCombatSubsystemTick(delta_time) @ 0x007b69c0
  │
  ├── 1. DispatchCombatSequenceSetupQueue()         0x007cb0c0
  │       Processes linked-list queue of pending combat behavior sequences
  │
  ├── 2. UpdateCombatTimedEffects(dt)               0x007b8dd0
  │       Updates buffs, conditions, timed effects
  │
  ├── 3. guard_check_icall(dt)                      (unnamed, internal)
  │       Guard/integrity validation
  │
  ├── 4. UpdateCombatPressureState(dt)              0x007c5730
  │       Evaluates threat ratio → combat music transitions
  │       Enumerates enemies (0x1f981) and friendlies (0x1f808)
  │
  ├── 5. RunScheduledCombatCallbacks(dt)            0x007c0880
  │       ★★★ Executes scheduled AI actions (skill casts, movements)
  │       Priority queue dispatch via callback structs
  │
  ├── 6. UpdateCombatAgentSequences(dt)             0x007d8dc0
  │       ★★★ Master per-agent AI tick:
  │       ├── AdvanceCombatSequenceQueues(dt)
  │       ├── Congestion check → vtable[+0x10] for type 0xDB agents
  │       └── For each agent: vtable[+0x0C](dt) + movement update
  │
  ├── 7. TickAutoTargetSelection(dt)                0x007bda80
  │       Throttled (every ~3 ticks):
  │       └── UpdateAutoTargetSelection()           0x007bd610
  │             Mode 0: EnumerateMatchingCombatAgents → closest enemy
  │             Mode 1: UpdateAutoTargetSelectionMode1()
  │             → SetCombatTargetSelection(mode, agent)
  │
  └── 8. FlushCombatSequenceVisualState(dt)         0x007c78c0
        Renders combat sequence visual effects
```

### EXE → WASM Symbol Mapping Table (New — 2026-05-30)

| EXE (Symbols) | WASM | WASM Address | Confidence |
|--------------|------|-------------|-----------|
| `TryUseSkillOnBestAvailableTarget` @ 0x004f4d00 | `IUi::Game::SkillOrderActivation(unsigned long, unsigned int)` | `ram:812475a1` | **100%** |
| `TryUseCombatSkillBySlot` @ 0x007edbc0 | `CharCliPlayerOrderSkill(unsigned long, unsigned int, unsigned long, int)` | `ram:80c4e74c` | **100%** |
| `ExecuteCombatContextAction` @ 0x004dc630 | `IUi::Game::ExecuteDefaultWorldAction(unsigned int, int, unsigned int)` | `ram:815e996e` | **95%** |
| `DoWorldAction_Func` @ 0x0050e5e0 | `IUi::Game::CoreActionExecuteWorldAction(IUi::Game::EWorldAction, unsigned long, int)` | `ram:81260cda` | **100%** |
| `CharCliAgentGetControlled()` thunk | `CharCliAgentGetControlled()` | `ram:80c13a2c` | **100%** |
| `CharCliSkillGetHotKey()` thunk | `CharCliSkillGetHotKey(unsigned long, unsigned int, unsigned int*, int*)` | `ram:80c52126` | **100%** |
| `ConstGetSkill()` thunk | `ConstGetSkill(ESkill)` | `ram:818b3d99` | **100%** |
| `CharCliPlayerCheckTargetType()` thunk | `CharCliPlayerCheckTargetType(ECharTarget, unsigned long)` | `ram:80c47c38` | **100%** |
| `AvSelectGetAuto()` thunk | `AvSelectGetAuto()` | `ram:80bc2a0a` | **100%** |
| `AvSelectGetManual()` thunk | `AvSelectGetManual()` | `ram:80bc2a40` | **100%** |
| `AvSelectHasAutoIntent()` thunk | `AvSelectHasAutoIntent()` | `ram:80bc2a5b` | **100%** |
| `AvValidate()` thunk | `AvValidate(unsigned long)` | `ram:80bba0f5` | **100%** |
| `SetPrimaryCombatTarget` @ 0x007b89e0 | `AvSelectSetManual(unsigned long)` | `ram:80bc35d7` | **100%** |
| `SendUseCombatSkillPacket` @ 0x008eb900 | *(EXE-specific wrapper — WASM calls CharMsgSendOrderSkill directly)* | N/A | EXE-only |
| `CharMsgSendOrderAttackSkill` thunk | `CharMsgSendOrderAttackSkill(unsigned int, int, unsigned long, int)` | `ram:80a13bed` | **100%** |
| `CharMsgSendOrderSkill` thunk | `CharMsgSendOrderSkill(unsigned int, int, unsigned long, int)` | `ram:80a16931` | **100%** |
| Combat AI orchestration functions (`UpdateCombatSubsystemTick`, `UpdateCombatAgentSequences`, etc.) | *(unnamed in WASM — exists under different namespace)* | N/A | Unnamed |
| `FUN_004e3320` (Combat context dispatcher) | `IUi::Game::OnKeyDown(unsigned int, FrameMsgKey const&)` | `ram:815bf776` | **70%** |

**Note:** The combat AI orchestration layer (`UpdateCombatSubsystemTick`, `UpdateCombatAgentSequences`, `UpdateCombatAgentView`, etc.) does NOT appear under those names in WASM. The WASM namespacing uses `IAgentView::` and `IUi::Game::` conventions. The EXE names are from `/Gw.exe(Symbols)` with custom annotations.

### Agent Enumeration Flags Reference (New — 2026-05-30)

| Flag | Purpose | Used In |
|------|---------|---------|
| `0x1f981` | Enemy agents | `UpdateCombatPressureState` (threat calculation) |
| `0x1f808` | Friendly agents | `UpdateCombatPressureState` (friendly strength) |
| `DAT_00bb9038 & 0x680 \| 0x301f800` | Auto-target candidates | `UpdateAutoTargetSelection` |
| *(param from TryUseSkillOnBestAvailableTarget)* | Skill-valid targets | Skill dispatch |

### Key Global Variables (New — 2026-05-30)

| Global | Address | Description |
|--------|---------|-------------|
| `DAT_00bb92d4` / `DAT_00bb92dc` | `00bb92d4` | Combat agent table (array of CombatAgentView pointers) |
| `DAT_00bb9060` / `DAT_00bb9068` | `00bb9060` | Scheduled callback priority queue |
| `DAT_00bb9038` | `00bb9038` | Auto-target filter flags |
| `DAT_00bb910c` / `DAT_00bb9114` | `00bb910c` | Temporary agent enumeration buffer |
| `DAT_01045e5c` | `01045e5c` | Current auto-target agent_id |
| `DAT_01045e64` | `01045e64` | Current combat mode target agent_id |
| `DAT_01045e80` | `01045e80` | Auto-target mode (0=nearest, 1=priority) |
| `DAT_01046468` | `01046468` | Combat music active flag |
| `DAT_01046464` | `01046464` | Current pressure/threat ratio |
| `DAT_01045ee8` | `01045ee8` | Cumulative callback time accumulator |

## Current Best Architecture Model

Current best model:

1. combat-capable agents are represented as shared `CombatAgentView` objects
2. `UpdateCombatSubsystemTick` runs broader combat systems
3. `UpdateCombatAgentSequences` dispatches per-agent updates
4. `UpdateCombatAgentView` performs local evaluation / coordination work
5. actions are converted into internal codes and variants
6. `PlanCombatActionTimeline` stages those actions into immediate state plus timed follow-ups
7. timed records are queued into shared trigger buckets
8. `HandleCombatAgentActionEvent` drains and merges later stages
9. lower-level movement, skill, effect, UI, and sync layers consume or reflect the result

## Best Current Hook Candidates

### ★★★ Recommended: `PlanCombatActionTimeline` @ `0x007cb500`

**Single choke-point for ALL AI combat actions.** Every skill cast and auto-attack from every combat agent
(heroes, henchmen, NPCs, monsters) flows through this function. It translates action decisions into
staged timed trigger records. Hook here to:

- Inspect every AI action before execution (action code, target, timing)
- Identify skills: action_code == `0x2D` (with skill_id in param3)
- Identify attacks: action_code in range `0x0C-0x15` (weapon-type-specific)
- Modify parameters or suppress execution entirely

### Action Record Handlers (per-type interception)

Decision-side (where AI decides what to do):

- `0x007caa00` `UpdateCombatAgentView` — per-agent AI tick, calls `ComputeCombatAgentMovementActionCode`
- `0x007cb500` `PlanCombatActionTimeline` ★★★ — action-to-timeline translator, ALL actions converge here

Execution-side (where decisions turn into staged records):

- `0x007d3370` `ApplyCombatAgentActionState` — applies action state to agent
- `0x007d2ff0` `QueueCombatTimedActionRecord` — enqueues a timed trigger record

Per-agent entry point:

- `0x007d8dc0` `UpdateCombatAgentSequences` — iterates all combat agents, dispatches vtable[+0x0C]

Skill-side:

- `0x007d0d10` `ProcessCombatSkillActionRecord` — handles skill records, calls PlanCombatActionTimeline(0x2D)
- `0x007d1070` `ProcessCombatTimedSkillActionRecord` — timed skill phase handler

Attack / coordination-side:

- `0x007cfa20` `ProcessCombatAttackActionRecord` — handles attack records with weapon-type mapping
- `0x007d4a70` `MergeCombatActionEventIntoTimedPhases` — merges events into timed trigger phases

Target-evaluation-side:

- `0x007d3c60` `MatchCombatAgentSelectionFilter`
- `0x007cda20` `EvaluateCombatAgentSelectionScore`
- `0x007bd610` `UpdateAutoTargetSelection`
- `0x007be240` `SetCombatTargetSelection`

Top-level subsystem:

- `0x007b69c0` `UpdateCombatSubsystemTick` — top-level orchestrator
- `0x007c0880` `RunScheduledCombatCallbacks` — executes timed callback queue

## Why Hooking Still Looks Better Than Replication

Reasons hooking looks better:

- the branch is shared and structured
- the game already computes internal action codes, variants, and timing
- skill and attack behavior are already represented inside the shared pipeline
- the timed trigger system offers natural interception points

Reasons replication looks worse:

- the logic is distributed across flags, tables, queued records, timelines, and trigger buckets
- there is no one clean standalone AI function to copy
- reproducing the exact timing and coordination behavior would be much harder than observing it

## Important Unknowns

Still unproven:

- how much final tactical authority remains server-side
- where the internal timeline branch finally reaches public movement execution
- where it finally reaches public skill execution
- full semantics of every action code
- full semantics of each timed trigger id

Resolved (2026-05-30):

- ✅ Combat agent vtable layout confirmed: `+0x0C`=AI_Tick, `+0x10`=Congestion, `+0x1C`=MatchFilter, `+0x20`=CallbackHandler
- ✅ Combat agent data structure partially mapped (position at +0x84, agent_id at +0x2C, threat at +0x110, flags at +0x15C)
- ✅ RunScheduledCombatCallbacks callback structure understood (linked list, timestamp dispatch, agent_id routing)
- ✅ UpdateCombatPressureState algorithm decoded (enemy/friendly enumeration, threat ratio, combat music state machine)
- ✅ EXE→WASM mapping for ~16 key functions confirmed with high confidence
- ✅ Agent enumeration flags identified (0x1f981=enemies, 0x1f808=friendlies)

Important negative result:

the shared combat-agent branch has not yet been shown to directly call:

- `TryUseCombatSkillBySlot`
- `IssueMoveToWorldPoint`
- `AgentMovementStateSetTargetPoint`

That strongly suggests the combat-agent layer stays above those public/shared execution functions and feeds them later through a deeper adapter path.

## False Lead

`0x00516db0` `RunAutoCombatRoutine` looked promising early because it casted, moved, and targeted.

It is very likely not the native shared combat AI because:

- it is tied to a `GmChat` path
- related strings include `/.hotkey 8 4`, `/.t %f, %f`, and `Rage mode deactivated.`

Current interpretation:

- local helper / debug / automation feature
- not the main built-in PvE combat AI branch

## Bookmarks

Bookmarks created or referenced during the session:

- `AI_FirstPass`
- `AI_CommonLayer`
- `AI_SkillUse`
- `AI_Movement`
- `AI_Brain_Clues`
- `AI_SkillCoord` at `0x007d0d10`
- `AI_OutputPort` at `0x007cb500`
- `AI_TimedPhases` at `0x007d4a70`

## Recommended Next Research

Highest-value next passes:

1. Decode the remaining timed trigger ids that appear central to execution:
   - `0xe`
   - `0x10`
   - `0x13`
   - `0x15`
2. Keep classifying action-record types inside:
   - `DispatchCombatActionCharQueue`
   - `DispatchCombatQueuedActionRecord`
3. Find where the internal planner/timeline branch finally meets:
   - public skill execution
   - public movement execution
   - outbound server synchronization
4. Test whether a small hook cluster around:
   - `UpdateCombatAgentView`
   - `PlanCombatActionTimeline`
   - `ApplyCombatAgentActionState`
   - `QueueCombatTimedActionRecord`
   is sufficient to capture reusable combat outputs

## Stability Note

REVA remained responsive throughout this investigation. No restart was needed during these passes.

## Skill Description Access Map

Date: 2026-03-26

This session also mapped the native text path relevant to obtaining skill descriptions directly, without wiki scraping.

### Core native fact

GWCA's native `Skill` layout already documents these three fields as string ids:

- `name` at `+0x98`
- `concise` at `+0x9C`
- `description` at `+0xA0`

Relevant local source:

- `vendor/gwca/Include/GWCA/GameEntities/Skill.h`
- `src/py_skills.cpp`

That means the game does not store full decoded skill descriptions in the constant skill record.
It stores text ids that must be resolved through the text subsystem.

### Confirmed local bridge path

The current Python/C++ bridge already exposes the exact primitives needed to resolve these ids:

1. read `skill.description` / `skill.concise` / `skill.name`
2. convert the uint32 id to encoded-string form with `GW::UI::UInt32ToEncStr(...)`
3. decode it with `GW::UI::AsyncDecodeStr(...)`

Relevant local source:

- `include/py_ui.h`
- `include/py_quest.h`
- `vendor/gwca/Examples/WorldInformation/main.cpp`

The map-name example in GWCA proves this pattern is valid for plain text ids:

- `area_info->name_id`
- `UInt32ToEncStr(...)`
- `AsyncDecodeStr(...)`

Skill descriptions are the strongest next candidate for the same treatment because their native fields are explicitly marked as string ids.

### Confirmed offline text-table path

The project also already contains a custom decoder for the game's string-table system in `gw.dat`:

- `Py4GWCoreLib/native_src/internals/string_table.py`
- `Py4GWCoreLib/native_src/context/TextContext.py`
- `Py4GWCoreLib/native_src/methods/DatFileMethods.py`

Important mapped facts:

- `GameContext + 0x18` -> `TextParser*`
- `TextParser` exposes current `language_id`
- `TextParser` exposes per-language file slots that point to hashed `gw.dat` text files
- the custom decoder already handles:
  - packed uint32/string-index encoding
  - optional key parsing
  - RC4-based entry decryption
  - bit-packed character decoding
  - raw UTF-16 entries
  - grammar/postprocessing cleanup

So there are now two viable direct paths:

- live/native path: `description_id -> UInt32ToEncStr -> AsyncDecodeStr`
- offline/dat path: `description_id -> encoded/string-table decode via TextParser + gw.dat`

### Ghidra anchors

Useful native functions identified in `/Gw.exe(Symbols)`:

- `0x007a1540` `Ui_CreateEncodedTextFromStringId`
- `0x007a1560` `Ui_CreateEncodedText`
- `0x005a1f90` `Ui_GetEncodedTextResourceById`
- `0x005ea970` `Ui_MultiLineTextControlProc`
- `0x005eb4b0` `Ui_ProcessMultiLineTextSegments`

Interpretation:

- `Ui_CreateEncodedTextFromStringId` is the simplest generic "string id -> encoded payload" helper
- `Ui_MultiLineTextControlProc` / `Ui_ProcessMultiLineTextSegments` are good tooltip/description-side UI anchors because long descriptions are likely rendered through the multiline text path
- `Ui_GetEncodedTextResourceById` is useful context for resource-driven text, but skill descriptions are more likely to come from runtime string ids than this smaller UI resource-id catalog

### Recommended next RE pass

Best next step is not a broad string hunt.

Best next step is:

1. pick a known skill tooltip UI frame or tooltip specimen
2. trace the frame creation path into `Ui_MultiLineTextControlProc`
3. identify the caller that supplies the encoded payload for the description body
4. confirm whether that caller pulls `skill->description` directly or routes through another small adapter

### Practical implementation hypothesis

Before deeper RE, test this directly in Python:

1. get a skill object's `description_id`
2. call the existing `UInt32ToEncStr`
3. call the existing `AsyncDecodeStr`

If that succeeds, the direct source-of-truth problem is already solved for descriptions and concise text.

If it fails, the fallback route is still local and direct:

- use the existing `TextParser` + `gw.dat` decoder to resolve the string id offline

Current judgment:

- wiki scraping should no longer be treated as the primary strategy
- the likely real source of truth is already present in-client and already partially exposed by this project

## AI Combat Path — Complete Pseudo-Code (2026-05-30)

### Overview

The AI combat system runs entirely client-side via a per-frame tick on registered `CombatAgentView` objects.
Each agent (hero, henchman, NPC, monster) evaluates its state, computes an action, and enqueues
it for staged execution through a timed trigger system.

### Architecture Layers

```
Layer 1: CombatAgentView Update     — per-agent AI tick (what should I do?)
Layer 2: Action Code Computation    — movement/action selection
Layer 3: Action Record Dispatch     — translate action into staged records
Layer 4: PlanCombatActionTimeline   — build timed trigger schedule
Layer 5: Timed Trigger Execution    — fire triggers at scheduled times
Layer 6: HandleCombatAgentActionEvent — process each trigger event
```

### Layer 1: UpdateCombatAgentView(agent, dt) @ 0x007caa00

```python
def UpdateCombatAgentView(agent: CombatAgentView, dt: float):
    # ---- State validation ----
    if agent.field_0x184 == 0 or agent.field_0xFC == 0:
        return  # agent not active
    if agent.field_0x104 != should_be_combat_mode:
        agent.field_0x104 = should_be_combat_mode
        reset_combat_state()

    # ---- Pressure/combat state init ----
    update_combat_pressure_state_agent(agent, dt)

    # ---- Altitude check ----
    agent_height = agent.field_0x8C
    ground_height = get_ground_height()
    if agent_height <= ground_height + THRESHOLD:
        agent.field_0x15C &= ~0x8000   # grounded
    else:
        agent.field_0x15C |= 0x8000    # airborne
    if agent_height <= ground_height:
        agent.field_0x15C &= ~0x4000   # on ground

    # ---- Process queued actions ----
    TickCombatActionCharQueue()        # process action records at agent+0xCC
    post_action_cleanup()

    # ---- Compute action code ----
    action_code = ComputeCombatAgentMovementActionCode(agent)  # @ 0x007d30e0
    if action_code == 0x3F:  # idle
        if agent.field_0x158 & 0x08:
            if agent.field_0x184:
                notify_action_update()
            fallback = SelectCombatAgentFallbackActionCode(agent)  # @ 0x007d32a0
            ApplyActionState(agent, fallback)  # via FUN_007d3310
        # grounded cleanup
    else:
        # Check priority of new action vs current
        current_action = agent.field_0xDC
        new_priority = ACTION_PRIORITY_TABLE[action_code]
        old_priority = ACTION_PRIORITY_TABLE[current_action]
        if new_priority <= old_priority:
            ApplyActionState(agent, action_code)  # via FUN_007d3310

    # ---- Movement/animation advance ----
    advance_combat_sequence(agent, dt)
    advance_combat_sequence(agent, dt)
    # Speed check
    speed = agent.field_0x130
    if agent.field_0x134 < speed:
        speed = agent.field_0x134
    if speed >= 1.0:
        return
    if speed < EPSILON:
        speed = 0.0
    if speed > 1.0:
        speed = 1.0
    if abs(speed - agent.field_0x16C) > THRESHOLD:
        agent.field_0x16C = speed
        update_movement_blend()  # @ 0x007cb820
```

### Layer 2: ComputeCombatAgentMovementActionCode(agent) @ 0x007d30e0

```python
def ComputeCombatAgentMovementActionCode(agent: CombatAgentView) -> int:
    """Returns action code 0x00-0x3F based on movement direction"""
    # Read velocity and facing direction
    vx = agent.field_0xA4      # velocity X
    vy = agent.field_0xA0      # velocity Y
    speed_sq = vy*vy + vx*vx

    if speed_sq == 0.0:
        # Agent is stationary
        if agent.field_0x58 & 0x2000:
            return 0x1F           # special stance A
        if agent.field_0x58 & 0x4000:
            return 0x3F           # idle
        return 0x1E               # default stance

    # Normalize velocity
    divisor = fast_sqrt(speed_sq)
    vx /= divisor
    vy /= divisor

    # Dot product with facing direction
    fx = agent.field_0x50        # facing X
    fy = agent.field_0x54        # facing Y
    dot_forward = vx*fx + vy*fy

    # Determine direction quadrant
    if dot_forward <= THRESHOLD_BACKWARD:                       # DAT_00a5b6d8
        direction_index = 0     # backward
    elif dot_forward >= THRESHOLD_FORWARD:                      # DAT_00a5b720
        direction_index = 4     # forward
    else:
        # Cross product for left/right
        cross = fx*vx - fy*vy
        is_right = cross > 0
        if dot_forward <= THRESHOLD_MID_BACK:                   # DAT_00a5b6b0
            if dot_forward <= THRESHOLD_NEUTRAL_BACK:           # DAT_00a5b718
                direction_index = 3 if is_right else 2          # strafe back
            else:
                direction_index = 2 + is_right * 4              # mid strafe
        else:
            direction_index = 1 + (6 if is_right else 0)        # slight turn

    # Look up final action code from movement table
    if agent.field_0x13C & 0x08:
        return MOVEMENT_TABLE_SPECIAL[direction_index]          # DAT_00a5b3f8
    if agent.field_0x184 and speed_sq >= THRESHOLD_RUNNING:     # DAT_00a5b710
        return MOVEMENT_TABLE_RUNNING[direction_index]          # DAT_00a5b418
    if speed_sq < THRESHOLD_WALKING:                            # DAT_00a5b70c
        return MOVEMENT_TABLE_WALKING[direction_index]          # DAT_00a5b478
    if agent.field_0x15C & 0x01:
        return MOVEMENT_TABLE_COMBAT[direction_index]           # DAT_00a5b458
    return MOVEMENT_TABLE_DEFAULT[direction_index]              # DAT_00a5b438
```

### Layer 2b: SelectCombatAgentFallbackActionCode(agent) @ 0x007d32a0

```python
def SelectCombatAgentFallbackActionCode(agent: CombatAgentView) -> int:
    """Returns stance/idle action code when no movement is chosen"""
    if agent.field_0x15C & 0x08:
        return 0x3D           # dead/disabled
    if agent.field_0x13C & 0x4000:
        return 0x00           # special stance
    if agent.field_0x13C & 0x2000:
        return 0x01           # alternate stance
    if agent.field_0x15C & 0x01:
        # In combat: random stance
        r = rand() & 7
        return 3 + (0 if r < 5 else 4)
    # Out of combat: check weapon data
    weapon_data = get_weapon_data(agent.field_0xF4)
    if weapon_data.field_0x10 & 0x8000:
        r = rand() & 3
        if r == 3:
            return 0x02
    return 0x02           # default idle
```

### Layer 3: DispatchCombatActionCharQueue(agent) @ 0x007cfc70

```python
def DispatchCombatActionCharQueue(agent: CombatAgentView):
    """Process action records linked at agent+0xCC"""
    record = agent.field_0xCC          # ActionChar* linked list head
    iteration_count = 0

    while record != None and not (agent.field_0xCC & 1):
        iteration_count += 1
        if iteration_count > 500:
            ERROR("Infinite loop in action queue")

        action_type = record.field_0x00

        if action_type in [0, 11, 17, 22]:     # 0x00, 0x0B, 0x11, 0x16
            AttachCombatRecordToTimedTriggerPhaseA(record)

        elif action_type in [1, 18]:            # 0x01, 0x12
            AttachCombatRecordToTimedTriggerPhaseB(record)

        elif action_type == 2:                  # Full action processing
            # Clean up timed triggers
            clean_timed_triggers([0, 2, 18, 8, 6, 7])
            current_action = agent.field_0xDC
            if current_action in [0x29, 0x2A, 0x2B, 0x2C, 0x23]:
                # Mid-skill/attack: re-evaluate movement
                if not agent.field_0x15C & 0x08:
                    move_code = ComputeCombatAgentMovementActionCode(agent)
                    if move_code == 0x3F:
                        move_code = SelectCombatAgentFallbackActionCode(agent)
                else:
                    move_code = 0x3D
                ResolveCombatActionVariant(agent.field_0x1BA, move_code, &variant_a, &variant_b)
                ApplyCombatAgentActionState(agent, move_code, variant_a, variant_b, 0.0)

        elif action_type == 3:                  # Auto-attack
            ProcessCombatAttackActionRecord(agent, record)

        elif action_type == 21:                 # 0x15: SKILL USAGE
            ProcessCombatSkillActionRecord(agent, record)

        elif action_type == 25:                 # 0x19: TIMED SKILL
            ProcessCombatTimedSkillActionRecord(agent, record)

        elif action_type == 23:                 # 0x17: Movement + cleanup
            # Re-evaluate movement
            if agent.field_0x158 & 0x200:
                clean_timed_triggers([5])
            clean_timed_triggers([6])
            if agent.field_0x158 & 0x01:
                if not agent.field_0x15C & 0x08:
                    move_code = ComputeCombatAgentMovementActionCode(agent)
                    if move_code == 0x3F:
                        move_code = SelectCombatAgentFallbackActionCode(agent)
                else:
                    move_code = 0x3D
                ResolveCombatActionVariant(agent.field_0x1BA, move_code, &variant_a, &variant_b)
                ApplyCombatAgentActionState(agent, move_code, variant_a, variant_b, 0.0)
            # Sound effect
            play_combat_sound(agent, SOUND_TABLE)
            # Broadcast UI message
            Ui_BroadcastRegisteredFrameMessage(0x10000026)

        # ---- Cleanup record ----
        FUN_007ca430(record)             # dequeue and free
        agent.field_0x1B8 = 0            # clear skill_id
        agent.field_0x1B7 = 0            # clear action byte
        record = agent.field_0xCC        # next record
```

### Layer 4: PlanCombatActionTimeline(...) @ 0x007cb500

```python
def PlanCombatActionTimeline(
    agent: CombatAgentView,
    action_code: int,           # 0x2D=skill, 0x0C-0x15=weapon attacks
    variant_a: int,
    variant_b: int,
    skill_or_action_id: int,    # skill_id for skills, 0 for attacks
    cast_time: float,           # total action duration
    byte_flags: int,            # animation flags from skill data
    trigger_id: int,            # base trigger ID for this action
    out_warmup_end: float* = None,
    out_completion: float* = None
):
    """Build staged timeline of QueueCombatTimedActionRecord calls"""
    # Get timing values from skill/weapon data tables
    warmup_duration = FUN_007db9f0(agent.field_0x60, action_code, WARMUP_TABLE)   # DAT_00a59570
    if warmup_duration == 0.0:
        warmup_duration = MINIMUM_WARMUP

    offset_duration = 0.0
    agent_type = agent.field_0x1BB
    if agent_type in [0x05, 0x1C]:
        offset_duration = FUN_007db9f0(agent.field_0x60, action_code, OFFSET_TABLE)  # DAT_00a59540

    # Adjust cast_time based on flags
    factor = 0.0 if byte_flags == 0 else THRESHOLD_VALUE
    warmup_end = cast_time * factor - SUBTRACT_VALUE
    mid_marker = warmup_end + ADD_VALUE
    total_time = warmup_end + SUBTRACT_VALUE

    # Get post-activation timing
    post_activation = FUN_007db9f0(agent.field_0x60, action_code, POST_TABLE)  # DAT_00a5957c
    if post_activation == 0.0 and byte_flags != 0:
        post_activation = cast_time * FACTOR2 + total_time

    # Check if action fits within warmup
    if total_time <= warmup_duration + EPSILON:
        # Action fits within warmup → apply immediately
        progress = total_time / warmup_duration
        atk_speed = FUN_007db8b0(agent.field_0x60, action_code)
        scaled_timing = atk_speed * progress
        scaled_offset = progress * offset_duration
        scaled_post = progress * post_activation

        ApplyCombatAgentActionState(agent, action_code, variant_a, variant_b, scaled_timing)

        # Optional: animation speed modifier
        if trigger_id != 0 and agent.field_0x70 != 0.0:
            FUN_007cc8d0(trigger_id, warmup_end)
    else:
        # Action exceeds warmup → split into stages
        gap = total_time - warmup_duration
        fallback_timing = gap + offset_duration
        fallback_post = post_activation + gap
        has_sub_action = agent.field_0x100 != 0

        ResolveCombatActionVariant(agent.field_0x1BA, 0x23, &variant_a2, &variant_b2)
        ApplyCombatAgentActionState(agent, 0x23, variant_a2, variant_b2, 0.0)
        QueueCombatTimedActionRecord(
            timing=gap,
            trigger_type=4,
            skill_or_action_id=variant_a,
            flags=(0x80 if not has_sub_action else 0) | (action_code << 8) | trigger_id << 16 | skill_or_action_id & 0xFFFF
        )

    # Always queue these timed triggers
    QueueCombatTimedActionRecord(warmup_end + 0.0,   0x12, 0, 0)  # pre-action
    QueueCombatTimedActionRecord(warmup_end + mid,   8,    0, 0)  # mid-action
    QueueCombatTimedActionRecord(total_time,          6,    0, 0)  # action start
    if offset_duration != 0.0:
        QueueCombatTimedActionRecord(fallback_timing, 2,    0, 0)  # offset
    if fallback_post != 0.0:
        QueueCombatTimedActionRecord(fallback_post - EPSILON, 0x12, 0, 0)  # post-action marker
        QueueCombatTimedActionRecord(fallback_post,          7,    0, 0)  # completion

    if out_warmup_end:
        *out_warmup_end = scaled_or_fallback_timing
    if out_completion:
        *out_completion = total_time
```

### Layer 5: QueueCombatTimedActionRecord(timing, trigger_type, data, flags) @ 0x007d2ff0

```python
def QueueCombatTimedActionRecord(timing: float, trigger_type: int, data: int, flags: int) -> TimedRecord:
    """Enqueue a timed trigger record into the shared trigger queue"""
    record = allocate_record()
    record.timing = timing          # execution time offset from now
    record.trigger_type = trigger_type
    record.data = data
    record.flags = flags
    insert_into_priority_queue(TRIGGER_QUEUE, record)
    return record
```

### Layer 5b: RunScheduledCombatCallbacks(dt) @ 0x007c0880

```python
def RunScheduledCombatCallbacks(dt: float):
    """Execute timed callbacks whose time has arrived"""
    CUMULATIVE_TIME += dt
    queue = TRIGGER_QUEUE          # DAT_00bb9060 / DAT_00bb9068
    if queue == None:
        return

    record = queue.head
    while record != None and record.field_0x0C < CUMULATIVE_TIME:
        record.field_0x1C = 1      # mark as executed
        agent_id = record.field_0x18

        if agent_id == 0:
            # Direct function call
            if record.field_0x24 != None:
                record.field_0x24(record)
        else:
            # Dispatch via agent vtable
            agent_view = GetAgentViewByAgentId(agent_id)
            if agent_view != None:
                agent_view.vtable[0x20](record)   # calls HandleCombatAgentActionEvent

        process_record()
        dequeue_record(record)
        free_record(record)

        record = queue.head
        if record == None:
            break
```

### Layer 6: HandleCombatAgentActionEvent(agent, event) @ 0x007d3e50

```python
def HandleCombatAgentActionEvent(agent: CombatAgentView, event: TimedRecord):
    """Process a timed trigger event based on trigger_type"""
    trigger_type = event.field_0x20

    # Find existing record of same type in agent's linked list at agent+0x1B0
    existing = find_existing(agent, trigger_type)
    if existing and existing.field_0x1C == 0:
        return  # already handled

    # Clear flag for this trigger type
    flag_mask = FLAG_TABLE[trigger_type]
    agent.field_0x158 &= ~flag_mask

    if trigger_type == 1:       # Initial setup
        FUN_007cb1d0(1)

    elif trigger_type == 2:     # Begin action
        FUN_007cdb70(0, 0, DATA_TABLE, 1.0, 1)

    elif trigger_type == 3:     # Action-specific
        FUN_007d4560(event.field_0x28)

    elif trigger_type == 4:     # ★ SKILL/ACTION DISPATCH
        packed = event.field_0x2C           # packed data from QueueCombatTimedActionRecord
        skill_or_action_id = packed & 0xFFFF
        trigger_extra = (packed >> 16) & 0x7F
        has_target = (packed >> 23) & 1
        action_code = (packed >> 24) & 0xFF

        target_agent_id = event.field_0x28   # target (if any)
        if target_agent_id == 0:
            target_agent_id = -1

        # Resolve variant if sub-action flag differs
        if (agent.field_0x100 != 0) != has_target:
            ResolveCombatActionVariant(agent.field_0x1BA, action_code, &variant_a, &variant_b)
            skill_or_action_id = variant_a
            target_agent_id = variant_b

        ApplyCombatAgentActionState(agent, action_code, skill_or_action_id, target_agent_id, 0.0)

        # Animation speed modifier
        if trigger_extra != 0:
            trigger_6 = FindCombatTimedActionTriggerByType(6)
            if trigger_6:
                remaining = trigger_6.field_0x0C - CUMULATIVE_TIME
                if remaining > 0 and agent.field_0x70 != 0:
                    FUN_007cc8d0(trigger_extra, remaining)

    elif trigger_type == 6:     # Action completion — process linked effects
        agent.field_0x158 &= ~0x0400
        linked_records = event.field_0x38
        while linked_records:
            record_type = linked_records.field_0x00
            if record_type == 0:
                FUN_007cde10(0, 0)
            elif record_type == 11:
                ProcessCombatLinkedEffectActionEvent(linked_records)
            elif record_type in [17, 22]:
                Ui_BroadcastRegisteredFrameMessage(0x10000024)
            dequeue_and_free(linked_records)
            linked_records = next_record
        # Clear skill tracking
        agent.field_0x1B8 = 0
        agent.field_0x1B7 = 0

    elif trigger_type == 7:     # Cleanup
        if event.field_0x28:
            FUN_007cc280(event.field_0x28, 0x10000, 0)
        agent.field_0x158 &= ~0x0400
        # Drain remaining records
        while linked_records:
            dequeue_and_free(linked_records)

    elif trigger_type == 8:     # Mid-action merge
        MergeCombatActionEventIntoTimedPhases(event)

    elif trigger_type == 13:    # Clear stance flag
        agent.field_0x15C &= ~0x2000
        FUN_00750250(agent.field_0x60, 8)

    elif trigger_type == 18:    # 0x12: death/defeat sound
        if agent.field_0x58 & 0x02:
            if agent.field_0x1BB == 0x2E:
                sound_id = FUN_0046fa50(agent.field_0x60)
            else:
                sound_id = FUN_00804af0(agent.field_0xFC, 0, 0)
            if sound_id:
                FUN_007c5360(sound_id, 5, agent.field_0x84 + 0x00, agent.field_0x15C >> 22 & 1)
                free_handle(sound_id)

    elif trigger_type == 19:    # 0x13: special variant
        if agent.field_0x158 & 0x10:
            if ACTION_PRIORITY[agent.field_0xDC] <= THRESHOLD:
                result = ResolveCombatActionVariant(agent.field_0x1BA, 0x3A, &a, &b)
                if result == 0:
                    fallback = SelectCombatAgentFallbackActionCode(agent)
                    ApplyActionViaVariant(agent, fallback)
                else:
                    ApplyCombatAgentActionState(agent, 0x3A, a, b, event.field_0x28)
```

### Layer 6b: ApplyCombatAgentActionState(agent, action_code, variant_a, variant_b, timing) @ 0x007d3370

```python
def ApplyCombatAgentActionState(
    agent: CombatAgentView,
    action_code: int,
    variant_a: int,
    variant_b: int,
    timing: float
):
    """Apply a new action state to the agent"""
    assert action_code <= 0x3E

    old_flags = agent.field_0x158
    old_action = agent.field_0xDC

    # Get flag mask/value for action transition
    FUN_007c9050(old_action, action_code, &new_flags_mask, &new_flags_value)
    agent.field_0x158 = (agent.field_0x158 & ~new_flags_value) | new_flags_mask

    # Movement tracking toggle
    was_moving = old_flags & 0x02
    is_moving  = agent.field_0x158 & 0x02
    if agent.field_0x184 and was_moving != is_moving:
        if is_moving:
            start_movement_tracking(agent.field_0x2C, agent.position, variant_b)
        else:
            stop_movement_tracking(agent.field_0x2C)

    # Store new action code
    agent.field_0xDC = action_code

    # Update visual/action state
    UpdateCombatAgentActionVisuals(agent, variant_a, variant_b, timing)
```

### ProcessCombatSkillActionRecord — Full Flow @ 0x007d0d10

```python
def ProcessCombatSkillActionRecord(agent: CombatAgentView, record):
    """Process a skill action record — called from DispatchCombatActionCharQueue type 0x15"""
    skill_id = record.field_0x38         # ID of the skill being used
    target_id = record.field_0x30        # target agent ID
    record_flag = record.field_0x3C       # flag (0 = normal, 1 = offhand?)

    agent.field_0x1B8 = skill_id          # track current skill

    # Get skill constant data
    skill = ConstGetSkill(skill_id)
    cast_time = skill.field_0x3C          # total cast time

    # ---- Special skill type 0x1B (resurrection?) ----
    if skill.field_0x0C == 0x1B:
        # Plays special animation sound
        ...

    # ---- Skill type 0x0E (attack skill) ----
    if skill.field_0x0C == 0x0E:
        # Get animation timing
        anim_byte = skill.field_0x32
        if anim_byte == 0:
            anim_byte = 2

        # Resolve variant based on offhand flag
        if record_flag == 0:
            variant_code = 0x29        # main-hand skill
        else:
            variant_code = 0x2A        # off-hand skill
        ResolveCombatActionVariant(agent.field_0x1BA, variant_code, &variant_a, &variant_b)

        # Adjust cast time
        adjusted_time = cast_time
        if adjusted_time == 0.0:
            adjusted_time = agent.field_0xEC          # base attack speed
        adjusted_time *= agent.field_0xF0              # speed modifier
        if record_flag:
            adjusted_time *= OFFHAND_FACTOR             # DAT_0091de00

        # ★★★ BUILD THE TIMELINE ★★★
        PlanCombatActionTimeline(
            agent,
            action_code=0x2D,              # "use skill"
            variant_a=variant_a,
            variant_b=variant_b,
            skill_id=record_flag,           # pass record flag as skill_id param
            cast_time=adjusted_time,
            byte_flags=anim_byte,
            trigger_id=anim_byte,
            out_warmup=warmup_ptr,
            out_completion=completion_ptr
        )
        agent.field_0x1B7 = record.field_0x34

    # ---- Notify target agent ----
    target_agent = GetCombatAgentViewByAgentId(target_id)
    if target_agent:
        FUN_007cb270()                       # notify target of incoming action

    # ---- Broadcast UI message ----
    Ui_BroadcastRegisteredFrameMessage(0x10000027)     # "agent used skill" UI notification

    # ---- Cleanup ----
    FUN_007ca430(record)                     # dequeue record
```

### Callable Function Summary

All these functions are designed to be called with a `CombatAgentView*` pointer. To call them from Python, you would need:

1. **Get a CombatAgentView*** — via `GetCombatAgentViewByAgentId(agent_id)` @ 0x007d98b0
2. **Check if agent is in combat** — via `agent.field_0x15C & flags`
3. **Use the skill** — call `ProcessCombatSkillActionRecord` or directly call `PlanCombatActionTimeline`

| Function | Address | Args | What it does |
|----------|---------|------|-------------|
| `GetCombatAgentViewByAgentId` | `0x007d98b0` | (id) → CombatAgentView* | Resolve agent |
| `ComputeCombatAgentMovementActionCode` | `0x007d30e0` | (agent) → int | Get movement action code |
| `SelectCombatAgentFallbackActionCode` | `0x007d32a0` | (agent) → int | Get idle stance code |
| `ResolveCombatActionVariant` | `0x007c9270` | (type, code, &a, &b) | Resolve action variant |
| `ApplyCombatAgentActionState` | `0x007d3370` | (agent, code, a, b, t) | Apply action state |
| `PlanCombatActionTimeline` | `0x007cb500` | (agent, code, a, b, skill, time, flags, tid, ...) | Build trigger timeline |
| `QueueCombatTimedActionRecord` | `0x007d2ff0` | (time, type, data, flags) → TimedRecord* | Enqueue trigger |
| `ProcessCombatSkillActionRecord` | `0x007d0d10` | (agent, record*) | Process skill record |
| `ProcessCombatAttackActionRecord` | `0x007cfa20` | (agent, record*) | Process attack record |

