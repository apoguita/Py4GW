from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path
from typing import Any

try:
    from Sources.oazix.CustomBehaviors.tests import (
        drop_tracker_live_test_harness as harness,
    )
except ImportError:
    import drop_tracker_live_test_harness as harness


def _default_oracle_policy() -> dict[str, Any]:
    return {
        "max_send_failed_count": 0,
        "max_missing_in_csv": 0,
        "max_latest_session_missing_in_csv": 0,
        "max_missing_in_accepted": 0,
        "max_duplicate_csv_event_ids": 0,
        "max_suspicious_name_update_count": 0,
        "max_stats_name_mismatch_count": 0,
        "max_invalid_target_count": 0,
        "max_forbidden_row_count": 0,
        "max_lifecycle_gap_count": 0,
        "max_accepted_missing_stats_binding_count": 0,
        "warn_duplicate_event_count_above": 0,
        "warn_suppressed_event_count_above": 0,
        "warn_reset_event_count_above": 0,
        "warn_duplicate_drop_rows_above": 0,
    }


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _load_oracle_policy() -> dict[str, Any]:
    policy = dict(_default_oracle_policy())
    path_value = getattr(harness, "ORACLE_POLICY_PATH", None)
    if path_value is None:
        return policy
    try:
        path = Path(path_value)
    except (TypeError, ValueError):
        return policy
    try:
        if not path.exists():
            return policy
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            return policy
    except OSError:
        return policy
    except json.JSONDecodeError:
        return policy

    for key, default_value in policy.items():
        if key not in payload:
            continue
        policy[key] = _safe_int(payload.get(key, default_value), int(default_value))
    return policy


def assess_summary(summary: dict[str, Any], policy: dict[str, Any] | None = None) -> tuple[bool, list[str], list[str]]:
    config = dict(policy or _load_oracle_policy())
    failures: list[str] = []
    warnings: list[str] = []

    send_failed_count = int(summary.get("send_failed_count", 0) or 0)
    missing_in_csv = list(summary.get("missing_in_csv", []))
    latest_session_missing_in_csv = list(summary.get("latest_session_missing_in_csv", []))
    missing_in_accepted = list(summary.get("missing_in_accepted", []))
    duplicate_drop_rows = list(summary.get("duplicate_drop_rows", []))
    duplicate_csv_event_ids = list(summary.get("duplicate_csv_event_ids", []))
    suspicious_name_update_count = int(summary.get("suspicious_name_update_count", 0) or 0)
    stats_name_mismatch_count = int(summary.get("stats_name_mismatch_count", 0) or 0)
    invalid_target_count = int(summary.get("invalid_target_count", 0) or 0)
    accepted_count = int(summary.get("accepted_count", 0) or 0)
    new_drop_rows = int(summary.get("new_drop_rows", 0) or 0)
    duplicate_event_count = int(summary.get("duplicate_event_count", 0) or 0)
    suppressed_event_count = int(summary.get("suppressed_event_count", 0) or 0)
    reset_event_count = int(summary.get("reset_event_count", 0) or 0)
    rezone_count = int(summary.get("rezone_count", 0) or 0)
    forbidden_row_count = int(summary.get("forbidden_row_count", 0) or 0)
    lifecycle_gap_count = int(summary.get("lifecycle_gap_count", 0) or 0)
    accepted_missing_stats_binding_count = int(summary.get("accepted_missing_stats_binding_count", 0) or 0)

    if send_failed_count > int(config.get("max_send_failed_count", 0) or 0):
        failures.append(f"Transport failed for {send_failed_count} tracker send attempt(s).")
    if rezone_count > 0:
        if len(latest_session_missing_in_csv) > int(config.get("max_latest_session_missing_in_csv", 0) or 0):
            failures.append(
                f"{len(latest_session_missing_in_csv)} accepted drop(s) in latest session never reached drop_log.csv."
            )
    elif len(missing_in_csv) > int(config.get("max_missing_in_csv", 0) or 0):
        failures.append(f"{len(missing_in_csv)} accepted drop(s) never reached drop_log.csv.")
    if len(missing_in_accepted) > int(config.get("max_missing_in_accepted", 0) or 0):
        failures.append(f"{len(missing_in_accepted)} CSV row(s) have no matching accepted viewer event.")
    if len(duplicate_csv_event_ids) > int(config.get("max_duplicate_csv_event_ids", 0) or 0):
        failures.append(f"{len(duplicate_csv_event_ids)} duplicate CSV event id(s) were recorded.")
    if suspicious_name_update_count > int(config.get("max_suspicious_name_update_count", 0) or 0):
        failures.append(
            f"{suspicious_name_update_count} suspicious late row rename(s) were detected."
        )
    if stats_name_mismatch_count > int(config.get("max_stats_name_mismatch_count", 0) or 0):
        failures.append(f"{stats_name_mismatch_count} stats/name binding mismatch event(s) were detected.")
    if invalid_target_count > int(config.get("max_invalid_target_count", 0) or 0):
        failures.append(f"{invalid_target_count} drop transport target(s) were outside current party members.")
    if forbidden_row_count > int(config.get("max_forbidden_row_count", 0) or 0):
        failures.append(f"{forbidden_row_count} forbidden loot-table row(s) were detected.")
    if lifecycle_gap_count > int(config.get("max_lifecycle_gap_count", 0) or 0):
        failures.append(f"{lifecycle_gap_count} event lifecycle gap(s) were detected.")
    if accepted_missing_stats_binding_count > int(config.get("max_accepted_missing_stats_binding_count", 0) or 0):
        failures.append(
            f"{accepted_missing_stats_binding_count} accepted drop(s) are missing bound stats."
        )
    if accepted_count == 0 and new_drop_rows == 0:
        failures.append("No tracked drops were captured during the test window.")

    if duplicate_event_count > int(config.get("warn_duplicate_event_count_above", 0) or 0):
        warnings.append(f"{duplicate_event_count} duplicate viewer event(s) were observed.")
    if suppressed_event_count > int(config.get("warn_suppressed_event_count_above", 0) or 0):
        warnings.append(f"{suppressed_event_count} candidate suppression event(s) were observed.")
    if reset_event_count > int(config.get("warn_reset_event_count_above", 0) or 0):
        warnings.append(f"{reset_event_count} session reset event(s) occurred during the run.")
    if len(duplicate_drop_rows) > int(config.get("warn_duplicate_drop_rows_above", 0) or 0):
        warnings.append(f"{len(duplicate_drop_rows)} repeated loot-table label(s) were observed.")

    return not failures, failures, warnings


