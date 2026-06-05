"""Validate the BT-native modular compiler architecture."""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULAR_DIR = REPO_ROOT / "Py4GWCoreLib" / "modular"
MODULAR_CORE_DIR = REPO_ROOT / "Py4GWCoreLib" / "routines_src" / "behaviourtrees_src" / "modular_core"
MODULAR_DATA_DIR = REPO_ROOT / "Sources" / "modular_data"
MODULAR_WIDGET_DIR = REPO_ROOT / "Widgets" / "Automation" / "modular"
COMPILER_PATH = MODULAR_DIR / "json_bt_compiler.py"
BT_PATH = REPO_ROOT / "Py4GWCoreLib" / "py4gwcorelib_src" / "BehaviorTree.py"
BOTTING_PLANNER_PATH = REPO_ROOT / "Py4GWCoreLib" / "botting_tree_src" / "planner.py"
COMPOSITE_PATH = REPO_ROOT / "Py4GWCoreLib" / "routines_src" / "behaviourtrees_src" / "composite.py"
PREBUILT_DIR = MODULAR_DATA_DIR / "prebuilt"
BOTTING_HERO_SETUP_PATH = REPO_ROOT / "Py4GWCoreLib" / "botting_tree_src" / "hero_setup.py"
BOTTING_HERO_SETUP_MODEL_PATH = REPO_ROOT / "Py4GWCoreLib" / "botting_tree_src" / "hero_setup_model.py"
EXPECTED_CANONICAL = {"behavior", "interact", "inventory", "map", "party", "route", "wait"}
REMOVED_PUBLIC_NAMES = {"ModularBot", "Phase", "register_action_node", "BTRecipeRunner"}
RAW_COMPILE_EXPORTS = {
    "compile_file_to_bt",
    "compile_recipe_to_bt",
    "compile_recipe_step_to_bt",
    "compile_recipe_steps_to_bt",
    "compile_step_to_bt",
}


def main() -> int:
    failures: list[str] = []
    failures.extend(_check_compiler_contract())
    failures.extend(_check_removed_runner_contract())
    failures.extend(_check_composition_ownership())
    failures.extend(_check_removed_runtime_paths())
    failures.extend(_check_broken_widget_references())
    failures.extend(_check_modular_tools_runtime_paths())
    failures.extend(_check_json_types())
    failures.extend(_check_json_audit())

    if failures:
        print("FAIL: modular architecture validation failed.")
        for failure in failures:
            print(failure)
        return 1

    print("PASS: BT-native modular architecture validation passed.")
    return 0


def _check_compiler_contract() -> list[str]:
    failures: list[str] = []
    tree = ast.parse(COMPILER_PATH.read_text(encoding="utf-8"))
    constants = _module_constants(tree)
    canonical = set(constants.get("CANONICAL_STEP_TYPES", ()))
    legacy = set(constants.get("LEGACY_STEP_TYPES", ()))
    if canonical != EXPECTED_CANONICAL:
        failures.append(f"[COMPILER] canonical types are {sorted(canonical)}, expected {sorted(EXPECTED_CANONICAL)}.")
    overlap = canonical & legacy
    if overlap:
        failures.append(f"[COMPILER] canonical and legacy types overlap: {sorted(overlap)}.")
    text = COMPILER_PATH.read_text(encoding="utf-8")
    for banned in ("build_action_step_tree", "@modular_step", "StepNodeRequest"):
        if banned in text:
            failures.append(f"[COMPILER] compiler still references legacy symbol {banned!r}.")
    if "compile_recipe_steps_to_named_planner_steps" not in text:
        failures.append("[COMPILER] missing compile_recipe_steps_to_named_planner_steps adapter.")
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    raw_public_functions = sorted(RAW_COMPILE_EXPORTS & functions)
    if raw_public_functions:
        failures.append(f"[COMPILER] raw compile-to-BT functions must be internal-only: {raw_public_functions}.")
    if "Py4GWCoreLib.botting_tree_src.hero_setup_model" not in text:
        failures.append("[COMPILER] party-load hero setup must come from BottingTree ownership.")
    init_text = (MODULAR_DIR / "__init__.py").read_text(encoding="utf-8")
    for name in REMOVED_PUBLIC_NAMES:
        if name in init_text:
            failures.append(f"[PUBLIC_API] __init__.py still exports removed name {name!r}.")
    for name in RAW_COMPILE_EXPORTS:
        if name in init_text:
            failures.append(f"[PUBLIC_API] __init__.py must not export raw compile helper {name!r}.")
    return failures


