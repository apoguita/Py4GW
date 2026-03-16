import ctypes
import time

import Py4GW
import PyImGui

from Py4GWCoreLib import GWContext, Scanner, UIManager
from Py4GWCoreLib.GWUI import GWUI
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction, ScannerSection
from Py4GWCoreLib.native_src.internals.prototypes import NativeFunctionPrototype, Prototypes


MODULE_NAME = "Empty Window Title Override Test"
SCRIPT_REVISION = "2026-03-09-empty-window-title-override-1"
WINDOW_OPEN = True
INITIALIZED = False

FRAME_LABEL = "PyEmptyWindowTitleOverride"
WINDOW_X = 120.0
WINDOW_Y_FROM_TOP = 120.0
WINDOW_WIDTH = 320.0
WINDOW_HEIGHT = 180.0
WINDOW_ANCHOR_FLAGS = 0x6

ARBITRARY_TITLE = "Py4GW Empty Clone Title"
LAST_STATUS = "idle"
LAST_ENCODED_TEXT_PTR = 0
PENDING_REPORTS: list[tuple[float, str]] = []

CREATE_ENCODED_TEXT_FN = None
SET_FRAME_TEXT_FN = None

STATIC_UI_DEVTEXT_DIALOG_PROC = 0x00864170
STATIC_UI_SET_FRAME_TEXT = 0x00610B00
DEVTEXT_USE_SCAN_AHEAD = 0x40

U32_U32_WCHARP_U32_RET_U32 = NativeFunctionPrototype(
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_wchar_p,
    ctypes.c_uint32,
)


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _schedule_report(prefix: str, delay_seconds: float = 0.50) -> None:
    PENDING_REPORTS.append((time.time() + max(0.0, float(delay_seconds)), prefix))


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


def _viewport_height() -> float:
    root_frame_id = int(UIManager.GetRootFrameID() or 0)
    _, viewport_height = UIManager.GetViewportDimensions(root_frame_id)
    return float(viewport_height)


def _engine_y_from_top(y_from_top: float, height: float) -> float:
    return _viewport_height() - float(y_from_top) - float(height)


def _resolve_window_id() -> int:
    return int(UIManager.GetFrameIDByLabel(FRAME_LABEL) or 0)


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


def _emit_snapshot(prefix: str) -> None:
    window_id = _resolve_window_id()
    host_id = int(GWUI.ResolveObservedContentHostByFrameId(window_id) or 0) if window_id > 0 else 0
    _log(
        f"{prefix} "
        f"window=({_frame_summary(window_id)}) "
        f"host=({_frame_summary(host_id)}) "
        f"hook_installed={GWUI.IsWindowTitleHookInstalled()} "
        f"pending_title={GWUI.HasNextCreatedWindowTitle()} "
        f"last_applied_frame={GWUI.GetLastAppliedWindowTitleFrameId()} "
        f"last_applied_title='{GWUI.GetLastAppliedWindowTitle()}' "
        f"frame_label='{GWUI.GetFrameLabelByFrameId(window_id)}' "
        f"last_encoded_text_ptr=0x{LAST_ENCODED_TEXT_PTR:X}"
    )


def _destroy_existing_window() -> None:
    window_id = _resolve_window_id()
    if window_id > 0:
        GWUI.DestroyUIComponentByFrameId(window_id)


def _resolve_caption_functions() -> bool:
    global CREATE_ENCODED_TEXT_FN
    global SET_FRAME_TEXT_FN

    if CREATE_ENCODED_TEXT_FN is None:
        CREATE_ENCODED_TEXT_FN = NativeFunction(
            name="Ui_CreateEncodedText",
            pattern=(
                b"\x55\x8B\xEC\x51\x56\x57\xE8\x00\x00\x00\x00\x8B\x48\x18"
                b"\xE8\x00\x00\x00\x00\x8B\xF8"
            ),
            mask="xxxxxxx????xxxx????xx",
            offset=0,
            section=ScannerSection.TEXT,
            prototype=U32_U32_WCHARP_U32_RET_U32,
            use_near_call=False,
            report_success=True,
        )

    if SET_FRAME_TEXT_FN is None:
        set_text_addr = _resolve_live_set_frame_text_addr()
        if set_text_addr > 0:
            SET_FRAME_TEXT_FN = NativeFunction.from_address(
                "Ui_SetFrameText_Live",
                set_text_addr,
                Prototypes["Void_U32_U32"],
                report_success=True,
            )

    return CREATE_ENCODED_TEXT_FN.is_valid() and SET_FRAME_TEXT_FN.is_valid()


