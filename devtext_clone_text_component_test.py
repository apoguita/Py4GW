import ctypes
import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "DevText Clone Text Component Test"
SCRIPT_REVISION = "2026-03-07-devtext-clone-text-component-test-6"
WINDOW_OPEN = True
INITIALIZED = False

READ_DELAY_SECONDS = 0.50
CLONE_LABEL = "PyDevTextRawComponentClone"
CREATED_FRAME_ID = 0
PENDING_REPORTS: list[tuple[float, str]] = []
PENDING_BUFFERS: list[ctypes.Array] = []

UI_MULTI_LINE_TEXT_CONTROL_PROC = 0x005EA970
INITIAL_TEXT = ctypes.create_unicode_buffer("Py4GW Inserted Text")
UPDATED_TEXT = ctypes.create_unicode_buffer("Py4GW Updated Text")


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
        _dump_state(prefix)


def _normalize_input_int(result, current: int) -> int:
    if isinstance(result, tuple):
        if len(result) >= 2:
            return int(result[1])
        if len(result) == 1:
            return int(result[0])
    if result is None:
        return int(current)
    return int(result)


def _frame_summary(frame_id: int) -> str:
    frame_id = int(frame_id or 0)
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


def _dump_callbacks(prefix: str, frame_id: int) -> None:
    frame_id = int(frame_id or 0)
    if frame_id <= 0:
        _log(f"{prefix} frame_id=0")
        return
    try:
        frame = UIManager.GetFrameByID(frame_id)
        _log(f"{prefix} callbacks={len(frame.frame_callbacks)}")
        for index, callback in enumerate(frame.frame_callbacks):
            callback_addr = int(getattr(callback, "callback_address", 0) or 0)
            callback_h0008 = int(getattr(callback, "h0008", 0) or 0)
            callback_ctx = int(getattr(callback, "uictl_context", 0) or 0)
            _log(
                f"{prefix} callback[{index}] "
                f"addr=0x{callback_addr:X} "
                f"h0008=0x{callback_h0008:X} "
                f"uictl_context=0x{callback_ctx:X}"
            )
    except Exception as exc:
        _log(f"{prefix} callback_dump_error={exc}")


def _current_clone_root() -> int:
    return int(UIManager.GetFrameIDByLabel(CLONE_LABEL) or 0)


def _current_clone_host() -> int:
    root = _current_clone_root()
    if root <= 0:
        return 0
    return int(UIManager.GetChildFramePathByFrameId(root, [0, 0, 0]) or 0)


def _current_view_root() -> int:
    host = _current_clone_host()
    if host <= 0:
        return 0
    try:
        return int(UIManager.GetParentID(host) or 0)
    except Exception:
        return 0


def _current_source_child() -> int:
    host = _current_clone_host()
    if host <= 0:
        return 0
    return int(UIManager.GetChildFrameByFrameId(host, 0) or 0)


def _current_created_child() -> int:
    if CREATED_FRAME_ID > 0:
        return int(CREATED_FRAME_ID)
    view_root = _current_view_root()
    if view_root <= 0:
        return 0
    return int(UIManager.GetChildFrameByFrameId(view_root, 1) or 0)


def _find_first_free_child_offset(parent_id: int, start: int = 1, end: int = 0xFF) -> int:
    if parent_id <= 0:
        return 0
    for child_offset in range(start, end + 1):
        if int(UIManager.GetChildFrameByFrameId(parent_id, child_offset) or 0) <= 0:
            return child_offset
    return 0


def _source_callbacks() -> list[tuple[int, int]]:
    frame_id = _current_source_child()
    if frame_id <= 0:
        return []
    try:
        frame = UIManager.GetFrameByID(frame_id)
        entries: list[tuple[int, int]] = []
        for callback in frame.frame_callbacks:
            callback_addr = int(getattr(callback, "callback_address", 0) or 0)
            callback_h0008 = int(getattr(callback, "h0008", 0) or 0)
            if callback_addr > 0:
                entries.append((callback_addr, callback_h0008))
        return entries
    except Exception:
        return []


def _dump_state(prefix: str) -> None:
    root = _current_clone_root()
    view_root = _current_view_root()
    host = _current_clone_host()
    current = _current_source_child()
    _log(
        f"{prefix} "
        f"clone_root=({_frame_summary(root)}) "
        f"view_root=({_frame_summary(view_root)}) "
        f"host=({_frame_summary(host)}) "
        f"current_element=({_frame_summary(current)})"
    )
    _dump_callbacks(f"{prefix} current_element", current)


