import os
import time

from Py4GWCoreLib import Map, Player, Py4GW

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import append_drop_log_rows
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_runtime_store import append_drop_rows_to_state

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


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
        viewer.last_read_time = os.path.getmtime(viewer.log_path) if os.path.exists(viewer.log_path) else time.time()
    except EXPECTED_RUNTIME_ERRORS as e:
        Py4GW.Console.Log("DropViewer", f"Log Error: {e}", Py4GW.Console.MessageType.Warning)
