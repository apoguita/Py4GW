import time

from Py4GWCoreLib import GWContext, PyImGui, UIManager


MODULE_NAME = "DevText Binding Showcase"
SCRIPT_REVISION = "2026-03-06-binding-showcase-1"
WINDOW_OPEN = True
REVISION_LOGGED = False

SOURCE_LABEL = "PyDevTextBindingSource"
CLONE_PREFIX = "PyDevTextBindingClone"

TARGET_X = 0.0
TARGET_Y = 0.0
TARGET_WIDTH = 100.0
TARGET_HEIGHT = 300.0
TARGET_FLAGS = 0x6

MOVE_X = 180.0
MOVE_Y = 40.0
RESIZE_WIDTH = 180.0
RESIZE_HEIGHT = 220.0
READ_DELAY_SECONDS = 0.50

LAST_STATUS = "idle"
MULTI_CLONE_LABELS: list[str] = []
PENDING_REPORTS: list[tuple[float, str, str]] = []
TEMP_DEVTEXT_OPENED = False


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _schedule_report(label: str, prefix: str, delay_seconds: float | None = None) -> None:
    delay = READ_DELAY_SECONDS if delay_seconds is None else max(0.0, float(delay_seconds))
    PENDING_REPORTS.append((time.time() + delay, label, prefix))
    _log(f"scheduled report label={label} prefix='{prefix}' delay={delay:.2f}s")


def _process_pending_reports() -> None:
    if not PENDING_REPORTS:
        return
    now = time.time()
    ready: list[tuple[float, str, str]] = []
    pending: list[tuple[float, str, str]] = []
    for scheduled_at, label, prefix in PENDING_REPORTS:
        if scheduled_at <= now:
            ready.append((scheduled_at, label, prefix))
        else:
            pending.append((scheduled_at, label, prefix))
    PENDING_REPORTS[:] = pending
    for _, label, prefix in ready:
        _report_state_for_label(prefix, label)


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


def _find_window_by_label(frame_label: str) -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(frame_label) or 0)
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


def _report_state_for_label(prefix: str, frame_label: str) -> None:
    root_id = _find_window_by_label(frame_label)
    host_id = UIManager.ResolveObservedContentHostByFrameId(root_id)
    _log(
        f"{prefix} "
        f"label={frame_label} "
        f"root=({_frame_summary(root_id)}) "
        f"host=({_frame_summary(host_id)}) "
        f"host_child_count={_direct_child_count(host_id)}"
    )


def _report_source_state(prefix: str) -> None:
    _report_state_for_label(prefix, SOURCE_LABEL)


def _show_binding_status() -> None:
    proc_addr = int(UIManager.ResolveDevTextDialogProc() or 0)
    source_frame_id, opened_temporarily = UIManager.EnsureDevTextSource()
    _log(
        f"binding status devtext_proc=0x{proc_addr:X} "
        f"source_frame_id={source_frame_id} opened_temporarily={opened_temporarily}"
    )
    if opened_temporarily:
        UIManager.RestoreDevTextSource(True)
        _log("binding status restored DevText source after status check")


def _create_source(raw: bool) -> None:
    global LAST_STATUS
    existing = _find_window_by_label(SOURCE_LABEL)
    if existing > 0:
        LAST_STATUS = f"source exists frame_id={existing}"
        _log(LAST_STATUS)
        return
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    if raw:
        frame_id = UIManager.CreateWindow(
            TARGET_X,
            engine_y,
            TARGET_WIDTH,
            TARGET_HEIGHT,
            frame_label=SOURCE_LABEL,
            parent_frame_id=9,
            child_index=0,
            frame_flags=0,
            create_param=0,
            frame_callback=0,
            anchor_flags=TARGET_FLAGS,
            ensure_devtext_source=True,
        )
        mode = "raw"
    else:
        frame_id = UIManager.CreateEmptyWindow(
            TARGET_X,
            engine_y,
            TARGET_WIDTH,
            TARGET_HEIGHT,
            frame_label=SOURCE_LABEL,
            parent_frame_id=9,
            child_index=0,
            frame_flags=0,
            create_param=0,
            frame_callback=0,
            anchor_flags=TARGET_FLAGS,
            ensure_devtext_source=True,
        )
        mode = "empty"

    LAST_STATUS = f"create {mode} source frame_id={int(frame_id or 0)}"
    _log(
        f"create {mode} source frame_id={int(frame_id or 0)} "
        f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT})"
    )
    _report_source_state(f"state immediately after create {mode}")
    _schedule_report(SOURCE_LABEL, f"state after create {mode} delay")


