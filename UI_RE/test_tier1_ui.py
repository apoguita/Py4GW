"""
Tier 1 UI Control Test Panel (2026-06-04)
=========================================
All native calls go through Py4GW.Game.enqueue() — game thread safe.
All debug output via print() to console — nothing on screen.

REQUIRES rebuilt DLL for the new Create bindings to exist.
"""
import Py4GW
import PyImGui
import PyUIManager

# ── State ─────────────────────────────────────────────────────────
controls = {}       # name -> frame_id
last_status = ""    # status from last enqueued operation


def _dbg(msg: str) -> None:
    print(f"[Tier1] {msg}")


def _enqueue(fn):
    """Enqueue a callable on the game thread."""
    Py4GW.Game.enqueue(fn)


# ═══════════════════════════════════════════════════════════════════
# Test: Dropdown
# ═══════════════════════════════════════════════════════════════════

def _test_dropdown_impl():
    um = PyUIManager.UIManager
    _dbg("═══ DROPDOWN ═══")

    # 1. Create container window
    win = int(um.CreateNativeWindow(50, 100, 400, 200, "Dropdown Test") or 0)
    if not win:
        _dbg("FAIL: CreateNativeWindow returned 0")
        return
    _dbg(f"Window fid={win}")

    # 2. Create dropdown
    try:
        fid = int(um.create_dropdown_frame_by_frame_id(win, 0x300, 0, "TestDD") or 0)
    except AttributeError:
        _dbg("ERROR: create_dropdown_frame_by_frame_id not found — rebuild DLL")
        return
    if not fid:
        _dbg("FAIL: Create returned 0")
        return
    _dbg(f"Dropdown fid={fid}")
    controls["Dropdown"] = fid

    # 3. Add options
    _dbg(f"AddOption(Alpha)={um.add_dropdown_option_by_frame_id(fid, 'Alpha  \x0108\x0107A\x0001', 10)}")
    _dbg(f"AddOption(Beta) ={um.add_dropdown_option_by_frame_id(fid, 'Beta  \x0108\x0107B\x0001', 20)}")
    _dbg(f"AddOption(Gamma)={um.add_dropdown_option_by_frame_id(fid, 'Gamma\x0108\x0107C\x0001', 30)}")

    # 4. Select and verify
    _dbg(f"SelectOption(20)={um.select_dropdown_option_by_frame_id(fid, 20)}")
    val = um.get_dropdown_value_by_frame_id(fid)
    _dbg(f"GetValue()={val} {'PASS' if val == 20 else 'FAIL expected 20'}")


def test_dropdown():
    _enqueue(_test_dropdown_impl)


# ═══════════════════════════════════════════════════════════════════
# Test: Slider
# ═══════════════════════════════════════════════════════════════════

def _test_slider_impl():
    um = PyUIManager.UIManager
    _dbg("═══ SLIDER ═══")
    win = int(um.CreateNativeWindow(70, 120, 400, 200, "Slider Test") or 0)
    if not win:
        _dbg("FAIL: CreateNativeWindow returned 0")
        return
    _dbg(f"Window fid={win}")

    try:
        fid = int(um.create_slider_frame_by_frame_id(win, 0x300, 0, "TestSlider") or 0)
    except AttributeError:
        _dbg("ERROR: binding not found — rebuild DLL")
        return
    if not fid:
        _dbg("FAIL: Create returned 0")
        return
    _dbg(f"Slider fid={fid}")
    controls["Slider"] = fid

    _dbg(f"SetValue(50)={um.set_slider_value_by_frame_id(fid, 50)}")
    val = um.get_slider_value_by_frame_id(fid)
    _dbg(f"GetValue()={val} {'PASS' if val == 50 else 'FAIL expected 50'}")


def test_slider():
    _enqueue(_test_slider_impl)


# ═══════════════════════════════════════════════════════════════════
# Test: EditableText
# ═══════════════════════════════════════════════════════════════════

