import ctypes
import time

import Py4GW
from Py4GWCoreLib import GWContext, PyImGui, UIManager
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction, ScannerSection
from Py4GWCoreLib.native_src.internals.prototypes import NativeFunctionPrototype, Prototypes
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "Window Caption Test"
SCRIPT_REVISION = "2026-03-06-window-caption-test-2"
WINDOW_OPEN = True
REVISION_LOGGED = False

FRAME_LABEL = "PyWindowCaptionTest"
TARGET_X = 0.0
TARGET_Y = 0.0
TARGET_WIDTH = 180.0
TARGET_HEIGHT = 220.0
TARGET_FLAGS = 0x6
READ_DELAY_SECONDS = 0.50

TITLE_TEXT = "Py4GW Caption Test"
TITLE_STRING_ID = 0x541

LAST_STATUS = "idle"
LAST_ENCODED_TEXT_PTR = 0
PENDING_REPORTS: list[tuple[float, str]] = []

CREATE_ENCODED_TEXT_FN = None
CREATE_ENCODED_TEXT_FROM_ID_FN = None
SET_FRAME_TEXT_FN = None


U32_U32_WCHARP_U32_RET_U32 = NativeFunctionPrototype(
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_wchar_p,
    ctypes.c_uint32,
)


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _schedule_source_report(prefix: str, delay_seconds: float | None = None) -> None:
    delay = READ_DELAY_SECONDS if delay_seconds is None else max(0.0, float(delay_seconds))
    PENDING_REPORTS.append((time.time() + delay, prefix))
    _log(f"scheduled source report prefix='{prefix}' delay={delay:.2f}s")


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
        _report_state(prefix)


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
            f"rect=({left},{top})-({right},{bottom})"
        )
    except Exception as exc:
        return f"frame_id={frame_id} summary_error={exc}"


def _direct_child_count(frame_id: int) -> int:
    if frame_id <= 0:
        return 0
    count = 0
    try:
        for fid in UIManager.GetFrameArray():
            child_id = int(fid)
            try:
                frame = UIManager.GetFrameByID(child_id)
            except Exception:
                continue
            if int(frame.parent_id) == int(frame_id):
                count += 1
    except Exception:
        return 0
    return count


def _report_state(prefix: str) -> None:
    root_id = _find_window()
    host_id = int(GWUI.ResolveObservedContentHostByFrameId(root_id) or 0)
    _log(
        f"{prefix} "
        f"root=({_frame_summary(root_id)}) "
        f"host=({_frame_summary(host_id)}) "
        f"host_child_count={_direct_child_count(host_id)} "
        f"last_encoded_text_ptr=0x{LAST_ENCODED_TEXT_PTR:X}"
    )


def _resolve_caption_functions() -> bool:
    global CREATE_ENCODED_TEXT_FN
    global CREATE_ENCODED_TEXT_FROM_ID_FN
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

    if CREATE_ENCODED_TEXT_FROM_ID_FN is None:
        CREATE_ENCODED_TEXT_FROM_ID_FN = NativeFunction(
            name="Ui_CreateEncodedTextFromStringId",
            pattern=b"\x55\x8B\xEC\x6A\x00\xFF\x75\x08\xE8\x13\x00\x00\x00\x83\xC4\x08\x5D\xC3",
            mask="xxxxxxxxxxxxxxxxxx",
            offset=0,
            section=ScannerSection.TEXT,
            prototype=NativeFunctionPrototype(ctypes.c_uint32, ctypes.c_uint32),
            use_near_call=False,
            report_success=True,
        )

    if SET_FRAME_TEXT_FN is None:
        SET_FRAME_TEXT_FN = NativeFunction(
            name="Ui_SetFrameText",
            pattern=b"\x55\x8B\xEC\x53\x56\x57\x8B\x7D\x08\x8B\xF7\xF7\xDE\x1B\xF6\x85",
            mask="xxxxxxxxxxxxxxxx",
            offset=0,
            section=ScannerSection.TEXT,
            prototype=Prototypes["Void_U32_U32"],
            use_near_call=False,
            report_success=True,
        )

    return (
        CREATE_ENCODED_TEXT_FN.is_valid()
        and CREATE_ENCODED_TEXT_FROM_ID_FN.is_valid()
        and SET_FRAME_TEXT_FN.is_valid()
    )


