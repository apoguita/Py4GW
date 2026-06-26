"""
Native Button Test Harness — CtlBtnProc (Approach 1).

Creates an empty window, then a native GW button inside it using the
CtlBtnProc engine-level FrameProc. Every step outputs self-describing
debug data for troubleshooting.

Usage: Run from UI_RE folder.
"""
import time
import ctypes
from typing import Optional

import Py4GW
import PyImGui
import PyUIManager

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI
from Py4GWCoreLib.native_src.methods.ButtonMethods import (
    ButtonMethods,
    CtlBtnProc_Callback,
    FrameCreate_Func,
    CtlBtnSetTextLiteral_Func,
)
from Py4GWCoreLib.Scanner import Scanner, ScannerSection

# ── Metadata ──────────────────────────────────────────────────────────
MODULE_NAME = "Native Button Test Harness"
SCRIPT_REVISION = "2026-06-17-cbtn-test-2 (EXE 06-14)"
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

# Alternative patterns to try if primary fails (build-robust fallbacks)
ALT_PATTERNS = [
    # Primary: 26-byte unique prologue (verified across 05-30 and 06-14 builds)
    {
        "name": "primary_26byte",
        "pattern": (
            b"\x55\x8B\xEC\x83\xEC\x30\x53\x8B\x5D\x08\x56\x57"
            b"\x8B\x7D\x0C\x8B\x43\x04\x8B\x53\x08\x48\x83\xF8\x5E"
        ),
        "mask": "xxxxxxxxxxxxxxxxxxxxxxxxxx",
        "offset": 0,
        "description": "26-byte prologue + CMP EAX,0x5E (verified 05-30/06-14)",
    },
    # Secondary: Short stack-frame prologue (9 bytes)
    {
        "name": "short_9byte",
        "pattern": b"\x83\xEC\x30\x53\x8B\x5D\x08\x56\x57",
        "mask": "xxxxxxxxx",
        "offset": 0,
        "description": "SUB ESP,0x30; PUSH EBX; MOV EBX,[EBP+8]; PUSH ESI; PUSH EDI",
    },
    # Tertiary: Max-message dispatch (CMP EAX,0x5E; JA)
    {
        "name": "max_msg_6byte",
        "pattern": b"\x48\x83\xF8\x5E\x0F\x87",
        "mask": "xxxxxx",
        "offset": -0x100,  # use ToFunctionStart to go back
        "description": "CMP EAX,0x5E; JA — unique max message for CtlBtnProc",
    },
]

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
# Scanner Verification — With Fallback Pattern Search
# =========================================================================

def _find_ctlbntextliteral_with_fallback() -> Optional[int]:
    """Try to find CtlBtnSetTextLiteral using string-based approach."""
    # Search for assertion string in CtlBtn.cpp that references SetText
    addr = Scanner.FindAssertion("CtlBtn.cpp", "pBtn", 0, 0)
    if addr:
        _log(f"  Fallback: CtlBtn.cpp assertion 'pBtn' found at 0x{addr:08X}")
        return Scanner.ToFunctionStart(addr, 0x200)
    return None


