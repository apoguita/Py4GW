"""
Validate modular architecture guardrails for changed modular-core files.

Checks:
- File size threshold (>800 lines)
- Top-level function size threshold (>50 lines)
- Every Sources/modular_data JSON step `type` has a registered @modular_step handler
- Every @modular_step allowed_params contract includes handler ctx.step keys

Python size checks apply to changed Python files in:
- Py4GWCoreLib/modular/
- Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
FILE_LINE_LIMIT = 800
FUNCTION_LINE_LIMIT = 50
TARGET_PREFIXES = (
    "Py4GWCoreLib/modular/",
    "Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/",
)
MODULAR_CORE_DIR = REPO_ROOT / "Py4GWCoreLib" / "routines_src" / "behaviourtrees_src" / "modular_core"
MODULAR_DATA_DIR = REPO_ROOT / "Sources" / "modular_data"
COMMON_STEP_KEYS: frozenset[str] = frozenset(
    {
        "type",
        "name",
        "repeat",
        "ms",
        "anchor",
        "debug",
        "debug_log",
        "debug_logging",
    }
)
SELECTOR_STEP_KEYS: frozenset[str] = frozenset(
    {
        "point",
        "x",
        "y",
        "npc",
        "enemy",
        "gadget",
        "target",
        "name_contains",
        "enemy_name",
        "agent_name",
        "model_id",
        "nearest",
        "max_dist",
        "exact_name",
        "agent_id",
        "id",
        "item",
    }
)

# Explicit temporary exceptions for complex workflows.
FILE_EXCEPTIONS: dict[str, str] = {
}

FUNCTION_EXCEPTIONS: dict[tuple[str, str], str] = {
    ("Py4GWCoreLib/modular/hero_setup_ui.py", "draw_priority_tab"): "UI-heavy rendering function kept together for immediate-mode UI readability.",
    ("Py4GWCoreLib/modular/hero_setup_ui.py", "draw_team_configuration_window"): "UI-heavy rendering function kept together for immediate-mode UI readability.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_interaction.py", "handle_dialog_multibox"): "Multibox transaction orchestration; refactor deferred.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_interaction.py", "handle_loot_chest"): "Gameplay-state guard complexity; refactor deferred.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_interaction.py", "handle_interact_item"): "Selector + FSM orchestration; refactor deferred.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory.py", "_wait_for_outbound_messages"): "Shared-memory completion contract helper.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory.py", "_yield_toggle_widgets"): "Cross-account widget sync sequence.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory.py", "_yield_shared_leave_party"): "Shared leave-party sequence.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory.py", "_yield_travel_gh"): "Guild hall travel orchestration.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory.py", "_yield_inventory_setup"): "Composite setup workflow; scheduled for phased extraction.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory_handlers.py", "handle_restock_kits"): "Merchant interaction + multibox synchronization.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory_handlers.py", "handle_restock_cons"): "Restock schedule orchestration.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory_handlers.py", "handle_inventory_cleanup"): "Cleanup workflow orchestration.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory_merchanting.py", "handle_sell_materials"): "Trader selector + multibox dispatch orchestration.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory_merchanting.py", "handle_deposit_materials"): "Storage + multibox sync orchestration.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory_merchanting.py", "handle_sell_nonsalvageable_golds"): "Merchant flow with rule filters.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory_merchanting.py", "handle_sell_leftover_materials"): "Merchant flow with inventory filters.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory_merchanting.py", "handle_sell_scrolls"): "Merchant flow with dynamic target maps.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory_merchanting.py", "handle_buy_ectoplasm"): "Rare-material purchase flow orchestration.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_inventory_merchanting.py", "handle_merchant_rules_execute"): "MerchantRules integration orchestration.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_movement.py", "handle_random_travel"): "Travel retry/state workflow.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_movement.py", "handle_travel_gh"): "Guild hall navigation flow.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_movement_pathing.py", "handle_auto_path"): "Waypoint retry/recovery workflow.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_movement_pathing.py", "handle_auto_path_until_enemy"): "Patrol selector workflow.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_movement_pathing.py", "handle_auto_path_till_timeout"): "Timeout-governed path loop.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_party.py", "handle_broadcast_summoning_stone"): "Effect-aware multibox broadcast orchestration.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/actions_party_load.py", "handle_load_party"): "Primary party assembly workflow; extraction staged.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/compose.py", "build_action_step_tree"): "Core runtime composition function.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/step_selectors.py", "resolve_agent_xy_from_step"): "Selector normalization + diagnostics workflow.",
    ("Py4GWCoreLib/routines_src/behaviourtrees_src/modular_core/step_selectors.py", "resolve_enemy_agent_id_from_step"): "Selector normalization + diagnostics workflow.",
}


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _git_paths(args: list[str]) -> list[str]:
    try:
        output = subprocess.check_output(["git", *args], cwd=REPO_ROOT).decode("utf-8", errors="replace")
    except Exception:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def _target_files() -> list[Path]:
    staged = _git_paths(["diff", "--staged", "--name-only"])
    if not staged:
        staged = _git_paths(["diff", "--name-only"])
    untracked = _git_paths(["ls-files", "--others", "--exclude-standard"])
    candidates = [*staged, *untracked]
    result: list[Path] = []
    for rel in candidates:
        if not rel.endswith(".py"):
            continue
        if not rel.startswith(TARGET_PREFIXES):
            continue
        path = REPO_ROOT / rel
        if path.exists():
            result.append(path)
    return sorted(set(result))


def _check_file_limits(paths: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in paths:
        rel = _relative(path)
        line_count = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        if line_count <= FILE_LINE_LIMIT:
            continue
        if rel in FILE_EXCEPTIONS:
            continue
        failures.append(
            f"[FILE] {rel} has {line_count} lines (limit {FILE_LINE_LIMIT})."
        )
    return failures


def _check_function_limits(paths: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in paths:
        rel = _relative(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            failures.append(f"[PARSE] {rel}: {exc}")
            continue
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            size = int(getattr(node, "end_lineno", node.lineno) - node.lineno + 1)
            if size <= FUNCTION_LINE_LIMIT:
                continue
            if (rel, node.name) in FUNCTION_EXCEPTIONS:
                continue
            failures.append(
                f"[FUNC] {rel}:{node.lineno} {node.name} has {size} lines (limit {FUNCTION_LINE_LIMIT})."
            )
    return failures


def _collect_registered_step_types() -> set[str]:
    step_types: set[str] = set()
    for path in MODULAR_CORE_DIR.glob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            else:
                call_name = ""
            if call_name != "modular_step":
                continue
            for kw in node.keywords:
                if kw.arg == "step_type" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    step_types.add(str(kw.value.value).strip())
    return {step_type for step_type in step_types if step_type}


def _collect_json_step_types() -> tuple[dict[str, set[str]], list[str]]:
    used: dict[str, set[str]] = {}
    failures: list[str] = []

    def walk(value, path: Path) -> None:
        if isinstance(value, dict):
            step_type = value.get("type")
            if isinstance(step_type, str) and step_type.strip():
                used.setdefault(step_type.strip(), set()).add(_relative(path))
            for child in value.values():
                walk(child, path)
        elif isinstance(value, list):
            for child in value:
                walk(child, path)

    for path in MODULAR_DATA_DIR.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            failures.append(f"[JSON] {_relative(path)} failed to parse: {exc}")
            continue
        walk(data, path)
    return used, failures


def _check_json_step_coverage() -> list[str]:
    used, failures = _collect_json_step_types()
    registered = _collect_registered_step_types()
    for step_type in sorted(set(used) - registered):
        examples = ", ".join(sorted(used[step_type])[:3])
        failures.append(f"[JSON_STEP] step type {step_type!r} has no registered @modular_step handler; examples: {examples}")
    return failures


def _literal_string_set(node: ast.AST | None) -> set[str]:
    if node is None:
        return set()
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        values: set[str] = set()
        for element in node.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                value = element.value.strip()
                if value:
                    values.add(value)
        return values
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        value = node.value.strip()
        return {value} if value else set()
    return set()


def _is_ctx_step_attribute(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "step"
        and isinstance(node.value, ast.Name)
        and node.value.id == "ctx"
    )


def _collect_ctx_step_keys(function_node: ast.FunctionDef) -> set[str]:
    keys: set[str] = set()
    for node in ast.walk(function_node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "get" and _is_ctx_step_attribute(node.func.value):
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    value = node.args[0].value.strip()
                    if value:
                        keys.add(value)
        elif isinstance(node, ast.Subscript) and _is_ctx_step_attribute(node.value):
            subscript_key = node.slice
            if isinstance(subscript_key, ast.Constant) and isinstance(subscript_key.value, str):
                value = subscript_key.value.strip()
                if value:
                    keys.add(value)
    return keys


def _collect_modular_core_functions() -> dict[str, list[tuple[Path, ast.FunctionDef]]]:
    functions: dict[str, list[tuple[Path, ast.FunctionDef]]] = {}
    for path in MODULAR_CORE_DIR.glob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                functions.setdefault(node.name, []).append((path, node))
    return functions


def _iter_modular_step_registrations() -> list[tuple[Path, int, str, str, set[str]]]:
    registrations: list[tuple[Path, int, str, str, set[str]]] = []
    for path in MODULAR_CORE_DIR.glob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for stmt in tree.body:
            if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
                continue
            outer_call = stmt.value
            if not isinstance(outer_call.func, ast.Call):
                continue
            inner_call = outer_call.func
            if not isinstance(inner_call.func, ast.Name) or inner_call.func.id != "modular_step":
                continue
            if not outer_call.args or not isinstance(outer_call.args[0], ast.Name):
                continue

            step_type = ""
            allowed_params: set[str] = set()
            for keyword in inner_call.keywords:
                if (
                    keyword.arg == "step_type"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ):
                    step_type = keyword.value.value.strip()
                elif keyword.arg == "allowed_params":
                    allowed_params = _literal_string_set(keyword.value)

            handler_name = outer_call.args[0].id
            if step_type and handler_name:
                registrations.append((path, int(stmt.lineno), step_type, handler_name, allowed_params))
    return registrations


def _check_step_allowed_params_contract() -> list[str]:
    failures: list[str] = []
    functions = _collect_modular_core_functions()
    always_allowed = set(COMMON_STEP_KEYS) | set(SELECTOR_STEP_KEYS)

    for registration_path, line_no, step_type, handler_name, allowed_params in _iter_modular_step_registrations():
        handler_candidates = functions.get(handler_name, [])
        if not handler_candidates:
            failures.append(
                f"[STEP_PARAMS] {_relative(registration_path)}:{line_no} step type {step_type!r} "
                f"references unknown handler {handler_name!r}."
            )
            continue
        if len(handler_candidates) > 1:
            locations = ", ".join(f"{_relative(path)}:{node.lineno}" for path, node in handler_candidates[:3])
            failures.append(
                f"[STEP_PARAMS] {_relative(registration_path)}:{line_no} step type {step_type!r} "
                f"references ambiguous handler {handler_name!r}; candidates: {locations}"
            )
            continue

        handler_path, handler_node = handler_candidates[0]
        consumed_keys = _collect_ctx_step_keys(handler_node)
        missing = sorted(consumed_keys - allowed_params - always_allowed)
        if missing:
            failures.append(
                f"[STEP_PARAMS] {_relative(registration_path)}:{line_no} step type {step_type!r} "
                f"handler {handler_name} consumes unsupported key(s): {', '.join(missing)} "
                f"(handler: {_relative(handler_path)}:{handler_node.lineno})"
            )
    return failures


def main() -> int:
    targets = _target_files()
    if not targets:
        print("PASS: no modular Python files to validate.")
        return 0

    failures: list[str] = []
    failures.extend(_check_file_limits(targets))
    failures.extend(_check_function_limits(targets))
    failures.extend(_check_json_step_coverage())
    failures.extend(_check_step_allowed_params_contract())

    if failures:
        print("FAIL: modular architecture validation failed.")
        for line in failures:
            print(line)
        print("\nDocumented exceptions:")
        for rel, reason in sorted(FILE_EXCEPTIONS.items()):
            print(f"  FILE {rel}: {reason}")
        for (rel, fn), reason in sorted(FUNCTION_EXCEPTIONS.items()):
            print(f"  FUNC {rel}::{fn}: {reason}")
        return 1

    print(f"PASS: modular architecture validation passed for {len(targets)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
