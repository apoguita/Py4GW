from __future__ import annotations

from typing import Any


IMMEDIATE_ACQUISITION_REASONS = frozenset(
    {
        "new_slot",
        "slot_replaced",
        "stack_increase",
    }
)


def filter_candidate_events_by_model_delta(
    candidate_events: list[dict[str, Any]],
    prev_model_qty: dict[int, int],
    current_model_qty: dict[int, int],
    prev_item_ids: set[int] | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """
    Limit immediate acquisition events to each model's observed net quantity increase.

    A new item can be picked up and then consumed/moved before the next snapshot
    (identify/salvage/sell routines). When that happens, net model delta can be zero.
    Keep events for truly new item IDs so valid pickups are not dropped.
    """
    model_claimed_qty: dict[int, int] = {}
    filtered_events: list[dict[str, Any]] = []
    suppressed_by_model_delta = 0
    previous_item_ids = {int(v) for v in set(prev_item_ids or set()) if int(v) > 0}

    for event in list(candidate_events or []):
        reason = str(event.get("reason", "delta"))
        model_id = int(event.get("model_id", 0))
        qty = max(1, int(event.get("qty", 1)))
        event_item_id = int(event.get("item_id", 0))

        apply_model_delta_guard = reason in IMMEDIATE_ACQUISITION_REASONS and model_id > 0
        if apply_model_delta_guard and event_item_id > 0 and event_item_id not in previous_item_ids:
            # This is a newly observed item identity this tick. Do not suppress it
            # only because model totals balanced back out within the same interval.
            apply_model_delta_guard = False

        if apply_model_delta_guard:
            model_delta_remaining = (
                int(current_model_qty.get(model_id, 0))
                - int(prev_model_qty.get(model_id, 0))
                - int(model_claimed_qty.get(model_id, 0))
            )
            if model_delta_remaining <= 0:
                suppressed_by_model_delta += 1
                continue

            if qty > model_delta_remaining:
                event = dict(event)
                event["qty"] = int(model_delta_remaining)
                qty = int(model_delta_remaining)

            model_claimed_qty[model_id] = int(model_claimed_qty.get(model_id, 0)) + int(qty)

        filtered_events.append(event)

    return filtered_events, suppressed_by_model_delta

