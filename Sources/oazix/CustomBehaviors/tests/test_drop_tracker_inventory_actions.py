from __future__ import annotations

import sys
import time
import types

import pytest

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_actions import IdentifyResponseScheduler
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_actions import run_inventory_action


class _FakeScheduler:
    def __init__(self) -> None:
        self.calls = []

    def schedule(self, item_id, reply_email, event_id, timeout_s=2.0):
        self.calls.append((int(item_id), str(reply_email), str(event_id), float(timeout_s)))


class _FakeViewer:
    def __init__(self) -> None:
        self.status_message = ""
        self.identify_calls = []
        self.salvage_calls = []
        self.identify_response_scheduler = _FakeScheduler()
        self.auto_id_enabled = False
        self.auto_salvage_enabled = False
        self.selected_id_rarities = ["Blue", "Purple"]
        self.selected_salvage_rarities = ["Gold"]
        self.payload_text = ""
        self.payload_send_ok = False
        self.stats_text = "Stats Line"
        self.stats_send_ok = True
        self.resolved_item_id = 0
        self.resolved_item_id_by_sig = 0
        self._snapshot_calls = []
        self._stats_calls = []

    def _ensure_text(self, value):
        return "" if value is None else str(value)

    def set_status(self, msg: str):
        self.status_message = str(msg)

    def _queue_identify_for_rarities(self, rarities):
        self.identify_calls.append(list(rarities))
        return len(rarities)

    def _queue_salvage_for_rarities(self, rarities):
        self.salvage_calls.append(list(rarities))
        return len(rarities)

    def _decode_rarities(self, payload):
        return [r for r in str(payload).split(",") if r]

    def _get_selected_id_rarities(self):
        return list(self.selected_id_rarities)

    def _get_selected_salvage_rarities(self):
        return list(self.selected_salvage_rarities)

    def _bitmask_to_rarities(self, mask):
        ordered = ("White", "Blue", "Green", "Purple", "Gold")
        result = []
        m = int(mask)
        for idx, rarity in enumerate(ordered):
            if (m & (1 << idx)) != 0:
                result.append(rarity)
        return result

    def _apply_auto_id_config_payload(self, payload):
        text = str(payload or "").strip()
        if ":" not in text:
            return
        enabled_txt, mask_txt = text.split(":", 1)
        if enabled_txt.strip() in ("0", "1"):
            self.auto_id_enabled = enabled_txt.strip() == "1"
        self.selected_id_rarities = self._bitmask_to_rarities(int(mask_txt.strip()))

    def _apply_auto_salvage_config_payload(self, payload):
        text = str(payload or "").strip()
        if ":" not in text:
            return
        enabled_txt, mask_txt = text.split(":", 1)
        if enabled_txt.strip() in ("0", "1"):
            self.auto_salvage_enabled = enabled_txt.strip() == "1"
        self.selected_salvage_rarities = self._bitmask_to_rarities(int(mask_txt.strip()))

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return int(default)

    def _build_item_snapshot_payload_from_live_item(self, item_id, item_name=""):
        self._snapshot_calls.append((int(item_id), str(item_name)))
        return str(self.payload_text)

    def _send_tracker_stats_payload_chunks_to_email(self, receiver_email, event_id, payload_text):
        return bool(self.payload_send_ok)

    def _build_item_stats_from_live_item(self, item_id, item_name=""):
        self._stats_calls.append((int(item_id), str(item_name)))
        return str(self.stats_text)

    def _send_tracker_stats_chunks_to_email(self, receiver_email, event_id, stats_text):
        return bool(self.stats_send_ok)

    def _clean_item_name(self, name):
        return self._ensure_text(name).strip()

    def _resolve_live_item_id_by_name(self, item_name, prefer_identified=False):
        return int(self.resolved_item_id)

    def _resolve_live_item_id_by_signature(self, name_signature, rarity_hint="", prefer_identified=False):
        return int(self.resolved_item_id_by_sig)


