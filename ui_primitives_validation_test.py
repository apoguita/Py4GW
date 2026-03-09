import time

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "UI Primitives Validation Test"
SCRIPT_REVISION = "2026-03-07-ui-primitives-validation-test-1"
WINDOW_OPEN = True
INITIALIZED = False

CLONE_LABEL = "PyUIPrimitiveValidationClone"
READ_DELAY_SECONDS = 0.50
TITLE_TEXT = "Py4GW Validation Title"
TEXT_LABEL_TEXT = "Py4GW Text Label"
MULTILINE_TEXT = "Py4GW Multiline Label\nSecond Line"
TARGET_MODE = "original"

BUTTON_SLOT = 10
CHECKBOX_SLOT = 11
SCROLLABLE_SLOT = 12
TEXT_LABEL_SLOT = 13

PENDING_REPORTS: list[tuple[float, str]] = []

CREATED_IDS = {
    "button": 0,
    "checkbox": 0,
    "scrollable": 0,
    "text_label": 0,
}

MANUAL_READONLY_TARGET = 0


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


def _current_clone_id() -> int:
    return int(UIManager.GetFrameIDByLabel(CLONE_LABEL) or 0)


def _current_root_id() -> int:
    if TARGET_MODE == "original":
        return int(GWUI.GetDevTextFrameID() or 0)
    return _current_clone_id()


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


def _label_for_frame(frame_id: int) -> str:
    frame_id = int(frame_id or 0)
    if frame_id <= 0:
        return ""
    try:
        return GWUI.GetFrameLabelByFrameId(frame_id)
    except Exception:
        return ""


def _clone_parent_for_created_controls() -> int:
    root_id = _current_root_id()
    if root_id <= 0:
        return 0
    child0 = int(UIManager.GetChildFrameByFrameId(root_id, 0) or 0)
    return child0 if child0 > 0 else root_id


def _clone_host_frame_id() -> int:
    root_id = _current_root_id()
    if root_id <= 0:
        return 0
    return int(UIManager.GetChildFramePathByFrameId(root_id, [0, 0, 0]) or 0)


def _dump_state(prefix: str) -> None:
    root_id = _current_root_id()
    root0 = int(UIManager.GetChildFrameByFrameId(root_id, 0) or 0) if root_id > 0 else 0
    host = _clone_host_frame_id()
    first_child = UIManager.GetFirstChildFrameID(root_id) if root_id > 0 else 0
    last_child = UIManager.GetLastChildFrameID(root_id) if root_id > 0 else 0
    item0 = UIManager.GetItemFrameID(root_id, 0) if root_id > 0 else 0
    tab0 = UIManager.GetTabFrameID(root_id, 0) if root_id > 0 else 0
    next_sibling = UIManager.GetNextChildFrameID(root_id) if root_id > 0 else 0
    prev_sibling = UIManager.GetPrevChildFrameID(root_id) if root_id > 0 else 0
    context_root = UIManager.GetFrameContext(root_id) if root_id > 0 else 0
    context_root0 = UIManager.GetFrameContext(root0) if root0 > 0 else 0
    context_host = UIManager.GetFrameContext(host) if host > 0 else 0

    _log(
        f"{prefix} "
        f"root=({_frame_summary(root_id)}) "
        f"root[0]=({_frame_summary(root0)}) "
        f"host=({_frame_summary(host)}) "
        f"context_root=0x{context_root:X} "
        f"context_root0=0x{context_root0:X} "
        f"context_host=0x{context_host:X}"
    )
    _log(
        f"{prefix} "
        f"first_child={first_child} "
        f"last_child={last_child} "
        f"item0={item0} "
        f"tab0={tab0} "
        f"next_sibling={next_sibling} "
        f"prev_sibling={prev_sibling}"
    )
    for key, frame_id in CREATED_IDS.items():
        _log(
            f"{prefix} created[{key}] "
            f"summary=({_frame_summary(frame_id)}) "
            f"label='{_label_for_frame(frame_id)}'"
        )


