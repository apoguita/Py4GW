from __future__ import annotations

from dataclasses import dataclass

from Py4GWCoreLib import ActionQueueManager, Agent, GLOBAL_CACHE, Range, Utils, Weapon
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.UI_enums import ControlAction
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

from ..cache_data import CacheData


@dataclass(slots=True)
class FollowExecutionState:
    last_follow_move_point: tuple[float, float] | None = None
    last_follow_assigned_point: tuple[float, float, int] | None = None
    follow_map_entry_signature: tuple[int, int, int, int, int] | None = None
    last_leader_publish_signature: tuple[int, int, int, int, int] | None = None


def execute_follower_follow(
    cached_data: CacheData,
    state: FollowExecutionState,
) -> BehaviorTree.NodeState:
    def _is_nonzero_xy(x: float, y: float) -> bool:
        return abs(float(x)) > 0.001 or abs(float(y)) > 0.001

    def _reset_follow_runtime() -> None:
        state.last_follow_move_point = None
        state.last_follow_assigned_point = None

    def _account_map_signature(account) -> tuple[int, int, int, int, int] | None:
        if account is None or not bool(getattr(account, "IsSlotActive", False)):
            return None
        return (
            int(account.AgentData.Map.MapID),
            int(account.AgentData.Map.Region),
            int(account.AgentData.Map.District),
            int(account.AgentData.Map.Language),
            int(account.AgentPartyData.PartyID),
        )

    def _assigned_point_changed(
        previous: tuple[float, float, int] | None,
        current: tuple[float, float, int],
        refresh_distance: float,
    ) -> bool:
        if previous is None:
            return True
        previous_x, previous_y, previous_z = previous
        current_x, current_y, current_z = current
        if previous_z != current_z:
            return True
        return Utils.Distance((previous_x, previous_y), (current_x, current_y)) > refresh_distance

    options = cached_data.account_options
    if not options or not options.Following:
        return BehaviorTree.NodeState.FAILURE

    if not cached_data.follow_throttle_timer.IsExpired():
        return BehaviorTree.NodeState.FAILURE

    player_agent_id = int(Player.GetAgentID())
    if player_agent_id == GLOBAL_CACHE.Party.GetPartyLeaderID():
        cached_data.follow_throttle_timer.Reset()
        return BehaviorTree.NodeState.FAILURE

    if Agent.IsCasting(player_agent_id):
        return BehaviorTree.NodeState.FAILURE

    map_sig = (
        int(Map.GetMapID()),
        int(Map.GetRegion()[0]),
        int(Map.GetDistrict()),
        int(Map.GetLanguage()[0]),
        int(cached_data.account_data.AgentPartyData.PartyID),
    )
    if state.follow_map_entry_signature != map_sig:
        state.follow_map_entry_signature = map_sig
        state.last_leader_publish_signature = None
        _reset_follow_runtime()

    own_flag_active = bool(getattr(options, "IsFlagged", False)) and _is_nonzero_xy(
        float(options.FlagPos.x),
        float(options.FlagPos.y),
    )
    leader_account = GLOBAL_CACHE.ShMem.GetAccountDataFromPartyNumber(0)
    leader_publish_signature = _account_map_signature(leader_account)
    leader_signature_matches_local = leader_publish_signature == map_sig
    if state.last_leader_publish_signature != leader_publish_signature:
        state.last_leader_publish_signature = leader_publish_signature
        _reset_follow_runtime()

    leader_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsByPartyNumber(0)
    all_flag_active = (
        leader_signature_matches_local
        and
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
        if not bool(getattr(options, "LeaderFollowReady", False)):
            _reset_follow_runtime()
            return BehaviorTree.NodeState.FAILURE
        if not leader_signature_matches_local:
            _reset_follow_runtime()
            return BehaviorTree.NodeState.FAILURE
        if follow_threshold_raw < 0.0 and combat_threshold_raw < 0.0:
            _reset_follow_runtime()
            return BehaviorTree.NodeState.FAILURE
        follow_x = float(options.FollowPos.x)
        follow_y = float(options.FollowPos.y)
        follow_z = int(float(options.FollowPos.z))
        if (not _is_nonzero_xy(follow_x, follow_y)) and follow_z == 0:
            _reset_follow_runtime()
            return BehaviorTree.NodeState.FAILURE

    combat_active = bool(cached_data.data.in_aggro)
    is_melee = cached_data.data.weapon_type in {
        Weapon.Axe.value,
        Weapon.Hammer.value,
        Weapon.Daggers.value,
        Weapon.Scythe.value,
        Weapon.Sword.value,
    }

    if combat_active:
        if combat_threshold_raw >= 0.0:
            follow_distance = max(0.0, combat_threshold_raw)
        else:
            follow_distance = max(0.0, follow_threshold_raw)
    else:
        follow_distance = max(0.0, follow_threshold_raw)

    if combat_active and is_melee and not own_flag_active and not all_flag_active:
        melee_leash_distance = max(follow_distance, float(Range.Spellcast.value))
        if Utils.Distance((follow_x, follow_y), Player.GetXY()) <= melee_leash_distance:
            cached_data.follow_throttle_timer.Reset()
            return BehaviorTree.NodeState.FAILURE

    assigned_point = (follow_x, follow_y, follow_z)
    destination_refresh_distance = max(25.0, min(150.0, follow_distance * 0.25))
    assigned_changed = _assigned_point_changed(
        state.last_follow_assigned_point,
        assigned_point,
        destination_refresh_distance,
    )
    if assigned_changed:
        state.last_follow_move_point = None
    state.last_follow_assigned_point = assigned_point

    if Utils.Distance((follow_x, follow_y), Player.GetXY()) <= follow_distance:
        return BehaviorTree.NodeState.FAILURE

    xx = follow_x
    yy = follow_y

    if not assigned_changed and state.last_follow_move_point is not None:
        last_x, last_y = state.last_follow_move_point
        if Utils.Distance((last_x, last_y), (xx, yy)) <= 10.0:
            return BehaviorTree.NodeState.FAILURE

    if not ActionQueueManager().IsEmpty("ACTION"):
        return BehaviorTree.NodeState.FAILURE

    if follow_z == 0:
        Player.Move(xx, yy)
    else:
        ActionQueueManager().AddAction("ACTION", UIManager.Keypress, ControlAction.ControlAction_TargetPartyMember1.value, 0)
        ActionQueueManager().AddAction("ACTION", UIManager.Keypress, ControlAction.ControlAction_Follow.value, 0)

    state.last_follow_move_point = (xx, yy)

    cached_data.follow_throttle_timer.Reset()
    return BehaviorTree.NodeState.FAILURE