def _log_caption_function_status() -> None:
    valid = _resolve_caption_functions()
    _log(
        "caption function status "
        f"valid={valid} "
        f"create_text=0x{CREATE_ENCODED_TEXT_FN.get_address():X} "
        f"create_text_from_id=0x{CREATE_ENCODED_TEXT_FROM_ID_FN.get_address():X} "
        f"set_frame_text=0x{SET_FRAME_TEXT_FN.get_address():X}"
        if valid
        else "caption function status valid=False"
    )


def _log_hook_status() -> None:
    _log(
        "hook status "
        f"installed={GWUI.IsWindowTitleHookInstalled()} "
        f"has_pending={GWUI.HasNextCreatedWindowTitle()} "
        f"last_frame={GWUI.GetLastAppliedWindowTitleFrameId()} "
        f"last_title='{GWUI.GetLastAppliedWindowTitle()}'"
    )


def _create_empty_window() -> None:
    global LAST_STATUS
    existing = _find_window()
    if existing > 0:
        LAST_STATUS = f"window exists frame_id={existing}"
        _log(LAST_STATUS)
        return
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    frame_id = int(
        GWUI.CreateEmptyWindow(
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
    LAST_STATUS = f"created empty window frame_id={frame_id}"
    _log(
        f"created empty window frame_id={frame_id} "
        f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT})"
    )
    _report_state("state immediately after create")
    _schedule_source_report("state after create delay")


def _create_raw_window() -> None:
    global LAST_STATUS
    existing = _find_window()
    if existing > 0:
        LAST_STATUS = f"window exists frame_id={existing}"
        _log(LAST_STATUS)
        return
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    frame_id = int(
        GWUI.CreateWindow(
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
    LAST_STATUS = f"created raw window frame_id={frame_id}"
    _log(
        f"created raw window frame_id={frame_id} "
        f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT})"
    )
    _report_state("state immediately after raw create")
    _schedule_source_report("state after raw create delay")


def _spawn_window() -> None:
    _create_empty_window()


def _spawn_raw_window_with_hook_title() -> None:
    global LAST_STATUS
    existing = _find_window()
    if existing > 0:
        LAST_STATUS = f"window exists frame_id={existing}"
        _log(LAST_STATUS)
        return
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return

    title_text = TITLE_TEXT
    if not GWUI.SetNextCreatedWindowTitle(title_text):
        LAST_STATUS = "failed to arm next-created title"
        _log(LAST_STATUS)
        _log_hook_status()
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    frame_id = int(
        GWUI.CreateWindow(
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
    LAST_STATUS = f"spawn raw + hook title frame_id={frame_id}"
    _log(
        f"spawn raw + hook title frame_id={frame_id} "
        f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT}) text='{title_text}'"
    )
    _report_state("state immediately after raw create with hook")
    _log_hook_status()
    _schedule_source_report("state after raw create + hook delay")


def _spawn_empty_window_with_hook_title() -> None:
    global LAST_STATUS
    existing = _find_window()
    if existing > 0:
        LAST_STATUS = f"window exists frame_id={existing}"
        _log(LAST_STATUS)
        return
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return

    title_text = TITLE_TEXT
    if not GWUI.SetNextCreatedWindowTitle(title_text):
        LAST_STATUS = "failed to arm next-created title"
        _log(LAST_STATUS)
        _log_hook_status()
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    frame_id = int(
        GWUI.CreateEmptyWindow(
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
    LAST_STATUS = f"spawn empty + hook title frame_id={frame_id}"
    _log(
        f"spawn empty + hook title frame_id={frame_id} "
        f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT}) text='{title_text}'"
    )
    _report_state("state immediately after empty create with hook")
    _log_hook_status()
    _schedule_source_report("state after empty create + hook delay")


