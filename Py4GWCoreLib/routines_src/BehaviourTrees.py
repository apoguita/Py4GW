
from Py4GWCoreLib.routines_src.Agents import Agents
from ..GlobalCache import GLOBAL_CACHE
from ..Py4GWcorelib import ConsoleLog, Console
from ..Map import Map
from ..Agent import Agent
from ..Player import Player
from ..enums_src.Title_enums import TITLE_NAME
from ..enums_src.Model_enums import ModelID
from ..UIManager import UIManager
from ..enums_src.GameData_enums import Range

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from enum import Enum, auto
from typing import Callable, cast

from .Checks import Checks

import importlib
import random

class _RProxy:
    def __getattr__(self, name: str):
        root_pkg = importlib.import_module("Py4GWCoreLib")
        return getattr(root_pkg.Routines, name)

Routines = _RProxy()


class BT:
    NodeState = BehaviorTree.NodeState
    #region composite nodes
    class Composite:
        SequenceBuildable = Callable[[], BehaviorTree | BehaviorTree.Node] | BehaviorTree | BehaviorTree.Node

        @staticmethod
        def _resolve_subtree_factory(subtree_or_builder: "BT.Composite.SequenceBuildable") -> BehaviorTree:
            subtree = subtree_or_builder() if callable(subtree_or_builder) else subtree_or_builder
            subtree = cast(BehaviorTree | BehaviorTree.Node, subtree)
            return BT.Composite._as_tree(subtree)

        @staticmethod
        def _as_tree(subtree: BehaviorTree | BehaviorTree.Node) -> BehaviorTree:
            if isinstance(subtree, BehaviorTree):
                return subtree
            if isinstance(subtree, BehaviorTree.Node):
                return BehaviorTree(subtree)
            raise TypeError("Composite helpers expect a BehaviorTree or BehaviorTree.Node.")

        @staticmethod
        def Sequence(*subtrees: BehaviorTree | BehaviorTree.Node, name: str = "CompositeSequence") -> BehaviorTree:
            children = [
                BehaviorTree.SubtreeNode(
                    name=f"Step{index + 1}",
                    subtree_fn=lambda node, subtree=subtree: BT.Composite._as_tree(subtree),
                )
                for index, subtree in enumerate(subtrees)
            ]
            return BehaviorTree(BehaviorTree.SequenceNode(name=name, children=children))

        @staticmethod
        def SequenceNames(steps: list[tuple[str, "BT.Composite.SequenceBuildable"]]) -> list[str]:
            return [step_name for step_name, _ in steps]

        @staticmethod
        def SequenceFrom(
            steps: list[tuple[str, "BT.Composite.SequenceBuildable"]],
            start_from: str | None = None,
            name: str = "NamedSequence",
        ) -> BehaviorTree:
            if not steps:
                return BehaviorTree(BehaviorTree.SequenceNode(name=name, children=[]))

            start_index = 0
            if start_from is not None:
                step_names = BT.Composite.SequenceNames(steps)
                if start_from not in step_names:
                    raise ValueError(f"Unknown sequence step '{start_from}'. Valid values: {', '.join(step_names)}")
                start_index = step_names.index(start_from)

            children = [
                BehaviorTree.SubtreeNode(
                    name=step_name,
                    subtree_fn=lambda node, subtree_or_builder=subtree_or_builder: BT.Composite._resolve_subtree_factory(subtree_or_builder),
                )
                for step_name, subtree_or_builder in steps[start_index:]
            ]
            return BehaviorTree(BehaviorTree.SequenceNode(name=name, children=children))

        @staticmethod
        def _MoveAndTarget(move_tree: BehaviorTree, target_tree: BehaviorTree) -> BehaviorTree:
            return BT.Composite.Sequence(
                move_tree,
                target_tree,
                name="MoveAndTarget",
            )

        @staticmethod
        def _TargetAndInteract(target_tree: BehaviorTree, log: bool = False) -> BehaviorTree:
            return BT.Composite.Sequence(
                target_tree,
                BT.Player.InteractTarget(log=log),
                name="TargetAndInteract",
            )

        @staticmethod
        def _MoveTargetAndInteract(move_tree: BehaviorTree, target_tree: BehaviorTree, log: bool = False) -> BehaviorTree:
            return BT.Composite.Sequence(
                move_tree,
                target_tree,
                BT.Player.InteractTarget(log=log),
                name="MoveTargetAndInteract",
            )

        @staticmethod
        def InteractAndDialog(dialog_id: str | int, log: bool = False) -> BehaviorTree:
            return BT.Composite.Sequence(
                BT.Player.InteractTarget(log=log),
                BT.Player.SendDialog(dialog_id=dialog_id, log=log),
                name="InteractAndDialog",
            )

        @staticmethod
        def InteractAndAutomaticDialog(button_number: int, log: bool = False) -> BehaviorTree:
            return BT.Composite.Sequence(
                BT.Player.InteractTarget(log=log),
                BT.Player.SendAutomaticDialog(button_number=button_number, log=log),
                name="InteractAndAutomaticDialog",
            )

        @staticmethod
        def _TargetInteractAndDialog(target_tree: BehaviorTree, dialog_id: str | int, log: bool = False) -> BehaviorTree:
            return BT.Composite.Sequence(
                target_tree,
                BT.Player.InteractTarget(log=log),
                BT.Player.SendDialog(dialog_id=dialog_id, log=log),
                name="TargetInteractAndDialog",
            )

        @staticmethod
        def _TargetInteractAndAutomaticDialog(
            target_tree: BehaviorTree,
            button_number: int,
            log: bool = False,
        ) -> BehaviorTree:
            return BT.Composite.Sequence(
                target_tree,
                BT.Player.InteractTarget(log=log),
                BT.Player.SendAutomaticDialog(button_number=button_number, log=log),
                name="TargetInteractAndAutomaticDialog",
            )

        @staticmethod
        def _MoveTargetInteractAndDialog(
            move_tree: BehaviorTree,
            target_tree: BehaviorTree,
            dialog_id: str | int,
            log: bool = False,
        ) -> BehaviorTree:
            return BT.Composite.Sequence(
                move_tree,
                target_tree,
                BT.Player.InteractTarget(log=log),
                BT.Player.SendDialog(dialog_id=dialog_id, log=log),
                name="MoveTargetInteractAndDialog",
            )

        @staticmethod
        def _MoveTargetInteractAndAutomaticDialog(
            move_tree: BehaviorTree,
            target_tree: BehaviorTree,
            button_number: int,
            log: bool = False,
        ) -> BehaviorTree:
            return BT.Composite.Sequence(
                move_tree,
                target_tree,
                BT.Player.InteractTarget(log=log),
                BT.Player.SendAutomaticDialog(button_number=button_number, log=log),
                name="MoveTargetInteractAndAutomaticDialog",
            )

        @staticmethod
        def MoveAndTarget(
            x: float,
            y: float,
            target_distance: float = Range.Adjacent.value,
            log: bool = False,
        ) -> BehaviorTree:
            return BT.Composite._MoveAndTarget(
                move_tree=BT.Player.Move(x=x, y=y, log=log),
                target_tree=BT.Agents.TargetNearestNPC(distance=target_distance, log=log),
            )

        @staticmethod
        def TargetAndInteract(target_distance: float = 4500.0, log: bool = False) -> BehaviorTree:
            return BT.Composite._TargetAndInteract(
                target_tree=BT.Agents.TargetNearestNPC(distance=target_distance, log=log),
                log=log,
            )

        @staticmethod
        def MoveTargetAndInteract(
            x: float,
            y: float,
            target_distance: float = Range.Adjacent.value,
            log: bool = False,
        ) -> BehaviorTree:
            return BT.Composite._MoveTargetAndInteract(
                move_tree=BT.Player.Move(x=x, y=y, log=log),
                target_tree=BT.Agents.TargetNearestNPC(distance=target_distance, log=log),
                log=log,
            )

        @staticmethod
        def TargetInteractAndDialog(
            target_distance: float = Range.Adjacent.value,
            dialog_id: str | int = 0,
            log: bool = False,
        ) -> BehaviorTree:
            return BT.Composite._TargetInteractAndDialog(
                target_tree=BT.Agents.TargetNearestNPC(distance=target_distance, log=log),
                dialog_id=dialog_id,
                log=log,
            )

        @staticmethod
        def TargetInteractAndAutomaticDialog(
            target_distance: float = Range.Adjacent.value,
            button_number: int = 0,
            log: bool = False,
        ) -> BehaviorTree:
            return BT.Composite._TargetInteractAndAutomaticDialog(
                target_tree=BT.Agents.TargetNearestNPC(distance=target_distance, log=log),
                button_number=button_number,
                log=log,
            )

        @staticmethod
        def MoveTargetInteractAndDialog(
            x: float,
            y: float,
            target_distance: float = Range.Adjacent.value,
            dialog_id: str | int = 0,
            log: bool = False,
        ) -> BehaviorTree:
            return BT.Composite._MoveTargetInteractAndDialog(
                move_tree=BT.Player.Move(x=x, y=y, log=log),
                target_tree=BT.Agents.TargetNearestNPC(distance=target_distance, log=log),
                dialog_id=dialog_id,
                log=log,
            )

        @staticmethod
        def MoveTargetInteractAndAutomaticDialog(
            x: float,
            y: float,
            target_distance: float = Range.Adjacent.value,
            button_number: int = 0,
            log: bool = False,
        ) -> BehaviorTree:
            return BT.Composite._MoveTargetInteractAndAutomaticDialog(
                move_tree=BT.Player.Move(x=x, y=y, log=log),
                target_tree=BT.Agents.TargetNearestNPC(distance=target_distance, log=log),
                button_number=button_number,
                log=log,
            )

    #region Player
    class Player:
        @staticmethod
        def InteractAgent(agent_id:int, log:bool=False):
            """
            Purpose: Interact with the specified agent.
            Args:
                agent_id (int): The ID of the agent to interact with.
                log (bool) Optional: Whether to log the action. Default is False.
            """
            def _interact_agent(agent_id:int):
                Player.Interact(agent_id, False)
                ConsoleLog("InteractAgent", f"Interacted with agent {agent_id}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="InteractAgent", action_fn=lambda: _interact_agent(agent_id), aftercast_ms=250)
            return BehaviorTree(tree)
            
        @staticmethod
        def InteractTarget(log:bool=False):
            """
            Purpose: Interact with the currently selected target.
            """
            def _get_target_id(node: BehaviorTree.Node):
                node.blackboard["target_id"] = Player.GetTargetID()
                if node.blackboard["target_id"] == 0:
                    ConsoleLog("InteractTarget", "No target selected.", Console.MessageType.Error, log=True)
                    return BehaviorTree.NodeState.FAILURE

                ConsoleLog("InteractTarget",
                        f"Target ID obtained: {node.blackboard['target_id']}.",
                        Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.SequenceNode(children=[
                BehaviorTree.ActionNode(
                    name="GetTargetID",
                    action_fn=lambda node:_get_target_id(node),
                    aftercast_ms=0
                ),

                #SubtreeNode factory receives *its own node* (with blackboard)
                BehaviorTree.SubtreeNode(
                    name="InteractAgent",
                    subtree_fn=lambda node: BT.Player.InteractAgent(
                        node.blackboard["target_id"],
                        log=log
                    ),
                ),
            ])

            return BehaviorTree(tree)

        @staticmethod
        def ChangeTarget(agent_id, log:bool=False):
            """
            Purpose: Change the player's target to the specified agent ID.
            Args:
                agent_id (int): The ID of the agent to target.
            Returns: None
            """
            def _change_target():
                if agent_id != 0:
                    Player.ChangeTarget(agent_id)
                    ConsoleLog("ChangeTarget", f"Changed target to agent {agent_id}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                
                ConsoleLog("ChangeTarget", "Invalid agent ID provided for targeting.", Console.MessageType.Error, log=log)
                return BehaviorTree.NodeState.FAILURE
            
            tree = BehaviorTree.ActionNode(name="ChangeTarget", action_fn=lambda: _change_target(), aftercast_ms=250)
            return BehaviorTree(tree)
        
        @staticmethod
        def SendDialog(dialog_id:str | int, log:bool=False):
            """
            Purpose: Send a dialog to the specified dialog ID.
            Args:
                dialog_id (str | int): The ID of the dialog to send.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _send_dialog(dialog_id):
                Player.SendDialog(dialog_id)
                ConsoleLog("SendDialog", f"Sent dialog {dialog_id}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SendDialog", action_fn=lambda: _send_dialog(dialog_id), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def SendAutomaticDialog(button_number: int, log: bool = False):
            """
            Purpose: Send the currently visible automatic dialog choice by button index.
            Args:
                button_number (int): Visible button index starting at 0.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _send_automatic_dialog(button_number: int):
                Player.SendAutomaticDialog(button_number)
                ConsoleLog(
                    "SendAutomaticDialog",
                    f"Sent automatic dialog button {button_number}.",
                    Console.MessageType.Info,
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.ActionNode(
                name="SendAutomaticDialog",
                action_fn=lambda: _send_automatic_dialog(button_number),
                aftercast_ms=300,
            )
            return BehaviorTree(tree)
        
        @staticmethod   
        def SetTitle(title_id:int, log:bool=False):
            """
            Purpose: Set the player's title to the specified title ID.
            Args:
                title_id (int): The ID of the title to set.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _set_title(title_id:int):
                Player.SetActiveTitle(title_id)
                ConsoleLog("SetTitle", f"Set title to {TITLE_NAME.get(title_id, 'Invalid')}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SetTitle", action_fn=lambda: _set_title(title_id), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def SendChatCommand(command:str, log=False):
            """
            Purpose: Send a chat command.
            Args:
                command (str): The chat command to send.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _send_chat_command(command:str):
                Player.SendChatCommand(command)
                ConsoleLog("SendChatCommand", f"Sent chat command: {command}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SendChatCommand", action_fn=lambda: _send_chat_command(command), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def BuySkill(skill_id: int, log: bool = False):
            """
            Purpose: Buy/Learn a skill from a Skill Trainer.
            Args:
                skill_id (int): The ID of the skill to purchase.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _buy_skill(skill_id: int):
                Player.BuySkill(skill_id)
                ConsoleLog("BuySkill", f"Buying skill {skill_id}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.ActionNode(name="BuySkill", action_fn=lambda: _buy_skill(skill_id), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def UnlockBalthazarSkill(skill_id: int, use_pvp_remap: bool = True, log: bool = False):
            """
            Purpose: Unlock a skill from the Priest of Balthazar vendor.
            Args:
                skill_id (int): The ID of the skill to unlock.
                use_pvp_remap (bool) Optional: Whether to remap via PvP skill id. Default is True.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _unlock_balthazar_skill(skill_id: int, use_pvp_remap: bool):
                Player.UnlockBalthazarSkill(skill_id, use_pvp_remap=use_pvp_remap)
                ConsoleLog(
                    "UnlockBalthazarSkill",
                    f"Unlocking Balthazar skill {skill_id} (use_pvp_remap={use_pvp_remap}).",
                    Console.MessageType.Info,
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.ActionNode(
                name="UnlockBalthazarSkill",
                action_fn=lambda: _unlock_balthazar_skill(skill_id, use_pvp_remap),
                aftercast_ms=300,
            )
            return BehaviorTree(tree)

        @staticmethod
        def Resign(log:bool=False):
            """
            Purpose: Resign from the current map.
            Args:
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _resign():
                Player.SendChatCommand("resign")
                ConsoleLog("Resign", "Resigned from party.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.ActionNode(name="Resign", action_fn=lambda: _resign(), aftercast_ms=250)
            return BehaviorTree(tree)

        @staticmethod
        def SendChatMessage(channel:str, message:str, log=False):
            """
            Purpose: Send a chat message to the specified channel.
            Args:
                channel (str): The channel to send the message to.
                message (str): The message to send.
                log (bool) Optional: Whether to log the action. Default is True.
            Returns: None
            """
            def _send_chat_message(channel:str, message:str):
                Player.SendChat(channel, message)
                ConsoleLog("SendChatMessage", f"Sent chat message to {channel}: {message}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SendChatMessage", action_fn=lambda: _send_chat_message(channel, message), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def PrintMessageToConsole(source:str, message: str, message_type: int = Console.MessageType.Info):
            """
            Purpose: Print a message to the console.
            Args:
                message (str): The message to print.
            Returns: None
            """
            def _print_message_to_console(source:str, message: str, message_type: int):
                ConsoleLog(source, message, message_type, log=True)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="PrintMessageToConsole", action_fn=lambda: _print_message_to_console(source, message, message_type), aftercast_ms=100)
            return BehaviorTree(tree)
        
        @staticmethod
        def Wait(duration_ms: int, log: bool = False):
            """
            Purpose: Wait for a specified duration.
            Args:
                duration_ms (int): The duration to wait in milliseconds.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: A BehaviorTree subtree.
            """
            def _wait_started():
                ConsoleLog("Wait", f"Waiting for {duration_ms}ms.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree(
                BehaviorTree.SequenceNode(
                    name="Wait",
                    children=[
                        BehaviorTree.ConditionNode(name="WaitStarted", condition_fn=_wait_started),
                        BehaviorTree.WaitForTimeNode(name="WaitForTime", duration_ms=duration_ms),
                    ],
                )
            )
            return tree

        #region Move
        @staticmethod
        def Move(
            x: float,
            y: float,
            tolerance: float = 50.0,
            timeout_ms: int = 5000,
            stall_threshold_ms: int = 500,
            pause_on_combat: bool = True,
            pause_flag_key: str = "PAUSE_MOVEMENT",
            log: bool = False,
        ):
            """
            Purpose: Move the player to the specified coordinates using autopathing.
            Args:
                x (float): The x coordinate.
                y (float): The y coordinate.
                tolerance (float): Arrival tolerance for each waypoint. Default is 50.0.
                timeout_ms (int): Timeout budget for the current waypoint.
                stall_threshold_ms (int): Time without progress before nudging again.
                pause_on_combat (bool): Pause while combat is active on the blackboard.
                pause_flag_key (str): Blackboard key used for external movement pauses.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: A BehaviorTree subtree.
            """
            state = {
                "path_gen": None,
                "path_points": None,
                "path_index": 0,
                "last_distance": None,
                "last_progress_ms": None,
                "move_issued": False,
                "completed": False,
                "result_state": "",
                "result_reason": "",
                "initial_map_id": None,
                "last_move_point": None,
                "pause_logged": False,
                "was_paused": False,
                "resume_recovery_active": False,
                "last_logged_waypoint_index": -1,
            }

            def _reset_runtime():
                state["path_gen"] = None
                state["path_points"] = None
                state["path_index"] = 0
                state["last_distance"] = None
                state["last_progress_ms"] = None
                state["move_issued"] = False
                state["initial_map_id"] = None
                state["last_move_point"] = None
                state["pause_logged"] = False
                state["was_paused"] = False
                state["resume_recovery_active"] = False
                state["last_logged_waypoint_index"] = -1

            def _reset_result():
                state["completed"] = False
                state["result_state"] = ""
                state["result_reason"] = ""

            def _set_blackboard(node: BehaviorTree.Node, move_state: str, reason: str = ""):
                path_points = [
                    (float(path_x), float(path_y))
                    for path_x, path_y in (state["path_points"] or [])
                ]
                current_waypoint = None
                current_waypoint_index = -1
                if state["path_points"] is not None and 0 <= state["path_index"] < len(state["path_points"]):
                    waypoint_x, waypoint_y = state["path_points"][state["path_index"]]
                    current_waypoint = (float(waypoint_x), float(waypoint_y))
                    current_waypoint_index = int(state["path_index"])

                node.blackboard["move_state"] = move_state
                node.blackboard["move_reason"] = reason
                node.blackboard["move_target"] = (x, y)
                total_points = len(path_points)
                node.blackboard["move_path_index"] = int(state["path_index"])
                node.blackboard["move_path_count"] = int(total_points)
                node.blackboard["move_path_points"] = path_points
                node.blackboard["move_current_waypoint"] = current_waypoint
                node.blackboard["move_current_waypoint_index"] = current_waypoint_index
                node.blackboard["move_last_move_point"] = state["last_move_point"]
                node.blackboard["move_resume_recovery_active"] = bool(state["resume_recovery_active"])

            def _debug_enabled(node: BehaviorTree.Node) -> bool:
                return log or (bool(node.blackboard.get("MOVE_DEBUG", False)) if node is not None else False)

            def _finalize_move(node: BehaviorTree.Node, move_state: str, reason: str = ""):
                state["completed"] = True
                state["result_state"] = move_state
                state["result_reason"] = reason
                if move_state == "failed":
                    ConsoleLog(
                        "Move",
                        f"Movement failed: reason={reason or 'unknown'}, target=({x}, {y}), path_index={state['path_index']}.",
                        Console.MessageType.Warning,
                        log=True,
                    )
                elif _debug_enabled(node):
                    ConsoleLog(
                        "Move",
                        f"Finalizing move with state={move_state}, reason={reason or 'none'}, path_index={state['path_index']}.",
                        Console.MessageType.Info if move_state == "finished" else Console.MessageType.Warning,
                        log=True,
                    )
                _set_blackboard(node, move_state, reason)
                _reset_runtime()

            def _get_pause_reason(node: BehaviorTree.Node) -> str:
                if pause_on_combat and bool(node.blackboard.get("COMBAT_ACTIVE", False)):
                    return "combat"
                if bool(node.blackboard.get(pause_flag_key, False)):
                    return "external_pause"
                if Checks.Player.IsCasting():
                    return "casting"
                return ""

            def _issue_move(target_x: float, target_y: float):
                move_x = target_x
                move_y = target_y
                last_move_point = state["last_move_point"]
                if last_move_point is not None:
                    last_x, last_y = last_move_point
                    if abs(move_x - last_x) <= 10 and abs(move_y - last_y) <= 10:
                        move_x += random.uniform(-5.0, 5.0)
                        move_y += random.uniform(-5.0, 5.0)
                Player.Move(move_x, move_y)
                state["last_move_point"] = (move_x, move_y)
                if log:
                    if move_x != target_x or move_y != target_y:
                        ConsoleLog(
                            "Move",
                            f"Moving to waypoint ({target_x}, {target_y}) with jittered point ({move_x}, {move_y}).",
                            Console.MessageType.Info,
                            log=log,
                        )
                    else:
                        ConsoleLog("Move", f"Moving to waypoint ({target_x}, {target_y}).", Console.MessageType.Info, log=log)

            def _move(node: BehaviorTree.Node):
                from ..Pathing import AutoPathing
                from ..Py4GWcorelib import Utils

                now = Utils.GetBaseTimestamp()
                if state["completed"] and state["result_state"] == "finished":
                    if log:
                        ConsoleLog("Move", f"Movement already finished ({state['result_reason']}).", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS

                if state["completed"] and state["result_state"] == "failed":
                    if log:
                        ConsoleLog("Move", f"Movement already failed ({state['result_reason']}).", Console.MessageType.Warning, log=log)
                    return BehaviorTree.NodeState.FAILURE

                if state["path_gen"] is None and state["path_points"] is None:
                    _reset_result()
                    state["initial_map_id"] = Map.GetMapID()
                    state["path_gen"] = AutoPathing().get_path_to(x, y)
                    if _debug_enabled(node):
                        ConsoleLog("Move", f"Starting autopath to ({x}, {y}).", Console.MessageType.Info, log=True)
                    _set_blackboard(node, "running")

                if state["path_gen"] is not None:
                    try:
                        next(state["path_gen"])
                        _set_blackboard(node, "running")
                        return BehaviorTree.NodeState.RUNNING
                    except StopIteration as path_result:
                        state["path_points"] = list(path_result.value or [])
                        state["path_gen"] = None
                        state["path_index"] = 0
                        state["move_issued"] = False
                        state["last_distance"] = None
                        state["last_progress_ms"] = now
                        state["pause_logged"] = False
                        state["last_logged_waypoint_index"] = -1

                        if _debug_enabled(node):
                            ConsoleLog(
                                "Move",
                                f"Autopath resolved with {len(state['path_points'])} points to ({x}, {y}).",
                                Console.MessageType.Info,
                                log=True,
                            )

                        current_pos = Player.GetXY()
                        if Utils.Distance(current_pos, (x, y)) <= tolerance:
                            if _debug_enabled(node):
                                ConsoleLog("Move", "Already within tolerance of destination.", Console.MessageType.Success, log=True)
                            _finalize_move(node, "finished")
                            return BehaviorTree.NodeState.SUCCESS

                        if len(state["path_points"]) == 0:
                            if _debug_enabled(node):
                                ConsoleLog("Move", "Autopath returned no path points; failing because there is no path to follow.", Console.MessageType.Warning, log=True)
                            _finalize_move(node, "failed", "autopath_failed")
                            return BehaviorTree.NodeState.FAILURE

                if Checks.Player.IsDead():
                    if log:
                        ConsoleLog("Move", "Player is dead; movement remains active and waiting.", Console.MessageType.Warning, log=log)
                    state["last_progress_ms"] = now
                    state["was_paused"] = True
                    _set_blackboard(node, "paused", "player_dead")
                    return BehaviorTree.NodeState.RUNNING

                pause_reason = _get_pause_reason(node)
                if pause_reason:
                    if not state["pause_logged"] and log:
                            ConsoleLog("Move", f"Movement paused due to {pause_reason}.", Console.MessageType.Info, log=log)
                    state["pause_logged"] = True
                    state["was_paused"] = True
                    state["last_progress_ms"] = now
                    _set_blackboard(node, "paused", pause_reason)
                    return BehaviorTree.NodeState.RUNNING
                elif state["pause_logged"]:
                    if log:
                        ConsoleLog("Move", "Movement resumed.", Console.MessageType.Info, log=log)
                    state["pause_logged"] = False
                if state["was_paused"]:
                    state["was_paused"] = False
                    state["resume_recovery_active"] = True

                if state["path_points"] is None or state["path_index"] >= len(state["path_points"]):
                    if log:
                        ConsoleLog("Move", "Movement finished with no remaining path points.", Console.MessageType.Success, log=log)
                    _finalize_move(node, "finished")
                    return BehaviorTree.NodeState.SUCCESS

                target_x, target_y = state["path_points"][state["path_index"]]
                if state["last_logged_waypoint_index"] != state["path_index"] and log:
                    ConsoleLog(
                        "Move",
                        f"Tracking waypoint {state['path_index'] + 1}/{len(state['path_points'])} at ({target_x}, {target_y}).",
                        Console.MessageType.Info,
                        log=log,
                    )
                    state["last_logged_waypoint_index"] = state["path_index"]
                current_pos = Player.GetXY()
                current_distance = Utils.Distance(current_pos, (target_x, target_y))

                if current_distance <= tolerance:
                    state["path_index"] += 1
                    state["move_issued"] = False
                    state["last_distance"] = None
                    state["last_progress_ms"] = now
                    state["resume_recovery_active"] = False
                    if log:
                        ConsoleLog("Move", f"Reached waypoint, advancing to index {state['path_index']}.", Console.MessageType.Info, log=log)

                    if state["path_index"] >= len(state["path_points"]):
                        if log:
                            ConsoleLog("Move", "Reached final destination.", Console.MessageType.Success, log=log)
                        _finalize_move(node, "finished")
                        return BehaviorTree.NodeState.SUCCESS

                    target_x, target_y = state["path_points"][state["path_index"]]
                    _issue_move(target_x, target_y)
                    state["move_issued"] = True
                    state["last_distance"] = Utils.Distance(Player.GetXY(), (target_x, target_y))
                    state["last_progress_ms"] = now
                    _set_blackboard(node, "running")
                    return BehaviorTree.NodeState.RUNNING

                if not state["move_issued"]:
                    _issue_move(target_x, target_y)
                    state["move_issued"] = True
                    state["last_distance"] = current_distance
                    state["last_progress_ms"] = now
                    _set_blackboard(node, "running")
                    return BehaviorTree.NodeState.RUNNING

                if state["last_distance"] is None or current_distance < state["last_distance"] - 1.0:
                    state["last_distance"] = current_distance
                    state["last_progress_ms"] = now
                elif state["last_progress_ms"] is not None and now - state["last_progress_ms"] >= stall_threshold_ms:
                    if log:
                        ConsoleLog(
                            "Move",
                            f"No progress for {stall_threshold_ms}ms, nudging waypoint ({target_x}, {target_y}).",
                            Console.MessageType.Warning,
                            log=log,
                        )
                    _issue_move(target_x, target_y)
                    state["last_progress_ms"] = now
                    state["last_distance"] = current_distance

                _set_blackboard(node, "running")
                return BehaviorTree.NodeState.RUNNING

            timeout_state = {
                "started_ms": None,
                "waypoint_index": None,
                "paused_since_ms": None,
                "paused_total_ms": 0,
            }

            def _reset_timeout():
                timeout_state["started_ms"] = None
                timeout_state["waypoint_index"] = None
                timeout_state["paused_since_ms"] = None
                timeout_state["paused_total_ms"] = 0

            def _timeout(node: BehaviorTree.Node):
                from ..Py4GWcorelib import Utils

                is_paused = bool(_get_pause_reason(node))
                if state["completed"] and state["result_state"] == "finished":
                    if log:
                        ConsoleLog("Move", f"Timeout watcher finished because movement succeeded ({state['result_reason']}).", Console.MessageType.Info, log=log)
                    _reset_timeout()
                    return BehaviorTree.NodeState.SUCCESS

                if state["completed"] and state["result_state"] == "failed":
                    if log:
                        ConsoleLog("Move", f"Timeout watcher finished because movement failed: {state['result_reason']}.", Console.MessageType.Info, log=log)
                    _reset_timeout()
                    return BehaviorTree.NodeState.SUCCESS

                now = Utils.GetBaseTimestamp()

                if is_paused:
                    if timeout_state["paused_since_ms"] is None:
                        timeout_state["paused_since_ms"] = now
                    return BehaviorTree.NodeState.RUNNING

                if state["path_points"] is None or state["path_index"] >= len(state["path_points"]):
                    return BehaviorTree.NodeState.RUNNING

                if timeout_state["waypoint_index"] != state["path_index"]:
                    timeout_state["started_ms"] = now
                    timeout_state["waypoint_index"] = state["path_index"]
                    timeout_state["paused_since_ms"] = None
                    timeout_state["paused_total_ms"] = 0
                    return BehaviorTree.NodeState.RUNNING

                if timeout_state["started_ms"] is None:
                    timeout_state["started_ms"] = now
                    timeout_state["waypoint_index"] = state["path_index"]
                    return BehaviorTree.NodeState.RUNNING

                if timeout_state["paused_since_ms"] is not None:
                    timeout_state["started_ms"] = now
                    timeout_state["paused_since_ms"] = None
                    timeout_state["paused_total_ms"] = 0
                    return BehaviorTree.NodeState.RUNNING

                elapsed_ms = now - timeout_state["started_ms"] - timeout_state["paused_total_ms"]
                effective_timeout_ms = timeout_ms * 3 if state["resume_recovery_active"] else timeout_ms
                if effective_timeout_ms > 0 and elapsed_ms >= effective_timeout_ms:
                    if log:
                        ConsoleLog(
                            "Move",
                            f"Movement timed out after {elapsed_ms}ms on path_index={state['path_index']}.",
                            Console.MessageType.Warning,
                            log=log,
                        )
                    _finalize_move(node, "failed", "timeout")
                    _reset_timeout()
                    return BehaviorTree.NodeState.FAILURE

                return BehaviorTree.NodeState.RUNNING

            def _map_transition(node: BehaviorTree.Node):
                if state["completed"] and state["result_state"] == "finished":
                    return BehaviorTree.NodeState.SUCCESS

                if state["completed"] and state["result_state"] == "failed":
                    return BehaviorTree.NodeState.SUCCESS

                current_map_id = Map.GetMapID()
                initial_map_id = int(state["initial_map_id"] or 0)
                map_loading = Map.IsMapLoading()
                map_changed = (
                    initial_map_id != 0
                    and current_map_id != 0
                    and current_map_id != initial_map_id
                )

                if map_loading or map_changed:
                    reason = "map_loading" if map_loading else "map_changed"
                    if _debug_enabled(node):
                        ConsoleLog(
                            "Move",
                            f"Movement finished successfully due to {reason}.",
                            Console.MessageType.Info,
                            log=True,
                        )
                    _finalize_move(node, "finished", reason)
                    return BehaviorTree.NodeState.SUCCESS

                if not Checks.Map.MapValid():
                    if _debug_enabled(node):
                        ConsoleLog(
                            "Move",
                            "Map is temporarily invalid during movement; waiting without finalizing move.",
                            Console.MessageType.Info,
                            log=True,
                        )
                    return BehaviorTree.NodeState.RUNNING

                return BehaviorTree.NodeState.RUNNING

            move_node = BehaviorTree.ConditionNode(
                name="MoveExecutor",
                condition_fn=lambda node: _move(node),
            )
            timeout_node = BehaviorTree.ConditionNode(
                name="MoveTimeout",
                condition_fn=lambda node: _timeout(node),
            )
            map_transition_node = BehaviorTree.ConditionNode(
                name="MoveMapTransition",
                condition_fn=lambda node: _map_transition(node),
            )
            tree = BehaviorTree.ParallelNode(
                name="Move",
                children=[move_node, timeout_node, map_transition_node],
            )
            return BehaviorTree(tree)
        

    #region Skills
    class Skills:
        @staticmethod
        def LoadSkillbar(template:str, log:bool=False):
            """
            Purpose: Load a skillbar template.
            Args:
                template (str): The skillbar template to load.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _load_skillbar(template:str):
                GLOBAL_CACHE.SkillBar.LoadSkillTemplate(template)
                ConsoleLog("LoadSkillbar", f"Loaded skillbar template.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="LoadSkillbar", action_fn=lambda: _load_skillbar(template), aftercast_ms=500)
            return BehaviorTree(tree)
        
        @staticmethod
        def LoadHeroSkillbar(hero_index:int, template:str, log:bool=False):
            """
            Purpose: Load a hero's skillbar template.
            Args:
                hero_index (int): The index of the hero.
                template (str): The skillbar template to load.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def _load_hero_skillbar(hero_index:int, template:str):
                GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(hero_index, template)
                ConsoleLog("LoadHeroSkillbar", f"Loaded hero {hero_index} skillbar template.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="LoadHeroSkillbar", action_fn=lambda: _load_hero_skillbar(hero_index, template), aftercast_ms=500)
            return BehaviorTree(tree)
        
        @staticmethod
        def CastSkillID (skill_id:int,target_agent_id:int =0, extra_condition=True, aftercast_delay=0,  log=False):
            """
            Purpose: Cast a skill by its ID using a Behavior Tree.
            Args:
                skill_id (int): The ID of the skill to cast.
                target_agent_id (int) Optional: The ID of the target agent. Default is 0.
                extra_condition (bool) Optional: An extra condition to check before casting. Default is True.
                aftercast_delay (int) Optional: Delay in milliseconds after casting the skill. Default is 0.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: A Behavior Tree that performs the skill cast.
            """
            def _use_skill(slot:int,target_agent_id:int, aftercast_delay:int, log:bool):
                GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=target_agent_id, aftercast_delay=aftercast_delay)
                ConsoleLog("CastSkillID", f"Cast {GLOBAL_CACHE.Skill.GetName(skill_id)}, slot: {GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)}", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.SequenceNode(children=[
                        BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Checks.Map.IsExplorable()),
                        BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Checks.Skills.HasEnoughEnergy(Player.GetAgentID(),skill_id)),
                        BehaviorTree.ConditionNode(name="IsSkillIDReady", condition_fn=lambda:Checks.Skills.IsSkillIDReady(skill_id)),
                        BehaviorTree.ConditionNode(name="IsSkillInSlot", condition_fn=lambda:1 <= GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id) <= 8),
                        BehaviorTree.ConditionNode(name="ExtraCustomCondition", condition_fn=lambda: extra_condition),
                        BehaviorTree.ActionNode(name="CastSkillID", action_fn=lambda:_use_skill(GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id), target_agent_id, aftercast_delay, log), aftercast_ms=aftercast_delay),
                    ])
            bt = BehaviorTree(root=tree)
            return bt
        
        @staticmethod
        def CastSkillSlot(slot:int,target_agent_id: int =0,extra_condition=True, aftercast_delay=0, log=False):
            """
            Purpose: Cast a skill in a specific slot using a Behavior Tree.
            Args:
                slot (int): The slot number of the skill to cast.
                extra_condition (bool) Optional: An extra condition to check before casting. Default is True.
                aftercast_delay (int) Optional: Delay in milliseconds after casting the skill. Default is 0.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: A Behavior Tree that performs the skill cast.
            """
            def _use_skill(slot:int,target_agent_id:int, aftercast_delay:int, log:bool):
                GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=target_agent_id, aftercast_delay=aftercast_delay)
                ConsoleLog("CastSkillSlot", f"Cast {GLOBAL_CACHE.Skill.GetName(GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot))}, slot: {slot}", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.SequenceNode(children=[
                        BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Routines.Checks.Map.IsExplorable()),
                        BehaviorTree.ConditionNode(name="ValidSkillSlot", condition_fn=lambda:1 <= slot <= 8),
                        BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Routines.Checks.Skills.HasEnoughEnergy(Player.GetAgentID(), GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot))),
                        BehaviorTree.ConditionNode(name="IsSkillSlotReady", condition_fn=lambda:Routines.Checks.Skills.IsSkillSlotReady(slot)),
                        BehaviorTree.ConditionNode(name="ExtraCustomCondition", condition_fn=lambda: extra_condition),
                        BehaviorTree.ActionNode(name="CastSkillSlot", action_fn=lambda:_use_skill(slot, target_agent_id, aftercast_delay, log), aftercast_ms=aftercast_delay),
                    ])
            bt = BehaviorTree(root=tree)
            return bt
        
        
        @staticmethod
        def IsSkillIDUsable(skill_id: int):
            """
            Purpose: Check if a skill by its ID is usable using a Behavior Tree.
            Args:
                skill_id (int): The ID of the skill to check.
            Returns: A Behavior Tree that checks if the skill is usable.
            """
            tree = BehaviorTree.SequenceNode(children=[
                BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Checks.Map.IsExplorable()),
                BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Checks.Skills.HasEnoughEnergy(Player.GetAgentID(),skill_id)),
                BehaviorTree.ConditionNode(name="IsSkillIDReady", condition_fn=lambda:Checks.Skills.IsSkillIDReady(skill_id)),
                BehaviorTree.ConditionNode(name="IsSkillInSlot", condition_fn=lambda:1 <= GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id) <= 8),
            ])
            bt = BehaviorTree(root=tree)
            return bt
        
        @staticmethod
        def IsSkillSlotUsable(skill_slot: int):
            """
            Purpose: Check if a skill in a specific slot is usable using a Behavior Tree.
            Args:
                skill_slot (int): The slot number of the skill to check.
            Returns: A Behavior Tree that checks if the skill in the slot is usable.
            """
            def _get_skill_id_from_slot(slot:int):
                return GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot)
            
            tree = BehaviorTree.SequenceNode(children=[
                BehaviorTree.ConditionNode(name="InExplorable", condition_fn=lambda:Checks.Map.IsExplorable()),
                BehaviorTree.ConditionNode(name="ValidSkillSlot", condition_fn=lambda:1 <= skill_slot <= 8),
                BehaviorTree.ConditionNode(name="EnoughEnergy", condition_fn=lambda:Checks.Skills.HasEnoughEnergy(Player.GetAgentID(), _get_skill_id_from_slot(skill_slot))),
                BehaviorTree.ConditionNode(name="IsSkillIDReady", condition_fn=lambda:Checks.Skills.IsSkillSlotReady(skill_slot)),
            ])
            bt = BehaviorTree(root=tree)
            return bt

    #region Map      
    class Map:  
        @staticmethod
        def SetHardMode(hard_mode=True, log=False):
            """
            Purpose: Set the map to hard mode.
            Args: None
            Returns: None
            """
            def set_mode():
                if not hard_mode:
                    GLOBAL_CACHE.Party.SetNormalMode()
                else:
                    GLOBAL_CACHE.Party.SetHardMode()
                return BehaviorTree.NodeState.SUCCESS
            
            def check_mode_and_log():
                if GLOBAL_CACHE.Party.IsHardMode() == hard_mode:
                    ConsoleLog("SetHardMode", f"Mode set to {'hard_mode' if hard_mode else 'normal_mode'}.", Console.MessageType.Info, log=log)
                    return True
                ConsoleLog("SetHardMode", f"Failed to set hard mode to {hard_mode}.", Console.MessageType.Error, log=log)
                return False
            
            tree = BehaviorTree.SequenceNode(children=[
                        BehaviorTree.ActionNode(name="SetMode", action_fn=lambda: set_mode(), aftercast_ms=500),
                        BehaviorTree.ConditionNode(name="CheckMode", condition_fn=lambda: check_mode_and_log()),
                    ])
            
            return BehaviorTree(tree)

        @staticmethod
        def TravelToOutpost(outpost_id: int, log: bool = False, timeout: int = 10000) -> BehaviorTree: 
            """
            Purpose: Positions yourself safely on the outpost.
            Args:
                outpost_id (int): The ID of the outpost to travel to.
                log (bool) Optional: Whether to log the action. Default is False.
            Returns: None
            """
            def arrived_early(outpost_id) -> bool: 
                if Map.IsMapIDMatch(0, outpost_id): 
                    ConsoleLog("TravelToOutpost", f"Already at {Map.GetMapName(outpost_id)}", log=log) 
                    return True
                return False

            def travel_action(outpost_id) -> BehaviorTree.NodeState:
                ConsoleLog("TravelToOutpost", f"Travelling to {Map.GetMapName(outpost_id)}", log=log)
                Map.Travel(outpost_id)
                return BehaviorTree.NodeState.SUCCESS 
            
            def map_arrival (outpost_id: int) -> BehaviorTree.NodeState: 
                if (Map.IsMapReady() and 
                    GLOBAL_CACHE.Party.IsPartyLoaded() and 
                    Map.IsMapIDMatch(0, outpost_id)): 
                    ConsoleLog("TravelToOutpost", f"Arrived at {Map.GetMapName(outpost_id)}", log=log) 
                    return BehaviorTree.NodeState.SUCCESS 
                return BehaviorTree.NodeState.RUNNING 
            
            tree = BehaviorTree.SelectorNode(children=[ 
                        BehaviorTree.ConditionNode(name="ArrivedEarly", condition_fn=lambda: arrived_early(outpost_id)),
                        BehaviorTree.SequenceNode(name="TravelSequence", children=[ 
                            BehaviorTree.ActionNode(name="TravelAction", action_fn=lambda: travel_action(outpost_id), aftercast_ms=3000),
                            BehaviorTree.WaitNode(name="MapArrival", check_fn=lambda: map_arrival(outpost_id), timeout_ms=timeout),
                            BehaviorTree.WaitForTimeNode(name="PostArrivalWait", duration_ms=1000)
                        ]) 
                ]) 
            
            return BehaviorTree(tree)

        @staticmethod
        def TravelToRegion(outpost_id, region, district, language=0, log:bool=False, timeout: int = 10000):
            # 1. EARLY ARRIVAL CHECK
            def arrived_early() -> bool:
                if (Map.IsMapIDMatch(0, outpost_id) and
                    Map.GetRegion() == region and
                    Map.GetDistrict() == district and
                    Map.GetLanguage() == language):

                    ConsoleLog("TravelToRegion",
                            f"Already at {Map.GetMapName(outpost_id)}",
                            log=log)
                    return True
                
                return False
            # 2. TRAVEL ACTION
            def travel_action() -> BehaviorTree.NodeState:
                ConsoleLog("TravelToRegion",
                        f"Travelling to {Map.GetMapName(outpost_id)}",
                        log=log)
                Map.TravelToRegion(outpost_id, region, district, language)
                return BehaviorTree.NodeState.SUCCESS
            # 3. ARRIVAL CHECK
            def map_arrival() -> BehaviorTree.NodeState:
                if (Map.IsMapReady() and
                    GLOBAL_CACHE.Party.IsPartyLoaded() and
                    Map.IsMapIDMatch(0, outpost_id) and
                    Map.GetRegion() == region and
                    Map.GetDistrict() == district and
                    Map.GetLanguage() == language):

                    ConsoleLog("TravelToRegion",
                            f"Arrived at {Map.GetMapName(outpost_id)}",
                            log=log)
                    return BehaviorTree.NodeState.SUCCESS

                return BehaviorTree.NodeState.RUNNING
                

            tree = BehaviorTree.SelectorNode(children=[
                BehaviorTree.ConditionNode(name="ArrivedEarly",condition_fn=lambda: arrived_early()),
                BehaviorTree.SequenceNode(name="TravelSequence", children=[
                    BehaviorTree.ActionNode(name="TravelToRegionAction", action_fn=lambda: travel_action(), aftercast_ms=2000),
                    BehaviorTree.WaitNode(name="WaitForMapArrival", check_fn=lambda: map_arrival(), timeout_ms=timeout),
                    BehaviorTree.WaitForTimeNode(name="PostArrivalWait", duration_ms=1000)
                ])
            ])

            return BehaviorTree(tree)
        
        @staticmethod
        def WaitforMapLoad(map_id:int=0, log:bool=False, timeout: int = 10000, map_name: str =""):   
            def _map_arrival_check(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                nonlocal map_id, map_name, log
                from .Checks import Checks
                
                if map_name:
                    map_id = Map.GetMapIDByName(map_name)
                    
                if map_id == 0:
                    return BehaviorTree.NodeState.RUNNING
                
                _map_valid = Checks.Map.MapValid()
                if not _map_valid:
                    return BehaviorTree.NodeState.RUNNING
                
                if not GLOBAL_CACHE.Party.IsPartyLoaded():
                    return BehaviorTree.NodeState.RUNNING
                
                if not Map.GetInstanceUptime() >= 1500:
                    return BehaviorTree.NodeState.RUNNING
                
                if not Player.GetInstanceUptime() >= 1500:
                    return BehaviorTree.NodeState.RUNNING

                if Map.IsMapIDMatch(Map.GetMapID(), map_id):
                    ConsoleLog("WaitforMapLoad", f"Map {Map.GetMapName(map_id)} loaded successfully.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                return BehaviorTree.NodeState.RUNNING

            tree = BehaviorTree.SequenceNode(name="WaitforMapLoadRoot",
                        children=[
                            BehaviorTree.WaitUntilNode(name="WaitForMapLoadUntil",
                                condition_fn=lambda node: _map_arrival_check(node),
                                throttle_interval_ms=500,
                                timeout_ms=timeout),
                            BehaviorTree.WaitForTimeNode(name="PostArrivalWait", duration_ms=1000)
                        ]
                    )
            
            return tree

    class Items:
        BONUS_ITEM_MODELS = [
            ModelID.Bonus_Luminescent_Scepter.value,
            ModelID.Bonus_Nevermore_Flatbow.value,
            ModelID.Bonus_Rhinos_Charge.value,
            ModelID.Bonus_Serrated_Shield.value,
            ModelID.Bonus_Soul_Shrieker.value,
            ModelID.Bonus_Tigers_Roar.value,
            ModelID.Bonus_Wolfs_Favor.value,
            ModelID.Igneous_Summoning_Stone.value,
        ]

        @staticmethod
        def SpawnBonusItems(log: bool = False, aftercast_ms: int = 500) -> BehaviorTree:
            def _spawn_bonus_items():
                Player.SendChatCommand("bonus")
                ConsoleLog("SpawnBonusItems", "Sent /bonus command.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.ActionNode(
                name="SpawnBonusItems",
                action_fn=_spawn_bonus_items,
                aftercast_ms=aftercast_ms,
            )
            return BehaviorTree(tree)

        @staticmethod
        def DestroyItem(
            model_id: int,
            log: bool = False,
            required: bool = False,
            aftercast_ms: int = 600,
        ) -> BehaviorTree:
            def _destroy_item():
                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                if item_id == 0:
                    ConsoleLog(
                        "DestroyItem",
                        f"Item model {model_id} was not found in inventory for destruction.",
                        Console.MessageType.Warning if required else Console.MessageType.Info,
                        log=True,
                    )
                    if required:
                        ConsoleLog(
                            "DestroyItem",
                            f"Item model {model_id} was not found for destruction.",
                            Console.MessageType.Warning,
                            log=True if required else log,
                        )
                        return BehaviorTree.NodeState.FAILURE
                    return BehaviorTree.NodeState.SUCCESS

                GLOBAL_CACHE.Inventory.DestroyItem(item_id)
                ConsoleLog(
                    "DestroyItem",
                    f"Queued destroy for item model {model_id} (item_id={item_id}).",
                    Console.MessageType.Info,
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.ActionNode(
                name="DestroyItem",
                action_fn=_destroy_item,
                aftercast_ms=aftercast_ms,
            )
            return BehaviorTree(tree)

        @staticmethod
        def DestroyBonusItems(
            exclude_list: list[int] | None = None,
            log: bool = False,
            aftercast_ms: int = 100,
        ) -> BehaviorTree:
            excluded_models = set(exclude_list or [
                ModelID.Igneous_Summoning_Stone.value,
            ])
            bonus_models_to_destroy = [
                model_id
                for model_id in BT.Items.BONUS_ITEM_MODELS
                if model_id not in excluded_models
            ]

            return BT.Composite.Sequence(
                BT.Player.PrintMessageToConsole(
                    source="DestroyBonusItems",
                    message=f"Destroy pass starting for models: {bonus_models_to_destroy}",
                ),
                *[
                    BT.Items.DestroyItem(model_id=model_id, log=log, required=False, aftercast_ms=aftercast_ms)
                    for model_id in bonus_models_to_destroy
                ],
                name="DestroyBonusItems",
            )

        @staticmethod
        def WaitForAnyModelInInventory(
            model_ids: list[int],
            timeout_ms: int = 5000,
            throttle_interval_ms: int = 100,
            log: bool = False,
        ) -> BehaviorTree:
            def _wait_for_any_model() -> BehaviorTree.NodeState:
                for model_id in model_ids:
                    item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
                    if item_id != 0:
                        ConsoleLog("WaitForAnyModelInInventory", f"Detected inventory model {model_id} as item_id={item_id}.", Console.MessageType.Info, log=log)
                        return BehaviorTree.NodeState.SUCCESS
                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree(
                BehaviorTree.WaitUntilNode(
                    name="WaitForAnyModelInInventory",
                    condition_fn=_wait_for_any_model,
                    throttle_interval_ms=throttle_interval_ms,
                    timeout_ms=timeout_ms,
                )
            )

        @staticmethod
        def MoveModelToBagSlot(
            model_id: int,
            target_bag: int = 1,
            slot: int = 0,
            log: bool = False,
            required: bool = True,
            aftercast_ms: int = 250,
        ) -> BehaviorTree:
            def _move_model_to_bag_slot():
                moved = GLOBAL_CACHE.Inventory.MoveModelToBagSlot(model_id, target_bag, slot)
                if not moved:
                    if required:
                        ConsoleLog(
                            "MoveModelToBagSlot",
                            f"Failed to move model {model_id} to bag {target_bag} slot {slot}.",
                            Console.MessageType.Warning,
                            log=True if required else log,
                        )
                        return BehaviorTree.NodeState.FAILURE
                    return BehaviorTree.NodeState.SUCCESS

                ConsoleLog(
                    "MoveModelToBagSlot",
                    f"Moved model {model_id} to bag {target_bag} slot {slot}.",
                    Console.MessageType.Info,
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.ActionNode(
                name="MoveModelToBagSlot",
                action_fn=_move_model_to_bag_slot,
                aftercast_ms=aftercast_ms,
            )
            return BehaviorTree(tree)

        @staticmethod
        def GetItemNameByItemID(item_id: int) -> BehaviorTree:
            def _request_item_name(node):
                GLOBAL_CACHE.Item.RequestName(item_id)
                return BehaviorTree.NodeState.SUCCESS

            def _check_item_name_ready(node):
                if not GLOBAL_CACHE.Item.IsNameReady(item_id):
                    return BehaviorTree.NodeState.FAILURE
                return BehaviorTree.NodeState.SUCCESS

            def _get_item_name(node):
                name = ''
                if GLOBAL_CACHE.Item.IsNameReady(item_id):
                    name = GLOBAL_CACHE.Item.GetName(item_id)

                node.blackboard["result"] = name
                return BehaviorTree.NodeState.SUCCESS if name else BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(
                name="GetItemNameByItemIDRoot",
                children=[
                    BehaviorTree.ActionNode(name="RequestItemName", action_fn=_request_item_name),
                    BehaviorTree.RepeaterUntilSuccessNode(
                        name="WaitUntilItemNameReadyRepeater",
                        timeout_ms=2000,
                        child=BehaviorTree.SelectorNode(
                            name="WaitUntilItemNameReadySelector",
                            children=[
                                BehaviorTree.ConditionNode(name="CheckItemNameReady", condition_fn=_check_item_name_ready),
                                BehaviorTree.SequenceNode(
                                    name="WaitForThrottle",
                                    children=[
                                        BehaviorTree.WaitForTimeNode(name="Throttle100ms", duration_ms=100),
                                        BehaviorTree.FailerNode(name="FailToRepeat")
                                    ]
                                ),
                            ]
                        )
                    ),
                    BehaviorTree.ActionNode(name="GetItemName", action_fn=_get_item_name)
                ]
            )
            return BehaviorTree(tree)

        @staticmethod
        def SpawnImp(
            target_bag: int = 1,
            slot: int = 0,
            exclude_list: list[int] | None = None,
            log: bool = False,
            spawn_settle_ms: int = 250,
        ) -> BehaviorTree:
            imp_model_id = ModelID.Igneous_Summoning_Stone.value
            effective_exclude_list = list(exclude_list or [
                imp_model_id,
            ])

            if imp_model_id not in effective_exclude_list:
                effective_exclude_list.append(imp_model_id)

            return BT.Composite.Sequence(
                BT.Items.SpawnBonusItems(log=log, aftercast_ms=spawn_settle_ms),
                BT.Items.DestroyBonusItems(exclude_list=effective_exclude_list, log=log),
                BT.Items.MoveModelToBagSlot(
                    model_id=imp_model_id,
                    target_bag=target_bag,
                    slot=slot,
                    log=log,
                    required=True,
                    aftercast_ms=spawn_settle_ms,
                ),
                name="SpawnImp",
            )

        @staticmethod
        def OutpostImpService(
            target_bag: int = 1,
            slot: int = 0,
            exclude_list: list[int] | None = None,
            log: bool = False,
        ) -> BehaviorTree:
            state = {
                "last_ready_map_id": 0,
                "map_processed": False,
                "spawn_tree": None,
                "last_stage_log": "",
            }

            imp_model_id = ModelID.Igneous_Summoning_Stone.value
            effective_exclude_list = list(exclude_list or [
                imp_model_id,
            ])
            

            def _reset_cache_data():
                state["last_ready_map_id"] = 0
                state["map_processed"] = False
                state["last_stage_log"] = ""
                if state["spawn_tree"] is not None:
                    state["spawn_tree"].reset()
                    state["spawn_tree"] = None


            def _tick_outpost_imp_service(node: BehaviorTree.Node):
                if Map.IsMapLoading() or not Checks.Map.MapValid() or not Map.IsMapReady():
                    _reset_cache_data()
                    return BehaviorTree.NodeState.RUNNING

                current_map_id = Map.GetMapID()
                if current_map_id == 0:
                    return BehaviorTree.NodeState.RUNNING

                if state["last_ready_map_id"] != current_map_id:
                    state["last_ready_map_id"] = current_map_id
                    state["map_processed"] = False
                    if state["spawn_tree"] is not None:
                        state["spawn_tree"].reset()
                        state["spawn_tree"] = None

                if not Map.IsOutpost():
                    return BehaviorTree.NodeState.RUNNING

                if state["map_processed"]:
                    return BehaviorTree.NodeState.RUNNING

                if state["spawn_tree"] is None:
                    if GLOBAL_CACHE.Inventory.GetFirstModelID(imp_model_id) != 0:
                        state["map_processed"] = True
                        if log:
                            ConsoleLog(
                                "OutpostImpService",
                                f"Imp model {imp_model_id} already present in bags for map {current_map_id}.",
                                Console.MessageType.Info,
                                log=log,
                            )
                        return BehaviorTree.NodeState.RUNNING

                    state["spawn_tree"] = BT.Items.SpawnImp(
                        target_bag=target_bag,
                        slot=slot,
                        exclude_list=effective_exclude_list,
                        log=log,
                    )

                state["spawn_tree"].blackboard = node.blackboard
                spawn_result = BehaviorTree.Node._normalize_state(state["spawn_tree"].tick())
                if spawn_result is None:
                    raise TypeError("OutpostImpService spawn tree returned a non-NodeState result.")

                if spawn_result == BehaviorTree.NodeState.SUCCESS:
                    if log:
                        ConsoleLog(
                            "OutpostImpService",
                            f"Prepared imp model {imp_model_id} in outpost map {current_map_id}.",
                            Console.MessageType.Success,
                            log=log,
                        )
                    state["map_processed"] = True
                    state["spawn_tree"].reset()
                    state["spawn_tree"] = None
                elif spawn_result == BehaviorTree.NodeState.FAILURE:
                    ConsoleLog(
                        "OutpostImpService",
                        f"Failed to prepare imp model {imp_model_id} in outpost map {current_map_id}; idling until next map change.",
                        Console.MessageType.Warning,
                        log=True,
                    )
                    state["map_processed"] = True
                    state["spawn_tree"].reset()
                    state["spawn_tree"] = None

                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree(
                BehaviorTree.ConditionNode(
                    name="OutpostImpService",
                    condition_fn=_tick_outpost_imp_service,
                )
            )

        @staticmethod
        def ExplorableImpService(
            imp_model_id: int = ModelID.Igneous_Summoning_Stone.value,
            log: bool = False,
            check_interval_ms: int = 1000,
        ) -> BehaviorTree:
            state = {
                "last_attempt_ms": 0,
            }

            summoning_sickness_effect_id = 2886
            summon_creature_model_ids = {
                513,   # Fire Imp
                1726,  # Fire Imp variant
            }

            def _has_alive_imp() -> bool:
                for other in GLOBAL_CACHE.Party.GetOthers():
                    if Agent.GetModelID(other) in summon_creature_model_ids and not Agent.IsDead(other):
                        return True
                return False

            def _tick_explorable_imp_service(node: BehaviorTree.Node):
                if Map.IsMapLoading() or not Checks.Map.MapValid() or not Map.IsMapReady():
                    return BehaviorTree.NodeState.RUNNING

                if not Map.IsExplorable():
                    return BehaviorTree.NodeState.RUNNING

                if Agent.IsDead(Player.GetAgentID()):
                    return BehaviorTree.NodeState.RUNNING

                if Player.GetLevel() >= 20:
                    return BehaviorTree.NodeState.RUNNING

                if GLOBAL_CACHE.Inventory.GetFirstModelID(imp_model_id) == 0:
                    return BehaviorTree.NodeState.RUNNING

                if GLOBAL_CACHE.Effects.HasEffect(Player.GetAgentID(), summoning_sickness_effect_id):
                    return BehaviorTree.NodeState.RUNNING

                if _has_alive_imp():
                    return BehaviorTree.NodeState.RUNNING

                from ..Py4GWcorelib import Utils
                now = Utils.GetBaseTimestamp()

                if now - int(state["last_attempt_ms"]) < check_interval_ms:
                    return BehaviorTree.NodeState.RUNNING

                item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(imp_model_id)
                if item_id == 0:
                    return BehaviorTree.NodeState.RUNNING

                GLOBAL_CACHE.Inventory.UseItem(item_id)
                state["last_attempt_ms"] = int(now)
                if log:
                    ConsoleLog(
                        "ExplorableImpService",
                        f"Used imp stone model {imp_model_id} in explorable map {Map.GetMapID()}.",
                        Console.MessageType.Info,
                        log=log,
                    )

                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree(
                BehaviorTree.ConditionNode(
                    name="ExplorableImpService",
                    condition_fn=_tick_explorable_imp_service,
                )
            )

    #region Agents        
    class Agents:
        agent_ids = None
        @staticmethod
        def GetAgentIDByName(agent_name: str) -> BehaviorTree:
            def _search_name(node):
                found = Agent.GetAgentIDByName(agent_name)
                node.blackboard["result"] = found
                return (BehaviorTree.NodeState.SUCCESS
                        if found != 0
                        else BehaviorTree.NodeState.FAILURE)

            tree = BehaviorTree.SequenceNode(name="GetAgentIDByNameRoot",
                children=[
                    BehaviorTree.ConditionNode(name="SearchName", condition_fn=_search_name)
                ]
            )
            return BehaviorTree(tree)
        
        @staticmethod
        def GetAgentIDByModelID(model_id:int, log:bool=False) -> BehaviorTree:
            """
            Purpose: Get the agent ID by model ID.
            Args:
                model_id (int): The model ID of the agent.
            Returns: int: The agent ID or 0 if not found.
            """
            def _search_model_id(node):
                from ..AgentArray import AgentArray
                ids = AgentArray.GetAgentArray()
                found = 0

                for aid in ids:
                    if Agent.GetModelID(aid) == model_id:
                        found = aid
                        break

                node.blackboard["result"] = found
                if found != 0:
                    ConsoleLog("GetAgentIDByModelID", f"Found agent ID {found} for model ID {model_id}.", Console.MessageType.Info, log=log)
                    BehaviorTree.NodeState.SUCCESS
                else:
                    ConsoleLog("GetAgentIDByModelID", f"No agent found for model ID {model_id}.", Console.MessageType.Warning, log=log) 
                    BehaviorTree.NodeState.FAILURE
                
                return (BehaviorTree.NodeState.SUCCESS
                        if found != 0
                        else BehaviorTree.NodeState.FAILURE)

            tree = BehaviorTree.ActionNode(name="GetAgentIDByModelID",
                action_fn=_search_model_id)
            return BehaviorTree(tree)
        
        @staticmethod
        def TargetAgentByName(agent_name:str, log:bool=False):
            """
            Purpose: Target an agent by name.
            Args:
                agent_name (str): The name of the agent to target.
            Returns: None
            """
            tree = BehaviorTree.SequenceNode(name="TargetAgentByName",
                children=[
                    BehaviorTree.SubtreeNode(name="GetAgentIDByNameSubtree",
                                             subtree_fn=lambda node: BT.Agents.GetAgentIDByName(agent_name)),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BT.Player.ChangeTarget(node.blackboard.get("result", 0),log=log))
                ]
            )
            return BehaviorTree(tree)
        
        @staticmethod
        def TargetNearestNPC(distance:float = 4500.0, log:bool=False):
            """
            Purpose: Target the nearest NPC within a specified distance.
            Args:
                distance (float) Optional: The maximum distance to search for an NPC. Default is 4500.0.
            Returns: None
            """
            def _find_nearest_npc(node):
                from .Agents import Agents
                nearest_npc = Agents.GetNearestNPC(distance)
                node.blackboard["nearest_npc_id"] = nearest_npc
                if nearest_npc != 0:
                    ConsoleLog("TargetNearestNPC", f"Found nearest NPC with ID {nearest_npc} within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestNPC", f"No NPC found within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestNPCRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestNPC", action_fn=_find_nearest_npc),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BT.Player.ChangeTarget(node.blackboard.get("nearest_npc_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
        @staticmethod
        def TargetNearestNPCXY(x,y,distance, log:bool=False):
            """
            Purpose: Target the nearest NPC to specified coordinates within a certain distance.
            Args:
                x (float): The x coordinate.
                y (float): The y coordinate.
                distance (float): The maximum distance to search for an NPC.
            Returns: None
            """
            def _find_nearest_npc_xy(node):
                from .Agents import Agents
                nearest_npc = Agents.GetNearestNPCXY(x,y,distance)
                node.blackboard["nearest_npc_id"] = nearest_npc
                if nearest_npc != 0:
                    ConsoleLog("TargetNearestNPCXY", f"Found nearest NPC with ID {nearest_npc} near ({x}, {y}) within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestNPCXY", f"No NPC found near ({x}, {y}) within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestNPCXYRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestNPCXY", action_fn=_find_nearest_npc_xy),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BT.Player.ChangeTarget(node.blackboard.get("nearest_npc_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
        @staticmethod
        def TargetNearestGadgetXY(x,y,distance, log:bool=False):
            """
            Purpose: Target the nearest gadget to specified coordinates within a certain distance.
            Args:
                x (float): The x coordinate.
                y (float): The y coordinate.
                distance (float): The maximum distance to search for a gadget.
            Returns: None
            """
            def _find_nearest_gadget_xy(node):
                from .Agents import Agents
                nearest_gadget = Agents.GetNearestGadgetXY(x,y, distance)
                node.blackboard["nearest_gadget_id"] = nearest_gadget
                if nearest_gadget != 0:
                    ConsoleLog("TargetNearestGadgetXY", f"Found nearest gadget with ID {nearest_gadget} near ({x}, {y}) within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestGadgetXY", f"No gadget found near ({x}, {y}) within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestGadgetXYRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestGadgetXY", action_fn=_find_nearest_gadget_xy),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BT.Player.ChangeTarget(node.blackboard.get("nearest_gadget_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
        @staticmethod
        def TargetNearestItemXY(x,y,distance, log:bool=False):
            """
            Purpose: Target the nearest item to specified coordinates within a certain distance.
            Args:
                x (float): The x coordinate.
                y (float): The y coordinate.
                distance (float): The maximum distance to search for an item.
            Returns: None
            """
            def _find_nearest_item_xy(node):
                from .Agents import Agents
                nearest_item = Agents.GetNearestItemXY(x,y, distance)
                node.blackboard["nearest_item_id"] = nearest_item
                if nearest_item != 0:
                    ConsoleLog("TargetNearestItemXY", f"Found nearest item with ID {nearest_item} near ({x}, {y}) within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestItemXY", f"No item found near ({x}, {y}) within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestItemXYRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestItemXY", action_fn=_find_nearest_item_xy),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BT.Player.ChangeTarget(node.blackboard.get("nearest_item_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
        @staticmethod
        def TargetNearestEnemy(distance, log:bool=False):
            """
            Purpose: Target the nearest enemy within a specified distance.
            Args:
                distance (float): The maximum distance to search for an enemy.
            Returns: None
            """
            def _find_nearest_enemy(node):
                from .Agents import Agents
                nearest_enemy = Agents.GetNearestEnemy(distance)
                node.blackboard["nearest_enemy_id"] = nearest_enemy
                if nearest_enemy != 0:
                    ConsoleLog("TargetNearestEnemy", f"Found nearest enemy with ID {nearest_enemy} within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestEnemy", f"No enemy found within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestEnemyRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestEnemy", action_fn=_find_nearest_enemy),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BT.Player.ChangeTarget(node.blackboard.get("nearest_enemy_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
        @staticmethod
        def TargetNearestItem(distance, log:bool=False):
            """
            Purpose: Target the nearest item within a specified distance.
            Args:
                distance (float): The maximum distance to search for an item.
            Returns: None
            """
            def _find_nearest_item(node):
                from .Agents import Agents
                nearest_item = Agents.GetNearestItem(distance)
                node.blackboard["nearest_item_id"] = nearest_item
                if nearest_item != 0:
                    ConsoleLog("TargetNearestItem", f"Found nearest item with ID {nearest_item} within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestItem", f"No item found within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestItemRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestItem", action_fn=_find_nearest_item),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BT.Player.ChangeTarget(node.blackboard.get("nearest_item_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
        @staticmethod
        def TargetNearestChest(distance, log:bool=False):
            """
            Purpose: Target the nearest chest within a specified distance.
            Args:
                distance (float): The maximum distance to search for a chest.
            Returns: None
            """
            def _find_nearest_chest(node):
                from .Agents import Agents
                nearest_chest = Agents.GetNearestChest(distance)
                node.blackboard["nearest_chest_id"] = nearest_chest
                if nearest_chest != 0:
                    ConsoleLog("TargetNearestChest", f"Found nearest chest with ID {nearest_chest} within distance {distance}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                ConsoleLog("TargetNearestChest", f"No chest found within distance {distance}.", Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            tree = BehaviorTree.SequenceNode(name="TargetNearestChestRoot",
                children=[
                    BehaviorTree.ActionNode(name="FindNearestChest", action_fn=_find_nearest_chest),
                    BehaviorTree.SubtreeNode(name="ChangeTargetSubtree",
                                             subtree_fn=lambda node: BT.Player.ChangeTarget(node.blackboard.get("nearest_chest_id", 0), log=log))
                ]
            )
            return BehaviorTree(tree)
        
        
        
#region Keybinds
    class Keybinds:
        @staticmethod
        def PressKeybind(keybind_index:int, duration_ms:int=125, log:bool=False):
            """
            Purpose: Press a keybind for a specified duration using a Behavior Tree.
            Args:
                keybind_index (int): The index of the keybind to press.
                duration_ms (int) Optional: The duration in milliseconds to hold the keybind. Default is 125ms.
            Returns: A Behavior Tree that performs the keybind press.
            """ 
            def _keydown():
                UIManager.Keydown(keybind_index,0)
                return BehaviorTree.NodeState.SUCCESS
            
            def _keyup():
                UIManager.Keyup(keybind_index,0)
                return BehaviorTree.NodeState.SUCCESS
            
            def _log_action():
                ConsoleLog("PressKeybind", f"Pressed keybind index {keybind_index} for {duration_ms}ms.", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.SequenceNode(
                    children=[
                        BehaviorTree.ActionNode(name="KeyDown", action_fn=_keydown, aftercast_ms=duration_ms),
                        BehaviorTree.ActionNode(name="KeyUp", action_fn=_keyup, aftercast_ms=50 ),#duration_ms),
                        BehaviorTree.ActionNode(name="LogAction", action_fn=_log_action)
                    ]
            )
            bt = BehaviorTree(root=tree)
            return bt
        
  
        
        
        
        
        
        
        
        
        
        
        
