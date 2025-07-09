import Py4GW
from Py4GWCoreLib import *

MODULE_NAME = "tester for planned paths"

script_running = False
planner = PyPathing.PathPlanner()  # Create planner object globally


def plan_path_coroutine():
    global script_running
    """
    Coroutine to plan a path from the current position to the target position.
    """
    while script_running:
        x, y, z = Agent.GetXYZ(Player.GetAgentID())
        mouse_x, mouse_y, mouse_z = Overlay().GetMouseWorldPos()

        planner.plan(x, y, z, mouse_x, mouse_y, z)

        while not planner.is_ready():
            yield from Routines.Yield.wait(25)

        # Wait one extra frame to ensure access safety
        yield from Routines.Yield.wait(10)


def main():
    global script_running
    try:
        window_flags = PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("move", window_flags):

            if PyImGui.button("Plan Path"):
                script_running = True
                GLOBAL_CACHE.Coroutines.append(plan_path_coroutine())
                ConsoleLog(MODULE_NAME, "Path planning started.", Py4GW.Console.MessageType.Info)

            if PyImGui.button("Stop Path Planning"):
                script_running = False
                GLOBAL_CACHE.Coroutines.clear()
                ConsoleLog(MODULE_NAME, "Path planning stopped.", Py4GW.Console.MessageType.Info)

            x, y, z = Agent.GetXYZ(Player.GetAgentID())
            mouse_x, mouse_y, mouse_z = Overlay().GetMouseWorldPos()
            path = planner.get_path()

            PyImGui.text(f"Planned Path: {len(path)} points")
            PyImGui.text(f"Start: {x:.2f}, {y:.2f}, {z:.2f}")
            PyImGui.text(f"Target: {mouse_x:.2f}, {mouse_y:.2f}, {mouse_z:.2f}")

            for i, point in enumerate(path):
                PyImGui.text(f"Point {i}: {point[0]:.2f}, {point[1]:.2f}, {point[2]:.2f}")

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


if __name__ == "__main__":
    main()
