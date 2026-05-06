from ..GlobalCache import GLOBAL_CACHE
from ..Player import Player
from ..py4gwcorelib_src.BehaviorTree import BehaviorTree
from ..py4gwcorelib_src.WidgetManager import get_widget_handler
from .enums import HeroAIStatus


class BottingTreeHeroAIMixin:
    _HEROAI_WIDGET_NAME = 'HeroAI'

    def _disable_heroai_widget_for_headless(self) -> bool:
        try:
            widget_handler = get_widget_handler()
            if bool(widget_handler.is_widget_enabled(self._HEROAI_WIDGET_NAME)):
                widget_handler.disable_widget(self._HEROAI_WIDGET_NAME)
                self._headless_disabled_heroai_widget = True
                return True
        except Exception:
            return False
        return False

    def _restore_heroai_widget_after_headless(self) -> bool:
        if not bool(getattr(self, '_headless_disabled_heroai_widget', False)):
            return False
        try:
            widget_handler = get_widget_handler()
            if not bool(widget_handler.is_widget_enabled(self._HEROAI_WIDGET_NAME)):
                widget_handler.enable_widget(self._HEROAI_WIDGET_NAME)
            self._headless_disabled_heroai_widget = False
            return True
        except Exception:
            return False

    def SetHeadlessHeroAIEnabled(self, enabled: bool, reset_runtime: bool = True):
        self.headless_heroai_enabled = enabled
        self._last_heroai_state = None
        self.ApplyAccountIsolation()
        if enabled:
            self._disable_heroai_widget_for_headless()
        else:
            self._restore_heroai_widget_after_headless()
        if reset_runtime:
            self.headless_heroai.reset()
            bb = self.blackboard
            bb['COMBAT_ACTIVE'] = False
            bb['LOOTING_ACTIVE'] = False
            bb['PAUSE_MOVEMENT'] = False
            bb['USER_INTERRUPT_ACTIVE'] = False
            bb['HEROAI_SUCCESS'] = False
            bb['HEROAI_STATUS'] = HeroAIStatus.DISABLED.value if not enabled else ''

    def EnableHeadlessHeroAI(self, reset_runtime: bool = True) -> None:
        self.SetHeadlessHeroAIEnabled(True, reset_runtime=reset_runtime)

    def DisableHeadlessHeroAI(self, reset_runtime: bool = True) -> None:
        self.SetHeadlessHeroAIEnabled(False, reset_runtime=reset_runtime)

    def ToggleHeadlessHeroAI(self, reset_runtime: bool = True) -> bool:
        new_state = not self.headless_heroai_enabled
        self.SetHeadlessHeroAIEnabled(new_state, reset_runtime=reset_runtime)
        return new_state

    def SetLootingEnabled(self, enabled: bool) -> bool:
        self.looting_enabled = enabled
        self.blackboard['looting_enabled'] = enabled

        self.headless_heroai.cached_data.account_options.Looting = enabled
        self.headless_heroai.cached_data.global_options.Looting = enabled

        account_email = Player.GetAccountEmail()
        if not account_email:
            return False

        account_options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        if account_options is None:
            return False

        account_options.Looting = enabled
        GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, account_options)
        return True

    def EnableLooting(self) -> bool:
        return self.SetLootingEnabled(True)

    def DisableLooting(self) -> bool:
        return self.SetLootingEnabled(False)

    def ToggleLooting(self) -> bool:
        self.SetLootingEnabled(not self.looting_enabled)
        return self.looting_enabled

    def IsLootingEnabled(self) -> bool:
        return self.looting_enabled

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

    def IsHeadlessHeroAIEnabled(self) -> bool:
        return self.headless_heroai_enabled
