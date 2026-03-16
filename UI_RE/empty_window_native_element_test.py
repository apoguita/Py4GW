import time

import Py4GW
import PyImGui

from Py4GWCoreLib import GWContext, UIManager
from Py4GWCoreLib.enums_src.UI_enums import ControlAction
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "Empty Window Native Element Test"
SCRIPT_REVISION = "2026-03-08-empty-window-native-element-test-1"
WINDOW_OPEN = True
INITIALIZED = False

FRAME_LABEL = "PyEmptyWindowNativeElementTest"
COMPONENT_LABEL = "PyEmptyWindowInventoryClone"
TARGET_X = 0.0
TARGET_Y = 0.0
TARGET_WIDTH = 220.0
TARGET_HEIGHT = 260.0
TARGET_FLAGS = 0x6
READ_DELAY_SECONDS = 0.50
TARGET_CHILD_OFFSET = 0xFFF1
USE_FREE_CHILD_SLOT = True
CREATED_FRAME_ID = 0
LAST_STATUS = "idle"
PENDING_REPORTS: list[tuple[float, str]] = []
HYBRID_STUFFED_CHILD_OFFSET = 0xFFF1
USE_FREE_STUFFED_CHILD_SLOT = True

TARGET_PARENT_MODES = [
    ("root[0]", "first child under cloned window root"),
    ("clear boundary parent", "parent of root[0][0]"),
    ("clear boundary", "root[0][0] after empty-window trim"),
    ("root[0][0][0]", "legacy observed-host path before trim"),
    ("view root", "parent of observed host"),
    ("observed host", "resolved host frame"),
    ("window root", "top-level cloned window root"),
]
TARGET_PARENT_MODE_INDEX = 0


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


def _frame_exists(frame_id: int) -> bool:
    if frame_id <= 0:
        return False
    try:
        return int(frame_id) in set(int(fid) for fid in UIManager.GetFrameArray())
    except Exception:
        return False


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


def _get_viewport_height() -> float:
    root_frame_id = UIManager.GetRootFrameID()
    _, viewport_height = UIManager.GetViewportDimensions(root_frame_id)
    return float(viewport_height)


def _to_engine_y_from_top(y_from_top: float, height: float) -> float:
    return _get_viewport_height() - float(y_from_top) - float(height)


def _find_window() -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(FRAME_LABEL) or 0)
    if frame_id > 0 and _frame_exists(frame_id):
        return frame_id
    return 0


def _inventory_root() -> int:
    return int(UIManager.GetFrameIDByLabel("Inventory") or 0)


def _game_root() -> int:
    return int(UIManager.GetFrameIDByLabel("Game") or 0)


def _game_child6() -> int:
    root = _game_root()
    if root <= 0:
        return 0
    return int(UIManager.GetChildFrameByFrameId(root, 6) or 0)


def _created_root() -> int:
    if CREATED_FRAME_ID > 0 and _frame_exists(CREATED_FRAME_ID):
        return int(CREATED_FRAME_ID)
    return 0


def _window_clear_boundary() -> int:
    root = _find_window()
    if root <= 0:
        return 0
    return int(GWUI.ResolveEmptyWindowClearBoundaryByFrameId(root) or 0)


def _safe_child(frame_id: int, child_offset: int) -> int:
    if frame_id <= 0:
        return 0
    return int(UIManager.GetChildFrameByFrameId(frame_id, child_offset) or 0)


def _window_root_child0() -> int:
    return _safe_child(_find_window(), 0)


def _window_clear_boundary_parent() -> int:
    clear_boundary = _window_clear_boundary()
    if clear_boundary <= 0:
        return 0
    return int(UIManager.GetParentID(clear_boundary) or 0)


def _window_interior_rect() -> tuple[int, int, int, int]:
    root0 = _window_root_child0()
    if root0 > 0:
        return UIManager.GetFrameCoords(root0)
    root = _find_window()
    if root > 0:
        return UIManager.GetContentFrameCoords(root)
    return (0, 0, 0, 0)


def _window_host() -> int:
    root = _find_window()
    if root <= 0:
        return 0
    host = int(GWUI.ResolveObservedContentHostByFrameId(root) or 0)
    if host > 0:
        return host
    return _safe_child(_safe_child(_window_root_child0(), 0), 0)


def _window_view_root() -> int:
    host = _window_host()
    if host <= 0:
        return 0
    return int(UIManager.GetParentID(host) or 0)


