from typing import Any, Generator

from Py4GWCoreLib import Map, Agent
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Pathing import AutoPathing


class PathHelper:
    
    @staticmethod
    def __chain_paths(waypoints: list[tuple[float, float]], z: float) -> Generator[Any, None, list[tuple[float, float]]]:
        """
        Chains multiple (x, y) waypoints using AutoPathing().get_path.
        Each segment starts at the end of the previous.
        
        Parameters:
            waypoints: A list of 2D (x, y) target points.
            z: The elevation to use (same for all points).
        
        Returns:
            A full 2D path as List[(x, y)], chained across all waypoints.
        """
        if not waypoints or len(waypoints) < 2:
            return [(waypoints[0][0], waypoints[0][1])] if waypoints else []

        full_path: list[tuple[float, float, float]] = []
        start: tuple[float, float, float] = waypoints[0] + (z,)
        full_path.append(start)

        for target in waypoints[1:]:
            end: tuple[float, float, float] = target + (z,)
            segment = yield from AutoPathing().get_path(start, end)
            full_path.extend(segment)
            start = segment[-1] if segment else end  # fallback in case of empty segment

        return [(x, y) for x, y, _ in full_path]

    @staticmethod
    def build_valid_path(path_2d: list[tuple[float, float]]) -> Generator[Any, None, list[tuple[float, float]]]:
        z = float(Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID()))
        result = yield from PathHelper.__chain_paths(path_2d, z)
        return result

    # Coordinate conversion methods
    @staticmethod
    def normalized_to_screen(norm_x: float, norm_y: float) -> tuple[float, float]:
        """Convert normalized coordinates (-1 to 1) to screen coordinates."""
        # Get mission map window bounds
        l, t, r, b = Map.MissionMap.GetMissionMapContentsCoords()
        left, top, right, bottom = int(l), int(t), int(r), int(b)
        width, height = right - left, bottom - top
        
        # Convert from [-1, 1] to [0, 1] with Y-inversion
        adjusted_x = (norm_x + 1.0) / 2.0
        adjusted_y = (1.0 - norm_y) / 2.0
        
        # Convert to screen coordinates
        screen_x = left + adjusted_x * width
        screen_y = top + adjusted_y * height
        
        return screen_x, screen_y
    
    @staticmethod
    def normalized_to_game(norm_x: float, norm_y: float) -> tuple[float, float]:
        """Convert normalized coordinates (-1 to 1) to game coordinates."""
        # First convert to screen coordinates
        screen_x, screen_y = PathHelper.normalized_to_screen(norm_x, norm_y)
        # Then convert to game coordinates
        return PathHelper.screen_to_game(screen_x, screen_y)
    
    @staticmethod
    def screen_to_game(sx: float, sy: float) -> tuple[float, float]:
        """Convert screen coordinates to game coordinates using Py4GW built-in methods."""
        return Map.MissionMap.MapProjection.ScreenToGameMap(sx, sy)
    
    @staticmethod
    def game_to_screen(x: float, y: float) -> tuple[float, float]:
        """Convert game coordinates to screen coordinates using Py4GW built-in methods."""
        return Map.MissionMap.MapProjection.GameMapToScreen(x, y)