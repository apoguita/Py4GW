"""
Slider Fix Test — step-by-step (2026-06-06)
============================================
Each step is a separate enqueued call. Click in order: 1→2→3→4→5→6.

FIX APPLIED: SliderFrame_Callback now resolves to IUi::UiCtlSliderProc (0x0087f440)
             instead of CtlSliderProc (0x00615fe0). The wrapper renders the textured
             slider bar+thumb; the base only drew a plain gray rectangle.
             Also: component_flags changed from 0x300 to 0 (matching game).

VISUAL VERIFICATION: After Step 5, the slider should show a TEXTURED bar with a
                     visible thumb indicator — NOT a plain gray rectangle.
                     If it looks like a featureless gray box, the FrameProc fix
                     didn't take (still using CtlSliderProc).

Usage: Open "Slider Fix" panel in Widget Manager.
"""
import Py4GW
import PyImGui
import PyUIManager

window_id = 0
slider_id = 0
last_msg = ""
slider_visible = None  # True = textured slider, False = gray rectangle, None = not tested


def _dbg(msg):
    global last_msg
    print(f"[SliderFix] {msg}")
    last_msg = msg


def _enqueue(fn):
    Py4GW.Game.enqueue(fn)


# ── Step 1: Create container window ──────────────────────────────

def _step1():
    global window_id
    um = PyUIManager.UIManager
    _dbg("═══ STEP 1: CreateNativeWindow ═══")
    try:
        raw = um.CreateNativeWindow(50, 100, 400, 200, "Slider Debug")
        _dbg(f"CreateNativeWindow returned: {raw} (type={type(raw).__name__})")
        window_id = int(raw or 0)
    except Exception as e:
        _dbg(f"EXCEPTION: {e}")
        return
    if not window_id:
        _dbg("FAIL: window_id = 0")
        return
    _dbg(f"OK: window_id={window_id}")


def step1():
    _enqueue(_step1)


# ── Step 2: Create slider frame (flags=0, wrapper FrameProc) ──────

def _step2():
    global slider_id, window_id
    um = PyUIManager.UIManager
    _dbg("═══ STEP 2: create_slider_frame_by_frame_id ═══")

    if not window_id:
        _dbg("FAIL: no window — run Step 1 first")
        return

    try:
        _ = um.create_slider_frame_by_frame_id
    except AttributeError:
        _dbg("FAIL: binding not found — rebuild DLL")
        return

    try:
        # flags=0 matches what the game passes (was 0x300 in Phase 7)
        raw = um.create_slider_frame_by_frame_id(window_id, 0, 0, "DebugSlider")
        _dbg(f"Returned: {raw} (type={type(raw).__name__})")
        slider_id = int(raw or 0)
    except Exception as e:
        _dbg(f"EXCEPTION: {e}")
        return

    if not slider_id:
        _dbg("FAIL: slider_id = 0")
        return
    _dbg(f"OK: slider_id={slider_id}")


def step2():
    _enqueue(_step2)


# ── Step 3: FrameSetSize (NEW binding — makes slider visible) ────

def _step3():
    global slider_id
    um = PyUIManager.UIManager
    _dbg("═══ STEP 3: frame_set_size_by_frame_id ═══")

    if not slider_id:
        _dbg("FAIL: no slider")
        return

    try:
        _ = um.frame_set_size_by_frame_id
    except AttributeError:
        _dbg("FAIL: frame_set_size_by_frame_id not found — rebuild DLL")
        return

    _dbg(f"Calling frame_set_size({slider_id}, 200.0, 30.0)")
    try:
        raw = um.frame_set_size_by_frame_id(slider_id, 200.0, 30.0)
        _dbg(f"Returned: {raw}")
    except Exception as e:
        _dbg(f"EXCEPTION: {e}")


def step3():
    _enqueue(_step3)


# ── Step 4: SetRange (works — returned True before) ───────────────

def _step4():
    global slider_id
    um = PyUIManager.UIManager
    _dbg("═══ STEP 4: set_slider_range_by_frame_id ═══")

    if not slider_id:
        _dbg("FAIL: no slider")
        return

    try:
        _ = um.set_slider_range_by_frame_id
    except AttributeError:
        _dbg("FAIL: binding not found — rebuild DLL")
        return

    _dbg(f"Calling set_slider_range({slider_id}, 0, 100)")
    try:
        raw = um.set_slider_range_by_frame_id(slider_id, 0, 100)
        _dbg(f"Returned: {raw}")
    except Exception as e:
        _dbg(f"EXCEPTION: {e}")


