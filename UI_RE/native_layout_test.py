"""
native_layout_test.py — ISOLATED harness for the native content-page path.

Separate from gwui_controls_test.py on purpose: this exercises ONLY the new native-layout mechanism
(controls nested under a real IUi::UiCtlContentPageProc content page in the reserved 0x2710 band), so
iterating here CANNOT regress the working controls in the main harness.

Hypothesis under test (docs/RE/native_dialog_layout_process.md):
  A control parented to a real content page (not the window chrome) —
    * renders on the correct layer (not buried),
    * is clickable,
    * and is torn down cleanly by the native title-bar [X] (IUi::PopCloser) with NO crash.

Workflow: click "Create <thing>" (each opens its own window with a content page + the control on it),
interact, then CLOSE VIA THE NATIVE [X] and watch for a crash. Crash-safe log at UI_RE/native_layout_log.txt
(the "CREATING"/"CLOSING" trail survives a hard crash so we know exactly what killed it).
"""

import os
import time

import Py4GW
import PyImGui
import PyUIManager

from Py4GWCoreLib.GWUI import GWUI

MODULE_NAME = "Native Layout Test"

try:
    _BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _BASE = r"C:\Users\Apo\Py4GW_python_files\UI_RE"
LOG_PATH = os.path.join(_BASE, "native_layout_log.txt")

_ctl: dict = {}
_log: list = []
_slot = [0]


