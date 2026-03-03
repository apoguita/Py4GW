import json
import time
from typing import Any

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def make_sender_identifier(viewer, sender_email: str = "", player_name: str = "") -> str:
    sender_key = viewer._ensure_text(sender_email).strip().lower()
    if sender_key:
        return f"email:{sender_key}"
    player_key = viewer._ensure_text(player_name).strip().lower()
    if player_key:
        return f"player:{player_key}"
    return "unknown"


def make_stats_cache_key(viewer, event_id: str, sender_email: str = "", player_name: str = "") -> str:
    event_key = viewer._ensure_text(event_id).strip()
    if not event_key:
        return ""
    sender_ident = make_sender_identifier(viewer, sender_email, player_name)
    return f"{sender_ident}:{event_key}"


def get_cached_stats_text(viewer, cache: dict[str, str], event_key: str) -> str:
    lookup_key = viewer._ensure_text(event_key).strip()
    if not lookup_key:
        return ""
    return viewer._ensure_text(cache.get(lookup_key, "")).strip()


def get_row_names_by_event_and_sender(
    viewer,
    event_id: str,
    sender_email: str = "",
    player_name: str = "",
) -> list[str]:
    event_key = viewer._ensure_text(event_id).strip()
    sender_key = viewer._ensure_text(sender_email).strip().lower()
    player_key = viewer._ensure_text(player_name).strip().lower()
    if not event_key:
        return []
    names: list[str] = []
    for row in viewer.raw_drops:
        parsed = viewer._parse_drop_row(row)
        if parsed is None:
            continue
        if viewer._ensure_text(parsed.event_id).strip() != event_key:
            continue
        row_sender = viewer._ensure_text(parsed.sender_email).strip().lower()
        row_player = viewer._ensure_text(parsed.player_name).strip().lower()
        if sender_key:
            if row_sender:
                if row_sender != sender_key:
                    continue
            elif player_key and row_player != player_key:
                continue
        elif player_key and row_player != player_key:
            continue
        names.append(viewer._clean_item_name(parsed.item_name).strip() or "Unknown Item")
    return names


def get_event_state(viewer, cache_key: str, create: bool = False) -> dict[str, Any]:
    key = viewer._ensure_text(cache_key).strip()
    if not key:
        return {}
    store = getattr(viewer, "event_state_by_key", None)
    if not isinstance(store, dict):
        viewer.event_state_by_key = {}
        store = viewer.event_state_by_key
    state = store.get(key)
    if isinstance(state, dict):
        return state
    if not create:
        return {}
    state = {
        "identified": None,
        "stats_text": "",
        "payload_text": "",
        "updated_at": time.time(),
    }
    store[key] = state
    return state


def update_event_state(
    viewer,
    cache_key: str,
    *,
    identified=None,
    stats_text: Any = "",
    set_stats_text: bool = False,
    payload_text: Any = "",
    set_payload_text: bool = False,
) -> dict[str, Any]:
    key = viewer._ensure_text(cache_key).strip()
    if not key:
        return {}
    state = get_event_state(viewer, key, create=True)
    if identified is not None:
        state["identified"] = bool(identified)
    if set_stats_text:
        normalized = viewer._normalize_stats_text(stats_text)
        if state.get("identified", None) is False and not normalized:
            normalized = viewer._build_unidentified_stats_text()
        state["stats_text"] = normalized
    if set_payload_text:
        state["payload_text"] = viewer._ensure_text(payload_text).strip()
    state["updated_at"] = time.time()
    return state


def get_event_state_stats_text(viewer, cache_key: str) -> str:
    state = get_event_state(viewer, cache_key, create=False)
    if not state:
        return ""
    stats_text = viewer._normalize_stats_text(state.get("stats_text", ""))
    if stats_text:
        return stats_text
    if state.get("identified", None) is False:
        return viewer._build_unidentified_stats_text()
    return ""


def get_event_state_payload_text(viewer, cache_key: str) -> str:
    state = get_event_state(viewer, cache_key, create=False)
    if not state:
        return ""
    return viewer._ensure_text(state.get("payload_text", "")).strip()


def extract_payload_item_name(viewer, payload_text: str, fallback_item_name: str = "") -> str:
    payload_raw = viewer._ensure_text(payload_text).strip()
    if not payload_raw:
        return viewer._clean_item_name(fallback_item_name)
    try:
        payload = json.loads(payload_raw)
        if not isinstance(payload, dict):
            return viewer._clean_item_name(fallback_item_name)
    except EXPECTED_RUNTIME_ERRORS:
        return viewer._clean_item_name(fallback_item_name)
    return viewer._clean_item_name(payload.get("n", "")) or viewer._clean_item_name(fallback_item_name)
