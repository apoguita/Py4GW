from __future__ import annotations

from typing import Any

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow


def parse_runtime_row(row: Any) -> DropLogRow | None:
    if not isinstance(row, list):
        return None
    return DropLogRow.from_runtime_row(row)


def set_runtime_row_item_stats(row: Any, item_stats: str) -> None:
    if not isinstance(row, list):
        return
    while len(row) <= 9:
        row.append("")
    row[9] = str(item_stats or "").strip()


def set_runtime_row_item_id(row: Any, item_id: int) -> None:
    if not isinstance(row, list):
        return
    while len(row) <= 10:
        row.append("")
    row[10] = str(max(0, int(item_id)))


def extract_runtime_row_event_id(row: Any) -> str:
    parsed = parse_runtime_row(row)
    return str(parsed.event_id or "").strip() if parsed else ""


def extract_runtime_row_item_stats(row: Any) -> str:
    parsed = parse_runtime_row(row)
    return str(parsed.item_stats or "").strip() if parsed else ""


def extract_runtime_row_item_id(row: Any) -> int:
    parsed = parse_runtime_row(row)
    return max(0, int(parsed.item_id)) if parsed else 0


def extract_runtime_row_sender_email(row: Any) -> str:
    parsed = parse_runtime_row(row)
    return str(parsed.sender_email or "").strip().lower() if parsed else ""


def update_rows_item_stats_by_event(rows: list[Any], event_id: str, item_stats: str) -> int:
    event_key = str(event_id or "").strip()
    if not event_key:
        return 0
    updated = 0
    for row in rows:
        if extract_runtime_row_event_id(row) != event_key:
            continue
        set_runtime_row_item_stats(row, item_stats)
        updated += 1
    return updated


def update_rows_item_stats_by_event_and_player(
    rows: list[Any],
    event_id: str,
    player_name: str,
    item_stats: str,
) -> int:
    event_key = str(event_id or "").strip()
    player_key = str(player_name or "").strip().lower()
    if not event_key:
        return 0
    if not player_key:
        # When player identity is unknown, only update a single unambiguous event row.
        # This avoids cross-player overwrite if different rows share the same event_id.
        matched_rows: list[Any] = []
        for row in rows:
            if extract_runtime_row_event_id(row) != event_key:
                continue
            matched_rows.append(row)
            if len(matched_rows) > 1:
                return 0
        if len(matched_rows) != 1:
            return 0
        set_runtime_row_item_stats(matched_rows[0], item_stats)
        return 1
    updated = 0
    for row in rows:
        parsed = parse_runtime_row(row)
        if parsed is None:
            continue
        row_event = str(parsed.event_id or "").strip()
        row_player = str(parsed.player_name or "").strip().lower()
        if row_event != event_key or row_player != player_key:
            continue
        set_runtime_row_item_stats(row, item_stats)
        updated += 1
    return updated


def update_rows_item_stats_by_event_and_sender(
    rows: list[Any],
    event_id: str,
    sender_email: str,
    item_stats: str,
    player_name: str = "",
) -> int:
    event_key = str(event_id or "").strip()
    sender_key = str(sender_email or "").strip().lower()
    if not event_key:
        return 0
    if sender_key:
        updated = 0
        for row in rows:
            parsed = parse_runtime_row(row)
            if parsed is None:
                continue
            row_event = str(parsed.event_id or "").strip()
            row_sender = str(parsed.sender_email or "").strip().lower()
            if row_event != event_key or row_sender != sender_key:
                continue
            set_runtime_row_item_stats(row, item_stats)
            updated += 1
        if updated > 0:
            return updated
    return update_rows_item_stats_by_event_and_player(rows, event_id, player_name, item_stats)
