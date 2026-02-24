import os
import queue
import socket
import threading
import time
import traceback
import inspect
from dataclasses import is_dataclass, asdict
from typing import Any

import PyImGui
import Py4GW

from BridgeRuntime.protocol import (
    PROTOCOL_VERSION,
    make_error_response,
    make_response,
    recv_json_message,
    send_json_message,
)
from Py4GWCoreLib import (
    GLOBAL_CACHE,
    ImGui,
    Map,
    Player,
    AgentArray,
    Agent,
    Party,
    Skill,
    SkillBar,
    Inventory,
    Quest,
    Effects,
    Color,
)
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType

MODULE_NAME = "Bridge Client"
OPTIONAL = True

__widget__ = {
    "name": "Bridge Client",
    "enabled": False,
    "category": "System",
    "subcategory": "Bridge",
    "icon": "ICON_SITEMAP",
    "quickdock": False,
    "hidden": False,
}

INI_KEY = ""
INI_PATH = "Widgets/BridgeClient"
INI_FILENAME = "BridgeClient.ini"


def _now_ms() -> int:
    return int(time.time() * 1000)

port = 47811
class BridgeClientState:
    def __init__(self):
        self.daemon_host = "127.0.0.1"
        self.daemon_port = port
        self.auth_token = ""
        self.sock: socket.socket | None = None
        self.socket_thread: threading.Thread | None = None
        self.stop_evt = threading.Event()
        self.inbox: "queue.Queue[dict[str, Any]]" = queue.Queue()
        self.outbox: "queue.Queue[dict[str, Any]]" = queue.Queue()
        self.pending_ops: dict[str, dict[str, Any]] = {}
        self.connected = False
        self.session_id = ""
        self.last_error = ""
        self.last_connect_attempt_ms = 0
        self.last_heartbeat_ms = 0
        self.requests_processed = 0
        self.responses_sent = 0
        self.cleanup_ttl_ms = 60_000
        self.heartbeat_interval_ms = 2000
        self.ui_host = "127.0.0.1"
        self.ui_port = port
        self.ui_token = ""

    def get_hwnd(self) -> int:
        try:
            return int(Py4GW.Console.get_gw_window_handle())
        except Exception:
            return 0

    def get_pid(self) -> int:
        return int(os.getpid())

    def get_client_meta(self) -> dict[str, Any]:
        try:
            account_email = Player.GetAccountEmail()
        except Exception:
            account_email = ""
        try:
            character_name = Player.GetName() if Player.IsPlayerLoaded() else ""
        except Exception:
            character_name = ""
        return {
            "hwnd": self.get_hwnd(),
            "pid": self.get_pid(),
            "account_email": account_email,
            "character_name": character_name,
        }

    def start(self):
        if self.socket_thread and self.socket_thread.is_alive():
            return
        self.stop_evt.clear()
        self.socket_thread = threading.Thread(target=self._socket_loop, daemon=True)
        self.socket_thread.start()

    def stop(self):
        self.stop_evt.set()
        self.connected = False
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass
        self.sock = None

    def _enqueue_response(self, response: dict[str, Any]):
        self.outbox.put(response)

    def _send_heartbeat(self):
        if not self.sock:
            return
        now = _now_ms()
        if now - self.last_heartbeat_ms < self.heartbeat_interval_ms:
            return
        self.last_heartbeat_ms = now
        self.outbox.put(
            {
                "type": "heartbeat",
                "protocol_version": PROTOCOL_VERSION,
                "client": self.get_client_meta(),
            }
        )

    def _flush_outbox(self):
        if not self.sock:
            return
        while True:
            try:
                msg = self.outbox.get_nowait()
            except queue.Empty:
                break
            send_json_message(self.sock, msg)
            self.responses_sent += 1

    def _try_connect(self):
        now = _now_ms()
        if now - self.last_connect_attempt_ms < 1000:
            return
        self.last_connect_attempt_ms = now
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.connect((self.daemon_host, self.daemon_port))
            self.sock = sock
            self.connected = True
            self.last_error = ""
            send_json_message(
                sock,
                {
                    "type": "hello",
                    "protocol_version": PROTOCOL_VERSION,
                    "token": self.auth_token,
                    "client": self.get_client_meta(),
                },
            )
        except Exception as exc:
            self.connected = False
            self.last_error = f"connect: {exc}"
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

    def _socket_loop(self):
        while not self.stop_evt.is_set():
            if not self.connected:
                self._try_connect()
                time.sleep(0.25)
                continue
            try:
                self._flush_outbox()
                self._send_heartbeat()
                msg = recv_json_message(self.sock, timeout=0.2)  # type: ignore[arg-type]
                mtype = str(msg.get("type") or "")
                if mtype == "request":
                    self.inbox.put(msg)
                elif mtype == "hello_ack":
                    self.session_id = str(msg.get("session_id") or "")
            except socket.timeout:
                continue
            except Exception as exc:
                self.last_error = f"socket: {exc}"
                self.connected = False
                try:
                    if self.sock:
                        self.sock.close()
                except Exception:
                    pass
                self.sock = None
                time.sleep(1.0)