def _install_fake_py4gw(
    monkeypatch,
    *,
    kit_id=1,
    identified=False,
    identify_result=True,
    identify_raises=False,
    kit_raises=False,
):
    class _Inventory:
        def GetFirstIDKit(self):
            if kit_raises:
                raise TypeError("kit lookup failed")
            return int(kit_id)

        def IdentifyItem(self, item_id, kit):
            if identify_raises:
                raise RuntimeError("identify boom")
            return identify_result

    class _GlobalCache:
        Inventory = _Inventory()

    class _Usage:
        @staticmethod
        def IsIdentified(_item_id):
            return bool(identified)

    class _Item:
        Usage = _Usage()

    py4gw_mod = types.ModuleType("Py4GWCoreLib")
    py4gw_mod.GLOBAL_CACHE = _GlobalCache()
    item_mod = types.ModuleType("Py4GWCoreLib.Item")
    item_mod.Item = _Item
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib", py4gw_mod)
    monkeypatch.setitem(sys.modules, "Py4GWCoreLib.Item", item_mod)


def test_identify_scheduler_sends_payload_when_identified():
    scheduler = IdentifyResponseScheduler()
    scheduler.schedule(item_id=42, reply_email="leader@test", event_id="ev-1", timeout_s=0.5)

    sent_payload = []
    sent_stats = []

    completed = scheduler.tick(
        build_payload_fn=lambda _item_id: '{"mods":[]}',
        is_identified_fn=lambda _item_id: True,
        send_payload_fn=lambda email, event_id, payload: sent_payload.append((email, event_id, payload)) or True,
        build_stats_fn=lambda _item_id: "",
        send_stats_fn=lambda email, event_id, stats: sent_stats.append((email, event_id, stats)) or True,
    )

    assert completed == 1
    assert len(sent_payload) == 1
    assert not sent_stats
    assert scheduler.pending_count() == 0


def test_identify_scheduler_falls_back_to_stats_on_timeout():
    scheduler = IdentifyResponseScheduler()
    scheduler.schedule(item_id=99, reply_email="leader@test", event_id="ev-timeout", timeout_s=0.2)

    sent_payload = []
    sent_stats = []

    completed = scheduler.tick(
        build_payload_fn=lambda _item_id: "",
        is_identified_fn=lambda _item_id: False,
        send_payload_fn=lambda email, event_id, payload: sent_payload.append((email, event_id, payload)) or True,
        build_stats_fn=lambda _item_id: "fallback stats",
        send_stats_fn=lambda email, event_id, stats: sent_stats.append((email, event_id, stats)) or True,
    )
    assert completed == 0
    assert scheduler.pending_count() == 1

    time.sleep(0.25)
    completed = scheduler.tick(
        build_payload_fn=lambda _item_id: "",
        is_identified_fn=lambda _item_id: False,
        send_payload_fn=lambda email, event_id, payload: sent_payload.append((email, event_id, payload)) or True,
        build_stats_fn=lambda _item_id: "fallback stats",
        send_stats_fn=lambda email, event_id, stats: sent_stats.append((email, event_id, stats)) or True,
    )

    assert completed == 1
    assert not sent_payload
    assert len(sent_stats) == 1
    assert sent_stats[0][1] == "ev-timeout"
    assert scheduler.pending_count() == 0


def test_identify_scheduler_skips_until_next_poll_and_clear():
    scheduler = IdentifyResponseScheduler()
    scheduler.schedule(item_id=100, reply_email="leader@test", event_id="ev-skip", timeout_s=2.0)
    pending_obj = next(iter(scheduler._pending.values()))
    pending_obj.next_poll_at = time.time() + 10.0

    completed = scheduler.tick(
        build_payload_fn=lambda _item_id: '{"mods":[]}',
        is_identified_fn=lambda _item_id: True,
        send_payload_fn=lambda _email, _event_id, _payload: True,
        build_stats_fn=lambda _item_id: "",
        send_stats_fn=lambda _email, _event_id, _stats: True,
    )
    assert completed == 0
    assert scheduler.pending_count() == 1

    scheduler.clear()
    assert scheduler.pending_count() == 0


