from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
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
    timeout_retry_count: int = 0
    max_timeout_retries: int = 4


class InventoryActionStatus(str, Enum):
    FINISHED = "finished"
    DEFERRED = "deferred"
    FAILED = "failed"


@dataclass(slots=True)
class InventoryActionResult:
    status: InventoryActionStatus

    @property
    def is_finished(self) -> bool:
        return self.status == InventoryActionStatus.FINISHED

    @property
    def is_deferred(self) -> bool:
        return self.status == InventoryActionStatus.DEFERRED

    @property
    def is_failed(self) -> bool:
        return self.status == InventoryActionStatus.FAILED


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
        payload_ready_fn: Callable[[str, int, bool, bool], bool] | None = None,
    ) -> int:
        now_ts = time.time()
        completed: list[str] = []

        for key, pending in list(self._pending.items()):
            if now_ts < float(pending.next_poll_at):
                continue

            payload_text = str(build_payload_fn(pending.item_id) or "").strip()
            identified = bool(is_identified_fn(pending.item_id))
            timed_out = now_ts >= float(pending.deadline_at)
            payload_ready = True
            if payload_text and payload_ready_fn is not None:
                try:
                    payload_ready = bool(payload_ready_fn(payload_text, int(pending.item_id), identified, timed_out))
                except (TypeError, ValueError, RuntimeError, AttributeError):
                    payload_ready = True

            sent = False
            if identified and (not timed_out) and payload_text and (not payload_ready):
                pending.next_poll_at = now_ts + max(0.05, float(pending.poll_interval_s))
                continue
            if payload_text and (identified or timed_out):
                sent = bool(send_payload_fn(pending.reply_email, pending.event_id, payload_text))

            if not sent and timed_out:
                stats_text = str(build_stats_fn(pending.item_id) or "").strip()
                if stats_text:
                    sent = bool(send_stats_fn(pending.reply_email, pending.event_id, stats_text))

            if sent:
                completed.append(key)
                continue
            if timed_out:
                pending.timeout_retry_count = int(pending.timeout_retry_count) + 1
                if int(pending.timeout_retry_count) >= int(pending.max_timeout_retries):
                    completed.append(key)
                    continue
                pending.next_poll_at = now_ts + max(0.25, float(pending.poll_interval_s))
                continue

            pending.next_poll_at = now_ts + max(0.05, float(pending.poll_interval_s))

        for key in completed:
            self._pending.pop(key, None)
        return len(completed)


