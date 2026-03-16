import ctypes
import time

import Py4GW
import PyImGui

from Py4GWCoreLib import GWContext, UIManager
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "Hosted FrameList Probe Test"
SCRIPT_REVISION = "2026-03-10-hosted-frame-list-probe-1"
WINDOW_OPEN = True
INITIALIZED = False

WINDOW_LABEL = "Py4GW_Hosted_FrameList_Window"
WINDOW_TITLE = "Py4GW Hosted FrameList"
HOST_LABEL = "Py4GW_Hosted_FrameList_Host"

TARGET_X = 140.0
TARGET_Y = 140.0
TARGET_WIDTH = 360.0
TARGET_HEIGHT = 220.0
READ_DELAY_SECONDS = 0.50
TEXT_LABEL_COUNT = 8

STATIC_UI_DEVTEXT_DIALOG_PROC = 0x00864170
STATIC_UI_INIT_SINGLE_TEXT_HOST_PROC = 0x004FA1E0
STATIC_UI_FRAME_LIST_PROC = 0x005F48E0

PENDING_REPORTS: list[tuple[float, str]] = []
PENDING_BUFFERS: list[ctypes.Array] = []
LAST_CREATED_LABEL_IDS: list[int] = []
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


def _frame_exists(frame_id: int) -> bool:
    if frame_id <= 0:
        return False
    try:
        return int(frame_id) in set(int(fid) for fid in UIManager.GetFrameArray())
    except Exception:
        return False


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


def _safe_child(frame_id: int, child_offset: int) -> int:
    if frame_id <= 0:
        return 0
    return int(UIManager.GetChildFrameByFrameId(frame_id, child_offset) or 0)


def _get_viewport_height() -> float:
    root_frame_id = UIManager.GetRootFrameID()
    _, viewport_height = UIManager.GetViewportDimensions(root_frame_id)
    return float(viewport_height)


def _to_engine_y_from_top(y_from_top: float, height: float) -> float:
    return _get_viewport_height() - float(y_from_top) - float(height)


def _current_window() -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(WINDOW_LABEL) or 0)
    if frame_id > 0 and _frame_exists(frame_id):
        return frame_id
    return 0


def _current_content() -> int:
    return int(GWUI.ResolveWindowContentFrameByFrameId(_current_window()) or 0)


def _current_host_root() -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(HOST_LABEL) or 0)
    if frame_id > 0 and _frame_exists(frame_id):
        return frame_id
    return 0


def _current_view_root() -> int:
    return _safe_child(_current_host_root(), 0)


def _current_relay_host() -> int:
    return _safe_child(_current_view_root(), 0)


def _current_terminal() -> int:
    return _safe_child(_current_relay_host(), 0)


def _current_scroll_vertical() -> int:
    return _safe_child(_current_view_root(), 2)


def _current_scroll_horizontal() -> int:
    return _safe_child(_current_view_root(), 3)


def _child_list(frame_id: int, limit: int = 64) -> list[int]:
    children: list[int] = []
    if frame_id <= 0:
        return children
    try:
        current = int(UIManager.GetFirstChildFrameID(frame_id) or 0)
        while current > 0 and len(children) < limit:
            children.append(current)
            current = int(UIManager.GetNextChildFrameID(current) or 0)
    except Exception:
        pass
    return children


def _runtime_slide() -> int:
    live = int(GWUI.ResolveDevTextDialogProc() or 0)
    if live <= 0:
        return 0
    return int(live - STATIC_UI_DEVTEXT_DIALOG_PROC)


def _runtime_proc(static_address: int) -> int:
    slide = _runtime_slide()
    if slide == 0:
        return 0
    return int(static_address + slide)


def _create_empty_window() -> None:
    global LAST_STATUS
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return
    existing = _current_window()
    if existing > 0:
        LAST_STATUS = f"window exists frame_id={existing}"
        _log(LAST_STATUS)
        return

    def _invoke() -> None:
        engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
        frame_id = int(
            GWUI.CreateWindow(
                TARGET_X,
                engine_y,
                TARGET_WIDTH,
                TARGET_HEIGHT,
                frame_label=WINDOW_LABEL,
                window_title=WINDOW_TITLE,
            )
            or 0
        )
        _log(
            f"create window invoke complete frame_id={frame_id} "
            f"label='{WINDOW_LABEL}' title='{WINDOW_TITLE}' "
            f"rect=({TARGET_X},{TARGET_Y},{TARGET_WIDTH},{TARGET_HEIGHT})"
        )

    Py4GW.Game.enqueue(_invoke)
    LAST_STATUS = "create window enqueued"
    _log(
        f"create window enqueued label='{WINDOW_LABEL}' title='{WINDOW_TITLE}' "
        f"rect=({TARGET_X},{TARGET_Y},{TARGET_WIDTH},{TARGET_HEIGHT})"
    )
    _schedule_report("state after create window")


