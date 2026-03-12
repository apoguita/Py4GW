import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "Empty Window Text Label Test"
SCRIPT_REVISION = "2026-03-08-empty-window-text-label-test-1"
WINDOW_OPEN = True
INITIALIZED = False

EMPTY_WINDOW_LABEL = "PyEmptyWindowTextLabelHost"
TEXT_LABEL_LABEL = "PyEmptyWindowTextLabel"
TEXT_LABEL_TEXT = "Py4GW Text Label Test"

EMPTY_WINDOW_ID = 0
TEXT_LABEL_ID = 0
LAST_STATUS = "idle"
PENDING_REPORTS: list[tuple[float, str]] = []


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _schedule_report(prefix: str, delay_seconds: float = 0.50) -> None:
    PENDING_REPORTS.append((time.time() + max(0.0, float(delay_seconds)), prefix))
    _log(f"scheduled report prefix='{prefix}' delay={delay_seconds:.2f}s")


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


def _read_decoded(frame_id: int) -> str:
    frame_id = int(frame_id or 0)
    if frame_id <= 0:
        return ""
    try:
        return str(GWUI.GetTextLabelDecodedByFrameId(frame_id) or "")
    except Exception as exc:
        return f"<decoded_error:{exc}>"


def _update_cached_ids() -> None:
    global EMPTY_WINDOW_ID
    global TEXT_LABEL_ID
    EMPTY_WINDOW_ID = int(UIManager.GetFrameIDByLabel(EMPTY_WINDOW_LABEL) or EMPTY_WINDOW_ID or 0)
    TEXT_LABEL_ID = int(UIManager.GetFrameIDByLabel(TEXT_LABEL_LABEL) or TEXT_LABEL_ID or 0)


def _enqueue_state_snapshot(prefix: str) -> None:
    def _invoke() -> None:
        _update_cached_ids()
        _log(
            f"{prefix} "
            f"empty_window=({_frame_summary(EMPTY_WINDOW_ID)}) "
            f"text_label=({_frame_summary(TEXT_LABEL_ID)}) "
            f"text_label_decoded='{_read_decoded(TEXT_LABEL_ID)}'"
        )

    Py4GW.Game.enqueue(_invoke)


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
        _enqueue_state_snapshot(prefix)


def _create_empty_window() -> None:
    global LAST_STATUS

    def _invoke() -> None:
        global EMPTY_WINDOW_ID
        global TEXT_LABEL_ID
        EMPTY_WINDOW_ID = int(
            GWUI.CreateWindow(
                120.0,
                120.0,
                320.0,
                180.0,
                EMPTY_WINDOW_LABEL,
            )
            or 0
        )
        TEXT_LABEL_ID = 0
        _update_cached_ids()
        _log(f"create empty window invoke result empty_window={EMPTY_WINDOW_ID}")

    LAST_STATUS = "create empty window enqueued"
    Py4GW.Game.enqueue(_invoke)
    _log(LAST_STATUS)
    _schedule_report("state after create empty window")


def _insert_text_label() -> None:
    global LAST_STATUS

    def _invoke() -> None:
        global TEXT_LABEL_ID
        _update_cached_ids()
        parent = int(EMPTY_WINDOW_ID or 0)
        if parent <= 0:
            _log("insert text label invoke aborted: empty window unavailable")
            return
        child_offset = int(GWUI.FindAvailableChildSlot(parent, 0x20, 0xFE) or 0)
        _log(
            f"insert text label invoke begin parent={parent} child_offset=0x{child_offset:X}"
        )
        if child_offset <= 0:
            _log("insert text label invoke aborted: no child slot available")
            return
        TEXT_LABEL_ID = int(
            GWUI.CreateTextLabel(
                parent,
                TEXT_LABEL_TEXT,
                TEXT_LABEL_LABEL,
                child_offset,
                0x300,
            )
            or 0
        )
        _update_cached_ids()
        _log(
            f"insert text label invoke result text_label={TEXT_LABEL_ID} "
            f"decoded='{_read_decoded(TEXT_LABEL_ID)}'"
        )

    LAST_STATUS = "insert text label enqueued"
    Py4GW.Game.enqueue(_invoke)
    _log(LAST_STATUS)
    _schedule_report("state after insert text label")


def _draw_window() -> None:
    global WINDOW_OPEN

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("flow: Create Empty Window -> Insert Text Label")
    PyImGui.separator()

    if PyImGui.button("Create Empty Window"):
        _create_empty_window()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Insert Text Label"):
        _insert_text_label()

    PyImGui.separator()
    PyImGui.text(f"last_status={LAST_STATUS}")
    PyImGui.text(f"empty_window={EMPTY_WINDOW_ID}")
    PyImGui.text(f"text_label={TEXT_LABEL_ID}")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("test flow:")
        _log("1) click 'Create Empty Window'")
        _log("2) click 'Insert Text Label'")
    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