def test_identify_scheduler_retries_after_timeout_when_sends_fail():
    scheduler = IdentifyResponseScheduler()
    scheduler.schedule(item_id=5, reply_email="leader@test", event_id="ev-fail", timeout_s=0.2)
    time.sleep(0.25)

    completed = scheduler.tick(
        build_payload_fn=lambda _item_id: '{"mods":[]}',
        is_identified_fn=lambda _item_id: False,
        send_payload_fn=lambda _email, _event_id, _payload: False,
        build_stats_fn=lambda _item_id: "fallback",
        send_stats_fn=lambda _email, _event_id, _stats: False,
    )
    assert completed == 0
    assert scheduler.pending_count() == 1

    saw_completion = 0
    for _ in range(5):
        time.sleep(0.26)
        completed = scheduler.tick(
            build_payload_fn=lambda _item_id: '{"mods":[]}',
            is_identified_fn=lambda _item_id: False,
            send_payload_fn=lambda _email, _event_id, _payload: False,
            build_stats_fn=lambda _item_id: "fallback",
            send_stats_fn=lambda _email, _event_id, _stats: False,
        )
        if completed > 0:
            saw_completion += completed
            break
    assert saw_completion == 1
    assert scheduler.pending_count() == 0


@pytest.mark.parametrize(
    "action_code,expected",
    [
        ("id_blue", ["Blue"]),
        ("id_purple", ["Purple"]),
        ("id_gold", ["Gold"]),
        ("id_all", ["White", "Blue", "Green", "Purple", "Gold"]),
    ],
)
def test_run_inventory_action_identify_variants(action_code, expected):
    viewer = _FakeViewer()
    ok = run_inventory_action(viewer, action_code)
    assert ok is True
    assert viewer.identify_calls[-1] == expected
    assert "started" in viewer.status_message


@pytest.mark.parametrize(
    "action_code,expected",
    [
        ("salvage_white", ["White"]),
        ("salvage_blue", ["Blue"]),
        ("salvage_purple", ["Purple"]),
        ("salvage_gold", ["Gold"]),
    ],
)
def test_run_inventory_action_salvage_variants(action_code, expected):
    viewer = _FakeViewer()
    ok = run_inventory_action(viewer, action_code)
    assert ok is True
    assert viewer.salvage_calls[-1] == expected
    assert "started" in viewer.status_message


def test_run_inventory_action_id_selected_uses_selected_rarities():
    viewer = _FakeViewer()
    ok = run_inventory_action(viewer, "id_selected")
    assert ok is True
    assert viewer.identify_calls == [["Blue", "Purple"]]
    assert "started" in viewer.status_message


def test_run_inventory_action_id_selected_uses_payload_when_given():
    viewer = _FakeViewer()
    ok = run_inventory_action(viewer, "id_selected", "Blue,Gold")
    assert ok is True
    assert viewer.identify_calls[-1] == ["Blue", "Gold"]


def test_run_inventory_action_salvage_selected_uses_selected_rarities():
    viewer = _FakeViewer()
    ok = run_inventory_action(viewer, "salvage_selected")
    assert ok is True
    assert viewer.salvage_calls == [["Gold"]]


def test_run_inventory_action_salvage_selected_uses_payload_when_given():
    viewer = _FakeViewer()
    ok = run_inventory_action(viewer, "salvage_selected", "White,Gold")
    assert ok is True
    assert viewer.salvage_calls[-1] == ["White", "Gold"]


def test_run_inventory_action_push_item_stats_fallback_to_text_send():
    viewer = _FakeViewer()
    ok = run_inventory_action(
        viewer,
        action_code="push_item_stats",
        action_payload="42",
        action_meta="ev-1",
        reply_email="leader@test",
    )
    assert ok is True
    assert "Push Item Stats" in viewer.status_message


def test_run_inventory_action_push_item_stats_invalid_args_return_false():
    viewer = _FakeViewer()
    ok = run_inventory_action(
        viewer,
        action_code="push_item_stats",
        action_payload="0",
        action_meta="",
        reply_email="",
    )
    assert ok is False


def test_run_inventory_action_push_item_stats_returns_false_when_no_stats_or_send_fails():
    viewer = _FakeViewer()
    viewer.stats_text = ""
    ok = run_inventory_action(
        viewer,
        action_code="push_item_stats",
        action_payload="42",
        action_meta="ev-2",
        reply_email="leader@test",
    )
    assert ok is False

    viewer.stats_text = "fallback"
    viewer.stats_send_ok = False
    ok = run_inventory_action(
        viewer,
        action_code="push_item_stats",
        action_payload="42",
        action_meta="ev-2",
        reply_email="leader@test",
    )
    assert ok is False


