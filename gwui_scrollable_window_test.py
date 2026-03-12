import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "GWUI Scrollable Composition Test"
SCRIPT_REVISION = "2026-03-09-gwui-scrollable-composition-test-1"
WINDOW_OPEN = True
INITIALIZED = False
READ_DELAY_SECONDS = 0.50

WINDOW_LABEL = "Py4GW_Scroll_Composition_Window"
WINDOW_TITLE = "Py4GW Scrollable Window"
WINDOW_X = 140
WINDOW_Y = 140
WINDOW_WIDTH = 360
WINDOW_HEIGHT = 220

SCROLLABLE_LABEL = "Py4GW_Scrollable"
SCROLLABLE_CHILD_INDEX = 0x20
SCROLLABLE_FLAGS = 0x20000

TEXT_LABEL_PREFIX = "Scrollable Label"
TEXT_LABEL_FLAGS = 0x300
TEXT_LABEL_COUNT = 5
TEXT_LABEL_X = 8
TEXT_LABEL_Y = 8
TEXT_LABEL_WIDTH = 220
TEXT_LABEL_HEIGHT = 18
TEXT_LABEL_VERTICAL_SPACING = 20
TEXT_LABEL_ANCHOR_FLAGS = 0x5

PENDING_REPORTS: list[tuple[float, str]] = []
LAST_SCROLLABLE_ID = 0
LAST_TEXT_LABEL_IDS: list[int] = []


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


def _normalize_input_text(result, current: str) -> str:
    if isinstance(result, tuple):
        if len(result) >= 2:
            return str(result[1])
        if len(result) == 1:
            return str(result[0])
    if result is None:
        return str(current)
    return str(result)


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


def _current_window_id() -> int:
    return int(UIManager.GetFrameIDByLabel(WINDOW_LABEL) or 0)


def _window() -> GWUI.Window:
    return GWUI.WrapWindow(_current_window_id())


def _scrollable() -> GWUI.Scrollable:
    return GWUI.WrapScrollable(LAST_SCROLLABLE_ID)


def _dump_state(prefix: str) -> None:
    window = _window()
    content = window.get_content()
    observed_scrollable = window.get_scrollable()
    scrollable = _scrollable()
    page = scrollable.get_page()
    item_ids: list[int] = []
    item_count = 0
    page_child_ids: list[int] = []
    if scrollable.exists():
        try:
            item_ids = scrollable.get_items()
            item_count = scrollable.get_count()
        except Exception as exc:
            _log(f"{prefix} item_inspection_error={exc}")
    if page.exists():
        try:
            page_child_ids = [
                int(UIManager.GetChildFrameByFrameId(page.frame_id, offset) or 0)
                for offset in range(0x20, 0x40)
            ]
            page_child_ids = [frame_id for frame_id in page_child_ids if frame_id > 0]
        except Exception as exc:
            _log(f"{prefix} page_child_inspection_error={exc}")
    _log(
        f"{prefix} "
        f"window=({_frame_summary(window.frame_id)}) "
        f"content=({_frame_summary(content.frame_id)}) "
        f"observed_scrollable=({_frame_summary(observed_scrollable.frame_id)}) "
        f"scrollable=({_frame_summary(scrollable.frame_id)}) "
        f"page=({_frame_summary(page.frame_id)}) "
        f"scrollable_count={item_count} "
        f"scrollable_items={item_ids} "
        f"page_children={page_child_ids} "
        f"last_text_labels={LAST_TEXT_LABEL_IDS}"
    )


def _create_window() -> None:
    def _invoke() -> None:
        GWUI.CreateWindow(
            float(WINDOW_X),
            float(WINDOW_Y),
            float(WINDOW_WIDTH),
            float(WINDOW_HEIGHT),
            frame_label=WINDOW_LABEL,
            window_title=WINDOW_TITLE,
        )

    Py4GW.Game.enqueue(_invoke)
    _log(
        f"create window enqueued label='{WINDOW_LABEL}' title='{WINDOW_TITLE}' "
        f"rect=({WINDOW_X},{WINDOW_Y},{WINDOW_WIDTH},{WINDOW_HEIGHT})"
    )
    _schedule_report("state after create window")


