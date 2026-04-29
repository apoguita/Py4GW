from enum import Enum
from collections.abc import Sequence as RuntimeSequence
import time
from typing import Callable, Sequence, cast

import Py4GW
import PyImGui
from HeroAI.headless_tree import HeroAIHeadlessTree

from .GlobalCache import GLOBAL_CACHE
from .GlobalCache.shared_memory_src.HeroAIOptionStruct import HeroAIOptionStruct
from .IniManager import IniManager
from .Overlay import Overlay
from .Player import Player
from .Routines import Routines
from .py4gwcorelib_src.Color import Color, ColorPalette
from .py4gwcorelib_src.BehaviorTree import BehaviorTree


class HeroAIStatus(Enum):
    WAITING_MAP = "PAUSED: Waiting for explorable map"
    PLAYER_DEAD = "PAUSED: Player dead"
    PLAYER_KNOCKED_DOWN = "PAUSED: Player knocked down"
    DISABLED = "PAUSED: Headless HeroAI disabled"
    COMBAT_TICK = "COMBAT: Tick"
    OOC_TICK = "COMBAT: OOC Tick"


class PlannerStatus(Enum):
    PAUSED_ON_COMBAT = "PAUSED: HeroAI owns combat"
    PAUSED_ON_LOOTING = "PAUSED: HeroAI owns looting"
    IDLE = "PLANNER: Idle"
    TICK = "PLANNER: Tick"
    OWNER_HEROAI = "OWNER: HeroAI"
    OWNER_PLANNER = "OWNER: Planner"


