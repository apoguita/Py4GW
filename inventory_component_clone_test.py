import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.enums_src.UI_enums import ControlAction


MODULE_NAME = "Inventory Component Clone Test"
SCRIPT_REVISION = "2026-03-07-inventory-component-clone-test-2"
WINDOW_OPEN = True
INITIALIZED = False

READ_DELAY_SECONDS = 0.50
CREATED_FRAME_ID = 0
TARGET_CHILD_OFFSET = 0xFFF1
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


def _direct_children(frame_id: int) -> list[tuple[int, int]]:
    frame_id = int(frame_id or 0)
    if frame_id <= 0:
        return []
    children: list[tuple[int, int]] = []
    try:
        for fid in UIManager.GetFrameArray():
            child_id = int(fid or 0)
            if child_id <= 0:
                continue
            try:
                frame = UIManager.GetFrameByID(child_id)
            except Exception:
                continue
            if int(frame.parent_id) == frame_id:
                children.append((int(frame.child_offset_id), child_id))
    except Exception:
        return []
    children.sort(key=lambda item: item[0])
    return children


def _log_direct_children(prefix: str, frame_id: int) -> None:
    children = _direct_children(frame_id)
    if frame_id <= 0:
        _log(f"{prefix} frame_id=0")
        return
    if not children:
        _log(f"{prefix} no direct children")
        return
    rendered = ", ".join(f"0x{child_offset:X}->{child_id}" for child_offset, child_id in children[:24])
    suffix = "" if len(children) <= 24 else f" ... total={len(children)}"
    _log(f"{prefix} direct_children={rendered}{suffix}")


def _open_inventory() -> None:
    def _invoke() -> None:
        UIManager.Keypress(ControlAction.ControlAction_ToggleInventoryWindow.value, 0)

    Py4GW.Game.enqueue(_invoke)
    _log("open inventory enqueued")
    _schedule_report("state after open inventory")


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
    if CREATED_FRAME_ID > 0:
        return int(CREATED_FRAME_ID)
    parent_id = _game_child6()
    if parent_id <= 0:
        return 0
    return int(UIManager.GetChildFrameByFrameId(parent_id, TARGET_CHILD_OFFSET) or 0)


def _source_callbacks() -> list[tuple[int, int]]:
    frame_id = _inventory_root()
    if frame_id <= 0:
        return []
    try:
        frame = UIManager.GetFrameByID(frame_id)
        entries: list[tuple[int, int]] = []
        for callback in frame.frame_callbacks:
            callback_addr = int(getattr(callback, "callback_address", 0) or 0)
            callback_h0008 = int(getattr(callback, "h0008", 0) or 0)
            if callback_addr > 0:
                entries.append((callback_addr, callback_h0008))
        return entries
    except Exception:
        return []


def _dump_callbacks(prefix: str, frame_id: int) -> None:
    frame_id = int(frame_id or 0)
    if frame_id <= 0:
        _log(f"{prefix} frame_id=0")
        return
    try:
        frame = UIManager.GetFrameByID(frame_id)
        _log(f"{prefix} callbacks={len(frame.frame_callbacks)}")
        for index, callback in enumerate(frame.frame_callbacks):
            callback_addr = int(getattr(callback, "callback_address", 0) or 0)
            callback_h0008 = int(getattr(callback, "h0008", 0) or 0)
            callback_ctx = int(getattr(callback, "uictl_context", 0) or 0)
            _log(
                f"{prefix} callback[{index}] "
                f"addr=0x{callback_addr:X} "
                f"h0008=0x{callback_h0008:X} "
                f"uictl_context=0x{callback_ctx:X}"
            )
    except Exception as exc:
        _log(f"{prefix} callback_dump_error={exc}")