def _clear_source_by_root() -> None:
    global LAST_STATUS
    root_id = _find_window_by_label(SOURCE_LABEL)
    if root_id <= 0:
        LAST_STATUS = "source missing"
        _log(LAST_STATUS)
        return
    _report_source_state("state before clear by root")
    result = bool(UIManager.ClearWindowContentsByFrameId(root_id))
    LAST_STATUS = f"clear by root result={result}"
    _log(f"clear by root root={root_id} result={result}")
    _schedule_report(SOURCE_LABEL, "state after clear by root delay")


def _clear_source_by_host() -> None:
    global LAST_STATUS
    root_id = _find_window_by_label(SOURCE_LABEL)
    if root_id <= 0:
        LAST_STATUS = "source missing"
        _log(LAST_STATUS)
        return
    host_id = int(UIManager.ResolveObservedContentHostByFrameId(root_id) or 0)
    if host_id <= 0:
        LAST_STATUS = "observed host unresolved"
        _log(LAST_STATUS)
        return
    _report_source_state("state before clear by host")
    result = bool(UIManager.ClearFrameChildrenRecursiveByFrameId(host_id))
    LAST_STATUS = f"clear by host result={result}"
    _log(f"clear by host root={root_id} host={host_id} result={result}")
    _schedule_report(SOURCE_LABEL, "state after clear by host delay")


def _collapse_source() -> None:
    global LAST_STATUS
    root_id = _find_window_by_label(SOURCE_LABEL)
    if root_id <= 0:
        LAST_STATUS = "source missing"
        _log(LAST_STATUS)
        return
    _report_source_state("state before collapse")
    result = bool(UIManager.CollapseWindowByFrameId(root_id))
    LAST_STATUS = f"collapse result={result}"
    _log(f"collapse source root={root_id} result={result}")
    _schedule_report(SOURCE_LABEL, "state after collapse delay")


def _restore_source() -> None:
    global LAST_STATUS
    root_id = _find_window_by_label(SOURCE_LABEL)
    if root_id <= 0:
        LAST_STATUS = "source missing"
        _log(LAST_STATUS)
        return
    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    _report_source_state("state before restore")
    result = bool(
        UIManager.RestoreWindowRectByFrameId(
            root_id,
            TARGET_X,
            engine_y,
            TARGET_WIDTH,
            TARGET_HEIGHT,
            0,
            True,
            True,
        )
    )
    LAST_STATUS = f"restore result={result}"
    _log(
        f"restore source root={root_id} "
        f"engine_rect=({TARGET_X},{engine_y},{TARGET_WIDTH},{TARGET_HEIGHT}) result={result}"
    )
    _schedule_report(SOURCE_LABEL, "state after restore delay")


def _move_source() -> None:
    global LAST_STATUS
    root_id = _find_window_by_label(SOURCE_LABEL)
    if root_id <= 0:
        LAST_STATUS = "source missing"
        _log(LAST_STATUS)
        return
    engine_y = _to_engine_y_from_top(MOVE_Y, TARGET_HEIGHT)
    _report_source_state("state before move")
    result = bool(UIManager.SetFramePosition(root_id, MOVE_X, engine_y, None, True))
    LAST_STATUS = f"move result={result}"
    _log(f"move source root={root_id} engine_pos=({MOVE_X},{engine_y}) result={result}")
    _schedule_report(SOURCE_LABEL, "state after move delay")


