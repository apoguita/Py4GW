
import math
import PyImGui
from Py4GWCoreLib import Camera, ImGui, Player
from Py4GWCoreLib.DXOverlay import DXOverlay
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.ImGui_src.WindowModule import WindowModule
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GW_widget_manager import Widget, WidgetHandler

from .settings import Settings
from .waypoint import Waypoint3D

widget_info : Widget | None = None
configure_window : WindowModule = WindowModule(
    "Sulfurous Runner",
    "Sulfurous Runner",
    window_size=(500, 280),
    window_pos=(200, 200),
    can_close=True,
)

def draw_flag(overlay: Overlay, wp: Waypoint3D, flag_color : Color = Color(0, 204, 156, 100), collision : bool = False):
    size = 25
    
    z = overlay.FindZ(wp.x, wp.y)
    z_min = z
    z_max = z - 75
        
    overlay.DrawLine3D(
        wp.x, wp.y, z_min,
        wp.x, wp.y, z_max,
        flag_color.color_int,
        3
    )

    overlay.DrawTriangleFilled3D(
        wp.x, wp.y, z_max,
        wp.x, wp.y, z_max + size,
        wp.x - size, wp.y, z_max + (size / 2),
        flag_color.color_int
    )
                
def draw_flags(waypoints : list[Waypoint3D], flag_color : Color = Color(0, 204, 156, 100), collision : bool = False):
    overlay = Overlay()
    overlay.BeginDraw()
            
    # Draw waypoint flags
    for idx, wp in enumerate(waypoints):
        if not GLOBAL_CACHE.Camera.IsPointInFOV(wp.x, wp.y):
            continue
        
        if wp.distance > 5000:
            continue

        draw_flag(overlay, wp, flag_color)
        
    overlay.EndDraw()
    
def draw_paths(paths : dict[int, list[Waypoint3D]], path_color : Color, closest_waypoint : int, collision : bool = False):
    if paths:
        # Draw paths
        player_x, player_y = Player.GetXY()
        
        for idx, path in paths.items():
            if idx < closest_waypoint:
                continue
            
            for i in range(len(path) - 1):
                p1 = path[i]
                
                distance = Utils.Distance(p1.as_tuple(), (player_x, player_y))
                if distance > 5000:
                    continue
                
                p2 = path[i + 1]
                z1 = DXOverlay.FindZ(p1.x, p1.y)
                z2 = DXOverlay.FindZ(p2.x, p2.y)
                
                DXOverlay().DrawLine3D(p1.x, p1.y, z1 - 50, p2.x, p2.y, z2 - 50, path_color.to_dx_color(), collision)
                
def color_equal(a: tuple[float, float, float, float],
                b: tuple[float, float, float, float],
                eps: float = 1e-6) -> bool:
    return all(math.isclose(x, y, abs_tol=eps) for x, y in zip(a, b))

def draw_configure():
    global widget_info
    
    if widget_info is None:
        widget_info = WidgetHandler().get_widget_info("Sulfurous Runner")
        
    configure_window.open = widget_info.configuring if widget_info else False
    
    if not widget_info:
        return
    
    if not configure_window.open:
        return
    
    open = configure_window.begin()
    
    if open: 
        settings = Settings()
        
        text = (
            "This widget allows you to visualize predefined waypoints and paths in the game world. "
            "You can configure the display settings, such as colors and visibility options, to suit your preferences.\n\n"
            "Use this tool to enhance your navigation through the sulfurous areas of the game."
        )
        ImGui.text_wrapped(text)
        
        draw_flags = ImGui.checkbox("Draw Waypoint Flags", settings.draw_flags)
        if draw_flags != settings.draw_flags:
            settings.draw_flags = draw_flags
            settings.save()
        
        draw_paths = ImGui.checkbox("Draw Paths", settings.draw_paths)
        if draw_paths != settings.draw_paths:
            settings.draw_paths = draw_paths        
            settings.save()
            
        path_collision = ImGui.checkbox("Use Path Collision", settings.use_path_collision)
        if path_collision != settings.use_path_collision:
            settings.use_path_collision = path_collision        
            settings.save()

        flag_color = ImGui.color_edit4("Flag Color", settings.flag_color.color_tuple)
        if flag_color is not None and not color_equal(flag_color, settings.flag_color.color_tuple):
            settings.flag_color = Color.from_tuple(flag_color)
            settings.save()
        
        path_color = ImGui.color_edit4("Path Color", settings.path_color.color_tuple)
        if path_color is not None and not color_equal(path_color, settings.path_color.color_tuple):
            settings.path_color = Color.from_tuple(path_color)
            settings.save()
        
        configure_window.process_window()
        
    configure_window.end()
        
    if configure_window.changed or not configure_window.open:
        if widget_info:
            widget_info.configuring = configure_window.open
    pass