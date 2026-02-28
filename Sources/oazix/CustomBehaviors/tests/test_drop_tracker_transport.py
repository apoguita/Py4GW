from __future__ import annotations

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import build_drop_meta
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import build_tracker_drop_message
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import decode_slot
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_inventory_action_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_inventory_stats_request_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_inventory_stats_response_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_tracker_drop_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_tracker_name_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_tracker_stats_payload_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import handle_tracker_stats_text_branch
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import extract_event_id_hint
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import iter_circular_indices
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import is_duplicate_event
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import merge_name_chunk
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import merge_stats_payload_chunk
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import merge_stats_text_chunk
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import mark_seen_event
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import parse_tracker_name_chunk
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import parse_tracker_stats_chunk
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import payload_has_valid_mods_json
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_transport import should_skip_inventory_action_message


def test_decode_slot_roundtrip():
    encoded = (4 << 16) | 23
    bag, slot = decode_slot(encoded)
    assert bag == 4
    assert slot == 23


def test_build_tracker_drop_message_parses_meta_and_params():
    meta = build_drop_meta("85e699300008", "deadbeef", "03:47 PM")
    msg = build_tracker_drop_message(
        sender_email="follower@test",
        item_name="Holy Staff",
        rarity="White",
        meta_text=meta,
        params=(1.0, 487.0, 90.0, float((1 << 16) | 7)),
    )
    assert msg.sender_email == "follower@test"
    assert msg.event_id == "85e699300008"
    assert msg.name_signature == "deadbeef"
    assert msg.item_id == 487
    assert msg.model_id == 90
    assert msg.slot_bag == 1
    assert msg.slot_index == 7


def test_dedupe_helpers():
    seen: dict[str, float] = {}
    key = "follower@test:85e699300008"
    assert not is_duplicate_event(seen, key)
    mark_seen_event(seen, key, now_ts=123.0)
    assert is_duplicate_event(seen, key)


def test_merge_name_chunk_completes_and_caches_full_name():
    name_buffers: dict[str, dict] = {}
    full_by_sig: dict[str, str] = {}
    now_ts = 10.0
    assert merge_name_chunk(name_buffers, full_by_sig, "abc123", "Holy ", 1, 2, now_ts) == ""
    merged = merge_name_chunk(name_buffers, full_by_sig, "abc123", "Staff", 2, 2, now_ts + 0.1)
    assert merged == "Holy Staff"
    assert full_by_sig["abc123"] == "Holy Staff"
    assert "abc123" not in name_buffers


def test_merge_stats_text_chunk_resets_on_first_chunk():
    buffers: dict[str, dict] = {
        "ev-1": {"chunks": {2: "old"}, "total": 2, "updated_at": 1.0},
    }
    # First chunk should reset stale partial state.
    assert merge_stats_text_chunk(buffers, "ev-1", "new ", 1, 2, 2.0) == ""
    merged = merge_stats_text_chunk(buffers, "ev-1", "text", 2, 2, 2.1)
    assert merged == "new text"
    assert "ev-1" not in buffers


def test_merge_stats_payload_chunk_and_payload_validation():
    buffers: dict[str, dict] = {}
    part1 = '{"mods":['
    part2 = "]}"
    assert merge_stats_payload_chunk(buffers, "ev-2", part1, 1, 2, 3.0) == ""
    merged = merge_stats_payload_chunk(buffers, "ev-2", part2, 2, 2, 3.1)
    assert merged == '{"mods":[]}'
    assert payload_has_valid_mods_json(merged) is True
    assert payload_has_valid_mods_json('{"mods":"bad"}') is False


class _FakeSharedMsg:
    def __init__(self, sender_email: str, params: tuple[float, float, float, float]) -> None:
        self.SenderEmail = sender_email
        self.Params = params


def test_handle_inventory_action_branch_dispatches_callback():
    calls = []
    handled = handle_inventory_action_branch(
        extra_0="TrackerInvActionV1",
        expected_tag="TrackerInvActionV1",
        extra_data_list=["TrackerInvActionV1", "id_blue", "payload", "meta"],
        shared_msg=_FakeSharedMsg("sender@test", (0.0, 0.0, 0.0, 0.0)),
        to_text_fn=lambda v: str(v),
        normalize_text_fn=lambda v: str(v).strip(),
        run_inventory_action_fn=lambda code, payload, meta, sender: calls.append((code, payload, meta, sender)),
    )
    assert handled is True
    assert calls == [("id_blue", "payload", "meta", "sender@test")]


