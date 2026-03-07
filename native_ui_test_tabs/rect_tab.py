import Py4GW
from Py4GWCoreLib import PyImGui, UIManager


MODULE_NAME = "Native UI Test"
DEVTEXT_LABEL = "DevText"

DRAW_OUTLINES = False

WINDOW_TITLE = "PyManagedDevTextClone"
TARGET_X = 0.0
TARGET_Y = 0.0
TARGET_WIDTH = 100.0
TARGET_HEIGHT = 300.0
TARGET_FLAGS = 0x6

ACTIVE_X = TARGET_X
ACTIVE_Y = TARGET_Y
ACTIVE_WIDTH = TARGET_WIDTH
ACTIVE_HEIGHT = TARGET_HEIGHT

LAST_TEST_STATUS = "idle"
CREATED_FRAME_ID = 0
CREATED_FRAME_VISIBLE = False
ORIGINAL_FRAME_ID = 0
ORIGINAL_FRAME_VISIBLE = False

PENDING_OBSERVE_FRAME_ID = 0
PENDING_OBSERVE_ACTION = ""
PENDING_OBSERVE_TICKS = 0
PENDING_OBSERVE_REQUESTED_X = None
PENDING_OBSERVE_REQUESTED_Y = None
PENDING_OBSERVE_REQUESTED_WIDTH = None
PENDING_OBSERVE_REQUESTED_HEIGHT = None

ORIGINAL_OUTLINE_COLOR = 0xFF00FF00
ORIGINAL_FILL_COLOR = 0x3000FF00
CREATED_OUTLINE_COLOR = 0xFFFFFFFF
CREATED_FILL_COLOR = 0x30FFFFFF


def _find_managed_clone_frame() -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(WINDOW_TITLE) or 0)
    if frame_id > 0 and UIManager.FrameExists(frame_id):
        return frame_id
    return 0


def _get_viewport_height() -> float:
    root_frame_id = UIManager.GetRootFrameID()
    _, viewport_height = UIManager.GetViewportDimensions(root_frame_id)
    return float(viewport_height)


def _to_engine_y_from_top(y_from_top: float, height: float) -> float:
    return _get_viewport_height() - float(y_from_top) - float(height)


def _safe_frame_coords(frame_id: int):
    try:
        if frame_id > 0 and UIManager.FrameExists(frame_id):
            return UIManager.GetFrameCoords(frame_id)
    except Exception:
        pass
    return None


def _safe_content_coords(frame_id: int):
    try:
        if frame_id > 0 and UIManager.FrameExists(frame_id):
            return UIManager.GetContentFrameCoords(frame_id)
    except Exception:
        pass
    return None


def _rect_metrics(rect):
    if not rect:
        return None
    left, top, right, bottom = rect
    return {
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "width": right - left,
        "height": bottom - top,
    }


def _format_metrics(metrics, prefix: str) -> str:
    if not metrics:
        return f"{prefix}=None"
    return (
        f"{prefix}={{left={metrics['left']}, top={metrics['top']}, "
        f"right={metrics['right']}, bottom={metrics['bottom']}, "
        f"width={metrics['width']}, height={metrics['height']}}}"
    )


def _format_deltas(
    metrics,
    requested_x: float | None = None,
    requested_y: float | None = None,
    requested_width: float | None = None,
    requested_height: float | None = None,
) -> str:
    if not metrics:
        return "delta=None"
    parts = []
    if requested_x is not None:
        parts.append(f"x={metrics['left'] - int(requested_x)}")
    if requested_y is not None:
        parts.append(f"y={metrics['top'] - int(requested_y)}")
    if requested_width is not None:
        parts.append(f"width={metrics['width'] - int(requested_width)}")
    if requested_height is not None:
        parts.append(f"height={metrics['height'] - int(requested_height)}")
    return "delta={}" if not parts else f"delta={{{', '.join(parts)}}}"


