import json
import sys
import time


IMPORT_OPTIONAL_ERRORS = (ImportError, ModuleNotFoundError, AttributeError)
EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _viewer_runtime_module(viewer):
    try:
        return sys.modules.get(viewer.__class__.__module__)
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _runtime_attr(viewer, name: str, fallback=None):
    module = _viewer_runtime_module(viewer)
    if module is not None and hasattr(module, name):
        return getattr(module, name)
    return fallback


def is_monitoring_settled_for_auto_inventory(viewer, set_status: bool = False) -> bool:
    drop_tracker_sender = _runtime_attr(viewer, "DropTrackerSender")
    reason = ""
    now_ts = time.time()
    try:
        sender = drop_tracker_sender()
        if not bool(getattr(sender, "is_warmed_up", True)):
            reason = "drop monitor warming up"
        elif int(getattr(sender, "last_snapshot_total", 0)) > 0 and int(getattr(sender, "last_snapshot_ready", 0)) == 0:
            reason = "inventory snapshot unstable"
        else:
            pending_names = len(getattr(sender, "pending_slot_deltas", {}) or {})
            if pending_names > 0:
                reason = f"pending name resolution ({pending_names})"
            else:
                settle_seconds = max(0.2, float(getattr(viewer, "auto_monitoring_settle_seconds", 1.2)))
                activity_ts = float(getattr(sender, "last_inventory_activity_ts", 0.0) or 0.0)
                if activity_ts > 0.0:
                    elapsed = max(0.0, now_ts - activity_ts)
                    if elapsed < settle_seconds:
                        reason = f"inventory changed {elapsed:.1f}s ago"
    except EXPECTED_RUNTIME_ERRORS:
        reason = ""

    if reason and set_status:
        last_gate_ts = float(getattr(viewer, "auto_monitoring_last_gate_status_ts", 0.0) or 0.0)
        if (now_ts - last_gate_ts) >= 1.5:
            viewer.auto_monitoring_last_gate_status_ts = now_ts
            viewer.set_status(f"Auto inventory paused: {reason}")
    return reason == ""


def refresh_auto_inventory_pending_counts(viewer, force: bool = False):
    routines = _runtime_attr(viewer, "Routines")
    if not force and not viewer.auto_inventory_snapshot_timer.IsExpired():
        return
    viewer.auto_inventory_snapshot_timer.Reset()

    id_pending = 0
    salvage_pending = 0
    try:
        id_rarities = viewer._get_selected_id_rarities()
        if id_rarities:
            id_items = routines.Items.GetUnidentifiedItems(list(id_rarities), [])
            id_pending = len(id_items) if id_items else 0
    except EXPECTED_RUNTIME_ERRORS:
        id_pending = 0
    try:
        salvage_rarities = viewer._get_selected_salvage_rarities()
        if salvage_rarities:
            salvage_items = routines.Items.GetSalvageableItems(list(salvage_rarities), [])
            salvage_pending = len(salvage_items) if salvage_items else 0
    except EXPECTED_RUNTIME_ERRORS:
        salvage_pending = 0

    viewer.auto_id_pending_jobs = max(0, int(id_pending))
    viewer.auto_salvage_pending_jobs = max(0, int(salvage_pending))


def run_inventory_routine_job(viewer, routine, job_type: str = ""):
    py4gw_api = _runtime_attr(viewer, "Py4GW")
    job = viewer._ensure_text(job_type).strip().lower()
    if job == "identify":
        viewer.auto_id_job_running = True
    elif job == "salvage":
        viewer.auto_salvage_job_running = True
    try:
        if routine is not None:
            yield from routine
    except EXPECTED_RUNTIME_ERRORS as e:
        if py4gw_api is not None:
            py4gw_api.Console.Log(
                "DropViewer",
                f"Auto {job or 'inventory'} routine failed: {e}",
                py4gw_api.Console.MessageType.Warning,
            )
    finally:
        if job == "identify":
            viewer.auto_id_job_running = False
        elif job == "salvage":
            viewer.auto_salvage_job_running = False
        refresh_auto_inventory_pending_counts(viewer, force=True)


def remember_identify_mod_capture_candidates(viewer, item_ids) -> int:
    try:
        raw_list = list(item_ids or [])
    except EXPECTED_RUNTIME_ERRORS:
        raw_list = []
    if not raw_list:
        return 0
    now_ts = time.time()
    ttl_s = max(5.0, float(getattr(viewer, "pending_identify_mod_capture_ttl_s", 20.0)))
    deadline = now_ts + ttl_s
    remembered = 0
    for raw_item_id in raw_list:
        item_id = max(0, viewer._safe_int(raw_item_id, 0))
        if item_id <= 0:
            continue
        prev_deadline = float(viewer.pending_identify_mod_capture.get(item_id, 0.0) or 0.0)
        viewer.pending_identify_mod_capture[item_id] = max(prev_deadline, deadline)
        remembered += 1
    return remembered


def queue_identify_for_rarities(viewer, rarities):
    routines = _runtime_attr(viewer, "Routines")
    global_cache = _runtime_attr(viewer, "GLOBAL_CACHE")
    py4gw_api = _runtime_attr(viewer, "Py4GW")
    now_ts = time.time()
    viewer.auto_id_last_run_ts = now_ts
    if not is_monitoring_settled_for_auto_inventory(viewer, set_status=False):
        viewer.auto_id_last_queued = 0
        return 0
    if viewer.auto_id_job_running or viewer.auto_salvage_job_running or viewer.auto_buy_kits_job_running or viewer.auto_inventory_reorder_job_running:
        return 0
    try:
        items = routines.Items.GetUnidentifiedItems(list(rarities), [])
        if not items:
            viewer.auto_id_last_queued = 0
            refresh_auto_inventory_pending_counts(viewer, force=True)
            return 0
        remember_identify_mod_capture_candidates(viewer, items)
        global_cache.Coroutines.append(
            run_inventory_routine_job(
                viewer,
                routines.Yield.Items.IdentifyItems(items, log=True),
                job_type="identify",
            )
        )
        queued = len(items)
        viewer.auto_id_last_queued = int(queued)
        viewer.auto_id_total_queued += int(queued)
        refresh_auto_inventory_pending_counts(viewer, force=True)
        return queued
    except EXPECTED_RUNTIME_ERRORS as e:
        if py4gw_api is not None:
            py4gw_api.Console.Log("DropViewer", f"Identify queue failed: {e}", py4gw_api.Console.MessageType.Warning)
        viewer.auto_id_last_queued = 0
        return 0


def queue_salvage_for_rarities(viewer, rarities):
    routines = _runtime_attr(viewer, "Routines")
    global_cache = _runtime_attr(viewer, "GLOBAL_CACHE")
    py4gw_api = _runtime_attr(viewer, "Py4GW")
    now_ts = time.time()
    viewer.auto_salvage_last_run_ts = now_ts
    if not is_monitoring_settled_for_auto_inventory(viewer, set_status=False):
        viewer.auto_salvage_last_queued = 0
        return 0
    if viewer.auto_id_job_running or viewer.auto_salvage_job_running or viewer.auto_buy_kits_job_running or viewer.auto_inventory_reorder_job_running:
        return 0
    try:
        items = routines.Items.GetSalvageableItems(list(rarities), [])
        if not items:
            viewer.auto_salvage_last_queued = 0
            refresh_auto_inventory_pending_counts(viewer, force=True)
            return 0
        salvage_checkboxes = {int(item_id): True for item_id in list(items) if int(item_id) > 0}
        if not salvage_checkboxes:
            viewer.auto_salvage_last_queued = 0
            refresh_auto_inventory_pending_counts(viewer, force=True)
            return 0
        salvage_routine = None
        try:
            from Sources.ApoSource.InvPlus.Coroutines import SalvageCheckedItems
            salvage_routine = SalvageCheckedItems(
                salvage_checkboxes,
                keep_salvage_kits=0,
                deposit_materials=False,
            )
        except IMPORT_OPTIONAL_ERRORS:
            salvage_routine = routines.Yield.Items.SalvageItems(items, log=True)

        global_cache.Coroutines.append(
            run_inventory_routine_job(
                viewer,
                salvage_routine,
                job_type="salvage",
            )
        )
        queued = len(items)
        viewer.auto_salvage_last_queued = int(queued)
        viewer.auto_salvage_total_queued += int(queued)
        refresh_auto_inventory_pending_counts(viewer, force=True)
        return queued
    except EXPECTED_RUNTIME_ERRORS as e:
        if py4gw_api is not None:
            py4gw_api.Console.Log("DropViewer", f"Salvage queue failed: {e}", py4gw_api.Console.MessageType.Warning)
        viewer.auto_salvage_last_queued = 0
        return 0


def process_pending_identify_mod_capture(viewer):
    item_api = _runtime_attr(viewer, "Item")
    drop_tracker_sender = _runtime_attr(viewer, "DropTrackerSender")
    pending = getattr(viewer, "pending_identify_mod_capture", None)
    if not isinstance(pending, dict) or not pending:
        return
    now_ts = time.time()
    max_scan = max(1, int(getattr(viewer, "pending_identify_mod_capture_max_scan_per_tick", 16)))
    scanned = 0
    for item_id in list(pending.keys()):
        if scanned >= max_scan:
            break
        scanned += 1
        deadline = float(pending.get(item_id, 0.0) or 0.0)
        if deadline > 0.0 and now_ts >= deadline:
            pending.pop(item_id, None)
            continue
        try:
            if not bool(item_api.Usage.IsIdentified(int(item_id))):
                continue
        except EXPECTED_RUNTIME_ERRORS:
            continue

        try:
            sender = drop_tracker_sender()
            model_id = max(0, viewer._safe_int(item_api.GetModelID(int(item_id)), 0))
            sender.clear_cached_event_stats_for_item(int(item_id), model_id)
            sender.schedule_name_refresh_for_item(int(item_id), model_id)
        except EXPECTED_RUNTIME_ERRORS:
            pass

        viewer._build_item_stats_from_live_item(int(item_id), "")
        pending.pop(item_id, None)


