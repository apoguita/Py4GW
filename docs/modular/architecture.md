# Modular JSON BT Architecture

Modular JSON now compiles directly into `BehaviorTree` trees. The runtime path is intentionally short:

```text
Sources/modular_data JSON
  -> Py4GWCoreLib.modular.compile_recipe_steps_to_bt
  -> BTRecipeRunner facade
  -> Py4GWCoreLib.BottingTree planner/services
  -> Py4GWCoreLib.routines_src.BehaviourTrees.BT
```

`BottingTree` is the runtime owner for planner ticking, blackboard state, HeroAI integration,
movement pause flags, services, and recovery. The modular runner must not tick compiled recipe
trees directly.

There is no `ModularBot`, `Phase`, action registry, `@modular_step`, or `modular_core` execution path.

## Public Surface

Supported callers should import from `Py4GWCoreLib.modular`:

- `compile_recipe_to_bt`
- `compile_recipe_steps_to_bt`
- `compile_recipe_step_to_bt`
- `compile_step_to_bt`
- `compile_file_to_bt`
- `load_recipe`
- `audit_recipe_vocabulary`
- `BTRecipeRunner`

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
  runner.py                 BottingTree-backed wrapper for compiled recipe groups
  selectors.py              Selector helper used by BT adapters and MerchantRules
  paths.py                  Project/data/settings path helpers
  hero_setup*.py            Account-scoped hero team setup data/UI
  domain/target_registry.py Named NPC/enemy/gadget definitions
```

Obsolete orchestration and registry packages were removed:

- `Py4GWCoreLib/modular/actions`
- `Py4GWCoreLib/modular/compiler`
- `Py4GWCoreLib/modular/recipes`
- `Py4GWCoreLib/modular/runtime_native`
- `Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core`

## JSON Data

Reusable content lives in `Sources/modular_data`. Recipes use the 7 smart node types only. Historical names such as `quest`, `move`, `dialog`, `auto_path`, `wait_map_load`, and `set_auto_behavior` are migration-only vocabulary and are rejected by the compiler.

## Validation

Use focused checks:

```powershell
python -m py_compile <changed python files>
python Sources/modular_data/tools/audit_json_bt_vocabulary.py --fail-on-issues
python Sources/modular_data/tools/test_json_bt_compiler_contract.py
python Sources/modular_data/tools/validate_modular_architecture.py
```

`Sources/modular_data/tools/compile_json_bt_recipes.py` imports Py4GW runtime bindings and is only expected to pass inside a runtime environment where those bindings are available.
