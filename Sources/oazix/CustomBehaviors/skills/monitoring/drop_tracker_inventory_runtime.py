import datetime
import re
import time
from typing import Any

from Py4GWCoreLib import Item, ItemArray, Py4GW

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_candidate_pipeline import (
    confirm_candidate_events,
    log_candidate_pipeline,
    log_candidate_reset_trace,
)

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _normalize_item_name(sender, raw_name: str, model_id: int) -> str:
    clean_name = sender._strip_tags(raw_name).strip() if raw_name else ""
    clean_name = re.sub(r"^[\d,]+\s+", "", clean_name) if clean_name else ""
    if clean_name:
        return clean_name
    return f"Model#{int(model_id)}"


def _normalize_rarity(item_id: int, clean_name: str, rarity: str) -> str:
    resolved = str(rarity or "Unknown")
    if Item.Type.IsTome(item_id):
        return "Tomes"
    if "Dye" in clean_name or "Vial of Dye" in clean_name:
        return "Dyes"
    if "Key" in clean_name:
        return "Keys"
    if Item.Type.IsMaterial(item_id) or Item.Type.IsRareMaterial(item_id):
        return "Material"
    return resolved


def take_inventory_snapshot(sender) -> dict[tuple[int, int], tuple[str, str, int, int, int]]:
    snapshot: dict[tuple[int, int], tuple[str, str, int, int, int]] = {}
    try:
        bag_ids = (1, 2, 3, 4)
        bags = ItemArray.CreateBagList(*bag_ids)
        item_ids = ItemArray.GetItemArray(bags)
        sender.last_snapshot_total = len(item_ids)
        ready_count = 0
        not_ready_count = 0
        for bag_id in bag_ids:
            bag_items = ItemArray.GetItemArray(ItemArray.CreateBagList(bag_id))
            for item_id in bag_items:
                item_instance = Item.item_instance(item_id)
                if item_instance:
                    slot_id = int(item_instance.slot)
                    model_id = int(item_instance.model_id)
                    rarity = item_instance.rarity.name if getattr(item_instance, "rarity", None) else "Unknown"
                    qty = int(item_instance.quantity) if getattr(item_instance, "quantity", None) is not None else 1
                else:
                    slot_id = int(Item.GetSlot(item_id))
                    model_id = int(Item.GetModelID(item_id))
                    rarity = Item.Rarity.GetRarity(item_id)[1]
                    qty = Item.Properties.GetQuantity(item_id)
                    qty = max(1, int(qty) if qty is not None else 1)

                raw_name = ""
                if Item.IsNameReady(item_id):
                    raw_name = Item.GetName(item_id) or ""
                    ready_count += 1
                else:
                    not_ready_count += 1
                    try:
                        Item.RequestName(item_id)
                    except EXPECTED_RUNTIME_ERRORS:
                        pass

                clean_name = _normalize_item_name(sender, raw_name, model_id)
                rarity = _normalize_rarity(item_id, clean_name, rarity)
                slot_key = (bag_id, int(slot_id))
                existing_entry = snapshot.get(slot_key)
                if (
                    existing_entry is not None
                    and isinstance(existing_entry, tuple)
                    and len(existing_entry) > 4
                    and int(existing_entry[4]) != int(item_id)
                ):
                    synthetic_slot_id = -max(1, abs(int(item_id)))
                    slot_key = (bag_id, synthetic_slot_id)
                    while slot_key in snapshot:
                        synthetic_slot_id -= 1
                        slot_key = (bag_id, synthetic_slot_id)
                snapshot[slot_key] = (clean_name, rarity, qty, model_id, int(item_id))

        sender.last_snapshot_ready = ready_count
        sender.last_snapshot_not_ready = not_ready_count
    except EXPECTED_RUNTIME_ERRORS:
        if sender.snapshot_error_timer.IsExpired():
            sender.snapshot_error_timer.Reset()
            Py4GW.Console.Log(
                "DropTrackerSender",
                "Inventory snapshot failed.",
                Py4GW.Console.MessageType.Warning,
            )
        return snapshot
    return snapshot


def _set_process_duration(sender, start_perf: float) -> None:
    sender.last_process_duration_ms = (time.perf_counter() - start_perf) * 1000.0


