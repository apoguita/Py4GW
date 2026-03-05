import os
import time

from Py4GWCoreLib import Map, Player, Py4GW

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import append_drop_log_rows
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import parse_drop_log_file
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import replace_drop_log_row
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_runtime_store import build_state_from_parsed_rows
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_runtime_store import append_drop_rows_to_state
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def rebuild_live_state_from_log(viewer) -> None:
    parsed_rows = parse_drop_log_file(viewer.log_path, map_name_resolver=Map.GetMapName)
    temp_drops, temp_agg, total, temp_stats_by_event = build_state_from_parsed_rows(
        parsed_rows=parsed_rows,
        ensure_text_fn=viewer._ensure_text,
        make_stats_cache_key_fn=viewer._make_stats_cache_key,
        canonical_name_fn=viewer._canonical_agg_item_name,
    )
    viewer.raw_drops = temp_drops
    viewer.aggregated_drops = temp_agg
    viewer.total_drops = int(total)
    viewer.stats_by_event = temp_stats_by_event


def log_drop_to_file(
    viewer,
    player_name,
    item_name,
    quantity,
    extra_info,
    timestamp_override=None,
    event_id="",
    item_stats="",
    item_id=0,
    sender_email="",
):
    viewer._log_drops_batch(
        [
            {
                "player_name": player_name,
                "item_name": item_name,
                "quantity": quantity,
                "extra_info": extra_info,
                "timestamp_override": timestamp_override,
                "event_id": event_id,
                "item_stats": item_stats,
                "item_id": item_id,
                "sender_email": sender_email,
            }
        ]
    )


def log_drops_batch(viewer, entries) -> None:
    try:
        bot_name = Player.GetName()
        map_id = Map.GetMapID()
        map_name = Map.GetMapName(map_id)
        os.makedirs(os.path.dirname(viewer.log_path), exist_ok=True)
        drop_rows = []
        for entry in entries:
            drop_rows.append(viewer._build_drop_log_row_from_entry(entry, bot_name, map_id, map_name))
        append_drop_log_rows(viewer.log_path, drop_rows)
        try:
            temp_drops, temp_agg, total, temp_stats_by_event = append_drop_rows_to_state(
                drop_rows=drop_rows,
                raw_drops=viewer.raw_drops,
                aggregated_drops=viewer.aggregated_drops,
                total_drops=viewer.total_drops,
                stats_by_event=viewer.stats_by_event,
                ensure_text_fn=viewer._ensure_text,
                make_stats_cache_key_fn=viewer._make_stats_cache_key,
                canonical_name_fn=viewer._canonical_agg_item_name,
            )
            viewer.raw_drops = temp_drops
            viewer.aggregated_drops = temp_agg
            viewer.total_drops = int(total)
            viewer.stats_by_event = temp_stats_by_event
            if drop_rows and (not isinstance(viewer.raw_drops, list) or len(viewer.raw_drops) <= 0 or int(viewer.total_drops) <= 0):
                rebuild_live_state_from_log(viewer)
        except EXPECTED_RUNTIME_ERRORS:
            rebuild_live_state_from_log(viewer)
        viewer.last_read_time = os.path.getmtime(viewer.log_path) if os.path.exists(viewer.log_path) else time.time()
    except EXPECTED_RUNTIME_ERRORS as e:
        Py4GW.Console.Log("DropViewer", f"Log Error: {e}", Py4GW.Console.MessageType.Warning)


def persist_runtime_row_to_file(viewer, row) -> int:
    try:
        if not isinstance(row, list):
            return 0
        log_path = viewer._ensure_text(getattr(viewer, "log_path", "")).strip()
        if not log_path:
            return 0
        parsed_row = DropLogRow.from_runtime_row(row)
        if parsed_row is None or not viewer._ensure_text(parsed_row.event_id).strip():
            return 0
        updated = int(replace_drop_log_row(log_path, parsed_row))
        if updated > 0:
            viewer.last_read_time = os.path.getmtime(log_path) if os.path.exists(log_path) else time.time()
        return updated
    except EXPECTED_RUNTIME_ERRORS:
        return 0
