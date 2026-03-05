from __future__ import annotations

import csv
import datetime
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PY4GW_ROOT = Path(__file__).resolve().parents[4]
WORK_ROOT = PY4GW_ROOT.parent
DATA_DIR = PY4GW_ROOT / "Py4GW"
DROP_LOG_PATH = DATA_DIR / "drop_log.csv"
LIVE_DEBUG_PATH = DATA_DIR / "drop_tracker_live_debug.jsonl"
STATE_DIR = WORK_ROOT / ".codex_tmp"
STATE_PATH = STATE_DIR / "drop_tracker_live_test_baseline.json"
ORACLE_POLICY_PATH = DATA_DIR / "drop_tracker_live_test_oracle.json"
BUNDLE_DIR = STATE_DIR / "drop_tracker_live_test_bundles"
FORBIDDEN_ITEM_NAME_PATTERNS = (
    r"(?i)\b(?:expert|superior)?\s*(?:salvage|identification)\s+kit\b",
    r"(?i)\bid\s+kit\b",
)
FORBIDDEN_ITEM_NAME_REGEXES = tuple(re.compile(pattern) for pattern in FORBIDDEN_ITEM_NAME_PATTERNS)
FORBIDDEN_MODEL_IDS = frozenset({239, 2611, 2989, 2992, 5899})


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _write_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with STATE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def _read_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        raise SystemExit("No baseline found. Run `begin`/`arm` first.")
    with STATE_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit("Baseline file is invalid.")
    return payload


