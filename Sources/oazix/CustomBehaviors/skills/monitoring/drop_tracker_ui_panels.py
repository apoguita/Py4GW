from __future__ import annotations

import time


def default_ui_colors() -> dict[str, tuple[float, float, float, float]]:
    return {
        "accent": (0.35, 0.72, 1.0, 1.0),
        "muted": (0.70, 0.74, 0.80, 1.0),
        "panel_bg": (0.11, 0.13, 0.17, 0.92),
        "primary_btn": (0.18, 0.48, 0.80, 0.95),
        "primary_hover": (0.24, 0.58, 0.93, 1.0),
        "primary_active": (0.14, 0.42, 0.72, 1.0),
        "secondary_btn": (0.20, 0.24, 0.30, 0.95),
        "secondary_hover": (0.27, 0.32, 0.39, 1.0),
        "secondary_active": (0.16, 0.20, 0.26, 1.0),
        "success_btn": (0.12, 0.53, 0.34, 0.95),
        "success_hover": (0.16, 0.64, 0.40, 1.0),
        "success_active": (0.10, 0.45, 0.30, 1.0),
        "warn_btn": (0.62, 0.44, 0.16, 0.95),
        "warn_hover": (0.74, 0.54, 0.20, 1.0),
        "warn_active": (0.54, 0.37, 0.13, 1.0),
        "danger_btn": (0.66, 0.23, 0.22, 0.95),
        "danger_hover": (0.79, 0.29, 0.27, 1.0),
        "danger_active": (0.57, 0.19, 0.18, 1.0),
    }


