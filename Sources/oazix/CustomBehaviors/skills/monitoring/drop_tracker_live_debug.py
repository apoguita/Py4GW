from __future__ import annotations

import datetime
import json
import os
from typing import Any

from Sources.oazix.CustomBehaviors.primitives import constants

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)
_LAST_EMIT_BY_KEY: dict[str, float] = {}
_LIVE_DEBUG_BASE_FIELDS = {"ts", "actor", "event", "message"}


def get_live_debug_log_path(drop_log_path: str = "") -> str:
    base_path = str(drop_log_path or constants.DROP_LOG_PATH or "").strip()
    if not base_path:
        base_path = "Py4GW/drop_log.csv"
    return os.path.join(os.path.dirname(base_path), "drop_tracker_live_debug.jsonl")


def _normalize_field_value(value: Any):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, tuple):
        return [_normalize_field_value(part) for part in value]
    if isinstance(value, list):
        return [_normalize_field_value(part) for part in value]
    if isinstance(value, dict):
        normalized = {}
        for key, item in value.items():
            normalized[str(key)] = _normalize_field_value(item)
        return normalized
    return str(value)


def _tail_read_text_lines(path: str, max_lines: int) -> list[str]:
    wanted = max(1, int(max_lines or 1))
    if wanted <= 0:
        return []
    with open(path, mode="rb") as handle:
        handle.seek(0, os.SEEK_END)
        file_size = int(handle.tell() or 0)
        if file_size <= 0:
            return []
        read_cursor = file_size
        chunk_size = 4096
        newline_count = 0
        buffer = bytearray()
        while read_cursor > 0 and newline_count <= wanted:
            read_size = min(chunk_size, read_cursor)
            read_cursor -= read_size
            handle.seek(read_cursor, os.SEEK_SET)
            chunk = handle.read(read_size)
            if not chunk:
                break
            buffer[:0] = chunk
            newline_count = int(buffer.count(b"\n"))
        text = bytes(buffer).decode("utf-8", errors="replace")
        lines = text.splitlines()
        if len(lines) > wanted:
            return lines[-wanted:]
        return lines


def parse_live_debug_line(raw_line: Any) -> dict[str, Any] | None:
    line = str(raw_line or "").strip()
    if not line:
        return None
    try:
        payload = json.loads(line)
    except EXPECTED_RUNTIME_ERRORS:
        payload = {
            "ts": "",
            "actor": "raw",
            "event": "raw",
            "message": line,
        }
    if not isinstance(payload, dict):
        payload = {
            "ts": "",
            "actor": "raw",
            "event": "raw",
            "message": line,
        }
    normalized: dict[str, Any] = {
        "ts": str(payload.get("ts", "") or "").strip(),
        "actor": str(payload.get("actor", "") or "").strip() or "unknown",
        "event": str(payload.get("event", "") or "").strip() or "log",
        "message": str(payload.get("message", "") or "").strip(),
    }
    for key, value in payload.items():
        key_txt = str(key or "").strip()
        if not key_txt or key_txt in _LIVE_DEBUG_BASE_FIELDS:
            continue
        normalized[key_txt] = _normalize_field_value(value)
    return normalized


def format_live_debug_record(payload: Any, max_extra_fields: int = 6) -> str:
    if not isinstance(payload, dict):
        return ""
    ts = str(payload.get("ts", "") or "").strip()
    actor = str(payload.get("actor", "") or "").strip() or "unknown"
    event = str(payload.get("event", "") or "").strip() or "log"
    message = str(payload.get("message", "") or "").strip()
    head_parts = []
    if ts:
        head_parts.append(ts)
    head_parts.append(f"[{actor}:{event}]")
    if message:
        head_parts.append(message)
    line = " ".join(head_parts).strip()
    extra_parts: list[str] = []
    max_fields = max(0, int(max_extra_fields or 0))
    if max_fields > 0:
        for key in sorted(payload.keys()):
            if key in _LIVE_DEBUG_BASE_FIELDS:
                continue
            value = payload.get(key)
            if isinstance(value, (dict, list, tuple)):
                value_txt = json.dumps(value, ensure_ascii=True, sort_keys=True)
            else:
                value_txt = str(value)
            extra_parts.append(f"{key}={value_txt}")
            if len(extra_parts) >= max_fields:
                break
    if extra_parts:
        line = f"{line} | " + " ".join(extra_parts)
    return line.strip()


