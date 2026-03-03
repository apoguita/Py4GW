import sys
        
from Py4GWCoreLib import UIManager, Color, ImGui
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

from Sources.frenkeyLib.SulfurousRunner.settings import Settings
from Sources.frenkeyLib.SulfurousRunner.pathing import search_paths, update_waypoints
from Sources.frenkeyLib.SulfurousRunner.ui import draw_configure, draw_flags, draw_paths
from Sources.frenkeyLib.SulfurousRunner.globals import Global
import PyImGui

MODULE_NAME = "Sulfurous Runner"
MODULE_ICON = "Textures\\Module_Icons\\Sulfurous_Haze.jpg"
g = Global()

settings = Settings()

draw_throttle = ThrottledTimer(2000)
path_throttle = ThrottledTimer(250)


def configure():
    draw_configure()
    pass

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Sulfurous Runner", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An advanced navigational overlay designed for exploring")
    PyImGui.text("the Desolation and hazardous sulfurous regions. It visualizes")
    PyImGui.text("safe pathing nodes and tactical waypoints in real-time.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Visual Pathing: Renders 3D lines and nodes to guide movement through hazards")
    PyImGui.bullet_text("Waypoint Tracking: Dynamic flagging of objectives and safe-zones in the sulfur")
    PyImGui.bullet_text("Collision Detection: Optional logic to adjust flags based on terrain height")
    PyImGui.bullet_text("Customizable UI: Configurable colors for flags and paths to match your preference")
    PyImGui.bullet_text("Performance Optimized: Uses throttled timers to ensure smooth rendering/logic")
    PyImGui.bullet_text("Map Aware: Automatically updates waypoints based on the current Map ID")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by frenkey")

    PyImGui.end_tooltip()

def main():            
    if Routines.Checks.Map.IsLoading():
        draw_throttle.Reset()
        return
      
    if not Routines.Checks.Map.IsMapReady():
        draw_throttle.Reset()
        return
        
    if not Routines.Checks.Map.IsExplorable():
        draw_throttle.Reset()
        return
    
    if UIManager.IsWorldMapShowing():
        draw_throttle.Reset()
        return
        
    if not settings.draw_flags and not settings.draw_paths:
        return

    update_waypoints()
    search_paths()
    
    if draw_throttle.IsExpired():
        if settings.draw_flags:
            draw_flags(
                g.waypoints.get(Map.GetMapID(), []),
                settings.flag_color,
                settings.use_flag_collision
            )
        
        if settings.draw_paths:
            draw_paths(
                g.paths,
                settings.path_color,
                g.closest_waypoint,
                settings.use_path_collision
            )

__all__ = ["main", "configure"]
