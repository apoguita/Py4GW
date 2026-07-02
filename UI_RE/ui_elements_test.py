"""
ui_elements_test.py — create each native UI element as a distinguishable row in a
SCROLLABLE FRAME LIST (the list stacks items so you can tell them apart).

NO REBUILD NEEDED for the list path — add_control_item_by_frame_id is already in the
loaded DLL (your button test used it). Each control is added on its own button so a
risky one is isolated. Verdict tags: [OK] confirmed, [~] likely, [?] uncertain,
[!] needs-workaround (may crash). Button-family items report clicks natively via
is_button_pushed_by_frame_id (msg 0x59).

NOTE on appearance:
 - The frame list stretches each item to the list width (rows) — that is the layout that
   keeps them distinguishable. Free-standing sizing is a separate problem (direct-child
   positioning didn't take; that needs another rebuild to fix).
 - flat_button (CtlBtnProc) is a SOLID-COLOR rectangle by design — no GW texture.
   For the real 9-slice GW button texture add styled_button, but OPEN A MERCHANT first
   (it needs s_btnCheckImageList, created when a store window opens).
"""

import time

import Py4GW
import PyImGui
import PyUIManager

from Py4GWCoreLib.GWUI import GWUI
from Py4GWCoreLib.UIManager import UIManager as UIMgr

MODULE_NAME = "UI Elements Test"

# (control, caption, item_flags, verdict-tag, is_button_family)
CONTROLS = [
    ("text_label",    "Text Label",    0,       "OK", False),
    ("text_button",   "Text Button",   0,       "OK", False),
    ("flat_button",   "Flat Button",   0x80000, "~",  True),
    ("checkbox",      "Checkbox",      0x10000, "~",  True),
    ("radio",         "Radio",         0x10000, "~",  True),
    ("slider",        "Slider",        0,       "~",  False),
    ("styled_button", "Py4GW", 0,       "!",  True),
    ("dropdown",      "Dropdown",      0,       "!",  False),
    ("edit",          "Edit Text",     0,       "?",  False),
    ("progress",      "Progress",      0,       "!",  False),
    ("tabs",          "Tabs",          0,       "!",  False),
    ("groupheader",   "Group Header",  0,       "!",  False),
]

_win = 0
_list = 0
_items: dict = {}
_pushed: dict = {}
_log: list[str] = []


def _log_msg(m: str) -> None:
    _log.append(f"[{time.strftime('%H:%M:%S')}] {m}")
    print(f"[{MODULE_NAME}] {m}")
    if len(_log) > 250:
        _log[:] = _log[-250:]


def _enq(fn) -> None:
    Py4GW.Game.enqueue(fn)


def _coords(fid: int) -> str:
    try:
        l, t, r, b = UIMgr.GetFrameCoords(fid)
        return f"({l:.0f},{t:.0f}) {r - l:.0f}x{b - t:.0f}"
    except Exception:
        return "?"


def step_window():
    def impl():
        global _win
        _win = int(GWUI.CreateWindow(300.0, 160.0, 320.0, 420.0, "UI Elements") or 0)
        _log_msg(f"window = {_win}")
    _enq(impl)


def step_list():
    def impl():
        global _list
        if not _win:
            _log_msg("no window - create window first"); return
        _list = int(PyUIManager.UIManager.create_scrollable_content_by_frame_id(_win, 0, 0x20000) or 0)
        _log_msg(f"scrollable frame list = {_list}")
        # Install the native no-stretch size handlers BEFORE adding items so controls keep
        # their own width instead of being stretched to the full list width.
        if _list:
            try:
                r = int(PyUIManager.UIManager.set_frame_list_no_stretch_by_frame_id(_list) or 0)
                _log_msg(f"no-stretch handlers installed: {'ok' if r else 'FAILED'}")
            except AttributeError:
                _log_msg("set_frame_list_no_stretch NOT in DLL — rebuild + copy the DLL first.")
    _enq(impl)


def add_control(control, caption, flags, is_btn, idx):
    def impl():
        if not _list:
            _log_msg("no list - create frame list first"); return
        try:
            fid = int(PyUIManager.UIManager.add_control_item_by_frame_id(_list, control, caption, idx, flags) or 0)
        except AttributeError:
            _log_msg("add_control_item NOT in DLL — rebuild + copy the DLL first."); return
        except Exception as e:
            _log_msg(f"{control}: EXCEPTION {e}"); return
        if fid:
            _items[control] = fid
            if is_btn:
                _pushed[fid] = False
            _log_msg(f"{control} -> id={fid}  {_coords(fid)}")
        else:
            _log_msg(f"{control} -> 0 (proc not resolved / not creatable)")
    _enq(impl)


def _poll_buttons():
    if not _pushed:
        return
    def impl():
        for fid in list(_pushed.keys()):
            try:
                p = bool(PyUIManager.UIManager.is_button_pushed_by_frame_id(fid))
            except Exception:
                continue
            if p != _pushed.get(fid):
                _pushed[fid] = p
                name = next((c for c, i in _items.items() if i == fid), str(fid))
                _log_msg(f"CLICK (native) -> {name} pushed={p}")
    _enq(impl)


def step_destroy():
    def impl():
        global _win, _list
        for fid in list(_items.values()) + [_list, _win]:
            if fid > 0:
                try:
                    PyUIManager.UIManager.destroy_ui_component_by_frame_id(fid)
                except Exception:
                    pass
        _items.clear(); _pushed.clear()
        _win = _list = 0
        _log_msg("destroyed all")
    _enq(impl)


def main() -> None:
    _poll_buttons()

    if not PyImGui.begin(MODULE_NAME, True, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    PyImGui.text_colored("1) window  2) scrollable frame list  3) add controls (stacked rows).", (0.4, 0.8, 1.0, 1.0))
    PyImGui.text(f"window={_win}  list={_list}  items={len(_items)}")
    PyImGui.text("verdict: [OK] confirmed  [~] likely  [?] uncertain  [!] needs-workaround (may crash)")
    PyImGui.text("styled_button: OPEN A MERCHANT first (needs its image list).")
    PyImGui.separator()

    if PyImGui.button("1) Create Window"):
        step_window()
    PyImGui.same_line(0, -1)
    if PyImGui.button("2) Create Scrollable Frame List"):
        step_list()

    PyImGui.separator()
    PyImGui.text_colored("Add each control as a row (one at a time):", (0.9, 0.8, 0.3, 1.0))
    for idx, (control, caption, flags, tag, is_btn) in enumerate(CONTROLS):
        color = {"OK": (0.3, 1.0, 0.4, 1.0), "~": (0.6, 1.0, 0.6, 1.0),
                 "?": (0.9, 0.9, 0.4, 1.0), "!": (1.0, 0.55, 0.3, 1.0)}[tag]
        if PyImGui.button(f"[{tag}] {control}##{idx}"):
            add_control(control, caption, flags, is_btn, idx)
        PyImGui.same_line(0, -1)
        got = _items.get(control, 0)
        PyImGui.text_colored(f" id={got}" if got else " -", color)

    PyImGui.separator()
    if PyImGui.button("Destroy All"):
        step_destroy()

    PyImGui.separator()
    PyImGui.text_colored("=== Log ===", (0.7, 0.7, 0.3, 1.0))
    if PyImGui.begin_child("##log", (0.0, 220.0), True):
        for line in _log[-22:]:
            PyImGui.text(line)
        PyImGui.end_child()
    PyImGui.end()


def configure() -> None:
    pass


if __name__ == "__main__":
    main()