def read_live_debug_records(
    *,
    drop_log_path: str = "",
    log_path: str = "",
    max_lines: int = 120,
    scan_lines: int = 0,
    contains_text: str = "",
    actor: str = "",
    event: str = "",
) -> list[dict[str, Any]]:
    try:
        limit = max(1, min(4000, int(max_lines or 120)))
        scan_limit = int(scan_lines or 0)
        if scan_limit <= 0:
            scan_limit = max(300, limit * 8)
        scan_limit = max(limit, min(50000, scan_limit))
        target_path = str(log_path or get_live_debug_log_path(drop_log_path)).strip()
        if not target_path or not os.path.exists(target_path):
            return []
        raw_lines = _tail_read_text_lines(target_path, scan_limit)
        if not raw_lines:
            return []
        wanted_actor = str(actor or "").strip().lower()
        wanted_event = str(event or "").strip().lower()
        wanted_contains = str(contains_text or "").strip().lower()
        records: list[dict[str, Any]] = []
        for raw_line in raw_lines:
            payload = parse_live_debug_line(raw_line)
            if not payload:
                continue
            actor_txt = str(payload.get("actor", "") or "").strip().lower()
            event_txt = str(payload.get("event", "") or "").strip().lower()
            if wanted_actor and actor_txt != wanted_actor:
                continue
            if wanted_event and event_txt != wanted_event:
                continue
            if wanted_contains:
                haystack = format_live_debug_record(payload, max_extra_fields=10).lower()
                if wanted_contains not in haystack:
                    continue
            records.append(payload)
        if len(records) > limit:
            return records[-limit:]
        return records
    except EXPECTED_RUNTIME_ERRORS:
        return []


def append_live_debug_log(
    *,
    actor: str,
    event: str,
    message: str,
    drop_log_path: str = "",
    dedupe_key: str = "",
    dedupe_interval_s: float = 0.0,
    **fields: Any,
) -> str:
    try:
        dedupe_key_txt = str(dedupe_key or "").strip()
        dedupe_interval = max(0.0, float(dedupe_interval_s or 0.0))
        if dedupe_key_txt and dedupe_interval > 0.0:
            now_ts = datetime.datetime.now().timestamp()
            prev_ts = float(_LAST_EMIT_BY_KEY.get(dedupe_key_txt, 0.0) or 0.0)
            if prev_ts > 0.0 and (now_ts - prev_ts) < dedupe_interval:
                return ""
            _LAST_EMIT_BY_KEY[dedupe_key_txt] = now_ts
            if len(_LAST_EMIT_BY_KEY) > 8000:
                stale_keys = sorted(_LAST_EMIT_BY_KEY.items(), key=lambda item: float(item[1]))[:2000]
                for stale_key, _ in stale_keys:
                    _LAST_EMIT_BY_KEY.pop(stale_key, None)
        target_path = get_live_debug_log_path(drop_log_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        payload: dict[str, Any] = {
            "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "actor": str(actor or "").strip() or "unknown",
            "event": str(event or "").strip() or "log",
            "message": str(message or "").strip(),
        }
        for key, value in fields.items():
            key_txt = str(key or "").strip()
            if not key_txt:
                continue
            payload[key_txt] = _normalize_field_value(value)
        with open(target_path, mode="a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")
        return target_path
    except EXPECTED_RUNTIME_ERRORS:
        return ""


def clear_live_debug_log(drop_log_path: str = "") -> str:
    try:
        target_path = get_live_debug_log_path(drop_log_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, mode="w", encoding="utf-8") as handle:
            handle.write("")
        return target_path
    except EXPECTED_RUNTIME_ERRORS:
        return ""
