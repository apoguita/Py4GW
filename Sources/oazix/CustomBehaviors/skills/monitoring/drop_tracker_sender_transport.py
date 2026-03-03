import json
import os
import time

from Py4GWCoreLib import GLOBAL_CACHE, Item, Party, Player, Py4GW
from Py4GWCoreLib.enums import SharedCommandType

from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers_party import CustomBehaviorHelperParty
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import (
    build_drop_meta,
    build_name_chunks,
    encode_name_chunk_meta,
    make_event_id,
    make_name_signature,
)


EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def resolve_party_leader_email(sender) -> str | None:
    try:
        helper_leader_email = CustomBehaviorHelperParty._get_party_leader_email()
        if helper_leader_email:
            return helper_leader_email

        leader_id = Party.GetPartyLeaderID()
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if int(account.AgentData.AgentID) == leader_id:
                return account.AccountEmail

        my_party_id = GLOBAL_CACHE.Party.GetPartyID()
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if not account.IsAccount:
                continue
            if int(account.AgentPartyData.PartyID) != int(my_party_id):
                continue
            if int(account.AgentPartyData.PartyPosition) == 0:
                return account.AccountEmail
    except EXPECTED_RUNTIME_ERRORS:
        return None
    return None


def is_party_leader_client(sender) -> bool:
    try:
        is_leader = int(Player.GetAgentID()) == int(Party.GetPartyLeaderID())
        sender.last_known_is_leader = bool(is_leader)
        return bool(is_leader)
    except EXPECTED_RUNTIME_ERRORS:
        return bool(getattr(sender, "last_known_is_leader", False))


def next_event_id(sender) -> str:
    sender.event_sequence = (int(sender.event_sequence) + 1) & 0xFFFF
    return make_event_id(sender.event_sequence)


def load_runtime_config(sender):
    try:
        if not os.path.exists(sender.runtime_config_path):
            return
        with open(sender.runtime_config_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return
        sender.debug_pipeline_logs = bool(data.get("debug_pipeline_logs", sender.debug_pipeline_logs))
        sender.enable_perf_logs = bool(data.get("enable_perf_logs", sender.enable_perf_logs))
        sender.enable_delivery_ack = bool(data.get("enable_delivery_ack", sender.enable_delivery_ack))
        sender.max_send_per_tick = max(1, int(data.get("max_send_per_tick", sender.max_send_per_tick)))
        sender.max_outbox_size = max(20, int(data.get("max_outbox_size", sender.max_outbox_size)))
        sender.max_snapshot_size_jump = max(
            6,
            int(data.get("max_snapshot_size_jump", sender.max_snapshot_size_jump)),
        )
        sender.retry_interval_seconds = max(0.2, float(data.get("retry_interval_seconds", sender.retry_interval_seconds)))
        sender.max_retry_attempts = max(1, int(data.get("max_retry_attempts", sender.max_retry_attempts)))
        sender.max_stats_builds_per_tick = max(
            0, int(data.get("max_stats_builds_per_tick", sender.max_stats_builds_per_tick))
        )
    except EXPECTED_RUNTIME_ERRORS:
        return


def send_name_chunks(sender, receiver_email: str, my_email: str, name_signature: str, full_name: str) -> bool:
    try:
        if not name_signature:
            return True
        chunks = build_name_chunks(full_name or "")
        for idx, total, chunk in chunks:
            sent_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email=my_email,
                receiver_email=receiver_email,
                command=SharedCommandType.CustomBehaviors,
                params=(0.0, 0.0, 0.0, 0.0),
                ExtraData=(
                    "TrackerNameV2",
                    (name_signature or "")[:31],
                    (chunk or "")[:31],
                    encode_name_chunk_meta(idx, total)[:31],
                ),
            )
            if sent_index == -1:
                return False
        return True
    except EXPECTED_RUNTIME_ERRORS:
        return False


def log_name_trace(sender, message: str) -> None:
    if not bool(getattr(sender, "debug_pipeline_logs", False)):
        return
    Py4GW.Console.Log(
        "DropTrackerSenderNameTrace",
        str(message or ""),
        Py4GW.Console.MessageType.Info,
    )


