"""
flat_button_click_test.py — Path B: Flat Engine Button Interactive Debug Panel
================================================================================

PyImGui widget panel that validates the button-rendering-pipeline consensus
implementation. Provides step-by-step creation, live status polling, and
individual debug probes — all non-blocking, frame-cycle driven.

Architecture:
    - Called every frame via main() by the widget manager.
    - State stored in module-level variables (no globals leak).
    - Native calls use NativeFunction.__call__ (→ Game.enqueue internally).
      NO user-written lambdas wrapping directCall().
    - Status auto-polled once per second using time.time() gating.
    - NO while loops, NO time.sleep() — the Python thread NEVER blocks.

Features:
    1. Live Status — window/button frame IDs, dimensions, position, pushed state.
    2. Step-by-step creation — 8 incremental buttons (Window → Subclass → Button → Size → Text → Input → Show → Invalidate).
    3. Debug probes — Read Base Ptr, Read Size, Read Position, Check Pushed, Force Redraw, Do Click.
    4. Scrollable debug log — timestamped events.
    5. Create/Destroy all in one click.
    6. Auto-poll — button state polled once per second.

Imports from ButtonMethods:
    FrameCreate_Func, CtlBtnSetTextLiteral_Func, FrameSetSize_Func,
    FrameSetPosition_Func, FrameMouseEnable_Func, CtlBtnProc_Callback,
    ButtonMethods (for helper wrappers), DIALOG_SUBCLASS_TYPE_ADDR

EXE Build: 06-14-2026
"""

import ctypes
import time
from typing import Any, Optional

import Py4GW
import PyImGui
import PyUIManager

from Py4GWCoreLib.GWUI import GWUI
from Py4GWCoreLib.UIManager import UIManager as UIMgr
from Py4GWCoreLib.native_src.methods.ButtonMethods import (
    ButtonMethods,
    DIALOG_SUBCLASS_TYPE_ADDR,
    FrameCreate_Func,
    CtlBtnSetTextLiteral_Func,
    FrameSetSize_Func,
    FrameSetPosition_Func,
    FrameMouseEnable_Func,
    CtlBtnProc_Callback,
)

# ── Metadata ──────────────────────────────────────────────────────────
MODULE_NAME = "Flat Button Click Test"
SCRIPT_REVISION = "2026-06-20-widget-rewrite"

# ── Debug: Dump all resolved addresses at startup ─────────────────────
def _dump_native_addresses():
    _log("=== RESOLVED NATIVE FUNCTION ADDRESSES ===")
    for name, obj in [
        ("FrameCreate_Func", FrameCreate_Func),
        ("CtlBtnSetTextLiteral_Func", CtlBtnSetTextLiteral_Func),
        ("FrameSetSize_Func", FrameSetSize_Func),
        ("FrameSetPosition_Func", FrameSetPosition_Func),
        ("FrameMouseEnable_Func", FrameMouseEnable_Func),
        ("CtlBtnProc_Callback", CtlBtnProc_Callback),
    ]:
        addr = getattr(obj, 'func_ptr', None) or getattr(obj, 'address', None) or '?'
        valid = getattr(obj, 'is_valid', lambda: False)()
        _log(f"  {name}: addr=0x{addr:08X}" if isinstance(addr, int) else f"  {name}: addr={addr}")
        _log(f"    valid={valid}")
    
    _log("=== UIMANAGER BINDINGS ===")
    for m in ["create_scrollable_content_by_frame_id",
              "add_text_item_to_frame_list_by_frame_id",
              "create_text_label_frame_by_frame_id",
              "create_ctl_button_frame_by_frame_id",
              "send_ui_message",
              "is_button_pushed_by_frame_id",
              "get_child_frame_ids"]:
        exists = hasattr(PyUIManager.UIManager, m)
        _log(f"  {m}: {'PRESENT' if exists else 'MISSING'}")
    _log("============================================")

# ── Tunables ──────────────────────────────────────────────────────────
WINDOW_TITLE = "Flat Button Test"
WINDOW_WIDTH = 280.0
WINDOW_HEIGHT = 160.0
WINDOW_X = 200.0
WINDOW_Y = 200.0

BUTTON_LABEL = "Click Me!"
BUTTON_WIDTH = 140.0
BUTTON_HEIGHT = 32.0
BUTTON_X = 10.0
BUTTON_Y = 40.0
BUTTON_FLAGS = 0x40000          # IME-style: flat background

