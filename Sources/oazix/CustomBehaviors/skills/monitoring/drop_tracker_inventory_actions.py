from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from typing import Callable


@dataclass(slots=True)
class PendingIdentifyResponse:
    item_id: int
    reply_email: str
    event_id: str
    requested_at: float
    deadline_at: float
    next_poll_at: float
    poll_interval_s: float = 0.15


class IdentifyResponseScheduler:
    def __init__(self) -> None:
        self._pending: dict[str, PendingIdentifyResponse] = {}

    @staticmethod
    def _key(reply_email: str, event_id: str, item_id: int) -> str:
        return f"{reply_email}:{event_id}:{int(item_id)}"

    def schedule(self, item_id: int, reply_email: str, event_id: str, timeout_s: float = 2.0) -> None:
        now_ts = time.time()
        key = self._key(reply_email, event_id, item_id)
        self._pending[key] = PendingIdentifyResponse(
            item_id=max(0, int(item_id)),
            reply_email=str(reply_email or "").strip(),
            event_id=str(event_id or "").strip(),
            requested_at=now_ts,
            deadline_at=now_ts + max(0.2, float(timeout_s)),
            next_poll_at=now_ts,
        )

    def pending_count(self) -> int:
        return len(self._pending)

    def clear(self) -> None:
        self._pending = {}

    def tick(
        self,
        build_payload_fn: Callable[[int], str],
        is_identified_fn: Callable[[int], bool],
        send_payload_fn: Callable[[str, str, str], bool],
        build_stats_fn: Callable[[int], str],
        send_stats_fn: Callable[[str, str, str], bool],
    ) -> int:
        now_ts = time.time()
        completed: list[str] = []

        for key, pending in list(self._pending.items()):
            if now_ts < float(pending.next_poll_at):
                continue

            payload_text = str(build_payload_fn(pending.item_id) or "").strip()
            identified = bool(is_identified_fn(pending.item_id))
            timed_out = now_ts >= float(pending.deadline_at)

            sent = False
            if payload_text and (identified or timed_out):
                sent = bool(send_payload_fn(pending.reply_email, pending.event_id, payload_text))

            if not sent and timed_out:
                stats_text = str(build_stats_fn(pending.item_id) or "").strip()
                if stats_text:
                    sent = bool(send_stats_fn(pending.reply_email, pending.event_id, stats_text))

            if sent or timed_out:
                completed.append(key)
                continue

            pending.next_poll_at = now_ts + max(0.05, float(pending.poll_interval_s))

        for key in completed:
            self._pending.pop(key, None)
        return len(completed)


