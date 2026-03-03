import time

from Py4GWCoreLib import Player, Py4GW


EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def prune_sent_event_stats_cache(sender, now_ts: float | None = None):
    now = float(now_ts if now_ts is not None else time.time())
    ttl_s = max(30.0, float(getattr(sender, "sent_event_stats_ttl_seconds", 600.0)))
    cache = getattr(sender, "sent_event_stats_cache", {})
    if not isinstance(cache, dict) or not cache:
        return
    for event_id in list(cache.keys()):
        entry = cache.get(event_id)
        if not isinstance(entry, dict):
            cache.pop(event_id, None)
            continue
        created_at = float(entry.get("created_at", now))
        if (now - created_at) > ttl_s:
            cache.pop(event_id, None)


def remember_event_identity(
    sender,
    event_id: str,
    item_id: int,
    model_id: int,
    item_name: str,
    name_signature: str = "",
    rarity: str = "",
    last_receiver_email: str = "",
):
    event_key = str(event_id or "").strip()
    if not event_key:
        return
    now_ts = time.time()
    sender._prune_sent_event_stats_cache(now_ts)
    cache = getattr(sender, "sent_event_stats_cache", None)
    if not isinstance(cache, dict):
        sender.sent_event_stats_cache = {}
        cache = sender.sent_event_stats_cache
    existing = cache.get(event_key, {})
    if not isinstance(existing, dict):
        existing = {}
    existing["item_id"] = int(item_id)
    existing["model_id"] = int(model_id)
    existing["item_name"] = str(item_name or "").strip()
    existing["name_signature"] = str(name_signature or "").strip().lower()
    existing["rarity"] = str(rarity or existing.get("rarity", "") or "").strip()
    existing["last_receiver_email"] = str(last_receiver_email or existing.get("last_receiver_email", "") or "").strip().lower()
    existing["created_at"] = float(now_ts)
    existing["stats_text"] = str(existing.get("stats_text", "") or "").strip()
    cache[event_key] = existing


def get_cached_event_identity(sender, event_id: str) -> dict:
    event_key = str(event_id or "").strip()
    if not event_key:
        return {}
    sender._prune_sent_event_stats_cache()
    cache = getattr(sender, "sent_event_stats_cache", {})
    if not isinstance(cache, dict):
        return {}
    entry = cache.get(event_key, None)
    if not isinstance(entry, dict):
        return {}
    return dict(entry)


def resolve_live_item_id_for_event(sender, event_id: str, preferred_item_id: int = 0) -> int:
    event_key = str(event_id or "").strip()
    preferred = int(preferred_item_id or 0)
    identity = sender.get_cached_event_identity(event_key) if event_key else {}
    has_identity = bool(identity)
    if not has_identity:
        return max(0, preferred)
    expected_model_id = int(identity.get("model_id", 0))
    if preferred > 0:
        direct_probe = {
            "item_id": int(preferred),
            "model_id": expected_model_id,
            "name_signature": "",
        }
        resolved_direct = sender._resolve_event_item_id_for_stats(direct_probe)
        if resolved_direct > 0:
            return int(resolved_direct)
    probe_entry = {
        "item_id": max(0, preferred) if preferred > 0 else int(identity.get("item_id", 0)),
        "model_id": expected_model_id,
        "name_signature": str(identity.get("name_signature", "") or "").strip().lower(),
    }
    resolved = sender._resolve_event_item_id_for_stats(probe_entry)
    if resolved > 0:
        return int(resolved)
    return 0


def clear_cached_event_stats(sender, event_id: str, item_id: int = 0):
    event_key = str(event_id or "").strip()
    if not event_key:
        return
    cache = getattr(sender, "sent_event_stats_cache", {})
    if not isinstance(cache, dict):
        return
    entry = cache.get(event_key)
    if not isinstance(entry, dict):
        return
    wanted_item_id = int(item_id or 0)
    if wanted_item_id > 0 and int(entry.get("item_id", 0)) > 0 and int(entry.get("item_id", 0)) != wanted_item_id:
        return
    entry["stats_text"] = ""
    entry["created_at"] = float(time.time())
    cache[event_key] = entry


