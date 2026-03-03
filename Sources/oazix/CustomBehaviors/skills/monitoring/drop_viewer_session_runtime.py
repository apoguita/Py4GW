import sys

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _viewer_runtime_module(viewer):
    try:
        return sys.modules.get(viewer.__class__.__module__)
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _bind_impl(viewer, export_name: str):
    module = _viewer_runtime_module(viewer)
    if module is None:
        raise RuntimeError("viewer runtime module unavailable")
    impl_name = f"_drop_viewer_session_runtime_impl_{export_name}"
    if hasattr(module, impl_name):
        return getattr(module, impl_name)
    source = _SOURCES[export_name]
    exec(source, module.__dict__, module.__dict__)
    return getattr(module, impl_name)


_SOURCES = {
    'reset_live_log_file': 'def _drop_viewer_session_runtime_impl_reset_live_log_file(viewer):\n    try:\n        os.makedirs(os.path.dirname(viewer.log_path), exist_ok=True)\n        with open(viewer.log_path, mode=\'w\', newline=\'\', encoding=\'utf-8\') as f:\n            writer = csv.writer(f)\n            writer.writerow(list(DROP_LOG_HEADER))\n        viewer.last_read_time = os.path.getmtime(viewer.log_path)\n    except EXPECTED_RUNTIME_ERRORS as e:\n        Py4GW.Console.Log("DropViewer", f"Failed to reset live log file: {e}", Py4GW.Console.MessageType.Warning)',
    'reset_live_session': 'def _drop_viewer_session_runtime_impl_reset_live_session(viewer):\n    viewer._seal_sender_session_floors()\n    viewer.raw_drops = []\n    viewer.aggregated_drops = {}\n    viewer.total_drops = 0\n    viewer.selected_item_key = None\n    viewer.selected_log_row = None\n    viewer._log_autoscroll_initialized = False\n    viewer._last_log_autoscroll_total_drops = 0\n    viewer._request_log_scroll_bottom = False\n    viewer._request_agg_scroll_bottom = False\n    viewer.shmem_bootstrap_done = False\n    viewer.last_read_time = 0\n    viewer.recent_log_cache = {}\n    viewer.seen_events = {}\n    viewer.name_chunk_buffers = {}\n    viewer.full_name_by_signature = {}\n    viewer.stats_by_event = {}\n    viewer.stats_chunk_buffers = {}\n    viewer.stats_payload_by_event = {}\n    viewer.stats_payload_chunk_buffers = {}\n    viewer.event_state_by_key = {}\n    viewer.stats_render_cache_by_event = {}\n    viewer.stats_name_signature_by_event = {}\n    viewer.remote_stats_request_last_by_event = {}\n    viewer.remote_stats_pending_by_event = {}\n    viewer.model_name_by_id = {}\n    viewer.name_trace_recent_lines = []\n    viewer._shmem_scan_start_index = 0\n    viewer.identify_response_scheduler.clear()\n    viewer.pending_identify_mod_capture = {}\n    viewer._reset_live_log_file()',
    'arm_reset_trace': 'def _drop_viewer_session_runtime_impl_arm_reset_trace(\n    viewer,\n    reason: str,\n    previous_map_id: int = 0,\n    current_map_id: int = 0,\n    previous_instance_uptime_ms: int = 0,\n    current_instance_uptime_ms: int = 0,\n):\n    viewer.reset_trace_until = time.time() + 20.0\n    viewer.reset_trace_drop_logs_remaining = 18\n    viewer._log_reset_trace(\n        (\n            f"RESET TRACE armed reason={str(reason or \'unknown\')} "\n            f"actor={viewer._reset_trace_actor_label()} "\n            f"map={int(previous_map_id or 0)}->{int(current_map_id or 0)} "\n            f"uptime_ms={int(previous_instance_uptime_ms or 0)}->{int(current_instance_uptime_ms or 0)} "\n            f"rows={len(viewer.raw_drops)} total={int(viewer.total_drops)}"\n        )\n    )',
    'reset_trace_active': 'def _drop_viewer_session_runtime_impl_reset_trace_active(viewer) -> bool:\n    return time.time() <= float(getattr(viewer, "reset_trace_until", 0.0) or 0.0)',
    'reset_trace_actor_label': 'def _drop_viewer_session_runtime_impl_reset_trace_actor_label(viewer) -> str:\n    try:\n        actor_name = viewer._ensure_text(Player.GetName()).strip()\n    except EXPECTED_RUNTIME_ERRORS:\n        actor_name = ""\n    try:\n        actor_email = viewer._ensure_text(Player.GetAccountEmail()).strip()\n    except EXPECTED_RUNTIME_ERRORS:\n        actor_email = ""\n    actor_name = actor_name or "Unknown"\n    actor_email = actor_email or "unknown@email"\n    return f"{actor_name}<{actor_email}>"',
    'log_reset_trace': 'def _drop_viewer_session_runtime_impl_log_reset_trace(viewer, message: str, consume: bool = False):\n    if not viewer._reset_trace_active():\n        return\n    if consume:\n        remaining = int(getattr(viewer, "reset_trace_drop_logs_remaining", 0) or 0)\n        if remaining <= 0:\n            return\n        viewer.reset_trace_drop_logs_remaining = remaining - 1\n    viewer.reset_trace_lines.append(str(message or ""))\n    if len(viewer.reset_trace_lines) > 120:\n        del viewer.reset_trace_lines[:-120]\n    Py4GW.Console.Log(\n        "DropViewer",\n        str(message or ""),\n        Py4GW.Console.MessageType.Warning,\n    )',
    'get_reset_trace_lines': 'def _drop_viewer_session_runtime_impl_get_reset_trace_lines(viewer) -> list[str]:\n    lines = []\n    viewer_lines = getattr(viewer, "reset_trace_lines", None)\n    if isinstance(viewer_lines, list):\n        for line in viewer_lines:\n            txt = viewer._ensure_text(line).strip()\n            if txt:\n                lines.append(f"Viewer | {txt}")\n    try:\n        sender = DropTrackerSender()\n        sender_lines = getattr(sender, "debug_reset_trace_lines", None)\n        if isinstance(sender_lines, list):\n            for line in sender_lines:\n                txt = viewer._ensure_text(line).strip()\n                if txt:\n                    lines.append(f"Sender | {txt}")\n    except EXPECTED_RUNTIME_ERRORS:\n        pass\n    return lines[-160:]',
    'clear_reset_trace_lines': 'def _drop_viewer_session_runtime_impl_clear_reset_trace_lines(viewer):\n    viewer.reset_trace_lines = []\n    try:\n        sender = DropTrackerSender()\n        if isinstance(getattr(sender, "debug_reset_trace_lines", None), list):\n            sender.debug_reset_trace_lines = []\n    except EXPECTED_RUNTIME_ERRORS:\n        pass',
    'log_map_watch': 'def _drop_viewer_session_runtime_impl_log_map_watch(viewer, message: str):\n    msg = viewer._ensure_text(message).strip()\n    if not msg:\n        return\n    viewer.map_watch_lines.append(msg)\n    if len(viewer.map_watch_lines) > 120:\n        del viewer.map_watch_lines[:-120]\n    Py4GW.Console.Log("DropViewer", msg, Py4GW.Console.MessageType.Warning)',
    'get_map_watch_lines': 'def _drop_viewer_session_runtime_impl_get_map_watch_lines(viewer) -> list[str]:\n    return list(getattr(viewer, "map_watch_lines", []) or [])[-120:]',
    'clear_map_watch_lines': 'def _drop_viewer_session_runtime_impl_clear_map_watch_lines(viewer):\n    viewer.map_watch_lines = []',
    'seal_sender_session_floors': 'def _drop_viewer_session_runtime_impl_seal_sender_session_floors(viewer):\n    floors = getattr(viewer, "sender_session_floor_by_email", None)\n    if not isinstance(floors, dict):\n        viewer.sender_session_floor_by_email = {}\n        floors = viewer.sender_session_floor_by_email\n    last_seen = getattr(viewer, "sender_session_last_seen_by_email", None)\n    if not isinstance(last_seen, dict):\n        return\n    for sender_email, session_id in list(last_seen.items()):\n        sender_key = viewer._ensure_text(sender_email).strip().lower()\n        session_value = max(0, viewer._safe_int(session_id, 0))\n        if not sender_key or session_value <= 0:\n            continue\n        floors[sender_key] = max(max(0, viewer._safe_int(floors.get(sender_key, 0), 0)), session_value)',
    'reset_sender_tracking_session': 'def _drop_viewer_session_runtime_impl_reset_sender_tracking_session(viewer, current_map_id: int = 0, current_instance_uptime_ms: int = 0):\n    try:\n        sender = DropTrackerSender()\n        if sender is None:\n            return\n        if hasattr(sender, "_begin_new_session"):\n            sender._begin_new_session("viewer_sync_reset", current_map_id, current_instance_uptime_ms)\n        else:\n            try:\n                sender._arm_reset_trace("viewer_sync_reset", current_map_id, current_instance_uptime_ms)\n            except EXPECTED_RUNTIME_ERRORS:\n                pass\n            sender._reset_tracking_state()\n            sender.last_seen_map_id = max(0, viewer._safe_int(current_map_id, 0))\n            sender.last_seen_instance_uptime_ms = max(0, viewer._safe_int(current_instance_uptime_ms, 0))\n    except EXPECTED_RUNTIME_ERRORS:\n        return',
    'begin_new_explorable_session': 'def _drop_viewer_session_runtime_impl_begin_new_explorable_session(\n    viewer,\n    reason: str,\n    current_map_id: int = 0,\n    current_instance_uptime_ms: int = 0,\n    status_message: str = "Auto reset on map change",\n) -> None:\n    viewer._arm_reset_trace(\n        reason,\n        viewer.last_seen_map_id,\n        current_map_id,\n        viewer.last_seen_instance_uptime_ms,\n        current_instance_uptime_ms,\n    )\n    viewer.last_seen_map_id = max(0, viewer._safe_int(current_map_id, 0))\n    viewer.last_seen_instance_uptime_ms = max(0, viewer._safe_int(current_instance_uptime_ms, 0))\n    viewer._reset_sender_tracking_session(current_map_id, current_instance_uptime_ms)\n    viewer._reset_live_session()\n    viewer._flush_pending_tracker_messages()\n    viewer.map_change_ignore_until = time.time() + 3.0\n    viewer.last_chat_index = -1\n    if Player.IsChatHistoryReady():\n        viewer.last_chat_index = len(Player.GetChatHistory())\n    viewer.set_status(status_message)',
    'flush_pending_tracker_messages': 'def _drop_viewer_session_runtime_impl_flush_pending_tracker_messages(viewer) -> int:\n    flushed = 0\n    try:\n        my_email = viewer._ensure_text(Player.GetAccountEmail()).strip()\n        if not my_email:\n            return 0\n        shmem = getattr(GLOBAL_CACHE, "ShMem", None)\n        if shmem is None:\n            return 0\n        tracker_tags = {\n            "TrackerDrop",\n            "TrackerNameV2",\n            "TrackerStatsV1",\n            "TrackerStatsV2",\n            "TrackerAckV2",\n        }\n        for msg_idx, shared_msg in shmem.GetAllMessages():\n            receiver_email = viewer._ensure_text(getattr(shared_msg, "ReceiverEmail", "")).strip()\n            if receiver_email != my_email:\n                continue\n            extra_data_list = getattr(shared_msg, "ExtraData", None)\n            if not extra_data_list or len(extra_data_list) <= 0:\n                continue\n            tag = viewer._ensure_text(extra_data_list[0]).strip()\n            if tag not in tracker_tags:\n                continue\n            shmem.MarkMessageAsFinished(my_email, msg_idx)\n            flushed += 1\n    except EXPECTED_RUNTIME_ERRORS:\n        return flushed\n    return flushed',
    'load_drops': 'def _drop_viewer_session_runtime_impl_load_drops(viewer):\n    if not os.path.isfile(viewer.log_path):\n        viewer.raw_drops = []\n        viewer.aggregated_drops = {}\n        viewer.total_drops = 0\n        return\n\n    try:\n        current_mtime = os.path.getmtime(viewer.log_path)\n        if current_mtime <= viewer.last_read_time:\n            return # No change\n\n        viewer.last_read_time = current_mtime\n\n        viewer._parse_log_file(viewer.log_path)\n\n    except EXPECTED_RUNTIME_ERRORS as e:\n        viewer.set_status(f"Error reading log: {e}")',
    'parse_log_file': 'def _drop_viewer_session_runtime_impl_parse_log_file(viewer, filepath):\n    parsed_rows = parse_drop_log_file(filepath, map_name_resolver=Map.GetMapName)\n    temp_drops, temp_agg, total, temp_stats_by_event = build_state_from_parsed_rows(\n        parsed_rows=parsed_rows,\n        ensure_text_fn=viewer._ensure_text,\n        make_stats_cache_key_fn=viewer._make_stats_cache_key,\n        canonical_name_fn=viewer._canonical_agg_item_name,\n    )\n    viewer.raw_drops = temp_drops\n    viewer.aggregated_drops = temp_agg\n    viewer.total_drops = int(total)\n    viewer.stats_by_event = temp_stats_by_event\n    viewer.stats_name_signature_by_event = {}\n    viewer._log_autoscroll_initialized = False\n    viewer._last_log_autoscroll_total_drops = int(viewer.total_drops)',
}


