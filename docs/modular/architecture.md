# Modular JSON BottingTree Architecture

Modular JSON now compiles into `BehaviorTree` planner steps that are installed directly into `BottingTree`.
The runtime path is intentionally short:

```text
Sources/modular_data JSON
  -> Py4GWCoreLib.modular.compile_recipe_steps_to_named_planner_steps
  -> Py4GWCoreLib.BottingTree.SetCurrentNamedPlannerSteps
  -> Py4GWCoreLib.routines_src.BehaviourTrees.BT
```

`BottingTree` is the runtime owner for planner ticking, blackboard state, HeroAI integration,
movement pause flags, services, party setup configuration, and recovery. Modular code must not tick
compiled recipe trees directly.

There is no `ModularBot`, `Phase`, `BTRecipeRunner`, action registry, `@modular_step`, or `modular_core`
execution path.

`BehaviorTree` is the only owner of BT node, coercion, and composition semantics. `BT.Composite`
remains as a non-modular compatibility surface, but its implementation delegates sequence construction
to `BehaviorTree`.

## Public Surface

Supported callers should import from `Py4GWCoreLib.modular`:

- `compile_recipe_steps_to_named_planner_steps`
- `load_recipe`
- `audit_recipe_vocabulary`
- `recipe_step_metadata`
- vocabulary/type metadata and compiler error/data types needed by the adapter

Raw compile-to-`BehaviorTree` helpers are compiler internals only. Runtime code must install planner
steps into `BottingTree`; it must not import or tick full-recipe compiled trees.

The only supported JSON step types are:

- `route`
- `interact`
- `map`
- `party`
- `behavior`
- `inventory`
- `wait`

## Package Shape

```text
Py4GWCoreLib/modular/
  json_bt_compiler.py       JSON validation and BT construction
  selectors.py              Selector helper used by BT adapters and MerchantRules
  paths.py                  Project/data/settings path helpers
  domain/target_registry.py Named NPC/enemy/gadget definitions
```

Hero team priority/configuration is owned by `Py4GWCoreLib.botting_tree_src.hero_setup*`.

Obsolete orchestration and registry packages were removed:

- `Py4GWCoreLib/modular/actions`
- `Py4GWCoreLib/modular/compiler`
- `Py4GWCoreLib/modular/recipes`
- `Py4GWCoreLib/modular/runner.py`
- `Py4GWCoreLib/modular/runtime_native`
- `Py4GWCoreLib/modular/widget_runtime.py`
- `Py4GWCoreLib/modular/hero_setup*.py`
- `Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core`

## JSON Data

Reusable content lives in `Sources/modular_data`. Recipes use the 7 smart node types only. Historical names such as `quest`, `move`, `dialog`, `auto_path`, `wait_map_load`, and `set_auto_behavior` are migration-only vocabulary and are rejected by the compiler.

## Validation

Use focused checks:

```powershell
python -m py_compile <changed python files>
python Sources/modular_data/tools/audit_json_bt_vocabulary.py --fail-on-issues
python Sources/modular_data/tools/test_json_bt_compiler_contract.py
python Sources/modular_data/tools/test_json_bt_compile_shape.py
python Sources/modular_data/tools/test_modular_botting_tree_adapter.py
python Sources/modular_data/tools/validate_modular_architecture.py
```

`Sources/modular_data/tools/compile_json_bt_recipes.py` imports Py4GW runtime bindings and is only expected to pass inside a runtime environment where those bindings are available.