def test_handle_inventory_stats_request_branch_sends_only_to_other_sender():
    sent = []
    handled = handle_inventory_stats_request_branch(
        extra_0="TrackerInvStatReq",
        expected_tag="TrackerInvStatReq",
        shared_msg=_FakeSharedMsg("peer@test", (0.0, 0.0, 0.0, 0.0)),
        my_email="self@test",
        normalize_text_fn=lambda v: str(v).strip(),
        send_inventory_kit_stats_response_fn=lambda email: sent.append(email),
    )
    assert handled is True
    assert sent == ["peer@test"]


def test_handle_inventory_stats_response_branch_parses_and_upserts():
    class _AgentPartyData:
        PartyID = 7

    class _MapData:
        MapID = 248

    class _AgentData:
        Map = _MapData()

    class _Account:
        AgentPartyData = _AgentPartyData()
        AgentData = _AgentData()

    upserts = []
    handled = handle_inventory_stats_response_branch(
        extra_0="TrackerInvStatRes",
        expected_tag="TrackerInvStatRes",
        extra_data_list=["TrackerInvStatRes", "Mesmer Tri", "2", ""],
        shared_msg=_FakeSharedMsg("peer@test", (3.0, 4.0, 5.0, 6.0)),
        to_text_fn=lambda v: str(v),
        normalize_text_fn=lambda v: str(v).strip(),
        safe_int_fn=lambda v, d: int(v) if str(v).strip() else int(d),
        get_account_data_fn=lambda _email: _Account(),
        upsert_inventory_kit_stats_fn=lambda *args: upserts.append(args),
    )
    assert handled is True
    assert len(upserts) == 1
    email, name, pos, stats, map_id, party_id = upserts[0]
    assert email == "peer@test"
    assert name == "Mesmer Tri"
    assert pos == 2
    assert stats["salvage_uses"] == 3
    assert stats["superior_id_uses"] == 4
    assert stats["salvage_kits"] == 5
    assert stats["superior_id_kits"] == 6
    assert map_id == 248
    assert party_id == 7


