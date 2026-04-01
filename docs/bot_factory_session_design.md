# Bot Factory Session Design

This document captures the design context, decisions, and planning outcome from the session focused on a wizard-first authoring system for BehaviorTree-based construction.

The goal of this record is not only to preserve the final plan, but also to preserve the reasoning and repo context that led to it so the session can be replicated later with minimal ambiguity.

## Why This Session Happened

The existing botting stack already supports composing behavior trees by stitching together reusable helpers and subtree builders.

The problem identified in this session was not a missing runtime system.

The problem was authoring.

The intended audience for this tool is close to zero-code users. They need a RAD-style utility that helps them construct behavior trees without needing to understand:

- raw `BehaviorTree` implementation details
- the lower-level code structure of `RoutinesBT`
- how builder functions are written by hand
- how planner trees are normally assembled in Python

At the start of the session, there was an initial idea of using a drag-and-drop node system, partly inspired by `Py4GWCoreLib/dNodes/dNodes.py`.

As the discussion evolved and more repo context was reviewed, the direction became much clearer:

- a visual node editor is not required for the first design
- a wizard plus hierarchical list/tree editor is enough
- the new system should be a configuration layer over the existing BT stack
- the system should help users compose trees, subtrees, and reusable pieces
- the system should generate valid Python in the same structural shape expected by the current BT framework

## Repo Context Reviewed In This Session

The following files were examined and used as the main source of truth during the session:

- [docs/bottingtree_and_bt_routines_guide.md]
- [Py4GWCoreLib/py4gwcorelib_src/BehaviorTree.py]
- [Py4GWCoreLib/routines_src/BehaviourTrees.py]
- [Py4GWCoreLib/BottingTree.py]
- [Absolute Pre-Searing.py]
- [Sources/ApoSource/absolute_pre_searing_src/prepare_quests.py]
- [Py4GWCoreLib/dNodes/dNodes.py]
- [Py4GWCoreLib/Botting.py]
- [Py4GWCoreLib/botting_src/config.py]
- [Py4GWCoreLib/botting_src/subclases_src/TEMPLATES_src.py]
- [Py4GWCoreLib/botting_src/subclases_src/UI_src.py]

## Architectural Context Learned During The Session

### 1. The Existing Runtime Is Already Layered

The repo already has a clean three-layer botting stack:

1. `BehaviorTree`
2. `RoutinesBT` from `BehaviourTrees.py`
3. `BottingTree`

This matters because the new system should not replace these layers.

It should sit above them and configure them.

#### `BehaviorTree`

`BehaviorTree.py` is the execution kernel.

It provides:

- canonical `NodeState`
- structural nodes such as `SequenceNode`, `ParallelNode`, `SwitchNode`
- `ActionNode`
- `ConditionNode`
- `SubtreeNode`
- lifecycle/reset semantics
- blackboard propagation

Important runtime implications noted during the session:

- `ActionNode` has aftercast behavior and does not immediately emit terminal state after a successful action
- `SubtreeNode` lazily builds subtrees and discards them on reset
- structural hierarchy is real and strict, not cosmetic
- parent/child relationships matter for both generation and reconstruction

These are critical because the authoring tool must generate valid BT structure, not a loose approximation.

#### `RoutinesBT`

`Py4GWCoreLib/routines_src/BehaviourTrees.py` is the reusable helper library.

It exposes public helper surfaces grouped as:

- `Player`
- `Map`
- `Items`
- `Agents`
- `Skills`

These groups became the preferred catalog grouping for the new authoring system.

Important observations from the session:

- the file contains both public end-user helpers and internal helper-of-helper functions
- internal helper functions often start with `_`
- public end-user helpers are the correct built-in authoring surface
- helper signatures are consistent enough to support discovery-driven wizard forms
- some helpers are built by stitching together subtrees and smaller helpers
- discovery should not infer meaning from raw implementation details when metadata is missing
- the shared docstring contract is now the intended discovery gate for the upcoming system

#### `BottingTree`

