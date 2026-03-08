import time

import Py4GW
import PyImGui

from Py4GWCoreLib import GWContext, UIManager
from Py4GWCoreLib.enums_src.UI_enums import ControlAction


MODULE_NAME = "Helper Frame Callback Graft Test"
SCRIPT_REVISION = "2026-03-08-helper-frame-callback-graft-test-1"
WINDOW_OPEN = True
INITIALIZED = False

READ_DELAY_SECONDS = 0.50
CLONE_LABEL = "PyHelperFrameHostClone"
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

HELPER_TYPES = [
    ("button", "CreateButtonFrameByFrameId"),
    ("checkbox", "CreateCheckboxFrameByFrameId"),
    ("text label", "CreateTextLabelFrameByFrameId"),
    ("scrollable", "CreateScrollableFrameByFrameId"),
]
HELPER_TYPE_INDEX = 0

DONOR_MODES = [
    ("none", "no callback grafting"),
    ("target parent", "copy callbacks from the selected host parent"),
    ("inventory root", "copy callbacks from the Inventory root"),
    ("devtext root", "copy callbacks from the original DevText root"),
]
DONOR_MODE_INDEX = 0

TARGET_PARENT_MODES = [
    ("clone root", "empty clone root"),
    ("root[0]", "first child under empty clone root"),
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
        frame_id = int(UIManager.OpenDevTextWindow() or 0)
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
            UIManager.CreateEmptyWindow(
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


def _devtext_root() -> int:
    return int(UIManager.GetDevTextFrameID() or 0)


def _clone_root() -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(CLONE_LABEL) or 0)
    if frame_id > 0 and _frame_exists(frame_id):
        return frame_id
    return 0


def _clone_root0() -> int:
    return _safe_child(_clone_root(), 0)


def _target_parent() -> int:
    if TARGET_PARENT_MODE_INDEX == 0:
        return _clone_root()
    if TARGET_PARENT_MODE_INDEX == 1:
        return _clone_root0()
    return 0


def _resolved_child_offset(parent_id: int) -> int:
    if parent_id <= 0:
        return 0
    if USE_FREE_CHILD_SLOT:
        return int(UIManager.FindAvailableChildSlot(parent_id, 0x20, 0xFE) or 0)
    return int(TARGET_CHILD_OFFSET)


def _callback_donor_frame() -> int:
    if DONOR_MODE_INDEX == 0:
        return 0
    if DONOR_MODE_INDEX == 1:
        return _target_parent()
    if DONOR_MODE_INDEX == 2:
        return _inventory_root()
    if DONOR_MODE_INDEX == 3:
        return _devtext_root()
    return 0


def _create_helper_frame_on_clone() -> None:
    global CREATED_FRAME_ID
    global LAST_STATUS

    helper_name = HELPER_TYPES[HELPER_TYPE_INDEX][0]
    parent_mode_name = TARGET_PARENT_MODES[TARGET_PARENT_MODE_INDEX][0]
    donor_mode_name = DONOR_MODES[DONOR_MODE_INDEX][0]

    def _invoke() -> None:
        global CREATED_FRAME_ID
        parent_id = _target_parent()
        donor_frame_id = _callback_donor_frame()
        child_offset = _resolved_child_offset(parent_id)
        if parent_id <= 0:
            CREATED_FRAME_ID = 0
            _log("create helper invoke aborted: target parent unavailable")
            return
        if child_offset <= 0:
            CREATED_FRAME_ID = 0
            _log(f"create helper invoke aborted: no child slot available for parent={parent_id}")
            return

        if HELPER_TYPE_INDEX == 0:
            CREATED_FRAME_ID = int(
                UIManager.CreateButtonFrameByFrameId(
                    parent_id,
                    0,
                    child_offset,
                    "PyButton",
                    "PyHelperButton",
                )
                or 0
            )
        elif HELPER_TYPE_INDEX == 1:
            CREATED_FRAME_ID = int(
                UIManager.CreateCheckboxFrameByFrameId(
                    parent_id,
                    0,
                    child_offset,
                    "PyCheckbox",
                    "PyHelperCheckbox",
                )
                or 0
            )
        elif HELPER_TYPE_INDEX == 2:
            CREATED_FRAME_ID = int(
                UIManager.CreateTextLabelFrameByFrameId(
                    parent_id,
                    0,
                    child_offset,
                    "PyTextLabel",
                    "PyHelperTextLabel",
                )
                or 0
            )
        else:
            CREATED_FRAME_ID = int(
                UIManager.CreateScrollableFrameByFrameId(
                    parent_id,
                    0,
                    child_offset,
                    0,
                    "PyHelperScrollable",
                )
                or 0
            )

        _log(
            f"create helper invoke result helper='{helper_name}' created_frame_id={CREATED_FRAME_ID} "
            f"parent={parent_id} child_offset=0x{child_offset:X}"
        )
        if CREATED_FRAME_ID > 0 and donor_frame_id > 0:
            callbacks = UIManager.GetFrameInteractionCallbacksByFrameId(donor_frame_id)
            added = UIManager.AddFrameUIInteractionCallbacksByFrameId(
                CREATED_FRAME_ID,
                callbacks,
                start_index=0,
            )
            _log(
                f"graft callbacks result donor={donor_frame_id} "
                f"callback_count={len(callbacks)} added={added}"
            )
        if CREATED_FRAME_ID > 0:
            UIManager.TriggerFrameRedrawByFrameId(CREATED_FRAME_ID)
            UIManager.TriggerFrameRedrawByFrameId(parent_id)

    Py4GW.Game.enqueue(_invoke)
    LAST_STATUS = (
        f"create helper enqueued helper='{helper_name}' "
        f"parent_mode='{parent_mode_name}' donor_mode='{donor_mode_name}'"
    )
    _log(LAST_STATUS)
    _schedule_report("state after create helper")


def _dump_state(prefix: str) -> None:
    clone_root = _clone_root()
    clone_root0 = _clone_root0()
    inventory = _inventory_root()
    devtext = _devtext_root()
    target_parent = _target_parent()
    donor = _callback_donor_frame()
    created = int(CREATED_FRAME_ID or 0)
    _log(
        f"{prefix} "
        f"clone_root=({_frame_summary(clone_root)}) "
        f"root[0]=({_frame_summary(clone_root0)}) "
        f"inventory=({_frame_summary(inventory)}) "
        f"devtext=({_frame_summary(devtext)}) "
        f"target_parent=({_frame_summary(target_parent)}) "
        f"donor=({_frame_summary(donor)}) "
        f"created=({_frame_summary(created)})"
    )


def _draw_radio_group(label: str, options: list[tuple[str, str]], current_index_name: str) -> int:
    current_index = globals()[current_index_name]
    PyImGui.text(label)
    for index, (name, description) in enumerate(options):
        current_index = int(
            PyImGui.radio_button(
                f"{name}##{label}_{index}",
                int(current_index),
                int(index),
            )
        )
        if description:
            PyImGui.same_line(0.0, 8.0)
            PyImGui.text_disabled(description)
    globals()[current_index_name] = current_index
    return current_index


def _draw_window() -> None:
    global WINDOW_OPEN
    global READ_DELAY_SECONDS
    global TARGET_CHILD_OFFSET
    global USE_FREE_CHILD_SLOT

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("goal: retest GWCA helper constructors on a proven empty-clone host with optional callback grafting")
    PyImGui.separator()
    PyImGui.text("flow:")
    PyImGui.text("1) Open Inventory")
    PyImGui.text("2) Ensure DevText")
    PyImGui.text("3) Create Empty Clone")
    PyImGui.text("4) Pick helper, parent, and donor")
    PyImGui.text("5) Create Helper Frame")
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

    _draw_radio_group("helper type:", HELPER_TYPES, "HELPER_TYPE_INDEX")
    _draw_radio_group("target parent mode:", TARGET_PARENT_MODES, "TARGET_PARENT_MODE_INDEX")
    _draw_radio_group("donor mode:", DONOR_MODES, "DONOR_MODE_INDEX")
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
    if PyImGui.button("Create Helper Frame"):
        _create_helper_frame_on_clone()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Dump State"):
        _dump_state("manual state report")

    PyImGui.separator()
    PyImGui.text(f"last_status={LAST_STATUS}")
    PyImGui.text(f"clone_root={_clone_root()}")
    PyImGui.text(f"root[0]={_clone_root0()}")
    PyImGui.text(f"inventory={_inventory_root()}")
    PyImGui.text(f"devtext={_devtext_root()}")
    PyImGui.text(f"target_parent={_target_parent()}")
    PyImGui.text(f"donor={_callback_donor_frame()}")
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
        _log("4) pick helper, parent, and donor")
        _log("5) click 'Create Helper Frame'")
    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
