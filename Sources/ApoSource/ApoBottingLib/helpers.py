import random
from collections.abc import Callable
from collections.abc import Mapping
from typing import TypedDict
from typing import cast

from Py4GWCoreLib.botting_tree_src.enums import HeroAIStatus
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.native_src.internals.types import PointOrPath
from Py4GWCoreLib.native_src.internals.types import PointPath
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.ActionQueue import ActionQueueManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT

_HEROAI_GUARD_KEY = '__apobottinglib_restore_headless_heroai'
_MULTIBOX_DIALOG_TARGET_KEY = '__apobottinglib_multibox_dialog_target_id'
_POST_MOVEMENT_SETTLE_MS = 125
_WAITSPECIAL_EMOTES: tuple[str, ...] = (
    'attention',
    'bowhead',
    'catchbreath',
    'dancenew',
    'drums',
    'excited',
    'fame',
    'flex',
    'flute',
    'guitar',
    'jump',
    'kneel',
    'paper',
    'rock',
    'salute',
    'scissors',
    'sit',
    'violin',
)
_heroai_pause_counter = 0


def _save_headless_heroai_state() -> BehaviorTree:
    started = {'value': False}

    def _save(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        if not started['value']:
            ActionQueueManager().ResetAllQueues()
            node.blackboard[_HEROAI_GUARD_KEY] = bool(node.blackboard.get('headless_heroai_enabled', True))
            node.blackboard['headless_heroai_enabled_request'] = False
            node.blackboard['headless_heroai_reset_runtime_request'] = True
            started['value'] = True

        if bool(node.blackboard.get('headless_heroai_enabled', True)):
            return BehaviorTree.NodeState.RUNNING
        if node.blackboard.get('HEROAI_STATUS', '') != HeroAIStatus.DISABLED.value:
            return BehaviorTree.NodeState.RUNNING
        if bool(node.blackboard.get('COMBAT_ACTIVE', False)):
            return BehaviorTree.NodeState.RUNNING
        if bool(node.blackboard.get('LOOTING_ACTIVE', False)):
            return BehaviorTree.NodeState.RUNNING
        if bool(node.blackboard.get('USER_INTERRUPT_ACTIVE', False)):
            return BehaviorTree.NodeState.RUNNING
        if bool(node.blackboard.get('PAUSE_MOVEMENT', False)):
            return BehaviorTree.NodeState.RUNNING

        started['value'] = False
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(BehaviorTree.ActionNode(name='PauseHeadlessHeroAIUntilReady', action_fn=_save))


def _restore_headless_heroai_state() -> BehaviorTree:
    def _restore(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        restore_enabled = bool(node.blackboard.pop(_HEROAI_GUARD_KEY, node.blackboard.get('headless_heroai_enabled', True)))
        node.blackboard['headless_heroai_enabled_request'] = restore_enabled
        node.blackboard['headless_heroai_reset_runtime_request'] = True
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(BehaviorTree.ActionNode(name='RestoreHeadlessHeroAIState', action_fn=_restore))


def _wait_until_player_action_settles(
    timeout_ms: int = 4000,
    throttle_interval_ms: int = 100,
) -> BehaviorTree:
    from Py4GWCoreLib.Agent import Agent
    from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
    from Py4GWCoreLib.Player import Player
    from Py4GWCoreLib.routines_src.Checks import Checks

    queue_names = ('ACTION', 'FAST', 'LOOT', 'MERCHANT', 'SALVAGE', 'IDENTIFY')

    def _is_ready() -> BehaviorTree.NodeState:
        if not Checks.Map.MapValid() or Checks.Map.IsLoading():
            return BehaviorTree.NodeState.SUCCESS

        player_agent_id = Player.GetAgentID()
        if player_agent_id == 0 or not Agent.IsValid(player_agent_id) or Checks.Player.IsDead():
            return BehaviorTree.NodeState.SUCCESS

        if Checks.Player.IsKnockedDown():
            return BehaviorTree.NodeState.RUNNING
        if Checks.Player.IsCasting():
            return BehaviorTree.NodeState.RUNNING
        if GLOBAL_CACHE.SkillBar.GetCasting() != 0:
            return BehaviorTree.NodeState.RUNNING
        if Agent.IsMoving(player_agent_id):
            return BehaviorTree.NodeState.RUNNING
        if Agent.IsAttacking(player_agent_id):
            return BehaviorTree.NodeState.RUNNING

        action_queue_manager = ActionQueueManager()
        for queue_name in queue_names:
            if not action_queue_manager.IsEmpty(queue_name):
                return BehaviorTree.NodeState.RUNNING

        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.WaitUntilNode(
            name='WaitUntilPlayerActionSettles',
            condition_fn=_is_ready,
            throttle_interval_ms=max(1, int(throttle_interval_ms)),
            timeout_ms=max(0, int(timeout_ms)),
        )
    )


def _pause_heroai_for_action(action_tree: BehaviorTree) -> BehaviorTree:
    global _heroai_pause_counter
    _heroai_pause_counter += 1
    name = f'HeroAIPausedAction_{_heroai_pause_counter}'

    guarded_action = RoutinesBT.Composite.Sequence(
        _save_headless_heroai_state(),
        action_tree,
        _wait_until_player_action_settles(),
        _restore_headless_heroai_state(),
        name=name,
    )
    restore_after_failure = RoutinesBT.Composite.Sequence(
        _wait_until_player_action_settles(),
        _restore_headless_heroai_state(),
        BehaviorTree(BehaviorTree.FailerNode(name=f'{name}Failed')),
        name=f'{name}RestoreAfterFailure',
    )
    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name=name,
            children=[
                BehaviorTree.SubtreeNode(
                    name=f'{name}Run',
                    subtree_fn=lambda node: guarded_action,
                ),
                BehaviorTree.SubtreeNode(
                    name=f'{name}Restore',
                    subtree_fn=lambda node: restore_after_failure,
                ),
            ],
        )
    )