def schedule_name_refresh_for_entry(sender, entry: dict, receiver_email: str = "") -> None:
    if not isinstance(entry, dict):
        return
    event_key = str(entry.get("event_id", "") or "").strip()
    if not event_key:
        return
    item_id = int(entry.get("item_id", 0) or 0)
    if item_id <= 0:
        return
    short_name = str(entry.get("item_name", "") or "").strip()
    full_name = str(entry.get("full_name", "") or "").strip()
    if full_name and full_name != short_name:
        return
    rarity = str(entry.get("rarity", "") or "").strip()
    now_ts = time.time()
    pending = getattr(sender, "pending_name_refresh_by_event", None)
    if not isinstance(pending, dict):
        sender.pending_name_refresh_by_event = {}
        pending = sender.pending_name_refresh_by_event
    existing_refresh = pending.get(event_key)
    if not isinstance(existing_refresh, dict):
        existing_refresh = {}
    resolved_receiver_email = str(
        receiver_email
        or entry.get("last_receiver_email", "")
        or existing_refresh.get("receiver_email", "")
        or ""
    ).strip().lower()
    pending[event_key] = {
        "event_id": event_key,
        "item_id": int(item_id or existing_refresh.get("item_id", 0) or 0),
        "model_id": int(entry.get("model_id", 0) or existing_refresh.get("model_id", 0) or 0),
        "item_name": short_name or str(existing_refresh.get("item_name", "") or "").strip(),
        "rarity": rarity or str(existing_refresh.get("rarity", "") or "").strip(),
        "name_signature": str(
            entry.get("name_signature", "")
            or existing_refresh.get("name_signature", "")
            or ""
        ).strip().lower(),
        "created_at": float(now_ts),
        "next_poll_at": float(now_ts + max(0.05, float(getattr(sender, "name_refresh_poll_interval_seconds", 0.25)))),
        "is_leader_sender": bool(entry.get("is_leader_sender", existing_refresh.get("is_leader_sender", False))),
        "receiver_email": resolved_receiver_email,
    }
    sender._log_name_trace(
        (
            f"NAME TRACE refresh_schedule ev={event_key} item='{short_name or '-'}' "
            f"sig={str(entry.get('name_signature', '') or '').strip().lower() or '-'} "
            f"receiver={resolved_receiver_email or '-'}"
        )
    )


