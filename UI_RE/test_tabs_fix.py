"""
TabsFrame Fix Test (2026-06-05)
================================
Tests the corrected TabsFrame (CtlPage) creation protocol:
  1. Use component_flags=0x40000, not 0x300.
  2. Correct struct size: 8 bytes (frame_id + active_index), not 16.

Phase 3 crash causes:
  - Wrong component_flags (0x300 instead of 0x40000)
  - Wrong struct size caused heap corruption

The 0x40000 flag is REQUIRED: AddTab checks FrameTestStyles(frame, 0x2000)
and FrameTestStyles(frame, 0x4000). Without it, layout calculations crash.

All native calls go through Game.enqueue() — game thread safe.
All output via print() to Py4GW console.
"""
import Py4GW
import PyUIManager

# ── State ─────────────────────────────────────────────────────────
window_id = 0
tabs_id = 0


def _dbg(msg: str) -> None:
    print(f"[TabsFix] {msg}")


def _enqueue(fn):
    Py4GW.Game.enqueue(fn)


# ── Creation (flags=0x40000 per real game protocol) ────────────────

def _create_impl():
    global window_id, tabs_id

    um = PyUIManager.UIManager
    _dbg("═══ TabsFrame Fix Test ═══")

    # 1. Create container window (wider to fit tabs)
    window_id = int(um.CreateNativeWindow(90, 140, 500, 300, "Tabs Fix Test") or 0)
    if not window_id:
        _dbg("FAIL: CreateNativeWindow returned 0")
        return
    _dbg(f"Container window: fid={window_id}")

    # 2. Create tabs frame with flags=0x40000 (NOT 0x300!)
    try:
        tabs_id = int(um.create_tabs_frame_by_frame_id(
            window_id, 0x40000, 0, "TestTabs"  # flags=0x40000
        ) or 0)
    except AttributeError:
        _dbg("ERROR: create_tabs_frame_by_frame_id not found — rebuild DLL")
        return
    if not tabs_id:
        _dbg("FAIL: Create returned 0 (flags=0x40000)")
        return
    _dbg(f"TabsFrame created: fid={tabs_id} (flags=0x40000)")

    # 3. Post-create: AddTab (creates content page + tab button internally)
    t1 = int(um.add_tab_by_frame_id(tabs_id, "Tab One", 0x300, 0, 0, 0) or 0)
    _dbg(f"AddTab('Tab One') → fid={t1}")

    t2 = int(um.add_tab_by_frame_id(tabs_id, "Tab Two", 0x300, 1, 0, 0) or 0)
    _dbg(f"AddTab('Tab Two') → fid={t2}")

    t3 = int(um.add_tab_by_frame_id(tabs_id, "Tab Three", 0x300, 2, 0, 0) or 0)
    _dbg(f"AddTab('Tab Three') → fid={t3}")

    # 4. Post-create: ChooseTab (select first tab)
    ok = um.choose_tab_by_index_by_frame_id(tabs_id, 0)
    _dbg(f"ChooseTab(0): {ok}")

    # 5. Verify: GetCurrentTabIndex
    cur = um.get_current_tab_index_by_frame_id(tabs_id)
    expected = 0
    passed = cur == expected
    _dbg(f"GetCurrentTabIndex(): {cur} {'PASS' if passed else f'FAIL expected {expected}'}")

    _dbg("═══ TabsFix complete ═══")


def test_create():
    _enqueue(_create_impl)


# ── Cleanup ────────────────────────────────────────────────────────

def _clean_impl():
    global window_id, tabs_id
    from Py4GWCoreLib import UIManager

    destroyed = 0
    frames = list(UIManager.GetFrameArray())
    for fid in frames:
        try:
            title = PyUIManager.UIManager.get_frame_title_by_frame_id(fid) or ""
            if "Tabs Fix Test" in title:
                PyUIManager.UIManager.destroy_ui_component_by_frame_id(fid)
                destroyed += 1
                _dbg(f"Destroyed {title} (fid={fid})")
        except Exception:
            pass
    _dbg(f"Cleanup: {destroyed} windows destroyed")
    window_id = 0
    tabs_id = 0


def clean():
    _enqueue(_clean_impl)


# ── Main ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_create()
