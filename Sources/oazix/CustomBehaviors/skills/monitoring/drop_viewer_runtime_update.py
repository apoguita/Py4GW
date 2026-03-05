import sys
import time
from typing import Any


EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _should_coalesce_viewer_reset(viewer, reason: str, current_map_id: int, current_instance_uptime_ms: int) -> bool:
    reset_reason = viewer._ensure_text(reason).strip() or "unknown"
    current_map = max(0, int(current_map_id or 0))
    current_uptime = max(0, int(current_instance_uptime_ms or 0))
    now_ts = time.time()
    last_reason = viewer._ensure_text(getattr(viewer, "last_reset_reason", "")).strip()
    last_map = max(0, int(getattr(viewer, "last_reset_map_id", 0) or 0))
    last_uptime = max(0, int(getattr(viewer, "last_reset_instance_uptime_ms", 0) or 0))
    last_started_at = float(getattr(viewer, "last_reset_started_at", 0.0) or 0.0)
    if (
        reset_reason == last_reason
        and current_map > 0
        and current_map == last_map
        and (now_ts - last_started_at) <= 3.5
        and current_uptime > 0
        and last_uptime > 0
        and abs(current_uptime - last_uptime) <= 2500
    ):
        viewer.last_seen_map_id = current_map
        viewer.last_seen_instance_uptime_ms = max(last_uptime, current_uptime)
        return True
    viewer.last_reset_reason = reset_reason
    viewer.last_reset_map_id = current_map
    viewer.last_reset_instance_uptime_ms = current_uptime
    viewer.last_reset_started_at = now_ts
    return False


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


def _log_update_error(viewer, message: str, is_warning: bool = False) -> None:
    py4gw_api = _runtime_attr(viewer, "Py4GW", None)
    if py4gw_api is None:
        return
    try:
        message_type = py4gw_api.Console.MessageType.Warning if is_warning else py4gw_api.Console.MessageType.Error
        py4gw_api.Console.Log("DropViewer", message, message_type)
    except EXPECTED_RUNTIME_ERRORS:
        return


def process_chat_message(viewer, msg: Any) -> None:
    player_api = _runtime_attr(viewer, "Player", None)
    party_api = _runtime_attr(viewer, "Party", None)
    py4gw_api = _runtime_attr(viewer, "Py4GW", None)

    text = viewer._ensure_text(msg)

    match_gold = viewer.gold_regex.search(text)
    if match_gold:
        try:
            if player_api is not None and party_api is not None:
                my_id = player_api.GetAgentID()
                leader_id = party_api.GetPartyLeaderID()
                if my_id == leader_id:
                    amount = int(match_gold.group(2).replace(",", ""))
                    viewer._log_drop_to_file(player_api.GetName(), "Gold", amount, "Currency")
                    if py4gw_api is not None:
                        py4gw_api.Console.Log("DropViewer", f"TRACKED: Gold x{amount}", py4gw_api.Console.MessageType.Info)
        except EXPECTED_RUNTIME_ERRORS:
            pass
        return

    if not viewer.enable_chat_item_tracking:
        return

    match_pickup = viewer.pickup_regex.search(text)
    if not match_pickup:
        return

    player_name = viewer._strip_tags(match_pickup.group(2)).strip() if match_pickup.group(2) else "Unknown"
    quantity_text = match_pickup.group(3)
    color_hex = match_pickup.group(4)
    item_name = viewer._clean_item_name(match_pickup.group(5) if match_pickup.group(5) else "Unknown Item")

    quantity = 1
    if quantity_text and quantity_text.isdigit():
        quantity = int(quantity_text)

    rarity = viewer._get_rarity_from_color_hex(color_hex) if color_hex else "Unknown"
    if not viewer._is_recent_duplicate(player_name, item_name, quantity, text):
        viewer._log_drop_to_file(player_name, item_name, quantity, rarity)
        viewer.last_tracked_item_name = item_name
        viewer.last_tracked_item_quantity = int(quantity)
        viewer.last_tracked_item_rarity = rarity
        viewer.last_tracked_item_player = player_name
        viewer.last_tracked_item_source = "chat"
        viewer.last_tracked_item_at = time.time()
        if py4gw_api is not None:
            py4gw_api.Console.Log(
                "DropViewer",
                f"TRACKED CHAT: {item_name} x{quantity} ({rarity}) [{player_name}]",
                py4gw_api.Console.MessageType.Info,
            )


