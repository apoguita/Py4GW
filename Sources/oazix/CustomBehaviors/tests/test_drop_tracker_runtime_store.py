from __future__ import annotations

import pytest

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import parse_runtime_row
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_runtime_store import append_drop_rows_to_state
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_runtime_store import build_state_from_parsed_rows
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_runtime_store import merge_parsed_rows_into_state
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_runtime_store import rebuild_aggregates_from_runtime_rows


def _text(value):
    return "" if value is None else str(value)


def _stats_key(event_id: str, sender_email: str, player_name: str) -> str:
    sender = str(sender_email or "").strip().lower()
    player = str(player_name or "").strip().lower()
    ident = sender if sender else player
    return f"{ident}:{event_id}" if ident and event_id else ""


def _canonical_name(item_name, _rarity, _agg):
    return str(item_name or "").strip() or "Unknown Item"


def test_build_state_from_parsed_rows_builds_all_indexes():
    parsed_rows = [
        DropLogRow(
            timestamp="2026-01-01 10:00:00",
            viewer_bot="Leader",
            map_id=1,
            map_name="Map",
            player_name="Follower",
            item_name="Ruby",
            quantity=2,
            rarity="Gold",
            event_id="ev-1",
            item_stats="mods",
            item_id=100,
            sender_email="follower@test",
        )
    ]
    raw, agg, total, stats = build_state_from_parsed_rows(
        parsed_rows=parsed_rows,
        ensure_text_fn=_text,
        make_stats_cache_key_fn=_stats_key,
        canonical_name_fn=_canonical_name,
    )
    assert total == 2
    assert len(raw) == 1
    assert agg[("Ruby", "Gold")]["Quantity"] == 2
    assert agg[("Ruby", "Gold")]["Count"] == 1
    assert stats["follower@test:ev-1"] == "mods"


def test_merge_parsed_rows_into_state_does_not_mutate_source_aggregates():
    initial_raw = [
        DropLogRow(
            timestamp="2026-01-01 10:00:00",
            viewer_bot="Leader",
            map_id=1,
            map_name="Map",
            player_name="Follower",
            item_name="Ruby",
            quantity=1,
            rarity="Gold",
        ).to_runtime_row()
    ]
    initial_agg = {("Ruby", "Gold"): {"Quantity": 1, "Count": 1}}
    parsed_rows = [
        DropLogRow(
            timestamp="2026-01-01 10:00:01",
            viewer_bot="Leader",
            map_id=1,
            map_name="Map",
            player_name="Follower",
            item_name="Ruby",
            quantity=3,
            rarity="Gold",
        )
    ]
    merged_raw, merged_agg, merged_total, _ = merge_parsed_rows_into_state(
        parsed_rows=parsed_rows,
        raw_drops=initial_raw,
        aggregated_drops=initial_agg,
        total_drops=1,
        stats_by_event={},
        ensure_text_fn=_text,
        make_stats_cache_key_fn=_stats_key,
        canonical_name_fn=_canonical_name,
    )
    assert len(merged_raw) == 2
    assert merged_total == 4
    assert merged_agg[("Ruby", "Gold")]["Quantity"] == 4
    assert initial_agg[("Ruby", "Gold")]["Quantity"] == 1


def test_append_drop_rows_to_state_and_rebuild_aggregates_are_consistent():
    base_raw = []
    base_agg = {}
    base_stats = {}
    rows = [
        DropLogRow(
            timestamp="2026-01-01 10:00:00",
            viewer_bot="Leader",
            map_id=1,
            map_name="Map",
            player_name="Follower",
            item_name="Sapphire",
            quantity=1,
            rarity="Blue",
            event_id="ev-2",
            item_stats="line",
            sender_email="follower@test",
        ),
        DropLogRow(
            timestamp="2026-01-01 10:00:01",
            viewer_bot="Leader",
            map_id=1,
            map_name="Map",
            player_name="Follower",
            item_name="Sapphire",
            quantity=2,
            rarity="Blue",
        ),
    ]
    raw, agg, total, stats = append_drop_rows_to_state(
        drop_rows=rows,
        raw_drops=base_raw,
        aggregated_drops=base_agg,
        total_drops=0,
        stats_by_event=base_stats,
        ensure_text_fn=_text,
        make_stats_cache_key_fn=_stats_key,
        canonical_name_fn=_canonical_name,
    )
    assert raw is base_raw
    assert agg is base_agg
    assert stats is base_stats
    rebuilt_agg, rebuilt_total = rebuild_aggregates_from_runtime_rows(
        raw_drops=raw,
        parse_runtime_row_fn=parse_runtime_row,
        canonical_name_fn=_canonical_name,
        safe_int_fn=lambda value, default: int(value) if str(value).strip() else int(default),
        ensure_text_fn=_text,
    )
    assert total == 3
    assert agg[("Sapphire", "Blue")]["Quantity"] == 3
    assert rebuilt_total == total
    assert rebuilt_agg == agg
    assert stats["follower@test:ev-2"] == "line"


def test_append_drop_rows_to_state_rejects_invalid_container_types():
    row = DropLogRow(
        timestamp="2026-01-01 10:00:00",
        viewer_bot="Leader",
        map_id=1,
        map_name="Map",
        player_name="Follower",
        item_name="Sapphire",
        quantity=1,
        rarity="Blue",
    )
    with pytest.raises(TypeError):
        append_drop_rows_to_state(
            drop_rows=[row],
            raw_drops=(),  # type: ignore[arg-type]
            aggregated_drops={},
            total_drops=0,
            stats_by_event={},
            ensure_text_fn=_text,
            make_stats_cache_key_fn=_stats_key,
            canonical_name_fn=_canonical_name,
        )
