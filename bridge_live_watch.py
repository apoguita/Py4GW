import argparse
import datetime
import json
import socket
import sys
import time
import uuid
from typing import Any

from BridgeRuntime.protocol import recv_json_message, send_json_message


def _request(
    host: str,
    port: int,
    command: str,
    params: dict[str, Any] | None = None,
    timeout: float = 5.0,
    request_id: str | None = None,
) -> dict[str, Any]:
    req = {
        "type": "request",
        "request_id": request_id or uuid.uuid4().hex,
        "command": command,
        "params": params or {},
    }
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        send_json_message(sock, req)
        return recv_json_message(sock, timeout=timeout)
    finally:
        try:
            sock.close()
        except Exception:
            pass


def _list_clients(host: str, port: int, timeout: float) -> list[dict[str, Any]]:
    response = _request(host, port, "system.list_clients", timeout=timeout)
    if not response.get("ok"):
        return []
    result = response.get("result", {})
    if not isinstance(result, dict):
        return []
    clients = result.get("clients", [])
    if not isinstance(clients, list):
        return []
    return [client for client in clients if isinstance(client, dict)]


def _matches_client(client: dict[str, Any], args: argparse.Namespace) -> bool:
    if args.hwnd is not None and int(client.get("hwnd") or 0) != args.hwnd:
        return False
    if args.pid is not None and int(client.get("pid") or 0) != args.pid:
        return False
    if args.name_contains:
        name = str(client.get("character_name") or "")
        if args.name_contains.lower() not in name.lower():
            return False
    return True


def _pick_client(clients: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any] | None:
    matching = [client for client in clients if _matches_client(client, args)]
    if not matching:
        return None
    matching.sort(key=lambda client: int(client.get("last_seen_ms") or 0), reverse=True)
    return matching[0]