def run_update_tick(viewer) -> None:
    player_api = _runtime_attr(viewer, "Player", None)
    read_current_map_instance_fn = _runtime_attr(viewer, "read_current_map_instance", None)
    classify_map_instance_transition_fn = _runtime_attr(viewer, "classify_map_instance_transition", None)

    now = time.time()
    if now - viewer.last_update_time < 0.5:
        return
    viewer.last_update_time = now

    try:
        viewer._process_pending_identify_mod_capture()

        if viewer.config_poll_timer.IsExpired():
            viewer.config_poll_timer.Reset()
            if viewer.runtime_config_dirty:
                viewer._flush_runtime_config_if_dirty()
            else:
                viewer._load_runtime_config()

        if viewer.paused:
            return

        current_map_id = 0
        current_instance_uptime_ms = 0
        try:
            if read_current_map_instance_fn is not None:
                current_map_id, current_instance_uptime_ms = read_current_map_instance_fn()
        except EXPECTED_RUNTIME_ERRORS:
            current_map_id = 0
            current_instance_uptime_ms = 0

        if current_map_id > 0:
            prev_watch_map_id = max(0, viewer._safe_int(getattr(viewer, "map_watch_last_map_id", 0), 0))
            prev_watch_uptime_ms = max(0, viewer._safe_int(getattr(viewer, "map_watch_last_instance_uptime_ms", 0), 0))
            if prev_watch_map_id <= 0:
                viewer._log_map_watch(f"MAP WATCH first_sample map={current_map_id} uptime_ms={current_instance_uptime_ms}")
            elif current_map_id != prev_watch_map_id:
                viewer._log_map_watch(
                    f"MAP WATCH map_change map={prev_watch_map_id}->{current_map_id} uptime_ms={prev_watch_uptime_ms}->{current_instance_uptime_ms}"
                )
            elif (
                prev_watch_uptime_ms > 0
                and current_instance_uptime_ms > 0
                and current_instance_uptime_ms + 500 < prev_watch_uptime_ms
            ):
                viewer._log_map_watch(
                    f"MAP WATCH uptime_rollback map={current_map_id} uptime_ms={prev_watch_uptime_ms}->{current_instance_uptime_ms}"
                )
            viewer.map_watch_last_map_id = current_map_id
            viewer.map_watch_last_instance_uptime_ms = current_instance_uptime_ms

        if current_map_id > 0:
            if viewer.last_seen_map_id <= 0:
                viewer.last_seen_map_id = current_map_id
                viewer.last_seen_instance_uptime_ms = current_instance_uptime_ms
            else:
                transition_reason = None
                if classify_map_instance_transition_fn is not None:
                    transition_reason = classify_map_instance_transition_fn(
                        previous_map_id=viewer.last_seen_map_id,
                        previous_instance_uptime_ms=viewer.last_seen_instance_uptime_ms,
                        current_map_id=current_map_id,
                        current_instance_uptime_ms=current_instance_uptime_ms,
                    )
                if transition_reason:
                    if _should_coalesce_viewer_reset(
                        viewer,
                        "viewer_instance_reset",
                        current_map_id,
                        current_instance_uptime_ms,
                    ):
                        return
                    viewer._begin_new_explorable_session("viewer_instance_reset", current_map_id, current_instance_uptime_ms)
                    return
                viewer.last_seen_instance_uptime_ms = current_instance_uptime_ms

        viewer._process_pending_identify_responses()
        viewer._run_auto_inventory_actions_tick()
        viewer._refresh_auto_inventory_pending_counts()
        viewer._poll_shared_memory()
        viewer._run_auto_conset_tick()

        if viewer.player_name == "Unknown" and player_api is not None:
            try:
                viewer.player_name = player_api.GetName()
            except EXPECTED_RUNTIME_ERRORS:
                pass

        if player_api is None:
            return

        if not viewer.chat_requested:
            player_api.player_instance().RequestChatHistory()
            viewer.chat_requested = True
            return

        if not player_api.IsChatHistoryReady():
            return

        chat_history = player_api.GetChatHistory()
        viewer.chat_requested = False
        if not chat_history:
            return

        current_len = len(chat_history)
        if viewer.last_chat_index < 0:
            viewer.last_chat_index = current_len
            return

        if current_len < viewer.last_chat_index:
            viewer.last_chat_index = 0

        new_messages = []
        if current_len > viewer.last_chat_index:
            new_messages = chat_history[viewer.last_chat_index:]
            viewer.last_chat_index = current_len

        for msg in new_messages:
            process_chat_message(viewer, msg)

    except EXPECTED_RUNTIME_ERRORS as e:
        _log_update_error(viewer, f"Update error: {e}")