def step4():
    _enqueue(_step4)


# ── Step 5: SetValue (fixed — direct SendFrameUIMessage) ──────────

def _step5():
    global slider_id
    um = PyUIManager.UIManager
    _dbg("═══ STEP 5: set_slider_value_by_frame_id ═══")

    if not slider_id:
        _dbg("FAIL: no slider")
        return

    _dbg(f"Calling set_slider_value({slider_id}, 50)")
    try:
        raw = um.set_slider_value_by_frame_id(slider_id, 50)
        _dbg(f"Returned: {raw}")
    except Exception as e:
        _dbg(f"EXCEPTION: {e}")


def step5():
    _enqueue(_step5)


# ── Step 6: GetValue ─────────────────────────────────────────────

def _step6():
    global slider_id
    um = PyUIManager.UIManager
    _dbg("═══ STEP 6: get_slider_value_by_frame_id ═══")

    if not slider_id:
        _dbg("FAIL: no slider")
        return

    try:
        val = um.get_slider_value_by_frame_id(slider_id)
        _dbg(f"GetValue returned: {val}")
        if val == 50:
            _dbg("PASS: value = 50")
        else:
            _dbg(f"MISMATCH: got {val}, expected 50")
    except Exception as e:
        _dbg(f"EXCEPTION: {e}")


def step6():
    _enqueue(_step6)


# ── All at once ──────────────────────────────────────────────────

def _all_impl():
    _step1()
    _step2()
    _step3()
    _step4()
    _step5()
    _step6()


def test_all():
    _enqueue(_all_impl)


# ── Clean ────────────────────────────────────────────────────────

def _clean_impl():
    global window_id, slider_id
    from Py4GWCoreLib import UIManager
    um = PyUIManager.UIManager
    destroyed = 0
    for fid in list(UIManager.GetFrameArray()):
        try:
            t = um.get_frame_title_by_frame_id(fid) or ""
            if "Slider Debug" in t:
                um.destroy_ui_component_by_frame_id(fid)
                destroyed += 1
                _dbg(f"Destroyed {t} (fid={fid})")
        except Exception:
            pass
    _dbg(f"Cleanup: {destroyed} destroyed")
    window_id = 0
    slider_id = 0


def clean_all():
    _enqueue(_clean_impl)


# ── PyImGui panel ────────────────────────────────────────────────

def main():
    global window_id, slider_id, last_msg, slider_visible

    if not PyImGui.begin("Slider Fix v2"):
        return

    PyImGui.text(f"window_id={window_id}  slider_id={slider_id}")
    PyImGui.separator()
    PyImGui.text("Click in order: 1 -> 2 -> 3 -> 4 -> 5 -> 6")
    PyImGui.separator()

    if PyImGui.button("1. CreateWindow"):
        step1()
    PyImGui.same_line(0, -1)
    if PyImGui.button("2. Create Slider"):
        step2()

    if PyImGui.button("3. FrameSetSize"):
        step3()
    PyImGui.same_line(0, -1)
    if PyImGui.button("4. SetRange(0,100)"):
        step4()

    if PyImGui.button("5. SetValue(50)"):
        step5()
    PyImGui.same_line(0, -1)
    if PyImGui.button("6. GetValue"):
        step6()

    PyImGui.separator()

    if PyImGui.button("Run ALL steps"):
        test_all()
    PyImGui.same_line(0, -1)
    if PyImGui.button("Clean All"):
        clean_all()

    PyImGui.separator()

    # ── Visual verification ─────────────────────────────────────
    PyImGui.text("VISUAL CHECK (look at the window):")
    if PyImGui.button("I see a TEXTURED SLIDER (bar+thumb)"):
        slider_visible = True
        _dbg("USER CONFIRMED: textured slider visible — FIX WORKS!")
    PyImGui.same_line(0, -1)
    if PyImGui.button("I see a GRAY RECTANGLE (no slider)"):
        slider_visible = False
        _dbg("USER REPORTED: gray rectangle — wrapper NOT applied")

    if slider_visible is True:
        PyImGui.text_colored((0.0, 1.0, 0.0, 1.0), "VERIFIED: Textured slider renders correctly")
    elif slider_visible is False:
        PyImGui.text_colored((1.0, 0.0, 0.0, 1.0), "FAIL: Only gray rectangle — fix not applied")

    PyImGui.separator()
    PyImGui.text("Last message:")
    PyImGui.text_wrapped(last_msg if last_msg else "(none)")

    PyImGui.end()


if __name__ == "__main__":
    main()