def run_inventory_action(viewer: Any, action_code: str, action_payload: str = "", action_meta: str = "", reply_email: str = "") -> bool:
    """Behavior-preserving inventory action router extracted from DropViewerWindow."""
    action_code = viewer._ensure_text(action_code).strip().lower()
    action_label = action_code
    queued = 0

    if action_code == "id_blue":
        action_label = "ID Blue Items"
        queued = viewer._queue_identify_for_rarities(["Blue"])
    elif action_code == "id_purple":
        action_label = "ID Purple Items"
        queued = viewer._queue_identify_for_rarities(["Purple"])
    elif action_code == "id_gold":
        action_label = "ID Gold Items"
        queued = viewer._queue_identify_for_rarities(["Gold"])
    elif action_code == "id_all":
        action_label = "ID All Items"
        queued = viewer._queue_identify_for_rarities(["White", "Blue", "Green", "Purple", "Gold"])
    elif action_code == "id_selected":
        selected = viewer._decode_rarities(action_payload) if action_payload else viewer._get_selected_id_rarities()
        action_label = "ID Selected Rarities"
        queued = viewer._queue_identify_for_rarities(selected)
    elif action_code == "salvage_white":
        action_label = "Salvage White Items"
        queued = viewer._queue_salvage_for_rarities(["White"])
    elif action_code == "salvage_blue":
        action_label = "Salvage Blue Items"
        queued = viewer._queue_salvage_for_rarities(["Blue"])
    elif action_code == "salvage_purple":
        action_label = "Salvage Purple Items"
        queued = viewer._queue_salvage_for_rarities(["Purple"])
    elif action_code == "salvage_gold":
        action_label = "Salvage Gold Items"
        queued = viewer._queue_salvage_for_rarities(["Gold"])
    elif action_code == "salvage_selected":
        selected = viewer._decode_rarities(action_payload) if action_payload else viewer._get_selected_salvage_rarities()
        action_label = "Salvage Selected Rarities"
        queued = viewer._queue_salvage_for_rarities(selected)
    elif action_code == "id_item_id":
        action_label = "Identify Single Item"
        from Py4GWCoreLib import GLOBAL_CACHE
        from Py4GWCoreLib.Item import Item

        target_item_id = max(0, viewer._safe_int(action_payload, 0))
        if target_item_id <= 0:
            viewer.set_status("Identify failed: invalid item_id")
            return False
        kit_id = 0
        try:
            kit_id = int(GLOBAL_CACHE.Inventory.GetFirstIDKit())
        except (TypeError, ValueError, RuntimeError, AttributeError):
            kit_id = 0
        if kit_id <= 0:
            viewer.set_status("Identify failed: no ID kit found")
            return False
        try:
            if Item.Usage.IsIdentified(target_item_id):
                viewer.set_status("Item already identified")
                queued = 0
            else:
                result = GLOBAL_CACHE.Inventory.IdentifyItem(target_item_id, kit_id)
                if result is False:
                    viewer.set_status("Identify failed: API rejected request")
                    return False
                queued = 1
        except (TypeError, ValueError, RuntimeError, AttributeError) as e:
            viewer.set_status(f"Identify failed: {e}")
            return False
        if queued > 0:
            event_id = viewer._ensure_text(action_meta).strip()
            if reply_email and event_id:
                viewer.identify_response_scheduler.schedule(
                    target_item_id,
                    reply_email,
                    event_id,
                    timeout_s=2.0,
                )
    elif action_code == "push_item_stats":
        action_label = "Push Item Stats"
        target_item_id = max(0, viewer._safe_int(action_payload, 0))
        event_id = viewer._ensure_text(action_meta).strip()
        if target_item_id <= 0 or not event_id or not reply_email:
            return False
        payload_text = viewer._build_item_snapshot_payload_from_live_item(target_item_id, "")
        if payload_text and viewer._send_tracker_stats_payload_chunks_to_email(reply_email, event_id, payload_text):
            queued = 1
        else:
            stats_text = viewer._build_item_stats_from_live_item(target_item_id, "")
            if not stats_text:
                return False
            if viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, stats_text):
                queued = 1
            else:
                return False
    elif action_code == "push_item_stats_name":
        action_label = "Push Item Stats By Name"
        target_name = viewer._clean_item_name(action_payload)
        event_id = viewer._ensure_text(action_meta).strip()
        if not target_name or not event_id or not reply_email:
            return False
        target_item_id = viewer._resolve_live_item_id_by_name(target_name, prefer_identified=True)
        if target_item_id <= 0:
            return False
        payload_text = viewer._build_item_snapshot_payload_from_live_item(target_item_id, target_name)
        if payload_text and viewer._send_tracker_stats_payload_chunks_to_email(reply_email, event_id, payload_text):
            queued = 1
        else:
            stats_text = viewer._build_item_stats_from_live_item(target_item_id, target_name)
            if not stats_text:
                return False
            if viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, stats_text):
                queued = 1
            else:
                return False
    else:
        viewer.set_status(f"Unknown inventory action: {action_code}")
        return False

    if queued > 0:
        viewer.set_status(f"{action_label}: started ({queued} items queued)")
        return True
    viewer.set_status(f"{action_label}: no matching items")
    return False
