import argparse
import socket
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from BridgeRuntime.protocol import (
    PROTOCOL_VERSION,
    ProtocolError,
    make_error_response,
    make_response,
    recv_json_message,
    send_json_message,
)


def _now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class ForwardRecord:
    request_id: str
    client_key: str
    created_ms: int
    last_response: dict[str, Any] | None = None


@dataclass
class BridgeClientSession:
    sock: socket.socket
    addr: tuple[str, int]
    daemon: "BridgeDaemon"
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    client_hwnd: int = 0
    client_pid: int = 0
    account_email: str = ""
    character_name: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    alive: bool = True
    send_lock: threading.Lock = field(default_factory=threading.Lock)
    pending: dict[str, tuple[threading.Event, dict[str, Any] | None]] = field(default_factory=dict)
    pending_lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def key(self) -> str:
        return f"hwnd:{self.client_hwnd}" if self.client_hwnd else f"pid:{self.client_pid}"

    def describe(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "key": self.key,
            "hwnd": self.client_hwnd,
            "pid": self.client_pid,
            "account_email": self.account_email,
            "character_name": self.character_name,
            "connected_at_ms": self.meta.get("connected_at_ms", 0),
            "last_seen_ms": self.meta.get("last_seen_ms", 0),
            "addr": f"{self.addr[0]}:{self.addr[1]}",
        }

    def set_handshake(self, hello: dict[str, Any]) -> None:
        client = hello.get("client", {})
        if not isinstance(client, dict):
            client = {}
        self.client_hwnd = int(client.get("hwnd") or 0)
        self.client_pid = int(client.get("pid") or 0)
        self.account_email = str(client.get("account_email") or "")
        self.character_name = str(client.get("character_name") or "")
        self.meta["connected_at_ms"] = _now_ms()
        self.meta["last_seen_ms"] = self.meta["connected_at_ms"]

    def call_client(
        self,
        command: str,
        params: dict[str, Any],
        timeout_s: float = 2.0,
        request_id_override: str | None = None,
    ) -> dict[str, Any]:
        request_id = request_id_override or uuid.uuid4().hex
        evt = threading.Event()
        with self.pending_lock:
            self.pending[request_id] = (evt, None)
        try:
            with self.send_lock:
                send_json_message(
                    self.sock,
                    {"type": "request", "request_id": request_id, "command": command, "params": params},
                )
            if not evt.wait(timeout_s):
                raise TimeoutError(f"client timeout for {command}")
            with self.pending_lock:
                _, resp = self.pending.pop(request_id, (None, None))
            if resp is None:
                raise RuntimeError("missing client response")
            return resp
        finally:
            with self.pending_lock:
                self.pending.pop(request_id, None)

    def recv_loop(self) -> None:
        try:
            hello = recv_json_message(self.sock, timeout=10.0)
            if hello.get("type") != "hello":
                raise ProtocolError("expected hello")
            if int(hello.get("protocol_version", 0)) != PROTOCOL_VERSION:
                raise ProtocolError("protocol version mismatch")
            if self.daemon.token and str(hello.get("token") or "") != self.daemon.token:
                raise ProtocolError("auth token mismatch")
            self.set_handshake(hello)
            self.daemon.register_client(self)
            with self.send_lock:
                send_json_message(
                    self.sock,
                    {
                        "type": "hello_ack",
                        "protocol_version": PROTOCOL_VERSION,
                        "session_id": self.session_id,
                        "server_time_ms": _now_ms(),
                    },
                )
            while self.alive:
                msg = recv_json_message(self.sock, timeout=30.0)
                self.meta["last_seen_ms"] = _now_ms()
                mtype = str(msg.get("type") or "")
                if mtype == "response":
                    req_id = str(msg.get("request_id") or "")
                    with self.pending_lock:
                        item = self.pending.get(req_id)
                        if item:
                            evt, _ = item
                            self.pending[req_id] = (evt, msg)
                            evt.set()
                elif mtype == "heartbeat":
                    client = msg.get("client", {})
                    if isinstance(client, dict):
                        self.account_email = str(client.get("account_email") or self.account_email)
                        self.character_name = str(client.get("character_name") or self.character_name)
        except Exception as exc:
            print(f"[daemon] client disconnected {self.addr}: {exc}")
        finally:
            self.alive = False
            self.daemon.unregister_client(self)
            try:
                self.sock.close()
            except Exception:
                pass


