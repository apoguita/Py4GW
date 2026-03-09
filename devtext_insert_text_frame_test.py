import ctypes
import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction, ScannerSection
from Py4GWCoreLib.native_src.internals.prototypes import NativeFunctionPrototype
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "DevText Insert Text Frame Test"
SCRIPT_REVISION = "2026-03-07-devtext-insert-text-frame-test-1"
WINDOW_OPEN = True
INITIALIZED = False
INIT_SINGLE_TEXT_HOST_FALLBACK = 0x004FA1E0

READ_DELAY_SECONDS = 0.50
FRAME_LABEL = "PyDevTextInsertedTextHost"
INSERTED_FRAME_ID = 0
LAST_CHILD_SLOT = 0

INIT_SINGLE_TEXT_HOST_PROC = None
PENDING_REPORTS: list[tuple[float, str]] = []


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


def _resolve_init_single_text_host_proc() -> int:
    global INIT_SINGLE_TEXT_HOST_PROC
    if INIT_SINGLE_TEXT_HOST_PROC is None:
        INIT_SINGLE_TEXT_HOST_PROC = NativeFunction(
            name="Ui_InitSingleTextHostProc",
            pattern=bytes.fromhex(
                "55 8B EC 8B 45 08 83 EC 0C 8B 48 04 83 F9 04 74 69 83 F9 09 74 13"
            ),
            mask="x" * 23,
            offset=0,
            section=ScannerSection.TEXT,
            prototype=NativeFunctionPrototype(ctypes.c_uint32),
            use_near_call=False,
            report_success=True,
        )
    if INIT_SINGLE_TEXT_HOST_PROC.is_valid():
        return int(INIT_SINGLE_TEXT_HOST_PROC.get_address() or 0)
    return int(INIT_SINGLE_TEXT_HOST_FALLBACK)


def _current_devtext_root() -> int:
    return int(GWUI.GetDevTextFrameID() or 0)


def _current_devtext_host() -> int:
    root = _current_devtext_root()
    if root <= 0:
        return 0
    return int(UIManager.GetChildFramePathByFrameId(root, [0, 0, 0]) or 0)


def _current_inserted_root() -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(FRAME_LABEL) or 0)
    if frame_id > 0:
        return frame_id
    return int(INSERTED_FRAME_ID or 0)


def _find_free_child_slot(parent_id: int, start_index: int = 0x20, end_index: int = 0xFE) -> int:
    return int(GWUI.FindAvailableChildSlot(parent_id, start_index, end_index) or 0)


def _dump_state(prefix: str) -> None:
    root = _current_devtext_root()
    host = _current_devtext_host()
    inserted = _current_inserted_root()
    inserted0 = int(UIManager.GetChildFrameByFrameId(inserted, 0) or 0) if inserted > 0 else 0
    inserted00 = int(UIManager.GetChildFrameByFrameId(inserted0, 0) or 0) if inserted0 > 0 else 0
    inserted000 = int(UIManager.GetChildFrameByFrameId(inserted00, 0) or 0) if inserted00 > 0 else 0
    _log(
        f"{prefix} "
        f"devtext_root=({_frame_summary(root)}) "
        f"host=({_frame_summary(host)}) "
        f"inserted=({_frame_summary(inserted)}) "
        f"inserted[0]=({_frame_summary(inserted0)}) "
        f"inserted[0][0]=({_frame_summary(inserted00)}) "
        f"inserted[0][0][0]=({_frame_summary(inserted000)})"
    )


def _open_original_devtext() -> None:
    def _invoke() -> None:
        GWUI.OpenDevTextWindow()

    Py4GW.Game.enqueue(_invoke)
    _log("open original DevText enqueued")
    _schedule_report("state after open original")