def _target_parent() -> int:
    if TARGET_PARENT_MODE_INDEX == 0:
        return _window_root_child0()
    if TARGET_PARENT_MODE_INDEX == 1:
        return _window_clear_boundary_parent()
    if TARGET_PARENT_MODE_INDEX == 2:
        return _window_clear_boundary()
    if TARGET_PARENT_MODE_INDEX == 3:
        return _safe_child(_safe_child(_window_root_child0(), 0), 0)
    if TARGET_PARENT_MODE_INDEX == 4:
        return _window_view_root()
    if TARGET_PARENT_MODE_INDEX == 5:
        return _window_host()
    if TARGET_PARENT_MODE_INDEX == 6:
        return _find_window()
    return 0


def _resolved_child_offset(parent_id: int) -> int:
    if parent_id <= 0:
        return 0
    if USE_FREE_CHILD_SLOT:
        return int(GWUI.FindAvailableChildSlot(parent_id, 0x20, 0xFE) or 0)
    return int(TARGET_CHILD_OFFSET)


def _open_inventory() -> None:
    def _invoke() -> None:
        UIManager.Keypress(ControlAction.ControlAction_ToggleInventoryWindow.value, 0)

    Py4GW.Game.enqueue(_invoke)
    _log("open inventory enqueued")
    _schedule_report("state after open inventory")


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

    def _invoke() -> None:
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
        _log(
            f"create empty invoke result frame_id={frame_id} "
            f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT})"
        )

    Py4GW.Game.enqueue(_invoke)
    LAST_STATUS = "create empty window enqueued"
    _log(LAST_STATUS)
    _schedule_report("state after empty create")


def _destroy_created_component() -> None:
    global CREATED_FRAME_ID
    global LAST_STATUS

    frame_id = _created_root()
    if frame_id <= 0:
        LAST_STATUS = "created component missing"
        _log(LAST_STATUS)
        return

    def _invoke() -> None:
        GWUI.DestroyUIComponentByFrameId(frame_id)
        parent_id = _target_parent()
        if parent_id > 0:
            GWUI.TriggerFrameRedrawByFrameId(parent_id)
        root = _find_window()
        if root > 0:
            GWUI.TriggerFrameRedrawByFrameId(root)

    Py4GW.Game.enqueue(_invoke)
    CREATED_FRAME_ID = 0
    LAST_STATUS = f"destroy created component frame_id={frame_id}"
    _log(LAST_STATUS)
    _schedule_report("state after destroy created component")


def _create_inventory_contract_component() -> None:
    global CREATED_FRAME_ID
    global LAST_STATUS

    parent_mode_name = TARGET_PARENT_MODES[TARGET_PARENT_MODE_INDEX][0]

    def _invoke() -> None:
        global CREATED_FRAME_ID
        parent_id = _target_parent()
        source_frame_id = _inventory_root()
        child_offset = _resolved_child_offset(parent_id)
        if parent_id <= 0:
            _log("create component invoke aborted: target parent unavailable")
            CREATED_FRAME_ID = 0
            return
        if source_frame_id <= 0:
            _log("create component invoke aborted: inventory source unavailable")
            CREATED_FRAME_ID = 0
            return
        if child_offset <= 0:
            _log(f"create component invoke aborted: no child slot available for parent={parent_id}")
            CREATED_FRAME_ID = 0
            return
        CREATED_FRAME_ID = int(
            GWUI.CreateUIComponentFromSourceFrameByFrameId(
                parent_id,
                source_frame_id,
                0x20,
                child_offset,
                COMPONENT_LABEL,
                reattach_remaining_callbacks=True,
                trigger_redraw=False,
            )
            or 0
        )
        _log(
            f"create component invoke result created_frame_id={CREATED_FRAME_ID} "
            f"parent={parent_id} source={source_frame_id} child_offset=0x{child_offset:X}"
        )
        if CREATED_FRAME_ID > 0:
            created7 = int(UIManager.GetChildFrameByFrameId(CREATED_FRAME_ID, 7) or 0)
            created9 = int(UIManager.GetChildFrameByFrameId(CREATED_FRAME_ID, 9) or 0)
            if created7 > 0:
                GWUI.TriggerFrameRedrawByFrameId(created7)
            if created9 > 0:
                GWUI.TriggerFrameRedrawByFrameId(created9)
            GWUI.TriggerFrameRedrawByFrameId(CREATED_FRAME_ID)
        GWUI.TriggerFrameRedrawByFrameId(parent_id)
        root = _find_window()
        if root > 0:
            GWUI.TriggerFrameRedrawByFrameId(root)

    Py4GW.Game.enqueue(_invoke)
    LAST_STATUS = f"create component enqueued parent_mode='{parent_mode_name}'"
    _log(LAST_STATUS)
    _schedule_report("state after create component")


