from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any
from typing import Callable

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import TrackerDropMessage
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import TrackerNameChunkMessage
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_models import TrackerStatsChunkMessage
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import parse_drop_meta


def decode_slot(slot_encoded: int) -> tuple[int, int]:
    value = int(slot_encoded or 0)
    if value <= 0:
        return 0, 0
    return int((value >> 16) & 0xFFFF), int(value & 0xFFFF)


def is_duplicate_event(seen_events: dict[str, float], event_key: str) -> bool:
    if not event_key:
        return False
    return event_key in seen_events


def mark_seen_event(seen_events: dict[str, float], event_key: str, now_ts: float) -> None:
    if event_key:
        seen_events[event_key] = float(now_ts)


def iter_circular_indices(message_count: int, start_index: int, max_indices: int) -> Iterator[int]:
    total = max(0, int(message_count))
    if total <= 0:
        return
    budget = max(0, int(max_indices))
    if budget <= 0:
        return
    start = int(start_index) % total
    limit = min(total, budget)
    for offset in range(limit):
        yield int((start + offset) % total)


def should_skip_inventory_action_message(
    *,
    tag: str,
    inventory_action_tag: str,
    inventory_action_msgs_handled: int,
    max_inventory_action_msgs_per_tick: int,
) -> bool:
    if str(tag or "") != str(inventory_action_tag or ""):
        return False
    return int(inventory_action_msgs_handled) >= int(max_inventory_action_msgs_per_tick)


def build_tracker_drop_message(
    sender_email: str,
    item_name: str,
    rarity: str,
    meta_text: str,
    params: Any,
) -> TrackerDropMessage:
    meta = parse_drop_meta(meta_text)
    quantity = int(round(params[0])) if len(params) > 0 and float(params[0]) > 0 else 1
    item_id = int(round(params[1])) if len(params) > 1 and float(params[1]) > 0 else 0
    model_id = int(round(params[2])) if len(params) > 2 and float(params[2]) > 0 else 0
    slot_encoded = int(round(params[3])) if len(params) > 3 and float(params[3]) > 0 else 0
    slot_bag, slot_index = decode_slot(slot_encoded)

    return TrackerDropMessage(
        sender_email=str(sender_email or "").strip(),
        event_id=str(meta.get("event_id", "") or "").strip(),
        name_signature=str(meta.get("name_signature", "") or "").strip(),
        item_name=str(item_name or "Unknown Item"),
        rarity=str(rarity or "Unknown"),
        quantity=max(1, quantity),
        item_id=max(0, item_id),
        model_id=max(0, model_id),
        slot_bag=slot_bag,
        slot_index=slot_index,
    )


def _merge_chunk_bucket(
    buffers: dict[str, dict[str, Any]],
    key: str,
    chunk_text: str,
    chunk_idx: int,
    chunk_total: int,
    now_ts: float,
    reset_on_first_chunk: bool = True,
    total_mode: str = "replace",
) -> str:
    if not key:
        return ""

    if reset_on_first_chunk and int(chunk_idx) <= 1:
        bucket = {"chunks": {}, "total": chunk_total, "updated_at": now_ts}
    else:
        bucket = buffers.get(key, {"chunks": {}, "total": chunk_total, "updated_at": now_ts})

    current_total = int(bucket.get("total", 1))
    next_total = int(chunk_total) if int(chunk_total) > 0 else current_total
    if total_mode == "max":
        bucket["total"] = max(current_total, next_total)
    else:
        bucket["total"] = next_total

    bucket["chunks"][int(chunk_idx)] = str(chunk_text or "")
    bucket["updated_at"] = float(now_ts)
    buffers[key] = bucket

    total = max(1, int(bucket["total"]))
    if len(bucket["chunks"]) < total:
        return ""

    merged = "".join(bucket["chunks"].get(i, "") for i in range(1, total + 1)).strip()
    buffers.pop(key, None)
    return merged


def merge_name_chunk(
    name_chunk_buffers: dict[str, dict[str, Any]],
    full_name_by_signature: dict[str, str],
    name_signature: str,
    chunk_text: str,
    chunk_idx: int,
    chunk_total: int,
    now_ts: float,
) -> str:
    merged = _merge_chunk_bucket(
        buffers=name_chunk_buffers,
        key=str(name_signature or "").strip(),
        chunk_text=chunk_text,
        chunk_idx=chunk_idx,
        chunk_total=chunk_total,
        now_ts=now_ts,
        reset_on_first_chunk=False,
        total_mode="max",
    )
    if merged:
        full_name_by_signature[str(name_signature or "").strip()] = merged
    return merged


