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
MODULAR_WIDGET_DIR = REPO_ROOT / "Widgets" / "Automation" / "modularbot"
COMPILER_PATH = MODULAR_DIR / "json_bt_compiler.py"
RUNNER_PATH = MODULAR_DIR / "runner.py"
EXPECTED_CANONICAL = {"behavior", "interact", "inventory", "map", "party", "route", "wait"}
REMOVED_PUBLIC_NAMES = {"ModularBot", "Phase", "register_action_node"}


def main() -> int:
    failures: list[str] = []
    failures.extend(_check_compiler_contract())
    failures.extend(_check_runner_contract())
    failures.extend(_check_removed_runtime_paths())
    failures.extend(_check_broken_widget_references())
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
    init_text = (MODULAR_DIR / "__init__.py").read_text(encoding="utf-8")
    for name in REMOVED_PUBLIC_NAMES:
        if name in init_text:
            failures.append(f"[PUBLIC_API] __init__.py still exports removed name {name!r}.")
    return failures


def _check_runner_contract() -> list[str]:
    failures: list[str] = []
    text = RUNNER_PATH.read_text(encoding="utf-8")
    if "from Py4GWCoreLib.BottingTree import BottingTree" not in text:
        failures.append("[RUNNER] BTRecipeRunner must import the BottingTree wrapper layer.")
    if "SetCurrentNamedPlannerSteps" not in text:
        failures.append("[RUNNER] BTRecipeRunner must install modular steps through BottingTree named planner steps.")
    for banned in ("recipe.tree.tick", "_refresh_runtime_blackboard"):
        if banned in text:
            failures.append(f"[RUNNER] BTRecipeRunner still contains raw-runtime symbol {banned!r}.")
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
