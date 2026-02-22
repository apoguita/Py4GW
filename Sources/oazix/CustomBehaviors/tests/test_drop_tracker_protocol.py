from __future__ import annotations

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import build_drop_meta
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import build_name_chunks
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import decode_name_chunk_meta
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import make_event_id
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import make_name_signature
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import parse_drop_meta


def test_make_name_signature_ignores_markup_and_case():
    sig_a = make_name_signature("<c=blue>Holy Staff</c>")
    sig_b = make_name_signature(" holy staff ")
    assert sig_a
    assert sig_a == sig_b


def test_make_name_signature_empty_input_returns_empty():
    assert make_name_signature("") == ""
    assert make_name_signature("   ") == ""


def test_make_event_id_masks_timestamp_and_sequence():
    event_id = make_event_id(sequence=0x123456, now_ms=0x1FFFFFFFF)
    assert len(event_id) == 12
    assert event_id.endswith("3456")


def test_build_drop_meta_normalizes_display_time_variants():
    meta_12h = build_drop_meta("abc", "def", "12:03 AM")
    parsed_12h = parse_drop_meta(meta_12h)
    assert parsed_12h["display_time"] == "0003"

    meta_digits = build_drop_meta("abc", "def", "2026-02-22 14:58")
    parsed_digits = parse_drop_meta(meta_digits)
    assert parsed_digits["display_time"] == "2026"


def test_build_drop_meta_truncates_to_payload_limit():
    meta = build_drop_meta("abcdef1234567890", "deadbeef", "12:03 AM")
    assert len(meta) == 31


def test_parse_drop_meta_legacy_variants():
    parsed_legacy_pair = parse_drop_meta("03:47 PM|deadbeef")
    assert parsed_legacy_pair["version"] == "v1"
    assert parsed_legacy_pair["display_time"] == "03:47 PM"
    assert parsed_legacy_pair["name_signature"] == "deadbeef"

    parsed_legacy_time_only = parse_drop_meta("03:47 PM")
    assert parsed_legacy_time_only["display_time"] == "03:47 PM"
    assert parsed_legacy_time_only["name_signature"] == ""


def test_build_name_chunks_handles_empty_and_nonpositive_chunk_size():
    assert build_name_chunks("", chunk_size=31) == [(1, 1, "")]
    chunks = build_name_chunks("abcdef", chunk_size=0)
    assert chunks == [(1, 1, "abcdef")]


def test_decode_name_chunk_meta_defaults_and_clamps():
    assert decode_name_chunk_meta("bad") == (1, 1)
    assert decode_name_chunk_meta("9/2") == (2, 2)
