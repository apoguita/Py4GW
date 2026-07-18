import time

from Py4GWCoreLib import GWContext, PyImGui, UIManager
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "DevText Trim Test"
SCRIPT_REVISION = "2026-03-07-devtext-trim-boundary-test-1"
WINDOW_OPEN = True
REVISION_LOGGED = False

FRAME_LABEL = "PyDevTextTrimTest"
TARGET_X = 0.0
TARGET_Y = 0.0
TARGET_WIDTH = 180.0
TARGET_HEIGHT = 220.0
TARGET_FLAGS = 0x6
READ_DELAY_SECONDS = 0.50

PENDING_REPORTS: list[tuple[float, str]] = []
LAST_STATUS = "idle"


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _schedule_report(prefix: str, delay_seconds: float | None = None) -> None:
    delay = READ_DELAY_SECONDS if delay_seconds is None else max(0.0, float(delay_seconds))
    PENDING_REPORTS.append((time.time() + delay, prefix))
    _log(f"scheduled report prefix='{prefix}' delay={delay:.2f}s")


def _process_pending_reports() -> None:
    if not PENDING_REPORTS:
        return
    now = time.time()
    ready: list[tuple[float, str]] = []
    pending: list[tuple[float, str]] = []
    for scheduled_at, prefix in PENDING_REPORTS:
        if scheduled_at <= now:
            ready.append((scheduled_at, prefix))
        else:
            pending.append((scheduled_at, prefix))
    PENDING_REPORTS[:] = pending
    for _, prefix in ready:
        _dump_trim_state(prefix)


def _get_viewport_height() -> float:
    root_frame_id = UIManager.GetRootFrameID()
    _, viewport_height = UIManager.GetViewportDimensions(root_frame_id)
    return float(viewport_height)


def _to_engine_y_from_top(y_from_top: float, height: float) -> float:
    return _get_viewport_height() - float(y_from_top) - float(height)


def _frame_exists(frame_id: int) -> bool:
    if frame_id <= 0:
        return False
    try:
        return int(frame_id) in set(int(fid) for fid in UIManager.GetFrameArray())
    except Exception:
        return False


def _find_window() -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(FRAME_LABEL) or 0)
    if frame_id > 0 and _frame_exists(frame_id):
        return frame_id
    return 0


def _frame_summary(frame_id: int) -> str:
    if frame_id <= 0:
        return "frame_id=0"
    try:
        frame = UIManager.GetFrameByID(frame_id)
        left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
        return (
            f"frame_id={frame_id} "
            f"parent_id={int(frame.parent_id)} "
            f"child_offset_id={int(frame.child_offset_id)} "
            f"is_created={bool(frame.is_created)} "
            f"is_visible={bool(frame.is_visible)} "
            f"frame_state=0x{int(frame.frame_state):X} "
            f"rect=({left},{top})-({right},{bottom})"
        )
    except Exception as exc:
        return f"frame_id={frame_id} summary_error={exc}"


def _child_count(frame_id: int) -> int:
    if frame_id <= 0:
        return 0
    try:
        return len(UIManager.GetChildFrameIDs(frame_id))
    except Exception:
        return 0


def _safe_child(frame_id: int, child_offset: int) -> int:
    if frame_id <= 0:
        return 0
    return int(UIManager.GetChildFrameByFrameId(frame_id, child_offset) or 0)


