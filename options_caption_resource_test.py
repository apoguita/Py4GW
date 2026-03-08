import ctypes
import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.enums_src.UI_enums import ControlAction
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction, ScannerSection
from Py4GWCoreLib.native_src.internals.prototypes import NativeFunctionPrototype


MODULE_NAME = "InvAggregate Caption Resource Test"
SCRIPT_REVISION = "2026-03-07-invaggregate-caption-resource-test-1"
WINDOW_OPEN = True

READ_DELAY_SECONDS = 0.50
RESOURCE_ID = 0x8D

PENDING_REPORTS: list[tuple[float, str]] = []
GET_ENCODED_TEXT_RESOURCE_FN = None
SET_FRAME_ENCODED_TEXT_RESOURCE_FN = None
CREATE_ENCODED_TEXT_FROM_ID_FN = None
LAST_RESOURCE_PTR = 0
ROOT_CHILDREN_BEFORE_OPEN: set[int] = set()
LAST_OPENED_ROOT_IDS: list[int] = []


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
        _report_state(prefix)


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


def _find_target_root() -> tuple[int, str]:
    for label in ("InvAggregate", "Inventory", "Inventory Bags"):
        frame_id = int(UIManager.GetFrameIDByLabel(label) or 0)
        if frame_id > 0 and _frame_exists(frame_id):
            return frame_id, label
    return 0, ""


def _root_level_children() -> set[int]:
    root_frame_id = int(UIManager.GetRootFrameID() or 0)
    if root_frame_id <= 0:
        return set()
    result: set[int] = set()
    try:
        for fid in UIManager.GetFrameArray():
            frame_id = int(fid or 0)
            if frame_id <= 0:
                continue
            try:
                frame = UIManager.GetFrameByID(frame_id)
            except Exception:
                continue
            if int(frame.parent_id) == root_frame_id and bool(frame.is_created):
                result.add(frame_id)
    except Exception:
        return set()
    return result


def _report_new_root_children(prefix: str) -> None:
    if not LAST_OPENED_ROOT_IDS:
        _log(f"{prefix} new_root_children=[]")
        return
    summaries = [f"{frame_id}:({_frame_summary(frame_id)})" for frame_id in LAST_OPENED_ROOT_IDS]
    _log(f"{prefix} new_root_children={summaries}")


def _report_state(prefix: str) -> None:
    global LAST_OPENED_ROOT_IDS
    root_id, label = _find_target_root()
    child0 = int(UIManager.GetChildFrameByFrameId(root_id, 0) or 0) if root_id > 0 else 0
    if prefix == "state after open target":
        after_children = _root_level_children()
        LAST_OPENED_ROOT_IDS = sorted(int(fid) for fid in (after_children - ROOT_CHILDREN_BEFORE_OPEN))
    _log(
        f"{prefix} label='{label}' "
        f"root=({_frame_summary(root_id)}) "
        f"root[0]=({_frame_summary(child0)}) "
        f"last_resource_ptr=0x{LAST_RESOURCE_PTR:X}"
    )
    if prefix == "state after open target":
        _report_new_root_children(prefix)


def _resolve_caption_resource_functions() -> bool:
    global GET_ENCODED_TEXT_RESOURCE_FN
    global SET_FRAME_ENCODED_TEXT_RESOURCE_FN

    if GET_ENCODED_TEXT_RESOURCE_FN is None:
        GET_ENCODED_TEXT_RESOURCE_FN = NativeFunction(
            name="Ui_GetEncodedTextResourceById",
            pattern=bytes.fromhex("55 8B EC 56 8B 75 08 83 FE 5B 74 27 83 FE 5C 74 22 83 FE 5D 74 1D 83 FE 5E 74 18 83 FE 69 74 13"),
            mask="x" * 32,
            offset=0,
            section=ScannerSection.TEXT,
            prototype=NativeFunctionPrototype(ctypes.c_uint32, ctypes.c_uint32),
            use_near_call=False,
            report_success=True,
        )

    if SET_FRAME_ENCODED_TEXT_RESOURCE_FN is None:
        SET_FRAME_ENCODED_TEXT_RESOURCE_FN = NativeFunction(
            name="Ui_SetFrameEncodedTextResource",
            pattern=bytes.fromhex("55 8B EC 53 56 57 8B 7D 08 8B F7 F7 DE 1B F6 85 FF 75 14 68 D2 0B 00 00"),
            mask="x" * 24,
            offset=0,
            section=ScannerSection.TEXT,
            prototype=Prototypes["Void_U32_U32"],
            use_near_call=False,
            report_success=True,
        )

    return (
        GET_ENCODED_TEXT_RESOURCE_FN.is_valid()
        and SET_FRAME_ENCODED_TEXT_RESOURCE_FN.is_valid()
    )