STATE = BridgeClientState()


def _add_config_vars():
    IniManager().add_str(INI_KEY, "daemon_host", "Connection", "host", default="127.0.0.1")
    IniManager().add_int(INI_KEY, "daemon_port", "Connection", "port", default=port)
    IniManager().add_str(INI_KEY, "auth_token", "Connection", "token", default="")


def _load_settings():
    STATE.daemon_host = str(IniManager().get(INI_KEY, "daemon_host", "127.0.0.1", section="Connection"))
    STATE.daemon_port = int(IniManager().get(INI_KEY, "daemon_port", port, section="Connection"))
    STATE.auth_token = str(IniManager().get(INI_KEY, "auth_token", "", section="Connection"))
    STATE.ui_host = STATE.daemon_host
    STATE.ui_port = STATE.daemon_port
    STATE.ui_token = STATE.auth_token


def _save_setting(name: str, value: Any):
    IniManager().set(INI_KEY, name, value, section="Connection")
    IniManager().save_vars(INI_KEY)


def _apply_connection_settings():
    new_host = str(STATE.ui_host or "127.0.0.1")
    try:
        new_port = int(STATE.ui_port)
    except Exception:
        new_port = port
    new_port = max(1, min(65535, new_port))
    new_token = str(STATE.ui_token or "")

    changed = (
        new_host != STATE.daemon_host
        or new_port != STATE.daemon_port
        or new_token != STATE.auth_token
    )

    STATE.ui_host = new_host
    STATE.ui_port = new_port
    STATE.ui_token = new_token

    if not changed:
        return

    STATE.daemon_host = new_host
    STATE.daemon_port = new_port
    STATE.auth_token = new_token
    _save_setting("daemon_host", new_host)
    _save_setting("daemon_port", new_port)
    _save_setting("auth_token", new_token)
    STATE.stop()
    STATE.start()


def _coerce_input_text_result(result: Any, previous: str) -> tuple[bool, str]:
    if isinstance(result, tuple) and len(result) >= 2:
        return bool(result[0]), str(result[1])
    if isinstance(result, str):
        return result != previous, result
    return False, previous


def _coerce_input_int_result(result: Any, previous: int) -> tuple[bool, int]:
    if isinstance(result, tuple) and len(result) >= 2:
        return bool(result[0]), int(result[1])
    if isinstance(result, int):
        return result != previous, int(result)
    return False, previous


def _map_state() -> dict[str, Any]:
    region_id, region_name = Map.GetRegion()
    language_id, language_name = Map.GetLanguage()
    return {
        "source_mode": "native",
        "map_data_loaded": bool(Map.IsMapDataLoaded()),
        "map_ready": bool(Map.IsMapReady()),
        "is_loading": bool(Map.IsMapLoading()),
        "is_cinematic": bool(Map.IsInCinematic()),
        "is_outpost": bool(Map.IsOutpost()),
        "is_explorable": bool(Map.IsExplorable()),
        "instance_type": {"id": int(Map.GetInstanceType()), "name": Map.GetInstanceTypeName()},
        "map": {"id": int(Map.GetMapID()), "name": Map.GetMapName()},
        "region": {"id": int(region_id), "name": region_name},
        "language": {"id": int(language_id), "name": language_name},
    }


def _player_state() -> dict[str, Any]:
    map_ready = bool(Map.IsMapReady())
    player_loaded = bool(Player.IsPlayerLoaded()) if map_ready else False
    result = {"source_mode": "hybrid", "map_ready": map_ready, "player_loaded": player_loaded, "player": None}
    if not player_loaded:
        return result
    x, y = Player.GetXY()
    result["player"] = {
        "agent_id": int(Player.GetAgentID()),
        "name": Player.GetName(),
        "account_name": Player.GetAccountName(),
        "account_email": Player.GetAccountEmail(),
        "target_id": int(Player.GetTargetID()),
        "position": {"x": float(x), "y": float(y)},
        "hwnd": STATE.get_hwnd(),
        "pid": STATE.get_pid(),
    }
    return result


