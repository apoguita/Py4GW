# BottingTree And BT Routines Guide

This document explains the current botting wrapper stack built around:

- `Py4GWCoreLib/BottingTree.py`
- `Py4GWCoreLib/routines_src/BehaviourTrees.py`
- `Py4GWCoreLib/py4gwcorelib_src/BehaviorTree.py`

It covers:

- what `BottingTree` owns
- how planner sequences are injected and restarted
- how upkeep/service trees work
- what `RoutinesBT` provides
- how a script should integrate with the system
- important execution details that affect behavior

## Overview

The runtime is split into three layers:

1. `BehaviorTree`
   - The generic BT framework: nodes, sequences, selectors, parallel nodes, subtree nodes, waits, action nodes, blackboard propagation, and state normalization.

2. `RoutinesBT` (`BehaviourTrees.py`)
   - A library of reusable behavior-tree helpers.
   - These helpers return ready-to-run `BehaviorTree` instances for common game actions such as movement, targeting, dialog, map travel, and imp handling.
   - Discovery for the upcoming configurator is now expected to be metadata-driven from this layer.

3. `BottingTree`
   - A wrapper/controller that runs:
     - headless HeroAI
     - the user planner tree
     - optional upkeep/service trees
   - It exposes a script-friendly API for start/stop/pause, planner sequencing, restart-from-step, and movement overlay drawing.

## The Actual BehaviorTree Layer

`BottingTree` and `RoutinesBT` are both built on top of the core `BehaviorTree` framework in [BehaviorTree.py](/c:/Users/Apo/Py4GW_python_files/Py4GWCoreLib/py4gwcorelib_src/BehaviorTree.py).

That framework provides:

- the canonical `NodeState`
- node lifecycle and `tick()`
- composite nodes such as sequence/selector/parallel
- decorator and utility nodes
- `SubtreeNode` for runtime-built subtrees
- blackboard propagation
- timing and tracing support

In practice:

- `RoutinesBT` is a library of prebuilt `BehaviorTree` subtrees
- `BottingTree` is a higher-level orchestration wrapper that assembles multiple trees into one root parallel execution model

So the relationship is:

- `BehaviorTree` defines how trees run
- `RoutinesBT` defines reusable trees
- `BottingTree` decides which trees run together, when they start, and how scripts interact with them

## Discovery Contract

The BT helper layer is now expected to participate in configurator discovery through a shared docstring contract.

The important rule is:

- metadata is mandatory for discovery
- no metadata means ignore

This means the parser should not attempt to infer user-facing meaning from:

- helper-only support code
- low-level implementation details
- nested local routines that did not opt in through metadata

### Contract Shape

Discoverable surfaces use:

1. a human-readable description
2. a structured `Meta:` block

Current `Meta:` keys used in the BT helper preparation work:

- `Expose`
- `Audience`
- `Display`
- `Purpose`
- `UserDescription`
- `Notes`

This applies to:

- the BT root catalog surface in `BehaviourTrees.py`
- grouped BT helper classes
- BT helper routines that are intended to be visible to the upcoming configurator

Support/helper code can still carry metadata too, typically with `Expose: false`, so discovery does not have to guess intent.

## BehaviorTree Concepts That Matter

### NodeState

The only valid runtime state is `BehaviorTree.NodeState`.

The framework normalizes node return values to that canonical enum. This is important because planner logic, wrapper logic, and helper logic all depend on terminal state propagation being consistent.

Valid states are:

- `RUNNING`
- `SUCCESS`
- `FAILURE`

### Nodes And Trees

A `BehaviorTree` instance wraps a root node.

That means there are two related but different concepts:

- `BehaviorTree.Node`
- `BehaviorTree`

Most user-facing helper APIs return a full `BehaviorTree`, because that is easier to compose safely in scripts.

Internally, the framework can often coerce between the two:

- if a full `BehaviorTree` is passed where a node is expected, the framework can use `.root`
- if a node is passed where a tree is needed, it can be wrapped as `BehaviorTree(node)`

