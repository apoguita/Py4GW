from __future__ import annotations

import json

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import build_drop_meta
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import extract_runtime_row_item_stats
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import parse_runtime_row
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_row_ops import update_rows_item_stats_by_event
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import build_tracker_drop_message
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_tracker_drop_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_tracker_stats_payload_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import merge_stats_payload_chunk
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import payload_has_valid_mods_json


class _FakeSharedMsg:
    def __init__(self, sender_email: str, params: tuple[float, float, float, float]) -> None:
        self.SenderEmail = sender_email
        self.Params = params


def test_white_staff_payload_flow_keeps_drop_rarity_white():
    event_id = "85e699300008"
    payload_obj = {
        "n": "Holy Staff",
        "v": 224,
        "m": 90,
        "t": 0,
        "mods": [[9224, 0, 254], [9520, 1, 253], [10218, 2, 234], [41928, 40, 0], [49152, 0, 0]],
    }
    payload_text = json.dumps(payload_obj, separators=(",", ":"))

    raw_rows = [
        DropLogRow(
            timestamp="2026-02-22 15:47:00",
            viewer_bot="Leader",
            map_id=248,
            map_name="Ice Caves",
            player_name="Mesmer Tri",
            item_name="Holy Staff",
            quantity=1,
            rarity="White",
            event_id=event_id,
            item_stats="",
            item_id=487,
        ).to_runtime_row()
    ]

    buffers: dict[str, dict] = {}
    stats_by_event: dict[str, str] = {}

    def _render_payload_for_test(text: str) -> str:
        parsed = json.loads(text)
        lines = [f"Value: {int(parsed.get('v', 0))} gold", "Warrior Rune of Superior Absorption"]
        return "\n".join(lines)

    def _on_payload(event_id_arg: str, merged_payload: str) -> None:
        assert payload_has_valid_mods_json(merged_payload) is True
        rendered = _render_payload_for_test(merged_payload)
        stats_by_event[event_id_arg] = rendered
        update_rows_item_stats_by_event(raw_rows, event_id_arg, rendered)

    part1 = payload_text[: len(payload_text) // 2]
    part2 = payload_text[len(payload_text) // 2 :]

    handled1 = handle_tracker_stats_payload_branch(
        extra_0="TrackerStatsV2",
        expected_tag="TrackerStatsV2",
        extra_data_list=["TrackerStatsV2", event_id, part1, "1/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_stats_payload_chunk_fn=merge_stats_payload_chunk,
        stats_payload_chunk_buffers=buffers,
        now_ts=10.0,
        on_merged_payload_fn=_on_payload,
    )
    handled2 = handle_tracker_stats_payload_branch(
        extra_0="TrackerStatsV2",
        expected_tag="TrackerStatsV2",
        extra_data_list=["TrackerStatsV2", event_id, part2, "2/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_stats_payload_chunk_fn=merge_stats_payload_chunk,
        stats_payload_chunk_buffers=buffers,
        now_ts=10.1,
        on_merged_payload_fn=_on_payload,
    )
    assert handled1 is True
    assert handled2 is True
    assert event_id in stats_by_event
    assert "Value: 224 gold" in stats_by_event[event_id]
    assert "Rune" in stats_by_event[event_id]
    assert "gold" in extract_runtime_row_item_stats(raw_rows[0]).lower()

    drop_meta = build_drop_meta(event_id, "deadbeef", "03:47 PM")
    drop_msg = handle_tracker_drop_branch(
        extra_0="TrackerDrop",
        expected_tag="TrackerDrop",
        extra_data_list=["TrackerDrop", "Holy Staff", "White", drop_meta],
        shared_msg=_FakeSharedMsg("follower@test", (1.0, 487.0, 90.0, float((1 << 16) | 7))),
        to_text_fn=lambda v: str(v),
        normalize_text_fn=lambda v: str(v).strip(),
        build_tracker_drop_message_fn=build_tracker_drop_message,
        resolve_full_name_fn=lambda _sig: "Holy Staff",
        normalize_rarity_label_fn=lambda _name, rarity: rarity,
    )
    assert drop_msg is not None
    assert drop_msg.rarity == "White"
    parsed_row = parse_runtime_row(raw_rows[0])
    assert parsed_row is not None
    assert parsed_row.rarity == "White"