def run_inventory_action(
    viewer: Any,
    action_code: str,
    action_payload: str = "",
    action_meta: str = "",
    reply_email: str = "",
    deferred_out: dict[str, bool] | None = None,
) -> bool:
    """Behavior-preserving inventory action router extracted from DropViewerWindow."""
    action_code = viewer._ensure_text(action_code).strip().lower()
    action_label = action_code
    queued = 0
    strict_event_binding = bool(getattr(viewer, "strict_event_stats_binding", False))
    drop_sender_cache: Any = None
    if isinstance(deferred_out, dict):
        deferred_out["deferred"] = False

    def _defer_action() -> bool:
        if isinstance(deferred_out, dict):
            deferred_out["deferred"] = True
        return False

    def _get_drop_tracker_sender():
        nonlocal drop_sender_cache
        if drop_sender_cache is False:
            return None
        if drop_sender_cache is not None:
            return drop_sender_cache
        try:
            from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_utility import DropTrackerSender

            drop_sender_cache = DropTrackerSender()
            return drop_sender_cache
        except (TypeError, ValueError, RuntimeError, AttributeError, ImportError, ModuleNotFoundError):
            drop_sender_cache = False
            return None

    def _resolve_event_item_id_with_grace(event_id_text: str, target_item_id: int = 0) -> tuple[int, bool, bool]:
        event_key = viewer._ensure_text(event_id_text).strip()
        fallback_item_id = max(0, int(target_item_id or 0))
        sender = _get_drop_tracker_sender()
        if sender is None or not event_key:
            return fallback_item_id, False, False

        try:
            identity = sender.get_cached_event_identity(event_key)
        except (TypeError, ValueError, RuntimeError, AttributeError):
            identity = {}
        has_identity = bool(identity)
        if not has_identity:
            return fallback_item_id, False, False

        try:
            resolved_item_id = max(0, int(sender.resolve_live_item_id_for_event(event_key, fallback_item_id)))
        except (TypeError, ValueError, RuntimeError, AttributeError):
            resolved_item_id = 0
        if resolved_item_id > 0:
            try:
                pending = getattr(viewer, "_event_identity_pending_deadline", None)
                if isinstance(pending, dict):
                    pending.pop(event_key, None)
            except (TypeError, ValueError, RuntimeError, AttributeError):
                pass
            return resolved_item_id, True, False

        # Non-blocking grace: keep retrying across future action ticks instead of sleeping.
        grace_s = max(0.0, float(getattr(viewer, "event_identity_resolve_grace_s", 1.2)))
        if grace_s <= 0.0:
            return 0, True, False
        now_ts = time.time()
        pending_deadline = getattr(viewer, "_event_identity_pending_deadline", None)
        if not isinstance(pending_deadline, dict):
            pending_deadline = {}
            try:
                setattr(viewer, "_event_identity_pending_deadline", pending_deadline)
            except (TypeError, ValueError, RuntimeError, AttributeError):
                pending_deadline = {}
        try:
            stale_cutoff = now_ts - 15.0
            for key in list(pending_deadline.keys()):
                try:
                    if float(pending_deadline.get(key, 0.0)) < stale_cutoff:
                        pending_deadline.pop(key, None)
                except (TypeError, ValueError, RuntimeError, AttributeError):
                    pending_deadline.pop(key, None)
        except (TypeError, ValueError, RuntimeError, AttributeError):
            pending_deadline = {}
        existing_deadline = float(pending_deadline.get(event_key, 0.0) or 0.0)
        if existing_deadline <= 0.0:
            pending_deadline[event_key] = now_ts + grace_s
            return 0, True, True
        if now_ts < existing_deadline:
            return 0, True, True
        pending_deadline.pop(event_key, None)
        return 0, True, False

    def _get_event_identity(event_id_text: str) -> dict:
        event_key = viewer._ensure_text(event_id_text).strip()
        if not event_key:
            return {}
        sender = _get_drop_tracker_sender()
        if sender is None:
            return {}
        try:
            identity = sender.get_cached_event_identity(event_key)
        except (TypeError, ValueError, RuntimeError, AttributeError):
            identity = {}
        return dict(identity) if isinstance(identity, dict) else {}

    def _get_cached_event_stats(event_id_text: str, target_item_id: int = 0) -> str:
        event_key = viewer._ensure_text(event_id_text).strip()
        if not event_key:
            return ""
        sender = _get_drop_tracker_sender()
        if sender is None:
            return ""
        try:
            strict_item_id = max(0, int(target_item_id or 0))
            cached = sender.get_cached_event_stats_text(event_key, strict_item_id, 0)
            if not cached and strict_item_id > 0:
                # Item IDs can drift after sorting/identify actions; event_id is the
                # stable identity for this request path.
                cached = sender.get_cached_event_stats_text(event_key, 0, 0)
            return viewer._ensure_text(cached).strip()
        except (TypeError, ValueError, RuntimeError, AttributeError):
            return ""

    if action_code == "cfg_auto_id":
        action_label = "Auto ID Config"
        viewer._apply_auto_id_config_payload(action_payload)
        current_rarities = viewer._get_selected_id_rarities()
        viewer.set_status(
            f"{action_label}: {'ON' if viewer.auto_id_enabled else 'OFF'} "
            f"({','.join(current_rarities) if current_rarities else 'None'})"
        )
        return True
    elif action_code == "cfg_auto_salvage":
        action_label = "Auto Salvage Config"
        viewer._apply_auto_salvage_config_payload(action_payload)
        current_rarities = viewer._get_selected_salvage_rarities()
        viewer.set_status(
            f"{action_label}: {'ON' if viewer.auto_salvage_enabled else 'OFF'} "
            f"({','.join(current_rarities) if current_rarities else 'None'})"
        )
        return True
    elif action_code == "cfg_auto_outpost_store":
        action_label = "Outpost Store Config"
        viewer._apply_auto_outpost_store_config_payload(action_payload)
        viewer.set_status(
            f"{action_label}: {'ON' if viewer.auto_outpost_store_enabled else 'OFF'} "
            f"(materials+tomes)"
        )
        return True
    elif action_code == "cfg_auto_buy_kits":
        action_label = "Auto Buy Kits Config"
        viewer._apply_auto_buy_kits_config_payload(action_payload)
        viewer.set_status(
            f"{action_label}: {'ON' if viewer.auto_buy_kits_enabled else 'OFF'} "
            f"(outpost auto-check)"
        )
        return True
    elif action_code == "cfg_auto_buy_kits_sort":
        action_label = "Auto Kit Sort Config"
        viewer._apply_auto_buy_kits_sort_config_payload(action_payload)
        viewer.set_status(
            f"{action_label}: {'ON' if viewer.auto_buy_kits_sort_to_front_enabled else 'OFF'} "
            f"(outpost-entry reorder)"
        )
        return True
    elif action_code == "cfg_auto_gold_balance":
        action_label = "Auto Gold Balance Config"
        viewer._apply_auto_gold_balance_config_payload(action_payload)
        viewer.set_status(
            f"{action_label}: {'ON' if viewer.auto_gold_balance_enabled else 'OFF'} "
            f"(once per outpost entry)"
        )
        return True
    elif action_code == "sell_gold_no_runes":
        return bool(viewer._queue_manual_sell_gold_items())
    elif action_code == "buy_kits_if_needed":
        return bool(viewer._queue_buy_kits_if_needed())
    elif action_code == "id_blue":
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
            try:
                viewer._remember_identify_mod_capture_candidates([target_item_id])
            except (TypeError, ValueError, RuntimeError, AttributeError):
                pass
            event_id = viewer._ensure_text(action_meta).strip()
            if event_id:
                try:
                    sender = _get_drop_tracker_sender()
                    if sender is not None:
                        sender.clear_cached_event_stats(event_id, target_item_id)
                except (TypeError, ValueError, RuntimeError, AttributeError):
                    pass
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
        resolved_item_id, has_event_identity, waiting_for_identity = _resolve_event_item_id_with_grace(event_id, target_item_id)
        if resolved_item_id <= 0 and has_event_identity:
            if waiting_for_identity:
                return _defer_action()
            cached_stats = _get_cached_event_stats(event_id, target_item_id)
            if cached_stats and viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, cached_stats):
                queued = 1
                viewer.set_status(f"{action_label}: started ({queued} items queued)")
                return True
            else:
                return False
        if resolved_item_id > 0:
            target_item_id = int(resolved_item_id)
        prefer_fresh_payload = False
        try:
            from Py4GWCoreLib.Item import Item

            prefer_fresh_payload = bool(Item.Usage.IsIdentified(target_item_id))
        except (TypeError, ValueError, RuntimeError, AttributeError, ImportError, ModuleNotFoundError):
            prefer_fresh_payload = False
        if prefer_fresh_payload:
            payload_text = viewer._build_item_snapshot_payload_from_live_item(target_item_id, "")
            if payload_text and viewer._send_tracker_stats_payload_chunks_to_email(reply_email, event_id, payload_text):
                queued = 1
            else:
                cached_stats = _get_cached_event_stats(event_id, target_item_id)
                if cached_stats and viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, cached_stats):
                    queued = 1
                else:
                    stats_text = viewer._build_item_stats_from_live_item(target_item_id, "")
                    if not stats_text:
                        return False
                    if viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, stats_text):
                        queued = 1
                    else:
                        return False
        else:
            cached_stats = _get_cached_event_stats(event_id, target_item_id)
            if cached_stats and viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, cached_stats):
                queued = 1
            else:
                payload_text = viewer._build_item_snapshot_payload_from_live_item(target_item_id, "")
                if payload_text and viewer._send_tracker_stats_payload_chunks_to_email(reply_email, event_id, payload_text):
                    queued = 1
                else:
                    if not cached_stats:
                        cached_stats = _get_cached_event_stats(event_id, target_item_id)
                    if cached_stats and viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, cached_stats):
                        queued = 1
                    else:
                        stats_text = viewer._build_item_stats_from_live_item(target_item_id, "")
                        if not stats_text:
                            return False
                        if viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, stats_text):
                            queued = 1
                        else:
                            return False
    elif action_code == "push_item_stats_event":
        action_label = "Push Item Stats By Event"
        target_item_id = max(0, viewer._safe_int(action_payload, 0))
        event_id = viewer._ensure_text(action_meta).strip()
        if not event_id or not reply_email:
            return False
        cached_stats = _get_cached_event_stats(event_id, target_item_id)
        if cached_stats and viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, cached_stats):
            queued = 1
        else:
            resolved_item_id, has_event_identity, waiting_for_identity = _resolve_event_item_id_with_grace(event_id, target_item_id)
            if resolved_item_id > 0:
                payload_text = viewer._build_item_snapshot_payload_from_live_item(resolved_item_id, "")
                if payload_text and viewer._send_tracker_stats_payload_chunks_to_email(reply_email, event_id, payload_text):
                    queued = 1
                else:
                    stats_text = viewer._build_item_stats_from_live_item(resolved_item_id, "")
                    if not stats_text:
                        return False
                    if viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, stats_text):
                        queued = 1
                    else:
                        return False
            elif has_event_identity:
                if waiting_for_identity:
                    return _defer_action()
                return False
            else:
                return False
    elif action_code == "push_item_stats_name":
        action_label = "Push Item Stats By Name"
        target_name = viewer._clean_item_name(action_payload)
        event_id = viewer._ensure_text(action_meta).strip()
        if not target_name or not event_id or not reply_email:
            return False
        cached_stats = _get_cached_event_stats(event_id, 0)
        if cached_stats and viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, cached_stats):
            queued = 1
        else:
            identity = _get_event_identity(event_id)
            if identity:
                resolved_item_id, _, waiting_for_identity = _resolve_event_item_id_with_grace(event_id, 0)
                if resolved_item_id <= 0:
                    if waiting_for_identity:
                        return _defer_action()
                    return False
                payload_text = viewer._build_item_snapshot_payload_from_live_item(resolved_item_id, "")
                if payload_text and viewer._send_tracker_stats_payload_chunks_to_email(reply_email, event_id, payload_text):
                    queued = 1
                else:
                    stats_text = viewer._build_item_stats_from_live_item(resolved_item_id, "")
                    if not stats_text:
                        return False
                    if viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, stats_text):
                        queued = 1
                    else:
                        return False
            else:
                if strict_event_binding:
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
    elif action_code == "push_item_stats_sig":
        action_label = "Push Item Stats By Signature"
        sig_payload = viewer._ensure_text(action_payload).strip()
        event_id = viewer._ensure_text(action_meta).strip()
        if not sig_payload or not event_id or not reply_email:
            return False
        cached_stats = _get_cached_event_stats(event_id, 0)
        if cached_stats and viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, cached_stats):
            queued = 1
        else:
            identity = _get_event_identity(event_id)
            if identity:
                resolved_item_id, _, waiting_for_identity = _resolve_event_item_id_with_grace(event_id, 0)
                if resolved_item_id <= 0:
                    if waiting_for_identity:
                        return _defer_action()
                    return False
                payload_text = viewer._build_item_snapshot_payload_from_live_item(resolved_item_id, "")
                if payload_text and viewer._send_tracker_stats_payload_chunks_to_email(reply_email, event_id, payload_text):
                    queued = 1
                else:
                    stats_text = viewer._build_item_stats_from_live_item(resolved_item_id, "")
                    if not stats_text:
                        return False
                    if viewer._send_tracker_stats_chunks_to_email(reply_email, event_id, stats_text):
                        queued = 1
                    else:
                        return False
            else:
                if strict_event_binding:
                    return False
                if "|" in sig_payload:
                    target_sig, rarity_hint = sig_payload.split("|", 1)
                    target_sig = viewer._ensure_text(target_sig).strip().lower()
                    rarity_hint = viewer._ensure_text(rarity_hint).strip()
                else:
                    target_sig = sig_payload.lower()
                    rarity_hint = ""
                if not target_sig:
                    return False
                target_item_id = viewer._resolve_live_item_id_by_signature(target_sig, rarity_hint, prefer_identified=True)
                if target_item_id <= 0:
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
    else:
        viewer.set_status(f"Unknown inventory action: {action_code}")
        return False

    if queued > 0:
        viewer.set_status(f"{action_label}: started ({queued} items queued)")
        return True
    viewer.set_status(f"{action_label}: no matching items")
    return False


def run_inventory_action_result(
    viewer: Any,
    action_code: str,
    action_payload: str = "",
    action_meta: str = "",
    reply_email: str = "",
) -> InventoryActionResult:
    deferred_state: dict[str, bool] = {"deferred": False}
    completed = bool(
        run_inventory_action(
            viewer,
            action_code,
            action_payload,
            action_meta,
            reply_email,
            deferred_out=deferred_state,
        )
    )
    if completed:
        return InventoryActionResult(status=InventoryActionStatus.FINISHED)
    if bool(deferred_state.get("deferred", False)):
        return InventoryActionResult(status=InventoryActionStatus.DEFERRED)
    return InventoryActionResult(status=InventoryActionStatus.FAILED)