def process_pending_name_refreshes(sender) -> int:
    pending = getattr(sender, "pending_name_refresh_by_event", None)
    if not isinstance(pending, dict) or not pending:
        return 0
    now_ts = time.time()
    ttl_s = max(0.5, float(getattr(sender, "name_refresh_ttl_seconds", 4.0)))
    poll_s = max(0.05, float(getattr(sender, "name_refresh_poll_interval_seconds", 0.25)))
    max_scan = max(1, int(getattr(sender, "max_name_refresh_per_tick", 4)))
    completed = 0

    for event_key in list(pending.keys()):
        refresh = pending.get(event_key)
        if not isinstance(refresh, dict):
            pending.pop(event_key, None)
            continue
        if (now_ts - float(refresh.get("created_at", now_ts))) > ttl_s:
            sender._log_name_trace(f"NAME TRACE refresh_expire ev={event_key}")
            pending.pop(event_key, None)
            continue
        if completed >= max_scan:
            break
        if now_ts < float(refresh.get("next_poll_at", 0.0) or 0.0):
            continue

        completed += 1
        item_id = int(refresh.get("item_id", 0) or 0)
        model_id = int(refresh.get("model_id", 0) or 0)
        original_name = str(refresh.get("item_name", "") or "").strip()
        original_signature = str(refresh.get("name_signature", "") or "").strip().lower()
        if item_id <= 0 or not original_signature:
            pending.pop(event_key, None)
            continue

        try:
            live_model_id = int(Item.GetModelID(item_id))
        except EXPECTED_RUNTIME_ERRORS:
            live_model_id = 0
        if model_id > 0 and live_model_id > 0 and live_model_id != model_id:
            sender._log_name_trace(
                f"NAME TRACE refresh_abort ev={event_key} reason=model_mismatch live={live_model_id} expected={model_id}"
            )
            pending.pop(event_key, None)
            continue

        clean_name = sender._resolve_best_live_item_name(item_id, original_name)
        if not clean_name or clean_name.startswith("Model#") or clean_name == original_name:
            refresh["next_poll_at"] = now_ts + poll_s
            continue

        receiver_email = str(refresh.get("receiver_email", "") or "").strip().lower()
        if not receiver_email:
            if bool(refresh.get("is_leader_sender", False)):
                try:
                    receiver_email = str(Player.GetAccountEmail() or "").strip().lower()
                except EXPECTED_RUNTIME_ERRORS:
                    receiver_email = ""
            else:
                receiver_email = str(sender._resolve_party_leader_email() or "").strip().lower()
        if not receiver_email:
            refresh["next_poll_at"] = now_ts + poll_s
            continue

        try:
            my_email = str(Player.GetAccountEmail() or "").strip()
        except EXPECTED_RUNTIME_ERRORS:
            my_email = ""
        if not my_email:
            refresh["next_poll_at"] = now_ts + poll_s
            continue

        sender._log_name_trace(
            (
                f"NAME TRACE refresh_send ev={event_key} old='{original_name or '-'}' new='{clean_name or '-'}' "
                f"sig={original_signature or '-'} receiver={receiver_email or '-'}"
            )
        )
        if sender._send_name_chunks(receiver_email, my_email, original_signature, clean_name):
            sender._remember_event_identity(
                event_id=event_key,
                item_id=item_id,
                model_id=model_id,
                item_name=clean_name,
                name_signature=original_signature,
                rarity=str(refresh.get("rarity", "") or "").strip(),
            )
            pending.pop(event_key, None)
            continue
        refresh["next_poll_at"] = now_ts + poll_s

    return completed


def schedule_name_refresh_for_item(sender, item_id: int = 0, model_id: int = 0) -> int:
    wanted_item_id = int(item_id or 0)
    wanted_model_id = int(model_id or 0)
    if wanted_item_id <= 0 and wanted_model_id <= 0:
        return 0
    cache = getattr(sender, "sent_event_stats_cache", {})
    if not isinstance(cache, dict) or not cache:
        return 0
    scheduled = 0
    for event_key, entry in list(cache.items()):
        if not isinstance(entry, dict):
            continue
        cached_item_id = int(entry.get("item_id", 0) or 0)
        cached_model_id = int(entry.get("model_id", 0) or 0)
        if wanted_item_id > 0 and cached_item_id > 0 and cached_item_id != wanted_item_id:
            if not (wanted_model_id > 0 and cached_model_id == wanted_model_id):
                continue
        elif wanted_item_id <= 0 and wanted_model_id > 0 and cached_model_id != wanted_model_id:
            continue
        refresh_entry = {
            "event_id": str(event_key or "").strip(),
            "item_id": cached_item_id if cached_item_id > 0 else wanted_item_id,
            "model_id": cached_model_id if cached_model_id > 0 else wanted_model_id,
            "item_name": str(entry.get("item_name", "") or "").strip(),
            "rarity": str(entry.get("rarity", "") or "").strip(),
            "name_signature": str(entry.get("name_signature", "") or "").strip().lower(),
            "is_leader_sender": bool(sender._is_party_leader_client()),
            "last_receiver_email": str(entry.get("last_receiver_email", "") or "").strip().lower(),
            "receiver_email": str(entry.get("last_receiver_email", "") or "").strip().lower(),
        }
        sender._schedule_name_refresh_for_entry(refresh_entry)
        scheduled += 1
    if scheduled > 0:
        sender._log_name_trace(
            f"NAME TRACE identify_refresh_rearm item_id={wanted_item_id} model_id={wanted_model_id} scheduled={scheduled}"
        )
    return scheduled


