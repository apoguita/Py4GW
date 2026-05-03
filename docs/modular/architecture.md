# ModularBot Architecture

ModularBot runs reusable JSON blocks through native `BottingTree` execution. The important idea is one direct path:

```text
Sources/modular_data JSON
  -> Phase.runtime_spec
  -> ModularBot
  -> NativeBlockPhaseRunner
  -> StepNodeRequest
  -> @modular_step registry
  -> BehaviorTree action node
  -> FSM/game API handler
```

## Public Surface

Supported callers should import from these modules:

- `Py4GWCoreLib.modular`: `ModularBot`, `Phase`, `register_action_node`, `get_target_registry`
- `Py4GWCoreLib.modular.recipes`: `Mission`, `Quest`, `Route`, `Farm`, `Dungeon`, `Vanquish`, `Bounty`, `ModularBlock`
- `Py4GWCoreLib.modular.actions`: `run_step`, `run_steps`, public selector/action helpers
- `Sources.modular_data.prebuilt`: campaign/FoW bot factories
- `Sources.modular_data.tools`: authoring and recorder tools

Widgets, prebuilts, and tools should not import `Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core` directly.

## Main Packages

```text
Py4GWCoreLib/modular/
  bot.py                    ModularBot orchestration and public object API
  phase.py                  Phase value object
  recipes/                  Phase factories and JSON block specs
  compiler/                 JSON loading and execution-plan construction
  runtime_native/           Native phase/step execution
  actions/                  Public action registry/runtime facade
  hero_setup.py             Account-scoped hero team setup and UI
  diagnostics.py            JSONL diagnostics/session logging

Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/
  step_registration.py      @modular_step decorator discovery
  step_type_specs.py        Canonical step metadata model
  node_registry.py          step.type -> BehaviorTree builder registry
  compose.py                Builds guarded/decorated step trees
  step_nodes.py             Function handler -> BT/FSM runtime adapter
  actions_*.py              Concrete step handlers
```

## Step Registration

Action handlers are plain functions decorated with `@modular_step(...)`.

The decorator records:

- `step_type`
- category
- allowed JSON parameters
- optional metadata/probes/builders

Bootstrap imports the decorated action modules and registers one canonical `StepTypeSpec` per `step.type`. The same registry is used by block execution and direct `run_step` helpers.

## Phase Execution

Recipe factories create `Phase` objects with `runtime_spec`. There are no fake runner callables or function-attribute phase specs.

At runtime:

1. `ModularBot` builds a native planner.
2. `NativeBlockPhaseRunner` loads the JSON block or inline plan.
3. Steps are expanded, sanitized, and executed in order.
4. Each step builds a BT node through the canonical registry.
5. Cross-cutting behavior is applied as decorators: diagnostics, recovery gate, auto-state guard, anchor, and post-delay.

## Data

Reusable bot content lives in `Sources/modular_data`:

- `missions/`
- `quests/`
- `routes/`
- `farms/`
- `dungeons/`
- `vanquishes/`
- `bounties/`
- `prebuilt/`
- `tools/`

Account-local runtime settings belong under `Settings/ModularBot`, not inside `Sources/modular_data`.

## Hero Teams

ModularBot needs account-scoped hero setup for `load_party`:

- static hero teams
- minionless variants
- priority list filling
- hero template loading

The runtime consumer is `actions_party_load.py`. The UI should stay convenient, but the core data model should remain small and explicit.

## Recovery And Diagnostics

Recovery is owned by `ModularBot` and support modules:

- configured restart targets: `on_party_wipe`, `on_death`
- runtime anchors: phase/state restart points
- suppression windows for steps that intentionally change map or party state
- diagnostics events written through `diagnostics.py`

Step failures and runtime exceptions should be recorded through diagnostics instead of silently disappearing.

## Validation

Before committing modular runtime changes, run:

```powershell
python -m py_compile <changed python files>
python Sources/modular_data/tools/validate_modular_architecture.py
```

Keep an architecture guard in the test suite that verifies modular JSON step types are registered and can build BT nodes, and that widgets/tools use public modular APIs.
