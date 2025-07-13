import Py4GW
from Py4GWCoreLib import *
import webbrowser

MODULE_NAME = "GwFake Window Test"
TEXTURE_FOLDER = "Textures\\Game UI\\"
FRAME_ATLAS = "ui_window_frame_atlas.png"
FRAME_ATLAS_DIMENSIONS = (128,128)
TITLE_ATLAS = "ui_window_title_frame_atlas.png"
TITLE_ATLAS_DIMENSIONS = (128, 32)

LOWER_BORDER_PIXEL_MAP = (11,110,78,128)
LOWER_RIGHT_CORNER_TAB_PIXEL_MAP = (78,110,117,128)
LOWER_RIGHT_CORNER_PIXEL_MAP = (117,110,128,128)
LOWER_LEFT_CORNER_PIXEL_MAP = (0,110,11,128)
LOWER_LEFT_TAB_PIXEL_MAP = (0,75,11,110)
LOWER_RIGHT_TAB_PIXEL_MAP = (117,85,128,110)
UPPER_LEFT_TAB_PIXEL_MAP = (0,0,15,35)
UPPER_RIGHT_TAB_PIXEL_MAP = (113,0,128,40)
LEFT_BORDER_PIXEL_MAP = (0,28,17,85)
RIGHT_BORDER_PIXEL_MAP = (111,28,128,85)

LEFT_TITLE_PIXEL_MAP = (0,0,18,32)
RIGHT_TITLE_PIXEL_MAP = (110,0,128,32)
TITLE_AREA_PIXEL_MAP = (19,0,109,32)

window_size = (300, 200)
window_pos = {"X": 500.0, "Y": 500.0}
first_run = True

pixel_origin = [0, 0]
pixel_ending = [128, 128]

set_pos_dragging = False

def draw_region_from_pixelmap(x: float, y: float, pixel_map: tuple[int, int, int, int], texture_path: str):
    x0, y0, x1, y1 = pixel_map
    width = x1 - x0
    height = y1 - y0

    uv0, uv1 = Utils.PixelsToUV(x0, y0, width, height, FRAME_ATLAS_DIMENSIONS[0], FRAME_ATLAS_DIMENSIONS[1])

    ImGui.DrawTexturedRectExtended(
        pos=(x, y),
        size=(width, height),
        texture_path=texture_path,
        uv0=uv0,
        uv1=uv1,
        tint=(255, 255, 255, 255)
    )


@staticmethod
def floating_textured_titlebar_via_imagebutton(x, y, width, height, texture_path, uv0, uv1, name=""):
    # Position the floating transparent window
    PyImGui.set_next_window_pos(x, y)
    PyImGui.set_next_window_size(width, height)

    flags = (
        PyImGui.WindowFlags.NoCollapse |
        PyImGui.WindowFlags.NoTitleBar |
        PyImGui.WindowFlags.NoScrollbar |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.AlwaysAutoResize |
        PyImGui.WindowFlags.NoBackground
    )

    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0, 0)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0.0)
    PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 0, 0, 0))
    
    # Transparent button face
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.0, 0.0, 0.0, 0.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.0, 0.0, 0.0, 0.0))
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.0, 0.0, 0.0, 0.0))

    result = False
    if PyImGui.begin(f"##titlebar_window{name}", flags):
        result = ImGui.ImageButtonExtended(
            caption=f"##titlebar_btn{name}",
            texture_path=texture_path,
            size=(width, height),
            uv0=uv0,
            uv1=uv1,
            bg_color=(0, 0, 0, 0),
            tint_color=(255, 255, 255, 255),
            frame_padding=0
        )


    PyImGui.end()
    PyImGui.pop_style_color(4)
    PyImGui.pop_style_var(2)

    return result



