"""
text_button_render_test.py — stable clickable buttons + crash-free click recognition.

Uses ONLY the stable pieces:
  - window (CreateNativeWindow)                       [confirmed working]
  - PLAIN scrollable frame list (create_scrollable_content)  [confirmed working]
  - button items (add_button_item -> CtlTextBtnProc) [render as clickable hyperlinks]

Click recognition is done PURELY in Python (no native msg 0x67, no selectable list —
those crashed): each frame, on a left-click, hit-test the mouse position against each
button item's on-screen rect (UIManager.GetFrameCoords). This cannot crash the client.

The panel shows the mouse position and each item's rect so we can verify coordinate
alignment (game frame coords vs overlay mouse). No DLL rebuild needed.
"""

import time

import Py4GW
import PyImGui
import PyUIManager

from Py4GWCoreLib.GWUI import GWUI
from Py4GWCoreLib.UIManager import UIManager as UIMgr

MODULE_NAME = "Text Button Render Test"

_win = 0
_list = 0
_btn_a = 0
_btn_b = 0
_last_click_msg = "(click a button in the game window)"
_log: list[str] = []


def _log_msg(m: str) -> None:
    _log.append(f"[{time.strftime('%H:%M:%S')}] {m}")
    print(f"[{MODULE_NAME}] {m}")
    if len(_log) > 200:
        _log[:] = _log[-200:]


def _enq(fn) -> None:
    Py4GW.Game.enqueue(fn)


def _rect(fid: int):
    if fid <= 0:
        return None
    try:
        l, t, r, b = UIMgr.GetFrameCoords(fid)
        return (float(l), float(t), float(r), float(b))
    except Exception:
        return None


def step_window():
    def impl():
        global _win
        _win = int(GWUI.CreateWindow(320.0, 220.0, 320.0, 240.0, "Button Test") or 0)
        _log_msg(f"[1] window = {_win}")
    _enq(impl)


def step_list():
    def impl():
        global _list
        if not _win:
            _log_msg("no window - do step 1"); return
        # PLAIN scrollable list (the stable, confirmed-working path)
        _list = int(PyUIManager.UIManager.create_scrollable_content_by_frame_id(_win, 0, 0x20000) or 0)
        _log_msg(f"[2] frame list = {_list}")
    _enq(impl)


def step_buttons():
    def impl():
        global _btn_a, _btn_b
        if not _list:
            _log_msg("no list - do step 2"); return
        _btn_a = int(PyUIManager.UIManager.add_button_item_to_frame_list_by_frame_id(_list, "Button A", 0, 0) or 0)
        _btn_b = int(PyUIManager.UIManager.add_button_item_to_frame_list_by_frame_id(_list, "Button B", 1, 0) or 0)
        _log_msg(f"[3] button A = {_btn_a} rect={_rect(_btn_a)}")
        _log_msg(f"[3] button B = {_btn_b} rect={_rect(_btn_b)}")
    _enq(impl)


def _hit_test():
    """Crash-free recognition: on left-click, test mouse pos vs each item rect."""
    global _last_click_msg
    if not (_btn_a or _btn_b):
        return
    try:
        if not PyImGui.is_mouse_clicked(0):
            return
        io = PyImGui.get_io()
        mx, my = float(io.mouse_pos_x), float(io.mouse_pos_y)
        for fid, name in ((_btn_a, "A"), (_btn_b, "B")):
            r = _rect(fid)
            if r and r[0] <= mx <= r[2] and r[1] <= my <= r[3]:
                _last_click_msg = f"CLICK RECOGNIZED -> Button {name}  @ ({mx:.0f},{my:.0f})"
                _log_msg(_last_click_msg)
                return
    except Exception as e:
        _log_msg(f"hit-test err: {e}")


def step_destroy():
    def impl():
        global _win, _list, _btn_a, _btn_b
        for fid in (_btn_a, _btn_b, _list, _win):
            if fid > 0:
                try:
                    PyUIManager.UIManager.destroy_ui_component_by_frame_id(fid)
                except Exception as e:
                    _log_msg(f"destroy {fid} err: {e}")
        _win = _list = _btn_a = _btn_b = 0
        _log_msg("destroyed all")
    _enq(impl)


def main() -> None:
    _hit_test()  # runs every frame — pure Python, cannot crash the client

    if not PyImGui.begin(MODULE_NAME, True, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    PyImGui.text_colored("Run 1 -> 2 -> 3, then CLICK a button in the game window.", (0.4, 0.8, 1.0, 1.0))
    PyImGui.text(f"window={_win} list={_list} A={_btn_a} B={_btn_b}")
    PyImGui.text_colored(f"  {_last_click_msg}", (0.3, 1.0, 0.4, 1.0))
    try:
        io = PyImGui.get_io()
        PyImGui.text(f"  mouse=({io.mouse_pos_x:.0f},{io.mouse_pos_y:.0f})  A.rect={_rect(_btn_a)}  B.rect={_rect(_btn_b)}")
    except Exception:
        pass
    PyImGui.separator()
    if PyImGui.button("1) Create Window"):
        step_window()
    if PyImGui.button("2) Create Frame List (plain)"):
        step_list()
    if PyImGui.button("3) Add Button A + Button B"):
        step_buttons()
    PyImGui.separator()
    if PyImGui.button("Destroy All"):
        step_destroy()

    PyImGui.separator()
    PyImGui.text_colored("=== Log ===", (0.7, 0.7, 0.3, 1.0))
    if PyImGui.begin_child("##log", (0.0, 200.0), True):
        for line in _log[-20:]:
            PyImGui.text(line)
        PyImGui.end_child()
    PyImGui.end()


def configure() -> None:
    pass


if __name__ == "__main__":
    main()
