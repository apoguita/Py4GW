"""Offline contract check for modular compiler planner-step adapter."""
from __future__ import annotations

import importlib
import json
import sys
import tempfile
import types
from enum import Enum
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]


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

    def get_children(self):
        return []


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

    def get_children(self):
        return list(self.children)


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

    @staticmethod
    def as_tree(value):
        if isinstance(value, _BehaviorTree):
            return value
        if isinstance(value, _Node):
            return _BehaviorTree(value)
        raise TypeError(type(value).__name__)

    @staticmethod
    def resolve_tree(value_or_builder):
        value = value_or_builder() if callable(value_or_builder) else value_or_builder
        return _BehaviorTree.as_tree(value)

    @staticmethod
    def build_sequence(children, name="Sequence", step_name_fn=None):
        nodes = [
            _SubtreeNode(
                name=step_name_fn(index, child) if step_name_fn else f"Step{index + 1}",
                subtree_fn=lambda _node, child=child: _BehaviorTree.resolve_tree(child),
            )
            for index, child in enumerate(children)
        ]
        return _BehaviorTree(_SequenceNode(children=nodes, name=name))

    @staticmethod
    def build_named_sequence(steps, start_from=None, name="NamedSequence", before_step=None, repeat=False):
        step_list = list(steps)
        if start_from is not None:
            names = [step_name for step_name, _builder in step_list]
            step_list = step_list[names.index(start_from) :]
        nodes = [
            _SubtreeNode(
                name=step_name,
                subtree_fn=lambda _node, builder=builder: _BehaviorTree.resolve_tree(builder),
            )
            for step_name, builder in step_list
        ]
        return _BehaviorTree(_SequenceNode(children=nodes, name=name))

    def reset(self) -> None:
        self.root.reset()

    def tick(self):
        return self.root.tick()


class _BTNamespace:
    def __getattr__(self, name: str):
        def _factory(*args: Any, **kwargs: Any) -> _BehaviorTree:
            return _BehaviorTree(_ActionNode(name=name, args=args, **kwargs))

        return _factory


class _CompositeNamespace:
    @staticmethod
    def Sequence(*trees: _BehaviorTree, name: str = "Sequence") -> _BehaviorTree:
        return _BehaviorTree.build_sequence(trees, name=name)


class _BottingTree:
    instances: list["_BottingTree"] = []

    def __init__(self, bot_name: str = "Botting Tree", pause_on_combat: bool = True, isolation_enabled=None, **_kwargs):
        self.bot_name = bot_name
        self.pause_on_combat = pause_on_combat
        self.isolation_enabled = isolation_enabled
        self.blackboard: dict = {}
        self.steps: list[tuple[str, Any]] = []
        self.repeat = False
        self.started = False
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
        if auto_start:
            self.Start()

    def Start(self):
        self.started = True

    def IsStarted(self):
        return self.started


def main() -> int:
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
        compiler = importlib.import_module("Py4GWCoreLib.modular.json_bt_compiler")
        recipe = compiler.load_recipe("routes/fixture.json")
        planner_steps = compiler.compile_recipe_steps_to_named_planner_steps(
            recipe,
            recipe_name="Fixture Route",
            planner_prefix="01.",
        )
        assert [name for name, _builder in planner_steps] == ["01.001 Warmup", "01.002 Move"]
        metadata = getattr(planner_steps[1][1], "modular_step_metadata")
        assert metadata.index == 2
        assert metadata.title == "Move"
        assert isinstance(planner_steps[1][1](), _BehaviorTree)

        botting_mod = importlib.import_module("Py4GWCoreLib.BottingTree")
        bot = botting_mod.BottingTree(bot_name="Fixture", pause_on_combat=False, isolation_enabled=False)
        bot.SetCurrentNamedPlannerSteps(planner_steps[1:], name="Fixture", repeat=True)
        assert bot.steps[0][0] == "01.002 Move"
        assert bot.repeat is True
    print("modular_botting_tree_adapter: ok")
    return 0


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