def main2():
    global MODULE_NAME, window_size, window_pos, first_run
    global pixel_origin, pixel_ending, set_pos_dragging
    
    flags = PyImGui.WindowFlags.NoTitleBar

    if first_run:
        PyImGui.set_next_window_size(window_size[0], window_size[1])     
        PyImGui.set_next_window_pos(window_pos["X"], window_pos["Y"])
        first_run = False
        
    if set_pos_dragging:
        PyImGui.set_next_window_pos(window_pos["X"], window_pos["Y"])
        set_pos_dragging = False
        
    if PyImGui.begin(MODULE_NAME, flags):
        
        pixel_origin[0] = PyImGui.input_int("Pixel Origin X", pixel_origin[0])
        pixel_origin[1] = PyImGui.input_int("Pixel Origin Y", pixel_origin[1])
        
        pixel_ending[0] = PyImGui.input_int("Pixel Ending X", pixel_ending[0])
        pixel_ending[1] = PyImGui.input_int("Pixel Ending Y", pixel_ending[1])
        
        region_width = pixel_ending[0] - pixel_origin[0]
        region_height = pixel_ending[1] - pixel_origin[1]

        # Show full texture preview
        PyImGui.text("Full Atlas Preview")
        ImGui.DrawTextureExtended(
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            size=(128, 128),
            uv0=(0.0, 0.0),
            uv1=(1.0, 1.0),
            tint=(255, 255, 255, 255),
            border_color=(0, 0, 0, 0)
        )

        # Convert to UVs
        uv0, uv1 = Utils.PixelsToUV(
            pixel_origin[0], pixel_origin[1],
            region_width, region_height,
            FRAME_ATLAS_DIMENSIONS[0], FRAME_ATLAS_DIMENSIONS[1]
        )

        # Show selected region with correct aspect
        PyImGui.text("Selected Region Preview")
        if region_height != 0:
            aspect = region_width / region_height
        else:
            aspect = 1.0

        draw_height = 256
        draw_width = draw_height * aspect

        ImGui.DrawTextureExtended(
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            size=(draw_width, draw_height),
            uv0=uv0,
            uv1=uv1,
            tint=(255, 255, 255, 255),
            border_color=(0, 0, 0, 0)
        )
        # === Draw fake bottom border using your pixel maps ===
        # Get current window draw position
        win_pos = PyImGui.get_window_pos()
        win_size = PyImGui.get_window_size()
        
        left = win_pos[0] - LOWER_LEFT_CORNER_PIXEL_MAP[2] +2
        right = win_pos[0] + win_size[0] - 4     
        top = win_pos[1]

        height = win_pos[1] + win_size[1] -4
        width = win_pos[1] + win_size[0] -4
        
        #LEFT TITLE
        x0, y0, x1, y1 = LEFT_TITLE_PIXEL_MAP
        t_width = x1 - x0
        t_height = y1 - y0

        uv0, uv1 = Utils.PixelsToUV(x0, y0, t_width, t_height, TITLE_ATLAS_DIMENSIONS[0], TITLE_ATLAS_DIMENSIONS[1])

        ImGui.DrawTexturedRectExtended(
            pos=(left, top-32),
            size=(18, 32),
            texture_path=TEXTURE_FOLDER + TITLE_ATLAS,
            uv0=uv0,
            uv1=(uv1),
            tint=(255, 255, 255, 255)
        )
        
        #RIGHT TITLE
        x0, y0, x1, y1 = RIGHT_TITLE_PIXEL_MAP
        t_width = x1 - x0
        t_height = y1 - y0
        
        uv0, uv1 = Utils.PixelsToUV(x0, y0, t_width, t_height, TITLE_ATLAS_DIMENSIONS[0], TITLE_ATLAS_DIMENSIONS[1])
        
        ImGui.DrawTexturedRectExtended(
            pos=(right-5, top-32),
            size=(18, 32),
            texture_path=TEXTURE_FOLDER + TITLE_ATLAS,
            uv0=uv0,
            uv1=uv1,
            tint=(255, 255, 255, 255)
        )
        
 
        #BOTTOM LEFT CORNER
        draw_region_from_pixelmap(left, height, LOWER_LEFT_CORNER_PIXEL_MAP, TEXTURE_FOLDER + FRAME_ATLAS)
        
        #BOTTOM RIGHT CORNER
        draw_region_from_pixelmap(right, height, LOWER_RIGHT_CORNER_PIXEL_MAP, TEXTURE_FOLDER + FRAME_ATLAS)
        
        #BOTTOM RIGHT TAB
        texture_width = LOWER_RIGHT_CORNER_TAB_PIXEL_MAP[2] - LOWER_RIGHT_CORNER_TAB_PIXEL_MAP[0]
        draw_region_from_pixelmap(right - texture_width, height, LOWER_RIGHT_CORNER_TAB_PIXEL_MAP, TEXTURE_FOLDER + FRAME_ATLAS)
        
        #stretched stretched bottom border
        bottom_border_x = left + LOWER_LEFT_CORNER_PIXEL_MAP[2]
        bottom_border_x2 = right - texture_width
        border_height = LOWER_BORDER_PIXEL_MAP[3] - LOWER_BORDER_PIXEL_MAP[1]
        stretched_width = bottom_border_x2 - bottom_border_x
        
        uv0, uv1 = Utils.PixelsToUV(
            LOWER_BORDER_PIXEL_MAP[0], LOWER_BORDER_PIXEL_MAP[1],
            LOWER_BORDER_PIXEL_MAP[2] - LOWER_BORDER_PIXEL_MAP[0],
            border_height,
            FRAME_ATLAS_DIMENSIONS[0], FRAME_ATLAS_DIMENSIONS[1]
        )
        ImGui.DrawTexturedRectExtended(
            pos=(bottom_border_x, height),
            size=(stretched_width, border_height),
            texture_path=TEXTURE_FOLDER + FRAME_ATLAS,
            uv0=uv0,
            uv1=uv1,
            tint=(255, 255, 255, 255)
        )

        #BOTTOM LEFT TAB
        tab_height = LOWER_LEFT_TAB_PIXEL_MAP[3] - LOWER_LEFT_TAB_PIXEL_MAP[1]
        texture_top = height - tab_height

        draw_region_from_pixelmap(left, texture_top, LOWER_LEFT_TAB_PIXEL_MAP, TEXTURE_FOLDER + FRAME_ATLAS)
        
        #BOTTOM RIGHT TAB
        tab_height = LOWER_RIGHT_TAB_PIXEL_MAP[3] - LOWER_RIGHT_TAB_PIXEL_MAP[1]
        texture_top = height - tab_height
        draw_region_from_pixelmap(right, texture_top, LOWER_RIGHT_TAB_PIXEL_MAP, TEXTURE_FOLDER + FRAME_ATLAS)
        
        #UPPER LEFT TAB
        tab_height = UPPER_LEFT_TAB_PIXEL_MAP[3] - UPPER_LEFT_TAB_PIXEL_MAP[1]
        texture_top = win_pos[1]
        draw_region_from_pixelmap(left-1, texture_top, UPPER_LEFT_TAB_PIXEL_MAP, TEXTURE_FOLDER + FRAME_ATLAS)
        
        #UPPER RIGHT TAB
        tab_height = UPPER_RIGHT_TAB_PIXEL_MAP[3] - UPPER_RIGHT_TAB_PIXEL_MAP[1]
        texture_top = win_pos[1]
        draw_region_from_pixelmap(right-2, texture_top, UPPER_RIGHT_TAB_PIXEL_MAP, TEXTURE_FOLDER + FRAME_ATLAS)

        # Track window position each frame
        x, y = PyImGui.get_window_pos()
        window_pos["X"] = x
        window_pos["Y"] = y
        PyImGui.end()
        
         # === TITLEBAR WINDOW ===
        titlebar_height = 32
        titlebar_width = window_size[0]

        titlebar_x = window_pos["X"]
        titlebar_y = window_pos["Y"] - titlebar_height

        # Set up UV
        x0, y0, x1, y1 = TITLE_AREA_PIXEL_MAP
        t_width = x1 - x0
        t_height = y1 - y0
        uv0, uv1 = Utils.PixelsToUV(x0, y0, t_width, t_height, TITLE_ATLAS_DIMENSIONS[0], TITLE_ATLAS_DIMENSIONS[1])

        # This must be OUTSIDE the function
        PyImGui.set_next_window_pos(titlebar_x, titlebar_y)
        PyImGui.set_next_window_size(titlebar_width, titlebar_height)

        if floating_textured_titlebar_via_imagebutton(
            x=titlebar_x,
            y=titlebar_y,
            width=titlebar_width,
            height=titlebar_height,
            texture_path=TEXTURE_FOLDER + TITLE_ATLAS,
            uv0=uv0,
            uv1=uv1,
            name="draggable_titlebar"
        ):
            print("Clicked titlebar")

        # === DRAG HANDLER ===
        if PyImGui.is_item_active() and PyImGui.is_mouse_down(0):
            dx, dy = PyImGui.get_mouse_drag_delta(0, 0.0)
            window_pos["X"] += dx
            window_pos["Y"] += dy
            PyImGui.reset_mouse_drag_delta(0)
        