def make_orphan_pending_slot_key(_sender, item_id: int, now_ts: float) -> tuple[int, int]:
    if int(item_id) > 0:
        return 0, -abs(int(item_id))
    fallback_seed = int(now_ts * 1000.0) & 0x7FFFFFFF
    return 0, -max(1, fallback_seed)


def buffer_pending_slot_delta(
    sender,
    slot_key: tuple[int, int],
    delta_qty: int,
    model_id: int,
    item_id: int,
    rarity: str,
    now_ts: float,
):
    qty_to_add = max(1, int(delta_qty))
    pending = sender.pending_slot_deltas.get(slot_key)
    if pending is None or not isinstance(pending, dict):
        sender.pending_slot_deltas[slot_key] = {
            "qty": int(qty_to_add),
            "model_id": int(model_id),
            "item_id": int(item_id),
            "rarity": rarity,
            "first_seen": now_ts,
            "last_seen": now_ts,
        }
        return

    pending_item_id = int(pending.get("item_id", 0))
    pending_model_id = int(pending.get("model_id", 0))
    same_item = pending_item_id > 0 and pending_item_id == int(item_id)
    same_model = pending_item_id <= 0 and pending_model_id > 0 and pending_model_id == int(model_id)
    if not (same_item or same_model):
        orphan_key = sender._make_orphan_pending_slot_key(pending_item_id, now_ts)
        orphan_entry = sender.pending_slot_deltas.get(orphan_key)
        if orphan_entry is None or not isinstance(orphan_entry, dict):
            preserved = dict(pending)
            preserved["last_seen"] = now_ts
            sender.pending_slot_deltas[orphan_key] = preserved
        else:
            orphan_entry["qty"] = int(orphan_entry.get("qty", 0)) + int(pending.get("qty", 0))
            orphan_entry["model_id"] = int(pending.get("model_id", orphan_entry.get("model_id", 0)))
            orphan_entry["item_id"] = int(pending.get("item_id", orphan_entry.get("item_id", 0)))
            orphan_entry["rarity"] = orphan_entry.get("rarity") or pending.get("rarity") or rarity
            orphan_entry["first_seen"] = min(
                float(orphan_entry.get("first_seen", now_ts)),
                float(pending.get("first_seen", now_ts)),
            )
            orphan_entry["last_seen"] = now_ts
        sender.pending_slot_deltas[slot_key] = {
            "qty": int(qty_to_add),
            "model_id": int(model_id),
            "item_id": int(item_id),
            "rarity": rarity,
            "first_seen": now_ts,
            "last_seen": now_ts,
        }
        return

    pending["qty"] = int(pending.get("qty", 0)) + int(qty_to_add)
    pending["model_id"] = int(model_id)
    pending["item_id"] = int(item_id)
    pending["rarity"] = pending.get("rarity") or rarity
    pending["last_seen"] = now_ts


def _build_model_qty_map(snapshot: dict[tuple[int, int], tuple[str, str, int, int, int]]) -> dict[int, int]:
    model_qty: dict[int, int] = {}
    for snapshot_entry in snapshot.values():
        if not isinstance(snapshot_entry, tuple) or len(snapshot_entry) < 4:
            continue
        model_id = int(snapshot_entry[3])
        qty = max(1, int(snapshot_entry[2])) if len(snapshot_entry) > 2 else 1
        model_qty[model_id] = int(model_qty.get(model_id, 0)) + int(qty)
    return model_qty


def _build_prev_item_state_by_id(snapshot: dict[tuple[int, int], tuple[str, str, int, int, int]]) -> dict[int, tuple[int, int]]:
    return {
        int(entry[4]): (int(entry[3]), int(entry[2]))
        for entry in snapshot.values()
        if isinstance(entry, tuple) and len(entry) > 4
    }


