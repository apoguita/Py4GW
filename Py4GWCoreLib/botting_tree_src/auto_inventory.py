from __future__ import annotations

from typing import Any
from typing import Protocol

from ..py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
from ..py4gwcorelib_src.BehaviorTree import BehaviorTree


class _BottingTreeAutoInventoryHost(Protocol):
    blackboard: dict[str, Any]
    started: bool
    auto_inventory_handler_enabled_policy: bool | None
    restore_auto_inventory_handler_on_stop: bool
    _auto_inventory_handler_restore_state: bool | None


class BottingTreeAutoInventoryMixin:
    def _get_auto_inventory_handler(self: _BottingTreeAutoInventoryHost) -> AutoInventoryHandler:
        return AutoInventoryHandler()

    def IsAutoInventoryHandlerEnabled(self: _BottingTreeAutoInventoryHost) -> bool:
        return bool(self._get_auto_inventory_handler().module_active)

    def SetAutoInventoryHandlerEnabled(self: _BottingTreeAutoInventoryHost, enabled: bool) -> bool:
        desired_state = bool(enabled)
        self._get_auto_inventory_handler().module_active = desired_state
        self.blackboard['auto_inventory_handler_enabled'] = desired_state
        return True

    def EnableAutoInventoryHandler(self: _BottingTreeAutoInventoryHost) -> bool:
        return self.SetAutoInventoryHandlerEnabled(True)

    def DisableAutoInventoryHandler(self: _BottingTreeAutoInventoryHost) -> bool:
        return self.SetAutoInventoryHandlerEnabled(False)

    def ToggleAutoInventoryHandler(self: _BottingTreeAutoInventoryHost) -> bool:
        next_state = not self.IsAutoInventoryHandlerEnabled()
        self.SetAutoInventoryHandlerEnabled(next_state)
        return next_state

    def SetRestoreAutoInventoryHandlerOnStop(self: _BottingTreeAutoInventoryHost, enabled: bool) -> None:
        self.restore_auto_inventory_handler_on_stop = bool(enabled)

    def _capture_auto_inventory_handler_state_for_restore(self: _BottingTreeAutoInventoryHost) -> None:
        if not self.restore_auto_inventory_handler_on_stop or self._auto_inventory_handler_restore_state is not None:
            return
        self._auto_inventory_handler_restore_state = self.IsAutoInventoryHandlerEnabled()

    def RestoreAutoInventoryHandlerState(self: _BottingTreeAutoInventoryHost) -> bool:
        prior_state = self._auto_inventory_handler_restore_state
        self._auto_inventory_handler_restore_state = None
        if not self.restore_auto_inventory_handler_on_stop or prior_state is None:
            return False
        return self.SetAutoInventoryHandlerEnabled(bool(prior_state))

    def ConfigureAutoInventoryHandler(
        self: _BottingTreeAutoInventoryHost,
        enabled: bool | None = None,
        *,
        restore_on_stop: bool = True,
    ) -> None:
        if enabled is not None:
            self.auto_inventory_handler_enabled_policy = bool(enabled)
        self.restore_auto_inventory_handler_on_stop = bool(restore_on_stop)
        if self.started:
            self._apply_auto_inventory_handler_policy()

    def _apply_auto_inventory_handler_policy(self: _BottingTreeAutoInventoryHost) -> bool:
        if self.auto_inventory_handler_enabled_policy is None:
            return False
        self._capture_auto_inventory_handler_state_for_restore()
        changed = self.SetAutoInventoryHandlerEnabled(self.auto_inventory_handler_enabled_policy)
        self.blackboard['auto_inventory_handler_enabled'] = self.IsAutoInventoryHandlerEnabled()
        return changed

    @staticmethod
    def GetAutoInventoryHandlerSetEnabledTree(enabled: bool, name: str | None = None) -> BehaviorTree:
        node_name = name or ('EnableAutoInventoryHandler' if enabled else 'DisableAutoInventoryHandler')

        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            node.blackboard['auto_inventory_handler_enabled_request'] = bool(enabled)
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=node_name,
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )

    @staticmethod
    def EnableAutoInventoryHandlerTree() -> BehaviorTree:
        return BottingTreeAutoInventoryMixin.GetAutoInventoryHandlerSetEnabledTree(
            True,
            name='EnableAutoInventoryHandler',
        )

    @staticmethod
    def DisableAutoInventoryHandlerTree() -> BehaviorTree:
        return BottingTreeAutoInventoryMixin.GetAutoInventoryHandlerSetEnabledTree(
            False,
            name='DisableAutoInventoryHandler',
        )

    @staticmethod
    def ToggleAutoInventoryHandlerTree() -> BehaviorTree:
        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            current_enabled = bool(node.blackboard.get('auto_inventory_handler_enabled', False))
            node.blackboard['auto_inventory_handler_enabled_request'] = not current_enabled
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name='ToggleAutoInventoryHandler',
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )
