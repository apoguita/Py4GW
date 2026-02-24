import json
import socket
import struct
import time
from typing import Any

PROTOCOL_VERSION = 1


class ProtocolError(RuntimeError):
    pass


def _read_exact(sock: socket.socket, size: int, timeout: float | None = None) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    deadline = None if timeout is None else (time.time() + timeout)
    while remaining:
        if deadline is not None:
            left = deadline - time.time()
            if left <= 0:
                raise socket.timeout()
            sock.settimeout(left)
        data = sock.recv(remaining)
        if not data:
            raise ConnectionError("socket closed")
        chunks.append(data)
        remaining -= len(data)
    return b"".join(chunks)


def send_json_message(sock: socket.socket, payload: dict[str, Any]) -> None:
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    sock.sendall(struct.pack("<I", len(raw)))
    sock.sendall(raw)


def recv_json_message(sock: socket.socket, timeout: float | None = None) -> dict[str, Any]:
    header = _read_exact(sock, 4, timeout=timeout)
    (size,) = struct.unpack("<I", header)
    if size <= 0 or size > 16 * 1024 * 1024:
        raise ProtocolError(f"invalid frame size: {size}")
    raw = _read_exact(sock, size, timeout=timeout)
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ProtocolError("payload must be object")
    return payload


def make_response(request_id: str, result: Any, ok: bool = True) -> dict[str, Any]:
    return {"type": "response", "request_id": request_id, "ok": ok, "result": result}


def make_error_response(
    request_id: str,
    code: str,
    message: str,
    retryable: bool = False,
) -> dict[str, Any]:
    return {
        "type": "response",
        "request_id": request_id,
        "ok": False,
        "error": {"code": code, "message": message, "retryable": retryable},
    }
