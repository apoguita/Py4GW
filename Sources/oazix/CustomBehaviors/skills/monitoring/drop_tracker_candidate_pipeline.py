from typing import Any

from Py4GWCoreLib import Py4GW

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_delta_filter import (
    filter_candidate_events_by_model_delta,
)

WORLD_CONFIRMATION_FALLBACK_REASONS = frozenset(
    {
        "new_slot",
        "pending_same_slot_name_ready",
        "pending_itemid_name_ready",
        "stack_increase",
    }
)


def _slot_tuple(event: dict[str, Any]) -> tuple[int, int]:
    slot_key = event.get("slot_key")
    bag_id = int(slot_key[0]) if isinstance(slot_key, tuple) and len(slot_key) > 0 else 0
    slot_id = int(slot_key[1]) if isinstance(slot_key, tuple) and len(slot_key) > 1 else 0
    return bag_id, slot_id


def _format_candidate_event(event: dict[str, Any]) -> str:
    bag_id, slot_id = _slot_tuple(event)
    return (
        f"reason={event.get('reason', 'delta')} "
        f"item='{event.get('name', 'Unknown Item')}' qty={int(event.get('qty', 1))} "
        f"rarity={event.get('rarity', 'Unknown')} "
        f"item_id={int(event.get('item_id', 0))} model_id={int(event.get('model_id', 0))} "
        f"slot={bag_id}:{slot_id}"
    )


def _allow_world_confirmation_fallback(
    sender,
    event: dict[str, Any],
    prev_item_ids: set[int],
) -> bool:
    reason = str(event.get("reason", "") or "").strip()
    if reason not in WORLD_CONFIRMATION_FALLBACK_REASONS:
        return False
    event_item_id = int(event.get("item_id", 0))
    if event_item_id <= 0 or event_item_id in prev_item_ids:
        return False
    if not bool(getattr(sender, "world_item_seen_since_reset", False)):
        return False
    if bool(getattr(sender, "session_startup_pending", False)):
        return False
    if bool(getattr(sender, "carryover_inventory_snapshot", {})):
        return False
    recent_world_count = len(getattr(sender, "recent_world_item_disappearances", []) or [])
    live_world_count = len(getattr(sender, "current_world_item_agents", {}) or {})
    if reason == "stack_increase":
        # Stack deltas can legitimately miss strict world-item matching due batching/races
        # with repeated stack updates. Allow fallback once world scanning is active.
        return bool(recent_world_count > 0 or live_world_count > 0)
    if recent_world_count > 0 or live_world_count > 0:
        return False
    return True


def confirm_candidate_events(
    sender,
    candidate_events: list[dict[str, Any]],
    prev_model_qty: dict[int, int],
    current_model_qty: dict[int, int],
    prev_item_ids: set[int],
    require_world_confirmation: bool = True,
) -> tuple[list[dict[str, Any]], int, list[dict[str, Any]]]:
    confirmed_events, suppressed_by_model_delta = filter_candidate_events_by_model_delta(
        candidate_events=candidate_events,
        prev_model_qty=prev_model_qty,
        current_model_qty=current_model_qty,
        prev_item_ids=prev_item_ids,
    )
    if not bool(require_world_confirmation):
        return confirmed_events, suppressed_by_model_delta, []
    world_confirmed_events: list[dict[str, Any]] = []
    suppressed_world_events: list[dict[str, Any]] = []
    for event in list(confirmed_events):
        if sender._consume_recent_world_item_confirmation(event):
            world_confirmed_events.append(event)
        elif _allow_world_confirmation_fallback(sender, event, prev_item_ids):
            world_confirmed_events.append(event)
            append_live_debug_log = getattr(sender, "_append_live_debug_log", None)
            if callable(append_live_debug_log):
                append_live_debug_log(
                    "candidate_world_confirmation_fallback",
                    _format_candidate_event(event),
                    fallback_reason=str(event.get("reason", "") or "").strip(),
                    event_item_id=int(event.get("item_id", 0)),
                )
        else:
            suppressed_world_events.append(dict(event))
    return world_confirmed_events, suppressed_by_model_delta, suppressed_world_events