def _pick_clients(clients: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    matching = [client for client in clients if _matches_client(client, args)]
    matching.sort(
        key=lambda client: (
            str(client.get("character_name") or ""),
            int(client.get("hwnd") or 0),
            int(client.get("pid") or 0),
        )
    )
    return matching


def _target_payload(client: dict[str, Any]) -> dict[str, int]:
    hwnd = int(client.get("hwnd") or 0)
    pid = int(client.get("pid") or 0)
    if hwnd:
        return {"hwnd": hwnd}
    return {"pid": pid}


def _client_request(
    host: str,
    port: int,
    timeout: float,
    client: dict[str, Any],
    command: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = _request(
        host,
        port,
        "client.request",
        {
            "target": _target_payload(client),
            "payload": {
                "command": command,
                "params": params or {},
            },
        },
        timeout=timeout,
    )
    if not response.get("ok"):
        return response
    result = response.get("result", {})
    if not isinstance(result, dict):
        return response
    bridge_response = result.get("bridge_response", {})
    if isinstance(bridge_response, dict):
        return bridge_response
    return response


def _parse_live_entries(lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line in lines:
        if not line:
            continue
        try:
            decoded = json.loads(line)
        except json.JSONDecodeError:
            decoded = {"raw": line}
        if isinstance(decoded, dict):
            entries.append(decoded)
    return entries


def _entry_key(entry: dict[str, Any]) -> str:
    if "raw" in entry:
        return str(entry["raw"])
    return json.dumps(entry, sort_keys=True, ensure_ascii=False)


def _entry_ts_text(entry: dict[str, Any]) -> str:
    ts_text = str(entry.get("ts") or "").strip()
    if ts_text:
        try:
            return datetime.datetime.strptime(ts_text, "%Y-%m-%d %H:%M:%S.%f").strftime("%H:%M:%S")
        except ValueError:
            return ts_text
    timestamp_ms = int(entry.get("timestamp_ms") or 0)
    if timestamp_ms > 0:
        return time.strftime("%H:%M:%S", time.localtime(timestamp_ms / 1000))
    return "--:--:--"


def _print_event(entry: dict[str, Any]) -> None:
    if "raw" in entry:
        print(str(entry["raw"]), flush=True)
        return
    event = str(entry.get("event") or "")
    actor = str(entry.get("actor") or "")
    message = str(entry.get("message") or "")
    fields = {
        key: value
        for key, value in entry.items()
        if key not in {"ts", "timestamp_ms", "event", "actor", "message"}
    }
    timestamp_text = _entry_ts_text(entry)
    line = f"[{timestamp_text}] {actor}:{event}"
    if message:
        line += f" {message}"
    if fields:
        line += f" | {json.dumps(fields, ensure_ascii=False, sort_keys=True)}"
    print(line, flush=True)


def _should_print_raw_event(entry: dict[str, Any]) -> bool:
    event_name = str(entry.get("event") or "").strip()
    if event_name in {"viewer_drop_ignored_non_leader", "viewer_drop_ignored_map_grace"}:
        return False
    return True


def _print_client(client: dict[str, Any]) -> None:
    name = str(client.get("character_name") or "<unknown>")
    hwnd = int(client.get("hwnd") or 0)
    pid = int(client.get("pid") or 0)
    print(f"watching client: {name} | hwnd={hwnd} pid={pid}", flush=True)


def _print_auto(message: str) -> None:
    now_text = time.strftime("%H:%M:%S", time.localtime())
    print(f"[{now_text}] AUTO {message}", flush=True)


def _event_id(entry: dict[str, Any]) -> str:
    return str(entry.get("event_id") or "").strip()


def _event_status_line(prefix: str, entry: dict[str, Any], reason: str = "") -> str:
    event_id = _event_id(entry) or "-"
    item_name = str(entry.get("item_name") or "").strip() or "Unknown Item"
    sender_email = str(entry.get("sender_email") or "").strip().lower() or "-"
    sender_name = str(entry.get("sender_name") or "").strip() or "-"
    quantity = int(entry.get("quantity") or 1)
    model_id = int(entry.get("model_id") or 0)
    line = (
        f"{prefix} event_id={event_id} item='{item_name}' qty={quantity} "
        f"sender_email={sender_email} sender_name={sender_name} model_id={model_id}"
    )
    if reason:
        line += f" reason={reason}"
    return line


def _track_event_lifecycle(
    entry: dict[str, Any],
    pending_by_event: dict[str, dict[str, Any]],
    reported_missing_events: set[str],
) -> None:
    event_name = str(entry.get("event") or "").strip()
    event_id = _event_id(entry)
    now_ts = time.time()

    if event_name == "tracker_drop_sent":
        if not bool(entry.get("success", False)) or not event_id:
            return
        pending_by_event[event_id] = {
            "event_id": event_id,
            "item_name": str(entry.get("item_name") or "").strip() or "Unknown Item",
            "quantity": int(entry.get("quantity") or 1),
            "sender_email": str(entry.get("sender_email") or "").strip().lower(),
            "sender_session_id": int(entry.get("sender_session_id") or 0),
            "model_id": int(entry.get("model_id") or 0),
            "sent_at": now_ts,
            "alerted_missing": False,
        }
        return

    if event_name == "tracker_drop_send_failed":
        if event_id:
            pending_by_event.pop(event_id, None)
            reported_missing_events.add(event_id)
        _print_auto(_event_status_line("missing_from_leader_table", entry, reason="send_failed"))
        return

    if event_name == "tracker_drop_acked" and event_id and event_id in pending_by_event:
        pending_by_event[event_id]["acked_at"] = now_ts
        return

    if event_name == "viewer_drop_accepted" and event_id:
        was_missing = event_id in reported_missing_events
        pending_by_event.pop(event_id, None)
        if was_missing:
            _print_auto(_event_status_line("late_leader_table_accept", entry))
        else:
            _print_auto(_event_status_line("leader_table_accept", entry))
        return

    if event_name == "viewer_drop_duplicate" and event_id:
        pending_by_event.pop(event_id, None)
        _print_auto(_event_status_line("duplicate_leader_table_event", entry, reason="already_seen"))
        return

    if event_name == "viewer_drop_rejected_stale_session" and event_id:
        pending_by_event.pop(event_id, None)
        reported_missing_events.add(event_id)
        _print_auto(_event_status_line("missing_from_leader_table", entry, reason="stale_session_rejected"))
        return

    if event_name in {"candidate_suppressed_model_delta", "candidate_suppressed_world_confirmation"}:
        _print_auto(
            f"pickup_suppressed_before_table event={event_name} "
            f"message={str(entry.get('message') or '').strip() or '-'}"
        )


def _emit_missing_timeouts(
    pending_by_event: dict[str, dict[str, Any]],
    reported_missing_events: set[str],
    match_timeout_seconds: float,
) -> None:
    now_ts = time.time()
    for event_id, entry in list(pending_by_event.items()):
        sent_at = float(entry.get("sent_at") or 0.0)
        if sent_at <= 0.0 or (now_ts - sent_at) < match_timeout_seconds:
            continue
        if bool(entry.get("alerted_missing", False)):
            continue
        entry["alerted_missing"] = True
        reported_missing_events.add(event_id)
        reason = "acked_without_table_accept" if float(entry.get("acked_at") or 0.0) > 0.0 else "timeout_waiting_for_table"
        _print_auto(_event_status_line("missing_from_leader_table", entry, reason=reason))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Watch live drop tracker events through the bridge daemon")
    parser.add_argument("--host", default="127.0.0.1", help="Daemon control host")
    parser.add_argument("--port", type=int, default=47812, help="Daemon control port")
    parser.add_argument("--timeout", type=float, default=5.0, help="Socket timeout seconds")
    parser.add_argument("--poll-interval", type=float, default=0.75, help="Polling interval seconds")
    parser.add_argument("--max-live-lines", type=int, default=120, help="Tail lines requested per poll")
    parser.add_argument("--hwnd", type=int, help="Exact client hwnd to watch")
    parser.add_argument("--pid", type=int, help="Exact client pid to watch")
    parser.add_argument("--name-contains", help="Watch the first connected client whose character name matches")
    parser.add_argument("--all", action="store_true", help="Watch all matching connected clients")
    parser.add_argument("--clear", action="store_true", help="Clear the live debug file when a client is acquired")
    parser.add_argument("--match-timeout", type=float, default=3.0, help="Seconds to wait for table acceptance")
    parser.add_argument("--once", action="store_true", help="Fetch once and exit")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    max_live_lines = max(1, min(200, int(args.max_live_lines or 120)))
    seen_entry_keys: set[str] = set()
    announced_keys: set[str] = set()
    cleared_for_keys: set[str] = set()
    waiting_logged = False
    pending_by_event: dict[str, dict[str, Any]] = {}
    reported_missing_events: set[str] = set()

    try:
        while True:
            clients = _list_clients(args.host, args.port, args.timeout)
            matching_clients = _pick_clients(clients, args) if args.all else []
            if args.all:
                active_clients = matching_clients
            else:
                picked_client = _pick_client(clients, args)
                active_clients = [picked_client] if picked_client is not None else []

            if not active_clients:
                if announced_keys:
                    print("watch target disconnected; waiting for reconnect", flush=True)
                    announced_keys.clear()
                    cleared_for_keys.clear()
                    seen_entry_keys.clear()
                    pending_by_event.clear()
                    reported_missing_events.clear()
                    waiting_logged = True
                elif not waiting_logged:
                    print("no matching bridge clients connected; waiting", flush=True)
                    waiting_logged = True
                if args.once:
                    return 1
                time.sleep(max(0.25, float(args.poll_interval)))
                continue

            waiting_logged = False
            active_keys = {str(client.get("key") or "") for client in active_clients}
            disconnected_keys = [client_key for client_key in list(announced_keys) if client_key not in active_keys]
            for client_key in disconnected_keys:
                announced_keys.discard(client_key)
                cleared_for_keys.discard(client_key)

            for client in active_clients:
                client_key = str(client.get("key") or "")
                if client_key not in announced_keys:
                    announced_keys.add(client_key)
                    _print_client(client)

                if args.clear and client_key not in cleared_for_keys:
                    clear_response = _client_request(
                        args.host,
                        args.port,
                        args.timeout,
                        client,
                        "drop_tracker.clear_live_debug",
                        {},
                    )
                    clear_ok = bool(clear_response.get("ok"))
                    clear_result = clear_response.get("result", {})
                    clear_path = ""
                    if isinstance(clear_result, dict):
                        clear_path = str(clear_result.get("cleared_path") or "")
                    if clear_ok:
                        print(f"cleared live debug: {clear_path}", flush=True)
                        cleared_for_keys.add(client_key)
                    else:
                        print(json.dumps(clear_response, ensure_ascii=False, indent=2), flush=True)

            for log_client in active_clients:
                bridge_response = _client_request(
                    args.host,
                    args.port,
                    args.timeout,
                    log_client,
                    "drop_tracker.get_live_debug",
                    {"max_live_lines": max_live_lines},
                )
                if not bridge_response.get("ok"):
                    client_name = str(log_client.get("character_name") or "<unknown>")
                    client_hwnd = int(log_client.get("hwnd") or 0)
                    client_pid = int(log_client.get("pid") or 0)
                    print(
                        f"client {client_name} hwnd={client_hwnd} pid={client_pid} request failed:",
                        flush=True,
                    )
                    print(json.dumps(bridge_response, ensure_ascii=False, indent=2), flush=True)
                    continue

                result = bridge_response.get("result", {})
                if not isinstance(result, dict):
                    result = {}
                live_debug_tail = result.get("live_debug_tail", [])
                lines = [str(line) for line in live_debug_tail] if isinstance(live_debug_tail, list) else []
                for entry in _parse_live_entries(lines):
                    entry_key = _entry_key(entry)
                    if entry_key in seen_entry_keys:
                        continue
                    seen_entry_keys.add(entry_key)
                    if _should_print_raw_event(entry):
                        _print_event(entry)
                    _track_event_lifecycle(entry, pending_by_event, reported_missing_events)

            _emit_missing_timeouts(
                pending_by_event=pending_by_event,
                reported_missing_events=reported_missing_events,
                match_timeout_seconds=max(0.5, float(args.match_timeout)),
            )

            if args.once:
                return 0
            time.sleep(max(0.25, float(args.poll_interval)))
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