`Py4GWCoreLib/BottingTree.py` is the wrapper/controller that orchestrates:

- planner tree
- HeroAI service branch
- service/upkeep trees
- wrapper blackboard
- start/stop/pause/restart logic

This class matters as runtime context, but it was explicitly decided in this session that it is not a helper catalog source.

It is supporting infrastructure.

The authoring tool may optionally export a full bot wrapper later, but the core authored unit is still BT code.

### 2. `Absolute Pre-Searing.py` Defines The Real Flow Pattern

The session initially drifted toward abstract authoring ideas until the user pointed back to `Absolute Pre-Searing.py` as the concrete model that should drive the design.

Reviewing that script clarified the intended flow model:

- the script composes named trees
- each tree is a `BottingTree`
- planner content is assembled by named step builders
- those steps are mostly subtree factories built from `RoutinesBT`
- the code is declarative and compositional, not deeply custom

Important examples from that script:

- `SetNamedPlannerSteps(...)`
- `SetUpkeepTrees(...)`
- use of sequence builder lists from `prepare_quests.py`
- multi-step planner content such as:
  - `Sequence_001_Common`
  - `Profession_Specific_Quest_001_Sequence`
  - `Sequence_002_Common`

The biggest takeaway was:

The system should think in terms of users constructing one big tree by stitching together smaller BT pieces, not in terms of inventing a totally separate authoring model.

### 3. `dNodes.py` Is Useful Inspiration, But Not Required

`Py4GWCoreLib/dNodes/dNodes.py` already provides:

- draggable nodes
- pins
- links
- a node space
- graph-like interaction patterns

But the session concluded that this is not required for the first design.

The main reasons were:

- the target audience is non-technical
- a wizard plus list/tree editor is easier to understand
- BT hierarchy is already naturally represented as a tree/indented list
- forcing a visual graph early would add complexity without being necessary

So `dNodes.py` remains a possible future reference, but not part of the required V1 design direction.

### 4. The Sibling Botting Configuration System Is Relevant Structurally

The session also reviewed the sibling botting system in:

- `Py4GWCoreLib/Botting.py`
- `Py4GWCoreLib/botting_src/*`

This system is not the target runtime for the new configurator, but it provided useful architectural inspiration:

- grouped helper namespaces
- config/state separation
- reusable templates
- UI override points

This reinforced the idea that the new system should expose grouped authoring surfaces, not a single giant procedural class.

However, the user explicitly clarified that:

- the helper catalog must come only from `BehaviourTrees.py`
- other classes are supporting classes, not helper sources

That clarification became part of the final design constraints.

## Product Context Clarified During The Session

The following product constraints were clarified directly in conversation and materially changed the design:

### Audience

The audience has close to zero coding experience.

Therefore:

- the system cannot assume familiarity with BT internals
- the primary interaction must be guided
- the primary surface should be a wizard and a tree/list editor
- advanced functionality should exist, but not as the primary interaction model

### Authoring Model

The user is constructing:

- nodes
- trees
- subtrees
- reusable helper flows
- reusable BT pieces

The user is not necessarily constructing complete bots.

The user may later export:

- subtree-only code
- or a full bot wrapper

### Reuse Model

The BT system is considered pluggable.

As long as something is a valid BT piece:

- node
- tree
- subtree builder

it can become reusable.

### User Code Model

User code must follow the same general shape as the built-in BT helper ecosystem:

- callable function
- returns `BehaviorTree`

This was chosen specifically to make discovery, signatures, and reuse tractable.

### External Code Boundary

One of the most important clarifications in the session was about user-provided code.

The user explained that:

- BT nodes already require a strict structure
- externally provided user code may contain internal helper logic that is hard or impossible to interpret safely
- the system must not try to semantically translate or reinterpret arbitrary user code

Therefore the session locked a two-tier model:

1. `system-managed`
   - fully generated/owned by the tool
   - expected to be reconstructable/editable
2. `external/user-callable`
   - callable and reusable
   - treated as a closed box
   - not guaranteed to be structurally editable later