def _read_u8(address: int) -> int:
    return int(ctypes.c_ubyte.from_address(address).value)


def _read_i32(address: int) -> int:
    return int(ctypes.c_int32.from_address(address).value)


def _resolve_relative_call_target(call_addr: int) -> int:
    if call_addr <= 0:
        return 0
    try:
        if _read_u8(call_addr) != 0xE8:
            return 0
        rel = _read_i32(call_addr + 1)
        return int(call_addr + 5 + rel)
    except (ValueError, OSError):
        return 0


def _resolve_live_set_frame_text_addr() -> int:
    try:
        use_addr = int(Scanner.FindNthUseOfStringW("DlgDevText", 0, 0, 0) or 0)
    except Exception:
        use_addr = 0
    if use_addr <= 0:
        _log("live set-frame-text resolve failed: DlgDevText xref missing")
        return 0

    try:
        proc_addr = int(Scanner.ToFunctionStart(use_addr, 0x1200) or 0)
    except Exception:
        proc_addr = 0
    if proc_addr <= 0:
        _log("live set-frame-text resolve failed: DevText proc start missing")
        return 0

    runtime_slide = int(proc_addr - STATIC_UI_DEVTEXT_DIALOG_PROC)
    expected_base = int(STATIC_UI_SET_FRAME_TEXT + runtime_slide)
    expected_called = int(expected_base + 0x30)

    create_addr = 0
    if CREATE_ENCODED_TEXT_FN and CREATE_ENCODED_TEXT_FN.is_valid():
        create_addr = int(CREATE_ENCODED_TEXT_FN.get_address() or 0)

    seen_create = False
    for addr in range(use_addr, use_addr + DEVTEXT_USE_SCAN_AHEAD):
        target = _resolve_relative_call_target(addr)
        if target <= 0:
            continue
        if create_addr and target == create_addr:
            seen_create = True
            continue
        if seen_create and target == expected_called:
            _log(
                "live set-frame-text resolved from DlgDevText xref "
                f"use=0x{use_addr:X} proc=0x{proc_addr:X} "
                f"runtime_slide=0x{runtime_slide:X} addr=0x{target:X}"
            )
            return target

    for addr in range(use_addr, use_addr + DEVTEXT_USE_SCAN_AHEAD):
        target = _resolve_relative_call_target(addr)
        if target == expected_called:
            _log(
                "live set-frame-text fallback match "
                f"use=0x{use_addr:X} proc=0x{proc_addr:X} "
                f"runtime_slide=0x{runtime_slide:X} addr=0x{target:X}"
            )
            return target

    _log(
        "live set-frame-text resolve failed "
        f"use=0x{use_addr:X} proc=0x{proc_addr:X} "
        f"runtime_slide=0x{runtime_slide:X} expected=0x{expected_called:X}"
    )
    return 0