def _enqueue_literal_caption() -> None:
    global LAST_STATUS
    root_id = _find_window()
    if root_id <= 0:
        LAST_STATUS = "window missing"
        _log(LAST_STATUS)
        return
    if not _resolve_caption_functions():
        LAST_STATUS = "caption functions unresolved"
        _log(LAST_STATUS)
        return

    title_text = TITLE_TEXT

    def _apply_caption() -> None:
        global LAST_ENCODED_TEXT_PTR
        encoded_text_ptr = int(CREATE_ENCODED_TEXT_FN.directCall(8, 7, title_text, 0) or 0)
        LAST_ENCODED_TEXT_PTR = encoded_text_ptr
        if encoded_text_ptr <= 0:
            print(f"[{MODULE_NAME}] literal caption create failed text='{title_text}'")
            return
        SET_FRAME_TEXT_FN.directCall(root_id, encoded_text_ptr)
        GWUI.TriggerFrameRedrawByFrameId(root_id)
        print(
            f"[{MODULE_NAME}] literal caption applied root={root_id} "
            f"text='{title_text}' encoded=0x{encoded_text_ptr:X}"
        )

    _report_state("state before literal caption")
    Py4GW.Game.enqueue(_apply_caption)
    LAST_STATUS = "literal caption enqueued"
    _log(f"literal caption enqueued root={root_id} text='{title_text}'")
    _schedule_source_report("state after literal caption delay")


def _spawn_raw_window_then_string_id_caption() -> None:
    global LAST_STATUS
    global LAST_ENCODED_TEXT_PTR
    existing = _find_window()
    if existing > 0:
        LAST_STATUS = f"window exists frame_id={existing}"
        _log(LAST_STATUS)
        return
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return
    if not _resolve_caption_functions():
        LAST_STATUS = "caption functions unresolved"
        _log(LAST_STATUS)
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    frame_id = int(
        GWUI.CreateWindow(
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
    if frame_id <= 0:
        LAST_STATUS = "raw create failed"
        _log(LAST_STATUS)
        return

    string_id = int(TITLE_STRING_ID)

    def _apply_caption() -> None:
        global LAST_ENCODED_TEXT_PTR
        encoded_text_ptr = int(CREATE_ENCODED_TEXT_FROM_ID_FN.directCall(string_id) or 0)
        LAST_ENCODED_TEXT_PTR = encoded_text_ptr
        if encoded_text_ptr <= 0:
            print(f"[{MODULE_NAME}] raw-create string-id caption create failed string_id=0x{string_id:X}")
            return
        SET_FRAME_TEXT_FN.directCall(frame_id, encoded_text_ptr)
        GWUI.TriggerFrameRedrawByFrameId(frame_id)
        print(
            f"[{MODULE_NAME}] raw-create string-id caption applied root={frame_id} "
            f"string_id=0x{string_id:X} encoded=0x{encoded_text_ptr:X}"
        )

    LAST_STATUS = f"spawn raw + string-id caption frame_id={frame_id}"
    _log(
        f"spawn raw + string-id caption frame_id={frame_id} "
        f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT}) string_id=0x{string_id:X}"
    )
    _report_state("state immediately after raw create before string-id caption")
    Py4GW.Game.enqueue(_apply_caption)
    _schedule_source_report("state after raw create + string-id caption delay")


def _spawn_empty_window_then_string_id_caption() -> None:
    global LAST_STATUS
    global LAST_ENCODED_TEXT_PTR
    existing = _find_window()
    if existing > 0:
        LAST_STATUS = f"window exists frame_id={existing}"
        _log(LAST_STATUS)
        return
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return
    if not _resolve_caption_functions():
        LAST_STATUS = "caption functions unresolved"
        _log(LAST_STATUS)
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    frame_id = int(
        GWUI.CreateEmptyWindow(
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
    if frame_id <= 0:
        LAST_STATUS = "empty create failed"
        _log(LAST_STATUS)
        return

    string_id = int(TITLE_STRING_ID)

    def _apply_caption() -> None:
        global LAST_ENCODED_TEXT_PTR
        encoded_text_ptr = int(CREATE_ENCODED_TEXT_FROM_ID_FN.directCall(string_id) or 0)
        LAST_ENCODED_TEXT_PTR = encoded_text_ptr
        if encoded_text_ptr <= 0:
            print(f"[{MODULE_NAME}] empty-create string-id caption create failed string_id=0x{string_id:X}")
            return
        SET_FRAME_TEXT_FN.directCall(frame_id, encoded_text_ptr)
        GWUI.TriggerFrameRedrawByFrameId(frame_id)
        print(
            f"[{MODULE_NAME}] empty-create string-id caption applied root={frame_id} "
            f"string_id=0x{string_id:X} encoded=0x{encoded_text_ptr:X}"
        )

    LAST_STATUS = f"spawn empty + string-id caption frame_id={frame_id}"
    _log(
        f"spawn empty + string-id caption frame_id={frame_id} "
        f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT}) string_id=0x{string_id:X}"
    )
    _report_state("state immediately after empty create before string-id caption")
    Py4GW.Game.enqueue(_apply_caption)
    _schedule_source_report("state after empty create + string-id caption delay")


