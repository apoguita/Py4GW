from __future__ import annotations

import ctypes
import importlib
import os
from pathlib import Path
import shutil
import sys
import types
from types import SimpleNamespace
import uuid


class _FakeTimer:
    def __init__(self, _ms: int = 0) -> None:
        self._expired = True

    def IsExpired(self) -> bool:  # noqa: N802 - mirrors runtime API
        return bool(self._expired)

    def Reset(self) -> None:  # noqa: N802 - mirrors runtime API
        self._expired = True


class _FakeSharedMsg:
    def __init__(
        self,
        *,
        receiver_email: str,
        sender_email: str,
        command: int,
        extra_data: list[str],
        params: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0),
    ) -> None:
        self.ReceiverEmail = receiver_email
        self.SenderEmail = sender_email
        self.Command = int(command)
        self.ExtraData = list(extra_data)
        self.Params = tuple(params)


class _FakeShMem:
    def __init__(self, messages: list[tuple[int, _FakeSharedMsg]]) -> None:
        self._messages = list(messages)
        self.finished: list[int] = []

    def GetAllMessages(self):  # noqa: N802 - mirrors runtime API
        return list(self._messages)

    def MarkMessageAsFinished(self, _receiver_email: str, idx: int):  # noqa: N802
        self.finished.append(int(idx))

    def GetAccountDataFromEmail(self, _email: str):  # noqa: N802
        return None


