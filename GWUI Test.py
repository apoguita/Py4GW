import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "GWUI End User Test"
SCRIPT_REVISION = "2026-03-09-gwui-end-user-test-1"
WINDOW_OPEN = True
INITIALIZED = False
READ_DELAY_SECONDS = 0.50

DEFAULT_WINDOW_LABEL = "Py4GW_EndUserWindow"
DEFAULT_WINDOW_TITLE = "Py4GW Window"
DEFAULT_TEXT_LABEL = "Hello from GWUI.CreateTextLabel"

WINDOW_LABEL = DEFAULT_WINDOW_LABEL
WINDOW_TITLE = DEFAULT_WINDOW_TITLE
TEXT_LABEL_TEXT = DEFAULT_TEXT_LABEL
TEXT_LABEL_COMPONENT_LABEL = "Py4GW_TextLabel"

WINDOW_X = 140
WINDOW_Y = 140
WINDOW_WIDTH = 360
WINDOW_HEIGHT = 220
WINDOW_FLAGS = 0
WINDOW_PARENT_ID = 9
WINDOW_CHILD_INDEX = 0
WINDOW_ANCHOR_FLAGS = 0x6

RECT_X = 140
RECT_Y = 140
RECT_WIDTH = 360
RECT_HEIGHT = 220
RECT_FLAGS = 0x6

POSITION_X = 140
POSITION_Y = 140
SIZE_WIDTH = 360
SIZE_HEIGHT = 220

TEXT_LABEL_CHILD_INDEX = 0
TEXT_LABEL_FLAGS = 0x300
PENDING_REPORTS: list[tuple[float, str]] = []
LAST_TEXT_LABEL_ID = 0


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _normalize_input_int(result, current: int) -> int:
    if isinstance(result, tuple):
        if len(result) >= 2:
            return int(result[1])
        if len(result) == 1:
            return int(result[0])
    if result is None:
        return int(current)
    return int(result)


def _normalize_input_text(result, current: str) -> str:
    if isinstance(result, tuple):
        if len(result) >= 2:
            return str(result[1])
        if len(result) == 1:
            return str(result[0])
    if result is None:
        return str(current)
    return str(result)


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


def _current_window_id() -> int:
    return int(UIManager.GetFrameIDByLabel(WINDOW_LABEL) or 0)


def _current_window_summary() -> str:
    return _frame_summary(_current_window_id())


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


def _dump_state(prefix: str) -> None:
    window_id = _current_window_id()
    host_id = int(GWUI.ResolveObservedContentHostByFrameId(window_id) or 0) if window_id > 0 else 0
    first_child = int(UIManager.GetFirstChildFrameID(window_id) or 0) if window_id > 0 else 0
    last_child = int(UIManager.GetLastChildFrameID(window_id) or 0) if window_id > 0 else 0
    label = GWUI.GetFrameLabelByFrameId(window_id) if window_id > 0 else ""
    _log(
        f"{prefix} "
        f"window=({_frame_summary(window_id)}) "
        f"host=({_frame_summary(host_id)}) "
        f"first_child={first_child} "
        f"last_child={last_child} "
        f"window_label='{label}' "
        f"last_text_label=({_frame_summary(LAST_TEXT_LABEL_ID)})"
    )


def _create_window() -> None:
    def _invoke() -> None:
        GWUI.CreateWindow(
            float(WINDOW_X),
            float(WINDOW_Y),
            float(WINDOW_WIDTH),
            float(WINDOW_HEIGHT),
            frame_label=WINDOW_LABEL,
            parent_frame_id=int(WINDOW_PARENT_ID),
            child_index=int(WINDOW_CHILD_INDEX),
            frame_flags=int(WINDOW_FLAGS),
            anchor_flags=int(WINDOW_ANCHOR_FLAGS),
            window_title=WINDOW_TITLE,
        )

    Py4GW.Game.enqueue(_invoke)
    _log(
        f"create window enqueued label='{WINDOW_LABEL}' rect=({WINDOW_X},{WINDOW_Y},{WINDOW_WIDTH},{WINDOW_HEIGHT}) "
        f"parent={WINDOW_PARENT_ID} child_index={WINDOW_CHILD_INDEX} flags=0x{WINDOW_FLAGS:X} "
        f"anchor=0x{WINDOW_ANCHOR_FLAGS:X} title='{WINDOW_TITLE}'"
    )
    _schedule_report("state after create window")


