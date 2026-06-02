from __future__ import annotations

from typing import Any
from typing import Protocol

from ..py4gwcorelib_src.BehaviorTree import BehaviorTree
from ..py4gwcorelib_src.WidgetManager import WidgetCatalog
from ..py4gwcorelib_src.WidgetManager import get_widget_handler


class _BottingTreeWidgetControlHost(Protocol):
    blackboard: dict[str, Any]
    started: bool
    widget_enabled_policies: dict[str, bool]
    restore_widget_states_on_stop: bool
    _widget_restore_snapshot: dict[str, bool] | None


class BottingTreeWidgetControlMixin:
    def _get_widget_info(self: _BottingTreeWidgetControlHost, widget_name: str):
        normalized_name = str(widget_name or '').strip()
        if not normalized_name:
            return None
        try:
            widget_handler = get_widget_handler()
            snapshot = WidgetCatalog.snapshot_from_handler(widget_handler)
            widget = snapshot.widgets_by_id.get(normalized_name)
            if widget is not None:
                return widget
            widget = widget_handler.get_widget_info(normalized_name)
            if widget is not None:
                return widget
            for candidate in snapshot.widgets_by_id.values():
                if str(getattr(candidate, 'plain_name', '') or '').strip() == normalized_name:
                    return candidate
            return None
        except Exception:
            return None

    def _resolve_widget_toggle_name(self: _BottingTreeWidgetControlHost, widget_name: str) -> str:
        widget = self._get_widget_info(widget_name)
        if widget is not None and getattr(widget, 'plain_name', ''):
            return str(widget.plain_name)
        return str(widget_name)

    def IsWidgetEnabled(self: _BottingTreeWidgetControlHost, widget_name: str) -> bool:
        widget = self._get_widget_info(widget_name)
        return bool(widget and widget.enabled)

    def SetWidgetEnabled(self: _BottingTreeWidgetControlHost, widget_name: str, enabled: bool) -> bool:
        toggle_name = self._resolve_widget_toggle_name(widget_name)
        desired_state = bool(enabled)
        try:
            widget_handler = get_widget_handler()
            if desired_state:
                widget_handler.enable_widget(toggle_name)
            else:
                widget_handler.disable_widget(toggle_name)
            self.blackboard[f'widget_enabled:{toggle_name}'] = desired_state
            return True
        except Exception:
            return False

    def EnableWidget(self: _BottingTreeWidgetControlHost, widget_name: str) -> bool:
        return self.SetWidgetEnabled(widget_name, True)

    def DisableWidget(self: _BottingTreeWidgetControlHost, widget_name: str) -> bool:
        return self.SetWidgetEnabled(widget_name, False)

    def ToggleWidget(self: _BottingTreeWidgetControlHost, widget_name: str) -> bool:
        new_state = not self.IsWidgetEnabled(widget_name)
        self.SetWidgetEnabled(widget_name, new_state)
        return new_state

    def SetRestoreWidgetStatesOnStop(self: _BottingTreeWidgetControlHost, enabled: bool) -> None:
        self.restore_widget_states_on_stop = bool(enabled)

    def ConfigureWidget(self: _BottingTreeWidgetControlHost, widget_name: str, enabled: bool, *, restore_on_stop: bool = True) -> None:
        normalized_name = self._resolve_widget_toggle_name(widget_name)
        if not normalized_name:
            return
        self.widget_enabled_policies[normalized_name] = bool(enabled)
        self.restore_widget_states_on_stop = bool(restore_on_stop)
        if self.started:
            self._apply_widget_policies()

    def ConfigureWidgets(
        self: _BottingTreeWidgetControlHost,
        *,
        activate_widget_list: list[str] | tuple[str, ...] | None = None,
        deactivate_widget_list: list[str] | tuple[str, ...] | None = None,
        restore_on_stop: bool = True,
        clear_existing: bool = False,
    ) -> None:
        if clear_existing:
            self.widget_enabled_policies.clear()
        for widget_name in activate_widget_list or ():
            self.ConfigureWidget(str(widget_name), True, restore_on_stop=restore_on_stop)
        for widget_name in deactivate_widget_list or ():
            self.ConfigureWidget(str(widget_name), False, restore_on_stop=restore_on_stop)
        self.restore_widget_states_on_stop = bool(restore_on_stop)
        if self.started:
            self._apply_widget_policies()

    def ClearWidgetPolicy(self: _BottingTreeWidgetControlHost, widget_name: str) -> bool:
        normalized_name = self._resolve_widget_toggle_name(widget_name)
        if normalized_name in self.widget_enabled_policies:
            self.widget_enabled_policies.pop(normalized_name, None)
            return True
        return False

    def _capture_widget_states_for_restore(self: _BottingTreeWidgetControlHost) -> None:
        if not self.restore_widget_states_on_stop or self._widget_restore_snapshot is not None:
            return
        snapshot: dict[str, bool] = {}
        for widget_name in self.widget_enabled_policies:
            snapshot[widget_name] = self.IsWidgetEnabled(widget_name)
        self._widget_restore_snapshot = snapshot

    def RestoreWidgetStates(self: _BottingTreeWidgetControlHost) -> bool:
        snapshot = self._widget_restore_snapshot
        self._widget_restore_snapshot = None
        if not self.restore_widget_states_on_stop or not snapshot:
            return False
        changed = False
        for widget_name, enabled in snapshot.items():
            changed = self.SetWidgetEnabled(widget_name, bool(enabled)) or changed
        return changed

    def _apply_widget_policies(self: _BottingTreeWidgetControlHost) -> bool:
        if not self.widget_enabled_policies:
            return False
        self._capture_widget_states_for_restore()
        changed = False
        for widget_name, enabled in self.widget_enabled_policies.items():
            changed = self.SetWidgetEnabled(widget_name, bool(enabled)) or changed
            self.blackboard[f'widget_enabled:{widget_name}'] = self.IsWidgetEnabled(widget_name)
        return changed

    @staticmethod
    def GetWidgetSetEnabledTree(widget_name: str, enabled: bool, name: str | None = None) -> BehaviorTree:
        node_name = name or (f"ActivateWidget({widget_name})" if enabled else f"DeactivateWidget({widget_name})")

        def _set_widget_enabled(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            requests = node.blackboard.setdefault('widget_enabled_requests', {})
            if isinstance(requests, dict):
                requests[str(widget_name)] = bool(enabled)
                return BehaviorTree.NodeState.SUCCESS
            return BehaviorTree.NodeState.FAILURE

        return BehaviorTree(
            BehaviorTree.ActionNode(name=node_name, action_fn=_set_widget_enabled, aftercast_ms=0)
        )

    @staticmethod
    def ActivateWidgetTree(widget_name: str, name: str | None = None) -> BehaviorTree:
        return BottingTreeWidgetControlMixin.GetWidgetSetEnabledTree(widget_name, True, name=name)

    @staticmethod
    def DeactivateWidgetTree(widget_name: str, name: str | None = None) -> BehaviorTree:
        return BottingTreeWidgetControlMixin.GetWidgetSetEnabledTree(widget_name, False, name=name)