def _spawn_raw_window_with_literal_caption() -> None:
    global LAST_STATUS
    global LAST_ENCODED_TEXT_PTR
    existing = _find_window()
    if existing > 0:
        LAST_STATUS = f"window exists frame_id={existing}"
        _log(LAST_STATUS)
        return
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return
    if not _resolve_caption_functions():
        LAST_STATUS = "caption functions unresolved"
        _log(LAST_STATUS)
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    frame_id = int(
        GWUI.CreateWindow(
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
    if frame_id <= 0:
        LAST_STATUS = "raw create failed"
        _log(LAST_STATUS)
        return

    title_text = TITLE_TEXT

    def _apply_caption() -> None:
        global LAST_ENCODED_TEXT_PTR
        encoded_text_ptr = int(CREATE_ENCODED_TEXT_FN.directCall(8, 7, title_text, 0) or 0)
        LAST_ENCODED_TEXT_PTR = encoded_text_ptr
        if encoded_text_ptr <= 0:
            print(f"[{MODULE_NAME}] raw-create caption create failed text='{title_text}'")
            return
        SET_FRAME_TEXT_FN.directCall(frame_id, encoded_text_ptr)
        GWUI.TriggerFrameRedrawByFrameId(frame_id)
        print(
            f"[{MODULE_NAME}] raw-create caption applied root={frame_id} "
            f"text='{title_text}' encoded=0x{encoded_text_ptr:X}"
        )

    LAST_STATUS = f"spawn raw + caption frame_id={frame_id}"
    _log(
        f"spawn raw + caption frame_id={frame_id} "
        f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT}) text='{title_text}'"
    )
    _report_state("state immediately after raw create before caption")
    Py4GW.Game.enqueue(_apply_caption)
    _schedule_source_report("state after raw create + caption delay")


def _spawn_empty_window_with_literal_caption() -> None:
    global LAST_STATUS
    global LAST_ENCODED_TEXT_PTR
    existing = _find_window()
    if existing > 0:
        LAST_STATUS = f"window exists frame_id={existing}"
        _log(LAST_STATUS)
        return
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return
    if not _resolve_caption_functions():
        LAST_STATUS = "caption functions unresolved"
        _log(LAST_STATUS)
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    frame_id = int(
        GWUI.CreateEmptyWindow(
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
    if frame_id <= 0:
        LAST_STATUS = "empty create failed"
        _log(LAST_STATUS)
        return

    title_text = TITLE_TEXT

    def _apply_caption() -> None:
        global LAST_ENCODED_TEXT_PTR
        encoded_text_ptr = int(CREATE_ENCODED_TEXT_FN.directCall(8, 7, title_text, 0) or 0)
        LAST_ENCODED_TEXT_PTR = encoded_text_ptr
        if encoded_text_ptr <= 0:
            print(f"[{MODULE_NAME}] empty-create caption create failed text='{title_text}'")
            return
        SET_FRAME_TEXT_FN.directCall(frame_id, encoded_text_ptr)
        GWUI.TriggerFrameRedrawByFrameId(frame_id)
        print(
            f"[{MODULE_NAME}] empty-create caption applied root={frame_id} "
            f"text='{title_text}' encoded=0x{encoded_text_ptr:X}"
        )

    LAST_STATUS = f"spawn empty + caption frame_id={frame_id}"
    _log(
        f"spawn empty + caption frame_id={frame_id} "
        f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT}) text='{title_text}'"
    )
    _report_state("state immediately after empty create before caption")
    Py4GW.Game.enqueue(_apply_caption)
    _schedule_source_report("state after empty create + caption delay")


