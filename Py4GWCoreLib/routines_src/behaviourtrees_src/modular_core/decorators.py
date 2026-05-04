"""
decorators module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from dataclasses import dataclass

from Py4GWCoreLib import Console, ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.actions_party_toggles import (
    apply_auto_combat_state,
    apply_auto_looting_state,
    current_auto_combat_enabled,
    current_auto_looting_enabled,
)
from Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.step_utils import (
    cutscene_active,
    parse_step_bool,
    step_delay_ms,
)

from .contracts import StepNodeRequest


AUTO_STATE_GUARD_STEP_TYPES = {
    "dialog",
    "dialogs",
    "dialog_multibox",
    "exit_map",
}


def _fail_log(message: str, *, message_type=Console.MessageType.Error) -> None:
    ConsoleLog("ModularBot", message, message_type)


@dataclass
class _AutoStateGuardedSubtreeAction:
    """
    A ut oS ta te Gu ar de dS ub tr ee Ac ti on class.
    
    Meta:
      Expose: false
      Audience: advanced
      Display: Auto State Guarded Subtree Action
      Purpose: Provide explicit modular runtime behavior and metadata.
      UserDescription: Internal class used by modular orchestration and step execution.
      Notes: Keep behavior explicit and side effects contained.
    """
    request: StepNodeRequest
    child_tree: BehaviorTree
    entered: bool = False
    looting_was_enabled: bool = False
    combat_was_enabled: bool = False
    pause_on_danger_exists: bool = False
    pause_on_danger_was_active: bool = False

    def _enter(self) -> None:
        if self.entered:
            return
        bot = self.request.bot
        self.looting_was_enabled = current_auto_looting_enabled(bot)
        self.combat_was_enabled = current_auto_combat_enabled(bot)
        self.pause_on_danger_exists = bool(bot.Properties.exists("pause_on_danger"))
        self.pause_on_danger_was_active = (
            bool(bot.Properties.IsActive("pause_on_danger")) if self.pause_on_danger_exists else False
        )
        if self.looting_was_enabled:
            apply_auto_looting_state(bot, False)
        if self.combat_was_enabled:
            apply_auto_combat_state(bot, False)
        self.entered = True

    def _exit(self) -> None:
        if not self.entered:
            return
        bot = self.request.bot
        if self.looting_was_enabled:
            apply_auto_looting_state(bot, True)
        if self.combat_was_enabled:
            apply_auto_combat_state(bot, True)
        if self.pause_on_danger_exists:
            bot.Properties.ApplyNow("pause_on_danger", "active", self.pause_on_danger_was_active)
        self.entered = False
        self.child_tree.reset()

    def __call__(self, node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        self._enter()
        self.child_tree.blackboard = node.blackboard
        try:
            result = BehaviorTree.Node._normalize_state(self.child_tree.tick())
            if result is None:
                raise TypeError("Guarded subtree returned non-NodeState result.")
        except Exception as exc:
            self._exit()
            _fail_log(
                f"Auto-state guard subtree failed for step {self.request.step_type!r}: {exc}",
                message_type=Console.MessageType.Error,
            )
            return BehaviorTree.NodeState.FAILURE

        if result != BehaviorTree.NodeState.RUNNING:
            self._exit()
        return result


def with_recovery_gate(child_tree: BehaviorTree, request: StepNodeRequest) -> BehaviorTree:
    owner = request.owner

    def _ready() -> bool:
        if owner._pending_recovery is not None:
            return False
        if owner._on_death is None and owner._is_player_dead():
            return False
        return True

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=f"RecoveryGate::{request.step_type}",
            children=[
                BehaviorTree.WaitUntilNode(
                    name=f"WaitRecoveryReady::{request.step_type}",
                    condition_fn=_ready,
                    throttle_interval_ms=50,
                    timeout_ms=0,
                ),
                BehaviorTree.SubtreeNode(
                    name=f"Core::{request.step_type}",
                    subtree_fn=lambda _node, _tree=child_tree: _tree,
                ),
            ],
        )
    )


def with_auto_state_guard(child_tree: BehaviorTree, request: StepNodeRequest) -> BehaviorTree:
    if request.step_type not in AUTO_STATE_GUARD_STEP_TYPES:
        return child_tree
    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"AutoStateGuard::{request.step_type}",
            action_fn=_AutoStateGuardedSubtreeAction(request=request, child_tree=child_tree),
            aftercast_ms=0,
        )
    )


def with_anchor(child_tree: BehaviorTree, request: StepNodeRequest) -> BehaviorTree:
    if not parse_step_bool(request.step.get("anchor", False), False):
        return child_tree

    def _set_anchor(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        target = str(node.blackboard.get("modular_last_registered_state_name", "") or "").strip()
        if target:
            request.owner.set_anchor(target)
        else:
            request.owner.set_anchor(request.step_display)
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=f"Anchor::{request.step_type}",
            children=[
                BehaviorTree.SubtreeNode(
                    name=f"AnchorCore::{request.step_type}",
                    subtree_fn=lambda _node, _tree=child_tree: _tree,
                ),
                BehaviorTree.ActionNode(
                    name=f"SetAnchor::{request.step_type}",
                    action_fn=_set_anchor,
                    aftercast_ms=0,
                ),
            ],
        )
    )


def with_post_delay(child_tree: BehaviorTree, request: StepNodeRequest) -> BehaviorTree:
    delay_ms = step_delay_ms(request.step)
    if delay_ms <= 0:
        return child_tree
    from time import monotonic

    started_at: float | None = None

    def _delay_or_cutscene() -> BehaviorTree.NodeState:
        nonlocal started_at
        if started_at is None:
            started_at = monotonic()
        if cutscene_active():
            started_at = None
            return BehaviorTree.NodeState.SUCCESS
        if (monotonic() - started_at) * 1000.0 >= delay_ms:
            started_at = None
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name=f"PostDelay::{request.step_type}",
            children=[
                BehaviorTree.SubtreeNode(
                    name=f"DelayCore::{request.step_type}",
                    subtree_fn=lambda _node, _tree=child_tree: _tree,
                ),
                BehaviorTree.ActionNode(
                    name=f"DelayOrCutscene::{request.step_type}",
                    action_fn=_delay_or_cutscene,
                    aftercast_ms=0,
                ),
            ],
        )
    )
