import re

from Py4GWCoreLib import Py4GW

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import decode_name_chunk_meta
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import make_name_signature
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import (
    handle_tracker_name_branch,
    handle_tracker_stats_payload_branch,
    handle_tracker_stats_text_branch,
    merge_name_chunk,
    merge_stats_payload_chunk,
    merge_stats_text_chunk,
    payload_has_valid_mods_json,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_row_updates import update_rows_item_stats_by_event_and_sender


def _append_stats_binding_debug_log(
    viewer,
    event_name: str,
    *,
    event_id: str,
    sender_email: str,
    player_name: str,
    row_names_before: list[str],
    row_names_after: list[str],
    payload_name: str = "",
    first_line_name: str = "",
    rendered_head: str = "",
    update_source: str,
) -> None:
    append_fn = getattr(viewer, "_append_live_debug_log", None)
    if not callable(append_fn):
        return
    append_fn(
        event_name,
        f"event_id={viewer._ensure_text(event_id).strip()}",
        event_id=viewer._ensure_text(event_id).strip(),
        sender_email=viewer._ensure_text(sender_email).strip().lower(),
        player_name=viewer._ensure_text(player_name).strip(),
        row_names_before=list(row_names_before or [])[:5],
        row_names_after=list(row_names_after or [])[:5],
        payload_name=viewer._clean_item_name(payload_name).strip(),
        first_line_name=viewer._clean_item_name(first_line_name).strip(),
        rendered_head=viewer._ensure_text(rendered_head).strip()[:220],
        update_source=viewer._ensure_text(update_source).strip() or "unknown",
    )


def _compact_item_name_key(viewer, value: str) -> str:
    clean_value = viewer._clean_item_name(value).strip().lower()
    if not clean_value:
        return ""
    return re.sub(r"[^a-z0-9]+", "", clean_value)


def _compact_name_keys_overlap(compact_rows: set[str], compact_candidates: set[str]) -> bool:
    if not compact_rows or not compact_candidates:
        return False
    for candidate_name in compact_candidates:
        for row_name in compact_rows:
            if candidate_name == row_name:
                return True
            if candidate_name in row_name:
                return True
            if row_name in candidate_name:
                return True
    return False


def _append_stats_name_mismatch_debug_log(
    viewer,
    *,
    event_id: str,
    sender_email: str,
    player_name: str,
    row_names: list[str],
    payload_name: str = "",
    first_line_name: str = "",
    rendered_head: str = "",
    update_source: str,
) -> None:
    clean_payload_name = viewer._clean_item_name(payload_name).strip()
    clean_first_line = viewer._clean_item_name(first_line_name).strip()
    normalized_candidates = [
        viewer._normalize_item_name(value)
        for value in [clean_payload_name, clean_first_line]
        if viewer._clean_item_name(value).strip()
    ]
    if not normalized_candidates:
        return
    normalized_rows = [
        viewer._normalize_item_name(value)
        for value in list(row_names or [])
        if viewer._clean_item_name(value).strip()
    ]
    if not normalized_rows:
        return
    for candidate_name in normalized_candidates:
        if any(candidate_name == row_name for row_name in normalized_rows):
            return
    compact_candidates = [
        _compact_item_name_key(viewer, value)
        for value in [clean_payload_name, clean_first_line]
        if viewer._clean_item_name(value).strip()
    ]
    compact_candidates = [value for value in compact_candidates if value]
    if compact_candidates:
        compact_rows = {
            _compact_item_name_key(viewer, value)
            for value in list(row_names or [])
            if viewer._clean_item_name(value).strip()
        }
        compact_rows = {value for value in compact_rows if value}
        if _compact_name_keys_overlap(set(compact_rows), set(compact_candidates)):
            return
    _append_stats_binding_debug_log(
        viewer,
        "viewer_stats_name_mismatch",
        event_id=event_id,
        sender_email=sender_email,
        player_name=player_name,
        row_names_before=row_names,
        row_names_after=row_names,
        payload_name=clean_payload_name,
        first_line_name=clean_first_line,
        rendered_head=rendered_head,
        update_source=update_source,
    )


def _should_bind_stats_to_rows(
    viewer,
    *,
    row_names: list[str],
    payload_name: str = "",
    first_line_name: str = "",
) -> bool:
    normalized_rows = {
        viewer._normalize_item_name(value)
        for value in list(row_names or [])
        if viewer._clean_item_name(value).strip()
    }
    if not normalized_rows:
        return True

    normalized_candidates = [
        viewer._normalize_item_name(value)
        for value in [payload_name, first_line_name]
        if viewer._clean_item_name(value).strip()
    ]
    if not normalized_candidates:
        return True

    if any(candidate in normalized_rows for candidate in normalized_candidates):
        return True

    compact_rows = {
        _compact_item_name_key(viewer, value)
        for value in list(row_names or [])
        if viewer._clean_item_name(value).strip()
    }
    compact_rows = {value for value in compact_rows if value}
    if not compact_rows:
        return False
    compact_candidates = {
        _compact_item_name_key(viewer, value)
        for value in [payload_name, first_line_name]
        if viewer._clean_item_name(value).strip()
    }
    compact_candidates = {value for value in compact_candidates if value}
    if not compact_candidates:
        return False
    return _compact_name_keys_overlap(compact_rows, compact_candidates)


def _should_preserve_existing_stats_text(viewer, existing_text: str, incoming_text: str) -> bool:
    normalized_existing = viewer._normalize_stats_text(existing_text)
    normalized_incoming = viewer._normalize_stats_text(incoming_text)
    if not normalized_existing or not normalized_incoming:
        return False
    if normalized_existing == normalized_incoming:
        return False
    try:
        existing_unidentified = bool(viewer._is_unidentified_stats_text(normalized_existing))
    except AttributeError:
        existing_unidentified = str(normalized_existing.splitlines()[0]).strip().lower() == "unidentified"
    try:
        incoming_unidentified = bool(viewer._is_unidentified_stats_text(normalized_incoming))
    except AttributeError:
        incoming_unidentified = str(normalized_incoming.splitlines()[0]).strip().lower() == "unidentified"
    if existing_unidentified:
        return False
    existing_basic = bool(viewer._stats_text_is_basic(normalized_existing))
    incoming_basic = bool(viewer._stats_text_is_basic(normalized_incoming))
    if incoming_unidentified:
        return True
    if (not existing_basic) and incoming_basic:
        return True
    return False


def _pending_row_matches_name_signature(
    viewer,
    pending_row,
    *,
    target_sig: str,
    sender_email: str,
    player_name: str,
) -> bool:
    target_sig_key = viewer._ensure_text(target_sig).strip().lower()
    if not target_sig_key or not isinstance(pending_row, dict):
        return False
    sender_key = viewer._ensure_text(sender_email).strip().lower()
    player_key = viewer._ensure_text(player_name).strip().lower()
    pending_sender = viewer._ensure_text(pending_row.get("sender_email", "")).strip().lower()
    pending_player = viewer._ensure_text(pending_row.get("player_name", "")).strip().lower()
    if sender_key:
        if pending_sender:
            if pending_sender != sender_key:
                return False
        elif not player_key or pending_player != player_key:
            return False
    elif player_key and pending_player != player_key:
        return False
    pending_event_id = viewer._ensure_text(pending_row.get("event_id", "")).strip()
    if not pending_event_id:
        return False
    pending_cache_key = viewer._make_stats_cache_key(
        pending_event_id,
        pending_sender,
        pending_player,
    )
    pending_sig = viewer._ensure_text(
        viewer.stats_name_signature_by_event.get(pending_cache_key, "")
    ).strip().lower()
    if pending_sig == target_sig_key:
        return True
    pending_name = viewer._clean_item_name(pending_row.get("item_name", "")).strip()
    derived_sig = viewer._ensure_text(make_name_signature(pending_name) if pending_name else "").strip().lower()
    return derived_sig == target_sig_key


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
        name_event_id="",
    ):
        merged = merge_name_chunk(
            name_chunk_buffers,
            full_name_by_signature,
            name_signature,
            chunk_text,
            chunk_idx,
            chunk_total,
            now_ts_arg,
            name_event_id,
        )
        nonlocal renamed_rows
        if merged:
            merged_event_id = viewer._ensure_text(name_event_id).strip()
            renamed_for_event = 0
            exact_pending_match = None
            fallback_pending_matches: list[dict] = []
            target_sig = viewer._ensure_text(name_signature).strip().lower()
            for pending_row in batch_rows:
                if not isinstance(pending_row, dict):
                    continue
                pending_event_id = viewer._ensure_text(pending_row.get("event_id", "")).strip()
                if not pending_event_id:
                    continue
                if merged_event_id and pending_event_id == merged_event_id:
                    exact_pending_match = pending_row
                    continue
                if _pending_row_matches_name_signature(
                    viewer,
                    pending_row,
                    target_sig=target_sig,
                    sender_email=name_sender_email,
                    player_name=name_sender_name,
                ):
                    fallback_pending_matches.append(pending_row)
            if merged_event_id:
                renamed_for_event = viewer._update_rows_item_name_by_event_and_sender(
                    merged_event_id,
                    name_sender_email,
                    merged,
                    player_name=name_sender_name,
                    only_if_unknown=False,
                )
                renamed_rows += int(renamed_for_event)
            should_try_committed_signature_fallback = (
                int(renamed_for_event) <= 0
                and exact_pending_match is None
                and len(fallback_pending_matches) <= 0
            )
            should_try_pending_signature_fallback = (
                int(renamed_for_event) <= 0
                and exact_pending_match is None
            )
            if should_try_committed_signature_fallback:
                renamed_rows += viewer._update_rows_item_name_by_signature_and_sender(
                    name_signature,
                    name_sender_email,
                    merged,
                    player_name=name_sender_name,
                )
            pending_rows_to_update: list[dict] = []
            if isinstance(exact_pending_match, dict):
                pending_rows_to_update.append(exact_pending_match)
            elif should_try_pending_signature_fallback and len(fallback_pending_matches) == 1:
                pending_rows_to_update.extend(fallback_pending_matches)
            elif should_try_pending_signature_fallback and len(fallback_pending_matches) > 1:
                append_fn = getattr(viewer, "_append_live_debug_log", None)
                if callable(append_fn):
                    append_fn(
                        "viewer_signature_name_update_skipped_ambiguous_pending",
                        f"sender={name_sender_email or name_sender_name}",
                        sender_email=viewer._ensure_text(name_sender_email).strip().lower(),
                        player_name=viewer._ensure_text(name_sender_name).strip().lower(),
                        name_signature=target_sig,
                        candidate_count=len(fallback_pending_matches),
                        candidate_event_ids=[
                            viewer._ensure_text(row.get("event_id", "")).strip()
                            for row in fallback_pending_matches[:8]
                        ],
                        proposed_name=viewer._clean_item_name(merged).strip(),
                    )
            for pending_row in pending_rows_to_update:
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
                    f"event_id={viewer._ensure_text(merged_event_id).strip() or '-'} "
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
        _append_stats_binding_debug_log(
            viewer,
            "viewer_stats_payload_bound",
            event_id=event_id,
            sender_email=stats_sender_email,
            player_name=stats_sender_name,
            row_names_before=before_names,
            row_names_after=after_names,
            payload_name=resolved_payload_name,
            rendered_head=rendered,
            update_source="payload",
        )
        _append_stats_name_mismatch_debug_log(
            viewer,
            event_id=event_id,
            sender_email=stats_sender_email,
            player_name=stats_sender_name,
            row_names=after_names or before_names,
            payload_name=resolved_payload_name,
            rendered_head=rendered,
            update_source="payload",
        )
        should_bind = _should_bind_stats_to_rows(
            viewer,
            row_names=after_names or before_names,
            payload_name=resolved_payload_name,
        )
        viewer._log_name_trace(
            (
                f"NAME TRACE payload ev={event_id or '-'} sender={stats_sender_email or '-'} "
                f"player={stats_sender_name or '-'} payload_name='{resolved_payload_name or '-'}' "
                f"renamed_rows={int(renamed_rows)} bind_stats={int(bool(should_bind))} "
                f"before={before_names[:3]} after={after_names[:3]}"
            )
        )
        if renamed_rows > 0:
            viewer._rebuild_aggregates_from_raw_drops()
        if rendered and should_bind:
            update_rows_item_stats_by_event_and_sender(
                viewer,
                event_id,
                stats_sender_email,
                rendered,
                player_name=stats_sender_name,
                allow_player_fallback=False,
            )
        if should_bind and viewer.selected_log_row and viewer._extract_row_event_id(viewer.selected_log_row) == event_id:
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
        existing_state_text = viewer._get_event_state_stats_text(stats_cache_key)
        preserve_existing = _should_preserve_existing_stats_text(
            viewer,
            existing_state_text,
            normalized_merged,
        )
        effective_text = existing_state_text if preserve_existing else normalized_merged
        viewer._update_event_state(
            stats_cache_key,
            identified=viewer._infer_identified_from_stats_text(effective_text),
            stats_text=effective_text,
            set_stats_text=True,
        )
        viewer.stats_by_event[stats_cache_key] = effective_text
        viewer.remote_stats_pending_by_event.pop(stats_cache_key, None)
        first_line = ""
        if effective_text:
            first_line = viewer._ensure_text(effective_text.splitlines()[0]).strip()
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
        _append_stats_binding_debug_log(
            viewer,
            "viewer_stats_text_bound",
            event_id=event_id,
            sender_email=stats_sender_email,
            player_name=stats_sender_name,
            row_names_before=before_names,
            row_names_after=after_names,
            first_line_name=first_line,
            rendered_head=effective_text,
            update_source="text",
        )
        if preserve_existing:
            _append_stats_binding_debug_log(
                viewer,
                "viewer_stats_text_downgrade_ignored",
                event_id=event_id,
                sender_email=stats_sender_email,
                player_name=stats_sender_name,
                row_names_before=before_names,
                row_names_after=after_names,
                first_line_name=first_line,
                rendered_head=normalized_merged,
                update_source="text",
            )
        _append_stats_name_mismatch_debug_log(
            viewer,
            event_id=event_id,
            sender_email=stats_sender_email,
            player_name=stats_sender_name,
            row_names=after_names or before_names,
            first_line_name=first_line,
            rendered_head=effective_text,
            update_source="text",
        )
        should_bind = _should_bind_stats_to_rows(
            viewer,
            row_names=after_names or before_names,
            first_line_name=first_line,
        )
        viewer._log_name_trace(
            (
                f"NAME TRACE text ev={event_id or '-'} sender={stats_sender_email or '-'} "
                f"player={stats_sender_name or '-'} first_line='{first_line or '-'}' "
                f"renamed_rows={int(renamed_rows)} bind_stats={int(bool(should_bind))} "
                f"before={before_names[:3]} after={after_names[:3]}"
            )
        )
        if renamed_rows > 0:
            viewer._rebuild_aggregates_from_raw_drops()
        if should_bind:
            update_rows_item_stats_by_event_and_sender(
                viewer,
                event_id,
                stats_sender_email,
                effective_text,
                player_name=stats_sender_name,
                allow_player_fallback=False,
            )
        if should_bind and viewer.selected_log_row and viewer._extract_row_event_id(viewer.selected_log_row) == event_id:
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
                viewer._set_row_item_stats(viewer.selected_log_row, effective_text)

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