def main():
    global window_pos, window_size, first_run

    # === Draggable Window with Normal Button ===
    PyImGui.set_next_window_pos(window_pos["X"], window_pos["Y"])
    PyImGui.set_next_window_size(window_size[0], window_size[1])

    PyImGui.begin("##drag_window", PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize)

    if PyImGui.button("Drag me", 100, 30):
        pass

    if PyImGui.is_item_active() and PyImGui.is_mouse_down(0):
        dx, dy = PyImGui.get_mouse_drag_delta(0, 0.0)
        window_pos["X"] += dx
        window_pos["Y"] += dy
        PyImGui.reset_mouse_drag_delta(0)

    PyImGui.end()

    # === Floating Textured Titlebar (Separate Drag Test) ===
    titlebar_height = 32
    titlebar_width = window_size[0]
    titlebar_x = window_pos["X"]
    titlebar_y = window_pos["Y"] - titlebar_height

    x0, y0, x1, y1 = TITLE_AREA_PIXEL_MAP
    t_width = x1 - x0
    t_height = y1 - y0
    uv0, uv1 = Utils.PixelsToUV(x0, y0, t_width, t_height, TITLE_ATLAS_DIMENSIONS[0], TITLE_ATLAS_DIMENSIONS[1])

    if floating_textured_titlebar_via_imagebutton(
        x=titlebar_x,
        y=titlebar_y,
        width=titlebar_width,
        height=titlebar_height,
        texture_path=TEXTURE_FOLDER + TITLE_ATLAS,
        uv0=uv0,
        uv1=uv1,
        name="drag_titlebar"
    ):
        pass  # Clicked titlebar

    if PyImGui.is_item_active() and PyImGui.is_mouse_down(0):
        dx, dy = PyImGui.get_mouse_drag_delta(0, 0.0)
        window_pos["X"] += dx
        window_pos["Y"] += dy
        PyImGui.reset_mouse_drag_delta(0)




    
if __name__ == "__main__":
    main()