def merge_stats_text_chunk(
    stats_chunk_buffers: dict[str, dict[str, Any]],
    event_id: str,
    chunk_text: str,
    chunk_idx: int,
    chunk_total: int,
    now_ts: float,
) -> str:
    return _merge_chunk_bucket(
        buffers=stats_chunk_buffers,
        key=str(event_id or "").strip(),
        chunk_text=chunk_text,
        chunk_idx=chunk_idx,
        chunk_total=chunk_total,
        now_ts=now_ts,
        reset_on_first_chunk=True,
        total_mode="replace",
    )


def merge_stats_payload_chunk(
    stats_payload_chunk_buffers: dict[str, dict[str, Any]],
    event_id: str,
    chunk_text: str,
    chunk_idx: int,
    chunk_total: int,
    now_ts: float,
) -> str:
    return _merge_chunk_bucket(
        buffers=stats_payload_chunk_buffers,
        key=str(event_id or "").strip(),
        chunk_text=chunk_text,
        chunk_idx=chunk_idx,
        chunk_total=chunk_total,
        now_ts=now_ts,
        reset_on_first_chunk=True,
        total_mode="replace",
    )


def payload_has_valid_mods_json(payload_text: str) -> bool:
    try:
        payload_obj = json.loads(str(payload_text or "").strip())
    except (TypeError, json.JSONDecodeError):
        return False
    return isinstance(payload_obj, dict) and isinstance(payload_obj.get("mods", []), list)


def _extra_text(extra_data_list: Any, index: int, to_text_fn: Callable[[Any], str]) -> str:
    if not extra_data_list or len(extra_data_list) <= int(index):
        return ""
    try:
        return str(to_text_fn(extra_data_list[index]) or "")
    except (TypeError, ValueError, IndexError):
        return ""


def parse_tracker_name_chunk(
    *,
    extra_data_list: Any,
    to_text_fn: Callable[[Any], str],
    decode_chunk_meta_fn: Callable[[str], tuple[int, int]],
) -> TrackerNameChunkMessage | None:
    name_sig = _extra_text(extra_data_list, 1, to_text_fn).strip()
    if not name_sig:
        return None
    chunk_text = _extra_text(extra_data_list, 2, to_text_fn)
    chunk_meta = _extra_text(extra_data_list, 3, to_text_fn)
    chunk_idx, chunk_total = decode_chunk_meta_fn(chunk_meta)
    return TrackerNameChunkMessage(
        name_signature=name_sig,
        chunk_text=chunk_text,
        chunk_idx=int(chunk_idx),
        chunk_total=int(chunk_total),
    )


def parse_tracker_stats_chunk(
    *,
    extra_data_list: Any,
    to_text_fn: Callable[[Any], str],
    decode_chunk_meta_fn: Callable[[str], tuple[int, int]],
) -> TrackerStatsChunkMessage | None:
    event_id = _extra_text(extra_data_list, 1, to_text_fn).strip()
    if not event_id:
        return None
    chunk_text = _extra_text(extra_data_list, 2, to_text_fn)
    chunk_meta = _extra_text(extra_data_list, 3, to_text_fn)
    chunk_idx, chunk_total = decode_chunk_meta_fn(chunk_meta)
    return TrackerStatsChunkMessage(
        event_id=event_id,
        chunk_text=chunk_text,
        chunk_idx=int(chunk_idx),
        chunk_total=int(chunk_total),
    )


def handle_tracker_name_branch(
    *,
    extra_0: str,
    expected_tag: str,
    extra_data_list: Any,
    to_text_fn: Callable[[Any], str],
    decode_chunk_meta_fn: Callable[[str], tuple[int, int]],
    merge_name_chunk_fn: Callable[[dict[str, dict[str, Any]], dict[str, str], str, str, int, int, float], str],
    name_chunk_buffers: dict[str, dict[str, Any]],
    full_name_by_signature: dict[str, str],
    now_ts: float,
) -> bool:
    if str(extra_0 or "") != str(expected_tag or ""):
        return False
    chunk = parse_tracker_name_chunk(
        extra_data_list=extra_data_list,
        to_text_fn=to_text_fn,
        decode_chunk_meta_fn=decode_chunk_meta_fn,
    )
    if chunk is None:
        return True
    merge_name_chunk_fn(
        name_chunk_buffers,
        full_name_by_signature,
        chunk.name_signature,
        chunk.chunk_text,
        chunk.chunk_idx,
        chunk.chunk_total,
        now_ts,
    )
    return True


