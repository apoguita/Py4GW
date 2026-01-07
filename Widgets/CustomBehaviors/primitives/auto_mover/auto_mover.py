from typing import Any, Callable, Generator

from Py4GWCoreLib import Map, Overlay
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Widgets.CustomBehaviors.primitives.auto_mover.follow_path_executor import FollowPathExecutor
from Widgets.CustomBehaviors.primitives.auto_mover.path_builder import PathBuilder
from Widgets.CustomBehaviors.primitives.auto_mover.path_renderer import PathRenderer
from Widgets.CustomBehaviors.primitives.auto_mover.waypoint_builder import WaypointBuilder


class AutoMover:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutoMover, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.__waypoint_builder = WaypointBuilder()
            self.__path_builder = PathBuilder()
            self.__path_renderer = PathRenderer()
            self.__follow_path_executor = FollowPathExecutor()
            self.__last_path_hash = None  # Track path changes
            
            # Initialize throttle timer for click processing (200ms)
            self.__click_throttle_timer = ThrottledTimer(200)

    def render(self):
        self._render_path()
        # Process new clicks and update path with throttle timer (200ms)
        if self.__click_throttle_timer.IsExpired():
            self.__waypoint_builder._process_new_clicks()
            self.__click_throttle_timer.Reset()

    # WAYPOINTS -----------------------------------------

    def remove_last_waypoint_from_the_list(self):
        return self.__waypoint_builder.remove_last_point_from_the_list()

    def is_waypoint_recording_activated(self) -> bool:
        return self.__waypoint_builder.is_new_waypoint_record_activated

    def set_waypoint_recording_activated(self, is_active):
        self.__waypoint_builder.is_new_waypoint_record_activated = is_active

    def clear_list_of_waypoints(self):
        self.__waypoint_builder.clear_list()
        self.__path_builder.clear()
        self.__last_path_hash = None  # Reset path hash when clearing

    def try_inject_waypoint_coordinates_from_clipboard(self, clipboard:str):
        self.__waypoint_builder.try_inject_waypoint_coordinates_from_clipboard(clipboard)

    def try_inject_waypoint_coordinate_from_clipboard(self, clipboard:str):
        self.__waypoint_builder.try_inject_waypoint_coordinate_from_clipboard(clipboard)

    def get_list_of_waypoints(self) -> list[tuple[float, float]]:
        '''
        used for copying clipboard
        '''
        return self.__waypoint_builder.get_waypoints()

    def add_raw_waypoint(self, waypoint: tuple[float, float]):
        return self.__waypoint_builder.add_raw_waypoint(waypoint)

    def remove_waypoint(self, index):
        return self.__waypoint_builder.remove_waypoint(index)

    # WAYPOINTS -----------------------------------------

    def get_final_path(self) -> list[tuple[float, float]]:
        '''
        used for copying clipboard
        '''
        return self.__path_builder.get_final_path()

    def start_movement(self, start_at_waypoint_index:int):
        print(f"start_movement{start_at_waypoint_index}")
        waypoints:list[tuple[float, float]] = self.__waypoint_builder.get_waypoints()
        waypoints_trucated = waypoints[start_at_waypoint_index:]
        self.__follow_path_executor.start(waypoints_trucated)

    def stop_movement(self):
        self.__follow_path_executor.stop()
    
    def pause_movement(self):
        self.__follow_path_executor.pause()

    def resume_movement(self):
        self.__follow_path_executor.resume()

    def is_movement_paused(self) -> bool:
        return self.__follow_path_executor.is_paused()

    def is_movement_running(self) -> bool:
        """Check if movement is currently running."""
        return self.__follow_path_executor.is_running()

    def get_movement_progress(self) -> float:
        """Get the current movement progress percentage."""
        return self.__follow_path_executor.movement_progress
    
    # FOLLOWING -----------------------------------------
    

    def act(self):
        """Main action method that coordinates path building and movement execution."""

        # Update autopathing builder with current points only if path has changed
        waypoints = self.__waypoint_builder.get_waypoints()
        if waypoints:
            # Create a simple hash of the path to detect changes
            current_waypoints_hash = hash(tuple(waypoints))
            if current_waypoints_hash != self.__last_path_hash:
                self.__path_builder.set_waypoint_list(waypoints)
                self.__last_path_hash = current_waypoints_hash
        
        # Process path generation
        self.__path_builder.process_generation()
        
        # Execute auto mover logic
        self.__follow_path_executor.act()

    def _render_path(self):
        """Render the complete path visualization with Overlay management."""
        if not Map.MissionMap.IsWindowOpen():
            return
        ov = Overlay()

        # Mission Map window rect & clip (cast to int for API)
        l, t, r, b = Map.MissionMap.GetWindowCoords()
        left, top, right, bottom = int(l), int(t), int(r), int(b)
        width, height = right - left, bottom - top

        ov.BeginDraw("MissionMapPathViewer", left, top, width, height)
        ov.PushClipRect(left, top, right, bottom)

        try:
            self.__path_renderer.draw_path(ov, self.__waypoint_builder.get_waypoints())
            self.__path_renderer.draw_list_of_points(ov, self.__waypoint_builder.get_waypoints())
            self.__path_renderer.draw_label(ov, self.__waypoint_builder.get_waypoints())

            self.__path_renderer.draw_path(ov, self.__path_builder.get_final_path(), Color(0, 0, 175, 255))
            self.__path_renderer.draw_list_of_points(ov, self.__path_builder.get_final_path(), radius=2, color=Color(0,0,250,255))

            self.__path_renderer.draw_path(ov, self.__follow_path_executor.current_path, Color(230, 0, 0, 255))
            
            self.__path_renderer.draw_label(ov, self.__waypoint_builder.get_waypoints())

            if not self.is_waypoint_recording_activated():
                shadow = Color(0, 0, 0, 200).to_color()
                color = Color(255, 0, 0, 255) 
                label_text = "WAYPOINT RECORDING IS NOT ACTIVATED"
                ov.DrawText(left, top + height - 50, label_text, shadow, False, 1.5)       # shadow
                ov.DrawText(left,   top + height - 50,   label_text, color.to_color(), False, 1.5) # foreground 
            else:
                shadow = Color(0, 0, 0, 200).to_color()
                color = Color(0, 255, 0, 255) 
                label_text = "WAYPOINT RECORDING IS ACTIVATED"
                ov.DrawText(left, top + height - 50, label_text, shadow, False, 1.5)       # shadow
                ov.DrawText(left,   top + height - 50,   label_text, color.to_color(), False, 1.5) # foreground 

            # Draw background overlay
            bgc = Color(0, 0, 0, int(255 * 0.3)).to_color()
            ov.DrawQuadFilled(left, top, left + width, top, left + width, top + height, left, top + height, bgc)

        finally:
            ov.PopClipRect()
            ov.EndDraw()
