from operator import ne
from Py4GWCoreLib import *

module_name = "Point Logger"

started = False
polling_time = 5
timer = Timer()
timer.Start()

outpost_coord_list = [(-24380, 15074), (-26375, 161)]

farming_route = [
    (11375, -22761), (10925, -23466), (10917, -24311), (10280, -24620),
    (9640, -23175), (7815, -23200), (7765, -22940), (8213, -22829), (8740, -22475),
    (8880, -21384), (8684, -20833), (8982, -20576)
]

farming_route2 = [
    (10196, -20124), (9976, -18338), (11316, -18056), (10392, -17512),
    (10114, -16948), (10729, -16273), (10505, -14750), (10815, -14790), (11090, -15345),
    (11670, -15457), (12604, -15320), (12450, -14800), (12725, -14850), (12476, -16157)
]

path_to_killing_spot = [
    (13070, -16911), (12938, -17081), (12790, -17201), (12747, -17220),
    (12703, -17239), (12684, -17184)
]

new_farming_route = [
    (11375, -22761), (10925, -23466), (10917, -24311), (10280, -24620),
	(9640, -23175), (7579, -23213), (7765, -22940), (8213, -22829), (8740, -22475),
	(8880, -21384), (8684, -20833), (8120, -20550), (8800, -20397), (9200, -20602)	
]

new_farming_route2 = [  
	(10306, -20249), (10104, -18715), (11316, -18056), (10392, -17512),
	(9457, -16814), (10114, -16948), (10729, -16273), (10505, -14750), (10815, -14790),
	(11090, -15345), (11670, -15457), (12494, -15250), (12603, -14824), (12750, -15685)
]
new_path = []

draw_original_route = False
draw_new_route = False
# Example of additional utility function
overlay = Overlay()
def DrawWindow():
    global module_name, started, polling_time, timer
    global draw_original_route, farming_route, farming_route2, path_to_killing_spot
    global overlay, new_path, draw_new_route
    try:
        if PyImGui.begin(module_name):
        
            PyImGui.text("Coordinate logger")
            PyImGui.separator()

            polling_time = PyImGui.input_int("Polling Time (s)", polling_time)
            
            started = ImGui.toggle_button("Start" if not started else "Stop", started)

            player_x, player_y = Player.GetXY()

            if started:
                if timer.HasElapsed(polling_time *1000):
                    Py4GW.Console.Log(module_name, f"({int(player_x)}, {int(player_y)}),", Py4GW.Console.MessageType.Info)
                    timer.Reset()

            PyImGui.separator()

            if started:
                PyImGui.text(f"Last polled: {timer.GetElapsedTime() / 1000:.2f}s ago")

            if PyImGui.button("Add current player position to route"):
                new_path.append((player_x, player_y))

            if PyImGui.button("remove last Point"):
                new_path.pop()

            if PyImGui.button("Clear new path"):
                new_path.clear()

            if PyImGui.button("print new path"):
                for coord in new_path:
                    Py4GW.Console.Log(module_name,f"({int(coord[0])}, {int(coord[1])}),", Py4GW.Console.MessageType.Info)

            draw_original_route = ImGui.toggle_button("Draw Original Route", draw_original_route)
            draw_new_route = ImGui.toggle_button("Draw New Route", draw_new_route)

            route = farming_route
            if draw_original_route:
                for i in range(len(route) - 1):
                    x1,y1 = route[i]
                    z1 = overlay.FindZ(x1, y1)
                    x2,y2 = route[i + 1]
                    z2 = overlay.FindZ(x2, y2)
                    overlay.DrawLine3D(x1, y1, z1, x2, y2, z2, 0xFF00FF00, 2.0)
                route = farming_route2
                for i in range(len(route) - 1):
                    x1,y1 = route[i]
                    z1 = overlay.FindZ(x1, y1)
                    x2,y2 = route[i + 1]
                    z2 = overlay.FindZ(x2, y2)
                    overlay.DrawLine3D(x1, y1, z1, x2, y2, z2, 0xFF00FF00, 2.0)

            if draw_new_route:
                for i in range(len(new_path) - 1):
                    x1,y1 = new_path[i]
                    z1 = overlay.FindZ(x1, y1)
                    x2,y2 = new_path[i + 1]
                    z2 = overlay.FindZ(x2, y2)
                    overlay.DrawLine3D(x1, y1, z1, x2, y2, z2, 0xFF0000FF, 2.0)

                for i in range(len(new_farming_route) - 1):
                    x1,y1 = new_farming_route[i]
                    z1 = overlay.FindZ(x1, y1)
                    x2,y2 = new_farming_route[i + 1]
                    z2 = overlay.FindZ(x2, y2)
                    overlay.DrawLine3D(x1, y1, z1, x2, y2, z2, 0xFFFF00FF, 2.0)

                for i in range(len(new_farming_route2) - 1):
                    x1,y1 = new_farming_route2[i]
                    z1 = overlay.FindZ(x1, y1)
                    x2,y2 = new_farming_route2[i + 1]
                    z2 = overlay.FindZ(x2, y2)
                    overlay.DrawLine3D(x1, y1, z1, x2, y2, z2, 0xFFFF00FF, 2.0)
                    
            PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

# main function must exist in every script and is the entry point for your script's execution.
def main():
    global module_name
    try:
        DrawWindow()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()

