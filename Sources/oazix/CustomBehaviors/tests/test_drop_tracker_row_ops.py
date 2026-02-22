from __future__ import annotations

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_event_id
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_item_id
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_item_stats
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import parse_runtime_row
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import set_runtime_row_item_id
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import set_runtime_row_item_stats
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import update_rows_item_stats_by_event


def _sample_row(event_id: str = "ev-1", stats: str = "", item_id: int = 0) -> list[str]:
    return DropLogRow(
        timestamp="2026-02-22 15:47:00",
        viewer_bot="Leader",
        map_id=248,
        map_name="Ice Caves",
        player_name="Mesmer Tri",
        item_name="Holy Staff",
        quantity=1,
        rarity="White",
        event_id=event_id,
        item_stats=stats,
        item_id=item_id,
    ).to_runtime_row()


def test_parse_runtime_row_roundtrip():
    row = _sample_row(event_id="ev-rt", stats="line", item_id=487)
    parsed = parse_runtime_row(row)
    assert parsed is not None
    assert parsed.item_name == "Holy Staff"
    assert parsed.rarity == "White"
    assert parsed.event_id == "ev-rt"
    assert parsed.item_stats == "line"
    assert parsed.item_id == 487


def test_extract_runtime_fields():
    row = _sample_row(event_id="ev-x", stats="mods", item_id=99)
    assert extract_runtime_row_event_id(row) == "ev-x"
    assert extract_runtime_row_item_stats(row) == "mods"
    assert extract_runtime_row_item_id(row) == 99


def test_set_runtime_fields_extend_short_rows():
    row = ["2026-02-22 15:47:00", "Leader", "248", "Ice Caves", "Mesmer Tri", "Holy Staff", "1", "White"]
    set_runtime_row_item_stats(row, "line-a")
    set_runtime_row_item_id(row, 123)
    assert len(row) >= 11
    assert row[9] == "line-a"
    assert row[10] == "123"


def test_update_rows_item_stats_by_event():
    rows = [_sample_row(event_id="ev-a"), _sample_row(event_id="ev-b"), _sample_row(event_id="ev-a")]
    updated = update_rows_item_stats_by_event(rows, "ev-a", "new-stats")
    assert updated == 2
    assert extract_runtime_row_item_stats(rows[0]) == "new-stats"
    assert extract_runtime_row_item_stats(rows[1]) == ""
    assert extract_runtime_row_item_stats(rows[2]) == "new-stats"


def test_row_ops_ignore_non_list_rows_and_empty_event():
    assert parse_runtime_row("not-a-row") is None
    assert extract_runtime_row_event_id("not-a-row") == ""
    assert extract_runtime_row_item_stats("not-a-row") == ""
    assert extract_runtime_row_item_id("not-a-row") == 0

    row = ["2026-02-22 15:47:00", "Leader", "248", "Ice Caves", "Mesmer Tri", "Holy Staff", "1", "White"]
    set_runtime_row_item_stats("not-a-row", "ignored")
    set_runtime_row_item_id("not-a-row", 77)
    assert update_rows_item_stats_by_event([row], "", "ignored") == 0
