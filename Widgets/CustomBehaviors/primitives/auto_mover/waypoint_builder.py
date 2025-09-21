
import ast
import time
from collections.abc import Generator
from typing import Any, List, Tuple

import PyMissionMap

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Pathing import AutoPathing
from Widgets.CustomBehaviors.primitives.auto_mover.path_helper import PathHelper
from Widgets.CustomBehaviors.primitives import constants

class WaypointBuilder:
    def __init__(self):
        self.list_of_points: list[tuple[float, float]] = []
        self._last_processed_click: tuple[float, float] | None = None
        self._last_point_add_time: float = 0.0
        self._point_add_delay: float = 0.5  # 500ms delay between adding points
        self._initialized_click: bool = False
        self.is_new_waypoint_record_activated = True

    def get_mm_last_click(self):
        """Get the last click position from Mission Map."""
        mm = PyMissionMap.PyMissionMap()  # singleton
        mm.GetContext()                   # refresh this frame
        if not mm.window_open:
            return None
        x = float(getattr(mm, "last_click_x", 0.0))
        y = float(getattr(mm, "last_click_y", 0.0))
        # some builds keep (0,0) until you click inside the MM panel
        if x == 0.0 and y == 0.0:
            return None
        return (x, y)

    def _process_new_clicks(self):
        if self.is_new_waypoint_record_activated == False:
            return 

        """Process new clicks and add points with delay control."""
        current_click = self.get_mm_last_click()
        
        # Initialize the last processed click to current position on first run
        if not self._initialized_click and current_click is not None:
            self._last_processed_click = current_click
            self._initialized_click = True
            if constants.DEBUG: print(f"Initialized click position: {current_click}")
            return
        
        if current_click is not None and current_click != self._last_processed_click:
            current_time = time.time()
            # Only add point if enough time has passed since last point was added
            if current_time - self._last_point_add_time >= self._point_add_delay:
                # Convert normalized coordinates to game coordinates and store them
                # This way points will move correctly with zoom
                game_x, game_y = PathHelper.normalized_to_game(current_click[0], current_click[1])
                self.list_of_points.append((game_x, game_y))
                self._last_processed_click = current_click
                self._last_point_add_time = current_time
                if constants.DEBUG: print(f"Added new point: normalized {current_click} -> game ({game_x}, {game_y})")
                if constants.DEBUG: print(f"Total points: {len(self.list_of_points)}")
            else:
                # Update last processed click to prevent spam but don't add point yet
                self._last_processed_click = current_click

    def remove_last_point_from_the_list(self):
        """Remove the most recently added point from the list."""
        if self.list_of_points:
            removed_point = self.list_of_points.pop()
            if constants.DEBUG: print(f"Removed last point: {removed_point}")
            if constants.DEBUG: print(f"Remaining points: {len(self.list_of_points)}")
            return removed_point
        else:
            if constants.DEBUG: print("No points to remove")
            return None

    def clear_list(self):
        """Clear all points from the list."""
        self.list_of_points = []

    def get_waypoints(self) -> list[tuple[float, float]]:
        """Get a copy of the current points list."""
        # return self.list_of_points.copy()
        return self.list_of_points

    def remove_waypoint(self, index):
        return self.list_of_points.pop(index)

    def try_inject_waypoint_coordinate_from_clipboard(self, clipboard:str):
        try:
            parsed = ast.literal_eval(clipboard)
            if isinstance(parsed, list):
                new_points: list[tuple[float, float]] = []
                for item in parsed:
                    if (
                        isinstance(item, tuple)
                        and len(item) == 2
                        and all(isinstance(x, (int, float)) for x in item)
                    ):
                        new_points.append((float(item[0]), float(item[1])))
                self.list_of_points = new_points
        except Exception:
            print("Failed to parse clipboard. Use a list of tuples like [(x1, y1), (x2, y2)].")