def _register_op(request_id: str, op: dict[str, Any]) -> None:
    now = _now_ms()
    op["request_id"] = request_id
    op.setdefault("created_ms", now)
    op["updated_ms"] = now
    STATE.pending_ops[request_id] = op


def _set_op_state(request_id: str, state: str, error: dict[str, Any] | None = None):
    op = STATE.pending_ops.get(request_id)
    if not op:
        return
    op["state"] = state
    op["updated_ms"] = _now_ms()
    if error is not None:
        op["error"] = error


def _status_payload(op: dict[str, Any]) -> dict[str, Any]:
    return {
        "request_id": op.get("request_id"),
        "state": op.get("state"),
        "kind": op.get("kind"),
        "created_ms": op.get("created_ms"),
        "updated_ms": op.get("updated_ms"),
        "meta": op.get("meta", {}),
        "error": op.get("error"),
    }


def _jsonable(value: Any, _depth: int = 0) -> Any:
    if _depth > 4:
        return repr(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if is_dataclass(value):
        try:
            return _jsonable(asdict(value), _depth + 1)
        except Exception:
            return repr(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v, _depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v, _depth + 1) for v in value]
    if hasattr(value, "value") and isinstance(getattr(value, "value"), (int, str)):
        # enum-like
        try:
            return {"value": value.value, "name": getattr(value, "name", str(value))}
        except Exception:
            pass
    for attr in ("x", "y", "z"):
        if hasattr(value, attr):
            try:
                coords = {k: float(getattr(value, k)) for k in ("x", "y", "z") if hasattr(value, k)}
                if coords:
                    return coords
            except Exception:
                break
    if hasattr(value, "__dict__"):
        try:
            return {
                "__type__": value.__class__.__name__,
                "fields": {k: _jsonable(v, _depth + 1) for k, v in vars(value).items() if not k.startswith("_")},
            }
        except Exception:
            return repr(value)
    return repr(value)


def _list_public_callables(target: Any) -> list[dict[str, Any]]:
    methods: list[dict[str, Any]] = []
    for name in dir(target):
        if name.startswith("_"):
            continue
        try:
            fn = getattr(target, name)
        except Exception:
            continue
        if not callable(fn):
            continue
        sig = ""
        try:
            sig = str(inspect.signature(fn))
        except Exception:
            sig = "(...)"
        methods.append({"name": name, "signature": sig})
    methods.sort(key=lambda m: m["name"])
    return methods


def _invoke_class_method(target: Any, class_name: str, params: dict[str, Any], request_id: str) -> dict[str, Any]:
    method_name = str(params.get("method") or "")
    if not method_name:
        return make_error_response(request_id, "validation_method", "method required")
    if method_name.startswith("_"):
        return make_error_response(request_id, "validation_method", "private methods are blocked")
    try:
        fn = getattr(target, method_name)
    except AttributeError:
        return make_error_response(request_id, "not_supported", f"{class_name}.{method_name} not found")
    if not callable(fn):
        return make_error_response(request_id, "validation_method", f"{class_name}.{method_name} is not callable")

    args = params.get("args", [])
    kwargs = params.get("kwargs", {})
    if not isinstance(args, list):
        return make_error_response(request_id, "validation_args", "args must be list")
    if not isinstance(kwargs, dict):
        return make_error_response(request_id, "validation_kwargs", "kwargs must be object")

    try:
        result = fn(*args, **kwargs)
        return make_response(
            request_id,
            {
                "class": class_name,
                "method": method_name,
                "result": _jsonable(result),
            },
        )
    except Exception as exc:
        return make_error_response(request_id, "execution_error", f"{class_name}.{method_name}: {exc}")