def _create_scrollable() -> None:
    global LAST_SCROLLABLE_ID

    window = _window()
    if not window.exists():
        _log("create scrollable skipped because window id is 0")
        return

    def _invoke() -> None:
        global LAST_SCROLLABLE_ID
        try:
            scrollable = window.create_scrollable(
                component_label=SCROLLABLE_LABEL,
                child_index=int(SCROLLABLE_CHILD_INDEX),
                component_flags=int(SCROLLABLE_FLAGS),
            )
            LAST_SCROLLABLE_ID = int(scrollable.frame_id or 0)
            _log(
                f"create scrollable returned frame_id={LAST_SCROLLABLE_ID} "
                f"page_frame_id={int(scrollable.get_page_frame_id() or 0)}"
            )
        except Exception as exc:
            LAST_SCROLLABLE_ID = 0
            _log(f"create scrollable invoke error={exc}")

    Py4GW.Game.enqueue(_invoke)
    _log(
        f"create scrollable enqueued window={window.frame_id} content={window.get_content_frame_id()} "
        f"child_index={SCROLLABLE_CHILD_INDEX} flags=0x{SCROLLABLE_FLAGS:X} label='{SCROLLABLE_LABEL}'"
    )
    _schedule_report("state after create scrollable")


def _insert_text_labels() -> None:
    global LAST_TEXT_LABEL_IDS

    scrollable = _scrollable()
    if not scrollable.exists():
        _log("insert text labels skipped because scrollable id is 0")
        return

    def _invoke() -> None:
        global LAST_TEXT_LABEL_IDS
        created_ids: list[int] = []
        try:
            for index in range(max(1, int(TEXT_LABEL_COUNT))):
                label = scrollable.create_text_label(
                    f"{TEXT_LABEL_PREFIX} {index + 1}",
                    component_label=f"Py4GW_Scroll_Text_{index + 1}",
                    child_index=0,
                    component_flags=int(TEXT_LABEL_FLAGS),
                )
                label_id = int(label.frame_id or 0)
                if label_id > 0:
                    GWUI.ApplyRect(
                        label_id,
                        float(TEXT_LABEL_X),
                        float(TEXT_LABEL_Y + index * TEXT_LABEL_VERTICAL_SPACING),
                        float(TEXT_LABEL_WIDTH),
                        float(TEXT_LABEL_HEIGHT),
                        flags=int(TEXT_LABEL_ANCHOR_FLAGS),
                        disable_center=True,
                    )
                    GWUI.TriggerFrameRedrawByFrameId(label_id)
                created_ids.append(label_id)
            LAST_TEXT_LABEL_IDS = created_ids
            page = scrollable.get_page()
            if page.exists():
                GWUI.TriggerFrameRedrawByFrameId(page.frame_id)
            GWUI.TriggerFrameRedrawByFrameId(scrollable.frame_id)
        except Exception as exc:
            LAST_TEXT_LABEL_IDS = created_ids
            _log(f"insert text labels invoke error={exc}")

    Py4GW.Game.enqueue(_invoke)
    _log(
        f"insert text labels enqueued scrollable={scrollable.frame_id} "
        f"count={TEXT_LABEL_COUNT} flags=0x{TEXT_LABEL_FLAGS:X} prefix='{TEXT_LABEL_PREFIX}'"
    )
    _schedule_report("state after insert text labels")


def _clear_scrollable_items() -> None:
    scrollable = _scrollable()
    if not scrollable.exists():
        _log("clear scrollable items skipped because scrollable id is 0")
        return

    def _invoke() -> None:
        scrollable.clear_items()

    Py4GW.Game.enqueue(_invoke)
    _log(f"clear scrollable items enqueued scrollable={scrollable.frame_id}")
    _schedule_report("state after clear scrollable items")


