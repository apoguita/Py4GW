import PyImGui
import math

from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.IniManager import IniManager


ini_file_path= "HeroAI"
ini_filename = "FollowModule.ini"
INI_KEY = ""

class RingConfig:
    def __init__(self, radius:Range | float, color:Color, thickness, show=True):
        if isinstance(radius, Range):
            name = radius.name
        else:
            name = f"{radius:.1f}"
        
        self.caption = name
        self.show = show
        self.radius = radius.value if isinstance(radius, Range) else radius
        self.color:Color = color
        self.thickness = thickness
        
class FollowerPoint:
    def __init__(self, x, y, color:Color):
        self.x = x
        self.y = y
        self.color = color
        
        
class FollowSettings:
    def __init__(self):
        self.scale = 0.5
        self.draw_area_rings = True
        self.area_rings = [
            RingConfig(Range.Touch.value / 2, ColorPalette.GetColor("gw_green"), 2),  # Green
            RingConfig(Range.Touch, ColorPalette.GetColor("gw_assassin"), 2, False),  # Green
            RingConfig(Range.Adjacent, ColorPalette.GetColor("gw_blue"), 2),  # Yellow
            RingConfig(Range.Nearby, ColorPalette.GetColor("blue"), 2),  # Orange
            RingConfig(Range.Area, ColorPalette.GetColor("firebrick"), 2),  # Red
            RingConfig(Range.Earshot, ColorPalette.GetColor("gw_purple"), 2, False),  # Blue
            RingConfig(Range.Spellcast, ColorPalette.GetColor("gold"), 2, False),  # Purple
        ]
    
        self.draw_3d_area_rings = True
        self.show_canvas = True
        self.canvas_size:tuple = (500,500)
        self.follower_points:list[FollowerPoint] = []
        
        
follow_settings = FollowSettings()