def send_stats_chunks(sender, receiver_email: str, my_email: str, event_id: str, stats_text: str) -> bool:
    try:
        if not event_id:
            return True
        if not stats_text:
            return True
        chunks = build_name_chunks(stats_text or "", 31)
        for idx, total, chunk in chunks:
            sent_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email=my_email,
                receiver_email=receiver_email,
                command=SharedCommandType.CustomBehaviors,
                params=(0.0, 0.0, 0.0, 0.0),
                ExtraData=(
                    "TrackerStatsV1",
                    (event_id or "")[:31],
                    (chunk or "")[:31],
                    encode_name_chunk_meta(idx, total)[:31],
                ),
            )
            if sent_index == -1:
                return False
        return True
    except EXPECTED_RUNTIME_ERRORS:
        return False


def send_drop(
    sender,
    item_name: str,
    quantity: int,
    rarity: str,
    display_time: str = "",
    item_id: int = 0,
    model_id: int = 0,
    slot_bag: int = 0,
    slot_index: int = 0,
    is_leader_sender: bool = False,
    event_id: str = "",
    name_signature: str = "",
    sender_session_id: int = 0,
) -> bool:
    try:
        my_email = Player.GetAccountEmail()
        if not my_email:
            return False
        if is_leader_sender:
            receiver_email = my_email
        else:
            receiver_email = sender._resolve_party_leader_email()
            if not receiver_email or receiver_email == my_email:
                return False
        meta = build_drop_meta(
            event_id,
            name_signature,
            display_time,
            sender_session_id=int(sender_session_id or 0),
        )
        sent_index = GLOBAL_CACHE.ShMem.SendMessage(
            sender_email=my_email,
            receiver_email=receiver_email,
            command=SharedCommandType.CustomBehaviors,
            params=(
                float(max(1, quantity)),
                float(max(0, int(item_id))),
                float(max(0, int(model_id))),
                float((int(slot_bag) << 16) | int(slot_index)),
            ),
            ExtraData=(
                "TrackerDrop",
                (item_name or "Unknown Item")[:31],
                (rarity or "Unknown")[:31],
                (meta or "")[:31],
            ),
        )
        if sent_index == -1 and sender.warn_timer.IsExpired():
            sender.warn_timer.Reset()
            Py4GW.Console.Log(
                "DropTrackerSender",
                f"SendMessage failed (inbox full?): sender={my_email}, receiver={receiver_email}, item={item_name}",
                Py4GW.Console.MessageType.Warning,
            )
        if hasattr(sender, "_append_live_debug_log"):
            sender._append_live_debug_log(
                "tracker_drop_sent" if sent_index != -1 else "tracker_drop_send_failed",
                f"item={str(item_name or '').strip() or 'Unknown Item'}",
                success=bool(sent_index != -1),
                receiver_email=str(receiver_email or "").strip().lower(),
                sender_email=str(my_email or "").strip().lower(),
                item_name=str(item_name or "").strip() or "Unknown Item",
                quantity=max(1, int(quantity)),
                rarity=str(rarity or "Unknown"),
                item_id=int(item_id),
                model_id=int(model_id),
                slot_bag=int(slot_bag),
                slot_index=int(slot_index),
                event_id=str(event_id or "").strip(),
                sender_session_id=int(sender_session_id or 0),
                sent_index=int(sent_index),
                role="leader" if is_leader_sender else "follower",
            )
        if sent_index != -1 and sender.debug_pipeline_logs:
            Py4GW.Console.Log(
                "DropTrackerSender",
                (
                    f"SENT idx={sent_index} role={'leader' if is_leader_sender else 'follower'} "
                    f"item='{item_name}' qty={max(1, int(quantity))} rarity={rarity} "
                    f"item_id={int(item_id)} model_id={int(model_id)} slot={int(slot_bag)}:{int(slot_index)} "
                    f"event_id={event_id} sender_session={int(sender_session_id or 0)}"
                ),
                Py4GW.Console.MessageType.Info,
            )
        return sent_index != -1
    except EXPECTED_RUNTIME_ERRORS:
        return False