def handle_tracker_stats_text_branch(
    *,
    extra_0: str,
    expected_tag: str,
    extra_data_list: Any,
    to_text_fn: Callable[[Any], str],
    decode_chunk_meta_fn: Callable[[str], tuple[int, int]],
    merge_stats_text_chunk_fn: Callable[[dict[str, dict[str, Any]], str, str, int, int, float], str],
    stats_chunk_buffers: dict[str, dict[str, Any]],
    now_ts: float,
    on_merged_text_fn: Callable[[str, str], Any],
) -> bool:
    if str(extra_0 or "") != str(expected_tag or ""):
        return False
    chunk = parse_tracker_stats_chunk(
        extra_data_list=extra_data_list,
        to_text_fn=to_text_fn,
        decode_chunk_meta_fn=decode_chunk_meta_fn,
    )
    if chunk is None:
        return True
    merged = merge_stats_text_chunk_fn(
        stats_chunk_buffers,
        chunk.event_id,
        chunk.chunk_text,
        chunk.chunk_idx,
        chunk.chunk_total,
        now_ts,
    )
    if merged:
        on_merged_text_fn(chunk.event_id, merged)
    return True


def handle_tracker_stats_payload_branch(
    *,
    extra_0: str,
    expected_tag: str,
    extra_data_list: Any,
    to_text_fn: Callable[[Any], str],
    decode_chunk_meta_fn: Callable[[str], tuple[int, int]],
    merge_stats_payload_chunk_fn: Callable[[dict[str, dict[str, Any]], str, str, int, int, float], str],
    stats_payload_chunk_buffers: dict[str, dict[str, Any]],
    now_ts: float,
    on_merged_payload_fn: Callable[[str, str], Any],
) -> bool:
    if str(extra_0 or "") != str(expected_tag or ""):
        return False
    chunk = parse_tracker_stats_chunk(
        extra_data_list=extra_data_list,
        to_text_fn=to_text_fn,
        decode_chunk_meta_fn=decode_chunk_meta_fn,
    )
    if chunk is None:
        return True
    merged_payload = merge_stats_payload_chunk_fn(
        stats_payload_chunk_buffers,
        chunk.event_id,
        chunk.chunk_text,
        chunk.chunk_idx,
        chunk.chunk_total,
        now_ts,
    )
    if merged_payload:
        on_merged_payload_fn(chunk.event_id, merged_payload)
    return True


def handle_tracker_drop_branch(
    *,
    extra_0: str,
    expected_tag: str,
    extra_data_list: Any,
    shared_msg: Any,
    to_text_fn: Callable[[Any], str],
    normalize_text_fn: Callable[[Any], str],
    build_tracker_drop_message_fn: Callable[[str, str, str, str, Any], TrackerDropMessage],
    resolve_full_name_fn: Callable[[str], str],
    normalize_rarity_label_fn: Callable[[str, str], str],
) -> TrackerDropMessage | None:
    if str(extra_0 or "") != str(expected_tag or ""):
        return None

    item_name_raw = _extra_text(extra_data_list, 1, to_text_fn) or "Unknown Item"
    rarity_raw = _extra_text(extra_data_list, 2, to_text_fn) or "Unknown"
    meta_text = _extra_text(extra_data_list, 3, to_text_fn)

    drop_msg = build_tracker_drop_message_fn(
        str(normalize_text_fn(getattr(shared_msg, "SenderEmail", "")) or "").strip(),
        item_name_raw,
        rarity_raw,
        meta_text,
        getattr(shared_msg, "Params", ()),
    )
    name_sig = str(drop_msg.name_signature or "").strip()
    raw_name_clean = str(item_name_raw or "").strip()
    raw_name_clean_lc = raw_name_clean.lower()
    if name_sig:
        resolved_name = str(resolve_full_name_fn(name_sig) or "").strip()
        if resolved_name:
            resolved_name_lc = resolved_name.lower()
            # Guard against stale/signature-collision substitutions:
            # only accept if resolved long name is compatible with raw drop name.
            if (
                not raw_name_clean_lc
                or resolved_name_lc.startswith(raw_name_clean_lc)
                or raw_name_clean_lc.startswith(resolved_name_lc)
            ):
                drop_msg.item_name = resolved_name
            elif len(drop_msg.item_name) >= 31:
                drop_msg.item_name = f"{drop_msg.item_name}~{name_sig[:4]}"
        elif len(drop_msg.item_name) >= 31:
            drop_msg.item_name = f"{drop_msg.item_name}~{name_sig[:4]}"
    drop_msg.rarity = str(normalize_rarity_label_fn(drop_msg.item_name, drop_msg.rarity) or "").strip() or drop_msg.rarity
    return drop_msg