This compatibility matters because planners, composites, and subtree factories often mix both forms.

### Blackboard

Every node can access a shared `blackboard` dictionary.

This is the main data-sharing mechanism between:

- HeroAI service logic
- planner logic
- movement runtime state
- service/upkeep trees

`BottingTree.blackboard` is effectively the root shared state for the wrapper.

### Composite Nodes

The framework provides standard control-flow nodes such as:

- `SequenceNode`
- `SelectorNode`
- `ChoiceNode`
- `ParallelNode`

These are the building blocks behind most `RoutinesBT` helpers.

Typical use:

- `SequenceNode`: run steps in order
- `ParallelNode`: run watchers/services beside a main task
- `SubtreeNode`: build a child tree at runtime
- `SwitchNode`: select one subtree from a runtime value such as profession, mode, or route variant

## Current Preparation Status

For the current session state:

- `BehaviourTrees.py` is the intended BT helper catalog root
- extracted BT helper group files now follow the shared contract guidance
- BT helper discovery should be treated as metadata-gated rather than inference-driven
- `Composite` is support/helper code, not a primary discovery target
- `BottingTree` remains runtime/orchestration infrastructure, not a helper catalog source

For the project status beyond metadata preparation:

- BT discovery is already loading metadata successfully
- parsed signatures are already available on the discoverable helper surface
- stable call references are already available for generated code targets such as `RoutinesBT.Map.TravelToOutpost`
- the remaining work is primarily taking discovered signatures, filling them with chosen values, and rendering valid Python calls

This is why the current state is closer to generation than it may initially appear:

- discovery is no longer the main blocker
- helper identity is no longer the main blocker
- the next bridge is parameter-value modeling and final code emission

### ActionNode

`ActionNode` has an important behavior that affects helper design.

It does not immediately emit terminal state after the action function returns `SUCCESS` or `FAILURE`.

Instead:

1. the action function returns a terminal state
2. `ActionNode` stores that result
3. it returns `RUNNING` during its `aftercast_ms`
4. once aftercast finishes, it emits the final state

This makes `ActionNode` good for:

- actions with a built-in wait
- commands that need settle time

But it also means it is not ideal for every watcher/helper. Some helpers need immediate terminal propagation instead of the extra delayed tick shape.

### SubtreeNode

`SubtreeNode` is one of the most important pieces for this wrapper stack.

It allows a node to build a full subtree dynamically from a factory.

That is what makes helpers like runtime movement and named planner steps practical:

- the subtree can be built when it is first ticked
- it can read live context
- it can be reset and rebuilt cleanly later

Current framework behavior:

- subtree is created lazily
- the parent blackboard is propagated
- on reset, the subtree is reset and discarded
- next execution gets a fresh subtree instance

This is critical for avoiding stale state across repeated planner executions.

### SwitchNode

`BehaviorTree.SwitchNode` is the generic value-based branch selector.

Use it when:

- a planner step depends on a runtime value already stored on the blackboard
- the branch is not naturally modeled as selector success/failure
- you want a single generic routing node instead of profession-specific or quest-specific wrappers

Example:

```python
BehaviorTree.SwitchNode(
    selector_fn=lambda node: node.blackboard.get("player_primary_profession_name", ""),
    cases=[
        ("Warrior", Warrior_001_Sequence),
        ("Ranger", Ranger_001_Sequence),
        ("Monk", Monk_001_Sequence),
    ],
    name="RunProfessionSequence",
)
```

This is the preferred pattern for route/profession switching in scripts.

## Core Composition

`BottingTree` builds one root parallel tree.

That root contains:

- a HeroAI service branch
- a planner service branch
- zero or more service/upkeep branches

Conceptually:

```text
Root Parallel
|- HeroAIService
|- PlannerService
|- ServiceTree: OutpostImpService
|- ServiceTree: ExplorableImpService
|- ...
```

This means:

- HeroAI is always ticked as a service
- the planner is the main user script flow
- upkeepers run independently beside the planner