def _dump_frame_fields(frame_id: int, name: str) -> None:
    if frame_id <= 0:
        _log(f"{name} frame_id=0")
        return
    try:
        frame = UIManager.GetFrameByID(frame_id)
        left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
        context_ptr = int(UIManager.GetFrameContext(frame_id) or 0)
        _log(
            f"{name} "
            f"frame_id={frame_id} "
            f"parent_id={int(frame.parent_id)} "
            f"child_offset_id={int(frame.child_offset_id)} "
            f"type=0x{int(frame.type):X} "
            f"template_type={int(frame.template_type)} "
            f"layout=0x{int(frame.frame_layout):X} "
            f"visibility_flags=0x{int(frame.visibility_flags):X} "
            f"frame_state=0x{int(frame.frame_state):X} "
            f"rect=({left},{top})-({right},{bottom}) "
            f"context=0x{context_ptr:X} "
            f"children={_child_count(frame_id)} "
            f"callbacks={len(frame.frame_callbacks)}"
        )
        for index, callback in enumerate(frame.frame_callbacks):
            callback_addr = int(getattr(callback, "callback_address", 0) or 0)
            callback_ctx = int(getattr(callback, "uictl_context", 0) or 0)
            callback_h0008 = int(getattr(callback, "h0008", 0) or 0)
            _log(
                f"{name} callback[{index}] "
                f"addr=0x{callback_addr:X} "
                f"uictl_context=0x{callback_ctx:X} "
                f"h0008=0x{callback_h0008:X}"
            )
    except Exception as exc:
        _log(f"{name} frame_id={frame_id} dump_error={exc}")


def _dump_trim_state(prefix: str) -> None:
    root_id = _find_window()
    child0 = _safe_child(root_id, 0)
    child0_0 = _safe_child(child0, 0)
    child0_0_0 = _safe_child(child0_0, 0)
    child0_3 = _safe_child(child0, 3)
    host_id = int(GWUI.ResolveObservedContentHostByFrameId(root_id) or 0)
    host_0 = _safe_child(host_id, 0)
    host_1 = _safe_child(host_id, 1)
    host_2 = _safe_child(host_id, 2)
    host_3 = _safe_child(host_id, 3)

    _log(f"{prefix} begin")
    _log(f"{prefix} root=({_frame_summary(root_id)})")
    _log(f"{prefix} root[0]=({_frame_summary(child0)})")
    _log(f"{prefix} root[0][0]=({_frame_summary(child0_0)})")
    _log(f"{prefix} root[0][0][0]=({_frame_summary(child0_0_0)})")
    _log(f"{prefix} root[0][3]=({_frame_summary(child0_3)})")
    _log(f"{prefix} resolved_host=({_frame_summary(host_id)})")
    _log(f"{prefix} host[0]=({_frame_summary(host_0)})")
    _log(f"{prefix} host[1]=({_frame_summary(host_1)})")
    _log(f"{prefix} host[2]=({_frame_summary(host_2)})")
    _log(f"{prefix} host[3]=({_frame_summary(host_3)})")

    _dump_frame_fields(root_id, f"{prefix}:root")
    _dump_frame_fields(child0, f"{prefix}:root[0]")
    _dump_frame_fields(child0_0, f"{prefix}:root[0][0]")
    _dump_frame_fields(child0_0_0, f"{prefix}:root[0][0][0]")
    _dump_frame_fields(child0_3, f"{prefix}:root[0][3]")
    if host_id not in {0, child0_0_0}:
        _dump_frame_fields(host_id, f"{prefix}:host")
    _dump_frame_fields(host_0, f"{prefix}:host[0]")
    _dump_frame_fields(host_1, f"{prefix}:host[1]")
    _dump_frame_fields(host_2, f"{prefix}:host[2]")
    _dump_frame_fields(host_3, f"{prefix}:host[3]")
    _log(f"{prefix} end")


def _create_raw_window() -> None:
    global LAST_STATUS
    existing = _find_window()
    if existing > 0:
        LAST_STATUS = f"window exists frame_id={existing}"
        _log(LAST_STATUS)
        return

    char_ctx = GWContext.Char.GetContext()
    if char_ctx is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    frame_id = int(
        GWUI.CreateWindowClone(
            TARGET_X,
            engine_y,
            TARGET_WIDTH,
            TARGET_HEIGHT,
            frame_label=FRAME_LABEL,
            parent_frame_id=9,
            child_index=0,
            frame_flags=0,
            create_param=0,
            frame_callback=0,
            anchor_flags=TARGET_FLAGS,
            ensure_devtext_source=True,
        )
        or 0
    )
    LAST_STATUS = f"created raw frame_id={frame_id}"
    _log(
        f"created raw window frame_id={frame_id} "
        f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT})"
    )
    _schedule_report("state after raw create")


