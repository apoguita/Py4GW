from __future__ import annotations

import ctypes
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import types
from types import SimpleNamespace
import uuid


def _set_module_attrs(module: types.ModuleType, **attrs: object) -> types.ModuleType:
    for name, value in attrs.items():
        setattr(module, name, value)
    return module


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
        receiver_email: object,
        sender_email: object,
        command: int,
        extra_data: list[object],
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

    class _Agent:
        @staticmethod
        def IsValid(_agent_id):  # noqa: N802 - runtime API
            return True

        @staticmethod
        def GetItemAgentItemID(_agent_id):  # noqa: N802 - runtime API
            return 0

        @staticmethod
        def GetItemAgentOwnerID(_agent_id):  # noqa: N802 - runtime API
            return 0

    class _AgentArray:
        @staticmethod
        def GetItemArray():  # noqa: N802 - runtime API
            return []

    class _Map:
        @staticmethod
        def GetMapID():  # noqa: N802 - runtime API
            return 1

        @staticmethod
        def GetInstanceUptime():  # noqa: N802 - runtime API
            return 1000

        @staticmethod
        def GetMapName(_map_id):  # noqa: N802 - runtime API
            return "Map"

    pyinventory_mod = types.ModuleType("PyInventory")
    pyagent_mod = types.ModuleType("PyAgent")
    py4gw_runtime_mod = _set_module_attrs(
        types.ModuleType("Py4GW"),
        Console=_Console,
    )

    py4gw_mod = types.ModuleType("Py4GWCoreLib")
    py4gw_mod.__path__ = []  # type: ignore[attr-defined]
    _set_module_attrs(
        py4gw_mod,
        GLOBAL_CACHE=SimpleNamespace(ShMem=None, Inventory=SimpleNamespace()),
        Agent=_Agent,
        AgentArray=_AgentArray,
        Player=_Player,
        Party=_Party,
        Map=_Map,
        Py4GW=SimpleNamespace(Console=_Console),
        Routines=SimpleNamespace(
            Checks=SimpleNamespace(Map=SimpleNamespace(MapValid=lambda: True))
        ),
        SharedCommandType=SimpleNamespace(CustomBehaviors=SimpleNamespace(value=997)),
        ThrottledTimer=_FakeTimer,
        __all__=[
            "GLOBAL_CACHE",
            "Agent",
            "AgentArray",
            "Player",
            "Party",
            "Map",
            "Py4GW",
            "Routines",
            "ThrottledTimer",
            "SharedCommandType",
        ],
    )

    item_mod = _set_module_attrs(
        types.ModuleType("Py4GWCoreLib.Item"),
        Item=SimpleNamespace(
            GetModelID=lambda _item_id: 0,
            Rarity=SimpleNamespace(GetRarity=lambda _item_id: (0, "Unknown")),
            Properties=SimpleNamespace(GetQuantity=lambda _item_id: 1),
            Type=SimpleNamespace(
                IsTome=lambda _item_id: False,
                IsMaterial=lambda _item_id: False,
                IsRareMaterial=lambda _item_id: False,
            ),
            Usage=SimpleNamespace(IsIdentified=lambda _item_id: True),
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Item",
            RequestName=lambda _item_id: None,
        ),
    )
    itemarray_mod = _set_module_attrs(
        types.ModuleType("Py4GWCoreLib.ItemArray"),
        ItemArray=SimpleNamespace(
            CreateBagList=lambda *_args: [],
            GetItemArray=lambda _bags: [],
        ),
    )

    helpers_mod = _set_module_attrs(
        types.ModuleType("Py4GWCoreLib.native_src.internals.helpers"),
        encoded_wstr_to_str=lambda value: str(value),
    )
    native_mod = types.ModuleType("Py4GWCoreLib.native_src")
    native_mod.__path__ = []  # type: ignore[attr-defined]
    internals_mod = types.ModuleType("Py4GWCoreLib.native_src.internals")
    internals_mod.__path__ = []  # type: ignore[attr-defined]

    corelib_mod = _set_module_attrs(
        types.ModuleType("Py4GWCoreLib.Py4GWcorelib"),
        ThrottledTimer=_FakeTimer,
    )

    enums_mod = _set_module_attrs(
        types.ModuleType("Py4GWCoreLib.enums"),
        SharedCommandType=py4gw_mod.SharedCommandType,
    )

    widget_manager_mod = _set_module_attrs(
        types.ModuleType("Py4GWCoreLib.py4gwcorelib_src.WidgetManager"),
        get_widget_handler=lambda: SimpleNamespace(
            get_widget_info=lambda _name: None,
            is_widget_enabled=lambda _name: False,
            disable_widget=lambda _name: None,
            enable_widget=lambda _name: None,
        ),
    )
    py4gwcorelib_src_mod = types.ModuleType("Py4GWCoreLib.py4gwcorelib_src")
    py4gwcorelib_src_mod.__path__ = []  # type: ignore[attr-defined]
    globalcache_mod = types.ModuleType("Py4GWCoreLib.GlobalCache")
    globalcache_mod.__path__ = []  # type: ignore[attr-defined]
    sharedmemory_mod = _set_module_attrs(
        types.ModuleType("Py4GWCoreLib.GlobalCache.SharedMemory"),
        AccountStruct=object,
    )

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