def reset_live_log_file(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'reset_live_log_file')(viewer, *args, **kwargs)

def reset_live_session(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'reset_live_session')(viewer, *args, **kwargs)

def arm_reset_trace(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'arm_reset_trace')(viewer, *args, **kwargs)

def reset_trace_active(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'reset_trace_active')(viewer, *args, **kwargs)

def reset_trace_actor_label(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'reset_trace_actor_label')(viewer, *args, **kwargs)

def log_reset_trace(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'log_reset_trace')(viewer, *args, **kwargs)

def get_reset_trace_lines(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'get_reset_trace_lines')(viewer, *args, **kwargs)

def clear_reset_trace_lines(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'clear_reset_trace_lines')(viewer, *args, **kwargs)

def log_map_watch(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'log_map_watch')(viewer, *args, **kwargs)

def get_map_watch_lines(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'get_map_watch_lines')(viewer, *args, **kwargs)

def clear_map_watch_lines(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'clear_map_watch_lines')(viewer, *args, **kwargs)

def seal_sender_session_floors(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'seal_sender_session_floors')(viewer, *args, **kwargs)

def reset_sender_tracking_session(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'reset_sender_tracking_session')(viewer, *args, **kwargs)

def begin_new_explorable_session(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'begin_new_explorable_session')(viewer, *args, **kwargs)

def flush_pending_tracker_messages(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'flush_pending_tracker_messages')(viewer, *args, **kwargs)

def load_drops(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'load_drops')(viewer, *args, **kwargs)

def parse_log_file(viewer, *args, **kwargs):
    return _bind_impl(viewer, 'parse_log_file')(viewer, *args, **kwargs)


def parse_log_file_local(viewer, *args, **kwargs):
    return parse_log_file(viewer, *args, **kwargs)