def _test_editable_text_impl():
    um = PyUIManager.UIManager
    _dbg("═══ EDITABLE TEXT ═══")
    win = int(um.CreateNativeWindow(90, 140, 400, 200, "EditableText Test") or 0)
    if not win:
        _dbg("FAIL: CreateNativeWindow returned 0")
        return
    _dbg(f"Window fid={win}")

    try:
        fid = int(um.create_editable_text_frame_by_frame_id(win, 0x300, 0, "TestEdit") or 0)
    except AttributeError:
        _dbg("ERROR: binding not found — rebuild DLL")
        return
    if not fid:
        _dbg("FAIL: Create returned 0")
        return
    _dbg(f"EditableText fid={fid}")
    controls["EditableText"] = fid

    _dbg(f"SetMaxLength(256)={um.set_editable_text_max_length_by_frame_id(fid, 256)}")
    _dbg(f"SetReadOnly(False)={um.set_editable_text_read_only_by_frame_id(fid, False)}")
    _dbg(f"SetValue('Hello GW!')={um.set_editable_text_value_by_frame_id(fid, 'Hello GW!')}")
    val = um.get_editable_text_value_by_frame_id(fid)
    _dbg(f"GetValue()='{val}' {'PASS' if val == 'Hello GW!' else 'FAIL'}")


def test_editable_text():
    _enqueue(_test_editable_text_impl)


# ═══════════════════════════════════════════════════════════════════
# Test: ProgressBar
# ═══════════════════════════════════════════════════════════════════

def _test_progress_bar_impl():
    um = PyUIManager.UIManager
    _dbg("═══ PROGRESS BAR ═══")
    win = int(um.CreateNativeWindow(110, 160, 400, 200, "ProgressBar Test") or 0)
    if not win:
        _dbg("FAIL: CreateNativeWindow returned 0")
        return
    _dbg(f"Window fid={win}")

    try:
        fid = int(um.create_progress_bar_by_frame_id(win, 0x300, 0, "TestProgress") or 0)
    except AttributeError:
        _dbg("ERROR: binding not found — rebuild DLL")
        return
    if not fid:
        _dbg("FAIL: Create returned 0")
        return
    _dbg(f"ProgressBar fid={fid}")
    controls["ProgressBar"] = fid

    _dbg(f"SetMax(100)={um.set_progress_bar_max_by_frame_id(fid, 100)}")
    _dbg(f"SetStyle(kPeach)={um.set_progress_bar_style_by_frame_id(fid, 0)}")
    _dbg(f"SetValue(42)={um.set_progress_bar_value_by_frame_id(fid, 42)}")
    val = um.get_progress_bar_value_by_frame_id(fid)
    _dbg(f"GetValue()={val} {'PASS' if val == 42 else 'FAIL expected 42'}")


def test_progress_bar():
    _enqueue(_test_progress_bar_impl)


# ═══════════════════════════════════════════════════════════════════
# Test: Tabs
# ═══════════════════════════════════════════════════════════════════

def _test_tabs_impl():
    um = PyUIManager.UIManager
    _dbg("═══ TABS ═══")
    win = int(um.CreateNativeWindow(130, 180, 400, 200, "Tabs Test") or 0)
    if not win:
        _dbg("FAIL: CreateNativeWindow returned 0")
        return
    _dbg(f"Window fid={win}")

    try:
        fid = int(um.create_tabs_frame_by_frame_id(win, 0x300, 0, "TestTabs") or 0)
    except AttributeError:
        _dbg("ERROR: binding not found — rebuild DLL")
        return
    if not fid:
        _dbg("FAIL: Create returned 0")
        return
    _dbg(f"Tabs fid={fid}")
    controls["Tabs"] = fid

    t1 = int(um.add_tab_by_frame_id(fid, "Tab One\x0108\x0107One\x0001", 0x300, 0, 0, 0) or 0)
    _dbg(f"AddTab('Tab One')={t1}")
    t2 = int(um.add_tab_by_frame_id(fid, "Tab Two\x0108\x0107Two\x0001", 0x300, 1, 0, 0) or 0)
    _dbg(f"AddTab('Tab Two')={t2}")
    _dbg(f"ChooseTab(0)={um.choose_tab_by_index_by_frame_id(fid, 0)}")
    cur = um.get_current_tab_index_by_frame_id(fid)
    _dbg(f"GetCurrentTabIndex()={cur} {'PASS' if cur == 0 else 'FAIL expected 0'}")


