import re

from Py4GWCoreLib import Py4GW

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import update_rows_item_stats_by_event_and_sender
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import decode_name_chunk_meta
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import (
    handle_tracker_name_branch,
    handle_tracker_stats_payload_branch,
    handle_tracker_stats_text_branch,
    merge_name_chunk,
    merge_stats_payload_chunk,
    merge_stats_text_chunk,
    payload_has_valid_mods_json,
)


def process_tracker_name_message(
    viewer,
    *,
    extra_0,
    extra_data_list,
    shared_msg,
    my_email,
    msg_idx,
    now_ts,
    is_leader_client,
    ignore_tracker_messages,
    shmem,
    batch_rows,
    to_text_fn,
):
    if extra_0 != "TrackerNameV2":
        return {"handled": 0, "processed": 0, "scanned": 0}
    if not is_leader_client:
        shmem.MarkMessageAsFinished(my_email, msg_idx)
        return {"handled": 1, "processed": 0, "scanned": 0}
    if ignore_tracker_messages:
        viewer._log_reset_trace(
            (
                f"RESET TRACE ignore actor={viewer._reset_trace_actor_label()} "
                f"tag=TrackerNameV2 idx={msg_idx}"
            ),
            consume=True,
        )
        return {"handled": 1, "processed": 0, "scanned": 0}

    name_sender_email = str(getattr(shared_msg, "SenderEmail", "") or "").strip()
    name_sender_name = viewer._resolve_sender_name_from_email(name_sender_email)
    renamed_rows = 0

    def _merge_name_chunk_and_refresh_rows(
        name_chunk_buffers,
        full_name_by_signature,
        name_signature,
        chunk_text,
        chunk_idx,
        chunk_total,
        now_ts_arg,
    ):
        merged = merge_name_chunk(
            name_chunk_buffers,
            full_name_by_signature,
            name_signature,
            chunk_text,
            chunk_idx,
            chunk_total,
            now_ts_arg,
        )
        nonlocal renamed_rows
        if merged:
            renamed_rows += viewer._update_rows_item_name_by_signature_and_sender(
                name_signature,
                name_sender_email,
                merged,
                player_name=name_sender_name,
            )
            for pending_row in batch_rows:
                if not isinstance(pending_row, dict):
                    continue
                pending_sender = viewer._ensure_text(pending_row.get("sender_email", "")).strip().lower()
                pending_player = viewer._ensure_text(pending_row.get("player_name", "")).strip()
                if name_sender_email:
                    if pending_sender and pending_sender != name_sender_email.lower():
                        continue
                elif name_sender_name and viewer._ensure_text(pending_player).strip().lower() != name_sender_name.lower():
                    continue
                pending_event_id = viewer._ensure_text(pending_row.get("event_id", "")).strip()
                if not pending_event_id:
                    continue
                pending_cache_key = viewer._make_stats_cache_key(
                    pending_event_id,
                    pending_sender,
                    pending_player,
                )
                pending_sig = viewer._ensure_text(
                    viewer.stats_name_signature_by_event.get(pending_cache_key, "")
                ).strip().lower()
                if pending_sig != viewer._ensure_text(name_signature).strip().lower():
                    continue
                if not viewer._should_allow_late_name_update(
                    pending_row.get("extra_info", ""),
                    pending_row.get("item_name", ""),
                    merged,
                ):
                    continue
                pending_row["item_name"] = viewer._clean_item_name(merged) or pending_row.get("item_name", "Unknown Item")
            viewer._log_name_trace(
                (
                    f"NAME TRACE chunk sender={name_sender_email or '-'} "
                    f"player={name_sender_name or '-'} sig={viewer._ensure_text(name_signature).strip().lower() or '-'} "
                    f"merged='{viewer._clean_item_name(merged) or '-'}' renamed_rows={int(renamed_rows)}"
                )
            )
        return merged

    if handle_tracker_name_branch(
        extra_0=extra_0,
        expected_tag="TrackerNameV2",
        extra_data_list=extra_data_list,
        to_text_fn=to_text_fn,
        decode_chunk_meta_fn=decode_name_chunk_meta,
        merge_name_chunk_fn=_merge_name_chunk_and_refresh_rows,
        name_chunk_buffers=viewer.name_chunk_buffers,
        full_name_by_signature=viewer.full_name_by_signature,
        now_ts=now_ts,
    ):
        if renamed_rows > 0:
            viewer._rebuild_aggregates_from_raw_drops()
        shmem.MarkMessageAsFinished(my_email, msg_idx)
    return {"handled": 1, "processed": 1, "scanned": 1}