def _insert_hosted_text_host() -> None:
    global LAST_STATUS
    parent_id = _current_content()
    if parent_id <= 0:
        LAST_STATUS = "content_unavailable"
        _log("insert host skipped because content frame is unavailable")
        return

    init_single_text_host_proc = _runtime_proc(STATIC_UI_INIT_SINGLE_TEXT_HOST_PROC)
    if init_single_text_host_proc <= 0:
        LAST_STATUS = "init_single_text_host_proc_unresolved"
        _log("insert host skipped because Ui_InitSingleTextHostProc is unresolved")
        return

    child_slot = int(GWUI.FindAvailableChildSlot(parent_id, 0x20, 0xFE) or 0)
    if child_slot <= 0:
        LAST_STATUS = "child_slot_unresolved"
        _log("insert host skipped because no free child slot was found")
        return

    def _invoke() -> None:
        frame_id = int(
            GWUI.CreateLabeledFrameByFrameId(
                parent_id,
                0,
                child_slot,
                init_single_text_host_proc,
                0,
                HOST_LABEL,
            )
            or 0
        )
        _log(
            f"insert host invoke complete parent={parent_id} child_slot=0x{child_slot:X} "
            f"callback=0x{init_single_text_host_proc:X} frame_id={frame_id}"
        )

    Py4GW.Game.enqueue(_invoke)
    LAST_STATUS = "insert host enqueued"
    _log(
        f"insert host enqueued parent={parent_id} child_slot=0x{child_slot:X} "
        f"callback=0x{init_single_text_host_proc:X} label='{HOST_LABEL}'"
    )
    _schedule_report("state after insert host")


def _replace_terminal_with_frame_list() -> None:
    global LAST_STATUS
    view_root = _current_view_root()
    if view_root <= 0:
        LAST_STATUS = "view_root_unavailable"
        _log("replace terminal skipped because view root is unavailable")
        return

    frame_list_proc = _runtime_proc(STATIC_UI_FRAME_LIST_PROC)
    if frame_list_proc <= 0:
        LAST_STATUS = "frame_list_proc_unresolved"
        _log("replace terminal skipped because Ui_FrameListProc is unresolved")
        return

    payload = (ctypes.c_uint32 * 3)(0, frame_list_proc, 0)
    payload_address = ctypes.addressof(payload)
    PENDING_BUFFERS.append(payload)

    def _invoke() -> None:
        UIManager.SendFrameUIMessage(view_root, 0x7FFFFFF5, payload_address, 0)
        host_root = _current_host_root()
        relay = _current_relay_host()
        terminal = _current_terminal()
        if terminal > 0:
            GWUI.TriggerFrameRedrawByFrameId(terminal)
        if relay > 0:
            GWUI.TriggerFrameRedrawByFrameId(relay)
        GWUI.TriggerFrameRedrawByFrameId(view_root)
        if host_root > 0:
            GWUI.TriggerFrameRedrawByFrameId(host_root)
        window = _current_window()
        if window > 0:
            GWUI.TriggerFrameRedrawByFrameId(window)
        _log(
            f"replace terminal invoke complete view_root={view_root} message=0x7FFFFFF5 "
            f"payload=0x{payload_address:X} terminal_proc=0x{frame_list_proc:X} "
            f"relay={relay} terminal={terminal}"
        )

    Py4GW.Game.enqueue(_invoke)
    LAST_STATUS = "replace terminal enqueued"
    _log(
        f"replace terminal enqueued view_root={view_root} message=0x7FFFFFF5 "
        f"payload=0x{payload_address:X} terminal_proc=0x{frame_list_proc:X}"
    )
    _schedule_report("state after replace terminal")


def _insert_text_labels() -> None:
    global LAST_CREATED_LABEL_IDS
    global LAST_STATUS
    terminal = _current_terminal()
    if terminal <= 0:
        LAST_STATUS = "terminal_unavailable"
        _log("insert text labels skipped because terminal child is unavailable")
        return

    count = max(1, int(TEXT_LABEL_COUNT))
    LAST_CREATED_LABEL_IDS = []

    def _invoke() -> None:
        global LAST_CREATED_LABEL_IDS
        created: list[int] = []
        for index in range(count):
            child_slot = 0x20 + index
            frame_id = int(
                GWUI.CreateTextLabel(
                    terminal,
                    f"Hosted Item {index + 1}",
                    component_label=f"Py4GW_Hosted_FrameList_Item_{index + 1}",
                    child_index=child_slot,
                    component_flags=0x300,
                )
                or 0
            )
            if frame_id > 0:
                created.append(frame_id)
        LAST_CREATED_LABEL_IDS = created
        if terminal > 0:
            GWUI.TriggerFrameRedrawByFrameId(terminal)
        relay = _current_relay_host()
        if relay > 0:
            GWUI.TriggerFrameRedrawByFrameId(relay)
        view_root = _current_view_root()
        if view_root > 0:
            GWUI.TriggerFrameRedrawByFrameId(view_root)
        host_root = _current_host_root()
        if host_root > 0:
            GWUI.TriggerFrameRedrawByFrameId(host_root)
        window = _current_window()
        if window > 0:
            GWUI.TriggerFrameRedrawByFrameId(window)
        _log(
            f"insert text labels invoke complete terminal={terminal} "
            f"count={count} created={created}"
        )

    Py4GW.Game.enqueue(_invoke)
    LAST_STATUS = "insert text labels enqueued"
    _log(f"insert text labels enqueued terminal={terminal} count={count}")
    _schedule_report("state after insert text labels")