def queue_drop(
    sender,
    item_name: str,
    quantity: int,
    rarity: str,
    display_time: str,
    item_id: int = 0,
    model_id: int = 0,
    slot_key: tuple[int, int] | None = None,
    reason: str = "delta",
    is_leader_sender: bool = False,
):
    bag_id = int(slot_key[0]) if slot_key else 0
    slot_id = int(slot_key[1]) if slot_key else 0
    entry = {
        "item_name": item_name or "Unknown Item",
        "full_name": item_name or "Unknown Item",
        "quantity": max(1, int(quantity)),
        "rarity": rarity or "Unknown",
        "display_time": display_time or "",
        "item_id": int(item_id),
        "model_id": int(model_id),
        "bag_id": bag_id,
        "slot_id": slot_id,
        "reason": reason or "delta",
        "is_leader_sender": bool(is_leader_sender),
        "event_id": sender._next_event_id(),
        "sender_session_id": int(getattr(sender, "sender_session_id", 1) or 1),
        "name_signature": make_name_signature(item_name or "Unknown Item"),
        "name_chunks_sent": False,
        "stats_chunks_sent": False,
        "stats_text": "",
        "attempts": 0,
        "next_retry_at": 0.0,
        "acked": False,
        "last_receiver_email": "",
        "name_refresh_scheduled": False,
    }
    sender._remember_event_identity(
        event_id=str(entry.get("event_id", "")),
        item_id=int(entry.get("item_id", 0)),
        model_id=int(entry.get("model_id", 0)),
        item_name=str(entry.get("item_name", "") or ""),
        name_signature=str(entry.get("name_signature", "") or ""),
        rarity=str(entry.get("rarity", "") or ""),
        last_receiver_email=str(entry.get("last_receiver_email", "") or ""),
    )
    sender._log_name_trace(
        (
            f"NAME TRACE enqueue ev={entry.get('event_id', '') or '-'} "
            f"item='{str(entry.get('item_name', '') or '').strip() or '-'}' "
            f"full='{str(entry.get('full_name', '') or '').strip() or '-'}' "
            f"sig={str(entry.get('name_signature', '') or '').strip().lower() or '-'} "
            f"model_id={int(entry.get('model_id', 0))} item_id={int(entry.get('item_id', 0))}"
        )
    )
    if len(sender.outbox_queue) >= int(sender.max_outbox_size):
        sender.outbox_queue.pop(0)
        if sender.warn_timer.IsExpired():
            sender.warn_timer.Reset()
            Py4GW.Console.Log(
                "DropTrackerSender",
                f"Outbox full, dropped oldest entry (limit={sender.max_outbox_size}).",
                Py4GW.Console.MessageType.Warning,
            )
    sender.outbox_queue.append(entry)
    if hasattr(sender, "_append_live_debug_log"):
        sender._append_live_debug_log(
            "tracker_drop_enqueued",
            f"event_id={str(entry['event_id'])}",
            entry=entry,
            queue_size=len(sender.outbox_queue),
        )
    if sender.debug_pipeline_logs:
        Py4GW.Console.Log(
            "DropTrackerSender",
            (
                f"ENQUEUE reason={entry['reason']} role={'leader' if entry['is_leader_sender'] else 'follower'} "
                f"item='{entry['item_name']}' qty={entry['quantity']} rarity={entry['rarity']} "
                f"item_id={entry['item_id']} model_id={entry['model_id']} "
                f"slot={entry['bag_id']}:{entry['slot_id']} queue={len(sender.outbox_queue)} "
                f"event_id={entry['event_id']} sender_session={int(entry['sender_session_id'])}"
            ),
            Py4GW.Console.MessageType.Info,
        )