def log_candidate_pipeline(
    sender,
    candidate_events: list[dict[str, Any]],
    suppressed_by_model_delta: int,
    suppressed_world_events: list[dict[str, Any]],
) -> None:
    append_live_debug_log = getattr(sender, "_append_live_debug_log", None)
    if callable(append_live_debug_log) and bool(getattr(sender, "live_debug_detailed", True)):
        append_live_debug_log(
            "candidate_pipeline_summary",
            (
                f"confirmed={len(candidate_events)} "
                f"suppressed_model_delta={int(suppressed_by_model_delta)} "
                f"suppressed_world={len(suppressed_world_events)}"
            ),
            dedupe_key="candidate_pipeline_summary",
            dedupe_interval_s=2.0,
            confirmed_count=len(candidate_events),
            suppressed_model_delta=int(suppressed_by_model_delta),
            suppressed_world_count=len(suppressed_world_events),
        )
    if sender.debug_pipeline_logs and suppressed_by_model_delta > 0:
        Py4GW.Console.Log(
            "DropTrackerSender",
            f"SUPPRESSED by model-delta filter: {suppressed_by_model_delta}",
            Py4GW.Console.MessageType.Info,
        )
    if callable(append_live_debug_log) and suppressed_by_model_delta > 0:
        append_live_debug_log(
            "candidate_suppressed_model_delta",
            f"suppressed={int(suppressed_by_model_delta)}",
            suppressed_count=int(suppressed_by_model_delta),
        )
    if sender.debug_pipeline_logs and suppressed_world_events:
        Py4GW.Console.Log(
            "DropTrackerSender",
            f"SUPPRESSED by world-item confirmation: {len(suppressed_world_events)}",
            Py4GW.Console.MessageType.Info,
        )
        if callable(append_live_debug_log):
            append_live_debug_log(
                "candidate_suppressed_world_confirmation",
                f"suppressed={len(suppressed_world_events)}",
                suppressed_events=suppressed_world_events[:8],
                recent_world_count=len(getattr(sender, "recent_world_item_disappearances", []) or []),
            )
        for event in suppressed_world_events[:8]:
            Py4GW.Console.Log(
                "DropTrackerSender",
                (
                    "SUPPRESSED local-delta "
                    + _format_candidate_event(event)
                    + f" recent_world={len(getattr(sender, 'recent_world_item_disappearances', []) or [])}"
                ),
                Py4GW.Console.MessageType.Info,
            )
        if len(suppressed_world_events) > 8:
            Py4GW.Console.Log(
                "DropTrackerSender",
                f"SUPPRESSED local-delta truncated: showing 8/{len(suppressed_world_events)}",
                Py4GW.Console.MessageType.Info,
            )

    if sender.debug_pipeline_logs and candidate_events:
        for event in candidate_events[:20]:
            Py4GW.Console.Log(
                "DropTrackerSender",
                f"CANDIDATE {_format_candidate_event(event)}",
                Py4GW.Console.MessageType.Info,
            )
        if len(candidate_events) > 20:
            Py4GW.Console.Log(
                "DropTrackerSender",
                f"CANDIDATE truncated: showing 20/{len(candidate_events)}",
                Py4GW.Console.MessageType.Info,
            )
    if callable(append_live_debug_log) and candidate_events:
        append_live_debug_log(
            "candidate_confirmed",
            f"candidate_count={len(candidate_events)}",
            candidate_events=candidate_events[:12],
            candidate_count=len(candidate_events),
        )


def log_candidate_reset_trace(sender, candidate_events: list[dict[str, Any]]) -> None:
    if not sender._reset_trace_active() or (not candidate_events and not sender.pending_slot_deltas):
        return
    sender._log_reset_trace(
        (
            f"RESET TRACE delta actor={sender._reset_trace_actor_label()} candidate_count={len(candidate_events)} "
            f"pending_names={len(sender.pending_slot_deltas)}"
        ),
        consume_event=True,
    )
    for event in candidate_events[:8]:
        sender._log_reset_trace(
            (
                f"RESET TRACE candidate actor={sender._reset_trace_actor_label()} "
                + _format_candidate_event(event)
            ),
            consume_event=True,
        )