def _set_window_title() -> None:
    window_id = _current_window_id()
    if window_id <= 0:
        _log("set window title skipped because current window id is 0")
        return
    applied = bool(GWUI.SetWindowTitle(window_id, WINDOW_TITLE))
    _log(f"set window title invoked window={window_id} title='{WINDOW_TITLE}' applied={applied}")
    _schedule_report("state after set title")


def _create_text_label() -> None:
    global LAST_TEXT_LABEL_ID

    window_id = _current_window_id()
    if window_id <= 0:
        _log("create text label skipped because current window id is 0")
        return
    host_id = int(GWUI.ResolveObservedContentHostByFrameId(window_id) or 0)
    parent_id = host_id if host_id > 0 else window_id

    def _invoke() -> None:
        global LAST_TEXT_LABEL_ID
        LAST_TEXT_LABEL_ID = int(
            GWUI.CreateTextLabel(
                parent_id,
                TEXT_LABEL_TEXT,
                component_label=TEXT_LABEL_COMPONENT_LABEL,
                child_index=int(TEXT_LABEL_CHILD_INDEX),
                component_flags=int(TEXT_LABEL_FLAGS),
            )
            or 0
        )

    Py4GW.Game.enqueue(_invoke)
    _log(
        f"create text label enqueued parent={parent_id} child_index={TEXT_LABEL_CHILD_INDEX} "
        f"flags=0x{TEXT_LABEL_FLAGS:X} text='{TEXT_LABEL_TEXT}' component_label='{TEXT_LABEL_COMPONENT_LABEL}'"
    )
    _schedule_report("state after create text label")




def _set_window_position() -> None:
    window_id = _current_window_id()
    if window_id <= 0:
        _log("set position skipped because current window id is 0")
        return
    applied = bool(
        GWUI.SetFramePosition(
            window_id,
            float(POSITION_X),
            float(POSITION_Y),
            flags=int(RECT_FLAGS),
        )
    )
    _log(
        f"set position invoked window={window_id} x={POSITION_X} y={POSITION_Y} "
        f"flags=0x{RECT_FLAGS:X} applied={applied}"
    )
    _schedule_report("state after set position")


def _set_window_size() -> None:
    window_id = _current_window_id()
    if window_id <= 0:
        _log("set size skipped because current window id is 0")
        return
    applied = bool(
        GWUI.SetFrameSize(
            window_id,
            float(SIZE_WIDTH),
            float(SIZE_HEIGHT),
            flags=int(RECT_FLAGS),
        )
    )
    _log(
        f"set size invoked window={window_id} width={SIZE_WIDTH} height={SIZE_HEIGHT} "
        f"flags=0x{RECT_FLAGS:X} applied={applied}"
    )
    _schedule_report("state after set size")


def _apply_window_rect() -> None:
    window_id = _current_window_id()
    if window_id <= 0:
        _log("apply rect skipped because current window id is 0")
        return
    applied = bool(
        GWUI.ApplyRect(
            window_id,
            float(RECT_X),
            float(RECT_Y),
            float(RECT_WIDTH),
            float(RECT_HEIGHT),
            flags=int(RECT_FLAGS),
        )
    )
    _log(
        f"apply rect invoked window={window_id} rect=({RECT_X},{RECT_Y},{RECT_WIDTH},{RECT_HEIGHT}) "
        f"flags=0x{RECT_FLAGS:X} applied={applied}"
    )
    _schedule_report("state after apply rect")


def _set_visible(is_visible: bool) -> None:
    window_id = _current_window_id()
    if window_id <= 0:
        _log(f"set visible skipped because current window id is 0 target={is_visible}")
        return

    def _invoke() -> None:
        GWUI.SetFrameVisibleByFrameId(window_id, is_visible)

    Py4GW.Game.enqueue(_invoke)
    _log(f"set visible enqueued window={window_id} is_visible={is_visible}")
    _schedule_report(f"state after set visible {is_visible}")


def _set_disabled(is_disabled: bool) -> None:
    window_id = _current_window_id()
    if window_id <= 0:
        _log(f"set disabled skipped because current window id is 0 target={is_disabled}")
        return

    def _invoke() -> None:
        GWUI.SetFrameDisabledByFrameId(window_id, is_disabled)

    Py4GW.Game.enqueue(_invoke)
    _log(f"set disabled enqueued window={window_id} is_disabled={is_disabled}")
    _schedule_report(f"state after set disabled {is_disabled}")