def test_tabs():
    _enqueue(_test_tabs_impl)


# ═══════════════════════════════════════════════════════════════════
# Test ALL
# ═══════════════════════════════════════════════════════════════════

def _test_all_impl():
    _dbg("=" * 50)
    _dbg("TEST ALL — Tier 1 Controls")
    _dbg("=" * 50)
    _test_dropdown_impl()
    _test_slider_impl()
    _test_editable_text_impl()
    _test_progress_bar_impl()
    _test_tabs_impl()
    _dbg("=" * 50)
    _dbg("TEST ALL COMPLETE")


def test_all():
    _enqueue(_test_all_impl)


# ═══════════════════════════════════════════════════════════════════
# Clean
# ═══════════════════════════════════════════════════════════════════

def _clean_impl():
    from Py4GWCoreLib import UIManager
    frames = list(UIManager.GetFrameArray())
    destroyed = 0
    for fid in frames:
        try:
            title = PyUIManager.UIManager.get_frame_title_by_frame_id(fid) or ""
            if any(kw in title for kw in ["Dropdown Test", "Slider Test",
                                            "EditableText Test", "ProgressBar Test",
                                            "Tabs Test"]):
                PyUIManager.UIManager.destroy_ui_component_by_frame_id(fid)
                destroyed += 1
                _dbg(f"Destroyed {title} (fid={fid})")
        except Exception:
            pass
    _dbg(f"Clean complete: {destroyed} windows destroyed")
    controls.clear()


def clean_all():
    _enqueue(_clean_impl)


# ═══════════════════════════════════════════════════════════════════
# PyImGui UI (buttons only — no debug on screen)
# ═══════════════════════════════════════════════════════════════════

def main():
    if not PyImGui.begin("Tier1 Controls"):
        return

    PyImGui.text("Tier 1 UI Control Tests — console for output")

    # Check if bindings exist
    um = PyUIManager.UIManager
    try:
        _ = um.create_dropdown_frame_by_frame_id
        _ = um.create_slider_frame_by_frame_id
        _ = um.create_editable_text_frame_by_frame_id
        _ = um.create_progress_bar_by_frame_id
        _ = um.create_tabs_frame_by_frame_id
        PyImGui.text_colored("Bindings: OK", (0.3, 1.0, 0.3, 1.0))
    except AttributeError:
        PyImGui.text_colored("Bindings: NOT FOUND — rebuild DLL", (1.0, 0.3, 0.3, 1.0))
        PyImGui.text("cmake -B build -A Win32")
        PyImGui.text("cmake --build build --config Release")
        PyImGui.end()
        return

    PyImGui.separator()

    if PyImGui.button("Test Dropdown"):
        test_dropdown()
    PyImGui.same_line(0, -1)
    PyImGui.text(f"fid={controls.get('Dropdown', '-')}")

    if PyImGui.button("Test Slider"):
        test_slider()
    PyImGui.same_line(0, -1)
    PyImGui.text(f"fid={controls.get('Slider', '-')}")

    if PyImGui.button("Test EditableText"):
        test_editable_text()
    PyImGui.same_line(0, -1)
    PyImGui.text(f"fid={controls.get('EditableText', '-')}")

    if PyImGui.button("Test ProgressBar"):
        test_progress_bar()
    PyImGui.same_line(0, -1)
    PyImGui.text(f"fid={controls.get('ProgressBar', '-')}")

    if PyImGui.button("Test Tabs"):
        test_tabs()
    PyImGui.same_line(0, -1)
    PyImGui.text(f"fid={controls.get('Tabs', '-')}")

    PyImGui.separator()

    if PyImGui.button("Test ALL"):
        test_all()

    PyImGui.same_line(0, -1)

    if PyImGui.button("Clean All"):
        clean_all()

    PyImGui.end()


if __name__ == "__main__":
    main()