def _verify_scanners() -> dict:
    """Verify all scanner-resolved addresses with fallback attempts."""
    status = {}

    # ── CtlBtnProc ──
    result = {"valid": False, "address": "0x00000000", "method": None}
    try:
        # Try primary pattern
        if CtlBtnProc_Callback.is_valid():
            result["valid"] = True
            result["address"] = f"0x{CtlBtnProc_Callback.func_ptr:08X}"
            result["method"] = "primary 26-byte pattern"
        else:
            # Try alternative pattern
            _log("  Primary CtlBtnProc pattern failed — trying alternatives...")
            for alt in ALT_PATTERNS:
                if alt["pattern"] is None:
                    continue  # skip string anchor for now
                try:
                    alt_addr = Scanner.Find(alt["pattern"], alt["mask"], alt["offset"], ScannerSection.TEXT)
                    if alt_addr:
                        result["valid"] = True
                        result["address"] = f"0x{alt_addr:08X}"
                        result["method"] = f"alt: {alt['name']} ({alt['description']})"
                        _log(f"  Found via {alt['name']}: 0x{alt_addr:08X}")
                        break
                except Exception:
                    continue
    except Exception as exc:
        result["error"] = str(exc)
    status["CtlBtnProc"] = result

    # ── FrameCreate ──
    result = {"valid": False, "address": "0x00000000", "method": None}
    try:
        if FrameCreate_Func.is_valid():
            result["valid"] = True
            try:
                result["address"] = f"0x{FrameCreate_Func.get_address():08X}"
            except Exception:
                result["address"] = f"0x{FrameCreate_Func.func_ptr:08X}" if isinstance(FrameCreate_Func.func_ptr, int) else "callable"
            result["method"] = "GWCA CreateUIComponent pattern"
    except Exception as exc:
        result["error"] = str(exc)
    status["FrameCreate"] = result

    # ── CtlBtnSetTextLiteral ──
    result = {"valid": False, "address": "0x00000000", "method": None}
    try:
        if CtlBtnSetTextLiteral_Func.is_valid():
            result["valid"] = True
            try:
                result["address"] = f"0x{CtlBtnSetTextLiteral_Func.get_address():08X}"
            except Exception:
                result["address"] = f"0x{CtlBtnSetTextLiteral_Func.func_ptr:08X}" if isinstance(CtlBtnSetTextLiteral_Func.func_ptr, int) else "callable"
            result["method"] = "primary 7-byte pattern"
    except Exception as exc:
        result["error"] = str(exc)
    status["CtlBtnSetTextLiteral"] = result

    status["all_valid"] = all(v.get("valid", False) for k, v in status.items() if k != "all_valid")
    return status


# =========================================================================
# Window & Button Actions
# =========================================================================

def _current_window_id() -> int:
    """Get the window frame ID. Uses label lookup first, falls back to LAST_WINDOW_ID."""
    # Try label lookup
    label_id = int(UIManager.GetFrameIDByLabel(WINDOW_LABEL) or 0)
    if label_id > 0:
        return label_id
    # Fall back to the frame ID we stored on creation
    return int(LAST_WINDOW_ID or 0)


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
        _error(f"Scanner resolution FAILED. Status: { {k:v for k,v in scanner.items() if k != 'all_valid'} }")
        _log("  Cannot proceed — scanner patterns didn't match. Possible EXE version mismatch.")
        return

    cb_addr = CtlBtnProc_Callback.func_ptr
    fc_addr = FrameCreate_Func.get_address()
    st_addr = CtlBtnSetTextLiteral_Func.get_address()
    _log(f"  scanners: all valid ✓")
    _log(f"    CtlBtnProc             = 0x{cb_addr:08X} ({scanner['CtlBtnProc']['method']})")
    _log(f"    FrameCreate            = 0x{fc_addr:08X} ({scanner['FrameCreate']['method']})")
    _log(f"    CtlBtnSetTextLiteral   = 0x{st_addr:08X} ({scanner['CtlBtnSetTextLiteral']['method']})")

    # Snapshot BEFORE
    before_children = _list_children(window_id)
    _log(f"  children BEFORE creation: {before_children}")

    def _invoke():
        global LAST_BUTTON_ID, LAST_ERROR
        try:
            _log(f"[call #{call_id}] Game thread: executing create_native_button_sync()")
            LAST_BUTTON_ID = int(
                ButtonMethods.create_native_button_sync(
                    parent_frame_id=window_id,
                    component_flags=BUTTON_FLAGS,
                    child_index=BUTTON_CHILD_INDEX,
                    label_text=BUTTON_TEXT,
                )
                or 0
            )
            _log(f"[call #{call_id}] create_native_button_sync returned frame_id={LAST_BUTTON_ID}")

            if LAST_BUTTON_ID == 0:
                _error(f"[call #{call_id}] Button creation returned 0 (FAILED)")
            else:
                _log(f"[call #{call_id}] Button created! frame_id={LAST_BUTTON_ID}")
                try:
                    frame = UIManager.GetFrameByID(LAST_BUTTON_ID)
                    _log(
                        f"[call #{call_id}] Button state: created={bool(frame.is_created)}, "
                        f"visible={bool(frame.is_visible)}, "
                        f"parent_id={int(frame.parent_id)}, "
                        f"child_offset=0x{int(frame.child_offset_id):X}"
                    )
                except Exception as exc:
                    _error(f"[call #{call_id}] GetFrameByID({LAST_BUTTON_ID}) failed: {exc}")
        except Exception as exc:
            _error(f"[call #{call_id}] Exception: {exc}")
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
            UIManager.DestroyUIComponentByFrameId(LAST_BUTTON_ID)
            _log(f"  DestroyUIComponentByFrameId({LAST_BUTTON_ID}) called")
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
            UIManager.DestroyUIComponentByFrameId(window_id)
            _log(f"  DestroyUIComponentByFrameId({window_id}) called")
        except Exception as exc:
            _error(f"Destroy failed: {exc}")

    Py4GW.Game.enqueue(_invoke)
    LAST_WINDOW_ID = 0
    LAST_ACTION = "destroy_window"
    _schedule_report("state after DestroyWindow")


