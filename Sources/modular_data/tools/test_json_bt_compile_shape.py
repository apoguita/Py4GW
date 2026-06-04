"""Offline compile-shape check for every modular JSON recipe.

This intentionally stubs PyGW runtime modules. It verifies the JSON-to-BT compiler
can build tree objects for the whole corpus without requiring injected bindings.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from enum import Enum
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
COMPILER_PATH = REPO_ROOT / "Py4GWCoreLib" / "modular" / "json_bt_compiler.py"
MODULAR_DATA_ROOT = REPO_ROOT / "Sources" / "modular_data"


class _NodeState(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class _Node:
    def __init__(self, name: str = "Node", **_kwargs: Any) -> None:
        self.name = name

    def reset(self) -> None:
        return


class _ActionNode(_Node):
    def __init__(self, name: str = "Action", action_fn=None, args=None, **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)
        self.action_fn = action_fn
        self.args = list(args or [])
        self.kwargs = dict(kwargs)


class _SequenceNode(_Node):
    def __init__(self, children=None, name: str = "Sequence") -> None:
        super().__init__(name=name)
        self.children = list(children or [])
        self._current_child_index = 0

    def reset(self) -> None:
        self._current_child_index = 0
        for child in self.children:
            reset = getattr(child, "reset", None)
            if callable(reset):
                reset()


class _SubtreeNode(_Node):
    def __init__(self, name: str = "Subtree", subtree_fn=None) -> None:
        super().__init__(name=name)
        self.subtree_fn = subtree_fn


class _BehaviorTree:
    NodeState = _NodeState
    Node = _Node
    ActionNode = _ActionNode
    SequenceNode = _SequenceNode
    SubtreeNode = _SubtreeNode
    SucceederNode = _Node

    def __init__(self, root: _Node) -> None:
        self.root = root

    def reset(self) -> None:
        self.root.reset()


class _BTNamespace:
    def __getattr__(self, name: str):
        def _factory(*args: Any, **kwargs: Any) -> _BehaviorTree:
            return _BehaviorTree(_ActionNode(name=name, args=args, **kwargs))

        return _factory


class _CompositeNamespace:
    @staticmethod
    def Sequence(*trees: _BehaviorTree, name: str = "Sequence") -> _BehaviorTree:
        return _BehaviorTree(_SequenceNode(children=[tree.root for tree in trees], name=name))


def main() -> int:
    _install_stubs()
    compiler = _load_compiler()
    _assert_route_pause_contract(compiler)
    failures: list[str] = []
    compiled = 0
    party_loads = 0
    route_moves = 0

    for path in sorted(MODULAR_DATA_ROOT.rglob("*.json")):
        try:
            recipe = json.loads(path.read_text(encoding="utf-8-sig"))
            tree = compiler.compile_recipe_to_bt(recipe, recipe_name=str(recipe.get("name") or path.stem))
            compiled_steps = compiler.compile_recipe_steps_to_bt(
                recipe,
                recipe_name=str(recipe.get("name") or path.stem),
            )
            if not isinstance(tree, _BehaviorTree):
                raise AssertionError(f"expected BehaviorTree, got {type(tree).__name__}")
            _assert_per_step_compile_shape(tree, compiled_steps, recipe)
            party_loads += _assert_party_load_shape(tree, recipe)
            route_moves += _assert_route_move_shape(tree, recipe)
            compiled += 1
        except Exception as exc:
            failures.append(f"{path.relative_to(REPO_ROOT)}: {type(exc).__name__}: {exc}")

    if failures:
        print(f"Compiled {compiled} recipe shape(s), {len(failures)} failure(s):")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(
        f"json_bt_compile_shape: compiled {compiled} recipe shape(s), verified {party_loads} party load(s), "
        f"{route_moves} non-combat route move(s)"
    )
    return 0


def _install_stubs() -> None:
    py4gwcorelib = types.ModuleType("Py4GWCoreLib")
    py4gwcorelib.__path__ = [str(REPO_ROOT / "Py4GWCoreLib")]
    sys.modules["Py4GWCoreLib"] = py4gwcorelib

    modular = types.ModuleType("Py4GWCoreLib.modular")
    modular.__path__ = [str(REPO_ROOT / "Py4GWCoreLib" / "modular")]
    sys.modules["Py4GWCoreLib.modular"] = modular

    behavior_pkg = types.ModuleType("Py4GWCoreLib.py4gwcorelib_src")
    behavior_pkg.__path__ = [str(REPO_ROOT / "Py4GWCoreLib" / "py4gwcorelib_src")]
    sys.modules["Py4GWCoreLib.py4gwcorelib_src"] = behavior_pkg

    behavior_mod = types.ModuleType("Py4GWCoreLib.py4gwcorelib_src.BehaviorTree")
    behavior_mod.BehaviorTree = _BehaviorTree
    sys.modules["Py4GWCoreLib.py4gwcorelib_src.BehaviorTree"] = behavior_mod

    bt_pkg = types.ModuleType("Py4GWCoreLib.routines_src")
    bt_pkg.__path__ = [str(REPO_ROOT / "Py4GWCoreLib" / "routines_src")]
    sys.modules["Py4GWCoreLib.routines_src"] = bt_pkg

    bt_mod = types.ModuleType("Py4GWCoreLib.routines_src.BehaviourTrees")
    bt = types.SimpleNamespace(
        Agents=_BTNamespace(),
        Composite=_CompositeNamespace(),
        Map=_BTNamespace(),
        Movement=_BTNamespace(),
        Party=_BTNamespace(),
        Player=_BTNamespace(),
        Shared=_BTNamespace(),
    )
    bt_mod.BT = bt
    sys.modules["Py4GWCoreLib.routines_src.BehaviourTrees"] = bt_mod

    hero_setup_model = types.ModuleType("Py4GWCoreLib.modular.hero_setup_model")
    hero_setup_model.get_team_by_priority = _stub_get_team_by_priority
    hero_setup_model.resolve_hero_ids = _stub_resolve_hero_ids
    sys.modules["Py4GWCoreLib.modular.hero_setup_model"] = hero_setup_model

    enum_pkg = types.ModuleType("Py4GWCoreLib.enums_src")
    enum_pkg.__path__ = [str(REPO_ROOT / "Py4GWCoreLib" / "enums_src")]
    sys.modules["Py4GWCoreLib.enums_src"] = enum_pkg

    multibox_mod = types.ModuleType("Py4GWCoreLib.enums_src.Multiboxing_enums")
    multibox_mod.SharedCommandType = types.SimpleNamespace(UseSummoningStone="UseSummoningStone")
    sys.modules["Py4GWCoreLib.enums_src.Multiboxing_enums"] = multibox_mod


def _load_compiler():
    spec = importlib.util.spec_from_file_location("Py4GWCoreLib.modular.json_bt_compiler", COMPILER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[str(spec.name)] = module
    spec.loader.exec_module(module)
    return module


_HERO_NAME_TO_ID = {
    "tahlkora": 3,
    "masterofwhispers": 4,
    "koss": 6,
    "dunkoro": 7,
    "melonni": 9,
    "zhedshadowhoof": 10,
    "generalmorgahn": 11,
}
_DEFAULT_PRIORITY = [24, 27, 21, 26, 25, 4, 37, 3, 6, 7, 9, 10, 11]


def _stub_get_team_by_priority(max_heroes: int, required_hero_ids=None) -> list[int]:
    slots = max(0, int(max_heroes) - 1)
    team: list[int] = []
    for hero_id in list(required_hero_ids or []) + _DEFAULT_PRIORITY:
        hero_id = int(hero_id)
        if hero_id > 0 and hero_id not in team:
            team.append(hero_id)
    return team[:slots]


def _stub_resolve_hero_ids(value: Any) -> list[int]:
    if value is None:
        names: list[str] = []
    elif isinstance(value, str):
        names = [value]
    elif isinstance(value, list):
        names = [str(item) for item in value if isinstance(item, str)]
    else:
        names = []
    resolved: list[int] = []
    for name in names:
        key = "".join(ch for ch in name.lower() if ch.isalnum())
        hero_id = _HERO_NAME_TO_ID.get(key)
        if hero_id and hero_id not in resolved:
            resolved.append(hero_id)
    return resolved


def _expanded_steps(recipe: dict[str, Any]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for step in recipe.get("steps") or []:
        repeat = max(1, int(step.get("repeat", 1) or 1))
        expanded.extend([step] * repeat)
    return expanded


def _assert_party_load_shape(tree: _BehaviorTree, recipe: dict[str, Any]) -> int:
    root = tree.root
    children = list(getattr(root, "children", []) or [])
    verified = 0
    for index, step in enumerate(_expanded_steps(recipe)):
        if step.get("type") != "party" or step.get("action") != "load":
            continue
        child = children[index]
        subtree_fn = getattr(child, "subtree_fn", None)
        step_tree = subtree_fn(child) if callable(subtree_fn) else None
        node = getattr(step_tree, "root", None)
        if getattr(node, "name", "") != "LoadParty":
            raise AssertionError(f"party load step {index + 1} did not compile to BT.Party.LoadParty")
        hero_ids = list(getattr(node, "kwargs", {}).get("hero_ids") or [])
        max_heroes = int(step.get("max_heroes", 7) or 7)
        if max_heroes > 1 and not hero_ids:
            raise AssertionError(f"party load step {index + 1} resolved no heroes")
        if len(hero_ids) > max(0, max_heroes - 1):
            raise AssertionError(f"party load step {index + 1} resolved too many heroes: {hero_ids}")
        required = _stub_resolve_hero_ids(step.get("required_hero", recipe.get("required_hero")))
        missing = [hero_id for hero_id in required if hero_id not in hero_ids]
        if missing and len(required) <= max(0, max_heroes - 1):
            raise AssertionError(f"party load step {index + 1} is missing required hero ids {missing}")
        verified += 1
    return verified


def _assert_route_move_shape(tree: _BehaviorTree, recipe: dict[str, Any]) -> int:
    root = tree.root
    children = list(getattr(root, "children", []) or [])
    verified = 0
    for index, step in enumerate(_expanded_steps(recipe)):
        if step.get("type") != "route" or step.get("mode", "move") not in {"move", "exit"}:
            continue
        child = children[index]
        subtree_fn = getattr(child, "subtree_fn", None)
        step_tree = subtree_fn(child) if callable(subtree_fn) else None
        node = _primary_step_node(step_tree)
        kwargs = getattr(node, "kwargs", {})
        if kwargs.get("pause_on_combat") is not False:
            raise AssertionError(
                f"route {step.get('mode', 'move')} step {index + 1} should not pause on combat by default"
            )
        verified += 1
    return verified


def _assert_route_pause_contract(compiler) -> None:
    recipe = {
        "name": "Route Pause Contract",
        "steps": [
            {"type": "route", "mode": "move", "points": [[1, 2]]},
            {"type": "route", "mode": "exit", "point": [1, 2], "target_map_id": 1},
            {"type": "route", "mode": "kill", "points": [[1, 2]]},
            {"type": "route", "mode": "move", "points": [[1, 2]], "pause_on_combat": True},
        ],
    }
    tree = compiler.compile_recipe_to_bt(recipe, recipe_name="Route Pause Contract")
    expected = [False, False, True, True]
    for index, expected_pause in enumerate(expected):
        child = tree.root.children[index]
        step_tree = child.subtree_fn(child)
        node = _primary_step_node(step_tree)
        actual = getattr(node, "kwargs", {}).get("pause_on_combat")
        if actual is not expected_pause:
            raise AssertionError(f"route pause contract step {index + 1}: expected {expected_pause}, got {actual}")


def _assert_per_step_compile_shape(tree: _BehaviorTree, compiled_steps: tuple, recipe: dict[str, Any]) -> None:
    expanded = _expanded_steps(recipe)
    if len(compiled_steps) != len(expanded):
        raise AssertionError(f"per-step compile count mismatch: {len(compiled_steps)} != {len(expanded)}")
    children = list(getattr(tree.root, "children", []) or [])
    if len(children) != len(compiled_steps):
        raise AssertionError(f"full tree child count mismatch: {len(children)} != {len(compiled_steps)}")
    for index, compiled_step in enumerate(compiled_steps):
        metadata = getattr(compiled_step, "metadata", None)
        if metadata is None or int(metadata.index) != index + 1:
            raise AssertionError(f"per-step metadata index mismatch at {index + 1}")
        full_step_tree = children[index].subtree_fn(children[index])
        per_step_tree = getattr(compiled_step, "tree", None)
        full_root_name = getattr(getattr(full_step_tree, "root", None), "name", "")
        per_step_root_name = getattr(getattr(per_step_tree, "root", None), "name", "")
        if full_root_name != per_step_root_name:
            raise AssertionError(f"per-step tree shape mismatch at {index + 1}")


def _primary_step_node(step_tree: _BehaviorTree | None) -> _Node | None:
    node = getattr(step_tree, "root", None)
    if getattr(node, "name", "") == "StepWithPostWait":
        children = list(getattr(node, "children", []) or [])
        if children:
            return children[0]
    return node


if __name__ == "__main__":
    raise SystemExit(main())
