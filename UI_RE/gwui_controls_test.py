"""
gwui_controls_test.py - in-client test harness for the native GWUI control toolkit.

Workflow:
  1. Click "Create <control>" for one control at a time (each opens its own staggered window).
  2. Interact with it in-game per the "how to test" hint (click / toggle / drag / type).
  3. Watch the live STATE line (polled every frame).
  4. Mark a verdict: [OK] works, [PART] partial, [FAIL] wrong/no-render, [CRASH] crashed the client.
  5. Results AUTO-SAVE to UI_RE/ui_test_results.txt on every verdict + every create, so a crash never
     loses what you already recorded. (If a control crashes: restart the client, reload this widget,
     mark that control [CRASH] - the file already has your earlier verdicts.)

The results file is plain text; share it or just tell me to read it.

REQUIRES the current rebuilt DLL.
"""

import os
import time

import Py4GW
import PyImGui
import PyUIManager

from Py4GWCoreLib.GWUI import GWUI

MODULE_NAME = "GWUI Controls Test"

# Py4GW exec's this script as a string, so __file__ is not defined — fall back to the known abs path.
try:
    _BASE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _cand = os.path.join(os.getcwd(), "UI_RE")
    _BASE = _cand if os.path.isdir(_cand) else r"C:\Users\Apo\Py4GW_python_files\UI_RE"

RESULTS_PATH = os.path.join(_BASE, "ui_test_results.txt")
LOG_PATH = os.path.join(_BASE, "ui_test_log.txt")

_ctl: dict = {}      # name -> dict(win, id, list, state, ...)
_verdict: dict = {}  # name -> "OK" | "PART" | "FAIL" | "CRASH" | "?"
_log: list = []
_slot = [0]

VERDICTS = ("OK", "PART", "FAIL", "CRASH")
VERDICT_COLOR = {
    "OK":    (0.3, 1.0, 0.4, 1.0),
    "PART":  (0.9, 0.85, 0.3, 1.0),
    "FAIL":  (1.0, 0.55, 0.3, 1.0),
    "CRASH": (1.0, 0.3, 0.3, 1.0),
    "?":     (0.5, 0.5, 0.5, 1.0),
}