def _log_window_snapshot(
    label: str,
    frame_id: int,
    requested_x: float | None = None,
    requested_y: float | None = None,
    requested_width: float | None = None,
    requested_height: float | None = None,
) -> None:
    frame_rect = _safe_frame_coords(frame_id)
    content_rect = _safe_content_coords(frame_id)
    frame_metrics = _rect_metrics(frame_rect)
    content_metrics = _rect_metrics(content_rect)
    extra = ""
    if any(value is not None for value in (requested_x, requested_y, requested_width, requested_height)):
        requested_parts = []
        if requested_x is not None:
            requested_parts.append(f"x={requested_x}")
        if requested_y is not None:
            requested_parts.append(f"y={requested_y}")
        if requested_width is not None:
            requested_parts.append(f"width={requested_width}")
        if requested_height is not None:
            requested_parts.append(f"height={requested_height}")
        extra = (
            " "
            + _format_deltas(frame_metrics, requested_x, requested_y, requested_width, requested_height)
            + " "
            + f"requested={{{', '.join(requested_parts)}}}"
        )
    print(
        f"[{MODULE_NAME}] {label} frame_id={frame_id} "
        f"{_format_metrics(frame_metrics, 'frame')} "
        f"{_format_metrics(content_metrics, 'content')}{extra}"
    )


def _log_operation_inputs(
    action: str,
    frame_id: int,
    requested_x: float,
    requested_y: float,
    requested_width: float,
    requested_height: float,
    engine_x: float | None,
    engine_y: float | None,
    preserved_x: float,
    preserved_y: float,
    preserved_width: float,
    preserved_height: float,
) -> None:
    print(
        f"[{MODULE_NAME}] {action} inputs "
        f"frame_id={frame_id} title='{WINDOW_TITLE}' "
        f"requested_pos=({requested_x}, {requested_y}) "
        f"requested_size=({requested_width}, {requested_height}) "
        f"engine_pos=({engine_x}, {engine_y}) "
        f"preserved_pos=({preserved_x}, {preserved_y}) "
        f"preserved_size=({preserved_width}, {preserved_height}) "
        f"flags=0x{TARGET_FLAGS:X}"
    )


def _schedule_observation(
    frame_id: int,
    action: str,
    ticks: int = 45,
    requested_x: float | None = None,
    requested_y: float | None = None,
    requested_width: float | None = None,
    requested_height: float | None = None,
) -> None:
    global PENDING_OBSERVE_FRAME_ID
    global PENDING_OBSERVE_ACTION
    global PENDING_OBSERVE_TICKS
    global PENDING_OBSERVE_REQUESTED_X
    global PENDING_OBSERVE_REQUESTED_Y
    global PENDING_OBSERVE_REQUESTED_WIDTH
    global PENDING_OBSERVE_REQUESTED_HEIGHT
    PENDING_OBSERVE_FRAME_ID = frame_id
    PENDING_OBSERVE_ACTION = action
    PENDING_OBSERVE_TICKS = ticks
    PENDING_OBSERVE_REQUESTED_X = requested_x
    PENDING_OBSERVE_REQUESTED_Y = requested_y
    PENDING_OBSERVE_REQUESTED_WIDTH = requested_width
    PENDING_OBSERVE_REQUESTED_HEIGHT = requested_height


