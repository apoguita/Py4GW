"""Behavior-tree helpers shared by mission implementations."""

from __future__ import annotations

import time
from collections.abc import Callable

from Py4GWCoreLib import Agent
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import Item
from Py4GWCoreLib import Map
from Py4GWCoreLib import Player
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.Agents import Agents as RoutinesAgents
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT
from Py4GWCoreLib.routines_src.behaviourtrees_src.items import BTItems
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.RootTerm.consumables import CONSET_MODELS
from Sources.RootTerm.consumables import STONE_ENTRIES
from Sources.RootTerm.options import OPTIONS


def action(name: str, callback: Callable[[], object], aftercast_ms: int = 0) -> BehaviorTree:
    def _run() -> BehaviorTree.NodeState:
        callback()
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=_run,
            aftercast_ms=aftercast_ms,
        )
    )


def enter_mission(name: str, confirm_extra: bool = False) -> BehaviorTree:
    children: list[BehaviorTree] = [
        action(f'{name} Enter', Map.EnterChallenge, aftercast_ms=500),
    ]
    if confirm_extra:
        started_at = [0.0]

        def _confirm() -> BehaviorTree.NodeState:
            if started_at[0] == 0.0:
                started_at[0] = time.monotonic()
            if not Map.IsOutpost() or time.monotonic() - started_at[0] >= 5.0:
                started_at[0] = 0.0
                return BehaviorTree.NodeState.SUCCESS
            Map.ConfirmEnterChallenge()
            return BehaviorTree.NodeState.RUNNING

        children.extend(
            [
                BehaviorTree(
                    BehaviorTree.ActionNode(
                        name=f'{name} Confirm',
                        action_fn=_confirm,
                        aftercast_ms=100,
                    )
                ),
            ]
        )
    children.extend(
        [
            BT.WaitUntilOnExplorable(timeout_ms=30000),
            BT.Wait(1500),
        ]
    )
    return BT.Sequence(name=f'{name} Mission Entry', children=children)


def set_title(title_id: int) -> BehaviorTree:
    return RoutinesBT.Player.SetTitle(title_id=title_id, log=False)


def mission_consumables() -> BehaviorTree:
    children: list[BehaviorTree] = []
    if OPTIONS.use_essence:
        children.append(BTItems.UseConsumable(CONSET_MODELS['essence']))
    if OPTIONS.use_armor:
        children.append(BTItems.UseConsumable(CONSET_MODELS['armor']))
    if OPTIONS.use_grail:
        children.append(BTItems.UseConsumable(CONSET_MODELS['grail']))
    if OPTIONS.use_stone and STONE_ENTRIES:
        index = max(0, min(OPTIONS.stone_index, len(STONE_ENTRIES) - 1))
        children.append(BTItems.UseConsumable(STONE_ENTRIES[index][1]))
    if not children:
        return BT.Succeeder(name='No Mission Consumables')
    return BT.Sequence(name='Mission Consumables', children=children)


def pickup_nearby_items(name: str, distance: float = 2500.0, timeout_ms: int = 30000) -> BehaviorTree:
    deadline = [0.0]

    def _pickup() -> BehaviorTree.NodeState:
        if deadline[0] == 0.0:
            deadline[0] = time.monotonic() + (timeout_ms / 1000.0)
        if time.monotonic() >= deadline[0]:
            deadline[0] = 0.0
            return BehaviorTree.NodeState.SUCCESS

        try:
            player_x, player_y = Player.GetXY()
            nearest_id = 0
            nearest_distance_sq = distance * distance
            for item_agent_id in AgentArray.GetItemArray():
                item_x, item_y = Agent.GetXY(item_agent_id)
                distance_sq = (item_x - player_x) ** 2 + (item_y - player_y) ** 2
                if distance_sq <= nearest_distance_sq:
                    nearest_id = item_agent_id
                    nearest_distance_sq = distance_sq
        except Exception:
            nearest_id = 0

        if nearest_id == 0:
            deadline[0] = 0.0
            return BehaviorTree.NodeState.SUCCESS

        Player.Interact(nearest_id)
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=_pickup,
            aftercast_ms=350,
        )
    )


def pickup_model_item(
    model_id: int,
    name: str,
    distance: float = 2500.0,
    timeout_ms: int = 30000,
) -> BehaviorTree:
    state = {'deadline': 0.0, 'seen': False}

    def _pickup() -> BehaviorTree.NodeState:
        if state['deadline'] == 0.0:
            state['deadline'] = time.monotonic() + (timeout_ms / 1000.0)
            state['seen'] = False

        nearest_id = 0
        try:
            player_x, player_y = Player.GetXY()
            nearest_distance_sq = distance * distance
            for item_agent_id in AgentArray.GetItemArray():
                item_id = Agent.GetItemAgentItemID(item_agent_id)
                if item_id == 0 or Item.GetModelID(item_id) != model_id:
                    continue
                item_x, item_y = Agent.GetXY(item_agent_id)
                distance_sq = (item_x - player_x) ** 2 + (item_y - player_y) ** 2
                if distance_sq <= nearest_distance_sq:
                    nearest_id = item_agent_id
                    nearest_distance_sq = distance_sq
        except Exception:
            nearest_id = 0

        if nearest_id:
            state['seen'] = True
            Player.ChangeTarget(nearest_id)
            Player.Interact(nearest_id, False)
            return BehaviorTree.NodeState.RUNNING

        if state['seen'] or time.monotonic() >= state['deadline']:
            state['deadline'] = 0.0
            state['seen'] = False
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=_pickup,
            aftercast_ms=350,
        )
    )


