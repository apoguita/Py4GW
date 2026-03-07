from Py4GWCoreLib import GWContext, PyImGui, Scanner, UIManager


MODULE_NAME = "Clone DevSound Window"
SCRIPT_REVISION = "2026-03-06-clone-devsound-window-1"
WINDOW_OPEN = True
REVISION_LOGGED = False

FRAME_LABEL = "PyDevSoundClone"
TARGET_X = 0.0
TARGET_Y = 0.0
TARGET_WIDTH = 420.0
TARGET_HEIGHT = 520.0
TARGET_FLAGS = 0x6
LAST_STATUS = "idle"
DEVSOUND_PROC_CACHE = 0


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _get_viewport_height() -> float:
    root_frame_id = UIManager.GetRootFrameID()
    _, viewport_height = UIManager.GetViewportDimensions(root_frame_id)
    return float(viewport_height)


def _to_engine_y_from_top(y_from_top: float, height: float) -> float:
    return _get_viewport_height() - float(y_from_top) - float(height)


def _find_window() -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(FRAME_LABEL) or 0)
    if frame_id > 0 and UIManager.FrameExists(frame_id):
        return frame_id
    return 0


def _frame_summary(frame_id: int) -> str:
    if frame_id <= 0:
        return "frame_id=0"
    try:
        frame = UIManager.GetFrameByID(frame_id)
        return (
            f"frame_id={frame_id} "
            f"parent_id={int(frame.parent_id)} "
            f"child_offset_id={int(frame.child_offset_id)} "
            f"type={int(frame.type)} "
            f"template_type={int(frame.template_type)} "
            f"is_created={bool(frame.is_created)} "
            f"is_visible={bool(frame.is_visible)}"
        )
    except Exception as exc:
        return f"frame_id={frame_id} summary_error={exc}"


def _resolve_devsound_dialog_proc() -> int:
    global DEVSOUND_PROC_CACHE
    if DEVSOUND_PROC_CACHE > 0:
        return DEVSOUND_PROC_CACHE

    for xref_index in range(8):
        try:
            use_addr = int(Scanner.FindNthUseOfStringW("DlgDevSound", xref_index, 0, 0) or 0)
        except Exception:
            use_addr = 0
        if use_addr <= 0:
            continue
        try:
            proc_addr = int(Scanner.ToFunctionStart(use_addr, 0x1200) or 0)
        except Exception:
            proc_addr = 0
        if proc_addr > 0:
            DEVSOUND_PROC_CACHE = proc_addr
            return proc_addr
    return 0


def _create_window() -> None:
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

    frame_callback = _resolve_devsound_dialog_proc()
    if frame_callback <= 0:
        LAST_STATUS = "resolve DlgDevSound proc failed"
        _log(LAST_STATUS)
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    frame_id = int(
        UIManager.CreateWindow(
            TARGET_X,
            engine_y,
            TARGET_WIDTH,
            TARGET_HEIGHT,
            frame_label=FRAME_LABEL,
            parent_frame_id=9,
            child_index=0,
            frame_flags=0,
            create_param=0,
            frame_callback=frame_callback,
            anchor_flags=TARGET_FLAGS,
            ensure_devtext_source=False,
        )
        or 0
    )
    if frame_id > 0:
        LAST_STATUS = f"created frame_id={frame_id}"
        _log(
            f"created frame_id={frame_id} source='DlgDevSound' proc=0x{frame_callback:X} "
            f"engine_pos=({TARGET_X}, {engine_y}) size=({TARGET_WIDTH}, {TARGET_HEIGHT})"
        )
    else:
        LAST_STATUS = "create failed"
        _log(f"create failed source='DlgDevSound' proc=0x{frame_callback:X}")


def _close_window() -> None:
    global LAST_STATUS
    frame_id = _find_window()
    if frame_id <= 0:
        LAST_STATUS = "no cloned window"
        _log(LAST_STATUS)
        return
    result = bool(UIManager.HideWindowByLabel(FRAME_LABEL))
    LAST_STATUS = f"closed frame_id={frame_id} result={result}"
    _log(LAST_STATUS)


def _refresh_window() -> None:
    global LAST_STATUS
    frame_id = _find_window()
    LAST_STATUS = _frame_summary(frame_id)
    _log(f"refresh {LAST_STATUS}")


def main() -> None:
    global WINDOW_OPEN
    global REVISION_LOGGED
    global TARGET_X
    global TARGET_Y
    global TARGET_WIDTH
    global TARGET_HEIGHT

    if not WINDOW_OPEN:
        return

    if not REVISION_LOGGED:
        REVISION_LOGGED = True
        _log(f"script revision={SCRIPT_REVISION}")

    if PyImGui.begin(f"{MODULE_NAME}##{MODULE_NAME}", WINDOW_OPEN):
        PyImGui.text("Clone DevSound")
        TARGET_X = float(PyImGui.input_float("X", TARGET_X))
        TARGET_Y = float(PyImGui.input_float("Y From Top", TARGET_Y))
        TARGET_WIDTH = float(PyImGui.input_float("Width", TARGET_WIDTH))
        TARGET_HEIGHT = float(PyImGui.input_float("Height", TARGET_HEIGHT))

        if PyImGui.button("Create Window"):
            _create_window()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Close Window"):
            _close_window()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Refresh"):
            _refresh_window()

        PyImGui.separator()
        PyImGui.text(f"Window Label: {FRAME_LABEL}")
        proc_addr = _resolve_devsound_dialog_proc()
        PyImGui.text(f"DevSound Proc: 0x{proc_addr:X}" if proc_addr > 0 else "DevSound Proc: unresolved")
        PyImGui.text(f"Current: {_frame_summary(_find_window())}")
        PyImGui.text(f"Status: {LAST_STATUS}")
    PyImGui.end()


if __name__ == "__main__":
    main()