## Metadata Contract

Late in the session, the metadata/discovery boundary was clarified more strictly.

The final rule is:

- metadata is mandatory for discovery
- no metadata means ignore
- low-level internals do not need to be interpreted just because they are present in Python
- the parser should not fall back to semantic inference when the metadata contract is absent

This matters because the repo contains a mix of:

- public BT helper groups
- public BT routines
- support classes
- helper-of-helper methods
- nested local implementation functions

Trying to infer intent from all of those layers would create avoidable guesswork.

Instead, the design now treats the shared docstring contract as the authoritative opt-in signal for discovery.

### Contract Shape

The contract has two layers:

1. human-readable description
2. structured `Meta:` block

Required `Meta:` keys currently used by the session work:

- `Expose`
- `Audience`
- `Display`
- `Purpose`
- `UserDescription`
- `Notes`

The parser is expected to trust the `Meta:` block and ignore code that has not opted in through that contract.

## Discovery Browser Context

After the metadata contract was locked, the work branch moved from metadata preparation into early wizard-system implementation.

The first concrete implementation artifact is a metadata-gated discovery browser script at:

- [Bot_Factory.py](/c:/Users/Apo/Py4GW_python_files/Bot_Factory.py)

This script is not yet the configurator itself.

Its role is to prove and exercise the discovery layer the future wizard will sit on top of.

### What the discovery browser currently does

- scans `BehaviorTree.py` for built-in BT node classes
- scans `BehaviourTrees.py` and the BT helper package for BT routine groups and routines
- supports arbitrary extra files or folders as search targets
- already includes frenkeyLib BT helper discovery as a representative external catalog source
- uses AST scanning rather than importing helper modules at discovery time
- only catalogs code that opted in through the shared `Meta:` contract

### Why this matters

This established an important implementation boundary for the wizard project:

- discovery is metadata-gated
- discovery is structure-aware
- discovery is not runtime-import driven
- low-level code without metadata is ignored instead of being guessed at

That means the wizard catalog layer can remain deterministic and low-guesswork even as the helper library keeps growing.

## Code Generation Context

During the first browser implementation pass, it became clear that descriptive metadata alone is not enough for the wizard.

The future system is not only browsing helpers.

It is expected to later produce workable pieces of Python code from discovered catalog entries.

Because of that, each discovered entry needs to carry enough information to generate a valid call site, not just enough information to display a friendly description.

### Important distinction

The catalog does not need live callable objects at discovery time.

What it does need is a stable object-to-call reference.

Examples:

- `RoutinesBT.Map.TravelToOutpost`
- `BehaviorTree.ActionNode`
- `BTNodes.Merchant.SellItems`

This is the important code-generation-facing identity, because it is what later generated code must actually emit.

### Discovery data now expected by the wizard layer

In addition to docstring metadata and display/catalog data, discovery entries are now expected to carry code-generation descriptors such as:

- call owner
- call target
- call kind
- code template

Examples of intended values:

- call owner: `RoutinesBT.Map`
- call target: `RoutinesBT.Map.TravelToOutpost`
- call kind: `static_method`
- code template: `RoutinesBT.Map.TravelToOutpost(...)`

For built-in nodes:

- call owner: `BehaviorTree`
- call target: `BehaviorTree.ActionNode`
- call kind: `nested_class_constructor`
- code template: `BehaviorTree.ActionNode(...)`

This is a key design clarification:

- metadata is the discovery gate
- call-reference data is the code-generation bridge

The configurator will eventually need both.

## Practical Project State

At this point, the project is closer to code generation than it may appear at first glance.

The important foundation pieces are already in place:

- discoverable entries can be loaded reliably through metadata
- grouped catalog structure is available
- signatures are available
- stable call targets are available

That means the remaining path is largely mechanical:

1. choose a discoverable entry
2. read its metadata
3. read its signature
4. collect parameter values
5. render the final Python call
6. write the generated code to file