def format_report(summary: dict[str, Any]) -> str:
    passed, failures, warnings = assess_summary(summary)
    lines = [
        f"LIVE TEST {'PASS' if passed else 'FAIL'}",
        (
            "Accepted Events: "
            f"{int(summary.get('accepted_count', 0) or 0)} | "
            f"CSV Rows: {int(summary.get('new_drop_rows', 0) or 0)} | "
            f"Sent: {int(summary.get('sent_count', 0) or 0)} | "
            f"Acked: {int(summary.get('acked_count', 0) or 0)} | "
            f"Send Failed: {int(summary.get('send_failed_count', 0) or 0)}"
        ),
        f"Rezones Detected: {int(summary.get('rezone_count', 0) or 0)}",
    ]
    latest_session_missing_in_csv = list(summary.get("latest_session_missing_in_csv", []))
    if latest_session_missing_in_csv:
        lines.append(f"Latest Session Missing In CSV: {len(latest_session_missing_in_csv)}")

    if failures:
        lines.append("Failures:")
        lines.extend(f"- {message}" for message in failures)
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {message}" for message in warnings)

    suspicious_name_updates = list(summary.get("suspicious_name_updates", []))
    if suspicious_name_updates:
        lines.append("Suspicious Renames:")
        for row in suspicious_name_updates[:5]:
            previous_name = str(row.get("previous_name", "") or "").strip() or "Unknown"
            new_name = str(row.get("new_name", "") or "").strip() or "Unknown"
            lines.append(f"- {previous_name} -> {new_name}")

    stats_name_mismatches = list(summary.get("stats_name_mismatches", []))
    if stats_name_mismatches:
        lines.append("Stats/Name Mismatches:")
        for row in stats_name_mismatches[:5]:
            payload_name = str(row.get("payload_name", "") or row.get("first_line_name", "") or "").strip() or "Unknown"
            row_names = list(row.get("row_names_after", []) or row.get("row_names_before", []) or [])
            row_name = str(row_names[0] if row_names else "Unknown").strip()
            lines.append(f"- row={row_name} bound={payload_name}")

    send_failed_events = list(summary.get("send_failed_events", []))
    if send_failed_events:
        lines.append("Recent Send Failures:")
        for row in send_failed_events[:5]:
            item_name = str(row.get("item_name", "") or "Unknown Item").strip()
            receiver = str(row.get("receiver_email", "") or "Unknown Receiver").strip()
            lines.append(f"- {item_name} -> {receiver}")

    invalid_target_events = list(summary.get("invalid_target_events", []))
    if invalid_target_events:
        lines.append("Invalid Transport Targets:")
        for row in invalid_target_events[:5]:
            sender = str(row.get("sender_email", "") or "unknown-sender").strip()
            receiver = str(row.get("receiver_email", "") or "unknown-receiver").strip()
            lines.append(f"- {sender} -> {receiver}")

    forbidden_rows = list(summary.get("forbidden_rows", []))
    if forbidden_rows:
        lines.append("Forbidden Loot Rows:")
        for row in forbidden_rows[:8]:
            label = str(row.get("label", "") or "").strip() or "Unknown Item"
            model_id = int(row.get("model_id", 0) or 0)
            lines.append(f"- model={model_id} {label}")

    accepted_missing_stats_binding = list(summary.get("accepted_missing_stats_binding", []))
    if accepted_missing_stats_binding:
        lines.append("Accepted Missing Stats Binding:")
        for row in accepted_missing_stats_binding[:8]:
            label = str(row.get("label", "") or "").strip() or "Unknown Item"
            event_id = str(row.get("event_id", "") or "").strip() or "-"
            lines.append(f"- ev={event_id} {label}")

    lifecycle_gaps = list(summary.get("lifecycle_gaps", []))
    if lifecycle_gaps:
        lines.append("Lifecycle Gaps:")
        for row in lifecycle_gaps[:10]:
            code = str(row.get("code", "") or "").strip() or "unknown"
            event_id = str(row.get("event_id", "") or "").strip() or "-"
            label = str(row.get("label", "") or "").strip() or "Unknown Item"
            lines.append(f"- {code} ev={event_id} {label}")

    sender_lifecycle = list(summary.get("sender_lifecycle", []))
    if sender_lifecycle:
        lines.append("Per-Sender Lifecycle:")
        for row in sender_lifecycle[:8]:
            sender_email = str(row.get("sender_email", "") or "").strip() or "unknown"
            accepted = int(row.get("accepted", 0) or 0)
            csv = int(row.get("csv", 0) or 0)
            stats_missing = int(row.get("accepted_missing_stats_binding", 0) or 0)
            lines.append(f"- {sender_email}: accepted={accepted} csv={csv} stats_missing={stats_missing}")

    rezones = list(summary.get("rezones", []))
    if rezones:
        lines.append("Rezones:")
        for row in rezones[:5]:
            map_id = int(row.get("current_map_id", 0) or 0)
            uptime_ms = int(row.get("current_instance_uptime_ms", 0) or 0)
            ts_value = str(row.get("ts", "") or "").strip() or "unknown-ts"
            reasons = ",".join(str(value or "").strip() for value in list(row.get("reasons", []) or []) if str(value or "").strip())
            lines.append(f"- map={map_id} uptime_ms={uptime_ms} ts={ts_value} reasons={reasons or 'unknown'}")

    return "\n".join(lines)


