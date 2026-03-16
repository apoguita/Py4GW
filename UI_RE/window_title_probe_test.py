import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "Window Title Probe"
SCRIPT_REVISION = "2026-03-08-window-title-probe-1"
WINDOW_OPEN = True
INITIALIZED = False

WINDOW_LABEL = "PyWindowTitleProbe"
WINDOW_ID = 0
LAST_STATUS = "idle"
PENDING_REPORTS: list[tuple[float, str]] = []

NEXT_CREATE_TITLE = "Clone Override Title"
DIRECT_SET_TITLE = "Direct SetFrameTitle Title"

WINDOW_X = 120.0
WINDOW_Y = 120.0
WINDOW_WIDTH = 280.0
WINDOW_HEIGHT = 180.0
WINDOW_ANCHOR_FLAGS = 0x6


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _schedule_report(prefix: str, delay_seconds: float = 0.50) -> None:
    PENDING_REPORTS.append((time.time() + max(0.0, float(delay_seconds)), prefix))


def _update_window_id() -> None:
    global WINDOW_ID
    resolved = int(UIManager.GetFrameIDByLabel(WINDOW_LABEL) or 0)
    if resolved > 0:
        WINDOW_ID = resolved


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
            f"rect=({left},{top})-({right},{bottom})"
        )
    except Exception as exc:
        return f"frame_id={frame_id} summary_error={exc}"


def _emit_snapshot(prefix: str) -> None:
    _update_window_id()
    _log(
        f"{prefix} "
        f"window=({_frame_summary(WINDOW_ID)}) "
        f"hook_installed={GWUI.IsWindowTitleHookInstalled()} "
        f"pending_title={GWUI.HasNextCreatedWindowTitle()} "
        f"last_applied_frame={GWUI.GetLastAppliedWindowTitleFrameId()} "
        f"last_applied_title='{GWUI.GetLastAppliedWindowTitle()}' "
        f"frame_label='{GWUI.GetFrameLabelByFrameId(WINDOW_ID)}'"
    )


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
        Py4GW.Game.enqueue(lambda prefix=prefix: _emit_snapshot(prefix))


def _destroy_window() -> None:
    global LAST_STATUS

    def _invoke() -> None:
        global WINDOW_ID
        _update_window_id()
        if WINDOW_ID > 0:
            GWUI.DestroyUIComponentByFrameId(WINDOW_ID)
        WINDOW_ID = 0
        _log("destroy window invoke complete")

    LAST_STATUS = "destroy enqueued"
    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after destroy")


def _create_window(with_title_override: bool) -> None:
    global LAST_STATUS

    def _invoke() -> None:
        global WINDOW_ID
        _update_window_id()
        if WINDOW_ID > 0:
            GWUI.DestroyUIComponentByFrameId(WINDOW_ID)
            WINDOW_ID = 0
        if with_title_override:
            GWUI.ClearNextCreatedWindowTitle()
            armed = GWUI.SetNextCreatedWindowTitle(NEXT_CREATE_TITLE)
            _log(f"armed next title override armed={armed} title='{NEXT_CREATE_TITLE}'")
        else:
            GWUI.ClearNextCreatedWindowTitle()
        WINDOW_ID = int(
            GWUI.CreateWindowClone(
                WINDOW_X,
                WINDOW_Y,
                WINDOW_WIDTH,
                WINDOW_HEIGHT,
                frame_label=WINDOW_LABEL,
                parent_frame_id=9,
                child_index=0,
                frame_flags=0,
                create_param=0,
                frame_callback=0,
                anchor_flags=WINDOW_ANCHOR_FLAGS,
                ensure_devtext_source=True,
            )
            or 0
        )
        _log(
            f"create window invoke complete frame_id={WINDOW_ID} "
            f"with_title_override={with_title_override}"
        )

    LAST_STATUS = "create enqueued with pending title override" if with_title_override else "create enqueued without title override"
    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after create")


def _apply_direct_title() -> None:
    global LAST_STATUS

    def _invoke() -> None:
        _update_window_id()
        if WINDOW_ID <= 0:
            _log("apply direct title invoke aborted: window unavailable")
            return
        applied = GWUI.SetWindowTitle(WINDOW_ID, DIRECT_SET_TITLE)
        _log(
            f"apply direct title invoke complete frame_id={WINDOW_ID} "
            f"applied={applied} title='{DIRECT_SET_TITLE}'"
        )

    LAST_STATUS = "direct title set enqueued"
    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after direct title set")


def _draw_window() -> None:
    global WINDOW_OPEN
    global NEXT_CREATE_TITLE
    global DIRECT_SET_TITLE

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    NEXT_CREATE_TITLE = str(PyImGui.input_text("Next Create Title", NEXT_CREATE_TITLE))
    DIRECT_SET_TITLE = str(PyImGui.input_text("Direct Set Title", DIRECT_SET_TITLE))

    if PyImGui.button("Create Window"):
        _create_window(False)
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Create With Override"):
        _create_window(True)
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Apply Direct Title"):
        _apply_direct_title()

    if PyImGui.button("Snapshot"):
        Py4GW.Game.enqueue(lambda: _emit_snapshot("manual snapshot"))
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Destroy Window"):
        _destroy_window()

    PyImGui.separator()
    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("test sequence:")
    PyImGui.text("1) Create With Override and inspect the visible title")
    PyImGui.text("2) Apply Direct Title and compare whether only the dynamic text channel changes")
    PyImGui.text(f"last_status={LAST_STATUS}")
    PyImGui.text(f"window_id={WINDOW_ID}")
    PyImGui.text(f"hook_installed={GWUI.IsWindowTitleHookInstalled()}")
    PyImGui.text(f"pending_title={GWUI.HasNextCreatedWindowTitle()}")
    PyImGui.text(f"last_applied_frame={GWUI.GetLastAppliedWindowTitleFrameId()}")
    PyImGui.text(f"last_applied_title={GWUI.GetLastAppliedWindowTitle()}")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("use 'Create With Override' to exercise clone-time title replacement")
        _log("use 'Apply Direct Title' to compare the dynamic text-only title path")
    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
