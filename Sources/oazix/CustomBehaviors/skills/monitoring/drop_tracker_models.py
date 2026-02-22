from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


@dataclass(slots=True)
class DropLogRow:
    timestamp: str
    viewer_bot: str
    map_id: int
    map_name: str
    player_name: str
    item_name: str
    quantity: int
    rarity: str
    event_id: str = ""
    item_stats: str = ""
    item_id: int = 0
    sender_email: str = ""

    @classmethod
    def from_runtime_row(cls, row: Sequence[Any]) -> "DropLogRow | None":
        if not isinstance(row, Sequence) or len(row) < 8:
            return None
        return cls(
            timestamp=_as_text(row[0]),
            viewer_bot=_as_text(row[1]),
            map_id=max(0, _safe_int(row[2], 0)),
            map_name=_as_text(row[3]),
            player_name=_as_text(row[4]),
            item_name=_as_text(row[5]),
            quantity=max(1, _safe_int(row[6], 1)),
            rarity=_as_text(row[7]) or "Unknown",
            event_id=_as_text(row[8]) if len(row) > 8 else "",
            item_stats=_as_text(row[9]) if len(row) > 9 else "",
            item_id=max(0, _safe_int(row[10], 0)) if len(row) > 10 else 0,
            sender_email=_as_text(row[11]) if len(row) > 11 else "",
        )

    @classmethod
    def from_csv_row(
        cls,
        row: Sequence[Any],
        has_map_name: bool,
        event_idx: int = -1,
        stats_idx: int = -1,
        item_id_idx: int = -1,
        sender_email_idx: int = -1,
        map_name_fallback: str = "Unknown",
    ) -> "DropLogRow | None":
        if not isinstance(row, Sequence):
            return None
        if has_map_name:
            if len(row) < 8:
                return None
            timestamp, bot, map_id, map_name, player, item_name, qty, rarity = row[:8]
        else:
            if len(row) < 7:
                return None
            timestamp, bot, map_id, player, item_name, qty, rarity = row[:7]
            map_name = map_name_fallback

        event_id = _as_text(row[event_idx]) if event_idx >= 0 and len(row) > event_idx else ""
        item_stats = _as_text(row[stats_idx]) if stats_idx >= 0 and len(row) > stats_idx else ""
        item_id = max(0, _safe_int(row[item_id_idx], 0)) if item_id_idx >= 0 and len(row) > item_id_idx else 0
        sender_email = _as_text(row[sender_email_idx]) if sender_email_idx >= 0 and len(row) > sender_email_idx else ""

        return cls(
            timestamp=_as_text(timestamp),
            viewer_bot=_as_text(bot),
            map_id=max(0, _safe_int(map_id, 0)),
            map_name=_as_text(map_name) or "Unknown",
            player_name=_as_text(player) or "Unknown",
            item_name=_as_text(item_name) or "Unknown Item",
            quantity=max(1, _safe_int(qty, 1)),
            rarity=_as_text(rarity) or "Unknown",
            event_id=event_id,
            item_stats=item_stats,
            item_id=item_id,
            sender_email=sender_email,
        )

    def to_runtime_row(self) -> list[str]:
        return [
            self.timestamp,
            self.viewer_bot,
            str(max(0, int(self.map_id))),
            self.map_name,
            self.player_name,
            self.item_name,
            str(max(1, int(self.quantity))),
            self.rarity,
            self.event_id,
            self.item_stats,
            str(max(0, int(self.item_id))),
            self.sender_email,
        ]

    def to_csv_row(self) -> list[str]:
        return [
            self.timestamp,
            self.viewer_bot,
            str(max(0, int(self.map_id))),
            self.map_name,
            self.player_name,
            self.item_name,
            str(max(1, int(self.quantity))),
            self.rarity,
            self.event_id,
            self.item_stats,
            str(max(0, int(self.item_id))),
            self.sender_email,
        ]


@dataclass(slots=True)
class TrackerDropMessage:
    sender_email: str
    event_id: str
    name_signature: str
    item_name: str
    rarity: str
    quantity: int
    item_id: int = 0
    model_id: int = 0
    slot_bag: int = 0
    slot_index: int = 0

    @property
    def event_key(self) -> str:
        if not self.event_id:
            return ""
        return f"{self.sender_email}:{self.event_id}"


@dataclass(slots=True)
class TrackerNameChunkMessage:
    name_signature: str
    chunk_text: str
    chunk_idx: int
    chunk_total: int


@dataclass(slots=True)
class TrackerStatsChunkMessage:
    event_id: str
    chunk_text: str
    chunk_idx: int
    chunk_total: int
