from __future__ import annotations

import random
from dataclasses import dataclass

from Py4GWCoreLib import ActionQueueManager, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.UI_enums import ControlAction
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

from .cache_data import CacheData
from .follow_movement import compute_mixed_follow_target, load_follow_movement_config


@dataclass(slots=True)
class FollowExecutionState:
    last_follow_move_point: tuple[float, float] | None = None
    follow_map_entry_signature: tuple[int, int, int, int] | None = None


def execute_follower_follow(
    cached_data: CacheData,
    state: FollowExecutionState,
) -> BehaviorTree.NodeState:
    def _is_nonzero_xy(x: float, y: float) -> bool:
        return abs(float(x)) > 0.001 or abs(float(y)) > 0.001

    def _has_valid_point(x: float, y: float) -> bool:
        return abs(float(x)) > 0.001 or abs(float(y)) > 0.001

    options = cached_data.account_options
    if not options or not options.Following:
        return BehaviorTree.NodeState.FAILURE

    combat_handler = getattr(cached_data, "combat_handler", None)
    if (
        (combat_handler is not None and combat_handler.InCastingRoutine())
        or GLOBAL_CACHE.SkillBar.GetCasting() != 0
    ):
        return BehaviorTree.NodeState.FAILURE

    if not cached_data.follow_throttle_timer.IsExpired():
        return BehaviorTree.NodeState.FAILURE

    if Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
        cached_data.follow_throttle_timer.Reset()
        return BehaviorTree.NodeState.FAILURE

    if not Agent.CanAct(Player.GetAgentID()):
        return BehaviorTree.NodeState.FAILURE

    map_sig = (
        int(Map.GetMapID()),
        int(Map.GetRegion()[0]),
        int(Map.GetDistrict()),
        int(Map.GetLanguage()[0]),
    )
    if state.follow_map_entry_signature != map_sig:
        state.follow_map_entry_signature = map_sig
        state.last_follow_move_point = None

    own_flag_active = bool(getattr(options, "IsFlagged", False)) and _is_nonzero_xy(
        float(options.FlagPos.x),
        float(options.FlagPos.y),
    )

    follow_threshold_raw = float(options.FollowMoveThreshold)
    combat_threshold_raw = float(options.FollowMoveThresholdCombat)

    if own_flag_active:
        follow_x = float(options.FlagPos.x)
        follow_y = float(options.FlagPos.y)
        follow_z = int(float(options.FollowPos.z))
    else:
        if not bool(getattr(options, "LeaderFollowReady", False)):
            return BehaviorTree.NodeState.FAILURE
        if follow_threshold_raw < 0.0 and combat_threshold_raw < 0.0:
            return BehaviorTree.NodeState.FAILURE
        follow_x = float(options.FollowPos.x)
        follow_y = float(options.FollowPos.y)
        follow_z = int(float(options.FollowPos.z))

    if not _has_valid_point(follow_x, follow_y):
        return BehaviorTree.NodeState.FAILURE

    if cached_data.data.in_aggro:
        if combat_threshold_raw >= 0.0:
            follow_distance = max(0.0, combat_threshold_raw)
        else:
            follow_distance = max(0.0, follow_threshold_raw)
    else:
        follow_distance = max(0.0, follow_threshold_raw)

    if follow_z != 0:
        ActionQueueManager().ResetQueue("ACTION")
        ActionQueueManager().AddAction("ACTION", UIManager.Keypress, ControlAction.ControlAction_TargetPartyMember1.value, 0)
        ActionQueueManager().AddAction("ACTION", UIManager.Keypress, ControlAction.ControlAction_Follow.value, 0)
        state.last_follow_move_point = None
        cached_data.follow_throttle_timer.Reset()
        return BehaviorTree.NodeState.SUCCESS

    current_pos = Player.GetXY()
    if current_pos is None:
        return BehaviorTree.NodeState.FAILURE

    mixed_target = compute_mixed_follow_target(
        current_pos=current_pos,
        assigned_pos=(follow_x, follow_y),
        follow_distance=follow_distance,
        in_combat=bool(cached_data.data.in_aggro),
        config=load_follow_movement_config(),
    )
    if mixed_target is None:
        return BehaviorTree.NodeState.FAILURE

    xx, yy = mixed_target
    if state.last_follow_move_point is not None:
        last_x, last_y = state.last_follow_move_point
        if abs(xx - last_x) <= 10 and abs(yy - last_y) <= 10:
            xx += random.uniform(-5.0, 5.0)
            yy += random.uniform(-5.0, 5.0)

    ActionQueueManager().ResetQueue("ACTION")
    Player.Move(xx, yy)
    state.last_follow_move_point = (xx, yy)

    cached_data.follow_throttle_timer.Reset()
    return BehaviorTree.NodeState.SUCCESS
