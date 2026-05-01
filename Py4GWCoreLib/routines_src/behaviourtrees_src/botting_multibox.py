"""
Reusable multibox and shared-command helpers for Botting-style runtimes.
"""
from __future__ import annotations

from typing import Callable

from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_movement import cutscene_active


LogFn = Callable[[str], None]


def _noop_log(_message: str) -> None:
    return


def other_account_emails() -> list[str]:
    from Py4GWCoreLib import GLOBAL_CACHE, Player

    sender_email = str(Player.GetAccountEmail() or "")
    emails: list[str] = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = str(getattr(account, "AccountEmail", "") or "")
        if account_email and account_email != sender_email:
            emails.append(account_email)
    return emails


def account_map_tuple(account) -> tuple[int, int, int, int]:
    map_obj = getattr(getattr(account, "AgentData", None), "Map", None)
    return (
        int(getattr(account, "MapID", 0) or getattr(map_obj, "MapID", 0) or 0),
        int(getattr(account, "MapRegion", 0) or getattr(map_obj, "Region", 0) or 0),
        int(getattr(account, "MapDistrict", 0) or getattr(map_obj, "District", 0) or 0),
        int(getattr(account, "MapLanguage", 0) or getattr(map_obj, "Language", 0) or 0),
    )


def send_shared_command(command_type, *, data=(0, 0, 0, 0), extra_data=("", "", "", "")) -> list[tuple[str, int]]:
    from Py4GWCoreLib import GLOBAL_CACHE, Player

    sender_email = str(Player.GetAccountEmail() or "")
    refs: list[tuple[str, int]] = []
    for account_email in other_account_emails():
        message_index = GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            account_email,
            command_type,
            data,
            extra_data,
        )
        refs.append((account_email, int(message_index)))
    return refs


def outbound_messages_done(refs: list[tuple[str, int]], shared_command_type: int) -> bool:
    from Py4GWCoreLib import GLOBAL_CACHE, Player

    sender_email = str(Player.GetAccountEmail() or "")
    for account_email, message_index in refs:
        if message_index < 0:
            continue
        message = GLOBAL_CACHE.ShMem.GetInbox(message_index)
        is_same_message = (
            bool(getattr(message, "Active", False))
            and str(getattr(message, "ReceiverEmail", "") or "") == account_email
            and str(getattr(message, "SenderEmail", "") or "") == sender_email
            and int(getattr(message, "Command", -1)) == int(shared_command_type)
        )
        if is_same_message:
            return False
    return True


def add_travel_gh_state(
    bot,
    *,
    multibox: bool,
    per_account_delay_ms: int = 500,
    name: str = "Travel GH",
    log: LogFn | None = None,
) -> None:
    log_fn = log or _noop_log

    def _run_travel_gh():
        from Py4GWCoreLib import GLOBAL_CACHE, Map, Player, Routines, SharedCommandType

        def _prepare_local_for_gh() -> None:
            if Routines.Checks.Map.MapValid() and Routines.Checks.Map.IsExplorable():
                log_fn("travel_gh requested while explorable; resigning to outpost first.")
                if multibox:
                    bot.Multibox.ResignParty()
                else:
                    bot.Party.Resign()
                bot.Wait.UntilOnOutpost()
                bot.Wait.ForTime(1000)

        def _send_remote_gh_messages():
            sender_email = Player.GetAccountEmail()
            refs: list[tuple[str, int]] = []
            for account_email in other_account_emails():
                message_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.TravelToGuildHall,
                    (0, 0, 0, 0),
                )
                refs.append((account_email, int(message_index)))
                if per_account_delay_ms > 0:
                    yield from bot.Wait._coro_for_time(per_account_delay_ms)
            return refs

        def _travel_local_gh():
            if not Map.IsGuildHall():
                yield from bot.Map._coro_travel_to_gh(wait_time=1000)

        _prepare_local_for_gh()
        if Map.IsGuildHall():
            log_fn("Already in Guild Hall; skipping TravelGH.")
            return
        if multibox:
            log_fn(f"travel_gh: dispatching shared GH travel command (delay={per_account_delay_ms}ms/account).")
            sent_refs = yield from _send_remote_gh_messages()
            yield from _travel_local_gh()
            yield from bot.Wait._coro_until_condition(
                lambda refs=sent_refs: outbound_messages_done(refs, SharedCommandType.TravelToGuildHall),
                duration=100,
            )
        else:
            yield from _travel_local_gh()

    bot.States.AddCustomState(_run_travel_gh, str(name))


