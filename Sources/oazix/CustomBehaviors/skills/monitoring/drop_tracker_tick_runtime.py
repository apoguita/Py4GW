import sys

from Py4GWCoreLib import Py4GW, Routines

from Sources.oazix.CustomBehaviors.primitives.helpers.map_instance_helper import (
    classify_map_instance_transition,
    read_current_map_instance,
)

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _sender_runtime_attr(sender, name: str, fallback):
    try:
        module = sys.modules.get(sender.__class__.__module__)
    except EXPECTED_RUNTIME_ERRORS:
        module = None
    if module is not None and hasattr(module, name):
        return getattr(module, name)
    return fallback


def run_sender_tick(sender) -> None:
    if not sender.enabled:
        return
    try:
        if not Routines.Checks.Map.MapValid():
            sender._begin_new_session("map_invalid", 0, 0)
            return
        read_current_map_instance_fn = _sender_runtime_attr(sender, "read_current_map_instance", read_current_map_instance)
        classify_transition_fn = _sender_runtime_attr(
            sender,
            "classify_map_instance_transition",
            classify_map_instance_transition,
        )
        current_map_id, current_instance_uptime_ms = read_current_map_instance_fn()
        if current_map_id > 0:
            if int(sender.last_seen_map_id) <= 0:
                sender.last_seen_map_id = current_map_id
                sender.last_seen_instance_uptime_ms = current_instance_uptime_ms
            else:
                transition_reason = classify_transition_fn(
                    previous_map_id=sender.last_seen_map_id,
                    previous_instance_uptime_ms=sender.last_seen_instance_uptime_ms,
                    current_map_id=current_map_id,
                    current_instance_uptime_ms=current_instance_uptime_ms,
                )
                if transition_reason:
                    sender._begin_new_session(transition_reason, current_map_id, current_instance_uptime_ms)
                    return
            sender.last_seen_instance_uptime_ms = current_instance_uptime_ms
        if sender.config_poll_timer.IsExpired():
            sender.config_poll_timer.Reset()
            sender._load_runtime_config()
        if sender.debug_enabled and sender.debug_timer.IsExpired():
            sender.debug_timer.Reset()
            Py4GW.Console.Log(
                "DropTrackerSender",
                (
                    "active "
                    f"snapshot_size={len(sender.last_inventory_snapshot)} "
                    f"items={sender.last_snapshot_total} "
                    f"ready={sender.last_snapshot_ready} "
                    f"not_ready={sender.last_snapshot_not_ready} "
                    f"sent={sender.last_sent_count} "
                    f"candidates={sender.last_candidate_count} "
                    f"enqueued={sender.last_enqueued_count} "
                    f"queued={len(sender.outbox_queue)} "
                    f"acks={sender.last_ack_count} "
                    f"pending_names={len(sender.pending_slot_deltas)} "
                    f"world_live={int(sender.last_world_item_scan_count)} "
                    f"world_recent={len(sender.recent_world_item_disappearances)} "
                    f"name_refresh={len(sender.pending_name_refresh_by_event)} "
                    f"role={'leader' if sender._is_party_leader_client() else 'follower'} "
                    f"warmed={sender.is_warmed_up} "
                    f"proc_ms={sender.last_process_duration_ms:.2f}"
                ),
                Py4GW.Console.MessageType.Info,
            )
        if sender.inventory_poll_timer.IsExpired():
            if sender.world_item_poll_timer.IsExpired():
                sender.world_item_poll_timer.Reset()
                sender._poll_world_item_disappearances()
            sender.inventory_poll_timer.Reset()
            sender._process_inventory_deltas()
        elif sender.world_item_poll_timer.IsExpired():
            sender.world_item_poll_timer.Reset()
            sender._poll_world_item_disappearances()
        if sender.outbox_queue:
            sender._flush_outbox()
        if sender.pending_name_refresh_by_event:
            sender._process_pending_name_refreshes()
    except EXPECTED_RUNTIME_ERRORS:
        return
