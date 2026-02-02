from Py4GWCoreLib import Overlay, Map
from Py4GWCoreLib.py4gwcorelib_src.Color import Color


class MapTransformCache:
    """Cache for map transformation parameters to avoid redundant API calls."""
    def __init__(self):
        self.gwinches = 96.0
        self.left = 0.0
        self.top = 0.0
        self.min_x = 0.0
        self.max_y = 0.0
        self.origin_x = 0.0
        self.origin_y = 0.0
        self.pan_offset_x = 0.0
        self.pan_offset_y = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.zoom = 1.0
        self.center_x = 0.0
        self.center_y = 0.0

    def update(self):
        """Update all cached map transformation parameters (7 API calls total)."""
        # Get map bounds
        self.left, self.top, _, _ = Map.GetMapWorldMapBounds()

        # Get game-space boundaries
        boundaries = Map.GetMapBoundaries()
        if len(boundaries) >= 4:
            self.min_x = boundaries[0]
            self.max_y = boundaries[3]

        # Compute origin
        self.origin_x = self.left + abs(self.min_x) / self.gwinches
        self.origin_y = self.top + abs(self.max_y) / self.gwinches

        # Get pan offset
        self.pan_offset_x, self.pan_offset_y = Map.MissionMap.GetPanOffset()

        # Get scale
        self.scale_x, self.scale_y = Map.MissionMap.GetScale()

        # Get zoom
        self.zoom = Map.MissionMap.GetZoom()

        # Get center
        self.center_x, self.center_y = Map.MissionMap.GetMapScreenCenter()

    def game_pos_to_screen(self, game_x: float, game_y: float) -> tuple[float, float]:

        """Convert game coordinates to screen coordinates using cached parameters."""
        # Convert game-space to world map space
        world_x = (game_x / self.gwinches) + self.origin_x
        world_y = (-game_y / self.gwinches) + self.origin_y  # Inverted Y

        # Apply pan offset
        offset_x = world_x - self.pan_offset_x
        offset_y = world_y - self.pan_offset_y

        # Apply scale
        scaled_x = offset_x * self.scale_x
        scaled_y = offset_y * self.scale_y

        # Apply zoom and center
        screen_x = scaled_x * self.zoom + self.center_x
        screen_y = scaled_y * self.zoom + self.center_y

        return screen_x, screen_y


class PathRenderer:
    def __init__(self):
        self._transform_cache = MapTransformCache()

    def draw_path(self, ov: Overlay, list_of_points: list[tuple[float, float]], color: Color | None = None, thickness: float = 2.0):
        """Draw lines connecting consecutive points in the path."""
        if len(list_of_points) < 2:
            return  # Need at least 2 points to draw a line

        if color is None:
            color = Color(0, 200, 0, 255)  # Green color by default

        last_sx, last_sy = None, None

        for game_x, game_y in list_of_points:
            # Convert game coordinates to screen coordinates using cached transform
            screen_x, screen_y = self._transform_cache.game_pos_to_screen(game_x, game_y)

            # Draw line from previous point to current point
            if last_sx is not None:
                ov.DrawLine(last_sx, last_sy, screen_x, screen_y, color.to_color(), thickness)

            last_sx, last_sy = screen_x, screen_y

    def draw_list_of_points(self, ov: Overlay, list_of_points: list[tuple[float, float]], radius: float = 7.0, color: Color | None = None):
        """Draw individual points with labels."""
        if color is None:
            color = Color(0, 200, 0, 255)  # Green color by default

        for game_x, game_y in list_of_points:
            # Convert game coordinates to screen coordinates using cached transform
            screen_x, screen_y = self._transform_cache.game_pos_to_screen(game_x, game_y)
            ov.DrawPolyFilled(screen_x, screen_y, radius=radius, color=color.to_color(), numsegments=18)

    def draw_label(self, ov: Overlay, list_of_points: list[tuple[float, float]], text: str = "Path", color: Color | None = None):
        """Draw text labels with point indices for each point in the path."""
        if not list_of_points:
            return

        if color is None:
            color = Color(255, 255, 255, 255)  # White color by default

        # Draw labels for each point showing their index
        for i, (game_x, game_y) in enumerate(list_of_points):
            screen_x, screen_y = self._transform_cache.game_pos_to_screen(game_x, game_y)

            # Create label text with point index
            label_text = f"{i}"

            # Draw shadow
            shadow = Color(0, 0, 0, 200).to_color()
            ov.DrawText(int(screen_x)+1, int(screen_y)+1, label_text, shadow, False, 1.0)       # shadow
            ov.DrawText(int(screen_x),   int(screen_y),   label_text, color.to_color(), False, 1.0) # foreground

    def update_transform_cache(self):
        """Update the cached map transformation parameters. Call this once per frame before drawing."""
        self._transform_cache.update()