def poll_ack_messages(sender) -> int:
    if not sender.enable_delivery_ack:
        return 0
    try:
        my_email = Player.GetAccountEmail()
        if not my_email:
            return 0
        shmem = getattr(GLOBAL_CACHE, "ShMem", None)
        if shmem is None:
            return 0
        acked_count = 0
        for msg_idx, shared_msg in shmem.GetAllMessages():
            receiver_email = str(getattr(shared_msg, "ReceiverEmail", "") or "").strip()
            if receiver_email != my_email:
                continue
            command_value = int(getattr(shared_msg, "Command", 0))
            expected_custom_behavior_command = 997
            try:
                expected_custom_behavior_command = int(SharedCommandType.CustomBehaviors.value)
            except EXPECTED_RUNTIME_ERRORS:
                pass
            if command_value != expected_custom_behavior_command and command_value != 997:
                continue
            extra_data_list = getattr(shared_msg, "ExtraData", None)
            if not extra_data_list or len(extra_data_list) == 0:
                continue
            extra_0 = "".join(ch for ch in extra_data_list[0] if ch != "\0").rstrip()
            if extra_0 != "TrackerAckV2":
                continue
            event_id = "".join(ch for ch in extra_data_list[1] if ch != "\0").rstrip() if len(extra_data_list) > 1 else ""
            ack_sender_email = str(getattr(shared_msg, "SenderEmail", "") or "").strip().lower()
            for entry in sender.outbox_queue:
                if str(entry.get("event_id", "")) == str(event_id):
                    if int(entry.get("attempts", 0)) <= 0:
                        continue
                    expected_sender = str(entry.get("last_receiver_email", "") or "").strip().lower()
                    if expected_sender and ack_sender_email and ack_sender_email != expected_sender:
                        continue
                    if not entry.get("acked", False):
                        entry["acked"] = True
                        acked_count += 1
                        if hasattr(sender, "_append_live_debug_log"):
                            sender._append_live_debug_log(
                                "tracker_drop_acked",
                                f"event_id={str(event_id or '').strip()}",
                                event_id=str(event_id or "").strip(),
                                ack_sender_email=ack_sender_email,
                                expected_sender=expected_sender,
                            )
            shmem.MarkMessageAsFinished(my_email, msg_idx)
        sender.last_ack_count = acked_count
        return acked_count
    except EXPECTED_RUNTIME_ERRORS:
        return 0