def _dump_state(prefix: str) -> None:
    inventory = _inventory_root()
    game = _game_root()
    game6 = _game_child6()
    created = _created_root()
    created7 = int(UIManager.GetChildFrameByFrameId(created, 7) or 0) if created > 0 else 0
    created9 = int(UIManager.GetChildFrameByFrameId(created, 9) or 0) if created > 0 else 0
    _log(
        f"{prefix} "
        f"inventory=({_frame_summary(inventory)}) "
        f"game=({_frame_summary(game)}) "
        f"game[6]=({_frame_summary(game6)}) "
        f"created=({_frame_summary(created)}) "
        f"created[7]=({_frame_summary(created7)}) "
        f"created[9]=({_frame_summary(created9)})"
    )
    _dump_callbacks(f"{prefix} inventory", inventory)
    _dump_callbacks(f"{prefix} created", created)
    _dump_callbacks(f"{prefix} created[7]", created7)
    _dump_callbacks(f"{prefix} created[9]", created9)
    _log_direct_children(f"{prefix} game[6]", game6)
    _log_direct_children(f"{prefix} created", created)
    _log_direct_children(f"{prefix} created[7]", created7)
    _log_direct_children(f"{prefix} created[9]", created9)


def _create_inventory_style_component() -> None:
    global CREATED_FRAME_ID

    parent_id = _game_child6()
    callbacks = _source_callbacks()
    if parent_id <= 0:
        _log("create component skipped because Game[6] is unavailable")
        return
    if not callbacks:
        _log("create component skipped because Inventory root callbacks are unavailable")
        return

    primary_callback, primary_h0008 = callbacks[0]

    def _invoke() -> None:
        global CREATED_FRAME_ID
        CREATED_FRAME_ID = int(
            UIManager.CreateUIComponentRawByFrameId(
                parent_id,
                0x20,
                TARGET_CHILD_OFFSET,
                primary_callback,
                primary_h0008,
                "PyInventoryClone",
            )
            or 0
        )
        _log(
            f"create invoke result created_frame_id={CREATED_FRAME_ID} "
            f"parent={parent_id} child_offset=0x{TARGET_CHILD_OFFSET:X}"
        )
        if CREATED_FRAME_ID > 0:
            for callback_addr, callback_h0008 in callbacks[1:]:
                UIManager.AddFrameUIInteractionCallbackByFrameId(
                    CREATED_FRAME_ID,
                    callback_addr,
                    callback_h0008,
                )
            UIManager.TriggerFrameRedrawByFrameId(CREATED_FRAME_ID)

    Py4GW.Game.enqueue(_invoke)
    _log(
        f"create component enqueued parent={parent_id} child_offset=0x{TARGET_CHILD_OFFSET:X} "
        f"callback_count={len(callbacks)} primary_callback=0x{primary_callback:X} "
        f"primary_h0008=0x{primary_h0008:X}"
    )
    _schedule_report("state after create component")


def _draw_window() -> None:
    global WINDOW_OPEN
    global READ_DELAY_SECONDS

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("goal: mirror the HeroEquipment CreateUIComponent recipe")
    PyImGui.separator()
    PyImGui.text("flow:")
    PyImGui.text("1) Open Inventory")
    PyImGui.text("2) Create Inventory-Style Component")
    PyImGui.text("3) Dump State")
    PyImGui.separator()

    READ_DELAY_SECONDS = float(
        _normalize_input_int(
            PyImGui.input_int("Read Delay (ms)", int(READ_DELAY_SECONDS * 1000.0)),
            int(READ_DELAY_SECONDS * 1000.0),
        )
    ) / 1000.0

    if PyImGui.button("Open Inventory"):
        _open_inventory()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Create Inventory-Style Component"):
        _create_inventory_style_component()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Dump State"):
        _dump_state("manual state report")

    PyImGui.separator()
    PyImGui.text(f"inventory={_inventory_root()}")
    PyImGui.text(f"game={_game_root()}")
    PyImGui.text(f"game[6]={_game_child6()}")
    PyImGui.text(f"created={_created_root()}")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("test flow:")
        _log("1) click 'Open Inventory'")
        _log("2) wait for 'state after open inventory'")
        _log("3) click 'Create Inventory-Style Component'")
        _log("4) wait for 'state after create component'")
        _log("5) click 'Dump State'")
    _process_pending_reports()
    _draw_window()


if __name__ == "__main__":
    main()