POLL_INTERVAL = 1.0             # seconds between auto-polls
MAX_LOG_LINES = 500

# ── State ─────────────────────────────────────────────────────────────
_window_id: int = 0
_button_id: int = 0
_window_created: bool = False
_button_created: bool = False
_subclass_applied: bool = False

_button_dimensions: str = "?"
_button_position: str = "?"
_button_base_ptr: str = "?"
_button_pushed: bool = False
_button_pushed_str: str = "?"
_button_visible: bool = False
_button_frame_created: bool = False

_debug_log: list[str] = []
_last_status: str = "idle"
_last_poll_time: float = 0.0
_initialized: bool = False

# Input buffers (mutated by ImGui)
_input_width: float = BUTTON_WIDTH
_input_height: float = BUTTON_HEIGHT
_input_text: str = BUTTON_LABEL
_input_x: float = BUTTON_X
_input_y: float = BUTTON_Y


# ═══════════════════════════════════════════════════════════════════════
# Logging
# ═══════════════════════════════════════════════════════════════════════

def _log(msg: str) -> None:
    timestamp = time.strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    _debug_log.append(entry)
    if len(_debug_log) > MAX_LOG_LINES:
        _debug_log[:] = _debug_log[-MAX_LOG_LINES:]
    print(f"[{MODULE_NAME}] {msg}")


# ═══════════════════════════════════════════════════════════════════════
# Frame Inspection Helpers
# ═══════════════════════════════════════════════════════════════════════

def _find_child_button(parent_id: int) -> int:
    """Scan all frames to find a child of parent_id that could be the button."""
    if parent_id <= 0:
        return 0
    try:
        for candidate in UIMgr.GetFrameArray():
            try:
                fr = PyUIManager.UIFrame(candidate)
                if int(fr.parent_id) == parent_id:
                    return int(candidate)
            except Exception:
                continue
    except Exception:
        pass
    return 0


def _read_button_state() -> None:
    """Called on game thread to poll button status."""
    global _button_id, _button_frame_created, _button_visible
    global _button_dimensions, _button_position, _button_base_ptr
    global _button_pushed, _button_pushed_str

    if _button_id <= 0:
        return

    try:
        fr = PyUIManager.UIFrame(_button_id)
        _button_frame_created = bool(fr.is_created)
        _button_visible = bool(fr.is_visible)
    except Exception:
        _button_frame_created = False
        _button_visible = False

    try:
        left, top, right, bottom = UIMgr.GetFrameCoords(_button_id)
        w = right - left
        h = bottom - top
        _button_dimensions = f"{w:.0f}x{h:.0f}"
        _button_position = f"({left:.0f}, {top:.0f})"
    except Exception:
        _button_dimensions = "error"
        _button_position = "error"

    try:
        base = PyUIManager.UIManager.get_frame_base_address(_button_id)
        _button_base_ptr = f"0x{base:08X}" if base else "NULL"
    except Exception:
        _button_base_ptr = "error"

    try:
        _button_pushed = bool(
            PyUIManager.UIManager.is_button_pushed_by_frame_id(_button_id)
        )
        _button_pushed_str = "YES (pushed)" if _button_pushed else "no"
    except Exception:
        _button_pushed_str = "error"


# ═══════════════════════════════════════════════════════════════════════
# Actions (all enqueued on game thread)
# ═══════════════════════════════════════════════════════════════════════

def _enqueue(fn):
    """Helper: enqueue a callable onto the game thread."""
    Py4GW.Game.enqueue(fn)


# ── Step 1: Create Window ─────────────────────────────────────────────