class BridgeDaemon:
    def __init__(self, widget_host: str, widget_port: int, control_host: str, control_port: int, token: str):
        self.widget_host = widget_host
        self.widget_port = widget_port
        self.control_host = control_host
        self.control_port = control_port
        self.token = token
        self._clients: dict[str, BridgeClientSession] = {}
        self._clients_lock = threading.Lock()
        self._forward_log: dict[str, ForwardRecord] = {}
        self._forward_lock = threading.Lock()

    def register_client(self, client: BridgeClientSession) -> None:
        with self._clients_lock:
            self._clients[client.key] = client
        print(f"[daemon] connected {client.describe()}")

    def unregister_client(self, client: BridgeClientSession) -> None:
        with self._clients_lock:
            if self._clients.get(client.key) is client:
                self._clients.pop(client.key, None)

    def list_clients(self) -> list[dict[str, Any]]:
        with self._clients_lock:
            return [c.describe() for c in self._clients.values()]

    def get_client(self, hwnd: int | None, pid: int | None) -> BridgeClientSession | None:
        with self._clients_lock:
            if hwnd:
                return self._clients.get(f"hwnd:{int(hwnd)}")
            if pid:
                return self._clients.get(f"pid:{int(pid)}")
            return None

    def _record_forward(self, request_id: str, client: BridgeClientSession, response: dict[str, Any]) -> None:
        with self._forward_lock:
            self._forward_log[request_id] = ForwardRecord(
                request_id=request_id,
                client_key=client.key,
                created_ms=_now_ms(),
                last_response=response,
            )

    def control_dispatch(self, request: dict[str, Any]) -> dict[str, Any]:
        request_id = str(request.get("request_id") or uuid.uuid4().hex)
        command = str(request.get("command") or "")
        params = request.get("params", {})
        if not isinstance(params, dict):
            return make_error_response(request_id, "validation_params", "params must be object")
        try:
            if command == "system.ping":
                return make_response(request_id, {"pong": True, "time_ms": _now_ms()})
            if command == "system.list_clients":
                return make_response(request_id, {"clients": self.list_clients()})
            if command == "client.request":
                target = params.get("target", {})
                payload = params.get("payload", {})
                if not isinstance(target, dict) or not isinstance(payload, dict):
                    return make_error_response(request_id, "validation_target", "target and payload must be objects")
                client = self.get_client(target.get("hwnd"), target.get("pid"))
                if client is None:
                    return make_error_response(request_id, "client_not_found", "target client not connected")
                payload_cmd = str(payload.get("command") or "")
                payload_params = payload.get("params", {})
                if not payload_cmd or not isinstance(payload_params, dict):
                    return make_error_response(request_id, "validation_payload", "payload.command and payload.params required")
                resp = client.call_client(payload_cmd, dict(payload_params), timeout_s=3.0, request_id_override=request_id)
                self._record_forward(request_id, client, resp)
                return make_response(request_id, {"target": client.describe(), "bridge_response": resp})
            if command == "client.get_status":
                target = params.get("target", {})
                tracked_request_id = str(params.get("tracked_request_id") or "")
                if not isinstance(target, dict) or not tracked_request_id:
                    return make_error_response(request_id, "validation_status", "target and tracked_request_id required")
                client = self.get_client(target.get("hwnd"), target.get("pid"))
                if client is None:
                    return make_error_response(request_id, "client_not_found", "target client not connected")
                resp = client.call_client("ops.get_status", {"request_id": tracked_request_id}, timeout_s=2.0)
                self._record_forward(tracked_request_id, client, resp)
                return make_response(request_id, {"target": client.describe(), "bridge_response": resp})
            return make_error_response(request_id, "not_supported", f"unsupported command: {command}")
        except TimeoutError as exc:
            return make_error_response(request_id, "timeout", str(exc), retryable=True)
        except Exception as exc:
            return make_error_response(request_id, "internal_error", str(exc))

    def _serve_widget_clients(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.widget_host, self.widget_port))
        server.listen()
        print(f"[daemon] widget server {self.widget_host}:{self.widget_port}")
        while True:
            sock, addr = server.accept()
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            threading.Thread(
                target=BridgeClientSession(sock=sock, addr=addr, daemon=self).recv_loop,
                daemon=True,
            ).start()

    def _handle_control_conn(self, sock: socket.socket) -> None:
        try:
            while True:
                req = recv_json_message(sock, timeout=300.0)
                if req.get("type") != "request":
                    send_json_message(sock, make_error_response("", "protocol_type", "expected request"))
                    continue
                send_json_message(sock, self.control_dispatch(req))
        except Exception:
            pass
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def _serve_control(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.control_host, self.control_port))
        server.listen()
        print(f"[daemon] control server {self.control_host}:{self.control_port}")
        while True:
            sock, _ = server.accept()
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            threading.Thread(target=self._handle_control_conn, args=(sock,), daemon=True).start()

    def run(self) -> None:
        threading.Thread(target=self._serve_widget_clients, daemon=True).start()
        threading.Thread(target=self._serve_control, daemon=True).start()
        while True:
            time.sleep(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Py4GW bridge daemon")
    parser.add_argument("--widget-host", default="127.0.0.1")
    parser.add_argument("--widget-port", type=int, default=47811)
    parser.add_argument("--control-host", default="127.0.0.1")
    parser.add_argument("--control-port", type=int, default=47812)
    parser.add_argument("--token", default="")
    args = parser.parse_args()
    BridgeDaemon(
        widget_host=args.widget_host,
        widget_port=args.widget_port,
        control_host=args.control_host,
        control_port=args.control_port,
        token=args.token,
    ).run()


if __name__ == "__main__":
    main()