## How BottingTree Uses BehaviorTree

`BottingTree` is itself not a replacement for `BehaviorTree`. It is a wrapper that builds and owns several actual trees.

Internally it maintains:

- one planner `BehaviorTree`
- one root parallel `BehaviorTree`
- zero or more service `BehaviorTree` instances
- one headless HeroAI tree that is ticked as a service branch

The wrapper then exposes script-level lifecycle control around that underlying BT execution.

Conceptually:

```text
Script
  -> BottingTree
      -> Root Parallel BehaviorTree
          -> HeroAI service tick branch
          -> Planner tick branch
          -> Upkeep/service branches
```

This separation is important:

- script authors usually work with `BottingTree` and `RoutinesBT`
- helper authors usually work with `BehaviorTree` node semantics
- wrapper bugs often come from the relationship between terminal state propagation and wrapper ownership

## Why The Relationship Matters

Most of the subtle behavior in this system comes from how `BottingTree` depends on correct `BehaviorTree` semantics.

Examples:

- if a planner subtree never propagates `SUCCESS`, `BottingTree` cannot auto-stop
- if a service tree returns terminal every tick, the wrapper will keep resetting it
- if a `SubtreeNode` keeps stale state, repeated planner legs can reuse old runtime data
- if a helper uses `ActionNode` where immediate terminal propagation was required, wrapper-level behavior can appear delayed or incorrect

So when troubleshooting:

- `BehaviorTree` explains how state propagates
- `RoutinesBT` explains what the helper is trying to do
- `BottingTree` explains how the wrapper reacts to that state

## BottingTree Responsibilities

`BottingTree` is the script-facing controller.

Main responsibilities:

- own the headless HeroAI instance
- own the current planner tree
- own upkeep/service trees
- maintain the shared blackboard
- expose planner sequence management
- expose movement path drawing helpers
- auto-stop when the planner reaches terminal state

Important constructor:

```python
botting_tree = BottingTree(INI_KEY, pause_on_combat=True)
```

### Blackboard Access Helpers

`BottingTree` also exposes direct shared-blackboard access helpers:

- `GetBlackboardValue(key, default=None)`
- `SetBlackboardValue(key, value)`
- `ClearBlackboardValue(key)`
- `HasBlackboardValue(key)`

These are useful for:

- UI state that depends on planner/runtime data
- debug reads without importing helper internals
- script-level flags that should live beside wrapper state

### Lifecycle API

Main lifecycle methods:

- `Start()`
- `Stop()`
- `Reset()`
- `Pause(pause=True)`
- `IsStarted()`
- `IsPaused()`

Behavior:

- `Start()` starts ticking the wrapper
- `Stop()` stops and resets runtime state
- `Reset()` resets:
  - root tree
  - planner tree
  - headless HeroAI
  - all service trees
  - blackboard contents

## Planner Trees

The planner is the main user flow.

You can inject it in two ways:

### 1. Set a planner directly

```python
botting_tree.SetPlannerTree(my_planner_tree)
```

Use this when you already built a single `BehaviorTree`.

### 2. Inject named sequence builders

```python
botting_tree.SetNamedPlannerSteps(
    _get_sequence_builders(),
    start_from=selected_start_sequence,
    name="All quests sequence",
)
```

This is the preferred mode for long scripts.

`_get_sequence_builders()` returns a list like:

```python
def _get_sequence_builders():
    return [
        ("Common_001", Common_001_Sequence),
        ("Warrior_001", Warrior_001_Sequence),
    ]
```

Each entry is:

- a step name
- a builder or tree-like object

`BottingTree` converts those steps into one planner sequence internally.

### Planner Sequence Helpers In BottingTree

Planner-related methods:

- `SetNamedPlannerSteps(steps, start_from=None, name="PlannerSequence")`
- `GetNamedPlannerStepNames()`
- `BuildAllSequences(start_from=None, name=None)`
- `RestartFromNamedPlannerStep(step_name, auto_start=True, name=None)`
- `RestartFromSequence(sequence_name, auto_start=True, name=None)`