def action_create_window():
    global _window_id, _window_created, _last_status, _subclass_applied

    if _window_id > 0:
        _log("Window already exists — skipping creation.")
        return

    _log(f"Creating window: '{WINDOW_TITLE}' ({WINDOW_WIDTH}x{WINDOW_HEIGHT})")

    def _impl():
        global _window_id, _window_created, _last_status
        _window_id = int(
            GWUI.CreateWindow(WINDOW_X, WINDOW_Y, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
            or 0
        )
        if _window_id:
            _window_created = True
            _last_status = f"window created: id={_window_id}"
            _log(_last_status)
        else:
            _last_status = "ERROR: CreateWindow returned 0"
            _log(_last_status)

    _enqueue(_impl)
    _last_status = "create_window enqueued"


# ── Step 2: Add OnFrameNotify (FrameNewSubclass) ──────────────────────
# ⚠️ SKIP THIS STEP! GWUI.CreateWindow ALREADY attaches CRProc.
# Calling FrameNewSubclass again DOUBLE-SUBCLASSES → CRASH.
# Only use if creating a BARE frame (without GWUI.CreateWindow).

def action_add_subclass():
    global _subclass_applied, _last_status

    if _subclass_applied:
        _log("OnFrameNotify already applied — skipping.")
        return
    if _window_id <= 0:
        _log("ERROR: No window — create window first.")
        return

    _log(f"⚠️ SKIP: GWUI.CreateWindow already has CRProc subclass (0x{DIALOG_SUBCLASS_TYPE_ADDR:08X})")
    _log("   Double-subclassing would CRASH. Use only with bare frames.")
    _last_status = "SKIPPED: already subclassed by GWUI.CreateWindow"


# ── Step 3: Create FrameList + Text Item ──────────────────────────────
# Uses REAL DLL bindings (verified exist):
#   - create_scrollable_frame_by_frame_id (not create_scrollable_content!)
#   - add_scrollable_item_by_frame_id (not add_text_item_to_frame_list!)
# The window-contents project used non-existent function names in GWUI.py.

_framelist_id: int = 0

def action_create_button():
    global _button_id, _button_created, _framelist_id, _last_status

    if _button_created:
        _log("Button already created — skipping. Destroy first to re-create.")
        return
    if _window_id <= 0:
        _log("ERROR: No window — create window first.")
        return

    _log(f"Creating scrollable frame + item: '{_input_text}'")

    def _impl():
        global _button_id, _button_created, _framelist_id, _last_status
        try:
            # Step 3a: Create scrollable frame as child of window
            _log(f"  Calling create_scrollable_frame_by_frame_id(parent={_window_id}, child=0, flags=0x20000)")
            _framelist_id = PyUIManager.UIManager.create_scrollable_frame_by_frame_id(
                _window_id,
                0,          # child_index
                0x20000,    # scrollable flag
            )
            _log(f"  create_scrollable_frame returned: {_framelist_id}")
            if not _framelist_id:
                _last_status = "ERROR: create_scrollable_frame returned 0"
                _log(_last_status)
                return

            # Step 3b: Add text item to the scrollable frame
            _log(f"  Calling add_scrollable_item_by_frame_id(framelist={_framelist_id}, text='{_input_text}')")
            _button_id = PyUIManager.UIManager.add_scrollable_item_by_frame_id(
                _framelist_id,
                _input_text,
                0,          # insert index
                0,          # item flags
            )
            _log(f"  add_scrollable_item returned: {_button_id}")
            if _button_id:
                _button_created = True
                _last_status = f"FrameList={_framelist_id} Item={_button_id}"
                _log(_last_status)
            else:
                _last_status = "ERROR: add_scrollable_item returned 0"
                _log(_last_status)
        except Exception as e:
            _last_status = f"EXCEPTION: {e}"
            _log(_last_status)
            import traceback
            _log(traceback.format_exc())

    _enqueue(_impl)
    _last_status = "create_scrollable+item enqueued"


# ── Step 4: Set Size ──────────────────────────────────────────────────

def action_set_size():
    if _button_id <= 0:
        _log("ERROR: No button — create button first.")
        return

    _log(f"SetSize: {_input_width}x{_input_height} on button {_button_id}")

    def _impl():
        global _last_status
        ButtonMethods.frame_set_size(_button_id, _input_width, _input_height)
        _last_status = f"SetSize({_input_width}x{_input_height}) enqueued"
        _log(_last_status)

    _enqueue(_impl)
    _last_status = "set_size enqueued"


# ── Step 5: Set Text ──────────────────────────────────────────────────

def action_set_text():
    global _last_status

    if _button_id <= 0:
        _log("ERROR: No button — create button first.")
        return
    if not CtlBtnSetTextLiteral_Func.is_valid():
        _log("ERROR: CtlBtnSetTextLiteral_Func not resolved")
        return

    _log(f"SetText: '{_input_text}' on button {_button_id}")

    label_buf = ctypes.create_unicode_buffer(_input_text)
    # NativeFunction.__call__ → Game.enqueue internally (no directCall, no lambda)
    CtlBtnSetTextLiteral_Func(
        ctypes.c_uint32(_button_id),
        label_buf,
    )
    _last_status = f"SetText('{_input_text}') enqueued"
    _log(_last_status)

    # Send msg 0x5F to trigger Sub-1 paint (renders text on button)
    # CtlBtnSetTextLiteral stores via msg 0x5E but doesn't render;
    # msg 0x5F is the text paint trigger in Ui_CompositeAuxButtonProc.
    try:
        PyUIManager.UIManager.send_ui_message(
            _button_id,
            0x5F,    # Sub-1 paint: state images + text
            0,       # param2
            0,       # param3
        )
        _log(f"msg 0x5F (paint text) sent to button {_button_id}")
    except Exception as e:
        _log(f"msg 0x5F failed: {e}")

    # Invalidate to trigger redraw (also via __call__)
    if _frame_content_invalidate_func and _frame_content_invalidate_func.is_valid():
        _frame_content_invalidate_func(
            ctypes.c_uint32(_button_id),
            ctypes.c_uint32(4),
        )
        _log(f"FrameContentInvalidate({_button_id}) enqueued after SetText")


# ── Step 6: Enable Input ──────────────────────────────────────────────

def action_enable_input():
    if _button_id <= 0:
        _log("ERROR: No button — create button first.")
        return

    _log(f"FrameMouseEnable(button={_button_id}, enable=True)")

    def _impl():
        global _last_status
        ButtonMethods.frame_mouse_enable(_button_id, True)
        _last_status = f"MouseEnable on button {_button_id}"
        _log(_last_status)

    _enqueue(_impl)
    _last_status = "enable_input enqueued"


# ── Step 7: Show ──────────────────────────────────────────────────────

def action_show():
    if _button_id <= 0:
        _log("ERROR: No button — create button first.")
        return

    _log(f"ShowFrame(button={_button_id})")

    def _impl():
        global _last_status
        UIMgr.ShowFrame(_button_id, True)
        _last_status = f"ShowFrame on button {_button_id}"
        _log(_last_status)

    _enqueue(_impl)
    _last_status = "show enqueued"


# ── Step 8: Force Redraw (FrameContentInvalidate) ─────────────────────

def action_invalidate():
    global _last_status

    if _button_id <= 0:
        _log("ERROR: No button — create button first.")
        return

    _log(f"FrameContentInvalidate(button={_button_id})")

    f = _resolve_frame_content_invalidate()
    if not f or not f.is_valid():
        _last_status = "ERROR: FrameContentInvalidate not resolved"
        _log(_last_status)
        return

    # NativeFunction.__call__ → Game.enqueue internally (no directCall, no lambda)
    f(
        ctypes.c_uint32(_button_id),
        ctypes.c_uint32(4),
    )
    _last_status = f"FrameContentInvalidate({_button_id}) enqueued"
    _log(_last_status)


# ── Debug Probes ──────────────────────────────────────────────────────

def probe_read_base_ptr():
    if _button_id <= 0:
        _log("No button to probe.")
        return
    _enqueue(_read_button_state)
    _log(f"Base ptr probe enqueued for button {_button_id}")


def probe_read_size():
    if _button_id <= 0:
        _log("No button to probe.")
        return
    _enqueue(_read_button_state)
    _log(f"Size probe enqueued for button {_button_id}")


def probe_read_position():
    if _button_id <= 0:
        _log("No button to probe.")
        return
    _enqueue(_read_button_state)
    _log(f"Position probe enqueued for button {_button_id}")


def probe_check_pushed():
    if _button_id <= 0:
        _log("No button to probe.")
        return
    _enqueue(_read_button_state)
    _log(f"Pushed probe enqueued for button {_button_id}")


# ── FrameContentInvalidate resolution (cached) ──────────────────────────

_frame_content_invalidate_addr: int = 0
_frame_content_invalidate_func: Any = None


def _resolve_frame_content_invalidate() -> Any:
    """Resolve FrameContentInvalidate address once, build NativeFunction for __call__ usage."""
    global _frame_content_invalidate_addr, _frame_content_invalidate_func
    if _frame_content_invalidate_func is not None:
        return _frame_content_invalidate_func

    from Py4GWCoreLib.Scanner import Scanner, ScannerSection
    from Py4GWCoreLib.native_src.internals.native_function import NativeFunction
    from Py4GWCoreLib.native_src.internals.prototypes import Prototypes

    # Pattern: lea ecx, [eax+4]; push ebx; push 4  (from EXE 0x0060d090, 06-14 build)
    addr = Scanner.Find(
        b"\x8D\x48\x04\x53\x6A\x04",
        "xxxxxx",
        0, ScannerSection.TEXT,
    )
    if addr:
        fn = Scanner.ToFunctionStart(addr, 0x100)
        if fn:
            _frame_content_invalidate_addr = fn
            _frame_content_invalidate_func = NativeFunction.from_address(
                "FrameContentInvalidate",
                fn,
                Prototypes["Void_U32_U32"],
            )
            _log(f"FrameContentInvalidate resolved @ 0x{fn:08X}")
            return _frame_content_invalidate_func

    _log("WARNING: FrameContentInvalidate pattern not found")
    return None


# Eager-resolve at import time
_resolve_frame_content_invalidate()


def probe_force_redraw():
    global _last_status

    if _button_id <= 0:
        _log("No button to force redraw.")
        return

    _log(f"Force redraw: FrameContentInvalidate(button={_button_id})")

    f = _resolve_frame_content_invalidate()
    if not f or not f.is_valid():
        _log("ERROR: FrameContentInvalidate not resolved")
        return

    # NativeFunction.__call__ → Game.enqueue internally (no directCall, no lambda)
    f(
        ctypes.c_uint32(_button_id),
        ctypes.c_uint32(4),
    )
    _last_status = f"FrameContentInvalidate({_button_id}, 4) enqueued"
    _log(_last_status)


def probe_do_click():
    if _button_id <= 0:
        _log("No button to click.")
        return

    _log(f"Do Click: programmatic click on button {_button_id}")

    def _impl():
        global _last_status
        PyUIManager.UIManager.button_click(_button_id)
        _last_status = f"button_click({_button_id}) called"
        _log(_last_status)

    _enqueue(_impl)
    _last_status = "do_click enqueued"


# ── Create / Destroy All ──────────────────────────────────────────────

def action_create_all():
    """Convenience: create window + subclass + button in one go."""
    _log("=== Create All ===")
    action_create_window()
    # Enqueue subclass after window creation delay
    def _delayed_subclass():
        global _window_id, _subclass_applied
        if _window_id > 0 and not _subclass_applied:
            ButtonMethods.frame_new_subclass(_window_id, DIALOG_SUBCLASS_TYPE_ADDR, 0)
            _subclass_applied = True
            _log(f"Delayed OnFrameNotify applied to window {_window_id}")

    # The subclass must run after window creation; we enqueue it after a small delay
    # by chaining through Game.enqueue.  The widget's auto-poll will discover the
    # button a few frames later.
    def _delayed_subclass_and_button():
        _delayed_subclass()
    _enqueue(_delayed_subclass_and_button)

    # Create button on next tick
    def _delayed_button():
        global _button_id, _button_created, _window_id
        if _window_id > 0:
            ButtonMethods.create_flat_button_with_click(
                parent_frame_id=_window_id,
                component_flags=BUTTON_FLAGS,
                child_index=0,
                label_text=_input_text,
                width=_input_width,
                height=_input_height,
                pos_x=_input_x,
                pos_y=_input_y,
                enable_click=False,
            )
            _button_created = True
            _log("Delayed button creation called")
    _enqueue(_delayed_button)


def action_destroy_all():
    global _window_id, _button_id, _window_created, _button_created
    global _subclass_applied, _button_frame_created, _button_visible
    global _button_dimensions, _button_position, _button_base_ptr
    global _button_pushed, _button_pushed_str

    _log("=== Destroy All ===")

    def _impl():
        global _window_id, _button_id, _window_created, _button_created
        global _subclass_applied, _button_frame_created, _button_visible
        global _button_dimensions, _button_position, _button_base_ptr
        global _button_pushed, _button_pushed_str
        try:
            if _button_id > 0:
                PyUIManager.UIManager.destroy_ui_component_by_frame_id(_button_id)
                _log(f"Button {_button_id} destroyed")
            if _window_id > 0:
                PyUIManager.UIManager.destroy_ui_component_by_frame_id(_window_id)
                _log(f"Window {_window_id} destroyed")
        except Exception as exc:
            _log(f"Destroy error: {exc}")
        _window_id = 0
        _button_id = 0
        _window_created = False
        _button_created = False
        _subclass_applied = False
        _button_frame_created = False
        _button_visible = False
        _button_dimensions = "?"
        _button_position = "?"
        _button_base_ptr = "?"
        _button_pushed = False
        _button_pushed_str = "?"
        _last_status = "all destroyed"

    _enqueue(_impl)
    _last_status = "destroy_all enqueued"


# ═══════════════════════════════════════════════════════════════════════
# Auto-Poll (called once per second, non-blocking)
# ═══════════════════════════════════════════════════════════════════════

def _auto_poll() -> None:
    """Discover button and read state — called from render each frame when gated."""
    global _button_id, _button_created, _last_poll_time

    # Discover button if window exists but button not found
    if _window_id > 0 and not _button_created:
        child = _find_child_button(_window_id)
        if child > 0:
            _button_id = child
            _button_created = True
            _log(f"Auto-discovered button: id={_button_id}")

            # Invalidate to trigger redraw (after FrameCreate, per user request)
            f = _resolve_frame_content_invalidate()
            if f and f.is_valid():
                f(
                    ctypes.c_uint32(_button_id),
                    ctypes.c_uint32(4),
                )
                _log(f"FrameContentInvalidate({_button_id}) enqueued after discovery")

    # Read button state
    if _button_id > 0:
        _enqueue(_read_button_state)


# ═══════════════════════════════════════════════════════════════════════
# PyImGui Panel
# ═══════════════════════════════════════════════════════════════════════

def main() -> None:
    """Called each frame by the Py4GW widget manager."""
    global _initialized, _last_poll_time
    global _input_width, _input_height, _input_text, _input_x, _input_y

    if not _initialized:
        _log(f"=== {MODULE_NAME} v{SCRIPT_REVISION} ===")
        _log(f"DIALOG_SUBCLASS_TYPE_ADDR = 0x{DIALOG_SUBCLASS_TYPE_ADDR:08X}")
        _dump_native_addresses()
        _initialized = True

    # ── Auto-poll once per second ──
    now = time.time()
    if now - _last_poll_time >= POLL_INTERVAL:
        _last_poll_time = now
        _auto_poll()

    # ── Draw ImGui window ──
    if not PyImGui.begin(f"{MODULE_NAME}##flat_btn_test", True, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    # ═══════════════════════════════════════════════════════════════════
    # Section: Status
    # ═══════════════════════════════════════════════════════════════════
    PyImGui.text_colored("=== Status ===", (0.4, 0.8, 1.0, 1.0))
    PyImGui.text(f"  Window frame_id:  {_window_id}")
    PyImGui.text(f"  Button frame_id:  {_button_id}")
    PyImGui.text(f"  Button found:     {_button_created}")
    PyImGui.text(f"  Button visible:   {_button_visible}")
    PyImGui.text(f"  Button created:   {_button_frame_created}")
    PyImGui.text(f"  OnFrameNotify:    {_subclass_applied}")
    PyImGui.text(f"  Dimensions:       {_button_dimensions}")
    PyImGui.text(f"  Position:         {_button_position}")
    PyImGui.text(f"  Base ptr:         {_button_base_ptr}")

    pushed_color = (0.2, 1.0, 0.2, 1.0) if _button_pushed else (1.0, 0.5, 0.3, 1.0)
    PyImGui.text_colored(f"  Button pushed:    {_button_pushed_str}", pushed_color)

    status_color = (1.0, 0.5, 0.3, 1.0) if "ERROR" in _last_status else (0.5, 0.5, 0.5, 1.0)
    PyImGui.text_colored(f"  Last status:      {_last_status}", status_color)

    PyImGui.separator()

    # ═══════════════════════════════════════════════════════════════════
    # Section: Quick Actions
    # ═══════════════════════════════════════════════════════════════════
    PyImGui.text_colored("=== Quick Actions ===", (0.4, 0.8, 1.0, 1.0))

    if PyImGui.button("Create All (Auto)"):
        action_create_all()
    PyImGui.same_line(0,-1)
    if PyImGui.button("Destroy All"):
        action_destroy_all()

    PyImGui.separator()

    # ═══════════════════════════════════════════════════════════════════
    # Section: Step-by-Step Creation
    # ═══════════════════════════════════════════════════════════════════
    PyImGui.text_colored("=== Step-by-Step Creation ===", (0.4, 0.8, 1.0, 1.0))

    if PyImGui.button("Step 1: Create Window"):
        action_create_window()
    PyImGui.same_line(0,-1)
    PyImGui.text("Creates CContainerFrame via GWUI.CreateWindow")

    if PyImGui.button("Step 2: Add OnFrameNotify"):
        action_add_subclass()
    PyImGui.same_line(0,-1)
    PyImGui.text(f"FrameNewSubclass(0x{DIALOG_SUBCLASS_TYPE_ADDR:08X})")

    if PyImGui.button("Step 3: Create FrameList+Item"):
        action_create_button()
    PyImGui.same_line(0,-1)
    PyImGui.text("FrameCreate + CtlBtnProc callback")

    if PyImGui.button("Step 4: Set Size"):
        action_set_size()
    PyImGui.same_line(0,-1)
    PyImGui.text(f"FrameSetSize({_input_width:.0f}, {_input_height:.0f})")

    if PyImGui.button("Step 5: Set Text"):
        action_set_text()
    PyImGui.same_line(0,-1)
    PyImGui.text(f"CtlBtnSetTextLiteral('{_input_text}')")

    if PyImGui.button("Step 6: Enable Input"):
        action_enable_input()
    PyImGui.same_line(0,-1)
    PyImGui.text("FrameMouseEnable(button, True)")

    if PyImGui.button("Step 7: Show"):
        action_show()
    PyImGui.same_line(0,-1)
    PyImGui.text("FrameShow(button)")

    if PyImGui.button("Step 8: Invalidate"):
        action_invalidate()
    PyImGui.same_line(0,-1)
    PyImGui.text("FrameContentInvalidate(button)  <-- call AFTER SetText!")

    PyImGui.separator()

    # ═══════════════════════════════════════════════════════════════════
    # Section: Tunable Parameters
    # ═══════════════════════════════════════════════════════════════════
    PyImGui.text_colored("=== Parameters ===", (0.4, 0.8, 1.0, 1.0))

    _input_text = PyImGui.input_text("Button Label", _input_text, 0) or _input_text
    _input_width = PyImGui.input_float("Width", _input_width)
    _input_height = PyImGui.input_float("Height", _input_height)
    _input_x = PyImGui.input_float("Pos X", _input_x)
    _input_y = PyImGui.input_float("Pos Y", _input_y)

    PyImGui.separator()

    # ═══════════════════════════════════════════════════════════════════
    # Section: Debug Probes
    # ═══════════════════════════════════════════════════════════════════
    PyImGui.text_colored("=== Debug Probes ===", (0.7, 0.7, 0.3, 1.0))

    if PyImGui.button("Read Base Ptr"):
        probe_read_base_ptr()
    PyImGui.same_line(0,-1)
    if PyImGui.button("Read Size"):
        probe_read_size()
    PyImGui.same_line(0,-1)
    if PyImGui.button("Read Position"):
        probe_read_position()

    if PyImGui.button("Check Pushed"):
        probe_check_pushed()
    PyImGui.same_line(0,-1)
    if PyImGui.button("Force Redraw"):
        probe_force_redraw()
    PyImGui.same_line(0,-1)
    if PyImGui.button("Do Click"):
        probe_do_click()

    PyImGui.separator()

    # ═══════════════════════════════════════════════════════════════════
    # Section: Debug Log
    # ═══════════════════════════════════════════════════════════════════
    PyImGui.text_colored("=== Debug Log ===", (0.7, 0.7, 0.3, 1.0))
    PyImGui.text(f"  ({len(_debug_log)} entries, show last 20)")

    if PyImGui.button("Clear Log"):
        _debug_log.clear()

    # Scrollable log area
    child_height = 200.0
    if PyImGui.begin_child("##debug_log_area", (0.0, child_height), True):
        for line in _debug_log[-20:]:
            PyImGui.text(line)
        PyImGui.end_child()

    PyImGui.separator()

    PyImGui.text_colored(f"{MODULE_NAME} v{SCRIPT_REVISION}", (0.4, 0.4, 0.4, 1.0))
    PyImGui.text("Poll interval: 1s  |  All actions via Game.enqueue()")

    PyImGui.end()


# ═══════════════════════════════════════════════════════════════════════
# Widget lifecycle
# ═══════════════════════════════════════════════════════════════════════

def configure() -> None:
    """Widget config entry point — no-op for this debug panel."""
    pass


if __name__ == "__main__":
    main()