Examples of the intended emitted shape include:

- `RoutinesBT.Map.TravelToOutpost(...)`
- `RoutinesBT.Agents.MoveTargetInteractAndAutomaticDialog(...)`
- `BehaviorTree.ActionNode(...)`

This is why the current milestone matters:

- the system is no longer blocked on discovery ambiguity
- the system is no longer blocked on helper identity
- the system is now primarily moving toward parameter modeling and final code emission

## Current Status

At the end of this session, the metadata-preparation work reached the following state:

- `BehaviorTree.py` is prepared as the structural foundation for discovery
- `BehaviourTrees.py` is prepared as the root BT helper catalog surface
- extracted BT helper group files now share the same file-level contract guidance
- BT routine discovery is now intended to be metadata-gated instead of inference-driven
- public BT helper groups and routines have the metadata needed for upcoming parser work
- support/helper surfaces that matter to discovery now explicitly communicate whether they are exposed

The current implementation status for the next phase is now:

- metadata preparation is sufficiently complete for the intended discovery surface
- a first working discovery browser exists
- the browser can scan built-in BT nodes, BT routines, and arbitrary external BT helper sources
- the browser now carries code-generation-oriented call-reference data in addition to descriptive metadata
- signatures are already available from the parsed surfaces
- the remaining implementation gap is mainly parameter filling and final code rendering

This means the metadata-preparation step for the BT helper catalog is considered complete enough for the next system phase.

This was one of the most important design decisions in the session because it prevented impossible requirements from leaking into the tool.

## Foundation Work Required Before Building The Configurator

One of the most important follow-up clarifications after the session was that the configurator should not be the first place where metadata and structure are introduced.

The library itself must be prepared first.

The system is expected to live on top of an ever-growing helper library that changes continuously over time.

Because of that:

- a fixed manually maintained catalog is not viable
- the configurator must discover what exists at load time
- discovery must rely on consistent code structure, not fragile guesswork
- the codebase must be made easier to scan before the configurator is implemented

This means the first real implementation phase is not wizard UI.

It is library preparation.

### Core Foundation Principle

The scanner should not need to be smart.

The code should be disciplined enough that scanning it is straightforward and reliable.

That requires explicit preparation work in `BehaviourTrees.py` and any related helper modules that are expected to participate in discovery.

### What The Base Foundation Must Provide

#### 1. Clear public vs internal naming

The library must adopt strict naming rules so discovery can distinguish end-user helpers from implementation details.

Required conventions:

- public end-user helpers must use stable descriptive names
- internal helper-of-helper callables must use a consistent private prefix such as `_`
- internal closures inside helper bodies should also follow a clear `_name` style
- helper internals should be clearly separated from public entrypoints
- anything not intended for direct user selection must be obviously internal by name

#### 2. Stable grouping and class organization

The helper library must remain organized around the existing `BT` groups:

- `Player`
- `Map`
- `Items`
- `Agents`
- `Skills`

Preparation goals:

- keep helpers grouped by purpose
- avoid dumping unrelated functionality into broad miscellaneous buckets
- keep related public and internal helpers near each other so the file remains maintainable
- preserve these groups as the primary discovery surface for the future configurator

#### 3. Consistent signatures

Discovery and form-building become much easier if public helpers follow stable signature conventions.

Required conventions:

- public helpers must have complete type annotations
- parameter names must be descriptive and stable
- similar helpers should use the same parameter names for the same concepts
- defaults should use normal Python literals where practical
- public helper signatures should avoid unnecessary drift between equivalent operations

Examples of parameter concepts that should remain consistently named include:

- `x`
- `y`
- `log`
- `target_distance`
- `button_number`
- `map_id`

#### 4. Consistent callable shape

The future scanner must be able to trust what a public helper is.

Required conventions:

- public BT helpers should consistently return `BehaviorTree`
- helper intent should be visible from the callable shape
- mixed or ambiguous public return patterns should be minimized or normalized where possible