def _create_clone() -> None:
    global TARGET_MODE
    def _invoke() -> None:
        GWUI.CreateEmptyWindow(
            0.0,
            0.0,
            180.0,
            220.0,
            frame_label=CLONE_LABEL,
        )

    Py4GW.Game.enqueue(_invoke)
    TARGET_MODE = "clone"
    _log(f"create clone enqueued label='{CLONE_LABEL}'")
    _schedule_report("state after create clone")


def _open_original_devtext() -> None:
    global TARGET_MODE

    def _invoke() -> None:
        GWUI.OpenDevTextWindow()

    Py4GW.Game.enqueue(_invoke)
    TARGET_MODE = "original"
    _log("open original DevText enqueued")
    _schedule_report("state after open original")


def _create_button() -> None:
    parent_id = _clone_parent_for_created_controls()
    if parent_id <= 0:
        _log("create button skipped because clone parent is unavailable")
        return

    def _invoke() -> None:
        CREATED_IDS["button"] = int(
            GWUI.CreateButtonFrameByFrameId(
                parent_id,
                component_flags=0,
                child_index=BUTTON_SLOT,
                name_enc="BtnPy4GW",
                component_label="PyButton",
            )
            or 0
        )

    Py4GW.Game.enqueue(_invoke)
    _log(f"create button enqueued parent={parent_id} slot={BUTTON_SLOT}")
    _schedule_report("state after create button")


def _create_checkbox() -> None:
    parent_id = _clone_parent_for_created_controls()
    if parent_id <= 0:
        _log("create checkbox skipped because clone parent is unavailable")
        return

    def _invoke() -> None:
        CREATED_IDS["checkbox"] = int(
            GWUI.CreateCheckboxFrameByFrameId(
                parent_id,
                component_flags=0,
                child_index=CHECKBOX_SLOT,
                name_enc="ChkPy4GW",
                component_label="PyCheckbox",
            )
            or 0
        )

    Py4GW.Game.enqueue(_invoke)
    _log(f"create checkbox enqueued parent={parent_id} slot={CHECKBOX_SLOT}")
    _schedule_report("state after create checkbox")


def _create_scrollable() -> None:
    parent_id = _clone_parent_for_created_controls()
    if parent_id <= 0:
        _log("create scrollable skipped because clone parent is unavailable")
        return

    def _invoke() -> None:
        CREATED_IDS["scrollable"] = int(
            GWUI.CreateScrollableFrameByFrameId(
                parent_id,
                component_flags=0,
                child_index=SCROLLABLE_SLOT,
                page_context=0,
                component_label="PyScrollable",
            )
            or 0
        )

    Py4GW.Game.enqueue(_invoke)
    _log(f"create scrollable enqueued parent={parent_id} slot={SCROLLABLE_SLOT}")
    _schedule_report("state after create scrollable")


def _create_text_label() -> None:
    parent_id = _clone_parent_for_created_controls()
    if parent_id <= 0:
        _log("create text label skipped because clone parent is unavailable")
        return

    def _invoke() -> None:
        CREATED_IDS["text_label"] = int(
            GWUI.CreateTextLabelFrameByFrameId(
                parent_id,
                component_flags=0,
                child_index=TEXT_LABEL_SLOT,
                name_enc="LblPy4GW",
                component_label="PyTextLabel",
            )
            or 0
        )

    Py4GW.Game.enqueue(_invoke)
    _log(f"create text label enqueued parent={parent_id} slot={TEXT_LABEL_SLOT}")
    _schedule_report("state after create text label")


