from __future__ import annotations

from dataclasses import dataclass, field

from Py4GWCoreLib import ActionQueueManager, Agent, GLOBAL_CACHE, Range, SharedCommandType, Utils, Weapon
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.UI_enums import ControlAction
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

from ..cache_data import CacheData
from .smart_unstuck import (
    SMART_UNSTUCK_CFG,
    SmartUnstuckState,
    force_front_detour,
    reset_smart_unstuck,
    update_smart_unstuck,
)


@dataclass(slots=True)
class FollowExecutionState:
    last_follow_move_point: tuple[float, float] | None = None
    last_follow_assigned_point: tuple[float, float, int] | None = None
    follow_map_entry_signature: tuple[int, int, int, int, int] | None = None
    last_leader_publish_signature: tuple[int, int, int, int, int] | None = None
    recovery_active: bool = False
    last_recovery_follow_command_ms: int = 0
    recovery_detour_attempted: bool = False
    pet_recovery_notified: bool = False
    relocating_to_flag: bool = False
    stuck: SmartUnstuckState = field(default_factory=SmartUnstuckState)


FOLLOW_RECOVERY_DISTANCE = Range.Spirit.value
FOLLOW_RECOVERY_START_DISTANCE = FOLLOW_RECOVERY_DISTANCE
FOLLOW_RECOVERY_RELEASE_DISTANCE = Range.Earshot.value


def get_follow_destination_distance(cached_data: CacheData) -> float:
    destination = get_follow_destination_xy(cached_data)
    if destination is None:
        return 0.0
    return float(Utils.Distance(destination, Agent.GetXY(Player.GetAgentID())))


def get_follow_destination_xy(cached_data: CacheData) -> tuple[float, float] | None:
    options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(cached_data.account_email)

    if not options:
        return None

    def _is_nonzero_xy(x: float, y: float) -> bool:
        return abs(float(x)) > 0.001 or abs(float(y)) > 0.001

    published_follow_xy = (float(options.FollowPos.x), float(options.FollowPos.y))
    flag_xy = (float(options.FlagPos.x), float(options.FlagPos.y))
    is_flagged = bool(getattr(options, "IsFlagged", False))
    if _is_nonzero_xy(*published_follow_xy):
        return published_follow_xy

    if is_flagged and _is_nonzero_xy(*flag_xy):
        return flag_xy

    return None


def _notify_recovery_console_message(message_text: str) -> None:
    sender_email = str(Player.GetAccountEmail() or "").strip()
    leader_account = GLOBAL_CACHE.ShMem.GetAccountDataFromPartyNumber(0)
    leader_email = str(getattr(leader_account, "AccountEmail", "") or "").strip() if leader_account else ""
    if sender_email and leader_email and sender_email != leader_email:
        GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            leader_email,
            SharedCommandType.ConsoleMessage,
            (0, 0, 0, 0),
            (message_text,),
        )


def _maybe_notify_pet_recovery(cached_data: CacheData, state: FollowExecutionState) -> None:
    player_agent_id = int(Player.GetAgentID())
    pet_id = int(GLOBAL_CACHE.Party.Pets.GetPetID(player_agent_id) or 0)
    if pet_id <= 0 or not Agent.IsValid(pet_id):
        state.pet_recovery_notified = False
        return

    destination = get_follow_destination_xy(cached_data)
    if destination is None:
        state.pet_recovery_notified = False
        return

    pet_x, pet_y = Agent.GetXY(pet_id)
    pet_distance = float(Utils.Distance(destination, (pet_x, pet_y)))
    if pet_distance < float(FOLLOW_RECOVERY_START_DISTANCE):
        state.pet_recovery_notified = False
        return

    if state.pet_recovery_notified:
        return

    _notify_recovery_console_message(f"pet lagged behind at x={pet_x:.0f}, y={pet_y:.0f}")
    state.pet_recovery_notified = True


def is_follow_recovery_active(cached_data: CacheData, state: FollowExecutionState) -> bool:
    options = cached_data.account_options
    player_agent_id = int(Player.GetAgentID())

    if (
        not options
        or not bool(getattr(options, "Following", False))
        or player_agent_id <= 0
        or player_agent_id == int(GLOBAL_CACHE.Party.GetPartyLeaderID())
    ):
        state.recovery_active = False
        state.pet_recovery_notified = False
        return False

    _maybe_notify_pet_recovery(cached_data, state)

    distance_to_destination = get_follow_destination_distance(cached_data)
    if state.recovery_active:
        state.recovery_active = distance_to_destination >= FOLLOW_RECOVERY_RELEASE_DISTANCE
        if not state.recovery_active:
            state.recovery_detour_attempted = False
        return state.recovery_active

    if distance_to_destination < FOLLOW_RECOVERY_START_DISTANCE:
        return False

    state.recovery_active = True
    state.recovery_detour_attempted = False
    try:
        _notify_recovery_console_message("Hey, Wait for me!")
    except Exception:
        pass
    return True


