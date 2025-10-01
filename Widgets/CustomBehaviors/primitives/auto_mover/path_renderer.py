from collections.abc import Generator
from typing import Any, List, Tuple

from Py4GWCoreLib import Map, Overlay
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Widgets.CustomBehaviors.primitives.auto_mover.path_helper import PathHelper


class PathRenderer:
    def __init__(self):
        pass
    

    def draw_path(self, ov: Overlay, list_of_points: list[tuple[float, float]], color: Color | None = None, thickness: float = 2.0):
        """Draw lines connecting consecutive points in the path."""
        if len(list_of_points) < 2:
            return  # Need at least 2 points to draw a line
            
        if color is None:
            color = Color(0, 200, 0, 255)  # Green color by default
            
        last_sx, last_sy = None, None
        
        for i, (game_x, game_y) in enumerate(list_of_points):
            # Convert game coordinates to screen coordinates each time (accounts for zoom)
            screen_x, screen_y = PathHelper.game_to_screen(game_x, game_y)
            
            # Draw line from previous point to current point
            if last_sx is not None:
                ov.DrawLine(last_sx, last_sy, screen_x, screen_y, color.to_color(), thickness)
            
            last_sx, last_sy = screen_x, screen_y

    def draw_list_of_points(self, ov: Overlay, list_of_points: list[tuple[float, float]], radius: float = 7.0, color: Color | None = None):
        """Draw individual points with labels."""
        if color is None:
            color = Color(0, 200, 0, 255)  # Green color by default
            
        for i, (game_x, game_y) in enumerate(list_of_points):
            # Convert game coordinates to screen coordinates each time (accounts for zoom)
            screen_x, screen_y = PathHelper.game_to_screen(game_x, game_y)
            ov.DrawPolyFilled(screen_x, screen_y, radius=radius, color=color.to_color(), numsegments=18)

    def draw_label(self, ov: Overlay, list_of_points: list[tuple[float, float]], text: str = "Path", color: Color | None = None):
        """Draw text labels with point indices for each point in the path."""
        if not list_of_points:
            return
            
        if color is None:
            color = Color(255, 255, 255, 255)  # White color by default
            
        # Draw labels for each point showing their index
        for i, (game_x, game_y) in enumerate(list_of_points):
            screen_x, screen_y = PathHelper.game_to_screen(game_x, game_y)
            
            # Create label text with point index
            label_text = f"{i}"
            
            # Draw shadow
            shadow = Color(0, 0, 0, 200).to_color()
            ov.DrawText(int(screen_x)+1, int(screen_y)+1, label_text, shadow, False, 1.0)       # shadow
            ov.DrawText(int(screen_x),   int(screen_y),   label_text, color.to_color(), False, 1.0) # foreground 