def _dump_scanner_status() -> None:
    """Log full scanner resolution status including fallback attempts."""
    status = _verify_scanners()
    SCANNER_STATUS.clear()
    SCANNER_STATUS.update(status)
    _log("--- SCANNER STATUS ---")
    for name in ["CtlBtnProc", "FrameCreate", "CtlBtnSetTextLiteral"]:
        info = status.get(name, {})
        _log(f"  {name}: valid={info.get('valid')}, addr={info.get('address','?')}, "
             f"method={info.get('method','?')}")
        if info.get("error"):
            _log(f"    error: {info['error']}")
    _log(f"  ALL VALID: {status.get('all_valid', False)}")
    _log("--- END SCANNER ---")

    if not status.get("all_valid"):
        _log("  ↓ SCANNER FAILURE — possible causes:")
        _log("    1. EXE build mismatch: analyzed 05-30-2026, runtime may differ")
        _log("    2. Pattern bytes changed in a newer build")
        _log("    3. Scanner looking in wrong section (TEXT vs CODE)")
        _log("    Run 'Dump Full State' for more details.")


def _dump_full_state() -> None:
    """Log complete debug state."""
    _dump_scanner_status()
    _dump_state("manual dump")


# ── Individual test actions ─────────────────────────────────────────

def _action_verify_scanners() -> None:
    """Verify all scanner patterns resolve."""
    _dump_scanner_status()


def _action_create_window() -> None:
    """Create the empty container window."""
    _create_window()


def _action_create_button() -> None:
    """Create a button inside the window."""
    _create_button()


def _action_destroy_button() -> None:
    """Destroy the last button."""
    _destroy_button()


def _action_destroy_window() -> None:
    """Destroy the window."""
    _destroy_window()


def _action_dump_window_state() -> None:
    """Log the current window state."""
    window_id = _current_window_id()
    if window_id > 0:
        _log(f"Window: {_frame_summary(window_id)}")
        _log("  Frame tree:")
        _scan_frame_tree(window_id)
    else:
        _log("No window exists yet.")


def _action_dump_button_state() -> None:
    """Log the current button state."""
    if LAST_BUTTON_ID > 0:
        _log(f"Button: {_frame_summary(LAST_BUTTON_ID)}")
    else:
        _log("No button created yet.")


def _action_scan_full_tree() -> None:
    """Full recursive tree scan of all windows."""
    window_id = _current_window_id()
    if window_id <= 0:
        _log("No window — scanning root children instead.")
        _scan_frame_tree(0, max_depth=2)
    else:
        _scan_frame_tree(window_id, max_depth=4)


def _action_create_ctl_button() -> None:
    """Create a button using the new C++ CreateCtlButtonFrame binding."""
    global LAST_BUTTON_ID, LAST_ACTION, CALL_COUNTER
    window_id = _current_window_id()
    if window_id <= 0:
        _error("No window.")
        return
    CALL_COUNTER += 1
    call_id = CALL_COUNTER
    _log(f"[ctl #{call_id}] Creating via C++ CtlButton binding")
    def _invoke():
        global LAST_BUTTON_ID
        LAST_BUTTON_ID = int(
            PyUIManager.UIManager.create_ctl_button_frame_by_frame_id(
                window_id, BUTTON_FLAGS, BUTTON_CHILD_INDEX, BUTTON_TEXT, BUTTON_TEXT
            ) or 0
        )
        _log(f"[ctl #{call_id}] returned frame_id={LAST_BUTTON_ID}")
    Py4GW.Game.enqueue(_invoke)
    LAST_ACTION = f"ctl_button_{call_id}"
    _schedule_report(f"state after CtlButton #{call_id}")


