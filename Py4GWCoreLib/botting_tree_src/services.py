import time

from ..GlobalCache import GLOBAL_CACHE
from ..Routines import Routines
from ..py4gwcorelib_src.BehaviorTree import BehaviorTree


class BottingTreeServicesMixin:
    @staticmethod
    def PartyWipeRecoveryServiceTree(
        default_step_name: str | None = None,
        return_interval_ms: float = 1000.0,
    ) -> BehaviorTree:
        state = {
            'active': False,
            'step_name': '',
            'last_return_ms': 0.0,
        }

        def _reset_state(node: BehaviorTree.Node) -> None:
            state['active'] = False
            state['step_name'] = ''
            state['last_return_ms'] = 0.0
            node.blackboard['party_wipe_recovery_active'] = False

        def _tick_party_wipe_service(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            from ..Map import Map
            from ..py4gwcorelib_src.ActionQueue import ActionQueueManager

            now = time.monotonic() * 1000.0
            is_wiped = bool(Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated())

            if not state['active']:
                if not is_wiped:
                    node.blackboard['party_wipe_recovery_active'] = False
                    return BehaviorTree.NodeState.RUNNING

                step_name = str(node.blackboard.get('current_step_name', '') or '')
                if not step_name:
                    step_name = str(default_step_name or '')

                state['active'] = True
                state['step_name'] = step_name
                state['last_return_ms'] = 0.0
                node.blackboard['party_wipe_recovery_active'] = True
                node.blackboard['party_wipe_recovery_step_name'] = step_name
                ActionQueueManager().ResetAllQueues()
                return BehaviorTree.NodeState.RUNNING

            node.blackboard['party_wipe_recovery_active'] = True
            node.blackboard['party_wipe_recovery_step_name'] = state['step_name']

            if Map.IsMapReady() and Map.IsOutpost() and GLOBAL_CACHE.Party.IsPartyLoaded():
                if state['step_name']:
                    node.blackboard['restart_step_name_request'] = state['step_name']
                _reset_state(node)
                return BehaviorTree.NodeState.SUCCESS

            if now - float(state['last_return_ms']) >= float(return_interval_ms):
                GLOBAL_CACHE.Party.ReturnToOutpost()
                state['last_return_ms'] = now

            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name='PartyWipeRecoveryService',
                action_fn=_tick_party_wipe_service,
                aftercast_ms=0,
            )
        )
