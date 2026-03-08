import time

import PyImGui

from Py4GWCoreLib import UIManager


SCRIPT_NAME = "Original DevText Caption Test"
SCRIPT_REVISION = "2026-03-07-original-devtext-caption-test-1"
TARGET_TITLE = "Py4GW Original DevText Title"
READ_DELAY_SECONDS = 0.50

_scheduled_report_at = 0.0
_scheduled_report_prefix = ""


def _log(message: str) -> None:
    print(f"[{SCRIPT_NAME}] {message}")


def _frame_summary(frame_id: int) -> str:
    frame_id = int(frame_id or 0)
    if frame_id <= 0:
        return "(frame_id=0)"
    try:
        frame = UIManager.GetFrameByID(frame_id)
    except Exception as exc:
        return f"(frame_id={frame_id} error={exc})"
    left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
    return (
        f"(frame_id={frame_id} parent_id={int(frame.parent_id)} "
        f"child_offset_id={int(frame.child_offset_id)} "
        f"is_created={bool(frame.is_created)} is_visible={bool(frame.is_visible)} "
        f"frame_state=0x{int(frame.frame_state):X} rect=({left},{top})-({right},{bottom}))"
    )


def _current_devtext_frame_id() -> int:
    return int(UIManager.GetDevTextFrameID() or 0)


def _report_state(prefix: str) -> None:
    root = _current_devtext_frame_id()
    child0 = int(UIManager.GetChildFrameByFrameId(root, 0) or 0) if root > 0 else 0
    _log(f"{prefix} root={_frame_summary(root)}")
    _log(f"{prefix} root[0]={_frame_summary(child0)}")


def _schedule_report(prefix: str) -> None:
    global _scheduled_report_at, _scheduled_report_prefix
    _scheduled_report_prefix = prefix
    _scheduled_report_at = time.monotonic() + READ_DELAY_SECONDS
    _log(f"scheduled report prefix='{prefix}' delay={READ_DELAY_SECONDS:.2f}s")


def _maybe_run_scheduled_report() -> None:
    global _scheduled_report_at, _scheduled_report_prefix
    if _scheduled_report_at <= 0.0:
        return
    if time.monotonic() < _scheduled_report_at:
        return
    prefix = _scheduled_report_prefix
    _scheduled_report_at = 0.0
    _scheduled_report_prefix = ""
    _report_state(prefix)


def _open_original_devtext() -> None:
    frame_id = UIManager.OpenDevTextWindow()
    _log(f"open original requested immediate_frame_id={int(frame_id or 0)}")
    _schedule_report("state after open original")


def _set_original_title() -> None:
    frame_id = _current_devtext_frame_id()
    if frame_id <= 0:
        _log("set title skipped because DevText root is not available")
        return
    _report_state("state before set title")
    result = bool(UIManager.SetFrameTitleByFrameId(frame_id, TARGET_TITLE))
    _log(f"set title root={frame_id} title='{TARGET_TITLE}' result={result}")
    _schedule_report("state after set title")


def _draw_controls() -> None:
    if PyImGui.button("Open Original DevText"):
        _open_original_devtext()
    if PyImGui.button("Report State"):
        _report_state("manual state report")
    if PyImGui.button("Set Original Title"):
        _set_original_title()


def main():
    _maybe_run_scheduled_report()
    PyImGui.begin(SCRIPT_NAME)
    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.separator()
    PyImGui.text("Test flow:")
    PyImGui.text("1) Click 'Open Original DevText'")
    PyImGui.text("2) Wait for 'state after open original'")
    PyImGui.text("3) Click 'Set Original Title'")
    PyImGui.text("4) Wait for 'state after set title'")
    PyImGui.separator()
    _draw_controls()
    PyImGui.end()


if __name__ == "__main__":
    main()