def _clear_by_root() -> None:
    global LAST_STATUS
    root_id = _find_window()
    if root_id <= 0:
        LAST_STATUS = "window missing"
        _log(LAST_STATUS)
        return
    result = bool(GWUI.ClearWindowContentsByFrameId(root_id))
    LAST_STATUS = f"clear by root result={result}"
    _log(f"clear by root root={root_id} result={result}")
    _schedule_report("state after clear by root")


def _clear_target(frame_id: int, target_name: str) -> None:
    global LAST_STATUS
    if frame_id <= 0:
        LAST_STATUS = f"{target_name} missing"
        _log(LAST_STATUS)
        return
    result = bool(GWUI.ClearFrameChildrenRecursiveByFrameId(frame_id))
    LAST_STATUS = f"clear {target_name} result={result}"
    _log(f"clear {target_name} frame={frame_id} result={result}")
    _schedule_report(f"state after clear {target_name}")


def _clear_by_parent_of_host() -> None:
    root_id = _find_window()
    child0 = _safe_child(root_id, 0)
    child0_0 = _safe_child(child0, 0)
    _clear_target(child0_0, "root[0][0]")


def _clear_by_host() -> None:
    root_id = _find_window()
    host_id = int(GWUI.ResolveObservedContentHostByFrameId(root_id) or 0)
    _clear_target(host_id, "host")


def _clear_by_host_child0() -> None:
    root_id = _find_window()
    host_id = int(GWUI.ResolveObservedContentHostByFrameId(root_id) or 0)
    _clear_target(_safe_child(host_id, 0), "host[0]")


def _log_startup() -> None:
    global REVISION_LOGGED
    if REVISION_LOGGED:
        return
    REVISION_LOGGED = True
    _log(f"script revision={SCRIPT_REVISION}")
    _log("test flow:")
    _log("1) click 'Create Raw Window'")
    _log("2) wait for 'state after raw create'")
    _log("3) click 'Dump Current Structure'")
    _log("4) try one clear target: 'Clear By Root', 'Clear root[0][0]', 'Clear Host', or 'Clear Host[0]'")
    _log("5) wait for the delayed state report")
    _log("6) click 'Dump Current Structure' again")
    _log("this tests which clear boundary is low enough to preserve window chrome")


def main() -> None:
    global WINDOW_OPEN
    global TARGET_X
    global TARGET_Y
    global TARGET_WIDTH
    global TARGET_HEIGHT
    global READ_DELAY_SECONDS

    _log_startup()
    _process_pending_reports()

    if not WINDOW_OPEN:
        return

    if PyImGui.begin(MODULE_NAME):
        TARGET_X = PyImGui.input_float("X", TARGET_X)
        TARGET_Y = PyImGui.input_float("Y From Top", TARGET_Y)
        TARGET_WIDTH = PyImGui.input_float("Width", TARGET_WIDTH)
        TARGET_HEIGHT = PyImGui.input_float("Height", TARGET_HEIGHT)
        READ_DELAY_SECONDS = PyImGui.input_float("Read Delay Seconds", READ_DELAY_SECONDS)

        PyImGui.text("Create raw clone -> dump -> try one clear target -> dump again")

        if PyImGui.button("Create Raw Window"):
            _create_raw_window()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Clear By Root"):
            _clear_by_root()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Clear root[0][0]"):
            _clear_by_parent_of_host()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Clear Host"):
            _clear_by_host()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Clear Host[0]"):
            _clear_by_host_child0()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Dump Current Structure"):
            _dump_trim_state("manual dump")

        PyImGui.separator()
        PyImGui.text(f"Label: {FRAME_LABEL}")
        PyImGui.text(f"Status: {LAST_STATUS}")

    PyImGui.end()


if __name__ == "__main__":
    main()