def _check_removed_runner_contract() -> list[str]:
    failures: list[str] = []
    runner_path = MODULAR_DIR / "runner.py"
    if runner_path.exists():
        failures.append("[RUNNER] Py4GWCoreLib/modular/runner.py must be removed.")
    widget_runtime_path = MODULAR_DIR / "widget_runtime.py"
    if widget_runtime_path.exists():
        failures.append("[RUNTIME] Py4GWCoreLib/modular/widget_runtime.py must be removed.")
    for rel in ("hero_setup.py", "hero_setup_model.py", "hero_setup_ui.py"):
        path = MODULAR_DIR / rel
        if path.exists():
            failures.append(f"[OWNERSHIP] modular hero setup shim/file must be removed: {path.relative_to(REPO_ROOT)}")
    if not BOTTING_HERO_SETUP_PATH.exists() or not BOTTING_HERO_SETUP_MODEL_PATH.exists():
        failures.append("[OWNERSHIP] BottingTree hero setup model/facade must exist.")
    for root in (MODULAR_DIR, MODULAR_WIDGET_DIR, PREBUILT_DIR):
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for banned in ("BTRecipeRunner", "RuntimeStepView", "RecipePhaseView"):
                if banned in text:
                    failures.append(
                        f"[RUNNER] {path.relative_to(REPO_ROOT)} still references removed runner symbol {banned!r}."
                    )
            if "class CompiledRecipe:" in text:
                failures.append(
                    f"[RUNNER] {path.relative_to(REPO_ROOT)} still defines removed runner symbol 'CompiledRecipe'."
                )
            for banned in ("recipe.tree.tick", "_refresh_runtime_blackboard"):
                if banned in text:
                    failures.append(
                        f"[RUNNER] {path.relative_to(REPO_ROOT)} still contains raw-runtime symbol {banned!r}."
                    )
            for banned in (
                "Py4GWCoreLib.modular.widget_runtime",
                "Py4GWCoreLib.modular.hero_setup",
                "Py4GWCoreLib.modular.hero_setup_model",
                "Py4GWCoreLib.modular.hero_setup_ui",
            ):
                if banned in text:
                    failures.append(f"[OWNERSHIP] {path.relative_to(REPO_ROOT)} still imports {banned!r}.")
    return failures


def _check_composition_ownership() -> list[str]:
    failures: list[str] = []
    bt_text = BT_PATH.read_text(encoding="utf-8")
    for required in ("def as_tree", "def resolve_tree", "def build_sequence", "def build_named_sequence"):
        if required not in bt_text:
            failures.append(f"[BEHAVIOR_TREE] missing canonical helper {required}.")
    planner_text = BOTTING_PLANNER_PATH.read_text(encoding="utf-8")
    if "BehaviorTree.build_named_sequence" not in planner_text:
        failures.append("[BOTTING_TREE] planner must delegate named sequence construction to BehaviorTree.")
    if "_build_named_planner_tree" in planner_text or "_coerce_runtime_tree" in planner_text:
        failures.append("[BOTTING_TREE] planner still contains duplicate sequence/coercion helpers.")
    composite_text = COMPOSITE_PATH.read_text(encoding="utf-8")
    if "BehaviorTree.build_sequence" not in composite_text or "BehaviorTree.build_named_sequence" not in composite_text:
        failures.append("[BT_COMPOSITE] composite helpers must delegate sequence construction to BehaviorTree.")
    return failures


def _check_broken_widget_references() -> list[str]:
    failures: list[str] = []
    banned_refs = {
        "test_modular_blocks.main",
        "test_modular_blocks.get_bot",
        "set_debug_logging",
        "main_ui=",
        "settings_ui=",
        "help_ui=",
    }
    for path in MODULAR_WIDGET_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for banned in banned_refs:
            if banned in text:
                failures.append(f"[WIDGET] {path.relative_to(REPO_ROOT)} still references removed API {banned!r}.")
    return failures


