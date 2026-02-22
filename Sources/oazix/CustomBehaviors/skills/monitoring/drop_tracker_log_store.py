from __future__ import annotations

import csv
import io
from typing import Callable

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow

DROP_LOG_HEADER = [
    "Timestamp",
    "ViewerBot",
    "MapID",
    "MapName",
    "Player",
    "ItemName",
    "Quantity",
    "Rarity",
    "EventID",
    "ItemStats",
    "ItemID",
    "SenderEmail",
]


def parse_drop_log_reader(
    reader: csv.reader,
    map_name_resolver: Callable[[int], str] | None = None,
) -> list[DropLogRow]:
    parsed_rows: list[DropLogRow] = []
    header = next(reader, None)
    if not isinstance(header, list):
        header = []

    has_map_name = "MapName" in header
    has_event_id = "EventID" in header
    has_item_stats = "ItemStats" in header
    has_item_id = "ItemID" in header
    has_sender_email = "SenderEmail" in header
    event_idx = header.index("EventID") if has_event_id else -1
    stats_idx = header.index("ItemStats") if has_item_stats else -1
    item_id_idx = header.index("ItemID") if has_item_id else -1
    sender_email_idx = header.index("SenderEmail") if has_sender_email else -1

    for csv_row in reader:
        fallback_map_name = "Unknown"
        if not has_map_name and map_name_resolver is not None:
            try:
                fallback_map_name = str(map_name_resolver(int(csv_row[2])) or "Unknown")
            except (IndexError, TypeError, ValueError):
                fallback_map_name = "Unknown"

        parsed = DropLogRow.from_csv_row(
            csv_row,
            has_map_name=has_map_name,
            event_idx=event_idx,
            stats_idx=stats_idx,
            item_id_idx=item_id_idx,
            sender_email_idx=sender_email_idx,
            map_name_fallback=fallback_map_name,
        )
        if parsed is not None:
            parsed_rows.append(parsed)
    return parsed_rows


def parse_drop_log_text(
    csv_text: str,
    map_name_resolver: Callable[[int], str] | None = None,
) -> list[DropLogRow]:
    with io.StringIO(str(csv_text or "")) as stream:
        reader = csv.reader(stream)
        return parse_drop_log_reader(reader, map_name_resolver=map_name_resolver)


def parse_drop_log_file(
    filepath: str,
    map_name_resolver: Callable[[int], str] | None = None,
) -> list[DropLogRow]:
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        return parse_drop_log_reader(reader, map_name_resolver=map_name_resolver)


def render_drop_log_csv(rows: list[DropLogRow]) -> str:
    with io.StringIO() as stream:
        writer = csv.writer(stream)
        writer.writerow(DROP_LOG_HEADER)
        for row in rows:
            writer.writerow(row.to_csv_row())
        return stream.getvalue()


def append_drop_log_rows(filepath: str, rows: list[DropLogRow]) -> None:
    if not rows:
        return
    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(DROP_LOG_HEADER)
        for row in rows:
            writer.writerow(row.to_csv_row())