def clear_cached_event_stats_for_item(sender, item_id: int = 0, model_id: int = 0):
    wanted_item_id = int(item_id or 0)
    wanted_model_id = int(model_id or 0)
    if wanted_item_id <= 0 and wanted_model_id <= 0:
        return
    cache = getattr(sender, "sent_event_stats_cache", {})
    if not isinstance(cache, dict) or not cache:
        return
    now_ts = float(time.time())
    for event_key, entry in cache.items():
        if not isinstance(entry, dict):
            continue
        cached_item_id = int(entry.get("item_id", 0))
        cached_model_id = int(entry.get("model_id", 0))
        if wanted_item_id > 0 and cached_item_id > 0 and cached_item_id == wanted_item_id:
            entry["stats_text"] = ""
            entry["created_at"] = now_ts
            continue
        if wanted_model_id > 0 and cached_model_id > 0 and cached_model_id == wanted_model_id:
            entry["stats_text"] = ""
            entry["created_at"] = now_ts


def remember_event_stats_snapshot(
    sender,
    event_id: str,
    item_id: int,
    model_id: int,
    item_name: str,
    stats_text: str,
    name_signature: str = "",
    rarity: str = "",
    last_receiver_email: str = "",
):
    event_key = str(event_id or "").strip()
    if not event_key:
        return
    stats_value = str(stats_text or "").strip()
    if not stats_value:
        return
    now_ts = time.time()
    sender._prune_sent_event_stats_cache(now_ts)
    cache = getattr(sender, "sent_event_stats_cache", None)
    if not isinstance(cache, dict):
        sender.sent_event_stats_cache = {}
        cache = sender.sent_event_stats_cache
    existing = cache.get(event_key, {})
    if not isinstance(existing, dict):
        existing = {}
    resolved_name_sig = str(name_signature or existing.get("name_signature", "") or "").strip().lower()
    cache[event_key] = {
        "item_id": int(item_id),
        "model_id": int(model_id),
        "item_name": str(item_name or "").strip(),
        "name_signature": resolved_name_sig,
        "rarity": str(rarity or existing.get("rarity", "") or "").strip(),
        "last_receiver_email": str(last_receiver_email or existing.get("last_receiver_email", "") or "").strip().lower(),
        "stats_text": stats_value,
        "created_at": float(now_ts),
    }


def should_track_name_refresh(_sender, item_name: str = "", rarity: str = "") -> bool:
    rarity_txt = str(rarity or "").strip().lower()
    if rarity_txt in {"blue", "purple", "gold"}:
        return True
    name_txt = str(item_name or "").strip().lower()
    return "rune" in name_txt


def get_cached_event_stats_text(sender, event_id: str, item_id: int = 0, model_id: int = 0) -> str:
    event_key = str(event_id or "").strip()
    if not event_key:
        return ""
    sender._prune_sent_event_stats_cache()
    cache = getattr(sender, "sent_event_stats_cache", {})
    if not isinstance(cache, dict):
        return ""
    entry = cache.get(event_key, None)
    if not isinstance(entry, dict):
        return ""
    cached_item_id = int(entry.get("item_id", 0))
    cached_model_id = int(entry.get("model_id", 0))
    wanted_item_id = int(item_id or 0)
    wanted_model_id = int(model_id or 0)
    if wanted_item_id > 0 and cached_item_id > 0 and wanted_item_id != cached_item_id:
        return ""
    if wanted_model_id > 0 and cached_model_id > 0 and wanted_model_id != cached_model_id:
        return ""
    return str(entry.get("stats_text", "") or "").strip()


