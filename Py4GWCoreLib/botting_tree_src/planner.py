from collections.abc import Sequence as RuntimeSequence
from typing import TYPE_CHECKING, Callable, Sequence, cast

from ..py4gwcorelib_src.BehaviorTree import BehaviorTree


class BottingTreePlannerMixin:
    _service_trees: list[tuple[str, BehaviorTree]]
    planner_tree: BehaviorTree
    tree: BehaviorTree
    _planner_steps: list[tuple[str, Callable[[], object] | object]]
    _planner_sequence_name: str
    planner_repeat: bool

    if TYPE_CHECKING:
        def Start(self) -> None: ...

        def Reset(self) -> None: ...

        def GetBlackboardValue(self, key: str, default=None): ...

        def SetBlackboardValue(self, key: str, value) -> None: ...

        def ClearBlackboardValue(self, key: str) -> None: ...

        def _tick_heroai(self, node: BehaviorTree.Node) -> BehaviorTree.NodeState: ...

        def _tick_planner(self, node: BehaviorTree.Node) -> BehaviorTree.NodeState: ...

        def _tick_service_tree(self, node: BehaviorTree.Node, service_tree: BehaviorTree, service_name: str) -> BehaviorTree.NodeState: ...

    def _build_default_planner_tree(self) -> BehaviorTree:
        return BehaviorTree(
            root=BehaviorTree.ActionNode(
                name='DefaultPlannerTick',
                action_fn=lambda node: BehaviorTree.NodeState.RUNNING,
            )
        )

    def _build_parallel_tree(self) -> BehaviorTree:
        heroai_branch = BehaviorTree.RepeaterForeverNode(
            BehaviorTree.ActionNode(
                name='HeroAIServiceTick',
                action_fn=lambda node: self._tick_heroai(node),
            ),
            name='HeroAIService',
        )

        planner_branch = BehaviorTree.RepeaterForeverNode(
            BehaviorTree.ActionNode(
                name='PlannerServiceTick',
                action_fn=lambda node: self._tick_planner(node),
            ),
            name='PlannerService',
        )

        service_branches = [
            BehaviorTree.RepeaterForeverNode(
                BehaviorTree.ActionNode(
                    name=f'{service_name}Tick',
                    action_fn=lambda node, service_tree=service_tree, service_name=service_name: self._tick_service_tree(
                        node,
                        service_tree,
                        service_name,
                    ),
                ),
                name=service_name,
            )
            for service_name, service_tree in self._service_trees
        ]

        return BehaviorTree(
            root=BehaviorTree.ParallelNode(
                children=[heroai_branch, planner_branch, *service_branches],
                name='Root',
            )
        )

    def ProcessRestartRequest(self) -> bool:
        restart_step_name = str(self.GetBlackboardValue('restart_step_name_request', '') or '')
        if not restart_step_name:
            return False

        self.ClearBlackboardValue('restart_step_name_request')
        self.ClearBlackboardValue('current_step_name')
        return self.RestartFromNamedPlannerStep(restart_step_name, auto_start=True)

    def tick(self):
        result = self.tree.tick()
        self.ProcessRestartRequest()
        return result

    def _rebuild_root_tree(self):
        blackboard = dict(self.tree.blackboard) if hasattr(self, 'tree') and self.tree is not None else {}
        self.tree = self._build_parallel_tree()
        self.tree.blackboard.update(blackboard)

    def _set_planner_tree(self, planner_tree: BehaviorTree | None):
        self.planner_tree = planner_tree or self._build_default_planner_tree()

    def SetPlannerTree(self, planner_tree: BehaviorTree | None):
        self._planner_steps = []
        self._planner_sequence_name = 'PlannerSequence'
        self._set_planner_tree(planner_tree)

    def SetCurrentTree(
        self,
        planner_tree: BehaviorTree | None,
        auto_start: bool = False,
        reset: bool = True,
    ):
        self.SetPlannerTree(planner_tree)
        if auto_start:
            self.Start()
        elif reset:
            self.Reset()

    def _build_sequence_from_children(
        self,
        children: Sequence[object],
        name: str = 'MainRoutine',
    ) -> BehaviorTree:
        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name=name,
                children=[
                    BehaviorTree.SubtreeNode(
                        name=f'{name} Step {index + 1}',
                        subtree_fn=lambda node, child=child: self._coerce_runtime_tree(child),
                    )
                    for index, child in enumerate(children)
                ],
            )
        )

    def _build_named_planner_tree(
        self,
        steps: Sequence[tuple[str, Callable[[], object] | object]],
        start_from: str | None = None,
        name: str = 'PlannerSequence',
        repeat: bool = False,
    ) -> BehaviorTree:
        if not steps:
            return BehaviorTree(BehaviorTree.SequenceNode(name=name, children=[]))

        step_names = [step_name for step_name, _ in steps]
        start_index = 0
        if start_from is not None:
            if start_from not in step_names:
                raise ValueError(f"Unknown planner step '{start_from}'. Valid values: {', '.join(step_names)}")
            start_index = step_names.index(start_from)

        def _as_tree(subtree_or_builder: Callable[[], object] | object) -> BehaviorTree:
            subtree = subtree_or_builder() if callable(subtree_or_builder) else subtree_or_builder
            if isinstance(subtree, BehaviorTree):
                return subtree
            if isinstance(subtree, BehaviorTree.Node):
                return BehaviorTree(subtree)
            if hasattr(subtree, 'root') and hasattr(subtree, 'tick') and hasattr(subtree, 'reset'):
                return cast(BehaviorTree, subtree)
            raise TypeError(f'Planner step returned invalid type {type(subtree).__name__}.')

        def _mark_current_step(step_name: str) -> BehaviorTree.Node:
            def _mark(node: BehaviorTree.Node, step_name: str = step_name) -> BehaviorTree.NodeState:
                node.blackboard['current_step_name'] = step_name
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.ActionNode(
                name=f'MarkCurrentStep({step_name})',
                action_fn=_mark,
                aftercast_ms=0,
            )

        children: list[BehaviorTree.Node] = [
            BehaviorTree.SequenceNode(
                name=f'Step: {step_name}',
                children=[
                    _mark_current_step(step_name),
                    BehaviorTree.SubtreeNode(
                        name=step_name,
                        subtree_fn=lambda node, subtree_or_builder=subtree_or_builder: _as_tree(subtree_or_builder),
                    ),
                ],
            )
            for step_name, subtree_or_builder in steps[start_index:]
        ]
        if repeat:
            full_pass = self._build_named_planner_tree(steps, start_from=None, name=f'{name} Full Pass', repeat=False)
            children.append(
                BehaviorTree.RepeaterForeverNode(
                    full_pass.root,
                    name='Loop: restart routine',
                )
            )
        return BehaviorTree(BehaviorTree.SequenceNode(name=name, children=children))

    def _coerce_runtime_tree(self, subtree_or_builder: Callable[[], object] | object) -> BehaviorTree:
        subtree = subtree_or_builder() if callable(subtree_or_builder) else subtree_or_builder
        if isinstance(subtree, BehaviorTree):
            return subtree
        if isinstance(subtree, BehaviorTree.Node):
            return BehaviorTree(subtree)
        if hasattr(subtree, 'root') and hasattr(subtree, 'tick') and hasattr(subtree, 'reset'):
            return cast(BehaviorTree, subtree)
        raise TypeError(f'Service step returned invalid type {type(subtree).__name__}.')

    def SetMainRoutine(
        self,
        routine: BehaviorTree | BehaviorTree.Node | Callable[[], object] | Sequence[object] | None,
        name: str = 'MainRoutine',
        auto_start: bool = False,
        reset: bool = True,
        repeat: bool = False,
    ):
        if routine is None:
            self.SetPlannerTree(None)
        elif callable(routine):
            self.SetPlannerTree(self._coerce_runtime_tree(routine))
        elif isinstance(routine, RuntimeSequence) and not isinstance(routine, (str, bytes)):
            routine_items = list(routine)
            if routine_items and all(
                isinstance(item, tuple)
                and len(item) == 2
                and isinstance(item[0], str)
                for item in routine_items
            ):
                self.SetNamedPlannerSteps(
                    cast(Sequence[tuple[str, Callable[[], object] | object]], routine_items),
                    name=name,
                    repeat=repeat,
                )
            else:
                self._planner_steps = []
                self._planner_sequence_name = name
                self.planner_repeat = False
                self.SetPlannerTree(self._build_sequence_from_children(routine_items, name=name))
        else:
            self.SetPlannerTree(self._coerce_runtime_tree(routine))

        if auto_start:
            self.Start()
        elif reset:
            self.Reset()

    def SetNamedPlannerSteps(
        self,
        steps: Sequence[tuple[str, Callable[[], object] | object]],
        start_from: str | None = None,
        name: str = 'PlannerSequence',
        repeat: bool = False,
    ):
        self._planner_steps = list(steps)
        self._planner_sequence_name = name
        self.planner_repeat = repeat
        self._set_planner_tree(self._build_named_planner_tree(self._planner_steps, start_from=start_from, name=name, repeat=repeat))

    def SetCurrentNamedPlannerSteps(
        self,
        steps: Sequence[tuple[str, Callable[[], object] | object]],
        start_from: str | None = None,
        name: str = 'PlannerSequence',
        auto_start: bool = False,
        reset: bool = True,
        repeat: bool = False,
    ):
        self.SetNamedPlannerSteps(
            steps,
            start_from=start_from,
            name=name,
            repeat=repeat,
        )
        if auto_start:
            self.Start()
        elif reset:
            self.Reset()

    def GetNamedPlannerStepNames(self) -> list[str]:
        return [step_name for step_name, _ in self._planner_steps]

    def RestartFromNamedPlannerStep(
        self,
        step_name: str,
        auto_start: bool = True,
        name: str | None = None,
    ) -> bool:
        if not self._planner_steps:
            return False
        sequence_name = name or self._planner_sequence_name
        self._set_planner_tree(self._build_named_planner_tree(
            self._planner_steps,
            start_from=step_name,
            name=sequence_name,
            repeat=self.planner_repeat,
        ))
        self.Reset()
        if auto_start:
            self.Start()
        return True

    def BuildAllSequences(
        self,
        start_from: str | None = None,
        name: str | None = None,
    ) -> BehaviorTree:
        if not self._planner_steps:
            return self._build_default_planner_tree()
        sequence_name = name or self._planner_sequence_name
        return self._build_named_planner_tree(self._planner_steps, start_from=start_from, name=sequence_name)

    def RestartFromSequence(
        self,
        sequence_name: str,
        auto_start: bool = True,
        name: str | None = None,
    ) -> bool:
        return self.RestartFromNamedPlannerStep(
            sequence_name,
            auto_start=auto_start,
            name=name,
        )