def _insert_text_host_frame() -> None:
    global LAST_CHILD_SLOT
    parent_id = _current_devtext_host()
    if parent_id <= 0:
        _log("insert text host skipped because DevText host is unavailable")
        return
    proc = _resolve_init_single_text_host_proc()
    if proc <= 0:
        _log("insert text host skipped because Ui_InitSingleTextHostProc is unresolved")
        return
    child_slot = _find_free_child_slot(parent_id)
    if child_slot <= 0:
        _log("insert text host skipped because no free child slot was found")
        return
    LAST_CHILD_SLOT = child_slot

    def _invoke() -> None:
        global INSERTED_FRAME_ID
        INSERTED_FRAME_ID = int(
            GWUI.CreateLabeledFrameByFrameId(
                parent_id,
                0,
                child_slot,
                proc,
                0,
                FRAME_LABEL,
            )
            or 0
        )

    Py4GW.Game.enqueue(_invoke)
    _log(
        f"insert text host enqueued parent={parent_id} child_slot=0x{child_slot:X} "
        f"callback=0x{proc:X} label='{FRAME_LABEL}'"
    )
    _schedule_report("state after insert text host")


def _apply_text_to_inserted() -> None:
    inserted = _current_inserted_root()
    inserted0 = int(UIManager.GetChildFrameByFrameId(inserted, 0) or 0) if inserted > 0 else 0
    inserted00 = int(UIManager.GetChildFrameByFrameId(inserted0, 0) or 0) if inserted0 > 0 else 0
    inserted000 = int(UIManager.GetChildFrameByFrameId(inserted00, 0) or 0) if inserted00 > 0 else 0
    target = inserted000 or inserted00 or inserted0 or inserted
    if target <= 0:
        _log("apply text skipped because inserted subtree is unavailable")
        return

    def _invoke() -> None:
        GWUI.SetMultilineLabelByFrameId(target, "Py4GW inserted text host\nSecond line")
        GWUI.SetLabelByFrameId(target, "Py4GW inserted text host")

    Py4GW.Game.enqueue(_invoke)
    _log(f"apply text enqueued target={target}")
    _schedule_report("state after apply text")


def _draw_window() -> None:
    global WINDOW_OPEN
    global READ_DELAY_SECONDS
    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("goal: insert a native text-bearing child frame into original DevText")
    PyImGui.separator()
    PyImGui.text("exact steps:")
    PyImGui.text("1) Open Original DevText")
    PyImGui.text("2) Insert Text Host Frame")
    PyImGui.text("3) Apply Text To Inserted")
    PyImGui.text("4) Dump State")
    PyImGui.separator()

    READ_DELAY_SECONDS = float(
        _normalize_input_int(
            PyImGui.input_int("Read Delay (ms)", int(READ_DELAY_SECONDS * 1000.0)),
            int(READ_DELAY_SECONDS * 1000.0),
        )
    ) / 1000.0

    if PyImGui.button("Open Original DevText"):
        _open_original_devtext()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Insert Text Host Frame"):
        _insert_text_host_frame()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Apply Text To Inserted"):
        _apply_text_to_inserted()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Dump State"):
        _dump_state("manual state report")

    PyImGui.separator()
    PyImGui.text(f"devtext_root={_current_devtext_root()}")
    PyImGui.text(f"devtext_host={_current_devtext_host()}")
    PyImGui.text(f"inserted_frame={_current_inserted_root()}")
    PyImGui.text(f"last_child_slot=0x{LAST_CHILD_SLOT:X}" if LAST_CHILD_SLOT > 0 else "last_child_slot=unresolved")
    proc = _resolve_init_single_text_host_proc()
    PyImGui.text(f"Ui_InitSingleTextHostProc=0x{proc:X}" if proc > 0 else "Ui_InitSingleTextHostProc=unresolved")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("test flow:")
        _log("1) click 'Open Original DevText'")
        _log("2) click 'Insert Text Host Frame'")
        _log("3) wait for 'state after insert text host'")
        _log("4) click 'Apply Text To Inserted'")
        _log("5) wait for 'state after apply text'")
        _log("6) click 'Dump State'")
    _process_pending_reports()
    _draw_window()
