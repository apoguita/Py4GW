import PyImGui
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import Color
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Pathing import AutoPathing
from typing import Tuple

MODULE_NAME = "Path Planner"
MODULE_ICON = "Textures/Module_Icons/Pathing.png"

PATH: list[tuple[float, float, int]] = []
draw_path_in_mission_map = False
draw_path_in_3d_world = False
draw_color:Color = Color(0, 255, 0, 255)
use_autopath_between_points = False

# key: ((sx,sy,sz),(gx,gy,gz))  value: list[(x,y,z)]
AUTO_SEG_CACHE: dict[tuple[tuple[float,float,int], tuple[float,float,int]], list[tuple[float,float,int]]] = {}
AUTO_SEG_PENDING: set[tuple[tuple[float,float,int], tuple[float,float,int]]] = set()
_LAST_MAP_ID: int = 0


def _coro_get_path(start_x:float, start_y:float, start_zplane:int,
                   end_x:float, end_y:float, end_zplane:int):
    start:Tuple[float, float, float] = (start_x, start_y, start_zplane)
    goal:Tuple[float, float, float]  = (end_x, end_y, end_zplane)
    key = ((start_x, start_y, start_zplane), (end_x, end_y, end_zplane))

    path_points = yield from AutoPathing().get_path(start, goal)

    # Normalize to the cache type: (float, float, int)
    normalized: list[tuple[float, float, int]] = [
        (float(x), float(y), int(z))
        for (x, y, z) in path_points
    ] if path_points else []

    AUTO_SEG_CACHE[key] = normalized
    AUTO_SEG_PENDING.discard(key)
    return



