"""
Native Button Test Harness — CtlBtnProc (Approach 1).

Creates an empty window, then a native GW button inside it using the
CtlBtnProc engine-level FrameProc. Every step outputs self-describing
debug data for troubleshooting.

Usage: Place in Widgets/ folder and load via Widget Manager.
"""
import time
import ctypes
from typing import Optional

import Py4GW
import PyImGui

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI
from Py4GWCoreLib.native_src.methods.ButtonMethods import (
    ButtonMethods,
    CtlBtnProc_Callback,
    FrameCreate_Func,
    CtlBtnSetTextLiteral_Func,
)
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction

# ── Metadata ──────────────────────────────────────────────────────────
MODULE_NAME = "Native Button Test Harness"
SCRIPT_REVISION = "2026-06-17-cbtn-test-1"
WINDOW_OPEN = True
INITIALIZED = False
READ_DELAY_SECONDS = 0.60

# ── Tunable Constants ─────────────────────────────────────────────────
WINDOW_LABEL = "Py4GW_ButtonTest_Window"
WINDOW_TITLE = "Py4GW Button Test"
WINDOW_X = 200
WINDOW_Y = 200
WINDOW_WIDTH = 320
WINDOW_HEIGHT = 200

BUTTON_LABEL = "PyTestButton"
BUTTON_CHILD_INDEX = 0x20
BUTTON_FLAGS = 0x40000       # IME-style: flat background
BUTTON_TEXT = "Click Me"

# ── Runtime State ─────────────────────────────────────────────────────
PENDING_REPORTS: list[tuple[float, str]] = []
LAST_WINDOW_ID = 0
LAST_BUTTON_ID = 0
LAST_ERROR = ""
LAST_ACTION = "idle"
CALL_COUNTER = 0
SCANNER_STATUS = {}


# =========================================================================
# Logging & Debug
# =========================================================================

def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _error(message: str) -> None:
    global LAST_ERROR
    LAST_ERROR = message
    print(f"[{MODULE_NAME}] ERROR: {message}")


def _schedule_report(prefix: str, delay_seconds: float | None = None) -> None:
    delay = READ_DELAY_SECONDS if delay_seconds is None else max(0.0, float(delay_seconds))
    PENDING_REPORTS.append((time.time() + delay, prefix))
    _log(f"  scheduled report '{prefix}' in {delay:.2f}s")


def _process_pending_reports() -> None:
    if not PENDING_REPORTS:
        return
    now = time.time()
    ready = []
    pending = []
    for scheduled_at, prefix in PENDING_REPORTS:
        (ready if scheduled_at <= now else pending).append((scheduled_at, prefix))
    PENDING_REPORTS[:] = pending
    for _, prefix in ready:
        _dump_state(prefix)


# =========================================================================
# Frame Inspection
# =========================================================================

def _frame_summary(frame_id: int) -> str:
    """Human-readable summary of a frame's state."""
    frame_id = int(frame_id or 0)
    if frame_id <= 0:
        return "frame_id=0 (INVALID)"
    try:
        frame = UIManager.GetFrameByID(frame_id)
        left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
        children = _list_children(frame_id)
        return (
            f"frame_id={frame_id} "
            f"parent_id={int(frame.parent_id)} "
            f"child_offset=0x{int(frame.child_offset_id):X} "
            f"created={bool(frame.is_created)} "
            f"visible={bool(frame.is_visible)} "
            f"state=0x{int(frame.frame_state):X} "
            f"rect=({int(left)},{int(top)})-({int(right)},{int(bottom)}) "
            f"children={children}"
        )
    except Exception as exc:
        return f"frame_id={frame_id} summary_error={exc}"


def _list_children(parent_id: int, limit: int = 16) -> list[int]:
    """List child frame IDs for a parent."""
    children = []
    for candidate_id in UIManager.GetFrameArray():
        try:
            frame = UIManager.GetFrameByID(candidate_id)
            if int(frame.parent_id) == parent_id:
                children.append(int(candidate_id))
        except Exception:
            continue
    children.sort()
    return children[:limit]


def _scan_frame_tree(root_id: int, depth: int = 0, max_depth: int = 3) -> None:
    """Recursively log the frame tree rooted at root_id."""
    if depth > max_depth or root_id <= 0:
        return
    indent = "  " * depth
    try:
        frame = UIManager.GetFrameByID(root_id)
        left, top, right, bottom = UIManager.GetFrameCoords(root_id)
        _log(
            f"{indent}[{root_id}] offset=0x{int(frame.child_offset_id):X} "
            f"created={bool(frame.is_created)} visible={bool(frame.is_visible)} "
            f"rect=({int(left)},{int(top)})-({int(right)},{int(bottom)})"
        )
    except Exception as exc:
        _log(f"{indent}[{root_id}] error={exc}")
        return
    children = _list_children(root_id)
    for child_id in children:
        _scan_frame_tree(child_id, depth + 1, max_depth)