def _draw_window_tab() -> None:
    global WINDOW_LABEL
    global WINDOW_TITLE
    global WINDOW_X
    global WINDOW_Y
    global WINDOW_WIDTH
    global WINDOW_HEIGHT
    global WINDOW_FLAGS
    global WINDOW_PARENT_ID
    global WINDOW_CHILD_INDEX
    global WINDOW_ANCHOR_FLAGS

    WINDOW_LABEL = _normalize_input_text(PyImGui.input_text("Window Label", WINDOW_LABEL), WINDOW_LABEL)
    WINDOW_TITLE = _normalize_input_text(PyImGui.input_text("Window Title", WINDOW_TITLE), WINDOW_TITLE)
    WINDOW_PARENT_ID = _normalize_input_int(PyImGui.input_int("Parent Frame ID", int(WINDOW_PARENT_ID)), int(WINDOW_PARENT_ID))
    WINDOW_CHILD_INDEX = _normalize_input_int(PyImGui.input_int("Child Index", int(WINDOW_CHILD_INDEX)), int(WINDOW_CHILD_INDEX))
    WINDOW_FLAGS = _normalize_input_int(PyImGui.input_int("Window Flags", int(WINDOW_FLAGS)), int(WINDOW_FLAGS))
    WINDOW_ANCHOR_FLAGS = _normalize_input_int(
        PyImGui.input_int("Window Anchor Flags", int(WINDOW_ANCHOR_FLAGS)),
        int(WINDOW_ANCHOR_FLAGS),
    )
    WINDOW_X = _normalize_input_int(PyImGui.input_int("Window X", int(WINDOW_X)), int(WINDOW_X))
    WINDOW_Y = _normalize_input_int(PyImGui.input_int("Window Y", int(WINDOW_Y)), int(WINDOW_Y))
    WINDOW_WIDTH = _normalize_input_int(PyImGui.input_int("Window Width", int(WINDOW_WIDTH)), int(WINDOW_WIDTH))
    WINDOW_HEIGHT = _normalize_input_int(PyImGui.input_int("Window Height", int(WINDOW_HEIGHT)), int(WINDOW_HEIGHT))

    if PyImGui.button("CreateWindow"):
        _create_window()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Snapshot"):
        _dump_state("manual snapshot")
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Open DevText"):
        frame_id = int(GWUI.OpenDevTextWindow() or 0)
        _log(f"open devtext invoked frame_id={frame_id}")

    PyImGui.separator()
    PyImGui.text("Window Label is the internal lookup id used to find the frame later.")
    PyImGui.text("Window Title is the visible caption shown on the native window.")
    PyImGui.text(f"lookup_by_label='{WINDOW_LABEL}'")
    PyImGui.text(f"create_title='{WINDOW_TITLE}'")
    PyImGui.text(f"current_window={_current_window_summary()}")


def _draw_title_tab() -> None:
    global WINDOW_TITLE

    WINDOW_TITLE = _normalize_input_text(PyImGui.input_text("Title", WINDOW_TITLE), WINDOW_TITLE)
    if PyImGui.button("SetWindowTitle"):
        _set_window_title()
    PyImGui.separator()
    PyImGui.text("Applies GWUI.SetWindowTitle to the window found by Window Label.")


def _draw_text_label_tab() -> None:
    global TEXT_LABEL_TEXT
    global TEXT_LABEL_COMPONENT_LABEL
    global TEXT_LABEL_CHILD_INDEX
    global TEXT_LABEL_FLAGS

    TEXT_LABEL_TEXT = _normalize_input_text(PyImGui.input_text("Label Text", TEXT_LABEL_TEXT), TEXT_LABEL_TEXT)
    TEXT_LABEL_COMPONENT_LABEL = _normalize_input_text(
        PyImGui.input_text("Component Label", TEXT_LABEL_COMPONENT_LABEL),
        TEXT_LABEL_COMPONENT_LABEL,
    )
    TEXT_LABEL_CHILD_INDEX = _normalize_input_int(
        PyImGui.input_int("Child Index", int(TEXT_LABEL_CHILD_INDEX)),
        int(TEXT_LABEL_CHILD_INDEX),
    )
    TEXT_LABEL_FLAGS = _normalize_input_int(
        PyImGui.input_int("Component Flags", int(TEXT_LABEL_FLAGS)),
        int(TEXT_LABEL_FLAGS),
    )

    if PyImGui.button("CreateTextLabel"):
        _create_text_label()
    PyImGui.separator()
    PyImGui.text(f"last_text_label={_frame_summary(LAST_TEXT_LABEL_ID)}")