def interact_gadget_id(
    gadget_id: int,
    pos: tuple[float, float],
    name: str,
    timeout_ms: int = 10000,
) -> BehaviorTree:
    deadline = [0.0]

    def _interact() -> BehaviorTree.NodeState:
        if deadline[0] == 0.0:
            deadline[0] = time.monotonic() + (timeout_ms / 1000.0)

        agent_id = RoutinesAgents.GetNearestGadgetByID(gadget_id, max_distance=2500.0)
        if agent_id:
            Player.ChangeTarget(agent_id)
            Player.Interact(agent_id, False)
            deadline[0] = 0.0
            return BehaviorTree.NodeState.SUCCESS

        if time.monotonic() >= deadline[0]:
            deadline[0] = 0.0
            return BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.RUNNING

    return BT.Sequence(
        name=name,
        children=[
            BT.Move(pos, pause_on_combat=False, tolerance=100.0),
            BehaviorTree(
                BehaviorTree.ActionNode(
                    name=f'{name} Interact',
                    action_fn=_interact,
                    aftercast_ms=500,
                )
            ),
        ],
    )


def interact_agent_id(
    agent_id: int,
    name: str,
    timeout_ms: int = 10000,
) -> BehaviorTree:
    state = {'deadline': 0.0, 'seen': False}

    def _interact() -> BehaviorTree.NodeState:
        if state['deadline'] == 0.0:
            state['deadline'] = time.monotonic() + (timeout_ms / 1000.0)
            state['seen'] = False

        if Agent.IsValid(agent_id):
            state['seen'] = True
            Player.ChangeTarget(agent_id)
            Player.Interact(agent_id, False)
            return BehaviorTree.NodeState.RUNNING

        if state['seen']:
            state['deadline'] = 0.0
            state['seen'] = False
            return BehaviorTree.NodeState.SUCCESS

        if time.monotonic() >= state['deadline']:
            state['deadline'] = 0.0
            return BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=_interact,
            aftercast_ms=350,
        )
    )


def interact_player_number(
    player_number: int,
    name: str,
    max_range: float = 3500.0,
    timeout_ms: int = 10000,
    aftercast_ms: int = 3000,
) -> BehaviorTree:
    deadline = [0.0]

    def _interact() -> BehaviorTree.NodeState:
        if deadline[0] == 0.0:
            deadline[0] = time.monotonic() + (timeout_ms / 1000.0)

        nearest_id = 0
        nearest_distance_sq = max_range * max_range
        try:
            player_x, player_y = Player.GetXY()
            candidate_ids = set(AgentArray.GetNPCMinipetArray())
            candidate_ids.update(AgentArray.GetAllyArray())
            for agent_id in candidate_ids:
                if Agent.GetPlayerNumber(agent_id) != player_number or Agent.IsDead(agent_id):
                    continue
                agent_x, agent_y = Agent.GetXY(agent_id)
                distance_sq = (agent_x - player_x) ** 2 + (agent_y - player_y) ** 2
                if distance_sq <= nearest_distance_sq:
                    nearest_id = agent_id
                    nearest_distance_sq = distance_sq
        except Exception:
            nearest_id = 0

        if nearest_id:
            Player.ChangeTarget(nearest_id)
            Player.Interact(nearest_id, False)
            deadline[0] = 0.0
            return BehaviorTree.NodeState.SUCCESS

        if time.monotonic() >= deadline[0]:
            deadline[0] = 0.0
            return BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=_interact,
            aftercast_ms=aftercast_ms,
        )
    )


def interact_nearest_npc(
    pos: tuple[float, float],
    name: str,
    max_distance: float = 1500.0,
    timeout_ms: int = 10000,
    aftercast_ms: int = 2000,
) -> BehaviorTree:
    deadline = [0.0]

    def _interact() -> BehaviorTree.NodeState:
        if deadline[0] == 0.0:
            deadline[0] = time.monotonic() + (timeout_ms / 1000.0)

        nearest_id = 0
        try:
            nearest_id = RoutinesAgents.GetNearestNPCXY(pos[0], pos[1], max_distance)
        except Exception:
            nearest_id = 0

        if nearest_id:
            Player.ChangeTarget(nearest_id)
            Player.Interact(nearest_id, False)
            deadline[0] = 0.0
            return BehaviorTree.NodeState.SUCCESS

        if time.monotonic() >= deadline[0]:
            deadline[0] = 0.0
            return BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.RUNNING

    return BT.Sequence(
        name=name,
        children=[
            BT.Move(pos, pause_on_combat=False, tolerance=150.0),
            BT.Wait(500),
            BehaviorTree(
                BehaviorTree.ActionNode(
                    name=f'{name} Interact',
                    action_fn=_interact,
                    aftercast_ms=aftercast_ms,
                )
            ),
        ],
    )


def skip_cinematic(name: str, wait_ms: int = 1000) -> BehaviorTree:
    return BT.Sequence(
        name=name,
        children=[
            BT.Wait(wait_ms),
            action(f'{name} Skip', lambda: Map.SkipCinematic() if Map.IsInCinematic() else None),
        ],
    )