def _action_create_gwca_button() -> None:
    """Create a button using the GWCA standard CreateButtonFrame (IUi::UiCtlBtnProc — styled)."""
    global LAST_BUTTON_ID, LAST_ACTION, CALL_COUNTER

    window_id = _current_window_id()
    if window_id <= 0:
        _error("Cannot create button: window does not exist.")
        return

    CALL_COUNTER += 1
    call_id = CALL_COUNTER
    _log(f"[gwca #{call_id}] Creating GWCA styled button:")
    _log(f"  parent_frame_id = {window_id}")
    _log(f"  label = '{BUTTON_TEXT}'")

    before_children = _list_children(window_id)
    _log(f"  children BEFORE: {before_children}")

    def _invoke():
        global LAST_BUTTON_ID, LAST_ERROR
        try:
            LAST_BUTTON_ID = int(
                PyUIManager.UIManager.create_button_frame_by_frame_id(
                    window_id,
                    0x300,              # GWCA standard button flags
                    BUTTON_CHILD_INDEX,
                    BUTTON_TEXT,        # name_enc
                    BUTTON_TEXT,        # component_label
                )
                or 0
            )
            _log(f"[gwca #{call_id}] CreateButtonFrameByFrameId returned frame_id={LAST_BUTTON_ID}")
            if LAST_BUTTON_ID > 0:
                frame = UIManager.GetFrameByID(LAST_BUTTON_ID)
                _log(f"[gwca #{call_id}] created={bool(frame.is_created)} visible={bool(frame.is_visible)}")
        except Exception as exc:
            _error(f"[gwca #{call_id}] GWCA button creation: {exc}")
            import traceback
            traceback.print_exc()

    Py4GW.Game.enqueue(_invoke)
    LAST_ACTION = f"gwca_button_{call_id}"
    _log(f"[gwca #{call_id}] enqueued GWCA button creation")
    _schedule_report(f"state after GWCA CreateButton #{call_id}")
    """Set text on the last-created button."""
    global LAST_BUTTON_ID
    if LAST_BUTTON_ID <= 0:
        _error("No button to set text on.")
        return
    if not CtlBtnSetTextLiteral_Func.is_valid():
        _error("CtlBtnSetTextLiteral not resolved.")
        return
    _log(f"Setting text '{BUTTON_TEXT}' on button {LAST_BUTTON_ID}")

    def _invoke():
        label_buf = ctypes.create_unicode_buffer(BUTTON_TEXT)
        CtlBtnSetTextLiteral_Func.directCall(
            ctypes.c_uint32(LAST_BUTTON_ID),
            label_buf,
        )
        _log(f"  CtlBtnSetTextLiteral({LAST_BUTTON_ID}, '{BUTTON_TEXT}') called")

    Py4GW.Game.enqueue(_invoke)
    _schedule_report("state after SetText")


def _action_dump_full_state() -> None:
    """Log complete debug state."""
    _dump_full_state()