def _log_msg(m: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    _log.append(line)
    print(f"[{MODULE_NAME}] {m}")
    if len(_log) > 200:
        _log[:] = _log[-200:]
    # CRASH-SAFE: append + flush + fsync each line so a native crash mid-test still leaves the trail
    # on disk (in particular the "CREATING <x>" line written right before a risky create).
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


def _enq(fn) -> None:
    Py4GW.Game.enqueue(fn)


def _new_window(name: str) -> int:
    s = _slot[0]; _slot[0] += 1
    return int(GWUI.CreateWindow(240.0 + s * 45.0, 120.0 + s * 45.0, 230.0, 190.0, name) or 0)


# ── per-control creation ────────────────────────────────────────────────
def _c_button(n):
    w = _new_window(n); bl = GWUI.CreateButtonList(w); b = GWUI.CreateButton(bl, "Button")
    _ctl[n] = {"win": w, "list": bl, "id": b, "state": "?"}

def _c_checkbox(n):
    w = _new_window(n); c = GWUI.CreateCheckbox(w, "Checkbox", 1)
    _ctl[n] = {"win": w, "id": c, "state": "?"}

def _c_radio(n):
    w = _new_window(n); r = GWUI.CreateRadioGroup(w, ["Option A", "Option B", "Option C"], 0)
    _ctl[n] = {"win": w, "id": r, "state": "?"}

def _c_hyperlink(n):
    w = _new_window(n); hl = GWUI.CreateHyperlinkList(w); GWUI.CreateHyperlink(hl, "Hyperlink")
    _ctl[n] = {"win": w, "list": hl, "state": "?"}

def _c_edit(n):
    w = _new_window(n); e = GWUI.CreateEditBox(w, "EditBox", 0)
    _ctl[n] = {"win": w, "id": e, "state": "?"}

def _c_progress(n):
    w = _new_window(n); pb = GWUI.CreateProgressBar(w, 10.0, 10.0, 160.0, 18.0)
    _ctl[n] = {"win": w, "id": pb, "state": "cycling", "val": 0}

def _c_tabs(n):
    w = _new_window(n); t = GWUI.CreateTabs(w)
    GWUI.AddTab(t, "Tab 1", 0, "body 1"); GWUI.AddTab(t, "Tab 2", 1, "body 2")
    _ctl[n] = {"win": w, "id": t, "state": "?"}

def _c_slider(n):
    w = _new_window(n); s = GWUI.CreateSlider(w, 0, 100, 25, 150.0, 18.0)
    _ctl[n] = {"win": w, "id": s, "state": "?"}

def _c_groupheader(n):
    w = _new_window(n)
    gl = int(PyUIManager.UIManager.create_scrollable_content_by_frame_id(w, 0, 0x20000) or 0)
    g = GWUI.CreateGroupHeader(gl, "Section", 0)
    codes = []
    for i, t in enumerate(("Item One", "Item Two", "Item Three"), start=1):
        try: GWUI.AddTextItem(gl, t, i)
        except Exception: pass
        codes.append(i)
    GWUI.RegisterGroupSection(g, gl, codes)
    _ctl[n] = {"win": w, "list": gl, "id": g, "state": "section"}


# (name, create fn, how-to-test hint)
CONTROLS = [
    ("button",      _c_button,      "click it -> STATE shows CLICKED"),
    ("checkbox",    _c_checkbox,    "click box -> STATE checked flips true/false; look for a real tick"),
    ("radio",       _c_radio,       "click rows -> only one highlights; STATE selection = index"),
    ("hyperlink",   _c_hyperlink,   "hover (no crash) + click -> STATE shows CLICKED"),
    ("edit",        _c_edit,        "should show an outlined box; click + TYPE; STATE shows text"),
    ("progress",    _c_progress,    "bar fill should animate 0->100 (auto-cycling)"),
    ("tabs",        _c_tabs,        "should show TEXTURED tabs; click to switch; STATE = active tab"),
    ("slider",      _c_slider,      "drag the thumb; STATE = value; (known: renders wide)"),
    ("groupheader", _c_groupheader, "toggle the section checkbox -> the 3 rows collapse/expand"),
]


def _make(name, fn):
    def impl():
        # Persist BEFORE the create so a HARD (native) crash — which raises no Python exception — still
        # leaves "CREATING <name>" on disk, telling us exactly which control killed the client.
        _verdict.setdefault(name, "?")
        _log_msg(f"CREATING {name} ...")
        _save()
        try:
            fn(name)
            _log_msg(f"{name}: created ok id={_ctl.get(name, {}).get('id', _ctl.get(name, {}).get('list'))}")
        except Exception as e:
            _verdict[name] = "CRASH"
            _log_msg(f"{name}: EXCEPTION {e}")
        _save()
    _enq(impl)


def _poll():
    def impl():
        GWUI.UpdateGroupSections()
        # Drop any control whose host window was closed (e.g. native [X]) BEFORE polling it — messaging a
        # freed frame id reads freed memory and crashes. This stops the "keeps ticking/accessing after
        # close" leaks/crashes for progress/tabs/slider.
        dead = []
        for n, c in list(_ctl.items()):
            win = c.get("win")
            try:
                alive = (not win) or bool(PyUIManager.UIManager.frame_exists_by_frame_id(win))
            except Exception:
                alive = True
            if not alive:
                dead.append(n)
        for n in dead:
            _ctl.pop(n, None)
            _log_msg(f"{n}: window gone — stopped polling")
        for n, c in list(_ctl.items()):
            try:
                if n == "button":
                    if GWUI.IsButtonClicked(c["id"]): c["state"] = f"CLICKED @ {time.strftime('%H:%M:%S')}"
                elif n == "checkbox":
                    c["state"] = f"checked={GWUI.IsChecked(c['id'])}"
                elif n == "radio":
                    c["state"] = f"selection={GWUI.GetRadioSelection(c['id'])}"
                elif n == "hyperlink":
                    h = GWUI.GetClickedHyperlink(c["list"])
                    if h: c["state"] = f"CLICKED item {h}"
                elif n == "edit":
                    c["state"] = f"text='{GWUI.GetEditBoxText(c['id'])}'"
                elif n == "progress":
                    v = (c.get("val", 0) + 1) % 101
                    c["val"] = v
                    GWUI.SetProgressBarPercent(c["id"], v)
                    c["state"] = f"percent={v} (cycling)"
                elif n == "tabs":
                    if GWUI.IsTabChanged(c["id"]): c["state"] = f"active tab={GWUI.GetActiveTab(c['id'])}"
                elif n == "slider":
                    c["state"] = f"value={GWUI.GetSliderValue(c['id'])}"
                elif n == "groupheader":
                    c["state"] = f"open={GWUI.IsGroupHeaderOpen(c['id'])} (toggle to collapse rows)"
            except Exception as e:
                c["state"] = f"err:{e}"
    _enq(impl)


def _set_verdict(name, v):
    _verdict[name] = v
    _log_msg(f"verdict {name} = {v}")
    _save()


def _save():
    try:
        with open(RESULTS_PATH, "w", encoding="utf-8") as f:
            f.write("GWUI native control test results\n")
            f.write("saved: %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
            f.write("=" * 60 + "\n")
            f.write("%-13s %-6s %s\n" % ("CONTROL", "VERDICT", "LIVE STATE"))
            f.write("-" * 60 + "\n")
            for name, _fn, _hint in CONTROLS:
                v = _verdict.get(name, "?")
                st = _ctl.get(name, {}).get("state", "(not created)")
                f.write("%-13s %-6s %s\n" % (name, v, st))
            f.write("=" * 60 + "\n")
            done = [v for v in _verdict.values() if v in VERDICTS]
            ok = sum(1 for v in _verdict.values() if v == "OK")
            f.write("marked %d/%d  |  OK=%d PART=%d FAIL=%d CRASH=%d\n" % (
                len(done), len(CONTROLS), ok,
                sum(1 for v in _verdict.values() if v == "PART"),
                sum(1 for v in _verdict.values() if v == "FAIL"),
                sum(1 for v in _verdict.values() if v == "CRASH")))
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"[{MODULE_NAME}] save failed: {e}")


def _destroy():
    def impl():
        # SAFE teardown: scrub hover/focus globals then destroy each window. This is the fix for the
        # "crash on closing the host window" UAF. IMPORTANT: close windows via THIS button, not the
        # window's native [X] (that path doesn't run the scrub yet).
        wins = {c.get("win") for c in _ctl.values() if c.get("win")}
        for w in wins:
            try: GWUI.DestroyWindow(w)     # destroy_window_safely_by_frame_id: scrub + native destroy
            except Exception as e: _log_msg(f"destroy {w}: {e}")
        _ctl.clear(); _slot[0] = 0
        _log_msg("destroyed all windows (safe)")
    _enq(impl)


def main() -> None:
    _poll()
    if not PyImGui.begin(MODULE_NAME, True, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end(); return

    PyImGui.text_colored("Create -> interact -> mark verdict. Auto-saves to ui_test_results.txt.", (0.4, 0.8, 1.0, 1.0))
    done = sum(1 for v in _verdict.values() if v in VERDICTS)
    PyImGui.text(f"marked {done}/{len(CONTROLS)}   file: UI_RE/ui_test_results.txt")
    PyImGui.separator()

    for name, fn, hint in CONTROLS:
        if PyImGui.button(f"Create {name}##c_{name}"):
            _make(name, fn)
        PyImGui.same_line(0, -1)
        v = _verdict.get(name, "?")
        PyImGui.text_colored(f"[{v}]", VERDICT_COLOR.get(v, VERDICT_COLOR["?"]))
        # verdict buttons
        for vb in VERDICTS:
            PyImGui.same_line(0, -1)
            if PyImGui.small_button(f"{vb}##{name}_{vb}"):
                _set_verdict(name, vb)
        c = _ctl.get(name)
        PyImGui.text_colored(f"    {hint}", (0.6, 0.6, 0.6, 1.0))
        PyImGui.text_colored(f"    STATE: {c['state']}" if c else "    STATE: (not created)",
                             (0.3, 1.0, 0.4, 1.0) if c else (0.5, 0.5, 0.5, 1.0))
        PyImGui.separator()

    if PyImGui.button("Save Results Now"):
        _save(); _log_msg("results saved")
    PyImGui.same_line(0, -1)
    if PyImGui.button("Destroy All"):
        _destroy()

    PyImGui.separator()
    PyImGui.text_colored("=== Log ===", (0.7, 0.7, 0.3, 1.0))
    if PyImGui.begin_child("##log", (0.0, 140.0), True):
        for line in _log[-12:]:
            PyImGui.text(line)
        PyImGui.end_child()
    PyImGui.end()


def configure() -> None:
    pass


if __name__ == "__main__":
    main()
