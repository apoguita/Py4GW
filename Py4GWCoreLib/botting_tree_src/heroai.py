from typing import Any
from typing import Protocol

from ..GlobalCache import GLOBAL_CACHE
from ..GlobalCache.shared_memory_src.Globals import SHMEM_MAX_NUMBER_OF_SKILLS
from ..GlobalCache.shared_memory_src.HeroAIOptionStruct import HeroAIOptionStruct
from ..Player import Player
from ..enums_src.Multiboxing_enums import SharedCommandType
from ..py4gwcorelib_src.BehaviorTree import BehaviorTree
from ..py4gwcorelib_src.WidgetManager import get_widget_handler
from ..py4gwcorelib_src.WidgetManager import WidgetCatalog
from .enums import HeroAIStatus


class _BottingTreeHeroAIHost(Protocol):
    _HEROAI_WIDGET_NAME: str
    _HEROAI_WIDGET_ID: str
    _headless_disabled_heroai_widget: bool
    blackboard: dict[str, Any]
    looting_enabled: bool
    started: bool
    paused: bool
    headless_heroai_enabled: bool
    headless_heroai: Any
    _last_heroai_state: str | None
    _last_multibox_heroai_widget_state: bool | None

    def IsMultiAccountMode(self) -> bool: ...
    def ApplyAccountIsolation(self) -> bool: ...
    def _get_heroai_widget(self): ...
    def _get_heroai_widget_toggle_name(self) -> str: ...
    def _sync_multibox_heroai_widget(self, enabled: bool) -> bool: ...
    def SetHeadlessHeroAIEnabled(self, enabled: bool, reset_runtime: bool = True): ...
    def SetLootingEnabled(self, enabled: bool) -> bool: ...
    def RestoreHeroAIOptions(self) -> bool: ...
    def _heroai_options_match_runtime_policy(self) -> bool: ...