def _movement_with_runtime_pause(
    name: str,
    builder: Callable[[bool], BehaviorTree],
    pause_on_combat: bool | None = None,
) -> BehaviorTree:
    def _subtree(node: BehaviorTree.Node) -> BehaviorTree:
        resolved_pause = bool(node.blackboard.get('pause_on_combat', True)) if pause_on_combat is None else bool(pause_on_combat)
        return builder(resolved_pause)

    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name=name,
            subtree_fn=_subtree,
        )
    )


def _coerce_dialog_int(value: int | str) -> int:
    if isinstance(value, str):
        return int(value.strip(), 0)
    return int(value)


def _capture_current_target(target_blackboard_key: str = _MULTIBOX_DIALOG_TARGET_KEY) -> BehaviorTree:
    from Py4GWCoreLib.Player import Player

    def _capture(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        target_id = int(Player.GetTargetID() or 0)
        if target_id <= 0:
            return BehaviorTree.NodeState.FAILURE
        node.blackboard[target_blackboard_key] = target_id
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name='CaptureCurrentTarget',
            action_fn=_capture,
        )
    )


def _send_multibox_auto_dialog(button_number: int, log: bool = False, aftercast_ms: int = 100) -> BehaviorTree:
    return RoutinesBT.Shared.SendAndWait(
        command=SharedCommandType.SendDialog,
        params=(float(int(button_number)), 0.0, 0.0, 0.0),
        extra_data=('auto', '', '', ''),
        timeout_ms=5000,
        poll_interval_ms=100,
        log=log,
        aftercast_ms=aftercast_ms,
    )


def _send_multibox_manual_dialog(dialog_id: int | str, log: bool = False, aftercast_ms: int = 100) -> BehaviorTree:
    return RoutinesBT.Shared.SendAndWait(
        command=SharedCommandType.SendManualDialog,
        params=(float(_coerce_dialog_int(dialog_id)), 0.0, 0.0, 0.0),
        timeout_ms=5000,
        poll_interval_ms=100,
        log=log,
        aftercast_ms=aftercast_ms,
    )


def _send_multibox_dialog_to_target(
    dialog_id: int | str,
    *,
    target_blackboard_key: str = _MULTIBOX_DIALOG_TARGET_KEY,
    log: bool = False,
    aftercast_ms: int = 100,
) -> BehaviorTree:
    dialog_value = float(_coerce_dialog_int(dialog_id))

    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name='SendMultiboxDialogToTarget',
            subtree_fn=lambda node: RoutinesBT.Shared.SendAndWait(
                command=SharedCommandType.SendDialogToTarget,
                params=(
                    float(int(node.blackboard.get(target_blackboard_key, 0) or 0)),
                    dialog_value,
                    0.0,
                    0.0,
                ),
                timeout_ms=5000,
                poll_interval_ms=100,
                log=log,
                aftercast_ms=aftercast_ms,
            ),
        )
    )


def _send_multibox_take_dialog_with_target(
    button_number: int,
    *,
    target_blackboard_key: str = _MULTIBOX_DIALOG_TARGET_KEY,
    log: bool = False,
    aftercast_ms: int = 100,
) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name='SendMultiboxTakeDialogWithTarget',
            subtree_fn=lambda node: RoutinesBT.Shared.SendAndWait(
                command=SharedCommandType.TakeDialogWithTarget,
                params=(
                    float(int(node.blackboard.get(target_blackboard_key, 0) or 0)),
                    float(int(button_number)),
                    0.0,
                    0.0,
                ),
                timeout_ms=5000,
                poll_interval_ms=100,
                log=log,
                aftercast_ms=aftercast_ms,
            ),
        )
    )


