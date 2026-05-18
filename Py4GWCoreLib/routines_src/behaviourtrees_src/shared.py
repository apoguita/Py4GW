"""
BT routines file notes
======================

This file is both:
- part of the public BT grouped routine surface
- a discovery source for higher-level tooling
"""

from __future__ import annotations

from ...GlobalCache import GLOBAL_CACHE
from ...Map import Map
from ...Party import Party
from ...Player import Player
from ...Py4GWcorelib import ConsoleLog, Console
from ...Py4GWcorelib import Utils
from ...enums_src.Multiboxing_enums import SharedCommandType
from ...py4gwcorelib_src.BehaviorTree import BehaviorTree


def _log(source: str, message: str, *, log: bool = False, message_type=Console.MessageType.Info) -> None:
    ConsoleLog(source, message, message_type, log=log)


def _fail_log(source: str, message: str, message_type=Console.MessageType.Warning) -> None:
    ConsoleLog(source, message, message_type, log=True)


def _coerce_command_value(command: SharedCommandType | int) -> int:
    try:
        return int(command.value)  # SharedCommandType
    except Exception:
        return int(command)


def _account_map_tuple(account) -> tuple[int, int, int, int]:
    map_obj = getattr(getattr(account, "AgentData", None), "Map", None)
    return (
        int(getattr(account, "MapID", 0) or getattr(map_obj, "MapID", 0) or 0),
        int(getattr(account, "MapRegion", 0) or getattr(map_obj, "Region", 0) or 0),
        int(getattr(account, "MapDistrict", 0) or getattr(map_obj, "District", 0) or 0),
        int(getattr(account, "MapLanguage", 0) or getattr(map_obj, "Language", 0) or 0),
    )


def _message_ref_is_active(
    sender_email: str,
    receiver_email: str,
    message_index: int,
    command_value: int,
) -> bool:
    if int(message_index) < 0:
        return False
    message = GLOBAL_CACHE.ShMem.GetInbox(int(message_index))
    return bool(
        getattr(message, "Active", False)
        and str(getattr(message, "ReceiverEmail", "") or "") == str(receiver_email or "")
        and str(getattr(message, "SenderEmail", "") or "") == str(sender_email or "")
        and int(getattr(message, "Command", -1)) == int(command_value)
    )


def _party_id_from_account(account) -> int:
    return int(getattr(getattr(account, "AgentPartyData", None), "PartyID", 0) or 0)


def _account_agent_id(account) -> int:
    return int(
        getattr(account, "PlayerID", 0)
        or getattr(getattr(account, "AgentData", None), "AgentID", 0)
        or 0
    )


def _local_party_player_agent_ids() -> set[int]:
    agent_ids: set[int] = set()
    for player in Party.GetPlayers() or []:
        login_number = int(getattr(player, "login_number", 0) or 0)
        if login_number <= 0:
            continue
        agent_id = int(Party.Players.GetAgentIDByLoginNumber(login_number) or 0)
        if agent_id > 0:
            agent_ids.add(agent_id)
    return agent_ids


def _account_is_in_local_party(account) -> bool:
    agent_id = _account_agent_id(account)
    if agent_id <= 0:
        return False
    return agent_id in _local_party_player_agent_ids()


def _account_character_name(account) -> str:
    return str(
        getattr(account, "CharacterName", "")
        or getattr(getattr(account, "AgentData", None), "CharacterName", "")
        or ""
    )


