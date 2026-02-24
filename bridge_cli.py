import argparse
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


def _target_args(args: argparse.Namespace) -> dict[str, Any]:
    target: dict[str, Any] = {}
    if args.hwnd is not None:
        target["hwnd"] = int(args.hwnd)
    if args.pid is not None:
        target["pid"] = int(args.pid)
    return target


def _parse_json_arg(raw: str | None, default: Any) -> Any:
    if raw is None:
        return default
    return json.loads(raw)


def _print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def cmd_ping(args: argparse.Namespace) -> int:
    _print_json(_request(args.host, args.port, "system.ping"))
    return 0


def cmd_list_clients(args: argparse.Namespace) -> int:
    _print_json(_request(args.host, args.port, "system.list_clients"))
    return 0


def cmd_client_request(args: argparse.Namespace) -> int:
    payload_params = _parse_json_arg(args.params_json, {})
    if not isinstance(payload_params, dict):
        raise SystemExit("--params-json must decode to an object")
    target = _target_args(args)
    if not target:
        raise SystemExit("Provide --hwnd or --pid")
    req_id = args.request_id or uuid.uuid4().hex
    resp = _request(
        args.host,
        args.port,
        "client.request",
        {
            "target": target,
            "payload": {
                "command": args.bridge_command,
                "params": payload_params,
            },
        },
        request_id=req_id,
        timeout=args.timeout,
    )
    _print_json(resp)
    if args.poll and resp.get("ok"):
        _poll_status(args, req_id)
    return 0


def _poll_status(args: argparse.Namespace, tracked_request_id: str) -> None:
    target = _target_args(args)
    deadline = time.time() + args.poll_timeout
    while True:
        status_resp = _request(
            args.host,
            args.port,
            "client.get_status",
            {"target": target, "tracked_request_id": tracked_request_id},
            timeout=max(2.0, min(args.timeout, 10.0)),
        )
        _print_json(status_resp)
        if not status_resp.get("ok"):
            return
        bridge_resp = ((status_resp.get("result") or {}).get("bridge_response") or {})
        state = ((bridge_resp.get("result") or {}).get("state")) if bridge_resp.get("ok") else None
        if state in {"completed", "failed", "expired"}:
            return
        if time.time() >= deadline:
            return
        time.sleep(args.poll_interval)


def cmd_client_status(args: argparse.Namespace) -> int:
    target = _target_args(args)
    if not target:
        raise SystemExit("Provide --hwnd or --pid")
    _print_json(
        _request(
            args.host,
            args.port,
            "client.get_status",
            {"target": target, "tracked_request_id": args.tracked_request_id},
            timeout=args.timeout,
        )
    )
    return 0


def cmd_namespaces(args: argparse.Namespace) -> int:
    target = _target_args(args)
    if not target:
        raise SystemExit("Provide --hwnd or --pid")
    _print_json(
        _request(
            args.host,
            args.port,
            "client.request",
            {
                "target": target,
                "payload": {"command": "system.list_namespaces", "params": {}},
            },
            timeout=args.timeout,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CLI for Py4GW bridge daemon control API")
    p.add_argument("--host", default="127.0.0.1", help="Daemon control host (default: 127.0.0.1)")
    p.add_argument("--port", type=int, default=47812, help="Daemon control port (default: 47812)")
    p.add_argument("--timeout", type=float, default=5.0, help="Socket timeout seconds")

    sub = p.add_subparsers(dest="subcmd", required=True)

    s = sub.add_parser("ping", help="Ping daemon")
    s.set_defaults(func=cmd_ping)

    s = sub.add_parser("list-clients", help="List connected bridge clients")
    s.set_defaults(func=cmd_list_clients)

    s = sub.add_parser("namespaces", help="List bridge namespaces on target client")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--pid", type=int)
    s.set_defaults(func=cmd_namespaces)

    s = sub.add_parser("request", help="Send a namespaced request to a target client")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--pid", type=int)
    s.add_argument("--cmd", dest="bridge_command", required=True, help="Bridge command (e.g. player.get_state)")
    s.add_argument("--params-json", help="JSON object for bridge payload params")
    s.add_argument("--request-id", help="Optional daemon request_id to reuse")
    s.add_argument("--poll", action="store_true", help="Poll status after request (for async/queued ops)")
    s.add_argument("--poll-timeout", type=float, default=30.0, help="Max seconds to poll")
    s.add_argument("--poll-interval", type=float, default=0.5, help="Polling interval seconds")
    s.set_defaults(func=cmd_client_request)

    s = sub.add_parser("status", help="Poll an existing tracked request status on a target client")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--pid", type=int)
    s.add_argument("--tracked-request-id", required=True)
    s.set_defaults(func=cmd_client_status)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