def _create_stuffed_inventory_clone() -> None:
    global CREATED_FRAME_ID
    global LAST_STATUS

    def _invoke() -> None:
        global CREATED_FRAME_ID
        source_frame_id = _inventory_root()
        parent_id = _game_child6()
        child_offset = int(HYBRID_STUFFED_CHILD_OFFSET)

        if source_frame_id <= 0:
            _log("stuff invoke aborted: inventory source unavailable")
            CREATED_FRAME_ID = 0
            return
        if parent_id <= 0:
            _log("stuff invoke aborted: Game[6] unavailable")
            CREATED_FRAME_ID = 0
            return
        if USE_FREE_STUFFED_CHILD_SLOT:
            child_offset = int(GWUI.FindAvailableChildSlot(parent_id, 0x20, 0xFE) or 0)
        if child_offset <= 0:
            _log(f"stuff invoke aborted: no child slot available for parent={parent_id}")
            CREATED_FRAME_ID = 0
            return

        CREATED_FRAME_ID = int(
            GWUI.CreateUIComponentFromSourceFrameByFrameId(
                parent_id,
                source_frame_id,
                0x20,
                child_offset,
                COMPONENT_LABEL,
                reattach_remaining_callbacks=True,
                trigger_redraw=False,
            )
            or 0
        )
        _log(
            f"stuff create invoke result created_frame_id={CREATED_FRAME_ID} "
            f"parent={parent_id} source={source_frame_id} child_offset=0x{child_offset:X}"
        )
        if CREATED_FRAME_ID > 0:
            GWUI.TriggerFrameRedrawByFrameId(CREATED_FRAME_ID)
            GWUI.TriggerFrameRedrawByFrameId(parent_id)

    Py4GW.Game.enqueue(_invoke)
    LAST_STATUS = "stuff inventory clone create enqueued"
    _log(LAST_STATUS)
    _schedule_report("state after stuff inventory clone")


def _fit_created_clone_to_empty_window() -> None:
    global LAST_STATUS

    def _invoke() -> None:
        created_id = _created_root()
        shell_root = _find_window()
        left, top, right, bottom = _window_interior_rect()
        width = max(0, int(right - left))
        height = max(0, int(bottom - top))

        if created_id <= 0:
            _log("fit invoke aborted: created component missing")
            return
        if shell_root <= 0:
            _log("fit invoke aborted: empty window missing")
            return
        if width <= 0 or height <= 0:
            _log(f"fit invoke aborted: window interior rect invalid rect=({left},{top})-({right},{bottom})")
            return

        rect_result = bool(
            UIManager.SetFrameRect(
                created_id,
                float(left),
                float(top),
                float(width),
                float(height),
                flags=None,
                disable_center=True,
            )
        )
        _log(
            f"fit invoke rect result={rect_result} "
            f"created={created_id} rect=({left},{top}) size=({width},{height})"
        )
        created7 = int(UIManager.GetChildFrameByFrameId(created_id, 7) or 0)
        created9 = int(UIManager.GetChildFrameByFrameId(created_id, 9) or 0)
        if created7 > 0:
            GWUI.TriggerFrameRedrawByFrameId(created7)
        if created9 > 0:
            GWUI.TriggerFrameRedrawByFrameId(created9)
        GWUI.TriggerFrameRedrawByFrameId(created_id)
        GWUI.TriggerFrameRedrawByFrameId(shell_root)

    Py4GW.Game.enqueue(_invoke)
    LAST_STATUS = "fit created clone to empty window enqueued"
    _log(LAST_STATUS)
    _schedule_report("state after fit created clone")


def _dump_state(prefix: str) -> None:
    root = _find_window()
    root0 = _window_root_child0()
    boundary = _window_clear_boundary()
    boundary_parent = _window_clear_boundary_parent()
    root0_0 = _safe_child(root0, 0)
    root0_0_0 = _safe_child(root0_0, 0)
    view_root = _window_view_root()
    host = _window_host()
    target_parent = _target_parent()
    inventory = _inventory_root()
    created = _created_root()
    created7 = int(UIManager.GetChildFrameByFrameId(created, 7) or 0) if created > 0 else 0
    created9 = int(UIManager.GetChildFrameByFrameId(created, 9) or 0) if created > 0 else 0
    game = _game_root()
    game6 = _game_child6()
    interior_left, interior_top, interior_right, interior_bottom = _window_interior_rect()

    _log(
        f"{prefix} "
        f"game=({_frame_summary(game)}) "
        f"game[6]=({_frame_summary(game6)}) "
        f"window_root=({_frame_summary(root)}) "
        f"root[0]=({_frame_summary(root0)}) "
        f"root[0][0]=({_frame_summary(root0_0)}) "
        f"root[0][0][0]=({_frame_summary(root0_0_0)}) "
        f"clear_boundary_parent=({_frame_summary(boundary_parent)}) "
        f"clear_boundary=({_frame_summary(boundary)}) "
        f"view_root=({_frame_summary(view_root)}) "
        f"host=({_frame_summary(host)}) "
        f"target_parent=({_frame_summary(target_parent)}) "
        f"window_interior=({interior_left},{interior_top})-({interior_right},{interior_bottom}) "
        f"inventory=({_frame_summary(inventory)}) "
        f"created=({_frame_summary(created)}) "
        f"created[7]=({_frame_summary(created7)}) "
        f"created[9]=({_frame_summary(created9)})"
    )