This is intentionally owned by `BottingTree`, not `RoutinesBT`, because this is wrapper-level planner management.

### Multi-Tree Script Pattern

The wrapper is not limited to one script-global tree.

A script can own multiple named `BottingTree` instances in a registry and tick them all from `main()`.

Typical pattern:

```python
botting_trees: dict[str, BottingTree] = {}

def _ensure_prepare_tree(auto_start: bool = False) -> BottingTree:
    if "Prepare Character" not in botting_trees:
        tree = BottingTree(INI_KEY)
        tree.SetNamedPlannerSteps(get_sequence_builders(MODULE_NAME), name="All quests sequence")
        botting_trees["Prepare Character"] = tree
    tree = botting_trees["Prepare Character"]
    if auto_start:
        tree.Start()
    return tree

def main():
    for tree in botting_trees.values():
        tree.tick()
```

This is the preferred pattern when a UI has multiple independent buttons that should launch unrelated flows.

### Planner Terminal Behavior

When the planner returns terminal state:

- `SUCCESS`:
  - logs `Planner tree completed.`
  - stops the wrapper
- `FAILURE`:
  - logs `Planner tree failed.`
  - stops the wrapper

The planner is therefore a bounded flow, not an always-on service.

## Upkeepers / Service Trees

Upkeepers are independent parallel trees that run beside the planner.

This is the BT equivalent of the older coroutine-based upkeeper model.

Public API:

- `SetServiceTrees(steps)`
- `AddServiceTree(name, subtree_or_builder)`
- `ClearServiceTrees()`
- `GetServiceTreeNames()`

Convenience aliases:

- `SetUpkeepTrees(steps)`
- `AddUpkeepTree(name, subtree_or_builder)`
- `ClearUpkeepTrees()`
- `GetUpkeepTreeNames()`

Example:

```python
botting_tree.SetUpkeepTrees([
    ("OutpostImpService", lambda: RoutinesBT.Upkeepers.OutpostImpService(
        target_bag=1,
        slot=0,
        log=False,
    )),
    ("ExplorableImpService", lambda: RoutinesBT.Upkeepers.ExplorableImpService(
        log=False,
    )),
])
```

### Service Tree Behavior

Service trees are meant to be persistent watchers or maintenance routines.

If a service returns:

- `SUCCESS`
- `FAILURE`

`BottingTree` resets that service tree and keeps the wrapper alive.

This makes service trees suitable for:

- outpost maintenance
- imp handling
- one-shot watchers that may need to run again later
- future town/explorable maintenance routines

## Shared Blackboard

All branches run against the same wrapper blackboard.

This is how HeroAI, planner logic, and movement cooperate.

Examples of wrapper blackboard values:

- `COMBAT_ACTIVE`
- `LOOTING_ACTIVE`
- `PAUSE_MOVEMENT`
- `HEROAI_STATUS`
- `PLANNER_STATUS`
- `PLANNER_OWNER`

Movement helpers also publish telemetry into the same blackboard.

## Headless HeroAI Integration

`BottingTree` owns a `HeroAIHeadlessTree`.

The wrapper ticks HeroAI as a service branch and reads its state back into the blackboard.

Current wrapper behavior:

- HeroAI is gated on map readiness
- HeroAI combat state is exposed
- HeroAI looting state is exposed
- planner movement can pause while HeroAI owns combat or looting

Important point:

- planner logic is not halted just because HeroAI is active
- instead, movement helpers react to blackboard pause flags

This avoids losing planner context during combat or looting.

### HeroAI Toggle Trees

`BottingTree` exposes reusable BT helpers that request HeroAI enable/disable through the wrapper blackboard.

Helpers:

- `BottingTree.EnableHeroAITree(reset_runtime=True)`
- `BottingTree.DisableHeroAITree(reset_runtime=True)`
- `BottingTree.ToggleHeroAITree(reset_runtime=True)`

