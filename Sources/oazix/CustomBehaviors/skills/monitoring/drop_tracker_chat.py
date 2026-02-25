from __future__ import annotations

import re
from typing import Hashable


_PICKUP_REGEX = re.compile(
    r"^(?:\[([\d: ]+[AaPp][Mm])\] )?"
    r"(?:<c=#(?:[A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})>)?"
    r"(You|.+?)"
    r"(?:<\/c>)? "
    r"(?:picks? up) "
    r"(?:the )?"
    r"(?:(\d+) )?"
    r"(?:<c=#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})>)?"
    r"(.+?)"
    r"(?:<\/c>)?"
    r"\.?$",
    flags=re.IGNORECASE,
)


def pickup_regex() -> re.Pattern[str]:
    return _PICKUP_REGEX


def make_chat_dedupe_key(
    player_name: str,
    item_name: str,
    quantity: int,
    raw_message_text: str = "",
) -> Hashable:
    message_key = " ".join(str(raw_message_text or "").split()).strip().lower()
    if message_key:
        return ("msg", message_key)
    return (
        "row",
        str(player_name or "").strip().lower(),
        str(item_name or "").strip().lower(),
        int(quantity),
    )