def _enqueue_string_id_caption() -> None:
    global LAST_STATUS
    root_id = _find_window()
    if root_id <= 0:
        LAST_STATUS = "window missing"
        _log(LAST_STATUS)
        return
    if not _resolve_caption_functions():
        LAST_STATUS = "caption functions unresolved"
        _log(LAST_STATUS)
        return

    string_id = int(TITLE_STRING_ID)

    def _apply_caption() -> None:
        global LAST_ENCODED_TEXT_PTR
        encoded_text_ptr = int(CREATE_ENCODED_TEXT_FROM_ID_FN.directCall(string_id) or 0)
        LAST_ENCODED_TEXT_PTR = encoded_text_ptr
        if encoded_text_ptr <= 0:
            print(f"[{MODULE_NAME}] string-id caption create failed string_id=0x{string_id:X}")
            return
        SET_FRAME_TEXT_FN.directCall(root_id, encoded_text_ptr)
        GWUI.TriggerFrameRedrawByFrameId(root_id)
        print(
            f"[{MODULE_NAME}] string-id caption applied root={root_id} "
            f"string_id=0x{string_id:X} encoded=0x{encoded_text_ptr:X}"
        )

    _report_state("state before string-id caption")
    Py4GW.Game.enqueue(_apply_caption)
    LAST_STATUS = "string-id caption enqueued"
    _log(f"string-id caption enqueued root={root_id} string_id=0x{string_id:X}")
    _schedule_source_report("state after string-id caption delay")


def main() -> None:
    global WINDOW_OPEN
    global REVISION_LOGGED
    global TARGET_X
    global TARGET_Y
    global TARGET_WIDTH
    global TARGET_HEIGHT
    global TITLE_TEXT
    global TITLE_STRING_ID
    global READ_DELAY_SECONDS

    if not WINDOW_OPEN:
        return

    if not REVISION_LOGGED:
        REVISION_LOGGED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("test flow:")
        _log("1) click 'Show Hook Status'")
        _log("2) click 'Spawn Raw + Hook Title' or 'Spawn Empty + Hook Title'")
        _log("3) visually verify whether the window caption changed at creation time")
        _log("reads are delayed after create/title updates to let UI state settle")

    _process_pending_reports()

    if PyImGui.begin(f"{MODULE_NAME}##{MODULE_NAME}", WINDOW_OPEN):
        PyImGui.text("Test creation-time window title override on cloned native windows")
        TARGET_X = float(PyImGui.input_float("X", TARGET_X))
        TARGET_Y = float(PyImGui.input_float("Y From Top", TARGET_Y))
        TARGET_WIDTH = float(PyImGui.input_float("Width", TARGET_WIDTH))
        TARGET_HEIGHT = float(PyImGui.input_float("Height", TARGET_HEIGHT))
        TITLE_TEXT = str(PyImGui.input_text("Literal Title", TITLE_TEXT))
        READ_DELAY_SECONDS = float(PyImGui.input_float("Read Delay Seconds", READ_DELAY_SECONDS))

        if PyImGui.button("Show Hook Status"):
            _log_hook_status()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Report Window State"):
            _report_state("window state report")

        if PyImGui.button("Spawn Raw + Hook Title"):
            _spawn_raw_window_with_hook_title()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Spawn Empty + Hook Title"):
            _spawn_empty_window_with_hook_title()

        PyImGui.separator()
        PyImGui.text("Suggested flow:")
        PyImGui.text("1. Show Hook Status")
        PyImGui.text("2. Use Spawn Raw/Empty + Hook Title")
        PyImGui.text("3. Check the visible title and delayed hook status")
        PyImGui.text(f"Current: {_frame_summary(_find_window())}")
        PyImGui.text(f"Last Encoded Text Ptr: 0x{LAST_ENCODED_TEXT_PTR:X}")
        PyImGui.text(f"Hook Last Frame: {GWUI.GetLastAppliedWindowTitleFrameId()}")
        PyImGui.text(f"Hook Last Title: {GWUI.GetLastAppliedWindowTitle()}")
        PyImGui.text(f"Status: {LAST_STATUS}")
    PyImGui.end()


if __name__ == "__main__":
    main()