def extract_event_id_hint(
    *,
    extra_0: str,
    extra_data_list: Any,
    to_text_fn: Callable[[Any], str],
) -> str:
    tag = str(extra_0 or "").strip()
    if tag in ("TrackerStatsV1", "TrackerStatsV2"):
        return _extra_text(extra_data_list, 1, to_text_fn).strip()
    if tag == "TrackerDrop":
        meta_text = _extra_text(extra_data_list, 3, to_text_fn)
        meta = parse_drop_meta(meta_text)
        return str(meta.get("event_id", "") or "").strip()
    return ""


def handle_inventory_action_branch(
    *,
    extra_0: str,
    expected_tag: str,
    extra_data_list: Any,
    shared_msg: Any,
    to_text_fn: Callable[[Any], str],
    normalize_text_fn: Callable[[Any], str],
    run_inventory_action_fn: Callable[[str, str, str, str], Any],
) -> bool:
    if str(extra_0 or "") != str(expected_tag or ""):
        return False
    sender_email = str(normalize_text_fn(getattr(shared_msg, "SenderEmail", "")) or "").strip()
    action_code = _extra_text(extra_data_list, 1, to_text_fn)
    action_payload = _extra_text(extra_data_list, 2, to_text_fn)
    action_meta = _extra_text(extra_data_list, 3, to_text_fn)
    run_inventory_action_fn(action_code, action_payload, action_meta, sender_email)
    return True


def handle_inventory_stats_request_branch(
    *,
    extra_0: str,
    expected_tag: str,
    shared_msg: Any,
    my_email: str,
    normalize_text_fn: Callable[[Any], str],
    send_inventory_kit_stats_response_fn: Callable[[str], Any],
) -> bool:
    if str(extra_0 or "") != str(expected_tag or ""):
        return False
    sender_email = str(normalize_text_fn(getattr(shared_msg, "SenderEmail", "")) or "").strip()
    if sender_email and sender_email != str(my_email or "").strip():
        send_inventory_kit_stats_response_fn(sender_email)
    return True


def handle_inventory_stats_response_branch(
    *,
    extra_0: str,
    expected_tag: str,
    extra_data_list: Any,
    shared_msg: Any,
    to_text_fn: Callable[[Any], str],
    normalize_text_fn: Callable[[Any], str],
    safe_int_fn: Callable[[Any, int], int],
    get_account_data_fn: Callable[[str], Any],
    upsert_inventory_kit_stats_fn: Callable[[str, str, int, dict[str, int], int, int], Any],
) -> bool:
    if str(extra_0 or "") != str(expected_tag or ""):
        return False

    sender_email = str(normalize_text_fn(getattr(shared_msg, "SenderEmail", "")) or "").strip()
    if not sender_email:
        return True

    sender_account = get_account_data_fn(sender_email)
    sender_name = _extra_text(extra_data_list, 1, to_text_fn) or sender_email
    sender_party_pos = int(safe_int_fn(_extra_text(extra_data_list, 2, to_text_fn), 0))
    sender_party_id = int(getattr(sender_account.AgentPartyData, "PartyID", 0)) if sender_account else 0
    sender_map_id = int(getattr(sender_account.AgentData.Map, "MapID", 0)) if sender_account else 0

    stats = {
        "salvage_uses": int(round(shared_msg.Params[0])) if len(shared_msg.Params) > 0 else 0,
        "superior_id_uses": int(round(shared_msg.Params[1])) if len(shared_msg.Params) > 1 else 0,
        "salvage_kits": int(round(shared_msg.Params[2])) if len(shared_msg.Params) > 2 else 0,
        "superior_id_kits": int(round(shared_msg.Params[3])) if len(shared_msg.Params) > 3 else 0,
    }
    upsert_inventory_kit_stats_fn(
        sender_email,
        sender_name,
        sender_party_pos,
        stats,
        sender_map_id,
        sender_party_id,
    )
    return True