These return `BehaviorTree` instances and are meant to be used directly inside planner sequences.

This is useful for scripted special cases where a planner temporarily needs to own combat behavior itself, then hand control back to headless HeroAI.

## RoutinesBT Overview

`BehaviourTrees.py` exposes the helper namespace `BT`.

In scripts this is normally imported as `RoutinesBT`.

Main helper groups:

- `RoutinesBT.Player`
- `RoutinesBT.Map`
- `RoutinesBT.Items`
- `RoutinesBT.Agents`

These helpers return `BehaviorTree` instances and are meant to be used directly inside planner sequences or upkeep trees.

Some routines are built by composing smaller helpers internally, but the main user-facing emphasis is on the grouped helper surfaces such as player, map, items, and agents.
- `MoveTargetInteractAndDialog(...)`
- `MoveTargetInteractAndAutomaticDialog(...)`

These are direct-access helpers. They take real routine parameters, not prebuilt subtree arguments.

Example:

```python
RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(
    x=9954.21,
    y=-472.19,
    button_number=0,
    log=False,
)
```

## Player Helpers

`RoutinesBT.Player` contains user-facing actions and movement.

Examples:

- `Wait(duration_ms, log=False)`
- `PrintMessageToConsole(source, message)`
- `LogMessageToBlackboard(source, message, ...)`
- `LogMessage(source, message, ...)`
- `SendAutomaticDialog(button_number, log=False)`
- `SendDialog(dialog_id, log=False)`
- `SendChatCommand(command, log=False)`
- `Resign(log=False)`
- `ChangeTarget(agent_id, log=False)`
- `Move(...)`

### Player.Wait

`RoutinesBT.Player.Wait(...)` is a real BT helper.

It wraps:

- optional start logging
- `BehaviorTree.WaitForTimeNode`

Example:

```python
RoutinesBT.Player.Wait(duration_ms=250, log=False)
```

### Player.LogMessage

`RoutinesBT.Player.LogMessage(...)` is the preferred script-facing logging helper.

It can:

- print to console
- write to the shared blackboard log history
- do both at once

Current blackboard log keys are fixed:

- `last_log_message`
- `last_log_message_data`
- `blackboard_log_history`

`to_console` can be either:

- a boolean
- a callable returning a boolean

Passing a callable is useful for UI-driven runtime toggles, because already-instanced trees will read the current value when they execute instead of using a stale value captured at construction time.

### Player.Move

`RoutinesBT.Player.Move(...)` is the main movement subtree.

Current design:

- autopath builds per execution
- state is local to the move runtime
- path progress is tracked per waypoint
- timeout is per waypoint, not per whole route
- map transition is watched in parallel
- pause/resume is built into the movement runtime

Important current behavior:

- normal timeout is per waypoint
- after any pause, recovery to the same waypoint gets `3x` timeout
- this applies to:
  - combat pauses
  - looting pauses
  - casting pauses
  - external pause flag
  - other movement pause conditions in the routine

Movement always writes telemetry to the blackboard.

Published fields include:

- `move_state`
- `move_reason`
- `move_target`
- `move_path_index`
- `move_path_count`
- `move_path_points`
- `move_current_waypoint`
- `move_current_waypoint_index`
- `move_last_move_point`
- `move_resume_recovery_active`

Movement failure always logs even when `log=False`.

### Player.MoveDirect

`RoutinesBT.Player.MoveDirect(...)` reuses the exact same movement runtime as `Move(...)`, but skips autopath generation and consumes a caller-supplied list of waypoints.

Use it when:

- the script already knows the exact point list to walk
- you want the normal pause/recovery/timeout/stall behavior
- you do not want autopath generation for that segment

Example:

```python
RoutinesBT.Player.MoveDirect(
    path_points=[
        (-6316.87, -6808.10),
        (-4833.97, -12199.93),
        (-3464.73, -13135.62),
    ],
    log=False,
)
```

## Agent Helpers