This is especially important because the configurator is expected to stitch together working helper calls rather than reinterpret arbitrary internal logic.

#### 5. Structured docstrings for scanable descriptions

The code needs descriptive text that is useful both for humans and for future tooling.

The goal is not heavy metadata yet.

The goal is to make the current code self-describing enough that a scanner can extract basic authoring information without guesswork.

Public helpers should therefore gain lightweight structured docstrings that clearly communicate:

- what the helper does
- which category/group it belongs to
- whether it is intended for end-user authoring
- what the important parameters mean
- any important usage caveats

These docstrings should be short, regular, and easy to parse.

They should not become large prose blocks.

#### 6. Standardized exposure rules

The library must define what qualifies as a discoverable user-facing helper.

At minimum, the foundation should make these rules reliable:

- public helpers do not start with `_`
- internal helpers do start with `_`
- public helpers are grouped under the expected `BT` namespaces
- public helpers include annotations and descriptive docstrings
- internal implementation details remain hidden from the authoring surface

### Why This Preparation Work Comes First

Without this preparation phase, any configurator built on top of the current helper library would be forced to rely on brittle heuristics, hand-maintained lists, or repeated maintenance whenever the library evolves.

That would be unsustainable.

The intended long-term model is:

1. prepare the helper library so it is consistent and scan-friendly
2. build discovery against those conventions
3. build the wizard and editor on top of that discovery layer

### Practical Preparation Scope

Before starting configurator implementation, the codebase should be audited and shaped so that:

- public helper names are consistent
- internal helper names are consistently private
- user-facing helpers have structured descriptive docstrings
- signatures are normalized across similar helpers
- group organization is stable and easy to inspect
- the discovery surface in `BehaviourTrees.py` is intentionally maintained

This preparation work is a core part of the configurator project, not optional cleanup.

It defines the base foundation the entire future system depends on.

### Base Tree Metadata Preparation

After the follow-up clarification, the project focus shifted even earlier than helper discovery.

Before preparing helper metadata in `BehaviourTrees.py`, the base `BehaviorTree` runtime itself needs to be scanned and normalized as a metadata source.

This matters because all future authoring and scanning logic will sit on top of the structural node system defined there.

#### What the base tree already provides

The current `BehaviorTree.Node` base class already exposes useful runtime metadata such as:

- unique node id
- display name
- node type string
- icon
- color
- blackboard reference
- last returned state
- tick count
- timing and accumulated runtime metrics

This is a strong starting point for runtime inspection and UI rendering.

#### What is still missing for authoring-oriented metadata

The current base tree metadata is mostly execution-oriented.

For configurator preparation, the base tree also needs a predictable authoring-oriented description of each node type.

The future system needs to know, in a normalized and reliable way:

- whether a node is a leaf, decorator, composite, repeater, router, or lazy subtree wrapper
- whether a node accepts zero, one, or many children
- which constructor inputs are authoring inputs versus runtime internals
- whether a node is intended to be directly authored by users or only used indirectly
- what the stable human-facing node label should be
- what structural role the node plays in a tree

#### Structural categories identified in the current runtime

Scanning `BehaviorTree.py` shows that the runtime already contains clear structural families that should later become normalized metadata categories:

- leaf nodes
  - `ActionNode`
  - `ConditionNode`
  - `WaitNode`
  - `WaitUntilNode`
  - `WaitUntilSuccessNode`
  - `WaitUntilFailureNode`
  - `WaitForTimeNode`
  - `SucceederNode`
  - `FailerNode`

- composite nodes with many children
  - `SequenceNode`
  - `SelectorNode`
  - `ChoiceNode`
  - `ParallelNode`

- routing or dynamic-selection nodes
  - `SwitchNode`
  - `SubtreeNode`

- single-child decorator or wrapper nodes
  - `InverterNode`
  - `RepeaterNode`
  - `RepeaterUntilSuccessNode`
  - `RepeaterUntilFailureNode`
  - `RepeaterForeverNode`

This classification should become part of the preparation work so future tooling does not need to rediscover it heuristically.