def add_leave_party_state(bot, *, multibox: bool, name: str = "Leave Party", log: LogFn | None = None) -> None:
    log_fn = log or _noop_log

    def _run_leave_party() -> None:
        from Py4GWCoreLib import SharedCommandType

        sent_refs: list[tuple[str, int]] = []
        if multibox:
            log_fn("leave_party: dispatching shared leave command.")
            sent_refs = send_shared_command(SharedCommandType.LeaveParty)
        bot.Party.LeaveParty()
        if sent_refs:
            bot.Wait.UntilCondition(
                lambda refs=sent_refs: outbound_messages_done(refs, SharedCommandType.LeaveParty),
                duration=100,
            )

    bot.States.AddCustomState(_run_leave_party, str(name))


def add_flag_all_accounts_state(bot, *, x: float, y: float, flagger: Callable[[float, float], int], name: str, log: LogFn | None = None) -> None:
    log_fn = log or _noop_log

    def _flag_all_accounts() -> None:
        changed = int(flagger(float(x), float(y)))
        if changed:
            log_fn(f"flag_all_accounts applied to {changed} account(s).")
        else:
            log_fn("flag_all_accounts had no eligible accounts.")

    bot.States.AddCustomState(_flag_all_accounts, str(name))


def add_unflag_all_accounts_state(bot, *, unflagger: Callable[[], int], name: str, log: LogFn | None = None) -> None:
    log_fn = log or _noop_log

    def _unflag_all_accounts() -> None:
        changed = int(unflagger())
        log_fn(f"unflag_all_accounts cleared flags for {changed} account(s).")

    bot.States.AddCustomState(_unflag_all_accounts, str(name))


def add_abandon_quest_state(
    bot,
    *,
    quest_id: int,
    multibox: bool,
    skip_leader: bool = False,
    name: str = "Abandon Quest",
) -> None:
    def _abandon_quest():
        if multibox:
            yield from bot.helpers.Multibox._abandon_quest_message(int(quest_id), skip_leader=skip_leader)
            return
        bot.Quest.AbandonQuest(int(quest_id))
        yield

    bot.States.AddCustomState(_abandon_quest, str(name))


def add_broadcast_summoning_stone_state(
    bot,
    *,
    model_ids: list[int],
    effect_id: int,
    repeat: int,
    per_message_wait_ms: int,
    name: str = "Broadcast Summoning Stone",
    log: LogFn | None = None,
) -> None:
    log_fn = log or _noop_log

    def _broadcast_summoning_stone():
        from Py4GWCoreLib import GLOBAL_CACHE, Map, Player, SharedCommandType

        sender_email = str(Player.GetAccountEmail() or "")
        sender_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(sender_email)
        sender_party_id = int(getattr(getattr(sender_data, "AgentPartyData", None), "PartyID", 0) or 0)
        current_map = (
            int(Map.GetMapID() or 0),
            int(Map.GetRegion()[0] or 0),
            int(Map.GetDistrict() or 0),
            int(Map.GetLanguage()[0] or 0),
        )

        recipients: list[str] = []
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            account_email = str(getattr(account, "AccountEmail", "") or "")
            if not account_email or account_email == sender_email:
                continue
            if account_map_tuple(account) != current_map:
                continue
            account_party_id = int(getattr(getattr(account, "AgentPartyData", None), "PartyID", 0) or 0)
            if sender_party_id and account_party_id and account_party_id != sender_party_id:
                continue
            recipients.append(account_email)

        if not recipients:
            log_fn("broadcast_summoning_stone: no eligible recipients.")
            return

        for account_email in recipients:
            for model_id in model_ids:
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    account_email,
                    SharedCommandType.UseItem,
                    (int(model_id), int(repeat), int(effect_id), 0),
                    ("modular_summoning_broadcast", "", "", ""),
                )
                if per_message_wait_ms > 0:
                    yield from bot.Wait._coro_for_time(per_message_wait_ms)

        log_fn(
            f"broadcast_summoning_stone sent {len(model_ids)} model request(s) "
            f"to {len(recipients)} account(s); effect_id={effect_id}, repeat={repeat}."
        )

    bot.States.AddCustomState(_broadcast_summoning_stone, str(name))
