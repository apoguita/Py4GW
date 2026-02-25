from __future__ import annotations

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_delta_filter import (
    filter_candidate_events_by_model_delta,
)


def test_keeps_new_item_id_when_model_net_delta_is_zero():
    events = [
        {
            "reason": "new_slot",
            "model_id": 1234,
            "item_id": 777,
            "qty": 1,
        }
    ]

    filtered, suppressed = filter_candidate_events_by_model_delta(
        candidate_events=events,
        prev_model_qty={1234: 10},
        current_model_qty={1234: 10},
        prev_item_ids={10, 11, 12},
    )

    assert suppressed == 0
    assert len(filtered) == 1
    assert int(filtered[0]["item_id"]) == 777


def test_suppresses_existing_item_id_when_model_net_delta_is_zero():
    events = [
        {
            "reason": "stack_increase",
            "model_id": 1234,
            "item_id": 42,
            "qty": 1,
        }
    ]

    filtered, suppressed = filter_candidate_events_by_model_delta(
        candidate_events=events,
        prev_model_qty={1234: 10},
        current_model_qty={1234: 10},
        prev_item_ids={42},
    )

    assert suppressed == 1
    assert filtered == []


def test_clamps_existing_item_qty_to_remaining_model_delta():
    events = [
        {
            "reason": "stack_increase",
            "model_id": 9001,
            "item_id": 7,
            "qty": 5,
        }
    ]

    filtered, suppressed = filter_candidate_events_by_model_delta(
        candidate_events=events,
        prev_model_qty={9001: 3},
        current_model_qty={9001: 5},
        prev_item_ids={7},
    )

    assert suppressed == 0
    assert len(filtered) == 1
    assert int(filtered[0]["qty"]) == 2

