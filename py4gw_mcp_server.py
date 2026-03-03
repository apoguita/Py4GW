import argparse
import json
import socket
import sys
import uuid
from typing import Any

from BridgeRuntime.protocol import recv_json_message
from BridgeRuntime.protocol import send_json_message


SERVER_NAME = "py4gw-bridge-mcp"
SERVER_VERSION = "0.1.0"
MCP_PROTOCOL_VERSION = "2024-11-05"


def _daemon_request(
    host: str,
    port: int,
    command: str,
    params: dict[str, Any] | None = None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    req = {
        "type": "request",
        "request_id": uuid.uuid4().hex,
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


def _read_stdio_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in {b"\r\n", b"\n"}:
            break
        raw = line.decode("utf-8").strip()
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    content_length = int(headers.get("content-length") or 0)
    if content_length <= 0:
        return None
    body = sys.stdin.buffer.read(content_length)
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("MCP payload must be an object")
    return payload


def _write_stdio_message(payload: dict[str, Any]) -> None:
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def _make_jsonrpc_result(msg_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _make_jsonrpc_error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _tool_list() -> list[dict[str, Any]]:
    target_schema = {
        "type": "object",
        "properties": {
            "hwnd": {"type": "integer"},
            "pid": {"type": "integer"},
        },
        "minProperties": 1,
        "additionalProperties": False,
    }
    return [
        {
            "name": "list_clients",
            "description": "List connected Py4GW bridge clients.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "list_namespaces",
            "description": "List bridge namespaces and namespace metadata for a target client.",
            "inputSchema": {
                "type": "object",
                "properties": target_schema["properties"],
                "minProperties": 1,
                "additionalProperties": False,
            },
        },
        {
            "name": "list_commands",
            "description": "List bridge command metadata for a target client.",
            "inputSchema": {
                "type": "object",
                "properties": target_schema["properties"],
                "minProperties": 1,
                "additionalProperties": False,
            },
        },
        {
            "name": "describe_runtime",
            "description": "Get normalized runtime metadata for a target client.",
            "inputSchema": {
                "type": "object",
                "properties": target_schema["properties"],
                "minProperties": 1,
                "additionalProperties": False,
            },
        },
        {
            "name": "get_map_state",
            "description": "Get normalized map state for a target client.",
            "inputSchema": {
                "type": "object",
                "properties": target_schema["properties"],
                "minProperties": 1,
                "additionalProperties": False,
            },
        },
        {
            "name": "get_player_state",
            "description": "Get normalized player state for a target client.",
            "inputSchema": {
                "type": "object",
                "properties": target_schema["properties"],
                "minProperties": 1,
                "additionalProperties": False,
            },
        },
        {
            "name": "list_agents",
            "description": "List agent ids for a target client and group.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "hwnd": {"type": "integer"},
                    "pid": {"type": "integer"},
                    "group": {
                        "type": "string",
                        "enum": ["all", "ally", "enemy", "item", "gadget", "npc"],
                    },
                },
                "minProperties": 1,
                "additionalProperties": False,
            },
        },
    ]


class Py4GWMcpServer:
    def __init__(self, daemon_host: str, daemon_port: int, timeout: float):
        self.daemon_host = daemon_host
        self.daemon_port = daemon_port
        self.timeout = timeout

    def _target_params(self, arguments: dict[str, Any]) -> dict[str, Any]:
        target: dict[str, Any] = {}
        hwnd = arguments.get("hwnd")
        pid = arguments.get("pid")
        if hwnd is not None:
            target["hwnd"] = int(hwnd)
        if pid is not None:
            target["pid"] = int(pid)
        if not target:
            raise ValueError("Provide hwnd or pid")
        return {"target": target}

    def _call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "list_clients":
            return _daemon_request(self.daemon_host, self.daemon_port, "system.list_clients", timeout=self.timeout)
        if name == "list_namespaces":
            return _daemon_request(
                self.daemon_host,
                self.daemon_port,
                "client.list_namespaces",
                self._target_params(arguments),
                timeout=self.timeout,
            )
        if name == "list_commands":
            return _daemon_request(
                self.daemon_host,
                self.daemon_port,
                "client.list_commands",
                self._target_params(arguments),
                timeout=self.timeout,
            )
        if name == "describe_runtime":
            return _daemon_request(
                self.daemon_host,
                self.daemon_port,
                "client.describe_runtime",
                self._target_params(arguments),
                timeout=self.timeout,
            )
        if name == "get_map_state":
            return _daemon_request(
                self.daemon_host,
                self.daemon_port,
                "client.get_map_state",
                self._target_params(arguments),
                timeout=self.timeout,
            )
        if name == "get_player_state":
            return _daemon_request(
                self.daemon_host,
                self.daemon_port,
                "client.get_player_state",
                self._target_params(arguments),
                timeout=self.timeout,
            )
        if name == "list_agents":
            params = self._target_params(arguments)
            if "group" in arguments and arguments.get("group") is not None:
                params["group"] = str(arguments["group"])
            return _daemon_request(
                self.daemon_host,
                self.daemon_port,
                "client.list_agents",
                params,
                timeout=self.timeout,
            )
        raise ValueError(f"Unknown tool: {name}")

    def _handle_initialize(self, msg_id: Any) -> dict[str, Any]:
        return _make_jsonrpc_result(
            msg_id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )

    def _handle_tools_list(self, msg_id: Any) -> dict[str, Any]:
        return _make_jsonrpc_result(msg_id, {"tools": _tool_list()})

    def _handle_tools_call(self, msg_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        name = str(params.get("name") or "")
        arguments = params.get("arguments", {})
        if not name:
            return _make_jsonrpc_error(msg_id, -32602, "tools/call requires a tool name")
        if not isinstance(arguments, dict):
            return _make_jsonrpc_error(msg_id, -32602, "tools/call arguments must be an object")
        try:
            result = self._call_tool(name, arguments)
        except ValueError as exc:
            return _make_jsonrpc_error(msg_id, -32602, str(exc))
        except Exception as exc:
            return _make_jsonrpc_error(msg_id, -32000, str(exc))
        return _make_jsonrpc_result(
            msg_id,
            {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2, ensure_ascii=False),
                    }
                ],
                "structuredContent": result,
                "isError": not bool(result.get("ok", False)),
            },
        )

    def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = str(message.get("method") or "")
        msg_id = message.get("id")
        params = message.get("params", {})
        if not isinstance(params, dict):
            params = {}
        if method == "initialize":
            return self._handle_initialize(msg_id)
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return _make_jsonrpc_result(msg_id, {})
        if method == "tools/list":
            return self._handle_tools_list(msg_id)
        if method == "tools/call":
            return self._handle_tools_call(msg_id, params)
        if msg_id is None:
            return None
        return _make_jsonrpc_error(msg_id, -32601, f"Method not found: {method}")

    def run(self) -> int:
        while True:
            try:
                message = _read_stdio_message()
            except Exception as exc:
                _write_stdio_message(_make_jsonrpc_error(None, -32700, f"Parse error: {exc}"))
                return 1
            if message is None:
                return 0
            response = self.handle_message(message)
            if response is not None:
                _write_stdio_message(response)


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal MCP server for the Py4GW bridge daemon")
    parser.add_argument("--host", default="127.0.0.1", help="Bridge daemon control host")
    parser.add_argument("--port", type=int, default=47812, help="Bridge daemon control port")
    parser.add_argument("--timeout", type=float, default=5.0, help="Bridge daemon request timeout seconds")
    args = parser.parse_args()
    server = Py4GWMcpServer(args.host, args.port, args.timeout)
    try:
        return server.run()
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
