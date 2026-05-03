from typing import Callable, Sequence

import Py4GW
from HeroAI.headless_tree import HeroAIHeadlessTree

from .botting_tree_src.blackboard import BottingTreeBlackboardMixin
from .botting_tree_src.config import _BottingTreeConfig
from .botting_tree_src.debugging import BottingTreeDebuggingMixin
from .botting_tree_src.enums import HeroAIStatus, PlannerStatus
from .botting_tree_src.heroai import BottingTreeHeroAIMixin
from .botting_tree_src.isolation import BottingTreeIsolationMixin
from .botting_tree_src.messaging import BottingTreeMessagingMixin
from .botting_tree_src.routine import BottingTreeRoutineMixin
from .botting_tree_src.services import BottingTreeServicesMixin
from .botting_tree_src.templates import BottingTreeTemplates, _BottingTreeTemplates
from .botting_tree_src.ticks import BottingTreeTicksMixin
from .botting_tree_src.ui import BottingTreeUIMovePathMixin, _BottingTreeUI
from .botting_tree_src.upkeep import BottingTreeUpkeepMixin
from .py4gwcorelib_src.BehaviorTree import BehaviorTree


class BottingTree(
    BottingTreeBlackboardMixin,
    BottingTreeDebuggingMixin,
    BottingTreeMessagingMixin,
    BottingTreeRoutineMixin,
    BottingTreeUpkeepMixin,
    BottingTreeServicesMixin,
    BottingTreeIsolationMixin,
    BottingTreeHeroAIMixin,
    BottingTreeTicksMixin,
    BottingTreeUIMovePathMixin,
):
    """
    Minimal botting tree controller:
    - owns a headless HeroAI combat service
    - pauses planner work during combat by default
    - lets the user plug in their own planner tree via SetPlannerTree(...)
    """

    @classmethod
    def Create(
        cls,
        bot_name: str = 'Botting Tree',
        *,
        main_routine: BehaviorTree | BehaviorTree.Node | Callable[[], object] | Sequence[object] | None = None,
        routine_name: str = 'MainRoutine',
        repeat: bool = False,
        reset: bool = False,
        auto_start: bool = False,
        pause_on_combat: bool = True,
        isolation_enabled: bool = True,
        configure_fn: Callable[['BottingTree'], object] | None = None,
    ) -> 'BottingTree':
        tree = cls(
            bot_name=bot_name,
            pause_on_combat=pause_on_combat,
            isolation_enabled=isolation_enabled,
        )

        if callable(configure_fn):
            configure_fn(tree)

        if main_routine is not None:
            tree.SetMainRoutine(
                main_routine,
                name=routine_name,
                repeat=repeat,
                reset=reset,
            )

        if auto_start:
            tree.Start()

        return tree

    def __init__(self, bot_name: str = 'Botting Tree', pause_on_combat: bool = True, isolation_enabled: bool = True):
        self.bot_name = bot_name
        self._previous_isolation_state: bool | None = None
        self._previous_isolation_group_id: int | None = None
        self.headless_heroai = HeroAIHeadlessTree()
        self._planner_steps: list[tuple[str, Callable[[], object] | object]] = []
        self._planner_sequence_name = 'PlannerSequence'
        self._service_steps: list[tuple[str, Callable[[], object] | object]] = []
        self._service_trees: list[tuple[str, BehaviorTree]] = []
        self.planner_tree = self._build_default_planner_tree()
        self.tree = self._build_parallel_tree()
        self._last_planner_gate_state = None
        self._last_heroai_state = None
        self.Config = _BottingTreeConfig(self)
        self.Templates = _BottingTreeTemplates(self)
        self.UI = _BottingTreeUI(self)

        self.pause_on_combat = pause_on_combat
        self.isolation_enabled = isolation_enabled
        self.restore_isolation_on_stop = True
        self.headless_heroai_enabled = True
        self.looting_enabled = True
        self.planner_repeat = False
        self.started = False
        self.paused = False
        self.draw_move_path_enabled = True
        self.draw_move_path_labels = False
        self.draw_move_path_thickness = 4.0
        self.draw_move_waypoint_radius = 15.0
        self.draw_move_current_waypoint_radius = 20.0
        self.output_detailed_logging = False

    def Start(self):
        self.Reset()
        if self.IsHeadlessHeroAIEnabled():
            self.RestoreHeroAIOptions()
        self.ClearPendingMessages()
        self._capture_isolation_state_for_restore()
        self.ApplyAccountIsolation()
        self.started = True
        self.paused = False

        Py4GW.Console.Log('BottingTree', 'Botting tree started.', Py4GW.Console.MessageType.Info)

    def Stop(self):
        if self.started:
            self.started = False
            self.paused = False
            self.ClearPendingMessages()
            self.RestoreAccountIsolation()
            self.Reset()

            Py4GW.Console.Log('BottingTree', 'Botting tree stopped and reset.', Py4GW.Console.MessageType.Info)

    def Reset(self):
        self.tree.reset()
        self.planner_tree.reset()
        self.headless_heroai.reset()
        if self._service_steps:
            self._service_trees = [
                (step_name, self._coerce_runtime_tree(subtree_or_builder))
                for step_name, subtree_or_builder in self._service_steps
            ]
            self._rebuild_root_tree()
        else:
            for _, service_tree in self._service_trees:
                service_tree.reset()
        self.tree.blackboard.clear()
        self._last_planner_gate_state = None
        self._last_heroai_state = None
        if self.IsHeadlessHeroAIEnabled():
            self.RestoreHeroAIOptions()
        self.ClearPendingMessages()

        Py4GW.Console.Log('BottingTree', 'Botting tree reset.', Py4GW.Console.MessageType.Info)

    def Pause(self, pause: bool = True):
        if pause and not self.paused:
            self.paused = True
            Py4GW.Console.Log('BottingTree', 'Botting tree paused.', Py4GW.Console.MessageType.Info)
        elif not pause and self.paused:
            self.paused = False
            Py4GW.Console.Log('BottingTree', 'Botting tree unpaused.', Py4GW.Console.MessageType.Info)

    def IsPaused(self) -> bool:
        return self.paused

    def IsStarted(self) -> bool:
        return self.started

__all__ = [
    'BottingTree',
    'BottingTreeTemplates',
    'HeroAIStatus',
    'PlannerStatus',
    '_BottingTreeConfig',
    '_BottingTreeTemplates',
    '_BottingTreeUI',
]
