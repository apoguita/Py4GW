"""
Window Title V3 — test all three vectors (2026-06-02)
Requires rebuilt DLL with Vector B/C/A C++ changes.
"""
import PyImGui, PyUIManager
from Py4GWCoreLib import Overlay, UIManager
from Py4GWCoreLib.GWUI import GWUI

COORDS: tuple[int, int] = (100, 250)
SIZE = (200, 250)
TITLE = "V3 Test"
draw_window_target = True
draw_window_border = True

BORDER_X = 20
BORDER_Y = 15
TITLE_Y_OFFSET = 20


def _get_viewport_height() -> float:
    root_frame_id = UIManager.GetRootFrameID()
    _, viewport_height = UIManager.GetViewportDimensions(root_frame_id)
    return float(viewport_height)


def _to_engine_y_from_top(y_from_top: float, height: float) -> float:
    return _get_viewport_height() - float(y_from_top) - float(height)


def test_c_create():
    global fid_a, TITLE
    engine_y = _to_engine_y_from_top(COORDS[1], SIZE[1])
    fid_a = PyUIManager.UIManager.CreateNativeWindow(
        COORDS[0], engine_y, SIZE[0], SIZE[1], TITLE, 9, 0, 0, 0x20, 0x6, 0x59
    ) or 0

# ── UI ──────────────────────────────────────────────────────────

def main():
    global COORDS, SIZE, TITLE, draw_window_target, draw_window_border

    if not PyImGui.begin("Py4GW"):
        return

    TITLE = PyImGui.input_text("##t", TITLE, 0)
    
    PyImGui.text("Coords From Top:")
    _x, _y = COORDS
    _x = PyImGui.input_int("x:", _x)
    _y = PyImGui.input_int("y:", _y)
    COORDS = (_x, _y)  
    
    PyImGui.text("Size:")
    _w, _h = SIZE
    _w = PyImGui.input_int("w:", _w)
    _h = PyImGui.input_int("h:", _h)
    SIZE = (_w, _h) 

    PyImGui.text(f"Engine y: {_to_engine_y_from_top(COORDS[1], SIZE[1]):.1f}")

    draw_window_target = PyImGui.checkbox("Draw Window Target", draw_window_target)
    draw_window_border = PyImGui.checkbox("Draw Window Border", draw_window_border)
    if PyImGui.button("C: Create"): 
        test_c_create()


    PyImGui.end()
    
    if draw_window_target:
        Overlay().BeginDraw()
        _x, _y = COORDS
        _w, _h = SIZE
        
        Overlay().DrawQuad (
            _x, _y, 
            _x + _w, _y,
            _x + _w, _y + _h,
            _x, _y + _h,
        )
        
        Overlay().EndDraw()
        
    if draw_window_border:
        Overlay().BeginDraw()
        _x, _y = COORDS
        _w, _h = SIZE
        bx = BORDER_X
        by = BORDER_Y
        
        Overlay().DrawQuad (
            _x - bx, _y - by - TITLE_Y_OFFSET, 
            _x + _w + bx, _y - by - TITLE_Y_OFFSET,
            _x + _w + bx, _y + _h + by,
            _x - bx, _y + _h + by,
            color=0xFFFF00FF,
            thickness=2.0
        )
        
        Overlay().EndDraw()        
        

if __name__ == "__main__":
    main()