def _bundle_dir_path() -> Path:
    bundle_dir = getattr(harness, "BUNDLE_DIR", None)
    if bundle_dir is None:
        return Path(".codex_tmp") / "drop_tracker_live_test_bundles"
    try:
        return Path(bundle_dir)
    except (TypeError, ValueError):
        return Path(".codex_tmp") / "drop_tracker_live_test_bundles"


def _extract_focus_event_ids(summary: dict[str, Any]) -> list[str]:
    event_ids: list[str] = []
    candidate_lists = [
        list(summary.get("lifecycle_gaps", [])),
        list(summary.get("accepted_missing_stats_binding", [])),
        list(summary.get("send_failed_events", [])),
        list(summary.get("stats_name_mismatches", [])),
        list(summary.get("suspicious_name_updates", [])),
        list(summary.get("invalid_target_events", [])),
        list(summary.get("forbidden_rows", [])),
    ]
    for rows in candidate_lists:
        for row in list(rows or []):
            if not isinstance(row, dict):
                continue
            event_id = str(row.get("event_id", "") or "").strip()
            if event_id and event_id not in event_ids:
                event_ids.append(event_id)
    return event_ids[:200]


def _write_bug_bundle_if_failed(
    *,
    summary: dict[str, Any],
    state: dict[str, Any],
    new_drop_rows: list[dict[str, Any]],
    new_debug_rows: list[dict[str, Any]],
    policy: dict[str, Any],
) -> str:
    passed, failures, warnings = assess_summary(summary, policy)
    if passed:
        return ""

    focus_event_ids = set(_extract_focus_event_ids(summary))
    if focus_event_ids:
        related_drop_rows = [
            row
            for row in list(new_drop_rows or [])
            if str(row.get("EventID", "") or "").strip() in focus_event_ids
        ]
        related_debug_rows = [
            row
            for row in list(new_debug_rows or [])
            if str(row.get("event_id", "") or "").strip() in focus_event_ids
        ]
    else:
        related_drop_rows = list(new_drop_rows or [])[:80]
        related_debug_rows = list(new_debug_rows or [])[:200]

    bundle_payload = {
        "generated_at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "failures": failures,
        "warnings": warnings,
        "policy": policy,
        "focus_event_ids": sorted(focus_event_ids),
        "summary": summary,
        "baseline_state": state,
        "related_drop_rows": related_drop_rows[:240],
        "related_debug_rows": related_debug_rows[:500],
    }

    bundle_dir = _bundle_dir_path()
    try:
        bundle_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return ""

    bundle_name = f"bundle_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.json"
    bundle_path = bundle_dir / bundle_name
    latest_path = bundle_dir / "latest.json"
    try:
        with bundle_path.open("w", encoding="utf-8") as handle:
            json.dump(bundle_payload, handle, indent=2)
        with latest_path.open("w", encoding="utf-8") as handle:
            json.dump(bundle_payload, handle, indent=2)
    except OSError:
        return ""
    return str(bundle_path)


