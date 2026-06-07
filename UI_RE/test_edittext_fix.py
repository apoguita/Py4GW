"""
EditableTextFrame Fix Test (2026-06-05)
========================================
Tests the corrected EditableTextFrame creation protocol:
  1. Use component_flags=0 (ZERO), not 0x300.
  2. Correct struct layout (CCtlEdit 0x90 bytes, auto-allocated by msg 0x09).

Phase 3 crash causes:
  - Wrong component_flags (0x300 instead of 0)
  - Wrong struct layout assumptions

All native calls go through Game.enqueue() — game thread safe.
All output via print() to Py4GW console.
"""
import Py4GW
import PyUIManager

# ── State ─────────────────────────────────────────────────────────
window_id = 0
edit_id = 0


def _dbg(msg: str) -> None:
    print(f"[EditTextFix] {msg}")


def _enqueue(fn):
    Py4GW.Game.enqueue(fn)


# ── Creation (flags=0 per real game protocol) ─────────────────────

def _create_impl():
    global window_id, edit_id

    um = PyUIManager.UIManager
    _dbg("═══ EditableTextFrame Fix Test ═══")

    # 1. Create container window
    window_id = int(um.CreateNativeWindow(70, 120, 400, 200, "EditableText Fix Test") or 0)
    if not window_id:
        _dbg("FAIL: CreateNativeWindow returned 0")
        return
    _dbg(f"Container window: fid={window_id}")

    # 2. Create editable text with flags=0 (NOT 0x300!)
    try:
        edit_id = int(um.create_editable_text_frame_by_frame_id(
            window_id, 0, 0, "TestEdit"  # flags=0
        ) or 0)
    except AttributeError:
        _dbg("ERROR: create_editable_text_frame_by_frame_id not found — rebuild DLL")
        return
    if not edit_id:
        _dbg("FAIL: Create returned 0 (flags=0)")
        return
    _dbg(f"EditableText created: fid={edit_id} (flags=0)")

    # 3. Post-create: SetMaxLength
    ok = um.set_editable_text_max_length_by_frame_id(edit_id, 256)
    _dbg(f"SetMaxLength(256): {ok}")

    # 4. Post-create: SetReadOnly
    ok = um.set_editable_text_read_only_by_frame_id(edit_id, False)
    _dbg(f"SetReadOnly(False): {ok}")

    # 5. Post-create: Set prompt text (watermark)
    ok = um.set_editable_text_value_by_frame_id(edit_id, "Type here...")
    _dbg(f"SetValue('Type here...'): {ok}")

    # 6. Verify: GetValue
    val = um.get_editable_text_value_by_frame_id(edit_id)
    expected = "Type here..."
    passed = val == expected
    _dbg(f"GetValue(): '{val}' {'PASS' if passed else f'FAIL expected \"{expected}\"'}")

    _dbg("═══ EditTextFix complete ═══")


def test_create():
    _enqueue(_create_impl)


# ── Cleanup ────────────────────────────────────────────────────────

def _clean_impl():
    global window_id, edit_id
    from Py4GWCoreLib import UIManager

    destroyed = 0
    frames = list(UIManager.GetFrameArray())
    for fid in frames:
        try:
            title = PyUIManager.UIManager.get_frame_title_by_frame_id(fid) or ""
            if "EditableText Fix Test" in title:
                PyUIManager.UIManager.destroy_ui_component_by_frame_id(fid)
                destroyed += 1
                _dbg(f"Destroyed {title} (fid={fid})")
        except Exception:
            pass
    _dbg(f"Cleanup: {destroyed} windows destroyed")
    window_id = 0
    edit_id = 0


def clean():
    _enqueue(_clean_impl)


# ── Main ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_create()