`RoutinesBT.Agents` contains target-acquisition helpers.

Examples include:

- `TargetNearestNPC(...)`
- name/model lookup helpers
- `ClearEnemiesInArea(...)`

The agent-name path is now based on synchronous lookup, not the old async request/wait pattern.

Current reusable lookup/composition patterns also include model-based helpers such as:

- `TargetAgentByModelID(...)`
- `MoveAndTargetByModelID(...)`
- `MoveTargetInteractAndAutomaticDialogByModelID(...)`

These are useful when a script wants to reuse existing move/target/dialog composition but resolve the target from a model ID first.

## Map Helpers

`RoutinesBT.Map` contains map and travel helpers.

Examples:

- `TravelToOutpost(...)`
- `TravelToRegion(...)`
- `WaitforMapLoad(...)`

These are useful when a planner explicitly needs to travel or wait for a destination map before continuing.

## Item Helpers

`RoutinesBT.Items` currently contains the item and imp flows that used to live in the coroutine layer.

Examples:

- `SpawnBonusItems(...)`
- `DestroyItem(...)`
- `DestroyBonusItems(...)`
- `MoveModelToBagSlot(...)`
- `SpawnAndDestroyBonusItems(...)`
- `Upkeepers.SpawnImp(...)`
- `Upkeepers.OutpostImpService(...)`
- `Upkeepers.ExplorableImpService(...)`

### SpawnImp

`Upkeepers.SpawnImp(...)` implements the current `/bonus` imp flow:

1. issue `/bonus`
2. wait for inventory settle
3. destroy unwanted bonus items
4. preserve the imp stone
5. move the imp stone into the requested bag/slot

### OutpostImpService

`Upkeepers.OutpostImpService(...)` is the outpost-side upkeep.

Behavior:

- resets when map context becomes invalid or loading
- processes each ready outpost map once
- if imp stone is already present, it idles
- if missing, it runs `Upkeepers.SpawnImp(...)`
- after the map is processed, it idles until map change

Important implementation detail:

If a `SpawnImp` subtree is already active, the service keeps ticking that subtree until it returns terminal. It does not abandon the subtree just because the imp stone appeared in inventory partway through the process.

### ExplorableImpService

`Upkeepers.ExplorableImpService(...)` is the explorable-side upkeep.

Behavior:

- only runs in ready explorable maps
- only applies below level 20
- requires the imp stone in inventory
- does nothing if the imp is already active
- does nothing while the summoning cooldown effect is active
- attempts to use the imp stone when allowed

This lets outposts manage imp inventory and explorables manage imp upkeep.

## BehaviorTree Details That Matter

There are a few framework details script authors need to know.

### Canonical NodeState

The canonical BT state is `BehaviorTree.NodeState`.

The framework normalizes tick results to that enum.

Non-state values are not valid tree results.

### ActionNode Aftercast Behavior

`BehaviorTree.ActionNode` does not immediately emit `SUCCESS` or `FAILURE` after the action completes.

Instead:

- the action function runs
- if it returns `RUNNING`, the node returns `RUNNING`
- if it returns `SUCCESS` or `FAILURE`, the node enters aftercast
- while aftercast is active, the node still returns `RUNNING`
- only after aftercast finishes does the node emit terminal state

This matters when designing helpers:

- use `ActionNode` for action + aftercast semantics
- use immediate-return logic carefully when a terminal state must propagate without an extra delayed tick

### SubtreeNode Runtime Behavior

`BehaviorTree.SubtreeNode` builds its subtree lazily from a factory.

Important reset behavior:

- when reset, it resets the created subtree
- then discards it

That means dynamic subtree factories get a fresh subtree on the next execution.

This is important for:

- movement helpers
- reusable planner steps
- dynamic runtime-dependent subtrees

## Path Overlay Support

`BottingTree` exposes movement overlay data and drawing.

### Read move state

```python
move_data = botting_tree.GetMoveData()
```

Returns:

- `state`
- `reason`
- `target`
- `path_points`
- `path_index`
- `path_count`
- `current_waypoint`
- `current_waypoint_index`
- `last_move_point`
- `resume_recovery_active`

### Draw active route

```python
botting_tree.DrawMovePath(
    draw_labels=False,
    path_thickness=2.0,
    waypoint_radius=15.0,
    current_waypoint_radius=20.0,
)
```

Current drawing behavior:

- only draws when move state is `running` or `paused`
- does not draw stale finished paths
- does not draw already reached nodes
- only draws visible points using camera FOV checks
- uses `Color` and `ColorPalette`

This is intended for overlay use in scripts such as `Presearing Dominator.py`.

## Minimal Script Pattern

The simplest integration pattern is:

```python
from Py4GWCoreLib import *
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT

INI_KEY = "MyScript"
botting_tree = None

def MySequence() -> BehaviorTree:
    return RoutinesBT.Player.Move(x=1000.0, y=2000.0, log=False)

def _get_sequence_builders():
    return [
        ("MySequence", MySequence),
    ]

def main():
    global botting_tree
    if botting_tree is None:
        botting_tree = BottingTree(INI_KEY)
        botting_tree.SetNamedPlannerSteps(
            _get_sequence_builders(),
            name="MainSequence",
        )
    botting_tree.tick()
```

## Recommended Long-Script Pattern

For longer scripts, use named sequence builders plus optional upkeep trees.

Pattern:

```python
def _get_sequence_builders():
    return [
        ("Common_001", Common_001_Sequence),
        ("Warrior_001", Warrior_001_Sequence),
        ("Ranger_001", Ranger_001_Sequence),
    ]

botting_tree = BottingTree(INI_KEY)

botting_tree.SetUpkeepTrees([
    ("OutpostImpService", lambda: RoutinesBT.Upkeepers.OutpostImpService(
        target_bag=1,
        slot=0,
        log=False,
    )),
    ("ExplorableImpService", lambda: RoutinesBT.Upkeepers.ExplorableImpService(
        log=False,
    )),
])

botting_tree.SetNamedPlannerSteps(
    _get_sequence_builders(),
    start_from=selected_start_sequence,
    name="All quests sequence",
)
```

Advantages:

- sequence restart is easy
- script organization scales cleanly
- upkeepers stay independent of planner logic
- planner steps remain readable and testable

## Current Reference Scripts

Good reference points in the repo:

- [Presearing Dominator.py](/c:/Users/Apo/Py4GW_python_files/Presearing%20Dominator.py)
  - long-form planner
  - named sequence restart
  - upkeepers
  - path overlay drawing

- [Absolute Pre-Searing.py](/c:/Users/Apo/Py4GW_python_files/Absolute%20Pre-Searing.py)
  - multi-tree registry pattern
  - button-triggered tree instancing
  - blackboard-backed UI log panel
  - runtime console-log toggle via `LogMessage(..., to_console=lambda: ...)`

- [botting_tree_template.py](/c:/Users/Apo/Py4GW_python_files/botting_tree_template.py)
  - minimal wrapper setup

- [HeroAI_ParallelTree_Example.py](/c:/Users/Apo/Py4GW_python_files/HeroAI_ParallelTree_Example.py)
  - parallel planner usage
  - movement test flow

## Practical Guidance

Use `BottingTree` for:

- planner ownership
- sequence management
- restart-from-step
- HeroAI coordination
- service/upkeep execution
- path visualization

Use `RoutinesBT` for:

- the actual behavior trees your planner or upkeep needs to run

Keep this separation:

- `BottingTree` manages execution and orchestration
- `RoutinesBT` provides reusable tree logic
- the script provides named steps and user-facing flow

## Summary

The current stack is designed so that a script can:

- register named planner sequences once
- register upkeep/service trees once
- let HeroAI run continuously
- pause planner movement when HeroAI owns the moment
- restart from a specific sequence when needed
- draw the live movement path for debugging or overlays

That is the intended model for future botting scripts built on this wrapper.
