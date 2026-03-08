import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager


MODULE_NAME = "WeaponBar Component Creation Test"
SCRIPT_REVISION = "2026-03-07-weaponbar-component-creation-test-1"
WINDOW_OPEN = True
INITIALIZED = False

READ_DELAY_SECONDS = 0.50
CREATED_FRAME_ID = 0
LAST_CHILD_OFFSET = 0
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


def _weaponbar_root() -> int:
    return int(UIManager.GetFrameIDByLabel("WeaponBar") or 0)


def _source_child() -> int:
    root = _weaponbar_root()
    if root <= 0:
        return 0
    return int(UIManager.GetChildFrameByFrameId(root, 0x10000000) or 0)


def _created_child() -> int:
    if CREATED_FRAME_ID > 0:
        return int(CREATED_FRAME_ID)
    root = _weaponbar_root()
    if root <= 0 or LAST_CHILD_OFFSET <= 0:
        return 0
    return int(UIManager.GetChildFrameByFrameId(root, LAST_CHILD_OFFSET) or 0)


def _source_callback() -> int:
    frame_id = _source_child()
    if frame_id <= 0:
        return 0
    try:
        frame = UIManager.GetFrameByID(frame_id)
        if not frame.frame_callbacks:
            return 0
        return int(getattr(frame.frame_callbacks[0], "callback_address", 0) or 0)
    except Exception:
        return 0


def _dump_state(prefix: str) -> None:
    root = _weaponbar_root()
    source = _source_child()
    created = _created_child()
    _log(
        f"{prefix} "
        f"weaponbar=({_frame_summary(root)}) "
        f"source_child=({_frame_summary(source)}) "
        f"created_child=({_frame_summary(created)})"
    )
    if source > 0:
        frame = UIManager.GetFrameByID(source)
        _log(f"{prefix} source_child callbacks={len(frame.frame_callbacks)}")
        for index, callback in enumerate(frame.frame_callbacks):
            callback_addr = int(getattr(callback, 'callback_address', 0) or 0)
            callback_ctx = int(getattr(callback, 'uictl_context', 0) or 0)
            _log(f"{prefix} source_child callback[{index}] addr=0x{callback_addr:X} uictl_context=0x{callback_ctx:X}")


def _create_extra_weapon_slot() -> None:
    global CREATED_FRAME_ID
    global LAST_CHILD_OFFSET

    root = _weaponbar_root()
    callback = _source_callback()
    if root <= 0:
        _log("create extra slot skipped because WeaponBar is unavailable")
        return
    if callback <= 0:
        _log("create extra slot skipped because source callback is unavailable")
        return

    LAST_CHILD_OFFSET = 0x10000004

    def _invoke() -> None:
        global CREATED_FRAME_ID
        CREATED_FRAME_ID = int(
            UIManager.CreateUIComponentRawByFrameId(
                root,
                0,
                LAST_CHILD_OFFSET,
                callback,
                4,
                "Slot5",
            )
            or 0
        )

    Py4GW.Game.enqueue(_invoke)
    _log(
        f"create extra slot enqueued parent={root} child_offset=0x{LAST_CHILD_OFFSET:X} "
        f"callback=0x{callback:X} wparam=4"
    )
    _schedule_report("state after create extra slot")


def _draw_window() -> None:
    global WINDOW_OPEN
    global READ_DELAY_SECONDS
    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("goal: validate raw CreateUIComponent on the known-working WeaponBar pattern")
    PyImGui.separator()
    PyImGui.text("flow:")
    PyImGui.text("1) Create Extra Weapon Slot")
    PyImGui.text("2) Wait for state after create extra slot")
    PyImGui.text("3) Dump State")
    PyImGui.separator()

    READ_DELAY_SECONDS = float(
        _normalize_input_int(
            PyImGui.input_int("Read Delay (ms)", int(READ_DELAY_SECONDS * 1000.0)),
            int(READ_DELAY_SECONDS * 1000.0),
        )
    ) / 1000.0

    if PyImGui.button("Create Extra Weapon Slot"):
        _create_extra_weapon_slot()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Dump State"):
        _dump_state("manual state report")

    PyImGui.separator()
    PyImGui.text(f"weaponbar={_weaponbar_root()}")
    PyImGui.text(f"source_child={_source_child()}")
    PyImGui.text(f"source_callback=0x{_source_callback():X}" if _source_callback() > 0 else "source_callback=unresolved")
    PyImGui.text(f"created_child={_created_child()}")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("test flow:")
        _log("1) click 'Create Extra Weapon Slot'")
        _log("2) wait for 'state after create extra slot'")
        _log("3) click 'Dump State'")
    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