def _draw_parent_mode_selector() -> None:
    global TARGET_PARENT_MODE_INDEX

    PyImGui.text("target parent mode:")
    for index, (name, description) in enumerate(TARGET_PARENT_MODES):
        TARGET_PARENT_MODE_INDEX = int(
            PyImGui.radio_button(
                f"{name}##parent_mode_{index}",
                int(TARGET_PARENT_MODE_INDEX),
                int(index),
            )
        )
        if description:
            PyImGui.same_line(0.0, 8.0)
            PyImGui.text_disabled(description)


def _draw_window() -> None:
    global WINDOW_OPEN
    global READ_DELAY_SECONDS
    global TARGET_CHILD_OFFSET
    global USE_FREE_CHILD_SLOT
    global HYBRID_STUFFED_CHILD_OFFSET
    global USE_FREE_STUFFED_CHILD_SLOT

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("goal: insert a native family-contracted component into a cloned empty window")
    PyImGui.separator()
    PyImGui.text("flow:")
    PyImGui.text("1) Open Inventory")
    PyImGui.text("2) Create Empty Window")
    PyImGui.text("3) Pick the candidate parent layer")
    PyImGui.text("4) Create Inventory-Contract Component or Stuff Inventory Clone")
    PyImGui.text("5) Fit created clone to empty window")
    PyImGui.text("6) Dump State")
    PyImGui.separator()

    READ_DELAY_SECONDS = float(
        _normalize_input_int(
            PyImGui.input_int("Read Delay (ms)", int(READ_DELAY_SECONDS * 1000.0)),
            int(READ_DELAY_SECONDS * 1000.0),
        )
    ) / 1000.0
    TARGET_CHILD_OFFSET = _normalize_input_int(
        PyImGui.input_int("Child Offset", TARGET_CHILD_OFFSET),
        TARGET_CHILD_OFFSET,
    )
    HYBRID_STUFFED_CHILD_OFFSET = _normalize_input_int(
        PyImGui.input_int("Stuffed Child Offset", HYBRID_STUFFED_CHILD_OFFSET),
        HYBRID_STUFFED_CHILD_OFFSET,
    )
    USE_FREE_CHILD_SLOT = PyImGui.checkbox("Use Free Child Slot", USE_FREE_CHILD_SLOT)
    USE_FREE_STUFFED_CHILD_SLOT = PyImGui.checkbox("Use Free Stuffed Child Slot", USE_FREE_STUFFED_CHILD_SLOT)

    _draw_parent_mode_selector()
    PyImGui.separator()

    if PyImGui.button("Open Inventory"):
        _open_inventory()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Create Empty Window"):
        _create_empty_window()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Create Inventory-Contract Component"):
        _create_inventory_contract_component()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Stuff Inventory Clone Into Empty Window"):
        _create_stuffed_inventory_clone()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Fit Created Clone To Empty Window"):
        _fit_created_clone_to_empty_window()

    if PyImGui.button("Destroy Created Component"):
        _destroy_created_component()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Dump State"):
        _dump_state("manual state report")

    PyImGui.separator()
    PyImGui.text(f"last_status={LAST_STATUS}")
    PyImGui.text(f"game={_game_root()}")
    PyImGui.text(f"game[6]={_game_child6()}")
    PyImGui.text(f"window_root={_find_window()}")
    PyImGui.text(f"root[0]={_window_root_child0()}")
    PyImGui.text(f"clear_boundary_parent={_window_clear_boundary_parent()}")
    PyImGui.text(f"clear_boundary={_window_clear_boundary()}")
    PyImGui.text(f"view_root={_window_view_root()}")
    PyImGui.text(f"host={_window_host()}")
    PyImGui.text(f"target_parent={_target_parent()}")
    PyImGui.text(
        f"resolved_child_offset=0x{_resolved_child_offset(_target_parent()):X}"
        if _resolved_child_offset(_target_parent()) > 0
        else "resolved_child_offset=unavailable"
    )
    left, top, right, bottom = _window_interior_rect()
    PyImGui.text(f"window_interior=({left},{top})-({right},{bottom})")
    PyImGui.text(f"inventory={_inventory_root()}")
    PyImGui.text(f"created={_created_root()}")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("test flow:")
        _log("1) click 'Open Inventory'")
        _log("2) click 'Create Empty Window'")
        _log("3) select a target parent mode")
        _log("4) click 'Create Inventory-Contract Component'")
        _log("5) wait for 'state after create component'")
    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