def draw_window():
    global draw_path_in_mission_map, draw_path_in_3d_world, PATH, draw_color, use_autopath_between_points
    if PyImGui.begin("Path Planner"):
        PyImGui.text(f"Map [{Map.GetMapID()}] - {Map.GetMapName()}")
        PyImGui.separator()
        player_x, player_y, _ = Agent.GetXYZ(Player.GetAgentID())
        player_zplane = Agent.GetZPlane(Player.GetAgentID())
        PyImGui.text(f"Player Position: X: {player_x:.2f}, Y: {player_y:.2f}, Z-Plane: {player_zplane}")
        PyImGui.separator()
        if PyImGui.button("Add current Position to Path"):
            PATH.append((player_x, player_y, player_zplane))
        PyImGui.same_line(0,-1)
        if PyImGui.button("Clear Path"):
            PATH.clear()
        PyImGui.same_line(0,-1)
        if PyImGui.button("Copy Path to Clipboard"):
            path_str = "; ".join([f"({x:.2f}, {y:.2f}, {z})" for x, y, z in PATH])
            PyImGui.set_clipboard_text(path_str)
            
    
        if len(PATH) == 0:
            PyImGui.text("Path is empty. Add points to the path.")
        else:
            use_autopath_between_points = PyImGui.checkbox("Use Autopath Between Points", use_autopath_between_points)
            PyImGui.separator()
            
            draw_path_in_mission_map = PyImGui.checkbox("Draw Path in Mission Map", draw_path_in_mission_map)
            draw_path_in_3d_world = PyImGui.checkbox("Draw Path in 3D World", draw_path_in_3d_world)
            color = PyImGui.color_edit4("Path Color", draw_color.to_tuple_normalized())
            draw_color = Color.from_tuple_normalized(color)
            PyImGui.separator()
        
            points = len(PATH)
            if PyImGui.collapsing_header(f"Edit Path ({points} points)", PyImGui.TreeNodeFlags.DefaultOpen):
                for index, (x, y, zplane) in enumerate(PATH):
                    if PyImGui.collapsing_header(f"Point {index} - (X: {x:.2f}, Y: {y:.2f}, Z-Plane: {zplane})"):
                        PyImGui.push_id(str(index))
                        new_x = PyImGui.input_float("X", x)
                        if new_x != x:
                            PATH[index] = (new_x, y, zplane)
                        new_y = PyImGui.input_float("Y", y)
                        if new_y != y:
                            PATH[index] = (PATH[index][0], new_y, zplane)
                        new_zplane = PyImGui.input_int("Z-Plane", zplane)
                        if new_zplane != zplane:
                            PATH[index] = (PATH[index][0], PATH[index][1], new_zplane)
                        if PyImGui.button("Remove Point"):
                            PATH.pop(index)
                            PyImGui.pop_id()
                            break
                        PyImGui.separator()
                        PyImGui.pop_id() 
    PyImGui.end()
    
    if draw_path_in_3d_world:
        
        def _draw_point_in_3d_world(x,y,z, index, color:Color=Color(0,0,255,200)):
            real_z = Overlay().FindZ(x, y)
            Overlay().DrawPolyFilled3D(x, y, real_z, 30, color.to_color(), 32)
            Overlay().DrawPoly3D(x, y, real_z, 23, Color(0,0,0,255).to_color(), 32, 5.0, False)
            Overlay().DrawText3D(x, y, real_z -100, f"{index}", Color(0, 0, 0, 255).to_color(), False, False, 5.0)
            Overlay().DrawText3D(x, y, real_z -100, f"{index}", Color(255, 255, 255, 255).to_color(), False, False, 4.2)
            
        
        Overlay().BeginDraw()

        if not use_autopath_between_points:
            # --- draw straight segments between waypoints ---
            for i in range(len(PATH) - 1):
                x1, y1, z1 = PATH[i]
                x2, y2, z2 = PATH[i + 1]

                if not GLOBAL_CACHE.Camera.IsPointInFOV(x1, y1) or not GLOBAL_CACHE.Camera.IsPointInFOV(x2, y2):
                    continue

                real_z1 = Overlay().FindZ(x1, y1, z1)
                real_z2 = Overlay().FindZ(x2, y2, z2)
                Overlay().DrawLine3D(x1, y1, real_z1, x2, y2, real_z2, draw_color.to_color(), 2.0)

        else:
            # --- autopath each segment and draw the FULL returned polyline ---
            for i in range(len(PATH) - 1):
                start = PATH[i]
                end   = PATH[i + 1]
                key = (start, end)

                # schedule once if missing
                if key not in AUTO_SEG_CACHE:
                    if key not in AUTO_SEG_PENDING:
                        AUTO_SEG_PENDING.add(key)
                        GLOBAL_CACHE.Coroutines.append(
                            _coro_get_path(
                                start[0], start[1], start[2],
                                end[0], end[1], end[2]
                            )
                        )
                    continue  # not ready yet, draw nothing (or you could draw a placeholder)

                seg_path = AUTO_SEG_CACHE.get(key, [])
                if not seg_path:
                    continue

                # --- draw from actual origin to first autopath point ---
                sx, sy, sz = start
                fx, fy, fz = seg_path[0]

                if GLOBAL_CACHE.Camera.IsPointInFOV(sx, sy) and GLOBAL_CACHE.Camera.IsPointInFOV(fx, fy):
                    real_zs = Overlay().FindZ(sx, sy, sz)
                    real_zf = Overlay().FindZ(fx, fy, fz)
                    Overlay().DrawLine3D(sx, sy, real_zs, fx, fy, real_zf, draw_color.to_color(), 2.0)

                # --- draw full autopath polyline ---
                for (x1, y1, z1), (x2, y2, z2) in zip(seg_path, seg_path[1:]):
                    if not GLOBAL_CACHE.Camera.IsPointInFOV(x1, y1) or not GLOBAL_CACHE.Camera.IsPointInFOV(x2, y2):
                        continue

                    real_z1 = Overlay().FindZ(x1, y1, z1)
                    real_z2 = Overlay().FindZ(x2, y2, z2)
                    Overlay().DrawLine3D(x1, y1, real_z1, x2, y2, real_z2, draw_color.to_color(), 2.0)


        # keep your waypoint circles/text exactly as you already draw them
        # (draw circles using PATH points, independent of autopath toggle)
        for i, (x, y, z) in enumerate(PATH):
            if not GLOBAL_CACHE.Camera.IsPointInFOV(x, y):
                continue
            _draw_point_in_3d_world(x, y, z, i, draw_color)

        Overlay().EndDraw()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Path Planner", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A navigation utility for creating, testing, and")
    PyImGui.text("visualizing movement paths. It allows developers to record")
    PyImGui.text("coordinates and preview pathing logic in real-time.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Point Recording: Instantly add your current player coordinates to a sequence")
    PyImGui.bullet_text("3D Visualization: Renders the planned path directly in the game world")
    PyImGui.bullet_text("Autopath Integration: Toggles between straight lines and engine-calculated paths")
    PyImGui.bullet_text("Path Editor: Fine-tune X, Y, and Z-Plane values for individual waypoints")
    PyImGui.bullet_text("Clipboard Export: Copy formatted coordinate lists for use in custom scripts")
    PyImGui.bullet_text("Smart Caching: Asynchronous path calculation to maintain high frame rates")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()
    

def main():
    draw_window()

if __name__ == "__main__":
    main()
