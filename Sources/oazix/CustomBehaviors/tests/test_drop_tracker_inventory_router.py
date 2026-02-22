from __future__ import annotations

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_actions import run_inventory_action


class _FakeViewer:
    def __init__(self) -> None:
        self.status_message = ""
        self.identify_calls = []
        self.salvage_calls = []

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
        return ["Blue", "Purple"]

    def _get_selected_salvage_rarities(self):
        return ["Gold"]

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return int(default)

    def _build_item_snapshot_payload_from_live_item(self, item_id, item_name=""):
        return ""

    def _send_tracker_stats_payload_chunks_to_email(self, receiver_email, event_id, payload_text):
        return False

    def _build_item_stats_from_live_item(self, item_id, item_name=""):
        return "Stats Line"

    def _send_tracker_stats_chunks_to_email(self, receiver_email, event_id, stats_text):
        return True

    def _clean_item_name(self, name):
        return self._ensure_text(name).strip()

    def _resolve_live_item_id_by_name(self, item_name, prefer_identified=False):
        return 0



def test_run_inventory_action_id_selected_uses_selected_rarities():
    viewer = _FakeViewer()
    ok = run_inventory_action(viewer, "id_selected")
    assert ok is True
    assert viewer.identify_calls == [["Blue", "Purple"]]
    assert "started" in viewer.status_message


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


def test_run_inventory_action_unknown_returns_false_and_sets_status():
    viewer = _FakeViewer()
    ok = run_inventory_action(viewer, "unknown_action")
    assert ok is False
    assert "Unknown inventory action" in viewer.status_message