def _generic_targets() -> dict[str, tuple[str, Any]]:
    return {
        # Native / wrapper layers
        "map": ("Map", Map),
        "player": ("Player", Player),
        "agent": ("Agent", Agent),
        "agent_array": ("AgentArray", AgentArray),
        "party_raw": ("Party", Party),
        "skill": ("Skill", Skill),
        "skillbar_raw": ("SkillBar", SkillBar),
        "inventory_raw": ("Inventory", Inventory),
        "quest_raw": ("Quest", Quest),
        "effects_raw": ("Effects", Effects),
        # Cache / service layers
        "party": ("GLOBAL_CACHE.Party", GLOBAL_CACHE.Party),
        "party.players": ("GLOBAL_CACHE.Party.Players", GLOBAL_CACHE.Party.Players),
        "party.heroes": ("GLOBAL_CACHE.Party.Heroes", GLOBAL_CACHE.Party.Heroes),
        "party.henchmen": ("GLOBAL_CACHE.Party.Henchmen", GLOBAL_CACHE.Party.Henchmen),
        "party.pets": ("GLOBAL_CACHE.Party.Pets", GLOBAL_CACHE.Party.Pets),
        "skillbar": ("GLOBAL_CACHE.SkillBar", GLOBAL_CACHE.SkillBar),
        "inventory": ("GLOBAL_CACHE.Inventory", GLOBAL_CACHE.Inventory),
        "quest": ("GLOBAL_CACHE.Quest", GLOBAL_CACHE.Quest),
        "effects": ("GLOBAL_CACHE.Effects", GLOBAL_CACHE.Effects),
        "shmem": ("GLOBAL_CACHE.ShMem", GLOBAL_CACHE.ShMem),
    }


