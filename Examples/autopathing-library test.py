import Py4GW
from Py4GWCoreLib import *
import math
import time

# Globals for testing
path = []
result_path = []
x, y = 6698, 16095

start_process_time = time.time()
elapsed_time = 0.0
pathing_object = AutoPathing()
path_requested = False

# Config options
smooth_by_los = True
smooth_by_chaikin = False
margin = 100.0
step_dist = 200.0
chaikin_iterations = 1

def main():
    def draw_path(points, rgba):
        if points and len(points) >= 2:
            color = Color(*rgba).to_dx_color()
            for i in range(len(points) - 1):
                x1, y1, z1 = points[i]
                x2, y2, z2 = points[i + 1]
                z1 = DXOverlay.FindZ(x1, y1) - 125
                z2 = DXOverlay.FindZ(x2, y2) - 125
                DXOverlay().DrawLine3D(x1, y1, z1, x2, y2, z2, color, False)

    global result_path, x, y, start_process_time, pathing_object, path_requested, elapsed_time
    global smooth_by_los, smooth_by_chaikin, margin, step_dist, chaikin_iterations


    if PyImGui.begin("Pathing Test", PyImGui.WindowFlags.AlwaysAutoResize):

        player_pos = GLOBAL_CACHE.Player.GetXY()
        player_z = Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID())
        map_id = Map.GetMapID()

        x = PyImGui.input_int("Target X", x)
        y = PyImGui.input_int("Target Y", y)

        if PyImGui.button("Capture Start Position"):
            player_pos = GLOBAL_CACHE.Player.GetXY()
            x = int(player_pos[0])
            y = int(player_pos[1])
            print(f"Captured start position: ({x}, {y})")
            
        PyImGui.separator()
        smooth_by_los = PyImGui.checkbox("Smooth by LOS", smooth_by_los)
        margin = PyImGui.input_float("LOS Margin", margin)
        step_dist = PyImGui.input_float("LOS Step Dist", step_dist)
        smooth_by_chaikin = PyImGui.checkbox("Smooth by Chaikin", smooth_by_chaikin)
        chaikin_iterations = PyImGui.input_int("Chaikin Iterations", chaikin_iterations)

        if PyImGui.button("Search Path"):
            start_process_time = time.time()
            path_requested = True
            def search_path_coroutine():
                global result_path, path_requested, elapsed_time
                zplane = Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID())
                result_path = yield from pathing_object.get_path(
                    (player_pos[0], player_pos[1], zplane),
                    (x, y, zplane),
                    smooth_by_los=smooth_by_los,
                    margin=margin,
                    step_dist=step_dist,
                    smooth_by_chaikin=smooth_by_chaikin,
                    chaikin_iterations=chaikin_iterations
                )
                path_requested = False
                yield
                elapsed_time = time.time() - start_process_time
                

            GLOBAL_CACHE.Coroutines.append(search_path_coroutine())

        PyImGui.separator()
        PyImGui.text(f"Map ID: {map_id}")
        PyImGui.text(f"Player: ({player_pos[0]:.1f}, {player_pos[1]:.1f}, {player_z})")
        PyImGui.text(f"Target: ({x}, {y}, {player_z})")
        PyImGui.text(f"Distance to target: {math.hypot(player_pos[0] - x, player_pos[1] - y):.1f} units")

        navmesh = pathing_object.get_navmesh()
        if navmesh:
            start_trap = navmesh.find_trapezoid_id_by_coord(player_pos)
            goal_trap = navmesh.find_trapezoid_id_by_coord((x, y))
            PyImGui.text(f"Start Trapezoid ID: {start_trap}")
            PyImGui.text(f"Goal Trapezoid ID: {goal_trap}")

            if start_trap and goal_trap:
                los = navmesh.has_line_of_sight(player_pos, (x, y))
                PyImGui.text(f"Line of Sight: {'YES' if los else 'NO'}")

        else:
            PyImGui.text("NavMesh not loaded.")

        PyImGui.separator()
        if path_requested:
            PyImGui.text("Searching for path...")
        else:
            if result_path:
                PyImGui.text(f"Path found with {len(result_path)} points")
                PyImGui.text(f"NavMesh load time: {elapsed_time:.2f} seconds")
                
                if PyImGui.button("Follow Path") and result_path:
                    def follow_path_coroutine():
                        path2d = [(x, y) for (x, y, _) in result_path]
                        yield from Routines.Yield.Movement.FollowPath(path2d)
                        yield
                    GLOBAL_CACHE.Coroutines.append(follow_path_coroutine())


                if PyImGui.collapsing_header("Path Points", PyImGui.TreeNodeFlags.DefaultOpen):
                    for i, point in enumerate(result_path):
                        PyImGui.text(f"Point {i}: ({point[0]:.1f}, {point[1]:.1f}, {point[2]:.1f})")
            else:
                PyImGui.text("No path found or search not initiated.")

        PyImGui.end()

    draw_path(result_path, (255, 255, 0, 255))  # Yellow

if __name__ == "__main__":
    main()
