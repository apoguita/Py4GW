"""
Window Title V3 — test all three vectors (2026-06-03)
Requires rebuilt DLL with Window-Polish C++ changes (FrameSetLayer, FrameSetPosition).
Chrome offsets verified against CRProc disassembly (05-30-2026 EXE):
  Title bar = 20 px, Left/Right border = 32 px, Bottom border = 32 px.

Y-inversion restored (Phase 3.5): CRect::BuildRect inverts Y during rendering,
so engine coords use bottom-left origin. _to_engine_coords() encapsulates this.
"""
import PyImGui, PyUIManager
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

# Legacy offsets (kept as reference):
WINDOW_OFFSET_X = 30  # old (~32)
WINDOW_OFFSET_Y = 60  # old (~52)
BORDER_X = 20          # old (~32)
BORDER_Y = 15          # old (~32)

_window_layer_counter = 0


def _get_viewport_height() -> float:
    """Returns viewport height (used for Y-inversion)."""
    root_frame_id = UIManager.GetRootFrameID()
    _, viewport_height = UIManager.GetViewportDimensions(root_frame_id)
    return float(viewport_height)


def _to_engine_y_from_top(y_from_top: float, height: float) -> float:
    """Convert screen-top Y to engine (bottom-left) Y, accounting for bottom chrome."""
    return _get_viewport_height() - float(y_from_top) - float(height) - BOTTOM_BORDER


def _to_engine_coords(content_x, content_y, content_w, content_h):
    """Convert screen coords (top-left origin) to engine coords (bottom-left origin).
    
    CRect stores position in top-left convention but BuildRect inverts Y during
    rendering. Engine coords must pre-invert to compensate for BuildRect's inversion.
    
    Borders are POSITIONAL OFFSETS only — the frame size is the requested content size.
    Chrome (title bar, borders) renders OUTSIDE the frame CRect.
    """
    engine_x = content_x - LEFT_BORDER
    # Content within frame starts at frame_top + TOP_TITLE.
    # In bottom-left: engine_y must place frame_top TOP_TITLE above desired content_y.
    # After BuildRect: screen(frame_top) = viewport_h - engine_y - content_h
    #   content_screen_y = screen(frame_top) + TOP_TITLE = viewport_h - engine_y - h + TOP_TITLE
    #   Set equal to content_y: engine_y = viewport_h - content_y - content_h + TOP_TITLE
    engine_y = _get_viewport_height() - content_y - content_h + TOP_TITLE
    return engine_x, engine_y, content_w, content_h  # size = content, no border addition


def test_c_create():
    global fid_a, TITLE, _window_layer_counter

    engine_x, engine_y, frame_w, frame_h = _to_engine_coords(
        COORDS[0], COORDS[1], SIZE[0], SIZE[1]
    )

    _window_layer_counter += 1
    layer = _window_layer_counter

    fid_a = PyUIManager.UIManager.CreateNativeWindow(
        engine_x, engine_y, frame_w, frame_h, TITLE,
        9,          # parent_frame_id
        0,          # child_index
        0x20,       # frame_flags (bit 0x20 = popup — enables click-to-raise)
        0x20,       # create_param
        0x6,        # anchor_flags
        0x59,       # subclass_flags
        layer,      # z-order layer (unique per window)
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

    # Show computed engine coords (bottom-left origin, including chrome)
    eng_x, eng_y, frm_w, frm_h = _to_engine_coords(_x, _y, _w, _h)
    PyImGui.text(f"Engine coords: ({eng_x:.0f}, {eng_y:.0f})  frame: {frm_w:.0f}x{frm_h:.0f}")
    PyImGui.text(f"Viewport: {_get_viewport_height():.0f}")

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
