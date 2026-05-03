"""
BT routines file notes
======================

This file is both:
- part of the public BT grouped routine surface
- a discovery source for higher-level tooling
"""

from __future__ import annotations

from ...GlobalCache import GLOBAL_CACHE
from ...Player import Player
from ...Py4GWcorelib import ConsoleLog, Console
from ...enums_src.Multiboxing_enums import SharedCommandType
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree


def _coerce_command_value(command: SharedCommandType | int) -> int:
    try:
        return int(command.value)  # SharedCommandType
    except Exception:
        return int(command)


class BTShared:
    """
    Public BT helper group for shared-memory command dispatch routines.

    Meta:
      Expose: true
      Audience: advanced
      Display: Shared
      Purpose: Group public BT routines related to shared multibox command send/wait flows.
      UserDescription: Built-in BT helper group for shared-command dispatch and acknowledgement checks.
      Notes: This surface is intentionally generic and reusable across bot families.
    """

    @staticmethod
    def SendCommand(
        command: SharedCommandType | int,
        params: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        extra_data: tuple[str, str, str, str] = ("", "", "", ""),
        recipients: list[str] | None = None,
        include_self: bool = False,
        refs_blackboard_key: str = "shared_refs",
        log: bool = False,
        aftercast_ms: int = 100,
    ) -> BehaviorTree:
        """
        Build an action tree that dispatches a shared command to recipients.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Send Shared Command
          Purpose: Send a shared-memory command to selected recipients and store message refs.
          UserDescription: Use this when you need to broadcast or unicast a multibox command.
          Notes: Stores `(receiver_email, message_index)` refs into the node blackboard.
        """

        command_value = _coerce_command_value(command)
        params = tuple(float(v) for v in params)
        extra_data = tuple(str(v) for v in extra_data)

        def _send(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            sender_email = str(Player.GetAccountEmail() or "")
            if not sender_email:
                node.blackboard[refs_blackboard_key] = []
                node.blackboard[f"{refs_blackboard_key}_command"] = command_value
                return BehaviorTree.NodeState.FAILURE

            if recipients is None:
                target_emails = [
                    str(getattr(account, "AccountEmail", "") or "")
                    for account in GLOBAL_CACHE.ShMem.GetAllAccountData()
                ]
            else:
                target_emails = [str(email or "").strip() for email in recipients]

            refs: list[tuple[str, int]] = []
            for receiver_email in target_emails:
                if not receiver_email:
                    continue
                if not include_self and receiver_email == sender_email:
                    continue
                message_index = int(
                    GLOBAL_CACHE.ShMem.SendMessage(
                        sender_email,
                        receiver_email,
                        command_value,
                        params,
                        extra_data,
                    )
                )
                refs.append((receiver_email, message_index))

            node.blackboard[refs_blackboard_key] = refs
            node.blackboard[f"{refs_blackboard_key}_command"] = command_value

            if log:
                ConsoleLog(
                    "BTShared.SendCommand",
                    f"Sent command={command_value} to recipients={len(refs)}.",
                    Console.MessageType.Info,
                    log=log,
                )

            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.ActionNode(
                name="SendSharedCommand",
                action_fn=_send,
                aftercast_ms=max(0, int(aftercast_ms)),
            )
        )

    @staticmethod
    def WaitCommandDispatch(
        command: SharedCommandType | int | None = None,
        refs_blackboard_key: str = "shared_refs",
        clear_refs_on_success: bool = True,
        timeout_ms: int = 5000,
        poll_interval_ms: int = 100,
        log: bool = False,
    ) -> BehaviorTree:
        """
        Build a wait tree that blocks until dispatched shared messages leave inbox.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Wait Shared Dispatch
          Purpose: Wait until previously sent shared command refs are no longer active.
          UserDescription: Use this after Send Shared Command when you need ack-style completion.
          Notes: Reads refs from blackboard key written by `SendCommand`.
        """

        timeout_ms = max(0, int(timeout_ms))
        poll_interval_ms = max(10, int(poll_interval_ms))
        explicit_command = _coerce_command_value(command) if command is not None else None

        def _all_sent(node: BehaviorTree.Node) -> bool:
            refs = node.blackboard.get(refs_blackboard_key, [])
            if not refs:
                return True

            command_value = explicit_command
            if command_value is None:
                command_value = int(node.blackboard.get(f"{refs_blackboard_key}_command", -1))

            sender_email = str(Player.GetAccountEmail() or "")
            for receiver_email, message_index in refs:
                if int(message_index) < 0:
                    continue
                message = GLOBAL_CACHE.ShMem.GetInbox(int(message_index))
                is_same_message = (
                    bool(getattr(message, "Active", False))
                    and str(getattr(message, "ReceiverEmail", "") or "") == str(receiver_email or "")
                    and str(getattr(message, "SenderEmail", "") or "") == sender_email
                    and int(getattr(message, "Command", -1)) == int(command_value)
                )
                if is_same_message:
                    return False

            if clear_refs_on_success:
                node.blackboard[refs_blackboard_key] = []
            if log:
                ConsoleLog(
                    "BTShared.WaitCommandDispatch",
                    f"Dispatch complete for refs_key={refs_blackboard_key}.",
                    Console.MessageType.Info,
                    log=log,
                )
            return True

        return BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name="WaitSharedDispatch",
                condition_fn=_all_sent,
                throttle_interval_ms=poll_interval_ms,
                timeout_ms=timeout_ms,
            )
        )

    @staticmethod
    def SendAndWait(
        command: SharedCommandType | int,
        params: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
        extra_data: tuple[str, str, str, str] = ("", "", "", ""),
        recipients: list[str] | None = None,
        include_self: bool = False,
        refs_blackboard_key: str = "shared_refs",
        timeout_ms: int = 5000,
        poll_interval_ms: int = 100,
        log: bool = False,
        aftercast_ms: int = 100,
    ) -> BehaviorTree:
        """
        Build a sequence that sends a shared command and waits for dispatch completion.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Send And Wait Shared Command
          Purpose: Dispatch shared command and wait until outbound refs are finished.
          UserDescription: Use this for one-shot command dispatch with acknowledgement wait.
          Notes: Convenience wrapper around `SendCommand` + `WaitCommandDispatch`.
        """

        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="SendAndWaitSharedCommand",
                children=[
                    BTShared.SendCommand(
                        command=command,
                        params=params,
                        extra_data=extra_data,
                        recipients=recipients,
                        include_self=include_self,
                        refs_blackboard_key=refs_blackboard_key,
                        log=log,
                        aftercast_ms=aftercast_ms,
                    ),
                    BTShared.WaitCommandDispatch(
                        command=command,
                        refs_blackboard_key=refs_blackboard_key,
                        timeout_ms=timeout_ms,
                        poll_interval_ms=poll_interval_ms,
                        log=log,
                    ),
                ],
            )
        )