def reset_tracking_state(sender, clear_outbox: bool = True):
    sender.last_inventory_snapshot = {}
    sender.pending_slot_deltas = {}
    sender.carryover_inventory_snapshot = {}
    sender.carryover_suppression_until = 0.0
    sender.current_world_item_agents = {}
    sender.recent_world_item_disappearances = []
    sender.world_item_seen_since_reset = False
    sender.last_world_item_scan_count = 0
    sender.is_warmed_up = False
    sender.stable_snapshot_count = 0
    sender.session_startup_pending = False
    sender.warmup_grace_until = 0.0
    sender.last_snapshot_total = 0
    sender.last_snapshot_ready = 0
    sender.last_snapshot_not_ready = 0
    sender.last_sent_count = 0
    sender.last_candidate_count = 0
    sender.last_enqueued_count = 0
    sender.last_ack_count = 0
    sender.last_process_duration_ms = 0.0
    sender.last_inventory_activity_ts = 0.0
    sender.pending_name_refresh_by_event = {}
    sender.sent_event_stats_cache = {}
    if clear_outbox:
        sender.outbox_queue = []


def arm_reset_trace(sender, reason: str, current_map_id: int = 0, current_instance_uptime_ms: int = 0):
    sender.debug_reset_trace_until = time.time() + 8.0
    sender.debug_reset_trace_snapshot_logs_remaining = 6
    sender.debug_reset_trace_event_logs_remaining = 10
    sender.debug_reset_trace_lines = []
    sender._log_reset_trace(
        (
            f"RESET TRACE armed reason={str(reason or '').strip() or 'unknown'} "
            f"actor={sender._reset_trace_actor_label()} "
            f"sender_session={int(getattr(sender, 'sender_session_id', 0) or 0)} "
            f"map={int(current_map_id or 0)} uptime_ms={int(current_instance_uptime_ms or 0)} "
            f"prev_snapshot={len(getattr(sender, 'last_inventory_snapshot', {}) or {})} "
            f"pending={len(getattr(sender, 'pending_slot_deltas', {}) or {})} "
            f"queued={len(getattr(sender, 'outbox_queue', []) or [])} warmed={bool(getattr(sender, 'is_warmed_up', False))}"
        ),
        consume_snapshot=False,
    )


def reset_trace_active(sender) -> bool:
    return float(getattr(sender, "debug_reset_trace_until", 0.0) or 0.0) > float(time.time())


def reset_trace_actor_label(_sender) -> str:
    try:
        player_name = str(Player.GetName() or "").strip()
    except EXPECTED_RUNTIME_ERRORS:
        player_name = ""
    try:
        player_email = str(Player.GetAccountEmail() or "").strip()
    except EXPECTED_RUNTIME_ERRORS:
        player_email = ""
    return f"{player_name or 'Unknown'}<{player_email or 'unknown@email'}>"


def advance_sender_session_id(sender) -> int:
    sender.sender_session_id = max(1, int(getattr(sender, "sender_session_id", 1) or 1) + 1)
    sender.event_sequence = 0
    return int(sender.sender_session_id)


def begin_new_session(sender, reason: str, current_map_id: int = 0, current_instance_uptime_ms: int = 0):
    normalized_reason = str(reason or "").strip() or "unknown"
    sender.last_session_transition_reason = normalized_reason
    sender._arm_reset_trace(normalized_reason, current_map_id, current_instance_uptime_ms)
    sender._advance_sender_session_id()
    sender._reset_tracking_state(clear_outbox=False)
    sender.last_seen_map_id = int(current_map_id or 0)
    sender.last_seen_instance_uptime_ms = int(current_instance_uptime_ms or 0)
    sender.session_startup_pending = bool(sender.carryover_inventory_snapshot) and normalized_reason == "map_change"


def log_reset_trace(sender, message: str, consume_snapshot: bool = False):
    if not sender._reset_trace_active():
        return
    if consume_snapshot:
        remaining = int(getattr(sender, "debug_reset_trace_snapshot_logs_remaining", 0) or 0)
        if remaining <= 0:
            return
        sender.debug_reset_trace_snapshot_logs_remaining = remaining - 1
    else:
        remaining = int(getattr(sender, "debug_reset_trace_event_logs_remaining", 0) or 0)
        if remaining > 0:
            sender.debug_reset_trace_event_logs_remaining = remaining - 1
    Py4GW.Console.Log("DropTrackerSender", str(message or ""), Py4GW.Console.MessageType.Info)
