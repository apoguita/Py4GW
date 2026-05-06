"""
BT routines file notes
======================

This file is both:
- part of the public BT grouped routine surface
- a discovery source for higher-level tooling

Authoring and discovery conventions
-----------------------------------
- Keep existing class names as the system-level grouping surface.
- Use `PascalCase` for public/front-facing routine methods.
- Use `snake_case` for helper/internal methods.
- Use `_snake_case` for explicitly private helpers.
- Keep helper/internal methods out of the public discovery surface.

Routine docstring template
--------------------------
Each user-facing routine method should use:
- a free human-readable description first
- a structured `Meta:` block after it

Template:

    \"\"\"
    One or more human-readable paragraphs explaining what the routine builds.

    Meta:
      Expose: true
      Audience: beginner
      Display: Interact Target
      Purpose: Build a tree that performs a player interaction routine.
      UserDescription: Use this when you want the player to interact with the current target.
      Notes: Keep metadata single-line. Structural truth should stay in code.
    \"\"\"

Docstring parsing rules
-----------------------
- Only the `Meta:` section is intended for machine parsing.
- Keep metadata lines single-line and in `Key: Value` form.
- Unknown keys should be safe for tooling to ignore.
- Prefer adding presentation/help metadata in docstrings instead of duplicating
  structural metadata that already exists in code.
"""

from __future__ import annotations

import importlib
import random
import time
from typing import Any, TYPE_CHECKING, Callable, TypedDict, cast

import PyImGui

from ...Py4GWcorelib import ConsoleLog, Console, Vec2f
from ...enums_src.IO_enums import CHAR_MAP, Key
from ...enums_src.GameData_enums import Range
from ...Map import Map
from ...Agent import Agent
from ...Player import Player
from ...enums_src.Title_enums import TITLE_NAME

from ...UIManager import UIManager, WindowFrames
from ...py4gwcorelib_src.ActionQueue import ActionQueueManager
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from ...py4gwcorelib_src.Keystroke import Keystroke


def _log(source: str, message: str, *, log: bool = False, message_type=Console.MessageType.Info) -> None:
    ConsoleLog(source, message, message_type, log=log)


def _fail_log(source: str, message: str, message_type=Console.MessageType.Warning) -> None:
    ConsoleLog(source, message, message_type, log=True)


if TYPE_CHECKING:
    from ..BehaviourTrees import BT as _BTCatalog

    BT: type[_BTCatalog]
else:
    class _BTProxy:
        """
        Internal proxy that resolves the `BT` catalog lazily for player helper composition.

        Meta:
          Expose: false
          Audience: advanced
          Display: Internal BT Proxy
          Purpose: Provide lazy access to the shared BT helper catalog from the BT player module.
          UserDescription: Internal support helper class.
          Notes: This proxy exists for module wiring and is not part of the public BT routine catalog.
        """
        def __getattr__(self, name: str) -> Any:
            """
            Resolve a BT helper group or attribute from the shared catalog on demand.

            Meta:
              Expose: false
              Audience: advanced
              Display: Internal BT Proxy Get Attribute
              Purpose: Lazily fetch a named BT catalog attribute.
              UserDescription: Internal support routine.
              Notes: Used only for internal helper composition and should not be surfaced by discovery tooling.
            """
            module = importlib.import_module('Py4GWCoreLib.routines_src.BehaviourTrees')
            return getattr(module.BT, name)


    BT = _BTProxy()


