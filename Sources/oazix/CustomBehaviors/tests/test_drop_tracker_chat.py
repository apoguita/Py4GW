from __future__ import annotations

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_chat import (
    make_chat_dedupe_key,
    pickup_regex,
)


def test_pickup_regex_accepts_uppercase_am_pm_and_pick_text():
    regex = pickup_regex()
    message = "[08:41 PM] Mesmer Cetiri Picks Up 2 <c=#FFD700>Stone Summit Badge</c>."
    match = regex.search(message)
    assert match is not None
    assert str(match.group(2)).strip() == "Mesmer Cetiri"
    assert str(match.group(3)).strip() == "2"
    assert str(match.group(4)).strip().upper() == "FFD700"
    assert "Stone Summit Badge" in str(match.group(5))


def test_chat_dedupe_key_prefers_normalized_message_text():
    key_a = make_chat_dedupe_key("Player", "Badge", 1, "  [08:41 PM]  Player picks up Badge. ")
    key_b = make_chat_dedupe_key("Different", "Other", 7, "[08:41 PM] Player picks up Badge.")
    assert key_a == key_b


def test_chat_dedupe_key_fallback_uses_player_item_qty():
    key_a = make_chat_dedupe_key("Player", "Badge", 1, "")
    key_b = make_chat_dedupe_key("player", "badge", 1, "")
    key_c = make_chat_dedupe_key("player", "badge", 2, "")
    assert key_a == key_b
    assert key_a != key_c