def main():
    global INI_KEY
    
    if not INI_KEY:
        INI_KEY = IniManager().ensure_key(ini_file_path, ini_filename)
        if not INI_KEY:
            return
        #_add_config_vars()
        IniManager().load_once(INI_KEY)
        
    canvas_w, canvas_h = follow_settings.canvas_size

    # Extra padding for settings panel + margins
    settings_width = 420
    window_w = canvas_w + settings_width if follow_settings.show_canvas else settings_width
    window_h = canvas_h + 80

    PyImGui.set_next_window_size(
        (window_w, window_h),
        PyImGui.ImGuiCond.Always
    )
        
    if ImGui.Begin(ini_key=INI_KEY,name="Following Module", flags=PyImGui.WindowFlags.NoFlag):    

        table_flags = (
            PyImGui.TableFlags.Borders |
            PyImGui.TableFlags.SizingStretchProp
        )

        column_count = 2 if follow_settings.show_canvas else 1
        
        if PyImGui.begin_table("FollowSettingsMainTable", column_count, table_flags):
            if follow_settings.show_canvas:
                PyImGui.table_setup_column(
                    "Canvas",
                    PyImGui.TableColumnFlags.WidthFixed,
                    follow_settings.canvas_size[0] + 20
                )

            PyImGui.table_setup_column(
                "Settings",
                PyImGui.TableColumnFlags.WidthStretch)
    
            if follow_settings.show_canvas:
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                child_flags = PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove

                if PyImGui.begin_child("FollowSettingsChild", follow_settings.canvas_size, True, child_flags):
                    canvas_pos = PyImGui.get_cursor_screen_pos()
                    center_x = canvas_pos[0] + follow_settings.canvas_size[0] / 2
                    center_y = canvas_pos[1] + follow_settings.canvas_size[1] / 2
                    
                    touch_color = follow_settings.area_rings[0].color.copy()
                    touch_color.set_a(100)
                    touch_radius = follow_settings.area_rings[0].radius * follow_settings.scale
                    
                    # -------------------------------------------------
                    # GRID DRAW
                    # -------------------------------------------------

                    grid_color = ColorPalette.GetColor("gray").copy()
                    grid_color.set_a(80)

                    grid_step_world = Range.Touch.value / 2
                    grid_step = grid_step_world * follow_settings.scale

                    canvas_x, canvas_y = canvas_pos
                    canvas_w, canvas_h = follow_settings.canvas_size

                    left   = canvas_x
                    right  = canvas_x + canvas_w
                    top    = canvas_y
                    bottom = canvas_y + canvas_h

                    # --- Vertical lines (origin-centered) ---
                    x = center_x
                    while x <= right:
                        PyImGui.draw_list_add_line(x, top, x, bottom, grid_color.to_color(), 1)
                        x += grid_step

                    x = center_x - grid_step
                    while x >= left:
                        PyImGui.draw_list_add_line(x, top, x, bottom, grid_color.to_color(), 1)
                        x -= grid_step


                    # --- Horizontal lines (origin-centered) ---
                    y = center_y
                    while y <= bottom:
                        PyImGui.draw_list_add_line(left, y, right, y, grid_color.to_color(), 1)
                        y += grid_step

                    y = center_y - grid_step
                    while y >= top:
                        PyImGui.draw_list_add_line(left, y, right, y, grid_color.to_color(), 1)
                        y -= grid_step

                    
                    #area rings
                    PyImGui.draw_list_add_circle_filled(center_x, center_y, touch_radius, touch_color.to_color(), 64)

                    
                    if follow_settings.draw_area_rings:
                        for ring in follow_settings.area_rings:
                            if ring.show:
                                PyImGui.draw_list_add_circle(center_x, center_y, ring.radius * follow_settings.scale, ring.color.to_color(), 32, ring.thickness)
                     
                    # -------------------------------------------------
                    # FOLLOWER POINTS (CANVAS)
                    # -------------------------------------------------

                    touch_radius = (Range.Touch.value / 2) * follow_settings.scale

                    for i, pt in enumerate(follow_settings.follower_points):

                        draw_x = center_x + (-pt.x * follow_settings.scale)
                        draw_y = center_y + ( pt.y * follow_settings.scale)


                        color = pt.color.copy()
                        color.set_a(120)

                        PyImGui.draw_list_add_circle_filled(
                            draw_x,
                            draw_y,
                            touch_radius,
                            color.to_color(),
                            32
                        )

                        PyImGui.draw_list_add_circle(
                            draw_x,
                            draw_y,
                            touch_radius,
                            pt.color.to_color(),
                            32,
                            2
                        )
                                
   
                    PyImGui.end_child()
                
                PyImGui.table_next_column()
            else:
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
            if PyImGui.collapsing_header("Canvas", PyImGui.TreeNodeFlags.DefaultOpen):
                PyImGui.text("Canvas")
                PyImGui.separator()

                follow_settings.show_canvas = PyImGui.checkbox(
                    "Show Canvas",
                    follow_settings.show_canvas
                )

                changed_w = PyImGui.input_int(
                    "Width",
                    follow_settings.canvas_size[0]
                )

                changed_h = PyImGui.input_int(
                    "Height",
                    follow_settings.canvas_size[1]
                )
                
                PyImGui.separator()
                follow_settings.scale = PyImGui.slider_float("Scale", follow_settings.scale, 0.1, 1.0)
                follow_settings.draw_3d_area_rings = PyImGui.checkbox("Draw 3D Area Rings", follow_settings.draw_3d_area_rings)
                follow_settings.draw_area_rings = PyImGui.checkbox("Draw Area Rings", follow_settings.draw_area_rings)

                # Clamp to sane values
                changed_w = max(100, changed_w)
                changed_h = max(100, changed_h)

                follow_settings.canvas_size = (changed_w, changed_h)
                
            if follow_settings.draw_area_rings:
                if PyImGui.collapsing_header("Area Rings", PyImGui.TreeNodeFlags.DefaultOpen):
                    PyImGui.text("Area Rings")
                    PyImGui.separator()

                    ring_table_flags = (
                        PyImGui.TableFlags.Borders |
                        PyImGui.TableFlags.RowBg |
                        PyImGui.TableFlags.SizingStretchProp
                    )

                    if PyImGui.begin_table("AreaRingsTable", 5, ring_table_flags):

                        # -------------------------
                        # Configurable widths
                        # -------------------------

                        PyImGui.table_setup_column("Show",
                            PyImGui.TableColumnFlags.WidthFixed, 80)

                        PyImGui.table_setup_column("Radius",
                            PyImGui.TableColumnFlags.WidthFixed, 70)

                        PyImGui.table_setup_column("Thickness",
                            PyImGui.TableColumnFlags.WidthFixed, 40)

                        PyImGui.table_setup_column("Color",
                            PyImGui.TableColumnFlags.WidthStretch)

                        PyImGui.table_headers_row()

                        
                        for i, ring in enumerate(follow_settings.area_rings):
                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            ring.show = PyImGui.checkbox(f"{ring.caption}##ShowRing{i}", ring.show)
                            PyImGui.table_next_column()
                            ring.radius = PyImGui.input_float(f"##Radius{i}", ring.radius)
                            PyImGui.table_next_column()
                            ring.thickness = int(PyImGui.input_text(f"##Thickness{i}", str(ring.thickness)))
                            PyImGui.table_next_column()
                            
                            old_color = ring.color.to_tuple_normalized()

                            flags = (
                                PyImGui.ColorEditFlags.NoInputs |
                                PyImGui.ColorEditFlags.NoTooltip |
                                PyImGui.ColorEditFlags.NoLabel |
                                PyImGui.ColorEditFlags.NoDragDrop |
                                PyImGui.ColorEditFlags.AlphaPreview
                            )

                            new_color_vec = PyImGui.color_edit4(
                                f"##Color{i}",
                                old_color,
                                PyImGui.ColorEditFlags(flags)
                            )
                            if new_color_vec != old_color:
                                ring.color = Color.from_tuple_normalized(new_color_vec)
                                    
                        PyImGui.end_table()
                        
            # -------------------------------------------------
            # FOLLOWER POINTS SETTINGS
            # -------------------------------------------------

            if PyImGui.collapsing_header("Follower Points", PyImGui.TreeNodeFlags.DefaultOpen):

                PyImGui.separator()

                # ---------- ADD BUTTON ----------
                if PyImGui.button("Add Point"):
                    follow_settings.follower_points.append(
                        FollowerPoint(
                            0.0,
                            0.0,
                            ColorPalette.GetColor("white")
                        )
                    )

                PyImGui.separator()

                table_flags = (
                    PyImGui.TableFlags.Borders |
                    PyImGui.TableFlags.RowBg |
                    PyImGui.TableFlags.SizingStretchProp
                )

                if PyImGui.begin_table("FollowerPointsTable", 5, table_flags):

                    PyImGui.table_setup_column("X", PyImGui.TableColumnFlags.WidthFixed, 80)
                    PyImGui.table_setup_column("Y", PyImGui.TableColumnFlags.WidthFixed, 80)
                    PyImGui.table_setup_column("Color", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_setup_column("Remove", PyImGui.TableColumnFlags.WidthFixed, 80)

                    PyImGui.table_headers_row()

                    remove_index = -1

                    for i, pt in enumerate(follow_settings.follower_points):

                        PyImGui.table_next_row()

                        # X
                        PyImGui.table_next_column()
                        edit_x = -pt.x
                        edit_x  = PyImGui.slider_float(f"##FP_X{i}", edit_x, -Range.Earshot.value /2, Range.Earshot.value /2)
                        pt.x = -edit_x

                        # Y
                        PyImGui.table_next_column()
                        pt.y = PyImGui.slider_float(f"##FP_Y{i}", pt.y, -Range.Earshot.value /2, Range.Earshot.value /2)

                        # Color
                        PyImGui.table_next_column()

                        old_color = pt.color.to_tuple_normalized()

                        flags = (
                            PyImGui.ColorEditFlags.NoInputs |
                            PyImGui.ColorEditFlags.NoTooltip |
                            PyImGui.ColorEditFlags.NoLabel |
                            PyImGui.ColorEditFlags.AlphaPreview
                        )

                        new_color = PyImGui.color_edit4(
                            f"##FP_Color{i}",
                            old_color,
                            PyImGui.ColorEditFlags(flags)
                        )

                        if new_color != old_color:
                            pt.color = Color.from_tuple_normalized(new_color)

                        # Remove
                        PyImGui.table_next_column()
                        if PyImGui.button(f"Delete##FP{i}"):
                            remove_index = i

                    if remove_index != -1:
                        follow_settings.follower_points.pop(remove_index)

                    PyImGui.end_table()

                    

            PyImGui.end_table()
            
            Overlay().BeginDraw()
            if follow_settings.draw_3d_area_rings:
                # -------------------------------------------------
                # 3D GRID DRAW
                # -------------------------------------------------

                grid_color = ColorPalette.GetColor("gray").copy()
                grid_color.set_a(120)

                grid_step = Range.Touch.value / 2
                grid_extent = Range.Spellcast.value   # how far grid extends from origin

                player_x, player_y, player_z = Agent.GetXYZ(Player.GetAgentID())

                # Snap origin to grid (optional but cleaner visually)
                origin_x = round(player_x / grid_step) * grid_step
                origin_y = round(player_y / grid_step) * grid_step

                # ---- Lines parallel to X axis ----
                y = origin_y - grid_extent
                while y <= origin_y + grid_extent:

                    Overlay().DrawLine3D(
                        origin_x - grid_extent,
                        y,
                        player_z,
                        origin_x + grid_extent,
                        y,
                        player_z,
                        grid_color.to_color(),
                        1
                    )

                    y += grid_step


                # ---- Lines parallel to Y axis ----
                x = origin_x - grid_extent
                while x <= origin_x + grid_extent:

                    Overlay().DrawLine3D(
                        x,
                        origin_y - grid_extent,
                        player_z,
                        x,
                        origin_y + grid_extent,
                        player_z,
                        grid_color.to_color(),
                        1
                    )

                    x += grid_step


            for ring in follow_settings.area_rings:
                if ring.show:
                    player_x, player_y, player_z = Agent.GetXYZ(Player.GetAgentID()) 
                    if follow_settings.draw_3d_area_rings:
                        Overlay().DrawPoly3D(player_x, player_y, player_z, ring.radius, ring.color.to_color(), 64, ring.thickness *2)
                
                # -------------------------------------------------
                # FOLLOWER POINTS (3D ROTATED)
                # -------------------------------------------------

                player_id = Player.GetAgentID()
                player_x, player_y, player_z = Agent.GetXYZ(player_id)

                angle = Agent.GetRotationAngle(player_id)
                angle -= math.pi / 2
                rotation_angle_cos = -math.cos(angle)
                rotation_angle_sin = -math.sin(angle)

                radius = Range.Touch.value / 2

                for pt in follow_settings.follower_points:

                    # --- Rotate local offset into world ---
                    rot_x = (pt.x * rotation_angle_cos) - (pt.y * rotation_angle_sin)
                    rot_y = (pt.x * rotation_angle_sin) + (pt.y * rotation_angle_cos)

                    world_x = player_x + rot_x
                    world_y = player_y + rot_y
                    world_z = player_z

                    Overlay().DrawPoly3D(
                        world_x,
                        world_y,
                        world_z,
                        radius,
                        pt.color.to_color(),
                        32,
                        2
                    )

            Overlay().EndDraw()
        

    ImGui.End(ini_key=INI_KEY)

if __name__ == "__main__":
    main()