# =========================================================================
# Scanner Verification
# =========================================================================

def _verify_scanners() -> dict:
    """Verify all scanner-resolved addresses and return status dict."""
    status = {}

    # CtlBtnProc
    try:
        valid = CtlBtnProc_Callback.is_valid()
        addr = CtlBtnProc_Callback.func_ptr if valid else 0
        status["CtlBtnProc"] = {
            "valid": valid,
            "address": f"0x{addr:08X}" if addr else "0x00000000",
            "pattern": "26-byte prologue (1 match verified)",
        }
    except Exception as exc:
        status["CtlBtnProc"] = {"valid": False, "error": str(exc)}

    # FrameCreate
    try:
        valid = FrameCreate_Func.is_valid() if hasattr(FrameCreate_Func, 'is_valid') else (FrameCreate_Func.address != 0)
        addr = FrameCreate_Func.address
        status["FrameCreate"] = {
            "valid": valid,
            "address": f"0x{addr:08X}" if addr else "0x00000000",
            "pattern": "GWCA CreateUIComponent pattern",
        }
    except Exception as exc:
        status["FrameCreate"] = {"valid": False, "error": str(exc)}

    # CtlBtnSetTextLiteral
    try:
        valid = CtlBtnSetTextLiteral_Func.is_valid() if hasattr(CtlBtnSetTextLiteral_Func, 'is_valid') else (CtlBtnSetTextLiteral_Func.address != 0)
        addr = CtlBtnSetTextLiteral_Func.address
        status["CtlBtnSetTextLiteral"] = {
            "valid": valid,
            "address": f"0x{addr:08X}" if addr else "0x00000000",
            "pattern": "7-byte unique (push 0; push ebx; push 0x5E; push edi; call)",
        }
    except Exception as exc:
        status["CtlBtnSetTextLiteral"] = {"valid": False, "error": str(exc)}

    status["all_valid"] = all(v["valid"] for v in status.values() if isinstance(v, dict) and "valid" in v)
    return status


# =========================================================================
# Window & Button Actions
# =========================================================================

def _current_window_id() -> int:
    return int(UIManager.GetFrameIDByLabel(WINDOW_LABEL) or 0)


def _dump_state(prefix: str) -> None:
    """Log full debug state at a point in time."""
    window_id = _current_window_id()
    _log(f"--- STATE DUMP: {prefix} ---")
    _log(f"  window_id={window_id} last_button_id={LAST_BUTTON_ID}")
    if window_id > 0:
        _log(f"  window: {_frame_summary(window_id)}")
        _log("  frame tree:")
        _scan_frame_tree(window_id, depth=0, max_depth=2)
    if LAST_BUTTON_ID > 0:
        _log(f"  button: {_frame_summary(LAST_BUTTON_ID)}")
    _log(f"  errors: {'(none)' if not LAST_ERROR else LAST_ERROR}")
    _log("--- END STATE ---")


def _create_window() -> None:
    """Step 1: Create the empty container window."""
    global LAST_WINDOW_ID, LAST_ACTION

    # Check if already exists
    existing = _current_window_id()
    if existing > 0:
        _log(f"Window already exists: frame_id={existing} — skipping creation")
        LAST_WINDOW_ID = existing
        _dump_state("pre-existing window")
        return

    _log(f"Creating window: label='{WINDOW_LABEL}' title='{WINDOW_TITLE}' "
         f"pos=({WINDOW_X},{WINDOW_Y}) size=({WINDOW_WIDTH}x{WINDOW_HEIGHT})")

    def _invoke():
        global LAST_WINDOW_ID
        LAST_WINDOW_ID = int(
            GWUI.CreateWindow(
                float(WINDOW_X), float(WINDOW_Y),
                float(WINDOW_WIDTH), float(WINDOW_HEIGHT),
                title=WINDOW_TITLE,
            )
            or 0
        )
        _log(f"  CreateWindow returned frame_id={LAST_WINDOW_ID}")

    Py4GW.Game.enqueue(_invoke)
    LAST_ACTION = "create_window"
    _log("  enqueued CreateWindow")
    _schedule_report("state after CreateWindow")


