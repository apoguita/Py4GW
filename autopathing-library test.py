import Py4GW
from Py4GWCoreLib import *

# Globals for testing
path = []
result_path = []
x,y = 0, 0

start_process_time = time.time()
pathing_object = AutoPathing()
path_requested = False

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
            
    global result_path, x, y, start_process_time, pathing_object, path_requested

    if PyImGui.begin("Pathing Test", PyImGui.WindowFlags.AlwaysAutoResize):
        
        start_process_time = time.time()
        
        player_pos = GLOBAL_CACHE.Player.GetXY()
        


        x = PyImGui.input_int("Start X", x)
        y = PyImGui.input_int("Start Y", y)

        if PyImGui.button("Capture Start Position"):
            player_pos = GLOBAL_CACHE.Player.GetXY()
            x = int(player_pos[0])
            y = int(player_pos[1])
            print(f"Captured start position: ({x}, {y})")

        if PyImGui.button("Search Path"):
            path_requested = True
            def search_path_coroutine():
                global result_path, path_requested
                player_pos = GLOBAL_CACHE.Player.GetXY()
                zplane = GLOBAL_CACHE.Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID())
                result_path = yield from pathing_object.get_path(
                    (player_pos[0], player_pos[1], zplane),
                    (x, y, zplane)
                )
                path_requested = False
                yield  # allow one final frame

            GLOBAL_CACHE.Coroutines.append(search_path_coroutine())
            
            
        if path_requested:
            PyImGui.text("Searching for path...")
        else:
            if result_path:
                PyImGui.text(f"Path found with {len(result_path)} points in {time.time() - start_process_time:.2f} seconds")
                for i, point in enumerate(result_path):
                    PyImGui.text(f"Point {i}: ({point[0]}, {point[1]}, {point[2]})")
            else:
                PyImGui.text("No path found or search not initiated.")

        PyImGui.end()

    # Draw all variants in different colors
    draw_path(result_path, (255, 255, 0, 255))         # Yellow





if __name__ == "__main__":
    main()