#### Base tree preparation goals

The preparation work for the base tree should make these things explicit and stable:

- node category
- child arity expectations
- whether children are static or lazily constructed
- which constructor arguments are structural authoring inputs
- which fields are runtime state only and should never be treated as authoring data
- stable naming conventions for node classes and node types

#### Runtime data versus authoring data

One important distinction became clear during scanning:

The base tree currently mixes metadata that is useful for runtime execution with metadata that is useful for future authoring surfaces.

Those are not the same thing.

Examples of runtime-only state:

- `last_state`
- `tick_count`
- `last_tick_time_ms`
- `total_time_ms`
- `avg_time_ms`
- `run_start_time`
- `run_last_duration_ms`
- `run_accumulated_ms`
- internal counters such as `current`, `current_count`, `start_time`, `last_check_time`

These fields are useful for debugging and live UI, but they should not be treated as reconstructable authoring metadata.

Examples of authoring-relevant structural data:

- node class
- node type
- node display name
- child list or child slot shape
- selector callback requirement
- subtree factory requirement
- repeat count
- timeout values
- throttle interval values

The preparation work should make this separation very clear.

#### Base tree conventions should come before wizard integration

The future configurator should not infer node structure by reverse-engineering implementation details.

Instead, the `BehaviorTree` runtime should be shaped so that each node type has a clear and stable structural identity that scanning code can rely on.

That means the preparation phase should include:

- documenting the structural role of each built-in node type
- standardizing node naming and node type labels
- deciding which node types are part of the direct authoring surface
- distinguishing constructor arguments from runtime bookkeeping fields
- making child shape expectations explicit

#### Immediate implication for the project

The project is no longer only about helper discovery.

It has shifted into a foundational metadata-preparation effort in two layers:

1. base tree structural metadata in `BehaviorTree.py`
2. helper discovery metadata and naming discipline in `BehaviourTrees.py`

The base tree layer must be understood and prepared first, because every higher-level authoring surface depends on it.

## Decisions Reached During The Session

The following decisions were explicitly made during the session.

### High-level direction

- The system is a configuration layer over the existing BT stack.
- The primary authored unit is one big tree at a time.
- Users build that tree by stitching together BT nodes, BT helpers, and user-provided BT pieces.

### No visual node system required

- A visual node editor is no longer required.
- The system is considered robust enough with:
  - wizard for add/edit
  - hierarchical tree/list editor for structure

### Wizard responsibility

- The wizard is only responsible for adding and editing items.
- Editing means reopening the wizard with stored values prefilled.

### Main manipulation surface

- The main editing surface is a hierarchical list/tree view.
- Users must be able to:
  - append
  - move
  - delete
  - edit
  - add child
  - add here
- append is the default/simple workflow
- insert-between is advanced

### Hierarchy is required

- The editor cannot be a flat list only.
- If a BT node requires children, the editor must represent nested structure through tree view or indentation.

### Built-in helper discovery

- Only `Py4GWCoreLib/routines_src/BehaviourTrees.py` should be scanned for built-in helpers.
- Public end-user helpers are exposed.
- Internal helper-of-helper functions starting with `_` are not exposed.

### Grouping

The catalog should follow the `BehaviourTrees.py` grouping model:

- `Player`
- `Map`
- `Items`
- `Agents`
- `Skills`

### Structural BT node exposure

- The system must also expose BT structural nodes/classes directly, because users need to choose, configure, and manipulate any kind of node required to construct trees.

### User folder

- The user will have a folder where generated and user-provided files are stored.
- This should not be over-formalized as a project system.
- The system may organize files inside that folder however is easiest to manage.

### File creation behavior

- The user should be able to decide whether changes append to an existing file or create a new one.

### Unified catalog

- Built-ins and user-generated entries should appear in one unified catalog, clearly labeled by origin.

### Reconstructability goal

- The system should aim to require only `.py` code to run and infer all its data, at least for system-managed code.
- Python-only round-trip is a goal for system-managed generated code.
- External callable code may remain opaque and non-reconstructable.