def process_tracker_stats_payload_message(
    viewer,
    *,
    extra_0,
    extra_data_list,
    shared_msg,
    my_email,
    msg_idx,
    now_ts,
    is_leader_client,
    ignore_tracker_messages,
    shmem,
    to_text_fn,
):
    if extra_0 != "TrackerStatsV2":
        return {"handled": 0, "processed": 0, "scanned": 0}
    if not is_leader_client:
        shmem.MarkMessageAsFinished(my_email, msg_idx)
        return {"handled": 1, "processed": 0, "scanned": 0}
    if ignore_tracker_messages:
        viewer._log_reset_trace(
            (
                f"RESET TRACE ignore actor={viewer._reset_trace_actor_label()} "
                f"tag=TrackerStatsV2 idx={msg_idx}"
            ),
            consume=True,
        )
        return {"handled": 1, "processed": 0, "scanned": 0}

    stats_sender_email = str(getattr(shared_msg, "SenderEmail", "") or "").strip()
    stats_sender_name = viewer._resolve_sender_name_from_email(stats_sender_email)

    def _merge_payload_chunk_scoped(buffers, event_id_arg, chunk_text_arg, chunk_idx_arg, chunk_total_arg, now_ts_arg):
        scoped_key = viewer._make_stats_cache_key(event_id_arg, stats_sender_email, stats_sender_name)
        return merge_stats_payload_chunk(
            buffers,
            scoped_key,
            chunk_text_arg,
            chunk_idx_arg,
            chunk_total_arg,
            now_ts_arg,
        )

    def _on_payload_merged(event_id, merged_payload):
        stats_cache_key = viewer._make_stats_cache_key(event_id, stats_sender_email, stats_sender_name)
        payload_ok = payload_has_valid_mods_json(merged_payload)
        if not payload_ok:
            if viewer.verbose_shmem_item_logs or viewer.debug_item_stats_panel:
                preview = merged_payload[:220].replace("\n", " ")
                Py4GW.Console.Log(
                    "DropViewer",
                    f"STATS V2 parse error ev={event_id} | payload_head={preview}",
                    Py4GW.Console.MessageType.Warning,
                )
            viewer.stats_payload_by_event.pop(stats_cache_key, None)
            viewer.remote_stats_pending_by_event.pop(stats_cache_key, None)
            viewer.remote_stats_request_last_by_event[stats_cache_key] = 0.0
            viewer.stats_render_cache_by_event.pop(stats_cache_key, None)
            return

        rendered = viewer._render_payload_stats_cached(
            stats_cache_key,
            merged_payload,
            "",
            owner_name=stats_sender_name,
        ).strip()
        viewer._update_event_state(
            stats_cache_key,
            identified=viewer._payload_is_identified(merged_payload),
            payload_text=merged_payload,
            set_payload_text=True,
            stats_text=rendered,
            set_stats_text=bool(rendered),
        )
        if rendered:
            viewer.stats_by_event[stats_cache_key] = rendered
        viewer.stats_payload_by_event[stats_cache_key] = merged_payload
        viewer.remote_stats_pending_by_event.pop(stats_cache_key, None)
        resolved_payload_name = viewer._extract_payload_item_name(merged_payload, "")
        before_names = viewer._get_row_names_by_event_and_sender(event_id, stats_sender_email, stats_sender_name)
        renamed_rows = viewer._update_rows_item_name_by_event_and_sender(
            event_id,
            stats_sender_email,
            resolved_payload_name,
            player_name=stats_sender_name,
            only_if_unknown=False,
        )
        after_names = viewer._get_row_names_by_event_and_sender(event_id, stats_sender_email, stats_sender_name)
        viewer._log_name_trace(
            (
                f"NAME TRACE payload ev={event_id or '-'} sender={stats_sender_email or '-'} "
                f"player={stats_sender_name or '-'} payload_name='{resolved_payload_name or '-'}' "
                f"renamed_rows={int(renamed_rows)} before={before_names[:3]} after={after_names[:3]}"
            )
        )
        if renamed_rows > 0:
            viewer._rebuild_aggregates_from_raw_drops()
        if rendered:
            update_rows_item_stats_by_event_and_sender(
                viewer.raw_drops,
                event_id,
                stats_sender_email,
                rendered,
                player_name=stats_sender_name,
                allow_player_fallback=False,
            )
        if viewer.selected_log_row and viewer._extract_row_event_id(viewer.selected_log_row) == event_id:
            selected_row = viewer._parse_drop_row(viewer.selected_log_row)
            selected_player = viewer._ensure_text(selected_row.player_name).strip() if selected_row else ""
            can_update_selected = False
            if stats_sender_name:
                can_update_selected = selected_player.lower() == stats_sender_name.lower()
            else:
                event_matches = 0
                for raw_row in viewer.raw_drops:
                    if viewer._extract_row_event_id(raw_row) == event_id:
                        event_matches += 1
                        if event_matches > 1:
                            break
                can_update_selected = event_matches <= 1
            if rendered and can_update_selected:
                viewer._set_row_item_stats(viewer.selected_log_row, rendered)

    if handle_tracker_stats_payload_branch(
        extra_0=extra_0,
        expected_tag="TrackerStatsV2",
        extra_data_list=extra_data_list,
        to_text_fn=to_text_fn,
        decode_chunk_meta_fn=decode_name_chunk_meta,
        merge_stats_payload_chunk_fn=_merge_payload_chunk_scoped,
        stats_payload_chunk_buffers=viewer.stats_payload_chunk_buffers,
        now_ts=now_ts,
        on_merged_payload_fn=_on_payload_merged,
    ):
        shmem.MarkMessageAsFinished(my_email, msg_idx)
    return {"handled": 1, "processed": 1, "scanned": 1}


