"""
Native Button Creation Test (2026-06-16)
=========================================
Creates a native GW window with a button using CtlTextBtnProc.
Tests:
  1. Window creation via GWUI.CreateWindow (high-level)
  2. Text button creation via create_text_button_frame_by_frame_id
  3. Caption auto-set during creation (msg 0x09 case 9 copies name_enc)
  4. Click detection via is_button_pushed_by_frame_id

CtlTextBtnProc = engine-level text button (EXE FUN_00616c00).
No IUi:: wrapper, no image list dependency, cold-creation safe.

REQUIRES rebuilt DLL for create_text_button_frame_by_frame_id binding.
All native calls go through Py4GW.Game.enqueue() — game thread safe.
"""
import Py4GW
import PyImGui
import PyUIManager

from Py4GWCoreLib.GWUI import GWUI

MODULE_NAME = "Button Test"
WINDOW_OPEN = True

# Window config
WIN_X, WIN_Y = 100.0, 100.0
WIN_W, WIN_H = 300.0, 180.0

# State
g_window_id: int = 0
g_button_id: int = 0
g_last_status: str = "idle"
g_pushed: bool = False
g_check_count: int = 0


def _log(msg: str) -> None:
    print(f"[{MODULE_NAME}] {msg}")


# ═══════════════════════════════════════════════════════════════════
# Actions (enqueued on game thread)
# ═══════════════════════════════════════════════════════════════════

def _create_window_and_button_impl():
    global g_window_id, g_button_id, g_last_status

    # 1. Create the native window
    g_window_id = GWUI.CreateWindow(WIN_X, WIN_Y, WIN_W, WIN_H, "Button Test")
    if not g_window_id:
        g_last_status = "FAIL: CreateWindow returned 0"
        _log(g_last_status)
        return
    _log(f"Window created: fid={g_window_id}")

    # 2. Create text button as child of the window (CtlTextBtnProc — engine-level)
    g_button_id = int(
        PyUIManager.UIManager.create_text_button_frame_by_frame_id(
            g_window_id,       # parent
            0x300,             # component_flags = F_VISIBLE | F_ENABLED
            0,                 # child_index
            "Click Me! \x0108\x0107Test\x0001",  # caption (auto-set during creation)
            "",                # component_label
        )
        or 0
    )
    if not g_button_id:
        g_last_status = "FAIL: create_text_button_frame returned 0"
        _log(g_last_status)
        return
    _log(f"Text button created: fid={g_button_id}")

    g_last_status = f"window={g_window_id} button={g_button_id}"
    _log(g_last_status)


def create_window_and_button():
    Py4GW.Game.enqueue(_create_window_and_button_impl)
    global g_last_status
    g_last_status = "create enqueued"


def _check_pushed_impl():
    global g_pushed, g_last_status, g_check_count
    if not g_button_id:
        g_last_status = "no button"
        return
    g_pushed = bool(
        PyUIManager.UIManager.is_button_pushed_by_frame_id(g_button_id)
    )
    g_check_count += 1
    g_last_status = f"pushed={g_pushed} (check #{g_check_count})"


def check_pushed():
    Py4GW.Game.enqueue(_check_pushed_impl)
    global g_last_status
    g_last_status = "check enqueued"


def _simulate_click_impl():
    global g_last_status
    if not g_button_id:
        g_last_status = "no button"
        return
    PyUIManager.UIManager.button_click(g_button_id)
    g_last_status = "click simulated"
    _log(g_last_status)


def simulate_click():
    Py4GW.Game.enqueue(_simulate_click_impl)
    global g_last_status
    g_last_status = "click enqueued"


def _update_caption_impl(text: str):
    global g_last_status
    if not g_button_id:
        g_last_status = "no button"
        return
    # CtlTextBtnProc uses msg 0x5F for SetText (not 0x5C which sets opacity)
    ok = PyUIManager.UIManager.SendFrameUIMessage(
        g_button_id, 0x5F, 0, str(text)
    )
    g_last_status = f"SetText(0x5F) '{text}' -> {ok}"
    _log(g_last_status)


def update_caption(text: str):
    Py4GW.Game.enqueue(lambda: _update_caption_impl(text))
    global g_last_status
    g_last_status = "caption enqueued"


def _cleanup_impl():
    global g_window_id, g_button_id, g_last_status
    if g_window_id:
        PyUIManager.UIManager.destroy_ui_component_by_frame_id(g_window_id)
        _log(f"Destroyed window fid={g_window_id}")
    g_window_id = 0
    g_button_id = 0
    g_last_status = "cleaned up"


def cleanup():
    Py4GW.Game.enqueue(_cleanup_impl)
    global g_last_status
    g_last_status = "cleanup enqueued"


# ═══════════════════════════════════════════════════════════════════
# PyImGui Panel
# ═══════════════════════════════════════════════════════════════════

g_caption_input: str = "Click Me!"


def main():
    global WINDOW_OPEN, g_caption_input, g_window_id, g_button_id
    global g_last_status, g_pushed, g_check_count

    if not PyImGui.begin(f"{MODULE_NAME}##button_test", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text("Native Button Creation Test")
    PyImGui.text("1. Create window + button")
    PyImGui.text("2. Click the button in the native window (or simulate)")
    PyImGui.text("3. Press 'Check Pushed' to poll state")
    PyImGui.separator()

    # Check if bindings exist
    try:
        _ = PyUIManager.UIManager.create_text_button_frame_by_frame_id
        PyImGui.text_colored("create_text_button_frame: OK", (0.3, 1.0, 0.3, 1.0))
    except AttributeError:
        PyImGui.text_colored("create_text_button_frame: NOT FOUND — rebuild C++ DLL", (1.0, 0.3, 0.3, 1.0))
        PyImGui.text("  cmake -B build -A Win32 && cmake --build build --config Release")

    PyImGui.separator()

    # Create button
    if PyImGui.button("Create Window + Button"):
        create_window_and_button()

    PyImGui.same_line(0, -1)

    if PyImGui.button("Clean Up"):
        cleanup()

    PyImGui.separator()

    # State display
    PyImGui.text(f"window_id: {g_window_id}")
    PyImGui.text(f"button_id: {g_button_id}")
    PyImGui.text(f"last_status: {g_last_status}")

    PyImGui.separator()

    # Caption
    g_caption_input = PyImGui.input_text("Caption", g_caption_input, 0) or g_caption_input
    if PyImGui.button("Set Caption"):
        update_caption(g_caption_input)

    PyImGui.separator()

    # Click detection
    if PyImGui.button("Check Pushed (poll msg 0x59)"):
        check_pushed()

    PyImGui.same_line(0, -1)

    pushed_color = (0.3, 1.0, 0.3, 1.0) if g_pushed else (1.0, 0.5, 0.3, 1.0)
    PyImGui.text_colored(f"PUSHED: {g_pushed}  (checks: {g_check_count})", pushed_color)

    # Click simulation
    if PyImGui.button("Simulate Click (button_click)"):
        simulate_click()

    PyImGui.separator()

    PyImGui.text("How to test:")
    PyImGui.text("  1. Click 'Create Window + Button'")
    PyImGui.text("  2. A native GW window appears with a button")
    PyImGui.text("  3. Click the button in the native window")
    PyImGui.text("  4. Press 'Check Pushed' to see if pushed state changes")
    PyImGui.text("  5. Or use 'Simulate Click' + immediately 'Check Pushed'")

    PyImGui.end()


if __name__ == "__main__":
    main()
