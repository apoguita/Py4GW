from __future__ import annotations


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

    if viewer.runtime_config_dirty:
        viewer._flush_runtime_config_if_dirty()

    PyImGui.text(
        f"Perf: poll_ms={viewer.last_shmem_poll_ms:.2f} "
        f"processed={viewer.last_shmem_processed} scanned={viewer.last_shmem_scanned} ack_sent={viewer.last_ack_sent}"
    )
