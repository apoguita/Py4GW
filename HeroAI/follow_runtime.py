from __future__ import annotations

import random
from dataclasses import dataclass

from Py4GWCoreLib import ActionQueueManager, GLOBAL_CACHE, Utils, Weapon
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

    def _cached_xy(account) -> tuple[float, float]:
        return (float(account.AgentData.Pos.x), float(account.AgentData.Pos.y))

    def _cached_ally_positions(own_agent_id: int) -> list[tuple[float, float]]:
        positions: list[tuple[float, float]] = []
        for account in cached_data.party:
            agent_id = int(account.AgentData.AgentID)
            if agent_id == 0 or agent_id == own_agent_id:
                continue
            if not bool(account.IsSlotActive):
                continue
            positions.append(_cached_xy(account))
        return positions

    options = cached_data.account_options
    if not options or not options.Following:
        return BehaviorTree.NodeState.FAILURE

    if not cached_data.follow_throttle_timer.IsExpired():
        return BehaviorTree.NodeState.FAILURE

    if Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID():
        cached_data.follow_throttle_timer.Reset()
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
    leader_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(0)
    all_flag_active = (
        leader_options is not None
        and bool(getattr(leader_options, "IsFlagged", False))
        and _is_nonzero_xy(float(leader_options.AllFlag.x), float(leader_options.AllFlag.y))
    )

    follow_threshold_raw = float(options.FollowMoveThreshold)
    combat_threshold_raw = float(options.FollowMoveThresholdCombat)

    if own_flag_active:
        follow_x = float(options.FlagPos.x)
        follow_y = float(options.FlagPos.y)
        follow_z = 0
    else:
        if follow_threshold_raw < 0.0 and combat_threshold_raw < 0.0:
            return BehaviorTree.NodeState.FAILURE
        follow_x = float(options.FollowPos.x)
        follow_y = float(options.FollowPos.y)
        follow_z = int(float(options.FollowPos.z))

    party_in_aggro = bool(getattr(cached_data.data, "party_in_aggro", cached_data.data.in_aggro))
    is_melee = cached_data.data.weapon_type in {
        Weapon.Axe.value,
        Weapon.Hammer.value,
        Weapon.Daggers.value,
        Weapon.Scythe.value,
        Weapon.Sword.value,
    }

    if party_in_aggro and is_melee:
        state.last_follow_move_point = None
        cached_data.follow_throttle_timer.Reset()
        return BehaviorTree.NodeState.FAILURE

    if party_in_aggro:
        if combat_threshold_raw >= 0.0:
            follow_distance = max(0.0, combat_threshold_raw)
        else:
            follow_distance = max(0.0, follow_threshold_raw)
    else:
        follow_distance = max(0.0, follow_threshold_raw)

    avoidance_enabled = bool(options.Avoidance)
    if (
        (not party_in_aggro or follow_z != 0 or not avoidance_enabled)
        and Utils.Distance((follow_x, follow_y), Player.GetXY()) <= follow_distance
    ):
        return BehaviorTree.NodeState.FAILURE

    xx = follow_x
    yy = follow_y

    if party_in_aggro and follow_z == 0 and avoidance_enabled:
        own_account = cached_data.account_data
        own_agent_id = int(own_account.AgentData.AgentID)
        if own_agent_id == 0:
            return BehaviorTree.NodeState.FAILURE
        mixed_target = compute_mixed_follow_target(
            current_pos=_cached_xy(own_account),
            assigned_pos=(follow_x, follow_y),
            follow_distance=follow_distance,
            in_combat=True,
            config=load_follow_movement_config(),
            ally_positions=_cached_ally_positions(own_agent_id),
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
    if follow_z == 0:
        Player.Move(xx, yy)
    else:
        ActionQueueManager().AddAction("ACTION", UIManager.Keypress, ControlAction.ControlAction_TargetPartyMember1.value, 0)
        ActionQueueManager().AddAction("ACTION", UIManager.Keypress, ControlAction.ControlAction_Follow.value, 0)

    state.last_follow_move_point = (xx, yy)

    cached_data.follow_throttle_timer.Reset()
    if party_in_aggro and is_melee:
        return BehaviorTree.NodeState.SUCCESS
    return BehaviorTree.NodeState.FAILURE
