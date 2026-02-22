from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import parse_drop_log_text
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import parse_drop_log_file
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import render_drop_log_csv
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store import append_drop_log_rows
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow


def test_parse_old_csv_format_back_compat():
    csv_text = "\n".join(
        [
            "Timestamp,ViewerBot,MapID,Player,ItemName,Quantity,Rarity",
            "2026-02-22 12:00:00,BotA,55,Mesmer Tri,Holy Staff,1,White",
        ]
    )
    rows = parse_drop_log_text(csv_text, map_name_resolver=lambda map_id: f"Map#{map_id}")
    assert len(rows) == 1
    row = rows[0]
    assert row.map_name == "Map#55"
    assert row.player_name == "Mesmer Tri"
    assert row.item_name == "Holy Staff"
    assert row.quantity == 1


def test_parse_new_csv_format_with_event_fields():
    csv_text = "\n".join(
        [
            "Timestamp,ViewerBot,MapID,MapName,Player,ItemName,Quantity,Rarity,EventID,ItemStats,ItemID",
            "2026-02-22 12:00:01,BotA,248,Temple of the Ages,Mesmer Tri,Holy Staff,1,White,85e699300008,\"Holy Staff\\nValue: 224 gold\",487",
        ]
    )
    rows = parse_drop_log_text(csv_text, map_name_resolver=lambda _: "unused")
    assert len(rows) == 1
    row = rows[0]
    assert row.event_id == "85e699300008"
    assert row.item_id == 487
    assert "Value: 224 gold" in row.item_stats


def test_append_and_parse_roundtrip():
    expected = DropLogRow(
        timestamp="2026-02-22 13:00:00",
        viewer_bot="BotA",
        map_id=200,
        map_name="Ascalon",
        player_name="Mesmer Tri",
        item_name="Holy Staff",
        quantity=2,
        rarity="White",
        event_id="abc123",
        item_stats="Holy Staff",
        item_id=321,
    )
    csv_text = render_drop_log_csv([expected])
    rows = parse_drop_log_text(csv_text, map_name_resolver=lambda _: "unused")
    assert len(rows) == 1
    got = rows[0]
    assert got.to_runtime_row() == expected.to_runtime_row()


def _make_local_temp_dir() -> Path:
    root = Path(".tmp") / "pytest-local"
    root.mkdir(parents=True, exist_ok=True)
    temp_dir = root / f"drop-tracker-{uuid.uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=False)
    return temp_dir


def test_parse_drop_log_file_roundtrip():
    expected = DropLogRow(
        timestamp="2026-02-22 13:05:00",
        viewer_bot="BotB",
        map_id=248,
        map_name="Temple of the Ages",
        player_name="Mesmer Tri",
        item_name="Holy Staff",
        quantity=1,
        rarity="White",
        event_id="ev-file",
        item_stats="Value: 224 gold",
        item_id=487,
    )
    temp_dir = _make_local_temp_dir()
    try:
        csv_text = render_drop_log_csv([expected])
        file_path = temp_dir / "drops.csv"
        file_path.write_text(csv_text, encoding="utf-8")
        parsed = parse_drop_log_file(str(file_path))
        assert len(parsed) == 1
        assert parsed[0].to_runtime_row() == expected.to_runtime_row()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_append_drop_log_rows_writes_header_once():
    temp_dir = _make_local_temp_dir()
    file_path = temp_dir / "append_log.csv"
    row_a = DropLogRow(
        timestamp="2026-02-22 13:06:00",
        viewer_bot="BotA",
        map_id=248,
        map_name="Temple of the Ages",
        player_name="PlayerA",
        item_name="ItemA",
        quantity=1,
        rarity="White",
        event_id="ev-a",
        item_stats="",
        item_id=1,
    )
    row_b = DropLogRow(
        timestamp="2026-02-22 13:07:00",
        viewer_bot="BotB",
        map_id=249,
        map_name="Ascalon",
        player_name="PlayerB",
        item_name="ItemB",
        quantity=2,
        rarity="Blue",
        event_id="ev-b",
        item_stats="line",
        item_id=2,
    )
    try:
        append_drop_log_rows(str(file_path), [row_a])
        append_drop_log_rows(str(file_path), [row_b])
        append_drop_log_rows(str(file_path), [])
        lines = file_path.read_text(encoding="utf-8").splitlines()
        assert lines[0].startswith("Timestamp,ViewerBot,MapID,MapName,Player")
        assert len([line for line in lines if line.startswith("Timestamp,ViewerBot,MapID,MapName,Player")]) == 1
        assert len(lines) == 3
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
