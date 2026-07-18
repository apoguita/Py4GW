import time
from typing import Callable

from ..GlobalCache import GLOBAL_CACHE
from ..Routines import Routines
from ..py4gwcorelib_src.BehaviorTree import BehaviorTree


class BottingTreeServicesMixin:
    @staticmethod
    def PartyWipeRecoveryServiceTree(
        default_step_name: str | Callable[[], str | None] | None = None,
        return_interval_ms: float = 1000.0,
    ) -> BehaviorTree:
        state = {
            'active': False,
            'step_name': '',
            'last_return_ms': 0.0,
            'player_was_dead': False,
            'player_dead_pos': None,
        }

        def _resolve_default_step_name() -> str:
            if callable(default_step_name):
                try:
                    resolved = default_step_name()
                except Exception:
                    resolved = None
            else:
                resolved = default_step_name
            return str(resolved or '')

        def _reset_state(node: BehaviorTree.Node) -> None:
            state['active'] = False
            state['step_name'] = ''
            state['last_return_ms'] = 0.0
            state['player_was_dead'] = False
            state['player_dead_pos'] = None
            node.blackboard['party_wipe_recovery_active'] = False

        def _detect_revive_teleport() -> bool:
            from ..Agent import Agent
            from ..Player import Player
            from ..enums_src.GameData_enums import Range
            from ..py4gwcorelib_src.Utils import Utils

            player_id = Player.GetAgentID()
            if not Agent.IsValid(player_id):
                state['player_was_dead'] = False
                state['player_dead_pos'] = None
                return False

            is_dead = bool(Agent.IsDead(player_id))
            if is_dead:
                current_pos = Agent.GetXY(player_id)
                if not state['player_was_dead']:
                    state['player_dead_pos'] = current_pos
                    state['player_was_dead'] = True
                    return False
                death_pos = state.get('player_dead_pos')
                if death_pos and Utils.Distance(death_pos, current_pos) > Range.Spellcast.value:
                    state['player_dead_pos'] = None
                    state['player_was_dead'] = False
                    return True
                state['player_was_dead'] = True
                return False

            if not state['player_was_dead']:
                return False

            state['player_was_dead'] = False
            death_pos = state.get('player_dead_pos')
            state['player_dead_pos'] = None
            if not death_pos:
                return False

            current_pos = Agent.GetXY(player_id)
            return Utils.Distance(death_pos, current_pos) > Range.Spellcast.value

        def _tick_party_wipe_service(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            from ..Map import Map
            from ..py4gwcorelib_src.ActionQueue import ActionQueueManager

            now = time.monotonic() * 1000.0
            if bool(node.blackboard.get('party_wipe_recovery_suppressed', False)):
                _reset_state(node)
                return BehaviorTree.NodeState.RUNNING
            revived_at_shrine = _detect_revive_teleport()
            is_wiped = bool(
                Routines.Checks.Party.IsPartyWiped()
                or GLOBAL_CACHE.Party.IsPartyDefeated()
                or revived_at_shrine
            )

            if not state['active']:
                if not is_wiped:
                    node.blackboard['party_wipe_recovery_active'] = False
                    return BehaviorTree.NodeState.RUNNING

                step_name = str(node.blackboard.get('current_step_name', '') or '')
                if not step_name:
                    step_name = _resolve_default_step_name()

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
                if not state['step_name']:
                    state['step_name'] = _resolve_default_step_name()
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
