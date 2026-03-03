import sys
import time


EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


def _runtime_module(viewer):
    try:
        return sys.modules.get(viewer.__class__.__module__)
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _runtime_attr(viewer, name: str, default=None):
    module = _runtime_module(viewer)
    if module is not None and hasattr(module, name):
        return getattr(module, name)
    return default


def set_status(viewer, msg):
    viewer.status_message = msg
    viewer.status_time = time.time()


def set_paused(viewer, paused: bool):
    player = _runtime_attr(viewer, "Player")
    expected_errors = _runtime_attr(viewer, "EXPECTED_RUNTIME_ERRORS", EXPECTED_RUNTIME_ERRORS)

    next_state = bool(paused)
    if bool(viewer.paused) == next_state:
        return
    viewer.paused = next_state
    # Avoid replaying stale chat lines when transitioning tracking state.
    viewer.chat_requested = False
    if not viewer.paused:
        viewer.last_chat_index = -1
        try:
            if player.IsChatHistoryReady():
                viewer.last_chat_index = len(player.GetChatHistory())
        except expected_errors:
            viewer.last_chat_index = -1


def toggle_follower_inventory_viewer(viewer):
    get_widget_handler = _runtime_attr(viewer, "get_widget_handler")
    expected_errors = _runtime_attr(viewer, "EXPECTED_RUNTIME_ERRORS", EXPECTED_RUNTIME_ERRORS)

    try:
        widget_handler = get_widget_handler()
        widget_info = widget_handler.get_widget_info("TeamInventoryViewer")
        if widget_info is None:
            viewer.set_status("TeamInventoryViewer widget not found")
            return
        if widget_handler.is_widget_enabled("TeamInventoryViewer"):
            widget_handler.disable_widget("TeamInventoryViewer")
            viewer.set_status("Closed Follower Inventory viewer")
        else:
            widget_handler.enable_widget("TeamInventoryViewer")
            viewer.set_status("Opened Follower Inventory viewer")
    except expected_errors as e:
        viewer.set_status(f"Failed to toggle Follower Inventory: {e}")


def send_tracker_ack(viewer, receiver_email: str, event_id: str) -> bool:
    player = _runtime_attr(viewer, "Player")
    global_cache = _runtime_attr(viewer, "GLOBAL_CACHE")
    shared_command_type = _runtime_attr(viewer, "SharedCommandType")
    expected_errors = _runtime_attr(viewer, "EXPECTED_RUNTIME_ERRORS", EXPECTED_RUNTIME_ERRORS)

    if not viewer.send_tracker_ack_enabled:
        return False
    event_id_text = (event_id or "").strip()
    if not receiver_email or not event_id_text:
        return False
    try:
        my_email = player.GetAccountEmail()
        if not my_email:
            return False
        sent_index = global_cache.ShMem.SendMessage(
            sender_email=my_email,
            receiver_email=receiver_email,
            command=shared_command_type.CustomBehaviors,
            params=(0.0, 0.0, 0.0, 0.0),
            ExtraData=("TrackerAckV2", event_id_text[:31], "", ""),
        )
        if sent_index != -1:
            viewer.last_ack_sent += 1
        return sent_index != -1
    except expected_errors:
        return False


def get_rarity_color(_viewer, rarity):
    col = (1.0, 1.0, 1.0, 1.0)

    if rarity == "Blue":
        col = (0.0, 0.8, 1.0, 1.0)
    elif rarity == "Purple":
        col = (0.8, 0.4, 1.0, 1.0)
    elif rarity == "Gold":
        col = (1.0, 0.84, 0.0, 1.0)
    elif rarity == "Green":
        col = (0.0, 1.0, 0.0, 1.0)
    elif rarity == "Dyes":
        col = (1.0, 0.6, 0.8, 1.0)
    elif rarity == "Keys":
        col = (0.8, 0.8, 0.8, 1.0)
    elif rarity == "Tomes":
        col = (0.0, 0.8, 0.0, 1.0)
    elif rarity == "Currency":
        col = (1.0, 1.0, 0.0, 1.0)
    elif rarity == "Unknown":
        col = (0.5, 0.5, 0.5, 1.0)
    elif rarity == "...":
        col = (0.5, 0.5, 0.5, 1.0)

    return col