def _dump_state(prefix: str) -> None:
    window = _current_window()
    content = _current_content()
    host_root = _current_host_root()
    view_root = _current_view_root()
    relay = _current_relay_host()
    terminal = _current_terminal()
    scroll_vertical = _current_scroll_vertical()
    scroll_horizontal = _current_scroll_horizontal()
    page_children = _child_list(terminal)
    _log(
        f"{prefix} "
        f"window=({_frame_summary(window)}) "
        f"content=({_frame_summary(content)}) "
        f"host_root=({_frame_summary(host_root)}) "
        f"view_root=({_frame_summary(view_root)}) "
        f"relay=({_frame_summary(relay)}) "
        f"terminal=({_frame_summary(terminal)}) "
        f"scroll_v=({_frame_summary(scroll_vertical)}) "
        f"scroll_h=({_frame_summary(scroll_horizontal)}) "
        f"terminal_children={page_children} "
        f"last_text_labels={LAST_CREATED_LABEL_IDS}"
    )


def _draw_window() -> None:
    global WINDOW_OPEN
    global READ_DELAY_SECONDS
    global TEXT_LABEL_COUNT

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("goal: validate the hosted Ui_FrameListProc chain from Python before any C++ changes")
    PyImGui.separator()
    PyImGui.text("exact steps:")
    PyImGui.text("1) Create Empty Window")
    PyImGui.text("2) Insert Hosted Text Host")
    PyImGui.text("3) Replace Terminal With FrameList")
    PyImGui.text("4) Insert Text Labels")
    PyImGui.text("5) Dump State")
    PyImGui.separator()

    READ_DELAY_SECONDS = float(
        _normalize_input_int(
            PyImGui.input_int("Read Delay (ms)", int(READ_DELAY_SECONDS * 1000.0)),
            int(READ_DELAY_SECONDS * 1000.0),
        )
    ) / 1000.0
    if READ_DELAY_SECONDS < 0.05:
        READ_DELAY_SECONDS = 0.05

    TEXT_LABEL_COUNT = _normalize_input_int(PyImGui.input_int("Text Label Count", TEXT_LABEL_COUNT), TEXT_LABEL_COUNT)
    if TEXT_LABEL_COUNT < 1:
        TEXT_LABEL_COUNT = 1

    if PyImGui.button("Create Empty Window"):
        _create_empty_window()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Insert Hosted Text Host"):
        _insert_hosted_text_host()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Replace Terminal With FrameList"):
        _replace_terminal_with_frame_list()

    if PyImGui.button("Insert Text Labels"):
        _insert_text_labels()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Dump State"):
        _dump_state("manual state")

    PyImGui.separator()
    PyImGui.text(f"runtime_slide=0x{_runtime_slide():X}")
    PyImGui.text(f"init_single_text_host_proc=0x{_runtime_proc(STATIC_UI_INIT_SINGLE_TEXT_HOST_PROC):X}")
    PyImGui.text(f"frame_list_proc=0x{_runtime_proc(STATIC_UI_FRAME_LIST_PROC):X}")
    PyImGui.text(f"current_window={_current_window()}")
    PyImGui.text(f"current_content={_current_content()}")
    PyImGui.text(f"current_host_root={_current_host_root()}")
    PyImGui.text(f"current_view_root={_current_view_root()}")
    PyImGui.text(f"current_relay={_current_relay_host()}")
    PyImGui.text(f"current_terminal={_current_terminal()}")
    PyImGui.text(f"current_scroll_v={_current_scroll_vertical()}")
    PyImGui.text(f"current_scroll_h={_current_scroll_horizontal()}")
    PyImGui.text(f"last_status={LAST_STATUS}")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("goal: validate a hosted Ui_FrameListProc chain using only Python-side creation and messages")
        _log("flow: create empty window, insert Ui_InitSingleTextHostProc host, reseed its terminal child to Ui_FrameListProc, then add labels")
    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
