import ctypes
import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction, ScannerSection
from Py4GWCoreLib.native_src.internals.prototypes import NativeFunctionPrototype, Prototypes


MODULE_NAME = "DevText Resource Caption Test"
SCRIPT_REVISION = "2026-03-07-devtext-resource-caption-test-4"
WINDOW_OPEN = True

READ_DELAY_SECONDS = 0.50
RESOURCE_ID = 0x8D
CLONE_LABEL = "PyDevTextResourceClone"
TITLE_TEXT = "Py4GW Arbitrary Name"

PENDING_REPORTS: list[tuple[float, str, str]] = []
GET_ENCODED_TEXT_RESOURCE_FN = None
SET_FRAME_ENCODED_TEXT_RESOURCE_FN = None
SELECT_FRAME_CONTEXT_FN = None
REMOVE_ATTACHED_ENTRY_FN = None
CREATE_ENCODED_TEXT_FN = None
SET_FRAME_TEXT_FN = None
LAST_RESOURCE_PTR = 0
LAST_TEXT_PTR = 0


U32_U32_WCHARP_U32_RET_U32 = NativeFunctionPrototype(
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_uint32,
    ctypes.c_wchar_p,
    ctypes.c_uint32,
)


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _schedule_report(prefix: str, target: str, delay_seconds: float | None = None) -> None:
    delay = READ_DELAY_SECONDS if delay_seconds is None else max(0.0, float(delay_seconds))
    PENDING_REPORTS.append((time.time() + delay, prefix, target))
    _log(f"scheduled report prefix='{prefix}' target={target} delay={delay:.2f}s")


def _process_pending_reports() -> None:
    if not PENDING_REPORTS:
        return
    now = time.time()
    ready: list[tuple[float, str, str]] = []
    pending: list[tuple[float, str, str]] = []
    for scheduled_at, prefix, target in PENDING_REPORTS:
        if scheduled_at <= now:
            ready.append((scheduled_at, prefix, target))
        else:
            pending.append((scheduled_at, prefix, target))
    PENDING_REPORTS[:] = pending
    for _, prefix, target in ready:
        if target == "clone":
            _report_state(prefix, _current_clone_frame_id())
        else:
            _report_state(prefix, 0)


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


def _current_clone_frame_id() -> int:
    return int(UIManager.GetFrameIDByLabel(CLONE_LABEL) or 0)


def _report_state(prefix: str, root_id: int) -> None:
    child0 = int(UIManager.GetChildFrameByFrameId(root_id, 0) or 0) if root_id > 0 else 0
    _log(
        f"{prefix} "
        f"root=({_frame_summary(root_id)}) "
        f"root[0]=({_frame_summary(child0)}) "
        f"last_resource_ptr=0x{LAST_RESOURCE_PTR:X} "
        f"last_text_ptr=0x{LAST_TEXT_PTR:X}"
    )


def _resolve_resource_functions() -> bool:
    global GET_ENCODED_TEXT_RESOURCE_FN
    global SET_FRAME_ENCODED_TEXT_RESOURCE_FN
    global SELECT_FRAME_CONTEXT_FN
    global REMOVE_ATTACHED_ENTRY_FN
    global CREATE_ENCODED_TEXT_FN
    global SET_FRAME_TEXT_FN

    if GET_ENCODED_TEXT_RESOURCE_FN is None:
        GET_ENCODED_TEXT_RESOURCE_FN = NativeFunction(
            name="Ui_GetEncodedTextResourceById",
            pattern=bytes.fromhex(
                "55 8B EC 56 8B 75 08 83 FE 5B 74 27 83 FE 5C 74 22 "
                "83 FE 5D 74 1D 83 FE 5E 74 18 83 FE 69 74 13"
            ),
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
            pattern=bytes.fromhex(
                "55 8B EC 53 56 57 8B 7D 08 8B F7 F7 DE 1B F6 85 FF 75 14 68 D2 0B 00 00"
            ),
            mask="x" * 24,
            offset=0,
            section=ScannerSection.TEXT,
            prototype=Prototypes["Void_U32_U32"],
            use_near_call=False,
            report_success=True,
        )

    if SELECT_FRAME_CONTEXT_FN is None:
        SELECT_FRAME_CONTEXT_FN = NativeFunction(
            name="Ui_SelectFrameContext",
            pattern=bytes.fromhex(
                "55 8B EC 56 8B 75 08 3B 35 00 00 00 00 73 1B A1 "
                "00 00 00 00 83 3C B0 00 74 10 56 B9 00 00 00 00"
            ),
            mask="xxxxxxxxx????xxx????xxxxxxxx????",
            offset=0,
            section=ScannerSection.TEXT,
            prototype=NativeFunctionPrototype(ctypes.c_uint32, ctypes.c_uint32),
            use_near_call=False,
            report_success=True,
        )

    if REMOVE_ATTACHED_ENTRY_FN is None:
        REMOVE_ATTACHED_ENTRY_FN = NativeFunction(
            name="Ui_RemoveAttachedEncodedEntryAndQueueUpdates",
            pattern=bytes.fromhex(
                "55 8B EC 83 EC 08 53 8B D9 56 57 89 5D FC 3B 1D "
                "00 00 00 00 75 14 68 17 01 00 00 BA 00 00 00 00"
            ),
            mask="xxxxxxxxxxxxxxxx????xxxxxxxx????",
            offset=0,
            section=ScannerSection.TEXT,
            prototype=Prototypes["Void_U32"],
            use_near_call=False,
            report_success=True,
        )

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

    if SET_FRAME_TEXT_FN is None:
        SET_FRAME_TEXT_FN = NativeFunction(
            name="Ui_SetFrameText",
            pattern=bytes.fromhex(
                "55 8B EC 53 56 57 8B 7D 08 8B F7 F7 DE 1B F6 85"
            ),
            mask="x" * 16,
            offset=0,
            section=ScannerSection.TEXT,
            prototype=Prototypes["Void_U32_U32"],
            use_near_call=False,
            report_success=True,
        )

    return (
        GET_ENCODED_TEXT_RESOURCE_FN.is_valid()
        and SET_FRAME_ENCODED_TEXT_RESOURCE_FN.is_valid()
        and SELECT_FRAME_CONTEXT_FN.is_valid()
        and REMOVE_ATTACHED_ENTRY_FN.is_valid()
        and CREATE_ENCODED_TEXT_FN.is_valid()
        and SET_FRAME_TEXT_FN.is_valid()
    )