def execute_follower_follow(
    cached_data: CacheData,
    state: FollowExecutionState,
) -> BehaviorTree.NodeState:
    follow_active_state = BehaviorTree.NodeState.SUCCESS

    def _is_nonzero_xy(x: float, y: float) -> bool:
        return abs(float(x)) > 0.001 or abs(float(y)) > 0.001

    def _reset_follow_runtime() -> None:
        state.last_follow_move_point = None
        state.last_follow_assigned_point = None
        state.last_recovery_follow_command_ms = 0
        state.recovery_detour_attempted = False
        state.relocating_to_flag = False
        reset_smart_unstuck(state.stuck)

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
        state.recovery_active = False
        return BehaviorTree.NodeState.FAILURE

    # During an active stuck-avoidance detour, BT.Move needs to tick at the
    # full HeroAI BT rate (~33ms) so it can detect "almost there" mid-walk and
    # switch the engine target BEFORE the follower physically arrives at a
    # waypoint. Apo's "constantly steer" — at the previous 100ms throttle the
    # follower covered an entire 89u waypoint between BT ticks, so BT only
    # ever sampled the player at arrival moments and tolerance had no effect.
    # Idle mode keeps the 250ms throttle since smoothness doesn't matter there.
    if state.stuck.mode != "idle":
        cached_data.follow_throttle_timer.SetThrottleTime(0)
    else:
        cached_data.follow_throttle_timer.SetThrottleTime(250)

    if not cached_data.follow_throttle_timer.IsExpired():
        return BehaviorTree.NodeState.FAILURE

    player_agent_id = int(Player.GetAgentID())
    if player_agent_id == GLOBAL_CACHE.Party.GetPartyLeaderID():
        state.recovery_active = False
        cached_data.follow_throttle_timer.Reset()
        return BehaviorTree.NodeState.FAILURE

    recovery_active = is_follow_recovery_active(cached_data, state)

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

    published_follow_xy = (float(options.FollowPos.x), float(options.FollowPos.y))
    published_follow_z = int(float(options.FollowPos.z))

    if own_flag_active:
        if _is_nonzero_xy(*published_follow_xy):
            follow_x, follow_y = published_follow_xy
            follow_z = published_follow_z
        else:
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
        follow_x, follow_y = published_follow_xy
        follow_z = published_follow_z
        if (not _is_nonzero_xy(follow_x, follow_y)) and follow_z == 0:
            _reset_follow_runtime()
            return BehaviorTree.NodeState.FAILURE

    combat_active = bool(cached_data.IsHeadlessCombatPauseActive())
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

    # A flag re-position (assigned point moved) takes priority over combat: the
    # follower must walk to the new flag even mid-fight. Latch a relocation
    # state that is cleared once the follower arrives, so it keeps moving across
    # ticks instead of re-yielding to local aggro after the one-tick
    # assigned_changed pulse.
    if (own_flag_active or all_flag_active) and assigned_changed:
        state.relocating_to_flag = True

    # Upstream "follow recovery": when the follower is far from its destination,
    # tighten the tolerance to FOLLOW_RECOVERY_RELEASE_DISTANCE so it keeps
    # closing the gap instead of stopping at the normal slot threshold.
    effective_follow_distance = min(follow_distance, FOLLOW_RECOVERY_RELEASE_DISTANCE) if recovery_active else follow_distance
    # When flagged the published threshold is 0.0 (hold position exactly), which
    # makes the arrival check below impossible to satisfy and permanently blocks
    # HandleCombat in the headless tree selector.  Enforce a minimum arrival
    # radius of Adjacent so followers that have reached the flag can fight.
    if (own_flag_active or all_flag_active) and effective_follow_distance < float(Range.Adjacent.value):
        effective_follow_distance = float(Range.Adjacent.value)
    dist_to_follow = Utils.Distance((follow_x, follow_y), Player.GetXY())
    if dist_to_follow <= effective_follow_distance:
        state.last_recovery_follow_command_ms = 0
        state.recovery_detour_attempted = False
        state.relocating_to_flag = False
        reset_smart_unstuck(state.stuck)
        return BehaviorTree.NodeState.FAILURE

    # Flagged followers: yield to HandleCombat only while there are enemies in
    # range of THIS follower (local aggro), not party-wide aggro. Holding
    # position makes Follow win the selector, which both blocks combat AND
    # leaves the follower idle once the engine move is interrupted by aggro.
    # Gating on local aggro (instead of the party-driven `in_aggro`) lets a
    # follower with no nearby enemies walk back to its flag even while the rest
    # of the party fights elsewhere. While relocating to a freshly moved flag,
    # do NOT yield — the flag move must win over combat. Recovery (dist >=
    # Spirit) is handled below and also takes priority over fighting.
    if (
        (own_flag_active or all_flag_active)
        and bool(cached_data.data.local_in_aggro)
        and not recovery_active
        and not state.relocating_to_flag
    ):
        # Drop the cached move point so that once combat ends the arrival/move
        # path below re-issues Player.Move toward the flag instead of skipping
        # it via the "already moved here" dedup — otherwise a follower that
        # chased an enemy away stays put after combat instead of returning.
        state.last_follow_move_point = None
        cached_data.follow_throttle_timer.Reset()
        return BehaviorTree.NodeState.FAILURE

    if follow_z == 0 and not own_flag_active:
        update_smart_unstuck(
            state.stuck,
            SMART_UNSTUCK_CFG,
            current_xy=Player.GetXY(),
            follow_xy=(follow_x, follow_y),
            assigned_changed=assigned_changed,
        )
    else:
        reset_smart_unstuck(state.stuck)

    # During an active detour, BT.Move has already issued Player.Move with its
    # own stall-aware pacing. Skip our Player.Move below — otherwise we clobber
    # the in-flight pathing and reintroduce inter-waypoint stutter.
    if state.stuck.mode != "idle":
        state.last_follow_move_point = None
        cached_data.follow_throttle_timer.Reset()
        return follow_active_state

    if recovery_active:
        if own_flag_active or all_flag_active:
            # Flagged followers have a fixed world destination (the flag), so
            # recover by walking straight to it. The detour/engine-follow
            # recovery below is meant for leader-following; for the flag case it
            # never issues a move command, leaving a far-flagged follower
            # standing still even when the leader is far away.
            if ActionQueueManager().IsEmpty("ACTION"):
                Player.Move(follow_x, follow_y)
                state.last_follow_move_point = (follow_x, follow_y)
            cached_data.follow_throttle_timer.Reset()
            return follow_active_state
        if not state.recovery_detour_attempted:
            force_front_detour(
                state.stuck,
                SMART_UNSTUCK_CFG,
                current_xy=Player.GetXY(),
                follow_xy=(follow_x, follow_y),
            )
            state.recovery_detour_attempted = True
            state.last_recovery_follow_command_ms = 0
            cached_data.follow_throttle_timer.Reset()
            return follow_active_state
        now_ms = int(Utils.GetBaseTimestamp())
        if now_ms - int(state.last_recovery_follow_command_ms) < 1000:
            cached_data.follow_throttle_timer.Reset()
            return follow_active_state
        if ActionQueueManager().IsEmpty("ACTION"):
            ActionQueueManager().AddAction("ACTION", UIManager.Keypress, ControlAction.ControlAction_TargetPartyMember1.value, 0)
            ActionQueueManager().AddAction("ACTION", UIManager.Keypress, ControlAction.ControlAction_Follow.value, 0)
            state.last_recovery_follow_command_ms = now_ms
        cached_data.follow_throttle_timer.Reset()
        return follow_active_state

    xx = follow_x
    yy = follow_y

    if not assigned_changed and state.last_follow_move_point is not None:
        last_x, last_y = state.last_follow_move_point
        if Utils.Distance((last_x, last_y), (xx, yy)) <= 10.0:
            return follow_active_state

    if not ActionQueueManager().IsEmpty("ACTION"):
        return follow_active_state

    if follow_z == 0 or own_flag_active or all_flag_active:
        Player.Move(xx, yy)
    else:
        ActionQueueManager().AddAction("ACTION", UIManager.Keypress, ControlAction.ControlAction_TargetPartyMember1.value, 0)
        ActionQueueManager().AddAction("ACTION", UIManager.Keypress, ControlAction.ControlAction_Follow.value, 0)

    state.last_follow_move_point = (xx, yy)

    cached_data.follow_throttle_timer.Reset()
    return follow_active_state
