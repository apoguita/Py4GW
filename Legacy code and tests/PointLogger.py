from operator import ne
from Py4GWCoreLib import *

module_name = "Point Logger"

started = False
polling_time = 5
timer = Timer()
timer.Start()

outpost_coord_list = [(-24380, 15074), (-26375, 161)]

bjora_coord_list = [
    (17810, -17649), (16582, -17136), (15257, -16568), (14084, -15748), (12940, -14873),
    (11790, -14004), (10640, -13136), (9404 , -12411), (8677 , -11176), (8581 , -9742 ),
    (7892 , -8494 ), (6989 , -7377 ), (6184 , -6180 ), (5384 , -4980 ), (4549 , -3809 ),
    (3622 , -2710 ), (2601 , -1694 ), (1185 , -1535 ), (-251 , -1514 ), (-1690, -1626 ),
    (-3122, -1771 ), (-4556, -1752 ), (-5809, -1109 ), (-6966,  -291 ), (-8390,  -142 ),
    (-9831,  -138 ), (-11272, -156 ), (-12685, -198 ), (-13933,  267 ), (-14914, 1325 ),
    (-15822, 2441 ), (-16917, 3375 ), (-18048, 4223 ), (-19196, 4986 ), (-20000, 5595 ),
    (-20300, 5600 )
]

new_bjora_coord_list = [(17810, -17649),
(17573, -17264),
(17251, -16787),
(16973, -16278),
(16673, -15784),
(16166, -15499),
(15633, -15268),
(15097, -15058),
(14545, -14879),
(13972, -14790),
(13393, -14745),
(12843, -14571),
(12343, -14290),
(11932, -13887),
(11545, -13453),
(11132, -13046),
(10759, -12607),
(10485, -12101),
(10297, -11558),
(10217, -10987),
(10173, -10411),
(10117, -9837),
(9916, -9310),
(9440, -8982),
(8943, -8687),
(8459, -8373),
(8006, -8022),
(7611, -7601),
(7205, -7214),
(6810, -6790),
(6418, -6371),
(6021, -5946),
(5627, -5523),
(5234, -5102),
(4849, -4673),
(4513, -4206),
(4188, -3732),
(3876, -3260),
(3550, -2775),
(3204, -2312),
(2852, -1849),
(2372, -1549),
(1795, -1487),
(1223, -1450),
(645, -1425),
(65, -1393),
(-515, -1358),
(-999, -1381),
(-1573, -1348),
(-2153, -1351),
(-2721, -1439),
(-3292, -1540),
(-3866, -1642),
(-4428, -1742),
(-4719, -1794),
(-5113, -1669),
(-5581, -1375),
(-5321, -1420),
(-5810, -1123),
(-6256, -755),
(-6672, -366),
(-7231, -245),
(-18048, 4223 ), (-19196, 4986 ), (-20000, 5595 ),
    (-20300, 5600 )
]

path_to_killing_spot = [
    (13070, -16911), (12938, -17081), (12790, -17201), (12747, -17220),
    (12703, -17239), (12684, -17184), (12526, -17275),
]


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

path_to_killing_spot2 = [
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

exit_jaga_moraine = [(12289, -17700) ,(15400, -20400),(15775,-20500),(15750,-20550)]

exit_jaga_moraine2 = [(12289, -17700) ,(13970, -18920), (15400, -20400),(15850,-20550)]


new_path = []

draw_original_route = False
draw_new_route = False
# Example of additional utility function
def DrawWindow():
    global module_name, started, polling_time, timer
    global draw_original_route, farming_route, farming_route2, path_to_killing_spot
    global new_path, draw_new_route
    try:
        if PyImGui.begin(module_name):
        
            PyImGui.text("Coordinate logger")
            PyImGui.separator()
            
            mwp_x, mwp_y, mwp_z = Overlay().GetMouseWorldPos()
            
            pos_x, pos_y = Player.GetXY()

            PyImGui.text(f"Mouse World Pos: x:{mwp_x:.0f} y:{mwp_y:.0f} z:{mwp_z:.0f}")
            PyImGui.text(f"Player Pos: x:{pos_x:.0f} y:{pos_y:.0f}")

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

            Overlay().BeginDraw()
            route = bjora_coord_list
            new_path = new_bjora_coord_list

            if draw_original_route:
                for i in range(len(route) - 1):
                    x1,y1 = route[i]
                    z1 = Overlay().FindZ(x1, y1)
                    x2,y2 = route[i + 1]
                    z2 = Overlay().FindZ(x2, y2)
                    Overlay().DrawLine3D(x1, y1, z1, x2, y2, z2, 0xFF00FF00, 2.0)
                    
                """
                route = farming_route2
                for i in range(len(route) - 1):
                    x1,y1 = route[i]
                    z1 = Overlay().FindZ(x1, y1)
                    x2,y2 = route[i + 1]
                    z2 = Overlay().FindZ(x2, y2)
                    Overlay().DrawLine3D(x1, y1, z1, x2, y2, z2, 0xFF00FF00, 2.0)
                """

            if draw_new_route:
                for i in range(len(new_path) - 1):
                    x1,y1 = new_path[i]
                    z1 = Overlay().FindZ(x1, y1)
                    x2,y2 = new_path[i + 1]
                    z2 = Overlay().FindZ(x2, y2)
                    Overlay().DrawLine3D(x1, y1, z1, x2, y2, z2, 0xFF0000FF, 2.0)
                    
                """

                for i in range(len(new_farming_route) - 1):
                    x1,y1 = new_farming_route[i]
                    z1 = Overlay().FindZ(x1, y1)
                    x2,y2 = new_farming_route[i + 1]
                    z2 = Overlay().FindZ(x2, y2)
                    Overlay().DrawLine3D(x1, y1, z1, x2, y2, z2, 0xFFFF00FF, 2.0)

                for i in range(len(new_farming_route2) - 1):
                    x1,y1 = new_farming_route2[i]
                    z1 = Overlay().FindZ(x1, y1)
                    x2,y2 = new_farming_route2[i + 1]
                    z2 = Overlay().FindZ(x2, y2)
                    Overlay().DrawLine3D(x1, y1, z1, x2, y2, z2, 0xFFFF00FF, 2.0)
                    """
                Overlay().EndDraw()
                    
            PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

# main function must exist in every script and is the entry point for your script's execution.
def main():
    global module_name
    try:
        if Map.IsMapLoading():
            return
        
        if not Party.IsPartyLoaded():
            return
        
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