def _log_function_status() -> None:
    valid = _resolve_resource_functions()
    if not valid:
        _log("resource function status valid=False")
        return
    _log(
        "resource function status "
        f"valid=True "
        f"get_resource=0x{GET_ENCODED_TEXT_RESOURCE_FN.get_address():X} "
        f"set_resource=0x{SET_FRAME_ENCODED_TEXT_RESOURCE_FN.get_address():X} "
        f"select_context=0x{SELECT_FRAME_CONTEXT_FN.get_address():X} "
        f"remove_entry=0x{REMOVE_ATTACHED_ENTRY_FN.get_address():X} "
        f"create_text=0x{CREATE_ENCODED_TEXT_FN.get_address():X} "
        f"set_text=0x{SET_FRAME_TEXT_FN.get_address():X}"
    )


def _create_clone() -> None:
    existing_id = _current_clone_frame_id()
    if existing_id > 0:
        GWUI.DestroyUIComponentByFrameId(existing_id)
    frame_id = GWUI.CreateWindowClone(
        0.0,
        0.0,
        180.0,
        220.0,
        frame_label=CLONE_LABEL,
        ensure_devtext_source=True,
    )
    _log(
        f"create clone requested label='{CLONE_LABEL}' "
        f"immediate_frame_id={int(frame_id or 0)}"
    )
    _schedule_report("state after create clone", "clone")


def _apply_resource_only(root_id: int, target_name: str) -> None:
    global LAST_RESOURCE_PTR
    if root_id <= 0:
        _log(f"apply resource-only skipped because {target_name} root is not available")
        return
    if not _resolve_resource_functions():
        _log("apply resource-only skipped because functions are unresolved")
        return

    def _invoke() -> None:
        global LAST_RESOURCE_PTR
        resource_ptr = int(GET_ENCODED_TEXT_RESOURCE_FN.directCall(int(RESOURCE_ID)) or 0)
        LAST_RESOURCE_PTR = resource_ptr
        if resource_ptr == 0:
            print(
                f"[{MODULE_NAME}] resource-only failed "
                f"target={target_name} resource_id=0x{int(RESOURCE_ID):X}"
            )
            return
        SET_FRAME_ENCODED_TEXT_RESOURCE_FN.directCall(int(root_id), int(resource_ptr))
        print(
            f"[{MODULE_NAME}] resource-only applied target={target_name} root={root_id} "
            f"resource_id=0x{int(RESOURCE_ID):X} resource_ptr=0x{resource_ptr:X}"
        )

    _report_state(f"state before resource-only target={target_name}", root_id)
    Py4GW.Game.enqueue(_invoke)
    _schedule_report(f"state after resource-only target={target_name}", target_name)


def _remove_last_resource_from_clone() -> None:
    if LAST_RESOURCE_PTR <= 0:
        _log("remove resource skipped because there is no last_resource_ptr")
        return
    if not _resolve_resource_functions():
        _log("remove resource skipped because functions are unresolved")
        return

    root_id = _current_clone_frame_id()
    if root_id <= 0:
        _log("remove resource skipped because clone root is not available")
        return

    def _invoke() -> None:
        context_key = int(SELECT_FRAME_CONTEXT_FN.directCall(int(root_id)) or 0)
        REMOVE_ATTACHED_ENTRY_FN.directCall(context_key)
        print(
            f"[{MODULE_NAME}] removed attached resource entry "
            f"root={root_id} context_key=0x{context_key:X} resource_ptr=0x{int(LAST_RESOURCE_PTR):X}"
        )

    _report_state("state before remove resource target=clone", root_id)
    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after remove resource target=clone", "clone")