def _install_runtime_stubs(monkeypatch, tmp_path: Path):
    class _MessageType:
        Info = 0
        Warning = 1
        Error = 2

    class _Console:
        MessageType = _MessageType

        @staticmethod
        def Log(*_args, **_kwargs):  # noqa: N802 - runtime API
            return None

        @staticmethod
        def get_projects_path():  # noqa: N802 - runtime API
            return str(tmp_path)

    class _Player:
        @staticmethod
        def GetAccountEmail():  # noqa: N802 - runtime API
            return "self@test"

        @staticmethod
        def GetAgentID():  # noqa: N802 - runtime API
            return 1

        @staticmethod
        def GetName():  # noqa: N802 - runtime API
            return "Leader"

        @staticmethod
        def IsChatHistoryReady():  # noqa: N802 - runtime API
            return True

        @staticmethod
        def GetChatHistory():  # noqa: N802 - runtime API
            return []

        @staticmethod
        def player_instance():  # noqa: N802 - runtime API
            return SimpleNamespace(RequestChatHistory=lambda: None)

    class _Party:
        @staticmethod
        def GetPartyLeaderID():  # noqa: N802 - runtime API
            return 1

    class _Map:
        @staticmethod
        def GetMapID():  # noqa: N802 - runtime API
            return 1

        @staticmethod
        def GetMapName(_map_id):  # noqa: N802 - runtime API
            return "Map"

    pyinventory_mod = types.ModuleType("PyInventory")
    pyagent_mod = types.ModuleType("PyAgent")
    py4gw_runtime_mod = types.ModuleType("Py4GW")
    py4gw_runtime_mod.Console = _Console

    py4gw_mod = types.ModuleType("Py4GWCoreLib")
    py4gw_mod.__path__ = []  # type: ignore[attr-defined]
    py4gw_mod.GLOBAL_CACHE = SimpleNamespace(ShMem=None, Inventory=SimpleNamespace())
    py4gw_mod.Player = _Player
    py4gw_mod.Party = _Party
    py4gw_mod.Map = _Map
    py4gw_mod.Py4GW = SimpleNamespace(Console=_Console)
    py4gw_mod.Routines = SimpleNamespace(
        Checks=SimpleNamespace(Map=SimpleNamespace(MapValid=lambda: True))
    )
    py4gw_mod.SharedCommandType = SimpleNamespace(CustomBehaviors=SimpleNamespace(value=997))
    py4gw_mod.ThrottledTimer = _FakeTimer
    py4gw_mod.__all__ = [
        "GLOBAL_CACHE",
        "Player",
        "Party",
        "Map",
        "Py4GW",
        "Routines",
        "ThrottledTimer",
        "SharedCommandType",
    ]

    item_mod = types.ModuleType("Py4GWCoreLib.Item")
    item_mod.Item = SimpleNamespace(
        Type=SimpleNamespace(
            IsTome=lambda _item_id: False,
            IsMaterial=lambda _item_id: False,
            IsRareMaterial=lambda _item_id: False,
        ),
        Usage=SimpleNamespace(IsIdentified=lambda _item_id: True),
        IsNameReady=lambda _item_id: True,
        GetName=lambda _item_id: "Item",
        RequestName=lambda _item_id: None,
    )
    itemarray_mod = types.ModuleType("Py4GWCoreLib.ItemArray")
    itemarray_mod.ItemArray = SimpleNamespace(
        CreateBagList=lambda *_args: [],
        GetItemArray=lambda _bags: [],
    )

    helpers_mod = types.ModuleType("Py4GWCoreLib.native_src.internals.helpers")
    helpers_mod.encoded_wstr_to_str = lambda value: str(value)
    native_mod = types.ModuleType("Py4GWCoreLib.native_src")
    native_mod.__path__ = []  # type: ignore[attr-defined]
    internals_mod = types.ModuleType("Py4GWCoreLib.native_src.internals")
    internals_mod.__path__ = []  # type: ignore[attr-defined]

    corelib_mod = types.ModuleType("Py4GWCoreLib.Py4GWcorelib")
    corelib_mod.ThrottledTimer = _FakeTimer

    enums_mod = types.ModuleType("Py4GWCoreLib.enums")
    enums_mod.SharedCommandType = py4gw_mod.SharedCommandType

    widget_manager_mod = types.ModuleType("Py4GWCoreLib.py4gwcorelib_src.WidgetManager")
    widget_manager_mod.get_widget_handler = lambda: SimpleNamespace(
        get_widget_info=lambda _name: None,
        is_widget_enabled=lambda _name: False,
        disable_widget=lambda _name: None,
        enable_widget=lambda _name: None,
    )
    py4gwcorelib_src_mod = types.ModuleType("Py4GWCoreLib.py4gwcorelib_src")
    py4gwcorelib_src_mod.__path__ = []  # type: ignore[attr-defined]
    globalcache_mod = types.ModuleType("Py4GWCoreLib.GlobalCache")
    globalcache_mod.__path__ = []  # type: ignore[attr-defined]
    sharedmemory_mod = types.ModuleType("Py4GWCoreLib.GlobalCache.SharedMemory")
    sharedmemory_mod.AccountStruct = object

    monkeypatch.setitem(sys.modules, "PyInventory", pyinventory_mod)
    monkeypatch.setitem(sys.modules, "PyAgent", pyagent_mod)
    monkeypatch.setitem(sys.modules, "Py4GW", py4gw_runtime_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib", py4gw_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.Item", item_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.ItemArray", itemarray_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.native_src", native_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.native_src.internals", internals_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.native_src.internals.helpers", helpers_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.Py4GWcorelib", corelib_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.enums", enums_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.py4gwcorelib_src", py4gwcorelib_src_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.GlobalCache", globalcache_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.GlobalCache.SharedMemory", sharedmemory_mod)
    monkeypatch.setitem(
        sys.modules,
        "Py4GWCoreLib.py4gwcorelib_src.WidgetManager",
        widget_manager_mod,
    )

    from Sources.oazix.CustomBehaviors.primitives import constants

    monkeypatch.setattr(constants, "DROP_LOG_PATH", str(tmp_path / "drop_log.csv"), raising=False)
    return py4gw_mod


def _import_start_drop_viewer(monkeypatch, tmp_path):
    py4gw_mod = _install_runtime_stubs(monkeypatch, tmp_path)
    module_name = "Sources.oazix.CustomBehaviors.start_drop_viewer"
    sys.modules.pop(module_name, None)
    module = importlib.import_module(module_name)
    return module, py4gw_mod


def _make_local_tmp_dir() -> Path:
    root = Path(os.getcwd()) / ".pytest_local_tmp"
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"drop_viewer_polling_{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _wch(text: str, width: int = 96):
    buf = (ctypes.c_wchar * int(width))()
    safe = str(text or "")[: max(0, width - 1)]
    for idx, ch in enumerate(safe):
        buf[idx] = ch
    buf[len(safe)] = "\0"
    return buf


def test_poll_shared_memory_mixed_backlog_processes_non_action_message(monkeypatch):
    from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_actions import InventoryActionStatus

    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20

    action_calls: list[tuple[str, str, str, str]] = []
    sent_stats_responses: list[str] = []

    def _fake_run_inventory_action(action_code, action_payload, action_meta, sender_email):
        action_calls.append((str(action_code), str(action_payload), str(action_meta), str(sender_email)))
        return module.InventoryActionResult(status=InventoryActionStatus.DEFERRED)

    viewer._run_inventory_action = _fake_run_inventory_action
    viewer._send_inventory_kit_stats_response = lambda email: sent_stats_responses.append(str(email))

    messages: list[tuple[int, _FakeSharedMsg]] = []
    for idx in range(100):
        messages.append(
            (
                idx,
                _FakeSharedMsg(
                    receiver_email="self@test",
                    sender_email="peer@test",
                    command=997,
                    extra_data=[viewer.inventory_action_tag, "push_item_stats_event", "1", f"ev-{idx}"],
                ),
            )
        )
    request_idx = 100
    messages.append(
        (
            request_idx,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=[viewer.inventory_stats_request_tag],
            ),
        )
    )
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert len(action_calls) == 8
        assert request_idx in py4gw_mod.GLOBAL_CACHE.ShMem.finished
        assert sent_stats_responses == ["peer@test"]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_poll_shared_memory_advances_scan_cursor_with_large_message_batches(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20

    messages = [
        (
            idx,
            _FakeSharedMsg(
                receiver_email="other@test",
                sender_email="peer@test",
                command=997,
                extra_data=[viewer.inventory_action_tag, "id_blue", "", ""],
            ),
        )
        for idx in range(300)
    ]
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert viewer._shmem_scan_start_index == 256
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_poll_shared_memory_does_not_advance_cursor_past_unexamined_message_on_processed_cap(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 1
    viewer.max_shmem_scan_per_tick = 20

    sent_stats_responses: list[str] = []
    viewer._send_inventory_kit_stats_response = lambda email: sent_stats_responses.append(str(email))

    messages: list[tuple[int, _FakeSharedMsg]] = [
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=[viewer.inventory_stats_request_tag],
            ),
        ),
        (
            1,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=[viewer.inventory_stats_request_tag],
            ),
        ),
    ]
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert py4gw_mod.GLOBAL_CACHE.ShMem.finished == [0]
        assert viewer._shmem_scan_start_index == 1
        assert sent_stats_responses == ["peer@test"]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_poll_shared_memory_accepts_c_wchar_message_fields(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20

    sent_stats_responses: list[str] = []
    viewer._send_inventory_kit_stats_response = lambda email: sent_stats_responses.append(str(email))

    messages: list[tuple[int, _FakeSharedMsg]] = [
        (
            0,
            _FakeSharedMsg(
                receiver_email=_wch("self@test"),
                sender_email=_wch("peer@test"),
                command=997,
                extra_data=[_wch(viewer.inventory_stats_request_tag)],
            ),
        ),
    ]
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert py4gw_mod.GLOBAL_CACHE.ShMem.finished == [0]
        assert sent_stats_responses == ["peer@test"]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_poll_shared_memory_handles_inventory_action_from_c_wchar_payload(monkeypatch):
    from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_actions import InventoryActionStatus

    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20

    action_calls: list[tuple[str, str, str, str]] = []

    def _fake_run_inventory_action(action_code, action_payload, action_meta, sender_email):
        action_calls.append((str(action_code), str(action_payload), str(action_meta), str(sender_email)))
        return module.InventoryActionResult(status=InventoryActionStatus.FINISHED)

    viewer._run_inventory_action = _fake_run_inventory_action

    messages: list[tuple[int, _FakeSharedMsg]] = [
        (
            0,
            _FakeSharedMsg(
                receiver_email=_wch("self@test"),
                sender_email=_wch("peer@test"),
                command=997,
                extra_data=[
                    _wch(viewer.inventory_action_tag),
                    _wch("id_blue"),
                    _wch(""),
                    _wch("ev-cw"),
                ],
            ),
        ),
    ]
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert action_calls == [("id_blue", "", "ev-cw", "peer@test")]
        assert py4gw_mod.GLOBAL_CACHE.ShMem.finished == [0]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)