def test_run_inventory_action_push_item_stats_name_failure_paths():
    viewer = _FakeViewer()
    assert run_inventory_action(viewer, "push_item_stats_name", "", "ev-1", "leader@test") is False
    assert run_inventory_action(viewer, "push_item_stats_name", "Holy Staff", "ev-1", "leader@test") is False

    viewer.resolved_item_id = 99
    viewer.stats_text = ""
    assert run_inventory_action(viewer, "push_item_stats_name", "Holy Staff", "ev-1", "leader@test") is False

    viewer.stats_text = "fallback"
    viewer.stats_send_ok = False
    assert run_inventory_action(viewer, "push_item_stats_name", "Holy Staff", "ev-1", "leader@test") is False


def test_run_inventory_action_push_item_stats_name_success():
    viewer = _FakeViewer()
    viewer.resolved_item_id = 77
    ok = run_inventory_action(viewer, "push_item_stats_name", "Holy Staff", "ev-3", "leader@test")
    assert ok is True
    assert "Push Item Stats By Name" in viewer.status_message


def test_run_inventory_action_push_item_stats_sig_success():
    viewer = _FakeViewer()
    viewer.resolved_item_id_by_sig = 88
    ok = run_inventory_action(viewer, "push_item_stats_sig", "deadbeef|Gold", "ev-sig", "leader@test")
    assert ok is True
    assert "Push Item Stats By Signature" in viewer.status_message


def test_run_inventory_action_id_item_id_invalid_item_id(monkeypatch):
    _install_fake_py4gw(monkeypatch, kit_id=1, identified=False, identify_result=True)
    viewer = _FakeViewer()
    ok = run_inventory_action(
        viewer,
        action_code="id_item_id",
        action_payload="0",
        action_meta="ev-4",
        reply_email="leader@test",
    )
    assert ok is False
    assert "invalid item_id" in viewer.status_message


def test_run_inventory_action_id_item_id_no_kit(monkeypatch):
    _install_fake_py4gw(monkeypatch, kit_id=0, identified=False, identify_result=True)
    viewer = _FakeViewer()
    ok = run_inventory_action(
        viewer,
        action_code="id_item_id",
        action_payload="42",
        action_meta="ev-5",
        reply_email="leader@test",
    )
    assert ok is False
    assert "no ID kit" in viewer.status_message


def test_run_inventory_action_id_item_id_handles_kit_lookup_exception(monkeypatch):
    _install_fake_py4gw(monkeypatch, kit_id=1, identified=False, identify_result=True, kit_raises=True)
    viewer = _FakeViewer()
    ok = run_inventory_action(
        viewer,
        action_code="id_item_id",
        action_payload="42",
        action_meta="ev-5b",
        reply_email="leader@test",
    )
    assert ok is False
    assert "no ID kit" in viewer.status_message


def test_run_inventory_action_id_item_id_already_identified(monkeypatch):
    _install_fake_py4gw(monkeypatch, kit_id=1, identified=True, identify_result=True)
    viewer = _FakeViewer()
    ok = run_inventory_action(
        viewer,
        action_code="id_item_id",
        action_payload="42",
        action_meta="ev-6",
        reply_email="leader@test",
    )
    assert ok is False
    assert "no matching items" in viewer.status_message


def test_run_inventory_action_id_item_id_api_reject(monkeypatch):
    _install_fake_py4gw(monkeypatch, kit_id=1, identified=False, identify_result=False)
    viewer = _FakeViewer()
    ok = run_inventory_action(
        viewer,
        action_code="id_item_id",
        action_payload="42",
        action_meta="ev-7",
        reply_email="leader@test",
    )
    assert ok is False
    assert "API rejected request" in viewer.status_message


def test_run_inventory_action_id_item_id_api_exception(monkeypatch):
    _install_fake_py4gw(monkeypatch, kit_id=1, identified=False, identify_result=True, identify_raises=True)
    viewer = _FakeViewer()
    ok = run_inventory_action(
        viewer,
        action_code="id_item_id",
        action_payload="42",
        action_meta="ev-8",
        reply_email="leader@test",
    )
    assert ok is False
    assert "Identify failed:" in viewer.status_message