def _build_carryover_match_entries(
    snapshot: dict[tuple[int, int], tuple[str, str, int, int, int]],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for baseline_entry in snapshot.values():
        if not isinstance(baseline_entry, tuple) or len(baseline_entry) < 4:
            continue
        baseline_name = str(baseline_entry[0] or "").strip()
        baseline_name_key = baseline_name if baseline_name and not baseline_name.startswith("Model#") else ""
        entries.append(
            {
                "model_id": int(baseline_entry[3]),
                "qty": max(1, int(baseline_entry[2])),
                "rarity": str(baseline_entry[1] or "Unknown"),
                "name_key": baseline_name_key,
                "consumed": False,
            }
        )
    return entries


def _build_carryover_snapshot_from_match_entries(
    match_entries: list[dict[str, Any]],
) -> dict[tuple[int, int], tuple[str, str, int, int, int]]:
    snapshot: dict[tuple[int, int], tuple[str, str, int, int, int]] = {}
    synthetic_index = 1
    for entry in list(match_entries or []):
        if not isinstance(entry, dict) or bool(entry.get("consumed", False)):
            continue
        slot_key = (0, -synthetic_index)
        synthetic_index += 1
        model_id = int(entry.get("model_id", 0))
        qty = max(1, int(entry.get("qty", 1)))
        rarity = str(entry.get("rarity", "Unknown") or "Unknown")
        name_key = str(entry.get("name_key", "") or "").strip()
        snapshot[slot_key] = (name_key or f"Model#{model_id}", rarity, qty, model_id, 0)
    return snapshot


def _pool_key_for_item(name_value: str, rarity_value: str, qty_value: int, model_value: int) -> tuple[int, int, str, str]:
    name_key = str(name_value or "").strip()
    if name_key.startswith("Model#"):
        name_key = ""
    return (
        int(model_value),
        max(1, int(qty_value)),
        str(rarity_value or "Unknown"),
        name_key,
    )


def _consume_carryover_identity(
    carryover_match_entries: list[dict[str, Any]],
    name_value: str,
    rarity_value: str,
    qty_value: int,
    model_value: int,
) -> bool:
    preferred_key = _pool_key_for_item(name_value, rarity_value, qty_value, model_value)
    for entry in carryover_match_entries:
        if bool(entry.get("consumed", False)):
            continue
        entry_key = (
            int(entry.get("model_id", 0)),
            max(1, int(entry.get("qty", 1))),
            str(entry.get("rarity", "Unknown") or "Unknown"),
            str(entry.get("name_key", "") or ""),
        )
        if entry_key == preferred_key:
            entry["consumed"] = True
            return True
    fallback_key = preferred_key[:3]
    for entry in carryover_match_entries:
        if bool(entry.get("consumed", False)):
            continue
        entry_key = (
            int(entry.get("model_id", 0)),
            max(1, int(entry.get("qty", 1))),
            str(entry.get("rarity", "Unknown") or "Unknown"),
        )
        entry_name_key = str(entry.get("name_key", "") or "")
        if entry_key == fallback_key and not entry_name_key:
            entry["consumed"] = True
            return True
    return False


def _carryover_same_item(previous_entry: tuple, name_value: str, rarity_value: str, qty_value: int, model_value: int) -> bool:
    previous_name = str(previous_entry[0] or "").strip()
    current_name = str(name_value or "").strip()
    previous_name_ready = bool(previous_name and not previous_name.startswith("Model#"))
    current_name_ready = bool(current_name and not current_name.startswith("Model#"))
    names_compatible = (not previous_name_ready) or (not current_name_ready) or previous_name == current_name
    return (
        int(previous_entry[3]) == int(model_value)
        and max(1, int(previous_entry[2])) == max(1, int(qty_value))
        and str(previous_entry[1] or "Unknown") == str(rarity_value or "Unknown")
        and names_compatible
    )


def _append_candidate_event(
    candidate_events: list[dict[str, Any]],
    changed_itemid_to_ready_name: dict[int, tuple[str, str]],
    changed_model_rarity_to_ready_name: dict[tuple[int, str], str],
    *,
    name: str,
    qty: int,
    rarity: str,
    item_id: int,
    model_id: int,
    slot_key: tuple[int, int],
    reason: str,
) -> None:
    candidate_events.append(
        {
            "name": name,
            "qty": int(qty),
            "rarity": rarity,
            "item_id": int(item_id),
            "model_id": int(model_id),
            "slot_key": slot_key,
            "reason": reason,
        }
    )
    changed_itemid_to_ready_name[int(item_id)] = (name, str(rarity or "Unknown"))
    changed_model_rarity_to_ready_name[(int(model_id), str(rarity or "Unknown"))] = name


def _flush_pending_same_slot_if_ready(
    sender,
    candidate_events: list[dict[str, Any]],
    slot_key: tuple[int, int],
    name: str,
    rarity: str,
    item_id: int,
    model_id: int,
) -> bool:
    pending_entry = sender.pending_slot_deltas.get(slot_key)
    pending_qty = int(pending_entry.get("qty", 0)) if isinstance(pending_entry, dict) else 0
    pending_item_id = int(pending_entry.get("item_id", 0)) if isinstance(pending_entry, dict) else 0
    if pending_qty > 0 and pending_item_id == int(item_id):
        candidate_events.append(
            {
                "name": name,
                "qty": int(pending_qty),
                "rarity": rarity,
                "item_id": int(item_id),
                "model_id": int(model_id),
                "slot_key": slot_key,
                "reason": "pending_same_slot_name_ready",
            }
        )
        sender.pending_slot_deltas.pop(slot_key, None)
        return True
    return False


def _resolve_ready_pending_name(sender, pending_item_id: int, pending_rarity: str) -> tuple[str, str]:
    raw_name = Item.GetName(pending_item_id) or ""
    resolved_name = re.sub(r"^[\d,]+\s+", "", sender._strip_tags(raw_name).strip())
    if not resolved_name:
        return "", pending_rarity
    resolved_rarity = pending_rarity
    if resolved_rarity == "Unknown":
        try:
            item_instance = Item.item_instance(pending_item_id)
            if item_instance and getattr(item_instance, "rarity", None):
                resolved_rarity = item_instance.rarity.name
        except EXPECTED_RUNTIME_ERRORS:
            pass
    resolved_rarity = _normalize_rarity(pending_item_id, resolved_name, resolved_rarity)
    return resolved_name, resolved_rarity


def _resolve_pending_slot_candidates(
    sender,
    candidate_events: list[dict[str, Any]],
    changed_itemid_to_ready_name: dict[int, tuple[str, str]],
    changed_model_rarity_to_ready_name: dict[tuple[int, str], str],
    live_item_ids: set[int],
    live_item_model_by_id: dict[int, int],
    now_ts: float,
) -> None:
    resolved_pending_slots = []
    for pending_slot, pending_entry in sender.pending_slot_deltas.items():
        if not isinstance(pending_entry, dict):
            continue
        pending_qty = int(pending_entry.get("qty", 0))
        if pending_qty <= 0:
            resolved_pending_slots.append(pending_slot)
            continue
        pending_model_id = int(pending_entry.get("model_id", 0))
        pending_item_id = int(pending_entry.get("item_id", 0))
        live_model_for_pending = int(live_item_model_by_id.get(pending_item_id, 0))
        pending_item_is_live = pending_item_id in live_item_ids and (
            pending_model_id <= 0 or live_model_for_pending <= 0 or live_model_for_pending == pending_model_id
        )
        pending_rarity = str(pending_entry.get("rarity") or "Unknown")

        if pending_item_id > 0 and pending_item_is_live:
            try:
                if Item.IsNameReady(pending_item_id):
                    resolved_name, resolved_rarity = _resolve_ready_pending_name(sender, pending_item_id, pending_rarity)
                    if resolved_name:
                        candidate_events.append(
                            {
                                "name": resolved_name,
                                "qty": int(pending_qty),
                                "rarity": resolved_rarity,
                                "item_id": int(pending_item_id),
                                "model_id": int(pending_model_id),
                                "slot_key": pending_slot,
                                "reason": "pending_itemid_name_ready",
                            }
                        )
                        resolved_pending_slots.append(pending_slot)
                        continue
                else:
                    Item.RequestName(pending_item_id)
            except EXPECTED_RUNTIME_ERRORS:
                pass

            by_item_id = changed_itemid_to_ready_name.get(pending_item_id)
            if by_item_id:
                resolved_name, resolved_rarity = by_item_id
                final_rarity = pending_rarity if pending_rarity != "Unknown" else resolved_rarity
                candidate_events.append(
                    {
                        "name": resolved_name,
                        "qty": int(pending_qty),
                        "rarity": final_rarity,
                        "item_id": int(pending_item_id),
                        "model_id": int(pending_model_id),
                        "slot_key": pending_slot,
                        "reason": "pending_changed_slot_lookup",
                    }
                )
                resolved_pending_slots.append(pending_slot)
                continue

        exact_name = changed_model_rarity_to_ready_name.get((pending_model_id, pending_rarity))
        if exact_name:
            candidate_events.append(
                {
                    "name": exact_name,
                    "qty": int(pending_qty),
                    "rarity": pending_rarity,
                    "item_id": int(pending_item_id),
                    "model_id": int(pending_model_id),
                    "slot_key": pending_slot,
                    "reason": "pending_model_rarity_lookup",
                }
            )
            resolved_pending_slots.append(pending_slot)
            continue

        first_seen = float(pending_entry.get("first_seen", now_ts))
        if (now_ts - first_seen) >= sender.pending_ttl_seconds:
            candidate_events.append(
                {
                    "name": "Unknown Item",
                    "qty": int(pending_qty),
                    "rarity": pending_entry.get("rarity") or "Unknown",
                    "item_id": int(pending_item_id),
                    "model_id": int(pending_model_id),
                    "slot_key": pending_slot,
                    "reason": "pending_ttl_fallback",
                }
            )
            resolved_pending_slots.append(pending_slot)

    for pending_slot in resolved_pending_slots:
        sender.pending_slot_deltas.pop(pending_slot, None)


def _expire_stale_pending_slots(
    sender,
    candidate_events: list[dict[str, Any]],
    live_slots: set[tuple[int, int]],
    live_item_ids: set[int],
    live_item_model_by_id: dict[int, int],
    now_ts: float,
) -> None:
    stale_slots = [slot_key for slot_key in sender.pending_slot_deltas.keys() if slot_key not in live_slots]
    for slot_key in stale_slots:
        entry = sender.pending_slot_deltas.get(slot_key)
        if not isinstance(entry, dict):
            sender.pending_slot_deltas.pop(slot_key, None)
            continue
        pending_item_id = int(entry.get("item_id", 0))
        pending_model_id = int(entry.get("model_id", 0))
        live_model_for_pending = int(live_item_model_by_id.get(pending_item_id, 0))
        pending_item_still_live = pending_item_id > 0 and pending_item_id in live_item_ids and (
            pending_model_id <= 0 or live_model_for_pending <= 0 or live_model_for_pending == pending_model_id
        )
        if pending_item_still_live:
            continue
        last_seen = float(entry.get("last_seen", now_ts))
        if (now_ts - last_seen) > sender.pending_ttl_seconds:
            qty = int(entry.get("qty", 0))
            if qty > 0:
                candidate_events.append(
                    {
                        "name": "Unknown Item",
                        "qty": int(qty),
                        "rarity": entry.get("rarity") or "Unknown",
                        "item_id": int(entry.get("item_id", 0)),
                        "model_id": int(entry.get("model_id", 0)),
                        "slot_key": slot_key,
                        "reason": "stale_slot_ttl_fallback",
                    }
                )
            sender.pending_slot_deltas.pop(slot_key, None)


def process_inventory_deltas(sender) -> None:
    start_perf = time.perf_counter()
    current_snapshot = sender._take_inventory_snapshot()
    now_ts = time.time()
    baseline_snapshot = sender.last_inventory_snapshot
    use_carryover_baseline = False
    if sender.session_startup_pending and not baseline_snapshot and sender.carryover_inventory_snapshot:
        baseline_snapshot = sender.carryover_inventory_snapshot
        use_carryover_baseline = True
    carryover_suppression_active = bool(sender.carryover_inventory_snapshot) and (
        bool(sender.session_startup_pending)
        or now_ts < float(getattr(sender, "carryover_suppression_until", 0.0) or 0.0)
    )
    if sender._reset_trace_active():
        sender._log_reset_trace(
            (
                f"RESET TRACE snapshot actor={sender._reset_trace_actor_label()} size={len(current_snapshot)} "
                f"ready={int(sender.last_snapshot_ready)} total={int(sender.last_snapshot_total)} "
                f"pending={len(sender.pending_slot_deltas)} warmed={bool(sender.is_warmed_up)} "
                f"carryover={len(sender.carryover_inventory_snapshot)} startup_pending={bool(sender.session_startup_pending)}"
            ),
            consume_snapshot=True,
        )

    if sender.last_snapshot_total > 0 and sender.last_snapshot_ready == 0:
        if not sender.session_startup_pending:
            sender.pending_slot_deltas = {}
            sender.last_inventory_snapshot = current_snapshot
        sender._log_reset_trace(
            (
                "RESET TRACE snapshot skipped: ready=0 transient inventory state"
                if sender.session_startup_pending
                else "RESET TRACE snapshot resynced: ready=0 transient inventory state"
            ),
            consume_snapshot=True,
        )
        sender.last_sent_count = 0
        _set_process_duration(sender, start_perf)
        return

    if not current_snapshot:
        sender._log_reset_trace("RESET TRACE snapshot skipped: empty snapshot", consume_snapshot=True)
        sender.last_sent_count = 0
        _set_process_duration(sender, start_perf)
        return

    readiness = (float(sender.last_snapshot_ready) / float(sender.last_snapshot_total)) if sender.last_snapshot_total else 0.0
    if sender.session_startup_pending:
        sender.stable_snapshot_count = sender.stable_snapshot_count + 1 if readiness >= 0.7 else 0
        sender._log_reset_trace(
            (
                f"RESET TRACE startup baseline actor={sender._reset_trace_actor_label()} size={len(current_snapshot)} "
                f"readiness={readiness:.2f} stable={int(sender.stable_snapshot_count)} "
                f"carryover={len(baseline_snapshot)}"
            ),
            consume_snapshot=True,
        )
        if sender.stable_snapshot_count < 2:
            sender.last_sent_count = 0
            _set_process_duration(sender, start_perf)
            return
        sender.session_startup_pending = False
        sender.is_warmed_up = True
        sender.stable_snapshot_count = 0
        sender.warmup_grace_until = 0.0

    if not sender.is_warmed_up:
        sender.stable_snapshot_count = sender.stable_snapshot_count + 1 if readiness >= 0.7 else 0
        sender._log_reset_trace(
            (
                f"RESET TRACE warmup baseline actor={sender._reset_trace_actor_label()} size={len(current_snapshot)} "
                f"readiness={readiness:.2f} stable={int(sender.stable_snapshot_count)}"
            ),
            consume_snapshot=True,
        )
        sender.last_inventory_snapshot = current_snapshot
        sender.last_sent_count = 0
        if sender.stable_snapshot_count >= 2:
            sender.is_warmed_up = True
            sender.warmup_grace_until = time.time() + sender.warmup_grace_seconds
        _set_process_duration(sender, start_perf)
        return

    if now_ts < sender.warmup_grace_until:
        sender._log_reset_trace(
            (
                f"RESET TRACE grace active actor={sender._reset_trace_actor_label()} size={len(current_snapshot)} "
                f"until_in={max(0.0, sender.warmup_grace_until - now_ts):.2f}s"
            ),
            consume_snapshot=True,
        )
        sender.last_inventory_snapshot = current_snapshot
        sender.last_sent_count = 0
        _set_process_duration(sender, start_perf)
        return

    snapshot_size_jump = abs(len(current_snapshot) - len(baseline_snapshot))
    max_jump = max(6, int(getattr(sender, "max_snapshot_size_jump", 40)))
    if snapshot_size_jump > max_jump:
        sender.pending_slot_deltas = {}
        sender.last_inventory_snapshot = current_snapshot
        sender.carryover_inventory_snapshot = {}
        sender.last_sent_count = 0
        sender._log_reset_trace(
            (
                f"RESET TRACE churn resync actor={sender._reset_trace_actor_label()} jump={snapshot_size_jump} "
                f"threshold={max_jump} size={len(current_snapshot)}"
            ),
            consume_snapshot=True,
        )
        if sender.debug_pipeline_logs:
            Py4GW.Console.Log(
                "DropTrackerSender",
                f"Snapshot churn guard resync: jump={snapshot_size_jump} threshold={max_jump}",
                Py4GW.Console.MessageType.Info,
            )
        _set_process_duration(sender, start_perf)
        return

    time_str = datetime.datetime.now().strftime("%I:%M %p")
    candidate_events: list[dict[str, Any]] = []
    prev_model_qty = _build_model_qty_map(baseline_snapshot)
    current_model_qty = _build_model_qty_map(current_snapshot)
    prev_item_ids = {int(entry[4]) for entry in baseline_snapshot.values() if isinstance(entry, tuple) and len(entry) > 4}
    prev_item_state_by_id = _build_prev_item_state_by_id(baseline_snapshot)
    carryover_match_entries = (
        _build_carryover_match_entries(sender.carryover_inventory_snapshot)
        if carryover_suppression_active
        else []
    )

    changed_itemid_to_ready_name: dict[int, tuple[str, str]] = {}
    changed_model_rarity_to_ready_name: dict[tuple[int, str], str] = {}
    live_slots: set[tuple[int, int]] = set()
    live_item_ids: set[int] = set()
    live_item_model_by_id: dict[int, int] = {}

    for slot_key, (name, rarity, qty, model_id, item_id) in current_snapshot.items():
        live_slots.add(slot_key)
        live_item_ids.add(int(item_id))
        live_item_model_by_id[int(item_id)] = int(model_id)
        carryover_identity_matched = False
        if carryover_suppression_active:
            carryover_identity_matched = _consume_carryover_identity(
                carryover_match_entries,
                name,
                rarity,
                qty,
                model_id,
            )
        previous = baseline_snapshot.get(slot_key)
        is_unknown_name = name.startswith("Model#")
        changed_this_tick = False
        if previous is None:
            if carryover_identity_matched:
                continue
            if int(item_id) in prev_item_ids:
                prev_state = prev_item_state_by_id.get(int(item_id))
                if prev_state is not None:
                    prev_model_for_item, prev_qty_for_item = prev_state
                    if int(prev_model_for_item) == int(model_id) and int(prev_qty_for_item) == int(qty):
                        continue
            changed_this_tick = True
            if is_unknown_name:
                sender._buffer_pending_slot_delta(
                    slot_key=slot_key,
                    delta_qty=int(qty),
                    model_id=int(model_id),
                    item_id=int(item_id),
                    rarity=str(rarity or "Unknown"),
                    now_ts=time.time(),
                )
            else:
                _append_candidate_event(
                    candidate_events,
                    changed_itemid_to_ready_name,
                    changed_model_rarity_to_ready_name,
                    name=name,
                    qty=int(qty),
                    rarity=rarity,
                    item_id=int(item_id),
                    model_id=int(model_id),
                    slot_key=slot_key,
                    reason="new_slot",
                )
            continue

        prev_qty = int(previous[2])
        prev_model_id = int(previous[3])
        prev_item_id = int(previous[4])

        if int(item_id) != prev_item_id:
            if _carryover_same_item(previous, name, rarity, qty, model_id):
                continue
            if carryover_identity_matched and _carryover_same_item(previous, name, rarity, qty, model_id):
                continue
            if (
                use_carryover_baseline
                and int(prev_model_id) == int(model_id)
                and str(previous[1] or "Unknown") == str(rarity or "Unknown")
            ):
                previous_name = str(previous[0] or "").strip()
                current_name = str(name or "").strip()
                previous_name_ready = bool(previous_name and not previous_name.startswith("Model#"))
                current_name_ready = bool(current_name and not current_name.startswith("Model#"))
                names_compatible = (not previous_name_ready) or (not current_name_ready) or previous_name == current_name
                if names_compatible and int(qty) > int(prev_qty):
                    changed_this_tick = True
                    delta = int(qty) - int(prev_qty)
                    if is_unknown_name:
                        sender._buffer_pending_slot_delta(
                            slot_key=slot_key,
                            delta_qty=int(delta),
                            model_id=int(model_id),
                            item_id=int(item_id),
                            rarity=str(rarity or "Unknown"),
                            now_ts=time.time(),
                        )
                    else:
                        _append_candidate_event(
                            candidate_events,
                            changed_itemid_to_ready_name,
                            changed_model_rarity_to_ready_name,
                            name=name,
                            qty=int(delta),
                            rarity=rarity,
                            item_id=int(item_id),
                            model_id=int(model_id),
                            slot_key=slot_key,
                            reason="stack_increase",
                        )
                    continue
            if int(item_id) in prev_item_ids:
                prev_state = prev_item_state_by_id.get(int(item_id))
                if prev_state is not None:
                    prev_model_for_item, prev_qty_for_item = prev_state
                    if int(prev_model_for_item) == int(model_id) and int(prev_qty_for_item) == int(qty):
                        continue
            changed_this_tick = True
            if is_unknown_name:
                sender._buffer_pending_slot_delta(
                    slot_key=slot_key,
                    delta_qty=int(qty),
                    model_id=int(model_id),
                    item_id=int(item_id),
                    rarity=str(rarity or "Unknown"),
                    now_ts=time.time(),
                )
            else:
                _append_candidate_event(
                    candidate_events,
                    changed_itemid_to_ready_name,
                    changed_model_rarity_to_ready_name,
                    name=name,
                    qty=int(qty),
                    rarity=rarity,
                    item_id=int(item_id),
                    model_id=int(model_id),
                    slot_key=slot_key,
                    reason="slot_replaced",
                )
        elif qty > prev_qty:
            changed_this_tick = True
            delta = qty - prev_qty
            if is_unknown_name:
                sender._buffer_pending_slot_delta(
                    slot_key=slot_key,
                    delta_qty=int(delta),
                    model_id=int(model_id),
                    item_id=int(item_id),
                    rarity=str(rarity or "Unknown"),
                    now_ts=time.time(),
                )
            else:
                _append_candidate_event(
                    candidate_events,
                    changed_itemid_to_ready_name,
                    changed_model_rarity_to_ready_name,
                    name=name,
                    qty=int(delta),
                    rarity=rarity,
                    item_id=int(item_id),
                    model_id=int(model_id),
                    slot_key=slot_key,
                    reason="stack_increase",
                )

        if not is_unknown_name and slot_key in sender.pending_slot_deltas:
            if _flush_pending_same_slot_if_ready(sender, candidate_events, slot_key, name, rarity, item_id, model_id):
                changed_this_tick = True

        if changed_this_tick and not is_unknown_name:
            changed_itemid_to_ready_name[int(item_id)] = (name, str(rarity or "Unknown"))
            changed_model_rarity_to_ready_name[(int(model_id), str(rarity or "Unknown"))] = name

    _resolve_pending_slot_candidates(
        sender,
        candidate_events,
        changed_itemid_to_ready_name,
        changed_model_rarity_to_ready_name,
        live_item_ids,
        live_item_model_by_id,
        now_ts,
    )
    _expire_stale_pending_slots(
        sender,
        candidate_events,
        live_slots,
        live_item_ids,
        live_item_model_by_id,
        now_ts,
    )

    if candidate_events or sender.pending_slot_deltas:
        sender.last_inventory_activity_ts = time.time()

    candidate_events, suppressed_by_model_delta, suppressed_world_events = confirm_candidate_events(
        sender=sender,
        candidate_events=candidate_events,
        prev_model_qty=prev_model_qty,
        current_model_qty=current_model_qty,
        prev_item_ids=prev_item_ids,
        require_world_confirmation=not (
            use_carryover_baseline
            and str(getattr(sender, "last_session_transition_reason", "") or "").strip() == "map_change"
        ),
    )
    log_candidate_pipeline(
        sender=sender,
        candidate_events=candidate_events,
        suppressed_by_model_delta=suppressed_by_model_delta,
        suppressed_world_events=suppressed_world_events,
    )
    log_candidate_reset_trace(sender, candidate_events)

    is_leader_sender = sender._is_party_leader_client()
    enqueued_count = 0
    for event in candidate_events:
        sender._queue_drop(
            str(event.get("name", "Unknown Item")),
            int(event.get("qty", 1)),
            str(event.get("rarity", "Unknown")),
            time_str,
            int(event.get("item_id", 0)),
            int(event.get("model_id", 0)),
            event.get("slot_key"),
            str(event.get("reason", "delta")),
            is_leader_sender=is_leader_sender,
        )
        enqueued_count += 1

    sent_count = sender._flush_outbox()
    sender.last_candidate_count = len(candidate_events)
    sender.last_enqueued_count = enqueued_count
    sender.last_inventory_snapshot = current_snapshot
    if carryover_suppression_active:
        sender.carryover_inventory_snapshot = _build_carryover_snapshot_from_match_entries(carryover_match_entries)
        if not sender.carryover_inventory_snapshot:
            sender.carryover_suppression_until = 0.0
    else:
        sender.carryover_inventory_snapshot = {}
    sender.last_sent_count = sent_count if enqueued_count == 0 else min(enqueued_count, sent_count)
    _set_process_duration(sender, start_perf)