def _check_removed_runtime_paths() -> list[str]:
    failures: list[str] = []
    if MODULAR_CORE_DIR.exists() and any(MODULAR_CORE_DIR.glob("*.py")):
        failures.append("[CLEANUP] modular_core Python files still exist.")
    for rel in ("actions", "compiler", "recipes", "runtime_native"):
        path = MODULAR_DIR / rel
        if path.exists() and any(path.rglob("*.py")):
            failures.append(f"[CLEANUP] obsolete modular package still has Python files: {path.relative_to(REPO_ROOT)}")
    return failures


def _check_modular_tools_runtime_paths() -> list[str]:
    failures: list[str] = []
    runtime_smoke = MODULAR_DATA_DIR / "tools" / "run_modular_action_smoke_tests.py"
    if runtime_smoke.exists():
        text = runtime_smoke.read_text(encoding="utf-8")
        for banned in (
            "compile_recipe_to_bt",
            "from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree",
            "tree.tick()",
        ):
            if banned in text:
                failures.append(f"[TOOLS] runtime smoke tool still bypasses BottingTree via {banned!r}.")
        if "BottingTree" not in text or "SetCurrentNamedPlannerSteps" not in text:
            failures.append("[TOOLS] runtime smoke tool must install generated recipes into BottingTree.")

    compile_tool = MODULAR_DATA_DIR / "tools" / "compile_json_bt_recipes.py"
    if compile_tool.exists():
        text = compile_tool.read_text(encoding="utf-8")
        if "compile_recipe_to_bt" in text:
            failures.append("[TOOLS] compile_json_bt_recipes.py must compile through the planner-step adapter.")
        if "compile_recipe_steps_to_named_planner_steps" not in text:
            failures.append("[TOOLS] compile_json_bt_recipes.py must use the planner-step adapter.")
    return failures


def _check_json_audit() -> list[str]:
    audit_path = MODULAR_DATA_DIR / "tools" / "audit_json_bt_vocabulary.py"
    spec = importlib.util.spec_from_file_location("_audit_json_bt_vocabulary", audit_path)
    if spec is None or spec.loader is None:
        return [f"[AUDIT] Could not load {audit_path.relative_to(REPO_ROOT)}."]
    module = importlib.util.module_from_spec(spec)
    sys.modules[str(spec.name)] = module
    spec.loader.exec_module(module)
    result = module.audit_root(MODULAR_DATA_DIR)
    if not result.has_issues:
        return []
    return ["[AUDIT] JSON vocabulary audit has issues:", *module.format_result(result).splitlines()]


def _check_json_types() -> list[str]:
    failures: list[str] = []
    for path in MODULAR_DATA_DIR.rglob("*.json"):
        try:
            recipe = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            failures.append(f"[JSON] {path.relative_to(REPO_ROOT)} failed to parse: {exc}")
            continue
        if not isinstance(recipe, dict):
            failures.append(f"[JSON] {path.relative_to(REPO_ROOT)} must be an object.")
            continue
        steps = recipe.get("steps", [])
        if not isinstance(steps, list):
            failures.append(f"[JSON] {path.relative_to(REPO_ROOT)} steps must be a list.")
            continue
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                failures.append(f"[JSON] {path.relative_to(REPO_ROOT)} step {index + 1} must be an object.")
                continue
            step_type = str(step.get("type", "") or "").strip().lower()
            if step_type not in EXPECTED_CANONICAL:
                failures.append(
                    f"[JSON] {path.relative_to(REPO_ROOT)} step {index + 1} uses non-smart type {step_type!r}."
                )
    return failures


def _module_constants(tree: ast.Module) -> dict[str, object]:
    constants: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            if name in {"CANONICAL_STEP_TYPES", "LEGACY_STEP_TYPES"}:
                constants[name] = ast.literal_eval(node.value)
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in {"CANONICAL_STEP_TYPES", "LEGACY_STEP_TYPES"}:
                constants[name] = ast.literal_eval(node.value)
    return constants


if __name__ == "__main__":
    raise SystemExit(main())
