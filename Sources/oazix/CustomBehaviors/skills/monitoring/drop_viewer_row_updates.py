import datetime
from typing import Any

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import parse_runtime_row
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import make_name_signature
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_batch_store import persist_runtime_row_to_file


def set_row_item_stats(viewer, row: Any, item_stats: str) -> None:
    from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import set_runtime_row_item_stats

    set_runtime_row_item_stats(row, viewer._ensure_text(item_stats).strip())
    persist_runtime_row_to_file(viewer, row)


def set_row_item_name(viewer, row: Any, item_name: Any) -> None:
    if not isinstance(row, list):
        return
    while len(row) <= 5:
        row.append("")
    row[5] = viewer._clean_item_name(item_name) or "Unknown Item"
    persist_runtime_row_to_file(viewer, row)


def update_rows_item_stats_by_event_and_sender(
    viewer,
    event_id: str,
    sender_email: str,
    item_stats: str,
    player_name: str = "",
    allow_player_fallback: bool = True,
) -> int:
    event_key = viewer._ensure_text(event_id).strip()
    sender_key = viewer._ensure_text(sender_email).strip().lower()
    player_key = viewer._ensure_text(player_name).strip().lower()
    if not event_key:
        return 0

    matched_rows: list[Any] = []
    for row in viewer.raw_drops:
        parsed = parse_runtime_row(row)
        if parsed is None:
            continue
        row_event = viewer._ensure_text(parsed.event_id).strip()
        if row_event != event_key:
            continue
        row_sender = viewer._ensure_text(parsed.sender_email).strip().lower()
        row_player = viewer._ensure_text(parsed.player_name).strip().lower()
        if sender_key:
            if row_sender != sender_key:
                continue
        elif allow_player_fallback:
            if not player_key or row_player != player_key:
                continue
        else:
            continue
        matched_rows.append(row)

    if not matched_rows and allow_player_fallback and player_key:
        for row in viewer.raw_drops:
            parsed = parse_runtime_row(row)
            if parsed is None:
                continue
            row_event = viewer._ensure_text(parsed.event_id).strip()
            row_player = viewer._ensure_text(parsed.player_name).strip().lower()
            if row_event == event_key and row_player == player_key:
                matched_rows.append(row)

    if not matched_rows:
        return 0

    for row in matched_rows:
        set_row_item_stats(viewer, row, item_stats)
    return len(matched_rows)


def _append_name_update_debug_log(
    viewer,
    *,
    event_id: str,
    sender_email: str,
    player_name: str,
    rarity: Any,
    previous_name: Any,
    new_name: Any,
    update_source: str,
) -> None:
    append_fn = getattr(viewer, "_append_live_debug_log", None)
    if not callable(append_fn):
        return
    previous_txt = viewer._clean_item_name(previous_name).strip()
    new_txt = viewer._clean_item_name(new_name).strip()
    append_fn(
        "viewer_row_name_updated",
        f"event_id={viewer._ensure_text(event_id).strip()}",
        event_id=viewer._ensure_text(event_id).strip(),
        sender_email=viewer._ensure_text(sender_email).strip().lower(),
        player_name=viewer._ensure_text(player_name).strip(),
        rarity=viewer._ensure_text(rarity).strip() or "Unknown",
        previous_name=previous_txt,
        new_name=new_txt,
        previous_was_unknown=bool(viewer._is_unknown_item_label(previous_txt)),
        update_source=viewer._ensure_text(update_source).strip() or "unknown",
    )


def should_allow_late_name_update(viewer, rarity: Any, current_name: Any, proposed_name: Any = "") -> bool:
    rarity_txt = viewer._ensure_text(rarity).strip().lower()
    current_txt = viewer._clean_item_name(current_name).strip().lower()
    proposed_txt = viewer._clean_item_name(proposed_name).strip().lower()
    if not current_txt:
        return True
    if bool(viewer._is_unknown_item_label(current_txt)):
        return True
    if not proposed_txt or proposed_txt == current_txt:
        return False
    # Preserve original pickup label for white non-rune items.
    if rarity_txt == "white":
        if "rune" not in current_txt and "rune" not in proposed_txt:
            return False
    if current_txt in proposed_txt and len(proposed_txt) > len(current_txt):
        return True
    return False


