from __future__ import annotations

from typing import Any


RENDER_CACHE_VERSION = 2


def prune_render_cache(cache: dict[str, dict[str, Any]], now_ts: float, ttl_seconds: float = 1800.0) -> dict[str, dict[str, Any]]:
    return {
        event_id: data
        for event_id, data in cache.items()
        if (now_ts - float((data or {}).get("updated_at", now_ts))) <= float(ttl_seconds)
    }


def get_cached_rendered_stats(
    cache: dict[str, dict[str, Any]],
    event_id: str,
    payload_text: str,
) -> str:
    if not event_id or not payload_text:
        return ""
    cached = cache.get(event_id, None)
    if not isinstance(cached, dict):
        return ""
    if int(cached.get("version", 0)) != RENDER_CACHE_VERSION:
        return ""
    if str(cached.get("payload", "")).strip() != str(payload_text).strip():
        return ""
    return str(cached.get("rendered", "")).strip()


def update_render_cache(
    cache: dict[str, dict[str, Any]],
    event_id: str,
    payload_text: str,
    rendered_text: str,
    now_ts: float,
) -> None:
    if not event_id:
        return
    cache[event_id] = {
        "payload": str(payload_text).strip(),
        "rendered": str(rendered_text).strip(),
        "updated_at": float(now_ts),
        "version": RENDER_CACHE_VERSION,
    }