class BottingTreeHeroAIMixin:
    _HEROAI_WIDGET_NAME = 'HeroAI'
    _HEROAI_WIDGET_ID = 'Automation/Multiboxing/HeroAI.py'

    def IsMultiAccountMode(self) -> bool:
        raise NotImplementedError

    def ApplyAccountIsolation(self) -> bool:
        raise NotImplementedError

    def _get_heroai_widget(self: _BottingTreeHeroAIHost):
        try:
            widget_handler = get_widget_handler()
            snapshot = WidgetCatalog.snapshot_from_handler(widget_handler)
            widget = snapshot.widgets_by_id.get(self._HEROAI_WIDGET_ID)
            if widget is not None:
                return widget
            widget = widget_handler.get_widget_info(self._HEROAI_WIDGET_ID)
            if widget is not None:
                return widget
            return widget_handler.get_widget_info(self._HEROAI_WIDGET_NAME)
        except Exception:
            return None

    def _get_heroai_widget_toggle_name(self: _BottingTreeHeroAIHost) -> str:
        widget = self._get_heroai_widget()
        if widget is not None and widget.plain_name:
            return widget.plain_name
        return self._HEROAI_WIDGET_NAME

    def _is_heroai_widget_enabled(self: _BottingTreeHeroAIHost) -> bool:
        widget = self._get_heroai_widget()
        return bool(widget and widget.enabled)

    def _sync_multibox_heroai_widget(self: _BottingTreeHeroAIHost, enabled: bool) -> bool:
        if not self.IsMultiAccountMode():
            self._last_multibox_heroai_widget_state = None
            return False

        desired_state = bool(enabled)
        if getattr(self, '_last_multibox_heroai_widget_state', None) is desired_state:
            return False

        sender_email = str(Player.GetAccountEmail() or '')
        if not sender_email:
            return False

        widget_name = self._get_heroai_widget_toggle_name()
        command = SharedCommandType.EnableWidget if desired_state else SharedCommandType.DisableWidget
        sent_any = False
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            receiver_email = str(getattr(account, 'AccountEmail', '') or '')
            if not receiver_email or receiver_email == sender_email:
                continue
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                receiver_email,
                command,
                (0.0, 0.0, 0.0, 0.0),
                (widget_name, '', '', ''),
            )
            sent_any = True

        self._last_multibox_heroai_widget_state = desired_state
        return sent_any

    def _sync_multibox_headless_looting(self: _BottingTreeHeroAIHost, enabled: bool) -> bool:
        if not self.IsMultiAccountMode():
            return False
        if not bool(enabled):
            return False

        sender_email = str(Player.GetAccountEmail() or '').strip()
        if not sender_email:
            return False

        local_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email)
        local_party_id = int(getattr(getattr(local_account, 'AgentPartyData', None), 'PartyID', 0) or 0) if local_account else 0
        local_group_id = int(getattr(local_account, 'IsolationGroupID', 0) or 0) if local_account else 0

        sent_any = False
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            receiver_email = str(getattr(account, 'AccountEmail', '') or '').strip()
            if not receiver_email or receiver_email == sender_email:
                continue
            if not bool(getattr(account, 'IsAccount', False)):
                continue

            same_party = (
                local_party_id > 0
                and int(getattr(getattr(account, 'AgentPartyData', None), 'PartyID', 0) or 0) == local_party_id
            )
            same_group = (
                not same_party
                and local_group_id > 0
                and int(getattr(account, 'IsolationGroupID', 0) or 0) == local_group_id
            )
            if not same_party and not same_group:
                continue

            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                receiver_email,
                SharedCommandType.SetHeadlessLooting,
                (1.0 if enabled else 0.0, 0.0, 0.0, 0.0),
            )
            sent_any = True
        return sent_any

    def _disable_heroai_widget_for_headless(self: _BottingTreeHeroAIHost) -> bool:
        try:
            widget_handler = get_widget_handler()
            widget = self._get_heroai_widget()
            if widget is not None and bool(widget.enabled):
                widget_handler.disable_widget(self._get_heroai_widget_toggle_name())
                self._headless_disabled_heroai_widget = True
                return True
        except Exception:
            return False
        return False

    def _restore_heroai_widget_after_headless(self: _BottingTreeHeroAIHost) -> bool:
        if not bool(getattr(self, '_headless_disabled_heroai_widget', False)):
            return False
        try:
            widget_handler = get_widget_handler()
            widget = self._get_heroai_widget()
            if widget is not None and not bool(widget.enabled):
                widget_handler.enable_widget(self._get_heroai_widget_toggle_name())
            self._headless_disabled_heroai_widget = False
            return True
        except Exception:
            return False

    def SetHeadlessHeroAIEnabled(self: _BottingTreeHeroAIHost, enabled: bool, reset_runtime: bool = True):
        self.headless_heroai_enabled = enabled
        self._last_heroai_state = None
        self.ApplyAccountIsolation()
        self._sync_multibox_heroai_widget(bool(enabled and self.started and not self.paused))
        if reset_runtime:
            self.headless_heroai.reset()
            bb = self.blackboard
            bb['COMBAT_ACTIVE'] = False
            bb['LOOTING_ACTIVE'] = False
            bb['PAUSE_MOVEMENT'] = False
            bb['USER_INTERRUPT_ACTIVE'] = False
            bb['HEROAI_SUCCESS'] = False
            bb['HEROAI_STATUS'] = HeroAIStatus.DISABLED.value if not enabled else ''

    def EnableHeadlessHeroAI(self: _BottingTreeHeroAIHost, reset_runtime: bool = True) -> None:
        self.SetHeadlessHeroAIEnabled(True, reset_runtime=reset_runtime)

    def DisableHeadlessHeroAI(self: _BottingTreeHeroAIHost, reset_runtime: bool = True) -> None:
        self.SetHeadlessHeroAIEnabled(False, reset_runtime=reset_runtime)

    def ToggleHeadlessHeroAI(self: _BottingTreeHeroAIHost, reset_runtime: bool = True) -> bool:
        new_state = not self.headless_heroai_enabled
        self.SetHeadlessHeroAIEnabled(new_state, reset_runtime=reset_runtime)
        return new_state

    def SetLootingEnabled(self: _BottingTreeHeroAIHost, enabled: bool) -> bool:
        self.looting_enabled = enabled
        self.blackboard['looting_enabled'] = enabled
        self.headless_heroai.SetLootingEnabled(enabled)
        return True

    def EnableLooting(self: _BottingTreeHeroAIHost) -> bool:
        return self.SetLootingEnabled(True)

    def DisableLooting(self: _BottingTreeHeroAIHost) -> bool:
        return self.SetLootingEnabled(False)

    def ToggleLooting(self: _BottingTreeHeroAIHost) -> bool:
        self.SetLootingEnabled(not self.looting_enabled)
        return self.looting_enabled

    def IsLootingEnabled(self: _BottingTreeHeroAIHost) -> bool:
        return self.looting_enabled

    def RestoreHeroAIOptions(self: _BottingTreeHeroAIHost) -> bool:
        cached_data = self.headless_heroai.cached_data
        changed = False

        def _ensure_core_options_on(options: HeroAIOptionStruct) -> tuple[HeroAIOptionStruct, bool]:
            local_changed = False
            if not bool(options.Following):
                options.Following = True
                local_changed = True
            if not bool(options.Avoidance):
                options.Avoidance = True
                local_changed = True
            if not bool(options.Targeting):
                options.Targeting = True
                local_changed = True
            if not bool(options.Combat):
                options.Combat = True
                local_changed = True
            for skill_index in range(SHMEM_MAX_NUMBER_OF_SKILLS):
                if not bool(options.Skills[skill_index]):
                    options.Skills[skill_index] = True
                    local_changed = True
            return options, local_changed

        account_options, account_changed = _ensure_core_options_on(cached_data.account_options or HeroAIOptionStruct())
        global_options, global_changed = _ensure_core_options_on(cached_data.global_options or HeroAIOptionStruct())
        cached_data.account_options = account_options
        cached_data.global_options = global_options
        changed = bool(account_changed or global_changed)

        account_email = Player.GetAccountEmail()
        if not account_email:
            return changed

        shared_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        if shared_options is None:
            return changed

        shared_options, shared_changed = _ensure_core_options_on(shared_options)
        if shared_changed:
            GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, shared_options)
            changed = True
        cached_data.account_options = shared_options
        return changed

    def _heroai_options_match_runtime_policy(self: _BottingTreeHeroAIHost) -> bool:
        cached_options = self.headless_heroai.cached_data.account_options
        if cached_options is not None:
            if not all([
                bool(cached_options.Following),
                bool(cached_options.Avoidance),
                bool(cached_options.Targeting),
                bool(cached_options.Combat),
            ]):
                return False
            if not all(bool(cached_options.Skills[skill_index]) for skill_index in range(SHMEM_MAX_NUMBER_OF_SKILLS)):
                return False

        account_email = Player.GetAccountEmail()
        if not account_email:
            return True

        shared_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        if shared_options is None:
            return True

        return all([
            bool(shared_options.Following),
            bool(shared_options.Avoidance),
            bool(shared_options.Targeting),
            bool(shared_options.Combat),
        ]) and all(bool(shared_options.Skills[skill_index]) for skill_index in range(SHMEM_MAX_NUMBER_OF_SKILLS))

    def EnsureHeroAIOptionsEnabled(self: _BottingTreeHeroAIHost) -> bool:
        if self._heroai_options_match_runtime_policy():
            return True
        return self.RestoreHeroAIOptions()

    @staticmethod
    def GetHeroAiSetEnabledTree(
        enabled: bool,
        reset_runtime: bool = True,
        name: str | None = None,
    ) -> BehaviorTree:
        node_name = name or ('EnableHeadlessHeroAI' if enabled else 'DisableHeadlessHeroAI')

        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            node.blackboard['headless_heroai_enabled_request'] = enabled
            node.blackboard['headless_heroai_reset_runtime_request'] = reset_runtime
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
        return BottingTreeHeroAIMixin.GetHeroAiSetEnabledTree(
            True,
            reset_runtime=reset_runtime,
            name='EnableHeadlessHeroAI',
        )

    @staticmethod
    def DisableHeroAITree(reset_runtime: bool = True) -> BehaviorTree:
        return BottingTreeHeroAIMixin.GetHeroAiSetEnabledTree(
            False,
            reset_runtime=reset_runtime,
            name='DisableHeadlessHeroAI',
        )

    @staticmethod
    def ToggleHeroAITree(reset_runtime: bool = True) -> BehaviorTree:
        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            current_enabled = bool(node.blackboard.get('headless_heroai_enabled', True))
            node.blackboard['headless_heroai_enabled_request'] = not current_enabled
            node.blackboard['headless_heroai_reset_runtime_request'] = reset_runtime
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name='ToggleHeadlessHeroAI',
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )

    @staticmethod
    def GetLootingSetEnabledTree(
        enabled: bool,
        name: str | None = None,
    ) -> BehaviorTree:
        node_name = name or ('EnableLooting' if enabled else 'DisableLooting')

        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            node.blackboard['looting_enabled_request'] = enabled
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
        return BottingTreeHeroAIMixin.GetLootingSetEnabledTree(
            True,
            name='EnableLooting',
        )

    @staticmethod
    def DisableLootingTree() -> BehaviorTree:
        return BottingTreeHeroAIMixin.GetLootingSetEnabledTree(
            False,
            name='DisableLooting',
        )

    @staticmethod
    def ToggleLootingTree() -> BehaviorTree:
        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            current_enabled = bool(node.blackboard.get('looting_enabled', True))
            node.blackboard['looting_enabled_request'] = not current_enabled
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name='ToggleLooting',
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )

    def IsHeadlessHeroAIEnabled(self: _BottingTreeHeroAIHost) -> bool:
        return self.headless_heroai_enabled
