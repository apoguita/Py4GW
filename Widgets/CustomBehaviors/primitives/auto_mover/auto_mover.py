from typing import Any, Callable, Generator

from Py4GWCoreLib import Map, Overlay
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Widgets.CustomBehaviors.primitives.auto_mover.follow_path_executor import FollowPathExecutor
from Widgets.CustomBehaviors.primitives.auto_mover.auto_pathing_builder import AutoPathingBuilder

from .path_builder import PathBuilder
from .path_renderer import PathRenderer

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
            self.__path_builder = PathBuilder()
            self.__autopathing_builder = AutoPathingBuilder()
            self.__path_renderer = PathRenderer()
            self.__auto_mover = FollowPathExecutor()
            self.__last_path_hash = None  # Track path changes
            
            # Initialize throttle timer for click processing (200ms)
            self.__click_throttle_timer = ThrottledTimer(200)

    def render(self):
        self._render_path()
        # Process new clicks and update path with throttle timer (200ms)
        if self.__click_throttle_timer.IsExpired():
            self.__path_builder._process_new_clicks()
            self.__click_throttle_timer.Reset()

    def remove_last_point_from_the_list(self):
        return self.__path_builder.remove_last_point_from_the_list()

    def clear_list(self):
        self.__path_builder.clear_list()
        self.__autopathing_builder.clear()
        self.__last_path_hash = None  # Reset path hash when clearing
        # Also stop the auto mover to prevent regeneration
        self.__auto_mover.stop()

    def get_list_of_points(self) -> list[tuple[float, float]]:
        return self.__path_builder.get_points()

    def get_final_path(self) -> list[tuple[float, float]]:
        return self.__autopathing_builder.get_final_path()

    def start_movement(self):
        autopathing_coordinates = self.__autopathing_builder.get_final_path()
        if autopathing_coordinates:
            self.__auto_mover.start(autopathing_coordinates)
        else:
            print("No autopathing coordinates available. Build autopathing first.")

    def stop_movement(self):
        self.__auto_mover.stop()

    def is_movement_running(self) -> bool:
        """Check if movement is currently running."""
        return self.__auto_mover.is_running()

    def get_movement_progress(self) -> float:
        """Get the current movement progress percentage."""
        return self.__auto_mover.movement_progress

    def act(self):
        """Main action method that coordinates path building and movement execution."""

        # Update autopathing builder with current points only if path has changed
        current_points = self.__path_builder.get_points()
        if current_points:
            # Create a simple hash of the path to detect changes
            current_path_hash = hash(tuple(current_points))
            if current_path_hash != self.__last_path_hash:
                self.__autopathing_builder.set_raw_path(current_points)
                self.__last_path_hash = current_path_hash
        
        # Process path generation
        self.__autopathing_builder.process_generation()
        
        # Execute auto mover logic
        self.__auto_mover.act()
    
    def follow_path(self):
        """Start following the built path."""
        if self.__autopathing_builder.has_final_path():
            self.start_movement()
        else:
            print("No valid path available. Build autopathing first.")

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
            self.__path_renderer.draw_path(ov, self.__path_builder.get_points())
            self.__path_renderer.draw_list_of_points(ov, self.__path_builder.get_points())
            self.__path_renderer.draw_label(ov, self.__path_builder.get_points())

            self.__path_renderer.draw_path(ov, self.__autopathing_builder.get_final_path(), Color(0, 0, 175, 255))
            self.__path_renderer.draw_list_of_points(ov, self.__autopathing_builder.get_final_path(), radius=2, color=Color(0,0,250,255))
            
            # Draw background overlay
            bgc = Color(0, 0, 0, int(255 * 0.3)).to_color()
            ov.DrawQuadFilled(left, top, left + width, top, left + width, top + height, left, top + height, bgc)

        finally:
            ov.PopClipRect()
            ov.EndDraw()