def flush_outbox(sender) -> int:
    if sender.enable_delivery_ack and sender.ack_poll_timer.IsExpired():
        sender.ack_poll_timer.Reset()
        sender._poll_ack_messages()

    now_ts = time.time()
    stats_build_budget = max(0, int(getattr(sender, "max_stats_builds_per_tick", 2)))
    kept_entries = []
    for entry in sender.outbox_queue:
        if entry.get("acked", False):
            continue
        attempts = int(entry.get("attempts", 0))
        if attempts >= int(sender.max_retry_attempts):
            if sender.warn_timer.IsExpired():
                sender.warn_timer.Reset()
                Py4GW.Console.Log(
                    "DropTrackerSender",
                    f"Dropping unacked event after retries: {entry.get('event_id', '')}",
                    Py4GW.Console.MessageType.Warning,
                )
            continue
        kept_entries.append(entry)
    sender.outbox_queue = kept_entries

    sent = 0
    attempted = 0
    retry_delay_s = max(0.2, float(sender.retry_interval_seconds))
    for entry in sender.outbox_queue:
        if attempted >= int(sender.max_send_per_tick):
            break
        if float(entry.get("next_retry_at", 0.0)) > now_ts:
            continue

        my_email = Player.GetAccountEmail()
        if not my_email:
            break
        is_leader_sender = bool(entry.get("is_leader_sender", False))
        receiver_email = my_email if is_leader_sender else sender._resolve_party_leader_email()
        if not receiver_email:
            continue
        if not is_leader_sender and receiver_email == my_email:
            continue

        attempted += 1
        entry["last_receiver_email"] = str(receiver_email or "").strip().lower()
        send_failed = False

        if not entry.get("name_chunks_sent", False):
            full_name = str(entry.get("full_name", "") or "")
            short_name = str(entry.get("item_name", "") or "")
            if (len(full_name) > 31 or full_name != short_name) and sender._should_track_name_refresh(
                short_name,
                str(entry.get("rarity", "") or ""),
            ):
                sender._log_name_trace(
                    (
                        f"NAME TRACE name_chunks_send ev={str(entry.get('event_id', '') or '').strip() or '-'} "
                        f"short='{short_name or '-'}' full='{full_name or '-'}' "
                        f"sig={str(entry.get('name_signature', '') or '').strip().lower() or '-'} "
                        f"receiver={str(receiver_email or '').strip().lower() or '-'}"
                    )
                )
                ok_chunks = sender._send_name_chunks(
                    receiver_email=receiver_email,
                    my_email=my_email,
                    name_signature=str(entry.get("name_signature", "")),
                    full_name=full_name,
                )
                if not ok_chunks:
                    sender._log_name_trace(
                        (
                            f"NAME TRACE name_chunks_failed ev={str(entry.get('event_id', '') or '').strip() or '-'} "
                            f"short='{short_name or '-'}' full='{full_name or '-'}'"
                        )
                    )
                    send_failed = True
            else:
                reason = "same_or_short"
                if len(full_name) > 31 or full_name != short_name:
                    reason = "ineligible"
                sender._log_name_trace(
                    (
                        f"NAME TRACE name_chunks_skip ev={str(entry.get('event_id', '') or '').strip() or '-'} "
                        f"short='{short_name or '-'}' full='{full_name or '-'}' reason={reason}"
                    )
                )
            entry["name_chunks_sent"] = True

        if (not send_failed) and (not entry.get("stats_chunks_sent", False)):
            stats_text = str(entry.get("stats_text", "") or "")
            if not stats_text and stats_build_budget > 0:
                stats_item_id = sender._resolve_event_item_id_for_stats(entry)
                built_text = ""
                if stats_item_id > 0:
                    entry["item_id"] = int(stats_item_id)
                    built_text = sender._build_item_stats_text(
                        int(stats_item_id),
                        str(entry.get("item_name", "Unknown Item") or "Unknown Item"),
                    )
                entry["stats_text"] = str(built_text or "")
                stats_text = str(entry.get("stats_text", "") or "")
                stats_build_budget -= 1
                if stats_text:
                    sender._remember_event_stats_snapshot(
                        event_id=str(entry.get("event_id", "")),
                        item_id=int(entry.get("item_id", 0)),
                        model_id=int(entry.get("model_id", 0)),
                        item_name=str(entry.get("item_name", "") or ""),
                        stats_text=stats_text,
                        name_signature=str(entry.get("name_signature", "") or ""),
                        rarity=str(entry.get("rarity", "") or ""),
                        last_receiver_email=str(entry.get("last_receiver_email", "") or ""),
                    )
            ok_stats = sender._send_stats_chunks(
                receiver_email=receiver_email,
                my_email=my_email,
                event_id=str(entry.get("event_id", "")),
                stats_text=stats_text,
            )
            if ok_stats:
                entry["stats_chunks_sent"] = True

        if not send_failed:
            sender._log_name_trace(
                (
                    f"NAME TRACE drop_send ev={str(entry.get('event_id', '') or '').strip() or '-'} "
                    f"item='{str(entry.get('item_name', '') or '').strip() or '-'}' "
                    f"full='{str(entry.get('full_name', '') or '').strip() or '-'}' "
                    f"sig={str(entry.get('name_signature', '') or '').strip().lower() or '-'} "
                    f"receiver={str(receiver_email or '').strip().lower() or '-'}"
                )
            )
            if not sender._send_drop(
                entry.get("item_name", "Unknown Item"),
                int(entry.get("quantity", 1)),
                str(entry.get("rarity", "Unknown")),
                str(entry.get("display_time", "")),
                int(entry.get("item_id", 0)),
                int(entry.get("model_id", 0)),
                int(entry.get("bag_id", 0)),
                int(entry.get("slot_id", 0)),
                is_leader_sender,
                str(entry.get("event_id", "")),
                str(entry.get("name_signature", "")),
                int(entry.get("sender_session_id", 0)),
            ):
                send_failed = True
            elif not bool(entry.get("name_refresh_scheduled", False)):
                sender._schedule_name_refresh_for_entry(entry, receiver_email)
                entry["name_refresh_scheduled"] = True

        entry["attempts"] = int(entry.get("attempts", 0)) + 1
        if send_failed:
            entry["next_retry_at"] = now_ts + retry_delay_s
            continue
        if sender.enable_delivery_ack:
            entry["next_retry_at"] = now_ts + retry_delay_s
        else:
            entry["acked"] = True
        sent += 1

    if not sender.enable_delivery_ack:
        sender.outbox_queue = [entry for entry in sender.outbox_queue if not entry.get("acked", False)]
    return sent
