from typing import TYPE_CHECKING

import Py4GW

from ..Agent import Agent
from ..Map import Map
from ..Player import Player
from ..Quest import Quest
from ..native_src.internals.types import PointOrPath
from ..native_src.internals.types import PointPath
from ..py4gwcorelib_src.BehaviorTree import BehaviorTree
from ..py4gwcorelib_src.Utils import Utils
from ..routines_src.Agents import Agents as RoutinesAgents
from ..routines_src.BehaviourTrees import BT as RoutinesBT

if TYPE_CHECKING:
    from ..BottingTree import BottingTree


class _BottingTreeRoutines:
    def __init__(self, parent: 'BottingTree'):
        self.parent = parent

    def HandleQuest(
        self,
        quest_id: int,
        point_or_path: PointOrPath,
        quest_dialog: int | str,
        mode: str = 'accept',
        quest_npc: int = 0,
        multi: int = 0,
        aftercast_ms: int = 125,
        success_map_id: int = 0,
    ) -> BehaviorTree:
        final_point = PointPath.final_point(point_or_path)
        if final_point is None:
            raise ValueError('HandleQuest requires a non-empty point_or_path.')

        state = {
            'npc_id': 0,
            'current_map': 0,
            'initial_active_quest_id': 0,
            'initialized': False,
            'initial_npc_has_quest': False,
            'attempt_tree': None,
            'attempt_started': False,
            'tick_count': 0,
            'last_status_log_tick': -1,
        }

        def _log(message: str, message_type=Py4GW.Console.MessageType.Info) -> None:
            Py4GW.Console.Log(
                'HandleQuest',
                f'quest={quest_id} mode={mode} {message}',
                message_type,
            )

        def _format_runtime_snapshot() -> str:
            player_x, player_y = Player.GetXY()
            target_id = int(Player.GetTargetID() or 0)
            active_quest_id = int(Quest.GetActiveQuest() or 0)
            endpoint_distance = Utils.Distance((player_x, player_y), (final_point.x, final_point.y))
            npc_id = int(state['npc_id'] or 0)
            npc_distance = -1.0
            npc_xy = (0.0, 0.0)
            has_quest = False
            if npc_id != 0:
                npc_xy = Agent.GetXY(npc_id)
                npc_distance = Utils.Distance((player_x, player_y), npc_xy)
                has_quest = bool(Agent.HasQuest(npc_id))
            return (
                f'map={int(Map.GetMapID() or 0)} active_quest={active_quest_id} '
                f'player=({player_x:.2f},{player_y:.2f}) end=({final_point.x:.2f},{final_point.y:.2f}) '
                f'end_dist={endpoint_distance:.2f} npc_id={npc_id} npc_xy=({npc_xy[0]:.2f},{npc_xy[1]:.2f}) '
                f'npc_dist={npc_distance:.2f} target_id={target_id} npc_has_quest={has_quest}'
            )

        def _reset_state() -> None:
            state['npc_id'] = 0
            state['current_map'] = 0
            state['initial_active_quest_id'] = 0
            state['initialized'] = False
            state['initial_npc_has_quest'] = False
            state['attempt_tree'] = None
            state['attempt_started'] = False
            state['tick_count'] = 0
            state['last_status_log_tick'] = -1

        def _initialize_target(node: BehaviorTree.Node) -> None:
            state['current_map'] = int(Map.GetMapID() or 0)
            state['initial_active_quest_id'] = int(Quest.GetActiveQuest() or 0)
            if quest_npc != 0:
                state['npc_id'] = int(RoutinesAgents.GetAgentIDByModelID(quest_npc) or 0)
            else:
                state['npc_id'] = int(RoutinesAgents.GetNearestNPCXY(final_point.x, final_point.y, 200) or 0)
            state['initial_npc_has_quest'] = bool(state['npc_id'] != 0 and Agent.HasQuest(state['npc_id']))
            state['initialized'] = True
            node.blackboard['handlequest_quest_id'] = int(quest_id)
            node.blackboard['handlequest_mode'] = mode
            node.blackboard['handlequest_initial_map_id'] = int(state['current_map'])
            node.blackboard['handlequest_initial_active_quest_id'] = int(state['initial_active_quest_id'])
            node.blackboard['handlequest_npc_id'] = int(state['npc_id'])
            node.blackboard['handlequest_initial_npc_has_quest'] = bool(state['initial_npc_has_quest'])
            node.blackboard['handlequest_success_map_id'] = int(success_map_id)
            node.blackboard['handlequest_attempt_started'] = False
            _log(f'initialized target. success_map_id={success_map_id} multi={multi} snapshot={_format_runtime_snapshot()}')

        def _success_condition(node: BehaviorTree.Node) -> bool:
            initial_map_id = int(node.blackboard.get('handlequest_initial_map_id', state['current_map']) or 0)
            initial_active_quest_id = int(
                node.blackboard.get('handlequest_initial_active_quest_id', state['initial_active_quest_id']) or 0
            )
            initial_npc_has_quest = bool(
                node.blackboard.get('handlequest_initial_npc_has_quest', state['initial_npc_has_quest'])
            )
            attempt_started = bool(node.blackboard.get('handlequest_attempt_started', state['attempt_started']))
            current_map_id = int(Map.GetMapID() or 0)
            current_active_quest_id = int(Quest.GetActiveQuest() or 0)
            if success_map_id != 0 and int(Map.GetMapID() or 0) == int(success_map_id):
                return True
            if mode == 'complete':
                return current_active_quest_id != int(quest_id)
            if mode in ('step', 'skip'):
                if current_map_id != initial_map_id:
                    return True
                if not attempt_started:
                    return False
                if current_active_quest_id != initial_active_quest_id:
                    return True
                if state['npc_id'] != 0 and initial_npc_has_quest and not Agent.HasQuest(state['npc_id']):
                    return True
                return False
            return current_active_quest_id == int(quest_id)

        def _build_attempt_tree() -> BehaviorTree:
            _log(f'building attempt tree. snapshot={_format_runtime_snapshot()}')
            attempt_children: list[BehaviorTree.Node] = [
                BehaviorTree.Node._coerce_node(
                    RoutinesBT.Composite.Sequence(
                        RoutinesBT.Movement.MoveAndTargetPath(
                            pos=point_or_path,
                            target_distance=200.0,
                            move_tolerance=150.0,
                            log=False,
                        ),
                        RoutinesBT.Player.Wait(duration_ms=500, log=False),
                        RoutinesBT.Player.InteractTarget(log=False),
                        RoutinesBT.Player.SendDialog(dialog_id=quest_dialog, log=False),
                        name='HandleQuestDialog',
                    )
                )
            ]
            if multi != 0:
                attempt_children.append(
                    BehaviorTree.Node._coerce_node(
                        RoutinesBT.Player.SendDialog(dialog_id=multi, log=False)
                    )
                )
            attempt_children.append(
                BehaviorTree.Node._coerce_node(
                    RoutinesBT.Player.Wait(duration_ms=250, log=False)
                )
            )
            return BehaviorTree(
                BehaviorTree.SequenceNode(
                    name=f'HandleQuestAttempt({quest_id},{mode})',
                    children=attempt_children,
                )
            )

        def _quest_loop(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            state['tick_count'] += 1
            if not state['initialized']:
                _initialize_target(node)

            if _success_condition(node):
                _log(f'success condition met before/without attempt completion. snapshot={_format_runtime_snapshot()}', Py4GW.Console.MessageType.Success)
                _reset_state()
                return BehaviorTree.NodeState.SUCCESS

            if state['attempt_tree'] is None:
                state['attempt_tree'] = _build_attempt_tree()
                state['attempt_started'] = True
                node.blackboard['handlequest_attempt_started'] = True

            attempt_tree = state['attempt_tree']
            if attempt_tree is None:
                raise RuntimeError('QuestLoop attempt tree failed to initialize.')

            attempt_tree.blackboard = node.blackboard
            attempt_result = BehaviorTree.Node._normalize_state(attempt_tree.tick())
            if attempt_result == BehaviorTree.NodeState.RUNNING:
                tick_count = int(state['tick_count'])
                if state['last_status_log_tick'] < 0 or tick_count - int(state['last_status_log_tick']) >= 8:
                    state['last_status_log_tick'] = tick_count
                    _log(f'attempt still running. tick={tick_count} snapshot={_format_runtime_snapshot()}')
            if attempt_result == BehaviorTree.NodeState.RUNNING:
                return BehaviorTree.NodeState.RUNNING

            _log(f'attempt finished with {attempt_result}. snapshot={_format_runtime_snapshot()}')
            state['attempt_tree'] = None

            if _success_condition(node):
                _log(f'success condition met after attempt completion. snapshot={_format_runtime_snapshot()}', Py4GW.Console.MessageType.Success)
                _reset_state()
                return BehaviorTree.NodeState.SUCCESS

            _log(
                'attempt ended but success condition is still false; resetting attempt state and retrying. '
                f'snapshot={_format_runtime_snapshot()}',
                Py4GW.Console.MessageType.Warning,
            )
            state['attempt_tree'] = None
            return BehaviorTree.NodeState.RUNNING

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name=f'HandleQuest({quest_id},{mode})',
                action_fn=_quest_loop,
                aftercast_ms=aftercast_ms,
            )
        )


BottingTreeRoutines = _BottingTreeRoutines