### Export shape

- Any export mode should generate a single self-contained file.
- The user should be able to generate either:
  - subtree-only file
  - full bot file

## Final Implementation Plan

### Summary

Build a wizard-first authoring system that configures and saves BehaviorTree-based code without requiring a visual node editor. The system helps non-coders construct one large authored tree by stitching together BT structural nodes, public `BehaviourTrees.py` helpers, and reusable user-provided BT pieces.

The primary workflow is:

- use a wizard to add or edit a BT piece
- view and manipulate the current structure in a hierarchical list/tree
- save code into a user-chosen folder
- optionally export as either a subtree file or a full single-file bot wrapper

The system must align to the existing stack, not replace it.

### Core design

#### Authored unit

The authored unit is one big tree.

Users build it from:

- BT structural nodes exposed by the configurator
- discovered public end-user helpers from `BehaviourTrees.py`
- reusable user-generated BT code stored in a user folder

#### Built-in catalog

The built-in catalog is discovered, not hardcoded.

Discovery rules:

- scan the prepared BT discovery surfaces, starting from:
  - `Py4GWCoreLib/py4gwcorelib_src/BehaviorTree.py`
  - `Py4GWCoreLib/routines_src/BehaviourTrees.py`
  - approved BT helper package sources
  - approved external BT helper sources
- include only entries that opted in through the shared `Meta:` contract
- ignore code without metadata instead of inferring from naming alone
- preserve grouped helper organization such as:
  - `Player`
  - `Map`
  - `Items`
  - `Agents`
  - `Skills`

In addition to discovered helpers, expose BT structural nodes directly from the configurator so users can build nested structures with children.

#### User code catalog

The user picks a folder where authored code is stored.

That folder is just storage, not a formal project system.

User-generated reusable entries live there and are discovered by scanning that folder.

Contract for user-provided code:

- it must follow the same shape as BT helpers
- it must be a function that returns a `BehaviorTree`

#### Reusable entry types

The system distinguishes between:

- `system-managed`
  - generated or owned by the configurator
  - expected to be reconstructable/editable by the system

- `external/user-callable`
  - reusable by signature and callable shape
  - treated as a closed box
  - not guaranteed to be structurally readable/editable later

#### Wizard and editor behavior

The wizard is only responsible for add/edit.

Add/edit behavior:

- user chooses a BT piece from one unified catalog
- built-ins and user-generated entries are both visible
- entries are clearly labeled by origin
- wizard forms are built from discovered call signatures
- edit means reopening the wizard with stored values prefilled

Main editing surface:

- hierarchical list/tree view, not visual nodes
- supports nesting/indentation because BT nodes can contain children
- supports:
  - append
  - move/reorder
  - delete
  - edit
  - add child
  - add here
- append is the default flow
- insert-between is advanced

#### Save and export

The system saves Python code.

Target behavior:

- aim for Python-only round-trip for system-managed code
- reconstruction should infer structure from generated `.py`
- external/user-callable code may remain opaque

Export options:

- subtree file
- full bot file

Both export modes must generate a single self-contained `.py` file.

### Implementation changes

Create a dedicated configurator layer that owns:

- built-in helper discovery from `BehaviourTrees.py`
- built-in node discovery from `BehaviorTree.py`
- user-folder discovery for BT-shaped callables
- catalog assembly and grouping
- signature extraction for wizard forms
- code-generation call-reference extraction
- parameter modeling from discovered signatures
- hierarchical authored tree model
- add/edit/remove/move/add-child/add-here operations
- code generation for system-managed entries
- code loading/reconstruction for system-managed files
- export to single-file subtree or single-file full bot

The configurator should preserve:

- whether an entry is built-in, system-managed, or external/user-callable
- whether an item is a container or leaf
- child ordering and hierarchy
- the exact chosen helper call for built-ins
- the exact call target used for generated code, such as `RoutinesBT.Map.TravelToOutpost`
- the filled parameter values used to render that final generated call

