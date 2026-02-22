from __future__ import annotations

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_event_id
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_item_id
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_sender_email
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_item_stats
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import parse_runtime_row
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import set_runtime_row_item_id
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import set_runtime_row_item_stats
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import update_rows_item_stats_by_event
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import update_rows_item_stats_by_event_and_sender
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import update_rows_item_stats_by_event_and_player


def _sample_row(event_id: str = "ev-1", stats: str = "", item_id: int = 0, sender_email: str = "") -> list[str]:
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
        sender_email=sender_email,
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
    row = _sample_row(event_id="ev-x", stats="mods", item_id=99, sender_email="hero@test")
    assert extract_runtime_row_event_id(row) == "ev-x"
    assert extract_runtime_row_item_stats(row) == "mods"
    assert extract_runtime_row_item_id(row) == 99
    assert extract_runtime_row_sender_email(row) == "hero@test"


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


def test_update_rows_item_stats_by_event_and_player():
    row_a = DropLogRow(
        timestamp="2026-02-22 15:47:00",
        viewer_bot="Leader",
        map_id=248,
        map_name="Ice Caves",
        player_name="Mesmer Tri",
        item_name="Holy Staff",
        quantity=1,
        rarity="White",
        event_id="ev-a",
        item_stats="",
        item_id=1,
    ).to_runtime_row()
    row_b = DropLogRow(
        timestamp="2026-02-22 15:47:01",
        viewer_bot="Leader",
        map_id=248,
        map_name="Ice Caves",
        player_name="Ranger One",
        item_name="Holy Staff",
        quantity=1,
        rarity="White",
        event_id="ev-a",
        item_stats="",
        item_id=2,
    ).to_runtime_row()
    rows = [row_a, row_b]
    updated = update_rows_item_stats_by_event_and_player(rows, "ev-a", "Mesmer Tri", "stats-a")
    assert updated == 1
    assert extract_runtime_row_item_stats(row_a) == "stats-a"
    assert extract_runtime_row_item_stats(row_b) == ""


def test_update_rows_item_stats_by_event_and_sender_prefers_sender_match():
    row_a = _sample_row(event_id="ev-s", sender_email="a@test")
    row_b = _sample_row(event_id="ev-s", sender_email="b@test")
    rows = [row_a, row_b]
    updated = update_rows_item_stats_by_event_and_sender(rows, "ev-s", "b@test", "sender-b")
    assert updated == 1
    assert extract_runtime_row_item_stats(row_a) == ""
    assert extract_runtime_row_item_stats(row_b) == "sender-b"


def test_update_rows_item_stats_by_event_and_player_requires_unambiguous_when_player_unknown():
    row_a = _sample_row(event_id="ev-z")
    row_b = _sample_row(event_id="ev-z")
    rows = [row_a, row_b]
    updated = update_rows_item_stats_by_event_and_player(rows, "ev-z", "", "stats-z")
    assert updated == 0
    assert extract_runtime_row_item_stats(row_a) == ""
    assert extract_runtime_row_item_stats(row_b) == ""

    single = [_sample_row(event_id="ev-single")]
    updated_single = update_rows_item_stats_by_event_and_player(single, "ev-single", "", "single-stats")
    assert updated_single == 1
    assert extract_runtime_row_item_stats(single[0]) == "single-stats"


def test_row_ops_ignore_non_list_rows_and_empty_event():
    assert parse_runtime_row("not-a-row") is None
    assert extract_runtime_row_event_id("not-a-row") == ""
    assert extract_runtime_row_item_stats("not-a-row") == ""
    assert extract_runtime_row_item_id("not-a-row") == 0

    row = ["2026-02-22 15:47:00", "Leader", "248", "Ice Caves", "Mesmer Tri", "Holy Staff", "1", "White"]
    set_runtime_row_item_stats("not-a-row", "ignored")
    set_runtime_row_item_id("not-a-row", 77)
    assert update_rows_item_stats_by_event([row], "", "ignored") == 0
