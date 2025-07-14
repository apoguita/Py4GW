import Py4GW
from Py4GWCoreLib import *
import webbrowser

MODULE_NAME = "GwFake Window Test"
TEXTURE_FOLDER = "Textures\\Game UI\\"
FRAME_ATLAS = "ui_window_frame_atlas.png"
FRAME_ATLAS_DIMENSIONS = (128,128)
TITLE_ATLAS = "ui_window_title_frame_atlas.png"
TITLE_ATLAS_DIMENSIONS = (128, 32)
CLOSE_BUTTON_ATLAS = "close_button.png"

LOWER_BORDER_PIXEL_MAP = (11,110,78,128)
LOWER_RIGHT_CORNER_TAB_PIXEL_MAP = (78,110,117,128)

# Pixel maps for title bar
LEFT_TITLE_PIXEL_MAP = (0,0,18,32)
RIGHT_TITLE_PIXEL_MAP = (110,0,128,32)
TITLE_AREA_PIXEL_MAP = (19,0,109,32)

# Pixel maps for LEFT side
UPPER_LEFT_TAB_PIXEL_MAP = (0,0,17,35)
LEFT_BORDER_PIXEL_MAP = (0,36,17,74)
LOWER_LEFT_TAB_PIXEL_MAP = (0,75,11,110)
LOWER_LEFT_CORNER_PIXEL_MAP = (0,110,11,128)

# Pixel maps for RIGHT side
UPPER_RIGHT_TAB_PIXEL_MAP = (113,0,128,35)
RIGHT_BORDER_PIXEL_MAP = (111,36,128,74)
LOWER_RIGHT_TAB_PIXEL_MAP = (117,75,128,110)
LOWER_RIGHT_CORNER_PIXEL_MAP = (117,110,128,128)

CLOSE_BUTTON_PIXEL_MAP = (0, 0, 15,15)
CLOSE_BUTTON_HOVERED_PIXEL_MAP = (16, 0, 31, 15)

window_size = (300, 200)
window_pos = {"X": 500.0, "Y": 500.0}
first_run = True
collapsed = False

pixel_origin = [0, 0]
pixel_ending = [128, 128]

set_pos_dragging = False
      
def draw_region_in_drawlist(x: float, y: float,
                            width: int, height: int,
                            pixel_map: tuple[int, int, int, int],
                            texture_path: str,
                            atlas_dimensions: tuple[int, int],
                            tint: tuple[int, int, int, int] = (255, 255, 255, 255)):
    """
    Draws a region defined by pixel_map into the current window's draw list at (x, y).
    """
    x0, y0, x1, y1 = pixel_map
    _width = x1 - x0 if width == 0 else width
    _height = y1 - y0 if height == 0 else height
    
    source_width = x1 - x0
    source_height = y1 - y0

    uv0, uv1 = Utils.PixelsToUV(x0, y0, source_width, source_height, atlas_dimensions[0], atlas_dimensions[1])

    ImGui.DrawTextureInDrawList(
        pos=(x, y),
        size=(_width, _height),
        texture_path=texture_path,
        uv0=uv0,
        uv1=uv1,
        tint=tint
    )

        