# =========================================================================
# ImGui Widget — Individual Test Buttons
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

    # ── Begin window ──
    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        return

    # ── Scanner Status ──
    PyImGui.text_colored("=== Scanner Resolution ===", (0.4, 0.8, 1.0, 1.0))
    if not SCANNER_STATUS:
        SCANNER_STATUS = _verify_scanners()

    all_ok = SCANNER_STATUS.get("all_valid", False)
    color = (0.2, 1.0, 0.2, 1.0) if all_ok else (1.0, 0.3, 0.3, 1.0)
    PyImGui.text_colored(f"All scanners: {'OK' if all_ok else 'FAIL'}", color)

    for name in ["CtlBtnProc", "FrameCreate", "CtlBtnSetTextLiteral"]:
        info = SCANNER_STATUS.get(name, {})
        st = "OK" if info.get("valid") else "FAIL"
        sc = (0.2, 1.0, 0.2, 1.0) if info.get("valid") else (1.0, 0.5, 0.2, 1.0)
        PyImGui.text_colored(f"  {name}: {st} @ {info.get('address','?')}", sc)

    PyImGui.button("Verify Scanners", 0, 0)
    if not all_ok:
        PyImGui.text_colored("EXE 06-14 — scanner mismatch?", (1.0, 0.6, 0.2, 1.0))

    PyImGui.separator()

    # ── Window ──
    PyImGui.text_colored("=== 1. Window ===", (0.4, 0.8, 1.0, 1.0))
    window_id = _current_window_id()
    if window_id > 0:
        PyImGui.text(f"frame_id={window_id}  label='{WINDOW_LABEL}'")
        try:
            frame = UIManager.GetFrameByID(window_id)
            PyImGui.text(f"  created={bool(frame.is_created)}  visible={bool(frame.is_visible)}")
        except Exception:
            pass
    else:
        PyImGui.text_colored("(not created)", (0.5, 0.5, 0.5, 1.0))

    PyImGui.columns(2, "window_cols", True)
    if PyImGui.button("Create Window", 0, 0):
        _action_create_window()
    PyImGui.next_column()
    if PyImGui.button("Destroy Window", 0, 0):
        _action_destroy_window()
    PyImGui.columns(1, "", True)

    PyImGui.separator()

    # ── Button ──
    PyImGui.text_colored("=== 2. Button ===", (0.4, 0.8, 1.0, 1.0))
    if LAST_BUTTON_ID > 0:
        PyImGui.text(f"frame_id={LAST_BUTTON_ID}  label='{BUTTON_TEXT}'")
        try:
            frame = UIManager.GetFrameByID(LAST_BUTTON_ID)
            PyImGui.text(f"  created={bool(frame.is_created)}  visible={bool(frame.is_visible)}")
        except Exception:
            pass
    else:
        PyImGui.text_colored("(not created)", (0.5, 0.5, 0.5, 1.0))

    PyImGui.text(f"Flags=0x{BUTTON_FLAGS:X}  ChildIdx=0x{BUTTON_CHILD_INDEX:X}")

    PyImGui.columns(2, "btn_cols", True)
    if PyImGui.button("Engine (flat)", 0, 0):
        _action_create_button()
    PyImGui.next_column()
    if PyImGui.button("CtlBtn (C++)", 0, 0):
        _action_create_ctl_button()
    PyImGui.next_column()
    if PyImGui.button("GWCA (styled)", 0, 0):
        _action_create_gwca_button()
    PyImGui.next_column()
    if PyImGui.button("Set Text", 0, 0):
        _action_set_button_text()
    PyImGui.next_column()
    if PyImGui.button("Destroy", 0, 0):
        _action_destroy_button()
    PyImGui.columns(1, "", True)

    PyImGui.separator()

    # ── Inspect ──
    PyImGui.text_colored("=== 3. Inspect ===", (0.4, 0.8, 1.0, 1.0))
    PyImGui.columns(2, "insp_cols", True)
    if PyImGui.button("Dump Window State", 0, 0):
        _action_dump_window_state()
    PyImGui.next_column()
    if PyImGui.button("Dump Button State", 0, 0):
        _action_dump_button_state()
    PyImGui.next_column()
    if PyImGui.button("Scan Full Tree", 0, 0):
        _action_scan_full_tree()
    PyImGui.columns(1, "", True)

    PyImGui.separator()

    # ── Status ──
    PyImGui.text_colored("=== Status ===", (0.4, 0.8, 1.0, 1.0))
    PyImGui.text(f"Action: {LAST_ACTION}   Calls: {CALL_COUNTER}")
    ec = (1.0, 0.3, 0.3, 1.0) if LAST_ERROR else (0.5, 0.5, 0.5, 1.0)
    PyImGui.text_colored(f"Error: {LAST_ERROR if LAST_ERROR else '(none)'}", ec)
    PyImGui.text(f"({SCRIPT_REVISION})")

    PyImGui.end()
