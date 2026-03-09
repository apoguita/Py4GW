import time

import Py4GW
import PyImGui

from Py4GWCoreLib import GWContext, UIManager
from Py4GWCoreLib.enums_src.UI_enums import ControlAction
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "Inventory Into Empty DevText Clone Test"
SCRIPT_REVISION = "2026-03-08-inventory-into-empty-devtext-clone-test-1"
WINDOW_OPEN = True
INITIALIZED = False

READ_DELAY_SECONDS = 0.50
CLONE_LABEL = "PyInventoryIntoEmptyDevTextClone"
TARGET_X = 0.0
TARGET_Y = 0.0
TARGET_WIDTH = 220.0
TARGET_HEIGHT = 260.0
TARGET_FLAGS = 0x6
TARGET_CHILD_OFFSET = 0x20
USE_FREE_CHILD_SLOT = True
CREATED_FRAME_ID = 0
LAST_STATUS = "idle"
PENDING_REPORTS: list[tuple[float, str]] = []

TARGET_PARENT_MODES = [
    ("clone root", "empty DevText clone root"),
    ("root[0]", "first child under empty clone root"),
    ("root[0][0]", "trim boundary child"),
    ("view root", "parent of observed host"),
    ("observed host", "resolved content host"),
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


def _safe_child(frame_id: int, child_offset: int) -> int:
    if frame_id <= 0:
        return 0
    return int(UIManager.GetChildFrameByFrameId(frame_id, child_offset) or 0)


def _frame_exists(frame_id: int) -> bool:
    if frame_id <= 0:
        return False
    try:
        return int(frame_id) in set(int(fid) for fid in UIManager.GetFrameArray())
    except Exception:
        return False


def _get_viewport_height() -> float:
    root_frame_id = UIManager.GetRootFrameID()
    _, viewport_height = UIManager.GetViewportDimensions(root_frame_id)
    return float(viewport_height)


def _to_engine_y_from_top(y_from_top: float, height: float) -> float:
    return _get_viewport_height() - float(y_from_top) - float(height)


def _open_inventory() -> None:
    def _invoke() -> None:
        UIManager.Keypress(ControlAction.ControlAction_ToggleInventoryWindow.value, 0)

    Py4GW.Game.enqueue(_invoke)
    _log("open inventory enqueued")
    _schedule_report("state after open inventory")


def _ensure_devtext() -> None:
    def _invoke() -> None:
        frame_id = int(GWUI.OpenDevTextWindow() or 0)
        _log(f"ensure devtext invoke result frame_id={frame_id}")

    Py4GW.Game.enqueue(_invoke)
    _log("ensure devtext enqueued")
    _schedule_report("state after ensure devtext")


def _create_empty_clone() -> None:
    global LAST_STATUS

    existing = _clone_root()
    if existing > 0:
        LAST_STATUS = f"clone exists frame_id={existing}"
        _log(LAST_STATUS)
        return
    if GWContext.Char.GetContext() is None:
        LAST_STATUS = "char_context_unavailable"
        _log(LAST_STATUS)
        return

    def _invoke() -> None:
        engine_y = _to_engine_y_from_top(TARGET_Y, TARGET_HEIGHT)
        frame_id = int(
            GWUI.CreateEmptyWindow(
                TARGET_X,
                engine_y,
                TARGET_WIDTH,
                TARGET_HEIGHT,
                frame_label=CLONE_LABEL,
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
            f"create empty clone invoke result frame_id={frame_id} "
            f"pos=({TARGET_X},{TARGET_Y}) size=({TARGET_WIDTH},{TARGET_HEIGHT})"
        )

    Py4GW.Game.enqueue(_invoke)
    LAST_STATUS = "create empty clone enqueued"
    _log(LAST_STATUS)
    _schedule_report("state after create empty clone")


def _inventory_root() -> int:
    return int(UIManager.GetFrameIDByLabel("Inventory") or 0)


def _clone_root() -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(CLONE_LABEL) or 0)
    if frame_id > 0 and _frame_exists(frame_id):
        return frame_id
    return 0


def _clone_root0() -> int:
    return _safe_child(_clone_root(), 0)


def _clone_root0_0() -> int:
    return _safe_child(_clone_root0(), 0)


def _clone_host() -> int:
    root = _clone_root()
    if root <= 0:
        return 0
    host = int(GWUI.ResolveObservedContentHostByFrameId(root) or 0)
    if host > 0:
        return host
    return _safe_child(_clone_root0_0(), 0)


def _clone_view_root() -> int:
    host = _clone_host()
    if host <= 0:
        return 0
    return int(UIManager.GetParentID(host) or 0)


def _target_parent() -> int:
    if TARGET_PARENT_MODE_INDEX == 0:
        return _clone_root()
    if TARGET_PARENT_MODE_INDEX == 1:
        return _clone_root0()
    if TARGET_PARENT_MODE_INDEX == 2:
        return _clone_root0_0()
    if TARGET_PARENT_MODE_INDEX == 3:
        return _clone_view_root()
    if TARGET_PARENT_MODE_INDEX == 4:
        return _clone_host()
    return 0


def _resolved_child_offset(parent_id: int) -> int:
    if parent_id <= 0:
        return 0
    if USE_FREE_CHILD_SLOT:
        return int(GWUI.FindAvailableChildSlot(parent_id, 0x20, 0xFE) or 0)
    return int(TARGET_CHILD_OFFSET)


def _create_inventory_into_empty_clone() -> None:
    global CREATED_FRAME_ID
    global LAST_STATUS

    parent_mode_name = TARGET_PARENT_MODES[TARGET_PARENT_MODE_INDEX][0]

    def _invoke() -> None:
        global CREATED_FRAME_ID
        source_frame_id = _inventory_root()
        parent_id = _target_parent()
        child_offset = _resolved_child_offset(parent_id)
        if source_frame_id <= 0:
            CREATED_FRAME_ID = 0
            _log("create invoke aborted: inventory source unavailable")
            return
        if parent_id <= 0:
            CREATED_FRAME_ID = 0
            _log("create invoke aborted: empty clone target parent unavailable")
            return
        if child_offset <= 0:
            CREATED_FRAME_ID = 0
            _log(f"create invoke aborted: no child slot available for parent={parent_id}")
            return

        CREATED_FRAME_ID = int(
            GWUI.CreateUIComponentFromSourceFrameByFrameId(
                parent_id,
                source_frame_id,
                0x20,
                child_offset,
                "PyInventoryIntoEmptyDevTextClone",
                reattach_remaining_callbacks=True,
                trigger_redraw=False,
            )
            or 0
        )
        _log(
            f"create invoke result created_frame_id={CREATED_FRAME_ID} "
            f"parent={parent_id} child_offset=0x{child_offset:X} mode='{parent_mode_name}'"
        )
        if CREATED_FRAME_ID > 0:
            GWUI.TriggerFrameRedrawByFrameId(CREATED_FRAME_ID)
            GWUI.TriggerFrameRedrawByFrameId(parent_id)

    Py4GW.Game.enqueue(_invoke)
    LAST_STATUS = f"create inventory into empty devtext clone enqueued mode='{parent_mode_name}'"
    _log(LAST_STATUS)
    _schedule_report("state after create inventory into empty devtext clone")


def _dump_state(prefix: str) -> None:
    inventory = _inventory_root()
    root = _clone_root()
    root0 = _clone_root0()
    root0_0 = _clone_root0_0()
    view_root = _clone_view_root()
    host = _clone_host()
    target_parent = _target_parent()
    created = int(CREATED_FRAME_ID or 0)
    _log(
        f"{prefix} "
        f"inventory=({_frame_summary(inventory)}) "
        f"clone_root=({_frame_summary(root)}) "
        f"root[0]=({_frame_summary(root0)}) "
        f"root[0][0]=({_frame_summary(root0_0)}) "
        f"view_root=({_frame_summary(view_root)}) "
        f"host=({_frame_summary(host)}) "
        f"target_parent=({_frame_summary(target_parent)}) "
        f"created=({_frame_summary(created)})"
    )


def _draw_parent_mode_selector() -> None:
    global TARGET_PARENT_MODE_INDEX

    PyImGui.text("target parent mode:")
    for index, (name, description) in enumerate(TARGET_PARENT_MODES):
        TARGET_PARENT_MODE_INDEX = int(
            PyImGui.radio_button(
                f"{name}##empty_clone_parent_mode_{index}",
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

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("goal: test whether an empty DevText clone can host the same inventory contract as a raw DevText clone")
    PyImGui.separator()
    PyImGui.text("flow:")
    PyImGui.text("1) Open Inventory")
    PyImGui.text("2) Ensure DevText")
    PyImGui.text("3) Create Empty Clone")
    PyImGui.text("4) Pick the empty-clone parent layer")
    PyImGui.text("5) Create Inventory Into Empty DevText Clone")
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
    USE_FREE_CHILD_SLOT = PyImGui.checkbox("Use Free Child Slot", USE_FREE_CHILD_SLOT)

    _draw_parent_mode_selector()
    PyImGui.separator()

    if PyImGui.button("Open Inventory"):
        _open_inventory()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Ensure DevText"):
        _ensure_devtext()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Create Empty Clone"):
        _create_empty_clone()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Create Inventory Into Empty DevText Clone"):
        _create_inventory_into_empty_clone()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Dump State"):
        _dump_state("manual state report")

    PyImGui.separator()
    PyImGui.text(f"last_status={LAST_STATUS}")
    PyImGui.text(f"inventory={_inventory_root()}")
    PyImGui.text(f"clone_root={_clone_root()}")
    PyImGui.text(f"root[0]={_clone_root0()}")
    PyImGui.text(f"root[0][0]={_clone_root0_0()}")
    PyImGui.text(f"view_root={_clone_view_root()}")
    PyImGui.text(f"host={_clone_host()}")
    PyImGui.text(f"target_parent={_target_parent()}")
    PyImGui.text(
        f"resolved_child_offset=0x{_resolved_child_offset(_target_parent()):X}"
        if _resolved_child_offset(_target_parent()) > 0
        else "resolved_child_offset=unavailable"
    )
    PyImGui.text(f"created={int(CREATED_FRAME_ID or 0)}")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("test flow:")
        _log("1) click 'Open Inventory'")
        _log("2) click 'Ensure DevText'")
        _log("3) click 'Create Empty Clone'")
        _log("4) pick an empty-clone parent mode")
        _log("5) click 'Create Inventory Into Empty DevText Clone'")
    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