def draw_runtime_controls_panel(viewer, PyImGui) -> None:
    """Behavior-preserving runtime controls drawer extracted from DropViewerWindow."""
    viewer._draw_section_header("Runtime")
    if viewer._styled_button(
        f"Verbose Logs: {'ON' if viewer.verbose_shmem_item_logs else 'OFF'}",
        "success" if viewer.verbose_shmem_item_logs else "secondary",
        tooltip="Detailed shared-memory logs.",
    ):
        viewer.verbose_shmem_item_logs = not viewer.verbose_shmem_item_logs
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button(
        f"ACK: {'ON' if viewer.send_tracker_ack_enabled else 'OFF'}",
        "success" if viewer.send_tracker_ack_enabled else "warning",
        tooltip="Acknowledges tracker events to peers.",
    ):
        viewer.send_tracker_ack_enabled = not viewer.send_tracker_ack_enabled
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button(
        f"Perf Logs: {'ON' if viewer.enable_perf_logs else 'OFF'}",
        "success" if viewer.enable_perf_logs else "secondary",
        tooltip="Periodic poll/throughput diagnostics.",
    ):
        viewer.enable_perf_logs = not viewer.enable_perf_logs
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button(
        f"Pickup Watch: {'ON' if viewer.enable_chat_item_tracking else 'OFF'}",
        "success" if viewer.enable_chat_item_tracking else "secondary",
        tooltip="Track pickup chat lines live without restarting the viewer.",
    ):
        viewer.enable_chat_item_tracking = not viewer.enable_chat_item_tracking
        viewer.runtime_config_dirty = True
    PyImGui.new_line()
    if viewer._styled_button(
        f"Debug Item Stats: {'ON' if viewer.debug_item_stats_panel else 'OFF'}",
        "success" if viewer.debug_item_stats_panel else "secondary",
        tooltip="Show raw selected-item modifiers and payload decode in Selected Item Stats panel.",
    ):
        viewer.debug_item_stats_panel = not viewer.debug_item_stats_panel
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    PyImGui.text(f"Debug Height: {int(viewer.debug_item_stats_panel_height)}")
    if viewer._styled_button("- DebugH", "secondary"):
        viewer.debug_item_stats_panel_height = max(120, int(viewer.debug_item_stats_panel_height) - 40)
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("+ DebugH", "secondary"):
        viewer.debug_item_stats_panel_height = min(900, int(viewer.debug_item_stats_panel_height) + 40)
        viewer.runtime_config_dirty = True

    sender_debug_logs = bool(viewer.runtime_config.get("debug_pipeline_logs", False))
    sender_ack = bool(viewer.runtime_config.get("enable_delivery_ack", True))
    sender_max_send = int(viewer.runtime_config.get("max_send_per_tick", 12))
    sender_outbox = int(viewer.runtime_config.get("max_outbox_size", 2000))
    sender_retry_s = float(viewer.runtime_config.get("retry_interval_seconds", 1.0))
    sender_max_retries = int(viewer.runtime_config.get("max_retry_attempts", 12))

    if viewer._styled_button(
        f"Sender Debug: {'ON' if sender_debug_logs else 'OFF'}",
        "success" if sender_debug_logs else "secondary",
    ):
        viewer.runtime_config["debug_pipeline_logs"] = not sender_debug_logs
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button(
        f"Sender ACK: {'ON' if sender_ack else 'OFF'}",
        "success" if sender_ack else "warning",
    ):
        viewer.runtime_config["enable_delivery_ack"] = not sender_ack
        viewer.runtime_config_dirty = True

    PyImGui.text(f"Sender max_send/tick: {sender_max_send}")
    if viewer._styled_button("- Send", "secondary"):
        viewer.runtime_config["max_send_per_tick"] = max(1, sender_max_send - 1)
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("+ Send", "secondary"):
        viewer.runtime_config["max_send_per_tick"] = min(100, sender_max_send + 1)
        viewer.runtime_config_dirty = True

    PyImGui.same_line(0.0, 25.0)
    PyImGui.text(f"Sender outbox: {sender_outbox}")
    if viewer._styled_button("- Outbox", "secondary"):
        viewer.runtime_config["max_outbox_size"] = max(100, sender_outbox - 100)
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("+ Outbox", "secondary"):
        viewer.runtime_config["max_outbox_size"] = min(20000, sender_outbox + 100)
        viewer.runtime_config_dirty = True

    PyImGui.text(f"Sender retry_s: {sender_retry_s:.1f} max_retries: {sender_max_retries}")
    if viewer._styled_button("- RetryS", "secondary"):
        viewer.runtime_config["retry_interval_seconds"] = max(0.2, round(sender_retry_s - 0.1, 2))
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("+ RetryS", "secondary"):
        viewer.runtime_config["retry_interval_seconds"] = min(10.0, round(sender_retry_s + 0.1, 2))
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("- Retries", "secondary"):
        viewer.runtime_config["max_retry_attempts"] = max(1, sender_max_retries - 1)
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("+ Retries", "secondary"):
        viewer.runtime_config["max_retry_attempts"] = min(100, sender_max_retries + 1)
        viewer.runtime_config_dirty = True

    PyImGui.text(f"ShMem msg/tick: {viewer.max_shmem_messages_per_tick}")
    if viewer._styled_button("- Msg", "secondary"):
        viewer.max_shmem_messages_per_tick = max(5, viewer.max_shmem_messages_per_tick - 5)
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("+ Msg", "secondary"):
        viewer.max_shmem_messages_per_tick = min(300, viewer.max_shmem_messages_per_tick + 5)
        viewer.runtime_config_dirty = True

    PyImGui.same_line(0.0, 25.0)
    PyImGui.text(f"ShMem scan/tick: {viewer.max_shmem_scan_per_tick}")
    if viewer._styled_button("- Scan", "secondary"):
        viewer.max_shmem_scan_per_tick = max(20, viewer.max_shmem_scan_per_tick - 20)
        viewer.runtime_config_dirty = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("+ Scan", "secondary"):
        viewer.max_shmem_scan_per_tick = min(3000, viewer.max_shmem_scan_per_tick + 20)
        viewer.runtime_config_dirty = True

    PyImGui.separator()
    unknown_count = viewer._get_unknown_mod_count()
    unresolved_count = viewer._get_unknown_mod_unresolved_count()
    PyImGui.text(f"Unknown mod IDs tracked: {unknown_count} (unresolved: {unresolved_count})")
    if viewer._styled_button(
        "Export Unknown Mods",
        "secondary",
        tooltip="Save unknown modifier ID catalog to JSON.",
    ):
        export_path = viewer._export_unknown_mod_catalog()
        if export_path:
            viewer.set_status(f"Unknown mods exported: {export_path}")
        else:
            viewer.set_status("Unknown mods export failed.")
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button(
        "Export Unknown Guesses",
        "secondary",
        tooltip="Save guessed modifier names with confidence to JSON.",
    ):
        guess_export_path = viewer._export_unknown_mod_guess_report(include_known=True)
        if guess_export_path:
            viewer.set_status(f"Unknown mod guess report exported: {guess_export_path}")
        else:
            viewer.set_status("Unknown mod guess export failed.")
    for summary_line in viewer._unknown_mod_summary_lines(limit=4):
        PyImGui.text(summary_line)
    for summary_line in viewer._unknown_mod_guess_summary_lines(limit=6, include_known=False):
        PyImGui.text(summary_line)
    for notify_line in viewer._unknown_mod_notification_lines(limit=4):
        PyImGui.text_colored(notify_line, (1.0, 0.86, 0.40, 1.0))
    pending_count = int(viewer._unknown_mod_pending_count())
    PyImGui.text_colored(f"Pending unknown notes: {pending_count}", (1.0, 0.80, 0.45, 1.0))
    for pending_line in viewer._unknown_mod_pending_lines(limit=6):
        PyImGui.text_colored(pending_line, (1.0, 0.80, 0.45, 1.0))

    PyImGui.separator()
    PyImGui.text("Unknown Mod Name Mapper")
    viewer.unknown_mod_name_edit_id = max(
        0,
        int(PyImGui.input_int("Mod ID##UnknownModMap", int(getattr(viewer, "unknown_mod_name_edit_id", 0)))),
    )
    viewer.unknown_mod_name_edit_text = PyImGui.input_text(
        "Name##UnknownModMap",
        viewer._ensure_text(getattr(viewer, "unknown_mod_name_edit_text", "")),
    )
    if viewer._styled_button("Save Mapping", "success", tooltip="Save ID -> name mapping for unknown mod rendering."):
        if viewer._set_unknown_mod_custom_name(
            int(getattr(viewer, "unknown_mod_name_edit_id", 0)),
            viewer._ensure_text(getattr(viewer, "unknown_mod_name_edit_text", "")),
        ):
            viewer.set_status(f"Unknown mod mapping saved for id={int(getattr(viewer, 'unknown_mod_name_edit_id', 0))}")
        else:
            viewer.set_status("Unknown mod mapping save failed.")
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("Remove Mapping", "warning", tooltip="Remove saved name for this mod ID."):
        if viewer._set_unknown_mod_custom_name(int(getattr(viewer, "unknown_mod_name_edit_id", 0)), ""):
            viewer.set_status(f"Unknown mod mapping removed for id={int(getattr(viewer, 'unknown_mod_name_edit_id', 0))}")
        else:
            viewer.set_status("No mapping removed.")
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("Remove Pending", "secondary", tooltip="Remove this ID from pending unknown notes without mapping it."):
        pending_id = int(getattr(viewer, "unknown_mod_name_edit_id", 0))
        if viewer._remove_unknown_mod_pending_note(pending_id):
            viewer.set_status(f"Pending unknown note removed for id={pending_id}")
        else:
            viewer.set_status("No pending note removed.")
    for mapped_line in viewer._unknown_mod_name_map_summary_lines(limit=4):
        PyImGui.text_colored(mapped_line, (0.62, 0.90, 0.72, 1.0))

    PyImGui.separator()
    trace_lines = list(viewer._get_reset_trace_lines() or [])
    PyImGui.text(f"Reset Trace: {len(trace_lines)} lines")
    if viewer._styled_button(
        "Copy Reset Trace",
        "secondary",
        tooltip="Copy captured reset trace lines to clipboard.",
    ):
        try:
            PyImGui.set_clipboard_text("\n".join(trace_lines))
            viewer.set_status("Reset trace copied to clipboard")
        except Exception as e:  # clipboard API can fail outside normal UI focus
            viewer.set_status(f"Reset trace copy failed: {e}")
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button(
        "Clear Reset Trace",
        "secondary",
        tooltip="Clear in-memory map/district reset trace lines.",
    ):
        viewer._clear_reset_trace_lines()
        trace_lines = []
    if trace_lines:
        if PyImGui.begin_child(
            "DropTrackerResetTracePanel",
            size=(0.0, 180.0),
            border=True,
            flags=PyImGui.WindowFlags.HorizontalScrollbar,
        ):
            for line in trace_lines[-80:]:
                PyImGui.text(viewer._ensure_text(line))
        PyImGui.end_child()
    else:
        PyImGui.text_colored("No reset trace lines captured yet.", (0.70, 0.74, 0.80, 1.0))

    PyImGui.separator()
    map_watch_lines = list(viewer._get_map_watch_lines() or [])
    PyImGui.text(f"Map Watch: {len(map_watch_lines)} lines")
    if viewer._styled_button(
        "Copy Map Watch",
        "secondary",
        tooltip="Copy raw map/instance watch lines to clipboard.",
    ):
        try:
            PyImGui.set_clipboard_text("\n".join(map_watch_lines))
            viewer.set_status("Map watch copied to clipboard")
        except Exception as e:
            viewer.set_status(f"Map watch copy failed: {e}")
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button(
        "Clear Map Watch",
        "secondary",
        tooltip="Clear in-memory map/instance watch lines.",
    ):
        viewer._clear_map_watch_lines()
        map_watch_lines = []
    if map_watch_lines:
        if PyImGui.begin_child(
            "DropTrackerMapWatchPanel",
            size=(0.0, 120.0),
            border=True,
            flags=PyImGui.WindowFlags.HorizontalScrollbar,
        ):
            for line in map_watch_lines[-40:]:
                PyImGui.text(viewer._ensure_text(line))
        PyImGui.end_child()
    else:
        PyImGui.text_colored("No map watch lines captured yet.", (0.70, 0.74, 0.80, 1.0))

    PyImGui.separator()
    viewer._draw_section_header("Live Debugger")
    runtime_cfg = viewer.runtime_config if isinstance(getattr(viewer, "runtime_config", None), dict) else {}
    detailed_emit = bool(runtime_cfg.get("live_debug_detailed", True))
    force_debug_refresh = False
    if viewer._styled_button(
        f"Auto Refresh: {'ON' if viewer.live_debug_auto_refresh else 'OFF'}",
        "success" if viewer.live_debug_auto_refresh else "secondary",
        tooltip="Refresh live debug tail every few hundred milliseconds.",
    ):
        viewer.live_debug_auto_refresh = not viewer.live_debug_auto_refresh
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("Refresh Now", "primary", tooltip="Force refresh live debug records."):
        force_debug_refresh = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button(
        f"Detailed Emit: {'ON' if detailed_emit else 'OFF'}",
        "success" if detailed_emit else "secondary",
        tooltip="Toggle verbose sender-side live debug events.",
    ):
        runtime_cfg["live_debug_detailed"] = not detailed_emit
        viewer.runtime_config = runtime_cfg
        viewer.runtime_config_dirty = True

    PyImGui.text(f"Tail Lines: {int(viewer.live_debug_tail_limit)}")
    if viewer._styled_button("- Lines", "secondary"):
        viewer.live_debug_tail_limit = max(20, int(viewer.live_debug_tail_limit) - 20)
        force_debug_refresh = True
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("+ Lines", "secondary"):
        viewer.live_debug_tail_limit = min(600, int(viewer.live_debug_tail_limit) + 20)
        force_debug_refresh = True

    previous_filter = viewer._ensure_text(getattr(viewer, "live_debug_filter_text", ""))
    viewer.live_debug_filter_text = PyImGui.input_text("Filter##DropTrackerLiveDebug", previous_filter)
    if viewer.live_debug_filter_text != previous_filter:
        force_debug_refresh = True

    previous_event_filter = viewer._ensure_text(getattr(viewer, "live_debug_event_filter", ""))
    viewer.live_debug_event_filter = PyImGui.input_text("Event##DropTrackerLiveDebug", previous_event_filter)
    if viewer.live_debug_event_filter != previous_event_filter:
        force_debug_refresh = True

    actor_options = ["All", "viewer", "sender", "raw"]
    current_actor = viewer._ensure_text(getattr(viewer, "live_debug_actor_filter", "")).strip().lower()
    actor_idx = 0
    if current_actor in actor_options[1:]:
        actor_idx = actor_options.index(current_actor)
    next_actor_idx = int(PyImGui.combo("Actor##DropTrackerLiveDebug", actor_idx, actor_options))
    if next_actor_idx != actor_idx:
        viewer.live_debug_actor_filter = "" if next_actor_idx <= 0 else actor_options[next_actor_idx]
        force_debug_refresh = True

    should_poll_debug = bool(viewer.live_debug_auto_refresh) or force_debug_refresh
    if should_poll_debug:
        debug_rows = viewer._refresh_live_debug_cache(force=force_debug_refresh)
    else:
        debug_rows = list(getattr(viewer, "live_debug_cached_records", []) or [])

    debug_lines: list[str] = []
    for payload in debug_rows:
        debug_lines.append(viewer._format_live_debug_record(payload, max_extra_fields=8))
    last_refresh_ts = float(getattr(viewer, "live_debug_last_refresh_at", 0.0) or 0.0)
    refresh_age = max(0.0, time.time() - last_refresh_ts) if last_refresh_ts > 0.0 else 0.0
    refresh_age_txt = f"{refresh_age:.1f}s ago" if last_refresh_ts > 0.0 else "never"
    PyImGui.text(
        f"Rows: {len(debug_lines)} | Last refresh: {refresh_age_txt} | {viewer._ensure_text(viewer.live_debug_log_path)}"
    )
    if viewer._styled_button("Copy Visible", "secondary", tooltip="Copy currently displayed debug lines."):
        try:
            PyImGui.set_clipboard_text("\n".join(debug_lines))
            viewer.set_status("Live debug lines copied to clipboard")
        except Exception as e:
            viewer.set_status(f"Live debug copy failed: {e}")
    PyImGui.same_line(0.0, 10.0)
    if viewer._styled_button("Clear Debug Log", "warning", tooltip="Truncate live debug JSONL log file."):
        cleared_path = viewer._clear_live_debug_log()
        viewer.live_debug_cached_records = []
        viewer.live_debug_last_refresh_at = 0.0
        force_debug_refresh = True
        if cleared_path:
            viewer.set_status(f"Live debug log cleared: {cleared_path}")
        else:
            viewer.set_status("Live debug clear failed")

    if force_debug_refresh:
        debug_rows = viewer._refresh_live_debug_cache(force=True)
        debug_lines = [viewer._format_live_debug_record(payload, max_extra_fields=8) for payload in debug_rows]
    if debug_lines:
        if PyImGui.begin_child(
            "DropTrackerLiveDebugPanel",
            size=(0.0, 220.0),
            border=True,
            flags=PyImGui.WindowFlags.HorizontalScrollbar,
        ):
            for line in debug_lines:
                PyImGui.text(viewer._ensure_text(line))
        PyImGui.end_child()
    else:
        PyImGui.text_colored("No live debug lines match current filters.", (0.70, 0.74, 0.80, 1.0))

    if viewer.runtime_config_dirty:
        viewer._flush_runtime_config_if_dirty()

    PyImGui.text(
        f"Perf: poll_ms={viewer.last_shmem_poll_ms:.2f} "
        f"processed={viewer.last_shmem_processed} scanned={viewer.last_shmem_scanned} ack_sent={viewer.last_ack_sent}"
    )
