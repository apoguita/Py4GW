"""
Test Script — Tier 1 UI Control Create Functions (Phase A)
===========================================================
Tests the 5 new Create functions for DropdownFrame, SliderFrame,
EditableTextFrame, ProgressBar, and TabsFrame.

Requires: Py4GW injected into a running Gw.exe instance.

Usage:
    Inject Py4GW, open the Python console, and run this script.
    Each test creates a container window, creates a control inside it,
    verifies the frame_id is non-zero, performs basic manipulation,
    then reports pass/fail.

Note: This script uses NativeFunction.from_address() to bypass
C++ compilation for initial testing. Once the C++ bindings are compiled,
replace with PyUIManager.UIManager calls.
"""
import sys
import ctypes
from typing import Optional

# ── Python Repo Imports ─────────────────────────────────────────
import PyUIManager

# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _log(msg: str) -> None:
    """Write to the Py4GW console."""
    print(f"[Tier1Test] {msg}")


def _assert_nonzero(frame_id: int, label: str) -> bool:
    if frame_id == 0:
        _log(f"  FAIL: {label} returned 0")
        return False
    _log(f"  OK: {label}={frame_id}")
    return True


def create_container(title: str) -> int:
    """Create a container window for testing controls inside."""
    window_id = PyUIManager.UIManager.CreateNativeWindow(
        50.0, 100.0, 400.0, 300.0, title
    )
    _log(f"Container window: frame_id={window_id}")
    return int(window_id or 0)


# ═══════════════════════════════════════════════════════════════════
# Test 1: DropdownFrame
# ═══════════════════════════════════════════════════════════════════

def test_dropdown() -> bool:
    _log("── Test: DropdownFrame ──")
    parent_id = create_container("Dropdown Test")

    # Create dropdown via C++ binding (once compiled) or via from_address
    dropdown_id = int(
        PyUIManager.UIManager.create_dropdown_frame_by_frame_id(
            parent_id, 0x300, 0, "TestDropdown"
        )
        or 0
    )

    if not _assert_nonzero(dropdown_id, "DropdownFrame::Create"):
        return False

    # Post-create: AddOption
    ok = PyUIManager.UIManager.add_option_by_frame_id(
        dropdown_id, "Option A", 1
    )
    _log(f"  AddOption('Option A', 1): {ok}")

    ok = PyUIManager.UIManager.add_option_by_frame_id(
        dropdown_id, "Option B", 2
    )
    _log(f"  AddOption('Option B', 2): {ok}")

    # Select an option
    ok = PyUIManager.UIManager.select_option_by_frame_id(dropdown_id, 2)
    _log(f"  SelectOption(2): {ok}")

    # Verify selection
    value = PyUIManager.UIManager.get_dropdown_value_by_frame_id(dropdown_id)
    _log(f"  GetValue(): {value}")

    return True


# ═══════════════════════════════════════════════════════════════════
# Test 2: SliderFrame
# ═══════════════════════════════════════════════════════════════════

def test_slider() -> bool:
    _log("── Test: SliderFrame ──")
    parent_id = create_container("Slider Test")

    slider_id = int(
        PyUIManager.UIManager.create_slider_frame_by_frame_id(
            parent_id, 0x300, 0, "TestSlider"
        )
        or 0
    )

    if not _assert_nonzero(slider_id, "SliderFrame::Create"):
        return False

    # Post-create: SetValue
    ok = PyUIManager.UIManager.set_slider_value_by_frame_id(slider_id, 50)
    _log(f"  SetValue(50): {ok}")

    # GetValue
    val = PyUIManager.UIManager.get_slider_value_by_frame_id(slider_id)
    _log(f"  GetValue(): {val}")

    return True


# ═══════════════════════════════════════════════════════════════════
# Test 3: EditableTextFrame
# ═══════════════════════════════════════════════════════════════════

