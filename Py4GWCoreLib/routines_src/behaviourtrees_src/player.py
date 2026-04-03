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
from typing import Callable

from ...GlobalCache import GLOBAL_CACHE
from ...Py4GWcorelib import ConsoleLog, Console, Vec2f
from ...Map import Map
from ...Agent import Agent
from ...Player import Player
from ...enums_src.Title_enums import TITLE_NAME
from ...enums import SharedCommandType
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree
from ..Checks import Checks


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
    def __getattr__(self, name: str):
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
        def InteractAgent(agent_id:int, log:bool=False):
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
            def _interact_agent(agent_id:int):
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
                ConsoleLog("InteractAgent", f"Interacted with agent {agent_id}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="InteractAgent", action_fn=lambda: _interact_agent(agent_id), aftercast_ms=250)
            return BehaviorTree(tree)
            
        @staticmethod
        def InteractTarget(log:bool=False):
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
            def _get_target_id(node: BehaviorTree.Node):
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
            Build a tree that changes the player's target to a specific agent id.

            Meta:
              Expose: true
              Audience: beginner
              Display: Change Target
              Purpose: Change the player's target to a specific agent id.
              UserDescription: Use this when you want to force targeting to a known agent id.
              Notes: Fails if the provided agent id is zero.
            """
            def _change_target():
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
                    ConsoleLog("ChangeTarget", f"Changed target to agent {agent_id}.", Console.MessageType.Info, log=log)
                    return BehaviorTree.NodeState.SUCCESS
                
                ConsoleLog("ChangeTarget", "Invalid agent ID provided for targeting.", Console.MessageType.Error, log=log)
                return BehaviorTree.NodeState.FAILURE
            
            tree = BehaviorTree.ActionNode(name="ChangeTarget", action_fn=lambda: _change_target(), aftercast_ms=250)
            return BehaviorTree(tree)
        
        @staticmethod
        def SendDialog(dialog_id:str | int, log:bool=False):
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
            def _send_dialog(dialog_id):
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
                ConsoleLog("SendDialog", f"Sent dialog {dialog_id}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SendDialog", action_fn=lambda: _send_dialog(dialog_id), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def SendAutomaticDialog(button_number: int, log: bool = False):
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

            def _dialog_ready():
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
                            ConsoleLog(
                                "SendAutomaticDialog",
                                f"Timed out waiting for dialog/button {button_number}; no dialog became active within 3000ms.",
                                Console.MessageType.Warning,
                                log=True,
                            )
                            state["started_ms"] = None
                            return BehaviorTree.NodeState.FAILURE
                        return BehaviorTree.NodeState.RUNNING

                    buttons = list(PyDialog.PyDialog.get_active_dialog_buttons())
                except Exception:
                    if now - int(state["started_ms"]) >= 3000:
                        ConsoleLog(
                            "SendAutomaticDialog",
                            f"Timed out waiting for dialog/button {button_number}; dialog state could not be read within 3000ms.",
                            Console.MessageType.Warning,
                            log=True,
                        )
                        state["started_ms"] = None
                        return BehaviorTree.NodeState.FAILURE
                    return BehaviorTree.NodeState.RUNNING

                available_buttons = [button for button in buttons if getattr(button, "dialog_id", 0) != 0]
                if button_number >= len(available_buttons):
                    if now - int(state["started_ms"]) >= 3000:
                        ConsoleLog(
                            "SendAutomaticDialog",
                            f"Timed out waiting for automatic dialog button {button_number}; available count stayed at {len(available_buttons)} for 3000ms.",
                            Console.MessageType.Warning,
                            log=True,
                        )
                        state["started_ms"] = None
                        return BehaviorTree.NodeState.FAILURE
                    return BehaviorTree.NodeState.RUNNING

                state["started_ms"] = None
                return BehaviorTree.NodeState.SUCCESS

            def _send_automatic_dialog(button_number: int):
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
                ConsoleLog(
                    "SendAutomaticDialog",
                    f"Sent automatic dialog button {button_number}.",
                    Console.MessageType.Info,
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.SequenceNode(
                name="SendAutomaticDialog",
                children=[
                    BehaviorTree.ConditionNode(
                        name="WaitForAutomaticDialog",
                        condition_fn=_dialog_ready,
                    ),
                    BehaviorTree.ActionNode(
                        name="SendAutomaticDialogAction",
                        action_fn=lambda: _send_automatic_dialog(button_number),
                        aftercast_ms=300,
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
        def SetTitle(title_id:int, log:bool=False):
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
            def _set_title(title_id:int):
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
                ConsoleLog("SetTitle", f"Set title to {TITLE_NAME.get(title_id, 'Invalid')}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SetTitle", action_fn=lambda: _set_title(title_id), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def SendChatCommand(command:str, log=False):
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
            def _send_chat_command(command:str):
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
                ConsoleLog("SendChatCommand", f"Sent chat command: {command}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SendChatCommand", action_fn=lambda: _send_chat_command(command), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def BuySkill(skill_id: int, log: bool = False):
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
            def _buy_skill(skill_id: int):
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
                ConsoleLog("BuySkill", f"Buying skill {skill_id}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.ActionNode(name="BuySkill", action_fn=lambda: _buy_skill(skill_id), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def UnlockBalthazarSkill(skill_id: int, use_pvp_remap: bool = True, log: bool = False):
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
            def _unlock_balthazar_skill(skill_id: int, use_pvp_remap: bool):
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
            Build a tree that resigns the player from the current party or map.

            Meta:
              Expose: true
              Audience: beginner
              Display: Resign
              Purpose: Send the resign command.
              UserDescription: Use this when you want the player to resign from the current run.
              Notes: Implements resign by sending the `resign` chat command.
            """
            def _resign():
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
                ConsoleLog("Resign", "Resigned from party.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.ActionNode(name="Resign", action_fn=lambda: _resign(), aftercast_ms=250)
            return BehaviorTree(tree)

        @staticmethod
        def SendChatMessage(channel:str, message:str, log=False):
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
            def _send_chat_message(channel:str, message:str):
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
                ConsoleLog("SendChatMessage", f"Sent chat message to {channel}: {message}.", Console.MessageType.Info, log=log)
                return BehaviorTree.NodeState.SUCCESS
            
            tree = BehaviorTree.ActionNode(name="SendChatMessage", action_fn=lambda: _send_chat_message(channel, message), aftercast_ms=300)
            return BehaviorTree(tree)

        @staticmethod
        def PrintMessageToConsole(source:str, message: str, message_type: int = Console.MessageType.Info):
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
            def _print_message_to_console(source:str, message: str, message_type: int):
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
                ConsoleLog(source, message, message_type, log=True)
                return BehaviorTree.NodeState.SUCCESS
             
            tree = BehaviorTree.ActionNode(name="PrintMessageToConsole", action_fn=lambda: _print_message_to_console(source, message, message_type), aftercast_ms=100)
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
            def _log_message_to_blackboard(node: BehaviorTree.Node):
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

                timestamp = int(Utils.GetBaseTimestamp())
                formatted_timestamp = _format_timestamp(timestamp)
                body = f"[{source}] {message}" if include_source_in_message and source else message
                full_message = f"[{formatted_timestamp}] {body}"
                node.blackboard[blackboard_key] = full_message
                node.blackboard[f"{blackboard_key}_data"] = {
                    "timestamp": timestamp,
                    "formatted_timestamp": formatted_timestamp,
                    "source": source,
                    "message": message,
                    "body": body,
                    "full_message": full_message,
                }
                history = node.blackboard.get(history_key, [])
                if not isinstance(history, list):
                    history = []
                history.append(full_message)
                if max_history > 0 and len(history) > max_history:
                    history = history[-max_history:]
                node.blackboard[history_key] = history
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.ActionNode(
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
            def _log_message(node: BehaviorTree.Node):
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

                timestamp = int(Utils.GetBaseTimestamp())
                formatted_timestamp = _format_timestamp(timestamp)
                should_print_to_console = to_console() if callable(to_console) else to_console
                if should_print_to_console:
                    ConsoleLog(source, message, message_type, log=True)
                if to_blackboard:
                    body = f"[{source}] {message}" if include_source_in_blackboard_message and source else message
                    full_message = f"[{formatted_timestamp}] {body}"
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
                    history = node.blackboard.get(history_key, [])
                    if not isinstance(history, list):
                        history = []
                    history.append(full_message)
                    if max_history > 0 and len(history) > max_history:
                        history = history[-max_history:]
                    node.blackboard[history_key] = history
                return BehaviorTree.NodeState.SUCCESS

            tree = BehaviorTree.ActionNode(
                name="LogMessage",
                action_fn=_log_message,
                aftercast_ms=0,
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
            def _store_profession_names(node: BehaviorTree.Node):
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
                primary_name, secondary_name = Agent.GetProfessionNames(Player.GetAgentID())
                node.blackboard[blackboard_primary_key] = primary_name
                node.blackboard[blackboard_secondary_key] = secondary_name

                if not primary_name:
                    ConsoleLog(
                        "StoreProfessionNames",
                        "Failed to resolve player primary profession name.",
                        Console.MessageType.Warning,
                        log=True if log else False,
                    )
                    return BehaviorTree.NodeState.FAILURE

                ConsoleLog(
                    "StoreProfessionNames",
                    f"Stored primary profession '{primary_name}' in blackboard key '{blackboard_primary_key}'.",
                    Console.MessageType.Info,
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
            value,
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
            def _save_blackboard_value(node: BehaviorTree.Node):
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
                resolved_value = value() if callable(value) else value
                node.blackboard[key] = resolved_value
                ConsoleLog(
                    "SaveBlackboardValue",
                    f"Stored blackboard key '{key}'.",
                    Console.MessageType.Info,
                    log=log,
                )
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
            def _load_blackboard_value(node: BehaviorTree.Node):
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
                    ConsoleLog(
                        "LoadBlackboardValue",
                        f"Blackboard key '{source_key}' is missing.",
                        Console.MessageType.Warning,
                        log=log or fail_if_missing,
                    )
                    return (
                        BehaviorTree.NodeState.FAILURE
                        if fail_if_missing
                        else BehaviorTree.NodeState.SUCCESS
                    )

                node.blackboard[target_key] = node.blackboard[source_key]
                ConsoleLog(
                    "LoadBlackboardValue",
                    f"Copied blackboard key '{source_key}' to '{target_key}'.",
                    Console.MessageType.Info,
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
            def _check_blackboard_value(node: BehaviorTree.Node):
                exists = key in node.blackboard
                ConsoleLog(
                    "HasBlackboardValue",
                    f"Blackboard key '{key}' exists={exists}.",
                    Console.MessageType.Info,
                    log=log,
                )
                return exists

            return BehaviorTree(
                BehaviorTree.ConditionNode(
                    name="HasBlackboardValue",
                    condition_fn=_check_blackboard_value,
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
            def _clear_blackboard_value(node: BehaviorTree.Node):
                node.blackboard.pop(key, None)
                ConsoleLog(
                    "ClearBlackboardValue",
                    f"Cleared blackboard key '{key}'.",
                    Console.MessageType.Info,
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="ClearBlackboardValue",
                    action_fn=_clear_blackboard_value,
                    aftercast_ms=0,
                )
            )
         
        @staticmethod
        def Wait(duration_ms: int, log: bool = False):
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
            def _wait_started():
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
            timeout_ms: int = 15000,
            stall_threshold_ms: int = 500,
            pause_on_combat: bool = True,
            pause_flag_key: str = "PAUSE_MOVEMENT",
            log: bool = False,
            path_points_override: list[tuple[float, float]] | None = None,
        ):
            """
            Build a tree that moves the player to target coordinates using autopathing and runtime recovery logic.

            Meta:
              Expose: true
              Audience: advanced
              Display: Move
              Purpose: Move the player to target coordinates with waypoint tracking, pause handling, and timeout protection.
              UserDescription: Use this when you want a robust movement routine that can pause, recover, and report progress through the blackboard.
              Notes: Writes movement state to the blackboard and uses a parallel runtime with move, timeout, and map-transition watchers.
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
                "resume_recovery_reason": "",
                "resume_recovery_restart_pending": False,
                "current_pause_reason": "",
                "last_logged_waypoint_index": -1,
                "failure_details": {},
            }

            def _reset_runtime():
                """
                Reset transient runtime movement state.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Reset Runtime Helper
                  Purpose: Clear path-following and pause-related runtime state for the movement routine.
                  UserDescription: Internal support routine.
                  Notes: Leaves final result state alone so completion reporting can happen separately.
                """
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
                state["resume_recovery_reason"] = ""
                state["resume_recovery_restart_pending"] = False
                state["current_pause_reason"] = ""
                state["last_logged_waypoint_index"] = -1
                state["failure_details"] = {}

            def _reset_result():
                """
                Reset completion and failure-result tracking for movement.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Reset Result Helper
                  Purpose: Clear the final result bookkeeping before a new movement attempt begins.
                  UserDescription: Internal support routine.
                  Notes: Preserves path runtime state until the broader runtime reset runs.
                """
                state["completed"] = False
                state["result_state"] = ""
                state["result_reason"] = ""
                state["failure_details"] = {}

            def _set_blackboard(node: BehaviorTree.Node, move_state: str, reason: str = ""):
                """
                Publish movement state and path details to the blackboard.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Set Blackboard Helper
                  Purpose: Write the current movement status, path information, and recovery flags to the blackboard.
                  UserDescription: Internal support routine.
                  Notes: Updates move-state keys consumed by diagnostics, UI, and downstream BT logic.
                """
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
                node.blackboard["move_resume_recovery_reason"] = state["resume_recovery_reason"]
                node.blackboard["move_resume_recovery_restart_pending"] = bool(state["resume_recovery_restart_pending"])
                node.blackboard["move_current_pause_reason"] = state["current_pause_reason"]

            def _debug_enabled(node: BehaviorTree.Node) -> bool:
                """
                Determine whether verbose movement debug logging should be active.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Debug Enabled Helper
                  Purpose: Combine the routine log flag with blackboard debug overrides for movement logging.
                  UserDescription: Internal support routine.
                  Notes: Reads `MOVE_DEBUG` from the blackboard when available.
                """
                return log or (bool(node.blackboard.get("MOVE_DEBUG", False)) if node is not None else False)

            def _finalize_move(node: BehaviorTree.Node, move_state: str, reason: str = ""):
                """
                Finalize movement with a terminal status and publish the result.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Finalize Move Helper
                  Purpose: Mark movement complete, emit final diagnostics, publish blackboard state, and reset runtime state.
                  UserDescription: Internal support routine.
                  Notes: Includes detailed failure diagnostics when the movement result is `failed`.
                """
                state["completed"] = True
                state["result_state"] = move_state
                state["result_reason"] = reason
                if move_state == "failed":
                    current_pos = Player.GetXY()
                    waypoint = None
                    distance_to_waypoint = None
                    remaining_waypoints = 0
                    if state["path_points"] is not None and 0 <= state["path_index"] < len(state["path_points"]):
                        waypoint = state["path_points"][state["path_index"]]
                        from ...Py4GWcorelib import Utils
                        distance_to_waypoint = Utils.Distance(current_pos, waypoint)
                        remaining_waypoints = len(state["path_points"]) - state["path_index"]
                    failure_details = state.get("failure_details", {})
                    ConsoleLog(
                        "Move",
                        (
                            f"Movement failed: reason={reason or 'unknown'}, target=({x}, {y}), "
                            f"path_index={state['path_index']}, current_pos={current_pos}, "
                            f"waypoint={waypoint}, distance_to_waypoint={distance_to_waypoint}, "
                            f"remaining_waypoints={remaining_waypoints}, move_issued={state['move_issued']}, "
                            f"resume_recovery_active={state['resume_recovery_active']}, "
                            f"resume_recovery_reason={state['resume_recovery_reason']}, "
                            f"current_pause_reason={state['current_pause_reason']}, "
                            f"failure_details={failure_details}."
                        ),
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
                """
                Determine whether movement should pause and why.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Get Pause Reason Helper
                  Purpose: Evaluate movement pause conditions such as loot handling, death, combat, external pause flags, and casting.
                  UserDescription: Internal support routine.
                  Notes: Returns an empty string when movement should continue normally.
                """
                account_email = Player.GetAccountEmail()
                index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
                if (
                    index != -1
                    and message
                    and message.Command == SharedCommandType.PickUpLoot
                    and bool(getattr(message, "Running", False))
                ):
                    return "loot_message_active"
                if Checks.Player.IsDead():
                    return "player_dead"
                if pause_on_combat and bool(node.blackboard.get("COMBAT_ACTIVE", False)):
                    return "combat"
                if bool(node.blackboard.get(pause_flag_key, False)):
                    return "external_pause"
                if Checks.Player.IsCasting():
                    return "casting"
                return ""

            def _issue_move(target_x: float, target_y: float):
                """
                Send a move command toward the current waypoint.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Issue Move Helper
                  Purpose: Dispatch the low-level move command and apply small jitter when repeated move points are too similar.
                  UserDescription: Internal support routine.
                  Notes: Records the last issued move point so repeated nudges can avoid exact duplicates.
                """
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
                """
                Drive the main movement execution loop.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Move Executor Helper
                  Purpose: Resolve or consume path points, handle progress, pauses, retries, and completion for the movement routine.
                  UserDescription: Internal support routine.
                  Notes: Returns running while pathing continues, success on completion, and failure on unrecoverable movement errors.
                """
                from ...Pathing import AutoPathing
                from ...Py4GWcorelib import Utils

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
                    if path_points_override is not None:
                        state["path_gen"] = None
                        state["path_points"] = [
                            (float(path_x), float(path_y))
                            for path_x, path_y in path_points_override
                        ]
                        state["path_index"] = 0
                        state["move_issued"] = False
                        state["last_distance"] = None
                        state["last_progress_ms"] = now
                        state["pause_logged"] = False
                        state["last_logged_waypoint_index"] = -1
                        if _debug_enabled(node):
                            ConsoleLog(
                                "MoveDirect",
                                f"Starting direct move with {len(state['path_points'])} supplied points to ({x}, {y}).",
                                Console.MessageType.Info,
                                log=True,
                            )
                        _set_blackboard(node, "running")
                    else:
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
                    state["was_paused"] = True
                    state["current_pause_reason"] = "player_dead"
                    state["last_progress_ms"] = None
                    state["last_distance"] = None
                    state["move_issued"] = False
                    state["last_move_point"] = None
                    state["resume_recovery_active"] = False
                    state["resume_recovery_reason"] = ""
                    _set_blackboard(node, "paused", "player_dead")
                    return BehaviorTree.NodeState.RUNNING

                pause_reason = _get_pause_reason(node)
                if pause_reason:
                    if not state["pause_logged"] and log:
                            ConsoleLog("Move", f"Movement paused due to {pause_reason}.", Console.MessageType.Info, log=log)
                    state["pause_logged"] = True
                    state["was_paused"] = True
                    state["current_pause_reason"] = pause_reason
                    state["last_progress_ms"] = None
                    state["last_distance"] = None
                    state["move_issued"] = False
                    state["last_move_point"] = None
                    state["resume_recovery_active"] = False
                    state["resume_recovery_reason"] = ""
                    _set_blackboard(node, "paused", pause_reason)
                    return BehaviorTree.NodeState.RUNNING
                elif state["pause_logged"]:
                    if log:
                        ConsoleLog("Move", "Movement resumed.", Console.MessageType.Info, log=log)
                    state["pause_logged"] = False
                if state["was_paused"]:
                    state["was_paused"] = False
                    state["resume_recovery_active"] = True
                    state["resume_recovery_reason"] = state["current_pause_reason"]
                    state["resume_recovery_restart_pending"] = True
                    state["current_pause_reason"] = ""
                    state["move_issued"] = False
                    state["last_distance"] = None
                    state["last_progress_ms"] = now
                    state["last_move_point"] = None

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
                    state["resume_recovery_reason"] = ""
                    state["resume_recovery_restart_pending"] = True
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
                """
                Reset timeout watcher state for the current waypoint.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Reset Timeout Helper
                  Purpose: Clear timeout-tracking timestamps and waypoint bookkeeping for the movement timeout watcher.
                  UserDescription: Internal support routine.
                  Notes: Called when movement pauses, finishes, fails, or restarts from a new waypoint.
                """
                timeout_state["started_ms"] = None
                timeout_state["waypoint_index"] = None
                timeout_state["paused_since_ms"] = None
                timeout_state["paused_total_ms"] = 0

            def _timeout(node: BehaviorTree.Node):
                """
                Watch the active waypoint for movement timeout conditions.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Timeout Helper
                  Purpose: Fail the movement routine when waypoint progress exceeds the configured timeout budget.
                  UserDescription: Internal support routine.
                  Notes: Extends the timeout budget during resume recovery and ignores time spent while movement is paused.
                """
                from ...Py4GWcorelib import Utils

                pause_reason = _get_pause_reason(node)
                is_paused = bool(pause_reason)
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
                    _reset_timeout()
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

                if state["resume_recovery_restart_pending"]:
                    timeout_state["started_ms"] = now
                    timeout_state["waypoint_index"] = state["path_index"]
                    timeout_state["paused_since_ms"] = None
                    timeout_state["paused_total_ms"] = 0
                    state["resume_recovery_restart_pending"] = False
                    return BehaviorTree.NodeState.RUNNING

                RECOVERY_FACTOR=3
                elapsed_ms = now - timeout_state["started_ms"] - timeout_state["paused_total_ms"]
                effective_timeout_ms = timeout_ms * RECOVERY_FACTOR if state["resume_recovery_active"] else timeout_ms
                if effective_timeout_ms > 0 and elapsed_ms >= effective_timeout_ms:
                    current_pos = Player.GetXY()
                    waypoint = None
                    distance_to_waypoint = None
                    if state["path_points"] is not None and 0 <= state["path_index"] < len(state["path_points"]):
                        waypoint = state["path_points"][state["path_index"]]
                        distance_to_waypoint = Utils.Distance(current_pos, waypoint)
                    state["failure_details"] = {
                        "timeout_elapsed_ms": int(elapsed_ms),
                        "timeout_budget_ms": int(effective_timeout_ms),
                        "base_timeout_ms": int(timeout_ms),
                        "paused_total_ms": int(timeout_state["paused_total_ms"]),
                        "paused_since_ms": timeout_state["paused_since_ms"],
                        "resume_recovery_active": bool(state["resume_recovery_active"]),
                        "resume_recovery_reason": state["resume_recovery_reason"],
                        "current_pause_reason": state["current_pause_reason"],
                        "current_pos": current_pos,
                        "current_waypoint": waypoint,
                        "distance_to_waypoint": distance_to_waypoint,
                    }
                    if log:
                        ConsoleLog(
                            "Move",
                            (
                                f"Movement timed out after {elapsed_ms}ms on path_index={state['path_index']} "
                                f"(budget={effective_timeout_ms}ms, base_timeout={timeout_ms}ms, "
                                f"paused_total={timeout_state['paused_total_ms']}ms, "
                                f"resume_recovery_active={state['resume_recovery_active']}, "
                                f"resume_recovery_reason='{state['resume_recovery_reason']}', "
                                f"current_pause_reason='{state['current_pause_reason']}', "
                                f"current_pos={current_pos}, "
                                f"waypoint={waypoint}, distance_to_waypoint={distance_to_waypoint})."
                            ),
                            Console.MessageType.Warning,
                            log=log,
                        )
                    _finalize_move(node, "failed", "timeout")
                    _reset_timeout()
                    return BehaviorTree.NodeState.FAILURE

                return BehaviorTree.NodeState.RUNNING

            def _map_transition(node: BehaviorTree.Node):
                """
                Detect successful completion through map loading or map change.

                Meta:
                  Expose: false
                  Audience: advanced
                  Display: Internal Map Transition Helper
                  Purpose: Finish the movement routine when map loading begins or the map id changes after movement starts.
                  UserDescription: Internal support routine.
                  Notes: Treats temporary map invalidity as a wait condition rather than an immediate failure.
                """
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
            class _MoveParallelNode(BehaviorTree.ParallelNode):
                def reset(self) -> None:
                    super().reset()
                    _reset_runtime()
                    _reset_result()
                    _reset_timeout()

            tree = _MoveParallelNode(
                name="Move",
                children=[move_node, timeout_node, map_transition_node],
            )
            return BehaviorTree(tree)

        @staticmethod
        def MoveDirect(
            path_points: list[Vec2f],
            tolerance: float = 50.0,
            timeout_ms: int = 15000,
            stall_threshold_ms: int = 500,
            pause_on_combat: bool = True,
            pause_flag_key: str = "PAUSE_MOVEMENT",
            log: bool = False,
        ):
            """
            Build a tree that follows caller-supplied waypoints using the same movement runtime as `Move`.

            Meta:
              Expose: true
              Audience: advanced
              Display: Move Direct
              Purpose: Follow a supplied waypoint list using the same movement runtime as `Move`.
              UserDescription: Use this when you already have a path and want the BT mover to follow it directly.
              Notes: Fails immediately on an empty waypoint list and otherwise forwards to `Move` with `path_points_override`.
            """
            if not path_points:
                return BehaviorTree(
                    BehaviorTree.FailerNode(
                        name="MoveDirectEmptyPath",
                    )
                )

            final_x, final_y = path_points[-1].x, path_points[-1].y
            return BT.Player.Move(
                x=float(final_x),
                y=float(final_y),
                tolerance=tolerance,
                timeout_ms=timeout_ms,
                stall_threshold_ms=stall_threshold_ms,
                pause_on_combat=pause_on_combat,
                pause_flag_key=pause_flag_key,
                log=log,
                path_points_override=[
                    (float(path_point.x), float(path_point.y))
                    for path_point in path_points
                ],
            )
        

