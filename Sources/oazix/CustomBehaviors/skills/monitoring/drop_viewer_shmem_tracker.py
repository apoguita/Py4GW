from typing import Any

from Py4GWCoreLib import Py4GW

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import (
    build_tracker_drop_message,
    handle_tracker_drop_branch,
    is_duplicate_event,
    mark_seen_event,
)


def classify_tracker_sender_source(my_email: str, sender_email: str) -> str:
    my_key = str(my_email or "").strip().lower()
    sender_key = str(sender_email or "").strip().lower()
    if my_key and sender_key and my_key == sender_key:
        return "local_sender"
    if sender_key:
        return "party_sender"
    return "unknown_sender"


def classify_drop_name_source(raw_drop_name: str, payload_name: str, final_name: str) -> str:
    raw_name = str(raw_drop_name or "").strip()
    payload = str(payload_name or "").strip()
    final = str(final_name or "").strip()
    if final and payload and final == payload:
        return "payload"
    if final and payload and final != payload:
        return "model_fallback"
    if final and raw_name and final == raw_name:
        return "raw"
    return "unknown"


def process_tracker_drop_message(
    viewer,
    *,
    extra_0: str,
    extra_data_list,
    shared_msg,
    my_email: str,
    msg_idx: int,
    now_ts: float,
    is_leader_client: bool,
    ignore_tracker_messages: bool,
    shmem,
    batch_rows: list[dict[str, Any]],
    to_text_fn,
    normalize_text_fn,
) -> dict[str, int]:
    if extra_0 != "TrackerDrop":
        return {"handled": 0, "processed": 0, "scanned": 0, "ack_sent": 0}

    if not is_leader_client:
        shmem.MarkMessageAsFinished(my_email, msg_idx)
        if hasattr(viewer, "_append_live_debug_log"):
            viewer._append_live_debug_log(
                "viewer_drop_ignored_non_leader",
                f"idx={int(msg_idx)}",
                msg_idx=int(msg_idx),
                sender_email=str(getattr(shared_msg, "SenderEmail", "") or "").strip(),
            )
        return {"handled": 1, "processed": 0, "scanned": 0, "ack_sent": 0}

    if ignore_tracker_messages:
        viewer._log_reset_trace(
            (
                f"RESET TRACE ignore actor={viewer._reset_trace_actor_label()} "
                f"tag=TrackerDrop idx={msg_idx}"
            ),
            consume=True,
        )
        if hasattr(viewer, "_append_live_debug_log"):
            viewer._append_live_debug_log(
                "viewer_drop_ignored_map_grace",
                f"idx={int(msg_idx)}",
                msg_idx=int(msg_idx),
                sender_email=str(getattr(shared_msg, "SenderEmail", "") or "").strip(),
            )
        return {"handled": 1, "processed": 0, "scanned": 0, "ack_sent": 0}

    drop_msg = handle_tracker_drop_branch(
        extra_0=extra_0,
        expected_tag="TrackerDrop",
        extra_data_list=extra_data_list,
        shared_msg=shared_msg,
        to_text_fn=to_text_fn,
        normalize_text_fn=normalize_text_fn,
        build_tracker_drop_message_fn=build_tracker_drop_message,
        resolve_full_name_fn=lambda sig: viewer.full_name_by_signature.get(sig, ""),
        normalize_rarity_label_fn=viewer._normalize_rarity_label,
    )
    if drop_msg is None:
        return {"handled": 1, "processed": 0, "scanned": 1, "ack_sent": 0}

    raw_drop_name = viewer._clean_item_name(to_text_fn(extra_data_list[1]) if len(extra_data_list) > 1 else "")
    event_id = drop_msg.event_id
    payload_name = str(getattr(drop_msg, "item_name", "") or "")
    item_name = viewer._resolve_unknown_name_from_model(payload_name, drop_msg.model_id)
    exact_rarity = drop_msg.rarity
    quantity = drop_msg.quantity
    row_item_id = drop_msg.item_id
    model_id_param = drop_msg.model_id
    slot_bag = drop_msg.slot_bag
    slot_index = drop_msg.slot_index
    sender_email = drop_msg.sender_email
    sender_session_id = max(0, viewer._safe_int(getattr(drop_msg, "sender_session_id", 0), 0))
    sender_key = viewer._ensure_text(sender_email).strip().lower()
    source_label = classify_tracker_sender_source(my_email, sender_email)
    name_source = classify_drop_name_source(raw_drop_name, payload_name, item_name)

    if sender_session_id > 0 and sender_key:
        session_floor = max(0, viewer._safe_int(viewer.sender_session_floor_by_email.get(sender_key, 0), 0))
        if session_floor > 0 and sender_session_id < session_floor:
            viewer._log_reset_trace(
                (
                    f"RESET TRACE rejected stale actor={viewer._reset_trace_actor_label()} "
                    f"sender_email={sender_email} sender_session={sender_session_id} "
                    f"floor={session_floor} item='{item_name}' ev={event_id}"
                ),
                consume=True,
            )
            if event_id:
                viewer._send_tracker_ack(sender_email, event_id)
            shmem.MarkMessageAsFinished(my_email, msg_idx)
            if hasattr(viewer, "_append_live_debug_log"):
                viewer._append_live_debug_log(
                    "viewer_drop_rejected_stale_session",
                    f"event_id={str(event_id or '').strip()}",
                    msg_idx=int(msg_idx),
                    event_id=str(event_id or "").strip(),
                    sender_email=sender_email,
                    sender_session_id=int(sender_session_id),
                    session_floor=int(session_floor),
                    item_name=item_name,
                    item_id=int(row_item_id),
                    model_id=int(model_id_param),
                )
            return {"handled": 1, "processed": 1, "scanned": 1, "ack_sent": 0}
        prev_sender_session = max(
            0,
            viewer._safe_int(viewer.sender_session_last_seen_by_email.get(sender_key, 0), 0),
        )
        if sender_session_id > prev_sender_session:
            viewer.sender_session_last_seen_by_email[sender_key] = sender_session_id

    sender_name_raw = viewer._resolve_sender_name_from_email(sender_email)
    sender_name = sender_name_raw or "Follower"
    stats_cache_key = viewer._make_stats_cache_key(event_id, sender_email, sender_name_raw)
    stats_text = viewer._get_cached_stats_text(viewer.stats_by_event, stats_cache_key)
    if stats_cache_key and drop_msg.name_signature:
        viewer.stats_name_signature_by_event[stats_cache_key] = viewer._ensure_text(drop_msg.name_signature).strip().lower()
    had_full_name_cache = bool(
        viewer._ensure_text(viewer.full_name_by_signature.get(viewer._ensure_text(drop_msg.name_signature).strip(), "")).strip()
    )
    viewer._log_name_trace(
        (
            f"NAME TRACE drop ev={event_id or '-'} sender={sender_email or '-'} player={sender_name or '-'} "
            f"source={source_label} raw='{raw_drop_name or '-'}' payload='{payload_name or '-'}' "
            f"final='{item_name or '-'}' name_src={name_source} "
            f"sig={viewer._ensure_text(drop_msg.name_signature).strip().lower() or '-'} "
            f"full_name_cached={had_full_name_cache}"
        )
    )

    event_key = drop_msg.event_key
    is_duplicate = is_duplicate_event(viewer.seen_events, event_key)
    if not is_duplicate:
        mark_seen_event(viewer.seen_events, event_key, now_ts)

    if not is_duplicate:
        batch_rows.append(
            {
                "player_name": sender_name,
                "item_name": item_name,
                "quantity": quantity,
                "extra_info": exact_rarity,
                "timestamp_override": None,
                "event_id": event_id,
                "item_stats": stats_text,
                "item_id": row_item_id,
                "sender_email": sender_email,
            }
        )
        viewer._log_name_trace(
            (
                f"NAME TRACE row ev={event_id or '-'} sender={sender_email or '-'} player={sender_name or '-'} "
                f"source={source_label} row_name='{item_name or '-'}' name_src={name_source} "
                f"sig={viewer._ensure_text(drop_msg.name_signature).strip().lower() or '-'}"
            )
        )
        viewer._remember_model_name(model_id_param, item_name)
        viewer._log_reset_trace(
            (
                f"RESET TRACE accepted actor={viewer._reset_trace_actor_label()} TrackerDrop idx={msg_idx} "
                f"item='{item_name}' qty={quantity} rarity={exact_rarity} "
                f"sender={sender_name} sender_email={sender_email} source={source_label} "
                f"sender_session={sender_session_id} "
                f"item_id={row_item_id} model_id={model_id_param} "
                f"slot={slot_bag}:{slot_index} ev={event_id}"
            ),
            consume=True,
        )
        if hasattr(viewer, "_append_live_debug_log"):
            viewer._append_live_debug_log(
                "viewer_drop_accepted",
                f"event_id={str(event_id or '').strip()}",
                msg_idx=int(msg_idx),
                event_id=str(event_id or "").strip(),
                sender_email=sender_email,
                sender_name=sender_name,
                sender_session_id=int(sender_session_id),
                item_name=item_name,
                quantity=int(quantity),
                rarity=exact_rarity,
                item_id=int(row_item_id),
                model_id=int(model_id_param),
                slot_bag=int(slot_bag),
                slot_index=int(slot_index),
                duplicate=bool(is_duplicate),
            )

    ack_sent = 0
    if event_id and viewer._send_tracker_ack(sender_email, event_id):
        ack_sent = 1
        if hasattr(viewer, "_append_live_debug_log"):
            viewer._append_live_debug_log(
                "viewer_drop_ack_sent",
                f"event_id={str(event_id or '').strip()}",
                event_id=str(event_id or "").strip(),
                sender_email=sender_email,
            )

    if viewer.verbose_shmem_item_logs:
        log_msg = (
            f"TRACKED: {item_name} x{quantity} ({exact_rarity}) "
            f"[{sender_name}] (source={source_label} name_src={name_source} "
            f"ShMem idx={msg_idx} item_id={row_item_id} "
            f"model_id={model_id_param} slot={slot_bag}:{slot_index} ev={event_id} dup={is_duplicate})"
        )
        Py4GW.Console.Log("DropViewer", log_msg, Py4GW.Console.MessageType.Info)

    shmem.MarkMessageAsFinished(my_email, msg_idx)
    if is_duplicate and hasattr(viewer, "_append_live_debug_log"):
        viewer._append_live_debug_log(
            "viewer_drop_duplicate",
            f"event_id={str(event_id or '').strip()}",
            event_id=str(event_id or "").strip(),
            sender_email=sender_email,
            item_name=item_name,
        )
    return {"handled": 1, "processed": 1, "scanned": 1, "ack_sent": ack_sent}