def test_drop_viewer_reload_state_round_trip(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.raw_drops = [{"item_name": "Bone", "qty": 2}]
    viewer.aggregated_drops = {"Bone": {"Quantity": 2}}
    viewer.total_drops = 2
    viewer.show_runtime_panel = True
    viewer.filter_player = "Leader"
    viewer.status_message = "Old"
    viewer.runtime_config["compact_mode"] = True

    state = module._capture_drop_viewer_reload_state(viewer)

    restored_viewer = module.DropViewerWindow()
    module._apply_drop_viewer_reload_state(restored_viewer, state)

    try:
        assert restored_viewer.raw_drops == [{"item_name": "Bone", "qty": 2}]
        assert restored_viewer.aggregated_drops == {"Bone": {"Quantity": 2}}
        assert restored_viewer.total_drops == 2
        assert restored_viewer.compact_mode is True
        assert restored_viewer.show_runtime_panel is False
        assert restored_viewer.filter_player == "Leader"
        assert restored_viewer.runtime_config["compact_mode"] is True
        assert restored_viewer.status_message == "Drop Viewer code auto-refreshed"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_drop_viewer_refresh_detects_changed_source(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.drop_viewer
    watched_path = str(tmp_path / "watched_drop_viewer_runtime.py")
    Path(watched_path).write_text("# watched\n", encoding="utf-8")

    setattr(module, "_DROP_VIEWER_LAST_RELOAD_SCAN_TS", 0.0)
    setattr(module, "_DROP_VIEWER_RELOAD_MTIMES", {watched_path: 100.0})

    monkeypatch.setattr(module, "_iter_drop_viewer_reload_targets", lambda: [("watched", types.SimpleNamespace(__file__=watched_path), watched_path)])
    monkeypatch.setattr(module, "_module_file_mtime", lambda path: 101.0 if path == watched_path else None)

    reload_calls: list[list[tuple[str, object, str]]] = []

    def _fake_reload(targets):
        reload_calls.append(list(targets))
        return viewer

    monkeypatch.setattr(module, "_reload_drop_viewer_runtime", _fake_reload)

    try:
        refreshed_viewer = module._maybe_refresh_drop_viewer()
        assert refreshed_viewer is viewer
        assert len(reload_calls) == 1
        assert reload_calls[0][0][0] == "watched"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


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


def test_run_inventory_action_sell_gold_recovers_stale_outpost_lock(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.auto_outpost_store_job_running = True
    viewer.auto_id_job_running = False
    viewer.auto_salvage_job_running = False
    viewer.auto_buy_kits_job_running = False
    viewer.auto_gold_balance_job_running = False
    viewer.auto_inventory_reorder_job_running = False

    queue_calls: list[int] = []

    def _queue_manual_sell_gold_items():
        queue_calls.append(1)
        if viewer.auto_outpost_store_job_running:
            return 0
        return 1

    monkeypatch.setattr(viewer, "_queue_manual_sell_gold_items", _queue_manual_sell_gold_items)

    try:
        result = viewer._run_inventory_action("sell_gold_no_runes")
        assert result.is_finished is True
        assert len(queue_calls) == 2
        assert viewer.auto_outpost_store_job_running is False
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sell_gold_items_accepts_lowercase_gold_and_keeps_runes(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()

    sold_batches: list[list[int]] = []

    monkeypatch.setattr(
        module,
        "ItemArray",
        SimpleNamespace(
            CreateBagList=lambda *_args: [1, 2, 3, 4],
            GetItemArray=lambda _bags: [101, 102, 103],
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "Item",
        SimpleNamespace(
            Rarity=SimpleNamespace(
                GetRarity=lambda item_id: (0, "gold")
                if int(item_id) in {101, 102}
                else (0, "Purple")
            ),
            GetName=lambda item_id: "Rune of Superior Vigor" if int(item_id) == 102 else "Gold Sword",
            item_instance=lambda _item_id: None,
        ),
        raising=False,
    )

    def _wait_gen(_ms):
        if False:
            yield None
        return None

    def _sell_items_gen(item_ids, log=False):
        sold_batches.append([int(v) for v in list(item_ids or [])])
        if False:
            yield None
        return None

    monkeypatch.setattr(
        module,
        "Routines",
        SimpleNamespace(
            Yield=SimpleNamespace(
                wait=_wait_gen,
                Merchant=SimpleNamespace(SellItems=_sell_items_gen),
            )
        ),
        raising=False,
    )

    monkeypatch.setattr(viewer, "_is_rune_item_for_reorder", lambda item_id: int(item_id) == 102, raising=False)
    monkeypatch.setattr(viewer, "_is_merchant_frame_open", lambda: True, raising=False)

    try:
        coroutine = viewer._sell_gold_items_except_runes()
        while True:
            next(coroutine)
    except StopIteration as stop:
        result = int(stop.value or 0)
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result == 1
    assert sold_batches == [[101]]


def test_poll_shared_memory_leaves_tracker_drop_pending_during_map_change_grace(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20
    viewer.map_change_ignore_until = 10**12

    messages: list[tuple[int, _FakeSharedMsg]] = [
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=["TrackerDrop", "Icy Lodestone", "White", "v2|ev-ignore||"],
                params=(1.0, 42.0, 500.0, 0.0),
            ),
        ),
    ]
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert py4gw_mod.GLOBAL_CACHE.ShMem.finished == []
        assert viewer.raw_drops == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_update_rows_item_name_only_if_unknown_preserves_known_name(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.raw_drops = [[
        "2026-02-28 14:42:37",
        "Leader",
        "1",
        "Map",
        "Player Five",
        "Molten Claw",
        "1",
        "White",
        "ev-rename",
        "",
        "42",
        "peer@test",
    ]]

    try:
        renamed = viewer._update_rows_item_name_by_event_and_sender(
            "ev-rename",
            "peer@test",
            "Scrolls of Resurrection",
            player_name="Player Five",
            only_if_unknown=True,
        )
        assert renamed == 0
        assert viewer.raw_drops[0][5] == "Molten Claw"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_poll_shared_memory_late_name_chunk_updates_pending_drop_row(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20

    full_name = "Shocking Magmas Arm of Fortitude"
    short_name = full_name[:31]
    name_sig = module.make_name_signature(full_name)
    name_chunks = module.build_name_chunks(full_name, 24)

    messages: list[tuple[int, _FakeSharedMsg]] = [
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=["TrackerDrop", short_name, "Gold", f"v3|ev-name|{name_sig}|0001"],
                params=(1.0, 42.0, 500.0, 0.0),
            ),
        ),
    ]
    for idx, total, chunk in name_chunks:
        messages.append(
            (
                idx,
                _FakeSharedMsg(
                    receiver_email="self@test",
                    sender_email="peer@test",
                    command=997,
                    extra_data=["TrackerNameV2", name_sig, chunk, module.encode_name_chunk_meta(idx, total)],
                ),
            )
        )
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert len(viewer.raw_drops) == 1
        assert viewer.raw_drops[0][5] == full_name
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_poll_shared_memory_preserves_space_across_name_chunk_boundary(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20

    full_name = "Hale Stone Summit Badge of the Assassin"
    short_name = "Stone Summit Badge"
    name_sig = module.make_name_signature(full_name)
    chunk_size = len("Hale Stone Summit Badge of the ")
    name_chunks = module.build_name_chunks(full_name, chunk_size)

    messages: list[tuple[int, _FakeSharedMsg]] = [
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=["TrackerDrop", short_name, "Gold", f"v3|ev-name-space|{name_sig}|0001"],
                params=(1.0, 42.0, 358.0, 0.0),
            ),
        ),
    ]
    for idx, total, chunk in name_chunks:
        messages.append(
            (
                idx,
                _FakeSharedMsg(
                    receiver_email="self@test",
                    sender_email="peer@test",
                    command=997,
                    extra_data=["TrackerNameV2", name_sig, chunk, module.encode_name_chunk_meta(idx, total)],
                ),
            )
        )
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert len(viewer.raw_drops) == 1
        assert viewer.raw_drops[0][5] == full_name
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_poll_shared_memory_signature_collision_keeps_raw_name_for_new_event(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20

    short_name = "Dolyak Cladding"
    stale_full_name = "Dolyak Cladding Warrior Rune of Superior Swordsmanship"
    name_sig = module.make_name_signature(short_name)
    viewer.full_name_by_signature[name_sig] = stale_full_name
    viewer.stats_name_signature_by_event[viewer._make_stats_cache_key("ev-old", "peer@test", "")] = name_sig

    messages: list[tuple[int, _FakeSharedMsg]] = [
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=["TrackerDrop", short_name, "Purple", f"v3|ev-new|{name_sig}|0001"],
                params=(1.0, 563.0, 1115.0, 0.0),
            ),
        ),
    ]
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert len(viewer.raw_drops) == 1
        assert viewer.raw_drops[0][5] == short_name
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_poll_shared_memory_event_scoped_name_cache_ignores_stale_signature_name(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20

    short_name = "Titan Armor"
    stale_full_name = "Titan Armor Monk Rune of Superior Divine Favor"
    name_sig = module.make_name_signature(short_name)
    viewer.full_name_by_signature[name_sig] = stale_full_name
    # No prior sender/event linkage should be required for stale signature fallback to be ignored.
    viewer.stats_name_signature_by_event = {}

    messages: list[tuple[int, _FakeSharedMsg]] = [
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=["TrackerDrop", short_name, "Gold", f"v3|ev-fresh|{name_sig}|0001"],
                params=(1.0, 538.0, 89.0, 0.0),
            ),
        ),
    ]
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert len(viewer.raw_drops) == 1
        assert viewer.raw_drops[0][5] == short_name
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_poll_shared_memory_late_name_chunk_does_not_rename_white_non_rune_drop(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20

    full_name = "Shocking Magmas Arm of Fortitude"
    short_name = "Magmas Arm"
    name_sig = module.make_name_signature(full_name)
    name_chunks = module.build_name_chunks(full_name, 24)

    messages: list[tuple[int, _FakeSharedMsg]] = [
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=["TrackerDrop", short_name, "White", f"v3|ev-white-name|{name_sig}|0001"],
                params=(1.0, 42.0, 500.0, 0.0),
            ),
        ),
    ]
    for idx, total, chunk in name_chunks:
        messages.append(
            (
                idx,
                _FakeSharedMsg(
                    receiver_email="self@test",
                    sender_email="peer@test",
                    command=997,
                    extra_data=["TrackerNameV2", name_sig, chunk, module.encode_name_chunk_meta(idx, total)],
                ),
            )
        )
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert len(viewer.raw_drops) == 1
        assert viewer.raw_drops[0][5] == short_name
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_poll_shared_memory_late_name_chunk_does_not_rename_uncached_same_sender_row(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20

    short_name = "Titan Armor"
    full_name = "Titan Armor Warrior Rune of Major Swordsmanship"
    name_sig = module.make_name_signature(short_name)
    viewer.raw_drops = [[
        "2026-03-05 22:39:40",
        "Viewer",
        "92",
        "Lair",
        "Follower",
        short_name,
        "1",
        "White",
        "ev-old",
        "",
        "200",
        "peer@test",
    ]]

    messages: list[tuple[int, _FakeSharedMsg]] = [
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=["TrackerDrop", short_name, "Purple", f"v3|ev-new|{name_sig}|0001"],
                params=(1.0, 201.0, 538.0, 0.0),
            ),
        ),
    ]
    for idx, total, chunk in module.build_name_chunks(full_name, 24):
        messages.append(
            (
                idx,
                _FakeSharedMsg(
                    receiver_email="self@test",
                    sender_email="peer@test",
                    command=997,
                    extra_data=["TrackerNameV2", name_sig, chunk, module.encode_name_chunk_meta(idx, total, "ev-new")],
                ),
            )
        )
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert len(viewer.raw_drops) == 2
        assert viewer.raw_drops[0][5] == short_name
        assert viewer.raw_drops[1][5] == full_name
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_poll_shared_memory_exact_event_name_update_does_not_rename_same_sender_pending_row(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.max_shmem_messages_per_tick = 8
    viewer.max_shmem_scan_per_tick = 20

    short_name = "Titan Armor"
    full_name = "Titan Armor Elementalist Rune of Superior Fire Magic"
    name_sig = module.make_name_signature(short_name)
    viewer.raw_drops = [[
        "2026-03-05 23:37:31",
        "Viewer",
        "92",
        "Tasca's Demise",
        "Player Six",
        short_name,
        "1",
        "Gold",
        "ev-gold",
        "",
        "487",
        "peer@test",
    ]]

    messages: list[tuple[int, _FakeSharedMsg]] = [
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=["TrackerDrop", short_name, "White", f"v3|ev-white|{name_sig}|0001"],
                params=(1.0, 484.0, 90.0, 0.0),
            ),
        ),
    ]
    for idx, total, chunk in module.build_name_chunks(full_name, 24):
        messages.append(
            (
                idx,
                _FakeSharedMsg(
                    receiver_email="self@test",
                    sender_email="peer@test",
                    command=997,
                    extra_data=["TrackerNameV2", name_sig, chunk, module.encode_name_chunk_meta(idx, total, "ev-gold")],
                ),
            )
        )
    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem(messages)

    try:
        viewer._poll_shared_memory()
        assert len(viewer.raw_drops) == 2
        assert viewer.raw_drops[0][5] == full_name
        assert viewer.raw_drops[1][5] == short_name
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_update_resets_existing_rows_on_map_change(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.last_update_time = 0.0
    viewer.last_seen_map_id = 1
    viewer.last_seen_instance_uptime_ms = 5000
    viewer.raw_drops = [[
        "2026-02-28 14:42:37",
        "Leader",
        "1",
        "Old Map",
        "Leader",
        "Icy Lodestone",
        "1",
        "White",
        "ev-old",
        "",
        "42",
        "self@test",
    ]]
    viewer.total_drops = 1

    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem([
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=["TrackerDrop", "Old Item", "White", "v2|ev-old||"],
                params=(1.0, 42.0, 500.0, 0.0),
            ),
        ),
    ])
    monkeypatch.setattr(module.Map, "GetMapID", lambda: 2)
    monkeypatch.setattr(module.Map, "GetInstanceUptime", lambda: 100, raising=False)
    monkeypatch.setattr(module.Player, "IsChatHistoryReady", lambda: True)
    monkeypatch.setattr(module.Player, "GetChatHistory", lambda: [])

    try:
        viewer.update()
        assert viewer.last_seen_map_id == 2
        assert viewer.raw_drops == []
        assert viewer.total_drops == 0
        assert viewer.map_change_ignore_until > 0.0
        assert viewer.status_message == "Auto reset on map change"
        assert py4gw_mod.GLOBAL_CACHE.ShMem.finished == [0]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_update_resets_existing_rows_on_instance_change(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.last_update_time = 0.0
    viewer.last_seen_map_id = 1
    viewer.last_seen_instance_uptime_ms = 5000
    viewer.raw_drops = [[
        "2026-02-28 14:42:37",
        "Leader",
        "1",
        "Old Map",
        "Leader",
        "Icy Lodestone",
        "1",
        "White",
        "ev-old",
        "",
        "42",
        "self@test",
    ]]
    viewer.total_drops = 1
    fake_sender = SimpleNamespace(
        resets=0,
        last_seen_map_id=0,
        last_seen_instance_uptime_ms=0,
    )
    def _reset_tracking_state():
        fake_sender.resets += 1
    fake_sender._reset_tracking_state = _reset_tracking_state
    monkeypatch.setattr(module, "DropTrackerSender", lambda: fake_sender)

    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem([])
    monkeypatch.setattr(module.Map, "GetMapID", lambda: 1)
    monkeypatch.setattr(module.Map, "GetInstanceUptime", lambda: 100, raising=False)
    monkeypatch.setattr(module.Player, "IsChatHistoryReady", lambda: True)
    monkeypatch.setattr(module.Player, "GetChatHistory", lambda: [])

    try:
        viewer.update()
        assert viewer.last_seen_map_id == 1
        assert viewer.last_seen_instance_uptime_ms == 100
        assert viewer.raw_drops == []
        assert viewer.total_drops == 0
        assert viewer.status_message == "Auto reset on map change"
        assert fake_sender.resets == 1
        assert fake_sender.last_seen_map_id == 1
        assert fake_sender.last_seen_instance_uptime_ms == 100
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_update_rejects_stale_follower_drop_session_after_reset(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.last_update_time = 0.0
    viewer.last_seen_map_id = 1
    viewer.last_seen_instance_uptime_ms = 1000
    viewer.sender_session_floor_by_email = {"peer@test": 4}
    ack_calls = []
    viewer._send_tracker_ack = lambda receiver_email, event_id: ack_calls.append((receiver_email, event_id)) or True

    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem([
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=["TrackerDrop", "Old Item", "White", "v3|ev-old||0003"],
                params=(1.0, 42.0, 500.0, 0.0),
            ),
        ),
    ])
    monkeypatch.setattr(module.Map, "GetMapID", lambda: 1)
    monkeypatch.setattr(module.Map, "GetInstanceUptime", lambda: 1000, raising=False)
    monkeypatch.setattr(module.Player, "IsChatHistoryReady", lambda: True)
    monkeypatch.setattr(module.Player, "GetChatHistory", lambda: [])

    try:
        viewer.update()
        assert viewer.raw_drops == []
        assert viewer.total_drops == 0
        assert py4gw_mod.GLOBAL_CACHE.ShMem.finished == [0]
        assert ack_calls == [("peer@test", "ev-old")]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_update_accepts_drop_when_sender_session_matches_floor(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.last_update_time = 0.0
    viewer.last_seen_map_id = 1
    viewer.last_seen_instance_uptime_ms = 1000
    viewer.sender_session_floor_by_email = {"peer@test": 3}

    py4gw_mod.GLOBAL_CACHE.ShMem = _FakeShMem([
        (
            0,
            _FakeSharedMsg(
                receiver_email="self@test",
                sender_email="peer@test",
                command=997,
                extra_data=["TrackerDrop", "Current Item", "White", "v3|ev-current||0003"],
                params=(1.0, 42.0, 500.0, 0.0),
            ),
        ),
    ])
    monkeypatch.setattr(module.Map, "GetMapID", lambda: 1)
    monkeypatch.setattr(module.Map, "GetInstanceUptime", lambda: 1000, raising=False)
    monkeypatch.setattr(module.Player, "IsChatHistoryReady", lambda: True)
    monkeypatch.setattr(module.Player, "GetChatHistory", lambda: [])

    try:
        viewer.update()
        assert viewer.total_drops == 1
        assert viewer.raw_drops[0][5] == "Current Item"
        assert py4gw_mod.GLOBAL_CACHE.ShMem.finished == [0]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_clear_cached_event_stats_preserves_event_identity(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = object.__new__(module.DropTrackerSender)
    sender.sent_event_stats_cache = {
        "ev-1": {
            "item_id": 42,
            "model_id": 500,
            "item_name": "Icy Lodestone",
            "name_signature": "deadbeef",
            "stats_text": "Old Stats",
            "created_at": 1.0,
        }
    }

    try:
        module.DropTrackerSender.clear_cached_event_stats(sender, "ev-1", 42)
        entry = sender.sent_event_stats_cache["ev-1"]
        assert entry["item_id"] == 42
        assert entry["model_id"] == 500
        assert entry["item_name"] == "Icy Lodestone"
        assert entry["name_signature"] == "deadbeef"
        assert entry["stats_text"] == ""
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_resets_tracking_state_on_instance_change(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()
    sender.last_seen_map_id = 1
    sender.last_seen_instance_uptime_ms = 5000
    sender.last_inventory_snapshot = {(1, 1): ("Icy Lodestone", "White", 1, 500, 42)}
    sender.pending_slot_deltas = {(1, 1): {"qty": 1, "item_id": 42, "model_id": 500}}
    sender.is_warmed_up = True

    monkeypatch.setattr(sender_module.Map, "GetMapID", lambda: 1)
    monkeypatch.setattr(sender_module.Map, "GetInstanceUptime", lambda: 100, raising=False)
    monkeypatch.setattr(sender_module, "read_current_map_instance", lambda: (1, 100))

    try:
        sender.act()
        assert sender.last_seen_map_id == 1
        assert sender.last_seen_instance_uptime_ms == 100
        assert sender.last_inventory_snapshot == {}
        assert sender.pending_slot_deltas == {}
        assert sender.is_warmed_up is False
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_buffer_pending_slot_delta_preserves_reused_slot_as_orphan(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.pending_slot_deltas = {
        (1, 2): {
            "qty": 2,
            "model_id": 500,
            "item_id": 42,
            "rarity": "Blue",
            "first_seen": 10.0,
            "last_seen": 10.0,
        }
    }

    try:
        sender._buffer_pending_slot_delta((1, 2), 1, 600, 43, "Gold", 20.0)
        assert sender.pending_slot_deltas[(1, 2)] == {
            "qty": 1,
            "model_id": 600,
            "item_id": 43,
            "rarity": "Gold",
            "first_seen": 20.0,
            "last_seen": 20.0,
        }
        assert sender.pending_slot_deltas[(0, -42)] == {
            "qty": 2,
            "model_id": 500,
            "item_id": 42,
            "rarity": "Blue",
            "first_seen": 10.0,
            "last_seen": 20.0,
        }
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_carryover_baseline_tracks_early_pickup_after_instance_change(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    old_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
    }
    new_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("New Item", "Blue", 1, 600, 43),
    }
    sender.last_inventory_snapshot = dict(old_snapshot)
    sender.is_warmed_up = True
    sender.pending_slot_deltas = {}
    sender.last_reset_reason = ""
    sender.last_reset_map_id = 0
    sender.last_reset_instance_uptime_ms = 0
    sender.last_reset_started_at = 0.0

    queued_events: list[tuple[str, int, str, int, int]] = []
    snapshots = [
        (new_snapshot, 2, 2),
        (new_snapshot, 2, 2),
        (new_snapshot, 2, 2),
    ]

    def _fake_take_inventory_snapshot():
        snapshot, total, ready = snapshots.pop(0)
        sender.last_snapshot_total = total
        sender.last_snapshot_ready = ready
        sender.last_snapshot_not_ready = max(0, total - ready)
        return snapshot

    monkeypatch.setattr(sender, "_take_inventory_snapshot", _fake_take_inventory_snapshot)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)

    try:
        sender._begin_new_session("instance_change", 1, 100)
        assert sender.last_inventory_snapshot == {}
        assert sender.carryover_inventory_snapshot == old_snapshot
        assert sender.session_startup_pending is True

        sender._process_inventory_deltas()
        assert queued_events == []
        assert sender.session_startup_pending is True

        sender.recent_world_item_disappearances = [
            {
                "agent_id": 9001,
                "item_id": 43,
                "model_id": 600,
                "qty": 1,
                "rarity": "Blue",
                "name": "New Item",
                "disappeared_at": time.time(),
            }
        ]
        sender._process_inventory_deltas()
        assert queued_events == [("New Item", 1, "Blue", 43, 600)]
        assert sender.session_startup_pending is False
        assert sender.carryover_inventory_snapshot == {}
        assert sender.last_inventory_snapshot == new_snapshot
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_carryover_baseline_ignores_existing_inventory_when_item_ids_churn(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    old_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("Blue Shield", "Blue", 1, 600, 43),
    }
    remapped_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 4200),
        (1, 2): ("Blue Shield", "Blue", 1, 600, 4300),
    }
    sender.last_inventory_snapshot = dict(old_snapshot)
    sender.is_warmed_up = True
    sender.pending_slot_deltas = {}

    queued_events: list[tuple[str, int, str, int, int]] = []
    snapshots = [
        (remapped_snapshot, 2, 2),
        (remapped_snapshot, 2, 2),
    ]

    def _fake_take_inventory_snapshot():
        snapshot, total, ready = snapshots.pop(0)
        sender.last_snapshot_total = total
        sender.last_snapshot_ready = ready
        sender.last_snapshot_not_ready = max(0, total - ready)
        return snapshot

    monkeypatch.setattr(sender, "_take_inventory_snapshot", _fake_take_inventory_snapshot)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)

    try:
        sender._begin_new_session("instance_change", 1, 100)

        sender._process_inventory_deltas()
        assert queued_events == []

        sender._process_inventory_deltas()
        assert queued_events == []
        assert sender.last_inventory_snapshot == remapped_snapshot
        assert sender.session_startup_pending is False
        assert sender.carryover_inventory_snapshot == {}
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_carryover_baseline_requires_world_confirmation_for_new_slot_after_map_change(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    old_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
    }
    new_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("New Item", "Blue", 1, 600, 43),
    }
    sender.last_inventory_snapshot = dict(old_snapshot)
    sender.is_warmed_up = True
    sender.pending_slot_deltas = {}

    queued_events: list[tuple[str, int, str, int, int]] = []
    snapshots = [
        (new_snapshot, 2, 2),
        (new_snapshot, 2, 2),
        (new_snapshot, 2, 2),
    ]

    def _fake_take_inventory_snapshot():
        snapshot, total, ready = snapshots.pop(0)
        sender.last_snapshot_total = total
        sender.last_snapshot_ready = ready
        sender.last_snapshot_not_ready = max(0, total - ready)
        return snapshot

    monkeypatch.setattr(sender, "_take_inventory_snapshot", _fake_take_inventory_snapshot)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)

    try:
        sender._begin_new_session("map_change", 2, 100)
        assert sender.last_session_transition_reason == "map_change"
        assert sender.last_inventory_snapshot == {}
        assert sender.carryover_inventory_snapshot == old_snapshot
        assert sender.session_startup_pending is True

        sender._process_inventory_deltas()
        assert queued_events == []
        assert sender.session_startup_pending is True

        sender.recent_world_item_disappearances = [
            {
                "agent_id": 9001,
                "item_id": 43,
                "model_id": 600,
                "qty": 1,
                "rarity": "Blue",
                "name": "New Item",
                "disappeared_at": time.time(),
            }
        ]
        sender._process_inventory_deltas()
        assert queued_events == [("New Item", 1, "Blue", 43, 600)]
        assert sender.session_startup_pending is False
        assert sender.session_startup_pending is False
        assert sender.carryover_inventory_snapshot == {}
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_carryover_baseline_ignores_existing_inventory_when_names_unresolved(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    old_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("Blue Shield", "Blue", 1, 600, 43),
    }
    unresolved_snapshot = {
        (1, 3): ("Model#500", "White", 1, 500, 4200),
        (1, 4): ("Model#600", "Blue", 1, 600, 4300),
    }
    resolved_snapshot = {
        (1, 3): ("Old Item", "White", 1, 500, 4200),
        (1, 4): ("Blue Shield", "Blue", 1, 600, 4300),
    }
    sender.last_inventory_snapshot = dict(old_snapshot)
    sender.is_warmed_up = True
    sender.pending_slot_deltas = {}

    queued_events: list[tuple[str, int, str, int, int]] = []
    snapshots = [
        (unresolved_snapshot, 2, 2),
        (unresolved_snapshot, 2, 2),
        (resolved_snapshot, 2, 2),
    ]

    def _fake_take_inventory_snapshot():
        snapshot, total, ready = snapshots.pop(0)
        sender.last_snapshot_total = total
        sender.last_snapshot_ready = ready
        sender.last_snapshot_not_ready = max(0, total - ready)
        return snapshot

    monkeypatch.setattr(sender, "_take_inventory_snapshot", _fake_take_inventory_snapshot)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)

    try:
        sender._begin_new_session("instance_change", 1, 100)

        sender._process_inventory_deltas()
        assert queued_events == []
        assert sender.session_startup_pending is True

        sender._process_inventory_deltas()
        assert queued_events == []
        assert sender.pending_slot_deltas == {}
        assert sender.session_startup_pending is False

        sender._process_inventory_deltas()
        assert queued_events == []
        assert sender.last_inventory_snapshot == resolved_snapshot
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_map_change_carryover_suppresses_late_existing_item_after_startup(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    old_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (3, 3): ("Superior Salvage Kit", "White", 1, 239, 45),
    }
    startup_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 4200),
    }
    late_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 4200),
        (3, 3): ("Superior Salvage Kit", "White", 1, 239, 145),
    }
    sender.last_inventory_snapshot = dict(old_snapshot)
    sender.is_warmed_up = True
    sender.pending_slot_deltas = {}

    queued_events: list[tuple[str, int, str, int, int]] = []
    snapshots = [
        (startup_snapshot, 1, 1),
        (startup_snapshot, 1, 1),
        (late_snapshot, 2, 2),
    ]

    def _fake_take_inventory_snapshot():
        snapshot, total, ready = snapshots.pop(0)
        sender.last_snapshot_total = total
        sender.last_snapshot_ready = ready
        sender.last_snapshot_not_ready = max(0, total - ready)
        return snapshot

    monkeypatch.setattr(sender, "_take_inventory_snapshot", _fake_take_inventory_snapshot)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)

    try:
        sender._begin_new_session("map_change", 2, 100)

        sender._process_inventory_deltas()
        assert queued_events == []

        sender._process_inventory_deltas()
        assert queued_events == []

        sender._process_inventory_deltas()
        assert queued_events == []
        assert sender.carryover_inventory_snapshot == {}
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_map_change_carryover_suppresses_late_resolved_existing_item(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    old_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (3, 3): ("Model#239", "White", 1, 239, 45),
    }
    startup_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 4200),
    }
    late_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 4200),
        (3, 3): ("Superior Salvage Kit", "White", 1, 239, 145),
    }
    sender.last_inventory_snapshot = dict(old_snapshot)
    sender.is_warmed_up = True
    sender.pending_slot_deltas = {}

    queued_events: list[tuple[str, int, str, int, int]] = []
    snapshots = [
        (startup_snapshot, 1, 1),
        (startup_snapshot, 1, 1),
        (late_snapshot, 2, 2),
    ]

    def _fake_take_inventory_snapshot():
        snapshot, total, ready = snapshots.pop(0)
        sender.last_snapshot_total = total
        sender.last_snapshot_ready = ready
        sender.last_snapshot_not_ready = max(0, total - ready)
        return snapshot

    monkeypatch.setattr(sender, "_take_inventory_snapshot", _fake_take_inventory_snapshot)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)

    try:
        sender._begin_new_session("map_change", 2, 100)

        sender._process_inventory_deltas()
        assert queued_events == []

        sender._process_inventory_deltas()
        assert queued_events == []

        sender._process_inventory_deltas()
        assert queued_events == []
        assert sender.carryover_inventory_snapshot == {}
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_reset_carryover_suppresses_existing_item_that_replaces_other_existing_slot(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    old_snapshot = {
        (2, 1): ("Identification Kit", "White", 9, 2611, 444),
        (2, 7): ("Earth Wand", "White", 2, 436, 450),
    }
    reshuffled_snapshot = {
        (2, 1): ("Earth Wand", "White", 2, 436, 1450),
        (2, 7): ("Identification Kit", "White", 9, 2611, 1444),
    }
    sender.last_inventory_snapshot = dict(old_snapshot)
    sender.is_warmed_up = True
    sender.pending_slot_deltas = {}

    queued_events: list[tuple[str, int, str, int, int]] = []
    snapshots = [
        (reshuffled_snapshot, 2, 2),
    ]

    def _fake_take_inventory_snapshot():
        snapshot, total, ready = snapshots.pop(0)
        sender.last_snapshot_total = total
        sender.last_snapshot_ready = ready
        sender.last_snapshot_not_ready = max(0, total - ready)
        return snapshot

    monkeypatch.setattr(sender, "_take_inventory_snapshot", _fake_take_inventory_snapshot)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)

    try:
        sender._begin_new_session("viewer_sync_reset", 14, 100)
        sender._process_inventory_deltas()
        assert queued_events == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_followup_reset_preserves_existing_carryover_snapshot_when_live_snapshot_is_already_cleared(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    old_snapshot = {
        (2, 1): ("Identification Kit", "White", 9, 2611, 444),
        (2, 7): ("Earth Wand", "White", 2, 436, 450),
    }
    sender.last_inventory_snapshot = dict(old_snapshot)
    sender.is_warmed_up = True
    sender.pending_slot_deltas = {}

    queued_events: list[tuple[str, int, str, int, int]] = []
    snapshots = [
        (old_snapshot, 2, 2),
        (old_snapshot, 2, 2),
    ]

    def _fake_take_inventory_snapshot():
        snapshot, total, ready = snapshots.pop(0)
        sender.last_snapshot_total = total
        sender.last_snapshot_ready = ready
        sender.last_snapshot_not_ready = max(0, total - ready)
        return snapshot

    monkeypatch.setattr(sender, "_take_inventory_snapshot", _fake_take_inventory_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )

    try:
        sender._begin_new_session("map_change", 14, 100)
        preserved_carryover = dict(sender.carryover_inventory_snapshot)
        assert preserved_carryover == old_snapshot
        assert sender.session_startup_pending is True

        sender._begin_new_session("viewer_sync_reset", 14, 100)
        assert sender.last_inventory_snapshot == {}
        assert sender.carryover_inventory_snapshot == preserved_carryover
        assert sender.session_startup_pending is True

        sender._process_inventory_deltas()
        assert queued_events == []

        sender._process_inventory_deltas()
        assert queued_events == []
        assert sender.carryover_inventory_snapshot == {}
        assert sender.last_inventory_snapshot == old_snapshot
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_followup_map_change_preserves_richer_existing_carryover_snapshot(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    rich_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("Blue Shield", "Blue", 1, 600, 43),
        (1, 3): ("Salvage Kit", "White", 1, 239, 44),
    }
    partial_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 4200),
    }
    sender.last_inventory_snapshot = dict(rich_snapshot)
    sender.is_warmed_up = True

    try:
        sender._begin_new_session("map_change", 14, 100)
        assert sender.carryover_inventory_snapshot == rich_snapshot

        sender.last_inventory_snapshot = dict(partial_snapshot)
        sender._begin_new_session("map_change", 14, 120)
        assert sender.carryover_inventory_snapshot == rich_snapshot
        assert sender.session_startup_pending is True
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_duplicate_map_change_reset_is_coalesced(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    original_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
    }
    sender.last_inventory_snapshot = dict(original_snapshot)
    sender.is_warmed_up = True

    try:
        sender._begin_new_session("map_change", 14, 1000)
        first_session_id = int(sender.sender_session_id)
        first_carryover = dict(sender.carryover_inventory_snapshot)

        sender.last_inventory_snapshot = {(1, 2): ("New Snapshot", "Blue", 1, 600, 43)}
        sender._begin_new_session("map_change", 14, 1200)

        assert int(sender.sender_session_id) == first_session_id
        assert sender.carryover_inventory_snapshot == first_carryover
        assert sender.last_seen_map_id == 14
        assert sender.last_seen_instance_uptime_ms == 1200
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_begin_new_session_clears_stale_outbox_and_name_refreshes(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.carryover_inventory_snapshot = {}
    sender.carryover_suppression_until = 0.0
    sender.last_reset_reason = ""
    sender.last_reset_map_id = 0
    sender.last_reset_instance_uptime_ms = 0
    sender.last_reset_started_at = 0.0
    sender.last_inventory_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
    }
    sender.outbox_queue = [
        {
            "event_id": "old-1",
            "item_name": "Old Item",
            "quantity": 1,
            "rarity": "White",
            "attempts": 3,
            "acked": False,
        }
    ]
    sender.pending_name_refresh_by_event = {
        "old-1": {
            "event_id": "old-1",
            "item_id": 42,
            "model_id": 500,
            "item_name": "Old Item",
            "name_signature": "deadbeef",
        }
    }
    sender.sent_event_stats_cache = {
        "old-1": {
            "item_id": 42,
            "model_id": 500,
            "item_name": "Old Item",
            "stats_text": "old",
            "created_at": 1.0,
        }
    }

    try:
        sender._begin_new_session("map_change", 14, 100)
        assert sender.carryover_inventory_snapshot == {(1, 1): ("Old Item", "White", 1, 500, 42)}
        assert sender.session_startup_pending is True
        assert sender.outbox_queue == []
        assert sender.pending_name_refresh_by_event == {}
        assert sender.sent_event_stats_cache == {}
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_viewer_duplicate_instance_reset_is_coalesced(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    runtime_update_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_runtime_update"
    )
    viewer = module.DropViewerWindow()
    viewer.last_reset_reason = "viewer_instance_reset"
    viewer.last_reset_map_id = 27
    viewer.last_reset_instance_uptime_ms = 1000
    viewer.last_reset_started_at = time.time()
    viewer.last_seen_map_id = 27
    viewer.last_seen_instance_uptime_ms = 1000

    try:
        coalesced = runtime_update_module._should_coalesce_viewer_reset(viewer, "viewer_instance_reset", 27, 1200)
        assert coalesced is True
        assert viewer.last_seen_map_id == 27
        assert viewer.last_seen_instance_uptime_ms == 1200
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_viewer_log_drops_batch_rebuilds_state_when_runtime_append_fails(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    batch_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_batch_store"
    )
    model_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models"
    )

    log_path = tmp_path / "drop_log.csv"
    rebuilt_row = model_module.DropLogRow(
        timestamp="2026-03-04 18:30:00",
        viewer_bot="Viewer",
        map_id=54,
        map_name="Scoundrel's Rise",
        player_name="Player Five",
        item_name="Ball Hammer",
        quantity=1,
        rarity="White",
        event_id="ev-1",
        item_stats="",
        item_id=99,
        sender_email="sender@test",
    )
    viewer = SimpleNamespace(
        log_path=str(log_path),
        raw_drops=[],
        aggregated_drops={},
        total_drops=0,
        stats_by_event={},
        _ensure_text=lambda value: "" if value is None else str(value),
        _make_stats_cache_key=lambda event_id, sender_email, player_name: f"{event_id}:{sender_email}:{player_name}",
        _canonical_agg_item_name=lambda item_name, _rarity, _agg: str(item_name),
        _build_drop_log_row_from_entry=lambda entry, bot_name, map_id, map_name: model_module.DropLogRow(
            timestamp="2026-03-04 18:30:00",
            viewer_bot=str(bot_name),
            map_id=int(map_id),
            map_name=str(map_name),
            player_name=str(entry["player_name"]),
            item_name=str(entry["item_name"]),
            quantity=int(entry["quantity"]),
            rarity=str(entry["extra_info"]),
            event_id=str(entry.get("event_id", "")),
            item_stats=str(entry.get("item_stats", "")),
            item_id=int(entry.get("item_id", 0)),
            sender_email=str(entry.get("sender_email", "")),
        ),
    )

    monkeypatch.setattr(batch_module.Player, "GetName", staticmethod(lambda: "Viewer"), raising=False)
    monkeypatch.setattr(batch_module.Map, "GetMapID", staticmethod(lambda: 54), raising=False)
    monkeypatch.setattr(batch_module.Map, "GetMapName", staticmethod(lambda _map_id: "Scoundrel's Rise"), raising=False)
    monkeypatch.setattr(batch_module, "append_drop_log_rows", lambda _path, _rows: log_path.write_text("written\n", encoding="utf-8"))
    monkeypatch.setattr(
        batch_module,
        "append_drop_rows_to_state",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("append failed")),
    )
    monkeypatch.setattr(batch_module, "parse_drop_log_file", lambda _path, map_name_resolver=None: [rebuilt_row])

    try:
        batch_module.log_drops_batch(
            viewer,
            [
                {
                    "player_name": "Player Five",
                    "item_name": "Ball Hammer",
                    "quantity": 1,
                    "extra_info": "White",
                    "event_id": "ev-1",
                    "item_stats": "",
                    "item_id": 99,
                    "sender_email": "sender@test",
                }
            ],
        )
        assert len(viewer.raw_drops) == 1
        assert viewer.total_drops == 1
        assert viewer.raw_drops[0][5] == "Ball Hammer"
        assert viewer.aggregated_drops == {("Ball Hammer", "White"): {"Quantity": 1, "Count": 1}}
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_viewer_row_updates_persist_late_name_and_stats_to_log_file(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    row_updates_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_row_updates"
    )
    log_store_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store"
    )
    model_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models"
    )

    viewer = module.DropViewerWindow()
    log_path = tmp_path / "drop_log.csv"
    viewer.log_path = str(log_path)
    original_row = model_module.DropLogRow(
        timestamp="2026-03-04 18:50:00",
        viewer_bot="Viewer",
        map_id=54,
        map_name="Scoundrel's Rise",
        player_name="Player Three",
        item_name="War Axe",
        quantity=1,
        rarity="Gold",
        event_id="ev-persist",
        item_stats="Unidentified",
        item_id=42,
        sender_email="sender@test",
    )
    log_store_module.append_drop_log_rows(str(log_path), [original_row])
    viewer.raw_drops = [[
        "2026-03-04 18:50:00",
        "Viewer",
        "54",
        "Scoundrel's Rise",
        "Player Three",
        "War Axe",
        "1",
        "Gold",
        "ev-persist",
        "Unidentified",
        "42",
        "sender@test",
    ]]

    try:
        renamed = row_updates_module.update_rows_item_name_by_event_and_sender(
            viewer,
            "ev-persist",
            "sender@test",
            "Furious War Axe of Warding",
            player_name="Player Three",
        )
        assert renamed == 1
        row_updates_module.set_row_item_stats(
            viewer,
            viewer.raw_drops[0],
            "Furious War Axe of Warding\nDamage: 6-28",
        )
        parsed = log_store_module.parse_drop_log_file(str(log_path))
        assert len(parsed) == 1
        assert parsed[0].item_name == "Furious War Axe of Warding"
        assert parsed[0].item_stats == "Furious War Axe of Warding\nDamage: 6-28"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_viewer_multi_row_stats_update_persists_late_text_bound_stats_to_log_file(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    row_updates_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_row_updates"
    )
    log_store_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store"
    )
    model_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models"
    )

    viewer = module.DropViewerWindow()
    log_path = tmp_path / "drop_log.csv"
    viewer.log_path = str(log_path)
    original_row = model_module.DropLogRow(
        timestamp="2026-03-06 01:25:31",
        viewer_bot="Viewer",
        map_id=92,
        map_name="Tasca's Demise",
        player_name="Player Six",
        item_name="Stalwart Insignia Beastmaster Harness Elementalist Rune of Minor Fire Magic",
        quantity=1,
        rarity="Blue",
        event_id="ev-text-persist",
        item_stats="Unidentified",
        item_id=372,
        sender_email="sender@test",
    )
    log_store_module.append_drop_log_rows(str(log_path), [original_row])
    viewer.raw_drops = [[
        "2026-03-06 01:25:31",
        "Viewer",
        "92",
        "Tasca's Demise",
        "Player Six",
        "Stalwart Insignia Beastmaster Harness Elementalist Rune of Minor Fire Magic",
        "1",
        "Blue",
        "ev-text-persist",
        "Unidentified",
        "372",
        "sender@test",
    ]]

    try:
        updated = row_updates_module.update_rows_item_stats_by_event_and_sender(
            viewer,
            "ev-text-persist",
            "sender@test",
            (
                "Stalwart Insignia Beastmaster Harness Elementalist Rune of Minor Fire Magic\n"
                "Armor +10 (vs. physical damage)\n"
                "+1 FireMagic (Non-stacking)\n"
                "Stalwart Insignia\n"
                "Elementalist Rune of Minor Fire Magic\n"
                "Value: 70 gold"
            ),
            player_name="Player Six",
            allow_player_fallback=False,
        )
        assert updated == 1
        parsed = log_store_module.parse_drop_log_file(str(log_path))
        assert len(parsed) == 1
        assert parsed[0].item_name == "Stalwart Insignia Beastmaster Harness Elementalist Rune of Minor Fire Magic"
        assert parsed[0].item_stats.startswith(
            "Stalwart Insignia Beastmaster Harness Elementalist Rune of Minor Fire Magic"
        )
        assert "Value: 70 gold" in parsed[0].item_stats
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_viewer_keeps_original_pickup_name_when_late_identified_name_arrives(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    row_updates_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_row_updates"
    )
    viewer = module.DropViewerWindow()
    viewer.raw_drops = [[
        "2026-03-04 18:40:00",
        "Viewer",
        "54",
        "Scoundrel's Rise",
        "Player One",
        "Superior Identification Kit",
        "1",
        "White",
        "ev-1",
        "",
        "169",
        "sender@test",
    ]]

    try:
        renamed = row_updates_module.update_rows_item_name_by_event_and_sender(
            viewer,
            "ev-1",
            "sender@test",
            "Zealous Identification Kit of Warding",
            player_name="Player One",
            only_if_unknown=False,
        )
        assert renamed == 0
        assert viewer.raw_drops[0][5] == "Superior Identification Kit"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_viewer_allows_safe_late_identified_name_expansion(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    row_updates_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_row_updates"
    )
    viewer = module.DropViewerWindow()
    viewer.raw_drops = [[
        "2026-03-04 18:40:00",
        "Viewer",
        "54",
        "Scoundrel's Rise",
        "Player One",
        "Break Hammer",
        "1",
        "Blue",
        "ev-1",
        "",
        "169",
        "sender@test",
    ]]

    try:
        renamed = row_updates_module.update_rows_item_name_by_event_and_sender(
            viewer,
            "ev-1",
            "sender@test",
            "Break Hammer ('Guided by Fate')",
            player_name="Player One",
            only_if_unknown=False,
        )
        assert renamed == 1
        assert viewer.raw_drops[0][5] == "Break Hammer ('Guided by Fate')"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_viewer_row_name_update_logs_debug_event(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    row_updates_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_row_updates"
    )
    logged_events: list[dict[str, object]] = []
    viewer = module.DropViewerWindow()
    viewer.raw_drops = [[
        "2026-03-04 18:40:00",
        "Viewer",
        "54",
        "Scoundrel's Rise",
        "Player Five",
        "Unknown Item",
        "1",
        "Gold",
        "ev-2",
        "",
        "170",
        "sender@test",
    ]]
    viewer._append_live_debug_log = lambda event, message, **fields: logged_events.append(
        {"event": event, "message": message, **fields}
    )

    try:
        renamed = row_updates_module.update_rows_item_name_by_event_and_sender(
            viewer,
            "ev-2",
            "sender@test",
            "Fiery Dragon Sword",
            player_name="Player Five",
            only_if_unknown=False,
        )
        assert renamed == 1
        assert len(logged_events) == 1
        assert logged_events[0]["event"] == "viewer_row_name_updated"
        assert logged_events[0]["previous_name"] == "Unknown Item"
        assert logged_events[0]["new_name"] == "Fiery Dragon Sword"
        assert logged_events[0]["previous_was_unknown"] is True
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_signature_and_sender_name_update_skips_ambiguous_multi_event_signature(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    row_updates_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_row_updates"
    )
    viewer = module.DropViewerWindow()
    sig = module.make_name_signature("Titan Armor")
    viewer.raw_drops = [
        [
            "2026-03-05 03:22:00",
            "Viewer",
            "92",
            "Boreal Station",
            "Player Five",
            "Titan Armor",
            "1",
            "Gold",
            "ev-1",
            "",
            "200",
            "sender@test",
        ],
        [
            "2026-03-05 03:22:05",
            "Viewer",
            "92",
            "Boreal Station",
            "Player Five",
            "Titan Armor",
            "1",
            "Gold",
            "ev-2",
            "",
            "201",
            "sender@test",
        ],
    ]
    viewer.stats_name_signature_by_event = {
        viewer._make_stats_cache_key("ev-1", "sender@test", "Player Five"): sig,
        viewer._make_stats_cache_key("ev-2", "sender@test", "Player Five"): sig,
    }

    try:
        renamed = row_updates_module.update_rows_item_name_by_signature_and_sender(
            viewer,
            sig,
            "sender@test",
            "Titan Armor Elementalist Rune of Superior Earth Magic",
            player_name="Player Five",
        )
        assert renamed == 0
        assert viewer.raw_drops[0][5] == "Titan Armor"
        assert viewer.raw_drops[1][5] == "Titan Armor"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_signature_and_sender_name_update_skips_uncached_same_sender_signature_row(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    row_updates_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_row_updates"
    )
    viewer = module.DropViewerWindow()
    sig = module.make_name_signature("Titan Armor")
    viewer.raw_drops = [
        [
            "2026-03-05 22:39:40",
            "Viewer",
            "92",
            "Lair",
            "Follower",
            "Titan Armor",
            "1",
            "White",
            "ev-old",
            "",
            "200",
            "sender@test",
        ],
        [
            "2026-03-05 22:39:46",
            "Viewer",
            "92",
            "Lair",
            "Follower",
            "Titan Armor",
            "1",
            "Purple",
            "ev-new",
            "",
            "201",
            "sender@test",
        ],
    ]
    viewer.stats_name_signature_by_event = {
        viewer._make_stats_cache_key("ev-new", "sender@test", "Follower"): sig,
    }

    try:
        renamed = row_updates_module.update_rows_item_name_by_signature_and_sender(
            viewer,
            sig,
            "sender@test",
            "Titan Armor Warrior Rune of Major Swordsmanship",
            player_name="Follower",
        )
        assert renamed == 0
        assert viewer.raw_drops[0][5] == "Titan Armor"
        assert viewer.raw_drops[1][5] == "Titan Armor"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_transport_resolve_party_leader_email_prefers_direct_leader_account_over_helper_cache(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    transport_module = sys.modules[module.DropTrackerSender.__module__.replace("drop_tracker_utility", "drop_tracker_sender_transport")]

    leader_account = SimpleNamespace(
        AccountEmail="leader@test",
        AgentData=SimpleNamespace(AgentID=1),
        AgentPartyData=SimpleNamespace(PartyID=777, PartyPosition=0),
        IsAccount=True,
    )
    follower_account = SimpleNamespace(
        AccountEmail="follower@test",
        AgentData=SimpleNamespace(AgentID=2),
        AgentPartyData=SimpleNamespace(PartyID=777, PartyPosition=1),
        IsAccount=True,
    )

    py4gw_mod.GLOBAL_CACHE.Party = SimpleNamespace(GetPartyLeaderID=lambda: 1, GetPartyID=lambda: 777)
    py4gw_mod.GLOBAL_CACHE.ShMem = SimpleNamespace(
        GetAllAccountData=lambda: [follower_account, leader_account],
    )
    monkeypatch.setattr(
        transport_module,
        "GLOBAL_CACHE",
        SimpleNamespace(
            Party=SimpleNamespace(GetPartyID=lambda: 777),
            ShMem=SimpleNamespace(GetAllAccountData=lambda: [follower_account, leader_account]),
        ),
        raising=False,
    )
    monkeypatch.setattr(transport_module.Party, "GetPartyLeaderID", staticmethod(lambda: 1), raising=False)
    monkeypatch.setattr(
        transport_module.CustomBehaviorHelperParty,
        "_get_party_leader_email",
        staticmethod(lambda: "stale@test"),
    )

    try:
        resolved_email = transport_module.resolve_party_leader_email(SimpleNamespace())
        assert resolved_email == "leader@test"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_transport_resolve_party_leader_email_ignores_stale_helper_email_and_picks_current_party_leader(
    monkeypatch,
):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    transport_module = sys.modules[module.DropTrackerSender.__module__.replace("drop_tracker_utility", "drop_tracker_sender_transport")]

    map_self = SimpleNamespace(MapID=54, Region=2, District=1, Language=0)
    self_account = SimpleNamespace(
        AccountEmail="self@test",
        AgentData=SimpleNamespace(AgentID=2, Map=map_self),
        AgentPartyData=SimpleNamespace(PartyID=777, PartyPosition=1),
        IsAccount=True,
    )
    stale_helper_account = SimpleNamespace(
        AccountEmail="stale@test",
        AgentData=SimpleNamespace(AgentID=99, Map=SimpleNamespace(MapID=54, Region=2, District=1, Language=0)),
        AgentPartyData=SimpleNamespace(PartyID=999, PartyPosition=0),
        IsAccount=True,
    )
    leader_account = SimpleNamespace(
        AccountEmail="leader@test",
        AgentData=SimpleNamespace(AgentID=11, Map=SimpleNamespace(MapID=54, Region=2, District=1, Language=0)),
        AgentPartyData=SimpleNamespace(PartyID=777, PartyPosition=0),
        IsAccount=True,
    )

    def _get_account_by_email(email: str):
        lookup = {
            "self@test": self_account,
            "stale@test": stale_helper_account,
            "leader@test": leader_account,
        }
        return lookup.get(str(email or "").strip().lower())

    shmem = SimpleNamespace(
        GetAllAccountData=lambda: [self_account, stale_helper_account, leader_account],
        GetAccountDataFromEmail=_get_account_by_email,
    )
    monkeypatch.setattr(transport_module.Player, "GetAccountEmail", staticmethod(lambda: "self@test"), raising=False)
    monkeypatch.setattr(transport_module.Party, "GetPartyLeaderID", staticmethod(lambda: 12345), raising=False)
    monkeypatch.setattr(
        transport_module,
        "GLOBAL_CACHE",
        SimpleNamespace(
            Party=SimpleNamespace(GetPartyID=lambda: 777),
            ShMem=shmem,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        transport_module.CustomBehaviorHelperParty,
        "_get_party_leader_email",
        staticmethod(lambda: "stale@test"),
    )

    try:
        resolved_email = transport_module.resolve_party_leader_email(SimpleNamespace())
        assert resolved_email == "leader@test"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_transport_resolve_party_leader_email_returns_none_when_only_stale_party_accounts_exist(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    transport_module = sys.modules[module.DropTrackerSender.__module__.replace("drop_tracker_utility", "drop_tracker_sender_transport")]

    map_self = SimpleNamespace(MapID=54, Region=2, District=1, Language=0)
    self_account = SimpleNamespace(
        AccountEmail="self@test",
        AgentData=SimpleNamespace(AgentID=2, Map=map_self),
        AgentPartyData=SimpleNamespace(PartyID=777, PartyPosition=1),
        IsAccount=True,
    )
    stale_account = SimpleNamespace(
        AccountEmail="stale@test",
        AgentData=SimpleNamespace(AgentID=11, Map=SimpleNamespace(MapID=54, Region=2, District=1, Language=0)),
        AgentPartyData=SimpleNamespace(PartyID=999, PartyPosition=0),
        IsAccount=True,
    )

    def _get_account_by_email(email: str):
        lookup = {
            "self@test": self_account,
            "stale@test": stale_account,
        }
        return lookup.get(str(email or "").strip().lower())

    shmem = SimpleNamespace(
        GetAllAccountData=lambda: [self_account, stale_account],
        GetAccountDataFromEmail=_get_account_by_email,
    )
    monkeypatch.setattr(transport_module.Player, "GetAccountEmail", staticmethod(lambda: "self@test"), raising=False)
    monkeypatch.setattr(transport_module.Party, "GetPartyLeaderID", staticmethod(lambda: 11), raising=False)
    monkeypatch.setattr(
        transport_module,
        "GLOBAL_CACHE",
        SimpleNamespace(
            Party=SimpleNamespace(GetPartyID=lambda: 777),
            ShMem=shmem,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        transport_module.CustomBehaviorHelperParty,
        "_get_party_leader_email",
        staticmethod(lambda: "stale@test"),
    )

    try:
        resolved_email = transport_module.resolve_party_leader_email(SimpleNamespace())
        assert resolved_email is None
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_transport_resolve_party_leader_email_prefers_party_position_zero_in_current_party(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    transport_module = sys.modules[module.DropTrackerSender.__module__.replace("drop_tracker_utility", "drop_tracker_sender_transport")]

    map_self = SimpleNamespace(MapID=54, Region=2, District=1, Language=0)
    self_account = SimpleNamespace(
        AccountEmail="self@test",
        AgentData=SimpleNamespace(AgentID=2, Map=map_self),
        AgentPartyData=SimpleNamespace(PartyID=777, PartyPosition=3),
        IsAccount=True,
    )
    leader_account = SimpleNamespace(
        AccountEmail="leader@test",
        AgentData=SimpleNamespace(AgentID=11, Map=SimpleNamespace(MapID=54, Region=2, District=1, Language=0)),
        AgentPartyData=SimpleNamespace(PartyID=777, PartyPosition=0),
        IsAccount=True,
    )
    follower_account = SimpleNamespace(
        AccountEmail="follower@test",
        AgentData=SimpleNamespace(AgentID=22, Map=SimpleNamespace(MapID=54, Region=2, District=1, Language=0)),
        AgentPartyData=SimpleNamespace(PartyID=777, PartyPosition=1),
        IsAccount=True,
    )
    stale_old_party_leader = SimpleNamespace(
        AccountEmail="stale@test",
        AgentData=SimpleNamespace(AgentID=999, Map=SimpleNamespace(MapID=54, Region=2, District=1, Language=0)),
        AgentPartyData=SimpleNamespace(PartyID=888, PartyPosition=0),
        IsAccount=True,
    )

    def _get_account_by_email(email: str):
        lookup = {
            "self@test": self_account,
            "leader@test": leader_account,
            "follower@test": follower_account,
            "stale@test": stale_old_party_leader,
        }
        return lookup.get(str(email or "").strip().lower())

    shmem = SimpleNamespace(
        GetAllAccountData=lambda: [stale_old_party_leader, follower_account, leader_account, self_account],
        GetAccountDataFromEmail=_get_account_by_email,
    )
    monkeypatch.setattr(transport_module.Player, "GetAccountEmail", staticmethod(lambda: "self@test"), raising=False)
    monkeypatch.setattr(transport_module.Party, "GetPartyLeaderID", staticmethod(lambda: 22), raising=False)
    monkeypatch.setattr(
        transport_module,
        "GLOBAL_CACHE",
        SimpleNamespace(
            Party=SimpleNamespace(GetPartyID=lambda: 777),
            ShMem=shmem,
        ),
        raising=False,
    )
    monkeypatch.setattr(
        transport_module.CustomBehaviorHelperParty,
        "_get_party_leader_email",
        staticmethod(lambda: "stale@test"),
    )

    try:
        resolved_email = transport_module.resolve_party_leader_email(SimpleNamespace())
        assert resolved_email == "leader@test"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_stats_binding_guard_rejects_mismatched_payload_name(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    stats_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_names_stats"
    )
    viewer = module.DropViewerWindow()
    try:
        should_bind = stats_module._should_bind_stats_to_rows(
            viewer,
            row_names=["Accursed Staff of Defense"],
            payload_name="Insightful Accursed Staff",
            first_line_name="",
        )
        assert should_bind is False
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_stats_binding_guard_allows_matching_or_missing_candidate(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    stats_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_names_stats"
    )
    viewer = module.DropViewerWindow()
    try:
        assert stats_module._should_bind_stats_to_rows(
            viewer,
            row_names=["Shiro's Return [Hard Mode]"],
            payload_name="",
            first_line_name="",
        )
        assert stats_module._should_bind_stats_to_rows(
            viewer,
            row_names=["Shiro's Return [Hard Mode]"],
            payload_name="Shiro's Return [Hard Mode]",
            first_line_name="",
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_stats_binding_guard_allows_camel_join_spacing_variants(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    stats_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_names_stats"
    )
    viewer = module.DropViewerWindow()
    try:
        assert stats_module._should_bind_stats_to_rows(
            viewer,
            row_names=["Dwarven Sage Outfit Monk Rune of Superior Divine Favor"],
            payload_name="Dwarven Sage Outfit Monk Rune of SuperiorDivine Favor",
            first_line_name="",
        )
        assert stats_module._should_bind_stats_to_rows(
            viewer,
            row_names=["Survivor Insignia Dwarven Scout Armor Rune of Vitae"],
            payload_name="Survivor InsigniaDwarven Scout Armor Rune of Vitae",
            first_line_name="",
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_stats_binding_guard_allows_joined_preposition_spacing_variant(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    stats_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_names_stats"
    )
    viewer = module.DropViewerWindow()
    try:
        assert stats_module._should_bind_stats_to_rows(
            viewer,
            row_names=["Radiant Insignia Titan Armor Warrior Rune of Superior Hammer Mastery"],
            payload_name="Radiant Insignia Titan Armor Warrior Runeof Superior Hammer Mastery",
            first_line_name="",
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_stats_binding_guard_allows_rune_first_line_subset_of_full_row_name(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    stats_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_names_stats"
    )
    viewer = module.DropViewerWindow()
    try:
        assert stats_module._should_bind_stats_to_rows(
            viewer,
            row_names=["Prodigy's Insignia [Mesmer] Titan Armor Monk Rune of Major Divine Favor"],
            payload_name="",
            first_line_name="Monk Rune of Major Divine Favor",
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_stats_mismatch_log_ignores_camel_join_spacing_variants(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    stats_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_names_stats"
    )
    viewer = module.DropViewerWindow()
    emitted: list[dict[str, object]] = []
    viewer._append_live_debug_log = lambda event, message, **fields: emitted.append(
        {"event": event, "message": message, **fields}
    )
    try:
        stats_module._append_stats_name_mismatch_debug_log(
            viewer,
            event_id="ev-camel-space",
            sender_email="sender@test",
            player_name="Player One",
            row_names=["Dwarven Sage Outfit Monk Rune of Superior Divine Favor"],
            payload_name="Dwarven Sage Outfit Monk Rune of SuperiorDivine Favor",
            first_line_name="",
            rendered_head="",
            update_source="payload",
        )
        assert emitted == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_stats_mismatch_log_ignores_rune_first_line_subset_of_full_row_name(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    stats_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_names_stats"
    )
    viewer = module.DropViewerWindow()
    emitted: list[dict[str, object]] = []
    viewer._append_live_debug_log = lambda event, message, **fields: emitted.append(
        {"event": event, "message": message, **fields}
    )
    try:
        stats_module._append_stats_name_mismatch_debug_log(
            viewer,
            event_id="ev-rune-subset",
            sender_email="sender@test",
            player_name="Player Four",
            row_names=["Prodigy's Insignia [Mesmer] Titan Armor Monk Rune of Major Divine Favor"],
            payload_name="",
            first_line_name="Monk Rune of Major Divine Favor",
            rendered_head="",
            update_source="text",
        )
        assert emitted == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_stats_mismatch_log_ignores_joined_preposition_spacing_variant(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    stats_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_names_stats"
    )
    viewer = module.DropViewerWindow()
    emitted: list[dict[str, object]] = []
    viewer._append_live_debug_log = lambda event, message, **fields: emitted.append(
        {"event": event, "message": message, **fields}
    )
    try:
        stats_module._append_stats_name_mismatch_debug_log(
            viewer,
            event_id="ev-joined-of",
            sender_email="sender@test",
            player_name="Player Four",
            row_names=["Radiant Insignia Titan Armor Warrior Rune of Superior Hammer Mastery"],
            payload_name="Radiant Insignia Titan Armor Warrior Runeof Superior Hammer Mastery",
            first_line_name="",
            rendered_head="",
            update_source="payload",
        )
        assert emitted == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_viewer_snapshot_stats_include_manual_shield_physical_reduction_line(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    snapshot = {
        "name": "Magmas Shield",
        "value": 85,
        "model_id": 321,
        "item_type": 24,
        "identified": True,
        "raw_mods": [(99999, 10, 65533)],
        "_source": "test",
        "_owner": "Leader",
    }
    try:
        stats = viewer._build_item_stats_from_snapshot(snapshot)
        assert "Received physical damage -3 (Chance: 10%)" in stats
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_stats_include_manual_shield_physical_reduction_line(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.mod_db = None
    sender_runtime_module = sys.modules.get(sender.__class__.__module__)
    assert sender_runtime_module is not None

    class _FakeMod:
        def GetIdentifier(self):
            return 99999

        def GetArg1(self):
            return 10

        def GetArg2(self):
            return 65533

    fake_mod = _FakeMod()
    fake_item_instance = SimpleNamespace(
        model_id=321,
        value=85,
        item_type=SimpleNamespace(ToInt=lambda: 24),
        modifiers=[fake_mod],
    )

    monkeypatch.setattr(module.Item, "IsNameReady", lambda _item_id: True, raising=False)
    monkeypatch.setattr(module.Item, "GetName", lambda _item_id: "Magmas Shield", raising=False)
    monkeypatch.setattr(module.Item, "RequestName", lambda _item_id: None, raising=False)
    monkeypatch.setattr(module.Item, "GetModelID", lambda _item_id: 321, raising=False)
    monkeypatch.setattr(module.Item, "GetItemType", lambda _item_id: (24, "Shield"), raising=False)
    monkeypatch.setattr(
        module.Item,
        "Usage",
        SimpleNamespace(IsIdentified=lambda _item_id: True),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Customization",
        SimpleNamespace(
            Modifiers=SimpleNamespace(GetModifiers=lambda _item_id: [fake_mod])
        ),
        raising=False,
    )
    monkeypatch.setattr(module.Item, "item_instance", lambda _item_id: fake_item_instance, raising=False)
    monkeypatch.setattr(sender_runtime_module, "Item", module.Item, raising=False)

    try:
        stats = sender._build_item_stats_text(42, "Magmas Shield")
        assert "Received physical damage -3 (Chance: 10%)" in stats
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_stats_do_not_add_manual_shield_line_for_non_shield_type(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.mod_db = None
    sender_runtime_module = sys.modules.get(sender.__class__.__module__)
    assert sender_runtime_module is not None

    class _FakeMod:
        def GetIdentifier(self):
            return 99999

        def GetArg1(self):
            return 10

        def GetArg2(self):
            return 65533

    fake_mod = _FakeMod()
    fake_item_instance = SimpleNamespace(
        model_id=358,
        value=236,
        item_type=SimpleNamespace(ToInt=lambda: 30),
        modifiers=[fake_mod],
    )

    monkeypatch.setattr(module.Item, "IsNameReady", lambda _item_id: True, raising=False)
    monkeypatch.setattr(module.Item, "GetName", lambda _item_id: "Stone Summit Badge", raising=False)
    monkeypatch.setattr(module.Item, "RequestName", lambda _item_id: None, raising=False)
    monkeypatch.setattr(module.Item, "GetModelID", lambda _item_id: 358, raising=False)
    monkeypatch.setattr(module.Item, "GetItemType", lambda _item_id: (30, "Focus"), raising=False)
    monkeypatch.setattr(
        module.Item,
        "Usage",
        SimpleNamespace(IsIdentified=lambda _item_id: True),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Customization",
        SimpleNamespace(
            Modifiers=SimpleNamespace(GetModifiers=lambda _item_id: [fake_mod])
        ),
        raising=False,
    )
    monkeypatch.setattr(module.Item, "item_instance", lambda _item_id: fake_item_instance, raising=False)
    monkeypatch.setattr(sender_runtime_module, "Item", module.Item, raising=False)

    try:
        stats = sender._build_item_stats_text(42, "Stone Summit Badge")
        assert "Received physical damage -3 (Chance: 10%)" not in stats
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_auto_buy_kits_allowed_in_configured_outpost(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    try:
        monkeypatch.setattr(module.Map, "IsOutpost", staticmethod(lambda: True), raising=False)
        monkeypatch.setattr(module.Map, "GetMapID", staticmethod(lambda: 156), raising=False)
        assert viewer._is_auto_buy_kits_allowed_outpost() is True
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_auto_buy_kits_rejected_for_unconfigured_outpost(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    try:
        monkeypatch.setattr(module.Map, "IsOutpost", staticmethod(lambda: True), raising=False)
        monkeypatch.setattr(module.Map, "GetMapID", staticmethod(lambda: 9999), raising=False)
        assert viewer._is_auto_buy_kits_allowed_outpost() is False
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_auto_buy_kits_rejected_outside_outpost(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    try:
        monkeypatch.setattr(module.Map, "IsOutpost", staticmethod(lambda: False), raising=False)
        assert viewer._is_auto_buy_kits_allowed_outpost() is False
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_same_slot_item_id_churn_for_same_item_does_not_emit_slot_replaced(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.last_inventory_snapshot = {
        (3, 3): ("Superior Salvage Kit", "White", 1, 239, 45),
    }
    new_snapshot = {
        (3, 3): ("Superior Salvage Kit", "White", 1, 239, 145),
    }

    queued_events: list[tuple[str, int, str, int, int]] = []
    monkeypatch.setattr(sender, "_take_inventory_snapshot", lambda: new_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    sender.last_snapshot_total = 1
    sender.last_snapshot_ready = 1
    sender.last_snapshot_not_ready = 0

    try:
        sender._process_inventory_deltas()
        assert queued_events == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_same_slot_item_id_churn_with_unresolved_name_does_not_emit_slot_replaced(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.last_inventory_snapshot = {
        (3, 3): ("Model#239", "White", 1, 239, 45),
    }
    new_snapshot = {
        (3, 3): ("Superior Salvage Kit", "White", 1, 239, 145),
    }

    queued_events: list[tuple[str, int, str, int, int]] = []
    monkeypatch.setattr(sender, "_take_inventory_snapshot", lambda: new_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    sender.last_snapshot_total = 1
    sender.last_snapshot_ready = 1
    sender.last_snapshot_not_ready = 0

    try:
        sender._process_inventory_deltas()
        assert queued_events == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_requires_recent_world_item_confirmation_for_inventory_delta(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.last_inventory_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
    }
    new_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("Fresh Pickup", "Gold", 1, 700, 99),
    }

    queued_events: list[tuple[str, int, str, int, int]] = []

    monkeypatch.setattr(sender, "_take_inventory_snapshot", lambda: new_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    sender.last_snapshot_total = 2
    sender.last_snapshot_ready = 2
    sender.last_snapshot_not_ready = 0

    try:
        sender._process_inventory_deltas()
        assert queued_events == []

        sender.last_inventory_snapshot = {
            (1, 1): ("Old Item", "White", 1, 500, 42),
        }
        sender.recent_world_item_disappearances = [
            {
                "agent_id": 4444,
                "item_id": 99,
                "model_id": 700,
                "qty": 1,
                "rarity": "Gold",
                "name": "Fresh Pickup",
                "disappeared_at": time.time(),
            }
        ]
        sender._process_inventory_deltas()
        assert queued_events == [("Fresh Pickup", 1, "Gold", 99, 700)]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_allows_fallback_for_new_item_when_world_candidates_are_empty(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.world_item_seen_since_reset = True
    sender.last_inventory_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
    }
    new_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("Fresh Pickup", "Gold", 1, 700, 99),
    }

    queued_events: list[tuple[str, int, str, int, int]] = []

    monkeypatch.setattr(sender, "_take_inventory_snapshot", lambda: new_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    sender.last_snapshot_total = 2
    sender.last_snapshot_ready = 2
    sender.last_snapshot_not_ready = 0
    sender.recent_world_item_disappearances = []
    sender.current_world_item_agents = {}

    try:
        sender._process_inventory_deltas()
        assert queued_events == [("Fresh Pickup", 1, "Gold", 99, 700)]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_suppresses_utility_kit_fallback_when_world_candidates_are_empty(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.world_item_seen_since_reset = True
    sender.last_inventory_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
    }
    new_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("Salvage Kit", "White", 1, 239, 99),
    }

    queued_events: list[tuple[str, int, str, int, int]] = []

    monkeypatch.setattr(sender, "_take_inventory_snapshot", lambda: new_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    sender.last_snapshot_total = 2
    sender.last_snapshot_ready = 2
    sender.last_snapshot_not_ready = 0
    sender.recent_world_item_disappearances = []
    sender.current_world_item_agents = {}

    try:
        sender._process_inventory_deltas()
        assert queued_events == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_does_not_fallback_accept_slot_replaced_when_world_candidates_are_empty(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.world_item_seen_since_reset = True
    sender.last_inventory_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("Existing Stack", "White", 20, 31154, 1001),
    }
    new_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("Zaishen Summoning Stones", "White", 20, 31154, 2002),
    }

    queued_events: list[tuple[str, int, str, int, int]] = []

    monkeypatch.setattr(sender, "_take_inventory_snapshot", lambda: new_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    sender.last_snapshot_total = 2
    sender.last_snapshot_ready = 2
    sender.last_snapshot_not_ready = 0
    sender.recent_world_item_disappearances = []
    sender.current_world_item_agents = {}

    try:
        sender._process_inventory_deltas()
        assert queued_events == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_accepts_live_world_item_confirmation_before_disappearance_poll(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.last_inventory_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
    }
    new_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("Fresh Pickup", "Gold", 1, 700, 99),
    }

    queued_events: list[tuple[str, int, str, int, int]] = []

    monkeypatch.setattr(sender, "_take_inventory_snapshot", lambda: new_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    sender.last_snapshot_total = 2
    sender.last_snapshot_ready = 2
    sender.last_snapshot_not_ready = 0
    sender.current_world_item_agents = {
        4444: {
            "agent_id": 4444,
            "item_id": 99,
            "model_id": 700,
            "qty": 1,
            "rarity": "Gold",
            "name": "Fresh Pickup",
        }
    }

    try:
        sender._process_inventory_deltas()
        assert queued_events == [("Fresh Pickup", 1, "Gold", 99, 700)]
        assert sender.current_world_item_agents == {}
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_accepts_tome_pickup_with_normalized_live_world_rarity(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.last_inventory_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
    }
    new_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("Elite Elementalist Tome", "Tomes", 1, 21789, 164),
    }

    queued_events: list[tuple[str, int, str, int, int]] = []

    monkeypatch.setattr(sender, "_take_inventory_snapshot", lambda: new_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    sender.last_snapshot_total = 2
    sender.last_snapshot_ready = 2
    sender.last_snapshot_not_ready = 0
    sender.current_world_item_agents = {
        4444: {
            "agent_id": 4444,
            "item_id": 164,
            "model_id": 21789,
            "qty": 1,
            "rarity": "Tomes",
            "name": "Elite Elementalist Tome",
        }
    }

    try:
        sender._process_inventory_deltas()
        assert queued_events == [("Elite Elementalist Tome", 1, "Tomes", 164, 21789)]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_inventory_identity_downgrades_stale_tome_name(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    inventory_module = sys.modules[module.DropTrackerSender.__module__.replace("drop_tracker_utility", "drop_tracker_inventory_runtime")]

    monkeypatch.setattr(
        inventory_module,
        "Item",
        SimpleNamespace(
            Type=SimpleNamespace(
                IsTome=lambda _item_id: True,
                IsMaterial=lambda _item_id: False,
                IsRareMaterial=lambda _item_id: False,
            )
        ),
        raising=False,
    )

    try:
        item_name, rarity, requested_refresh = inventory_module.coerce_consistent_item_identity(
            164,
            21791,
            "Bog Skale Fin",
            "White",
        )
        assert (item_name, rarity, requested_refresh) == ("Model#21791", "Tomes", True)
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_world_item_state_downgrades_stale_tome_name(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    world_module = sys.modules[module.DropTrackerSender.__module__.replace("drop_tracker_utility", "drop_tracker_world_items")]
    inventory_module = sys.modules[module.DropTrackerSender.__module__.replace("drop_tracker_utility", "drop_tracker_inventory_runtime")]

    requested_item_ids: list[int] = []
    monkeypatch.setattr(
        world_module,
        "Agent",
        SimpleNamespace(
            IsValid=lambda _agent_id: True,
            GetItemAgentItemID=lambda _agent_id: 164,
            GetItemAgentOwnerID=lambda _agent_id: 0,
        ),
        raising=False,
    )
    monkeypatch.setattr(world_module, "Player", SimpleNamespace(GetAgentID=lambda: 1), raising=False)
    monkeypatch.setattr(
        world_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda _item_id: 21791,
            Properties=SimpleNamespace(GetQuantity=lambda _item_id: 1),
            Rarity=SimpleNamespace(GetRarity=lambda _item_id: (0, "White")),
            Type=SimpleNamespace(
                IsTome=lambda _item_id: True,
                IsMaterial=lambda _item_id: False,
                IsRareMaterial=lambda _item_id: False,
            ),
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Bog Skale Fin",
            RequestName=lambda item_id: requested_item_ids.append(int(item_id)),
        ),
        raising=False,
    )
    monkeypatch.setattr(
        inventory_module,
        "Item",
        SimpleNamespace(
            Type=SimpleNamespace(
                IsTome=lambda _item_id: True,
                IsMaterial=lambda _item_id: False,
                IsRareMaterial=lambda _item_id: False,
            )
        ),
        raising=False,
    )

    sender = SimpleNamespace(_strip_tags=lambda text: text)

    try:
        state = world_module.build_world_item_state(sender, 4444)
        assert state is not None
        assert state["name"] == "Model#21791"
        assert state["rarity"] == "Tomes"
        assert requested_item_ids == [164]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_accepts_stack_increase_with_larger_live_world_stack_qty(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.last_inventory_snapshot = {
        (1, 12): ("Icy Hump", "White", 4, 490, 741),
    }
    new_snapshot = {
        (1, 12): ("Icy Hump", "White", 5, 490, 741),
    }

    queued_events: list[tuple[str, int, str, int, int]] = []

    monkeypatch.setattr(sender, "_take_inventory_snapshot", lambda: new_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    sender.last_snapshot_total = 1
    sender.last_snapshot_ready = 1
    sender.last_snapshot_not_ready = 0
    sender.current_world_item_agents = {
        4444: {
            "agent_id": 4444,
            "item_id": 9001,
            "model_id": 490,
            "qty": 2,
            "rarity": "White",
            "name": "Icy Hump",
        }
    }

    try:
        sender._process_inventory_deltas()
        assert queued_events == [("Icy Hump", 1, "White", 741, 490)]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_accepts_stack_increase_with_pluralized_live_world_name(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.last_inventory_snapshot = {
        (3, 1): ("Mergoyle Skull", "White", 2, 436, 20),
    }
    new_snapshot = {
        (3, 1): ("Mergoyle Skull", "White", 3, 436, 20),
    }

    queued_events: list[tuple[str, int, str, int, int]] = []

    monkeypatch.setattr(sender, "_take_inventory_snapshot", lambda: new_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    sender.last_snapshot_total = 1
    sender.last_snapshot_ready = 1
    sender.last_snapshot_not_ready = 0
    sender.current_world_item_agents = {
        4444: {
            "agent_id": 4444,
            "item_id": 9002,
            "model_id": 436,
            "qty": 2,
            "rarity": "White",
            "name": "Mergoyle Skulls",
        }
    }

    try:
        sender._process_inventory_deltas()
        assert queued_events == [("Mergoyle Skull", 1, "White", 20, 436)]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_stack_increase_prefers_previous_ready_name_when_current_name_flaps(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.last_inventory_snapshot = {
        (3, 1): ("Mergoyle Skull", "White", 2, 436, 20),
    }
    new_snapshot = {
        (3, 1): ("Longbow", "White", 3, 436, 20),
    }

    queued_events: list[tuple[str, int, str, int, int]] = []

    monkeypatch.setattr(sender, "_take_inventory_snapshot", lambda: new_snapshot)
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    sender.last_snapshot_total = 1
    sender.last_snapshot_ready = 1
    sender.last_snapshot_not_ready = 0
    sender.current_world_item_agents = {
        4444: {
            "agent_id": 4444,
            "item_id": 9002,
            "model_id": 436,
            "qty": 2,
            "rarity": "White",
            "name": "Mergoyle Skulls",
        }
    }

    try:
        sender._process_inventory_deltas()
        assert queued_events == [("Mergoyle Skull", 1, "White", 20, 436)]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_ready_zero_snapshot_resync_does_not_replay_inventory(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.is_warmed_up = True
    sender.warmup_grace_until = 0.0
    sender.session_startup_pending = False
    sender.carryover_inventory_snapshot = {}
    sender.last_inventory_snapshot = {(1, 1): ("Old Item", "White", 1, 500, 42)}
    sender.pending_slot_deltas = {(1, 2): {"qty": 1, "item_id": 43, "model_id": 600}}

    unstable_snapshot = {
        (1, 1): ("Model#500", "White", 1, 500, 42),
        (1, 2): ("Model#600", "Blue", 1, 600, 43),
    }
    stable_snapshot = {
        (1, 1): ("Old Item", "White", 1, 500, 42),
        (1, 2): ("New Item", "Blue", 1, 600, 43),
    }
    snapshots = [
        (unstable_snapshot, 2, 0),
        (stable_snapshot, 2, 2),
    ]
    queued_events: list[tuple[str, int, str, int, int]] = []

    def _fake_take_inventory_snapshot():
        snapshot, total, ready = snapshots.pop(0)
        sender.last_snapshot_total = total
        sender.last_snapshot_ready = ready
        return snapshot

    monkeypatch.setattr(sender, "_take_inventory_snapshot", _fake_take_inventory_snapshot)
    monkeypatch.setattr(
        sender,
        "_queue_drop",
        lambda item_name, quantity, rarity, _time_str, item_id, model_id, *_args, **_kwargs: queued_events.append(
            (str(item_name), int(quantity), str(rarity), int(item_id), int(model_id))
        ),
    )
    monkeypatch.setattr(sender, "_flush_outbox", lambda: 0)

    try:
        sender._process_inventory_deltas()
        assert sender.last_inventory_snapshot == unstable_snapshot
        assert sender.pending_slot_deltas == {}
        assert queued_events == []

        sender._process_inventory_deltas()
        assert sender.last_inventory_snapshot == stable_snapshot
        assert queued_events == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_late_name_refresh_sends_correction_with_original_signature(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()
    sender.pending_name_refresh_by_event = {}
    sender.outbox_queue = []
    sender.name_refresh_poll_interval_seconds = 0.0
    sender.name_refresh_ttl_seconds = 5.0
    sender.max_name_refresh_per_tick = 4
    sender.max_stats_builds_per_tick = 0

    sent_name_chunks: list[tuple[str, str, str, str]] = []

    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_stats_chunks", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        sender,
        "_send_name_chunks",
        lambda receiver_email, my_email, name_signature, full_name: sent_name_chunks.append(
            (str(receiver_email), str(my_email), str(name_signature), str(full_name))
        ) or True,
    )
    monkeypatch.setattr(
        sender_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda _item_id: 90,
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Prismatic Titan Armor of Superior Absorption",
            RequestName=lambda _item_id: None,
        ),
        raising=False,
    )

    try:
        sender._queue_drop(
            "Titan Armor",
            1,
            "Gold",
            "",
            572,
            90,
            (2, 5),
            "delta",
            is_leader_sender=False,
        )
        event_id = sender.outbox_queue[0]["event_id"]
        expected_sig = module.make_name_signature("Titan Armor")

        sender._flush_outbox()
        assert event_id in sender.pending_name_refresh_by_event
        sender.pending_name_refresh_by_event[event_id]["next_poll_at"] = 0.0

        sender._process_pending_name_refreshes()
        assert sent_name_chunks == [
            ("leader@test", "self@test", expected_sig, "Prismatic Titan Armor of Superior Absorption")
        ]
        assert event_id not in sender.pending_name_refresh_by_event
        assert sender.sent_event_stats_cache[event_id]["item_name"] == "Prismatic Titan Armor of Superior Absorption"
        assert sender.sent_event_stats_cache[event_id]["name_signature"] == expected_sig
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_late_name_refresh_resends_stats_after_unidentified_placeholder(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()
    sender.pending_name_refresh_by_event = {}
    sender.outbox_queue = []
    sender.name_refresh_poll_interval_seconds = 0.0
    sender.name_refresh_ttl_seconds = 5.0
    sender.max_name_refresh_per_tick = 4
    sender.max_stats_builds_per_tick = 0
    sender.refresh_stats_after_name_refresh = True

    sent_name_chunks: list[tuple[str, str, str, str]] = []
    sent_stats_chunks: list[tuple[str, str, str, str]] = []

    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        sender,
        "_send_stats_chunks",
        lambda receiver_email, my_email, event_id, stats_text: sent_stats_chunks.append(
            (str(receiver_email), str(my_email), str(event_id), str(stats_text))
        ) or True,
    )
    monkeypatch.setattr(
        sender,
        "_send_name_chunks",
        lambda receiver_email, my_email, name_signature, full_name: sent_name_chunks.append(
            (str(receiver_email), str(my_email), str(name_signature), str(full_name))
        ) or True,
    )
    monkeypatch.setattr(
        sender,
        "_build_item_stats_text",
        lambda item_id, item_name="": (
            "Prismatic Titan Armor of Superior Absorption\nArmor +10 (while attacking)\nValue: 200 gold"
            if int(item_id) == 572 and "Prismatic Titan Armor" in str(item_name or "")
            else "Unidentified"
        ),
    )
    monkeypatch.setattr(
        sender_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda _item_id: 90,
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Prismatic Titan Armor of Superior Absorption",
            RequestName=lambda _item_id: None,
        ),
        raising=False,
    )

    try:
        sender._queue_drop(
            "Titan Armor",
            1,
            "Gold",
            "",
            572,
            90,
            (2, 5),
            "delta",
            is_leader_sender=False,
        )
        event_id = sender.outbox_queue[0]["event_id"]
        sender.outbox_queue[0]["acked"] = False
        sender.outbox_queue[0]["stats_chunks_sent"] = False
        sender.outbox_queue[0]["stats_text"] = "Unidentified"
        sender.sent_event_stats_cache[event_id] = {
            "event_id": event_id,
            "item_id": 572,
            "model_id": 90,
            "item_name": "Titan Armor",
            "stats_text": "Unidentified",
            "name_signature": module.make_name_signature("Titan Armor"),
            "rarity": "Gold",
            "last_receiver_email": "leader@test",
            "created_at": time.time(),
            "updated_at": time.time(),
        }

        sender._flush_outbox()
        assert event_id in sender.pending_name_refresh_by_event
        sender.pending_name_refresh_by_event[event_id]["next_poll_at"] = 0.0

        sender._process_pending_name_refreshes()
        assert sent_name_chunks
        assert len(sent_stats_chunks) >= 2
        assert sent_stats_chunks[-1][2] == event_id
        assert "Prismatic Titan Armor of Superior Absorption" in sent_stats_chunks[-1][3]
        assert event_id not in sender.pending_name_refresh_by_event
        assert "Prismatic Titan Armor of Superior Absorption" in str(
            sender.sent_event_stats_cache[event_id].get("stats_text", "")
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_late_name_refresh_retries_stats_without_resending_name(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()
    sender.pending_name_refresh_by_event = {}
    sender.outbox_queue = []
    sender.name_refresh_poll_interval_seconds = 0.0
    sender.name_refresh_ttl_seconds = 5.0
    sender.max_name_refresh_per_tick = 4
    sender.max_stats_builds_per_tick = 0
    sender.refresh_stats_after_name_refresh = True

    sent_name_chunks: list[tuple[str, str, str, str]] = []
    sent_stats_chunks: list[tuple[str, str, str, str]] = []
    stats_attempts = {"count": 0}

    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        sender,
        "_send_stats_chunks",
        lambda receiver_email, my_email, event_id, stats_text: sent_stats_chunks.append(
            (str(receiver_email), str(my_email), str(event_id), str(stats_text))
        ) or True,
    )
    monkeypatch.setattr(
        sender,
        "_send_name_chunks",
        lambda receiver_email, my_email, name_signature, full_name, event_id=None: sent_name_chunks.append(
            (str(receiver_email), str(my_email), str(name_signature), str(full_name))
        ) or True,
    )

    def _build_stats(item_id, item_name=""):
        stats_attempts["count"] += 1
        if stats_attempts["count"] == 1:
            return "Unidentified"
        if int(item_id) == 572 and "Prismatic Titan Armor" in str(item_name or ""):
            return "Prismatic Titan Armor of Superior Absorption\nArmor +10 (while attacking)\nValue: 200 gold"
        return "Unidentified"

    monkeypatch.setattr(sender, "_build_item_stats_text", _build_stats)
    monkeypatch.setattr(
        sender_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda _item_id: 90,
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Prismatic Titan Armor of Superior Absorption",
            RequestName=lambda _item_id: None,
        ),
        raising=False,
    )

    try:
        sender._queue_drop(
            "Titan Armor",
            1,
            "Gold",
            "",
            572,
            90,
            (2, 5),
            "delta",
            is_leader_sender=False,
        )
        event_id = sender.outbox_queue[0]["event_id"]
        sender.outbox_queue[0]["acked"] = False
        sender.outbox_queue[0]["stats_chunks_sent"] = False
        sender.outbox_queue[0]["stats_text"] = "Unidentified"
        sender.sent_event_stats_cache[event_id] = {
            "event_id": event_id,
            "item_id": 572,
            "model_id": 90,
            "item_name": "Titan Armor",
            "stats_text": "Unidentified",
            "name_signature": module.make_name_signature("Titan Armor"),
            "rarity": "Gold",
            "last_receiver_email": "leader@test",
            "created_at": time.time(),
            "updated_at": time.time(),
        }

        sender._flush_outbox()
        assert event_id in sender.pending_name_refresh_by_event
        sender.pending_name_refresh_by_event[event_id]["next_poll_at"] = 0.0

        sender._process_pending_name_refreshes()
        assert len(sent_name_chunks) == 1
        assert sent_stats_chunks[-1][3] == "Unidentified"
        assert event_id in sender.pending_name_refresh_by_event
        assert sender.pending_name_refresh_by_event[event_id]["name_sent"] is True
        assert sender.pending_name_refresh_by_event[event_id]["item_name"] == "Prismatic Titan Armor of Superior Absorption"

        sender.pending_name_refresh_by_event[event_id]["next_poll_at"] = 0.0
        sender._process_pending_name_refreshes()
        assert len(sent_name_chunks) == 1
        assert "Prismatic Titan Armor of Superior Absorption" in sent_stats_chunks[-1][3]
        assert event_id not in sender.pending_name_refresh_by_event
        assert "Prismatic Titan Armor of Superior Absorption" in str(
            sender.sent_event_stats_cache[event_id].get("stats_text", "")
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_late_name_refresh_schedules_white_non_rune_items(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.pending_name_refresh_by_event = {}
    sender.outbox_queue = []
    sender.max_stats_builds_per_tick = 0

    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_stats_chunks", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_name_chunks", lambda *args, **kwargs: True)

    try:
        sender._queue_drop(
            "Molten Claw",
            1,
            "White",
            "",
            818,
            503,
            (2, 6),
            "delta",
            is_leader_sender=False,
        )
        event_id = sender.outbox_queue[0]["event_id"]

        sender._flush_outbox()
        assert event_id in sender.pending_name_refresh_by_event
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_late_name_refresh_corrects_white_non_rune_item(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()
    sender.pending_name_refresh_by_event = {}
    sender.outbox_queue = []
    sender.name_refresh_poll_interval_seconds = 0.0
    sender.name_refresh_ttl_seconds = 5.0
    sender.max_name_refresh_per_tick = 4
    sender.max_stats_builds_per_tick = 0

    sent_name_chunks: list[tuple[str, str, str, str]] = []

    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_stats_chunks", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        sender,
        "_send_name_chunks",
        lambda receiver_email, my_email, name_signature, full_name: sent_name_chunks.append(
            (str(receiver_email), str(my_email), str(name_signature), str(full_name))
        ) or True,
    )
    monkeypatch.setattr(
        sender_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda _item_id: 142,
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Spear",
            RequestName=lambda _item_id: None,
        ),
        raising=False,
    )

    try:
        sender._queue_drop(
            "Tengu Support Flares",
            1,
            "White",
            "",
            50,
            142,
            (2, 3),
            "delta",
            is_leader_sender=True,
        )
        event_id = sender.outbox_queue[0]["event_id"]
        expected_sig = module.make_name_signature("Tengu Support Flares")

        sender._flush_outbox()
        assert event_id in sender.pending_name_refresh_by_event
        sender.pending_name_refresh_by_event[event_id]["next_poll_at"] = 0.0

        sender._process_pending_name_refreshes()
        assert sent_name_chunks == [
            ("self@test", "self@test", expected_sig, "Spear")
        ]
        assert event_id not in sender.pending_name_refresh_by_event
        assert sender.sent_event_stats_cache[event_id]["item_name"] == "Spear"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_skips_name_chunks_for_white_non_rune_items(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.outbox_queue = []
    sender.max_stats_builds_per_tick = 0
    sent_name_chunks: list[tuple[str, str, str, str]] = []

    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_stats_chunks", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        sender,
        "_send_name_chunks",
        lambda receiver_email, my_email, name_signature, full_name: sent_name_chunks.append(
            (str(receiver_email), str(my_email), str(name_signature), str(full_name))
        ) or True,
    )

    try:
        sender._queue_drop(
            "Magmas Arm",
            1,
            "White",
            "",
            569,
            221,
            (1, 14),
            "delta",
            is_leader_sender=False,
        )
        sender.outbox_queue[0]["full_name"] = "Shocking Magmas Arm of Fortitude"
        sender._flush_outbox()
        assert sent_name_chunks == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_flush_outbox_keeps_acked_entry_until_stats_sent(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.outbox_queue = []
    sender.max_stats_builds_per_tick = 0

    sent_drops: list[tuple] = []
    sent_stats: list[tuple] = []

    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_name_chunks", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: sent_drops.append(args) or True)
    monkeypatch.setattr(
        sender,
        "_send_stats_chunks",
        lambda receiver_email, my_email, event_id, stats_text: sent_stats.append(
            (str(receiver_email), str(my_email), str(event_id), str(stats_text))
        ) or True,
    )

    try:
        sender._queue_drop(
            "Jeweled Staff",
            1,
            "Gold",
            "",
            355,
            352,
            (1, 16),
            "delta",
            is_leader_sender=False,
        )
        sender.outbox_queue[0]["acked"] = True
        sender.outbox_queue[0]["stats_chunks_sent"] = False
        sender.outbox_queue[0]["stats_text"] = ""

        sender._flush_outbox()

        assert len(sent_drops) == 0
        assert len(sent_stats) == 0
        assert len(sender.outbox_queue) == 1
        assert sender.outbox_queue[0]["acked"] is True
        assert sender.outbox_queue[0]["stats_chunks_sent"] is False
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_flush_outbox_removes_acked_entry_after_stats_sent(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.outbox_queue = []
    sender.max_stats_builds_per_tick = 0

    sent_drops: list[tuple] = []
    sent_stats: list[tuple] = []

    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_name_chunks", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: sent_drops.append(args) or True)
    monkeypatch.setattr(
        sender,
        "_send_stats_chunks",
        lambda receiver_email, my_email, event_id, stats_text: sent_stats.append(
            (str(receiver_email), str(my_email), str(event_id), str(stats_text))
        ) or True,
    )

    try:
        sender._queue_drop(
            "Jeweled Staff",
            1,
            "Gold",
            "",
            355,
            352,
            (1, 16),
            "delta",
            is_leader_sender=False,
        )
        sender.outbox_queue[0]["acked"] = True
        sender.outbox_queue[0]["stats_chunks_sent"] = False
        sender.outbox_queue[0]["stats_text"] = "Unidentified"

        sender._flush_outbox()

        assert len(sent_drops) == 0
        assert len(sent_stats) == 1
        assert len(sender.outbox_queue) == 1
        assert sender.outbox_queue[0]["stats_chunks_sent"] is True

        sender._flush_outbox()
        assert sender.outbox_queue == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_flush_outbox_keeps_acked_entry_with_pending_stats_even_after_retry_limit(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.outbox_queue = []
    sender.max_stats_builds_per_tick = 0
    sender.max_retry_attempts = 2

    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_name_chunks", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_stats_chunks", lambda *args, **kwargs: False)

    try:
        sender._queue_drop(
            "Titan Armor",
            1,
            "White",
            "",
            355,
            352,
            (1, 16),
            "delta",
            is_leader_sender=False,
        )
        sender.outbox_queue[0]["acked"] = True
        sender.outbox_queue[0]["stats_chunks_sent"] = False
        sender.outbox_queue[0]["stats_text"] = ""
        sender.outbox_queue[0]["attempts"] = int(sender.max_retry_attempts)

        sender._flush_outbox()

        assert len(sender.outbox_queue) == 1
        assert sender.outbox_queue[0]["acked"] is True
        assert sender.outbox_queue[0]["stats_chunks_sent"] is False
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_flush_outbox_uses_stats_fallback_after_defer_threshold(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.outbox_queue = []
    sender.max_stats_builds_per_tick = 0
    sender.stats_fallback_after_attempts = 1

    sent_stats: list[tuple[str, str, str, str]] = []
    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_name_chunks", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        sender,
        "_send_stats_chunks",
        lambda receiver_email, my_email, event_id, stats_text: sent_stats.append(
            (str(receiver_email), str(my_email), str(event_id), str(stats_text))
        ) or True,
    )

    try:
        sender._queue_drop(
            "Stone Summit Badge",
            1,
            "White",
            "",
            355,
            352,
            (1, 16),
            "delta",
            is_leader_sender=False,
        )
        sender.outbox_queue[0]["acked"] = True
        sender.outbox_queue[0]["stats_chunks_sent"] = False
        sender.outbox_queue[0]["stats_text"] = ""
        sender.outbox_queue[0]["stats_deferred_count"] = 0

        sender._flush_outbox()

        assert len(sent_stats) == 1
        assert "Stone Summit Badge" in sent_stats[0][3]
        assert sender.outbox_queue[0]["stats_chunks_sent"] is True
        assert sender.outbox_queue[0]["stats_fallback_used"] is True
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_resolve_event_item_id_prefers_slot_match_when_name_signature_changes(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()

    item_slots = {
        101: 5,
        102: 6,
    }
    item_names = {
        101: "Titan Armor Rune of Major Vigor",
        102: "Stone Summit Badge",
    }
    item_models = {
        101: 352,
        102: 352,
    }

    monkeypatch.setattr(
        sender_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda item_id: int(item_models.get(int(item_id), 0)),
            IsNameReady=lambda _item_id: True,
            GetName=lambda item_id: str(item_names.get(int(item_id), "")),
            RequestName=lambda _item_id: None,
            GetSlot=lambda item_id: int(item_slots.get(int(item_id), 0)),
            item_instance=lambda item_id: SimpleNamespace(
                slot=int(item_slots.get(int(item_id), 0)),
                model_id=int(item_models.get(int(item_id), 0)),
            ),
        ),
        raising=False,
    )
    monkeypatch.setattr(
        sender_module,
        "ItemArray",
        SimpleNamespace(
            CreateBagList=lambda *bag_ids: tuple(int(v) for v in bag_ids),
            GetItemArray=lambda bags: [101, 102] if 1 in list(bags or []) else [],
        ),
        raising=False,
    )

    try:
        resolved = sender._resolve_event_item_id_for_stats(
            {
                "item_id": 0,
                "model_id": 352,
                "name_signature": module.make_name_signature("Titan Armor"),
                "item_name": "Titan Armor",
                "bag_id": 1,
                "slot_id": 5,
            }
        )
        assert resolved == 101
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_resolve_event_item_id_does_not_fallback_to_stale_expected_item(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()

    monkeypatch.setattr(
        sender_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda item_id: 352 if int(item_id) == 101 else 0,
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Wrong Item",
            RequestName=lambda _item_id: None,
            GetSlot=lambda _item_id: 0,
            item_instance=lambda _item_id: SimpleNamespace(slot=0, model_id=352),
        ),
        raising=False,
    )
    monkeypatch.setattr(
        sender_module,
        "ItemArray",
        SimpleNamespace(
            CreateBagList=lambda *bag_ids: tuple(int(v) for v in bag_ids),
            GetItemArray=lambda _bags: [],
        ),
        raising=False,
    )

    try:
        resolved = sender._resolve_event_item_id_for_stats(
            {
                "item_id": 101,
                "model_id": 352,
                "name_signature": module.make_name_signature("Titan Armor"),
                "item_name": "Titan Armor",
                "bag_id": 1,
                "slot_id": 5,
            }
        )
        assert resolved == 0
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_identify_rearm_preserves_original_refresh_receiver(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()
    sender.pending_name_refresh_by_event = {}
    sender.outbox_queue = []
    sender.name_refresh_poll_interval_seconds = 0.0
    sender.name_refresh_ttl_seconds = 5.0
    sender.max_name_refresh_per_tick = 4
    sender.max_stats_builds_per_tick = 0

    sent_name_chunks: list[tuple[str, str, str, str]] = []

    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_stats_chunks", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        sender,
        "_send_name_chunks",
        lambda receiver_email, my_email, name_signature, full_name: sent_name_chunks.append(
            (str(receiver_email), str(my_email), str(name_signature), str(full_name))
        ) or True,
    )
    monkeypatch.setattr(
        sender_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda _item_id: 352,
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Shocking Jeweled Staff of Fortitude",
            RequestName=lambda _item_id: None,
        ),
        raising=False,
    )

    try:
        sender._queue_drop(
            "Jeweled Staff",
            1,
            "Gold",
            "",
            355,
            352,
            (1, 16),
            "delta",
            is_leader_sender=False,
        )
        event_id = sender.outbox_queue[0]["event_id"]
        expected_sig = module.make_name_signature("Jeweled Staff")

        sender._flush_outbox()
        assert sender.pending_name_refresh_by_event[event_id]["receiver_email"] == "leader@test"

        sender.schedule_name_refresh_for_item(355, 352)
        assert sender.pending_name_refresh_by_event[event_id]["receiver_email"] == "leader@test"

        sender.pending_name_refresh_by_event[event_id]["next_poll_at"] = 0.0
        sender._process_pending_name_refreshes()
        assert sent_name_chunks == [
            ("leader@test", "self@test", expected_sig, "Shocking Jeweled Staff of Fortitude")
        ]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_name_refresh_synthesizes_name_from_identified_modifiers(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()
    sender.pending_name_refresh_by_event = {}
    sender.outbox_queue = []
    sender.name_refresh_poll_interval_seconds = 0.0
    sender.name_refresh_ttl_seconds = 5.0
    sender.max_name_refresh_per_tick = 4
    sender.max_stats_builds_per_tick = 0
    sender.mod_db = object()

    sent_name_chunks: list[tuple[str, str, str, str]] = []

    fake_mod = SimpleNamespace(GetIdentifier=lambda: 1, GetArg1=lambda: 2, GetArg2=lambda: 3)
    fake_item_instance = SimpleNamespace(
        model_id=605,
        modifiers=[fake_mod],
        item_type=SimpleNamespace(ToInt=lambda: 26),
    )
    fake_parsed = SimpleNamespace(
        prefix=SimpleNamespace(weapon_mod=SimpleNamespace(name="Shocking")),
        suffix=SimpleNamespace(weapon_mod=SimpleNamespace(name="of Fortitude")),
        inherent=None,
    )

    monkeypatch.setattr(sender, "_resolve_party_leader_email", lambda: "leader@test")
    monkeypatch.setattr(sender, "_send_drop", lambda *args, **kwargs: True)
    monkeypatch.setattr(sender, "_send_stats_chunks", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        sender,
        "_send_name_chunks",
        lambda receiver_email, my_email, name_signature, full_name: sent_name_chunks.append(
            (str(receiver_email), str(my_email), str(name_signature), str(full_name))
        ) or True,
    )
    monkeypatch.setattr(sender_module, "ItemType", lambda value: value, raising=False)
    monkeypatch.setattr(sender_module, "parse_modifiers", lambda *_args, **_kwargs: fake_parsed, raising=False)
    monkeypatch.setattr(
        sender_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda _item_id: 605,
            GetItemType=lambda _item_id: (26, "Staff"),
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Earth Staff",
            RequestName=lambda _item_id: None,
            item_instance=lambda _item_id: fake_item_instance,
            Usage=SimpleNamespace(IsIdentified=lambda _item_id: True),
            Customization=SimpleNamespace(
                Modifiers=SimpleNamespace(GetModifiers=lambda _item_id: [fake_mod])
            ),
        ),
        raising=False,
    )

    try:
        sender._queue_drop(
            "Earth Staff",
            1,
            "Gold",
            "",
            572,
            605,
            (3, 3),
            "delta",
            is_leader_sender=False,
        )
        event_id = sender.outbox_queue[0]["event_id"]
        expected_sig = module.make_name_signature("Earth Staff")

        sender._flush_outbox()
        sender.pending_name_refresh_by_event[event_id]["next_poll_at"] = 0.0
        sender._process_pending_name_refreshes()

        assert sent_name_chunks == [
            ("leader@test", "self@test", expected_sig, "Shocking Earth Staff of Fortitude")
        ]
        assert sender.sent_event_stats_cache[event_id]["item_name"] == "Shocking Earth Staff of Fortitude"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_resolve_live_item_id_for_event_keeps_preferred_item_after_identify_name_change(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()
    sender.sent_event_stats_cache = {
        "ev-blue-staff": {
            "item_id": 42,
            "model_id": 500,
            "item_name": "Unidentified Blue Staff",
            "name_signature": "oldsig",
            "stats_text": "old stats",
            "created_at": time.time(),
        }
    }

    monkeypatch.setattr(
        sender_module,
        "ItemArray",
        SimpleNamespace(CreateBagList=lambda *_args: [], GetItemArray=lambda _bags: [42]),
        raising=False,
    )
    monkeypatch.setattr(
        sender_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda _item_id: 500,
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Jeweled Staff",
            RequestName=lambda _item_id: None,
        ),
        raising=False,
    )

    try:
        resolved = sender.resolve_live_item_id_for_event("ev-blue-staff", preferred_item_id=42)
        assert resolved == 42
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_resolve_live_item_id_for_event_allows_unknown_item_signature(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()
    sender.sent_event_stats_cache = {
        "ev-unknown-item": {
            "item_id": 42,
            "model_id": 500,
            "item_name": "Unknown Item",
            "name_signature": module.make_name_signature("Unknown Item"),
            "stats_text": "old stats",
            "created_at": time.time(),
        }
    }

    monkeypatch.setattr(
        sender_module,
        "ItemArray",
        SimpleNamespace(CreateBagList=lambda *_args: [], GetItemArray=lambda _bags: [42]),
        raising=False,
    )
    monkeypatch.setattr(
        sender_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda _item_id: 500,
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Completely Different Staff",
            RequestName=lambda _item_id: None,
        ),
        raising=False,
    )

    try:
        resolved = sender.resolve_live_item_id_for_event("ev-unknown-item", preferred_item_id=42)
        assert resolved == 42
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_resolve_live_item_id_for_event_rejects_ambiguous_inventory_matches(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_module = sys.modules[module.DropTrackerSender.__module__]
    sender = module.DropTrackerSender()
    sender.sent_event_stats_cache = {
        "ev-ambiguous": {
            "item_id": 0,
            "model_id": 500,
            "item_name": "Blue Staff",
            "name_signature": "",
            "stats_text": "old stats",
            "created_at": time.time(),
        }
    }

    monkeypatch.setattr(
        sender_module,
        "ItemArray",
        SimpleNamespace(CreateBagList=lambda *_args: [], GetItemArray=lambda _bags: [41, 42]),
        raising=False,
    )
    monkeypatch.setattr(
        sender_module,
        "Item",
        SimpleNamespace(
            GetModelID=lambda _item_id: 500,
            IsNameReady=lambda _item_id: True,
            GetName=lambda _item_id: "Blue Staff",
            RequestName=lambda _item_id: None,
        ),
        raising=False,
    )

    try:
        resolved = sender.resolve_live_item_id_for_event("ev-ambiguous", preferred_item_id=0)
        assert resolved == 0
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_local_row_stats_use_event_resolved_live_item_after_id_drift(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    row = [
        "2026-02-28 14:42:37",
        "Leader",
        "1",
        "Map",
        "Leader",
        "Unknown Staff",
        "1",
        "Blue",
        "ev-staff",
        "Pickup Stats",
        "42",
        "self@test",
    ]
    viewer.raw_drops = [row]

    monkeypatch.setattr(module.ItemArray, "CreateBagList", lambda *_args: [])
    monkeypatch.setattr(module.ItemArray, "GetItemArray", lambda _bags: [99])
    monkeypatch.setattr(module.Item, "IsNameReady", lambda _item_id: True)
    monkeypatch.setattr(module.Item, "GetName", lambda _item_id: "Identified Staff")
    monkeypatch.setattr(module.Item, "RequestName", lambda _item_id: None)
    monkeypatch.setattr(
        module.Item,
        "Rarity",
        SimpleNamespace(GetRarity=lambda _item_id: (0, "Blue")),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Usage",
        SimpleNamespace(IsIdentified=lambda _item_id: True),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "DropTrackerSender",
        lambda: SimpleNamespace(resolve_live_item_id_for_event=lambda event_id, preferred_item_id=0: 99),
    )
    monkeypatch.setattr(
        viewer,
        "_get_live_item_snapshot",
        lambda item_id, item_name="": {
            "name": "Identified Staff",
            "value": 0,
            "model_id": 500,
            "item_type": 26,
            "identified": True,
            "raw_mods": [(10328, 4, 0)],
        },
    )
    monkeypatch.setattr(viewer, "_build_item_stats_from_snapshot", lambda snapshot: "Identified Staff Stats")

    try:
        stats = viewer._get_row_stats_text(row)
        assert stats == "Identified Staff Stats"
        assert row[10] == "99"
        assert row[9] == "Identified Staff Stats"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_known_modifier_tracking_includes_manual_spellcast_and_condition_ids(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)

    try:
        expected_ids = {8712, 10248, 10280, 10328, 32784, 32880, 42290}
        assert expected_ids.issubset(set(module.UNKNOWN_MOD_EXCLUDE_IDS))
        for ident in expected_ids:
            assert int(ident) in module.UNKNOWN_MOD_KNOWN_NAME_HINTS
            assert str(module.UNKNOWN_MOD_KNOWN_NAME_HINTS[int(ident)]).strip()
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_prune_resolved_unknown_mod_entries_removes_known_hint_ids(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()

    viewer.unknown_mod_catalog = {
        "32880": viewer._normalize_unknown_mod_entry({"count": 2, "item_types": [26]}),
        "99999": viewer._normalize_unknown_mod_entry({"count": 1, "item_types": [26]}),
    }
    viewer.unknown_mod_pending_notes = {
        "32880": {"id": 32880, "count": 1, "owner": "Leader", "item": "Staff"},
        "99999": {"id": 99999, "count": 1, "owner": "Leader", "item": "Staff"},
    }

    try:
        removed = viewer._prune_resolved_unknown_mod_entries()
        assert removed == 1
        assert "32880" not in viewer.unknown_mod_catalog
        assert "32880" not in viewer.unknown_mod_pending_notes
        assert "99999" in viewer.unknown_mod_catalog
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_live_item_snapshot_survives_modifier_errors(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()

    monkeypatch.setattr(module.Item, "IsNameReady", lambda _item_id: True)
    monkeypatch.setattr(module.Item, "GetName", lambda _item_id: "Staff")
    monkeypatch.setattr(module.Item, "RequestName", lambda _item_id: None)
    monkeypatch.setattr(module.Item, "GetModelID", lambda _item_id: 500, raising=False)
    monkeypatch.setattr(module.Item, "GetItemType", lambda _item_id: (12, "Staff"), raising=False)
    monkeypatch.setattr(
        module.Item,
        "Properties",
        SimpleNamespace(GetValue=lambda _item_id: 123),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Customization",
        SimpleNamespace(
            Modifiers=SimpleNamespace(
                GetModifiers=lambda _item_id: (_ for _ in ()).throw(RuntimeError("mod fail"))
            )
        ),
        raising=False,
    )

    try:
        snapshot = viewer._get_live_item_snapshot(42, "")
        assert snapshot["name"] == "Staff"
        assert snapshot["value"] == 123
        assert snapshot["model_id"] == 500
        assert snapshot["item_type"] == 12
        assert snapshot["raw_mods"] == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_live_item_snapshot_synthesizes_identified_name_from_modifiers(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.mod_db = object()

    fake_mod = SimpleNamespace(GetIdentifier=lambda: 1, GetArg1=lambda: 2, GetArg2=lambda: 3)
    fake_item_instance = SimpleNamespace(
        model_id=605,
        modifiers=[fake_mod],
        item_type=SimpleNamespace(ToInt=lambda: 26),
    )
    fake_parsed = SimpleNamespace(
        prefix=SimpleNamespace(weapon_mod=SimpleNamespace(name="Shocking")),
        suffix=SimpleNamespace(weapon_mod=SimpleNamespace(name="of Fortitude")),
        inherent=None,
    )

    monkeypatch.setattr(module, "ItemType", lambda value: value, raising=False)
    monkeypatch.setattr(module, "parse_modifiers", lambda *_args, **_kwargs: fake_parsed, raising=False)
    monkeypatch.setattr(module.Item, "IsNameReady", lambda _item_id: True)
    monkeypatch.setattr(module.Item, "GetName", lambda _item_id: "Earth Staff")
    monkeypatch.setattr(module.Item, "RequestName", lambda _item_id: None)
    monkeypatch.setattr(module.Item, "GetModelID", lambda _item_id: 605, raising=False)
    monkeypatch.setattr(module.Item, "GetItemType", lambda _item_id: (26, "Staff"), raising=False)
    monkeypatch.setattr(
        module.Item,
        "Properties",
        SimpleNamespace(GetValue=lambda _item_id: 123),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Usage",
        SimpleNamespace(IsIdentified=lambda _item_id: True),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Customization",
        SimpleNamespace(Modifiers=SimpleNamespace(GetModifiers=lambda _item_id: [fake_mod])),
        raising=False,
    )
    monkeypatch.setattr(module.Item, "item_instance", lambda _item_id: fake_item_instance, raising=False)

    try:
        snapshot = viewer._get_live_item_snapshot(42, "")
        assert snapshot["name"] == "Shocking Earth Staff of Fortitude"
        assert snapshot["raw_mods"] == [(1, 2, 3)]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_live_item_snapshot_falls_back_to_item_instance_modifiers(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()

    class _FakeMod:
        def __init__(self, ident, arg1, arg2):
            self._ident = ident
            self._arg1 = arg1
            self._arg2 = arg2

        def GetIdentifier(self):
            return self._ident

        def GetArg1(self):
            return self._arg1

        def GetArg2(self):
            return self._arg2

    monkeypatch.setattr(module.Item, "IsNameReady", lambda _item_id: True)
    monkeypatch.setattr(module.Item, "GetName", lambda _item_id: "Blue Staff")
    monkeypatch.setattr(module.Item, "RequestName", lambda _item_id: None)
    monkeypatch.setattr(module.Item, "GetModelID", lambda _item_id: 500, raising=False)
    monkeypatch.setattr(module.Item, "GetItemType", lambda _item_id: (26, "Staff"), raising=False)
    monkeypatch.setattr(
        module.Item,
        "Properties",
        SimpleNamespace(GetValue=lambda _item_id: 123),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Customization",
        SimpleNamespace(
            Modifiers=SimpleNamespace(
                GetModifiers=lambda _item_id: (_ for _ in ()).throw(RuntimeError("mod fail"))
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "item_instance",
        lambda _item_id: SimpleNamespace(
            item_type=SimpleNamespace(ToInt=lambda: 26),
            modifiers=[_FakeMod(10328, 4, 0), _FakeMod(25288, 10, 0)],
        ),
        raising=False,
    )

    try:
        snapshot = viewer._get_live_item_snapshot(42, "")
        assert snapshot["raw_mods"] == [(10328, 4, 0), (25288, 10, 0)]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_live_item_snapshot_merges_customization_and_item_instance_modifiers(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()

    class _FakeMod:
        def __init__(self, ident, arg1, arg2):
            self._ident = ident
            self._arg1 = arg1
            self._arg2 = arg2

        def GetIdentifier(self):
            return self._ident

        def GetArg1(self):
            return self._arg1

        def GetArg2(self):
            return self._arg2

    monkeypatch.setattr(module.Item, "IsNameReady", lambda _item_id: True)
    monkeypatch.setattr(module.Item, "GetName", lambda _item_id: "Jeweled Staff")
    monkeypatch.setattr(module.Item, "RequestName", lambda _item_id: None)
    monkeypatch.setattr(module.Item, "GetModelID", lambda _item_id: 350, raising=False)
    monkeypatch.setattr(module.Item, "GetItemType", lambda _item_id: (26, "Staff"), raising=False)
    monkeypatch.setattr(
        module.Item,
        "Properties",
        SimpleNamespace(GetValue=lambda _item_id: 264),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Usage",
        SimpleNamespace(IsIdentified=lambda _item_id: True),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Customization",
        SimpleNamespace(
            Modifiers=SimpleNamespace(
                GetModifiers=lambda _item_id: [_FakeMod(42920, 22, 11), _FakeMod(10280, 20, 0), _FakeMod(25288, 10, 0)]
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "item_instance",
        lambda _item_id: SimpleNamespace(
            item_type=SimpleNamespace(ToInt=lambda: 26),
            modifiers=[_FakeMod(42920, 22, 11), _FakeMod(10280, 20, 0), _FakeMod(25288, 10, 0), _FakeMod(10328, 6, 0)],
        ),
        raising=False,
    )

    try:
        snapshot = viewer._get_live_item_snapshot(42, "")
        assert snapshot["raw_mods"] == [(42920, 22, 11), (10280, 20, 0), (25288, 10, 0), (10328, 6, 0)]
        payload = json.loads(viewer._build_item_snapshot_payload_from_live_item(42, ""))
        assert payload["mods"] == [[42920, 22, 11], [10280, 20, 0], [25288, 10, 0], [10328, 6, 0]]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_live_item_snapshot_hides_mods_until_identified(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()

    class _FakeMod:
        def __init__(self, ident, arg1, arg2):
            self._ident = ident
            self._arg1 = arg1
            self._arg2 = arg2

        def GetIdentifier(self):
            return self._ident

        def GetArg1(self):
            return self._arg1

        def GetArg2(self):
            return self._arg2

    monkeypatch.setattr(module.Item, "IsNameReady", lambda _item_id: True)
    monkeypatch.setattr(module.Item, "GetName", lambda _item_id: "Unidentified Blue Staff")
    monkeypatch.setattr(module.Item, "RequestName", lambda _item_id: None)
    monkeypatch.setattr(module.Item, "GetModelID", lambda _item_id: 500, raising=False)
    monkeypatch.setattr(module.Item, "GetItemType", lambda _item_id: (26, "Staff"), raising=False)
    monkeypatch.setattr(
        module.Item,
        "Properties",
        SimpleNamespace(GetValue=lambda _item_id: 123),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Usage",
        SimpleNamespace(IsIdentified=lambda _item_id: False),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Customization",
        SimpleNamespace(
            Modifiers=SimpleNamespace(
                GetModifiers=lambda _item_id: [_FakeMod(10328, 4, 0), _FakeMod(25288, 10, 0)]
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "item_instance",
        lambda _item_id: SimpleNamespace(
            item_type=SimpleNamespace(ToInt=lambda: 26),
            modifiers=[_FakeMod(10328, 4, 0), _FakeMod(25288, 10, 0)],
        ),
        raising=False,
    )

    try:
        snapshot = viewer._get_live_item_snapshot(42, "")
        payload = json.loads(viewer._build_item_snapshot_payload_from_live_item(42, ""))
        assert snapshot["identified"] is False
        assert snapshot["raw_mods"] == []
        assert viewer._build_item_stats_from_snapshot(snapshot) == "Unidentified"
        assert payload["i"] == 0
        assert payload["mods"] == []
        assert viewer._build_item_stats_from_payload_text(json.dumps(payload), "Unidentified Blue Staff") == "Unidentified"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_local_row_unidentified_stats_stay_minimal_until_identified(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    row = [
        "2026-02-28 14:42:37",
        "Leader",
        "1",
        "Map",
        "Leader",
        "Unidentified Blue Staff",
        "1",
        "Blue",
        "ev-unid-staff",
        "",
        "42",
        "self@test",
    ]
    viewer.raw_drops = [row]

    class _FakeMod:
        def __init__(self, ident, arg1, arg2):
            self._ident = ident
            self._arg1 = arg1
            self._arg2 = arg2

        def GetIdentifier(self):
            return self._ident

        def GetArg1(self):
            return self._arg1

        def GetArg2(self):
            return self._arg2

    identified_state = {"value": False}

    monkeypatch.setattr(module.ItemArray, "CreateBagList", lambda *_args: [])
    monkeypatch.setattr(module.ItemArray, "GetItemArray", lambda _bags: [42])
    monkeypatch.setattr(module.Item, "IsNameReady", lambda _item_id: True)
    monkeypatch.setattr(module.Item, "GetName", lambda _item_id: "Jeweled Staff" if identified_state["value"] else "Unidentified Blue Staff")
    monkeypatch.setattr(module.Item, "RequestName", lambda _item_id: None)
    monkeypatch.setattr(module.Item, "GetModelID", lambda _item_id: 500, raising=False)
    monkeypatch.setattr(module.Item, "GetItemType", lambda _item_id: (26, "Staff"), raising=False)
    monkeypatch.setattr(
        module.Item,
        "Rarity",
        SimpleNamespace(GetRarity=lambda _item_id: (0, "Blue")),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Properties",
        SimpleNamespace(GetValue=lambda _item_id: 123),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Usage",
        SimpleNamespace(IsIdentified=lambda _item_id: bool(identified_state["value"])),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Customization",
        SimpleNamespace(
            Modifiers=SimpleNamespace(
                GetModifiers=lambda _item_id: [_FakeMod(10328, 4, 0), _FakeMod(25288, 10, 0)] if identified_state["value"] else []
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "item_instance",
        lambda _item_id: SimpleNamespace(
            item_type=SimpleNamespace(ToInt=lambda: 26),
            modifiers=[_FakeMod(10328, 4, 0), _FakeMod(25288, 10, 0)] if identified_state["value"] else [],
        ),
        raising=False,
    )
    monkeypatch.setattr(module.Player, "GetName", lambda: "Leader")
    monkeypatch.setattr(
        module,
        "DropTrackerSender",
        lambda: SimpleNamespace(resolve_live_item_id_for_event=lambda event_id, preferred_item_id=0: 42),
    )
    monkeypatch.setattr(
        viewer,
        "_build_item_stats_from_snapshot",
        lambda snapshot: "Unidentified"
        if not bool(snapshot.get("identified", False))
        else "Halves casting time of Fire Magic spells (Chance: 20%)",
    )

    try:
        stats_cache_key = viewer._resolve_stats_cache_key_for_row(row)

        stats_before = viewer._get_row_stats_text(row)
        assert stats_before == "Unidentified"
        assert row[9] == "Unidentified"
        assert viewer.event_state_by_key[stats_cache_key]["identified"] is False

        identified_state["value"] = True
        stats_after = viewer._get_row_stats_text(row)
        assert stats_after != "Unidentified"
        assert "halves casting time" in stats_after.lower()
        assert row[9] == stats_after
        assert viewer.event_state_by_key[stats_cache_key]["identified"] is True
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_local_row_identified_basic_text_replaces_stale_unidentified(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    row = [
        "2026-03-05 19:16:25",
        "Leader",
        "1",
        "Map",
        "Leader",
        "Gladius",
        "1",
        "Blue",
        "ev-gladius-basic",
        "Unidentified",
        "42",
        "self@test",
    ]
    viewer.raw_drops = [row]
    viewer.selected_log_row = row

    stats_cache_key = viewer._resolve_stats_cache_key_for_row(row)
    viewer.event_state_by_key[stats_cache_key] = {"stats_text": "Unidentified", "identified": False}
    viewer.stats_by_event[stats_cache_key] = "Unidentified"

    monkeypatch.setattr(viewer, "_resolve_live_item_id_for_row", lambda _row, prefer_unidentified=False: 42)
    monkeypatch.setattr(
        viewer,
        "_get_live_item_snapshot",
        lambda item_id, item_name="": {
            "name": "Gladius",
            "value": 0,
            "model_id": 123,
            "item_type": 2,
            "identified": True,
            "raw_mods": [],
        },
    )
    monkeypatch.setattr(viewer, "_build_item_stats_from_snapshot", lambda snapshot: "Gladius")
    monkeypatch.setattr(viewer, "_stats_text_is_basic", lambda text: True)
    monkeypatch.setattr(module.Player, "GetName", lambda: "Leader")

    try:
        stats = viewer._get_row_stats_text(row)
        assert stats == "Gladius"
        assert row[9] == "Gladius"
        assert viewer.event_state_by_key[stats_cache_key]["identified"] is True
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_viewer_stats_text_message_ignores_late_unidentified_downgrade(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    shmem_names_stats_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_names_stats"
    )
    viewer = module.DropViewerWindow()
    row = [
        "2026-03-06 01:57:15",
        "Leader",
        "650",
        "Tasca's Demise",
        "Player Six",
        "Fiery Feathered Longbow of Defense",
        "1",
        "Gold",
        "ev-downgrade",
        (
            "Fiery Feathered Longbow of Defense\n"
            "Damage: 15-28\n"
            "Requires 11 Marksmanship\n"
            "Damage +14% (while Enchanted)\n"
            "Armor +5\n"
            "Value: 380 gold"
        ),
        "546",
        "peer@test",
    ]
    viewer.raw_drops = [row]
    viewer.selected_log_row = row
    stats_cache_key = viewer._make_stats_cache_key("ev-downgrade", "peer@test", "Player Six")
    existing_stats = str(row[9])
    viewer.event_state_by_key[stats_cache_key] = {"stats_text": existing_stats, "identified": True}
    viewer.stats_by_event[stats_cache_key] = existing_stats

    finished: list[tuple[str, int]] = []
    shmem = SimpleNamespace(MarkMessageAsFinished=lambda email, idx: finished.append((str(email), int(idx))))

    monkeypatch.setattr(viewer, "_resolve_sender_name_from_email", lambda _email: "Player Six")
    monkeypatch.setattr(
        shmem_names_stats_module,
        "handle_tracker_stats_text_branch",
        lambda **kwargs: kwargs["on_merged_text_fn"]("ev-downgrade", "Unidentified") or True,
    )

    try:
        result = shmem_names_stats_module.process_tracker_stats_text_message(
            viewer,
            extra_0="TrackerStatsV1",
            extra_data_list=[],
            shared_msg=SimpleNamespace(SenderEmail="peer@test"),
            my_email="self@test",
            msg_idx=17,
            now_ts=time.time(),
            is_leader_client=True,
            ignore_tracker_messages=False,
            shmem=shmem,
            to_text_fn=lambda value: str(value),
        )
        assert result == {"handled": 1, "processed": 1, "scanned": 1}
        assert row[9] == existing_stats
        assert viewer.stats_by_event[stats_cache_key] == existing_stats
        assert viewer.event_state_by_key[stats_cache_key]["stats_text"] == existing_stats
        assert finished == [("self@test", 17)]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_build_item_stats_text_returns_unidentified_until_identified(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender_runtime_module = sys.modules.get(sender.__class__.__module__)
    assert sender_runtime_module is not None

    monkeypatch.setattr(
        module.Item,
        "Usage",
        SimpleNamespace(IsIdentified=lambda _item_id: False),
        raising=False,
    )
    monkeypatch.setattr(sender_runtime_module, "Item", module.Item, raising=False)

    try:
        assert sender._build_item_stats_text(42, "Unidentified Blue Staff") == "Unidentified"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_build_item_stats_text_keeps_simple_item_name_and_value_when_identity_unavailable(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.mod_db = None
    sender_runtime_module = sys.modules.get(sender.__class__.__module__)
    assert sender_runtime_module is not None

    fake_item_instance = SimpleNamespace(
        model_id=502,
        value=8,
        item_type=SimpleNamespace(ToInt=lambda: 30),
        modifiers=[],
    )

    monkeypatch.setattr(module.Item, "IsNameReady", lambda _item_id: True, raising=False)
    monkeypatch.setattr(module.Item, "GetName", lambda _item_id: "Stone Summit Badge", raising=False)
    monkeypatch.setattr(module.Item, "RequestName", lambda _item_id: None, raising=False)
    monkeypatch.setattr(module.Item, "GetModelID", lambda _item_id: 502, raising=False)
    monkeypatch.setattr(module.Item, "GetItemType", lambda _item_id: (30, "Focus"), raising=False)
    monkeypatch.setattr(module.Item, "Usage", SimpleNamespace(), raising=False)
    monkeypatch.setattr(
        module.Item,
        "Customization",
        SimpleNamespace(
            Modifiers=SimpleNamespace(GetModifiers=lambda _item_id: [])
        ),
        raising=False,
    )
    monkeypatch.setattr(module.Item, "item_instance", lambda _item_id: fake_item_instance, raising=False)
    monkeypatch.setattr(sender_runtime_module, "Item", module.Item, raising=False)

    try:
        stats = sender._build_item_stats_text(42, "Stone Summit Badge")
        assert stats != "Unidentified"
        assert "Stone Summit Badge" in stats
        assert "Value: 8 gold" in stats
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_build_identified_name_from_modifiers_normalizes_armor_title(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender.mod_db = object()
    sender_runtime_module = sys.modules.get(sender.__class__.__module__)
    assert sender_runtime_module is not None

    parsed = SimpleNamespace(
        prefix=SimpleNamespace(rune=None, weapon_mod=SimpleNamespace(name="Hydromancer Insignia [Elementalist]")),
        suffix=SimpleNamespace(rune=None, weapon_mod=SimpleNamespace(name="Elementalist Rune of Superior Energy Storage")),
        inherent=None,
    )

    monkeypatch.setattr(sender_runtime_module, "parse_modifiers", lambda raw_mods, item_type, model_id, mod_db: parsed, raising=False)
    monkeypatch.setattr(sender_runtime_module, "ItemType", lambda value: value, raising=False)

    try:
        result = sender._build_identified_name_from_modifiers(
            "Titan Armor",
            [(8408, 10, 0), (8680, 12, 3)],
            89,
            92,
        )
        assert result == "Hydromancer Titan Armor of Superior Energy Storage"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_sender_collect_live_item_modifiers_merges_both_sources(monkeypatch):
    import importlib

    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender = module.DropTrackerSender()
    sender_runtime_module = sys.modules.get(sender.__class__.__module__)
    sender_stats_runtime = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_item_stats_runtime"
    )
    assert sender_runtime_module is not None

    class _FakeMod:
        def __init__(self, ident, arg1, arg2):
            self._ident = ident
            self._arg1 = arg1
            self._arg2 = arg2

        def GetIdentifier(self):
            return self._ident

        def GetArg1(self):
            return self._arg1

        def GetArg2(self):
            return self._arg2

    fake_item_instance = SimpleNamespace(
        model_id=350,
        value=264,
        item_type=SimpleNamespace(ToInt=lambda: 26),
        modifiers=[
            _FakeMod(42920, 22, 11),
            _FakeMod(10280, 20, 0),
            _FakeMod(25288, 10, 0),
            _FakeMod(10328, 6, 0),
        ],
    )

    monkeypatch.setattr(module.Item, "IsNameReady", lambda _item_id: True, raising=False)
    monkeypatch.setattr(module.Item, "GetName", lambda _item_id: "Jeweled Staff", raising=False)
    monkeypatch.setattr(module.Item, "RequestName", lambda _item_id: None, raising=False)
    monkeypatch.setattr(module.Item, "GetModelID", lambda _item_id: 350, raising=False)
    monkeypatch.setattr(module.Item, "GetItemType", lambda _item_id: (26, "Staff"), raising=False)
    monkeypatch.setattr(
        module.Item,
        "Usage",
        SimpleNamespace(IsIdentified=lambda _item_id: True),
        raising=False,
    )
    monkeypatch.setattr(
        module.Item,
        "Customization",
        SimpleNamespace(
            Modifiers=SimpleNamespace(
                GetModifiers=lambda _item_id: [_FakeMod(42920, 22, 11), _FakeMod(10280, 20, 0), _FakeMod(25288, 10, 0)]
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(module.Item, "item_instance", lambda _item_id: fake_item_instance, raising=False)
    monkeypatch.setattr(sender_runtime_module, "Item", module.Item, raising=False)
    monkeypatch.setattr(sender_stats_runtime, "Item", module.Item, raising=False)

    try:
        raw_mods = sender_stats_runtime._collect_live_item_modifiers(module.Item, 42, fake_item_instance)
        assert raw_mods == [(42920, 22, 11), (10280, 20, 0), (25288, 10, 0), (10328, 6, 0)]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_identify_item_from_row_keeps_visible_stats_until_refresh(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    row = [
        "2026-02-28 14:42:37",
        "Leader",
        "1",
        "Map",
        "Leader",
        "Icy Lodestone",
        "1",
        "White",
        "ev-identify",
        "Old Stats",
        "42",
        "self@test",
    ]
    viewer.selected_log_row = row
    viewer.raw_drops = [row]
    module.ItemArray.CreateBagList = lambda *_args: []
    module.ItemArray.GetItemArray = lambda _bags: [42]
    module.Item.IsNameReady = lambda _item_id: True
    module.Item.GetName = lambda _item_id: "Icy Lodestone"
    module.Item.RequestName = lambda _item_id: None
    module.Item.Usage.IsIdentified = lambda _item_id: False
    py4gw_mod.GLOBAL_CACHE.Inventory = SimpleNamespace(
        GetFirstIDKit=lambda: 99,
        IdentifyItem=lambda _item_id, _kit_id: True,
    )

    try:
        ok = viewer._identify_item_from_row(row)
        assert ok is True
        assert viewer._extract_row_item_stats(row) == "Old Stats"
        assert viewer._extract_row_item_stats(viewer.selected_log_row) == "Old Stats"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_request_remote_stats_for_row_prefers_sender_email_when_player_name_unresolved(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    row = [
        "2026-03-05 23:10:00",
        "Leader",
        "1",
        "Map",
        "Follower",
        "Titan Armor",
        "1",
        "White",
        "ev-remote-stats",
        "",
        "42",
        "peer@test",
    ]
    viewer.raw_drops = [row]
    sent_requests: list[tuple[str, str, str, str]] = []

    monkeypatch.setattr(module.Player, "GetName", lambda: "Leader")
    monkeypatch.setattr(module.Player, "GetAccountEmail", lambda: "self@test")
    monkeypatch.setattr(viewer, "_resolve_account_email_by_character_name", lambda _name: "")
    monkeypatch.setattr(
        viewer,
        "_send_inventory_action_to_email",
        lambda receiver_email, action_code, action_payload="", action_meta="": (
            sent_requests.append((str(receiver_email), str(action_code), str(action_payload), str(action_meta))) or True
        ),
    )

    try:
        viewer._request_remote_stats_for_row(row)
        assert sent_requests
        assert sent_requests[0] == ("peer@test", "push_item_stats", "42", "ev-remote-stats")
        stats_cache_key = viewer._resolve_stats_cache_key_for_row(row)
        assert float(viewer.remote_stats_pending_by_event.get(stats_cache_key, 0.0)) > 0.0
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_identify_item_from_row_prefers_sender_email_when_player_name_unresolved(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    row = [
        "2026-03-05 23:11:00",
        "Leader",
        "1",
        "Map",
        "Follower",
        "Titan Armor",
        "1",
        "White",
        "ev-remote-identify",
        "",
        "42",
        "peer@test",
    ]
    viewer.raw_drops = [row]
    sent_requests: list[tuple[str, str, str, str]] = []

    monkeypatch.setattr(module.Player, "GetName", lambda: "Leader")
    monkeypatch.setattr(module.Player, "GetAccountEmail", lambda: "self@test")
    monkeypatch.setattr(viewer, "_resolve_account_email_by_character_name", lambda _name: "")
    monkeypatch.setattr(
        viewer,
        "_send_inventory_action_to_email",
        lambda receiver_email, action_code, action_payload="", action_meta="": (
            sent_requests.append((str(receiver_email), str(action_code), str(action_payload), str(action_meta))) or True
        ),
    )

    try:
        ok = viewer._identify_item_from_row(row)
        assert ok is True
        assert sent_requests == [("peer@test", "id_item_id", "42", "ev-remote-identify")]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_collect_selected_item_stats_separates_unresolved_followers_by_sender_email(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    row_one = [
        "2026-03-05 23:12:00",
        "Leader",
        "1",
        "Map",
        "Follower",
        "Titan Armor",
        "1",
        "White",
        "ev-one",
        "",
        "42",
        "alpha@test",
    ]
    row_two = [
        "2026-03-05 23:12:01",
        "Leader",
        "1",
        "Map",
        "Follower",
        "Titan Armor",
        "1",
        "White",
        "ev-two",
        "",
        "43",
        "beta@test",
    ]
    viewer.raw_drops = [row_one, row_two]
    viewer.selected_item_key = ("Titan Armor", "White")

    try:
        stats = viewer._collect_selected_item_stats()
        assert stats is not None
        labels = [label for label, _data in stats["characters"]]
        assert labels == ["Follower [alpha]", "Follower [beta]"]
        assert viewer._find_best_row_for_item_and_character("Titan Armor", "White", "Follower [alpha]") == row_one
        assert viewer._find_best_row_for_item_and_character("Titan Armor", "White", "Follower [beta]") == row_two
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_parse_log_file_clears_transient_runtime_caches(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()

    viewer._log_drops_batch(
        [
            {
                "player_name": "Player One",
                "item_name": "Titan Armor",
                "quantity": 1,
                "extra_info": "White",
                "event_id": "ev-reload",
                "item_stats": "Old Stats",
                "item_id": 42,
                "sender_email": "peer@test",
            }
        ]
    )
    viewer.name_chunk_buffers = {"deadbeef": {"updated_at": 1.0, "chunks": {1: "Titan"}, "total": 1}}
    viewer.full_name_by_signature = {"deadbeef": "Titan Armor"}
    viewer.stats_chunk_buffers = {"stale": {"updated_at": 1.0, "chunks": {1: "Stats"}, "total": 1}}
    viewer.stats_payload_by_event = {"stale": "{\"n\":\"Titan Armor\"}"}
    viewer.stats_payload_chunk_buffers = {"stale": {"updated_at": 1.0, "chunks": {1: "{}"}, "total": 1}}
    viewer.event_state_by_key = {"stale": {"stats_text": "stale", "identified": True}}
    viewer.stats_render_cache_by_event = {"stale": {"text": "stale"}}
    viewer.stats_name_signature_by_event = {"stale": "deadbeef"}
    viewer.remote_stats_request_last_by_event = {"stale": 123.0}
    viewer.remote_stats_pending_by_event = {"stale": 456.0}

    try:
        viewer._parse_log_file(viewer.log_path)
        assert len(viewer.raw_drops) == 1
        assert viewer.name_chunk_buffers == {}
        assert viewer.full_name_by_signature == {}
        assert viewer.stats_chunk_buffers == {}
        assert viewer.stats_payload_by_event == {}
        assert viewer.stats_payload_chunk_buffers == {}
        assert viewer.event_state_by_key == {}
        assert viewer.stats_render_cache_by_event == {}
        assert viewer.stats_name_signature_by_event == {}
        assert viewer.remote_stats_request_last_by_event == {}
        assert viewer.remote_stats_pending_by_event == {}
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_pending_identify_mod_capture_rearms_sender_name_refresh(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    sender = module.DropTrackerSender()
    viewer.pending_identify_mod_capture = {42: time.time() + 10.0}

    cleared: list[tuple[int, int]] = []
    rearmed: list[tuple[int, int]] = []

    monkeypatch.setattr(
        module.Item,
        "Usage",
        SimpleNamespace(IsIdentified=lambda _item_id: True),
        raising=False,
    )
    monkeypatch.setattr(module.Item, "GetModelID", lambda _item_id: 90, raising=False)
    monkeypatch.setattr(sender, "clear_cached_event_stats_for_item", lambda item_id, model_id: cleared.append((int(item_id), int(model_id))))
    monkeypatch.setattr(sender, "schedule_name_refresh_for_item", lambda item_id, model_id: rearmed.append((int(item_id), int(model_id))) or 1)
    monkeypatch.setattr(viewer, "_build_item_stats_from_live_item", lambda _item_id, _fallback_name: "identified stats")

    try:
        viewer._process_pending_identify_mod_capture()
        assert cleared == [(42, 90)]
        assert rearmed == [(42, 90)]
        assert viewer.pending_identify_mod_capture == {}
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_reset_live_session_clears_tracker_linkage_state(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    viewer = module.DropViewerWindow()
    viewer.raw_drops = [["ts", "bot", "1", "Map", "Leader", "Icy Lodestone", "1", "White", "ev-1", "stats", "42", "self@test"]]
    viewer.aggregated_drops = {("Icy Lodestone", "White"): {"Quantity": 1, "Count": 1}}
    viewer.total_drops = 1
    viewer.seen_events = {"self@test:ev-1": 123.0}
    viewer.name_chunk_buffers = {"deadbeef": {"updated_at": 1.0, "chunks": {1: "Icy"}, "total": 1}}
    viewer.full_name_by_signature = {"deadbeef": "Icy Lodestone"}
    viewer.stats_by_event = {"email:self@test:ev-1": "stats"}
    viewer.stats_chunk_buffers = {"email:self@test:ev-1": {"updated_at": 1.0, "chunks": {1: "stats"}, "total": 1}}
    viewer.stats_payload_by_event = {"email:self@test:ev-1": "{\"mods\":[]}"}
    viewer.stats_payload_chunk_buffers = {"email:self@test:ev-1": {"updated_at": 1.0, "chunks": {1: "{}"}, "total": 1}}
    viewer.event_state_by_key = {"email:self@test:ev-1": {"identified": False, "stats_text": "Unidentified"}}
    viewer.stats_render_cache_by_event = {"email:self@test:ev-1": {"payload": "{}", "rendered": "stats", "updated_at": 1.0}}
    viewer.stats_name_signature_by_event = {"email:self@test:ev-1": "deadbeef"}
    viewer.remote_stats_request_last_by_event = {"email:self@test:ev-1": 10.0}
    viewer.remote_stats_pending_by_event = {"email:self@test:ev-1": 11.0}
    viewer.model_name_by_id = {500: "Icy Lodestone"}
    viewer._shmem_scan_start_index = 17

    try:
        viewer._reset_live_session()
        assert viewer.raw_drops == []
        assert viewer.aggregated_drops == {}
        assert viewer.total_drops == 0
        assert viewer.seen_events == {}
        assert viewer.name_chunk_buffers == {}
        assert viewer.full_name_by_signature == {}
        assert viewer.stats_by_event == {}
        assert viewer.stats_chunk_buffers == {}
        assert viewer.stats_payload_by_event == {}
        assert viewer.stats_payload_chunk_buffers == {}
        assert viewer.event_state_by_key == {}
        assert viewer.stats_render_cache_by_event == {}
        assert viewer.stats_name_signature_by_event == {}
        assert viewer.remote_stats_request_last_by_event == {}
        assert viewer.remote_stats_pending_by_event == {}
        assert viewer.model_name_by_id == {}
        assert viewer._shmem_scan_start_index == 0
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_viewer_duplicate_same_map_session_reset_preserves_existing_rows(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    session_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_session_runtime"
    )
    viewer = module.DropViewerWindow()
    viewer.raw_drops = [[
        "2026-03-04 18:58:00",
        "Viewer",
        "54",
        "Scoundrel's Rise",
        "Player Five",
        "Truncheon",
        "1",
        "Purple",
        "ev-keep",
        "",
        "101",
        "sender@test",
    ]]
    viewer.total_drops = 1
    viewer.last_session_reset_map_id = 54
    viewer.last_session_reset_started_at = time.time()
    reset_sender_calls: list[tuple[int, int]] = []
    reset_live_calls: list[str] = []
    flushed_calls: list[str] = []
    statuses: list[str] = []
    reset_logs: list[str] = []
    viewer._reset_sender_tracking_session = lambda current_map_id=0, current_instance_uptime_ms=0: reset_sender_calls.append(
        (int(current_map_id), int(current_instance_uptime_ms))
    )
    viewer._reset_live_session = lambda: reset_live_calls.append("reset")
    viewer._flush_pending_tracker_messages = lambda: flushed_calls.append("flush")
    viewer._log_reset_trace = lambda message, consume=False: reset_logs.append(str(message))
    viewer.set_status = lambda message: statuses.append(str(message))

    monkeypatch.setattr(module.time, "time", lambda: viewer.last_session_reset_started_at + 1.5, raising=False)
    monkeypatch.setattr(module.Player, "IsChatHistoryReady", staticmethod(lambda: False), raising=False)

    try:
        session_module.begin_new_explorable_session(
            viewer,
            "viewer_instance_reset",
            54,
            5000,
            "Auto reset on map change",
        )
        assert reset_sender_calls == []
        assert reset_live_calls == []
        assert flushed_calls == []
        assert viewer.total_drops == 1
        assert viewer.raw_drops[0][5] == "Truncheon"
        assert statuses == ["Auto reset on map change"]
        assert any("RESET TRACE preserved" in line for line in reset_logs)
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


class _HoverTestPyImGui:
    WindowFlags = SimpleNamespace(NoFlag=0)

    def __init__(self, *, mouse_pos=(0.0, 0.0), window_pos=(100.0, 100.0), window_size=(300.0, 200.0), window_hovered=False, opened=True):
        self._mouse_pos = tuple(float(v) for v in mouse_pos)
        self._window_pos = tuple(float(v) for v in window_pos)
        self._window_size = tuple(float(v) for v in window_size)
        self._window_hovered = bool(window_hovered)
        self._opened = bool(opened)

    def begin(self, _name, _flags=0):
        return self._opened

    def end(self):
        return None

    def get_window_pos(self):
        return self._window_pos

    def get_window_size(self):
        return self._window_size

    def is_window_hovered(self):
        return self._window_hovered

    def get_io(self):
        return SimpleNamespace(mouse_pos_x=self._mouse_pos[0], mouse_pos_y=self._mouse_pos[1])


class _HoverTestViewer:
    __module__ = "test_drop_viewer_hover_runtime"

    def __init__(self, pyimgui, *, hover_is_visible=True, hover_deadline=0.0, pin_open=False):
        self.window_name = "Drop Tracker Viewer"
        self.hover_handle_mode = True
        self.hover_pin_open = bool(pin_open)
        self.hover_is_visible = bool(hover_is_visible)
        self.hover_hide_delay_s = 0.35
        self.hover_hide_deadline = float(hover_deadline)
        self.viewer_window_initialized = True
        self.saved_viewer_window_pos = None
        self.saved_viewer_window_size = None
        self.last_main_window_rect = (0.0, 0.0, 0.0, 0.0)
        self.runtime_controls_popout = False
        self._pyimgui = pyimgui

    def _draw_hover_handle(self):
        return False

    def _persist_layout_value(self, _key, _value):
        return None

    def _flush_runtime_config_if_dirty(self):
        return None

    def _flush_unknown_mod_catalog_if_dirty(self):
        return None

    def _mouse_in_current_window_rect(self):
        io = self._pyimgui.get_io()
        wx, wy = self._pyimgui.get_window_pos()
        ww, wh = self._pyimgui.get_window_size()
        mx = float(io.mouse_pos_x)
        my = float(io.mouse_pos_y)
        return wx <= mx <= (wx + ww) and wy <= my <= (wy + wh)


def test_drop_viewer_hover_mode_keeps_window_visible_while_mouse_is_inside_gui(monkeypatch):
    runtime_name = _HoverTestViewer.__module__
    draw_module = importlib.import_module("Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_draw_window")
    pyimgui = _HoverTestPyImGui(mouse_pos=(150.0, 150.0), window_pos=(100.0, 100.0), window_size=(300.0, 200.0))
    runtime_mod = _set_module_attrs(
        types.ModuleType(runtime_name),
        PyImGui=pyimgui,
        ImGui=SimpleNamespace(),
        Map=SimpleNamespace(),
        Player=SimpleNamespace(),
        Py4GW=SimpleNamespace(),
    )
    monkeypatch.setitem(sys.modules, runtime_name, runtime_mod)
    def _stub_draw_main_gui(viewer, pyimgui, imgui, map_api, player_api, py4gw_api):
        wx, wy = pyimgui.get_window_pos()
        ww, wh = pyimgui.get_window_size()
        viewer.last_main_window_rect = (float(wx), float(wy), float(ww), float(wh))
        return bool(viewer._mouse_in_current_window_rect() or pyimgui.is_window_hovered())

    monkeypatch.setattr(draw_module, "_draw_main_gui", _stub_draw_main_gui)
    viewer = _HoverTestViewer(pyimgui, hover_is_visible=True, hover_deadline=0.0, pin_open=False)

    draw_module.draw_window(viewer)

    assert viewer.hover_is_visible is True
    assert viewer.hover_hide_deadline > 0.0
    assert viewer.last_main_window_rect == (100.0, 100.0, 300.0, 200.0)


def test_drop_viewer_hover_mode_hides_window_when_mouse_leaves_gui_and_not_pinned(monkeypatch):
    runtime_name = _HoverTestViewer.__module__
    draw_module = importlib.import_module("Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_draw_window")
    pyimgui = _HoverTestPyImGui(mouse_pos=(50.0, 50.0), window_pos=(100.0, 100.0), window_size=(300.0, 200.0))
    runtime_mod = _set_module_attrs(
        types.ModuleType(runtime_name),
        PyImGui=pyimgui,
        ImGui=SimpleNamespace(),
        Map=SimpleNamespace(),
        Player=SimpleNamespace(),
        Py4GW=SimpleNamespace(),
    )
    monkeypatch.setitem(sys.modules, runtime_name, runtime_mod)
    def _stub_draw_main_gui(viewer, pyimgui, imgui, map_api, player_api, py4gw_api):
        wx, wy = pyimgui.get_window_pos()
        ww, wh = pyimgui.get_window_size()
        viewer.last_main_window_rect = (float(wx), float(wy), float(ww), float(wh))
        return bool(viewer._mouse_in_current_window_rect() or pyimgui.is_window_hovered())

    monkeypatch.setattr(draw_module, "_draw_main_gui", _stub_draw_main_gui)
    viewer = _HoverTestViewer(pyimgui, hover_is_visible=True, hover_deadline=time.time() - 1.0, pin_open=False)

    draw_module.draw_window(viewer)

    assert viewer.hover_is_visible is False


def test_drop_viewer_hover_mode_keeps_window_visible_when_mouse_is_inside_window_rect(monkeypatch):
    runtime_name = _HoverTestViewer.__module__
    draw_module = importlib.import_module("Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_draw_window")
    pyimgui = _HoverTestPyImGui(mouse_pos=(150.0, 150.0), window_pos=(100.0, 100.0), window_size=(300.0, 200.0))
    runtime_mod = _set_module_attrs(
        types.ModuleType(runtime_name),
        PyImGui=pyimgui,
        ImGui=SimpleNamespace(),
        Map=SimpleNamespace(),
        Player=SimpleNamespace(),
        Py4GW=SimpleNamespace(),
    )
    monkeypatch.setitem(sys.modules, runtime_name, runtime_mod)

    def _stub_draw_main_gui(viewer, pyimgui, imgui, map_api, player_api, py4gw_api):
        wx, wy = pyimgui.get_window_pos()
        ww, wh = pyimgui.get_window_size()
        viewer.last_main_window_rect = (float(wx), float(wy), float(ww), float(wh))
        return False

    monkeypatch.setattr(draw_module, "_draw_main_gui", _stub_draw_main_gui)
    viewer = _HoverTestViewer(pyimgui, hover_is_visible=True, hover_deadline=time.time() - 1.0, pin_open=False)

    draw_module.draw_window(viewer)

    assert viewer.hover_is_visible is True
    assert viewer.hover_hide_deadline > 0.0


def test_party_leader_email_ignores_stale_cached_value(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    py4gw_mod = _install_runtime_stubs(monkeypatch, tmp_path)
    module_name = "Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers_party"
    widget_module_name = "Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory"
    sys.modules.pop(module_name, None)
    monkeypatch.setitem(
        sys.modules,
        widget_module_name,
        _set_module_attrs(
            types.ModuleType(widget_module_name),
            CustomBehaviorWidgetMemoryManager=lambda: SimpleNamespace(
                GetCustomBehaviorWidgetData=lambda: SimpleNamespace(
                    party_target_id=None,
                    party_leader_email=None,
                )
            ),
        ),
    )
    helper_module = importlib.import_module(module_name)
    helper_module.MemoryCacheManager().refresh()

    leader_account = SimpleNamespace(
        AccountEmail="leader@test",
        AgentData=SimpleNamespace(
            AgentID=1,
            Map=SimpleNamespace(MapID=1, Region=2, District=3, Language=4),
        ),
        AgentPartyData=SimpleNamespace(PartyID=777, PartyPosition=0),
    )

    monkeypatch.setattr(py4gw_mod.Map, "GetRegion", staticmethod(lambda: (2, 0)), raising=False)
    monkeypatch.setattr(py4gw_mod.Map, "GetDistrict", staticmethod(lambda: 3), raising=False)
    monkeypatch.setattr(py4gw_mod.Map, "GetLanguage", staticmethod(lambda: (4, 0)), raising=False)
    monkeypatch.setattr(py4gw_mod.Map, "IsExplorable", staticmethod(lambda: False), raising=False)
    py4gw_mod.GLOBAL_CACHE.Party = SimpleNamespace(GetPartyLeaderID=lambda: 1, GetPartyID=lambda: 777)
    py4gw_mod.GLOBAL_CACHE.ShMem = SimpleNamespace(
        GetAccountDataFromEmail=lambda email: leader_account if str(email) == "leader@test" else None,
        GetAllAccountData=lambda: [leader_account],
    )
    helper_module.MemoryCacheManager().set("party_leader_email", "stale@test")

    try:
        resolved_email = helper_module.CustomBehaviorHelperParty._get_party_leader_email()
        assert resolved_email == "leader@test"
        assert helper_module.MemoryCacheManager().get("party_leader_email") == "leader@test"
    finally:
        helper_module.MemoryCacheManager().refresh()
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_stats_normalization_preserves_combined_armor_requirement_lines(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    sender_runtime = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_item_stats_runtime"
    )
    viewer = module.DropViewerWindow()

    try:
        source_lines = [
            "Prismatic Dolyak Cladding",
            "Armor: 38",
            "Armor +5 (Requires 9 Air Magic)",
            "Armor +5 (Requires 9 Earth Magic)",
            "Armor +5 (Requires 9 Fire Magic)",
            "Armor +5 (Requires 9 Water Magic)",
            "Value: 70 gold",
        ]
        normalized_sender = sender_runtime.normalize_stats_lines(SimpleNamespace(), source_lines)
        assert normalized_sender == source_lines

        normalized_viewer = viewer._normalize_stats_text("\n".join(source_lines))
        assert normalized_viewer.splitlines() == source_lines
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_tracker_stats_payload_binding_persists_late_payload_stats_to_log_file(monkeypatch):
    tmp_path = _make_local_tmp_dir()
    module, _py4gw_mod = _import_start_drop_viewer(monkeypatch, tmp_path)
    shmem_names_stats = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_viewer_shmem_names_stats"
    )
    log_store_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_log_store"
    )
    protocol_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol"
    )
    model_module = importlib.import_module(
        "Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models"
    )

    viewer = module.DropViewerWindow()
    log_path = tmp_path / "drop_log.csv"
    viewer.log_path = str(log_path)
    viewer.raw_drops = [[
        "2026-03-06 02:48:25",
        "Viewer",
        "92",
        "Tasca's Demise",
        "Player Two",
        "Earthbound Dwarven Scout Armor of Major Soul Reaping",
        "1",
        "Purple",
        "ev-payload-persist",
        "Unidentified",
        "431",
        "sender@test",
    ]]
    original_row = model_module.DropLogRow.from_runtime_row(viewer.raw_drops[0])
    assert original_row is not None
    log_store_module.append_drop_log_rows(str(log_path), [original_row])

    payload_text = json.dumps(
        {
            "n": "Earthbound Dwarven Scout Armor of Major Soul Reaping",
            "i": 1,
            "mods": [],
        }
    )
    rendered_stats = (
        "Earthbound Dwarven Scout Armor of Major Soul Reaping\n"
        "Armor +15 (vs. Earth damage)\n"
        "+2 Soul Reaping (Non-stacking)\n"
        "-35 Health\n"
        "Earthbound Insignia [Ranger]\n"
        "Necromancer Rune of Major Soul Reaping\n"
        "Value: 192 gold"
    )
    monkeypatch.setattr(viewer, "_resolve_sender_name_from_email", lambda _email: "Player Two")
    monkeypatch.setattr(viewer, "_render_payload_stats_cached", lambda *_args, **_kwargs: rendered_stats)

    chunks = protocol_module.build_name_chunks(payload_text, 24)
    shmem = _FakeShMem([])
    shared_msg = _FakeSharedMsg(
        receiver_email="self@test",
        sender_email="sender@test",
        command=997,
        extra_data=[],
    )

    try:
        for idx, total, chunk in chunks:
            result = shmem_names_stats.process_tracker_stats_payload_message(
                viewer,
                extra_0="TrackerStatsV2",
                extra_data_list=[
                    "TrackerStatsV2",
                    "ev-payload-persist",
                    chunk,
                    protocol_module.encode_name_chunk_meta(idx, total),
                ],
                shared_msg=shared_msg,
                my_email="self@test",
                msg_idx=idx,
                now_ts=time.time(),
                is_leader_client=True,
                ignore_tracker_messages=False,
                shmem=shmem,
                to_text_fn=str,
            )
            assert result["handled"] == 1

        parsed = log_store_module.parse_drop_log_file(str(log_path))
        assert len(parsed) == 1
        assert parsed[0].item_name == "Earthbound Dwarven Scout Armor of Major Soul Reaping"
        assert parsed[0].item_stats == rendered_stats
        assert viewer.raw_drops[0][9] == rendered_stats
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)