def process_tracker_stats_text_message(
    viewer,
    *,
    extra_0,
    extra_data_list,
    shared_msg,
    my_email,
    msg_idx,
    now_ts,
    is_leader_client,
    ignore_tracker_messages,
    shmem,
    to_text_fn,
):
    if extra_0 != "TrackerStatsV1":
        return {"handled": 0, "processed": 0, "scanned": 0}
    if not is_leader_client:
        shmem.MarkMessageAsFinished(my_email, msg_idx)
        return {"handled": 1, "processed": 0, "scanned": 0}
    if ignore_tracker_messages:
        viewer._log_reset_trace(
            (
                f"RESET TRACE ignore actor={viewer._reset_trace_actor_label()} "
                f"tag=TrackerStatsV1 idx={msg_idx}"
            ),
            consume=True,
        )
        return {"handled": 1, "processed": 0, "scanned": 0}

    stats_sender_email = str(getattr(shared_msg, "SenderEmail", "") or "").strip()
    stats_sender_name = viewer._resolve_sender_name_from_email(stats_sender_email)

    def _merge_text_chunk_scoped(buffers, event_id_arg, chunk_text_arg, chunk_idx_arg, chunk_total_arg, now_ts_arg):
        scoped_key = viewer._make_stats_cache_key(event_id_arg, stats_sender_email, stats_sender_name)
        return merge_stats_text_chunk(
            buffers,
            scoped_key,
            chunk_text_arg,
            chunk_idx_arg,
            chunk_total_arg,
            now_ts_arg,
        )

    def _on_text_merged(event_id, merged):
        stats_cache_key = viewer._make_stats_cache_key(event_id, stats_sender_email, stats_sender_name)
        normalized_merged = viewer._normalize_stats_text(merged)
        viewer._update_event_state(
            stats_cache_key,
            identified=viewer._infer_identified_from_stats_text(normalized_merged),
            stats_text=normalized_merged,
            set_stats_text=True,
        )
        viewer.stats_by_event[stats_cache_key] = normalized_merged
        viewer.remote_stats_pending_by_event.pop(stats_cache_key, None)
        first_line = ""
        if normalized_merged:
            first_line = viewer._ensure_text(normalized_merged.splitlines()[0]).strip()
            if re.match(
                r"(?i)^(value:|damage:|armor:|requires\b|halves\b|reduces\b|improved sale value\b)",
                first_line,
            ):
                first_line = ""
            elif first_line.lower() == "unidentified":
                first_line = ""
        before_names = viewer._get_row_names_by_event_and_sender(event_id, stats_sender_email, stats_sender_name)
        renamed_rows = viewer._update_rows_item_name_by_event_and_sender(
            event_id,
            stats_sender_email,
            first_line,
            player_name=stats_sender_name,
            only_if_unknown=False,
        )
        after_names = viewer._get_row_names_by_event_and_sender(event_id, stats_sender_email, stats_sender_name)
        viewer._log_name_trace(
            (
                f"NAME TRACE text ev={event_id or '-'} sender={stats_sender_email or '-'} "
                f"player={stats_sender_name or '-'} first_line='{first_line or '-'}' "
                f"renamed_rows={int(renamed_rows)} before={before_names[:3]} after={after_names[:3]}"
            )
        )
        if renamed_rows > 0:
            viewer._rebuild_aggregates_from_raw_drops()
        update_rows_item_stats_by_event_and_sender(
            viewer.raw_drops,
            event_id,
            stats_sender_email,
            normalized_merged,
            player_name=stats_sender_name,
            allow_player_fallback=False,
        )
        if viewer.selected_log_row and viewer._extract_row_event_id(viewer.selected_log_row) == event_id:
            selected_row = viewer._parse_drop_row(viewer.selected_log_row)
            selected_player = viewer._ensure_text(selected_row.player_name).strip() if selected_row else ""
            can_update_selected = False
            if stats_sender_name:
                can_update_selected = selected_player.lower() == stats_sender_name.lower()
            else:
                event_matches = 0
                for raw_row in viewer.raw_drops:
                    if viewer._extract_row_event_id(raw_row) == event_id:
                        event_matches += 1
                        if event_matches > 1:
                            break
                can_update_selected = event_matches <= 1
            if can_update_selected:
                viewer._set_row_item_stats(viewer.selected_log_row, normalized_merged)

    if handle_tracker_stats_text_branch(
        extra_0=extra_0,
        expected_tag="TrackerStatsV1",
        extra_data_list=extra_data_list,
        to_text_fn=to_text_fn,
        decode_chunk_meta_fn=decode_name_chunk_meta,
        merge_stats_text_chunk_fn=_merge_text_chunk_scoped,
        stats_chunk_buffers=viewer.stats_chunk_buffers,
        now_ts=now_ts,
        on_merged_text_fn=_on_text_merged,
    ):
        shmem.MarkMessageAsFinished(my_email, msg_idx)
    return {"handled": 1, "processed": 1, "scanned": 1}