def test_run_inventory_action_id_item_id_success_schedules_response(monkeypatch):
    _install_fake_py4gw(monkeypatch, kit_id=1, identified=False, identify_result=True)
    viewer = _FakeViewer()
    ok = run_inventory_action(
        viewer,
        action_code="id_item_id",
        action_payload="42",
        action_meta="ev-9",
        reply_email="leader@test",
    )
    assert ok is True
    assert viewer.identify_response_scheduler.calls == [(42, "leader@test", "ev-9", 2.0)]
    assert "started" in viewer.status_message


def test_run_inventory_action_unknown_returns_false_and_sets_status():
    viewer = _FakeViewer()
    ok = run_inventory_action(viewer, "unknown_action")
    assert ok is False
    assert "Unknown inventory action" in viewer.status_message


def test_run_inventory_action_cfg_auto_id_applies_enabled_and_rarities():
    viewer = _FakeViewer()
    ok = run_inventory_action(viewer, "cfg_auto_id", "1:18")
    assert ok is True
    assert viewer.auto_id_enabled is True
    assert viewer.selected_id_rarities == ["Blue", "Gold"]
    assert "Auto ID Config" in viewer.status_message


def test_run_inventory_action_cfg_auto_salvage_applies_enabled_and_rarities():
    viewer = _FakeViewer()
    ok = run_inventory_action(viewer, "cfg_auto_salvage", "0:9")
    assert ok is True
    assert viewer.auto_salvage_enabled is False
    assert viewer.selected_salvage_rarities == ["White", "Purple"]
    assert "Auto Salvage Config" in viewer.status_message


def test_run_inventory_action_push_item_stats_prefers_payload_send():
    viewer = _FakeViewer()
    viewer.payload_text = '{"mods":[]}'
    viewer.payload_send_ok = True
    ok = run_inventory_action(
        viewer,
        action_code="push_item_stats",
        action_payload="42",
        action_meta="ev-payload",
        reply_email="leader@test",
    )
    assert ok is True
    assert viewer._stats_calls == []


def test_run_inventory_action_push_item_stats_name_prefers_payload_send():
    viewer = _FakeViewer()
    viewer.resolved_item_id = 77
    viewer.payload_text = '{"mods":[]}'
    viewer.payload_send_ok = True
    ok = run_inventory_action(
        viewer,
        action_code="push_item_stats_name",
        action_payload="Holy Staff",
        action_meta="ev-name-payload",
        reply_email="leader@test",
    )
    assert ok is True
    assert viewer._stats_calls == []


def test_run_inventory_action_push_item_stats_sig_invalid_payload_and_missing_item():
    viewer = _FakeViewer()
    assert run_inventory_action(viewer, "push_item_stats_sig", "deadbeef", "ev-a", "") is False
    assert run_inventory_action(viewer, "push_item_stats_sig", "|", "ev-b", "leader@test") is False

    viewer.resolved_item_id_by_sig = 0
    assert run_inventory_action(viewer, "push_item_stats_sig", "deadbeef", "ev-c", "leader@test") is False


def test_run_inventory_action_push_item_stats_sig_prefers_payload_send():
    viewer = _FakeViewer()
    viewer.resolved_item_id_by_sig = 88
    viewer.payload_text = '{"mods":[]}'
    viewer.payload_send_ok = True
    ok = run_inventory_action(
        viewer,
        action_code="push_item_stats_sig",
        action_payload="deadbeef",
        action_meta="ev-sig-payload",
        reply_email="leader@test",
    )
    assert ok is True
    assert viewer._stats_calls == []


def test_run_inventory_action_push_item_stats_sig_fallback_failures():
    viewer = _FakeViewer()
    viewer.resolved_item_id_by_sig = 88
    viewer.payload_text = '{"mods":[]}'
    viewer.payload_send_ok = False
    viewer.stats_text = ""
    assert run_inventory_action(viewer, "push_item_stats_sig", "deadbeef", "ev-sig-fail-a", "leader@test") is False

    viewer.stats_text = "fallback"
    viewer.stats_send_ok = False
    assert run_inventory_action(viewer, "push_item_stats_sig", "deadbeef", "ev-sig-fail-b", "leader@test") is False
