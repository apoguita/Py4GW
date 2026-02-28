from __future__ import annotations

from typing import Any
from typing import Callable

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import DropLogRow


def _clone_aggregates(aggregated_drops: dict[Any, Any]) -> dict[tuple[str, str], dict[str, int]]:
    cloned: dict[tuple[str, str], dict[str, int]] = {}
    for key, data in (aggregated_drops or {}).items():
        if not isinstance(key, tuple) or len(key) != 2:
            continue
        if not isinstance(data, dict):
            continue
        name = str(key[0])
        rarity = str(key[1])
        cloned[(name, rarity)] = {
            "Quantity": int(data.get("Quantity", 0)),
            "Count": int(data.get("Count", 0)),
        }
    return cloned


def _merge_parsed_rows_inplace(
    *,
    parsed_rows: list[DropLogRow],
    raw_drops: list[list[str]],
    aggregated_drops: dict[tuple[str, str], dict[str, int]],
    total_drops: int,
    stats_by_event: dict[str, str],
    ensure_text_fn: Callable[[Any], str],
    make_stats_cache_key_fn: Callable[[str, str, str], str],
    canonical_name_fn: Callable[[Any, Any, dict[tuple[str, str], dict[str, int]]], str],
) -> int:
    total = int(total_drops)
    for parsed in list(parsed_rows or []):
        if not isinstance(parsed, DropLogRow):
            continue
        qty = max(1, int(parsed.quantity))
        rarity = str(ensure_text_fn(parsed.rarity)).strip() or "Unknown"
        raw_drops.append(parsed.to_runtime_row())
        total += int(qty)

        if parsed.event_id:
            sender_email = str(ensure_text_fn(parsed.sender_email)).strip().lower()
            stats_cache_key = str(
                make_stats_cache_key_fn(parsed.event_id, sender_email, parsed.player_name) or ""
            ).strip()
            if stats_cache_key:
                stats_by_event[stats_cache_key] = str(ensure_text_fn(parsed.item_stats)).strip()

        canonical_name = str(canonical_name_fn(parsed.item_name, rarity, aggregated_drops))
        agg_key = (canonical_name, rarity)
        if agg_key not in aggregated_drops:
            aggregated_drops[agg_key] = {"Quantity": 0, "Count": 0}
        aggregated_drops[agg_key]["Quantity"] += int(qty)
        aggregated_drops[agg_key]["Count"] += 1
    return int(total)


def build_state_from_parsed_rows(
    *,
    parsed_rows: list[DropLogRow],
    ensure_text_fn: Callable[[Any], str],
    make_stats_cache_key_fn: Callable[[str, str, str], str],
    canonical_name_fn: Callable[[Any, Any, dict[tuple[str, str], dict[str, int]]], str],
) -> tuple[list[list[str]], dict[tuple[str, str], dict[str, int]], int, dict[str, str]]:
    raw_drops: list[list[str]] = []
    aggregated_drops: dict[tuple[str, str], dict[str, int]] = {}
    stats_by_event: dict[str, str] = {}
    total_drops = _merge_parsed_rows_inplace(
        parsed_rows=list(parsed_rows or []),
        raw_drops=raw_drops,
        aggregated_drops=aggregated_drops,
        total_drops=0,
        stats_by_event=stats_by_event,
        ensure_text_fn=ensure_text_fn,
        make_stats_cache_key_fn=make_stats_cache_key_fn,
        canonical_name_fn=canonical_name_fn,
    )
    return raw_drops, aggregated_drops, int(total_drops), stats_by_event


def merge_parsed_rows_into_state(
    *,
    parsed_rows: list[DropLogRow],
    raw_drops: list[list[str]],
    aggregated_drops: dict[tuple[str, str], dict[str, int]],
    total_drops: int,
    stats_by_event: dict[str, str],
    ensure_text_fn: Callable[[Any], str],
    make_stats_cache_key_fn: Callable[[str, str, str], str],
    canonical_name_fn: Callable[[Any, Any, dict[tuple[str, str], dict[str, int]]], str],
) -> tuple[list[list[str]], dict[tuple[str, str], dict[str, int]], int, dict[str, str]]:
    next_raw_drops = list(raw_drops or [])
    next_aggregated_drops = _clone_aggregates(aggregated_drops or {})
    next_stats_by_event = dict(stats_by_event or {})
    next_total = _merge_parsed_rows_inplace(
        parsed_rows=list(parsed_rows or []),
        raw_drops=next_raw_drops,
        aggregated_drops=next_aggregated_drops,
        total_drops=int(total_drops),
        stats_by_event=next_stats_by_event,
        ensure_text_fn=ensure_text_fn,
        make_stats_cache_key_fn=make_stats_cache_key_fn,
        canonical_name_fn=canonical_name_fn,
    )
    return next_raw_drops, next_aggregated_drops, int(next_total), next_stats_by_event


def append_drop_rows_to_state(
    *,
    drop_rows: list[DropLogRow],
    raw_drops: list[list[str]],
    aggregated_drops: dict[tuple[str, str], dict[str, int]],
    total_drops: int,
    stats_by_event: dict[str, str],
    ensure_text_fn: Callable[[Any], str],
    make_stats_cache_key_fn: Callable[[str, str, str], str],
    canonical_name_fn: Callable[[Any, Any, dict[tuple[str, str], dict[str, int]]], str],
) -> tuple[list[list[str]], dict[tuple[str, str], dict[str, int]], int, dict[str, str]]:
    if not isinstance(raw_drops, list):
        raise TypeError("raw_drops must be a list")
    if not isinstance(aggregated_drops, dict):
        raise TypeError("aggregated_drops must be a dict")
    if not isinstance(stats_by_event, dict):
        raise TypeError("stats_by_event must be a dict")
    next_total = _merge_parsed_rows_inplace(
        parsed_rows=list(drop_rows or []),
        raw_drops=raw_drops,
        aggregated_drops=aggregated_drops,
        total_drops=int(total_drops),
        stats_by_event=stats_by_event,
        ensure_text_fn=ensure_text_fn,
        make_stats_cache_key_fn=make_stats_cache_key_fn,
        canonical_name_fn=canonical_name_fn,
    )
    return raw_drops, aggregated_drops, int(next_total), stats_by_event


def rebuild_aggregates_from_runtime_rows(
    *,
    raw_drops: list[Any],
    parse_runtime_row_fn: Callable[[Any], Any],
    canonical_name_fn: Callable[[Any, Any, dict[tuple[str, str], dict[str, int]]], str],
    safe_int_fn: Callable[[Any, int], int],
    ensure_text_fn: Callable[[Any], str],
) -> tuple[dict[tuple[str, str], dict[str, int]], int]:
    aggregated_drops: dict[tuple[str, str], dict[str, int]] = {}
    total_drops = 0
    for row in list(raw_drops or []):
        parsed = parse_runtime_row_fn(row)
        if parsed is None:
            continue
        qty = max(1, int(safe_int_fn(getattr(parsed, "quantity", 1), 1)))
        rarity = str(ensure_text_fn(getattr(parsed, "rarity", ""))).strip() or "Unknown"
        item_name = getattr(parsed, "item_name", "")
        canonical_name = str(canonical_name_fn(item_name, rarity, aggregated_drops))
        agg_key = (canonical_name, rarity)
        if agg_key not in aggregated_drops:
            aggregated_drops[agg_key] = {"Quantity": 0, "Count": 0}
        aggregated_drops[agg_key]["Quantity"] += int(qty)
        aggregated_drops[agg_key]["Count"] += 1
        total_drops += int(qty)
    return aggregated_drops, int(total_drops)