def _invite_priority(account) -> tuple[int, str]:
    from ...enums_src.GameData_enums import Profession
    melee_professions = {
            Profession.Warrior.value, 
            Profession.Ranger.value, 
            Profession.Assassin.value, 
            Profession.Dervish.value
        }
    
    priority_by_profession = {
        Profession.Mesmer.value: 1,
        Profession.Paragon.value: 2,
        Profession.Elementalist.value: 2,
        Profession.Necromancer.value: 3,
        Profession.Monk.value: 4,
        Profession.Ritualist.value: 5,
    }
    profession = int(
        getattr(account, "PlayerPrimaryProfession", 0)
        or getattr(getattr(account, "AgentData", None), "Profession", [0])[0]
        or 0
    )
    if profession in melee_professions:
        return (0, str(getattr(account, "CharacterName", "") or getattr(getattr(account, "AgentData", None), "CharacterName", "") or ""))
    return (
        priority_by_profession.get(profession, 5),
        str(getattr(account, "CharacterName", "") or getattr(getattr(account, "AgentData", None), "CharacterName", "") or ""),
    )


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
        send_command = command if isinstance(command, SharedCommandType) else SharedCommandType(int(command_value))
        params = tuple(float(v) for v in params)
        extra_data = tuple(str(v) for v in extra_data)

        def _send(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            sender_email = str(Player.GetAccountEmail() or "")
            if not sender_email:
                node.blackboard[refs_blackboard_key] = []
                node.blackboard[f"{refs_blackboard_key}_command"] = command_value
                _fail_log(
                    "BTShared.SendCommand",
                    f"Failed to send shared command {command_value}: sender email is empty.",
                )
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
                        send_command,
                        params,
                        extra_data,
                    )
                )
                refs.append((receiver_email, message_index))

            node.blackboard[refs_blackboard_key] = refs
            node.blackboard[f"{refs_blackboard_key}_command"] = command_value

            _log(
                "BTShared.SendCommand",
                f"Sent command={command_value} to recipients={len(refs)}.",
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
                return BehaviorTree.NodeState.SUCCESS

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
                    return BehaviorTree.NodeState.RUNNING

            if clear_refs_on_success:
                node.blackboard[refs_blackboard_key] = []
            _log(
                "BTShared.WaitCommandDispatch",
                f"Dispatch complete for refs_key={refs_blackboard_key}.",
                log=log,
            )
            return BehaviorTree.NodeState.SUCCESS

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

    @staticmethod
    def SummonAllAccounts(
        refs_blackboard_key: str = "shared_refs",
        timeout_ms: int = 15000,
        poll_interval_ms: int = 100,
        log: bool = False,
        aftercast_ms: int = 100,
    ) -> BehaviorTree:
        """
        Build a BT summon flow for all other accounts using map travel or GH travel.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Summon All Accounts
          Purpose: Dispatch summon travel commands to all other accounts based on the current local map context.
          UserDescription: Use this to summon every other account to your current outpost or guild hall.
          Notes: Uses `TravelToGuildHall` when the sender is in GH, otherwise sends `TravelToMap`.
        """

        def _prepare_summon(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            sender_email = str(Player.GetAccountEmail() or "")
            if not sender_email:
                node.blackboard[f"{refs_blackboard_key}_recipient_emails"] = []
                _fail_log("BTShared.SummonAllAccounts", "Failed to summon accounts: sender email is empty.")
                return BehaviorTree.NodeState.FAILURE

            sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email)
            summon_to_guild_hall = bool(Map.IsGuildHall())
            if sender_data is not None:
                sender_map_tuple = _account_map_tuple(sender_data)
            else:
                sender_map_tuple = (
                    int(Map.GetMapID() or 0),
                    int(Map.GetRegion()[0] or 0),
                    int(Map.GetDistrict() or 0),
                    int(Map.GetLanguage()[0] or 0),
                )

            command = SharedCommandType.TravelToGuildHall if summon_to_guild_hall else SharedCommandType.TravelToMap
            command_value = _coerce_command_value(command)
            params = (
                (0.0, 0.0, 0.0, 0.0)
                if summon_to_guild_hall
                else (
                    float(sender_map_tuple[0]),
                    float(sender_map_tuple[1]),
                    float(sender_map_tuple[2]),
                    float(sender_map_tuple[3]),
                )
            )

            recipient_emails: list[str] = []
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                receiver_email = str(getattr(account, "AccountEmail", "") or "")
                if not receiver_email or receiver_email == sender_email:
                    continue
                if _account_map_tuple(account) == sender_map_tuple:
                    continue
                recipient_emails.append(receiver_email)

            node.blackboard[f"{refs_blackboard_key}_prepared_command"] = command
            node.blackboard[f"{refs_blackboard_key}_prepared_params"] = params
            node.blackboard[f"{refs_blackboard_key}_recipient_emails"] = recipient_emails
            node.blackboard[f"{refs_blackboard_key}_expected_map_tuple"] = sender_map_tuple
            node.blackboard[refs_blackboard_key] = []
            _log(
                "BTShared.SummonAllAccounts",
                f"Prepared summon command={command_value} for recipients={len(recipient_emails)}.",
                log=log,
            )
            return BehaviorTree.NodeState.SUCCESS

        def _all_accounts_ready(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            recipient_emails = list(node.blackboard.get(f"{refs_blackboard_key}_recipient_emails", []))
            if not recipient_emails:
                return BehaviorTree.NodeState.SUCCESS

            expected_map_tuple = tuple(node.blackboard.get(f"{refs_blackboard_key}_expected_map_tuple", (0, 0, 0, 0)))
            for receiver_email in recipient_emails:
                receiver_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(str(receiver_email or ""))
                if receiver_data is None:
                    return BehaviorTree.NodeState.RUNNING
                if _account_map_tuple(receiver_data) != expected_map_tuple:
                    return BehaviorTree.NodeState.RUNNING

            _log(
                "BTShared.SummonAllAccounts",
                f"All summoned accounts are ready on target map {expected_map_tuple}.",
                log=log,
            )
            node.blackboard[refs_blackboard_key] = []
            node.blackboard[f"{refs_blackboard_key}_recipient_emails"] = []
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="SummonAllAccounts",
                children=[
                    BehaviorTree.ActionNode(
                        name="PrepareSummonAllAccounts",
                        action_fn=_prepare_summon,
                    ),
                    BehaviorTree(
                        BehaviorTree.SubtreeNode(
                            name="DispatchSummonAllAccounts",
                            subtree_fn=lambda node: BTShared.SendAndWait(
                                command=node.blackboard.get(f"{refs_blackboard_key}_prepared_command", SharedCommandType.TravelToMap),
                                params=tuple(node.blackboard.get(f"{refs_blackboard_key}_prepared_params", (0.0, 0.0, 0.0, 0.0))),
                                recipients=list(node.blackboard.get(f"{refs_blackboard_key}_recipient_emails", [])),
                                refs_blackboard_key=refs_blackboard_key,
                                timeout_ms=timeout_ms,
                                poll_interval_ms=poll_interval_ms,
                                log=log,
                                aftercast_ms=aftercast_ms,
                            ),
                        )
                    ),
                    BehaviorTree.WaitUntilNode(
                        name="WaitSummonedAccountsReady",
                        condition_fn=_all_accounts_ready,
                        throttle_interval_ms=poll_interval_ms,
                        timeout_ms=timeout_ms,
                    ),
                ],
            )
        )

    @staticmethod
    def SummonAccountByEmail(
        account_email: str,
        refs_blackboard_key: str = "shared_refs",
        timeout_ms: int = 60000,
        poll_interval_ms: int = 100,
        log: bool = False,
        aftercast_ms: int = 100,
    ) -> BehaviorTree:
        """
        Build a BT summon flow for one account using map travel or GH travel.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Summon Account By Email
          Purpose: Dispatch a summon travel command to one target account based on the current local map context.
          UserDescription: Use this to summon a specific account to your current outpost or guild hall.
          Notes: Skips dispatch when the target is already on the same map tuple.
        """

        target_email = str(account_email or "").strip()

        def _prepare_summon(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            sender_email = str(Player.GetAccountEmail() or "")
            if not sender_email:
                node.blackboard[f"{refs_blackboard_key}_recipient_emails"] = []
                _fail_log("BTShared.SummonAccountByEmail", "Failed to summon account: sender email is empty.")
                return BehaviorTree.NodeState.FAILURE
            if not target_email:
                node.blackboard[f"{refs_blackboard_key}_recipient_emails"] = []
                _fail_log("BTShared.SummonAccountByEmail", "Failed to summon account: target email is empty.")
                return BehaviorTree.NodeState.FAILURE

            sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email)
            target_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(target_email)
            if target_data is None:
                node.blackboard[f"{refs_blackboard_key}_recipient_emails"] = []
                _fail_log("BTShared.SummonAccountByEmail", f"Failed to summon account: target '{target_email}' was not found.")
                return BehaviorTree.NodeState.FAILURE

            summon_to_guild_hall = bool(Map.IsGuildHall())
            if sender_data is not None:
                sender_map_tuple = _account_map_tuple(sender_data)
            else:
                sender_map_tuple = (
                    int(Map.GetMapID() or 0),
                    int(Map.GetRegion()[0] or 0),
                    int(Map.GetDistrict() or 0),
                    int(Map.GetLanguage()[0] or 0),
                )

            if _account_map_tuple(target_data) == sender_map_tuple:
                node.blackboard[f"{refs_blackboard_key}_recipient_emails"] = []
                _log(
                    "BTShared.SummonAccountByEmail",
                    f"Skipped summon for '{target_email}': already on the same map tuple.",
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            command = SharedCommandType.TravelToGuildHall if summon_to_guild_hall else SharedCommandType.TravelToMap
            command_value = _coerce_command_value(command)
            params = (
                (0.0, 0.0, 0.0, 0.0)
                if summon_to_guild_hall
                else (
                    float(sender_map_tuple[0]),
                    float(sender_map_tuple[1]),
                    float(sender_map_tuple[2]),
                    float(sender_map_tuple[3]),
                )
            )
            node.blackboard[f"{refs_blackboard_key}_prepared_command"] = command
            node.blackboard[f"{refs_blackboard_key}_prepared_params"] = params
            node.blackboard[f"{refs_blackboard_key}_recipient_emails"] = [target_email]
            node.blackboard[f"{refs_blackboard_key}_expected_map_tuple"] = sender_map_tuple
            node.blackboard[refs_blackboard_key] = []
            _log(
                "BTShared.SummonAccountByEmail",
                f"Prepared summon command={command_value} to '{target_email}'.",
                log=log,
            )
            return BehaviorTree.NodeState.SUCCESS

        def _account_ready(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            recipient_emails = list(node.blackboard.get(f"{refs_blackboard_key}_recipient_emails", []))
            if not recipient_emails:
                return BehaviorTree.NodeState.SUCCESS

            expected_map_tuple = tuple(node.blackboard.get(f"{refs_blackboard_key}_expected_map_tuple", (0, 0, 0, 0)))
            receiver_email = str(recipient_emails[0] or "")
            receiver_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(str(receiver_email or ""))
            if receiver_data is None:
                return BehaviorTree.NodeState.RUNNING
            if _account_map_tuple(receiver_data) != expected_map_tuple:
                return BehaviorTree.NodeState.RUNNING

            _log(
                "BTShared.SummonAccountByEmail",
                f"Summoned account '{receiver_email}' is ready on target map {expected_map_tuple}.",
                log=log,
            )
            node.blackboard[refs_blackboard_key] = []
            node.blackboard[f"{refs_blackboard_key}_recipient_emails"] = []
            return BehaviorTree.NodeState.SUCCESS

        return BehaviorTree(
            BehaviorTree.SequenceNode(
                name="SummonAccountByEmail",
                children=[
                    BehaviorTree.ActionNode(
                        name="PrepareSummonAccountByEmail",
                        action_fn=_prepare_summon,
                    ),
                    BehaviorTree(
                        BehaviorTree.SubtreeNode(
                            name="DispatchSummonAccountByEmail",
                            subtree_fn=lambda node: BTShared.SendAndWait(
                                command=node.blackboard.get(f"{refs_blackboard_key}_prepared_command", SharedCommandType.TravelToMap),
                                params=tuple(node.blackboard.get(f"{refs_blackboard_key}_prepared_params", (0.0, 0.0, 0.0, 0.0))),
                                recipients=list(node.blackboard.get(f"{refs_blackboard_key}_recipient_emails", [])),
                                refs_blackboard_key=refs_blackboard_key,
                                timeout_ms=timeout_ms,
                                poll_interval_ms=poll_interval_ms,
                                log=log,
                                aftercast_ms=aftercast_ms,
                            ),
                        )
                    ),
                    BehaviorTree.WaitUntilNode(
                        name="WaitSummonedAccountReady",
                        condition_fn=_account_ready,
                        throttle_interval_ms=poll_interval_ms,
                        timeout_ms=timeout_ms,
                    ),
                ],
            )
        )

    @staticmethod
    def InviteAllAccounts(
        refs_blackboard_key: str = "shared_refs",
        timeout_ms: int = 15000,
        poll_interval_ms: int = 100,
        log: bool = False,
        aftercast_ms: int = 250,
    ) -> BehaviorTree:
        """
        Build a BT invite flow for all eligible other accounts on the current map.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Invite All Accounts
          Purpose: Invite all eligible same-map accounts and wait until they join the local party.
          UserDescription: Use this to party up all summon-ready accounts from the current leader account.
          Notes: Invites one account at a time. Skips accounts already in the same party or not on the same map tuple.
        """
        state: dict[str, object] = {
            "initialized": False,
            "sender_email": "",
            "recipient_emails": [],
            "current_index": 0,
            "current_receiver_email": "",
            "next_dispatch_ms": 0,
        }

        def _invite_all_accounts_sequential(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            if not bool(state["initialized"]):
                sender_email = str(Player.GetAccountEmail() or "")
                if not sender_email:
                    _fail_log("BTShared.InviteAllAccounts", "Failed to invite accounts: sender email is empty.")
                    return BehaviorTree.NodeState.FAILURE

                recipients = []
                for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                    receiver_email = str(getattr(account, "AccountEmail", "") or "")
                    if not receiver_email or receiver_email == sender_email:
                        continue
                    recipients.append(account)

                recipients.sort(key=_invite_priority)
                recipient_emails = [str(getattr(account, "AccountEmail", "") or "") for account in recipients]

                state["initialized"] = True
                state["sender_email"] = sender_email
                state["recipient_emails"] = recipient_emails
                state["current_index"] = 0
                state["current_receiver_email"] = ""
                state["next_dispatch_ms"] = 0

                node.blackboard[refs_blackboard_key] = []
                node.blackboard[f"{refs_blackboard_key}_sender_email"] = sender_email

                if not recipient_emails:
                    _log("BTShared.InviteAllAccounts", "No eligible accounts to invite.", log=log)
                    return BehaviorTree.NodeState.SUCCESS

            sender_email = str(state["sender_email"] or "")
            recipient_emails = list(state["recipient_emails"])
            current_index = int(state["current_index"])
            current_receiver_email = str(state["current_receiver_email"] or "")

            if current_receiver_email:
                receiver_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(current_receiver_email)
                if receiver_data is None:
                    return BehaviorTree.NodeState.RUNNING
                if not _account_is_in_local_party(receiver_data):
                    return BehaviorTree.NodeState.RUNNING

                _log(
                    "BTShared.InviteAllAccounts",
                    f"Invited '{current_receiver_email}' into the local party.",
                    log=log,
                )
                state["current_receiver_email"] = ""
                state["current_index"] = current_index + 1
                state["next_dispatch_ms"] = int(Utils.GetBaseTimestamp()) + max(0, int(aftercast_ms))
                node.blackboard[refs_blackboard_key] = []
                return BehaviorTree.NodeState.RUNNING

            current_index = int(state["current_index"])
            if current_index >= len(recipient_emails):
                _log(
                    "BTShared.InviteAllAccounts",
                    f"All invited accounts joined sequentially: count={len(recipient_emails)}.",
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            next_dispatch_ms = int(state["next_dispatch_ms"])
            if next_dispatch_ms > 0 and int(Utils.GetBaseTimestamp()) < next_dispatch_ms:
                return BehaviorTree.NodeState.RUNNING

            receiver_email = str(recipient_emails[current_index] or "")
            receiver_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(receiver_email)
            if receiver_data is None:
                _fail_log("BTShared.InviteAllAccounts", f"Failed to invite account: target '{receiver_email}' was not found.")
                return BehaviorTree.NodeState.FAILURE
            if _account_is_in_local_party(receiver_data):
                state["current_index"] = current_index + 1
                return BehaviorTree.NodeState.RUNNING

            character_name = str(
                getattr(receiver_data, "CharacterName", "")
                or getattr(getattr(receiver_data, "AgentData", None), "CharacterName", "")
                or ""
            )
            if not character_name:
                _fail_log("BTShared.InviteAllAccounts", f"Failed to invite account: target '{receiver_email}' has no character name.")
                return BehaviorTree.NodeState.FAILURE

            GLOBAL_CACHE.Party.Players.InvitePlayer(character_name)
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                receiver_email,
                SharedCommandType.InviteToParty,
                (0.0, 0.0, 0.0, 0.0),
            )

            state["current_receiver_email"] = receiver_email
            node.blackboard[refs_blackboard_key] = [(receiver_email, -1)]
            _log(
                "BTShared.InviteAllAccounts",
                f"Sent invite command to '{receiver_email}'.",
                log=log,
            )
            return BehaviorTree.NodeState.RUNNING

        invite_tree = BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name="InviteAllAccountsSequential",
                condition_fn=_invite_all_accounts_sequential,
                throttle_interval_ms=poll_interval_ms,
                timeout_ms=timeout_ms,
            )
        )

        original_reset = invite_tree.root.reset

        def _reset_with_state() -> None:
            state["initialized"] = False
            state["sender_email"] = ""
            state["recipient_emails"] = []
            state["current_index"] = 0
            state["current_receiver_email"] = ""
            state["next_dispatch_ms"] = 0
            original_reset()

        invite_tree.root.reset = _reset_with_state
        return invite_tree

    @staticmethod
    def KickAllAccounts(
        timeout_ms: int = 15000,
        poll_interval_ms: int = 100,
        log: bool = False,
        aftercast_ms: int = 250,
    ) -> BehaviorTree:
        """
        Build a BT kick flow for all other local-party accounts, one at a time.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Kick All Accounts
          Purpose: Kick all other multibox accounts from the current local party before leaving it.
          UserDescription: Use this when the local leader should remove all follower accounts from party sequentially.
          Notes: Uses local party membership as the only completion check and skips work when the local player is not party leader.
        """
        state: dict[str, object] = {
            "initialized": False,
            "recipient_emails": [],
            "current_index": 0,
            "current_receiver_email": "",
            "next_dispatch_ms": 0,
        }

        def _kick_all_accounts_sequential(_node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            if not Party.IsPartyLeader():
                return BehaviorTree.NodeState.SUCCESS

            if not bool(state["initialized"]):
                sender_email = str(Player.GetAccountEmail() or "")
                recipients = []
                for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                    receiver_email = str(getattr(account, "AccountEmail", "") or "")
                    if not receiver_email or receiver_email == sender_email:
                        continue
                    recipients.append(account)

                recipients.sort(key=_invite_priority)
                state["initialized"] = True
                state["recipient_emails"] = [str(getattr(account, "AccountEmail", "") or "") for account in recipients]
                state["current_index"] = 0
                state["current_receiver_email"] = ""
                state["next_dispatch_ms"] = 0

                if not state["recipient_emails"]:
                    return BehaviorTree.NodeState.SUCCESS

            recipient_emails = list(state["recipient_emails"])
            current_index = int(state["current_index"])
            current_receiver_email = str(state["current_receiver_email"] or "")

            if current_receiver_email:
                receiver_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(current_receiver_email)
                if receiver_data is not None and _account_is_in_local_party(receiver_data):
                    return BehaviorTree.NodeState.RUNNING

                _log(
                    "BTShared.KickAllAccounts",
                    f"Kicked '{current_receiver_email}' from the local party.",
                    log=log,
                )
                state["current_receiver_email"] = ""
                state["current_index"] = current_index + 1
                state["next_dispatch_ms"] = int(Utils.GetBaseTimestamp()) + max(0, int(aftercast_ms))
                return BehaviorTree.NodeState.RUNNING

            if current_index >= len(recipient_emails):
                _log(
                    "BTShared.KickAllAccounts",
                    f"All follower accounts were kicked sequentially: count={len(recipient_emails)}.",
                    log=log,
                )
                return BehaviorTree.NodeState.SUCCESS

            next_dispatch_ms = int(state["next_dispatch_ms"])
            if next_dispatch_ms > 0 and int(Utils.GetBaseTimestamp()) < next_dispatch_ms:
                return BehaviorTree.NodeState.RUNNING

            receiver_email = str(recipient_emails[current_index] or "")
            receiver_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(receiver_email)
            if receiver_data is None:
                state["current_index"] = current_index + 1
                return BehaviorTree.NodeState.RUNNING
            if not _account_is_in_local_party(receiver_data):
                state["current_index"] = current_index + 1
                return BehaviorTree.NodeState.RUNNING

            character_name = _account_character_name(receiver_data)
            if not character_name:
                _fail_log("BTShared.KickAllAccounts", f"Failed to kick account: target '{receiver_email}' has no character name.")
                return BehaviorTree.NodeState.FAILURE

            GLOBAL_CACHE.Party.Players.KickPlayer(character_name)
            state["current_receiver_email"] = receiver_email
            _log(
                "BTShared.KickAllAccounts",
                f"Sent kick command to '{receiver_email}'.",
                log=log,
            )
            return BehaviorTree.NodeState.RUNNING

        kick_tree = BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name="KickAllAccountsSequential",
                condition_fn=_kick_all_accounts_sequential,
                throttle_interval_ms=poll_interval_ms,
                timeout_ms=timeout_ms,
            )
        )

        original_reset = kick_tree.root.reset

        def _reset_kick_state() -> None:
            state["initialized"] = False
            state["recipient_emails"] = []
            state["current_index"] = 0
            state["current_receiver_email"] = ""
            state["next_dispatch_ms"] = 0
            original_reset()

        kick_tree.root.reset = _reset_kick_state
        return kick_tree

    @staticmethod
    def InviteAccountByEmail(
        account_email: str,
        refs_blackboard_key: str = "shared_refs",
        timeout_ms: int = 60000,
        poll_interval_ms: int = 100,
        log: bool = False,
        aftercast_ms: int = 100,
    ) -> BehaviorTree:
        """
        Build a BT invite flow for one eligible account on the current map.

        Meta:
          Expose: true
          Audience: intermediate
          Display: Invite Account By Email
          Purpose: Invite one same-map account and wait until it joins the local party.
          UserDescription: Use this to party up a specific account from the current leader account.
          Notes: Skips invite when the target is already in the same party.
        """

        target_email = str(account_email or "").strip()
        state: dict[str, object] = {
            "sender_email": "",
            "target_email": target_email,
            "sent": False,
            "next_finish_ms": 0,
        }

        def _invite_account(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
            sender_email = str(Player.GetAccountEmail() or "")
            if not sender_email:
                _fail_log("BTShared.InviteAccountByEmail", "Failed to invite account: sender email is empty.")
                return BehaviorTree.NodeState.FAILURE
            if not target_email:
                _fail_log("BTShared.InviteAccountByEmail", "Failed to invite account: target email is empty.")
                return BehaviorTree.NodeState.FAILURE

            state["sender_email"] = sender_email
            target_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(target_email)
            if target_data is None:
                return BehaviorTree.NodeState.RUNNING

            if not bool(state["sent"]):
                if _account_is_in_local_party(target_data):
                    return BehaviorTree.NodeState.SUCCESS
                character_name = str(
                    getattr(target_data, "CharacterName", "")
                    or getattr(getattr(target_data, "AgentData", None), "CharacterName", "")
                    or ""
                )
                if not character_name:
                    _fail_log("BTShared.InviteAccountByEmail", f"Failed to invite account: target '{target_email}' has no character name.")
                    return BehaviorTree.NodeState.FAILURE
                GLOBAL_CACHE.Party.Players.InvitePlayer(character_name)
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    target_email,
                    SharedCommandType.InviteToParty,
                    (0.0, 0.0, 0.0, 0.0),
                )
                state["sent"] = True
                node.blackboard[refs_blackboard_key] = [(target_email, -1)]
                _log(
                    "BTShared.InviteAccountByEmail",
                    f"Sent invite command to '{target_email}'.",
                    log=log,
                )
                return BehaviorTree.NodeState.RUNNING

            if not _account_is_in_local_party(target_data):
                return BehaviorTree.NodeState.RUNNING

            finish_at = int(state["next_finish_ms"] or 0)
            now = int(Utils.GetBaseTimestamp())
            if finish_at <= 0:
                state["next_finish_ms"] = now + max(0, int(aftercast_ms))
                return BehaviorTree.NodeState.RUNNING
            if now < finish_at:
                return BehaviorTree.NodeState.RUNNING

            node.blackboard[refs_blackboard_key] = []
            return BehaviorTree.NodeState.SUCCESS

        invite_tree = BehaviorTree(
            BehaviorTree.WaitUntilNode(
                name="InviteAccountByEmail",
                condition_fn=_invite_account,
                throttle_interval_ms=poll_interval_ms,
                timeout_ms=timeout_ms,
            )
        )

        original_reset = invite_tree.root.reset

        def _reset_single_state() -> None:
            state["sender_email"] = ""
            state["sent"] = False
            state["next_finish_ms"] = 0
            original_reset()

        invite_tree.root.reset = _reset_single_state
        return invite_tree