def _draw_window() -> None:
    global WINDOW_OPEN
    global READ_DELAY_SECONDS
    global WINDOW_LABEL
    global WINDOW_TITLE
    global WINDOW_X
    global WINDOW_Y
    global WINDOW_WIDTH
    global WINDOW_HEIGHT
    global SCROLLABLE_LABEL
    global SCROLLABLE_CHILD_INDEX
    global SCROLLABLE_FLAGS
    global TEXT_LABEL_PREFIX
    global TEXT_LABEL_FLAGS
    global TEXT_LABEL_COUNT
    global TEXT_LABEL_X
    global TEXT_LABEL_Y
    global TEXT_LABEL_WIDTH
    global TEXT_LABEL_HEIGHT
    global TEXT_LABEL_VERTICAL_SPACING
    global TEXT_LABEL_ANCHOR_FLAGS

    PyImGui.set_next_window_size(760, 460)
    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    delay_ms = int(READ_DELAY_SECONDS * 1000.0)
    delay_ms = _normalize_input_int(PyImGui.input_int("Read Delay (ms)", delay_ms), delay_ms)
    READ_DELAY_SECONDS = max(0.0, float(delay_ms) / 1000.0)

    WINDOW_LABEL = _normalize_input_text(PyImGui.input_text("Window Label", WINDOW_LABEL), WINDOW_LABEL)
    WINDOW_TITLE = _normalize_input_text(PyImGui.input_text("Window Title", WINDOW_TITLE), WINDOW_TITLE)
    WINDOW_X = _normalize_input_int(PyImGui.input_int("Window X", int(WINDOW_X)), int(WINDOW_X))
    WINDOW_Y = _normalize_input_int(PyImGui.input_int("Window Y", int(WINDOW_Y)), int(WINDOW_Y))
    WINDOW_WIDTH = _normalize_input_int(PyImGui.input_int("Window Width", int(WINDOW_WIDTH)), int(WINDOW_WIDTH))
    WINDOW_HEIGHT = _normalize_input_int(PyImGui.input_int("Window Height", int(WINDOW_HEIGHT)), int(WINDOW_HEIGHT))

    SCROLLABLE_LABEL = _normalize_input_text(PyImGui.input_text("Scrollable Label", SCROLLABLE_LABEL), SCROLLABLE_LABEL)
    SCROLLABLE_CHILD_INDEX = _normalize_input_int(PyImGui.input_int("Scrollable Child Index", int(SCROLLABLE_CHILD_INDEX)), int(SCROLLABLE_CHILD_INDEX))
    SCROLLABLE_FLAGS = _normalize_input_int(PyImGui.input_int("Scrollable Flags", int(SCROLLABLE_FLAGS)), int(SCROLLABLE_FLAGS))

    TEXT_LABEL_PREFIX = _normalize_input_text(PyImGui.input_text("Text Prefix", TEXT_LABEL_PREFIX), TEXT_LABEL_PREFIX)
    TEXT_LABEL_COUNT = _normalize_input_int(PyImGui.input_int("Text Count", int(TEXT_LABEL_COUNT)), int(TEXT_LABEL_COUNT))
    TEXT_LABEL_FLAGS = _normalize_input_int(PyImGui.input_int("Text Flags", int(TEXT_LABEL_FLAGS)), int(TEXT_LABEL_FLAGS))
    TEXT_LABEL_X = _normalize_input_int(PyImGui.input_int("Text X", int(TEXT_LABEL_X)), int(TEXT_LABEL_X))
    TEXT_LABEL_Y = _normalize_input_int(PyImGui.input_int("Text Y", int(TEXT_LABEL_Y)), int(TEXT_LABEL_Y))
    TEXT_LABEL_WIDTH = _normalize_input_int(PyImGui.input_int("Text Width", int(TEXT_LABEL_WIDTH)), int(TEXT_LABEL_WIDTH))
    TEXT_LABEL_HEIGHT = _normalize_input_int(PyImGui.input_int("Text Height", int(TEXT_LABEL_HEIGHT)), int(TEXT_LABEL_HEIGHT))
    TEXT_LABEL_VERTICAL_SPACING = _normalize_input_int(
        PyImGui.input_int("Text Vertical Spacing", int(TEXT_LABEL_VERTICAL_SPACING)),
        int(TEXT_LABEL_VERTICAL_SPACING),
    )
    TEXT_LABEL_ANCHOR_FLAGS = _normalize_input_int(
        PyImGui.input_int("Text Anchor Flags", int(TEXT_LABEL_ANCHOR_FLAGS)),
        int(TEXT_LABEL_ANCHOR_FLAGS),
    )

    if PyImGui.button("Create Window"):
        _create_window()
    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Create Scrollable"):
        _create_scrollable()
    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Insert Text Labels"):
        _insert_text_labels()
    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Clear Scrollable Items"):
        _clear_scrollable_items()
    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Dump State"):
        _dump_state("manual state")

    window = _window()
    scrollable = _scrollable()
    page = scrollable.get_page()

    PyImGui.separator()
    PyImGui.text(f"current_window={window.frame_id}")
    PyImGui.text(f"content_frame={window.get_content_frame_id() if window.exists() else 0}")
    PyImGui.text(f"scrollable_frame={scrollable.frame_id}")
    PyImGui.text(f"scrollable_page={page.frame_id}")
    PyImGui.text(f"scrollable_item_count={scrollable.get_count() if scrollable.exists() else 0}")
    PyImGui.text(f"last_text_labels={LAST_TEXT_LABEL_IDS}")

    PyImGui.end()


def configure() -> None:
    pass


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        _log(f"script revision={SCRIPT_REVISION}")
        _log("goal: test GWUI.Window and GWUI.Scrollable wrappers on a custom empty window")
        _log("flow: create window, create scrollable, insert text labels into scrollable page, then inspect state")
        INITIALIZED = True

    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