def _observe_pending_action() -> None:
    global PENDING_OBSERVE_FRAME_ID
    global PENDING_OBSERVE_ACTION
    global PENDING_OBSERVE_TICKS
    global PENDING_OBSERVE_REQUESTED_X
    global PENDING_OBSERVE_REQUESTED_Y
    global PENDING_OBSERVE_REQUESTED_WIDTH
    global PENDING_OBSERVE_REQUESTED_HEIGHT

    if PENDING_OBSERVE_FRAME_ID <= 0 or PENDING_OBSERVE_TICKS <= 0:
        return
    PENDING_OBSERVE_TICKS -= 1
    if PENDING_OBSERVE_TICKS > 0:
        return

    _log_window_snapshot(
        f"{PENDING_OBSERVE_ACTION} settled",
        PENDING_OBSERVE_FRAME_ID,
        PENDING_OBSERVE_REQUESTED_X,
        PENDING_OBSERVE_REQUESTED_Y,
        PENDING_OBSERVE_REQUESTED_WIDTH,
        PENDING_OBSERVE_REQUESTED_HEIGHT,
    )
    PENDING_OBSERVE_FRAME_ID = 0
    PENDING_OBSERVE_ACTION = ""
    PENDING_OBSERVE_TICKS = 0
    PENDING_OBSERVE_REQUESTED_X = None
    PENDING_OBSERVE_REQUESTED_Y = None
    PENDING_OBSERVE_REQUESTED_WIDTH = None
    PENDING_OBSERVE_REQUESTED_HEIGHT = None


def _refresh_frame_state() -> None:
    global ORIGINAL_FRAME_ID
    global ORIGINAL_FRAME_VISIBLE
    global CREATED_FRAME_ID
    global CREATED_FRAME_VISIBLE

    source_id = int(UIManager.GetFrameIDByLabel(DEVTEXT_LABEL) or 0)
    if source_id > 0 and UIManager.FrameExists(source_id):
        ORIGINAL_FRAME_ID = source_id
        try:
            ORIGINAL_FRAME_VISIBLE = bool(UIManager.GetFrameByID(source_id).is_visible)
        except Exception:
            ORIGINAL_FRAME_VISIBLE = False
    else:
        ORIGINAL_FRAME_ID = 0
        ORIGINAL_FRAME_VISIBLE = False

    clone_id = _find_managed_clone_frame()
    if clone_id > 0:
        CREATED_FRAME_ID = clone_id
        try:
            CREATED_FRAME_VISIBLE = bool(UIManager.GetFrameByID(clone_id).is_visible)
        except Exception:
            CREATED_FRAME_VISIBLE = False
    else:
        CREATED_FRAME_ID = 0
        CREATED_FRAME_VISIBLE = False