def _log_function_status() -> None:
    valid = _resolve_caption_resource_functions()
    if not valid:
        _log("caption resource function status valid=False")
        return
    _log(
        "caption resource function status "
        f"valid=True "
        f"get_resource=0x{GET_ENCODED_TEXT_RESOURCE_FN.get_address():X} "
        f"set_resource=0x{SET_FRAME_ENCODED_TEXT_RESOURCE_FN.get_address():X}"
    )


def _open_target_window() -> None:
    global ROOT_CHILDREN_BEFORE_OPEN
    root_id, label = _find_target_root()
    if root_id > 0:
        _log(f"target already open label='{label}' frame_id={root_id}")
        _schedule_report("state after target already open")
        return
    ROOT_CHILDREN_BEFORE_OPEN = _root_level_children()
    UIManager.Keypress(int(ControlAction.ControlAction_ToggleAllBags), 0)
    _log("control action toggle all bags sent")
    _schedule_report("state after open target")


def _apply_resource_only() -> None:
    global LAST_RESOURCE_PTR
    root_id, label = _find_target_root()
    if root_id <= 0:
        _log("apply resource-only skipped because target root is not available")
        return
    if not _resolve_caption_resource_functions():
        _log("apply resource-only skipped because functions are unresolved")
        return

    def _invoke() -> None:
        global LAST_RESOURCE_PTR
        resource_ptr = int(GET_ENCODED_TEXT_RESOURCE_FN.directCall(int(RESOURCE_ID)) or 0)
        LAST_RESOURCE_PTR = resource_ptr
        if resource_ptr == 0:
            print(f"[{MODULE_NAME}] resource-only failed resource_id=0x{int(RESOURCE_ID):X}")
            return
        SET_FRAME_ENCODED_TEXT_RESOURCE_FN.directCall(int(root_id), int(resource_ptr))
        print(
            f"[{MODULE_NAME}] resource-only applied label='{label}' root={root_id} "
            f"resource_id=0x{int(RESOURCE_ID):X} resource_ptr=0x{resource_ptr:X}"
        )

    _report_state("state before resource-only")
    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after resource-only")


def _draw_window() -> None:
    global RESOURCE_ID

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.separator()
    PyImGui.text("Test flow:")
    PyImGui.text("1) Resolve Functions")
    PyImGui.text("2) Open InvAggregate")
    PyImGui.text("3) Apply Resource Only")
    PyImGui.text("4) Change Resource ID and retry")
    PyImGui.separator()

    RESOURCE_ID = max(0, int(PyImGui.input_int("Resource ID", int(RESOURCE_ID))))

    if PyImGui.button("Resolve Functions"):
        _log_function_status()
    if PyImGui.button("Open InvAggregate"):
        _open_target_window()
    if PyImGui.button("Report State"):
        _report_state("manual state report")
    if PyImGui.button("Apply Resource Only"):
        _apply_resource_only()
    if PyImGui.button("Resource -1"):
        RESOURCE_ID = max(0, int(RESOURCE_ID) - 1)
    if PyImGui.button("Resource +1"):
        RESOURCE_ID = max(0, int(RESOURCE_ID) + 1)


def main():
    global WINDOW_OPEN
    _process_pending_reports()
    if not WINDOW_OPEN:
        return
    PyImGui.set_next_window_size(460, 0)
    if PyImGui.begin(MODULE_NAME):
        _draw_window()
    PyImGui.end()


if __name__ == "__main__":
    main()