def _capture_current_state() -> dict[str, Any]:
    drop_rows = _load_csv_rows(DROP_LOG_PATH)
    debug_rows = _load_jsonl_rows(LIVE_DEBUG_PATH)
    last_drop = drop_rows[-1] if drop_rows else {}
    last_debug = debug_rows[-1] if debug_rows else {}
    return {
        "drop_row_count": len(drop_rows),
        "debug_row_count": len(debug_rows),
        "drop_last_event_id": str(last_drop.get("EventID", "") or "").strip(),
        "drop_last_ts": str(last_drop.get("Timestamp", "") or "").strip(),
        "drop_last_label": _row_item_label(last_drop) if isinstance(last_drop, dict) else "",
        "debug_last_ts": str(last_debug.get("ts", "") or "").strip(),
        "debug_last_event": str(last_debug.get("event", "") or "").strip(),
        "debug_last_event_id": str(last_debug.get("event_id", "") or "").strip(),
        "debug_last_message": str(last_debug.get("message", "") or "").strip(),
        "armed_at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _begin() -> int:
    state = _capture_current_state()
    _write_state(state)
    print(
        json.dumps(
            {
                "status": "baseline_ready",
                "drop_row_count": int(state.get("drop_row_count", 0) or 0),
                "debug_row_count": int(state.get("debug_row_count", 0) or 0),
                "state_path": str(STATE_PATH),
            },
            indent=2,
        )
    )
    return 0


def _refresh_baseline() -> dict[str, Any]:
    state = _capture_current_state()
    _write_state(state)
    return state


def _row_item_label(row: dict[str, Any]) -> str:
    name = str(row.get("ItemName", "") or row.get("item_name", "") or "Unknown Item").strip()
    qty = int(row.get("Quantity", row.get("quantity", 1)) or 1)
    rarity = str(row.get("Rarity", row.get("rarity", "Unknown")) or "Unknown").strip()
    player = str(row.get("Player", row.get("sender_name", "")) or "").strip()
    if player:
        return f"{name} x{qty} ({rarity}) [{player}]"
    return f"{name} x{qty} ({rarity})"


def _parse_ts(value: Any) -> datetime.datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return None


def _collect_likely_rezones(new_debug_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reset_rows = []
    for row in new_debug_rows:
        event_name = str(row.get("event", "")).strip()
        if event_name not in {"viewer_session_reset", "sender_session_reset"}:
            continue
        reason = str(row.get("reason", "")).strip().lower()
        uptime_ms = max(0, int(row.get("current_instance_uptime_ms", 0) or 0))
        if reason not in {"viewer_instance_reset", "viewer_sync_reset", "instance_change"} and uptime_ms > 5000:
            continue
        reset_rows.append(row)

    reset_rows.sort(
        key=lambda row: (
            _parse_ts(row.get("ts")) or datetime.datetime.min,
            max(0, int(row.get("current_map_id", 0) or 0)),
            max(0, int(row.get("current_instance_uptime_ms", 0) or 0)),
        )
    )

    rezones: list[dict[str, Any]] = []
    for row in reset_rows:
        ts_value = _parse_ts(row.get("ts"))
        map_id = max(0, int(row.get("current_map_id", 0) or 0))
        uptime_ms = max(0, int(row.get("current_instance_uptime_ms", 0) or 0))
        reason = str(row.get("reason", "")).strip() or "unknown"
        event_name = str(row.get("event", "")).strip() or "unknown"

        if rezones:
            last = rezones[-1]
            last_ts = _parse_ts(last.get("ts"))
            same_map = int(last.get("current_map_id", 0) or 0) == map_id
            close_in_time = bool(
                ts_value is not None
                and last_ts is not None
                and abs((ts_value - last_ts).total_seconds()) <= 8.0
            )
            if same_map and close_in_time:
                reasons = list(last.get("reasons", []) or [])
                if reason not in reasons:
                    reasons.append(reason)
                events = list(last.get("events", []) or [])
                if event_name not in events:
                    events.append(event_name)
                last["reasons"] = reasons
                last["events"] = events
                last["current_instance_uptime_ms"] = max(
                    max(0, int(last.get("current_instance_uptime_ms", 0) or 0)),
                    uptime_ms,
                )
                continue

        rezones.append(
            {
                "ts": str(row.get("ts", "") or "").strip(),
                "current_map_id": map_id,
                "current_instance_uptime_ms": uptime_ms,
                "reasons": [reason],
                "events": [event_name],
            }
        )
    return rezones


def _latest_viewer_reset_ts(new_debug_rows: list[dict[str, Any]]) -> datetime.datetime | None:
    latest: datetime.datetime | None = None
    for row in new_debug_rows:
        if str(row.get("event", "")).strip() != "viewer_session_reset":
            continue
        ts_value = _parse_ts(row.get("ts"))
        if ts_value is None:
            continue
        if latest is None or ts_value > latest:
            latest = ts_value
    return latest


def _slice_drop_rows_since_baseline(state: dict[str, Any], drop_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not drop_rows:
        return []
    baseline_last_event_id = str(state.get("drop_last_event_id", "") or "").strip()
    if baseline_last_event_id:
        for idx in range(len(drop_rows) - 1, -1, -1):
            if str(drop_rows[idx].get("EventID", "") or "").strip() == baseline_last_event_id:
                return list(drop_rows[idx + 1 :])
        # Baseline marker missing means file was likely reset/rotated.
        return list(drop_rows)
    baseline_count = max(0, int(state.get("drop_row_count", 0) or 0))
    if len(drop_rows) < baseline_count:
        return list(drop_rows)
    return list(drop_rows[baseline_count:])


def _slice_debug_rows_since_baseline(state: dict[str, Any], debug_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not debug_rows:
        return []
    marker_ts = str(state.get("debug_last_ts", "") or "").strip()
    marker_event = str(state.get("debug_last_event", "") or "").strip()
    marker_event_id = str(state.get("debug_last_event_id", "") or "").strip()
    marker_message = str(state.get("debug_last_message", "") or "").strip()
    if marker_ts and marker_event:
        for idx in range(len(debug_rows) - 1, -1, -1):
            row = debug_rows[idx]
            if str(row.get("ts", "") or "").strip() != marker_ts:
                continue
            if str(row.get("event", "") or "").strip() != marker_event:
                continue
            if marker_event_id and str(row.get("event_id", "") or "").strip() != marker_event_id:
                continue
            if marker_message and str(row.get("message", "") or "").strip() != marker_message:
                continue
            return list(debug_rows[idx + 1 :])
        # Baseline marker missing means file was likely reset/rotated.
        return list(debug_rows)
    baseline_count = max(0, int(state.get("debug_row_count", 0) or 0))
    if len(debug_rows) < baseline_count:
        return list(debug_rows)
    return list(debug_rows[baseline_count:])


def _slice_rows_since_baseline(
    state: dict[str, Any],
    drop_rows: list[dict[str, Any]],
    debug_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return (
        _slice_drop_rows_since_baseline(state, drop_rows),
        _slice_debug_rows_since_baseline(state, debug_rows),
    )


def _clean_sender_email(value: Any) -> str:
    return str(value or "").strip().lower()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _event_id_from_csv_row(row: dict[str, Any]) -> str:
    return str(row.get("EventID", "") or "").strip()


def _event_id_from_debug_row(row: dict[str, Any]) -> str:
    return str(row.get("event_id", "") or "").strip()


def _csv_item_stats_text(row: dict[str, Any]) -> str:
    return str(row.get("ItemStats", "") or "").strip()


def _csv_sender_email(row: dict[str, Any]) -> str:
    return _clean_sender_email(row.get("SenderEmail", ""))


def _debug_sender_email(row: dict[str, Any]) -> str:
    return _clean_sender_email(row.get("sender_email", ""))


def _is_stats_exempt_rarity(rarity_value: Any) -> bool:
    rarity = str(rarity_value or "").strip().lower()
    return rarity in {"material", "dyes", "keys", "gold"}


def _is_forbidden_loot_row(row: dict[str, Any]) -> bool:
    name = str(row.get("ItemName", "") or row.get("item_name", "") or "").strip()
    model_id = max(0, _safe_int(row.get("ModelID", row.get("model_id", 0)) or 0, 0))
    if model_id in FORBIDDEN_MODEL_IDS:
        return True
    if not name:
        return False
    return any(regex.search(name) for regex in FORBIDDEN_ITEM_NAME_REGEXES)


def _build_event_lifecycle(
    new_drop_rows: list[dict[str, Any]],
    new_debug_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    lifecycle: dict[str, dict[str, Any]] = {}

    def _entry(event_id: str) -> dict[str, Any]:
        if event_id not in lifecycle:
            lifecycle[event_id] = {
                "event_id": event_id,
                "sender_email": "",
                "accepted": False,
                "sent": False,
                "acked": False,
                "csv": False,
                "stats_bound": False,
                "stats_name_mismatch": False,
                "send_failed": False,
                "csv_has_stats": False,
                "csv_rarity": "Unknown",
                "csv_label": "",
                "csv_rows": 0,
                "debug_events": [],
            }
        return lifecycle[event_id]

    for row in list(new_debug_rows or []):
        event_id = _event_id_from_debug_row(row)
        if not event_id:
            continue
        event_name = str(row.get("event", "") or "").strip()
        entry = _entry(event_id)
        if event_name and event_name not in entry["debug_events"]:
            entry["debug_events"].append(event_name)
        sender_email = _debug_sender_email(row)
        if sender_email and not entry["sender_email"]:
            entry["sender_email"] = sender_email
        if event_name == "viewer_drop_accepted":
            entry["accepted"] = True
        elif event_name == "tracker_drop_sent":
            entry["sent"] = True
        elif event_name == "tracker_drop_acked":
            entry["acked"] = True
        elif event_name == "tracker_drop_send_failed":
            entry["send_failed"] = True
        elif event_name in {"viewer_stats_payload_bound", "viewer_stats_text_bound"}:
            entry["stats_bound"] = True
        elif event_name == "viewer_stats_name_mismatch":
            entry["stats_name_mismatch"] = True

    for row in list(new_drop_rows or []):
        event_id = _event_id_from_csv_row(row)
        if not event_id:
            continue
        entry = _entry(event_id)
        entry["csv"] = True
        entry["csv_rows"] = int(entry.get("csv_rows", 0) or 0) + 1
        stats_text = _csv_item_stats_text(row)
        if stats_text:
            entry["csv_has_stats"] = True
        sender_email = _csv_sender_email(row)
        if sender_email and not entry["sender_email"]:
            entry["sender_email"] = sender_email
        entry["csv_rarity"] = str(row.get("Rarity", "") or "Unknown").strip() or "Unknown"
        entry["csv_label"] = _row_item_label(row)

    lifecycle_rows = sorted(
        lifecycle.values(),
        key=lambda row: (str(row.get("sender_email", "") or ""), str(row.get("event_id", "") or "")),
    )

    lifecycle_gaps: list[dict[str, Any]] = []
    accepted_missing_stats_binding: list[dict[str, Any]] = []
    for row in lifecycle_rows:
        event_id = str(row.get("event_id", "") or "").strip()
        if not event_id:
            continue
        sender_email = str(row.get("sender_email", "") or "").strip().lower()
        csv_label = str(row.get("csv_label", "") or "").strip() or event_id
        if bool(row.get("accepted", False)) and not bool(row.get("csv", False)):
            lifecycle_gaps.append(
                {
                    "severity": "critical",
                    "code": "accepted_missing_csv",
                    "event_id": event_id,
                    "sender_email": sender_email,
                    "label": csv_label,
                }
            )
        if bool(row.get("csv", False)) and not bool(row.get("accepted", False)):
            lifecycle_gaps.append(
                {
                    "severity": "critical",
                    "code": "csv_missing_accepted",
                    "event_id": event_id,
                    "sender_email": sender_email,
                    "label": csv_label,
                }
            )
        if (
            bool(row.get("accepted", False))
            and bool(row.get("csv", False))
            and (not bool(row.get("stats_bound", False)))
            and (not bool(row.get("csv_has_stats", False)))
            and (not _is_stats_exempt_rarity(row.get("csv_rarity", "Unknown")))
        ):
            accepted_missing_stats_binding.append(
                {
                    "event_id": event_id,
                    "sender_email": sender_email,
                    "label": csv_label,
                    "rarity": str(row.get("csv_rarity", "") or "Unknown").strip() or "Unknown",
                }
            )
            lifecycle_gaps.append(
                {
                    "severity": "major",
                    "code": "accepted_missing_stats_binding",
                    "event_id": event_id,
                    "sender_email": sender_email,
                    "label": csv_label,
                }
            )
    return lifecycle_rows, lifecycle_gaps, accepted_missing_stats_binding


def _build_sender_lifecycle_summary(lifecycle_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_sender: dict[str, dict[str, Any]] = {}
    for row in list(lifecycle_rows or []):
        sender_email = str(row.get("sender_email", "") or "").strip().lower() or "unknown"
        sender_entry = by_sender.get(sender_email)
        if sender_entry is None:
            sender_entry = {
                "sender_email": sender_email,
                "events": 0,
                "accepted": 0,
                "sent": 0,
                "acked": 0,
                "csv": 0,
                "stats_bound": 0,
                "send_failed": 0,
                "accepted_missing_csv": 0,
                "csv_missing_accepted": 0,
                "accepted_missing_stats_binding": 0,
            }
            by_sender[sender_email] = sender_entry
        sender_entry["events"] = int(sender_entry.get("events", 0)) + 1
        if bool(row.get("accepted", False)):
            sender_entry["accepted"] = int(sender_entry.get("accepted", 0)) + 1
        if bool(row.get("sent", False)):
            sender_entry["sent"] = int(sender_entry.get("sent", 0)) + 1
        if bool(row.get("acked", False)):
            sender_entry["acked"] = int(sender_entry.get("acked", 0)) + 1
        if bool(row.get("csv", False)):
            sender_entry["csv"] = int(sender_entry.get("csv", 0)) + 1
        if bool(row.get("stats_bound", False)):
            sender_entry["stats_bound"] = int(sender_entry.get("stats_bound", 0)) + 1
        if bool(row.get("send_failed", False)):
            sender_entry["send_failed"] = int(sender_entry.get("send_failed", 0)) + 1
        if bool(row.get("accepted", False)) and (not bool(row.get("csv", False))):
            sender_entry["accepted_missing_csv"] = int(sender_entry.get("accepted_missing_csv", 0)) + 1
        if bool(row.get("csv", False)) and (not bool(row.get("accepted", False))):
            sender_entry["csv_missing_accepted"] = int(sender_entry.get("csv_missing_accepted", 0)) + 1
        if (
            bool(row.get("accepted", False))
            and bool(row.get("csv", False))
            and (not bool(row.get("stats_bound", False)))
            and (not bool(row.get("csv_has_stats", False)))
            and (not _is_stats_exempt_rarity(row.get("csv_rarity", "Unknown")))
        ):
            sender_entry["accepted_missing_stats_binding"] = int(
                sender_entry.get("accepted_missing_stats_binding", 0)
            ) + 1

    return sorted(
        by_sender.values(),
        key=lambda row: (
            -int(row.get("accepted_missing_csv", 0) or 0),
            -int(row.get("csv_missing_accepted", 0) or 0),
            -int(row.get("accepted_missing_stats_binding", 0) or 0),
            str(row.get("sender_email", "") or ""),
        ),
    )


def _summarize(new_drop_rows: list[dict[str, Any]], new_debug_rows: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in new_debug_rows if str(row.get("event", "")) == "viewer_drop_accepted"]
    duplicates = [row for row in new_debug_rows if str(row.get("event", "")) == "viewer_drop_duplicate"]
    suppressed = [row for row in new_debug_rows if str(row.get("event", "")).startswith("candidate_suppressed_")]
    sent = [row for row in new_debug_rows if str(row.get("event", "")) == "tracker_drop_sent"]
    send_failed = [row for row in new_debug_rows if str(row.get("event", "")) == "tracker_drop_send_failed"]
    acked = [row for row in new_debug_rows if str(row.get("event", "")) == "tracker_drop_acked"]
    resets = [row for row in new_debug_rows if str(row.get("event", "")).endswith("session_reset")]
    row_name_updates = [row for row in new_debug_rows if str(row.get("event", "")) == "viewer_row_name_updated"]
    stats_name_mismatches = [row for row in new_debug_rows if str(row.get("event", "")) == "viewer_stats_name_mismatch"]
    target_resolved = [row for row in new_debug_rows if str(row.get("event", "")) == "tracker_transport_target_resolved"]
    rezones = _collect_likely_rezones(new_debug_rows)
    latest_reset_ts = _latest_viewer_reset_ts(new_debug_rows)

    accepted_by_event = {
        str(row.get("event_id", "")).strip(): row
        for row in accepted
        if str(row.get("event_id", "")).strip()
    }
    csv_by_event = {
        str(row.get("EventID", "")).strip(): row
        for row in new_drop_rows
        if str(row.get("EventID", "")).strip()
    }

    missing_in_csv = [
        _row_item_label(row)
        for event_id, row in accepted_by_event.items()
        if event_id not in csv_by_event
    ]
    missing_in_accepted = [
        _row_item_label(row)
        for event_id, row in csv_by_event.items()
        if event_id not in accepted_by_event
    ]

    accepted_latest_session = []
    if latest_reset_ts is None:
        accepted_latest_session = list(accepted)
    else:
        for row in accepted:
            row_ts = _parse_ts(row.get("ts"))
            if row_ts is None or row_ts >= latest_reset_ts:
                accepted_latest_session.append(row)

    accepted_by_event_latest_session = {
        str(row.get("event_id", "")).strip(): row
        for row in accepted_latest_session
        if str(row.get("event_id", "")).strip()
    }
    latest_session_missing_in_csv = [
        _row_item_label(row)
        for event_id, row in accepted_by_event_latest_session.items()
        if event_id not in csv_by_event
    ]

    row_counter = Counter(_row_item_label(row) for row in new_drop_rows)
    duplicate_row_labels = [label for label, count in row_counter.items() if count > 1]
    csv_event_id_counter = Counter(
        str(row.get("EventID", "")).strip()
        for row in new_drop_rows
        if str(row.get("EventID", "")).strip()
    )
    duplicate_csv_event_ids = [
        event_id for event_id, count in csv_event_id_counter.items() if count > 1
    ]
    suspicious_name_updates = []
    for row in row_name_updates:
        previous_name = str(row.get("previous_name", "") or "").strip()
        new_name = str(row.get("new_name", "") or "").strip()
        previous_was_unknown = bool(row.get("previous_was_unknown", False))
        if not previous_name or not new_name or previous_name == new_name:
            continue
        if previous_was_unknown:
            continue
        if previous_name.lower() in new_name.lower() and len(new_name) > len(previous_name):
            continue
        suspicious_name_updates.append(
            {
                "event_id": str(row.get("event_id", "") or "").strip(),
                "player_name": str(row.get("player_name", "") or "").strip(),
                "sender_email": str(row.get("sender_email", "") or "").strip(),
                "rarity": str(row.get("rarity", "") or "").strip(),
                "previous_name": previous_name,
                "new_name": new_name,
                "update_source": str(row.get("update_source", "") or "").strip(),
            }
        )

    invalid_target_events = []
    for row in target_resolved:
        receiver_email = str(row.get("receiver_email", "") or "").strip().lower()
        if not receiver_email:
            continue
        in_party_flag = row.get("receiver_in_party", None)
        if isinstance(in_party_flag, bool):
            if not in_party_flag:
                invalid_target_events.append(
                    {
                        "event_id": str(row.get("event_id", "") or "").strip(),
                        "sender_email": str(row.get("sender_email", "") or "").strip().lower(),
                        "receiver_email": receiver_email,
                        "party_member_emails": list(row.get("party_member_emails", []) or [])[:24],
                    }
                )
            continue
        party_member_emails = [
            str(value or "").strip().lower()
            for value in list(row.get("party_member_emails", []) or [])
            if str(value or "").strip()
        ]
        if party_member_emails and receiver_email not in set(party_member_emails):
            invalid_target_events.append(
                {
                    "event_id": str(row.get("event_id", "") or "").strip(),
                    "sender_email": str(row.get("sender_email", "") or "").strip().lower(),
                    "receiver_email": receiver_email,
                    "party_member_emails": party_member_emails[:24],
                }
            )

    forbidden_rows = []
    for row in list(new_drop_rows or []):
        if not isinstance(row, dict):
            continue
        if not _is_forbidden_loot_row(row):
            continue
        forbidden_rows.append(
            {
                "event_id": _event_id_from_csv_row(row),
                "sender_email": _csv_sender_email(row),
                "item_name": str(row.get("ItemName", "") or row.get("item_name", "") or "").strip() or "Unknown Item",
                "rarity": str(row.get("Rarity", "") or row.get("rarity", "") or "Unknown").strip() or "Unknown",
                "model_id": max(0, _safe_int(row.get("ModelID", row.get("model_id", 0)) or 0, 0)),
                "label": _row_item_label(row),
            }
        )

    lifecycle_rows, lifecycle_gaps, accepted_missing_stats_binding = _build_event_lifecycle(
        new_drop_rows,
        new_debug_rows,
    )
    if rezones and latest_reset_ts is not None:
        latest_session_event_ids: set[str] = set()
        for row in list(accepted_latest_session or []):
            event_id = str(row.get("event_id", "") or "").strip()
            if event_id:
                latest_session_event_ids.add(event_id)
        for row in list(new_drop_rows or []):
            event_id = _event_id_from_csv_row(row)
            if not event_id:
                continue
            row_ts = _parse_ts(row.get("Timestamp"))
            if row_ts is not None and row_ts >= latest_reset_ts:
                latest_session_event_ids.add(event_id)
        if latest_session_event_ids:
            lifecycle_gaps = [
                gap
                for gap in list(lifecycle_gaps or [])
                if (
                    str(gap.get("code", "") or "").strip() not in {"accepted_missing_csv", "csv_missing_accepted"}
                    or str(gap.get("event_id", "") or "").strip() in latest_session_event_ids
                )
            ]
    sender_lifecycle = _build_sender_lifecycle_summary(lifecycle_rows)

    return {
        "new_drop_rows": len(new_drop_rows),
        "new_debug_rows": len(new_debug_rows),
        "accepted_count": len(accepted),
        "sent_count": len(sent),
        "send_failed_count": len(send_failed),
        "acked_count": len(acked),
        "duplicate_event_count": len(duplicates),
        "suppressed_event_count": len(suppressed),
        "reset_event_count": len(resets),
        "rezone_count": len(rezones),
        "row_name_update_count": len(row_name_updates),
        "suspicious_name_update_count": len(suspicious_name_updates),
        "stats_name_mismatch_count": len(stats_name_mismatches),
        "invalid_target_count": len(invalid_target_events),
        "forbidden_row_count": len(forbidden_rows),
        "lifecycle_event_count": len(lifecycle_rows),
        "lifecycle_gap_count": len(lifecycle_gaps),
        "accepted_missing_stats_binding_count": len(accepted_missing_stats_binding),
        "drop_rows": [_row_item_label(row) for row in new_drop_rows],
        "accepted_rows": [_row_item_label(row) for row in accepted],
        "missing_in_csv": missing_in_csv,
        "latest_session_missing_in_csv": latest_session_missing_in_csv,
        "latest_session_accepted_count": len(accepted_latest_session),
        "missing_in_accepted": missing_in_accepted,
        "duplicate_drop_rows": duplicate_row_labels,
        "duplicate_csv_event_ids": duplicate_csv_event_ids,
        "row_name_updates": row_name_updates[:20],
        "suspicious_name_updates": suspicious_name_updates[:20],
        "stats_name_mismatches": stats_name_mismatches[:20],
        "invalid_target_events": invalid_target_events[:20],
        "forbidden_rows": forbidden_rows[:24],
        "lifecycle_gaps": lifecycle_gaps[:60],
        "accepted_missing_stats_binding": accepted_missing_stats_binding[:40],
        "lifecycle_rows": lifecycle_rows[:120],
        "sender_lifecycle": sender_lifecycle[:40],
        "send_failed_events": send_failed[:20],
        "suppressed_events": suppressed[:12],
        "rezones": rezones[:12],
        "recent_resets": resets[-12:],
    }


def _end() -> int:
    state = _read_state()
    drop_rows = _load_csv_rows(DROP_LOG_PATH)
    debug_rows = _load_jsonl_rows(LIVE_DEBUG_PATH)

    new_drop_rows, new_debug_rows = _slice_rows_since_baseline(state, drop_rows, debug_rows)
    summary = _summarize(new_drop_rows, new_debug_rows)
    print(json.dumps(summary, indent=2))
    return 0


def _status() -> int:
    payload = {
        "drop_log_exists": DROP_LOG_PATH.exists(),
        "live_debug_exists": LIVE_DEBUG_PATH.exists(),
        "baseline_exists": STATE_PATH.exists(),
        "drop_row_count": len(_load_csv_rows(DROP_LOG_PATH)),
        "debug_row_count": len(_load_jsonl_rows(LIVE_DEBUG_PATH)),
    }
    print(json.dumps(payload, indent=2))
    return 0


def main(argv: list[str]) -> int:
    command = argv[1].strip().lower() if len(argv) > 1 else "status"
    if command == "begin":
        return _begin()
    if command == "end":
        return _end()
    if command == "status":
        return _status()
    raise SystemExit("Usage: python drop_tracker_live_test_harness.py [status|begin|end]")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