def _create_empty_window(with_override: bool) -> None:
    global LAST_STATUS

    def _invoke() -> None:
        if GWContext.Char.GetContext() is None:
            _log("create empty invoke aborted: char_context_unavailable")
            return
        _destroy_existing_window()
        GWUI.ClearNextCreatedWindowTitle()
        if with_override:
            armed = GWUI.SetNextCreatedWindowTitle(ARBITRARY_TITLE)
            _log(f"armed next title override armed={armed} title='{ARBITRARY_TITLE}'")
        frame_id = int(
            GWUI.CreateWindow(
                WINDOW_X,
                _engine_y_from_top(WINDOW_Y_FROM_TOP, WINDOW_HEIGHT),
                WINDOW_WIDTH,
                WINDOW_HEIGHT,
                frame_label=FRAME_LABEL,
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
            f"create empty invoke complete frame_id={frame_id} "
            f"with_override={with_override} title='{ARBITRARY_TITLE}'"
        )

    LAST_STATUS = (
        "create empty with override enqueued"
        if with_override
        else "create empty baseline enqueued"
    )
    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after empty create")


def _apply_direct_setter() -> None:
    global LAST_STATUS

    def _invoke() -> None:
        window_id = _resolve_window_id()
        if window_id <= 0:
            _log("direct setter invoke aborted: window unavailable")
            return
        applied = GWUI.SetWindowTitle(window_id, ARBITRARY_TITLE)
        _log(
            f"direct setter invoke complete frame_id={window_id} "
            f"applied={applied} title='{ARBITRARY_TITLE}'"
        )

    LAST_STATUS = "direct setter enqueued"
    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after direct setter")


def _apply_native_literal_caption() -> None:
    global LAST_STATUS

    def _invoke() -> None:
        global LAST_ENCODED_TEXT_PTR
        window_id = _resolve_window_id()
        if window_id <= 0:
            _log("native literal invoke aborted: window unavailable")
            return
        if not _resolve_caption_functions():
            _log("native literal invoke aborted: caption functions unresolved")
            return
        encoded_text_ptr = int(CREATE_ENCODED_TEXT_FN.directCall(8, 7, ARBITRARY_TITLE, 0) or 0)
        LAST_ENCODED_TEXT_PTR = encoded_text_ptr
        if encoded_text_ptr <= 0:
            _log(f"native literal invoke failed title='{ARBITRARY_TITLE}'")
            return
        SET_FRAME_TEXT_FN.directCall(window_id, encoded_text_ptr)
        GWUI.TriggerFrameRedrawByFrameId(window_id)
        _log(
            f"native literal invoke complete frame_id={window_id} "
            f"title='{ARBITRARY_TITLE}' encoded=0x{encoded_text_ptr:X}"
        )

    LAST_STATUS = "native literal title enqueued"
    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after native literal")


def _destroy_window() -> None:
    global LAST_STATUS

    def _invoke() -> None:
        _destroy_existing_window()
        GWUI.ClearNextCreatedWindowTitle()
        _log("destroy invoke complete")

    LAST_STATUS = "destroy enqueued"
    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after destroy")


def _draw_window() -> None:
    global WINDOW_OPEN
    global ARBITRARY_TITLE
    global WINDOW_X
    global WINDOW_Y_FROM_TOP
    global WINDOW_WIDTH
    global WINDOW_HEIGHT

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    ARBITRARY_TITLE = str(PyImGui.input_text("Arbitrary Title", ARBITRARY_TITLE))
    WINDOW_X = float(PyImGui.input_float("X", WINDOW_X))
    WINDOW_Y_FROM_TOP = float(PyImGui.input_float("Y From Top", WINDOW_Y_FROM_TOP))
    WINDOW_WIDTH = float(PyImGui.input_float("Width", WINDOW_WIDTH))
    WINDOW_HEIGHT = float(PyImGui.input_float("Height", WINDOW_HEIGHT))

    if PyImGui.button("Create Empty Baseline"):
        _create_empty_window(False)
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Create Empty + Hook Override"):
        _create_empty_window(True)

    if PyImGui.button("Apply Direct Setter"):
        _apply_direct_setter()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Apply Native Literal"):
        _apply_native_literal_caption()

    if PyImGui.button("Snapshot"):
        Py4GW.Game.enqueue(lambda: _emit_snapshot("manual snapshot"))
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Destroy"):
        _destroy_window()

    PyImGui.separator()
    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("flow:")
    PyImGui.text("1) Create Empty Baseline and inspect the default title")
    PyImGui.text("2) Create Empty + Hook Override and inspect whether the title is fully replaced")
    PyImGui.text("3) Recreate baseline, then Apply Direct Setter")
    PyImGui.text("4) Recreate baseline, then Apply Native Literal")
    PyImGui.text(f"last_status={LAST_STATUS}")
    PyImGui.text(f"hook_installed={GWUI.IsWindowTitleHookInstalled()}")
    PyImGui.text(f"pending_title={GWUI.HasNextCreatedWindowTitle()}")
    PyImGui.text(f"last_applied_frame={GWUI.GetLastAppliedWindowTitleFrameId()}")
    PyImGui.text(f"last_applied_title={GWUI.GetLastAppliedWindowTitle()}")
    PyImGui.text(f"current_window={_resolve_window_id()}")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("goal: compare all current arbitrary-title paths on an empty cloned window")
        _log("use the hook path first, then compare direct setter and native literal setter")
    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
