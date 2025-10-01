import Py4GW
import PyPathing
import PyImGui
from Py4GWCoreLib import *

from typing import List, Tuple

MODULE_NAME = "PathPlanner Continuous Test"

# Global state
planned_path: List[Tuple[float, float, float]] = []
path_planner = PyPathing.PathPlanner()
last_goal_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
last_start_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)

update_timer = ThrottledTimer(50)  # Update every 100ms
update_path_by_mouse_coords = False

def main():
    global planned_path, last_goal_pos, last_start_pos, path_planner, update_timer, update_path_by_mouse_coords

    try:
        # Get positions
        mouse_x, mouse_y, mouse_z = Overlay().GetMouseWorldPos()
        player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        player_z = GLOBAL_CACHE.Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID())

        if PyImGui.begin("PathPlanner Test", PyImGui.WindowFlags.AlwaysAutoResize):
            PyImGui.text(f"Player: ({player_x:.0f}, {player_y:.0f}, {player_z:.0f})")
            PyImGui.text(f"Mouse:  ({mouse_x:.0f}, {mouse_y:.0f}, {mouse_z:.0f})")
            PyImGui.separator()
            
            if PyImGui.button("Capture End Position"):
                last_goal_pos = (-14961, 11453, player_z)
            
            update_path_by_mouse_coords = ImGui.toggle_button(
                "Update Path by Mouse Coordinates",
                update_path_by_mouse_coords
            )
            
            if update_path_by_mouse_coords:
                status = path_planner.get_status()
                if update_timer.IsExpired() and status != PyPathing.PathStatus.Pending:
                    last_goal_pos = (mouse_x, mouse_y, player_z)
                    last_goal_pos = (-14961, 11453, player_z)
                    path_planner.reset()
                    path_planner.plan(
                        start_x=player_x,
                        start_y=player_y,
                        start_z=player_z,
                        goal_x=last_goal_pos[0],
                        goal_y=last_goal_pos[1],
                        goal_z=last_goal_pos[2]
                    )
                    # Do not clear planned_path to prevent flicker
                    update_timer.Reset()
            

            if PyImGui.button("Plan Path"):
                last_start_pos = (player_x, player_y, player_z)
                last_goal_pos = (0, 0, player_z)
                path_planner.reset()
                path_planner.plan(
                    start_x=last_start_pos[0],
                    start_y=last_start_pos[1],
                    start_z=last_start_pos[2],
                    goal_x=last_goal_pos[0],
                    goal_y=last_goal_pos[1],
                    goal_z=last_goal_pos[2]
                )
                # Do not clear planned_path

            status = path_planner.get_status()

            if status == PyPathing.PathStatus.Pending:
                PyImGui.text("Path planning in progress...")

            elif status == PyPathing.PathStatus.Failed:
                PyImGui.text("Path planning failed. Try again.")

            elif status == PyPathing.PathStatus.Ready:
                planned_path = path_planner.get_path()
                PyImGui.text("Path planned successfully.")

            elif status == PyPathing.PathStatus.Idle:
                if not planned_path:
                    PyImGui.text("No path planned yet.")
                else:
                    PyImGui.text("Path already planned. Click 'Plan Path' to replan.")

            if planned_path:
                PyImGui.text("Path Points:")
                for i, pt in enumerate(planned_path):
                    PyImGui.text(f"{i+1}: ({pt[0]:.0f}, {pt[1]:.0f}, {pt[2]:.0f})")

        PyImGui.end()

        # Draw path
        if len(planned_path) >= 1:
            Overlay().BeginDraw()

            # Connect player to first path point
            z_player = Overlay().FindZ(player_x, player_y, player_z)
            z_first = Overlay().FindZ(planned_path[0][0], planned_path[0][1], player_z)
            Overlay().DrawLine3D(
                x1=player_x, y1=player_y, z1=z_player,
                x2=planned_path[0][0], y2=planned_path[0][1], z2=z_first,
                color=0xFF00FF00, thickness=2.5  # Yellow for origin connection
            )

            # Draw path segments
            for i in range(len(planned_path) - 1):
                z1 = Overlay().FindZ(planned_path[i][0], planned_path[i][1], player_z)
                z2 = Overlay().FindZ(planned_path[i + 1][0], planned_path[i + 1][1], player_z)
                Overlay().DrawLine3D(
                    x1=planned_path[i][0], y1=planned_path[i][1], z1=z1,
                    x2=planned_path[i + 1][0], y2=planned_path[i + 1][1], z2=z2,
                    color=0xFF00FF00, thickness=2.0
                )

            Overlay().EndDraw()


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