def _resize_source() -> None:
    global LAST_STATUS
    root_id = _find_window_by_label(SOURCE_LABEL)
    if root_id <= 0:
        LAST_STATUS = "source missing"
        _log(LAST_STATUS)
        return
    _report_source_state("state before resize")
    result = bool(UIManager.SetFrameSize(root_id, RESIZE_WIDTH, RESIZE_HEIGHT, None, True))
    LAST_STATUS = f"resize result={result}"
    _log(f"resize source root={root_id} size=({RESIZE_WIDTH},{RESIZE_HEIGHT}) result={result}")
    _schedule_report(SOURCE_LABEL, "state after resize delay")


def _set_source_rect() -> None:
    global LAST_STATUS
    root_id = _find_window_by_label(SOURCE_LABEL)
    if root_id <= 0:
        LAST_STATUS = "source missing"
        _log(LAST_STATUS)
        return
    engine_y = _to_engine_y_from_top(MOVE_Y, RESIZE_HEIGHT)
    _report_source_state("state before set rect")
    result = bool(UIManager.SetFrameRect(root_id, MOVE_X, engine_y, RESIZE_WIDTH, RESIZE_HEIGHT, None, True))
    LAST_STATUS = f"set rect result={result}"
    _log(
        f"set rect source root={root_id} "
        f"engine_rect=({MOVE_X},{engine_y},{RESIZE_WIDTH},{RESIZE_HEIGHT}) result={result}"
    )
    _schedule_report(SOURCE_LABEL, "state after set rect delay")


def _create_additional_empty_clones() -> None:
    global LAST_STATUS
    global MULTI_CLONE_LABELS
    clone_specs = [
        ("A", 220.0, 20.0, 140.0, 180.0),
        ("B", 400.0, 80.0, 180.0, 200.0),
        ("C", 620.0, 160.0, 220.0, 240.0),
    ]
    MULTI_CLONE_LABELS = []
    results: list[str] = []

    for suffix, x, y_from_top, width, height in clone_specs:
        label = f"{CLONE_PREFIX}_{suffix}"
        frame_id = _find_window_by_label(label)
        if frame_id <= 0:
            frame_id = UIManager.CreateEmptyWindow(
                x,
                _to_engine_y_from_top(y_from_top, height),
                width,
                height,
                frame_label=label,
                parent_frame_id=9,
                child_index=0,
                frame_flags=0,
                create_param=0,
                frame_callback=0,
                anchor_flags=TARGET_FLAGS,
                ensure_devtext_source=True,
            )
        frame_id = int(frame_id or 0)
        results.append(f"{label}:frame={frame_id}")
        if frame_id > 0:
            MULTI_CLONE_LABELS.append(label)
            _schedule_report(label, "additional clone state after create delay")

    LAST_STATUS = f"additional empty clones count={len(MULTI_CLONE_LABELS)}"
    _log(f"create additional empty clones results={results}")


def _report_all_additional() -> None:
    if not MULTI_CLONE_LABELS:
        _log("additional clone state labels=<none>")
        return
    for label in MULTI_CLONE_LABELS:
        _report_state_for_label("additional clone state", label)


def _toggle_devtext_source() -> None:
    global LAST_STATUS
    global TEMP_DEVTEXT_OPENED
    if not TEMP_DEVTEXT_OPENED:
        frame_id, opened_temporarily = UIManager.EnsureDevTextSource()
        TEMP_DEVTEXT_OPENED = bool(opened_temporarily)
        LAST_STATUS = f"ensure devtext source frame_id={frame_id} opened_temporarily={opened_temporarily}"
        _log(LAST_STATUS)
        return
    UIManager.RestoreDevTextSource(True)
    TEMP_DEVTEXT_OPENED = False
    LAST_STATUS = "restored devtext source after explicit ensure"
    _log(LAST_STATUS)