def _draw_rect_tab() -> None:
    global POSITION_X
    global POSITION_Y
    global SIZE_WIDTH
    global SIZE_HEIGHT
    global RECT_X
    global RECT_Y
    global RECT_WIDTH
    global RECT_HEIGHT
    global RECT_FLAGS

    RECT_FLAGS = _normalize_input_int(PyImGui.input_int("Rect Flags", int(RECT_FLAGS)), int(RECT_FLAGS))

    PyImGui.text("Position")
    POSITION_X = _normalize_input_int(PyImGui.input_int("Position X", int(POSITION_X)), int(POSITION_X))
    POSITION_Y = _normalize_input_int(PyImGui.input_int("Position Y", int(POSITION_Y)), int(POSITION_Y))
    if PyImGui.button("SetFramePosition"):
        _set_window_position()

    PyImGui.separator()
    PyImGui.text("Size")
    SIZE_WIDTH = _normalize_input_int(PyImGui.input_int("Size Width", int(SIZE_WIDTH)), int(SIZE_WIDTH))
    SIZE_HEIGHT = _normalize_input_int(PyImGui.input_int("Size Height", int(SIZE_HEIGHT)), int(SIZE_HEIGHT))
    if PyImGui.button("SetFrameSize"):
        _set_window_size()

    PyImGui.separator()
    PyImGui.text("Rect")
    RECT_X = _normalize_input_int(PyImGui.input_int("Rect X", int(RECT_X)), int(RECT_X))
    RECT_Y = _normalize_input_int(PyImGui.input_int("Rect Y", int(RECT_Y)), int(RECT_Y))
    RECT_WIDTH = _normalize_input_int(PyImGui.input_int("Rect Width", int(RECT_WIDTH)), int(RECT_WIDTH))
    RECT_HEIGHT = _normalize_input_int(PyImGui.input_int("Rect Height", int(RECT_HEIGHT)), int(RECT_HEIGHT))
    if PyImGui.button("ApplyRect"):
        _apply_window_rect()


def _draw_state_tab() -> None:
    global READ_DELAY_SECONDS

    delay_ms = int(READ_DELAY_SECONDS * 1000.0)
    delay_ms = _normalize_input_int(PyImGui.input_int("Read Delay (ms)", delay_ms), delay_ms)
    READ_DELAY_SECONDS = max(0.0, float(delay_ms) / 1000.0)

    if PyImGui.button("Hide Window"):
        _set_visible(False)
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Show Window"):
        _set_visible(True)
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Disable Window"):
        _set_disabled(True)
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Enable Window"):
        _set_disabled(False)

    PyImGui.separator()
    PyImGui.text(f"lookup_window_label='{WINDOW_LABEL}'")
    PyImGui.text(f"pending_window_title='{WINDOW_TITLE}'")
    PyImGui.text(f"current_window={_current_window_summary()}")
    PyImGui.text(f"last_text_label={_frame_summary(LAST_TEXT_LABEL_ID)}")


def _draw_window() -> None:
    global WINDOW_OPEN

    PyImGui.set_next_window_size(760, 620)
    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("goal: validate end-user GWUI window primitives with a single clean harness")
    PyImGui.separator()

    if PyImGui.begin_tab_bar("GWUIEndUserTabs"):
        if PyImGui.begin_tab_item("Window"):
            _draw_window_tab()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Title"):
            _draw_title_tab()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Text Label"):
            _draw_text_label_tab()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Rect"):
            _draw_rect_tab()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("State"):
            _draw_state_tab()
            PyImGui.end_tab_item()
        PyImGui.end_tab_bar()

    PyImGui.end()


def main() -> None:
    global INITIALIZED

    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("tabs: Window, Title, Text Label, Rect, State")
        _log("flow: create a labeled window first, then test title, text label, and rect primitives on it")
        _log("state-changing calls schedule delayed reports so the frame tree can settle")
    _process_pending_reports()
    _draw_window()