def _create_button() -> None:
    """Step 2: Create a button inside the window."""
    global LAST_BUTTON_ID, LAST_ACTION, CALL_COUNTER

    window_id = _current_window_id()
    if window_id <= 0:
        _error("Cannot create button: window does not exist. Create window first.")
        return

    CALL_COUNTER += 1
    call_id = CALL_COUNTER

    _log(f"[call #{call_id}] Creating button:")
    _log(f"  parent_frame_id = {window_id}")
    _log(f"  component_flags = 0x{BUTTON_FLAGS:X}")
    _log(f"  child_index     = 0x{BUTTON_CHILD_INDEX:X} ({BUTTON_CHILD_INDEX})")
    _log(f"  label_text      = '{BUTTON_TEXT}'")

    # Verify scanners before attempting
    scanner = _verify_scanners()
    if not scanner["all_valid"]:
        _error(f"Scanner resolution FAILED: {scanner}")
        return
    _log(f"  scanners: all valid ✓ (CtlBtnProc=0x{CtlBtnProc_Callback.func_ptr:08X}, "
         f"FrameCreate=0x{FrameCreate_Func.address:08X}, "
         f"CtlBtnSetTextLiteral=0x{CtlBtnSetTextLiteral_Func.address:08X})")

    # Snapshot BEFORE
    before_children = _list_children(window_id)
    _log(f"  children BEFORE creation: {before_children}")

    def _invoke():
        global LAST_BUTTON_ID, LAST_ERROR
        try:
            _log(f"[call #{call_id}] Game thread: executing ButtonMethods.create_native_button_sync()")
            LAST_BUTTON_ID = int(
                ButtonMethods.create_native_button_sync(
                    parent_frame_id=window_id,
                    component_flags=BUTTON_FLAGS,
                    child_index=BUTTON_CHILD_INDEX,
                    label_text=BUTTON_TEXT,
                )
                or 0
            )
            _log(f"[call #{call_id}] Game thread: create_native_button_sync returned frame_id={LAST_BUTTON_ID}")

            if LAST_BUTTON_ID == 0:
                _error(f"[call #{call_id}] Button creation returned 0 (FAILED)")
            else:
                _log(f"[call #{call_id}] Button created successfully! frame_id={LAST_BUTTON_ID}")
                # Verify button exists
                try:
                    frame = UIManager.GetFrameByID(LAST_BUTTON_ID)
                    _log(f"[call #{call_id}] Button frame: created={bool(frame.is_created)}, "
                         f"visible={bool(frame.is_visible)}, "
                         f"parent_id={int(frame.parent_id)}, "
                         f"child_offset=0x{int(frame.child_offset_id):X}")
                except Exception as exc:
                    _error(f"[call #{call_id}] Button frame_id={LAST_BUTTON_ID} but GetFrameByID failed: {exc}")

        except Exception as exc:
            _error(f"[call #{call_id}] Exception during button creation: {exc}")
            import traceback
            traceback.print_exc()

    Py4GW.Game.enqueue(_invoke)
    LAST_ACTION = f"create_button_{call_id}"
    _log(f"[call #{call_id}] enqueued button creation")
    _schedule_report(f"state after CreateButton #{call_id}")


def _destroy_button() -> None:
    """Destroy the last-created button."""
    global LAST_BUTTON_ID, LAST_ACTION
    btn_id = LAST_BUTTON_ID
    if btn_id <= 0:
        _log("No button to destroy")
        return
    _log(f"Destroying button frame_id={btn_id}")

    def _invoke():
        global LAST_BUTTON_ID
        try:
            result = UIManager.DestroyUIComponentByFrameId(LAST_BUTTON_ID)
            _log(f"  DestroyUIComponentByFrameId({LAST_BUTTON_ID}) returned {result}")
        except Exception as exc:
            _error(f"Destroy failed: {exc}")
        LAST_BUTTON_ID = 0

    Py4GW.Game.enqueue(_invoke)
    LAST_ACTION = "destroy_button"
    _schedule_report("state after DestroyButton")


def _destroy_window() -> None:
    """Destroy the window and everything in it."""
    global LAST_WINDOW_ID, LAST_BUTTON_ID, LAST_ACTION
    window_id = _current_window_id()
    if window_id <= 0:
        _log("No window to destroy")
        return
    _log(f"Destroying window frame_id={window_id} (and all children)")
    LAST_BUTTON_ID = 0

    def _invoke():
        try:
            result = UIManager.DestroyUIComponentByFrameId(window_id)
            _log(f"  DestroyUIComponentByFrameId({window_id}) returned {result}")
        except Exception as exc:
            _error(f"Destroy failed: {exc}")

    Py4GW.Game.enqueue(_invoke)
    LAST_WINDOW_ID = 0
    LAST_ACTION = "destroy_window"
    _schedule_report("state after DestroyWindow")


def _dump_scanner_status() -> None:
    """Log full scanner resolution status."""
    status = _verify_scanners()
    SCANNER_STATUS.clear()
    SCANNER_STATUS.update(status)
    _log("--- SCANNER STATUS ---")
    for name, info in status.items():
        if name == "all_valid":
            continue
        if isinstance(info, dict):
            _log(f"  {name}: valid={info.get('valid')}, addr={info.get('address','?')}, "
                 f"pattern='{info.get('pattern','?')}'")
    _log(f"  ALL VALID: {status.get('all_valid', False)}")
    _log("--- END SCANNER ---")