def _create_raw_clone() -> None:
    global CREATED_FRAME_ID
    CREATED_FRAME_ID = 0

    def _invoke() -> None:
        GWUI.CreateWindow(
            0.0,
            0.0,
            180.0,
            220.0,
            frame_label=CLONE_LABEL,
        )

    Py4GW.Game.enqueue(_invoke)
    _log(f"create raw clone enqueued label='{CLONE_LABEL}'")
    _schedule_report("state after create raw clone")


def _create_component_clone() -> None:
    global CREATED_FRAME_ID
    view_root = _current_view_root()
    if view_root <= 0:
        _log("create component skipped because DevText view root is unavailable")
        return

    payload = (ctypes.c_uint32 * 3)(
        0,
        UI_MULTI_LINE_TEXT_CONTROL_PROC,
        ctypes.addressof(INITIAL_TEXT),
    )
    payload_address = ctypes.addressof(payload)
    PENDING_BUFFERS.append(payload)

    def _invoke() -> None:
        global CREATED_FRAME_ID
        UIManager.SendFrameUIMessage(view_root, 0x7FFFFFF5, payload_address, 0)
        host = _current_clone_host()
        CREATED_FRAME_ID = int(UIManager.GetChildFrameByFrameId(host, 0) or 0) if host > 0 else 0
        if CREATED_FRAME_ID > 0:
            GWUI.TriggerFrameRedrawByFrameId(CREATED_FRAME_ID)
        GWUI.TriggerFrameRedrawByFrameId(view_root)
        clone_root = _current_clone_root()
        if clone_root > 0:
            GWUI.TriggerFrameRedrawByFrameId(clone_root)

    Py4GW.Game.enqueue(_invoke)
    _log(
        f"create component enqueued view_root={view_root} "
        f"message=0x7FFFFFF5 flags=0x0 proc=0x{UI_MULTI_LINE_TEXT_CONTROL_PROC:X} "
        f"create_param=0x{ctypes.addressof(INITIAL_TEXT):X} text='{INITIAL_TEXT.value}' "
        f"payload=0x{payload_address:X}"
    )
    _schedule_report("state after create component")


def _update_current_element_text() -> None:
    target = _current_source_child()
    if target <= 0:
        _log("update text skipped because current element is unavailable")
        return

    def _invoke() -> None:
        UIManager.SendFrameUIMessage(target, 0x62, ctypes.addressof(UPDATED_TEXT), 0)
        GWUI.TriggerFrameRedrawByFrameId(target)
        host = _current_clone_host()
        if host > 0:
            GWUI.TriggerFrameRedrawByFrameId(host)
        clone_root = _current_clone_root()
        if clone_root > 0:
            GWUI.TriggerFrameRedrawByFrameId(clone_root)

    Py4GW.Game.enqueue(_invoke)
    _log(
        f"update text enqueued target={target} message=0x62 "
        f"text=0x{ctypes.addressof(UPDATED_TEXT):X} value='{UPDATED_TEXT.value}'"
    )
    _schedule_report("state after update text")


def _draw_window() -> None:
    global WINDOW_OPEN
    global READ_DELAY_SECONDS

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("goal: test DevText multiline element replacement and text update")
    PyImGui.separator()
    PyImGui.text("flow:")
    PyImGui.text("1) Create Raw Clone")
    PyImGui.text("2) Replace Host Element")
    PyImGui.text("3) Update Current Element Text")
    PyImGui.text("4) Dump State")
    PyImGui.separator()

    READ_DELAY_SECONDS = float(
        _normalize_input_int(
            PyImGui.input_int("Read Delay (ms)", int(READ_DELAY_SECONDS * 1000.0)),
            int(READ_DELAY_SECONDS * 1000.0),
        )
    ) / 1000.0

    if PyImGui.button("Create Raw Clone"):
        _create_raw_clone()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Replace Host Element"):
        _create_component_clone()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Update Current Element Text"):
        _update_current_element_text()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Dump State"):
        _dump_state("manual state report")

    PyImGui.separator()
    PyImGui.text(f"clone_root={_current_clone_root()}")
    PyImGui.text(f"view_root={_current_view_root()}")
    PyImGui.text(f"clone_host={_current_clone_host()}")
    PyImGui.text(f"current_element={_current_source_child()}")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("test flow:")
        _log("1) click 'Create Raw Clone'")
        _log("2) wait for 'state after create raw clone'")
        _log("3) click 'Create Component Clone'")
        _log("4) wait for 'state after create component'")
        _log("5) click 'Dump State'")
    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