def main() -> None:
    global WINDOW_OPEN
    global REVISION_LOGGED
    global TARGET_X
    global TARGET_Y
    global TARGET_WIDTH
    global TARGET_HEIGHT
    global MOVE_X
    global MOVE_Y
    global RESIZE_WIDTH
    global RESIZE_HEIGHT
    global READ_DELAY_SECONDS

    if not WINDOW_OPEN:
        return

    if not REVISION_LOGGED:
        REVISION_LOGGED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("showcase buttons map directly to the new C++ bindings and high-level Python wrappers")
        _log("raw create = populated DevText clone")
        _log("empty create = clone + clear contents in one call")
        _log("clear by root uses ClearWindowContentsByFrameId")
        _log("clear by host uses ResolveObservedContentHostByFrameId + ClearFrameChildrenRecursiveByFrameId")
        _log("collapse/restore/move/resize/set rect use the new bound helpers")
        _show_binding_status()

    _process_pending_reports()

    if PyImGui.begin(f"{MODULE_NAME}##{MODULE_NAME}", WINDOW_OPEN):
        PyImGui.text("Showcase the new empty-window binding helpers")
        TARGET_X = float(PyImGui.input_float("Source X", TARGET_X))
        TARGET_Y = float(PyImGui.input_float("Source Y From Top", TARGET_Y))
        TARGET_WIDTH = float(PyImGui.input_float("Source Width", TARGET_WIDTH))
        TARGET_HEIGHT = float(PyImGui.input_float("Source Height", TARGET_HEIGHT))
        MOVE_X = float(PyImGui.input_float("Move X", MOVE_X))
        MOVE_Y = float(PyImGui.input_float("Move Y From Top", MOVE_Y))
        RESIZE_WIDTH = float(PyImGui.input_float("Resize Width", RESIZE_WIDTH))
        RESIZE_HEIGHT = float(PyImGui.input_float("Resize Height", RESIZE_HEIGHT))
        READ_DELAY_SECONDS = float(PyImGui.input_float("Read Delay Seconds", READ_DELAY_SECONDS))

        PyImGui.separator()
        PyImGui.text("Binding status and DevText source")
        if PyImGui.button("Show Binding Status"):
            _show_binding_status()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Ensure/Restore DevText Source"):
            _toggle_devtext_source()

        PyImGui.separator()
        PyImGui.text("Create helpers")
        if PyImGui.button("Create Raw Source Clone"):
            _create_source(True)
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Create Empty Source Clone"):
            _create_source(False)
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Report Source State"):
            _report_source_state("source state report")

        PyImGui.separator()
        PyImGui.text("Clear helpers")
        if PyImGui.button("Clear Source By Root"):
            _clear_source_by_root()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Clear Source By Host"):
            _clear_source_by_host()

        PyImGui.separator()
        PyImGui.text("Rect and lifecycle helpers")
        if PyImGui.button("Collapse Source"):
            _collapse_source()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Restore Source"):
            _restore_source()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Move Source"):
            _move_source()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Resize Source"):
            _resize_source()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Set Source Rect"):
            _set_source_rect()

        PyImGui.separator()
        PyImGui.text("Multiple empty clone helper")
        if PyImGui.button("Create Additional Empty Clones"):
            _create_additional_empty_clones()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Report Additional Clone States"):
            _report_all_additional()

        PyImGui.separator()
        PyImGui.text("Suggested test flow:")
        PyImGui.text("1. Show Binding Status")
        PyImGui.text("2. Create Raw Source Clone, then Report Source State")
        PyImGui.text("3. Clear Source By Root or Clear Source By Host")
        PyImGui.text("4. Create Empty Source Clone in a fresh run to test one-shot empty creation")
        PyImGui.text("5. Collapse Source, Restore Source, Move Source, Resize Source, Set Source Rect")
        PyImGui.text("6. Create Additional Empty Clones and report them")
        PyImGui.text(f"Current Source: {_frame_summary(_find_window_by_label(SOURCE_LABEL))}")
        PyImGui.text(f"Additional Labels: {', '.join(MULTI_CLONE_LABELS) if MULTI_CLONE_LABELS else '<none>'}")
        PyImGui.text(f"Status: {LAST_STATUS}")
    PyImGui.end()


if __name__ == "__main__":
    main()
