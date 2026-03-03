from __future__ import annotations

import datetime
import json
import os
from typing import Any

from Sources.oazix.CustomBehaviors.primitives import constants

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


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


def append_live_debug_log(
    *,
    actor: str,
    event: str,
    message: str,
    drop_log_path: str = "",
    **fields: Any,
) -> str:
    try:
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