def _dump_full_state() -> None:
    """Log complete debug state."""
    _dump_scanner_status()
    _dump_state("manual dump")


# =========================================================================
# ImGui Widget
# =========================================================================

def configure():
    """Widget Manager entry point."""
    pass


def main():
    """Main render loop — called every frame by Widget Manager."""
    global WINDOW_OPEN, INITIALIZED, SCANNER_STATUS

    if not INITIALIZED:
        _log(f"=== {MODULE_NAME} v{SCRIPT_REVISION} initialized ===")
        _dump_scanner_status()
        INITIALIZED = True

    _process_pending_reports()

    if not WINDOW_OPEN:
        return

    if PyImGui.begin(MODULE_NAME, PyImGui.ImGuiWindowFlags_AlwaysAutoResize)[0]:
        # ── Section: Scanner Status ──
        PyImGui.text_colored("=== Scanner Resolution ===", (0.4, 0.8, 1.0, 1.0))
        if not SCANNER_STATUS:
            SCANNER_STATUS = _verify_scanners()

        all_ok = SCANNER_STATUS.get("all_valid", False)
        color = (0.2, 1.0, 0.2, 1.0) if all_ok else (1.0, 0.3, 0.3, 1.0)
        PyImGui.text_colored(f"All scanners valid: {all_ok}", color)

        for name in ["CtlBtnProc", "FrameCreate", "CtlBtnSetTextLiteral"]:
            info = SCANNER_STATUS.get(name, {})
            status_text = "OK" if info.get("valid") else "FAIL"
            status_color = (0.2, 1.0, 0.2, 1.0) if info.get("valid") else (1.0, 0.5, 0.2, 1.0)
            PyImGui.text_colored(
                f"  {name}: {status_text} @ {info.get('address', '?')}",
                status_color,
            )
            if info.get("error"):
                PyImGui.text_colored(f"    error: {info['error']}", (1.0, 0.3, 0.3, 1.0))

        PyImGui.separator()

        # ── Section: Window ──
        PyImGui.text_colored("=== Window ===", (0.4, 0.8, 1.0, 1.0))
        window_id = _current_window_id()
        PyImGui.text(f"Window frame_id: {window_id} (label='{WINDOW_LABEL}')")
        if window_id > 0:
            PyImGui.text(f"  {_frame_summary(window_id)}")

        if PyImGui.button("1. Create Window"):
            _create_window()
        PyImGui.same_line()
        if PyImGui.button("Destroy Window"):
            _destroy_window()

        PyImGui.separator()

        # ── Section: Button ──
        PyImGui.text_colored("=== Button ===", (0.4, 0.8, 1.0, 1.0))
        PyImGui.text(f"Last button frame_id: {LAST_BUTTON_ID}")
        if LAST_BUTTON_ID > 0:
            PyImGui.text(f"  {_frame_summary(LAST_BUTTON_ID)}")

        PyImGui.text(f"Flags: 0x{BUTTON_FLAGS:X}  Child index: 0x{BUTTON_CHILD_INDEX:X}")
        PyImGui.text(f"Label: '{BUTTON_TEXT}'")

        if PyImGui.button("2. Create Button"):
            _create_button()
        PyImGui.same_line()
        if PyImGui.button("Destroy Button"):
            _destroy_button()

        PyImGui.separator()

        # ── Section: Status ──
        PyImGui.text_colored("=== Status ===", (0.4, 0.8, 1.0, 1.0))
        PyImGui.text(f"Last action: {LAST_ACTION}")
        error_color = (1.0, 0.3, 0.3, 1.0) if LAST_ERROR else (0.5, 0.5, 0.5, 1.0)
        PyImGui.text_colored(f"Last error: {LAST_ERROR if LAST_ERROR else '(none)'}", error_color)
        PyImGui.text(f"Call counter: {CALL_COUNTER}")
        PyImGui.text(f"Pending reports: {len(PENDING_REPORTS)}")

        PyImGui.separator()

        # ── Section: Debug Actions ──
        PyImGui.text_colored("=== Debug ===", (0.7, 0.7, 0.3, 1.0))
        if PyImGui.button("Dump Full State"):
            _dump_full_state()
        PyImGui.same_line()
        if PyImGui.button("Refresh Scanners"):
            SCANNER_STATUS = {}
            _dump_scanner_status()

        PyImGui.text("Steps: 1) Create Window  2) Create Button")
        PyImGui.text("Check Py4GW console for detailed logs.")
        PyImGui.text(f"({SCRIPT_REVISION})")

    PyImGui.end()