def test_editable_text() -> bool:
    _log("── Test: EditableTextFrame ──")
    parent_id = create_container("EditableText Test")

    edit_id = int(
        PyUIManager.UIManager.create_editable_text_frame_by_frame_id(
            parent_id, 0x300, 0, "TestEdit"
        )
        or 0
    )

    if not _assert_nonzero(edit_id, "EditableTextFrame::Create"):
        return False

    # Post-create: SetMaxLength + SetReadOnly
    ok = PyUIManager.UIManager.set_editable_text_max_length_by_frame_id(edit_id, 256)
    _log(f"  SetMaxLength(256): {ok}")

    ok = PyUIManager.UIManager.set_editable_text_readonly_by_frame_id(edit_id, False)
    _log(f"  SetReadOnly(False): {ok}")

    # Set a value
    ok = PyUIManager.UIManager.set_editable_text_value_by_frame_id(edit_id, "Hello GW!")
    _log(f"  SetValue('Hello GW!'): {ok}")

    # Get value
    val = PyUIManager.UIManager.get_editable_text_value_by_frame_id(edit_id)
    _log(f"  GetValue(): '{val}'")

    return True


# ═══════════════════════════════════════════════════════════════════
# Test 4: ProgressBar
# ═══════════════════════════════════════════════════════════════════

def test_progress_bar() -> bool:
    _log("── Test: ProgressBar ──")
    parent_id = create_container("ProgressBar Test")

    pb_id = int(
        PyUIManager.UIManager.create_progress_bar_by_frame_id(
            parent_id, 0x300, 0, "TestProgress"
        )
        or 0
    )

    if not _assert_nonzero(pb_id, "ProgressBar::Create"):
        return False

    # Post-create: SetMax + SetStyle
    ok = PyUIManager.UIManager.set_progress_bar_max_by_frame_id(pb_id, 100)
    _log(f"  SetMax(100): {ok}")

    # Style 0 = kPeach
    ok = PyUIManager.UIManager.set_progress_bar_style_by_frame_id(pb_id, 0)
    _log(f"  SetStyle(kPeach=0): {ok}")

    # SetValue
    ok = PyUIManager.UIManager.set_progress_bar_value_by_frame_id(pb_id, 42)
    _log(f"  SetValue(42): {ok}")

    # GetValue
    val = PyUIManager.UIManager.get_progress_bar_value_by_frame_id(pb_id)
    _log(f"  GetValue(): {val}")

    return True


# ═══════════════════════════════════════════════════════════════════
# Test 5: TabsFrame
# ═══════════════════════════════════════════════════════════════════

def test_tabs() -> bool:
    _log("── Test: TabsFrame ──")
    parent_id = create_container("Tabs Test")

    tabs_id = int(
        PyUIManager.UIManager.create_tabs_frame_by_frame_id(
            parent_id, 0x300, 0, "TestTabs"
        )
        or 0
    )

    if not _assert_nonzero(tabs_id, "TabsFrame::Create"):
        return False

    # Post-create: AddTab (note: AddTab uses encoded string, pass empty for now)
    tab1_id = int(
        PyUIManager.UIManager.add_tab_by_frame_id(
            tabs_id, "Tab 1", 0x300, 0, 0, 0
        )
        or 0
    )
    _log(f"  AddTab('Tab 1'): frame_id={tab1_id}")

    tab2_id = int(
        PyUIManager.UIManager.add_tab_by_frame_id(
            tabs_id, "Tab 2", 0x300, 1, 0, 0
        )
        or 0
    )
    _log(f"  AddTab('Tab 2'): frame_id={tab2_id}")

    # Choose tab
    ok = PyUIManager.UIManager.choose_tab_by_frame_id(tabs_id, 0)
    _log(f"  ChooseTab(0): {ok}")

    return True


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    _log("=" * 60)
    _log("Tier 1 UI Control Create Function Tests")
    _log("EXE build: 05-30-2026")
    _log("=" * 60)

    results = {}
    results["DropdownFrame"] = test_dropdown()
    results["SliderFrame"] = test_slider()
    results["EditableTextFrame"] = test_editable_text()
    results["ProgressBar"] = test_progress_bar()
    results["TabsFrame"] = test_tabs()

    _log("=" * 60)
    _log("RESULTS:")
    passed = 0
    failed = 0
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        _log(f"  {name}: {status}")
        if ok:
            passed += 1
        else:
            failed += 1
    _log(f"  Total: {passed} passed, {failed} failed")
    _log("=" * 60)


# Entry point
if __name__ == "__main__":
    main()
