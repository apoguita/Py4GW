"""Offline contract check for the BottingTree-backed modular recipe runner."""
from __future__ import annotations

import ast
import importlib
import json
import sys
import tempfile
import types
from enum import Enum
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = REPO_ROOT / "Py4GWCoreLib" / "modular" / "runner.py"


class _NodeState(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class _Node:
    def __init__(self, name: str = "Node", **_kwargs: Any) -> None:
        self.name = name
        self.blackboard: dict = {}

    def reset(self) -> None:
        return

    def tick(self):
        return _NodeState.SUCCESS


class _ActionNode(_Node):
    def __init__(self, name: str = "Action", action_fn=None, args=None, **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)
        self.action_fn = action_fn
        self.args = list(args or [])
        self.kwargs = dict(kwargs)

    def tick(self):
        if callable(self.action_fn):
            result = self.action_fn()
            return result if isinstance(result, _NodeState) else _NodeState.SUCCESS
        return _NodeState.SUCCESS


class _SequenceNode(_Node):
    def __init__(self, children=None, name: str = "Sequence") -> None:
        super().__init__(name=name)
        self.children = list(children or [])
        self._current_child_index = 0


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
        self.blackboard: dict = {}
        self.tick_count = 0

    def reset(self) -> None:
        self.root.reset()

    def tick(self):
        self.tick_count += 1
        self.root.blackboard = self.blackboard
        return self.root.tick()


class _BottingTree:
    instances: list["_BottingTree"] = []

    def __init__(self, bot_name: str = "Botting Tree", pause_on_combat: bool = True, isolation_enabled=None, **_kwargs):
        self.bot_name = bot_name
        self.pause_on_combat = pause_on_combat
        self.isolation_enabled = isolation_enabled
        self.blackboard: dict = {}
        self.started = False
        self.paused = False
        self.steps: list[tuple[str, Any]] = []
        self.repeat = False
        self.current_index = 0
        _BottingTree.instances.append(self)

    def SetCurrentNamedPlannerSteps(
        self,
        steps,
        start_from=None,
        name="PlannerSequence",
        auto_start=False,
        reset=True,
        repeat=False,
    ):
        self.steps = list(steps)
        self.repeat = bool(repeat)
        self.current_index = 0
        if reset:
            self.Reset()
        if auto_start:
            self.Start()

    def Start(self):
        self.started = True
        self.paused = False
        self._publish_current_step()

    def Stop(self):
        self.started = False
        self.paused = False

    def Reset(self):
        self.blackboard.clear()
        self.current_index = 0

    def Pause(self, pause=True):
        self.paused = bool(pause)

    def IsStarted(self):
        return self.started

    def IsPaused(self):
        return self.paused

    def tick(self):
        if not self.started or self.paused:
            return _NodeState.RUNNING
        self._publish_current_step()
        if self.steps:
            _name, builder = self.steps[self.current_index]
            tree = builder() if callable(builder) else builder
            self.blackboard["runner_used_botting_tree_blackboard"] = True
            tick = getattr(tree, "tick", None)
            if callable(tick):
                tick()
        self.blackboard["PLANNER_STATUS"] = "TICK"
        return _NodeState.RUNNING

    def GetBlackboardValue(self, key, default=None):
        return self.blackboard.get(key, default)

    def _publish_current_step(self):
        if self.steps:
            self.blackboard["current_step_name"] = self.steps[self.current_index][0]


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
    _assert_runner_source_contract()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "routes").mkdir()
        (root / "routes" / "fixture.json").write_text(
            json.dumps(
                {
                    "name": "Fixture Route",
                    "steps": [
                        {"type": "wait", "ms": 1, "name": "Warmup"},
                        {"type": "route", "mode": "move", "points": [[1, 2]], "name": "Move"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        _install_stubs(root)
        runner_mod = importlib.import_module("Py4GWCoreLib.modular.runner")
        runner = runner_mod.BTRecipeRunner(
            name="Runner Fixture",
            specs=[runner_mod.RecipeSpec(kind="route", key="fixture", title="Fixture Route")],
            start_step_index=1,
            loop=True,
        )
        botting_tree = _BottingTree.instances[-1]
        assert botting_tree.pause_on_combat is False
        assert botting_tree.repeat is True
        assert len(botting_tree.steps) == 1
        assert botting_tree.steps[0][0].startswith("01.002 ")
        runner.start()
        assert runner.is_running()
        assert runner.get_step_progress()[0:2] == (2, 2)
        runner.update()
        blackboard = runner.get_runtime_blackboard()
        assert blackboard["runner_used_botting_tree_blackboard"] is True
        assert blackboard["current_step_name"] == botting_tree.steps[0][0]
    print("bt_recipe_runner_botting_tree: ok")
    return 0


def _assert_runner_source_contract() -> None:
    text = RUNNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imported_names = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "Py4GWCoreLib.BottingTree"
        for alias in node.names
    }
    assert "BottingTree" in imported_names
    assert "SetCurrentNamedPlannerSteps" in text
    assert "_refresh_runtime_blackboard" not in text
    assert "recipe.tree.tick" not in text


def _install_stubs(modular_root: Path) -> None:
    for name in list(sys.modules):
        if name == "Py4GWCoreLib" or name.startswith("Py4GWCoreLib."):
            sys.modules.pop(name, None)

    py4gwcorelib = types.ModuleType("Py4GWCoreLib")
    py4gwcorelib.__path__ = [str(REPO_ROOT / "Py4GWCoreLib")]
    sys.modules["Py4GWCoreLib"] = py4gwcorelib

    modular = types.ModuleType("Py4GWCoreLib.modular")
    modular.__path__ = [str(REPO_ROOT / "Py4GWCoreLib" / "modular")]
    sys.modules["Py4GWCoreLib.modular"] = modular

    paths_mod = types.ModuleType("Py4GWCoreLib.modular.paths")
    paths_mod.modular_data_root = lambda: str(modular_root)
    sys.modules["Py4GWCoreLib.modular.paths"] = paths_mod

    botting_tree_mod = types.ModuleType("Py4GWCoreLib.BottingTree")
    botting_tree_mod.BottingTree = _BottingTree
    sys.modules["Py4GWCoreLib.BottingTree"] = botting_tree_mod

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
    bt_mod.BT = types.SimpleNamespace(
        Agents=_BTNamespace(),
        Composite=_CompositeNamespace(),
        Map=_BTNamespace(),
        Movement=_BTNamespace(),
        Party=_BTNamespace(),
        Player=_BTNamespace(),
        Shared=_BTNamespace(),
    )
    sys.modules["Py4GWCoreLib.routines_src.BehaviourTrees"] = bt_mod


if __name__ == "__main__":
    raise SystemExit(main())
