"""
Window Contents Pipeline Test (2026-06-04)

Verifies the CContainerFrame -> FrameList -> TextLabels pipeline:
  1. Create a titled container window
  2. Create a scrollable frame list as child 0
  3. Add text label items via C++ bindings
  4. Verify items stack vertically without overlap

All address resolution is handled in C++ (py_ui.h / py_ui.cpp).
This test uses only the C++-bound Python API.
"""

import time

import Py4GW
import PyImGui
import PyUIManager

from Py4GWCoreLib import UIManager


MODULE_NAME = "Window Contents Test"
SCRIPT_REVISION = "2026-06-04-window-contents-2"
WINDOW_OPEN = True
INITIALIZED = False

# Window configuration
TARGET_X = 100.0
TARGET_Y = 100.0
TARGET_WIDTH = 280.0
TARGET_HEIGHT = 220.0

# Test items
DEFAULT_ITEMS = [
    "Item 1: Hello, Guild Wars!",
    "Item 2: This is a scrollable window.",
    "Item 3: Each item auto-stacks.",
    "Item 4: No overlap!",
    "Item 5: The frame list handles layout.",
    "Item 6: Long item to test wrapping: Lorem ipsum dolor sit amet.",
    "Item 7: Native CtlFrameListCreateItem via msg 0x57.",
    "Item 8: CContainerFrame root with CRProc chrome.",
]

# State
g_window_id: int = 0
g_frame_list_id: int = 0
g_item_ids: list[int] = []
g_last_status: str = "idle"


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _inspect_frame(frame_id: int) -> str:
    """Return a diagnostic string for a frame."""
    if frame_id <= 0:
        return "frame_id=0"
    try:
        frame = UIManager.GetFrameByID(frame_id)
        left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
        return (
            f"id={frame_id} parent={int(frame.parent_id)} "
            f"created={bool(frame.is_created)} visible={bool(frame.is_visible)} "
            f"state=0x{int(frame.frame_state):X} "
            f"rect=({left:.0f},{top:.0f})-({right:.0f},{bottom:.0f})"
        )
    except Exception as exc:
        return f"id={frame_id} error={exc}"


def _dump_state() -> str:
    """Return a multi-line state report."""
    lines = []
    lines.append(f"window: {_inspect_frame(g_window_id)}")
    lines.append(f"frame_list: {_inspect_frame(g_frame_list_id)}")
    lines.append(f"item_count: {len(g_item_ids)}")
    for i, item_id in enumerate(g_item_ids):
        lines.append(f"  item[{i}]: {_inspect_frame(item_id)}")
    return "\n".join(lines)


def _create_window_only() -> None:
    """Create just the window (no content)."""
    global g_window_id, g_frame_list_id, g_item_ids, g_last_status

    def _invoke():
        global g_window_id, g_frame_list_id, g_item_ids, g_last_status
        g_window_id = int(
            PyUIManager.UIManager.CreateNativeWindow(
                TARGET_X, TARGET_Y, TARGET_WIDTH, TARGET_HEIGHT, "Empty Window"
            )
            or 0
        )
        g_frame_list_id = 0
        g_item_ids = []
        g_last_status = f"window={g_window_id}"
        _log(g_last_status)

    Py4GW.Game.enqueue(_invoke)
    g_last_status = "create window enqueued"


def _create_scrollable_content() -> None:
    """Add scrollable frame list to the existing window."""
    global g_frame_list_id, g_last_status

    def _invoke():
        global g_frame_list_id, g_last_status
        if not g_window_id:
            g_last_status = "no window"
            return
        g_frame_list_id = int(
            PyUIManager.UIManager.create_scrollable_content_by_frame_id(
                g_window_id, 0, 0, ""
            )
            or 0
        )
        g_last_status = f"framelist={g_frame_list_id}"
        _log(g_last_status)

    Py4GW.Game.enqueue(_invoke)
    g_last_status = "create scrollable enqueued"