def update_rows_item_name_by_event_and_sender(
    viewer,
    event_id: str,
    sender_email: str,
    item_name: Any,
    player_name: str = "",
    only_if_unknown: bool = False,
) -> int:
    event_key = viewer._ensure_text(event_id).strip()
    if not event_key:
        return 0
    clean_name = viewer._clean_item_name(item_name).strip()
    if not clean_name or viewer._is_unknown_item_label(clean_name):
        return 0
    sender_key = viewer._ensure_text(sender_email).strip().lower()
    player_key = viewer._ensure_text(player_name).strip().lower()
    if not sender_key and not player_key:
        return 0
    updated = 0
    for row in viewer.raw_drops:
        parsed = viewer._parse_drop_row(row)
        if parsed is None:
            continue
        if viewer._ensure_text(parsed.event_id).strip() != event_key:
            continue
        row_sender = viewer._ensure_text(parsed.sender_email).strip().lower()
        row_player = viewer._ensure_text(parsed.player_name).strip().lower()
        if sender_key:
            if row_sender:
                if row_sender != sender_key:
                    continue
            else:
                if not player_key or row_player != player_key:
                    continue
        elif player_key and row_player != player_key:
            continue
        current_name = viewer._clean_item_name(parsed.item_name).strip()
        if only_if_unknown and current_name and not viewer._is_unknown_item_label(current_name):
            continue
        if not should_allow_late_name_update(viewer, parsed.rarity, current_name, clean_name):
            continue
        if current_name == clean_name:
            continue
        set_row_item_name(viewer, row, clean_name)
        _append_name_update_debug_log(
            viewer,
            event_id=event_key,
            sender_email=row_sender or sender_key,
            player_name=parsed.player_name,
            rarity=parsed.rarity,
            previous_name=current_name,
            new_name=clean_name,
            update_source="event_and_sender",
        )
        updated += 1
    return updated


def update_rows_item_name_by_signature_and_sender(
    viewer,
    name_signature: str,
    sender_email: str,
    item_name: Any,
    player_name: str = "",
) -> int:
    target_sig = viewer._ensure_text(name_signature).strip().lower()
    clean_name = viewer._clean_item_name(item_name).strip()
    sender_key = viewer._ensure_text(sender_email).strip().lower()
    player_key = viewer._ensure_text(player_name).strip().lower()
    if not target_sig or not clean_name:
        return 0
    if not sender_key and not player_key:
        return 0

    matching_rows: list[tuple[Any, Any, str, str]] = []
    for row in viewer.raw_drops:
        parsed = viewer._parse_drop_row(row)
        if parsed is None:
            continue
        row_sender = viewer._ensure_text(parsed.sender_email).strip().lower()
        row_player = viewer._ensure_text(parsed.player_name).strip().lower()
        if sender_key:
            if row_sender:
                if row_sender != sender_key:
                    continue
            elif not player_key or row_player != player_key:
                continue
        elif player_key and row_player != player_key:
            continue
        event_id = viewer._ensure_text(parsed.event_id).strip()
        if not event_id:
            continue
        cache_key = viewer._make_stats_cache_key(event_id, row_sender, parsed.player_name)
        cached_sig = viewer._ensure_text(viewer.stats_name_signature_by_event.get(cache_key, "")).strip().lower()
        current_name = viewer._clean_item_name(parsed.item_name).strip()
        derived_sig = viewer._ensure_text(make_name_signature(current_name) if current_name else "").strip().lower()
        if cached_sig != target_sig and derived_sig != target_sig:
            continue
        matching_rows.append((row, parsed, row_sender, event_id))

    if len(matching_rows) != 1:
        if len(matching_rows) > 1:
            append_fn = getattr(viewer, "_append_live_debug_log", None)
            if callable(append_fn):
                append_fn(
                    "viewer_signature_name_update_skipped_ambiguous",
                    f"sender={sender_key or player_key}",
                    sender_email=sender_key,
                    player_name=player_key,
                    name_signature=target_sig,
                    candidate_count=len(matching_rows),
                    candidate_event_ids=[event_id for _row, _parsed, _sender, event_id in matching_rows[:8]],
                    proposed_name=clean_name,
                )
        return 0

    row, parsed, row_sender, event_id = matching_rows[0]
    current_name = viewer._clean_item_name(parsed.item_name).strip()
    if not should_allow_late_name_update(viewer, parsed.rarity, current_name, clean_name):
        return 0
    if current_name == clean_name:
        return 0
    set_row_item_name(viewer, row, clean_name)
    _append_name_update_debug_log(
        viewer,
        event_id=event_id,
        sender_email=row_sender or sender_key,
        player_name=parsed.player_name,
        rarity=parsed.rarity,
        previous_name=current_name,
        new_name=clean_name,
        update_source="signature_and_sender",
    )
    return 1


