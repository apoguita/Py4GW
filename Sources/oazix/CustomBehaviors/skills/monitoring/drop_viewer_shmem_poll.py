import sys
import time
from typing import Any


EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _viewer_runtime_module(viewer):
    try:
        return sys.modules.get(viewer.__class__.__module__)
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _runtime_attr(viewer, name: str, fallback=None):
    module = _viewer_runtime_module(viewer)
    if module is not None and hasattr(module, name):
        return getattr(module, name)
    return fallback


def poll_shared_memory(viewer) -> None:
    player_api = _runtime_attr(viewer, "Player", None)
    party_api = _runtime_attr(viewer, "Party", None)
    shared_command_type = _runtime_attr(viewer, "SharedCommandType", None)
    global_cache = _runtime_attr(viewer, "GLOBAL_CACHE", None)
    py4gw_api = _runtime_attr(viewer, "Py4GW", None)
    prune_render_cache_fn = _runtime_attr(viewer, "prune_render_cache", None)
    iter_circular_indices_fn = _runtime_attr(viewer, "iter_circular_indices", None)
    should_skip_inventory_action_message_fn = _runtime_attr(viewer, "should_skip_inventory_action_message", None)
    process_inventory_message_fn = _runtime_attr(viewer, "process_inventory_message", None)
    process_tracker_name_message_fn = _runtime_attr(viewer, "process_tracker_name_message", None)
    process_tracker_stats_payload_message_fn = _runtime_attr(viewer, "process_tracker_stats_payload_message", None)
    process_tracker_stats_text_message_fn = _runtime_attr(viewer, "process_tracker_stats_text_message", None)
    process_tracker_drop_message_fn = _runtime_attr(viewer, "process_tracker_drop_message", None)
    extract_event_id_hint_fn = _runtime_attr(viewer, "extract_event_id_hint", None)

    def _c_wchar_array_to_str(arr) -> str:
        return "".join(ch for ch in arr if ch != "\0").rstrip()

    def _normalize_shmem_text(value: Any) -> str:
        if value is None:
            return ""
        if (
            not isinstance(value, str)
            and (
                hasattr(value, "__iter__")
                or (hasattr(value, "__len__") and hasattr(value, "__getitem__"))
            )
        ):
            try:
                return _c_wchar_array_to_str(value)
            except (TypeError, ValueError, RuntimeError, AttributeError):
                pass
        return str(value).strip()

    poll_started = time.perf_counter()
    processed_tracker_msgs = 0
    scanned_msgs = 0
    inventory_action_msgs_handled = 0
    max_shmem_scan_per_tick = max(1, int(viewer._safe_int(viewer.max_shmem_scan_per_tick, 600)))
    max_shmem_messages_per_tick = max(1, int(viewer._safe_int(viewer.max_shmem_messages_per_tick, 80)))
    max_custom_messages_examined_per_tick = max(
        max_shmem_scan_per_tick,
        min(4096, max(32, max_shmem_messages_per_tick * 4)),
    )
    custom_messages_examined = 0
    max_raw_messages_examined_per_tick = max(
        256,
        min(8192, max_shmem_scan_per_tick * 6),
    )
    raw_messages_examined = 0
    max_inventory_action_msgs_per_tick = max(
        8,
        min(64, max_shmem_messages_per_tick),
    )
    batch_rows = []
    ack_sent_this_tick = 0
    try:
        if player_api is None or global_cache is None:
            return

        my_email = player_api.GetAccountEmail()
        if not my_email:
            return

        is_leader_client = False
        try:
            if party_api is not None:
                is_leader_client = (player_api.GetAgentID() == party_api.GetPartyLeaderID())
        except EXPECTED_RUNTIME_ERRORS:
            is_leader_client = False

        shmem = getattr(global_cache, "ShMem", None)
        if shmem is None:
            return

        viewer.shmem_bootstrap_done = True

        now_ts = time.time()
        viewer.seen_events = {
            key: ts for key, ts in viewer.seen_events.items()
            if (now_ts - ts) <= viewer.seen_event_ttl_seconds
        }
        viewer.name_chunk_buffers = {
            sig: data for sig, data in viewer.name_chunk_buffers.items()
            if (now_ts - float(data.get("updated_at", now_ts))) <= 30.0
        }
        viewer.stats_chunk_buffers = {
            sig: data for sig, data in viewer.stats_chunk_buffers.items()
            if (now_ts - float(data.get("updated_at", now_ts))) <= 30.0
        }
        viewer.stats_payload_chunk_buffers = {
            sig: data for sig, data in viewer.stats_payload_chunk_buffers.items()
            if (now_ts - float(data.get("updated_at", now_ts))) <= 30.0
        }
        if prune_render_cache_fn is not None:
            viewer.stats_render_cache_by_event = prune_render_cache_fn(
                viewer.stats_render_cache_by_event,
                now_ts,
                ttl_seconds=1800.0,
            )

        ignore_tracker_messages = now_ts < float(viewer.map_change_ignore_until)
        messages = shmem.GetAllMessages()
        message_count = len(messages)
        if message_count <= 0:
            viewer._shmem_scan_start_index = 0
        start_index = max(0, int(viewer._safe_int(getattr(viewer, "_shmem_scan_start_index", 0), 0)))
        scan_order = iter_circular_indices_fn(message_count, start_index, max_raw_messages_examined_per_tick)
        next_scan_index = start_index
        for message_list_index in scan_order:
            msg_idx, shared_msg = messages[message_list_index]
            if processed_tracker_msgs >= max_shmem_messages_per_tick:
                break
            raw_messages_examined += 1
            if raw_messages_examined > max_raw_messages_examined_per_tick:
                break
            next_scan_index = int((message_list_index + 1) % message_count) if message_count > 0 else 0
            receiver_email = _normalize_shmem_text(getattr(shared_msg, "ReceiverEmail", ""))
            if receiver_email != my_email:
                continue

            command_value = int(getattr(shared_msg, "Command", 0))
            expected_custom_behavior_command = 997
            try:
                if shared_command_type is not None:
                    expected_custom_behavior_command = int(shared_command_type.CustomBehaviors.value)
            except EXPECTED_RUNTIME_ERRORS:
                pass
            if command_value != expected_custom_behavior_command and command_value != 997:
                continue

            should_finish = False
            extra_data_list = None
            try:
                should_finish = False
                extra_data_list = getattr(shared_msg, "ExtraData", None)
                if not extra_data_list or len(extra_data_list) == 0:
                    continue

                extra_0 = _c_wchar_array_to_str(extra_data_list[0])
                if should_skip_inventory_action_message_fn is not None and should_skip_inventory_action_message_fn(
                    tag=extra_0,
                    inventory_action_tag=viewer.inventory_action_tag,
                    inventory_action_msgs_handled=inventory_action_msgs_handled,
                    max_inventory_action_msgs_per_tick=max_inventory_action_msgs_per_tick,
                ):
                    continue
                custom_messages_examined += 1
                if custom_messages_examined > max_custom_messages_examined_per_tick:
                    break

                if process_inventory_message_fn is not None:
                    inventory_result = process_inventory_message_fn(
                        viewer,
                        extra_0=extra_0,
                        extra_data_list=extra_data_list,
                        shared_msg=shared_msg,
                        my_email=my_email,
                        msg_idx=msg_idx,
                        shmem=shmem,
                        to_text_fn=_c_wchar_array_to_str,
                        normalize_text_fn=_normalize_shmem_text,
                    )
                    if inventory_result.get("handled", 0):
                        inventory_action_msgs_handled += int(inventory_result.get("inventory_action", 0))
                        should_finish = bool(inventory_result.get("processed", 0))
                        processed_tracker_msgs += int(inventory_result.get("processed", 0))
                        continue

                if process_tracker_name_message_fn is not None:
                    name_result = process_tracker_name_message_fn(
                        viewer,
                        extra_0=extra_0,
                        extra_data_list=extra_data_list,
                        shared_msg=shared_msg,
                        my_email=my_email,
                        msg_idx=msg_idx,
                        now_ts=now_ts,
                        is_leader_client=is_leader_client,
                        ignore_tracker_messages=ignore_tracker_messages,
                        shmem=shmem,
                        batch_rows=batch_rows,
                        to_text_fn=_c_wchar_array_to_str,
                    )
                    if name_result.get("handled", 0):
                        should_finish = bool(name_result.get("processed", 0))
                        processed_tracker_msgs += int(name_result.get("processed", 0))
                        scanned_msgs += int(name_result.get("scanned", 0))
                        if scanned_msgs > max_shmem_scan_per_tick:
                            break
                        continue

                if process_tracker_stats_payload_message_fn is not None:
                    stats_payload_result = process_tracker_stats_payload_message_fn(
                        viewer,
                        extra_0=extra_0,
                        extra_data_list=extra_data_list,
                        shared_msg=shared_msg,
                        my_email=my_email,
                        msg_idx=msg_idx,
                        now_ts=now_ts,
                        is_leader_client=is_leader_client,
                        ignore_tracker_messages=ignore_tracker_messages,
                        shmem=shmem,
                        to_text_fn=_c_wchar_array_to_str,
                    )
                    if stats_payload_result.get("handled", 0):
                        should_finish = bool(stats_payload_result.get("processed", 0))
                        processed_tracker_msgs += int(stats_payload_result.get("processed", 0))
                        scanned_msgs += int(stats_payload_result.get("scanned", 0))
                        if scanned_msgs > max_shmem_scan_per_tick:
                            break
                        continue

                if process_tracker_stats_text_message_fn is not None:
                    stats_text_result = process_tracker_stats_text_message_fn(
                        viewer,
                        extra_0=extra_0,
                        extra_data_list=extra_data_list,
                        shared_msg=shared_msg,
                        my_email=my_email,
                        msg_idx=msg_idx,
                        now_ts=now_ts,
                        is_leader_client=is_leader_client,
                        ignore_tracker_messages=ignore_tracker_messages,
                        shmem=shmem,
                        to_text_fn=_c_wchar_array_to_str,
                    )
                    if stats_text_result.get("handled", 0):
                        should_finish = bool(stats_text_result.get("processed", 0))
                        processed_tracker_msgs += int(stats_text_result.get("processed", 0))
                        scanned_msgs += int(stats_text_result.get("scanned", 0))
                        if scanned_msgs > max_shmem_scan_per_tick:
                            break
                        continue

                if process_tracker_drop_message_fn is not None:
                    drop_result = process_tracker_drop_message_fn(
                        viewer,
                        extra_0=extra_0,
                        extra_data_list=extra_data_list,
                        shared_msg=shared_msg,
                        my_email=my_email,
                        msg_idx=msg_idx,
                        now_ts=now_ts,
                        is_leader_client=is_leader_client,
                        ignore_tracker_messages=ignore_tracker_messages,
                        shmem=shmem,
                        batch_rows=batch_rows,
                        to_text_fn=_c_wchar_array_to_str,
                        normalize_text_fn=_normalize_shmem_text,
                    )
                    if drop_result.get("handled", 0):
                        should_finish = bool(drop_result.get("processed", 0))
                        processed_tracker_msgs += int(drop_result.get("processed", 0))
                        scanned_msgs += int(drop_result.get("scanned", 0))
                        ack_sent_this_tick += int(drop_result.get("ack_sent", 0))
                        if scanned_msgs > max_shmem_scan_per_tick:
                            break
                        continue
            except (TypeError, ValueError, RuntimeError, AttributeError, IndexError) as msg_e:
                event_hint = ""
                tag_hint = ""
                try:
                    tag_hint = _c_wchar_array_to_str(extra_data_list[0]) if extra_data_list and len(extra_data_list) > 0 else ""
                except (TypeError, ValueError, RuntimeError, AttributeError, IndexError):
                    tag_hint = ""
                try:
                    if extract_event_id_hint_fn is not None:
                        event_hint = extract_event_id_hint_fn(
                            extra_0=tag_hint,
                            extra_data_list=extra_data_list,
                            to_text_fn=_c_wchar_array_to_str,
                        )
                except (TypeError, ValueError, RuntimeError, AttributeError, IndexError):
                    event_hint = ""
                if py4gw_api is not None:
                    py4gw_api.Console.Log(
                        "DropViewer",
                        f"ShMem parse warning idx={msg_idx} tag={tag_hint} ev={event_hint}: {msg_e}",
                        py4gw_api.Console.MessageType.Warning,
                    )
                try:
                    if should_finish:
                        shmem.MarkMessageAsFinished(my_email, msg_idx)
                except (TypeError, ValueError, RuntimeError, AttributeError):
                    pass
                continue

        if message_count > 0:
            viewer._shmem_scan_start_index = int(next_scan_index % message_count)

        if batch_rows:
            viewer._log_drops_batch(batch_rows)
            if py4gw_api is not None:
                py4gw_api.Console.Log(
                    "DropViewer",
                    f"TRACKED BATCH: {len(batch_rows)} items (ShMem)",
                    py4gw_api.Console.MessageType.Info,
                )
    except (TypeError, ValueError, RuntimeError, AttributeError) as e:
        if viewer.shmem_error_timer.IsExpired():
            viewer.shmem_error_timer.Reset()
            if py4gw_api is not None:
                py4gw_api.Console.Log(
                    "DropViewer",
                    f"ShMem poll skipped: {e}",
                    py4gw_api.Console.MessageType.Warning,
                )
    finally:
        viewer.last_shmem_poll_ms = (time.perf_counter() - poll_started) * 1000.0
        viewer.last_shmem_processed = processed_tracker_msgs
        viewer.last_shmem_scanned = scanned_msgs
        if viewer.enable_perf_logs and viewer.perf_timer.IsExpired():
            viewer.perf_timer.Reset()
            if py4gw_api is not None:
                py4gw_api.Console.Log(
                    "DropViewer",
                    (
                        f"perf poll_ms={viewer.last_shmem_poll_ms:.2f} "
                        f"processed={viewer.last_shmem_processed} scanned={viewer.last_shmem_scanned} "
                        f"ack_sent={ack_sent_this_tick}"
                    ),
                    py4gw_api.Console.MessageType.Info,
                )