def _apply_margins_to_created_controls() -> None:
    parent_id = _clone_parent_for_created_controls()
    if parent_id <= 0:
        _log("apply margins skipped because clone parent is unavailable")
        return
    left, top, right, bottom = UIManager.GetFrameCoords(parent_id)
    parent_width = max(1.0, float(right - left))
    parent_height = max(1.0, float(bottom - top))
    layouts = {
        "button": (8.0, 8.0, 120.0, 24.0),
        "checkbox": (8.0, 36.0, 140.0, 24.0),
        "text_label": (8.0, 66.0, 160.0, 48.0),
        "scrollable": (8.0, 118.0, max(80.0, parent_width - 24.0), max(40.0, parent_height - 126.0)),
    }
    plan: list[tuple[str, int, float, float, float, float, int]] = []
    for key, rect in layouts.items():
        frame_id = int(CREATED_IDS.get(key, 0) or 0)
        if frame_id <= 0:
            continue
        x, y, width, height = rect
        flags = GWUI.ChooseAnchorFlagsForDesiredRect(
            x,
            y,
            width,
            height,
            parent_width,
            parent_height,
            True,
        )
        plan.append((key, frame_id, x, y, width, height, int(flags)))

    def _invoke() -> None:
        for _, frame_id, x, y, width, height, flags in plan:
            GWUI.SetFrameMarginsByFrameId(frame_id, flags, x, y, width, height)

    Py4GW.Game.enqueue(_invoke)
    _log(f"apply margins enqueued targets={[f'{key}:{frame_id}:0x{flags:X}' for key, frame_id, _, _, _, _, flags in plan]}")
    _schedule_report("state after apply margins")


def _apply_labels() -> None:
    text_label_id = int(CREATED_IDS.get("text_label", 0) or 0)
    button_id = int(CREATED_IDS.get("button", 0) or 0)
    checkbox_id = int(CREATED_IDS.get("checkbox", 0) or 0)
    scrollable_id = int(CREATED_IDS.get("scrollable", 0) or 0)

    def _invoke() -> None:
        if button_id > 0:
            GWUI.SetLabelByFrameId(button_id, "PyButton Updated")
        if checkbox_id > 0:
            GWUI.SetLabelByFrameId(checkbox_id, "PyCheckbox Updated")
        if text_label_id > 0:
            GWUI.SetLabelByFrameId(text_label_id, TEXT_LABEL_TEXT)
            GWUI.SetMultilineLabelByFrameId(text_label_id, MULTILINE_TEXT)
        if scrollable_id > 0:
            GWUI.SetLabelByFrameId(scrollable_id, "PyScrollable Updated")

    Py4GW.Game.enqueue(_invoke)
    _log(
        "apply labels enqueued "
        f"button={button_id} checkbox={checkbox_id} text_label={text_label_id} scrollable={scrollable_id}"
    )
    _schedule_report("state after apply labels")


def _try_set_clone_title() -> None:
    root_id = _current_root_id()
    if root_id <= 0:
        _log("set title skipped because target root is unavailable")
        return
    def _invoke() -> None:
        GWUI.SetFrameTitleByFrameId(root_id, TITLE_TEXT)

    Py4GW.Game.enqueue(_invoke)
    _log(f"set title enqueued target={TARGET_MODE} root={root_id} title='{TITLE_TEXT}'")
    _schedule_report("state after set title")


def _set_clone_visible(is_visible: bool) -> None:
    root_id = _current_root_id()
    if root_id <= 0:
        _log(f"set visible skipped because target root is unavailable target={is_visible}")
        return
    def _invoke() -> None:
        GWUI.SetFrameVisibleByFrameId(root_id, is_visible)

    Py4GW.Game.enqueue(_invoke)
    _log(f"set visible enqueued target={TARGET_MODE} root={root_id} is_visible={is_visible}")
    _schedule_report(f"state after set visible {is_visible}")


def _set_clone_disabled(is_disabled: bool) -> None:
    root_id = _current_root_id()
    if root_id <= 0:
        _log(f"set disabled skipped because target root is unavailable target={is_disabled}")
        return
    def _invoke() -> None:
        GWUI.SetFrameDisabledByFrameId(root_id, is_disabled)

    Py4GW.Game.enqueue(_invoke)
    _log(f"set disabled enqueued target={TARGET_MODE} root={root_id} is_disabled={is_disabled}")
    _schedule_report(f"state after set disabled {is_disabled}")