def _send_multibox_get_blessing_with_target(
    buttons: int | list[int] | tuple[int, ...],
    *,
    target_blackboard_key: str = _MULTIBOX_DIALOG_TARGET_KEY,
    log: bool = False,
    aftercast_ms: int = 100,
) -> BehaviorTree:
    if isinstance(buttons, int):
        resolved_buttons = [int(buttons)]
    else:
        resolved_buttons = [int(button) for button in buttons]

    buttons_csv = ','.join(str(button) for button in resolved_buttons)
    first_button = resolved_buttons[0] if resolved_buttons else 0

    return BehaviorTree(
        BehaviorTree.SubtreeNode(
            name='SendMultiboxGetBlessingWithTarget',
            subtree_fn=lambda node: RoutinesBT.Shared.SendAndWait(
                command=SharedCommandType.GetBlessing,
                params=(
                    float(int(node.blackboard.get(target_blackboard_key, 0) or 0)),
                    float(first_button),
                    0.0,
                    0.0,
                ),
                extra_data=('auto', buttons_csv, '', ''),
                timeout_ms=5000,
                poll_interval_ms=100,
                log=log,
                aftercast_ms=aftercast_ms,
            ),
        )
    )


def _final_point(pos: PointOrPath) -> Vec2f:
    point = PointPath.final_point(pos)
    if point is None:
        raise ValueError('PointPath cannot be empty.')
    return point


def _wait_special(emote: str | None = None, duration_ms: int = 0, log: bool = False) -> BehaviorTree:
    def _pick_emote(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        node.blackboard['waitspecial_emote'] = emote or random.choice(_WAITSPECIAL_EMOTES)
        return BehaviorTree.NodeState.SUCCESS

    return RoutinesBT.Composite.Sequence(
        BehaviorTree(
            BehaviorTree.ActionNode(
                name='WaitSpecialPickEmote',
                action_fn=_pick_emote,
            )
        ),
        BehaviorTree(
            BehaviorTree.SubtreeNode(
                name='WaitSpecialSendEmote',
                subtree_fn=lambda node: RoutinesBT.Player.SendChatCommand(
                    command=str(node.blackboard.get('waitspecial_emote', 'dance')),
                    log=log,
                ),
            )
        ),
        RoutinesBT.Player.Wait(duration_ms=duration_ms, log=log),
        name='WaitSpecial',
    )


def _wait_until_player_stops_moving(
    timeout_ms: int = 2000,
    throttle_interval_ms: int = 100,
    log: bool = False,
) -> BehaviorTree:
    from Py4GWCoreLib.Agent import Agent
    from Py4GWCoreLib.Player import Player

    def _not_moving() -> BehaviorTree.NodeState:
        if not Agent.IsMoving(Player.GetAgentID()):
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.WaitUntilNode(
            name='WaitUntilPlayerStopsMoving',
            condition_fn=_not_moving,
            throttle_interval_ms=max(1, int(throttle_interval_ms)),
            timeout_ms=max(0, int(timeout_ms)),
        )
    )


class _MoveAndKillStep(TypedDict, total=False):
    pos: PointOrPath
    path: PointOrPath
    clear_area_radius: float
    pause_on_combat: bool | None
    flag_heroes_to_waypoint: bool


def _coerce_vanquish_step(
    step: object,
    clear_area_radius: float,
    pause_on_combat: bool | None,
    flag_heroes_to_waypoint: bool,
) -> tuple[PointOrPath, float, bool | None, bool]:
    if isinstance(step, Mapping):
        step_data = cast(_MoveAndKillStep, dict(step))
        resolved_pos = step_data.get('pos', step_data.get('path'))
        step_clear_area_radius = float(step_data.get('clear_area_radius', clear_area_radius))
        step_pause_on_combat = cast(bool | None, step_data.get('pause_on_combat', pause_on_combat))
        step_flag_heroes_to_waypoint = bool(step_data.get('flag_heroes_to_waypoint', flag_heroes_to_waypoint))
    else:
        resolved_pos = cast(PointOrPath | None, step)
        step_clear_area_radius = clear_area_radius
        step_pause_on_combat = pause_on_combat
        step_flag_heroes_to_waypoint = flag_heroes_to_waypoint

    if resolved_pos is None:
        raise ValueError('VanquishNode steps must provide `pos` or `path`.')

    return (
        resolved_pos,
        step_clear_area_radius,
        step_pause_on_combat,
        step_flag_heroes_to_waypoint,
    )