def _apply_text_only_to_clone() -> None:
    global LAST_TEXT_PTR
    root_id = _current_clone_frame_id()
    if root_id <= 0:
        _log("apply text skipped because clone root is not available")
        return
    if not _resolve_resource_functions():
        _log("apply text skipped because functions are unresolved")
        return

    title_text = str(TITLE_TEXT)

    def _invoke() -> None:
        global LAST_TEXT_PTR
        SELECT_FRAME_CONTEXT_FN.directCall(int(root_id))
        text_ptr = int(CREATE_ENCODED_TEXT_FN.directCall(8, 7, title_text, 0) or 0)
        LAST_TEXT_PTR = text_ptr
        if text_ptr == 0:
            print(f"[{MODULE_NAME}] text-only failed title='{title_text}'")
            return
        SET_FRAME_TEXT_FN.directCall(int(root_id), int(text_ptr))
        print(
            f"[{MODULE_NAME}] text-only applied target=clone root={root_id} "
            f"title='{title_text}' text_ptr=0x{text_ptr:X}"
        )

    _report_state("state before text-only target=clone", root_id)
    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after text-only target=clone", "clone")


def _remove_resource_then_apply_text_to_clone() -> None:
    if LAST_RESOURCE_PTR <= 0:
        _log("remove+text skipped because there is no last_resource_ptr")
        return
    root_id = _current_clone_frame_id()
    if root_id <= 0:
        _log("remove+text skipped because clone root is not available")
        return
    if not _resolve_resource_functions():
        _log("remove+text skipped because functions are unresolved")
        return

    title_text = str(TITLE_TEXT)

    def _invoke() -> None:
        global LAST_TEXT_PTR
        context_key = int(SELECT_FRAME_CONTEXT_FN.directCall(int(root_id)) or 0)
        REMOVE_ATTACHED_ENTRY_FN.directCall(context_key)
        text_ptr = int(CREATE_ENCODED_TEXT_FN.directCall(8, 7, title_text, 0) or 0)
        LAST_TEXT_PTR = text_ptr
        if text_ptr == 0:
            print(
                f"[{MODULE_NAME}] remove+text text create failed "
                f"title='{title_text}' context_key=0x{context_key:X} resource_ptr=0x{int(LAST_RESOURCE_PTR):X}"
            )
            return
        SET_FRAME_TEXT_FN.directCall(int(root_id), int(text_ptr))
        print(
            f"[{MODULE_NAME}] remove+text applied target=clone root={root_id} "
            f"context_key=0x{context_key:X} resource_ptr=0x{int(LAST_RESOURCE_PTR):X} text_ptr=0x{text_ptr:X} "
            f"title='{title_text}'"
        )

    _report_state("state before remove+text target=clone", root_id)
    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after remove+text target=clone", "clone")


def _draw_window() -> None:
    global RESOURCE_ID
    global TITLE_TEXT

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.separator()
    PyImGui.text("Test flow:")
    PyImGui.text("1) Resolve Functions")
    PyImGui.text("2) Create Clone")
    PyImGui.text("3) Apply Resource Only To Clone")
    PyImGui.text("4) Remove resource and/or apply text")
    PyImGui.separator()

    RESOURCE_ID = max(0, int(PyImGui.input_int("Resource ID", int(RESOURCE_ID))))
    TITLE_TEXT = str(PyImGui.input_text("Title Text", TITLE_TEXT))

    if PyImGui.button("Resolve Functions"):
        _log_function_status()
    if PyImGui.button("Create Clone"):
        _create_clone()
    if PyImGui.button("Report Clone State"):
        _report_state("manual clone state report", _current_clone_frame_id())
    if PyImGui.button("Apply Resource Only To Clone"):
        _apply_resource_only(_current_clone_frame_id(), "clone")
    if PyImGui.button("Remove Last Resource From Clone"):
        _remove_last_resource_from_clone()
    if PyImGui.button("Apply Text Only To Clone"):
        _apply_text_only_to_clone()
    if PyImGui.button("Remove Resource Then Apply Text"):
        _remove_resource_then_apply_text_to_clone()
    if PyImGui.button("Resource -1"):
        RESOURCE_ID = max(0, int(RESOURCE_ID) - 1)
    if PyImGui.button("Resource +1"):
        RESOURCE_ID = max(0, int(RESOURCE_ID) + 1)


def main():
    global WINDOW_OPEN
    _process_pending_reports()
    if not WINDOW_OPEN:
        return
    PyImGui.set_next_window_size(420, 0)
    if PyImGui.begin(MODULE_NAME):
        _draw_window()
    PyImGui.end()


if __name__ == "__main__":
    main()