The configurator must not reinterpret external callable code beyond registration and invocation shape.

### Tests and scenarios

#### Discovery and catalog

- scanner finds only public end-user helpers from `BehaviourTrees.py`
- `_`-prefixed internal helpers are excluded
- user-folder scanning finds valid BT-returning functions
- built-in and user entries appear in one unified grouped catalog with origin labels

#### Wizard behavior

- add wizard creates configured items from discovered signatures
- edit wizard reopens with stored values prefilled
- built-in helper parameters round-trip correctly
- external callable entries can be selected and configured as callable closed boxes

#### Tree editor behavior

- append adds items in correct order
- add child nests under container nodes correctly
- add here inserts at selected structural position
- reorder preserves valid hierarchy
- delete removes nested content safely
- hierarchical list view renders nested BT structures clearly

#### Save/load/reconstruction

- system-managed saved Python can be reopened and reconstructed into the same hierarchy
- helper calls reconstruct as the same helper calls originally chosen
- system-managed helper calls reopen structurally
- external/user-callable entries remain reusable even if structural reopening is unavailable

#### Export

- subtree export produces one self-contained `.py` file
- full bot export produces one self-contained `.py` file
- exported system-managed code preserves valid BT structure
- exported code can be consumed by existing BT/BottingTree flows

## Session Pitfalls And Corrections

This section exists so a future replication of the session does not fall into the same traps.

### Pitfall 1: abstracting too early

The session initially drifted into over-abstract planning language such as broad schema talk, generalized “project” structure, and reduced V1 scope choices before enough repo grounding had been applied.

The user explicitly pushed back on this.

Correction:

- use repo examples first
- use `Absolute Pre-Searing.py` as the concrete behavior model
- avoid collapsing the problem before the real flow is understood

### Pitfall 2: treating the tool like a generic node editor

The existence of `dNodes.py` made it tempting to center the design on a visual graph system.

Correction:

- the audience is non-technical
- wizard plus list/tree is enough
- visual nodes are optional and not required

### Pitfall 3: over-formalizing “project”

At one point the conversation started treating the system like a mini IDE project model.

The user explicitly corrected this and clarified that “project” in practice just meant:

- a folder where files are stored

Correction:

- do not formalize the folder into a heavyweight project concept unless truly necessary

### Pitfall 4: assuming all code must be fully reconstructable

There was a risk of forcing the tool to parse and reconstruct any external user code.

The user clarified that this is not realistic because user-provided callables may contain internal helpers and patterns the tool cannot safely interpret.

Correction:

- treat external user code as a closed box
- only require full structural round-trip for system-managed code

## Guidance For A Future Session

If this work is picked up again, the next productive steps should be:

1. Define the configurator’s internal object model for:
   - structural BT nodes
   - discovered helper calls
   - system-managed reusable entries
   - external callable entries
   - hierarchical child relationships

2. Define the discovery/introspection strategy for:
   - public helper extraction from `BehaviourTrees.py`
   - user-folder callable extraction
   - parameter extraction and value modeling from discovered signatures

3. Define the hierarchical editor operations precisely:
   - append
   - add child
   - add here
   - move within level
   - move across hierarchy
   - delete
   - reopen wizard for edit

4. Define codegen and reconstruction rules for:
   - system-managed code
   - opaque external callable entries
   - single-file subtree export
   - single-file full bot export

5. Only after those are stable, begin implementing the actual configurator class and UI flow.

## Final Notes

This session ended with a much clearer and more practical design than it started with.

The main shift was:

- away from a visual node editor
- away from an abstract schema-heavy “project system”
- toward a wizard-first configurator that generates valid BT code and uses a tree/list as the main manipulation surface

That direction fits:

- the actual repo architecture
- the helper composition style already used in `BehaviourTrees.py`
- the planner/subtree patterns already used in `Absolute Pre-Searing.py`
- the skill level of the target users

This document should be treated as the authoritative design handoff from this session.