def item_names_match(viewer, selected_name: Any, row_name: Any) -> bool:
    selected_norm = viewer._normalize_item_name(selected_name)
    row_norm = viewer._normalize_item_name(row_name)
    if selected_norm == row_norm:
        return True
    if selected_norm.endswith("s") and selected_norm[:-1] == row_norm:
        return True
    if row_norm.endswith("s") and row_norm[:-1] == selected_norm:
        return True
    return False


def build_drop_log_row_from_entry(viewer, entry: Any, bot_name: str, map_id: int, map_name: str) -> DropLogRow:
    if isinstance(entry, DropLogRow):
        sender_email = viewer._ensure_text(entry.sender_email).strip().lower()
        if not sender_email:
            sender_email = viewer._resolve_account_email_by_character_name(viewer._ensure_text(entry.player_name).strip())
        return DropLogRow(
            timestamp=viewer._ensure_text(entry.timestamp) or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            viewer_bot=viewer._ensure_text(bot_name),
            map_id=max(0, viewer._safe_int(map_id, 0)),
            map_name=viewer._ensure_text(map_name) or "Unknown",
            player_name=viewer._ensure_text(entry.player_name) or "Unknown",
            item_name=viewer._ensure_text(entry.item_name) or "Unknown Item",
            quantity=max(1, viewer._safe_int(entry.quantity, 1)),
            rarity=viewer._normalize_rarity_label(entry.item_name, entry.rarity),
            event_id=viewer._ensure_text(entry.event_id).strip(),
            item_stats=viewer._ensure_text(entry.item_stats).strip(),
            item_id=max(0, viewer._safe_int(entry.item_id, 0)),
            sender_email=sender_email,
        )
    if isinstance(entry, dict):
        player_name = entry.get("player_name", "Unknown")
        item_name = entry.get("item_name", "Unknown Item")
        quantity = entry.get("quantity", 1)
        extra_info = entry.get("extra_info", "Unknown")
        timestamp_override = entry.get("timestamp_override", None)
        event_id = viewer._ensure_text(entry.get("event_id", "")).strip()
        item_stats = viewer._ensure_text(entry.get("item_stats", "")).strip()
        item_id = max(0, viewer._safe_int(entry.get("item_id", 0), 0))
        sender_email = viewer._ensure_text(entry.get("sender_email", "")).strip().lower()
    else:
        player_name = entry[0] if len(entry) > 0 else "Unknown"
        item_name = entry[1] if len(entry) > 1 else "Unknown Item"
        quantity = entry[2] if len(entry) > 2 else 1
        extra_info = entry[3] if len(entry) > 3 else "Unknown"
        timestamp_override = entry[4] if len(entry) > 4 else None
        event_id = viewer._ensure_text(entry[5]).strip() if len(entry) > 5 else ""
        item_stats = viewer._ensure_text(entry[6]).strip() if len(entry) > 6 else ""
        item_id = max(0, viewer._safe_int(entry[7], 0)) if len(entry) > 7 else 0
        sender_email = viewer._ensure_text(entry[8]).strip().lower() if len(entry) > 8 else ""
    if not sender_email:
        sender_email = viewer._resolve_account_email_by_character_name(viewer._ensure_text(player_name).strip())
    if event_id and not item_stats:
        stats_cache_key = viewer._make_stats_cache_key(event_id, sender_email, player_name)
        item_stats = viewer._get_cached_stats_text(viewer.stats_by_event, stats_cache_key)

    timestamp = timestamp_override if timestamp_override else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rarity = viewer._normalize_rarity_label(item_name, extra_info if extra_info else "Unknown")
    qty = max(1, viewer._safe_int(quantity, 1))
    return DropLogRow(
        timestamp=timestamp,
        viewer_bot=viewer._ensure_text(bot_name),
        map_id=max(0, viewer._safe_int(map_id, 0)),
        map_name=viewer._ensure_text(map_name) or "Unknown",
        player_name=viewer._ensure_text(player_name) or "Unknown",
        item_name=viewer._ensure_text(item_name) or "Unknown Item",
        quantity=qty,
        rarity=rarity,
        event_id=event_id,
        item_stats=item_stats,
        item_id=item_id,
        sender_email=sender_email,
    )