def test_parse_tracker_name_chunk_reads_meta():
    chunk = parse_tracker_name_chunk(
        extra_data_list=["TrackerNameV2", "sig123", "Holy ", "1/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
    )
    assert chunk is not None
    assert chunk.name_signature == "sig123"
    assert chunk.chunk_text == "Holy "
    assert chunk.chunk_idx == 1
    assert chunk.chunk_total == 2


def test_parse_tracker_stats_chunk_reads_meta():
    chunk = parse_tracker_stats_chunk(
        extra_data_list=["TrackerStatsV1", "ev-1", "line", "2/3"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
    )
    assert chunk is not None
    assert chunk.event_id == "ev-1"
    assert chunk.chunk_text == "line"
    assert chunk.chunk_idx == 2
    assert chunk.chunk_total == 3


def test_handle_tracker_name_branch_merges_chunks():
    name_buffers: dict[str, dict] = {}
    full_names: dict[str, str] = {}
    handled1 = handle_tracker_name_branch(
        extra_0="TrackerNameV2",
        expected_tag="TrackerNameV2",
        extra_data_list=["TrackerNameV2", "sig456", "Holy ", "1/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_name_chunk_fn=merge_name_chunk,
        name_chunk_buffers=name_buffers,
        full_name_by_signature=full_names,
        now_ts=10.0,
    )
    handled2 = handle_tracker_name_branch(
        extra_0="TrackerNameV2",
        expected_tag="TrackerNameV2",
        extra_data_list=["TrackerNameV2", "sig456", "Staff", "2/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_name_chunk_fn=merge_name_chunk,
        name_chunk_buffers=name_buffers,
        full_name_by_signature=full_names,
        now_ts=10.1,
    )
    assert handled1 is True
    assert handled2 is True
    assert full_names["sig456"] == "Holy Staff"


def test_handle_tracker_stats_text_branch_calls_callback_on_complete():
    merged = []
    buffers: dict[str, dict] = {}
    assert handle_tracker_stats_text_branch(
        extra_0="TrackerStatsV1",
        expected_tag="TrackerStatsV1",
        extra_data_list=["TrackerStatsV1", "ev-t", "line1 ", "1/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_stats_text_chunk_fn=merge_stats_text_chunk,
        stats_chunk_buffers=buffers,
        now_ts=20.0,
        on_merged_text_fn=lambda event_id, text: merged.append((event_id, text)),
    )
    assert handle_tracker_stats_text_branch(
        extra_0="TrackerStatsV1",
        expected_tag="TrackerStatsV1",
        extra_data_list=["TrackerStatsV1", "ev-t", "line2", "2/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_stats_text_chunk_fn=merge_stats_text_chunk,
        stats_chunk_buffers=buffers,
        now_ts=20.1,
        on_merged_text_fn=lambda event_id, text: merged.append((event_id, text)),
    )
    assert merged == [("ev-t", "line1 line2")]


def test_handle_tracker_stats_payload_branch_calls_callback_on_complete():
    merged = []
    buffers: dict[str, dict] = {}
    assert handle_tracker_stats_payload_branch(
        extra_0="TrackerStatsV2",
        expected_tag="TrackerStatsV2",
        extra_data_list=["TrackerStatsV2", "ev-p", '{"mods":[', "1/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_stats_payload_chunk_fn=merge_stats_payload_chunk,
        stats_payload_chunk_buffers=buffers,
        now_ts=30.0,
        on_merged_payload_fn=lambda event_id, text: merged.append((event_id, text)),
    )
    assert handle_tracker_stats_payload_branch(
        extra_0="TrackerStatsV2",
        expected_tag="TrackerStatsV2",
        extra_data_list=["TrackerStatsV2", "ev-p", "]}", "2/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_stats_payload_chunk_fn=merge_stats_payload_chunk,
        stats_payload_chunk_buffers=buffers,
        now_ts=30.1,
        on_merged_payload_fn=lambda event_id, text: merged.append((event_id, text)),
    )
    assert merged == [("ev-p", '{"mods":[]}')]


def test_handle_tracker_drop_branch_builds_and_normalizes():
    meta = build_drop_meta("85e699300008", "cafebabe", "03:47 PM")
    msg = _FakeSharedMsg("follower@test", (1.0, 487.0, 90.0, float((2 << 16) | 9)))
    drop_msg = handle_tracker_drop_branch(
        extra_0="TrackerDrop",
        expected_tag="TrackerDrop",
        extra_data_list=["TrackerDrop", "Holy Staff", "White", meta],
        shared_msg=msg,
        to_text_fn=lambda v: str(v),
        normalize_text_fn=lambda v: str(v).strip(),
        build_tracker_drop_message_fn=build_tracker_drop_message,
        resolve_full_name_fn=lambda sig: "Holy Staff" if sig == "cafebabe" else "",
        normalize_rarity_label_fn=lambda _name, rarity: rarity,
    )
    assert drop_msg is not None
    assert drop_msg.sender_email == "follower@test"
    assert drop_msg.event_id == "85e699300008"
    assert drop_msg.name_signature == "cafebabe"
    assert drop_msg.item_name == "Holy Staff"
    assert drop_msg.item_id == 487
    assert drop_msg.model_id == 90
    assert drop_msg.slot_bag == 2
    assert drop_msg.slot_index == 9


def test_handle_tracker_drop_branch_suffixes_truncated_name_when_unresolved():
    meta = build_drop_meta("85e699300009", "abcd1234", "03:48 PM")
    long_name = "X" * 31
    drop_msg = handle_tracker_drop_branch(
        extra_0="TrackerDrop",
        expected_tag="TrackerDrop",
        extra_data_list=["TrackerDrop", long_name, "White", meta],
        shared_msg=_FakeSharedMsg("follower@test", (1.0, 0.0, 0.0, 0.0)),
        to_text_fn=lambda v: str(v),
        normalize_text_fn=lambda v: str(v).strip(),
        build_tracker_drop_message_fn=build_tracker_drop_message,
        resolve_full_name_fn=lambda _sig: "",
        normalize_rarity_label_fn=lambda _name, rarity: rarity,
    )
    assert drop_msg is not None
    assert drop_msg.item_name.endswith("~abcd")


def test_handle_tracker_drop_branch_ignores_mismatched_resolved_name():
    meta = build_drop_meta("85e69930000a", "abcd1234", "03:48 PM")
    long_name = "A" * 31
    drop_msg = handle_tracker_drop_branch(
        extra_0="TrackerDrop",
        expected_tag="TrackerDrop",
        extra_data_list=["TrackerDrop", long_name, "White", meta],
        shared_msg=_FakeSharedMsg("follower@test", (1.0, 777.0, 888.0, 0.0)),
        to_text_fn=lambda v: str(v),
        normalize_text_fn=lambda v: str(v).strip(),
        build_tracker_drop_message_fn=build_tracker_drop_message,
        resolve_full_name_fn=lambda _sig: "Completely Different Item Name",
        normalize_rarity_label_fn=lambda _name, rarity: rarity,
    )
    assert drop_msg is not None
    # Keep raw/truncated name (with suffix) instead of applying mismatched resolved name.
    assert drop_msg.item_name.endswith("~abcd")
    assert drop_msg.item_name.startswith("A" * 31)


def test_extract_event_id_hint_for_tracker_drop_and_stats():
    drop_meta = build_drop_meta("85e699300010", "beadfeed", "03:49 PM")
    drop_hint = extract_event_id_hint(
        extra_0="TrackerDrop",
        extra_data_list=["TrackerDrop", "Holy Staff", "White", drop_meta],
        to_text_fn=lambda v: str(v),
    )
    stats_hint = extract_event_id_hint(
        extra_0="TrackerStatsV2",
        extra_data_list=["TrackerStatsV2", "ev-stats", "", ""],
        to_text_fn=lambda v: str(v),
    )
    assert drop_hint == "85e699300010"
    assert stats_hint == "ev-stats"


def test_decode_slot_nonpositive_returns_zeroes():
    assert decode_slot(0) == (0, 0)
    assert decode_slot(-1) == (0, 0)


def test_is_duplicate_event_empty_key_is_not_duplicate():
    assert is_duplicate_event({}, "") is False


def test_payload_has_valid_mods_json_rejects_malformed_or_non_object():
    assert payload_has_valid_mods_json("{") is False
    assert payload_has_valid_mods_json('["mods"]') is False


def test_iter_circular_indices_rotates_across_ticks():
    first = list(iter_circular_indices(10, 0, 3))
    second = list(iter_circular_indices(10, 3, 3))
    third = list(iter_circular_indices(10, 6, 3))
    fourth = list(iter_circular_indices(10, 9, 3))
    assert first == [0, 1, 2]
    assert second == [3, 4, 5]
    assert third == [6, 7, 8]
    assert fourth == [9, 0, 1]


def test_iter_circular_indices_handles_empty_and_zero_budget():
    assert list(iter_circular_indices(0, 0, 5)) == []
    assert list(iter_circular_indices(10, 3, 0)) == []


def test_mixed_backlog_fair_scan_skips_over_cap_inventory_actions():
    tags = ["TrackerInvActionV1"] * 12 + ["TrackerDrop", "TrackerStatsV1"]
    seen_tags = []
    inventory_action_msgs_handled = 0
    custom_messages_examined = 0
    max_custom_messages_examined_per_tick = 6
    max_inventory_action_msgs_per_tick = 2

    for idx in iter_circular_indices(len(tags), 0, 64):
        tag = tags[idx]
        if should_skip_inventory_action_message(
            tag=tag,
            inventory_action_tag="TrackerInvActionV1",
            inventory_action_msgs_handled=inventory_action_msgs_handled,
            max_inventory_action_msgs_per_tick=max_inventory_action_msgs_per_tick,
        ):
            continue
        custom_messages_examined += 1
        if custom_messages_examined > max_custom_messages_examined_per_tick:
            break
        seen_tags.append(tag)
        if tag == "TrackerInvActionV1":
            inventory_action_msgs_handled += 1

    assert seen_tags[:2] == ["TrackerInvActionV1", "TrackerInvActionV1"]
    assert "TrackerDrop" in seen_tags


def test_parse_tracker_name_chunk_missing_signature_returns_none():
    parsed = parse_tracker_name_chunk(
        extra_data_list=["TrackerNameV2", "", "Holy ", "1/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
    )
    assert parsed is None


def test_parse_tracker_stats_chunk_missing_event_returns_none():
    parsed = parse_tracker_stats_chunk(
        extra_data_list=["TrackerStatsV1", "", "line", "1/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
    )
    assert parsed is None


def test_parse_tracker_stats_chunk_to_text_errors_are_handled():
    parsed = parse_tracker_stats_chunk(
        extra_data_list=["TrackerStatsV1", "ev", "line", "1/2"],
        to_text_fn=lambda _v: (_ for _ in ()).throw(TypeError("bad text")),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
    )
    assert parsed is None


def test_stats_payload_out_of_order_requires_retry_then_merges():
    merged = []
    buffers: dict[str, dict] = {}
    # Out-of-order chunk 2 arrives first.
    assert handle_tracker_stats_payload_branch(
        extra_0="TrackerStatsV2",
        expected_tag="TrackerStatsV2",
        extra_data_list=["TrackerStatsV2", "ev-retry", "]}", "2/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_stats_payload_chunk_fn=merge_stats_payload_chunk,
        stats_payload_chunk_buffers=buffers,
        now_ts=1.0,
        on_merged_payload_fn=lambda event_id, text: merged.append((event_id, text)),
    )
    # First chunk resets stale partial state by design.
    assert handle_tracker_stats_payload_branch(
        extra_0="TrackerStatsV2",
        expected_tag="TrackerStatsV2",
        extra_data_list=["TrackerStatsV2", "ev-retry", '{"mods":[', "1/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_stats_payload_chunk_fn=merge_stats_payload_chunk,
        stats_payload_chunk_buffers=buffers,
        now_ts=1.1,
        on_merged_payload_fn=lambda event_id, text: merged.append((event_id, text)),
    )
    # Retry of chunk 2 is required to complete.
    assert handle_tracker_stats_payload_branch(
        extra_0="TrackerStatsV2",
        expected_tag="TrackerStatsV2",
        extra_data_list=["TrackerStatsV2", "ev-retry", "]}", "2/2"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_stats_payload_chunk_fn=merge_stats_payload_chunk,
        stats_payload_chunk_buffers=buffers,
        now_ts=1.2,
        on_merged_payload_fn=lambda event_id, text: merged.append((event_id, text)),
    )
    assert merged == [("ev-retry", '{"mods":[]}')]


def test_handle_branches_with_tag_mismatch_return_unhandled():
    assert handle_tracker_name_branch(
        extra_0="OtherTag",
        expected_tag="TrackerNameV2",
        extra_data_list=["TrackerNameV2", "sig", "n", "1/1"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_name_chunk_fn=merge_name_chunk,
        name_chunk_buffers={},
        full_name_by_signature={},
        now_ts=1.0,
    ) is False

    assert handle_tracker_stats_text_branch(
        extra_0="OtherTag",
        expected_tag="TrackerStatsV1",
        extra_data_list=["TrackerStatsV1", "ev", "t", "1/1"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_stats_text_chunk_fn=merge_stats_text_chunk,
        stats_chunk_buffers={},
        now_ts=1.0,
        on_merged_text_fn=lambda _event_id, _text: None,
    ) is False

    assert handle_tracker_stats_payload_branch(
        extra_0="OtherTag",
        expected_tag="TrackerStatsV2",
        extra_data_list=["TrackerStatsV2", "ev", "t", "1/1"],
        to_text_fn=lambda v: str(v),
        decode_chunk_meta_fn=lambda text: tuple(int(p) for p in str(text).split("/", 1)),
        merge_stats_payload_chunk_fn=merge_stats_payload_chunk,
        stats_payload_chunk_buffers={},
        now_ts=1.0,
        on_merged_payload_fn=lambda _event_id, _text: None,
    ) is False

    assert handle_tracker_drop_branch(
        extra_0="OtherTag",
        expected_tag="TrackerDrop",
        extra_data_list=["TrackerDrop", "Holy Staff", "White", "v2|ev|sig|0350"],
        shared_msg=_FakeSharedMsg("follower@test", (1.0, 0.0, 0.0, 0.0)),
        to_text_fn=lambda v: str(v),
        normalize_text_fn=lambda v: str(v).strip(),
        build_tracker_drop_message_fn=build_tracker_drop_message,
        resolve_full_name_fn=lambda _sig: "",
        normalize_rarity_label_fn=lambda _name, rarity: rarity,
    ) is None


def test_extract_event_id_hint_unknown_tag_is_empty():
    hint = extract_event_id_hint(
        extra_0="UnknownTag",
        extra_data_list=["UnknownTag", "ev-x", "", ""],
        to_text_fn=lambda v: str(v),
    )
    assert hint == ""


def test_handle_inventory_action_branch_tag_mismatch_is_false():
    calls = []
    handled = handle_inventory_action_branch(
        extra_0="OtherTag",
        expected_tag="TrackerInvActionV1",
        extra_data_list=["TrackerInvActionV1", "id_blue", "payload", "meta"],
        shared_msg=_FakeSharedMsg("sender@test", (0.0, 0.0, 0.0, 0.0)),
        to_text_fn=lambda v: str(v),
        normalize_text_fn=lambda v: str(v).strip(),
        run_inventory_action_fn=lambda code, payload, meta, sender: calls.append((code, payload, meta, sender)),
    )
    assert handled is False
    assert calls == []


def test_handle_inventory_stats_request_branch_self_and_mismatch_no_send():
    sent = []
    assert handle_inventory_stats_request_branch(
        extra_0="OtherTag",
        expected_tag="TrackerInvStatReq",
        shared_msg=_FakeSharedMsg("peer@test", (0.0, 0.0, 0.0, 0.0)),
        my_email="self@test",
        normalize_text_fn=lambda v: str(v).strip(),
        send_inventory_kit_stats_response_fn=lambda email: sent.append(email),
    ) is False
    assert handle_inventory_stats_request_branch(
        extra_0="TrackerInvStatReq",
        expected_tag="TrackerInvStatReq",
        shared_msg=_FakeSharedMsg("self@test", (0.0, 0.0, 0.0, 0.0)),
        my_email="self@test",
        normalize_text_fn=lambda v: str(v).strip(),
        send_inventory_kit_stats_response_fn=lambda email: sent.append(email),
    ) is True
    assert sent == []


def test_handle_inventory_stats_response_branch_ignores_empty_sender():
    upserts = []
    assert handle_inventory_stats_response_branch(
        extra_0="OtherTag",
        expected_tag="TrackerInvStatRes",
        extra_data_list=["TrackerInvStatRes", "Mesmer Tri", "2", ""],
        shared_msg=_FakeSharedMsg("peer@test", (1.0, 2.0, 3.0, 4.0)),
        to_text_fn=lambda v: str(v),
        normalize_text_fn=lambda v: str(v).strip(),
        safe_int_fn=lambda v, d: int(v) if str(v).strip() else int(d),
        get_account_data_fn=lambda _email: None,
        upsert_inventory_kit_stats_fn=lambda *args: upserts.append(args),
    ) is False

    assert handle_inventory_stats_response_branch(
        extra_0="TrackerInvStatRes",
        expected_tag="TrackerInvStatRes",
        extra_data_list=["TrackerInvStatRes", "Mesmer Tri", "2", ""],
        shared_msg=_FakeSharedMsg("   ", (1.0, 2.0, 3.0, 4.0)),
        to_text_fn=lambda v: str(v),
        normalize_text_fn=lambda v: str(v).strip(),
        safe_int_fn=lambda v, d: int(v) if str(v).strip() else int(d),
        get_account_data_fn=lambda _email: None,
        upsert_inventory_kit_stats_fn=lambda *args: upserts.append(args),
    ) is True
    assert upserts == []