def _handle_command(request: dict[str, Any]) -> dict[str, Any]:
    request_id = str(request.get("request_id") or "")
    command = str(request.get("command") or "")
    params = request.get("params", {})
    if not isinstance(params, dict):
        return make_error_response(request_id, "validation_params", "params must be object")

    try:
        if command == "system.ping":
            return make_response(request_id, {"pong": True, "time_ms": _now_ms()})

        if command == "system.list_namespaces":
            targets = _generic_targets()
            return make_response(
                request_id,
                {
                    "namespaces": sorted(targets.keys()),
                    "note": "Use <namespace>.list_methods and <namespace>.call",
                },
            )

        if command == "client.describe":
            return make_response(
                request_id,
                {
                    "session_id": STATE.session_id,
                    "connected": STATE.connected,
                    "client": STATE.get_client_meta(),
                    "metrics": {
                        "pending_ops": len(STATE.pending_ops),
                        "requests_processed": STATE.requests_processed,
                        "responses_sent": STATE.responses_sent,
                    },
                },
            )

        if command == "map.get_state":
            return make_response(request_id, _map_state())

        if command == "player.get_state":
            return make_response(request_id, _player_state())

        if command == "agent.list":
            group = str(params.get("group") or "all").lower()
            getter_map = {
                "all": AgentArray.GetAgentArray,
                "ally": AgentArray.GetAllyArray,
                "enemy": AgentArray.GetEnemyArray,
                "item": AgentArray.GetItemArray,
                "gadget": AgentArray.GetGadgetArray,
                "npc": AgentArray.GetNPCMinipetArray,
            }
            getter = getter_map.get(group)
            if getter is None:
                return make_error_response(request_id, "validation_group", f"unsupported group: {group}")
            return make_response(request_id, {"group": group, "agents": [int(a) for a in getter()]})

        if command == "agent.get_info":
            agent_id = int(params.get("agent_id") or 0)
            if agent_id <= 0 or not Agent.IsValid(agent_id):
                return make_error_response(request_id, "invalid_agent", "agent not valid")
            x, y = Agent.GetXY(agent_id)
            return make_response(
                request_id,
                {
                    "agent_id": agent_id,
                    "xy": {"x": float(x), "y": float(y)},
                    "z_plane": int(Agent.GetZPlane(agent_id)),
                },
            )

        if command.endswith(".list_methods") or command.endswith(".call"):
            namespace, suffix = command.rsplit(".", 1)
            targets = _generic_targets()
            target_info = targets.get(namespace)
            if target_info is not None:
                display_name, target_obj = target_info
                if suffix == "list_methods":
                    return make_response(
                        request_id,
                        {"namespace": namespace, "class": display_name, "methods": _list_public_callables(target_obj)},
                    )
                if suffix == "call":
                    return _invoke_class_method(target_obj, display_name, params, request_id)

        if command == "map.travel":
            map_id = int(params.get("map_id") or 0)
            if map_id <= 0:
                return make_error_response(request_id, "invalid_map_id", "map_id must be > 0")
            if bool(params.get("reject_if_loading", True)) and Map.IsMapLoading():
                return make_error_response(request_id, "guard_map_loading", "map is loading", retryable=True)
            if bool(params.get("reject_if_cinematic", True)) and Map.IsInCinematic():
                return make_error_response(request_id, "guard_cinematic", "in cinematic", retryable=True)
            mode = str(params.get("mode") or "travel")
            if mode == "region":
                Map.TravelToRegion(
                    map_id,
                    int(params.get("server_region") or 0),
                    int(params.get("district_number") or 0),
                    int(params.get("language") or 0),
                )
            elif mode == "district":
                Map.TravelToDistrict(
                    map_id,
                    int(params.get("district") or 0),
                    int(params.get("district_number") or 0),
                )
            else:
                Map.Travel(map_id)
            _register_op(
                request_id,
                {
                    "state": "queued",
                    "kind": "local_queue",
                    "meta": {"action": "map.travel", "map_id": map_id},
                    "probe": {"type": "map_id", "map_id": map_id},
                },
            )
            return make_response(request_id, {"accepted": True, "result_mode": "queued", "queue": "ACTION"})

        if command == "map.skip_cinematic":
            if bool(params.get("reject_if_not_cinematic", True)) and not Map.IsInCinematic():
                return make_error_response(request_id, "guard_not_cinematic", "not in cinematic")
            Map.SkipCinematic()
            _register_op(
                request_id,
                {
                    "state": "queued",
                    "kind": "local_queue",
                    "meta": {"action": "map.skip_cinematic"},
                    "probe": {"type": "not_cinematic"},
                },
            )
            return make_response(request_id, {"accepted": True, "result_mode": "queued", "queue": "TRANSITION"})

        if command == "ops.get_status":
            tracked_id = str(params.get("request_id") or "")
            if not tracked_id:
                return make_error_response(request_id, "validation_request_id", "request_id required")
            op = STATE.pending_ops.get(tracked_id)
            if op is None:
                return make_response(request_id, {"request_id": tracked_id, "state": "expired"})
            return make_response(request_id, _status_payload(op))

        if command == "shmem.send_command":
            sender_email = Player.GetAccountEmail()
            receiver_email = str(params.get("receiver_email") or "")
            if not receiver_email:
                return make_error_response(request_id, "validation_receiver", "receiver_email required")
            raw_command = params.get("command")
            if isinstance(raw_command, str):
                try:
                    command_enum = SharedCommandType[raw_command]
                except KeyError:
                    return make_error_response(request_id, "validation_command", f"unknown command: {raw_command}")
            else:
                try:
                    command_enum = SharedCommandType(int(raw_command))
                except Exception:
                    return make_error_response(request_id, "validation_command", "invalid command")
            raw_params = params.get("msg_params", [0, 0, 0, 0])
            if not isinstance(raw_params, (list, tuple)):
                return make_error_response(request_id, "validation_msg_params", "msg_params must be list")
            msg_params = [float(v) for v in list(raw_params)[:4]]
            while len(msg_params) < 4:
                msg_params.append(0.0)
            extra_data = params.get("extra_data", [])
            if not isinstance(extra_data, (list, tuple)):
                return make_error_response(request_id, "validation_extra_data", "extra_data must be list")
            msg_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                receiver_email,
                command_enum,
                tuple(msg_params),
                tuple(str(v) for v in extra_data),
            )
            if msg_index < 0:
                return make_error_response(request_id, "shmem_send_failed", "shared memory send failed")
            _register_op(
                request_id,
                {
                    "state": "queued",
                    "kind": "remote_message",
                    "meta": {"receiver_email": receiver_email, "message_index": int(msg_index), "command": command_enum.name},
                    "probe": {"type": "shmem_message", "receiver_email": receiver_email, "message_index": int(msg_index)},
                },
            )
            return make_response(
                request_id,
                {
                    "accepted": True,
                    "result_mode": "async",
                    "transport": "shmem",
                    "message_index": int(msg_index),
                    "receiver_email": receiver_email,
                },
            )

        return make_error_response(request_id, "not_supported", f"unsupported command: {command}")
    except Exception as exc:
        return make_error_response(request_id, "internal_error", str(exc))


