from typing import Generator
from PyOverlay import Overlay
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Agent import Agent
from .waypoint import Waypoint3D, Waypoints
from .globals import Global

def update_waypoints():
    g = Global()        
    overlay = Overlay()
    
    waypoints = g.waypoints.get(Map.GetMapID(), [])
    if not waypoints:
        return
    
    player_x, player_y = GLOBAL_CACHE.Player.GetXY()
    closest_distance = float("inf")
    
    for idx, wp in enumerate(waypoints):
        wp.distance = Utils.Distance((player_x, player_y), (wp.x, wp.y))
        if wp.z == 0.0:
            wp.z = overlay.FindZ(wp.x, wp.y)
                    
        if wp.distance < closest_distance:
            closest_distance = wp.distance
            g.closest_waypoint = idx

def search_paths():
    g = Global()
    
    if g.current_path_generator is not None:
        try:
            next(g.current_path_generator, None)
            
        except StopIteration:
            g.current_path_generator = None
    else:
        # ConsoleLog("Sulfurous Runner", "Starting new path search...")
        g.current_path_generator = search_path_generator(g.waypoints.get(Map.GetMapID(), []))
        
def search_path_generator(waypoints : list[Waypoint3D] | None = None) -> Generator:   
    if not waypoints:
        return
    
    g = Global()        
            
    player_x, player_y = GLOBAL_CACHE.Player.GetXY()
    zplane = Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID())
    
    for idx in range(g.closest_waypoint, len(waypoints)):                
        if idx in g.paths and idx != g.closest_waypoint:
            continue
        
        if idx == 0 or idx == g.closest_waypoint:
            start = Waypoint3D(player_x, player_y, zplane)
            
        else:
            start = waypoints[idx - 1].with_z(zplane)

        goal = waypoints[idx].with_z(zplane)

        path = yield from AutoPathing().get_path(start.as_tuple(), goal.as_tuple())
        if path:                
            g.paths[idx] = [Waypoint3D(*p) for p in path]
                            
    g.current_path_generator = None
    