class BTPlayer:
        """
        Public BT helper group for direct player actions, dialog, messaging, logging, and movement.

        Meta:
          Expose: true
          Audience: advanced
          Display: Player
          Purpose: Group public BT routines related to direct player actions and player-owned runtime flows.
          UserDescription: Built-in BT helper group for player action, messaging, and movement routines.
          Notes: Public `PascalCase` methods in this class are discovery candidates when marked exposed.
        """
        @staticmethod
        def InteractAgent(agent_id: int, log: bool = False) -> BehaviorTree:
            """
            Build a tree that interacts with a specific agent id.

            Meta:
              Expose: true
              Audience: beginner
              Display: Interact Agent
              Purpose: Interact with a specific agent id.
              UserDescription: Use this when you already know the agent id you want to interact with.
              Notes: Wraps a single player interact action with a short aftercast delay.
            """
            aftercast_ms: int = 350
             
            def _interact_agent(agent_id: int) -> BehaviorTree.NodeState:
                """
                Interact with the provided agent id.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Interact Agent Helper
                  Purpose: Dispatch the low-level player interact request for a known agent id.
                  UserDescription: Internal support routine.
                  Notes: Returns success immediately after sending the interact request.
                """
                Player.Interact(agent_id, False)
                _log("InteractAgent", f"Interacted with agent {agent_id}.", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(name="InteractAgent", action_fn=lambda: _interact_agent(agent_id), aftercast_ms=aftercast_ms)
            return BehaviorTree(tree)
            
        @staticmethod
        def InteractTarget(log: bool = False) -> BehaviorTree:
            """
            Build a tree that interacts with the currently selected target.

            Meta:
              Expose: true
              Audience: beginner
              Display: Interact Target
              Purpose: Interact with the current player target.
              UserDescription: Use this when you want to interact with whatever is already targeted.
              Notes: Reads the target id first and then delegates to `InteractAgent`.
            """
            def _get_target_id(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                """
                Read the current player target id and store it on the blackboard.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Get Target ID Helper
                  Purpose: Capture the current target id for the enclosing interact-target routine.
                  UserDescription: Internal support routine.
                  Notes: Stores the value in `blackboard['target_id']` and fails when no target is selected.
                """
                node.blackboard["target_id"] = Player.GetTargetID()
                if node.blackboard["target_id"] == 0:
                    _fail_log("InteractTarget", "No target selected.", Console.MessageType.Error)
                    return BehaviorTree.NodeState.FAILURE

                _log("InteractTarget", f"Target ID obtained: {node.blackboard['target_id']}.", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree: BehaviorTree.SequenceNode = BehaviorTree.SequenceNode(children=[
                BehaviorTree.ActionNode(
                    name="GetTargetID",
                    action_fn=lambda node:_get_target_id(node),
                    aftercast_ms=25
                ),
                BehaviorTree.SubtreeNode(
                    name="InteractAgentSubtree",
                    subtree_fn=lambda node: BTPlayer.InteractAgent(
                        cast(int, node.blackboard["target_id"]),
                        log=log,
                    ),
                ),
            ])

            return BehaviorTree(tree)

        @staticmethod
        def ChangeTarget(agent_id: int, log: bool = False) -> BehaviorTree:
            """
            Build a tree that changes the player's target to a specific agent id.

            Meta:
              Expose: true
              Audience: beginner
              Display: Change Target
              Purpose: Change the player's target to a specific agent id.
              UserDescription: Use this when you want to force targeting to a known agent id.
              Notes: Fails if the provided agent id is zero.
            """
            def _change_target() -> BehaviorTree.NodeState:
                """
                Change the player's target to the requested agent id.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Change Target Helper
                  Purpose: Dispatch the low-level target-change request for a known agent id.
                  UserDescription: Internal support routine.
                  Notes: Fails when the provided agent id is zero.
                """
                if agent_id != 0:
                    Player.ChangeTarget(agent_id)
                    _log("ChangeTarget", f"Changed target to agent {agent_id}.", log=log)
                    return BehaviorTree.NodeState.SUCCESS
                
                _fail_log("ChangeTarget", "Invalid agent ID provided for targeting.", Console.MessageType.Error)
                return BehaviorTree.NodeState.FAILURE
            
            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(name="ChangeTarget", action_fn=lambda: _change_target(), aftercast_ms=250)
            return BehaviorTree(tree)
        
        @staticmethod
        def SendDialog(dialog_id: str | int, log: bool = False) -> BehaviorTree:
            """
            Build a tree that sends a manual dialog id.

            Meta:
              Expose: true
              Audience: beginner
              Display: Send Dialog
              Purpose: Send a dialog id through the player dialog API.
              UserDescription: Use this when you know the dialog id that should be sent next.
              Notes: Wraps a single send-dialog action with a short aftercast delay.
            """
            def _send_dialog(dialog_id: str | int) -> BehaviorTree.NodeState:
                """
                Send the requested dialog id.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Send Dialog Helper
                  Purpose: Dispatch the low-level dialog send request for the enclosing routine.
                  UserDescription: Internal support routine.
                  Notes: Returns success immediately after sending the dialog id.
                """
                Player.SendDialog(dialog_id)
                _log("SendDialog", f"Sent dialog {dialog_id}.", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(name="SendDialog", action_fn=lambda: _send_dialog(dialog_id), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def SendAutomaticDialog(button_number: int, log: bool = False, aftercast_ms: int = 250) -> BehaviorTree:
            """
            Build a tree that waits for an automatic dialog and presses a visible button index.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Send Automatic Dialog
              Purpose: Wait for an active dialog and press a visible automatic dialog button.
              UserDescription: Use this when dialog options appear dynamically and you want to choose by visible button index.
              Notes: Waits up to 3000ms for dialog state and fails if the requested button never becomes available.
            """
            import PyDialog
            from ...Py4GWcorelib import Utils

            state: dict[str, int | None] = {
                "started_ms": None,
            }

            def _dialog_ready() -> BehaviorTree.NodeState:
                """
                Wait until the requested automatic dialog button is available.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Automatic Dialog Ready Helper
                  Purpose: Poll dialog state until a valid automatic dialog button can be pressed.
                  UserDescription: Internal support routine.
                  Notes: Returns running while waiting and fails after the 3000ms timeout budget expires.
                """
                now = Utils.GetBaseTimestamp()
                if state["started_ms"] is None:
                    state["started_ms"] = now

                try:
                    if not PyDialog.PyDialog.is_dialog_active():
                        if now - int(state["started_ms"]) >= 3000:
                            _fail_log(
                                "SendAutomaticDialog",
                                f"Timed out waiting for dialog/button {button_number}; no dialog became active within 3000ms.",
                            )
                            state["started_ms"] = None
                            return BehaviorTree.NodeState.FAILURE
                        return BehaviorTree.NodeState.RUNNING

                    buttons: list[Any] = list(PyDialog.PyDialog.get_active_dialog_buttons())
                except Exception:
                    if now - int(state["started_ms"]) >= 3000:
                        _fail_log(
                            "SendAutomaticDialog",
                            f"Timed out waiting for dialog/button {button_number}; dialog state could not be read within 3000ms.",
                        )
                        state["started_ms"] = None
                        return BehaviorTree.NodeState.FAILURE
                    return BehaviorTree.NodeState.RUNNING

                available_buttons: list[Any] = [button for button in buttons if getattr(button, "dialog_id", 0) != 0]
                if button_number >= len(available_buttons):
                    if now - int(state["started_ms"]) >= 3000:
                        _fail_log(
                            "SendAutomaticDialog",
                            f"Timed out waiting for automatic dialog button {button_number}; available count stayed at {len(available_buttons)} for 3000ms.",
                        )
                        state["started_ms"] = None
                        return BehaviorTree.NodeState.FAILURE
                    return BehaviorTree.NodeState.RUNNING

                state["started_ms"] = None
                return BehaviorTree.NodeState.SUCCESS

            def _send_automatic_dialog(button_number: int) -> BehaviorTree.NodeState:
                """
                Press the requested automatic dialog button.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Send Automatic Dialog Helper
                  Purpose: Dispatch the low-level automatic dialog button action.
                  UserDescription: Internal support routine.
                  Notes: Returns success immediately after sending the button press.
                """
                Player.SendAutomaticDialog(button_number)
                _log("SendAutomaticDialog", f"Sent automatic dialog button {button_number}.", log=log)
                return BehaviorTree.NodeState.SUCCESS

            tree: BehaviorTree.SequenceNode = BehaviorTree.SequenceNode(
                name="SendAutomaticDialog",
                children=[
                    BehaviorTree.ConditionNode(
                        name="WaitForAutomaticDialog",
                        condition_fn=_dialog_ready,
                    ),
                    BehaviorTree.ActionNode(
                        name="SendAutomaticDialogAction",
                        action_fn=lambda: _send_automatic_dialog(button_number),
                        aftercast_ms=aftercast_ms,
                    ),
                ],
            )
            return BehaviorTree(tree)

        @staticmethod
        def InteractAndDialog(dialog_id: str | int, log: bool = False) -> BehaviorTree:
            """
            Build a tree that interacts with the current target and then sends a dialog id.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Interact And Dialog
              Purpose: Interact with the current target and then send a dialog id.
              UserDescription: Use this when an interaction should be followed by a manual dialog response.
              Notes: Composes `InteractTarget` and `SendDialog` into a single sequence.
            """
            return BT.Composite.Sequence(
                BT.Player.InteractTarget(log=log),
                BT.Player.SendDialog(dialog_id=dialog_id, log=log),
                name="InteractAndDialog",
            )

        @staticmethod
        def InteractAndAutomaticDialog(button_number: int, log: bool = False) -> BehaviorTree:
            """
            Build a tree that interacts with the current target and then presses an automatic dialog button.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Interact And Automatic Dialog
              Purpose: Interact with the current target and then choose an automatic dialog button.
              UserDescription: Use this when an interaction should be followed by a visible dialog button selection.
              Notes: Composes `InteractTarget` and `SendAutomaticDialog` into a single sequence.
            """
            return BT.Composite.Sequence(
                BT.Player.InteractTarget(log=log),
                BT.Player.SendAutomaticDialog(button_number=button_number, log=log),
                name="InteractAndAutomaticDialog",
            )

        @staticmethod
        def CancelSkillRewardWindow(aftercast_ms: int = 1000) -> BehaviorTree:
            """
            Build a tree that dismisses the skill reward window if it is open.

            Meta:
              Expose: true
              Audience: beginner
              Display: Cancel Skill Reward Window
              Purpose: Close the skill reward window when it is present.
              UserDescription: Use this when a skill reward dialog can block later steps and should be dismissed safely.
              Notes: Succeeds immediately when the window is not present.
            """
            def _cancel_skill_reward_window() -> BehaviorTree.NodeState:
                cancel_button_frame_id = UIManager.GetFrameIDByHash(784833442)
                if not cancel_button_frame_id or not UIManager.FrameExists(cancel_button_frame_id):
                    return BehaviorTree.NodeState.SUCCESS
                UIManager.FrameClick(cancel_button_frame_id)
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="CancelSkillRewardWindow",
                    action_fn=_cancel_skill_reward_window,
                    aftercast_ms=max(0, int(aftercast_ms)),
                )
            )
        
        @staticmethod   
        def SetTitle(title_id: int, log: bool = False) -> BehaviorTree:
            """
            Build a tree that sets the active player title.

            Meta:
              Expose: true
              Audience: beginner
              Display: Set Title
              Purpose: Set the player's active title by title id.
              UserDescription: Use this when you want the player to switch to a specific title track.
              Notes: Logs the resolved title name when available.
            """
            def _set_title(title_id: int) -> BehaviorTree.NodeState:
                """
                Set the player's active title.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Set Title Helper
                  Purpose: Dispatch the low-level active-title change request.
                  UserDescription: Internal support routine.
                  Notes: Logs the resolved title name when available.
                """
                Player.SetActiveTitle(title_id)
                _log("SetTitle", f"Set title to {TITLE_NAME.get(title_id, 'Invalid')}.", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(name="SetTitle", action_fn=lambda: _set_title(title_id), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def SendChatCommand(command: str, log: bool = False) -> BehaviorTree:
            """
            Build a tree that sends a chat command.

            Meta:
              Expose: true
              Audience: beginner
              Display: Send Chat Command
              Purpose: Send a slash command or other chat command.
              UserDescription: Use this when you want a tree step to issue a chat command.
              Notes: Wraps a single chat command send with a short aftercast delay.
            """
            def _send_chat_command(command: str) -> BehaviorTree.NodeState:
                """
                Send the requested chat command.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Send Chat Command Helper
                  Purpose: Dispatch the low-level player chat-command request.
                  UserDescription: Internal support routine.
                  Notes: Returns success immediately after sending the command.
                """
                Player.SendChatCommand(command)
                _log("SendChatCommand", f"Sent chat command: {command}.", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(name="SendChatCommand", action_fn=lambda: _send_chat_command(command), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def BuySkill(skill_id: int, log: bool = False) -> BehaviorTree:
            """
            Build a tree that buys or learns a skill from a skill trainer.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Buy Skill
              Purpose: Buy or learn a skill by skill id.
              UserDescription: Use this when the player is already at a trainer and you want to purchase a skill.
              Notes: Wraps a single buy-skill action with a short aftercast delay.
            """
            def _buy_skill(skill_id: int) -> BehaviorTree.NodeState:
                """
                Send the requested buy-skill action.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Buy Skill Helper
                  Purpose: Dispatch the low-level skill purchase request.
                  UserDescription: Internal support routine.
                  Notes: Returns success immediately after sending the purchase action.
                """
                Player.BuySkill(skill_id)
                _log("BuySkill", f"Buying skill {skill_id}.", log=log)
                return BehaviorTree.NodeState.SUCCESS

            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(name="BuySkill", action_fn=lambda: _buy_skill(skill_id), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def UnlockBalthazarSkill(skill_id: int, use_pvp_remap: bool = True, log: bool = False) -> BehaviorTree:
            """
            Build a tree that unlocks a skill from the Priest of Balthazar flow.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Unlock Balthazar Skill
              Purpose: Unlock a skill by id through the Balthazar vendor flow.
              UserDescription: Use this when the player is already at the vendor and you want to unlock a skill.
              Notes: Can optionally remap the requested skill through the PvP skill id flow.
            """
            def _unlock_balthazar_skill(skill_id: int, use_pvp_remap: bool) -> BehaviorTree.NodeState:
                """
                Send the requested Balthazar unlock action.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Unlock Balthazar Skill Helper
                  Purpose: Dispatch the low-level Balthazar skill unlock request.
                  UserDescription: Internal support routine.
                  Notes: Preserves the requested PvP remap behavior from the enclosing routine.
                """
                Player.UnlockBalthazarSkill(skill_id, use_pvp_remap=use_pvp_remap)
                _log(
                    "UnlockBalthazarSkill",
                    f"Unlocking Balthazar skill {skill_id} (use_pvp_remap={use_pvp_remap}).",
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(
                name="UnlockBalthazarSkill",
                action_fn=lambda: _unlock_balthazar_skill(skill_id, use_pvp_remap),
                aftercast_ms=300,
            )
            return BehaviorTree(tree)

        @staticmethod
        def Resign(log: bool = False) -> BehaviorTree:
            """
            Build a tree that resigns the player from the current party or map.

            Meta:
              Expose: true
              Audience: beginner
              Display: Resign
              Purpose: Send the resign command.
              UserDescription: Use this when you want the player to resign from the current run.
              Notes: Implements resign by sending the `resign` chat command.
            """
            def _resign() -> BehaviorTree.NodeState:
                """
                Send the resign command.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Resign Helper
                  Purpose: Dispatch the low-level resign chat command.
                  UserDescription: Internal support routine.
                  Notes: Returns success immediately after sending the command.
                """
                Player.SendChatCommand("resign")
                _log("Resign", "Resigned from party.", log=log)
                return BehaviorTree.NodeState.SUCCESS

            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(name="Resign", action_fn=lambda: _resign(), aftercast_ms=250)
            return BehaviorTree(tree)

        @staticmethod
        def SendChatMessage(channel: str, message: str, log: bool = False) -> BehaviorTree:
            """
            Build a tree that sends a chat message to a specific channel.

            Meta:
              Expose: true
              Audience: beginner
              Display: Send Chat Message
              Purpose: Send a chat message to a specific channel.
              UserDescription: Use this when you want the player to post a message to chat from a tree step.
              Notes: Wraps a single chat send action with a short aftercast delay.
            """
            def _send_chat_message(channel: str, message: str) -> BehaviorTree.NodeState:
                """
                Send the requested chat message.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Send Chat Message Helper
                  Purpose: Dispatch the low-level player chat message request.
                  UserDescription: Internal support routine.
                  Notes: Returns success immediately after sending the message.
                """
                Player.SendChat(channel, message)
                _log("SendChatMessage", f"Sent chat message to {channel}: {message}.", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(name="SendChatMessage", action_fn=lambda: _send_chat_message(channel, message), aftercast_ms=300)
            return BehaviorTree(tree)
        
        @staticmethod
        def SendChatCommandWithMessage(channel: str, command: str, message: str, log: bool = False) -> BehaviorTree:
            """
            Build a tree that sends a chat command followed by a chat message.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Send Chat Command With Message
              Purpose: Send a chat command.
              UserDescription: Use this when you want to issue a chat command.
            """
            def _send_chat_command(_command: str) -> BehaviorTree.NodeState:
                """
                Send the requested chat command.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Send Chat Command Helper
                  Purpose: Dispatch the low-level player chat command request.
                  UserDescription: Internal support routine.
                  Notes: Returns success immediately after sending the command.
                """
                Player.SendChatCommand(_command)
                _log("SendChatCommandWithMessage", f"Sent chat command: {_command}.", log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(name="SendChatCommand", action_fn=lambda: _send_chat_command(command), aftercast_ms=300)
            return BehaviorTree(tree)
                

        @staticmethod
        def PrintMessageToConsole(source: str, message: str, message_type: int = Console.MessageType.Info) -> BehaviorTree:
            """
            Build a tree that prints a message to the console log.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Print Message To Console
              Purpose: Print a formatted message to the console log.
              UserDescription: Use this when you want a lightweight debug or progress step in a tree.
              Notes: Always logs to console and does not depend on the `log` flag pattern used elsewhere.
            """
            def _print_message_to_console(source: str, message: str, message_type: int) -> BehaviorTree.NodeState:
                """
                Print the requested message to the console log.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Print Message To Console Helper
                  Purpose: Emit a formatted console message for the enclosing routine.
                  UserDescription: Internal support routine.
                  Notes: Always logs to console and returns success immediately.
                """
                _fail_log(source, message, message_type)
                return BehaviorTree.NodeState.SUCCESS
             
            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(name="PrintMessageToConsole", action_fn=lambda: _print_message_to_console(source, message, message_type), aftercast_ms=100)
            return BehaviorTree(tree)

        @staticmethod
        def LogMessageToBlackboard(
            source: str,
            message: str,
            max_history: int = 200,
            include_source_in_message: bool = True,
        ) -> BehaviorTree:
            """
            Build a tree that stores a formatted log message on the blackboard.

            Meta:
              Expose: true
              Audience: advanced
              Display: Log Message To Blackboard
              Purpose: Store a timestamped message and message metadata on the blackboard.
              UserDescription: Use this when you want later tree steps or UI code to read a structured message from the blackboard.
              Notes: Updates `last_log_message`, metadata, and bounded history keys on the blackboard.
            """
            def _log_message_to_blackboard(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                """
                Write a formatted message and metadata payload to the blackboard.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Log Message To Blackboard Helper
                  Purpose: Store formatted log text and structured metadata on the blackboard.
                  UserDescription: Internal support routine.
                  Notes: Maintains bounded blackboard history under `blackboard_log_history`.
                """
                from ...Py4GWcorelib import Utils
                blackboard_key = "last_log_message"
                history_key = "blackboard_log_history"

                def _format_timestamp(timestamp_ms: int) -> str:
                    """
                    Format a millisecond timestamp into a readable time string.

                    Meta:
                      Expose: false
                      Audience: advanced
                      Display: Internal Format Timestamp Helper
                      Purpose: Convert a millisecond timestamp into the string format used by blackboard logging.
                      UserDescription: Internal support routine.
                      Notes: Produces `HH:MM:SS.mmm` output.
                    """
                    hours = (timestamp_ms // 3_600_000) % 24
                    minutes = (timestamp_ms // 60_000) % 60
                    seconds = (timestamp_ms // 1_000) % 60
                    milliseconds = timestamp_ms % 1_000
                    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

                timestamp: int = int(Utils.GetBaseTimestamp())
                formatted_timestamp: str = _format_timestamp(timestamp)
                body: str = f"[{source}] {message}" if include_source_in_message and source else message
                full_message: str = f"[{formatted_timestamp}] {body}"
                node.blackboard[blackboard_key] = full_message
                node.blackboard[f"{blackboard_key}_data"] = {
                    "timestamp": timestamp,
                    "formatted_timestamp": formatted_timestamp,
                    "source": source,
                    "message": message,
                    "body": body,
                    "full_message": full_message,
                }
                history: list[str] | Any = node.blackboard.get(history_key, [])
                if not isinstance(history, list):
                    history = []
                history.append(full_message)
                if max_history > 0 and len(history) > max_history:
                    history = history[-max_history:]
                node.blackboard[history_key] = history
                return BehaviorTree.NodeState.SUCCESS

            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(
                name="LogMessageToBlackboard",
                action_fn=_log_message_to_blackboard,
                aftercast_ms=0,
            )
            return BehaviorTree(tree)

        @staticmethod
        def LogMessage(
            source: str,
            message: str,
            message_type: int = Console.MessageType.Info,
            to_console: bool | Callable[[], bool] = True,
            to_blackboard: bool = False,
            max_history: int = 200,
            include_source_in_blackboard_message: bool = True,
        ) -> BehaviorTree:
            """
            Build a tree that logs a message to console, blackboard, or both.

            Meta:
              Expose: true
              Audience: advanced
              Display: Log Message
              Purpose: Broadcast a timestamped message to console, blackboard, or both.
              UserDescription: Use this when you want one routine to publish progress or status information to multiple outputs.
              Notes: Supports callable `to_console` evaluation and blackboard history storage.
            """
            def _log_message(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                """
                Broadcast a formatted message to console, blackboard, or both.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Log Message Helper
                  Purpose: Execute the output routing logic for the enclosing log-message routine.
                  UserDescription: Internal support routine.
                  Notes: Supports callable console gating and blackboard history storage.
                """
                from ...Py4GWcorelib import Utils
                blackboard_key = "last_log_message"
                history_key = "blackboard_log_history"

                def _format_timestamp(timestamp_ms: int) -> str:
                    """
                    Format a millisecond timestamp into a readable time string.

                    Meta:
                      Expose: false
                      Audience: advanced
                      Display: Internal Format Timestamp Helper
                      Purpose: Convert a millisecond timestamp into the string format used by logging helpers.
                      UserDescription: Internal support routine.
                      Notes: Produces `HH:MM:SS.mmm` output.
                    """
                    hours = (timestamp_ms // 3_600_000) % 24
                    minutes = (timestamp_ms // 60_000) % 60
                    seconds = (timestamp_ms // 1_000) % 60
                    milliseconds = timestamp_ms % 1_000
                    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

                timestamp: int = int(Utils.GetBaseTimestamp())
                formatted_timestamp: str = _format_timestamp(timestamp)
                should_print_to_console: bool = to_console() if callable(to_console) else to_console
                if should_print_to_console:
                    _fail_log(source, message, message_type)
                if to_blackboard:
                    body: str = f"[{source}] {message}" if include_source_in_blackboard_message and source else message
                    full_message: str = f"[{formatted_timestamp}] {body}"
                    node.blackboard[blackboard_key] = full_message
                    node.blackboard[f"{blackboard_key}_data"] = {
                        "timestamp": timestamp,
                        "formatted_timestamp": formatted_timestamp,
                        "source": source,
                        "message": message,
                        "body": body,
                        "full_message": full_message,
                        "message_type": message_type,
                    }
                    history: list[str] | Any = node.blackboard.get(history_key, [])
                    if not isinstance(history, list):
                        history = []
                    history.append(full_message)
                    if max_history > 0 and len(history) > max_history:
                        history = history[-max_history:]
                    node.blackboard[history_key] = history
                return BehaviorTree.NodeState.SUCCESS

            tree: BehaviorTree.ActionNode = BehaviorTree.ActionNode(
                name="LogMessage",
                action_fn=_log_message,
                aftercast_ms=100,
            )
            return BehaviorTree(tree)

        @staticmethod
        def StoreProfessionNames(
            blackboard_primary_key: str = "player_primary_profession_name",
            blackboard_secondary_key: str = "player_secondary_profession_name",
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that stores the player's primary profession name on the blackboard.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Store Primary Profession Name
              Purpose: Resolve the player's primary profession name and store it on the blackboard.
              UserDescription: Use this when later routing logic needs the player's primary profession name.
              Notes: Writes the resolved profession name to the configured blackboard key.
            """
            def _store_profession_names(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                """
                Resolve the player's primary profession name and store it on the blackboard.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Store Profession Names Helper
                  Purpose: Capture the player's primary profession name for later BT steps.
                  UserDescription: Internal support routine.
                  Notes: Writes the resolved profession name to the configured blackboard key and fails when resolution returns empty.
                """
                primary_name: str
                secondary_name: str
                primary_name, secondary_name = Agent.GetProfessionNames(Player.GetAgentID())
                node.blackboard[blackboard_primary_key] = primary_name
                node.blackboard[blackboard_secondary_key] = secondary_name

                if not primary_name:
                    _fail_log(
                        "StoreProfessionNames",
                        "Failed to resolve player primary profession name.",
                    )
                    return BehaviorTree.NodeState.FAILURE

                _log(
                    "StoreProfessionNames",
                    f"Stored primary profession '{primary_name}' in blackboard key '{blackboard_primary_key}'.",
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="StoreProfessionNames",
                    action_fn=_store_profession_names,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def SaveBlackboardValue(
            key: str,
            value: Any | Callable[[], Any],
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that stores a value in the blackboard under a key.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Save Blackboard Value
              Purpose: Store a value in the blackboard for later BT steps.
              UserDescription: Use this when later nodes need to read a value you want to save under a known key.
              Notes: Accepts either a literal value or a callable that is evaluated at runtime.
            """
            def _save_blackboard_value(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                """
                Save a literal or runtime-computed value into the blackboard.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Save Blackboard Value Helper
                  Purpose: Write a value to a configured blackboard key.
                  UserDescription: Internal support routine.
                  Notes: Callable inputs are evaluated at execution time.
                """
                resolved_value: Any = value() if callable(value) else value
                node.blackboard[key] = resolved_value
                _log("SaveBlackboardValue", f"Stored blackboard key '{key}'.", log=log)
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="SaveBlackboardValue",
                    action_fn=_save_blackboard_value,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def LoadBlackboardValue(
            source_key: str,
            target_key: str = "result",
            fail_if_missing: bool = True,
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that copies a blackboard value from one key to another.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Load Blackboard Value
              Purpose: Read a saved blackboard value and copy it to another key.
              UserDescription: Use this when a later subtree expects a value under a specific blackboard key such as `result`.
              Notes: Fails when the source key is missing unless `fail_if_missing` is false.
            """
            def _load_blackboard_value(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                """
                Copy a blackboard value from the source key to the target key.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Load Blackboard Value Helper
                  Purpose: Move or mirror a saved blackboard value for later BT steps.
                  UserDescription: Internal support routine.
                  Notes: Reads from the current shared blackboard at runtime.
                """
                if source_key not in node.blackboard:
                    if fail_if_missing:
                        _fail_log("LoadBlackboardValue", f"Blackboard key '{source_key}' is missing.")
                    else:
                        _log("LoadBlackboardValue", f"Blackboard key '{source_key}' is missing.", log=log)
                    return (
                        BehaviorTree.NodeState.FAILURE
                        if fail_if_missing
                        else BehaviorTree.NodeState.SUCCESS
                    )

                node.blackboard[target_key] = node.blackboard[source_key]
                _log(
                    "LoadBlackboardValue",
                    f"Copied blackboard key '{source_key}' to '{target_key}'.",
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="LoadBlackboardValue",
                    action_fn=_load_blackboard_value,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def HasBlackboardValue(
            key: str,
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that succeeds only when a blackboard key exists.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Has Blackboard Value
              Purpose: Check whether a blackboard key exists.
              UserDescription: Use this when a branch should only continue if a prior step saved a value.
              Notes: Checks key existence, not truthiness of the stored value.
            """
            def _check_blackboard_value(node: BehaviorTree.Node) -> bool:
                exists: bool = key in node.blackboard
                _log("HasBlackboardValue", f"Blackboard key '{key}' exists={exists}.", log=log)
                return exists

            return BehaviorTree(
                BehaviorTree.ConditionNode(
                    name="HasBlackboardValue",
                    condition_fn=_check_blackboard_value,
                )
            )

        @staticmethod
        def BlackboardValueEquals(
            key: str,
            value,
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that succeeds when a blackboard value equals the expected value.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Blackboard Value Equals
              Purpose: Check a stored blackboard value against an expected value.
              UserDescription: Use this when a branch should continue only for a specific stored value.
              Notes: Uses normal Python equality against the value currently stored for the key.
            """
            def _blackboard_value_equals(node: BehaviorTree.Node) -> bool:
                current_value = node.blackboard.get(key)
                matches = current_value == value
                _log(
                    "BlackboardValueEquals",
                    f"Blackboard key '{key}' value={current_value!r} expected={value!r} matches={matches}.",
                    log=log,
                )
                return matches

            return BehaviorTree(
                BehaviorTree.ConditionNode(
                    name="BlackboardValueEquals",
                    condition_fn=_blackboard_value_equals,
                )
            )

        @staticmethod
        def ClearBlackboardValue(
            key: str,
            log: bool = False,
        ) -> BehaviorTree:
            """
            Build a tree that removes a key from the blackboard.

            Meta:
              Expose: true
              Audience: intermediate
              Display: Clear Blackboard Value
              Purpose: Remove a saved value from the blackboard.
              UserDescription: Use this when a temporary blackboard value should be discarded before later steps run.
              Notes: Succeeds even if the key did not exist.
            """
            def _clear_blackboard_value(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                node.blackboard.pop(key, None)
                _log("ClearBlackboardValue", f"Cleared blackboard key '{key}'.", log=log)
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="ClearBlackboardValue",
                    action_fn=_clear_blackboard_value,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def StoreRerollContext(
            character_name_key: str = "reroll_character_name",
            profession_key: str = "reroll_primary_profession",
            campaign_key: str = "reroll_campaign",
            campaign_name: str = "Nightfall",
            fallback_profession: str = "Warrior",
        ) -> BehaviorTree:
            def _store_reroll_context(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                primary_profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
                node.blackboard[character_name_key] = Player.GetName()
                node.blackboard[profession_key] = primary_profession or fallback_profession
                node.blackboard[campaign_key] = campaign_name
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="StoreRerollContext",
                    action_fn=_store_reroll_context,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def LogoutToCharacterSelect() -> BehaviorTree:
            def _logout_to_character_select() -> BehaviorTree.NodeState:
                if Map.Pregame.InCharacterSelectScreen():
                    return BehaviorTree.NodeState.SUCCESS
                Map.Pregame.LogoutToCharacterSelect()
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="LogoutToCharacterSelect",
                    action_fn=_logout_to_character_select,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def WaitUntilCharacterSelect(timeout_ms: int = 45000) -> BehaviorTree:
            def _wait_until_character_select() -> BehaviorTree.NodeState:
                if Map.Pregame.InCharacterSelectScreen():
                    return BehaviorTree.NodeState.SUCCESS
                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree(
                BehaviorTree.WaitUntilNode(
                    name="WaitUntilCharacterSelect",
                    condition_fn=_wait_until_character_select,
                    throttle_interval_ms=250,
                    timeout_ms=timeout_ms,
                )
            )

        @staticmethod
        def ClickWindowFrame(frame_name: str, aftercast_ms: int = 250) -> BehaviorTree:
            def _click_window_frame() -> BehaviorTree.NodeState:
                frame = WindowFrames.get(frame_name)
                if frame is None:
                    return BehaviorTree.NodeState.FAILURE
                frame.FrameClick()
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name=f"ClickWindowFrame({frame_name})",
                    action_fn=_click_window_frame,
                    aftercast_ms=aftercast_ms,
                )
            )

        @staticmethod
        def TypeTextFromBlackboard(
            key: str,
            delay_ms: int = 50,
            name: str = "TypeTextFromBlackboard",
        ) -> BehaviorTree:
            state = {
                "text": None,
                "index": 0,
                "last_ms": 0.0,
            }

            def _type_text(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                if state["text"] is None:
                    state["text"] = str(node.blackboard.get(key, "") or "")
                    state["index"] = 0
                    state["last_ms"] = 0.0
                    if not state["text"]:
                        return BehaviorTree.NodeState.FAILURE

                now = time.monotonic() * 1000
                if state["last_ms"] and now - state["last_ms"] < delay_ms:
                    return BehaviorTree.NodeState.RUNNING

                text = state["text"]
                if state["index"] >= len(text):
                    state["text"] = None
                    state["index"] = 0
                    state["last_ms"] = 0.0
                    return BehaviorTree.NodeState.SUCCESS

                char = text[state["index"]]
                key_info = CHAR_MAP.get(char)
                if key_info is not None:
                    mapped_key, needs_shift = key_info
                    if needs_shift:
                        Keystroke.Press(Key.LShift.value)
                    Keystroke.PressAndRelease(mapped_key.value)
                    if needs_shift:
                        Keystroke.Release(Key.LShift.value)

                state["index"] += 1
                state["last_ms"] = now
                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name=name,
                    action_fn=_type_text,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def PasteTextFromBlackboard(
            key: str,
            name: str = "PasteTextFromBlackboard",
        ) -> BehaviorTree:
            def _paste_text(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                text = str(node.blackboard.get(key, "") or "")
                if not text:
                    return BehaviorTree.NodeState.FAILURE
                PyImGui.set_clipboard_text(text)
                Keystroke.PressAndReleaseCombo([Key.Ctrl.value, Key.V.value])
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name=name,
                    action_fn=_paste_text,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def PressRightArrowTimes(
            count_key: str,
            delay_ms: int = 100,
            name: str = "PressRightArrowTimes",
        ) -> BehaviorTree:
            state = {
                "remaining": None,
                "last_ms": 0.0,
            }

            def _press_right_arrow_times(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                if state["remaining"] is None:
                    state["remaining"] = max(0, int(node.blackboard.get(count_key, 0) or 0))
                    state["last_ms"] = 0.0

                if state["remaining"] <= 0:
                    state["remaining"] = None
                    state["last_ms"] = 0.0
                    return BehaviorTree.NodeState.SUCCESS

                now = time.monotonic() * 1000
                if state["last_ms"] and now - state["last_ms"] < delay_ms:
                    return BehaviorTree.NodeState.RUNNING

                Keystroke.PressAndRelease(Key.RightArrow.value)
                state["remaining"] -= 1
                state["last_ms"] = now
                return BehaviorTree.NodeState.RUNNING

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name=name,
                    action_fn=_press_right_arrow_times,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def StoreCampaignArrowCount(
            campaign_key: str = "reroll_campaign",
            count_key: str = "reroll_campaign_arrow_count",
        ) -> BehaviorTree:
            campaign_counts = {
                "Nightfall": 0,
                "Prophecies": 1,
                "Factions": 2,
            }

            def _store_campaign_arrow_count(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                campaign_name = str(node.blackboard.get(campaign_key, "Nightfall") or "Nightfall")
                node.blackboard[count_key] = campaign_counts.get(campaign_name, 0)
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="StoreCampaignArrowCount",
                    action_fn=_store_campaign_arrow_count,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def StoreProfessionArrowCount(
            profession_key: str = "reroll_primary_profession",
            count_key: str = "reroll_profession_arrow_count",
        ) -> BehaviorTree:
            profession_counts = {
                "Warrior": 0,
                "Ranger": 1,
                "Monk": 2,
                "Necromancer": 3,
                "Mesmer": 4,
                "Elementalist": 5,
                "Assassin": 6,
                "Ritualist": 7,
                "Paragon": 6,
                "Dervish": 7,
            }

            def _store_profession_arrow_count(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                profession_name = str(node.blackboard.get(profession_key, "Warrior") or "Warrior")
                node.blackboard[count_key] = profession_counts.get(profession_name, 0)
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="StoreProfessionArrowCount",
                    action_fn=_store_profession_arrow_count,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def ResolveRerollNewCharacterName(
            character_name_key: str = "reroll_character_name",
            new_character_name_key: str = "reroll_character_name",
        ) -> BehaviorTree:
            def _resolve_new_name(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
                character_name = str(node.blackboard.get(character_name_key, "") or "")
                if not character_name:
                    return BehaviorTree.NodeState.FAILURE
                node.blackboard[new_character_name_key] = character_name
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="ResolveRerollNewCharacterName",
                    action_fn=_resolve_new_name,
                    aftercast_ms=0,
                )
            )

        @staticmethod
        def DeleteCharacterFromBlackboard(
            character_name_key: str = "reroll_character_name",
            timeout_ms: int = 45000,
        ) -> BehaviorTree:
            return BehaviorTree(
                BehaviorTree.SequenceNode(
                    name="DeleteCharacterFromBlackboard",
                    children=[
                        BTPlayer.LogoutToCharacterSelect().root,
                        BTPlayer.WaitUntilCharacterSelect(timeout_ms=timeout_ms).root,
                        BTPlayer.Wait(1000).root,
                        BTPlayer.ClickWindowFrame("DeleteCharacterButton", aftercast_ms=750).root,
                        BTPlayer.PasteTextFromBlackboard(character_name_key, name="PasteDeleteCharacterName").root,
                        BTPlayer.Wait(750).root,
                        BTPlayer.ClickWindowFrame("FinalDeleteCharacterButton", aftercast_ms=750).root,
                        BTPlayer.Wait(7000).root,
                    ],
                )
            )

        @staticmethod
        def CreateCharacterFromBlackboard(
            character_name_key: str = "reroll_new_character_name",
            campaign_key: str = "reroll_campaign",
            profession_key: str = "reroll_primary_profession",
            timeout_ms: int = 60000,
        ) -> BehaviorTree:
            return BehaviorTree(
                BehaviorTree.SequenceNode(
                    name="CreateCharacterFromBlackboard",
                    children=[
                        BTPlayer.WaitUntilCharacterSelect(timeout_ms=timeout_ms).root,
                        BTPlayer.Wait(1000).root,
                        BTPlayer.ClickWindowFrame("CreateCharacterButton1", aftercast_ms=500).root,
                        BTPlayer.ClickWindowFrame("CreateCharacterButton2", aftercast_ms=1000).root,
                        BTPlayer.ClickWindowFrame("CreateCharacterTypeNextButton", aftercast_ms=1000).root,
                        BTPlayer.StoreCampaignArrowCount(campaign_key=campaign_key).root,
                        BTPlayer.PressRightArrowTimes("reroll_campaign_arrow_count", name="SelectCampaign").root,
                        BTPlayer.Wait(500).root,
                        BTPlayer.ClickWindowFrame("CreateCharacterNextButtonGeneric", aftercast_ms=1000).root,
                        BTPlayer.StoreProfessionArrowCount(profession_key=profession_key).root,
                        BTPlayer.PressRightArrowTimes("reroll_profession_arrow_count", name="SelectProfession").root,
                        BTPlayer.Wait(500).root,
                        BTPlayer.ClickWindowFrame("CreateCharacterNextButtonGeneric", aftercast_ms=1000).root,
                        BTPlayer.ClickWindowFrame("CreateCharacterNextButtonGeneric", aftercast_ms=1000).root,
                        BTPlayer.ClickWindowFrame("CreateCharacterNextButtonGeneric", aftercast_ms=1000).root,
                        BTPlayer.ClickWindowFrame("CreateCharacterNextButtonGeneric", aftercast_ms=1000).root,
                        BTPlayer.PasteTextFromBlackboard(character_name_key, name="PasteCreateCharacterName").root,
                        BTPlayer.Wait(1000).root,
                        BTPlayer.ClickWindowFrame("FinalCreateCharacterButton", aftercast_ms=3000).root,
                        BTPlayer.Wait(7000).root,
                    ],
                )
            )

        @staticmethod
        def ResetActionQueues() -> BehaviorTree:
            def _reset_action_queues() -> BehaviorTree.NodeState:
                ActionQueueManager().ResetAllQueues()
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="ResetActionQueues",
                    action_fn=_reset_action_queues,
                    aftercast_ms=0,
                )
            )
         
        @staticmethod
        def Wait(duration_ms: int, log: bool = False) -> BehaviorTree:
            """
            Build a tree that waits for a fixed amount of time.

            Meta:
              Expose: true
              Audience: beginner
              Display: Wait
              Purpose: Wait for a fixed duration in milliseconds.
              UserDescription: Use this when you want to insert a timed delay between BT steps.
              Notes: Logs the wait start when enabled and then uses `WaitForTimeNode` for the duration.
            """
            def _wait_started() -> BehaviorTree.NodeState:
                """
                Log the beginning of the fixed wait step.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Wait Started Helper
                  Purpose: Emit the optional wait-start log for the enclosing wait routine.
                  UserDescription: Internal support routine.
                  Notes: Returns success immediately before the timed wait node begins.
                """
                _log("Wait", f"Waiting for {duration_ms}ms.", log=log)
                return BehaviorTree.NodeState.SUCCESS

            tree: BehaviorTree = BehaviorTree(
                BehaviorTree.SequenceNode(
                    name="Wait",
                    children=[
                        BehaviorTree.ConditionNode(name="WaitStarted", condition_fn=_wait_started),
                        BehaviorTree.WaitForTimeNode(name="WaitForTime", duration_ms=duration_ms),
                    ],
                )
            )
            return tree
