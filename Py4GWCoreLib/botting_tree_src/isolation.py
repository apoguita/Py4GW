import Py4GW

from ..GlobalCache import GLOBAL_CACHE
from ..Player import Player
from ..py4gwcorelib_src.BehaviorTree import BehaviorTree


class BottingTreeIsolationMixin:
    def _resolve_isolation_group_id(self, account_email: str) -> int:
        import zlib

        account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if account is not None:
            existing_group_id = int(getattr(account, 'IsolationGroupID', 0) or 0)
            if existing_group_id > 0:
                return existing_group_id
            party_id = int(getattr(account.AgentPartyData, 'PartyID', 0) or 0)
            if party_id > 0:
                return party_id

        deterministic_group = int(zlib.crc32(str(account_email).encode('utf-8')) % 1_000_000)
        return max(1, deterministic_group)

    def _sync_party_isolation_group(self, account_email: str, group_id: int) -> bool:
        local_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
        if local_account is None:
            return False

        local_party_id = int(getattr(local_account.AgentPartyData, 'PartyID', 0) or 0)
        if local_party_id <= 0:
            return False

        changed = False
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if not bool(getattr(account, 'IsAccount', False)):
                continue

            other_email = str(getattr(account, 'AccountEmail', '') or '').strip()
            if not other_email:
                continue

            other_party_id = int(getattr(account.AgentPartyData, 'PartyID', 0) or 0)
            if other_party_id != local_party_id:
                continue

            other_group_id = int(getattr(account, 'IsolationGroupID', 0) or 0)
            if other_group_id != group_id:
                changed = bool(GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(other_email, group_id)) or changed

            if not bool(getattr(account, 'IsIsolated', False)):
                changed = bool(GLOBAL_CACHE.ShMem.SetAccountIsolationByEmail(other_email, True)) or changed

        return changed

    def _capture_isolation_state_for_restore(self) -> None:
        account_email = Player.GetAccountEmail()
        if not account_email:
            self._previous_isolation_state = None
            self._previous_isolation_group_id = None
            return
        self._previous_isolation_state = bool(GLOBAL_CACHE.ShMem.IsAccountIsolated(account_email))
        self._previous_isolation_group_id = int(GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(account_email) or 0)

    def ApplyAccountIsolation(self) -> bool:
        account_email = Player.GetAccountEmail()
        if not account_email:
            return False

        changed = False
        current_isolated = bool(GLOBAL_CACHE.ShMem.IsAccountIsolated(account_email))
        if current_isolated != bool(self.isolation_enabled):
            changed = bool(GLOBAL_CACHE.ShMem.SetAccountIsolationByEmail(account_email, self.isolation_enabled)) or changed

        if self.isolation_enabled:
            target_group_id = self._resolve_isolation_group_id(account_email)
            current_group_id = int(GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(account_email) or 0)
            if current_group_id != target_group_id:
                changed = bool(GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(account_email, target_group_id)) or changed
            changed = self._sync_party_isolation_group(account_email, target_group_id) or changed
        else:
            current_group_id = int(GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(account_email) or 0)
            if current_group_id != 0:
                changed = bool(GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(account_email, 0)) or changed

        if changed:
            Py4GW.Console.Log(
                'BottingTree',
                f"Account isolation {'enabled' if self.isolation_enabled else 'disabled'} for {account_email}.",
                Py4GW.Console.MessageType.Info,
            )
        return bool(changed)

    def RestoreAccountIsolation(self) -> bool:
        if not self.restore_isolation_on_stop:
            return False

        account_email = Player.GetAccountEmail()
        if not account_email or self._previous_isolation_state is None:
            return False

        changed = False
        current_isolated = bool(GLOBAL_CACHE.ShMem.IsAccountIsolated(account_email))
        if current_isolated != bool(self._previous_isolation_state):
            changed = bool(GLOBAL_CACHE.ShMem.SetAccountIsolationByEmail(
                account_email,
                self._previous_isolation_state,
            )) or changed

        restore_group_id = int(self._previous_isolation_group_id or 0)
        current_group_id = int(GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(account_email) or 0)
        if current_group_id != restore_group_id:
            changed = bool(GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(account_email, restore_group_id)) or changed

        if changed:
            Py4GW.Console.Log(
                'BottingTree',
                f"Account isolation restored to {'enabled' if self._previous_isolation_state else 'disabled'} for {account_email}.",
                Py4GW.Console.MessageType.Info,
            )
        self._previous_isolation_state = None
        self._previous_isolation_group_id = None
        return bool(changed)

    def SetIsolationEnabled(self, enabled: bool) -> bool:
        self.isolation_enabled = enabled
        return self.ApplyAccountIsolation()

    def EnableIsolation(self) -> bool:
        return self.SetIsolationEnabled(True)

    def DisableIsolation(self) -> bool:
        return self.SetIsolationEnabled(False)

    def ToggleIsolation(self) -> bool:
        self.isolation_enabled = not self.isolation_enabled
        self.ApplyAccountIsolation()
        return self.isolation_enabled

    def IsIsolationEnabled(self) -> bool:
        return self.isolation_enabled

    def SetRestoreIsolationOnStop(self, enabled: bool) -> None:
        self.restore_isolation_on_stop = enabled

    @staticmethod
    def GetIsolationSetEnabledTree(
        enabled: bool,
        name: str | None = None,
    ) -> BehaviorTree:
        node_name = name or ('EnableIsolation' if enabled else 'DisableIsolation')

        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            node.blackboard['account_isolation_enabled_request'] = enabled
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=node_name,
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )

    @staticmethod
    def EnableIsolationTree() -> BehaviorTree:
        return BottingTreeIsolationMixin.GetIsolationSetEnabledTree(
            True,
            name='EnableIsolation',
        )

    @staticmethod
    def DisableIsolationTree() -> BehaviorTree:
        return BottingTreeIsolationMixin.GetIsolationSetEnabledTree(
            False,
            name='DisableIsolation',
        )

    @staticmethod
    def ToggleIsolationTree() -> BehaviorTree:
        def _request_toggle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            current_enabled = bool(node.blackboard.get('account_isolation_enabled', True))
            node.blackboard['account_isolation_enabled_request'] = not current_enabled
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name='ToggleIsolation',
                action_fn=_request_toggle,
                aftercast_ms=0,
            )
        )