def _test_read_only(is_read_only: bool) -> None:
    target = int(MANUAL_READONLY_TARGET or 0)
    if target <= 0:
        _log("set read-only skipped because manual target frame id is 0")
        return
    def _invoke() -> None:
        GWUI.SetReadOnlyByFrameId(target, is_read_only)

    Py4GW.Game.enqueue(_invoke)
    _log(f"set read-only enqueued target={target} is_read_only={is_read_only}")


def _query_read_only() -> None:
    target = int(MANUAL_READONLY_TARGET or 0)
    if target <= 0:
        _log("query read-only skipped because manual target frame id is 0")
        return
    current = GWUI.IsReadOnlyByFrameId(target)
    _log(f"query read-only target={target} current={current}")


def _draw_window() -> None:
    global WINDOW_OPEN
    global READ_DELAY_SECONDS
    global MANUAL_READONLY_TARGET

    PyImGui.set_next_window_size(760, 760)
    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.text("goal: validate migrated UI primitives against original DevText or a clone")
    PyImGui.separator()
    PyImGui.text("exact steps:")
    PyImGui.text("1) Open Original DevText or Create Clone Window")
    PyImGui.text("2) Test one create primitive at a time")
    PyImGui.text("3) Apply Margins")
    PyImGui.text("4) Apply Labels")
    PyImGui.text("5) Test Hide/Show and Disable/Enable")
    PyImGui.text("6) Dump Current State")
    PyImGui.text("manual: use the read-only target only if you know an editable frame id")
    PyImGui.separator()

    READ_DELAY_SECONDS = float(
        _normalize_input_int(PyImGui.input_int("Read Delay (ms)", int(READ_DELAY_SECONDS * 1000.0)), int(READ_DELAY_SECONDS * 1000.0))
    ) / 1000.0
    MANUAL_READONLY_TARGET = _normalize_input_int(
        PyImGui.input_int("Manual ReadOnly Target", int(MANUAL_READONLY_TARGET)),
        int(MANUAL_READONLY_TARGET),
    )

    if PyImGui.button("Create Clone Window"):
        _create_clone()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Open Original DevText"):
        _open_original_devtext()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Dump Current State"):
        _dump_state("manual state report")

    if PyImGui.button("Create Button"):
        _create_button()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Create Checkbox"):
        _create_checkbox()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Create Scrollable"):
        _create_scrollable()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Create Text Label"):
        _create_text_label()

    if PyImGui.button("Apply Margins"):
        _apply_margins_to_created_controls()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Apply Labels"):
        _apply_labels()

    if PyImGui.button("Try Clone Title Setter"):
        _try_set_clone_title()
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Hide Clone"):
        _set_clone_visible(False)
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Show Clone"):
        _set_clone_visible(True)

    if PyImGui.button("Disable Clone"):
        _set_clone_disabled(True)
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Enable Clone"):
        _set_clone_disabled(False)

    if PyImGui.button("Set ReadOnly True"):
        _test_read_only(True)
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Set ReadOnly False"):
        _test_read_only(False)
    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Query ReadOnly"):
        _query_read_only()

    PyImGui.separator()
    PyImGui.text(f"target_mode={TARGET_MODE}")
    PyImGui.text(
        "created ids: "
        f"button={CREATED_IDS['button']} "
        f"checkbox={CREATED_IDS['checkbox']} "
        f"scrollable={CREATED_IDS['scrollable']} "
        f"text_label={CREATED_IDS['text_label']}"
    )

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("test flow:")
        _log("1) click 'Open Original DevText' or 'Create Clone Window'")
        _log("2) click one create primitive at a time: Button, Checkbox, Scrollable, or Text Label")
        _log("3) after each create, wait for the delayed state report")
        _log("4) click 'Apply Margins'")
        _log("5) click 'Apply Labels'")
        _log("6) click 'Hide Clone' then 'Show Clone'")
        _log("7) click 'Disable Clone' then 'Enable Clone'")
        _log("8) click 'Dump Current State'")
        _log("manual: set 'Manual ReadOnly Target' only if you know an editable frame id")
        _log("reports are delayed after mutating calls so frame data can settle")
    _process_pending_reports()
    _draw_window()