def main():
    global MODULE_NAME, window_size, window_pos, first_run, collapsed
    
    if first_run:
        PyImGui.set_next_window_size(window_size[0], window_size[1])     
        PyImGui.set_next_window_pos(window_pos["X"], window_pos["Y"])
        first_run = False
        
    PyImGui.set_next_window_collapsed(collapsed, PyImGui.ImGuiCond.Always)
    
    if collapsed:
        flags = (PyImGui.WindowFlags.NoFlag)
    else:
        flags = (PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoBackground)
    
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0, 0)
  
    window_open = PyImGui.begin(MODULE_NAME, flags)
    collapsed = PyImGui.is_window_collapsed()
    
    if window_open:

        window_size = PyImGui.get_window_size()
        win_pos = PyImGui.get_window_pos()
        window_pos["X"] = win_pos[0]
        window_pos["Y"] = win_pos[1]
        
        left = window_pos["X"]
        right = window_pos["X"] + window_size[0]
        top = window_pos["Y"]
        bottom = window_pos["Y"] + window_size[1]
        window_width = int(window_size[0])
        window_height = int(window_size[1])
        
        
        #LEFT TITLE
        x0, y0, x1, y1 = LEFT_TITLE_PIXEL_MAP
        LT_width = x1 - x0
        LT_height = y1 - y0
        draw_region_in_drawlist(
            x=left,
            y=top-5,
            width=LT_width,
            height=LT_height,
            pixel_map=LEFT_TITLE_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + TITLE_ATLAS,
            atlas_dimensions=TITLE_ATLAS_DIMENSIONS,
            tint=(255, 255, 255, 255)
        )
        
        # RIGHT TITLE
        x0, y0, x1, y1 = RIGHT_TITLE_PIXEL_MAP
        rt_width = x1 - x0
        rt_height = y1 - y0
        draw_region_in_drawlist(
            x=right - rt_width,
            y=top - 5,
            width=rt_width,
            height=rt_height,
            pixel_map=RIGHT_TITLE_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + TITLE_ATLAS,
            atlas_dimensions=TITLE_ATLAS_DIMENSIONS
        )

        
        # CLOSE BUTTON
        x0, y0, x1, y1 = CLOSE_BUTTON_PIXEL_MAP
        cb_width = x1 - x0
        cb_height = y1 - y0

        x = right - cb_width - 13
        y = top + 8

        # Position the interactive region
        PyImGui.draw_list_add_rect(
            x,                    # x1
            y,                    # y1
            x + cb_width,         # x2
            y + cb_height,        # y2
            Color(255, 0, 0, 255).to_color(),  # col in ABGR
            0.0,                  # rounding
            0,                    # rounding_corners_flags
            1.0                   # thickness
        )

        PyImGui.set_cursor_screen_pos(x-1, y-1)
        if PyImGui.invisible_button("##close_button", cb_width+2, cb_height+2):
            collapsed = not collapsed
            PyImGui.set_window_collapsed(collapsed, PyImGui.ImGuiCond.Always)

        # Determine UV range based on state
        if PyImGui.is_item_active():
            uv0 = (0.666, 0.0)  # Pushed
            uv1 = (1.0, 1.0)
        elif PyImGui.is_item_hovered():
            uv0 = (0.333, 0.0)  # Hovered
            uv1 = (0.666, 1.0)
        else:
            uv0 = (0.0, 0.0)     # Normal
            uv1 = (0.333, 1.0)

        #Draw close button is done after the title bar
        
        #TITLE BAR
        x0, y0, x1, y1 = TITLE_AREA_PIXEL_MAP
        title_width = window_width - 36
        title_height = y1 - y0
        draw_region_in_drawlist(
            x=left + 18,
            y=top - 5,
            width=title_width,
            height=title_height,
            pixel_map=TITLE_AREA_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + TITLE_ATLAS,
            atlas_dimensions=TITLE_ATLAS_DIMENSIONS,
            tint=(255, 255, 255, 255)
        )
        
        # FLOATING BUTTON: Title bar behavior (drag + double-click collapse)
        titlebar_x = left + 18
        titlebar_y = top - 5
        titlebar_width = window_width - 36
        titlebar_height = title_height

        PyImGui.set_cursor_screen_pos(titlebar_x, titlebar_y)
        PyImGui.invisible_button("##titlebar_fake", titlebar_width, 32)

        # Handle dragging
        if PyImGui.is_item_active():
            delta = PyImGui.get_mouse_drag_delta(0, 0.0)
            new_window_pos = (window_pos["X"] + delta[0], window_pos["Y"] + delta[1])
            PyImGui.reset_mouse_drag_delta(0)
            PyImGui.set_window_pos(new_window_pos[0], new_window_pos[1], PyImGui.ImGuiCond.Always)

        # Handle double-click to collapse
        if PyImGui.is_item_hovered() and PyImGui.is_mouse_double_clicked(0):
            collapsed = not collapsed
            PyImGui.set_window_collapsed(collapsed, PyImGui.ImGuiCond.Always)
            
        # Draw CLOSE BUTTON in the title bar
        ImGui.DrawTextureInDrawList(
            pos=(x, y),
            size=(cb_width, cb_height),
            texture_path=TEXTURE_FOLDER + CLOSE_BUTTON_ATLAS,
            uv0=uv0,
            uv1=uv1,
            tint=(255, 255, 255, 255)
        )
        
        
        title_text = MODULE_NAME
        
        text_x = left + 32
        text_y = top + 10
        
        PyImGui.draw_list_add_text(
            text_x,
            text_y,
            Color(225, 225, 225, 225).to_color(),  # White text (ABGR)
            title_text
        )
        
    
        #LEFT UPPER TAB
        x0, y0, x1, y1 = UPPER_LEFT_TAB_PIXEL_MAP
        lut_tab_width = x1 - x0
        lut_tab_height = y1 - y0
        draw_region_in_drawlist(
            x=left,
            y=top + LT_height - 5,
            width= lut_tab_width,
            height= lut_tab_height,
            pixel_map=UPPER_LEFT_TAB_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            atlas_dimensions=FRAME_ATLAS_DIMENSIONS,
            tint=(255, 255, 255, 255)
        )
        
        #LEFT CORNER
        x0, y0, x1, y1 = LOWER_LEFT_CORNER_PIXEL_MAP
        lc_width = x1 - x0
        lc_height = y1 - y0
        draw_region_in_drawlist(
            x=left,
            y=bottom - lc_height,
            width= lc_width,
            height= lc_height,
            pixel_map=LOWER_LEFT_CORNER_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            atlas_dimensions=FRAME_ATLAS_DIMENSIONS,
            tint=(255, 255, 255, 255)
        )
        
        
        #LEFT LOWER TAB
        x0, y0, x1, y1 = LOWER_LEFT_TAB_PIXEL_MAP
        ll_tab_width = x1 - x0
        ll_tab_height = y1 - y0
        draw_region_in_drawlist(
            x=left,
            y=bottom - lc_height -ll_tab_height,
            width=ll_tab_width,
            height=ll_tab_height,
            pixel_map=LOWER_LEFT_TAB_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            atlas_dimensions=FRAME_ATLAS_DIMENSIONS,
            tint=(255, 255, 255, 255)
        )
        
        
        
        #LEFT BORDER
        x0, y0, x1, y1 = LEFT_BORDER_PIXEL_MAP
        left_border_width = x1 - x0
        left_border_height = y1 - y0
        draw_region_in_drawlist(
            x=left,
            y=top + LT_height - 5 + lut_tab_height,
            width= left_border_width,
            height= window_height - (LT_height + lut_tab_height + ll_tab_height + lc_height) +5,
            pixel_map=LEFT_BORDER_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            atlas_dimensions=FRAME_ATLAS_DIMENSIONS,
            tint=(255, 255, 255, 255)
        )
        

        # UPPER RIGHT TAB
        x0, y0, x1, y1 = UPPER_RIGHT_TAB_PIXEL_MAP
        urt_width = x1 - x0
        urt_height = y1 - y0
        draw_region_in_drawlist(
            x=right - urt_width,
            y=top + rt_height - 5,
            width=urt_width,
            height=urt_height,
            pixel_map=UPPER_RIGHT_TAB_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            atlas_dimensions=FRAME_ATLAS_DIMENSIONS
        )

        # LOWER RIGHT CORNER
        x0, y0, x1, y1 = LOWER_RIGHT_CORNER_PIXEL_MAP
        rc_width = x1 - x0
        rc_height = y1 - y0
        corner_x = right - rc_width
        corner_y = bottom - rc_height
        draw_region_in_drawlist(
            x=right - rc_width,
            y=bottom - rc_height,
            width=rc_width,
            height=rc_height,
            pixel_map=LOWER_RIGHT_CORNER_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            atlas_dimensions=FRAME_ATLAS_DIMENSIONS
        )
        # DRAG: Resize from corner
        PyImGui.set_cursor_screen_pos(corner_x-10, corner_y-10)
        PyImGui.invisible_button("##resize_corner", rc_width+10, rc_height+10)
        if PyImGui.is_item_active():
            delta = PyImGui.get_mouse_drag_delta(0, 0.0)
            new_window_size = (window_size[0] + delta[0], window_size[1] + delta[1])
            PyImGui.reset_mouse_drag_delta(0)
            PyImGui.set_window_size(new_window_size[0], new_window_size[1], PyImGui.ImGuiCond.Always)

        # LOWER RIGHT TAB
        x0, y0, x1, y1 = LOWER_RIGHT_TAB_PIXEL_MAP
        lrt_width = x1 - x0
        lrt_height = y1 - y0
        tab_x = right - lrt_width
        tab_y = bottom - rc_height - lrt_height
        draw_region_in_drawlist(
            x=right - lrt_width,
            y=bottom - rc_height - lrt_height,
            width=lrt_width,
            height=lrt_height,
            pixel_map=LOWER_RIGHT_TAB_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            atlas_dimensions=FRAME_ATLAS_DIMENSIONS
        )
        PyImGui.set_cursor_screen_pos(tab_x-10, tab_y)
        PyImGui.invisible_button("##resize_tab_above", lrt_width+10, lrt_height)
        if PyImGui.is_item_active():
            delta = PyImGui.get_mouse_drag_delta(0, 0.0)
            new_window_size = (window_size[0] + delta[0], window_size[1] + delta[1])
            PyImGui.reset_mouse_drag_delta(0)
            PyImGui.set_window_size(new_window_size[0], new_window_size[1], PyImGui.ImGuiCond.Always)

        # RIGHT BORDER
        x0, y0, x1, y1 = RIGHT_BORDER_PIXEL_MAP
        right_border_width = x1 - x0
        right_border_height = y1 - y0
        draw_region_in_drawlist(
            x=right - right_border_width,
            y=top + rt_height - 5 + urt_height,
            width=right_border_width,
            height=window_height - (rt_height + urt_height + lrt_height + rc_height) + 5,
            pixel_map=RIGHT_BORDER_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            atlas_dimensions=FRAME_ATLAS_DIMENSIONS
        )

        # Tab to the left of LOWER_RIGHT_CORNER
        x0, y0, x1, y1 = LOWER_RIGHT_CORNER_TAB_PIXEL_MAP
        tab_width = x1 - x0
        tab_height = y1 - y0
        
        tab_x = right - rc_width - tab_width
        tab_y = bottom - rc_height

        draw_region_in_drawlist(
            x=right - rc_width - tab_width,       # left of the corner
            y=bottom - rc_height,                 # same vertical alignment as corner
            width=tab_width,
            height=tab_height,
            pixel_map=LOWER_RIGHT_CORNER_TAB_PIXEL_MAP,
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            atlas_dimensions=FRAME_ATLAS_DIMENSIONS
        )
        
        # DRAG: Resize from left tab
        PyImGui.set_cursor_screen_pos(tab_x, tab_y-10)
        PyImGui.invisible_button("##resize_tab_left", tab_width, tab_height+10)
        PyImGui.set_item_allow_overlap()
        if PyImGui.is_item_active():
            delta = PyImGui.get_mouse_drag_delta(0,0.0)
            new_window_size = (window_size[0] + delta[0], window_size[1] + delta[1])
            PyImGui.reset_mouse_drag_delta(0)
            PyImGui.set_window_size(new_window_size[0], new_window_size[1], PyImGui.ImGuiCond.Always)
        
        x0, y0, x1, y1 = LOWER_BORDER_PIXEL_MAP
        border_tex_width = x1 - x0
        border_tex_height = y1 - y0
        border_start_x = left + lc_width
        border_end_x = right - rc_width - tab_width  # ← use the actual width of LOWER_RIGHT_CORNER_TAB
        border_draw_width = border_end_x - border_start_x

        uv0, uv1 = Utils.PixelsToUV(x0, y0, border_tex_width, border_tex_height,
                                    FRAME_ATLAS_DIMENSIONS[0], FRAME_ATLAS_DIMENSIONS[1])

        ImGui.DrawTextureInDrawList(
            pos=(border_start_x, bottom - border_tex_height),
            size=(border_draw_width, border_tex_height),
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            uv0=uv0,
            uv1=uv1,
            tint=(255, 255, 255, 255)
        )
        
        
        content_margin_top = title_height  # e.g. 32
        content_margin_left = lc_width     # left corner/border
        content_margin_right = rc_width    # right corner/border
        content_margin_bottom = border_tex_height  # bottom border height
        
        content_x = left + content_margin_left -1
        content_y = top + content_margin_top -5
        content_width = window_width - content_margin_left - content_margin_right +2
        content_height = window_height - content_margin_top - content_margin_bottom +10

        PyImGui.set_cursor_screen_pos(content_x, content_y)

        color = Color(0, 0, 0, 200)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, color.to_tuple_normalized())
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.ChildRounding, 6.0)

        # Create a child window for the content area
        padding = 8.0
        if PyImGui.begin_child("ContentArea", (content_width, content_height), False, PyImGui.WindowFlags.NoFlag):
            PyImGui.set_cursor_pos(padding, padding)  # Manually push content in from top-left
            PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, (0, 0, 0, 0)) 
            
            inner_width = content_width - (padding * 2)
            inner_height = content_height - (padding * 2)
            
            if PyImGui.begin_child("InnerLayout", (inner_width, inner_height), False, PyImGui.WindowFlags.NoFlag):
                #WINDOW CONTENT
                PyImGui.text("Inside framed content area")
                PyImGui.text("You can add more widgets here.")
                PyImGui.text("This area is framed by the custom window frame.")
                if PyImGui.button("push me"):
                    print("Button clicked!")
                    collapsed = not collapsed  # Toggle collapse state on button click
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("This is a tooltip for the button.")
                    
                #END OF WINDOW CONTENT
                PyImGui.end_child()
            PyImGui.pop_style_color(1)
            PyImGui.end_child()

        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(1)

      
    PyImGui.end()
    PyImGui.pop_style_var(1)
    
    
    
if __name__ == "__main__":
    main()
