"""
Native window creation POC.

CreateWindow now accepts content-space pixel bounds directly and handles
chrome expansion, viewport scaling, and Y inversion internally in the C++ layer.
"""
import PyImGui
from Py4GWCoreLib import Overlay, UIManager
from Py4GWCoreLib.GWUI import GWUI

COORDS: tuple[int, int] = (100, 250)
SIZE = (200, 250)
TITLE = "V3 Test"
draw_window_target = True
draw_window_border = True

# Chrome dimensions — verified from CRProc disassembly (subclass 0x59, bit 9 NOT set):
LEFT_BORDER   = 32   # left chrome border
TOP_TITLE     = 20   # title bar height
RIGHT_BORDER  = 32   # right chrome border
BOTTOM_BORDER = 32   # bottom chrome border

def _get_pixel_viewport() -> tuple[float, float]:
    """Get pixel dimensions of DirectX render target (same space as Overlay)."""
    display = Overlay().GetDisplaySize()
    return float(display.x), float(display.y)


def test_c_create():
    global fid_a, TITLE

    fid_a = GWUI.CreateWindow(
        COORDS[0],
        COORDS[1],
        SIZE[0],
        SIZE[1],
        TITLE,
    ) or 0

# ── UI ──────────────────────────────────────────────────────────

def main():
    global COORDS, SIZE, TITLE, draw_window_target, draw_window_border

    if not PyImGui.begin("Py4GW"):
        return

    TITLE = PyImGui.input_text("##t", TITLE, 0)
    
    PyImGui.text("Content Coords (screen top-left):")
    _x, _y = COORDS
    _x = PyImGui.input_int("x:", _x)
    _y = PyImGui.input_int("y:", _y)
    COORDS = (_x, _y)  
    
    PyImGui.text("Content Size:")
    _w, _h = SIZE
    _w = PyImGui.input_int("w:", _w)
    _h = PyImGui.input_int("h:", _h)
    SIZE = (_w, _h)

    draw_window_target = PyImGui.checkbox("Draw Content Quad (green)", draw_window_target)
    draw_window_border = PyImGui.checkbox("Draw Frame Quad (magenta)", draw_window_border)
    if PyImGui.button("C: Create"): 
        test_c_create()

    PyImGui.end()
    
    # Green quad = content area (screen top-left coords)
    if draw_window_target:
        Overlay().BeginDraw()
        _x, _y = COORDS
        _w, _h = SIZE
        Overlay().DrawQuad(
            _x, _y,
            _x + _w, _y,
            _x + _w, _y + _h,
            _x, _y + _h,
        )
        Overlay().EndDraw()
        
    # Magenta quad = full frame including chrome (screen top-left coords)
    if draw_window_border:
        Overlay().BeginDraw()
        _x, _y = COORDS
        _w, _h = SIZE
        frame_left   = _x - LEFT_BORDER
        frame_top    = _y - TOP_TITLE
        frame_right  = _x + _w + RIGHT_BORDER
        frame_bottom = _y + _h + BOTTOM_BORDER
        Overlay().DrawQuad(
            frame_left,  frame_top,
            frame_right, frame_top,
            frame_right, frame_bottom,
            frame_left,  frame_bottom,
            color=0xFFFF00FF,
            thickness=2.0,
        )
        Overlay().EndDraw()        
        

if __name__ == "__main__":
    main()
