from __future__ import annotations

import csv
import io
import os
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


def _is_header_row(row: list[str]) -> bool:
    if not isinstance(row, list) or not row:
        return False
    lowered = {str(cell or "").strip().lower() for cell in row}
    required = {"timestamp", "viewerbot", "mapid", "itemname", "quantity", "rarity"}
    return required.issubset(lowered)


def _is_int_text(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if text[0] in ("+", "-"):
        text = text[1:]
    return text.isdigit()


def _infer_has_map_name(first_data_row: list[str]) -> bool:
    # Legacy rows without MapName are 7 columns:
    # Timestamp,ViewerBot,MapID,Player,ItemName,Quantity,Rarity,(...)
    # Current rows with MapName are 8+ columns:
    # Timestamp,ViewerBot,MapID,MapName,Player,ItemName,Quantity,Rarity,(...)
    if not isinstance(first_data_row, list):
        return True
    if len(first_data_row) < 7:
        return True
    if len(first_data_row) == 7:
        return False
    # Heuristic: Quantity sits at index 6 with MapName schema, index 5 otherwise.
    qty_at_6 = _is_int_text(first_data_row[6]) if len(first_data_row) > 6 else False
    qty_at_5 = _is_int_text(first_data_row[5]) if len(first_data_row) > 5 else False
    if qty_at_6 and not qty_at_5:
        return True
    if qty_at_5 and not qty_at_6:
        return False
    return len(first_data_row) >= 8


def _effective_optional_indices(
    csv_row: list[str],
    has_map_name: bool,
    event_idx: int,
    stats_idx: int,
    item_id_idx: int,
    sender_email_idx: int,
) -> tuple[int, int, int, int]:
    if has_map_name:
        default_event = 8
    else:
        default_event = 7
    default_stats = default_event + 1
    default_item_id = default_event + 2
    default_sender = default_event + 3

    effective_event_idx = int(event_idx)
    effective_stats_idx = int(stats_idx)
    effective_item_id_idx = int(item_id_idx)
    effective_sender_idx = int(sender_email_idx)

    if effective_event_idx < 0 and len(csv_row) > default_event:
        effective_event_idx = default_event
    if effective_stats_idx < 0 and len(csv_row) > default_stats:
        effective_stats_idx = default_stats
    if effective_item_id_idx < 0 and len(csv_row) > default_item_id:
        effective_item_id_idx = default_item_id
    if effective_sender_idx < 0 and len(csv_row) > default_sender:
        effective_sender_idx = default_sender
    return effective_event_idx, effective_stats_idx, effective_item_id_idx, effective_sender_idx


def parse_drop_log_reader(
    reader: csv.reader,
    map_name_resolver: Callable[[int], str] | None = None,
) -> list[DropLogRow]:
    parsed_rows: list[DropLogRow] = []
    first_row = next(reader, None)
    if first_row is None:
        return parsed_rows

    if _is_header_row(first_row):
        header = list(first_row)
        first_data_row = None
    else:
        header = []
        first_data_row = list(first_row) if isinstance(first_row, list) else None

    has_map_name = ("MapName" in header) if header else _infer_has_map_name(first_data_row or [])
    has_event_id = "EventID" in header
    has_item_stats = "ItemStats" in header
    has_item_id = "ItemID" in header
    has_sender_email = "SenderEmail" in header
    configured_event_idx = header.index("EventID") if has_event_id else -1
    configured_stats_idx = header.index("ItemStats") if has_item_stats else -1
    configured_item_id_idx = header.index("ItemID") if has_item_id else -1
    configured_sender_email_idx = header.index("SenderEmail") if has_sender_email else -1

    if first_data_row is None:
        row_iter = reader
    else:
        def _iter_rows():
            yield first_data_row
            for next_row in reader:
                yield next_row
        row_iter = _iter_rows()

    for csv_row in row_iter:
        fallback_map_name = "Unknown"
        if not has_map_name and map_name_resolver is not None:
            try:
                fallback_map_name = str(map_name_resolver(int(csv_row[2])) or "Unknown")
            except (IndexError, TypeError, ValueError):
                fallback_map_name = "Unknown"

        event_idx, stats_idx, item_id_idx, sender_email_idx = _effective_optional_indices(
            csv_row=list(csv_row),
            has_map_name=bool(has_map_name),
            event_idx=configured_event_idx,
            stats_idx=configured_stats_idx,
            item_id_idx=configured_item_id_idx,
            sender_email_idx=configured_sender_email_idx,
        )
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
    try:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            with open(filepath, mode="r", encoding="utf-8") as f_read:
                existing_reader = csv.reader(f_read)
                existing_header = next(existing_reader, [])
            if _is_header_row(existing_header):
                if "EventID" not in existing_header or "ItemStats" not in existing_header or "ItemID" not in existing_header or "SenderEmail" not in existing_header:
                    existing_rows = parse_drop_log_file(filepath)
                    with open(filepath, mode="w", newline="", encoding="utf-8") as f_write:
                        writer = csv.writer(f_write)
                        writer.writerow(DROP_LOG_HEADER)
                        for existing in existing_rows:
                            writer.writerow(existing.to_csv_row())
    except OSError:
        # Best-effort header upgrade; append path still attempts to proceed.
        pass

    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(DROP_LOG_HEADER)
        for row in rows:
            writer.writerow(row.to_csv_row())