def _update_pending_ops():
    now = _now_ms()
    for request_id, op in list(STATE.pending_ops.items()):
        state = str(op.get("state") or "")
        if state in {"completed", "failed"}:
            if now - int(op.get("updated_ms", now)) > STATE.cleanup_ttl_ms:
                STATE.pending_ops.pop(request_id, None)
            continue
        probe = op.get("probe", {})
        if not isinstance(probe, dict):
            continue
        try:
            ptype = probe.get("type")
            if ptype == "map_id":
                target_map_id = int(probe.get("map_id") or 0)
                if target_map_id > 0 and Map.IsMapReady() and Map.GetMapID() == target_map_id:
                    _set_op_state(request_id, "completed")
            elif ptype == "not_cinematic":
                if not Map.IsInCinematic():
                    _set_op_state(request_id, "completed")
            elif ptype == "shmem_message":
                receiver = str(probe.get("receiver_email") or "")
                target_index = int(probe.get("message_index") or -1)
                found = False
                for msg_index, message in GLOBAL_CACHE.ShMem.GetAllMessages():
                    if int(msg_index) != target_index:
                        continue
                    if str(getattr(message, "ReceiverEmail", "")) != receiver:
                        continue
                    found = True
                    active = bool(getattr(message, "Active", False))
                    running = bool(getattr(message, "Running", False))
                    if running:
                        _set_op_state(request_id, "running")
                    if not active and not running:
                        _set_op_state(request_id, "completed")
                    break
                if not found:
                    _set_op_state(request_id, "completed")
        except Exception as exc:
            _set_op_state(request_id, "failed", {"code": "probe_error", "message": str(exc)})


def _process_inbox():
    while True:
        try:
            request = STATE.inbox.get_nowait()
        except queue.Empty:
            break
        request_id = str(request.get("request_id") or "")
        try:
            response = _handle_command(request)
        except Exception as exc:
            response = make_error_response(request_id, "internal_error", str(exc))
        STATE._enqueue_response(response)
        STATE.requests_processed += 1


def tooltip():
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.text("TCP bridge client for the external bridge daemon.")
    PyImGui.text("Executes namespaced commands in the injected runtime.")
    PyImGui.end_tooltip()


def draw():
    if not INI_KEY:
        return
    if ImGui.Begin(INI_KEY, MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text(f"Connected: {STATE.connected}")
        PyImGui.text(f"Daemon: {STATE.daemon_host}:{STATE.daemon_port}")
        PyImGui.text(f"HWND: {STATE.get_hwnd()}")
        PyImGui.text(f"PID: {STATE.get_pid()}")
        PyImGui.text(f"Session: {STATE.session_id or '-'}")
        PyImGui.separator()
        PyImGui.text(f"Inbox: {STATE.inbox.qsize()}")
        PyImGui.text(f"Outbox: {STATE.outbox.qsize()}")
        PyImGui.text(f"Pending ops: {len(STATE.pending_ops)}")
        PyImGui.text(f"Req processed: {STATE.requests_processed}")
        PyImGui.text(f"Resp sent: {STATE.responses_sent}")
        if STATE.last_error:
            PyImGui.separator()
            PyImGui.text_wrapped(f"Last error: {STATE.last_error}")

        _, STATE.ui_host = _coerce_input_text_result(
            PyImGui.input_text("Host", STATE.ui_host),
            STATE.ui_host,
        )

        _, STATE.ui_port = _coerce_input_int_result(
            PyImGui.input_int("Port", int(STATE.ui_port)),
            int(STATE.ui_port),
        )

        # Some PyImGui builds in this project do not support the password-flags overload.
        _, STATE.ui_token = _coerce_input_text_result(
            PyImGui.input_text("Token", STATE.ui_token),
            STATE.ui_token,
        )

        if PyImGui.button("Apply Connection Settings"):
            _apply_connection_settings()
        PyImGui.same_line(0, 8)
        if PyImGui.button("Reset Draft"):
            STATE.ui_host = STATE.daemon_host
            STATE.ui_port = STATE.daemon_port
            STATE.ui_token = STATE.auth_token

        if PyImGui.button("Reconnect"):
            STATE.stop()
            STATE.start()
    ImGui.End(INI_KEY)


def main():
    global INI_KEY
    try:
        if not INI_KEY:
            INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not INI_KEY:
                return
            _add_config_vars()
            IniManager().load_once(INI_KEY)
            _load_settings()
            STATE.start()
        _process_inbox()
        _update_pending_ops()
    except Exception as exc:
        STATE.last_error = f"main: {exc}"
        try:
            Py4GW.Console.Log(MODULE_NAME, traceback.format_exc(), Py4GW.Console.MessageType.Error)
        except Exception:
            pass


if __name__ == "__main__":
    main()