def _create_window() -> None:
    global CREATED_FRAME_ID, CREATED_FRAME_VISIBLE, LAST_TEST_STATUS
    global ACTIVE_X, ACTIVE_Y, ACTIVE_WIDTH, ACTIVE_HEIGHT

    frame_id = _find_managed_clone_frame()
    if frame_id > 0:
        CREATED_FRAME_ID = frame_id
        try:
            CREATED_FRAME_VISIBLE = bool(UIManager.GetFrameByID(frame_id).is_visible)
        except Exception:
            CREATED_FRAME_VISIBLE = False
        print(f"[{MODULE_NAME}] create skipped existing frame_id={frame_id} title='{WINDOW_TITLE}'")
        LAST_TEST_STATUS = "window_exists"
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    _log_operation_inputs(
        "window create",
        0,
        TARGET_X,
        TARGET_Y,
        TARGET_WIDTH,
        TARGET_HEIGHT,
        TARGET_X,
        engine_y,
        ACTIVE_X,
        ACTIVE_Y,
        ACTIVE_WIDTH,
        ACTIVE_HEIGHT,
    )
    frame_id = int(
        UIManager.CreateWindow(
            TARGET_X,
            engine_y,
            TARGET_WIDTH,
            TARGET_HEIGHT,
            frame_label=WINDOW_TITLE,
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
        LAST_TEST_STATUS = "window_create_failed"
        return

    ACTIVE_X = TARGET_X
    ACTIVE_Y = TARGET_Y
    ACTIVE_WIDTH = TARGET_WIDTH
    ACTIVE_HEIGHT = TARGET_HEIGHT
    CREATED_FRAME_ID = frame_id
    try:
        CREATED_FRAME_VISIBLE = bool(UIManager.GetFrameByID(frame_id).is_visible)
    except Exception:
        CREATED_FRAME_VISIBLE = False
    print(
        f"[{MODULE_NAME}] window created frame_id={frame_id} title='{WINDOW_TITLE}' "
        f"requested_rect=({TARGET_X}, {TARGET_Y}, {TARGET_WIDTH}, {TARGET_HEIGHT})"
    )
    _log_window_snapshot("window create immediate", frame_id, TARGET_X, TARGET_Y, TARGET_WIDTH, TARGET_HEIGHT)
    _schedule_observation(
        frame_id,
        "window create",
        requested_x=TARGET_X,
        requested_y=TARGET_Y,
        requested_width=TARGET_WIDTH,
        requested_height=TARGET_HEIGHT,
    )
    LAST_TEST_STATUS = "window_created"


def _apply_rect() -> None:
    global CREATED_FRAME_ID, CREATED_FRAME_VISIBLE, LAST_TEST_STATUS
    global ACTIVE_X, ACTIVE_Y, ACTIVE_WIDTH, ACTIVE_HEIGHT

    frame_id = _find_managed_clone_frame()
    if frame_id <= 0:
        LAST_TEST_STATUS = "apply_rect_missing"
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
    _log_operation_inputs(
        "window apply rect",
        frame_id,
        TARGET_X,
        TARGET_Y,
        TARGET_WIDTH,
        TARGET_HEIGHT,
        TARGET_X,
        engine_y,
        ACTIVE_X,
        ACTIVE_Y,
        ACTIVE_WIDTH,
        ACTIVE_HEIGHT,
    )
    _log_window_snapshot("window apply rect before", frame_id, TARGET_X, TARGET_Y, TARGET_WIDTH, TARGET_HEIGHT)
    applied = bool(UIManager.ApplyRect(frame_id, TARGET_X, engine_y, TARGET_WIDTH, TARGET_HEIGHT, flags=TARGET_FLAGS))
    if applied:
        ACTIVE_X = TARGET_X
        ACTIVE_Y = TARGET_Y
        ACTIVE_WIDTH = TARGET_WIDTH
        ACTIVE_HEIGHT = TARGET_HEIGHT
    CREATED_FRAME_ID = frame_id
    try:
        CREATED_FRAME_VISIBLE = bool(UIManager.GetFrameByID(frame_id).is_visible)
    except Exception:
        CREATED_FRAME_VISIBLE = False
    print(
        f"[{MODULE_NAME}] window apply rect frame_id={frame_id} applied={applied} "
        f"requested_rect=({TARGET_X}, {TARGET_Y}, {TARGET_WIDTH}, {TARGET_HEIGHT})"
    )
    _log_window_snapshot("window apply rect after", frame_id, TARGET_X, TARGET_Y, TARGET_WIDTH, TARGET_HEIGHT)
    if applied:
        _schedule_observation(
            frame_id,
            "window apply rect",
            requested_x=TARGET_X,
            requested_y=TARGET_Y,
            requested_width=TARGET_WIDTH,
            requested_height=TARGET_HEIGHT,
        )
    LAST_TEST_STATUS = "window_rect_applied" if applied else "window_rect_apply_failed"


def _move_rect() -> None:
    global CREATED_FRAME_ID, CREATED_FRAME_VISIBLE, LAST_TEST_STATUS
    global ACTIVE_X, ACTIVE_Y

    frame_id = _find_managed_clone_frame()
    if frame_id <= 0:
        LAST_TEST_STATUS = "move_rect_missing"
        return

    engine_y = _to_engine_y_from_top(TARGET_Y, ACTIVE_HEIGHT)
    _log_operation_inputs(
        "window move rect",
        frame_id,
        TARGET_X,
        TARGET_Y,
        ACTIVE_WIDTH,
        ACTIVE_HEIGHT,
        TARGET_X,
        engine_y,
        ACTIVE_X,
        ACTIVE_Y,
        ACTIVE_WIDTH,
        ACTIVE_HEIGHT,
    )
    _log_window_snapshot("window move rect before", frame_id, TARGET_X, TARGET_Y, ACTIVE_WIDTH, ACTIVE_HEIGHT)
    moved = bool(UIManager.MoveRect(frame_id, TARGET_X, engine_y, ACTIVE_WIDTH, ACTIVE_HEIGHT, flags=TARGET_FLAGS))
    if moved:
        ACTIVE_X = TARGET_X
        ACTIVE_Y = TARGET_Y
    CREATED_FRAME_ID = frame_id
    try:
        CREATED_FRAME_VISIBLE = bool(UIManager.GetFrameByID(frame_id).is_visible)
    except Exception:
        CREATED_FRAME_VISIBLE = False
    print(
        f"[{MODULE_NAME}] window move rect frame_id={frame_id} moved={moved} "
        f"requested_pos=({TARGET_X}, {TARGET_Y}) preserved_size=({ACTIVE_WIDTH}, {ACTIVE_HEIGHT})"
    )
    _log_window_snapshot("window move rect after", frame_id, TARGET_X, TARGET_Y, ACTIVE_WIDTH, ACTIVE_HEIGHT)
    if moved:
        _schedule_observation(
            frame_id,
            "window move rect",
            requested_x=TARGET_X,
            requested_y=TARGET_Y,
            requested_width=ACTIVE_WIDTH,
            requested_height=ACTIVE_HEIGHT,
        )
    LAST_TEST_STATUS = "window_rect_moved" if moved else "window_rect_move_failed"


def _resize_rect() -> None:
    global CREATED_FRAME_ID, CREATED_FRAME_VISIBLE, LAST_TEST_STATUS
    global ACTIVE_WIDTH, ACTIVE_HEIGHT

    frame_id = _find_managed_clone_frame()
    if frame_id <= 0:
        LAST_TEST_STATUS = "resize_rect_missing"
        return

    engine_y = _to_engine_y_from_top(ACTIVE_Y, TARGET_HEIGHT)
    _log_operation_inputs(
        "window resize rect",
        frame_id,
        ACTIVE_X,
        ACTIVE_Y,
        TARGET_WIDTH,
        TARGET_HEIGHT,
        ACTIVE_X,
        engine_y,
        ACTIVE_X,
        ACTIVE_Y,
        ACTIVE_WIDTH,
        ACTIVE_HEIGHT,
    )
    _log_window_snapshot("window resize rect before", frame_id, requested_width=TARGET_WIDTH, requested_height=TARGET_HEIGHT)
    resized = bool(UIManager.ResizeRect(frame_id, TARGET_WIDTH, TARGET_HEIGHT, ACTIVE_X, engine_y, flags=TARGET_FLAGS))
    if resized:
        ACTIVE_WIDTH = TARGET_WIDTH
        ACTIVE_HEIGHT = TARGET_HEIGHT
    CREATED_FRAME_ID = frame_id
    try:
        CREATED_FRAME_VISIBLE = bool(UIManager.GetFrameByID(frame_id).is_visible)
    except Exception:
        CREATED_FRAME_VISIBLE = False
    print(
        f"[{MODULE_NAME}] window resize rect frame_id={frame_id} resized={resized} "
        f"requested_size=({TARGET_WIDTH}, {TARGET_HEIGHT}) preserved_pos=({ACTIVE_X}, {ACTIVE_Y})"
    )
    _log_window_snapshot("window resize rect after", frame_id, requested_width=TARGET_WIDTH, requested_height=TARGET_HEIGHT)
    if resized:
        _schedule_observation(
            frame_id,
            "window resize rect",
            requested_width=TARGET_WIDTH,
            requested_height=TARGET_HEIGHT,
        )
    LAST_TEST_STATUS = "window_rect_resized" if resized else "window_rect_resize_failed"


def _close_window() -> None:
    global CREATED_FRAME_ID, CREATED_FRAME_VISIBLE, LAST_TEST_STATUS
    hidden = bool(UIManager.HideWindowByLabel(WINDOW_TITLE))
    if hidden:
        CREATED_FRAME_ID = 0
        CREATED_FRAME_VISIBLE = False
        print(f"[{MODULE_NAME}] window close title='{WINDOW_TITLE}'")
        LAST_TEST_STATUS = "window_closed"
    else:
        LAST_TEST_STATUS = "window_close_failed"


def draw_debug_outlines() -> None:
    global DRAW_OUTLINES
    _refresh_frame_state()
    _observe_pending_action()
    if not DRAW_OUTLINES:
        return

    ui = UIManager()
    if ORIGINAL_FRAME_ID > 0 and UIManager.FrameExists(ORIGINAL_FRAME_ID):
        ui.DrawFrame(ORIGINAL_FRAME_ID, ORIGINAL_FILL_COLOR)
        outline = ORIGINAL_OUTLINE_COLOR if ORIGINAL_FRAME_VISIBLE else 0xFFAAAAAA
        ui.DrawFrameOutline(ORIGINAL_FRAME_ID, outline, 4.0)

    if CREATED_FRAME_ID > 0 and UIManager.FrameExists(CREATED_FRAME_ID):
        ui.DrawFrame(CREATED_FRAME_ID, CREATED_FILL_COLOR)
        outline = CREATED_OUTLINE_COLOR if CREATED_FRAME_VISIBLE else 0xFFAAAAAA
        ui.DrawFrameOutline(CREATED_FRAME_ID, outline, 6.0)


def draw() -> None:
    global DRAW_OUTLINES
    global WINDOW_TITLE
    global TARGET_X
    global TARGET_Y
    global TARGET_WIDTH
    global TARGET_HEIGHT
    global TARGET_FLAGS

    PyImGui.text("Rect")
    PyImGui.separator()
    PyImGui.text("This harness uses the base rect helpers directly.")
    PyImGui.text("Input coords use top-left origin.")
    WINDOW_TITLE = str(PyImGui.input_text("Window Title", WINDOW_TITLE))
    TARGET_X = float(PyImGui.input_float("X", float(TARGET_X)))
    TARGET_Y = float(PyImGui.input_float("Y From Top", float(TARGET_Y)))
    TARGET_WIDTH = float(PyImGui.input_float("Width", float(TARGET_WIDTH)))
    TARGET_HEIGHT = float(PyImGui.input_float("Height", float(TARGET_HEIGHT)))
    TARGET_FLAGS = int(PyImGui.input_int("Flags", int(TARGET_FLAGS)))

    if TARGET_FLAGS < 0:
        TARGET_FLAGS = 0

    if PyImGui.button("Create"):
        Py4GW.Game.enqueue(_create_window)
    if PyImGui.button("Apply Rect"):
        Py4GW.Game.enqueue(_apply_rect)
    if PyImGui.button("Move Rect"):
        Py4GW.Game.enqueue(_move_rect)
    if PyImGui.button("Resize Rect"):
        Py4GW.Game.enqueue(_resize_rect)
    if PyImGui.button("Close"):
        Py4GW.Game.enqueue(_close_window)

    DRAW_OUTLINES = PyImGui.checkbox("Draw Outlines", DRAW_OUTLINES)

    PyImGui.text(f"Last status: {LAST_TEST_STATUS}")
    PyImGui.text(f"Source DevText: {ORIGINAL_FRAME_ID} visible={ORIGINAL_FRAME_VISIBLE}")
    PyImGui.text(f"Managed Window: {WINDOW_TITLE}")
    PyImGui.text(f"Managed Frame: {CREATED_FRAME_ID} visible={CREATED_FRAME_VISIBLE}")
    PyImGui.text(f"Target Rect (top-left): ({TARGET_X}, {TARGET_Y}, {TARGET_WIDTH}, {TARGET_HEIGHT}) flags=0x{TARGET_FLAGS:X}")
    PyImGui.text(f"Active Rect (top-left intent): ({ACTIVE_X}, {ACTIVE_Y}, {ACTIVE_WIDTH}, {ACTIVE_HEIGHT})")