def _log_msg(m: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    _log.append(line)
    if len(_log) > 200:
        _log[:] = _log[-200:]
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n"); f.flush(); os.fsync(f.fileno())
    except Exception:
        pass


def _enq(fn) -> None:
    Py4GW.Game.enqueue(fn)


def _new_window(name: str) -> int:
    """The working Py4GW window (CtlView + chrome — the same family DevText uses)."""
    s = _slot[0]; _slot[0] += 1
    return int(GWUI.CreateWindow(300.0 + s * 40.0, 160.0 + s * 40.0, 240.0, 210.0, name) or 0)


def _list(window_id: int) -> int:
    """A scrollable frame list (the DevText/button host)."""
    return int(GWUI.CreateButtonList(window_id) or 0)


def _add_item(list_id: int, control: str, caption: str, idx: int) -> int:
    """Add a control as a FRAME-LIST ITEM — the native DevText pattern (CtlFrameListCreateItem),
    the same path the working button uses. NOT a direct child."""
    return int(PyUIManager.UIManager.add_control_item_by_frame_id(list_id, control, caption, idx, 0) or 0)


# ── PHASE 2: OWNED BAND-MEMBER content frame (teardown fix) ──
def _c_dispatcher(n):
    """Host the checkbox in an OWNED band-member content frame (band 0x2710 + our dispatcher). The
    native [X] should now route through PopCloser and tear it down WITHOUT crashing."""
    w = _new_window(n)
    band = int(PyUIManager.UIManager.create_owned_band_frame_by_frame_id(w, 200.0, 160.0) or 0)
    host = band or w
    c = GWUI.CreateCheckbox(host, "Checkbox (band-owned)", 1)
    _ctl[n] = {"win": w, "band": band, "id": c, "state": f"band={band}"}


# ── DevText pattern: controls hosted as FRAME-LIST ITEMS in a scrollable view ──
def _c_button(n):
    w = _new_window(n); li = _list(w); it = _add_item(li, "flat_button", "Button", 1)
    _ctl[n] = {"win": w, "list": li, "id": it, "state": "?"}

def _c_checkbox(n):
    w = _new_window(n); li = _list(w); it = _add_item(li, "checkbox", "Checkbox item", 1)
    _ctl[n] = {"win": w, "list": li, "id": it, "state": "?"}

def _c_slider(n):
    w = _new_window(n); li = _list(w); it = _add_item(li, "slider", "Slider item", 1)
    _ctl[n] = {"win": w, "list": li, "id": it, "state": "?"}

def _c_edit(n):
    w = _new_window(n); li = _list(w); it = _add_item(li, "edit", "Edit item", 1)
    _ctl[n] = {"win": w, "list": li, "id": it, "state": "?"}


CONTROLS = [
    ("dispatcher", _c_dispatcher, "PHASE 2: checkbox in an OWNED band frame — renders? toggles? survives native [X]?"),
    ("button",     _c_button,     "as a list item (baseline that works): renders? survives [X]?"),
    ("checkbox",   _c_checkbox,   "checkbox as a LIST ITEM (DevText pattern): renders? toggles? survives [X]?"),
    ("slider",     _c_slider,     "slider as a LIST ITEM: renders? width sane? survives [X]?"),
    ("edit",       _c_edit,       "edit as a LIST ITEM: shows a box? survives [X]?"),
]


def _make(name, fn):
    def impl():
        _log_msg(f"CREATING {name} (page path) ...")
        try:
            fn(name)
            c = _ctl.get(name, {})
            _log_msg(f"{name}: created ok win={c.get('win')} page={c.get('page')} id={c.get('id')}")
        except Exception as e:
            _log_msg(f"{name}: EXCEPTION {e}")
    _enq(impl)


def _poll():
    def impl():
        for n, c in list(_ctl.items()):
            win = c.get("win")
            try:
                alive = (not win) or bool(PyUIManager.UIManager.frame_exists_by_frame_id(win))
            except Exception:
                alive = True
            if not alive:
                _ctl.pop(n, None)
                _log_msg(f"{n}: window gone — stopped polling")
                continue
            try:
                if n == "dispatcher":
                    c["state"] = f"checked={GWUI.IsChecked(c['id'])} (owned frame)"
                elif n == "button":
                    if GWUI.IsButtonClicked(c["id"]): c["state"] = f"CLICKED @ {time.strftime('%H:%M:%S')}"
                elif n == "checkbox":
                    c["state"] = f"checked={GWUI.IsChecked(c['id'])}"
                elif n == "slider":
                    c["state"] = f"value={GWUI.GetSliderValue(c['id'])}"
                elif n == "edit":
                    c["state"] = f"text='{GWUI.GetEditBoxText(c['id'])}'"
            except Exception as e:
                c["state"] = f"err:{e}"
    _enq(impl)


def _destroy():
    def impl():
        wins = {c.get("win") for c in _ctl.values() if c.get("win")}
        for w in wins:
            try: GWUI.DestroyWindow(w)
            except Exception as e: _log_msg(f"destroy {w}: {e}")
        _ctl.clear(); _slot[0] = 0
        _log_msg("destroyed all (safe path)")
    _enq(impl)


def main() -> None:
    _poll()
    if not PyImGui.begin(MODULE_NAME, True, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end(); return
    PyImGui.text_colored("ISOLATED native content-page test. Close each window via its native [X] to test teardown.",
                         (0.4, 0.8, 1.0, 1.0))
    PyImGui.separator()
    for name, fn, hint in CONTROLS:
        if PyImGui.button(f"Create {name}##nl_{name}"):
            _make(name, fn)
        c = _ctl.get(name)
        PyImGui.text_colored(f"    {hint}", (0.6, 0.6, 0.6, 1.0))
        PyImGui.text_colored(f"    STATE: {c['state']}" if c else "    STATE: (not created)",
                             (0.3, 1.0, 0.4, 1.0) if c else (0.5, 0.5, 0.5, 1.0))
        PyImGui.separator()
    if PyImGui.button("Destroy All (safe)"):
        _destroy()
    PyImGui.separator()
    PyImGui.text_colored("=== Log ===", (0.7, 0.7, 0.3, 1.0))
    if PyImGui.begin_child("##nllog", (0.0, 130.0), True):
        for line in _log[-10:]:
            PyImGui.text(line)
        PyImGui.end_child()
    PyImGui.end()


def configure() -> None:
    pass


if __name__ == "__main__":
    main()
