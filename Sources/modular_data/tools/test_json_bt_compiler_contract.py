"""Offline contract checks for the BT-native modular JSON compiler."""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
COMPILER_PATH = REPO_ROOT / "Py4GWCoreLib" / "modular" / "json_bt_compiler.py"
AUDIT_PATH = REPO_ROOT / "Sources" / "modular_data" / "tools" / "audit_json_bt_vocabulary.py"
EXPECTED_CANONICAL = {"behavior", "interact", "inventory", "map", "party", "route", "wait"}


def main() -> int:
    compiler_tree = ast.parse(COMPILER_PATH.read_text(encoding="utf-8"))
    compiler_constants = _module_constants(compiler_tree)
    canonical = set(compiler_constants["CANONICAL_STEP_TYPES"])
    legacy = set(compiler_constants["LEGACY_STEP_TYPES"])

    assert canonical == EXPECTED_CANONICAL
    assert {"move", "dialog", "quest", "automatic_dialog", "wait_for_map_load", "auto_path", "loot_chest"} <= legacy
    assert not (canonical & legacy)

    functions = {node.name for node in compiler_tree.body if isinstance(node, ast.FunctionDef)}
    assert {
        "compile_recipe_to_bt",
        "compile_recipe_steps_to_bt",
        "compile_recipe_step_to_bt",
        "compile_step_to_bt",
        "compile_file_to_bt",
        "load_recipe",
    } <= functions
    assert "build_action_step_tree" not in COMPILER_PATH.read_text(encoding="utf-8")

    audit = _load_audit_module()
    assert canonical == set(audit.CANONICAL_STEP_TYPES)
    assert legacy == set(audit.LEGACY_STEP_TYPES)
    assert audit.ALLOWED_VALUES[("behavior", "action")] == frozenset({"enemy_blacklist"})
    assert audit.ALLOWED_VALUES[("behavior", "mode")] == frozenset({"add", "remove"})

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "canonical.json").write_text(
            json.dumps(
                {
                    "name": "Canonical Fixture",
                    "required_hero": "Any",
                    "steps": [
                        {"type": "route", "mode": "move", "points": [[1, 2], [3, 4]], "repeat": 2},
                        {"type": "wait", "ms": 100},
                        {"type": "interact", "action": "dialog", "id": [1, 2]},
                        {"type": "map", "action": "wait_for_map_load", "target_map_id": 42},
                    ],
                }
            ),
            encoding="utf-8",
        )
        clean = audit.audit_root(root)
        assert clean.files == 1
        assert clean.steps == 4
        assert not clean.has_issues

        (root / "legacy.json").write_text(
            json.dumps({"name": "Legacy Fixture", "steps": [{"type": "move", "points": [[1, 2]]}]}),
            encoding="utf-8",
        )
        dirty = audit.audit_root(root)
        assert dirty.legacy_counts["move"] == 1
        assert dirty.has_issues

        (root / "unknown.json").write_text(
            json.dumps({"name": "Unknown Fixture", "steps": [{"type": "surprise"}]}),
            encoding="utf-8",
        )
        unknown = audit.audit_root(root)
        assert unknown.unknown_counts["surprise"] == 1
        assert unknown.has_issues

        (root / "bad_selector.json").write_text(
            json.dumps({"name": "Bad Selector", "steps": [{"type": "interact", "target": "npc", "npc": "NOPE"}]}),
            encoding="utf-8",
        )
        bad_selector = audit.audit_root(root)
        assert bad_selector.semantic_counts["npc.unknown_selector.NOPE"] == 1
        assert bad_selector.has_issues

        (root / "bad_party.json").write_text(
            json.dumps({"name": "Bad Party", "steps": [{"type": "party", "action": "load", "use_priority": True}]}),
            encoding="utf-8",
        )
        bad_party = audit.audit_root(root)
        assert bad_party.semantic_counts["party.unsupported_field.use_priority"] == 1
        assert bad_party.has_issues

        (root / "bad_behavior.json").write_text(
            json.dumps(
                {"name": "Bad Behavior", "steps": [{"type": "behavior", "action": "set_auto_behavior"}]}
            ),
            encoding="utf-8",
        )
        bad_behavior = audit.audit_root(root)
        assert bad_behavior.semantic_counts["behavior.unsupported_action.set_auto_behavior"] == 1
        assert bad_behavior.has_issues

        (root / "duplicate_selector.json").write_text(
            json.dumps(
                {
                    "name": "Duplicate Selector",
                    "steps": [
                        {
                            "type": "interact",
                            "target": "gadget",
                            "gadget": "CHEST",
                            "selector": "CHEST",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        duplicate_selector = audit.audit_root(root)
        assert duplicate_selector.semantic_counts["gadget.duplicate_selector"] == 1
        assert duplicate_selector.has_issues

    print("json_bt_compiler_contract: ok")
    return 0


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


def _load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_json_bt_vocabulary", AUDIT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
