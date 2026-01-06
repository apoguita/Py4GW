import sys
        
from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

from Widgets.SulfurousRunner.settings import Settings
from Widgets.SulfurousRunner.pathing import search_paths, update_waypoints
from Widgets.SulfurousRunner.ui import draw_configure, draw_flags, draw_paths
from Widgets.SulfurousRunner.globals import Global

MODULE_NAME = "Sulfurous Runner"

g = Global()

settings = Settings()

draw_throttle = ThrottledTimer(2000)
path_throttle = ThrottledTimer(250)


def configure():
    draw_configure()
    pass

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
                g.waypoints.get(GLOBAL_CACHE.Map.GetMapID(), []),
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