def _add_text_item(text: str) -> None:
    """Add one text item to the frame list."""
    global g_item_ids, g_last_status

    def _invoke():
        global g_item_ids, g_last_status
        if not g_frame_list_id:
            g_last_status = "no frame list"
            return
        item_id = int(
            PyUIManager.UIManager.add_text_item_to_frame_list_by_frame_id(
                g_frame_list_id, str(text), 0, 0
            )
            or 0
        )
        if item_id:
            g_item_ids.append(item_id)
        g_last_status = f"added item={item_id}, total={len(g_item_ids)}"
        _log(g_last_status)

    Py4GW.Game.enqueue(_invoke)
    g_last_status = "add item enqueued"


def _create_scrollable_window(items: list[str]) -> None:
    """One-step: window + scrollable + items via C++ binding."""
    global g_window_id, g_frame_list_id, g_item_ids, g_last_status

    def _invoke():
        global g_window_id, g_frame_list_id, g_item_ids, g_last_status
        g_window_id = int(
            PyUIManager.UIManager.create_scrollable_text_window(
                TARGET_X, TARGET_Y, TARGET_WIDTH, TARGET_HEIGHT,
                "Py4GW Scroll Test", list(items),
            )
            or 0
        )
        g_frame_list_id = 0
        g_item_ids = []
        g_last_status = f"one-step window={g_window_id}"
        _log(g_last_status)

    Py4GW.Game.enqueue(_invoke)
    g_last_status = "one-step enqueued"


def _draw_window() -> None:
    global WINDOW_OPEN, g_window_id, g_frame_list_id, g_item_ids, g_last_status

    if not PyImGui.begin(f"{MODULE_NAME}##{SCRIPT_REVISION}", WINDOW_OPEN):
        PyImGui.end()
        return

    PyImGui.text(f"revision: {SCRIPT_REVISION}")
    PyImGui.separator()
    PyImGui.text("CContainerFrame -> FrameList (child 0, type 0xAEA) -> TextLabels")
    PyImGui.text("All address resolution: C++ layer (py_ui.h / py_ui.cpp)")
    PyImGui.separator()

    # Step-by-step: window -> scrollable -> add items one at a time
    PyImGui.text("Step-by-step:")
    if PyImGui.button("1. Create Window"):
        _create_window_only()
    PyImGui.same_line(0,-1)
    if PyImGui.button("2. Add Scrollable"):
        _create_scrollable_content()
    PyImGui.same_line(0,-1)
    if PyImGui.button("3. Add Text Item"):
        item_idx = len(g_item_ids)
        text = DEFAULT_ITEMS[item_idx] if item_idx < len(DEFAULT_ITEMS) else f"Item {item_idx + 1}"
        _add_text_item(text)

    PyImGui.separator()

    # One-step convenience
    PyImGui.text("One-step:")
    if PyImGui.button("Create Scrollable Window (8 items)"):
        _create_scrollable_window(DEFAULT_ITEMS)

    PyImGui.separator()
    PyImGui.text(f"last_status: {g_last_status}")
    PyImGui.text(f"window_id: {g_window_id}")
    PyImGui.text(f"frame_list_id: {g_frame_list_id}")
    PyImGui.text(f"items: {len(g_item_ids)} {g_item_ids[:5]}{'...' if len(g_item_ids) > 5 else ''}")

    if PyImGui.button("Dump State"):
        _log(_dump_state())

    PyImGui.separator()
    PyImGui.text("Known Limitations:")
    PyImGui.text("  - Scrollbars may not render (scrollbar chrome proc TBD)")
    PyImGui.text("  - C++ repo must be rebuilt after adding bindings")
    PyImGui.text("  - Return values are async (0 until game thread processes)")

    PyImGui.end()


def main() -> None:
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        _log(f"script revision={SCRIPT_REVISION}")
        _log("All address resolution in C++ — test uses C++ bindings only.")
    _draw_window()


if __name__ == "__main__":
    main()
