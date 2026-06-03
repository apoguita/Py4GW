"""
Window Title V3 — test all three vectors (2026-06-02)
Requires rebuilt DLL with Vector B/C/A C++ changes.
"""
import PyImGui, PyUIManager
from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI

fid_a, fid_b, fid_d = 0, 0, 0
TITLE = "V3 Test"

def _ex(fid):
    return fid > 0 and int(fid) in set(int(x) for x in UIManager.GetFrameArray())

def _caps(fid):
    try:
        t = PyUIManager.UIManager.get_frame_text_caption_text(fid) or ""
        r = PyUIManager.UIManager.get_frame_resource_caption_text(fid) or ""
        return t, r
    except:
        return "?", "?"

def _mask(fid):
    try:
        base = PyUIManager.UIManager.get_frame_base_address(fid)
        import ctypes
        return ctypes.c_uint32.from_address(base + 0x18).value if base else 0
    except:
        return 0

# ── Vector B: Clone Hook ────────────────────────────────────────

def test_b():
    global fid_b
    if fid_b and _ex(fid_b): GWUI.DestroyUIComponentByFrameId(fid_b); fid_b = 0

    print("─── B: Clone Hook ───")
    PyUIManager.UIManager.set_next_created_window_title(TITLE)
    print(f"B: armed title='{TITLE}'")

    fid_b = GWUI.CreateWindow(150, 500, 400, 300, "V3_B", ensure_devtext_source=True) or 0
    if not fid_b:
        print("B: CreateWindow FAILED")
        return

    # ClearWindowContentsByFrameId is already called inside CreateWindow;
    # calling it again would enqueue a second recursive clear on the same
    # frame, causing a crash when the duplicate lambda executes on children
    # that were already destroyed. The redraw is also handled internally.
    mask = _mask(fid_b)
    t, r = _caps(fid_b)
    print(f"B: fid={fid_b} mask=0x{mask:08X} text_caption='{t}' resource='{r}'")
    if t and t != "DlgDevText":
        print(f"B: ★ HOOK WORKED — title='{t}'")
    elif t == "DlgDevText":
        print("B: ✗ Title still 'DlgDevText' — hook did not fire (rebuild DLL?)")
    else:
        print("B: ? Title empty — hook may have fired but text cleared")

# ── Vector A: DialogShow ────────────────────────────────────────

def test_a():
    global fid_d
    if fid_d and _ex(fid_d): GWUI.DestroyUIComponentByFrameId(fid_d); fid_d = 0

    print("─── A: DialogShow ───")
    fid_d = PyUIManager.UIManager.create_dialog_with_title(9, TITLE) or 0
    if fid_d:
        mask = _mask(fid_d)
        t, r = _caps(fid_d)
        print(f"A: fid={fid_d} mask=0x{mask:08X} text_caption='{t}' resource='{r}'")
        print(f"A: ★ Created with title='{t}'" if t == TITLE else f"A: title mismatch: '{t}' vs '{TITLE}'")
    else:
        print("A: create_dialog_with_title returned 0 — hook may not be installed")

# ── Vector C: msg 0x5E ──────────────────────────────────────────

def test_c_create():
    global fid_a
    if fid_a and _ex(fid_a): GWUI.DestroyUIComponentByFrameId(fid_a); fid_a = 0
    print("─── C: Create Container ───")
    fid_a = PyUIManager.UIManager.create_titled_container_window(
        500, 500, 400, 300, "V3_C", 9, 0, 0x20, 0x6, 0x59) or 0
    mask = _mask(fid_a)
    t, r = _caps(fid_a)
    print(f"C: fid={fid_a} mask=0x{mask:08X} text='{t}' resource='{r}'")

def test_c_msg():
    global fid_a
    if not (fid_a and _ex(fid_a)):
        print("C: no container — click Create first")
        return
    print(f"─── C: msg 0x5E ───")
    pre_t, _ = _caps(fid_a)
    print(f"C: PRE  text='{pre_t}'")
    ok = PyUIManager.UIManager.send_title_msg_5e(fid_a, TITLE)
    print(f"C: send_title_msg_5e → {'OK' if ok else 'FAILED'}")
    post_t, _ = _caps(fid_a)
    print(f"C: POST text='{post_t}'")
    print(f"C: ★ Title set!" if post_t == TITLE else f"C: ✗ Title mismatch: '{post_t}'")

# ── UI ──────────────────────────────────────────────────────────

def main():
    global fid_a, fid_b, fid_d, TITLE

    if not PyImGui.begin("Py4GW"):
        return

    TITLE = PyImGui.input_text("##t", TITLE, 0)

    if PyImGui.button("B: Clone Hook"): test_b()
    PyImGui.same_line(0,-1)
    PyImGui.text(f"fid_b={fid_b}")

    if PyImGui.button("A: DialogShow"): test_a()
    PyImGui.same_line(0,-1)
    PyImGui.text(f"fid_d={fid_d}")

    if PyImGui.button("C: Create"): test_c_create()
    PyImGui.same_line(0,-1)
    if PyImGui.button("C: msg 0x5E"): test_c_msg()
    PyImGui.same_line(0,-1)
    PyImGui.text(f"fid_a={fid_a}")

    PyImGui.end()

if __name__ == "__main__":
    main()
