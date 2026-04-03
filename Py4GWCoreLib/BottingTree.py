from enum import Enum
from typing import Callable, Sequence, cast

import Py4GW
import PyImGui
from HeroAI.headless_tree import HeroAIHeadlessTree

from .GlobalCache import GLOBAL_CACHE
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

    def __init__(self, ini_key: str, pause_on_combat: bool = True, isolation_enabled: bool = True):
        self.ini_key = ini_key
        self.pause_on_combat = pause_on_combat
        self.isolation_enabled = isolation_enabled
        self._restore_isolation_on_stop = True
        self._previous_isolation_state: bool | None = None
        self.headless_heroai = HeroAIHeadlessTree()
        self.headless_heroai_enabled = True
        self._planner_steps: list[tuple[str, Callable[[], object] | object]] = []
        self._planner_sequence_name = "PlannerSequence"
        self._service_steps: list[tuple[str, Callable[[], object] | object]] = []
        self._service_trees: list[tuple[str, BehaviorTree]] = []
        self.planner_tree = self._build_default_planner_tree()
        self.tree = self._build_parallel_tree()
        self._last_planner_gate_state = None
        self._last_heroai_state = None
        self.started = False
        self.paused = False

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
        value = self.blackboard.get("last_log_message", "")
        return value if isinstance(value, str) else ""

    def GetLastBlackboardLogData(self) -> dict:
        value = self.blackboard.get("last_log_message_data", {})
        return value if isinstance(value, dict) else {}

    def GetBlackboardLogHistory(self) -> list[str]:
        value = self.blackboard.get("blackboard_log_history", [])
        if not isinstance(value, list):
            return []
        return [entry for entry in value if isinstance(entry, str)]

    def ClearBlackboardLog(self) -> None:
        self.blackboard.pop("last_log_message", None)
        self.blackboard.pop("last_log_message_data", None)

    def ClearBlackboardLogHistory(self) -> None:
        self.blackboard.pop("blackboard_log_history", None)
    
    def Start(self):
        self.Reset()
        self._capture_isolation_state_for_restore()
        self.ApplyAccountIsolation()
        self.started = True
        self.paused = False
        Py4GW.Console.Log("BottingTree", "Botting tree started.", Py4GW.Console.MessageType.Info)
            
    def Stop(self):
        if self.started:
            self.started = False
            self.paused = False
            self.RestoreAccountIsolation()
            self.Reset()
            Py4GW.Console.Log("BottingTree", "Botting tree stopped and reset.", Py4GW.Console.MessageType.Info)

    def Reset(self):
        self.tree.reset()
        self.planner_tree.reset()
        self.headless_heroai.reset()
        for _, service_tree in self._service_trees:
            service_tree.reset()
        self.tree.blackboard.clear()
        self._last_planner_gate_state = None
        self._last_heroai_state = None
            
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
            

    def SetPlannerTree(self, planner_tree: BehaviorTree | None):
        self.planner_tree = planner_tree or self._build_default_planner_tree()

    def _rebuild_root_tree(self):
        blackboard = dict(self.tree.blackboard) if hasattr(self, "tree") and self.tree is not None else {}
        self.tree = self._build_parallel_tree()
        self.tree.blackboard.update(blackboard)

    def _build_named_planner_tree(
        self,
        steps: Sequence[tuple[str, Callable[[], object] | object]],
        start_from: str | None = None,
        name: str = "PlannerSequence",
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

        children = [
            BehaviorTree.SubtreeNode(
                name=step_name,
                subtree_fn=lambda node, subtree_or_builder=subtree_or_builder: _as_tree(subtree_or_builder),
            )
            for step_name, subtree_or_builder in steps[start_index:]
        ]
        return BehaviorTree(BehaviorTree.SequenceNode(name=name, children=children))

    def SetNamedPlannerSteps(
        self,
        steps: Sequence[tuple[str, Callable[[], object] | object]],
        start_from: str | None = None,
        name: str = "PlannerSequence",
    ):
        self._planner_steps = list(steps)
        self._planner_sequence_name = name
        self.SetPlannerTree(self._build_named_planner_tree(self._planner_steps, start_from=start_from, name=name))

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
        self.SetPlannerTree(self._build_named_planner_tree(self._planner_steps, start_from=step_name, name=sequence_name))
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

        changed = GLOBAL_CACHE.ShMem.SetAccountIsolationByEmail(account_email, self.isolation_enabled)
        if changed:
            Py4GW.Console.Log(
                "BottingTree",
                f"Account isolation {'enabled' if self.isolation_enabled else 'disabled'} for {account_email}.",
                Py4GW.Console.MessageType.Info,
            )
        return bool(changed)

    def _capture_isolation_state_for_restore(self) -> None:
        account_email = Player.GetAccountEmail()
        if not account_email:
            self._previous_isolation_state = None
            return
        self._previous_isolation_state = bool(GLOBAL_CACHE.ShMem.IsAccountIsolated(account_email))

    def RestoreAccountIsolation(self) -> bool:
        if not self._restore_isolation_on_stop:
            return False

        account_email = Player.GetAccountEmail()
        if not account_email or self._previous_isolation_state is None:
            return False

        changed = GLOBAL_CACHE.ShMem.SetAccountIsolationByEmail(
            account_email,
            self._previous_isolation_state,
        )
        if changed:
            Py4GW.Console.Log(
                "BottingTree",
                f"Account isolation restored to {'enabled' if self._previous_isolation_state else 'disabled'} for {account_email}.",
                Py4GW.Console.MessageType.Info,
            )
        self._previous_isolation_state = None
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

    def tick(self):
        if not self.started or self.paused:
            return
        return self.tree.tick()