class BottingTree:
    """
    Minimal botting tree controller:
    - owns a headless HeroAI combat service
    - pauses planner work during combat by default
    - lets the user plug in their own planner tree via SetPlannerTree(...)
    """

    def __init__(self, bot_name: str = "Botting Tree", pause_on_combat: bool = True, isolation_enabled: bool = True):
        self.bot_name = bot_name
        self.pause_on_combat = pause_on_combat
        self.isolation_enabled = isolation_enabled
        self._restore_isolation_on_stop = True
        self._previous_isolation_state: bool | None = None
        self._previous_isolation_group_id: int | None = None
        self.headless_heroai = HeroAIHeadlessTree()
        self.headless_heroai_enabled = True
        self.looting_enabled = True
        self._planner_steps: list[tuple[str, Callable[[], object] | object]] = []
        self._planner_sequence_name = "PlannerSequence"
        self._planner_repeat = False
        self._service_steps: list[tuple[str, Callable[[], object] | object]] = []
        self._service_trees: list[tuple[str, BehaviorTree]] = []
        self.planner_tree = self._build_default_planner_tree()
        self.tree = self._build_parallel_tree()
        self._last_planner_gate_state = None
        self._last_heroai_state = None
        self.started = False
        self.paused = False
        self.draw_move_path_enabled = True
        self.draw_move_path_labels = False
        self.draw_move_path_thickness = 4.0
        self.draw_move_waypoint_radius = 15.0
        self.draw_move_current_waypoint_radius = 20.0
        self.Templates = _BottingTreeTemplates(self)
        self.UI = _BottingTreeUI(self)

    _LOG_LAST_MESSAGE_KEY = "last_log_message"
    _LOG_LAST_MESSAGE_DATA_KEY = "last_log_message_data"
    _LOG_HISTORY_KEY = "blackboard_log_history"

    @property
    def blackboard(self) -> dict:
        return self.tree.blackboard

    def GetBlackboardValue(self, key: str, default=None):
        return self.blackboard.get(key, default)

    def SetBlackboardValue(self, key: str, value) -> None:
        self.blackboard[key] = value

    def ClearBlackboardValue(self, key: str) -> None:
        self.blackboard.pop(key, None)

    def HasBlackboardValue(self, key: str) -> bool:
        return key in self.blackboard

    def GetLastBlackboardLogMessage(self) -> str:
        value = self.blackboard.get(self._LOG_LAST_MESSAGE_KEY, "")
        return value if isinstance(value, str) else ""

    def GetLastBlackboardLogData(self) -> dict:
        value = self.blackboard.get(self._LOG_LAST_MESSAGE_DATA_KEY, {})
        return value if isinstance(value, dict) else {}

    def GetBlackboardLogHistory(self) -> list[str]:
        value = self.blackboard.get(self._LOG_HISTORY_KEY, [])
        if not isinstance(value, list):
            return []
        return [entry for entry in value if isinstance(entry, str)]

    def ClearBlackboardLog(self) -> None:
        self.blackboard.pop(self._LOG_LAST_MESSAGE_KEY, None)
        self.blackboard.pop(self._LOG_LAST_MESSAGE_DATA_KEY, None)

    def ClearBlackboardLogHistory(self) -> None:
        self.blackboard.pop(self._LOG_HISTORY_KEY, None)

    def GetDebugConsoleLastMessage(self) -> str:
        return self.GetLastBlackboardLogMessage()

    def GetDebugConsoleLastMessageData(self) -> dict:
        return self.GetLastBlackboardLogData()

    def GetDebugConsoleHistory(self) -> list[str]:
        return self.GetBlackboardLogHistory()

    def ClearDebugConsole(self) -> None:
        self.ClearBlackboardLog()
        self.ClearBlackboardLogHistory()

    def CopyDebugConsoleToClipboard(self) -> None:
        PyImGui.set_clipboard_text("\n".join(self.GetDebugConsoleHistory()))

    def DrawDebugConsole(
        self,
        child_id: str | None = None,
        height: float = 200.0,
        reverse_order: bool = True,
        show_controls: bool = True,
    ) -> None:
        if show_controls:
            if PyImGui.button("Clear UI Log"):
                self.ClearDebugConsole()
            PyImGui.same_line(0, -1)
            if PyImGui.button("Copy UI Log"):
                self.CopyDebugConsoleToClipboard()

        log_history = self.GetDebugConsoleHistory()
        child_name = child_id or f"BottingTreeDebugConsole##{id(self)}"
        if PyImGui.begin_child(child_name, (0, height), True, PyImGui.WindowFlags.HorizontalScrollbar):
            entries = log_history[::-1] if reverse_order else log_history
            for entry in entries:
                PyImGui.text_wrapped(entry)
        PyImGui.end_child()
    
    def Start(self):
        self.Reset()
        if self.IsHeadlessHeroAIEnabled():
            self.RestoreHeroAIOptions()
        self.ClearPendingMessages()
        self._capture_isolation_state_for_restore()
        self.ApplyAccountIsolation()
        self.started = True
        self.paused = False
        Py4GW.Console.Log("BottingTree", "Botting tree started.", Py4GW.Console.MessageType.Info)
            
    def Stop(self):
        if self.started:
            self.started = False
            self.paused = False
            self.ClearPendingMessages()
            self.RestoreAccountIsolation()
            self.Reset()
            Py4GW.Console.Log("BottingTree", "Botting tree stopped and reset.", Py4GW.Console.MessageType.Info)

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

    def ClearPendingMessages(self) -> int:
        account_email = Player.GetAccountEmail()
        if not account_email:
            return 0

        cleared_count = 0
        for message_index, message in GLOBAL_CACHE.ShMem.GetAllMessages():
            if message is None:
                continue
            if not getattr(message, "Active", False):
                continue
            if getattr(message, "ReceiverEmail", "") != account_email:
                continue
            GLOBAL_CACHE.ShMem.MarkMessageAsFinished(account_email, message_index)
            cleared_count += 1
        return cleared_count

    def RestoreHeroAIOptions(self) -> bool:
        cached_data = self.headless_heroai.cached_data

        def _apply_core_options(options: HeroAIOptionStruct) -> HeroAIOptionStruct:
            options.Following = True
            options.Avoidance = True
            options.Targeting = True
            options.Combat = True
            options.Looting = self.looting_enabled
            return options

        cached_data.account_options = _apply_core_options(cached_data.account_options or HeroAIOptionStruct())
        cached_data.global_options = _apply_core_options(cached_data.global_options or HeroAIOptionStruct())

        account_email = Player.GetAccountEmail()
        if not account_email:
            return False

        shared_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email) or HeroAIOptionStruct()
        shared_options = _apply_core_options(shared_options)
        GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, shared_options)
        cached_data.account_options = shared_options
        return True

    def _heroai_options_match_runtime_policy(self) -> bool:
        expected_looting = bool(self.looting_enabled)
        cached_options = self.headless_heroai.cached_data.account_options
        if cached_options is not None:
            if not all([
                bool(cached_options.Following),
                bool(cached_options.Avoidance),
                bool(cached_options.Targeting),
                bool(cached_options.Combat),
            ]):
                return False
            if bool(cached_options.Looting) != expected_looting:
                return False

        account_email = Player.GetAccountEmail()
        if not account_email:
            return True

        shared_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        if shared_options is None:
            return False

        if not all([
            bool(shared_options.Following),
            bool(shared_options.Avoidance),
            bool(shared_options.Targeting),
            bool(shared_options.Combat),
        ]):
            return False

        return bool(shared_options.Looting) == expected_looting

    def EnsureHeroAIOptionsEnabled(self) -> bool:
        if self._heroai_options_match_runtime_policy():
            return True
        return self.RestoreHeroAIOptions()
            
    def Pause(self, pause: bool = True):
        if pause and not self.paused:
            self.paused = True
            Py4GW.Console.Log("BottingTree", "Botting tree paused.", Py4GW.Console.MessageType.Info)
        elif not pause and self.paused:
            self.paused = False
            Py4GW.Console.Log("BottingTree", "Botting tree unpaused.", Py4GW.Console.MessageType.Info)    
                       
    def IsPaused(self) -> bool:
        return self.paused
    
    def IsStarted(self) -> bool:
        return self.started    
            

    def _set_planner_tree(self, planner_tree: BehaviorTree | None):
        self.planner_tree = planner_tree or self._build_default_planner_tree()

    def SetPlannerTree(self, planner_tree: BehaviorTree | None):
        self._planner_steps = []
        self._planner_sequence_name = "PlannerSequence"
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

    def SetMainRoutine(
        self,
        routine: BehaviorTree | BehaviorTree.Node | Callable[[], object] | Sequence[object] | None,
        name: str = "MainRoutine",
        auto_start: bool = False,
        reset: bool = True,
        repeat: bool = False,
    ):
        """
        Configure the planner routine used by the default BottingTree UI.

        Accepted shapes:
        - BehaviorTree
        - BehaviorTree.Node
        - callable returning a BehaviorTree or node
        - sequence of child trees/nodes/callables, wrapped in a SequenceNode
        - sequence of (step_name, tree_or_builder) tuples, exposed as restartable named steps
        """
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
                self._planner_repeat = False
                self.SetPlannerTree(self._build_sequence_from_children(routine_items, name=name))
        else:
            self.SetPlannerTree(self._coerce_runtime_tree(routine))

        if auto_start:
            self.Start()
        elif reset:
            self.Reset()

    def _build_sequence_from_children(
        self,
        children: Sequence[object],
        name: str = "MainRoutine",
    ) -> BehaviorTree:
        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name=name,
                children=[
                    BehaviorTree.SubtreeNode(
                        name=f"{name} Step {index + 1}",
                        subtree_fn=lambda node, child=child: self._coerce_runtime_tree(child),
                    )
                    for index, child in enumerate(children)
                ],
            )
        )

    def _rebuild_root_tree(self):
        blackboard = dict(self.tree.blackboard) if hasattr(self, "tree") and self.tree is not None else {}
        self.tree = self._build_parallel_tree()
        self.tree.blackboard.update(blackboard)

    def _build_named_planner_tree(
        self,
        steps: Sequence[tuple[str, Callable[[], object] | object]],
        start_from: str | None = None,
        name: str = "PlannerSequence",
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
            if hasattr(subtree, "root") and hasattr(subtree, "tick") and hasattr(subtree, "reset"):
                return cast(BehaviorTree, subtree)
            raise TypeError(f"Planner step returned invalid type {type(subtree).__name__}.")

        def _mark_current_step(step_name: str) -> BehaviorTree.Node:
            def _mark(node: BehaviorTree.Node, step_name: str = step_name) -> BehaviorTree.NodeState:
                node.blackboard["current_step_name"] = step_name
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree.ActionNode(
                name=f"MarkCurrentStep({step_name})",
                action_fn=_mark,
                aftercast_ms=0,
            )

        children: list[BehaviorTree.Node] = [
            BehaviorTree.SequenceNode(
                name=f"Step: {step_name}",
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
            full_pass = self._build_named_planner_tree(steps, start_from=None, name=f"{name} Full Pass", repeat=False)
            children.append(
                BehaviorTree.RepeaterForeverNode(
                    full_pass.root,
                    name="Loop: restart routine",
                )
            )
        return BehaviorTree(BehaviorTree.SequenceNode(name=name, children=children))

    def SetNamedPlannerSteps(
        self,
        steps: Sequence[tuple[str, Callable[[], object] | object]],
        start_from: str | None = None,
        name: str = "PlannerSequence",
        repeat: bool = False,
    ):
        self._planner_steps = list(steps)
        self._planner_sequence_name = name
        self._planner_repeat = repeat
        self._set_planner_tree(self._build_named_planner_tree(self._planner_steps, start_from=start_from, name=name, repeat=repeat))

    def SetCurrentNamedPlannerSteps(
        self,
        steps: Sequence[tuple[str, Callable[[], object] | object]],
        start_from: str | None = None,
        name: str = "PlannerSequence",
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

    def _coerce_runtime_tree(self, subtree_or_builder: Callable[[], object] | object) -> BehaviorTree:
        subtree = subtree_or_builder() if callable(subtree_or_builder) else subtree_or_builder
        if isinstance(subtree, BehaviorTree):
            return subtree
        if isinstance(subtree, BehaviorTree.Node):
            return BehaviorTree(subtree)
        if hasattr(subtree, "root") and hasattr(subtree, "tick") and hasattr(subtree, "reset"):
            return cast(BehaviorTree, subtree)
        raise TypeError(f"Service step returned invalid type {type(subtree).__name__}.")

    def SetServiceTrees(
        self,
        steps: Sequence[tuple[str, Callable[[], object] | object]],
    ):
        self._service_steps = list(steps)
        self._service_trees = [
            (step_name, self._coerce_runtime_tree(subtree_or_builder))
            for step_name, subtree_or_builder in self._service_steps
        ]
        self._rebuild_root_tree()

    def AddServiceTree(self, name: str, subtree_or_builder: Callable[[], object] | object):
        self._service_steps.append((name, subtree_or_builder))
        self._service_trees.append((name, self._coerce_runtime_tree(subtree_or_builder)))
        self._rebuild_root_tree()

    def ClearServiceTrees(self):
        self._service_steps = []
        self._service_trees = []
        self._rebuild_root_tree()

    def GetServiceTreeNames(self) -> list[str]:
        return [step_name for step_name, _ in self._service_steps]

    def SetUpkeepTrees(
        self,
        steps: Sequence[tuple[str, Callable[[], object] | object]],
    ):
        self.SetServiceTrees(steps)

    def AddUpkeepTree(self, name: str, subtree_or_builder: Callable[[], object] | object):
        self.AddServiceTree(name, subtree_or_builder)

    def ClearUpkeepTrees(self):
        self.ClearServiceTrees()

    def GetUpkeepTreeNames(self) -> list[str]:
        return self.GetServiceTreeNames()

    def AddPartyWipeRecoveryService(
        self,
        default_step_name: str | None = None,
        return_interval_ms: float = 1000.0,
    ) -> None:
        self.AddServiceTree(
            "PartyWipeRecoveryService",
            lambda: BottingTree.PartyWipeRecoveryServiceTree(
                default_step_name=default_step_name,
                return_interval_ms=return_interval_ms,
            ),
        )

    @staticmethod
    def PartyWipeRecoveryServiceTree(
        default_step_name: str | None = None,
        return_interval_ms: float = 1000.0,
    ) -> BehaviorTree:
        state = {
            "active": False,
            "step_name": "",
            "last_return_ms": 0.0,
        }

        def _reset_state(node: BehaviorTree.Node) -> None:
            state["active"] = False
            state["step_name"] = ""
            state["last_return_ms"] = 0.0
            node.blackboard["party_wipe_recovery_active"] = False

        def _tick_party_wipe_service(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            from .Map import Map
            from .py4gwcorelib_src.ActionQueue import ActionQueueManager

            now = time.monotonic() * 1000.0
            is_wiped = bool(Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated())

            if not state["active"]:
                if not is_wiped:
                    node.blackboard["party_wipe_recovery_active"] = False
                    return BehaviorTree.NodeState.RUNNING

                step_name = str(node.blackboard.get("current_step_name", "") or "")
                if not step_name:
                    step_name = str(default_step_name or "")

                state["active"] = True
                state["step_name"] = step_name
                state["last_return_ms"] = 0.0
                node.blackboard["party_wipe_recovery_active"] = True
                node.blackboard["party_wipe_recovery_step_name"] = step_name
                ActionQueueManager().ResetAllQueues()
                return BehaviorTree.NodeState.RUNNING

            node.blackboard["party_wipe_recovery_active"] = True
            node.blackboard["party_wipe_recovery_step_name"] = state["step_name"]

            if Map.IsMapReady() and Map.IsOutpost() and GLOBAL_CACHE.Party.IsPartyLoaded():
                if state["step_name"]:
                    node.blackboard["restart_step_name_request"] = state["step_name"]
                _reset_state(node)
                return BehaviorTree.NodeState.SUCCESS

            if now - float(state["last_return_ms"]) >= float(return_interval_ms):
                GLOBAL_CACHE.Party.ReturnToOutpost()
                state["last_return_ms"] = now

            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="PartyWipeRecoveryService",
                action_fn=_tick_party_wipe_service,
                aftercast_ms=0,
            )
        )

    def GetNamedPlannerStepNames(self
    ) -> list[str]:
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
            repeat=self._planner_repeat,
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

    def RestartFromSequence(self,
        sequence_name: str,
        auto_start: bool = True,
        name: str | None = None,
    ) -> bool:
        return self.RestartFromNamedPlannerStep(
            sequence_name,
            auto_start=auto_start,
            name=name,
        )

    def SetHeadlessHeroAIEnabled(self, enabled: bool, reset_runtime: bool = True):
        self.headless_heroai_enabled = enabled
        self._last_heroai_state = None
        self.ApplyAccountIsolation()
        if reset_runtime:
            self.headless_heroai.reset()
            bb = self.blackboard
            bb["COMBAT_ACTIVE"] = False
            bb["LOOTING_ACTIVE"] = False
            bb["PAUSE_MOVEMENT"] = False
            bb["USER_INTERRUPT_ACTIVE"] = False
            bb["HEROAI_SUCCESS"] = False
            bb["HEROAI_STATUS"] = HeroAIStatus.DISABLED.value if not enabled else ""

    def SetLootingEnabled(self, enabled: bool) -> bool:
        self.looting_enabled = enabled
        self.blackboard["looting_enabled"] = enabled

        self.headless_heroai.cached_data.account_options.Looting = enabled
        self.headless_heroai.cached_data.global_options.Looting = enabled

        account_email = Player.GetAccountEmail()
        if not account_email:
            return False

        account_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        if account_options is None:
            return False

        account_options.Looting = enabled
        GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, account_options)
        return True

    def EnableLooting(self) -> bool:
        return self.SetLootingEnabled(True)

    def DisableLooting(self) -> bool:
        return self.SetLootingEnabled(False)

    def ToggleLooting(self) -> bool:
        self.SetLootingEnabled(not self.looting_enabled)
        return self.looting_enabled

    def IsLootingEnabled(self) -> bool:
        return self.looting_enabled

    def EnableHeadlessHeroAI(self, reset_runtime: bool = True) -> None:
        self.SetHeadlessHeroAIEnabled(True, reset_runtime=reset_runtime)

    def DisableHeadlessHeroAI(self, reset_runtime: bool = True) -> None:
        self.SetHeadlessHeroAIEnabled(False, reset_runtime=reset_runtime)

    def ToggleHeadlessHeroAI(self, reset_runtime: bool = True) -> bool:
        new_state = not self.headless_heroai_enabled
        self.SetHeadlessHeroAIEnabled(new_state, reset_runtime=reset_runtime)
        return new_state

    def ApplyAccountIsolation(self) -> bool:
        account_email = Player.GetAccountEmail()
        if not account_email:
            return False

        changed = False
        current_isolated = bool(GLOBAL_CACHE.ShMem.IsAccountIsolated(account_email))
        if current_isolated != bool(self.isolation_enabled):
            changed = bool(GLOBAL_CACHE.ShMem.SetAccountIsolationByEmail(account_email, self.isolation_enabled)) or changed

        if self.isolation_enabled:
            target_group_id = self._resolve_isolation_group_id(account_email)
            current_group_id = int(GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(account_email) or 0)
            if current_group_id != target_group_id:
                changed = bool(GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(account_email, target_group_id)) or changed
            changed = self._sync_party_isolation_group(account_email, target_group_id) or changed
        else:
            current_group_id = int(GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(account_email) or 0)
            if current_group_id != 0:
                changed = bool(GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(account_email, 0)) or changed

        if changed:
            Py4GW.Console.Log(
                "BottingTree",
                f"Account isolation {'enabled' if self.isolation_enabled else 'disabled'} for {account_email}.",
                Py4GW.Console.MessageType.Info,
            )
        return bool(changed)

    def _resolve_isolation_group_id(self, account_email: str) -> int:
        import zlib

        account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if account is not None:
            existing_group_id = int(getattr(account, "IsolationGroupID", 0) or 0)
            if existing_group_id > 0:
                return existing_group_id
            party_id = int(getattr(account.AgentPartyData, "PartyID", 0) or 0)
            if party_id > 0:
                return party_id

        deterministic_group = int(zlib.crc32(str(account_email).encode("utf-8")) % 1_000_000)
        return max(1, deterministic_group)

    def _sync_party_isolation_group(self, account_email: str, group_id: int) -> bool:
        local_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if local_account is None:
            return False

        local_party_id = int(getattr(local_account.AgentPartyData, "PartyID", 0) or 0)
        if local_party_id <= 0:
            return False

        changed = False
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if not bool(getattr(account, "IsAccount", False)):
                continue

            other_email = str(getattr(account, "AccountEmail", "") or "").strip()
            if not other_email:
                continue

            other_party_id = int(getattr(account.AgentPartyData, "PartyID", 0) or 0)
            if other_party_id != local_party_id:
                continue

            other_group_id = int(getattr(account, "IsolationGroupID", 0) or 0)
            if other_group_id != group_id:
                changed = bool(GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(other_email, group_id)) or changed

            if not bool(getattr(account, "IsIsolated", False)):
                changed = bool(GLOBAL_CACHE.ShMem.SetAccountIsolationByEmail(other_email, True)) or changed

        return changed

    def _capture_isolation_state_for_restore(self) -> None:
        account_email = Player.GetAccountEmail()
        if not account_email:
            self._previous_isolation_state = None
            self._previous_isolation_group_id = None
            return
        self._previous_isolation_state = bool(GLOBAL_CACHE.ShMem.IsAccountIsolated(account_email))
        self._previous_isolation_group_id = int(GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(account_email) or 0)

    def RestoreAccountIsolation(self) -> bool:
        if not self._restore_isolation_on_stop:
            return False

        account_email = Player.GetAccountEmail()
        if not account_email or self._previous_isolation_state is None:
            return False

        changed = False
        current_isolated = bool(GLOBAL_CACHE.ShMem.IsAccountIsolated(account_email))
        if current_isolated != bool(self._previous_isolation_state):
            changed = bool(GLOBAL_CACHE.ShMem.SetAccountIsolationByEmail(
                account_email,
                self._previous_isolation_state,
            )) or changed

        restore_group_id = int(self._previous_isolation_group_id or 0)
        current_group_id = int(GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(account_email) or 0)
        if current_group_id != restore_group_id:
            changed = bool(GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(account_email, restore_group_id)) or changed

        if changed:
            Py4GW.Console.Log(
                "BottingTree",
                f"Account isolation restored to {'enabled' if self._previous_isolation_state else 'disabled'} for {account_email}.",
                Py4GW.Console.MessageType.Info,
            )
        self._previous_isolation_state = None
        self._previous_isolation_group_id = None
        return bool(changed)

    def SetIsolationEnabled(self, enabled: bool) -> bool:
        self.isolation_enabled = enabled
        return self.ApplyAccountIsolation()

    def EnableIsolation(self) -> bool:
        return self.SetIsolationEnabled(True)

    def DisableIsolation(self) -> bool:
        return self.SetIsolationEnabled(False)

    def ToggleIsolation(self) -> bool:
        self.isolation_enabled = not self.isolation_enabled
        self.ApplyAccountIsolation()
        return self.isolation_enabled

    def IsIsolationEnabled(self) -> bool:
        return self.isolation_enabled

    def SetRestoreIsolationOnStop(self, enabled: bool) -> None:
        self._restore_isolation_on_stop = enabled

    @staticmethod
    def GetIsolationSetEnabledTree(
        enabled: bool,
        name: str | None = None,
    ) -> BehaviorTree:
        node_name = name or ("EnableIsolation" if enabled else "DisableIsolation")

        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            node.blackboard["account_isolation_enabled_request"] = enabled
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=node_name,
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )

    @staticmethod
    def EnableIsolationTree() -> BehaviorTree:
        return BottingTree.GetIsolationSetEnabledTree(
            True,
            name="EnableIsolation",
        )

    @staticmethod
    def DisableIsolationTree() -> BehaviorTree:
        return BottingTree.GetIsolationSetEnabledTree(
            False,
            name="DisableIsolation",
        )

    @staticmethod
    def ToggleIsolationTree() -> BehaviorTree:
        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            current_enabled = bool(node.blackboard.get("account_isolation_enabled", True))
            node.blackboard["account_isolation_enabled_request"] = not current_enabled
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="ToggleIsolation",
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )

    @staticmethod
    def GetHeroAiSetEnabledTree(
        enabled: bool,
        reset_runtime: bool = True,
        name: str | None = None,
    ) -> BehaviorTree:
        node_name = name or ("EnableHeadlessHeroAI" if enabled else "DisableHeadlessHeroAI")

        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            node.blackboard["headless_heroai_enabled_request"] = enabled
            node.blackboard["headless_heroai_reset_runtime_request"] = reset_runtime
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=node_name,
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )

    @staticmethod
    def EnableHeroAITree(reset_runtime: bool = True) -> BehaviorTree:
        return BottingTree.GetHeroAiSetEnabledTree(
            True,
            reset_runtime=reset_runtime,
            name="EnableHeadlessHeroAI",
        )

    @staticmethod
    def DisableHeroAITree(reset_runtime: bool = True) -> BehaviorTree:
        return BottingTree.GetHeroAiSetEnabledTree(
            False,
            reset_runtime=reset_runtime,
            name="DisableHeadlessHeroAI",
        )

    @staticmethod
    def ToggleHeroAITree(reset_runtime: bool = True) -> BehaviorTree:
        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            current_enabled = bool(node.blackboard.get("headless_heroai_enabled", True))
            node.blackboard["headless_heroai_enabled_request"] = not current_enabled
            node.blackboard["headless_heroai_reset_runtime_request"] = reset_runtime
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="ToggleHeadlessHeroAI",
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )

    @staticmethod
    def GetLootingSetEnabledTree(
        enabled: bool,
        name: str | None = None,
    ) -> BehaviorTree:
        node_name = name or ("EnableLooting" if enabled else "DisableLooting")

        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            node.blackboard["looting_enabled_request"] = enabled
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=node_name,
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )

    @staticmethod
    def EnableLootingTree() -> BehaviorTree:
        return BottingTree.GetLootingSetEnabledTree(
            True,
            name="EnableLooting",
        )

    @staticmethod
    def DisableLootingTree() -> BehaviorTree:
        return BottingTree.GetLootingSetEnabledTree(
            False,
            name="DisableLooting",
        )

    @staticmethod
    def ToggleLootingTree() -> BehaviorTree:
        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            current_enabled = bool(node.blackboard.get("looting_enabled", True))
            node.blackboard["looting_enabled_request"] = not current_enabled
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="ToggleLooting",
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )
        
    def IsHeadlessHeroAIEnabled(self) -> bool:
        return self.headless_heroai_enabled

    def GetMoveData(self) -> dict:
        bb = self.blackboard
        path_points_raw = bb.get("move_path_points", [])
        path_points: list[tuple[float, float]] = []
        if isinstance(path_points_raw, list):
            for point in path_points_raw:
                if isinstance(point, tuple) and len(point) == 2:
                    path_points.append((float(point[0]), float(point[1])))

        current_waypoint_raw = bb.get("move_current_waypoint")
        current_waypoint: tuple[float, float] | None = None
        if isinstance(current_waypoint_raw, tuple) and len(current_waypoint_raw) == 2:
            current_waypoint = (float(current_waypoint_raw[0]), float(current_waypoint_raw[1]))

        target_raw = bb.get("move_target")
        move_target: tuple[float, float] | None = None
        if isinstance(target_raw, tuple) and len(target_raw) == 2:
            move_target = (float(target_raw[0]), float(target_raw[1]))

        last_move_point_raw = bb.get("move_last_move_point")
        last_move_point: tuple[float, float] | None = None
        if isinstance(last_move_point_raw, tuple) and len(last_move_point_raw) == 2:
            last_move_point = (float(last_move_point_raw[0]), float(last_move_point_raw[1]))

        return {
            "state": str(bb.get("move_state", "")),
            "reason": str(bb.get("move_reason", "")),
            "target": move_target,
            "path_points": path_points,
            "path_index": int(bb.get("move_path_index", 0) or 0),
            "path_count": int(bb.get("move_path_count", len(path_points)) or 0),
            "current_waypoint": current_waypoint,
            "current_waypoint_index": int(bb.get("move_current_waypoint_index", -1) or -1),
            "last_move_point": last_move_point,
            "resume_recovery_active": bool(bb.get("move_resume_recovery_active", False)),
        }

    #region DrawMovePath
    def SetMovePathDrawingEnabled(self, enabled: bool) -> None:
        self.draw_move_path_enabled = bool(enabled)

    def IsMovePathDrawingEnabled(self) -> bool:
        return bool(self.draw_move_path_enabled)

    def DrawMovePathDebugOptions(self, label: str = "Draw Move Path Debug Options") -> None:
        if PyImGui.collapsing_header(label):
            self.draw_move_path_enabled = PyImGui.checkbox(
                "Draw Move Path",
                self.draw_move_path_enabled,
            )
            self.draw_move_path_labels = PyImGui.checkbox(
                "Draw Path Labels",
                self.draw_move_path_labels,
            )
            self.draw_move_path_thickness = PyImGui.slider_float(
                "Path Thickness",
                self.draw_move_path_thickness,
                1.0,
                6.0,
            )
            self.draw_move_waypoint_radius = PyImGui.slider_float(
                "Waypoint Radius",
                self.draw_move_waypoint_radius,
                15.0,
                100.0,
            )
            self.draw_move_current_waypoint_radius = PyImGui.slider_float(
                "Current Waypoint Radius",
                self.draw_move_current_waypoint_radius,
                20.0,
                120.0,
            )

    def DrawMovePathIfEnabled(self) -> None:
        if not self.draw_move_path_enabled:
            return
        self.DrawMovePath(
            draw_labels=self.draw_move_path_labels,
            path_thickness=self.draw_move_path_thickness,
            waypoint_radius=self.draw_move_waypoint_radius,
            current_waypoint_radius=self.draw_move_current_waypoint_radius,
        )

    def DrawMovePath(
        self,
        draw_labels: bool = False,
        player_to_waypoint_color: Color = ColorPalette.GetColor("aqua"),
        remaining_path_color: Color = ColorPalette.GetColor("orange"),
        waypoint_color: Color = ColorPalette.GetColor("dodger_blue"),
        current_waypoint_color: Color = ColorPalette.GetColor("tomato"),
        player_marker_color: Color = ColorPalette.GetColor("white"),
        path_thickness: float = 4.0,
        waypoint_radius: float = 15.0,
        current_waypoint_radius: float = 20.0,
    ) -> None:
        move_data = self.GetMoveData()
        move_state = move_data["state"]
        path_points = move_data["path_points"]
        if move_state not in ("running", "paused") or not path_points:
            return

        path_index = move_data["path_index"]
        current_waypoint = move_data["current_waypoint"]
        player_x, player_y = Player.GetXY()
        overlay = Overlay()

        def _ground_z(x: float, y: float) -> float:
            return float(Overlay.FindZ(float(x), float(y)))

        def _is_visible(x: float, y: float) -> bool:
            return bool(GLOBAL_CACHE.Camera.IsPointInFOV(float(x), float(y)))

        def _draw_waypoint_marker(point_x: float, point_y: float, radius: float, color: int) -> None:
            if not _is_visible(point_x, point_y):
                return
            point_z = _ground_z(point_x, point_y)
            overlay.DrawPolyFilled3D(point_x, point_y, point_z, radius, color, 24)

        overlay.BeginDraw()
        try:
            if current_waypoint is not None:
                current_x, current_y = current_waypoint
                if _is_visible(player_x, player_y) and _is_visible(current_x, current_y):
                    overlay.DrawLine3D(
                        player_x,
                        player_y,
                        _ground_z(player_x, player_y),
                        current_x,
                        current_y,
                        _ground_z(current_x, current_y),
                        player_to_waypoint_color.to_color(),
                        path_thickness,
                    )

            start_index = max(0, min(path_index, len(path_points) - 1))
            for i in range(start_index, len(path_points) - 1):
                x1, y1 = path_points[i]
                x2, y2 = path_points[i + 1]
                if not (_is_visible(x1, y1) and _is_visible(x2, y2)):
                    continue
                overlay.DrawLine3D(
                    x1,
                    y1,
                    _ground_z(x1, y1),
                    x2,
                    y2,
                    _ground_z(x2, y2),
                    remaining_path_color.to_color(),
                    path_thickness,
                )

            for i, (point_x, point_y) in enumerate(path_points[start_index:], start=start_index):
                is_current = (i == move_data["current_waypoint_index"])
                marker_color = current_waypoint_color if is_current else waypoint_color
                marker_radius = current_waypoint_radius if is_current else waypoint_radius
                _draw_waypoint_marker(point_x, point_y, marker_radius, marker_color.to_color())
                if draw_labels and _is_visible(point_x, point_y):
                    point_z = _ground_z(point_x, point_y)
                    overlay.DrawText3D(point_x, point_y, point_z - 100.0, str(i), marker_color.to_color(), False, True, 2.0)

            if _is_visible(player_x, player_y):
                overlay.DrawPoly3D(player_x, player_y, _ground_z(player_x, player_y), waypoint_radius, player_marker_color.to_color(), 24, 2.0, False)
        finally:
            overlay.EndDraw()
         
    def Draw(self):
        self.tree.draw()

    def _tick_heroai(self, node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        bb = node.blackboard
        requested_isolation = bb.pop("account_isolation_enabled_request", None)
        if isinstance(requested_isolation, bool):
            self.SetIsolationEnabled(requested_isolation)
        bb["account_isolation_enabled"] = self.IsIsolationEnabled()

        requested_enabled = bb.pop("headless_heroai_enabled_request", None)
        requested_reset_runtime = bool(bb.pop("headless_heroai_reset_runtime_request", True))
        if isinstance(requested_enabled, bool):
            self.SetHeadlessHeroAIEnabled(requested_enabled, reset_runtime=requested_reset_runtime)
        bb["headless_heroai_enabled"] = self.IsHeadlessHeroAIEnabled()

        requested_looting_enabled = bb.pop("looting_enabled_request", None)
        if isinstance(requested_looting_enabled, bool):
            self.SetLootingEnabled(requested_looting_enabled)
        bb["looting_enabled"] = self.IsLootingEnabled()

        requested_pause_on_combat = bb.pop("pause_on_combat_request", None)
        if isinstance(requested_pause_on_combat, bool):
            self.pause_on_combat = requested_pause_on_combat
        bb["pause_on_combat"] = self.pause_on_combat

        if not self.started or self.paused:
            bb["COMBAT_ACTIVE"] = False
            bb["LOOTING_ACTIVE"] = False
            bb["PAUSE_MOVEMENT"] = False
            bb["HEROAI_SUCCESS"] = False
            return BehaviorTree.NodeState.RUNNING

        if not self.IsHeadlessHeroAIEnabled():
            if self._last_heroai_state != "disabled":
                Py4GW.Console.Log("BottingTree", "Headless HeroAI is disabled.", Py4GW.Console.MessageType.Info)
                self._last_heroai_state = "disabled"
            bb["COMBAT_ACTIVE"] = False
            bb["LOOTING_ACTIVE"] = False
            bb["PAUSE_MOVEMENT"] = False
            bb["HEROAI_STATUS"] = HeroAIStatus.DISABLED.value
            bb["HEROAI_SUCCESS"] = False
            self.headless_heroai.reset()
            return BehaviorTree.NodeState.RUNNING

        self.EnsureHeroAIOptionsEnabled()

        if Routines.Checks.Map.IsLoading() or not Routines.Checks.Map.IsExplorable():
            if self._last_heroai_state != "waiting_map":
                Py4GW.Console.Log("BottingTree", "HeroAI waiting for combat-ready map.", Py4GW.Console.MessageType.Info)
                self._last_heroai_state = "waiting_map"
            bb["COMBAT_ACTIVE"] = False
            bb["LOOTING_ACTIVE"] = False
            bb["PAUSE_MOVEMENT"] = False
            bb["HEROAI_STATUS"] = HeroAIStatus.WAITING_MAP.value
            bb["HEROAI_SUCCESS"] = False
            self.headless_heroai.reset()
            return BehaviorTree.NodeState.RUNNING

        if Routines.Checks.Player.IsDead():
            if self._last_heroai_state != "player_dead":
                Py4GW.Console.Log("BottingTree", "HeroAI paused because player is dead.", Py4GW.Console.MessageType.Warning)
                self._last_heroai_state = "player_dead"
            bb["COMBAT_ACTIVE"] = False
            bb["LOOTING_ACTIVE"] = False
            bb["PAUSE_MOVEMENT"] = False
            bb["HEROAI_STATUS"] = HeroAIStatus.PLAYER_DEAD.value
            bb["HEROAI_SUCCESS"] = False
            return BehaviorTree.NodeState.RUNNING

        if Routines.Checks.Player.IsKnockedDown():
            if self._last_heroai_state != "knocked_down":
                Py4GW.Console.Log("BottingTree", "HeroAI paused because player is knocked down.", Py4GW.Console.MessageType.Warning)
                self._last_heroai_state = "knocked_down"
            bb["COMBAT_ACTIVE"] = bool(self.headless_heroai.cached_data.data.in_aggro)
            bb["LOOTING_ACTIVE"] = False
            bb["PAUSE_MOVEMENT"] = False
            bb["HEROAI_STATUS"] = HeroAIStatus.PLAYER_KNOCKED_DOWN.value
            bb["HEROAI_SUCCESS"] = False
            return BehaviorTree.NodeState.RUNNING

        self.headless_heroai.tick()
        bb["USER_INTERRUPT_ACTIVE"] = self.headless_heroai.IsUserInterrupting()
        bb["LOOTING_ACTIVE"] = self.headless_heroai.IsLootingActive()
        bb["PAUSE_MOVEMENT"] = bool(bb["LOOTING_ACTIVE"] or bb["USER_INTERRUPT_ACTIVE"])

        if self.headless_heroai.cached_data.data.in_aggro:
            if self._last_heroai_state != "combat":
                self._last_heroai_state = "combat"
            bb["COMBAT_ACTIVE"] = True
            bb["HEROAI_STATUS"] = HeroAIStatus.COMBAT_TICK.value
        else:
            if self._last_heroai_state != "ooc":
                self._last_heroai_state = "ooc"
            bb["COMBAT_ACTIVE"] = False
            bb["HEROAI_STATUS"] = HeroAIStatus.OOC_TICK.value

        bb["HEROAI_SUCCESS"] = bool(self.headless_heroai.heroai_build.DidTickSucceed())
        return BehaviorTree.NodeState.RUNNING

    def _tick_planner(self, node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        bb = node.blackboard

        if not self.started or self.paused:
            bb["PLANNER_STATUS"] = PlannerStatus.IDLE.value
            bb["PLANNER_OWNER"] = PlannerStatus.OWNER_PLANNER.value
            return BehaviorTree.NodeState.RUNNING

        if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
            bb["PLANNER_STATUS"] = "PAUSED: Party wipe recovery"
            bb["PLANNER_OWNER"] = PlannerStatus.OWNER_PLANNER.value
            return BehaviorTree.NodeState.RUNNING

        if bb.get("COMBAT_ACTIVE", False) and self.pause_on_combat:
            if self._last_planner_gate_state != "paused_on_combat":
                self._last_planner_gate_state = "paused_on_combat"
            bb["PLANNER_STATUS"] = PlannerStatus.PAUSED_ON_COMBAT.value
            bb["PLANNER_OWNER"] = PlannerStatus.OWNER_HEROAI.value
        elif bb.get("LOOTING_ACTIVE", False):
            if self._last_planner_gate_state != "paused_on_looting":
                self._last_planner_gate_state = "paused_on_looting"
            bb["PLANNER_STATUS"] = PlannerStatus.PAUSED_ON_LOOTING.value
            bb["PLANNER_OWNER"] = PlannerStatus.OWNER_HEROAI.value

        if self.planner_tree is None:
            if self._last_planner_gate_state != "idle_no_planner":
                Py4GW.Console.Log("BottingTree", "Planner tree is not set; planner idling.", Py4GW.Console.MessageType.Warning)
                self._last_planner_gate_state = "idle_no_planner"
            bb["PLANNER_STATUS"] = PlannerStatus.IDLE.value
            bb["PLANNER_OWNER"] = PlannerStatus.OWNER_PLANNER.value
            return BehaviorTree.NodeState.RUNNING

        self._last_planner_gate_state = "planner_tick"
        bb["PLANNER_STATUS"] = PlannerStatus.TICK.value
        bb["PLANNER_OWNER"] = PlannerStatus.OWNER_PLANNER.value
        self.planner_tree.blackboard = bb
        planner_result = BehaviorTree.Node._normalize_state(self.planner_tree.tick())
        if planner_result is None:
            raise TypeError("Planner tree returned a non-NodeState result.")
        if planner_result == BehaviorTree.NodeState.SUCCESS:
            Py4GW.Console.Log("BottingTree", "Planner tree completed.", Py4GW.Console.MessageType.Success)
            bb["PLANNER_STATUS"] = "PLANNER: Completed"
            bb["PLANNER_OWNER"] = PlannerStatus.OWNER_PLANNER.value
            self.started = False
            self.paused = False
            self.RestoreAccountIsolation()
        elif planner_result == BehaviorTree.NodeState.FAILURE:
            Py4GW.Console.Log("BottingTree", "Planner tree failed.", Py4GW.Console.MessageType.Warning)
            bb["PLANNER_STATUS"] = "PLANNER: Failed"
            bb["PLANNER_OWNER"] = PlannerStatus.OWNER_PLANNER.value
            self.started = False
            self.paused = False
            self.RestoreAccountIsolation()
        return BehaviorTree.NodeState.RUNNING

    def _tick_service_tree(self, node: BehaviorTree.Node, service_tree: BehaviorTree, service_name: str) -> BehaviorTree.NodeState:
        if not self.started or self.paused:
            return BehaviorTree.NodeState.RUNNING

        service_tree.blackboard = node.blackboard
        service_result = BehaviorTree.Node._normalize_state(service_tree.tick())
        if service_result is None:
            raise TypeError(f"Service tree '{service_name}' returned a non-NodeState result.")
        if service_result in (BehaviorTree.NodeState.SUCCESS, BehaviorTree.NodeState.FAILURE):
            Py4GW.Console.Log(
                "BottingTree",
                f"Upkeep tree '{service_name}' returned {service_result.name}.",
                Py4GW.Console.MessageType.Info if service_result == BehaviorTree.NodeState.SUCCESS else Py4GW.Console.MessageType.Warning,
            )
        if service_result in (BehaviorTree.NodeState.SUCCESS, BehaviorTree.NodeState.FAILURE):
            service_tree.reset()
        return BehaviorTree.NodeState.RUNNING

    def _build_default_planner_tree(self) -> BehaviorTree:
        return BehaviorTree(
            root=BehaviorTree.ActionNode(
                name="DefaultPlannerTick",
                action_fn=lambda node: BehaviorTree.NodeState.RUNNING,
            )
        )

    def _build_parallel_tree(self) -> BehaviorTree:
        heroai_branch = BehaviorTree.RepeaterForeverNode(
            BehaviorTree.ActionNode(
                name="HeroAIServiceTick",
                action_fn=lambda node: self._tick_heroai(node),
            ),
            name="HeroAIService",
        )

        planner_branch = BehaviorTree.RepeaterForeverNode(
            BehaviorTree.ActionNode(
                name="PlannerServiceTick",
                action_fn=lambda node: self._tick_planner(node),
            ),
            name="PlannerService",
        )

        service_branches = [
            BehaviorTree.RepeaterForeverNode(
                BehaviorTree.ActionNode(
                    name=f"{service_name}Tick",
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
                name="Root",
            )
        )

    def ProcessRestartRequest(self) -> bool:
        restart_step_name = str(self.GetBlackboardValue("restart_step_name_request", "") or "")
        if not restart_step_name:
            return False

        self.ClearBlackboardValue("restart_step_name_request")
        self.ClearBlackboardValue("current_step_name")
        return self.RestartFromNamedPlannerStep(restart_step_name, auto_start=True)

    def tick(self):
        result = self.tree.tick()
        self.ProcessRestartRequest()
        return result


class _BottingTreeTemplates:
    def __init__(self, parent: BottingTree):
        self.parent = parent

    @staticmethod
    def _request_template_state(
        *,
        name: str,
        hero_ai: bool,
        looting: bool,
        isolation: bool,
        pause_on_combat: bool,
        reset_hero_ai: bool = True,
    ) -> BehaviorTree:
        state = {"requested": False}
        request_keys = (
            "headless_heroai_enabled_request",
            "headless_heroai_reset_runtime_request",
            "looting_enabled_request",
            "account_isolation_enabled_request",
            "pause_on_combat_request",
        )

        def _apply_template(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            if state["requested"]:
                if any(key in node.blackboard for key in request_keys):
                    return BehaviorTree.NodeState.RUNNING
                state["requested"] = False
                return BehaviorTree.NodeState.SUCCESS

            node.blackboard["headless_heroai_enabled_request"] = bool(hero_ai)
            node.blackboard["headless_heroai_reset_runtime_request"] = bool(reset_hero_ai)
            node.blackboard["looting_enabled_request"] = bool(looting)
            node.blackboard["account_isolation_enabled_request"] = bool(isolation)
            node.blackboard["pause_on_combat_request"] = bool(pause_on_combat)
            node.blackboard["botting_tree_template"] = name
            state["requested"] = True
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=name,
                action_fn=_apply_template,
                aftercast_ms=0,
            )
        )

    @staticmethod
    def PacifistTree(
        *,
        account_isolation: bool = True,
        reset_hero_ai: bool = True,
        name: str = "ConfigurePacifistEnv",
    ) -> BehaviorTree:
        return _BottingTreeTemplates._request_template_state(
            name=name,
            hero_ai=False,
            looting=False,
            isolation=account_isolation,
            pause_on_combat=False,
            reset_hero_ai=reset_hero_ai,
        )

    @staticmethod
    def PacifistForceHeroAITree(
        *,
        reset_hero_ai: bool = True,
        name: str = "ConfigurePacifistForceHeroAIEnv",
    ) -> BehaviorTree:
        return _BottingTreeTemplates.PacifistTree(
            account_isolation=False,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    @staticmethod
    def AggressiveTree(
        *,
        pause_on_danger: bool = True,
        account_isolation: bool = True,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = "ConfigureAggressiveEnv",
    ) -> BehaviorTree:
        return _BottingTreeTemplates._request_template_state(
            name=name,
            hero_ai=True,
            looting=auto_loot,
            isolation=account_isolation,
            pause_on_combat=pause_on_danger,
            reset_hero_ai=reset_hero_ai,
        )

    @staticmethod
    def AggressiveForceHeroAITree(
        *,
        pause_on_danger: bool = True,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = "ConfigureAggressiveForceHeroAIEnv",
    ) -> BehaviorTree:
        return _BottingTreeTemplates.AggressiveTree(
            pause_on_danger=pause_on_danger,
            account_isolation=False,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    @staticmethod
    def MultiboxAggressiveTree(
        *,
        auto_loot: bool = True,
        reset_hero_ai: bool = True,
        name: str = "ConfigureMultiboxAggressiveEnv",
    ) -> BehaviorTree:
        return _BottingTreeTemplates.AggressiveTree(
            pause_on_danger=True,
            account_isolation=False,
            auto_loot=auto_loot,
            reset_hero_ai=reset_hero_ai,
            name=name,
        )

    def Pacifist(self, **kwargs) -> BehaviorTree:
        return self.PacifistTree(**kwargs)

    def PacifistForceHeroAI(self, **kwargs) -> BehaviorTree:
        return self.PacifistForceHeroAITree(**kwargs)

    def Aggressive(self, **kwargs) -> BehaviorTree:
        return self.AggressiveTree(**kwargs)

    def AggressiveForceHeroAI(self, **kwargs) -> BehaviorTree:
        return self.AggressiveForceHeroAITree(**kwargs)

    def Multibox_Aggressive(self, **kwargs) -> BehaviorTree:
        return self.MultiboxAggressiveTree(**kwargs)

    ConfigurePacifistEnv = Pacifist
    ConfigureAggressiveEnv = Aggressive


BottingTreeTemplates = _BottingTreeTemplates


class _BottingTreeUI:
    def __init__(self, parent: BottingTree):
        self.parent = parent
        self.draw_texture_fn: Callable[[], None] | None = None
        self.draw_config_fn: Callable[[], None] | None = None
        self.draw_help_fn: Callable[[], None] | None = None
        self._selected_start_index = 0
        self._show_tree = True
        self._debug_console_height = 200.0

    def override_draw_texture(self, draw_fn: Callable[[], None] | None = None) -> None:
        self.draw_texture_fn = draw_fn

    def override_draw_config(self, draw_fn: Callable[[], None] | None = None) -> None:
        self.draw_config_fn = draw_fn

    def override_draw_help(self, draw_fn: Callable[[], None] | None = None) -> None:
        self.draw_help_fn = draw_fn

    def PrintMessageToConsole(self, source: str, message: str) -> None:
        Py4GW.Console.Log(source, message, Py4GW.Console.MessageType.Info)

    def _draw_texture(self, icon_path: str = "", size: tuple[float, float] = (96.0, 96.0)) -> None:
        if self.draw_texture_fn is not None:
            self.draw_texture_fn()
            return
        if not icon_path:
            return

        try:
            from .ImGui import ImGui

            ImGui.DrawTextureExtended(
                texture_path=icon_path,
                size=size,
                uv0=(0.0, 0.0),
                uv1=(1.0, 1.0),
                tint=(255, 255, 255, 255),
                border_color=(0, 0, 0, 0),
            )
        except Exception:
            PyImGui.text(icon_path)

    def _colored_bool(self, label: str, value: bool) -> None:
        color = (0, 255, 0, 255) if value else (255, 80, 80, 255)
        PyImGui.text_colored(f"{label}: {value}", color)

    def _current_step_name(self) -> str:
        current_step_name = str(self.parent.GetBlackboardValue("current_step_name", "") or "")
        if current_step_name:
            return current_step_name
        planner_status = str(self.parent.GetBlackboardValue("PLANNER_STATUS", "") or "")
        return planner_status or "Idle"

    def _draw_main_child(
        self,
        main_child_dimensions: tuple[int, int] = (350, 275),
        icon_path: str = "",
        iconwidth: int = 96,
    ) -> None:
        if PyImGui.begin_table("botting_tree_header_table", 2, PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersOuterH):
            PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, iconwidth)
            PyImGui.table_setup_column("Status", PyImGui.TableColumnFlags.WidthFixed, main_child_dimensions[0] - iconwidth)
            PyImGui.table_next_row()
            PyImGui.table_set_column_index(0)
            self._draw_texture(icon_path, (float(iconwidth), float(iconwidth)))
            PyImGui.table_set_column_index(1)
            PyImGui.text(self.parent.bot_name)
            PyImGui.text(f"Current: {self._current_step_name()}")
            PyImGui.text(f"HeroAI: {self.parent.GetBlackboardValue('HEROAI_STATUS', 'Idle')}")
            PyImGui.text(f"Planner: {self.parent.GetBlackboardValue('PLANNER_STATUS', 'Idle')}")
            PyImGui.end_table()

        if self.parent.IsStarted():
            if PyImGui.button("Stop##BottingTreeStop"):
                self.parent.Stop()
            PyImGui.same_line(0, -1)
            if self.parent.IsPaused():
                if PyImGui.button("Resume##BottingTreePause"):
                    self.parent.Pause(False)
            else:
                if PyImGui.button("Pause##BottingTreePause"):
                    self.parent.Pause(True)
        else:
            step_names = self.parent.GetNamedPlannerStepNames()
            if step_names:
                self._selected_start_index = max(0, min(self._selected_start_index, len(step_names) - 1))
                self._selected_start_index = PyImGui.combo("Start At", self._selected_start_index, step_names)
                if PyImGui.button("Start##BottingTreeStart"):
                    self.parent.RestartFromNamedPlannerStep(step_names[self._selected_start_index], auto_start=True)
            else:
                if PyImGui.button("Start##BottingTreeStart"):
                    self.parent.Start()

        PyImGui.separator()
        self._colored_bool("Started", self.parent.IsStarted())
        self._colored_bool("Paused", self.parent.IsPaused())
        self._colored_bool("Headless HeroAI", self.parent.IsHeadlessHeroAIEnabled())
        self._colored_bool("Looting", self.parent.IsLootingEnabled())
        self._colored_bool("Account Isolation", self.parent.IsIsolationEnabled())
        self._colored_bool("Combat Active", bool(self.parent.GetBlackboardValue("COMBAT_ACTIVE", False)))
        self._colored_bool("Looting Active", bool(self.parent.GetBlackboardValue("LOOTING_ACTIVE", False)))

    def _draw_navigation_child(self, child_size: tuple[int, int] = (350, 275)) -> None:
        step_names = self.parent.GetNamedPlannerStepNames()
        if not step_names:
            PyImGui.text("No named planner steps configured.")
            return

        self._selected_start_index = max(0, min(self._selected_start_index, len(step_names) - 1))
        self._selected_start_index = PyImGui.combo("Restart From", self._selected_start_index, step_names)
        if PyImGui.button("Restart Selected"):
            self.parent.RestartFromNamedPlannerStep(step_names[self._selected_start_index], auto_start=True)

        PyImGui.separator()
        if PyImGui.begin_child("BottingTreeNamedSteps", child_size, True, PyImGui.WindowFlags.HorizontalScrollbar):
            for index, step_name in enumerate(step_names):
                marker = ">" if index == self._selected_start_index else " "
                PyImGui.text(f"{marker} {index}: {step_name}")
        PyImGui.end_child()

    def _draw_settings_child(self) -> None:
        if self.draw_config_fn is not None:
            self.draw_config_fn()
            return

        self.parent.pause_on_combat = PyImGui.checkbox("Pause Planner On Combat", self.parent.pause_on_combat)
        headless_heroai_enabled = PyImGui.checkbox("Headless HeroAI", self.parent.IsHeadlessHeroAIEnabled())
        if headless_heroai_enabled != self.parent.IsHeadlessHeroAIEnabled():
            self.parent.SetHeadlessHeroAIEnabled(headless_heroai_enabled, reset_runtime=False)

        looting_enabled = PyImGui.checkbox("Looting", self.parent.IsLootingEnabled())
        if looting_enabled != self.parent.IsLootingEnabled():
            self.parent.SetLootingEnabled(looting_enabled)

        isolation_enabled = PyImGui.checkbox("Account Isolation", self.parent.IsIsolationEnabled())
        if isolation_enabled != self.parent.IsIsolationEnabled():
            self.parent.SetIsolationEnabled(isolation_enabled)
        PyImGui.separator()
        self.parent.DrawMovePathDebugOptions()

    def _draw_help_child(self) -> None:
        if self.draw_help_fn is not None:
            self.draw_help_fn()
            return

        PyImGui.text("BottingTree default UI")
        PyImGui.separator()
        PyImGui.text("Use SetMainRoutine(...) with a BehaviorTree, node, callable, child list, or named step list.")
        PyImGui.text("Call tick() every frame, then draw_window(...).")

    def draw_debug_window(self) -> None:
        if PyImGui.collapsing_header("Runtime"):
            PyImGui.text(f"HeroAI Status: {self.parent.GetBlackboardValue('HEROAI_STATUS', '')}")
            PyImGui.text(f"Planner Status: {self.parent.GetBlackboardValue('PLANNER_STATUS', '')}")
            PyImGui.text(f"Last UI Log: {self.parent.GetDebugConsoleLastMessage()}")

        if PyImGui.collapsing_header("Blackboard"):
            for key in sorted(self.parent.blackboard.keys()):
                value = self.parent.blackboard.get(key)
                PyImGui.text_wrapped(f"{key}: {value}")

        if PyImGui.collapsing_header("Debug Console"):
            self.parent.DrawDebugConsole(height=self._debug_console_height)

        if PyImGui.collapsing_header("Behavior Tree"):
            self._show_tree = PyImGui.checkbox("Show Tree", self._show_tree)
            if self._show_tree:
                self.parent.Draw()

    def draw_window(
        self,
        main_child_dimensions: tuple[int, int] = (350, 275),
        icon_path: str = "",
        iconwidth: int = 96,
        additional_ui: Callable[[], None] | None = None,
        extra_tabs: list[tuple[str, Callable[[], None]]] | None = None,
    ) -> bool:
        if PyImGui.begin(self.parent.bot_name, PyImGui.WindowFlags.AlwaysAutoResize):
            if PyImGui.begin_tab_bar(self.parent.bot_name + "_tabs"):
                if PyImGui.begin_tab_item("Main"):
                    if PyImGui.begin_child(f"{self.parent.bot_name} - Main", main_child_dimensions, True, PyImGui.WindowFlags.NoFlag):
                        self._draw_main_child(main_child_dimensions, icon_path, iconwidth)
                        if additional_ui is not None:
                            PyImGui.separator()
                            additional_ui()
                    PyImGui.end_child()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Navigation"):
                    self._draw_navigation_child(main_child_dimensions)
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Settings"):
                    self._draw_settings_child()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Help"):
                    self._draw_help_child()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Debug"):
                    self.draw_debug_window()
                    PyImGui.end_tab_item()

                if extra_tabs:
                    for tab_label, tab_draw_fn in extra_tabs:
                        if PyImGui.begin_tab_item(tab_label):
                            if callable(tab_draw_fn):
                                tab_draw_fn()
                            PyImGui.end_tab_item()

                PyImGui.end_tab_bar()
        PyImGui.end()
        self.parent.DrawMovePathIfEnabled()
        return True

    DrawWindow = draw_window
    DrawDebugWindow = draw_debug_window