def _end() -> int:
    try:
        state = harness._read_state()
    except SystemExit:
        # Auto-arm first run so "done" works without a manual arm step.
        harness._refresh_baseline()
        state = harness._read_state()
    drop_rows = harness._load_csv_rows(harness.DROP_LOG_PATH)
    debug_rows = harness._load_jsonl_rows(harness.LIVE_DEBUG_PATH)

    slice_rows_fn = getattr(harness, "_slice_rows_since_baseline", None)
    if callable(slice_rows_fn):
        new_drop_rows, new_debug_rows = slice_rows_fn(state, drop_rows, debug_rows)
    else:
        drop_start = max(0, int(state.get("drop_row_count", 0)))
        debug_start = max(0, int(state.get("debug_row_count", 0)))
        new_drop_rows = drop_rows[drop_start:]
        new_debug_rows = debug_rows[debug_start:]
    policy = _load_oracle_policy()
    summary = harness._summarize(new_drop_rows, new_debug_rows)
    bug_bundle_path = _write_bug_bundle_if_failed(
        summary=summary,
        state=state,
        new_drop_rows=new_drop_rows,
        new_debug_rows=new_debug_rows,
        policy=policy,
    )
    if bug_bundle_path:
        summary["bug_bundle_path"] = bug_bundle_path
    print(format_report(summary))
    if bug_bundle_path:
        print(f"Bug Bundle: {bug_bundle_path}")
    print()
    print(json.dumps(summary, indent=2))
    passed, _failures, _warnings = assess_summary(summary, policy)
    # Keep windows clean by default: every `done` becomes baseline for the next run.
    harness._refresh_baseline()
    return 0 if passed else 1


def _baseline_exists() -> bool:
    state_path = getattr(harness, "STATE_PATH", None)
    if state_path is None:
        return False
    try:
        return bool(state_path.exists())
    except OSError:
        return False


def _auto() -> int:
    if not _baseline_exists():
        begin_rc = harness._begin()
        print("AUTO MODE: baseline armed. Run your test session, then run auto/done again.")
        return int(begin_rc)

    state = harness._read_state()
    drop_rows = harness._load_csv_rows(harness.DROP_LOG_PATH)
    debug_rows = harness._load_jsonl_rows(harness.LIVE_DEBUG_PATH)

    slice_rows_fn = getattr(harness, "_slice_rows_since_baseline", None)
    if callable(slice_rows_fn):
        new_drop_rows, new_debug_rows = slice_rows_fn(state, drop_rows, debug_rows)
    else:
        drop_start = max(0, int(state.get("drop_row_count", 0)))
        debug_start = max(0, int(state.get("debug_row_count", 0)))
        new_drop_rows = drop_rows[drop_start:]
        new_debug_rows = debug_rows[debug_start:]

    if not new_drop_rows and not new_debug_rows:
        print("AUTO MODE: no new tracker/debug rows since baseline.")
        return 0

    policy = _load_oracle_policy()
    summary = harness._summarize(new_drop_rows, new_debug_rows)
    bug_bundle_path = _write_bug_bundle_if_failed(
        summary=summary,
        state=state,
        new_drop_rows=new_drop_rows,
        new_debug_rows=new_debug_rows,
        policy=policy,
    )
    if bug_bundle_path:
        summary["bug_bundle_path"] = bug_bundle_path
    print(format_report(summary))
    if bug_bundle_path:
        print(f"Bug Bundle: {bug_bundle_path}")
    print()
    print(json.dumps(summary, indent=2))
    passed, _failures, _warnings = assess_summary(summary, policy)
    harness._refresh_baseline()
    return 0 if passed else 1


def main(argv: list[str]) -> int:
    command = argv[1].strip().lower() if len(argv) > 1 else "status"
    if command in {"begin", "arm", "start"}:
        return harness._begin()
    if command in {"status", "check"}:
        return harness._status()
    if command in {"end", "finish", "done"}:
        return _end()
    if command in {"auto", "watch"}:
        return _auto()
    raise SystemExit(
        "Usage: python drop_tracker_live_test_report.py "
        "[status|check|begin|arm|start|end|finish|done|auto|watch]"
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