def process_pending_identify_responses(viewer):
    item_api = _runtime_attr(viewer, "Item")
    py4gw_api = _runtime_attr(viewer, "Py4GW")

    def _is_identified(item_id: int) -> bool:
        try:
            return bool(item_api.Usage.IsIdentified(int(item_id)))
        except (TypeError, ValueError, RuntimeError, AttributeError):
            return False

    def _payload_ready_for_identify(payload_text: str, item_id: int, identified: bool, timed_out: bool) -> bool:
        if not identified or timed_out:
            return True
        try:
            payload_obj = json.loads(viewer._ensure_text(payload_text).strip())
        except EXPECTED_RUNTIME_ERRORS:
            return False
        if not isinstance(payload_obj, dict):
            return False
        mods = list(payload_obj.get("mods", []) or [])
        if mods:
            return True
        return False

    try:
        completed = viewer.identify_response_scheduler.tick(
            build_payload_fn=lambda item_id: viewer._build_item_snapshot_payload_from_live_item(int(item_id), ""),
            is_identified_fn=_is_identified,
            send_payload_fn=lambda receiver_email, event_id, payload: viewer._send_tracker_stats_payload_chunks_to_email(receiver_email, event_id, payload),
            build_stats_fn=lambda item_id: viewer._build_item_stats_from_live_item(int(item_id), ""),
            send_stats_fn=lambda receiver_email, event_id, stats: viewer._send_tracker_stats_chunks_to_email(receiver_email, event_id, stats),
            payload_ready_fn=_payload_ready_for_identify,
        )
        if completed > 0 and viewer.verbose_shmem_item_logs and py4gw_api is not None:
            py4gw_api.Console.Log(
                "DropViewer",
                f"ASYNC ID responses completed={completed} pending={viewer.identify_response_scheduler.pending_count()}",
                py4gw_api.Console.MessageType.Info,
            )
    except (TypeError, ValueError, RuntimeError, AttributeError) as e:
        if py4gw_api is not None:
            py4gw_api.Console.Log(
                "DropViewer",
                f"ASYNC ID scheduler error: {e}",
                py4gw_api.Console.MessageType.Warning,
            )


def run_auto_inventory_actions_tick(viewer):
    py4gw_api = _runtime_attr(viewer, "Py4GW")
    try:
        if viewer.auto_outpost_store_enabled and viewer._run_auto_outpost_store_tick():
            return

        if (
            viewer.auto_outpost_store_job_running
            or viewer.auto_id_job_running
            or viewer.auto_salvage_job_running
            or viewer.auto_buy_kits_job_running
            or viewer.auto_gold_balance_job_running
            or viewer.auto_inventory_reorder_job_running
        ):
            return

        if viewer._run_auto_gold_balance_once_on_outpost_entry_tick():
            return

        if viewer._run_auto_buy_kits_once_on_outpost_entry_tick():
            return

        if viewer._run_auto_inventory_reorder_once_on_outpost_entry_tick():
            return

        if (viewer.auto_id_enabled or viewer.auto_salvage_enabled) and not is_monitoring_settled_for_auto_inventory(viewer, set_status=True):
            return

        queued_id = 0
        id_due = viewer.auto_id_enabled and viewer.auto_id_timer.IsExpired()
        if id_due:
            viewer.auto_id_timer.Reset()
            id_rarities = viewer._get_selected_id_rarities()
            if id_rarities:
                queued_id = queue_identify_for_rarities(viewer, id_rarities)
                if queued_id > 0:
                    viewer.set_status(f"Auto ID: queued {queued_id}")
                    return

        if viewer.auto_salvage_enabled and viewer.auto_salvage_timer.IsExpired():
            viewer.auto_salvage_timer.Reset()
            salvage_rarities = viewer._get_selected_salvage_rarities()
            if salvage_rarities:
                queued_salvage = queue_salvage_for_rarities(viewer, salvage_rarities)
                if queued_salvage > 0:
                    viewer.set_status(f"Auto Salvage: queued {queued_salvage}")
    except EXPECTED_RUNTIME_ERRORS as e:
        if viewer.verbose_shmem_item_logs and py4gw_api is not None:
            py4gw_api.Console.Log("DropViewer", f"Auto inventory tick failed: {e}", py4gw_api.Console.MessageType.Warning)
